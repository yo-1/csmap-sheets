# PR #31 / Issue #67 根拠一覧

2026-10-24。非公開の原本・実機パスは掲載しない。E番号は担当作業領域の受領原本と対応。公開URLがない原本はハッシュで特定し、恒久保存先は統括側の共有待ち。

|ID|原本名・内容|SHA-256|
|---|---|---|
|E01-Windows-safe-mask-manifest|run.json|d7e40b2c279d940bdaaee6c63f7a455d58c0b1c579e7776a98ab7da5079a207b|
|E02-Windows-webp-lossy-manifest|run.json|ddb8f9cc4b790bde18f5d033479068fe4126982b45501f8f25e08155f40f78f1|
|E03-Windows-webp-lossless-manifest|run.json|b22f7ce84f10f72db7e90c87207464e8ee62f455616d0fb8ebcad13b72ae9672|
|E04-Windows-CS-TIFF|cs_relief_merged.tif|13fedca65225bb7e060171158eecce9a27ff4f68aa06397dd9cc2624de7f15c0|
|E05-Windows-DEM-TIFF|dem_merged.tif|8d9da86c08eb93e442f9ac3e92908ddc3ad35019cf32ecc9e8e9c2a1e97041e0|
|E06-QGIS-221-test-log|qgis-tests.log|277aed8d94dab3757e87d2a524498d85308d382ef0a371eff0045969ce624685|
|E07-package-test-log|qgis-package.log|d9c5798ed13f3eddd7939cf0d2f7fae96c3ea95df26d531dda0691a05c2a2db2|
|E08-final-ZIP|csmap_sheets-v0.13.0.zip|fda9d6597da2397315d80b0c3b93f6edc2a54e86ac7805800e3ff3ebe103f317|
|E09-Windows-acceptance-record|windows-0.13.0.md|d738db14495dcfa5a97af693014cd2c905909aa3dc304d00a01b7ed6fbdf697f|
|E10-validation-history|VALIDATION.txt|5141ed107982036871f88ee58d12d53b02a81c092a5adeab760d86a6872b589b|
|E11-linux-reproduced-manifest|run.json|ecf2591ea24340544da182806e5db1d02e078df9e5db1ad0e47e52da2f22f7e1|

## 公開根拠
- [W1〜W4旧定義](../validation/project-audit-20261017.md)
- [UIの旧6手順](../validation/ui-fixes-0.12.3.md)
- [後続Windows記録](../validation/windows-0.13.0.md)
- [検査履歴](../../csmap_sheets/VALIDATION.txt)
- [PR31本文](https://github.com/yo-1/csmap-sheets/pull/31)
- [PR31 CI](https://github.com/yo-1/csmap-sheets/actions/runs/39460122695)
- [製品main CI](https://github.com/yo-1/csmap-sheets/actions/runs/39877040470)
- [公開版とZIP](https://github.com/yo-1/csmap-sheets/releases/tag/v0.13.0)
- R01 [論文担当既存成果報告](20261024_research-to-gpt_csmap_comparison_status.md)
- R02 比較資料v1.6：R01記載URLを参照。本文未取得。
- [既存TIFF配列比較結果](20261024_pr31_existing-tiff-comparison.json)

## 未取得・保存上の限界
- 元CS_Map_Sheets_PR31_Windows_minimum_validation_20261009.md、CS_Map_Sheets_PR31_ready_20261014.zip。PR31コメントには別のDrive ZIP案内があるが、指定ZIPと同一と確認できないため流用しない。
- profile_v5_test.json原本、test-settings.json原本、1345画素差比較のrun.json対応、独立参照出力と広域負荷原本。
- 実機スクリーンショットは会話内で確認。公開保存URLと最終導入ZIP SHAは未取得。
- Driveツール未提供。公開GitHubに非公開パスや原JSONを転記しない。元実機ファイルの恒久共有は統括へ依頼。
- 本一覧はハッシュ台帳であり、原本ファイル自体の公開配布ではない。

## 追加依頼の再探索・照合記録

- [追加依頼 #6382247016](https://github.com/yo-1/csmap-sheets/issues/67#issuecomment-6382247016)、[担当区分 #6382170158](https://github.com/yo-1/csmap-sheets/issues/67#issuecomment-6382170158)を読了。
- main再取得：9db30b214cd869b4b967cc8751771b38adec3a55。指定元MD／ZIPを取得済みGit履歴の名前、mainツリー全体、入手済み添付・成果物で再探索、未発見。Drive取得ツールも未提供。
- 20261024_PR31_Issue67_report.zipは1ec0991の3成果物の束であり、20261014 ready ZIPではない。
- R01の引継ぎ報告は取得済み。長野36条件の台帳・入力・製品出力・独立参照出力は未取得。R02本文も未取得。理論値・人工DEM・長野製品出力・独立参照出力を区別。
- CI、81ラスタ差0、RGBA/alpha差0の再実行はしていない。追加のTIFF再計算もなし。
- T0〜T7は人手へ渡す未実施手順であり、その期待結果を今回の実測値として扱わない。
