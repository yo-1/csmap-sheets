"""Numerical tests; GDAL integration test runs only when GDAL is installed."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from csmap_sheets.engine.pipeline import (relief, run, read_config, validate_config, mosaic_message,
    _jpr_zone_of, infer_target_crs_from_raster, JPR_ZONE_ORIGINS)


class ConfigDefaultsTests(unittest.TestCase):
    """validate_config()'s bare defaults must reproduce independent_v040 (legacy) behaviour
    exactly when a config omits curvature_limit, and must not leak the fme_manual figure into
    it. Regression guard for a bug found 2026-09-24: the bare default had stayed at the FME
    figure (0.03) even for independent_v040, only the QGIS UI's built-in presets masked it."""

    def base_config(self, **overrides):
        work = Path(tempfile.mkdtemp())
        dummy = work / 'dummy.tif'
        dummy.write_bytes(b'')  # discover() only checks extension/existence, not GDAL validity
        c = dict(inputs=[str(dummy)], output_dir=str(work / 'out'),
                 target_crs='EPSG:6677', cell_size=1.0, confirm_elevation_metres=True)
        c.update(overrides)
        return c

    def test_bare_defaults_match_independent_v040(self):
        c = validate_config(self.base_config(), Path.cwd())
        self.assertEqual(c['render_mode'], 'independent_v040')
        self.assertEqual(c['curvature_limit'], 0.05)
        self.assertEqual(c['elevation_range'], [0, 3000])

    def test_fme_manual_bare_defaults_unaffected(self):
        c = validate_config(self.base_config(render_mode='fme_manual'), Path.cwd())
        self.assertEqual(c['curvature_limit'], 0.1)
        self.assertEqual(c['elevation_range'], [200.0, 2000.0])

    def test_merged_geotiff_enabled_defaults_true_and_is_type_checked(self):
        # v0.9.3: 図郭タイルに加えて全域CS方式画像を結合済み1枚のGeoTIFFとしても
        # 出力する設定（ユーザー要望、2026-09-30）。既定は有効、かつbool以外を
        # 与えた場合は明確なエラーで停止することを確認する。
        c = validate_config(self.base_config(), Path.cwd())
        self.assertIs(c['merged_geotiff_enabled'], True)
        with self.assertRaisesRegex(ValueError, 'merged_geotiff_enabled must be boolean'):
            validate_config(self.base_config(merged_geotiff_enabled='yes'), Path.cwd())

    def test_slope_algorithm_defaults_to_horn_and_is_validated(self):
        # v0.10.0: 傾斜計算アルゴリズムの選択（ユーザー決定、2026-10-02）。既定値はHorn法とし、
        # 中央差分法(v0.9.4以前の既定)は明示指定時のみ使う。
        c = validate_config(self.base_config(), Path.cwd())
        self.assertEqual(c['slope_algorithm'], 'horn')
        c2 = validate_config(self.base_config(slope_algorithm='central_difference'), Path.cwd())
        self.assertEqual(c2['slope_algorithm'], 'central_difference')
        with self.assertRaisesRegex(ValueError, 'slope_algorithm must be one of'):
            validate_config(self.base_config(slope_algorithm='bogus'), Path.cwd())

    def test_missing_slope_algorithm_notice_only_for_old_profiles(self):
        from csmap_sheets.engine.pipeline import missing_slope_algorithm_notice
        notice = missing_slope_algorithm_notice({'sigma_m': 3.0}, 'horn')
        self.assertIn('Horn法', notice)
        self.assertIn('中央差分法', notice)
        self.assertIn('中央差分法を使います', missing_slope_algorithm_notice({}, 'central_difference'))
        self.assertIsNone(missing_slope_algorithm_notice({'slope_algorithm': 'horn'}, 'horn'))


class StubSRS:
    """osr.SpatialReferenceの必要最小限のダック型スタブ。この開発環境には
    osgeo(GDAL/OSR)自体が入っていないため、_jpr_zone_of()の純粋な数値照合
    ロジックだけを、実GDALなしで検証する。"""
    def __init__(self, projection='Transverse_Mercator', **parms):
        self._projection = projection
        self._parms = dict(scale_factor=.9999, false_easting=0, false_northing=0, **parms)

    def IsProjected(self):
        return True

    def GetAttrValue(self, key):
        return self._projection if key == 'PROJECTION' else None

    def GetProjParm(self, name):
        return self._parms.get(name, float('nan'))


class StubDataset:
    def __init__(self, srs, wkt='STUB_WKT'):
        self._srs = srs
        self._wkt = wkt

    def GetSpatialRef(self):
        return self._srs

    def GetProjection(self):
        return self._wkt


class StubGDAL:
    def __init__(self, dataset):
        self._dataset = dataset

    def Open(self, path):
        return self._dataset


class JPRZoneDetectionTests(unittest.TestCase):
    """v0.9.3: 出力CRS未指定時に入力ラスターのCRSから第I～XIX系を自動推定する
    機能の回帰テスト（ユーザー要望、2026-09-30）。"""

    def test_zone_ix_origin_matches_known_default(self):
        # 従来のデフォルト値EPSG:6677は第IX系であることをコード内の対応関係
        # (JPR_ZONE_ORIGINSの並び)から確認する。
        lat0, lon0 = JPR_ZONE_ORIGINS[8]
        srs = StubSRS(latitude_of_origin=lat0, central_meridian=lon0)
        self.assertEqual(_jpr_zone_of(srs), 9)

    def test_non_transverse_mercator_is_not_a_zone(self):
        srs = StubSRS(projection='Mercator_1SP')
        self.assertIsNone(_jpr_zone_of(srs))

    def test_transverse_mercator_with_unmatched_origin_is_not_a_zone(self):
        # UTM等、Transverse_Mercatorだが第I～XIX系のいずれの原点とも一致しない場合。
        srs = StubSRS(latitude_of_origin=0, central_meridian=141)
        self.assertIsNone(_jpr_zone_of(srs))

    def test_infer_target_crs_from_raster_returns_wkt_when_zone_matches(self):
        lat0, lon0 = JPR_ZONE_ORIGINS[8]
        srs = StubSRS(latitude_of_origin=lat0, central_meridian=lon0)
        gdal = StubGDAL(StubDataset(srs, wkt='ZONE9_WKT'))
        wkt, reason = infer_target_crs_from_raster('dummy.tif', gdal)
        self.assertEqual(wkt, 'ZONE9_WKT')
        self.assertIsNone(reason)

    def test_infer_target_crs_from_raster_returns_none_when_unmatched(self):
        srs = StubSRS(latitude_of_origin=0, central_meridian=141)
        gdal = StubGDAL(StubDataset(srs))
        wkt, reason = infer_target_crs_from_raster('dummy.tif', gdal)
        self.assertIsNone(wkt)
        self.assertIn('平面直角座標系', reason)

    def test_infer_target_crs_from_raster_returns_none_when_unreadable_or_no_crs(self):
        wkt, reason = infer_target_crs_from_raster('dummy.tif', StubGDAL(None))
        self.assertIsNone(wkt);self.assertIn('開けません', reason)
        # TIFF+TFW（ワールドファイル）はCRS情報自体を持たないため、GDALで開けても
        # GetSpatialRef()がNoneまたはGetProjection()が空文字列になる。この場合を
        # 「一致しなかった」場合と区別できるメッセージを返すことを確認する
        # （ユーザー報告、2026-09-30：この違いが分かりにくいという指摘）。
        wkt, reason = infer_target_crs_from_raster('dummy.tif', StubGDAL(StubDataset(None)))
        self.assertIsNone(wkt);self.assertIn('TFW', reason)
        wkt, reason = infer_target_crs_from_raster('dummy.tif', StubGDAL(StubDataset(StubSRS(), wkt='')))
        self.assertIsNone(wkt);self.assertIn('TFW', reason)


class ReliefTests(unittest.TestCase):
    def render(self, a, cell=1, sigma=2):
        return relief(a, np.isfinite(a), cell, sigma, .05, 60, [0, 3000])

    def test_flat(self):
        a = np.full((81, 81), 100.)
        rgba, slope, curv = self.render(a)
        self.assertEqual(int(rgba[40, 40, 3]), 255)
        self.assertAlmostEqual(slope[40, 40], 0)
        self.assertAlmostEqual(curv[40, 40], 0)

    def test_plane_and_units(self):
        y, x = np.mgrid[:81, :81]
        for cell in (1, 5):
            _, slope, curv = self.render(100 + x*cell*.2 + y*cell*.3, cell=cell)
            self.assertAlmostEqual(slope[40, 40], np.degrees(np.arctan(np.hypot(.2, .3))))
            self.assertAlmostEqual(curv[40, 40], 0)

    def test_bowl_hill_sign_and_colour(self):
        y, x = np.mgrid[-40:41, -40:41]
        bowl = 100 + .01*(x*x+y*y)
        hill = 100 - .01*(x*x+y*y)
        for a, sign in ((bowl, -1), (hill, 1)):
            rgba, _, curv = self.render(a)
            self.assertAlmostEqual(curv[40, 40], sign*.04)
            if sign == 1:
                self.assertGreater(int(rgba[40, 40, 0]), int(rgba[40, 40, 2]))
            else:
                self.assertLess(int(rgba[40, 40, 0]), int(rgba[40, 40, 2]))

    def test_nodata_and_outer_edge(self):
        a = np.full((81, 81), 100.)
        a[40, 40] = np.nan
        rgba, _, _ = self.render(a)
        self.assertEqual(int(rgba[40, 49, 3]), 0)  # radius 8 + derivative 1
        self.assertEqual(int(rgba[40, 50, 3]), 255)
        self.assertEqual(int(rgba[0, 40, 3]), 0)

    def test_all_nodata(self):
        rgba, _, _ = self.render(np.full((81, 81), np.nan))
        self.assertFalse(np.any(rgba))

    def test_block_seams(self):
        y, x = np.mgrid[:163, :175]
        a = 100 + np.sin(x/7)*3 + np.cos(y/9)*5
        a[81, 89] = np.nan
        expected, _, _ = self.render(a)
        actual = np.zeros_like(expected)
        halo, block = 9, 37
        for yy in range(0, a.shape[0], block):
            for xx in range(0, a.shape[1], block):
                x0, y0 = max(0, xx-halo), max(0, yy-halo)
                x1, y1 = min(a.shape[1], xx+block+halo), min(a.shape[0], yy+block+halo)
                rgba, _, _ = self.render(a[y0:y1, x0:x1])
                bw, bh = min(block, a.shape[1]-xx), min(block, a.shape[0]-yy)
                actual[yy:yy+bh, xx:xx+bw] = rgba[yy-y0:yy-y0+bh, xx-x0:xx-x0+bw]
        np.testing.assert_array_equal(actual, expected)

    def test_fme_block_seams(self):
        y,x=np.mgrid[:163,:175]
        a=500+np.sin(x/7)*3+np.cos(y/9)*5
        expected=relief(a,np.isfinite(a),1,2,.1,60,[200,2000],None,'fme_manual')[0]
        actual=np.zeros_like(expected);halo,block=9,37
        for yy in range(0,a.shape[0],block):
            for xx in range(0,a.shape[1],block):
                x0,y0=max(0,xx-halo),max(0,yy-halo)
                x1,y1=min(a.shape[1],xx+block+halo),min(a.shape[0],yy+block+halo)
                rgba=relief(a[y0:y1,x0:x1],np.ones((y1-y0,x1-x0),bool),1,2,.1,60,
                            [200,2000],None,'fme_manual')[0]
                bw,bh=min(block,a.shape[1]-xx),min(block,a.shape[0]-yy)
                actual[yy:yy+bh,xx:xx+bw]=rgba[yy-y0:yy-y0+bh,xx-x0:xx-x0+bw]
        np.testing.assert_array_equal(actual,expected)


@unittest.skipUnless(importlib.util.find_spec("osgeo"), "GDAL is not installed")
class ElevationAutoRangeTests(unittest.TestCase):
    def test_elevation_range_auto_detects_from_mosaic(self):
        from osgeo import gdal, osr
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            srs = osr.SpatialReference()
            srs.ImportFromEPSG(6677)
            ds = gdal.GetDriverByName("GTiff").Create(str(root/"dem.tif"), 40, 40, 1, gdal.GDT_Float32)
            ds.SetProjection(srs.ExportToWkt())
            ds.SetGeoTransform((0, 1, 0, 0, 0, -1))
            yy, xx = np.mgrid[:40, :40]
            elev = (500 + xx.astype("float32") * 2)  # ranges exactly 500..578
            ds.GetRasterBand(1).WriteArray(elev)
            ds.GetRasterBand(1).SetNoDataValue(-9999)
            ds = None
            config = root/"config.json"
            config.write_text(json.dumps(dict(inputs=[str(root/"dem.tif")],
                output_dir=str(root/"result"), target_crs="EPSG:6677", cell_size=1,
                sigma_m=2, plane_zone=9, sheet_level=500, render_mode="fme_manual",
                elevation_range_auto=True, elevation_range_margin=25.0,
                confirm_elevation_metres=True)), encoding="utf-8")
            run(read_config(config))
            manifest = json.loads((root/"result/run.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "completed")
            detected = manifest["elevation_range_detected"]
            self.assertAlmostEqual(detected[0], 500.0, delta=1.0)
            self.assertAlmostEqual(detected[1], 578.0, delta=1.0)
            used = manifest["rendering"]["normalization"]["elevation_m"]
            self.assertAlmostEqual(used[0], detected[0] - 25.0, delta=1.0)
            self.assertAlmostEqual(used[1], detected[1] + 25.0, delta=1.0)


@unittest.skipUnless(importlib.util.find_spec("osgeo"), "GDAL is not installed")
class IntegrationTests(unittest.TestCase):
    def test_two_dem_mosaic_to_map_sheets(self):
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
                ds.GetRasterBand(1).WriteArray((100+(xx+i*96)*.2+yy*.1).astype("float32"))
                ds.GetRasterBand(1).SetNoDataValue(-9999)
                ds = None
            config = root/"config.json"
            config.write_text(json.dumps(dict(inputs=[str(root/"dem_*.tif")],
                output_dir=str(root/"result"), target_crs="EPSG:6677", cell_size=1,
                sigma_m=2, plane_zone=9, sheet_level=500,
                confirm_elevation_metres=True)), encoding="utf-8")
            run(read_config(config))
            self.assertTrue((root/'result/projected_dem.vrt').exists())
            rgba = gdal.Open(str(root/"result/cs_relief.vrt"))
            self.assertEqual((rgba.RasterXSize,rgba.RasterYSize),(800,300))
            self.assertEqual(int(rgba.GetRasterBand(4).ReadAsArray()[40,400]),255)
            expected=rgba.ReadAsArray()[:,:96,304:496]
            rgba=None
            files=sorted((root/"result/sheets").glob("*.tif"))
            self.assertEqual([f.stem for f in files],["09KD0909","09KE0000"])
            left=gdal.Open(str(files[0]))
            right=gdal.Open(str(files[1]))
            self.assertEqual((left.RasterXSize,left.RasterYSize),(400,300))
            self.assertEqual(left.GetGeoTransform(),(-400.,1.,0.,0.,0.,-1.))
            self.assertEqual(right.GetGeoTransform(),(0.,1.,0.,0.,0.,-1.))
            reconstructed=np.concatenate((left.ReadAsArray()[:,:96,304:],right.ReadAsArray()[:,:96,:96]),axis=2)
            np.testing.assert_array_equal(reconstructed,expected)
            self.assertFalse(np.any(left.GetRasterBand(4).ReadAsArray()[:, :304]))
            self.assertEqual(files[0].with_suffix('.tfw').read_text().splitlines()[-2:],
                             ['-399.500000000000','-0.500000000000'])
            left=right=None
            self.assertTrue((root/'result/sheet_index.gpkg').exists())
            self.assertEqual(json.loads((root/"result/run.json").read_text(encoding="utf-8"))["status"], "completed")



class VersionDisplayTests(unittest.TestCase):
    def test_version_banner_shows_name_and_version(self):
        from csmap_sheets.engine.pipeline import version_banner, VERSION
        banner=version_banner()
        self.assertIn('図郭対応CS立体図作成プラグイン（CS Map Sheets）',banner)
        self.assertTrue(banner.endswith(' v'+VERSION))

    def test_version_matches_metadata(self):
        # 画面・ログ・run.jsonに出る版（VERSION）と、プラグイン管理画面に出る版（metadata.txt）の一致
        from csmap_sheets.engine.pipeline import VERSION
        meta=Path(__file__).resolve().parents[1]/'metadata.txt'
        lines=[l for l in meta.read_text(encoding='utf-8').splitlines() if l.startswith('version=')]
        self.assertEqual(lines,['version='+VERSION])



class MosaicMessageTests(unittest.TestCase):
    def test_gsi_reports_groups_and_tiles(self):
        c = {'input_type': 'gsi', 'inputs': ['a.tif'] * 7}
        self.assertEqual(mosaic_message(c, {'sources': [{}] * 100}),
                         'Mosaic: 7 grid groups from 100 GSI DEM tiles '
                         '(tiles sharing a pixel grid are merged into one group)')

    def test_other_inputs_keep_previous_wording(self):
        self.assertEqual(mosaic_message({'input_type': 'raster', 'inputs': ['a', 'b']},
                                        {'sources': [{}, {}]}), 'Mosaic: 2 DEM files')
        self.assertEqual(mosaic_message({'input_type': 'gsi', 'inputs': ['a']}, {}),
                         'Mosaic: 1 DEM files')


if __name__ == "__main__":
    unittest.main(verbosity=2)
