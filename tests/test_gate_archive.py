"""17-J paired archival: offline filesystem/CLI tests, never live project writes."""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_task_archive import TASK, PLACEHOLDER

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from task_archive import ArchiveError, archive_pair, archive_task, report_identity  # noqa: E402

REPORT = (
    "---\ntask_id: T-001\nrevision: 1\nstatus: completed\n"
    "branch: claude/T-001\ncommit: 123abcd\n---\n\n# Worker Report\n"
    "## 結果\n定義（全角）・空白  を保持。\n閾値: 0.95\n"
    "```text\n1\t2\tfile.txt\n```\n## 未解決事項\n無し\n"
).encode("utf-8")


class GateArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.task = self.root / "task.md"
        self.report = self.root / "report.md"
        self.archive = self.root / "archive"
        self.task.write_bytes(TASK)
        self.report.write_bytes(REPORT)

    def run_pair(self, **kwargs):
        return archive_pair(self.task, self.report, self.archive, **kwargs)

    def assert_windows_unchanged(self):
        self.assertEqual(self.task.read_bytes(), TASK)
        self.assertEqual(self.report.read_bytes(), REPORT)

    def test_pair_exact_bytes_and_hashes(self):
        task, report = self.run_pair()
        self.assertEqual(task.path.name, "T-001_task_r1.md")
        self.assertEqual(report.path.name, "T-001_report_r1.md")
        for result, raw in ((task, TASK), (report, REPORT)):
            self.assertTrue(result.created)
            self.assertEqual(result.path.read_bytes(), raw)
            self.assertEqual(result.sha256, hashlib.sha256(raw).hexdigest())
        self.assert_windows_unchanged()
        self.assertEqual(len(list(self.archive.iterdir())), 2)

    def test_report_newlines_preserved(self):
        for raw in (REPORT.replace(b"\n", b"\r\n"), REPORT.rstrip(b"\n")):
            with self.subTest(raw=raw[-5:]):
                self.report.write_bytes(raw)
                _, result = self.run_pair()
                self.assertEqual(result.path.read_bytes(), raw)
                self.assertEqual(self.report.read_bytes(), raw)
                result.path.unlink()

    def test_completed_blocked_failed_are_not_rewritten(self):
        for status in (b"completed", b"blocked", b"failed"):
            with self.subTest(status=status):
                raw = REPORT.replace(b"status: completed", b"status: " + status)
                self.report.write_bytes(raw)
                _, result = self.run_pair()
                self.assertEqual(result.path.read_bytes(), raw)
                result.path.unlink()

    def test_same_pair_is_idempotent(self):
        self.run_pair()
        self.assertEqual([r.created for r in self.run_pair()], [False, False])
        self.assert_windows_unchanged()

    def test_existing_task_only_can_be_completed(self):
        archive_task(self.task, self.archive)
        self.assertEqual([r.created for r in self.run_pair()], [False, True])

    def test_both_old_revisions_remain(self):
        first = self.run_pair()
        for source in (self.task, self.report):
            source.write_bytes(source.read_bytes().replace(b"revision: 1", b"revision: 2"))
        second = self.run_pair()
        self.assertEqual(first[0].path.read_bytes(), TASK)
        self.assertEqual(first[1].path.read_bytes(), REPORT)
        self.assertEqual([r.path.name for r in second], ["T-001_task_r2.md", "T-001_report_r2.md"])
        self.assertEqual(len(list(self.archive.iterdir())), 4)

    def test_missing_report_does_not_archive_task(self):
        self.report.unlink()
        with self.assertRaises(ArchiveError):
            self.run_pair()
        self.assertFalse(self.archive.exists())
        self.assertEqual(self.task.read_bytes(), TASK)

    def test_id_or_revision_mismatch_creates_nothing(self):
        for raw in (REPORT.replace(b"T-001", b"T-002"),
                    REPORT.replace(b"revision: 1", b"revision: 2")):
            self.report.write_bytes(raw)
            with self.subTest(raw=raw[:60]), self.assertRaises(ArchiveError):
                self.run_pair()
            self.assertFalse(self.archive.exists())
            self.assertEqual(self.task.read_bytes(), TASK)
            self.assertEqual(self.report.read_bytes(), raw)

    def test_placeholder_or_active_report_rejected(self):
        for raw in (PLACEHOLDER, REPORT.replace(b"status: completed", b"status: active")):
            self.report.write_bytes(raw)
            with self.subTest(raw=raw[:70]), self.assertRaises(ArchiveError):
                self.run_pair()
            self.assertFalse(self.archive.exists())

    def test_bad_frontmatter_or_body_rejected(self):
        invalid = [
            REPORT.replace(b"revision: 1", b"revision: 1\nrevision: 2"),
            REPORT.replace(b"task_id: T-001", b"task_id: ../escape"),
            REPORT.replace(b"branch: claude/T-001", b"branch: claude/T-999"),
            REPORT.replace(b"commit: 123abcd", b"commit: HEAD"),
            REPORT.replace(b"commit: 123abcd\n", b""),
            REPORT.replace(b"revision: 1", b"revision: 01"),
            REPORT.split(b"# Worker Report")[0], b"# No frontmatter",
            b"\xef\xbb\xbf" + REPORT, REPORT + b"\x00", REPORT + b"\xff",
        ]
        for raw in invalid:
            with self.subTest(raw=raw[:80]), self.assertRaises(ArchiveError):
                report_identity(raw)

    def test_independent_hashes(self):
        result = self.run_pair(expected_task_sha256=hashlib.sha256(TASK).hexdigest().upper(),
                               expected_report_sha256=hashlib.sha256(REPORT).hexdigest().upper())
        self.assertEqual(result[1].sha256, hashlib.sha256(REPORT).hexdigest())

    def test_bad_hash_preflight_creates_nothing(self):
        for key in ("expected_task_sha256", "expected_report_sha256"):
            for value in ("0" * 64, "invalid"):
                with self.subTest(key=key, value=value), self.assertRaises(ArchiveError):
                    self.run_pair(**{key: value})
                self.assertFalse(self.archive.exists())
                self.assert_windows_unchanged()

    def test_either_conflict_prevents_other_archive(self):
        self.archive.mkdir()
        for kind in ("task", "report"):
            target = self.archive / ("T-001_" + kind + "_r1.md")
            target.write_bytes(b"a conflicting original")
            with self.subTest(kind=kind), self.assertRaises(ArchiveError):
                self.run_pair()
            self.assertEqual(list(self.archive.iterdir()), [target])
            self.assertEqual(target.read_bytes(), b"a conflicting original")
            self.assert_windows_unchanged()
            target.unlink()

    def test_report_symlink_source_rejected(self):
        original = self.root / "original.md"
        self.report.rename(original)
        try:
            self.report.symlink_to(original)
        except OSError:
            self.skipTest("Symlinks unavailable")
        with self.assertRaises(ArchiveError):
            self.run_pair()
        self.assertFalse(self.archive.exists())

    def test_report_symlink_target_preflight_rejected(self):
        self.archive.mkdir()
        link = self.archive / "T-001_report_r1.md"
        try:
            link.symlink_to(self.report)
        except OSError:
            self.skipTest("Symlinks unavailable")
        with self.assertRaises(ArchiveError):
            self.run_pair()
        self.assertFalse((self.archive / "T-001_task_r1.md").exists())
        self.assert_windows_unchanged()

    def test_second_publication_failure_keeps_windows_and_is_retryable(self):
        original_link = os.link
        count = 0

        def link_once(source, target):
            nonlocal count
            count += 1
            if count == 2:
                raise OSError("simulated report write failure")
            return original_link(source, target)

        with patch("task_archive.os.link", side_effect=link_once):
            with self.assertRaises(OSError):
                self.run_pair()
        self.assert_windows_unchanged()
        self.assertEqual([p.name for p in self.archive.iterdir()], ["T-001_task_r1.md"])
        self.assertEqual([r.created for r in self.run_pair()], [False, True])

    def test_report_changes_after_task_publication_stops(self):
        original_link = os.link
        changed = REPORT + b"Unexpected appended text\n"

        def change_report(source, target):
            original_link(source, target)
            self.report.write_bytes(changed)

        with patch("task_archive.os.link", side_effect=change_report):
            with self.assertRaises(ArchiveError):
                self.run_pair()
        self.assertEqual(self.task.read_bytes(), TASK)
        self.assertEqual(self.report.read_bytes(), changed)
        self.assertFalse((self.archive / "T-001_report_r1.md").exists())

    def test_task_changes_during_report_publication_stops(self):
        original_link = os.link
        changed = TASK + b"Unexpected appended text\n"

        def change_task(source, target):
            original_link(source, target)
            if str(target).endswith("_report_r1.md"):
                self.task.write_bytes(changed)

        with patch("task_archive.os.link", side_effect=change_task):
            with self.assertRaises(ArchiveError):
                self.run_pair()
        self.assertEqual(self.task.read_bytes(), changed)
        self.assertEqual(self.report.read_bytes(), REPORT)

    def test_cli_pair_returns_both_raw_hashes(self):
        run = subprocess.run([sys.executable, str(ROOT / "scripts/task_archive.py"),
                              "--task", str(self.task), "--report", str(self.report),
                              "--archive-dir", str(self.archive)],
                             check=True, capture_output=True, text=True)
        data = json.loads(run.stdout)
        self.assertEqual(set(data), {"task", "report"})
        self.assertEqual(data["report"]["sha256"], hashlib.sha256(REPORT).hexdigest())
        self.assert_windows_unchanged()

    def test_cli_mismatch_is_nonzero_no_success_record(self):
        self.report.write_bytes(REPORT.replace(b"revision: 1", b"revision: 2"))
        run = subprocess.run([sys.executable, str(ROOT / "scripts/task_archive.py"),
                              "--task", str(self.task), "--report", str(self.report),
                              "--archive-dir", str(self.archive)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 1)
        self.assertEqual(run.stdout, "")
        self.assertFalse(self.archive.exists())

    def test_cli_report_hash_requires_report_argument(self):
        run = subprocess.run([sys.executable, str(ROOT / "scripts/task_archive.py"),
                              "--expected-report-sha256", "0" * 64], cwd=self.root,
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)
        self.assertFalse((self.root / ".ai").exists())


if __name__ == "__main__":
    unittest.main()
