"""Generate synthetic terrain for GUI acceptance; no survey data is used."""
import argparse
import json
from pathlib import Path

import numpy as np
from osgeo import gdal, osr


def generate(destination):
    root = Path(destination)
    (root / "tiles").mkdir(parents=True, exist_ok=True)
    # Pixel centres: easting/northing in JGD2011 Japan Plane IX (metres).
    west, north, size = -50200.0, -74400.0, 400
    x, y = np.meshgrid(np.arange(size) + 0.5, np.arange(size) + 0.5)
    height = (100 + 55 * np.exp(-((x - 110)**2 + (y - 120)**2) / 4500)
              - 30 * np.exp(-((x - 290)**2 + (y - 280)**2) / 3500)
              + 8 * np.sin(x / 35) * np.cos(y / 45))
    hole = ((x - 210)**2 + (y - 180)**2 < 22**2)
    hole |= (x < 35) & (y > 350)
    height = height.astype(np.float32)
    height[hole] = -9999
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(6677)

    def write(path, data, origin):
        ds = gdal.GetDriverByName("GTiff").Create(
            str(path), data.shape[1], data.shape[0], 1, gdal.GDT_Float32,
            options=["COMPRESS=DEFLATE", "PREDICTOR=3"],
        )
        ds.SetGeoTransform((origin, 1, 0, north, 0, -1))
        ds.SetProjection(srs.ExportToWkt())
        ds.SetMetadataItem("DESCRIPTION", "Synthetic terrain; not survey data")
        ds.GetRasterBand(1).SetNoDataValue(-9999)
        ds.GetRasterBand(1).SetUnitType("m")
        ds.GetRasterBand(1).WriteArray(data)
        ds = None
        reopened = gdal.Open(str(path))
        np.testing.assert_array_equal(
            reopened.GetRasterBand(1).ReadAsArray(), data,
        )
        assert reopened.GetGeoTransform() == (origin, 1, 0, north, 0, -1)
        assert reopened.GetRasterBand(1).GetNoDataValue() == -9999

    write(root / "dem_full.tif", height, west)
    write(root / "tiles" / "dem_west.tif", height[:, :200], west)
    write(root / "tiles" / "dem_east.tif", height[:, 200:], west + 200)
    metadata = {
        "kind": "synthetic, not measured terrain",
        "license": "CC0-1.0",
        "crs": "EPSG:6677",
        "width": size, "height": size, "cell_size_m": 1,
        "bounds_easting_northing": [-50200, -74800, -49800, -74400],
        "nodata": -9999,
        "synthetic_height_unit": "m",
        "vertical_datum": "arbitrary synthetic heights; no real datum",
        "tile_join_easting": -50000,
        "features": "hill, depression, waves, internal hole, missing edge",
        "checks": "both tiles exactly reconstruct dem_full including NoData",
    }
    (root / "sample-info.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metadata, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination")
    generate(parser.parse_args().destination)
