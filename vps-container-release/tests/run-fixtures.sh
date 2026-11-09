#!/bin/sh
# End-to-end check of scripts/release.py on Docker Desktop: build+smoke twice, then rehearse.
# Never touches the VPS or GHCR. Usage: tests/run-fixtures.sh [static-site|node-app]...
set -eu
SKILL=$(cd "$(dirname "$0")/.." && pwd)
WORK=$(mktemp -d "${TMPDIR:-/tmp}/vps-release-fixtures.XXXXXX")
for name in "${@:-static-site node-app}"; do
  for fx in $name; do
    d="$WORK/$fx"; cp -R "$SKILL/tests/fixtures/$fx" "$d"
    cp "$SKILL/scripts/release.py" "$SKILL/scripts/test_release.py" "$d/ops/"
    cd "$d"; git init -q; git add -A; git -c user.email=f@x -c user.name=fixture commit -qm v1
    python3 ops/release.py build --record .releases/v1.json >/dev/null
    first=$(python3 -c "import json;r=json.load(open('.releases/v1.json'));print(' '.join(f'--previous {k}={v[\"tag\"]}' for k,v in r['images'].items()))")
    # second build needs a distinct revision
    echo "// v2" >> ops/release-config.json.note 2>/dev/null || true
    git add -A; git -c user.email=f@x -c user.name=fixture commit -qm v2 --allow-empty
    python3 ops/release.py build --record .releases/v2.json >/dev/null
    python3 ops/release.py rehearse --target-record .releases/v2.json $first
    echo "fixture $fx: PASSED"
  done
done
rm -rf "$WORK"
