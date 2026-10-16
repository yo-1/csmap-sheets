"""Regression coverage for the final settings filename."""
import unittest
from csmap_sheets.profile_paths import json_path


class ProfilePathTests(unittest.TestCase):
    def test_json_suffix_and_empty_optional_value(self):
        for raw, expected in (
            ("", ""), ("  ", ""), ("settings", "settings.json"),
            ("settings.json", "settings.json"),
            ("settings.JSON", "settings.JSON"),
            ("settings.txt", "settings.txt.json"),
            (r"C:\試験\設定", r"C:\試験\設定.json"),
        ):
            with self.subTest(raw=raw):
                self.assertEqual(json_path(raw), expected)
