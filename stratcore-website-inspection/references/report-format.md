# Report format

Deliver the review in-thread in this shape. Keep it scannable — the user acts from this
list.

---

## Full review

### Summary

| | |
|---|---|
| URL(s) | ... |
| Stack (if detectable) | ... |
| Viewports tested | 375 / 768 / 1280 / 1920 |
| Brand module | on / off |
| Findings | P1: _n_ · P2: _n_ · P3: _n_ |

### P1 — fix before anything else

**1. <short title>**
- **Where:** <page> → <section / element / selector>
- **Issue:** <what is wrong, concretely>
- **Rule / evidence:** <the checklist dimension, brand rule, or the evidence it contradicts>
- **Fix:** <the specific change>

(repeat)

### P2 — degrades UX or conversion

(same structure)

### P3 — polish and consistency

(same structure; these can be terser — one line each is fine)

### Needs a decision from you

- <items that are not clear-cut: client naming, whether to name a tool, scope calls>

### Recommendations

- <higher-level suggestions that are not single fixes: a missing section, a restructure>

---

## Re-review (after a patch)

### Prior findings — status

| # | Finding | Status |
|---|---|---|
| 1 | <short title> | fixed / partial / unaddressed / regressed |
| 2 | ... | ... |

- **partial** — say what is still off.
- **regressed** — say what broke.

### New issues introduced by the patch

(P1 / P2 / P3, same structure as the full review)

### Still open

- <unaddressed prior findings worth restating, plus anything still needing a decision>
