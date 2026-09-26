"""Check the updated document surface and unchanged Git wire key sets."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DocumentTests(unittest.TestCase):
    def test_local_markdown_links_resolve(self):
        paths = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md")),
                 *sorted((ROOT / ".claude/skills/tai").rglob("*.md"))]
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
                if "://" in target or target.startswith("#"):
                    continue
                relative = target.split("#", 1)[0]
                with self.subTest(path=str(path.relative_to(ROOT)), target=target):
                    self.assertTrue((path.parent / relative).exists(), target)

    def test_git_task_frontmatter_stays_compatible(self):
        path = ROOT / ".claude/skills/tai/templates/task.md"
        header = path.read_text(encoding="utf-8").split("---")[1]
        fields = dict(line.split(":", 1) for line in header.strip().splitlines())
        self.assertEqual(set(fields), {"task_id", "revision", "status", "commit", "push", "model"})
        self.assertEqual(fields["status"].strip(), "active")
        self.assertEqual(fields["model"].strip(), "sonnet")

    def test_git_report_frontmatter_stays_compatible(self):
        path = ROOT / ".claude/skills/tai/templates/report.md"
        header = path.read_text(encoding="utf-8").split("---")[1]
        fields = dict(line.split(":", 1) for line in header.strip().splitlines())
        self.assertEqual(set(fields), {"task_id", "revision", "status", "branch", "commit"})

    def test_version_is_presented_as_candidate(self):
        version = (ROOT / "VERSION").read_text().strip()
        self.assertEqual(version, "0.2.0-rc.1")
        self.assertIn(version, (ROOT / "README.md").read_text(encoding="utf-8"))
        self.assertIn(version, (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
