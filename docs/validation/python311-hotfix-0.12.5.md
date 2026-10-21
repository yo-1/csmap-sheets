# CS Map Sheets v0.12.5 準備記録

v0.12.4タグ `2f8951ba561663c58b98a90ed4a6177959c4dbd3` を基準にする、Python 3.11構文互換だけのホットフィックスです。準備中で、まだ公開していません。

## 修正と版表記

- input_sources.py、map_sheets.py、xyz_tiles.py、pipeline.pyのf文字列を置換。計算・既定値・出力文字列は維持。
- metadata.txtのversionと最新changelog、pipeline.pyのVERSIONを0.12.5へ更新。
- README.mdとREADME_ja.mdに準備版・未公開を明記。CHANGELOG.mdに0.12.5節を追加。
- VALIDATION.txtへ今回の記録を追記。以前の版・機能導入時期・配布実績の記録は書き換えない。
- release.ymlはmetadataとタグから版・ZIP名を組み立てるため変更不要。

## 検証

Python 3.11／3.12で `python -m compileall -q csmap_sheets tools` を実行。
文字列回帰テスト4件は修正後の両版と、変更前v0.12.4のPython 3.12で同じ期待値と照合します。
既存のunit・GDAL・preflightに、QGIS 3.44での既存回帰・実ZIP起動検査を加えます。実行結果は準備PRを参照してください。

## 未確認・承認後の作業

Windows/QGIS実機、Qt6、3.11での全依存環境は未確認です。
今回の作業はrelease/v0.12.5向けのPR作成までです。マージ・タグ・Release公開・公式申請は行いません。
公開済みZIPは差し替えません。
