# Review checklist

Run this after applying changes, before telling the user the work is done. Most of these defects are
invisible while writing and obvious on a second reading - which is precisely why the pass is a
separate step rather than something to hold in mind during editing.

Work through the list in order. The first four catch real damage; the rest are polish.

## 1. Duplicate claims across sections

The most common defect when a CV grows incrementally. A project gets added as an experience bullet,
then later a Selected Projects section is created and the same project is described again. Fifteen
lines apart, both readings look fine; together they read as padding, and a parser counts the claim
twice.

**Check:** for each named project or system, count how many sections mention it substantively.
Passing mentions are fine; two full descriptions are not.

**Fix:** pick which section owns the detail. Usually the dedicated projects section keeps it and the
experience bullet collapses to one line that names the systems and points there.

> **Example.** Four experience bullets each describing a platform, plus four project entries
> describing the same four platforms. Collapsed to one experience bullet naming all four and
> deferring to the projects section - the detail survives, the repetition does not.

## 2. Tense consistency within a role

A role dated `Present` whose bullets are past tense reads as though the work has stopped. This
happens whenever new bullets are drafted in isolation, because describing completed work in past
tense is the natural default.

**Check:** for every role marked `Present`, confirm the bullets are present tense and consistent
with the role's existing bullets. For ended roles, confirm past tense throughout.

**Fix:** convert. "Designed and operated X" becomes "Designs and operates X" in a current role.

## 3. Unsupported and untraceable claims

**Check:** every number - team sizes, budgets, percentages, counts, durations - and every superlative.
Can you point at the evidence the user supplied? Every project claim: does its status label match
what the evidence actually says?

**Fix:** remove, or replace with a qualitative scope statement. Never leave a placeholder like
`X%` or `[NUMBER]` - placeholders get filled in later by someone guessing, which is how a fabricated
metric reaches an employer.

Watch specifically for a `proposed` item that has drifted into sounding `implemented`.

## 4. Variant overclaim

For any file with `cv.derived_from`, every claim must exist in the master. This is the failure mode
with the worst consequences, because the variant is what gets sent and nobody re-reads the master
before sending.

**Check:** run `scripts/cv_lint.py` on the variant - the drift check does this mechanically. Also
confirm the contact block, education, and certifications match master exactly.

## 5. Audience balance

**Check:** count bullets that signal leadership versus bullets that signal hands-on delivery, and
compare the ratio against `cv.target`. A Head of IT CV where hands-on bullets outnumber leadership
bullets undersells the person; an engineering CV dominated by budget and procurement suggests they
have stopped building.

**Fix:** rebalance by moving detail into or out of a projects section, not by inventing.

## 6. Internal jargon

Process vocabulary and system names that mean something only inside the user's employer. The writer
cannot see these - they are simply what things are called.

**Check:** read as an outsider. Would a hiring manager at a different company know what this word
means? Internal codenames, in-house process terms, project numbers.

**Fix:** replace with the externally legible equivalent, or gloss it in three words.

> **Example.** "across eight controlled microphases" - "microphase" is internal vocabulary and reads
> as padding. "through a staged, gated deployment process" says the same thing to a stranger.

Internal system codenames carry a second problem: they may not be disclosable. Flag them for the
user rather than deciding alone.

## 7. Sentence health

**Check:** a word repeated within a single sentence; sentences over `max_sentence_words`; a
duplicated phrase from a copy-paste; a bullet that has grown past three lines.

> **Example.** "deterministic-first AI platforms ... and deterministic workflow automation" - the
> repetition is invisible while writing and obvious on rereading.

Also check for jargon that adds length without adding meaning to an outside reader. Vocabulary that
is precise internally can be dead weight externally.

## 8. Structure and volume

**Check:** bullets per role against `max_bullets_per_role`; total length against the target format;
section ordering still sensible after edits; heading conventions intact.

A role that has grown to sixteen bullets has usually accumulated detail that belongs in a projects
section, or detail that has stopped earning its place.

## 9. Mechanical pass

Run `scripts/cv_lint.py` last and fix regressions. It catches charset violations, date-format
drift, missing sections, never-disclose hits, and variant drift - the things that are tedious to
check by eye and easy to verify by machine.

## Reporting

Tell the user what the pass changed and what it found but did not change - a disclosure question,
a claim resting on thin evidence, a length problem needing their judgement. Findings you sit on are
findings that reach an employer.
