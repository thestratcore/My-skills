#!/usr/bin/env python3
"""Deterministic tests for sync_skills.py Git and health-check behavior."""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import sync_skills


class SyncSkillsTests(unittest.TestCase):
    def test_frontmatter_requires_name_and_description(self) -> None:
        metadata, issues = sync_skills.frontmatter_metadata(
            "---\nname: example\ndescription: A test skill\n---\n# Example\n"
        )
        self.assertEqual(metadata["name"], "example")
        self.assertEqual(metadata["description"], "A test skill")
        self.assertEqual(issues, [])

    def test_sensitive_paths_are_blocked(self) -> None:
        blocked = sync_skills.sensitive_paths([".env", "agents/openai.yaml", "docs/API-TOKEN.md"])
        self.assertEqual(blocked, [".env", "docs/API-TOKEN.md"])

    def test_commit_changes_in_temporary_repository(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repository, check=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repository, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repository, check=True)
            (repository / "README.md").write_text("test\n", encoding="utf-8")

            actions = sync_skills.commit_and_push(
                repository,
                commit=True,
                push=False,
                commit_message="test: commit sync changes",
                remote="origin",
                branch=None,
            )

            self.assertEqual(actions[0]["status"], "committed")
            log = subprocess.run(
                ["git", "log", "-1", "--pretty=%s"],
                cwd=repository,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            self.assertEqual(log, "test: commit sync changes")

    def test_commit_refuses_secret_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repository, check=True)
            (repository / "notes.md").write_text("pass" + "word: hunter2hunter2\n", encoding="utf-8")
            actions = sync_skills.commit_and_push(
                repository, commit=True, push=False, commit_message="x", remote="origin", branch=None
            )
            self.assertEqual(actions[0]["status"], "error")
            self.assertIn("password assignment", actions[0]["detail"])

    def test_secret_scan_ignores_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.md").write_text("password: <your password>\nPGPASSWORD=$PASS\n", encoding="utf-8")
            self.assertEqual(sync_skills.scan_secrets(root), [])


def write_skill(root: Path, name: str, body: str, mtime: float) -> Path:
    path = root / name
    path.mkdir(parents=True, exist_ok=True)
    skill = path / "SKILL.md"
    skill.write_text(f"---\nname: {name}\ndescription: test\n---\n{body}\n", encoding="utf-8")
    os.utime(skill, (mtime, mtime))
    return path


class SyncPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory()
        base = Path(self._directory.name)
        self.vault, self.claude, self.codex, self.feeder = (base / n for n in ("vault", "claude", "codex", "feeder"))
        for root in (self.vault, self.claude, self.codex, self.feeder):
            root.mkdir()
        self.hubs = [self.vault, self.claude, self.codex]

    def tearDown(self) -> None:
        self._directory.cleanup()

    def sync(self) -> list[dict[str, str]]:
        actions, _ = sync_skills.plan_sync(self.hubs, [self.feeder])
        sync_skills.apply_sync(actions, self.vault)
        return actions

    def test_missing_skills_copied_from_feeder_and_hubs(self) -> None:
        write_skill(self.feeder, "fed", "x", 1000)
        write_skill(self.claude, "local", "y", 1000)
        self.sync()
        self.assertEqual(sync_skills.verify_hubs(self.hubs), [])
        self.assertTrue((self.codex / "fed" / "SKILL.md").is_file())
        self.assertFalse((self.feeder / "local").exists())

    def test_newest_wins_and_old_copy_backed_up(self) -> None:
        write_skill(self.vault, "s", "old", 1000)
        (self.vault / "s" / "stale.txt").write_text("gone", encoding="utf-8")
        os.utime(self.vault / "s" / "stale.txt", (1000, 1000))
        write_skill(self.claude, "s", "new", 2000)
        write_skill(self.codex, "s", "old", 1000)
        actions = self.sync()
        self.assertIn("new", (self.vault / "s" / "SKILL.md").read_text(encoding="utf-8"))
        self.assertFalse((self.vault / "s" / "stale.txt").exists())
        backups = [a["backup"] for a in actions if "backup" in a]
        self.assertEqual(len(backups), 2)
        self.assertTrue(all(Path(b).is_dir() for b in backups))
        self.assertEqual(sync_skills.verify_hubs(self.hubs), [])

    def test_tie_with_different_content_is_left_alone(self) -> None:
        write_skill(self.vault, "s", "one", 1000)
        write_skill(self.claude, "s", "two", 1000)
        actions = self.sync()
        self.assertEqual([a["status"] for a in actions], ["tie"])
        self.assertFalse((self.codex / "s").exists())

    def test_non_skill_folders_are_ignored(self) -> None:
        write_skill(self.claude, "cv-craft-workspace", "x", 1000)
        write_skill(self.claude, "synced", "x", 1000)
        write_skill(self.claude, "_archive", "x", 1000)
        (self.claude / "no-skill-md").mkdir()
        actions, _ = sync_skills.plan_sync(self.hubs, [])
        self.assertEqual(actions, [])

    def test_ds_store_does_not_cause_differences(self) -> None:
        write_skill(self.vault, "s", "same", 1000)
        write_skill(self.claude, "s", "same", 1000)
        write_skill(self.codex, "s", "same", 1000)
        (self.claude / "s" / ".DS_Store").write_bytes(b"junk")
        actions, _ = sync_skills.plan_sync(self.hubs, [])
        self.assertEqual(actions, [])


if __name__ == "__main__":
    unittest.main()
