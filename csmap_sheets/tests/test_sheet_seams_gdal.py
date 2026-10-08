"""C1: actual buffered Warp/render/crop versus joint render on adjacent sheets."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from csmap_sheets.engine.pipeline import (validate_config, gaussian_sigma,
                                         make_relief, render_sheets, NODATA)
from csmap_sheets.engine.map_sheets import sheet_at


@unittest.skipUnless(importlib.util.find_spec('osgeo'), 'GDAL is not installed')
class SheetSeamsGdalTests(unittest.TestCase):
    def test_adjacent_sheets_warp_render_crop_matches_joint(self):
        from osgeo import gdal, ogr, osr
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root/'dem.tif'
            source.touch()
            c = validate_config(dict(inputs=[str(source)], output_dir=str(root/'out'),
                target_crs='EPSG:6677', cell_size=1., plane_zone=9, sheet_level=500,
                sigma_m=2.5, block_size=128, confirm_elevation_metres=True), root)
            halo = gaussian_sigma(c)[1]+1
            width, height = 800+2*halo, 300+2*halo
            yy, xx = np.mgrid[:height, :width]
            z = (100 + .2*xx + .1*yy + 4*np.sin(xx/7.)*np.cos(yy/9.)).astype('float32')
            # A hole crosses the shared map-sheet boundary.
            z[halo+140:halo+145, halo+398:halo+403] = NODATA
            srs = osr.SpatialReference(); srs.ImportFromEPSG(6677)
            ds = gdal.GetDriverByName('GTiff').Create(str(source), width, height, 1, gdal.GDT_Float32)
            ds.SetProjection(srs.ExportToWkt())
            ds.SetGeoTransform((-halo, 1., 0., halo, 0., -1.))
            ds.GetRasterBand(1).SetNoDataValue(NODATA)
            ds.GetRasterBand(1).WriteArray(z); ds = None
            sheets = [sheet_at(200., -150., 9, 500), sheet_at(600., -150., 9, 500)]
            for mode in ('safe_mask', 'pss_approximation'):
                for slope in ('horn', 'central_difference'):
                    with self.subTest(mode=mode, slope=slope):
                        cfg = dict(c, nodata_edge_mode=mode, slope_algorithm=slope)
                        out = root/(mode+'_'+slope); out.mkdir()
                        joint_path = out/'joint.tif'
                        make_relief(source, joint_path, cfg, gdal)
                        joint_ds = gdal.Open(str(joint_path))
                        expected = joint_ds.ReadAsArray()[:, halo:halo+300, halo:halo+800]
                        joint_ds = None
                        # Only choose these two real sheets, leaving extra source coverage as halo.
                        with patch('csmap_sheets.engine.pipeline.intersecting_sheets', return_value=sheets):
                            render_sheets(source, out, cfg, gdal, ogr, osr)
                        actual_parts = []
                        for sheet in sheets:
                            ds = gdal.Open(str(out/'sheets'/(sheet.code+'.tif')))
                            self.assertEqual(ds.GetGeoTransform(), (sheet.west, 1., 0., sheet.north, 0., -1.))
                            actual_parts.append(ds.ReadAsArray()); ds = None
                        actual = np.concatenate(actual_parts, axis=2)
                        delta = np.abs(actual.astype('int16')-expected.astype('int16'))
                        print('C1_GDAL '+json.dumps(dict(mode=mode, slope=slope,
                            halo=halo, max_rgba_difference=int(delta.max()),
                            changed_pixels=int(np.count_nonzero(np.any(delta, axis=0)))), sort_keys=True))
                        np.testing.assert_array_equal(actual, expected)
                        self.assertTrue((actual[3, 140:145, 398:403] == 0).all())


if __name__ == '__main__':
    unittest.main()
