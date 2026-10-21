# 図郭対応CS立体図作成プラグイン（CS Map Sheets）

多様な標高データから、傾斜・曲率・標高を組み合わせたCS立体図を作成するQGISプラグインです。

- **多様な入力に対応**：GeoTIFFなどの標高ラスタ、国土地理院の数値標高モデル（ZIP/XML）、森林航空レーザ成果のLEM＋CSV/TXT、標高テキスト、LAS/LAZ点群を利用できます。
- **計算方式・パラメータを選択**：傾斜計算はHorn法（既定）・中央差分法から選択できます。描画方式、平滑化、曲率の範囲、配色なども調整でき、設定をJSONで保存・再利用できます。
- **GIS・Web配信用の出力**：国土基本図の図郭単位のGeoTIFF、全域を結合したGeoTIFF、PNG・WebP形式のXYZタイルを作成できます。WebPは可逆・非可逆圧縮を選択できます。
- **FMEから利用できる姉妹ツール**：[FME CSMap Pipeline](https://github.com/yo-1/fme-csmap-pipeline)も公開しています。FMEのSystemCallerから呼び出せるツールです。

## 公開版と開発版

QGIS公式で公開済みの実験的プラグインは [0.12.2](https://plugins.qgis.org/plugins/csmap_sheets/version/0.12.2/) です。
登録用ZIPとSHA-256は [GitHub Release v0.12.2](https://github.com/yo-1/csmap-sheets/releases/tag/v0.12.2) から取得できます。
GitHub版の最新版は **v0.12.5** です。[Release・導入用ZIP・SHA-256](https://github.com/yo-1/csmap-sheets/releases/tag/v0.12.5) から取得できます。v0.12.4にPython 3.11の構文互換修正だけを加え、計算・既定値・出力文字列は維持します。
QGIS公式リポジトリへ0.12.5をアップロードしました（自動検査は合格。公開状態は別途確認します）。mainにはPR #31の欠測・端部方式など、v0.12.5に含まれない未リリースの変更が入っています。
詳細は [v0.12.5記録](docs/validation/python311-hotfix-0.12.5.md)、[v0.12.4記録](docs/validation/merged-dem-0.12.4.md) を参照してください。

本体は [`csmap_sheets/`](csmap_sheets/) フォルダーです。QGISの「ZIPからインストール」機能で
導入する場合は、このフォルダーをZIP化して指定してください（プラグインIDは `csmap_sheets`）。

## 利用手順書

- [利用手順書](docs/user-guide.md) — 導入、基本作成、成果確認、トラブル対処
- [推奨設定](docs/recommended-settings.md) — 実装上の既定値・暫定推奨・比較検証済みの範囲
- [技術解説](docs/technical-guide.md) — 傾斜・曲率・配色・欠測処理と再現条件

Markdownが正本です。公開版0.12.2とGitHub版0.12.5の差は各書に明記しています。
画面内の手順書リンクは開発版で追加した機能です。

詳細な機能説明・入力形式・設定項目・既知の制約は以下を参照してください。

- [csmap_sheets/README_ja.md](csmap_sheets/README_ja.md) — 機能・使い方・XYZタイル出力の詳細
- [csmap_sheets/INPUT_GUIDE_ja.md](csmap_sheets/INPUT_GUIDE_ja.md) — 対応入力形式ごとの詳細
- [csmap_sheets/CHANGELOG.md](csmap_sheets/CHANGELOG.md) — バージョンごとの変更点
- [csmap_sheets/VALIDATION.txt](csmap_sheets/VALIDATION.txt) — 検証記録・未確認事項

## ライセンス

GNU GPL v3.0 only。詳細は [LICENSE](LICENSE) を参照してください。

Copyright (C) 2026 Yoichi Wada.

## English

CS Map Sheets generates CS terrain relief from elevation rasters, GSI DEMs (ZIP/XML), forestry LEM data with CSV/TXT metadata, elevation text grids, and LAS/LAZ point clouds. Choose Horn (default) or central-difference slope calculations, rendering methods, smoothing, curvature ranges, and colors. Save and reload settings as JSON. Export Japanese national base-map sheet GeoTIFFs, a merged GeoTIFF, and PNG/WebP XYZ tiles with lossy or lossless WebP compression. The companion FME CSMap Pipeline can be called from FME SystemCaller: https://github.com/yo-1/fme-csmap-pipeline
