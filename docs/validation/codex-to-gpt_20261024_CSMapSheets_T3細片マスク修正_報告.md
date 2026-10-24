# Codex→統括：T3細片マスク修正報告

2026-10-24 JST。[管理Issue #67](https://github.com/yo-1/csmap-sheets/issues/67)。完全版作業指示書を受領し、調査後の最小実装・回帰・PR準備を実施。公開v0.13.0のタグ・Release・ZIP・版番号は変更していない。PR未マージ・次版未公開であり、Windows正式受入とは別。

基準main：`9db30b214cd869b4b967cc8751771b38adec3a55`。製品v0.13.0は`79dd5da6a15733a59973ef65f19f84f54cc8135a`、対象pipeline.pyは両者で一致。修正コミットとPR URLは本報告を格納するPRおよびIssue最終コメントに完全SHAで記録する。

## 原因と最小修正

`run(stage=sheet_streaming)`→`render_sheets`→`make_relief`→`relief(safe_mask)`の順で実行。DEM被覆がある細片でも、近傍のNoDataによりminimum_filterの安全側マスク（σ2.5pxならhalo11、窓23）でalphaが全0になり得る。描画前のcoverage=0と描画後切出しalpha=0は既存スキップ対象だが、その間でmake_reliefがValueErrorを送出するため後段へ到達せずrun()の失敗記録・再送出へ達していた。

変更ファイル：

- `csmap_sheets/engine/pipeline.py`：EmptyReliefError（ValueErrorサブクラス）を当該全alpha=0条件にだけ使用。図郭ループはこの専用例外だけを捕捉して一時DEM/RGBAを削除し、警告・診断を記録して継続。GDALバンド参照を解放してから削除。マスク・計算・配色を変更せず、広いValueError捕捉や文字列一致判定をしない。
- `csmap_sheets/tests/test_empty_sheet_mask.py`：細片と正常図郭の混在、全空、破損DEM、無関係ValueError、Warp失敗、キャンセル、境界補完を回帰試験化。
- `csmap_sheets/VALIDATION.txt`および本報告・[診断証跡](t3-mask-evidence/summary.json)：結果・仕様と未確認範囲。

## run.json追加仕様・警告

既存statusのcompleted/failed/cancelledと、sheets.written、sheets.skipped_emptyを維持する。正常図郭・索引・VRT・結合GeoTIFF・XYZの作り方も維持する。render_sheetsの戻り値3要素は維持し、任意のsummary引数を追加。run()が共有する集計は失敗時の既存save()でも保存され、全空時も理由が失われない。

|追加キー|型・意味|
|---|---|
|sheets.skipped|配列。各要素はsheet_codeとreason。スキップの記録順|
|sheets.partial_success|boolean。written>0かつskipped_empty>0のときtrue。最終的な成否はstatusで判断し、failed/cancelledを成功へ変えない|

理由は`no_dem_coverage`（既存の被覆なし）、`no_valid_relief_pixels_after_mask`（今回）、`no_valid_pixels_in_sheet`（既存の切出し後空）。skipped_emptyは理由を問わない空図郭総数で、skipped配列の長さと一致する。部分出力はstatus=completedのまま診断を追加して既存利用側との互換を保つ。厳格に未知キーを拒否する独自の外部消費側があれば、追加キー対応が必要。

図郭ごとにID・理由・累積件数と「一部の図郭成果物は出力されません」をpushWarningへ出す。pushWarningのないfeedbackやCLIはWARNING接頭辞付き情報ログへフォールバック。全空時はNo nonempty sheets producedの明示的エラーとなりfailed。単一図郭エラーを何でも無視する修正ではない。

## 再現と結果

Driveの元TIFF/JSON/ZIPは未取得。Museの報告配置（822×322、1m、EPSG6677、左上-11/11、欠測5×5、σ2.5m、図郭500）に基づく人工DEMを試験で生成した。標高値は新規合成で、原本の同一SHAや649エントリCRCを本担当が確認したとはしない。

同フィクスチャを変更前pipelineへ読み込ませるとNo valid relief pixelsの1エラーで停止することを確認。変更後は09JD9999を含む10図郭を理由付きスキップし2図郭を書出し、stage=finished/status=completed/partial_success=true。有効画素239271。スキップTIF/TFWなし、一時sheet_work削除、索引件数とwritten一致、VRT参照も有効図郭だけ、結合画像alpha有効、XYZ生成成功を確認した。profile_warningsも保存されるが、ここでは固定文字列を与えたため旧JSON読込のWindows試験には算入しない。

全空時はfailed・written0・partial_success=falseとスキップ理由をrun.jsonへ保持、最終CS VRT/GeoTIFFは生成しない。破損DEM、Warp失敗、無関係ValueErrorはfailedで伝播、キャンセルはcancelled。境界補完では09JD9999が出力される。正常図郭のRGBAは既存GDAL図郭／一括比較の両方式×両傾斜法で差0を維持。

## 検査環境・コマンド・成績

Linux / Python3.14.8 / QGIS3.44.14 / GDAL3.13.3 / NumPy2.5.3 / SciPy1.18.1 / Qt5.15.15。QT_QPA_PLATFORM=offscreen、XDG作業用ディレクトリで実行。

|検査|結果|
|---|---|
|tools/run_qgis_tests.py（影響が広いpipeline変更に対し既存関連検査を含め実施）|228件、227成功・1スキップ・失敗0。WEBP存在時の欠如分岐をskip|
|unittest 新規test_empty_sheet_mask＋test_sheet_seams_gdal|8件成功・スキップ0・失敗0。最後のGDAL参照解放調整後にも実施|
|flake8 csmap_sheets tools|指摘0|
|bandit -q -r csmap_sheets -x csmap_sheets/tests|セキュリティ指摘0。既存nosecコメントの説明語に関する解析警告あり|
|compileall -q csmap_sheets、git diff --check、Markdownリンク|成功|

変更前の再現失敗ログ、変更後検査ログ、再構成入力、run.jsonと成果物は作業領域のt3-mask-fix成果物へ保存した。公開する診断抜粋はユーザー固有パスを含めずsummary.jsonへ保存。過去の81ラスタ全条件は繰り返していない。PDALの任意HDF/icebridge依存警告は従来環境の制約で、本修正の失敗ではない。

## Windows残試験・原本照合・担当

1. 統括経由でMuse証跡ZIPを取得後、SHA `0ddb477da22fa7615f2e1306df3faea3dbee7528ba3f126f54a60470ffbf9b38`・CRC・入力ハッシュを照合。同梱元人工DEMと旧v4 JSONでLinux再現条件を原本確認する。今回は未実施。
2. Windows QGIS3.44.13担当はPRの修正コードを隔離した検証プロファイルで実行。09JD9999のスキップ警告、正常図郭継続、run.jsonの旧JSON警告・safe_mask・追加診断、索引/画像/XYZの欠落説明を確認。公開ZIPを差替えない。
3. 全空失敗、一時TIF削除（Windowsファイルロック）、破損入力の失敗、境界補完の既存動作を確認する。Linux成功をWindows合格に置き換えない。
4. 統括がWindows結果とPRレビューを踏まえ次版採用・公開可否を判断。CodexのPR作成はマージ・公開を意味しない。

Driveツールはこのセッションに提供されておらず、Drive保存未実施。指定名の本MarkdownをGitHubへ代替保存し、PRとIssue #67から辿れるようにする。受領・着手・実装完了・Windows受入・公開を区別して報告する。
