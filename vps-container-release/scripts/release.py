#!/usr/bin/env python3
"""Stratcore VPS releases: local build -> private GHCR -> digest-pinned Docker Compose.

Canonical copy lives in the vps-container-release skill (scripts/release.py).
Projects vendor it into ops/release.py; see references/config-schema.md.
"""
import argparse
import base64
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
import uuid

HELPER_VERSION = '2.0.1'
ROOT = Path(__file__).resolve().parents[1]
CONFIG = 'ops/release-config.json'
PLATFORM = 'linux/amd64'
DIGEST = re.compile(r'sha256:[0-9a-f]{64}')
REVISION = re.compile(r'[0-9a-f]{40}')
LONG_RUNNING = ('app', 'worker')


# ---------------------------------------------------------------- utilities

def run(args, *, capture=True, env=None, cwd=None, check=True):
    result = subprocess.run(args, cwd=cwd or ROOT, env={**os.environ, **(env or {})},
                            text=True, stdout=subprocess.PIPE if capture else None,
                            stderr=subprocess.PIPE if capture else None)
    if check and result.returncode:
        detail = (result.stderr or '').strip().splitlines()[-1:] if capture else []
        raise RuntimeError(f'{" ".join(str(a) for a in args[:3])} failed (exit {result.returncode})'
                           + (f': {detail[0][:300]}' if detail else ''))
    return result.stdout.strip() if capture else ''


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_name(path.name + '.tmp-' + uuid.uuid4().hex)
    with os.fdopen(os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as f:
        json.dump(value, f, indent=2)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(path)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


# ------------------------------------------------------------------- config

def validate_config(c):
    if c.get('schema') != 2:
        raise ValueError('release-config.json must be schema 2 (see references/onboarding.md)')
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]*', c['project']):
        raise ValueError('Invalid Compose project name')
    if not c.get('images'):
        raise ValueError('Config needs at least one image')
    for name, img in c['images'].items():
        if not re.fullmatch(r'[a-z0-9_]+', name):
            raise ValueError(f'Invalid image key {name!r}')
        if not c.get('rehearsal') and not re.fullmatch(r'ghcr\.io/[a-z0-9_-]+/[a-z0-9_.-]+', img['repository']):
            raise ValueError(f'Image {name}: expected a fixed ghcr.io/<owner>/<package> repository')
    if not long_running(c):
        raise ValueError('Config needs at least one app or worker service')
    for name, s in c['services'].items():
        if s.get('role') not in ('app', 'worker', 'job'):
            raise ValueError(f'Service {name}: role must be app, worker or job')
        if s.get('image') not in c['images']:
            raise ValueError(f'Service {name}: unknown image {s.get("image")!r}')
        if s['role'] in LONG_RUNNING and not s.get('container'):
            raise ValueError(f'Service {name}: container name required')
        port = s.get('port')
        if port is not None:
            if not isinstance(port.get('container'), int):
                raise ValueError(f'Service {name}: port.container must be an integer')
            if port.get('host') is not None and not (1 <= port['host'] <= 65535):
                raise ValueError(f'Service {name}: invalid host port')
    for f in c.get('envFiles', []):
        if f.startswith('/') or '..' in Path(f).parts:
            raise ValueError('envFiles must be relative to deployDir')
    if c.get('envFiles') and not c.get('deployDir'):
        raise ValueError('envFiles require deployDir')
    c.setdefault('composeFile', 'ops/compose.production.yml')
    c.setdefault('checks', [])
    c.setdefault('smoke', {})
    c.setdefault('legacyEnvironment', {})
    c.setdefault('productionHostname', 'n8n')
    return c


def long_running(c):
    return [n for n, s in c['services'].items() if s.get('role') in LONG_RUNNING]


def jobs(c):
    return [n for n, s in c['services'].items() if s.get('role') == 'job']


def bundle_files(c):
    return ['ops/release.py', CONFIG, c['composeFile']]


def image_env(c, refs):
    """Compose variables: RELEASE_IMAGE_<KEY>; single-image projects also get RELEASE_IMAGE."""
    env = {'RELEASE_IMAGE_' + k.upper(): v for k, v in refs.items()}
    if len(refs) == 1:
        env['RELEASE_IMAGE'] = next(iter(refs.values()))
    return env


def compose_base(c, compose_file, project_dir=None):
    args = ['docker', 'compose', '-p', c['project']]
    directory = project_dir or c.get('deployDir')
    if directory:
        args += ['--project-directory', str(directory)]
    return args + ['-f', str(compose_file)]


# ------------------------------------------------------------------- record

def ref_ok(c, name, ref):
    if c.get('rehearsal') and DIGEST.fullmatch(ref):
        return True
    prefix = c['images'][name]['repository'] + '@'
    return ref.startswith(prefix) and bool(DIGEST.fullmatch(ref[len(prefix):]))


def target_refs(record):
    return {k: v['image'] for k, v in record['images'].items()}


def ref_digest(ref):
    return ref.split('@')[-1]


def validate_record(record, c):
    if record.get('schema') != 2 or record.get('project') != c['project']:
        raise ValueError('Release record belongs to another project or schema')
    if record.get('source') != c['source'] or record.get('mode') != c.get('mode'):
        raise ValueError('Release record source or mode differs from config')
    if not REVISION.fullmatch(record.get('revision', '')) or record.get('platform') != PLATFORM:
        raise ValueError('Invalid release revision/platform')
    if set(record.get('images', {})) != set(c['images']):
        raise ValueError('Release record images differ from config')
    for name, img in record['images'].items():
        if not ref_ok(c, name, img.get('image', '')):
            raise ValueError(f'Image {name}: deployment requires the immutable GHCR digest')
        if img.get('visibility') != 'private':
            raise ValueError(f'Image {name}: private publication evidence missing')
    if set(record.get('bundleHashes', {})) != set(bundle_files(c)):
        raise ValueError('Incomplete release bundle hashes')
    for name, expected in record['bundleHashes'].items():
        if sha(ROOT / name) != expected:
            raise ValueError(f'Release bundle changed: {name}')
    return record


# ------------------------------------------------------------------- docker

def inspect_image(ref):
    return json.loads(run(['docker', 'image', 'inspect', ref]))[0]


def check_image(ref, revision, c, name):
    image = inspect_image(ref)
    labels = image['Config'].get('Labels') or {}
    if f"{image['Os']}/{image['Architecture']}" != PLATFORM:
        raise ValueError(f'Image {name} is not {PLATFORM}')
    if labels.get('org.opencontainers.image.revision') != revision:
        raise ValueError(f'Image {name}: source revision label mismatch')
    if labels.get('org.opencontainers.image.source') != c['source']:
        raise ValueError(f'Image {name}: source repository label mismatch')
    if c.get('modeLabel') and labels.get(c['modeLabel']) != c.get('mode'):
        raise ValueError(f'Image {name}: release mode label mismatch')
    return image


def inspect_container(name):
    out = subprocess.run(['docker', 'inspect', name], text=True, capture_output=True)
    if out.returncode:
        if re.search(r'no such (object|container)', out.stderr, re.I):
            return None
        raise RuntimeError(f'docker inspect {name} failed')
    return json.loads(out.stdout)[0]


def container_ok(data):
    health = data['State'].get('Health')
    if health is not None:
        return health.get('Status') == 'healthy'
    return bool(data['State'].get('Running'))


def published(data, container_port, stopped_ok):
    ports = (data.get('NetworkSettings') or {}).get('Ports') or {}
    bound = ports.get(f'{container_port}/tcp') or []
    if not bound and stopped_ok:
        bound = (data.get('HostConfig') or {}).get('PortBindings', {}).get(f'{container_port}/tcp') or []
    return bound


def any_published(data, stopped_ok):
    ports = (data.get('NetworkSettings') or {}).get('Ports') or {}
    if any(v for v in ports.values()):
        return True
    if stopped_ok:
        return any(v for v in ((data.get('HostConfig') or {}).get('PortBindings') or {}).values())
    return False


def current(c, expected, require_healthy=True):
    """Check every long-running service against config and the expected image IDs.

    expected maps service -> image ID, or None when the service must not exist yet.
    """
    found = {}
    for name in long_running(c):
        s = c['services'][name]
        want = expected.get(name, 'missing')
        if want == 'missing':
            raise ValueError(f'Expected identity missing for service {name}; re-run status')
        data = inspect_container(s['container'])
        if want is None:
            if data is not None:
                raise ValueError(f'{s["container"]} exists but the expected state says it does not')
            found[name] = None
            continue
        if not DIGEST.fullmatch(want):
            raise ValueError(f'Expected image ID for {name} is not sha256:...')
        if data is None or data['Image'] != want:
            raise ValueError(f'Current image of {name} changed; stop and re-review')
        if require_healthy and not container_ok(data):
            raise ValueError(f'{name} is not healthy/running; stop and re-review')
        labels = data['Config'].get('Labels') or {}
        if labels.get('com.docker.compose.project') != c['project']:
            raise ValueError(f'{name}: Compose project mismatch')
        if labels.get('com.docker.compose.service') != name:
            raise ValueError(f'{name}: Compose service mismatch')
        port = s.get('port')
        if port and port.get('host') is not None:
            got = published(data, port['container'], not require_healthy)
            if got != [{'HostIp': '127.0.0.1', 'HostPort': str(port['host'])}]:
                raise ValueError(f'{name}: published port is not 127.0.0.1:{port["host"]}')
        elif any_published(data, not require_healthy):
            raise ValueError(f'{name}: publishes a port the config does not declare')
        mounts = sorted((m['Type'], m['Destination']) for m in data.get('Mounts', [])
                        if m['Type'] in ('bind', 'volume'))
        declared = sorted((m['type'], m['target']) for m in s.get('mounts', []))
        if mounts != declared:
            raise ValueError(f'{name}: persistent mounts {mounts} differ from config {declared}')
        found[name] = data
    return found


def status_snapshot(c):
    services = {}
    for name in long_running(c):
        data = inspect_container(c['services'][name]['container'])
        services[name] = None if data is None else {
            'imageId': data['Image'],
            'running': bool(data['State'].get('Running')),
            'health': (data['State'].get('Health') or {}).get('Status'),
            'composeProject': (data['Config'].get('Labels') or {}).get('com.docker.compose.project'),
        }
    return {'schema': 2, 'project': c['project'], 'host': platform.node(),
            'capturedAt': now(), 'helperVersion': HELPER_VERSION, 'services': services}


def expected_ids(snapshot, c):
    if snapshot.get('project') != c['project']:
        raise ValueError('Expected-state file belongs to another project')
    return {n: (v or {}).get('imageId') if v else None for n, v in snapshot['services'].items()}


def check_env_files(c):
    found = {}
    for rel in c.get('envFiles', []):
        path = Path(c['deployDir']) / rel
        if not path.is_file():
            raise ValueError(f'Runtime env file missing: {path}')
        if path.stat().st_mode & 0o077:
            raise ValueError(f'Runtime env file must be chmod 600: {path}')
        found[rel] = sha(path)  # hash only, never values
    return found


# --------------------------------------------------- derived compose models

def derive_compose(c, refs, workdir, project, *, names, ports):
    """Turn the production compose file into an isolated local model.

    names: 'prefixed' sets container_name to <project>-<service>; 'auto' drops it.
    ports: dict service -> host port (int) or 'ephemeral'; others lose published ports.
    """
    workdir = Path(workdir)
    for rel in c.get('envFiles', []):
        stub = workdir / rel
        stub.parent.mkdir(parents=True, exist_ok=True)
        stub.write_text(''.join(f'{k}={v}\n' for k, v in c['smoke'].get('env', {}).items()))
        stub.chmod(0o600)
    model = json.loads(run(['docker', 'compose', '-p', project, '--project-directory', str(workdir),
                            '-f', str(ROOT / c['composeFile']), '--profile', '*', 'config', '--format', 'json'],
                           env=image_env(c, refs)))
    model['name'] = project
    keep = set(c['services'])
    for name in list(model.get('services', {})):
        if name not in keep:
            model['services'].pop(name)
    for name, svc in model['services'].items():
        if 'build' in svc:
            raise ValueError(f'Production compose service {name} must not have a build section')
        svc.pop('container_name', None)
        svc['platform'] = PLATFORM
        if names == 'prefixed':
            svc['container_name'] = f'{project}-{name}'
        if svc.get('image') != refs[c['services'][name]['image']]:
            raise ValueError(f'Compose service {name} must use ${{RELEASE_IMAGE_{c["services"][name]["image"].upper()}}}')
        mapped = []
        port_cfg = c['services'][name].get('port')
        if name in ports and port_cfg:
            entry = {'target': port_cfg['container'], 'host_ip': '127.0.0.1', 'protocol': 'tcp'}
            if ports[name] != 'ephemeral':
                entry['published'] = str(ports[name])
            mapped.append(entry)
        svc['ports'] = mapped
        # Derived networks are throwaway and have no configured subnet, so a static address from the
        # production compose file (e.g. a fixed IP on a proxy network) would make Compose refuse to start.
        for attachment in (svc.get('networks') or {}).values():
            if isinstance(attachment, dict):
                for key in ('ipv4_address', 'ipv6_address'):
                    attachment.pop(key, None)
    for extra, svc in c['smoke'].get('extraServices', {}).items():
        model['services'][extra] = svc
    for key in ('networks', 'volumes'):
        for name in list(model.get(key, {}) or {}):
            model[key][name] = {}
    path = workdir / 'compose.derived.json'
    path.write_text(json.dumps(model, indent=2))
    return path


def wait_http(url, timeout):
    deadline = time.monotonic() + timeout
    while True:
        try:
            with urllib.request.urlopen(url, timeout=10) as res:
                return res
        except (urllib.error.URLError, ConnectionError, OSError):
            if time.monotonic() > deadline:
                raise RuntimeError(f'Smoke URL never answered: {url}')
            time.sleep(1)


def smoke(c, refs, build_infos):
    sm = c['smoke']
    project = c['project'] + '-smoke-' + uuid.uuid4().hex[:8]
    workdir = Path(tempfile.mkdtemp(prefix='release-smoke-'))
    service = sm.get('service') or next((n for n in long_running(c) if c['services'][n].get('port')), None)
    ports = {service: 'ephemeral'} if service else {}
    compose = derive_compose(c, refs, workdir, project, names='auto', ports=ports)
    base = ['docker', 'compose', '-p', project, '--project-directory', str(workdir), '-f', str(compose)]
    env = image_env(c, refs)
    timeout = str(sm.get('timeout', 120))
    try:
        extras = list(sm.get('extraServices', {}))
        if extras:
            run(base + ['up', '-d', '--wait', '--wait-timeout', timeout] + extras, capture=False, env=env)
        if sm.get('runJobs'):
            for job in jobs(c):
                profile = c['services'][job].get('profile')
                run(base + (['--profile', profile] if profile else []) + ['run', '--rm', job], capture=False, env=env)
        run(base + ['up', '-d', '--no-build', '--pull', 'never', '--wait', '--wait-timeout', timeout]
            + long_running(c), capture=False, env=env)
        if service:
            address = run(base + ['port', service, str(c['services'][service]['port']['container'])], env=env)
            if not re.fullmatch(r'127\.0\.0\.1:\d+', address):
                raise ValueError('Smoke port must be loopback-only')
            for path in sm.get('paths', []):
                res = wait_http('http://' + address + path, int(timeout))
                if res.status != 200:
                    raise RuntimeError(f'Smoke HTTP {path} returned {res.status}')
            info = build_infos.get(c['services'][service]['image'])
            if info is not None:
                with urllib.request.urlopen('http://' + address + '/version.json', timeout=10) as res:
                    if res.headers.get('Cache-Control') != 'no-store' or json.load(res) != info:
                        raise ValueError('Served /version.json differs from the release build object')
        for check in sm.get('execChecks', []):
            run(base + ['exec', '-T', check['service']] + check['command'], env=env)
        if sm.get('containerTest'):
            run(sm['containerTest'] + [refs[c['services'][service]['image']] if service else ''], capture=False)
    finally:
        run(base + ['down', '-v', '--timeout', '5'], env=env, check=False)
        shutil.rmtree(workdir, ignore_errors=True)


# ------------------------------------------------------------- build/publish

def build(c, output):
    if platform.node() == c['productionHostname']:
        raise ValueError('Build on the workstation, not on the VPS')
    context = json.loads(run(['docker', 'context', 'inspect']))[0]
    if not context['Endpoints']['docker']['Host'].startswith(('unix://', 'npipe://')) or os.environ.get('DOCKER_HOST'):
        raise ValueError('Use a local Docker context for release builds')
    if run(['git', 'status', '--porcelain', '--untracked-files=all']):
        raise ValueError('Build requires a clean committed checkout, including untracked files')
    revision = run(['git', 'rev-parse', 'HEAD'])
    if Path(output).exists():
        raise ValueError('Output record already exists; use a new path per candidate')
    for command in c['checks']:
        run(command, capture=False, env={'CI': 'true'})
    if run(['git', 'status', '--porcelain', '--untracked-files=all']):
        raise ValueError('Checks changed the source checkout')
    commit_time = run(['git', 'show', '-s', '--format=%cI', 'HEAD'])
    images, refs, infos = {}, {}, {}
    built_at = now()
    for name, img in c['images'].items():
        tag = img['repository'] + ':sha-' + revision
        created = commit_time
        args = ['docker', 'buildx', 'build', '--platform', PLATFORM, '--load',
                '--provenance=false', '--sbom=false', '-t', tag,
                '-f', img.get('dockerfile', 'Dockerfile')]
        if img.get('buildMetadata'):
            created = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
            infos[name] = {'version': read(ROOT / 'package.json')['version'], 'commit': revision, 'builtAt': created}
            args += ['--build-arg', 'APP_RELEASE_BUILD=1', '--build-arg', 'APP_COMMIT=' + revision,
                     '--build-arg', 'APP_BUILD_TIME=' + created]
        for key, value in (img.get('buildArgs') or {}).items():
            args += ['--build-arg', f'{key}={value}']
        if img.get('target'):
            args += ['--target', img['target']]
        for key, value in {'source': c['source'], 'revision': revision, 'created': created,
                           'version': 'sha-' + revision, 'title': f'{c["project"]}-{name}',
                           'url': c['source']}.items():
            args += ['--label', f'org.opencontainers.image.{key}={value}']
        run(args + [img.get('context', '.')], capture=False)
        images[name] = {'tag': tag, 'localImageId': check_image(tag, revision, c, name)['Id']}
        if name in infos:
            images[name]['buildInfo'] = infos[name]
        refs[name] = tag
    smoke(c, refs, infos)
    record = {'schema': 2, 'helperVersion': HELPER_VERSION, 'project': c['project'],
              'revision': revision, 'source': c['source'], 'platform': PLATFORM,
              'mode': c.get('mode'), 'builtAt': built_at, 'buildCompletedAt': now(),
              'checksPassed': c['checks'], 'smokePassed': True, 'images': images,
              'bundleHashes': {n: sha(ROOT / n) for n in bundle_files(c)}}
    write(output, record)
    print(json.dumps(record, indent=2))


def ghcr_token():
    cfg = read(Path(os.environ.get('DOCKER_CONFIG', Path.home() / '.docker')) / 'config.json')
    helper = cfg.get('credHelpers', {}).get('ghcr.io') or cfg.get('credsStore')
    if helper:
        binary = shutil.which('docker-credential-' + helper)
        if not binary:
            raise ValueError('Docker credential helper unavailable')
        result = subprocess.run([binary, 'get'], input='ghcr.io\n', text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return json.loads(result.stdout)['Secret']
    auth = cfg.get('auths', {}).get('ghcr.io', {}).get('auth', '')
    if not auth:
        raise ValueError('No ghcr.io credential in Docker config; run docker login ghcr.io')
    return base64.b64decode(auth).decode().split(':', 1)[1]


def registry_visibility(repository, missing_ok=False):
    """Use only the configured GHCR credential; never print it."""
    token = ghcr_token()
    owner, package = repository.split('/')[1:]
    headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
               'X-GitHub-Api-Version': '2022-11-28'}
    with urllib.request.urlopen(urllib.request.Request('https://api.github.com/user', headers=headers), timeout=30) as res:
        if json.load(res)['login'].lower() != owner:
            raise ValueError('GHCR credential account differs from the image namespace')
    url = f'https://api.github.com/users/{owner}/packages/container/{package}'
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as res:
            visibility = json.load(res)['visibility']
    except urllib.error.HTTPError as error:
        if error.code == 404 and missing_ok:
            return None
        raise
    if visibility != 'private':
        raise ValueError(f'{repository} is not private; stop publication')
    return visibility


def publish(c, path):
    record = read(path)
    if record.get('project') != c['project'] or not record.get('smokePassed'):
        raise ValueError('Wrong project or missing smoke evidence')
    if any(img.get('image') for img in record['images'].values()):
        raise ValueError('Release already published; do not overwrite evidence')
    if run(['git', 'rev-parse', 'HEAD']) != record['revision'] or run(['git', 'status', '--porcelain']):
        raise ValueError('Publish from the unchanged release checkout')
    branch = run(['git', 'branch', '--show-current'])
    remote = run(['git', 'ls-remote', '--exit-code', 'origin', 'refs/heads/' + branch]).split()[0]
    if remote != record['revision']:
        raise ValueError('Push the reviewed source commit before publishing its image')
    for name, img in record['images'].items():
        if check_image(img['tag'], record['revision'], c, name)['Id'] != img['localImageId']:
            raise ValueError(f'Local image {name} changed since testing')
        if registry_visibility(c['images'][name]['repository'], missing_ok=True) is not None:
            probe = subprocess.run(['docker', 'buildx', 'imagetools', 'inspect', img['tag']],
                                   text=True, capture_output=True)
            if probe.returncode == 0:
                raise ValueError(f'{img["tag"]} already exists; never overwrite a release tag')
            if not re.search(r'not found|manifest unknown|404', probe.stderr, re.I):
                raise RuntimeError('Cannot establish tag absence; check GHCR authentication')
    for name, img in record['images'].items():
        run(['docker', 'push', img['tag']], capture=False)
        desc = run(['docker', 'buildx', 'imagetools', 'inspect', img['tag']])
        match = re.search(r'^Digest:\s+(sha256:[0-9a-f]{64})\s*$', desc, re.M)
        if not match:
            raise ValueError('Registry did not return an immutable digest')
        img['image'] = c['images'][name]['repository'] + '@' + match[1]
        img['visibility'] = 'unverified'
        img['publishedAt'] = now()
        write(path, record)
        img['visibility'] = registry_visibility(c['images'][name]['repository'])
        write(path, record)
    print(json.dumps(record, indent=2))


def bundle(c, path):
    record = read(path)
    validate_record(record, c)
    out = ROOT / '.releases' / f'bundle-{record["revision"][:12]}.tar'
    if out.exists():
        raise ValueError(f'{out} exists; keep prior bundles')
    manifest = ''.join(f'{sha(ROOT / n)}  {n}\n' for n in bundle_files(c))
    manifest += f'{sha(path)}  release.json\n'
    out.parent.mkdir(exist_ok=True)
    with tarfile.open(out, 'w') as tar:
        for n in bundle_files(c):
            tar.add(ROOT / n, arcname=n)
        tar.add(path, arcname='release.json')
        data = manifest.encode()
        info = tarfile.TarInfo('MANIFEST.sha256'); info.size = len(data); info.mtime = int(time.time())
        import io
        tar.addfile(info, io.BytesIO(data))
    print(json.dumps({'bundle': str(out), 'sha256': sha(out),
                      'vpsDirectory': f'/root/release-preparation/{c["project"]}/{record["revision"]}/'}, indent=2))


# --------------------------------------------------------------- production

def status(c, output):
    snap = status_snapshot(c)
    if output:
        if Path(output).exists():
            raise ValueError(f'{output} exists; write a fresh status file')
        write(output, snap)
    print(json.dumps(snap, indent=2))


def preflight(c, record, expected_file):
    validate_record(record, c)
    expected = expected_ids(read(expected_file), c)
    current(c, expected)
    for name, ref in target_refs(record).items():
        if not c.get('rehearsal'):
            run(['docker', 'pull', '--platform', PLATFORM, ref], capture=False)
        check_image(ref, record['revision'], c, name)
    env_hashes = check_env_files(c)
    run(compose_base(c, ROOT / c['composeFile']) + ['config', '--quiet'], env=image_env(c, target_refs(record)))
    print(json.dumps({'status': 'preflight passed; no container changed', 'current': expected,
                      'target': target_refs(record), 'envFiles': sorted(env_hashes)}, indent=2))


def approve(record, approved):
    wanted = {ref_digest(r) for r in target_refs(record).values()}
    if set(approved or []) != wanted:
        raise ValueError('Approval must name exactly the target digest(s): ' + ', '.join(sorted(wanted)))


def migrate(c, record, expected_file, approved, backup_ref, no_schema_change, state_root):
    validate_record(record, c)
    approve(record, approved)
    if not jobs(c):
        raise ValueError('Config declares no job service')
    if bool(backup_ref) == bool(no_schema_change):
        raise ValueError('Give exactly one of --backup-ref or --no-schema-change')
    current(c, expected_ids(read(expected_file), c))
    check_env_files(c)
    refs = target_refs(record)
    log = Path(state_root).resolve() / 'migrations' / f'{stamp()}-{record["revision"][:12]}.json'
    entry = {'project': c['project'], 'revision': record['revision'], 'targets': refs,
             'backupRef': backup_ref, 'noSchemaChange': bool(no_schema_change),
             'startedAt': now(), 'status': 'running'}
    write(log, entry)
    try:
        for job in jobs(c):
            check_image(refs[c['services'][job]['image']], record['revision'], c, job)
            profile = c['services'][job].get('profile')
            run(compose_base(c, ROOT / c['composeFile']) + (['--profile', profile] if profile else [])
                + ['run', '--rm', '--no-deps', job], capture=False, env=image_env(c, refs))
        entry['status'] = 'completed'
    except Exception:
        entry['status'] = 'failed'
        raise
    finally:
        entry['finishedAt'] = now()
        write(log, entry)
    print('Migration record: ' + str(log))


def migrations_for(state_root, record):
    directory = Path(state_root) / 'migrations'
    if not directory.is_dir():
        return []
    found = []
    for p in sorted(directory.glob('*.json')):
        m = read(p)
        if m.get('revision') == record['revision'] and m.get('status') == 'completed':
            found.append({'file': str(p), 'noSchemaChange': m['noSchemaChange'], 'backupRef': m['backupRef']})
    return found


def capture_previous(c, found, directory):
    existing = {n: d for n, d in found.items() if d is not None}
    if not existing:
        return None, None
    labels = next(iter(existing.values()))['Config']['Labels']
    files = labels['com.docker.compose.project.config_files'].split(',')
    workdir = labels.get('com.docker.compose.project.working_dir')
    for d in existing.values():
        if d['Config']['Labels']['com.docker.compose.project.config_files'].split(',') != files:
            raise ValueError('Services were started from different compose files; capture manually')
    args = ['docker', 'compose', '-p', c['project']]
    if workdir:
        args += ['--project-directory', workdir]
    for f in files:
        args += ['-f', f]
    refs = {}
    for n, d in existing.items():
        refs.setdefault(c['services'][n]['image'], d['Image'])
    for k in c['images']:
        refs.setdefault(k, 'unused')
    model = json.loads(run(args + ['config', '--format', 'json', '--no-env-resolution'],
                           env={**c['legacyEnvironment'], **image_env(c, refs)}))
    for n, d in existing.items():
        if n not in model.get('services', {}):
            raise ValueError(f'Previous compose model lacks service {n}')
        model['services'][n]['image'] = d['Image']
        model['services'][n].pop('build', None)
    write(directory / 'previous-compose.json', model)
    return sha(directory / 'previous-compose.json'), workdir


def compose_up(c, compose_file, refs, services, project_dir=None):
    run(compose_base(c, compose_file, project_dir) + ['up', '-d', '--no-build', '--pull', 'never',
        '--no-deps', '--wait', '--wait-timeout', '120'] + services, capture=False, env=image_env(c, refs))


def lock(state_root):
    root = Path(state_root).resolve()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    handle = (root / '.deployment-lock').open('a')
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise RuntimeError('Another release operation holds the deployment lock')
    return handle


def deploy(c, record, expected_file, approved, state_root):
    validate_record(record, c)
    approve(record, approved)
    expected = expected_ids(read(expected_file), c)
    refs = target_refs(record)
    found = current(c, expected)
    targets = {k: check_image(refs[k], record['revision'], c, k)['Id'] for k in c['images']}
    env_hashes = check_env_files(c)
    services = long_running(c)
    with lock(state_root):
        found = current(c, expected)
        directory = Path(state_root).resolve() / f'{stamp()}-{record["revision"][:12]}'
        directory.mkdir(mode=0o700)
        prev_sha, prev_dir = capture_previous(c, found, directory)
        ran = migrations_for(state_root, record)
        state = {'schema': 2, 'helperVersion': HELPER_VERSION, 'project': c['project'],
                 'revision': record['revision'], 'targetImages': refs,
                 'targetImageIds': {n: targets[c['services'][n]['image']] for n in services},
                 'previousImageIds': {n: (d['Image'] if d else None) for n, d in found.items()},
                 'containers': {n: c['services'][n]['container'] for n in services},
                 'previousComposeSha256': prev_sha, 'previousProjectDir': prev_dir,
                 'envFileHashes': env_hashes, 'migrations': ran,
                 'migrationRan': any(not m['noSchemaChange'] for m in ran),
                 'startedAt': now(), 'status': 'prepared'}
        write(directory / 'state.json', state)
        try:
            compose_up(c, ROOT / c['composeFile'], refs, services)
            for n in services:
                data = inspect_container(c['services'][n]['container'])
                if data is None or data['Image'] != state['targetImageIds'][n] or not container_ok(data):
                    raise RuntimeError(f'Post-deployment check failed for {n}')
            state['status'] = 'deployed'
        except Exception:
            state['status'] = 'deployment-failed; rollback required'
            print('Deployment failed. State: ' + str(directory), file=sys.stderr)
            raise
        finally:
            state['finishedAt'] = now()
            write(directory / 'state.json', state)
    print('Deployment state: ' + str(directory))


def rollback(c, directory, approved, approve_removal, schema_compatible):
    directory = Path(directory).resolve()
    state = read(directory / 'state.json')
    if state.get('schema') != 2:
        raise ValueError('Not a v2 state; roll back with the release.py from that release bundle')
    if state['project'] != c['project']:
        raise ValueError('Rollback state belongs to another project')
    previous = {n: i for n, i in state['previousImageIds'].items() if i}
    new_only = [n for n, i in state['previousImageIds'].items() if not i]
    if set(approved or []) != set(previous.values()):
        raise ValueError('Approval must name exactly the previous image ID(s): ' + ', '.join(sorted(set(previous.values()))))
    if new_only and not approve_removal:
        raise ValueError(f'Services {new_only} had no previous release; pass --approve-removal to remove them')
    if state.get('migrationRan') and not schema_compatible:
        raise ValueError('A migration ran for this release. An image rollback does not undo it. '
                         'Pass --schema-compatible only after the owner confirms the old version works on the new schema.')
    if previous and sha(directory / 'previous-compose.json') != state['previousComposeSha256']:
        raise ValueError('Captured rollback configuration changed')
    with lock(directory.parent):
        current(c, state['targetImageIds'], require_healthy=False)
        for image in previous.values():
            inspect_image(image)
        if previous:
            compose_up(c, directory / 'previous-compose.json', {}, sorted(previous),
                       project_dir=state.get('previousProjectDir'))
        for n in new_only:
            run(['docker', 'rm', '-f', state['containers'][n]])
        for n, image in previous.items():
            data = inspect_container(c['services'][n]['container'])
            if data is None or data['Image'] != image or not container_ok(data):
                raise RuntimeError(f'Rollback check failed for {n}')
        state['status'] = 'rolled-back'
        state['rolledBackAt'] = now()
        state['schemaCompatibleConfirmed'] = bool(schema_compatible)
        write(directory / 'state.json', state)
    print('Rolled back: ' + str(directory))


# ---------------------------------------------------------------- rehearsal

def rehearse(c, target_path, previous_specs):
    """Deploy -> stop -> rollback against throwaway Docker Desktop projects. Never the VPS."""
    if platform.node() == c['productionHostname']:
        raise ValueError('Rehearse on the workstation only')
    if run(['docker', 'context', 'show']) != 'desktop-linux':
        raise ValueError('Rehearsal requires the desktop-linux Docker context')
    target = read(target_path)
    if target.get('project') != c['project'] or not target.get('smokePassed'):
        raise ValueError('Target record must be a smoke-tested build of this project')
    previous = {}
    for spec in previous_specs or []:
        key, _, ref = spec.partition('=')
        if key not in c['images'] or not ref:
            raise ValueError('--previous takes IMAGE_KEY=REF')
        if subprocess.run(['docker', 'image', 'inspect', ref], capture_output=True).returncode:
            run(['docker', 'pull', '--platform', PLATFORM, ref], capture=False)
        previous[key] = inspect_image(ref)['Id']
    if set(previous) != set(c['images']):
        raise ValueError('Give --previous for every image key: ' + ', '.join(c['images']))
    tmp = Path(tempfile.mkdtemp(prefix='release-rehearsal-'))
    project = c['project'] + '-rehearsal-' + uuid.uuid4().hex[:6]
    deploy_dir = tmp / 'deploy'
    deploy_dir.mkdir()
    services = long_running(c)
    ports = {n: free_port() for n in services
             if c['services'][n].get('port') and c['services'][n]['port'].get('host') is not None}
    prev_compose = derive_compose(c, previous, deploy_dir, project, names='prefixed', ports=ports)
    model = json.loads(prev_compose.read_text())
    for n, svc in model['services'].items():
        if n in c['services']:
            svc['image'] = '${RELEASE_IMAGE_' + c['services'][n]['image'].upper() + '}'
    (tmp / 'ops').mkdir()
    (tmp / 'ops/compose.production.yml').write_text(json.dumps(model, indent=2))
    shutil.copy2(Path(__file__), tmp / 'ops/release.py')
    rc = json.loads(json.dumps(c))
    rc.update({'project': project, 'rehearsal': True, 'deployDir': str(deploy_dir),
               'composeFile': 'ops/compose.production.yml', 'legacyEnvironment': {}})
    for n in services:
        rc['services'][n]['container'] = f'{project}-{n}'
        if n in ports:
            rc['services'][n]['port']['host'] = ports[n]
    (tmp / CONFIG).write_text(json.dumps(rc, indent=2))
    record = {**target, 'project': project,
              'images': {k: {**v, 'image': v['localImageId'], 'visibility': 'private'}
                         for k, v in target['images'].items()},
              'bundleHashes': {n: sha(tmp / n) for n in bundle_files(rc)}}
    write(tmp / 'release.json', record)
    result = {'project': c['project'], 'scope': 'temporary Docker Desktop project only',
              'productionTouched': False, 'helperVersion': HELPER_VERSION,
              'targetRevision': target['revision'], 'previous': previous, 'startedAt': now()}
    tool = ['python3', str(tmp / 'ops/release.py')]
    states = tmp / 'states'
    base = ['docker', 'compose', '-p', project, '--project-directory', str(deploy_dir),
            '-f', str(tmp / 'ops/compose.production.yml')]
    try:
        extras = list(c['smoke'].get('extraServices', {}))
        run(base + ['up', '-d', '--no-build', '--pull', 'never', '--wait', '--wait-timeout', '120']
            + extras + services, capture=False, env=image_env(c, previous))
        run(tool + ['status', '--output', str(tmp / 'current.json')], cwd=tmp)
        run(tool + ['preflight', '--record', 'release.json', '--expected', 'current.json'], cwd=tmp)
        result['preflightPassed'] = True
        approvals = []
        for d in {r['localImageId'] for r in target['images'].values()}:
            approvals += ['--approve-digest', d]
        if jobs(c):
            run(tool + ['migrate', '--record', 'release.json', '--expected', 'current.json',
                        '--backup-ref', 'rehearsal-no-backup', '--state-root', str(states)] + approvals, cwd=tmp)
            result['migratePassed'] = True
        run(tool + ['deploy', '--record', 'release.json', '--expected', 'current.json',
                    '--state-root', str(states)] + approvals, cwd=tmp)
        state_dir = next(p for p in states.iterdir() if p.is_dir() and p.name != 'migrations')
        if read(state_dir / 'state.json')['status'] != 'deployed':
            raise RuntimeError('Deploy did not reach deployed status')
        result['deploymentPassed'] = True
        run(['docker', 'stop', '-t', '2', f'{project}-{services[0]}'])
        back = []
        for i in sorted({previous[c['services'][n]['image']] for n in services}):
            back += ['--approve-image-id', i]
        if jobs(c):
            refused = subprocess.run(tool + ['rollback', '--state', str(state_dir)] + back,
                                     cwd=tmp, capture_output=True, text=True)
            if refused.returncode == 0:
                raise RuntimeError('Rollback after a migration ran without --schema-compatible')
            result['migrationGateEnforced'] = True
            back.append('--schema-compatible')
        run(tool + ['rollback', '--state', str(state_dir)] + back, cwd=tmp)
        for n in services:
            data = inspect_container(f'{project}-{n}')
            if data['Image'] != previous[c['services'][n]['image']] or not container_ok(data):
                raise RuntimeError(f'Rollback did not restore {n}')
        result['rollbackFromStoppedTargetPassed'] = True
    except Exception as exc:
        result['failure'] = f'{type(exc).__name__}: {exc}'
    finally:
        down = subprocess.run(base + ['down', '-v', '--timeout', '5'], capture_output=True,
                              env={**os.environ, **image_env(c, previous)})
        result['fixtureCleanupPassed'] = down.returncode == 0
        if down.returncode == 0:
            shutil.rmtree(tmp, ignore_errors=True)
        else:
            result['remainingFixturePath'] = str(tmp)
        result['finishedAt'] = now()
        write(ROOT / '.releases' / f'rehearsal-{stamp()}.json', result)
        print(json.dumps(result, indent=2))
    if not result.get('rollbackFromStoppedTargetPassed'):
        sys.exit(1)


# --------------------------------------------------------------------- main

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', action='version', version=HELPER_VERSION)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('status', help='VPS, read-only: write current identities')
    p.add_argument('--output')
    for name in ('build', 'publish', 'bundle'):
        sub.add_parser(name).add_argument('--record', required=True)
    p = sub.add_parser('preflight'); p.add_argument('--record', required=True); p.add_argument('--expected', required=True)
    p = sub.add_parser('migrate')
    p.add_argument('--record', required=True); p.add_argument('--expected', required=True)
    p.add_argument('--approve-digest', action='append', required=True)
    p.add_argument('--backup-ref'); p.add_argument('--no-schema-change', action='store_true')
    p.add_argument('--state-root', required=True)
    p = sub.add_parser('deploy')
    p.add_argument('--record', required=True); p.add_argument('--expected', required=True)
    p.add_argument('--approve-digest', action='append', required=True)
    p.add_argument('--state-root', required=True)
    p = sub.add_parser('rollback')
    p.add_argument('--state', required=True)
    p.add_argument('--approve-image-id', action='append')
    p.add_argument('--approve-removal', action='store_true')
    p.add_argument('--schema-compatible', action='store_true')
    p = sub.add_parser('rehearse', help='Docker Desktop only')
    p.add_argument('--target-record', required=True)
    p.add_argument('--previous', action='append', help='IMAGE_KEY=REF, repeat per image')
    a = parser.parse_args(argv)
    c = validate_config(read(ROOT / CONFIG))
    if a.command == 'status': status(c, a.output)
    elif a.command == 'build': build(c, a.record)
    elif a.command == 'publish': publish(c, a.record)
    elif a.command == 'bundle': bundle(c, a.record)
    elif a.command == 'preflight': preflight(c, read(a.record), a.expected)
    elif a.command == 'migrate':
        migrate(c, read(a.record), a.expected, a.approve_digest, a.backup_ref, a.no_schema_change, a.state_root)
    elif a.command == 'deploy': deploy(c, read(a.record), a.expected, a.approve_digest, a.state_root)
    elif a.command == 'rollback':
        rollback(c, a.state, a.approve_image_id, a.approve_removal, a.schema_compatible)
    else: rehearse(c, a.target_record, a.previous)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, RuntimeError, OSError, KeyError, subprocess.SubprocessError) as error:
        print('Release stopped: ' + str(error), file=sys.stderr)
        sys.exit(1)
