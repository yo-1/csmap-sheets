"""Standalone DEM export: completion, cancellation, and real GDAL copy."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from csmap_sheets.engine.dem_export import export_merged_dem
from csmap_sheets.engine.pipeline import validate_config
from csmap_sheets.engine.progress import CancelledError


class DemExportTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.root = Path(self.work.name)
        self.destination = self.root / 'dem_merged.tif'
        self.partial = self.root / 'dem_merged.partial.tif'

    def fake_gdal(self, *, fails=False, cancel=None, bands=1):
        result = Mock(RasterCount=bands)
        result.FlushCache.return_value = None

        def translate(path, source, **options):
            Path(path).write_bytes(b'partial-dem')
            if cancel is not None:
                cancel.isCanceled.return_value = True
            return None if fails else result

        return Mock(Translate=Mock(side_effect=translate))

    def test_completed_output_is_published_without_resampling_options(self):
        gdal = self.fake_gdal()
        export_merged_dem('projected_dem.vrt', self.destination, gdal)
        self.assertEqual(self.destination.read_bytes(), b'partial-dem')
        self.assertFalse(self.partial.exists())
        args, kwargs = gdal.Translate.call_args
        self.assertEqual(args[1], 'projected_dem.vrt')
        self.assertEqual(kwargs['format'], 'GTiff')
        self.assertNotIn('resampleAlg', kwargs)
        self.assertNotIn('width', kwargs)
        self.assertNotIn('outputType', kwargs)

    def test_failure_does_not_leave_final_or_partial_output(self):
        with self.assertRaises(RuntimeError):
            export_merged_dem(
                'source.vrt', self.destination, self.fake_gdal(fails=True)
            )
        self.assertFalse(self.destination.exists())
        self.assertFalse(self.partial.exists())

    def test_cancellation_does_not_publish_output(self):
        feedback = Mock()
        feedback.isCanceled.return_value = False
        with self.assertRaises(CancelledError):
            export_merged_dem(
                'source.vrt', self.destination,
                self.fake_gdal(cancel=feedback), feedback,
            )
        self.assertFalse(self.destination.exists())
        self.assertFalse(self.partial.exists())

    def test_existing_file_is_not_replaced(self):
        self.destination.write_bytes(b'original')
        gdal = self.fake_gdal()
        with self.assertRaises(FileExistsError):
            export_merged_dem('source.vrt', self.destination, gdal)
        self.assertEqual(self.destination.read_bytes(), b'original')
        gdal.Translate.assert_not_called()

    def test_wrong_band_count_is_rejected(self):
        with self.assertRaises(ValueError):
            export_merged_dem(
                'rgb.tif', self.destination, self.fake_gdal(bands=4)
            )
        self.assertFalse(self.destination.exists())
        self.assertFalse(self.partial.exists())

    def test_option_is_off_by_default_and_strict_boolean(self):
        dummy = self.root / 'source.tif'
        dummy.touch()
        config = dict(
            inputs=[str(dummy)], output_dir=str(self.root / 'out'),
            target_crs='EPSG:6677', cell_size=1,
            confirm_elevation_metres=True,
        )
        self.assertIs(
            validate_config(config, self.root)['merged_dem_enabled'], False
        )
        enabled = validate_config(
            {**config, 'merged_dem_enabled': True}, self.root
        )
        self.assertIs(enabled['merged_dem_enabled'], True)
        for value in ('yes', 1, None):
            with self.assertRaisesRegex(
                ValueError, 'merged_dem_enabled must be boolean'
            ):
                validate_config(
                    {**config, 'merged_dem_enabled': value}, self.root
                )


@unittest.skipUnless(
    importlib.util.find_spec('osgeo'), 'GDAL is not installed'
)
class RealGdalDemExportTests(unittest.TestCase):
    def test_copy_preserves_elevations_grid_crs_and_nodata(self):
        import numpy as np
        from osgeo import gdal, osr
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            source = root/'source.tif'
            data = np.arange(48, dtype=np.float32).reshape(6, 8)
            data[0, 0] = -999999
            srs = osr.SpatialReference()
            srs.ImportFromEPSG(6677)
            src = gdal.GetDriverByName('GTiff').Create(
                str(source), 8, 6, 1, gdal.GDT_Float32
            )
            src.SetProjection(srs.ExportToWkt())
            src.SetGeoTransform((100, 0.5, 0, 200, 0, -0.5))
            src.GetRasterBand(1).SetNoDataValue(-999999)
            src.GetRasterBand(1).WriteArray(data)
            src = None
            vrt = gdal.BuildVRT(str(root/'projected_dem.vrt'), [str(source)])
            vrt.FlushCache()
            del vrt
            export_merged_dem(
                root / 'projected_dem.vrt', root / 'dem_merged.tif', gdal
            )
            src = gdal.Open(str(source))
            dst = gdal.Open(str(root/'dem_merged.tif'))
            self.assertEqual(dst.RasterCount, 1)
            self.assertEqual(dst.GetGeoTransform(), src.GetGeoTransform())
            self.assertTrue(dst.GetSpatialRef().IsSame(src.GetSpatialRef()))
            self.assertEqual(dst.GetRasterBand(1).GetNoDataValue(), -999999)
            np.testing.assert_array_equal(dst.ReadAsArray(), data)
            src = dst = None
            # The exported elevation raster is independent of the original/VRT.
            source.unlink()
            (root/'projected_dem.vrt').unlink()
            dst = gdal.Open(str(root/'dem_merged.tif'))
            np.testing.assert_array_equal(dst.ReadAsArray(), data)
            dst = None
