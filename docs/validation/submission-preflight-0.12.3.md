# QGIS登録前検査：v0.12.3

実施日：2026-10-17 JST。対象は**公開前のv0.12.3**。公開済みv0.12.2の公式合格結果とは区別する。

## 固定した対象

- 配布内容の基準コミット：`c214911`（PR #43マージ後main）。今回の変更は開発用検査・CI・この報告のみで、プラグイン配布ファイルは変更していない。
- ZIP：`csmap_sheets-v0.12.3.zip`、30ファイル、metadata version=0.12.3、experimental=True、QGIS 3.44〜3.99。
- SHA-256：`29911e7ad6b9ed43eec64e56c4e8c500c3108d29fd6034a1d012fbaa60226678`
- 先に配布した同版の試験ZIP（SHA-256先頭`7c20320d`）とは異なる。PR #43で追加されたVALIDATION.txtの公開記録を反映して再生成したため。実行コードは同じ。今回の検査・次回申請には本報告のZIPを使う。

## 実行した検査

| 検査 | 結果・範囲 |
|---|---|
| 公式パッケージvalidator | 合格。必須メタデータ、UTF-8、LICENSE、アイコン、パス、CRC、名称、URL等 |
| Bandit | 配布ZIPを展開して実行、指摘0・解析エラー0 |
| detect-secrets | 配布ZIPを展開して全ファイル対象に実行、指摘0 |
| Flake8 | 配布ZIP・開発コードとも指摘0。ローカルは79文字、公式は120文字の基準 |
| 公式ファイル権限検査 | 30ファイル合格。実行権限なし |
| 公式不審ファイル検査 | 30ファイル合格。隠しファイル・バイナリ・実行用スクリプトなし |
| 公式セキュリティ検査集計 | 5項目合格、情報0・警告0・重大0・指摘0 |
| Qt6静的検査 | 配布Python 19ファイル、修正指摘0。コピーに実変換を適用しても全ファイル変更なし |
| Python構文・コンパイル | 合格 |
| QGIS 3.44.15 / GDAL 3.8.4 | 182件中180成功・2スキップ・失敗0 |
| QGISなし | 182件中161成功・21スキップ・失敗0 |
| ZIPを用いた起動試験 | 展開したZIPからimport、classFactory、GUI登録、Processing登録・実ダイアログ生成、JSON保存欄、解除まで合格 |
| 検査処理の異常系試験 | 3テスト合格。8種類の壊れたZIPを拒否し、検査ツールの異常終了も合格扱いしないことを確認 |
| 配布整合 | 全30ファイルの内容と基準コミットの配布対象が一致、ZIP CRC合格 |

QGIS試験の2スキップは、PDAL未導入の点群実行と、WEBPドライバが存在する環境での「ドライバ欠如」専用経路。成功件数には含めない。

## 公式実装の使用条件

- 公式サイトの公開コード：QGIS-Plugins-Website、コミット `0f098e2ab786ce34bc14be8870f03e03d90374b3` の `qgis-app/plugins/security_scanner.py` と `validator.py` を使用。
- セキュリティ検査はサイト側DBのSecurityRuleモデル読込だけを独立実行用に差し替え、enabled_rules=[]で全組込みルールを実行。検査処理は変更せず、スキップ設定・baseline・配布内抑制設定を追加していない。
- validatorは既定で環境プロキシを無効にするため、そのままではこの実行環境からURLへ到達できなかった。環境に必要なプロキシを使用するtransport設定で再実行し、全チェック合格。homepage / repository / trackerは別途HTTP 200も確認。サイト上の実行環境そのものを再現したものではない。
- Qt6はQGIS公式 `scripts/pyqt5_to_pyqt6/pyqt5_to_pyqt6.py` を使用。スクリプトSHA-256：`c6734b909bf29d06c1d173ed03f03e4ee87abf29308932a3f0b1833288f837de`。PyQt6 6.11.0、QGIS 3.44.15クラス参照を併用した静的検査。Qt5共存の警告が出る環境なので、QGIS 4/Qt6の実行試験とは扱わない。QGIS未読込のQt APIのみの検査でも指摘0。
- 公式checkerのdry_runは指摘があっても0で終了するため、終了コードだけでは判定せず、コピーで実変換を適用し差分が0であることも確認した。
- 使用ツール：Bandit 1.9.4 / detect-secrets 1.5.0 / Flake8 7.4.1。
- [公式の検査説明](https://plugins.qgis.org/docs/security-scanning/tools)、[公開前承認要件](https://plugins.qgis.org/docs/approval)。

## 再実行と継続検査

```bash
python tools/check_plugin_package.py /tmp/csmap_sheets.zip
python tools/check_submission.py /tmp/csmap_sheets.zip /tmp/submission-checks
python -m unittest discover -s tools/tests -v
python -m flake8 csmap_sheets tools
python -m compileall -q csmap_sheets tools
python -m unittest discover -s csmap_sheets/tests -t . -v
```

QGIS Python環境では、QGIS本体とProcessingプラグインのPythonパスを設定して次を実行する。Linuxでは画面なし実行に`QT_QPA_PLATFORM=offscreen`を使える。

```bash
python tools/run_qgis_tests.py
# リポジトリ直下をPYTHONPATHへ含める
python tools/check_qgis_package.py /tmp/csmap_sheets.zip
```

CI preflightにも「配布ZIPの実体の検査」と検査処理の異常系試験を追加した。ツール不足・JSON解析失敗・Bandit解析エラーを合格扱いしない。開発用スクリプトを起動するsubprocessは固定のPython実行ファイル・固定モジュール・shell=Falseであることを確認し、B404/B603の例外を当該行に限定している。プラグインZIPには含めない。

## 公式側・実機側に残る確認

- QGIS公式サイトでアップロード後に行われる検査と承認。サイトDBの同版登録の有無、アカウントのメール確認等はローカル検査では確定できない。公開ページの参照時点では公開版は0.12.2。
- Windowsのネイティブ保存ダイアログ、DPI・表示幅、ZIP導入。[実機手順](ui-fixes-0.12.3.md)に従う。
- QGIS 4 / Qt6の実行。本版の対応宣言は3.44〜3.99のまま。
- これらを「公式審査済み」「Windows実機合格」「QGIS 4対応済み」とは表記しない。

本作業では公式サイトへのアップロード、タグ・Release公開、未マージPR #31の統合は行っていない。
