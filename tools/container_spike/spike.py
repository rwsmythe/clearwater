"""Run the WP1.5 container spike (spec D104): capabilities, camera record, identity re-encode.

Usage::

    uv run python tools/container_spike/spike.py capability [--chapter NAME]
    uv run python tools/container_spike/spike.py camera [NAME ...]
    uv run python tools/container_spike/spike.py reencode NAME [--encoder hevc_nvenc|libx265]

All three read the two folders from the local configuration (``--config`` to choose the
file). Chapters are named by file name inside the footage folder, which is only ever an
input. Every file written goes under ``<working folder>/wp1.5/``, and before each
FFmpeg run that writes a file the resolved output path is checked to lie inside that
folder and outside the footage folder (:func:`container_spike.compare.check_output_path`).
FFmpeg runs as a separate process, always with ``-nostdin -hide_banner``; ``-y``
(overwrite) is passed only for an output that has passed the check.

* ``capability`` (D74) writes ``capability.json``: which HEVC and AV1 encoders, hardware
  decoders and hardware acceleration methods the installed build lists, then a proof per
  claim: a 2-second synthetic encode per encoder and bit depth that ``ffprobe``
  confirms, and a hardware (``-hwaccel cuda``) decode of one real chapter that
  completes, each with ``nvidia-smi`` sampled while it runs.
* ``camera`` (D54, D73) writes ``camera.json``: what the camera wrote in each chapter.
* ``reencode`` (D104) decodes one chapter and encodes it again with no correction at
  the source's pixel format and colour tags, copies audio and data streams and
  metadata, keeps the timestamps, writes ``reencode/<stem>_corrected<ext>`` (spec 8.3
  naming), then compares source and output (:mod:`container_spike.compare`) and
  measures the identity PSNR.

Exit status 0 on success; 2, with a one-line ``error: ...`` on standard error, on a
configuration, probe, path or FFmpeg failure.
"""

from __future__ import annotations

import argparse
import datetime
import itertools
import json
import re
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any

if not __package__:
    # Script mode (``python tools/container_spike/spike.py``): sys.path[0] is
    # tools/container_spike, so put the tools directory first to make the
    # ``container_spike`` package and ``local_config`` importable.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from container_spike.compare import (
    MANDATORY,
    SPIKE_SUBDIR,
    OutputPathError,
    ProbeError,
    build_record,
    check_output_path,
    compare_facts,
    edit_effect,
    exact,
    gather,
    pix_fmt_shape,
    run_ffprobe,
    udta_atom,
    write_checked,
    write_record,
)
from local_config import LocalConfigError, load_local_config

FFMPEG_TIMEOUT_SECONDS = 7200.0
OUTPUT_SUFFIX = "_corrected"
ENCODERS = ("hevc_nvenc", "libx265")
# The listing entries the capability record reports (D74), each True when listed.
LISTED_ENCODERS = ("hevc_nvenc", "libx265", "av1_nvenc", "libsvtav1", "libaom-av1")
LISTED_DECODERS = ("hevc_cuvid", "h264_cuvid", "av1_cuvid", "hevc", "h264")
LISTED_HWACCELS = ("cuda", "d3d11va", "dxva2", "d3d12va", "vulkan")
# Quality settings used by the spike (recorded; the product's mapping is D75, WP2.1).
ENCODER_SETTINGS: dict[str, tuple[str, ...]] = {
    "hevc_nvenc": ("-preset", "p5", "-tune", "hq", "-rc", "vbr", "-cq", "20", "-b:v", "0"),
    "libx265": ("-preset", "medium", "-crf", "20"),
}
# (chroma subsampling, bit depth) -> (encoder input pixel format, HEVC profile) per encoder.
_PIXEL_FORMATS: dict[str, dict[tuple[str, int], tuple[str, str]]] = {
    "hevc_nvenc": {("4:2:0", 8): ("yuv420p", "main"), ("4:2:0", 10): ("p010le", "main10")},
    "libx265": {("4:2:0", 8): ("yuv420p", "main"), ("4:2:0", 10): ("yuv420p10le", "main10")},
}
# GoPro global settings keys (moov/udta/GPMF) recorded for D73; the serial number and
# other identifiers are deliberately not read.
GPMF_SETTING_KEYS = ("MINF", "FMWR", "HDRV", "PRTN", "PTCL", "BITR")
_HDR_TRANSFERS = frozenset({"arib-std-b67", "smpte2084"})
_GPU_QUERY = "name,utilization.encoder,utilization.decoder,encoder.stats.sessionCount"
_GPU_SAMPLE_SECONDS = 0.1
_PSNR = re.compile(r"PSNR y:(\S+) u:(\S+) v:(\S+) average:(\S+) min:(\S+) max:(\S+)")
_DECODED = re.compile(r"(\d+) frames decoded; (\d+) decode errors")


class SpikeError(Exception):
    """A spike step failed; the message says which and why."""


# --- running tools ------------------------------------------------------------------


def run_tool(command: Sequence[str], timeout: float = FFMPEG_TIMEOUT_SECONDS) -> tuple[int, str]:
    """Run a command without a shell and return (exit status, standard error text).

    Standard output is discarded unless the caller needs it (see :func:`_ffmpeg_output`).

    Args:
        command: The command and its arguments.
        timeout: Seconds before the run is abandoned.

    Returns:
        The exit status and the standard error text.

    Raises:
        SpikeError: If the program is absent, cannot start or times out.
    """
    try:
        result = subprocess.run(
            list(command),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        raise SpikeError(f"{command[0]} not found") from None
    except subprocess.TimeoutExpired:
        raise SpikeError(f"{command[0]} timed out after {timeout:g} s") from None
    except OSError as exc:
        raise SpikeError(f"{command[0]} could not run: {exc}") from None
    return result.returncode, result.stderr.decode("utf-8", errors="replace")


def _ffmpeg_output(arguments: Sequence[str]) -> str:
    """Return the standard output of ``ffmpeg -hide_banner <arguments>`` (a listing).

    Raises:
        SpikeError: If ``ffmpeg`` is absent or fails.
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", *arguments],
            capture_output=True,
            stdin=subprocess.DEVNULL,
            timeout=60,
            check=False,
        )
    except FileNotFoundError:
        raise SpikeError("ffmpeg not found") from None
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SpikeError(f"ffmpeg could not list {arguments}: {exc}") from None
    if result.returncode != 0:
        raise SpikeError(f"ffmpeg {' '.join(arguments)} failed (status {result.returncode})")
    return result.stdout.decode("utf-8", errors="replace")


def _codec_names(listing: str) -> set[str]:
    """Return the codec names from an ``ffmpeg -encoders`` or ``-decoders`` listing.

    Codec lines have a six-character flag field (``V....D``) and then the name; the
    legend above the ``------`` line is skipped.
    """
    _, _, body = listing.partition("------")
    names = set()
    for line in body.splitlines():
        parts = line.split()
        if len(parts) >= 2 and len(parts[0]) == 6:
            names.add(parts[1])
    return names


def _hwaccel_names(listing: str) -> set[str]:
    """Return the method names from an ``ffmpeg -hwaccels`` listing."""
    _, _, body = listing.partition("Hardware acceleration methods:")
    return {line.strip() for line in body.splitlines() if line.strip()}


def capability_listing() -> dict[str, dict[str, bool]]:
    """Report which encoders, decoders and acceleration methods the build lists (D74).

    An entry absent from a listing is reported False; nothing raises for it.

    Returns:
        ``{"encoders": {...}, "decoders": {...}, "hwaccels": {...}}``, each mapping the
        names in ``LISTED_ENCODERS``, ``LISTED_DECODERS`` and ``LISTED_HWACCELS`` to
        whether the build lists them.

    Raises:
        SpikeError: If ``ffmpeg`` cannot produce a listing.
    """
    encoders = _codec_names(_ffmpeg_output(["-encoders"]))
    decoders = _codec_names(_ffmpeg_output(["-decoders"]))
    hwaccels = _hwaccel_names(_ffmpeg_output(["-hwaccels"]))
    return {
        "encoders": {name: name in encoders for name in LISTED_ENCODERS},
        "decoders": {name: name in decoders for name in LISTED_DECODERS},
        "hwaccels": {name: name in hwaccels for name in LISTED_HWACCELS},
    }


def _gpu_query() -> list[list[str]]:
    """Run one ``nvidia-smi`` query and return its rows (name, encoder %, decoder %, sessions).

    Raises:
        SpikeError: If ``nvidia-smi`` is absent, fails, times out or exits non-zero.
    """
    try:
        result = subprocess.run(
            ["nvidia-smi", f"--query-gpu={_GPU_QUERY}", "--format=csv,noheader,nounits"],
            capture_output=True,
            stdin=subprocess.DEVNULL,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SpikeError(f"nvidia-smi could not run: {exc}") from None
    if result.returncode != 0:
        raise SpikeError(f"nvidia-smi exited with status {result.returncode}")
    text = result.stdout.decode("utf-8", errors="replace")
    return [[part.strip() for part in line.split(",")] for line in text.splitlines()]


@contextmanager
def gpu_samples(record: dict[str, Any]) -> Iterator[None]:
    """Sample ``nvidia-smi`` about every 0.1 s while the ``with`` body runs.

    On exit, ``record`` receives ``gpu``: ``available`` (True only when at least one
    sample succeeded and named a GPU), the GPU names seen, the sample count, the highest
    encoder and decoder utilisation and NVENC session count, and the first sampling error
    if any.

    Args:
        record: The dict that receives the ``gpu`` entry.

    Yields:
        Nothing; the body runs while sampling.
    """
    rows: list[list[str]] = []
    stop = threading.Event()
    errors: list[str] = []

    def sample() -> None:
        # At least one sample, however short the body.
        while True:
            try:
                rows.extend(_gpu_query())
            except SpikeError as exc:
                errors.append(str(exc))
                return
            if stop.wait(_GPU_SAMPLE_SECONDS):
                return

    worker = threading.Thread(target=sample, daemon=True)
    worker.start()
    try:
        yield
    finally:
        stop.set()
        worker.join(timeout=15)
        usable = [row for row in rows if len(row) == 4 and row[0]]

        def highest(column: int) -> int | None:
            values = [int(row[column]) for row in usable if row[column].isdigit()]
            return max(values) if values else None

        record["gpu"] = {
            "available": bool(usable),
            "names": sorted({row[0] for row in usable}),
            "samples": len(usable),
            "max_encoder_utilisation_percent": highest(1),
            "max_decoder_utilisation_percent": highest(2),
            "max_nvenc_sessions": highest(3),
            "error": errors[0] if errors else None,
        }


# --- capability proofs (D74) ---------------------------------------------------------


def synthetic_encode_command(encoder: str, pix_fmt: str, profile: str, output: Path) -> list[str]:
    """Return the FFmpeg command of a 2-second synthetic 1080p30 encode (a capability proof).

    Args:
        encoder: ``hevc_nvenc`` or ``libx265``.
        pix_fmt: The encoder input pixel format, for example ``p010le``.
        profile: The HEVC profile, ``main`` or ``main10``.
        output: The output file (already checked).

    Returns:
        The command.
    """
    return [
        "ffmpeg",
        "-nostdin",
        "-hide_banner",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "testsrc2=size=1920x1080:rate=30:duration=2",
        "-c:v",
        encoder,
        "-pix_fmt",
        pix_fmt,
        "-profile:v",
        profile,
        str(output),
    ]


def encode_proof(
    encoder: str, pix_fmt: str, profile: str, folder: Path, allowed: Path, footage: Path
) -> dict[str, Any]:
    """Encode the synthetic clip and confirm the result with ``ffprobe``.

    The proof holds when FFmpeg exits 0 and ``ffprobe`` reads an HEVC stream of 60
    frames with the expected profile and pixel format; for ``hevc_nvenc`` it also needs
    ``nvidia-smi`` to have named a GPU and counted at least one NVENC session during the
    encode.

    Args:
        encoder: ``hevc_nvenc`` or ``libx265``.
        pix_fmt: The encoder input pixel format.
        profile: ``main`` or ``main10``.
        folder: Where the proof clip is written (created if absent).
        allowed: The spike folder (output check).
        footage: The footage folder (output check).

    Returns:
        The proof record: command, exit status, elapsed seconds, the ``ffprobe``
        reading, the GPU samples and ``proven``.
    """
    output = check_output_path(folder / f"proof-{encoder}-{pix_fmt}.mp4", allowed, footage)
    output.parent.mkdir(parents=True, exist_ok=True)
    command = synthetic_encode_command(encoder, pix_fmt, profile, output)
    record: dict[str, Any] = {"command": command}
    started = time.monotonic()
    with gpu_samples(record):
        status, stderr = run_tool(command)
    record["elapsed_seconds"] = round(time.monotonic() - started, 2)
    record["exit_status"] = status
    expected_pix_fmt = {"p010le": "yuv420p10le"}.get(pix_fmt, pix_fmt)
    expected_profile = {"main": "Main", "main10": "Main 10"}[profile]
    if status != 0:
        record["stderr_tail"] = stderr.strip().splitlines()[-3:]
        record["proven"] = False
        return record
    data = run_ffprobe(
        [
            "-show_entries",
            "stream=codec_name,profile,pix_fmt,width,height,nb_frames:stream_tags=encoder",
            str(output),
        ]
    )
    stream = next((s for s in data.get("streams", []) if isinstance(s, dict)), {})
    record["ffprobe"] = stream
    gpu = record["gpu"]
    record["proven"] = (
        stream.get("codec_name") == "hevc"
        and stream.get("profile") == expected_profile
        and stream.get("pix_fmt") == expected_pix_fmt
        and str(stream.get("nb_frames")) == "60"
        and (
            encoder != "hevc_nvenc"
            or (bool(gpu["names"]) and (gpu["max_nvenc_sessions"] or 0) >= 1)
        )
    )
    return record


def hardware_decode_command(chapter: Path) -> list[str]:
    """Return the FFmpeg command that decodes a chapter's video on the GPU and discards it.

    ``-hwaccel_output_format cuda`` keeps the frames in GPU memory, so the run fails
    rather than falling back to the CPU decoder. The output is FFmpeg's null muxer:
    nothing is written.

    Args:
        chapter: The chapter (an input only).

    Returns:
        The command.
    """
    return [
        "ffmpeg",
        "-nostdin",
        "-hide_banner",
        "-v",
        "verbose",
        "-hwaccel",
        "cuda",
        "-hwaccel_output_format",
        "cuda",
        "-i",
        str(chapter),
        "-map",
        "0:v:0",
        "-f",
        "null",
        "-",
    ]


def hardware_decode_proof(chapter: Path) -> dict[str, Any]:
    """Decode one chapter with ``-hwaccel cuda`` and check every frame was decoded.

    The proof holds when FFmpeg exits 0, reports every container frame decoded with no
    error, its filter graph received ``cuda`` frames, and ``nvidia-smi`` named a GPU
    during the decode.

    Args:
        chapter: The chapter (an input only).

    Returns:
        The proof record: command, exit status, frames decoded and decode errors as
        FFmpeg reports them, the container's frame count, whether the filter graph saw
        ``cuda`` frames, the GPU samples and ``proven``.
    """
    command = hardware_decode_command(chapter)
    record: dict[str, Any] = {"command": command}
    started = time.monotonic()
    with gpu_samples(record):
        status, stderr = run_tool(command)
    record["elapsed_seconds"] = round(time.monotonic() - started, 2)
    record["exit_status"] = status
    decoded = _DECODED.search(stderr)
    record["frames_decoded"] = int(decoded.group(1)) if decoded else None
    record["decode_errors"] = int(decoded.group(2)) if decoded else None
    record["graph_input_pixfmt_cuda"] = "pixfmt:cuda" in stderr
    data = run_ffprobe(
        ["-select_streams", "v:0", "-show_entries", "stream=nb_frames", str(chapter)]
    )
    streams = [s for s in data.get("streams", []) if isinstance(s, dict)]
    nb_frames = streams[0].get("nb_frames") if streams else None
    record["container_nb_frames"] = nb_frames
    record["proven"] = (
        status == 0
        and record["decode_errors"] == 0
        and record["graph_input_pixfmt_cuda"]
        and str(record["frames_decoded"]) == str(nb_frames)
        and bool(record["gpu"]["names"])
    )
    return record


def capability_record(chapter: Path, folder: Path, allowed: Path, footage: Path) -> dict[str, Any]:
    """Build the full capability record: the listings and every proof (D74).

    Args:
        chapter: The real chapter for the hardware decode proof.
        folder: Where the proof clips are written.
        allowed: The spike folder (output check).
        footage: The footage folder (output check).

    Returns:
        ``listing``, ``encode_proofs`` (one per encoder and bit depth) and
        ``hardware_decode``.
    """
    proofs = []
    for encoder in ENCODERS:
        for (_, depth), (pix_fmt, profile) in _PIXEL_FORMATS[encoder].items():
            proof = encode_proof(encoder, pix_fmt, profile, folder, allowed, footage)
            proofs.append({"encoder": encoder, "bit_depth": depth, **proof})
    return {
        "listing": capability_listing(),
        "encode_proofs": proofs,
        "hardware_decode": {"chapter": chapter.name, **hardware_decode_proof(chapter)},
    }


# --- camera record (D54, D73) -------------------------------------------------------


def gpmf_settings(payload: bytes | None, keys: Sequence[str] = GPMF_SETTING_KEYS) -> dict[str, str]:
    """Read the named character-valued keys from a GPMF KLV payload (first occurrence).

    GPMF is a key-length-value stream: a four-character key, a type character (0 for a
    nested stream), a structure size, a big-endian repeat count, and the value padded to
    four bytes. Only the requested keys are read, so identifiers such as the camera's
    serial number never enter the record.

    Args:
        payload: The ``moov/udta/GPMF`` payload, or None.
        keys: The keys to read.

    Returns:
        ``{key: text}`` for each requested key found with a character type.
    """
    found: dict[str, str] = {}

    def walk(data: bytes) -> None:
        position = 0
        while position + 8 <= len(data):
            key = data[position : position + 4].decode("latin-1")
            kind = data[position + 4]
            length = data[position + 5] * int.from_bytes(data[position + 6 : position + 8], "big")
            value = data[position + 8 : position + 8 + length]
            if kind == 0:
                walk(value)
            elif kind == ord("c") and key in keys and key not in found:
                found[key] = value.split(b"\0", 1)[0].decode("latin-1").strip()
            position += 8 + (length + 3) // 4 * 4

    if payload:
        walk(payload)
    return found


def camera_record(chapter: Path) -> dict[str, Any]:
    """Record what the camera wrote in one chapter (read only).

    Args:
        chapter: The chapter.

    Returns:
        Codec, profile, pixel format, colour tags as written, frame rate and whether
        the decoded frames step evenly, start offsets, edit lists, orientation, audio,
        data streams, creation time, the ``moov/udta`` atom types and the GoPro
        settings that bear on D73.
    """
    facts = gather(chapter)
    movie = facts.movie
    streams = [s for s in facts.probe.get("streams", []) if isinstance(s, dict)]
    video = next((s for s in streams if s.get("index") == facts.video_index), {})
    chroma, depth = pix_fmt_shape(video.get("pix_fmt"))
    steps = sorted(
        {
            str(exact(b - a))
            for a, b in itertools.pairwise(facts.pts)
            if a is not None and b is not None
        }
    )
    track_by_id = {t.track_id: t for t in movie.tracks}

    def track_of(stream: Mapping[str, Any]) -> Any:
        try:
            return track_by_id.get(int(str(stream.get("id", "")), 16))
        except ValueError:
            return None

    settings = gpmf_settings(udta_atom(chapter, "GPMF"))
    transfer = video.get("color_transfer")
    creation_1904 = movie.creation_time
    return {
        "file": chapter.name,
        "size_bytes": chapter.stat().st_size,
        "codec": video.get("codec_name"),
        "codec_tag": video.get("codec_tag_string"),
        "profile": video.get("profile"),
        "pix_fmt": video.get("pix_fmt"),
        "chroma_subsampling": chroma,
        "bit_depth": depth,
        "width": video.get("width"),
        "height": video.get("height"),
        "colour": {
            "primaries": video.get("color_primaries"),
            "transfer": transfer,
            "matrix": video.get("color_space"),
            "range": video.get("color_range"),
            "chroma_location": video.get("chroma_location"),
        },
        "hdr_transfer_tag": transfer in _HDR_TRANSFERS,
        "r_frame_rate": video.get("r_frame_rate"),
        "avg_frame_rate": video.get("avg_frame_rate"),
        "frames_decoded": len(facts.pts),
        "nb_frames": video.get("nb_frames"),
        "pts_steps": steps,
        "constant_frame_rate": len(steps) == 1,
        "start": {
            "format_start_time": dict(facts.probe.get("format") or {}).get("start_time"),
            "first_frame_pts": exact(facts.pts[0]) if facts.pts else None,
            "stream_start_pts": {facts.keys[int(s["index"])]: s.get("start_pts") for s in streams},
        },
        "edit_lists": {
            facts.keys[int(s["index"])]: {
                "as_written": None
                if track.edits is None
                else [[e.segment_duration, e.media_time, str(e.rate)] for e in track.edits],
                "movie_timescale": movie.timescale,
                "media_timescale": track.media_timescale,
                "effect": edit_effect(movie, track),
            }
            for s in streams
            if (track := track_of(s)) is not None
        },
        "orientation": {
            "side_data": video.get("side_data_list"),
            "tkhd_matrix": list(track.matrix) if (track := track_of(video)) else None,
        },
        "audio": [
            {
                k: s.get(k)
                for k in ("codec_name", "profile", "sample_rate", "channels", "channel_layout")
            }
            for s in streams
            if s.get("codec_type") == "audio"
        ],
        "data_streams": [
            {
                "key": facts.keys[int(s["index"])],
                "codec_tag": s.get("codec_tag_string"),
                "handler_name": dict(s.get("tags") or {}).get("handler_name"),
                "packets": len(facts.packets.get(int(s["index"]), [])),
            }
            for s in streams
            if s.get("codec_type") == "data"
        ],
        "timecode": dict(video.get("tags") or {}).get("timecode"),
        "creation_time": {
            "container_tag": dict(dict(facts.probe.get("format") or {}).get("tags") or {}).get(
                "creation_time"
            ),
            "mvhd_seconds_since_1904": creation_1904,
            "mvhd_utc": (
                datetime.datetime(1904, 1, 1, tzinfo=datetime.UTC)
                + datetime.timedelta(seconds=creation_1904)
            ).isoformat(),
        },
        "udta_atoms": [[kind, size] for kind, size, _ in movie.udta],
        "gopro_settings": settings,
        "container_tags": dict(dict(facts.probe.get("format") or {}).get("tags") or {}),
    }


def sidecars(footage: Path) -> list[str]:
    """List the ``.LRV`` and ``.THM`` files in the footage folder (names only).

    Args:
        footage: The footage folder.

    Returns:
        The sorted file names (D60 alignment can only be tested when ``.LRV`` exists).
    """
    return sorted(
        p.name for p in footage.iterdir() if p.is_file() and p.suffix.lower() in (".lrv", ".thm")
    )


# --- the identity re-encode (D104) --------------------------------------------------


def output_name(source: Path) -> str:
    """Return the spec 8.3 output name: the source stem, ``_corrected``, the source suffix.

    Args:
        source: The source file.

    Returns:
        For example ``GX011627_corrected.MP4``.
    """
    return f"{source.stem}{OUTPUT_SUFFIX}{source.suffix}"


def reencode_command(
    source: Path, output: Path, probe: Mapping[str, Any], encoder: str
) -> list[str]:
    """Return the FFmpeg command of the identity re-encode (the simple approach).

    The first video stream is decoded and encoded again at the source's pixel format
    and bit depth with the source's colour tags (D55, D114); audio and every data
    stream except the timecode track are copied (the MP4 muxer cannot copy a ``tmcd``
    track, so it is written again from the ``timecode`` tag, ``-write_tmcd 1``);
    container and stream metadata are copied (``-map_metadata 0``). Timing:
    ``-copyts`` keeps the source timestamps (no shift to zero), ``-fps_mode
    passthrough`` neither drops nor duplicates a frame, ``-enc_time_base:v demux``
    encodes in the source's time base, and ``negative_cts_offsets`` lets the muxer
    store B-frame reordering as negative composition offsets instead of shifting the
    edit list. ``-noautorotate`` keeps a display matrix instead of rotating pixels.

    Args:
        source: The source file (an input only).
        output: The output file (already checked).
        probe: The source's ``ffprobe -show_format -show_streams`` document.
        encoder: ``hevc_nvenc`` or ``libx265``.

    Returns:
        The command.

    Raises:
        SpikeError: If the source has no video stream, or a pixel format the spike does
            not encode (anything but 8- or 10-bit 4:2:0 is out of its envelope).
    """
    streams = [s for s in probe.get("streams", []) if isinstance(s, dict)]
    video = next(
        (
            s
            for s in streams
            if s.get("codec_type") == "video"
            and not dict(s.get("disposition") or {}).get("attached_pic")
        ),
        None,
    )
    if video is None:
        raise SpikeError(f"{source.name}: no video stream")
    shape = pix_fmt_shape(video.get("pix_fmt"))
    target = _PIXEL_FORMATS[encoder].get((shape[0] or "", shape[1] or 0))
    if target is None:
        raise SpikeError(f"{source.name}: pixel format {video.get('pix_fmt')} is outside the spike")
    pix_fmt, profile = target
    colour = []
    for field, option in (
        ("color_primaries", "-color_primaries"),
        ("color_transfer", "-color_trc"),
        ("color_space", "-colorspace"),
        ("color_range", "-color_range"),
    ):
        value = video.get(field)
        if isinstance(value, str) and value not in ("", "unknown"):
            colour += [option, value]
    maps = ["-map", f"0:{video['index']}"]
    for stream in streams:
        if stream.get("codec_type") == "audio" or (
            stream.get("codec_type") == "data" and stream.get("codec_tag_string") != "tmcd"
        ):
            maps += ["-map", f"0:{stream['index']}"]
    return [
        "ffmpeg",
        "-nostdin",
        "-hide_banner",
        "-y",
        "-copyts",
        "-noautorotate",
        "-i",
        str(source),
        *maps,
        "-c:v",
        encoder,
        *ENCODER_SETTINGS[encoder],
        "-pix_fmt",
        pix_fmt,
        "-profile:v",
        profile,
        *colour,
        "-tag:v",
        "hvc1",
        "-fps_mode",
        "passthrough",
        "-enc_time_base:v",
        "demux",
        "-c:a",
        "copy",
        "-c:d",
        "copy",
        "-map_metadata",
        "0",
        "-write_tmcd",
        "1",
        "-movflags",
        "+negative_cts_offsets",
        str(output),
    ]


def identity_psnr(source: Path, output: Path) -> dict[str, Any]:
    """Measure the PSNR of the re-encode against the source over every frame.

    FFmpeg's ``psnr`` filter compares the two decoded videos frame by frame; the output
    is the null muxer, so nothing is written. A frame misalignment or a range or matrix
    error shows as a low figure.

    Args:
        source: The source file.
        output: The re-encoded file.

    Returns:
        ``{"y", "u", "v", "average", "min", "max"}`` in dB (strings as FFmpeg prints
        them), or ``{"error": ...}``.
    """
    command = [
        "ffmpeg",
        "-nostdin",
        "-hide_banner",
        "-i",
        str(source),
        "-i",
        str(output),
        "-lavfi",
        "[0:v:0][1:v:0]psnr",
        "-f",
        "null",
        "-",
    ]
    status, stderr = run_tool(command)
    match = _PSNR.search(stderr)
    if status != 0 or match is None:
        return {"command": command, "error": f"status {status}; no PSNR line"}
    return {
        "command": command,
        **dict(zip(("y", "u", "v", "average", "min", "max"), match.groups(), strict=True)),
    }


def reencode(
    source: Path, folder: Path, encoder: str, allowed: Path, footage: Path
) -> dict[str, Any]:
    """Run the identity re-encode, compare source and output, and write both records.

    Args:
        source: The source file (an input only).
        folder: Where the output and records are written.
        encoder: ``hevc_nvenc`` or ``libx265``.
        allowed: The spike folder (output check).
        footage: The footage folder (output check).

    Returns:
        The run record: command, exit status, elapsed seconds, GPU samples, the
        comparison summary, the PSNR and the paths written.

    Raises:
        SpikeError: If FFmpeg fails.
        OutputPathError: If an output path is refused.
        ProbeError: If a file cannot be probed.
    """
    check_output_path(folder, allowed, footage)
    output = check_output_path(folder / output_name(source), allowed, footage)
    run_path = folder / f"{output.stem}.run.json"
    # Every file this run writes is checked before FFmpeg starts (and again when written).
    for record_path in (
        run_path,
        folder / f"{output.stem}.compare.json",
        folder / f"{output.stem}.compare.md",
    ):
        check_output_path(record_path, allowed, footage)
    folder.mkdir(parents=True, exist_ok=True)
    probe = run_ffprobe(["-show_format", "-show_streams", str(source)])
    command = reencode_command(source, output, probe, encoder)
    run: dict[str, Any] = {"source": str(source), "output": str(output), "command": command}
    started = time.monotonic()
    with gpu_samples(run):
        status, stderr = run_tool(command)
    run["elapsed_seconds"] = round(time.monotonic() - started, 2)
    run["exit_status"] = status
    if status != 0:
        tail = " / ".join(stderr.strip().splitlines()[-3:])
        raise SpikeError(f"ffmpeg re-encode failed (status {status}): {tail}")
    source_facts, output_facts = gather(source), gather(output)
    record = build_record(source_facts, output_facts, compare_facts(source_facts, output_facts))
    json_path, md_path = write_record(record, folder, output.stem, allowed, footage)
    run["compare_json"] = str(json_path)
    run["compare_md"] = str(md_path)
    run["summary"] = record["summary"]
    run["psnr"] = identity_psnr(source, output)
    write_checked(json.dumps(run, indent=1) + "\n", run_path, allowed, footage)
    run["run_json"] = str(run_path)
    return run


# --- command line -------------------------------------------------------------------


def _chapter(footage: Path, name: str) -> Path:
    """Return a chapter path inside the footage folder, refusing anything else."""
    path = footage / name
    if Path(name).name != name or not path.is_file():
        raise SpikeError(f"no file named {name} in the footage folder")
    return path


def _write_json(data: Mapping[str, Any], path: Path, allowed: Path, footage: Path) -> Path:
    """Write ``data`` as JSON after checking the file's own resolved path."""
    return write_checked(json.dumps(data, indent=1) + "\n", path, allowed, footage)


def main(argv: list[str] | None = None) -> int:
    """Run one spike step (see the module docstring).

    Args:
        argv: Command-line arguments; defaults to ``sys.argv[1:]``.

    Returns:
        0 on success; 2 (with a one-line ``error: ...``) on failure.
    """
    parser = argparse.ArgumentParser(description="WP1.5 container spike.")
    parser.add_argument("--config", type=Path, help="local configuration file to read")
    steps = parser.add_subparsers(dest="step", required=True)
    capability = steps.add_parser("capability", help="encoder capability record (D74)")
    capability.add_argument(
        "--chapter", default="GX011627.MP4", help="chapter for the decode proof"
    )
    camera = steps.add_parser("camera", help="camera record (D54, D73)")
    camera.add_argument("names", nargs="*", help="chapters (default: every .MP4)")
    encode = steps.add_parser("reencode", help="identity re-encode and comparison (D104)")
    encode.add_argument("name", help="the chapter")
    encode.add_argument("--encoder", choices=ENCODERS, default="hevc_nvenc")
    args = parser.parse_args(argv)

    try:
        config = load_local_config(args.config)
        footage = config.footage_path
        allowed = config.working_path / SPIKE_SUBDIR
        check_output_path(allowed, allowed, footage)
        if not footage.is_dir():
            raise SpikeError(f"footage folder not found: {footage}")
        step: Callable[[], Path]
        if args.step == "capability":
            chapter = _chapter(footage, args.chapter)

            def step() -> Path:
                record = capability_record(chapter, allowed / "capability", allowed, footage)
                return _write_json(record, allowed / "capability.json", allowed, footage)

        elif args.step == "camera":
            names = args.names or sorted(
                p.name for p in footage.iterdir() if p.is_file() and p.suffix.lower() == ".mp4"
            )
            chapters = [_chapter(footage, name) for name in names]

            def step() -> Path:
                record = {
                    "chapters": [camera_record(c) for c in chapters],
                    "sidecars": sidecars(footage),
                }
                return _write_json(record, allowed / "camera.json", allowed, footage)

        else:
            source = _chapter(footage, args.name)

            def step() -> Path:
                run = reencode(source, allowed / "reencode", args.encoder, allowed, footage)
                summary = run["summary"]
                print(f"DIFFERENT by class: {summary['different']}")
                print(f"every {MANDATORY} item SAME: {summary['mandatory_all_same']}")
                print(f"PSNR: {run['psnr']}")
                return Path(run["run_json"])

        print(step())
    except (LocalConfigError, OutputPathError, ProbeError, SpikeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
