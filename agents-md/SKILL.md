---
name: agents-md
description: Create, review, or update concise AGENTS.md and CLAUDE.md instructions for code repositories. Use when a project needs agent setup, scoped instructions, verified commands, or links to authoritative project documentation.
---

# Maintain repository agent instructions

Write the smallest instruction file that helps an agent work correctly in this repository. Preserve the user's requested scope and any existing project policy.

## Inspect

1. Read existing `AGENTS.md` and `CLAUDE.md` files in the repository and its ancestor directories. Inspect nested files when the task touches their subtrees. Treat nested instructions as narrower guidance; resolve conflicts using authority and scope, not a blanket “closest file wins” rule.
2. Check the README, relevant project docs and policies, package manifest and lockfile, task runners, CI workflows, code layout, tests, and generated-file rules. Use this evidence to identify the actual package manager, commands, and constraints.
3. For Stratcore projects under `/Users/admin/Documents/CodeProjects/`, read [CodeProjects AGENTS.md Methodology](</Users/admin/Documents/Obsidian-Stratcore/CodeProjects AGENTS.md Methodology.md>) and locate the corresponding vault project note when one exists. Before using vault notes as requirements or editing them, read the vault root `AGENTS.md` and respect note status and credential rules.

## Scope and content

- Put repository-wide rules in the root file. Add a nested file only for distinct subtree behavior; keep shared rules in the parent.
- State the project's purpose in one sentence, then include only instructions that change behavior: authoritative references, non-obvious constraints, generated files, required tools, and relevant validation.
- Use exact repo-relative paths for files in the repository and exact paths for external documents. Say when each reference applies. If no authoritative project note exists, use current repository sources and avoid inventing requirements.
- Copy commands from verified manifests or documentation. Prefer a focused command when it satisfies the task; retain a documented full-project gate when the project requires one.
- Keep guidance easy to scan, usually within one screen. Use headings, bullets, or a table when they help. Avoid copied README content, generic quality slogans, configuration restatements, and unverified claims.
- Keep secrets, credentials, and connection strings out of instruction files and examples.
- Preserve existing `AGENTS.md` / `CLAUDE.md` relationships. Create a pointer or symlink only when the repository needs it and the target workflow supports it. Add commit-attribution rules only when an existing project policy requires them.

## Finish

Read the completed file as an agent would. Verify every referenced path and command, confirm that the root/nested scope is correct, and check the diff for unrelated changes. Report what changed and any unresolved uncertainty. Run project checks when the user requests verification or the change affects executable behavior; editing agent instructions alone does not require executing the application test suite.
