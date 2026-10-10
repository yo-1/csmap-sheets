import unittest
import hashlib
import numpy as np
from csmap_sheets.engine.pipeline import (
    relief,
    color_settings,
    rendering_settings,
    slope_gradients,
)
from csmap_sheets.engine.color_fme import (
    FME_COLORS,
    FME_WEIGHTS,
    apply_stretch,
    lut2,
    lut3,
    normalise_index,
    render_fme,
    rendering_record,
    validate_fme_settings,
)


class ColorTests(unittest.TestCase):
    def render(self, tone, a=None):
        if a is None:
            y, x = np.mgrid[:81, :81]
            a = 500 + 5 * np.sin(x / 6) + 3 * np.cos(y / 9)
        return relief(a, np.isfinite(a), 1, 2, 0.05, 60, [0, 3000], tone)

    def test_only_colours_change(self):
        base, slope, curvature = self.render({})
        edited, s2, c2 = self.render(
            dict(saturation=0.3, gamma=1.2, slope_darkness=0.2)
        )
        np.testing.assert_array_equal(slope, s2)
        np.testing.assert_array_equal(curvature, c2)
        np.testing.assert_array_equal(base[:, :, 3], edited[:, :, 3])
        self.assertFalse(np.array_equal(base[:, :, :3], edited[:, :, :3]))

    def test_grayscale_and_transparency(self):
        a = np.full((81, 81), 100.0)
        a[40, 40] = np.nan
        img, _, _ = self.render(dict(saturation=0, brightness=2, gamma=1.5), a)
        np.testing.assert_array_equal(img[:, :, 0], img[:, :, 1])
        np.testing.assert_array_equal(img[:, :, 1], img[:, :, 2])
        self.assertFalse(img[40, 40].any())

    def test_custom_palette(self):
        img, _, _ = self.render(
            dict(
                neutral_rgb=[40, 80, 120],
                curvature_strength=0,
                elevation_mix=0,
                slope_darkness=0,
            )
        )
        np.testing.assert_array_equal(img[40, 40], [40, 80, 120, 255])

    def test_middle_colour_is_an_independent_stop(self):
        tone = dict(
            valley_rgb=[0, 0, 255],
            neutral_rgb=[255, 255, 0],
            ridge_rgb=[255, 0, 0],
            curvature_strength=1,
            elevation_mix=0,
            slope_darkness=0,
        )
        flat = np.full((81, 81), 500.0)
        img, _, curvature = self.render(tone, flat)
        self.assertAlmostEqual(float(curvature[40, 40]), 0.0)
        np.testing.assert_array_equal(img[40, 40], [255, 255, 0, 255])

    def test_fme_middle_colour_changes_flat_curvature_output(self):
        flat = np.full((81, 81), 500.0)
        base = relief(
            flat,
            np.isfinite(flat),
            1,
            2,
            0.1,
            60,
            [200, 2000],
            {},
            "fme_manual",
        )[0]
        edited = relief(
            flat,
            np.isfinite(flat),
            1,
            2,
            0.1,
            60,
            [200, 2000],
            {},
            "fme_manual",
            {"colors": {"curvature_b_mid": [0, 255, 0]}},
        )[0]
        self.assertFalse(np.array_equal(base[40, 40, :3], edited[40, 40, :3]))
        np.testing.assert_array_equal(base[:, :, 3], edited[:, :, 3])

    def test_independent_v040_regression_hash(self):
        y, x = np.mgrid[:97, :103]
        a = (
            500
            + 5 * np.sin(x / 6)
            + 3 * np.cos(y / 9)
            + 0.001 * (x - 51) ** 2
            - 0.002 * (y - 48) ** 2
        )
        valid = np.isfinite(a)
        valid[20, 30] = False
        a[20, 30] = np.nan
        # v0.10.0: slope_algorithm defaults changed to 'horn'; pin this
        # historical
        # regression lock-in to the pre-v0.10.0 'central_difference' behaviour
        # explicitly so the hash below (computed before slope_algorithm
        # existed)
        # keeps meaning unchanged (central-difference backward compatibility).
        rgba = relief(
            a,
            valid,
            1,
            2,
            0.05,
            60,
            [0, 3000],
            None,
            "independent_v040",
            None,
            "central_difference",
        )[0]
        self.assertEqual(
            hashlib.sha256(rgba.tobytes()).hexdigest(),
            # Fixed image checksum, not an authentication secret.
            "32448c448f375a16ac6a29321204af8540"  # pragma: allowlist secret
            "fd86e5f9ae566b985004e96199227b",  # pragma: allowlist secret
        )

    def test_brightness_direction(self):
        base, _, _ = self.render({})
        dark, _, _ = self.render(dict(brightness=0.7))
        light, _, _ = self.render(dict(gamma=1.4))
        self.assertTrue(np.all(dark[40, 40, :3] < base[40, 40, :3]))
        self.assertTrue(np.all(light[40, 40, :3] > base[40, 40, :3]))

    def test_validation(self):
        for invalid in (
            {"valley_rgb": [256, 0, 0]},
            {"ridge_rgb": [0, 1]},
            {"brightness": float("nan")},
            {"gamma": 0},
            {"slope_darkness": 1.1},
            {"saturation": -1},
            {"typo": 1},
        ):
            with self.assertRaises(ValueError):
                color_settings(invalid)


class FMEColorTests(unittest.TestCase):
    def test_two_colour_lut_endpoints(self):
        for low, high in [
            ("elevation_low", "elevation_high"),
            ("slope_a_low", "slope_a_high"),
            ("slope_b_low", "slope_b_high"),
            ("curvature_a_low", "curvature_a_high"),
        ]:
            table = lut2(FME_COLORS[low], FME_COLORS[high])
            np.testing.assert_array_equal(table[0], FME_COLORS[low])
            np.testing.assert_array_equal(table[255], FME_COLORS[high])

    def test_curvature_b_endpoints_and_double_middle(self):
        table = lut3(
            FME_COLORS["curvature_b_low"],
            FME_COLORS["curvature_b_mid"],
            FME_COLORS["curvature_b_high"],
        )
        np.testing.assert_array_equal(table[0], [50, 96, 207])
        np.testing.assert_array_equal(table[127], [255, 254, 190])
        np.testing.assert_array_equal(table[128], [255, 254, 190])
        np.testing.assert_array_equal(table[255], [198, 72, 59])

    def test_normalisation_clips_and_curvature_sign(self):
        np.testing.assert_array_equal(
            normalise_index([-2, -0.1, 0, 0.1, 2], -0.1, 0.1),
            [0, 0, 128, 255, 255],
        )
        table = lut3(
            FME_COLORS["curvature_b_low"],
            FME_COLORS["curvature_b_mid"],
            FME_COLORS["curvature_b_high"],
        )
        self.assertGreater(table[0, 2], table[0, 0])
        self.assertGreater(table[255, 0], table[255, 2])

    def test_weights_and_hand_calculated_composite(self):
        self.assertAlmostEqual(sum(FME_WEIGHTS.values()), 1.0)
        rgb = render_fme(
            np.array([[200.0]]),
            np.array([[0.0]]),
            np.array([[-0.1]]),
            [200, 2000],
            [0, 60],
            [-0.1, 0.1],
        )
        expected = (
            np.array([36, 36, 36]) * 0.125
            + np.array([247, 213, 213]) * 0.25
            + np.array([246, 246, 246]) * 0.25
            + np.array([42, 95, 131]) * 0.125
            + np.array([50, 96, 207]) * 0.25
        )
        np.testing.assert_allclose(rgb[0, 0], expected, rtol=0, atol=1e-12)

    def test_stretch_bounds_and_validation(self):
        values = np.array([[[65.0, 57.0, 66.0], [234.0, 229.0, 216.0]]])
        stretched = apply_stretch(
            values, "custom", [[65, 234], [57, 229], [66, 216]]
        )
        np.testing.assert_array_equal(stretched[0, 0], [0, 0, 0])
        np.testing.assert_array_equal(stretched[0, 1], [255, 255, 255])
        for invalid in (
            {"stretch_mode": "bad"},
            {
                "stretch_mode": "custom",
                "stretch_ranges": [[1, 1], [0, 1], [0, 1]],
            },
            {"weights": {"elevation": 0.2}},
            {"colors": {"curvature_b_mid": [256, 0, 0]}},
        ):
            with self.assertRaises(ValueError):
                validate_fme_settings(invalid)

    def test_rendering_record_is_reproducible(self):
        record = rendering_record(
            [200, 2000],
            [0, 60],
            [-0.1, 0.1],
            {"stretch_mode": "nagano_reference"},
        )
        self.assertEqual(record["mode_id"], "fme_manual")
        self.assertEqual(record["colors"]["curvature_b_mid"], [255, 254, 190])
        self.assertEqual(
            record["stretch"]["ranges_rgb"],
            [[65.0, 234.0], [57.0, 229.0], [66.0, 216.0]],
        )

    def test_pipeline_manifest_record_contains_complete_fme_spec(self):
        record = rendering_settings(
            dict(
                render_mode="fme_manual",
                elevation_range=[200, 2000],
                slope_max=60,
                curvature_limit=0.1,
                sigma_m=3,
                input_type="forest",
                fme=validate_fme_settings({"stretch_mode": "none"}),
            )
        )
        self.assertEqual(record["mode_id"], "fme_manual")
        self.assertEqual(len(record["colors"]), 11)
        self.assertEqual(len(record["weights"]), 5)
        self.assertEqual(record["terrain_calculation"]["input_type"], "forest")
        # v0.10.0: slope_algorithmがconfigに無い場合は既定のHorn法として記録される
        # (関数外でvalidate_config()が常に補うため、通常は到達しない経路だが、
        # rendering_settings()自体のデフォルト処理を直接検証する)。
        self.assertEqual(
            record["terrain_calculation"]["slope_algorithm"], "horn"
        )

    def test_pipeline_manifest_record_reflects_chosen_slope_algorithm(self):
        for algorithm, expected_fragment in (
            ("horn", "Horn"),
            ("central_difference", "central differences"),
        ):
            record = rendering_settings(
                dict(
                    render_mode="independent_v040",
                    elevation_range=[0, 3000],
                    slope_max=60,
                    curvature_limit=0.05,
                    sigma_m=3,
                    color={},
                    slope_algorithm=algorithm,
                )
            )
            self.assertEqual(
                record["terrain_calculation"]["slope_algorithm"], algorithm
            )
            self.assertIn(
                expected_fragment, record["terrain_calculation"]["slope"]
            )


class SlopeAlgorithmTests(unittest.TestCase):
    """v0.10.0: 傾斜計算アルゴリズムの選択（ユーザー決定、2026-10-02）。既定値はHorn法。
    中央差分法(v0.9.4以前の既定)は明示指定時のみ使う。"""

    def test_relief_default_matches_explicit_horn(self):
        y, x = np.mgrid[:41, :41]
        a = 500 + 5 * np.sin(x / 6) + 3 * np.cos(y / 9)
        valid = np.isfinite(a)
        default_rgba, default_slope, _ = relief(
            a, valid, 1, 2, 0.05, 60, [0, 3000], None, "independent_v040"
        )
        horn_rgba, horn_slope, _ = relief(
            a,
            valid,
            1,
            2,
            0.05,
            60,
            [0, 3000],
            None,
            "independent_v040",
            None,
            "horn",
        )
        np.testing.assert_array_equal(default_rgba, horn_rgba)
        np.testing.assert_array_equal(default_slope, horn_slope)

    def test_invalid_slope_algorithm_raises_in_slope_gradients_and_relief(
        self,
    ):
        with self.assertRaisesRegex(
            ValueError, "slope_algorithm must be one of"
        ):
            slope_gradients(np.zeros((5, 5)), 1.0, "bogus")
        a = np.full((21, 21), 100.0)
        with self.assertRaisesRegex(
            ValueError, "slope_algorithm must be one of"
        ):
            relief(
                a,
                np.isfinite(a),
                1,
                2,
                0.05,
                60,
                [0, 3000],
                None,
                "independent_v040",
                None,
                "bogus",
            )

    def test_planar_surface_gives_identical_slope_for_both_algorithms(self):
        # Both methods are exact (zero error) on a perfectly planar surface, so
        # they
        # must agree away from the array-wrap edges, regardless of the tilt
        # direction.
        cell = 2.0
        yy, xx = np.mgrid[:21, :21].astype(float)
        plane = 100 + 0.3 * xx * cell - 0.2 * yy * cell
        dx_cd, dy_cd = slope_gradients(plane, cell, "central_difference")
        dx_h, dy_h = slope_gradients(plane, cell, "horn")
        interior = np.s_[2:-2, 2:-2]
        np.testing.assert_allclose(dx_cd[interior], dx_h[interior], atol=1e-9)
        np.testing.assert_allclose(dy_cd[interior], dy_h[interior], atol=1e-9)
        expected_dx, expected_dy = 0.3, -0.2
        np.testing.assert_allclose(dx_h[10, 10], expected_dx, atol=1e-9)
        np.testing.assert_allclose(dy_h[10, 10], expected_dy, atol=1e-9)

    def test_horn_reduces_spike_sensitivity(
        self,
    ):
        # Horn(1981)'s 3x3 weighting averages in the two neighbouring
        # rows/columns
        # untouched by a single-cell spike, so the resulting gradient at a cell
        # adjacent to the spike is damped relative to the simple 2-point method
        # (which only looks at the one row/column containing the spike). This
        # is
        # the concrete form of "Horn法は1セルノイズに頑健" in README_ja.md/CHANGELOG.md.
        cell = 1.0
        z = np.full((15, 15), 100.0)
        z[7, 8] += 50.0  # single-cell spike, one cell east of (7,7)
        dx_cd, _ = slope_gradients(z, cell, "central_difference")
        dx_h, _ = slope_gradients(z, cell, "horn")
        self.assertAlmostEqual(float(dx_cd[7, 7]), 25.0)
        self.assertAlmostEqual(float(dx_h[7, 7]), 12.5)
        self.assertLess(abs(dx_h[7, 7]), abs(dx_cd[7, 7]))

    def test_constant_surface_gives_zero_slope_for_both_algorithms(self):
        z = np.full((9, 9), 123.4)
        for algorithm in ("horn", "central_difference"):
            dx, dy = slope_gradients(z, 2.0, algorithm)
            np.testing.assert_allclose(
                np.degrees(np.arctan(np.hypot(dx, dy))), 0.0, atol=1e-12
            )

    def test_planar_slope_matches_analytic_angle(self):
        yy, xx = np.mgrid[:11, :11].astype(float)
        cell = 0.5
        gx, gy = 0.7, -0.4
        plane = 50 + gx * xx * cell + gy * yy * cell
        expected = np.degrees(np.arctan(np.hypot(gx, gy)))
        for algorithm in ("horn", "central_difference"):
            dx, dy = slope_gradients(plane, cell, algorithm)
            self.assertAlmostEqual(
                float(np.degrees(np.arctan(np.hypot(dx, dy)))[5, 5]),
                expected,
                places=9,
            )

    def test_horn_matches_hand_calculation_on_nonlinear_3x3(self):
        # z1..z9 row-major (north row first):
        #   1 2 4 / 3 5 8 / 6 9 13
        # dz/dx=((4+2*8+13)-(1+2*3+6))/8=2.5,
        # dz/dy=((6+2*9+13)-(1+2*2+4))/8=3.5
        z = np.array([[1, 2, 4], [3, 5, 8], [6, 9, 13]], dtype=float)
        dx, dy = slope_gradients(z, 1.0, "horn")
        self.assertAlmostEqual(abs(float(dx[1, 1])), 2.5)
        self.assertAlmostEqual(abs(float(dy[1, 1])), 3.5)
        self.assertAlmostEqual(
            float(np.degrees(np.arctan(np.hypot(dx[1, 1], dy[1, 1])))),
            float(np.degrees(np.arctan(np.hypot(2.5, 3.5)))),
        )

    def test_central_difference_reproduces_pre_v0_10_formula(self):
        rng = np.random.default_rng(7)
        z = rng.normal(300, 20, (17, 19))
        cell = 1.5
        dx, dy = slope_gradients(z, cell, "central_difference")
        np.testing.assert_array_equal(
            dx, (np.roll(z, -1, 1) - np.roll(z, 1, 1)) / (2 * cell)
        )
        np.testing.assert_array_equal(
            dy, (np.roll(z, -1, 0) - np.roll(z, 1, 0)) / (2 * cell)
        )

    def test_horn_nodata_neighbourhood_and_edges_are_transparent(self):
        # sigma=0 gives the smallest support (halo=1, 3x3), i.e. exactly Horn's
        # window.
        y, x = np.mgrid[:21, :21]
        a = (200 + 3 * np.sin(x / 3) + 2 * np.cos(y / 4)).astype(float)
        valid = np.ones(a.shape, bool)
        valid[10, 10] = False
        a[10, 10] = np.nan
        rgba, _, _ = relief(
            a,
            valid,
            1,
            0,
            0.05,
            60,
            [0, 3000],
            None,
            "independent_v040",
            None,
            "horn",
        )
        alpha = rgba[:, :, 3]
        for r, c in ((9, 9), (9, 11), (11, 9), (11, 11), (10, 9), (9, 10)):
            self.assertEqual(alpha[r, c], 0, (r, c))
        self.assertGreater(alpha[10, 12], 0)
        self.assertGreater(alpha[12, 12], 0)
        self.assertTrue((alpha[0, :] == 0).all() and (alpha[-1, :] == 0).all())
        self.assertTrue((alpha[:, 0] == 0).all() and (alpha[:, -1] == 0).all())

    def test_block_split_has_no_seam_for_both_algorithms(self):
        y, x = np.mgrid[:60, :50]
        a = 500 + 5 * np.sin(x / 6) + 3 * np.cos(y / 9) + 0.002 * (x - 25) ** 2
        valid = np.isfinite(a)
        sigma = 2
        halo = int(np.ceil(4 * sigma / 1)) + 1
        for algorithm in ("horn", "central_difference"):
            full = relief(
                a,
                valid,
                1,
                sigma,
                0.05,
                60,
                [0, 3000],
                None,
                "independent_v040",
                None,
                algorithm,
            )[0]
            part = relief(
                a[:40],
                valid[:40],
                1,
                sigma,
                0.05,
                60,
                [0, 3000],
                None,
                "independent_v040",
                None,
                algorithm,
            )[0]
            np.testing.assert_array_equal(
                part[halo: 40 - halo], full[halo: 40 - halo]
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
