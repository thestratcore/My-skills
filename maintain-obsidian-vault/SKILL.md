---
name: maintain-obsidian-vault
description: Maintain and normalize an Obsidian Markdown vault for human navigation and AI/RAG indexing. Use when Codex is asked to audit, update, cross-link, clean up, align terminology, validate frontmatter, add hub/index pages, enforce vault indexing policy, maintain PROJECT_KNOWLEDGE.md files, or keep an Obsidian vault continuously current without losing information.
---

# Maintain Obsidian Vault

## Core rule

Treat the Obsidian vault as the source of truth. Preserve existing information. Never delete, merge, rename, or archive notes without explicit user approval. Never edit credential-like files structurally.

Keep generated content deterministic and separate from handwritten content. Use
stable filenames and metadata so Obsidian, external Markdown tooling, and RAG
pipelines can address notes consistently.

## Standard workflow

1. Inventory Markdown files with `rg --files -g '*.md'`, excluding generated dependency folders.
2. Run `scripts/vault_audit.py <vault-root>` before editing.
3. Detect available vault tooling before relying on it. Use the filesystem and
   `vault_audit.py` workflow when optional Obsidian CLI or other helpers are
   unavailable; do not assume an Obsidian CLI installation.
4. Read root governance notes if present:
   - `Vault Indexing Policy.md`
   - `Canonical Terminology.md`
   - `Document Lifecycle.md`
   - `Repository Improvement Report.md`
5. Read the target notes and nearby directory context before changing links or metadata.
6. Apply minimal edits:
   - add or repair YAML frontmatter
   - add semantic wikilinks where they improve navigation
   - add `## See also` sections for genuinely related concepts
   - add hub/index pages only when they connect existing knowledge
   - add placeholder concept pages only when repeated concepts have no canonical note
7. For any approved rename, inventory inbound wikilinks first, repair every affected reference, and validate that no links were broken. Prefer leaving the filename stable when a rename has no clear benefit.
8. Validate with `scripts/vault_audit.py <vault-root> --json <report.json>` and fix unresolved wikilinks introduced by the work.
9. Report what changed, what was intentionally skipped, and remaining risks.

## Exclusions

Do not index or structurally edit:

- `node_modules/**`
- `.venv/**`
- `.pytest_cache/**`
- `.git/**`
- `.obsidian/**`
- `.next/**`
- generated caches and build output
- files whose names suggest secrets: `key`, `token`, `secret`, `password`, `credential`, `oauth`, `login`

If a secret-like file already contains generated frontmatter or `See also`, ask before changing it unless the user explicitly requested cleanup.

## Frontmatter policy

For permanent authored Markdown, ensure frontmatter has at least:

```yaml
---
title: "Document Title"
type: project
status: active
tags:
  - example
---
```

Use existing repository evidence only. Do not fabricate owners, dates, infrastructure, project status, or technical claims.
Keep frontmatter keys stable. Prefer predictable scalar values and existing
repository conventions so Obsidian search, Dataview/Bases-style views, and
external Markdown/RAG tooling can consume notes consistently.

Allowed `type` values:

- `architecture`
- `technology`
- `project`
- `guide`
- `reference`
- `decision`
- `process`
- `specification`
- `business`
- `meeting`
- `research`
- `template`
- `index`
- `archive`

Preferred `status` values:

- `draft`
- `active`
- `placeholder`
- `superseded`
- `archive`
- `unknown`

## Linking policy

Prefer concept relationships over keyword relationships.

Good links connect:

- project to company hub
- project to architecture note
- implementation note to technology concept
- duplicate draft to canonical note
- source evidence to project hub

Avoid linking every occurrence of a word. Usually link once in a section or in `See also`.

Use path-based wikilinks when duplicate filenames or ambiguous titles exist:

```md
[[Company/Bauart/BauartURS/PROJECT_KNOWLEDGE|BauartURS]]
```

## Placeholder concept pages

Create placeholder pages only when a concept is referenced repeatedly and has no canonical note.

Required placeholder wording:

```md
Generated placeholder.
```

Keep placeholder definitions conservative and supported by repository references.

## Maintenance report

When completing a maintenance pass, update or create a report section covering:

- files changed
- new hubs or placeholders
- unresolved duplicates
- stale/generated artifacts
- secret-like files skipped
- unresolved risks
- validation results

Generated sections must be reproducible across repeated runs. Mark their
boundaries clearly, update only the generated region, and preserve handwritten
content outside it.

## References

Read `references/vault-maintenance.md` when planning larger maintenance passes or designing recurring review routines.
