"""出力の平面直角座標系（第I～XIX系）を、ラスター以外の入力から推定する補助関数。

v0.11.0（ユーザー要望、2026-10-03）。推定は「入力が持つ確かな情報」だけを使い、
緯度経度からの近似や最寄りの原点による推測はしない（県境付近で誤るため）。

推定に使う情報（信頼度の高い順）:
1. 画面で指定した「入力の水平座標系」(INPUT_CRS)が平面直角座標系であれば、その系。
2. LAS/LAZ のヘッダー（VLR/EVLR）に記録された座標系が平面直角座標系であれば、その系。
3. 森林航空レーザ成果（LEM）のメタデータの「平面直角座標系番号」は、測地系
   （JGD2000/JGD2011）を区別できないため出力座標系には使わず、1との照合と
   エラー時の案内にだけ使う。

4. 国土地理院DEM（基盤地図情報 数値標高モデル、GML）は、ファイル名とGMLの<mesh>から
   地域メッシュ番号を読み、メッシュ→系の対応表（data/jpr_zone_mesh.csv、総務省統計局の
   市区町村別メッシュ・コード一覧から tools/build_jpr_zone_table.py で作成）で系を決める。
   測地系はGMLのsrsName（JGD2000／JGD2011・JGD2024）で決める。

複数のファイルで系が食い違う場合は推定しない（呼び出し側が明示指定を求める）。
"""
import os
import re
import struct
import zipfile
from pathlib import Path

ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X',
         'XI', 'XII', 'XIII', 'XIV', 'XV', 'XVI', 'XVII', 'XVIII', 'XIX']

# 走査するファイル数の上限。大量のファイルを持つフォルダーでもQGISの主スレッドを
# 長時間止めないため（v0.9.2の「応答なし」の教訓）。先頭からこの件数だけ調べる。
PROBE_FILE_LIMIT = 50

LAS_EXTENSIONS = ('.las', '.laz')
_LASF_PROJECTION = b'LASF_Projection'
_GEOKEY_DIRECTORY = 34735
_OGC_WKT = 2112
_PROJECTED_CS_TYPE_GEOKEY = 3072


def zone_label(zone):
    return f'第{ROMAN[zone-1]}系'


def suggested_epsg(zone):
    """系番号から候補のEPSGコード（JGD2011、JGD2000）を返す（案内表示用）。"""
    return 6668+zone, 2442+zone


def _iter_files(paths, extensions, recursive, limit=PROBE_FILE_LIMIT):
    """paths（ファイルまたはフォルダー）から拡張子が一致するファイルを、名前順に最大limit件返す。"""
    found = []
    for raw in paths:
        path = Path(raw)
        if path.is_file():
            if path.suffix.lower() in extensions:
                found.append(path)
        elif path.is_dir():
            walker = os.walk(path) if recursive else [(str(path), [], os.listdir(path))]
            for root, dirs, files in walker:
                dirs.sort()
                for name in sorted(files):
                    if Path(name).suffix.lower() in extensions:
                        found.append(Path(root)/name)
                        if len(found) >= limit:
                            return found
        if len(found) >= limit:
            break
    return found[:limit]


def read_las_crs(path):
    """LAS/LAZのヘッダーから座標系を読む。点データ（圧縮部分）は読まない。

    戻り値: ('wkt', 文字列) / ('epsg', 整数) / None（座標系の記録が無い）。
    LAS 1.4はOGC WKT（record 2112）をVLRまたはEVLRに、1.0～1.3は主にGeoTIFFの
    GeoKeyDirectory（record 34735）をVLRに持つ。LAZもヘッダーとVLRは非圧縮。
    """
    with open(path, 'rb') as f:
        head = f.read(375)
        if len(head) < 227 or head[:4] != b'LASF':
            raise ValueError('LAS/LAZのヘッダーではありません: '+str(path))
        version = (head[24], head[25])
        header_size = struct.unpack_from('<H', head, 94)[0]
        vlr_count = struct.unpack_from('<I', head, 100)[0]
        records = []
        f.seek(header_size)
        for _ in range(min(vlr_count, 1000)):
            vh = f.read(54)
            if len(vh) < 54:
                break
            user_id = vh[2:18].rstrip(b'\0')
            record_id, length = struct.unpack_from('<HH', vh, 18)
            data = f.read(length)
            records.append((user_id, record_id, data))
        if version >= (1, 4) and len(head) >= 375:
            evlr_start, evlr_count = struct.unpack_from('<QI', head, 235)
            if evlr_start and evlr_count:
                f.seek(evlr_start)
                for _ in range(min(evlr_count, 1000)):
                    eh = f.read(60)
                    if len(eh) < 60:
                        break
                    user_id = eh[2:18].rstrip(b'\0')
                    record_id = struct.unpack_from('<H', eh, 18)[0]
                    length = struct.unpack_from('<Q', eh, 20)[0]
                    if length > 1 << 20:  # 座標系の記録としては大きすぎる。読まずに飛ばす
                        f.seek(length, 1)
                        continue
                    records.append((user_id, record_id, f.read(length)))
    for user_id, record_id, data in records:
        if user_id == _LASF_PROJECTION and record_id == _OGC_WKT:
            text = data.split(b'\0', 1)[0].decode('utf-8', 'replace').strip()
            if text:
                return ('wkt', text)
    for user_id, record_id, data in records:
        if user_id == _LASF_PROJECTION and record_id == _GEOKEY_DIRECTORY and len(data) >= 8:
            values = struct.unpack_from('<%dH' % (len(data)//2), data)
            count = values[3]
            for i in range(count):
                key, location, _, value = values[4+4*i:8+4*i]
                if key == _PROJECTED_CS_TYPE_GEOKEY and location == 0 and value not in (0, 32767):
                    return ('epsg', value)
    return None


def _srs_from(kind, value, osr):
    srs = osr.SpatialReference()
    if kind == 'epsg':
        if srs.ImportFromEPSG(int(value)) != 0:
            raise ValueError('EPSG:%s' % value)
    elif srs.SetFromUserInput(value) != 0:
        raise ValueError('WKT')
    return srs


def _same_crs(a, b):
    same = getattr(a, 'IsSame', None)
    if same is not None:
        return bool(same(b))
    return a.ExportToWkt() == b.ExportToWkt()


def lem_zones(paths, recursive, limit=PROBE_FILE_LIMIT):
    """森林LEMのメタデータから「平面直角座標系番号」を集める。{系番号: [ファイル]} を返す。"""
    from .forest_dem import is_lem_metadata, read_lem_metadata
    zones = {}
    for path in _iter_files(paths, ('.csv', '.txt'), recursive, limit):
        if not is_lem_metadata(path):
            continue
        try:
            zone = read_lem_metadata(path).get('zone')
        except (OSError, ValueError):
            continue
        if isinstance(zone, int) and 1 <= zone <= 19:
            zones.setdefault(zone, []).append(str(path))
    return zones


# ---- 国土地理院DEM（v0.11.0）------------------------------------------------------

ZONE_TABLE = Path(__file__).resolve().parent/'data'/'jpr_zone_mesh.csv'
GSI_HEAD_BYTES = 65536
_GSI_NAME = re.compile(r'FG-GML-(\d{4})-?(\d{2})(?:-(\d{2}))?-DEM', re.I)
_GSI_MESH = re.compile(rb'<(?:[\w.-]+:)?mesh>\s*(\d{6}|\d{8})\s*</', re.I)
_GSI_SRS = re.compile(rb'srsName\s*=\s*["\']([^"\']+)["\']', re.I)
_zone_table = None


def load_zone_table(path=None):
    """メッシュ→系の対応表を読む（初回のみ）。{メッシュ番号: frozenset(系番号)}。"""
    global _zone_table
    if path is None and _zone_table is not None:
        return _zone_table
    table = {}
    with open(path or ZONE_TABLE, encoding='utf-8') as f:
        if f.readline().strip() != 'mesh,zones':
            raise ValueError('系の対応表の形式が想定と異なります')
        for line in f:
            mesh, zones = line.strip().split(',')
            table[mesh] = frozenset(int(z) for z in zones.split('|'))
    if path is None:
        _zone_table = table
    return table


def zones_of_mesh(mesh, table=None):
    """地域メッシュ番号（6桁=2次、8桁=3次）の系の集合。分からなければ None。"""
    table = load_zone_table() if table is None else table
    if len(mesh) == 8:
        if mesh in table:
            return table[mesh]
        return table.get(mesh[:6])
    if len(mesh) == 6:
        if mesh in table:
            return table[mesh]
        found = [z for m, z in table.items() if len(m) == 8 and m.startswith(mesh)]
        return frozenset().union(*found) if found else None
    return None


def mesh_from_gsi_name(name):
    """FG-GML-5338-44-00-DEM1A… → '53384400'、FG-GML-533844-DEM1A… → '533844'。"""
    match = _GSI_NAME.search(Path(name).name)
    if match is None:
        return None
    return match.group(1)+match.group(2)+(match.group(3) or '')


def _gsi_head(data):
    mesh = _GSI_MESH.search(data)
    srs = _GSI_SRS.search(data)
    return (mesh.group(1).decode() if mesh else None,
            srs.group(1).decode('ascii', 'replace').lower() if srs else '')


def gsi_records(paths, recursive, limit=PROBE_FILE_LIMIT):
    """国土地理院DEMの各ファイル（ZIP内を含む）から (表示名, 名前のメッシュ, GMLのメッシュ, srsName)。"""
    records = []
    for path in _iter_files(paths, ('.xml', '.zip'), recursive, limit):
        if path.suffix.lower() == '.zip':
            try:
                with zipfile.ZipFile(path) as archive:
                    names = [n for n in archive.namelist() if n.lower().endswith('.xml')]
                    for name in names[:max(0, limit-len(records))]:
                        with archive.open(name) as f:
                            head = f.read(GSI_HEAD_BYTES)
                        records.append((f'{path.name}:{name}', mesh_from_gsi_name(name)
                                        or mesh_from_gsi_name(path.name), *_gsi_head(head)))
            except (OSError, zipfile.BadZipFile):
                continue
        else:
            with open(path, 'rb') as f:
                head = f.read(GSI_HEAD_BYTES)
            records.append((path.name, mesh_from_gsi_name(path.name), *_gsi_head(head)))
        if len(records) >= limit:
            break
    return records[:limit]


def infer_gsi_zone(paths, recursive, table=None):
    """国土地理院DEMの系と測地系を決める。戻り値: (系, 'jgd2000'|'jgd2011', 根拠) または (None, None, 理由)。"""
    records = gsi_records(paths, recursive)
    if not records:
        return None, None, '国土地理院DEMのファイル（.xml／.zip）が見つかりません'
    zones, datums, meshes = set(), set(), set()
    for label, name_mesh, gml_mesh, srs in records:
        if name_mesh and gml_mesh and not (name_mesh.startswith(gml_mesh) or gml_mesh.startswith(name_mesh)):
            return None, None, f'ファイル名とGMLのメッシュ番号が一致しません（{label}：{name_mesh}／{gml_mesh}）'
        mesh = gml_mesh if gml_mesh and len(gml_mesh) >= len(name_mesh or '') else name_mesh
        if not mesh:
            continue
        found = zones_of_mesh(mesh, table)
        if found is None:
            continue
        if 0 in found:
            return None, None, f'メッシュ{mesh}は境界未定地域を含むため、系を決められません'
        zones |= found
        meshes.add(mesh)
        if 'jgd2000' in srs:
            datums.add('jgd2000')
        elif 'jgd2011' in srs or 'jgd2024' in srs:
            datums.add('jgd2011')
    if not zones:
        return None, None, '地域メッシュ番号から系を決められません（対応表に無いメッシュ、またはメッシュ番号が読めません）'
    if len(zones) > 1:
        listed = '、'.join(zone_label(z) for z in sorted(zones))
        return None, None, f'入力の範囲が複数の系にまたがっています（{listed}）'
    if len(datums) > 1:
        return None, None, 'JGD2000とJGD2011のファイルが混在しています'
    if not datums:
        return None, None, 'GMLの測地系（srsName）を読めません'
    zone = next(iter(zones))
    sample = sorted(meshes)[0]
    more = '' if len(records) < PROBE_FILE_LIMIT else f'、先頭{PROBE_FILE_LIMIT}件で確認'
    return zone, next(iter(datums)), (f'地域メッシュ（{sample}など{len(meshes)}件{more}）が'
                                      f'{zone_label(zone)}の区域です')


def infer_target_crs(mode, input_crs_wkt, paths, recursive, osr, zone_of):
    """ラスター以外の入力から出力の平面直角座標系を推定する。

    zone_of: osr.SpatialReference を受け取り系番号（1-19）かNoneを返す関数
    （pipeline._jpr_zone_of。循環importを避けるため引数で受け取る）。
    戻り値: (wkt, 根拠の説明) で成功、(None, 理由) で失敗。
    """
    if mode == 'gsi':
        if input_crs_wkt:
            srs = osr.SpatialReference()
            if srs.SetFromUserInput(input_crs_wkt) != 0 or not srs.IsGeographic():
                return None, ('国土地理院DEMでは「入力の水平座標系」は空欄にしてください'
                              '（ファイル内の緯度経度の座標系を使います）')
        zone, datum, reason = infer_gsi_zone(paths, recursive)
        if zone is None:
            return None, reason
        code = (6668 if datum == 'jgd2011' else 2442)+zone
        srs = osr.SpatialReference()
        if srs.ImportFromEPSG(code) != 0:
            return None, f'EPSG:{code}を作成できません'
        return srs.ExportToWkt(), reason+f'（{"JGD2011" if datum == "jgd2011" else "JGD2000"}、EPSG:{code}）'
    lem = lem_zones(paths, recursive) if mode == 'forest' else {}
    if input_crs_wkt:
        srs = osr.SpatialReference()
        if srs.SetFromUserInput(input_crs_wkt) != 0:
            return None, '入力の水平座標系を解釈できません'
        zone = zone_of(srs)
        if zone is None:
            return None, '入力の水平座標系が平面直角座標系第I～XIX系のいずれでもありません'
        if lem and set(lem) != {zone}:
            found = '、'.join(zone_label(z) for z in sorted(lem))
            return None, (f'入力の水平座標系は{zone_label(zone)}ですが、LEMのメタデータの'
                          f'平面直角座標系番号は{found}です。どちらが正しいか確認してください')
        return input_crs_wkt, f'入力の水平座標系（{zone_label(zone)}）と同じ座標系を使います'
    if mode == 'lidar':
        found = {}
        files = _iter_files(paths, LAS_EXTENSIONS, recursive)
        if not files:
            return None, 'LAS/LAZファイルが見つかりません'
        for path in files:
            try:
                record = read_las_crs(path)
            except (OSError, ValueError, struct.error):
                return None, 'LAS/LAZのヘッダーを読めません: '+str(path)
            if record is None:
                return None, 'LAS/LAZに座標系の記録がありません: '+str(path)
            try:
                srs = _srs_from(*record, osr)
            except ValueError:
                return None, 'LAS/LAZの座標系を解釈できません: '+str(path)
            zone = zone_of(srs)
            if zone is None:
                return None, 'LAS/LAZの座標系が平面直角座標系ではありません: '+str(path)
            first = found.setdefault(zone, (srs, []))[0]
            if first is not srs and not _same_crs(first, srs):
                return None, (f'LAS/LAZの座標系が、同じ{zone_label(zone)}でも測地系などが'
                              'ファイルによって異なります: '+str(path))
            found[zone][1].append(str(path))
        if len(found) > 1:
            listed = '、'.join(zone_label(z) for z in sorted(found))
            return None, f'LAS/LAZの座標系が複数の系にまたがっています（{listed}）'
        zone, (srs, used) = next(iter(found.items()))
        more = '' if len(files) < PROBE_FILE_LIMIT else f'（先頭{PROBE_FILE_LIMIT}件で確認）'
        return srs.ExportToWkt(), (f'LAS/LAZのヘッダーの座標系（{zone_label(zone)}、'
                                   f'{len(used)}件で一致{more}）を使います')
    if mode == 'forest' and lem:
        if len(lem) > 1:
            listed = '、'.join(zone_label(z) for z in sorted(lem))
            return None, f'LEMのメタデータの平面直角座標系番号が複数あります（{listed}）'
        zone = next(iter(lem))
        jgd2011, jgd2000 = suggested_epsg(zone)
        return None, (f'LEMのメタデータでは{zone_label(zone)}です。測地系はメタデータから判断できないため、'
                      f'「入力の水平座標系」に JGD2011 なら EPSG:{jgd2011}、JGD2000 なら EPSG:{jgd2000} を'
                      '指定してください（出力座標系もそれに合わせて自動で決まります）')
    return None, '「入力の水平座標系」が未指定です'
