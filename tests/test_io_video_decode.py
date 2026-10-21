"""Video decode (WP3.9): frames, pts, pixels and seeking on the WP2.3 samples.

- Every decodable sample yields its manifest frame count and tick list (DR-36 (b): the decoded
  ticks hash to ``facts.pts.sha256``), at its size and bit depth, with the probe's colour.
- The pixels equal an independent FFmpeg run of the same filter (V4 / V9 decode leg); 10-bit
  stays 10-bit.
- The probe's colour description is used as given, never re-probed (D54).
- HLG and PQ are refused before FFmpeg starts; the truncated sample ends cleanly (D86).
- Seeking is frame-exact at, between, before and after pts, also with a non-zero start.
- DR-39 (c) decode rows, and a path holding ``%`` and non-ASCII characters (DR-20 (3)).
"""

from __future__ import annotations

import dataclasses
import hashlib
import importlib
import shutil
import subprocess
from collections.abc import Callable
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from clearwater.color import decode_filter, rgb_frame_bytes, rgb_to_planes
from clearwater.interfaces.image import Frame
from clearwater.interfaces.video import ProbeResult, VideoSource
from clearwater.io.video import FFmpegVideoSource, VideoDecodeError, probe
from clearwater.io.video import decode as decode_module

pytestmark = pytest.mark.usefixtures("ffmpeg_tools")

DECODABLE = [
    "vid-hevc8-bt709-full",
    "vid-hevc10",
    "vid-untagged",
    "vid-truncated",
    "vid-vfr",
    "vid-rotated",
]
INTACT = [sample_id for sample_id in DECODABLE if sample_id != "vid-truncated"]
REFUSED = ["vid-hlg", "vid-pq"]

SOURCE = FFmpegVideoSource()


def decode_all(result: ProbeResult, **kwargs: Any) -> list[Frame]:
    """Decode every frame of a probed file in software."""
    return list(SOURCE.frames(result, hw_decode=False, **kwargs))


def reference_planes(
    result: ProbeResult, out_dir: Path, *, filter_text: str | None = None
) -> list[bytes]:
    """Decode with an independent FFmpeg command to a raw file and split it into frames."""
    raw = out_dir / "reference.raw"
    command = [
        "ffmpeg",
        "-nostdin",
        "-v",
        "error",
        "-noautorotate",
        "-i",
        str(result.path),
        "-map",
        "0:v:0",
        "-vf",
        filter_text if filter_text is not None else decode_filter(result.video),
        "-fps_mode",
        "passthrough",
        "-f",
        "rawvideo",
        "-y",
        str(raw),
    ]
    subprocess.run(command, check=True, capture_output=True, timeout=120)
    data = raw.read_bytes()
    video = result.video
    size = rgb_frame_bytes(video.width, video.height, video.bit_depth)
    assert len(data) % size == 0
    return [data[at : at + size] for at in range(0, len(data), size)]


def planes(frame: Frame) -> bytes:
    """Recover the integer planes of a decoded frame (exact, see ``planes_to_rgb``)."""
    return rgb_to_planes(frame.pixels, bit_depth=frame.color.bit_depth)


def ticks_of(entry: dict[str, Any]) -> list[int]:
    """The manifest's decodable tick list of a sample."""
    facts = entry["facts"]
    return list(facts["pts"]["ticks"][: facts["decoded"]["frames"]])


def test_the_source_satisfies_the_if5_protocol() -> None:
    assert isinstance(SOURCE, VideoSource)


@pytest.mark.parametrize("sample_id", DECODABLE)
def test_every_decodable_sample_yields_its_manifest_frames_and_ticks(
    sample_id: str,
    sample: Callable[[str], Path],
    sample_entry: Callable[[str], dict[str, Any]],
) -> None:
    entry = sample_entry(sample_id)
    result = probe(sample(sample_id))
    frames = decode_all(result)
    facts = entry["facts"]
    ticks = [frame.pts_ticks for frame in frames]
    assert len(frames) == facts["decoded"]["frames"]
    assert ticks == ticks_of(entry)
    video = facts["video"]
    for index, frame in enumerate(frames):
        assert frame.pixels.shape == (video["height"], video["width"], 3)
        assert frame.pixels.dtype == np.float32
        assert frame.time_base == result.video.time_base == Fraction(1, 30000)
        assert frame.pts == frame.pts_ticks * frame.time_base
        assert isinstance(frame.pts, Fraction)
        assert frame.index == index
        assert frame.device == "cpu"
        assert frame.orientation_applied is False
        assert frame.color is result.video.color
        assert frame.color.bit_depth == video["bit_depth"]
    assert float(frames[0].pixels.min()) >= 0.0 and float(frames[0].pixels.max()) <= 1.0


@pytest.mark.parametrize("sample_id", INTACT)
def test_the_decoded_ticks_hash_to_the_manifest_packet_hash(
    sample_id: str,
    sample: Callable[[str], Path],
    sample_entry: Callable[[str], dict[str, Any]],
) -> None:
    frames = decode_all(probe(sample(sample_id)))
    joined = ",".join(str(frame.pts_ticks) for frame in frames)
    assert (
        hashlib.sha256(joined.encode("ascii")).hexdigest()
        == (sample_entry(sample_id)["facts"]["pts"]["sha256"])
    )


@pytest.mark.parametrize("sample_id", DECODABLE)
def test_the_pixels_equal_an_independent_ffmpeg_run(
    sample_id: str, sample: Callable[[str], Path], tmp_path: Path
) -> None:
    result = probe(sample(sample_id))
    frames = decode_all(result)
    reference = reference_planes(result, tmp_path)
    assert len(frames) == len(reference)
    for frame, expected in zip(frames, reference, strict=True):
        assert planes(frame) == expected


def test_ten_bit_stays_ten_bit(sample: Callable[[str], Path]) -> None:
    result = probe(sample("vid-hevc10"))
    frame = next(iter(SOURCE.frames(result, hw_decode=False)))
    codes = np.unique(np.rint(frame.pixels * 1023).astype(np.int64))
    # An 8-bit path gives at most 256 levels per channel; 10-bit data gives more.
    assert len(codes) > 256
    # Only 0, 341, 682 and 1023 are 10-bit codes that an 8-bit level k/255 can land on.
    assert set(codes.tolist()) - {0, 341, 682, 1023}


def test_the_vfr_sample_yields_exactly_its_intended_frames(
    sample: Callable[[str], Path], sample_entry: Callable[[str], dict[str, Any]]
) -> None:
    intended = sample_entry("vid-vfr")["facts"]["pts_ticks_intended"]
    ticks = [frame.pts_ticks for frame in decode_all(probe(sample("vid-vfr")))]
    assert ticks == intended
    assert len(ticks) == 30 and len(set(ticks)) == 30


def test_the_truncated_sample_yields_its_readable_frames_then_ends(
    sample: Callable[[str], Path],
) -> None:
    result = probe(sample("vid-truncated"))
    assert [fault.kind for fault in result.faults] == ["truncated"]
    stream = SOURCE.frames(result, hw_decode=False)
    frames = list(stream)
    assert len(frames) == 24
    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize("sample_id", REFUSED)
def test_hlg_and_pq_are_refused_before_ffmpeg_starts(
    sample_id: str, sample: Callable[[str], Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    result = probe(sample(sample_id))

    def no_process(*args: object, **kwargs: object) -> None:
        raise AssertionError("a process was started")

    monkeypatch.setattr(decode_module.subprocess, "Popen", no_process)
    monkeypatch.setattr(decode_module.subprocess, "run", no_process)
    with pytest.raises(VideoDecodeError) as caught:
        SOURCE.frames(result, hw_decode=True)
    assert caught.value.kind == "refused"
    assert str(caught.value).isascii()


def test_the_rotated_sample_keeps_its_stored_pixels(sample: Callable[[str], Path]) -> None:
    result = probe(sample("vid-rotated"))
    assert result.video.rotation == 90
    frames = decode_all(result)
    assert len(frames) == 45
    assert all(frame.pixels.shape == (180, 320, 3) for frame in frames)
    assert all(frame.orientation_applied is False for frame in frames)


# --- D54: the colour description is the probe's, never re-probed ---------------------------------


def test_the_colour_description_given_is_used_and_nothing_is_re_probed(
    sample: Callable[[str], Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = probe(sample("vid-untagged"))
    assert (result.video.color.range, result.video.color.assumed) == ("limited", True)
    color = dataclasses.replace(result.video.color, range="full")
    altered = dataclasses.replace(result, video=dataclasses.replace(result.video, color=color))

    probe_module = importlib.import_module("clearwater.io.video.probe")

    def no_ffprobe(*args: object, **kwargs: object) -> None:
        raise AssertionError("ffprobe was run during a decode")

    monkeypatch.setattr(probe_module, "_run_ffprobe", no_ffprobe)
    limited = [planes(frame) for frame in decode_all(result)]
    full = [planes(frame) for frame in decode_all(altered)]
    assert all(frame.color is color for frame in decode_all(altered))
    assert limited != full
    assert full == reference_planes(altered, tmp_path, filter_text=decode_filter(altered.video))
    (tmp_path / "limited").mkdir()
    assert limited == reference_planes(result, tmp_path / "limited")


# --- seeking -----------------------------------------------------------------------------------


@pytest.mark.parametrize("sample_id", ["vid-vfr", "vid-hevc8-bt709-full"])
def test_start_at_every_pts_yields_from_that_frame(
    sample_id: str,
    sample: Callable[[str], Path],
    sample_entry: Callable[[str], dict[str, Any]],
) -> None:
    result = probe(sample(sample_id))
    ticks = ticks_of(sample_entry(sample_id))
    time_base = result.video.time_base
    for at, tick in enumerate(ticks):
        got = [frame.pts_ticks for frame in decode_all(result, start_s=tick * time_base)]
        assert got == ticks[at:], f"start at {tick}"


@pytest.mark.parametrize("sample_id", ["vid-vfr", "vid-hevc8-bt709-full"])
def test_start_between_before_and_after_the_pts(
    sample_id: str,
    sample: Callable[[str], Path],
    sample_entry: Callable[[str], dict[str, Any]],
) -> None:
    result = probe(sample(sample_id))
    ticks = ticks_of(sample_entry(sample_id))
    time_base = result.video.time_base
    for at in (0, 3, len(ticks) // 2, len(ticks) - 2):
        between = Fraction(ticks[at] + ticks[at + 1], 2) * time_base
        got = [frame.pts_ticks for frame in decode_all(result, start_s=between)]
        assert got == ticks[at + 1 :]
        just_after = ticks[at] * time_base + Fraction(1, 10**9)
        assert [f.pts_ticks for f in decode_all(result, start_s=just_after)] == ticks[at + 1 :]
    assert [f.pts_ticks for f in decode_all(result, start_s=Fraction(-1))] == ticks
    assert [f.pts_ticks for f in decode_all(result, start_s=Fraction(0))] == ticks
    assert decode_all(result, start_s=(ticks[-1] + 1) * time_base) == []
    assert decode_all(result, start_s=Fraction(3600)) == []


@pytest.mark.parametrize("sample_id", ["vid-vfr", "vid-hevc8-bt709-full"])
def test_end_is_exclusive(
    sample_id: str,
    sample: Callable[[str], Path],
    sample_entry: Callable[[str], dict[str, Any]],
) -> None:
    result = probe(sample(sample_id))
    ticks = ticks_of(sample_entry(sample_id))
    time_base = result.video.time_base
    for at in (0, 1, 7, len(ticks) - 1):
        got = [f.pts_ticks for f in decode_all(result, end_s=ticks[at] * time_base)]
        assert got == ticks[:at]
    window = decode_all(result, start_s=ticks[4] * time_base, end_s=ticks[9] * time_base)
    assert [f.pts_ticks for f in window] == ticks[4:9]
    assert [f.index for f in window] == list(range(5))
    assert decode_all(result, start_s=ticks[5] * time_base, end_s=ticks[5] * time_base) == []
    assert decode_all(result, start_s=ticks[6] * time_base, end_s=ticks[2] * time_base) == []


def test_seeking_is_exact_on_a_file_that_does_not_start_at_zero(
    sample: Callable[[str], Path], tmp_path: Path
) -> None:
    moved = tmp_path / "moved.mp4"
    subprocess.run(
        [
            "ffmpeg", "-nostdin", "-v", "error", "-i", str(sample("vid-vfr")),
            "-map", "0:v:0", "-c", "copy", "-output_ts_offset", "2", str(moved),
        ],
        check=True,
        capture_output=True,
        timeout=60,
    )  # fmt: skip
    result = probe(moved)
    assert result.start_offset_s == 2
    ticks = [frame.pts_ticks for frame in decode_all(result)]
    assert ticks[0] == 60000 and len(ticks) == 30
    time_base = result.video.time_base
    for at in (0, 1, 10, 29):
        got = [f.pts_ticks for f in decode_all(result, start_s=ticks[at] * time_base)]
        assert got == ticks[at:]
    assert decode_all(result, start_s=Fraction(1)) != []
    assert [f.pts_ticks for f in decode_all(result, start_s=Fraction(1))] == ticks


def test_the_seek_argument_counts_from_the_container_start(sample: Callable[[str], Path]) -> None:
    result = probe(sample("vid-hevc8-bt709-full"))
    rate = result.video.frame_rate
    assert decode_module.seek_position(result, Fraction(0)) is None
    assert decode_module.seek_position(result, 1 / rate) is None
    assert decode_module.seek_position(result, Fraction(1)) == "0.966633"
    moved = dataclasses.replace(result, start_offset_s=Fraction(1, 2))
    assert decode_module.seek_position(moved, Fraction(1)) == "0.466633"


# --- DR-39 (c) decode rows and paths -----------------------------------------------------------


def _build_clip(path: Path, *, pix_fmt: str, matrix: str, color_range: str, siting: str) -> None:
    """Encode a short H.264 test clip with the given tags."""
    scale_range = "pc" if color_range == "pc" else "tv"
    subprocess.run(
        [
            "ffmpeg", "-nostdin", "-y", "-v", "error",
            "-f", "lavfi", "-i", "testsrc2=s=320x180:r=30:d=0.5",
            "-vf", f"scale=out_color_matrix={matrix}:out_range={scale_range},format={pix_fmt}",
            "-c:v", "libx264", "-crf", "12", "-pix_fmt", pix_fmt,
            "-colorspace", matrix, "-color_primaries", matrix, "-color_trc", matrix,
            "-color_range", color_range, "-chroma_sample_location", siting, str(path),
        ],
        check=True,
        capture_output=True,
        timeout=60,
    )  # fmt: skip


def test_a_yuvj420p_bt601_full_range_clip_decodes_as_ffmpeg_does(tmp_path: Path) -> None:
    path = tmp_path / "bt601-full.mp4"
    _build_clip(path, pix_fmt="yuvj420p", matrix="smpte170m", color_range="pc", siting="left")
    result = probe(path)
    assert result.video.pix_fmt == "yuvj420p"
    assert (result.video.color.matrix, result.video.color.range) == ("bt601", "full")
    frames = decode_all(result)
    assert len(frames) == 15
    assert [planes(frame) for frame in frames] == reference_planes(result, tmp_path)
    as_709 = dataclasses.replace(result.video.color, matrix="bt709")
    wrong = dataclasses.replace(result, video=dataclasses.replace(result.video, color=as_709))
    assert [planes(frame) for frame in decode_all(wrong)] != [planes(f) for f in frames]


def test_a_non_left_chroma_siting_decodes_with_that_siting(tmp_path: Path) -> None:
    path = tmp_path / "center.mp4"
    _build_clip(path, pix_fmt="yuvj420p", matrix="smpte170m", color_range="pc", siting="center")
    result = probe(path)
    assert result.video.chroma_siting == "center"
    assert "in_chroma_loc=center" in decode_filter(result.video)
    frames = [planes(frame) for frame in decode_all(result)]
    assert frames == reference_planes(result, tmp_path)
    left = dataclasses.replace(
        result, video=dataclasses.replace(result.video, chroma_siting="left")
    )
    assert [planes(frame) for frame in decode_all(left)] != frames


def test_a_path_with_percent_and_non_ascii_characters_decodes_identically(
    sample: Callable[[str], Path], tmp_path: Path
) -> None:
    folder = tmp_path / "a%d b%05d é水"
    folder.mkdir()
    copy = folder / "clip%03d é.mp4"
    shutil.copyfile(sample("vid-vfr"), copy)
    original = decode_all(probe(sample("vid-vfr")))
    moved = decode_all(probe(copy))
    assert [f.pts_ticks for f in moved] == [f.pts_ticks for f in original]
    assert [planes(f) for f in moved] == [planes(f) for f in original]
