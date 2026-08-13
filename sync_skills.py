#!/usr/bin/env python3
"""Audit personal agent skills and copy healthy skills without overwriting.

Default mode is audit-only. Use ``--apply`` to copy healthy skill directories to
the configured Codex and Claude skill roots.

The script intentionally does not merge existing directories. If a destination
entry already exists, the complete skill is skipped so the destination remains
unchanged and the decision is visible in the report.
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
from pathlib import Path
from typing import Iterable


DEFAULT_SOURCE = Path("/Users/admin/Documents/Obsidian-Stratcore/MySKILLS")
DEFAULT_DESTINATIONS = (
    Path.home() / ".codex" / "skills",
    Path.home() / ".claude" / "skills",
)
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
        description="Audit MySKILLS and copy healthy skills without overwriting."
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
        help="destination skill root; may be supplied more than once",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="create destination roots and copy healthy skills; default is audit-only",
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


def occupied(path: Path) -> bool:
    """Return true for existing paths and dangling symlinks."""

    return os.path.lexists(path)


def copy_skills(entries: Iterable[Entry], destinations: Iterable[Path], apply: bool) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    copyable = [entry for entry in entries if entry.copyable and entry.kind == "directory"]
    for destination in destinations:
        if occupied(destination) and not destination.is_dir():
            actions.append({"destination": str(destination), "status": "error", "detail": "destination root is not a directory"})
            continue
        if apply:
            try:
                destination.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                actions.append({"destination": str(destination), "status": "error", "detail": str(exc)})
                continue
        else:
            actions.append({"destination": str(destination), "status": "would-create-root"})

        for entry in copyable:
            source = Path(entry.path)
            target = destination / source.name
            if occupied(target):
                actions.append({"destination": str(target), "status": "skipped-existing"})
                continue
            if not apply:
                actions.append({"destination": str(target), "status": "would-copy"})
                continue
            try:
                # dirs_exist_ok=False preserves the no-overwrite guarantee.
                shutil.copytree(source, target, symlinks=True, dirs_exist_ok=False)
                if sha256_tree(source) != sha256_tree(target):
                    actions.append({"destination": str(target), "status": "error", "detail": "post-copy hash mismatch"})
                else:
                    actions.append({"destination": str(target), "status": "copied"})
            except FileExistsError:
                actions.append({"destination": str(target), "status": "skipped-existing"})
            except OSError as exc:
                actions.append({"destination": str(target), "status": "error", "detail": str(exc)})
    return actions


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
) -> dict:
    duplicates = duplicate_groups(entries)
    return {
        "source": str(source),
        "destinations": [str(path) for path in destinations],
        "summary": {
            "entries": len(entries),
            "healthy_directories": sum(entry.copyable for entry in entries),
            "unhealthy_entries": sum(not entry.healthy for entry in entries),
            "duplicate_groups": sum(len(groups) for groups in duplicates.values()),
        },
        "duplicates": duplicates,
        "entries": [asdict(entry) for entry in entries],
        "copy_actions": actions,
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

    if report["copy_actions"]:
        print("Copy actions:")
        for action in report["copy_actions"]:
            detail = f" ({action['detail']})" if "detail" in action else ""
            print(f"  {action['status']}: {action['destination']}{detail}")

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
    try:
        entries = inspect_source(args.source)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    actions = copy_skills(entries, destinations, apply=args.apply)
    git_actions = commit_and_push(
        args.source,
        commit=args.commit,
        push=args.push,
        commit_message=args.commit_message,
        remote=args.remote,
        branch=args.branch,
    )
    report = build_report(args.source, destinations, entries, actions, git_actions)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_report(report)

    has_errors = any(entry["issues"] for entry in report["entries"])
    has_errors = has_errors or any(action["status"] == "error" for action in actions)
    has_errors = has_errors or any(action["status"] == "error" for action in git_actions)
    has_duplicates = bool(report["duplicates"])
    if has_errors or (args.fail_on_duplicates and has_duplicates):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
