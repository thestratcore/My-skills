---
name: vps-container-release
description: Release, deploy and roll back Docker apps from /Users/admin/Documents/CodeProjects to the Stratcore Hetzner VPS (stratcore-vps) through private GHCR images and digest-pinned Docker Compose, using a vendored ops/release.py helper. Use when the user says release, deploy, ship or push a new version of <project> to the VPS, roll back <project>, publish an image to GHCR, or onboard or set up a project for container releases. Covers static nginx sites, Node/Next.js servers, workers, one-off migration jobs and volumes.
---

# VPS container release

One procedure for every CodeProjects app on the Stratcore VPS:
build once on the Mac → publish a private GHCR image → deploy its exact digest with the owner's approval → keep a rollback.
The tool is `ops/release.py` in each repo, a vendored copy of `scripts/release.py` (helper v2.0.1).

## Hard rules

1. Build only on the Mac. Never `git pull`, build or edit files on the VPS.
2. Deploy registry digests only. Tags are `sha-<full revision>` and are never reused.
3. Building and publishing are not approval. Stop at the approval gate unless the owner already approved **this exact replacement**.
4. Never restart or reconfigure Caddy, Authelia, client-postgres, n8n, shared networks or other projects.
5. Secrets never go in Git, images, records, command lines or chat. They live in chmod-600 env files on the VPS.
6. Capture the previous state before replacing anything (`deploy` does this). Keep old bundles and images.
7. An image rollback does not undo a migration. Settle the data path before approval.
8. Report what you verified separately from what you assumed: prepared, tested, published, deployed, verified.

VPS: `ssh stratcore-vps` (root, amd64, hostname `n8n`, Caddy in front, loopback-only ports, disk ~85% full).
Details, the port registry and paths: [references/vps-facts.md](references/vps-facts.md). Wider host context: the `connect-to-vps` skill.

## Step 0: triage

1. Find the repo with `ls /Users/admin/Documents/CodeProjects` (suffixes vary). Read the vault `PROJECT_KNOWLEDGE.md`, the repo's AGENTS/CLAUDE.md and `ops/DEPLOYMENT.md`.
2. Look at `ops/release-config.json`:
   - `"schema": 2` → **Path A**.
   - schema 1 or no `schema` → upgrade first ([onboarding § adopting](references/onboarding.md)), then Path A.
   - missing → **Path B**.
3. Compare `python3 ops/release.py --version` with the skill's `HELPER_VERSION`. If the repo is older, offer to re-vendor it as its own commit, never mixed into a feature release.
4. If the release touches a database, volume or migration, read [references/stateful-releases.md](references/stateful-releases.md) now.

## Path A: release an onboarded project

Work from a clean checkout of the commit being released, using a worktree if the main checkout has unrelated changes.
Each step ends with its "Done:" check. Stop at the first failure and see [troubleshooting](references/troubleshooting.md).

**1. Build and smoke** (Mac, repo root)
```sh
python3 ops/release.py build --record .releases/<rev12>.json
```
This runs the configured checks, builds linux/amd64 with OCI labels, and smoke-tests the whole stack under the production compose file with fake env values on an isolated network.
Done: the record exists with `smokePassed: true`.

**2. Push and publish**
```sh
git push origin HEAD
python3 ops/release.py publish --record .releases/<rev12>.json
```
Done: every `images.<key>.image` is `ghcr.io/thestratcore/…@sha256:…` and `visibility` is `private`.

**3. Bundle and transfer**
```sh
python3 ops/release.py bundle --record .releases/<rev12>.json
scp .releases/bundle-<rev12>.tar stratcore-vps:/root/release-preparation/
ssh stratcore-vps 'd=/root/release-preparation/<project>/<full-rev>; mkdir -p $d && tar -xf /root/release-preparation/bundle-<rev12>.tar -C $d && cd $d && sha256sum -c MANIFEST.sha256'
```
Done: the manifest check prints OK for every file.

**4. Status and preflight** (VPS, in the bundle dir; changes no container)
```sh
python3 ops/release.py status --output current.json
python3 ops/release.py preflight --record release.json --expected current.json
df -h /
```
Done: "preflight passed", with enough free disk for the new image(s).

**5. Data** (only if state changes): back up and check the archive per stateful-releases.md, and note the path for `--backup-ref`.

**6. Approval gate.** Fill in [templates/approval-summary.md](templates/approval-summary.md) and show it to the owner. **Wait for an explicit OK.**

**7. Migrate** (only if the project has a job service)
```sh
python3 ops/release.py migrate --record release.json --expected current.json \
  --approve-digest sha256:<digest> --backup-ref <path> --state-root /root/release-state/<project>
# or --no-schema-change instead of --backup-ref when nothing changes
```

**8. Deploy**
```sh
python3 ops/release.py deploy --record release.json --expected current.json \
  --approve-digest sha256:<digest> --state-root /root/release-state/<project>
```
This replaces only the config's app and worker services (`--no-build --pull never --no-deps --wait`), then checks image IDs and health.
Done: it prints `Deployment state: <dir>`. Keep that path.

**9. Verify.** Check these, each separately:
- the loopback health URL
- the origin route: `curl -sk --resolve <domain>:443:127.0.0.1 https://<domain>/ -o /dev/null -w '%{http_code}'` (expect 200, or 302 for Authelia-gated sites)
- one real app behaviour
- workers processing safe test work
- unrelated containers unchanged (`docker ps`)

List anything you could not check.

**10. Record.** Add a dated entry to the vault `PROJECT_KNOWLEDGE.md` covering: revision, digest(s), previous image ID(s), state dir, checks and their results, gaps, and who approved.

## Rollback

```sh
python3 ops/release.py rollback --state /root/release-state/<project>/<dir> \
  --approve-image-id sha256:<previous image id>   # one flag per previous image
```
- Rollback accepts a stopped or unhealthy target. It refuses if someone else has changed the containers since.
- After a migration it needs `--schema-compatible`, which only the owner can decide.
- Services added by this release need `--approve-removal`.
- v1 deployments (before 2026-11) roll back with the `release.py` inside that release's own bundle directory.

A failed deploy prints its state dir. Run the rollback that was in the approval summary, then re-verify.

## Path B: onboard a project

Follow [references/onboarding.md](references/onboarding.md). In short:
- gather production evidence, including uncommitted production drift
- pick a shape from `templates/`
- vendor `scripts/release.py` and `scripts/test_release.py` into `ops/`
- write `release-config.json` ([schema](references/config-schema.md)), `compose.production.yml` and `DEPLOYMENT.md`
- reserve the port in vps-facts.md
- run `build`, then `rehearse`

The first release should change nothing visible. Then go to Path A.

## Proving changes to the helper

Run `python3 -m unittest -v scripts/test_release.py` and `tests/run-fixtures.sh` (Docker Desktop: a static site, then a Node app with a worker, migrate job and volume). Bump `HELPER_VERSION` for any behaviour change.
`rehearse` on a real repo runs deploy → stop → rollback against a throwaway Docker Desktop copy of its production compose. It never touches the VPS.

## Other files

- [references/gotchas.md](references/gotchas.md): lessons from real releases. Read before onboarding.
- [templates/repo-agents-snippet.md](templates/repo-agents-snippet.md): paste into a repo's AGENTS.md.
- Out of scope: GitHub Actions, dependency upgrades (`nodejs-project-upgrade`), Caddy/DNS/Authelia changes. Each is a separate task with its own approval.
