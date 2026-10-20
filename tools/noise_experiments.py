"""WP1.4b: the gain-cap noise test and the deep-frame statistics (spec v0.5.3).

Usage::

    uv run python tools/noise_experiments.py extract
    uv run python tools/noise_experiments.py grid [--frame STEM] [--limit N] [--device gpu|cpu]
    uv run python tools/noise_experiments.py smoothing [--device gpu|cpu]
    uv run python tools/noise_experiments.py lighting-step [--device gpu|cpu]
    uv run python tools/noise_experiments.py summarise

``extract`` re-extracts, at full resolution as 16-bit PNG, the 8 deepest frames of WP1.3D's
``work/wp1.3d/deep-frames.json`` (key ``deepest``), its open-water candidates (case
``open-blue-water``) and one shallow reference (``GX011627`` at the WP1.3 flicker excerpt's
first pts), and attaches to each frame the camera state of its chapter's GPMF track
(:mod:`camera_state`). ``grid`` corrects each frame under every setting of
:func:`settings_grid` (claim 3), one frame per pass, with the frame's own unsmoothed
statistics, and records per render the pipeline's own compensation and white-balance
records, what bound, the N{} bounds, the noise figures and the residual cast; it writes the
owner's crops (claim 6). ``smoothing`` runs claim 10 on the WP1.3D deep clip;
``lighting-step`` runs claim 10b on the same clip widened backwards (:func:`run_lighting_step`).
``summarise`` assembles ``grid.json``, the tables of claims 7-9 (``summary.json``) and the
crop page ``index.html``.

The noise measure (claim 4, as ruled by the orchestrator on the 2026-10-19 STOP): the primary
``sigma`` is Immerkaer's fast estimator (:func:`immerkaer_sigma`) per 64x64 tile, taken as the
median over a FIXED set of tiles. The brief's Donoho estimate ``median(|HH1|) / 0.6745``
(:func:`donoho_sigma`; HH1 the finest diagonal detail of the orthonormal Haar transform,
``(a - b - c + d) / 2`` on each 2x2 block) is kept as the cross-check, with the fraction of
exactly-zero HH1 coefficients recorded beside it: on the deep 8-bit HEVC frames most of those
coefficients are 0 in the flat tiles, and the median collapses to 0. Two tile sets serve every
setting of a frame (:func:`tile_sets`): ``flat``, the quarter of the full tiles with the lowest
gradient energy of the SOURCE frame's BT.709 luma (:func:`flat_tiles`), and ``red_lit``, the
quarter of the tiles whose SOURCE red mean is at least 16/255 with the lowest such energy
(:func:`red_lit_tiles`), reported only when it holds at least :data:`MIN_TILES` tiles. Settings
are compared on the absolute output sigma in 8-bit code values; the amplification over the
source is recorded only where the source figure is above 0.

Every output goes under ``<working folder>/wp1.4b`` through the checked writer of
:class:`lookcheck.frames.OutputRoots`; the footage is only read.
"""

from __future__ import annotations

import argparse
import dataclasses
import html
import io
import itertools
import json
import math
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray
from PIL import Image as PILImage

if not __package__:
    # Script mode: sys.path[0] is tools/, which holds the lookcheck, prototype and
    # local_config modules.
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import camera_state
from local_config import LocalConfig, find_footage_file, load_local_config
from lookcheck import pack
from lookcheck.frames import (
    ExtractError,
    FrameFile,
    OutputRoots,
    excerpt,
    extract,
    read_png16,
    run_ffprobe,
    run_tool,
    to_uint8,
)
from prototype import temporal
from prototype.backend import Backend, select_backend
from prototype.params import Params
from prototype.pipeline import Result, correct
from prototype.temporal import Series, Smoother

WORK_SUBDIR = "wp1.4b"
"""The folder inside the working folder that every output goes to."""

DEEP_FRAMES = Path("wp1.3d") / "deep-frames.json"
"""WP1.3D's frame list, relative to the working folder (read only)."""

DEEP_CLIP_STATISTICS = Path("wp1.3d") / "clip" / "statistics.json"
"""WP1.3D's deep clip record, relative to the working folder (read only)."""

SHALLOW_REFERENCE = ("GX011627", 205205, Fraction(1, 30000))
"""The shallow reference: chapter, pts in ticks, time base (the WP1.3 flicker excerpt's
first frame)."""

DEEP_COUNT = 8
"""The number of deep frames the brief requires."""

TILE = 64
"""The side of a noise tile in pixels."""

FLAT_FRACTION = 0.25
"""The fraction of the full tiles, lowest source-luma gradient energy first, that is measured."""

RED_FLOOR = 16.0 / 255.0
"""The source red tile mean a ``red_lit`` tile needs, so that a red baseline exists."""

MIN_TILES = 8
"""The fewest tiles a ``red_lit`` set may hold; a frame with fewer reports none."""

DONOHO_CONSTANT = 0.6745
"""The median of ``|N(0, 1)|``: ``median(|HH1|) / 0.6745`` estimates the noise sigma."""

LUMA_709 = (0.2126, 0.7152, 0.0722)
"""BT.709 luma weights of the gradient-energy selection."""

CROP = 512
"""The side of an owner crop in pixels (at 100 %)."""

RED_CAPS: tuple[float | None, ...] = (None, 0.5, 1.0, 2.0)
"""The Ancuti 2018 red gain caps of the grid (``None`` = off; 2.0 is the default)."""

CLAMPS: tuple[float, ...] = (1.5, 2.0, 3.0, 5.0, 1000.0)
"""The white-balance clamps of the grid (3.0 is the default; 1000 is effectively none)."""

DEFAULT_CAP = 2.0
DEFAULT_CLAMP = 3.0

SMOOTHER = Smoother("gaussian", 2.0)
"""Claim 10's filter: the 2.0 s centred Gaussian."""

CAP_BINDING_FLOOR = 0.10
"""Claim 10 stops when the cap binds on fewer than this fraction of the clip's frames."""


def setting_label(params: Params) -> str:
    """Return the grid label of a parameter set: method, then the cap (Ancuti) and the clamp.

    Args:
        params: The parameter set.

    Returns:
        ``"ancuti2018 cap=off clamp=3"``, ``"c3 clamp=1000"``, ...
    """
    clamp = f"clamp={params.max_white_balance_gain:g}"
    if params.method == "c3":
        return f"c3 {clamp}"
    cap = "off" if params.red_gain_cap is None else f"{params.red_gain_cap:g}"
    return f"ancuti2018 cap={cap} {clamp}"


@dataclass(frozen=True)
class Setting:
    """One setting of the grid.

    Attributes:
        label: :func:`setting_label` of ``params``.
        params: The parameter set the render runs with.
    """

    label: str
    params: Params


def settings_grid() -> tuple[Setting, ...]:
    """Return the 25 settings of claim 3, each labelled from the ``Params`` it runs with.

    Ancuti 2018 with blue compensation off, at the defaults except the red gain cap
    (:data:`RED_CAPS`) and the white-balance clamp (:data:`CLAMPS`): 20 settings; then 3C at
    the defaults with the same five clamps: 5 settings.

    Returns:
        The settings, Ancuti 2018 first (cap-major), then 3C.
    """
    out: list[Setting] = []
    for cap in RED_CAPS:
        for clamp in CLAMPS:
            params = Params(
                method="ancuti2018",
                blue_compensation=False,
                red_gain_cap=cap,
                max_white_balance_gain=clamp,
            )
            out.append(Setting(setting_label(params), params))
    for clamp in CLAMPS:
        params = Params(method="c3", max_white_balance_gain=clamp)
        out.append(Setting(setting_label(params), params))
    return tuple(out)


DEFAULT_SETTINGS = (
    setting_label(Params(method="ancuti2018", blue_compensation=False)),
    setting_label(Params(method="c3")),
)
"""The two settings at the defaults (claim 9's open-water frames run these only)."""

CROP_SETTINGS = (
    "ancuti2018 cap=off clamp=3",
    "ancuti2018 cap=2 clamp=3",
    "ancuti2018 cap=0.5 clamp=3",
    "ancuti2018 cap=2 clamp=1.5",
    "ancuti2018 cap=2 clamp=1000",
    "c3 clamp=3",
    "c3 clamp=1000",
)
"""The seven settings of the owner's crops (claim 6), in page order."""


# --- the noise measure ----------------------------------------------------------------------------


def tile_grid(shape: tuple[int, ...], size: int = TILE) -> tuple[int, int]:
    """Return the number of full ``size x size`` tiles down and across, from the top left.

    Args:
        shape: The image shape; the first two entries are height and width.
        size: The tile side.

    Returns:
        Rows and columns of full tiles (a partial tile at the right or bottom is not used).
    """
    return shape[0] // size, shape[1] // size


def _tiles(channel: NDArray[Any], size: int) -> NDArray[np.float64]:
    """Return every full tile of a 2-D array, shape ``(rows, cols, size, size)``, in float64."""
    rows, cols = tile_grid(channel.shape, size)
    cropped = np.asarray(channel[: rows * size, : cols * size], dtype=np.float64)
    return cropped.reshape(rows, size, cols, size).transpose(0, 2, 1, 3)


def luma(image: NDArray[np.float32]) -> NDArray[np.float64]:
    """Return the BT.709 luma of a display-encoded RGB image, in float64.

    Args:
        image: RGB, shape ``(H, W, 3)``.

    Returns:
        ``0.2126 R + 0.7152 G + 0.0722 B``, shape ``(H, W)``.
    """
    weights = np.asarray(LUMA_709, dtype=np.float64)
    out: NDArray[np.float64] = np.asarray(image, dtype=np.float64) @ weights
    return out


def gradient_energy(channel: NDArray[Any], size: int = TILE) -> NDArray[np.float64]:
    """Return each full tile's gradient energy: the mean of ``dx^2 + dy^2`` inside the tile.

    ``dx`` and ``dy`` are forward differences between neighbours that both lie in the tile,
    so a tile's energy never sees its neighbours.

    Args:
        channel: A 2-D array (the source luma).
        size: The tile side.

    Returns:
        Shape ``(rows, cols)``.
    """
    tiles = _tiles(channel, size)
    dx = np.diff(tiles, axis=3)
    dy = np.diff(tiles, axis=2)
    out: NDArray[np.float64] = (dx**2).mean(axis=(2, 3)) + (dy**2).mean(axis=(2, 3))
    return out


def flat_tiles(
    image: NDArray[np.float32], fraction: float = FLAT_FRACTION, size: int = TILE
) -> NDArray[np.int64]:
    """Return the fixed tile set: the ``fraction`` of full tiles of lowest luma gradient energy.

    The count is ``max(1, round(fraction * tiles))``; ties are broken by tile order (row-major),
    so the set is deterministic.

    Args:
        image: The SOURCE frame, RGB ``(H, W, 3)`` (or a 2-D luma).
        fraction: The fraction kept.
        size: The tile side.

    Returns:
        ``(k, 2)`` tile coordinates ``(row, col)``, flattest first.

    Raises:
        ValueError: The image holds no full tile.
    """
    plane = luma(image) if image.ndim == 3 else np.asarray(image, dtype=np.float64)
    energy = gradient_energy(plane, size)
    if energy.size == 0:
        raise ValueError(f"a {plane.shape[1]}x{plane.shape[0]} image holds no {size}px tile")
    count = max(1, round(fraction * energy.size))
    order = np.argsort(energy, axis=None, kind="stable")[:count]
    rows, cols = np.unravel_index(order, energy.shape)
    return np.stack([rows, cols], axis=1).astype(np.int64)


def red_lit_tiles(
    image: NDArray[np.float32],
    fraction: float = FLAT_FRACTION,
    floor: float = RED_FLOOR,
    size: int = TILE,
) -> tuple[NDArray[np.int64], int]:
    """Return the second fixed tile set: the flattest ``fraction`` of the red-lit tiles.

    A tile is red-lit when its SOURCE red mean is at least ``floor``. Of those, the
    ``round(fraction * eligible)`` tiles of lowest luma gradient energy are kept (ties by tile
    order, row-major); there is no minimum of one, so a frame without red-lit tiles gets none.

    Args:
        image: The SOURCE frame, RGB ``(H, W, 3)``.
        fraction: The fraction of the red-lit tiles kept.
        floor: The red tile mean a tile needs.
        size: The tile side.

    Returns:
        ``(k, 2)`` tile coordinates ``(row, col)``, flattest first, and the number of red-lit
        tiles they were chosen from.
    """
    energy = gradient_energy(luma(image), size)
    red = _tiles(image[..., 0], size).mean(axis=(2, 3))
    eligible = red >= floor
    count = round(fraction * int(eligible.sum()))
    order = np.argsort(np.where(eligible, energy, np.inf), axis=None, kind="stable")[:count]
    rows, cols = np.unravel_index(order, energy.shape)
    return np.stack([rows, cols], axis=1).astype(np.int64), int(eligible.sum())


TileSets = dict[str, NDArray[np.int64] | None]
"""A frame's fixed tile sets by name; ``None`` marks a set with too few tiles."""


def tile_sets(image: NDArray[np.float32]) -> tuple[TileSets, dict[str, Any]]:
    """Return a SOURCE frame's two fixed tile sets and a record of how they were formed.

    Args:
        image: The SOURCE frame, RGB ``(H, W, 3)``.

    Returns:
        ``{"flat": ..., "red_lit": ...}`` (``red_lit`` is ``None`` when it holds fewer than
        :data:`MIN_TILES` tiles), and per set its size, the tiles it was chosen from and its
        coordinates.
    """
    flat = flat_tiles(image)
    lit, eligible = red_lit_tiles(image)
    sets: TileSets = {"flat": flat, "red_lit": lit if len(lit) >= MIN_TILES else None}
    rows, cols = tile_grid(image.shape)
    record = {
        "size": TILE,
        "fraction": FLAT_FRACTION,
        "flat": {"count": len(flat), "chosen_from": rows * cols, "rows_cols": flat.tolist()},
        "red_lit": {
            "floor_8bit": RED_FLOOR * 255.0,
            "count": len(lit),
            "chosen_from": eligible,
            "too_few": len(lit) < MIN_TILES,
            "rows_cols": lit.tolist(),
        },
    }
    return sets, record


def _selected(channel: NDArray[Any], tiles: NDArray[np.int64], size: int) -> NDArray[np.float64]:
    """Return the selected tiles of a 2-D array, shape ``(k, size, size)``, float64."""
    out: NDArray[np.float64] = _tiles(channel, size)[tiles[:, 0], tiles[:, 1]]
    return out


def haar_hh1(blocks: NDArray[np.float64]) -> NDArray[np.float64]:
    """Return the finest diagonal Haar detail of each tile: ``(a - b - c + d) / 2`` per 2x2 block.

    With ``a b / c d`` the block's top-left, top-right, bottom-left and bottom-right pixels;
    this is the orthonormal Haar HH coefficient, so white noise of sigma ``s`` gives
    coefficients of sigma ``s``, and any plane (a linear gradient) gives exactly 0.

    Args:
        blocks: Tiles, shape ``(k, size, size)`` with an even ``size``.

    Returns:
        Shape ``(k, size / 2, size / 2)``.
    """
    a = blocks[:, 0::2, 0::2]
    b = blocks[:, 0::2, 1::2]
    c = blocks[:, 1::2, 0::2]
    d = blocks[:, 1::2, 1::2]
    out: NDArray[np.float64] = (a - b - c + d) / 2.0
    return out


def donoho_sigma(channel: NDArray[Any], tiles: NDArray[np.int64], size: int = TILE) -> float:
    """The cross-check: the median over the tiles of ``median(|HH1|) / 0.6745`` (Donoho).

    It reads 0 when more than half of a tile's HH1 coefficients are exactly 0, as in the flat
    regions of 8-bit HEVC frames (:func:`hh1_zero_fraction`).

    Args:
        channel: A 2-D array, values in [0, 1] (one colour channel).
        tiles: The fixed tile set (:func:`flat_tiles` of the source).
        size: The tile side.

    Returns:
        The noise sigma estimate on [0, 1] (multiply by 255 for 8-bit code values).
    """
    detail = np.abs(haar_hh1(_selected(channel, tiles, size)))
    per_tile = np.median(detail.reshape(len(tiles), -1), axis=1) / DONOHO_CONSTANT
    return float(np.median(per_tile))


def hh1_zero_fraction(channel: NDArray[Any], tiles: NDArray[np.int64], size: int = TILE) -> float:
    """Return the fraction of the tiles' HH1 coefficients that are exactly 0.

    Above one half, the Donoho median of a tile is 0 (:func:`donoho_sigma`).

    Args:
        channel: A 2-D array.
        tiles: The fixed tile set.
        size: The tile side.

    Returns:
        The fraction, over every coefficient of every tile.
    """
    return float(np.mean(haar_hh1(_selected(channel, tiles, size)) == 0.0))


_IMMERKAER = np.array([[1.0, -2.0, 1.0], [-2.0, 4.0, -2.0], [1.0, -2.0, 1.0]])


def immerkaer_sigma(channel: NDArray[Any], tiles: NDArray[np.int64], size: int = TILE) -> float:
    """The primary noise measure: Immerkaer's fast estimator per tile, median over the tiles.

    Per tile, ``sqrt(pi / 2) / (6 (W - 2) (H - 2)) * sum |I * N|`` over the tile's interior,
    ``N = [[1, -2, 1], [-2, 4, -2], [1, -2, 1]]`` (J. Immerkaer, "Fast Noise Variance
    Estimation", CVIU 64(2), 1996).

    Args:
        channel: A 2-D array, values in [0, 1].
        tiles: The fixed tile set.
        size: The tile side.

    Returns:
        The noise sigma estimate on [0, 1].
    """
    blocks = _selected(channel, tiles, size)
    response = np.zeros((len(tiles), size - 2, size - 2), dtype=np.float64)
    for dy in range(3):
        for dx in range(3):
            response += _IMMERKAER[dy, dx] * blocks[:, dy : dy + size - 2, dx : dx + size - 2]
    scale = math.sqrt(math.pi / 2.0) / (6.0 * (size - 2) * (size - 2))
    per_tile = scale * np.abs(response).sum(axis=(1, 2))
    return float(np.median(per_tile))


def crop_windows(
    image: NDArray[np.float32], tiles: NDArray[np.int64], crop: int = CROP, size: int = TILE
) -> dict[str, tuple[int, int]]:
    """Return the top-left corners of the flattest and the most textured crop.

    Windows of ``crop`` pixels are aligned to the tile grid. The flattest holds the most tiles
    of the fixed set (ties: the lower mean luma gradient energy); the most textured has the
    highest mean gradient energy.

    Args:
        image: The source frame.
        tiles: The fixed tile set.
        crop: The crop side (a multiple of ``size``).
        size: The tile side.

    Returns:
        ``{"flat": (y, x), "textured": (y, x)}`` in pixels.
    """
    energy = gradient_energy(luma(image), size)
    span = crop // size
    member = np.zeros(energy.shape, dtype=np.float64)
    member[tiles[:, 0], tiles[:, 1]] = 1.0
    best_flat: tuple[float, float, int, int] | None = None
    best_busy: tuple[float, int, int] | None = None
    for row in range(energy.shape[0] - span + 1):
        for col in range(energy.shape[1] - span + 1):
            count = float(member[row : row + span, col : col + span].sum())
            mean = float(energy[row : row + span, col : col + span].mean())
            if best_flat is None or (-count, mean) < best_flat[:2]:
                best_flat = (-count, mean, row, col)
            if best_busy is None or mean > best_busy[0]:
                best_busy = (mean, row, col)
    assert best_flat is not None and best_busy is not None
    return {
        "flat": (best_flat[2] * size, best_flat[3] * size),
        "textured": (best_busy[1] * size, best_busy[2] * size),
    }


# --- one render's record --------------------------------------------------------------------------


def channel_means(image: NDArray[np.float32]) -> tuple[float, float, float]:
    """Return the R, G, B means of an image, accumulated in float64."""
    means = np.asarray(image).reshape(-1, 3).mean(axis=0, dtype=np.float64)
    return float(means[0]), float(means[1]), float(means[2])


def _ratio(value: float, reference: float) -> float | None:
    """``value / reference``, or ``None`` when the reference is 0 (no measurable source noise)."""
    return value / reference if reference > 0.0 else None


def sigma_figures(channel: NDArray[Any], tiles: NDArray[np.int64]) -> dict[str, float]:
    """Return one channel's noise figures on one tile set.

    Args:
        channel: A 2-D array, values in [0, 1].
        tiles: The fixed tile set.

    Returns:
        ``immerkaer`` (primary) and ``donoho`` (cross-check) on [0, 1], both x 255
        (``*_8bit``), and ``hh1_zero_fraction``.
    """
    immerkaer = immerkaer_sigma(channel, tiles)
    donoho = donoho_sigma(channel, tiles)
    return {
        "immerkaer": immerkaer,
        "immerkaer_8bit": immerkaer * 255.0,
        "donoho": donoho,
        "donoho_8bit": donoho * 255.0,
        "hh1_zero_fraction": hh1_zero_fraction(channel, tiles),
    }


def noise_figures(
    channel: NDArray[Any],
    sets: Mapping[str, NDArray[np.int64] | None],
    source: Mapping[str, Mapping[str, float] | None],
) -> dict[str, dict[str, float | None] | None]:
    """Return an output channel's noise figures on each tile set, with the amplification.

    Args:
        channel: The output's channel.
        sets: The frame's fixed tile sets (:func:`tile_sets`).
        source: Per set, the source channel's :func:`sigma_figures` (``None`` for a set with
            too few tiles).

    Returns:
        Per set (``None`` for a set with too few tiles), :func:`sigma_figures` plus
        ``immerkaer_amplification`` and ``donoho_amplification``: the output figure divided by
        the source's, ``None`` when the source figure is 0.
    """
    out: dict[str, dict[str, float | None] | None] = {}
    for name, tiles in sets.items():
        reference = source[name]
        if tiles is None or reference is None:
            out[name] = None
            continue
        figures: dict[str, float | None] = dict(sigma_figures(channel, tiles))
        for kind in ("immerkaer", "donoho"):
            value = figures[kind]
            assert value is not None
            figures[f"{kind}_amplification"] = _ratio(value, reference[kind])
        out[name] = figures
    return out


def source_noise(
    image: NDArray[np.float32], sets: Mapping[str, NDArray[np.int64] | None]
) -> dict[str, dict[str, dict[str, float]] | None]:
    """Return the SOURCE frame's noise figures per tile set and channel.

    Args:
        image: The source frame.
        sets: Its fixed tile sets.

    Returns:
        Per set (``None`` for a set with too few tiles), per channel ``R``, ``G``, ``B``,
        :func:`sigma_figures`.
    """
    return {
        name: None
        if tiles is None
        else {c: sigma_figures(image[..., k], tiles) for k, c in enumerate("RGB")}
        for name, tiles in sets.items()
    }


def green_fraction(compensation: Mapping[str, Any]) -> float | None:
    """Return the share of the compensated red mean that came from the green term (Ancuti).

    ``mean_added.red / (channel_means.R + mean_added.red)``, both from the pipeline's own
    compensation record (``mean_added`` is measured after the clip to [0, 1]).

    Args:
        compensation: ``dataclasses.asdict`` of the record.

    Returns:
        The fraction, or ``None`` for 3C (which has no green term).
    """
    if compensation["method"] != "ancuti2018":
        return None
    added = float(compensation["mean_added"]["red"])
    return added / (float(compensation["channel_means"][0]) + added)


def render_record(
    result: Result,
    backend: Backend,
    sets: Mapping[str, NDArray[np.int64] | None],
    source_red: Mapping[str, Mapping[str, float] | None],
) -> dict[str, Any]:
    """Record one render (claims 3-5): what the pipeline did and bound, the noise, the cast.

    The compensation and white-balance records, the bound flags and the N{} bounds are
    :func:`lookcheck.pack.statistics_record`'s (the pipeline's own records; a cap binds when
    the effective alpha is below the requested one, the clamp when the record says so).

    Args:
        result: The pipeline's result (host arrays).
        backend: The backend it ran on.
        sets: The source frame's fixed tile sets (:func:`tile_sets`).
        source_red: Per set, the source red channel's :func:`sigma_figures`.

    Returns:
        A JSON-ready record.
    """
    stats = pack.statistics_record(result, backend)
    compensation = stats["compensation"]
    balance = stats["white_balance"]
    low, high = stats["normalisation"]["low"], stats["normalisation"]["high"]
    means = channel_means(result.output)
    return {
        "label": setting_label(result.params),
        "params": stats["params"],
        "effective_alpha": compensation["effective"].get("red"),
        "requested_alpha": compensation["requested"].get("red"),
        "cap": {
            "red": result.params.red_gain_cap if result.params.method == "ancuti2018" else None,
            "blue": (
                result.params.blue_gain_cap
                if result.params.method == "ancuti2018" and result.params.blue_compensation
                else None
            ),
        },
        "bound": stats["bound"],
        "white_balance": {
            "gray_world_gains": balance["gray_world_gains"],
            "requested_gains": balance["requested_gains"],
            "applied_gains": balance["applied_gains"],
            "clamped": balance["clamped"],
        },
        "compensation": compensation,
        "green_fraction": green_fraction(compensation),
        "normalisation": {
            "low": low,
            "high": high,
            "range": high - low,
            "stretch": (1.0 / (high - low)) if high > low else None,
            "collapsed": stats["normalisation"]["collapsed"],
        },
        "noise_red": noise_figures(result.output[..., 0], sets, source_red),
        "residual_cast": {"R/G": means[0] / means[1], "B/G": means[2] / means[1]},
        "output_means": list(means),
    }


# --- frames and footage ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Wanted:
    """A frame to extract.

    Attributes:
        name: The frame's name in WP1.3D's list (``<chapter>_<pts seconds>``).
        chapter: The source chapter's stem.
        pts_ticks: The frame's pts in ticks of ``time_base``.
        time_base: Seconds per tick.
        role: ``"deep"``, ``"open-water"`` or ``"shallow"``.
        extra: The list's own entry (rank, D, W, H...), kept in the record.
    """

    name: str
    chapter: str
    pts_ticks: int
    time_base: Fraction
    role: str
    extra: dict[str, Any]


def wanted_frames(deep_frames: Mapping[str, Any]) -> list[Wanted]:
    """Return the frames of claims 2 and 9: the 8 deepest, the open-water candidates, the shallow.

    Args:
        deep_frames: WP1.3D's ``deep-frames.json``.

    Returns:
        The frames, deep first (rank order), then open water (rank order), then the shallow
        reference.

    Raises:
        ValueError: The list holds fewer than 8 deep frames (a STOP of the brief).
    """
    deepest = deep_frames.get("deepest", [])
    if len(deepest) < DEEP_COUNT:
        raise ValueError(f"deep-frames.json holds {len(deepest)} deep frames, not {DEEP_COUNT}")
    out: list[Wanted] = []
    for role, entries in (
        ("deep", deepest[:DEEP_COUNT]),
        ("open-water", deep_frames["cases"]["open-blue-water"]["frames"]),
    ):
        for entry in entries:
            out.append(
                Wanted(
                    name=entry["frame"],
                    chapter=entry["chapter"],
                    pts_ticks=int(entry["pts_ticks"]),
                    time_base=Fraction(entry["time_base"]),
                    role=role,
                    extra=dict(entry),
                )
            )
    chapter, ticks, base = SHALLOW_REFERENCE
    out.append(Wanted(f"{chapter}@{ticks}", chapter, ticks, base, "shallow", {}))
    return out


CameraState = tuple[dict[str, list[tuple[float, ...]]], float, int]
"""A chapter's camera-state samples, its gpmd stream duration and index."""


def gpmd_stream(video: Path) -> tuple[int, float]:
    """Return the index and the duration in seconds of a chapter's GPMF (``gpmd``) stream.

    Args:
        video: The chapter (read only).

    Returns:
        The stream index and its duration.

    Raises:
        ExtractError: The probe fails or the chapter has no ``gpmd`` stream.
    """
    probe = run_ffprobe(["-show_entries", "stream=index,codec_tag_string,duration", str(video)])
    for stream in probe.get("streams", []):
        if stream.get("codec_tag_string") == "gpmd":
            return int(stream["index"]), float(stream["duration"])
    raise ExtractError(f"{video.name} has no gpmd stream")


def chapter_camera_state(video: Path, roots: OutputRoots) -> CameraState:
    """Copy a chapter's GPMF track into ``gpmd/`` (once) and read its camera state.

    The copy holds GPS as well; it stays in the working folder and is never committed.

    Args:
        video: The chapter (read only).
        roots: The output roots.

    Returns:
        The six keys' samples, the stream duration and the stream index.

    Raises:
        ExtractError: The probe or the copy fails.
    """
    index, duration = gpmd_stream(video)
    target = roots.check(roots.allowed / "gpmd" / f"{video.stem}.bin")
    if not target.is_file():
        roots.mkdir(target.parent)
        partial = roots.check(target.with_suffix(".part"))
        command = [
            "ffmpeg", "-nostdin", "-hide_banner", "-v", "error", "-y", "-i", str(video),
            "-map", f"0:{index}", "-codec", "copy", "-f", "data", str(partial),
        ]  # fmt: skip
        completed = run_tool(command)
        if completed.returncode != 0 or not partial.is_file():
            raise ExtractError(f"gpmd copy of {video.name} failed: {completed.stderr[-300:]!r}")
        roots.rename(partial, target)
    return camera_state.read_track(target), duration, index


EXTRACT_LEAD_S = 1e-4
"""Extraction asks for the first frame at or after ``pts - EXTRACT_LEAD_S`` (well under one
frame period), so a float rounding of the exact pts can never pick the next frame; the
extracted pts is then checked against the list's."""


def frame_record(
    wanted: Wanted,
    config: LocalConfig,
    roots: OutputRoots,
    states: dict[str, CameraState],
) -> dict[str, Any]:
    """Extract one wanted frame at full resolution and record it with its camera state.

    Args:
        wanted: The frame.
        config: The local configuration.
        roots: The output roots.
        states: Camera states already read, by chapter (filled in here).

    Returns:
        The frame's ``frames.json`` entry.

    Raises:
        ExtractError: The extracted frame's pts differs from the wanted one.
    """
    video = find_footage_file(wanted.chapter, config.footage_path)
    seconds = float(wanted.pts_ticks * wanted.time_base) - EXTRACT_LEAD_S
    out_dir = roots.mkdir(roots.allowed / "frames")
    (frame,) = extract(video, [seconds], out_dir, roots=roots)
    if frame.pts_ticks * frame.time_base != wanted.pts_ticks * wanted.time_base:
        raise ExtractError(
            f"{wanted.name}: extracted pts {frame.pts_ticks} differs from the list's"
        )
    if wanted.chapter not in states:
        states[wanted.chapter] = chapter_camera_state(video, roots)
    state, duration, index = states[wanted.chapter]
    return {
        "name": wanted.name,
        "role": wanted.role,
        "listed": wanted.extra,
        "frame": frame.record(),
        "camera": {
            "gpmd_stream": index,
            "gpmd_duration_s": duration,
            "samples": {key: len(values) for key, values in state.items()},
            "state": camera_state.state_at(state, duration, float(frame.pts)),
        },
    }


def extract_frames(
    config: LocalConfig, roots: OutputRoots, log: Callable[[str], None] = print
) -> list[dict[str, Any]]:
    """Extract every wanted frame (:func:`wanted_frames`) and write ``frames.json``.

    Args:
        config: The local configuration (the working folder holds WP1.3D's list).
        roots: The output roots.
        log: Progress output.

    Returns:
        The frame records written to ``frames.json``.
    """
    listed = json.loads((config.working_path / DEEP_FRAMES).read_text(encoding="utf-8"))
    states: dict[str, CameraState] = {}
    records: list[dict[str, Any]] = []
    for wanted in wanted_frames(listed):
        records.append(frame_record(wanted, config, roots, states))
        log(f"extracted {wanted.role} {records[-1]['frame']['file']}")
    roots.write_text(roots.allowed / "frames.json", json.dumps(records, indent=1))
    return records


# --- the grid -------------------------------------------------------------------------------------


def free_device(backend: Backend) -> None:
    """Release the GPU memory pool between full-resolution renders (no-op on the CPU)."""
    if backend.name == "gpu":
        backend.xp.get_default_memory_pool().free_all_blocks()


def png8(array: NDArray[np.float32]) -> bytes:
    """Encode an RGB or gray array in [0, 1] as an 8-bit PNG (for the page)."""
    buffer = io.BytesIO()
    PILImage.fromarray(to_uint8(array)).save(buffer, format="PNG")
    return buffer.getvalue()


def write_crops(
    roots: OutputRoots,
    folder: Path,
    image: NDArray[np.float32],
    windows: Mapping[str, tuple[int, int]],
    tag: str,
) -> dict[str, dict[str, str]]:
    """Write the two crops of one image, each as RGB and as the red channel in grayscale.

    Args:
        roots: The output roots.
        folder: The frame's crop folder.
        image: The full-resolution image.
        windows: :func:`crop_windows`'s corners.
        tag: The file-name tag of the image (``source`` or a setting slug).

    Returns:
        Per window, the ``rgb`` and ``red`` file names.
    """
    names: dict[str, dict[str, str]] = {}
    for window, (y, x) in windows.items():
        part = image[y : y + CROP, x : x + CROP]
        rgb, red = f"{window}-{tag}-rgb.png", f"{window}-{tag}-red.png"
        roots.write_bytes(folder / rgb, png8(part))
        roots.write_bytes(folder / red, png8(np.ascontiguousarray(part[..., 0])))
        names[window] = {"rgb": rgb, "red": red}
    return names


def slug(label: str) -> str:
    """Return a file-name form of a setting label (``ancuti2018_cap-off_clamp-3``)."""
    return label.replace(" ", "_").replace("=", "-")


def run_frame(
    record: Mapping[str, Any],
    settings: Sequence[Setting],
    roots: OutputRoots,
    backend: Backend,
    log: Callable[[str], None] = print,
) -> dict[str, Any]:
    """Render one frame under the settings and record each render (claims 3-6).

    Each render uses the frame's own unsmoothed statistics. The full-resolution results are
    released after their figures and crops are written.

    Args:
        record: The frame's entry of ``frames.json``.
        settings: The settings to render.
        roots: The output roots.
        backend: Where the pipeline runs.
        log: Progress output.

    Returns:
        The frame's grid record (also written to ``grid/<name>.json``).
    """
    path = roots.allowed / "frames" / record["frame"]["file"]
    image = read_png16(path)
    sets, sets_record = tile_sets(image)
    source = source_noise(image, sets)
    source_red = {name: None if per is None else per["R"] for name, per in source.items()}
    flat = sets["flat"]
    assert flat is not None
    windows = crop_windows(image, flat)
    crop_dir = roots.allowed / "crops" / record["name"].replace("@", "_")
    crops: dict[str, Any] = {}
    if record["role"] != "open-water":
        crops["source"] = write_crops(roots, crop_dir, image, windows, "source")
    renders: list[dict[str, Any]] = []
    for setting in settings:
        started = time.monotonic()
        result = correct(image, setting.params, backend)
        entry = render_record(result, backend, sets, source_red)
        if entry["label"] != setting.label:
            raise ValueError(f"render labelled {entry['label']}, setting {setting.label}")
        if setting.label in CROP_SETTINGS and record["role"] != "open-water":
            crops[setting.label] = write_crops(
                roots, crop_dir, result.output, windows, slug(setting.label)
            )
        renders.append(entry)
        del result
        free_device(backend)
        log(f"  {setting.label}: sigma_R {entry['noise_red']['flat']['immerkaer_8bit']:.3f} "
            f"(8-bit) ({time.monotonic() - started:.1f} s)")  # fmt: skip
    frame_record = {
        "name": record["name"],
        "role": record["role"],
        "frame": record["frame"],
        "listed": record["listed"],
        "camera": record["camera"],
        "backend": backend.name,
        "tiles": sets_record,
        "source_noise": source,
        "source_means": list(channel_means(image)),
        "windows": {name: list(corner) for name, corner in windows.items()},
        "crops": crops,
        "renders": renders,
    }
    roots.write_text(
        roots.allowed / "grid" / f"{record['name'].replace('@', '_')}.json",
        json.dumps(frame_record, indent=1),
    )
    return frame_record


def run_grid(
    roots: OutputRoots,
    backend: Backend,
    only: str | None = None,
    limit: int | None = None,
    log: Callable[[str], None] = print,
) -> list[str]:
    """Run :func:`run_frame` on the frames not yet done, one at a time.

    Deep and shallow frames get all 25 settings; open-water frames only the two default
    settings (claim 9).

    Args:
        roots: The output roots.
        backend: Where the pipeline runs.
        only: Run this frame only (its name in ``frames.json``), even when done.
        limit: Stop after this many frames.
        log: Progress output.

    Returns:
        The names of the frames run.
    """
    records = json.loads((roots.allowed / "frames.json").read_text(encoding="utf-8"))
    grid = settings_grid()
    done: list[str] = []
    for record in records:
        target = roots.allowed / "grid" / f"{record['name'].replace('@', '_')}.json"
        if only is not None and record["name"] != only:
            continue
        if only is None and target.is_file():
            continue
        if limit is not None and len(done) >= limit:
            break
        chosen = (
            [s for s in grid if s.label in DEFAULT_SETTINGS]
            if record["role"] == "open-water"
            else list(grid)
        )
        log(f"{record['role']} {record['name']}: {len(chosen)} settings on {backend.name}")
        run_frame(record, chosen, roots, backend, log)
        done.append(record["name"])
    return done


# --- claim 10: the capped alpha under smoothing ---------------------------------------------------


def cap_statistic(image: NDArray[np.float32]) -> float:
    """Return the source-only cap statistic ``mean((1 - R) * G)``, as the pipeline forms it.

    The product is formed in float32 and averaged in float64, as
    :func:`prototype.pipeline.compensate_ancuti2018` does.

    Args:
        image: The (proxy) frame, NumPy float32.

    Returns:
        The statistic.
    """
    shape = (np.float32(1.0) - image[..., 0]) * image[..., 1]
    return float(shape.mean(dtype=np.float64))


def capped_alpha(means: Sequence[float], statistic: float, params: Params) -> float:
    """Return the red alpha after the gain cap, from the means and the cap statistic.

    The pipeline's rule (spec 6.3.1, D50, D100): with ``added = (mean_g - mean_r) * statistic``,
    ``alpha = min(params.alpha, red_gain_cap * mean_r / added)`` when the cap is on and
    ``added > 0``, else ``params.alpha``.

    Args:
        means: The R, G, B means.
        statistic: :func:`cap_statistic`.
        params: Uses ``alpha`` and ``red_gain_cap``.

    Returns:
        The effective alpha.
    """
    added_per_alpha = (means[1] - means[0]) * statistic
    alpha = params.alpha
    if params.red_gain_cap is not None and added_per_alpha > 0.0:
        alpha = min(alpha, params.red_gain_cap * means[0] / added_per_alpha)
    return alpha


def analyse_staged_derived_alpha(
    images: Sequence[NDArray[np.float32]],
    params: Params,
    smoother: Smoother,
    frame_rate: Fraction,
    backend: Backend | None = None,
) -> tuple[Series, dict[str, Series]]:
    """Claim 10 variant (B): smooth the means and the cap statistic, then derive the alpha.

    The compensation stage smooths the source channel means and the source-only cap
    statistic and derives each frame's alpha from the smoothed values (:func:`capped_alpha`);
    the white-balance and fusion stages then run exactly as in
    :func:`prototype.temporal.analyse_staged` (each measured with the smoothed earlier stages
    supplied, then smoothed), from ``temporal``'s public functions.

    Args:
        images: The proxies, in presentation order (NumPy).
        params: Ancuti 2018 with blue compensation off.
        smoother: The filter.
        frame_rate: Frames per second.
        backend: Where the steps run.

    Returns:
        The smoothed series of every stage, and per stage the measured (unsmoothed) series;
        the compensation stage's holds the raw means and ``cap_statistic``.

    Raises:
        ValueError: The method is not Ancuti 2018 with blue off.
    """
    if params.method != "ancuti2018" or params.blue_compensation:
        raise ValueError("variant B is defined for Ancuti 2018 red compensation only")
    names = ("compensation_means.R", "compensation_means.G", "compensation_means.B")
    raw_means = np.array([channel_means(image) for image in images], dtype=np.float64)
    statistic = np.array([cap_statistic(image) for image in images], dtype=np.float64)
    measured_means = {name: raw_means[:, k] for k, name in enumerate(names)}
    smoothed: Series = temporal.smooth(measured_means, smoother, frame_rate)
    smoothed_statistic = smoother.apply(statistic, frame_rate)
    smoothed["compensation_alpha.red"] = np.array(
        [
            capped_alpha([smoothed[name][k] for name in names], smoothed_statistic[k], params)
            for k in range(len(images))
        ],
        dtype=np.float64,
    )
    measured: dict[str, Series] = {
        "compensation": {**measured_means, "cap_statistic": statistic},
    }
    for stage in temporal.STAGES[params.method][1:]:
        records = [
            temporal.measure(image, params, temporal.at(smoothed, index), backend)
            for index, image in enumerate(images)
        ]
        stage_series = {
            name: values
            for name, values in temporal.stack(records).items()
            if name.split(".", 1)[0] in stage.fields
        }
        measured[stage.name] = stage_series
        smoothed.update(temporal.smooth(stage_series, smoother, frame_rate))
    return smoothed, measured


def clip_proxies(
    config: LocalConfig, roots: OutputRoots, log: Callable[[str], None] = print
) -> tuple[NDArray[np.float32], list[int], Fraction]:
    """Re-extract the WP1.3D deep clip by its pts and return its 540 NumPy proxies.

    The full-resolution PNGs are deleted once proxied; the proxies are cached as
    ``clip/proxies.npy`` with their pts.

    Args:
        config: The local configuration.
        roots: The output roots.
        log: Progress output.

    Returns:
        The proxies ``(frames, 540, 960, 3)``, their pts ticks and the frame rate.

    Raises:
        ExtractError: The re-extracted pts differ from WP1.3D's record.
    """
    record = json.loads((config.working_path / DEEP_CLIP_STATISTICS).read_text(encoding="utf-8"))
    window = record["excerpt"]
    expected = [int(frame["pts_ticks"]) for frame in record["variants"]["ancuti2018"]["frames"]]
    rate = Fraction(window["frame_rate"])
    folder = roots.mkdir(roots.allowed / "clip")
    cache = roots.check(folder / "proxies.npy")
    ticks_file = roots.check(folder / "proxies-pts.json")
    if cache.is_file() and ticks_file.is_file():
        cached = json.loads(ticks_file.read_text(encoding="utf-8"))
        if cached == expected:
            return np.load(cache), expected, rate
    video = find_footage_file(record["chapter"], config.footage_path)
    frames: list[FrameFile] = excerpt(
        video, window["start_s"], window["duration_s"], folder / "full", roots=roots
    )
    ticks = [frame.pts_ticks for frame in frames]
    if ticks != expected:
        raise ExtractError(f"re-extracted pts differ from WP1.3D's ({len(ticks)} frames)")
    stacked: list[NDArray[np.float32]] = []
    for frame in frames:
        stacked.append(temporal.proxy(read_png16(frame.path)))
        roots.remove(frame.path)
    proxies = np.stack(stacked)
    log(f"proxied {len(frames)} frames")
    buffer = io.BytesIO()
    np.save(buffer, proxies)
    roots.write_bytes(cache, buffer.getvalue())
    roots.write_text(ticks_file, json.dumps(ticks))
    return proxies, ticks, rate


def run_smoothing(
    config: LocalConfig,
    roots: OutputRoots,
    backend: Backend,
    log: Callable[[str], None] = print,
) -> dict[str, Any]:
    """Claim 10: the capped alpha smoothed as a value (A) against derived from smoothed values (B).

    Args:
        config: The local configuration.
        roots: The output roots.
        backend: Where the steps run.
        log: Progress output.

    Returns:
        The record written to ``smoothing.json``.
    """
    proxies, ticks, rate = clip_proxies(config, roots, log)
    images = list(proxies)
    params = Params(method="ancuti2018", blue_compensation=False)
    raw = temporal.stack([temporal.statistics_of(image, params, backend) for image in images])
    raw_alpha = raw["compensation_alpha.red"]
    binding = int(np.sum(raw_alpha < params.alpha))
    record: dict[str, Any] = {
        "params": dataclasses.asdict(params),
        "smoother": {"kind": SMOOTHER.kind, "window_s": SMOOTHER.window_s},
        "frame_rate": f"{rate.numerator}/{rate.denominator}",
        "frames": len(images),
        "pts_ticks": ticks,
        "proxy": "temporal.proxy, exact 4x4 area mean in NumPy (960x540)",
        "backend": backend.name,
        "cap_binding_frames": binding,
        "cap_binding_fraction": binding / len(images),
        "alpha_raw": raw_alpha.tolist(),
    }
    if binding / len(images) < CAP_BINDING_FLOOR:
        record["stopped"] = (
            "the cap binds on fewer than 10 % of the frames; the question stays open"
        )
        roots.write_text(roots.allowed / "smoothing.json", json.dumps(record, indent=1))
        return record
    smoothed_a, _ = temporal.analyse_staged(images, params, SMOOTHER, rate, backend)
    smoothed_b, measured_b = analyse_staged_derived_alpha(images, params, SMOOTHER, rate, backend)
    reference = temporal.constant_statistics(raw)
    signals: dict[str, list[NDArray[np.float64]]] = {"A": [], "B": [], "reference": []}
    differences: list[float] = []
    for index, image in enumerate(images):
        out_a = temporal.render(image, params, temporal.at(smoothed_a, index), backend)
        out_b = temporal.render(image, params, temporal.at(smoothed_b, index), backend)
        out_r = temporal.render(image, params, reference, backend)
        signals["A"].append(temporal.frame_signals(out_a))
        signals["B"].append(temporal.frame_signals(out_b))
        signals["reference"].append(temporal.frame_signals(out_r))
        differences.append(float(np.abs(out_a - out_b).mean(dtype=np.float64)) * 255.0)
    ref = np.array(signals["reference"])
    flicker_a = temporal.flicker(np.array(signals["A"]), ref)
    flicker_b = temporal.flicker(np.array(signals["B"]), ref)
    alpha_a, alpha_b = smoothed_a["compensation_alpha.red"], smoothed_b["compensation_alpha.red"]
    record.update(
        {
            "alpha_A": alpha_a.tolist(),
            "alpha_B": alpha_b.tolist(),
            "cap_statistic_raw": measured_b["compensation"]["cap_statistic"].tolist(),
            "alpha_difference": {
                "mean_abs": float(np.mean(np.abs(alpha_a - alpha_b))),
                "max_abs": float(np.max(np.abs(alpha_a - alpha_b))),
            },
            "render_difference_8bit": {
                "mean_abs": float(np.mean(differences)),
                "max_frame": float(np.max(differences)),
                "per_frame": differences,
            },
            "flicker": {
                "A": {"value": flicker_a.value, "per_signal": flicker_a.per_signal},
                "B": {"value": flicker_b.value, "per_signal": flicker_b.per_signal},
            },
        }
    )
    pts = [tick / 30000 for tick in ticks]
    plot = pack.plot_series(
        {"alpha raw": raw_alpha.tolist(), "alpha A": alpha_a.tolist(), "alpha B": alpha_b.tolist()},
        pts,
    )
    roots.write_bytes(roots.allowed / "smoothing-alpha.png", plot)
    roots.write_text(roots.allowed / "smoothing.json", json.dumps(record, indent=1))
    return record


# --- claim 10b: the lighting step in the deep clip ------------------------------------------------

WIDEN_S = 3.0
"""Claim 10b: how far the deep clip's excerpt is widened backwards. More than the 2 s window's
reach (1 s each side), so the widened analysis holds no edge value anywhere in the original
excerpt's first second."""

SHORT_SMOOTHER = Smoother("gaussian", 0.5)
"""Claim 10b option (b): the shorter centred Gaussian."""

STEP_HALF_S = 0.5
"""The step detector compares the mean of this many seconds after a frame with the mean before."""

STEP_SPAN_S = 1.0
"""The size of a step in a series is its change from this long before the step to this long
after it; the step window for the peak figures is the same span on each side."""

STEP_KEYS = (
    "compensation_alpha.red",
    "white_balance_gains.R",
    "white_balance_gains.G",
    "white_balance_gains.B",
    "normalisation_bounds.low",
    "normalisation_bounds.high",
)
"""The applied statistics traced across the step (alpha for Ancuti 2018 only)."""


def lead_in_proxies(
    config: LocalConfig, roots: OutputRoots, log: Callable[[str], None] = print
) -> tuple[NDArray[np.float32], list[int]]:
    """Extract the :data:`WIDEN_S` seconds before the deep clip's excerpt as 540 NumPy proxies.

    The frames are the ones with pts in ``[start - WIDEN_S, start)``; their pts must run on
    without a gap into the excerpt's first frame. The full-resolution PNGs are deleted once
    proxied; the proxies are cached as ``clip/lead-in.npy`` with their pts.

    Args:
        config: The local configuration.
        roots: The output roots.
        log: Progress output.

    Returns:
        The proxies ``(frames, 540, 960, 3)`` and their pts ticks.

    Raises:
        ExtractError: The lead-in's pts are not contiguous with the excerpt's first frame.
    """
    record = json.loads((config.working_path / DEEP_CLIP_STATISTICS).read_text(encoding="utf-8"))
    window = record["excerpt"]
    first = int(window["first_pts_ticks"])
    folder = roots.mkdir(roots.allowed / "clip")
    cache = roots.check(folder / "lead-in.npy")
    ticks_file = roots.check(folder / "lead-in-pts.json")
    if cache.is_file() and ticks_file.is_file():
        return np.load(cache), json.loads(ticks_file.read_text(encoding="utf-8"))
    video = find_footage_file(record["chapter"], config.footage_path)
    frames = excerpt(video, window["start_s"] - WIDEN_S, WIDEN_S, folder / "lead-in", roots=roots)
    ticks = [frame.pts_ticks for frame in frames]
    steps = set(np.diff([*ticks, first]).tolist())
    if len(steps) != 1:
        raise ExtractError(f"the lead-in's pts do not run on into the excerpt: steps {steps}")
    stacked: list[NDArray[np.float32]] = []
    for frame in frames:
        stacked.append(temporal.proxy(read_png16(frame.path)))
        roots.remove(frame.path)
    proxies = np.stack(stacked)
    log(f"proxied {len(frames)} lead-in frames")
    buffer = io.BytesIO()
    np.save(buffer, proxies)
    roots.write_bytes(cache, buffer.getvalue())
    roots.write_text(ticks_file, json.dumps(ticks))
    return proxies, ticks


def detect_step(signal: NDArray[np.float64], frame_rate: Fraction) -> tuple[int, float]:
    """Locate the largest step of a source signal: the two-sided mean difference.

    For each frame ``k`` with ``m = round(STEP_HALF_S * frame_rate)`` frames on each side,
    ``d[k] = mean(signal[k : k + m]) - mean(signal[k - m : k])``; the step is at the ``k`` of
    largest ``|d|`` (the first such ``k`` on a tie).

    Args:
        signal: One value per frame (a source-only signal, e.g. the frame's mean luma).
        frame_rate: Frames per second.

    Returns:
        The index of the first frame after the step, and ``d`` there (signed).

    Raises:
        ValueError: The signal is shorter than two detector halves.
    """
    m = round(STEP_HALF_S * float(frame_rate))
    if len(signal) < 2 * m:
        raise ValueError(f"a step detector of {m} frames a side needs {2 * m} frames")
    cumulative = np.concatenate([[0.0], np.cumsum(np.asarray(signal, dtype=np.float64))])
    k = np.arange(m, len(signal) - m + 1)
    difference = (cumulative[k + m] - cumulative[k]) / m - (cumulative[k] - cumulative[k - m]) / m
    best = int(np.argmax(np.abs(difference)))
    return int(k[best]), float(difference[best])


def analyse_segments(
    images: Sequence[NDArray[np.float32]],
    params: Params,
    smoother: Smoother,
    frame_rate: Fraction,
    cuts: Sequence[int],
    backend: Backend | None = None,
) -> Series:
    """Option (a) of claim 10b: STAGED analysis with the window reset at each cut.

    Each segment between cuts is analysed on its own by
    :func:`prototype.temporal.analyse_staged`, so no smoothing window reaches across a cut
    (inside a segment the edge rule holds the segment's end values); the series are joined.

    Args:
        images: The proxies, in presentation order.
        params: The parameter set.
        smoother: The filter.
        frame_rate: Frames per second.
        cuts: The indices of the first frame of each new segment, increasing.
        backend: Where the steps run.

    Returns:
        The smoothed series over all the frames.
    """
    bounds = [0, *cuts, len(images)]
    parts = [
        temporal.analyse_staged(images[a:b], params, smoother, frame_rate, backend)[0]
        for a, b in itertools.pairwise(bounds)
    ]
    return {name: np.concatenate([part[name] for part in parts]) for name in parts[0]}


def step_figures(values: NDArray[np.float64], step: int, frame_rate: Fraction) -> dict[str, float]:
    """Return the size of a series' step: its change across the step and its largest jump.

    Args:
        values: One value per frame.
        step: The first frame after the step.
        frame_rate: Frames per second.

    Returns:
        ``change``: the value :data:`STEP_SPAN_S` after the step minus the value as long before
        it (indices clipped to the series); ``max_jump``: the largest frame-to-frame change
        inside that span; ``max_jump_at``: the frame it lands on.
    """
    span = round(STEP_SPAN_S * float(frame_rate))
    before, after = max(step - span, 0), min(step + span, len(values) - 1)
    jumps = np.abs(np.diff(values[before : after + 1]))
    at_jump = int(np.argmax(jumps))
    return {
        "change": float(values[after] - values[before]),
        "max_jump": float(jumps[at_jump]),
        "max_jump_at": before + at_jump + 1,
    }


STRETCH_KEY = "normalisation_stretch"
"""The derived series ``1 / (high - low)`` of the N{} bounds, traced with :data:`STEP_KEYS`."""


def traced(series: Mapping[str, NDArray[np.float64]]) -> Series:
    """Return the :data:`STEP_KEYS` a series holds, plus the N{} stretch (:data:`STRETCH_KEY`).

    Args:
        series: A raw or smoothed statistics series.

    Returns:
        The traced series.
    """
    out: Series = {key: series[key] for key in STEP_KEYS if key in series}
    out[STRETCH_KEY] = 1.0 / (
        series["normalisation_bounds.high"] - series["normalisation_bounds.low"]
    )
    return out


def signal_steps(
    signals: NDArray[np.float64],
    source: NDArray[np.float64] | None,
    step: int,
    frame_rate: Fraction,
) -> dict[str, dict[str, float | int | None]]:
    """Return the step of each frame signal (R, G, B, luma means) in 8-bit levels.

    Args:
        signals: :func:`prototype.temporal.frame_signals` per frame, shape ``(frames, 4)``.
        source: The source frames' signals, the same shape; ``None`` for the source itself.
        step: The first frame after the step.
        frame_rate: Frames per second.

    Returns:
        Per signal name, :func:`step_figures` with ``change`` and ``max_jump`` in 8-bit levels
        (``change_8bit``, ``max_jump_8bit``) and, against a source, ``change_over_source`` and
        ``max_jump_over_source`` (``|change|`` ratios; ``None`` where the source's is 0).
    """
    out: dict[str, dict[str, float | int | None]] = {}
    for k, name in enumerate(temporal.SIGNALS):
        figures = step_figures(signals[:, k], step, frame_rate)
        entry: dict[str, float | int | None] = {
            "change_8bit": figures["change"] * 255.0,
            "max_jump_8bit": figures["max_jump"] * 255.0,
            "max_jump_at": figures["max_jump_at"],
        }
        if source is not None:
            reference = step_figures(source[:, k], step, frame_rate)
            entry["change_over_source"] = _ratio(abs(figures["change"]), abs(reference["change"]))
            entry["max_jump_over_source"] = _ratio(figures["max_jump"], reference["max_jump"])
        out[name] = entry
    return out


def run_lighting_step(
    config: LocalConfig,
    roots: OutputRoots,
    backend: Backend,
    log: Callable[[str], None] = print,
) -> dict[str, Any]:
    """Claim 10b: the lighting step in the deep clip, edge effect first, then two remedies.

    On the 540 NumPy proxies of WP1.3D's deep clip, with the excerpt widened backwards by
    :data:`WIDEN_S` (:func:`lead_in_proxies`), for 3C and Ancuti 2018 (blue off) at the
    defaults, STAGED: the 2 s Gaussian on the original excerpt alone (``narrow``, what WP1.3D
    rendered) and on the widened sequence (``wide``), then on the widened sequence the window
    reset at the detected step (``reset``) and the 0.5 s Gaussian (``short``). Every option
    is evaluated on the original excerpt's frames: the applied statistics' step
    (:func:`step_figures`), the rendered frames' R, G, B and luma means across the step
    against the source's (:func:`signal_steps`), and the flicker measure
    (:func:`prototype.temporal.flicker`).

    Args:
        config: The local configuration.
        roots: The output roots.
        backend: Where the steps run.
        log: Progress output.

    Returns:
        The record written to ``lighting-step.json``.
    """
    proxies, ticks, rate = clip_proxies(config, roots, log)
    narrow = list(proxies)
    lead, lead_ticks = lead_in_proxies(config, roots, log)
    count = len(lead)
    wide = [*lead, *narrow]
    source = np.array([temporal.frame_signals(image) for image in wide])
    step_wide, size = detect_step(source[:, 3], rate)
    step = step_wide - count
    pts = [tick / 30000 for tick in ticks]
    record: dict[str, Any] = {
        "frame_rate": f"{rate.numerator}/{rate.denominator}",
        "excerpt_frames": len(narrow),
        "lead_in_frames": count,
        "lead_in_first_pts_ticks": lead_ticks[0],
        "excerpt_pts_ticks": [ticks[0], ticks[-1]],
        "detector": {"signal": "source mean luma", "half_s": STEP_HALF_S},
        "step": {
            "frame_in_excerpt": step,
            "pts_s": pts[step] if 0 <= step < len(pts) else None,
            "seconds_into_excerpt": pts[step] - pts[0] if 0 <= step < len(pts) else None,
            "luma_difference_8bit": size * 255.0,
        },
        "source_signals_8bit": {
            name: (source[count:, k] * 255.0).tolist() for k, name in enumerate(temporal.SIGNALS)
        },
        "source_step": signal_steps(source[count:], None, step, rate),
        "methods": {},
    }
    for params in (Params(method="c3"), Params(method="ancuti2018", blue_compensation=False)):
        log(f"{params.method}: analysing")
        raw = temporal.stack([temporal.statistics_of(image, params, backend) for image in narrow])
        reference = temporal.constant_statistics(raw)
        options: dict[str, Series] = {
            "narrow 2 s": temporal.analyse_staged(narrow, params, SMOOTHER, rate, backend)[0],
        }
        for name, series in (
            ("wide 2 s", temporal.analyse_staged(wide, params, SMOOTHER, rate, backend)[0]),
            (
                "wide 2 s reset at step",
                analyse_segments(wide, params, SMOOTHER, rate, [step_wide], backend),
            ),
            ("wide 0.5 s", temporal.analyse_staged(wide, params, SHORT_SMOOTHER, rate, backend)[0]),
        ):
            options[name] = {key: values[count:] for key, values in series.items()}
        traces = {name: traced(series) for name, series in (("raw", raw), *options.items())}
        keys = list(traces["raw"])
        ref_signals = np.array(
            [
                temporal.frame_signals(temporal.render(image, params, reference, backend))
                for image in narrow
            ]
        )
        method: dict[str, Any] = {
            "params": dataclasses.asdict(params),
            "raw_step": {key: step_figures(traces["raw"][key], step, rate) for key in keys},
            "raw": {key: traces["raw"][key].tolist() for key in keys},
            "options": {},
        }
        for name, series in options.items():
            log(f"  {name}: rendering")
            signals = np.array(
                [
                    temporal.frame_signals(
                        temporal.render(image, params, temporal.at(series, index), backend)
                    )
                    for index, image in enumerate(narrow)
                ]
            )
            measured = temporal.flicker(signals, ref_signals)
            method["options"][name] = {
                "applied_step": {key: step_figures(traces[name][key], step, rate) for key in keys},
                "applied": {key: traces[name][key].tolist() for key in keys},
                "rendered_step": signal_steps(signals, source[count:], step, rate),
                "rendered_signals_8bit": {
                    signal: (signals[:, k] * 255.0).tolist()
                    for k, signal in enumerate(temporal.SIGNALS)
                },
                "flicker": {"value": measured.value, "per_signal": measured.per_signal},
                "flicker_peak_step_8bit": float(measured.per_step.max()),
                "flicker_peak_at": int(np.argmax(measured.per_step.max(axis=1))) + 1,
            }
        edge: dict[str, Any] = {}
        first_second = round(float(rate))
        for key in keys:
            gap = np.abs(traces["narrow 2 s"][key] - traces["wide 2 s"][key])
            edge[key] = {
                "max_abs_difference_first_second": float(gap[:first_second].max()),
                "max_abs_difference_rest": float(gap[first_second:].max()),
                "applied_change_narrow": method["options"]["narrow 2 s"]["applied_step"][key][
                    "change"
                ],
                "applied_change_wide": method["options"]["wide 2 s"]["applied_step"][key]["change"],
            }
        method["edge_effect"] = edge
        record["methods"][params.method] = method
        plot = pack.plot_series(
            {
                f"{key} {name}": method["options"][name]["applied"][key]
                for key in keys
                for name in ("narrow 2 s", "wide 2 s")
            },
            pts,
        )
        roots.write_bytes(roots.allowed / f"lighting-step-{params.method}.png", plot)
    roots.write_text(roots.allowed / "lighting-step.json", json.dumps(record, indent=1))
    return record


# --- the summary ----------------------------------------------------------------------------------


def _spread(values: Sequence[float]) -> dict[str, float]:
    """Median, minimum and maximum."""
    return {
        "median": float(np.median(values)),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
    }


def rank_correlation(x: Sequence[float], y: Sequence[float]) -> float | None:
    """Spearman's rank correlation (average ranks for ties); ``None`` when a side is constant."""

    def ranks(values: Sequence[float]) -> NDArray[np.float64]:
        array = np.asarray(values, dtype=np.float64)
        order = np.argsort(array, kind="stable")
        out = np.empty(len(array), dtype=np.float64)
        out[order] = np.arange(len(array), dtype=np.float64)
        for value in np.unique(array):
            tied = array == value
            out[tied] = out[tied].mean()
        return out

    rx, ry = ranks(x), ranks(y)
    if np.ptp(rx) == 0.0 or np.ptp(ry) == 0.0:
        return None
    return float(np.corrcoef(rx, ry)[0, 1])


def discordant_pairs(first: Sequence[float], second: Sequence[float]) -> int:
    """Count the pairs the two sequences order differently (a tie in either one agrees)."""
    count = 0
    for i in range(len(first)):
        for j in range(i + 1, len(first)):
            if (first[i] - first[j]) * (second[i] - second[j]) < 0.0:
                count += 1
    return count


def _render(frame: Mapping[str, Any], label: str) -> Mapping[str, Any]:
    """Return a frame's render under a setting label."""
    for entry in frame["renders"]:
        if entry["label"] == label:
            return dict(entry)
    raise KeyError(f"{frame['name']} has no render {label}")


TILE_SETS = ("flat", "red_lit")
"""The names of the two fixed tile sets, in report order."""


def summarise(frames: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Compute the tables of claims 4 and 7-9 from the grid records.

    Noise figures are Immerkaer's (the primary measure) on each tile set: the absolute output
    ``sigma_out_8bit``, and the ``amplification`` over the source where the source figure is
    above 0 (``None`` otherwise, left out of the spreads). A frame whose ``red_lit`` set has too
    few tiles is left out of that set's spreads and counted in ``frames_without_set``.

    Args:
        frames: The per-frame grid records.

    Returns:
        The summary (JSON-ready).
    """
    deep = [frame for frame in frames if frame["role"] == "deep"]
    shallow = [frame for frame in frames if frame["role"] == "shallow"]
    water = [frame for frame in frames if frame["role"] == "open-water"]

    def row(frame: Mapping[str, Any], label: str, tile_set: str) -> dict[str, Any]:
        entry = _render(frame, label)
        noise = entry["noise_red"][tile_set]
        camera = frame["camera"]["state"]
        return {
            "frame": frame["name"],
            "sigma_out_8bit": None if noise is None else noise["immerkaer_8bit"],
            "amplification": None if noise is None else noise["immerkaer_amplification"],
            "donoho_8bit": None if noise is None else noise["donoho_8bit"],
            "red_gain": entry["white_balance"]["applied_gains"][0],
            "residual_RG": entry["residual_cast"]["R/G"],
            "residual_BG": entry["residual_cast"]["B/G"],
            "green_fraction": entry["green_fraction"],
            "effective_alpha": entry["effective_alpha"],
            "stretch": entry["normalisation"]["stretch"],
            "cap_bound": entry["bound"]["red_gain_cap"],
            "clamp_bound": entry["bound"]["white_balance_clamp"],
            "ISOE": camera.get("ISOE"),
            "WRGB_red": camera["WRGB"][0] if "WRGB" in camera else None,
        }

    def table(
        labels: Sequence[str], group: Sequence[Mapping[str, Any]], tile_set: str
    ) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for label in labels:
            rows = [row(frame, label, tile_set) for frame in group]
            cell: dict[str, Any] = {
                "frames": len(rows),
                "frames_without_set": sum(r["sigma_out_8bit"] is None for r in rows),
            }
            for key in ("sigma_out_8bit", "amplification", "red_gain", "residual_RG",
                        "residual_BG", "effective_alpha", "green_fraction",
                        "stretch"):  # fmt: skip
                values = [r[key] for r in rows if r[key] is not None]
                cell[key] = _spread(values) if values else None
            cell["amplification_frames"] = sum(r["amplification"] is not None for r in rows)
            cell["cap_bound_frames"] = sum(bool(r["cap_bound"]) for r in rows)
            cell["clamp_bound_frames"] = sum(any(r["clamp_bound"]) for r in rows)
            cell["clamp_bound_red_frames"] = sum(bool(r["clamp_bound"][0]) for r in rows)
            cell["per_frame"] = rows
            out[label] = cell
        return out

    clamp = f"{DEFAULT_CLAMP:g}"
    cap_labels = [
        f"ancuti2018 cap={'off' if cap is None else f'{cap:g}'} clamp={clamp}" for cap in RED_CAPS
    ] + [f"c3 clamp={clamp}"]
    gate4 = {
        tile_set: {
            "deep": table(cap_labels, deep, tile_set),
            "shallow": table(cap_labels, shallow, tile_set),
        }
        for tile_set in TILE_SETS
    }
    # Within each deep frame: does the tightest cap raise or lower the output red noise?
    tightest = min(cap for cap in RED_CAPS if cap is not None)
    loose_label, tight_label = cap_labels[0], f"ancuti2018 cap={tightest:g} clamp={clamp}"
    direction: dict[str, Any] = {}
    for tile_set in TILE_SETS:
        counts = {"raises": 0, "lowers": 0, "equal": 0, "no_set": 0}
        per_frame: dict[str, Any] = {}
        for frame in deep:
            loose, tight = row(frame, loose_label, tile_set), row(frame, tight_label, tile_set)
            if loose["sigma_out_8bit"] is None:
                counts["no_set"] += 1
                continue
            change = tight["sigma_out_8bit"] - loose["sigma_out_8bit"]
            verdict = "equal" if change == 0.0 else "raises" if change > 0.0 else "lowers"
            counts[verdict] += 1
            per_frame[frame["name"]] = {
                "sigma_cap_off_8bit": loose["sigma_out_8bit"],
                "sigma_cap_tight_8bit": tight["sigma_out_8bit"],
                "relative_change": _ratio(change, loose["sigma_out_8bit"]),
                "red_gain_cap_off": loose["red_gain"],
                "red_gain_cap_tight": tight["red_gain"],
                "alpha_cap_tight": tight["effective_alpha"],
                "verdict": verdict,
            }
        direction[tile_set] = {"tight": tight_label, "counts": counts, "per_frame": per_frame}
    tracking: dict[str, Any] = {}
    default_label = f"ancuti2018 cap={DEFAULT_CAP:g} clamp={clamp}"
    for tile_set in TILE_SETS:
        for label in (default_label, loose_label, f"c3 clamp={clamp}"):
            rows = [r for r in (row(frame, label, tile_set) for frame in deep)
                    if r["amplification"] is not None]  # fmt: skip
            amplification = [r["amplification"] for r in rows]
            tracking[f"{label} / {tile_set}"] = {
                "frames": len(rows),
                "vs_red_gain": rank_correlation(amplification, [r["red_gain"] for r in rows]),
                "vs_stretch": rank_correlation(amplification, [r["stretch"] for r in rows]),
                "vs_ISOE": rank_correlation(amplification, [float(r["ISOE"] or 0) for r in rows]),
                "vs_camera_WRGB_red": rank_correlation(
                    amplification, [float(r["WRGB_red"] or 0) for r in rows]
                ),
                "ISOE_values": sorted({r["ISOE"] for r in rows}),
            }
    clamp_labels = [f"c3 clamp={value:g}" for value in CLAMPS] + [
        f"ancuti2018 cap={DEFAULT_CAP:g} clamp={value:g}" for value in CLAMPS
    ]
    clamp_table = {tile_set: table(clamp_labels, deep, tile_set) for tile_set in TILE_SETS}
    ranking: dict[str, Any] = {}
    for frame in deep + shallow:
        flat = [entry["noise_red"]["flat"] for entry in frame["renders"]]
        lit = [entry["noise_red"]["red_lit"] for entry in frame["renders"]]
        immerkaer = [figures["immerkaer"] for figures in flat]
        donoho = [figures["donoho"] for figures in flat]
        count = len(flat)
        ranking[frame["name"]] = {
            "pairs": count * (count - 1) // 2,
            "donoho_vs_immerkaer_discordant": discordant_pairs(donoho, immerkaer),
            "donoho_tied_pairs": sum(
                donoho[i] == donoho[j] for i in range(count) for j in range(i + 1, count)
            ),
            "donoho_zero_renders": sum(value == 0.0 for value in donoho),
            "flat_vs_red_lit_discordant": None
            if any(figures is None for figures in lit)
            else discordant_pairs(immerkaer, [figures["immerkaer"] for figures in lit]),
        }
    floor: dict[str, Any] = {}
    for label in DEFAULT_SETTINGS:
        for role, group in (("deep", deep), ("open-water", water), ("shallow", shallow)):
            ranges = [_render(frame, label)["normalisation"]["range"] for frame in group]
            floor[f"{label} / {role}"] = {
                "range": _spread(ranges),
                "stretch": _spread([1.0 / value for value in ranges]),
                "per_frame": {
                    frame["name"]: {
                        "range": value,
                        "sigma_out_flat_8bit": row(frame, label, "flat")["sigma_out_8bit"],
                        "source_sigma_flat_8bit": frame["source_noise"]["flat"]["R"][
                            "immerkaer_8bit"
                        ],
                    }
                    for frame, value in zip(group, ranges, strict=True)
                },
            }
    source = {
        frame["name"]: {
            "noise": frame["source_noise"],
            "tiles": {
                tile_set: {key: frame["tiles"][tile_set][key] for key in ("count", "chosen_from")}
                for tile_set in TILE_SETS
            },
            "camera": frame["camera"]["state"],
            "D": frame["listed"].get("D"),
        }
        for frame in deep + shallow
    }
    return {
        "measure": "immerkaer (primary), donoho (cross-check); 8-bit code values",
        "gate4": gate4,
        "cap_direction": direction,
        "tracking": tracking,
        "clamp": clamp_table,
        "ranking": ranking,
        "nfloor": floor,
        "source": source,
    }


# --- the page -------------------------------------------------------------------------------------


def _esc(text: object) -> str:
    """HTML-escape a value's text."""
    return html.escape(str(text))


def _fmt(value: float | None) -> str:
    """Two decimals, or ``n/a`` for a missing value."""
    return "n/a" if value is None else f"{value:.2f}"


def _sigma_caption(noise: Mapping[str, Any], channel: str | None = None) -> str:
    """Return the ``sigma_R`` caption lines of a crop: Immerkaer per tile set, the amplification.

    Args:
        noise: Per tile set, the figures (a render's ``noise_red``, or the source's
            ``source_noise``, then per channel).
        channel: The channel key of a source record; ``None`` for a render's.

    Returns:
        HTML with one line per tile set.
    """
    lines = []
    for tile_set, name in (("flat", "flat"), ("red_lit", "lit")):
        figures = noise[tile_set]
        if figures is None:
            lines.append(f"sigma_R {name} n/a (too few tiles)")
            continue
        if channel is not None:
            lines.append(f"sigma_R {name} {figures[channel]['immerkaer_8bit']:.2f}")
            continue
        lines.append(
            f"sigma_R {name} {figures['immerkaer_8bit']:.2f} "
            f"(x{_fmt(figures['immerkaer_amplification'])})"
        )
    return "<br>".join(lines)


def page(frames: Sequence[Mapping[str, Any]]) -> str:
    """Build the static crop page: per frame, the flat and the textured crop under 7 settings.

    Args:
        frames: The deep and shallow grid records (open-water frames have no crops).

    Returns:
        The HTML (no external resource; images by relative path).
    """
    out = [
        "<!doctype html><html><head><meta charset='utf-8'><title>WP1.4b noise crops</title>",
        "<style>body{font-family:sans-serif;margin:16px}td{vertical-align:top;font-size:12px;"
        "padding:2px}img{width:256px;height:256px;image-rendering:pixelated}"
        "table{border-collapse:collapse}</style></head><body>",
        "<h1>WP1.4b: red-channel noise under the gain caps and the clamp</h1>",
        "<p>Each crop is 512x512 at 100 % shown at half size (open it for full size). Row one is "
        "RGB, row two the red channel alone in grayscale. sigma_R is Immerkaer's estimate in "
        "8-bit code values on the frame's two fixed tile sets: 'flat' (the flattest quarter of "
        "the source tiles) and 'lit' (the flattest quarter of the tiles whose source red mean "
        "is at least 16/255); x is the amplification over the source (n/a where the source "
        "reads 0). On deep 8-bit HEVC frames much of what it measures is compression artefact "
        "carried into red, not sensor grain: the crops are the direct evidence.</p>",
    ]
    for frame in frames:
        if not frame["crops"]:
            continue
        folder = "crops/" + frame["name"].replace("@", "_")
        camera = frame["camera"]["state"]
        out.append(
            f"<h2>{_esc(frame['name'])} ({_esc(frame['role'])}, D = "
            f"{_esc(frame['listed'].get('D', 'n/a'))}, ISO {_esc(camera.get('ISOE'))}, "
            f"camera WB red {_esc(camera.get('WRGB', ['?'])[0])})</h2>"
        )
        columns = ["source", *CROP_SETTINGS]
        for window in ("flat", "textured"):
            y, x = frame["windows"][window]
            out.append(f"<h3>{window} crop at x={x}, y={y}</h3><table><tr>")
            for column in columns:
                if column == "source":
                    caption = "source<br>" + _sigma_caption(frame["source_noise"], "R")
                else:
                    entry = _render(frame, column)
                    bound = entry["bound"]
                    flags = [
                        name
                        for name, flag in (
                            ("cap", bound["red_gain_cap"]),
                            ("clamp R", bound["white_balance_clamp"][0]),
                            ("clamp G", bound["white_balance_clamp"][1]),
                            ("clamp B", bound["white_balance_clamp"][2]),
                        )
                        if flag
                    ]
                    caption = (
                        f"{_esc(column)}<br>{_sigma_caption(entry['noise_red'])}<br>red gain "
                        f"{entry['white_balance']['applied_gains'][0]:.2f}<br>bound: "
                        f"{_esc(', '.join(flags) or 'none')}"
                    )
                out.append(f"<td>{caption}</td>")
            for kind in ("rgb", "red"):
                out.append("</tr><tr>")
                for column in columns:
                    name = frame["crops"][column][window][kind]
                    out.append(
                        f"<td><a href='{folder}/{_esc(name)}'><img src='{folder}/{_esc(name)}' "
                        f"alt='{_esc(name)}'></a></td>"
                    )
            out.append("</tr></table>")
    out.append("</body></html>")
    return "\n".join(out)


def run_summary(roots: OutputRoots) -> dict[str, Any]:
    """Assemble ``grid.json``, write ``summary.json`` and the crop page ``index.html``.

    Args:
        roots: The output roots.

    Returns:
        The summary.

    Raises:
        FileNotFoundError: A frame of ``frames.json`` has no grid record yet.
    """
    records = json.loads((roots.allowed / "frames.json").read_text(encoding="utf-8"))
    frames = []
    for record in records:
        path = roots.allowed / "grid" / f"{record['name'].replace('@', '_')}.json"
        frames.append(json.loads(path.read_text(encoding="utf-8")))
    grid = {
        "schema": 1,
        "spec": "0.5.3",
        "settings": [
            {"label": s.label, "params": dataclasses.asdict(s.params)} for s in settings_grid()
        ],
        "frames": frames,
    }
    roots.write_text(roots.allowed / "grid.json", json.dumps(grid, indent=1))
    summary = summarise(frames)
    roots.write_text(roots.allowed / "summary.json", json.dumps(summary, indent=1))
    roots.write_text(
        roots.allowed / "index.html",
        page([frame for frame in frames if frame["role"] != "open-water"]),
    )
    return summary


def main(argv: Sequence[str] | None = None) -> int:
    """Run one phase of the experiments.

    Args:
        argv: The arguments (``sys.argv[1:]`` when ``None``).

    Returns:
        0 on success.
    """
    parser = argparse.ArgumentParser(description="WP1.4b gain-cap noise experiments.")
    parser.add_argument(
        "phase", choices=("extract", "grid", "smoothing", "lighting-step", "summarise")
    )
    parser.add_argument("--frame", help="grid: run this frame only (its frames.json name)")
    parser.add_argument("--limit", type=int, help="grid: stop after this many frames")
    parser.add_argument("--device", choices=("gpu", "cpu"), default="gpu")
    args = parser.parse_args(argv)
    config = load_local_config()
    roots = OutputRoots.from_config(config, subdir=WORK_SUBDIR)
    roots.mkdir(roots.allowed)
    if args.phase == "extract":
        extract_frames(config, roots)
    elif args.phase == "grid":
        run_grid(roots, select_backend(args.device), args.frame, args.limit)
    elif args.phase == "smoothing":
        record = run_smoothing(config, roots, select_backend(args.device))
        print(f"cap binds on {record['cap_binding_fraction']:.1%} of the frames")
    elif args.phase == "lighting-step":
        record = run_lighting_step(config, roots, select_backend(args.device))
        print(f"step at {record['step']['seconds_into_excerpt']} s into the excerpt")
    else:
        run_summary(roots)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
