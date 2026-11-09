"""The packet table the sink reads from a source and from its finished output (WP3.10, D94).

D94 says per-frame timestamps, start offset and edit list are "preserved and verified". The sink
reads one :class:`PacketTable` of the source when it opens (the per-frame pts the probe result
does not carry, the audio packets, the sample aspect ratio) and one of the output when it
closes, and :func:`check_output` compares the MANDATORY items it can see without decoding: the
frame count and every pts against the pts written, the video start, the video track's edit list
against the written start and end (its ``media_time`` is checked through its effect: the
demuxer applies it to every pts compared), the display rotation, and the audio: PCM format,
first pts, presented/stored sample totals and timeline runs, or every compressed packet's pts.
The full item-by-item comparison is the fidelity instrument's (``tools/video_fidelity.py``);
this check is what every export runs.

Each table is three ``ffprobe`` listings (no decode): the stream list with the few container
tags asked for by name (``creation_time`` and ``firmware``, so the best-effort report can say
whether they were carried; never a location tag), then the packets of the video stream, then
the packets of the audio streams. The packets of a data track (the camera's telemetry, the
timecode) are never listed: the listings select the video and audio streams only, and a data
track is judged from the stream list (its sample count) alone.

Each table also carries the video track's own sample table (``stts`` and ``ctts`` from
``moov``, read by :func:`read_sample_table`). A cut-short file's packet listing stops at the
cut, but its ``moov`` (when it can be read at all) still describes every sample, so the frame
after the last readable one -- and so where that frame ends -- comes from the sample table,
exact in ticks (:func:`readable_end`).
"""

from __future__ import annotations

import json
import re
import struct
import subprocess
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any

from clearwater.interfaces.video import ProbeResult
from clearwater.io.video.boxes import MAX_MOOV_BYTES, BoxError, read_movie_boxes
from clearwater.io.video.inputs import ascii_text
from clearwater.io.video.pipes import tool_spawn_kwargs
from clearwater.io.video.probe import VideoProbeError, find_tool

READ_TIMEOUT_S = 600
"""Seconds one packet listing may take (a long 4K clip lists in seconds; this is a backstop)."""

TIMECODE_TAG = "tmcd"
"""The codec tag of a timecode track; the MP4 muxer regenerates it rather than copying it."""

CUT_SLACK_S = Fraction(2, 1_000_000)
"""How near an audio packet may lie to a cut and still go either way, in seconds: FFmpeg reads
the input ``-to`` and the input's start time in microseconds, so a packet within this of the cut
point may be kept or dropped."""

_STREAM_ENTRIES = (
    "stream=index,codec_type,codec_tag_string,time_base,start_pts,duration_ts,nb_frames,"
    "codec_name,sample_rate,channels,sample_fmt,"
    "sample_aspect_ratio:stream_side_data=rotation:format_tags=creation_time,firmware"
)
MAX_SAMPLES = 10_000_000
"""The most video samples a sample table may describe (46 hours at 60 fps); more is malformed."""

_PACKET_ENTRIES = "packet=stream_index,pts,flags,duration,size"
_RATIO = re.compile(r"^(\d+):(\d+)$")
_HEADER = 8
_LARGE_HEADER = 16


@dataclass(frozen=True)
class SampleTable:
    """The video track's sample timing as its ``moov`` writes it (``stts`` and ``ctts``).

    Attributes:
        timescale: The video media's ticks per second (``mdhd``).
        composition: Every sample's composition time in media ticks, in decode order: its
            decode time (the ``stts`` deltas summed from 0) plus its ``ctts`` offset (0
            without a ``ctts`` box). Never empty.
    """

    timescale: int
    composition: tuple[int, ...]

    @property
    def earliest(self) -> Fraction:
        """The track's earliest composition time, in seconds."""
        return Fraction(min(self.composition), self.timescale)


@dataclass(frozen=True)
class HevcLevel:
    """The HEVC level and tier a video track signals in its ``hvcC`` box.

    Attributes:
        level_idc: ``general_level_idc``: 30 times the level number (180 is level 6.0).
        high_tier: ``general_tier_flag``: True for the High tier, False for the Main tier.
    """

    level_idc: int
    high_tier: bool

    @property
    def name(self) -> str:
        """The level and tier as people write them, for example ``"6.0 Main"``."""
        return f"{self.level_idc / 30:.1f} {'High' if self.high_tier else 'Main'}"


@dataclass(frozen=True)
class StreamRow:
    """One stream of a packet table.

    Attributes:
        index: The stream index in the file.
        codec_type: ``"video"``, ``"audio"``, ``"data"`` or another FFmpeg codec type.
        codec_tag: The stream's codec tag, for example ``"hvc1"`` or ``"tmcd"``.
        time_base: The stream's time base, or None when ffprobe gives none.
        start_pts: The stream's first pts in ticks, or None.
        duration_ts: The stream's duration in ticks, or None.
        sample_aspect_ratio: The ratio as ffprobe prints it (``"1:1"``), or None.
        rotation: The display-matrix rotation as ffprobe prints it, or None without a matrix.
        packets: The number of packets listed: video and audio streams only; None for a stream
            whose packets are never listed (a data track).
        frames: The sample count the stream list gives (``nb_frames``, from the container's
            sample table, no packet read), or None.
        codec_name: FFmpeg's codec name, used to identify raw PCM audio.
        sample_rate: Audio sample frames per second, or None.
        channels: Audio channel count, or None.
        sample_fmt: FFmpeg's decoded audio sample format, or None.
    """

    index: int
    codec_type: str
    codec_tag: str
    time_base: Fraction | None
    start_pts: int | None
    duration_ts: int | None
    sample_aspect_ratio: str | None
    rotation: Fraction | None
    packets: int | None
    frames: int | None = None
    codec_name: str = ""
    sample_rate: int | None = None
    channels: int | None = None
    sample_fmt: str | None = None


@dataclass(frozen=True)
class PacketTable:
    """The packets and stream facts of one file, as one ``ffprobe`` listing gives them.

    Attributes:
        streams: Every stream, in index order.
        video_index: The index of the first video stream.
        video_pts: The video packets' pts in file (decode) order; packets without a pts are
            counted in ``video_missing_pts`` instead.
        video_missing_pts: The number of video packets without a pts.
        video_corrupt_pts: The pts of the video packets flagged corrupt (``C``).
        tags: The ``creation_time`` and ``firmware`` container tags that are present.
        audio_pts: Per audio stream index, its packets' pts in file order (None for a packet
            without one).
        samples: The video track's sample table, or None when it cannot be read.
        sample_pts: Every video sample's pts as the demuxer gives it, in decode order, from
            the sample table: its composition times moved by the one offset the listed packets
            show (the edit list's effect). None when there is no sample table, it disagrees
            with the listed packets, or a listed packet has no pts. On a cut-short file it runs
            past the listing to the samples the cut removed.
        audio_durations: Per audio index, packet durations in stream ticks, aligned with pts.
        audio_sizes: Per audio index, packet payload sizes in bytes, aligned with pts.
    """

    streams: tuple[StreamRow, ...]
    video_index: int
    video_pts: tuple[int, ...]
    video_missing_pts: int
    video_corrupt_pts: tuple[int, ...]
    tags: Mapping[str, str]
    audio_pts: Mapping[int, tuple[int | None, ...]] = field(default_factory=dict)
    samples: SampleTable | None = None
    sample_pts: tuple[int, ...] | None = None
    audio_durations: Mapping[int, tuple[int | None, ...]] = field(default_factory=dict)
    audio_sizes: Mapping[int, tuple[int | None, ...]] = field(default_factory=dict)

    @property
    def video(self) -> StreamRow:
        """The first video stream."""
        return next(s for s in self.streams if s.index == self.video_index)

    def of_type(self, codec_type: str) -> tuple[StreamRow, ...]:
        """Return the streams of one codec type, in index order.

        Args:
            codec_type: For example ``"audio"`` or ``"data"``.

        Returns:
            The matching streams.
        """
        return tuple(s for s in self.streams if s.codec_type == codec_type)

    def pcm_dropped_bytes(
        self, output: PacketTable, *, probe: ProbeResult, audio_end: Fraction | None
    ) -> int:
        """Return partial-frame bytes discarded by a successful D86 PCM comparison.

        Args:
            output: The finished output's packet table.
            probe: The source's probe result, including its truncated fault if any.
            audio_end: The source audio cut, or None for a whole-stream copy.

        Returns:
            The dropped byte count, defaulting to zero without a matching D86 exception.
            This read-only calculation changes neither table nor the check's return value.
        """
        if audio_end is None or not any(f.kind == "truncated" for f in probe.faults):
            return 0
        return sum(
            _pcm_problems(number, src, out, self, output, audio_end, truncated=True).dropped_bytes
            for number, (src, out) in enumerate(
                zip(self.of_type("audio"), output.of_type("audio"), strict=False)
            )
            if src.codec_name.startswith("pcm_")
        )


def _int(value: object) -> int | None:
    """Return an int from an int or an integer string; None otherwise."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.fullmatch(r"-?\d+", value):
        return int(value)
    return None


def _fraction(value: object) -> Fraction | None:
    """Parse ``"1/30000"`` or a decimal rotation; None when absent or malformed."""
    try:
        return Fraction(str(value))
    except (ValueError, ZeroDivisionError):
        return None


def _rotation(stream: Mapping[str, Any]) -> Fraction | None:
    """Return the stream's display-matrix rotation as printed, or None without a matrix."""
    for item in stream.get("side_data_list") or []:
        if isinstance(item, Mapping) and "rotation" in item:
            return _fraction(item["rotation"])
    return None


def _listing(path: Path, arguments: Sequence[str], *, strict: bool) -> dict[str, Any]:
    """Run one ``ffprobe`` JSON listing of ``path`` and return the parsed document.

    Raises:
        VideoProbeError: ``"missing_tool"`` without ffprobe; ``"unreadable"`` when it cannot run,
            its output is not a JSON object, or (``strict``) it exits with a non-zero status.
    """
    name = ascii_text(path.name)
    command = [str(find_tool("ffprobe")), "-v", "error", "-of", "json", *arguments]
    command.append(str(path.absolute()))  # absolute: a relative name could read as an option
    try:
        done = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=READ_TIMEOUT_S,
            check=False,
            **tool_spawn_kwargs(),
        )
    except subprocess.TimeoutExpired as error:
        raise VideoProbeError(
            "unreadable", f"{name} could not be listed: timed out after {READ_TIMEOUT_S} s."
        ) from error
    except OSError as error:
        raise VideoProbeError("unreadable", f"{name} could not be listed: {error}") from error
    if strict and done.returncode != 0:
        raise VideoProbeError(
            "unreadable", f"{name} could not be listed (ffprobe exit status {done.returncode})."
        )
    try:
        data = json.loads(done.stdout.decode("utf-8", errors="replace"))
    except ValueError as error:
        raise VideoProbeError("unreadable", f"{name} could not be listed.") from error
    if not isinstance(data, dict):
        raise VideoProbeError("unreadable", f"{name} could not be listed.")
    return data


def _packets(document: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """Return the packet entries of a listing."""
    return [p for p in document.get("packets") or [] if isinstance(p, Mapping)]


def _boxes(data: bytes, start: int, end: int) -> Iterator[tuple[bytes, int, int]]:
    """Yield the child boxes in ``data[start:end]`` as ``(type, payload_start, box_end)``.

    Raises:
        BoxError: If a child is smaller than its header or extends past ``end``.
    """
    pos = start
    while end - pos >= _HEADER:  # fewer bytes left: QuickTime's 32-bit zero terminator
        size, kind = struct.unpack_from(">I4s", data, pos)
        header = _HEADER
        if size == 1:
            if end - pos < _LARGE_HEADER:
                raise BoxError("64-bit box header past the end of its parent")
            (size,) = struct.unpack_from(">Q", data, pos + _HEADER)
            header = _LARGE_HEADER
        elif size == 0:
            size = end - pos
        if size < header or pos + size > end:
            raise BoxError("box size is inconsistent with its parent")
        yield kind, pos + header, pos + size
        pos += size


def _child(data: bytes, span: tuple[int, int], kind: bytes) -> tuple[int, int] | None:
    """Return the payload span of the first child of ``span`` of the given type, or None."""
    for found, start, end in _boxes(data, *span):
        if found == kind:
            return start, end
    return None


def _moov(path: Path) -> bytes | None:
    """Return the payload of the file's ``moov`` box, or None when it has none.

    Top-level boxes are walked by their sizes (the media data is skipped, never read).

    Raises:
        BoxError: If a top-level box before ``moov`` is malformed, or ``moov`` overruns the file.
        OSError: If the file cannot be read.
    """
    with path.open("rb") as handle:
        total = handle.seek(0, 2)
        pos = 0
        while total - pos >= _HEADER:
            handle.seek(pos)
            size, kind = struct.unpack(">I4s", handle.read(_HEADER))
            header = _HEADER
            if size == 1:
                extension = handle.read(_HEADER)
                if len(extension) < _HEADER:
                    raise BoxError("64-bit top-level box header is cut short")
                (size,) = struct.unpack(">Q", extension)
                header = _LARGE_HEADER
            elif size == 0:
                size = total - pos
            if size < header:
                raise BoxError("top-level box smaller than its header")
            if kind == b"moov":
                if pos + size > total or size - header > MAX_MOOV_BYTES:
                    raise BoxError("moov is cut short or larger than the supported maximum")
                handle.seek(pos + header)
                return handle.read(size - header)
            pos += size
    return None


def _table_entries(data: bytes, span: tuple[int, int], form: str) -> Iterator[tuple[int, int]]:
    """Yield the ``(count, value)`` entries of an ``stts`` or ``ctts`` payload."""
    start, end = span
    if end - start < 8:
        raise BoxError("sample table box too short")
    (count,) = struct.unpack_from(">I", data, start + 4)
    if count * 8 > end - start - 8:
        raise BoxError("sample table entry count past the end of the box")
    for index in range(count):
        yield struct.unpack_from(form, data, start + 8 + index * 8)


def _video_media(moov: bytes) -> tuple[int, int] | None:
    """Return the ``mdia`` payload span of the first video track in ``moov``, or None."""
    for kind, start, end in _boxes(moov, 0, len(moov)):
        if kind != b"trak":
            continue
        mdia = _child(moov, (start, end), b"mdia")
        hdlr = _child(moov, mdia, b"hdlr") if mdia else None
        if mdia is None or hdlr is None or hdlr[1] - hdlr[0] < 12:
            continue
        if moov[hdlr[0] + 8 : hdlr[0] + 12] == b"vide":
            return mdia
    return None


_VISUAL_SAMPLE_ENTRY = 78
"""Bytes of a visual sample entry's fixed fields, before its child boxes (ISO 14496-12)."""

_HEVC_ENTRIES = (b"hvc1", b"hev1")


def read_hevc_level(path: Path) -> HevcLevel | None:
    """Read the level and tier the first video track signals in its ``hvcC`` box.

    Only ``moov`` is read (no decode, no FFmpeg): the first sample entry of the video track's
    ``stsd``, which for HEVC is ``hvc1`` or ``hev1`` with an ``hvcC`` child.

    Args:
        path: The file; opened read only.

    Returns:
        The level and tier, or None when the file has no ``moov``, no video track, or its first
        video sample entry is not HEVC or has no ``hvcC``.

    Raises:
        BoxError: If a box on the path is malformed or ``hvcC`` is too short.
        OSError: If the file cannot be read.
    """
    moov = _moov(path)
    mdia = _video_media(moov) if moov is not None else None
    if moov is None or mdia is None:
        return None
    minf = _child(moov, mdia, b"minf")
    stbl = _child(moov, minf, b"stbl") if minf else None
    stsd = _child(moov, stbl, b"stsd") if stbl else None
    if stsd is None or stsd[1] - stsd[0] < 8:
        return None
    entry = next(_boxes(moov, stsd[0] + 8, stsd[1]), None)  # after version, flags and count
    if entry is None or entry[0] not in _HEVC_ENTRIES:
        return None
    if entry[2] - entry[1] < _VISUAL_SAMPLE_ENTRY:
        raise BoxError("HEVC sample entry too short")
    config = _child(moov, (entry[1] + _VISUAL_SAMPLE_ENTRY, entry[2]), b"hvcC")
    if config is None:
        return None
    if config[1] - config[0] < 13:
        raise BoxError("hvcC too short")
    return HevcLevel(level_idc=moov[config[0] + 12], high_tier=bool(moov[config[0] + 1] & 0x20))


def read_sample_table(path: Path) -> SampleTable | None:
    """Read the first video track's sample timing from ``moov`` (``mdhd``, ``stts``, ``ctts``).

    Only ``moov`` is read, so the table is whole on a file cut short inside its media data.
    ``ctts`` offsets are read as signed (version 1 is signed; FFmpeg reads version 0 the same
    way).

    Args:
        path: The file; opened read only.

    Returns:
        The table, or None when the file has no ``moov``, no video track or no ``stts``.

    Raises:
        BoxError: If a box on the path is malformed, the ``ctts`` sample count differs from the
            ``stts`` one, or the table describes more than :data:`MAX_SAMPLES` samples.
        OSError: If the file cannot be read.
    """
    moov = _moov(path)
    if moov is None:
        return None
    for kind, start, end in _boxes(moov, 0, len(moov)):
        if kind != b"trak":
            continue
        mdia = _child(moov, (start, end), b"mdia")
        hdlr = _child(moov, mdia, b"hdlr") if mdia else None
        if mdia is None or hdlr is None or hdlr[1] - hdlr[0] < 12:
            continue
        if moov[hdlr[0] + 8 : hdlr[0] + 12] != b"vide":
            continue
        mdhd = _child(moov, mdia, b"mdhd")
        minf = _child(moov, mdia, b"minf")
        stbl = _child(moov, minf, b"stbl") if minf else None
        stts = _child(moov, stbl, b"stts") if stbl else None
        if mdhd is None or stts is None:
            return None
        if mdhd[1] - mdhd[0] < 4 or moov[mdhd[0]] not in (0, 1):
            raise BoxError("mdhd too short or of unknown version")
        offset = mdhd[0] + 4 + (16 if moov[mdhd[0]] == 1 else 8)
        if offset + 4 > mdhd[1]:
            raise BoxError("mdhd too short")
        (timescale,) = struct.unpack_from(">I", moov, offset)
        if timescale == 0:
            raise BoxError("time scale is zero")
        decode: list[int] = []
        now = 0
        for count, delta in _table_entries(moov, stts, ">II"):
            if len(decode) + count > MAX_SAMPLES:
                raise BoxError("the sample table describes too many samples")
            for _ in range(count):
                decode.append(now)
                now += delta
        if not decode:
            return None
        assert stbl is not None  # stts was found inside it
        ctts = _child(moov, stbl, b"ctts")
        offsets: list[int] = []
        if ctts is not None:
            for count, value in _table_entries(moov, ctts, ">Ii"):
                if len(offsets) + count > len(decode):
                    raise BoxError("ctts describes more samples than stts")
                offsets += [value] * count
            if len(offsets) != len(decode):
                raise BoxError("ctts describes fewer samples than stts")
        else:
            offsets = [0] * len(decode)
        composition = tuple(d + o for d, o in zip(decode, offsets, strict=True))
        return SampleTable(timescale=int(timescale), composition=composition)
    return None


def _sample_pts(
    samples: SampleTable | None, listed: Sequence[int], missing: int, time_base: Fraction | None
) -> tuple[int, ...] | None:
    """Map a sample table onto the demuxer's pts, checked against every listed packet.

    The demuxer's pts are the composition times moved by one offset (the edit list's effect:
    an empty edit's dwell less the media segment's start). The offset is read off the first
    listed packet and must hold for every listed packet, which are the table's first samples
    in decode order (a cut file lists a prefix).
    """
    if samples is None or missing or not listed or time_base != Fraction(1, samples.timescale):
        return None
    composition = samples.composition
    if len(listed) > len(composition):
        return None
    shift = listed[0] - composition[0]
    if any(pts != time + shift for pts, time in zip(listed, composition, strict=False)):
        return None
    return tuple(time + shift for time in composition)


def read_packet_table(path: Path, *, strict: bool = False) -> PacketTable:
    """List the stream facts and the video and audio packets of one file (no decode).

    Three ``ffprobe`` calls: the stream list, the video stream's packets, the audio streams'
    packets (skipped without audio). A data track's packets are never listed. The video
    track's sample table is read from ``moov`` and mapped onto the listed pts
    (``PacketTable.sample_pts``); a malformed table is recorded as absent.

    Args:
        path: The file; opened read only.
        strict: Fail when ffprobe exits with a non-zero status (the output read-back). Without
            it, a listing that ffprobe ends with an error still counts as far as it got (a
            cut-short source lists its readable part).

    Returns:
        The table.

    Raises:
        VideoProbeError: ``"missing_tool"`` without ffprobe; ``"unreadable"`` when a listing
            fails or the file has no video stream.
    """
    document = _listing(path, ["-show_entries", _STREAM_ENTRIES], strict=strict)
    raw_streams = [s for s in document.get("streams") or [] if isinstance(s, Mapping)]
    video_index = next(
        (_int(s.get("index")) for s in raw_streams if s.get("codec_type") == "video"), None
    )
    if video_index is None:
        raise VideoProbeError("unreadable", f"{ascii_text(path.name)} has no video stream.")
    audio_pts: dict[int, list[int | None]] = {
        index: []
        for s in raw_streams
        if s.get("codec_type") == "audio" and (index := _int(s.get("index"))) is not None
    }
    counts: dict[int, int] = {video_index: 0}
    audio_durations: dict[int, list[int | None]] = {index: [] for index in audio_pts}
    audio_sizes: dict[int, list[int | None]] = {index: [] for index in audio_pts}
    video_pts: list[int] = []
    corrupt: list[int] = []
    missing = 0
    selected = ["-select_streams", str(video_index), "-show_entries", _PACKET_ENTRIES]
    for packet in _packets(_listing(path, selected, strict=strict)):
        if _int(packet.get("stream_index")) != video_index:
            continue
        counts[video_index] += 1
        pts = _int(packet.get("pts"))
        if pts is None:
            missing += 1
            continue
        video_pts.append(pts)
        if "C" in str(packet.get("flags", "")):
            corrupt.append(pts)
    if audio_pts:
        selected = ["-select_streams", "a", "-show_entries", _PACKET_ENTRIES]
        for packet in _packets(_listing(path, selected, strict=strict)):
            index = _int(packet.get("stream_index"))
            if index is not None and index in audio_pts:
                audio_pts[index].append(_int(packet.get("pts")))
                audio_durations[index].append(_int(packet.get("duration")))
                audio_sizes[index].append(_int(packet.get("size")))
    counts.update({index: len(listed) for index, listed in audio_pts.items()})
    streams = tuple(
        StreamRow(
            index=index,
            codec_type=str(s.get("codec_type", "")),
            codec_tag=str(s.get("codec_tag_string", "")),
            time_base=_fraction(s.get("time_base")),
            start_pts=_int(s.get("start_pts")),
            duration_ts=_int(s.get("duration_ts")),
            sample_aspect_ratio=str(s["sample_aspect_ratio"])
            if s.get("sample_aspect_ratio") is not None
            else None,
            rotation=_rotation(s),
            packets=counts.get(index),
            frames=_int(s.get("nb_frames")),
            codec_name=str(s.get("codec_name", "")),
            sample_rate=_int(s.get("sample_rate")),
            channels=_int(s.get("channels")),
            sample_fmt=str(s["sample_fmt"]) if s.get("sample_fmt") is not None else None,
        )
        for s in raw_streams
        if (index := _int(s.get("index"))) is not None
    )
    tags = (document.get("format") or {}).get("tags") or {}
    try:
        samples = read_sample_table(path)
    except (BoxError, OSError):
        samples = None  # a malformed table is no table: whatever needs it refuses
    video_time_base = next((s.time_base for s in streams if s.index == video_index), None)
    return PacketTable(
        streams=streams,
        video_index=video_index,
        video_pts=tuple(video_pts),
        video_missing_pts=missing,
        video_corrupt_pts=tuple(corrupt),
        tags={
            key: str(tags[key])
            for key in ("creation_time", "firmware")
            if isinstance(tags, Mapping) and key in tags
        },
        audio_pts={index: tuple(listed) for index, listed in audio_pts.items()},
        samples=samples,
        sample_pts=_sample_pts(samples, video_pts, missing, video_time_base),
        audio_durations={index: tuple(values) for index, values in audio_durations.items()},
        audio_sizes={index: tuple(values) for index, values in audio_sizes.items()},
    )


def square_pixels(ratio: str | None) -> bool:
    """Return whether a sample aspect ratio is square, or cannot be seen (CHARC P8 ruling).

    A ratio that cannot be seen at all -- absent, unspecified (``0:1``) or not a ratio (``N/A``)
    -- is treated as 1:1, so only a stated non-square ratio such as ``4:3`` is refused.

    Args:
        ratio: The ratio as ffprobe prints it, or None.

    Returns:
        True for square pixels or a ratio that cannot be seen.
    """
    if ratio is None:
        return True
    match = _RATIO.match(ratio)
    if match is None:
        return True  # not a ratio at all: cannot be seen, treated as 1:1
    numerator, denominator = int(match.group(1)), int(match.group(2))
    return numerator == 0 or numerator == denominator


def presentation_end(probe: ProbeResult, table: PacketTable) -> Fraction:
    """Return the end of the source video's presentation in time-base ticks.

    The sum of the edit list's segment durations when the video track has an edit list (the
    demuxer's pts are presentation times, so the edit list's end is the last frame's end);
    otherwise the stream's start plus its duration.

    Args:
        probe: The source's probe result.
        table: The source's packet table.

    Returns:
        The end in ticks, exact (it may be a fraction of a tick).
    """
    time_base = probe.video.time_base
    if probe.edit_list:
        return sum((e.segment_duration_s for e in probe.edit_list), Fraction(0)) / time_base
    video = table.video
    if video.duration_ts is not None:
        start = video.start_pts if video.start_pts is not None else 0
        return Fraction(start + video.duration_ts)
    return Fraction(max(table.video_pts, default=0))


def frame_end(probe: ProbeResult, table: PacketTable, last_pts: int) -> int:
    """Return the end time of the frame at ``last_pts``: the source's next pts, else its end.

    The sink sends this as the end sentinel, so the last frame written keeps its source
    duration, also when the caller stops early (a truncated source or a readable tail). The
    next pts comes from the sample table when it is known (``PacketTable.sample_pts``, which
    on a cut file names the samples past the cut too), else from the listed packets.

    Without a next pts, the end is the presentation end (:func:`presentation_end`). An edit
    list written in a movie timescale coarser than the track's (WP7.2: Insta360 Studio writes
    whole microseconds, rounded up from 1/30000 ticks) ends a fraction of a tick away from the
    track's own end (``start_pts + duration_ts``); when the two lie less than one tick apart
    and the track ends after ``last_pts``, the track's end wins, exact. Otherwise -- no track
    end known in these ticks, or an edit list that really trims the tail or runs past the
    media -- a fractional end is rounded up.

    Args:
        probe: The source's probe result.
        table: The source's packet table.
        last_pts: The pts of the last frame written, in ticks.

    Returns:
        The end in ticks; greater than ``last_pts`` whenever ``last_pts`` is a source pts and
        the presentation ends after the last source pts (both checked by the sink).
    """
    known = table.sample_pts if table.sample_pts is not None else table.video_pts
    later = [p for p in known if p > last_pts]
    if later:
        return min(later)
    end = presentation_end(probe, table)
    track = _track_end(probe, table)
    if track is not None and track > last_pts and abs(end - track) < 1:
        return track  # the edit list's end is the track's, rounded to a coarser movie tick
    whole = end.numerator // end.denominator
    if whole * end.denominator != end.numerator:
        whole += 1  # a fractional tick: the frame keeps at least its full source duration
    return whole


def _track_end(probe: ProbeResult, table: PacketTable) -> int | None:
    """Return the video track's own end in ticks (``start_pts + duration_ts``), or None.

    None when the stream gives no duration or counts it in ticks other than the probe's video
    time base (``presentation_end``'s unit). A missing start counts as 0, as there.
    """
    video = table.video
    if video.duration_ts is None or video.time_base != probe.video.time_base:
        return None
    return (video.start_pts if video.start_pts is not None else 0) + video.duration_ts


def readable_end(probe: ProbeResult, table: PacketTable, last_pts: int) -> int:
    """Return the end of the last readable frame of a cut-short source, in ticks (D86).

    A cut file's packet listing stops at the cut, so "the next pts" is the next pts in the
    source's own sample table (:func:`frame_end`), exact in ticks; the whole file's
    presentation end is used only when the sample table shows no later frame. The sink plans
    its cut with this and the fidelity instrument judges the output with it, so the two agree.

    Args:
        probe: The source's probe result.
        table: The source's packet table.
        last_pts: The pts of the last readable frame, in ticks.

    Returns:
        The end in ticks.

    Raises:
        VideoProbeError: ``"unreadable"`` when the sample table is unknown and the listing
            names no later frame, so where the frame ends cannot be told.
    """
    if table.sample_pts is None and not any(p > last_pts for p in table.video_pts):
        raise VideoProbeError(
            "unreadable",
            f"{ascii_text(probe.path.name)} is cut short, and where its last readable frame "
            "ends cannot be read from its sample table.",
        )
    return frame_end(probe, table, last_pts)


def readable_video_pts(probe: ProbeResult, source: PacketTable) -> tuple[int, ...]:
    """Return the source video pts an export writes, in presentation order (D86, Q-B).

    Every listed pts; for a source the probe found ``truncated``, the pts of the packets listed
    BEFORE its first corrupt packet in file (decode) order: the frames WP3.9's decoder yields
    before the cut. With B-frames that set is not "every pts below the corrupt packet's" (a
    P-frame decoded before the cut can lie after B-frames that come after it in the file;
    Reviewer B pass 2 #1). The sink plans the track cut at ``open`` from the same set.

    Args:
        probe: The source's probe result.
        source: The source's packet table.

    Returns:
        The pts in ticks, ascending, each once.
    """
    listed = list(source.video_pts)
    if any(fault.kind == "truncated" for fault in probe.faults):
        corrupt = set(source.video_corrupt_pts)
        cut = next((i for i, p in enumerate(listed) if p in corrupt), len(listed))
        listed = listed[:cut]
    return tuple(sorted(set(listed)))


def missing_frames(probe: ProbeResult, source: PacketTable, written: Sequence[int]) -> str | None:
    """Return why the frames written are not the source's whole readable video, or None.

    The frames written must be exactly :func:`readable_video_pts`. For a source the probe found
    ``unreadable_tail`` the decodable end cannot be told without decoding, so the frames written
    must be those pts up to the last one written, none skipped (an early stop there is the
    decoder's end, D86).

    Args:
        probe: The source's probe result.
        source: The source's packet table.
        written: The pts of every frame written, in ticks, ascending.

    Returns:
        The first missing pts and the counts, or None when nothing is missing or extra.
    """
    readable = readable_video_pts(probe, source)
    tail = any(fault.kind == "unreadable_tail" for fault in probe.faults)
    required = [p for p in readable if p <= written[-1]] if tail and written else list(readable)
    done = set(written)
    missing = [p for p in required if p not in done]
    extra = sorted(done.difference(readable))
    parts = []
    if missing:
        at = float(missing[0] * probe.video.time_base)
        scope = " up to the last frame written" if tail else ""
        parts.append(
            f"{len(missing)} of the source's {len(required)} readable frames{scope} were not "
            f"written (the first at pts {missing[0]}, {at:.6f} s; {len(written)} written)"
        )
    if extra:
        parts.append(
            f"{len(extra)} frames past the readable end were written (the first at pts {extra[0]})"
        )
    return "; ".join(parts) or None


def _edit_problems(out_path: Path, first: Fraction, end: Fraction) -> list[str]:
    """Check the output video's edit list against the written start and end, in seconds."""
    try:
        boxes = read_movie_boxes(out_path)
    except (BoxError, OSError) as error:
        return [f"the output's movie boxes cannot be read ({error})"]
    if boxes.movie_timescale is None:
        return ["the output has no movie header"]
    scale = boxes.movie_timescale
    entries = [
        (Fraction(e.segment_duration, scale), e.media_time == -1, e.media_rate) for e in boxes.edits
    ]
    expected = [(first, True, Fraction(1))] if first > 0 else []
    expected.append((end - first, False, Fraction(1)))
    if entries != expected:
        shown = [(str(d), "empty" if empty else "media", str(r)) for d, empty, r in entries]
        wanted = [(str(d), "empty" if empty else "media", str(r)) for d, empty, r in expected]
        return [f"video edit list {shown} where {wanted} was written"]
    return []


def check_output(
    out_path: Path,
    output: PacketTable,
    *,
    probe: ProbeResult,
    source: PacketTable,
    written: Sequence[int],
    end_pts: int,
    audio_end: Fraction | None,
) -> list[str]:
    """Compare a finished output with the source and the frames written (D94).

    Compressed audio retains every source packet's pts in order. Raw PCM retains its format,
    first pts, presented/stored sample totals and timeline runs, regardless of packet boundaries.
    With ``audio_end``, compare whole source packets starting before that point; a packet
    within :data:`CUT_SLACK_S` may go either way, always as a complete prefix.
    Only a truncated source with an audio cut uses complete readable sample frames (D86).

    Args:
        out_path: The output file (its edit list is read from its boxes).
        output: The output's packet table.
        probe: The source's probe result.
        source: The source's packet table.
        written: The pts of every frame written, in ticks, in order.
        end_pts: The end sentinel's pts (the end of the last frame).
        audio_end: Where the audio was cut, in seconds (a truncated source: the readable video
            end), or None when it was copied whole.

    Returns:
        One line per MANDATORY mismatch; empty when the output matches.
    """
    problems: list[str] = []
    time_base = probe.video.time_base
    video = output.video
    if video.time_base != time_base:
        problems.append(f"video time base {video.time_base} where {time_base} was written")
    if output.video_missing_pts:
        problems.append(f"{output.video_missing_pts} output video packets have no pts")
    got = sorted(output.video_pts)
    if len(got) != len(written):
        problems.append(f"{len(got)} video frames in the output where {len(written)} were written")
    elif got != list(written):
        at = next(i for i, (a, b) in enumerate(zip(got, written, strict=True)) if a != b)
        problems.append(f"video pts {got[at]} at frame {at} where {written[at]} was written")
    if written and video.start_pts != written[0]:
        problems.append(f"video start {video.start_pts} where {written[0]} was written")
    if written:
        problems += _edit_problems(out_path, written[0] * time_base, end_pts * time_base)
    rotation = int(video.rotation % 360) if video.rotation is not None else 0
    if rotation != probe.video.rotation:
        problems.append(f"display rotation {rotation} where the source has {probe.video.rotation}")
    source_audio, output_audio = source.of_type("audio"), output.of_type("audio")
    if len(source_audio) != len(output_audio):
        problems.append(
            f"{len(output_audio)} audio streams in the output where the source has "
            f"{len(source_audio)}"
        )
    for number, (src, out) in enumerate(zip(source_audio, output_audio, strict=False)):
        if src.codec_name.startswith("pcm_"):
            problems += _pcm_problems(
                number,
                src,
                out,
                source,
                output,
                audio_end,
                truncated=any(f.kind == "truncated" for f in probe.faults),
            ).problems
            continue
        problems += _audio_problems(
            number,
            _seconds(source.audio_pts.get(src.index, ()), src.time_base),
            _seconds(output.audio_pts.get(out.index, ()), out.time_base),
            audio_end,
        )
    return problems


@dataclass(frozen=True)
class _PcmExtent:
    """Exact sample totals and maximal timeline runs for one compared packet prefix."""

    totals: tuple[int, int]
    runs: tuple[tuple[Fraction, Fraction], ...]
    dropped_bytes: int = 0


@dataclass(frozen=True)
class _PcmResult:
    """Read-only PCM verdict, with a default-zero successful D86 partial-byte count."""

    problems: tuple[str, ...] = ()
    dropped_bytes: int = 0


def _pcm_totals(
    stream: StreamRow, table: PacketTable, count: int | None = None, *, d86: bool = False
) -> _PcmExtent | None:
    """Read exact totals/runs; only D86 source prefixes may floor their final packet.

    Each source packet presents min(declared, stored) sample frames under D86. Output
    packets always use strict declared durations and frame-aligned payloads. Runs use
    exact ticks, with effective durations only for the normalised source.
    """
    rate, base, channels = stream.sample_rate, stream.time_base, stream.channels
    if not rate or rate < 0 or base is None or base <= 0 or not channels or channels < 0:
        return None
    if stream.sample_fmt not in {
        "u8",
        "s16",
        "s32",
        "s64",
        "flt",
        "dbl",
        "u8p",
        "s16p",
        "s32p",
        "s64p",
        "fltp",
        "dblp",
    }:
        return None
    # Packed 24-bit PCM decodes to s32, but stores three bytes per channel sample.
    width = re.fullmatch(r"pcm_[suf](8|16|24|32|64)(?:le|be)?(?:_planar)?", stream.codec_name)
    if width is None:
        return None  # Block-packed/companded variants need their own exact payload rule.
    frame_bytes = int(width[1]) // 8 * channels
    pts = table.audio_pts.get(stream.index, ())[:count]
    durations = table.audio_durations.get(stream.index, ())[:count]
    sizes = table.audio_sizes.get(stream.index, ())[:count]
    if len(pts) != len(durations) or len(pts) != len(sizes) or any(p is None for p in pts):
        return None
    presented_total = stored_total = dropped_bytes = 0
    runs: list[tuple[Fraction, Fraction]] = []
    for i, (start, duration, size) in enumerate(zip(pts, durations, sizes, strict=True)):
        if start is None or duration is None or duration < 0 or size is None or size < 0:
            return None
        remainder = size % frame_bytes
        if remainder and not (d86 and i == len(pts) - 1):
            return None
        presented = duration * base * rate
        if presented.denominator != 1:
            return None
        stored = size // frame_bytes
        if d86:
            presented = min(presented, Fraction(stored))
        presented_total += int(presented)
        stored_total += stored
        dropped_bytes += remainder
        end = Fraction(start) + (presented / (base * rate) if d86 else duration)
        if runs and start == runs[-1][1]:
            runs[-1] = (runs[-1][0], end)
        else:
            runs.append((Fraction(start), Fraction(end)))
    return _PcmExtent((presented_total, stored_total), tuple(runs), dropped_bytes)


def _pcm_problems(
    number: int,
    src: StreamRow,
    out: StreamRow,
    source: PacketTable,
    output: PacketTable,
    end: Fraction | None,
    *,
    truncated: bool = False,
) -> _PcmResult:
    """Compare PCM format, exact paired totals and gap-preserving timeline runs.

    Run equality is in SOURCE ticks and depends on the equal-time-base requirement
    below; neither may be relaxed without the other. A run continues exactly when
    next_pts == pts + duration, using D86-normalised source durations only when the
    probe reports truncation AND the audio cut is set. Floor a partial sample frame
    only in the final source packet of the compared window; output remains strict.
    """
    label = f"audio stream {number} (PCM)"
    problems = []
    for name, expected, got in (
        ("codec", src.codec_name, out.codec_name),
        ("time base", src.time_base, out.time_base),
        ("sample rate", src.sample_rate, out.sample_rate),
        ("channel count", src.channels, out.channels),
        ("sample format", src.sample_fmt, out.sample_fmt),
    ):
        if expected != got:
            problems.append(
                f"{label}: {name} {ascii_text(str(got))} where the source has "
                f"{ascii_text(str(expected))}"
            )
    if problems:
        return _PcmResult(tuple(problems))
    src_pts = source.audio_pts.get(src.index, ())
    out_pts = output.audio_pts.get(out.index, ())
    if any(p is None for p in src_pts):
        return _PcmResult((f"{label}: missing source packet pts for the sample window",))
    if end is None:
        low = high = len(src_pts)
    else:
        timed = _seconds(src_pts, src.time_base)
        low = sum(p is not None and p < end - CUT_SLACK_S for p in timed)
        high = sum(p is not None and p < end + CUT_SLACK_S for p in timed)
    candidates = [
        _pcm_totals(src, source, count, d86=truncated and end is not None)
        for count in range(low, high + 1)
    ]
    source_extents = [extent for extent in candidates if extent is not None]
    out_extent = _pcm_totals(out, output)
    if not source_extents or out_extent is None:
        return _PcmResult(
            (f"{label}: missing or invalid evidence for exact presented/stored samples",)
        )
    # A straddling packet contributes its whole extent (normalised only under D86).
    # Slack admits whole prefixes only; both totals and runs must match the SAME prefix.
    wanted = [extent.totals for extent in source_extents]
    got_totals = out_extent.totals
    if got_totals not in wanted:
        for column, name in enumerate(("presented", "stored")):
            values = sorted({pair[column] for pair in wanted})
            if got_totals[column] not in values:
                expected_text = " or ".join(str(value) for value in values)
                problems.append(
                    f"{label}: {got_totals[column]} {name} samples in the output "
                    f"where the source has {expected_text}"
                )
        if not problems:
            problems.append(
                f"{label}: presented/stored samples {got_totals} do not match "
                f"one source packet prefix {wanted}"
            )
    if out_pts:
        if not src_pts or out_pts[0] != src_pts[0]:
            problems.append(
                f"{label}: first packet pts {out_pts[0]} where the source has "
                f"{src_pts[0] if src_pts else None}"
            )
    elif low:
        problems.append(f"{label}: missing first packet pts")
    matches = [extent for extent in source_extents if extent.totals == got_totals]
    same_runs = [extent for extent in matches if extent.runs == out_extent.runs]
    if matches and not same_runs:
        problems.append(f"{label}: output timeline runs do not match the source in source ticks")
    if problems:
        return _PcmResult(tuple(problems))
    return _PcmResult(dropped_bytes=same_runs[0].dropped_bytes)


def _seconds(pts: Sequence[int | None], time_base: Fraction | None) -> list[Fraction | None]:
    """Convert packet pts to seconds (ticks unchanged when the stream has no time base)."""
    scale = time_base if time_base is not None else Fraction(1)
    return [None if p is None else p * scale for p in pts]


def _audio_problems(
    number: int,
    source: Sequence[Fraction | None],
    output: Sequence[Fraction | None],
    end: Fraction | None,
) -> list[str]:
    """Check one audio stream's packet pts (seconds) against the source's, whole or cut."""
    if end is None:
        low = high = len(source)
    else:
        timed = [p for p in source if p is not None]
        low = sum(1 for p in timed if p < end - CUT_SLACK_S)
        high = sum(1 for p in timed if p < end + CUT_SLACK_S)
    wanted = str(low) if low == high else f"{low} to {high}"
    if not low <= len(output) <= high:
        return [
            f"audio stream {number}: {len(output)} packets in the output where {wanted} of the "
            f"source's {len(source)} were to be copied"
        ]
    if list(output) != list(source[: len(output)]):
        at = next(i for i, (a, b) in enumerate(zip(output, source, strict=False)) if a != b)
        return [
            f"audio stream {number}: packet {at} at {output[at]} s where the source has "
            f"{source[at]} s"
        ]
    return []


def not_carried(probe: ProbeResult, source: PacketTable, output: PacketTable) -> list[str]:
    """List the best-effort items of the source that the output does not carry (D105).

    A data track is compared by its codec tag and its sample count from the stream list; its
    packets are never listed.

    Args:
        probe: The source's probe result.
        source: The source's packet table.
        output: The output's packet table.

    Returns:
        User-readable names of the items not carried, in a fixed order.
    """
    missing: list[str] = []
    created = source.tags.get("creation_time")
    if created is not None and output.tags.get("creation_time") != created:
        missing.append("creation date and time")
    if "firmware" in source.tags and output.tags.get("firmware") != source.tags["firmware"]:
        missing.append("camera firmware tag")
    source_timecode = [s for s in source.of_type("data") if s.codec_tag == TIMECODE_TAG]
    output_timecode = [s for s in output.of_type("data") if s.codec_tag == TIMECODE_TAG]
    if source_timecode and len(output_timecode) < len(source_timecode):
        missing.append("timecode track")
    source_data = [s for s in source.of_type("data") if s.codec_tag != TIMECODE_TAG]
    output_data = [s for s in output.of_type("data") if s.codec_tag != TIMECODE_TAG]
    for number, src in enumerate(source_data):
        out = output_data[number] if number < len(output_data) else None
        if out is None or out.codec_tag != src.codec_tag:
            missing.append(f"data track {ascii_text(src.codec_tag)}")
        elif out.frames != src.frames:
            missing.append(
                f"data track {ascii_text(src.codec_tag)} ({out.frames} samples where the source "
                f"has {src.frames})"
            )
    if probe.gopro is not None:
        missing.append("camera settings atoms (moov/udta)")
    return missing
