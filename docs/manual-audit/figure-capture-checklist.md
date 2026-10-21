# v0.12.3 図版の再撮影・実機確認チェックリスト

## 現在の監査基準：Drive版v0.8（2026-10-20）

ユーザーの「0.8で進めてください」により、**Drive版v0.8を今回の基準資料とし、v0.5比較は対象外**とする。過去の未取得・比較待ち記録は履歴であり、v0.5原本を今回の完了条件として要求しない。

- 原本: [CS_Map_Sheets_利用手順書_操作実務v0.8_20261020.md](https://drive.google.com/file/d/1HN-oR11516UTGDwGjQGcoP4-1fAY54Wk/view?usp=drivesdk)
- DriveファイルID: `1HN-oR11516UTGDwGjQGcoP4-1fAY54Wk`、サイズ61957 bytes、更新2026-10-20T12:35:49.901Z（Driveメタデータ）。チェックサムは未取得。
- 1～34章の本文を取得。貼付稿R34と章構成、R01（§4手順10）・R02（§13.2）の対象文が対応することを確認した。全文バイト一致とは認定しない。
- 表紙v0.3・本文v0.7・v0.8追補の混在は原本にも残る。ファイル名とユーザー指定によりv0.8として扱い、版表記の統一を編集者へ提案する。
- 編集者向けの[監査結果・差替え指示](https://docs.google.com/document/d/1Da3-oGSzWZKPxIX6dWxrwkLyUD9WN6dvhBUvoNYVi8I/edit?usp=drivesdk)を同じDriveフォルダーへ保存し、本文と13行×3列の実効値表を読み戻して一致確認した。原本MD・Word・PDFは変更していない。

実装基準は `12447d3f7cf8a04bb1e63d798ddc189f5976c889`（v0.12.3）。計算コード・既定値は変更しない。Windows/QGIS実機、元PNG、比較研究、Word/PDFのページ校正は未確認。Draft PR #47はレビュー前にマージしない。

基準main: `12447d3f7cf8a04bb1e63d798ddc189f5976c889`。未撮影・未実機確認。貼付稿R34の章・図候補と下表で対応付けた。v0.5比較は今回対象外。Word/PDFページ番号は未対応。Libraryの画像にはv0.12.2が含まれるという依頼条件に従い、撮影版が不明な画像をv0.12.3の証跡に使わない。

## 撮影前の共通記録

- [ ] v0.12.3の導入ZIPとSHA-256、ソースcommit、metadata/VERSIONを照合し、旧版を更新後QGISを再起動する。mainの版表示と公式公開版は分けて書く。
- [ ] OS、QGIS、Qt、GDAL、PDAL（使用時）、filter backend、画面解像度・DPI・表示倍率・撮影日時を記録する。
- [ ] 履歴・既存プロファイルが初期値に影響しない試験用プロジェクトを使う。初期値画面とプロファイル適用画面を区別する。
- [ ] 入力DEMの取得元・利用条件・加工、範囲、水平／鉛直基準、セル間隔、NoDataを記録し、配布可能な小範囲で確認する。
- [ ] キャプチャと設定JSON・ログ・run.json・GPKG/QML・出力画像を同じ試験IDへ紐付ける。個人名・共有パスなど公開不適切な情報はマニュアル掲載前に確認する。

## v0.12.2画像から必ず差し替える箇所

| ID | 撮影対象・操作 | 合格条件／画面に含める内容 | 優先度 | 根拠 |
|---|---|---|---|---|
| F01 | 処理ダイアログの先頭と右側ヘルプ | 版バナーv0.12.3。GeoTIFF入力セル間隔自動取得、テキスト欄不要、出力格子との違いを読める幅で撮る | 必須 | [csmap_sheets/algorithm.py:169–185](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L169-L185) |
| F02 | 詳細パラメータのJSON保存欄と「…」 | 現行の保存先選択UI、保存ダイアログ、JSONフィルターを撮る。v0.12.2のテキスト欄画像を流用しない | 必須 | [csmap_sheets/algorithm.py:235–249](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L235-L249)、[csmap_sheets/profile_widget.py:46–57](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/profile_widget.py#L46-L57) |
| F03 | 拡張子なしsettingsで保存 | 補完後settings.jsonの最終名を確認し、実ファイル名と再読込成功を記録。.json/.JSONを二重付与しないケースも確認 | 必須 | [csmap_sheets/profile_paths.py:4–9](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/profile_paths.py#L4-L9) |
| F04 | 既存settings.jsonへ拡張子なしで保存、No／取消 | 確認ダイアログに最終.json名を表示、既定No。No／取消後の既存内容・更新日時（可能ならハッシュ）が不変。Yesは試験用コピーで確認 | 必須 | [csmap_sheets/profile_widget.py:33–57](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/profile_widget.py#L33-L57) |
| F05 | 保存欄へ既存名を直接入力して実行 | value()で同じ最終名の上書き確認。Noでは既存内容を維持。未確認のまま処理開始しないことを実機確認 | 必須 | [csmap_sheets/profile_widget.py:59–68](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/profile_widget.py#L59-L68) |
| F06 | 新規処理後の地図キャンバスとレイヤ一覧 | CS画像上の索引が塗りなし・枠線。sheet_index.gpkgと隣接sheet_index.qmlの2ファイルも撮る | 必須 | [csmap_sheets/engine/output_style.py:4–29](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/output_style.py#L4-L29) |
| F07 | GPKG手動再読込と旧プロジェクト | 新規読込の枠線を確認。旧プロジェクトに保存済みの塗りは自動更新されないことを区別し、QMLの手動スタイル読込手順を撮る。QMLも一緒に移動 | 必須 | [csmap_sheets/README_ja.md:342](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/README_ja.md#L342) |
| F08 | TEXT_CELLとCELL欄 | 「規則格子テキスト専用・GeoTIFFでは不要」と「再投影後の計算・出力格子」を含む現行ラベル。0.5m GeoTIFF→出力1mの例で入力テキスト格子欄を変えない | 必須 | [csmap_sheets/algorithm.py:428–435](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L428-L435)、[csmap_sheets/algorithm.py:535–543](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L535-L543) |

F03～F05はWindowsネイティブ保存ダイアログで実施する。APIからのProcessing実行にはGUI確認がないので、GUIと同じ確認ダイアログを要求しない。

## v0.5図の版・記載内容に応じて差し替える箇所

| ID | 対象 | 撮影・確認内容 | 根拠 |
|---|---|---|---|
| F09 | 長い処理画面 | 【設定】【入力】【点群】【テキスト】【森林レーザ】【出力・図郭】【地形計算】【配色】【XYZ】【出力】の順序。複数枚に分けても前後の共通項目を残す。スクロールで値が変化しないこと、狭幅・高DPIで操作可能なことを確認 | [csmap_sheets/algorithm.py:71–145](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L71-L145)、[csmap_sheets/algorithm.py:824–836](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L824-L836) |
| F10 | 傾斜計算とσ | Horn初期／中央差分の選択肢、m/pxの指定方式と別々の値欄。σ=3px、CELL=0.5/1/2mの実効値1.5/3/6mをログ・run.jsonと照合。σ=0も確認 | [csmap_sheets/algorithm.py:545–588](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L545-L588)、[csmap_sheets/engine/pipeline.py:194–210](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L194-L210) |
| F11 | プロファイル・色設定 | 画面設定、標準CS1m、試験2m、暫定±0.03、外部JSONの違いを撮る。独自標準の実効±0.05と画面初期±0.1を混同しないようrun.jsonを添付。FME長野ストレッチは任意実績値と注記 | [csmap_sheets/algorithm.py:1301–1352](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L1301-L1352)、[csmap_sheets/algorithm.py:611–621](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L611-L621) |
| F12 | XYZ詳細 | PNG初期、WebP選択、lossless初期OFF、QUALITY75、zoom12～16・候補上限100000。透明境界の見え方とRGB/RGBAの扱いは実ファイルで確認 | [csmap_sheets/algorithm.py:727–776](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L727-L776)、[csmap_sheets/README_ja.md:261–291](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/README_ja.md#L261-L291) |
| F13 | 入力選択とCRS | 形式別に関係する設定だけを使う。LAS/LAZのPDAL、LEM+同stem CSV/TXT、テキスト軸順序、入力水平CRS、出力CRS推定の成功／指定必要例。個別選択30件とフォルダー指定を区別 | [csmap_sheets/algorithm.py:250–472](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L250-L472)、[csmap_sheets/algorithm.py:838–863](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L838-L863) |
| F14 | 出力フォルダー・完了 | sheets、結合TIFF、索引GPKG/QML、VRT、XYZ、run.json.status=completed。MERGED_GEOTIFFとXYZのOFFも確認。終了後の自動読込はVRTと索引であることを示す | [csmap_sheets/engine/pipeline.py:1267–1324](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L1267-L1324)、[csmap_sheets/algorithm.py:1524–1555](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L1524-L1555) |
| F15 | NoData／外縁 | 有効な標高0m、欠測孔、外周を含む小DEMで透明境界を確認。黒を欠測と説明しない。smoothing・CELL・傾斜法をキャプションに併記 | [csmap_sheets/engine/pipeline.py:270–338](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L270-L338) |
| F16 | QGIS標準の仮想ラスタを構築 | 掲載するなら「QGIS標準機能の任意の前処理」と明記。CS Map Sheetsの固有ダイアログ・必須機能と誤認させない。複数DEMは直接まとめて入力できる説明と整合させる | [csmap_sheets/algorithm.py:264–291](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L264-L291)、[csmap_sheets/engine/pipeline.py:1193–1198](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L1193-L1198) |

## 比較画像のキャプションに必要な情報

- [ ] プラグイン版・commit、方式（独自/FME）、傾斜法、出力セル、σの指定単位と指定値／実効値、曲率範囲、標高範囲、自動検出、色・ストレッチ、NoData、バックエンドを併記。
- [ ] DEMが人工か実測か、取得元・範囲・解像度・標高量子化・加工を示す。同じ条件でない比較の理由を記す。
- [ ] FME/PSSの実出力と比較したか、人工DEMでの数値試験か、単に外観比較かを明記。「最適」「完全一致」はその証拠と適用範囲がある場合だけ使用する。
- [ ] Draft PR #31のPSS近似モードを現行mainの機能として掲載しない。

## 図版台帳の記入欄

R34に挙がった図候補を下表に登録した。画像名と内容は制作側本文の申告であり、元PNGの受領・閲覧・撮影完了前にチェックを付けない。

| マニュアル節／図番号 | 既存画像の撮影版・出典 | 対応F ID | 新画像ファイル | 試験ID・設定・run.json | OS/QGIS/DPI | 結果・撮影日 |
|---|---|---|---|---|---|---|
| R34 §13～§18・§21・§28・§31 | 以下の候補表参照。制作側申告、原図未確認 | 以下参照 | 未撮影 | 未実施 | 未確認 | 保留 |

既存の受入手順: [docs/validation/ui-fixes-0.12.3.md:1–45](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/docs/validation/ui-fixes-0.12.3.md#L1-L45)。既存のLinux/QGIS試験結果はWindows撮影完了の代替にしない。Word/PDFの図番号対応と必須F01～F08の証跡が揃うまでは、図版更新完了としない。

## 版別図版の扱い（制作側連絡の反映）

撮影版を確認できたv0.12.2画像は「旧版（プラグインv0.12.2）」と明記し、撮影版不明の画像は「版未確認」とする。現行v0.12.3の再撮影と区別する。v0.5とR34（版名未統一の34章稿）ごとに節／図番号を記録する。R34本文の図候補対応は下表に記録し、画像の実体・流用状況は原本PNG受領後に確認する。QGIS標準の仮想ラスタ構築画面は「QGIS標準機能」と表示する。

## R34貼付稿の図・画像候補との対応

**以下は原図を閲覧した結果ではない。** 画像名・撮影版・内容はR34本文の記述から転記した。本文に記載されない撮影版を周辺の画像から推定しない。旧画像の参考掲載と現行UIの実機確認を分離する。

| R34箇所・図候補 | 原画像（本文の記載） | 制作側の内容・版の申告 | 対応F ID／次の作業 | 監査側の確認状態 |
|---|---|---|---|---|
| §13.1 図13-1候補・§14/15/31 | image(20261017-022554).png | プラグインv0.12.2、配色・出力・保存画面 | F02～F08/F11/F12。旧版注記。現行の区分・順序・保存UIを再撮影 | 原図未取得 |
| §13.2 図13-2候補・§14/15 | image(20261017-022905).png | v0.12.2、1m処理ログ | F10/F14。R02に従い入力値と実効値を区別 | 原図・run.json未取得 |
| §13.2・§14/15/31 | image(20261017-024419).png | v0.12.2、0.5m処理ログ | F10/F14。保存設定・run.jsonとの対応が必要 | 原図・run.json未取得 |
| §13.3・§14/15 | image(20261017-022952).png | CS表示。個別画像に撮影版を特定できる証跡は未受領 | F06/F14/F15。欠測・縮尺・範囲の確認 | 原図未取得 |
| §13.3 | image(20261017-042916).png | MIERUNE成果、TIFFReadEncodedStrip failed表示 | 不具合説明専用。正常成果図に使わないという選定方針を維持 | エラー内容も原図未確認 |
| §13.4 図13-3候補・§14/15 | image(20261016-144216).png | MIERUNE人工地形0.5m | 比較用。DEM・格子・σ・表示条件を取得 | 原図・計算条件未取得 |
| §13.4 | image(20261016-145024).png | 人工地形の別表示 | 図13-3との役割・出典・条件を確定 | 原図未取得 |
| §13.4 図13-3候補・§14/15/31 | CSMap_Complex_Horn_CD_Difference_20261017.png | 1m、FME色、RGB差と傾斜角差、シアン円 | 左右の指標・単位・円の意味を原図で確認。一般的な優劣にしない | 原図・差分生成条件未取得 |
| §15/16 | image(20261017-012645).png / image(20261017-012659).png | QGIS情報、EPSG6676、0.5m、2000×1500、NoData=-9999等 | 入力点検用。例示値と実データの一致を確認 | 原図・元DEM未取得 |
| §15/17 | image(20261017-020143).png / image(20261017-020301).png / image(20261017-020339).png | QGIS標準VRT、64入力、平均解像度、ログ | F16。CS固有UIとしない。64件は標準VRT入力例でありプラグイン個別選択上限30件と混同しない | 原図・VRT未取得 |
| §21/31 | image(20261017-014839).png | QGIS標準VRTダイアログ | F16。標準機能と明記 | 原図未取得 |
| §21/31 | image(20261017-014559).png | 複数DEMの地図表示 | 入力配置確認用。完成CS成果としない | 原図未取得 |
| §21/31 | image(20261017-013321).png | QGIS標準ラスタ保存、EPSG6676、0.5m | 標準機能の前処理として掲載 | 原図未取得 |
| §21 | image(20261017-013418).png | Windowsの比較TIFFフォルダー | 原則不採用という編集方針。私的パスは原図で確認 | 原図未取得 |
| §15 | image(20261016-200238).png | QGIS登録サイトv0.12.2検査結果 | 公開管理用。Windows受入結果や0.12.3公開済み証拠に流用しない | 原図未取得 |
| §34 | 長野報告 図A-1～A-3／B-1～B-3 | 比較図・条件・掲載許諾の確認待ち | 比較報告書本体、図、条件、出典を取得 | 報告書・図未取得 |

## §28.1の撮影リストとF台帳の対応

| 原稿の番号 | 章内の対象 | F台帳 |
|---|---|---|
| 16 | ツールボックス位置・処理名・版 | F01/F09 |
| 17 | 入力形式・ファイル／フォルダー・入力CRS | F09/F13 |
| 18 | 出力CRS・CELL・図郭・方式・傾斜・σ | F08～F11/F13 |
| 19 | 配色・ストレッチ・XYZ・保存先 | F02～F05/F11/F12 |
| 20 | 正常終了・run.json・GPKG/QML | F06/F07/F14 |
| 21 | GeoTIFF表示・欠測・接合・ピクセル | F08/F14/F15 |

§12の「QGIS v0.12.2」はプラグインv0.12.2との表記混同なので訂正する（R09）。現行撮影はプラグインv0.12.3とQGIS 3.44系を別々に記録する。本文にある画像閲覧報告・ファイル複製制限を、この監査側で実行した操作の証跡とは扱わない。
