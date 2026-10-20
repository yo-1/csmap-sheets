# v0.12.3 図版の再撮影・実機確認チェックリスト

基準main: `12447d3f7cf8a04bb1e63d798ddc189f5976c889`。未撮影・未実機確認。マニュアルv0.5原本未取得のため既存図番号は未対応。Libraryの画像にはv0.12.2が含まれるという依頼条件に従い、撮影版が不明な画像をv0.12.3の証跡に使わない。

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

原本受領後、既存図を1行ずつ登録する。撮影完了前にチェックを付けない。

| マニュアル節／図番号 | 既存画像の撮影版・出典 | 対応F ID | 新画像ファイル | 試験ID・設定・run.json | OS/QGIS/DPI | 結果・撮影日 |
|---|---|---|---|---|---|---|
| 原本未取得 | Libraryの過去画像は版未確認 | 未対応 | 未撮影 | 未実施 | 未確認 | 保留 |

既存の受入手順: [docs/validation/ui-fixes-0.12.3.md:1–45](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/docs/validation/ui-fixes-0.12.3.md#L1-L45)。既存のLinux/QGIS試験結果はWindows撮影完了の代替にしない。マニュアル原本の図番号対応と必須F01～F08の証跡が揃うまでは、図版更新完了としない。
