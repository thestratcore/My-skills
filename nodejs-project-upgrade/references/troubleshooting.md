# Troubleshooting

Use only the section that matches what you observed. Record exit codes and sanitized errors, never credentials.
Keep fixes that worked separate from attempts that didn't when you write the upgrade record.

## `npm ci` fails

- **"package.json and package-lock.json are not in sync":** someone edited `package.json` by hand. In the worktree, run `npm install` (without flags) once, check that the lockfile diff only touches the intended packages, and commit it as part of the group.
- **`EBADENGINE`:** a package needs a newer Node than the local or `engines` version. Either the package needs a Mode C first, or pick an older version. Don't use `--engine-strict=false` to hide it.
- **Lifecycle script failure (`postinstall`, `prepare`):** read the script before re-running it. Never let an install script reach a real database or service.

## Peer conflicts (`ERESOLVE`) and resolver crashes

- Read the conflict tree, then upgrade the coupled packages together (see policy.md). Usually one plugin lags behind. Defer that major, or upgrade the plugin too.
- Never use `--force` or `--legacy-peer-deps`.
- npm `Cannot read properties of null (reading 'edgesOut')` is a resolver bug, not an incompatibility. Reproduce it with a clean `npm ci`. If it persists, test a newer npm through a project-scoped `npx npm@<version> install`, and record whether the lockfile format changed. Never change the global npm installation.
- If it stays unresolved, keep the last commit that works, defer the group with the evidence, and continue with the independent groups.

## Network

- Test the endpoint directly with a bounded timeout: `curl --connect-timeout 10 --max-time 20 -I https://registry.npmjs.org/`. A timeout means "unknown", not "no updates".
- `next/font/google` and other build-time downloads fail without network. Retry with network access, and don't swap fonts or disable TLS verification to get past it.
- The survey marks registry and audit failures as data gaps. Re-run it later; don't infer "up to date".

## Docker builds

- The Mac is arm64 and the VPS is amd64. `--platform linux/amd64` builds and smoke tests run under emulation, so they're slow (minutes), but slow is not a failure. Watch the build log instead of starting a second build.
- **Native module compiles during `npm ci` in Alpine:** there's no prebuilt binary for musl or the new Node ABI. Pick a package version that ships one, or defer the Node bump.
- **"Docker daemon not running":** start Docker Desktop (`open -a Docker`). Never point the Docker context at the VPS to work around a local problem.
- Clean up only the containers and images you created (`docker rm -f <name>`, `docker rmi <tag>`).

## Playwright

- **"Executable doesn't exist" or a browser version mismatch:** run `npx playwright install chromium` (or the configured browsers) after every `@playwright/test` bump.
- **Screenshot diffs:** report them with the diff images. Changing baselines needs the owner's approval.
- **Flaky timeouts after an upgrade:** re-run once. A test that fails twice the same way is a regression.

## Slow or apparently stalled commands

- Check elapsed time, CPU usage and the log tail before deciding a command is stuck. Never run two installs in the same worktree.
- If it really is stuck, stop only your own process, check the manifest and lockfile state, and retry once with `--loglevel verbose` and a timeout.

## When running in a sandbox (Codex and similar)

- A denied write to `.git/index.lock` or a branch ref usually comes from the sandbox, not file ownership. Request the supported escalation. Never delete a lock another process holds, and never use sudo, `chown -R` or `chmod` on sockets.
- **Sandbox DNS failures:** request network permission. If that's refused, report the exact rejection and the smallest action the owner needs to take.
- Having the Docker client doesn't mean you can reach the daemon. Confirm the context is the local Docker Desktop before running anything.
