# CS Map Sheets

QGIS 3.44 向けプラグイン。DEM（数値標高モデル）をマージし、曲率・傾斜・標高からCS立体図
（長野県林業総合センター考案の可視化手法）の色調を付け、国土基本図図郭単位のGeoTIFFと
XYZタイル（PNG/WebP）を生成します。

本体は [`csmap_sheets/`](csmap_sheets/) フォルダーです。QGISの「ZIPからインストール」機能で
導入する場合は、このフォルダーをZIP化して指定してください（プラグインIDは `csmap_sheets`）。

詳細な機能説明・入力形式・設定項目・既知の制約は以下を参照してください。

- [csmap_sheets/README_ja.md](csmap_sheets/README_ja.md) — 機能・使い方・XYZタイル出力の詳細
- [csmap_sheets/INPUT_GUIDE_ja.md](csmap_sheets/INPUT_GUIDE_ja.md) — 対応入力形式ごとの詳細
- [csmap_sheets/CHANGELOG.md](csmap_sheets/CHANGELOG.md) — バージョンごとの変更点
- [csmap_sheets/VALIDATION.txt](csmap_sheets/VALIDATION.txt) — 検証記録・未確認事項

姉妹プロジェクトとして、DEMからCS立体図を生成するスタンドアロンCLIツール
[fme-csmap-pipeline](https://github.com/yo-1/fme-csmap-pipeline) があります。

## ライセンス

GNU GPL v3.0 only。詳細は [LICENSE](LICENSE) を参照してください。

Copyright (C) 2026 Yoichi Wada.
