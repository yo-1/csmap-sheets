# Linux 代替セッション結果（2026-11-03、項目 A〜H）

実機セッション実施票（2026-10-31、Drive「CS_Map-Sheets_AI連絡」）の項目 A〜H を、利用者の判断（2026-11-03）により Muse が Linux で代替実施した記録。環境は QGIS 3.44.14（conda env、QT_QPA_PLATFORM=offscreen）。**Windows 実機そのものの確認ではない。** 数値系の項目は、2026-10-28 に Linux と Windows で全件結果が一致した前例（PR #68 証跡照合）を根拠に代替を認めた。表示系はダイアログ描画と例外文面で確認した。

## 結果

| 項目 | 結果 | 実施内容と証跡 |
|---|---|---|
| A 配布ZIP導入・版表示（W1） | 確認（GUI画面を除く） | 配布ZIP（272,685 bytes、SHA-256 6d9c7501…）を再取得しハッシュ一致を確認。展開して QGIS Python で provider 登録とアルゴリズム `csmapsheets:create` の生成を確認。metadata.txt の version=0.13.1、engine VERSION=0.13.1。プラグインマネージャの GUI 画面そのものは未実施 |
| B 設定画面の撮影 | 確認 | main（2324f21、PR #79 反映）の処理ダイアログを描画・撮影（Drive に PNG 4点）。区分名の形式併記（例【点群（LAS・LAZ）】）と DEMS ラベルの「標高ラスタ形式のみ」注記、ヘルプ欄の形式×区分対応表を確認 |
| C プロファイル警告（PR #57） | 確認 | max_pixels を既定の2倍（2,000,000,000）にした外部JSONプロファイルで実走（完走）。上限警告「この設定プロファイルは処理上限 max_pixels を既定値（1,000,000,000）より大きい 2,000,000,000 に設定しています。メモリ使用量・処理時間が大きくなる可能性があります。」が feedback.pushWarning と profile_warnings の双方に出た |
| D 旧JSON の mode 固定＋警告（W2） | 確認 | nodata_edge_mode キーのないプロファイル → safe_mask に固定され、実走の run.json の settings でも safe_mask を確認。画面の選択が pss_approximation のとき警告文「この設定プロファイルには欠測・端部の処理方式（nodata_edge_mode）がないため、標準（safe_mask）として読みます。画面の境界補完の選択は適用しません。」が出て、safe_mask のときは出ない（設計どおり） |
| E PSS の JSON 往復（W2） | 確認 | nodata_edge_mode=pss_approximation のプロファイルを settings_profile → JSON → merge_settings_profile で往復。58キーすべて差分ゼロ、値も保持 |
| F 実DEM nodata 中心の透明化（W2） | 確認（合成DEM） | 検証用サンプル（内部欠測穴つき dem_full.tif、tools/make_validation_samples.py）で実走し run.json を記録。座標換算のうえ、欠測穴の中心画素（シート 09MC4785 の (10,180)）の alpha=0（透明）、丘の中心画素の alpha=255（不透明）を確認 |
| G DPI・表示幅（W1） | 等価確認のみ | QT_SCALE_FACTOR=1.5 でダイアログを再描画し、レイアウトの崩れがないことを撮影で確認。Windows 実モニターの DPI そのものは未実施 |
| H Issue #71 の案内表示 | 確認 | 再現条件（入力形式=森林航空レーザ、DEMS 指定、FILES/INPUT_FOLDER 空）で prepareAlgorithm が案内文の例外を送出：「標高ラスタ（DEM）が指定されていますが、現在の入力形式「森林航空レーザ成果（LEM・CSV格子・TIFF・GeoTIFF・ZIP）」では使用されません。入力形式を「標高ラスタ（GeoTIFF・IMG・ASC）」に変更するか、選択した入力形式に対応するファイルまたはフォルダーを指定してください。」ダイアログのエラー表示と同一文面 |

## 残る未実施（次版の受入へ）

- Windows 実機のプラグインマネージャ画面での導入・版表示
- Windows 実モニターでの DPI・表示幅
- Windows のネイティブ保存ダイアログ

画面 PNG と各 run.json は Drive「CS_Map-Sheets_AI連絡」の実施報告（muse-to-ai_20261103_CSMapSheets_Linux代替セッション結果.md）に添付した。実施票は本記録をもって取り下げた（muse-to-codex_20261103_CSMapSheets_実機セッション実施票_取り下げ.md）。
