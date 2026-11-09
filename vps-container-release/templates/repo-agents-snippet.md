<!-- Paste into the repo's AGENTS.md / CLAUDE.md -->
## Releases to the Stratcore VPS

- Use the `vps-container-release` skill and `ops/DEPLOYMENT.md` for any build, publish, deploy or rollback.
- `ops/release.py` is a vendored copy of the skill's helper, so don't edit it here. Change it in the skill, then re-vendor.
- Production runs only reviewed GHCR digests via `ops/compose.production.yml`. Never build, `git pull` or edit files on the VPS.
- Publishing is not approval: wait for the owner's explicit OK on the approval summary before `migrate` or `deploy`.
- Secrets stay in the VPS env file(s) named in `ops/release-config.json`, never in Git, images, records or chat.
- After a release, add a dated entry to the project's PROJECT_KNOWLEDGE.md: revision, digest, state dir, checks, gaps.
