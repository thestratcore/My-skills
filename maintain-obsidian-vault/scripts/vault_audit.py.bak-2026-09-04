#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

EXCLUDED_PARTS = {".git", ".obsidian", "node_modules", ".venv", ".pytest_cache", ".next"}
SECRET_HINTS = ("key", "token", "secret", "password", "credential", "oauth", "login")
REQUIRED_FRONTMATTER = ("title", "type", "status", "tags")


def is_markdown(path: Path) -> bool:
    return path.suffix.lower() == ".md" and not any(part in EXCLUDED_PARTS for part in path.parts)


def is_secret_like(path: Path) -> bool:
    name = path.name.lower()
    return any(hint in name for hint in SECRET_HINTS)


def has_frontmatter(text: str) -> bool:
    return text.startswith("---\n") and "\n---\n" in text[4:]


def frontmatter_block(text: str) -> str:
    if not has_frontmatter(text):
        return ""
    end = text.find("\n---\n", 4)
    return text[4:end]


def frontmatter_keys(block: str) -> set[str]:
    keys: set[str] = set()
    for line in block.splitlines():
        match = re.match(r"^([A-Za-z0-9_-]+):", line)
        if match:
            keys.add(match.group(1))
    return keys


def wikilinks(text: str) -> list[str]:
    return [m.strip() for m in re.findall(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]", text)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit an Obsidian vault for Codex maintenance.")
    parser.add_argument("vault", type=Path)
    parser.add_argument("--json", dest="json_path", type=Path)
    args = parser.parse_args()

    root = args.vault.resolve()
    files = sorted(p for p in root.rglob("*.md") if is_markdown(p.relative_to(root)))
    stems = {p.stem for p in files}
    path_targets = {p.relative_to(root).with_suffix("").as_posix() for p in files}

    missing_frontmatter = []
    missing_required_keys = []
    secret_like = []
    unresolved_links: dict[str, list[str]] = {}
    see_also_count = 0

    for path in files:
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        if is_secret_like(path):
            secret_like.append(rel)
            continue
        if not has_frontmatter(text):
            missing_frontmatter.append(rel)
        else:
            keys = frontmatter_keys(frontmatter_block(text))
            missing = [key for key in REQUIRED_FRONTMATTER if key not in keys]
            if missing:
                missing_required_keys.append({"path": rel, "missing": missing})
        if re.search(r"^## See also\s*$", text, flags=re.MULTILINE):
            see_also_count += 1
        for target in wikilinks(text):
            if target not in stems and target not in path_targets:
                unresolved_links.setdefault(target, []).append(rel)

    report = {
        "vault": str(root),
        "markdown_files": len(files),
        "secret_like_files": secret_like,
        "missing_frontmatter": missing_frontmatter,
        "missing_required_frontmatter_keys": missing_required_keys,
        "unresolved_wikilinks": unresolved_links,
        "see_also_sections": see_also_count,
        "excluded_parts": sorted(EXCLUDED_PARTS),
    }

    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.json_path:
        args.json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
