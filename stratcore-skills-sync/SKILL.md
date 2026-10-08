---
name: stratcore-skills-sync
description: Sync Stratcore's personal agent skills so MySKILLS, ~/.codex/skills and ~/.claude/skills hold the same set — missing skills copied in every direction, the newest version kept when copies differ — then optionally commit and push MySKILLS to its Git repository.
disable-model-invocation: true
---

# Stratcore Skills Sync

Use this microskill when the user asks to check, sync, install, or copy skills
between the Stratcore personal collection and the agent skill directories.

The implementation is:

`/Users/admin/Documents/Obsidian-Stratcore/MySKILLS/sync_skills.py`

## What it syncs

- **Hubs** — end up identical: `MySKILLS/` (source), `~/.codex/skills`,
  `~/.claude/skills`.
- **Feeders** — read-only, only contribute skills: the vault's own
  `.claude/skills` and `.codex/skills`. They never receive copies.

A folder counts as a skill only if it holds a `SKILL.md`. Folders starting with
`_` or `.`, `synced` (Claude's sync cache) and `*-workspace` folders (eval
workspaces) are never synced. `.DS_Store` files are ignored when comparing.

Rules:

1. A skill missing from a hub is copied there from wherever it exists.
2. When copies differ, the copy whose newest file is latest wins and replaces
   the others as a whole folder, so files only in older copies are removed.
3. The replaced folder is moved first to
   `MySKILLS/_MySKILLS-zips/sync-backups/<timestamp>/` — `~/.claude` and
   `~/.codex` are not under git, so this is the only undo.
4. Different content with the same newest timestamp is a **tie**: reported,
   left alone, and must be resolved by the user.
5. Unhealthy copies (bad frontmatter, broken symlinks) are reported and never
   overwritten or used as a source.

## Workflow

Always run in this order and stop at each checkpoint.

1. **Plan** — audit only, nothing changes:

   ```bash
   python3 /Users/admin/Documents/Obsidian-Stratcore/MySKILLS/sync_skills.py
   ```

   Summarize for the user: skills to copy (and where), skills to replace (which
   copy wins and its date), ties, errors, and any secret-looking content in
   skills being copied.

2. **Checkpoint** — wait for the user to confirm the plan.

3. **Apply** — executes the plan and verifies all hubs are identical:

   ```bash
   python3 /Users/admin/Documents/Obsidian-Stratcore/MySKILLS/sync_skills.py --apply
   ```

   Report what was copied, replaced (with backup paths), and the verify line.

4. **Commit and push** — only when the user asks:

   ```bash
   python3 /Users/admin/Documents/Obsidian-Stratcore/MySKILLS/sync_skills.py \
     --commit --push --commit-message "chore(skills): sync personal skills"
   ```

   The commit is refused if a changed path has a sensitive-looking name or a
   changed file contains secret-looking content (private keys, API tokens,
   passwords, URLs with credentials). Show the findings to the user; do not
   edit or bypass them yourself.

After a sync that adds skills, offer to update the skill tables in
`MySKILLS/README.md`.

## Options

- `--json` — machine-readable report.
- `--destination PATH` (repeatable) — replaces the default non-source hubs.
- `--feeder PATH` (repeatable) — replaces the default feeders.
- `--remote NAME`, `--branch BRANCH` — for non-default Git setups. `--push`
  requires `--commit`.

Never add `--apply`, `--commit`, or `--push` without the user's go-ahead.
