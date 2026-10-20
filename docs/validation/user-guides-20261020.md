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
- 既存preflight/unit/gdalに加えQGIS 3.44コンテナで既存回帰を実行。スキップを成功に含めない。
- tools/check_qgis_package.py: 実ZIPのimport、classFactory、GUI/Processing登録、実ダイアログ、JSON保存欄、解除。両アンカーと標準ヘルプを実クリックし、QDesktopServicesのHTTPSハンドラでURLを捕捉する（外部ブラウザは起動しない）。
- 同じZIPの画面を幅1400・1000でPNG保存し、Actions artifact `csmap-sheets-help-screenshots` へ添付。
- オンライン正本はマージ後のmainを指す。レビュー中はREADMEの相対リンクを使う。新文書がまだmainにないことと公開版反映を混同しない。

## 実行結果

作業環境はexecutor構成取得エラーで2回起動失敗。ローカル成功は主張しない。Actionsの結果・件数・証跡をPRとここへ追記する。

## 未確認

Windowsのネイティブブラウザ・保存ダイアログ・DPI、QGIS 4/Qt6、実DEMの最適性・FME/PSS実出力一致は本自動検査の対象外。[監査記録](project-audit-20261017.md)と[UI受入手順](ui-fixes-0.12.3.md)で追跡する。
