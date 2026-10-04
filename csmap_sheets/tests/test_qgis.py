"""Run in QGIS Python for a real API smoke test; skipped without QGIS."""
import unittest
try:
    from qgis.core import QgsApplication, QgsProcessingContext, QgsProcessingFeedback
    AVAILABLE=True
except ImportError:
    AVAILABLE=False


@unittest.skipUnless(AVAILABLE,'QGIS is not installed')
class QgisTests(unittest.TestCase):
    def test_file_selection_limit_checked_before_qgis_validation(self):
        # v0.11.0: 個別選択の件数・存在は、QGIS標準の検査（各ファイルを開く）より前に検査する
        import tempfile
        from pathlib import Path
        from csmap_sheets.algorithm import CSMapAlgorithm, INDIVIDUAL_FILE_SELECTION_LIMIT
        alg=CSMapAlgorithm();alg.initAlgorithm()
        context=QgsProcessingContext()
        with tempfile.TemporaryDirectory() as tmp:
            files=[]
            for i in range(INDIVIDUAL_FILE_SELECTION_LIMIT+1):
                path=Path(tmp)/f'{i:03d}.xml';path.write_text('<x/>');files.append(str(path))
            ok,message=alg.checkParameterValues({'FILES':files},context)
            self.assertFalse(ok);self.assertIn('入力フォルダー',message)
            ok,message=alg.checkParameterValues({'FILES':[str(Path(tmp)/'missing.xml')]},context)
            self.assertFalse(ok);self.assertIn('見つかりません',message)

    def test_algorithm_parameters(self):
        from csmap_sheets.algorithm import CSMapAlgorithm
        alg=CSMapAlgorithm()
        alg.initAlgorithm()
        self.assertEqual(alg.name(),'create')
        self.assertIsNotNone(alg.parameterDefinition('DEMS'))
        self.assertEqual(alg.parameterDefinition('LEGACY_VALLEY_RGB').type(),'color')
        self.assertEqual(alg.parameterDefinition('FME_CURVATURE_B_MID').type(),'color')
        self.assertIsNotNone(alg.outputDefinition('SHEET_INDEX'))
        self.assertIsNotNone(alg.outputDefinition('XYZ_FOLDER'))
        self.assertIsNone(alg.parameterDefinition('ZONE'))
        for key in ('PROFILE','PROFILE_FILE','SAVE_PROFILE','RENDER_MODE','FME_STRETCH',
                    'XYZ','XYZ_FORMAT','XYZ_WEBP_LOSSLESS','XYZ_WEBP_QUALITY',
                    'XYZ_MIN','XYZ_MAX','XYZ_LIMIT','INPUT_TYPE','FILES',
                    'INPUT_FOLDER','PDAL','LIDAR_MODE','TEXT_COLUMNS'):
            self.assertIsNotNone(alg.parameterDefinition(key))
        # XYZ_FORMAT defaults to PNG; WebP is opt-in (handover doc 2026-09-27, section 3).
        self.assertEqual(alg.parameterDefinition('XYZ_FORMAT').defaultValue(),0)
        self.assertEqual(len(alg.parameterDefinition('XYZ_FORMAT').options()),2)
        # WebPは既定で可逆(lossless)。非可逆(lossy)はユーザー要望により選択制で追加(2026-09-28)。
        self.assertEqual(alg.parameterDefinition('XYZ_WEBP_LOSSLESS').defaultValue(),True)
        self.assertEqual(alg.parameterDefinition('XYZ_WEBP_QUALITY').defaultValue(),75)
        # PROFILE must keep the FME-manual and provisional ±0.03 curvature figures as separate,
        # clearly-labelled choices (2026-09-20/24 decisions), not merged into one default.
        options=alg.parameterDefinition('PROFILE').options()
        self.assertEqual(len(options),5)
        self.assertIn('0.1',options[1]);self.assertIn('0.1',options[2]);self.assertIn('0.03',options[3])
        # FME_STRETCH's default selection should reproduce the manual's own documented output
        # (色の鮮明化) out of the box, not silently skip it.
        self.assertEqual(alg.parameterDefinition('FME_STRETCH').defaultValue(),1)
        # v0.12.0: σの指定方式。既定は地上距離（m）3m、画素数の初期値は3px。
        self.assertEqual(alg.parameterDefinition('SIGMA_UNIT').defaultValue(),0)
        self.assertEqual(len(alg.parameterDefinition('SIGMA_UNIT').options()),2)
        self.assertEqual(alg.parameterDefinition('SIGMA').defaultValue(),3.)
        self.assertEqual(alg.parameterDefinition('SIGMA_PX').defaultValue(),3.)


if __name__=='__main__':unittest.main(verbosity=2)
