"""Exact public strings retained by the Python 3.11 syntax repair."""
import tempfile
import unittest
from unittest.mock import patch

from csmap_sheets.engine.input_sources import input_type_guidance
from csmap_sheets.engine.map_sheets import sheet_at
from csmap_sheets.engine.pipeline import color_settings
from csmap_sheets.engine.xyz_tiles import precheck_xyz_tile_count


class MessageCompatibilityTests(unittest.TestCase):
    def test_input_guidance_keeps_labels_extensions_and_punctuation(self):
        cases = (
            ("raster", "標高ラスタ（GeoTIFF・IMG・ASC）",
             ".asc・.img・.tif・.tiff・.vrt"),
            ("gsi", "国土地理院DEM（ZIP・XML）", ".xml・.zip"),
            ("text", "標高テキスト（XYZ・CSV・TXT）", ".csv・.txt・.xyz"),
            ("lidar", "レーザ点群（LAS・LAZ）", ".las・.laz"),
            ("forest", "森林航空レーザ成果（LEM・CSV格子・TIFF・GeoTIFF・ZIP）",
             ".csv・.lem・.tif・.tiff・.txt・.xyz・.zip"),
        )
        with tempfile.TemporaryDirectory() as directory:
            for selected, label, extensions in cases:
                with self.subTest(selected=selected):
                    expected = (
                        "入力形式「" + label + "」で使えるファイル（"
                        + extensions + "）が、指定した入力にありません。\n"
                        "指定した入力では、ほかの入力形式のファイルも見つかりません。"
                        "入力フォルダー・ファイルを確認してください。"
                    )
                    self.assertEqual(
                        input_type_guidance(directory, {"input_type": selected}),
                        expected,
                    )

    def test_sheet_codes_keep_zero_padding_and_subdivision_suffixes(self):
        cases = (
            (0, 0, 9, ("09KE00", "09KE001", "09KE000A", "09KE0000")),
            (-160000, 300000, 1,
             ("01AA00", "01AA001", "01AA000A", "01AA0000")),
            (159999, -299999, 19,
             ("19TH99", "19TH994", "19TH994E", "19TH9999")),
        )
        for east, north, zone, expected in cases:
            for level, code in zip((5000, 2500, 1000, 500), expected):
                with self.subTest(zone=zone, level=level):
                    self.assertEqual(sheet_at(east, north, zone, level).code,
                                     code)

    def test_xyz_limit_message_keeps_comma_grouping_and_full_text(self):
        cases = (
            (1234567, 100000, "1,234,567", "100,000"),
            (2, 1, "2", "1"),
        )
        for total, limit, total_text, limit_text in cases:
            with self.subTest(total=total, limit=limit):
                with patch(
                    "csmap_sheets.engine.xyz_tiles.raster_bounds_3857",
                    return_value=(0, 0, 1, 1),
                ), patch(
                    "csmap_sheets.engine.xyz_tiles.estimate_candidate_tiles",
                    return_value=total,
                ):
                    with self.assertRaises(ValueError) as caught:
                        precheck_xyz_tile_count(
                            "unused.vrt", {"xyz_max_tiles": limit}, None, None
                        )
                self.assertEqual(
                    str(caught.exception),
                    "XYZ candidate tiles(事前見積り)=" + total_text
                    + "; limit=" + limit_text + "。"
                    "CS立体図の計算を開始する前に停止しました"
                    "（無駄な計算時間を避けるため）。"
                    "XYZ最大ズームを下げるか、"
                    "XYZ候補枚数の上限(xyz_max_tiles)を増やしてください。",
                )

    def test_unknown_color_keys_keep_sorted_python_list_representation(self):
        with self.assertRaises(ValueError) as caught:
            color_settings({"z_unknown": 1, "gamma": 1, "a_unknown": 2})
        self.assertEqual(
            str(caught.exception),
            "Unknown color keys: ['a_unknown', 'z_unknown']",
        )
