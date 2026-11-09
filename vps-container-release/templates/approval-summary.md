# Release approval: <project> <rev12>

Show this to the owner and wait for an explicit "deploy" answer. Fill every field and write "none" rather than leaving one out.

| | |
|---|---|
| Project / mode | <project> / <production\|preview> |
| Source | <full revision> on <branch>, pushed to <remote> |
| Change | <1-3 lines: what users will notice; "no visible change" for onboarding> |
| Target image(s) | <key>: `ghcr.io/thestratcore/<pkg>@sha256:<digest>` |
| Current image ID(s) | <service>: `sha256:<id>` (from status, <capturedAt>) |
| Services replaced | <list>; untouched: Caddy, Authelia, client-postgres, n8n, other projects |
| Config diff | <compose/config changes vs the currently running model, or "none"> |
| Checks passed | <tests>, smoke <paths>, rehearsal <file>, preflight <time> |
| Data | <no state change \| migration X, backup <path>, old app compatible with new schema: yes/no> |
| Expected impact | <seconds of restart per service / maintenance window> |
| Rollback | `python3 ops/release.py rollback --state /root/release-state/<project>/<dir> --approve-image-id sha256:<previous>` <plus --schema-compatible only if confirmed> |
| Not verifiable by agent | <e.g. authenticated browser session behind Authelia> |

Commands that will run after approval (from `/root/release-preparation/<project>/<rev>/`):

```sh
python3 ops/release.py migrate ...   # only if Data says so
python3 ops/release.py deploy --record release.json --expected current.json \
  --approve-digest sha256:<digest> --state-root /root/release-state/<project>
```
