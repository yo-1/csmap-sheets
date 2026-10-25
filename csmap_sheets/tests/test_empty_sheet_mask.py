"""T3: empty masked edge sheets must not abort usable map-sheet output."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from csmap_sheets.engine import pipeline
from csmap_sheets.engine.map_sheets import intersecting_sheets


class Feedback:
    def __init__(self):
        self.warnings = []

    def isCanceled(self):
        return False

    def pushInfo(self, message):
        pass

    def setProgress(self, value):
        pass

    def pushWarning(self, message):
        self.warnings.append(message)


@unittest.skipUnless(
    importlib.util.find_spec("osgeo"), "GDAL is not installed"
)
class EmptySheetMaskTests(unittest.TestCase):
    def setUp(self):
        from osgeo import gdal, osr
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "dem.tif"
        self.out = self.root / "out"
        # Geometry reported by Muse; synthetic elevations, not the Drive file.
        yy, xx = np.mgrid[:322, :822]
        z = (100 + xx * .05 + yy * .03).astype("float32")
        z[150:155, 400:405] = pipeline.NODATA
        ds = gdal.GetDriverByName("GTiff").Create(
            str(self.source), 822, 322, 1, gdal.GDT_Float32
        )
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(6677)
        ds.SetProjection(srs.ExportToWkt())
        ds.SetGeoTransform((-11, 1, 0, 11, 0, -1))
        ds.GetRasterBand(1).SetNoDataValue(pipeline.NODATA)
        ds.GetRasterBand(1).WriteArray(z)
        ds = None
        self.c = pipeline.validate_config(dict(
            inputs=[str(self.source)], output_dir=str(self.out),
            target_crs="EPSG:6677", plane_zone=9, sheet_level=500,
            cell_size=1, sigma_m=2.5, block_size=128,
            confirm_elevation_metres=True, xyz_enabled=False,
        ), self.root)
        self.feedback = Feedback()

    def manifest(self):
        return json.loads((self.out / "run.json").read_text())

    def test_sliver_continues_and_indexes_only_written_sheets(self):
        from osgeo import gdal, ogr
        pipeline.run(dict(self.c, xyz_enabled=True, xyz_min_zoom=12,
                          xyz_max_zoom=12),
                     self.feedback, profile_warnings=["old v4"])
        m = self.manifest()
        self.assertEqual(m["status"], "completed")
        self.assertEqual(m["profile_warnings"], ["old v4"])
        self.assertEqual(m["xyz"]["status"], "completed")
        self.assertTrue(list((self.out / "xyz").rglob("*.png")))
        s = m["sheets"]
        self.assertTrue(s["partial_success"])
        self.assertGreater(s["written"], 0)
        self.assertEqual(s["skipped_empty"], len(s["skipped"]))
        self.assertIn(dict(sheet_code="09JD9999",
                           reason="no_valid_relief_pixels_after_mask"),
                      s["skipped"])
        self.assertTrue(any("09JD9999" in w for w in self.feedback.warnings))
        written = list((self.out / "sheets").glob("*.tif"))
        self.assertEqual(len(written), s["written"])
        index = ogr.Open(str(self.out / "sheet_index.gpkg"))
        self.assertEqual(index.GetLayer(0).GetFeatureCount(), s["written"])
        index = None
        for item in s["skipped"]:
            stem = self.out / "sheets" / item["sheet_code"]
            self.assertFalse(stem.with_suffix(".tif").exists())
            self.assertFalse(stem.with_suffix(".tfw").exists())
        self.assertFalse((self.out / "sheet_work").exists())
        vrt = gdal.Open(str(self.out / "cs_relief.vrt"))
        self.assertEqual(len([p for p in vrt.GetFileList()
                              if p.endswith(".tif")]), s["written"])
        vrt = None
        ds = gdal.Open(str(self.out / "cs_relief_merged.tif"))
        self.assertGreater(
            np.count_nonzero(ds.GetRasterBand(4).ReadAsArray()), 0
        )
        ds = None

    def test_all_masked_fails_and_retains_summary(self):
        candidates = list(intersecting_sheets((-11, -311, 811, 11), 9, 500))
        sliver = next(
            s for s in candidates if s.code == "09JD9999"
        )
        with patch.object(
            pipeline, "intersecting_sheets", return_value=[sliver]
        ):
            with self.assertRaisesRegex(ValueError, "No nonempty sheets"):
                pipeline.run(self.c, self.feedback)
        m = self.manifest()
        self.assertEqual(m["status"], "failed")
        self.assertEqual(m["sheets"]["written"], 0)
        self.assertFalse(m["sheets"]["partial_success"])
        self.assertEqual(m["sheets"]["skipped"][0]["sheet_code"], "09JD9999")
        self.assertFalse((self.out / "cs_relief.vrt").exists())
        self.assertFalse((self.out / "cs_relief_merged.tif").exists())

    def test_unrelated_value_error_is_not_skipped(self):
        with patch.object(pipeline, "make_relief",
                          side_effect=ValueError("broken raster read")):
            with self.assertRaisesRegex(ValueError, "broken raster read"):
                pipeline.run(self.c, self.feedback)
        self.assertEqual(self.manifest()["status"], "failed")
        self.assertEqual(self.manifest()["sheets"]["skipped_empty"], 0)

    def test_corrupt_dem_fails_as_input_error(self):
        self.source.write_bytes(b"not a raster")
        with self.assertRaises(Exception):
            pipeline.run(self.c, self.feedback)
        self.assertEqual(self.manifest()["status"], "failed")
        self.assertNotIn("sheets", self.manifest())

    def test_boundary_completion_writes_sliver(self):
        pipeline.run(dict(self.c, nodata_edge_mode="pss_approximation"),
                     self.feedback)
        m = self.manifest()
        self.assertEqual(m["status"], "completed")
        self.assertTrue((self.out / "sheets" / "09JD9999.tif").exists())
        self.assertNotIn("no_valid_relief_pixels_after_mask",
                         [s["reason"] for s in m["sheets"]["skipped"]])

    def test_cancellation_is_not_skipped(self):
        from csmap_sheets.engine.progress import CancelledError
        with patch.object(pipeline, "make_relief",
                          side_effect=CancelledError("stop")):
            with self.assertRaises(CancelledError):
                pipeline.run(self.c, self.feedback)
        self.assertEqual(self.manifest()["status"], "cancelled")
        self.assertEqual(self.manifest()["sheets"]["skipped_empty"], 0)

    def test_warp_failure_is_not_skipped(self):
        from osgeo import gdal, ogr, osr
        self.out.mkdir()
        summary = {}
        with patch.object(gdal, "Warp", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "DEM warp failed"):
                pipeline.render_sheets(self.source, self.out, self.c,
                                       gdal, ogr, osr, self.feedback, summary)
        self.assertEqual(summary["skipped_empty"], 0)
