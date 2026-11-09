# Upgrade policy

## Priorities (what the survey's P1–P4 mean)

| Priority | Trigger | Action |
|---|---|---|
| P1 | High or critical advisory in runtime dependencies; Node pin past end-of-life | Check exposure, then fix in a dedicated upgrade soon (days, not weeks) |
| P2 | Node within 90 days of end-of-life; pins disagree; deprecated runtime dependency; `latest` base image; mixed lockfiles | Next maintenance pass |
| P3 | Majors behind; Node in maintenance with less than a year left; dev-only high advisories; coupled packages out of step; `engines` floor below the pinned Node | Plan as separate majors |
| P4 | Patch/minor updates; moderate/low advisories; tag-only base images | Routine monthly batch |

Cadence: survey all apps monthly, or before any release. P1 items don't wait for the schedule.

## Advisories

- `npm audit` reports a vulnerable version in the tree. That is not the same as being exploitable. Before calling a finding urgent, check:
  - **runtime vs dev:** the survey separates them, and a dev-only finding doesn't ship in the image
  - **reachability:** is the vulnerable function used, and is it fed untrusted input? Find out with `npm ls <pkg>` and a code search
  - **fix availability:** a fixed version exists within the allowed range, or needs a parent major
- **Static sites** (DrezuraTop, ParkourTop, MarcelKocian) ship only built assets in nginx. Runtime advisories there usually affect the build, not visitors, so say so. That doesn't mean ignore them.
- Fix a transitive advisory by upgrading the direct parent. Use an `overrides` entry only when the parent has no fix. Comment the reason in the commit and remove the override once the parent catches up.
- Never report "0 vulnerabilities" as "secure". Advisory databases have gaps, and private packages aren't covered.

## Choosing versions

- **Safe batch:** all patch/minor updates within the current majors, in one group. That's the survey's first group.
- **Majors:** one group each, in dependency order: tooling (TypeScript, ESLint) before frameworks, and test runners after the code compiles. Never combine a framework major with anything else.
- **Coupled packages move together:**
  - `react`, `react-dom` and `@types/react*`
  - `next` and `eslint-config-next`
  - `vitest` and `@vitest/*` (same exact version)
  - `@playwright/test` and the Playwright browsers or Docker image
  - `typescript-eslint` packages
  - `tailwindcss` and `@tailwindcss/*`
- **`@types/node`** follows the **lowest Node major the project runs on**, never npm "latest". The survey caps it automatically.
- **Too new:** skip prereleases and versions published less than about 7 days ago, unless they fix a P1 advisory. Fresh releases are often yanked or patched, and they're a supply-chain risk.
- **TypeScript majors** (6 → 7, the native compiler) are their own group. Check build scripts that import the `typescript` API.
- **Deferring** is fine when the reason is specific: "blocked by peer range of X", "needs code migration Y, separate task", "owner decision". Vague reasons aren't acceptable.

## Node.js

- **Production images use even-numbered LTS lines only.** The survey reads the live schedule (`nodejs/Release` `schedule.json`).
- As of 2026-11-09 the lines are:
  - Node 20: end-of-life
  - Node 22: maintenance, end-of-life 2027-04-30
  - Node 24: maintenance, end-of-life 2028-04-30
  - Node 26: active LTS
  - From Node 27 onward, Node moves to one major per year.
- **Move off a line** at the latest when it has under a year of maintenance left. New projects start on the newest active LTS.
- **The four sources must agree:**
  - `.nvmrc` or `.node-version`, the exact local version
  - `engines.node` (floor = the production major)
  - every Dockerfile stage
  - CI `node-version`
- **Change Node in its own Mode C branch**, never mixed with a framework major.

## Base images

- Pin by digest (`image:tag@sha256:…`). The tag stays as a readable label, but the digest is what actually decides the image.
- Refresh digests on each maintenance pass. That's how Alpine and nginx security fixes arrive.
- Keep build and runtime stages on the same Node major. For GarageERP's copied-Node runtime, keep the Alpine version compatible with the Node build stage.
- Never use `latest`. That includes Playwright images, which must match the `@playwright/test` version.
