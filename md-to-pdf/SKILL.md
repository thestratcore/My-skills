---
name: md-to-pdf
description: "Turn any Markdown file (or Markdown you just wrote) into a branded Stratcore PDF — dark theme, cover page, running footer. Use when the user asks to export, convert, or 'make a PDF' of a note, doc, README, report draft, or any .md file, including vault notes. For data-driven reports built from KPIs and tables rather than an existing document, use pdf-report instead."
updated: 2026-09-19
---

# md-to-pdf

Converts Markdown → Stratcore-branded PDF using the local **StratcoreReport**
generator at `~/Documents/CodeProjects/StratcoreReport-html/`. Same theme, cover,
and footer as [pdf-report]; the difference is the input. `pdf-report` interviews the
user and assembles a JSON payload; this skill takes a document that already exists
and gets out of the way.

Brand source of truth: `Company/Stratcore/Stratcore Design System/` in the Obsidian
vault. Theme is dark-only.

## Run it

```bash
cd ~/Documents/CodeProjects/StratcoreReport-html
node src/render.mjs <document.md> [out.pdf]
```

Output defaults to `out/<document>.pdf` inside the generator. Pass an explicit
second argument to write next to the source document instead — usually what the
user wants for a vault note.

Debug flags: `--payload` prints the intermediate JSON (use this when a block renders
wrong — it shows whether the problem is parsing or styling), `--html` emits the HTML
to `.build/` without launching Chrome.

## Process

1. **Resolve the file.** If the user named a note rather than a path, find it before
   rendering. Don't guess between two similar filenames — ask.
2. **Check the frontmatter.** It drives the cover page (see mapping below). If the
   document has none, or has no `title`, the title falls back to the first H1 and then
   to the filename. Offer to add a `subtitle`/`client`/`period` if the cover looks bare,
   but don't edit the user's note without asking.
3. **Render**, writing the PDF next to the source unless told otherwise.
4. **Look at the result before handing it over:**
   ```bash
   pdftoppm -png -r 70 out.pdf /tmp/p && ls /tmp/p-*.png
   ```
   Read the PNGs. Check for: tables overflowing the page width, code blocks pushed to
   a near-empty page, an empty trailing page, and headings stranded at a page bottom.
5. **Report** the PDF path and the page count. Offer adjustments.

## Frontmatter → cover page

| Frontmatter | Effect |
|---|---|
| `title` | cover headline (falls back to first H1, then filename) |
| `subtitle` or `description` | line under the title |
| `client`, `period`, `audience`, `author` | cover meta rows |
| `date` or `updated` | "Prepared" row (defaults to today) |
| `type` or `report_type` | mono status label, top-right of cover |
| `eyebrow` | small mono label above the title |
| `confidential: true` | amber pill on the cover + `CONFIDENTIAL` in every footer |
| `cover_image` | replaces the default cover art; path relative to the document |

Vault notes already carry `title`, `type`, and `updated`, so they cover themselves.

## Markdown mapping

| Markdown | Renders as |
|---|---|
| `#` / `##` | section heading with hairline rule (a leading H1 matching the title is dropped — the cover already shows it) |
| `###` and deeper | subheading |
| paragraph | body text; `**bold**`, `*italic*`, `` `code` ``, `[links](url)` all work |
| `-` / `*` / `1.` | bullet or numbered list; one level of nesting |
| GFM table | branded table — right-aligned (`---:`) columns become mono figures, and `+3.2%` / `-8.4%` cells pick up green/red automatically |
| `> quote` | callout. `> **WATCH:** …` or `> [!DANGER]` sets the label and colour (info/tip/warning/danger) |
| ` ```lang ` | code block with a mono language tag |
| `![alt](src)` | figure with caption; `src` resolves relative to the document |
| `---` | hairline rule (dropped before a heading, which draws its own) |
| `<!-- pagebreak -->` | forced page break |
| raw `<svg>` / `<div>` | passed through untouched — the escape hatch for inline charts |

Anything unsupported degrades to a paragraph rather than disappearing.

## Notes

- **Needs Chrome.** Drives the installed Google Chrome via `puppeteer-core`; set
  `CHROME_PATH` if it isn't at the default macOS location. First render needs network
  for Syne + Montserrat (Chrome caches them after). Kode Mono is bundled
  (`assets/KodeMono-Variable.ttf`, SIL OFL) and is the mono face for all text.
  OCR-A Extended is deliberately absent — it has no Czech carons or rings, so Czech
  in table headers, KPI deltas and the footer fell back mid-word. It survives only
  inside the logo artwork, and the cover lockup is a PNG.
- **`---` is a rule, not a page break.** Many documents use one before every heading;
  breaking there gives a page per section with four lines on it. Use
  `<!-- pagebreak -->` where a real break is wanted.
- **Wide tables are the main failure mode.** A table past ~6 columns will crowd at A4.
  Either cut columns with the user, or split it into two tables.
- **To change the look, edit `src/report.css` in the generator, not this skill.**
  Both skills share it, so a change here changes report output too. Page margins are
  the exception: they are split between `report.css` and `render.mjs` and must stay in
  step — see "Page margins" in the generator's README before touching them.
- **Dark-only.** A long PDF is a lot of ink if anyone prints it. Say so when the user
  is producing something print-bound; a light variant is not built yet.
- Don't render documents listed under "Files never to edit structurally" in the vault's
  `CLAUDE.md` — they hold live credentials and must not leave the machine as a PDF.
