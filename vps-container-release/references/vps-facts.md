# Stratcore VPS facts for releases

Verified live (read-only) on 2026-11-09. If the host disagrees, trust the host and fix this file.
Wider host context (databases, credentials, Authelia users): the `connect-to-vps` skill.

## Host

| | |
|---|---|
| Access | `ssh stratcore-vps` (root, `~/.ssh/id_ed25519`), IP 178.105.186.47, hostname `n8n` |
| Arch / OS | linux/amd64, Ubuntu 26.04, 2 vCPU, ~3.7 GB RAM, **no swap** (keep `mem_limit` on everything) |
| Tooling | Docker Compose v5.6.1, Python 3.14 (helper is stdlib-only) |
| Disk | 75 GB, **85% used** on 2026-11-09; ~15 GB of reclaimable images. Check `df -h /` in preflight |
| Front | Caddy (systemd) `/etc/caddy/Caddyfile`, behind Cloudflare (80/443 only from CF ranges). Authelia at 127.0.0.1:9091 gates selected sites via the `authelia_gate` snippet |
| Firewall | Docker bypasses ufw → **publish only on 127.0.0.1**, never 0.0.0.0 |

## Loopback port registry

Pick a free port at onboarding and add it here in the same change.

| Port | Owner |
|---|---|
| 2019 | Caddy admin API |
| 3000 | silvaros-app |
| 3003 | openwebui |
| 3010 | garageerp app |
| 3011 | marcelkocian web |
| 5432 | client-postgres |
| 5678 | n8n |
| 8080 | drezuratop |
| 8081 | parkourtop |
| 9091 | authelia |
| — | stratdesk, vault-mcp: no published port (Caddy reaches them over a Docker network) |

## Docker networks (shared, never recreate)

`client-db-net` (client-postgres; apps that need a client DB join it as `external: true`),
`stratdesk-proxy`, `n8n_default`, `authelia_default`, plus per-project `<project>_default`.

## Release paths and naming

| Thing | Convention |
|---|---|
| Registry | `ghcr.io/thestratcore/<package>`, **private**; tag `sha-<full git revision>`, never reused |
| GHCR auth, Mac | Docker credential store (osxkeychain), classic PAT with `write:packages` |
| GHCR auth, VPS | `/root/.docker/config.json`, classic PAT with `read:packages` only |
| Bundles | `/root/release-preparation/<project>/<full revision>/` (keep them all, their `release.py` is the rollback tool) |
| Deploy state | `/root/release-state/<project>/<UTC stamp>-<rev12>/` (`state.json`, `previous-compose.json`) |
| Migration log | `/root/release-state/<project>/migrations/` |
| Runtime secrets | chmod-600 env file(s) in `deployDir`, e.g. `/opt/<project>/.env.production`; never in the bundle |

GitHub SSH keys do not authenticate GHCR; the two are separate credentials.
Classic PATs expire. A `denied` or `unauthorized` error on push or pull usually means an
expired token: renew it on GitHub and `docker login ghcr.io` again on that machine.

## Never touched by a release

Caddy, Authelia, client-postgres, n8n, other projects' containers, and shared networks.
A release replaces only its own app and worker services, and runs only its own job.

## Image retention

Keep the current and previous image for every released project. Removing anything older is an
owner-approved cleanup, never part of a release:

```sh
docker image ls --format '{{.Repository}}:{{.Tag}} {{.ID}} {{.CreatedSince}} {{.Size}}' | sort
docker image rm <id>   # only images not referenced by a container or the last two state dirs
```
