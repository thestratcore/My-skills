# Stratcore brand module

Run this module when the brand module is **on** — the domain is Stratcore-owned
(`thestratcore.com`) or the site was built by Stratcore to its design system. It powers
inspection dimensions **G, L, M, N** and sharpens A–F for Stratcore's own claims.

**Authoritative sources — read these, do not rely only on this summary:**

- `Company/Stratcore/stratcore-brand-guidelines.md` — the active brand digest.
- The `stratcore-design` skill (`~/.claude/skills/stratcore-design/`) — `README.md`,
  `tokens/*.css` (`colors.css`, `typography.css`, `spacing.css`, `effects.css`),
  `guidelines/*.html`, `components/*/*.prompt.md`.
- `Company/Stratcore/stratcore-web-improvement.md` — the running review log for the AI
  services page; check it for prior findings and decisions before re-reviewing that page.

---

## Canonical positioning

> **Stratcore is a Czech IT consultancy** — AI, data analysis, web development,
> automation, digital transformation.

Mission (from the archived 2024 guideline, still cited): "empower businesses with
innovative AI-driven solutions for smarter decision-making and greater efficiency."
Values: Innovation, Integrity, Excellence.

**The uBrand sample-copy trap.** The design-system `README.md` frames Stratcore as
*"an AI-driven enterprise architecture platform"* with the tagline *"Architecture,
aligned."* — this is **illustrative sample copy from the uBrand export, not a
repositioning.** The *visual* system in that folder is authoritative and used as-is; the
product story is not. Flag any site copy that:

- adopts the "enterprise architecture platform" framing as Stratcore's actual business, or
- uses the sample lexicon — **map, govern, drift, dependency, coverage** — as if it were
  Stratcore's positioning vocabulary, when the real engagement is something else.

---

## Colour (dimension L)

Dark theme only. Page background near-black `#0a0a0b` — **never pure `#000`**, never a
light theme.

| Token | Hex | Role |
|---|---|---|
| `--black` / `--bg-page` | `#0a0a0b` | Page background |
| `--surface-1` | `#0f1011` | Base surface |
| `--surface-2` | `#161719` | Cards, elevated panels |
| `--surface-3` | `#1e2022` | Inset / recessed |
| `--border-hairline` | `rgba(255,255,255,0.08)` | Default border |
| `--border-hairline-strong` | `rgba(255,255,255,0.14)` | Emphasised border |
| `--green-500` / `--accent` | `#008568` | Primary actions, active nav, focus, success |
| `--green-200` / hover | `#7fd6bd` | Accent hover |
| `--green-700` / active | `#014b3b` | Accent press |
| `--green-600` | `#026e56` | Glow ring border |
| `--accent-tint` | `rgba(0,133,104,0.14)` | Subtle green fill behind active items |
| `--green-glow` | `rgba(0,133,104,0.35)` | Focus glow |
| `--text-primary` | `#f5f6f5` | Headings, primary body |
| `--text-secondary` | `#9a9fa0` | Supporting text, labels |
| `--text-tertiary` | `#6b6f70` | Captions, disabled, metadata |
| `--text-on-accent` | `#04120e` | The only text colour on a green fill |
| `--success` | `#008568` | (semantic, supporting — not a brand colour) |
| `--warning` | `#e8a33d` | semantic |
| `--danger` | `#e5484d` | semantic |
| `--info` | `#4c9aff` | semantic |

Use green **sparingly — one accent.** If everything is green, that is a finding.

---

## Typography (dimension L)

| Role | Font | Size |
|---|---|---|
| Display XL / L | Syne 700–800 | `clamp(40–72px)` / `clamp(32–48px)` |
| Display M | Syne 700 | 28px |
| Heading L / M / S | Syne 700 | 24 / 20 / 17px |
| Body L / M / S | Montserrat 400–500 | 17 / 15 / 13px |
| Caption | Montserrat 500, uppercase, `0.08em` tracking | 12px |
| Mono accent | OCR-A Extended, `0.04em` tracking | 13px |

- Line height: 1.1 display, 1.25 heading, 1.6 body. Display tracking −0.01em.
- **OCR-A Extended is an accent voice only** — eyebrow labels, status strings
  (`SYS.STATUS: ONLINE`), version tags, KPI deltas, code-like labels. **Never body copy,
  never headlines.** OCR-A in a paragraph or an `h*` is a finding.
- Headlines and buttons: **sentence case** ("Start mapping", not "Start Mapping").
  Uppercase letter-spaced text is reserved for eyebrow labels and status strings.

---

## Spacing, radius, elevation, motion (dimension L)

- Spacing: base-8 — 4, 8, 12, 16, 24, 32, 48, 64, 96px. Content max-width 1200px,
  gutter 24px.
- Radius: 8px controls, 12px cards, 16 / 24px larger, 999px pill on badges.
- Elevation: 1px hairline border **plus** soft shadow — the shadow supplements, never
  replaces, the hairline. Focus = green glow ring.
- Motion: 120 / 200 / 320ms, easing `cubic-bezier(.4,0,.2,1)`. No bounce, no springy
  overshoot. Blur 20px only for the hero scrim and modal scrim.

---

## Imagery (dimensions L, O)

- Dark, cool, technical: isometric grids, particle meshes, teal / blue-black gradients.
- Full-bleed only behind hero / section-opener moments, **always with a dark gradient
  scrim** so foreground type stays legible (this is also an accessibility requirement).
- No illustration, no repeating pattern or texture, no hand-drawn elements.
- Never warm or saturated. Don't add grain.
- Approved set: `hero-lockup-grid.jpg`, `grid-perspective.jpg`, `particle-mesh.jpg`,
  `gradient-teal.jpg` (in the `stratcore-design` skill `assets/imagery/`).
- Explicitly rejected as off-brand: pink / warm ombre gradients, generic stock.

---

## Logo (dimension M)

Full lockup = cube-in-hexagon mark + `STRATCORE` wordmark (wordmark in OCR-A Extended).

- Default: **white lockup on a dark surface.**
- On light: black lockup on `#f5f6f5`, not pure white.
- Mark on solid `#008568`: white mark only.
- Preserve mark ↔ wordmark proportion and clear space.
- Never recolour, distort, rotate, rearrange, outline, or add effects.

---

## Iconography (dimensions G, N)

Interface icons are **Lucide**, 1.5px stroke. No emoji. No unicode-character icons. No
second icon set — flag one if it appears.

---

## Voice and copy (dimension G)

Enterprise / technical B2B. Direct, declarative, information-dense.

- State what the product does, not how the reader should feel — "Map, govern, and evolve
  your systems with AI", not "Revolutionize your architecture!".
- Third person about the product; second person ("your systems") in CTAs and body.
- **No exclamation points. No "we're excited". No emoji.**
- Prefer concrete, domain-specific vocabulary over generic SaaS words ("workspace",
  "workflow", "solution", "seamless", "empower", "unlock").
- Short sentences; ~two sentences per paragraph in hero / marketing copy.
- Support claims with evidence. No hype, no unsupported guarantees, no guaranteed business
  outcomes.
- Headlines and buttons in sentence case.

---

## AI content constraints (applies whenever generating or editing Stratcore copy)

- Treat brand statements as guidance, not independently verified fact.
- Do not invent services, clients, partnerships, awards, certifications, metrics, or
  case-study results.
- Do not claim guaranteed business outcomes.
- Keep output consistent with the mission, values, voice, palette, typography, and visual
  direction defined here and in the design system.
- Flag missing information instead of filling gaps with assumptions.

---

## Components (dimension N)

Authored primitives only: Button, IconButton, Icon, Card, StatCard, Table, Badge, Tag,
Toast, Tooltip, Checkbox, Input, Radio, Select, Switch, Tabs, Dialog. Each has a
`.jsx` + `.d.ts` + `.prompt.md` under the `stratcore-design` skill `components/`
(`core/`, `forms/`, `feedback/`, `navigation/`, `overlay/`, `data/`). `StatCard` and
`Table` are the data-dense additions — use them for metric tables, not a bespoke layout.
