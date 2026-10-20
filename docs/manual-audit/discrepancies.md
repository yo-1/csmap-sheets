# マニュアル整合性・差異台帳（Draft）

## 受領原稿と照合状態（2026-10-20更新）

このチャットで**本文34章を受領**した。監査資料IDは **R34-20261020**、識別名は「2026-10-20貼付34章稿」。冒頭は「一般利用者・森林GIS／測量技術者向け統合版｜編集稿 v0.3」、第III部は「v0.8追補」、第23章には「本書v0.7」があり、統一された版名は未確定。先に連絡されたv0.8ファイルとバイト単位で同一とは認定しない。貼付本文の章・節と引用を照合根拠に使い、Word/PDFのページ番号・原本ファイルのSHA-256は未取得のため付与しない。

**本文の再添付は今回の静的照合の前提ではなくなった。** v0.5原本は引き続き未取得。Library画像、Word/PDFの実体、比較データ、Windows/QGISの実機証跡は未取得・未確認。本文にある「画像を実際に確認した」は制作側の報告であり、この監査で画像を見たことを意味しない。

実装根拠はmain `12447d3f7cf8a04bb1e63d798ddc189f5976c889` (v0.12.3) に固定し、更新時にmainが同じSHAであることを再確認した。92項目の対応章と、原文に対する四分類・修正案を追加した。分類は主要実装命題の照合結果であり、34章の全文章・図版・研究結論を検証済みとするものではない。旧M01～M22は仮説台帳として残し、貼付本文での実在確認と判定は新しいR/T台帳に分ける。

計算コード・既定値は変更しない。PR #47はDraftを維持し、レビュー前にマージしない。

対象main: `12447d3f7cf8a04bb1e63d798ddc189f5976c889` (v0.12.3)、監査日2026-10-20 UTC。

**R34-20261020の本文を受領し、下記の原文引用・主要命題・章対応を追記した。** v0.5原本、画像・実機・比較データは未取得。旧M01～M22は想定命題の履歴であり、受領稿の誤り件数に数えない。同梱README／INPUT_GUIDEのD01～D04も受領稿とは別の資料として扱う。

## 分類と重大度

| 分類 | 判定規則 |
|---|---|
| 正しい | 原文の条件・対象版を含め現行実装と一致 |
| 版依存 | 旧版では成立するが現行で変更。旧版仕様として残すなら版を併記 |
| 誤り | 対象版・条件の下でソースと矛盾。説明を修正し計算コードは変えない |
| 要実機確認 | 静的ソースだけでは表示・ドライバ挙動・実DEM比較の結果を確定できない |

原本未取得は上の四分類とは別の**照合状態**であり、『要実機確認』へ押し込めない。高=計算条件／誤入力／誤成果判断に影響、中=手順・版・成果物運用に影響、低=用語・帰属・補足。

## R34貼付稿: 修正・追記が必要な箇所

原文のページは未確定のため実在章・節で指定する。**四分類の正誤と、未記載事項の追記・編集上の改善を区別する。** 「正しい」行の修正は矛盾訂正ではなく、再現性と操作の明確化のための追記。原画像を見ていない項目に「画像照合済み」を付けない。

| ID | 重大度 | 原稿の箇所 | 原文引用（短縮） | 四分類 | 修正区分 | 修正案・理由 | 根拠 |
|---|---|---|---|---|---|---|---|
| R01 | 高 | §4 手順10 | 「成果が妥当なら、設定JSONを保存し」 | 誤り | 手順修正 | 専用の処理後保存機能はない。SAVE_PROFILEはprepareAlgorithm内、DEM計算前に保存する。『実行前に保存先を指定して設定JSONを保存する。標高範囲自動検出の今回の実効範囲はrun.jsonで確認する』へ変更。検査後に数値を固定して再利用する場合は別途条件設定が必要。 | [csmap_sheets/algorithm.py:1434–1479](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L1434-L1479)、[csmap_sheets/algorithm.py:1504–1512](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L1504-L1512)、[csmap_sheets/engine/pipeline.py:1222–1232](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L1222-L1232) |
| R02 | 高 | §13.2 第2箇条 | 「ログの`CELL`、`SLOPE_ALGORITHM`、`RENDER_MODE`、`SIGMA`等の実効値」 | 誤り | 参照先修正 | Processing入力値は画面値で、プロファイル適用後の実効値とは限らない。『ログの入力パラメータと、適用・警告・傾斜法・平滑化サマリーを区別し、最終値はrun.json.settingsとrenderingで確認する』へ変更。SIGMA欄だけではpx方式の実効値を表せない。 | [csmap_sheets/algorithm.py:1301–1352](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L1301-L1352)、[csmap_sheets/algorithm.py:1390–1446](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L1390-L1446)、[csmap_sheets/engine/pipeline.py:1059–1110](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L1059-L1110) |
| R03 | 高 | §5・§25・§30 | 「最初は実装の既定値を変更せず、実効値を記録」 | 正しい | 不足条件の追記 | 方針は妥当だが『画面初期値と実効値の違い』表を追加する。RENDER_MODE初期は独自方式、FME起点は本書の暫定案。独自標準は曲率±0.05・標高0～3000m・自動検出OFF、画面欄は±0.1・200～2000m。PROFILE=標準CS1m/試験2mはFME・σ=m3m・曲率±0.1・標高200～2000m・自動OFF。PROFILE=暫定は±0.03。XYZ初期ON、形式初期PNG、MERGED_GEOTIFF初期ON。 | [csmap_sheets/algorithm.py:589–658](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L589-L658)、[csmap_sheets/algorithm.py:1301–1352](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L1301-L1352)、[csmap_sheets/algorithm.py:727–738](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L727-L738)、[csmap_sheets/algorithm.py:790–800](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L790-L800) |
| R04 | 中 | §7 成果表・§8・§32 | 「run.json、設定JSON」「完了状態、実効設定、使用版、入力一覧」 | 正しい | 記録の役割を分記 | 2資料を合わせた説明として成立するが、両方が同じ情報を持つと誤読させない。run.jsonはstatus・settings・sources・rendering・版・バックエンド等。設定JSONはschema/settingsで、inputs/output_dir/target_crs/plane_zone/input_type/confirm_elevation_metresを除外。input_crs等の入力変換条件は保存される。標高自動検出はJSON保存後に実施する。 | [csmap_sheets/algorithm.py:1454–1472](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L1454-L1472)、[csmap_sheets/engine/pipeline.py:1162–1182](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L1162-L1182)、[csmap_sheets/engine/pipeline.py:1222–1232](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L1222-L1232) |
| R05 | 中 | §7・§25・§26 | 「図郭GeoTIFF」「cs_relief_merged.tif」「候補枚数上限は既定10万枚」 | 正しい | 作成条件の追記 | 図郭はalpha非ゼロのものだけ、全透明は省略。結合TIFFはMERGED_GEOTIFF=True、XYZはXYZ=True時。候補10万は透明除外前。出力は親フォルダー直下ではなくcsmap_日時_識別子。run.jsonは事前検査失敗時に存在しない場合もある。 | [csmap_sheets/algorithm.py:1169–1178](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L1169-L1178)、[csmap_sheets/engine/pipeline.py:947–1001](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L947-L1001)、[csmap_sheets/engine/pipeline.py:1267–1324](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L1267-L1324)、[csmap_sheets/engine/xyz_tiles.py:248–260](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/xyz_tiles.py#L248-L260) |
| R06 | 高 | §26 完了状態・§32 処理完了 | 「ログ・run.jsonに重大エラーがなく、必要な図郭が出力されている」 | 正しい | 合格条件を厳密化 | ログに重大エラーが見えないだけでは十分でない。『run.json.statusがcompletedで、必要な出力の存在・件数を確認できる』を必須条件にする。failed/cancelled/running/欠落は完成扱いしない。§8の『失敗・スキップ件数』は、常に存在する単一失敗件数キーがあると解釈せず、status/errorと図郭・XYZの省略件数を区別する。 | [csmap_sheets/engine/pipeline.py:1052–1055](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L1052-L1055)、[csmap_sheets/engine/pipeline.py:1307–1324](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L1307-L1324)、[csmap_sheets/engine/xyz_tiles.py:345–374](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/xyz_tiles.py#L345-L374) |
| R07 | 中 | §13.1 第1箇条 | 「実際にどちらが用いられるかは『描画方式』の選択による」 | 正しい | 適用条件の追記 | 描画方式に加え、独自方式の個別色・調整係数はLEGACY_PRESET=カスタム時に画面値を使用する。FMEの個別ストレッチ範囲はcustom時に使用。外部JSON/組込みプロファイルによる上書きも区別する。 | [csmap_sheets/algorithm.py:1107–1138](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L1107-L1138)、[csmap_sheets/algorithm.py:1148–1168](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L1148-L1168)、[csmap_sheets/algorithm.py:1301–1433](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L1301-L1433) |
| R08 | 中 | §25 記録先・§9.2 | 「run.json の smoothing」「run.json の elevation_m」 | 正しい | キー階層の明示 | 略記を完全パスへ。平滑化はrendering.terrain_calculation.smoothing、標高範囲はrendering.normalization.elevation_m。sigma_unit、sigma_setting、effective_sigma_m、effective_sigma_pxを併記。σ=0は平滑化なし、方式未指定の旧JSONはm。 | [csmap_sheets/engine/pipeline.py:194–210](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L194-L210)、[csmap_sheets/engine/pipeline.py:1059–1110](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L1059-L1110)、[csmap_sheets/algorithm.py:1397–1410](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L1397-L1410) |
| R09 | 中 | §12 第1項・§28.1・§34 | 「QGIS v0.12.2の全パラメータ画面と既定値」 | 版依存 | 対象版の統一 | v0.12.2はプラグイン版でありQGIS版ではない。『プラグインv0.12.3／QGIS 3.44系の初期状態で全項目を確認し、v0.12.2旧版画像は差分資料として保持』とする。§13の画面値は試験値と明記している点を維持。 | [csmap_sheets/algorithm.py:169–185](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L169-L185)、[csmap_sheets/CHANGELOG.md:10–21](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/CHANGELOG.md#L10-L21) |
| R10 | 中 | §4手順9・§7・§30 | 「出力GeoTIFFをQGISで再読み込み」 | 正しい | 自動読込対象の追記 | 手動再読込は妥当。初期LOAD=Trueで自動追加されるのは全域CS画像cs_relief.vrtと図郭索引だけと追記。結合TIFF・全図郭・XYZ接続の自動追加とは説明しない。 | [csmap_sheets/algorithm.py:1523–1555](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L1523-L1555) |
| R11 | 中 | §3・§24・§26 | 「NoData、元セルサイズ」「-9999/-1111混入を確認」 | 正しい | 入力制限の追記 | ラスタはローカル単バンド、CRS・NoDataまたは明示上書きが必要。格子整合OFF時はCRS/解像度/格子を共通化。森林TIFFの追加欠測-9999/-1111処理と、汎用ラスタでの明示定義を区別。点群は外部PDAL>=2.9、Withheld/7/18除外、補間半径外NoDataなどを技術付録へ。 | [csmap_sheets/algorithm.py:941–958](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L941-L958)、[csmap_sheets/engine/pipeline.py:707–761](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L707-L761)、[csmap_sheets/engine/input_sources.py:627–703](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/input_sources.py#L627-L703)、[csmap_sheets/engine/point_inputs.py:270–280](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/point_inputs.py#L270-L280)、[csmap_sheets/engine/point_inputs.py:369–380](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/point_inputs.py#L369-L380) |
| R12 | 中 | §13～§18・§21・§31 | 「スクリーンショットを実際に確認して作成した」 | 要実機確認 | 証跡状態を分離 | 制作側による閲覧報告として保持。この監査は元PNGを受領・閲覧しておらず、表示内容・版・数値・画像名の一致を追認しない。画像バイト取得、v0.12.3撮影、条件突合の結果は図版台帳で個別管理。差分図のシアン円や単位も原図確認まで保留。 | [docs/validation/ui-fixes-0.12.3.md:1–45](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/docs/validation/ui-fixes-0.12.3.md#L1-L45)。原図の根拠は未取得でありソースだけでは確定不可 |
| R13 | 中 | 冒頭・§23・§29・§34 | 「編集稿 v0.3」「本書v0.7」「v0.8追補」「未完了：ソースコードからの全UIパラメータ抽出」 | 正しい | 文書管理情報の更新 | 監査前の編集履歴として保持できるが公開版では表紙版名・対象ソースSHA・監査状態を統一。『PR #47で92項目の静的抽出と本貼付稿の主要命題照合を実施、Windows画面・画像・v0.5比較は未了』へ更新。v0.9への反映時は元稿R34と区別。 | 本チャット受領本文の冒頭・§23・§29・§34、およびPR #47。実装正誤ではなく編集履歴の更新 |
| R14 | 中 | §33 試験B/C | 「B：解像度」「固定：入力範囲、方式、傾斜法、色」「C：平滑化」 | 正しい | 比較条件の追記 | 試験案であり検証済み結果ではない。解像度比較Bでは入力DEM同一・実効σ(m)・曲率範囲・標高範囲・欠測をどう固定するか明示。σpx固定で格子を変えると実効σmも変わる。Cは傾斜法も固定条件に追記。 | [csmap_sheets/engine/pipeline.py:171–210](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L171-L210)。試験の判読性結果は未取得 |

### 手順へそのまま反映できる修正文

**§4 手順7～10の差替え案**

7. 標高単位・鉛直基準の統一を確認し、出力親フォルダーを指定します。条件を保存する場合は、実行前に詳細パラメータ「現在の処理設定をJSONへ保存」の保存先も指定します。
8. 初回はXYZを無効にして実行します。設定JSONは設定検証後・DEM計算前に保存されます。ファイルがあっても処理成功の証拠にはなりません。
9. run.jsonのstatusがcompletedであることと、必要な図郭・成果を確認します。GeoTIFFをQGISで再読込し、位置・透明部・継ぎ目を検査します。
10. 次回は外部JSONプロファイルとして設定を再利用できます。標高範囲自動検出で今回使った範囲はrun.jsonのrendering.normalization.elevation_mを確認してください。同じ色基準を固定する場合は、その範囲を指定し、自動検出を無効にして保存・再実行する条件を明示します。組込みプロファイルによる上書きにも注意します。

**§13.2 第2箇条の差替え案**

ログ冒頭のProcessing入力値と、プロファイル適用後の実効設定は区別します。ログの適用・警告・傾斜法・平滑化サマリーを確認し、最終値はrun.jsonのsettingsとrenderingで照合します。曲率平滑化はrendering.terrain_calculation.smoothingの指定方式・指定値・実効m/pxを記録します。

## R34貼付稿: 旧M命題との対応・四分類

この表は受領本文を引用した判定であり、旧M表の否定的な想定文を原稿に存在するとみなさない。版依存は現行記述が誤りという意味ではない。T20/T21は未検証とする文章は妥当だが、主題である比較・実機結果が未判定なので要実機確認とする。

| ID/旧命題 | 原稿の箇所 | 原文引用 | 判定 | 結論・適用範囲 | 根拠 |
|---|---|---|---|---|---|
| T01/M01 | §5・§9.1・§20 | 「Horn法」「実装既定値（v0.10以降）」 | 版依存 | 現行と一致。v0.9.4以前は中央差分。旧M01の誤記想定は本文にはない。 | [csmap_sheets/algorithm.py:579–588](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L579-L588)、[csmap_sheets/CHANGELOG.md:72–85](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/CHANGELOG.md#L72-L85) |
| T02/M02 | §9.3 | 「独自方式v0.4互換とFMEマニュアル方式では色の合成が異なります」 | 正しい | 独自混色と5層加重和を区別している。 | [csmap_sheets/engine/pipeline.py:295–338](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L295-L338) |
| T03/M03 | §33 | 「一般納品の唯一の最適設定と断定しません」 | 正しい | 暫定案と検証済み推奨を区別。最適性の実証結果を本監査が確認したわけではない。 | [csmap_sheets/algorithm.py:1334–1352](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L1334-L1352)、[docs/validation/project-audit-20261017.md:35–42](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/docs/validation/project-audit-20261017.md#L35-L42) |
| T04/M04 | §9.2・§25 | 「σ(px) = σ(m) / セルサイズ(m)」「0.5m格子の3px=1.5m」 | 正しい | 出力計算格子について成立。旧JSON・σ=0は追記候補R08。 | [csmap_sheets/engine/pipeline.py:168–210](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L168-L210) |
| T05/M05 | §3・§24 | 「GeoTIFFの元セルサイズは自動取得。テキスト格子間隔欄は使用しない」 | 正しい | 0.12.3はこの案内をUIにも追加。 | [csmap_sheets/algorithm.py:183–185](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L183-L185)、[csmap_sheets/algorithm.py:428–435](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L428-L435) |
| T06/M06 | §5・§9.4 | 「0mを欠測と決めつけず」「正常な0mをNoDataに置き換えない」 | 正しい | 欠測は明示定義、有限値、safe maskで扱う。 | [csmap_sheets/engine/pipeline.py:270–294](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L270-L294)、[csmap_sheets/engine/pipeline.py:334–338](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L334-L338) |
| T07/M07 | §3・§17 | 「.tif .tiff .img .asc .vrt」 | 正しい | 標高ラスタ区分はVRTを許可。§17の追加確認指示は妥当。 | [csmap_sheets/engine/input_sources.py:66–72](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/input_sources.py#L66-L72) |
| T08/M08 | §3・§24 | 「国土地理院DEM」「配布ZIP、数値標高XML」 | 正しい | GSI DEMを対象としており任意ZIP/XML対応とは書いていない。内部仕様の制限は付録へ。 | [csmap_sheets/engine/gsi_dem.py:62–110](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/gsi_dem.py#L62-L110) |
| T09/M09 | §3・§24 | 「.lem＋同名.csv/.txt」「対応メタデータ欠落は停止」 | 正しい | 同じフォルダー・stemでCSV/TXTを対応付け。CSV優先は未記載。 | [csmap_sheets/engine/forest_dem.py:353–399](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/forest_dem.py#L353-L399) |
| T10/M10 | §2 | 「通常の標高ラスタ・国土地理院DEM・規則格子テキストの処理には外部PDALは原則不要」 | 正しい | LAS/LAZ・不規則点にPDAL。>=2.9は追記候補R11。 | [csmap_sheets/engine/input_sources.py:968–975](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/input_sources.py#L968-L975)、[csmap_sheets/engine/point_inputs.py:369–380](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/point_inputs.py#L369-L380) |
| T11/M11 | §5・§20・§25 | 「現行既定は非可逆 QUALITY 75」 | 版依存 | WebPを選んだ場合の既定。画像形式の初期値はPNG。旧保存プロファイルは保存値を使う。 | [csmap_sheets/engine/xyz_tiles.py:24–32](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/xyz_tiles.py#L24-L32)、[csmap_sheets/CHANGELOG.md:29–33](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/CHANGELOG.md#L29-L33) |
| T12/M12 | §20 | 「v0.12.3で拡張子自動付与・重複回避・最終パス上書き確認」 | 版依存 | 実装と一致。Windowsネイティブ表示は未確認。 | [csmap_sheets/profile_paths.py:4–9](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/profile_paths.py#L4-L9)、[csmap_sheets/profile_widget.py:33–68](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/profile_widget.py#L33-L68) |
| T13/M13 | §7・§20 | 「sheet_index.qml（v0.12.3）」「GPKGと同じフォルダーで保管」 | 版依存 | 隣接QML作成と一致。実機の自動適用は画像／実機証跡待ち。 | [csmap_sheets/engine/output_style.py:4–29](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/output_style.py#L4-L29)、[csmap_sheets/engine/pipeline.py:1034–1037](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L1034-L1037) |
| T14/M14 | §4手順8・§7・§26 | 「run.jsonの状態とログを確認」「完了状態、実効設定、使用版、入力一覧」 | 正しい | run.json確認は妥当。ただし設定JSONと役割を分記しcompletedを明記する（R04/R06）。 | [csmap_sheets/engine/pipeline.py:1162–1182](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L1162-L1182)、[csmap_sheets/engine/pipeline.py:1307–1324](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L1307-L1324) |
| T15/M15 | §7・§25 | 「図郭GeoTIFF」「候補枚数上限は既定10万枚」 | 正しい | 保存対象・候補数の区別が欠落。『全候補を必ず保存』という旧M15の想定誤文は存在しない。R05として追記。 | [csmap_sheets/engine/pipeline.py:947–1001](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L947-L1001)、[csmap_sheets/engine/xyz_tiles.py:248–260](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/xyz_tiles.py#L248-L260) |
| T16/M16 | §3・§20 | 「個別ファイル指定は現行資料で30件上限」「非ラスタ入力も…推定可能」 | 版依存 | 現行と一致。v0.11.0以降の説明として保持。 | [csmap_sheets/algorithm.py:838–863](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L838-L863)、[csmap_sheets/CHANGELOG.md:47–60](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/CHANGELOG.md#L47-L60) |
| T17/M17 | §5・§25・§26 | 「同一案件で一貫した範囲」「固定範囲を再利用」 | 正しい | 1回の全域で共通範囲を使う仕様に整合。別実行の統一には実効範囲の固定が必要。 | [csmap_sheets/engine/pipeline.py:1222–1232](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L1222-L1232) |
| T18/M18 | §4手順9 | 「出力GeoTIFFをQGISで再読み込み」 | 正しい | 手動確認として妥当。自動LOAD対象の記載はない（R10）。『すべてを自動追加』という想定誤文は存在しない。 | [csmap_sheets/algorithm.py:1544–1555](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L1544-L1555) |
| T19/M19 | §17 | 「QGIS標準機能」「CS Map SheetsにVRT作成機能があると説明するものではない」 | 正しい | 標準UIとプラグイン内部BuildVRTを区別している。 | [csmap_sheets/algorithm.py:160–168](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L160-L168)、[csmap_sheets/engine/pipeline.py:1193–1198](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L1193-L1198) |
| T20/M20 | §6.1・§11・§33 | 「FME実成果との画素完全一致は未検証」「原資料と試験条件を突合してから」 | 要実機確認 | 一致未検証という慎重な表現は実装の保証範囲と整合。実成果の一致・方式の優劣自体は未判定。 | [csmap_sheets/algorithm.py:200–201](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L200-L201)、[docs/validation/project-audit-20261017.md:35–42](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/docs/validation/project-audit-20261017.md#L35-L42) |
| T21/M21 | 冒頭・§12・§34 | 「Windows/QGIS実機での画面ラベル照合…未了」 | 要実機確認 | 受入未了として扱う点に整合。§13以降の旧画像内容は制作側の報告であり原図未確認。 | [docs/validation/ui-fixes-0.12.3.md:1–45](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/docs/validation/ui-fixes-0.12.3.md#L1-L45) |
| T22/M22 | §9.1・§25 | 「中央差分法を選択可能」 | 正しい | 傾斜選択肢と一致。旧M22のσ=0命題は貼付稿では説明未記載であり、記載済み扱いしない。 | [csmap_sheets/algorithm.py:579–588](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/algorithm.py#L579-L588)、[csmap_sheets/engine/pipeline.py:273–279](https://github.com/yo-1/csmap-sheets/blob/12447d3f7cf8a04bb1e63d798ddc189f5976c889/csmap_sheets/engine/pipeline.py#L273-L279) |

## 34章の被覆と残件

各章に実装照合対象があるかを確認した台帳。章全体の保証ではなく、主要実装命題の対応を示す。編集方針や将来の比較計画を、ソース検証済みの研究結果へ昇格させない。

| 章 | 見出し／話題 | 照合結果・残件 | 対応ID |
|---|---|---|---|
| 1 | このマニュアルの使い方 | 用途説明は整合。地形の自動認定・最適性保証は対象外。 | T02/T03 |
| 2 | 導入前の確認 | QGIS3.44・QGIS4非保証、PDALの区別は整合。バージョン下限を補足。 | T10/R11 |
| 3 | 入力データを選ぶ | 形式、VRT、LEM、軸順、30件は整合。専用入力制限を補足。 | T05～T10/T16/R11 |
| 4 | 初心者向けクイックスタート | 実行後の設定JSON保存手順を修正。実行前の確認・再読込は妥当。 | R01/R03/R10 |
| 5 | 標準設定の選び方 | 暫定案・実装既定値の区別は妥当。画面値と実効値の表を追加。 | T01/T03/T11/R03 |
| 6 | 判読目的別の設定と評価 | 最適値未確定とする編集方針は妥当。FME/MIERUNEの評価結果は未検証。 | T03/T20 |
| 7 | 出力成果と納品確認 | 成果名・QML・XYZ仕様は整合。条件と記録の役割を追記。 | T13/T14/R04/R05 |
| 8 | 品質管理と再現性 | 記録方針は妥当。status/errorとスキップの読み方を具体化。 | R04/R06/R08 |
| 9 | 地形量とパラメータ | 傾斜・負ラプラシアン・σ換算・方式差は整合。実効値・欠測付録を補足。 | T01/T02/T04/T06/R08/R11 |
| 10 | トラブルシューティング | 対処方向は整合。実際のエラー画面・原因特定は未実機確認。 | T09/T10/T11/T13/R11 |
| 11 | 比較研究の反映ルール | 人工DEMと実地形を分ける方針は妥当。長野報告の内容は未取得。 | T03/T20 |
| 12 | 次の編集・実機確認 | QGIS版とプラグイン版の表記を分離。撮影基準を0.12.3へ統一。 | R09 |
| 13 | 画面に対応した設定解説 | 原画像は未確認。ログ入力値と実効値の区別を修正し、配色適用条件を補足。 | R02/R07/R12 |
| 14 | 図版選定台帳 | 画像内容と埋込制限は制作側報告。14.1の連番11～15は公開稿で整理。 | R12/R13 |
| 15 | 画像の種類と誤掲載防止 | 標準機能との区別は整合。原画像で各キャプション確認が必要。 | T19/R12 |
| 16 | 入力DEMの事前点検 | 例示数値を一般化しない方針は妥当。EPSG等は原画像未確認。 | R11/R12 |
| 17 | 複数DEMをVRTにまとめる | QGIS標準機能・参照の説明は整合。任意の前処理で必須ではない。 | T07/T19 |
| 18 | 画像掲載・版照合の実務ルール | 版別区分は妥当。A認定は元画像と現行実機証跡が必要。 | R09/R12 |
| 19 | 担当分担と完了条件 | 編集・監査の分担は妥当。監査の現状をPR47へ更新。 | R13 |
| 20 | 現行版と過去資料の差異 | Horn/σ/WebP/CRS/JSON/QMLの版差は整合。実装と固定SHAを最終根拠に。 | T01/T11～T13/T16/R13 |
| 21 | 設定画面の画像追加調査 | 標準画面との区別は妥当。個別PNGの内容は未追認。 | T19/R12 |
| 22 | 画像入り完成版の優先順位 | 旧版注記と埋込未完了を明示する方針は妥当。 | R09/R12 |
| 23 | 役割分担と確認状況 | Issue作成と実行開始を区別。v0.7表記と監査未着手情報を更新。 | R13 |
| 24 | 入力形式別の実務手順 | 形式別操作の主要記述は整合。詳細の制限と初期値は付録参照。 | T05～T10/T16/R11 |
| 25 | 設定項目の読み方 | 主要値は整合。実効値の上書き、JSONキーの階層を明記。 | R03/R04/R08 |
| 26 | 出力成果の受入検査 | 検査方向は妥当。completed、任意出力、全透明省略を明記。 | R05/R06/R11 |
| 27 | 比較評価票と採用決定 | 試験設計であり比較結果ではない。27.1表が27.2後にある編集順を整理。 | T03/T20/R14 |
| 28 | 既存資料の版差・図版台帳 | 0.12.3撮影計画は妥当。連番16～21、metadata優先の表現を整理。 | R09/R12/R13 |
| 29 | 確定事項と次回条件 | 記述済み/資料照合/実機確認を分離。92項目監査の状態を更新。 | R13 |
| 30 | 初回処理の確認順序 | 操作順の主要要素は整合。実効値・保存のタイミングを補足。 | R01/R02/R03 |
| 31 | スクリーンショット採用台帳 | 標準機能とプラグイン画面を区別。元PNG・試験条件は未確認。 | T19/R12 |
| 32 | 納品前検査の記録例 | 重大エラーなしだけで完成としない。completedと必要成果を明記。 | R04/R06 |
| 33 | 地形別推奨の最小比較設計 | 唯一の最適設定を断定しない点は妥当。解像度/σの交絡を明示。 | T03/T20/R14 |
| 34 | 未完了事項 | 撮影・画像・比較は継続保留。ソース抽出と本稿照合の現状を更新。 | R12/R13 |

## 旧M01～M22: 原本受領前の想定命題（履歴）

この旧表自体は仮説の履歴として維持する。R34での実在確認と判定は下記T台帳へ移し、v0.5は未照合。分類欄は「当該命題が原本にあった場合」の判定案。M20/M21の断定部分は削り、確認が必要な比較・UI結果を実機試験へ送る。

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

## 残る完了条件

1. 表紙の版名を統一し、v0.8原本ファイルと貼付R34の同一性を確認する。Word/PDFは受領後にページ・表・図番号、文字欠け・画像埋込を検査する。
2. R01/R02の矛盾を修正し、R03～R14の追記・版整理・実機条件を制作側で反映する。R34の章参照は付与済みで、v0.5は全件未照合。
3. Library原PNGと比較データを受領し、Windows/QGISの撮影・受入手順を実施する。T20/T21/R12を証跡に基づき更新する。
4. v0.5原本を取得した場合は本文改訂差分を別台帳に記録する。後続v0.9を受領したらR34との修正差分を追跡し、未受領の版を照合済みとしない。
5. レビュー前にPR #47をマージしない。

## 今回の検証範囲

固定mainのソースを再取得し、貼付本文の主要実装命題、22件の旧想定との対応、34章の章別被覆、92項目の記載範囲を静的照合した。本文で矛盾を確認したのはR01（保存時点）とR02（入力値と実効値の同一視）。その他のR行は不足の追記・編集改善・要証跡確認であり、すべてを誤り件数に加算しない。同梱資料D01～D04と旧想定M01～M22も別集計。

既存監査表のNODATA初期値誤抽出は「未指定（空欄）」へ訂正した。これは文書の訂正でありプラグインの変更ではない。QGIS/Windows/PDAL/GDALの新規実行・撮影、Library原図確認、実DEMとFME/MIERUNE比較は今回実施していない。
