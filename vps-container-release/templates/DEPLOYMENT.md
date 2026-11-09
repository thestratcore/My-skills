# Releases: <project>

Local committed source → checks → linux/amd64 image(s) → private GHCR → owner-approved,
digest-pinned Compose deployment on the Stratcore VPS. Procedure and rules: the
`vps-container-release` skill. This file holds only what is specific to this project.

## Identity

| | |
|---|---|
| Shape | <static nginx \| node server (+worker, +migrate job)> |
| Compose project / services | `<project>` / <services and roles> |
| Image(s) | `ghcr.io/thestratcore/<pkg>` |
| Public URL | https://<domain> (<Authelia-gated?>) |
| Loopback port | 127.0.0.1:<port> → <container port> (or: proxy network <name>, no port) |
| Deploy dir / env files | <`/opt/<project>`, `.env.production` (chmod 600)> or none |
| State | <volumes, databases, or "none: stateless"> |
| Release mode | <production \| preview/noindex> |
| Helper | vendored vps-container-release <version> |

## Project-specific checks and verification

- Checks run by `build`: <from release-config.json>
- Smoke paths: <...>
- After deploy, verify: <loopback health URL, origin route expectation (200 / 302 to Authelia), one real app action>

## Data and migrations

<"No persistent state; no migrations." or: DB name, migration command/job, backup command, compatibility notes>

## Commands

Mac (repo root, clean checkout):

```sh
python3 ops/release.py build   --record .releases/<rev12>.json
git push
python3 ops/release.py publish --record .releases/<rev12>.json
python3 ops/release.py bundle  --record .releases/<rev12>.json
scp .releases/bundle-<rev12>.tar stratcore-vps:/root/release-preparation/
ssh stratcore-vps 'd=/root/release-preparation/<project>/<full-rev>; mkdir -p $d && tar -xf /root/release-preparation/bundle-<rev12>.tar -C $d && cd $d && sha256sum -c MANIFEST.sha256'
```

VPS (`cd /root/release-preparation/<project>/<full-rev>`):

```sh
python3 ops/release.py status --output current.json
python3 ops/release.py preflight --record release.json --expected current.json
# approval → (migrate) → deploy, rollback: see the skill
```

## History

Release history is kept in the vault PROJECT_KNOWLEDGE.md, not here.
