"""Fail on missing documentation and anchors, including main URLs."""
from pathlib import Path
import tempfile
import unittest
from tools.check_markdown_links import check, REPOSITORY


class MarkdownLinksTests(unittest.TestCase):
    def test_targets_and_missing_anchor(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            guide = root / "guide.md"
            guide.write_text("# 利用手順書\n", encoding="utf-8")
            index = root / "README.md"
            for target in (
                "guide.md#利用手順書",
                REPOSITORY + "blob/main/guide.md",
            ):
                index.write_text(f"[guide]({target})", encoding="utf-8")
                self.assertEqual(check([index], root), 1)
            index.write_text("[bad](guide.md#absent)", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing anchor"):
                check([index], root)
            guide.unlink()
            index.write_text(
                f"[bad]({REPOSITORY}blob/main/guide.md)", encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "missing target"):
                check([index], root)
