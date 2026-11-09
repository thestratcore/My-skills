# Summarising a survey for the owner

`survey.py` writes the full report: a summary table, then for each project the findings, the suggested groups and the data gaps.
Don't paste the whole report into chat. Give the path, and summarise like this:

```
Survey <date> (<n> projects, report: <absolute path>)

Act now (P1)
- <project>: <finding>. <one line: runtime or build-only, reachable?, fix = which group>

Next maintenance pass (P2)
- <project>: <finding>

Worth planning (P3, majors)
- <package> <from>→<to> in <projects>. <known migration cost from frameworks.md>

Routine (P4): <projects> have patch/minor batches ready.

Data gaps: <projects and what could not be checked>. These are not "up to date".

Suggested next step: <one project + mode>, e.g. "Mode B on stratdesk: safe batch fixes the zod and body-parser advisories."
```

Rules:
- Group the same major across projects (for example "TypeScript 7 behind in 5 apps"). One migration study covers all of them.
- Say whether a runtime advisory reaches users. For static nginx sites it usually affects only the build.
- Name the source of the Node schedule: the live fetch, or the built-in table.
