#!/usr/bin/env python3
"""Read-only dependency survey for the Stratcore CodeProjects (nodejs-project-upgrade skill).

Never installs, never writes inside a repository, never touches node_modules.
Data comes from manifests, lockfiles, Dockerfiles, CI files, `npm audit --package-lock-only`
and public registry metadata.

  survey.py [<project> ...] [--all] [--root DIR] [--md FILE] [--json FILE] [--offline]
"""
import argparse
import concurrent.futures
import datetime as dt
import json
import pathlib
import re
import subprocess
import sys
import urllib.parse
import urllib.request

SURVEY_VERSION = '1.0.0'
DEFAULT_ROOT = '/Users/admin/Documents/CodeProjects'
REGISTRY = 'https://registry.npmjs.org/'
SCHEDULE_URL = 'https://raw.githubusercontent.com/nodejs/Release/main/schedule.json'
TIMEOUT = 20

# Registered production apps. Keep in sync with references/projects.md (a test checks it).
PROJECTS = {
    'garageerp': {'repo': 'GarageERP-React', 'delivery': 'VPS container garageerp-app, 127.0.0.1:3010'},
    'stratdesk': {'repo': 'StratDesk-nextjs', 'delivery': 'VPS container stratdesk (no published port)'},
    'silvaros-nli': {'repo': 'Silvaros-NLI-React', 'delivery': 'VPS container silvaros, 127.0.0.1:3000'},
    'drezuratop': {'repo': 'DrezuraTop-web', 'delivery': 'VPS container drezuratop, 127.0.0.1:8080 (ops/release.py)'},
    'parkourtop': {'repo': 'ParkourTop-web', 'delivery': 'VPS container parkourtop, 127.0.0.1:8081'},
    'marcelkocian': {'repo': 'MarcelKocian-ts', 'delivery': 'VPS container marcelkocian-web-1, 127.0.0.1:3011 (ops/release.py)'},
}

# Fallback Node release schedule (nodejs/Release schedule.json, checked 2026-11-09).
NODE_SCHEDULE = {
    18: {'start': '2022-04-19', 'lts': '2022-10-25', 'maintenance': '2023-10-18', 'end': '2025-04-30'},
    20: {'start': '2023-04-18', 'lts': '2023-10-24', 'maintenance': '2024-10-22', 'end': '2026-04-30'},
    22: {'start': '2024-04-24', 'lts': '2024-10-29', 'maintenance': '2025-10-21', 'end': '2027-04-30'},
    24: {'start': '2025-05-06', 'lts': '2025-10-28', 'maintenance': '2026-10-20', 'end': '2028-04-30'},
    26: {'start': '2026-05-05', 'lts': '2026-10-28', 'maintenance': '2027-10-20', 'end': '2029-04-30'},
}
LTS_CODENAMES = {'argon': 4, 'boron': 6, 'carbon': 8, 'dubnium': 10, 'erbium': 12, 'fermium': 14,
                 'gallium': 16, 'hydrogen': 18, 'iron': 20, 'jod': 22, 'krypton': 24, 'lithium': 26}

# Packages that must move together: (anchor, partners, how strictly).
COUPLED = [
    ('react', ['react-dom'], 'exact'),
    ('react', ['@types/react', '@types/react-dom'], 'major'),
    ('next', ['eslint-config-next', '@next/eslint-plugin-next', '@next/bundle-analyzer'], 'major'),
    ('vitest', ['@vitest/coverage-v8', '@vitest/coverage-istanbul', '@vitest/ui', '@vitest/browser'], 'exact'),
    ('@playwright/test', ['playwright', 'playwright-core'], 'exact'),
    ('typescript-eslint', ['@typescript-eslint/parser', '@typescript-eslint/eslint-plugin'], 'exact'),
    ('tailwindcss', ['@tailwindcss/postcss', '@tailwindcss/vite', '@tailwindcss/cli'], 'major'),
    ('eslint', ['@eslint/js'], 'major'),
]
# Where the migration notes for a major live (references/frameworks.md sections).
FRAMEWORK_NOTES = {
    'next': 'Next.js', 'eslint-config-next': 'Next.js', 'react': 'React', 'react-dom': 'React',
    '@types/react': 'React', '@types/react-dom': 'React', 'vite': 'Vite', '@vitejs/plugin-react': 'Vite',
    'eslint': 'ESLint', '@eslint/js': 'ESLint', 'typescript-eslint': 'ESLint', 'vitest': 'Vitest',
    '@vitest/coverage-v8': 'Vitest', '@playwright/test': 'Playwright', 'playwright': 'Playwright',
    'tailwindcss': 'Tailwind CSS', '@tailwindcss/postcss': 'Tailwind CSS', 'typescript': 'TypeScript',
    '@types/node': 'Node.js', 'zod': 'Zod', 'drizzle-orm': 'Drizzle', 'drizzle-kit': 'Drizzle',
}
SKIP_DIRS = {'node_modules', '.next', '.git', 'dist', 'build', 'coverage', 'output'}


def run(cmd, cwd, timeout=120):
    """Run a command; never raises. Returns (rc, stdout, stderr); rc None on timeout/missing."""
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except FileNotFoundError as e:
        return None, '', str(e)
    except subprocess.TimeoutExpired:
        return None, '', f'timeout after {timeout}s'


# ---------- versions ----------

VER_RE = re.compile(r'^v?(\d+)(?:\.(\d+|x|\*))?(?:\.(\d+|x|\*))?(?:-([0-9A-Za-z.-]+))?')


def parse_version(s):
    """'1.2.3' -> (1, 2, 3, prerelease-or-None); None if unparsable."""
    m = VER_RE.match(str(s).strip())
    if not m:
        return None
    nums = [int(x) if x and x.isdigit() else 0 for x in m.group(1, 2, 3)]
    return nums[0], nums[1], nums[2], m.group(4)


def classify_update(locked, latest):
    """How far `locked` is behind `latest`: major / minor / patch / current."""
    a, b = parse_version(locked), parse_version(latest)
    if not a or not b:
        return 'unknown'
    if a[:3] >= b[:3]:
        return 'current'
    if a[0] != b[0]:
        return 'major'
    if a[1] != b[1]:
        return 'minor'
    return 'patch'


def newest_in_major(versions, major):
    best = None
    for v in versions:
        p = parse_version(v)
        if p and p[0] == major and not p[3] and (best is None or p[:3] > best[0]):
            best = (p[:3], v)
    return best[1] if best else None


# ---------- Node pins ----------

def node_major(spec):
    """Concrete Node major from '.nvmrc'-style text: '22', 'v24.14.0', 'lts/jod', 'node:24-alpine'."""
    s = str(spec).strip().lower()
    if s.startswith('lts/'):
        return LTS_CODENAMES.get(s[4:])
    m = re.match(r'^v?(\d+)', s)
    return int(m.group(1)) if m else None


def engine_intervals(spec):
    """Allowed Node major intervals for an engines range, e.g. '>=22 <23' -> [(22, 22)]."""
    out = []
    for clause in str(spec).split('||'):
        lo, hi = 0, 10 ** 6
        toks = re.findall(r'(>=|<=|>|<|\^|~|=)?\s*v?(\d+(?:\.(?:\d+|x|\*))*)', clause)
        if not toks:
            continue
        for op, ver in toks:
            parts = [int(p) if p.isdigit() else None for p in ver.split('.')]
            major = parts[0]
            rest_zero = all((p or 0) == 0 for p in parts[1:])
            if op in ('>=', '>'):
                lo = max(lo, major + (1 if op == '>' and len(parts) == 1 else 0))
            elif op == '<':
                hi = min(hi, major - 1 if rest_zero else major)
            elif op == '<=':
                hi = min(hi, major)
            else:  # ^ ~ = or bare
                lo, hi = max(lo, major), min(hi, major)
        if lo <= hi:
            out.append((lo, hi))
    return out


def engines_allow(spec, major):
    return any(lo <= major <= hi for lo, hi in engine_intervals(spec))


def parse_dockerfile(text):
    """Return FROM entries: {'stage', 'image', 'pinning', 'node_major', 'raw'} with ARG defaults resolved."""
    args, stages, out = {}, set(), []
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r'(?i)^ARG\s+([A-Za-z_][A-Za-z0-9_]*)(?:=(.*))?$', line)
        if m:
            if m.group(2) is not None:
                args[m.group(1)] = m.group(2).strip().strip('"\'')
            continue
        m = re.match(r'(?i)^FROM\s+(.*)$', line)
        if not m:
            continue
        toks = [t for t in m.group(1).split() if not t.startswith('--')]
        if not toks:
            continue
        raw = toks[0]
        image = re.sub(r'\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?', lambda x: args.get(x.group(1), x.group(0)), raw)
        alias = toks[2] if len(toks) >= 3 and toks[1].lower() == 'as' else None
        if image in stages:
            if alias:
                stages.add(alias)
            continue
        if alias:
            stages.add(alias)
        name, _, digest = image.partition('@')
        repo, tag = name, ''
        if ':' in name.rsplit('/', 1)[-1]:
            repo, tag = name.rsplit(':', 1)
        if '$' in image:
            pinning = 'unresolved'
        elif digest.startswith('sha256:'):
            pinning = 'digest'
        elif not tag or tag == 'latest':
            pinning = 'latest'
        else:
            pinning = 'tag'
        nm = node_major(tag) if repo.split('/')[-1] == 'node' and tag else None
        out.append({'stage': alias, 'image': image, 'repo': repo, 'tag': tag, 'pinning': pinning,
                    'node_major': nm, 'raw': raw})
    return out


def workflow_node_versions(repo_dir):
    found = []
    wf = repo_dir / '.github' / 'workflows'
    if wf.is_dir():
        for f in sorted(wf.glob('*.y*ml')):
            for m in re.finditer(r'node-version:\s*["\']?([\w./*-]+)', f.read_text(errors='replace')):
                found.append((f'{f.name}', m.group(1)))
    return found


def node_status(major, schedule, today):
    if major is None:
        return 'unknown'
    s = schedule.get(major)
    if not s:
        return 'unknown'
    d = lambda k: dt.date.fromisoformat(s[k]) if s.get(k) else None
    end, maint, lts = d('end'), d('maintenance'), d('lts')
    if end and today >= end:
        return 'eol'
    if maint and today >= maint:
        left = (end - today).days if end else None
        return f'maintenance, {left} days to EOL' if left is not None else 'maintenance'
    if lts and today >= lts:
        return 'active LTS'
    return 'current (not LTS yet)' if major % 2 == 0 else 'current (odd, never LTS)'


def days_to_eol(major, schedule, today):
    s = schedule.get(major) or {}
    return (dt.date.fromisoformat(s['end']) - today).days if s.get('end') else None


def load_schedule(offline):
    sched = {k: dict(v) for k, v in NODE_SCHEDULE.items()}
    if offline:
        return sched, 'built-in table (offline)'
    try:
        req = urllib.request.Request(SCHEDULE_URL, headers={'User-Agent': 'stratcore-survey'})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            data = json.load(r)
        for k, v in data.items():
            if re.fullmatch(r'v\d+', k):
                sched[int(k[1:])] = {x: v.get(x) for x in ('start', 'lts', 'maintenance', 'end')}
        return sched, 'nodejs/Release schedule.json (live)'
    except Exception as e:  # noqa: BLE001 - report, never fail
        return sched, f'built-in table (live fetch failed: {e.__class__.__name__})'


# ---------- lockfile / registry / audit ----------

def locked_versions(lock):
    """Map package name -> locked version from a package-lock v2/v3 (top-level installs only)."""
    out = {}
    for path, meta in (lock.get('packages') or {}).items():
        if path.startswith('node_modules/') and '/node_modules/' not in path[len('node_modules/'):]:
            if 'version' in meta:
                out[path[len('node_modules/'):]] = meta['version']
    if not out:  # lockfile v1
        for name, meta in (lock.get('dependencies') or {}).items():
            if 'version' in meta:
                out[name] = meta['version']
    return out


def fetch_registry(name):
    url = REGISTRY + urllib.parse.quote(name, safe='@').replace('/', '%2f')
    req = urllib.request.Request(url, headers={'Accept': 'application/vnd.npm.install-v1+json',
                                               'User-Agent': 'stratcore-survey'})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        d = json.load(r)
    return {'latest': d.get('dist-tags', {}).get('latest'), 'versions': d.get('versions', {})}


def registry_lookup(names, offline, fetch=fetch_registry):
    if offline:
        return {n: {'error': 'offline'} for n in names}
    out = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        futs = {pool.submit(fetch, n): n for n in names}
        for f in concurrent.futures.as_completed(futs):
            try:
                out[futs[f]] = f.result()
            except Exception as e:  # noqa: BLE001
                out[futs[f]] = {'error': f'{e.__class__.__name__}: {e}'[:120]}
    return out


def npm_audit(cwd, omit_dev, offline, runner=run):
    if offline:
        return {'error': 'offline'}
    cmd = ['npm', 'audit', '--package-lock-only', '--json'] + (['--omit=dev'] if omit_dev else [])
    rc, out, err = runner(cmd, str(cwd), 180)
    try:
        data = json.loads(out)
    except (ValueError, TypeError):
        return {'error': (err or out or f'rc={rc}').strip().splitlines()[-1][:160] if (err or out) else f'rc={rc}'}
    if 'error' in data:
        e = data['error']
        return {'error': (e.get('summary') if isinstance(e, dict) else str(e))[:160]}
    counts = (data.get('metadata') or {}).get('vulnerabilities') or {}
    serious = sorted(n for n, v in (data.get('vulnerabilities') or {}).items()
                     if v.get('severity') in ('high', 'critical'))
    return {'counts': {k: counts.get(k, 0) for k in ('critical', 'high', 'moderate', 'low')},
            'serious': serious}


# ---------- per project ----------

def git_info(d, runner=run):
    def g(*a):
        rc, out, _ = runner(['git', '--no-optional-locks', '-C', str(d)] + list(a), str(d), 30)
        return out.strip() if rc == 0 else None
    if g('rev-parse', '--is-inside-work-tree') != 'true':
        return {'repo': False}
    ab = g('rev-list', '--left-right', '--count', '@{u}...HEAD')
    behind, ahead = (ab.split() if ab else (None, None))
    status = g('status', '--porcelain')
    return {'repo': True, 'branch': g('rev-parse', '--abbrev-ref', 'HEAD'), 'head': g('rev-parse', '--short=12', 'HEAD'),
            'dirty': len(status.splitlines()) if status else 0, 'ahead': ahead, 'behind': behind,
            'last_commit': g('log', '-1', '--format=%cs')}


def coupled_drift(locked):
    issues = []
    for anchor, partners, mode in COUPLED:
        if anchor not in locked:
            continue
        a = parse_version(locked[anchor])
        for p in partners:
            if p not in locked:
                continue
            b = parse_version(locked[p])
            if not a or not b:
                continue
            bad = a[:3] != b[:3] if mode == 'exact' else a[0] != b[0]
            if bad:
                issues.append(f'{anchor} {locked[anchor]} vs {p} {locked[p]} ({mode} match expected)')
    return issues


def survey_project(key, d, meta, schedule, today, offline, registered=True, runner=run, fetch=fetch_registry):
    r = {'key': key, 'path': str(d), 'registered': registered, 'delivery': meta.get('delivery', ''),
         'findings': [], 'gaps': []}
    add = lambda level, text: r['findings'].append({'priority': level, 'text': text})
    pkg = json.loads((d / 'package.json').read_text())
    r['git'] = git_info(d, runner)

    locks = [n for n in ('package-lock.json', 'npm-shrinkwrap.json', 'pnpm-lock.yaml', 'yarn.lock', 'bun.lockb', 'bun.lock')
             if (d / n).exists()]
    pm_field = pkg.get('packageManager', '')
    pm = ('pnpm' if 'pnpm-lock.yaml' in locks else 'yarn' if 'yarn.lock' in locks
          else 'bun' if any(l.startswith('bun') for l in locks) else 'npm' if locks else (pm_field.split('@')[0] or 'none'))
    r['package_manager'] = {'tool': pm, 'lockfiles': locks, 'packageManager': pm_field}
    if len(locks) > 1:
        add('P2', f'mixed lockfiles: {", ".join(locks)}')
    if not locks:
        add('P2', 'no lockfile: installs are not reproducible')

    # Node pins
    pins = []
    for f in ('.nvmrc', '.node-version'):
        if (d / f).exists():
            v = (d / f).read_text().strip()
            pins.append({'source': f, 'value': v, 'major': node_major(v)})
    if isinstance(pkg.get('volta'), dict) and pkg['volta'].get('node'):
        pins.append({'source': 'package.json volta', 'value': pkg['volta']['node'], 'major': node_major(pkg['volta']['node'])})
    images = []
    for df in sorted(d.glob('Dockerfile*')):
        for e in parse_dockerfile(df.read_text(errors='replace')):
            e['file'] = df.name
            images.append(e)
            if e['node_major']:
                pins.append({'source': f'{df.name} {e["stage"] or "FROM"}', 'value': e['image'].split('@')[0], 'major': e['node_major']})
    for wf, v in workflow_node_versions(d):
        pins.append({'source': f'workflow {wf}', 'value': v, 'major': node_major(v)})
    engines = (pkg.get('engines') or {}).get('node')
    r['node'] = {'pins': pins, 'engines': engines}
    majors = sorted({p['major'] for p in pins if p['major']})
    if len(majors) > 1:
        add('P2', f'Node pins disagree: majors {majors} across {", ".join(p["source"] for p in pins)}')
    if engines:
        outside = [m for m in majors if not engines_allow(engines, m)]
        if outside:
            add('P2', f'engines.node "{engines}" excludes pinned major(s) {outside}')
        floors = [lo for lo, _ in engine_intervals(engines)]
        if majors and floors and min(floors) < min(majors):
            add('P3', f'engines.node "{engines}" still allows Node {min(floors)}, below the pinned {min(majors)}')
    if not pins:
        r['gaps'].append('no concrete Node pin (.nvmrc, Dockerfile node image or CI)')
    r['node']['status'] = {m: node_status(m, schedule, today) for m in majors}
    for m in majors:
        st, left = r['node']['status'][m], days_to_eol(m, schedule, today)
        if st == 'eol':
            add('P1', f'Node {m} is end-of-life')
        elif st.startswith('maintenance') and left is not None and left < 90:
            add('P2', f'Node {m} reaches end-of-life in {left} days')
        elif st.startswith('maintenance') and left is not None and left < 365:
            add('P3', f'Node {m} is in maintenance ({left} days to EOL); plan the move to the active LTS')
        elif 'odd' in st:
            add('P2', f'Node {m} is an odd release, never LTS')

    # Base images
    r['images'] = [{k: e[k] for k in ('file', 'stage', 'image', 'pinning')} for e in images]
    for e in images:
        if e['pinning'] == 'latest':
            add('P2', f'{e["file"]}: base image {e["image"]} floats on latest')
        elif e['pinning'] == 'tag':
            add('P4', f'{e["file"]}: base image {e["image"]} pinned by tag only (pin a digest)')
        elif e['pinning'] == 'unresolved':
            r['gaps'].append(f'{e["file"]}: base image {e["raw"]} could not be resolved from ARG defaults')

    # Dependencies
    deps = {n: 'runtime' for n in pkg.get('dependencies', {})}
    deps.update({n: 'dev' for n in pkg.get('devDependencies', {}) if n not in deps})
    locked = {}
    if 'package-lock.json' in locks:
        try:
            locked = locked_versions(json.loads((d / 'package-lock.json').read_text()))
        except ValueError:
            r['gaps'].append('package-lock.json is not valid JSON')
    elif locks:
        r['gaps'].append(f'{pm}: lockfile not parsed; locked versions taken from package.json ranges (registry lookups only)')
    info = registry_lookup(sorted(deps), offline, fetch)
    rows, reg_errors = [], []
    for n, kind in sorted(deps.items()):
        cur = locked.get(n) or re.sub(r'^[\^~>=<\s]+', '', str(pkg.get('dependencies', {}).get(n) or pkg.get('devDependencies', {}).get(n)))
        meta_n = info.get(n, {})
        if 'error' in meta_n:
            reg_errors.append(f'{n}: {meta_n["error"]}')
            continue
        latest = meta_n.get('latest')
        cur_v = parse_version(cur)
        wanted = newest_in_major(meta_n.get('versions', {}), cur_v[0]) if cur_v else None
        deprecated = (meta_n.get('versions', {}).get(cur) or {}).get('deprecated')
        if n == '@types/node' and majors and cur_v:
            # @types/node follows the oldest Node runtime the project supports, not npm "latest".
            target = min(majors)
            if cur_v[0] > target:
                add('P3', f'@types/node {cur} is ahead of the Node {target} runtime (types allow APIs production lacks)')
            latest = newest_in_major(meta_n.get('versions', {}), target) or latest
            wanted = newest_in_major(meta_n.get('versions', {}), min(cur_v[0], target)) or wanted
        rows.append({'name': n, 'kind': kind, 'locked': cur, 'wanted': wanted, 'latest': latest,
                     'update': classify_update(cur, latest), 'in_major': classify_update(cur, wanted) if wanted else 'unknown',
                     'deprecated': bool(deprecated)})
        if deprecated and kind == 'runtime':
            add('P2', f'runtime dependency {n}@{cur} is deprecated: {str(deprecated)[:100]}')
    if reg_errors:
        r['gaps'].append(f'registry lookup failed for {len(reg_errors)}/{len(deps)} packages (e.g. {reg_errors[0]})')
    r['dependencies'] = rows
    majors_behind = [x for x in rows if x['update'] == 'major']
    minor_patch = [x for x in rows if x['update'] in ('minor', 'patch') or x['in_major'] in ('minor', 'patch')]
    if majors_behind:
        add('P3', f'{len(majors_behind)} direct dependencies a major behind: ' +
            ', '.join(f'{x["name"]} {x["locked"]}→{x["latest"]}' for x in majors_behind[:8]) + (' …' if len(majors_behind) > 8 else ''))
    if minor_patch:
        add('P4', f'{len(minor_patch)} direct dependencies have patch/minor updates')
    for issue in coupled_drift(locked):
        add('P3', f'coupled packages out of step: {issue}')

    # Advisories
    if pm == 'npm':
        r['audit'] = {'all': npm_audit(d, False, offline, runner), 'runtime': npm_audit(d, True, offline, runner)}
        rt, al = r['audit']['runtime'], r['audit']['all']
        for label, a in (('runtime', rt), ('full', al)):
            if 'error' in a:
                r['gaps'].append(f'npm audit ({label}) unavailable: {a["error"]}')
        if 'counts' in rt and rt['counts']['critical'] + rt['counts']['high']:
            add('P1', f'runtime advisories: {rt["counts"]["critical"]} critical, {rt["counts"]["high"]} high ({", ".join(rt["serious"][:6])})')
        if 'counts' in al and 'counts' in rt:
            dev_serious = (al['counts']['critical'] + al['counts']['high']) - (rt['counts']['critical'] + rt['counts']['high'])
            if dev_serious > 0:
                add('P3', f'{dev_serious} high/critical advisories in dev-only packages')
            if al['counts']['moderate'] + al['counts']['low']:
                add('P4', f'{al["counts"]["moderate"]} moderate, {al["counts"]["low"]} low advisories (full tree)')
    else:
        r['audit'] = {}
        r['gaps'].append(f'{pm}: no lockfile-only audit available; run the package manager audit inside an upgrade worktree')

    seen, unique = set(), []
    for f in r['findings']:
        if f['text'] not in seen:
            seen.add(f['text'])
            unique.append(f)
    r['findings'] = unique
    order = {'P1': 1, 'P2': 2, 'P3': 3, 'P4': 4}
    r['findings'].sort(key=lambda f: order[f['priority']])
    r['priority'] = r['findings'][0]['priority'] if r['findings'] else 'OK'
    r['groups'] = suggest_groups(rows)
    return r


def suggest_groups(rows):
    safe = [x for x in rows if x['in_major'] in ('minor', 'patch')]
    groups = []
    if safe:
        groups.append({'name': 'safe batch (patch/minor within current major)',
                       'command': 'npm install ' + ' '.join(f'{x["name"]}@{x["wanted"]}' for x in safe),
                       'packages': [x['name'] for x in safe]})
    seen = set()
    for x in rows:
        if x['update'] != 'major':
            continue
        note = FRAMEWORK_NOTES.get(x['name'])
        key = note or x['name']
        if key in seen:
            continue
        seen.add(key)
        members = [y for y in rows if y['update'] == 'major' and (FRAMEWORK_NOTES.get(y['name']) or y['name']) == key]
        groups.append({'name': f'major: {key}', 'command': 'npm install ' + ' '.join(f'{y["name"]}@{y["latest"]}' for y in members),
                       'packages': [y['name'] for y in members],
                       'notes': f'references/frameworks.md § {note}' if note else 'read the package changelog / migration guide'})
    return groups


# ---------- discovery / output ----------

def discover(root, registered_paths):
    found = []
    for pj in sorted(root.glob('*/package.json')) + sorted(root.glob('*/*/package.json')):
        d = pj.parent
        rel = d.relative_to(root).parts
        if any(p.startswith('.') or p in SKIP_DIRS for p in rel) or d.resolve() in registered_paths:
            continue
        found.append(d)
    return found


def render_md(results, schedule_src, today):
    L = [f'# Dependency survey {today.isoformat()}', '',
         f'survey.py {SURVEY_VERSION} · read-only · Node schedule: {schedule_src}', '',
         '| Priority | Project | Branch / HEAD | Node | Advisories (runtime / full) | Majors behind | Gaps |',
         '|---|---|---|---|---|---|---|']
    for r in results:
        g = r['git']
        gitcol = f'{g.get("branch")} {g.get("head")}' + (f' dirty={g["dirty"]}' if g.get('dirty') else '') if g.get('repo') else 'not a git repo'
        node = ', '.join(f'{m} ({s})' for m, s in r['node']['status'].items()) or 'unpinned'
        def adv(a):
            if not a:
                return 'n/a'
            if 'error' in a:
                return 'unavailable'
            c = a['counts']
            return f'{c["critical"]}C {c["high"]}H {c["moderate"]}M {c["low"]}L'
        audit = f'{adv(r["audit"].get("runtime"))} / {adv(r["audit"].get("all"))}' if r['audit'] else 'n/a'
        majors = sum(1 for x in r['dependencies'] if x['update'] == 'major')
        name = r['key'] + ('' if r['registered'] else ' (unregistered)')
        L.append(f'| {r["priority"]} | {name} | {gitcol} | {node} | {audit} | {majors} | {len(r["gaps"])} |')
    L += ['', 'P1 act now · P2 fix in the next maintenance pass · P3 plan · P4 routine', '']
    for r in results:
        L += [f'## {r["key"]}' + ('' if r['registered'] else ' (unregistered)'), '',
              f'- Path: `{r["path"]}`' + (f' · delivery: {r["delivery"]}' if r['delivery'] else ''),
              f'- Package manager: {r["package_manager"]["tool"]} ({", ".join(r["package_manager"]["lockfiles"]) or "no lockfile"})',
              f'- Node pins: ' + ('; '.join(f'{p["source"]} = {p["value"]}' for p in r['node']['pins']) or 'none') +
              (f'; engines = {r["node"]["engines"]}' if r['node']['engines'] else ''),
              f'- Base images: ' + ('; '.join(f'{i["image"]} ({i["pinning"]})' for i in r['images']) or 'none'), '']
        if r['findings']:
            L += ['Findings:', ''] + [f'- **{f["priority"]}** {f["text"]}' for f in r['findings']] + ['']
        if r['groups']:
            L += ['Suggested groups (one commit each, in this order):', '']
            for gr in r['groups']:
                L.append(f'- {gr["name"]}: `{gr["command"]}`' + (f' — {gr["notes"]}' if gr.get('notes') else ''))
            L.append('')
        if r['gaps']:
            L += ['Data gaps (not evidence of "up to date"):', ''] + [f'- {x}' for x in r['gaps']] + ['']
    return '\n'.join(L) + '\n'


def main(argv=None):
    ap = argparse.ArgumentParser(description='Read-only dependency survey (nodejs-project-upgrade).')
    ap.add_argument('projects', nargs='*', help=f'registered keys ({", ".join(PROJECTS)}) or repo paths')
    ap.add_argument('--all', action='store_true', help='also survey unregistered package.json projects under --root')
    ap.add_argument('--root', default=DEFAULT_ROOT)
    ap.add_argument('--md', help='write the Markdown report here (default: stdout)')
    ap.add_argument('--json', help='also write the full JSON result here')
    ap.add_argument('--offline', action='store_true', help='no network: skip registry, audit and live schedule')
    ap.add_argument('--version', action='version', version=f'survey.py {SURVEY_VERSION}')
    a = ap.parse_args(argv)
    root = pathlib.Path(a.root)
    today = dt.date.today()
    targets = []
    for p in a.projects or list(PROJECTS):
        if p in PROJECTS:
            targets.append((p, root / PROJECTS[p]['repo'], PROJECTS[p], True))
        elif (pathlib.Path(p) / 'package.json').exists():
            targets.append((pathlib.Path(p).name, pathlib.Path(p), {}, False))
        else:
            print(f'Survey stopped: unknown project {p!r} (known: {", ".join(PROJECTS)})', file=sys.stderr)
            return 2
    if a.all:
        known = {t[1].resolve() for t in targets} | {(root / m['repo']).resolve() for m in PROJECTS.values()}
        targets += [(str(d.relative_to(root)), d, {}, False) for d in discover(root, known)]
    schedule, src = load_schedule(a.offline)
    results = []
    for key, d, meta, reg in targets:
        if not (d / 'package.json').exists():
            results.append({'key': key, 'path': str(d), 'error': 'package.json not found'})
            print(f'warning: {key}: package.json not found at {d}', file=sys.stderr)
            continue
        print(f'surveying {key} …', file=sys.stderr)
        results.append(survey_project(key, d, meta, schedule, today, a.offline, reg))
    ok = [r for r in results if 'error' not in r]
    md = render_md(ok, src, today)
    if a.md:
        pathlib.Path(a.md).write_text(md)
        print(f'Report: {a.md}', file=sys.stderr)
    else:
        sys.stdout.write(md)
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({'surveyVersion': SURVEY_VERSION, 'date': today.isoformat(),
                                                    'schedule': src, 'results': results}, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
