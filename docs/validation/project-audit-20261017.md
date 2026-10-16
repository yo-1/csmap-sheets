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
- 公開済みv0.12.1、mainのv0.12.3、GitHub Release、QGIS公式登録版を混同しない。
- ZIP公開・公式申請は版と実機検証が整ってから個別に判断する。

## Windows受入試験の最小証跡
QGIS/Qt/GDAL/PDAL版、ZIPのSHA-256、設定JSON、実行ログ、run.json、sheet_index.gpkgと隣接QML、出力GeoTIFF、画面キャプチャ、合否と再現手順を同一試験フォルダーに保存する。
