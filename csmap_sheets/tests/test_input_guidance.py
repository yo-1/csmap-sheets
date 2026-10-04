"""入力形式の選び間違いの案内（GDAL不要）。

選んだ入力形式のファイルが既存の探索で1件も無いと確定したときだけ案内し、設定は自動で切り替えない。
拡張子だけで国土地理院DEMと断定しない。形式が混在していても、選んだ形式のファイルがあれば通常どおり進む。
"""
from pathlib import Path
import tempfile
import unittest
import zipfile
from unittest import mock
from csmap_sheets.engine import input_sources as inputs

GSI_XML = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<Dataset xmlns="http://fgd.gsi.go.jp/spec/2008/FGD_GMLSchema"><DEM><mesh>533844</mesh></DEM></Dataset>')
OTHER_XML = '<?xml version="1.0" encoding="UTF-8"?>\n<metadata><title>other</title></metadata>'


def config(input_type, **kw):
    return {**inputs.DEFAULTS, 'input_type': input_type, **kw}


class InputTypeGuidanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, text=''):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return path

    def message(self, input_type, entries=None):
        with self.assertRaises(ValueError) as caught:
            inputs.discover(entries or [str(self.root)], self.root, config(input_type))
        return str(caught.exception)

    def test_wrong_type_for_gsi_xml_folder(self):
        for i in range(3):
            self.write(f'FG-GML-5338-44-{i:02d}-DEM1A-20251113.xml', GSI_XML)
        text = self.message('raster')
        self.assertTrue(text.startswith('No supported files in: '))  # 既存の英語の見出しは残す
        self.assertIn('入力形式「標高ラスタ（GeoTIFF・IMG・ASC）」で使えるファイル', text)
        self.assertIn('国土地理院DEMの候補：3件（内容を確かめた3件のうち、国土地理院DEMは3件）', text)
        self.assertIn('「国土地理院DEM（ZIP・XML）」', text)
        self.assertNotIn('「森林航空レーザ成果', text)  # XMLは森林航空レーザ成果の入力ではない
        self.assertIn('自動では切り替えません', text)

    def test_mixed_formats_proceed_with_selected_type(self):
        tif = self.write('dem.tif')
        self.write('FG-GML-5338-44-00-DEM1A-20251113.xml', GSI_XML)
        self.write('points.las')
        files = inputs.discover([str(self.root)], self.root, config('raster'))
        self.assertEqual([Path(f).name for f in files], [tif.name])

    def test_unrelated_xml_and_zip_are_only_candidates(self):
        self.write('metadata.xml', OTHER_XML)
        with zipfile.ZipFile(self.root / 'photos.zip', 'w') as archive:
            archive.writestr('readme.txt', 'not a DEM')
        text = self.message('raster')
        self.assertIn('国土地理院DEMの候補：2件（内容を確かめた2件のうち、国土地理院DEMは0件）', text)
        self.assertNotIn('「国土地理院DEM（ZIP・XML）」', text)
        self.assertIn('入力形式と入力フォルダー・ファイルを確認してください', text)

    def test_gsi_zip_detected_by_member_name(self):
        with zipfile.ZipFile(self.root / 'FG-GML-533844-DEM1A-20251113.zip', 'w') as archive:
            archive.writestr('FG-GML-5338-44-00-DEM1A-20251113.xml', GSI_XML)
        text = self.message('lidar')
        self.assertIn('国土地理院DEMは1件', text)
        self.assertIn('「国土地理院DEM（ZIP・XML）」', text)

    def test_forest_zip_is_suggested_by_contents(self):
        with zipfile.ZipFile(self.root / 'lem_tiles.zip', 'w') as archive:
            archive.writestr('09LD1234.lem', '')
            archive.writestr('09LD1234.csv', '')
        text = self.message('raster')
        self.assertIn('国土地理院DEMは0件、森林航空レーザ成果の可能性があるZIPは1件', text)
        self.assertIn('「森林航空レーザ成果', text)
        self.assertNotIn('「国土地理院DEM（ZIP・XML）」', text)

    def test_valid_input_after_scan_limit_is_still_used(self):
        # 案内用の確認には上限があるが、選んだ形式の探索（既存）は上限なしで全件を見る
        for i in range(6):
            self.write(f'a{i}.xml', OTHER_XML)
        tif = self.write('z/last.tif')
        with mock.patch.object(inputs, 'GUIDANCE_SCAN_LIMIT', 3):
            files = inputs.discover([str(self.root)], self.root, config('raster'))
        self.assertEqual([Path(f).name for f in files], [tif.name])

    def test_partial_check_is_stated(self):
        for i in range(6):
            self.write(f'p{i}.las')
        with mock.patch.object(inputs, 'GUIDANCE_SCAN_LIMIT', 3):
            text = self.message('raster')
        self.assertIn('確認した範囲（先頭3件）で見つかった', text)
        self.assertIn('レーザ点群：3件', text)
        self.assertIn('「レーザ点群（LAS・LAZ）」', text)

    def test_nothing_recognisable(self):
        self.write('notes.docx')
        text = self.message('gsi')
        self.assertIn('ほかの入力形式のファイルも見つかりません', text)

    def test_single_file_with_wrong_extension(self):
        las = self.write('points.las')
        with self.assertRaises(ValueError) as caught:
            inputs.discover([str(las)], self.root, config('raster'))
        text = str(caught.exception)
        self.assertTrue(text.startswith('Input extension does not match input_type'))
        self.assertIn('レーザ点群：1件', text)
        self.assertIn('「レーザ点群（LAS・LAZ）」', text)

    def test_ambiguous_extensions_list_both_types(self):
        self.write('grid.csv', 'x,y,z\n')
        text = self.message('lidar')
        self.assertIn('標高テキストの候補：1件', text)
        self.assertIn('「標高テキスト（XYZ・CSV・TXT）」、「森林航空レーザ成果', text)


if __name__ == '__main__':
    unittest.main()
