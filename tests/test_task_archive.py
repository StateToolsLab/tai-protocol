"""Offline unit tests; no external models, credentials, or network calls."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from task_archive import ArchiveError, archive_pair, archive_task, task_identity  # noqa: E402

TASK = (
    "---\ntask_id: T-001\nrevision: 1\nstatus: active\n"
    "commit: auto\npush: confirm\nmodel: sonnet\n---\n\n"
    "# Task\n定義（全角）を変更しない。\n閾値: 0.95\n"
).encode("utf-8")
REPORT = b"---\ntask_id: T-001\nrevision: 1\nstatus: completed\nbranch: claude/T-001\ncommit: 123abcd\n---\n# Completed report\n"
PLACEHOLDER = b"---\ntask_id: none\nrevision: 0\nstatus: none\n---\n"


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "task.md"
        self.archive = self.root / "archive"
        self.source.write_bytes(TASK)

    def test_exact_bytes_and_source_preserved(self):
        result = archive_task(self.source, self.archive)
        self.assertTrue(result.created)
        self.assertEqual(result.path.name, "T-001_task_r1.md")
        self.assertEqual(result.path.read_bytes(), TASK)
        self.assertEqual(self.source.read_bytes(), TASK)
        self.assertEqual(result.sha256, hashlib.sha256(TASK).hexdigest())
        self.assertEqual(len(list(self.archive.iterdir())), 1)

    def test_crlf_preserved(self):
        raw = TASK.replace(b"\n", b"\r\n")
        self.source.write_bytes(raw)
        self.assertEqual(archive_task(self.source, self.archive).path.read_bytes(), raw)

    def test_missing_final_newline_preserved(self):
        raw = TASK.rstrip(b"\n")
        self.source.write_bytes(raw)
        self.assertEqual(archive_task(self.source, self.archive).path.read_bytes(), raw)

    def test_repeat_identical_is_idempotent(self):
        archive_task(self.source, self.archive)
        self.assertFalse(archive_task(self.source, self.archive).created)

    def test_conflict_never_overwrites(self):
        first = archive_task(self.source, self.archive)
        changed = TASK.replace(b"0.95", b"0.90")
        self.source.write_bytes(changed)
        with self.assertRaises(ArchiveError):
            archive_task(self.source, self.archive)
        self.assertEqual(first.path.read_bytes(), TASK)
        self.assertEqual(self.source.read_bytes(), changed)

    def test_next_revision_keeps_previous(self):
        first = archive_task(self.source, self.archive)
        self.source.write_bytes(TASK.replace(b"revision: 1", b"revision: 2"))
        second = archive_task(self.source, self.archive)
        self.assertEqual(first.path.read_bytes(), TASK)
        self.assertEqual(second.path.name, "T-001_task_r2.md")

    def test_trusted_hash(self):
        digest = hashlib.sha256(TASK).hexdigest()
        self.assertEqual(archive_task(self.source, self.archive, digest.upper()).sha256, digest)

    def test_wrong_hash_has_no_archive_side_effect(self):
        with self.assertRaises(ArchiveError):
            archive_task(self.source, self.archive, "0" * 64)
        self.assertFalse(self.archive.exists())

    def test_malformed_hash(self):
        with self.assertRaises(ArchiveError):
            archive_task(self.source, self.archive, "not-a-hash")

    def test_placeholder_rejected(self):
        self.source.write_bytes(PLACEHOLDER)
        with self.assertRaises(ArchiveError):
            archive_task(self.source, self.archive)
        self.assertFalse(self.archive.exists())

    def test_non_active_rejected(self):
        with self.assertRaises(ArchiveError):
            task_identity(TASK.replace(b"status: active", b"status: completed"))

    def test_unsafe_id_rejected(self):
        for value in (b"../escape", b"T-001/../../escape", b"T-NNN", b"T-01"):
            with self.subTest(value=value), self.assertRaises(ArchiveError):
                task_identity(TASK.replace(b"T-001", value))

    def test_invalid_revisions_rejected(self):
        for value in (b"0", b"-1", b"1.0", b"01", b"one"):
            with self.subTest(value=value), self.assertRaises(ArchiveError):
                task_identity(TASK.replace(b"revision: 1", b"revision: " + value))

    def test_duplicate_key_rejected(self):
        with self.assertRaises(ArchiveError):
            task_identity(TASK.replace(b"revision: 1", b"revision: 1\nrevision: 2"))

    def test_missing_frontmatter_or_body_rejected(self):
        for raw in (b"# Task", b"---\ntask_id: T-001", TASK.split(b"# Task")[0]):
            with self.subTest(raw=raw), self.assertRaises(ArchiveError):
                task_identity(raw)

    def test_invalid_encoding_rejected(self):
        for raw in (b"\xef\xbb\xbf" + TASK, TASK + b"\xff", TASK + b"\x00"):
            with self.subTest(raw=raw[-8:]), self.assertRaises(ArchiveError):
                task_identity(raw)

    def test_comments_preserved_not_evaluated(self):
        raw = TASK.replace(b"model: sonnet", b"model: sonnet  # historical annotation")
        self.source.write_bytes(raw)
        self.assertEqual(archive_task(self.source, self.archive).path.read_bytes(), raw)

    def test_symlink_source_rejected(self):
        link = self.root / "link.md"
        try:
            link.symlink_to(self.source)
        except OSError:
            self.skipTest("Symlinks unavailable")
        with self.assertRaises(ArchiveError):
            archive_task(link, self.archive)

    def test_symlink_destination_rejected(self):
        self.archive.mkdir()
        target = self.archive / "T-001_task_r1.md"
        try:
            target.symlink_to(self.source)
        except OSError:
            self.skipTest("Symlinks unavailable")
        with self.assertRaises(ArchiveError):
            archive_task(self.source, self.archive)
        self.assertEqual(self.source.read_bytes(), TASK)

    def test_symlink_archive_directory_rejected(self):
        other = self.root / "other"
        other.mkdir()
        try:
            self.archive.symlink_to(other, target_is_directory=True)
        except OSError:
            self.skipTest("Symlinks unavailable")
        with self.assertRaises(ArchiveError):
            archive_task(self.source, self.archive)
        self.assertEqual(list(other.iterdir()), [])

    def test_sync_failure_cleans_temporary_file(self):
        with patch("task_archive.os.fsync", side_effect=OSError("write failure")):
            with self.assertRaises(OSError):
                archive_task(self.source, self.archive)
        self.assertEqual(list(self.archive.iterdir()), [])
        self.assertEqual(self.source.read_bytes(), TASK)

    def test_link_failure_cleans_temporary_file(self):
        with patch("task_archive.os.link", side_effect=OSError("unsupported filesystem")):
            with self.assertRaises(OSError):
                archive_task(self.source, self.archive)
        self.assertEqual(list(self.archive.iterdir()), [])
        self.assertEqual(self.source.read_bytes(), TASK)

    def test_concurrent_conflict_not_overwritten(self):
        target = self.archive / "T-001_task_r1.md"
        other = b"a concurrent different document"

        def conflict(_source, _target):
            target.write_bytes(other)
            raise FileExistsError()

        with patch("task_archive.os.link", side_effect=conflict):
            with self.assertRaises(ArchiveError):
                archive_task(self.source, self.archive)
        self.assertEqual(target.read_bytes(), other)
        self.assertEqual(len(list(self.archive.iterdir())), 1)

    def test_cli_success(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/task_archive.py"), "--task", str(self.source),
             "--archive-dir", str(self.archive)], capture_output=True, text=True, check=True,
        )
        self.assertTrue(json.loads(result.stdout)["created"])

    def test_cli_missing_source_fails(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/task_archive.py"), "--task", str(self.root / "missing.md")],
            cwd=self.root, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("tai archive:", result.stderr)
        self.assertFalse((self.root / ".ai").exists())


@unittest.skipUnless(shutil.which("git"), "Git is required for the local integration test")
class GitCleanupTests(unittest.TestCase):
    def test_crlf_archive_survives_git_text_conversion(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            env = dict(os.environ)
            env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull})

            def git(*args):
                return subprocess.run(["git", *args], cwd=root, env=env, check=True, capture_output=True).stdout

            git("init", "-q")
            git("config", "core.autocrlf", "true")
            (root / ".gitattributes").write_bytes((ROOT / ".gitattributes").read_bytes())
            source = root / "task.md"
            raw = TASK.replace(b"\n", b"\r\n")
            source.write_bytes(raw)
            report = root / "report.md"
            report_raw = REPORT.replace(b"\n", b"\r\n")
            report.write_bytes(report_raw)
            archive_pair(source, report, root / ".ai/archive")
            git("add", ".gitattributes", ".ai/archive")
            self.assertEqual(git("show", ":.ai/archive/T-001_task_r1.md"), raw)
            self.assertEqual(git("show", ":.ai/archive/T-001_report_r1.md"), report_raw)

    def test_archive_and_reset_are_in_same_commit(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            env = dict(os.environ)
            env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
                        "GIT_AUTHOR_NAME": "TAI Test", "GIT_AUTHOR_EMAIL": "test@example.invalid",
                        "GIT_COMMITTER_NAME": "TAI Test", "GIT_COMMITTER_EMAIL": "test@example.invalid"})

            def git(*args):
                return subprocess.run(["git", *args], cwd=root, env=env, check=True, capture_output=True).stdout

            git("init", "-q")
            ai = root / ".ai"
            ai.mkdir()
            source = ai / "task.md"
            source.write_bytes(TASK)
            report = ai / "report.md"
            report.write_bytes(REPORT)
            git("add", ".ai")
            git("commit", "-qm", "issued task and returned report")
            report_ref = git("rev-parse", "HEAD").decode().strip()
            archived, archived_report = archive_pair(source, report, ai / "archive")
            source.write_bytes(PLACEHOLDER)
            report.write_bytes(PLACEHOLDER)
            git("add", ".ai")
            git("commit", "-qm", "archive Task and Report and reset both windows")
            changed = set(git("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").decode().splitlines())
            self.assertEqual(changed, {".ai/archive/T-001_task_r1.md", ".ai/archive/T-001_report_r1.md",
                                       ".ai/task.md", ".ai/report.md"})
            self.assertEqual(git("show", "HEAD:.ai/archive/" + archived.path.name), TASK)
            self.assertEqual(git("show", "HEAD:.ai/archive/" + archived_report.path.name), REPORT)
            self.assertEqual(git("show", "HEAD:.ai/task.md"), PLACEHOLDER)
            self.assertEqual(git("show", "HEAD:.ai/report.md"), PLACEHOLDER)
            self.assertIn(b"Completed report", git("show", report_ref + ":.ai/report.md"))


if __name__ == "__main__":
    unittest.main()
