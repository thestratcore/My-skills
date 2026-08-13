#!/usr/bin/env python3
"""Deterministic tests for sync_skills.py Git and health-check behavior."""

from __future__ import annotations

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


if __name__ == "__main__":
    unittest.main()
