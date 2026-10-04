"""地域メッシュ→平面直角座標系の系番号の対応表を作る（開発用。プラグインの実行時には使わない）。

入力: 総務省統計局「市区町村別メッシュ・コード一覧」（令和2年10月1日現在の市区町村区域）の都道府県別CSV
      （https://www.stat.go.jp/data/mesh/m_itiran.html）
      （列：都道府県市区町村コード、市区町村名、基準メッシュ・コード（3次メッシュ、8桁）、
      一部の県のみ備考。cp932）
出力: csmap_sheets/engine/data/jpr_zone_mesh.csv

系の割り当ては「平面直角座標系（平成14年国土交通省告示第9号）」による。
都道府県単位で決まる系に加え、次の例外を扱う。
- 北海道：第XI系・第XIII系に属する市町村を列挙し、残りを第XII系とする。
- 東京都：北緯28度より南は、東経140度30分より西が第XVIII系、東経143度より東が第XIX系、
  その間が第XIV系。それ以外は第IX系。
- 沖縄県：東経126度より西が第XVI系、東経130度より東が第XVII系、その間が第XV系。
- 鹿児島県：北緯27度～32度、東経128度18分～130度（奄美群島は130度13分まで）の区域が第I系、
  それ以外は第II系。
緯度経度による判定は3次メッシュの四隅で行い、境界をまたぐメッシュは複数の系を持つ。
「境界未定地域」（コード末尾999）は系を確定できないものとして 0 を記録する。

照合：上の規則で市区町村ごとに付く系番号を、告示の全文と照合済みの資料（姉妹リポジトリ
yo-1/japan-plane-rectangular-cs-zones の data/municipality_zones.csv、国土数値情報（行政区域）2026年版）
と比べ、比較できた1,895件の市区町村で食い違いがないことを確かめた（2026-10-04、
tools/crosscheck_zone_table.py）。奄美群島を奄美市と大島郡とみなす扱いは、両者に共通の仮定である。

出力形式（1行1件、ヘッダー付き）:
  mesh,zones
  533844,8        … 2次メッシュ（6桁）。その中の陸域の3次メッシュがすべて同じ系の場合
  53394512,8|9    … 3次メッシュ（8桁）。系が混在する2次メッシュの中のものだけ
zones は系番号を「|」でつないだもの（0 は確定できないことを表す）。

使い方:
  python tools/build_jpr_zone_table.py <CSVのフォルダー> [出力ファイル]
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

PREFECTURE_ZONE = {
    '02': 10, '03': 10, '04': 10, '05': 10, '06': 10, '07': 9, '08': 9, '09': 9, '10': 9,
    '11': 9, '12': 9, '13': 9, '14': 9, '15': 8, '16': 7, '17': 7, '18': 6, '19': 8,
    '20': 8, '21': 7, '22': 8, '23': 7, '24': 6, '25': 6, '26': 6, '27': 6, '28': 5,
    '29': 6, '30': 6, '31': 5, '32': 3, '33': 5, '34': 3, '35': 3, '36': 4, '37': 4,
    '38': 4, '39': 4, '40': 2, '41': 2, '42': 1, '43': 2, '44': 2, '45': 2, '46': 2,
    '47': 15,
}

# 北海道 第XI系：小樽市、函館市、伊達市、北斗市、後志総合振興局・渡島総合振興局・檜山振興局の
# 所管区域、胆振総合振興局の所管区域のうち豊浦町・壮瞥町・洞爺湖町
HOKKAIDO_XI = {
    '01202', '01203', '01233', '01236',
    '01331', '01332', '01333', '01334', '01337', '01343', '01345', '01346', '01347',  # 渡島
    '01361', '01362', '01363', '01364', '01367', '01370', '01371',  # 檜山
    '01391', '01392', '01393', '01394', '01395', '01396', '01397', '01398', '01399', '01400',
    '01401', '01402', '01403', '01404', '01405', '01406', '01407', '01408', '01409',  # 後志
    '01571', '01575', '01584',  # 胆振のうち豊浦町・壮瞥町・洞爺湖町
}
# 北海道 第XIII系：北見市、帯広市、釧路市、網走市、根室市、オホーツク総合振興局の所管区域のうち
# 美幌町・津別町・斜里町・清里町・小清水町・訓子府町・置戸町・佐呂間町・大空町、
# 十勝総合振興局・釧路総合振興局・根室振興局の所管区域
HOKKAIDO_XIII = {
    '01206', '01207', '01208', '01211', '01223',
    '01543', '01544', '01545', '01546', '01547', '01549', '01550', '01552', '01564',  # オホーツクの一部
    '01631', '01632', '01633', '01634', '01635', '01636', '01637', '01638', '01639', '01641',
    '01642', '01643', '01644', '01645', '01646', '01647', '01648', '01649',  # 十勝
    '01661', '01662', '01663', '01664', '01665', '01667', '01668',  # 釧路
    '01691', '01692', '01693', '01694', '01695', '01696', '01697', '01698', '01699', '01700',  # 根室
}
# 奄美群島（大島郡と奄美市）。第I系の東の境界が東経130度13分まで広がる
AMAMI = {'46222', '46523', '46524', '46525', '46527', '46529', '46530', '46531', '46532',
         '46533', '46534', '46535'}

LAT3 = 30/3600
LON3 = 45/3600


def mesh_bounds(mesh):
    """3次メッシュ（8桁）の南西端と北東端の緯度経度。"""
    lat = int(mesh[0:2])/1.5 + int(mesh[4])*5/60 + int(mesh[6])*LAT3
    lon = int(mesh[2:4]) + 100 + int(mesh[5])*7.5/60 + int(mesh[7])*LON3
    return lat, lon, lat+LAT3, lon+LON3


def corners(mesh):
    s, w, n, e = mesh_bounds(mesh)
    eps = 1e-9  # 境界線上の端点を、メッシュの内側として判定する
    return [(s+eps, w+eps), (s+eps, e-eps), (n-eps, w+eps), (n-eps, e-eps)]


def zone_at(code, lat, lon):
    pref = code[:2]
    if code.endswith('999'):
        return 0
    if pref == '01':
        return 11 if code in HOKKAIDO_XI else 13 if code in HOKKAIDO_XIII else 12
    if pref == '13' and lat < 28:
        return 18 if lon < 140.5 else 19 if lon >= 143 else 14
    if pref == '47':
        return 16 if lon < 126 else 17 if lon >= 130 else 15
    if pref == '46':
        east = 130 + 13/60 if code in AMAMI else 130
        return 1 if (27 <= lat < 32 and 128.3 <= lon < east) else 2
    return PREFECTURE_ZONE[pref]


def build(folder):
    third = defaultdict(set)
    for path in sorted(Path(folder).glob('*.csv')):
        with open(path, encoding='cp932', newline='') as f:
            reader = csv.reader(f)
            header = next(reader)
            if header[:3] != ['都道府県市区町村コード', '市区町村名', '基準メッシュ・コード']:
                raise ValueError('想定外の列名: %s %s' % (path, header))
            # 一部の県のCSVには4列目「備考」がある（「*」の印。系の判定には使わない）
            for row in reader:
                code, mesh = row[0], row[2]
                if len(code) != 5 or len(mesh) != 8 or not mesh.isdigit():
                    raise ValueError('想定外の行: %s %s %s' % (path, code, mesh))
                for lat, lon in corners(mesh):
                    third[mesh].add(zone_at(code, lat, lon))
    second = defaultdict(set)
    for mesh, zones in third.items():
        second[mesh[:6]].add(frozenset(zones))
    rows = []
    for mesh6 in sorted(second):
        variants = second[mesh6]
        if len(variants) == 1 and len(next(iter(variants))) == 1:
            rows.append((mesh6, next(iter(variants))))
        else:
            for mesh8 in sorted(m for m in third if m.startswith(mesh6)):
                rows.append((mesh8, frozenset(third[mesh8])))
    return rows, third


def main():
    folder = sys.argv[1]
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else (
        Path(__file__).resolve().parents[1]/'csmap_sheets'/'engine'/'data'/'jpr_zone_mesh.csv')
    rows, third = build(folder)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        f.write('mesh,zones\n')
        for mesh, zones in rows:
            f.write('%s,%s\n' % (mesh, '|'.join(str(z) for z in sorted(zones))))
    multi = sum(1 for z in third.values() if len(z) > 1)
    print('3次メッシュ %d件（複数の系にまたがる %d件）、出力 %d行 → %s'
          % (len(third), multi, len(rows), out))


if __name__ == '__main__':
    main()
