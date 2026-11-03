> Historical project evidence only. Current reusable procedure: [SKILL.md](../SKILL.md).
> Paths, identities and helper assumptions below apply to the recorded projects.

# Verification record

2026-10-28: preparation completed for both projects; DrezuraTop subsequently deployed with
explicit owner approval. MarcelKocian remains unchanged. Existing GitHub SSH keys were retained for Git; GHCR uses
separate classic package tokens (Mac write:packages, VPS read:packages), verified by scope
metadata. No token values are stored in these notes or source.

| Case | Required outcome | Status |
|---|---|---|
| DrezuraTop initial release | Preserve production lockfile; local tests and AMD64 image; private GHCR push; VPS pull-only preflight | Passed: 181 unit + 101 browser tests, ten release safety tests, image smoke and private registry/pull checks |
| MarcelKocian reuse | Reuse the same release tool; preserve production dependencies and preview/noindex mode | Passed: 93 application tests, ten release safety tests, type-checked build, detailed container smoke, private publication and VPS pull |
| Safety gates | Reject wrong digest/project, altered bundle and changed production identity; recover a stopped target | Passed: safety tests plus actual deploy/stop/rollback on temporary local Docker Desktop fixtures for both projects; fixtures removed |

## Implementation identities

Both repositories use branch `chore/manual-ghcr-release`, in isolated local worktrees under
`/Users/admin/Documents/CodeProjects/.release-worktrees/`. Original workspaces/main branches
and unrelated user files were left intact. No GitHub Actions workflow was added.

The shared `ops/release.py` is byte-identical in both projects:
SHA-256 `2b7cb1de340e346f4ba9803920e6d22f3e5c558f5e0dd5743f2005727921c662`.

| Project | Source revision | Published private image |
|---|---|---|
| DrezuraTop | `ab523371767b8a270457442ee77c871228a1ed27` | `ghcr.io/thestratcore/drezuratop-web@sha256:3211cc29a1457f75a59c86f488c3b2e4068b9f758f307c668effc8da6b4ac358` |
| MarcelKocian | `2b0122e32799c41f0d386a89262e19e6a433662d` | `ghcr.io/thestratcore/marcelkocian-web@sha256:9fe87da528940ab0f746d38aabaf234161bc8cb125c836ff369c4efd3d506fc1` |

Release records and local verification evidence are in each worktree's ignored `.releases/`.
Prepared server bundles, release records and rollback-model validation are under
`/root/release-preparation/PROJECT/FULL_REVISION/` on the VPS. Production source checkouts
were retained; delivery uses the image and bundle instead of a VPS pull/build.

## DrezuraTop production cutover

- Owner approval: deploy DrezuraTop now; MarcelKocian excluded.
- DrezuraTop local/remote `main` fast-forwarded to `ab523371767b8a270457442ee77c871228a1ed27`.
  Original unrelated untracked documents were preserved. MarcelKocian main was not merged.
- Live image: `ghcr.io/thestratcore/drezuratop-web@sha256:3211cc29a1457f75a59c86f488c3b2e4068b9f758f307c668effc8da6b4ac358`.
- Deployment/rollback state: `/root/release-state/drezuratop/20261028T172701Z-ab523371767b`.
  The prior effective Compose model and image `sha256:5648bce4d060c238ab4643cebda675ee3ee5c506a89cea2c1bd717dead4f88be` are retained.
- Container healthy; homepage, health endpoint and rule/configuration endpoints HTTP 200.
  Static tree remains byte-identical to the previous production release.
- Loopback port 8080, 64 MiB, 0.5 CPU and runtime restrictions preserved. Caddy's configuration
  hash and MarcelKocian's container/image identities remained unchanged.
- Origin HTTPS route, tested with correct TLS hostname on loopback, returns 302 to Authelia.
  Automated external requests through Cloudflare return 403. Public browser access and an
  authenticated session were not verified; do not represent the complete login flow as passed.
- Subsequent owner confirmation: DrezuraTop is publicly accessible after login. This is
  owner-reported acceptance, distinct from the automated origin/edge checks above.

## Browser build identity follow-up

DrezuraTop feature branch `feat/browser-build-identity` adds an expandable version/commit/
UTC build-time footer and uncached `/version.json`, both from one Vite build object.
The release helper injects the exact source commit and build-start timestamp as build args;
publishing and deployment times remain external release records. Development builds are
explicitly unversioned. The owner approved commit, push and deployment of this follow-up.

Prepared candidate: `1c7406b7ae50104a5089812a1151f3be0ec2d101`, private image
`ghcr.io/thestratcore/drezuratop-web@sha256:9828f11fefadcc0a5b1fdceed3ec9f4a3be4f01da92e7ce807e40554e9b1d5b0`.
Build time: `2026-10-28T17:52:02Z`; application version remains `0.1.0`.
Verification passed: 184 unit tests, 102 browser tests, 10 release safety tests,
actual-image mobile Czech/desktop English footer checks and exact JSON/no-store checks.
VPS preflight passed against the existing `3211cc29…` image without changing containers.
The reviewed bundle is under `/root/release-preparation/drezuratop/1c7406b7ae50104a5089812a1151f3be0ec2d101`.
Local `.releases/browser-identity-cutover-review.json` records the exact replacement and
reviewed command. The owner subsequently approved deployment; it is now **deployed**.

Production follow-up cutover: main fast-forwarded/pushed to `1c7406b7ae50`; exact image
`9828f11f…` deployed and healthy. Rollback state:
`/root/release-state/drezuratop/20261028T180743Z-1c7406b7ae50`.
The previous image `3211cc29…` and effective Compose are retained. Runtime JSON exactly
matches the release build object with no-store; homepage/health/config return HTTP 200.
Caddy hash, port/resource restrictions and MarcelKocian identities remained unchanged.
Origin HTTPS still redirects to Authelia; agent-authenticated browser access was not tested.
Local evidence: `.releases/browser-identity-deployment-verification.json`; server evidence:
`deployment-verification.json` in the deployment state directory.

This branch extends the earlier shared helper with optional `buildMetadata` support;
MarcelKocian's existing prepared bundle remains frozen at its previously tested revision.
When reusing the newer helper for another application, enable metadata only when its
Dockerfile/build implements the matching contract.

## Replication lessons

- Import the exact production dependency files before writing the release workflow;
  this versions existing production state rather than introducing an upgrade.
- Git SSH access does not authenticate GHCR. Normal-user Docker publishing and root VPS
  pulling were verified independently; credentials stayed in Docker configuration/helpers.
- Preserve the application's current release mode. MarcelKocian remains preview/noindex;
  formal public-release/privacy approvals were not fabricated or bypassed.
- Stopped containers lose their runtime port map. Rollback validates the configured
  HostConfig port binding when recovering a stopped target, rather than requiring health.
- Save the effective previous Compose model, not merely its mutable source filename.
- Build once, retain the manifest/bundle hashes and deploy the exact registry digest.
- Compare static output when preserving behavior. The first published candidate trees
  matched production byte-for-byte; final builds reused those same static output layers.

This evidence is not blanket authorization for later deployments or for MarcelKocian cutover.
