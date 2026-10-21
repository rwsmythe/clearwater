"""The packet table the sink reads from a source and from its finished output (WP3.10, D94).

D94 says per-frame timestamps, start offset and edit list are "preserved and verified". The sink
reads one :class:`PacketTable` of the source when it opens (the per-frame pts the probe result
does not carry, the audio packets, the sample aspect ratio) and one of the output when it
closes, and :func:`check_output` compares the MANDATORY items it can see without decoding: the
frame count and every pts against the pts written, the video start, the video track's edit list
against the written start and end (its ``media_time`` is checked through its effect: the
demuxer applies it to every pts compared), the display rotation, and every audio packet's pts.
The full item-by-item comparison is the fidelity instrument's (``tools/video_fidelity.py``);
this check is what every export runs.

Each table is three ``ffprobe`` listings (no decode): the stream list with the few container
tags asked for by name (``creation_time`` and ``firmware``, so the best-effort report can say
whether they were carried; never a location tag), then the packets of the video stream, then
the packets of the audio streams. The packets of a data track (the camera's telemetry, the
timecode) are never listed: the listings select the video and audio streams only, and a data
track is judged from the stream list (its sample count) alone.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any

from clearwater.interfaces.video import ProbeResult
from clearwater.io.video.boxes import BoxError, read_movie_boxes
from clearwater.io.video.capability import tool_env
from clearwater.io.video.inputs import ascii_text
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
    "sample_aspect_ratio:stream_side_data=rotation:format_tags=creation_time,firmware"
)
_PACKET_ENTRIES = "packet=stream_index,pts,flags"
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
        packets: The number of packets listed: video and audio streams only; None for a stream
            whose packets are never listed (a data track).
        frames: The sample count the stream list gives (``nb_frames``, from the container's
            sample table, no packet read), or None.
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
    """

    streams: tuple[StreamRow, ...]
    video_index: int
    video_pts: tuple[int, ...]
    video_missing_pts: int
    video_corrupt_pts: tuple[int, ...]
    tags: Mapping[str, str]
    audio_pts: Mapping[int, tuple[int | None, ...]] = field(default_factory=dict)

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
            env=tool_env(),
        )
    except (OSError, subprocess.TimeoutExpired) as error:
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


def read_packet_table(path: Path, *, strict: bool = False) -> PacketTable:
    """List the stream facts and the video and audio packets of one file (no decode).

    Three ``ffprobe`` calls: the stream list, the video stream's packets, the audio streams'
    packets (skipped without audio). A data track's packets are never listed.

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
        )
        for s in raw_streams
        if (index := _int(s.get("index"))) is not None
    )
    tags = (document.get("format") or {}).get("tags") or {}
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
    audio_end: Fraction | None,
) -> list[str]:
    """Compare a finished output with the source and the frames written (D94).

    Every audio stream's packets must have the source's pts, in order: all of them, or with
    ``audio_end`` the source's packets before that point (a packet within
    :data:`CUT_SLACK_S` of it may go either way), never another subset.

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
        problems += _audio_problems(
            number,
            _seconds(source.audio_pts.get(src.index, ()), src.time_base),
            _seconds(output.audio_pts.get(out.index, ()), out.time_base),
            audio_end,
        )
    return problems


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
