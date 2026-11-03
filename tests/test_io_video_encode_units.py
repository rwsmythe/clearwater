"""Unit tests of the WP3.10 encode side: carrier, capabilities, command, edit-list rule, checks.

These run no encode (the carrier and the capability parser use FFmpeg only for small reads).
The end-to-end tests are in ``test_io_video_encode.py``.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
import threading
import time
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from clearwater.interfaces.image import ColorDescription, Frame
from clearwater.interfaces.video import (
    EditEntry,
    EncoderCapability,
    Fault,
    GoProInfo,
    ProbeResult,
    SinkReport,
    VideoStreamInfo,
)
from clearwater.io.video import capability, encode, nut, verify
from clearwater.io.video.capability import resolve_encoder
from clearwater.io.video.encode import (
    PROVENANCE_MAX_BYTES,
    VideoEncodeError,
    encode_command,
    provenance_comment,
)
from clearwater.io.video.probe import VideoProbeError
from clearwater.io.video.verify import PacketTable, StreamRow

TB = Fraction(1, 30000)
AUDIO_PTS: tuple[int | None, ...] = tuple(range(0, 7 * 1024, 1024))


def _color(**changes: Any) -> ColorDescription:
    base = ColorDescription("bt709", "bt709", "bt709", "limited", 8, False, None)
    return replace(base, **changes)


def _probe(
    *,
    edits: tuple[EditEntry, ...] = (),
    rotation: int = 0,
    color: ColorDescription | None = None,
    faults: tuple[Fault, ...] = (),
    pix_fmt: str = "yuv420p",
    bit_depth: int = 8,
) -> ProbeResult:
    from clearwater.interfaces.video import AudioStreamInfo, DataStreamInfo

    video = VideoStreamInfo(
        codec="hevc",
        width=64,
        height=48,
        bit_depth=bit_depth,
        pix_fmt=pix_fmt,
        chroma_siting="left",
        color=color or _color(bit_depth=bit_depth),
        frame_rate=Fraction(30000, 1001),
        time_base=TB,
        nb_frames=4,
        rotation=rotation,
        vfr=False,
    )
    return ProbeResult(
        path=Path("src.mp4"),
        container="mov,mp4",
        duration_s=Fraction(4004, 30000),
        start_offset_s=Fraction(0),
        video=video,
        audio=(AudioStreamInfo(1, "aac", 48000, 2, Fraction(0)),),
        data=(DataStreamInfo(2, "tmcd"), DataStreamInfo(3, "gpmd")),
        edit_list=edits,
        faults=faults,
        gopro=None,
    )


def _table(
    pts: tuple[int, ...], *, sar: str | None = "1:1", corrupt: tuple[int, ...] = ()
) -> PacketTable:
    video = StreamRow(0, "video", "hvc1", TB, min(pts), 4004, sar, None, len(pts))
    audio = StreamRow(1, "audio", "mp4a", Fraction(1, 48000), 0, 6400, None, None, 7)
    return PacketTable(
        streams=(video, audio),
        video_index=0,
        video_pts=pts,
        video_missing_pts=0,
        video_corrupt_pts=corrupt,
        tags={},
        audio_pts={1: AUDIO_PTS},
    )


# --- the NUT carrier --------------------------------------------------------------------------


def test_crc32_matches_the_nut_polynomial_reference_value() -> None:
    # CRC-32/MPEG-2 has init 0xFFFFFFFF; NUT uses the same polynomial, MSB first, init 0.
    assert nut.crc32(b"") == 0
    assert nut.crc32(b"123456789") == 0x89A1897F


def test_frame_header_refuses_a_payload_the_sentinel_filter_would_drop() -> None:
    with pytest.raises(ValueError, match="under 2"):
        nut.frame_header(0, 1)
    with pytest.raises(ValueError, match="under 2"):
        nut.frame_header(0, 0)
    assert nut.frame_header(0, nut.MIN_FRAME_BYTES)


def test_negative_pts_and_bad_headers_are_refused() -> None:
    with pytest.raises(ValueError, match="negative"):
        nut.frame_header(-1, 100)
    with pytest.raises(ValueError, match="bit depth"):
        nut.stream_header(width=4, height=4, bit_depth=12, time_base=TB, frame_rate=Fraction(30))
    with pytest.raises(ValueError, match="empty"):
        nut.stream_header(width=0, height=4, bit_depth=8, time_base=TB, frame_rate=Fraction(30))
    with pytest.raises(ValueError, match="positive"):
        nut.stream_header(width=4, height=4, bit_depth=8, time_base=TB, frame_rate=Fraction(0))


def test_the_sentinel_filter_drops_only_payloads_under_two_bytes() -> None:
    assert "lt(size\\,2)" in nut.INPUT_BITSTREAM_FILTER
    assert nut.MIN_FRAME_BYTES == 2 and len(nut.SENTINEL_PAYLOAD) == 1


@pytest.mark.usefixtures("ffmpeg_tools")
@pytest.mark.parametrize("bit_depth", [8, 10])
def test_ffmpeg_reads_the_stream_with_exact_pts_durations_and_bytes(bit_depth: int) -> None:
    import hashlib
    import os

    width, height = 64, 48
    pts = [0, 1001, 3003, 4004, 9009]
    size = 3 * width * height * (2 if bit_depth == 10 else 1)
    frames = [os.urandom(size) for _ in pts]
    stream = nut.stream_header(
        width=width, height=height, bit_depth=bit_depth, time_base=TB, frame_rate=Fraction(30)
    )
    stream += b"".join(nut.frame_header(t, len(f)) + f for t, f in zip(pts, frames, strict=True))
    stream += nut.sentinel(11011)
    command = ["ffmpeg", "-v", "error", "-bsf:v", nut.INPUT_BITSTREAM_FILTER, "-f", "nut"]
    command += ["-i", "pipe:0", "-c:v", "rawvideo", "-fps_mode", "passthrough"]
    command += ["-enc_time_base:v", "demux", "-f", "framemd5", "pipe:1"]
    done = subprocess.run(command, input=stream, capture_output=True, check=True)
    rows = [
        [cell.strip() for cell in line.split(",")]
        for line in done.stdout.decode().splitlines()
        if not line.startswith("#")
    ]
    assert len(rows) == len(pts)  # the sentinel is dropped
    assert [int(r[2]) for r in rows] == pts
    assert [int(r[3]) for r in rows] == [1001, 2002, 1001, 5005, 2002]  # last ends at 11011
    assert [r[5] for r in rows] == [hashlib.md5(f).hexdigest() for f in frames]


@pytest.mark.usefixtures("ffmpeg_tools")
def test_the_info_packet_gives_ffmpeg_the_frame_rate() -> None:
    stream = nut.stream_header(
        width=16, height=16, bit_depth=8, time_base=TB, frame_rate=Fraction(30000, 1001)
    )
    stream += nut.frame_header(0, 768) + bytes(768) + nut.sentinel(1001)
    done = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-of",
            "json",
            "-show_entries",
            "stream=r_frame_rate",
            "-f",
            "nut",
            "pipe:0",
        ],
        input=stream,
        capture_output=True,
        check=True,
    )
    assert json.loads(done.stdout)["streams"][0]["r_frame_rate"] == "30000/1001"


# --- capabilities -----------------------------------------------------------------------------

LISTING = """Encoders:
 V..... = Video
 ------
 V....D libx265              libx265 H.265 / HEVC (codec hevc)
 V....D hevc_nvenc           NVIDIA NVENC hevc encoder (codec hevc)
 A....D aac                  AAC (Advanced Audio Coding)
"""


def _fake_run(outcomes: dict[tuple[str, int], tuple[int, str]], listing: str = LISTING) -> Any:
    def run(command: list[str]) -> tuple[int, str]:
        if "-encoders" in command:
            return 0, listing
        encoder = command[command.index("-c:v") + 1]
        depth = 10 if command[command.index("-profile:v") + 1] == "main10" else 8
        return outcomes[(encoder, depth)]

    return run


def test_capabilities_from_the_listing_and_the_test_encodes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outcomes = {
        ("hevc_nvenc", 8): (0, ""),
        ("hevc_nvenc", 10): (0, ""),
        ("libx265", 8): (0, ""),
        ("libx265", 10): (1, "10-bit not built"),
    }
    monkeypatch.setattr(capability, "_run", _fake_run(outcomes))
    nvenc, x265 = capability._detect(Path("ffmpeg"))
    assert nvenc == EncoderCapability("hevc_nvenc", True, None, (8, 10), True)
    assert x265 == EncoderCapability("libx265", True, None, (8,), False)


def test_no_nvidia_device_gives_a_readable_reason(monkeypatch: pytest.MonkeyPatch) -> None:
    failure = (1, "[hevc_nvenc @ 0x1] OpenEncodeSessionEx failed: no capable devices found (2)")
    outcomes = {
        ("hevc_nvenc", 8): failure,
        ("hevc_nvenc", 10): failure,
        ("libx265", 8): (0, ""),
        ("libx265", 10): (0, ""),
    }
    monkeypatch.setattr(capability, "_run", _fake_run(outcomes))
    nvenc, x265 = capability._detect(Path("ffmpeg"))
    assert not nvenc.available and nvenc.bit_depths == ()
    assert nvenc.reason is not None and "No NVIDIA graphics card" in nvenc.reason
    assert x265.available and x265.bit_depths == (8, 10)


def test_an_encoder_missing_from_the_build_is_named(monkeypatch: pytest.MonkeyPatch) -> None:
    listing = LISTING.replace(" V....D hevc_nvenc", " A....D not_video")
    outcomes = {("libx265", 8): (0, ""), ("libx265", 10): (0, "")}
    monkeypatch.setattr(capability, "_run", _fake_run(outcomes, listing))
    nvenc, _ = capability._detect(Path("ffmpeg"))
    assert nvenc.reason == "This FFmpeg build does not include the hevc_nvenc encoder."


def test_a_failed_listing_makes_every_encoder_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(capability, "_run", lambda command: (1, "boom"))
    caps = capability._detect(Path("ffmpeg"))
    assert [c.available for c in caps] == [False, False]
    assert all(c.reason and "could not list" in c.reason for c in caps)


def test_missing_ffmpeg_is_a_reason_not_an_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(name: str) -> Path:
        from clearwater.io.video import VideoProbeError

        raise VideoProbeError("missing_tool", "ffmpeg was not found on the PATH.")

    monkeypatch.setattr(capability, "find_tool", missing)
    caps = capability.detect_capabilities(refresh=True)
    assert all(not c.available and "not found" in (c.reason or "") for c in caps)


def test_detection_is_cached_per_process(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[Path] = []

    def detect(ffmpeg: Path) -> tuple[EncoderCapability, ...]:
        calls.append(ffmpeg)
        return (EncoderCapability("libx265", True, None, (8,), False),)

    monkeypatch.setattr(capability, "_detect", detect)
    monkeypatch.setattr(capability, "find_tool", lambda name: Path("/x/ffmpeg-cached-test"))
    first = capability.detect_capabilities()
    assert capability.detect_capabilities() is first
    capability.detect_capabilities(refresh=True)
    assert len(calls) == 2
    capability._cache.pop(str(Path("/x/ffmpeg-cached-test")), None)


def test_resolve_encoder_is_the_one_auto_rule() -> None:
    both = (
        EncoderCapability("hevc_nvenc", True, None, (8, 10), True),
        EncoderCapability("libx265", True, None, (8, 10), False),
    )
    no_gpu = (replace(both[0], available=False, reason="no card", bit_depths=()), both[1])
    assert resolve_encoder("auto", both) == "hevc_nvenc"
    assert resolve_encoder("auto", no_gpu) == "libx265"
    assert resolve_encoder("hevc_nvenc", no_gpu) == "hevc_nvenc"  # open refuses it, by name
    nothing = (no_gpu[0], replace(both[1], available=False, reason="broken", bit_depths=()))
    with pytest.raises(VideoEncodeError) as caught:
        resolve_encoder("auto", nothing)
    assert caught.value.kind == "unavailable" and "no card" in str(caught.value)
    with pytest.raises(VideoEncodeError) as caught:
        resolve_encoder("h264_nvenc", both)
    assert caught.value.kind == "refused"


# --- provenance -------------------------------------------------------------------------------


def test_provenance_is_compact_ascii_json() -> None:
    text = provenance_comment({"app_version": "1.0", "name": 'caf\u00e9 "x" \\ \n'})
    assert text.isascii()
    assert json.loads(text) == {"app_version": "1.0", "name": 'caf\u00e9 "x" \\ \n'}
    assert provenance_comment(None) == ""


@pytest.mark.parametrize(
    "bad",
    [{1: "x"}, {"a": {"b": {2.0: 1}}}, {"a": float("nan")}, {"a": math.inf}, {"a": object()}],
    ids=["int-key", "nested-float-key", "nan", "inf", "object"],
)
def test_provenance_json_cannot_hold_is_refused(bad: dict[Any, Any]) -> None:
    with pytest.raises(VideoEncodeError) as caught:
        provenance_comment(bad)
    assert caught.value.kind == "refused"


def test_provenance_over_16_kib_is_refused() -> None:
    assert provenance_comment({"a": "x" * (PROVENANCE_MAX_BYTES - 20)})
    with pytest.raises(VideoEncodeError, match="at most 16384"):
        provenance_comment({"a": "x" * PROVENANCE_MAX_BYTES})


# --- the command ------------------------------------------------------------------------------


def _command(probe: ProbeResult, **changes: Any) -> list[str]:
    options: dict[str, Any] = {
        "encoder": "libx265",
        "quality": "standard",
        "bit_depth": 8,
        "comment": "",
        "cut_at": None,
    }
    options.update(changes)
    return encode_command(Path("ffmpeg"), probe, Path("out.tmp"), **options)


def _after(command: list[str], option: str) -> str:
    return command[command.index(option) + 1]


def test_the_command_keeps_timing_and_writes_only_out_path() -> None:
    command = _command(_probe())
    assert command[-3:] == ["-f", "mp4", str(Path("out.tmp").absolute())] and "-y" in command
    for flag in ("-copyts", "-noautorotate", "-nostdin"):
        assert flag in command
    assert _after(command, "-fps_mode") == "passthrough"
    assert _after(command, "-enc_time_base:v") == "demux"
    assert _after(command, "-video_track_timescale") == "30000"
    assert _after(command, "-bsf:v") == nut.INPUT_BITSTREAM_FILTER
    assert command[command.index("pipe:0") - 3 : command.index("pipe:0")] == ["-f", "nut", "-i"]
    assert _after(command, "-movflags") == "+negative_cts_offsets"
    assert _after(command, "-tag:v") == "hvc1"
    assert "-display_rotation" not in command and "-to" not in command


def test_the_map_copies_audio_and_data_but_not_the_timecode_track() -> None:
    command = _command(_probe())
    maps = [command[i + 1] for i, a in enumerate(command) if a == "-map"]
    assert maps == ["0:v:0", "1:1", "1:3"]
    assert _after(command, "-c:a") == "copy" and _after(command, "-c:d") == "copy"
    assert _after(command, "-write_tmcd") == "1"
    assert _after(command, "-map_metadata") == "1"
    assert _after(command, "-map_metadata:s:v:0") == "1:s:v:0"


def test_rotation_is_set_on_the_frames_input_counter_clockwise() -> None:
    command = _command(_probe(rotation=90))
    at = command.index("-display_rotation")
    assert command[at + 1] == "90" and at < command.index("pipe:0")


@pytest.mark.parametrize(
    ("encoder", "quality", "depth", "expected"),
    [
        ("hevc_nvenc", "high", 8, ["-cq", "22", "-pix_fmt", "yuv420p", "-profile:v", "main"]),
        ("hevc_nvenc", "standard", 10, ["-cq", "26", "-pix_fmt", "p010le", "-profile:v", "main10"]),
        ("hevc_nvenc", "draft", 8, ["-cq", "30", "-pix_fmt", "yuv420p", "-profile:v", "main"]),
        ("libx265", "draft", 8, ["-crf", "30", "-pix_fmt", "yuv420p", "-profile:v", "main"]),
        ("libx265", "high", 10, ["-crf", "21", "-pix_fmt", "yuv420p10le", "-profile:v", "main10"]),
        ("libx265", "standard", 8, ["-crf", "26", "-pix_fmt", "yuv420p", "-profile:v", "main"]),
    ],
)
def test_quality_levels_follow_ad12(
    encoder: str, quality: str, depth: int, expected: list[str]
) -> None:
    command = _command(_probe(), encoder=encoder, quality=quality, bit_depth=depth)
    for option, value in zip(expected[::2], expected[1::2], strict=True):
        assert _after(command, option) == value
    if encoder == "hevc_nvenc":
        for option, value in (("-preset", "p5"), ("-tune", "hq"), ("-rc", "vbr"), ("-b:v", "0")):
            assert _after(command, option) == value
    else:
        assert _after(command, "-preset") == "medium"


NTSC = Fraction(30000, 1001)
MAIN_6_0 = (180, False)  # what GX011627 signals: level 6.0, Main tier
MAIN_2_0 = (60, False)  # what the 320x180 WP2.3 HEVC samples signal
QUALITIES = ("high", "standard", "draft")
UHD30 = [(59_660_019, "5.2"), (29_830_009, "5.1"), (14_915_004, "5.0")]
"""(maxrate, level) per quality at 3840x2160 and 30000/1001 fps, from the pixel rate alone."""


def _level(spec: tuple[int, bool] | None) -> Any:
    return verify.HevcLevel(*spec) if spec is not None else None


def _sized(width: int, height: int, rate: Fraction) -> ProbeResult:
    base = _probe()
    return replace(base, video=replace(base.video, width=width, height=height, frame_rate=rate))


@pytest.mark.parametrize(
    ("width", "height", "rate", "source", "expected"),
    [
        (3840, 2160, NTSC, MAIN_6_0, UHD30),
        (3840, 2160, NTSC, None, UHD30),
        (1920, 1080, NTSC, None, [(14_915_004, "4.1"), (7_457_502, "4.0"), (3_728_751, "4.0")]),
        (
            1920,
            1080,
            2 * NTSC,
            None,
            [(29_830_009, "5.1"), (14_915_004, "4.1"), (7_457_502, "4.1")],
        ),
        (320, 180, NTSC, MAIN_2_0, [(414_305, "2.0"), (207_152, "2.0"), (103_576, "2.0")]),
    ],
    ids=["4k30-hevc6.0", "4k30-h264", "1080p30", "1080p59.94", "320x180-hevc2.0"],
)
def test_nvenc_options_follow_the_pixel_rate_at_an_explicit_main_tier_level(
    width: int,
    height: int,
    rate: Fraction,
    source: Any,
    expected: list[tuple[int, str]],
) -> None:
    # High = 0.24 bit/pixel x the pixel rate, rounded down; Standard 1/2; Draft 1/4 (AD-12).
    for quality, (maxrate, level) in zip(QUALITIES, expected, strict=True):
        probe = _sized(width, height, rate)
        command = _command(
            probe, encoder="hevc_nvenc", quality=quality, source_level=_level(source)
        )
        assert _after(command, "-maxrate") == str(maxrate)
        assert _after(command, "-bufsize") == str(maxrate)
        assert _after(command, "-tier") == "main"
        assert _after(command, "-level") == level


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        # a planted low-level HEVC source: High is cut to level 5.1's Main-tier cap, then halved
        ((153, False), [(40_000_000, "5.1"), (20_000_000, "5.0"), (10_000_000, "5.0")]),
        # the High tier, or a level the table does not know: the pixel-rate ceiling alone
        ((153, True), UHD30),
        ((77, False), UHD30),
    ],
    ids=["main-5.1", "high-5.1", "unknown"],
)
def test_a_main_tier_source_level_caps_the_high_ceiling(
    source: Any, expected: list[tuple[int, str]]
) -> None:
    for quality, (maxrate, level) in zip(QUALITIES, expected, strict=True):
        rate = encode.nvenc_rate(3840, 2160, NTSC, quality, _level(source))
        assert (rate.maxrate, rate.bufsize, rate.level) == (maxrate, maxrate, level)


def test_nvenc_rate_refuses_a_picture_no_level_holds() -> None:
    with pytest.raises(ValueError, match="no HEVC level"):
        encode.nvenc_rate(16384, 16384, NTSC, "high", None)
    with pytest.raises(ValueError, match="not positive"):
        encode.nvenc_rate(320, 180, Fraction(0), "high", None)
    # a ceiling above every Main-tier cap that holds the picture is cut to the highest one
    rate = encode.nvenc_rate(3840, 2160, Fraction(240), "high", None)
    assert (rate.maxrate, rate.level) == (240_000_000, "6.2")


def test_libx265_has_no_rate_ceiling() -> None:
    command = _command(_sized(3840, 2160, NTSC), encoder="libx265", source_level=_level(MAIN_6_0))
    for option in ("-maxrate", "-bufsize", "-tier", "-level"):
        assert option not in command


@pytest.mark.parametrize(
    ("source", "output", "warned"),
    [
        (MAIN_2_0, (60, False), False),
        (MAIN_6_0, (156, False), False),
        (MAIN_2_0, (120, False), True),  # a higher level
        (MAIN_2_0, (60, True), True),  # the High tier over a Main-tier source
        ((153, True), (153, True), False),
        (None, (186, True), False),  # not an HEVC source
        (MAIN_2_0, None, False),  # the output's level not read
    ],
)
def test_a_higher_output_level_or_tier_is_warned(source: Any, output: Any, warned: bool) -> None:
    warning = encode.level_warning(_level(source), _level(output))
    assert (warning is not None) == warned
    if warning is not None:
        assert warning.isascii()
        assert _level(output).name in warning and _level(source).name in warning


def test_colour_tags_go_on_the_stream_and_the_frames() -> None:
    command = _command(_probe(color=_color(range="full"), pix_fmt="yuvj420p"))
    assert _after(command, "-color_primaries") == "bt709"
    assert _after(command, "-color_trc") == "bt709"
    assert _after(command, "-colorspace") == "bt709"
    assert _after(command, "-color_range") == "pc"
    vf = _after(command, "-vf")
    assert vf.endswith(",setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=pc")
    assert "out_range=pc" in vf


def test_provenance_and_the_truncation_cut_are_placed() -> None:
    command = _command(_probe(), comment='{"a":1}', cut_at=Fraction(1001, 1250))
    assert _after(command, "-metadata") == 'comment={"a":1}'
    at = command.index("-to")
    source = str(Path("src.mp4").absolute())
    assert command[at + 1] == "0.800800" and command[at + 2 : at + 4] == ["-i", source]
    assert _after(_command(_probe()), "-metadata") == "comment="


# --- the edit-list rule -----------------------------------------------------------------------

EMPTY = EditEntry(Fraction(1, 2), None, Fraction(1))


def _media(
    duration: Fraction, start: Fraction = Fraction(0), rate: Fraction = Fraction(1)
) -> EditEntry:
    return EditEntry(duration, start, rate)


@pytest.mark.parametrize(
    ("edits", "pts", "refusal"),
    [
        ((), (0, 1001, 2002), None),
        ((_media(Fraction(3003, 30000)),), (0, 1001, 2002), None),
        ((_media(Fraction(3003, 30000), Fraction(1, 15)),), (0, 1001, 2002), None),
        ((EMPTY, _media(Fraction(3003, 30000))), (15000, 16001, 17002), None),
        ((_media(Fraction(1, 10), rate=Fraction(2)),), (0, 1001), "changes the playback rate"),
        ((_media(Fraction(1, 10)), _media(Fraction(1, 10))), (0, 1001), "several segments"),
        ((EMPTY, EMPTY, _media(Fraction(1))), (30000,), "several segments"),
        ((_media(Fraction(1)), EMPTY), (0,), "several segments"),
        ((EMPTY, _media(Fraction(1))), (14000, 15000), "trims the start"),
        ((_media(Fraction(1, 30000)),), (0, 1001), "trims the end"),
    ],
    ids=[
        "absent",
        "identity",
        "reorder-delay",
        "empty-identity",
        "rate",
        "two-media",
        "two-empty",
        "empty-last",
        "head-trim",
        "tail-trim",
    ],
)
def test_edit_list_forms(
    edits: tuple[EditEntry, ...], pts: tuple[int, ...], refusal: str | None
) -> None:
    result = encode._edit_list_refusal(_probe(edits=edits), _table(pts))
    if refusal is None:
        assert result is None
    else:
        assert result is not None and refusal in result


@pytest.mark.parametrize(
    ("media_time", "earliest", "refused"),
    [
        (Fraction(0), 0, False),  # identity
        (Fraction(1, 15), 2000, False),  # AD-22's reorder delay
        (Fraction(1, 3), 0, True),  # a head trim that lands on a keyframe
        (Fraction(0), 2000, True),  # the presentation starts before the earliest frame
    ],
    ids=["identity", "reorder-delay", "keyframe-trim", "before-earliest"],
)
def test_the_media_segment_starts_at_the_earliest_composition_time(
    media_time: Fraction, earliest: int, refused: bool
) -> None:
    # Round-2 #2: a keyframe-aligned head trim passed open (its first pts equals the dwell).
    probe = _probe(edits=(_media(Fraction(4004, 30000), media_time),))
    samples = verify.SampleTable(30000, (earliest, earliest + 1001, earliest + 2002))
    result = encode._edit_list_refusal(probe, replace(_table((0, 1001, 2002)), samples=samples))
    if refused:
        assert result is not None and "earliest frame" in result
    else:
        assert result is None


# --- verify helpers ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("ratio", "square"),
    [(None, True), ("1:1", True), ("0:1", True), ("4:3", False), ("2:1", False), ("N/A", True)],
)
def test_square_pixels(ratio: str | None, square: bool) -> None:
    assert verify.square_pixels(ratio) is square


def test_frame_end_is_the_next_source_pts_else_the_presentation_end() -> None:
    probe = _probe(edits=(_media(Fraction(4004, 30000)),))
    table = _table((0, 2002, 1001, 3003))  # decode order with a B-frame
    assert verify.frame_end(probe, table, 1001) == 2002
    assert verify.frame_end(probe, table, 3003) == 4004
    no_edits = _probe()
    assert verify.frame_end(no_edits, table, 3003) == 0 + 4004  # start_pts + duration_ts
    odd = _probe(edits=(_media(Fraction(4004, 30000) + Fraction(1, 90000)),))
    assert verify.frame_end(odd, table, 3003) == 4005  # a fractional tick rounds up


def test_a_cut_files_frame_end_comes_from_its_sample_table() -> None:
    # Round-2 S1: the listing of a cut file stops at the cut; the sample table does not.
    probe = _probe(edits=(_media(Fraction(4004, 30000)),))
    cut = replace(_table((0, 1001)), sample_pts=(0, 1001, 2002, 3003))
    assert verify.frame_end(probe, cut, 1001) == 2002  # was 4004, the whole file's end
    assert verify.readable_end(probe, cut, 1001) == 2002
    assert verify.readable_end(probe, cut, 3003) == 4004  # the table's own last frame
    unknown = _table((0, 1001))
    with pytest.raises(VideoProbeError, match="cut short") as caught:
        verify.readable_end(probe, unknown, 1001)
    assert caught.value.kind == "unreadable"
    assert verify.readable_end(probe, _table((0, 1001, 2002)), 1001) == 2002  # listed: no table


def test_the_sample_table_maps_onto_the_listed_pts_by_one_offset() -> None:
    samples = verify.SampleTable(30000, (2002, 5005, 3003, 4004))  # decode order, B-frames
    assert verify._sample_pts(samples, (15000, 18003), 0, TB) == (15000, 18003, 16001, 17002)
    assert verify._sample_pts(samples, (15000, 18004), 0, TB) is None  # disagrees
    assert verify._sample_pts(samples, (15000,), 1, TB) is None  # a packet without a pts
    assert verify._sample_pts(samples, (15000,), 0, Fraction(1, 90000)) is None  # other ticks
    assert verify._sample_pts(samples, (), 0, TB) is None
    assert verify._sample_pts(None, (15000,), 0, TB) is None
    assert verify._sample_pts(samples, (0, 1, 2, 3, 4), 0, TB) is None  # more than the table
    assert samples.earliest == Fraction(2002, 30000)


def test_missing_frames_wants_the_whole_readable_video_in_any_listing_order() -> None:
    # Reviewer B pass 1 #1: the frames written must be the source's readable video.
    source = _table((0, 3003, 1001, 2002))  # decode order (B-frames)
    probe = _probe()
    assert verify.missing_frames(probe, source, [0, 1001, 2002, 3003]) is None
    gap = verify.missing_frames(probe, source, [0, 2002, 3003])
    assert gap is not None and "1 of the source's 4 readable frames" in gap
    assert "pts 1001," in gap and "3 written" in gap
    early = verify.missing_frames(probe, source, [0, 1001])
    assert early is not None and "2 of the source's 4" in early and "pts 2002," in early


def test_missing_frames_follows_the_cut_of_a_truncated_or_unreadable_source() -> None:
    truncated = _probe(faults=(Fault("truncated", "warn", "cut"),))
    # decode order with B-frames: the P-frame 6006 is listed (and decoded) before the corrupt
    # B-frame 5005 (Reviewer B pass 2 #1: the cut is in file order, not below the corrupt pts)
    cut = _table((0, 3003, 1001, 2002, 6006, 4004, 5005), corrupt=(5005,))
    readable = (0, 1001, 2002, 3003, 4004, 6006)
    assert verify.readable_video_pts(truncated, cut) == readable
    assert verify.missing_frames(truncated, cut, list(readable)) is None
    past = verify.missing_frames(truncated, cut, [*readable[:5], 5005, 6006])
    assert past is not None and "1 frames past the readable end" in past
    short = verify.missing_frames(truncated, cut, [0, 1001, 2002, 3003])
    assert short is not None and "pts 4004," in short
    tail = _probe(faults=(Fault("unreadable_tail", "warn", "tail"),))
    whole = _table((0, 1001, 2002, 3003))
    assert verify.missing_frames(tail, whole, [0, 1001]) is None  # the decoder's end (D86)
    skipped = verify.missing_frames(tail, whole, [0, 2002])
    assert skipped is not None and "up to the last frame written" in skipped
    assert "pts 1001," in skipped


def _out_table(
    pts: tuple[int, ...],
    audio: tuple[int | None, ...] = AUDIO_PTS,
    rotation: Fraction | None = None,
) -> PacketTable:
    table = _table(pts)
    video = replace(table.streams[0], rotation=rotation)
    stream = replace(table.streams[1], packets=len(audio))
    return replace(table, streams=(video, stream), audio_pts={1: audio})


def _check(output: PacketTable, audio_end: Fraction | None = None) -> list[str]:
    return verify.check_output(
        Path("o"),
        output,
        probe=_probe(),
        source=_table((0, 1001, 2002, 3003)),
        written=[0, 1001, 2002, 3003],
        end_pts=4004,
        audio_end=audio_end,
    )


def test_check_output_names_each_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(verify, "_edit_problems", lambda path, first, end: [])
    assert _check(_out_table((0, 2002, 1001, 3003))) == []
    cases = {
        "3 video frames": _out_table((0, 1001, 2002)),
        "video pts 1002": _out_table((0, 1002, 2002, 3003)),
        "display rotation 90": _out_table((0, 1001, 2002, 3003), rotation=Fraction(90)),
        "audio stream 0: 6 packets in the output where 7": _out_table(
            (0, 1001, 2002, 3003), AUDIO_PTS[:6]
        ),
        "audio stream 0: packet 2 at": _out_table(
            (0, 1001, 2002, 3003), (*AUDIO_PTS[:2], 2049, *AUDIO_PTS[3:])
        ),
    }
    for expected, output in cases.items():
        problems = _check(output)
        assert any(expected in p for p in problems), (expected, problems)


def test_a_cut_audio_stream_must_be_the_source_packets_before_the_cut(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Round-1 finding 6: a cut stream used to pass with ANY non-empty subset of the packets.
    monkeypatch.setattr(verify, "_edit_problems", lambda path, first, end: [])
    video = (0, 1001, 2002, 3003)
    between = Fraction(3500, 48000)  # packets 0, 1024, 2048 and 3072 lie before it
    assert _check(_out_table(video, AUDIO_PTS[:4]), between) == []
    for wrong in (AUDIO_PTS[:3], AUDIO_PTS[:5], AUDIO_PTS[:6]):
        problems = _check(_out_table(video, wrong), between)
        assert any("where 4 of the source's 7 were to be copied" in p for p in problems), problems
    skipped = (*AUDIO_PTS[:2], AUDIO_PTS[3], AUDIO_PTS[4])  # four packets, not the first four
    assert any("packet 2 at" in p for p in _check(_out_table(video, skipped), between))
    on_a_packet = Fraction(4096, 48000)  # a packet AT the cut may go either way (microseconds)
    assert _check(_out_table(video, AUDIO_PTS[:4]), on_a_packet) == []
    assert _check(_out_table(video, AUDIO_PTS[:5]), on_a_packet) == []
    problems = _check(_out_table(video, AUDIO_PTS[:3]), on_a_packet)
    assert any("where 4 to 5 of" in p for p in problems), problems


@dataclass(frozen=True)
class _PcmStreamRow(StreamRow):
    """Keep the explicit PCM defaults used by the original RED regression tables."""

    codec_name: str = "pcm_s16le"
    sample_rate: int | None = 48000
    channels: int | None = 1
    sample_fmt: str | None = "s16"


@dataclass(frozen=True)
class _PcmPacketTable(PacketTable):
    """Plant packet durations and payload sizes alongside the unchanged pts mapping."""

    audio_durations: Mapping[int, tuple[int | None, ...]] = field(default_factory=dict)
    audio_sizes: Mapping[int, tuple[int | None, ...]] = field(default_factory=dict)


def _pcm_table(
    durations: tuple[int, ...] = (1024,) * 7,
    *,
    last_stored_samples: int | None = None,
) -> _PcmPacketTable:
    """Build a mono s16 table with independently planted presentation and stored extents."""
    starts = [0]
    for duration in durations[:-1]:
        starts.append(starts[-1] + duration)
    sizes = [2 * duration for duration in durations]
    if last_stored_samples is not None:
        sizes[-1] = 2 * last_stored_samples
    base = _table((0, 1001, 2002, 3003))
    stream = _PcmStreamRow(
        index=1,
        codec_type="audio",
        codec_tag="lpcm",
        time_base=Fraction(1, 48000),
        start_pts=0,
        duration_ts=sum(durations),
        sample_aspect_ratio=None,
        rotation=None,
        packets=len(durations),
        frames=sum(sizes) // 2,
    )
    return _PcmPacketTable(
        streams=(base.video, stream),
        video_index=base.video_index,
        video_pts=base.video_pts,
        video_missing_pts=base.video_missing_pts,
        video_corrupt_pts=base.video_corrupt_pts,
        tags=base.tags,
        audio_pts={1: tuple(starts)},
        audio_durations={1: durations},
        audio_sizes={1: tuple(sizes)},
    )


def _pcm_check(
    monkeypatch: pytest.MonkeyPatch,
    source: _PcmPacketTable,
    output: _PcmPacketTable,
    end: Fraction | None = None,
    *,
    truncated: bool = False,
) -> list[str]:
    """Run the real mandatory check with only the unrelated file-box read stubbed."""
    from clearwater.interfaces.video import AudioStreamInfo

    monkeypatch.setattr(verify, "_edit_problems", lambda path, first, end: [])
    info = replace(_probe(), audio=(AudioStreamInfo(1, "pcm_s16le", 48000, 1, Fraction(0)),))
    if truncated:
        info = replace(info, faults=(Fault("truncated", "warn", "cut short"),))
    return verify.check_output(
        Path("o"),
        output,
        probe=info,
        source=source,
        written=[0, 1001, 2002, 3003],
        end_pts=4004,
        audio_end=end,
    )


def _assert_pcm_refusal(problems: list[str], *words: str) -> None:
    """Require a refusal to identify both the PCM rule and its failed comparison."""
    assert any(
        problem.startswith("audio stream 0 (PCM)") and all(word in problem for word in words)
        for problem in problems
    ), problems


def test_check_output_pcm_accepts_coalesced_packets(monkeypatch: pytest.MonkeyPatch) -> None:
    """Coalescing 100 packets into 99 preserves both presented and stored samples."""
    source = _pcm_table(
        (1024,) * 70 + (508,) + (1024,) * 23 + (736,) + (1024,) * 4 + (148,),
        last_stored_samples=240,
    )
    output = _pcm_table((1024,) * 70 + (508,) + (1024,) * 27 + (884,), last_stored_samples=976)
    assert sum(source.audio_durations[1]) == sum(output.audio_durations[1]) == 100720
    assert sum(source.audio_sizes[1]) // 2 == sum(output.audio_sizes[1]) // 2 == 100812
    assert source.audio_pts[1][-1] == 100572 and output.audio_pts[1][-1] == 99836
    problems = _pcm_check(monkeypatch, source, output)
    assert problems == [], problems


def test_check_output_pcm_accepts_moved_packet_boundaries(monkeypatch: pytest.MonkeyPatch) -> None:
    """A boundary moves by 1024 samples while both 133-packet totals remain exact."""
    source = _pcm_table(
        (1024,) * 70
        + (541,)
        + (1024,) * 23
        + (736,)
        + (1024,) * 23
        + (736,)
        + (1024,) * 13
        + (291,),
        last_stored_samples=305,
    )
    output = _pcm_table(
        (1024,) * 70
        + (541,)
        + (1024,) * 23
        + (736,)
        + (1024,) * 24
        + (736,)
        + (1024,) * 12
        + (291,),
        last_stored_samples=305,
    )
    assert sum(source.audio_durations[1]) == sum(output.audio_durations[1]) == 134400
    assert sum(source.audio_sizes[1]) // 2 == sum(output.audio_sizes[1]) // 2 == 134414
    assert source.audio_pts[1][119] == 120797 and output.audio_pts[1][119] == 121085
    problems = _pcm_check(monkeypatch, source, output)
    assert problems == [], problems


def test_check_output_pcm_regular_packets_are_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    """The existing regular-packet PCM control still passes."""
    assert _pcm_check(monkeypatch, _pcm_table(), _pcm_table()) == []


def test_check_output_pcm_refuses_one_sample_fewer(monkeypatch: pytest.MonkeyPatch) -> None:
    """Losing one presented and stored sample must name the failed sample count."""
    problems = _pcm_check(monkeypatch, _pcm_table(), _pcm_table((1024,) * 6 + (1023,)))
    _assert_pcm_refusal(problems, "presented", "7167", "7168")


def test_check_output_pcm_refuses_only_presented_samples_changed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A presentation trim changes even when all stored payload samples remain."""
    output = _pcm_table((1024,) * 6 + (1023,), last_stored_samples=1024)
    assert sum(output.audio_sizes[1]) // 2 == 7168
    problems = _pcm_check(monkeypatch, _pcm_table(), output)
    _assert_pcm_refusal(problems, "presented", "7167", "7168")


def test_check_output_pcm_refuses_only_stored_samples_changed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A lost payload sample is refused even when all presented durations remain."""
    output = _pcm_table(last_stored_samples=1023)
    assert sum(output.audio_durations[1]) == 7168
    problems = _pcm_check(monkeypatch, _pcm_table(), output)
    _assert_pcm_refusal(problems, "stored", "7167", "7168")


def test_check_output_pcm_refuses_another_sample_rate(monkeypatch: pytest.MonkeyPatch) -> None:
    """An unchanged packet list cannot conceal a changed sample rate."""
    output = _pcm_table()
    output = replace(output, streams=(output.video, replace(output.streams[1], sample_rate=44100)))
    problems = _pcm_check(monkeypatch, _pcm_table(), output)
    _assert_pcm_refusal(problems, "sample rate", "44100", "48000")


def test_check_output_pcm_refuses_another_sample_format(monkeypatch: pytest.MonkeyPatch) -> None:
    """The same pts and durations cannot conceal a different stored sample format."""
    output = _pcm_table()
    output = replace(output, streams=(output.video, replace(output.streams[1], sample_fmt="s32")))
    problems = _pcm_check(monkeypatch, _pcm_table(), output)
    _assert_pcm_refusal(problems, "sample format", "s32", "s16")


def test_check_output_pcm_refuses_another_first_pts(monkeypatch: pytest.MonkeyPatch) -> None:
    """A moved first packet must be refused by name under the PCM rule."""
    output = _pcm_table()
    output = replace(output, audio_pts={1: (1, *output.audio_pts[1][1:])})
    problems = _pcm_check(monkeypatch, _pcm_table(), output)
    _assert_pcm_refusal(problems, "first", "pts")


@pytest.mark.parametrize("samples", [1532, 1200, 1531], ids=["whole", "at-cut", "one-fewer"])
def test_check_output_pcm_cut_counts_the_whole_straddling_packet(
    monkeypatch: pytest.MonkeyPatch, samples: int
) -> None:
    """A start before the cut includes the whole packet in both sample totals."""
    source = _pcm_table((1024, 508, 1024))
    problems = _pcm_check(monkeypatch, source, _pcm_table((samples,)), Fraction(1200, 48000))
    if samples == 1532:
        assert problems == [], problems
    else:
        _assert_pcm_refusal(problems, "presented", str(samples), "1532")


@pytest.mark.parametrize("samples", [1024, 1532, 1025], ids=["drop", "keep", "partial"])
def test_check_output_pcm_cut_slack_allows_only_complete_packet_totals(
    monkeypatch: pytest.MonkeyPatch, samples: int
) -> None:
    """Cut slack permits whole source prefixes, not intermediate sample counts."""
    source = _pcm_table((1024, 508, 1024))
    problems = _pcm_check(monkeypatch, source, _pcm_table((samples,)), Fraction(1024, 48000))
    if samples in (1024, 1532):
        assert problems == [], problems
    else:
        _assert_pcm_refusal(problems, "presented", "1025")


@pytest.mark.parametrize(
    ("changes", "words"),
    [({"time_base": Fraction(1, 96000)}, ("time base",)), ({"channels": 2}, ("channel",))],
    ids=["time-base", "channels"],
)
def test_check_output_pcm_refuses_another_time_base_or_channel_count(
    monkeypatch: pytest.MonkeyPatch, changes: dict[str, Any], words: tuple[str, ...]
) -> None:
    """Both stream-clock and channel-count changes must identify the PCM rule."""
    output = _pcm_table()
    output = replace(output, streams=(output.video, replace(output.streams[1], **changes)))
    problems = _pcm_check(monkeypatch, _pcm_table(), output)
    _assert_pcm_refusal(problems, *words)


@pytest.mark.parametrize(
    "missing",
    ["duration", "size", "sample_rate", "time_base", "channels", "sample_fmt", "first_pts"],
)
def test_check_output_pcm_refuses_missing_sample_evidence(
    monkeypatch: pytest.MonkeyPatch, missing: str
) -> None:
    """Container aggregates must not hide unavailable packet or stream evidence."""
    output = _pcm_table()
    if missing == "duration":
        output = replace(output, audio_durations={1: (1024,) * 6 + (None,)})
    elif missing == "size":
        output = replace(output, audio_sizes={1: (2048,) * 6 + (None,)})
    elif missing == "first_pts":
        output = replace(output, audio_pts={1: (None, *output.audio_pts[1][1:])})
    else:
        output = replace(
            output, streams=(output.video, replace(output.streams[1], **{missing: None}))
        )
    problems = _pcm_check(monkeypatch, _pcm_table(), output)
    _assert_pcm_refusal(problems)


def test_check_output_pcm_cut_ignores_duration_and_size_after_the_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing facts in a packet excluded by the cut do not change its included prefix."""
    source = _pcm_table((1024, 508, 1024))
    source = replace(
        source,
        audio_durations={1: (1024, 508, None)},
        audio_sizes={1: (2048, 1016, None)},
    )
    assert _pcm_check(monkeypatch, source, _pcm_table((1532,)), Fraction(1200, 48000)) == []


def test_check_output_pcm_cut_requires_both_totals_from_the_same_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Slack cannot mix a dropped packet's presentation with a kept packet's payload."""
    source = _pcm_table((1024, 508, 1024))
    source = replace(source, audio_sizes={1: (2048, 1200, 2048)})
    output = _pcm_table((1024,), last_stored_samples=1624)
    problems = _pcm_check(monkeypatch, source, output, Fraction(1024, 48000))
    _assert_pcm_refusal(problems, "presented/stored", "prefix")


@pytest.mark.parametrize("invalid", ["negative-duration", "partial-sample", "fractional-duration"])
def test_check_output_pcm_refuses_inexact_sample_evidence(
    monkeypatch: pytest.MonkeyPatch,
    invalid: str,
) -> None:
    """Neither negative durations nor fractional sample frames are exact evidence."""
    source = _pcm_table()
    output = _pcm_table()
    if invalid == "negative-duration":
        output = replace(output, audio_durations={1: (1024,) * 6 + (-1,)})
    elif invalid == "partial-sample":
        output = replace(output, audio_sizes={1: (2048,) * 6 + (2047,)})
    else:
        source = replace(
            source, streams=(source.video, replace(source.streams[1], time_base=Fraction(1, 96000)))
        )
        output = replace(output, streams=source.streams, audio_durations={1: (1024,) * 6 + (1023,)})
    _assert_pcm_refusal(_pcm_check(monkeypatch, source, output), "evidence")


def _truncated_pcm_pair(percent: int) -> tuple[_PcmPacketTable, _PcmPacketTable, Fraction, int]:
    """Reproduce the three measured faststart EOF shapes without opening media."""
    count, size, end, samples = {
        55: (39, 909, Fraction(1001, 1250), 38814),
        70: (50, 860, Fraction(31031, 30000), 49502),
        85: (61, 647, Fraction(19019, 15000), 60659),
    }[percent]
    durations = ((1024,) * 23 + (472,)) * 3
    source = _pcm_table(durations[:count])
    source = replace(source, audio_sizes={1: (*source.audio_sizes[1][:-1], size)})
    out_durations = (
        (*durations[:47], 1024, 902) if percent == 70 else (*durations[: count - 1], size // 2)
    )
    return source, _pcm_table(out_durations), end, samples


@pytest.mark.parametrize("percent", [55, 70, 85])
def test_check_output_truncated_pcm_uses_complete_readable_tail(
    monkeypatch: pytest.MonkeyPatch, percent: int
) -> None:
    """D86 carries every whole readable frame, including a re-chunked short tail."""
    source, output, end, samples = _truncated_pcm_pair(percent)
    assert sum(output.audio_durations[1]) == samples
    assert _pcm_check(monkeypatch, source, output, end, truncated=True) == []


@pytest.mark.parametrize("percent", [55, 70, 85])
def test_check_output_truncated_pcm_refuses_one_readable_sample_fewer(
    monkeypatch: pytest.MonkeyPatch, percent: int
) -> None:
    """Normalising the EOF packet never excuses losing a complete readable sample."""
    source, output, end, samples = _truncated_pcm_pair(percent)
    last = output.audio_durations[1][-1]
    assert last is not None
    output = replace(
        output,
        audio_durations={1: (*output.audio_durations[1][:-1], last - 1)},
        audio_sizes={1: (*output.audio_sizes[1][:-1], 2 * (last - 1))},
    )
    problems = _pcm_check(monkeypatch, source, output, end, truncated=True)
    _assert_pcm_refusal(problems, "presented", str(samples - 1), str(samples))


@pytest.mark.parametrize("partial", ["earlier-source", "output"])
def test_check_output_truncated_pcm_refuses_other_partial_packets(
    monkeypatch: pytest.MonkeyPatch, partial: str
) -> None:
    """Only the final included SOURCE packet may discard an incomplete sample frame."""
    source, output, end, _ = _truncated_pcm_pair(70)
    if partial == "earlier-source":
        source = replace(source, audio_sizes={1: (2047, *source.audio_sizes[1][1:])})
    else:
        output = replace(output, audio_sizes={1: (*output.audio_sizes[1][:-1], 1803)})
    _assert_pcm_refusal(_pcm_check(monkeypatch, source, output, end, truncated=True), "evidence")


@pytest.mark.parametrize(("truncated", "cut"), [(False, False), (False, True), (True, False)])
def test_check_output_pcm_odd_source_requires_both_d86_conditions(
    monkeypatch: pytest.MonkeyPatch, truncated: bool, cut: bool
) -> None:
    """A cut alone or a truncated fault alone cannot enable the source-only exception."""
    source, output, end, _ = _truncated_pcm_pair(55)
    _assert_pcm_refusal(
        _pcm_check(monkeypatch, source, output, end if cut else None, truncated=truncated),
        "evidence",
    )


@pytest.mark.parametrize("change", ["shift-after-30", "all-zero", "closes-gap", "opens-gap"])
def test_check_output_pcm_refuses_changed_timeline_runs(
    monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    """Equal totals and first pts cannot conceal moved samples or a changed source gap."""
    source = _pcm_table(((1024,) * 23 + (472,)) * 3)
    output = source
    shifted = tuple(p if i <= 30 else p + 1024 for i, p in enumerate(source.audio_pts[1]))
    if change == "closes-gap":
        source = replace(source, audio_pts={1: shifted})
    elif change == "all-zero":
        output = replace(output, audio_pts={1: (0,) * 72})
    elif change == "opens-gap":
        gapful = tuple(p if i <= 10 else p + 512 for i, p in enumerate(source.audio_pts[1]))
        source = replace(source, audio_pts={1: gapful})
        output = replace(
            output,
            audio_pts={1: tuple(p if i <= 30 else p + 1024 for i, p in enumerate(gapful))},
        )
    else:
        output = replace(output, audio_pts={1: shifted})
    _assert_pcm_refusal(_pcm_check(monkeypatch, source, output), "timeline", "runs")


def test_check_output_pcm_accepts_same_gap_with_different_packet_boundaries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Gapful sources remain supported when output re-chunking preserves every run."""
    source = replace(_pcm_table((1024, 508, 1024)), audio_pts={1: (0, 1024, 2048)})
    output = replace(_pcm_table((1532, 512, 512)), audio_pts={1: (0, 2048, 2560)})
    assert _pcm_check(monkeypatch, source, output) == []


def test_check_output_pcm_accepts_the_manifest_packet_table(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The fixture's measured packet table is a pure-table timeline control."""
    manifest = json.loads((Path(__file__).parent / "fixtures/manifest.json").read_text())
    entry = next(row for row in manifest["samples"] if row["id"] == "vid-pcm-irregular")
    packets = entry["facts"]["audio"][0]["pcm"]["packets"]
    source = _pcm_table(tuple(p["duration"] for p in packets))
    source = replace(
        source,
        audio_pts={1: tuple(p["pts"] for p in packets)},
        audio_sizes={1: tuple(p["size"] for p in packets)},
    )
    assert _pcm_check(monkeypatch, source, source) == []


def test_not_carried_lists_best_effort_items() -> None:
    probe = _probe()
    source = replace(
        _table((0,)),
        streams=(
            *_table((0,)).streams,
            StreamRow(2, "data", "tmcd", Fraction(1, 30000), 0, 1, None, None, None, 1),
            StreamRow(3, "data", "meta", Fraction(1, 1000), 0, 1, None, None, None, 5),
        ),
        tags={"creation_time": "2026-01-01T00:00:00.000000Z", "firmware": "X"},
    )
    output = _table((0,))
    assert verify.not_carried(probe, source, output) == [
        "creation date and time",
        "camera firmware tag",
        "timecode track",
        "data track meta",
    ]
    assert verify.not_carried(probe, source, source) == []
    fewer = replace(source.streams[3], frames=3)
    partial = replace(source, streams=(*source.streams[:3], fewer))
    assert verify.not_carried(probe, source, partial) == [
        "data track meta (3 samples where the source has 5)"
    ]
    gopro = replace(probe, gopro=GoProInfo("F", True, "NATURAL"))
    assert verify.not_carried(gopro, source, source) == ["camera settings atoms (moov/udta)"]


# --- the listings: no data-track packet, no FFREPORT, a failed read-back ----------------------


@pytest.mark.usefixtures("ffmpeg_tools")
def test_the_listings_never_list_a_data_track_packet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Round-1 finding 1: one listing used to ask for the packets of EVERY stream.
    clip = tmp_path / "tc.mp4"
    subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "lavfi",
         "-i", "testsrc2=size=64x48:rate=30:duration=0.5", "-f", "lavfi",
         "-i", "sine=duration=0.5", "-c:v", "libx264", "-bf", "0", "-c:a", "aac",
         "-timecode", "01:00:00:00", str(clip)],
        check=True, capture_output=True,
    )  # fmt: skip
    commands: list[list[str]] = []
    real_run = subprocess.run

    def recording(command: list[str], **kwargs: Any) -> Any:
        commands.append(list(command))
        return real_run(command, **kwargs)

    monkeypatch.setattr(verify.subprocess, "run", recording)
    table = verify.read_packet_table(clip)
    data = table.of_type("data")
    assert [s.codec_tag for s in data] == ["tmcd"] and data[0].packets is None
    assert data[0].frames == 1  # the sample count from the stream list
    assert table.video.packets == 15 and table.of_type("audio")[0].packets
    listings = [c for c in commands if any("packet=" in a for a in c)]
    assert len(listings) == 2 and len(commands) == 3
    for command in listings:
        selected = command[command.index("-select_streams") + 1]
        assert selected in (str(table.video_index), "a"), command
    data_index = str(data[0].index)
    assert all(data_index != c[c.index("-select_streams") + 1] for c in listings)


def test_every_product_tool_process_runs_without_ffreport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Round-1 finding 9: FFREPORT makes FFmpeg and ffprobe write a report file of their own.
    monkeypatch.setenv("FFREPORT", "file=report.log")
    monkeypatch.setenv("ffreport", "file=report.log")
    assert all(key.upper() != "FFREPORT" for key in capability.tool_env())
    seen: list[dict[str, str] | None] = []

    def fake_run(command: list[str], **kwargs: Any) -> Any:
        seen.append(kwargs.get("env"))
        return subprocess.CompletedProcess(command, 0, b"{}", b"")

    monkeypatch.setattr(capability.subprocess, "run", fake_run)
    capability._run(["ffmpeg", "-version"])
    with pytest.raises(VideoProbeError, match="no video stream"):
        verify.read_packet_table(Path("x.mp4"))
    assert len(seen) == 2
    for env in seen:
        assert env is not None and all(key.upper() != "FFREPORT" for key in env)


def test_a_failed_output_listing_is_an_error_a_source_listing_is_not(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Round-1 finding 12: the read-back accepted the JSON of an ffprobe run that had failed.
    document = {"streams": [{"index": 0, "codec_type": "video"}], "packets": []}

    def failing(command: list[str], **kwargs: Any) -> Any:
        return subprocess.CompletedProcess(command, 1, json.dumps(document).encode(), b"")

    monkeypatch.setattr(verify.subprocess, "run", failing)
    assert verify.read_packet_table(Path("cut.mp4")).video_index == 0  # cut short: tolerated
    with pytest.raises(VideoProbeError, match="exit status 1"):
        verify.read_packet_table(Path("out.mp4"), strict=True)


# --- WP5.8: real pipe backpressure, with Python standing in for the encoder -------------------

_WATCHDOG_PAYLOAD_BYTES = 36 * 1024 * 1024
_WATCHDOG_READER = """
import os
import sys
import time
from pathlib import Path

def read_exact(count):
    while count:
        chunk = os.read(0, min(count, 65536))
        if not chunk:
            raise RuntimeError('unexpected end of frame pipe')
        count -= len(chunk)
"""


class _WatchdogSink(encode.FFmpegVideoSink):
    """Keep the real lifecycle and transport; substitute media payloads and the encoder."""

    def __init__(self, script: str, payload: bytes) -> None:
        super().__init__()
        self.script = script
        self.payload = payload

    def _command(self, command: list[str]) -> list[str]:
        return [sys.executable, "-c", self.script]

    def _payload(self, frame: Frame) -> tuple[int, bytes]:
        # Quantisation is unrelated to pipe backpressure; avoid a 144 MiB float32 image.
        assert frame.pts_ticks is not None
        return frame.pts_ticks, self.payload

    def _verify(self, end: int) -> SinkReport:
        # The Python child consumes counted bytes, not NUT, and cannot make an MP4.
        return SinkReport(len(self._written), (), ())


def _watchdog_header() -> bytes:
    probe = _probe()
    return nut.stream_header(
        width=probe.video.width,
        height=probe.video.height,
        bit_depth=8,
        time_base=TB,
        frame_rate=probe.video.frame_rate,
    )


def _watchdog_frame(index: int = 0) -> Frame:
    return Frame(
        pixels=np.zeros((1, 1, 3), dtype=np.float32),
        color=_color(),
        orientation_applied=False,
        device="cpu",
        pts=index * 1001 * TB,
        pts_ticks=index * 1001,
        time_base=TB,
        index=index,
    )


def _watchdog_wait(path: Path, timeout: float = 1.0) -> bool:
    deadline = time.monotonic() + timeout
    while not path.exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    return path.exists()


@contextmanager
def _watchdog_encoder(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    body: str,
    *,
    count: int = 1,
) -> Iterator[tuple[_WatchdogSink, Path, threading.Event]]:
    """Run a real Python child with a four-second rescue independent of the product watcher."""
    pts = tuple(index * 1001 for index in range(count))
    source = _table(pts)
    source = replace(
        source,
        streams=(replace(source.video, duration_ts=count * 1001), *source.streams[1:]),
    )
    monkeypatch.setattr(encode, "read_packet_table", lambda *args, **kwargs: source)
    monkeypatch.setattr(encode, "find_tool", lambda name: Path(sys.executable))
    # raising=False permits the RED run against the unchanged module.
    monkeypatch.setattr(encode, "STALL_TIMEOUT_S", 1.0, raising=False)
    sink = _WatchdogSink(_WATCHDOG_READER + body, bytes(_WATCHDOG_PAYLOAD_BYTES))
    monkeypatch.setattr(
        sink, "capabilities", lambda: (EncoderCapability("libx265", True, None, (8,), False),)
    )
    out = tmp_path / "partial.mp4"
    out.write_bytes(b"partial output")
    rescued = threading.Event()

    def rescue() -> None:
        rescued.set()
        process = sink._process
        if process is not None and process.poll() is None:
            process.kill()

    timer = threading.Timer(4.0, rescue)
    timer.daemon = True
    timer.start()
    try:
        sink.open(
            _probe(), out, encoder="libx265", quality="standard", bit_depth=8, provenance=None
        )
        yield sink, out, rescued
    finally:
        timer.cancel()
        process = sink._process
        if process is not None and process.poll() is None:
            process.kill()
        sink.abort()
        timer.join(timeout=0.5)


def test_watchdog_stalled_frame_fails_and_removes_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A live encoder that stops reading a pipe-filling frame fails before the rescue."""
    first = len(_watchdog_header()) + len(nut.frame_header(0, _WATCHDOG_PAYLOAD_BYTES)) + 4096
    with _watchdog_encoder(tmp_path, monkeypatch, f"\nread_exact({first})\ntime.sleep(60)\n") as (
        sink,
        out,
        rescued,
    ):
        process = sink._process
        assert process is not None
        timeline: dict[str, float | None] = {}
        kill = process.kill
        remove = encode._remove

        def timed_kill() -> None:
            timeline["watcher_kill"] = time.monotonic()
            timeline["waiting_since"] = getattr(sink, "_waiting_since", None)
            kill()

        def timed_remove(path: Path) -> None:
            remove(path)
            timeline["output_deleted"] = time.monotonic()

        monkeypatch.setattr(process, "kill", timed_kill)
        monkeypatch.setattr(encode, "_remove", timed_remove)
        started = time.monotonic()
        with pytest.raises(VideoEncodeError) as caught:
            sink.write(_watchdog_frame())
        timeline["writer_error_observed"] = time.monotonic()
        assert caught.value.kind == "encoder_failed"
        assert "stopped accepting frames" in str(caught.value)
        assert "libx265" in str(caught.value)
        assert not rescued.is_set() and time.monotonic() - started < 5
        assert not out.exists() and process.poll() is not None
        assert sink._watchdog_thread is not None and not sink._watchdog_thread.is_alive()
        (tmp_path / "timeline.json").write_text(json.dumps(timeline), encoding="ascii")


def test_watchdog_healthy_slow_encoder_completes_six_frames(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Six 0.3-second frame reads remain healthy although their total exceeds the threshold."""
    sizes = [
        len(nut.frame_header(index * 1001, _WATCHDOG_PAYLOAD_BYTES)) + _WATCHDOG_PAYLOAD_BYTES
        for index in range(6)
    ]
    body = (
        f"\nread_exact({len(_watchdog_header())})\n"
        f"for size in {sizes!r}:\n    time.sleep(0.3)\n    read_exact(size)\n"
        "while os.read(0, 65536):\n    pass\n"
    )
    with _watchdog_encoder(tmp_path, monkeypatch, body, count=6) as (sink, out, rescued):
        for index in range(6):
            sink.write(_watchdog_frame(index))
        assert sink.close().frames_written == 6
        assert getattr(sink, "_stalled", None) is None
        assert not rescued.is_set() and out.exists()
        watcher = getattr(sink, "_watchdog_thread", None)
        assert watcher is None or not watcher.is_alive()


def test_watchdog_stalled_sentinel_fails_before_finish_timeout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Append an invalid 36 MiB tail to the sentinel solely to fill the fake reader's pipe.

    The Python child parses no NUT; a real sentinel is too small to force backpressure after
    all frames have been read. Only this test replaces the sentinel bytes (CHARC R2).
    """
    consumed = (
        len(_watchdog_header())
        + len(nut.frame_header(0, _WATCHDOG_PAYLOAD_BYTES))
        + _WATCHDOG_PAYLOAD_BYTES
    )
    sentinel = nut.sentinel
    monkeypatch.setattr(nut, "sentinel", lambda pts: sentinel(pts) + bytes(_WATCHDOG_PAYLOAD_BYTES))
    body = f"\nread_exact({consumed})\ntime.sleep(60)\n"
    with _watchdog_encoder(tmp_path, monkeypatch, body) as (sink, out, rescued):
        sink.write(_watchdog_frame())
        started = time.monotonic()
        with pytest.raises(VideoEncodeError) as caught:
            sink.close()
        assert caught.value.kind == "encoder_failed"
        assert "stopped accepting frames" in str(caught.value)
        assert "libx265" in str(caught.value)
        assert not rescued.is_set() and time.monotonic() - started < 5 < encode.FINISH_TIMEOUT_S
        assert not out.exists()
        assert sink._process is not None and sink._process.poll() is not None


def test_watchdog_normal_nonzero_exit_keeps_status_and_stderr(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An ordinary exit during a frame retains the existing error instead of a stall report."""
    consumed = len(_watchdog_header()) + len(nut.frame_header(0, _WATCHDOG_PAYLOAD_BYTES)) + 4096
    body = (
        f"\nread_exact({consumed})\n"
        "sys.stderr.write('fake encoder exit witness\\n')\nsys.stderr.flush()\nsys.exit(7)\n"
    )
    with _watchdog_encoder(tmp_path, monkeypatch, body) as (sink, out, rescued):
        with pytest.raises(VideoEncodeError) as caught:
            sink.write(_watchdog_frame())
        assert caught.value.kind == "encoder_failed"
        assert "exit status 7" in str(caught.value)
        assert "fake encoder exit witness" in str(caught.value)
        assert "stopped accepting frames" not in str(caught.value)
        assert getattr(sink, "_stalled", None) is None
        assert not rescued.is_set() and not out.exists()


def test_watchdog_abort_during_wait_joins_watcher_without_thread_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cancellation releases a blocked writer and joins the watcher without a thread exception."""
    ready = tmp_path / "reader-stopped"
    consumed = len(_watchdog_header()) + len(nut.frame_header(0, _WATCHDOG_PAYLOAD_BYTES)) + 4096
    body = f"\nread_exact({consumed})\nPath({str(ready)!r}).touch()\ntime.sleep(60)\n"
    thread_errors: list[threading.ExceptHookArgs] = []
    monkeypatch.setattr(threading, "excepthook", thread_errors.append)
    with _watchdog_encoder(tmp_path, monkeypatch, body) as (sink, out, rescued):
        errors: list[BaseException] = []

        def write_frame() -> None:
            try:
                sink.write(_watchdog_frame())
            except BaseException as error:
                errors.append(error)

        writer = threading.Thread(target=write_frame, daemon=True)
        writer.start()
        try:
            assert _watchdog_wait(ready) and writer.is_alive()
            sink.abort()
        finally:
            if sink._process is not None and sink._process.poll() is None:
                sink._process.kill()
            writer.join(timeout=1)
        assert not writer.is_alive() and errors and isinstance(errors[0], VideoEncodeError)
        assert not thread_errors and not rescued.is_set() and not out.exists()
        assert sink._process is not None and sink._process.poll() is not None
        watcher = getattr(sink, "_watchdog_thread", None)
        assert watcher is not None, "abort must stop the started watchdog thread"
        assert not watcher.is_alive()


def test_watchdog_small_send_flushes_before_another_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A frame header smaller than Python's buffer reaches the child without another write."""
    ready = tmp_path / "header-read"
    header = nut.frame_header(0, _WATCHDOG_PAYLOAD_BYTES)
    consumed = len(_watchdog_header()) + len(header)
    body = f"\nread_exact({consumed})\nPath({str(ready)!r}).touch()\ntime.sleep(60)\n"
    with _watchdog_encoder(tmp_path, monkeypatch, body) as (sink, _out, rescued):
        sink._send(header)
        assert _watchdog_wait(ready), "small _send was buffered instead of readable by the encoder"
        assert not rescued.is_set()
