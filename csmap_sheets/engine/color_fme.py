"""FME manual colour model for CS Map Sheets.

This module only handles colour lookup, weighted composition and optional
per-band stretch. Terrain derivatives are calculated by ``pipeline.py``.
"""
from copy import deepcopy
import math

import numpy as np


FME_COLORS = {
    "elevation_low": [36, 36, 36],
    "elevation_high": [246, 246, 246],
    "slope_a_low": [247, 213, 213],
    "slope_a_high": [134, 28, 33],
    "slope_b_low": [246, 246, 246],
    "slope_b_high": [36, 36, 36],
    "curvature_a_low": [42, 95, 131],
    "curvature_a_high": [208, 223, 230],
    "curvature_b_low": [50, 96, 207],
    "curvature_b_mid": [255, 254, 190],
    "curvature_b_high": [198, 72, 59],
}

FME_WEIGHTS = {
    "elevation": 0.125,
    "slope_a": 0.25,
    "slope_b": 0.25,
    "curvature_a": 0.125,
    "curvature_b": 0.25,
}

NAGANO_REFERENCE_RANGES = [[65.0, 234.0], [57.0, 229.0], [66.0, 216.0]]

FME_DEFAULTS = {
    "colors": FME_COLORS,
    "weights": FME_WEIGHTS,
    "stretch_mode": "none",
    "stretch_ranges": NAGANO_REFERENCE_RANGES,
}


def _rgb(value, name):
    if (not isinstance(value, (list, tuple)) or len(value) != 3 or
            any(type(v) is not int or not 0 <= v <= 255 for v in value)):
        raise ValueError(f"fme.colors.{name} requires three integer RGB values in 0..255")
    return list(value)


def validate_fme_settings(settings=None):
    """Return a complete, JSON-serialisable FME colour specification."""
    if settings is None:
        settings = {}
    if not isinstance(settings, dict):
        raise ValueError("fme must be an object")
    allowed = {"colors", "weights", "stretch_mode", "stretch_ranges"}
    unknown = set(settings) - allowed
    if unknown:
        raise ValueError(f"Unknown fme keys: {sorted(unknown)}")

    result = deepcopy(FME_DEFAULTS)
    colors = settings.get("colors", {})
    if not isinstance(colors, dict):
        raise ValueError("fme.colors must be an object")
    unknown = set(colors) - set(FME_COLORS)
    if unknown:
        raise ValueError(f"Unknown fme.colors keys: {sorted(unknown)}")
    result["colors"].update({key: _rgb(value, key) for key, value in colors.items()})
    for key, value in result["colors"].items():
        result["colors"][key] = _rgb(value, key)

    weights = settings.get("weights", {})
    if not isinstance(weights, dict):
        raise ValueError("fme.weights must be an object")
    unknown = set(weights) - set(FME_WEIGHTS)
    if unknown:
        raise ValueError(f"Unknown fme.weights keys: {sorted(unknown)}")
    result["weights"].update(weights)
    for key, value in result["weights"].items():
        if (not isinstance(value, (int, float)) or isinstance(value, bool) or
                not math.isfinite(value) or value < 0):
            raise ValueError(f"fme.weights.{key} must be a finite nonnegative number")
        result["weights"][key] = float(value)
    if not math.isclose(sum(result["weights"].values()), 1.0, rel_tol=0, abs_tol=1e-12):
        raise ValueError("fme.weights must sum to 1.0")

    mode = settings.get("stretch_mode", result["stretch_mode"])
    if mode not in ("none", "nagano_reference", "custom"):
        raise ValueError("fme.stretch_mode must be none, nagano_reference or custom")
    result["stretch_mode"] = mode
    ranges = settings.get("stretch_ranges", result["stretch_ranges"])
    if (not isinstance(ranges, (list, tuple)) or len(ranges) != 3 or
            any(not isinstance(pair, (list, tuple)) or len(pair) != 2 for pair in ranges)):
        raise ValueError("fme.stretch_ranges requires R, G and B [lower, upper] pairs")
    checked = []
    for band, pair in zip("RGB", ranges):
        lo, hi = pair
        if (not isinstance(lo, (int, float)) or isinstance(lo, bool) or
                not isinstance(hi, (int, float)) or isinstance(hi, bool) or
                not math.isfinite(lo) or not math.isfinite(hi) or lo >= hi):
            raise ValueError(f"fme.stretch_ranges {band} lower must be less than upper")
        checked.append([float(lo), float(hi)])
    result["stretch_ranges"] = checked
    return result


def lut2(low, high):
    """Return a 256-entry float LUT with exact endpoints."""
    return np.linspace(np.asarray(_rgb(low, "low"), dtype=np.float64),
                       np.asarray(_rgb(high, "high"), dtype=np.float64), 256)


def lut3(low, middle, high):
    """Return a 256-entry float LUT; indices 127 and 128 are the middle colour."""
    low = np.asarray(_rgb(low, "low"), dtype=np.float64)
    middle = np.asarray(_rgb(middle, "middle"), dtype=np.float64)
    high = np.asarray(_rgb(high, "high"), dtype=np.float64)
    left = np.linspace(low, middle, 128)
    right = np.linspace(middle, high, 128)
    return np.concatenate((left, right), axis=0)


def normalise_index(values, lower, upper):
    """Clip numeric values to a normalisation range and return 0..255 indices."""
    if not math.isfinite(lower) or not math.isfinite(upper) or lower >= upper:
        raise ValueError("normalisation lower must be less than upper")
    scaled = np.clip((np.asarray(values, dtype=np.float64) - lower) / (upper - lower), 0, 1)
    return np.rint(scaled * 255).astype(np.uint8)


def apply_stretch(rgb, mode, ranges):
    """Apply an optional per-band linear stretch and clip to 0..255."""
    if mode == "none":
        return np.clip(np.asarray(rgb, dtype=np.float64), 0, 255)
    selected = NAGANO_REFERENCE_RANGES if mode == "nagano_reference" else ranges
    out = np.asarray(rgb, dtype=np.float64).copy()
    for band, (lo, hi) in enumerate(selected):
        out[..., band] = (out[..., band] - lo) * 255.0 / (hi - lo)
    return np.clip(out, 0, 255)


def render_fme(raw, slope, curvature, elevation_range, slope_range,
               curvature_range, settings=None):
    """Render the five independent LUT layers and return float RGB."""
    spec = validate_fme_settings(settings)
    colors = spec["colors"]
    elevation_i = normalise_index(raw, *elevation_range)
    slope_i = normalise_index(slope, *slope_range)
    curvature_i = normalise_index(curvature, *curvature_range)

    layers = {
        "elevation": lut2(colors["elevation_low"], colors["elevation_high"])[elevation_i],
        "slope_a": lut2(colors["slope_a_low"], colors["slope_a_high"])[slope_i],
        "slope_b": lut2(colors["slope_b_low"], colors["slope_b_high"])[slope_i],
        "curvature_a": lut2(colors["curvature_a_low"], colors["curvature_a_high"])[curvature_i],
        "curvature_b": lut3(colors["curvature_b_low"], colors["curvature_b_mid"],
                            colors["curvature_b_high"])[curvature_i],
    }
    rgb = sum(layers[name] * spec["weights"][name] for name in FME_WEIGHTS)
    return apply_stretch(rgb, spec["stretch_mode"], spec["stretch_ranges"])


def rendering_record(elevation_range, slope_range, curvature_range, settings=None):
    """Return the complete resolved colour record stored in run.json."""
    spec = validate_fme_settings(settings)
    return {
        "mode_id": "fme_manual",
        "normalization": {
            "elevation_m": list(elevation_range),
            "slope_degrees": list(slope_range),
            "curvature_1_per_m": list(curvature_range),
        },
        "colors": spec["colors"],
        "weights": spec["weights"],
        "stretch": {
            "mode": spec["stretch_mode"],
            "ranges_rgb": (deepcopy(NAGANO_REFERENCE_RANGES)
                           if spec["stretch_mode"] == "nagano_reference"
                           else spec["stretch_ranges"]),
            "nagano_reference_is_optional_empirical_value": True,
        },
        "curvature_sign": "negative=concave/valley/blue; zero=yellow in curvature_b; positive=convex/ridge/red",
    }
