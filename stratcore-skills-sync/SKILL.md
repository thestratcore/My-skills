---
name: stratcore-skills-sync
description: Audit and install Stratcore's personal agent skills into the user's global Codex and Claude skill directories without overwriting existing entries, and explicitly commit and push MySKILLS changes to its dedicated Git repository.
disable-model-invocation: true
---

# Stratcore Skills Sync

Use this microskill when the user asks to check, validate, install, copy, or
sync skills from the Stratcore personal collection.

The persistent implementation is the source-of-truth script:

`/Users/admin/Documents/Obsidian-Stratcore/MySKILLS/sync_skills.py`

## Execution

Run an audit first:

```bash
python3 /Users/admin/Documents/Obsidian-Stratcore/MySKILLS/sync_skills.py
```

Copy healthy skills only when the user explicitly requests installation or
syncing:

```bash
python3 /Users/admin/Documents/Obsidian-Stratcore/MySKILLS/sync_skills.py --apply
```

Commit the current `MySKILLS` repository changes explicitly:

```bash
python3 /Users/admin/Documents/Obsidian-Stratcore/MySKILLS/sync_skills.py \
  --commit --commit-message "chore(skills): sync personal skills"
```

Commit and push to the configured `origin` remote explicitly:

```bash
python3 /Users/admin/Documents/Obsidian-Stratcore/MySKILLS/sync_skills.py \
  --commit --push --commit-message "chore(skills): sync personal skills"
```

Use `--remote NAME` and `--branch BRANCH` when the repository does not use
`origin` and the checked-out branch name. `--push` requires `--commit`.

The default destinations are:

- `/Users/admin/.codex/skills`
- `/Users/admin/.claude/skills`

## Operating rules

1. Inspect the source collection before copying.
2. Report duplicate skill names, duplicate `SKILL.md` content, and duplicate
   package representations.
3. Treat a directory as healthy only when it contains a readable `SKILL.md`
   with valid required frontmatter and no broken symlinks.
4. Skip unhealthy directories and `.skill` package archives. Prefer the
   unpacked directory representation.
5. Treat any existing destination entry as occupied. Never merge, replace,
   delete, or overwrite it.
6. Verify copied directory content using the script's post-copy hash check.
7. Report errors, skipped entries, and copies explicitly.
8. Before committing, refuse to stage paths whose names look like credentials
   or secrets. Resolve those files manually before retrying.
9. Stage all changes in the `MySKILLS` repository only when `--commit` is
   present. Push only when `--push` is also present.

Use `--json` when a machine-readable report is required. Use repeated
`--destination PATH` arguments only when the user explicitly supplies
alternative destination roots.

The script is audit-only unless `--apply`, `--commit`, or `--push` is present.
Do not add any mutating flag implicitly. A normal sync-and-publish run is:

```bash
python3 /Users/admin/Documents/Obsidian-Stratcore/MySKILLS/sync_skills.py \
  --apply --commit --push
```
