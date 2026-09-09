# Playwright MCP recipes

Exact call sequences for the capture step. Assumes the `playwright` MCP server is
connected (see SKILL.md prerequisites). Tool names are from `@playwright/mcp`.

---

## 0. Temp directory for screenshots

Save every screenshot under a per-run temp directory and `Read` each one back — the
visual analysis is done from the images. Use the session scratchpad directory if one is
announced in the environment; otherwise create one:

```
mkdir -p /tmp/webinspect-<yyyymmdd-hhmm>
```

Name shots `<width>-<page-slug>.png` (e.g. `375-services-ai.png`).

---

## 1. Navigate

```
browser_navigate  { "url": "<target URL>" }
```

Then give the page a moment to settle (lazy images, web fonts). If the MCP exposes a wait
tool use it; otherwise take an initial throwaway screenshot, then the real one.

---

## 2. Screenshot at four breakpoints

For each width in **1280, 1920, 768, 375**:

```
browser_resize          { "width": <W>, "height": 900 }
browser_take_screenshot { "fullPage": true, "filename": "/tmp/webinspect-<ts>/<W>-<slug>.png" }
```

Notes:
- Start at 1280 (the "reference" desktop), then 1920, then the two narrow widths — some
  layouts only load the mobile nav after a resize down.
- `fullPage: true` captures the whole scroll height. Also take one **above-the-fold**
  shot (`fullPage: false`) at 1280 and at 375 — first impression matters and a full-page
  shot flattens it.
- If the page has a cookie banner or modal on load, screenshot it, then dismiss it and
  re-shoot.

---

## 3. DOM / accessibility snapshot

```
browser_snapshot
```

Returns the accessibility tree. Use it for:
- every heading, in document order, with its level (dimension H)
- images and their accessible names / alt (dimension O)
- interactive elements and their names (dimensions O, P)
- any text containing internal hostnames, IPs, secrets (dimension E)

---

## 4. Console and network

```
browser_console_messages
```

Record JS errors, failed requests, mixed-content warnings, CSP violations. A page that
throws on load is at least P2.

---

## 5. Horizontal-overflow detector

```
browser_evaluate  { "function": "() => { const out = []; document.querySelectorAll('*').forEach(el => { if (el.scrollWidth > el.clientWidth + 1 && getComputedStyle(el).overflowX !== 'auto' && getComputedStyle(el).overflowX !== 'scroll') { out.push({ tag: el.tagName, cls: el.className, id: el.id, scrollWidth: el.scrollWidth, clientWidth: el.clientWidth }); } }); return out.slice(0, 40); }" }
```

Run it at **375** and **768** especially. Any hit that is not an intentional scroll
container is a dimension Q finding.

---

## 6. Optional: computed styles for the visual pass (brand module)

To confirm fonts and colours rather than eyeballing:

```
browser_evaluate  { "function": "() => { const pick = sel => { const el = document.querySelector(sel); if (!el) return null; const s = getComputedStyle(el); return { fontFamily: s.fontFamily, fontWeight: s.fontWeight, fontSize: s.fontSize, color: s.color, background: s.backgroundColor }; }; return { body: pick('body'), h1: pick('h1'), h2: pick('h2'), button: pick('button, .btn, a.button') }; }" }
```

Check against `brand-and-positioning.md`: body should be Montserrat, headings Syne,
page background `rgb(10, 10, 11)` (`#0a0a0b`).

---

## 7. Interactive states

If the page has tabs, an accordion, a nav dropdown, or a carousel: use `browser_click`
on each control and `browser_take_screenshot` the resulting state. Broken or empty
expanded states are findings.

---

## If the MCP is unavailable

Stop. Report that the visual and responsive passes cannot run, give the user the
`claude mcp add playwright ...` line from SKILL.md, and offer a **content-only** review
(dimensions A–K, P) via `WebFetch` — but only if the user explicitly accepts that
reduced scope. Do not present a content-only review as a full inspection.
