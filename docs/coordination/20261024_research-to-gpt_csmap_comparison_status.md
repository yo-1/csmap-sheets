# 論文担当→統括｜CS Map Sheets 資料現行化・成果共有

日付：2026-10-24。対象：論文資料、既存利用資料および公開状況。調査範囲は下記のみで全Drive/Libraryの網羅確認ではない。

## 実施済み
- 指示書 `20261024_work_documents.md` と PR #66 を確認。PR #66 は open・未マージ。
- PR #66 の `docs/user-guide.md` 冒頭を確認し、v0.13.0 GitHub Release公開済・QGIS公式申請済・管理者承認/通常配信未確認、と記載されていることを確認。重複編集は行わない。
- PR #65（公開状況の文書改訂）、#62（Windows実機試験記録）、#59（人工DEM試料）を論文の根拠候補に分類。
- 既存論文準備v0.1・論文草稿v0.2・証拠台帳v0.2・独立理論検算を再利用対象に指定。独立理論検算を製品実測値と取り違えない。
- 既存比較資料 `01_CS立体図_4ツール徹底比較_v1.6.md` を再利用資料とし、FME/MIERUNE/PSSの計算一致・地形判読性能・運用適合を別評価とする。

## 未完了
- Google Drive検索は連携アカウント認証エラーで今回実施不可。全件棚卸し、最新の論文成果および長野DEM原データの取得と完全照合は未実施。
- 林野庁説明資料・推奨設定・技術解説全文の現行化はWork担当範囲。論文担当による重複改訂なし。
- 原データに基づく統計、図版最終化、独立コードレビューの原文取り込み、先行文献原本の書誌確認は未完了。論文完成・投稿可能とは判定しない。

## 根拠・版・保存先
- 指示書：https://github.com/yo-1/csmap-sheets/blob/docs/coordination-20261024/docs/coordination/20261024_work_documents.md
- PR #66：https://github.com/yo-1/csmap-sheets/pull/66
- PR #65：https://github.com/yo-1/csmap-sheets/pull/65
- PR #62：https://github.com/yo-1/csmap-sheets/pull/62
- PR #59：https://github.com/yo-1/csmap-sheets/pull/59
- 比較資料v1.6：https://drive.google.com/file/d/1hRg-BvXjMSN7Wb660YEE8NXYYo1cjsEN/view
- 論文草稿v0.2：2026-10-22会話内生成物。現行Drive保存先・原本の再取得は未確認。

## 要判断事項／引継ぎ
- PR #66のマージは統括判断。本報告は当該PRブランチ上の追加文書であり、mainには未反映。
- 論文用数値は独立理論検算とプラグイン実測を区別し、証拠とバージョンがそろった結果だけを確定値として用いる。
- Google Driveの連絡用フォルダへの指定名 `20261024_research-to-gpt_csmap_comparison_status.md` の保存は、当該連携認証エラーのため未達。代替としてGitHub本ファイルを保存した。Work担当の別ファイル `20261024_work-to-gpt_csmap_document_status.md` は本担当では作成しない。
