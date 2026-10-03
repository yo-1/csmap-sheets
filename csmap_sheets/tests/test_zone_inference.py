import struct
import tempfile
import unittest
from pathlib import Path

from csmap_sheets.engine import zone_inference as zi


def las_bytes(version=(1, 2), vlrs=(), evlrs=()):
    """VLR/EVLRだけを持つ最小のLASヘッダー（点データは無し）。"""
    header_size = 375 if version >= (1, 4) else 227
    head = bytearray(header_size)
    head[0:4] = b'LASF'
    head[24], head[25] = version
    struct.pack_into('<H', head, 94, header_size)
    struct.pack_into('<I', head, 100, len(vlrs))
    body = bytearray()
    for user_id, record_id, data in vlrs:
        vh = bytearray(54)
        vh[2:2+len(user_id)] = user_id
        struct.pack_into('<HH', vh, 18, record_id, len(data))
        body += vh + data
    struct.pack_into('<I', head, 96, header_size+len(body))
    out = head + body
    if evlrs:
        struct.pack_into('<QI', out, 235, len(out), len(evlrs))
        for user_id, record_id, data in evlrs:
            eh = bytearray(60)
            eh[2:2+len(user_id)] = user_id
            struct.pack_into('<H', eh, 18, record_id)
            struct.pack_into('<Q', eh, 20, len(data))
            out += eh + data
    return bytes(out)


def geokeys(epsg):
    return struct.pack('<8H', 1, 1, 0, 1, 3072, 0, 1, epsg)


class FakeSRS:
    def __init__(self):
        self.value = None
    def SetFromUserInput(self, value):
        self.value = value
        return 0
    def ImportFromEPSG(self, code):
        self.value = 'EPSG:%d' % code
        return 0
    def ExportToWkt(self):
        return 'WKT(%s)' % self.value


class FakeOSR:
    SpatialReference = FakeSRS


def fake_zone_of(srs):
    """'EPSG:66xx'（JGD2011の平面直角座標系）と'JPR8'だけを系として扱う簡易版。"""
    value = srs.value or ''
    if value.startswith('EPSG:') and 6669 <= int(value[5:]) <= 6687:
        return int(value[5:]) - 6668
    if value.startswith('JPR'):
        return int(value[3:])
    return None


LEM_META = ('東西方向の点数,3\n南北方向の点数,2\n東西方向のデータ間隔,1\n南北方向のデータ間隔,1\n'
            '区画左下X座標,0\n区画左下Y座標,0\n区画右上X座標,200\n区画右上Y座標,300\n平面直角座標系番号,{zone}\n')


class LasCrsTests(unittest.TestCase):
    def write(self, tmp, name, data):
        path = Path(tmp)/name
        path.write_bytes(data)
        return path

    def test_geokey_directory_epsg(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write(tmp, 'a.las', las_bytes(vlrs=[(b'LASF_Projection', 34735, geokeys(6676))]))
            self.assertEqual(zi.read_las_crs(path), ('epsg', 6676))

    def test_las14_wkt_in_evlr_and_vlr(self):
        with tempfile.TemporaryDirectory() as tmp:
            wkt = 'PROJCRS["JGD2011 / Japan Plane Rectangular CS VIII"]'.encode() + b'\0'
            path = self.write(tmp, 'b.laz', las_bytes((1, 4), evlrs=[(b'LASF_Projection', 2112, wkt)]))
            self.assertEqual(zi.read_las_crs(path)[0], 'wkt')
            self.assertIn('VIII', zi.read_las_crs(path)[1])
            path = self.write(tmp, 'c.las', las_bytes((1, 4), vlrs=[(b'LASF_Projection', 2112, wkt)]))
            self.assertEqual(zi.read_las_crs(path)[0], 'wkt')

    def test_no_crs_and_not_las(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(zi.read_las_crs(self.write(tmp, 'd.las', las_bytes())))
            with self.assertRaises(ValueError):
                zi.read_las_crs(self.write(tmp, 'e.las', b'not a las file' * 30))


class InferTargetCrsTests(unittest.TestCase):
    def infer(self, mode, input_crs='', paths=(), recursive=True):
        return zi.infer_target_crs(mode, input_crs, [str(p) for p in paths], recursive, FakeOSR, fake_zone_of)

    def test_input_crs_in_jpr_zone_is_used(self):
        wkt, reason = self.infer('text', 'JPR8')
        self.assertEqual(wkt, 'JPR8')
        self.assertIn('第VIII系', reason)

    def test_input_crs_not_jpr_is_rejected(self):
        wkt, reason = self.infer('text', 'EPSG:4326')
        self.assertIsNone(wkt)
        self.assertIn('平面直角座標系', reason)

    def test_missing_input_crs_for_text_and_gsi(self):
        self.assertIsNone(self.infer('text')[0])
        wkt, reason = self.infer('gsi')
        self.assertIsNone(wkt)
        self.assertIn('国土地理院DEM', reason)

    def test_lidar_header_zone(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ('a.las', 'b.laz'):
                (Path(tmp)/name).write_bytes(las_bytes(vlrs=[(b'LASF_Projection', 34735, geokeys(6676))]))
            wkt, reason = self.infer('lidar', paths=[tmp])
            self.assertEqual(wkt, 'WKT(EPSG:6676)')
            self.assertIn('第VIII系', reason)
            self.assertIn('2件', reason)

    def test_lidar_mixed_zones_or_missing_crs_not_guessed(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp)/'a.las').write_bytes(las_bytes(vlrs=[(b'LASF_Projection', 34735, geokeys(6676))]))
            (Path(tmp)/'b.las').write_bytes(las_bytes(vlrs=[(b'LASF_Projection', 34735, geokeys(6677))]))
            wkt, reason = self.infer('lidar', paths=[tmp])
            self.assertIsNone(wkt)
            self.assertIn('複数の系', reason)
            (Path(tmp)/'b.las').write_bytes(las_bytes())
            wkt, reason = self.infer('lidar', paths=[tmp])
            self.assertIsNone(wkt)
            self.assertIn('座標系の記録がありません', reason)

    def test_lidar_same_zone_different_datum_not_guessed(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp)/'a.las').write_bytes(las_bytes(vlrs=[(b'LASF_Projection', 34735, geokeys(6676))]))
            (Path(tmp)/'b.las').write_bytes(las_bytes((1, 4), vlrs=[(b'LASF_Projection', 2112, b'JPR8\0')]))
            wkt, reason = self.infer('lidar', paths=[tmp])
            self.assertIsNone(wkt)
            self.assertIn('測地系', reason)

    def test_lidar_input_crs_takes_precedence(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp)/'a.las').write_bytes(las_bytes())
            self.assertEqual(self.infer('lidar', 'JPR9', [tmp])[0], 'JPR9')

    def test_forest_lem_zone_checks_input_crs(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp)/'09LE001.csv').write_text(LEM_META.format(zone=9), encoding='cp932')
            self.assertEqual(self.infer('forest', 'JPR9', [tmp])[0], 'JPR9')
            wkt, reason = self.infer('forest', 'JPR8', [tmp])
            self.assertIsNone(wkt)
            self.assertIn('第IX系', reason)
            self.assertIn('第VIII系', reason)

    def test_forest_lem_zone_without_input_crs_suggests_epsg(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp)/'09LE001.csv').write_text(LEM_META.format(zone=8), encoding='cp932')
            wkt, reason = self.infer('forest', paths=[tmp])
            self.assertIsNone(wkt)
            self.assertIn('EPSG:6676', reason)
            self.assertIn('EPSG:2450', reason)

    def test_forest_lem_mixed_zones(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp)/'a.csv').write_text(LEM_META.format(zone=8), encoding='cp932')
            (Path(tmp)/'b.csv').write_text(LEM_META.format(zone=9), encoding='cp932')
            wkt, reason = self.infer('forest', paths=[tmp])
            self.assertIsNone(wkt)
            self.assertIn('複数', reason)

    def test_probe_limit_and_non_recursive(self):
        with tempfile.TemporaryDirectory() as tmp:
            sub = Path(tmp)/'sub'
            sub.mkdir()
            (sub/'a.las').write_bytes(las_bytes(vlrs=[(b'LASF_Projection', 34735, geokeys(6676))]))
            self.assertIsNone(self.infer('lidar', paths=[tmp], recursive=False)[0])
            self.assertIsNotNone(self.infer('lidar', paths=[tmp], recursive=True)[0])
            files = [Path(tmp)/f'{i:03d}.las' for i in range(zi.PROBE_FILE_LIMIT+5)]
            for f in files:
                f.write_bytes(b'')
            self.assertEqual(len(zi._iter_files([tmp], zi.LAS_EXTENSIONS, True)), zi.PROBE_FILE_LIMIT)


class RealOsrTests(unittest.TestCase):
    def test_jgd2011_and_jgd2000_zone_viii(self):
        try:
            from osgeo import osr
        except ImportError:
            self.skipTest('GDAL runtime unavailable')
        from csmap_sheets.engine.pipeline import _jpr_zone_of
        jgd2011, jgd2000 = zi.suggested_epsg(8)
        for code in (jgd2011, jgd2000):
            srs = osr.SpatialReference()
            self.assertEqual(srs.ImportFromEPSG(code), 0)
            self.assertEqual(_jpr_zone_of(srs), 8)


if __name__ == '__main__':
    unittest.main()
