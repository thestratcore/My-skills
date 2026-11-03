# Project deployment contract

Maintain this information in the application's existing deployment runbook, conventionally
`ops/DEPLOYMENT.md`. Use existing authoritative configuration rather than duplicating values.
The fields below are documentation requirements, not a schema consumed by a generic CLI.

## Project configuration

| Area | Required facts |
|---|---|
| Source | Repository/workspace, remote, release branch policy, build context and Dockerfile(s) |
| Build | Toolchain, lockfiles, existing checks, target OS/architecture, build args and base-image pins |
| Artifacts | Registry namespace/package for each built service, visibility and unique-tag convention |
| Target | Host/access context, Compose project/files, exact service names, deployment directory |
| Runtime | Commands, ports, routes, health/readiness checks, limits, networks and restart policies |
| Configuration | Runtime files, secret locations/references, external integrations and owners if known |
| State | Every volume/bind mount/database, ownership, backup and recovery dependencies |
| Release | Explicit build, smoke, publish, preflight, deploy, verify and rollback commands |
| Evidence | Release-record, previous configuration and rollback-state storage/retention |

For new projects, choose the smallest layout that meets these requirements. A static site
may need one image and one Compose service. A web/API/worker application may need several
images and ordered replacements; name the exact subset included in each release.
Do not restart a shared database or proxy merely because the app depends on it.

## Release record

Record without secrets:

- Full source revision(s), pushed remote, build-input/configuration hashes and platform.
- Per-service immutable image digest, local image ID where applicable, tag and source labels.
- Build, publish and deployment timestamps as distinct events; checks and their outcomes.
- Expected current runtime identity, target Compose/configuration hashes and secret references.
- Previous image/configuration identities, rollback command/state and data compatibility limits.
- Observed deployed identities, application checks and unresolved evidence gaps.

For multi-platform images distinguish the registry index digest, selected platform manifest
and runtime image/config ID; these are different objects. Compare the appropriate identities.
Never assume that an image tag alone identifies source or that a healthy process proves the app.

## Stateful services and migrations

List all state touched by the release, including shared databases, uploads, queues and
scheduled/outbound integrations. Determine whether old and new app versions can operate
against the same schema and data. Inspect entrypoints for automatic migrations.

For a release changing persistent state, specify:

- Consistent backup method, timestamp/coverage, storage and available restore evidence.
- Migration command, execution order, expected locks/downtime and authorization.
- Whether app rollback is compatible with the changed schema; otherwise a forward fix or
  explicit data recovery procedure, including potential data loss and maintenance needs.
- Isolated validation using separate volumes/databases and disabled production integrations.

An unchanged database need not be redeployed or restored for an ordinary code release.
Validate the actual release's compatibility rather than imposing a migration on every release.
If safe validation requires a production pause, obtain approval for that impact first.

## Existing tooling compatibility

Inspect project scripts before execution. Check service count, names, ports, health paths,
platform, persistent mounts, migration behavior, registry namespace and rollback semantics.
Reuse safety logic when applicable; adapt configuration for differences it actually supports.
When assumptions differ, implement and test project-specific steps instead of pretending
that renaming a static application makes its helper universal.

The historical `ops/release.py` copies in the initial example projects support a restricted
single-service static deployment. The bundled `scripts/rehearse.py` is likewise restricted
and must not be used as a general onboarding tool. Historical success is evidence for those
fixtures only. Rehearse changed deploy/rollback logic against isolated resources before cutover.
