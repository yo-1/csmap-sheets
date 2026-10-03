from datetime import datetime
import glob
import json
from pathlib import Path
import uuid
from qgis.PyQt.QtGui import QColor
from qgis.core import (
    Qgis, QgsProcessing, QgsProcessingAlgorithm, QgsProcessingException,
    QgsProcessingParameterMultipleLayers, QgsProcessingParameterCrs,
    QgsProcessingParameterNumber, QgsProcessingParameterEnum,
    QgsProcessingParameterBoolean, QgsProcessingParameterColor,
    QgsProcessingParameterFolderDestination, QgsProcessingOutputRasterLayer,
    QgsProcessingOutputVectorLayer, QgsProcessingOutputFile, QgsProcessingContext,
    QgsProviderRegistry, QgsVariantUtils, QgsProcessingOutputFolder,
    QgsProcessingParameterFile, QgsProcessingParameterString,
    QgsProcessingParameterFileDestination, QgsCoordinateReferenceSystem,
)

# v0.9.3: 個別ファイル選択（FILESパラメータ）の件数上限。QGIS自身の
# Processingフレームワークが実行時に選択件数分のレイヤー解決を試みる挙動により、
# 件数超過時にQGISが長時間「応答なし」になることが確認されている（詳細は
# prepareAlgorithm()内のコメントを参照）。暫定値であり、実運用での再調整を想定。
INDIVIDUAL_FILE_SELECTION_LIMIT = 100

COLOR_NUMBERS = [
    ('curvature_strength','曲率色の濃さ',1.,0.,1.),
    ('elevation_mix','標高色の混合率',.15,0.,1.),
    ('slope_darkness','傾斜による暗さ（小さいほど明るい）',.55,0.,1.),
    ('brightness','明るさの倍率',1.,0.,3.),
    ('saturation','彩度（0でグレースケール）',1.,0.,3.),
    ('contrast','コントラスト',1.,0.,3.),
    ('gamma','ガンマ（1より大きいと中間調が明るい）',1.,.1,5.),
]
LEGACY_PALETTE = [
    ('valley_rgb','独自方式：曲率・凹型側（小さい値）',(74,140,198)),
    ('neutral_rgb','独自方式：曲率0（中間）',(248,247,242)),
    ('ridge_rgb','独自方式：曲率・凸型側（大きい値）',(192,119,71)),
    ('elevation_low_rgb','独自方式：標高・低い側',(222,236,244)),
    ('elevation_high_rgb','独自方式：標高・高い側',(250,242,223)),
]
FME_PALETTE = [
    ('elevation_low','FME 標高：低い側',(36,36,36)),
    ('elevation_high','FME 標高：高い側',(246,246,246)),
    ('slope_a_low','FME 傾斜A：緩斜面側',(247,213,213)),
    ('slope_a_high','FME 傾斜A：急斜面側',(134,28,33)),
    ('slope_b_low','FME 傾斜B：緩斜面側',(246,246,246)),
    ('slope_b_high','FME 傾斜B：急斜面側',(36,36,36)),
    ('curvature_a_low','FME 曲率A：凹型側（小さい値）',(42,95,131)),
    ('curvature_a_high','FME 曲率A：凸型側（大きい値）',(208,223,230)),
    ('curvature_b_low','FME 曲率B：凹型側（小さい値）',(50,96,207)),
    ('curvature_b_mid','FME 曲率B：曲率0（中間）',(255,254,190)),
    ('curvature_b_high','FME 曲率B：凸型側（大きい値）',(198,72,59)),
]


class CSMapAlgorithm(QgsProcessingAlgorithm):
    def name(self):return 'create'
    def displayName(self):return 'DEMマージ・CS色調調整・国土基本図図郭・XYZ出力'
    def group(self):return 'CS立体図'
    def groupId(self):return 'terrain'
    def createInstance(self):return CSMapAlgorithm()
    def tags(self):return ['CS','DEM','国土基本図','図郭','立体図','色調','merge']
    def shortHelpString(self):
        from .engine.pipeline import version_banner
        return (
            version_banner()+'\n'
            '複数DEM→平面直角座標系へ整合→独自CS方式画像→国土基本図図郭GeoTIFF→XYZタイル（EPSG:3857、PNGまたはWebP）。'
            '入力形式を選び、ファイルまたはフォルダーを指定します。LAS/LAZと不規則テキスト点には外部PDAL 2.9以降が必要です。'
            '\n入力形式に関係する設定だけを使用します。森林航空レーザ成果はLEM、CSV/XYZ格子、TIFF+TFW、GeoTIFFとZIPを自動判別します。'
            '地理院ZIPは自動読込み、LASは分類方法を選択します。'
            '\n鉛直基準の変換は行いません。標高基準をそろえたデータを使用してください。'
            '\n出力先の下に毎回新しいcsmap_日時_識別子フォルダーを作ります。'
            '\n描画方式は「独自方式 v0.4互換」と「FMEマニュアル方式」を明示的に分けます。'
            'FME方式は5レイヤー加重和で、RGBストレッチはなし・長野県実績値・カスタムから選択します。'
            '\n色調設定は全域共通です。ライブプレビューはありません。'
            '\n標高色の下限/上限は「標高色の下限/上限を自動検出する」を有効にすると、対象範囲を再投影・'
            'モザイク化した後に実際の標高min/maxを検出し、余白（既定50m）を加えて自動設定します（ELEV_MIN/MAXの'
            '数値は無視されます）。組込み設定プロファイルを選んだ場合はプロファイル側の値が優先され、自動検出は無効になります。'
            '\n県全域は図郭単位で処理し、全域をメモリーへ展開しません。系番号は選択した平面直角座標系から自動決定します。'
            '\n設定プロファイルは処理設定をJSONで保存・読込みできます。入力・出力・CRS・確認欄は安全のため保存対象外です。'
            '\n図郭レベルはファイル寸法・番号の選択で、DEM精度の保証ではありません。'
            'FME方式でも地形量計算は本プラグイン方式のため、FME出力との画素完全一致を保証しません。'
            '\nXYZ画像形式はPNG（既定）またはWebPを選択します。WebPは既定で可逆(lossless)ですが、'
            '「WebPを可逆(lossless)にする」を無効にすると非可逆(lossy)になり、QUALITY（1-100、既定75、'
            'GDAL WEBPドライバの既定値と同じ）で圧縮率を調整できます。QGIS同梱GDALにWEBP'
            'ドライバが無い環境では、可逆・非可逆いずれの設定でもPNGへ自動的に切り替えず、エラーで停止します。'
            'MBTiles・GeoPackageへの格納は未対応です（フォルダーXYZのみ）。'
            '\nCopyright (C) 2026 Yoichi Wada. GNU GPL v3.0 only.'
        )

    def initAlgorithm(self, config=None):
        profile=self.addParameter(QgsProcessingParameterEnum('PROFILE','設定プロファイル',
            ['画面の設定を使用','標準CS・1m（FMEマニュアル方式、曲率±0.1）',
             '試験処理・2m（FMEマニュアル方式、曲率±0.1）',
             '林野庁近似設定（暫定）・1m（曲率±0.03）','外部JSONプロファイル'],defaultValue=0))
        profile_file=QgsProcessingParameterFile('PROFILE_FILE','読込む設定プロファイル（JSON）',
            extension='json',optional=True)
        profile_file.setFlags(profile_file.flags() | Qgis.ProcessingParameterFlag.Advanced);self.addParameter(profile_file)
        save_profile=QgsProcessingParameterFileDestination('SAVE_PROFILE','現在の処理設定をJSONへ保存（省略可）',
            fileFilter='JSON (*.json)',optional=True)
        save_profile.setFlags(save_profile.flags() | Qgis.ProcessingParameterFlag.Advanced);self.addParameter(save_profile)
        self.addParameter(QgsProcessingParameterEnum('INPUT_TYPE','入力形式',
            ['標高ラスタ（GeoTIFF・IMG・ASC）','国土地理院DEM（ZIP・XML）',
             '標高テキスト（XYZ・CSV・TXT）','レーザ点群（LAS・LAZ）',
             '森林航空レーザ成果（LEM・CSV格子・TIFF・GeoTIFF・ZIP）'],defaultValue=0))
        self.addParameter(QgsProcessingParameterMultipleLayers('FILES','入力ファイル（複数選択、フォルダー指定時は省略可）',
            QgsProcessing.TypeFile,optional=True))
        self.addParameter(QgsProcessingParameterFile('INPUT_FOLDER','入力フォルダー（省略可）',
            behavior=QgsProcessingParameterFile.Folder,optional=True))
        self.addParameter(QgsProcessingParameterBoolean('RECURSIVE','サブフォルダーも検索する',True))
        self.addParameter(QgsProcessingParameterMultipleLayers('DEMS','読込み済み標高ラスタを使う場合（省略可）',QgsProcessing.TypeRaster,optional=True))
        self.addParameter(QgsProcessingParameterCrs('INPUT_CRS','入力の水平座標系（テキスト・LEM・非GeoTIFFは必須／その他は空欄で自動）',optional=True))
        self.addParameter(QgsProcessingParameterString('VERTICAL','入力標高の基準名（記録用、例：測地成果2024）',optional=True))
        self.addParameter(QgsProcessingParameterBoolean('NORMALIZE','標高ラスタの座標系・解像度・格子をそろえる',True))
        self.addParameter(QgsProcessingParameterEnum('LIDAR_MODE','LAS/LAZ：地表面の取り出し方',
            ['分類済み（指定分類コードを抽出）','地表面点のみのデータ','自動分類（SMRF、結果確認が必要）'],defaultValue=0))
        self.addParameter(QgsProcessingParameterString('GROUND_CLASSES','LAS/LAZ：地表面分類コード（カンマ区切り）',defaultValue='2'))
        self.addParameter(QgsProcessingParameterFile('PDAL','点群用PDAL実行ファイル（pdal.exe。PATHにあれば省略可）',optional=True))
        self.addParameter(QgsProcessingParameterEnum('POINT_METHOD','点群DEMの補間方法',
            ['距離による重み付け（IDW）','近傍点の平均','近傍点の最低値'],defaultValue=0))
        self.addParameter(QgsProcessingParameterNumber('POINT_RADIUS','点群DEMの補間半径（m、範囲外は欠測）',
            QgsProcessingParameterNumber.Double,2.,minValue=.01,maxValue=1000.))
        self.addParameter(QgsProcessingParameterEnum('TEXT_MODE','テキスト：点の並び',
            ['規則格子（座標をセル中心として復元）','不規則点（PDALで補間）'],defaultValue=0))
        self.addParameter(QgsProcessingParameterEnum('TEXT_DELIMITER','テキスト：区切り文字',
            ['カンマ','タブ','空白','セミコロン'],defaultValue=0))
        self.addParameter(QgsProcessingParameterString('TEXT_ENCODING','テキスト：文字コード',defaultValue='utf-8-sig'))
        self.addParameter(QgsProcessingParameterNumber('TEXT_SKIP','テキスト：先頭の読み飛ばし行数',
            QgsProcessingParameterNumber.Integer,1,minValue=0))
        self.addParameter(QgsProcessingParameterString('TEXT_COLUMNS','テキスト：座標1・座標2・標高の列番号（1始まり）',defaultValue='1,2,3'))
        self.addParameter(QgsProcessingParameterEnum('TEXT_AXES','テキスト：座標列の順序',
            ['東方向、北方向（経度、緯度）','北方向、東方向（測量のX、Y）'],defaultValue=0))
        self.addParameter(QgsProcessingParameterNumber('TEXT_CELL','テキスト：入力格子間隔（m、規則格子の場合）',
            QgsProcessingParameterNumber.Double,1.,minValue=.01))
        self.addParameter(QgsProcessingParameterEnum('FOREST_AXES','森林航空レーザCSV：X/Y列の順序',
            ['測量X（北）、測量Y（東）','GIS X（東）、GIS Y（北）'],defaultValue=0))
        forest_cell=QgsProcessingParameterString('FOREST_CELL','森林航空レーザCSV：格子間隔（autoまたはm）',defaultValue='auto')
        forest_cell.setFlags(forest_cell.flags() | Qgis.ProcessingParameterFlag.Advanced)
        self.addParameter(forest_cell)
        lem_scale=QgsProcessingParameterString('LEM_SCALE','LEM座標値の倍率（auto、通常は自動判定）',defaultValue='auto')
        lem_scale.setFlags(lem_scale.flags() | Qgis.ProcessingParameterFlag.Advanced)
        self.addParameter(lem_scale)
        forest_nd=QgsProcessingParameterNumber('FOREST_NODATA','森林航空レーザ成果の既定NoData',
            QgsProcessingParameterNumber.Double,-9999.)
        forest_nd.setFlags(forest_nd.flags() | Qgis.ProcessingParameterFlag.Advanced)
        self.addParameter(forest_nd)
        for key,label,default,lo,hi in [
            ('POINT_TILE','点群DEM：1ブロックの辺の画素数',512,64,2048),
            ('AUTO_LIMIT','自動分類：バッファー込みの点数上限／ブロック',10000000,1,1000000000)]:
            param=QgsProcessingParameterNumber(key,label,QgsProcessingParameterNumber.Integer,default,minValue=lo,maxValue=hi)
            param.setFlags(param.flags() | Qgis.ProcessingParameterFlag.Advanced)
            self.addParameter(param)
        for key,label,default in [('SMRF_CELL','分類用セル幅（m）',1.),('SMRF_SLOPE','傾斜係数',.15),
            ('SMRF_THRESHOLD','標高差閾値（m）',.5),('SMRF_SCALAR','標高差係数',1.25),('SMRF_WINDOW','最大窓幅（m）',18.)]:
            param=QgsProcessingParameterNumber(key,'SMRF：'+label,QgsProcessingParameterNumber.Double,default,minValue=.001,maxValue=1000.)
            param.setFlags(param.flags() | Qgis.ProcessingParameterFlag.Advanced)
            self.addParameter(param)
        self.addParameter(QgsProcessingParameterCrs('CRS',
            '出力の平面直角座標系（空欄なら入力ラスターのCRS、入力の水平座標系、LAS/LAZのヘッダーから'
            '第I～XIX系を自動推定。国土地理院DEMや自動推定できない場合は明示指定が必須）',
            optional=True))
        self.addParameter(QgsProcessingParameterEnum('LEVEL','国土基本図の図郭レベル',
            ['5000：東西4000m × 南北3000m','2500：東西2000m × 南北1500m',
             '1000：東西800m × 南北600m','500：東西400m × 南北300m'],defaultValue=0))
        for name,label,value,lo,hi in [
            ('CELL','出力セルサイズ（m）',1.,.01,100.),
            ('SIGMA','曲率用平滑化の標準偏差（m）',3.,0.,1000.),
            ('CURVE_LIMIT','曲率色の飽和値（±、1/m。FME資料の「±10」に対応する値。'
             '同梱FMWのKERNEL_DIVISOR=cell_size²×0.01から換算・確認済み）',.1,.000001,100.),
            ('SLOPE_MAX','傾斜の暗さが飽和する角度（度。色調の設定であり、傾斜の計算方式とは別）',60.,.1,90.),
            ('ELEV_MIN','標高色の下限（m）',200.,-10000.,10000.),
            ('ELEV_MAX','標高色の上限（m）',2000.,-10000.,10000.),
        ]:
            self.addParameter(QgsProcessingParameterNumber(name,label,
                QgsProcessingParameterNumber.Double,value,minValue=lo,maxValue=hi))
        slope_algorithm=QgsProcessingParameterEnum('SLOPE_ALGORITHM','傾斜計算のアルゴリズム',
            ['Horn法（推奨・既定。3×3加重差分）',
             '中央差分法（従来互換。v0.9.4以前の既定）'],defaultValue=0)
        self.addParameter(slope_algorithm)
        self.addParameter(QgsProcessingParameterBoolean('ELEV_AUTO',
            '標高色の下限/上限を自動検出する（対象範囲の実際の標高min/maxに'
            '下記の余白を加えて使用。ELEV_MIN/ELEV_MAXの数値は無視されます）',
            defaultValue=False))
        elev_margin=QgsProcessingParameterNumber('ELEV_MARGIN',
            '自動検出時の余白（m。入力データの最小値から差し引き、最大値に加える）',
            QgsProcessingParameterNumber.Double,50.,minValue=0.,maxValue=1000.)
        elev_margin.setFlags(elev_margin.flags() | Qgis.ProcessingParameterFlag.Advanced)
        self.addParameter(elev_margin)
        self.addParameter(QgsProcessingParameterEnum('RENDER_MODE','描画方式',
            ['独自方式 v0.4互換','FMEマニュアル方式'],defaultValue=0))
        self.addParameter(QgsProcessingParameterEnum('LEGACY_PRESET','独自方式の色設定',
            ['従来標準','カスタム','従来淡色','従来地形強調','グレースケール'],defaultValue=0))
        self.addParameter(QgsProcessingParameterEnum('FME_STRETCH','FME RGBストレッチ',
            ['なし','長野県実績値（R 65–234、G 57–229、B 66–216）','カスタム'],defaultValue=1))
        for name,label,rgb in LEGACY_PALETTE:
            param=QgsProcessingParameterColor('LEGACY_'+name.upper(),label,QColor(*rgb),opacityEnabled=False)
            param.setFlags(param.flags() | Qgis.ProcessingParameterFlag.Advanced);self.addParameter(param)
        for name,label,rgb in FME_PALETTE:
            param=QgsProcessingParameterColor('FME_'+name.upper(),label,QColor(*rgb),opacityEnabled=False)
            param.setFlags(param.flags() | Qgis.ProcessingParameterFlag.Advanced);self.addParameter(param)
        for band,lo,hi in [('R',65.,234.),('G',57.,229.),('B',66.,216.)]:
            for suffix,label,value in [('MIN','下限',lo),('MAX','上限',hi)]:
                param=QgsProcessingParameterNumber('FME_'+band+'_'+suffix,
                    'FME カスタムストレッチ '+band+' '+label,QgsProcessingParameterNumber.Double,
                    value,minValue=-1000000.,maxValue=1000000.)
                param.setFlags(param.flags() | Qgis.ProcessingParameterFlag.Advanced);self.addParameter(param)
        for name,label,value,lo,hi in COLOR_NUMBERS:
            self.addParameter(QgsProcessingParameterNumber(name.upper(),label,
                QgsProcessingParameterNumber.Double,value,minValue=lo,maxValue=hi))
        self.addParameter(QgsProcessingParameterBoolean('METRES',
            '全入力の標高がm単位で、鉛直基準が統一済みであることを確認した',False))
        nd=QgsProcessingParameterNumber('NODATA','入力NoDataを上書き（空欄なら入力の定義を使用）',
            QgsProcessingParameterNumber.Double,optional=True)
        nd.setFlags(nd.flags() | Qgis.ProcessingParameterFlag.Advanced)
        self.addParameter(nd)
        compression=QgsProcessingParameterEnum('COMPRESSION','図郭GeoTIFFの圧縮',
            ['DEFLATE（可逆圧縮）','NONE（非圧縮）'],defaultValue=0)
        compression.setFlags(compression.flags() | Qgis.ProcessingParameterFlag.Advanced)
        self.addParameter(compression)
        self.addParameter(QgsProcessingParameterBoolean('XYZ','XYZタイルも生成する（EPSG:3857、256px）',True))
        self.addParameter(QgsProcessingParameterEnum('XYZ_FORMAT','XYZ画像形式',
            ['PNG','WebP（要GDAL WEBPドライバ）'],defaultValue=0))
        webp_lossless=QgsProcessingParameterBoolean('XYZ_WEBP_LOSSLESS',
            'WebPを可逆(lossless)にする（無効の場合は下のQUALITYを使う非可逆(lossy)）',True)
        webp_lossless.setFlags(webp_lossless.flags() | Qgis.ProcessingParameterFlag.Advanced)
        self.addParameter(webp_lossless)
        webp_quality=QgsProcessingParameterNumber('XYZ_WEBP_QUALITY',
            'WebP非可逆時のQUALITY（1-100、既定75）',QgsProcessingParameterNumber.Integer,
            75,minValue=1,maxValue=100)
        webp_quality.setFlags(webp_quality.flags() | Qgis.ProcessingParameterFlag.Advanced)
        self.addParameter(webp_quality)
        for key,label,default,lo,hi in [
            ('XYZ_MIN','XYZ最小ズーム',12,0,24),
            ('XYZ_MAX','XYZ最大ズーム',16,0,24),
            ('XYZ_LIMIT','XYZ候補枚数の上限',100000,1,10000000)]:
            self.addParameter(QgsProcessingParameterNumber(key,label,
                QgsProcessingParameterNumber.Integer,default,minValue=lo,maxValue=hi))
        self.addOutput(QgsProcessingOutputFolder('XYZ_FOLDER','XYZタイルフォルダー'))
        self.addParameter(QgsProcessingParameterBoolean('MERGED_GEOTIFF',
            '図郭タイルに加えて、全域CS方式画像を結合済み1枚のGeoTIFFとしても出力する',True))
        self.addParameter(QgsProcessingParameterBoolean('LOAD','終了後に全域CS画像と図郭索引を読み込む',True))
        self.addParameter(QgsProcessingParameterFolderDestination('OUTPUT','出力先の親フォルダー'))
        self.addOutput(QgsProcessingOutputRasterLayer('CS_IMAGE','全域CS方式画像'))
        self.addOutput(QgsProcessingOutputRasterLayer('CS_MERGED_GEOTIFF','全域CS方式画像（結合GeoTIFF）'))
        self.addOutput(QgsProcessingOutputVectorLayer('SHEET_INDEX','出力図郭索引'))
        self.addOutput(QgsProcessingOutputFile('MANIFEST','処理記録'))
        self.addOutput(QgsProcessingOutputFolder('INPUT_WORK','入力変換の中間成果・点群分類結果'))

    def prepareAlgorithm(self, parameters, context, feedback):
        # Resolve project-owned layers on the main thread; keep plain data only.
        from .engine.pipeline import validate_config, COLOR_DEFAULTS
        from .engine.color_fme import FME_COLORS, FME_WEIGHTS
        from .engine.input_sources import explicit_file_parameter, _absolute_path, EXTENSIONS
        from .engine.pipeline import version_banner
        feedback.pushInfo(version_banner())
        mode=['raster','gsi','text','lidar','forest'][self.parameterAsEnum(parameters,'INPUT_TYPE',context)]
        layers=self.parameterAsLayerList(parameters,'DEMS',context) if mode=='raster' else []
        # Read the raw FILES value only. In QGIS 3.44, QgsProcessingParameters
        # .parameterAsFileList() was observed (2026-09-30, user report) to return
        # a completely unrelated stale path (a Windows special folder such as
        # "Documents/My Music") even though the official "入力パラメータ" log
        # dump and this raw dict both showed FILES as None/empty at the same
        # moment. Since the raw parameters dict has matched reality in every
        # observed case (both when a value was present and when it was empty),
        # it alone decides whether files were explicitly selected; the
        # unreliable parameterAsFileList() fallback that used to run when
        # raw_files was empty has been removed entirely, rather than trusted
        # for a "maybe more accurate" empty-case value.
        # 未確認の残存リスク：このフォールバックは元々、生パラメータ側が異常値を
        # 返す別の不具合への対策として追加されていた（詳細な経緯は現行コードから
        # 追跡できず未確認）。今回の実測（異常時・正常時の両方でraw_filesが実態と
        # 一致）を根拠に削除するが、将来「生パラメータが空でないのに実際の選択と
        # 食い違う」という逆パターンが再発する可能性は否定できない。
        raw_files=parameters.get('FILES')
        raw_present=not QgsVariantUtils.isNull(raw_files) and raw_files not in ('',[])
        paths=explicit_file_parameter(raw_files) if raw_present else []
        # v0.9.3: 個別ファイル選択（FILESパラメータでのチェックボックス方式）は、
        # QGIS自身のProcessingフレームワークが実行時に選択件数分のレイヤー解決を
        # 試みるため、件数が多い（実測で数百～千件超）と主スレッドが長時間
        # 「応答なし」になることを確認済み（ユーザー報告、2026-09-30。MORIZON
        # 監視ツールで約56分の無応答を実測）。この根本原因はQGIS本体側の挙動で
        # あり本プラグインのPythonコードでは直接制御できないため、事前に件数を
        # 検査し、閾値超過時は処理を開始せず「入力フォルダー」の使用を明確に
        # 案内する。閾値(INDIVIDUAL_FILE_SELECTION_LIMIT)は暫定値であり、実運用
        # での再調整を想定する。
        if raw_present and len(paths) > INDIVIDUAL_FILE_SELECTION_LIMIT:
            raise QgsProcessingException(
                f'個別ファイル選択が{len(paths)}件と多いため処理を開始しません'
                f'（上限{INDIVIDUAL_FILE_SELECTION_LIMIT}件）。QGIS自身の内部処理により'
                'QGISが長時間「応答なし」になることが確認されています。'
                '「入力フォルダー」を指定する方法に切り替えてください。')
        folder=self.parameterAsFile(parameters,'INPUT_FOLDER',context)
        if paths and folder:
            feedback.pushInfo('入力ファイルが明示指定されているため、入力フォルダーは使用しません: '+folder)
        elif folder:paths.append(folder)
        explicit_paths=list(paths) if paths else []
        if len(paths) <= 10:
            for path in paths:feedback.pushInfo('画面指定入力: '+path)
        elif paths:
            feedback.pushInfo(f'画面指定入力: {len(paths)}件（ログには先頭3件と末尾1件のみ表示）')
            for path in paths[:3]:feedback.pushInfo('  '+path)
            feedback.pushInfo('  …')
            feedback.pushInfo('  '+paths[-1])
        for layer in layers:
            decoded=QgsProviderRegistry.instance().decodeUri(layer.providerType(),layer.source())
            path=decoded.get('path',layer.source())
            if layer.providerType() != 'gdal' or not Path(path).is_file() or str(layer.source()).startswith(('NETCDF:','HDF')):
                raise QgsProcessingException('入力はローカルの単バンドDEMファイルにしてください。WMSや仮想サブデータセットは事前にGeoTIFFへ保存します。')
            if layer.bandCount() != 1:
                raise QgsProcessingException('RGB画像ではなく、標高値を持つ単バンドDEMを選択してください。')
            if str(Path(path).resolve()) not in paths:paths.append(str(Path(path).resolve()))
        if not paths:raise QgsProcessingException('入力ファイルまたはフォルダーを指定してください。')
        source=self.parameterAsCrs(parameters,'INPUT_CRS',context)
        source_value=parameters.get('INPUT_CRS')
        source_set=not QgsVariantUtils.isNull(source_value) and str(source_value).strip()!=''
        if source_set and not source.isValid():raise QgsProcessingException('入力座標系が無効です。')
        try:
            columns=[int(v.strip()) for v in self.parameterAsString(parameters,'TEXT_COLUMNS',context).split(',')] if mode=='text' else [1,2,3]
            classes=[int(v.strip()) for v in self.parameterAsString(parameters,'GROUND_CLASSES',context).split(',')] if mode=='lidar' else [2]
        except ValueError as exc:raise QgsProcessingException('列番号・分類コードは整数をカンマで区切って指定してください。') from exc
        crs_raw=parameters.get('CRS')
        crs_set=not QgsVariantUtils.isNull(crs_raw) and str(crs_raw).strip()!=''
        if crs_set:
            crs=self.parameterAsCrs(parameters,'CRS',context)
            if not crs.isValid():raise QgsProcessingException('有効な出力座標系を選択してください。')
        else:
            # v0.9.3: CRSが未指定の場合、入力(先頭のラスターファイル)のCRSから
            # 平面直角座標系第I～XIX系を自動推定する（ユーザー要望、2026-09-30）。
            # あくまで「入力が既にJPRゾーンの1つである場合にそれを推定するだけ」で
            # あり、任意の座標系から最寄りのゾーンへ変換・推測することはしない
            # （黙ったフォールバックは行わない設計方針を維持するため）。
            # v0.10.2: ラスター以外の入力は、「入力の水平座標系」やLAS/LAZのヘッダーが
            # 平面直角座標系であればそれを使う。推定しない条件（系の食い違い、測地系が
            # 分からない森林LEMなど）は engine/zone_inference.py を参照。
            if mode != 'raster':
                from osgeo import osr as _osr
                from .engine.pipeline import _jpr_zone_of
                from .engine.zone_inference import infer_target_crs
                inferred_wkt,reason=infer_target_crs(
                    mode,source.toWkt() if source_set else '',paths,
                    self.parameterAsBool(parameters,'RECURSIVE',context),_osr,_jpr_zone_of)
                if inferred_wkt is None:
                    raise QgsProcessingException(
                        '出力座標系（CRS）を自動推定できませんでした（'+reason+'）。'
                        '出力の平面直角座標系を明示的に選択してください。')
                crs=QgsCoordinateReferenceSystem(inferred_wkt)
                if not crs.isValid():
                    raise QgsProcessingException('入力から自動推定した出力座標系が無効です。')
                feedback.pushInfo('出力座標系を自動推定しました: '+crs.authid()+'。'+reason)
            else:
                if not paths:
                    raise QgsProcessingException('入力ファイルまたはフォルダーを指定してください。')
                from osgeo import gdal as _gdal
                from .engine.pipeline import infer_target_crs_from_raster
                from .engine.input_sources import crs_probe_raster
                try:
                    probe_path=crs_probe_raster(paths[0],self.parameterAsBool(parameters,'RECURSIVE',context),feedback)
                except ValueError as exc:
                    raise QgsProcessingException(
                        '出力座標系（CRS）が未指定で、入力「'+paths[0]+'」から自動推定に使える'
                        'ラスターファイルが見つかりませんでした（'+str(exc)+'）。CRSを明示的に選択してください。')
                if probe_path!=paths[0]:
                    feedback.pushInfo('入力フォルダー内の先頭のラスターファイルで出力座標系を推定します: '+probe_path)
                inferred_wkt,reason=infer_target_crs_from_raster(probe_path,_gdal,feedback=feedback)
                if inferred_wkt is None:
                    raise QgsProcessingException(
                        '出力座標系（CRS）が未指定で、かつ入力「'+probe_path+'」から'
                        '自動推定できませんでした（'+reason+'）。CRSを明示的に選択してください。')
                crs=QgsCoordinateReferenceSystem(inferred_wkt)
                if not crs.isValid():
                    raise QgsProcessingException('入力から自動推定した出力座標系が無効です: '+probe_path)
                feedback.pushInfo('出力座標系を入力から自動推定しました（'+probe_path+'）: '+crs.authid())
        render_mode=['independent_v040','fme_manual'][self.parameterAsEnum(parameters,'RENDER_MODE',context)]
        legacy_preset=self.parameterAsEnum(parameters,'LEGACY_PRESET',context)
        color=dict(COLOR_DEFAULTS)
        if legacy_preset == 1:
            for name,_,_ in LEGACY_PALETTE:
                qcolor=self.parameterAsColor(parameters,'LEGACY_'+name.upper(),context)
                if not qcolor.isValid():raise QgsProcessingException('有効な独自方式の色を指定してください: '+name)
                color[name]=[qcolor.red(),qcolor.green(),qcolor.blue()]
            for name,_,_,_,_ in COLOR_NUMBERS:
                color[name]=self.parameterAsDouble(parameters,name.upper(),context)
        elif legacy_preset == 2:
            color.update(slope_darkness=.35,curvature_strength=.75,elevation_mix=.08,saturation=.85,gamma=1.10)
        elif legacy_preset == 3:
            color.update(slope_darkness=.50,elevation_mix=.05,saturation=1.10,contrast=1.05)
        elif legacy_preset == 4:
            color.update(saturation=0,elevation_mix=0)
        fme_colors=dict(FME_COLORS)
        for name,_,_ in FME_PALETTE:
            qcolor=self.parameterAsColor(parameters,'FME_'+name.upper(),context)
            if not qcolor.isValid():raise QgsProcessingException('有効なFME方式の色を指定してください: '+name)
            fme_colors[name]=[qcolor.red(),qcolor.green(),qcolor.blue()]
        stretch_mode=['none','nagano_reference','custom'][self.parameterAsEnum(parameters,'FME_STRETCH',context)]
        stretch_ranges=[[self.parameterAsDouble(parameters,'FME_'+band+'_MIN',context),
                         self.parameterAsDouble(parameters,'FME_'+band+'_MAX',context)] for band in 'RGB']
        fme=dict(colors=fme_colors,weights=dict(FME_WEIGHTS),stretch_mode=stretch_mode,
                 stretch_ranges=stretch_ranges)
        parent=Path(self.parameterAsFileOutput(parameters,'OUTPUT',context))
        name='csmap_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:6]
        self.result_dir=parent/name
        nd=parameters.get('NODATA')
        c=dict(inputs=paths,output_dir=str(self.result_dir),target_crs=crs.toWkt(),
            input_type=mode,recursive=self.parameterAsBool(parameters,'RECURSIVE',context),
            normalize_rasters=self.parameterAsBool(parameters,'NORMALIZE',context),
            input_crs=source.toWkt() if source_set else '',
            vertical_reference=self.parameterAsString(parameters,'VERTICAL',context),
            lidar_mode=['classified','ground_only','auto'][self.parameterAsEnum(parameters,'LIDAR_MODE',context)],
            ground_classes=classes,pdal_path=self.parameterAsFile(parameters,'PDAL',context),
            point_method=['idw','mean','min'][self.parameterAsEnum(parameters,'POINT_METHOD',context)],
            point_radius=self.parameterAsDouble(parameters,'POINT_RADIUS',context),
            text_mode=['grid','points'][self.parameterAsEnum(parameters,'TEXT_MODE',context)],
            text_delimiter=['comma','tab','space','semicolon'][self.parameterAsEnum(parameters,'TEXT_DELIMITER',context)],
            text_encoding=self.parameterAsString(parameters,'TEXT_ENCODING',context),
            text_skip_rows=self.parameterAsInt(parameters,'TEXT_SKIP',context),
            text_columns=columns,text_axis_order=['east_north','north_east'][self.parameterAsEnum(parameters,'TEXT_AXES',context)],
            text_grid_cell=self.parameterAsDouble(parameters,'TEXT_CELL',context),
            forest_axis_order=['north_east','east_north'][self.parameterAsEnum(parameters,'FOREST_AXES',context)],
            forest_grid_cell=self.parameterAsString(parameters,'FOREST_CELL',context).strip().lower(),
            forest_lem_coordinate_scale=self.parameterAsString(parameters,'LEM_SCALE',context),
            forest_nodata=self.parameterAsDouble(parameters,'FOREST_NODATA',context),
            point_tile_size=self.parameterAsInt(parameters,'POINT_TILE',context),
            max_points_auto=self.parameterAsInt(parameters,'AUTO_LIMIT',context),
            plane_zone=None,
            sheet_level=[5000,2500,1000,500][self.parameterAsEnum(parameters,'LEVEL',context)],
            cell_size=self.parameterAsDouble(parameters,'CELL',context),
            sigma_m=self.parameterAsDouble(parameters,'SIGMA',context),
            curvature_limit=self.parameterAsDouble(parameters,'CURVE_LIMIT',context),
            slope_max=self.parameterAsDouble(parameters,'SLOPE_MAX',context),
            slope_algorithm=['horn','central_difference'][self.parameterAsEnum(parameters,'SLOPE_ALGORITHM',context)],
            elevation_range=[self.parameterAsDouble(parameters,'ELEV_MIN',context),
                             self.parameterAsDouble(parameters,'ELEV_MAX',context)],
            elevation_range_auto=self.parameterAsBool(parameters,'ELEV_AUTO',context),
            elevation_range_margin=self.parameterAsDouble(parameters,'ELEV_MARGIN',context),
            xyz_enabled=self.parameterAsBool(parameters,'XYZ',context),
            xyz_format=['png','webp'][self.parameterAsEnum(parameters,'XYZ_FORMAT',context)],
            xyz_webp_lossless=self.parameterAsBool(parameters,'XYZ_WEBP_LOSSLESS',context),
            xyz_webp_quality=self.parameterAsInt(parameters,'XYZ_WEBP_QUALITY',context),
            xyz_min_zoom=self.parameterAsInt(parameters,'XYZ_MIN',context),
            xyz_max_zoom=self.parameterAsInt(parameters,'XYZ_MAX',context),
            xyz_max_tiles=self.parameterAsInt(parameters,'XYZ_LIMIT',context),
            color=color,render_mode=render_mode,fme=fme,
            confirm_elevation_metres=self.parameterAsBool(parameters,'METRES',context),
            source_nodata=None if QgsVariantUtils.isNull(nd) or nd == '' else self.parameterAsDouble(parameters,'NODATA',context),
            compression=['DEFLATE','NONE'][self.parameterAsEnum(parameters,'COMPRESSION',context)],
            merged_geotiff_enabled=self.parameterAsBool(parameters,'MERGED_GEOTIFF',context))
        if render_mode == 'independent_v040' and legacy_preset != 1:
            c.update(curvature_limit=.05,elevation_range=[0.,3000.],elevation_range_auto=False)
        for key in ('smrf_cell','smrf_slope','smrf_threshold','smrf_scalar','smrf_window'):
            c[key]=self.parameterAsDouble(parameters,key.upper(),context)
        profile_choice=self.parameterAsEnum(parameters,'PROFILE',context)
        if profile_choice in (1,2):
            # 傾斜計算アルゴリズム(SLOPE_ALGORITHM)はプロファイルで上書きせず、
            # 利用者の選択（既定Horn法）をそのまま使う（v0.10.0、ユーザー決定）。
            c.update(cell_size=1. if profile_choice==1 else 2.,sigma_m=3.,curvature_limit=.1,
                     slope_max=60.,elevation_range=[200.,2000.],elevation_range_auto=False,
                     render_mode='fme_manual',fme=fme)
            feedback.pushInfo('組込み設定プロファイルを適用しました: '+('標準CS・1m' if profile_choice==1 else '試験処理・2m'))
        elif profile_choice==3:
            # Separate, opt-in provisional value (not the manual's own figure).
            # Never overwrites the FME manual default
            # (profile_choice 1/2) silently; the person must choose this profile explicitly.
            c.update(cell_size=1.,sigma_m=3.,curvature_limit=.03,
                     slope_max=60.,elevation_range=[200.,2000.],elevation_range_auto=False,
                     render_mode='fme_manual',fme=fme)
            feedback.pushInfo('組込み設定プロファイルを適用しました: 林野庁近似設定（暫定）（曲率±0.03）')
        elif profile_choice==4:
            profile_path=self.parameterAsFile(parameters,'PROFILE_FILE',context)
            if not profile_path:raise QgsProcessingException('外部JSONプロファイルを選択してください。')
            try:data=json.loads(Path(profile_path).read_text(encoding='utf-8-sig'))
            except (OSError,ValueError) as exc:raise QgsProcessingException('設定プロファイルを読み込めません: '+str(exc)) from exc
            saved=data.get('settings',data)
            protected={'inputs','output_dir','target_crs','plane_zone','input_type','confirm_elevation_metres'}
            unknown=set(saved)-set(c)-protected-{'color_model'}
            if unknown:raise QgsProcessingException('設定プロファイルに不明な項目があります: '+repr(sorted(unknown)))
            c.update({k:v for k,v in saved.items() if k in c and k not in protected})
            if 'render_mode' not in saved and saved.get('color_model') in ('legacy','fme'):
                c['render_mode']={'legacy':'independent_v040','fme':'fme_manual'}[saved['color_model']]
            if 'render_mode' not in saved and 'color_model' not in saved:
                c['render_mode']='independent_v040'
                feedback.pushInfo('旧設定プロファイルのため、従来の色合成方式で再現します。')
            feedback.pushInfo('設定プロファイルを読み込みました: '+profile_path)
            from .engine.pipeline import missing_slope_algorithm_notice
            notice=missing_slope_algorithm_notice(saved,c['slope_algorithm'])
            if notice:feedback.pushWarning(notice)
        try:self.settings=validate_config(c,Path.cwd(),feedback=feedback)
        except (ValueError,TypeError,OSError) as exc:raise QgsProcessingException(str(exc)) from exc
        from .engine.pipeline import SLOPE_ALGORITHM_NAMES
        feedback.pushInfo('傾斜計算方式: '+SLOPE_ALGORITHM_NAMES[self.settings['slope_algorithm']])
        save_value=parameters.get('SAVE_PROFILE')
        if not QgsVariantUtils.isNull(save_value) and str(save_value).strip():
            save_path=Path(self.parameterAsFileOutput(parameters,'SAVE_PROFILE',context))
            excluded={'inputs','output_dir','target_crs','plane_zone','input_type','confirm_elevation_metres'}
            payload={'schema':'csmap-settings-profile-v3','settings':{k:v for k,v in self.settings.items() if k not in excluded}}
            try:save_path.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
            except OSError as exc:raise QgsProcessingException('設定プロファイルを保存できません: '+str(exc)) from exc
            feedback.pushInfo('設定プロファイルを保存しました: '+str(save_path))
        direct_file_selection = bool(explicit_paths) and all(
            Path(path).suffix.lower() in EXTENSIONS[mode] and not glob.has_magic(path)
            for path in explicit_paths)
        if direct_file_selection:
            expected=list(dict.fromkeys(_absolute_path(path) for path in explicit_paths))
            actual=self.settings['inputs']
            if actual != expected:
                raise QgsProcessingException('入力一覧の不一致を検出したため、処理を開始しません。画面指定: '
                    +repr(expected)+' / 内部処理対象: '+repr(actual))
            feedback.pushInfo('入力一覧照合OK: '+str(len(actual))+'ファイル')
        self.result_dir=Path(self.settings['output_dir'])
        self.load_outputs=self.parameterAsBool(parameters,'LOAD',context)
        return True

    def processAlgorithm(self, parameters, context, feedback):
        from .engine.pipeline import run
        from .engine.filters import BACKEND
        from .engine.progress import CancelledError
        feedback.pushInfo('計算バックエンド: '+BACKEND)
        feedback.pushInfo('出力: '+str(self.result_dir))
        try:run(self.settings,feedback)
        except CancelledError as exc:raise QgsProcessingException(str(exc)) from exc
        except Exception as exc:
            if feedback.isCanceled():raise QgsProcessingException('キャンセルしました。部分成果は未完了です。') from exc
            raise QgsProcessingException('CS処理に失敗しました: '+str(exc)) from exc
        outputs={'OUTPUT':str(self.result_dir),'CS_IMAGE':str(self.result_dir/'cs_relief.vrt'),
                 'SHEET_INDEX':str(self.result_dir/'sheet_index.gpkg'),
                 'MANIFEST':str(self.result_dir/'run.json')}
        outputs['INPUT_WORK']=str(self.result_dir/'input') if (self.result_dir/'input').is_dir() else ''
        outputs['XYZ_FOLDER']=str(self.result_dir/'xyz') if self.settings['xyz_enabled'] else ''
        outputs['CS_MERGED_GEOTIFF']=str(self.result_dir/'cs_relief_merged.tif') if self.settings['merged_geotiff_enabled'] else ''
        if self.load_outputs and context.project() is not None:
            for key,label in [('CS_IMAGE','CS方式立体図'),('SHEET_INDEX','CS出力図郭')]:
                context.addLayerToLoadOnCompletion(outputs[key],
                    QgsProcessingContext.LayerDetails(label,context.project(),key))
        return outputs
