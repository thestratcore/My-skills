# Publish gate

Run this as a standalone pass when the user is about to publish, or asks "is this safe to
publish". Report **pass / fail per item**. Any single fail on items 1–5 blocks
publication.

---

## 1. Client naming cleared

- Every client name on the page has **written sign-off**, or the case study is anonymised.
- If anonymised: read the description as an outsider trying to identify the client.
  Sector + technology + region + size together can de-anonymise. Fail if it can be
  guessed.

**Pass / Fail:**

## 2. Every published metric is signed off and traceable

- Each number traces to a graded evaluation, a measurement, or a dated log.
- Metrics from a pilot under a separate engagement have explicit clearance to be public.
- No estimate is presented as a result.

**Pass / Fail:**

## 3. Delivered vs draft status is accurate

- Nothing scoped, in design, or in draft is presented as delivered.
- Portfolio / use-case items carry a maturity tag.
- Verb tense and plurals do not imply more clients or more delivery than is real.

**Pass / Fail:**

## 4. No secrets or internal infrastructure

- No credentials, API keys, tokens, passwords on or linked from the site.
- No internal hostnames, internal IPs, or internal project numbers — in copy, in alt
  text, or baked into any diagram or embedded SVG.
- Published diagrams use role labels ("Control plane", "GPU compute host"), not real host
  names.

**Pass / Fail:**

## 5. Internal records do not contradict public claims

- No vault note or project doc marked `archive` / `superseded` / "not pursued" while the
  page runs the same thing as a live case study. Reconcile the record or the page first.

**Pass / Fail:**

## 6. Regulated case studies carry compliance framing

- EU AI Act risk tier stated.
- GDPR basis and data residency stated.
- Medical-device (MDR) scope stated where healthcare (in scope, or out and why).
- Human-in-the-loop boundary stated.

**Pass / Fail:**

## 7. Voice pass

- Sentence-case headings, no trailing `.` / `?`, no ALL-CAPS words.
- No exclamation points, no emoji, no "we're excited" / hype.
- Claims are evidence-backed; no guaranteed business outcomes.
- No invented entities.

**Pass / Fail:**

## 8. Visual pass (brand module)

- Dark-only palette; background `#0a0a0b` not `#000`; one green accent.
- Syne display, Montserrat body, OCR-A Extended for labels / status / KPI only.
- Lucide icons; approved imagery with a scrim; correct radius / spacing / motion tokens.
- Logo: correct lockup for the background, undistorted.

**Pass / Fail:**

---

## Worked example — the Stratcore AI services page

Verbatim §7 checklist from `Company/Stratcore/stratcore-web-improvement.md`:

> - [ ] **Client naming.** Named-hospital version vs "a regional hospital" version. Get
>   written sign-off before naming, and before publishing any metric — eval numbers come
>   from a pilot under a separate engagement.
> - [ ] **Do not promote drafts as delivered.** Use cases 1.1–7.0 are scoped, not
>   shipped. Keep the "delivered / in design" split honest.
> - [ ] **Secrets.** `Company/KNTB/KNTB-AI-Collection/DGX SPARK.md` contains live
>   monitoring and hotspot passwords; other collection files hold credentials. No
>   credentials, IP addresses or hostnames anywhere near the website.
> - [ ] **Reconcile the internal record.** Main vault `[[KNTB RAG Pipeline]]` is
>   `status: archive` ("no longer pursued"), while `KNTB-AI-Collection` shows it went live
>   (Phase 17, retrieval index activated 2026-07-09). Fix the main-vault note so it does
>   not contradict the case study.
