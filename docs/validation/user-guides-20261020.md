# 利用手順書・ヘルプ導線の検証（2026-10-20）

## 基準・範囲

- 基準main: `12447d3f7cf8a04bb1e63d798ddc189f5976c889`（PR #44後）。
- 最新main追従: `92b8c28f342dee698a87d917632558caac30915e`（PR #49/#50後）。0.12.4のMERGED_DEM・既定オフと関連試験、公開情報を保持して競合解消。
- 作業ブランチ: `docs/user-guides-help`、版は最新mainと同じ0.12.4。
- 既存QGIS公式版0.12.2・GitHub Release v0.12.4、Release・タグ・QGIS登録は変更しない。mainへマージしない。
- engine、パラメータ定義・既定値、prepareAlgorithm/processAlgorithmは変更しない。
- 既存Processingヘルプを残し、先頭に利用手順書・推奨設定リンク、標準ヘルプボタンに利用手順書URLを設定。ツールバー・ツールボックス起動に共通。
- metadataのhomepage/repository/trackerはGitHubの既存URLを維持。独立ドキュメント項目は元からないため、aboutで案内しProcessingのhelpUrlを利用。非標準キーは追加しない。

## 文書の重複整理

基本操作・設定選定・計算根拠を3書へ整理。既存READMEのRGB表・XYZ、入力ガイドの形式仕様、VALIDATIONの履歴、SOURCESの出典は参照元として残す。古い版表示・公式未申請・全QGIS試験未実施の記述は現行記録への案内へ更新。

実装既定・暫定推奨・比較検証済みの範囲を分離。±0.03と長野ストレッチを全国共通の確定値にしない。未マージPSS近似は対象外。

リポジトリに配布マニュアルPDFはなく、新規PDFは作らない。Markdown正本とし、外部参考PDFと区別する。

## 検査

- `python tools/check_markdown_links.py`: Markdownの相対パス・main向け自リポジトリURL・見出しを作業ツリーで解決。外部全URLの稼働検査ではない。
- tools/tests: 欠落文書・見出しで不合格になるリンク検査と既存パッケージ検査の異常系。
- 既存preflight/unit/gdalに加えUbuntuのQGIS 3.44 LTR環境で既存回帰を実行。スキップを成功に含めない。
- tools/check_qgis_package.py: 実ZIPのimport、classFactory、GUI/Processing登録、実ダイアログ、JSON保存欄、解除。両アンカーと標準ヘルプを実クリックし、QDesktopServicesのHTTPSハンドラでURLを捕捉する（外部ブラウザは起動しない）。
- 同じZIPの画面を幅1400・1000でPNG保存し、Actions artifact `csmap-sheets-help-screenshots` へ添付。
- オンライン正本はマージ後のmainを指す。レビュー中はREADMEの相対リンクを使う。新文書がまだmainにないことと公開版反映を混同しない。

## 実行結果

作業環境はexecutor構成取得エラーで2回起動失敗。ローカル成功は主張しない。
[Actions 39459353128](https://github.com/yo-1/csmap-sheets/actions/runs/39459353128)、対象head `72b1d06d461b0e1329f96a1d878f1ef9a36d651d`（PRマージ検査ref）で全4ジョブ成功。

| 検査 | 結果 |
|---|---|
| unit（Python 3.12.15、GDAL/QGISなし） | 190件中167成功・23スキップ・失敗0 |
| gdal（GDAL 3.8.4、NumPy 1.26.4、SciPy 1.11.4） | 190件中180成功・10スキップ・失敗0 |
| qgis（QGIS 3.44.15、GDAL 3.8.4） | 190件中188成功・2スキップ・失敗0 |
| tools/tests | 4成功・スキップ0・失敗0 |
| Markdown | 14ファイル・64リポジトリリンク成功 |
| preflight | Flake8・Bandit・detect-secrets・ZIP構造／構文／CRC／metadata成功 |
| 実ZIPの起動 | import、classFactory、GUI/Processing登録、実ダイアログ、JSON保存欄、unload成功 |
| ヘルプ操作 | 利用手順書・推奨設定・標準Helpを実クリックし3遷移先URL一致 |
| スクリーンショット | dialog-wide.png（幅1400）、dialog-narrow.png（幅1000）を同じZIPから生成 |

QGISの2スキップはPDAL未導入の点群実行、WEBPドライバ存在環境でのドライバ欠如専用経路。成功数には含めない。画面はLinux offscreen描画で、Windows・実モニターのDPI・ネイティブブラウザの検査ではない。

[スクリーンショットZIP](https://github.com/yo-1/csmap-sheets/actions/runs/39459353128/artifacts/12281469541)をPRにも添付。自動保存・リンク実クリックを確認し、目視比較済みとは扱わない。
[検査済みパッケージ](https://github.com/yo-1/csmap-sheets/actions/runs/39459353128/artifacts/12282315879)は31ファイル、metadata 0.12.4、内部ZIP SHA-256 `165eeaea3777fed1c00f688ff62771b9caf11bc9243f0ce0471fde2e3ca7f600`。既存Release資産の差替えには使っていない。

初回[39459050904](https://github.com/yo-1/csmap-sheets/actions/runs/39459050904)は存在しないDockerタグの取得でQGIS起動前に失敗。QGIS公式Ubuntu LTRパッケージへ修正後、3.44系を明示検査して全ジョブ成功。

## 未確認

Windowsのネイティブブラウザ・保存ダイアログ・DPI、QGIS 4/Qt6、実DEMの最適性・FME/PSS実出力一致は本自動検査の対象外。[監査記録](project-audit-20261017.md)と[UI受入手順](ui-fixes-0.12.3.md)で追跡する。
