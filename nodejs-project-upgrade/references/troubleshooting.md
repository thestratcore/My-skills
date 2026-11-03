# Dependency-maintenance troubleshooting

Apply only the branch matching observed evidence. Commands are examples; use the actual
package manager and project paths. Record exit codes and sanitized errors, not credentials.

## Network restrictions

Distinguish sandbox DNS/access failures from unavailable upstream services. Test endpoints
separately with bounded timeouts; for example `curl --connect-timeout 10 --max-time 20 -I
https://registry.npmjs.org/`. An npm query timing out is not evidence that no update exists.
Use supported permission escalation when authorized. If it is rejected, report the exact
rejection and smallest required owner action; do not bypass the restriction.

Production builds may fetch fonts or other assets. Retry with supported network access before
changing application assets. Do not silently change typography or disable TLS verification.
Official browser-accessible advisories can support research, but do not substitute for a
successful installation/build when those remain blocked.

## Git metadata and Docker socket restrictions

A denied `.git/index.lock` or branch-ref write can come from sandbox access, not ownership.
Use supported escalation where available. Inspect actual locks before considering removal;
do not remove another process's lock. Avoid sudo, recursive ownership/permission changes,
socket chmod or hook bypasses as shortcuts.

Docker client availability does not prove daemon access. Check daemon/context with supported
access and confirm it is the intended local test environment before mutations. Never switch
to a production daemon to get around a local socket denial.

## Slow or apparently stalled commands

Poll the existing session; inspect elapsed time, process activity and relevant log tails.
Do not run competing installs in one worktree. If a command has stopped making progress,
terminate only the process you own, inspect manifest/lockfile state and retry with a bounded,
diagnostic command. ARM-host AMD64 emulation may be slow; elapsed time alone is not failure.

## Resolver crashes and peer conflicts

Capture Node/package-manager versions, stack trace and affected dependency graph. For npm,
`Cannot read properties of null (reading 'edgesOut')` is a resolver failure, not proof that
an application upgrade is incompatible. Inspect peer ranges and update coupled packages
together. Reproduce with the current manifest/lockfile in a clean isolated install before
changing resolution strategy. Preserve evidence before removing disposable installation output.

When justified, test a compatible package-manager version with a project-scoped invocation;
record its version and effect on lockfile format. Do not change the global installation or
silently bypass conflicts with force/legacy-peer flags. If unresolved, retain the last coherent
candidate, defer the affected group explicitly and verify independent updates.

## Useful npm examples

Use only for npm projects and adapt available scripts:

```sh
node --version
npm --version
npm outdated --json
npm audit --json
npm audit --omit=dev --json
npm ci
```

Outdated/audit commands can exit nonzero because findings exist; inspect their structured output
and distinguish findings from access/tool failures. pnpm/Yarn audit features and flags vary by
version: inspect installed CLI help and official documentation rather than copying npm flags.
Private registries may provide incomplete advisory coverage; disclose this limit.
