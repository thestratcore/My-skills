#!/usr/bin/env python3
"""Audit personal agent skills and sync them across every skill root.

Default mode is audit-only: it prints the sync plan. ``--apply`` executes it.

Hub roots (MySKILLS, ~/.codex/skills, ~/.claude/skills) end up identical. Feeder
roots (the vault's own .claude/skills and .codex/skills) only contribute skills;
they never receive copies. When copies of a skill differ, the copy whose newest
file is latest wins and replaces the others as a whole folder. The replaced
folder is moved to a timestamped backup first. Equal timestamps with different
content are reported as a tie and left alone.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable


DEFAULT_SOURCE = Path("/Users/admin/Documents/Obsidian-Stratcore/MySKILLS")
DEFAULT_DESTINATIONS = (
    Path.home() / ".codex" / "skills",
    Path.home() / ".claude" / "skills",
)
DEFAULT_FEEDERS = (
    DEFAULT_SOURCE.parent / ".claude" / "skills",
    DEFAULT_SOURCE.parent / ".codex" / "skills",
)
# Folders that live in skill roots but are not skills.
EXCLUDED_NAMES = {"synced"}
EXCLUDED_SUFFIXES = ("-workspace",)
IGNORED_FILES = {".DS_Store"}
BACKUP_DIR = "_MySKILLS-zips/sync-backups"
SECRET_PATTERNS = (
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("API key (sk-)", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Slack token", re.compile(r"\bxox[abpr]-[A-Za-z0-9-]{10,}")),
    ("URL with password", re.compile(r"[a-z][a-z0-9+.-]*://[^\s:/@]+:[^\s@/<>{}$]{3,}@")),
    (
        "password assignment",
        re.compile(
            r"(?i)\b(?:password|passwd|pwd|pgpassword|secret)\b\s*[:=]\s*[\"']?"
            r"(?![<{$*\[(]|\s|$)[^\s\"'`]{4,}"
        ),
    ),
)
SECRET_SCAN_MAX_BYTES = 1024 * 1024
DEFAULT_COMMIT_MESSAGE = "chore(skills): sync personal skills"
SENSITIVE_NAME_PARTS = (
    ".env",
    "api-key",
    "apikey",
    "credential",
    "login",
    "oauth",
    "password",
    "private-key",
    "secret",
    "token",
)


@dataclass
class Entry:
    path: str
    kind: str
    folder_name: str
    healthy: bool = False
    copyable: bool = False
    skill_name: str | None = None
    skill_hash: str | None = None
    tree_hash: str | None = None
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit skill roots and sync them (missing copied, newest version wins)."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"source directory (default: {DEFAULT_SOURCE})",
    )
    parser.add_argument(
        "--destination",
        type=Path,
        action="append",
        dest="destinations",
        help="hub skill root besides --source; may be supplied more than once",
    )
    parser.add_argument(
        "--feeder",
        type=Path,
        action="append",
        dest="feeders",
        help="read-only skill root that only contributes skills; may be supplied more than once",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="execute the sync plan; default is audit-only",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit the report as JSON",
    )
    parser.add_argument(
        "--fail-on-duplicates",
        action="store_true",
        help="return exit code 1 when duplicate skills are found",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="stage all MySKILLS repository changes and create a commit",
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="push the new commit to the configured remote; requires --commit",
    )
    parser.add_argument(
        "--commit-message",
        default=DEFAULT_COMMIT_MESSAGE,
        help=f"commit message (default: {DEFAULT_COMMIT_MESSAGE!r})",
    )
    parser.add_argument(
        "--remote",
        default="origin",
        help="Git remote to push (default: origin)",
    )
    parser.add_argument(
        "--branch",
        help="current Git branch to push; defaults to the checked-out branch",
    )
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_tree(root: Path) -> str:
    """Hash relative paths and file contents in deterministic order."""

    digest = hashlib.sha256()
    paths = sorted(root.rglob("*"), key=lambda path: path.relative_to(root).as_posix())
    for path in paths:
        if path.name in IGNORED_FILES:
            continue
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            digest.update(f"L:{relative}:{os.readlink(path)}\n".encode("utf-8"))
        elif path.is_dir():
            digest.update(f"D:{relative}\n".encode("utf-8"))
        elif path.is_file():
            digest.update(f"F:{relative}\n".encode("utf-8"))
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
        else:
            digest.update(f"?:{relative}\n".encode("utf-8"))
    return digest.hexdigest()


def frontmatter_metadata(text: str) -> tuple[dict[str, str], list[str]]:
    """Read the small subset of frontmatter needed for health checks.

    This avoids a PyYAML dependency. The check validates required keys and
    delimiters, but does not claim to be a complete YAML parser.
    """

    issues: list[str] = []
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, ["SKILL.md does not start with YAML frontmatter (---)"]

    closing_index = next(
        (index for index in range(1, len(lines)) if lines[index].strip() == "---"),
        None,
    )
    if closing_index is None:
        return {}, ["SKILL.md frontmatter has no closing --- delimiter"]

    metadata: dict[str, str] = {}
    key_pattern = re.compile(r"^([A-Za-z0-9_-]+):(?:\s*(.*))?$")
    current_key: str | None = None
    for line in lines[1:closing_index]:
        match = key_pattern.match(line)
        if match:
            current_key = match.group(1)
            metadata[current_key] = (match.group(2) or "").strip()
        elif line.strip() and current_key in {"name", "description"}:
            # Multiline YAML values are accepted when they are indented.
            if line[:1].isspace():
                metadata[current_key] = (metadata[current_key] + " " + line.strip()).strip()
            else:
                issues.append(f"unrecognized frontmatter line: {line}")

    if not metadata.get("name"):
        issues.append("frontmatter is missing a non-empty name")
    if not metadata.get("description"):
        issues.append("frontmatter is missing a non-empty description")
    return metadata, issues


def check_broken_symlinks(root: Path) -> list[str]:
    issues: list[str] = []
    for path in root.rglob("*"):
        if path.is_symlink() and not path.exists():
            issues.append(f"broken symlink: {path.relative_to(root)}")
    return issues


def inspect_directory(path: Path) -> Entry:
    entry = Entry(
        path=str(path),
        kind="directory",
        folder_name=path.name,
    )
    if path.is_symlink():
        entry.issues.append("skill directory is a symlink; refusing to copy it")
        return entry

    skill_md = path / "SKILL.md"
    if not skill_md.is_file():
        entry.issues.append("missing SKILL.md")
        return entry

    try:
        text = skill_md.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        entry.issues.append(f"cannot read SKILL.md: {exc}")
        return entry

    metadata, frontmatter_issues = frontmatter_metadata(text)
    entry.issues.extend(frontmatter_issues)
    entry.skill_name = metadata.get("name") or None
    if entry.skill_name and entry.skill_name.casefold() != path.name.casefold():
        entry.warnings.append(
            f"frontmatter name {entry.skill_name!r} differs from directory name {path.name!r}"
        )
    entry.issues.extend(check_broken_symlinks(path))

    try:
        entry.skill_hash = sha256_file(skill_md)
        entry.tree_hash = sha256_tree(path)
    except OSError as exc:
        entry.issues.append(f"cannot hash skill contents: {exc}")

    entry.healthy = not entry.issues
    entry.copyable = entry.healthy
    return entry


def inspect_package(path: Path) -> Entry:
    entry = Entry(
        path=str(path),
        kind=".skill archive",
        folder_name=path.stem,
    )
    try:
        with zipfile.ZipFile(path) as archive:
            bad_member = archive.testzip()
            if bad_member:
                entry.issues.append(f"archive integrity check failed at {bad_member}")
            skill_members = [
                name
                for name in archive.namelist()
                if Path(name).name == "SKILL.md" and not name.endswith("/")
            ]
            if not skill_members:
                entry.issues.append("archive does not contain SKILL.md")
            else:
                metadata, frontmatter_issues = frontmatter_metadata(
                    archive.read(skill_members[0]).decode("utf-8")
                )
                entry.issues.extend(frontmatter_issues)
                entry.skill_name = metadata.get("name") or None
    except (OSError, zipfile.BadZipFile, UnicodeError) as exc:
        entry.issues.append(f"cannot inspect archive: {exc}")

    entry.healthy = not entry.issues
    entry.warnings.append("package archive is reported but not copied; use its unpacked directory")
    entry.copyable = False
    return entry


def inspect_source(source: Path) -> list[Entry]:
    if not source.is_dir():
        raise ValueError(f"source directory does not exist: {source}")

    entries: list[Entry] = []
    for path in sorted(source.iterdir(), key=lambda item: item.name.casefold()):
        if path.name.startswith("."):
            continue
        if path.is_dir():
            entries.append(inspect_directory(path))
        elif path.is_file() and path.suffix == ".skill":
            entries.append(inspect_package(path))
    return entries


def duplicate_groups(entries: Iterable[Entry]) -> dict[str, list[list[str]]]:
    groups: dict[str, list[list[str]]] = {}

    def collect(label: str, values: Iterable[tuple[str, str | None]]) -> None:
        by_value: dict[str, list[str]] = defaultdict(list)
        for display_name, value in values:
            if value:
                by_value[value].append(display_name)
        duplicates = [sorted(names) for names in by_value.values() if len(names) > 1]
        if duplicates:
            groups[label] = sorted(duplicates)

    collect(
        "frontmatter_name",
        ((entry.path, entry.skill_name.casefold() if entry.skill_name else None) for entry in entries),
    )
    collect("SKILL.md content", ((entry.path, entry.skill_hash) for entry in entries))
    collect("complete tree content", ((entry.path, entry.tree_hash) for entry in entries))

    # A .skill archive and an unpacked directory with the same base name are
    # duplicate representations of one skill, even though their byte hashes differ.
    by_folder_name: dict[str, list[str]] = defaultdict(list)
    for entry in entries:
        by_folder_name[entry.folder_name.casefold()].append(entry.path)
    package_duplicates = [sorted(paths) for paths in by_folder_name.values() if len(paths) > 1]
    if package_duplicates:
        groups["same skill/package name"] = sorted(package_duplicates)
    return groups


def is_skill_candidate(path: Path) -> bool:
    """Return true for folders that look like skills rather than workspaces or caches."""

    name = path.name
    if name.startswith((".", "_")) or name in EXCLUDED_NAMES or name.endswith(EXCLUDED_SUFFIXES):
        return False
    return path.is_dir() and not path.is_symlink() and (path / "SKILL.md").is_file()


def newest_mtime(root: Path) -> float:
    times = [
        path.lstat().st_mtime
        for path in root.rglob("*")
        if path.name not in IGNORED_FILES and not path.is_dir()
    ]
    return max(times, default=root.lstat().st_mtime)


def scan_secrets(root: Path, paths: Iterable[Path] | None = None) -> list[str]:
    """Return "relative/path:line: kind" findings for secret-looking file content."""

    findings: list[str] = []
    candidates = paths if paths is not None else root.rglob("*")
    for path in sorted(candidates):
        if path.name in IGNORED_FILES or path.is_symlink() or not path.is_file():
            continue
        try:
            if path.stat().st_size > SECRET_SCAN_MAX_BYTES:
                continue
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        try:
            shown = path.relative_to(root).as_posix()
        except ValueError:
            shown = str(path)
        for kind, pattern in SECRET_PATTERNS:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                findings.append(f"{shown}:{line}: {kind}")
    return findings


def plan_sync(hubs: list[Path], feeders: list[Path]) -> tuple[list[dict[str, str]], dict[str, list[str]]]:
    """Plan copies and replacements so every hub holds the newest copy of every skill."""

    actions: list[dict[str, str]] = []
    secrets: dict[str, list[str]] = {}
    roots = [*hubs, *feeders]
    names: set[str] = set()
    for root in roots:
        if root.is_dir():
            names.update(path.name for path in root.iterdir() if is_skill_candidate(path))

    for name in sorted(names, key=str.casefold):
        copies = {root: inspect_directory(root / name) for root in roots if is_skill_candidate(root / name)}
        healthy = {root: entry for root, entry in copies.items() if entry.healthy}
        for entry in copies.values():
            if not entry.healthy:
                actions.append({
                    "skill": name, "status": "error", "destination": entry.path,
                    "detail": "unhealthy copy ignored: " + "; ".join(entry.issues),
                })
        if not healthy:
            continue

        times = {root: newest_mtime(Path(entry.path)) for root, entry in healthy.items()}
        newest_time = max(times.values())
        newest = [root for root, time in times.items() if time == newest_time]
        if len({healthy[root].tree_hash for root in newest}) > 1:
            actions.append({
                "skill": name, "status": "tie",
                "destination": " <-> ".join(healthy[root].path for root in newest),
                "detail": "different content with the same newest timestamp; resolve manually",
            })
            continue
        winner = healthy[newest[0]]
        stamp = datetime.fromtimestamp(newest_time).strftime("%Y-%m-%d %H:%M:%S")

        for hub in hubs:
            target = hub / name
            if hub in healthy and healthy[hub].tree_hash == winner.tree_hash:
                continue
            if hub in copies and not copies[hub].healthy:
                continue  # already reported; never overwrite an unhealthy copy silently
            if os.path.lexists(target) and hub not in copies:
                actions.append({
                    "skill": name, "status": "error", "destination": str(target),
                    "detail": "target exists but is not a skill folder; resolve manually",
                })
                continue
            actions.append({
                "skill": name, "status": "replace" if hub in copies else "copy",
                "source": winner.path, "destination": str(target), "detail": f"newest {stamp}",
            })
            if name not in secrets:
                findings = scan_secrets(Path(winner.path))
                if findings:
                    secrets[name] = findings
    return actions, secrets


def backup_path(source: Path, target: Path, run_stamp: str) -> Path:
    label = re.sub(r"[^A-Za-z0-9._-]+", "_", str(target.parent).strip("/"))
    return source / BACKUP_DIR / run_stamp / label / target.name


def apply_sync(actions: list[dict[str, str]], source: Path) -> None:
    """Execute planned copy/replace actions, updating each action's status in place."""

    run_stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    for action in actions:
        if action["status"] not in {"copy", "replace"}:
            continue
        origin = Path(action["source"])
        target = Path(action["destination"])
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            if action["status"] == "replace":
                backup = backup_path(source, target, run_stamp)
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(target), str(backup))
                action["backup"] = str(backup)
            shutil.copytree(origin, target, symlinks=True, ignore=shutil.ignore_patterns(*IGNORED_FILES))
            if sha256_tree(origin) != sha256_tree(target):
                action["status"] = "error"
                action["detail"] = "post-copy hash mismatch"
            else:
                action["status"] = "copied" if action["status"] == "copy" else "replaced"
        except OSError as exc:
            action["status"] = "error"
            action["detail"] = str(exc)


def verify_hubs(hubs: list[Path]) -> list[str]:
    """Return skill names whose content is missing or differs across hubs."""

    names: set[str] = set()
    for hub in hubs:
        if hub.is_dir():
            names.update(path.name for path in hub.iterdir() if is_skill_candidate(path))
    return [
        name
        for name in sorted(names, key=str.casefold)
        if len({sha256_tree(hub / name) if is_skill_candidate(hub / name) else None for hub in hubs}) > 1
    ]


def redact_git_output(text: str) -> str:
    """Remove credentials from Git diagnostics before they reach the report."""

    return re.sub(r"(https?://)([^/@\s]+@)", r"\1REDACTED@", text).strip()


def run_git(source: Path, arguments: list[str]) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=source,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        diagnostic = redact_git_output(result.stderr or result.stdout)
        raise RuntimeError(f"git {' '.join(arguments)} failed: {diagnostic}")
    return result.stdout.strip()


def git_changed_paths(source: Path) -> list[str]:
    output = run_git(source, ["status", "--porcelain=v1", "-z"])
    paths: list[str] = []
    records = [record for record in output.split("\0") if record]
    index = 0
    while index < len(records):
        record = records[index]
        if not record:
            index += 1
            continue
        status_code = record[:2]
        path = record[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path)
        if "R" in status_code or "C" in status_code:
            # NUL-delimited porcelain v1 stores the old rename/copy path in
            # the following record without a status prefix.
            index += 1
            if index < len(records):
                paths.append(records[index])
        index += 1
    return paths


def sensitive_paths(paths: Iterable[str]) -> list[str]:
    blocked: list[str] = []
    for path in paths:
        components = [component.casefold() for component in Path(path).parts]
        if any(
            part == ".env"
            or any(marker in part for marker in SENSITIVE_NAME_PARTS if marker != ".env")
            for part in components
        ):
            blocked.append(path)
    return sorted(set(blocked))


def commit_and_push(
    source: Path,
    commit: bool,
    push: bool,
    commit_message: str,
    remote: str,
    branch: str | None,
) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    if push and not commit:
        return [{"status": "error", "detail": "--push requires --commit"}]
    if not commit:
        return actions

    try:
        repository_root = Path(run_git(source, ["rev-parse", "--show-toplevel"])).resolve()
        if repository_root != source.resolve():
            return [{
                "status": "error",
                "detail": f"source must be the Git repository root: {repository_root}",
            }]

        current_branch = run_git(source, ["branch", "--show-current"])
        target_branch = branch or current_branch
        if not target_branch:
            return [{"status": "error", "detail": "repository is in detached HEAD state; provide a checked-out branch"}]
        if branch and branch != current_branch:
            return [{
                "status": "error",
                "detail": f"--branch {branch!r} does not match checked-out branch {current_branch!r}",
            }]

        existing_changes = git_changed_paths(source)
        blocked = sensitive_paths(existing_changes)
        if blocked:
            return [{
                "status": "error",
                "detail": "refusing to stage sensitive-looking paths: " + ", ".join(blocked),
            }]

        content_findings = scan_secrets(
            source, [source / path for path in existing_changes if not path.startswith("_")]
        )
        if content_findings:
            return [{
                "status": "error",
                "detail": "refusing to commit secret-looking content: " + "; ".join(content_findings),
            }]

        run_git(source, ["add", "--all", "--", "."])
        staged = run_git(source, ["diff", "--cached", "--name-only"])
        if staged:
            run_git(source, ["commit", "-m", commit_message])
            commit_hash = run_git(source, ["rev-parse", "--short", "HEAD"])
            actions.append({
                "status": "committed",
                "detail": f"{commit_hash} on {current_branch}",
            })
        else:
            actions.append({"status": "nothing-to-commit", "detail": current_branch})

        if push:
            run_git(source, ["push", remote, target_branch])
            actions.append({
                "status": "pushed",
                "detail": f"{remote}/{target_branch}",
            })
    except (OSError, RuntimeError) as exc:
        actions.append({"status": "error", "detail": str(exc)})
    return actions


def build_report(
    source: Path,
    destinations: list[Path],
    entries: list[Entry],
    actions: list[dict[str, str]],
    git_actions: list[dict[str, str]],
    feeders: list[Path] | None = None,
    secrets: dict[str, list[str]] | None = None,
    mismatched: list[str] | None = None,
) -> dict:
    duplicates = duplicate_groups(entries)
    return {
        "source": str(source),
        "destinations": [str(path) for path in destinations],
        "feeders": [str(path) for path in feeders or []],
        "summary": {
            "entries": len(entries),
            "healthy_directories": sum(entry.copyable for entry in entries),
            "unhealthy_entries": sum(not entry.healthy for entry in entries),
            "duplicate_groups": sum(len(groups) for groups in duplicates.values()),
        },
        "duplicates": duplicates,
        "entries": [asdict(entry) for entry in entries],
        "sync_actions": actions,
        "secret_findings": secrets or {},
        "hub_mismatches": mismatched,
        "git_actions": git_actions,
    }


def print_report(report: dict) -> None:
    summary = report["summary"]
    print(f"Source: {report['source']}")
    print(
        "Inventory: {entries} entries; {healthy_directories} healthy directories; "
        "{unhealthy_entries} unhealthy entries; {duplicate_groups} duplicate groups".format(**summary)
    )

    for entry in report["entries"]:
        status = "HEALTHY" if entry["healthy"] else "UNHEALTHY"
        print(f"[{status}] {entry['path']}")
        for issue in entry["issues"]:
            print(f"  ERROR: {issue}")
        for warning in entry["warnings"]:
            print(f"  WARNING: {warning}")

    if report["duplicates"]:
        print("Duplicates:")
        for kind, groups in report["duplicates"].items():
            for group in groups:
                print(f"  {kind}: {' <-> '.join(group)}")

    print("Hubs: " + ", ".join([report["source"], *report["destinations"]]))
    if report["feeders"]:
        print("Feeders (read-only): " + ", ".join(report["feeders"]))
    if report["sync_actions"]:
        print("Sync actions:" if report.get("applied") else "Sync plan (audit only):")
        for action in report["sync_actions"]:
            origin = f" <- {action['source']}" if "source" in action else ""
            detail = f" ({action['detail']})" if "detail" in action else ""
            backup = f" [backup: {action['backup']}]" if "backup" in action else ""
            print(f"  {action['status']}: {action['skill']} -> {action['destination']}{origin}{detail}{backup}")
    else:
        print("Sync plan: nothing to do; all hubs already match.")
    if report["secret_findings"]:
        print("Secret-looking content in skills being copied (review before committing):")
        for name, findings in report["secret_findings"].items():
            for finding in findings:
                print(f"  {name}/{finding}")
    if report["hub_mismatches"] is not None:
        if report["hub_mismatches"]:
            print("Verify: hubs still differ for: " + ", ".join(report["hub_mismatches"]))
        else:
            print("Verify: all hubs identical.")

    if report["git_actions"]:
        print("Git actions:")
        for action in report["git_actions"]:
            detail = f" ({action['detail']})" if "detail" in action else ""
            print(f"  {action['status']}{detail}")


def main() -> int:
    args = parse_args()
    if args.push and not args.commit:
        print("ERROR: --push requires --commit", file=sys.stderr)
        return 2
    destinations = args.destinations or list(DEFAULT_DESTINATIONS)
    feeders = args.feeders if args.feeders is not None else list(DEFAULT_FEEDERS)
    hubs = [args.source, *destinations]
    try:
        entries = inspect_source(args.source)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    actions, secrets = plan_sync(hubs, feeders)
    mismatched = None
    if args.apply:
        apply_sync(actions, args.source)
        mismatched = verify_hubs(hubs)
    git_actions = commit_and_push(
        args.source,
        commit=args.commit,
        push=args.push,
        commit_message=args.commit_message,
        remote=args.remote,
        branch=args.branch,
    )
    report = build_report(
        args.source, destinations, entries, actions, git_actions,
        feeders=feeders, secrets=secrets, mismatched=mismatched,
    )
    report["applied"] = args.apply
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_report(report)

    has_errors = any(entry["issues"] for entry in report["entries"])
    has_errors = has_errors or any(action["status"] in {"error", "tie"} for action in actions)
    has_errors = has_errors or bool(mismatched)
    has_errors = has_errors or any(action["status"] == "error" for action in git_actions)
    has_duplicates = bool(report["duplicates"])
    if has_errors or (args.fail_on_duplicates and has_duplicates):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
