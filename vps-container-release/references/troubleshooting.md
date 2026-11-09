# Troubleshooting `Release stopped:` messages

Every refusal is deliberate. Fix the cause and never bypass the check.

| Message (start) | Meaning | Do |
|---|---|---|
| `release-config.json must be schema 2` | Repo still on helper v1 | onboarding.md § adopting a schema-1 repo |
| `Build requires a clean committed checkout` | Uncommitted or untracked files | Commit, or build from a clean worktree |
| `Checks changed the source checkout` | A check wrote files (formatter, generated code) | Commit the generated output, or fix the check |
| `Output record already exists` | Each candidate needs its own record | Use a new `.releases/<name>.json` |
| `Push the reviewed source commit before publishing` | Remote branch head ≠ built revision | `git push`, then publish again |
| `... already exists; never overwrite a release tag` | Same commit was published before | Reuse that record, or make a new commit |
| `Cannot establish tag absence` / `denied` / 401 | GHCR token missing or expired | `docker login ghcr.io` (Mac: write:packages; VPS: read:packages) |
| `Release bundle changed` | Bundle files differ from the record | Re-transfer the bundle; never edit files on the VPS |
| `Current image of X changed` | Someone deployed or restarted since `status` | Re-run `status`, re-review, get approval again |
| `persistent mounts ... differ` | Config doesn't describe the running container | Fix `mounts` in the config (a reviewed repo change) |
| `published port is not 127.0.0.1:N` | Port drift, or a wrong config | Investigate the live container; don't "fix" production in passing |
| `Runtime env file must be chmod 600` | Env file is readable by others | `chmod 600 <file>` (tell the owner) |
| `Approval must name exactly the target digest(s)` | Approval doesn't match the record | Copy the digests from the approval summary |
| `A migration ran for this release` | Rollback after migrate | stateful-releases.md § compatibility, and ask the owner |
| `Another release operation holds the deployment lock` | Concurrent operation | Wait for it, and find out who is running it |
| `Services were started from different compose files` | Mixed manual history | Capture the previous state by hand (`docker inspect`, compose files) before going on |
| `deployment-failed; rollback required` | Deploy didn't reach healthy | Run the reviewed rollback command from the state dir it printed |

Smoke fails while the app works in production → usually missing fake values in `smoke.env`, or an
outbound dependency. Add a `smoke.extraServices` stub or a disable flag rather than real credentials.
