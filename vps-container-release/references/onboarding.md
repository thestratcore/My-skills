# Onboarding a project (path B)

Goal: the first release changes nothing visible in production. It only moves an existing app
onto versioned, digest-pinned images. Feature work and dependency upgrades are separate releases.

## 1. Gather evidence (read-only)

- Repo: `ls /Users/admin/Documents/CodeProjects`, then read `PROJECT_KNOWLEDGE.md`, the Dockerfile(s) and compose files.
- Production, over `ssh stratcore-vps`:
  - `docker ps`, then `docker inspect <container>` for: image ID, Compose labels (`project`, `service`, `config_files`, `working_dir`), ports, mounts, networks, limits, healthcheck
  - the compose file and directory currently in use (`/opt/<project>` or `/root/<project>`), and the env file names (never print their contents)
  - `git -C <dir> status` in any production checkout. **Uncommitted production changes** (lockfile updates from maintenance are common) must be brought into the repo first, or the release silently undoes them.
  - the Caddy site block: `grep -n -A8 <domain> /etc/caddy/Caddyfile`
- Data: every volume, bind mount and database the app touches, and whether the entrypoint runs migrations automatically.

## 2. Choose the shape

| Shape | Examples | Templates |
|---|---|---|
| Static site (nginx) | DrezuraTop, MarcelKocian, ParkourTop | `Dockerfile.static-nginx`, `nginx.conf`, `compose.static.yml`, `release-config.static.json` |
| Node/Next.js server, optional worker, optional migration job, env file, external networks | GarageERP, StratDesk, Silvaros NLI | `Dockerfile.node`, `compose.server.yml`, `release-config.server.json` |

Delete what does not apply (no worker → remove it from both compose and config).
One image per project is normal. Use several `images` keys only when services really need different images.

## 3. Add the files (on a branch, in an isolated worktree if the main checkout has unrelated work)

```
ops/release.py              # copy of the skill's scripts/release.py, plus a header line (below)
ops/test_release.py         # copy of the skill's scripts/test_release.py
ops/release-config.json
ops/compose.production.yml  # no build:, image: ${RELEASE_IMAGE_<KEY>}
ops/DEPLOYMENT.md           # from templates/DEPLOYMENT.md
.releases/  →  .gitignore and .dockerignore
```

Header line to add as line 2 of `ops/release.py`:
`# vendored from vps-container-release <HELPER_VERSION> sha256:<sha of the skill copy>`.
Check drift later with `python3 ops/release.py --version`.

Rules for `compose.production.yml`:
- Copy the **current production** settings exactly: ports, limits, networks, user, tmpfs, healthcheck, restart, logging, container names. Changing them is a separate, explicitly approved change.
- Keep the same Compose project name and service names as the running stack. Otherwise Compose starts a second copy instead of replacing the first.
- Secrets only via `env_file`. Never use `${VAR}` interpolation for secrets in `environment:`.
- Shared networks are `external: true`.
- If the old setup was started from a compose file with a `build:` section or other variables, put those variables in `legacyEnvironment` so `deploy` can re-render the current model.

Fill in `release-config.json` field by field (see `config-schema.md`). Reserve the host port in `vps-facts.md`.
Pin base images by digest in the Dockerfile.

## 4. Prove it locally

```sh
python3 -m unittest discover -s ops -p test_release.py
python3 ops/release.py build --record .releases/onboard-candidate.json
python3 ops/release.py rehearse --target-record .releases/onboard-candidate.json \
  --previous <key>=<image matching current production, e.g. a local build of the prod revision>
```

For static sites, compare the built static tree with production to show nothing changes:
`docker create` and `docker export` on both images, then `diff -r` of `/usr/share/nginx/html`.

## 5. First production release

Follow path A in SKILL.md. Notes for the first one:
- If the current container has no previous v2 state, the `status` output is still the expected identity.
- A brand-new app (no container yet) shows `null` in `status`. `deploy` treats that as an initial deployment, and rollback then needs `--approve-removal`.
- After the cutover, the old production checkout is no longer used for deploys. Leave it in place and record that in `PROJECT_KNOWLEDGE.md`.

## Adopting a schema-1 repo (pre-v2 helper)

1. Copy the v2 `release.py` and `test_release.py` into `ops/`.
2. Convert the config by hand:
   - `image` → `images.web.repository`
   - `service`, `container`, `port` → `services.<service>` with `port: {host: <port>, container: 8080}`
   - `smokePaths` → `smoke.paths`
   - `buildMetadata` and `target` move under `images.web`
   - `containerTest` → `smoke.containerTest`
   - add `smoke.execChecks` with `nginx -t` for nginx images
3. The compose file may keep `${RELEASE_IMAGE}`, which the helper still sets for single-image projects.
4. Run the tests, `build` and `rehearse`.

Bundles already on the VPS keep their v1 `release.py`. Roll back a v1 deployment with that bundle's tool, not v2.
