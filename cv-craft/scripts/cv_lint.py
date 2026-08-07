#!/usr/bin/env python3
"""Mechanical checks for Markdown CVs.

Reads each CV's own `cv:` frontmatter block for its rules, so the same linter works on any CV
without hard-coded assumptions. Checks that find nothing to run against are reported as skipped
rather than silently passing - a check you did not run is not a check that passed.

Usage:
    cv_lint.py <cv-file-or-directory> [--json report.json] [--quiet]

Exit codes: 0 clean or warnings only, 1 errors found, 2 bad invocation.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

# Characters that defeat naive parsers. Checked when conventions.ascii_only is true.
BAD_CHARS = {
    "‐": "hyphen", "‑": "non-breaking hyphen", "‒": "figure dash",
    "–": "en dash", "—": "em dash", "―": "horizontal bar",
    "‘": "left single quote", "’": "right single quote",
    "“": "left double quote", "”": "right double quote",
    "→": "right arrow", "®": "registered sign", "™": "trademark sign",
    "…": "ellipsis",
}

DATE_PATTERNS = {
    "MM/YYYY": re.compile(r"\b(0[1-9]|1[0-2])/(19|20)\d{2}\b"),
    "YYYY-MM": re.compile(r"\b(19|20)\d{2}-(0[1-9]|1[0-2])\b"),
    "Month YYYY": re.compile(
        r"\b(January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+(19|20)\d{2}\b"
    ),
}
# A line that looks like it is stating a date range, so we can tell "should match" from "irrelevant".
DATE_LINE = re.compile(r"\d{4}")

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "over", "across", "their", "them",
    "than", "then", "there", "these", "those", "was", "were", "are", "his", "her", "its", "not",
    "but", "all", "any", "our", "out", "including", "incl", "via", "per", "such", "also", "both",
    "each", "using", "used", "use", "within", "under", "while", "where", "which", "who", "whom",
    "how", "what", "when", "have", "has", "had", "been", "being", "will", "would", "can", "could",
}
# Tokens that look like entities: acronyms, product names, CamelCase, dotted or hyphenated names.
ENTITY = re.compile(r"\b(?:[A-Z][A-Za-z0-9]*(?:[.+#/-][A-Za-z0-9]+)*){1,}\b")
NUMERIC = re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:%|[KMB](?![A-Za-z])|CZK|EUR|USD|GBP|yrs?|years?)?\b",
                     re.IGNORECASE)
PLACEHOLDER = re.compile(r"(\[NUMBER\]|\[X\]|\bTODO\b|\bTBD\b|\bXX\b|<[A-Z ]{3,}>)")


@dataclass
class Finding:
    level: str          # error | warn | info
    check: str
    file: str
    line: int
    message: str


@dataclass
class FileReport:
    path: str
    role: str = "unknown"
    findings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)
    skipped: list = field(default_factory=list)


# ---------------------------------------------------------------------------- parsing


def split_frontmatter(text: str):
    """Return (frontmatter_dict, body, body_offset). Minimal YAML - no external dependency."""
    if not text.startswith("---"):
        return {}, text, 0
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text, 0
    raw = text[3:end]
    body = text[end + 4:]
    offset = text[:end + 4].count("\n")
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(raw) or {}
        if isinstance(data, dict):
            return data, body, offset
    except Exception:
        pass
    return _mini_yaml(raw), body, offset


def _mini_yaml(raw: str) -> dict:
    """Enough YAML for the cv: block - nested maps, block and inline lists, scalars.

    A key with an empty value is ambiguous between a map and a list until the next non-blank
    line is seen, so resolve it by lookahead rather than guessing.
    """
    lines = [l for l in raw.splitlines() if l.strip() and not l.lstrip().startswith("#")]

    def parse(idx: int, indent: int):
        """Parse a block at the given indent. Returns (value, next_index)."""
        if idx < len(lines) and lines[idx].strip().startswith("- "):
            items = []
            while idx < len(lines):
                cur = lines[idx]
                if len(cur) - len(cur.lstrip()) != indent or not cur.strip().startswith("- "):
                    break
                items.append(_scalar(cur.strip()[2:]))
                idx += 1
            return items, idx

        node: dict = {}
        while idx < len(lines):
            cur = lines[idx]
            cur_indent = len(cur) - len(cur.lstrip())
            if cur_indent < indent:
                break
            item = cur.strip()
            if ":" not in item:
                idx += 1
                continue
            key, _, val = item.partition(":")
            key, val = key.strip(), val.strip()
            idx += 1
            if val == "":
                if idx < len(lines):
                    nxt = lines[idx]
                    nxt_indent = len(nxt) - len(nxt.lstrip())
                    if nxt_indent > cur_indent or nxt.strip().startswith("- "):
                        child, idx = parse(idx, nxt_indent)
                        node[key] = child
                        continue
                node[key] = {}
            elif val.startswith("[") and val.endswith("]"):
                node[key] = [_scalar(v) for v in val[1:-1].split(",") if v.strip()]
            else:
                node[key] = _scalar(val)
        return node, idx

    result, _ = parse(0, 0)
    return result if isinstance(result, dict) else {}


def _scalar(v: str):
    v = v.strip().strip('"').strip("'")
    if v.lower() in ("true", "yes"):
        return True
    if v.lower() in ("false", "no"):
        return False
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    return v


def parse_body(body: str, offset: int):
    """Return sections: [{name, line, roles: [{title, line, bullets: [(line, text)]}]}]."""
    sections, cur_sec, cur_role = [], None, None
    for i, line in enumerate(body.splitlines(), start=offset + 1):
        s = line.strip()
        if s.startswith("## "):
            cur_sec = {"name": s[3:].strip(), "line": i, "roles": [], "bullets": []}
            sections.append(cur_sec)
            cur_role = None
        elif s.startswith("### ") and cur_sec is not None:
            cur_role = {"title": s[4:].strip(), "line": i, "bullets": []}
            cur_sec["roles"].append(cur_role)
        elif s.startswith("- ") and cur_sec is not None:
            target = cur_role["bullets"] if cur_role else cur_sec["bullets"]
            target.append((i, s[2:].strip()))
    return sections


def content_words(text: str) -> set:
    words = re.findall(r"[A-Za-z][A-Za-z0-9'+.#-]*", text.lower())
    return {w for w in words if len(w) > 2 and w not in STOPWORDS}


def strip_code_and_links(text: str) -> str:
    text = re.sub(r"`[^`]*`", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    return text


def entities(text: str) -> set:
    """Proper nouns, acronyms and product names - the tokens that carry factual claims.

    Ordinary words capitalised only because they open a sentence, bullet, or heading are not
    entities; treating them as such would flag every rewording as fabricated.
    """
    text = strip_code_and_links(text)
    out = set()
    for m in ENTITY.finditer(text):
        tok = m.group(0)
        if len(tok) < 2 or tok in ("The", "A", "An", "I"):
            continue
        prefix = text[:m.start()].rstrip(" \t*_")
        at_boundary = not prefix or prefix[-1] in ".!?:;\n-*|>#("
        # A plain Capitalised-then-lowercase word at a boundary is ordinary prose, not a name.
        if at_boundary and tok.isalpha() and tok[1:].islower():
            continue
        out.add(tok)
    return out


def numerics(text: str) -> set:
    return {m.group(0).strip().lower() for m in NUMERIC.finditer(strip_code_and_links(text))
            if any(c.isdigit() for c in m.group(0))}


def sentences(text: str):
    for part in re.split(r"(?<=[.!?])\s+", text):
        part = part.strip()
        if part:
            yield part


# ---------------------------------------------------------------------------- checks


def lint_file(path: Path, masters: dict) -> FileReport:
    text = path.read_text(encoding="utf-8")
    fm, body, offset = split_frontmatter(text)
    cv = fm.get("cv") if isinstance(fm.get("cv"), dict) else {}
    conv = cv.get("conventions") if isinstance(cv.get("conventions"), dict) else {}
    rep = FileReport(path=str(path), role=str(cv.get("role", "unknown")))
    add = lambda lvl, chk, ln, msg: rep.findings.append(
        Finding(lvl, chk, str(path), ln, msg))
    sections = parse_body(body, offset)
    lines = text.splitlines()

    if not cv:
        rep.skipped.append("no `cv:` frontmatter block - config-driven checks skipped; "
                           "see references/conventions.md to add one")

    # -- charset
    if conv.get("ascii_only"):
        for i, line in enumerate(lines, start=1):
            for ch, name in BAD_CHARS.items():
                if ch in line:
                    add("error", "charset", i, f"non-ASCII {name} ({ch!r}) breaks parser-safe output")
    elif cv:
        rep.skipped.append("charset: conventions.ascii_only not set")

    # -- dates
    fmt = conv.get("date_format")
    if fmt and fmt in DATE_PATTERNS:
        pat = DATE_PATTERNS[fmt]
        for i, line in enumerate(lines, start=1):
            s = line.strip().strip("*_ ")
            if not DATE_LINE.search(s) or s.startswith(("http", "|", ">")):
                continue
            if re.match(r"^\*{0,2}\d", s) or " - " in s:
                if not pat.search(s) and "Present" not in s and not re.search(r"\b(19|20)\d{2}\b", s):
                    add("warn", "dates", i, f"date line does not match declared format {fmt}")
    elif cv:
        rep.skipped.append("dates: conventions.date_format not set")

    # -- required sections
    required = conv.get("required_sections")
    if isinstance(required, list) and required:
        present = {s["name"].lower() for s in sections}
        for want in required:
            if str(want).lower() not in present:
                add("error", "structure", 1, f"required section missing: {want}")
    elif cv:
        rep.skipped.append("structure: conventions.required_sections not set")

    # -- heading separator
    sep = conv.get("heading_separator")
    if sep:
        for sec in sections:
            for role in sec["roles"]:
                if sep not in role["title"]:
                    add("warn", "structure", role["line"],
                        f"role heading lacks '{sep}' separator: {role['title'][:60]}")

    # Frontmatter declares the rules, so it must not be scanned for violations of them -
    # a never_disclose entry naming a topic is not the CV disclosing that topic.
    body_start = offset + 1

    # -- never disclose
    nd = cv.get("never_disclose")
    if isinstance(nd, list) and nd:
        for phrase in nd:
            p = str(phrase).lower()
            if not p:
                continue
            for i, line in enumerate(lines, start=1):
                if i >= body_start and p in line.lower():
                    add("error", "never-disclose", i, f"contains withheld topic: {phrase!r}")
                    break

    # -- placeholders and untraceable metric stubs
    for i, line in enumerate(lines, start=1):
        if i < body_start:
            continue
        m = PLACEHOLDER.search(line)
        if m and not line.strip().startswith(">"):
            add("error", "placeholder", i,
                f"unfilled placeholder {m.group(0)!r} - these get guessed at later")

    # -- bullets per role, sentence length
    cap = conv.get("max_bullets_per_role")
    longest = (0, 0, "")
    all_bullets = []
    for sec in sections:
        for role in sec["roles"]:
            all_bullets.extend(role["bullets"])
            if isinstance(cap, int) and len(role["bullets"]) > cap:
                add("warn", "volume", role["line"],
                    f"{len(role['bullets'])} bullets exceeds max_bullets_per_role={cap}: "
                    f"{role['title'][:50]}")
        all_bullets.extend(sec["bullets"])
    maxw = conv.get("max_sentence_words")
    for ln, btext in all_bullets:
        for sent in sentences(btext):
            n = len(sent.split())
            if n > longest[0]:
                longest = (n, ln, sent[:70])
            if isinstance(maxw, int) and n > maxw:
                add("warn", "sentence", ln, f"sentence is {n} words (cap {maxw})")
        # repeated content word inside one sentence
        for sent in sentences(btext):
            seen = {}
            # Split hyphenated compounds so "deterministic-first ... deterministic" is caught -
            # the repetition is just as audible to a reader as two bare repeats.
            for w in re.findall(r"[A-Za-z]{5,}", sent.lower()):
                if w in STOPWORDS:
                    continue
                seen[w] = seen.get(w, 0) + 1
            for w, c in seen.items():
                # A repeated noun is often just the subject matter ("retrieval evaluation ...
                # retrieval collections") and flagging every one buries the real defects. Three
                # uses, or two uses of a long distinctive word, is where it starts to read badly.
                if c >= 3 or (c == 2 and len(w) >= 11):
                    add("warn", "sentence", ln, f"word {w!r} repeats {c}x in one sentence")

    # -- duplicate claims across sections
    seen_pairs = set()
    for a in range(len(all_bullets)):
        la, ta = all_bullets[a]
        wa = content_words(ta)
        if len(wa) < 8:
            continue
        for b in range(a + 1, len(all_bullets)):
            lb, tb = all_bullets[b]
            wb = content_words(tb)
            if len(wb) < 8:
                continue
            j = len(wa & wb) / len(wa | wb)
            if j > 0.45 and (la, lb) not in seen_pairs:
                seen_pairs.add((la, lb))
                add("warn", "duplicate", lb,
                    f"reads as a duplicate of line {la} (overlap {j:.0%}) - the same claim twice "
                    f"reads as padding")

    # -- variant drift
    derived = cv.get("derived_from")
    if derived:
        mpath = (path.parent / str(derived)).resolve()
        master_text = masters.get(str(mpath))
        if master_text is None and mpath.exists():
            master_text = mpath.read_text(encoding="utf-8")
        if master_text is None:
            add("error", "drift", 1, f"derived_from points at missing master: {derived}")
        else:
            m_ent, m_num = entities(master_text), numerics(master_text)
            m_words = content_words(master_text)
            m_ent_lower = {e.lower() for e in m_ent}
            for i, line in enumerate(lines, start=1):
                stripped = line.strip()
                if i < body_start or not stripped or stripped.startswith((">", "#")):
                    continue
                # Section labels like "**Pipelines and Processing:**" are structure, not claims -
                # regrouping skills under new headings is exactly what derivation is supposed to
                # do, so scanning them for new entities flags every legitimate variant.
                content = re.sub(r"^\s*(?:[-*]\s+)?\*\*[^*]+:\*\*", "", line)
                if content.strip().startswith("**") or not content.strip():
                    continue
                is_claim = bool(re.match(r"^\s*[-*]\s+", line))
                for tok in entities(content):
                    if tok.lower() in m_ent_lower or tok.lower() in m_words:
                        continue
                    if is_claim:
                        add("error", "drift", i,
                            f"entity {tok!r} appears in this variant but not in the master - a "
                            f"variant must not claim what its master does not")
                    else:
                        add("warn", "drift", i,
                            f"entity {tok!r} is not in the master - fine if it is rewording, "
                            f"not fine if it is a new claim")
                for tok in numerics(content) - m_num:
                    add("error", "drift", i,
                        f"figure {tok!r} appears in this variant but not in the master")
            for ln, btext in all_bullets:
                w = content_words(btext)
                if len(w) >= 8 and len(w & m_words) / len(w) < 0.55:
                    add("warn", "drift", ln,
                        "bullet shares little vocabulary with the master - confirm it is a rewording "
                        "and not a new claim")
    elif rep.role == "variant":
        add("warn", "drift", 1, "cv.role is variant but cv.derived_from is unset - drift cannot be checked")

    rep.stats = {
        "words": len(text.split()),
        "sections": len(sections),
        "roles": sum(len(s["roles"]) for s in sections),
        "bullets": len(all_bullets),
        "longest_sentence_words": longest[0],
        "longest_sentence_line": longest[1],
    }
    return rep


# ---------------------------------------------------------------------------- driver


def collect(target: Path):
    if target.is_dir():
        return sorted(p for p in target.rglob("*.md") if not p.name.startswith("."))
    return [target]


SELFTEST_MASTER = """---
title: "Test Master"
cv:
  role: master
  conventions:
    ascii_only: true
    date_format: "MM/YYYY"
    heading_separator: "|"
    required_sections: [Professional Summary, Experience, Education]
    max_bullets_per_role: 3
    max_sentence_words: 30
  never_disclose: ["secret figure"]
---

# Test Person

## Professional Summary

Engineer with 6 years building data pipelines in Python and Airflow.

## Experience

### Data Engineer | Acme Corp
**01/2020 - Present | Berlin, Germany**

- Builds ingestion pipelines in Python and Airflow across 12 source systems.

## Education

### BSc Computer Science | TU Berlin
**09/2014 - 06/2017 | Berlin, Germany**
"""

SELFTEST_VARIANT = """---
title: "Test Variant"
cv:
  role: variant
  derived_from: ./master.md
  conventions:
    ascii_only: true
---

# Test Person

## Professional Summary

Engineer with 6 years building data pipelines in Python and Airflow.

## Experience

### Data Engineer | Acme Corp
**01/2020 - Present | Berlin, Germany**

- Builds ingestion pipelines in Python and Airflow across 12 source systems.
- Led the Kubernetes migration for 40 microservices, cutting costs by 35%.
"""

SELFTEST_DEFECTIVE = """---
title: "Test Defective"
cv:
  role: master
  conventions:
    ascii_only: true
    date_format: "MM/YYYY"
    heading_separator: "|"
    required_sections: [Professional Summary, Experience, Education]
    max_bullets_per_role: 3
  never_disclose: ["secret figure"]
---

# Test Person

## Professional Summary

Engineer — with experience.

## Experience

### Senior Engineer at Globex
**01/2021 - Present | Prague**

- Designed and operated the Atlas platform with metadata validation, deterministic chunking, embedding, retrieval evaluation and approval-based activation across the estate.
- Built the Atlas platform with metadata validation, deterministic chunking, embedding, retrieval evaluation and approval-based activation for the group.
- Improved throughput by [NUMBER]% using a deterministic-first approach with deterministic scheduling.
- Reduced the secret figure considerably.
"""


def selftest() -> int:
    """Verify the linter catches what it claims to. Run after installing on a new machine."""
    import tempfile

    cases = []
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "master.md").write_text(SELFTEST_MASTER, encoding="utf-8")
        (d / "variant.md").write_text(SELFTEST_VARIANT, encoding="utf-8")
        (d / "defective.md").write_text(SELFTEST_DEFECTIVE, encoding="utf-8")
        masters = {str(p.resolve()): p.read_text(encoding="utf-8") for p in d.glob("*.md")}

        def checks(name):
            rep = lint_file(d / name, masters)
            return rep, {f.check for f in rep.findings if f.level == "error"}, rep.findings

        rep, errs, all_f = checks("master.md")
        cases.append(("clean master reports nothing",
                      not rep.findings, f"{len(rep.findings)} finding(s)"))

        rep, errs, all_f = checks("variant.md")
        drift = [f for f in all_f if f.check == "drift" and f.level == "error"]
        cases.append(("variant drift catches the fabricated entity",
                      any("Kubernetes" in f.message for f in drift), f"{len(drift)} drift error(s)"))
        cases.append(("variant drift catches fabricated figures",
                      sum("figure" in f.message for f in drift) >= 2,
                      f"{sum('figure' in f.message for f in drift)} figure error(s)"))
        cases.append(("variant drift does not fire on shared content",
                      not any("Airflow" in f.message or "Acme" in f.message for f in drift),
                      "no false positives on master-shared entities"))

        rep, errs, all_f = checks("defective.md")
        warns = {f.check for f in all_f if f.level == "warn"}
        for label, want, pool in [
            ("charset catches the em dash", "charset", errs),
            ("structure catches the missing section", "structure", errs),
            ("placeholder catches [NUMBER]", "placeholder", errs),
            ("never-disclose catches the withheld phrase", "never-disclose", errs),
            ("duplicate catches the repeated claim", "duplicate", warns),
            ("volume catches bullets over cap", "volume", warns),
            ("sentence catches the repeated word", "sentence", warns),
        ]:
            cases.append((label, want in pool, f"{'found' if want in pool else 'MISSING'}: {want}"))

    failed = 0
    for label, ok, detail in cases:
        print(f"  {'PASS' if ok else 'FAIL'}  {label:52} {detail}")
        failed += not ok
    print(f"\nselftest: {len(cases) - failed}/{len(cases)} passed")
    return 1 if failed else 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Lint Markdown CVs against the conventions declared in their own frontmatter.")
    ap.add_argument("target", type=Path, nargs="?", help="CV file, or a directory of CVs")
    ap.add_argument("--json", type=Path, help="also write the full report as JSON")
    ap.add_argument("--quiet", action="store_true", help="print only errors")
    ap.add_argument("--selftest", action="store_true",
                    help="verify the linter's own checks against built-in fixtures")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    if args.target is None:
        ap.error("a target path is required (or use --selftest)")

    if not args.target.exists():
        print(f"error: no such path: {args.target}", file=sys.stderr)
        return 2

    files = collect(args.target)
    if not files:
        print(f"error: no .md files under {args.target}", file=sys.stderr)
        return 2

    masters = {str(p.resolve()): p.read_text(encoding="utf-8") for p in files}
    reports = [lint_file(p, masters) for p in files]

    errors = warns = 0
    for rep in reports:
        errs = [f for f in rep.findings if f.level == "error"]
        wrns = [f for f in rep.findings if f.level == "warn"]
        errors += len(errs)
        warns += len(wrns)
        show = errs if args.quiet else errs + wrns
        if not show and args.quiet:
            continue
        status = "FAIL" if errs else ("warn" if wrns else "ok")
        print(f"\n{rep.path}  [{rep.role}]  {status}")
        for f in sorted(show, key=lambda f: (f.line, f.check)):
            print(f"  {f.level:5} {f.check:14} line {f.line:<5} {f.message}")
        if not args.quiet:
            for s in rep.skipped:
                print(f"  skip  {s}")
            st = rep.stats
            print(f"  stats  {st['words']} words · {st['roles']} roles · {st['bullets']} bullets · "
                  f"longest sentence {st['longest_sentence_words']}w (line {st['longest_sentence_line']})")

    print(f"\n{len(files)} file(s): {errors} error(s), {warns} warning(s)")

    if args.json:
        payload = [{**asdict(r), "findings": [asdict(f) for f in r.findings]} for r in reports]
        args.json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"report written to {args.json}")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
