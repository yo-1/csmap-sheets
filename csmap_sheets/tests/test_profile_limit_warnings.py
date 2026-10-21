"""Profiles may raise processing limits; a larger value is reported, not rejected.

No raster computation or QGIS is required.
"""

import unittest

from csmap_sheets.engine.pipeline import (
    PROFILE_LIMIT_KEYS,
    configuration_defaults,
    profile_limit_warnings,
)


class ProfileLimitWarningTests(unittest.TestCase):
    def test_limit_keys_exist_in_defaults(self):
        defaults = configuration_defaults()
        for key in PROFILE_LIMIT_KEYS:
            self.assertIn(key, defaults)
            self.assertIs(type(defaults[key]), int)

    def test_no_warning_without_limit_keys(self):
        self.assertEqual(profile_limit_warnings({}), [])
        self.assertEqual(profile_limit_warnings({"cell_size": 1.0}), [])

    def test_no_warning_at_or_below_default(self):
        defaults = configuration_defaults()
        saved = {key: defaults[key] for key in PROFILE_LIMIT_KEYS}
        self.assertEqual(profile_limit_warnings(saved), [])
        saved = {key: 1 for key in PROFILE_LIMIT_KEYS}
        self.assertEqual(profile_limit_warnings(saved), [])

    def test_warning_names_each_raised_key(self):
        defaults = configuration_defaults()
        for key in PROFILE_LIMIT_KEYS:
            warnings = profile_limit_warnings({key: defaults[key] + 1})
            self.assertEqual(len(warnings), 1, key)
            self.assertIn(key, warnings[0])
            self.assertIn(f"{defaults[key] + 1:,}", warnings[0])

    def test_one_warning_per_raised_key(self):
        defaults = configuration_defaults()
        saved = {
            "max_pixels": defaults["max_pixels"] * 2,
            "max_sheets": defaults["max_sheets"] * 2,
            "max_input_files": 5,
        }
        self.assertEqual(len(profile_limit_warnings(saved)), 2)

    def test_non_integer_values_are_left_to_validation(self):
        saved = {
            "max_pixels": True,
            "max_sheets": "999999999999",
            "max_sheet_pixels": 1e18,
            "max_input_pixels": None,
        }
        self.assertEqual(profile_limit_warnings(saved), [])


if __name__ == "__main__":
    unittest.main()
