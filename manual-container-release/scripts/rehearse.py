"""Run only against Docker Desktop temporary projects, never the VPS."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import uuid

import argparse
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('worktree')
parser.add_argument('--previous-record', default='.releases/candidate.json')
parser.add_argument('--target-record', default='.releases/final.json')
args = parser.parse_args()
source = Path(args.worktree).resolve()
config = json.loads((source / 'ops/release-config.json').read_text())
old = json.loads((source / args.previous_record).read_text())
new = json.loads((source / args.target_record).read_text())
assert new.get('image') and new['visibility'] == 'private'
assert subprocess.check_output(['docker', 'context', 'show'], text=True).strip() == 'desktop-linux'
root = Path(tempfile.mkdtemp(prefix='manual-release-rehearsal-', dir='/private/tmp'))
ops = root / 'ops'; ops.mkdir()
project = config['project'] + '-rehearsal-' + uuid.uuid4().hex[:8]
container = project + '-' + config['service'] + '-1'
with socket.socket() as sock:
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
cfg = {**config, 'project': project, 'container': container, 'port': port}
compose = (source / 'ops/compose.production.yml').read_text()
compose = compose.replace('name: ' + config['project'], 'name: ' + project, 1)
compose = compose.replace(f'127.0.0.1:{config["port"]}:8080', f'127.0.0.1:{port}:8080')
if '    container_name:' in compose:
    compose = compose.replace('    container_name: drezuratop', '    container_name: ' + container)
(ops / 'compose.production.yml').write_text(compose)
(root / 'old.yml').write_text(compose)
(ops / 'release.py').write_bytes((source / 'ops/release.py').read_bytes())
(ops / 'release-config.json').write_text(json.dumps(cfg, indent=2) + '\n')
record = {**new, 'project': project, 'bundleHashes': {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in ['ops/release.py', 'ops/release-config.json', 'ops/compose.production.yml']}}
(root / 'release.json').write_text(json.dumps(record))
result = {'project': config['project'], 'scope': 'temporary local Docker Desktop fixtures only',
          'startedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'productionTouched': False}
env = {**os.environ, 'RELEASE_IMAGE': old['image']}
try:
    subprocess.run(['docker', 'compose', '-p', project, '-f', str(root / 'old.yml'),
                    'up', '--no-build', '--pull', 'never', '--wait', '--wait-timeout', '100'],
                   env=env, check=True, capture_output=True)
    subprocess.run(['python3', str(ops / 'release.py'), 'deploy', '--record',
                    str(root / 'release.json'), '--expected-current-image', old['localImageId'],
                    '--approve-digest', new['image'].split('@')[1], '--state-root', str(root / 'states')],
                   cwd=root, check=True, capture_output=True)
    state_dir = next(p for p in (root / 'states').iterdir() if p.is_dir())
    state = json.loads((state_dir / 'state.json').read_text())
    assert state['status'] == 'deployed'
    result['deploymentPassed'] = True
    subprocess.run(['docker', 'stop', '-t', '2', container], check=True, capture_output=True)
    subprocess.run(['python3', str(ops / 'release.py'), 'rollback', '--state', str(state_dir),
                    '--approve-image-id', old['localImageId']], cwd=root,
                   check=True, capture_output=True)
    actual = json.loads(subprocess.check_output(['docker', 'inspect', container], text=True))[0]
    assert actual['Image'] == old['localImageId']
    assert actual['State']['Health']['Status'] == 'healthy'
    assert json.loads((state_dir / 'state.json').read_text())['status'] == 'rolled-back'
    result['rollbackFromStoppedTargetPassed'] = True
    result['restoredImageId'] = actual['Image']
except Exception as exc:
    result['failureType'] = type(exc).__name__
    if isinstance(exc, subprocess.CalledProcessError):
        # Command output belongs only to the temporary static fixture, never production.
        result['failureDiagnostics'] = (exc.stderr or b'').decode(errors='replace')[-3000:]
finally:
    cleanup = subprocess.run(['docker', 'compose', '-p', project, '-f', str(root / 'old.yml'),
                              'down', '--timeout', '5'], env=env, capture_output=True)
    result['fixtureCleanupPassed'] = cleanup.returncode == 0
    if cleanup.returncode == 0:
        shutil.rmtree(root)
    else:
        result['remainingFixturePath'] = str(root)
    result['finishedAt'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (source / '.releases/deploy-rollback-rehearsal.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
if not result.get('deploymentPassed') or not result.get('rollbackFromStoppedTargetPassed'):
    sys.exit(1)
