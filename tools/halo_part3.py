"""WP5.7 Part 3 instruments: V3 and the N6 row under a switch, and the whole-set batch.

Seat-run instruments for CHARC's rulings C1-C4 (2026-11-03): candidate (d), input 2 clipped to
the local range of its unsharpened form over a window of half side 1 sharpening sigma
(:data:`CANDIDATE`, the probe's ``--switch clip_overshoot=unsharpened:1``), against the shipped
defaults. Nothing under ``src/`` is edited and no default changes: every candidate analysis and
render runs inside :func:`halo_probe.applied`, which patches the product's module attributes for a
``with`` block and restores them on any exit; every shipped-defaults one runs outside it.

``v3`` (C3 as amended by Q2). V3 and AD-14 on WP4.2's two synthetic clips, measured by WP4.2's
OWN code (:func:`suite`): the repository's ``tests`` folder is appended to the import path and
``tests/test_wp42_v3_product.py`` is imported by name, so the legs, the region statistic, the
planted controls and the acceptance predicates are the suite's objects, not copies. Per clip and
method its ``_v3`` runs inside ``applied`` (:func:`measure_v3`): the smoothed leg is an export
through the composition root's engine IN THIS PROCESS (its sink records each frame's measured
region before the encode), the per-frame leg renders each decoded frame from
``AnalysisEngine.provisional_record`` of a second, in-process analysis, so the switch reaches both
legs' analyses and renders. PASS / FAIL (:func:`v3_verdict`) repeats the two acceptance tests'
assertions with the suite's own predicates ``_v3_holds`` (V3: per measure, smoothed flicker at
most 25 % of the per-frame) and ``_ad14_holds`` (AD-14: under 0.5/255), imported, never retyped:
the jittering-patch clip asserts V3, ``ad14-flicker`` asserts AD-14 and records V3's ratios. The
clips are built as the module's ``clips`` fixture builds them (:func:`build_clips`: its body, as
pytest refuses a direct call of a fixture; a test checks the result equals the fixture's frame for
frame) from the shared samples through the suite's ``fixture_plugin.SampleProvider`` (its cache of
generated samples under the run's folder). The shipped-defaults leg runs first and must REPRODUCE
WP4.2's figures of record (:data:`V3_RECORD`) within :data:`AD14_TOLERANCE` and
:data:`RATIO_TOLERANCE`, one unit in the record's last printed place; otherwise the run STOPS
(exit 4) before the candidate leg runs (an instrument STOP, not a candidate result). ``v3``
refuses ``--switch full_res_bounds`` (exit 2): nothing in its legs overrides the bounds, so (e3)
would be recorded without taking effect; Part 3's contracted V3 candidate is (d).

``n6`` and ``n6-summary`` (C4). ONE timed export of the whole GX011627 under one setting, by the
V16 / N6 instrument of record, ``tools/export_bench.py`` (``run GX011627 --runs 1 --device-frames``,
WP5.2's W52-1 form), called in this process inside ``applied`` (:func:`run_n6`). The bench builds
``clearwater.jobs.ExportEngine`` in its own process (the GUI's spawned export worker, AD-31, is not
on this path, and was not on N6's of record either), so the switch reaches the engine's analysis
thread and its renders; a counter around the method's ``fusion_inputs`` proves it ran (and that
the clip was in effect) on every run. Each run writes the bench's own record and a sidecar
``n6-<setting>-<stamp>.json``; ``n6-summary`` (:func:`n6_summary`) reads them: D106 min/min per run
(``wall_s / frames * frame_rate``, the bench's ``total.min_per_min``), the median per setting,
the effect ``median(candidate) / median(shipped) - 1`` and each adjacent pair's ratio. The summary
is valid only for C4's protocol of record (:func:`n6_protocol_problems`: S D alternating from
shipped, complete pairs, at least :data:`N6_MIN_PAIRS`); an invalid one exits
:data:`N6_INVALID_EXIT`, and on a valid one an effect over :data:`N6_STOP_FRACTION` is C4's STOP
(exit 4). Every JSON record this tool writes is staged, then published by rename
(:func:`_write_json`).

``wholeset-list``, ``wholeset-run`` and ``wholeset-sheet`` (Part 3; C1, C2, C3 (3)). The 120 other
CP5 items (:func:`wholeset_items`: the pack's manifest ``records/pack.json``, the items whose
status is ``done``, which must be exactly the review sheet's 126 judged items, minus the six halo
items of :data:`HALO_ITEMS`). Per item, the same image rendered at the shipped defaults and under
the candidate (photos: statistics on the block-mean proxy, as the photo export measures them;
videos: two whole-clip analyses, as the export runs them, then the frames at the pack's three
still times rendered from each analysis's smoothed records; a still time is the ABSOLUTE source
time, matched on ``pts * time_base`` by :func:`still_pts`), and recorded: the probe's
:func:`halo_probe.whole_image` change (per-channel mean shift, clipped fractions, mean and 99th
percentile absolute difference), the edge-band scan (:func:`scan_pair`) of both renders, the
render (and video analysis) walls, both renders as full-resolution 8-bit PNGs, and for a video
how far the candidate moves the smoothed statistics (:func:`statistics_movement`). The sheet
(:func:`select_contact`) is 20 items: the :data:`CONTACT_VIDEO_SLOTS` video items whose input-2
saliency mean moves most, then the largest whole-image changes. It is built from the PUBLISHED
item records only (:func:`published_records`: no staging or failed folder), and fails unless they
are exactly the whole set.

The edge-band scan (:func:`scan_points`, :func:`scan_pair`; the brief's "maximum edge-band
overshoot found by scanning strong edges"). On the SOURCE's BT.709 luma (smoothed by a Gaussian of
:data:`SCAN_SMOOTHING_PX`), the Sobel gradient; the candidate points are the pixels at or above its
:data:`SCAN_PERCENTILE` th percentile, inside a margin that keeps every profile in the image; taken
strongest first, at most one per square cell of the profile half-length, at most
:data:`SCAN_POINTS` of them. Through each point a line along the gradient, half-length
:data:`SCAN_HALF_LENGTH_SIGMAS` sharpening sigmas, is measured from BOTH ends (each end once the
line's start, i.e. the side whose band is measured) with the probe's own band rule
(:func:`halo_probe.water_band` of the render's luma against the source's, half width
:data:`SCAN_HALF_WIDTH`, the probe's threshold): the same sides for both renders. Per render the
summary counts the sides by verdict (band / none / undecided; undecided is never removal) and
gives the largest qualifying band and the largest band. A cell metric, not the owner's eye.

Command line (from the repository root)::

    uv run python tools/halo_part3.py v3 --out DIR [--switch S ...] [--method M ...]
    uv run python tools/halo_part3.py n6 --setting shipped|candidate [--subdir D] [--keep]
    uv run python tools/halo_part3.py n6-summary [--subdir D]
    uv run python tools/halo_part3.py wholeset-list [--kind photo|video]
    uv run python tools/halo_part3.py wholeset-run ITEM [ITEM ...] [--out DIR] [--cache-dir DIR]
    uv run python tools/halo_part3.py wholeset-sheet [--out DIR]

Every output goes under ``<working folder>/wp5.7/part3`` or ``part3r`` (Reviewer A round 5's
re-render; refused elsewhere, and checked against the footage folder); the CP5 pack is read in
place, never written; footage is reached only through ``local_config.find_footage_file`` and
:func:`halo_probe.find_footage_photo`, read-only.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import html
import importlib
import json
import math
import os
import statistics
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from datetime import UTC, datetime
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
from numpy.typing import NDArray
from PIL import Image as PILImage
from scipy import ndimage

import export_bench
import halo_probe as hp
import headless_export
from clearwater.analysis import AnalysisEngine
from clearwater.cache import DiskProxyCache, cache_key
from clearwater.core import select_backend, spatial_sigma
from clearwater.interfaces import Image, Settings
from clearwater.io.photo import read_photo
from clearwater.io.video import FFmpegVideoSource
from clearwater.jobs.export import expected_frames
from clearwater.methods import AncutiFusionMethod, available_methods
from clearwater.methods import ancuti_fusion as _ancuti_module
from clearwater.methods import fusion as _fusion_module
from local_config import LocalConfigError, find_footage_file, load_local_config

REPO_ROOT = Path(__file__).resolve().parent.parent
"""The repository (or worktree) root: this file is ``tools/halo_part3.py``."""

TESTS_DIR = REPO_ROOT / "tests"
"""Where WP4.2's acceptance module and the suite's fixture plugin live."""

CANDIDATE = "clip_overshoot=unsharpened:1"
"""CHARC C1: Part 3's candidate, (d) unsharpened clip at 1 sigma, as a probe ``--switch``."""

CANDIDATE_METHOD = "c3"
"""The method of every whole-set render: the shipped default (D16), as the CP5 presets."""

PART3 = Path("wp5.7") / "part3"
"""The Part 3 window's folder of the working folder (the default of every output)."""

PART3R = Path("wp5.7") / "part3r"
"""Reviewer A round 5's re-render folder (the affected items, then the rebuilt sheet)."""

OUTPUT_ROOTS = (PART3, PART3R)
"""Every output of this tool lies under one of these folders of the working folder."""

# --- V3 -----------------------------------------------------------------------------------------

V3_RECORD: dict[tuple[str, str], dict[str, Any]] = {
    ("jitter", "c3"): {
        "ad14_unsmoothed": 0.1006,
        "ad14_smoothed": 0.0017,
        "ratios": (0.018, 0.014, 0.026, 0.016),
    },
    ("jitter", "ancuti2018"): {
        "ad14_unsmoothed": 0.1055,
        "ad14_smoothed": 0.0017,
        "ratios": (0.012, 0.016, 0.024, 0.012),
    },
    ("ad14", "c3"): {
        "ad14_unsmoothed": 0.0416,
        "ad14_smoothed": 0.0102,
        "ratios": (0.053, 0.200, 0.401, 0.072),
    },
    ("ad14", "ancuti2018"): {
        "ad14_unsmoothed": 0.0388,
        "ad14_smoothed": 0.0067,
        "ratios": (0.061, 0.257, 0.497, 0.071),
    },
}
"""WP4.2's figures of record (``docs/reports/wp4.2-video-path.md``, "V3 ratios", the GPU job, the
same on the CPU job): per (clip, method) the AD-14 figure of the per-frame and the smoothed leg
(/255, four decimals) and V3's four ratios L*, a*, b*, contrast (three decimals)."""

AD14_TOLERANCE = 1e-4
"""The reproduction tolerance of an AD-14 figure: one unit in the record's fourth decimal."""

RATIO_TOLERANCE = 1e-3
"""The reproduction tolerance of a V3 ratio: one unit in the record's third decimal."""

V3_CLIPS = ("jitter", "ad14")
"""The two clips: the jittering-patch clip (V3 asserted) and ``ad14-flicker`` (AD-14 asserted)."""

V3_STOP_EXIT = 4
"""The exit status when the shipped-defaults leg does not reproduce the record (a STOP)."""

# --- N6 -----------------------------------------------------------------------------------------

N6_CLIP = "GX011627"
"""The clip of N6's figures of record (WP5.2 W52-1, D106 / V16)."""

N6_STOP_FRACTION = 0.10
"""CHARC C4: an N6 effect over this fraction is a STOP to CHARC before the proposal."""

N6_SETTINGS = ("shipped", "candidate")
"""The two settings of the timed row, in the order each pair runs them (shipped first)."""

N6_MIN_PAIRS = 3
"""The fewest complete shipped / candidate pairs of a valid row: CHARC C4's six alternating cold
runs S1 D1 S2 D2 S3 D3 (ledger, "C4 sizing"; CHARC may add a further pair or two, never fewer)."""

N6_INVALID_EXIT = 5
"""The ``n6-summary`` exit status when the runs are not the protocol of record (no N6 row; the
STOP's 4 is given only on a valid summary)."""

# --- the whole set ------------------------------------------------------------------------------

HALO_ITEMS = (
    "IMG_6739",
    "IMG_6743",
    "IMG_6744",
    "IMG_6738",
    "GX011627",
    "compilation-20261010-1080p60",
)
"""The six CP5 items with the owner's halo observations (DR-117); the whole set is the rest."""

WHOLESET_COUNT = 120
"""The brief's count of the other CP5 items (126 judged minus the six)."""

PACK = Path("wp5.3")
"""The CP5 pack under the working folder (read-only)."""

STILL_FRACTIONS = (0.1, 0.5, 0.9)
"""A video item's frames when the pack lists no stills: these fractions of its frames."""

CONTACT_ITEMS = 20
"""The contact sheet's size (the brief)."""

CONTACT_VIDEO_SLOTS = 5
"""Sheet places reserved for the video items whose smoothed statistics move most (C3 (3))."""

PREVIEW_WIDTH = 1200
"""The width of each half of a contact-sheet preview, in pixels."""

SCAN_POINTS = 48
"""The most strong-edge points scanned per image (each measured from both ends)."""

SCAN_PERCENTILE = 99.5
"""Candidate edge points: the source gradient magnitude at or above this percentile."""

SCAN_HALF_LENGTH_SIGMAS = 8.0
"""The scan line's half-length in sharpening sigmas (each plateau a quarter of the line)."""

SCAN_HALF_WIDTH = 4
"""The scan profiles' half width (Part 1's half width of record)."""

SCAN_SMOOTHING_PX = 1.0
"""The Gaussian smoothing of the source luma before the gradient, in pixels."""

UNDECIDED_LINES = (
    ("IMG_6739", None, 3, "undecided"),
    ("IMG_6738", 0.4333, 2, "undecided"),
    ("IMG_6738", 0.4667, 2, "undecided"),
    ("IMG_6738", 0.6333, 2, "undecided"),
    ("GX011627", 22.1555, 1, "undecided"),
    ("GX011627", 22.3557, 1, "undecided"),
    ("GX011627", 22.3890, 1, "undecided"),
    ("GX011627", 22.4224, 1, "undecided"),
    ("GX011627", 22.4558, 1, "undecided"),
    ("compilation-20261010-1080p60", 27.0270, 1, "undecided"),
    ("compilation-20261010-1080p60", 27.0103, 3, "band"),
)
"""C2's crops: the decided lines (Part 1 table of record) that are NOT ``none`` under (d) 1 sigma
in Part 2's records (``part2/d-unsharpened-1``): the one photo and nine video undecided lines, and
the one remaining band (item, time in s or None for a photo, line number, verdict under (d))."""


# --- shared -------------------------------------------------------------------------------------


def part3_roots() -> tuple[Path, ...]:
    """The folders an output may go under: ``<working folder>/wp5.7/part3`` and ``part3r``."""
    work = load_local_config().working_path
    return tuple(work / root for root in OUTPUT_ROOTS)


def checked_output(target: Path) -> Path:
    """Refuse an output path outside ``part3`` / ``part3r`` or refused by the footage check.

    Args:
        target: The planned output folder or file.

    Returns:
        ``target`` resolved (absolute), the path the checks accepted: a relative ``target`` would
        otherwise reach callers that need an absolute one (the sheet's ``as_uri`` links;
        Reviewer B finding 3).

    Raises:
        hp.ProbeError: It lies outside ``<working>/wp5.7/part3`` and ``<working>/wp5.7/part3r``,
            or the footage check refuses it.
    """
    roots = part3_roots()
    if not any(headless_export.inside(target, root) for root in roots):
        raise hp.ProbeError(f"{target} is not inside {' or '.join(str(r) for r in roots)}")
    footage = headless_export.configured_footage_folder()
    if footage is not None:
        refusal = headless_export.write_target_refusal(target, footage)
        if refusal is not None:
            raise hp.ProbeError(refusal)
    return target.resolve()


def _temporary(path: Path) -> Path:
    """The staging name of a record :func:`_write_json` publishes as ``path``.

    Dot-prefixed, in the same folder (so the publish is one rename on one volume), and so never
    matched by a pattern that starts with a name (``n6-<setting>-*.json``, ``sheet-*``).
    """
    return path.with_name(f".{path.name}.staging-{_stamp()}")


def _write_json(path: Path, record: Mapping[str, Any]) -> None:
    """Write a record to a NEW file, staged: written whole to a temporary, then renamed.

    The record is written to :func:`_temporary` (exclusive create) and published by renaming it
    to ``path``, so an interrupt never leaves a partial file under the final name (Reviewer B
    finding 2); on any exception the temporary is removed and the exception re-raised. ``path``
    must not exist: refused before writing, and the rename refuses it again on Windows (on POSIX
    a rename replaces a file that appeared in between, the same platform limit as the probe's
    folder publication).

    Raises:
        FileExistsError: ``path`` exists.
    """
    if os.path.lexists(path):
        raise FileExistsError(f"{path} exists")
    text = json.dumps(hp._plain(record), indent=1)
    temporary = _temporary(path)
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            handle.write(text)
        temporary.rename(path)
    except BaseException:
        with contextlib.suppress(OSError):
            temporary.unlink()
        raise


def _stamp() -> str:
    """The UTC time to the microsecond, for file names."""
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")


# --- V3 -----------------------------------------------------------------------------------------


def suite() -> SimpleNamespace:
    """WP4.2's acceptance module and the suite's fixture plugin, imported by name.

    The repository's ``tests`` folder is APPENDED to ``sys.path`` (so a ``tools`` module of the
    same name still wins); under pytest the modules are the ones pytest imported.

    Returns:
        ``wp42`` (``test_wp42_v3_product``) and ``plugin`` (``fixture_plugin``).
    """
    if str(TESTS_DIR) not in sys.path:
        sys.path.append(str(TESTS_DIR))
    return SimpleNamespace(
        wp42=importlib.import_module("test_wp42_v3_product"),
        plugin=importlib.import_module("fixture_plugin"),
    )


def sample_provider(modules: SimpleNamespace, folder: Path) -> Callable[[str], Path]:
    """The suite's sample lookup, its generated samples cached under ``folder``.

    Args:
        modules: :func:`suite`.
        folder: The cache of generated samples (made when needed) and scratch folders.

    Returns:
        ``sample(sample_id) -> Path``, as the suite's ``sample`` fixture gives it.
    """
    plugin = modules.plugin
    folder.mkdir(parents=True, exist_ok=True)
    provider = plugin.SampleProvider(
        plugin.load_manifest(),
        plugin.FIXTURES_DIR,
        folder / "generated",
        lambda: Path(tempfile.mkdtemp(prefix="committed-", dir=folder)),
    )
    path: Callable[[str], Path] = provider.path
    return path


def build_clips(
    modules: SimpleNamespace, folder: Path, sample: Callable[[str], Path]
) -> dict[str, Path]:
    """The two clips as WP4.2's ``clips`` fixture builds them (lossless 8-bit 4:2:0 HEVC MP4).

    The fixture's body, calling the module's own ``_encode_lossless`` and ``jitter_clip``.

    Args:
        modules: :func:`suite`.
        folder: Where the clips are written (made when needed).
        sample: The sample lookup.

    Returns:
        ``{"ad14": ..., "jitter": ...}``.
    """
    wp42 = modules.wp42
    folder.mkdir(parents=True, exist_ok=True)
    ad14: Path = wp42._encode_lossless(
        ["-i", str(sample("ad14-flicker"))], folder / "ad14-flicker.mp4"
    )
    _, images, _ = wp42.jitter_clip()
    height, width = images[0].shape[:2]
    raw = b"".join(np.ascontiguousarray(image).tobytes() for image in images)
    jitter: Path = wp42._encode_lossless(
        [
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{width}x{height}",
            "-framerate", "30000/1001", "-i", "-",
        ],
        folder / "jitter.mp4",
        stdin=raw,
    )  # fmt: skip
    return {"ad14": ad14, "jitter": jitter}


def v3_masks(
    modules: SimpleNamespace, sample: Callable[[str], Path]
) -> dict[str, NDArray[np.bool_]]:
    """The measured regions of the two clips.

    ``ad14-mask`` as WP4.2's ``ad14_mask`` fixture reads it, and the jittering-patch clip's upper
    half (WP4.2's ``_jitter_mask``).
    """
    with PILImage.open(sample("ad14-mask")) as image:
        ad14 = np.asarray(image.convert("L")) > 127
    jitter: NDArray[np.bool_] = modules.wp42._jitter_mask()
    return {"ad14": ad14, "jitter": jitter}


def measure_v3(
    modules: SimpleNamespace,
    clip: Path,
    method: str,
    mask: NDArray[np.bool_],
    folder: Path,
    switches: hp.Switches,
) -> dict[str, Any]:
    """WP4.2's ``_v3`` of one clip and method, both legs inside ``applied(switches)``.

    Args:
        modules: :func:`suite`.
        clip: The lossless clip.
        method: The method id.
        mask: The measured region.
        folder: A new folder for the legs' outputs and caches (made here).
        switches: The setting; ``Switches()`` for the shipped defaults.

    Returns:
        ``_v3``'s figures.
    """
    folder.mkdir(parents=True)
    with hp.applied(switches):
        figures: dict[str, Any] = dict(modules.wp42._v3(clip, method, mask, folder))
    return figures


def v3_verdict(modules: SimpleNamespace, clip: str, figures: Mapping[str, Any]) -> dict[str, Any]:
    """PASS / FAIL at the bound the acceptance suite asserts on the clip, with its own predicates.

    The jittering-patch clip: per-frame flicker positive, the planted control refused and
    ``_v3_holds`` (V3's 25 %). ``ad14-flicker``: the ratios finite, the planted control refused and
    ``_ad14_holds`` (AD-14's 0.5/255); there V3 at 25 % is recorded, not asserted (CHARC V3-1).

    Args:
        modules: :func:`suite`.
        clip: ``"jitter"`` or ``"ad14"``.
        figures: ``_v3``'s figures.

    Returns:
        ``asserted`` (the bound in words), ``checks``, ``verdict`` and ``v3_within_25_percent``.
    """
    wp42 = modules.wp42
    smoothed, unsmoothed = figures["v3_smoothed"], figures["v3_unsmoothed"]
    if clip == "jitter":
        asserted = "V3: per measure, smoothed flicker <= 25 % of the per-frame (asserted)"
        checks = {
            "per_frame_flicker_positive": bool(np.all(np.asarray(unsmoothed) > 0)),
            "planted_control_refused": not wp42._v3_holds(figures["v3_planted"], unsmoothed),
            "v3_holds": bool(wp42._v3_holds(smoothed, unsmoothed)),
        }
    else:
        asserted = "AD-14: mean abs frame-to-frame difference < 0.5/255 after smoothing (asserted)"
        checks = {
            "ratios_finite": bool(np.all(np.isfinite(list(figures["ratios"].values())))),
            "planted_control_refused": not wp42._ad14_holds(figures["raw_planted_ad14"]),
            "ad14_holds": bool(wp42._ad14_holds(figures["raw_ad14_smoothed"])),
        }
    return {
        "asserted": asserted,
        "checks": checks,
        "verdict": "PASS" if all(checks.values()) else "FAIL",
        "v3_within_25_percent": bool(wp42._v3_holds(smoothed, unsmoothed)),
    }


def reproduction(
    modules: SimpleNamespace, clip: str, method: str, figures: Mapping[str, Any]
) -> dict[str, Any]:
    """Compare a shipped-defaults leg with WP4.2's figures of record (:data:`V3_RECORD`).

    Args:
        modules: :func:`suite` (``MEASURES`` orders the ratios).
        clip: The clip name.
        method: The method id.
        figures: ``_v3``'s figures of the shipped-defaults leg.

    Returns:
        ``reproduces`` and, per figure, the record, the measurement and the difference.
    """
    record = V3_RECORD[(clip, method)]
    rows: dict[str, dict[str, float]] = {}
    for key in ("ad14_unsmoothed", "ad14_smoothed"):
        rows[key] = {"record": record[key], "measured": float(figures[key])}
    for name, value in zip(modules.wp42.MEASURES, record["ratios"], strict=True):
        rows[f"ratio {name}"] = {"record": value, "measured": float(figures["ratios"][name])}
    ok = True
    for key, row in rows.items():
        row["difference"] = row["measured"] - row["record"]
        tolerance = RATIO_TOLERANCE if key.startswith("ratio") else AD14_TOLERANCE
        ok = ok and abs(row["difference"]) <= tolerance + 1e-12
    return {"reproduces": ok, "figures": rows}


def run_v3(
    modules: SimpleNamespace,
    out: Path,
    switches: hp.Switches,
    methods: Sequence[str],
    sample: Callable[[str], Path],
) -> tuple[dict[str, Any], int]:
    """The shipped-defaults leg on both clips (reproduction checked), then the candidate's.

    Args:
        modules: :func:`suite`.
        out: The run's folder (exists).
        switches: The candidate.
        methods: The method ids.
        sample: The sample lookup.

    Returns:
        The record and the exit status (0, or :data:`V3_STOP_EXIT` when the shipped-defaults leg
        did not reproduce the record, in which case the candidate leg did not run).
    """
    clips = build_clips(modules, out / "clips", sample)
    masks = v3_masks(modules, sample)
    rows: list[dict[str, Any]] = []
    record: dict[str, Any] = {
        "tool": "halo_part3 v3",
        "candidate": switches.describe(),
        "tolerances": {"ad14": AD14_TOLERANCE, "ratio": RATIO_TOLERANCE},
        "rows": rows,
    }
    for setting, chosen in (("shipped", hp.Switches()), ("candidate", switches)):
        for clip in V3_CLIPS:
            for method in methods:
                began = time.perf_counter()
                folder = out / "legs" / f"{setting}-{clip}-{method}"
                figures = measure_v3(modules, clips[clip], method, masks[clip], folder, chosen)
                row: dict[str, Any] = {
                    "setting": setting,
                    "clip": clip,
                    "method": method,
                    "figures": figures,
                    "verdict": v3_verdict(modules, clip, figures),
                    "wall_s": time.perf_counter() - began,
                }
                if setting == "shipped":
                    row["reproduction"] = reproduction(modules, clip, method, figures)
                rows.append(row)
                print(v3_line(row), flush=True)
        if setting == "shipped" and not all(r["reproduction"]["reproduces"] for r in rows):
            record["stop"] = (
                "the shipped-defaults leg does not reproduce WP4.2's figures of record within "
                "the stated tolerance: an instrument STOP; the candidate leg was not run"
            )
            return record, V3_STOP_EXIT
    return record, 0


def v3_line(row: Mapping[str, Any]) -> str:
    """One text line of a V3 row (ASCII)."""
    figures, verdict = row["figures"], row["verdict"]
    ratios = " / ".join(f"{value:.3f}" for value in figures["ratios"].values())
    tail = ""
    if "reproduction" in row:
        tail = f" | reproduces record: {'yes' if row['reproduction']['reproduces'] else 'NO'}"
    return (
        f"V3 {row['setting']:9s} {row['clip']:6s} {row['method']:10s} AD-14 /255 "
        f"{figures['ad14_unsmoothed']:.4f} -> {figures['ad14_smoothed']:.4f}; V3 ratios L*/a*/b*/"
        f"contrast {ratios}; {verdict['verdict']} ({verdict['asserted'].split(':')[0]}); "
        f"V3 25 %: {'within' if verdict['v3_within_25_percent'] else 'over'}{tail}"
    )


def v3_table(record: Mapping[str, Any]) -> str:
    """The side-by-side table: each clip and method, the shipped defaults beside the candidate."""
    rows = {(r["setting"], r["clip"], r["method"]): r for r in record["rows"]}
    lines = [
        "| Clip | Method | Setting | AD-14 /255 per-frame -> smoothed | V3 ratio L* / a* / b* / "
        "contrast | Asserted bound: verdict | V3 <= 25 % |",
        "|---|---|---|---|---|---|---|",
    ]
    for clip in V3_CLIPS:
        methods = sorted({m for (_, c, m) in rows if c == clip})
        for method in methods:
            for setting in ("shipped", "candidate"):
                row = rows.get((setting, clip, method))
                if row is None:
                    lines.append(f"| {clip} | {method} | {setting} | not run | | | |")
                    continue
                figures, verdict = row["figures"], row["verdict"]
                ratios = " / ".join(f"{v:.3f}" for v in figures["ratios"].values())
                lines.append(
                    f"| {clip} | {method} | {setting} | {figures['ad14_unsmoothed']:.4f} -> "
                    f"{figures['ad14_smoothed']:.4f} | {ratios} | "
                    f"{verdict['asserted'].split(':')[0]}: {verdict['verdict']} | "
                    f"{'yes' if verdict['v3_within_25_percent'] else 'no'} |"
                )
    return "\n".join(lines) + "\n"


# --- N6 -----------------------------------------------------------------------------------------


_INPUTS = "fusion_inputs"
"""The method module's name for the fusion-input function (what ``applied`` patches for (d))."""


@contextlib.contextmanager
def counted_inputs() -> Iterator[dict[str, Any]]:
    """Count the calls of the method's ``fusion_inputs`` (whatever it is now) for a block.

    Wraps ``clearwater.methods.ancuti_fusion.fusion_inputs`` (the name ``analyze`` and ``render``
    call) with a counter and restores the object on exit. Used inside ``applied``, it wraps the
    candidate's clip; outside, the product's own function.

    Yields:
        ``{"calls": n, "clip_in_effect": bool}``, updated as the block runs.
    """
    inner = getattr(_ancuti_module, _INPUTS)
    counter: dict[str, Any] = {
        "calls": 0,
        "clip_in_effect": inner is not _fusion_module.fusion_inputs,
    }
    lock = threading.Lock()

    def counting(*args: Any, **kwargs: Any) -> Any:
        with lock:
            counter["calls"] += 1
        return inner(*args, **kwargs)

    setattr(_ancuti_module, _INPUTS, counting)
    try:
        yield counter
    finally:
        setattr(_ancuti_module, _INPUTS, inner)


def n6_arguments(subdir: str, keep: bool) -> list[str]:
    """The bench's arguments for one N6 run: WP5.2 W52-1's form with one run."""
    return [
        "run", N6_CLIP, "--runs", "1", "--device-frames", "--subdir", subdir,
        *(["--keep"] if keep else []),
    ]  # fmt: skip


def run_n6(setting: str, subdir: str, keep: bool) -> int:
    """One timed export of GX011627 by ``export_bench`` under ``setting``, in this process.

    Args:
        setting: ``"shipped"`` or ``"candidate"`` (:data:`CANDIDATE`).
        subdir: The bench's ``--subdir`` (below ``wp5.7/part3``).
        keep: Keep the export and its cache (the bench's ``--keep``).

    Returns:
        The bench's exit status (0 done; 3 a failed memory check, the run still timed and
        recorded; 1 or 2 a failure).
    """
    switches = hp.Switches() if setting == "shipped" else hp.parse_switches([CANDIDATE])
    folder = checked_output(load_local_config().working_path / subdir)
    folder.mkdir(parents=True, exist_ok=True)
    before = set(folder.glob("export-bench-*.json"))
    started = datetime.now(UTC)
    with hp.applied(switches), counted_inputs() as counter:
        status = export_bench.main(n6_arguments(subdir, keep))
    records = sorted(p.name for p in set(folder.glob("export-bench-*.json")) - before)
    sidecar = {
        "tool": "halo_part3 n6",
        "setting": setting,
        "switches": switches.describe(),
        "bench_arguments": n6_arguments(subdir, keep),
        "export_bench_exit": status,
        "records": records,
        "fusion_inputs_calls": counter["calls"],
        "clip_in_effect": counter["clip_in_effect"],
        "started": started.isoformat(),
        "finished": datetime.now(UTC).isoformat(),
    }
    _write_json(folder / f"n6-{setting}-{_stamp()}.json", sidecar)
    print(
        f"N6 {setting}: bench exit {status}; fusion_inputs calls {counter['calls']}; "
        f"clip in effect {counter['clip_in_effect']}; records {', '.join(records) or 'none'}"
    )
    return status


def n6_summary(folder: Path) -> dict[str, Any]:
    """Read the N6 sidecars and the bench's records: per run, per setting, the effect.

    Only the run sidecars are read, by their name ``n6-<setting>-<stamp>.json`` for the two
    settings of :data:`N6_SETTINGS`: a summary this function's caller wrote before
    (``n6-summary-<stamp>.json``, in the same folder) is not a run.

    Args:
        folder: The bench folder holding ``n6-<setting>-*.json`` and ``export-bench-*.json``.

    ``valid`` holds only for the protocol of record (:func:`n6_protocol_problems`): both
    settings, the runs in ``started`` order strictly alternating from ``shipped``, complete pairs
    only, at least :data:`N6_MIN_PAIRS` of them, and every run finished whole with the switch
    where it belongs. An interrupted or resumed window therefore never reads as a row (Reviewer
    B finding 1).

    Returns:
        ``runs`` (in time order), ``medians`` (min/min per setting), ``effect``
        (``median(candidate) / median(shipped) - 1``), ``pair_ratios`` (candidate / shipped of
        each adjacent run pair in time order), ``valid`` with its ``problems``, and ``stop`` (a
        VALID summary whose effect is over :data:`N6_STOP_FRACTION`; never set on an invalid
        one, whose effect is not C4's measurement).
    """
    runs: list[dict[str, Any]] = []
    problems: list[str] = []
    sidecars = {p for setting in N6_SETTINGS for p in folder.glob(f"n6-{setting}-*.json")}
    for path in sorted(sidecars):
        sidecar = json.loads(path.read_text(encoding="utf-8"))
        run: dict[str, Any] = {
            "sidecar": path.name,
            "setting": sidecar["setting"],
            "started": sidecar["started"],
            "exit": sidecar["export_bench_exit"],
            "calls": sidecar["fusion_inputs_calls"],
            "clip_in_effect": sidecar["clip_in_effect"],
        }
        bench = [
            json.loads((folder / name).read_text(encoding="utf-8")) for name in sidecar["records"]
        ]
        timed = [r for record in bench for r in record.get("runs", [])]
        if len(timed) != 1:
            problems.append(f"{path.name}: {len(timed)} bench runs, 1 expected")
        else:
            row = timed[0]
            run.update(
                {
                    "ok": row["ok"],
                    "frames": row["frames"],
                    "source_frames": row["source_frames"],
                    "wall_s": row["wall_s"],
                    "min_per_min": (row["total"] or {}).get("min_per_min"),
                    "memory_check_passes": (row.get("memory_check") or {}).get("passes"),
                    "tied": (row.get("nvenc_proof") or {}).get("tied"),
                }
            )
            if not row["ok"] or run["min_per_min"] is None:
                problems.append(f"{path.name}: the export did not finish ok")
            elif row["frames"] != row["source_frames"]:
                problems.append(f"{path.name}: {row['frames']} of {row['source_frames']} frames")
        if run["calls"] <= 0:
            problems.append(f"{path.name}: fusion_inputs never called")
        if run["clip_in_effect"] != (run["setting"] == "candidate"):
            problems.append(f"{path.name}: the clip in effect does not match the setting")
        runs.append(run)
    runs.sort(key=lambda r: r["started"])
    problems += n6_protocol_problems(runs)
    medians: dict[str, float | None] = {}
    for setting in N6_SETTINGS:
        values = [r["min_per_min"] for r in runs if r["setting"] == setting and r.get("ok")]
        medians[setting] = statistics.median(values) if values else None
    shipped, candidate = medians["shipped"], medians["candidate"]
    effect = candidate / shipped - 1.0 if shipped and candidate else None
    timed_runs = [r for r in runs if r.get("ok")]
    pair_ratios = [
        b["min_per_min"] / a["min_per_min"]
        for a, b in zip(timed_runs[::2], timed_runs[1::2], strict=False)
        if a["setting"] == "shipped" and b["setting"] == "candidate"
    ]
    valid = not problems
    return {
        "runs": runs,
        "medians": medians,
        "effect": effect,
        "pair_ratios": pair_ratios,
        "valid": valid,
        "problems": problems,
        "stop_fraction": N6_STOP_FRACTION,
        "stop": valid and effect is not None and effect > N6_STOP_FRACTION,
    }


def n6_protocol_problems(runs: Sequence[Mapping[str, Any]]) -> list[str]:
    """The ways a population of N6 runs departs from C4's protocol of record (none: it holds).

    The protocol: both settings of :data:`N6_SETTINGS` present; the runs, in ``started`` order,
    strictly alternate starting with ``shipped`` (S D S D ...); an even count, so every run is in
    a complete shipped-then-candidate pair; and at least :data:`N6_MIN_PAIRS` pairs.

    Args:
        runs: The runs, sorted by ``started`` (each with its ``sidecar`` name and ``setting``).

    Returns:
        One problem line per departure.
    """
    present = {run["setting"] for run in runs}
    problems = [f"no {setting} run" for setting in N6_SETTINGS if setting not in present]
    for index, run in enumerate(runs):
        expected = N6_SETTINGS[index % len(N6_SETTINGS)]
        if run["setting"] != expected:
            problems.append(
                f"{run['sidecar']}: run {index + 1} in time order is {run['setting']}, {expected} "
                "expected (the runs alternate, shipped first)"
            )
    if len(runs) % len(N6_SETTINGS):
        problems.append(f"{len(runs)} runs: an odd count leaves an incomplete pair")
    pairs = len(runs) // len(N6_SETTINGS)
    if pairs < N6_MIN_PAIRS:
        problems.append(f"{pairs} complete pairs, at least {N6_MIN_PAIRS} expected (CHARC C4)")
    return problems


def n6_text(summary: Mapping[str, Any]) -> str:
    """The N6 summary as text lines (ASCII)."""
    lines = []
    for run in summary["runs"]:
        rate = run.get("min_per_min")
        lines.append(
            f"RUN {run['started']} {run['setting']:9s} exit {run['exit']} "
            f"{f'{rate:.4f} min/min' if rate is not None else 'no rate'} "
            f"wall {run.get('wall_s', float('nan')):.1f} s frames {run.get('frames')} "
            f"memory_check {run.get('memory_check_passes')} tied {run.get('tied')} "
            f"calls {run['calls']} clip {run['clip_in_effect']}"
        )
    medians = summary["medians"]
    effect = summary["effect"]
    lines.append(
        f"MEDIAN shipped {medians['shipped']} candidate {medians['candidate']} min/min; effect "
        f"{'n/a' if effect is None else f'{100 * effect:+.2f} %'}; pair ratios "
        f"{', '.join(f'{r:.4f}' for r in summary['pair_ratios']) or 'none'}"
    )
    lines.append(f"VALID {summary['valid']}" + "".join(f"; {p}" for p in summary["problems"]))
    if not summary["valid"]:
        lines.append("INVALID: not the protocol of record; no N6 row (the effect is not C4's)")
    if summary["stop"]:
        lines.append(f"STOP: the N6 effect is over {100 * N6_STOP_FRACTION:.0f} % (CHARC C4)")
    return "\n".join(lines) + "\n"


# --- the edge-band scan -------------------------------------------------------------------------


def scan_points(
    source_luma: NDArray[Any], sigma_px: float
) -> tuple[list[tuple[float, float, float, float]], int]:
    """Choose the strong-edge points of an image to scan (see the module docstring).

    Args:
        source_luma: The source's luma, ``(H, W)``.
        sigma_px: The sharpening sigma in pixels.

    Returns:
        The points ``(x, y, ux, uy)`` (``u`` the unit gradient, dark to bright), strongest
        first, and the line half-length in pixels.
    """
    half = max(8, math.ceil(SCAN_HALF_LENGTH_SIGMAS * sigma_px))
    plane = np.asarray(source_luma, dtype=np.float64)
    smooth = ndimage.gaussian_filter(plane, SCAN_SMOOTHING_PX)
    gx = ndimage.sobel(smooth, axis=1)
    gy = ndimage.sobel(smooth, axis=0)
    magnitude = np.hypot(gx, gy)
    margin = half + SCAN_HALF_WIDTH + 2
    height, width = plane.shape
    if height <= 2 * margin or width <= 2 * margin:
        return [], half
    inner = magnitude[margin : height - margin, margin : width - margin]
    level = float(np.percentile(inner, SCAN_PERCENTILE))
    ys, xs = np.nonzero((inner >= level) & (inner > 0))
    order = np.lexsort((xs, ys, -inner[ys, xs]))  # strongest first; ties by row, then column
    taken: set[tuple[int, int]] = set()
    points: list[tuple[float, float, float, float]] = []
    for index in order:
        y, x = int(ys[index]) + margin, int(xs[index]) + margin
        cell = (y // half, x // half)
        if cell in taken:
            continue
        taken.add(cell)
        g = float(magnitude[y, x])
        points.append((float(x), float(y), float(gx[y, x]) / g, float(gy[y, x]) / g))
        if len(points) == SCAN_POINTS:
            break
    return points, half


def _scan_summary(sides: Sequence[Mapping[str, Any]], name: str) -> dict[str, Any]:
    """Count one render's scanned sides by verdict; the largest qualifying and overall bands."""
    verdicts = [side[name]["verdict"] for side in sides]
    qualifying = [side[name]["band"] for side in sides if side[name]["verdict"] == "band"]
    return {
        "band": verdicts.count("band"),
        "none": verdicts.count("none"),
        "undecided": verdicts.count("undecided"),
        "max_qualifying_band": max(qualifying, default=0.0),
        "max_band": max((side[name]["band"] for side in sides), default=0.0),
    }


def scan_pair(
    source: NDArray[Any],
    shipped: NDArray[Any],
    candidate: NDArray[Any],
    sigma_px: float,
    *,
    threshold: float = hp.DEFAULT_THRESHOLD,
) -> dict[str, Any]:
    """The edge-band scan of two renders of one source, on the same lines.

    Args:
        source: The source, host ``(H, W, 3)``.
        shipped: The shipped-defaults render, host ``(H, W, 3)``.
        candidate: The candidate's render, host ``(H, W, 3)``.
        sigma_px: The sharpening sigma in pixels.
        threshold: The band threshold (the probe's).

    Returns:
        ``half_length_px``, ``points``, ``sides`` (per side: the point, the start side and each
        render's band, absolute band, verdict, FWHM and weak-edge flag) and ``summary`` per render
        (:func:`_scan_summary`).
    """
    src = hp.luma(source)
    planes = {"shipped": hp.luma(shipped), "candidate": hp.luma(candidate)}
    points, half = scan_points(src, sigma_px)
    sides: list[dict[str, Any]] = []
    for x, y, ux, uy in points:
        for start in (-1.0, 1.0):  # the line's start (the measured side): dark, then bright
            line = hp.Line(
                x + start * half * ux,
                y + start * half * uy,
                x - start * half * ux,
                y - start * half * uy,
            )
            reference = hp.line_profile(src, line, half_width=SCAN_HALF_WIDTH)
            fits = hp.profile_fits(reference)
            spacing = hp.sample_spacing(line)
            side: dict[str, Any] = {"x": x, "y": y, "start_side": "dark" if start < 0 else "bright"}
            for name, plane in planes.items():
                profile = hp.line_profile(plane, line, half_width=SCAN_HALF_WIDTH)
                band = hp.water_band(profile, reference, fits, threshold=threshold, spacing=spacing)
                side[name] = {
                    key: band[key]
                    for key in ("band", "band_abs", "verdict", "fwhm_px", "weak_edge")
                }
            sides.append(side)
    return {
        "half_length_px": half,
        "points": len(points),
        "sides": sides,
        "summary": {name: _scan_summary(sides, name) for name in planes},
    }


# --- the whole set ------------------------------------------------------------------------------


def wholeset_items(pack: Path) -> list[dict[str, Any]]:
    """The 120 other CP5 items, in the pack's order.

    Args:
        pack: The CP5 pack folder (read only).

    Returns:
        The pack manifest's entries of the items whose status is ``done``, minus the six.

    Raises:
        hp.ProbeError: The done items are not exactly the review sheet's judged items, a halo
            item is missing, or the count is not :data:`WHOLESET_COUNT`.
    """
    manifest = json.loads((pack / "records" / "pack.json").read_text(encoding="utf-8"))
    with (pack / "review-sheet.csv").open(newline="", encoding="utf-8") as handle:
        judged = {row["item"] for row in csv.DictReader(handle)}
    done = [item for item in manifest["items"] if item["status"] == "done"]
    if {item["item"] for item in done} != judged:
        raise hp.ProbeError("the pack's done items are not the review sheet's judged items")
    if not set(HALO_ITEMS) <= judged:
        raise hp.ProbeError(f"halo items missing from the sheet: {set(HALO_ITEMS) - judged}")
    items = [item for item in done if item["item"] not in HALO_ITEMS]
    if len(items) != WHOLESET_COUNT:
        raise hp.ProbeError(f"{len(items)} items, {WHOLESET_COUNT} expected")
    return items


def item_source(item: Mapping[str, Any], pack: Path, footage: Path) -> Path:
    """Where an item's source is read: the pack's excerpt when the pack cut one, else footage.

    Args:
        item: The pack manifest entry.
        pack: The pack folder.
        footage: The footage folder (read only).

    Returns:
        The file the pack processed.
    """
    stem = Path(item["source_name"]).stem
    if item["kind"] == "photo":
        return hp.find_footage_photo(stem, footage)
    excerpt = item.get("excerpt") or {}
    if excerpt.get("excerpt"):
        return pack / "excerpts" / str(excerpt["name"])
    return find_footage_file(stem, footage)


def save_png8(path: Path, pixels: NDArray[Any]) -> None:
    """Write a host ``(H, W, 3)`` float image in [0, 1] as an 8-bit PNG (values as they are)."""
    data = np.round(np.clip(np.asarray(pixels, dtype=np.float32), 0.0, 1.0) * 255.0)
    PILImage.fromarray(data.astype(np.uint8)).save(path, compress_level=3)


def _timed_render(
    backend: Any, method: AncutiFusionMethod, image: Image, params: Mapping[str, Any], record: Any
) -> tuple[Any, NDArray[np.float32], float]:
    """Render and download (the download synchronises the device); return both and the wall."""
    began = time.perf_counter()
    out = method.render(image, params, record).pixels
    host = np.asarray(backend.to_host(out), dtype=np.float32)
    return out, host, time.perf_counter() - began


def frame_record(
    backend: Any,
    source: NDArray[Any],
    shipped: tuple[Any, NDArray[np.float32]],
    candidate: tuple[Any, NDArray[np.float32]],
    sigma_px: float,
    folder: Path,
    tag: str,
) -> dict[str, Any]:
    """The whole-image change, the edge scan and the two saved renders of one image.

    Args:
        backend: The renders' backend.
        source: The source, host.
        shipped: The shipped-defaults render (device array, host array).
        candidate: The candidate's render (device array, host array).
        sigma_px: The sharpening sigma in pixels.
        folder: The item's folder.
        tag: The image's name in the folder (``photo`` or ``fNN``).

    Returns:
        ``tag``, ``whole_image`` (candidate against shipped) and ``edge_scan``.
    """
    whole = hp.whole_image(backend, candidate[0], shipped[0])
    scan = scan_pair(source, shipped[1], candidate[1], sigma_px)
    save_png8(folder / f"{tag}-shipped.png", shipped[1])
    save_png8(folder / f"{tag}-candidate.png", candidate[1])
    return {"tag": tag, "whole_image": whole, "edge_scan": scan}


def process_photo(
    path: Path, method: AncutiFusionMethod, switches: hp.Switches, folder: Path, *, force_cpu: bool
) -> dict[str, Any]:
    """Render a photo at the shipped defaults and under the candidate; measure; save both.

    Args:
        path: The photo (read only).
        method: The method.
        switches: The candidate.
        folder: The item's folder (exists).
        force_cpu: Process on the CPU.

    Returns:
        The item's run record.
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
    params = hp.resolve_parameters(method, [])
    began = time.perf_counter()
    shipped_statistics = hp.photo_statistics(method, on_device, params)
    shipped_out, shipped_host, render_s = _timed_render(
        backend, method, on_device, params, shipped_statistics
    )
    shipped_wall = time.perf_counter() - began
    with hp.applied(switches):
        began = time.perf_counter()
        candidate_statistics = hp.photo_statistics(method, on_device, params)
        candidate_out, candidate_host, candidate_render_s = _timed_render(
            backend, method, on_device, params, candidate_statistics
        )
        candidate_wall = time.perf_counter() - began
    sigma = spatial_sigma(pixels.shape, params["sharpen_blur_fraction"])
    frame = frame_record(
        backend,
        pixels,
        (shipped_out, shipped_host),
        (candidate_out, candidate_host),
        sigma,
        folder,
        "photo",
    )
    return {
        "kind": "photo",
        "device": reason,
        "size": [height, width],
        "walls_s": {
            "shipped_statistics_and_render": shipped_wall,
            "shipped_render": render_s,
            "candidate_statistics_and_render": candidate_wall,
            "candidate_render": candidate_render_s,
        },
        "statistics": {"shipped": shipped_statistics, "candidate": candidate_statistics},
        "frames": [frame],
    }


def _flat(record: Mapping[str, Any]) -> dict[str, NDArray[np.float64]]:
    """A statistics record as ``{"stage.name": values}`` (float64, flattened)."""
    return {
        f"{stage}.{name}": np.asarray(value, dtype=np.float64).ravel()
        for stage, values in record.items()
        for name, value in values.items()
    }


def statistics_movement(shipped: Any, candidate: Any, axis: Sequence[int]) -> dict[str, Any]:
    """How far the candidate's analysis moves the smoothed statistics, over every frame.

    Args:
        shipped: The shipped-defaults analysis (completed engine).
        candidate: The candidate's analysis (completed engine).
        axis: The clip's frame pts.

    Returns:
        Per statistic: ``max_abs`` (the largest absolute difference over frames and
        components) and the temporal spread of each (the standard deviation of its frame-to-frame
        differences, per component, shipped and candidate); ``input2_saliency_max_abs`` (the
        headline: the largest change of input 2's row of ``fusion.saliency_means``, its mean
        L*, a* and b*; the record is ``(inputs, 3)``, input-major).
    """
    rows_s = [_flat(shipped.smoothed_record(p, schema_hash=shipped.schema_hash)) for p in axis]
    rows_d = [_flat(candidate.smoothed_record(p, schema_hash=candidate.schema_hash)) for p in axis]
    out: dict[str, Any] = {}
    for key in rows_s[0]:
        series_s = np.stack([row[key] for row in rows_s])
        series_d = np.stack([row[key] for row in rows_d])
        spread_s = np.std(np.diff(series_s, axis=0), axis=0) if len(axis) > 1 else series_s[0] * 0
        spread_d = np.std(np.diff(series_d, axis=0), axis=0) if len(axis) > 1 else series_d[0] * 0
        out[key] = {
            "max_abs": float(np.max(np.abs(series_d - series_s))),
            "temporal_spread_shipped": spread_s.tolist(),
            "temporal_spread_candidate": spread_d.tolist(),
        }
    saliency = out.get("fusion.saliency_means")
    headline = None
    if saliency is not None:
        series_s = np.stack([row["fusion.saliency_means"] for row in rows_s])
        series_d = np.stack([row["fusion.saliency_means"] for row in rows_d])
        width = series_s.shape[1] // 2  # two inputs, input-major: input 2 is the second half
        headline = float(np.max(np.abs(series_d[:, width:] - series_s[:, width:])))
    return {"statistics": out, "input2_saliency_max_abs": headline}


STILL_MATCH_S = 1e-6
"""The largest gap between a pack still's time and its chosen frame's (s): CP5's still time is
itself a frame's pts, so the match is exact up to float printing (round 5: 0.0 on all 150)."""


def still_pts(axis: Sequence[int], time_base: Fraction, at: float) -> int:
    """The decoded frame at a CP5 still's time: absolute source time on both sides.

    The convention, confirmed in the code: CP5 stores ``source_pts_s`` as the ABSOLUTE source
    time of the still, ffprobe's ``best_effort_timestamp`` of the first frame at or after the
    wanted time, times the stream's time base (``tools/reviewpack/build.py:227`` ``_frame_time``,
    recorded at ``build.py:1141``), with no start offset removed; the product's decoder keeps the
    container's pts (``-copyts``, ``src/clearwater/io/video/decode.py:247``; ``Frame.pts_ticks``
    is ``showinfo``'s pts, ``decode.py:553``). So a still is matched on ``pts * time_base``, never
    on the time from the first frame (Reviewer A round 5 finding 1: on a clip whose first pts is
    not 0 that match chose the next frame on GX011590, GX011603 and GX011609).

    Args:
        axis: The clip's frame pts (ticks), sorted.
        time_base: The stream's time base.
        at: The still's ``source_pts_s``.

    Returns:
        The pts of the frame at that time.

    Raises:
        hp.ProbeFailedError: No frame of the axis lies within :data:`STILL_MATCH_S` of ``at``.
    """
    pts = min(axis, key=lambda p: abs(float(p * time_base) - at))
    if abs(float(pts * time_base) - at) > STILL_MATCH_S:
        raise hp.ProbeFailedError(
            f"no decoded frame at the pack's still time {at:.6f} s (nearest pts {pts}, "
            f"{float(pts * time_base):.6f} s)"
        )
    return pts


def process_video(
    path: Path,
    method: AncutiFusionMethod,
    switches: hp.Switches,
    folder: Path,
    *,
    stills: Sequence[Mapping[str, Any]],
    cache_dir: Path,
    force_cpu: bool,
) -> dict[str, Any]:
    """Analyse a clip twice (shipped, candidate), render its still frames both ways; measure.

    Args:
        path: The clip (read only).
        method: The method.
        switches: The candidate.
        folder: The item's folder (exists).
        stills: The pack's stills (``fraction``, ``source_pts_s``, ABSOLUTE source time: each is
            the frame :func:`still_pts` finds); empty: :data:`STILL_FRACTIONS` of the frames.
        cache_dir: The analysis cache folder.
        force_cpu: Process on the CPU.

    Returns:
        The item's run record. Per frame ``pts_ticks``, ``source_pts_s`` (``pts * time_base``,
        the absolute time CP5's still names), ``time_s`` (seconds from the clip's first frame)
        and ``pack_still_s`` (the still's recorded time, or None).

    Raises:
        hp.ProbeFailedError: An analysis failed, the two axes differ, a still names no frame
            (:func:`still_pts`), or the decode did not deliver a chosen frame.
    """
    source = FFmpegVideoSource()
    probe = source.probe(path)
    video = probe.video
    backend, reason = select_backend(
        Settings(force_cpu=force_cpu), video.height, video.width, method.id
    )
    cache = DiskProxyCache(cache_dir)
    params = hp.resolve_parameters(method, [])
    hw_decode = backend.device != "cpu"

    def analysed() -> tuple[Any, float]:
        began = time.perf_counter()
        engine = AnalysisEngine(
            method=method,
            backend=backend,
            cache=cache,
            key=cache_key(path),
            source=source,
            probe=probe,
            params=dict(params),
            hw_decode=hw_decode,
            expected_frames=expected_frames(probe),
        )
        result = engine.analysis_job()(hp._Progress())
        if not result.ok:
            raise hp.ProbeFailedError(f"the analysis failed: {result.failure}")
        return engine, time.perf_counter() - began

    shipped, shipped_analysis_s = analysed()
    with hp.applied(switches):
        candidate, candidate_analysis_s = analysed()
    axis = sorted(int(p) for p in shipped.store.axis())
    if axis != sorted(int(p) for p in candidate.store.axis()):
        raise hp.ProbeFailedError("the two analyses have different frame axes")
    movement = statistics_movement(shipped, candidate, axis)
    first, time_base = axis[0], video.time_base
    targets: list[tuple[float, float | None]] = [
        (float(s["fraction"]), float(s["source_pts_s"])) for s in stills
    ] or [(fraction, None) for fraction in STILL_FRACTIONS]
    chosen: dict[int, tuple[str, float | None]] = {}
    for fraction, at in targets:
        if at is None:
            pts = axis[min(len(axis) - 1, int(fraction * len(axis)))]
        else:
            pts = still_pts(axis, time_base, at)
        chosen[pts] = (f"f{round(100 * fraction):02d}", at)
    sigma = spatial_sigma((video.height, video.width, 3), params["sharpen_blur_fraction"])
    frames: list[dict[str, Any]] = []
    last = max(chosen)
    stream = source.frames(probe, hw_decode=hw_decode)
    try:
        for frame in stream:
            pts = int(frame.pts_ticks)
            if pts > last:
                break
            if pts not in chosen:
                continue
            host = np.asarray(frame.pixels, dtype=np.float32)
            on_device = Image(
                pixels=backend.asarray(host, np.float32),
                device=backend.device,
                color=frame.color,
                orientation_applied=frame.orientation_applied,
            )
            record_s = shipped.smoothed_record(pts, schema_hash=shipped.schema_hash)
            out_s, host_s, wall_s = _timed_render(backend, method, on_device, params, record_s)
            record_d = candidate.smoothed_record(pts, schema_hash=candidate.schema_hash)
            with hp.applied(switches):
                out_d, host_d, wall_d = _timed_render(backend, method, on_device, params, record_d)
            tag, at = chosen[pts]
            entry = frame_record(
                backend, host, (out_s, host_s), (out_d, host_d), sigma, folder, tag
            )
            entry.update(
                {
                    "pts_ticks": pts,
                    "source_pts_s": float(pts * time_base),
                    "time_s": float((pts - first) * time_base),
                    "pack_still_s": at,
                    "render_s": {"shipped": wall_s, "candidate": wall_d},
                }
            )
            frames.append(entry)
            del out_s, out_d
    finally:
        close = getattr(stream, "close", None)
        if close is not None:
            close()
    missing = sorted(set(chosen) - {entry["pts_ticks"] for entry in frames})
    if missing:
        raise hp.ProbeFailedError(f"the decode did not deliver {len(missing)} chosen frames")
    return {
        "kind": "video",
        "device": reason,
        "size": [video.height, video.width],
        "frames_in_clip": len(axis),
        "walls_s": {
            "shipped_analysis": shipped_analysis_s,
            "candidate_analysis": candidate_analysis_s,
        },
        "statistics_movement": movement,
        "frames": frames,
    }


def run_item(
    item: Mapping[str, Any],
    pack: Path,
    footage: Path,
    items_dir: Path,
    cache_dir: Path,
    switches: hp.Switches,
    *,
    force_cpu: bool = False,
) -> str:
    """Process one whole-set item into ``items_dir/<item>`` (staged; published on success).

    An item whose folder exists is skipped (a resumed batch). The work is done in
    ``.<item>.staging-<stamp>``, renamed to ``<item>`` with its record on success; a failure keeps
    the staging folder as ``.<item>.failed-<stamp>`` and is reported, not raised.

    Args:
        item: The pack manifest entry.
        pack: The pack folder (read only).
        footage: The footage folder (read only).
        items_dir: The items' folder.
        cache_dir: The analysis cache folder.
        switches: The candidate.
        force_cpu: Process on the CPU.

    Returns:
        ``"skipped"``, ``"done"`` or ``"FAILED: <reason>"``.
    """
    name = str(item["item"])
    hp._check_name(name)
    out = items_dir / name
    if out.exists():
        return "skipped"
    stamp = _stamp()
    staging = items_dir / f".{name}.staging-{stamp}"
    staging.mkdir(parents=True)
    began = time.perf_counter()
    method = available_methods()[CANDIDATE_METHOD]
    if not isinstance(method, AncutiFusionMethod):
        raise hp.ProbeError(f"{CANDIDATE_METHOD} is not an Ancuti fusion method")
    try:
        path = item_source(item, pack, footage)
        if item["kind"] == "photo":
            run = process_photo(path, method, switches, staging, force_cpu=force_cpu)
        else:
            run = process_video(
                path,
                method,
                switches,
                staging,
                stills=item.get("stills") or [],
                cache_dir=cache_dir,
                force_cpu=force_cpu,
            )
        record = {
            "tool": "halo_part3 wholeset-run",
            "item": name,
            "group": item["group"],
            "source": path.name,
            "method": method.id,
            "candidate": switches.describe(),
            "item_wall_s": time.perf_counter() - began,
            **run,
        }
        _write_json(staging / f"{name}.json", record)
        staging.rename(out)
    except Exception as exc:  # recorded per item; the batch goes on
        staging.rename(items_dir / f".{name}.failed-{stamp}")
        return f"FAILED: {type(exc).__name__}: {exc}"
    return "done"


def item_summary(record: Mapping[str, Any]) -> dict[str, Any]:
    """One item's sheet figures from its record (largest over its frames)."""
    frames = record["frames"]
    whole = [f["whole_image"] for f in frames]
    scans = [f["edge_scan"]["summary"] for f in frames]
    worst = max(range(len(frames)), key=lambda i: whole[i]["mean_abs_difference"])
    movement = record.get("statistics_movement") or {}

    def scan(name: str) -> dict[str, Any]:
        return {
            "band": sum(s[name]["band"] for s in scans),
            "none": sum(s[name]["none"] for s in scans),
            "undecided": sum(s[name]["undecided"] for s in scans),
            "max_qualifying_band": max(s[name]["max_qualifying_band"] for s in scans),
        }

    return {
        "item": record["item"],
        "group": record["group"],
        "kind": record["kind"],
        "frames": len(frames),
        "worst_tag": frames[worst]["tag"],
        "mean_abs_difference": max(w["mean_abs_difference"] for w in whole),
        "p99_abs_difference": max(w["p99_abs_difference"] for w in whole),
        "max_mean_shift": max(abs(v) for w in whole for v in w["mean_shift_rgb"]),
        "clipped_shipped": max(w["baseline_clipped_fraction"] for w in whole),
        "clipped_candidate": max(w["clipped_fraction"] for w in whole),
        "scan_shipped": scan("shipped"),
        "scan_candidate": scan("candidate"),
        "input2_saliency_max_abs": movement.get("input2_saliency_max_abs"),
        "item_wall_s": record["item_wall_s"],
        "walls_s": record["walls_s"],
    }


def select_contact(summaries: Sequence[Mapping[str, Any]]) -> list[str]:
    """The contact sheet's items, in order (see the module docstring).

    First the :data:`CONTACT_VIDEO_SLOTS` video items with the largest
    ``input2_saliency_max_abs``, then the largest ``mean_abs_difference`` among the rest, to
    :data:`CONTACT_ITEMS`; ties by item name.

    Args:
        summaries: :func:`item_summary` of every item.

    Returns:
        The item names.
    """
    videos = sorted(
        (s for s in summaries if s["kind"] == "video" and s["input2_saliency_max_abs"] is not None),
        key=lambda s: (-s["input2_saliency_max_abs"], s["item"]),
    )
    chosen = [s["item"] for s in videos[:CONTACT_VIDEO_SLOTS]]
    rest = sorted(
        (s for s in summaries if s["item"] not in chosen),
        key=lambda s: (-s["mean_abs_difference"], s["item"]),
    )
    chosen += [s["item"] for s in rest[: CONTACT_ITEMS - len(chosen)]]
    return chosen


def scan_regressions(summaries: Sequence[Mapping[str, Any]], chosen: Sequence[str]) -> list[str]:
    """The items outside ``chosen`` whose edge scan rises under the candidate, by name.

    A rise: more qualifying sides, or a larger largest qualifying band, than at the shipped
    defaults (a possible regression, shown beside the 20 with its figures).
    """
    out = []
    for s in sorted(summaries, key=lambda s: s["item"]):
        shipped, candidate = s["scan_shipped"], s["scan_candidate"]
        rises = candidate["band"] > shipped["band"] or (
            candidate["max_qualifying_band"] > shipped["max_qualifying_band"]
        )
        if rises and s["item"] not in chosen:
            out.append(s["item"])
    return out


def preview(left: Path, right: Path, target: Path) -> None:
    """A side-by-side 8-bit preview: ``left`` | ``right``, each scaled to :data:`PREVIEW_WIDTH`."""
    with PILImage.open(left) as a, PILImage.open(right) as b:
        height = round(a.height * PREVIEW_WIDTH / a.width)
        sheet = PILImage.new("RGB", (2 * PREVIEW_WIDTH + 8, height), (255, 255, 255))
        sheet.paste(a.convert("RGB").resize((PREVIEW_WIDTH, height), PILImage.Resampling.LANCZOS))
        sheet.paste(
            b.convert("RGB").resize((PREVIEW_WIDTH, height), PILImage.Resampling.LANCZOS),
            (PREVIEW_WIDTH + 8, 0),
        )
        sheet.save(target)


def nearest_crop(folder: Path, at: float) -> Path:
    """The probe's output crop (``tSSSS.sss-output.png``) in ``folder`` nearest to ``at`` s.

    A path that does not exist when the folder holds no crop within half a frame at 60 fps.
    """
    best: tuple[float, Path] | None = None
    for path in folder.glob("t*-output.png"):
        try:
            seconds = float(path.name[1:].split("-", 1)[0])
        except ValueError:
            continue
        if best is None or abs(seconds - at) < best[0]:
            best = (abs(seconds - at), path)
    if best is None or best[0] > 1.0 / 120.0:
        return folder / f"t{at:08.3f}-output.png"
    return best[1]


def undecided_crops(work: Path) -> list[dict[str, Any]]:
    """C2's crop pairs (shipped | candidate) for :data:`UNDECIDED_LINES`, where they exist.

    Photos read Part 2's crops (``part2/defaults`` and ``part2/d-unsharpened-1``, read only);
    videos the window's probe runs (``part3/crops/<setting>/<item>``, the probe's crop of the
    frame nearest the time, :func:`nearest_crop`).

    Args:
        work: The working folder.

    Returns:
        Per line: the item, time, line, verdict and the two crop paths (None when absent).
    """
    rows = []
    for item, at, line, verdict in UNDECIDED_LINES:
        if at is None:
            shipped = work / "wp5.7" / "part2" / "defaults" / item / "photo-output.png"
            candidate = work / "wp5.7" / "part2" / "d-unsharpened-1" / item / "photo-output.png"
        else:
            shipped = nearest_crop(work / PART3 / "crops" / "shipped" / item, at)
            candidate = nearest_crop(work / PART3 / "crops" / "candidate" / item, at)
        rows.append(
            {
                "item": item,
                "time_s": at,
                "line": line,
                "verdict_under_candidate": verdict,
                "shipped": shipped if shipped.is_file() else None,
                "candidate": candidate if candidate.is_file() else None,
            }
        )
    return rows


def published_records(items_dir: Path, listed: Sequence[str]) -> list[dict[str, Any]]:
    """The published item records, exactly one per listed item, in folder-name order.

    Only published folders are read: a folder whose name starts with ``.`` is a staging
    (``.<item>.staging-<stamp>``) or kept failed (``.<item>.failed-<stamp>``) folder of
    :func:`run_item`, whose record may be complete but was never published, and is skipped;
    files beside the folders are skipped. Each published folder must hold exactly one record,
    ``<item>.json``, whose ``item`` is the folder's name (Reviewer A round 5 finding 2: a staging
    copy left by an interrupt was counted beside its resumed publication).

    Args:
        items_dir: The whole-set ``items`` folder.
        listed: The items the sheet covers (:func:`wholeset_items`' names).

    Returns:
        The records.

    Raises:
        hp.ProbeError: The records are not exactly the listed items (one missing, unlisted or
            duplicated, a folder without its record or with a second one): the sheet fails.
    """
    records: list[dict[str, Any]] = []
    problems: list[str] = []
    for folder in sorted(items_dir.iterdir(), key=lambda p: p.name):
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        found = sorted(p.name for p in folder.glob("*.json"))
        if found != [f"{folder.name}.json"]:
            problems.append(f"{folder.name}: records {found or 'none'}")
            continue
        record = json.loads((folder / found[0]).read_text(encoding="utf-8"))
        if record.get("item") != folder.name:
            problems.append(f"{folder.name}: its record names {record.get('item')!r}")
            continue
        records.append(record)
    names = [str(r["item"]) for r in records]
    missing = sorted(set(listed) - set(names))
    unlisted = sorted(set(names) - set(listed))
    duplicated = sorted({n for n in names if names.count(n) > 1})
    problems += [f"missing {', '.join(missing)}"] if missing else []
    problems += [f"unlisted {', '.join(unlisted)}"] if unlisted else []
    problems += [f"duplicated {', '.join(duplicated)}"] if duplicated else []
    if problems or len(records) != len(listed):
        raise hp.ProbeError(
            f"the published records are not exactly the listed items ({len(records)} records, "
            f"{len(listed)} listed): {'; '.join(problems)}"
        )
    return records


def build_sheet(out: Path, work: Path) -> dict[str, Any]:
    """The per-item table, the contact sheet of 20 and C2's crops, from the items' records.

    The records are :func:`published_records` of ``out/items`` against the whole set
    (:func:`wholeset_items` of the CP5 pack: 70 photos and 50 videos); any other population
    fails before the sheet folder is made. The sheet is built in a fresh staging folder,
    ``.sheet-<stamp>.staging-<stamp>``, and published as ``sheet-<stamp>`` by one rename with the
    probe's own helpers (:func:`halo_probe._publish`; on any exception
    :func:`halo_probe._abandon` removes an empty staging folder or keeps a partial one as
    ``.sheet-<stamp>.failed-<stamp>``), so an interrupt never leaves a ``sheet-*`` folder
    (Reviewer B finding 2).

    Args:
        out: The whole-set folder (``items/`` inside it; the sheet is written beside it).
        work: The working folder (the CP5 pack's list and the crops).

    Returns:
        The summary record (also written as ``sheet-<stamp>.json``).

    Raises:
        hp.ProbeError: The published records are not exactly the whole set.
    """
    listed = [str(item["item"]) for item in wholeset_items(work / PACK)]
    records = published_records(out / "items", listed)
    summaries = [item_summary(r) for r in records]
    chosen = select_contact(summaries)
    regressions = scan_regressions(summaries, chosen)
    stamp = _stamp()
    sheet = out / f"sheet-{stamp}"
    staging = out / f".{sheet.name}.staging-{stamp}"
    staging.mkdir()  # exclusive, as the probe's staging folder
    try:
        record = _write_sheet(staging, out, work, summaries, chosen, regressions)
        hp._publish(staging, sheet, None)
    except BaseException as exc:
        note = hp._abandon(staging, out / f".{sheet.name}.failed-{stamp}")
        if note:
            exc.add_note(f"halo_part3: the sheet was not published{note}")
        raise
    return record


def _write_sheet(
    sheet_dir: Path,
    out: Path,
    work: Path,
    summaries: Sequence[Mapping[str, Any]],
    chosen: Sequence[str],
    regressions: Sequence[str],
) -> dict[str, Any]:
    """Write the sheet's files into ``sheet_dir`` (:func:`build_sheet`'s staging folder).

    Nothing written names ``sheet_dir`` itself (the page's previews are relative), so the
    folder publishes by rename.

    Args:
        sheet_dir: The staging folder (exists, empty).
        out: The whole-set folder (the items' renders are linked in place).
        work: The working folder (C2's crops).
        summaries: :func:`item_summary` of every item.
        chosen: :func:`select_contact`'s items.
        regressions: :func:`scan_regressions`' items.

    Returns:
        The summary record (also written as ``sheet.json``).
    """
    by_name = {s["item"]: s for s in summaries}
    cards = []
    for rank, name in enumerate([*chosen, *regressions], start=1):
        tag = by_name[name]["worst_tag"]
        left = out / "items" / name / f"{tag}-shipped.png"
        right = out / "items" / name / f"{tag}-candidate.png"
        target = sheet_dir / f"{rank:02d}-{name}-{tag}.png"
        preview(left, right, target)
        cards.append((rank, name, tag, target.name, left, right))
    crops = undecided_crops(work)
    page = [
        "<!doctype html><meta charset='utf-8'><title>WP5.7 Part 3 contact sheet</title>",
        "<h1>WP5.7 Part 3: shipped defaults (left) | candidate (d) 1 sigma (right)</h1>",
        "<p>Renders shown as 8-bit values, not display-converted; both halves alike. Selection: "
        f"the {CONTACT_VIDEO_SLOTS} video items whose input-2 saliency mean moves most, then the "
        "largest whole-image mean absolute change; after them, every other item whose edge scan "
        "rises under (d) (more qualifying sides or a larger band). No preference judgement is "
        "made here.</p>",
    ]
    for rank, name, tag, file_name, left, right in cards:
        s = by_name[name]
        a, b = s["scan_shipped"], s["scan_candidate"]
        why = "scan rises under (d)" if name in regressions else "contact sheet"
        page.append(
            f"<h2>{rank}. {html.escape(name)} ({s['group']}, {tag}; {why})</h2><p>edge scan "
            f"b/n/u {a['band']}/{a['none']}/{a['undecided']} max {a['max_qualifying_band']:.3f} -> "
            f"{b['band']}/{b['none']}/{b['undecided']} max {b['max_qualifying_band']:.3f}; "
            "mean abs "
            f"{s['mean_abs_difference']:.4f}, p99 {s['p99_abs_difference']:.4f}, max mean shift "
            f"{s['max_mean_shift']:.4f}, input-2 saliency moved {s['input2_saliency_max_abs']}; "
            f"full size: <a href='{left.as_uri()}'>shipped</a> | "
            f"<a href='{right.as_uri()}'>candidate</a></p><img src='{file_name}' width='100%'>"
        )
    page.append("<h1>C2: the lines not shown absent under (d) 1 sigma (shipped | candidate)</h1>")
    for row in crops:
        when = "photo" if row["time_s"] is None else f"{row['time_s']:.3f} s"
        images = " ".join(
            f"<img src='{p.as_uri()}' height='360'>" if p else "(crop missing)"
            for p in (row["shipped"], row["candidate"])
        )
        page.append(
            f"<h2>{html.escape(row['item'])} {when} line {row['line']}: "
            f"{row['verdict_under_candidate']} under (d)</h2><p>{images}</p>"
        )
    (sheet_dir / "contact-sheet.html").write_text("\n".join(page) + "\n", encoding="ascii")
    record = {
        "tool": "halo_part3 wholeset-sheet",
        "items": len(summaries),
        "contact": chosen,
        "scan_regressions": regressions,
        "summaries": summaries,
        "crops": [
            {**r, "shipped": str(r["shipped"]), "candidate": str(r["candidate"])} for r in crops
        ],
    }
    _write_json(sheet_dir / "sheet.json", record)
    (sheet_dir / "summary.tsv").write_text(summary_tsv(summaries), encoding="ascii")
    return record


def summary_tsv(summaries: Sequence[Mapping[str, Any]]) -> str:
    """The per-item table as tab-separated text (ASCII)."""
    head = [
        "item", "group", "kind", "frames", "mean_abs", "p99", "max_mean_shift", "clipped_s",
        "clipped_d", "scan_s_b/n/u", "scan_s_max", "scan_d_b/n/u", "scan_d_max", "sal2_moved",
        "item_wall_s",
    ]  # fmt: skip
    lines = ["\t".join(head)]
    for s in summaries:
        a, b = s["scan_shipped"], s["scan_candidate"]
        lines.append(
            "\t".join(
                [
                    s["item"],
                    s["group"],
                    s["kind"],
                    str(s["frames"]),
                    f"{s['mean_abs_difference']:.4f}",
                    f"{s['p99_abs_difference']:.4f}",
                    f"{s['max_mean_shift']:.4f}",
                    f"{s['clipped_shipped']:.4f}",
                    f"{s['clipped_candidate']:.4f}",
                    f"{a['band']}/{a['none']}/{a['undecided']}",
                    f"{a['max_qualifying_band']:.3f}",
                    f"{b['band']}/{b['none']}/{b['undecided']}",
                    f"{b['max_qualifying_band']:.3f}",
                    str(s["input2_saliency_max_abs"]),
                    f"{s['item_wall_s']:.1f}",
                ]
            )
        )
    return "\n".join(lines) + "\n"


# --- command line -------------------------------------------------------------------------------


def _parser() -> argparse.ArgumentParser:
    """The command-line parser."""
    parser = argparse.ArgumentParser(prog="halo_part3", description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    v3 = commands.add_parser("v3", help="V3 and AD-14 on WP4.2's clips, shipped then candidate")
    v3.add_argument("--out", type=Path, required=True, help="a NEW folder below wp5.7/part3")
    v3.add_argument("--switch", action="append", default=None, metavar="SWITCH")
    v3.add_argument("--method", action="append", default=None, metavar="ID")
    n6 = commands.add_parser("n6", help="one timed GX011627 export by export_bench")
    n6.add_argument("--setting", choices=N6_SETTINGS, required=True)
    n6.add_argument("--subdir", default=str(PART3 / "n6"))
    n6.add_argument("--keep", action="store_true")
    summary = commands.add_parser("n6-summary", help="the N6 row from the runs' records")
    summary.add_argument("--subdir", default=str(PART3 / "n6"))
    listing = commands.add_parser("wholeset-list", help="the 120 other CP5 items")
    listing.add_argument("--kind", choices=("photo", "video"))
    run = commands.add_parser("wholeset-run", help="process whole-set items")
    run.add_argument("items", nargs="+")
    run.add_argument("--out", type=Path, help="default <working>/wp5.7/part3/wholeset")
    run.add_argument("--cache-dir", type=Path, help="default <working>/wp5.7/part3/cache")
    run.add_argument("--force-cpu", action="store_true")
    sheet = commands.add_parser("wholeset-sheet", help="the table, contact sheet and crops")
    sheet.add_argument("--out", type=Path, help="default <working>/wp5.7/part3/wholeset")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run one subcommand.

    Args:
        argv: The arguments; ``sys.argv[1:]`` when None.

    Returns:
        The exit status: 0 done; 1 a failure (an item, or the bench); 2 a refusal (among them
        ``v3 --switch full_res_bounds``); 3 the bench's failed memory check (``n6``); 4 a STOP
        (``v3``: no reproduction; ``n6-summary``: a VALID summary's effect over 10 %);
        :data:`N6_INVALID_EXIT` (5) ``n6-summary`` on runs that are not the protocol of record.
    """
    args = _parser().parse_args(argv)
    try:
        config = load_local_config()
        work = config.working_path
        pack = work / PACK
        if args.command == "v3":
            out = checked_output(Path(args.out))
            if out.exists():
                raise hp.ProbeError(f"{out} exists; each V3 run writes a new folder")
            switches = hp.parse_switches(args.switch or [CANDIDATE])
            if switches.full_res_bounds:
                raise hp.ProbeError(
                    "v3 does not take --switch full_res_bounds: nothing in the V3 legs overrides "
                    "the bounds, so it would be recorded without taking effect (Part 3's V3 "
                    f"candidate is (d), {CANDIDATE})"
                )
            modules = suite()
            methods = tuple(args.method or modules.wp42.METHODS)
            out.mkdir(parents=True)
            sample = sample_provider(modules, out / "fixtures")
            record, status = run_v3(modules, out, switches, methods, sample)
            _write_json(out / "v3.json", record)
            (out / "v3-table.md").write_text(v3_table(record), encoding="ascii")
            if status:
                print(f"STOP: {record['stop']}")
            return status
        if args.command == "n6":
            if not Path(args.subdir).as_posix().startswith(PART3.as_posix() + "/"):
                raise hp.ProbeError(f"--subdir must lie below {PART3.as_posix()}")
            return run_n6(args.setting, args.subdir, args.keep)
        if args.command == "n6-summary":
            result = n6_summary(work / args.subdir)
            text = n6_text(result)
            print(text, end="")
            folder = checked_output(work / args.subdir)
            _write_json(folder / f"n6-summary-{_stamp()}.json", result)
            if not result["valid"]:
                return N6_INVALID_EXIT
            return 4 if result["stop"] else 0
        items = wholeset_items(pack)
        if args.command == "wholeset-list":
            for item in items:
                if args.kind is None or item["kind"] == args.kind:
                    print(item["item"])
            return 0
        out = checked_output(Path(args.out) if args.out else work / PART3 / "wholeset")
        if args.command == "wholeset-run":
            cache_dir = checked_output(
                Path(args.cache_dir) if args.cache_dir else work / PART3 / "cache"
            )
            by_name = {item["item"]: item for item in items}
            unknown = [name for name in args.items if name not in by_name]
            if unknown:
                raise hp.ProbeError(f"not whole-set items: {', '.join(unknown)}")
            switches = hp.parse_switches([CANDIDATE])
            (out / "items").mkdir(parents=True, exist_ok=True)
            failed = 0
            for name in args.items:
                began = time.perf_counter()
                result_text = run_item(
                    by_name[name],
                    pack,
                    config.footage_path,
                    out / "items",
                    cache_dir,
                    switches,
                    force_cpu=args.force_cpu,
                )
                failed += result_text.startswith("FAILED")
                print(
                    f"ITEM {name} {result_text} wall={time.perf_counter() - began:.1f}s", flush=True
                )
            return 1 if failed else 0
        record = build_sheet(out, work)
        print(f"SHEET {len(record['summaries'])} items; contact: {', '.join(record['contact'])}")
        return 0
    except (hp.ProbeError, LocalConfigError) as exc:
        print(f"halo_part3: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
