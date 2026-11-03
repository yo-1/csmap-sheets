"""Issue #64: optional COG (Cloud Optimized GeoTIFF) output.

Unit tests use a fake GDAL module; the integration tests run only when
GDAL is installed.
"""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from csmap_sheets.engine.pipeline import (
    configuration_defaults,
    read_config,
    run,
    settings_profile,
    merge_settings_profile,
    validate_config,
    write_cog,
)


class CogConfigTests(unittest.TestCase):
    def base_config(self, **overrides):
        work = Path(tempfile.mkdtemp())
        dummy = work / "dummy.tif"
        dummy.write_bytes(b"")
        c = dict(
            inputs=[str(dummy)],
            output_dir=str(work / "out"),
            target_crs="EPSG:6677",
            cell_size=1.0,
            confirm_elevation_metres=True,
        )
        c.update(overrides)
        return c

    def test_default_is_off(self):
        self.assertIs(configuration_defaults()["cog_enabled"], False)
        c = validate_config(self.base_config(), Path.cwd())
        self.assertIs(c["cog_enabled"], False)

    def test_non_bool_rejected(self):
        with self.assertRaises(ValueError):
            validate_config(self.base_config(cog_enabled="yes"), Path.cwd())

    def test_profile_round_trip_keeps_cog_enabled(self):
        saved = settings_profile({**configuration_defaults(),
                                  "cog_enabled": True})
        merged, _ = merge_settings_profile(
            json.loads(json.dumps(saved)), configuration_defaults()
        )
        self.assertIs(merged["cog_enabled"], True)


class _FakeDataset:
    def FlushCache(self):
        pass


class _FakeGdal:
    def __init__(self, has_driver=True):
        self._has_driver = has_driver
        self.translate_calls = []

    def GetDriverByName(self, name):
        assert name == "COG"
        return object() if self._has_driver else None

    def Open(self, path):
        return _FakeDataset()

    def Translate(self, dest, src, format=None, creationOptions=None):
        self.translate_calls.append(
            (dest, format, list(creationOptions or []))
        )
        return _FakeDataset()


class WriteCogTests(unittest.TestCase):
    def test_missing_driver_is_a_clear_error(self):
        with self.assertRaises(RuntimeError) as ctx:
            write_cog(_FakeGdal(has_driver=False),
                      "in.vrt", "out_cog.tif", "DEFLATE")
        self.assertIn("COG", str(ctx.exception))

    def test_creation_options_record_overview_resampling(self):
        fake = _FakeGdal()
        write_cog(fake, "in.vrt", "out_cog.tif", "DEFLATE")
        [(dest, fmt, options)] = fake.translate_calls
        self.assertEqual(dest, "out_cog.tif")
        self.assertEqual(fmt, "COG")
        self.assertIn("COMPRESS=DEFLATE", options)
        self.assertIn("OVERVIEW_RESAMPLING=NEAREST", options)


@unittest.skipUnless(
    importlib.util.find_spec("osgeo"), "GDAL is not installed"
)
class CogIntegrationTests(unittest.TestCase):
    def _run_sample(self, root, **overrides):
        from osgeo import gdal, osr

        srs = osr.SpatialReference()
        srs.ImportFromEPSG(6677)
        for i in range(2):
            ds = gdal.GetDriverByName("GTiff").Create(
                str(root / f"dem_{i}.tif"), 96, 96, 1, gdal.GDT_Float32
            )
            ds.SetProjection(srs.ExportToWkt())
            ds.SetGeoTransform((i * 96 - 96, 1, 0, 0, 0, -1))
            import numpy as np

            yy, xx = np.mgrid[:96, :96]
            ds.GetRasterBand(1).WriteArray(
                (100 + (xx + i * 96) * 0.2 + yy * 0.1).astype("float32")
            )
            ds.GetRasterBand(1).SetNoDataValue(-9999)
            ds = None
        config = dict(
            inputs=[str(root / "dem_*.tif")],
            output_dir=str(root / "result"),
            target_crs="EPSG:6677",
            merged_dem_enabled=True,
            cell_size=1,
            sigma_m=2,
            plane_zone=9,
            sheet_level=500,
            confirm_elevation_metres=True,
        )
        config.update(overrides)
        path = root / "config.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        run(read_config(path))
        return json.loads(
            (root / "result/run.json").read_text(encoding="utf-8")
        )

    def test_cog_written_and_matches_merged(self):
        from osgeo import gdal
        import numpy as np

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = self._run_sample(root, cog_enabled=True)
            cog_path = root / "result/cs_relief_merged_cog.tif"
            self.assertTrue(cog_path.exists())
            self.assertEqual(
                manifest["cs_cog_geotiff"], "cs_relief_merged_cog.tif"
            )
            cog = gdal.Open(str(cog_path))
            self.assertEqual(
                cog.GetMetadata("IMAGE_STRUCTURE").get("LAYOUT"), "COG"
            )
            merged = gdal.Open(str(root / "result/cs_relief_merged.tif"))
            self.assertEqual(cog.RasterCount, merged.RasterCount)
            for band in range(1, cog.RasterCount + 1):
                np.testing.assert_array_equal(
                    cog.GetRasterBand(band).ReadAsArray(),
                    merged.GetRasterBand(band).ReadAsArray(),
                )

    def test_cog_off_by_default(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = self._run_sample(root)
            self.assertFalse(
                (root / "result/cs_relief_merged_cog.tif").exists()
            )
            self.assertIsNone(manifest["cs_cog_geotiff"])

    def test_cog_independent_of_merged_geotiff(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = self._run_sample(
                root, cog_enabled=True, merged_geotiff_enabled=False
            )
            self.assertTrue(
                (root / "result/cs_relief_merged_cog.tif").exists()
            )
            self.assertFalse((root / "result/cs_relief_merged.tif").exists())
            self.assertIsNone(manifest["cs_merged_geotiff"])


if __name__ == "__main__":
    unittest.main()
