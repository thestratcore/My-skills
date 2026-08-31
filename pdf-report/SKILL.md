---
name: pdf-report
description: "Generate branded PDF reports for Stratcore (dark theme). Use when creating executive summaries, campaign/channel reports, client deliverables, or monthly/quarterly reviews."
---

# pdf-report

Generates a branded PDF via the local **StratcoreReport** generator at
`~/Documents/CodeProjects/StratcoreReport-html/`. Output is the dark, screen-first
Stratcore theme (brand source: the "Stratcore Design System" folder in the Obsidian vault).

> The original version of this skill drove a `digital-marketing-pro` plugin
> (`pdf-generator.py`, `~/.claude-marketing/`) that is not installed. That machinery is
> gone; this skill now assembles a JSON payload and runs the local Node generator.

## Process

1. **Confirm scope with the user** (ask only for what's missing):
   - Report type: `executive-summary`, `campaign-report`, `channel-report`,
     `competitor-report`, `monthly-review`, `quarterly-review`.
   - What data / metrics / period to cover, and the audience
     (`c-suite`, `team`, `client`).
   - Whether it's `confidential`.
2. **Gather the data.** Pull from whatever source applies (Postgres via the vault's
   `PostgreSQL-login.md` conventions, n8n, analytics, files the user provides).
   Do not fabricate figures — flag gaps instead.
3. **Build the payload.** Write a `*.json` file matching the schema in
   `~/Documents/CodeProjects/StratcoreReport-html/README.md` (top-level meta +
   `sections[]`: `h2`/`h3`/`p`/`list`/`kpis`/`table`/`note`/`image`/`html`/`pagebreak`).
   - Audience shaping: **c-suite** → 3–5 `kpis` + short narrative + a `note`-flagged
     recommendation list; **team** → full `table`s, test results, numbered actions;
     **client** → objectives recap, goal-vs-actual tables, next-period plan.
   - Tables: use `{ "v": "...", "tone": "pos|neg|warn", "num": true }` for conditional
     colour and right-aligned figures.
   - Charts: render inline SVG into an `html` section (respect brand tokens —
     `#008568` accent, `#f5f6f5`/`#9a9fa0` text on `#0a0a0b`), or embed a PNG via `image`.
   - Save the payload next to related work or in the generator's `examples/`.
4. **Render:**
   ```
   cd ~/Documents/CodeProjects/StratcoreReport-html
   node src/render.mjs <payload.json> [out.pdf]
   ```
   Needs network on first run (Google Fonts). If Chrome isn't at the default macOS
   path, set `CHROME_PATH`.
5. **Review before delivering.** Convert pages to PNG and inspect
   (`pdftoppm -png -r 90 out/<name>.pdf /tmp/p`), or re-run with `--html` and open the
   file. Check for overflowing tables, wrapped KPI values, and empty trailing pages.
   Offer the user adjustments (sections, emphasis, metrics) and re-render.
6. **Report** the payload path and the final PDF path.

## Notes

- The generator is a git repo; committing/pushing report *outputs* is usually unwanted
  (`out/` and `.build/` are gitignored). Commit payloads only if the user wants them kept.
- To change the look, edit `src/report.css` in the generator, not this skill.
