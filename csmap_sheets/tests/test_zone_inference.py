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


def latlon_to_mesh8(lat, lon):
    p = int(lat*1.5); u = int(lon-100)
    lat_r = lat - p/1.5; lon_r = lon - (u+100)
    q = int(lat_r/(5/60)); v = int(lon_r/(7.5/60))
    lat_r -= q*5/60; lon_r -= v*7.5/60
    r = int(lat_r/(30/3600)); w = int(lon_r/(45/3600))
    return f'{p:02d}{u:02d}{q}{v}{r}{w}'


class ZoneTableTests(unittest.TestCase):
    # 市役所・役場付近の点で、対応表から1つの系が引けること（告示の区分との照合）
    POINTS = [
        ('甲府市', 35.662, 138.568, 8), ('箱根町', 35.232, 139.106, 9), ('札幌市', 43.062, 141.354, 12),
        ('函館市', 41.768, 140.729, 11), ('釧路市', 42.985, 144.381, 13), ('帯広市', 42.923, 143.196, 13),
        ('旭川市', 43.771, 142.365, 12), ('小樽市', 43.190, 140.994, 11),
        ('小笠原村父島', 27.094, 142.192, 14), ('南大東村', 25.829, 131.232, 17),
        ('石垣市', 24.341, 124.156, 16), ('那覇市', 26.212, 127.681, 15),
        ('奄美市名瀬', 28.377, 129.494, 1), ('鹿児島市', 31.596, 130.557, 2),
        ('長崎市', 32.750, 129.877, 1), ('福岡市', 33.590, 130.402, 2), ('松江市', 35.468, 133.048, 3),
        ('高知市', 33.559, 133.531, 4), ('神戸市', 34.690, 135.196, 5), ('京都市', 35.011, 135.768, 6),
        ('名古屋市', 35.181, 136.906, 7), ('新宿区', 35.694, 139.703, 9), ('仙台市', 38.268, 140.872, 10),
    ]

    def test_known_points(self):
        for name, lat, lon, zone in self.POINTS:
            mesh = latlon_to_mesh8(lat, lon)
            self.assertEqual(zi.zones_of_mesh(mesh), {zone}, f'{name} {mesh}')

    def test_table_values_and_unknown(self):
        table = zi.load_zone_table()
        self.assertGreater(len(table), 30000)
        for mesh, zones in table.items():
            self.assertIn(len(mesh), (6, 8))
            self.assertTrue(zones and zones <= set(range(0, 20)), mesh)
        self.assertIsNone(zi.zones_of_mesh('00000000'))
        self.assertIsNone(zi.zones_of_mesh('123'))

    def test_second_mesh_lookup_and_border(self):
        self.assertEqual(zi.zones_of_mesh('533844'), {8})
        # 神奈川県（第IX系）と静岡県・山梨県（第VIII系）の境を含む2次メッシュは複数の系になる
        mixed = [m for m, z in zi.load_zone_table().items() if len(m) == 8 and z == {8, 9}]
        self.assertTrue(mixed)
        self.assertGreaterEqual(len(zi.zones_of_mesh(mixed[0][:6])), 2)

    def test_mesh_from_gsi_name(self):
        self.assertEqual(zi.mesh_from_gsi_name('FG-GML-5338-44-00-DEM1A-20250822.xml'), '53384400')
        self.assertEqual(zi.mesh_from_gsi_name('C:/x/FG-GML-533844-DEM1A-20251113.zip'), '533844')
        self.assertEqual(zi.mesh_from_gsi_name('FG-GML-5338-44-DEM10B-20161001.xml'), '533844')
        self.assertIsNone(zi.mesh_from_gsi_name('dem.xml'))


def gsi_xml(mesh='53384400', srs='fguuid:jgd2011.bl'):
    return (f'<?xml version="1.0" encoding="UTF-8"?><Dataset><DEM><mesh>{mesh}</mesh>'
            f'<gml:Envelope srsName="{srs}"></gml:Envelope></DEM></Dataset>').encode()


class GsiInferenceTests(unittest.TestCase):
    def test_folder_and_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            for i in range(3):
                (Path(tmp)/f'FG-GML-5338-44-0{i}-DEM1A-20250822.xml').write_bytes(gsi_xml(f'5338440{i}'))
            zone, datum, reason = zi.infer_gsi_zone([tmp], True)
            self.assertEqual((zone, datum), (8, 'jgd2011'))
            self.assertIn('第VIII系', reason)
            z = Path(tmp)/'FG-GML-533844-DEM1A-20251113.zip'
            import zipfile
            with zipfile.ZipFile(z, 'w') as archive:
                archive.writestr('FG-GML-5338-44-10-DEM1A-20251113.xml', gsi_xml('53384410', 'fguuid:jgd2024.bl'))
            self.assertEqual(zi.infer_gsi_zone([str(z)], True)[:2], (8, 'jgd2011'))

    def test_jgd2000_and_mixed_datum(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp)/'FG-GML-5338-44-00-DEM5A-2012.xml').write_bytes(gsi_xml(srs='fguuid:jgd2000.bl'))
            self.assertEqual(zi.infer_gsi_zone([tmp], True)[:2], (8, 'jgd2000'))
            (Path(tmp)/'FG-GML-5338-44-01-DEM5A-2020.xml').write_bytes(gsi_xml('53384401'))
            zone, _, reason = zi.infer_gsi_zone([tmp], True)
            self.assertIsNone(zone)
            self.assertIn('混在', reason)

    def test_multiple_zones_and_name_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            kofu = latlon_to_mesh8(35.662, 138.568); tokyo = latlon_to_mesh8(35.694, 139.703)
            (Path(tmp)/'a.xml').write_bytes(gsi_xml(kofu))
            (Path(tmp)/'b.xml').write_bytes(gsi_xml(tokyo))
            zone, _, reason = zi.infer_gsi_zone([tmp], True)
            self.assertIsNone(zone)
            self.assertIn('複数の系', reason)
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp)/'FG-GML-5339-01-00-DEM1A-2025.xml').write_bytes(gsi_xml('53384400'))
            zone, _, reason = zi.infer_gsi_zone([tmp], True)
            self.assertIsNone(zone)
            self.assertIn('一致しません', reason)

    def test_projected_input_crs_rejected_for_gsi(self):
        class GeoSRS(FakeSRS):
            def IsGeographic(self):
                return self.value.startswith('GEO')
        class Osr:
            SpatialReference = GeoSRS
        wkt, reason = zi.infer_target_crs('gsi', 'JPR8', [], True, Osr, fake_zone_of)
        self.assertIsNone(wkt)
        self.assertIn('空欄', reason)
