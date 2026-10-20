"""Regression for Windows-generated v5 profiles.

No raster computation is required.
"""

import json
from pathlib import Path
import unittest
from csmap_sheets.engine.pipeline import (
    merge_settings_profile,
    settings_profile,
    validate_config,
    profile_nodata_edge_mode,
)
from csmap_sheets.tests.test_sigma_unit import base_config


class ProfileRoundtripTests(unittest.TestCase):
    def fixture(self):
        return json.loads(
            (
                Path(__file__).parent
                / "fixtures/profile_v5_public_reproducer.json"
            ).read_text()
        )

    def resolve(self, data, current=None):
        current = (
            base_config(nodata_edge_mode="pss_approximation")
            if current is None
            else current
        )
        merged, saved = merge_settings_profile(data, current)
        merged["nodata_edge_mode"], warning = profile_nodata_edge_mode(
            saved, current["nodata_edge_mode"]
        )
        if "sigma_unit" not in saved:
            merged["sigma_unit"] = "m"
        return validate_config(merged, Path.cwd()), warning

    def test_public_reproducer_roundtrip_both_modes(self):
        for mode in ("safe_mask", "pss_approximation"):
            with self.subTest(mode=mode):
                data = self.fixture()
                data["settings"]["nodata_edge_mode"] = mode
                first, warning = self.resolve(data)
                self.assertIsNone(warning)
                payload = settings_profile(first)
                second, warning = self.resolve(json.loads(json.dumps(payload)))
                self.assertEqual(payload, settings_profile(second))
                for key, value in data["settings"].items():
                    self.assertEqual(second[key], value, key)
                self.assertEqual(
                    payload["schema"], "csmap-settings-profile-v5"
                )
                self.assertFalse(
                    set(payload["settings"])
                    & {
                        "inputs",
                        "output_dir",
                        "target_crs",
                        "plane_zone",
                        "input_type",
                        "confirm_elevation_metres",
                    }
                )

    def test_merged_dem_and_edge_mode_roundtrip_together(self):
        # v0.12.4 added merged_dem_enabled; the PR #31 allowlist comes from
        # configuration_defaults(), so the new key must survive save/load.
        for merged_dem in (True, False):
            for mode in ("safe_mask", "pss_approximation"):
                with self.subTest(merged_dem=merged_dem, mode=mode):
                    data = self.fixture()
                    data["settings"].update(
                        merged_dem_enabled=merged_dem, nodata_edge_mode=mode
                    )
                    first, warning = self.resolve(data)
                    self.assertIsNone(warning)
                    payload = json.loads(json.dumps(settings_profile(first)))
                    self.assertIs(
                        payload["settings"]["merged_dem_enabled"], merged_dem
                    )
                    self.assertEqual(
                        payload["settings"]["nodata_edge_mode"], mode
                    )
                    second, _ = self.resolve(payload)
                    self.assertIs(second["merged_dem_enabled"], merged_dem)
                    self.assertEqual(second["nodata_edge_mode"], mode)
                    self.assertEqual(payload, settings_profile(second))

    def test_merged_dem_must_be_boolean(self):
        data = self.fixture()
        data["settings"]["merged_dem_enabled"] = "yes"
        with self.assertRaisesRegex(ValueError, "merged_dem_enabled"):
            self.resolve(data)

    def test_engine_only_nondefault_limits_survive(self):
        data = self.fixture()
        limits = dict(
            block_size=256,
            max_sheets=200,
            max_sheet_pixels=20000000,
            max_pixels=200000000,
            max_input_pixels=30000000,
            max_input_files=2000,
        )
        data["settings"].update(limits)
        result, _ = self.resolve(data)
        for key, value in limits.items():
            self.assertEqual(result[key], value)

    def test_invalid_limits_rejected(self):
        for key in (
            "block_size",
            "max_sheets",
            "max_sheet_pixels",
            "max_pixels",
            "max_input_pixels",
            "max_input_files",
        ):
            for value in (0, -1, True, 1.5, "512"):
                with self.subTest(key=key, value=value):
                    data = self.fixture()
                    data["settings"][key] = value
                    with self.assertRaises((ValueError, TypeError)):
                        self.resolve(data)
        data = self.fixture()
        data["settings"]["block_size"] = 4096
        with self.assertRaisesRegex(ValueError, "block_size"):
            self.resolve(data)

    def test_unknown_key_still_rejected(self):
        data = self.fixture()
        data["settings"]["typo_limit"] = 100
        with self.assertRaisesRegex(ValueError, "typo_limit"):
            self.resolve(data)

    def test_invalid_profile_shapes(self):
        for data in ([], None, {"settings": []}, {"settings": None}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                self.resolve(data)

    def test_protected_runtime_values_not_loaded(self):
        current = base_config(nodata_edge_mode="safe_mask")
        data = self.fixture()
        for key in (
            "inputs",
            "output_dir",
            "target_crs",
            "input_type",
            "plane_zone",
            "confirm_elevation_metres",
        ):
            data["settings"][key] = "must not load"
        result, _ = self.resolve(data, current)
        self.assertEqual(result["inputs"], current["inputs"])
        self.assertEqual(result["target_crs"], current["target_crs"])
        self.assertTrue(result["confirm_elevation_metres"])

    def test_v4_missing_mode_forces_safe_and_warns(self):
        data = self.fixture()
        data["schema"] = "csmap-settings-profile-v4"
        del data["settings"]["nodata_edge_mode"]
        result, warning = self.resolve(data)
        self.assertEqual(result["nodata_edge_mode"], "safe_mask")
        self.assertIn("nodata_edge_mode", warning)

    def test_old_bare_profile_metres(self):
        result, warning = self.resolve(
            {"sigma_m": 3},
            base_config(
                sigma_unit="px",
                sigma_px=5,
                nodata_edge_mode="pss_approximation",
            ),
        )
        self.assertEqual(
            (
                result["sigma_unit"],
                result["sigma_m"],
                result["nodata_edge_mode"],
            ),
            ("m", 3, "safe_mask"),
        )

    def test_invalid_mode_not_silently_accepted(self):
        data = self.fixture()
        data["settings"]["nodata_edge_mode"] = "typo"
        with self.assertRaisesRegex(ValueError, "nodata_edge_mode"):
            self.resolve(data)
