---
name: connect-to-vps
description: Context for connecting to and working on the Stratcore Hetzner VPS (178.105.186.47, hostname n8n). Use whenever the user says "connect to vps", "ssh to the vps", "log into the server", or asks about what runs on the Stratcore VPS, its containers, ports, domains, databases, or credentials.
---

# Stratcore Hetzner VPS

Compiled from the Obsidian vault on 2026-10-03. Vault: `/Users/admin/Documents/Obsidian-Stratcore/`; Sources (subfolders): `Technology/Hetzner VPS.md`,
`Company/Stratcore/HetznerVPS-Services.md` (inventory audited 2026-06-30, predates later apps),
`Company/Stratcore/Hetzner VPS Agent Access.md`, `Company/Stratcore/Authelia Access Portal.md`,
`Company/Stratcore/OpenWebUI/OpenWebUI Deployment.md`, `Company/Silvaros/NLI/NLI Deployment.md`,
`Personal/DrezuraTop/drezuratop-access-gate-as-built.md`, `PostgreSQL-login.md`.
If facts here conflict with the live host, trust the host and tell the user which vault note is stale.

## Connecting

```
ssh stratcore-vps        # = agents@178.105.186.47 with ~/.ssh/stratcore_agents_ed25519
```

- **Always connect as `agents`. `root` is reserved for Lukáš personally** — never `root` or `deploy`,
  never `su`, never a privileged container used to escape. Claude Code settings deny `ssh root@178.105.186.47`.
- `agents` rights (set 2026-10-03):
  - **`docker` group** — `docker ps/logs/exec/compose …` for every container. Root-equivalent in
    practice (accepted risk); use it only for the project being worked on.
  - **Read/write (ACL, inherited):** `/root/n8n`, `/root/client-postgres`, `/root/openwebui`,
    `/root/mytools`, `/opt/drezuratop`, `/home/agents`. `/root` itself is traverse-only (no `ls /root`).
  - **Read-only:** `/opt/silvaros` (CI deploys as `deploy`; don't write there; `compose` there fails on its
    `.env` — use `docker logs/restart silvaros-app` instead).
  - **Denied:** `/root/dbSilvaros`, `/root/backups`, `/root/hantec-poc`, `/root/.ssh`, loose `/root` files,
    `/opt/authelia`, `/etc/caddy` (write), `/home/deploy`.
  - **sudo (only):** `sudo caddy validate --config /etc/caddy/Caddyfile`, `sudo systemctl reload caddy`.
  - Git: `/opt/drezuratop` pulls with agents' own deploy key `~/.ssh/drezuratop_github`.
- Still root-only (ask Lukáš to do it): editing the Caddyfile, Authelia config/users, `/root` crontab,
  system packages, ufw, users/sudoers.
- SSH is key-only (`PasswordAuthentication no`). ufw: 22 open to all; 80/443 only from Cloudflare ranges.

## Host

| | |
|---|---|
| Provider | Hetzner, account K0520192526 (console.hetzner.com) |
| IP / hostname | 178.105.186.47 / `n8n` |
| OS | Ubuntu 26.04 LTS |
| Size | 2 vCPU, ~3.7 GB RAM, 75–80 GB disk, **no swap** (OOM risk) |
| Front | Caddy (systemd, `/etc/caddy/Caddyfile`, admin API 127.0.0.1:2019) behind Cloudflare proxy, Full (strict) TLS, Let's Encrypt origin certs |

## Containers & apps

All containers publish to `127.0.0.1` only (Docker bypasses ufw — never publish `0.0.0.0`).

| Container | Image | Port | Compose dir | Public URL |
|---|---|---|---|---|
| `client-postgres` | postgres:17 | 127.0.0.1:5432 | `/root/client-postgres` | — (tunnel only) |
| `n8n-n8n-1` | n8n:latest | 127.0.0.1:5678 | `/root/n8n` | https://n8n.stratcore.cz |
| `n8n-postgres-1` | postgres:16 | internal | `/root/n8n` | — (n8n metadata) |
| `silvaros-app` | built from repo | 127.0.0.1:3000 | `/opt/silvaros` (owner `deploy`) | https://app.silvaros.cz |
| `openwebui` | ghcr.io/open-webui/open-webui:main | 127.0.0.1:3003 | `/root/openwebui` | https://chat.stratcore.cz |
| DrezuraTop | built from repo | 127.0.0.1:8080 | `/opt/drezuratop` | https://drezura.stratcore.cz (Authelia-gated) |
| Authelia | authelia/authelia:4.39.28 | 127.0.0.1:9091 | `/opt/authelia` | https://auth.stratcore.cz |
| `weathercloud-collector` | ephemeral | — | `/root/mytools/weathercloud-headless` | cron `*/10`, log `/var/log/weathercloud-collector.log` |

Docker networks: `client-db-net` (client-postgres 172.19.0.2, n8n 172.19.0.3, silvaros-app) and
`n8n_default` (n8n + n8n-postgres). n8n reaches client-postgres directly at `172.19.0.2:5432`.

Deploys:
- **Silvaros NLI**: CI/CD — `git push` to `main` of `thestratcore/Silvaros-React-NLI`; GitHub Actions SSHes
  as `deploy` and runs `cd /opt/silvaros && git pull --ff-only && APP_VERSION=$(git rev-parse --short HEAD) docker compose up -d --build`.
  Apply migrations before restart. Never rsync over `/opt/silvaros`.
- **DrezuraTop**: `cd /opt/drezuratop && git pull && docker compose up -d --build` (needs docker → ask).
- Authelia: only DrezuraTop uses the `authelia_gate` snippet; users in `/opt/authelia/private/users.yml`
  (Argon2id digests). Shared login username `drezura-visitor`; password is not stored in the vault.

Other systemd: docker, ssh, cron, chrony, unattended-upgrades, snap CUPS (port 631, likely unused).

## Databases (`client-postgres`, PG 17)

Superuser/owner `clientuser`. Databases: `clientdb`, `dbBauartURS`, `dbKarla`, `dbAuta`,
`dbWeathercloud`, `dbSilvaros`. pgvector not installed. Server has `ssl = off` → use `sslmode=disable`.

Tunnel from the Mac (tunnel itself uses the SSH user; agents may tunnel as `agents`):
```
ssh -N -o ExitOnForwardFailure=yes -L 127.0.0.1:5435:127.0.0.1:5432 agents@178.105.186.47
psql "host=localhost port=5435 user=clientuser dbname=dbSilvaros sslmode=disable"
```
Port convention on the Mac: 5435 = this VPS's client-postgres (`dbSilvaros` etc).

## Credentials (from vault — local use only)

| Role | Password |
|---|---|
| `clientuser` (superuser) | `K3W8Xb60ZIQMo5euLhwN4nSQsBScpqCkqv5HD+QjZ9Y=` |
| `appsmith_app` | `8QiUwRs2P01gROgT3Zfr5EFT` |
| `n8n_app` | `prGpwzV7qWFDf1XHaTe2Q9AL` |
| `docker_app` | `yWLqL6xgw2S3vQ4019hTeXyQ` |

Not in the vault (live on the host only): `silvaros_app`/`silvaros_ro` passwords (`/opt/silvaros/.env`,
`/root/dbSilvaros/001_init.sql`), OpenWebUI `.env` (OpenRouter key, WEBUI_SECRET_KEY), Authelia secrets.

Rules: never echo these into commits, vault notes, logs, chat outputs sent elsewhere, or shell history
(prefer `PGPASSWORD` from a prompt or `~/.pgpass`). Source of truth is vault `PostgreSQL-login.md`
and `Company/Stratcore/HetznerVPS-Services.md` — if a password fails, re-read those.

## Not on this VPS

Bosono (`bosono`, Mac port 5433) and Greenidea (`greenidea`, port 5434) live on **David's VPS
188.245.223.244** (user `lukas.navratil`), not here — `Technology/Hetzner VPS.md` says otherwise and is wrong.

## Known risks

No automatic backups of `dbSilvaros`; Cloudflare ufw range refresh cron not installed; CUPS exposed on 631;
David Navrátil's key is in root's `authorized_keys` (deliberate emergency access).
