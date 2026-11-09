"""Safety tests for release.py. Docker is mocked; run: python3 -m unittest -v test_release.py"""
import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('release', Path(__file__).with_name('release.py'))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)

ID = lambda ch: 'sha256:' + ch * 64  # noqa: E731

STATIC = {
    'schema': 2, 'project': 'example', 'source': 'https://github.com/owner/example', 'mode': 'production',
    'images': {'web': {'repository': 'ghcr.io/owner/example-web'}},
    'services': {'web': {'role': 'app', 'image': 'web', 'container': 'example-web',
                         'port': {'host': 3011, 'container': 8080}}},
}
SERVER = {
    'schema': 2, 'project': 'shop', 'source': 'https://github.com/owner/shop', 'mode': 'production',
    'deployDir': '/opt/shop', 'envFiles': ['.env.production'],
    'images': {'app': {'repository': 'ghcr.io/owner/shop'}},
    'services': {
        'shop-app': {'role': 'app', 'image': 'app', 'container': 'shop-app', 'port': {'host': None, 'container': 3000}},
        'shop-worker': {'role': 'worker', 'image': 'app', 'container': 'shop-worker',
                        'mounts': [{'type': 'volume', 'target': '/data'}]},
        'shop-migrate': {'role': 'job', 'image': 'app', 'profile': 'migrate'},
    },
}


def container(project, service, image, ports=None, mounts=(), healthy=True):
    return {'Image': image, 'Mounts': list(mounts),
            'State': {'Running': True, 'Health': {'Status': 'healthy' if healthy else 'unhealthy'}},
            'Config': {'Labels': {'com.docker.compose.project': project, 'com.docker.compose.service': service,
                                  'com.docker.compose.project.config_files': '/x/compose.yml'}},
            'NetworkSettings': {'Ports': ports or {}}, 'HostConfig': {'PortBindings': {}}}


class Base(unittest.TestCase):
    cfg = STATIC

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        p = patch.object(r, 'ROOT', self.root); p.start(); self.addCleanup(p.stop)
        self.c = r.validate_config(copy.deepcopy(self.cfg))
        for name in r.bundle_files(self.c):
            (self.root / name).parent.mkdir(parents=True, exist_ok=True)
            (self.root / name).write_text(name)
        self.record = {'schema': 2, 'project': self.c['project'], 'revision': 'a' * 40,
                       'platform': 'linux/amd64', 'mode': 'production', 'source': self.c['source'],
                       'images': {k: {'image': v['repository'] + '@' + ID('b'), 'visibility': 'private'}
                                  for k, v in self.c['images'].items()},
                       'bundleHashes': {n: r.sha(self.root / n) for n in r.bundle_files(self.c)}}

    def inspect(self, mapping):
        return patch.object(r, 'inspect_container', side_effect=lambda name: copy.deepcopy(mapping.get(name)))

    def expected_file(self, ids):
        path = self.root / 'current.json'
        r.write(path, {'project': self.c['project'],
                       'services': {n: ({'imageId': i} if i else None) for n, i in ids.items()}})
        return path


class ConfigAndRecord(Base):
    def test_valid_record(self):
        self.assertEqual(r.validate_record(self.record, self.c), self.record)

    def test_schema_one_config_rejected(self):
        with self.assertRaises(ValueError):
            r.validate_config({**copy.deepcopy(STATIC), 'schema': 1})

    def test_non_ghcr_repository_rejected(self):
        bad = copy.deepcopy(STATIC); bad['images']['web']['repository'] = 'docker.io/owner/x'
        with self.assertRaises(ValueError): r.validate_config(bad)

    def test_env_files_need_relative_paths_and_deploy_dir(self):
        for change in [{'envFiles': ['/etc/x']}, {'envFiles': ['../x']}, {'envFiles': ['.env'], 'deployDir': None}]:
            bad = {**copy.deepcopy(SERVER), **change}
            with self.assertRaises(ValueError): r.validate_config(bad)

    def test_mutable_or_foreign_reference_rejected(self):
        for ref in ['ghcr.io/owner/example-web:latest', 'ghcr.io/other/example-web@' + ID('b'), ID('b')]:
            rec = copy.deepcopy(self.record); rec['images']['web']['image'] = ref
            with self.assertRaises(ValueError): r.validate_record(rec, self.c)

    def test_bare_id_allowed_only_in_rehearsal(self):
        rec = copy.deepcopy(self.record); rec['images']['web']['image'] = ID('b')
        r.validate_record(rec, {**self.c, 'rehearsal': True})

    def test_changed_or_incomplete_bundle_rejected(self):
        with self.assertRaises(ValueError): r.validate_record({**self.record, 'bundleHashes': {}}, self.c)
        (self.root / 'ops/release.py').write_text('changed')
        with self.assertRaises(ValueError): r.validate_record(self.record, self.c)

    def test_wrong_project_mode_or_visibility_rejected(self):
        for key, value in [('project', 'other'), ('mode', 'preview')]:
            with self.assertRaises(ValueError): r.validate_record({**self.record, key: value}, self.c)
        rec = copy.deepcopy(self.record); rec['images']['web']['visibility'] = 'public'
        with self.assertRaises(ValueError): r.validate_record(rec, self.c)

    def test_approval_must_match_all_digests(self):
        with self.assertRaises(ValueError): r.approve(self.record, [ID('e')])
        r.approve(self.record, [ID('b')])


class StaticCurrent(Base):
    def ports(self, ip='127.0.0.1', port='3011'):
        return {'8080/tcp': [{'HostIp': ip, 'HostPort': port}]}

    def test_changed_image_rejected(self):
        with self.inspect({'example-web': container('example', 'web', ID('c'), self.ports())}):
            with self.assertRaises(ValueError): r.current(self.c, {'web': ID('d')})

    def test_public_port_rejected(self):
        with self.inspect({'example-web': container('example', 'web', ID('c'), self.ports('0.0.0.0'))}):
            with self.assertRaises(ValueError): r.current(self.c, {'web': ID('c')})

    def test_undeclared_mount_rejected(self):
        m = [{'Type': 'volume', 'Destination': '/data'}]
        with self.inspect({'example-web': container('example', 'web', ID('c'), self.ports(), m)}):
            with self.assertRaises(ValueError): r.current(self.c, {'web': ID('c')})

    def test_unhealthy_allowed_only_for_rollback(self):
        data = container('example', 'web', ID('c'), self.ports(), healthy=False)
        with self.inspect({'example-web': data}):
            r.current(self.c, {'web': ID('c')}, require_healthy=False)
            with self.assertRaises(ValueError): r.current(self.c, {'web': ID('c')})

    def test_stopped_target_uses_original_port_binding(self):
        data = container('example', 'web', ID('c'), {}, healthy=False)
        data['HostConfig']['PortBindings'] = self.ports()
        with self.inspect({'example-web': data}):
            r.current(self.c, {'web': ID('c')}, require_healthy=False)
        data['HostConfig']['PortBindings'] = self.ports('0.0.0.0')
        with self.inspect({'example-web': data}):
            with self.assertRaises(ValueError): r.current(self.c, {'web': ID('c')}, require_healthy=False)

    def test_initial_deployment_requires_absent_container(self):
        with self.inspect({}):
            self.assertEqual(r.current(self.c, {'web': None}), {'web': None})
        with self.inspect({'example-web': container('example', 'web', ID('c'), self.ports())}):
            with self.assertRaises(ValueError): r.current(self.c, {'web': None})

    def test_missing_expected_entry_rejected(self):
        with self.inspect({}):
            with self.assertRaises(ValueError): r.current(self.c, {})

    def test_wrong_approval_stops_before_inspection(self):
        with patch.object(r, 'current') as cur:
            with self.assertRaises(ValueError):
                r.deploy(self.c, self.record, self.expected_file({'web': ID('c')}), [ID('e')], self.root / 's')
            cur.assert_not_called()


class ServerShape(Base):
    cfg = SERVER

    def healthy_state(self):
        return {'shop-app': container('shop', 'shop-app', ID('c')),
                'shop-worker': container('shop', 'shop-worker', ID('c'),
                                         mounts=[{'Type': 'volume', 'Destination': '/data'}])}

    def test_jobs_are_not_long_running(self):
        self.assertEqual(r.long_running(self.c), ['shop-app', 'shop-worker'])
        self.assertEqual(r.jobs(self.c), ['shop-migrate'])

    def test_declared_mounts_and_proxy_only_service_pass(self):
        with self.inspect(self.healthy_state()):
            r.current(self.c, {'shop-app': ID('c'), 'shop-worker': ID('c')})

    def test_proxy_only_service_must_not_publish(self):
        state = self.healthy_state()
        state['shop-app']['NetworkSettings']['Ports'] = {'3000/tcp': [{'HostIp': '127.0.0.1', 'HostPort': '3000'}]}
        with self.inspect(state):
            with self.assertRaises(ValueError): r.current(self.c, {'shop-app': ID('c'), 'shop-worker': ID('c')})

    def test_env_file_missing_or_readable_rejected(self):
        d = self.root / 'deploy'; d.mkdir()
        c = {**self.c, 'deployDir': str(d)}
        with self.assertRaises(ValueError): r.check_env_files(c)
        f = d / '.env.production'; f.write_text('A=1\n'); os.chmod(f, 0o644)
        with self.assertRaises(ValueError): r.check_env_files(c)
        os.chmod(f, 0o600)
        self.assertEqual(r.check_env_files(c), {'.env.production': r.sha(f)})

    def test_migrate_needs_exactly_one_backup_decision(self):
        exp = self.expected_file({'shop-app': ID('c'), 'shop-worker': ID('c')})
        for backup, none in [(None, False), ('dump-1', True)]:
            with self.assertRaises(ValueError):
                r.migrate(self.c, self.record, exp, [ID('b')], backup, none, self.root / 's')

    def test_rollback_refused_after_migration_without_confirmation(self):
        d = self.root / 's' / 'one'; d.mkdir(parents=True)
        r.write(d / 'previous-compose.json', {'services': {}})
        r.write(d / 'state.json', {'schema': 2, 'project': 'shop', 'migrationRan': True,
                                   'previousImageIds': {'shop-app': ID('c'), 'shop-worker': ID('c')},
                                   'targetImageIds': {'shop-app': ID('d'), 'shop-worker': ID('d')},
                                   'previousComposeSha256': r.sha(d / 'previous-compose.json')})
        with patch.object(r, 'current') as cur:
            with self.assertRaises(ValueError): r.rollback(self.c, d, [ID('c')], False, False)
            cur.assert_not_called()

    def test_new_service_removal_needs_explicit_approval(self):
        d = self.root / 's' / 'two'; d.mkdir(parents=True)
        r.write(d / 'state.json', {'schema': 2, 'project': 'shop', 'previousImageIds': {'shop-app': None, 'shop-worker': None},
                                   'targetImageIds': {}, 'containers': {}})
        with self.assertRaises(ValueError): r.rollback(self.c, d, [], False, False)

    def test_v1_state_refused(self):
        d = self.root / 's' / 'old'; d.mkdir(parents=True)
        r.write(d / 'state.json', {'project': 'shop', 'previousImageId': ID('c')})
        with self.assertRaises(ValueError): r.rollback(self.c, d, [ID('c')], False, False)

    def test_rollback_restores_previous_images_with_captured_model(self):
        d = self.root / 's' / 'three'; d.mkdir(parents=True)
        r.write(d / 'previous-compose.json', {'services': {'shop-app': {}, 'shop-worker': {}}})
        state = {'schema': 2, 'project': 'shop', 'migrationRan': False,
                 'previousImageIds': {'shop-app': ID('c'), 'shop-worker': ID('c')},
                 'targetImageIds': {'shop-app': ID('d'), 'shop-worker': ID('d')},
                 'containers': {'shop-app': 'shop-app', 'shop-worker': 'shop-worker'},
                 'previousProjectDir': '/opt/shop',
                 'previousComposeSha256': r.sha(d / 'previous-compose.json')}
        r.write(d / 'state.json', state)
        with patch.object(r, 'current') as cur, patch.object(r, 'inspect_image'), \
                patch.object(r, 'compose_up') as up, self.inspect(self.healthy_state()):
            r.rollback(self.c, d, [ID('c')], False, False)
            cur.assert_called_once_with(self.c, state['targetImageIds'], require_healthy=False)
            up.assert_called_once_with(self.c, d / 'previous-compose.json', {}, ['shop-app', 'shop-worker'],
                                       project_dir='/opt/shop')
        self.assertEqual(r.read(d / 'state.json')['status'], 'rolled-back')

    def test_tampered_rollback_model_rejected(self):
        d = self.root / 's' / 'four'; d.mkdir(parents=True)
        r.write(d / 'previous-compose.json', {'services': {}})
        r.write(d / 'state.json', {'schema': 2, 'project': 'shop', 'previousImageIds': {'shop-app': ID('c')},
                                   'targetImageIds': {}, 'previousComposeSha256': '0' * 64})
        with self.assertRaises(ValueError): r.rollback(self.c, d, [ID('c')], False, False)

    def test_derived_model_drops_static_network_addresses_only(self):
        model = {'services': {'shop-app': {'image': 'ghcr.io/owner/shop@' + ID('b'), 'container_name': 'shop-app',
                                           'networks': {'proxy': {'ipv4_address': '172.24.0.2',
                                                                  'ipv6_address': 'fd00::2',
                                                                  'aliases': ['shop']},
                                                        'db': None}}},
                 'networks': {'proxy': {'external': True, 'name': 'x-proxy'}, 'db': {'external': True}}}
        refs = {'app': 'ghcr.io/owner/shop@' + ID('b')}
        with patch.object(r, 'run', return_value=json.dumps(model)):
            path = r.derive_compose(self.c, refs, self.root / 'work', 'shop-smoke-x', names='auto', ports={})
        derived = json.loads(path.read_text())
        self.assertEqual(derived['services']['shop-app']['networks'],
                         {'proxy': {'aliases': ['shop']}, 'db': None})
        self.assertEqual(derived['networks'], {'proxy': {}, 'db': {}})

    def test_image_env_names(self):
        self.assertEqual(r.image_env(self.c, {'app': 'x'}), {'RELEASE_IMAGE_APP': 'x', 'RELEASE_IMAGE': 'x'})
        self.assertEqual(r.image_env(self.c, {'a': 'x', 'b': 'y'}), {'RELEASE_IMAGE_A': 'x', 'RELEASE_IMAGE_B': 'y'})


if __name__ == '__main__':
    unittest.main()
