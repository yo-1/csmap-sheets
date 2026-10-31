# 検証証跡の索引（2026-10-31）

PR #31 W1〜W5 統括（pr31-w1-w5-status.md）が参照する証跡の所在一覧。
新しい証跡を作ったときは、ここへ1行追加してから判定を更新する。

## リポジトリ内（docs/validation ほか）

| 証跡 | 内容 |
|---|---|
| project-audit-20261017.md | 旧監査。W1〜W4 の定義の出所 |
| ui-fixes-0.12.3.md | v0.12.3 のUI修正6手順。DPI等は実機未確認と明記 |
| windows-0.13.0.md | QGIS 3.44.13 での 0.13.0 受入記録（項目別の確認範囲つき） |
| release-0.13.0-prep.md / release-0.13.1.md | リリース管理・検証記録 |
| merged-dem-0.12.4.md | MERGED_DEM の検証記録 |
| sample-data-0.13.0.md | 検証用サンプルの生成手順（PR #59 で main 取込済み） |
| manual-audit/ 3文書＋ addendum-0.13.1.md（PR #75） | 手順書の実装照合と v0.13.1 追補 |
| t3-mask-evidence/ | PR #68 T3 の証跡 |

## Google Drive「CS_Map-Sheets_AI連絡」

| 証跡 | 内容 |
|---|---|
| muse-to-ai_20261028-0902_CSMapSheets_PR68_受入完了と閉鎖_決定.md（ID 12ycxljDht-Q3n_0cztEuhpRvAYqKbSox） | PR #68 の受入完了・閉鎖の決定 |
| GPT 正式受入報告（ID 1v1oJAERtVoW907sLlWr2wAofJQqFfhG1） | Windows QGIS 3.44.15、60候補・51出力・9スキップの対象機能受入 |
| pr68_windows_evidence_20261028.zip（ID 1izmNLV0LtAKps9oLnIlVcNm8b6sXRI9T、SHA-256 b816ac40…） | Codex の Windows 全件実行（1,103/289）・ロック・キャンセルの証跡一式。Muse が全 run.json を照合済み |
| t3-fixture.zip（ID 1yDLYCa5SuB_JoK7Nam574oHsLerIOkwC） | PR #68 検証で使った人工DEM・sliver-only DEM・プロファイル |
| v0.13.1 リリースZIP（ID 1mIZLOa0fhnPpKmCqbx6QfqO6fREqyYDX、SHA-256 6d9c7501…） | 配布物。検証用テストZIPとのコード同一性は PR #75 追補で確認 |

## GitHub

| 証跡 | 内容 |
|---|---|
| PR #31（マージ済み b753aa3） | 本統括の対象 |
| PR #68 / Issue #67 | 空図郭スキップの修正と検証経過 |
| PR #57（マージ済み） | 処理上限の警告（次版採用、実機表示は未確認） |
| PR #59（マージ済み 24a061f） | 検証用サンプル生成の正式取込 |
| PR #75（Draft） | 手順書監査の v0.13.1 追補と実機リスト |
| PR #76 | Issue #71 の案内実装（次版候補） |

## 未取得のまま記録するもの

- `CS_Map_Sheets_PR31_Windows_minimum_validation_20261009.md`（W5 の定義を含む可能性のある原本）
- `CS_Map_Sheets_PR31_ready_20261014.zip`
- 利用手順書 rc6 の DOCX/PDF（Drive の最新は 2026-10-20 の rc2）
