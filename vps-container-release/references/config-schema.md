# `ops/release-config.json` (schema 2)

One file per repo; the only project-specific input to `ops/release.py`. Starting points:
`templates/release-config.static.json`, `templates/release-config.server.json`.

| Field | Required | Meaning |
|---|---|---|
| `schema` | yes | `2` |
| `project` | yes | Compose project name on the VPS (`docker inspect` label `com.docker.compose.project`) |
| `source` | yes | GitHub URL; written into the OCI `source` label and checked on every image |
| `mode` | yes | Release mode, e.g. `production` or `preview`. Records with a different mode are refused |
| `modeLabel` | no | Image label that must equal `mode` (MarcelKocian: `cz.marcelkocian.release-mode`) |
| `productionHostname` | no | Default `n8n`; build and rehearse refuse to run on this host |
| `deployDir` | with env files | VPS directory passed as `--project-directory`; env_file paths resolve here |
| `envFiles` | no | Paths relative to `deployDir`; must exist with mode 600. Only their sha256 is recorded |
| `composeFile` | no | Default `ops/compose.production.yml` |
| `checks` | no | Commands run (with `CI=true`) before building; must leave the tree clean |
| `images.<key>` | yes | `repository` (ghcr.io/thestratcore/…), `dockerfile` (default `Dockerfile`), `context` (default `.`), `target`, `buildArgs` (non-secret), `buildMetadata` |
| `services.<name>` | yes | Must match the Compose service name |
| `services.<name>.role` | yes | `app` or `worker` (long-running, replaced by deploy) or `job` (run only by `migrate`) |
| `services.<name>.image` | yes | Key into `images`; Compose uses `${RELEASE_IMAGE_<KEY>}` (single-image projects may also use `${RELEASE_IMAGE}`) |
| `services.<name>.container` | app/worker | Exact container name on the VPS (`marcelkocian-web-1` if Compose auto-names it) |
| `services.<name>.port` | no | `{"host": 8080, "container": 8080}`; `host: null` means no published port (proxy network). Production must publish exactly `127.0.0.1:<host>` |
| `services.<name>.mounts` | no | `[{"type": "volume"\|"bind", "target": "/path"}]`; must equal the running container's persistent mounts |
| `services.<name>.profile` | job | Compose profile that keeps the job out of `up` |
| `smoke.service` | no | Service probed over HTTP (default: first app with a port) |
| `smoke.paths` | no | Paths that must return 200 |
| `smoke.execChecks` | no | `[{"service", "command": [...]}]` run with `compose exec` (e.g. `nginx -t`) |
| `smoke.containerTest` | no | Local command; the smoke service's image ref is appended |
| `smoke.env` | no | **Fake** values written into every env file stub for smoke and rehearsal |
| `smoke.runJobs` | no | Run job services against the smoke stack before starting apps |
| `smoke.extraServices` | no | Throwaway Compose services for smoke/rehearsal only (e.g. a `postgres:17-alpine` test DB) |
| `smoke.timeout` | no | Seconds, default 120 |
| `legacyEnvironment` | no | Variables needed to re-render the compose file that started the *current* containers (first v2 deploy over a pre-v2 setup) |

## Build metadata contract (`buildMetadata: true`)

The helper passes `APP_RELEASE_BUILD=1`, `APP_COMMIT=<rev>`, `APP_BUILD_TIME=<UTC>` build args,
then checks that the smoke service serves `/version.json` with `Cache-Control: no-store` and exactly
`{"version": <package.json version>, "commit", "builtAt"}`. Enable it only when the app implements this.

## Release record (`.releases/<name>.json`, written by build/publish)

`schema`, `helperVersion`, `project`, `revision`, `source`, `platform`, `mode`, `builtAt`,
`checksPassed`, `smokePassed`, `bundleHashes` (release.py, config, compose), and
`images.<key>`: `tag`, `localImageId`, `image` (`repo@sha256:` registry digest), `visibility`, `publishedAt`, `buildInfo`.
Records never contain secret values. `.releases/` is git-ignored local evidence: keep it.
