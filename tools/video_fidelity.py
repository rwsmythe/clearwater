"""The video fidelity instrument: a source against its Clearwater output, item by item (V4).

Usage::

    uv run python tools/video_fidelity.py compare SOURCE OUTPUT [--bit-depth N] [--out DIR]
    uv run python tools/video_fidelity.py encode SOURCE --encoder E [--quality Q]
        [--bit-depth N] [--out DIR]

``compare`` reads two files (both read only). ``encode`` first writes SOURCE through the
product sink (:class:`clearwater.io.video.FFmpegVideoSink`) with a test-side FFmpeg decode in
front (no correction), samples the graphics card while an NVENC encode runs, then compares.
Every record and output goes to the configured working folder (``wp3.10`` by default), never to
the footage folder.

The items are WP1.5's (``tools/container_spike/compare.py``, reused by import) with the
product's readings applied:

* colour tags are compared with the source's D54-resolved description, the raw source tag
  recorded beside it (round-0 ruling Q-E), and pixel format and bit depth with the selected
  output depth (D76);
* the video edit list "as written" follows AD-22: where it differs only by the
  composition-offset convention (each ``media_time`` equals its own track's earliest
  composition time) it is SAME with a note, and an absent source edit list against an identity
  output list is SAME with a NOTE (AD-22 extended, Q-C) -- never a silent pass: every such note
  is listed in the summary's ``notes``;
* the presentation-effect item models an absent edit list as the identity from media time 0;
* the movie duration (``mvhd`` over its timescale, the presentation form, WP3.7's note) is a
  MANDATORY item of its own; whole-file movie-level durations may read SAME for movie-tick
  rounding of the same exact track value (owner 2026-11-10, AD-22), with per-side figures;
* a cut-short source (D86) is compared on its readable part: the video ends at the readable end
  and, for a truncated file, each copied track at the end of its last packet before it. The
  expected video duration, the video edit list (its ``media_time`` and rate kept, AD-22's
  reading applied), the video and audio presentation effect, the movie duration and the copied
  packets are all taken from the source cut there;

and with the DR-18 points closed:

1. an NVENC encode is tied to the encode window, the GPU UUID and the FFmpeg PID by
   ``nvidia-smi pmon`` samples taken while it runs, every time on one monotonic clock
   (``encode`` only; the record says when no sample saw the encoder);
2. the AAC decoder configuration (profile, initial padding, extradata size and MD5), the
   priming (discard-flagged packets) and every packet's side data are compared, MANDATORY;
3. a roster invariant: every expected item must be present, else a MANDATORY ``item roster``
   item is DIFFERENT and the summary fails;
4. decoded frames with no pts are counted in both files (MANDATORY, both must be zero).

The telemetry data track is compared packet for packet in memory (pts, duration, size and the
payload MD5 that ffprobe computes); the record keeps only its packet counts and the status, no
payload, digest or decoded value. Every location-like tag value (and the digest of a
location-like ``udta`` atom) is replaced by :data:`LOCATION_WITHHELD` as soon as the file's facts
are read, before any comparison, so only its presence is compared and no location value reaches
an item or a record.

Exit status 0 when the comparison ran; 1 when an encode failed; 2 on a usage, configuration,
probe or output-path error.

Windows / NVIDIA evidence; not a Mac instrument (WP6.4, audit row T36): its NVENC proof uses
nvidia-smi pmon, which proves nothing about VideoToolbox; the VT V4 evidence is WP6.5's.
"""

from __future__ import annotations

import argparse
import hashlib
import struct
import subprocess
import sys
import threading
import time
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field, replace
from fractions import Fraction
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from clearwater.color import decode_filter, ffmpeg_color_names, planes_to_rgb, rgb_frame_bytes
from clearwater.interfaces.image import Frame
from clearwater.interfaces.video import ProbeResult, SinkReport
from clearwater.io.video import FFmpegVideoSink, VideoEncodeError, VideoProbeError, probe
from clearwater.io.video.verify import read_packet_table, readable_end
from container_spike import compare
from local_config import LocalConfigError, load_local_config

SUBDIR = "wp3.10"
"""The default record folder under the working folder."""

TELEMETRY_ITEM = "GPMF track gpmd"
"""The start of the WP1.5 item name for the telemetry data track (its values are redacted)."""

VIDEO_EDIT_AS_WRITTEN = "edit list, video track, as written (media_time in media seconds)"
EDIT_EFFECT = "edit list, video and audio tracks (presentation effect)"
VIDEO_DURATION = "video stream duration"
MOVIE_DURATION = "movie duration: mvhd (presentation form, exact)"
AUDIO_PACKETS = "audio packets passed through (pts, duration, size, MD5)"
COLOUR_ITEMS = {
    "colour primaries": "color_primaries",
    "colour transfer": "color_trc",
    "colour matrix": "colorspace",
    "colour range": "color_range",
}
"""The WP1.5 colour items and the :func:`ffmpeg_color_names` key each is compared with."""

ROSTER = (
    "video frame count",
    "video per-frame pts (presentation, exact, full sequence)",
    VIDEO_DURATION,
    MOVIE_DURATION,
    "start offset: first video frame pts",
    "start offset: video and audio stream start_pts",
    "start offset: container start over video and audio (earliest start, exact)",
    "start offset: container start_time (ffprobe format, as printed)",
    VIDEO_EDIT_AS_WRITTEN,
    EDIT_EFFECT,
    "audio streams present",
    AUDIO_PACKETS,
    "audio sync: first audio pts minus first video pts",
    "display orientation: display matrix (ffprobe side data)",
    "display orientation: video tkhd matrix",
    "output video codec (8.2 requires HEVC)",
    "output container (8.2 requires MP4)",
    *COLOUR_ITEMS,
    "pixel format (decoded)",
    "chroma subsampling",
    "bit depth",
    "frame size and sample aspect ratio",
    "creation time: container tag",
    "creation time: mvhd (seconds since 1904)",
    "creation time: per-stream tags",
    TELEMETRY_ITEM + " (pts, duration, size, MD5)",
    "timecode track tmcd (pts, duration, size, MD5)",
    "timecode value (stream tags)",
    "camera atoms: moov/udta children (type, bytes, MD5)",
    "ftyp brands",
    "container tags other than creation_time",
    "stream tags other than creation_time and timecode",
    "chroma location",
    "track layout (key:sample entry:tkhd flags)",
    "video sample entry child boxes",
    "edit lists as written, non-video tracks (media_time in media seconds)",
    "edit list, data tracks (presentation effect)",
    "start offset: container start over all tracks (earliest start, exact)",
    "container duration (ffprobe, 1 us)",
    "audio decoder configuration (profile, initial padding, extradata)",
    "audio priming and packet side data",
    "video frames with no pts (decoded)",
)
"""Every item a record must hold (keyed items by their name before `` [key]``), DR-18 (3)."""

_ROSTER_ITEM = "item roster (every expected item present, DR-18 (3))"
_PMON_PERIOD_S = 0.5

LOCATION_WITHHELD = "(present; a location value, not read)"
"""What a location-like tag value or atom digest is replaced with: only its presence compares."""

_LOCATION_WORDS = ("location", "iso6709", "gps", "coordinate", "latitude", "longitude", "loci")
"""Fragments of a tag key or atom type that can carry a location (ISO 6709 text, GPS)."""

_clock = time.monotonic
"""The one clock of the encode window and the graphics-card samples (DR-18 (1))."""

Entry = tuple[Fraction, Fraction | None, Fraction]
"""One edit-list entry: duration in movie seconds, media time in media seconds (None for an
empty edit), rate."""


# --- decode and encode ---------------------------------------------------------------------


def decode_frames(source: Path, info: ProbeResult) -> Iterator[Frame]:
    """Decode a source test-side with FFmpeg and yield its frames with their exact pts.

    The pts come from ``ffprobe``'s decoded frame list, in presentation order; the pixels from
    one streamed FFmpeg decode through :func:`clearwater.color.decode_filter` (no frame is held
    longer than it is yielded). This stands in for WP3.9's decoder in tests and tools.

    Args:
        source: The source file (read only).
        info: Its probe result.

    Yields:
        Frames on the CPU, float32 RGB.

    Raises:
        RuntimeError: When the decode delivers a frame count other than the pts list's.
    """
    video = info.video
    listing = compare.run_ffprobe(
        ["-select_streams", "v:0", "-show_entries", "frame=pts", str(source)]
    )
    pts = [
        int(frame["pts"])
        for frame in listing.get("frames", [])
        if isinstance(frame, dict) and isinstance(frame.get("pts"), int)
    ]
    command = ["ffmpeg", "-nostdin", "-v", "error", "-noautorotate", "-i", str(source)]
    command += ["-map", "0:v:0", "-vf", decode_filter(video), "-fps_mode", "passthrough"]
    command += ["-f", "rawvideo", "pipe:1"]
    size = rgb_frame_bytes(video.width, video.height, video.bit_depth)
    process = subprocess.Popen(
        command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, env=compare.tool_env()
    )
    stdout = process.stdout
    assert stdout is not None
    count = 0
    try:
        for number, ticks in enumerate(pts):
            data = stdout.read(size)
            if len(data) < size:
                break
            pixels = planes_to_rgb(
                data, width=video.width, height=video.height, bit_depth=video.bit_depth
            )
            count += 1
            yield Frame(
                pixels=pixels,
                device="cpu",
                color=video.color,
                orientation_applied=False,
                pts=ticks * video.time_base,
                pts_ticks=ticks,
                time_base=video.time_base,
                index=number,
            )
        extra = stdout.read(size)
    finally:
        stdout.close()
        if process.poll() is None:
            process.kill()
        process.wait()
    if count != len(pts) or extra:
        raise RuntimeError(f"the decode gave {count} frames for {len(pts)} pts")


@dataclass
class GpuSamples:
    """``nvidia-smi`` samples taken while an encode runs (DR-18 (1)).

    Attributes:
        gpus: ``index -> UUID`` of every graphics card ``nvidia-smi`` lists.
        rows: ``(call start, call end, gpu index, pid, enc %)`` per sampled process, the times
            on :data:`_clock` (the clock of the encode window): the sample describes the
            interval its ``nvidia-smi`` call ran in.
        error: Why sampling did not run, or None.
    """

    gpus: dict[str, str] = field(default_factory=dict)
    rows: list[tuple[float, float, str, int, str]] = field(default_factory=list)
    error: str | None = None


def _nvidia_smi(arguments: Sequence[str]) -> str | None:
    """Run ``nvidia-smi`` and return its output, or None when it cannot run."""
    try:
        done = subprocess.run(
            ["nvidia-smi", *arguments],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if done.returncode != 0:
        return None
    return done.stdout.decode("utf-8", errors="replace")


class _Sampler:
    """Samples ``nvidia-smi pmon`` in a thread from :meth:`start` to :meth:`stop`."""

    def __init__(self) -> None:
        self.samples = GpuSamples()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        listing = _nvidia_smi(["--query-gpu=index,uuid", "--format=csv,noheader"])
        if listing is None:
            self.samples.error = "nvidia-smi is not available"
            return
        for line in listing.splitlines():
            index, _, uuid = line.partition(",")
            if uuid.strip():
                self.samples.gpus[index.strip()] = uuid.strip()
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.is_set():
            called = _clock()
            text = _nvidia_smi(["pmon", "-c", "1", "-s", "u"])
            returned = _clock()
            for line in (text or "").splitlines():
                parts = line.split()
                if len(parts) >= 6 and not line.startswith("#") and parts[1].isdigit():
                    row = (called, returned, parts[0], int(parts[1]), parts[5])
                    self.samples.rows.append(row)
            self._stop.wait(_PMON_PERIOD_S)

    def stop(self) -> GpuSamples:
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join(timeout=30)
        return self.samples


class _RecordingSink(FFmpegVideoSink):
    """The product sink, recording the FFmpeg process id and the encode window."""

    def __init__(self) -> None:
        super().__init__()
        self.pid: int | None = None
        self.started = 0.0
        self.ended = 0.0

    def _start(self, command: list[str]) -> None:
        self.started = _clock()
        super()._start(command)
        process = self._process
        self.pid = process.pid if process is not None else None

    def _end_stream(self) -> int:
        end = super()._end_stream()
        self.ended = _clock()  # FFmpeg's exit seen: the window closes before verification
        return end


@dataclass
class EncodeRun:
    """What :func:`encode_file` did.

    Attributes:
        report: The sink's report.
        encoder: The encoder used.
        bit_depth: The output bit depth.
        pid: The FFmpeg process id.
        started: Start of the encode window (FFmpeg about to start), on :data:`_clock`.
        ended: End of the window, on the same clock: when the sink saw FFmpeg exit, before the
            output is verified (round-4 #2); after a failure before that, when the sink failed.
        gpu: The graphics-card samples taken during the window (NVENC only), or None.
    """

    report: SinkReport
    encoder: str
    bit_depth: int
    pid: int | None
    started: float
    ended: float
    gpu: GpuSamples | None


def encode_file(
    source: Path,
    output: Path,
    *,
    encoder: str,
    quality: str = "standard",
    bit_depth: int | None = None,
    provenance: Mapping[str, Any] | None = None,
) -> EncodeRun:
    """Write ``source`` through the product sink with no correction (a decode-encode loop).

    Args:
        source: The source file (read only).
        output: The output file; created empty first, as the caller's ``SafeWrite`` would.
        encoder: ``"hevc_nvenc"`` or ``"libx265"``.
        quality: The quality level.
        bit_depth: The output bit depth; the source's when None.
        provenance: The provenance to embed, or None.

    Returns:
        The run record.
    """
    info = probe(source)
    depth = bit_depth if bit_depth is not None else info.video.bit_depth
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(b"")
    sink = _RecordingSink()
    sampler = _Sampler() if encoder == "hevc_nvenc" else None
    if sampler is not None:
        sampler.start()
    try:
        sink.open(
            info, output, encoder=encoder, quality=quality, bit_depth=depth, provenance=provenance
        )
        for frame in decode_frames(source, info):
            sink.write(frame)
        report = sink.close()
    except BaseException:
        sink.abort()
        raise
    finally:
        if not sink.ended:  # FFmpeg's exit was not seen: the encode failed first
            sink.ended = _clock()
        samples = sampler.stop() if sampler is not None else None
    return EncodeRun(report, encoder, depth, sink.pid, sink.started, sink.ended, samples)


def nvenc_proof(run: EncodeRun) -> dict[str, Any]:
    """Summarise the DR-18 (1) proof: the FFmpeg PID seen encoding on a named GPU in the window.

    Args:
        run: An encode run.

    Returns:
        ``tied`` True when at least one sample whose ``nvidia-smi`` call overlaps the window
        shows the FFmpeg PID with a non-zero encoder load on a GPU whose UUID is resolved,
        with the GPU UUID, the PID and the matching samples (their times in seconds from the
        window's start); otherwise ``tied`` False and the reason (no matching sample, or no
        UUID for the GPU the matching samples name).
    """
    if run.encoder != "hevc_nvenc":
        return {"tied": False, "reason": f"not an NVENC encode ({run.encoder})"}
    gpu = run.gpu
    if gpu is None or gpu.error is not None:
        return {"tied": False, "reason": gpu.error if gpu is not None else "not sampled"}
    hits = [
        row
        for row in gpu.rows
        if row[3] == run.pid
        and row[4] not in ("-", "0")
        and row[0] <= run.ended
        and row[1] >= run.started
    ]
    proof: dict[str, Any] = {
        "pid": run.pid,
        "window_s": round(run.ended - run.started, 2),
        "samples": len(gpu.rows),
        "pid_samples_with_encoder_load": [
            [round(called - run.started, 2), round(returned - run.started, 2), index, pid, load]
            for called, returned, index, pid, load in hits
        ],
        "gpu_uuid": sorted({gpu.gpus[row[2]] for row in hits if gpu.gpus.get(row[2])}),
    }
    proof["tied"] = bool(proof["gpu_uuid"])  # DR-18 (1) closes only on a named GPU
    if not hits:
        proof["reason"] = "no sample in the window showed the FFmpeg PID with encoder load"
    elif not proof["tied"]:
        indexes = ", ".join(sorted({row[2] for row in hits}))
        proof["reason"] = (
            f"the samples showing the FFmpeg PID name GPU index {indexes}, which nvidia-smi "
            "resolved to no UUID"
        )
    return proof


# --- facts ---------------------------------------------------------------------------------


def _top_level_tolerant(path: Path) -> tuple[list[str], bytes, bytes]:
    """Return the top-level box types, ``ftyp`` payload and ``moov`` box of a cut-short file.

    The walk stops at a box the end of the file cuts short (the media data of a truncated file).
    """
    top: list[str] = []
    ftyp, moov = b"", b""
    with path.open("rb") as handle:
        total = handle.seek(0, 2)
        position = 0
        while position + 8 <= total:
            handle.seek(position)
            head = handle.read(16)
            size, kind = int.from_bytes(head[:4], "big"), head[4:8].decode("latin-1")
            header = 8
            if size == 1:
                size, header = int.from_bytes(head[8:16], "big"), 16
            top.append(kind)
            if size < header or position + size > total:
                break
            if kind in ("ftyp", "moov"):
                handle.seek(position)
                payload = handle.read(size)
                ftyp, moov = (payload[header:], moov) if kind == "ftyp" else (ftyp, payload)
            position += size
    if not moov:
        raise compare.ProbeError(f"no readable moov box in {path}")
    return top, ftyp, moov


def _movie_tolerant(path: Path) -> compare.Movie:
    """Read the movie boxes as WP1.5's reader does, tolerating a cut-short media data box."""
    try:
        return compare.read_movie(path)
    except compare.ProbeError:
        top, ftyp, moov = _top_level_tolerant(path)
    head = compare._moov_header_size(moov)
    mvhd = compare._child(moov, head, len(moov), "mvhd")
    if mvhd is None:
        raise compare.ProbeError("moov without mvhd")
    layout = ">QQI" if moov[mvhd[0]] == 1 else ">III"
    creation, _, timescale = struct.unpack_from(layout, moov, mvhd[0] + 4)
    tracks = tuple(
        compare._track(moov, start, stop)
        for kind, start, stop in compare._children(moov, head, len(moov))
        if kind == "trak"
    )
    udta_span = compare._child(moov, head, len(moov), "udta")
    udta = (
        tuple(
            (kind, stop - start, hashlib.md5(moov[start:stop]).hexdigest())
            for kind, start, stop in compare._children(moov, udta_span[0], udta_span[1])
        )
        if udta_span is not None
        else ()
    )
    return compare.Movie(
        top_level=tuple(top),
        major_brand=ftyp[:4].decode("latin-1"),
        compatible_brands=tuple(
            ftyp[i : i + 4].decode("latin-1") for i in range(8, len(ftyp) - 3, 4)
        ),
        timescale=timescale,
        creation_time=creation,
        tracks=tracks,
        udta=udta,
    )


def location_like(key: str) -> bool:
    """Return whether a tag key or ``udta`` atom type can carry a location.

    Args:
        key: For example ``"location"``, ``"com.apple.quicktime.location.ISO6709"`` or the
            QuickTime ``udta`` atom type of a copyright sign then ``xyz``.

    Returns:
        True for a key that names a location, GPS coordinates or the QuickTime ``xyz`` atom.
    """
    name = key.lower()
    return any(word in name for word in _LOCATION_WORDS) or name.endswith("xyz")


def _withheld_tags(tags: Any) -> Any:
    """Return a tag mapping with every location-like value replaced (presence only)."""
    if not isinstance(tags, Mapping):
        return tags
    return {k: LOCATION_WITHHELD if location_like(str(k)) else v for k, v in tags.items()}


def without_locations(facts: compare.Facts) -> compare.Facts:
    """Return the facts with every location value replaced by :data:`LOCATION_WITHHELD`.

    The container and stream tags of the ``ffprobe`` document and the digest of each
    location-like ``moov/udta`` atom are replaced, so only their presence is compared and no
    location value reaches an item or a record.

    Args:
        facts: The facts as read.

    Returns:
        A copy with the values replaced; the input is not changed.
    """
    document = dict(facts.probe)
    if isinstance(document.get("format"), Mapping):
        container = dict(document["format"])
        if "tags" in container:
            container["tags"] = _withheld_tags(container["tags"])
        document["format"] = container
    document["streams"] = [
        {**s, "tags": _withheld_tags(s["tags"])} if isinstance(s, Mapping) and "tags" in s else s
        for s in document.get("streams") or []
    ]
    udta = tuple(
        (kind, size, LOCATION_WITHHELD if location_like(kind) else digest)
        for kind, size, digest in facts.movie.udta
    )
    return replace(facts, probe=document, movie=replace(facts.movie, udta=udta))


def movie_duration(path: Path) -> Fraction:
    """Return the movie duration, ``mvhd`` duration over its timescale, exact (presentation form).

    Args:
        path: The file (read only); a cut-short file is read as far as its ``moov`` allows.

    Returns:
        The duration in seconds.

    Raises:
        compare.ProbeError: When there is no readable ``moov``, no ``mvhd`` or a zero timescale.
    """
    try:
        _, _, moov = compare._top_level(path)
    except compare.ProbeError:
        _, _, moov = _top_level_tolerant(path)
    head = compare._moov_header_size(moov)
    span = compare._child(moov, head, len(moov), "mvhd")
    if span is None:
        raise compare.ProbeError(f"moov without mvhd in {path}")
    layout = ">QQIQ" if moov[span[0]] == 1 else ">IIII"  # version 1: 64-bit times and duration
    _, _, timescale, duration = struct.unpack_from(layout, moov, span[0] + 4)
    if timescale == 0:
        raise compare.ProbeError(f"mvhd timescale 0 in {path}")
    return Fraction(duration, timescale)


def gather(path: Path) -> compare.Facts:
    """Read every fact the comparison needs from one file, a cut-short one included.

    WP1.5's reader refuses a cut-short file (round-0 P5); this one reads it as far as its
    ``moov`` allows. Location values are withheld before the facts are returned
    (:func:`without_locations`).

    Args:
        path: The file (read only).

    Returns:
        The facts.
    """
    return without_locations(_gather(path))


def _gather(path: Path) -> compare.Facts:
    """Read the facts of one file as they are (see :func:`gather`)."""
    try:
        return compare.gather(path)
    except compare.ProbeError:
        pass
    movie = _movie_tolerant(path)
    document = compare.run_ffprobe(["-show_format", "-show_streams", str(path)])
    streams = [s for s in document.get("streams", []) if isinstance(s, dict)]
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    video_index = int(video["index"]) if video is not None else None
    pts = (
        []
        if video is None
        else compare.video_pts(path, int(video["index"]), compare._time_base(video))
    )
    packets = {
        int(s["index"]): compare.stream_packets(path, int(s["index"]), compare._time_base(s))
        for s in streams
        if s.get("codec_type") in ("audio", "data")
    }
    return compare.Facts(
        path=path,
        probe=document,
        movie=movie,
        video_index=video_index,
        pts=pts,
        packets=packets,
        keys=compare._stream_keys(streams, movie),
    )


def audio_configuration(facts: compare.Facts) -> dict[str, Any]:
    """Return each audio stream's decoder configuration: profile, padding, extradata (DR-18 2)."""
    document = compare.run_ffprobe(
        [
            "-select_streams",
            "a",
            "-show_entries",
            "stream=index,profile,initial_padding,extradata_size,extradata_hash",
            "-show_data_hash",
            "MD5",
            str(facts.path),
        ]
    )
    result = {}
    for stream in document.get("streams", []):
        if isinstance(stream, dict) and "index" in stream:
            key = facts.keys.get(int(stream["index"]), str(stream["index"]))
            result[key] = {
                k: stream.get(k)
                for k in ("profile", "initial_padding", "extradata_size", "extradata_hash")
            }
    return result


def audio_side_data(facts: compare.Facts) -> dict[str, list[Any]]:
    """Return each audio stream's packets as ``[pts, discard flag, side data]`` (DR-18 2).

    The discard-flagged packets are the encoder priming; the side data carries the skip-samples
    values a decoder applies.
    """
    result: dict[str, list[Any]] = {}
    for stream in compare._streams_of(facts, "audio"):
        index = int(stream["index"])
        document = compare.run_ffprobe(
            [
                "-select_streams",
                str(index),
                "-show_entries",
                "packet=pts,flags:packet_side_data",
                str(facts.path),
            ]
        )
        rows = []
        for packet in document.get("packets", []):
            if not isinstance(packet, dict):
                continue
            side = [
                {k: v for k, v in entry.items() if k != "side_data_size"}
                for entry in packet.get("side_data_list") or []
                if isinstance(entry, dict) and entry
            ]
            rows.append([packet.get("pts"), "D" in str(packet.get("flags", "")), side])
        result[facts.keys[index]] = rows
    return result


# --- the product readings ------------------------------------------------------------------


def _earliest_seconds(track: compare.Track) -> Fraction:
    """Return a track's earliest composition time in seconds (0 for a track with no samples)."""
    return Fraction(track.earliest_composition or 0, track.media_timescale)


def _written_entries(movie: compare.Movie, track: compare.Track) -> list[Entry] | None:
    """Return a track's edit list as written, in seconds, or None when it has none."""
    if track.edits is None:
        return None
    return [
        (
            Fraction(e.segment_duration, movie.timescale),
            None if e.media_time == -1 else Fraction(e.media_time, track.media_timescale),
            Fraction(e.rate),
        )
        for e in track.edits
    ]


def _effect_entries(movie: compare.Movie, track: compare.Track) -> list[Entry]:
    """Return a track's edit list by presentation effect; absent = identity from media time 0.

    Each media time is taken relative to the track's earliest composition time (WP1.5's
    ``edit_effect``). An absent edit list presents media time ``t`` at movie time ``t`` (AD-22
    extended): with an earliest composition time ``C`` above 0, an empty dwell of ``C`` and then
    the whole media from ``C``.
    """
    earliest = _earliest_seconds(track)
    written = _written_entries(movie, track)
    if written is not None:
        return [(d, None if m is None else m - earliest, r) for d, m, r in written]
    media = Fraction(track.media_duration, track.media_timescale)
    rows: list[Entry] = [(earliest, None, Fraction(1))] if earliest > 0 else []
    return [*rows, (media, Fraction(0), Fraction(1))]


def _render(entries: Sequence[Entry], key: str) -> list[dict[str, Any]]:
    """Render entries as WP1.5's items do (exact seconds; ``key`` names the media time)."""
    return [
        {
            "duration": compare.exact(d),
            key: "empty" if m is None else compare.exact(m),
            "rate": str(r),
        }
        for d, m, r in entries
    ]


def _cut(entries: Sequence[Entry], end: Fraction) -> list[Entry] | None:
    """Return a presentation that stops at ``end`` (seconds), or None when it cannot be cut.

    Cut: empty edits, then ONE media entry at rate 1 (the forms the sink reproduces), whose
    duration becomes the time from its presentation start to ``end``, never longer than it was.
    """
    if not entries or entries[-1][1] is None or any(m is not None for _, m, _ in entries[:-1]):
        return None
    if any(r != 1 for _, _, r in entries):
        return None
    start = sum((d for d, _, _ in entries[:-1]), Fraction(0))
    duration, media, rate = entries[-1]
    if end <= start:
        return None
    return [*entries[:-1], (min(duration, end - start), media, rate)]


def effect(movie: compare.Movie, track: compare.Track) -> list[dict[str, Any]]:
    """Render a track's edit list by its presentation effect; absent = identity from media 0.

    An absent edit list presents media time ``t`` at movie time ``t`` (AD-22 extended): when
    the earliest composition time ``C`` is above 0, that is an empty dwell of ``C`` followed by
    the whole media from ``C``. Present edit lists are rendered as WP1.5's ``edit_effect``
    (media start relative to the earliest composition time).

    Args:
        movie: The movie, for its timescale.
        track: The track.

    Returns:
        One dict per entry, as :func:`compare.edit_effect`.
    """
    return _render(_effect_entries(movie, track), "media_start")


def _video_track(facts: compare.Facts) -> compare.Track | None:
    """Return the video track of a file's facts."""
    return compare._track_of(facts, facts.video_index)


def _movie_tick_reading(
    source: compare.Facts,
    output: compare.Facts,
    item: compare.Item,
    *,
    movie_values: tuple[Fraction, Fraction] | None = None,
) -> tuple[compare.Item, str | None]:
    """Read whole-file movie-level rounding of equal exact track values (AD-22).

    A final rate-1 media edit has exact value V = (mdhd duration - media_time) /
    mdhd timescale. Its written D must satisfy abs(D - V) < 1 / movie timescale
    on each side; directions of rounding are independent. Earlier media entries
    and empty edits stay exact. For mvhd, V is the longest exact presentation
    across ALL movie tracks, with empty edits counted by their written duration.
    Both sides must have the same tracks. D86 cut-short paths never call this
    helper and are unchanged. At least one duration must actually be rounded
    (D != V); the existing AD-22 reading takes precedence in ``fidelity_items``.
    """
    if item.status == compare.SAME:
        return item, None
    is_movie = item.name == MOVIE_DURATION
    handlers = {
        VIDEO_EDIT_AS_WRITTEN: ("vide",),
        EDIT_EFFECT: ("vide", "soun"),
        "edit lists as written, non-video tracks (media_time in media seconds)": (
            "soun",
            "tmcd",
            "meta",
            "text",
            "subt",
        ),
    }
    if not is_movie and item.name not in handlers:
        return item, None
    canonical: list[Any] = []
    figures: list[str] = []
    rounded = False
    track_sets: list[set[str]] = []
    conventional_keys: list[set[str]] = []
    for side, (label, facts, written) in enumerate(
        (("source", source, item.source), ("output", output, item.output))
    ):
        movie = facts.movie
        if movie.timescale <= 0:
            return item, None
        tick = Fraction(1, movie.timescale)
        selected: dict[str, compare.Track] = {}
        if is_movie:
            counts: dict[str, int] = {}
            for track in movie.tracks:
                occurrence = counts.get(track.handler, 0)
                selected[f"{track.handler}#{occurrence}"] = track
                counts[track.handler] = occurrence + 1
        else:
            for index, key in facts.keys.items():
                keyed_track = compare._track_of(facts, index)
                if keyed_track is not None and keyed_track.handler in handlers[item.name]:
                    selected[key] = keyed_track
            if set(selected) != set(written):
                return item, None
        track_sets.append(set(selected))
        conventional: set[str] = set()
        normalized: dict[str, Any] = {}
        presentations: list[Fraction] = []
        for key, track in selected.items():
            if track.media_timescale <= 0:
                return item, None
            entries = (
                _effect_entries(movie, track)
                if is_movie or item.name == EDIT_EFFECT
                else _written_entries(movie, track)
            )
            if entries is None:
                normalized[key] = None
                continue
            if any(rate != 1 for _, _, rate in entries):
                return item, None
            rows = list(entries)
            tail_value = None
            for position, (duration, media, rate) in enumerate(entries):
                if media is None:
                    continue  # An empty edit counts by its segment duration, exactly.
                if position != len(entries) - 1:
                    if is_movie:
                        return item, None
                    continue  # A mid-list segment is never a rounding of the media end.
                media_time = track.edits[-1].media_time if track.edits else 0
                value = Fraction(track.media_duration - media_time, track.media_timescale)
                if track.edits is None:
                    value = duration  # The existing implicit identity presentation.
                if media_time < 0 or value < 0 or abs(duration - value) >= tick:
                    if is_movie:
                        return item, None
                    continue  # A trimmed tail keeps its exact written duration.
                tail_value = value
                rounded = rounded or duration != value
                rows[position] = (value, media, rate)
                figures.append(
                    f"{label} {key} entry {position}: D={duration}, V={value}, tick={tick}"
                )
            if item.name == VIDEO_EDIT_AS_WRITTEN:
                media_entries = [m for _, m, _ in rows if m is not None]
                if media_entries == [_earliest_seconds(track)]:
                    conventional.add(key)
            normalized[key] = (rows, tail_value)
            presentations.append(sum((d for d, _, _ in rows), Fraction(0)))
        if is_movie:
            longest = max(presentations, default=None)
            if longest is None or movie_values is None or abs(movie_values[side] - longest) >= tick:
                return item, None
            canonical.append(longest)
            rounded = rounded or movie_values[side] != longest
            figures.append(f"{label} mvhd: D={movie_values[side]}, V={longest}, tick={tick}")
        else:
            canonical.append(normalized)
        conventional_keys.append(conventional)
    composition_notes: list[str] = []
    if item.name == VIDEO_EDIT_AS_WRITTEN:
        # AD-22 permits differing offsets only when BOTH sides use the convention.
        for key in conventional_keys[0] & conventional_keys[1]:
            source_at = next(m for _, m, _ in canonical[0][key][0] if m is not None)
            output_at = next(m for _, m, _ in canonical[1][key][0] if m is not None)
            if source_at != output_at:
                composition_notes.append(
                    "AD-22: the media_time differs only by the composition-offset convention "
                    f"(source {compare.exact(source_at)}, output {compare.exact(output_at)}, "
                    "each its track's earliest composition time)"
                )
            for normalized in canonical:
                rows, tail_value = normalized[key]
                normalized[key] = (
                    [(d, None if m is None else Fraction(0), r) for d, m, r in rows],
                    tail_value,
                )
    if not rounded or not figures or track_sets[0] != track_sets[1] or canonical[0] != canonical[1]:
        return item, None
    note = "movie-tick rounding of the exact track value (owner 2026-11-10, AD-22); " + "; ".join(
        (*figures, *composition_notes)
    )
    return replace(item, status=compare.SAME, note=note), note


def video_edit_reading(
    source: compare.Facts,
    output: compare.Facts,
    item: compare.Item,
    *,
    end: Fraction | None = None,
) -> tuple[compare.Item, str | None]:
    """Apply AD-22 (and its Q-C extension) to the video edit list "as written" item.

    AD-22 reads a DIFFERENT "as written" item as SAME only where the media times differ by the
    composition-offset convention alone: the same entries (durations, empty or media, rate 1),
    one media entry each, and each media time equal to its own track's earliest composition
    time. An absent source list (Q-C) is SAME when the output's list is conventional and the
    presentation effect is the same. For a cut-short source the source's list is first cut at
    the readable end ``end``. For whole files, ``fidelity_items`` applies the
    owner's movie-tick reading only after this reading; D86 paths are unchanged.

    Args:
        source: The source's facts.
        output: The output's facts.
        item: The "as written" item (WP1.5's, or the cut-short one).
        end: The readable video end in seconds for a cut-short source, else None.

    Returns:
        The item (SAME with a note where AD-22 reads it so) and the note for the summary, or
        None when no reading applied.
    """
    if item.status == compare.SAME:
        return item, None
    src, out = _video_track(source), _video_track(output)
    if src is None or out is None:
        return item, None
    out_entries = _written_entries(output.movie, out)
    if out_entries is None or any(r != 1 for _, _, r in out_entries):
        return item, None
    out_media = [m for _, m, _ in out_entries if m is not None]
    if len(out_media) != 1:
        return item, None
    out_conventional = out_media[0] == _earliest_seconds(out)
    src_entries = _written_entries(source.movie, src)
    if src_entries is None:
        src_effect: list[Entry] | None = _effect_entries(source.movie, src)
        if end is not None and src_effect is not None:
            src_effect = _cut(src_effect, end)
        if out_conventional and src_effect == _effect_entries(output.movie, out):
            note = (
                "AD-22 extended (Q-C): the source has no edit list (identity from media time 0); "
                "the output writes the identity list explicitly -- same presentation"
            )
            return replace(item, status=compare.SAME, note=note), note
        return item, None
    if end is not None:
        cut = _cut(src_entries, end)
        if cut is None:
            return item, None
        src_entries = cut
    if any(r != 1 for _, _, r in src_entries):
        return item, None
    src_media = [m for _, m, _ in src_entries if m is not None]
    same_shape = [(d, m is None) for d, m, _ in src_entries] == [
        (d, m is None) for d, m, _ in out_entries
    ]
    src_conventional = len(src_media) == 1 and src_media[0] == _earliest_seconds(src)
    if same_shape and src_conventional and out_conventional:
        src_at, out_at = (
            compare.exact(_earliest_seconds(src)),
            compare.exact(_earliest_seconds(out)),
        )
        note = (
            "AD-22: the media_time differs only by the composition-offset convention (source "
            f"{src_at}, output {out_at}, each its track's earliest composition time)"
        )
        return replace(item, status=compare.SAME, note=note), note
    return item, None


def _readable_end(source: Path, info: ProbeResult, facts: compare.Facts) -> Fraction | None:
    """Return the end of the readable video in seconds, or None for a source that is whole."""
    if not {f.kind for f in info.faults} & {"truncated", "unreadable_tail"}:
        return None
    readable = [p for p in facts.pts if p is not None]
    if not readable:
        return None
    table = read_packet_table(source)
    last = max(readable) / info.video.time_base
    return readable_end(info, table, int(last)) * info.video.time_base  # the sink's own rule


def _kept_end(facts: compare.Facts, index: int, end: Fraction) -> Fraction | None:
    """Return the end of the last packet of a stream before ``end`` (the copied part), or None."""
    ends = [
        p.pts + (p.duration or Fraction(0))
        for p in facts.packets.get(index, [])
        if p.pts is not None and p.pts < end
    ]
    return max(ends, default=None)


def readable_tracks(
    facts: compare.Facts, end: Fraction, cut: bool
) -> dict[str, tuple[str, list[Entry] | str]]:
    """Return each track's presentation (by effect) on the readable part of a cut-short source.

    The video ends at ``end``. With ``cut`` (a truncated file, whose copied tracks the sink cuts
    there too) every other track except the timecode track (regenerated by the muxer from the
    video) ends at the end of its last packet before ``end``; without it they are whole.

    Args:
        facts: The source's facts.
        end: The readable video end in seconds.
        cut: Whether the copied tracks are cut.

    Returns:
        ``stream key -> (handler, entries)``, or ``(handler, reason)`` where the presentation
        cannot be cut (a form the sink does not reproduce, or no packet before ``end``).
    """
    result: dict[str, tuple[str, list[Entry] | str]] = {}
    for index, key in facts.keys.items():
        track = compare._track_of(facts, index)
        if track is None:
            continue
        entries = _effect_entries(facts.movie, track)
        if index == facts.video_index:
            stop = end
        elif cut and track.handler != "tmcd":
            kept_end = _kept_end(facts, index, end)
            if kept_end is None:
                result[key] = (track.handler, "no packet before the readable end")
                continue
            stop = kept_end
        else:
            result[key] = (track.handler, entries)
            continue
        shortened = _cut(entries, stop)
        result[key] = (
            track.handler,
            shortened
            if shortened is not None
            else f"cannot be cut at {compare.exact(stop)}: not one media entry, last, at rate 1",
        )
    return result


def _cut_items(
    items: list[compare.Item],
    source: compare.Facts,
    output: compare.Facts,
    end: Fraction,
    cut: bool,
) -> list[compare.Item]:
    """Compare the duration, edit lists and copied packets of a cut-short source (D86).

    The comparison is with the readable part (:func:`readable_tracks`): the video ends at
    ``end``; with ``cut`` the audio and data tracks stop there too. The video edit list keeps
    the source's media time and rate (AD-22's reading is applied afterwards), and the video
    and audio presentation effect is the source's cut there.
    """
    first = next((p for p in source.pts if p is not None), Fraction(0))
    tracks = readable_tracks(source, end, cut)
    video_key = source.keys.get(source.video_index) if source.video_index is not None else None
    result = []
    for item in items:
        name = item.name
        if name == VIDEO_DURATION:
            out_video = compare._stream(output, output.video_index)
            got = compare._ticks(out_video.get("duration_ts"), compare._time_base(out_video))
            want = end - first
            item = compare.Item(
                name,
                item.item_class,
                item.clause,
                {"readable part": compare.exact(want), "whole file": item.source},
                compare.exact(got),
                compare.SAME if got == want else compare.DIFFERENT,
                "D86: compared with the readable part of a cut-short source",
            )
        elif name == VIDEO_EDIT_AS_WRITTEN:
            src_track = _video_track(source)
            written = _written_entries(source.movie, src_track) if src_track else None
            shortened = _cut(written, end) if written is not None else None
            want_rows: Any = (
                None
                if written is None
                else _render(shortened, "media_time")
                if shortened is not None
                else f"cannot be cut at {compare.exact(end)}"
            )
            item = compare._edit_item(
                name,
                item.item_class,
                item.clause,
                {video_key: want_rows} if video_key is not None else {},
                compare._keyed_edits(output, compare._edits_as_written, ("vide",)),
                "D86: the source's video edit list cut at the readable end",
            )
        elif name == EDIT_EFFECT:
            item = compare._edit_item(
                name,
                item.item_class,
                item.clause,
                {
                    key: _render(entries, "media_start") if isinstance(entries, list) else entries
                    for key, (handler, entries) in tracks.items()
                    if handler in ("vide", "soun")
                },
                compare._keyed_edits(output, effect, ("vide", "soun")),
                "D86: the source's presentation cut at the readable end (each copied track at "
                "its last packet before it)",
            )
        elif cut and name.startswith((AUDIO_PACKETS, TELEMETRY_ITEM)):
            key = name.partition(" [")[2].rstrip("]")
            index = next((i for i, k in source.keys.items() if k == key), None)
            out_index = next((i for i, k in output.keys.items() if k == key), None)
            whole = source.packets.get(index, []) if index is not None else []
            kept = [p for p in whole if p.pts is None or p.pts < end]
            got_packets = output.packets.get(out_index, []) if out_index is not None else []
            if name.startswith(AUDIO_PACKETS) and str(
                compare._audio_stream(source, key).get("codec_name", "")
            ).startswith("pcm_"):
                result.append(
                    compare._pcm_packet_item(item, source, output, key, kept=kept, d86=True)
                )
                continue
            want_packets, got_rows = compare._packet_rows(kept), compare._packet_rows(got_packets)
            item = compare.Item(
                name,
                item.item_class,
                item.clause,
                compare._packets_summary(want_packets),
                compare._packets_summary(got_rows),
                compare.SAME if want_packets == got_rows else compare.DIFFERENT,
                "D86: the source's packets before the readable video end",
            )
        result.append(item)
    return result


def _audio_side_item(
    source: compare.Facts,
    output: compare.Facts,
    items: Sequence[compare.Item],
    *,
    end: Fraction | None,
    cut: bool,
) -> tuple[compare.Item, list[str]]:
    """Compare priming rows, using PCM extents only without discard flags or side data.

    Compressed and ineligible PCM streams retain the per-packet rule, including
    its D86 output-count slice. Eligible PCM uses the same source packet window
    as the packet item, independently of how many output packets the sink wrote.
    """
    whole_side, out_side = audio_side_data(source), audio_side_data(output)
    src_side = whole_side
    if cut:
        out_counts = {k: len(v) for k, v in out_side.items()}
        src_side = {k: v[: out_counts.get(k, 0)] for k, v in src_side.items()}
    # Work on copies so the exact legacy rows remain available for fallback.
    src_side, out_side = dict(src_side), dict(out_side)
    notes: list[str] = []
    refusals: list[str] = []
    packet_items = {i.name: i for i in items if i.name.startswith(AUDIO_PACKETS)}
    for stream in compare._streams_of(source, "audio"):
        if not str(stream.get("codec_name", "")).startswith("pcm_"):
            continue
        index = int(stream["index"])
        key = source.keys[index]
        out_stream = compare._audio_stream(output, key)
        if not out_stream:
            continue
        packets = source.packets.get(index, [])
        src_rows = whole_side.get(key, [])
        out_rows = out_side.get(key, [])
        # A second probe must account for every packet before its empty rows can
        # establish that there is no priming or side data to preserve.
        if len(src_rows) != len(packets) or len(out_rows) != len(
            output.packets.get(int(out_stream["index"]), [])
        ):
            refusals.append(f"PCM: incomplete priming/side-data packet evidence [{key}]")
            continue
        if cut and end is not None:
            src_rows = [
                row
                for packet, row in zip(packets, src_rows, strict=True)
                if packet.pts is None or packet.pts < end
            ]
        if any(row[1] or row[2] for row in (*src_rows, *out_rows)):
            continue
        packet_item = packet_items[f"{AUDIO_PACKETS} [{key}]"]
        src_side[key] = [["PCM sample extent and timeline runs", packet_item.source]]
        out_side[key] = [["PCM sample extent and timeline runs", packet_item.output]]
        if packet_item.status == compare.SAME:
            note = f"{packet_item.note} [{key}]"
            if note not in notes:
                notes.append(note)
        else:
            refusals.append(packet_item.note)
    item = compare._sequence_item(
        "audio priming and packet side data",
        compare.MANDATORY,
        "7.5",
        [[k, *row] for k in sorted(src_side) for row in src_side[k]],
        [[k, *row] for k in sorted(out_side) for row in out_side[k]],
        compare._sequence_summary,
    )
    if notes or refusals:
        item = replace(
            item,
            status=compare.DIFFERENT if refusals else item.status,
            note="; ".join(part for part in (item.note, *notes, *refusals) if part),
        )
    return item, notes


def movie_duration_item(
    source: compare.Facts, output: compare.Facts, *, end: Fraction | None, cut: bool
) -> compare.Item:
    """Compare mvhd durations, with the owner's movie-tick reading for whole files (AD-22).

    For a cut-short source the expected duration is the longest readable track presentation
    (:func:`readable_tracks`; the timecode track is left out, the muxer regenerates it from the
    video); a track whose presentation cannot be cut makes the item DIFFERENT, never skipped.
    D86 cut-short paths are unchanged; only ``end is None`` uses the movie-tick reading.

    Args:
        source: The source's facts.
        output: The output's facts.
        end: The readable video end in seconds for a cut-short source, else None.
        cut: Whether the copied tracks are cut at it.

    Returns:
        A MANDATORY item.
    """
    whole_value = movie_duration(source.path)
    whole = compare.exact(whole_value)
    got = movie_duration(output.path)
    if end is None:
        item = compare._item(
            MOVIE_DURATION, compare.MANDATORY, "D94, 7.5", whole, compare.exact(got)
        )
        return _movie_tick_reading(source, output, item, movie_values=(whole_value, got))[0]
    tracks = [
        (key, entries)
        for key, (handler, entries) in readable_tracks(source, end, cut).items()
        if handler != "tmcd"
    ]
    lost = [f"{key}: {entries}" for key, entries in tracks if isinstance(entries, str)]
    want = None
    if not lost:
        want = max(
            (
                sum((d for d, _, _ in entries), Fraction(0))
                for _, entries in tracks
                if isinstance(entries, list)
            ),
            default=None,
        )
    return compare.Item(
        MOVIE_DURATION,
        compare.MANDATORY,
        "D94, 7.5",
        {"readable part": compare.exact(want) if want is not None else lost, "whole file": whole},
        compare.exact(got),
        compare.SAME if want is not None and got == want else compare.DIFFERENT,
        "D86: the longest track presentation of the readable part (the timecode track follows "
        "the video)",
    )


def _colour_items(items: list[compare.Item], info: ProbeResult) -> list[compare.Item]:
    """Compare the colour tags with the D54-resolved description (Q-E), raw tag beside it.

    A field the description leaves ``unknown`` is DIFFERENT, never skipped (DR-20 (4)); with the
    pixel-format row this also refuses a full-range ``yuvj420p`` output tagged ``tv``.
    """
    names = ffmpeg_color_names(info.video.color)
    result = []
    for item in items:
        key = COLOUR_ITEMS.get(item.name)
        if key is not None:
            want = names.get(key)
            item = compare.Item(
                item.name,
                item.item_class,
                item.clause,
                {"resolved (D54)": want, "source tag": item.source},
                item.output,
                compare.SAME if want is not None and item.output == want else compare.DIFFERENT,
                "compared with the source's resolved description"
                + (" (assumed per D54)" if info.video.color.assumed else "")
                + ("; the description has no value here, never skipped" if want is None else ""),
            )
        result.append(item)
    return result


def _depth_items(items: list[compare.Item], info: ProbeResult, depth: int) -> list[compare.Item]:
    """Compare pixel format and bit depth with the selected output depth (D76)."""
    if depth == info.video.bit_depth:
        return items
    result = []
    for item in items:
        if item.name == "pixel format (decoded)":
            want: Any = "yuv420p10le"
        elif item.name == "bit depth":
            want = depth
        else:
            result.append(item)
            continue
        result.append(
            compare.Item(
                item.name,
                item.item_class,
                item.clause,
                {"selected (D76)": want, "source": item.source},
                item.output,
                compare.SAME if item.output == want else compare.DIFFERENT,
                f"D76: {depth}-bit output selected for a {info.video.bit_depth}-bit source",
            )
        )
    return result


def _missing_pts_item(source: compare.Facts, output: compare.Facts) -> compare.Item:
    """Count decoded frames with no pts in each file; both must be zero (DR-18 (4))."""
    src = sum(1 for p in source.pts if p is None)
    out = sum(1 for p in output.pts if p is None)
    return compare.Item(
        "video frames with no pts (decoded)",
        compare.MANDATORY,
        "D94, D95",
        src,
        out,
        compare.SAME if src == 0 and out == 0 else compare.DIFFERENT,
        "both files must have none",
    )


def _redact(item: compare.Item) -> compare.Item:
    """Keep only packet counts of the telemetry data track item (no payload digests)."""
    if not item.name.startswith(TELEMETRY_ITEM):
        return item

    def count(value: Any) -> Any:
        return {"count": value.get("count")} if isinstance(value, dict) else value

    return replace(item, source=count(item.source), output=count(item.output), note="")


def roster_item(items: Sequence[compare.Item]) -> compare.Item:
    """Check that every expected item is present (DR-18 (3)).

    Args:
        items: The record's items.

    Returns:
        A MANDATORY item, DIFFERENT when an expected item is missing or an unexpected one
        appears, naming them.
    """
    present = {item.name.partition(" [")[0] for item in items}
    missing = sorted(set(ROSTER) - present)
    unexpected = sorted(present - set(ROSTER))
    return compare.Item(
        _ROSTER_ITEM,
        compare.MANDATORY,
        "V4, DR-18",
        len(ROSTER),
        {"missing": missing, "unexpected": unexpected},
        compare.SAME if not missing and not unexpected else compare.DIFFERENT,
        "a missing item fails the summary",
    )


def fidelity_items(
    source: compare.Facts,
    output: compare.Facts,
    *,
    info: ProbeResult,
    bit_depth: int,
) -> tuple[list[compare.Item], list[str]]:
    """Compare two files' facts with the product's readings applied.

    Args:
        source: The source's facts.
        output: The output's facts.
        info: The source's probe result.
        bit_depth: The selected output bit depth.

    Returns:
        The items (the roster item last) and the notes the summary must show.
    """
    items = compare.compare_facts(source, output)
    notes: list[str] = []
    end = _readable_end(source.path, info, source)
    cut = end is not None and any(f.kind == "truncated" for f in info.faults)
    if end is not None:
        items = _cut_items(items, source, output, end, cut)
        notes.append(f"D86: compared on the readable part, video end {compare.exact(end)}")
    src_video, out_video = _video_track(source), _video_track(output)
    duration_at = len(items)
    for position, item in enumerate(items):
        if item.name == VIDEO_EDIT_AS_WRITTEN:
            items[position], note = video_edit_reading(source, output, item, end=end)
            if end is None and items[position].status != compare.SAME:
                items[position], note = _movie_tick_reading(source, output, items[position])
            if note is not None:
                notes.append(note)
        elif item.name == EDIT_EFFECT and end is None and src_video and out_video:
            items[position] = compare._edit_item(
                item.name,
                item.item_class,
                item.clause,
                compare._keyed_edits(source, effect, ("vide", "soun")),
                compare._keyed_edits(output, effect, ("vide", "soun")),
                "an absent edit list is the identity from media time 0 (AD-22 extended)",
            )
        elif item.name == VIDEO_DURATION:
            duration_at = position + 1
        if end is None and item.name in (
            EDIT_EFFECT,
            "edit lists as written, non-video tracks (media_time in media seconds)",
        ):
            items[position], note = _movie_tick_reading(source, output, items[position])
            if note is not None:
                notes.append(note)
    duration = movie_duration_item(source, output, end=end, cut=cut)
    items.insert(duration_at, duration)
    if end is None and duration.status == compare.SAME and duration.note:
        notes.append(duration.note)
    items = _colour_items(items, info)
    items = _depth_items(items, info, bit_depth)
    items.append(
        compare._item(
            "audio decoder configuration (profile, initial padding, extradata)",
            compare.MANDATORY,
            "7.5",
            audio_configuration(source),
            audio_configuration(output),
        )
    )
    if cut:
        notes.append("D86: audio side data compared on the source packets kept")
    side_item, pcm_notes = _audio_side_item(source, output, items, end=end, cut=cut)
    items.append(side_item)
    for note in (
        *(
            f"{i.note} [{i.name.partition(' [')[2]}"
            for i in items
            if i.name.startswith(AUDIO_PACKETS)
            and i.status == compare.SAME
            and i.note.startswith("PCM:")
        ),
        *pcm_notes,
    ):
        if note not in notes:
            notes.append(note)
    items.append(_missing_pts_item(source, output))
    items = [_redact(item) for item in items]
    items.append(roster_item(items))
    return items, notes


def fidelity_record(
    source: Path,
    output: Path,
    *,
    bit_depth: int | None = None,
    run: EncodeRun | None = None,
) -> dict[str, Any]:
    """Compare a source with its output and return the JSON record (nothing is written).

    Args:
        source: The source file (read only).
        output: The output file (read only).
        bit_depth: The selected output bit depth; the source's when None.
        run: The encode run, when this instrument made the output (adds the DR-18 (1) proof).

    Returns:
        WP1.5's record with the product's readings, ``summary.notes`` and, for a run, ``encode``.
    """
    info = probe(source)
    depth = bit_depth if bit_depth is not None else info.video.bit_depth
    source_facts, output_facts = gather(source), gather(output)
    items, notes = fidelity_items(source_facts, output_facts, info=info, bit_depth=depth)
    record = compare.build_record(source_facts, output_facts, items)
    record["summary"]["notes"] = notes
    record["bit_depth"] = depth
    if run is not None:
        record["encode"] = {
            "encoder": run.encoder,
            "bit_depth": run.bit_depth,
            "frames_written": run.report.frames_written,
            "warnings": list(run.report.warnings),
            "not_carried": list(run.report.not_carried),
            "window_s": round(run.ended - run.started, 2),
            "nvenc_proof": nvenc_proof(run),
        }
    return record


def summary_line(record: Mapping[str, Any]) -> str:
    """Return the one-line verdict of a record.

    Args:
        record: A record from :func:`fidelity_record`.

    Returns:
        The DIFFERENT counts by class and whether every MANDATORY and REQUIRED item is SAME.
    """
    summary = record["summary"]
    return (
        f"items {summary['items']}; DIFFERENT by class {summary['different']}; "
        f"MANDATORY+REQUIRED all SAME: {summary['mandatory_and_required_all_same']}; "
        f"notes {len(summary.get('notes', []))}"
    )


def main(argv: list[str] | None = None) -> int:
    """Run ``compare`` or ``encode`` and write the record into the working folder.

    Args:
        argv: Command-line arguments; defaults to ``sys.argv[1:]``.

    Returns:
        0 when the comparison ran, 1 when the encode failed, 2 on any other error.
    """
    parser = argparse.ArgumentParser(description="Compare a source video with its output (V4).")
    commands = parser.add_subparsers(dest="command", required=True)
    one = commands.add_parser("compare", help="compare SOURCE with OUTPUT")
    one.add_argument("source", type=Path)
    one.add_argument("output", type=Path)
    two = commands.add_parser("encode", help="encode SOURCE through the sink, then compare")
    two.add_argument("source", type=Path)
    two.add_argument("--encoder", required=True, choices=("hevc_nvenc", "libx265"))
    two.add_argument("--quality", default="standard", choices=("high", "standard", "draft"))
    for sub in (one, two):
        sub.add_argument("--bit-depth", type=int, choices=(8, 10))
        sub.add_argument("--out", type=Path, help=f"record folder (default <working>/{SUBDIR})")
        sub.add_argument("--config", type=Path, help="local configuration file to read")
    args = parser.parse_args(argv)
    try:
        config = load_local_config(args.config)
        root = config.working_path / SUBDIR
        folder = compare.check_output_path(args.out or root, root, config.footage_path)
        run = None
        if args.command == "encode":
            depth = args.bit_depth
            output = folder / f"{args.source.stem}-{args.encoder}-{depth or 'src'}.mp4"
            compare.check_output_path(output, root, config.footage_path)
            try:
                run = encode_file(
                    args.source, output, encoder=args.encoder, quality=args.quality, bit_depth=depth
                )
            except VideoEncodeError as error:
                print(f"error: the encode failed ({error.kind}): {error}", file=sys.stderr)
                return 1
        else:
            output = args.output
        record = fidelity_record(args.source, output, bit_depth=args.bit_depth, run=run)
        paths = compare.write_record(record, folder, output.stem, root, config.footage_path)
    except (
        LocalConfigError,
        compare.OutputPathError,
        compare.ProbeError,
        VideoProbeError,
        OSError,
    ) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    for path in paths:
        print(path)
    print(summary_line(record))
    return 0


if __name__ == "__main__":
    sys.exit(main())
