# Stateful releases: data, migrations, volumes

Read this when a release touches a database, volume, upload directory, queue or scheduled/outbound job.
An image rollback never reverts data. Plan the data path before asking for approval.

## Decide whether this release changes state

- Diff the migrations directory and schema files between the deployed revision and the candidate: `git diff <deployed>..<candidate> -- <migrations path>`.
- Inspect the entrypoint and start command for automatic migrations. A container that migrates on start makes every deploy a migration. Move that into a `job` service before onboarding finishes.
- No state change → `migrate` is not needed. If the project has a job service, `--no-schema-change` documents that decision.

## Compatibility

Answer before approval:
1. Can the **old** version run on the **new** schema? If yes, image rollback stays possible after migrating. Say so in the approval summary.
2. If not, rollback means a forward fix or a data restore, with possible loss of data written since the backup. Get explicit approval for that risk, and a maintenance window if needed.

`rollback` refuses after a recorded migration unless `--schema-compatible` is passed. Pass it only when the owner has confirmed point 1.

## Backup before migrate (client-postgres)

On the VPS, as root. Credentials come from the environment, never the command line:

```sh
mkdir -p /root/backups/<project> && chmod 700 /root/backups/<project>
docker exec client-postgres pg_dump -U clientuser -Fc <dbName> > /root/backups/<project>/<dbName>-$(date -u +%Y%m%dT%H%M%SZ).dump
pg_restore --list /root/backups/<project>/<file>.dump >/dev/null && echo "archive readable"
```

- Pass the file path as `--backup-ref`.
- Report precisely what was done: *backup created*, *archive readable*, and *restore proven* are three different claims. Restore is proven only by restoring into a scratch database (`createdb <db>_restore_check` → `pg_restore -d` → spot-check → `dropdb`).
- `df -h /` first: the disk is tight (see vps-facts.md).

## Order on release day

1. `status`, then `preflight`.
2. Backup, or decide `--no-schema-change`.
3. Approval (see templates/approval-summary.md).
4. `migrate`.
5. `deploy`.
6. Verify, including one real read/write path.

Migrating first is correct when the new schema is backward compatible (expand, then contract).
If it is not, the old app may fail between steps 4 and 5. Decide whether a short outage is acceptable, or stop the app first. Either way, it needs approval.

## Volumes

- Declare every persistent mount in `services.<name>.mounts`. The helper refuses to touch a container whose mounts differ from the config.
- Named volumes are scoped by Compose project. Keeping the project name unchanged keeps the data.
- Back up a volume before a release changes its format: `docker run --rm -v <project>_<vol>:/v:ro -v /root/backups/<project>:/b alpine tar czf /b/<vol>-<stamp>.tgz -C /v .`

## Smoke and rehearsal never use production state

They get fake env values (`smoke.env`), throwaway volumes and an isolated network. A test DB, if needed,
comes from `smoke.extraServices`. Keep outbound integrations (mail, ntfy, webhooks, external APIs) disabled with a
flag in `smoke.env`.
