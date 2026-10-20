# マニュアル整合性・差異台帳（Draft）

## 監査対象の追加（2026-10-20）

[制作側のPR連絡](https://github.com/yo-1/csmap-sheets/pull/47#issuecomment-6290395663)を確認し、対象を**v0.5と最新版v0.8**へ拡張した。v0.8は「CS_Map_Sheets_利用手順書_操作実務v0.8_20261020」（Word・PDF・Markdown、34章）と報告されているが、本文・章構成・図版はまだ取得していない。34章という情報は制作側の申告であり、原本を読んで確認した値ではない。

これらは別のChatGPT会話内の成果物と報告されており、このチャットから本文を取得できる添付・ダウンロードURLは提供されていない。**v0.8のMarkdown（優先）またはWordをこのチャットへ再添付してもらう必要がある。** v0.5も未取得のため、過去版比較を完了するには同様に原本が必要。原本未照合22件は維持し、実在する誤りや照合済み項目として計上しない。

v0.8を現行記述の照合対象、v0.5を改訂差分の比較対象として別々に記録する。92項目の画面初期値と実効設定、根拠ソースの固定SHAは既存台帳を使用する。v0.9は制作中の後続版として扱い、受領前にv0.8を置き換えない。計算コード・既定値は変更せず、PR #47はDraftのままレビュー前にマージしない。

対象main: `12447d3f7cf8a04bb1e63d798ddc189f5976c889` (v0.12.3)、監査日2026-10-20 UTC。

**マニュアルv0.5・v0.8原本未取得のため、マニュアルの確定差異件数は未集計。** 以下のM番号は原文の引用ではなく、原本取得時の照合命題。記述が実在すると確認するまではマニュアルの誤りとして計上しない。節・ページ・図番号はすべて保留。取得済みの同梱README／INPUT_GUIDEは別の資料として扱う。

## 分類と重大度

| 分類 | 判定規則 |
|---|---|
| 正しい | 原文の条件・対象版を含め現行実装と一致 |
| 版依存 | 旧版では成立するが現行で変更。旧版仕様として残すなら版を併記 |
| 誤り | 対象版・条件の下でソースと矛盾。説明を修正し計算コードは変えない |
| 要実機確認 | 静的ソースだけでは表示・ドライバ挙動・実DEM比較の結果を確定できない |

原本未取得は上の四分類とは別の**照合状態**であり、『要実機確認』へ押し込めない。高=計算条件／誤入力／誤成果判断に影響、中=手順・版・成果物運用に影響、低=用語・帰属・補足。

## 原本取得後に照合する命題

全行の原本照合状態: **未照合**。分類欄は「当該命題が原本にあった場合」の判定案。M20/M21の断定部分は削り、確認が必要な比較・UI結果を実機試験へ送る。

| ID | 重大度 | 照合命題（原文引用ではない） | 分類案 | 修正案／現行の記述 | 根拠 |
|---|---|---|---|---|---|
| M01 | 高 | 傾斜は中央差分が既定 | 版依存 | v0.9.4以前の既定。現行はHorn。旧結果再現時に中央差分を明示する。 | [csmap_sheets/algorithm.py:579–588](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L579-L588)、[csmap_sheets/CHANGELOG.md:72–85](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/CHANGELOG.md#L72-L85) |
| M02 | 高 | 独自方式／FME方式が同じ計算・同じ色になる | 誤り | 地形量の傾斜法選択は共通だが、色合成は別。FMEは5層LUT加重和。画素完全一致は保証しない。 | [csmap_sheets/engine/pipeline.py:295–338](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L295-L338) |
| M03 | 高 | 曲率±0.03がすべての入力で最適 | 誤り | ±0.03は明示選択の暫定プロファイル。FME標準±0.1、独自標準±0.05。人工DEMだけの結果を現地最適化の根拠にしない。 | [csmap_sheets/algorithm.py:1301–1352](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L1301-L1352) |
| M04 | 高 | σは常にm／入力DEMの画素数 | 版依存 | v0.12.0以降m/pxを選択。pxは再投影後の計算格子。例:3pxは0.5m格子で1.5m。旧JSONにsigma_unitがなければm。 | [csmap_sheets/engine/pipeline.py:168–210](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L168-L210)、[csmap_sheets/algorithm.py:1397–1410](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L1397-L1410) |
| M05 | 高 | GeoTIFFでもテキスト入力格子間隔を設定する | 誤り | GeoTIFF入力間隔は自動取得。テキスト欄を変えず、出力CELLを指定する。案内追加は0.12.3。 | [csmap_sheets/algorithm.py:183–185](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L183-L185)、[csmap_sheets/algorithm.py:428–435](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L428-L435) |
| M06 | 高 | 欠測を0mで埋め、黒を透明化する | 誤り | 正常な0mを欠測化しない。入力NoData定義／上書きを使い、支持領域のsafe maskでalphaを作る。 | [csmap_sheets/engine/pipeline.py:270–294](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L270-L294)、[csmap_sheets/engine/pipeline.py:334–338](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L334-L338) |
| M07 | 中 | VRTは入力できない | 誤り | 標高ラスタ区分で.vrtも許可。GDALで読める単バンドDEM・CRS・格子等の制約は受ける。 | [csmap_sheets/engine/input_sources.py:66–72](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/input_sources.py#L66-L72)、[csmap_sheets/engine/pipeline.py:707–761](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L707-L761) |
| M08 | 高 | 任意のZIP/XMLを地理院DEMとして読み込める | 誤り | GSI DEM GMLの仕様を解析する。森林成果ZIPは森林区分。ZIP/XMLの拡張子だけで内容を保証しない。 | [csmap_sheets/engine/gsi_dem.py:62–110](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/gsi_dem.py#L62-L110)、[csmap_sheets/engine/input_sources.py:350–374](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/input_sources.py#L350-L374) |
| M09 | 高 | LEMは単体で使用、同名CSVのみ対応 | 版依存 | 現行は同stem CSVまたはTXTのメタデータが必須。CSV優先、内容の必須項目も検査。 | [csmap_sheets/engine/forest_dem.py:353–399](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/forest_dem.py#L353-L399) |
| M10 | 高 | 全形式でPDAL必須／QGISに点群が表示できれば外部PDAL不要 | 誤り | LAS/LAZと不規則テキスト点に外部PDAL>=2.9。通常ラスタ・GSI・規則格子は不要。 | [csmap_sheets/engine/input_sources.py:968–975](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/input_sources.py#L968-L975)、[csmap_sheets/engine/point_inputs.py:369–380](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/point_inputs.py#L369-L380) |
| M11 | 中 | WebPは可逆のみ／可逆が初期値 | 版依存 | v0.9.0からlossyを選択可、v0.12.0からWebP初期lossy QUALITY75。PNGが画像形式の初期値。旧保存値は別。 | [csmap_sheets/engine/xyz_tiles.py:24–32](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/xyz_tiles.py#L24-L32)、[csmap_sheets/CHANGELOG.md:29–33](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/CHANGELOG.md#L29-L33) |
| M12 | 中 | JSONは自分で拡張子を付ける／上書き確認なし | 版依存 | 0.12.3は.json補完後の最終名を確認。.JSONを保持。取消／Noで既存を維持。APIにはGUI確認がない。 | [csmap_sheets/profile_paths.py:4–9](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/profile_paths.py#L4-L9)、[csmap_sheets/profile_widget.py:33–68](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/profile_widget.py#L33-L68) |
| M13 | 中 | 索引は塗りつぶし／GPKGだけ移動すればスタイルも付く | 版依存 | 0.12.3は隣接sheet_index.qmlで塗りなし・枠線。同時に移動する。既存プロジェクトは必要に応じQML再読込。 | [csmap_sheets/engine/output_style.py:4–29](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/output_style.py#L4-L29)、[csmap_sheets/README_ja.md:342](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/README_ja.md#L342) |
| M14 | 高 | 設定JSON・TIFFがあれば全工程成功 | 誤り | 設定JSONは計算前保存、TIFFは後工程失敗でも残る。完了はrun.json.status=completedを確認。事前失敗ではrun.json自体がない場合もある。 | [csmap_sheets/algorithm.py:1434–1479](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L1434-L1479)、[csmap_sheets/engine/pipeline.py:1301–1324](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L1301-L1324) |
| M15 | 中 | 全図郭／全XYZ候補を必ず保存 | 誤り | alphaがすべて0の成果は省略。候補上限は省略前。結合TIFFはMERGED_GEOTIFF、XYZはXYZで生成可否を選ぶ。 | [csmap_sheets/engine/pipeline.py:947–1001](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L947-L1001)、[csmap_sheets/engine/xyz_tiles.py:317–347](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/xyz_tiles.py#L317-L347) |
| M16 | 中 | 出力CRS自動推定はラスタだけ／個別選択は100件まで | 版依存 | 現行は入力水平CRS・LASヘッダー・GSI地域メッシュにも対応。個別選択上限30。多数は入力フォルダーを使用。 | [csmap_sheets/CHANGELOG.md:47–60](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/CHANGELOG.md#L47-L60)、[csmap_sheets/algorithm.py:838–863](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L838-L863) |
| M17 | 中 | 標高色は図郭ごとに最小最大を伸張 | 誤り | 同一処理の全域DEMから共通範囲を取得。別実行も色を統一したい場合は同じ固定範囲・方式・配色を明示。 | [csmap_sheets/engine/pipeline.py:1222–1232](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L1222-L1232) |
| M18 | 中 | 終了時に結合TIFF／すべての図郭／XYZ接続を追加 | 誤り | LOADは全域VRTと索引を追加する。個別図郭、結合TIFF、XYZ接続は必要に応じ手動読込。 | [csmap_sheets/algorithm.py:1524–1555](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L1524-L1555) |
| M19 | 低 | QGIS『仮想ラスタを構築』はCS Map Sheets固有機能 | 誤り | QGIS標準Processing/GDALの前処理として表記。内部でBuildVRTを使うことと、標準UIの所属を区別。 | [csmap_sheets/engine/pipeline.py:1193–1198](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L1193-L1198)、[csmap_sheets/algorithm.py:160–168](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L160-L168) |
| M20 | 高 | FME方式HornならPSS/FME実成果と画素完全一致 | 要実機確認 | 同一DEM・範囲・格子・σ・欠測・FME版の参照成果で比較が必要。現行は一致保証なし。人工DEM一致を実成果の一致へ一般化しない。 | [csmap_sheets/algorithm.py:200–201](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L200-L201)、[docs/validation/project-audit-20261017.md:35–42](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/docs/validation/project-audit-20261017.md#L35-L42) |
| M21 | 中 | Windowsの保存確認／QML自動適用は実機合格済み | 要実機確認 | Linux既存試験とWindowsネイティブUIの証跡を区別。DPI、再導入、再読込を撮影手順で確認。 | [docs/validation/ui-fixes-0.12.3.md:1–45](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/docs/validation/ui-fixes-0.12.3.md#L1-L45) |
| M22 | 低 | Horn法を選択できる／σ=0で平滑化なし | 正しい | 現行ソースに一致する確認用命題。原本に同趣旨の記述があることを確認後に『正しい』を確定する。 | [csmap_sheets/engine/pipeline.py:131–165](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L131-L165)、[csmap_sheets/engine/pipeline.py:273–279](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L273-L279) |

## 同梱資料で実際に確認した不整合（v0.5原本とは別）

| ID | 資料・記述箇所 | 重大度／分類 | 実装との差・修正案 | 根拠 |
|---|---|---|---|---|
| D01 | INPUT_GUIDE「一括処理」: WebPを「可逆圧縮のみ」 | 中／版依存 | 古い説明。現行はlossy/lossless、初期lossy75。後段READMEの記述と統一し対象版を追記 | [csmap_sheets/INPUT_GUIDE_ja.md:7–13](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/INPUT_GUIDE_ja.md#L7-L13)、[csmap_sheets/engine/xyz_tiles.py:24–32](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/xyz_tiles.py#L24-L32) |
| D02 | INPUT_GUIDE v0.9.3解説・QGIS手順: CRS自動推定を「ラスター入力の場合のみ」と案内 | 中／版依存 | 旧版の履歴としては成立するが現行手順に残っている。v0.11.0の推定対象へ更新し、非GeoTIFF／LEMの入力水平CRS要件は維持 | [csmap_sheets/INPUT_GUIDE_ja.md:76–85](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/INPUT_GUIDE_ja.md#L76-L85)、[csmap_sheets/INPUT_GUIDE_ja.md:121–128](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/INPUT_GUIDE_ja.md#L121-L128)、[csmap_sheets/CHANGELOG.md:52–60](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/CHANGELOG.md#L52-L60) |
| D03 | shortHelpString: 「入力・出力・CRS・確認欄は…保存対象外」 | 中／誤り（範囲が曖昧） | input_crsは保存除外されない。実際に除外するキーを列挙し、「CRS」は出力CRSを指すと限定。inputs以外の入力変換条件も保存されるため「入力すべて」と誤読させない | [csmap_sheets/algorithm.py:199](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L199)、[csmap_sheets/algorithm.py:1454–1466](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L1454-L1466) |
| D04 | 入力形式UIラベル: 「標高ラスタ（GeoTIFF・IMG・ASC）」 | 低／説明の不足 | VRTも実装で許可。マニュアルの対応形式一覧にVRTを含める。UIラベル変更は本監査では実施しない | [csmap_sheets/algorithm.py:255](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L255)、[csmap_sheets/engine/input_sources.py:66–72](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/input_sources.py#L66-L72) |

本PRで同梱資料・UI・計算コードは修正しない。上記はレビュー可能な修正提案であり、マニュアルv0.5本文の差異と混ぜない。

## 版差と図版の扱い

0.12.2→0.12.3の変更対象はJSON保存UI・索引QML・セルサイズ案内。Hornの既定変更は0.10.0、σpxとWebP初期lossyは0.12.0。Libraryの過去画像は撮影版未確認として扱い、外観だけで0.12.3と認定しない。再撮影は[figure-capture-checklist.md](figure-capture-checklist.md)に従う。

PSS近似モードの未マージPR #31は対象mainに含めない。人工DEMの比較数値は試験条件と出典が確認できる場合のみ掲載し、「すべての地形で最適」「FME実出力と一致」へ言い換えない。[docs/validation/project-audit-20261017.md:10–13](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/docs/validation/project-audit-20261017.md#L10-L13)、[docs/validation/project-audit-20261017.md:35–42](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/docs/validation/project-audit-20261017.md#L35-L42)。

## 原本受領後の完了手順

1. マニュアルv0.5のファイル名・URL・取得日・SHA-256・対象プラグイン版・ページ数を記録する。
2. 全節・本文命題・図番号を列挙し、M番号または追加IDへ原文引用とページ／節を紐付ける。
3. [parameter-matrix.md](parameter-matrix.md)の92項目・入出力・既定値上書きと照合。未記載は「欠落」として明示し、正誤と区別する。
4. 四分類・重大度・修正文を確定し、正しい記述も含む集計と全記述の被覆を確認する。
5. Windows/QGIS確認結果と図の撮影版を追記。未確認の行は残してレビューし、レビュー前にマージしない。

## 今回の検証範囲

GitHubからソースを読み、main SHA・v0.12.2との差分・92パラメータ定義・上書き条件・出力分岐を静的照合した。参照リンクは固定SHAへ向ける。新しい計算・既定値・テストコードを追加していない。作業環境の起動待ちのためQGIS/PDAL/GDALの実行試験は行っておらず、既存検証結果を今回の実行結果として報告しない。
