---
name: nodejs-project-upgrade
description: Audit and upgrade dependencies, Node.js toolchains and container build inputs in JavaScript or TypeScript projects using npm, pnpm or Yarn. Use for dependency maintenance, vulnerability remediation and supported-version upgrades, with isolated changes and application verification before deployment.
---

# Node.js project upgrade

Produce a reviewable dependency update with compatibility evidence. Use the project's
existing package manager and delivery model. This skill does not authorize pushing,
package/image publication, deployment, production writes or database migrations.
Existing explicit user authorization takes precedence; do not ask for it twice.

## 1. Establish the baseline

Locate the requested repository; discover its real path under CodeProjects when needed.
Read applicable AGENTS.md, project knowledge, existing maintenance/deployment docs and
phase gates where present. Record repository, branch, HEAD, remote, status, manifests,
lockfile(s), workspaces, Node/package-manager versions and Docker build inputs if present.
Resolve package-manager selection from project configuration; do not mix lockfile formats.

Preserve unrelated changes. Prefer a separate branch/worktree based on an explicit revision.
Record inherited unpublished commits: a dependency-only tip does not make its branch history
dependency-only. Run all installs, edits, builds and tests from the isolated worktree root
(or its documented workspace subdirectory), not the original checkout.

Run a clean/frozen install and existing baseline checks, inspecting lifecycle scripts first
for migrations or live integrations. Compare production inputs read-only if deployed and
access is authorized; record inaccessible evidence without blocking independent local work.
Keep secret values out of commands, logs and reports.

Done: baseline and existing failures are recorded, unrelated work is preserved and execution
uses isolated data/configuration. Workspace creation alone is not task completion.

## 2. Audit and select updates

Use outdated/audit facilities supported by the installed package-manager version. Record
direct/transitive dependency paths, runtime/development classification, advisory IDs,
affected versions and exposure evidence. Check current official advisories, support policies
and migration guides, especially for framework, Node.js and major-version upgrades.
Package-manager audit output alone does not establish exploitability or support status.

Assess runtime dependencies, development tooling, types, Node.js, package-manager pins and
container bases where applicable. Prefer compatible supported updates with practical benefit;
evaluate majors individually. A major may be necessary when the current line is unsupported.
Keep peer-coupled packages aligned, including framework/lint and test/coverage pairs.
For React-like version transitions, classify actual semver changes rather than package names.

Done: selected versions have reasons, compatibility requirements and source evidence;
deferred updates have specific reasons. Do not promise that zero findings means vulnerability-free.

## 3. Implement and resolve tooling failures

Update in coherent groups through the existing package manager; let it generate the lockfile.
Include necessary compatibility fixes and focused tests for changed non-trivial behavior.
Keep unrelated features, styling and architecture outside the diff. Do not force audit fixes,
bypass peer constraints or delete the lockfile indiscriminately.

Preserve behavior, schema, authentication and integrations. If an upgrade needs an otherwise
unauthorized change to these boundaries, prepare the concrete options and ask before that work.
Toolchain/base changes must remain aligned across local configuration and Docker stages.
Inspect lockfile changes for unintended registry URLs or unrelated package churn.

For DNS, permission, stalled install or resolver failures, read
[troubleshooting](references/troubleshooting.md). Continue routine diagnosis autonomously.
Monitor your running commands through completion; do not report a running install/build as
a final blocker. Stop dependent work only when supported remedies are exhausted or require
an owner decision. Complete unaffected work and provide the exact remaining blocker.

Done: changes are limited to justified upgrades/fixes, installs complete, and deferred work
is explicit. A verified partial update is acceptable when the remainder is concretely blocked.

## 4. Verify the updated application

Repeat clean/frozen installation, full and runtime-focused audit where supported, existing
lint/type/unit checks and production build. Use repository commands rather than assuming
`npm run check` exists. Add integration/E2E checks appropriate to the upgrade's impact.
Separate baseline failures, infrastructure restrictions and actual compatibility regressions.

For containerized projects, build the actual production Dockerfile for the verified target
platform(s); do not assume AMD64. Smoke-test that image using isolated volumes, synthetic
configuration and test databases/services where required. Disable live SMTP, outbound jobs,
production queues and paid integrations. Inspect entrypoints for automatic migrations.
Use loopback-only ports and clean up only your own temporary test resources.
For non-containerized projects, validate their actual delivery artifact instead.

Verify meaningful behavior, not just process startup. A database health 503 without a test
database is a startup-only observation, not a health pass. Record local image/config IDs and
platform; distinguish these from registry/index/manifest digests. No publication is needed.

Done: each applicable check has an outcome and any missing functional coverage is explicit.
Do not claim full compatibility when the production build or required checks remain blocked.

## 5. Review and hand off

Inspect the exact diff against the baseline and classify every changed file. Exclude session
artifacts, secrets, unrelated assets and generated output unless intentionally required.
Run diff whitespace checks. If committing is authorized, stage explicit reviewed paths,
inspect the staged diff and create a dependency-focused commit. Otherwise leave a reviewed diff.
Before any separately authorized push, inspect every outgoing commit against the actual target
remote branch; disclose inherited unpublished application commits and their publication scope.

Write/update the project's maintenance record with:

- Baseline, inherited commits, branch/worktree and read-only production comparison/gaps.
- Before/after versions, compatibility fixes, current advisory references and deferred updates.
- Exact successful commands, tool versions, execution context and required access.
- Check results, image/platform identity where applicable and verification limitations.
- Proven troubleshooting resolutions separately from unsuccessful attempts or unresolved issues.
- Changed files, commit if created, and explicit push/deploy status.

Done: the owner can review the update and repeat the successful process without reconstructing
session history. Report incomplete work candidly; do not turn preparation into a completion claim.
