# Upgrade record (paste into the vault PROJECT_KNOWLEDGE.md as a dated entry)

```markdown
### Dependency upgrade <YYYY-MM-DD> (prepared | released <date>)

- **Branch:** `chore/deps-<date>` in `.upgrade-worktrees/<repo>`, from `<base rev>` (inherits: <none | list of unreleased commits>)
- **Toolchain:** Node <local version>, npm <version>; production Node <major> (<image@digest>)
- **Groups:**
  | Group | Packages (from → to) | Commit | Reason |
  |---|---|---|---|
  | safe batch | … | `<sha>` | P4 routine / fixes <advisory> |
  | major: … | … | `<sha>` | … |
- **Compatibility fixes:** <files and why, or none>
- **Deferred:** <package → version: specific reason>
- **Advisories:** before <runtime C/H/M/L> → after <…>; references: <GHSA ids>; remaining: <with exposure note>
- **Checks:** <command: result> for each verify command, including e2e and `release.py build` / docker smoke (image ID, platform)
- **Not verified:** <anything skipped and why>
- **Troubleshooting that worked:** <or none>
- **Status:** prepared (local commits, not pushed) | pushed | released via vps-container-release (<state dir>)
```

Keep it factual and short. Logs belong in the branch or the scratchpad, not the vault.
