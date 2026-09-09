---
name: stratcore-website-inspection
description: Inspect a live website for content, claims, structure, brand-voice, visual, and accessibility issues and produce a ranked punch-list. Use when the user asks to review / inspect / audit / evaluate a website, web page, or site, or to re-check a page after a patch, or gives a URL and asks "what's wrong with this page" or "how do I improve this page". Requires a Playwright MCP server for the visual pass. Reports in-thread; only writes findings to a file when asked.
---

# Website inspection

Review a **live, rendered website** and return a ranked punch-list of what to fix.
Covers content accuracy, claim substantiation, honesty about status, confidentiality,
compliance framing, information architecture, brand voice, the visual system,
accessibility, and responsive layout.

This is a general reviewer usable on any URL. The Stratcore-specific brand, positioning,
and evidence checks are an **optional module** (`references/brand-and-positioning.md`)
that switches on for Stratcore-owned or Stratcore-built sites.

## When not to use this skill

- Reviewing source code or a pull request — that is ordinary code review.
- Authoring or extending the Stratcore design system — use `stratcore-design`.
- Extracting a brand kit from a site — use `brand-extract`.
- Performance / Core Web Vitals audits — run Lighthouse; this skill does not measure load.

## Prerequisites

1. **Playwright MCP server, connected.** The visual and responsive passes depend on it.
   If `browser_navigate` / `browser_take_screenshot` / `browser_snapshot` /
   `browser_resize` / `browser_console_messages` / `browser_evaluate` are not available,
   stop and tell the user to run:

   ```
   claude mcp add playwright -s user -- npx -y @playwright/mcp@latest --caps=vision
   ```

   then `/mcp` to connect, then re-invoke. Do not attempt the visual pass without it and
   do not silently fall back to a text-only fetch unless the user explicitly accepts that.
2. **The target URL is reachable** from this machine.

---

## Step 1 — Scope and context

Establish, asking the user only for what you cannot infer:

- **Which URL(s) and pages.** One page, a set, or "the whole site" (in which case pick the
  key templates: home, a service / product page, a case study, contact).
- **Brand module on or off.** ON when the domain is Stratcore-owned (e.g.
  `thestratcore.com`) or the site was built by Stratcore to its design system. When ON,
  read `references/brand-and-positioning.md` now. When OFF, skip dimensions G, L, M, N.
- **The evidence base.** What backs the page's factual and metric claims — vault notes,
  evaluation logs, project handoff docs, a client's own published material. Claim-checking
  needs something concrete to check against; if there is nothing, say so and treat every
  unsupported metric as a finding rather than assuming it is true.
- **Anything to skip** — pages, sections, or known-WIP areas.
- **Re-review?** If this is a re-check after a patch, get the prior findings list (from the
  conversation or a file the user points at) and switch to the mode in Step 6.

---

## Step 2 — Capture

Follow `references/playwright-recipes.md` for the exact call sequence. In short:

1. `browser_navigate` to the URL.
2. Full-page screenshot at **1280** (desktop). Then `browser_resize` and re-shoot at
   **1920**, **768**, **375**.
3. `browser_snapshot` for the DOM / accessibility tree.
4. `browser_console_messages` — record any JS errors or failed requests.
5. `browser_evaluate` the horizontal-overflow snippet from the recipes file.
6. Save every screenshot to a temp directory and **`Read` each one back** — the visual
   analysis is done from the images, not from memory of the snapshot.

If a page has meaningful interactive state (menus, tabs, accordions), capture the
relevant states too.

---

## Step 3 — Inspect

Work `references/inspection-checklist.md` dimension by dimension. Do not skip a dimension
because nothing jumped out — go looking. The dimensions:

| | Dimension | Module |
|---|---|---|
| A | Claim substantiation | all |
| B | Content & technical accuracy | all |
| C | Honesty about status (delivered vs draft / in-design) | all |
| D | Fabrication guard (invented clients, metrics, certs) | all |
| E | Confidentiality (secrets, internal hostnames / IPs, de-anonymisation) | all |
| F | Compliance framing (regulated / healthcare case studies) | all |
| G | Brand voice & tone | brand |
| H | Heading casing & punctuation consistency | all |
| I | Structure / information architecture | all |
| J | Redundancy vs breadth | all |
| K | Logo / technology strip | all |
| L | Visual system (palette, type, imagery, motion, spacing) | brand |
| M | Logo usage | brand |
| N | Component conformance | brand |
| O | Accessibility | all |
| P | CTA quality | all |
| Q | Responsive / layout | all |

For each issue note: the page, the element (selector or plain description), what is wrong,
the rule or evidence it violates, and the fix.

---

## Step 4 — Rank

- **P1** — breaks function or credibility, or risks a confidentiality breach or a false /
  unsupported public claim. Fix before anything else.
- **P2** — degrades UX or conversion: missing services list, weak CTA, one thin proof
  point, poor mobile layout.
- **P3** — polish and consistency: heading casing, spacing drift, minor copy edits.

---

## Step 5 — Report

Report **in-thread** using `references/report-format.md`. **Do not write to the vault or
any file** unless the user asks.

If the user asks to save the findings:

- For the Stratcore AI services page, append a dated `## §0.x` review block to
  `Company/Stratcore/stratcore-web-improvement.md`, matching that file's existing
  structure and callout conventions.
- Otherwise create a dated note where the user specifies.
- After any vault file changes, run `python3 scripts/vault_audit.py .` from the vault root
  and confirm it is clean.

---

## Step 6 — Re-review mode

When re-checking after a patch:

1. Restate the prior findings as a list.
2. Re-capture (Step 2) and re-inspect (Step 3).
3. Mark every prior finding **fixed / partial / unaddressed / regressed**.
4. Call out any **new** issue the patch introduced (duplicated headings, broken layout,
   copy that now contradicts another section).
5. Use the re-review table in `references/report-format.md`.

---

## Publish gate

If the user is about to publish (or asks "is this safe to publish"), run
`references/publish-gate.md` as a standalone pass and report pass / fail per item. A
single failing item on client naming, secrets, unsupported metrics, or
delivered-vs-draft status blocks publication.

---

## Constraints

- **Read-only.** Never edit website source. The only exception: the user explicitly asks
  for fixes *and* the site's source is in the workspace — then follow the project's
  existing styling method, change the minimum, and re-verify each fix.
- **Never reproduce a secret, credential, internal IP, or internal hostname** in the
  report — name that one was found and where, nothing more.
- **Flag client-identifying content; do not quietly rewrite it.** Anonymisation is the
  user's call.
- Keep recommendations specific and actionable. "Tighten the hero" is not a finding;
  "hero has no services list — add a 4–6 item 'What we do' block above the logo strip" is.
