# v0.13.1 リリース管理・検証記録

記録日：2026-10-26。基準main：`ea1c238cc0f846eaf9acf3342f95c12961c1b7e4`。

## 採用範囲

- PR #68：マスク後の全透明図郭を専用例外でスキップし、正常図郭を継続。全空はfailed、異常・キャンセルは伝播。スキップ理由とpartial_successを記録。
- PR #69：公開連絡先メール更新。
- 版番号・変更履歴・公開状態の文書を更新。プロファイルv5、計算式、既定値、配色は維持。
- PR #57の処理上限警告は2026-10-26利用者判断により当面見送り。問題発生時に再検討。
- Issue #71の入力案内、MBTiles・COG・フォーム再編は別件。既存v0.13.0のタグ・ZIPを差し替えない。

## 既存証跡の再利用

- PR #68のCodex検査：Linux/QGIS回帰228件中227成功・1スキップ・失敗0。最終調整後の関連8件成功。両方式・両傾斜法で正常図郭RGBA差0。
- MuseのLinux予備検証：マスク後全透明図郭10件スキップ・2出力、全空failed、異常分離、出力非退行を報告。Windows正式試験とは区別する。
- 2026-10-26の統括正式受入：Windows QGIS 3.44.15で60候補中51出力・9件no_dem_coverage、completed、partial_success=true。9図郭は元DEMの独立検査で有効画素0と確認した報告に基づく。対象機能受入承認済み。
- Windows受入の9件を、新規理由no_valid_relief_pixels_after_maskのWindows実測と読み替えない。試験ZIP内と実機algorithm.pyの一致は報告済みだが全体コミット同一性とはしない。
- 基準mainのCI：unit/gdal/qgis/preflight、Python構文互換が成功。

本リリース準備ではWindows試験を重複実施しない。全画素品質、境界シーム、追加GUI・キャンセル、独立FME完全一致などを今回の正式受入で合格とは扱わない。Issue #67の他項目を一括完了にしない。

## 配布物の確認と公開手順

登録用ZIPはtools/check_plugin_package.pyで固定した候補ソースから生成し、tools/check_submission.pyで実ZIPを検査する。全エントリをソースと照合しSHA-256を記録する。metadata版とengineのVERSIONは0.13.1、experimental=False。

旧CIのv0.13.0固定名レビュー資材生成を削除し、汎用submission ZIPとリリース用ワークフローを維持する。v0.13.1のPR/main CI成功後、新規タグ・Releaseを作成し、同タグからリリースワークフローが生成したZIP・SHA256SUMSを照合する。

QGIS公式へのv0.13.1申請はユーザー担当。申請・審査・通常版配信・公式ZIP照合はそれぞれ別確認であり、この文書作成時点では未実施。既存公式通常版は0.13.0。過去の検証文書の「未申請」は当時の履歴。

## 参照

- [PR #68](https://github.com/yo-1/csmap-sheets/pull/68)
- [修正・回帰報告](codex-to-gpt_20261024_CSMapSheets_T3細片マスク修正_報告.md)
- [基準main tests CI](https://github.com/yo-1/csmap-sheets/actions/runs/40212247622)
- [QGIS公式掲載](https://plugins.qgis.org/plugins/csmap_sheets/)

## リリース準備時の実行結果

- Python 3.12：228件中196成功・32スキップ・失敗0。GDAL/QGIS等がない環境の未実行分はCIで区別して確認する。
- tools/tests：4成功・失敗0。compileall、Markdownリンク74件、git diff --check成功。
- 実ZIP検査：31ファイル、0.13.1、構造・構文・Flake8・Bandit・秘密情報検査に合格。全31エントリが作成元ソースとバイト一致。
- 候補ZIP SHA-256：`6d9c75017f044668f731d5c7ca818c82cb9f6a410e088d09b964ef12c0df7239`。
- PR/main CIおよび公開タグ由来ZIPは公開時に別照合する。
