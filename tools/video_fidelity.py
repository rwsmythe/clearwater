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
* a cut-short source (D86) is compared on its readable part: the expected video duration and
  edit list end at the readable end, the audio and data packets at the copied part;

and with the DR-18 points closed:

1. an NVENC encode is tied to the encode window, the GPU UUID and the FFmpeg PID by
   ``nvidia-smi pmon`` samples taken while it runs (``encode`` only; the record says when no
   sample saw the encoder);
2. the AAC decoder configuration (profile, initial padding, extradata size and MD5), the
   priming (discard-flagged packets) and every packet's side data are compared, MANDATORY;
3. a roster invariant: every expected item must be present, else a MANDATORY ``item roster``
   item is DIFFERENT and the summary fails;
4. decoded frames with no pts are counted in both files (MANDATORY, both must be zero).

The telemetry data track is compared packet for packet in memory (pts, duration, size and the
payload MD5 that ffprobe computes); the record keeps only its packet counts and the status, no
payload, digest or decoded value, and no location value is read from any tag.

Exit status 0 when the comparison ran; 1 when an encode failed; 2 on a usage, configuration,
probe or output-path error.
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
from clearwater.io.video.verify import frame_end, read_packet_table
from container_spike import compare
from local_config import LocalConfigError, load_local_config

SUBDIR = "wp3.10"
"""The default record folder under the working folder."""

TELEMETRY_ITEM = "GPMF track gpmd"
"""The start of the WP1.5 item name for the telemetry data track (its values are redacted)."""

VIDEO_EDIT_AS_WRITTEN = "edit list, video track, as written (media_time in media seconds)"
EDIT_EFFECT = "edit list, video and audio tracks (presentation effect)"
VIDEO_DURATION = "video stream duration"
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
        rows: ``(seconds since the window opened, gpu index, pid, enc %)`` per sampled process.
        error: Why sampling did not run, or None.
    """

    gpus: dict[str, str] = field(default_factory=dict)
    rows: list[tuple[float, str, int, str]] = field(default_factory=list)
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
        self._opened = 0.0

    def start(self) -> None:
        listing = _nvidia_smi(["--query-gpu=index,uuid", "--format=csv,noheader"])
        if listing is None:
            self.samples.error = "nvidia-smi is not available"
            return
        for line in listing.splitlines():
            index, _, uuid = line.partition(",")
            if uuid.strip():
                self.samples.gpus[index.strip()] = uuid.strip()
        self._opened = time.monotonic()
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.is_set():
            text = _nvidia_smi(["pmon", "-c", "1", "-s", "u"])
            at = time.monotonic() - self._opened
            for line in (text or "").splitlines():
                parts = line.split()
                if len(parts) >= 6 and not line.startswith("#") and parts[1].isdigit():
                    self.samples.rows.append((round(at, 2), parts[0], int(parts[1]), parts[5]))
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
        self.started = time.time()
        super()._start(command)
        process = self._process
        self.pid = process.pid if process is not None else None


@dataclass
class EncodeRun:
    """What :func:`encode_file` did.

    Attributes:
        report: The sink's report.
        encoder: The encoder used.
        bit_depth: The output bit depth.
        pid: The FFmpeg process id.
        started: Wall-clock start of the encode window (seconds since the epoch).
        ended: Wall-clock end of the window.
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
        sink.ended = time.time()
        samples = sampler.stop() if sampler is not None else None
    return EncodeRun(report, encoder, depth, sink.pid, sink.started, sink.ended, samples)


def nvenc_proof(run: EncodeRun) -> dict[str, Any]:
    """Summarise the DR-18 (1) proof: the FFmpeg PID seen encoding on a named GPU in the window.

    Args:
        run: An encode run.

    Returns:
        ``tied`` True when at least one sample inside the window shows the FFmpeg PID with a
        non-zero encoder load, with the GPU UUID, the PID and the matching samples; otherwise
        ``tied`` False and the reason.
    """
    if run.encoder != "hevc_nvenc":
        return {"tied": False, "reason": f"not an NVENC encode ({run.encoder})"}
    gpu = run.gpu
    if gpu is None or gpu.error is not None:
        return {"tied": False, "reason": gpu.error if gpu is not None else "not sampled"}
    hits = [
        row
        for row in gpu.rows
        if row[2] == run.pid and row[3] not in ("-", "0") and row[0] <= run.ended - run.started
    ]
    proof: dict[str, Any] = {
        "pid": run.pid,
        "window_s": round(run.ended - run.started, 2),
        "samples": len(gpu.rows),
        "pid_samples_with_encoder_load": [list(row) for row in hits],
        "gpu_uuid": sorted({gpu.gpus.get(row[1], "?") for row in hits}),
    }
    proof["tied"] = bool(hits)
    if not hits:
        proof["reason"] = "no sample in the window showed the FFmpeg PID with encoder load"
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


def gather(path: Path) -> compare.Facts:
    """Read every fact the comparison needs from one file, a cut-short one included.

    WP1.5's reader refuses a cut-short file (round-0 P5); this one reads it as far as its
    ``moov`` allows.

    Args:
        path: The file (read only).

    Returns:
        The facts.
    """
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
    if track.edits is not None:
        return compare.edit_effect(movie, track)
    earliest = _earliest_seconds(track)
    media = Fraction(track.media_duration, track.media_timescale)
    rows: list[dict[str, Any]] = []
    if earliest > 0:
        rows.append({"duration": compare.exact(earliest), "media_start": "empty", "rate": "1"})
    zero = compare.exact(Fraction(0))
    rows.append({"duration": compare.exact(media), "media_start": zero, "rate": "1"})
    return rows


def _video_track(facts: compare.Facts) -> compare.Track | None:
    """Return the video track of a file's facts."""
    return compare._track_of(facts, facts.video_index)


def _edits_seconds(movie: compare.Movie, track: compare.Track) -> list[tuple[Fraction, bool]]:
    """Return a track's edits as ``(duration seconds, empty)``; rates are checked by the caller."""
    return [
        (Fraction(e.segment_duration, movie.timescale), e.media_time == -1)
        for e in track.edits or ()
    ]


def video_edit_reading(
    source: compare.Facts, output: compare.Facts, item: compare.Item
) -> tuple[compare.Item, str | None]:
    """Apply AD-22 (and its Q-C extension) to the video edit list "as written" item.

    Args:
        source: The source's facts.
        output: The output's facts.
        item: WP1.5's "as written" item.

    Returns:
        The item (SAME with a note where AD-22 reads it so) and the note for the summary, or
        None when no reading applied.
    """
    if item.status == compare.SAME:
        return item, None
    src, out = _video_track(source), _video_track(output)
    if src is None or out is None or out.edits is None:
        return item, None
    if any(e.rate != 1 for e in out.edits) or (
        src.edits is not None and any(e.rate != 1 for e in src.edits)
    ):
        return item, None
    out_media = [e for e in out.edits if e.media_time != -1]
    if len(out_media) != 1:
        return item, None
    out_conventional = Fraction(out_media[0].media_time, out.media_timescale) == _earliest_seconds(
        out
    )
    if src.edits is None:
        if out_conventional and effect(source.movie, src) == effect(output.movie, out):
            note = (
                "AD-22 extended (Q-C): the source has no edit list (identity from media time 0); "
                "the output writes the identity list explicitly -- same presentation"
            )
            return replace(item, status=compare.SAME, note=note), note
        return item, None
    src_media = [e for e in src.edits if e.media_time != -1]
    same_shape = _edits_seconds(source.movie, src) == _edits_seconds(output.movie, out)
    src_conventional = len(src_media) == 1 and Fraction(
        src_media[0].media_time, src.media_timescale
    ) == _earliest_seconds(src)
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
    return frame_end(info, table, int(last)) * info.video.time_base


def _cut_items(
    items: list[compare.Item],
    source: compare.Facts,
    output: compare.Facts,
    end: Fraction,
    cut: bool,
) -> list[compare.Item]:
    """Compare the duration, edit list and copied packets of a cut-short source (D86).

    The comparison is with the readable part: the video ends at ``end``; with ``cut`` the audio
    and data tracks stop there too.
    """
    first = next((p for p in source.pts if p is not None), Fraction(0))
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
        elif name in (VIDEO_EDIT_AS_WRITTEN, EDIT_EFFECT):
            track = _video_track(output)
            want_edits = ([(first, True)] if first > 0 else []) + [(end - first, False)]
            got_edits = _edits_seconds(output.movie, track) if track is not None else []
            item = compare.Item(
                name,
                item.item_class,
                item.clause,
                {"readable part": [[compare.exact(d), e] for d, e in want_edits]},
                [[compare.exact(d), e] for d, e in got_edits],
                compare.SAME if got_edits == want_edits else compare.DIFFERENT,
                "D86: the video edit list of a cut-short source ends at its readable end",
            )
        elif cut and name.startswith((AUDIO_PACKETS, TELEMETRY_ITEM)):
            key = name.partition(" [")[2].rstrip("]")
            index = next((i for i, k in source.keys.items() if k == key), None)
            out_index = next((i for i, k in output.keys.items() if k == key), None)
            whole = source.packets.get(index, []) if index is not None else []
            kept = [p for p in whole if p.pts is None or p.pts < end]
            got_packets = output.packets.get(out_index, []) if out_index is not None else []
            want_rows, got_rows = compare._packet_rows(kept), compare._packet_rows(got_packets)
            item = compare.Item(
                name,
                item.item_class,
                item.clause,
                compare._packets_summary(want_rows),
                compare._packets_summary(got_rows),
                compare.SAME if want_rows == got_rows else compare.DIFFERENT,
                "D86: the source's packets before the readable video end",
            )
        result.append(item)
    return result


def _colour_items(items: list[compare.Item], info: ProbeResult) -> list[compare.Item]:
    """Compare the colour tags with the D54-resolved description (Q-E), raw tag beside it."""
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
                compare.SAME if item.output == want else compare.DIFFERENT,
                "compared with the source's resolved description"
                + (" (assumed per D54)" if info.video.color.assumed else ""),
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
    src_video, out_video = _video_track(source), _video_track(output)
    for position, item in enumerate(items):
        if item.name == VIDEO_EDIT_AS_WRITTEN:
            items[position], note = video_edit_reading(source, output, item)
            if note is not None:
                notes.append(note)
        elif item.name == EDIT_EFFECT and src_video is not None and out_video is not None:
            items[position] = compare._edit_item(
                item.name,
                item.item_class,
                item.clause,
                compare._keyed_edits(source, effect, ("vide", "soun")),
                compare._keyed_edits(output, effect, ("vide", "soun")),
                "an absent edit list is the identity from media time 0 (AD-22 extended)",
            )
    end = _readable_end(source.path, info, source)
    if end is not None:
        cut = any(f.kind == "truncated" for f in info.faults)
        items = _cut_items(items, source, output, end, cut)
        notes.append(f"D86: compared on the readable part, video end {compare.exact(end)}")
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
    src_side, out_side = audio_side_data(source), audio_side_data(output)
    if end is not None and any(f.kind == "truncated" for f in info.faults):
        notes.append("D86: audio side data compared on the source packets kept")
        out_counts = {k: len(v) for k, v in out_side.items()}
        src_side = {k: v[: out_counts.get(k, 0)] for k, v in src_side.items()}
    items.append(
        compare._sequence_item(
            "audio priming and packet side data",
            compare.MANDATORY,
            "7.5",
            [[k, *row] for k in sorted(src_side) for row in src_side[k]],
            [[k, *row] for k in sorted(out_side) for row in out_side[k]],
            compare._sequence_summary,
        )
    )
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
