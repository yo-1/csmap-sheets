# Codex向け指示｜v0.13.0公開・整合検査
指示日：2026-10-24。担当：既存「CS Map Sheets｜公開・リリース管理」。
## 目的
v0.13.0のmain・tag・Release・ZIP・CI・QGIS公式申請・承認状態を最新の証拠で照合する。既に完了した公開操作は繰り返さない。
## 作業
1. main metadata version=0.13.0、experimental=False、タグ/Release/ZIPの一致とSHA-256を照合。参照コミットを記録。
2. PR #31/#42/#44およびv0.13.0関連PRの統合状況と最新CI、申請前検査を確認。旧「Draft/未マージ」は現在の状態に転記しない。
3. QGIS公式プラグイン掲載ページの版、experimental区分、Approved、公開日時を直接確認。申請済みと承認済みを区別する。承認未確認なら未確認と記す。
4. 公式配信が確認できた場合のみ通常版配信合格とする。Windows実機の合格は別証跡とする。
5. README、metadata、docs/user-guide.md等の版・公開状態の古い記述を列挙。変更が必要なら別PRで修正する。
## 成果物・返答必須
Google DriveのCS Map Sheets連絡用フォルダへ `20261024_codex-to-gpt_csmap_release_status.md` を保存（保存不能ならGitHubのdocs/coordinationへコミット）。統括チャットに **必ず**「完了/未完了、確認日時、根拠URL、ZIP SHA、承認・配信状態、保存先URL、次の担当」を返信。返答なしを完了扱いしない。公開申請・タグ再作成・Release再発行は行わない。
