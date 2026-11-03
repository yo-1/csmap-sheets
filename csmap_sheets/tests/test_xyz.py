import unittest
import tempfile
from pathlib import Path
import numpy as np
from csmap_sheets.engine.xyz_tiles import (
    HALF_WORLD,
    tile_range,
    tile_bounds,
    estimate_candidate_tiles,
    DEFAULTS,
    precheck_xyz_tile_count,
    validate_xyz,
    write_xyz,
    _tile_encoder,
)


class XYZTests(unittest.TestCase):
    def test_world(self):
        h = HALF_WORLD
        self.assertEqual(tile_range((-h, -h, h, h), 0), (0, 0, 0, 0))
        self.assertEqual(tile_range((-h, -h, h, h), 2), (0, 3, 0, 3))

    def test_north_origin_and_adjacent_edges(self):
        nw = tile_bounds(1, 0, 0)
        se = tile_bounds(1, 1, 1)
        self.assertEqual(nw, (-HALF_WORLD, 0, 0, HALF_WORLD))
        self.assertEqual(se, (0, -HALF_WORLD, HALF_WORLD, 0))
        self.assertEqual(tile_range(nw, 1), (0, 0, 0, 0))

    def test_japan(self):
        h = HALF_WORLD
        east = 139 / 180 * h
        north = 6378137 * np.log(np.tan(np.pi / 4 + np.deg2rad(35) / 2))
        self.assertEqual(
            tile_range((east, north, east + 1, north + 1), 2), (3, 3, 1, 1)
        )

    def test_estimate_candidate_tiles_matches_manual_sum(self):
        h = HALF_WORLD
        bounds = (-h, -h, h, h)
        manual = sum(
            estimate_candidate_tiles(bounds, z, z) for z in range(0, 4)
        )
        self.assertEqual(estimate_candidate_tiles(bounds, 0, 3), manual)
        self.assertEqual(estimate_candidate_tiles(bounds, 2, 2), 16)

    def test_default_max_zoom_is_16(self):
        # v0.9.4: 検証用データでの確認の結果、標準運用のXYZ最大ズームは16とする。
        self.assertEqual(DEFAULTS["xyz_max_zoom"], 16)

    def test_cli_defaults_match_plugin_defaults(self):
        # CLIの既定値がプラグイン本体（DEFAULTS）と一致すること（--max-zoomが18のまま残っていた不整合の回帰防止）。
        from csmap_sheets.engine.xyz_tiles import build_cli_parser

        a = build_cli_parser().parse_args(
            ["--input", "in.tif", "--output", "out"]
        )
        self.assertEqual(a.min_zoom, DEFAULTS["xyz_min_zoom"])
        self.assertEqual(a.max_zoom, DEFAULTS["xyz_max_zoom"])
        self.assertEqual(a.max_zoom, 16)
        self.assertEqual(a.max_tiles, DEFAULTS["xyz_max_tiles"])
        self.assertEqual(a.format, DEFAULTS["xyz_format"])
        self.assertEqual(a.webp_quality, DEFAULTS["xyz_webp_quality"])
        self.assertFalse(a.webp_lossy)
        # 明示指定は既定値より優先される
        b = build_cli_parser().parse_args(
            ["--input", "i", "--output", "o", "--max-zoom", "18"]
        )
        self.assertEqual(b.max_zoom, 18)
        with self.assertRaises(SystemExit):
            build_cli_parser().parse_args(
                ["--input", "i", "--output", "o", "--format", "jpg"]
            )

    def test_precheck_xyz_tile_count_integration(self):
        try:
            from osgeo import gdal, osr
        except ImportError:
            self.skipTest("GDAL runtime unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "projected_dem.vrt"
            ds = gdal.GetDriverByName("GTiff").Create(
                str(root / "dem.tif"), 256, 256, 1, gdal.GDT_Float32
            )
            # 世界全体（-h..h、幅2h）を256画素で覆う。以前は画素幅をh/256としていたため
            # 北西の4分の1しか覆っておらず、期待値（全球の候補数）と食い違っていた。
            h = HALF_WORLD
            ds.SetGeoTransform((-h, 2 * h / 256, 0, h, 0, -2 * h / 256))
            crs = osr.SpatialReference()
            crs.ImportFromEPSG(3857)
            ds.SetProjection(crs.ExportToWkt())
            ds.GetRasterBand(1).Fill(100.0)
            ds = None
            gdal.Translate(str(src), str(root / "dem.tif"), format="VRT")
            # 十分小さいズーム範囲なら通過し、候補数を返す。
            total = precheck_xyz_tile_count(
                str(src),
                {**DEFAULTS, "xyz_min_zoom": 0, "xyz_max_zoom": 2},
                gdal,
                osr,
            )
            self.assertEqual(
                total, estimate_candidate_tiles((-h, -h, h, h), 0, 2)
            )
            # 上限を明らかに超えるズーム範囲・上限値なら、CS立体図計算を待たずに例外。
            with self.assertRaises(ValueError):
                precheck_xyz_tile_count(
                    str(src),
                    {
                        **DEFAULTS,
                        "xyz_min_zoom": 0,
                        "xyz_max_zoom": 10,
                        "xyz_max_tiles": 1,
                    },
                    gdal,
                    osr,
                )
            # xyz_enabled=Falseなら範囲を開かずNoneを返す（存在しないパスでも例外にならない）。
            self.assertIsNone(
                precheck_xyz_tile_count(
                    str(root / "does_not_exist.vrt"),
                    {**DEFAULTS, "xyz_enabled": False},
                    gdal,
                    osr,
                )
            )

    def test_settings(self):
        validate_xyz(DEFAULTS)
        validate_xyz({**DEFAULTS, "xyz_format": "webp"})
        validate_xyz(
            {
                **DEFAULTS,
                "xyz_format": "webp",
                "xyz_webp_lossless": False,
                "xyz_webp_quality": 40,
            }
        )
        for patch in (
            {"xyz_min_zoom": 19},
            {"xyz_max_zoom": 25},
            {"xyz_max_tiles": 0},
            {"xyz_enabled": "true"},
            {"xyz_min_zoom": True},
            {"xyz_format": "jpeg"},
            {"xyz_format": "PNG"},
            {"xyz_webp_lossless": "true"},
            {"xyz_webp_quality": 0},
            {"xyz_webp_quality": 101},
            {"xyz_webp_quality": 75.0},
        ):
            with self.assertRaises(ValueError):
                validate_xyz({**DEFAULTS, **patch})

    def test_webp_defaults_are_lossy_quality75(self):
        # v0.12.0: WebPの既定は非可逆・QUALITY 75（ユーザー決定、2026-10-04）。形式の既定はPNGのまま。
        self.assertFalse(DEFAULTS["xyz_webp_lossless"])
        self.assertEqual(DEFAULTS["xyz_webp_quality"], 75)

    def test_default_format_is_png(self):
        self.assertEqual(DEFAULTS["xyz_format"], "png")

    def test_encoder_selection_and_missing_driver_error(self):
        class _FakeDriver:
            pass

        class _FakeGDAL:
            def __init__(self, available):
                self._available = available

            def GetDriverByName(self, name):
                return _FakeDriver() if name in self._available else None

        driver, ext, options, encoder = _tile_encoder(
            "png", _FakeGDAL({"PNG"})
        )
        self.assertEqual((ext, options, encoder["driver"]), ("png", [], "PNG"))

        driver, ext, options, encoder = _tile_encoder(
            "webp", _FakeGDAL({"PNG", "WEBP"})
        )
        self.assertEqual(ext, "webp")
        self.assertIn("LOSSLESS=TRUE", options)
        self.assertEqual(encoder["driver"], "WEBP")
        self.assertTrue(encoder["lossless"])
        self.assertIsNone(encoder["quality"])

        # 非可逆(lossy)：LOSSLESS=FALSEとQUALITYが作成オプションへ明示的に渡ること。
        driver, ext, options, encoder = _tile_encoder(
            "webp",
            _FakeGDAL({"PNG", "WEBP"}),
            webp_lossless=False,
            webp_quality=40,
        )
        self.assertEqual(ext, "webp")
        self.assertIn("LOSSLESS=FALSE", options)
        self.assertIn("QUALITY=40", options)
        self.assertFalse(encoder["lossless"])
        self.assertEqual(encoder["quality"], 40)

        # WEBP unavailable must raise a clear error, never fall back to PNG
        # silently
        # (regardless of lossless/lossy selection).
        with self.assertRaises(RuntimeError):
            _tile_encoder("webp", _FakeGDAL({"PNG"}))
        with self.assertRaises(RuntimeError):
            _tile_encoder(
                "webp",
                _FakeGDAL({"PNG"}),
                webp_lossless=False,
                webp_quality=40,
            )

    def test_rgba_png_integration(self):
        try:
            from osgeo import gdal, osr
        except ImportError:
            self.skipTest("GDAL runtime unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "rgba.tif"
            ds = gdal.GetDriverByName("GTiff").Create(
                str(src), 256, 256, 4, gdal.GDT_Byte
            )
            h = HALF_WORLD
            ds.SetGeoTransform((-h, h / 256, 0, h, 0, -h / 256))
            crs = osr.SpatialReference()
            crs.ImportFromEPSG(3857)
            ds.SetProjection(crs.ExportToWkt())
            for i, value in enumerate((180, 90, 45, 255), 1):
                ds.GetRasterBand(i).Fill(value)
            ds.GetRasterBand(4).SetColorInterpretation(gdal.GCI_AlphaBand)
            ds.GetRasterBand(4).WriteArray(
                np.zeros((128, 256), dtype="uint8"), 0, 128
            )
            ds = None
            result = write_xyz(
                src,
                root / "tiles",
                dict(xyz_min_zoom=1, xyz_max_zoom=1),
                gdal,
                osr,
            )
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["written_tiles"], 1)
            tile = gdal.Open(str(root / "tiles/1/0/0.png"))
            self.assertEqual(
                (tile.RasterXSize, tile.RasterYSize, tile.RasterCount),
                (256, 256, 4),
            )
            pixels = tile.ReadAsArray()
            np.testing.assert_array_equal(pixels[:3, 10, 10], [180, 90, 45])
            self.assertEqual(pixels[3, 10, 10], 255)
            self.assertEqual(pixels[3, 200, 10], 0)
            tile = None
            with self.assertRaises(ValueError):
                write_xyz(
                    src,
                    root / "limited",
                    dict(xyz_min_zoom=1, xyz_max_zoom=2, xyz_max_tiles=1),
                    gdal,
                    osr,
                )
            self.assertFalse((root / "limited").exists())

    def test_rgba_webp_lossless_integration(self):
        try:
            from osgeo import gdal, osr
        except ImportError:
            self.skipTest("GDAL runtime unavailable")
        if gdal.GetDriverByName("WEBP") is None:
            self.skipTest("GDAL WEBP driver unavailable in this environment")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "rgba.tif"
            ds = gdal.GetDriverByName("GTiff").Create(
                str(src), 256, 256, 4, gdal.GDT_Byte
            )
            h = HALF_WORLD
            ds.SetGeoTransform((-h, h / 256, 0, h, 0, -h / 256))
            crs = osr.SpatialReference()
            crs.ImportFromEPSG(3857)
            ds.SetProjection(crs.ExportToWkt())
            for i, value in enumerate((180, 90, 45, 255), 1):
                ds.GetRasterBand(i).Fill(value)
            ds.GetRasterBand(4).SetColorInterpretation(gdal.GCI_AlphaBand)
            ds.GetRasterBand(4).WriteArray(
                np.zeros((128, 256), dtype="uint8"), 0, 128
            )
            ds = None
            result = write_xyz(
                src,
                root / "tiles",
                dict(xyz_min_zoom=1, xyz_max_zoom=1, xyz_format="webp"),
                gdal,
                osr,
            )
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["format"], "webp")
            self.assertEqual(result["template"], "{z}/{x}/{y}.webp")
            tile = gdal.Open(str(root / "tiles/1/0/0.webp"))
            self.assertEqual(
                (tile.RasterXSize, tile.RasterYSize, tile.RasterCount),
                (256, 256, 4),
            )
            pixels = tile.ReadAsArray()
            # Lossless: decoded pixels must match the source exactly (handover
            # doc 5.2).
            np.testing.assert_array_equal(pixels[:3, 10, 10], [180, 90, 45])
            self.assertEqual(pixels[3, 10, 10], 255)
            self.assertEqual(pixels[3, 200, 10], 0)
            tile = None

    def test_rgba_webp_lossy_integration(self):
        try:
            from osgeo import gdal, osr
        except ImportError:
            self.skipTest("GDAL runtime unavailable")
        if gdal.GetDriverByName("WEBP") is None:
            self.skipTest("GDAL WEBP driver unavailable in this environment")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "rgba.tif"
            ds = gdal.GetDriverByName("GTiff").Create(
                str(src), 256, 256, 4, gdal.GDT_Byte
            )
            h = HALF_WORLD
            ds.SetGeoTransform((-h, h / 256, 0, h, 0, -h / 256))
            crs = osr.SpatialReference()
            crs.ImportFromEPSG(3857)
            ds.SetProjection(crs.ExportToWkt())
            for i, value in enumerate((180, 90, 45, 255), 1):
                ds.GetRasterBand(i).Fill(value)
            ds.GetRasterBand(4).SetColorInterpretation(gdal.GCI_AlphaBand)
            ds.GetRasterBand(4).WriteArray(
                np.zeros((128, 256), dtype="uint8"), 0, 128
            )
            ds = None
            result = write_xyz(
                src,
                root / "tiles",
                dict(
                    xyz_min_zoom=1,
                    xyz_max_zoom=1,
                    xyz_format="webp",
                    xyz_webp_lossless=False,
                    xyz_webp_quality=40,
                ),
                gdal,
                osr,
            )
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["format"], "webp")
            self.assertEqual(result["encoder"]["lossless"], False)
            self.assertEqual(result["encoder"]["quality"], 40)
            tile = gdal.Open(str(root / "tiles/1/0/0.webp"))
            self.assertEqual(
                (tile.RasterXSize, tile.RasterYSize, tile.RasterCount),
                (256, 256, 4),
            )
            pixels = tile.ReadAsArray()
            # 非可逆(lossy)のため画素完全一致は保証しないが、無地の単色領域はJPEG系圧縮でも
            # ほぼ復元されるはずで、大きくかけ離れないことだけを確認する（許容差20）。
            self.assertLess(abs(int(pixels[0, 10, 10]) - 180), 20)
            self.assertLess(abs(int(pixels[1, 10, 10]) - 90), 20)
            self.assertLess(abs(int(pixels[2, 10, 10]) - 45), 20)
            tile = None

    def test_webp_driver_missing_raises_and_writes_no_output(self):
        try:
            from osgeo import gdal, osr
        except ImportError:
            self.skipTest("GDAL runtime unavailable")
        if gdal.GetDriverByName("WEBP") is not None:
            self.skipTest(
                "GDAL WEBP driver is available; miss"
                "ing-driver path not exercised here"
            )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "rgba.tif"
            ds = gdal.GetDriverByName("GTiff").Create(
                str(src), 256, 256, 4, gdal.GDT_Byte
            )
            h = HALF_WORLD
            ds.SetGeoTransform((-h, h / 256, 0, h, 0, -h / 256))
            crs = osr.SpatialReference()
            crs.ImportFromEPSG(3857)
            ds.SetProjection(crs.ExportToWkt())
            ds = None
            with self.assertRaises(RuntimeError):
                write_xyz(
                    src,
                    root / "tiles",
                    dict(xyz_min_zoom=1, xyz_max_zoom=1, xyz_format="webp"),
                    gdal,
                    osr,
                )
            self.assertFalse((root / "tiles").exists())


if __name__ == "__main__":
    unittest.main()


class MbtilesTests(unittest.TestCase):
    def test_tile_row_is_tms_flipped(self):
        from csmap_sheets.engine.xyz_tiles import mbtiles_tile_row

        self.assertEqual(mbtiles_tile_row(0, 0), 0)
        self.assertEqual(mbtiles_tile_row(1, 0), 1)
        self.assertEqual(mbtiles_tile_row(1, 1), 0)
        self.assertEqual(mbtiles_tile_row(12, 100), (1 << 12) - 1 - 100)

    def test_validate_accepts_mbtiles(self):
        validate_xyz({**DEFAULTS, "xyz_format": "mbtiles"})

    def test_writer_finalize_and_abort(self):
        import sqlite3

        from csmap_sheets.engine.xyz_tiles import MbtilesWriter

        meta = {"name": "x", "format": "png", "bounds": "0,0,1,1"}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            writer = MbtilesWriter(root / "a.mbtiles", meta)
            writer.add(1, 0, 0, b"\x89PNG\r\n\x1a\nfake")
            writer.finalize()
            final = root / "a.mbtiles"
            self.assertTrue(final.exists())
            self.assertFalse((root / "a.mbtiles.part").exists())
            conn = sqlite3.connect(str(final))
            rows = conn.execute(
                "SELECT zoom_level, tile_column, tile_row FROM tiles"
            ).fetchall()
            self.assertEqual(rows, [(1, 0, 1)])
            stored = dict(conn.execute("SELECT name, value FROM metadata"))
            self.assertEqual(stored["format"], "png")
            conn.close()
            writer2 = MbtilesWriter(root / "b.mbtiles", meta)
            writer2.add(1, 0, 0, b"\x89PNG\r\n\x1a\nfake")
            writer2.abort()
            self.assertFalse((root / "b.mbtiles").exists())
            self.assertFalse((root / "b.mbtiles.part").exists())

    def _world_source(self, root, gdal, osr):
        src = root / "rgba.tif"
        ds = gdal.GetDriverByName("GTiff").Create(
            str(src), 256, 256, 4, gdal.GDT_Byte
        )
        h = HALF_WORLD
        ds.SetGeoTransform((-h, h / 256, 0, h, 0, -h / 256))
        crs = osr.SpatialReference()
        crs.ImportFromEPSG(3857)
        ds.SetProjection(crs.ExportToWkt())
        for i, value in enumerate((180, 90, 45, 255), 1):
            ds.GetRasterBand(i).Fill(value)
        ds.GetRasterBand(4).SetColorInterpretation(gdal.GCI_AlphaBand)
        ds.GetRasterBand(4).WriteArray(
            np.zeros((128, 256), dtype="uint8"), 0, 128
        )
        ds = None
        return src

    def test_rgba_mbtiles_integration(self):
        import sqlite3

        from csmap_sheets.engine.xyz_tiles import (
            mbtiles_tile_row,
            tile_bounds,
        )

        try:
            from osgeo import gdal, osr
        except ImportError:
            self.skipTest("GDAL runtime unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Source covering exactly one z10 tile over Japan.
            z, tx, ty = 10, 906, 403
            west, south, east, north = tile_bounds(z, tx, ty)
            src = root / "rgba.tif"
            ds = gdal.GetDriverByName("GTiff").Create(
                str(src), 256, 256, 4, gdal.GDT_Byte
            )
            ds.SetGeoTransform(
                (west, (east - west) / 256, 0,
                 north, 0, -(north - south) / 256)
            )
            crs = osr.SpatialReference()
            crs.ImportFromEPSG(3857)
            ds.SetProjection(crs.ExportToWkt())
            for i, value in enumerate((180, 90, 45, 255), 1):
                ds.GetRasterBand(i).Fill(value)
            ds.GetRasterBand(4).SetColorInterpretation(gdal.GCI_AlphaBand)
            ds.GetRasterBand(4).WriteArray(
                np.zeros((128, 256), dtype="uint8"), 0, 128
            )
            ds = None
            result = write_xyz(
                src,
                root / "tiles",
                dict(xyz_min_zoom=z, xyz_max_zoom=z,
                     xyz_format="mbtiles"),
                gdal,
                osr,
            )
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["format"], "mbtiles")
            self.assertEqual(result["written_tiles"], 1)
            mbtiles = root / "tiles/cs_relief.mbtiles"
            self.assertTrue(mbtiles.exists())
            self.assertFalse((root / "tiles/cs_relief.mbtiles.part").exists())
            conn = sqlite3.connect(str(mbtiles))
            rows = conn.execute(
                "SELECT zoom_level, tile_column, tile_row, tile_data"
                " FROM tiles"
            ).fetchall()
            self.assertEqual(len(rows), 1)
            rz, rx, row, blob = rows[0]
            # Stored row is TMS: flipped against the XYZ y.
            self.assertEqual((rz, rx, row),
                             (z, tx, mbtiles_tile_row(z, ty)))
            self.assertEqual(blob[:8], b"\x89PNG\r\n\x1a\n")
            meta = dict(conn.execute("SELECT name, value FROM metadata"))
            conn.close()
            self.assertEqual(meta["format"], "png")
            self.assertEqual(meta["type"], "baselayer")
            self.assertEqual(meta["minzoom"], str(z))
            self.assertEqual(meta["maxzoom"], str(z))
            # metadata bounds are the tile's WGS84 bounds.
            import math

            radius = 6378137.0
            exp = (
                math.degrees(west / radius),
                math.degrees(math.atan(math.sinh(south / radius))),
                math.degrees(east / radius),
                math.degrees(math.atan(math.sinh(north / radius))),
            )
            bounds = [float(v) for v in meta["bounds"].split(",")]
            for got, want in zip(bounds, exp):
                self.assertAlmostEqual(got, want, places=4)
            # The stored tile decodes as a 256x256 RGBA PNG.
            Path(root / "tile.png").write_bytes(bytes(blob))
            tile = gdal.Open(str(root / "tile.png"))
            self.assertEqual(
                (tile.RasterXSize, tile.RasterYSize, tile.RasterCount),
                (256, 256, 4),
            )
            pixels = tile.ReadAsArray()
            np.testing.assert_array_equal(pixels[:3, 10, 10], [180, 90, 45])
            self.assertEqual(pixels[3, 10, 10], 255)
            self.assertEqual(pixels[3, 200, 10], 0)
            tile = None

    def test_mbtiles_tile_set_matches_folder_output(self):
        try:
            from osgeo import gdal, osr
        except ImportError:
            self.skipTest("GDAL runtime unavailable")
        import sqlite3

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = self._world_source(root, gdal, osr)
            write_xyz(
                src, root / "folder",
                dict(xyz_min_zoom=1, xyz_max_zoom=2),
                gdal, osr,
            )
            folder_tiles = {
                (int(p.parts[-3]), int(p.parts[-2]),
                 int(p.stem))
                for p in (root / "folder").rglob("*.png")
            }
            result = write_xyz(
                src, root / "mb",
                dict(xyz_min_zoom=1, xyz_max_zoom=2,
                     xyz_format="mbtiles"),
                gdal, osr,
            )
            conn = sqlite3.connect(str(root / "mb/cs_relief.mbtiles"))
            stored = conn.execute(
                "SELECT zoom_level, tile_column, tile_row FROM tiles"
            ).fetchall()
            conn.close()
            mb_tiles = {
                (z, x, (1 << z) - 1 - row) for z, x, row in stored
            }
            self.assertEqual(mb_tiles, folder_tiles)
            self.assertEqual(result["written_tiles"], len(folder_tiles))
