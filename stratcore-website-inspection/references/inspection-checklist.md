# Inspection checklist

The dimension catalogue for a website review. Each dimension has: what it is, the
concrete checks, how to detect it from the capture, and severity guidance.

Dimensions marked **(brand)** run only when the Stratcore brand module is active —
see `brand-and-positioning.md`. All others run on every review.

Origin of these checks: distilled from prior Stratcore web-review work
(`Company/Stratcore/stratcore-web-improvement.md` §0–§7,
`Company/Stratcore/stratcore-brand-guidelines.md`) plus the responsive / layout set
from Microsoft's `web-design-reviewer` skill.

---

## A. Claim substantiation

Every factual and performance claim on the page must trace to a real, dated source.

- Each metric or number is backed by a graded evaluation, a measurement, or a dated log
  — **measured, not asserted**. An estimate presented as a result is a finding.
- A capability or benefit stated with **zero proof** (no number, no case study, no
  diagram, no link to where it is demonstrated) is a gap, not necessarily wrong — flag it
  as under-evidenced.
- No hype, no unsupported guarantees, no "guaranteed" business outcomes.
- Superlatives ("best", "leading", "fastest") need a citation or they come out.

Detect: read every sentence with a number or a comparative in it; cross-check against the
evidence base gathered in Step 1. List each claim → its evidence (or "none found").

Severity: unsupported public metric = **P1**. Under-evidenced capability bullet = P2/P3.

---

## B. Content and technical accuracy

The page must describe the real thing.

- Technology logos / names shown match what the referenced work actually uses in the
  delivered path. A tool used only in experiments or evaluation, but shown as part of the
  production stack, is misleading — flag it (note: some tools legitimately belong if the
  page frames them as "evaluation / pre-PoC"; check the framing, not just the presence).
- Architecture descriptions match the real system: component split, model names and
  dimensions, corpus size, hosting model.
- Page claims do not contradict internal records. If a vault note says a project is
  `status: archive` while the page runs it as a live case study, that contradiction must
  be resolved before publish (fix the record or fix the page).

Detect: compare the page's stack section, architecture prose, and any diagram against the
project's handoff docs and the evidence base.

Severity: factual error in a case study = **P1**. Stack-strip imprecision = P2.

---

## C. Honesty about project status

Delivered work and planned work must be visibly separated.

- Nothing scoped, in design, or in draft is presented as delivered.
- If the page lists a portfolio or use-case set, every item carries a maturity tag
  (live / pilot / in design / concept) — no bare list that implies all are shipped.
- "We built X for a hospital" when X is one deployment must not be phrased to imply many
  clients ("our hospital deployments").

Detect: for each thing the page claims to have done, ask "is there a delivered artefact?"
Check verb tense and plurals.

Severity: draft promoted as delivered = **P1**.

---

## D. Fabrication guard

- No invented services, clients, partnerships, awards, certifications, metrics, or
  case-study results. If it is not in the evidence base, it does not go on the page.
- Client names require written sign-off. Absent that, the case study is anonymised
  ("a regional hospital", "a Czech manufacturer").
- **De-anonymisation check:** even without a name, a combination of sector + technology +
  region + size can identify a client. Read the anonymised description as an outsider
  trying to guess who it is.

Detect: list every named or describable entity on the page; confirm each against
known-true facts and sign-off status.

Severity: fabricated entity or uncleared client name = **P1**.

---

## E. Confidentiality

- No credentials, API keys, tokens, passwords anywhere on or linked from the site.
- No internal hostnames, internal IP addresses, or internal project numbers — in copy,
  in image alt text, or baked into a diagram.
- Internal system names in any published diagram are renamed to role labels
  ("Control plane", "GPU compute host"), not the real host names.
- Pilot metrics from an engagement governed by a separate contract need explicit
  clearance before they appear publicly.

Detect: scan copy, `browser_snapshot` output, image contents, and any embedded SVG /
diagram text. Check `view-source` style artefacts in the DOM snapshot.

Severity: any secret or internal host exposed = **P1**, report location only, never the
value.

---

## F. Compliance framing

For a case study in a regulated domain (healthcare, finance, legal, public sector):

- State the **EU AI Act** risk tier the system sits in, and that it is compliant / how.
- State the **GDPR** basis and data residency (e.g. "processed on-premise, no data leaves
  the client network").
- For healthcare: state whether the system is **in or out of medical-device (MDR) scope**,
  and why (e.g. "advisory only, physician-in-the-loop, makes no diagnosis or treatment
  recommendation" → outside MDR).
- State the **human-in-the-loop** boundary.

A governance-led or regulated case study with none of this framing is a finding.

Detect: if the page has a regulated case study, look for a compliance sentence or table
row. Missing = P2 (P1 if the page actively markets to that regulated sector).

---

## G. Brand voice and tone (brand)

From `stratcore-brand-guidelines.md` "Voice and copy" (and the still-binding rules
carried over from the 2024 guideline):

- **Sentence case** for headings and buttons ("Reference build", not "Reference Build",
  not "OUR Frameworks").
- **No exclamation points.**
- **No emoji, anywhere.** No unicode-character icons.
- No "we're excited", no hype, no promotional superlatives. Confident, not promotional.
- State what the product does, not how the reader should feel.
- Third person about the product; second person ("your systems", "your team") in CTAs and
  body copy.
- Prefer concrete, domain-specific vocabulary over generic SaaS words ("workspace",
  "workflow", "solution", "empower", "seamless").
- **Do not import the design-system sample lexicon** (map / govern / drift / dependency /
  coverage) as if it were Stratcore's positioning — it is illustrative uBrand copy. See
  `brand-and-positioning.md`.
- Short sentences. Roughly two sentences per paragraph in hero / marketing copy.
- Connect technology to a business outcome; explain complex ideas in accessible terms;
  no unexplained jargon.

Detect: read the copy aloud against this list. Grep the DOM text for `!`, for emoji, for
title-case headings.

Severity: mostly P3, but hype or a false-feeling promotional claim can be P2.

---

## H. Heading casing and punctuation consistency

- One heading style across the whole page.
- Sentence case, no trailing `.` or `?`, no ALL-CAPS words inside a heading.
- No duplicated or empty headings (a stray "MEMBER of." mid-narrative is a build bug).
- Heading levels nest correctly (no `h2` → `h4` jump).

Detect: extract every heading from `browser_snapshot`; list them in document order and
scan the list.

Severity: P3, unless a heading is empty / duplicated / clearly a build artefact → P2.

---

## I. Structure and information architecture

A services or product page should contain, roughly in this order:

1. Hero — what this is, one line.
2. **A plain statement of engageable services** — "What we do", 4–6 offerings, one line
   each. A page that goes hero → method → one proof → logo strip with no services list
   has the biggest conversion gap there is. This is almost always a finding when absent.
3. How we work — the delivery method / principles.
4. At least one **case study with a metrics table**.
5. A **sanitised architecture diagram**.
6. A lighter breadth section (see J) if there is only one deep case study.
7. Technology strip (see K).
8. A concrete CTA (see P).

Card layouts: equal-height rows, 4-up on desktop → 2×2 on tablet → stacked on mobile.

Detect: map the page's actual section order against the above; note what is missing or
out of order.

Severity: missing services list = **P2** (P1 if the page's job is lead-gen). Missing
case study or diagram = P2.

---

## J. Redundancy vs breadth

- One proof point reads as thin. Add a breadth grid (anonymised use cases) so the page
  shows range **without over-claiming**.
- A breadth section must be visually **lighter** than the deep case study and must carry
  **no metrics** — numbers belong only to the one deep reference build.
- A breadth section must not duplicate the deep case study's own component description. If
  "Also in production" just restates what the reference build already broke down, retitle
  and reframe it (e.g. "Delivered components" with an intro line) rather than repeating.
- Capability bullets should **link to where each is demonstrated**, not restate the claim
  in three places.

Detect: look for the same capability described in two or three sections; look for metrics
appearing outside the case study.

Severity: P2 (redundancy that inflates perceived scope) / P3 (mild repetition).

---

## K. Logo / technology strip

- Group logos into labelled role rows (e.g. "Architecture & governance", "Orchestration &
  data", "Local inference", "Cloud LLMs") — or leave the strip flat only if the layout
  genuinely cannot support grouping.
- When swapping a logo, keep the count stable so a symmetrical grid stays symmetrical.
- Add a one-line "why this stack" / "why local" rationale near the strip.
- Every logo is a tool actually used (ties back to B).

Detect: count the logos, check for labels, check for a rationale line.

Severity: P3.

---

## L. Visual system (brand)

Check the rendered page against `stratcore-brand-guidelines.md` "Colour", "Typography",
"Spacing, radius, elevation, motion", "Imagery". Full token values live in
`brand-and-positioning.md`. Key checks:

- **Dark only.** Page background near-black `#0a0a0b` — never pure `#000`, never a light
  theme.
- Accent **Observatory green `#008568`**, used sparingly — one accent. If everything is
  green, that is a finding.
- Surfaces step by lightness (`#0f1011` → `#161719` → `#1e2022`), each with a 1px hairline
  border `rgba(255,255,255,0.08)` — the shadow supplements the hairline, never replaces it.
- Type: **Syne** 600/700/800 for display and headings, **Montserrat** 400–700 for body /
  UI. **OCR-A Extended** is an accent voice only — eyebrow labels, status strings, KPI
  deltas, code-like tags. Never body copy, never headlines.
- Radii: 8px controls, 12px cards, 16/24px larger, pill on badges.
- Motion: 120 / 200 / 320ms, `cubic-bezier(.4,0,.2,1)`, no bounce or springy overshoot.
- Spacing: base-8 (4, 8, 12, 16, 24, 32, 48, 64, 96). Content max-width 1200px, 24px
  gutter.
- Imagery: dark, cool, technical (isometric grids, particle meshes, teal / blue-black
  gradients). Full-bleed only behind hero / section openers, **always with a dark gradient
  scrim** so foreground type stays legible. No illustration, no repeating texture, no
  hand-drawn elements, never warm or saturated, don't add grain.
- Icons: **Lucide**, 1.5px stroke. No emoji, no unicode-character icons, no second icon
  set.

Detect: eyedrop key colours from the screenshots; identify fonts from the snapshot's
computed styles or visually; check imagery against the approved set.

Severity: light theme / pure black / wrong accent = P2. Font-role violation (OCR-A in
body) = P2. Imagery without scrim = P2 (also an accessibility finding, see O).

---

## M. Logo usage (brand)

- White lockup on dark surfaces (the default). Black lockup on `#f5f6f5`, not pure white.
- Mark on solid `#008568` — white mark only.
- Mark ↔ wordmark proportion and clear space preserved.
- Not recoloured, distorted, rotated, rearranged, outlined, or given effects.
- Wordmark set in OCR-A Extended.

Detect: find every logo instance in the screenshots; check placement, colour, proportion.

Severity: distorted / recoloured logo = P2.

---

## N. Component conformance (brand)

The page should use only the authored design-system primitives: Button, IconButton, Icon,
Card, StatCard, Table, Badge, Tag, Toast, Tooltip, Checkbox, Input, Radio, Select, Switch,
Tabs, Dialog. Each has a `.prompt.md` spec in the `stratcore-design` skill under
`components/`.

Detect: identify UI elements that look like off-system one-offs (a bespoke button style, a
card that ignores the radius / border tokens).

Severity: P3 unless it visibly breaks the brand (P2).

---

## O. Accessibility

- Foreground text over full-bleed imagery stays legible — scrim present and strong enough.
- Visible focus states on every interactive element (Stratcore: green glow ring).
- Contrast meets WCAG AA. On the dark palette, the defined text tokens pass; `#04120e` is
  the only approved text colour on a green fill. Spot-check any custom-coloured text.
- **Alt text on every meaningful image.** A decorative image gets `alt=""`. An informative
  image (a diagram, a screenshot) gets a real description — **not** the lightbox label
  ("View fullsize" is a bug, not alt text).
- Heading levels form a correct outline (ties to H).
- Touch targets on mobile are at least ~44px.
- Page is keyboard-navigable; tab order is sane; no keyboard trap.
- Language attribute set; form inputs labelled.

Detect: `browser_snapshot` gives the accessibility tree — read it for missing names,
missing alt, heading order. Tab through the page if the MCP allows. Contrast-check from
the screenshots.

Severity: missing alt on a diagram, no focus states, failing contrast = P2 (P1 if the
page is legally required to be accessible).

---

## P. CTA quality

- The primary call to action is concrete and action-oriented, in second person, and
  routes to a real destination (`/contact` or equivalent).
- "Ready to discuss your next initiative?" is weaker than "Schedule a consultation" —
  prefer a verb the visitor can act on.
- One primary CTA per view; secondary actions visually subordinate.

Detect: find every CTA; check wording, destination, prominence.

Severity: P2.

---

## Q. Responsive and layout

Test at **375** (mobile), **768** (tablet), **1280** (desktop), **1920** (wide).

- **Overflow** — content spilling past its parent or the viewport; horizontal scrollbar on
  the body. Run the overflow snippet in `playwright-recipes.md`.
- **Overlap** — elements colliding unintentionally.
- **Alignment** — grid / flex items not lining up.
- **Spacing consistency** — uneven padding / margins between sibling elements.
- **Text clipping** — long strings truncated without ellipsis, or breaking layout.
- **Breakpoint transitions** — no broken intermediate state as the viewport changes;
  images scale (`max-width: 100%`); cards reflow cleanly.
- **Touch targets** — buttons and links large enough on mobile (ties to O).

Detect: compare the four screenshots; run the overflow detector at each width.

Severity: body horizontal scroll or overlap on a common viewport = **P1**. Spacing drift
= P3.
