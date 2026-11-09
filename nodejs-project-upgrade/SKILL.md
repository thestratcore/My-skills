---
name: nodejs-project-upgrade
description: Check for available updates, vulnerabilities and Node.js support status across the Stratcore CodeProjects, then upgrade one project's npm dependencies, Node.js version or Docker base images on an isolated branch with verification. Use when the user says check updates, what's outdated, npm audit, vulnerabilities, upgrade or bump dependencies, upgrade Next.js/React/Node, maintenance pass on <project>, or update base images. Covers GarageERP, StratDesk, Silvaros NLI, DrezuraTop, ParkourTop and MarcelKocian (plus a read-only survey of every other Node repo). Hands releases to vps-container-release.
---

# Node.js project upgrade

Survey first, then upgrade one project in small verified groups on its own branch, then hand off to `vps-container-release` to release.
Projects, their pins and verify commands: [references/projects.md](references/projects.md).
`<skill>` below means this skill's folder (`~/.claude/skills/nodejs-project-upgrade`, or the `MySKILLS` copy).

## Hard rules

1. Survey before changing anything. Plan the update groups from the survey.
2. Work in an isolated worktree branched from an explicit revision. Never touch unrelated changes in the main checkout.
3. Use npm, the projects' package manager. Never mix lockfiles, never delete `package-lock.json`, and never use `--force`, `--legacy-peer-deps` or `npm audit fix --force`.
4. One update group per commit. Every major is its own group.
5. A Node version change updates `.nvmrc`/`.node-version`, `engines`, every Dockerfile stage and the CI `node-version` together.
6. Don't change behaviour, schema, authentication, integrations, screenshot baselines or release mode in passing. If an upgrade needs any of that, stop and ask.
7. No push, publish or deploy. Releasing is `vps-container-release`, with its own approval. Pushing Silvaros NLI's `main` **deploys**.
8. Report verified checks separately from assumptions. Zero audit findings does not mean "secure".

## Step 0: triage

1. Find the project in `projects.md`. Read its vault `PROJECT_KNOWLEDGE.md` and the repo's `AGENTS.md`.
2. Pick the mode:
   - "Check updates", "what's outdated" or "audit" → **Mode A**.
   - "Upgrade X" → Mode A for that project, then **Mode B**.
   - Node version or base images → **Mode C**, which is Mode B with an extra checklist.

## Mode A: survey (read-only, the default)

```sh
python3 <skill>/scripts/survey.py                 # the six registered apps
python3 <skill>/scripts/survey.py stratdesk       # one app
python3 <skill>/scripts/survey.py --all --md <scratchpad>/survey.md --json <scratchpad>/survey.json
```

The survey reads manifests, lockfiles, Dockerfiles and CI files, runs `npm audit --package-lock-only`, and queries the npm registry and the Node release schedule. It never installs anything and never writes inside a repo. It takes about a minute for everything.

Report to the owner using [templates/survey-report.md](templates/survey-report.md):
- P1 and P2 items with one line of context each
- the suggested groups for the project they care about
- the data gaps

Check a high or critical advisory before calling it urgent (see [policy § advisories](references/policy.md)).
Done: the report has been delivered, and nothing changed.

## Mode B: upgrade one project

Each step ends with its "Done:" check. Stop at the first failure and read [troubleshooting](references/troubleshooting.md).

**1. Worktree**
```sh
cd /Users/admin/Documents/CodeProjects/<repo>
git fetch origin
git worktree add ../.upgrade-worktrees/<repo> -b chore/deps-$(date +%Y%m%d) origin/main
cd ../.upgrade-worktrees/<repo>
```
- For a VPS app, compare `origin/main` with the deployed revision in `PROJECT_KNOWLEDGE.md`. If `main` contains unreleased feature commits, ask whether to branch from the deployed revision instead.
- Write down which commits the branch inherits, so they're disclosed at release time.

Done: a clean worktree on a new branch.

**2. Baseline**
- Read the `scripts` section of `package.json` and look for `preinstall`, `postinstall`, `prepare` and migrations.
- Run `npm ci`, then the project's verify commands from `projects.md`. Record what was already failing.

Done: the baseline results are written down. A failure that already existed is not something the upgrade broke.

**3. Select.** Start from the survey's suggested groups and apply [policy.md](references/policy.md). Write a table with columns: group, package, from, to, reason, risk. Defer anything you aren't doing, with a reason. For each major, read its section in [frameworks.md](references/frameworks.md) and the official migration guide.

**4. Apply, one group at a time**
```sh
npm install <pkg>@<version> ...      # exact versions from the selection table
npm ls --all >/dev/null              # no invalid or missing peer trees
<verify commands from projects.md>
git add package.json package-lock.json <compat fixes> && git commit -m "deps: <group>"
```
- Compatibility fixes go in the same commit as the group that needs them.
- If a group can't be made to work without breaking rule 6, reset to the previous commit, defer that group with the evidence, and carry on with the others.

Done: every selected group is committed, or deferred with a reason.

**5. Verify the whole branch**
```sh
rm -rf node_modules && npm ci
npm audit --json; npm audit --omit=dev --json
<every verify command from projects.md, including e2e>
python3 ops/release.py build --record .releases/deps-<rev12>.json    # if the repo has ops/release.py (schema 2)
```
- **Without `ops/release.py`:** run `docker buildx build --platform linux/amd64 --load -t <repo>:deps-check .`. Start the image on a loopback port with fake env values (no production `.env`, outbound integrations disabled), and check its health route and one real page. Then remove your container and image. Recommend onboarding through `vps-container-release` Path B.

Done: each check has a result. Anything not covered is listed as not covered.

**6. Review the diff**
```sh
git diff origin/main --stat
git diff origin/main --check
grep -o '"resolved": "[^"]*' package-lock.json | grep -v 'https://registry.npmjs.org/' | head   # expect nothing
```
Every changed file should be explained by a group. Session artifacts and stray generated files don't belong in the diff.

**7. Record.** Add a dated entry to the vault `PROJECT_KNOWLEDGE.md` using [templates/upgrade-record.md](templates/upgrade-record.md). GarageERP's `docs/release-journal.md` and `lib/release-journal.ts` are updated when it's released, not before.

**8. Hand off.** Report the branch, the commits, the checks and the deferrals. The state is **prepared**: committed locally and verified, but not pushed. If the owner wants it in production, the next step is `vps-container-release` Path A.

## Mode C: Node or base-image bump

Mode B, plus these steps:
- Target the newest **active LTS** that every dependency supports (`npm ls` engines warnings, native modules). See policy.md.
- Update every pin the survey listed (`.nvmrc`/`.node-version`, `engines`, each Dockerfile `FROM`/`ARG NODE_IMAGE`, workflow `node-version`). Add the pins that are missing (a `.nvmrc`, and `engines` with the new floor).
- Pin each base image by digest: `docker buildx imagetools inspect node:<major>-alpine --format '{{json .Manifest.Digest}}'`, then write `node:<major>-alpine@sha256:<digest>`.
- Bump `@types/node` to the new runtime major in the same commit.
- Verify with a container build in every case, since the Docker build is where a Node change shows up.
- Read [frameworks § Node.js](references/frameworks.md) and § Alpine.

## Other files

- [references/policy.md](references/policy.md): what to update, when, and how to group it.
- [references/frameworks.md](references/frameworks.md): per-tool notes on migrating majors.
- [references/troubleshooting.md](references/troubleshooting.md): install, resolver, network, Docker and sandbox failures.
- Changing the survey: `python3 -m unittest discover -s <skill>/scripts -p test_survey.py`. Keep `PROJECTS` and `projects.md` in sync.
- Out of scope: releasing (`vps-container-release`), feature work, adding new dependencies without the owner's OK, and Python/Swift projects.
