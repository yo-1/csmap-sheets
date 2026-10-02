import unittest
import tempfile
from pathlib import Path
import numpy as np
from csmap_sheets.engine.xyz_tiles import *
from csmap_sheets.engine.xyz_tiles import _tile_encoder

class XYZTests(unittest.TestCase):
    def test_world(self):
        h=HALF_WORLD
        self.assertEqual(tile_range((-h,-h,h,h),0),(0,0,0,0))
        self.assertEqual(tile_range((-h,-h,h,h),2),(0,3,0,3))

    def test_north_origin_and_adjacent_edges(self):
        nw=tile_bounds(1,0,0);se=tile_bounds(1,1,1)
        self.assertEqual(nw,(-HALF_WORLD,0,0,HALF_WORLD))
        self.assertEqual(se,(0,-HALF_WORLD,HALF_WORLD,0))
        self.assertEqual(tile_range(nw,1),(0,0,0,0))

    def test_japan(self):
        h=HALF_WORLD
        east=139/180*h
        north=6378137*np.log(np.tan(np.pi/4+np.deg2rad(35)/2))
        self.assertEqual(tile_range((east,north,east+1,north+1),2),(3,3,1,1))

    def test_estimate_candidate_tiles_matches_manual_sum(self):
        h = HALF_WORLD
        bounds = (-h, -h, h, h)
        manual = sum(estimate_candidate_tiles(bounds, z, z) for z in range(0, 4))
        self.assertEqual(estimate_candidate_tiles(bounds, 0, 3), manual)
        self.assertEqual(estimate_candidate_tiles(bounds, 2, 2), 16)

    def test_default_max_zoom_is_16(self):
        # v0.9.4: 検証用データでの確認の結果、標準運用のXYZ最大ズームは16とする。
        self.assertEqual(DEFAULTS['xyz_max_zoom'], 16)

    def test_precheck_xyz_tile_count_integration(self):
        try: from osgeo import gdal, osr
        except ImportError: self.skipTest('GDAL runtime unavailable')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); src = root/'projected_dem.vrt'
            ds = gdal.GetDriverByName('GTiff').Create(str(root/'dem.tif'), 256, 256, 1, gdal.GDT_Float32)
            h = HALF_WORLD; ds.SetGeoTransform((-h, h/256, 0, h, 0, -h/256))
            crs = osr.SpatialReference(); crs.ImportFromEPSG(3857); ds.SetProjection(crs.ExportToWkt())
            ds.GetRasterBand(1).Fill(100.0)
            ds = None
            gdal.Translate(str(src), str(root/'dem.tif'), format='VRT')
            # 十分小さいズーム範囲なら通過し、候補数を返す。
            total = precheck_xyz_tile_count(str(src), {**DEFAULTS, 'xyz_min_zoom': 0, 'xyz_max_zoom': 2}, gdal, osr)
            self.assertEqual(total, estimate_candidate_tiles((-h, -h, h, h), 0, 2))
            # 上限を明らかに超えるズーム範囲・上限値なら、CS立体図計算を待たずに例外。
            with self.assertRaises(ValueError):
                precheck_xyz_tile_count(str(src), {**DEFAULTS, 'xyz_min_zoom': 0, 'xyz_max_zoom': 10,
                                                    'xyz_max_tiles': 1}, gdal, osr)
            # xyz_enabled=Falseなら範囲を開かずNoneを返す（存在しないパスでも例外にならない）。
            self.assertIsNone(precheck_xyz_tile_count(
                str(root/'does_not_exist.vrt'), {**DEFAULTS, 'xyz_enabled': False}, gdal, osr))

    def test_settings(self):
        validate_xyz(DEFAULTS)
        validate_xyz({**DEFAULTS, 'xyz_format': 'webp'})
        validate_xyz({**DEFAULTS, 'xyz_format': 'webp', 'xyz_webp_lossless': False, 'xyz_webp_quality': 40})
        for patch in ({'xyz_min_zoom':19},{'xyz_max_zoom':25},{'xyz_max_tiles':0},
                      {'xyz_enabled':'true'},{'xyz_min_zoom':True},
                      {'xyz_format':'jpeg'},{'xyz_format':'PNG'},
                      {'xyz_webp_lossless':'true'},{'xyz_webp_quality':0},
                      {'xyz_webp_quality':101},{'xyz_webp_quality':75.0}):
            with self.assertRaises(ValueError): validate_xyz({**DEFAULTS,**patch})

    def test_webp_defaults_are_lossless_quality75(self):
        self.assertTrue(DEFAULTS['xyz_webp_lossless'])
        self.assertEqual(DEFAULTS['xyz_webp_quality'], 75)

    def test_default_format_is_png(self):
        self.assertEqual(DEFAULTS['xyz_format'], 'png')

    def test_encoder_selection_and_missing_driver_error(self):
        class _FakeDriver:
            pass

        class _FakeGDAL:
            def __init__(self, available):
                self._available = available
            def GetDriverByName(self, name):
                return _FakeDriver() if name in self._available else None

        driver, ext, options, encoder = _tile_encoder('png', _FakeGDAL({'PNG'}))
        self.assertEqual((ext, options, encoder['driver']), ('png', [], 'PNG'))

        driver, ext, options, encoder = _tile_encoder('webp', _FakeGDAL({'PNG', 'WEBP'}))
        self.assertEqual(ext, 'webp')
        self.assertIn('LOSSLESS=TRUE', options)
        self.assertEqual(encoder['driver'], 'WEBP')
        self.assertTrue(encoder['lossless'])
        self.assertIsNone(encoder['quality'])

        # 非可逆(lossy)：LOSSLESS=FALSEとQUALITYが作成オプションへ明示的に渡ること。
        driver, ext, options, encoder = _tile_encoder(
            'webp', _FakeGDAL({'PNG', 'WEBP'}), webp_lossless=False, webp_quality=40)
        self.assertEqual(ext, 'webp')
        self.assertIn('LOSSLESS=FALSE', options)
        self.assertIn('QUALITY=40', options)
        self.assertFalse(encoder['lossless'])
        self.assertEqual(encoder['quality'], 40)

        # WEBP unavailable must raise a clear error, never fall back to PNG silently
        # (regardless of lossless/lossy selection).
        with self.assertRaises(RuntimeError):
            _tile_encoder('webp', _FakeGDAL({'PNG'}))
        with self.assertRaises(RuntimeError):
            _tile_encoder('webp', _FakeGDAL({'PNG'}), webp_lossless=False, webp_quality=40)

    def test_rgba_png_integration(self):
        try: from osgeo import gdal,osr
        except ImportError: self.skipTest('GDAL runtime unavailable')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); src=root/'rgba.tif'
            ds=gdal.GetDriverByName('GTiff').Create(str(src),256,256,4,gdal.GDT_Byte)
            h=HALF_WORLD; ds.SetGeoTransform((-h,h/256,0,h,0,-h/256))
            crs=osr.SpatialReference();crs.ImportFromEPSG(3857);ds.SetProjection(crs.ExportToWkt())
            for i,value in enumerate((180,90,45,255),1):
                ds.GetRasterBand(i).Fill(value)
            ds.GetRasterBand(4).SetColorInterpretation(gdal.GCI_AlphaBand)
            ds.GetRasterBand(4).WriteArray(np.zeros((128,256),dtype='uint8'),0,128)
            ds=None
            result=write_xyz(src,root/'tiles',dict(xyz_min_zoom=1,xyz_max_zoom=1),gdal,osr)
            self.assertEqual(result['status'],'completed')
            self.assertEqual(result['written_tiles'],1)
            tile=gdal.Open(str(root/'tiles/1/0/0.png'))
            self.assertEqual((tile.RasterXSize,tile.RasterYSize,tile.RasterCount),(256,256,4))
            pixels=tile.ReadAsArray()
            np.testing.assert_array_equal(pixels[:3,10,10],[180,90,45])
            self.assertEqual(pixels[3,10,10],255)
            self.assertEqual(pixels[3,200,10],0)
            tile=None
            with self.assertRaises(ValueError):
                write_xyz(src,root/'limited',dict(xyz_min_zoom=1,xyz_max_zoom=2,xyz_max_tiles=1),gdal,osr)
            self.assertFalse((root/'limited').exists())

    def test_rgba_webp_lossless_integration(self):
        try: from osgeo import gdal,osr
        except ImportError: self.skipTest('GDAL runtime unavailable')
        if gdal.GetDriverByName('WEBP') is None:
            self.skipTest('GDAL WEBP driver unavailable in this environment')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); src=root/'rgba.tif'
            ds=gdal.GetDriverByName('GTiff').Create(str(src),256,256,4,gdal.GDT_Byte)
            h=HALF_WORLD; ds.SetGeoTransform((-h,h/256,0,h,0,-h/256))
            crs=osr.SpatialReference();crs.ImportFromEPSG(3857);ds.SetProjection(crs.ExportToWkt())
            for i,value in enumerate((180,90,45,255),1):
                ds.GetRasterBand(i).Fill(value)
            ds.GetRasterBand(4).SetColorInterpretation(gdal.GCI_AlphaBand)
            ds.GetRasterBand(4).WriteArray(np.zeros((128,256),dtype='uint8'),0,128)
            ds=None
            result=write_xyz(src,root/'tiles',dict(xyz_min_zoom=1,xyz_max_zoom=1,xyz_format='webp'),gdal,osr)
            self.assertEqual(result['status'],'completed')
            self.assertEqual(result['format'],'webp')
            self.assertEqual(result['template'],'{z}/{x}/{y}.webp')
            tile=gdal.Open(str(root/'tiles/1/0/0.webp'))
            self.assertEqual((tile.RasterXSize,tile.RasterYSize,tile.RasterCount),(256,256,4))
            pixels=tile.ReadAsArray()
            # Lossless: decoded pixels must match the source exactly (handover doc 5.2).
            np.testing.assert_array_equal(pixels[:3,10,10],[180,90,45])
            self.assertEqual(pixels[3,10,10],255)
            self.assertEqual(pixels[3,200,10],0)
            tile=None

    def test_rgba_webp_lossy_integration(self):
        try: from osgeo import gdal,osr
        except ImportError: self.skipTest('GDAL runtime unavailable')
        if gdal.GetDriverByName('WEBP') is None:
            self.skipTest('GDAL WEBP driver unavailable in this environment')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); src=root/'rgba.tif'
            ds=gdal.GetDriverByName('GTiff').Create(str(src),256,256,4,gdal.GDT_Byte)
            h=HALF_WORLD; ds.SetGeoTransform((-h,h/256,0,h,0,-h/256))
            crs=osr.SpatialReference();crs.ImportFromEPSG(3857);ds.SetProjection(crs.ExportToWkt())
            for i,value in enumerate((180,90,45,255),1):
                ds.GetRasterBand(i).Fill(value)
            ds.GetRasterBand(4).SetColorInterpretation(gdal.GCI_AlphaBand)
            ds.GetRasterBand(4).WriteArray(np.zeros((128,256),dtype='uint8'),0,128)
            ds=None
            result=write_xyz(src,root/'tiles',dict(xyz_min_zoom=1,xyz_max_zoom=1,xyz_format='webp',
                              xyz_webp_lossless=False,xyz_webp_quality=40),gdal,osr)
            self.assertEqual(result['status'],'completed')
            self.assertEqual(result['format'],'webp')
            self.assertEqual(result['encoder']['lossless'],False)
            self.assertEqual(result['encoder']['quality'],40)
            tile=gdal.Open(str(root/'tiles/1/0/0.webp'))
            self.assertEqual((tile.RasterXSize,tile.RasterYSize,tile.RasterCount),(256,256,4))
            pixels=tile.ReadAsArray()
            # 非可逆(lossy)のため画素完全一致は保証しないが、無地の単色領域はJPEG系圧縮でも
            # ほぼ復元されるはずで、大きくかけ離れないことだけを確認する（許容差20）。
            self.assertLess(abs(int(pixels[0,10,10])-180),20)
            self.assertLess(abs(int(pixels[1,10,10])-90),20)
            self.assertLess(abs(int(pixels[2,10,10])-45),20)
            tile=None

    def test_webp_driver_missing_raises_and_writes_no_output(self):
        try: from osgeo import gdal,osr
        except ImportError: self.skipTest('GDAL runtime unavailable')
        if gdal.GetDriverByName('WEBP') is not None:
            self.skipTest('GDAL WEBP driver is available; missing-driver path not exercised here')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); src=root/'rgba.tif'
            ds=gdal.GetDriverByName('GTiff').Create(str(src),256,256,4,gdal.GDT_Byte)
            h=HALF_WORLD; ds.SetGeoTransform((-h,h/256,0,h,0,-h/256))
            crs=osr.SpatialReference();crs.ImportFromEPSG(3857);ds.SetProjection(crs.ExportToWkt())
            ds=None
            with self.assertRaises(RuntimeError):
                write_xyz(src,root/'tiles',dict(xyz_min_zoom=1,xyz_max_zoom=1,xyz_format='webp'),gdal,osr)
            self.assertFalse((root/'tiles').exists())

if __name__=='__main__':unittest.main()
