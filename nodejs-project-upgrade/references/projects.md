# Registered projects

The six production apps on the Stratcore VPS. `scripts/survey.py` has the same list in `PROJECTS`. A test fails if the two drift apart, so update both together.
Facts were checked read-only on 2026-11-09. Re-check them with the survey and `git log` before relying on them.

All six use **npm** with `package-lock.json`. Every upgrade runs from a worktree under
`/Users/admin/Documents/CodeProjects/.upgrade-worktrees/<repo>`, never from the main checkout.

**Verify** means: run all of these on the upgraded worktree, in this order, and stop at the first failure.

## garageerp

- **Repo:** `/Users/admin/Documents/CodeProjects/GarageERP-React`. Next.js 16 (webpack build), React 19, PostgreSQL.
- **Vault:** `Company/Stratcore/Projects/GarageERP/PROJECT_KNOWLEDGE.md`. **Repo docs:** `AGENTS.md`, `docs/release-process.md`, `docs/release-journal.md`.
- **Node pins:** `.nvmrc` 22, `engines` `>=22 <23`, Dockerfile `base` and `node-runtime` stages `node:22-alpine`. Mode C changes all four together.
- **Dockerfile:** `base` → `dependencies` → `builder` → `node-runtime` (`node:22-alpine`) → `runner` (`alpine:3.24`, which gets Node copied in). A Node bump must keep the copied binary and the Alpine release compatible (musl).
- **Baseline / verify:**
  - `npm ci`
  - `npm run check` (lint, check:tokens, typecheck, unit tests)
  - `npm run build`
  - `npm run test:integration`, then `npm run test:e2e`. Run these two **one after the other, never in parallel**. Both use the local `TEST_DATABASE_URL` (`*_test` only), and e2e resets it.
- **Delivery:** VPS container `garageerp-app`, `127.0.0.1:3010`. Not on `ops/release.py` yet. Verify the image with the generic Docker build (SKILL.md Mode B step 5), or onboard it through `vps-container-release` Path B first.
- **Caveats:**
  - Release-journal entries in `lib/release-journal.ts` are written by hand, one per release.
  - The catalogue-sync job is a separate service, so don't change it in passing.

## stratdesk

- **Repo:** `/Users/admin/Documents/CodeProjects/StratDesk-nextjs`. Next.js 16, MCP server (`@modelcontextprotocol/sdk`), PostgreSQL `dbStratDesk`, n8n workflow exports.
- **Vault:** `Company/Stratcore/Projects/StratDesk/PROJECT_KNOWLEDGE.md`. **Repo docs:** `AGENTS.md`, `docs/DEPLOY.md`.
- **Node pins:** `engines` `>=22.18`, and three Dockerfile stages on `node:22-alpine`. There is no `.nvmrc`; Mode C should add one.
- **Baseline / verify:**
  - `npm ci`
  - `npm run lint`
  - `npm run typecheck`
  - `npm run format:check`
  - `npm test`: unit and integration tests. It needs Docker, because it starts a throwaway `postgres:17-alpine` on `127.0.0.1:55432`. Stop it afterwards with `npm run db:test:down`.
  - `npm run build`
  - `npm run check:n8n`
  - `npm run docker:build`, then `npm run check:no-gh-key -- stratdesk:local`, which must print `OK`
  - Optionally, for `@modelcontextprotocol/sdk` or n8n-related upgrades: `npm run test:n8n` (slow, about 90 s).
- **Delivery:** VPS container `stratdesk`, with no published port (Caddy reaches it over `stratdesk-proxy`). Not on `ops/release.py` yet.
- **Caveats:**
  - `n8n/*.json` is generated: run `npm run build:n8n`, never edit it by hand.
  - Never run `npm run migrate` against production as part of an upgrade.

## silvaros-nli

- **Repo:** `/Users/admin/Documents/CodeProjects/Silvaros-NLI-React`. Next.js 16, PostgreSQL `dbSilvaros`, MCP SDK, NLI and ČÚZK integrations.
- **Vault:** `Company/Silvaros/NLI/PROJECT_KNOWLEDGE.md` and `Company/Silvaros/NLI/NLI Deployment.md`.
- **Node pins:** three Dockerfile stages on `node:22-alpine`, plus `.github/workflows/deploy.yml` `node-version: "22"`. There is no `.nvmrc` and no `engines`; Mode C adds both and updates the workflow.
- **Baseline / verify:**
  - `npm ci`
  - `npm run lint`
  - `npm run typecheck`
  - `npm test`
  - `npm run build`
  - Optionally, with a local test database only: `npm run test:integration`, which uses `vitest.integration.config.ts`.
- **Delivery:** VPS container `silvaros`, `127.0.0.1:3000`. `.github/workflows/deploy.yml` ("CI/CD", concurrency group `production-deploy`) runs on **every push to `main`**, so pushing to `main` deploys. Upgrade branches stay local until a release is approved. Not on `ops/release.py`.
- **Caveats:**
  - Outbound NLI/ČÚZK calls cost money (the `wsdp_charge` ledger). Keep them disabled in any smoke test.
  - The integration suite must never point at the production database.

## drezuratop

- **Repo:** `/Users/admin/Documents/CodeProjects/DrezuraTop-web`. Vite + TypeScript static site served by nginx; no UI framework.
- **Vault:** `Personal/DrezuraTop/PROJECT_KNOWLEDGE.md`. **Repo docs:** `AGENTS.md`, `ops/DEPLOYMENT.md`.
- **Node pins:** the Dockerfile `ARG NODE_IMAGE=node:24-alpine@sha256:…` (digest-pinned), plus `NGINX_IMAGE`. There is no `.nvmrc` and no `engines`; Mode C adds both.
- **Baseline / verify:**
  - `npm ci`
  - `npm run check`, which runs validate-rules, a type-checked build, unit tests and Playwright e2e
  - `python3 ops/release.py build --record .releases/deps-<rev12>.json`
- **Delivery:** VPS container `drezuratop`, `127.0.0.1:8080`, via `ops/release.py`. Helper v2 is on branch `chore/release-helper-v2`, not yet merged; if `main` still has v1, build from a branch that contains v2.
- **Caveats:**
  - `src/` YAML rules are validated with zod. A zod major changes the validation API, so test `validate-rules` explicitly.
  - Playwright screenshot baselines may need the owner's approval to change.

## parkourtop

- **Repo:** `/Users/admin/Documents/CodeProjects/ParkourTop-web`. Vite + TypeScript static site served by nginx, modelled on DrezuraTop.
- **Vault:** `Personal/ParkourTop/PROJECT_KNOWLEDGE.md`. **Repo docs:** `AGENTS.md`, `PARKOURTOP_SPEC.md`.
- **Node pins:** Dockerfile `node:24-alpine` and `nginxinc/nginx-unprivileged:1.29-alpine`, both tag-only. There is no `.nvmrc` and no `engines`.
- **Baseline / verify:**
  - `npm ci`
  - `npm run check`: build, unit tests, then Playwright e2e on the desktop and phone projects
  - `cd investigation-mimic && npm test`, but only if its dependencies changed
- **Delivery:** the VPS port registry lists `parkourtop` on `127.0.0.1:8081`, but the repo `AGENTS.md` still says deployment was deferred. Reconcile the two from `docker ps` before claiming it is in production. Not on `ops/release.py`.
- **Caveats:**
  - Screenshot baselines in `tests/e2e/*-snapshots/` change only with the owner's approval. A dependency upgrade that moves pixels is a finding, not a baseline refresh.
  - Ask before adding any new dependency.

## marcelkocian

- **Repo:** `/Users/admin/Documents/CodeProjects/MarcelKocian-ts`. Static site: a custom build script (`scripts/build.mjs`), Tailwind 4 via Vite, served by nginx.
- **Vault:** `Company/Stratcore/Projects/MarcelKocianCZ/PROJECT_KNOWLEDGE.md`. **Repo docs:** `DEPLOYMENT.md`, on the release branch.
- **Node pins:** `.node-version` 24.14.0, `engines` `>=22.12.0`, Dockerfile `ARG NODE_IMAGE=node:24.14.0-alpine@sha256:…`. The `engines` floor still allows Node 22; raise it to `>=24` in the next Mode C.
- **Baseline / verify:**
  - `npm ci`
  - `npm run build` (includes typecheck)
  - `npm test` (node:test with strip-types)
  - `python3 ops/release.py build --record .releases/deps-<rev12>.json`, which also runs `test-container.mjs`
- **Delivery:** VPS container `marcelkocian-web-1`, `127.0.0.1:3011`, preview/noindex mode, via `ops/release.py`. Helper v2 is on branch `chore/release-helper-v2` (from `main` `c940b3c`).
- **Caveats:**
  - Keep preview mode. Going public is a separate decision.
  - The output should stay byte-identical unless the upgrade intends to change it. Compare with `docker export` (see `vps-container-release` onboarding).

## Not registered

`survey.py --all` also lists the other Node repos and marks them "unregistered":
- DrezuraTop-Capacitor (no git repository)
- REA-typescript
- StinnDenik-Appsmith
- LinkedInMCP-server (pnpm)
- StratcoreReport-html
- weathercloud-headless
- LangChain_test
- the nested apps (RetoolSmlouvy, KnihaJizd web, InstagramAgent frontend, ClaudeFlow driver)

To register one, add it here and to `PROJECTS`, with its own verify commands.
