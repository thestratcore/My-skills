#!/usr/bin/env python3
"""Unit tests for survey.py. No network, no real npm: subprocess and registry calls are faked."""
import datetime as dt
import json
import pathlib
import re
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import survey as s  # noqa: E402

TODAY = dt.date(2026, 11, 9)
SKILL = pathlib.Path(__file__).resolve().parent.parent


class Versions(unittest.TestCase):
    def test_classify(self):
        self.assertEqual(s.classify_update('1.2.3', '2.0.0'), 'major')
        self.assertEqual(s.classify_update('1.2.3', '1.3.0'), 'minor')
        self.assertEqual(s.classify_update('1.2.3', '1.2.4'), 'patch')
        self.assertEqual(s.classify_update('1.2.3', '1.2.3'), 'current')
        self.assertEqual(s.classify_update('2.0.0', '1.9.0'), 'current')
        self.assertEqual(s.classify_update('nonsense', '1.0.0'), 'unknown')

    def test_newest_in_major_skips_prereleases(self):
        vs = ['4.1.0', '4.2.0-beta.1', '4.1.9', '5.0.0']
        self.assertEqual(s.newest_in_major(vs, 4), '4.1.9')
        self.assertIsNone(s.newest_in_major(vs, 3))


class NodePins(unittest.TestCase):
    def test_node_major(self):
        self.assertEqual(s.node_major('22'), 22)
        self.assertEqual(s.node_major('v24.14.0\n'), 24)
        self.assertEqual(s.node_major('lts/jod'), 22)
        self.assertEqual(s.node_major('24.14.0-alpine'), 24)
        self.assertIsNone(s.node_major('lts/*'))

    def test_engines(self):
        self.assertTrue(s.engines_allow('>=22 <23', 22))
        self.assertFalse(s.engines_allow('>=22 <23', 24))
        self.assertTrue(s.engines_allow('>=22.12.0', 24))
        self.assertTrue(s.engines_allow('^22.23.4 || ^24.22.1 || >=26.12.1', 24))
        self.assertFalse(s.engines_allow('^22.23.4 || ^24.22.1 || >=26.12.1', 23))
        self.assertTrue(s.engines_allow('22.x', 22))
        self.assertEqual(min(lo for lo, _ in s.engine_intervals('>=22.12.0')), 22)

    def test_dockerfile_args_platform_and_stages(self):
        text = '\n'.join([
            'ARG NODE_IMAGE=node:24-alpine@sha256:' + 'a' * 64,
            'FROM --platform=$BUILDPLATFORM ${NODE_IMAGE} AS build',
            'FROM build AS config',
            'FROM nginxinc/nginx-unprivileged:1.29-alpine AS runtime',
            'FROM mcr.microsoft.com/playwright:latest',
            'FROM ${UNKNOWN_IMAGE}',
        ])
        e = s.parse_dockerfile(text)
        self.assertEqual([x['pinning'] for x in e], ['digest', 'tag', 'latest', 'unresolved'])
        self.assertEqual(e[0]['node_major'], 24)
        self.assertIsNone(e[1]['node_major'])

    def test_node_status(self):
        sch = s.NODE_SCHEDULE
        self.assertEqual(s.node_status(20, sch, TODAY), 'eol')
        self.assertTrue(s.node_status(22, sch, TODAY).startswith('maintenance, 172'))
        self.assertEqual(s.node_status(26, sch, TODAY), 'active LTS')
        self.assertEqual(s.node_status(25, sch, TODAY), 'unknown')
        self.assertEqual(s.node_status(None, sch, TODAY), 'unknown')


class Lockfile(unittest.TestCase):
    def test_v3_top_level_only(self):
        lock = {'lockfileVersion': 3, 'packages': {
            '': {'name': 'x'},
            'node_modules/react': {'version': '19.3.1'},
            'node_modules/@types/react': {'version': '19.3.0'},
            'node_modules/a/node_modules/react': {'version': '18.0.0'},
        }}
        self.assertEqual(s.locked_versions(lock), {'react': '19.3.1', '@types/react': '19.3.0'})

    def test_v1(self):
        self.assertEqual(s.locked_versions({'dependencies': {'a': {'version': '1.0.0'}}}), {'a': '1.0.0'})

    def test_coupled_drift(self):
        issues = s.coupled_drift({'react': '19.3.1', 'react-dom': '19.2.0', '@types/react': '19.1.0',
                                  'vitest': '4.1.10', '@vitest/coverage-v8': '4.1.12', 'next': '16.4.5',
                                  'eslint-config-next': '16.0.0'})
        text = ' '.join(issues)
        self.assertIn('react-dom', text)
        self.assertIn('@vitest/coverage-v8', text)
        self.assertNotIn('@types/react ', text)
        self.assertNotIn('eslint-config-next', text)


class Audit(unittest.TestCase):
    def test_nonzero_exit_with_json_is_findings(self):
        payload = {'vulnerabilities': {'zod': {'severity': 'high'}, 'x': {'severity': 'moderate'}},
                   'metadata': {'vulnerabilities': {'high': 1, 'moderate': 1, 'critical': 0, 'low': 0}}}
        a = s.npm_audit('.', True, False, runner=lambda *a, **k: (1, json.dumps(payload), ''))
        self.assertEqual(a['counts']['high'], 1)
        self.assertEqual(a['serious'], ['zod'])

    def test_network_error_is_unavailable(self):
        payload = {'error': {'code': 'ENOTFOUND', 'summary': 'request to registry failed'}}
        a = s.npm_audit('.', False, False, runner=lambda *a, **k: (1, json.dumps(payload), ''))
        self.assertIn('error', a)
        self.assertIn('error', s.npm_audit('.', False, False, runner=lambda *a, **k: (None, '', 'timeout')))
        self.assertEqual(s.npm_audit('.', False, True), {'error': 'offline'})


def fake_runner(audit_payload):
    def runner(cmd, cwd, timeout=120):
        if cmd[0] == 'git':
            return 1, '', 'not a repo'
        return 1, json.dumps(audit_payload), ''
    return runner


def fake_fetch(name):
    data = {
        'next': {'latest': '16.4.5', 'versions': {'16.4.0': {}, '16.4.5': {}}},
        'react': {'latest': '19.3.1', 'versions': {'19.3.0': {}, '19.3.1': {}}},
        'typescript': {'latest': '7.0.2', 'versions': {'5.9.3': {}, '5.9.4': {}, '7.0.2': {}}},
        'left-pad': {'latest': '1.3.0', 'versions': {'1.3.0': {'deprecated': 'use String.padStart'}}},
        '@types/node': {'latest': '26.6.6', 'versions': {'22.20.5': {}, '22.21.0': {}, '26.6.6': {}}},
    }
    if name == 'broken':
        raise OSError('ECONNRESET')
    return data[name]


class ProjectSurvey(unittest.TestCase):
    def make(self, files):
        d = pathlib.Path(tempfile.mkdtemp())
        for rel, content in files.items():
            p = d / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content if isinstance(content, str) else json.dumps(content))
        return d

    def base(self, **over):
        pkg = {'name': 'x', 'engines': {'node': '>=22 <23'},
               'dependencies': {'next': '16.4.0', 'react': '19.3.0', 'left-pad': '1.3.0', 'broken': '1.0.0'},
               'devDependencies': {'typescript': '5.9.3', '@types/node': '26.6.6'}}
        lock = {'lockfileVersion': 3, 'packages': {'': {}, **{f'node_modules/{n}': {'version': v} for n, v in
                {'next': '16.4.0', 'react': '19.3.0', 'left-pad': '1.3.0', 'broken': '1.0.0',
                 'typescript': '5.9.3', '@types/node': '26.6.6'}.items()}}}
        files = {'package.json': pkg, 'package-lock.json': lock, '.nvmrc': '22\n',
                 'Dockerfile': 'FROM node:24-alpine AS build\nFROM build\n'}
        files.update(over)
        return self.make(files)

    def test_end_to_end(self):
        d = self.base()
        audit = {'metadata': {'vulnerabilities': {'critical': 1, 'high': 0, 'moderate': 2, 'low': 0}},
                 'vulnerabilities': {'next': {'severity': 'critical'}}}
        r = s.survey_project('demo', d, {}, s.NODE_SCHEDULE, TODAY, False, runner=fake_runner(audit), fetch=fake_fetch)
        texts = [f['priority'] + ' ' + f['text'] for f in r['findings']]
        joined = '\n'.join(texts)
        self.assertEqual(r['priority'], 'P1')
        self.assertIn('runtime advisories: 1 critical', joined)
        self.assertIn('Node pins disagree: majors [22, 24]', joined)
        self.assertIn('excludes pinned major(s) [24]', joined)
        self.assertIn('left-pad@1.3.0 is deprecated', joined)
        self.assertIn('@types/node 26.6.6 is ahead of the Node 22 runtime', joined)
        self.assertIn('pinned by tag only', joined)
        self.assertTrue(any('registry lookup failed for 1/6' in g for g in r['gaps']))
        ts = next(x for x in r['dependencies'] if x['name'] == 'typescript')
        self.assertEqual((ts['update'], ts['wanted']), ('major', '5.9.4'))
        names = [g['name'] for g in r['groups']]
        self.assertTrue(names[0].startswith('safe batch'))
        self.assertIn('major: TypeScript', names)
        self.assertNotIn('major: Node.js', names)  # @types/node is capped at the runtime major
        self.assertEqual(len(texts), len(set(texts)))  # deduplicated
        md = s.render_md([r], 'test', TODAY)
        self.assertIn('| P1 | demo |', md)
        self.assertIn('Data gaps', md)

    def test_offline_marks_gaps_not_up_to_date(self):
        d = self.base()
        r = s.survey_project('demo', d, {}, s.NODE_SCHEDULE, TODAY, True, runner=fake_runner({}), fetch=fake_fetch)
        self.assertEqual(r['dependencies'], [])
        self.assertTrue(any('offline' in g for g in r['gaps']))

    def test_pnpm_is_registry_only(self):
        d = self.make({'package.json': {'name': 'p', 'dependencies': {'react': '^19.3.0'}},
                       'pnpm-lock.yaml': 'lockfileVersion: 9\n', '.nvmrc': 'lts/jod'})
        r = s.survey_project('p', d, {}, s.NODE_SCHEDULE, TODAY, False, runner=fake_runner({}), fetch=fake_fetch)
        self.assertEqual(r['package_manager']['tool'], 'pnpm')
        self.assertEqual(r['audit'], {})
        self.assertTrue(any('no lockfile-only audit' in g for g in r['gaps']))
        self.assertEqual(r['dependencies'][0]['locked'], '19.3.0')

    def test_ranking(self):
        d = self.make({'package.json': {'name': 'ok'}, 'package-lock.json': {'lockfileVersion': 3, 'packages': {'': {}}},
                       '.nvmrc': '26'})
        r = s.survey_project('ok', d, {}, s.NODE_SCHEDULE, TODAY, False,
                             runner=fake_runner({'metadata': {'vulnerabilities': {}}, 'vulnerabilities': {}}), fetch=fake_fetch)
        self.assertEqual(r['priority'], 'OK')
        d = self.make({'package.json': {'name': 'old'}, 'package-lock.json': {'lockfileVersion': 3, 'packages': {'': {}}},
                       '.nvmrc': '20'})
        r = s.survey_project('old', d, {}, s.NODE_SCHEDULE, TODAY, True, runner=fake_runner({}), fetch=fake_fetch)
        self.assertEqual(r['priority'], 'P1')

    def test_discover_skips_hidden_and_registered(self):
        root = self.make({'A/package.json': {}, 'B/sub/package.json': {}, '.release-worktrees/A/package.json': {},
                          'C/node_modules/x/package.json': {}})
        found = s.discover(root, {(root / 'A').resolve()})
        self.assertEqual([p.relative_to(root).as_posix() for p in found], ['B/sub'])


class Registry(unittest.TestCase):
    def test_projects_md_matches_registry(self):
        text = (SKILL / 'references' / 'projects.md').read_text()
        keys = re.findall(r'^## ([a-z0-9-]+)$', text, re.M)
        self.assertEqual(sorted(keys), sorted(s.PROJECTS))
        for meta in s.PROJECTS.values():
            self.assertIn(meta['repo'], text)


if __name__ == '__main__':
    unittest.main()
