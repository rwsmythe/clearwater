"""Run the WP1.4 noise-and-statistics experiments (shallow part) on the owner's footage.

Usage::

    uv run python tools/statistics_experiments.py extract [--long] [--config FILE] [--device ...]
    uv run python tools/statistics_experiments.py analyse [--long] [--config FILE] [--device ...]
    uv run python tools/statistics_experiments.py render  [--config FILE] [--device ...]

The footage folder is only ever an input. Every file is written under
``<working folder>/wp1.4/`` (``wp-dr25/`` with ``--long``) after
:class:`lookcheck.frames.OutputRoots` has checked it
(inside that folder, outside the footage folder, no shared hard link); ``FFREPORT`` is
stripped from every FFmpeg and ffprobe run (:func:`lookcheck.frames.tool_env`). A chapter is
found by its stem anywhere under the footage folder (:func:`local_config.find_footage_file`);
a missing or ambiguous chapter is refused before anything is written.

Two excerpts (:data:`EXCERPTS`): ``GX011627`` (WP1.3's flicker excerpt, 6 s from 30 % of the
duration; its pts ticks are asserted) and ``GX011625`` (6 s from 50 %). Each phase reads what
the previous one wrote in ``wp1.4/<excerpt>/``:

``extract``
    Decodes every frame of each excerpt at full resolution as 16-bit PNG
    (:func:`lookcheck.frames.excerpt`), builds each frame's analysis proxy (a 4x4 area
    average to 960x540, :func:`prototype.temporal.proxy`, saved as ``proxies.npy``), and
    measures each frame's own (raw, unsmoothed) whole-frame statistics on the proxy for both
    methods, and for ``GX011627`` also on the full frame: ``excerpt.json``,
    ``statistics-raw.json``. The full-resolution PNGs of an excerpt that is not rendered are
    then removed but for the first, middle and last.
``analyse``
    From the proxies: the STAGED and the FLAT analysis with the centred 1.0 s Gaussian
    (``statistics-staged.json``, ``statistics-flat.json``), then the experiments
    (``results.json``, ``flicker.png``): the flat-minus-staged mismatch, the proxy-versus-full
    gap, the flicker of the unsmoothed, staged and flat renders, the smoothing candidates
    and the robust candidates for the N{} bounds.
``render``
    Renders every frame of ``GX011627`` at full resolution three ways through the
    supplied-statistics hook (``ancuti2018``, blue off): ``unsmoothed`` (each frame's own
    full-frame statistics, the same as WP1.3's clip), ``staged`` and ``flat`` (the smoothed
    proxy statistics), encodes and verifies each clip as WP1.3 did
    (:func:`lookcheck.pack.encode_verified_pair`: NVENC, the source's tags, every frame read
    back), writes ``render.json``, and then removes the full-resolution PNGs but for the
    first, middle and last of each set.

``--long`` selects two 20 s excerpts for WP-DR25, with the same requested starts
but clamped back to fit the chapters. It skips full-frame statistics and clip
rendering. The window study covers both methods and records per-step flicker
and edge-free counts, using each method's staged reach (flat: one filter radius).
The default WP1.4 study and its fixed interior margin are unchanged.

Exit status 0 on success; 2, with a one-line ``error: ...`` on standard error, on a
configuration, probe, device, path, FFmpeg or premise failure.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import json
import sys
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

if not __package__:
    # Script mode: sys.path[0] is tools/, which holds the lookcheck, prototype and
    # local_config modules.
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from local_config import LocalConfigError, find_footage_file, load_local_config
from lookcheck.frames import (
    ExtractError,
    OutputRoots,
    excerpt,
    probe_stream,
    read_png16,
    run_ffprobe,
    tool_version,
)
from lookcheck.pack import encode_verified_pair, plot_series
from prototype import temporal
from prototype.backend import DEVICES, Backend, select_backend
from prototype.params import Params
from prototype.pipeline import Statistics
from prototype.run import write_png16
from prototype.temporal import (
    COMPARISON_SMOOTHER,
    ROBUST_CANDIDATES,
    SMOOTHING_CANDIDATES,
    Series,
    Smoother,
)

WORK_SUBDIR = "wp1.4"
"""The folder inside the working folder that every output goes to."""

RECORD_SCHEMA = 1

METHODS: dict[str, Params] = {
    "ancuti2018": Params(method="ancuti2018", blue_compensation=False),
    "c3": Params(method="c3"),
}
"""The two methods of the statistics study, at the defaults (blue compensation off)."""

RENDER_METHOD = "ancuti2018"
"""The one method of the renders and of the smoothing and robust studies (brief decision)."""

VERSIONS = ("unsmoothed", "staged", "flat")
"""The three full-resolution renders of the first excerpt, for the owner at CP2."""


PROXY_METHOD = (
    "area average in NumPy from the full-resolution 16-bit frame: each 4x4 block of the "
    "3840x2160 frame replaced by its mean (float64 accumulation, cast to float32), giving "
    "960x540 (prototype.temporal.proxy)"
)

NEAR_FLAT_SEED = 0
NEAR_FLAT_RGB = (0.10, 0.45, 0.55)
NEAR_FLAT_NOISE = 0.002
"""The synthetic near-flat frame of the DR-14 check: a uniform blue-green 960x540 frame plus
Gaussian noise of this standard deviation (seed :data:`NEAR_FLAT_SEED`)."""


def interior_margin(frame_rate: Fraction) -> int:
    """Return the flicker's interior margin in frames: the widest candidate's filter reach.

    The interior frame set holds the frames at least this far from either end of an excerpt,
    where no smoothing candidate's single filter chain reaches the edge rule
    (:meth:`prototype.temporal.Smoother.radius`: the 4 s ``median_gaussian`` reaches 60 frames,
    2.00 s, at 30000/1001 fps: 59 for its Gaussian and 1 for its median). That holds exactly for
    the flat analysis. The staged analysis nests its stages, so its reach is the number of stages
    times the radius (:func:`staged_reach`) and the interior is edge-free for it only where that
    is within the margin.

    Args:
        frame_rate: Frames per second.

    Returns:
        The largest :meth:`prototype.temporal.Smoother.radius` over the smoothing candidates.
    """
    return max(smoother.radius(frame_rate) for smoother in SMOOTHING_CANDIDATES)


def staged_reach(method: str, smoother: Smoother, frame_rate: Fraction) -> int:
    """Return the frames on each side that can influence one STAGED output value.

    Stage ``k`` is measured on frames corrected with the smoothed stages before it and is then
    smoothed itself, so each stage adds one filter radius: ``len(STAGES[method]) * radius``.

    Args:
        method: ``"ancuti2018"`` (3 stages) or ``"c3"`` (2 stages).
        smoother: The filter.
        frame_rate: Frames per second.

    Returns:
        The reach of the nested analysis in frames.
    """
    return len(temporal.STAGES[method]) * smoother.radius(frame_rate)


FLICKER_DEFINITION = (
    "per frame step and signal (R, G, B mean and BT.709 luma mean of the rendered proxy), "
    "|(s[t+1] - s[t]) - (r[t+1] - r[t])| in 8-bit levels, where r is the same proxy rendered "
    "with constant statistics (the mean of the method's raw series); averaged over the steps "
    "and the four signals (prototype.temporal.flicker). An instrument of WP1.4, not V3 (D112)."
)


class PremiseError(ExtractError):
    """A premise the brief fixes does not hold on the footage (a STOP, not a workaround)."""


@dataclass(frozen=True)
class ExcerptSpec:
    """One excerpt of the study.

    Attributes:
        name: Folder name under the selected output root and the clips' stem.
        chapter: The chapter file's stem in the footage folder.
        start_fraction: Start as a fraction of the probed stream duration.
        duration_s: Length in seconds.
        full_frame: Whether the raw statistics are also measured on the full frames.
        render: Whether the three full-resolution clips are rendered from it.
        expected_ticks: ``(first, last, step)`` pts ticks the excerpt must have, or ``None``.
    """

    name: str
    chapter: str
    start_fraction: float
    duration_s: float
    full_frame: bool
    render: bool
    expected_ticks: tuple[int, int, int] | None = None


EXCERPTS = (
    ExcerptSpec("GX011627", "GX011627", 0.30, 6.0, True, True, (205205, 384384, 1001)),
    ExcerptSpec("GX011625", "GX011625", 0.50, 6.0, False, False),
)
"""The first excerpt is WP1.3's flicker excerpt (WP1.3 report section 5); the second is 6 s at
50 % of a second shallow chapter."""


LONG_EXCERPTS = (
    ExcerptSpec("GX011627-long", "GX011627", 0.30, 20.0, False, False),
    ExcerptSpec("GX011625-long", "GX011625", 0.50, 20.0, False, False),
)
"""WP-DR25's 20 s excerpts; requested starts are clamped back when needed to fit."""


# --- small checked writers ------------------------------------------------------------------------


def _now() -> str:
    """The current UTC time to the second, ISO 8601."""
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


def _write_json(roots: OutputRoots, path: Path, document: Mapping[str, Any]) -> None:
    """Write indented JSON after checking the path; NaN and infinity are errors."""
    roots.write_text(path, json.dumps(document, indent=2, allow_nan=False) + "\n")


def _read_json(path: Path) -> dict[str, Any]:
    """Read a JSON object written by this runner."""
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError(f"{path} does not hold a JSON object")
    return document


def _write_png(roots: OutputRoots, path: Path, image: NDArray[np.float32]) -> None:
    """Write a 16-bit PNG with the prototype's writer after checking the path."""
    target = roots.check(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    write_png16(target, image)


def _save_array(roots: OutputRoots, path: Path, array: NDArray[Any]) -> None:
    """Save a NumPy array (``.npy``) after checking the path."""
    target = roots.check(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("wb") as handle:
        np.save(handle, array, allow_pickle=False)


def _keep(count: int) -> set[int]:
    """The frames whose full-resolution PNGs are kept: the first, the middle and the last."""
    return {0, count // 2, count - 1}


# --- series in records ----------------------------------------------------------------------------


def series_record(
    series: Mapping[str, NDArray[np.float64]], frames: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    """Turn a series into per-frame JSON entries with the frame's pts.

    Args:
        series: Scalar name to one value per frame.
        frames: The excerpt's frame entries (``index``, ``pts_ticks``, ``pts_seconds``).

    Returns:
        One entry per frame: ``index``, ``pts_ticks``, ``pts_seconds`` and ``statistics``
        (name to value).
    """
    return [
        {
            "index": frame["index"],
            "pts_ticks": frame["pts_ticks"],
            "pts_seconds": frame["pts_seconds"],
            "statistics": {name: float(values[number]) for name, values in series.items()},
        }
        for number, frame in enumerate(frames)
    ]


def check_ticks(entries: Sequence[Mapping[str, Any]], ticks: Sequence[int], label: str) -> None:
    """Refuse a record whose frames are not the excerpt's, in order (matched on ``pts_ticks``).

    A series is applied to the frames BY POSITION, so a reordered, shortened or stale record
    would render the wrong statistics onto a frame and nothing downstream would notice.

    Args:
        entries: The record's per-frame entries.
        ticks: The excerpt's ``pts_ticks``, in presentation order (its ``excerpt.json``).
        label: What the record is, for the message.

    Raises:
        ValueError: The record's ``pts_ticks`` sequence differs from ``ticks``.
    """
    found = [entry["pts_ticks"] for entry in entries]
    if found == list(ticks):
        return
    first = next(
        (n for n, (a, b) in enumerate(zip(found, ticks, strict=False)) if a != b),
        min(len(found), len(ticks)),
    )
    raise ValueError(
        f"{label}: the record's pts_ticks are not the excerpt's, in order ({len(found)} entries "
        f"against {len(ticks)}; first difference at position {first})"
    )


def series_from_record(
    entries: Sequence[Mapping[str, Any]], ticks: Sequence[int], label: str
) -> Series:
    """Inverse of :func:`series_record`, after :func:`check_ticks`.

    Args:
        entries: The per-frame entries.
        ticks: The excerpt's ``pts_ticks``, in order; the entries must carry exactly these.
        label: What the record is, for the message of a refusal.

    Returns:
        The series.

    Raises:
        ValueError: The entries' ``pts_ticks`` are not ``ticks``, in order.
    """
    check_ticks(entries, ticks, label)
    names = list(entries[0]["statistics"])
    return {
        name: np.array([entry["statistics"][name] for entry in entries], dtype=np.float64)
        for name in names
    }


# --- extract --------------------------------------------------------------------------------------


def require_frames(name: str, count: int) -> None:
    """Refuse an excerpt with fewer than :data:`prototype.temporal.MIN_FRAMES` frames, up front.

    The flicker measure needs one frame step, so two frames is the least that can complete
    ``analyse``. An interior result needs ``2 * margin + 2`` frames (:func:`_interior`); a
    shorter excerpt reports it as absent (``null``) instead.

    Args:
        name: The excerpt's name, for the message.
        count: Its number of frames.

    Raises:
        PremiseError: ``count`` is below the minimum.
    """
    if count < temporal.MIN_FRAMES:
        raise PremiseError(
            f"{name}: {count} frame(s); the experiments need at least {temporal.MIN_FRAMES} "
            "(the flicker measure needs one frame step)"
        )


def _duration_source(video: Path) -> str:
    """Recover the stream/container duration choice discarded by ``StreamInfo``."""
    document = run_ffprobe(
        [
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=duration:format=duration",
            str(video),
        ]
    )
    return "container" if document["streams"][0].get("duration") in (None, "N/A") else "stream"


def extract_excerpt(
    spec: ExcerptSpec, footage: Path, roots: OutputRoots, backend: Backend
) -> dict[str, Any]:
    """Decode an excerpt, build its proxies and measure its raw statistics (phase ``extract``).

    Writes, in ``roots.allowed / spec.name``: ``frames/`` (the full-resolution 16-bit PNGs,
    ``<chapter>_f0000.png``...), ``proxies.npy`` (float32, frames x 540 x 960 x 3),
    ``excerpt.json`` and ``statistics-raw.json`` (each frame's own statistics on the proxy
    for both methods, and on the full frame when ``spec.full_frame``). When ``spec.render``
    is false the full-resolution PNGs are then removed but for the first, middle and last.
    Long specs also record the requested start and duration source (stream or container),
    recovered with an additional read-only timing probe; default records are unchanged.

    Args:
        spec: The excerpt.
        footage: The footage folder (read only).
        roots: The output safety roots under the configured working folder.
        backend: Where the measurements run.

    Returns:
        The ``excerpt.json`` document.

    Raises:
        PremiseError: The excerpt's pts ticks differ from ``spec.expected_ticks``.
        local_config.FootageLookupError: The chapter is not in the footage folder, or is in it
            more than once (raised before anything is written).
        lookcheck.frames.ExtractError: A probe or decode fails.
        lookcheck.frames.OutputPathError: An output path is refused.
    """
    video = find_footage_file(spec.chapter, footage)  # refused before any write
    folder = roots.allowed / spec.name
    info = probe_stream(video)
    start = spec.start_fraction * info.duration_s
    is_long = spec in LONG_EXCERPTS
    duration_source = None
    if is_long:
        start = min(start, info.duration_s - spec.duration_s)
        duration_source = _duration_source(video)
    began = time.monotonic()
    frames = excerpt(video, start, spec.duration_s, folder / "frames", roots=roots, naming="index")
    print(
        f"{spec.name}: extracted {len(frames)} frames in {time.monotonic() - began:.0f} s",
        file=sys.stderr,
    )
    require_frames(spec.name, len(frames))
    ticks = [frame.pts_ticks for frame in frames]
    if spec.expected_ticks is not None:
        first, last, step = spec.expected_ticks
        if ticks != list(range(first, last + 1, step)):
            raise PremiseError(
                f"STOP: {spec.name} excerpt ticks {ticks[:2]}...{ticks[-1:]} ({len(ticks)} "
                f"frames) differ from the brief's {first}..{last} step {step}"
            )
    proxies: list[NDArray[np.float32]] = []
    raw_proxy: dict[str, list[Statistics]] = {name: [] for name in METHODS}
    raw_full: dict[str, list[Statistics]] = {name: [] for name in METHODS}
    for number, frame in enumerate(frames):
        image = read_png16(frame.path)
        small = temporal.proxy(image)
        proxies.append(small)
        for name, params in METHODS.items():
            raw_proxy[name].append(temporal.statistics_of(small, params, backend))
            if spec.full_frame:
                raw_full[name].append(temporal.statistics_of(image, params, backend))
        if number % 30 == 0:
            print(f"{spec.name}: measured {number + 1}/{len(frames)}", file=sys.stderr)
    _save_array(roots, folder / "proxies.npy", np.stack(proxies))
    entries = [{"index": number, **frame.record()} for number, frame in enumerate(frames)]
    document: dict[str, Any] = {
        "schema": RECORD_SCHEMA,
        "written": _now(),
        "excerpt": spec.name,
        "source": str(video),
        "start_fraction": spec.start_fraction,
        "start_s": start,
        "duration_s": spec.duration_s,
        "stream_duration_s": info.duration_s,
        "frame_rate": f"{info.frame_rate.numerator}/{info.frame_rate.denominator}",
        "time_base": f"{info.time_base.numerator}/{info.time_base.denominator}",
        "size": [info.width, info.height],
        "frames_count": len(frames),
        "first_pts_ticks": ticks[0],
        "last_pts_ticks": ticks[-1],
        "tags": info.tags.record(),
        "ffmpeg": tool_version("ffmpeg"),
        "extract_command": list(frames[0].command),
        "proxy": {"method": PROXY_METHOD, "shape": list(proxies[0].shape)},
        "device": backend.name,
        "frames": entries,
    }
    if is_long:
        document["requested_start_s"] = spec.start_fraction * info.duration_s
        document["duration_source"] = duration_source
    _write_json(roots, folder / "excerpt.json", document)
    raw: dict[str, Any] = {
        "schema": RECORD_SCHEMA,
        "written": _now(),
        "excerpt": spec.name,
        "kind": "raw: every frame's own statistics, unsmoothed (prototype.temporal.statistics_of)",
        "device": backend.name,
        "proxy": {
            name: {
                "params": dataclasses.asdict(METHODS[name]),
                "frames": series_record(temporal.stack(records), entries),
            }
            for name, records in raw_proxy.items()
        },
        "full": {
            name: {
                "params": dataclasses.asdict(METHODS[name]),
                "frames": series_record(temporal.stack(records), entries),
            }
            for name, records in raw_full.items()
            if records
        },
    }
    _write_json(roots, folder / "statistics-raw.json", raw)
    if not spec.render:
        for number, frame in enumerate(frames):
            if number not in _keep(len(frames)):
                roots.remove(frame.path)
    return document


# --- analyse --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Loaded:
    """What ``extract`` left for an excerpt.

    Attributes:
        folder: The excerpt's folder.
        excerpt: The ``excerpt.json`` document.
        proxies: The proxies, frames x H x W x 3.
        frame_rate: The source frame rate.
        raw: Per method the raw proxy series.
        raw_full: Per method the raw full-frame series (empty when not measured).
    """

    folder: Path
    excerpt: dict[str, Any]
    proxies: NDArray[np.float32]
    frame_rate: Fraction
    raw: dict[str, Series]
    raw_full: dict[str, Series]


def load_excerpt(folder: Path) -> Loaded:
    """Read an excerpt's ``excerpt.json``, ``proxies.npy`` and ``statistics-raw.json``.

    Args:
        folder: The excerpt's folder.

    Returns:
        The loaded data.

    Raises:
        PremiseError: The excerpt has fewer than :data:`prototype.temporal.MIN_FRAMES` frames.
        ValueError: A record's ``pts_ticks`` are not the excerpt's, in order, or the proxies
            are not one per frame.
    """
    document = _read_json(folder / "excerpt.json")
    raw = _read_json(folder / "statistics-raw.json")
    proxies = np.load(folder / "proxies.npy", allow_pickle=False)
    ticks = [entry["pts_ticks"] for entry in document["frames"]]
    require_frames(folder.name, len(ticks))
    if len(proxies) != len(ticks):
        raise ValueError(
            f"{folder.name}: proxies.npy holds {len(proxies)} frames, excerpt.json {len(ticks)}"
        )
    return Loaded(
        folder=folder,
        excerpt=document,
        proxies=proxies,
        frame_rate=Fraction(document["frame_rate"]),
        raw={
            name: series_from_record(m["frames"], ticks, f"statistics-raw.json proxy {name}")
            for name, m in raw["proxy"].items()
        },
        raw_full={
            name: series_from_record(m["frames"], ticks, f"statistics-raw.json full {name}")
            for name, m in raw["full"].items()
        },
    )


def analyse_statistics(
    folder: Path, roots: OutputRoots, backend: Backend, smoother: Smoother = COMPARISON_SMOOTHER
) -> dict[str, dict[str, Series]]:
    """Run the STAGED and the FLAT analysis for both methods (phase ``analyse``, first part).

    Writes ``statistics-staged.json`` (per method: the smoothed series, and per stage the
    series that stage measured before smoothing) and ``statistics-flat.json``.

    Args:
        folder: The excerpt's folder.
        roots: The output safety roots.
        backend: Where the measurements run.
        smoother: The filter of the comparison (the centred 1.0 s Gaussian).

    Returns:
        ``{"staged": {method: series}, "flat": {method: series}}``.
    """
    loaded = load_excerpt(folder)
    entries = loaded.excerpt["frames"]
    staged: dict[str, Series] = {}
    flat: dict[str, Series] = {}
    staged_document: dict[str, Any] = {}
    flat_document: dict[str, Any] = {}
    for name, params in METHODS.items():
        smoothed, measured = temporal.analyse_staged(
            list(loaded.proxies), params, smoother, loaded.frame_rate, backend
        )
        staged[name] = smoothed
        flat[name] = temporal.analyse_flat(loaded.raw[name], smoother, loaded.frame_rate)
        staged_document[name] = {
            "params": dataclasses.asdict(params),
            "stages": [stage.name for stage in temporal.STAGES[params.method]],
            "frames": series_record(smoothed, entries),
            "measured_per_stage": {
                stage: series_record(series, entries) for stage, series in measured.items()
            },
        }
        flat_document[name] = {
            "params": dataclasses.asdict(params),
            "frames": series_record(flat[name], entries),
        }
    common = {
        "schema": RECORD_SCHEMA,
        "written": _now(),
        "excerpt": loaded.excerpt["excerpt"],
        "smoother": _smoother_record(smoother, loaded.frame_rate),
        "device": backend.name,
    }
    _write_json(
        roots,
        folder / "statistics-staged.json",
        {
            **common,
            "kind": "staged (D97): each stage measured on the proxies corrected with the "
            "smoothed earlier stages, then smoothed",
            "methods": staged_document,
        },
    )
    _write_json(
        roots,
        folder / "statistics-flat.json",
        {
            **common,
            "kind": "flat (D98): every raw statistic smoothed independently",
            "methods": flat_document,
        },
    )
    return {"staged": staged, "flat": flat}


def _smoother_record(smoother: Smoother, frame_rate: Fraction) -> dict[str, Any]:
    """The filter's definition as it ran: kind, window, taps and kernel."""
    kernel = smoother.kernel(frame_rate)
    return {
        "kind": smoother.kind,
        "window_s": smoother.window_s,
        "frame_rate": f"{frame_rate.numerator}/{frame_rate.denominator}",
        "taps": len(kernel),
        "kernel": [float(w) for w in kernel],
        "edges": temporal.EDGE_MODE,
    }


def _signals(
    proxies: NDArray[np.float32],
    params: Params,
    series: Mapping[str, NDArray[np.float64]] | None,
    backend: Backend,
    constant: Statistics | None = None,
) -> NDArray[np.float64]:
    """Render every proxy and return the flicker signals of the outputs (frames x 4).

    ``series`` gives each frame its statistics; ``None`` renders each frame with its own
    (unsmoothed); ``constant`` renders every frame with the same record.
    """
    out = []
    for index, image in enumerate(proxies):
        if constant is not None:
            statistics: Statistics | None = constant
        elif series is None:
            statistics = None
        else:
            statistics = temporal.at(series, index)
        out.append(temporal.frame_signals(temporal.render(image, params, statistics, backend)))
    return np.array(out)


def _render_difference(
    proxies: NDArray[np.float32],
    params: Params,
    first: Mapping[str, NDArray[np.float64]],
    second: Mapping[str, NDArray[np.float64]],
    backend: Backend,
) -> dict[str, Any]:
    """Per frame, how far apart two renders of the same proxy are, in 8-bit levels.

    Returns:
        ``mean_abs`` (over pixels and channels) and ``max_abs`` (the largest single value)
        per frame, and over the frames the mean of ``mean_abs``, the largest ``mean_abs``
        and the largest ``max_abs`` with their frames.
    """
    mean_abs: list[float] = []
    max_abs: list[float] = []
    for index, image in enumerate(proxies):
        a = temporal.render(image, params, temporal.at(first, index), backend)
        b = temporal.render(image, params, temporal.at(second, index), backend)
        difference = np.abs(a.astype(np.float64) - b) * 255.0
        mean_abs.append(float(difference.mean()))
        max_abs.append(float(difference.max()))
    return _difference_summary(mean_abs, max_abs)


def _difference_summary(mean_abs: Sequence[float], max_abs: Sequence[float]) -> dict[str, Any]:
    """Summarise per-frame render differences (see :func:`_render_difference`)."""
    return {
        "mean_abs_levels": float(np.mean(mean_abs)),
        "largest_mean_abs_levels": float(np.max(mean_abs)),
        "largest_mean_abs_frame": int(np.argmax(mean_abs)),
        "largest_max_abs_levels": float(np.max(max_abs)),
        "largest_max_abs_frame": int(np.argmax(max_abs)),
        "per_frame_mean_abs": [float(v) for v in mean_abs],
        "per_frame_max_abs": [float(v) for v in max_abs],
    }


def _interior(count: int, frame_rate: Fraction) -> slice | None:
    """The frame steps between the interior frames (:func:`interior_margin`), if any.

    An excerpt of ``count`` frames has an interior only when ``count >= 2 * margin + 2``
    (122 frames at 30000/1001 fps); a shorter one returns ``None``.
    """
    margin = interior_margin(frame_rate)
    if count - 1 - 2 * margin < 1:
        return None
    return slice(margin, count - 1 - margin)


def _flicker_record(
    signals: NDArray[np.float64],
    reference: NDArray[np.float64],
    interior: slice | None,
    series: bool = False,
) -> dict[str, Any]:
    """The flicker over all steps and over the interior steps (and the per-step series)."""
    whole = temporal.flicker(signals, reference)
    record: dict[str, Any] = {
        "all": whole.value,
        "all_per_signal": whole.per_signal,
        "interior": None
        if interior is None
        else temporal.flicker(signals, reference, interior).value,
        "peak_step": int(np.argmax(whole.per_step.mean(axis=1))),
        "peak_value": float(whole.per_step.mean(axis=1).max()),
    }
    if series:
        record["per_step"] = [float(v) for v in whole.per_step.mean(axis=1)]
    return record


def _sequence_record(
    signals: NDArray[np.float64],
    reference: NDArray[np.float64],
    interior: slice | None,
    source_signals: NDArray[np.float64],
    series: bool = False,
) -> dict[str, Any]:
    """:func:`_flicker_record` plus the brief's source-referenced form, for every sequence."""
    record = _flicker_record(signals, reference, interior, series=series)
    record["source_referenced"] = temporal.source_referenced_flicker(signals, source_signals)
    return record


def _mismatch_record(
    first: Mapping[str, NDArray[np.float64]],
    second: Mapping[str, NDArray[np.float64]],
    entries: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """:func:`prototype.temporal.mismatch` with the pts of each worst frame."""
    report = temporal.mismatch(first, second)
    for values in report.values():
        values["pts_seconds"] = entries[int(values["frame"])]["pts_seconds"]
    return report


def _relative_step(values: NDArray[np.float64]) -> float:
    """Mean absolute frame-to-frame change of a bound over the mean absolute bound."""
    return float(np.abs(np.diff(values)).mean() / np.abs(values).mean())


def _near_flat_frame() -> NDArray[np.float32]:
    """The synthetic near-flat 960x540 frame of the DR-14 check (:data:`NEAR_FLAT_NOISE`)."""
    rng = np.random.default_rng(NEAR_FLAT_SEED)
    base = np.broadcast_to(np.array(NEAR_FLAT_RGB, dtype=np.float32), (540, 960, 3))
    noisy = base + rng.normal(0.0, NEAR_FLAT_NOISE, base.shape)
    return np.clip(noisy, 0.0, 1.0).astype(np.float32)


def robust_study(loaded: Loaded, params: Params, backend: Backend) -> dict[str, Any]:
    """Evaluate every robust candidate for the N{} bounds on the excerpt's proxies.

    Per frame, on the high-pass of the frame's own white-balanced proxy
    (:func:`prototype.temporal.white_balanced_high_pass`): each candidate's bounds and the
    fraction of pixels its stretch clips (a pixel counts when any channel is clipped; the
    fraction of channel samples is recorded beside it); and the effect on the result: the
    proxy rendered with the candidate's bounds supplied (everything else the frame's own)
    against the proxy rendered at the default, as the mean absolute difference in 8-bit levels.

    Args:
        loaded: The excerpt.
        params: The parameter set (``ancuti2018``).
        backend: Where the steps run.

    Returns:
        Per candidate: the per-frame bounds, the coefficient of variation of each bound
        over the frames (before smoothing), the clipped fraction of pixels and of samples
        (mean, max), the smallest
        range and how often it fell under the flat floor, and the effect on the result
        (mean, max, frame); and the near-flat synthetic frame's ranges.
    """
    high_passes = [
        temporal.white_balanced_high_pass(image, params, backend) for image in loaded.proxies
    ]
    defaults = [temporal.render(image, params, None, backend) for image in loaded.proxies]
    out: dict[str, Any] = {}
    for candidate in ROBUST_CANDIDATES:
        bounds = [temporal.robust_bounds(values, candidate) for values in high_passes]
        lows = np.array([b[0] for b in bounds])
        highs = np.array([b[1] for b in bounds])
        ranges = highs - lows
        clipped = np.array(
            [temporal.clipped_fraction(v, b) for v, b in zip(high_passes, bounds, strict=True)]
        )
        clipped_samples = np.array(
            [
                temporal.clipped_sample_fraction(v, b)
                for v, b in zip(high_passes, bounds, strict=True)
            ]
        )
        effect = np.array(
            [
                float(
                    np.abs(
                        temporal.render(image, params, Statistics(normalisation_bounds=b), backend)
                        - default
                    ).mean()
                )
                * 255.0
                for image, b, default in zip(loaded.proxies, bounds, defaults, strict=True)
            ]
        )
        out[candidate.name] = {
            "definition": dataclasses.asdict(candidate),
            "cv_low": float(np.std(lows) / abs(np.mean(lows))),
            "cv_high": float(np.std(highs) / abs(np.mean(highs))),
            "cv_range": float(np.std(ranges) / abs(np.mean(ranges))),
            "relative_step_low": _relative_step(lows),
            "relative_step_high": _relative_step(highs),
            "mean_low": float(np.mean(lows)),
            "mean_high": float(np.mean(highs)),
            "clipped_pixels_mean": float(clipped.mean()),
            "clipped_pixels_max": float(clipped.max()),
            "clipped_samples_mean": float(clipped_samples.mean()),
            "clipped_samples_max": float(clipped_samples.max()),
            "smallest_range": float(ranges.min()),
            "smallest_range_frame": int(np.argmin(ranges)),
            "floor_triggered_frames": int(np.count_nonzero(ranges < temporal.FLAT_FLOOR)),
            "effect_mean_levels": float(effect.mean()),
            "effect_max_levels": float(effect.max()),
            "effect_max_frame": int(np.argmax(effect)),
            "frames": [{"low": b[0], "high": b[1]} for b in bounds],
        }
    near_flat = temporal.white_balanced_high_pass(_near_flat_frame(), params, backend)
    flat_frame = np.full((540, 960, 3), NEAR_FLAT_RGB, dtype=np.float32)
    exactly_flat = temporal.white_balanced_high_pass(flat_frame, params, backend)
    synthetic: dict[str, Any] = {
        "near_flat": {
            "rgb": list(NEAR_FLAT_RGB),
            "noise_sd": NEAR_FLAT_NOISE,
            "seed": NEAR_FLAT_SEED,
            "size": [960, 540],
        },
        "candidates": {},
    }
    for candidate in ROBUST_CANDIDATES:
        low, high = temporal.robust_bounds(near_flat, candidate)
        flat_low, flat_high = temporal.robust_bounds(exactly_flat, candidate)
        synthetic["candidates"][candidate.name] = {
            "near_flat_range": high - low,
            "near_flat_floor_triggered": bool(high - low < temporal.FLAT_FLOOR),
            "flat_range": flat_high - flat_low,
            "flat_floor_triggered": bool(flat_high - flat_low < temporal.FLAT_FLOOR),
        }
    return {"candidates": out, "synthetic": synthetic}


def _long_smoothing_study(
    loaded: Loaded, backend: Backend, source_signals: NDArray[np.float64]
) -> dict[str, Any]:
    """Measure both methods' candidates with auditable, reach-specific interior records."""
    rate = loaded.frame_rate
    count = len(loaded.proxies)
    methods: dict[str, Any] = {}
    for name, params in METHODS.items():
        reference_statistics = temporal.constant_statistics(loaded.raw[name])
        reference = _signals(loaded.proxies, params, None, backend, reference_statistics)
        candidates: dict[str, Any] = {}
        for smoother in SMOOTHING_CANDIDATES:
            flat = temporal.analyse_flat(loaded.raw[name], smoother, rate)
            staged, _ = temporal.analyse_staged(
                list(loaded.proxies), params, smoother, rate, backend
            )
            candidate: dict[str, Any] = {
                "definition": _smoother_record(smoother, rate),
                "step": temporal.step_response(smoother, rate),
            }
            for analysis, series, reach in (
                ("flat", flat, smoother.radius(rate)),
                ("staged", staged, staged_reach(name, smoother, rate)),
            ):
                steps = max(count - 1 - 2 * reach, 0)
                interior = slice(reach, count - 1 - reach) if steps else None
                record = _sequence_record(
                    _signals(loaded.proxies, params, series, backend),
                    reference,
                    interior,
                    source_signals,
                    series=True,
                )
                record.update(
                    reach_frames=reach,
                    edge_free_frames=max(count - 2 * reach, 0),
                    edge_free_steps=steps,
                    interior_steps=None if interior is None else [interior.start, interior.stop],
                )
                candidate[analysis] = record
            candidates[smoother.label] = candidate
            print(
                f"{loaded.folder.name}: {name} smoothing {smoother.label}: "
                f"staged {candidate['staged']['edge_free_frames']} edge-free frames / "
                f"{candidate['staged']['edge_free_steps']} steps; "
                f"flat {candidate['flat']['edge_free_frames']} edge-free frames / "
                f"{candidate['flat']['edge_free_steps']} steps",
                file=sys.stderr,
            )
        methods[name] = candidates
    return methods


def run_experiments(
    folder: Path,
    roots: OutputRoots,
    backend: Backend,
    analyses: Mapping[str, Mapping[str, Series]],
    *,
    long: bool = False,
) -> dict[str, Any]:
    """Run the experiments on one excerpt's proxies and write ``results.json`` (``analyse``).

    The flicker measure (:func:`prototype.temporal.flicker`) is applied identically to every
    rendered sequence: its proxies rendered with the statistics under test, against the same
    proxies rendered with constant statistics (the mean of the raw series of the method), over
    all frame steps and over the interior steps (:func:`interior_margin`). With
    ``long=True``, a two-method window study replaces the Ancuti-only study,
    using each candidate's own staged or flat reach for its interior.

    Args:
        folder: The excerpt's folder.
        roots: The output safety roots.
        backend: Where the steps run.
        analyses: :func:`analyse_statistics`'s result for this excerpt.
        long: Run WP-DR25's two-method, reach-specific window study instead of WP1.4's.

    Returns:
        The ``results.json`` document.
    """
    loaded = load_excerpt(folder)
    entries = loaded.excerpt["frames"]
    rate = loaded.frame_rate
    count = len(loaded.proxies)
    interior = _interior(count, rate)
    source_signals = np.array([temporal.frame_signals(image) for image in loaded.proxies])
    document: dict[str, Any] = {
        "schema": RECORD_SCHEMA,
        "written": _now(),
        "excerpt": loaded.excerpt["excerpt"],
        "device": backend.name,
        "frames": count,
        "frame_rate": loaded.excerpt["frame_rate"],
        "interior_margin_frames": interior_margin(rate),
        "interior_steps": None if interior is None else [interior.start, interior.stop],
        "flicker_definition": FLICKER_DEFINITION,
        "comparison_smoother": _smoother_record(COMPARISON_SMOOTHER, rate),
        "mismatch_flat_minus_staged": {},
        "proxy_minus_full": {},
        "flicker": {},
        "smoothing": {},
        "robust": {},
    }
    for name, params in METHODS.items():
        staged = analyses["staged"][name]
        flat = analyses["flat"][name]
        document["mismatch_flat_minus_staged"][name] = _mismatch_record(flat, staged, entries)
        if name in loaded.raw_full:
            document["proxy_minus_full"][name] = _mismatch_record(
                loaded.raw[name], loaded.raw_full[name], entries
            )
        reference_statistics = temporal.constant_statistics(loaded.raw[name])
        reference = _signals(loaded.proxies, params, None, backend, reference_statistics)
        method_flicker: dict[str, Any] = {
            "reference": temporal.flatten(reference_statistics),
            "source_steps_mean_levels": float(np.abs(np.diff(source_signals, axis=0)).mean() * 255),
        }
        trend = temporal.linear_trend(loaded.raw[name])
        for label, series in (
            ("unsmoothed", None),
            ("staged", staged),
            ("flat", flat),
            ("linear_trend", trend),
        ):
            signals = _signals(loaded.proxies, params, series, backend)
            method_flicker[label] = _sequence_record(
                signals, reference, interior, source_signals, series=True
            )
        method_flicker["staged_vs_flat_render"] = _render_difference(
            loaded.proxies, params, staged, flat, backend
        )
        document["flicker"][name] = method_flicker
        print(f"{folder.name}: {name} staged/flat done", file=sys.stderr)
    if long:
        document["smoothing"] = _long_smoothing_study(loaded, backend, source_signals)
        params = METHODS[RENDER_METHOD]
    else:
        params = METHODS[RENDER_METHOD]
        reference_statistics = temporal.constant_statistics(loaded.raw[RENDER_METHOD])
        reference = _signals(loaded.proxies, params, None, backend, reference_statistics)
        for smoother in SMOOTHING_CANDIDATES:
            flat = temporal.analyse_flat(loaded.raw[RENDER_METHOD], smoother, rate)
            staged, _ = temporal.analyse_staged(
                list(loaded.proxies), params, smoother, rate, backend
            )
            document["smoothing"][smoother.label] = {
                "definition": _smoother_record(smoother, rate),
                "step": temporal.step_response(smoother, rate),
                "flat": _sequence_record(
                    _signals(loaded.proxies, params, flat, backend),
                    reference,
                    interior,
                    source_signals,
                ),
                "staged": _sequence_record(
                    _signals(loaded.proxies, params, staged, backend),
                    reference,
                    interior,
                    source_signals,
                ),
            }
            print(f"{folder.name}: smoothing {smoother.label} done", file=sys.stderr)
    document["robust"] = robust_study(loaded, params, backend)
    _write_json(roots, folder / "results.json", document)
    flicker_plot = {
        f"{label} (levels)": document["flicker"][RENDER_METHOD][label]["per_step"]
        for label in ("unsmoothed", "staged", "flat")
    }
    pts = [entry["pts_seconds"] for entry in entries[1:]]
    roots.write_bytes(folder / "flicker.png", plot_series(flicker_plot, pts))
    return document


# --- render ---------------------------------------------------------------------------------------


def _render_statistics(folder: Path, ticks: Sequence[int]) -> dict[str, list[Statistics]]:
    """Per version, the statistics each full-resolution frame is rendered with.

    Raises:
        ValueError: A record's ``pts_ticks`` are not ``ticks`` (the excerpt's), in order.
    """
    raw = _read_json(folder / "statistics-raw.json")
    staged = _read_json(folder / "statistics-staged.json")
    flat = _read_json(folder / "statistics-flat.json")
    sources = {
        "unsmoothed": raw["full"][RENDER_METHOD]["frames"],
        "staged": staged["methods"][RENDER_METHOD]["frames"],
        "flat": flat["methods"][RENDER_METHOD]["frames"],
    }
    for version, entries in sources.items():
        check_ticks(entries, ticks, f"the {version} record")
    return {
        version: [temporal.unflatten(entry["statistics"]) for entry in entries]
        for version, entries in sources.items()
    }


def compare_witness(witness: Path, ours: Path, chapter: str, count: int) -> dict[str, Any]:
    """Compare the kept unsmoothed frames with WP1.3's (the identity witness on real footage).

    Args:
        witness: WP1.3's ``flicker/corrected`` folder (``<chapter>_f<n>-ancuti2018.png``).
        ours: This run's ``renders/unsmoothed`` folder (``<chapter>_f<n>.png``).
        chapter: The chapter stem.
        count: The excerpt's number of frames (the kept ones are first, middle and last).

    Returns:
        Per kept frame number (as a string): ``file`` and either ``identical`` and ``max_abs``
        or ``missing: True``.
    """
    record: dict[str, Any] = {}
    for number in sorted(_keep(count)):
        theirs = witness / f"{chapter}_f{number:04d}-{RENDER_METHOD}.png"
        mine = ours / f"{chapter}_f{number:04d}.png"
        if theirs.is_file():
            difference = np.abs(read_png16(theirs) - read_png16(mine))
            record[str(number)] = {
                "file": theirs.name,
                "identical": bool(difference.max() == 0.0),
                "max_abs": float(difference.max()),
            }
        else:
            record[str(number)] = {"file": theirs.name, "missing": True}
    return record


def require_identical_witness(record: Mapping[str, Any], count: int, witness: Path) -> None:
    """Fail the render step unless every kept frame is present in the witness and identical.

    Called before anything is encoded or removed, so a failure leaves every frame in place.

    Args:
        record: :func:`compare_witness`'s result.
        count: The excerpt's number of frames.
        witness: The witness folder, for the message.

    Raises:
        PremiseError: A kept frame is missing from the witness or differs from it.
    """
    failed = [n for n in sorted(_keep(count)) if not record[str(n)].get("identical", False)]
    if failed:
        raise PremiseError(
            f"STOP: the unsmoothed render of frames {failed} is not identical to WP1.3's kept "
            f"frames in {witness} (missing or different: see the witness record); nothing was "
            "encoded and no frame was removed"
        )


def render_clips(
    spec: ExcerptSpec, footage: Path, roots: OutputRoots, backend: Backend, witness: Path
) -> dict[str, Any]:
    """Render, encode and verify the three full-resolution clips (phase ``render``).

    Every frame is corrected with the method pinned to ``ancuti2018`` (blue off; the WP1.4
    renders' method, not the ``Params()`` default, which is ``c3``) through the
    supplied-statistics hook three times: ``unsmoothed`` with its own full-frame statistics
    (identical to ``correct()`` without the hook, so to WP1.3's clip), ``staged`` and
    ``flat`` with the smoothed proxy statistics; and once more, unwritten, with constant
    statistics for the full-resolution flicker cross-check. Each set is encoded and verified
    by :func:`lookcheck.pack.encode_verified_pair` (NVENC, the source's colour tags and frame
    rate, every frame read back). Only when all three clips pass are the frame PNGs removed,
    but for the first, middle and last of each set.

    Args:
        spec: The excerpt (``GX011627``).
        footage: The footage folder (read only).
        roots: The output safety roots.
        backend: Where the pipeline runs.
        witness: WP1.3's ``flicker/corrected`` folder, whose kept frames the unsmoothed
            render must equal (a missing or different frame fails the step before any
            encode or removal). It is required: there is no way to skip the comparison.

    Returns:
        The ``render.json`` document.

    Raises:
        PremiseError: The witness is missing or not identical, or the excerpt has fewer than
            :data:`prototype.temporal.MIN_FRAMES` frames.
        ValueError: A statistics record's ``pts_ticks`` are not the excerpt's, in order.
        local_config.FootageLookupError: The chapter is not in the footage folder, or is in it
            more than once.
        lookcheck.frames.ExtractError: A probe, encode or check fails (the PNGs are kept).
    """
    folder = roots.allowed / spec.name
    document_in = _read_json(folder / "excerpt.json")
    entries = document_in["frames"]
    count = len(entries)
    ticks = [entry["pts_ticks"] for entry in entries]
    require_frames(spec.name, count)
    statistics = _render_statistics(folder, ticks)
    params = METHODS[RENDER_METHOD]
    raw = _read_json(folder / "statistics-raw.json")
    constant = temporal.constant_statistics(
        series_from_record(
            raw["full"][RENDER_METHOD]["frames"], ticks, "statistics-raw.json full constant"
        )
    )
    video = find_footage_file(spec.chapter, footage)
    info = probe_stream(video)
    signals: dict[str, list[NDArray[np.float64]]] = {v: [] for v in (*VERSIONS, "reference")}
    pairs = (("staged", "flat"), ("staged", "unsmoothed"), ("flat", "unsmoothed"))
    differences: dict[str, tuple[list[float], list[float]]] = {
        f"{a}_vs_{b}": ([], []) for a, b in pairs
    }
    began = time.monotonic()
    for number, entry in enumerate(entries):
        image = read_png16(folder / "frames" / entry["file"])
        outputs: dict[str, NDArray[np.float32]] = {}
        for version in VERSIONS:
            output = temporal.render(image, params, statistics[version][number], backend)
            outputs[version] = output
            _write_png(
                roots, folder / "renders" / version / f"{spec.chapter}_f{number:04d}.png", output
            )
            signals[version].append(temporal.frame_signals(output))
        signals["reference"].append(
            temporal.frame_signals(temporal.render(image, params, constant, backend))
        )
        for a, b in pairs:
            difference = np.abs(outputs[a].astype(np.float64) - outputs[b]) * 255.0
            differences[f"{a}_vs_{b}"][0].append(float(difference.mean()))
            differences[f"{a}_vs_{b}"][1].append(float(difference.max()))
        if number % 20 == 0:
            print(
                f"rendered {number + 1}/{count} ({time.monotonic() - began:.0f} s)", file=sys.stderr
            )
    witness_record: dict[str, Any] = {"folder": str(witness)}
    witness_record.update(
        compare_witness(witness, folder / "renders" / "unsmoothed", spec.chapter, count)
    )
    require_identical_witness(witness_record, count, witness)
    clips_dir = folder / "clips"
    commands: dict[str, list[str]] = {}
    checks: dict[str, Any] = {}
    for version in VERSIONS:
        clip_commands, clip_checks = encode_verified_pair(
            roots,
            {
                version: (
                    folder / "renders" / version / f"{spec.chapter}_f%04d.png",
                    clips_dir / f"{spec.chapter}_{version}.mp4",
                )
            },
            info,
            count,
            clips_dir,
        )
        commands.update(clip_commands)
        checks[version] = clip_checks
        print(f"encoded and verified {version}", file=sys.stderr)
    reference = np.array(signals["reference"])
    interior = _interior(count, Fraction(document_in["frame_rate"]))
    document: dict[str, Any] = {
        "schema": RECORD_SCHEMA,
        "written": _now(),
        "excerpt": spec.name,
        "device": backend.name,
        "params": dataclasses.asdict(params),
        "versions": {
            "unsmoothed": "each frame's own full-frame statistics (raw full), unsmoothed",
            "staged": "statistics-staged.json, ancuti2018 (proxy, smoothed)",
            "flat": "statistics-flat.json, ancuti2018 (proxy, smoothed)",
        },
        "encode_commands": commands,
        "checks": checks,
        "wp13_witness": witness_record,
        "full_resolution_differences": {
            label: _difference_summary(*values) for label, values in differences.items()
        },
        "full_resolution_flicker": {
            version: _flicker_record(np.array(signals[version]), reference, interior)
            for version in VERSIONS
        },
    }
    _write_json(roots, folder / "render.json", document)
    keep = _keep(count)
    for number, entry in enumerate(entries):
        if number in keep:
            continue
        roots.remove(folder / "frames" / entry["file"])
        for version in VERSIONS:
            roots.remove(folder / "renders" / version / f"{spec.chapter}_f{number:04d}.png")
    return document


# --- command line ---------------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    """Run one phase (module docstring).

    Args:
        argv: Command-line arguments; defaults to ``sys.argv[1:]``.

    Returns:
        0 on success; 2, with a one-line error on standard error, on a configuration, probe,
        device, path, FFmpeg or premise failure.
    """
    parser = argparse.ArgumentParser(description="Run the WP1.4 statistics experiments.")
    parser.add_argument("phase", choices=("extract", "analyse", "render"))
    parser.add_argument("--config", type=Path, help="local configuration file")
    parser.add_argument("--device", choices=DEVICES, default="gpu")
    parser.add_argument("--long", action="store_true", help="run WP-DR25's 20 s excerpt study")
    args = parser.parse_args(argv)
    if args.long and args.phase == "render":
        print(
            "error: --long supports extract and analyse only; render is disabled", file=sys.stderr
        )
        return 2
    excerpts = LONG_EXCERPTS if args.long else EXCERPTS
    try:
        config = load_local_config(args.config)
        roots = OutputRoots.from_config(config, subdir="wp-dr25" if args.long else WORK_SUBDIR)
        backend = select_backend(args.device)
        if backend.reason:
            print(f"note: running on the CPU: {backend.reason}", file=sys.stderr)
        if args.phase != "analyse":
            # Every chapter the phase reads is looked up before the first output write.
            for spec in excerpts:
                if args.phase == "extract" or spec.render:
                    find_footage_file(spec.chapter, config.footage_path)
        began = time.monotonic()
        for spec in excerpts:
            folder = roots.allowed / spec.name
            if args.phase == "extract":
                extract_excerpt(spec, config.footage_path, roots, backend)
            elif args.phase == "analyse":
                analyses = analyse_statistics(folder, roots, backend)
                if args.long:
                    run_experiments(folder, roots, backend, analyses, long=True)
                else:
                    run_experiments(folder, roots, backend, analyses)
            elif spec.render:
                witness = config.working_path / "wp1.3" / "flicker" / "corrected"
                render_clips(spec, config.footage_path, roots, backend, witness)
            print(folder)
        print(f"elapsed {time.monotonic() - began:.0f} s", file=sys.stderr)
    except (LocalConfigError, ExtractError, RuntimeError, OSError, ValueError, KeyError) as exc:
        print(f"error: {' '.join(str(exc).split()) or type(exc).__name__}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
