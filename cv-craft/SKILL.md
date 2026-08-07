---
name: cv-craft
description: >
  Build, edit, tailor, and maintain CVs and resumes in Markdown - including writing one from
  scratch when the user has none, importing an existing PDF or DOCX, and keeping several targeted
  variants in sync with a single master. Use this skill whenever the user mentions their CV,
  resume, or zivotopis: writing a first one, converting an old one, adding a project or a list of
  work to it, tailoring it to a job advert or a kind of role, producing a version aimed at a
  different audience, presenting awkward history such as a career break, gap, or unfinished
  degree, checking it for unsupported or fabricated claims, or reviewing it before they send it
  out. Trigger it even when the words "CV" or "resume" never appear, as in "I need something to
  send to recruiters", "add this project to my career doc", "make a version of this for a Head of
  AI role", "how do I explain the year I took off", or "tidy this up before I send it".
---

# CV Craft

A CV is a set of claims about a real person that an employer may check. That single fact drives
everything below: the method here exists to keep the document honest, keep several tailored
versions from drifting apart, and make changes reviewable instead of silently applied.

## Core rule

The master CV is the source of truth. Every claim in it traces to evidence the user supplied or
confirmed - never invent metrics, dates, job titles, team sizes, or outcomes, and never upgrade a
tentative claim into a confident one because it reads better. Derived variants may drop and
reorder content but may never assert something their master does not, because a variant is what
actually gets sent and nobody re-checks it against the master. Any change that alters what the CV
asserts goes through a decision table the user approves row by row - the user decides what goes on
their own CV, not you - while changes that alter no claim are simply made and reported.

## Standard workflow

### 1. Orient - find or create the master

**No CV exists yet?** Follow `references/from-scratch.md`, which interviews the user section by
section and writes the master. Come back here when it exists, then continue at step 5.

**Given a PDF, DOCX, or RTF?** Convert it to Markdown and adopt the result as the master, recording
where it came from in `cv.imported_from`. `references/conventions.md` has the converter ladder -
probe for each tool rather than assuming it is installed. Converted CVs deserve one extra look:
two-column layouts and tables scramble their reading order on conversion, so after adopting, check
that sections, dates, and role headings survived and say so in your report if they did not. Report
it rather than stopping - the user asked for the work, not for a conversion review.

**Otherwise:** find the master - the CV whose frontmatter says `cv.role: master`, or ask if it is
ambiguous. Read its `cv.conventions` block - this is where each CV declares its own formatting
rules, so the same skill works on any CV without hard-coded assumptions. Run the linter for a
baseline:

```bash
scripts/cv_lint.py <path-to-cv-or-directory>
```

If the CV carries no `cv:` block, do not invent conventions from what the file happens to look
like. Offer to write one - see `references/conventions.md` for the contract. Working without it is
fine; you just lose mechanical verification and have to ask about formatting instead.

Never make a factual change in a variant. Facts change in the master, then propagate outward.

### 2. Evidence intake

When the user brings new material - a project inventory, a wiki export, a handoff document, notes
from a review - inventory it against the CV before writing anything. For each item, record a status
drawn from this closed list, because the difference between "we built this" and "we wrote a proposal
for this" is exactly the difference between a true CV and a false one:

`implemented` · `in production` · `in validation` · `prototype` · `documented handoff` · `proposed`

Two rules follow from that list. An item marked `proposed` does not become `implemented` because it
would strengthen the CV - only the user can promote it, and they have to say so explicitly. An item
whose ownership or authorship is unclear gets quarantined and raised with the user rather than
written, since claiming someone else's work is the worst failure mode this skill has.

### 3. Decision table

The gate is about *what a change does to the claims*, not how many changes there are. Counting
edits is the wrong test: fixing eight typos is harmless and proposing one new bullet is not.

**Apply directly, then report** - changes that leave every claim exactly as it was:

- Formatting and convention fixes: non-ASCII punctuation, date format, heading separators
- Tense and grammar corrections
- Collapsing a claim that appears twice into one place, keeping the wording
- Reordering, regrouping, or relabelling existing content

**Propose in a table and stop** - changes that alter what the CV asserts:

- Adding anything new, from a bullet to a keyword
- Removing or softening an existing claim
- Rewording that changes scope, strength, or meaning
- Anything touching a figure, date, title, or employer
- Anything whose disclosure is uncertain - internal names, client identities

When the two are mixed, do both: apply the safe fixes, table the rest, and say clearly which is
which. A user who asks you to tidy their CV and gets back a table and an untouched file has been
told "no" in a way they did not ask for.

Write the table into a gap-analysis note beside the CV using `assets/gap-analysis-template.md`.
Its value is that it separates two things people conflate: *what could go on the CV* and *what the
user wants on their CV*. You are qualified to judge the first and not the second.

| # | Target section | Change type | Proposed text | Rationale | Risk | Decision |

Practical points that make the difference between a table the user can act on and one they cannot:

- **Proposed text is the exact string to insert**, not a description of it. The user is approving
  wording, so they need to see the wording.
- **Fill the Risk column honestly.** Disclosure concerns (internal system names, client identities),
  overclaim risk, length cost. A blank risk column trains the user to skim.
- **Include explicit no-go rows** for material you considered and rejected, with the reason. This
  stops the same rejected item being re-proposed in six months, and shows the user the search was
  thorough.
- Leave Decision blank. The user fills it.

The gate exists to stop claims appearing on someone's CV without their say-so - not to slow down
small work, and not as a way of avoiding the judgement calls that are genuinely yours to make.

### 4. Apply

Apply approved rows only. If a row was approved with a note ("yes but shorter"), honour the note.
If you think an approved row is a mistake, apply it and say why you disagree - it is their CV.

Then write an outcome callout back into the gap-analysis note: what landed, what the review pass
changed afterwards, what stayed open. That note becomes the audit trail, and it is the reason a
session six months from now does not start from zero.

### 5. Review pass

Run before declaring the work done. Fresh-eyes reading of what you just wrote catches things that
were invisible while writing. Full heuristics with worked examples in
`references/review-checklist.md`; the short version:

- **Duplicate claims** - the same project described in two sections is the most common defect when
  content is added incrementally, and it reads as padding.
- **Tense consistency** - a role dated `Present` carrying past-tense bullets reads as though the
  work stopped.
- **Audience balance** - count leadership versus hands-on bullets and compare against `cv.target`.
- **Internal jargon** - names and process vocabulary that mean nothing outside the user's employer.
- **Sentence health** - a word repeated inside one sentence, sentences past the configured cap.
- **Untraceable metrics** - any number you cannot point at evidence for.

Then run the linter again and fix regressions.

### 6. Variant derivation

Variants exist because one document cannot address a hiring manager and an engineering lead at
once. Derivation is subtraction and reordering, never addition.

- Lead with the role the target audience cares about; ordering signals what the person is.
- Reorder and rename skills blocks for the audience - the same underlying skills, grouped and
  labelled the way that reader thinks about them.
- Drop by audience. Budget figures, headcount and procurement leave an engineering CV; tool
  inventories and model names leave a leadership CV.
- Contact block, education, and certifications stay identical to master. They are facts, not
  positioning, and divergence there looks like carelessness or worse.
- Cross-link each variant to its master and siblings, and set `cv.derived_from`, so the linter can
  check for drift.

See `references/variants.md` for per-archetype guidance on what each audience wants.

### 7. Report

Close with what changed, what you skipped and why, and what risks remain open - disclosure
questions, claims resting on thin evidence, stale exports. Say plainly if something is unverified.

## References

Read these when the task calls for them rather than upfront:

| Task | File |
|---|---|
| No CV exists yet - interviewing the user and writing the first master | `references/from-scratch.md` |
| Importing a PDF, DOCX, or RTF; establishing or reading a CV's `cv:` frontmatter block; machine-ingestion formatting rules | `references/conventions.md` |
| Deriving or updating a targeted variant; deciding what a given audience wants | `references/variants.md` |
| Running the review pass; diagnosing a specific defect | `references/review-checklist.md` |
| Starting a decision table | `assets/gap-analysis-template.md` |
