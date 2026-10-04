#!/usr/bin/env python3
"""DEM mosaic -> independent CS-style RGBA relief -> Japanese map-sheet GeoTIFFs.

Read README_ja.md. This is NOT a pixel-identical reproduction of Nagano CSMap.
QGIS Processing adaptation; no external Python process.
"""
import argparse
import glob
import json
import math
from pathlib import Path
import sys
import traceback

import numpy as np
from .filters import gaussian_filter, minimum_filter, BACKEND
from .map_sheets import dimensions, cut_sheets, intersecting_sheets
from .progress import report, check_cancel, gdal_progress, CancelledError
from .color_fme import render_fme, rendering_record as fme_rendering_record, validate_fme_settings

VERSION = "0.11.0"
PLUGIN_TITLE_JA = "図郭対応CS立体図作成プラグイン（CS Map Sheets）"


def version_banner():
    """画面の説明欄と実行ログの先頭に出す版表示。VERSIONから組み立てるため、
    版を上げるときに画面側の文言を書き換える必要はない。"""
    return f"{PLUGIN_TITLE_JA} v{VERSION}"
from .xyz_tiles import DEFAULTS as XYZ_DEFAULTS, validate_xyz, write_xyz, precheck_xyz_tile_count

from .input_sources import DEFAULTS as INPUT_DEFAULTS, validate_input, discover, prepare_inputs

NODATA = -999999.0
COLOR_DEFAULTS = dict(
    valley_rgb=[74, 140, 198], ridge_rgb=[192, 119, 71], neutral_rgb=[248, 247, 242],
    elevation_low_rgb=[222, 236, 244], elevation_high_rgb=[250, 242, 223],
    curvature_strength=1.0, elevation_mix=0.15, slope_darkness=0.55,
    brightness=1.0, saturation=1.0, contrast=1.0, gamma=1.0)

def color_settings(settings=None):
    if settings is None:
        settings = {}
    if not isinstance(settings, dict):
        raise ValueError("color must be an object")
    if set(settings)-set(COLOR_DEFAULTS):
        raise ValueError(f"Unknown color keys: {sorted(set(settings)-set(COLOR_DEFAULTS))}")
    result = {**COLOR_DEFAULTS, **settings}
    for key, value in result.items():
        if key.endswith('_rgb'):
            if not isinstance(value, (list, tuple)) or len(value) != 3 or any(
                not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 255 for v in value):
                raise ValueError(f"color.{key} requires three integer RGB values in 0..255")
        else:
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
                raise ValueError(f"color.{key} must be finite")
            low, high = ((0, 1) if key in ('curvature_strength','elevation_mix','slope_darkness')
                         else (0.1, 5) if key == 'gamma' else (0, 3))
            if not low <= value <= high:
                raise ValueError(f"color.{key} must be within {low}..{high}")
    return result


SLOPE_ALGORITHMS = ('horn', 'central_difference')
SLOPE_ALGORITHM_NAMES = {'horn': 'Horn法', 'central_difference': '中央差分法'}


def missing_slope_algorithm_notice(saved, chosen):
    """Warning text when a loaded profile predates slope_algorithm (v0.9.4 and
    earlier), else None. Those profiles were produced with central differences,
    so silently applying the new Horn default would change colours unnoticed."""
    if 'slope_algorithm' in saved:
        return None
    return ('この設定プロファイルには傾斜計算方式（slope_algorithm）の指定がないため、'
            f'画面で選択中の{SLOPE_ALGORITHM_NAMES[chosen]}を使います。v0.9.4以前の出力を'
            '再現する場合は「傾斜計算のアルゴリズム」で中央差分法を選んでください。')


def slope_gradients(raw, cell, slope_algorithm='horn'):
    """Return (dz/dx, dz/dy) in the same units as raw/cell for the selected method.

    Both methods need only a 1-cell halo (callers already supply
    ceil(4*sigma_m/cell)+1 >= 1), so this does not change the halo requirement
    documented on relief(). Sign convention is whatever falls out of the
    np.roll shifts below; only the magnitude (via np.hypot in relief()) is
    used downstream, so the sign is not significant here.

    - 'central_difference': simple 2-point central difference (v0.9.4 and
      earlier behaviour; kept as a selectable option for continuity with
      prior outputs / third-party comparisons).
    - 'horn' (default from v0.10.0): Horn (1981) 3x3 weighted method, the
      same formula used by most GIS slope tools (e.g. ArcGIS, GDAL
      gdaldem/QGIS "Slope"), which is less sensitive to single-cell noise
      than the 2-point method.
    """
    if slope_algorithm not in SLOPE_ALGORITHMS:
        raise ValueError(f"slope_algorithm must be one of {SLOPE_ALGORITHMS}")
    if slope_algorithm == 'central_difference':
        dx = (np.roll(raw, -1, 1) - np.roll(raw, 1, 1)) / (2 * cell)
        dy = (np.roll(raw, -1, 0) - np.roll(raw, 1, 0)) / (2 * cell)
        return dx, dy
    # Horn (1981): 3x3 neighbourhood, row index increasing southward.
    n = np.roll(raw, 1, 0);   s = np.roll(raw, -1, 0)
    w = np.roll(raw, 1, 1);   e = np.roll(raw, -1, 1)
    nw = np.roll(n, 1, 1);    ne = np.roll(n, -1, 1)
    sw = np.roll(s, 1, 1);    se = np.roll(s, -1, 1)
    dx = ((ne + 2 * e + se) - (nw + 2 * w + sw)) / (8 * cell)
    dy = ((sw + 2 * s + se) - (nw + 2 * n + ne)) / (8 * cell)
    return dx, dy


SIGMA_UNITS = ('m', 'px')


def gaussian_sigma(c):
    """Return (sigma in calculation-grid pixels, kernel radius in pixels) for a config.

    v0.12.0: the Gaussian sigma can be given as a ground distance (``sigma_unit='m'``,
    ``sigma_m``) or as a number of calculation-grid pixels (``sigma_unit='px'``,
    ``sigma_px``). The calculation grid is the reprojected DEM grid of ``cell_size``
    (always square here) on which relief() smooths -- not the source grid or XYZ pixels.
    The 'm' branch keeps the exact float expressions used up to v0.11.0 so that
    existing settings give bit-identical radii and results.
    """
    if c.get('sigma_unit', 'm') == 'px':
        sigma_px = c['sigma_px']
        return sigma_px, math.ceil(4 * sigma_px)
    return c['sigma_m'] / c['cell_size'], math.ceil(4 * c['sigma_m'] / c['cell_size'])


def smoothing_record(c):
    """Smoothing conditions for logs and run.json (setting and effective values kept apart)."""
    sigma_px, radius = gaussian_sigma(c)
    unit = c.get('sigma_unit', 'm')
    return {
        'sigma_unit': unit,
        'sigma_setting': c['sigma_px'] if unit == 'px' else c['sigma_m'],
        'cell_size_m': c['cell_size'],
        'effective_sigma_m': sigma_px * c['cell_size'] if unit == 'px' else c['sigma_m'],
        'effective_sigma_px': sigma_px,
        'kernel_radius_px': radius if sigma_px > 0 else 0,
        'kernel_size_px': 2 * radius + 1 if sigma_px > 0 else 0,
    }


def smoothing_summary(c):
    r = smoothing_record(c)
    if r['effective_sigma_px'] == 0:
        return ('曲率用平滑化: なし（σ=0）／指定方式 '
                + ('地上距離（m）' if r['sigma_unit'] == 'm' else '計算格子の画素数（px）'))
    head = (f"地上距離 {r['sigma_setting']:g} m" if r['sigma_unit'] == 'm'
            else f"計算格子の画素数 {r['sigma_setting']:g} px")
    return (f"曲率用平滑化: 指定 {head}／計算格子 {r['cell_size_m']:g} m／"
            f"実効σ {r['effective_sigma_m']:g} m = {r['effective_sigma_px']:g} px／"
            f"カーネル {r['kernel_size_px']}×{r['kernel_size_px']} 画素")


def relief(z, valid, cell, sigma_m, curvature_limit, slope_max, elev_range, color=None,
           render_mode='independent_v040', fme=None, slope_algorithm='horn', sigma_px=None):
    """Return RGBA, slope degrees and negative-Laplacian proxy (1/m).

    All samples touching a missing value within the full processing support
    are transparent. Callers must supply ceil(4*sigma_m/cell)+1 halo cells
    (>=1 cell, which both supported slope_algorithm values need).
    ``sigma_px`` (v0.12.0) gives sigma directly in grid pixels and then takes
    precedence over ``sigma_m``; the halo is ceil(4*sigma_px)+1 in that case.
    """
    render_mode = {'legacy': 'independent_v040', 'fme': 'fme_manual'}.get(render_mode, render_mode)
    if render_mode not in ('independent_v040', 'fme_manual'):
        raise ValueError("render_mode must be independent_v040 or fme_manual")
    if slope_algorithm not in SLOPE_ALGORITHMS:
        raise ValueError(f"slope_algorithm must be one of {SLOPE_ALGORITHMS}")
    tone = color_settings(color) if render_mode == 'independent_v040' else None
    if sigma_px is None:
        radius = math.ceil(4 * sigma_m / cell)
        sigma_grid = sigma_m / cell
    else:
        radius = math.ceil(4 * sigma_px)
        sigma_grid = sigma_px
    halo = radius + 1
    valid = valid & np.isfinite(z)
    raw = np.where(valid, z, 0).astype(np.float64)
    smooth = (gaussian_filter(raw, sigma=sigma_grid, radius=radius,
                              mode="constant", cval=0)
              if sigma_grid > 0 else raw.copy())
    dx, dy = slope_gradients(raw, cell, slope_algorithm)
    slope = np.degrees(np.arctan(np.hypot(dx, dy)))
    curvature = -(np.roll(smooth, -1, 1) + np.roll(smooth, 1, 1)
                  + np.roll(smooth, -1, 0) + np.roll(smooth, 1, 0)
                  - 4 * smooth) / cell**2
    safe = minimum_filter(valid.astype(np.uint8), size=2 * halo + 1,
                          mode="constant", cval=0).astype(bool)
    if render_mode == 'fme_manual':
        rgb = render_fme(raw, slope, curvature, elev_range, [0.0, slope_max],
                         [-curvature_limit, curvature_limit], fme)
    else:
        # Convex = positive = warm brown; concave = negative = blue.
        t = np.clip(curvature / curvature_limit, -1, 1)
        neutral = np.array(tone['neutral_rgb'], dtype=float)
        warm = np.array(tone['ridge_rgb'], dtype=float)
        cool = np.array(tone['valley_rgb'], dtype=float)
        target = np.where((t >= 0)[..., None], warm, cool)
        rgb = neutral + tone['curvature_strength'] * np.abs(t)[..., None] * (target - neutral)
        emin, emax = elev_range
        h = np.clip((raw - emin) / (emax - emin), 0, 1)
        low = np.array(tone['elevation_low_rgb'], dtype=float)
        high = np.array(tone['elevation_high_rgb'], dtype=float)
        tint = low + h[..., None] * (high-low)
        mix = tone['elevation_mix']
        rgb = (1-mix) * rgb + mix * tint
        shade = 1 - tone['slope_darkness'] * np.clip(slope / slope_max, 0, 1)
        rgb *= shade[..., None]
        if tone['saturation'] != 1:
            gray = np.sum(rgb * np.array([.2126, .7152, .0722]), axis=2, keepdims=True)
            rgb = gray + tone['saturation']*(rgb-gray)
        if tone['contrast'] != 1:
            rgb = 127.5 + tone['contrast']*(rgb-127.5)
        rgb = np.clip(rgb*tone['brightness'], 0, 255)
        if tone['gamma'] != 1:
            rgb = 255 * (rgb/255)**(1/tone['gamma'])
    rgb = np.rint(rgb).astype(np.uint8)
    rgb[~safe] = 0
    rgba = np.concatenate([rgb, (safe.astype(np.uint8) * 255)[..., None]], axis=2)
    return rgba, slope, curvature


def read_config(path):
    return validate_config(json.loads(path.read_text(encoding="utf-8-sig")), path.parent)


def mosaic_message(c, input_report):
    """Log line for the mosaic stage.

    For GSI DEMs the prepared inputs are groups of tiles sharing one pixel grid
    (normalize_gsi_groups), not individual files, so say so: "Mosaic: 7 DEM files"
    for 100 XML tiles was read as files being dropped (user report, 2026-10-03).
    """
    count = len(c['inputs'])
    sources = len(input_report.get('sources', [])) if isinstance(input_report, dict) else 0
    if c.get('input_type') == 'gsi' and sources:
        return (f"Mosaic: {count} grid groups from {sources} GSI DEM tiles "
                "(tiles sharing a pixel grid are merged into one group)")
    return f"Mosaic: {count} DEM files"


def validate_config(c, base_dir, feedback=None):
    base_dir = Path(base_dir)
    provided = set(c)
    # NOTE: this bare default is independent_v040 (legacy)'s own value, matching pre-FME v0.4
    # behaviour exactly. It was previously left at 0.03 (the FME-mode figure) here, so a config
    # or external profile that picked independent_v040 while omitting curvature_limit would
    # silently get 0.03 instead of the documented v0.4-compatible 0.05 (found by comparison
    # against a parallel implementation, 2026-09-24; the QGIS UI itself always forces 0.05 for
    # its built-in legacy presets, so this only bit bare configs/external profiles).
    defaults = dict(sigma_m=3.0, curvature_limit=0.05, slope_max=60.0,
                    elevation_range=[0, 3000], elevation_range_auto=False,
                    elevation_range_margin=50.0, block_size=512, sheet_level=5000,
                    max_sheets=100000, max_sheet_pixels=100000000, compression="DEFLATE",
                    max_pixels=1000000000, source_nodata=None,
                    confirm_elevation_metres=False, color={}, render_mode=None, fme={},
                    # v0.9.3: 図郭タイル出力に加えて、全域CS方式画像をVRTだけでなく
                    # 単体のGeoTIFFとしても書き出すかどうか（ユーザー要望、
                    # 2026-09-30。VRTは個々の図郭タイルへの参照のため、成果物を
                    # 単独で移動・配布する用途にはGeoTIFFの方が扱いやすい）。
                    merged_geotiff_enabled=True,
                    # v0.10.0: 傾斜計算アルゴリズムの選択（ユーザー要望、2026-10-02）。
                    # 既定はHorn法（3x3加重、ArcGIS/gdaldem等の標準的な傾斜算出法と同じ
                    # 式。1セルノイズに対して中央差分法より頑健）。中央差分法は
                    # v0.9.4以前の挙動（2点差分）との比較・互換のために選択可能とする。
                    slope_algorithm='horn',
                    # v0.12.0: Gaussian σの指定方式（ユーザー承認の改訂依頼、2026-10-03）。
                    # 'm'＝地上距離（sigma_mを使う。従来どおり・既定）、'px'＝計算格子の
                    # 画素数（sigma_pxを使う）。方式ごとの値を別々に保持し、方式を切り替えても
                    # 同じ数値を別の単位として読み替えない。方式の指定がない旧設定はm。
                    sigma_unit='m', sigma_px=3.0)
    defaults.update(XYZ_DEFAULTS)
    defaults.update(INPUT_DEFAULTS)
    unknown = set(c) - set(defaults) - {"inputs", "output_dir", "target_crs", "cell_size", "plane_zone", "color_model"}
    if unknown:
        raise ValueError(f"Unknown configuration keys: {sorted(unknown)}")
    c = {**defaults, **c}
    validate_input(c)
    validate_xyz(c)
    legacy_mode = c.pop('color_model', None)
    if c['render_mode'] is None:
        c['render_mode'] = {'legacy': 'independent_v040', 'fme': 'fme_manual'}.get(
            legacy_mode, 'independent_v040')
    if c['render_mode'] not in ('independent_v040', 'fme_manual'):
        raise ValueError('render_mode must be independent_v040 or fme_manual')
    if c['render_mode'] == 'fme_manual':
        if 'curvature_limit' not in provided:
            # FME manual (別紙3) states curvature as "-10~+10" (10m DEM: -5~+5), no unit given.
            # Confirmed (2026-09-24, by reading s2_...fmw directly) equal to ±0.1 [1/m] in this
            # plugin's own metric: the workspace's RasterConvolver curvature kernel uses
            # KERNEL_WEIGHTS="0 -1 0 -1 4 -1 0 -1 0" (same negative-Laplacian shape as relief()'s
            # `curvature`) with KERNEL_DIVISOR="$(CELL_SIZE)**2 * 0.01" - i.e. FME's own curvature
            # values are 100x this plugin's 1/m metric, so its "±10" is this plugin's "±0.1".
            c['curvature_limit'] = 0.1
        if 'elevation_range' not in provided:
            c['elevation_range'] = [200.0, 2000.0]
        if legacy_mode == 'fme' and 'fme' not in provided:
            old = c['color']
            c['fme'] = {'colors': {
                'elevation_low': old.get('elevation_low_rgb', [36, 36, 36]),
                'elevation_high': old.get('elevation_high_rgb', [246, 246, 246]),
                'curvature_b_low': old.get('valley_rgb', [50, 96, 207]),
                'curvature_b_mid': old.get('neutral_rgb', [255, 254, 190]),
                'curvature_b_high': old.get('ridge_rgb', [198, 72, 59]),
            }, 'stretch_mode': 'nagano_reference'}
    c['color'] = color_settings(c['color'])
    c['fme'] = validate_fme_settings(c['fme'])
    for name in ("inputs", "output_dir", "target_crs", "cell_size"):
        if name not in c:
            raise ValueError(f"Missing configuration: {name}")
    if not c["confirm_elevation_metres"]:
        raise ValueError("Confirm all source elevations use metres and the same vertical datum; then set confirm_elevation_metres=true")
    if not isinstance(c["merged_geotiff_enabled"], bool):
        raise ValueError("merged_geotiff_enabled must be boolean")
    for key in ("cell_size", "curvature_limit", "slope_max"):
        if not math.isfinite(c[key]) or c[key] <= 0:
            raise ValueError(f"{key} must be finite and positive")
    if c["sigma_unit"] not in SIGMA_UNITS:
        raise ValueError(f"sigma_unit must be one of {SIGMA_UNITS}")
    for key in ("sigma_m", "sigma_px"):
        if isinstance(c[key], bool) or not isinstance(c[key], (int, float)) \
                or not math.isfinite(c[key]) or c[key] < 0:
            raise ValueError(f"{key} must be finite and nonnegative")
    if not 0 < c["slope_max"] <= 90:
        raise ValueError("slope_max must be <= 90 degrees")
    if c["slope_algorithm"] not in SLOPE_ALGORITHMS:
        raise ValueError(f"slope_algorithm must be one of {SLOPE_ALGORITHMS}")
    if c.get("elevation_range_auto"):
        margin = c.get("elevation_range_margin", 50.0)
        if not math.isfinite(margin) or margin < 0:
            raise ValueError("elevation_range_margin must be finite and non-negative")
        # elevation_range itself is a placeholder here; run() overwrites it after
        # scanning the projected mosaic, so the strict increasing/finite check below
        # does not apply while auto-detection is enabled.
    else:
        er = c["elevation_range"]
        if len(er) != 2 or not all(math.isfinite(x) for x in er) or er[0] >= er[1]:
            raise ValueError("elevation_range must contain two increasing finite values")
    for key in ("block_size", "max_pixels", "max_sheets", "max_sheet_pixels"):
        if not isinstance(c[key], int) or c[key] <= 0:
            raise ValueError(f"{key} must be a positive integer")
    if not 64 <= c["block_size"] <= 2048:
        raise ValueError("block_size:64..2048")
    if c.get("plane_zone") is not None and (type(c["plane_zone"]) is not int or not 1 <= c["plane_zone"] <= 19):
        raise ValueError("plane_zone must be omitted/auto or an integer in 1..19")
    width, height = dimensions(c["sheet_level"])
    if any(abs(v/c["cell_size"]-round(v/c["cell_size"])) > 1e-6 for v in (width, height)):
        raise ValueError("cell_size must divide sheet width and height exactly")
    if round(width/c["cell_size"])*round(height/c["cell_size"]) > c["max_sheet_pixels"]:
        raise ValueError("Sheet dimensions exceed max_sheet_pixels")
    if c["compression"] not in ("DEFLATE", "NONE"):
        raise ValueError("compression must be DEFLATE or NONE")
    if gaussian_sigma(c)[1] > 512:
        raise ValueError("Gaussian radius >512 cells; reduce sigma or use coarser DEM")
    nd = c["source_nodata"]
    if nd is not None and not math.isfinite(nd):
        raise ValueError("source_nodata override must be a finite number")
    files = discover(c["inputs"], base_dir, c, feedback=feedback)
    p = Path(c["output_dir"]).expanduser()
    out = (base_dir / p if not p.is_absolute() else p).resolve()
    if out.exists():
        raise ValueError(f"Output directory already exists; choose a new directory: {out}")
    c["inputs"] = files
    c["output_dir"] = str(out)
    return c


# GSI Notice: https://www.gsi.go.jp/LAW/heimencho.html
# 平面直角座標系 第I系～第XIX系の原点(緯度,経度)。zoneはこの並びの1-based index。
JPR_ZONE_ORIGINS = [(33,129.5), (33,131), (36,132+10/60), (33,133.5), (36,134+20/60),
           (36,136), (36,137+10/60), (36,138.5), (36,139+50/60), (40,140+50/60),
           (44,140.25), (44,142.25), (44,144.25), (26,142), (26,127.5),
           (26,124), (26,131), (20,136), (26,154)]


def _jpr_zone_of(srs):
    """srs(osr.SpatialReference、投影済み)が平面直角座標系第I～XIX系のいずれかに
    一致すればその番号(1-19)を、一致しなければNoneを返す。投影法・原点緯度経度・
    縮尺係数・偽東距/偽北距の一致でのみ判定し、権威コード(EPSG番号)には依存しない。"""
    if srs is None or not srs.IsProjected() or srs.GetAttrValue("PROJECTION") != "Transverse_Mercator":
        return None
    for number, (lat0, lon0) in enumerate(JPR_ZONE_ORIGINS, 1):
        if all(abs(srs.GetProjParm(parm)-expected) <= 1e-8 for parm, expected in (
                ("latitude_of_origin",lat0),("central_meridian",lon0),
                ("scale_factor",.9999),("false_easting",0),("false_northing",0))):
            return number
    return None


def infer_target_crs_from_raster(path, gdal, feedback=None):
    """v0.9.3: 出力CRSが未指定のとき、先頭の入力ラスターファイルの実際のCRSを読み取り、
    平面直角座標系第I～XIX系のいずれかと一致すればそのWKTを返す（ユーザー要望、
    2026-09-30）。一致しない場合・ファイルを開けない場合・CRSが定義されていない場合は、
    その理由を示す短い日本語文字列と共に(None, reason)を返す（v0.9.3追記、
    2026-09-30：TIFF＋TFW(ワールドファイル)はTFW自体に座標系情報を持たないため、
    このケースを「単に一致しなかった」場合と区別してユーザーに案内できるようにした。
    ユーザー報告：「森林航空レーザ成果」モードでTIFF＋TFW入力を使う際、この違いが
    分かりにくいという指摘を受けた）。呼び出し側（algorithm.py）がNone時に明確な
    エラーで停止する。ラスター入力（mode=='raster'）にのみ適用し、text/lidar/forest
    等の非GeoTIFF系入力には適用しない（それらのCRSはINPUT_CRSで別途明示されるため）。
    未確認事項：本関数はこのモジュールのGDAL/OSR非搭載環境では未検証（テストは
    GDAL利用可能な環境でのみ実行される）。

    戻り値：(wkt, None) で成功、(None, reason) で失敗。"""
    check_cancel(feedback)
    ds = gdal.Open(str(path))
    if ds is None:
        return None, 'ファイルを開けませんでした'
    srs = ds.GetSpatialRef()
    wkt = ds.GetProjection()
    ds = None
    if srs is None or not wkt:
        return None, ('この入力にはCRS(座標系)情報がありません。TIFF＋TFW(ワールドファイル)'
                       'はTFW自体に位置合わせ情報しか持たず、CRS情報は持ちません')
    if _jpr_zone_of(srs) is None:
        return None, '入力のCRSが平面直角座標系第I～XIX系のいずれとも一致しません'
    return wkt, None


def check_sources(c, gdal, osr, feedback=None):
    target = osr.SpatialReference()
    target.SetFromUserInput(c["target_crs"])
    if not target.IsProjected() or abs(target.GetLinearUnits() - 1) > 1e-9:
        raise ValueError("target_crs must be a projected CRS with metre units")
    if target.GetAuthorityCode(None) in ("3857", "3395"):
        raise ValueError("Use a suitable local projected CRS, not Web/World Mercator, for terrain derivatives")
    if target.IsCompound() or target.GetAttrValue("PROJECTION") != "Transverse_Mercator":
        raise ValueError("target_crs must be a two-dimensional Japan Plane Rectangular CRS")
    zone = _jpr_zone_of(target)
    if zone is None:
        raise ValueError("Selected CRS is not one of Japan Plane Rectangular zones I-XIX")
    if c.get("plane_zone") is not None and c["plane_zone"] != zone:
        raise ValueError(f"target_crs is zone {zone}, but legacy plane_zone={c['plane_zone']}")
    c["plane_zone"] = zone
    lat, lon = JPR_ZONE_ORIGINS[zone-1]
    for parm, expected in (("latitude_of_origin", lat), ("central_meridian", lon),
                           ("scale_factor", .9999), ("false_easting", 0), ("false_northing", 0)):
        if abs(target.GetProjParm(parm)-expected) > 1e-8:
            raise ValueError(f"target_crs does not match automatically detected plane zone {zone}: {parm}")
    base_srs, base_gt = None, None
    records = []
    for path in c["inputs"]:
        check_cancel(feedback)
        ds = gdal.Open(path)
        if ds is None or ds.RasterCount != 1:
            raise ValueError(f"Expected a single-band DEM: {path}")
        srs = ds.GetSpatialRef()
        gt = ds.GetGeoTransform()
        if srs is None or not ds.GetProjection():
            raise ValueError(f"Missing CRS: {path}")
        if srs.IsCompound():
            raise ValueError(f"Normalize compound/vertical CRS explicitly before input: {path}")
        if abs(gt[2]) > 1e-12 or abs(gt[4]) > 1e-12 or gt[1] <= 0 or gt[5] >= 0:
            raise ValueError(f"Rotated/south-up raster: normalize first: {path}")
        if base_srs is not None:
            if not srs.IsSame(base_srs):
                raise ValueError("Mixed source CRSs: reproject onto one common grid before this pipeline")
            if not np.allclose([gt[1], gt[5]], [base_gt[1], base_gt[5]], rtol=1e-7, atol=0):
                raise ValueError("Mixed source resolutions: normalize onto one common grid first")
            offsets = [(gt[0]-base_gt[0])/gt[1], (gt[3]-base_gt[3])/gt[5]]
            if any(abs(v-round(v)) > 1e-5 for v in offsets):
                raise ValueError(f"Source grids are not aligned: {path}")
        else:
            base_srs, base_gt = srs.Clone(), gt
        band = ds.GetRasterBand(1)
        if band.GetScale() not in (None, 1) or band.GetOffset() not in (None, 0):
            raise ValueError(f"Apply band scale/offset to actual elevation values first: {path}")
        if band.GetNoDataValue() is None and c["source_nodata"] is None:
            raise ValueError(f"No NoData metadata: set source_nodata after checking data: {path}")
        stat = Path(path).stat()
        records.append(dict(path=path, size=stat.st_size, mtime_ns=stat.st_mtime_ns,
                            nodata=repr(band.GetNoDataValue()), width=ds.RasterXSize,
                            height=ds.RasterYSize, crs=ds.GetProjection(), transform=gt))
        ds = None
    return records


def make_relief(dem_path, output_path, c, gdal, feedback=None):
    src = gdal.Open(str(dem_path))
    w, h = src.RasterXSize, src.RasterYSize
    dst = gdal.GetDriverByName("GTiff").Create(str(output_path), w, h, 4,
        gdal.GDT_Byte, options=["TILED=YES", "COMPRESS=DEFLATE", "BIGTIFF=IF_SAFER",
                               "PHOTOMETRIC=RGB", "ALPHA=YES"])
    dst.SetProjection(src.GetProjection())
    dst.SetGeoTransform(src.GetGeoTransform())
    for i, ci in enumerate((gdal.GCI_RedBand, gdal.GCI_GreenBand,
                             gdal.GCI_BlueBand, gdal.GCI_AlphaBand), 1):
        dst.GetRasterBand(i).SetColorInterpretation(ci)
    dst.SetMetadataItem("METHOD", c.get("render_mode", "independent_v040"))
    dst.SetMetadataItem("SETTINGS", json.dumps(c, ensure_ascii=True))
    sigma_px, radius = gaussian_sigma(c)
    halo = radius+1
    block = c["block_size"]
    band = src.GetRasterBand(1)
    valid_count = 0
    for y in range(0, h, block):
        for x in range(0, w, block):
            check_cancel(feedback)
            bw, bh = min(block, w-x), min(block, h-y)
            x0, y0 = max(0, x-halo), max(0, y-halo)
            x1, y1 = min(w, x+bw+halo), min(h, y+bh+halo)
            a = band.ReadAsArray(x0, y0, x1-x0, y1-y0).astype(np.float64)
            valid = np.isfinite(a) & (a != NODATA)
            rgba, _, _ = relief(a, valid, c["cell_size"], c["sigma_m"],
                c["curvature_limit"], c["slope_max"], c["elevation_range"], c.get('color'),
                c.get('render_mode', 'independent_v040'), c.get('fme'),
                c.get('slope_algorithm', 'horn'),
                sigma_px if c.get('sigma_unit', 'm') == 'px' else None)
            tile = rgba[y-y0:y-y0+bh, x-x0:x-x0+bw]
            valid_count += int(np.count_nonzero(tile[:, :, 3]))
            for b in range(4):
                dst.GetRasterBand(b+1).WriteArray(tile[:, :, b], x, y)
        report(feedback, f"CS relief: {min(y+block,h)}/{h} rows", 25+50*min(y+block,h)/h)
    dst.FlushCache()
    dst = src = None
    if valid_count == 0:
        raise ValueError("No valid relief pixels: check DEM coverage, NoData and smoothing radius")
    return valid_count


def render_sheets(projected_path, out, c, gdal, ogr, osr, feedback=None):
    """Render directly from a virtual province mosaic, one map sheet at a time."""
    src=gdal.Open(str(projected_path))
    gt=src.GetGeoTransform()
    bounds=(gt[0],gt[3]+gt[5]*src.RasterYSize,
            gt[0]+gt[1]*src.RasterXSize,gt[3])
    candidates=list(intersecting_sheets(bounds,c['plane_zone'],c['sheet_level'],c['max_sheets']))
    sheets_dir=out/'sheets';work=out/'sheet_work'
    sheets_dir.mkdir(exist_ok=False);work.mkdir(exist_ok=False)
    index=ogr.GetDriverByName('GPKG').CreateDataSource(str(out/'sheet_index.gpkg'))
    srs=src.GetSpatialRef().Clone();srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    layer=index.CreateLayer('sheets',srs,ogr.wkbPolygon)
    for name,kind in (('sheet_code',ogr.OFTString),('plane_zone',ogr.OFTInteger),
        ('sheet_level',ogr.OFTInteger),('file',ogr.OFTString),('cell_m',ogr.OFTReal),
        ('valid_px',ogr.OFTInteger64)):
        layer.CreateField(ogr.FieldDefn(name,kind))
    width_m,height_m=dimensions(c['sheet_level'])
    width,height=round(width_m/c['cell_size']),round(height_m/c['cell_size'])
    halo=gaussian_sigma(c)[1]+1
    written=[];skipped=0;valid_total=0
    for number,sheet in enumerate(candidates,1):
        check_cancel(feedback)
        dem_path=work/(sheet.code+'_dem.tif');relief_path=work/(sheet.code+'_rgba.tif')
        buffered=(sheet.west-halo*c['cell_size'],sheet.south-halo*c['cell_size'],
                  sheet.east+halo*c['cell_size'],sheet.north+halo*c['cell_size'])
        dem=gdal.Warp(str(dem_path),src,format='GTiff',dstSRS=c['target_crs'],
            outputBounds=buffered,width=width+2*halo,height=height+2*halo,
            outputType=gdal.GDT_Float32,resampleAlg='bilinear',srcNodata=NODATA,
            dstNodata=NODATA,errorThreshold=0,
            creationOptions=['TILED=YES','COMPRESS=DEFLATE','PREDICTOR=3','BIGTIFF=IF_SAFER'])
        if dem is None:raise RuntimeError('Map-sheet DEM warp failed: '+sheet.code)
        band=dem.GetRasterBand(1);coverage=0
        block=c['block_size']
        for y in range(halo,halo+height,block):
            for x in range(halo,halo+width,block):
                a=band.ReadAsArray(x,y,min(block,halo+width-x),min(block,halo+height-y))
                coverage+=int(np.count_nonzero(np.isfinite(a)&(a!=NODATA)))
        dem=None
        if coverage == 0:
            dem_path.unlink(missing_ok=True);skipped+=1;continue
        make_relief(dem_path,relief_path,c,gdal,feedback)
        dest=sheets_dir/(sheet.code+'.tif')
        rgba=gdal.Open(str(relief_path))
        tile=gdal.Translate(str(dest),rgba,srcWin=[halo,halo,width,height],format='GTiff',
            creationOptions=['TILED=YES',f"COMPRESS={c['compression']}",'BIGTIFF=IF_SAFER',
                             'PHOTOMETRIC=RGB','ALPHA=YES'])
        if tile is None:raise RuntimeError('Map-sheet CS write failed: '+sheet.code)
        tile.SetMetadataItem('SHEET_CODE',sheet.code);tile.SetMetadataItem('SHEET_LEVEL',str(c['sheet_level']))
        tile.SetMetadataItem('PLANE_ZONE',str(c['plane_zone']));tile.FlushCache();tile=None;rgba=None
        ds=gdal.Open(str(dest));alpha=ds.GetRasterBand(4);count=0
        for y in range(0,height,block):
            for x in range(0,width,block):
                a=alpha.ReadAsArray(x,y,min(block,width-x),min(block,height-y));count+=int(np.count_nonzero(a))
        ds=None
        dem_path.unlink(missing_ok=True);relief_path.unlink(missing_ok=True)
        if count == 0:
            dest.unlink(missing_ok=True);skipped+=1;continue
        tfw=(c['cell_size'],0,0,-c['cell_size'],sheet.west+c['cell_size']/2,sheet.north-c['cell_size']/2)
        dest.with_suffix('.tfw').write_text('\n'.join(f'{v:.12f}' for v in tfw)+'\n',encoding='ascii')
        ring=ogr.Geometry(ogr.wkbLinearRing)
        for e,n in ((sheet.west,sheet.south),(sheet.east,sheet.south),(sheet.east,sheet.north),
                    (sheet.west,sheet.north),(sheet.west,sheet.south)):ring.AddPoint_2D(e,n)
        polygon=ogr.Geometry(ogr.wkbPolygon);polygon.AddGeometry(ring)
        feature=ogr.Feature(layer.GetLayerDefn())
        for key,value in dict(sheet_code=sheet.code,plane_zone=c['plane_zone'],sheet_level=c['sheet_level'],
            file='sheets/'+dest.name,cell_m=c['cell_size'],valid_px=count).items():feature.SetField(key,value)
        feature.SetGeometry(polygon)
        if layer.CreateFeature(feature)!=0:raise RuntimeError('Failed to write sheet index')
        feature=None;written.append(str(dest));valid_total+=count
        report(feedback,f"Sheet {number}/{len(candidates)}: {sheet.code}",10+70*number/len(candidates))
    layer=index=src=None
    try:work.rmdir()
    except OSError:pass
    if not written:raise ValueError('No nonempty sheets produced')
    mosaic=out/'cs_relief.vrt'
    vrt=gdal.BuildVRT(str(mosaic),written,resolution='highest',strict=True)
    if vrt is None:raise RuntimeError('CS sheet VRT build failed')
    vrt.FlushCache();vrt=None
    return str(mosaic),dict(written=len(written),skipped_empty=skipped),valid_total


def rendering_settings(c):
    """Build the complete, serialisable rendering section for run.json."""
    if c.get("render_mode", "independent_v040") == "fme_manual":
        rendering = fme_rendering_record(c["elevation_range"], [0.0, c["slope_max"]],
                                         [-c["curvature_limit"], c["curvature_limit"]], c["fme"])
    else:
        rendering = {
            "mode_id": "independent_v040",
            "normalization": {
                "elevation_m": list(c["elevation_range"]),
                "slope_degrees": [0.0, c["slope_max"]],
                "curvature_1_per_m": [-c["curvature_limit"], c["curvature_limit"]],
            },
            "colors_and_display_adjustments": c["color"],
            "curvature_sign": "negative=concave/valley/blue; positive=convex/ridge/warm",
        }
    slope_algorithm = c.get("slope_algorithm", "horn")
    rendering["terrain_calculation"] = {
        "curvature": "negative five-point Laplacian of Gaussian-smoothed elevation (1/m)",
        "slope": {
            "horn": "Horn (1981) 3x3 weighted method on unsmoothed elevation (degrees)",
            "central_difference": "2-point central differences of unsmoothed elevation (degrees)",
        }[slope_algorithm],
        "slope_algorithm": slope_algorithm,
        # v0.12.0: smoothing_sigma_m is the sigma in metres actually used (equal to the
        # setting in 'm' mode, as before); "smoothing" keeps the setting and the
        # effective values separately so a px setting is never recorded as metres.
        "smoothing_sigma_m": (c["sigma_m"] if c.get("sigma_unit", "m") == "m"
                              else smoothing_record(c)["effective_sigma_m"]),
        "filter_backend": BACKEND,
        "input_type": c.get("input_type", "raster"),
    }
    if "cell_size" in c:
        rendering["terrain_calculation"]["smoothing"] = smoothing_record(c)
    return rendering


def detect_elevation_range(raster_ds, margin, feedback=None):
    """Compute [min-margin, max+margin] elevation from a projected mosaic dataset.

    Uses GDAL's approximate statistics (fast, sampled) rather than an exact scan,
    since this only needs to be accurate enough to set a display normalization
    range, not for scientific measurement. Returns (used_range, detected_raw_range).
    """
    band = raster_ds.GetRasterBand(1)
    try:
        dmin, dmax, _mean, _std = band.ComputeStatistics(1)
    except RuntimeError as exc:
        raise RuntimeError("標高の自動検出に失敗しました（統計情報を取得できません）。"
                            "有効なDEMセルが1つもない可能性があります。") from exc
    if not (math.isfinite(dmin) and math.isfinite(dmax)) or dmin >= dmax:
        raise RuntimeError("標高の自動検出に失敗しました（有効な標高範囲が見つかりません）。"
                            "「標高色の下限/上限」欄に手動で値を入力してください。")
    lo, hi = dmin - margin, dmax + margin
    report(feedback, f"標高色の範囲を自動検出: 入力値 {dmin:.1f}〜{dmax:.1f}m "
                      f"→ 余白{margin:g}m込みで {lo:.1f}〜{hi:.1f}mを使用")
    return [lo, hi], [dmin, dmax]


def run(c, feedback=None):
    from osgeo import gdal, osr, ogr
    check_cancel(feedback)
    # API floor; no gdal2tiles dependency in the map-sheet workflow.
    ver = int(gdal.VersionInfo("VERSION_NUM"))
    if ver < 3060000:
        raise RuntimeError("GDAL >=3.6 is required. The supplied environment requires GDAL >=3.10.")
    # Validate the target projection before doing any input conversion.
    check_sources({**c, "inputs": []}, gdal, osr, feedback)
    records = []
    out = Path(c["output_dir"])
    out.mkdir(parents=True, exist_ok=False)
    rendering = rendering_settings(c)
    manifest = dict(status="running", plugin_version=VERSION, algorithm_version=VERSION,
        rendering=rendering, settings=c,
        sources=records, python=sys.version, numpy=np.__version__, filter_backend=BACKEND,
        gdal=gdal.VersionInfo("RELEASE_NAME"), overlap_priority="later valid input wins")
    def save():
        (out/"run.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    save()
    try:
        manifest["stage"] = "input_conversion"
        save()
        c, input_report = prepare_inputs(c, out/"input", gdal, osr, feedback)
        manifest["input_report"] = input_report
        manifest["sources"] = check_sources(c, gdal, osr, feedback)
        manifest["stage"] = "mosaic"
        save()
        report(feedback, smoothing_summary(c), 0)
        report(feedback, mosaic_message(c, input_report), 0)
        kwargs = dict(resolution="highest", VRTNodata=NODATA, strict=True)
        if c["source_nodata"] is not None:
            kwargs["srcNodata"] = c["source_nodata"]
        vrt = gdal.BuildVRT(str(out/"source_mosaic.vrt"), c["inputs"], **kwargs)
        if vrt is None:
            raise RuntimeError("BuildVRT failed")
        vrt.FlushCache()
        projected_path=out/'projected_dem.vrt'
        projected = gdal.Warp(str(projected_path), vrt, format="VRT", dstSRS=c["target_crs"],
            xRes=c["cell_size"], yRes=c["cell_size"], targetAlignedPixels=True,
            resampleAlg="bilinear", srcNodata=NODATA, dstNodata=NODATA,
            outputType=gdal.GDT_Float32, errorThreshold=0)
        check_cancel(feedback)
        if projected is None:
            raise RuntimeError("DEMの再投影に失敗しました。GDALログを確認してください。")
        if c.get("elevation_range_auto"):
            detected_range, raw_range = detect_elevation_range(
                projected, c.get("elevation_range_margin", 50.0), feedback)
            c["elevation_range"] = detected_range
            manifest["elevation_range_detected"] = raw_range
            manifest["elevation_range_margin_m"] = c.get("elevation_range_margin", 50.0)
            manifest["rendering"] = rendering_settings(c)
            save()
        gt = projected.GetGeoTransform()
        bounds = (gt[0], gt[3]+gt[5]*projected.RasterYSize,
                  gt[0]+gt[1]*projected.RasterXSize, gt[3])
        # Validate domain and sheet count before materializing a large mosaic.
        manifest["candidate_sheets"] = sum(1 for _ in intersecting_sheets(bounds,
            c["plane_zone"], c["sheet_level"], c["max_sheets"]))
        # v0.9.4: CS立体図の計算(render_sheets、最重量の処理)を始める前に、
        # XYZ候補タイル数が上限を超えないか事前検証する（フェイルファスト）。
        # 超過が判明していれば、1時間超かかることもある本計算を無駄に走らせない。
        manifest["xyz_candidate_tiles_precheck"] = precheck_xyz_tile_count(
            str(projected_path), c, gdal, osr)
        save()
        report(feedback, f"Projected mosaic: {projected.RasterXSize} x {projected.RasterYSize}")
        projected.FlushCache();projected=vrt=None
        manifest['stage']='sheet_streaming';save()
        cs_mosaic,manifest['sheets'],manifest['valid_relief_pixels']=render_sheets(
            projected_path,out,c,gdal,ogr,osr,feedback)
        if c.get("merged_geotiff_enabled", True):
            check_cancel(feedback)
            manifest["stage"] = "merged_geotiff"
            save()
            merged_path = out / "cs_relief_merged.tif"
            mosaic_ds = gdal.Open(cs_mosaic)
            if mosaic_ds is None:
                raise RuntimeError("結合GeoTIFF書き出し用のVRTを開けませんでした: " + cs_mosaic)
            merged = gdal.Translate(str(merged_path), mosaic_ds, format="GTiff",
                creationOptions=["TILED=YES", f"COMPRESS={c['compression']}", "BIGTIFF=IF_SAFER",
                                 "PHOTOMETRIC=RGB", "ALPHA=YES"])
            mosaic_ds = None
            if merged is None:
                raise RuntimeError("結合GeoTIFFの書き出しに失敗しました: " + str(merged_path))
            merged.FlushCache(); merged = None
            manifest["cs_merged_geotiff"] = "cs_relief_merged.tif"
            report(feedback, f"Merged GeoTIFF: {merged_path}")
        else:
            manifest["cs_merged_geotiff"] = None
        if c.get("xyz_enabled", True):
            manifest["stage"] = "xyz"
            save()
            manifest["xyz"] = write_xyz(cs_mosaic, out/"xyz", c, gdal, osr, feedback)
        manifest["stage"] = "finished"
        manifest["status"] = "completed"
        manifest["sheet_template"] = "sheets/{sheet_code}.tif"
        manifest["cs_mosaic"] = "cs_relief.vrt"
        save()
        report(feedback, f"COMPLETED: {out}", 100)
    except BaseException as exc:
        manifest["status"] = "cancelled" if (isinstance(exc, CancelledError) or (feedback and feedback.isCanceled())) else "failed"
        manifest["error"] = str(exc)
        save()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args()
    run(read_config(args.config.resolve()))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
