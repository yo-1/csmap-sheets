"""External profile compatibility, without QGIS."""
import unittest
from pathlib import Path
from csmap_sheets.engine.pipeline import profile_nodata_edge_mode, validate_config
from csmap_sheets.tests.test_sigma_unit import base_config, terrain
from csmap_sheets.engine.pipeline import relief
import numpy as np
import math


class ProfileNodataTests(unittest.TestCase):
    def test_old_profile_default_screen(self):
        self.assertEqual(profile_nodata_edge_mode({}, 'safe_mask'), ('safe_mask', None))

    def test_old_profile_pss_screen_warns(self):
        mode, warning = profile_nodata_edge_mode({}, 'pss_approximation')
        self.assertEqual(mode, 'safe_mask')
        self.assertIn('nodata_edge_mode', warning)

    def test_explicit_modes_override_screen(self):
        for mode in ('safe_mask', 'pss_approximation'):
            for screen in ('safe_mask', 'pss_approximation'):
                self.assertEqual(profile_nodata_edge_mode({'nodata_edge_mode': mode}, screen), (mode, None))

    def test_invalid_mode_reaches_existing_validation(self):
        mode, warning = profile_nodata_edge_mode({'nodata_edge_mode': 'invalid'}, 'safe_mask')
        self.assertIsNone(warning)
        with self.assertRaisesRegex(ValueError, 'nodata_edge_mode'):
            validate_config(base_config(nodata_edge_mode=mode), Path.cwd())

    def test_v4_profile(self):
        profile = {'schema': 'csmap-settings-profile-v4', 'settings': {'sigma_unit': 'px', 'sigma_px': 2.5}}
        mode, _ = profile_nodata_edge_mode(profile['settings'], 'pss_approximation')
        result = validate_config(base_config(**profile['settings'], nodata_edge_mode=mode), Path.cwd())
        self.assertEqual((result['nodata_edge_mode'], result['sigma_unit'], result['sigma_px']), ('safe_mask', 'px', 2.5))


class BufferedSheetTests(unittest.TestCase):
    def test_adjacent_buffered_sheets_match_joint_render(self):
        # Mirrors render_sheets: halo=ceil(4*sigma_px)+1, render then crop.
        z = terrain((100, 160))
        valid = np.ones(z.shape, dtype=bool)
        valid[48:52, 79:82] = False
        sigma = 2.5
        halo = math.ceil(4*sigma)+1
        for mode in ('safe_mask', 'pss_approximation'):
            for slope in ('horn', 'central_difference'):
                def render(a, mask):
                    return relief(a, mask, 1., sigma, .05, 60, [0, 3000],
                                  slope_algorithm=slope, nodata_edge_mode=mode)[0]
                full = render(z, valid)[30:70, 40:120]
                parts = []
                for left, right in ((40, 80), (80, 120)):
                    part = render(z[30-halo:70+halo, left-halo:right+halo],
                                  valid[30-halo:70+halo, left-halo:right+halo])
                    parts.append(part[halo:-halo, halo:-halo])
                np.testing.assert_array_equal(full, np.concatenate(parts, axis=1))


if __name__ == '__main__':
    unittest.main()
