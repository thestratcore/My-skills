#!/usr/bin/env python3
"""Audit Obsidian vault metadata, wikilinks, and indexing-risk signals."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


EXCLUDED_DIRS = {
    ".git",
    ".claude",
    ".obsidian",
    ".venv",
    ".pytest_cache",
    "node_modules",
    ".next",
}
# Vault-specific non-knowledge folders are NOT hardcoded here - pass them with
# --exclude (repeatable). For the Stratcore vault that means:
#   --exclude MySKILLS --exclude KNTB-AI-Collection --exclude slug \
#   --exclude "Stratcore Design System"
# Prefer the vault's own scripts/vault_audit.py when it has one; it is canonical.
REQUIRED_FRONTMATTER = ("title", "type", "status", "tags")
ALLOWED_TYPES = {
    "architecture",
    "technology",
    "project",
    "guide",
    "reference",
    "decision",
    "process",
    "specification",
    "business",
    "meeting",
    "research",
    "template",
    "index",
    "archive",
}
ALLOWED_STATUSES = {
    "draft",
    "active",
    "placeholder",
    "superseded",
    "archive",
    "unknown",
}
SECRET_PATTERN = re.compile(
    r"(key|token|secret|password|credential|oauth|login)", re.IGNORECASE
)
WIKILINK_PATTERN = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
FENCED_CODE_PATTERN = re.compile(r"^(```|~~~).*?^\1", re.MULTILINE | re.DOTALL)
INLINE_CODE_PATTERN = re.compile(r"`[^`\n]*`")


def strip_code(text: str) -> str:
    """Blank out code blocks and inline code before scanning for wikilinks.

    A [[link]] inside backticks is documentation *about* a link, not a link -
    e.g. a maintenance log describing a rename, or a component doc showing
    sample markup. Counting those as broken produces false positives, and a
    checker that cries wolf gets ignored."""
    text = FENCED_CODE_PATTERN.sub(" ", text)
    return INLINE_CODE_PATTERN.sub(" ", text)


EXTRA_EXCLUDED_DIRS: set[str] = set()


def is_excluded(path: Path) -> bool:
    excluded = EXCLUDED_DIRS | EXTRA_EXCLUDED_DIRS
    return any(part in excluded for part in path.parts)


def is_secret_like(path: Path) -> bool:
    return any(SECRET_PATTERN.search(part) for part in path.parts)


def parse_frontmatter(text: str) -> dict[str, Any] | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None

    frontmatter: dict[str, Any] = {}
    current_key: str | None = None
    for raw_line in text[4:end].splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - ") and current_key:
            frontmatter.setdefault(current_key, []).append(line[4:].strip().strip('"'))
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        current_key = key
        if value == "":
            frontmatter[key] = []
        else:
            frontmatter[key] = value.strip('"')
    return frontmatter


def markdown_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.md")
        if path.is_file() and not is_excluded(path.relative_to(root))
    )


def link_targets(paths: list[Path], root: Path) -> tuple[set[str], set[str]]:
    stems: set[str] = set()
    path_targets: set[str] = set()
    for path in paths:
        rel = path.relative_to(root)
        stems.add(path.stem)
        path_targets.add(rel.with_suffix("").as_posix())
    return stems, path_targets


def base_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.base")
        if path.is_file() and not is_excluded(path.relative_to(root))
    )


def non_markdown_files(root: Path) -> list[Path]:
    """Every non-Markdown file in scope. Obsidian happily links to attachments
    (PDF, images, spreadsheets) and to .base files, so they are legitimate
    wikilink targets and must not be reported as broken."""
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() != ".md"
        and not path.name.startswith(".")
        and not is_excluded(path.relative_to(root))
    )


BASE_VIEW_TYPE_RE = re.compile(r"^\s*-?\s*type:\s*(\S+)", re.MULTILINE)
BASE_VIEW_NAME_RE = re.compile(r"^\s*name:\s*(.+)$", re.MULTILINE)
BASE_ORDER_ITEM_RE = re.compile(r"^\s*-\s*([A-Za-z_][\w.]*)\s*$", re.MULTILINE)
BASE_GROUPBY_RE = re.compile(r"^\s*property:\s*([A-Za-z_][\w.]*)", re.MULTILINE)
BASE_COMPARISON_RE = re.compile(r"([A-Za-z_][\w.]*)\s*(?:==|!=|>=|<=|>|<)")
BASE_KNOWN_PREFIXES = ("file.", "formula.", "note.", "this.")


def base_referenced_properties(text: str) -> set[str]:
    """Property names a .base refers to, excluding file./formula./note. builtins."""
    names: set[str] = set()
    for pattern in (BASE_ORDER_ITEM_RE, BASE_GROUPBY_RE, BASE_COMPARISON_RE):
        for match in pattern.finditer(text):
            name = match.group(1)
            if name.startswith(BASE_KNOWN_PREFIXES):
                continue
            names.add(name)
    return names


def audit_bases(root: Path, known_properties: set[str]) -> list[dict[str, str]]:
    """Structural and property-reference checks for .base files.

    A .base with a mistyped property renders an empty view, which is
    indistinguishable from "nothing matched" - so an unknown property name is
    reported as a defect rather than left to be discovered by eye.

    Note: match counts per view are deliberately not computed. Doing so would
    require interpreting the Bases filter expression language.
    """
    issues: list[dict[str, str]] = []
    for path in base_files(root):
        rel_text = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            issues.append({"path": rel_text, "issue": f"unreadable: {exc}"})
            continue

        if "views:" not in text:
            issues.append({"path": rel_text, "issue": "no views: block"})
            continue
        view_types = BASE_VIEW_TYPE_RE.findall(text)
        view_names = BASE_VIEW_NAME_RE.findall(text)
        if not view_types:
            issues.append({"path": rel_text, "issue": "no view defines type:"})
        if len(view_names) < len(view_types):
            issues.append({"path": rel_text, "issue": "a view is missing name:"})

        for name in sorted(base_referenced_properties(text)):
            if name not in known_properties:
                issues.append(
                    {"path": rel_text, "issue": f"references unknown property {name!r}"}
                )
    return issues


def audit(root: Path) -> dict[str, Any]:
    paths = markdown_files(root)
    stems, path_targets = link_targets(paths, root)
    # Attachments and .base files are legitimate wikilink/embed targets, so count
    # them as resolvable rather than reporting them as broken links.
    for extra in non_markdown_files(root):
        rel = extra.relative_to(root)
        stems.add(extra.stem)
        stems.add(extra.name)
        path_targets.add(rel.with_suffix("").as_posix())
        path_targets.add(rel.as_posix())

    # Obsidian resolves wikilinks case-insensitively; match that, or notes like
    # [[OpenRouter]] pointing at Openrouter.md are reported as false positives.
    stems = {s.casefold() for s in stems}
    path_targets = {p.casefold() for p in path_targets}
    report: dict[str, Any] = {
        "root": str(root),
        "markdown_count": len(paths),
        "missing_frontmatter": [],
        "invalid_frontmatter": [],
        "secret_like_files": [],
        "broken_wikilinks": [],
        "placeholders": [],
        "base_issues": [],
    }
    known_properties: set[str] = set()

    for path in paths:
        rel = path.relative_to(root)
        rel_text = rel.as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        secret_like = is_secret_like(rel)
        if secret_like:
            report["secret_like_files"].append(rel_text)

        frontmatter = parse_frontmatter(text)
        if frontmatter is None:
            if not secret_like and path.name not in {"AGENTS.md", "CLAUDE.md"}:
                report["missing_frontmatter"].append(rel_text)
        else:
            for field in REQUIRED_FRONTMATTER:
                if field not in frontmatter:
                    report["invalid_frontmatter"].append(
                        {"path": rel_text, "issue": f"missing {field}"}
                    )
            known_properties.update(frontmatter)
            note_type = frontmatter.get("type")
            status = frontmatter.get("status")
            if note_type is not None and note_type not in ALLOWED_TYPES:
                report["invalid_frontmatter"].append(
                    {"path": rel_text, "issue": f"invalid type {note_type}"}
                )
            if status is not None and status not in ALLOWED_STATUSES:
                report["invalid_frontmatter"].append(
                    {"path": rel_text, "issue": f"invalid status {status}"}
                )
            if status == "placeholder":
                report["placeholders"].append(rel_text)

        for match in WIKILINK_PATTERN.finditer(strip_code(text)):
            target = match.group(1).strip().replace("\\", "/")
            target_name = Path(target).name
            if (
                target.casefold() not in path_targets
                and target_name.casefold() not in stems
            ):
                report["broken_wikilinks"].append({"path": rel_text, "target": target})

    report["base_issues"] = audit_bases(root, known_properties)

    report["summary"] = {
        "missing_frontmatter": len(report["missing_frontmatter"]),
        "invalid_frontmatter": len(report["invalid_frontmatter"]),
        "secret_like_files": len(report["secret_like_files"]),
        "broken_wikilinks": len(report["broken_wikilinks"]),
        "placeholders": len(report["placeholders"]),
        "base_issues": len(report["base_issues"]),
    }
    return report


def print_text_report(report: dict[str, Any]) -> None:
    print(f"Vault: {report['root']}")
    print(f"Markdown files: {report['markdown_count']}")
    for key, label in (
        ("missing_frontmatter", "Missing frontmatter"),
        ("invalid_frontmatter", "Invalid frontmatter"),
        ("secret_like_files", "Secret-like files"),
        ("broken_wikilinks", "Broken wikilinks"),
        ("placeholders", "Placeholder notes"),
        ("base_issues", "Base (.base) issues"),
    ):
        values = report[key]
        print(f"\n{label}: {len(values)}")
        for value in values:
            if isinstance(value, dict):
                print(f"- {value.get('path')}: {value.get('issue') or value.get('target')}")
            else:
                print(f"- {value}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vault_root", help="Path to the Obsidian vault root")
    parser.add_argument("--json", dest="json_path", help="Write JSON report to this path")
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="DIR",
        help=(
            "Directory name to exclude in addition to the built-in list. "
            "Repeatable. Use for vault-specific non-knowledge folders."
        ),
    )
    args = parser.parse_args()
    EXTRA_EXCLUDED_DIRS.update(args.exclude)

    root = Path(args.vault_root).resolve()
    if not root.exists() or not root.is_dir():
        print(f"Vault root does not exist or is not a directory: {root}", file=sys.stderr)
        return 2

    report = audit(root)
    if args.json_path:
        json_path = Path(args.json_path)
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print_text_report(report)

    has_errors = bool(
        report["missing_frontmatter"]
        or report["invalid_frontmatter"]
        or report["broken_wikilinks"]
        or report["base_issues"]
    )
    return 1 if has_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
