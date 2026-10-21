"""The packet table the sink reads from a source and from its finished output (WP3.10, D94).

D94 says per-frame timestamps, start offset and edit list are "preserved and verified". The sink
reads one :class:`PacketTable` of the source when it opens (the per-frame pts the probe result
does not carry, the packet count of every stream, the sample aspect ratio) and one of the output
when it closes, and :func:`check_output` compares the MANDATORY items it can see without decoding:
the frame count and every pts against the pts written, the video start, the video track's edit
list against the written start and end, the display rotation, and the packet count of every
audio stream. The full item-by-item comparison is the fidelity instrument's
(``tools/video_fidelity.py``); this check is what every export runs.

Each read is one ``ffprobe`` packet listing (no decode); it names the fields it wants, and the
only tags it asks for are ``creation_time`` and ``firmware`` (so the best-effort report can say
whether they were carried), never a location tag.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

from clearwater.interfaces.video import ProbeResult
from clearwater.io.video.boxes import BoxError, read_movie_boxes
from clearwater.io.video.inputs import ascii_text
from clearwater.io.video.probe import VideoProbeError, find_tool

READ_TIMEOUT_S = 600
"""Seconds one packet listing may take (a long 4K clip lists in seconds; this is a backstop)."""

TIMECODE_TAG = "tmcd"
"""The codec tag of a timecode track; the MP4 muxer regenerates it rather than copying it."""

_ENTRIES = (
    "stream=index,codec_type,codec_tag_string,time_base,start_pts,duration_ts,"
    "sample_aspect_ratio:stream_side_data=rotation:format_tags=creation_time,firmware"
    ":packet=stream_index,pts,flags"
)
_RATIO = re.compile(r"^(\d+):(\d+)$")


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
        packets: The number of packets of the stream.
    """

    index: int
    codec_type: str
    codec_tag: str
    time_base: Fraction | None
    start_pts: int | None
    duration_ts: int | None
    sample_aspect_ratio: str | None
    rotation: Fraction | None
    packets: int


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
    """

    streams: tuple[StreamRow, ...]
    video_index: int
    video_pts: tuple[int, ...]
    video_missing_pts: int
    video_corrupt_pts: tuple[int, ...]
    tags: Mapping[str, str]

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


def read_packet_table(path: Path) -> PacketTable:
    """List the packets and stream facts of one file with one ``ffprobe`` call (no decode).

    Args:
        path: The file; opened read only.

    Returns:
        The table.

    Raises:
        VideoProbeError: ``"missing_tool"`` without ffprobe; ``"unreadable"`` when the listing
            fails or the file has no video stream.
    """
    name = ascii_text(path.name)
    command = [str(find_tool("ffprobe")), "-v", "error", "-of", "json"]
    command += ["-show_entries", _ENTRIES, str(path)]
    try:
        done = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=READ_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise VideoProbeError("unreadable", f"{name} could not be listed: {error}") from error
    try:
        data = json.loads(done.stdout.decode("utf-8", errors="replace"))
    except ValueError as error:
        raise VideoProbeError("unreadable", f"{name} could not be listed.") from error
    if not isinstance(data, dict):
        raise VideoProbeError("unreadable", f"{name} could not be listed.")
    counts: dict[int, int] = {}
    video_pts: list[int] = []
    corrupt: list[int] = []
    missing = 0
    raw_streams = [s for s in data.get("streams") or [] if isinstance(s, Mapping)]
    video_index = next(
        (_int(s.get("index")) for s in raw_streams if s.get("codec_type") == "video"), None
    )
    if video_index is None:
        raise VideoProbeError("unreadable", f"{name} has no video stream.")
    for packet in data.get("packets") or []:
        if not isinstance(packet, Mapping):
            continue
        index = _int(packet.get("stream_index"))
        if index is None:
            continue
        counts[index] = counts.get(index, 0) + 1
        if index != video_index:
            continue
        pts = _int(packet.get("pts"))
        if pts is None:
            missing += 1
            continue
        video_pts.append(pts)
        if "C" in str(packet.get("flags", "")):
            corrupt.append(pts)
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
            packets=counts.get(index, 0),
        )
        for s in raw_streams
        if (index := _int(s.get("index"))) is not None
    )
    tags = (data.get("format") or {}).get("tags") or {}
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
    )


def square_pixels(ratio: str | None) -> bool:
    """Return whether a sample aspect ratio is square (``1:1``) or unspecified (``0:1``, none).

    Args:
        ratio: The ratio as ffprobe prints it, or None.

    Returns:
        True for square or unspecified pixels.
    """
    if ratio is None:
        return True
    match = _RATIO.match(ratio)
    if match is None:
        return False
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
    duration, also when the caller stops early (a truncated source or a readable tail).

    Args:
        probe: The source's probe result.
        table: The source's packet table.
        last_pts: The pts of the last frame written, in ticks.

    Returns:
        The end in ticks; greater than ``last_pts`` whenever ``last_pts`` is a source pts and
        the presentation ends after the last source pts (both checked by the sink).
    """
    later = [p for p in table.video_pts if p > last_pts]
    if later:
        return min(later)
    end = presentation_end(probe, table)
    whole = end.numerator // end.denominator
    if whole * end.denominator != end.numerator:
        whole += 1  # a fractional tick: the frame keeps at least its full source duration
    return whole


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
    audio_cut: bool,
) -> list[str]:
    """Compare a finished output with the source and the frames written (D94).

    Args:
        out_path: The output file (its edit list is read from its boxes).
        output: The output's packet table.
        probe: The source's probe result.
        source: The source's packet table.
        written: The pts of every frame written, in ticks, in order.
        end_pts: The end sentinel's pts (the end of the last frame).
        audio_cut: Whether the audio was cut at the video end (a truncated source), so the
            output may hold fewer audio packets than the source.

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
        short = out.packets < src.packets if audio_cut else out.packets != src.packets
        if out.packets == 0 or short or out.packets > src.packets:
            problems.append(
                f"audio stream {number}: {out.packets} packets in the output where the source "
                f"has {src.packets}"
            )
        if not audio_cut and out.start_pts != src.start_pts:
            problems.append(
                f"audio stream {number}: start {out.start_pts} where the source has {src.start_pts}"
            )
    return problems


def not_carried(probe: ProbeResult, source: PacketTable, output: PacketTable) -> list[str]:
    """List the best-effort items of the source that the output does not carry (D105).

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
        elif out.packets != src.packets:
            missing.append(
                f"data track {ascii_text(src.codec_tag)} (only {out.packets} of {src.packets} "
                "packets)"
            )
    if probe.gopro is not None:
        missing.append("camera settings atoms (moov/udta)")
    return missing
