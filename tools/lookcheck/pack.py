"""Build the WP1.3 look check pack: stills under three variants and the flicker clip.

Usage::

    uv run python tools/lookcheck/pack.py stills [--config FILE] [--device gpu|cpu|auto]
    uv run python tools/lookcheck/pack.py flicker [--config FILE] [--device gpu|cpu|auto]

Both read the two folders from the local configuration. The footage folder is only ever an
input; every file written goes under ``<working folder>/wp1.3/`` and is checked first
(:class:`lookcheck.frames.OutputRoots`).

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

``flicker`` corrects every frame of a 6 s excerpt of ``GX011627.MP4`` (starting at 30 %
of the duration) at the defaults with ``ancuti2018``, UNSMOOTHED (each frame its own
statistics), encodes the corrected frames and the untouched source frames to
``flicker/GX011627_unsmoothed.mp4`` and ``flicker/GX011627_source.mp4`` (HEVC NVENC 8-bit
4:2:0 with the source's colour tags and frame rate) under temporary names, checks both
(ffprobe, and every frame of each clip read back against its own PNG), renames them only
when both pass, writes ``flicker/statistics.json`` and a plot, and removes all frame PNGs
but the first, middle and last of each set.

Exit status 0 on success; 2, with a one-line ``error: ...`` on standard error, on a
configuration, probe, device, path or FFmpeg failure.
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import datetime
import html
import io
import json
import statistics
import sys
import time
from collections.abc import Iterator, Mapping, Sequence
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

from local_config import LocalConfigError, load_local_config
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
from prototype.backend import DEVICES, Backend, select_backend
from prototype.params import Params
from prototype.pipeline import Result, correct, normalisation_bounds
from prototype.run import write_png16

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


def statistics_record(result: Result, backend: Backend) -> dict[str, Any]:
    """Record what the prototype measured and did on one frame under one variant.

    The compensation and white balance records are the prototype's own, unchanged
    (``dataclasses.asdict``); the parameters are the ones the pipeline ran with
    (``result.params``). The N{} bounds are not part of :class:`prototype.pipeline.Result`:
    they are recomputed with the prototype's :func:`prototype.pipeline.normalisation_bounds`
    on ``result.white_balanced``, the image that :func:`prototype.pipeline.fusion_inputs`
    measured them on, on the same device. ``bound`` says whether anything bound: a gain cap
    (the effective alpha below the requested one), the white-balance clamp, or an N{} that
    collapsed (a spread under 1e-6, which makes N{} a constant 0.5).

    Args:
        result: The prototype's result for the frame.
        backend: The backend ``result`` was computed on.

    Returns:
        A JSON-ready dictionary.
    """
    compensation = dataclasses.asdict(result.compensation)
    balance = dataclasses.asdict(result.white_balance)
    low, high = normalisation_bounds(backend.to_device(result.white_balanced), result.params)
    requested, effective = compensation["requested"], compensation["effective"]
    cap_bound = {
        channel: bool(effective[channel] < requested[channel])
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
    roots.write_text(pack_dir / "index.html", render_index(frames, chosen, document, pack_dir))
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
            label: readback_clip(partials[label], clips[label][0], count, info, flicker_dir, roots)
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
) -> dict[str, Any]:
    """Read back EVERY frame of an encoded clip and match each to the PNG it came from.

    The clip is converted with the extraction's colour conversion (its own tags) and the PNG
    sequence ``pattern`` is read through FFmpeg, both reduced to 1/8 size
    (:data:`READBACK_METHOD`). Frame ``i`` passes when its mean
    absolute difference to its own PNG (``own``) is at most :data:`READBACK_MAX_OWN` AND is
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
                if not own <= READBACK_MAX_OWN:
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
                "max_own": READBACK_MAX_OWN,
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


# --- command line ----------------------------------------------------------------------------


def _run_stills(roots: OutputRoots, footage: Path, backend: Backend) -> None:
    """Extract the stills of every shallow chapter and build the pack."""
    pack_dir = roots.allowed
    frames: list[FrameFile] = []
    for chapter in CHAPTERS:
        video = footage / f"{chapter}.MP4"
        info = probe_stream(video)
        for note in info.tags.assumed:
            print(f"warning: {chapter}: {note} missing, assumed (spec D54)", file=sys.stderr)
        frames.extend(
            extract(video, still_timestamps(info.duration_s), pack_dir / "frames", roots=roots)
        )
    build_pack(frames, pack_dir, roots, backend)
    print(pack_dir / "index.html")


def main(argv: Sequence[str] | None = None) -> int:
    """Run ``stills`` or ``flicker`` (module docstring).

    Args:
        argv: Command-line arguments; defaults to ``sys.argv[1:]``.

    Returns:
        0 on success; 2, with a one-line error on standard error, on a configuration, probe,
        device, path or FFmpeg failure.
    """
    parser = argparse.ArgumentParser(description="Build the WP1.3 look check pack.")
    parser.add_argument("command", choices=("stills", "flicker"))
    parser.add_argument("--config", type=Path, help="local configuration file")
    parser.add_argument("--device", choices=DEVICES, default="gpu")
    args = parser.parse_args(argv)
    try:
        config = load_local_config(args.config)
        roots = OutputRoots.from_config(config)
        backend = select_backend(args.device)
        if backend.reason:
            print(f"note: running on the CPU: {backend.reason}", file=sys.stderr)
        began = time.monotonic()
        if args.command == "stills":
            _run_stills(roots, config.footage_path, backend)
        else:
            video = config.footage_path / f"{FLICKER_CHAPTER}.MP4"
            run_flicker(video, roots, backend, roots.allowed / "flicker")
            print(roots.allowed / "flicker")
        print(f"elapsed {time.monotonic() - began:.0f} s", file=sys.stderr)
    except (LocalConfigError, ExtractError, RuntimeError, OSError, ValueError) as exc:
        print(f"error: {' '.join(str(exc).split()) or type(exc).__name__}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
