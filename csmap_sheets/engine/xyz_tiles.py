"""Serial GDAL XYZ tile writer (PNG or WebP); no external process or gdal2tiles dependency."""
import json
import math
from pathlib import Path

HALF_WORLD = math.pi * 6378137.0
XYZ_FORMATS = ('png', 'webp')
# WebP creation options per the GDAL WEBP driver (gdal.org): QUALITY is 1-100 (driver
# default 75), LOSSLESS is TRUE/FALSE (driver default FALSE). xyz_webp_lossless=True
# keeps the v0.8.0 behaviour (LOSSLESS=TRUE) as the plugin default; quality is only
# meaningful when xyz_webp_lossless is False.
# v0.9.4: 標準運用として最大ズーム16を採用（検証用データでの検証結果、2026-09-30。
# 18のままだと広域・高解像度データで候補タイル数がxyz_max_tilesの上限を
# 超過しやすく、しかも超過判定がCS立体図計算・結合GeoTIFF書き出しの後まで
# 遅延するため、無駄な計算時間を招く。恒久対応は事前検証の追加を別途検討。
DEFAULTS = dict(xyz_enabled=True, xyz_min_zoom=12, xyz_max_zoom=16,
                xyz_max_tiles=100000, xyz_format='png',
                xyz_webp_lossless=True, xyz_webp_quality=75)


def validate_xyz(c):
    if not isinstance(c['xyz_enabled'], bool):
        raise ValueError('xyz_enabled must be boolean')
    for key in ('xyz_min_zoom', 'xyz_max_zoom', 'xyz_max_tiles'):
        if type(c[key]) is not int:
            raise ValueError(key+' must be an integer')
    if not 0 <= c['xyz_min_zoom'] <= c['xyz_max_zoom'] <= 24:
        raise ValueError('XYZ zoom requires 0 <= min <= max <= 24')
    if c['xyz_max_tiles'] <= 0:
        raise ValueError('xyz_max_tiles must be positive')
    if c['xyz_format'] not in XYZ_FORMATS:
        raise ValueError(f'xyz_format must be one of {XYZ_FORMATS}')
    if not isinstance(c['xyz_webp_lossless'], bool):
        raise ValueError('xyz_webp_lossless must be boolean')
    if type(c['xyz_webp_quality']) is not int or not 1 <= c['xyz_webp_quality'] <= 100:
        raise ValueError('xyz_webp_quality must be an integer in 1..100')


def _tile_encoder(xyz_format, gdal, webp_lossless=True, webp_quality=75):
    """Return (driver, extension, creation_options, encoder_record) for the chosen tile format.

    Raises RuntimeError with a clear message if the required GDAL driver is
    unavailable in the running environment; never silently falls back to PNG
    (per the WebP handover instructions, section 3). webp_lossless/webp_quality
    are ignored for xyz_format='png'.
    """
    if xyz_format == 'png':
        driver = gdal.GetDriverByName('PNG')
        if driver is None:
            raise RuntimeError('GDAL PNG driver is unavailable in this environment.')
        return driver, 'png', [], {'driver': 'PNG', 'lossless': True, 'creation_options': []}
    if xyz_format == 'webp':
        driver = gdal.GetDriverByName('WEBP')
        if driver is None:
            raise RuntimeError(
                'GDAL WEBPドライバがこの環境で利用できません（libwebpなしでビルドされたGDALの可能性があります）。'
                'PNGへの自動切替えは行いません。QGIS同梱GDALのビルド構成を確認するか、'
                'XYZ画像形式をPNGへ変更してください。')
        if webp_lossless:
            options = ['LOSSLESS=TRUE']
            record = {'driver': 'WEBP', 'lossless': True, 'quality': None, 'creation_options': options}
        else:
            options = ['LOSSLESS=FALSE', f'QUALITY={webp_quality}']
            record = {'driver': 'WEBP', 'lossless': False, 'quality': webp_quality, 'creation_options': options}
        return driver, 'webp', options, record
    raise ValueError(f'xyz_format must be one of {XYZ_FORMATS}')


def tile_bounds(z, x, y):
    span = 2*HALF_WORLD/(1 << z)
    return (-HALF_WORLD+x*span, HALF_WORLD-(y+1)*span,
            -HALF_WORLD+(x+1)*span, HALF_WORLD-y*span)


def tile_range(bounds, z):
    west, south, east, north = bounds
    if not all(math.isfinite(v) for v in bounds) or west >= east or south >= north:
        raise ValueError('Invalid XYZ extent')
    n = 1 << z
    span = 2*HALF_WORLD/n
    # Exclusive east/south edges avoid duplicate tiles on exact boundaries.
    x0 = max(0, math.floor((west+HALF_WORLD)/span))
    x1 = min(n-1, math.ceil((east+HALF_WORLD)/span)-1)
    y0 = max(0, math.floor((HALF_WORLD-north)/span))
    y1 = min(n-1, math.ceil((HALF_WORLD-south)/span)-1)
    return x0, x1, y0, y1


def raster_bounds_3857(path, gdal, osr):
    """任意の測地参照ラスターの範囲をEPSG:3857のbounds (west,south,east,north) として返す。

    write_xyz()内のRGBA/Byte検証とは独立しており、CS立体図(render_sheets)計算を
    開始する前に候補タイル数を見積もる目的（precheck_xyz_tile_count）でも使う。
    """
    src = gdal.Open(str(path))
    if src is None:
        raise ValueError('Raster could not be opened for XYZ extent check: ' + str(path))
    try:
        srs = osr.SpatialReference()
        if not src.GetProjection() or srs.ImportFromWkt(src.GetProjection()) != 0:
            raise ValueError('XYZ input CRS is missing or invalid')
        merc = osr.SpatialReference()
        merc.ImportFromEPSG(3857)
        for crs in (srs, merc):
            crs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        gt = src.GetGeoTransform()
        if gt[2] != 0 or gt[4] != 0 or gt[1] <= 0 or gt[5] >= 0:
            raise ValueError('XYZ input must be north-up')
        return osr.CoordinateTransformation(srs, merc).TransformBounds(
            gt[0], gt[3]+gt[5]*src.RasterYSize,
            gt[0]+gt[1]*src.RasterXSize, gt[3], 41)
    finally:
        src = None


def estimate_candidate_tiles(bounds, min_zoom, max_zoom):
    """指定範囲(EPSG:3857のbounds)・ズーム範囲でのXYZ候補タイル数を返す。

    write_xyz()の本チェックと同じ計算式。実タイル生成前の早期見積りに使う。
    """
    ranges = [(z, tile_range(bounds, z)) for z in range(min_zoom, max_zoom+1)]
    return sum(max(0, b-a+1)*max(0, d-e+1) for _, (a, b, e, d) in ranges)


def precheck_xyz_tile_count(path, c, gdal, osr):
    """CS立体図の計算(render_sheets、本プラグイン最重量の処理)を始める前に、
    候補タイル数が上限(xyz_max_tiles)を超えないか検証する（フェイルファスト）。

    見積りにはCS立体図と概ね同じ範囲を持つ投影済みDEM(projected_dem.vrt)を使う。
    render_sheetsは図郭境界に合わせて範囲をわずかに拡張する場合があるため、
    ここでの見積りは実際の候補数よりわずかに小さくなり得る。最終的な安全性は
    write_xyz()側の本チェック（CS立体図そのものから再計算）で担保される。

    xyz_enabledがFalseの場合は何もせずNoneを返す。
    """
    c = {**DEFAULTS, **c}
    if not c['xyz_enabled']:
        return None
    bounds = raster_bounds_3857(path, gdal, osr)
    total = estimate_candidate_tiles(bounds, c['xyz_min_zoom'], c['xyz_max_zoom'])
    if total > c['xyz_max_tiles']:
        raise ValueError(
            f'XYZ candidate tiles(事前見積り)={total:,}; limit={c["xyz_max_tiles"]:,}。'
            'CS立体図の計算を開始する前に停止しました（無駄な計算時間を避けるため）。'
            'XYZ最大ズームを下げるか、XYZ候補枚数の上限(xyz_max_tiles)を増やしてください。')
    return total


def write_xyz(source, destination, c, gdal, osr, feedback=None):
    validate_xyz({**DEFAULTS, **c})
    c = {**DEFAULTS, **c}
    # Fail fast, before any output is created, if the requested encoder is unavailable.
    driver, ext, creation_options, encoder = _tile_encoder(
        c['xyz_format'], gdal, c['xyz_webp_lossless'], c['xyz_webp_quality'])
    def cancel():
        if feedback is not None and feedback.isCanceled():
            raise RuntimeError('XYZ cancelled; output is incomplete')
    cancel()
    src = gdal.Open(str(source))
    if src is None or src.RasterCount != 4:
        raise ValueError('XYZ input must be a georeferenced RGBA raster')
    if any(src.GetRasterBand(i).DataType != gdal.GDT_Byte for i in range(1, 5)):
        raise ValueError('XYZ input must be Byte RGBA')
    srs = osr.SpatialReference()
    if not src.GetProjection() or srs.ImportFromWkt(src.GetProjection()) != 0:
        raise ValueError('XYZ input CRS is missing or invalid')
    merc = osr.SpatialReference()
    merc.ImportFromEPSG(3857)
    for crs in (srs, merc):
        crs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    gt = src.GetGeoTransform()
    if gt[2] != 0 or gt[4] != 0 or gt[1] <= 0 or gt[5] >= 0:
        raise ValueError('XYZ input must be north-up')
    bounds = osr.CoordinateTransformation(srs, merc).TransformBounds(
        gt[0], gt[3]+gt[5]*src.RasterYSize,
        gt[0]+gt[1]*src.RasterXSize, gt[3], 41)
    ranges = [(z, tile_range(bounds, z)) for z in range(c['xyz_min_zoom'], c['xyz_max_zoom']+1)]
    total = sum(max(0,b-a+1)*max(0,d-e+1) for _,(a,b,e,d) in ranges)
    if total == 0 or total > c['xyz_max_tiles']:
        raise ValueError(f'XYZ candidate tiles={total:,}; limit={c["xyz_max_tiles"]:,}. Reduce extent/max zoom or increase xyz_max_tiles.')
    out = Path(destination)
    out.mkdir(parents=True, exist_ok=False)
    info = dict(status='running', scheme='xyz', crs='EPSG:3857', tile_size=256,
                minzoom=c['xyz_min_zoom'], maxzoom=c['xyz_max_zoom'],
                bounds_3857=list(bounds), format=c['xyz_format'],
                template='{z}/{x}/{y}.'+ext, encoder=encoder,
                candidate_tiles=total, written_tiles=0, skipped_empty_tiles=0)
    def save():
        (out/'xyz.json').write_text(json.dumps(info, indent=2), encoding='utf-8')
    save()
    try:
        done = 0
        for z,(x0,x1,y0,y1) in ranges:
            for x in range(x0,x1+1):
                for y in range(y0,y1+1):
                    cancel()
                    tile = gdal.Warp('', src, format='MEM', dstSRS='EPSG:3857',
                        outputBounds=tile_bounds(z,x,y), width=256, height=256,
                        outputType=gdal.GDT_Byte, srcAlpha=True, dstAlpha=True,
                        resampleAlg='average', errorThreshold=0, warpMemoryLimit=64,
                        callback=lambda fraction,message,data: 0 if feedback is not None and feedback.isCanceled() else 1)
                    cancel()
                    if tile is None or tile.RasterCount != 4:
                        raise RuntimeError('XYZ warp failed')
                    pixels = tile.ReadAsArray()
                    if pixels is None:
                        raise RuntimeError('XYZ pixel read failed')
                    if pixels[3].any():
                        folder = out/str(z)/str(x)
                        folder.mkdir(parents=True,exist_ok=True)
                        # Plain image dataset avoids sidecar georeferencing files.
                        plain = gdal.GetDriverByName('MEM').Create('',256,256,4,gdal.GDT_Byte)
                        for i, ci in enumerate((gdal.GCI_RedBand,gdal.GCI_GreenBand,gdal.GCI_BlueBand,gdal.GCI_AlphaBand)):
                            band = plain.GetRasterBand(i+1)
                            band.WriteArray(pixels[i])
                            band.SetColorInterpretation(ci)
                        written = driver.CreateCopy(str(folder/f'{y}.{ext}'),plain,options=creation_options)
                        if written is None:
                            raise RuntimeError(f'{ext.upper()} write failed')
                        written.FlushCache()
                        written = plain = None
                        info['written_tiles'] += 1
                    else:
                        info['skipped_empty_tiles'] += 1
                    tile = None
                    done += 1
                    if feedback is not None:
                        feedback.setProgress(85+14*done/total)
            save()
            message = f'XYZ z={z}: {done}/{total}, {ext.upper()}={info["written_tiles"]}'
            if feedback is not None: feedback.pushInfo(message)
            else: print(message,flush=True)
        if info['written_tiles'] == 0:
            raise ValueError('No visible XYZ tiles; choose a higher zoom or check alpha')
        info['status'] = 'completed'
        save()
        return info
    except BaseException as exc:
        info.update(status='cancelled' if feedback is not None and feedback.isCanceled() else 'failed', error=str(exc))
        save()
        raise
    finally:
        src = None


if __name__ == '__main__':
    import argparse
    from osgeo import gdal, osr
    p = argparse.ArgumentParser(description='Existing CS RGBA GeoTIFF -> XYZ PNG/WebP')
    p.add_argument('--input',required=True)
    p.add_argument('--output',required=True,help='New folder, must not exist')
    p.add_argument('--min-zoom',type=int,default=12)
    p.add_argument('--max-zoom',type=int,default=18)
    p.add_argument('--max-tiles',type=int,default=100000)
    p.add_argument('--format',choices=XYZ_FORMATS,default='png')
    p.add_argument('--webp-lossy',action='store_true',
                   help='WebP選択時に非可逆(lossy)で出力する（既定は可逆/LOSSLESS=TRUE）')
    p.add_argument('--webp-quality',type=int,default=75,
                   help='--webp-lossy指定時のQUALITY(1-100、既定75、GDAL WEBPドライバのデフォルトと同じ)')
    a = p.parse_args()
    gdal.UseExceptions()
    write_xyz(a.input,a.output,dict(xyz_min_zoom=a.min_zoom,xyz_max_zoom=a.max_zoom,
              xyz_max_tiles=a.max_tiles,xyz_format=a.format,
              xyz_webp_lossless=not a.webp_lossy,xyz_webp_quality=a.webp_quality),gdal,osr)
