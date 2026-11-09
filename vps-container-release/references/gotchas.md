# Gotchas (learned from real releases)

From the DrezuraTop and MarcelKocian releases (2026-10-28) and building helper v2 (2026-11-09).

- **Import production drift first.** Production checkouts often carry uncommitted lockfile
  updates from maintenance. Version that state before writing release tooling, or the first release
  silently downgrades dependencies.
- **Git SSH does not authenticate GHCR.** Publishing from the Mac and pulling as root on the VPS
  use separate PATs (write vs read). Check both independently.
- **Keep the release mode.** MarcelKocian is preview/noindex. Moving it to public is a separate decision,
  never a side effect of a release.
- **Stopped containers lose their runtime port map.** Rollback reads `HostConfig.PortBindings`
  for a stopped target. That's why rollback accepts an unhealthy or stopped target and deploy doesn't.
- **Save the effective Compose model, not a filename.** Files change. `previous-compose.json` is the
  rendered model (with `--no-env-resolution`, so env-file values never land in it).
- **Profiles hide services from `compose config`.** The helper renders with `--profile '*'` so job
  services exist in derived models.
- **Same compose project name and service names, or you get a second stack.** Compose matches by labels,
  not by container name.
- **Compose `--wait` treats "running" as success for services without a healthcheck.** Give app services a
  healthcheck. Disable the image healthcheck on workers and jobs that don't serve HTTP.
- **A green healthcheck is not the app working.** Check the real route through Caddy: 200, or 302 to Authelia for
  gated sites. Cloudflare returns 403 to automated requests, so check on the origin with the right SNI:
  `curl -sk --resolve <domain>:443:127.0.0.1 https://<domain>/ -o /dev/null -w '%{http_code}\n'`.
  Report owner-confirmed browser access separately from automated checks.
- **Compare static output to show "no visible change".** Byte-identical `/usr/share/nginx/html`
  between old and new images is strong evidence for onboarding releases.
- **Multi-arch identities differ.** Registry index digest, platform manifest digest, and local image ID are
  three different objects. Records keep the registry digest (`image`) and the local image ID (`localImageId`).
  `status`, `--expected` and rollback approvals use image IDs; deploy approvals use registry digests.
- **The Mac is arm64.** Builds use buildx with `--platform linux/amd64`. Local smoke and rehearsal run under emulation (slower, same image).
- **`$` in rendered compose values** can be re-interpolated when a derived model is reused. Avoid literal `$` in
  compose values, or escape it as `$$`.
- **Earlier evidence is not authorization.** A past approval covers only that exact replacement.
