"""メッシュ→系の対応表の規則を、市区町村ごとの系番号データと突き合わせる（開発用）。

`tools/build_jpr_zone_table.py` の規則（都道府県単位の系と、北海道・東京都・沖縄県・
鹿児島県の例外）で、市区町村ごとに付く系番号の集合を求め、別の資料（姉妹リポジトリ
yo-1/japan-plane-rectangular-cs-zones の data/municipality_zones.csv。告示の全文と照合済み）
の系番号の集合と比べる。食い違った市区町村と、片方にしかないコードを表示する。

使い方:
  python tools/crosscheck_zone_table.py <統計局CSVのフォルダー> <municipality_zones.csv>
"""

import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_jpr_zone_table as table  # noqa: E402


def zones_by_code(folder):
    zones, names = defaultdict(set), {}
    for path in sorted(Path(folder).glob("*.csv")):
        with open(path, encoding="cp932", newline="") as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                code, name, mesh = row[0], row[1], row[2]
                names[code] = name
                for lat, lon in table.corners(mesh):
                    zones[code].add(table.zone_at(code, lat, lon))
    return zones, names


def reference_zones(path):
    zones = defaultdict(set)
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            zones[row["code"]].update(
                int(z) for z in re.split("[;|]", row["zones"]) if z
            )
    return zones


def main():
    mine, names = zones_by_code(sys.argv[1])
    reference = reference_zones(sys.argv[2])
    compared = differ = 0
    for code in sorted(mine):
        if code.endswith("999"):
            continue
        if code not in reference:
            print("参照側になし", code, names[code])
            continue
        compared += 1
        if mine[code] != reference[code]:
            differ += 1
            print(
                "食い違い",
                code,
                names[code],
                sorted(mine[code]),
                sorted(reference[code]),
            )
    print(f"比較 {compared} 件、食い違い {differ} 件")
    return 1 if differ else 0


if __name__ == "__main__":
    sys.exit(main())
