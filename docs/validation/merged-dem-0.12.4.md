# CS Map Sheets v0.12.4

2026-10-20。変更: マージ済み標高DEMの任意保存。

- `MERGED_DEM`（既定オフ）を有効にすると、`dem_merged.tif`を保存。
- 元はCS計算で使用する`projected_dem.vrt`。平滑化前の単バンド標高を保存し、書出し時の再補間なし。
- GeoTIFF以外の変換入力と標高ラスタ入力の共通経路に適用。
- Processing出力`DEM_MERGED_GEOTIFF`、run.jsonに保存先と出力内容を記録。
- 図郭別DEM恒久保存は別プロジェクトDEM Map Sheetsで扱う。
- 新設定を含むプロファイルは未対応旧版では拒否される。旧プロファイルの読込は維持。

## 確認済み

[機能追加コミットのCI](https://github.com/yo-1/csmap-sheets/actions/runs/39442868908): unit / gdal / preflight成功。
GDAL 3.8.4、NumPy 1.26.4、SciPy 1.11.4で189件中180成功・9スキップ・失敗0。
実GeoTIFF保存、VRTとの値・座標系・格子・NoData一致、単独での読込を確認。
Pythonのみの環境は189件中167成功・22スキップ・失敗0。
Flake8・Bandit・detect-secrets・配布ZIP構造/構文/CRC/metadata検査成功。

## 未確認

Windows/QGIS 3.44のGUI・Qt6実行、大容量BigTIFF。
QGIS公式リポジトリへの新版掲載はGitHub Releaseと別に扱う。

## 配布

Release公開を契機に、タグのソースからZIPを作成・検査し、`csmap_sheets-v0.12.4.zip`と`SHA256SUMS.txt`をReleaseへ添付する。
ZIPは`csmap_sheets/`一階層から始まるQGIS導入用。GitHubの自動生成Source code ZIPとは区別する。
