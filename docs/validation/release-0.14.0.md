# v0.14.0 リリース管理・検証記録

記録日：2026-11-04。基準main：`aa074bd`（PR #83 リリース準備マージ時点）。タグ `v0.14.0` は同コミット。

## 採用範囲

- PR #81：全域CS方式画像のCOG追加出力（Issue #64）。既定オフ、統合GeoTIFFとは別ファイル、自動読込なし。
- PR #82：XYZタイルのMBTiles形式（Issue #63）。既定はPNGフォルダーのまま。失敗時は未完成ファイルを残さない。
- PR #79：フォーム整理案A（Issue #45）。区分名への形式併記とDEM欄の適用範囲明記。
- PR #76：DEMが使われない場合の具体的案内（Issue #71）。
- PR #57：外部JSONプロファイルが処理上限を既定より大きく設定した場合の警告。
- 設定プロファイルはv6（v5も読み込み可）。既存の計算式・既定の出力に変更なし。
- PR #83：CHANGELOG確定、metadata版差、VALIDATION.txtの公開準備記録。

## 検証

- Linux QGIS 3.44.14 で全251件のテスト成功（skipped=4）、flake8 clean、GitHub CI 全通過。
- 実機セッション実施票A〜HのLinux代替実施（2026-11-03、linux-session-0.13.1-20261103.md）で、表示・警告・旧JSON・プロファイル往復・nodata透明化を確認。
- 配布ZIPはGitHubリリースワークフローが生成し、同ワークフローの check_submission.py 検査に合格。csmap_sheets-v0.14.0.zip（277,619バイト、SHA-256 2743b8e4290640d5268b2c848eb9bd6c9c8448c7d0c5d57cd2fe1f0cb49749ee）。
- Muse が配布ZIPを単体で導入し、版数0.14.0の表示、アルゴリズム生成、COG（LAYOUT=COG）とMBTilesのスモーク実行を確認。

## 申請

- 2026-11-04 19:29 JST に plugins.qgis.org へ提出済み。バージョンページ：https://plugins.qgis.org/plugins/csmap_sheets/version/0.14.0/
- 実施はClaude（ZIPの受け渡しとチェックリスト1〜3）と利用者（ログイン、チェックリスト4〜6、Save）の分担。Muse のブラウザ担当はポリシーにより送信を引き受けなかったため、依頼文書（Drive、muse-to-claude / muse-to-gpt 20261104-0725）で委託した。
- Muse が 2026-11-04 20:55 JST にポータルで実測：Approved = no（手動審査待ち）、Security Scan ✓、Qt6 Check ✓、Experimental = no、対応版 3.44.0〜3.99.0、外部依存なし。変更履歴は metadata の 0.14.0 版差と一致。
- 承認：2026-11-11 20:38 JST に Muse が実測し **Approved = yes** を確認。プラグイン本体ページでも 0.14.0 が最新の安定版として掲載されている（提出から約7日で手動承認通過）。
- ポータル登録ZIPの照合（同日）：バージョンページのダウンロード（/plugins/csmap_sheets/version/0.14.0/download/）から取得したZIPは 277,619バイト、SHA-256 2743b8e4290640d5268b2c848eb9bd6c9c8448c7d0c5d57cd2fe1f0cb49749ee で、配布ZIPと完全一致。Claude報告の未確認事項はこれで解消した。

## 未確認（次版の受入へ）

- Windows実機・QFieldでの表示確認、プラグインマネージャ画面、実モニターDPI、ネイティブ保存ダイアログ。

## 参照

- [GitHub Release v0.14.0](https://github.com/yo-1/csmap-sheets/releases/tag/v0.14.0)
- [QGIS公式掲載](https://plugins.qgis.org/plugins/csmap_sheets/)
- Drive「CS_Map-Sheets_AI連絡」：Claude実施報告（claude-to-muse_20261104-1935、ID 1TqoeDoq5fbdX2jsmIKpRhD6Ykqx-r0h2）
