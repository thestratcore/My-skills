# cv-craft

A Claude Code skill for building, editing, tailoring, and maintaining CVs written in Markdown.

It is fully generic — it contains no personal data and makes no assumptions about your formatting.
Each CV declares its own rules in its own frontmatter, and the skill reads them.

## What it does

- **Writes a CV from scratch** through a structured interview, when you have none
- **Imports a PDF, DOCX, or RTF** and converts it into a Markdown master
- **Folds in new evidence** — a project list, a wiki export, a handoff doc — classified by status
  and proposed in an approval table rather than silently written
- **Derives targeted variants** from one master (leadership vs engineering, for example) and keeps
  them from drifting apart
- **Reviews before you send**, catching duplicate claims, tense breaks, internal jargon, and
  unsupported metrics
- **Verifies mechanically** with a linter, including a drift check that catches a variant claiming
  something its master does not

## The one idea worth knowing

A CV is a set of claims about a real person that an employer may check. Everything here follows
from that: nothing is invented, evidence is classified by how solid it actually is
(`implemented` / `in production` / `in validation` / `prototype` / `documented handoff` /
`proposed`), and any change that alters what the CV asserts is proposed for your approval rather
than applied. Changes that alter no claim — formatting, tense, deduplication — are just made.

## Install

Copy the `cv-craft/` directory into `~/.claude/skills/` (personal) or `.claude/skills/` (per
project). No dependencies beyond Python 3; `PyYAML` is used if present and a built-in fallback
parser is used if not.

Optional, for importing non-Markdown CVs — the skill probes for these in order and degrades
gracefully if none are installed:

| Tool | Handles |
|---|---|
| `markitdown` | PDF, DOCX, PPTX, HTML (best structure retention) |
| `pdftotext` | PDF fallback |
| `textutil` | DOC/DOCX/RTF fallback, macOS only |

## Using the linter directly

```bash
python3 scripts/cv_lint.py path/to/cv.md
python3 scripts/cv_lint.py path/to/cv-directory/ --json report.json
```

Exit code is 1 when errors are found, 0 otherwise, so it drops into a pre-commit hook or CI step.
Checks that have nothing to run against are reported as skipped rather than silently passing.

To confirm the linter works correctly after installing it, run its built-in regression set — it
builds throwaway fixtures containing known defects and asserts each check fires:

```bash
python3 scripts/cv_lint.py --selftest
```

## The `cv:` frontmatter block

Optional — the skill works without it and will offer to write one. With it, the linter can verify
your conventions mechanically instead of asking.

```yaml
cv:
  role: master                    # master | variant
  derived_from: ./CV-Full.md      # variants only
  imported_from: ./old-cv.docx    # set when converted from another format
  target: "AI Engineer, ML Engineer"
  conventions:
    ascii_only: true              # forbid en/em dashes, smart quotes, arrows
    date_format: "MM/YYYY"
    heading_separator: "|"
    required_sections: [Professional Summary, Core Skills, Experience, Education]
    max_bullets_per_role: 12
    max_sentence_words: 45
  never_disclose: ["client count", "headcount savings"]
```

Full contract in `references/conventions.md`.

## Layout

```
cv-craft/
├── SKILL.md                       entry point: core rule and the 7-step workflow
├── references/
│   ├── conventions.md             frontmatter contract, import ladder, honesty conventions
│   ├── from-scratch.md            the cold-start interview
│   ├── variants.md                what each audience wants, and what to drop
│   └── review-checklist.md        the pre-send review pass
├── assets/
│   └── gap-analysis-template.md   the decision-table scaffold
├── scripts/
│   └── cv_lint.py                 mechanical verification
├── agents/openai.yaml             cross-harness adapter
└── evals/
    ├── evals.json                 5 test cases, 36 assertions
    └── fixtures/                  sample CVs and inputs the test cases run against
```

## Measured behaviour

Against a five-case eval suite, each run with and without the skill:

| | With skill | Baseline |
|---|---|---|
| Overall | **100%** | 71% |
| Evidence intake (approval gate) | 8/8 | 6/8 |
| Variant derivation | 8/8 | 8/8 |
| Pre-send review | 5/5 | 5/5 |
| Cold start | 8/8 | 3/8 |
| Document intake | 7/7 | 3/7 |

The gap is concentrated in cold start and document intake. On tasks where the CV already carries a
`cv:` block, a capable model does most of this unaided — the block itself carries much of the
method. The skill earns its keep when there is no scaffolding to copy, and on the approval gate,
where the baseline silently rewrote the CV instead of proposing changes.

Trigger accuracy on a 20-query set (10 should-trigger, 10 deliberate near-misses such as cover
letters, screening other people's CVs, and LinkedIn edits): 20/20.
