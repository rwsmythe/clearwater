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

Profiles. The caller marks a line across an edge (two points in source pixels, the edge near
its middle), starting in open water and ending inside the object. Along the line each stage's
BT.709 luma (and each channel) is sampled ``round(length) + 1`` times, ``length /
round(length)`` pixels apart (:func:`sample_spacing`), each sample the mean of ``2 * half_width
+ 1`` parallel lines; the whole strip (and its bilinear support) must lie inside the sampled
array, never clamped to it. A straight line is fitted to each outer quarter of the source's
profile (the plateaus, so a background gradient is not read as a band); the edge is where the
profile crosses the mid level of the two fits nearest the middle. Every stage is measured on the
source's layout (one edge, one zone).

The band (:func:`water_band`, the table's metric) is what a stage ADDS beyond the source's
water-side profile, over ONE common contrast. On the water side (from the end of the start
plateau to the edge) the stage's OUTWARD overshoot is its rise past its own water-plateau line
away from the object (above the line beside a darker object, below it beside a brighter one),
zero where it does not pass the line; the source's overshoot is measured the same way. The
excess at each sample is the stage's overshoot minus the source's, divided by the SOURCE's
signed water contrast ``C`` (the start plateau's line at the edge minus the median of the end
segment); the band is the largest excess (0 when none is positive). A monotonic remap (gamma,
white balance, a change of either plateau's level) of a source with no overshoot moves no sample
past its own water plateau, so it reports no band (a source that already overshoots is the
pointwise-stage case below); an inward spread of the object's level into the water is not a
band either. A band QUALIFIES only when the edge is not weak (``|C| >= MIN_CONTRAST``) and at least
``MIN_SUPPORT_SAMPLES`` consecutive samples around its peak each exceed both the threshold and
``NOISE_FACTOR`` times the water-side uncertainty there (:func:`water_uncertainty` of the stage
and of the source in quadrature, over ``|C|``: the plateau fit's residual noise plus the error
of its line extrapolated to that sample, with an AR(1) effective sample count). Each
stage's verdict is ``band`` (qualifies), ``undecided`` (a weak edge, or over the threshold
without qualifying) or ``none``; :func:`first_stage` names the first product stage whose band
qualifies, ``undecided`` when none does but one is undecided, None otherwise. Widths are the
interpolated crossings of half the peak (``fwhm_px``) and of the threshold (``extent_px``), in
pixels at the line's sample spacing. :func:`band_statistics` is a two-sided diagnostic (each
side against its own plateau line, over the stage's own contrast), not the table's metric.

The pointwise stages (CHARC's ruling S1, step 2B; :func:`stage_band`). White balance and input 1
are per-pixel tone remaps; a source that already overshoots (in-camera sharpening) passes its
overshoot through them scaled by the remap's local gain, which the face-value excess above
would charge to the stage. So each pointwise stage subtracts the overshoot of the SOURCE
REMAPPED through that stage's own operation instead of the source's: for ``balanced`` the
source white-balanced with the gains the render used (``AncutiFusionMethod._white_balance``
on the source, from the same record: the gray-world gains of that frame, smoothed for video,
after the strength and the D99 clamp; never re-estimated); for ``input1`` that remapped source
raised to the render's ``gamma`` and clipped as ``fusion_inputs`` forms input 1, so the two
remaps chain as the product chains them. :func:`staged_render` yields the two references
(``remap_balanced``, ``remap_input1``) after ``output``. Everything else is unchanged: the common
denominator stays the SOURCE's signed contrast ``C`` (and the weak-edge test with it), the
uncertainty is the stage's and the remapped reference's in quadrature, and compensation (3C is
local: Gaussian means of the chroma under a smoothed mask), input 2, ``naive``, fused and output
are read at face value against the source. Each luma and channel band records its
``reference`` (``"remapped_source"`` or ``"source"``).

The attributed stage (CHARC's ruling S2; :func:`attributed_stage`). Beside the first qualifying
stage, each line names the input that carries its qualifying FUSED band: the input whose terms
carry the larger share of the band at its peak (:func:`attribute_band`'s ``per_input``).
``"none"`` when the fused verdict is ``none``; ``"undecided"`` when it is ``undecided``, when
the two shares are within :data:`ATTRIBUTION_TIE` of each other (a tie), or when neither share
is positive (the inputs carry none of it).

Attribution (:func:`attribute_band`). The product's fused image is ``clip(prefused)`` with
``prefused`` the sum over inputs ``k`` and pyramid levels ``l`` of ``collapse(G_l{Wbar_k} *
L_l{I_k})``. Because ``sum_k Wbar_k = 1``, the source decomposes the same way:
``S = sum_k,l collapse(G_l{Wbar_k} * L_l{S})``. At the fused band's peak the added band is
``sign(C) * dev(fused) - overshoot(source)`` over ``|C|`` (``dev`` = the deviation from the
profile's own water-plateau line, linear in the profile). The probe splits it exactly into
per-input, per-level terms ``sign(C) * (dev(term_kl) - [s] dev(srcterm_kl)) / |C|`` (``[s]`` = 1
when the source is outward at the peak, so its overshoot is the one subtracted; 0 otherwise)
plus the clip's share ``sign(C) * (dev(fused) - dev(prefused)) / |C|``; the record carries the
terms, their sums per input and per level, the clip's share and the residual against the
detected band. The terms are computed pre-clip and the clip's share is reported, never folded
into a term.

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
Writes are confined: ``--name`` must be a plain file stem (no separator, drive, ``:`` or
``..``, and not a Windows device name such as ``NUL`` or ``COM1``, on every system); the output
and cache folders, and the run's three sibling folders below, must resolve inside ``<working
folder>/wp5.7`` (the output strictly below it) and pass the runner's footage write check; a run
that breaks either is refused before anything is written.

Publication (Reviewer A round 1, fixes 1 and 2). No write opens a file that existed before the
run: every output file is created inside a FRESH staging folder, ``.<out>.staging-<stamp>``
beside the output folder (``<stamp>`` the run's UTC start, to the microsecond), made with an
exclusive ``mkdir`` that fails if anything holds that name; the record is opened in exclusive
mode too. Only a successful run publishes, by renaming the staging folder to ``<out>``. An
existing ``<out>`` (or a link of that name) is refused unless ``--replace``; with ``--replace``
it is renamed aside, before the publish, to the kept sibling ``<out>.replaced-<stamp>`` (the
tool never deletes or writes into a published folder, so a link planted in it is never written
through). A run that fails or is refused after the staging folder was made publishes nothing
and leaves ``<out>`` untouched: an empty staging folder is removed (``os.rmdir``, which removes
nothing else); one holding partial output is kept, renamed ``.<out>.failed-<stamp>``. When
either publish rename fails or is interrupted after ``<out>`` was moved aside, the old
publication is renamed back (for any exception, which is then re-raised once the staging folder
is retired as above); if that also fails, the run exits 1 naming both failures and the kept
folder that holds the old publication. The
analysis cache (``--cache-dir``) is the product's ``DiskProxyCache``, reused across runs by
design, and keeps its own write discipline; it is refused when it equals, lies inside or
contains ``<out>``, or lies inside any of ``<out>``'s sibling folders (``<out>.*`` or
``.<out>.*``), so the analysis never writes into a publication or a staging tree. Limits (out of
the instrument's envelope, a seat-run tool on a single-user laptop): confinement is checked at
start-up and holds against pre-existing files and links; it does not pin the ancestors against
a concurrent process that swaps a directory for a junction during the run, nor against one that
plants a link in the fresh staging folder; and on POSIX a rename can replace an existing EMPTY
directory, so the publish-time collision refusals are Windows guarantees.

A run FAILS (exit 1, no record) when the staged render's output differs from the product's
``render`` by any amount, when ``clip(prefused)`` differs from the staged ``fused``, or when the
video decode did not deliver every selected frame. The video analysis is given the clip's
expected frame count (:func:`clearwater.jobs.export.expected_frames`), as the export gives it.

Exit status: 0 on success, 2 on a usage refusal, 1 on a failure (nothing published).
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import math
import os
import sys
from collections.abc import Iterator, Mapping, Sequence
from datetime import UTC, datetime
from fractions import Fraction
from pathlib import Path, PurePath
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
from clearwater.jobs.export import expected_frames
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
ratios divide by a near-zero contrast, so its bands are ``undecided``, never a stage."""

MIN_SUPPORT_SAMPLES = 3
"""A band qualifies only when at least this many consecutive samples (about 1 px apart) around
its peak stay above the qualifying level: a one- or two-sample excursion is not a band."""

NOISE_FACTOR = 3.0
"""A band qualifies only above this many times the water-side uncertainty
(:func:`water_uncertainty` of the stage and of the source, in quadrature, over the source
contrast) at each sample of its support."""

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

POINTWISE_REFERENCES = {"balanced": "remap_balanced", "input1": "remap_input1"}
"""The pointwise stages (ruling S1) -> the staged array each is measured against: the source
remapped through the stage's own operation (:func:`staged_render`). Every other stage is
measured against the source (face value)."""

ATTRIBUTION_TIE = 1e-4
"""Two inputs' shares of a fused band (in units of the source contrast) closer than this are a
tie (:func:`attributed_stage`): the order of float32 sums alone moves a share by about this."""

WINDOWS_DEVICE_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}
    | {f"{port}{digit}" for port in ("COM", "LPT") for digit in "123456789\u00b9\u00b2\u00b3"}
)
"""Names Windows maps to a device whatever their extension (``NUL.json`` is ``NUL``):
:func:`_check_name` refuses them on every system (spec N1: one portable rule)."""

_LUMA = np.array([0.2126, 0.7152, 0.0722])  # BT.709, as clearwater.core.luminance


class ProbeError(Exception):
    """A usage or input problem the command line reports with exit status 2."""


class ProbeFailedError(Exception):
    """A run whose measurement cannot be trusted (exit status 1, no record written).

    Raised when the staged render's output differs from the product's ``render``, when
    ``clip(prefused)`` differs from the staged ``fused``, or when the video decode did not deliver
    every selected frame.
    """


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
    ``round(length) + 1`` of them (:func:`sample_spacing` apart); each is the mean of
    ``2 * half_width + 1`` samples on the perpendicular through it, 1 pixel apart. Every sample
    of the strip must lie inside the array (``0 <= x <= W - 1``, ``0 <= y <= H - 1``, so its
    bilinear support does too): nothing is clamped.

    Args:
        plane: An ``(H, W)`` array.
        line: The line, in the array's pixel coordinates.
        half_width: The number of parallel lines on each side.

    Returns:
        The profile, float64.

    Raises:
        ValueError: ``plane`` is not 2-D, the line is shorter than 4 pixels, ``half_width`` is
            negative, or the strip leaves the array.
    """
    if plane.ndim != 2:
        raise ValueError(f"need an (H, W) array, got shape {plane.shape}")
    if half_width < 0:
        raise ValueError(f"half_width must be at least 0, got {half_width}")
    length = line.length
    if length < 4:
        raise ValueError(f"the line is {length:.1f} px long; at least 4 px is needed")
    left, top, right, bottom = strip_bounds(line, half_width)
    height, width = plane.shape
    tolerance = 1e-9
    if left < -tolerance or top < -tolerance:
        raise ValueError(f"the profile strip of {line} leaves the array (above or left)")
    if right > width - 1 + tolerance or bottom > height - 1 + tolerance:
        raise ValueError(f"the profile strip of {line} leaves the {width} x {height} array")
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


def strip_bounds(line: Line, half_width: int) -> tuple[float, float, float, float]:
    """The bounding box of a line's averaging strip (the corners of its outermost parallels).

    Args:
        line: The line.
        half_width: The number of parallel lines on each side, 1 pixel apart.

    Returns:
        ``(left, top, right, bottom)`` in the line's pixel coordinates.
    """
    length = line.length
    ux, uy = (line.x1 - line.x0) / length, (line.y1 - line.y0) / length
    xs = [x - o * uy for x in (line.x0, line.x1) for o in (-half_width, half_width)]
    ys = [y + o * ux for y in (line.y0, line.y1) for o in (-half_width, half_width)]
    return min(xs), min(ys), max(xs), max(ys)


def sample_spacing(line: Line) -> float:
    """The distance in pixels between two profile samples: ``length / round(length)``.

    Args:
        line: The line.

    Returns:
        The spacing (1 for a line whose length is a whole number of pixels).
    """
    return line.length / round(line.length)


def _bilinear(data: FloatArray, xs: FloatArray, ys: FloatArray) -> FloatArray:
    """Bilinear samples of ``data`` at ``(xs, ys)`` (inside the array: see line_profile)."""
    height, width = data.shape
    xs = np.clip(xs, 0.0, width - 1.0)  # only rounding below 1e-9: line_profile checked bounds
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
    spacing: float = 1.0,
) -> dict[str, Any]:
    """Measure the two-sided edge band of one profile (a diagnostic, not the table's metric).

    Each side's outward deviation from its own plateau line, over the profile's own contrast:
    meaningful when both sides are plateaus.

    Args:
        profile: The samples, ``spacing`` pixels apart across the edge.
        threshold: The band threshold as a fraction of the edge contrast.
        fits: The layout to use; :func:`profile_fits` of ``profile`` when None.
        spacing: The distance between samples in pixels (:func:`sample_spacing`).

    Returns:
        ``edge_index``; ``contrast`` (C); ``overshoot`` and ``undershoot`` (absolute, the
        image's units) with their ratios to C; ``band`` (the larger), ``band_ratio``,
        ``band_side`` (``"bright"`` or ``"dark"``), ``peak_index``, ``peak_distance_px``
        (from the edge); ``fwhm_px`` (the interpolated width at half the peak); ``extent_px``
        (the interpolated width above ``threshold * C``; 0 when the peak is below it);
        ``exceeds`` (``band_ratio > threshold``); and ``noise`` (the RMS residual of the two
        plateau fits).
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
        "peak_distance_px": abs(peak - layout.edge) * spacing,
        "fwhm_px": _width(dev, peak, band / 2.0) * spacing if band > 0 else 0.0,
        "extent_px": _width(dev, peak, threshold * contrast) * spacing
        if band > threshold * contrast
        else 0.0,
        "exceeds": bool(ratio > threshold),
        "noise": _noise(profile, layout),
    }


def _run_bounds(values: FloatArray, peak: int, level: float) -> tuple[int, int] | None:
    """The first and last index of the contiguous run around ``peak`` where ``values >= level``.

    None when ``values[peak]`` is below ``level``.
    """
    if values[peak] < level:
        return None
    lo = peak
    while lo > 0 and values[lo - 1] >= level:
        lo -= 1
    hi = peak
    while hi < values.size - 1 and values[hi + 1] >= level:
        hi += 1
    return lo, hi


def _support(values: FloatArray, peak: int, level: float) -> int:
    """The number of consecutive samples around ``peak`` at or above ``level`` (0 if none)."""
    bounds = _run_bounds(values, peak, level)
    return 0 if bounds is None else bounds[1] - bounds[0] + 1


def _width(values: FloatArray, peak: int, level: float) -> float:
    """The width, in samples, of the run around ``peak`` above ``level``, crossings interpolated.

    Each end is the linear interpolation between the last sample at or above ``level`` and the
    first below it; a run that reaches the array's end stops at that sample. A single sample
    whose neighbours are 0, at half its height, is 1 sample wide.
    """
    bounds = _run_bounds(values, peak, level)
    if bounds is None:
        return 0.0
    lo, hi = bounds
    left = float(lo)
    if lo > 0:
        left = lo - 1 + (level - values[lo - 1]) / (values[lo] - values[lo - 1])
    right = float(hi)
    if hi < values.size - 1:
        right = hi + (values[hi] - level) / (values[hi] - values[hi + 1])
    return float(right - left)


def _noise(profile: FloatArray, fits: Fits) -> float:
    """The RMS residual of the two plateau fits."""
    count, outer = fits.count, fits.outer
    residuals = []
    for start, stop in ((0, outer), (count - outer, count)):
        index = np.arange(start, stop, dtype=np.float64)
        residuals.append(profile[start:stop] - np.polyval(_fit(profile, start, stop), index))
    return float(np.sqrt(np.mean(np.concatenate(residuals) ** 2)))


def water_uncertainty(profile: FloatArray, fits: Fits) -> FloatArray:
    """The standard uncertainty of each sample's deviation from the water-plateau line.

    From the start plateau's line fit (``n = fits.outer`` samples at ``x``): ``sigma`` the RMS
    residual (``n - 2`` degrees of freedom), ``rho`` the residuals' lag-1 autocorrelation
    (clamped to [0, 0.99]) and ``n_eff = max(2, n (1 - rho) / (1 + rho))`` (AR(1)). At sample
    ``i`` the deviation's uncertainty is ``sigma * sqrt(1 + (1 / n + (i - mean(x))^2 / Sxx) *
    n / n_eff)``: the sample's own noise plus the error of the line extrapolated to it, which a
    spatially correlated noise (texture, codec blocks, amplified grain) makes much larger than
    the residual alone suggests.

    Args:
        profile: The samples.
        fits: The layout.

    Returns:
        The uncertainty at every sample, in the profile's units.
    """
    n = fits.outer
    x = np.arange(n, dtype=np.float64)
    residual = profile[:n] - np.polyval(_fit(profile, 0, n), x)
    energy = float(np.sum(residual**2))
    sigma = math.sqrt(energy / max(n - 2, 1))
    rho = float(np.sum(residual[1:] * residual[:-1]) / energy) if energy > 0 else 0.0
    rho = min(max(rho, 0.0), 0.99)
    n_eff = max(2.0, n * (1.0 - rho) / (1.0 + rho))
    centre = float(x.mean())
    sxx = float(np.sum((x - centre) ** 2))
    index = np.arange(fits.count, dtype=np.float64)
    spread = (1.0 / n + (index - centre) ** 2 / sxx) * n / n_eff
    out: FloatArray = sigma * np.sqrt(1.0 + spread)
    return out


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


def water_deviation(profile: FloatArray, fits: Fits) -> FloatArray:
    """Each sample's deviation from the profile's own water-plateau line (linear in the profile).

    Args:
        profile: The samples.
        fits: The layout.

    Returns:
        ``profile`` minus the least-squares line through its start segment, at every sample.
    """
    index = np.arange(fits.count, dtype=np.float64)
    out: FloatArray = profile - np.polyval(_fit(profile, 0, fits.outer), index)
    return out


def outward_overshoot(profile: FloatArray, fits: Fits, sign: float) -> FloatArray:
    """The water side's rise past its own plateau line, away from the object (absolute units).

    Args:
        profile: The samples.
        fits: The layout.
        sign: +1 when the water is brighter than the object (outward is up), -1 otherwise.

    Returns:
        ``max(0, sign * water_deviation)`` on the zone ``[outer, edge]``; 0 elsewhere.
    """
    zone = np.zeros(fits.count, dtype=bool)
    zone[fits.outer : fits.edge + 1] = True
    out: FloatArray = np.where(zone, np.maximum(sign * water_deviation(profile, fits), 0.0), 0.0)
    return out


def water_band(
    profile: FloatArray,
    reference: FloatArray,
    fits: Fits,
    *,
    threshold: float = DEFAULT_THRESHOLD,
    spacing: float = 1.0,
    remapped: FloatArray | None = None,
) -> dict[str, Any]:
    """Measure the band a stage ADDS beyond the source's water-side profile (the table's metric).

    The line's start lies in open water (a plateau); its end inside the object (which may be
    textured). The excess at each water-side sample is the stage's outward overshoot past its
    own water-plateau line minus the source's (:func:`outward_overshoot`), divided by ONE common
    contrast: the source's signed water contrast (:func:`water_contrast` of ``reference``). A
    monotonic remap (gamma, white balance, a plateau change) of a source with no overshoot moves
    no sample past its own plateau line and reports no band (of a source that already
    overshoots it scales that overshoot: hence ``remapped``); an inward spread is not a band.
    With ``remapped`` (a pointwise stage, ruling S1) the overshoot subtracted, and the second
    uncertainty, are the remapped source's instead of the source's; the contrast stays the
    source's.

    Args:
        profile: The stage's samples.
        reference: The source's samples on the same line and channel.
        fits: The source profile's layout (one edge for every stage).
        threshold: The band threshold, a fraction of the source contrast.
        spacing: The distance between samples in pixels (:func:`sample_spacing`).
        remapped: The source remapped through the stage's own pointwise operation, on the same
            line and channel; None measures against ``reference`` (face value).

    Returns:
        ``contrast`` (the source's signed contrast, the common denominator);
        ``stage_contrast`` (the stage's own, for reading); ``band`` (the largest excess, 0 when
        none is positive) and ``band_ratio`` (the same); ``excess_at_peak`` (the excess at
        ``peak_index``, which may be negative when there is no band); ``band_abs`` (``band *
        |contrast|``, the image's units); ``peak_index``; ``peak_distance_px``; ``fwhm_px``
        and ``extent_px`` (interpolated widths at half the band and at ``threshold``);
        ``noise_ratio`` (the stage's and the source's :func:`water_uncertainty` in quadrature,
        over ``|contrast|``, at the peak); ``level`` (the qualifying level there, ``max(threshold,
        NOISE_FACTOR * noise_ratio)``); ``support_samples`` (consecutive samples around the peak
        each at or above its own level); ``weak_edge``;
        ``exceeds`` (``band > threshold``); ``qualifies``; ``verdict`` (``"band"``,
        ``"undecided"`` or ``"none"``); and ``reference`` (``"remapped_source"`` or
        ``"source"``).
    """
    contrast = water_contrast(reference, fits)
    weak = abs(contrast) < MIN_CONTRAST
    sign = 1.0 if contrast >= 0 else -1.0
    scale = 1.0 / abs(contrast) if contrast != 0.0 else 0.0
    baseline = reference if remapped is None else remapped
    excess = (
        outward_overshoot(profile, fits, sign) - outward_overshoot(baseline, fits, sign)
    ) * scale
    peak = int(np.argmax(excess))
    at_peak = float(excess[peak])
    band = max(at_peak, 0.0)
    noise = np.hypot(water_uncertainty(profile, fits), water_uncertainty(baseline, fits)) * scale
    levels = np.maximum(threshold, NOISE_FACTOR * noise)
    support = _support(excess - levels, peak, 0.0) if band > 0 else 0
    exceeds = band > threshold
    qualifies = (not weak) and band > levels[peak] and support >= MIN_SUPPORT_SAMPLES
    verdict = "band" if qualifies else "undecided" if weak or exceeds else "none"
    return {
        "contrast": contrast,
        "stage_contrast": water_contrast(profile, fits),
        "weak_edge": weak,
        "band": band,
        "band_ratio": band,
        "excess_at_peak": at_peak,
        "band_abs": band * abs(contrast),
        "peak_index": peak,
        "peak_distance_px": abs(fits.edge - peak) * spacing,
        "fwhm_px": _width(excess, peak, band / 2.0) * spacing if band > 0 else 0.0,
        "extent_px": _width(excess, peak, threshold) * spacing if exceeds else 0.0,
        "noise_ratio": float(noise[peak]),
        "level": float(levels[peak]),
        "support_samples": support,
        "exceeds": exceeds,
        "qualifies": qualifies,
        "verdict": verdict,
        "reference": "source" if remapped is None else "remapped_source",
    }


def stage_band(
    stage: str,
    profile: FloatArray,
    source: FloatArray,
    fits: Fits,
    *,
    references: Mapping[str, FloatArray],
    threshold: float = DEFAULT_THRESHOLD,
    spacing: float = 1.0,
) -> dict[str, Any]:
    """Measure one stage's band against the reference ruling S1 assigns it.

    Args:
        stage: The stage name (an :data:`IMAGE_STAGES` entry).
        profile: The stage's samples.
        source: The source's samples on the same line and channel.
        fits: The source profile's layout.
        references: Pointwise stage name (a :data:`POINTWISE_REFERENCES` key) -> the source
            remapped through that stage's operation, on the same line and channel.
        threshold: The band threshold.
        spacing: The distance between samples in pixels.

    Returns:
        :func:`water_band` of the stage: against ``references[stage]`` for a pointwise stage,
        against the source (face value) for every other.
    """
    remapped = references[stage] if stage in POINTWISE_REFERENCES else None
    return water_band(
        profile, source, fits, threshold=threshold, spacing=spacing, remapped=remapped
    )


def attributed_stage(fused: Mapping[str, Any], attribution: Mapping[str, Any] | None) -> str:
    """Name the input that carries a qualifying fused band (ruling S2).

    Args:
        fused: The fused stage's :func:`water_band` (luma) record.
        attribution: :func:`attribute_band` of it (None when there is no positive excess).

    Returns:
        ``"none"`` when the fused verdict is ``none``; ``"undecided"`` when it is
        ``undecided``, when there is no attribution, when neither input's share is positive, or
        when the two shares are within :data:`ATTRIBUTION_TIE` (a tie); otherwise ``"input1"``
        or ``"input2"``, the input whose terms carry the larger share at the band's peak.
    """
    if fused["verdict"] != "band":
        return "none" if fused["verdict"] == "none" else "undecided"
    if attribution is None:
        return "undecided"
    first = float(attribution["per_input"].get("k1", 0.0))
    second = float(attribution["per_input"].get("k2", 0.0))
    if max(first, second) <= 0.0 or abs(first - second) <= ATTRIBUTION_TIE:
        return "undecided"
    return "input1" if first > second else "input2"


def first_stage(bands: Mapping[str, Mapping[str, Any]]) -> str | None:
    """Name the first product stage whose band qualifies.

    Args:
        bands: Product stage name -> its :func:`water_band` (luma) record; the stages after
            ``source`` in :data:`PRODUCT_STAGES` are read in pipeline order.

    Returns:
        The first stage whose verdict is ``band``; ``"undecided"`` when the edge is weak, or
        when no stage qualifies but one is ``undecided``; None when no stage exceeds the
        threshold. A stage over the threshold that does not qualify never decides the answer.
    """
    stages = [name for name in PRODUCT_STAGES[1:] if name in bands]
    if any(bands[name]["weak_edge"] for name in stages):
        return "undecided"
    for name in stages:
        if bands[name]["verdict"] == "band":
            return name
    if any(bands[name]["verdict"] == "undecided" for name in stages):
        return "undecided"
    return None


def term_deviation(term: FloatArray, fits: Fits, peak: int) -> float:
    """Return one additive term's deviation from its own water-plateau line at ``peak``.

    Args:
        term: The term's profile (one input's and one level's share of a profile).
        fits: The layout.
        peak: The sample index.

    Returns:
        ``term[peak]`` minus the term's start-plateau line there; least squares is linear, so
        the terms of a sum add up to the sum's deviation.
    """
    line = np.polyval(_fit(term, 0, fits.outer), peak)
    return float(term[peak] - line)


def attribute_band(
    band: Mapping[str, Any],
    profiles: Mapping[str, FloatArray],
    fits: Fits,
) -> dict[str, Any] | None:
    """Split the fused stage's detected band, at its peak, over inputs and pyramid levels.

    The added band at the peak is ``(sign * dev(fused) - overshoot(source)) / |C|``. With the
    product's decomposition ``prefused = sum_kl term_kl`` and the source's ``S = sum_kl
    srcterm_kl`` (same weights; :func:`staged_render`), the share of input ``k`` at level ``l``
    is ``sign * (dev(term_kl) - [s] dev(srcterm_kl)) / |C|`` with ``[s]`` 1 when the source is
    outward at the peak (its overshoot is what was subtracted) and 0 otherwise; the clip's share
    is ``sign * (dev(fused) - dev(prefused)) / |C|``. The shares and the clip add up to
    ``excess_at_peak`` exactly in real arithmetic (``residual`` is the float difference).

    Args:
        band: The fused stage's :func:`water_band` (luma) record.
        profiles: Luma profiles: ``source``, ``fused``, ``prefused``, every ``term_k<k>_l<l>``
            and ``srcterm_k<k>_l<l>``.
        fits: The source's layout.

    Returns:
        None when there is no positive excess to split (``excess_at_peak <= 0``) or the
        contrast is 0; otherwise ``peak_index``, ``excess_at_peak``, ``source_subtracted``,
        ``terms`` (``k<k>_l<l>`` -> share), ``per_input`` (``k<k>``), ``per_level`` (``l<l>``),
        ``clip``, ``total`` (the shares plus the clip), ``residual`` (``total -
        excess_at_peak``) and ``raw_per_input`` (each input's terms without the source
        subtraction, for comparison).
    """
    contrast = band["contrast"]
    at_peak = band["excess_at_peak"]
    if contrast == 0.0 or at_peak <= 0.0:
        return None
    peak = band["peak_index"]
    sign = 1.0 if contrast > 0 else -1.0
    scale = sign / abs(contrast)
    subtract = sign * term_deviation(profiles["source"], fits, peak) > 0.0
    terms: dict[str, float] = {}
    raw: dict[str, float] = {}
    for name, term in profiles.items():
        if not name.startswith("term_"):
            continue
        key = name.removeprefix("term_")
        own = term_deviation(term, fits, peak)
        source = term_deviation(profiles[f"srcterm_{key}"], fits, peak) if subtract else 0.0
        terms[key] = scale * (own - source)
        raw[key] = scale * own
    clip = scale * (
        term_deviation(profiles["fused"], fits, peak)
        - term_deviation(profiles["prefused"], fits, peak)
    )
    per_input: dict[str, float] = {}
    per_level: dict[str, float] = {}
    raw_per_input: dict[str, float] = {}
    for key, share in terms.items():
        k, level = key.split("_")
        per_input[k] = per_input.get(k, 0.0) + share
        per_level[level] = per_level.get(level, 0.0) + share
        raw_per_input[k] = raw_per_input.get(k, 0.0) + raw[key]
    total = sum(terms.values()) + clip
    return {
        "peak_index": peak,
        "excess_at_peak": at_peak,
        "source_subtracted": subtract,
        "terms": terms,
        "per_input": per_input,
        "per_level": per_level,
        "clip": clip,
        "total": total,
        "residual": total - at_peak,
        "raw_per_input": raw_per_input,
    }


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
    are ``(H, W, 3)`` and maps ``(H, W)``. After ``output`` it yields the two pointwise
    references of ruling S1: ``remap_balanced`` (the SOURCE through the render's white balance,
    the same gains) and ``remap_input1`` (that through the render's gamma, as input 1 is formed);
    then, per input k, the
    attribution terms ``term_k<k>_l<l>`` (``collapse`` of input k's blended band at level l
    alone, zeros at the other levels) and the source's ``srcterm_k<k>_l<l>`` (the source's
    Laplacian band under the same weight pyramid), then ``prefused``: the collapse of the
    blended pyramid summed as :func:`multiscale_fusion` sums it, before its clip (the terms add
    up to it; the source terms add up to the source because the weights sum to 1).

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
    remap_balanced = method._white_balance(backend, pixels, params, records["white_balance"])
    yield "remap_balanced", remap_balanced
    yield "remap_input1", (remap_balanced ** np.float32(float(params["gamma"]))).clip(0.0, 1.0)
    del remap_balanced
    levels = pyramid_levels(inputs[0].shape, params["pyramid_min_level_size"])
    source_bands = laplacian_pyramid(backend, pixels, levels)
    summed: list[Any] = []
    for k, (fusion_input, weight) in enumerate(zip(inputs, weights, strict=True), start=1):
        weight_pyramid = gaussian_pyramid(backend, weight, levels)
        pairs = zip(weight_pyramid, laplacian_pyramid(backend, fusion_input, levels), strict=True)
        bands = [w[..., None] * band for w, band in pairs]  # as multiscale_fusion forms them
        summed = bands if not summed else [f + b for f, b in zip(summed, bands, strict=True)]
        for level in range(levels):
            yield f"term_k{k}_l{level}", collapse_pyramid(backend, _alone(backend, bands, level))
        source_weighted = [
            w[..., None] * band for w, band in zip(weight_pyramid, source_bands, strict=True)
        ]
        for level in range(levels):
            alone = _alone(backend, source_weighted, level)
            yield f"srcterm_k{k}_l{level}", collapse_pyramid(backend, alone)
        del bands, source_weighted, weight_pyramid
    yield "prefused", collapse_pyramid(backend, summed)  # multiscale_fusion's sum, before the clip


def _alone(backend: CoreBackend, bands: Sequence[Any], level: int) -> list[Any]:
    """A pyramid holding ``bands[level]`` and zeros at every other level."""
    return [band if i == level else backend.xp.zeros_like(band) for i, band in enumerate(bands)]


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

    Two checks make the measurement trustworthy, and either failing raises
    :class:`ProbeFailedError`: the staged ``output`` equals ``method.render``'s result bit for bit,
    and ``clip(prefused)`` equals the staged ``fused`` bit for bit (so the attribution terms
    decompose the very image that was measured).

    Args:
        method: The method.
        image: The image on its device.
        params: The resolved parameters.
        statistics: The stage records used for the render.
        lines: The profile lines, in source pixels.
        region: The crop region (contains every line's strip).
        half_width: The profile's half width.
        threshold: The band threshold.
        crops: The folder for the 16-bit crops, or None for none.
        prefix: The crops' file-name prefix.

    Returns:
        The frame's record: per line, per stage, per channel band statistics; the first stage
        whose band qualifies; the attribution per input and level; the weight profiles; the
        two checks; the saved crops.

    Raises:
        ProbeFailedError: Either check fails.
    """
    backend = _backend(image)
    local = [_shifted(line, region) for line in lines]
    profiles: dict[str, list[dict[str, FloatArray]]] = {}
    maps: dict[str, list[FloatArray]] = {}
    saved: dict[str, Any] = {}
    output_full: Any = None
    fused_full: Any = None
    prefused_difference = math.inf
    shape = image.pixels.shape
    for name, array in staged_render(method, image, params, statistics):
        crop = _crop(backend, array, region)
        if name == "output":
            output_full = array
        elif name == "fused":
            fused_full = array
        elif name == "prefused":
            prefused_difference = float(abs(array.clip(0.0, 1.0) - fused_full).max())
            fused_full = None
        if crops is not None and not name.startswith(_UNSAVED):
            path = crops / f"{prefix}-{name}.png"
            saved[name] = {"file": path.name, "scale": save_crop(path, crop)}
            if name in ("source", "output"):  # an 8-bit view with the lines, for reading
                whole = Region(0, 0, region.w, region.h)
                save_overview(crops / f"{prefix}-{name}-marked.png", crop, whole, local, 1400)
        if crop.ndim == 3:
            planes = channel_planes(crop)
            channels = ("Y",) if name.startswith(("term_", "srcterm_")) else CHANNELS
            profiles[name] = [
                {c: line_profile(planes[c], line, half_width=half_width) for c in channels}
                for line in local
            ]
        else:
            maps[name] = [line_profile(crop, line, half_width=half_width) for line in local]
    rendered = method.render(image, params, dict(statistics)).pixels
    difference = float(abs(rendered - output_full).max())  # one device-to-host read
    del rendered, output_full
    if difference != 0.0:
        raise ProbeFailedError(
            f"the staged output differs from the product's render by up to {difference:.3g}"
        )
    if prefused_difference != 0.0:
        raise ProbeFailedError(
            f"clip(prefused) differs from the staged fused image by up to {prefused_difference:.3g}"
        )
    results = []
    for index, line in enumerate(lines):
        results.append(_line_record(index, line, profiles, maps, threshold=threshold))
    return {
        "render_check_max_abs_difference": difference,
        "render_check_equal": True,
        "prefused_check_max_abs_difference": prefused_difference,
        "prefused_check_equal": True,
        "shape": list(shape),
        "lines": results,
        "crops": saved,
        "pyramid_levels": pyramid_levels(shape, params["pyramid_min_level_size"]),
    }


_UNSAVED = ("term_", "srcterm_", "prefused")
"""Name prefixes of the staged arrays that are measured but not saved as crops."""


def _line_record(
    index: int,
    line: Line,
    profiles: Mapping[str, list[dict[str, FloatArray]]],
    maps: Mapping[str, list[FloatArray]],
    *,
    threshold: float,
) -> dict[str, Any]:
    """The record of one line: stage bands, the first qualifying stage, the attribution.

    ``water`` (the table's metric) is :func:`stage_band` per stage and channel (against the
    remapped source for a pointwise stage, the source otherwise), on the source's layout, at the
    line's sample spacing; ``two_sided`` is
    :func:`band_statistics` per stage and channel on each stage's own layout (meaningful when
    both sides are plateaus). ``first_stage_over_threshold`` is :func:`first_stage` of the luma
    bands; ``unqualified_exceedances`` lists the product stages over the threshold whose band
    does not qualify; ``attribution`` is :func:`attribute_band` of the fused luma band and
    ``attributed_stage`` its :func:`attributed_stage`.
    """
    spacing = sample_spacing(line)
    source = profiles["source"][index]
    fits = profile_fits(source["Y"])
    two_sided: dict[str, Any] = {}
    water: dict[str, Any] = {}
    for name in IMAGE_STAGES:
        per = profiles[name][index]
        two_sided[name] = {
            c: band_statistics(per[c], threshold=threshold, spacing=spacing) for c in CHANNELS
        }
        water[name] = {
            c: stage_band(
                name,
                per[c],
                source[c],
                fits,
                references={
                    stage: profiles[array][index][c]
                    for stage, array in POINTWISE_REFERENCES.items()
                },
                threshold=threshold,
                spacing=spacing,
            )
            for c in CHANNELS
        }
    luma_bands = {name: water[name]["Y"] for name in PRODUCT_STAGES[1:]}
    unqualified = [
        name for name, band in luma_bands.items() if band["exceeds"] and not band["qualifies"]
    ]
    terms = {
        name: values[index]["Y"]
        for name, values in profiles.items()
        if name.startswith(("term_", "srcterm_"))
    }
    attribution = attribute_band(
        water["fused"]["Y"],
        {
            "source": source["Y"],
            "fused": profiles["fused"][index]["Y"],
            "prefused": profiles["prefused"][index]["Y"],
            **terms,
        },
        fits,
    )
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
        "sample_spacing_px": spacing,
        "edge_index": edge,
        "outer_samples": fits.outer,
        "first_stage_over_threshold": first_stage(luma_bands),
        "attributed_stage": attributed_stage(water["fused"]["Y"], attribution),
        "unqualified_exceedances": unqualified,
        "water": water,
        "two_sided": two_sided,
        "attribution": attribution,
        "weights": weights,
        "profiles_Y": {
            name: [round(float(v), 5) for v in profiles[name][index]["Y"]]
            for name in (*IMAGE_STAGES, "stretched", *POINTWISE_REFERENCES.values())
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
    _check_region(region, pixels.shape, options["lines"], options["half_width"])
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
        expected_frames=expected_frames(probe),
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
    _check_region(region, shape, options["lines"], options["half_width"])
    scales = scale_facts(shape, params)
    frames: list[dict[str, Any]] = []
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
    missing = sorted(set(chosen) - {frame["pts_ticks"] for frame in frames})
    if missing:
        raise ProbeFailedError(
            f"the decode did not deliver {len(missing)} of the {len(chosen)} selected frames "
            f"(first missing pts {missing[0]})"
        )
    return {
        "kind": "video",
        "device": reason,
        "analysis": "AnalysisEngine.analysis_job over the whole clip (smoothing defaults, "
        "expected_frames as the export passes it)",
        "expected_frames": expected_frames(probe),
        "frames_in_clip": len(axis),
        "scales": scales,
        "region": dataclasses.asdict(region),
        "frames": frames,
    }


def _check_region(
    region: Region, shape: tuple[int, ...], lines: Sequence[Line], half_width: int
) -> None:
    """Refuse a region outside the image, or a line whose averaging strip leaves the region.

    The whole footprint is checked (:func:`strip_bounds`: both ends of every parallel line),
    so no profile sample is clamped at the crop's border.
    """
    if region.w < 8 or region.h < 8 or region.x < 0 or region.y < 0:
        raise ProbeError(f"region {region} is too small or negative")
    if region.x + region.w > shape[1] or region.y + region.h > shape[0]:
        raise ProbeError(f"region {region} exceeds the image {shape[1]} x {shape[0]}")
    for line in lines:
        if line.length < 4:
            raise ProbeError(f"line {line} is shorter than 4 px")
        left, top, right, bottom = strip_bounds(line, half_width)
        inside_x = region.x <= left and right <= region.x + region.w - 1
        if not (inside_x and region.y <= top and bottom <= region.y + region.h - 1):
            raise ProbeError(
                f"the strip of line {line} (half width {half_width}) leaves the region {region}"
            )


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
    parser.add_argument(
        "--replace",
        action="store_true",
        help="keep an existing output folder aside (<out>.replaced-<stamp>) and publish anew",
    )
    return parser


def _options(args: argparse.Namespace) -> tuple[Path, str, Path, dict[str, Any]]:
    """Resolve the source, the run name, the output folder and the run options.

    The local configuration is read only when it is needed: for a footage stem, or for the
    default output or cache folder. ``options`` also names the run's three sibling folders of
    the output (``staging``, ``failed``, ``replaced``; see the module docstring), each checked
    like the output.
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
    name = source.stem if args.name is None else args.name
    _check_name(name)
    root = load_local_config().working_path / "wp5.7"
    out = args.out or root / "part1" / name
    cache_dir = args.cache_dir or root / "cache"
    if headless_export.inside(root, out):
        raise ProbeError(f"{out} must be a folder below the working folder's wp5.7 folder")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    siblings = {
        "staging": out.parent / f".{out.name}.staging-{stamp}",
        "failed": out.parent / f".{out.name}.failed-{stamp}",
        "replaced": out.parent / f"{out.name}.replaced-{stamp}",
    }
    if _cache_conflict(cache_dir, out):
        raise ProbeError(
            f"--cache-dir {cache_dir} must lie outside the output folder {out.name}, its "
            "sibling folders and every folder that contains them"
        )
    footage = headless_export.configured_footage_folder()
    for target in (out, cache_dir, out / f"{name}.json", *siblings.values()):
        if not headless_export.inside(target, root):
            raise ProbeError(f"{target} is not inside the working folder's wp5.7 folder")
        if footage is not None:
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
        **siblings,
    }
    return source, name, out, options


def _cache_conflict(cache_dir: Path, out: Path) -> bool:
    """True when the cache folder would share a tree with the publication.

    That is: ``cache_dir`` equals, lies inside or contains ``out``, or lies inside a sibling of
    ``out`` named ``<out>.*`` or ``.<out>.*`` (the staging, failed and replaced folders of any
    run). Compared resolved and case-normalised (:func:`headless_export.inside` for the first
    three).
    """
    if headless_export.inside(cache_dir, out) or headless_export.inside(out, cache_dir):
        return True
    parent = PurePath(os.path.normcase(str(out.parent.resolve())))
    cache = PurePath(os.path.normcase(str(cache_dir.resolve())))
    if not cache.is_relative_to(parent) or cache == parent:
        return False
    first = cache.relative_to(parent).parts[0]
    stem = os.path.normcase(out.name)
    return first.startswith((f"{stem}.", f".{stem}."))


def _check_name(name: str) -> None:
    """Refuse a run name that is not a plain file stem (it becomes a path component).

    Raises:
        ProbeError: The name is empty, holds a path separator, a drive or stream ``:``, a
            ``..`` or a control character, is not its own last path component, or is a Windows
            device name (:data:`WINDOWS_DEVICE_NAMES`; any case, any extension, trailing spaces
            before the extension ignored as Windows ignores them).
    """
    plain = (
        bool(name)
        and not any(ch in name for ch in '/\\:<>"|?*')
        and ".." not in name
        and all(ch.isprintable() for ch in name)
        and Path(name).name == name
        and name.strip(" .") == name
        and name.split(".")[0].rstrip(" ").upper() not in WINDOWS_DEVICE_NAMES
    )
    if not plain:
        raise ProbeError(f"--name {name!r} is not a plain file stem")


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
        if os.path.lexists(out) and not args.replace:
            raise ProbeError(f"{out.name} exists; pass --replace to keep it aside and publish anew")
        is_video = source.suffix.lower() in {".mp4", ".mov"}
        if is_video and (args.start is None or args.end is None):
            raise ProbeError("a video needs --start and --end")
    except (ProbeError, LocalConfigError) as exc:
        print(f"halo_probe: {exc}", file=sys.stderr)
        return 2
    staging: Path = options["staging"]
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        staging.mkdir()  # exclusive: fails when anything (a folder, a file, a link) has the name
    except OSError as exc:
        print(f"halo_probe: FAILED, cannot make the staging folder: {exc}", file=sys.stderr)
        return 1
    began = datetime.now(UTC)
    try:
        run = (run_video if is_video else run_photo)(
            source, method, params, force_cpu=args.force_cpu, options={**options, "out": staging}
        )
        record = _record(args, name, source, method, params, options, began, run)
        with (staging / f"{name}.json").open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(_plain(record), indent=1))
    except BaseException as exc:
        kept = _abandon(staging, options["failed"])
        if isinstance(exc, ProbeError):
            print(f"halo_probe: {exc}{kept}", file=sys.stderr)
            return 2
        if isinstance(exc, ProbeFailedError):
            print(f"halo_probe: FAILED, nothing published: {exc}{kept}", file=sys.stderr)
            return 1
        raise
    try:
        _publish(staging, out, options["replaced"] if args.replace else None)
    except BaseException as exc:  # round 3, fix 3: retire the staging folder on ANY exception
        kept = _abandon(staging, options["failed"])
        if isinstance(exc, OSError):
            print(f"halo_probe: FAILED to publish: {exc}{kept}", file=sys.stderr)
            return 1
        raise
    print(summary(record))
    return 0


def _record(
    args: argparse.Namespace,
    name: str,
    source: Path,
    method: AncutiFusionMethod,
    params: Mapping[str, Any],
    options: Mapping[str, Any],
    began: datetime,
    run: Mapping[str, Any],
) -> dict[str, Any]:
    """The run record: the settings, the rules in words, the times and the run's results."""
    return {
        "schema": 3,
        "tool": "halo_probe",
        "name": name,
        "source": source.name,
        "method": method.id,
        "parameters": params,
        "overrides": list(args.param),
        "threshold": options["threshold"],
        "half_width": options["half_width"],
        "outer_fraction": OUTER_FRACTION,
        "min_contrast": MIN_CONTRAST,
        "min_support_samples": MIN_SUPPORT_SAMPLES,
        "noise_factor": NOISE_FACTOR,
        "metric": "water: outward overshoot past the stage's own water plateau minus the "
        "source's (for the pointwise stages balanced and input1: minus the source remapped "
        "through the stage's own gains / gamma, ruling S1), over the source's signed contrast; "
        "qualifies when not weak, above max(threshold, noise_factor * noise) over "
        "min_support_samples",
        "attributed_stage_rule": "ruling S2: the input whose terms carry the larger share of a "
        "qualifying fused band at its peak; none / undecided when the fused band is none / "
        "undecided; undecided on a tie (within attribution_tie) or when neither share is "
        "positive",
        "attribution_tie": ATTRIBUTION_TIE,
        "started": began.isoformat(),
        "finished": datetime.now(UTC).isoformat(),
        **run,
    }


def _abandon(staging: Path, failed: Path) -> str:
    """Retire a failed run's staging folder; return a note for the message (may be empty).

    An empty folder is removed with ``os.rmdir`` (it removes nothing else); one holding partial
    output is renamed ``failed`` and kept. Nothing is published either way. A staging folder
    that is already gone (the publish rename completed before an interrupt) is left alone.
    """
    if not os.path.lexists(staging):
        return ""
    try:
        os.rmdir(staging)
        return ""
    except OSError:
        pass
    try:
        staging.rename(failed)
        return f" (partial output kept in {failed.name})"
    except OSError as exc:
        return f" (partial output left in {staging.name}: {exc})"


class RollbackError(OSError):
    """The publish rename failed and putting the old publication back failed too."""


def _publish(staging: Path, out: Path, replaced: Path | None) -> None:
    """Publish the staging folder as ``out``, keeping an existing ``out`` aside as ``replaced``.

    Both renames sit inside one guard (Reviewer A round 3, fix 2). When either fails or is
    interrupted (any exception), the rollback reads the folders to tell where the publication
    stopped: ``out`` absent and ``replaced`` present means ``out`` was renamed aside and nothing
    took its place, so ``replaced`` is renamed back; ``out`` still present means it was not yet
    renamed aside (or the publish completed), so nothing is moved. ``replaced`` is a fresh
    stamped name, so its presence is this run's doing. The exception is then re-raised; the
    staging folder stays for the caller to retire.

    Raises:
        OSError: ``out`` exists and ``replaced`` is None, or a rename fails.
        RollbackError: Putting the old publication back failed as well; the message names the
            publish failure, the rollback failure and ``replaced``, which holds the old
            publication.
    """
    if os.path.lexists(out):
        if replaced is None:
            raise FileExistsError(f"{out.name} appeared during the run; nothing published")
        try:
            out.rename(replaced)
            staging.rename(out)
        except BaseException as exc:
            if os.path.lexists(out) or not os.path.lexists(replaced):
                raise  # not yet renamed aside (or already published): nothing to put back
            try:
                replaced.rename(out)
            except BaseException as undo:
                raise RollbackError(
                    f"publishing failed ({exc!r}) and putting the old publication back failed "
                    f"({undo!r}); the old publication is kept in {replaced.name}, beside "
                    f"{out.name}"
                ) from exc
            raise
        return
    staging.rename(out)


def summary(record: Mapping[str, Any]) -> str:
    """One text line per frame and line: the first qualifying and attributed stages, luma bands.

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
                f"{stage}={line['water'][stage]['Y']['band']:.2f}"
                f"{_MARK[line['water'][stage]['Y']['verdict']]}"
                for stage in IMAGE_STAGES
            )
            fused = line["water"]["fused"]["Y"]
            rows.append(
                f"{record['name']} {when} line{number}: first>{record['threshold']:.2f}="
                f"{line['first_stage_over_threshold']} "
                f"attributed={line['attributed_stage']} fused fwhm={fused['fwhm_px']:.1f}px "
                f"({fused['fwhm_sigma']:.2f} sigma) abs={fused['band_abs']:.3f}"
                f"{' WEAK-EDGE' if fused['weak_edge'] else ''} | {bands} | "
                f"render_check={frame['render_check_equal']}"
            )
    return "\n".join(rows)


_MARK = {"band": "*", "undecided": "?", "none": ""}
"""The summary's mark after a band: qualifies (``*``), undecided (``?``) or neither."""


if __name__ == "__main__":
    sys.exit(main())
