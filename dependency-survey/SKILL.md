---
name: dependency-survey
description: Run, read, or maintain the weekly read-only dependency and vulnerability survey that covers every project in /Users/admin/Documents/CodeProjects (Node, Python, Swift, Docker images, Appsmith) and emails a P1/P2 summary every Monday. Use when the user says run the dependency survey, weekly security report, what's vulnerable across my projects, why didn't the Monday report arrive, add/archive a project in the survey, or change the survey schedule or email. For upgrading a single project use nodejs-project-upgrade instead.
---

# Dependency survey

Everything lives in `/Users/admin/Documents/CodeProjects/StratcoreDependencyReports-md`, a private repo at
`github.com/thestratcore/stratcore-dependency-reports`. Read its `README.md` first; it is the source of truth.

## Hard rules

1. The survey is read-only for the surveyed repos. Never add install, build, fix or branch steps to it.
2. Secrets stay in the macOS Keychain (service `stratcore-dependency-survey`: `webhook-url`, `webhook-token`).
   Never print the token, and never write it to a file, the repo, the vault or chat.
3. A data gap means "not checked". Never report it as "up to date". Zero advisories doesn't mean "secure".
4. Patching is a separate, owner-started task. Recommend a fix; don't apply it.

## Tasks

**Run it now.** Run `cd <repo> && python3 -m depsurvey.run`. That writes `reports/<date>.md`, commits, pushes and sends the email.
For a dry run, add `--no-push --no-mail --out <scratchpad>`. Summarise the P1/P2 findings from the report and give the report path.

**Read a report.** Open `reports/latest.md`. Group the same issue across projects. For static nginx sites, runtime
advisories usually affect only the build. The `Context:` line carries per-project notes, such as Silvaros, where a push to `main` deploys.

**The Monday mail didn't arrive.** Check these in order:
1. `tail -50 ~/Library/Logs/stratcore-dependency-survey.log`
2. `launchctl print gui/$(id -u)/cz.stratcore.dependency-survey | grep -E 'state|last exit'`
3. Did the Mac sleep through it? launchd runs the job on wake.
4. The n8n workflow `iRVXAIRKeiSzZT7o` (*Dependency survey: weekly email*): is it published, and what do its last executions show?
5. A 403 from the webhook means the token in the Keychain doesn't match the n8n credential *Dependency survey token*.

**Add or retire a project.** Edit the tiers in `projects.toml` (production, internal or archived), run the tests, then commit.

**Change a checker.** Edit the code in `depsurvey/`, then run `python3 -m unittest discover tests` and a `--only <project>` dry run before committing.
The Node logic itself lives in the `nodejs-project-upgrade` skill's `survey.py`, which the Node checker imports.

**Reinstall the schedule.** Run `launchd/install.sh` (Mondays 20:00). To remove it, run `launchd/install.sh --uninstall`.

## Acting on findings

- Node: `nodejs-project-upgrade` Mode B (dependency groups) or Mode C (Node or base image).
- Python and Swift: upgrade on a branch in that repo and run its tests. The finding's fix line names the target versions.
- Release: `vps-container-release`, with its own approval.
