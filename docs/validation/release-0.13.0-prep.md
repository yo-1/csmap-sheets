# v0.13.0 通常版登録準備（2026-10-22、未申請・未公開）

## 対象と採用範囲

- 最新main確認SHA：`d0920f0b8b1f40813188f60cba6c2d1f6dd5bed6`。
- 再利用したDraft PR #56：`40de7f3fa6b368b4680d61848926939f598e68cc`。
- 今回のZIP元コミット：`SOURCE_COMMIT_SHA`（納品報告で確定SHAに置換）。
- v0.12.5公開系列のタグ：`3bc0d9cf9c38837bb462b580b536c73ae15e1f29`。
- 採用：main取り込み済みPR #31（欠測・端部方式、プロファイルv5）、#52（方式読込時の変数修正）、#47/#48/#51（利用手順書・ヘルプ）、#53/#54/#55（Python 3.11互換と公開系列との整合）。
- #56の版表示・説明文・変更履歴を再利用し、通常版指定と文書の整合のみ追加する。
- 除外：未マージPR #57、SHA `3053d84a2ca9d0b3954500f2e0a823c51404eb16`。既定値を超える処理上限の追加警告は含まない。
- #56の旧記載に#57が含まれていたが、実装は含まれていないため記載を訂正した。未承認PRの一括取込みは行わない。

## 通常版指定と制約

ZIP内部でversion=0.13.0、experimental=False。通常版指定はWindows実機合格・申請・承認・公開の意味ではない。
今回の追加差分はmetadata、README、CHANGELOG、検証文書、成果物梱包のCIのみ。計算式・配色・DEM処理・JSONスキーマは#56から変更しない。
標準safe_maskと明示選択のpss_approximationを含む。後者はPSS/FMEとの完全一致を保証しない。
Windows実機、Qt6実行、広域BigTIFF、独立FME参照出力との比較は未実施。
[Windows確認手順](windows-0.13.0.md)の結果を記録し、ユーザーが公開判断する。

## 検査

今回の実行結果・環境・コマンドはVALIDATION.txt追記と納品報告に記載する。旧版の結果を今回の合格根拠にしない。
最終ZIPに対し、パッケージ検査、構文・品質・セキュリティ、QGISのZIP起動・ヘルプ導線検査を実施する。
CIは最終対象コミットの結果を参照し、手動承認・公開状態とは区別する。

## 成果物と操作範囲

`csmap_sheets-v0.13.0.zip`、`SHA256SUMS.txt`、本報告、ZIPファイル一覧、Windows確認手順をまとめる。
サイズ・SHA-256・ファイル一覧は最終ZIP生成後の添付記録を参照する。
GitHub Actionsの成果物から取得できるようにする。Driveツールは本セッションにないためDrive保存は行っていない。
マージ・タグ・Release公開・既存v0.12.5変更・QGIS申請は行わない。申請はユーザーが行う。

## 今回のローカル検査結果

- Linux、Python 3.14.8、QGIS 3.44.14、GDAL 3.13.3、NumPy 2.5.3、SciPy 1.18.1、Qt 5.15.15、PyQt 5.15.11。
- `QT_QPA_PLATFORM=offscreen python tools/run_qgis_tests.py`：220件中219成功、1スキップ、失敗0。
  スキップはWEBPドライバーが存在する環境で「ドライバーなし」の分岐を実行しないため。
- `python -m unittest discover -s tools/tests -v`：4件成功、失敗0。通常版指定で不正Booleanの試験が空振りしないよう修正。
- `flake8 csmap_sheets tools`（7.4.1）：0件。`python -m compileall -q csmap_sheets`成功。Python 3.11文法もastで確認。
- `python tools/check_markdown_links.py`：リンク検査成功。
- `python tools/check_plugin_package.py ZIP`、`python tools/check_submission.py ZIP REPORT_DIR`：31ファイル、必須資材・構文・CRC・metadata・Flake8・Bandit 1.9.4・detect-secrets 1.5.0成功。
- `python tools/check_qgis_package.py ZIP --screenshots DIR`：ZIPからのimport、initGui、Processingダイアログ、保存設定ウィジェット、3ヘルプ操作、unload成功。
- 採用済みDEM/設定で画像再生成：RGB/alpha全画素一致、変更画素0、最大差0（独立した正解画像との比較ではない）。
- PDALの任意HDF/icebridge readerは依存ライブラリ不足の診断を出す。今回のLAS/LAZテストは成功。HDF/icebridge入力は未検証。
- Windows実機・Qt6実行・QGISサイト検査は未実施。CIのPython 3.11/3.12、unit/gdal/qgis/preflightは最終コミットのチェック結果を別途確認する。
