# CV conventions and the `cv:` frontmatter contract

## Why conventions live in the file

Different people need different things from a CV file. One wants it parsed cleanly by applicant
tracking systems and language models, so they forbid typographic dashes and fix a date format.
Another wants a visually rich document and does not care. A third has topics they will not disclose.

Hard-coding any of that into the skill would make it work for one person and fight everyone else.
So each CV declares its own rules in its frontmatter, and `scripts/cv_lint.py` enforces whatever it
finds there. The skill stays generic; the document carries its own contract.

## The contract

```yaml
---
title: "Jane Doe - CV 2026"
cv:
  role: master                      # master | variant
  derived_from: ./CV-Full.md        # variants only; path relative to this file
  target: "AI Engineer, ML Engineer, LLM Engineer"
  conventions:
    ascii_only: true                # forbid en/em dashes, arrows, smart quotes, (R), (TM)
    date_format: "MM/YYYY"          # MM/YYYY | YYYY-MM | Month YYYY
    heading_separator: "|"          # separator between job title and employer in role headings
    required_sections:
      - Professional Summary
      - Core Skills
      - Experience
      - Education
    max_bullets_per_role: 12
    max_sentence_words: 45
  never_disclose:
    - "client count"
    - "headcount savings"
---
```

Every field is optional. A CV with no `cv:` block still works - you simply ask the user about
formatting instead of reading it, and the linter reports which checks it skipped.

### Field notes

- **`role`** - exactly one file in a set should be `master`. It is the only file where facts are
  edited. If two files claim `master`, stop and ask; guessing corrupts the whole set.
- **`derived_from`** - what makes drift detection possible. Without it the linter cannot tell a
  variant from a standalone CV, and a variant that quietly acquires a claim its master lacks will
  go out undetected.
- **`target`** - the roles this file is aimed at. Drives the audience-balance check in the review
  pass and the drop decisions in `variants.md`.
- **`never_disclose`** - substrings or regexes the linter flags if they appear. Use for figures and
  topics the user has decided stay private. This is a safety net, not a substitute for asking.

## Machine-ingestion formatting

When `ascii_only` is set, the user has decided the document must survive parsers that mangle
typography. The rules below are what that means in practice. They are worth following even for the
sections you are not editing, since a single stray character defeats the point.

| Rule | Why |
|---|---|
| ASCII hyphen `-` only; no en dash, em dash, arrows, `(R)`, `(TM)` | Non-ASCII punctuation is the most common cause of garbled parser output |
| Straight quotes `'` `"` only | Smart quotes break naive tokenizers and some ATS importers |
| `MM/YYYY - MM/YYYY` or `MM/YYYY - Present` | Unambiguous across locales; `03/04/2024` is not |
| `### Job Title \| Employer` for role headings | A fixed separator lets a parser split title from employer reliably |
| No tables, no multi-column layout, in the CV body | Reading order in tables is unreliable once converted to PDF or plain text |
| Spell out acronyms once with the short form in parentheses | Matches both the spelled-out and abbreviated forms of a search |
| An explicit total-experience line when roles overlap | Concurrent roles otherwise get summed, inflating or confusing the total |
| Mark concurrent roles explicitly in the role heading | Prevents a reader assuming a gap or a job-hop |

## Importing a non-Markdown CV

Most people arrive with a PDF or a DOCX. Convert it, adopt the result as the master, and record
where it came from:

```yaml
cv:
  role: master
  imported_from: "./Jane-Doe-CV.pdf"
```

### Converter ladder

Probe for each tool before using it - the skill runs on machines other than the one it was written
on, and a missing binary should degrade to the next rung rather than fail the task.

| Order | Command | Handles | Notes |
|---|---|---|---|
| 1 | `markitdown <file>` | PDF, DOCX, PPTX, HTML | Best structure retention; keeps headings and lists |
| 2 | `pdftotext -layout <file> -` | PDF | `-layout` preserves column geometry, which matters for CVs |
| 3 | `textutil -convert txt -stdout <file>` | DOC, DOCX, RTF | macOS only |
| 4 | ask the user to paste the text | anything | When nothing is installed - say why rather than failing silently |

After converting, restructure the plain output into the section headings and role headings the rest
of this contract expects, and add a `cv:` block. Conversion gives you text, not structure - expect
to do real work here. Converting a DOCX with `markitdown`, for example, typically yields headings
flattened to `**bold paragraphs**` and list items rendered as `• ` literals rather than Markdown
bullets, with the `### Title | Employer` split gone entirely. None of that is wrong output; it is
just not yet a CV under this contract.

### Check the conversion before building on it

Adopt the conversion directly - do not hold the task up for approval. But CV documents are unusually
prone to converting badly: two-column layouts interleave lines from both columns, tables lose their
reading order, and headers and footers land mid-document. Everything downstream treats the master as
truth, so a scrambled import quietly corrupts every later claim.

So after adopting, look for the signs and report what you find:

- Sections you would expect are missing, or appear in an impossible order
- Dates that no longer parse, or role headings that lost their title/employer split
- Sentences that break off mid-clause and resume in an unrelated one - the signature of column
  interleaving
- Bullets merged into paragraphs, or contact details scattered through the body

Run `scripts/cv_lint.py` as part of this - missing required sections and unparseable dates are
exactly what it checks.

If the conversion looks damaged, say so plainly in your report and name what looks wrong, then
carry on with the work the user asked for. What you must not do is repair the damage by inventing
the missing content: a role whose bullets were lost in conversion gets flagged, not rewritten from
imagination.

## Honesty conventions

These are not formatting, but they belong in the same contract because they are equally mechanical
once decided:

- **Incomplete study is labelled as such** in the heading itself, not softened elsewhere. "Bachelor's
  studies (not completed)" is honest and costs less than being caught.
- **Status labels ride with project claims.** `(prototype, in validation)` after a project name is
  worth more than a confident sentence you cannot defend in an interview.
- **A qualitative scope statement beats a fabricated number.** If the user will not disclose a
  figure, write the scope in words rather than leaving a placeholder that later gets filled with a
  guess.
- **Regenerate exports after any edit.** A stale PDF or RTF next to an updated Markdown master is
  how an old claim reaches an employer after it was corrected.

### Career breaks and gaps

People often want a gap hidden, and hiding it is the one approach that reliably backfires: an
unexplained hole invites the reader to imagine something worse than the truth, and a stretched date
range to paper over it is a falsifiable claim on a checkable document.

What works is a short, unapologetic entry in the same format as any other role - a line naming the
period and the reason in the user's own words, with no justification attached. "Career break -
caring responsibilities" is complete. Breaks for health, caring, parenting, study, travel, or
redundancy are ordinary and need no defence; adding one signals composure, while an obvious dodge
does the opposite.

Two things to get right. Use the user's framing, not a euphemism you picked - ask if you do not
have their words. And if they did anything during the period they would want counted (study, open
source, contracting, volunteering), it goes in as substance rather than as an excuse.

If the user would rather leave it out entirely, that is their call. Say plainly that the gap will
still be visible from the dates, then do as they ask.
