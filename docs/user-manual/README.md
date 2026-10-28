# CS Map Sheets 利用手順書（暫定版 v1.0-rc6）

更新日：2026-10-26｜**レビュー用暫定版・正式版ではありません**

## 対象と成果物

- 基本操作：CS Map Sheets **v0.13.0**、QGIS 3.44系。
- 版差：**v0.13.1**（空図郭スキップ修正、設定プロファイルv5維持）を付録Fに記載。
- 制作済み：`CS_Map_Sheets_利用手順書_利用者向け暫定版v1.0-rc6_20261026.docx`、同名PDF（20ページ）、改訂記録、SHA-256一覧、一括ZIP。
- **このPRにはPDF・DOCXのバイナリを添付していません。** 公開URLとアクセス権が確認できるまで、旧rc2のDriveリンクをrc6のダウンロード先として流用しません。

## 公開・検証の区別

- [現行 metadata.txt](../../csmap_sheets/metadata.txt) は`version=0.13.1`。
- [現行オンライン利用手順書](../user-guide.md)は、v0.13.0のQGIS公式通常版掲載、v0.13.1のGitHub Release公開を記録。v0.13.1のQGIS公式配信は別途確認。
- 掲載図版は主にv0.12.1～v0.12.2の**実地形試験図**。v0.13.1の実操作画面や同版の検証結果ではありません。
- Windows／QGISでのv0.13.1最終ZIP再導入、空図郭スキップ修正の実機確認は未実施。
- 地形判読支援機能は独立したCS Terrain Interpreterが担当。Sheetsには実装しません。

## 正式版v1.0の前に必要な作業

- [ ] v0.13.1の配布ZIPとSHA-256を確定し、Windows／QGIS 3.44で再導入・空図郭・図郭索引・`run.json`・GeoTIFFを検証。
- [ ] 操作画面の旧版原本11点を回収し、必要箇所だけ再撮影。
- [ ] PDF・Word・ZIPの実体を公開先へ登録し、匿名閲覧権限とハッシュを確認。
- [ ] 最終校正と図版の版別表記を確認。

## 関連

- [PR #48](https://github.com/yo-1/csmap-sheets/pull/48) はClosed。旧rc2の公開案内を最新版と誤認しない。
- [PR #47](https://github.com/yo-1/csmap-sheets/pull/47) の監査記録を参照。
- このPRは文書案内の更新のみ。プラグイン本体・Releaseは変更しません。
