"""Build the WP1.3 look check pack: stills under three variants, the flicker clip, the deep part.

Usage::

    uv run python tools/lookcheck/pack.py stills [--config FILE] [--device gpu|cpu|auto]
    uv run python tools/lookcheck/pack.py flicker [--config FILE] [--device gpu|cpu|auto]
    uv run python tools/lookcheck/pack.py deep [--part all|clip|render|encode|stills]
        [--config FILE] [--device D]

All read the two folders from the local configuration. The footage folder is only ever an
input; every file written goes under ``<working folder>/wp1.3/`` (``stills`` and ``flicker``) or
``<working folder>/wp1.3d/`` (``deep``) and is checked first
(:class:`lookcheck.frames.OutputRoots`). A chapter is named by its stem and found anywhere
under the footage folder (:func:`local_config.find_footage_file`); a chapter that is missing
or ambiguous is a configuration error.

``stills`` extracts 6 frames from each of the four shallow chapters, at timestamps spaced
evenly from 5 % to 95 % of the duration, as 16-bit RGB PNG (:mod:`lookcheck.frames`), and
corrects each at the prototype's ``Params()`` defaults under three variants, on the device
chosen (default the graphics card; an unusable card is an error, never a silent fallback):

* ``ancuti2018``: Ancuti 2018 compensation, blue compensation off;
* ``ancuti2018-blue``: the same with blue compensation on (``--blue``);
* ``c3``: the 3C compensation.

It writes, in ``wp1.3/``: ``frames/`` (source PNGs and ``<frame>-<variant>.png``),
``thumbs/`` (short side 540 px), ``pairs/`` (source left, corrected right, short side
1080 px, JPEG quality 92), ``frames.json`` (exact pts and colour tags), ``statistics.json``
(what the prototype measured on each frame under each variant) and ``index.html``.

``flicker`` corrects every frame of a 6 s excerpt of chapter ``GX011627`` (starting at 30 %
of the duration) at the defaults with ``ancuti2018``, UNSMOOTHED (each frame its own
statistics), encodes the corrected frames and the untouched source frames to
``flicker/GX011627_unsmoothed.mp4`` and ``flicker/GX011627_source.mp4`` (HEVC NVENC 8-bit
4:2:0 with the source's colour tags and frame rate) under temporary names, checks both
(ffprobe, and every frame of each clip read back against its own PNG), renames them only
when both pass, writes ``flicker/statistics.json`` and a plot, and removes all frame PNGs
but the first, middle and last of each set.

Exit status 0 on success; 2, with a one-line ``error: ...`` on standard error, on a
configuration, probe, device, path or FFmpeg failure.

``deep`` (WP1.3D, spec v0.5.3) builds the deep half of the pack under ``<working folder>/wp1.3d/``
from the eight ``SCUBA/`` chapters and the scan's ``deep-frames.json`` (``lookcheck.scan``).
Its variants are ``c3`` (the default method of v0.5.3), ``ancuti2018`` and ``ancuti2018-blue``,
in that order, at the ``Params()`` defaults with only the method (and blue compensation) set.
``--part clip`` builds the deep clip in motion (:func:`render_deep_clip`, then
:func:`encode_deep_clip`; ``render`` and ``encode`` run one step each, the encode from the
rendered PNGs), ``--part stills`` the 48 chapter stills, the 12 case candidates at full
resolution and the page (:func:`build_deep_pack`); ``all`` (the default) does the clip first, so
that the page links it. The page links the clip only when its statistics record that it was
encoded, that every check held and that it is centred on the current deepest frame
(:func:`clip_files`); :func:`render_deep_clip` first deletes what an earlier clip left
(:func:`clear_clip`) and :func:`encode_deep_clip` refuses PNG sets that do not belong to the
statistics (:func:`clip_inputs_problem`).
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import datetime
import hashlib
import html
import io
import json
import statistics
import sys
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray
from PIL import Image as PILImage
from PIL import ImageDraw

if not __package__:
    # Script mode (``python tools/lookcheck/pack.py``): sys.path[0] is tools/lookcheck, so
    # put the tools directory first to make the ``lookcheck``, ``prototype`` and
    # ``local_config`` modules importable.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import itertools
import shutil

from local_config import LocalConfigError, find_footage_file, load_local_config
from lookcheck import scan
from lookcheck.frames import (
    ExtractError,
    FrameFile,
    OutputRoots,
    StreamInfo,
    StreamTags,
    colour_filter,
    excerpt,
    extract,
    probe_stream,
    read_png16,
    run_ffprobe,
    run_tool,
    scale_matrix,
    scale_range,
    to_uint8,
    tool_version,
)
from prototype import temporal
from prototype.backend import DEVICES, Backend, select_backend
from prototype.params import Params
from prototype.pipeline import Result, correct, normalisation_bounds
from prototype.run import write_png16
from prototype.temporal import Smoother

CHAPTERS = ("GX011625", "GX011626", "GX011627", "GX011628")
"""The four shallow chapters of the owner's footage (CP1, 2026-10-15)."""

STILL_FRACTIONS = tuple(0.05 + 0.9 * index / 5 for index in range(6))
"""Where the six stills of a chapter lie, as fractions of its duration (5 % to 95 %)."""

FLICKER_CHAPTER = "GX011627"
FLICKER_START_FRACTION = 0.30
FLICKER_SECONDS = 6.0
THUMB_SHORT_SIDE = 540
PAIR_SHORT_SIDE = 1080
JPEG_QUALITY = 92
NORMALISATION_COLLAPSE = 1e-6
"""N{} counts as collapsed below this spread; mirrors ``prototype.pipeline._EPS`` (a test
asserts the two are equal)."""

STATISTICS_SCHEMA = 1

PENDING_CASES: tuple[tuple[str, str], ...] = (
    ("Deeper footage (below the shallow range)", "not sorted by the owner yet (CP1 partial)"),
    (
        "Open blue water: gray-world on open water (spec 12)",
        "no dedicated open-water footage sorted yet (the water-dominant stills of GX011628 and "
        "the closing frames of the flicker clip are shallow-category frames, not this case)",
    ),
    ("Distance haze (spec 12)", "no distance-haze footage sorted yet"),
    ("Deep-water noise (spec 12)", "no deep footage sorted yet"),
    ("Photos (iPhone)", "none supplied for this part"),
    ("Chaptered recordings across a chapter boundary", "not in the shallow set"),
)
"""The look check cases this part cannot show; they are named, never approximated."""

_NVENC_SETTINGS = (
    "-c:v",
    "hevc_nvenc",
    "-preset",
    "p5",
    "-tune",
    "hq",
    "-rc",
    "vbr",
    "-cq",
    "20",
    "-b:v",
    "0",
    "-pix_fmt",
    "yuv420p",
    "-profile:v",
    "main",
)
# The read-back of every frame of an encoded clip against the PNG it was encoded from. Both
# sides are reduced by the same factor with the same FFmpeg scaler, so the comparison is on
# 1/8-size images; the differences are mean absolute differences in 8-bit levels.
READBACK_FACTOR = 8
READBACK_MAX_OWN = 3.0
"""Largest mean difference of a clip frame to its own PNG: a lossy encode differs a little."""
READBACK_MAX_CHANNEL_BIAS = 2.0
"""Largest mean signed difference of any one channel over the clip: a range or matrix error
shifts a channel by many levels."""
READBACK_METHOD = (
    "every frame of the encoded clip converted to 16-bit RGB at full size with the "
    "extraction's colour conversion (lookcheck.frames.colour_filter, the clip's own tags) and "
    "every PNG it was encoded from read through FFmpeg, both then reduced by 1/8 with the "
    "same scale filter (flags=accurate_rnd); per frame the mean absolute difference to its "
    "own PNG and to the PNG of the previous and the next frame, in 8-bit levels"
)


@dataclasses.dataclass(frozen=True)
class Variant:
    """One way of correcting a frame: its file label, its flags and its parameters.

    Attributes:
        name: Label used in file names (``<frame>-<name>.png``).
        flags: The same variant as prototype command-line flags, for the page and report.
        params: The full parameter set the correction runs with.
    """

    name: str
    flags: str
    params: Params


def default_variants(base: Params | None = None) -> tuple[Variant, ...]:
    """Return the three variants of the pack, all at the defaults of ``base``.

    Args:
        base: The parameter set the variants change; defaults to ``Params()``.

    Returns:
        ``ancuti2018`` (blue off), ``ancuti2018-blue`` and ``c3``, in that order.
    """
    start = Params() if base is None else base
    return (
        Variant(
            "ancuti2018",
            "--method ancuti2018",
            dataclasses.replace(start, method="ancuti2018", blue_compensation=False),
        ),
        Variant(
            "ancuti2018-blue",
            "--method ancuti2018 --blue",
            dataclasses.replace(start, method="ancuti2018", blue_compensation=True),
        ),
        Variant("c3", "--method c3", dataclasses.replace(start, method="c3")),
    )


def still_timestamps(duration_s: float) -> list[float]:
    """Return the six still timestamps of a clip: evenly from 5 % to 95 % of its duration.

    Args:
        duration_s: The clip duration in seconds.

    Returns:
        Six timestamps in seconds.
    """
    return [duration_s * fraction for fraction in STILL_FRACTIONS]


# --- statistics --------------------------------------------------------------------------------


def statistics_record(
    result: Result, backend: Backend, cap_tolerance: float = 0.0
) -> dict[str, Any]:
    """Record what the prototype measured and did on one frame under one variant.

    The compensation and white balance records are the prototype's own, unchanged
    (``dataclasses.asdict``); the parameters are the ones the pipeline ran with
    (``result.params``). The N{} bounds are not part of :class:`prototype.pipeline.Result`:
    they are recomputed with the prototype's :func:`prototype.pipeline.normalisation_bounds`
    on ``result.white_balanced``, the image that :func:`prototype.pipeline.fusion_inputs`
    measured them on, on the same device. ``bound`` says whether anything bound: a gain cap
    (the effective alpha below the requested one), the white-balance clamp, or an N{} that
    collapsed (a spread under 1e-6, which makes N{} a constant 0.5). A gain cap counts as
    binding when the effective alpha is below the requested one by more than ``cap_tolerance``.

    Args:
        result: The prototype's result for the frame.
        backend: The backend ``result`` was computed on.
        cap_tolerance: The alpha shortfall that still counts as "not bound". ``0.0`` (the
            default, the shallow pack's behaviour) is a strict comparison; the deep clip passes
            :data:`DEEP_CAP_TOLERANCE`, because a Gaussian-smoothed alpha of a constant 1.0 comes
            out as 0.9999999999999999 and would otherwise flag every frame.

    Returns:
        A JSON-ready dictionary.
    """
    compensation = dataclasses.asdict(result.compensation)
    balance = dataclasses.asdict(result.white_balance)
    low, high = normalisation_bounds(backend.to_device(result.white_balanced), result.params)
    requested, effective = compensation["requested"], compensation["effective"]
    cap_bound = {
        channel: bool(effective[channel] < requested[channel] - cap_tolerance)
        for channel in ("red", "blue")
        if channel in requested
    }
    collapsed = high - low < NORMALISATION_COLLAPSE
    clamp = [bool(flag) for flag in balance["clamped"]]
    return {
        "params": dataclasses.asdict(result.params),
        "backend": backend.name,
        "compensation": compensation,
        "white_balance": balance,
        "normalisation": {"low": low, "high": high, "collapsed": collapsed},
        "red_gain": balance["applied_gains"][0],
        "blue_gain": balance["applied_gains"][2],
        "bound": {
            "red_gain_cap": cap_bound.get("red", False),
            "blue_gain_cap": cap_bound.get("blue", False),
            "white_balance_clamp": clamp,
            "normalisation_collapsed": collapsed,
            "any": any(cap_bound.values()) or any(clamp) or collapsed,
        },
    }


def summary_line(record: Mapping[str, Any]) -> str:
    """Summarise a :func:`statistics_record` in one line: gains, alpha and what bound.

    Args:
        record: A statistics record.

    Returns:
        For example ``red gain 2.31, blue gain 1.02, alpha R 1.00; bound: none``.
    """
    effective = record["compensation"]["effective"]
    parts = [f"red gain {record['red_gain']:.2f}", f"blue gain {record['blue_gain']:.2f}"]
    if "red" in effective:
        alpha = f"alpha R {effective['red']:.2f}"
        if "blue" in effective:
            alpha += f" B {effective['blue']:.2f}"
        parts.append(alpha)
    bound = record["bound"]
    names = []
    if bound["red_gain_cap"]:
        names.append("red cap")
    if bound["blue_gain_cap"]:
        names.append("blue cap")
    names.extend(
        f"white-balance clamp {channel}"
        for channel, flag in zip("RGB", bound["white_balance_clamp"], strict=True)
        if flag
    )
    if bound["normalisation_collapsed"]:
        names.append("N{} collapsed")
    return ", ".join(parts) + "; bound: " + (", ".join(names) if names else "none")


def correct_variants(
    image: NDArray[np.float32], variants: Sequence[Variant], backend: Backend
) -> Iterator[tuple[Variant, NDArray[np.float32], dict[str, Any]]]:
    """Correct one frame under each variant, one at a time.

    Args:
        image: The source frame, float32 RGB in [0, 1].
        variants: The variants to run.
        backend: Where the pipeline runs.

    Yields:
        Each variant with its corrected image and its :func:`statistics_record`.
    """
    for variant in variants:
        result = correct(image, variant.params, backend)
        yield variant, result.output, statistics_record(result, backend)


# --- images and pages ---------------------------------------------------------------------------


def resized(image: NDArray[np.uint8], short_side: int) -> NDArray[np.uint8]:
    """Shrink an 8-bit RGB image so that its shorter side has ``short_side`` pixels.

    An image whose shorter side is already at most ``short_side`` is returned unchanged:
    nothing is enlarged (the frames of this pack are 2160 px high).

    Args:
        image: The image, shape ``(H, W, 3)``.
        short_side: The wanted shorter side in pixels.

    Returns:
        The resized image (Lanczos).
    """
    height, width = image.shape[:2]
    if min(height, width) <= short_side:
        return image
    scale = short_side / min(height, width)
    size = (max(1, round(width * scale)), max(1, round(height * scale)))
    return np.asarray(PILImage.fromarray(image).resize(size, PILImage.Resampling.LANCZOS))


def jpeg_bytes(image: NDArray[np.uint8]) -> bytes:
    """Encode an 8-bit RGB image as JPEG at the pack's quality (92).

    Args:
        image: The image.

    Returns:
        The JPEG file content.
    """
    buffer = io.BytesIO()
    PILImage.fromarray(image).save(buffer, format="JPEG", quality=JPEG_QUALITY)
    return buffer.getvalue()


def _write_png(roots: OutputRoots, path: Path, image: NDArray[np.float32]) -> None:
    """Write a 16-bit PNG with the prototype's writer, after checking the path."""
    roots.check(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_png16(path, image)


def _json_text(document: Mapping[str, Any]) -> str:
    """Serialise ``document`` as indented JSON; NaN and infinity are errors."""
    return json.dumps(document, indent=2, allow_nan=False) + "\n"


def _now() -> str:
    """The current UTC time to the second, ISO 8601."""
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


def build_pack(
    frames: Sequence[FrameFile],
    pack_dir: Path,
    roots: OutputRoots,
    backend: Backend,
    variants: Sequence[Variant] | None = None,
    render_page: Callable[[Sequence[FrameFile], Sequence[Variant], Mapping[str, Any], Path], str]
    | None = None,
) -> dict[str, Any]:
    """Correct the frames under each variant and write the pack around them.

    The source PNGs of ``frames`` must already be in ``pack_dir/frames`` (where
    :func:`lookcheck.frames.extract` put them). For each frame and variant the corrected
    16-bit PNG goes beside the source as ``<frame>-<variant>.png``, a thumbnail (short
    side 540) and a side-by-side JPEG (short side 1080 per half, source left) are written,
    and the statistics are collected. Then ``frames.json``, ``statistics.json`` and
    ``index.html`` are written.

    Args:
        frames: The extracted source frames, in the order the page lists them.
        pack_dir: The pack folder (``<working folder>/wp1.3``).
        roots: The output safety roots.
        backend: Where the pipeline runs.
        variants: The variants; defaults to :func:`default_variants`.
        render_page: Writes ``index.html`` from the frames, variants, statistics document and
            pack folder; ``None`` (the default) is :func:`render_index`, the shallow page.

    Returns:
        The statistics document that was written.

    Raises:
        lookcheck.frames.OutputPathError: An output path is refused.
        ValueError: A frame's PNG is not a 16-bit RGB PNG.
    """
    chosen = tuple(default_variants() if variants is None else variants)
    entries: list[dict[str, Any]] = []
    for number, frame in enumerate(frames, start=1):
        print(f"[{number}/{len(frames)}] {frame.path.name}", file=sys.stderr)
        image = read_png16(frame.path)
        source8 = to_uint8(image)
        roots.write_bytes(
            pack_dir / "thumbs" / f"{frame.path.stem}.jpg",
            jpeg_bytes(resized(source8, THUMB_SHORT_SIDE)),
        )
        source_pair = resized(source8, PAIR_SHORT_SIDE)
        per_variant: dict[str, Any] = {}
        for variant, output, record in correct_variants(image, chosen, backend):
            stem = f"{frame.path.stem}-{variant.name}"
            _write_png(roots, frame.path.with_name(f"{stem}.png"), output)
            corrected8 = to_uint8(output)
            roots.write_bytes(
                pack_dir / "thumbs" / f"{stem}.jpg",
                jpeg_bytes(resized(corrected8, THUMB_SHORT_SIDE)),
            )
            pair = np.hstack([source_pair, resized(corrected8, PAIR_SHORT_SIDE)])
            roots.write_bytes(pack_dir / "pairs" / f"{stem}.jpg", jpeg_bytes(pair))
            per_variant[variant.name] = record
        entries.append(
            {
                "frame": frame.path.stem,
                "chapter": frame.chapter,
                "pts_ticks": frame.pts_ticks,
                "pts_seconds": float(frame.pts),
                "variants": per_variant,
            }
        )
    document = {
        "schema": STATISTICS_SCHEMA,
        "written": _now(),
        "device": backend.name,
        "defaults": dataclasses.asdict(Params()),
        "variants": {
            variant.name: {"flags": variant.flags, "params": dataclasses.asdict(variant.params)}
            for variant in chosen
        },
        "frames": entries,
    }
    roots.write_text(pack_dir / "statistics.json", _json_text(document))
    frames_document = {
        "schema": STATISTICS_SCHEMA,
        "written": _now(),
        "ffmpeg": tool_version("ffmpeg"),
        "frames": [frame.record() for frame in frames],
    }
    roots.write_text(pack_dir / "frames.json", _json_text(frames_document))
    page = render_index if render_page is None else render_page
    roots.write_text(pack_dir / "index.html", page(frames, chosen, document, pack_dir))
    return document


_STYLE = (
    "body{font-family:sans-serif;margin:1.5em;background:#fafafa;color:#111}"
    "table{border-collapse:collapse;margin:0.5em 0}"
    "td,th{border:1px solid #ccc;padding:4px;vertical-align:top;font-size:13px}"
    "img{display:block;max-width:100%;height:auto}"
    ".grid td{width:25%}.grid img{width:100%}"
    ".cap{font-size:11px;color:#333;margin-top:3px}"
    "h2{margin-top:1.5em}"
)


def render_index(
    frames: Sequence[FrameFile],
    variants: Sequence[Variant],
    statistics_document: Mapping[str, Any],
    pack_dir: Path,
) -> str:
    """Render ``index.html``: one static page, relative links only, no external resource.

    The head lists the variants, the defaults used (every ``Params`` field) and the pending
    cases. Then, per chapter, one row per frame: the source thumbnail and the variants'
    thumbnails, each linking to its full-size PNG, with the pts, a link to each
    side-by-side JPEG and the one-line statistics under each variant.

    Args:
        frames: The frames in page order.
        variants: The variants shown.
        statistics_document: The document returned by :func:`build_pack`.
        pack_dir: The pack folder (links are relative to it).

    Returns:
        The page.
    """
    by_frame = {entry["frame"]: entry for entry in statistics_document["frames"]}

    def link(path: Path) -> str:
        return html.escape(path.relative_to(pack_dir).as_posix(), quote=True)

    out: list[str] = [
        "<!DOCTYPE html>",
        '<html lang="en"><head><meta charset="utf-8">',
        "<title>Clearwater WP1.3 look check pack (shallow part)</title>",
        f"<style>{_STYLE}</style></head><body>",
        "<h1>Clearwater look check pack: shallow footage (WP1.3)</h1>",
        f"<p>Device: {html.escape(str(statistics_document['device']))}. Written "
        f"{html.escape(str(statistics_document['written']))}. Full-size 16-bit PNGs are behind "
        "every thumbnail; the pair links are side-by-side JPEGs (source left, corrected "
        'right). Raw numbers: <a href="statistics.json">statistics.json</a>, '
        '<a href="frames.json">frames.json</a> (exact pts and colour tags).</p>',
        "<h2>Variants</h2><table><tr><th>Name</th><th>Prototype flags</th></tr>",
    ]
    out.extend(
        f"<tr><td>{html.escape(v.name)}</td><td>{html.escape(v.flags)}</td></tr>" for v in variants
    )
    out.append("</table><h2>Defaults used (Params)</h2><table>")
    defaults = statistics_document["defaults"]
    out.extend(
        f"<tr><td>{html.escape(name)}</td><td>{html.escape(str(value))}</td></tr>"
        for name, value in defaults.items()
    )
    out.append("</table><h2>Pending cases (not in this part)</h2><ul>")
    out.extend(
        f"<li>PENDING: {html.escape(name)} - {html.escape(why)}</li>" for name, why in PENDING_CASES
    )
    out.append("</ul>")
    current = ""
    for frame in frames:
        if frame.chapter != current:
            if current:
                out.append("</table>")
            current = frame.chapter
            out.append(f"<h2>{html.escape(current)}</h2>")
            out.append('<table class="grid"><tr><th>Source</th>')
            out.extend(f"<th>{html.escape(v.name)}</th>" for v in variants)
            out.append("</tr>")
        source_png = frame.path
        thumb = pack_dir / "thumbs" / f"{frame.path.stem}.jpg"
        cells = [
            f'<td><a href="{link(source_png)}"><img src="{link(thumb)}" '
            f'alt="{html.escape(frame.path.stem)}"></a>'
            f'<div class="cap">{html.escape(frame.chapter)} at {float(frame.pts):.3f} s '
            f"(pts {frame.pts_ticks} / {frame.time_base.denominator})</div></td>"
        ]
        for variant in variants:
            stem = f"{frame.path.stem}-{variant.name}"
            png = frame.path.with_name(f"{stem}.png")
            record = by_frame[frame.path.stem]["variants"][variant.name]
            cells.append(
                f'<td><a href="{link(png)}"><img src="{link(pack_dir / "thumbs" / f"{stem}.jpg")}"'
                f' alt="{html.escape(stem)}"></a><div class="cap">'
                f'<a href="{link(pack_dir / "pairs" / f"{stem}.jpg")}">pair</a> '
                f"{html.escape(summary_line(record))}</div></td>"
            )
        out.append("<tr>" + "".join(cells) + "</tr>")
    if current:
        out.append("</table>")
    out.append("</body></html>")
    return "\n".join(out) + "\n"


# --- the flicker clip -----------------------------------------------------------------------------


def _properties_filter(tags: StreamTags) -> str:
    """The ``setparams`` filter that puts the source's colour description on every frame.

    FFmpeg's encoder takes the colour description from the frames, and the ``scale`` filter
    sets only matrix and range, so without this the encoded stream would lose the primaries
    and the transfer characteristic (a tag that is ``unknown`` is left out).

    Args:
        tags: The source stream's tags.

    Returns:
        The filter text.
    """
    parts = [f"range={tags.color_range}", f"colorspace={tags.color_space}"]
    if tags.color_primaries != "unknown":
        parts.append(f"color_primaries={tags.color_primaries}")
    if tags.color_transfer != "unknown":
        parts.append(f"color_trc={tags.color_transfer}")
    return "setparams=" + ":".join(parts)


def encode_command(
    pattern: Path, output: Path, tags: StreamTags, frame_rate: Fraction
) -> list[str]:
    """Build the FFmpeg command that encodes a numbered PNG sequence with NVENC.

    The 16-bit RGB frames are converted with the source's matrix and range (the same
    ``scale`` arguments :func:`lookcheck.frames.colour_filter` reads the source with) to
    8-bit 4:2:0 and encoded as HEVC with the settings WP1.5 used (``p5``, ``hq``, constant
    quality 20), tagged with the source's colour tags (range, matrix, primaries, transfer:
    on the frames by ``setparams`` and by the encoder options) and frame rate; no audio.

    Args:
        pattern: The input path with a ``%04d`` counter, counting from 0.
        output: The MP4 to write.
        tags: The source stream's tags.
        frame_rate: The source frame rate in frames per second.

    Returns:
        The command and its arguments.
    """
    command = [
        "ffmpeg",
        "-nostdin",
        "-hide_banner",
        "-nostats",
        "-y",
        "-framerate",
        f"{frame_rate.numerator}/{frame_rate.denominator}",
        "-start_number",
        "0",
        "-i",
        str(pattern),
        "-vf",
        f"scale=out_color_matrix={scale_matrix(tags)}:out_range={scale_range(tags)},"
        f"format=yuv420p,{_properties_filter(tags)}",
        *_NVENC_SETTINGS,
    ]
    for option, value in (
        ("-color_primaries", tags.color_primaries),
        ("-color_trc", tags.color_transfer),
        ("-colorspace", tags.color_space),
        ("-color_range", tags.color_range),
    ):
        if value != "unknown":
            command += [option, value]
    command += ["-tag:v", "hvc1", "-fps_mode", "passthrough", "-enc_time_base:v", "demux"]
    return [*command, "-an", str(output)]


def verify_clip(
    video: Path, count: int, tags: StreamTags, frame_rate: Fraction, size: tuple[int, int]
) -> dict[str, Any]:
    """Check a re-assembled clip with ``ffprobe``: format, size, timing, tags, no audio.

    The clip must be one HEVC Main 8-bit 4:2:0 video stream (``yuv420p``, or ``yuvj420p``
    which is how FFmpeg reports a full-range one) of ``size`` holding ``count`` frames with
    first pts 0 and every pts step, taken in the order ``ffprobe`` lists the frames (not
    sorted), one frame period, carrying the colour range, matrix, primaries and transfer of
    ``tags`` (a tag that is ``unknown`` is not compared), and no audio stream.

    Args:
        video: The MP4.
        count: The number of frames it must hold.
        tags: The colour tags it must carry.
        frame_rate: The frame rate whose period every pts step must equal.
        size: The ``(width, height)`` it must have.

    Returns:
        A record of what was read, with ``ok`` true when every check holds.
    """
    document = run_ffprobe(["-show_streams", str(video)])
    streams = document.get("streams", [])
    video_streams = [s for s in streams if s.get("codec_type") == "video"]
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
    stream = video_streams[0] if video_streams else {}
    time_base = Fraction(stream.get("time_base", "1/1"))
    listing = run_ffprobe(
        [
            "-select_streams",
            "v:0",
            "-show_frames",
            "-show_entries",
            "frame=pts",
            str(video),
        ]
    )
    pts = [int(frame["pts"]) for frame in listing.get("frames", [])]
    steps = {b - a for a, b in itertools.pairwise(pts)}
    period = 1 / frame_rate / time_base
    record: dict[str, Any] = {
        "file": video.name,
        "codec": stream.get("codec_name"),
        "pix_fmt": stream.get("pix_fmt"),
        "color_range": stream.get("color_range"),
        "color_space": stream.get("color_space"),
        "color_primaries": stream.get("color_primaries"),
        "color_transfer": stream.get("color_transfer"),
        "profile": stream.get("profile"),
        "size": [stream.get("width"), stream.get("height")],
        "frames": len(pts),
        "first_pts": pts[0] if pts else None,
        "pts_steps": sorted(steps),
        "time_base": str(time_base),
        "audio_streams": len(audio_streams),
    }
    record["ok"] = bool(
        len(video_streams) == 1
        and stream.get("codec_name") == "hevc"
        and stream.get("profile") == "Main"
        and stream.get("pix_fmt") in ("yuv420p", "yuvj420p")
        and (stream.get("width"), stream.get("height")) == size
        and all(
            tag == "unknown" or stream.get(key) == tag
            for key, tag in (
                ("color_primaries", tags.color_primaries),
                ("color_transfer", tags.color_transfer),
            )
        )
        and len(pts) == count
        and pts[0] == 0
        and steps == {period}
        and stream.get("color_range") == tags.color_range
        and stream.get("color_space") == tags.color_space
        and not audio_streams
    )
    return record


def encode_clip(
    roots: OutputRoots,
    pattern: Path,
    output: Path,
    info: StreamInfo,
    count: int,
    flicker_dir: Path,
) -> tuple[list[str], dict[str, Any]]:
    """Encode one numbered PNG sequence to an MP4 and verify it; a bad clip is deleted.

    Runs :func:`encode_command` on a checked output path and then :func:`verify_clip`. If
    FFmpeg fails, or the clip fails its check, the output file is removed again (so that no
    partial or unverified clip is left under its final name) and an error is raised; the
    frame PNGs are never touched here.

    Args:
        roots: The output safety roots.
        pattern: The numbered input PNG path.
        output: The MP4 to write.
        info: The source stream (frame rate, size and tags the clip must carry).
        count: The number of frames the clip must hold.
        flicker_dir: The folder of ``output`` (created if absent).

    Returns:
        The FFmpeg command and the :func:`verify_clip` record (``ok`` true).

    Raises:
        lookcheck.frames.ExtractError: FFmpeg fails or the clip fails its check.
    """
    roots.check(output)
    roots.mkdir(flicker_dir)
    command = encode_command(pattern, output, info.tags, info.frame_rate)
    done = run_tool(command)
    if done.returncode != 0:
        roots.remove(output)
        tail = done.stderr.decode("utf-8", errors="replace").strip().splitlines()[-1:]
        raise ExtractError(f"ffmpeg failed encoding {output.name}: {tail}")
    record = verify_clip(output, count, info.tags, info.frame_rate, (info.width, info.height))
    if not record["ok"]:
        roots.remove(output)
        raise ExtractError(f"encode check failed for {output.name}: {record}")
    return command, record


def series_summary(values: Sequence[float]) -> dict[str, float]:
    """Summarise a statistic over the frames of a clip.

    Args:
        values: One value per frame, in order.

    Returns:
        ``min``, ``max``, ``mean``, ``stdev`` (population) and ``max_step``, the largest
        absolute change between consecutive frames.
    """
    steps = [abs(b - a) for a, b in itertools.pairwise(values)]
    return {
        "min": min(values),
        "max": max(values),
        "mean": statistics.fmean(values),
        "stdev": statistics.pstdev(values),
        "max_step": max(steps) if steps else 0.0,
    }


def plot_series(series: Mapping[str, Sequence[float]], pts: Sequence[float]) -> bytes:
    """Plot the flicker statistics against pts as one PNG, one small panel per statistic.

    Args:
        series: Statistic name to one value per frame.
        pts: The frames' pts in seconds.

    Returns:
        The PNG file content.
    """
    width, panel, margin = 1000, 170, 60
    image = PILImage.new("RGB", (width, panel * len(series) + 20), "white")
    draw = ImageDraw.Draw(image)
    x_low, x_high = min(pts), max(pts)
    for row, (name, values) in enumerate(series.items()):
        top = 10 + row * panel
        low, high = min(values), max(values)
        spread = high - low if high > low else 1.0
        draw.rectangle([margin, top, width - 20, top + panel - 30], outline="gray")
        draw.text((5, top), name, fill="black")
        draw.text((5, top + 20), f"max {high:.4g}", fill="black")
        draw.text((5, top + panel - 55), f"min {low:.4g}", fill="black")
        points = [
            (
                margin + (t - x_low) / (x_high - x_low or 1.0) * (width - 20 - margin),
                top + (panel - 30) * (1 - (v - low) / spread),
            )
            for t, v in zip(pts, values, strict=True)
        ]
        if len(points) > 1:
            draw.line(points, fill="navy", width=2)
    draw.text(
        (margin, panel * len(series) + 5), f"pts {x_low:.3f} s to {x_high:.3f} s", fill="black"
    )
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def run_flicker(
    video: Path, roots: OutputRoots, backend: Backend, flicker_dir: Path
) -> dict[str, Any]:
    """Build the flicker clip: unsmoothed frame-by-frame correction of a 6 s excerpt.

    Extracts every frame of the excerpt (``excerpt`` from 30 % of the duration, 6 s) as a
    numbered sequence, corrects each at the ``Params()`` defaults with ``ancuti2018``
    (blue off, its own statistics, no smoothing), encodes the corrected frames and the
    source frames to two MP4s (:func:`encode_command`) under temporary names, checks both
    (:func:`verify_clip` and the read-back of EVERY frame of both clips against its own
    PNG, :func:`readback_clip`), and only when both pass gives them their names
    (:func:`encode_verified_pair`). Then it writes ``statistics.json`` and
    ``statistics.png`` and deletes all frame PNGs except the first, middle and last of each
    set; no PNG is deleted before every check has held.

    Args:
        video: The source chapter.
        roots: The output safety roots.
        backend: Where the pipeline runs.
        flicker_dir: The output folder (``<working folder>/wp1.3/flicker``).

    Returns:
        The statistics document that was written.

    Raises:
        lookcheck.frames.ExtractError: A probe, decode or encode fails or a check does not
            hold (the frame PNGs are then kept and no clip exists under its final name).
    """
    info = probe_stream(video)
    tags = info.tags
    variant = default_variants()[0]
    start = FLICKER_START_FRACTION * info.duration_s
    source_dir, corrected_dir = flicker_dir / "source", flicker_dir / "corrected"
    began = time.monotonic()
    frames = excerpt(video, start, FLICKER_SECONDS, source_dir, roots=roots, naming="index")
    print(f"extracted {len(frames)} frames in {time.monotonic() - began:.0f} s", file=sys.stderr)
    entries: list[dict[str, Any]] = []
    corrected_paths: list[Path] = []
    for number, frame in enumerate(frames):
        image = read_png16(frame.path)
        result = correct(image, variant.params, backend)
        target = corrected_dir / f"{frame.path.stem}-{variant.name}.png"
        _write_png(roots, target, result.output)
        corrected_paths.append(target)
        entries.append(
            {
                "index": number,
                "pts_ticks": frame.pts_ticks,
                "pts_seconds": float(frame.pts),
                "source_file": frame.path.name,
                "corrected_file": target.name,
                "statistics": statistics_record(result, backend),
            }
        )
        if number % 20 == 0:
            print(f"corrected {number + 1}/{len(frames)}", file=sys.stderr)
    stem = video.stem
    clips = {
        "unsmoothed": (
            corrected_dir / f"{stem}_f%04d-{variant.name}.png",
            flicker_dir / f"{stem}_unsmoothed.mp4",
        ),
        "source": (source_dir / f"{stem}_f%04d.png", flicker_dir / f"{stem}_source.mp4"),
    }
    commands, checks = encode_verified_pair(roots, clips, info, len(frames), flicker_dir)
    series = {
        "red gain (white balance)": [e["statistics"]["red_gain"] for e in entries],
        "blue gain (white balance)": [e["statistics"]["blue_gain"] for e in entries],
        "effective alpha (red)": [
            e["statistics"]["compensation"]["effective"]["red"] for e in entries
        ],
        "N{} low bound": [e["statistics"]["normalisation"]["low"] for e in entries],
        "N{} high bound": [e["statistics"]["normalisation"]["high"] for e in entries],
    }
    document = {
        "schema": STATISTICS_SCHEMA,
        "written": _now(),
        "source": str(video),
        "variant": {"name": variant.name, "params": dataclasses.asdict(variant.params)},
        "smoothing": "none (every frame its own statistics)",
        "device": backend.name,
        "excerpt": {
            "start_s": start,
            "duration_s": FLICKER_SECONDS,
            "frames": len(frames),
            "first_pts_ticks": frames[0].pts_ticks,
            "last_pts_ticks": frames[-1].pts_ticks,
            "time_base": f"{info.time_base.numerator}/{info.time_base.denominator}",
            "first_pts_seconds": float(frames[0].pts),
            "last_pts_seconds": float(frames[-1].pts),
        },
        "tags": tags.record(),
        "ffmpeg": tool_version("ffmpeg"),
        "extract_command": list(frames[0].command),
        "encode_commands": commands,
        "checks": checks,
        "summary": {name: series_summary(values) for name, values in series.items()},
        "bound_counts": {
            "red_gain_cap": sum(e["statistics"]["bound"]["red_gain_cap"] for e in entries),
            "white_balance_clamp_any": sum(
                any(e["statistics"]["bound"]["white_balance_clamp"]) for e in entries
            ),
            "normalisation_collapsed": sum(
                e["statistics"]["bound"]["normalisation_collapsed"] for e in entries
            ),
        },
        "frames": entries,
    }
    roots.write_text(flicker_dir / "statistics.json", _json_text(document))
    plot = plot_series(series, [e["pts_seconds"] for e in entries])
    roots.write_bytes(flicker_dir / "statistics.png", plot)
    keep = {0, len(frames) // 2, len(frames) - 1}
    for number, frame in enumerate(frames):
        if number not in keep:
            roots.remove(frame.path)
            roots.remove(corrected_paths[number])
    return document


def partial_name(output: Path) -> Path:
    """Return the temporary name a clip is written under until both clips are verified.

    Args:
        output: The final clip name (``GX011627_source.mp4``).

    Returns:
        The same folder, ``GX011627_source.partial.mp4`` (FFmpeg picks the MP4 muxer from the
        extension).
    """
    return output.with_name(f"{output.stem}.partial{output.suffix}")


def discard(roots: OutputRoots, paths: Sequence[Path], failure: BaseException) -> None:
    """Remove every one of ``paths``, whatever happens to the others; never mask ``failure``.

    A removal that raises (a locked file, a refused path) does not stop the loop: the other
    names are still visited, and the problem is attached to ``failure`` as a note.

    Args:
        roots: The output safety roots.
        paths: The files to remove (a missing file is not an error).
        failure: The exception being handled; it is not raised or changed except for notes.
    """
    for path in paths:
        try:
            roots.remove(path)
        except Exception as problem:  # cleanup is best effort by design
            failure.add_note(f"could not remove {path}: {problem}")


def encode_verified_pair(
    roots: OutputRoots,
    clips: Mapping[str, tuple[Path, Path]],
    info: StreamInfo,
    count: int,
    flicker_dir: Path,
    max_own: float = READBACK_MAX_OWN,
) -> tuple[dict[str, list[str]], dict[str, Any]]:
    """Encode the clips under temporary names, verify every one, then give them their names.

    No clip exists under its final name unless every clip passed :func:`verify_clip` and
    the full read-back (:func:`readback_clip`). A clip of an earlier run is removed first,
    so a failed run leaves none. Each clip is written under :func:`partial_name`; on ANY
    exception (an FFmpeg failure, a probe that raises, a failed check, a failed rename) every
    temporary and final name is removed again (:func:`discard`, best effort: one removal that
    fails does not stop the others or replace the exception) and the exception propagates.
    Only when everything passed are the clips renamed. The frame PNGs are never touched here.

    Args:
        roots: The output safety roots.
        clips: Label to ``(numbered PNG input path, final MP4 path)``.
        info: The source stream (frame rate, size and tags the clips must carry).
        count: The number of frames each clip must hold.
        flicker_dir: The folder of the clips.
        max_own: The read-back bound on a clip frame's difference to its own PNG
            (:func:`readback_clip`; :data:`READBACK_MAX_OWN` by default).

    Returns:
        The FFmpeg command per label (with the final clip name as its output) and the
        checks: per label the :func:`verify_clip` record, and ``readback`` with one
        :func:`readback_clip` record per label and ``ok``.

    Raises:
        lookcheck.frames.ExtractError: An encode, probe or check fails; the message names
            the failing check (and, for the read-back, the failing frames).
    """
    finals = {label: output for label, (_pattern, output) in clips.items()}
    partials = {label: partial_name(output) for label, output in finals.items()}
    commands: dict[str, list[str]] = {}
    checks: dict[str, Any] = {}
    try:
        for output in (*finals.values(), *partials.values()):
            roots.remove(output)
        for label, (pattern, _output) in clips.items():
            commands[label], checks[label] = encode_clip(
                roots, pattern, partials[label], info, count, flicker_dir
            )
            checks[label]["file"] = finals[label].name
        readback: dict[str, Any] = {
            label: readback_clip(
                partials[label], clips[label][0], count, info, flicker_dir, roots, max_own
            )
            for label in clips
        }
        readback["ok"] = all(record["ok"] for record in readback.values())
        checks["readback"] = readback
        if not readback["ok"]:
            failing = {
                label: record["failed_frames"] or record["problems"]
                for label, record in readback.items()
                if label != "ok" and not record["ok"]
            }
            raise ExtractError(f"read-back check failed; no clip kept, frames kept: {failing}")
        for label, command in commands.items():
            command[-1] = str(finals[label])
        for label in clips:
            roots.rename(partials[label], finals[label])
    except BaseException as failure:
        discard(roots, [*finals.values(), *partials.values()], failure)
        raise
    return commands, checks


def reduced_command(pattern: Path, count: int, size: tuple[int, int], output: Path) -> list[str]:
    """Build the FFmpeg command that reduces a numbered PNG sequence to 16-bit RGB PNGs.

    It uses the same ``scale`` flags as :func:`lookcheck.frames.colour_filter`, so the
    reference frames of the read-back are reduced the way the clip's frames are.

    Args:
        pattern: The input path with a ``%04d`` counter, counting from 0.
        count: The number of frames to read.
        size: The output ``(width, height)``.
        output: The output path with a ``%06d`` counter.

    Returns:
        The command and its arguments.
    """
    return [
        "ffmpeg",
        "-nostdin",
        "-hide_banner",
        "-nostats",
        "-y",
        "-start_number",
        "0",
        "-i",
        str(pattern),
        "-vf",
        f"scale=w={size[0]}:h={size[1]}:flags=accurate_rnd,format=rgb48be",
        "-frames:v",
        str(count),
        "-fps_mode",
        "passthrough",
        "-pred",
        "none",
        str(output),
    ]


def reduced_clip_command(
    clip: Path, tags: StreamTags, count: int, size: tuple[int, int], output: Path
) -> list[str]:
    """Build the FFmpeg command that reduces the frames of an encoded clip to 16-bit RGB PNGs.

    The YUV frames are first converted to RGB at full size with the extraction's own filter
    (:func:`lookcheck.frames.colour_filter`) and only then reduced, with the flags
    :func:`reduced_command` uses. (One ``scale`` that converts and resizes in a single step
    is less accurate: it measured about 4 levels of error on saturated test frames, against
    0.1 for this chain.) ``count`` frames are asked for; the caller asks for one more than
    it expects so that a surplus frame shows.

    Args:
        clip: The encoded MP4.
        tags: The clip's own tags.
        count: The number of frames to write at most.
        size: The output ``(width, height)``.
        output: The output path with a ``%06d`` counter.

    Returns:
        The command and its arguments.
    """
    return [
        "ffmpeg",
        "-nostdin",
        "-hide_banner",
        "-nostats",
        "-y",
        "-i",
        str(clip),
        "-map",
        "0:v:0",
        "-an",
        "-sn",
        "-dn",
        "-vf",
        f"{colour_filter(tags)},scale=w={size[0]}:h={size[1]}:flags=accurate_rnd,format=rgb48be",
        "-frames:v",
        str(count),
        "-fps_mode",
        "passthrough",
        "-pred",
        "none",
        str(output),
    ]


def _mean_abs(a: NDArray[np.float32], b: NDArray[np.float32]) -> float:
    """The mean absolute difference of two float images in [0, 1], in 8-bit levels."""
    return float(np.abs(a - b).mean(dtype=np.float64) * 255.0)


def readback_clip(
    clip: Path,
    pattern: Path,
    count: int,
    info: StreamInfo,
    flicker_dir: Path,
    roots: OutputRoots,
    max_own: float = READBACK_MAX_OWN,
) -> dict[str, Any]:
    """Read back EVERY frame of an encoded clip and match each to the PNG it came from.

    The clip is converted with the extraction's colour conversion (its own tags) and the PNG
    sequence ``pattern`` is read through FFmpeg, both reduced to 1/8 size
    (:data:`READBACK_METHOD`). Frame ``i`` passes when its mean
    absolute difference to its own PNG (``own``) is at most ``max_own`` AND is
    smaller than its difference to the PNG of frame ``i - 1`` (``previous``) and of frame
    ``i + 1`` (``next``): an encode that repeats, drops or swaps a frame fails by name.
    ``margin`` is the smaller neighbour difference minus ``own``. The clip as a whole
    also fails when its frame count differs, its range or matrix tag differs from ``info``,
    or any one channel's mean signed difference exceeds :data:`READBACK_MAX_CHANNEL_BIAS`
    (a range or matrix error).

    Args:
        clip: The encoded MP4.
        pattern: The numbered PNG input it was encoded from (``%04d``, from 0).
        count: The number of frames it must hold.
        info: The source stream (size and tags).
        flicker_dir: Folder for the temporary decoded frames (cleared first, removed again).
        roots: The output safety roots.
        max_own: The bound on ``own`` in 8-bit levels (:data:`READBACK_MAX_OWN` by default).

    Returns:
        The record: ``frames`` (per frame, in presentation order: ``index``, ``own``,
        ``previous``, ``next``, ``margin``, ``bias`` per channel R, G, B, ``ok``),
        ``failed_frames`` (index and reason), ``worst_own``, ``smallest_margin`` with its
        frame, ``channel_bias``, ``problems`` (whole-clip failures), the thresholds, the
        method and ``ok``.

    Raises:
        lookcheck.frames.ExtractError: The size is not a multiple of the factor, or an
            FFmpeg run fails.
    """
    factor = READBACK_FACTOR
    if info.width % factor or info.height % factor:
        raise ExtractError(f"{info.width}x{info.height} is not a multiple of {factor}")
    size = (info.width // factor, info.height // factor)
    scratch = flicker_dir / "readback" / clip.stem
    shutil.rmtree(roots.check(scratch), ignore_errors=True)  # nothing of an earlier run
    if scratch.exists():
        raise ExtractError(f"cannot clear the read-back folder {scratch}")
    roots.mkdir(scratch)
    try:
        clip_tags = probe_stream(clip).tags
        decoded_dir = roots.mkdir(scratch / "clip")
        for index in range(1, count + 2):
            roots.check(decoded_dir / f"c{index:06d}.png")
        done = run_tool(
            reduced_clip_command(clip, clip_tags, count + 1, size, decoded_dir / "c%06d.png")
        )
        if done.returncode != 0:
            tail = done.stderr.decode("utf-8", errors="replace").strip().splitlines()[-1:]
            raise ExtractError(f"ffmpeg failed reading back {clip.name}: {tail}")
        decoded = sorted(decoded_dir.glob("c*.png"))
        reference_dir = roots.mkdir(scratch / "reference")
        for index in range(1, count + 1):
            roots.check(reference_dir / f"r{index:06d}.png")
        done = run_tool(reduced_command(pattern, count, size, reference_dir / "r%06d.png"))
        if done.returncode != 0:
            tail = done.stderr.decode("utf-8", errors="replace").strip().splitlines()[-1:]
            raise ExtractError(f"ffmpeg failed reducing the frames of {clip.name}: {tail}")
        problems: list[str] = []
        if len(decoded) != count:
            problems.append(f"the clip holds {len(decoded)} frames, expected {count}")
        for name, got, wanted in (
            ("color_range", clip_tags.color_range, info.tags.color_range),
            ("color_space", clip_tags.color_space, info.tags.color_space),
        ):
            if got != wanted:
                problems.append(f"{name} is {got}, expected {wanted}")
        records: list[dict[str, Any]] = []
        failed: list[dict[str, Any]] = []
        bias_sum = np.zeros(3)
        if len(decoded) == count:
            references = [
                read_png16(reference_dir / f"r{index:06d}.png") for index in range(1, count + 1)
            ]
            for index, frame in enumerate(decoded):
                image = read_png16(frame)
                own = _mean_abs(image, references[index])
                previous = _mean_abs(image, references[index - 1]) if index > 0 else None
                following = _mean_abs(image, references[index + 1]) if index + 1 < count else None
                neighbours = [value for value in (previous, following) if value is not None]
                margin = min(neighbours) - own if neighbours else None
                bias = (image - references[index]).mean(axis=(0, 1), dtype=np.float64) * 255.0
                bias_sum += bias
                reasons = []
                if not own <= max_own:
                    reasons.append(f"differs from its own PNG by {own:.3f} levels")
                if margin is not None and not margin > 0:
                    reasons.append(
                        f"is no closer to its own PNG ({own:.3f}) than to a neighbour's "
                        f"({min(neighbours):.3f})"
                    )
                records.append(
                    {
                        "index": index,
                        "own": own,
                        "previous": previous,
                        "next": following,
                        "margin": margin,
                        "bias": [float(value) for value in bias],
                        "ok": not reasons,
                    }
                )
                if reasons:
                    failed.append({"index": index, "reason": "; ".join(reasons)})
        channel_bias = [float(value) for value in bias_sum / max(count, 1)]
        if any(not abs(value) <= READBACK_MAX_CHANNEL_BIAS for value in channel_bias):
            problems.append(f"a channel's mean bias {channel_bias} exceeds the limit")
        margins = [(r["margin"], r["index"]) for r in records if r["margin"] is not None]
        smallest = min(margins) if margins else (None, None)
        return {
            "label": clip.name,
            "method": READBACK_METHOD,
            "factor": factor,
            "reduced_size": list(size),
            "frames_expected": count,
            "frames_read": len(decoded),
            "thresholds": {
                "max_own": max_own,
                "max_channel_bias": READBACK_MAX_CHANNEL_BIAS,
                "margin": "own below both neighbours' differences",
            },
            "clip_tags": clip_tags.record(),
            "worst_own": max((r["own"] for r in records), default=None),
            "smallest_margin": smallest[0],
            "smallest_margin_frame": smallest[1],
            "channel_bias": channel_bias,
            "problems": problems,
            "failed_frames": failed,
            "frames": records,
            "ok": bool(records) and not problems and not failed,
        }
    finally:
        shutil.rmtree(roots.check(scratch), ignore_errors=True)
        if scratch.exists():
            print(f"warning: could not remove {scratch}", file=sys.stderr)
        with contextlib.suppress(OSError):  # other read-back folders there, or already gone
            roots.check(scratch.parent).rmdir()


# --- the deep part (WP1.3D) -----------------------------------------------------------------------

DEEP_VARIANT_ORDER = ("c3", "ancuti2018", "ancuti2018-blue")
"""The deep pack's variants, c3 first (the default method of spec v0.5.3)."""

DEEP_CLIP_VARIANTS = ("c3", "ancuti2018")
"""The variants the deep clip is rendered with."""

DEEP_SMOOTHER = Smoother("gaussian", 2.0)
"""The deep clip's smoothing: the centred Gaussian at 2.0 s, the provisional default (DR-25(3))."""

DEEP_CLIP_SECONDS = 6.0
DEEP_CAP_TOLERANCE = 1e-9
"""The alpha shortfall below which the deep clip does not call a gain cap bound: rounding of the
smoothed statistics (a smoothed constant 1.0 is 0.9999999999999999), not a cap."""
DEEP_READBACK_MAX_OWN = 5.0
"""The deep clip's read-back bound on a frame's difference to its own PNG, in 8-bit levels.

The shallow clip's 3.0 (:data:`READBACK_MAX_OWN`) is too tight for the noisy deep footage: a
lossy encode of the first render measured 1.0 to 3.85 levels (mean 1.9) on the corrected frames and
up to 3.03 on the source frames, with every frame still closer to its own PNG than to a
neighbour's by at least 1.6 levels. The neighbour test and the channel-bias bound are unchanged.
"""
DEEP_PENDING: tuple[tuple[str, str], ...] = (
    ("Photos (iPhone)", "none supplied for this part"),
    (
        "Chaptered recordings across a chapter boundary",
        "none in the SCUBA/ set (inventory 2026-10-18)",
    ),
)
"""Cases this part cannot show; they are named, never approximated."""


def deep_variants(base: Params | None = None) -> tuple[Variant, ...]:
    """Return the three variants of the deep pack: ``c3``, ``ancuti2018``, ``ancuti2018-blue``.

    The same variants as :func:`default_variants`, in the order of :data:`DEEP_VARIANT_ORDER`
    (the only presentation change from WP1.3: c3 is the default method of spec v0.5.3). Each sets
    its method explicitly, so a later change of the ``Params()`` default method does not change
    this pack.

    Args:
        base: The parameter set the variants change; defaults to ``Params()``.

    Returns:
        The variants.
    """
    by_name = {variant.name: variant for variant in default_variants(base)}
    return tuple(by_name[name] for name in DEEP_VARIANT_ORDER)


@dataclasses.dataclass(frozen=True)
class DeepEntry:
    """One frame on the deep page: the extracted frame and the caption under its source.

    Attributes:
        frame: The extracted full-resolution frame.
        caption: Text for the line under the source thumbnail (the candidate's rank and
            measures, or empty).
    """

    frame: FrameFile
    caption: str = ""


@dataclasses.dataclass(frozen=True)
class DeepSection:
    """A titled group of frames on the deep page.

    Attributes:
        group: The page heading the section belongs to (several sections may share one).
        title: The section's own heading.
        note: A line under the heading.
        entries: The frames, in page order.
    """

    group: str
    title: str
    note: str
    entries: tuple[DeepEntry, ...]


def clip_window(centre_s: float, duration_s: float, seconds: float = DEEP_CLIP_SECONDS) -> float:
    """Return the start of an excerpt of ``seconds`` centred on ``centre_s``, inside the chapter.

    Args:
        centre_s: The wanted centre in seconds.
        duration_s: The chapter duration in seconds.
        seconds: The excerpt length in seconds.

    Returns:
        ``centre_s - seconds / 2``, but not before 0 and not after ``duration_s - seconds`` (a
        chapter shorter than the excerpt starts at 0).
    """
    return min(max(centre_s - seconds / 2.0, 0.0), max(duration_s - seconds, 0.0))


def candidate_caption(case: scan.Case, entry: Mapping[str, Any]) -> str:
    """Return the caption of a case candidate: rank, the rule, the measures, the other cases.

    The wording is "candidate", never a claim that the frame shows the case.

    Args:
        case: The case.
        entry: The candidate's entry of ``deep-frames.json``.

    Returns:
        The caption text.
    """
    text = (
        f"{case.label}: {case.rule}, rank {entry['rank']}; "
        f"D {entry['D']:.3f}, W {entry['W']:.3f}, H {entry['H']:.4f}"
    )
    others = [name for name in entry["serves_cases"] if name != case.name]
    if others:
        text += "; also a candidate for " + ", ".join(others)
    return text


def deep_sections(
    stills: Sequence[FrameFile],
    candidates: Mapping[str, Sequence[tuple[FrameFile, Mapping[str, Any]]]],
) -> list[DeepSection]:
    """Arrange the deep page: the chapter stills, then one section per case.

    Args:
        stills: The chapter stills in order (grouped by chapter).
        candidates: Case name to its ranked ``(frame, deep-frames.json entry)`` pairs.

    Returns:
        The sections: one per chapter (group "Chapter stills"), then one per case in
        :data:`lookcheck.scan.CASES` that has candidates (group "Case candidates").
    """
    sections: list[DeepSection] = []
    for chapter in dict.fromkeys(frame.chapter for frame in stills):
        sections.append(
            DeepSection(
                "Chapter stills",
                chapter,
                "six stills from 5 % to 95 % of the chapter",
                tuple(DeepEntry(frame) for frame in stills if frame.chapter == chapter),
            )
        )
    for case in scan.CASES:
        found = candidates.get(case.name, ())
        if found:
            sections.append(
                DeepSection(
                    "Case candidates",
                    case.label,
                    f"{case.rule}. These are CANDIDATES proposed by the scan; the owner decides "
                    "at CP2 whether each shows the case.",
                    tuple(
                        DeepEntry(frame, candidate_caption(case, entry)) for frame, entry in found
                    ),
                )
            )
    return sections


def render_deep_index(
    sections: Sequence[DeepSection],
    variants: Sequence[Variant],
    statistics_document: Mapping[str, Any],
    pack_dir: Path,
    clips: Sequence[Path] = (),
) -> str:
    """Render the deep ``index.html``: one static page, relative links only, no external resource.

    The head lists the variants (with the method and blue compensation each runs with), every
    ``Params`` default, the scan and candidate rules and the cases not shown. Then, per section,
    one row per frame as in :func:`render_index`; the case sections come after the chapter
    stills. Clip files, if any, are linked after the head.

    Args:
        sections: The page's sections (:func:`deep_sections`).
        variants: The variants shown, in column order.
        statistics_document: The document returned by :func:`build_pack`.
        pack_dir: The pack folder (links are relative to it).
        clips: The clip files of :func:`run_deep_clip`, if built.

    Returns:
        The page.
    """
    by_frame = {entry["frame"]: entry for entry in statistics_document["frames"]}

    def link(path: Path) -> str:
        return html.escape(path.relative_to(pack_dir).as_posix(), quote=True)

    rules = scan.rules_record()
    out: list[str] = [
        "<!DOCTYPE html>",
        '<html lang="en"><head><meta charset="utf-8">',
        "<title>Clearwater WP1.3D look check pack (deep part)</title>",
        f"<style>{_STYLE}</style></head><body>",
        "<h1>Clearwater look check pack: deep footage (WP1.3D, spec v0.5.3)</h1>",
        f"<p>Device: {html.escape(str(statistics_document['device']))}. Written "
        f"{html.escape(str(statistics_document['written']))}. Full-size 16-bit PNGs are behind "
        "every thumbnail; the pair links are side-by-side JPEGs (source left, corrected "
        'right). Raw numbers: <a href="statistics.json">statistics.json</a>, '
        '<a href="frames.json">frames.json</a> (exact pts and colour tags), '
        '<a href="scan.json">scan.json</a> (every scanned frame) and '
        '<a href="deep-frames.json">deep-frames.json</a> (the ranked candidates).</p>',
        "<h2>Variants</h2><p>Every variant runs at the Params defaults below with only the "
        "method (and blue compensation) set. The method is set explicitly in each variant, so a "
        "later change of the Params() default method does not change this pack. Order: c3 (the "
        "default method of v0.5.3) first.</p>",
        "<table><tr><th>Name</th><th>Prototype flags</th><th>method</th>"
        "<th>blue_compensation</th></tr>",
    ]
    out.extend(
        f"<tr><td>{html.escape(v.name)}</td><td>{html.escape(v.flags)}</td>"
        f"<td>{html.escape(v.params.method)}</td><td>{v.params.blue_compensation}</td></tr>"
        for v in variants
    )
    out.append("</table><h2>Defaults used (Params)</h2><table>")
    out.extend(
        f"<tr><td>{html.escape(name)}</td><td>{html.escape(str(value))}</td></tr>"
        for name, value in statistics_document["defaults"].items()
    )
    out.append("</table><h2>How the candidates were picked</h2><ul>")
    scanned = rules["scan"]
    water = rules["open_water"]
    out.extend(
        f"<li>{html.escape(text)}</li>"
        for text in (
            f"Scan: one frame every {scanned['step_s']:g} s from {scanned['start_s']:g} s to the "
            f"end of each chapter, short side {scanned['short_side']} (FFmpeg scaler, for "
            "ranking only).",
            "D = mean R / mean G (lower = deeper). W = fraction of pixels whose luma local "
            f"standard deviation over a {water['box']}x{water['box']} box is below "
            f"{water['luma_local_std_below']:g} and whose blue or green exceeds red by at least "
            f"{water['blue_or_green_exceeds_red_by_at_least']:g}. H = luma RMS contrast "
            "(lower = hazier).",
            "A frame whose luma mean is below "
            f"{rules['exclusion']['luma_mean_below']:g} or above "
            f"{rules['exclusion']['luma_mean_above']:g} is excluded from every ranking.",
            *(f"{case.label}: {case.rule}." for case in scan.CASES),
            f"{rules['candidates']['per_case']} candidates per case, at least "
            f"{rules['candidates']['min_separation_s']:g} s apart within a chapter, at most "
            f"{rules['candidates']['per_chapter_per_case']} per chapter per case; ties break by "
            "chapter name, then pts. A frame may serve two cases (its caption says so).",
            "These are CANDIDATES; the owner decides at CP2 what each frame shows.",
        )
    )
    out.append("</ul><h2>Not in this part</h2><ul>")
    out.extend(
        f"<li>PENDING: {html.escape(name)} - {html.escape(why)}</li>" for name, why in DEEP_PENDING
    )
    out.append("</ul>")
    if clips:
        out.append(
            "<h2>The deep clip in motion</h2><p>Six seconds centred on the deepest candidate, "
            "statistics STAGED and smoothed with a centred Gaussian at 2.0 s (the provisional "
            'default). Statistics: <a href="clip/statistics.json">clip/statistics.json</a>.'
            "</p><ul>"
        )
        out.extend(
            f'<li><a href="{link(clip)}">{html.escape(clip.name)}</a></li>' for clip in clips
        )
        out.append("</ul>")
    current_group = ""
    for section in sections:
        if section.group != current_group:
            current_group = section.group
            out.append(f"<h2>{html.escape(current_group)}</h2>")
        out.append(
            f"<h3>{html.escape(section.title)}</h3><p>{html.escape(section.note)}</p>"
            '<table class="grid"><tr><th>Source</th>'
        )
        out.extend(f"<th>{html.escape(v.name)}</th>" for v in variants)
        out.append("</tr>")
        for entry in section.entries:
            frame = entry.frame
            thumb = pack_dir / "thumbs" / f"{frame.path.stem}.jpg"
            caption = f"<br>{html.escape(entry.caption)}" if entry.caption else ""
            cells = [
                f'<td><a href="{link(frame.path)}"><img src="{link(thumb)}" '
                f'alt="{html.escape(frame.path.stem)}"></a>'
                f'<div class="cap">{html.escape(frame.chapter)} at {float(frame.pts):.3f} s '
                f"(pts {frame.pts_ticks} / {frame.time_base.denominator}){caption}</div></td>"
            ]
            for variant in variants:
                stem = f"{frame.path.stem}-{variant.name}"
                png = frame.path.with_name(f"{stem}.png")
                record = by_frame[frame.path.stem]["variants"][variant.name]
                thumb_link = link(pack_dir / "thumbs" / f"{stem}.jpg")
                cells.append(
                    f'<td><a href="{link(png)}"><img src="{thumb_link}"'
                    f' alt="{html.escape(stem)}"></a><div class="cap">'
                    f'<a href="{link(pack_dir / "pairs" / f"{stem}.jpg")}">pair</a> '
                    f"{html.escape(summary_line(record))}</div></td>"
                )
            out.append("<tr>" + "".join(cells) + "</tr>")
        out.append("</table>")
    out.append("</body></html>")
    return "\n".join(out) + "\n"


def build_deep_pack(
    stills: Sequence[FrameFile],
    candidates: Mapping[str, Sequence[tuple[FrameFile, Mapping[str, Any]]]],
    pack_dir: Path,
    roots: OutputRoots,
    backend: Backend,
    clips: Sequence[Path] = (),
) -> dict[str, Any]:
    """Correct the deep frames under the three deep variants and write the pack and its page.

    The frames are the chapter stills and the case candidates (a frame that is both, or serves
    two cases, is corrected once); their source PNGs must already be in ``pack_dir/frames``.
    The files are :func:`build_pack`'s, in the order c3, ancuti2018, ancuti2018-blue; the page
    is :func:`render_deep_index`.

    Args:
        stills: The chapter stills in page order.
        candidates: Case name to its ranked ``(frame, deep-frames.json entry)`` pairs.
        pack_dir: The pack folder (``<working folder>/wp1.3d``).
        roots: The output safety roots.
        backend: Where the pipeline runs.
        clips: The deep clip files to link on the page, if built.

    Returns:
        The statistics document that was written.

    Raises:
        lookcheck.frames.OutputPathError: An output path is refused.
        ValueError: A frame's PNG is not a 16-bit RGB PNG.
    """
    chosen = deep_variants()
    unique: dict[Path, FrameFile] = {}
    for frame in [*stills, *(frame for found in candidates.values() for frame, _ in found)]:
        unique.setdefault(frame.path, frame)
    sections = deep_sections(stills, candidates)

    def page(
        _frames: Sequence[FrameFile],
        variants: Sequence[Variant],
        document: Mapping[str, Any],
        folder: Path,
    ) -> str:
        return render_deep_index(sections, variants, document, folder, clips)

    return build_pack(list(unique.values()), pack_dir, roots, backend, chosen, page)


def _load_deep_frames(roots: OutputRoots) -> dict[str, Any]:
    """Read the scan's ``deep-frames.json`` and check it against ``scan.json``.

    The candidates and the deepest list are rebuilt from the frames of ``scan.json`` with
    :func:`lookcheck.scan.deep_frames_document`; a file that differs from the rebuilt one (other
    than in its ``written`` time) is an error, so the page can only present the candidates the
    scan's own records give.

    Raises:
        lookcheck.frames.ExtractError: Either file is missing, or they disagree.
    """
    path = roots.check(roots.allowed / "deep-frames.json")
    scan_path = roots.check(roots.allowed / "scan.json")
    if not path.is_file() or not scan_path.is_file():
        raise ExtractError(
            f"{path} or {scan_path.name} does not exist; run tools/lookcheck/scan.py"
        )
    document: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    scanned = json.loads(scan_path.read_text(encoding="utf-8"))
    records = [scan.ScanRecord.from_record(entry) for entry in scanned["frames"]]
    rebuilt = json.loads(
        _json_text(scan.deep_frames_document(records, document.get("written", "")))
    )
    if document != rebuilt:
        raise ExtractError("deep-frames.json does not match the frames of scan.json; run the scan")
    return document


def run_deep_stills(
    roots: OutputRoots, footage: Path, backend: Backend, clips: Sequence[Path] = ()
) -> dict[str, Any]:
    """Extract the deep stills and candidates at full resolution and build the pack.

    Six stills per ``SCUBA/`` chapter at the WP1.3 positions (:data:`STILL_FRACTIONS`), and
    each candidate of ``deep-frames.json`` re-extracted at its exact pts (an error if the frame
    found is not the scan's).

    Args:
        roots: The output safety roots.
        footage: The footage folder (read only).
        backend: Where the pipeline runs.
        clips: The deep clip files to link on the page, if built.

    Returns:
        The statistics document of :func:`build_deep_pack`.

    Raises:
        lookcheck.frames.ExtractError: A probe or decode fails, or a candidate is not the frame
            the scan measured.
    """
    deep = _load_deep_frames(roots)
    pack_dir = roots.allowed
    stills: list[FrameFile] = []
    videos: dict[str, Path] = {}
    for chapter in scan.SCAN_CHAPTERS:
        video = find_footage_file(chapter, footage)
        videos[chapter] = video
        info = probe_stream(video)
        for note in info.tags.assumed:
            print(f"warning: {chapter}: {note} missing, assumed (spec D54)", file=sys.stderr)
        stills.extend(
            extract(video, still_timestamps(info.duration_s), pack_dir / "frames", roots=roots)
        )
    candidates: dict[str, list[tuple[FrameFile, Mapping[str, Any]]]] = {}
    for case in scan.CASES:
        for entry in deep["cases"][case.name]["frames"]:
            (frame,) = extract(
                videos[entry["chapter"]],
                [float(Fraction(entry["pts_ticks"]) * Fraction(entry["time_base"]))],
                pack_dir / "frames",
                roots=roots,
            )
            if frame.pts_ticks != entry["pts_ticks"] or frame.path.stem != entry["frame"]:
                raise ExtractError(
                    f"candidate {entry['frame']} (pts {entry['pts_ticks']}) was extracted as "
                    f"{frame.path.stem} (pts {frame.pts_ticks}); refusing to label it"
                )
            candidates.setdefault(case.name, []).append((frame, entry))
    return build_deep_pack(stills, candidates, pack_dir, roots, backend, clips)


def _sha256(path: Path) -> str:
    """Return the SHA-256 of a file's bytes as hex."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clear_clip(roots: OutputRoots, clip_dir: Path) -> None:
    """Delete what an earlier deep clip left in ``clip_dir``: MP4s, statistics, frame PNGs.

    :func:`render_deep_clip` calls it before it writes anything, so that a render that fails
    leaves neither a stale ``statistics.json`` nor stale frames or clips for
    :func:`encode_deep_clip` or the page to pick up.

    Args:
        roots: The output safety roots.
        clip_dir: The clip folder (a missing folder is fine).
    """
    for pattern in ("*.mp4", "statistics.json", "statistics-*.png"):
        for path in sorted(clip_dir.glob(pattern)):
            roots.remove(path)
    for folder in [*sorted(clip_dir.glob("corrected-*")), clip_dir / "source"]:
        for path in sorted(folder.glob("*.png")):
            roots.remove(path)


def render_deep_clip(
    video: Path,
    centre_s: float,
    roots: OutputRoots,
    backend: Backend,
    clip_dir: Path,
    *,
    seconds: float = DEEP_CLIP_SECONDS,
    smoother: Smoother = DEEP_SMOOTHER,
) -> dict[str, Any]:
    """Render the deep clip's frames: a 6 s excerpt corrected with STAGED, smoothed statistics.

    The excerpt (:func:`clip_window` around ``centre_s``) is extracted frame by frame at full
    resolution. Statistics are measured on the 540-line proxy built in NumPy, an exact 4x4
    area mean (:func:`prototype.temporal.proxy`, not FFmpeg's scaler), analysed STAGED (spec D97,
    :func:`prototype.temporal.analyse_staged`) and smoothed with ``smoother`` (the centred
    Gaussian at 2.0 s). Each frame is rendered from its smoothed statistics for ``c3`` and
    ``ancuti2018`` (:data:`DEEP_CLIP_VARIANTS`; the same call as
    :func:`prototype.temporal.render`, kept as a :class:`prototype.pipeline.Result` so that its
    record is available). The numbered PNG sets go to ``clip_dir/source`` and
    ``clip_dir/corrected-<variant>``. ``statistics.json`` (per variant and frame: the raw
    unsmoothed and the smoothed statistics and the render's record) and one plot per variant are
    written BEFORE any encode, so that the slow part is never lost to a failing encode check;
    ``encode_commands`` and ``checks`` in it are ``null`` until :func:`encode_deep_clip` runs.

    Args:
        video: The source chapter.
        centre_s: The centre of the excerpt in seconds (the deepest candidate's pts).
        roots: The output safety roots.
        backend: Where the pipeline runs.
        clip_dir: The output folder (``<working folder>/wp1.3d/clip``).
        seconds: The excerpt length in seconds.
        smoother: The statistics smoother.

    Returns:
        The statistics document that was written.

    Raises:
        lookcheck.frames.ExtractError: A probe or decode fails.
    """
    info = probe_stream(video)
    start = clip_window(centre_s, info.duration_s, seconds)
    source_dir = clip_dir / "source"
    clear_clip(roots, clip_dir)  # a failed render must leave nothing for an encode to pick up
    began = time.monotonic()
    got = excerpt(video, start, seconds, source_dir, roots=roots, naming="index")
    print(f"extracted {len(got)} frames in {time.monotonic() - began:.0f} s", file=sys.stderr)
    chosen = [variant for variant in deep_variants() if variant.name in DEEP_CLIP_VARIANTS]
    proxies = [temporal.proxy(read_png16(frame.path)) for frame in got]
    analyses = {
        variant.name: temporal.analyse_staged(
            proxies, variant.params, smoother, info.frame_rate, backend
        )
        for variant in chosen
    }
    del proxies
    print(f"analysed {len(got)} frames in {time.monotonic() - began:.0f} s", file=sys.stderr)
    entries: dict[str, list[dict[str, Any]]] = {variant.name: [] for variant in chosen}
    for number, frame in enumerate(got):
        image = read_png16(frame.path)
        source_sha = _sha256(frame.path)
        for variant in chosen:
            smoothed, measured = analyses[variant.name]
            result = correct(
                image, variant.params, backend, statistics=temporal.at(smoothed, number)
            )
            target = (
                clip_dir / f"corrected-{variant.name}" / f"{frame.path.stem}-{variant.name}.png"
            )
            _write_png(roots, target, result.output)
            record = statistics_record(result, backend, DEEP_CAP_TOLERANCE)
            del record["params"], record["backend"]
            entries[variant.name].append(
                {
                    "index": number,
                    "pts_ticks": frame.pts_ticks,
                    "pts_seconds": float(frame.pts),
                    "source_file": frame.path.name,
                    "source_sha256": source_sha,
                    "corrected_file": target.name,
                    "corrected_sha256": _sha256(target),
                    "raw": {
                        name: float(values[number])
                        for stage in measured.values()
                        for name, values in stage.items()
                    },
                    "smoothed": {name: float(values[number]) for name, values in smoothed.items()},
                    "rendered": record,
                }
            )
        if number % 20 == 0:
            print(f"rendered {number + 1}/{len(got)}", file=sys.stderr)
    pts_seconds = [float(frame.pts) for frame in got]
    variants_record: dict[str, Any] = {}
    for variant in chosen:
        rows = entries[variant.name]
        series = {
            "red gain, applied": [r["rendered"]["red_gain"] for r in rows],
            "red gain, raw gray-world": [r["raw"]["white_balance_gains.R"] for r in rows],
            "red gain, smoothed gray-world": [r["smoothed"]["white_balance_gains.R"] for r in rows],
            "blue gain, applied": [r["rendered"]["blue_gain"] for r in rows],
            "blue gain, raw gray-world": [r["raw"]["white_balance_gains.B"] for r in rows],
            "blue gain, smoothed gray-world": [
                r["smoothed"]["white_balance_gains.B"] for r in rows
            ],
        }
        if variant.params.method == "ancuti2018":
            series["effective alpha (red)"] = [
                r["rendered"]["compensation"]["effective"]["red"] for r in rows
            ]
        roots.write_bytes(
            clip_dir / f"statistics-{variant.name}.png", plot_series(series, pts_seconds)
        )
        variants_record[variant.name] = {
            "flags": variant.flags,
            "params": dataclasses.asdict(variant.params),
            "summary": {name: series_summary(values) for name, values in series.items()},
            "bound_counts": {
                "red_gain_cap": sum(r["rendered"]["bound"]["red_gain_cap"] for r in rows),
                "blue_gain_cap": sum(r["rendered"]["bound"]["blue_gain_cap"] for r in rows),
                "white_balance_clamp_any": sum(
                    any(r["rendered"]["bound"]["white_balance_clamp"]) for r in rows
                ),
                "normalisation_collapsed": sum(
                    r["rendered"]["bound"]["normalisation_collapsed"] for r in rows
                ),
            },
            "frames": rows,
        }
    document = {
        "schema": STATISTICS_SCHEMA,
        "written": _now(),
        "spec": scan.SPEC_VERSION,
        "source": str(video),
        "source_bytes": video.stat().st_size,
        "chapter": video.stem,
        "analysis": "STAGED (spec D97), prototype.temporal.analyse_staged",
        "proxy": "exact area mean of the full-resolution frame in NumPy (prototype.temporal.proxy)",
        "smoother": {"kind": smoother.kind, "window_s": smoother.window_s},
        "centre_s": centre_s,
        "device": backend.name,
        "excerpt": {
            "start_s": start,
            "duration_s": seconds,
            "frames": len(got),
            "first_pts_ticks": got[0].pts_ticks,
            "last_pts_ticks": got[-1].pts_ticks,
            "time_base": f"{info.time_base.numerator}/{info.time_base.denominator}",
            "frame_rate": f"{info.frame_rate.numerator}/{info.frame_rate.denominator}",
            "first_pts_seconds": pts_seconds[0],
            "last_pts_seconds": pts_seconds[-1],
        },
        "tags": info.tags.record(),
        "ffmpeg": tool_version("ffmpeg"),
        "extract_command": list(got[0].command),
        "encode_commands": None,
        "checks": None,
        "variants": variants_record,
    }
    roots.write_text(clip_dir / "statistics.json", _json_text(document))
    return document


def clip_inputs_problem(
    document: Mapping[str, Any], stem: str, clip_dir: Path, source_bytes: int | None = None
) -> str | None:
    """Say why the PNG sets in ``clip_dir`` cannot be encoded under ``document``, or ``None``.

    The statistics document and the frames must belong together: it is the document that
    :func:`render_deep_clip` wrote for this chapter, not yet encoded (``checks`` is ``null``), for
    the variants and parameters of this code, with the same frames and pts in every variant, and
    the PNG sets on disk are exactly the files it names, byte for byte (the SHA-256 recorded
    when each was written).

    Args:
        document: The parsed ``statistics.json``.
        stem: The chapter stem of the source video.
        clip_dir: The clip folder.
        source_bytes: The size of the source video now on disk; when given it must be the size of
            the file the clip was rendered from.

    Returns:
        A one-line reason, or ``None``.
    """
    if document.get("chapter") != stem:
        return f"the statistics are for chapter {document.get('chapter')!r}, not {stem}"
    if document.get("checks") is not None:
        return "it is already encoded (its frames were pruned); render the clip again"
    if not str(document.get("analysis", "")).startswith("STAGED"):
        return "the statistics were not analysed STAGED"
    if source_bytes is not None and document.get("source_bytes") != source_bytes:
        return "the source video is not the file the clip was rendered from"
    variants = document.get("variants", {})
    if list(variants) != list(DEEP_CLIP_VARIANTS):
        return f"variants {list(variants)} are not {list(DEEP_CLIP_VARIANTS)}"
    smoother = document.get("smoother")
    if smoother != {"kind": DEEP_SMOOTHER.kind, "window_s": DEEP_SMOOTHER.window_s}:
        return f"smoother {smoother} is not the deep clip's"
    count = document["excerpt"]["frames"]
    expected = {variant.name: variant for variant in deep_variants()}
    ticks: list[int] | None = None
    for name, body in variants.items():
        if body["params"] != dataclasses.asdict(expected[name].params):
            return f"the {name} parameters differ from this code's"
        rows = body["frames"]
        if [row["index"] for row in rows] != list(range(count)):
            return f"the {name} frames are not 0..{count - 1}"
        row_ticks = [row["pts_ticks"] for row in rows]
        if ticks is not None and row_ticks != ticks:
            return f"the {name} frames have other pts than the first variant's"
        ticks = row_ticks
        if {path.name for path in (clip_dir / f"corrected-{name}").glob("*.png")} != {
            row["corrected_file"] for row in rows
        }:
            return f"the corrected-{name} PNGs are not the {count} the statistics name"
        for row in rows:
            if (
                _sha256(clip_dir / f"corrected-{name}" / row["corrected_file"])
                != row["corrected_sha256"]
            ):
                return f"{row['corrected_file']} is not the file the render wrote"
    sources = {row["source_file"] for body in variants.values() for row in body["frames"]}
    if {path.name for path in (clip_dir / "source").glob("*.png")} != sources:
        return f"the source PNGs are not the {count} the statistics name"
    first = variants[next(iter(variants))]["frames"]
    for row in first:
        if _sha256(clip_dir / "source" / row["source_file"]) != row["source_sha256"]:
            return f"{row['source_file']} is not the file the render read"
    return None


def encode_deep_clip(
    video: Path, roots: OutputRoots, clip_dir: Path, *, max_own: float = DEEP_READBACK_MAX_OWN
) -> dict[str, Any]:
    """Encode the rendered deep clip's PNG sets to MP4, check them, and prune the PNGs.

    Reads ``clip_dir/statistics.json`` (:func:`render_deep_clip`), encodes the corrected sets
    and the untouched source frames to ``<chapter>_c3.mp4``, ``<chapter>_ancuti2018.mp4`` and
    ``<chapter>_source.mp4`` with :func:`encode_verified_pair` (the clip check of
    :func:`verify_clip` and the read-back of every frame, whose own-PNG bound is ``max_own``),
    records the commands and checks in ``statistics.json``, and only then deletes all frame
    PNGs but the first, middle and last of each set.

    Args:
        video: The source chapter (probed for the frame rate, size and tags the clips carry).
        roots: The output safety roots.
        clip_dir: The clip folder.
        max_own: The read-back bound on a clip frame's difference to its own PNG, in 8-bit
            levels (:data:`DEEP_READBACK_MAX_OWN` by default).

    Returns:
        The updated statistics document.

    Raises:
        lookcheck.frames.ExtractError: The statistics and the PNG sets do not belong together
            (:func:`clip_inputs_problem`), a probe or encode fails or a check does not hold (the
            frame PNGs are then kept and no clip exists under its final name).
    """
    path = roots.check(clip_dir / "statistics.json")
    if not path.is_file():
        raise ExtractError(f"{path} does not exist; render the deep clip first")
    document: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    problem = clip_inputs_problem(document, video.stem, clip_dir, video.stat().st_size)
    if problem is not None:
        raise ExtractError(f"the deep clip cannot be encoded: {problem}")
    info = probe_stream(video)
    count = document["excerpt"]["frames"]
    stem = video.stem
    names = list(document["variants"])
    clips = {
        **{
            name: (
                clip_dir / f"corrected-{name}" / f"{stem}_f%04d-{name}.png",
                clip_dir / f"{stem}_{name}.mp4",
            )
            for name in names
        },
        "source": (clip_dir / "source" / f"{stem}_f%04d.png", clip_dir / f"{stem}_source.mp4"),
    }
    commands, checks = encode_verified_pair(roots, clips, info, count, clip_dir, max_own)
    document["encode_commands"] = commands
    document["checks"] = checks
    document["clips"] = {
        label: {"file": target.name, "bytes": target.stat().st_size, "sha256": _sha256(target)}
        for label, (_pattern, target) in clips.items()
    }
    roots.write_text(path, _json_text(document))
    keep = {0, count // 2, count - 1}
    for number in range(count):
        if number not in keep:
            roots.remove(clip_dir / "source" / f"{stem}_f{number:04d}.png")
            for name in names:
                roots.remove(clip_dir / f"corrected-{name}" / f"{stem}_f{number:04d}-{name}.png")
    return document


def run_deep_clip(
    video: Path,
    centre_s: float,
    roots: OutputRoots,
    backend: Backend,
    clip_dir: Path,
    *,
    seconds: float = DEEP_CLIP_SECONDS,
    smoother: Smoother = DEEP_SMOOTHER,
) -> dict[str, Any]:
    """Build the deep clip: :func:`render_deep_clip`, then :func:`encode_deep_clip`.

    Args:
        video: The source chapter.
        centre_s: The centre of the excerpt in seconds (the deepest candidate's pts).
        roots: The output safety roots.
        backend: Where the pipeline runs.
        clip_dir: The output folder (``<working folder>/wp1.3d/clip``).
        seconds: The excerpt length in seconds.
        smoother: The statistics smoother.

    Returns:
        The statistics document, with the encode commands and checks.

    Raises:
        lookcheck.frames.ExtractError: A probe, decode or encode fails or a check does not hold.
    """
    render_deep_clip(video, centre_s, roots, backend, clip_dir, seconds=seconds, smoother=smoother)
    return encode_deep_clip(video, roots, clip_dir)


def clip_files(roots: OutputRoots, clip_dir: Path) -> list[Path]:
    """Return the deep clip's MP4s (c3, ancuti2018, source) for the page, once they are verified.

    The clips are returned only when ``clip_dir/statistics.json`` records that they were
    encoded and that every check held, and when that clip was centred on the deepest frame of
    the current ``deep-frames.json``; a half-built or stale clip is an error, never a link.

    Args:
        roots: The output safety roots.
        clip_dir: The clip folder.

    Returns:
        The clips, in a fixed order; empty if no clip was ever rendered.

    Raises:
        lookcheck.frames.ExtractError: The clip is rendered but not encoded and verified, a check
            failed, it was cut around another frame than the current deepest one, or an MP4 is
            missing.
    """
    statistics_path = roots.check(clip_dir / "statistics.json")
    if not statistics_path.is_file():
        return []
    document = json.loads(statistics_path.read_text(encoding="utf-8"))
    checks = document.get("checks")
    if checks is None:
        raise ExtractError("the deep clip is rendered but not encoded; run deep --part encode")
    wanted = (*DEEP_CLIP_VARIANTS, "source", "readback")
    failed = [label for label in wanted if not (checks.get(label) or {}).get("ok")]
    if failed:
        raise ExtractError(f"the deep clip's checks are missing or did not hold: {failed}")
    deepest = _load_deep_frames(roots)["deepest"][0]
    if document["chapter"] != deepest["chapter"] or document["centre_s"] != float(
        deepest["pts_seconds"]
    ):
        raise ExtractError(
            f"the deep clip is centred on {document['chapter']} at {document['centre_s']} s, "
            f"not the deepest frame {deepest['frame']}; render it again"
        )
    found: list[Path] = []
    for label in (*DEEP_CLIP_VARIANTS, "source"):
        path = roots.check(clip_dir / f"{document['chapter']}_{label}.mp4")
        if not path.is_file():
            raise ExtractError(f"{path.name} is missing; render and encode the deep clip again")
        recorded = (document.get("clips") or {}).get(label)
        if not recorded or recorded["sha256"] != _sha256(path):
            raise ExtractError(f"{path.name} is not the file that was verified; encode it again")
        found.append(path)
    return found


def _run_deep(roots: OutputRoots, footage: Path, backend: Backend, part: str) -> None:
    """Run the deep part: the clip (or one of its steps), the stills and page, or all."""
    clip_dir = roots.allowed / "clip"
    if part in ("all", "clip", "render", "encode"):
        deepest = _load_deep_frames(roots)["deepest"][0]
        video = find_footage_file(deepest["chapter"], footage)
        centre = float(deepest["pts_seconds"])
        if part in ("all", "clip", "render"):
            render_deep_clip(video, centre, roots, backend, clip_dir)
        if part in ("all", "clip", "encode"):
            encode_deep_clip(video, roots, clip_dir)
        print(clip_dir)
    if part in ("all", "stills"):
        run_deep_stills(roots, footage, backend, clip_files(roots, clip_dir))
        print(roots.allowed / "index.html")


# --- command line ----------------------------------------------------------------------------


def _run_stills(roots: OutputRoots, footage: Path, backend: Backend) -> None:
    """Extract the stills of every shallow chapter and build the pack."""
    pack_dir = roots.allowed
    frames: list[FrameFile] = []
    for chapter in CHAPTERS:
        video = find_footage_file(chapter, footage)
        info = probe_stream(video)
        for note in info.tags.assumed:
            print(f"warning: {chapter}: {note} missing, assumed (spec D54)", file=sys.stderr)
        frames.extend(
            extract(video, still_timestamps(info.duration_s), pack_dir / "frames", roots=roots)
        )
    build_pack(frames, pack_dir, roots, backend)
    print(pack_dir / "index.html")


def main(argv: Sequence[str] | None = None) -> int:
    """Run ``stills``, ``flicker`` or ``deep`` (module docstring).

    Args:
        argv: Command-line arguments; defaults to ``sys.argv[1:]``.

    Returns:
        0 on success; 2, with a one-line error on standard error, on a configuration, probe,
        device, path or FFmpeg failure.
    """
    parser = argparse.ArgumentParser(description="Build the WP1.3 look check pack.")
    parser.add_argument("command", choices=("stills", "flicker", "deep"))
    parser.add_argument("--config", type=Path, help="local configuration file")
    parser.add_argument("--device", choices=DEVICES, default="gpu")
    parser.add_argument(
        "--part",
        choices=("all", "clip", "render", "encode", "stills"),
        default="all",
        help="deep only: the clip (render, then encode), one of its two steps, the stills and "
        "page, or everything (default)",
    )
    args = parser.parse_args(argv)
    try:
        config = load_local_config(args.config)
        if args.command == "deep":
            roots = OutputRoots.from_config(config, subdir=scan.WORK_SUBDIR)
        else:
            roots = OutputRoots.from_config(config)
        backend = select_backend(args.device)
        if backend.reason:
            print(f"note: running on the CPU: {backend.reason}", file=sys.stderr)
        began = time.monotonic()
        if args.command == "stills":
            _run_stills(roots, config.footage_path, backend)
        elif args.command == "deep":
            _run_deep(roots, config.footage_path, backend, args.part)
        else:
            video = find_footage_file(FLICKER_CHAPTER, config.footage_path)
            run_flicker(video, roots, backend, roots.allowed / "flicker")
            print(roots.allowed / "flicker")
        print(f"elapsed {time.monotonic() - began:.0f} s", file=sys.stderr)
    except (LocalConfigError, ExtractError, RuntimeError, OSError, ValueError) as exc:
        print(f"error: {' '.join(str(exc).split()) or type(exc).__name__}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
