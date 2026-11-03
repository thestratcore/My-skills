---
name: manual-container-release
description: Prepare, publish, manually deploy and roll back Docker applications built from CodeProjects repositories. Use for onboarding a project to versioned image releases or releasing an existing static app, application server, worker or multi-service application through a registry and Docker Compose.
---

# Manual container release

Use a committed source revision, build once on the development machine, publish a
versioned image and deploy its immutable digest. Keep project identities and exact
commands in the project's deployment contract, not in this skill.

Local builds → private GHCR → manual Docker Compose deployment is the current default.
Discover the target architecture; do not assume AMD64 from the workstation architecture.
Use another registry or runtime only when the project or owner specifies it.
GitHub Actions, dependency upgrades and infrastructure migrations are outside this workflow.

## 1. Resolve the project and scope

Locate the requested repository under `/Users/admin/Documents/CodeProjects`; inspect
actual directories rather than guessing a suffix. Read applicable agent rules and project
knowledge. Use existing deployment documentation; for a new or incomplete setup, read
[the deployment contract](references/project-contract.md) and fill it from evidence.

Identify the application's complete release unit: web/API/worker services, associated
images, persistent data and shared dependencies. Compare local source, remote Git,
production sources and runtime identities. Preserve production-only changes before
reconciliation; keep unrelated work intact, preferably using an isolated worktree.

Done: source inputs, current release, target environment, deployment scope and data
requirements are known. Mark inaccessible evidence explicitly; stop only dependent work.

## 2. Prepare a reproducible candidate

Use the project's verified commands or implement the missing release steps within the
requested scope. Existing helpers are implementation options, not prerequisites.
Inspect their assumptions before reuse. In particular, a single-service static-app helper
is unsuitable unchanged for databases, workers, multiple ports or coordinated releases.

Run existing checks appropriate to the change. Build from a clean committed checkout
with pinned/locked inputs and an explicit target platform. Record build-time configuration;
keep runtime secrets out of the image, Git, command arguments and release record.
Smoke-test the actual image in isolation with test data and safe integration settings.
Never point a rehearsal at production databases, queues or outbound jobs.

Publish a unique commit-specific tag once; record the registry digest, platform and source
revision. For a rebuild of the same commit use a new unique build suffix. Verify visibility
and target pull access. Git SSH access does not authenticate a container registry.
Workstation publishing credentials need write access; production credentials need pull access.

Done: candidate source is pushed, checks and image smoke tests passed, immutable image
references and configuration hashes are recorded. Publishing is distinct from deployment.

## 3. Preflight and review

Transfer a restricted release bundle or use an equivalent verified project mechanism.
Check capacity, current runtime identity, target image availability and effective Compose
configuration without recreating services. Keep build steps off production.

For stateful or coordinated releases, follow the data/recovery section of the deployment
contract. Establish migration order, compatibility, recoverable backups and any maintenance
requirement before cutover. Image rollback alone does not reverse database changes.

Present the exact source/image targets, current identity, affected services, configuration
diff, expected impact and executable rollback procedure. Obtain production authorization
unless it already explicitly covers this replacement. Preparation is not deployment approval.

Done: prerequisites are met and the concrete replacement is authorized. If not, retain
prepared artifacts and report the specific blocker.

## 4. Deploy, verify and retain

Use the project's reviewed command. Enforce the expected current identity immediately
before replacement and prevent simultaneous deployments. Capture the previous effective
configuration and exact images first. Replace only the approved services, without builds,
unrelated dependency restarts or implicit migrations. An initial deployment has no previous
image; document its recovery procedure explicitly.

Verify running image/revision, health and meaningful application behavior. Check proxy,
authentication and public access separately where applicable. For workers, verify readiness
and job processing using safe test work. Record unavailable checks rather than implying success.
If deployment fails, execute the reviewed rollback within its authorization and compatibility
limits; stop if another operator has changed the target or data recovery needs a new decision.

Retain previous images, effective configuration, runtime secret references and required data
recovery artifacts. Preserve active Compose bundles even when stored under a preparation path.
Update project knowledge with deployed identity, timestamps, checks, rollback location and gaps.
Distinguish backup creation, integrity checks and proven restoration.

Done: the release is verified or its failure/recovery state is explicitly recorded.

## Supporting files

- [Project contract](references/project-contract.md): onboarding fields, release record,
  stateful-service requirements and helper compatibility checks. Read when adopting a new
  repository or changing its deployment topology.
- [AGENTS.md](AGENTS.md): concise block to adapt into repository agent instructions.
- [Historical verification](references/verification.md): prior project executions and limits;
  consult only for those projects or when assessing the legacy helper.
- `scripts/rehearse.py`: legacy static-app Docker Desktop rehearsal, **not a universal runner**.
  It assumes the old helper schema, one service and internal port 8080, and contains a fixed
  container-name substitution. Use only for previously verified fixtures after inspection;
  use project-specific isolated tests for other deployment shapes.
