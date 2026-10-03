"""v0.12.0: Gaussian σの指定方式（地上距離m／計算格子の画素数px）のテスト。

依頼書（2026-10-03、ユーザー承認）の完了条件の数値と、旧設定（方式の指定なし）がm方式として
従来と同じ計算条件になることを確認する。GDAL・QGISは不要。
"""
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest
import numpy as np
from csmap_sheets.engine.pipeline import (relief, validate_config, gaussian_sigma,
    smoothing_record, smoothing_summary, rendering_settings, run, read_config)


def base_config(**overrides):
    work = Path(tempfile.mkdtemp())
    dummy = work / 'dummy.tif'
    dummy.write_bytes(b'')
    c = dict(inputs=[str(dummy)], output_dir=str(work / 'out'),
             target_crs='EPSG:6677', cell_size=1.0, confirm_elevation_metres=True)
    c.update(overrides)
    return c


def terrain(shape=(70, 80), seed=3):
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[:shape[0], :shape[1]]
    return 300 + 8*np.sin(x/7.) + 5*np.cos(y/5.) + rng.normal(0, .3, shape)


class SigmaUnitTests(unittest.TestCase):
    def kernel(self, **kw):
        r = smoothing_record(validate_config(base_config(**kw), Path.cwd()))
        return r['effective_sigma_m'], r['effective_sigma_px'], r['kernel_size_px']

    def test_completion_conditions(self):
        # 依頼書の完了条件：d=0.5m／1m／2m で、m方式3m・px方式3pxの実効σとカーネル幅
        self.assertEqual(self.kernel(cell_size=.5, sigma_m=3.), (3., 6., 49))
        self.assertEqual(self.kernel(cell_size=.5, sigma_unit='px', sigma_px=3.), (1.5, 3., 25))
        self.assertEqual(self.kernel(cell_size=1., sigma_m=3.), (3., 3., 25))
        self.assertEqual(self.kernel(cell_size=1., sigma_unit='px', sigma_px=3.), (3., 3., 25))
        self.assertEqual(self.kernel(cell_size=2., sigma_m=3.), (3., 1.5, 13))
        self.assertEqual(self.kernel(cell_size=2., sigma_unit='px', sigma_px=3.), (6., 3., 25))

    def test_defaults_and_old_configs_are_metres(self):
        # 方式の指定がない設定（旧プロファイル・旧CLI設定）はm方式・3mで、pxの初期値は3
        c = validate_config(base_config(), Path.cwd())
        self.assertEqual((c['sigma_unit'], c['sigma_m'], c['sigma_px']), ('m', 3.0, 3.0))
        c = validate_config(base_config(sigma_m=2.5, cell_size=.5), Path.cwd())
        self.assertEqual(c['sigma_unit'], 'm')
        self.assertEqual(gaussian_sigma(c), (5.0, 20))

    def test_metre_mode_keeps_previous_float_expressions(self):
        # m方式の半径は従来の式 ceil(4*sigma_m/cell) と完全に同じ（境界値を含む）
        for cell in (.25, .5, 1., 2., 5.):
            for sigma in (0., .1, .3, .7, 1., 2.5, 3., 7.3):
                c = dict(sigma_unit='m', sigma_m=sigma, sigma_px=3., cell_size=cell)
                self.assertEqual(gaussian_sigma(c), (sigma/cell, math.ceil(4*sigma/cell)))

    def test_one_metre_grid_same_result_in_both_modes(self):
        a = terrain()
        valid = np.isfinite(a)
        m = relief(a, valid, 1., 3., .05, 60, [0, 3000])
        px = relief(a, valid, 1., 999., .05, 60, [0, 3000], sigma_px=3.)
        for left, right in zip(m, px):
            np.testing.assert_array_equal(left, right)

    def test_px_mode_matches_equivalent_metres(self):
        # 0.5m格子でpx方式6px ＝ m方式3m（同じ実効σ・同じ半径）
        a = terrain()
        valid = np.isfinite(a)
        m = relief(a, valid, .5, 3., .05, 60, [0, 3000])
        px = relief(a, valid, .5, 0., .05, 60, [0, 3000], sigma_px=6.)
        np.testing.assert_array_equal(m[0], px[0])
        np.testing.assert_array_equal(m[2], px[2])

    def test_px_mode_changes_curvature_on_fine_grid(self):
        a = terrain()
        valid = np.isfinite(a)
        m = relief(a, valid, .5, 3., .05, 60, [0, 3000])[2]
        px = relief(a, valid, .5, 3., .05, 60, [0, 3000], sigma_px=3.)[2]
        self.assertFalse(np.allclose(m[30:40, 30:40], px[30:40, 30:40]))

    def test_zero_sigma_disables_smoothing_in_both_modes(self):
        a = terrain()
        valid = np.isfinite(a)
        m = relief(a, valid, .5, 0., .05, 60, [0, 3000])
        px = relief(a, valid, .5, 3., .05, 60, [0, 3000], sigma_px=0.)
        np.testing.assert_array_equal(m[0], px[0])
        r = smoothing_record(validate_config(base_config(sigma_unit='px', sigma_px=0.), Path.cwd()))
        self.assertEqual((r['effective_sigma_px'], r['kernel_size_px']), (0., 0))
        self.assertIn('なし', smoothing_summary(dict(sigma_unit='px', sigma_px=0., sigma_m=3., cell_size=1.)))

    def test_fractional_px_allowed_and_invalid_values_rejected(self):
        c = validate_config(base_config(sigma_unit='px', sigma_px=1.25, cell_size=.5), Path.cwd())
        self.assertEqual(gaussian_sigma(c), (1.25, 5))
        for bad in (-1., float('nan'), float('inf'), '3', True, None):
            with self.assertRaises(ValueError, msg=repr(bad)):
                validate_config(base_config(sigma_unit='px', sigma_px=bad), Path.cwd())
        for bad in (-1., float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                validate_config(base_config(sigma_m=bad), Path.cwd())
        with self.assertRaisesRegex(ValueError, 'sigma_unit'):
            validate_config(base_config(sigma_unit='cm'), Path.cwd())
        with self.assertRaisesRegex(ValueError, '512'):
            validate_config(base_config(sigma_unit='px', sigma_px=129.), Path.cwd())

    def test_inactive_mode_value_is_kept_not_reinterpreted(self):
        # 方式を切り替えても、もう一方の値を別の単位として読み替えない
        c = validate_config(base_config(sigma_unit='px', sigma_px=4., sigma_m=3., cell_size=.5), Path.cwd())
        self.assertEqual((c['sigma_m'], c['sigma_px']), (3., 4.))
        self.assertEqual(gaussian_sigma(c), (4., 16))
        c['sigma_unit'] = 'm'
        self.assertEqual(gaussian_sigma(c), (6., 24))

    def test_px_mode_block_seams(self):
        # 余白 ceil(4σ_px)+1 があれば、分割して計算しても有効範囲の結果は全体と一致する
        a = terrain((90, 60))
        valid = np.isfinite(a)
        sigma_px = 2.5
        halo = math.ceil(4*sigma_px)+1
        full = relief(a, valid, .5, 0., .05, 60, [0, 3000], sigma_px=sigma_px)[0]
        part = relief(a[:50], valid[:50], .5, 0., .05, 60, [0, 3000], sigma_px=sigma_px)[0]
        np.testing.assert_array_equal(full[halo:50-halo], part[halo:50-halo])

    def test_record_keeps_setting_and_effective_values(self):
        c = validate_config(base_config(sigma_unit='px', sigma_px=3., sigma_m=3., cell_size=2.), Path.cwd())
        terrain_record = rendering_settings(c)['terrain_calculation']
        self.assertEqual(terrain_record['smoothing_sigma_m'], 6.)
        self.assertEqual(terrain_record['smoothing'], dict(
            sigma_unit='px', sigma_setting=3., cell_size_m=2., effective_sigma_m=6.,
            effective_sigma_px=3., kernel_radius_px=12, kernel_size_px=25))
        text = smoothing_summary(c)
        for part in ('画素数 3 px', '計算格子 2 m', '実効σ 6 m = 3 px', '25×25'):
            self.assertIn(part, text)
        c = validate_config(base_config(cell_size=2.), Path.cwd())
        self.assertEqual(rendering_settings(c)['terrain_calculation']['smoothing_sigma_m'], 3.)

    def test_profile_round_trip(self):
        # 保存した設定（JSON）を読み直しても方式と両方の値が保たれる
        c = validate_config(base_config(sigma_unit='px', sigma_px=2.5, sigma_m=4., cell_size=.5), Path.cwd())
        saved = json.loads(json.dumps({k: c[k] for k in ('sigma_unit', 'sigma_px', 'sigma_m')}))
        again = validate_config(base_config(cell_size=.5, **saved), Path.cwd())
        self.assertEqual(gaussian_sigma(again), gaussian_sigma(c))
        self.assertEqual((again['sigma_unit'], again['sigma_px'], again['sigma_m']), ('px', 2.5, 4.))



@unittest.skipUnless(importlib.util.find_spec("osgeo"), "GDAL is not installed")
class SigmaUnitIntegrationTests(unittest.TestCase):
    """図郭の継ぎ目（余白）を含め、px方式が同じ実効σのm方式と同じ図郭を出すこと。"""

    def run_case(self, root, name, **kw):
        config = root/f"{name}.json"
        config.write_text(json.dumps(dict(inputs=[str(root/"dem_*.tif")],
            output_dir=str(root/name), target_crs="EPSG:6677", cell_size=.5,
            plane_zone=9, sheet_level=500, confirm_elevation_metres=True, **kw)), encoding="utf-8")
        run(read_config(config))
        return json.loads((root/name/"run.json").read_text(encoding="utf-8"))

    def test_px_mode_sheets_match_equivalent_metre_mode(self):
        from osgeo import gdal, osr
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            srs = osr.SpatialReference()
            srs.ImportFromEPSG(6677)
            for i in range(2):
                ds = gdal.GetDriverByName("GTiff").Create(str(root/f"dem_{i}.tif"), 96, 96, 1, gdal.GDT_Float32)
                ds.SetProjection(srs.ExportToWkt())
                ds.SetGeoTransform((i*96-96, 1, 0, 0, 0, -1))
                yy, xx = np.mgrid[:96, :96]
                z = 100+(xx+i*96)*.2+yy*.1+3*np.sin((xx+i*96)/6.)*np.cos(yy/5.)
                ds.GetRasterBand(1).WriteArray(z.astype("float32"))
                ds.GetRasterBand(1).SetNoDataValue(-9999)
                ds = None
            metre = self.run_case(root, "metre", sigma_m=1.)
            pixel = self.run_case(root, "pixel", sigma_unit="px", sigma_px=2., sigma_m=3.)
            self.assertEqual(metre["status"], "completed")
            self.assertEqual(pixel["status"], "completed")
            self.assertEqual(pixel["rendering"]["terrain_calculation"]["smoothing"]["kernel_size_px"], 17)
            self.assertEqual(pixel["rendering"]["terrain_calculation"]["smoothing_sigma_m"], 1.)
            self.assertEqual(pixel["settings"]["sigma_m"], 3.)
            names = sorted(f.name for f in (root/"metre/sheets").glob("*.tif"))
            self.assertEqual(names, sorted(f.name for f in (root/"pixel/sheets").glob("*.tif")))
            self.assertEqual(len(names), 2)
            for name in names:
                np.testing.assert_array_equal(gdal.Open(str(root/"metre/sheets"/name)).ReadAsArray(),
                                              gdal.Open(str(root/"pixel/sheets"/name)).ReadAsArray())


if __name__ == '__main__':
    unittest.main()
