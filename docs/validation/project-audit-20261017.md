# CS Map Sheets 関係資料・残作業監査（2026-10-17）

## 基準と検証範囲
- リポジトリ: yo-1/csmap-sheets
- main: `1fd7268d5ebd38a313cb397ace8eeaca4b607d0d`
- `csmap_sheets/metadata.txt`: version=0.12.3、experimental=True
- README、metadata、PR #31/#32/#40/#41/#42、`docs/validation/ui-fixes-0.12.3.md`を照合。
- Google Drive・Libraryの関連資料は検索したが、全ファイル本文の完全監査は未了。古い資料の比較値を現行版の保証値に流用しない。

## 確認済み
- #32 設定プロファイル再読込、#40 日本語説明、#41 v0.12.2、#42 v0.12.3 UI改善はマージ済み。
- #42 はJSON拡張子補完、上書き確認、sheet_index枠線QML、GeoTIFF入力案内を実装。Linux/QGIS 3.44.15/GDAL 3.8.4で182件中180成功、2スキップ、0失敗（PR記録）。Windows実機確認ではない。
- #31 はPSS**近似**モードのDraft PR。GDAL 3.8.4の図郭比較190件中186成功、4スキップ、0失敗。人工DEM4組合せのRGBA差0。PSS/FME実出力との一致を保証しない。
- #31 head `d68154542934451498841fe5aec0dda7606d19c4` とmainの比較: diverged、ahead 5、behind 26、変更14ファイル。統合競合の有無は未検証。

## v0.12.2 公開整合記録（2026-10-17 05:11 JST）
- QGIS公式公開版: [0.12.2](https://plugins.qgis.org/plugins/csmap_sheets/version/0.12.2/)（実験的プラグイン）。ユーザー提供画面でAll Plugins掲載、日本語説明、インストール済み／提供版0.12.2を確認済み。
- [GitHub Release v0.12.2](https://github.com/yo-1/csmap-sheets/releases/tag/v0.12.2) を2026-10-17 05:11 JSTに公開。Pre-release。
- タグの実参照先: `fdfb133e1b00d9239472876e574541c61ea22434`（PR #41マージ）。APIのrefs/tags/v0.12.2で確認。
- 登録用資産: `csmap_sheets-v0.12.2.zip`、252254 bytes、27ファイル、metadata version=0.12.2。
- SHA-256: `3497e77cca09223661cb55b20f2cdc940fe37b073e042c6ff2dd0a27b442852b`。ローカル計算とGitHub資産digestが一致。`SHA256SUMS.txt`も添付。
- ZIP内の27ファイルすべてのGit blob SHAをタグ対象の配布対象ファイルと照合し一致。ZIP整合性検査も成功。
- 公式自動検査: ユーザー提供記録ではセキュリティ・品質5件合格、情報0・警告0・重大0、Qt6チェック合格（画面の実行日時2026-10-14 10:10 JST）。Qt6実行試験や全Windows受入試験の合格とは区別する。
- PR #40の日本語説明、PR #41の版更新、Qt6対応を含む。PR #42の0.12.3変更と未マージPR #31は含まない。
- 開発コードの基準mainは `1fd7268d5ebd38a313cb397ace8eeaca4b607d0d`、version=0.12.3。以後の文書コミットでmain SHAは更新されるため都度取得する。
- v0.12.2の修正・検証・申請・公式公開確認とGitHub配布整合は完了。下記v0.12.3／PR #31／実データ比較の未確認事項は残る。

## 残作業と完了条件
| ID | 担当 | 作業 | 完了条件 |
|---|---|---|---|
| A1 | Codex | #31を現行mainへ取り込む際の競合・回帰監査（Draft維持） | 競合解消案と全試験結果、#42保存UI非退行を記録 |
| A2 | Codex | v0.12.3 ZIP・タグ・Release・公式登録の相互照合 | 同一版・ソースコミット・SHA-256・ZIP構造を証跡付きで確定 |
| A3 | Work/Chat | 比較表・説明資料・操作マニュアルの版別整理 | 各結果に方式・版・DEM・格子・傾斜法・σ・欠測・出典・確認状態を明記 |
| W1 | Windows実機 | v0.12.3保存ダイアログ、JSON再読込、図郭QML、GeoTIFF案内、DPI、ZIP再導入 | `docs/validation/ui-fixes-0.12.3.md` の6手順を記録、証跡保存 |
| W2 | Windows実機 | #31旧プロファイルのsafe_mask固定・警告・run.json、実DEMの透明欠測中心 | 各画面・run.json・RGBA・差分画像を記録 |
| W3 | 実データ | 長野DEMでFMEマニュアル方式Horn 1m/0.5mとMIERUNE 1m/0.5mを比較 | 同一範囲・入力条件、画像・数値差分、比較表、データ出典を保存 |
| W4 | 実データ | PSS/FME参照成果との照合、広域処理負荷 | 参照成果と実行環境を特定、差分と時間・メモリを記録 |
| E1 | 対外 | 林野庁の利用承認・QGIS公式更新 | 申請先・対象版・回答と公開URLを記録 |

## 判断基準
- #31はW2/W4の評価とA1が完了するまでDraft維持。既定safe_maskの非退行を必須とする。
- FME/MIERUNE/PSSと「完全一致」「同等」とは、対応する参照成果で確認するまで表記しない。
- 地形判読上の有用性、計算の数値一致、運用・納品適合性を別指標で判定。
- 公開済みv0.12.2、mainのv0.12.3、GitHub Release、QGIS公式登録版を混同しない。
- ZIP公開・公式申請は版と実機検証が整ってから個別に判断する。

## Windows受入試験の最小証跡
QGIS/Qt/GDAL/PDAL版、ZIPのSHA-256、設定JSON、実行ログ、run.json、sheet_index.gpkgと隣接QML、出力GeoTIFF、画面キャプチャ、合否と再現手順を同一試験フォルダーに保存する。
