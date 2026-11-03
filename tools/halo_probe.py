"""Halo probe: render one item through the product's method with every spec 6.2 stage kept (WP5.7).

A diagnostic instrument, not a product feature. It renders a photo, or chosen frames of a video,
through :class:`clearwater.methods.AncutiFusionMethod` exactly as the export does (the photo
path of ``clearwater.jobs.export``: statistics measured on the block-mean proxy, render at full
resolution; the video path: a real :class:`clearwater.analysis.AnalysisEngine` run over the
whole clip, then each frame rendered from its smoothed record), keeping each intermediate of
spec 6.2 steps 1-5 and the blend:

``source``, ``compensated``, ``balanced``, ``high_pass`` (``I - G*I``, shown as ``0.5 + hp``),
``stretched`` (N{hp}), ``input1`` (gamma), ``input2`` (sharpened), the three weights of each
input (``w_laplacian_k``, ``w_saliency_k``, ``w_saturation_k``), the normalised weights
(``wbar_k``), ``naive`` (the single-scale blend ``sum_k Wbar_k * I_k``, a counterfactual, not a
product stage), ``fused`` (the multiscale fusion) and ``output`` (after the blend with the
original).

The staged render calls the product's own functions in the order ``AncutiFusionMethod.render``
calls them (the method's private ``_records``, ``_compensate`` and ``_white_balance``, then
``fusion_inputs``, ``weight_maps``, ``multiscale_fusion`` and ``blend_with_original``), and every
run checks that its ``output`` equals ``render``'s result (``render_check`` in the record): a
probe that drifted from the product would say so.

Edge-band statistics (:func:`band_statistics`). The caller marks a line across an edge (two
points in source pixels, the edge near its middle). Along the line each stage's BT.709 luma (and
each channel) is sampled at 1-pixel steps, averaged over ``2 * half_width + 1`` parallel lines.
A straight line is fitted to each outer quarter of the profile (the plateaus, so a background
gradient is not read as a band); the edge is where the profile crosses the mid level of the two
fits nearest the middle. The edge contrast ``C`` is the gap between the fits at the edge. The
**band** is the larger of the overshoot (the bright side above its fit) and the undershoot (the
dark side below its fit), between the edge and the outer quarter; ``band_ratio = band / C``. Its
width is the full width at half maximum of the deviation around its peak (``fwhm_px``) and the
run above ``threshold * C`` (``extent_px``). The deviations inward of the fits (the edge's own
ramp) are not a band and are not counted.

Attribution. The fused image is the sum over inputs ``k`` and pyramid levels ``l`` of
``collapse(G_l{Wbar_k} * L_l{I_k})`` (before the final clip). The probe samples each term on the
line and reports its deviation from its own outer-quarter fit at the band's peak: the terms add
up to the fused band (least squares is linear), so the record says which input and which
pyramid level carry it.

Command line (from the repository root)::

    uv run python tools/halo_probe.py (STEM | --source PATH) --line X0,Y0,X1,Y1 [--line ...]
        [--name NAME] [--out DIR] [--region X,Y,W,H] [--margin PX] [--half-width PX]
        [--threshold F] [--param NAME=VALUE ...] [--method ID] [--force-cpu]
        [--start S --end S] [--crop-at S ...] [--cache-dir DIR] [--replace]

``STEM`` is found in the configured footage folder (read-only; a video through
``local_config.find_footage_file``, a photo through :func:`find_footage_photo`). ``--source``
names a file elsewhere (a pack excerpt, a synthetic test image). Times are seconds from the
clip's first frame. Outputs go to ``--out`` (default ``<working folder>/wp5.7/part1/<name>``):
16-bit PNG crops of the region per stage (``<frame>-<stage>.png``), an 8-bit overview of the
source and the output with the region and lines marked, and one JSON record (``<name>.json``).
Nothing is written inside the footage folder (the runner's write check refuses it).

Exit status: 0 on success, 2 on a usage refusal, 1 on a failure.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import math
import sys
from collections.abc import Iterator, Mapping, Sequence
from datetime import UTC, datetime
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray
from PIL import Image as PILImage
from PIL import ImageDraw

import headless_export
from clearwater.analysis import AnalysisEngine
from clearwater.analysis.proxy import block_mean, proxy_factor
from clearwater.cache import DiskProxyCache, cache_key
from clearwater.core import (
    CoreBackend,
    backend_for,
    collapse_pyramid,
    gaussian_pyramid,
    laplacian_pyramid,
    pyramid_levels,
    select_backend,
    spatial_sigma,
)
from clearwater.interfaces import Image, Settings
from clearwater.io.photo import read_photo
from clearwater.io.photo.png import write_png
from clearwater.io.video import FFmpegVideoSource
from clearwater.methods import AncutiFusionMethod, available_methods
from clearwater.methods.ancuti_fusion import blend_with_original
from clearwater.methods.fusion import (
    _checked_bounds,
    _floored,
    fusion_inputs,
    high_pass,
    laplacian_weight,
    multiscale_fusion,
    normalisation_bounds,
    saliency_weight,
    saturation_weight,
    weight_maps,
)
from local_config import LocalConfigError, find_footage_file, load_local_config

type FloatArray = NDArray[np.float64]

PHOTO_EXTENSIONS = frozenset({".heic", ".heif", ".jpg", ".jpeg", ".png", ".tif", ".tiff"})
"""Lower-case suffixes :func:`find_footage_photo` accepts."""

DEFAULT_THRESHOLD = 0.10
"""The band threshold: a stage "has a band" when ``band_ratio`` exceeds it (10 % of the edge)."""

MIN_CONTRAST = 0.02
"""A line whose source contrast is below this (in [0, 1] units) is flagged ``weak_edge``: its
ratios divide by a near-zero contrast and are not read."""

OUTER_FRACTION = 0.25
"""The share of the profile at each end taken as a plateau for the linear fit."""

CHANNELS = ("Y", "R", "G", "B")
"""The profiles measured: BT.709 luma and the three channels."""

PRODUCT_STAGES = ("source", "compensated", "balanced", "input1", "input2", "fused", "output")
"""The product's image stages in pipeline order (searched for the first over the threshold)."""

IMAGE_STAGES = (
    "source",
    "compensated",
    "balanced",
    "input1",
    "input2",
    "naive",
    "fused",
    "output",
)
"""The image stages whose edge bands are measured, in pipeline order."""

_LUMA = np.array([0.2126, 0.7152, 0.0722])  # BT.709, as clearwater.core.luminance


class ProbeError(Exception):
    """A usage or input problem the command line reports with exit status 2."""


@dataclasses.dataclass(frozen=True)
class Line:
    """A profile line across an edge, in source pixels (x right, y down).

    Attributes:
        x0: Start x.
        y0: Start y.
        x1: End x.
        y1: End y.
    """

    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def length(self) -> float:
        """The line's length in pixels."""
        return math.hypot(self.x1 - self.x0, self.y1 - self.y0)


@dataclasses.dataclass(frozen=True)
class Region:
    """A crop rectangle in source pixels.

    Attributes:
        x: Left column.
        y: Top row.
        w: Width.
        h: Height.
    """

    x: int
    y: int
    w: int
    h: int


# --- profiles and band statistics ------------------------------------------------------------


def line_profile(plane: NDArray[Any], line: Line, *, half_width: int = 0) -> FloatArray:
    """Sample a 2-D array along a line at 1-pixel steps, averaged across parallel lines.

    Bilinear interpolation; the samples run from ``(x0, y0)`` to ``(x1, y1)`` inclusive,
    ``round(length) + 1`` of them; each is the mean of ``2 * half_width + 1`` samples on the
    perpendicular through it, 1 pixel apart. Coordinates outside the array are clamped to it.

    Args:
        plane: An ``(H, W)`` array.
        line: The line, in the array's pixel coordinates.
        half_width: The number of parallel lines on each side.

    Returns:
        The profile, float64.

    Raises:
        ValueError: ``plane`` is not 2-D, the line is shorter than 4 pixels, or ``half_width``
            is negative.
    """
    if plane.ndim != 2:
        raise ValueError(f"need an (H, W) array, got shape {plane.shape}")
    if half_width < 0:
        raise ValueError(f"half_width must be at least 0, got {half_width}")
    length = line.length
    if length < 4:
        raise ValueError(f"the line is {length:.1f} px long; at least 4 px is needed")
    count = round(length) + 1
    t = np.linspace(0.0, 1.0, count)
    ux, uy = (line.x1 - line.x0) / length, (line.y1 - line.y0) / length
    xs = line.x0 + t * (line.x1 - line.x0)
    ys = line.y0 + t * (line.y1 - line.y0)
    data = np.asarray(plane, dtype=np.float64)
    total = np.zeros(count)
    for offset in range(-half_width, half_width + 1):
        total += _bilinear(data, xs - offset * uy, ys + offset * ux)
    out: FloatArray = total / (2 * half_width + 1)
    return out


def _bilinear(data: FloatArray, xs: FloatArray, ys: FloatArray) -> FloatArray:
    """Bilinear samples of ``data`` at ``(xs, ys)``, clamped to the array."""
    height, width = data.shape
    xs = np.clip(xs, 0.0, width - 1.0)
    ys = np.clip(ys, 0.0, height - 1.0)
    x0 = np.minimum(np.floor(xs).astype(np.int64), width - 2) if width > 1 else np.zeros_like(xs)
    y0 = np.minimum(np.floor(ys).astype(np.int64), height - 2) if height > 1 else np.zeros_like(ys)
    x0 = np.asarray(x0, dtype=np.int64)
    y0 = np.asarray(y0, dtype=np.int64)
    x1 = np.minimum(x0 + 1, width - 1)
    y1 = np.minimum(y0 + 1, height - 1)
    fx, fy = xs - x0, ys - y0
    top = data[y0, x0] * (1 - fx) + data[y0, x1] * fx
    bottom = data[y1, x0] * (1 - fx) + data[y1, x1] * fx
    out: FloatArray = top * (1 - fy) + bottom * fy
    return out


@dataclasses.dataclass(frozen=True)
class Fits:
    """The plateau fits and the edge of one profile (shared by its attribution terms).

    Attributes:
        count: The number of samples.
        outer: The number of samples in each outer segment.
        edge: The edge's sample index.
        high_first: True when the profile's start side is the bright side.
    """

    count: int
    outer: int
    edge: int
    high_first: bool


def profile_fits(profile: FloatArray, *, outer_fraction: float = OUTER_FRACTION) -> Fits:
    """Locate the plateaus and the edge of a profile.

    Args:
        profile: The samples.
        outer_fraction: The share of samples at each end taken as a plateau.

    Returns:
        The fits' layout and the edge index: the crossing of the mid level of the two plateau
        lines nearest the middle; when the profile never crosses it inside the central part,
        the steepest point there.

    Raises:
        ValueError: The profile has fewer than 16 samples or ``outer_fraction`` is not in
            (0, 0.45].
    """
    count = profile.size
    if count < 16:
        raise ValueError(f"a profile needs at least 16 samples, got {count}")
    if not 0.0 < outer_fraction <= 0.45:
        raise ValueError(f"outer_fraction must be in (0, 0.45], got {outer_fraction}")
    outer = max(3, int(count * outer_fraction))
    first, last = _fit(profile, 0, outer), _fit(profile, count - outer, count)
    index = np.arange(count, dtype=np.float64)
    mid = (np.polyval(first, index) + np.polyval(last, index)) / 2.0
    sign = np.sign(profile - mid)
    lo, hi = outer, count - outer
    crossings = [i for i in range(lo, hi - 1) if sign[i] != 0 and sign[i] != sign[i + 1]]
    centre = (count - 1) / 2.0
    if crossings:
        edge = min(crossings, key=lambda i: abs(i + 0.5 - centre))
    else:
        edge = lo + int(np.argmax(np.abs(np.gradient(profile[lo:hi]))))
    high_first = bool(np.polyval(first, edge) >= np.polyval(last, edge))
    return Fits(count=count, outer=outer, edge=int(edge), high_first=high_first)


def _fit(profile: FloatArray, start: int, stop: int) -> FloatArray:
    """The least-squares line through ``profile[start:stop]`` (``np.polyfit`` degree 1)."""
    index = np.arange(start, stop, dtype=np.float64)
    out: FloatArray = np.polyfit(index, profile[start:stop], 1)
    return out


def deviations(profile: FloatArray, fits: Fits) -> tuple[FloatArray, FloatArray, float]:
    """Return the outward deviation of each side from its plateau line, and the edge contrast.

    Outward means away from the edge's other side: above the line on the bright side, below
    it on the dark side. The start side runs from its outer segment to the edge sample inclusive
    (the last sample before the crossing), the end side from the next sample; the rest is 0.

    Args:
        profile: The samples.
        fits: :func:`profile_fits` of the profile (or of the profile it is a term of).

    Returns:
        The bright side's outward deviation, the dark side's, and the contrast (the absolute gap
        between the two lines at the edge).
    """
    count, outer, edge = fits.count, fits.outer, fits.edge
    first, last = _fit(profile, 0, outer), _fit(profile, count - outer, count)
    index = np.arange(count, dtype=np.float64)
    line_first, line_last = np.polyval(first, index), np.polyval(last, index)
    contrast = float(abs(line_first[edge] - line_last[edge]))
    side_first = np.zeros(count, dtype=bool)
    side_first[outer : edge + 1] = True
    side_last = np.zeros(count, dtype=bool)
    side_last[edge + 1 : count - outer] = True
    dev_first = np.where(side_first, profile - line_first, 0.0)
    dev_last = np.where(side_last, profile - line_last, 0.0)
    if fits.high_first:
        return dev_first, -dev_last, contrast
    return dev_last, -dev_first, contrast


def band_statistics(
    profile: FloatArray,
    *,
    threshold: float = DEFAULT_THRESHOLD,
    fits: Fits | None = None,
) -> dict[str, Any]:
    """Measure the edge band (halo) of one profile.

    Args:
        profile: The samples, at 1-pixel steps across the edge.
        threshold: The band threshold as a fraction of the edge contrast.
        fits: The layout to use; :func:`profile_fits` of ``profile`` when None.

    Returns:
        ``edge_index``; ``contrast`` (C); ``overshoot`` and ``undershoot`` (absolute, the
        image's units) with their ratios to C; ``band`` (the larger), ``band_ratio``,
        ``band_side`` (``"bright"`` or ``"dark"``), ``peak_index``, ``peak_distance_px``
        (from the edge); ``fwhm_px``; ``extent_px`` (the run around the peak above
        ``threshold * C``; 0 when the peak is below it); ``exceeds`` (``band_ratio >
        threshold``); and ``noise`` (the RMS residual of the two plateau fits).
    """
    layout = profile_fits(profile) if fits is None else fits
    bright, dark, contrast = deviations(profile, layout)
    over, under = float(bright.max()), float(dark.max())
    side, dev = ("bright", bright) if over >= under else ("dark", dark)
    peak = int(np.argmax(dev))
    band = max(over, under, 0.0)
    ratio = band / contrast if contrast > 0 else math.inf if band > 0 else 0.0
    return {
        "edge_index": layout.edge,
        "contrast": contrast,
        "overshoot": max(over, 0.0),
        "undershoot": max(under, 0.0),
        "overshoot_ratio": max(over, 0.0) / contrast if contrast > 0 else None,
        "undershoot_ratio": max(under, 0.0) / contrast if contrast > 0 else None,
        "band": band,
        "band_ratio": ratio,
        "band_side": side,
        "peak_index": peak,
        "peak_distance_px": abs(peak - layout.edge),
        "fwhm_px": _run(dev, peak, band / 2.0) if band > 0 else 0,
        "extent_px": _run(dev, peak, threshold * contrast) if band > threshold * contrast else 0,
        "exceeds": bool(ratio > threshold),
        "noise": _noise(profile, layout),
    }


def _run(dev: FloatArray, peak: int, level: float) -> int:
    """The length of the contiguous run around ``peak`` where ``dev >= level``."""
    if dev[peak] < level:
        return 0
    lo = peak
    while lo > 0 and dev[lo - 1] >= level:
        lo -= 1
    hi = peak
    while hi < dev.size - 1 and dev[hi + 1] >= level:
        hi += 1
    return hi - lo + 1


def _noise(profile: FloatArray, fits: Fits) -> float:
    """The RMS residual of the two plateau fits."""
    count, outer = fits.count, fits.outer
    residuals = []
    for start, stop in ((0, outer), (count - outer, count)):
        index = np.arange(start, stop, dtype=np.float64)
        residuals.append(profile[start:stop] - np.polyval(_fit(profile, start, stop), index))
    return float(np.sqrt(np.mean(np.concatenate(residuals) ** 2)))


def water_contrast(profile: FloatArray, fits: Fits) -> float:
    """The signed edge contrast seen from the line's start (the open-water side).

    Args:
        profile: The samples.
        fits: The layout (the source profile's, so every stage shares one edge).

    Returns:
        The start plateau's line at the edge minus the median of the end segment (the object,
        which may be textured): positive for a dark object seen from brighter water.
    """
    line = np.polyval(_fit(profile, 0, fits.outer), fits.edge)
    return float(line - np.median(profile[fits.count - fits.outer :]))


def normalised_water_side(profile: FloatArray, fits: Fits) -> FloatArray:
    """The start side's deviation from its plateau line, over the signed contrast.

    Positive is OUTWARD (away from the object's level: a bright ring beside a dark object, a
    dark ring beside a bright one); negative is inward (a glow or spread of the object's level
    into the water). Samples outside ``[outer, edge]`` are 0.

    Args:
        profile: The samples.
        fits: The layout.

    Returns:
        The normalised deviation.
    """
    contrast = water_contrast(profile, fits)
    if contrast == 0.0:
        return np.zeros(fits.count)
    index = np.arange(fits.count, dtype=np.float64)
    deviation = profile - np.polyval(_fit(profile, 0, fits.outer), index)
    zone = np.zeros(fits.count, dtype=bool)
    zone[fits.outer : fits.edge + 1] = True
    out: FloatArray = np.where(zone, deviation / contrast, 0.0)
    return out


def water_band(
    profile: FloatArray,
    reference: FloatArray,
    fits: Fits,
    *,
    threshold: float = DEFAULT_THRESHOLD,
) -> dict[str, Any]:
    """Measure the band a stage ADDS on the open-water side, relative to the source.

    The line's start lies in open water (a plateau); its end inside the object (which may be
    textured). Each profile's start-side deviation is normalised by its own signed contrast
    (:func:`normalised_water_side`); the stage's band is its normalised deviation minus the
    reference's (the source's), so the source's own edge ramp and any in-camera halo cancel.

    Args:
        profile: The stage's samples.
        reference: The source's samples on the same line and channel.
        fits: The source profile's layout (one edge for every stage).
        threshold: The band threshold, a fraction of the contrast.

    Returns:
        ``contrast`` (signed, the stage's), ``band`` (the signed excess at the peak: positive
        outward, negative inward), ``band_ratio`` (its magnitude), ``direction``,
        ``peak_index``, ``peak_distance_px`` (from the edge), ``fwhm_px`` and ``extent_px``
        (the same-sign run around the peak at or above half the peak, and above
        ``threshold``), ``exceeds`` (``band_ratio > threshold``), ``band_abs`` (the band in
        the image's units, ``band * |contrast|``) and ``weak_edge`` (the source's contrast is
        under :data:`MIN_CONTRAST`).
    """
    excess = normalised_water_side(profile, fits) - normalised_water_side(reference, fits)
    peak = int(np.argmax(np.abs(excess)))
    band = float(excess[peak])
    signed = excess if band >= 0 else -excess
    ratio = abs(band)
    contrast = water_contrast(profile, fits)
    return {
        "contrast": contrast,
        "weak_edge": abs(water_contrast(reference, fits)) < MIN_CONTRAST,
        "band": band,
        "band_abs": band * abs(contrast),
        "band_ratio": ratio,
        "direction": "outward" if band >= 0 else "inward",
        "peak_index": peak,
        "peak_distance_px": abs(fits.edge - peak),
        "fwhm_px": _run(signed, peak, ratio / 2.0) if ratio > 0 else 0,
        "extent_px": _run(signed, peak, threshold) if ratio > threshold else 0,
        "exceeds": bool(ratio > threshold),
    }


def term_deviation(term: FloatArray, fits: Fits, peak: int) -> float:
    """Return one additive term's start-side deviation from its own plateau line at ``peak``.

    Args:
        term: The term's profile (one input's and one level's share of the fused profile).
        fits: The layout.
        peak: The sample index.

    Returns:
        ``term[peak]`` minus the term's start-plateau line there; least squares is linear, so
        the terms of a sum add up to the sum's deviation.
    """
    line = np.polyval(_fit(term, 0, fits.outer), peak)
    return float(term[peak] - line)


def luma(rgb: NDArray[Any]) -> FloatArray:
    """BT.709 luma of a host ``(H, W, 3)`` array, float64."""
    out: FloatArray = np.asarray(rgb, dtype=np.float64) @ _LUMA
    return out


def channel_planes(rgb: NDArray[Any]) -> dict[str, FloatArray]:
    """The planes :data:`CHANNELS` names, of a host ``(H, W, 3)`` array."""
    data = np.asarray(rgb, dtype=np.float64)
    return {"Y": luma(data), "R": data[..., 0], "G": data[..., 1], "B": data[..., 2]}


# --- the staged render -----------------------------------------------------------------------


def staged_render(
    method: AncutiFusionMethod,
    image: Image,
    params: Mapping[str, Any],
    statistics: Mapping[str, Mapping[str, Any]],
) -> Iterator[tuple[str, Any]]:
    """Render ``image`` as ``method.render`` does, yielding each intermediate on the device.

    The product functions are called in ``render``'s order with ``render``'s arguments. Images
    are ``(H, W, 3)`` and maps ``(H, W)``. After ``output`` it yields the attribution terms
    ``term_k<k>_l<l>``: ``collapse`` of input k's blended band at level l alone (zeros at the
    other levels), whose sum over k and l is the fused image before its clip.

    Args:
        method: The method.
        image: The image (on its backend's device).
        params: The resolved parameter values.
        statistics: Every stage's record (smoothed for video).

    Yields:
        ``(name, array)`` pairs, in pipeline order.
    """
    backend = _backend(image)
    pixels = image.pixels
    records = method._records(dict(statistics), tuple(stage.name for stage in method.stages))
    yield "source", pixels
    compensated = method._compensate(backend, pixels, params, records)
    yield "compensated", compensated
    balanced = method._white_balance(backend, compensated, params, records["white_balance"])
    del compensated
    yield "balanced", balanced
    bounds = records["fusion"]["bounds"].tolist()
    hp = high_pass(backend, balanced, sharpen_blur_fraction=params["sharpen_blur_fraction"])
    yield "high_pass", hp + np.float32(0.5)
    inputs = fusion_inputs(
        backend,
        balanced,
        gamma=params["gamma"],
        sharpen_strength=params["sharpen_strength"],
        sharpen_blur_fraction=params["sharpen_blur_fraction"],
        bounds=bounds,
    )
    low, high = _floored(*_checked_bounds(bounds))
    yield "stretched", ((hp - low) / (high - low)).clip(0.0, 1.0)  # as fusion_inputs forms N{}
    del hp, balanced
    yield "input1", inputs[0]
    yield "input2", inputs[1]
    means = records["fusion"]["saliency_means"].tolist()
    for k, fusion_input in enumerate(inputs, start=1):
        yield (
            f"w_laplacian_{k}",
            laplacian_weight(
                backend, fusion_input, laplacian_fraction=params["laplacian_fraction"]
            ),
        )
        yield (
            f"w_saliency_{k}",
            saliency_weight(
                backend,
                fusion_input,
                saliency_blur_fraction=params["saliency_blur_fraction"],
                saliency_mean=means[k - 1],
            ),
        )
        yield f"w_saturation_{k}", saturation_weight(backend, fusion_input)
    weights = weight_maps(
        backend,
        inputs,
        laplacian_fraction=params["laplacian_fraction"],
        saliency_blur_fraction=params["saliency_blur_fraction"],
        weight_delta=params["weight_delta"],
        saliency_means=means,
    )
    for k, weight in enumerate(weights, start=1):
        yield f"wbar_{k}", weight
    naive = weights[0][..., None] * inputs[0]
    for weight, fusion_input in zip(weights[1:], inputs[1:], strict=True):
        naive = naive + weight[..., None] * fusion_input
    yield "naive", naive
    del naive
    fused = multiscale_fusion(
        backend, inputs, weights, pyramid_min_level_size=params["pyramid_min_level_size"]
    )
    yield "fused", fused
    yield "output", blend_with_original(fused, pixels, params["blend_with_original"])
    del fused
    levels = pyramid_levels(inputs[0].shape, params["pyramid_min_level_size"])
    for k, (fusion_input, weight) in enumerate(zip(inputs, weights, strict=True), start=1):
        bands = [
            w[..., None] * band
            for w, band in zip(
                gaussian_pyramid(backend, weight, levels),
                laplacian_pyramid(backend, fusion_input, levels),
                strict=True,
            )
        ]
        for level, band in enumerate(bands):
            alone = [band if i == level else backend.xp.zeros_like(b) for i, b in enumerate(bands)]
            yield f"term_k{k}_l{level}", collapse_pyramid(backend, alone)


def _backend(image: Image) -> CoreBackend:
    """The core backend of an image's device."""
    return backend_for(image.device)


# --- items -----------------------------------------------------------------------------------


def find_footage_photo(stem: str, root: Path) -> Path:
    """Find the one photo with the given stem under the footage folder (read-only walk).

    Args:
        stem: The bare stem, e.g. ``"IMG_6739"`` (case-insensitive).
        root: The footage folder.

    Returns:
        The match.

    Raises:
        ProbeError: No match, or more than one.
    """
    wanted = stem.casefold()
    matches = sorted(
        path
        for path in root.rglob("*")
        if path.stem.casefold() == wanted
        and path.suffix.lower() in PHOTO_EXTENSIONS
        and path.is_file()
        and not path.is_symlink()
    )
    if len(matches) != 1:
        raise ProbeError(f"{len(matches)} photos named {stem} in the footage folder")
    return matches[0]


def resolve_parameters(method: AncutiFusionMethod, overrides: Sequence[str]) -> dict[str, Any]:
    """The method's defaults overlaid with ``NAME=VALUE`` overrides (as the export resolves them).

    Args:
        method: The method.
        overrides: ``NAME=VALUE`` strings; the value is parsed by the parameter's type.

    Returns:
        Parameter name -> value.

    Raises:
        ProbeError: An unknown name or an unparsable value.
    """
    values: dict[str, Any] = {p.name: p.default for p in method.parameters}
    kinds = {p.name: p.type for p in method.parameters}
    for item in overrides:
        name, sep, text = item.partition("=")
        if not sep or name not in kinds:
            raise ProbeError(f"--param {item!r}: not NAME=VALUE with a parameter of {method.id}")
        try:
            if kinds[name] == "int":
                values[name] = int(text)
            elif kinds[name] == "bool":
                values[name] = {"true": True, "false": False}[text.lower()]
            else:
                values[name] = float(text)
        except (ValueError, KeyError) as exc:
            raise ProbeError(f"--param {item!r}: {exc}") from exc
    return values


def photo_statistics(
    method: AncutiFusionMethod, image: Image, params: Mapping[str, Any]
) -> dict[str, Any]:
    """Measure every stage on the block-mean proxy, as the photo export does.

    Args:
        method: The method.
        image: The full-resolution image on its device.
        params: The resolved parameters.

    Returns:
        Stage name -> record.
    """
    backend = _backend(image)
    pixels = np.asarray(backend.to_host(image.pixels), dtype=np.float32)
    proxy_pixels = block_mean(pixels, proxy_factor(*pixels.shape[:2])).astype(np.float32)
    proxy = dataclasses.replace(image, pixels=backend.asarray(proxy_pixels, np.float32))
    statistics: dict[str, Any] = {}
    for stage in method.stages:
        statistics[stage.name] = method.analyze(stage.name, proxy, params, dict(statistics))
    return statistics


class _Progress:
    """A Progress that never cancels and prints every hundredth report."""

    def report(self, done: int, total: int | None, message: str) -> None:
        """Print some reports to stderr."""
        if done % 100 == 0:
            print(f"  analysis {done}/{total}: {message}", file=sys.stderr)

    def cancelled(self) -> bool:
        """Never cancel."""
        return False


# --- outputs ---------------------------------------------------------------------------------


def region_for(lines: Sequence[Line], shape: tuple[int, ...], margin: int) -> Region:
    """The bounding box of the lines, grown by ``margin`` and clamped to the image.

    Args:
        lines: The profile lines.
        shape: The image shape.
        margin: The margin in pixels.

    Returns:
        The region.
    """
    height, width = shape[0], shape[1]
    xs = [v for line in lines for v in (line.x0, line.x1)]
    ys = [v for line in lines for v in (line.y0, line.y1)]
    x0, y0 = max(0, math.floor(min(xs)) - margin), max(0, math.floor(min(ys)) - margin)
    x1, y1 = (
        min(width, math.ceil(max(xs)) + margin + 1),
        min(height, math.ceil(max(ys)) + margin + 1),
    )
    return Region(x0, y0, x1 - x0, y1 - y0)


def _crop(backend: CoreBackend, array: Any, region: Region) -> NDArray[np.float32]:
    """The region of a device array, on the host."""
    part = array[region.y : region.y + region.h, region.x : region.x + region.w]
    return np.asarray(backend.to_host(part), dtype=np.float32)


def _shifted(line: Line, region: Region) -> Line:
    """A line in the region's coordinates."""
    return Line(line.x0 - region.x, line.y0 - region.y, line.x1 - region.x, line.y1 - region.y)


def save_crop(path: Path, crop: NDArray[np.float32]) -> float:
    """Write a crop as a 16-bit PNG; a map is shown grey, scaled to its maximum when above 1.

    Args:
        path: The ``.png`` file.
        crop: An ``(h, w, 3)`` image or ``(h, w)`` map.

    Returns:
        The factor the samples were multiplied by (1 unless a map exceeded 1).
    """
    scale = 1.0
    data = crop
    if data.ndim == 2:
        peak = float(data.max()) if data.size else 0.0
        scale = 1.0 / peak if peak > 1.0 else 1.0
        data = np.repeat((data * np.float32(scale))[..., None], 3, axis=2)
    write_png(
        path,
        np.ascontiguousarray(data.clip(0.0, 1.0), dtype=np.float32),
        bit_depth=16,
        icc=None,
        exif=None,
        provenance_json=None,
    )
    return scale


def save_overview(
    path: Path, rgb: NDArray[np.float32], region: Region, lines: Sequence[Line], size: int
) -> None:
    """Write an 8-bit overview with the region boxed and the lines drawn.

    Args:
        path: The ``.png`` file.
        rgb: The host image (whole frame or the region's crop).
        region: The box to draw, in ``rgb``'s coordinates.
        lines: The lines, in ``rgb``'s coordinates.
        size: The overview's longer side in pixels (never enlarged).
    """
    picture = PILImage.fromarray((rgb.clip(0.0, 1.0) * 255.0 + 0.5).astype(np.uint8))
    scale = min(1.0, size / max(picture.size))
    if scale < 1.0:
        picture = picture.resize(
            (max(1, round(picture.width * scale)), max(1, round(picture.height * scale))),
            PILImage.Resampling.LANCZOS,
        )
    draw = ImageDraw.Draw(picture)
    box = [region.x * scale, region.y * scale, (region.x + region.w) * scale]
    box.append((region.y + region.h) * scale)
    draw.rectangle(box, outline=(255, 0, 0), width=2)
    for number, line in enumerate(lines, start=1):
        ends = [line.x0 * scale, line.y0 * scale, line.x1 * scale, line.y1 * scale]
        draw.line(ends, fill=(255, 255, 0), width=1)
        draw.text((line.x0 * scale + 3, line.y0 * scale + 3), str(number), fill=(255, 255, 0))
    picture.save(path)


# --- one frame -------------------------------------------------------------------------------


def probe_frame(
    method: AncutiFusionMethod,
    image: Image,
    params: Mapping[str, Any],
    statistics: Mapping[str, Any],
    *,
    lines: Sequence[Line],
    region: Region,
    half_width: int,
    threshold: float,
    crops: Path | None,
    prefix: str,
) -> dict[str, Any]:
    """Run the staged render of one image and measure the band on each line at each stage.

    Args:
        method: The method.
        image: The image on its device.
        params: The resolved parameters.
        statistics: The stage records used for the render.
        lines: The profile lines, in source pixels.
        region: The crop region (contains the lines).
        half_width: The profile's half width.
        threshold: The band threshold.
        crops: The folder for the 16-bit crops, or None for none.
        prefix: The crops' file-name prefix.

    Returns:
        The frame's record: per line, per stage, per channel band statistics; the attribution
        per input and level; the weight profiles; the render check; the saved crops.
    """
    backend = _backend(image)
    local = [_shifted(line, region) for line in lines]
    profiles: dict[str, list[dict[str, FloatArray]]] = {}
    maps: dict[str, list[FloatArray]] = {}
    saved: dict[str, Any] = {}
    output_full: Any = None
    shape = image.pixels.shape
    for name, array in staged_render(method, image, params, statistics):
        crop = _crop(backend, array, region)
        if name == "output":
            output_full = array
        if crops is not None and not name.startswith("term_"):
            path = crops / f"{prefix}-{name}.png"
            saved[name] = {"file": path.name, "scale": save_crop(path, crop)}
            if name in ("source", "output"):  # an 8-bit view with the lines, for reading
                whole = Region(0, 0, region.w, region.h)
                save_overview(crops / f"{prefix}-{name}-marked.png", crop, whole, local, 1400)
        if crop.ndim == 3:
            planes = channel_planes(crop)
            profiles[name] = [
                {c: line_profile(planes[c], line, half_width=half_width) for c in CHANNELS}
                for line in local
            ]
        else:
            maps[name] = [line_profile(crop, line, half_width=half_width) for line in local]
    rendered = method.render(image, params, dict(statistics)).pixels
    difference = float(abs(rendered - output_full).max())  # one device-to-host read
    del rendered, output_full
    results = []
    for index, line in enumerate(lines):
        results.append(_line_record(index, line, profiles, maps, threshold=threshold))
    return {
        "render_check_max_abs_difference": difference,
        "render_check_equal": difference == 0.0,
        "shape": list(shape),
        "lines": results,
        "crops": saved,
        "pyramid_levels": pyramid_levels(shape, params["pyramid_min_level_size"]),
    }


def _line_record(
    index: int,
    line: Line,
    profiles: Mapping[str, list[dict[str, FloatArray]]],
    maps: Mapping[str, list[FloatArray]],
    *,
    threshold: float,
) -> dict[str, Any]:
    """The record of one line: stage bands, the first stage over threshold, the attribution.

    ``water`` (the table's metric) is :func:`water_band` per stage and channel against the
    source, on the source's layout; ``two_sided`` is :func:`band_statistics` per stage and
    channel on each stage's own layout (meaningful when both sides are plateaus).
    """
    source = profiles["source"][index]
    fits = profile_fits(source["Y"])
    two_sided: dict[str, Any] = {}
    water: dict[str, Any] = {}
    for name in IMAGE_STAGES:
        per = profiles[name][index]
        two_sided[name] = {c: band_statistics(per[c], threshold=threshold) for c in CHANNELS}
        water[name] = {
            c: water_band(per[c], source[c], fits, threshold=threshold) for c in CHANNELS
        }
    first_over = next((n for n in PRODUCT_STAGES[1:] if water[n]["Y"]["exceeds"]), None)
    peak = water["fused"]["Y"]["peak_index"]
    attribution: dict[str, float] = {}
    for name, term in profiles.items():
        if name.startswith("term_"):
            attribution[name] = term_deviation(term[index]["Y"], fits, peak)
    fused_y = profiles["fused"][index]["Y"]
    edge = fits.edge
    weights = {
        name: {
            "at_edge": float(values[index][edge]),
            "plateau_start": float(np.median(values[index][: fits.outer])),
            "plateau_end": float(np.median(values[index][-fits.outer :])),
            "max": float(values[index].max()),
        }
        for name, values in maps.items()
    }
    return {
        "line": dataclasses.asdict(line),
        "length_px": line.length,
        "edge_index": edge,
        "outer_samples": fits.outer,
        "first_stage_over_threshold": first_over,
        "water": water,
        "two_sided": two_sided,
        "attribution_at_fused_peak": attribution,
        "attribution_sum": float(sum(attribution.values())),
        "fused_deviation_at_peak": term_deviation(fused_y, fits, peak),
        "weights": weights,
        "profiles_Y": {
            name: [round(float(v), 5) for v in profiles[name][index]["Y"]]
            for name in (*IMAGE_STAGES, "stretched")
        },
        "profile_wbar_2": [round(float(v), 5) for v in maps["wbar_2"][index]]
        if "wbar_2" in maps
        else None,
    }


def scale_facts(shape: tuple[int, ...], params: Mapping[str, Any]) -> dict[str, Any]:
    """The pixel scales the band widths are compared with.

    Args:
        shape: The full-resolution image shape.
        params: The resolved parameters.

    Returns:
        The sharpening sigma, the Laplacian and saliency sigmas, the pyramid depth, the
        coarsest level's short side and the source pixels one coarsest-level pixel spans.
    """
    levels = pyramid_levels(shape, params["pyramid_min_level_size"])
    short = min(shape[0], shape[1])
    size = short
    for _ in range(levels - 1):
        size = math.ceil(size / 2)
    return {
        "short_side_px": short,
        "sharpen_sigma_px": spatial_sigma(shape, params["sharpen_blur_fraction"]),
        "laplacian_sigma_px": spatial_sigma(shape, params["laplacian_fraction"]),
        "saliency_sigma_px": spatial_sigma(shape, params["saliency_blur_fraction"]),
        "pyramid_levels": levels,
        "coarsest_short_side_px": size,
        "coarsest_pixel_span_px": 2 ** (levels - 1),
    }


def add_widths_in_units(frame: dict[str, Any], scales: Mapping[str, Any]) -> None:
    """Add each stage band's widths in sharpening sigmas and coarsest-level pixels.

    Args:
        frame: A :func:`probe_frame` record (changed in place).
        scales: :func:`scale_facts` of the image.
    """
    sigma, span = scales["sharpen_sigma_px"], scales["coarsest_pixel_span_px"]
    for line in frame["lines"]:
        for stage in (*line["water"].values(), *line["two_sided"].values()):
            for stats in stage.values():
                for key in ("fwhm_px", "extent_px", "peak_distance_px"):
                    stats[key.replace("_px", "_sigma")] = stats[key] / sigma
                    stats[key.replace("_px", "_coarsest")] = stats[key] / span


# --- runs ------------------------------------------------------------------------------------


def run_photo(
    path: Path,
    method: AncutiFusionMethod,
    params: Mapping[str, Any],
    *,
    force_cpu: bool,
    options: Mapping[str, Any],
) -> dict[str, Any]:
    """Probe a photo: read, measure on the proxy, run the staged render, save the crops.

    Args:
        path: The photo.
        method: The method.
        params: The resolved parameters.
        force_cpu: Process on the CPU.
        options: ``lines``, ``region`` (or None), ``margin``, ``half_width``, ``threshold``,
            ``out``.

    Returns:
        The run record.
    """
    image, _meta = read_photo(path)
    pixels = np.asarray(image.pixels, dtype=np.float32)
    height, width = pixels.shape[:2]
    backend, reason = select_backend(Settings(force_cpu=force_cpu), height, width, method.id)
    on_device = Image(
        pixels=backend.asarray(pixels, np.float32),
        device=backend.device,
        color=image.color,
        orientation_applied=True,
    )
    statistics = photo_statistics(method, on_device, params)
    region = options["region"] or region_for(options["lines"], pixels.shape, options["margin"])
    _check_region(region, pixels.shape, options["lines"])
    frame = probe_frame(
        method,
        on_device,
        params,
        statistics,
        lines=options["lines"],
        region=region,
        half_width=options["half_width"],
        threshold=options["threshold"],
        crops=options["out"],
        prefix="photo",
    )
    scales = scale_facts(pixels.shape, params)
    add_widths_in_units(frame, scales)
    frame["full_resolution_bounds"] = _full_bounds(method, on_device, params, statistics)
    out: Path = options["out"]
    save_overview(out / "overview-source.png", pixels, region, options["lines"], 1600)
    rendered = method.render(on_device, params, statistics).pixels
    save_overview(
        out / "overview-output.png",
        np.asarray(backend.to_host(rendered), dtype=np.float32),
        region,
        options["lines"],
        1600,
    )
    del rendered
    return {
        "kind": "photo",
        "device": reason,
        "statistics": _plain(statistics),
        "scales": scales,
        "region": dataclasses.asdict(region),
        "frames": [{"time_s": None, **frame}],
    }


def _full_bounds(
    method: AncutiFusionMethod,
    image: Image,
    params: Mapping[str, Any],
    statistics: Mapping[str, Any],
) -> list[float]:
    """The N{} bounds the full-resolution image itself would give (a diagnostic only).

    The product measures them on the analysis proxy (AD-4); this measures the same percentiles
    of the full-resolution high-pass under the same compensation and white balance.
    """
    backend = _backend(image)
    records = method._records(dict(statistics), tuple(stage.name for stage in method.stages))
    compensated = method._compensate(backend, image.pixels, params, records)
    balanced = method._white_balance(backend, compensated, params, records["white_balance"])
    del compensated
    low, high = normalisation_bounds(
        backend,
        balanced,
        sharpen_blur_fraction=params["sharpen_blur_fraction"],
        normalisation_low=params["normalisation_low"],
        normalisation_high=params["normalisation_high"],
    )
    return [low, high]


def run_video(
    path: Path,
    method: AncutiFusionMethod,
    params: Mapping[str, Any],
    *,
    force_cpu: bool,
    options: Mapping[str, Any],
) -> dict[str, Any]:
    """Probe the frames of a clip between two times, from a real analysis run of the clip.

    The analysis engine is built as ``ExportEngine._analyse`` builds it (the cache in
    ``options["cache_dir"]``) and runs its job to completion; each frame between ``start``
    and ``end`` (seconds from the first frame) is decoded by the product's source and
    rendered from its smoothed record. Crops are saved for the frames nearest the
    ``crop_at`` times.

    Args:
        path: The clip.
        method: The method.
        params: The resolved parameters.
        force_cpu: Process on the CPU.
        options: As :func:`run_photo`'s, plus ``start``, ``end``, ``crop_at``, ``cache_dir``.

    Returns:
        The run record.
    """
    source = FFmpegVideoSource()
    probe = source.probe(path)
    video = probe.video
    backend, reason = select_backend(
        Settings(force_cpu=force_cpu), video.height, video.width, method.id
    )
    engine = AnalysisEngine(
        method=method,
        backend=backend,
        cache=DiskProxyCache(options["cache_dir"]),
        key=cache_key(path),
        source=source,
        probe=probe,
        params=dict(params),
        hw_decode=backend.device != "cpu",
    )
    result = engine.analysis_job()(_Progress())
    if not result.ok:
        raise RuntimeError(f"the analysis failed: {result.failure}")
    axis = sorted(int(p) for p in engine.store.axis())
    first = axis[0]
    time_base = video.time_base
    start_s, end_s = Fraction(options["start"]), Fraction(options["end"])
    chosen = [p for p in axis if start_s <= (p - first) * time_base <= end_s]
    if not chosen:
        raise ProbeError(f"no frame between {options['start']} s and {options['end']} s")
    crop_at = options["crop_at"] or [float((start_s + end_s) / 2)]
    crop_frames = {
        min(chosen, key=lambda p: abs(float((p - first) * time_base) - t)) for t in crop_at
    }
    shape = (video.height, video.width, 3)
    region = options["region"] or region_for(options["lines"], shape, options["margin"])
    _check_region(region, shape, options["lines"])
    scales = scale_facts(shape, params)
    frames = []
    out: Path = options["out"]
    stream = source.frames(probe, hw_decode=False)
    try:
        for frame in stream:
            pts = int(frame.pts_ticks)
            if pts > chosen[-1]:
                break
            if pts not in chosen:
                continue
            seconds = float((pts - first) * time_base)
            statistics = engine.smoothed_record(pts, schema_hash=engine.schema_hash)
            on_device = Image(
                pixels=backend.asarray(np.asarray(frame.pixels, dtype=np.float32), np.float32),
                device=backend.device,
                color=frame.color,
                orientation_applied=frame.orientation_applied,
            )
            keep = pts in crop_frames
            tag = f"t{seconds:08.3f}"
            record = probe_frame(
                method,
                on_device,
                params,
                statistics,
                lines=options["lines"],
                region=region,
                half_width=options["half_width"],
                threshold=options["threshold"],
                crops=out if keep else None,
                prefix=tag,
            )
            add_widths_in_units(record, scales)
            record["full_resolution_bounds"] = _full_bounds(method, on_device, params, statistics)
            if keep:
                host = np.asarray(frame.pixels, dtype=np.float32)
                save_overview(
                    out / f"{tag}-overview-source.png", host, region, options["lines"], 1600
                )
                rendered = method.render(on_device, params, statistics).pixels
                save_overview(
                    out / f"{tag}-overview-output.png",
                    np.asarray(backend.to_host(rendered), dtype=np.float32),
                    region,
                    options["lines"],
                    1600,
                )
                del rendered
            frames.append(
                {"time_s": seconds, "pts_ticks": pts, "statistics": _plain(statistics), **record}
            )
            print(f"  frame {seconds:.3f} s done", file=sys.stderr)
    finally:
        close = getattr(stream, "close", None)
        if close is not None:
            close()
    return {
        "kind": "video",
        "device": reason,
        "analysis": "AnalysisEngine.analysis_job over the whole clip (smoothing defaults)",
        "frames_in_clip": len(axis),
        "scales": scales,
        "region": dataclasses.asdict(region),
        "frames": frames,
    }


def _check_region(region: Region, shape: tuple[int, ...], lines: Sequence[Line]) -> None:
    """Refuse a region outside the image or a line outside the region."""
    if region.w < 8 or region.h < 8 or region.x < 0 or region.y < 0:
        raise ProbeError(f"region {region} is too small or negative")
    if region.x + region.w > shape[1] or region.y + region.h > shape[0]:
        raise ProbeError(f"region {region} exceeds the image {shape[1]} x {shape[0]}")
    for line in lines:
        for x, y in ((line.x0, line.y0), (line.x1, line.y1)):
            inside_x = region.x <= x <= region.x + region.w - 1
            if not (inside_x and region.y <= y <= region.y + region.h - 1):
                raise ProbeError(f"line {line} leaves the region {region}")


def _plain(value: Any) -> Any:
    """``value`` with numpy arrays and scalars turned into JSON lists and numbers."""
    if isinstance(value, Mapping):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, np.ndarray):
        return _plain(value.tolist())
    if isinstance(value, np.generic):
        return _plain(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value


# --- command line ----------------------------------------------------------------------------


def _numbers(text: str, count: int, what: str) -> list[float]:
    """Parse ``count`` comma-separated numbers."""
    parts = text.split(",")
    try:
        values = [float(p) for p in parts]
    except ValueError as exc:
        raise ProbeError(f"{what} {text!r}: {exc}") from exc
    if len(values) != count:
        raise ProbeError(f"{what} {text!r}: need {count} comma-separated numbers")
    return values


def _parser() -> argparse.ArgumentParser:
    """The command-line parser."""
    parser = argparse.ArgumentParser(prog="halo_probe", description=__doc__.splitlines()[0])
    parser.add_argument("stem", nargs="?", help="a footage file stem (photo or video)")
    parser.add_argument("--source", type=Path, help="a file outside the footage folder")
    parser.add_argument("--line", action="append", required=True, metavar="X0,Y0,X1,Y1")
    parser.add_argument("--name", help="the run name (default: the stem)")
    parser.add_argument("--out", type=Path, help="the output folder")
    parser.add_argument("--region", metavar="X,Y,W,H")
    parser.add_argument("--margin", type=int, default=64)
    parser.add_argument("--half-width", type=int, default=4)
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--param", action="append", default=[], metavar="NAME=VALUE")
    parser.add_argument("--method", default="c3")
    parser.add_argument("--force-cpu", action="store_true")
    parser.add_argument("--start", type=float, help="video: first time (s from the first frame)")
    parser.add_argument("--end", type=float, help="video: last time (s from the first frame)")
    parser.add_argument("--crop-at", type=float, action="append", default=[], metavar="S")
    parser.add_argument("--cache-dir", type=Path, help="video: the analysis cache folder")
    parser.add_argument("--replace", action="store_true", help="overwrite an existing record")
    return parser


def _options(args: argparse.Namespace) -> tuple[Path, str, Path, dict[str, Any]]:
    """Resolve the source, the run name, the output folder and the run options.

    The local configuration is read only when it is needed: for a footage stem, or for the
    default output or cache folder.
    """
    if (args.stem is None) == (args.source is None):
        raise ProbeError("give exactly one of STEM and --source")
    if args.source is not None:
        source = Path(args.source)
        if not source.is_file():
            raise ProbeError(f"--source {source.name} is not a file")
    else:
        footage_path = load_local_config().footage_path
        if Path(args.stem).suffix.lower() in PHOTO_EXTENSIONS or _is_photo_stem(
            args.stem, footage_path
        ):
            source = find_footage_photo(Path(args.stem).stem, footage_path)
        else:
            source = find_footage_file(args.stem, footage_path)
    name = args.name or source.stem
    out = args.out or load_local_config().working_path / "wp5.7" / "part1" / name
    cache_dir = args.cache_dir or load_local_config().working_path / "wp5.7" / "cache"
    footage = headless_export.configured_footage_folder()
    if footage is not None:
        for target in (out, cache_dir):
            refusal = headless_export.write_target_refusal(target, footage)
            if refusal is not None:
                raise ProbeError(refusal)
    lines = [Line(*_numbers(text, 4, "--line")) for text in args.line]
    region = None
    if args.region is not None:
        x, y, w, h = (int(v) for v in _numbers(args.region, 4, "--region"))
        region = Region(x, y, w, h)
    options: dict[str, Any] = {
        "lines": lines,
        "region": region,
        "margin": args.margin,
        "half_width": args.half_width,
        "threshold": args.threshold,
        "out": out,
        "start": args.start,
        "end": args.end,
        "crop_at": args.crop_at,
        "cache_dir": cache_dir,
    }
    return source, name, out, options


def _is_photo_stem(stem: str, root: Path) -> bool:
    """True when the footage folder holds a photo with this stem."""
    wanted = stem.casefold()
    return any(
        p.stem.casefold() == wanted and p.suffix.lower() in PHOTO_EXTENSIONS
        for p in root.rglob("*")
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run the probe from the command line.

    Args:
        argv: The arguments; ``sys.argv[1:]`` when None.

    Returns:
        The exit status: 0 done, 1 failed, 2 refused.
    """
    args = _parser().parse_args(argv)
    try:
        source, name, out, options = _options(args)
        methods = available_methods()
        method = methods.get(args.method)
        if not isinstance(method, AncutiFusionMethod):
            raise ProbeError(f"unknown method {args.method!r}")
        params = resolve_parameters(method, args.param)
        record_path = out / f"{name}.json"
        if record_path.exists() and not args.replace:
            raise ProbeError(f"{record_path.name} exists; pass --replace to overwrite")
        is_video = source.suffix.lower() in {".mp4", ".mov"}
        if is_video and (args.start is None or args.end is None):
            raise ProbeError("a video needs --start and --end")
    except (ProbeError, LocalConfigError) as exc:
        print(f"halo_probe: {exc}", file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)
    began = datetime.now(UTC)
    try:
        run = (run_video if is_video else run_photo)(
            source, method, params, force_cpu=args.force_cpu, options=options
        )
    except ProbeError as exc:
        print(f"halo_probe: {exc}", file=sys.stderr)
        return 2
    record = {
        "schema": 1,
        "tool": "halo_probe",
        "name": name,
        "source": source.name,
        "method": method.id,
        "parameters": params,
        "overrides": list(args.param),
        "threshold": options["threshold"],
        "half_width": options["half_width"],
        "outer_fraction": OUTER_FRACTION,
        "started": began.isoformat(),
        "finished": datetime.now(UTC).isoformat(),
        **run,
    }
    record_path.write_text(json.dumps(_plain(record), indent=1), encoding="utf-8")
    print(summary(record))
    return 0


def summary(record: Mapping[str, Any]) -> str:
    """One text line per frame and line: the first stage over the threshold and the bands.

    Args:
        record: A run record.

    Returns:
        The lines, ASCII.
    """
    rows = []
    for frame in record["frames"]:
        when = "photo" if frame["time_s"] is None else f"{frame['time_s']:.3f}s"
        for number, line in enumerate(frame["lines"], start=1):
            bands = " ".join(
                f"{stage}={line['water'][stage]['Y']['band']:+.2f}" for stage in IMAGE_STAGES
            )
            fused = line["water"]["fused"]["Y"]
            rows.append(
                f"{record['name']} {when} line{number}: first>{record['threshold']:.2f}="
                f"{line['first_stage_over_threshold']} fused fwhm={fused['fwhm_px']}px "
                f"({fused['fwhm_sigma']:.2f} sigma) {fused['direction']} "
                f"abs={fused['band_abs']:+.3f}"
                f"{' WEAK-EDGE' if fused['weak_edge'] else ''} | {bands} | "
                f"render_check={frame['render_check_equal']}"
            )
    return "\n".join(rows)


if __name__ == "__main__":
    sys.exit(main())
