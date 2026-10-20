# CS Map Sheets 利用手順書（暫定版 v1.0-rc2）

対象：**CS Map Sheets v0.12.3 / QGIS 3.44系**  
文書更新日：2026-10-20  
公開状態：**暫定版（Release Candidate）／Windows実機・旧版スクリーンショットの最終照合前**

## 利用手順書

- [PDF版（Google Drive、30ページ）](https://drive.google.com/file/d/12b2O_G-Ht8d3D6by2HPilN6Z8Kax57w7/view)
- [編集用Word版（Google Drive）](https://docs.google.com/document/d/1cF_Bi7OjpcwVYkC-qyPTLx6iLxgG3vk7/edit)
- [操作画面の採用判定台帳（CSV、Google Drive）](https://drive.google.com/file/d/1v2Lk_F8229Aq5owN0OPGYDV9u0mqzd_-/view)
- [Drive保存フォルダ](https://drive.google.com/drive/folders/15BVxBClxzgH4amSaG8LhiZgcGGHY3TTQ)

**注意：** 上記リンクはDrive上の保存先です。リンクを知る全員に閲覧を許可する設定かどうかは未確認です。GitHubへのこの変更は、文書本体のバイナリをリポジトリに格納するものではありません。外部リンクが閲覧できない場合は公開権限の確認が必要です。

## 主な内容

入力DEMの事前確認、図郭単位でのCS立体図作成、設定JSONの保存、`run.json`の実効設定・処理完了状態の確認、GeoTIFF／XYZ等の成果確認、トラブルシューティング、操作確認シート（付録E）、旧版スクリーンショット採用判定（付録F）を収録。

## 暫定版としての制約

- 既存の地形比較画像は、操作画面のスクリーンショットではありません。
- 過去のQGIS操作画面の原本11点は未回収であり、v0.12.3の実画面との照合は未完了です。
- Windows／QGIS 3.44での画面・操作の最終確認は未実施です。
- 画面初期値とプロファイル適用後の実効値は異なる場合があります。実効設定は`run.json`の`settings`と`rendering`で確認してください。
- 設定JSONの保存先は実行前に指定します。設定JSONの存在は処理成功の証明ではありません。`run.json.status == "completed"`および必要な成果物を確認してください。
- 特定の計算格子・平滑化・配色をあらゆる地形に対する最適条件とは断定していません。

## 関連監査

- [マニュアル整合性監査 Draft PR #47](https://github.com/yo-1/csmap-sheets/pull/47)（未マージ）

この文書案内の追加はプラグインの計算コード、既定値、既存の公開Releaseを変更しません。レビュー後に本案内をmainへ反映するかを判断します。
