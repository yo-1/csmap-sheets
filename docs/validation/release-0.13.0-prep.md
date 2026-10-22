# v0.13.0 通常版登録準備・最終検査報告

2026-10-22。ZIP準備とレビュー資料の作成まで。申請・審査承認・公開確認は未実施。

## 対象コミット・採用範囲

- 最終ZIP元コミット：`SOURCE_COMMIT_SHA`（Actions成果物の報告では完全SHAへ置換）。
- 最新main確認：`d0920f0b8b1f40813188f60cba6c2d1f6dd5bed6`。最終確認時に変化があれば納品報告で区別する。
- 既存準備PR #56：`40de7f3fa6b368b4680d61848926939f598e68cc`を再利用。
- v0.12.5公開系列タグ：`3bc0d9cf9c38837bb462b580b536c73ae15e1f29`。
- 採用済みmainの#31（欠測・端部方式、v5）、#52（読込時の変数修正）、#47/#48/#51（文書・ヘルプ）、#53/#54/#55（構文互換・公開系列との整合）を含む。
- この準備系列に含む差分：#56版準備、#58通常版指定と文書・ZIP納品、#60図郭索引の読込み後スタイル、#61「境界補完」名称、今回の実機記録・最終納品整理。
- 除外：未承認#57、SHA `3053d84a2ca9d0b3954500f2e0a823c51404eb16`。処理上限を超えたプロファイルの追加警告は含めない。
- #59人工DEM配布は別検証資材。プラグイン本体へ同梱せず、登録準備系列へ一括取り込みしない。

## 版・通常版・差分

ZIP内部でversion=0.13.0、experimental=False。名称は「標準：欠測の影響範囲を透過」「境界補完：計算時のみ端部・欠測近傍を補完」。
内部識別子pss_approximationは既存JSON互換のため維持する。
#56から追加した実行時変更は図郭索引の読み込み後スタイル修正と表示文字列。計算式・配色・DEM処理・JSONスキーマの追加変更はない。
境界補完は計算中だけ端値延長・中心値代用を行い、欠測中心は透明。独立PSS/FME出力との完全一致は保証しない。

## 今回の検査と環境

Linux / Python 3.14.8 / QGIS 3.44.14 / GDAL 3.13.3 / NumPy 2.5.3 / SciPy 1.18.1 / Qt 5.15.15 / PyQt 5.15.11。

|コマンド・対象|結果|
|---|---|
|QT_QPA_PLATFORM=offscreen python tools/run_qgis_tests.py|221件中220成功、1スキップ、失敗0。WEBP存在時のドライバー欠如分岐をスキップ|
|python -m unittest discover -s tools/tests -v|4件成功、失敗0|
|flake8 csmap_sheets tools|7.4.1、指摘0|
|python -m compileall -q csmap_sheets|成功。Python 3.11文法はastでも確認|
|python tools/check_markdown_links.py|成功|
|python tools/check_plugin_package.py ZIP|31ファイル、必須資材・構造・CRC確認|
|python tools/check_submission.py ZIP REPORT_DIR|構文・metadata・Flake8・Bandit 1.9.4・detect-secrets 1.5.0成功|
|python tools/check_qgis_package.py ZIP --screenshots DIR|ZIPからimport・initGui・Processing画面・設定ウィジェット・3ヘルプ操作・unload成功|
|同条件の実DEM再生成・Windows人工DEM出力再生成|各比較でRGB/alpha全画素一致、最大差0。独立した正解地図との比較ではない|

対象SHAのCI（Python 3.11/3.12、preflight/unit/gdal/qgis）は最終PRのチェックとActions実行ページを参照する。
完了前のCIは合格扱いにしない。旧版・親コミットの結果を最終SHAのCIの代わりにしない。
PDALの任意HDF/icebridge readerは依存警告あり。当該入力は未検証、LAS/LAZのテストは成功。

## Windows受入結果と未確認事項

ユーザーのQGIS 3.44.13/Python 3.12.13/GDAL 3.13.2で実施したログ・画面・提供TIFF/JSONを確認。
基本処理、DEM保存、標準JSON再読込、分割入力、境界補完、図郭表示修正、PNG生成、WebP両圧縮のエンコーダー指定・正常完了を確認。
[受入結果表](windows-0.13.0.md)に証拠の種類・限界・追加手順を記載した。
最終名称変更後ZIPの実機再導入、旧JSON移行警告、境界補完JSON往復、日本語パス等の全UI分岐、XYZそのものの表示やWebP復号比較は未確認。
Qt6実行、広域BigTIFF、独立FME出力比較も未確認。通常版指定と実機の全項目合格は別。

## レビュー対象・マージ順序（まだ実行しない）

依存するDraft PRの取り込み先を維持する場合は、上位差分から親へ順に反映する。

1. 今回の最終記録PR → #61のブランチ ui/0130-boundary-completion。
2. #61 → #60のブランチ fix/0130-sheet-index-loading。
3. #60 → #58のブランチ prep/0.13.0-standard。
4. #58 → #56のブランチ chore/release-0.13.0-prep。
5. #56 → main。

各段階で差分と更新された対象SHAのCIを再確認する。#57は除外、#59は必要なら検証資材として別途判断する。
統合後にコード内容・ZIP内部資材が変わる場合は再生成・再検査・ハッシュ再計算する。
本作業ではマージ・タグ・Release公開・既存0.12.5変更を一切行わない。

## 納品と次の操作

最終成果物 csmap-sheets-v0.13.0-final をActionsから取得する。
外側の成果物ZIPを展開し、内側のcsmap_sheets-v0.13.0.zipを導入・申請に使用する。
SHA256SUMS.txt、ZIPサイズ、全ファイル一覧、Windows受入記録を同梱する。
Driveツールは本セッションに提供されていないためDrive保存済みとは報告しない。
ユーザーは未確認項目を踏まえて公開判断し、レビュー・統合後の確定ZIPをQGISサイトへ申請する。
承認後は0.13.0自体のexperimental=Falseを確認する。過去の実験版の存在とは区別する。
