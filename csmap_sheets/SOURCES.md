# 参照した仕様・API

確認日：2026-09-20。以下を読込み設計の情報源として使用しました。
本ソフトは、これらのすべての成果定義に完全準拠した納品物を自動作成するものではありません。

- Pacific Spatial Solutions株式会社「FMEによるCS立体図作成マニュアル」（2020年、G空間情報センター配布）別紙3、および同梱FMW：5レイヤーのパレット、比率、標高・傾斜範囲、RGB別ストレッチを確認。FMWの曲率は `0 -1 0 / -1 4 -1 / 0 -1 0` の畳み込みで、除数に `cell_size**2 * 0.01` を使うため、本実装の1/m値を100倍した尺度と整合することも確認。ただしFMEは傾斜にHorn法を使用し、平滑化カーネル条件も本プラグインと同一とは限らない。
  https://www.geospatial.jp/ckan/dataset/fme-csmapmaker
- Forestgeo.info「CS立体図の色合いを本家に近づけてみた」：FME版マニュアル参考のLUT、5レイヤー混合比、RGB別ストレッチ。
  https://forestgeo.info/2026/04/23/cs%E7%AB%8B%E4%BD%93%E5%9B%B3%E3%81%AE%E8%89%B2%E5%90%88%E3%81%84%E3%82%92%E6%9C%AC%E5%AE%B6%E3%81%AB%E8%BF%91%E3%81%A5%E3%81%91%E3%81%A6%E3%81%BF%E3%81%9F/
- Qiita「CS立体図の “色” について考えてみた」：主要実装間の配色・合成方式の比較。
  https://qiita.com/salamanderezo/items/484dd619c281750271d3

- 森林GISフォーラム・森林情報標準仕様分科会：森林資源データ解析・管理標準仕様書Ver.3.1、オープンデータ標準仕様書Ver.2.1（2026年8月版）。DEMと微地形図の位置づけ・成果の区別を参照。
  https://fgis.jp/cloud
- 国土地理院「航空レーザ測量データを用いた樹高等のデータ作成」：一般的な航空レーザ成果のLEM、CSV、GROUND等の構成を参照。
  https://www.gsi.go.jp/chirijoho/chirijoho40069.html
- 国土地理院・基盤地図情報ダウンロードサービスの仕様公開ページ：ZIP/XML、スキーマ世代、DEMの種類を確認。
  https://service.gsi.go.jp/kiban/app/help/
- 基盤地図情報ダウンロードデータファイル仕様書 第5.3版：GML及びJGD2024の識別子。
  https://service.gsi.go.jp/kiban/contents/screen/basismap/documents/FGD_DLFileSpecV5.3.pdf
- 国土地理院「日本の測地系」：JGD2024の水平座標がJGD2011から引き継がれることを確認。鉛直基準の変換とは区別。
  https://www.gsi.go.jp/sokuchikijun/datum-main.html
- PDAL readers.las：LAS/LAZ、scale/offset、波形付きPoint Formatの制限。
  https://pdal.io/en/stable/stages/readers.las.html
- PDAL writers.gdal：補間半径、IDW/mean/min、格子原点、幅・高さ、NoData。
  https://pdal.io/en/stable/stages/writers.gdal.html
- PDAL filters.smrf：地表面分類と分類用の設定。
  https://pdal.io/en/stable/stages/filters.smrf.html
- PDAL info：ファイルの点数・範囲・座標系の取得。
  https://pdal.io/en/stable/apps/info.html
- GDAL Python Utilities：モザイク、再投影、GeoTIFF作成、XYZ工程。
  https://gdal.org/en/stable/api/python/utilities.html
- QGIS 3.44 Processing API：ファイル複数選択とパラメータ評価。
  https://api.qgis.org/api/3.44/classQgsProcessingParameters.html
