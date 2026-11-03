# Manual container release instructions

Adapt this block into a repository's agent context. Keep project facts and executable
commands in its deployment runbook; this file does not configure a target application.

- For release preparation, publishing, deployment or rollback, read the
  `manual-container-release` skill and the project's deployment contract/runbook.
- Resolve repository, target host/platform, registry, services and persistence from
  project configuration. Preserve production-only source changes before reconciliation.
- Default to local builds, private GHCR and manual digest-based Docker Compose deployment.
  Keep project-specific commands in the repository; use existing verified tooling when compatible.
- Build from committed inputs, test the actual image and record source, digest and effective
  configuration separately. Preserve unrelated work and current runtime behavior.
- For databases or other persistent state, document backup, migration compatibility and
  data recovery before replacing services. An image rollback cannot undo data changes.
- Present a concrete tested replacement and rollback before the production approval gate;
  existing explicit authorization applies. Preparation and publication do not authorize cutover.
- Preserve routing, authentication, ports, resource limits and release mode unless separately
  authorized. Scope changes to the approved services and retain previous images/configuration.
- Keep secrets in the established runtime mechanism and registry credential store, outside
  source, images and evidence output. Record secret references, never secret values.
- Verify runtime identity and meaningful behavior; distinguish prepared, tested, published,
  pulled, deployed and verified states. Record limitations and update project knowledge.
- Build-info UI/endpoints are optional per project. When present, generate version/commit/
  build time from the same build object; retain publish/deploy times in release records.
