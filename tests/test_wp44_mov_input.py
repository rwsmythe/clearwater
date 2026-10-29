"""WP4.4: QuickTime inputs use the existing video path and export as MP4."""

from __future__ import annotations

import json
import subprocess
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

import headless_export as he
import video_fidelity as vf
from clearwater.interfaces.image import ColorDescription
from clearwater.interfaces.video import (
    AudioStreamInfo,
    DataStreamInfo,
    ProbeResult,
    VideoStreamInfo,
)
from clearwater.io.video import FFmpegVideoSource, find_tool, probe
from clearwater.io.video.encode import encode_command
from container_spike import compare
from local_config import FootageLookupError, find_footage_file, load_local_config


@pytest.mark.parametrize("name", ["a.mov", "a.MOV", "a.Mov"])
def test_runner_routes_mov(name: str) -> None:
    """Accept QuickTime suffixes regardless of case (spec 5.2, 0.5.7)."""
    assert he.route(Path(name)) == "video"


def test_runner_unknown_extension_refusal_is_unchanged() -> None:
    """Keep the refusal for other extensions verbatim."""
    assert he.route(Path("notes.txt")) == "notes.txt is not a supported photo or video file."


def test_data_map_only_carries_proved_mp4_tags(tmp_path: Path) -> None:
    """Copy gpmd and audio, exclude timecode and an unproved synthetic codec tag."""
    video = VideoStreamInfo(
        codec="hevc",
        width=192,
        height=144,
        bit_depth=8,
        pix_fmt="yuv420p",
        chroma_siting="left",
        color=ColorDescription("bt709", "bt709", "bt709", "limited", 8, False, None),
        frame_rate=Fraction(30),
        time_base=Fraction(1, 600),
        nb_frames=15,
        rotation=0,
        vfr=False,
    )
    info = ProbeResult(
        path=tmp_path / "source.MOV",
        container="mov,mp4",
        duration_s=Fraction(1, 2),
        start_offset_s=Fraction(0),
        video=video,
        audio=(AudioStreamInfo(1, "pcm_s16le", 48000, 1, Fraction(0)),),
        data=(DataStreamInfo(2, "tmcd"), DataStreamInfo(3, "gpmd"), DataStreamInfo(4, "zzzz")),
        edit_list=(),
        faults=(),
        gopro=None,
    )
    command = encode_command(
        Path("ffmpeg"),
        info,
        tmp_path / "out.mp4",
        encoder="libx265",
        quality="standard",
        bit_depth=8,
        comment="",
        cut_at=None,
    )
    assert [command[i + 1] for i, arg in enumerate(command) if arg == "-map"] == [
        "0:v:0",
        "1:1",
        "1:3",
    ]
    assert command[command.index("-c:a") + 1] == "copy"
    assert command[command.index("-c:d") + 1] == "copy"
    assert command.count("-i") == 2  # One mux command: piped frames plus the source.
    assert command[-3:] == ["-f", "mp4", str((tmp_path / "out.mp4").absolute())]


def _ffmpeg(*args: str) -> None:
    subprocess.run(
        [str(find_tool("ffmpeg")), "-nostdin", "-hide_banner", "-v", "error", "-y", *args],
        check=True,
        capture_output=True,
        timeout=120,
    )


@pytest.fixture
def qt_mov(tmp_path: Path) -> Path:
    """Build a rotated qt-brand HEVC/B-frame/PCM source under this test's temp root."""
    unrotated = tmp_path / "unrotated.mov"
    source = tmp_path / "clip.MOV"
    _ffmpeg(
        "-f", "lavfi", "-i", "testsrc2=size=192x144:rate=30:duration=0.5",
        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=0.5",
        "-c:v", "libx265", "-pix_fmt", "yuv420p",
        "-x265-params", "bframes=2:log-level=error",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-color_range", "tv", "-c:a", "pcm_s16le", "-ac", "2", "-f", "mov", str(unrotated),
    )  # fmt: skip
    _ffmpeg(
        "-display_rotation", "180", "-i", str(unrotated),
        "-map", "0", "-c", "copy", "-f", "mov", str(source),
    )  # fmt: skip
    return source


def _assert_v4(source: Path, output: Path) -> dict[str, Any]:
    """Assert the house V4 contract, exposing only item names on failure."""
    record = vf.fidelity_record(source, output, bit_depth=8)
    wrong = record["summary"]["different_items"]
    assert record["summary"]["mandatory_and_required_all_same"], (
        wrong["MANDATORY"],
        wrong[compare.REQUIRED],
    )
    items = {item["name"]: item for item in record["items"]}
    assert items[vf._ROSTER_ITEM]["status"] == "SAME"
    return items


def test_qt_mov_probe_decode_runner_and_v4(qt_mov: Path, tmp_path: Path) -> None:
    """Preserve the required video facts through a rotated QuickTime export."""
    assert compare.read_movie(qt_mov).major_brand == "qt  "
    streams = compare.run_ffprobe(["-show_streams", str(qt_mov)])["streams"]
    video = next(stream for stream in streams if stream["codec_type"] == "video")
    audio = next(stream for stream in streams if stream["codec_type"] == "audio")
    assert video["codec_name"] == "hevc" and video["has_b_frames"] > 0
    rotations = [side["rotation"] for side in video["side_data_list"] if "rotation" in side]
    assert rotations and abs(rotations[0]) == 180
    assert any("displaymatrix" in side for side in video["side_data_list"])
    assert audio["codec_name"] == "pcm_s16le" and int(audio["sample_rate"]) == 48000
    assert audio["channels"] == 2 and audio["channel_layout"] == "stereo"

    info = probe(qt_mov)
    assert "mov" in info.container.split(",")
    assert abs(info.video.rotation) == 180
    assert sum(1 for _ in FFmpegVideoSource().frames(info, hw_decode=False)) == info.video.nb_frames
    assert info.video.nb_frames == 15
    out, cache = tmp_path / "out", tmp_path / "cache"
    out.mkdir()
    cache.mkdir()
    assert (
        he.main(
            [
                str(qt_mov),
                "--out",
                str(out),
                "--cache-dir",
                str(cache),
                "--force-cpu",
                "--encoder",
                "libx265",
            ]
        )
        == 0
    )
    output = out / "clip_corrected.mp4"
    assert list(out.iterdir()) == [output]
    items = _assert_v4(qt_mov, output)
    assert items["display orientation: display matrix (ffprobe side data)"]["status"] == "SAME"


def _phone_mov() -> Path:
    """Locate the phone clip, skipping only absence in a successfully searched folder."""
    root = load_local_config().footage_path
    try:
        return find_footage_file("IMG_6702", root)
    except FootageLookupError as error:
        if error.matches or error.__cause__ is not None or not root.is_dir():
            raise
        pytest.skip("IMG_6702 is not in the footage folder")


@pytest.mark.footage  # Serial leg: reads owner footage, read-only.
def test_phone_mov_runner_and_v4(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Export the rotated phone MOV with V4 preserved and only omitted-data warnings."""
    source = _phone_mov()
    out, cache = tmp_path / "out", tmp_path / "cache"
    out.mkdir()
    cache.mkdir()
    record_path = tmp_path / "runner-record.json"
    status = he.main(
        [
            str(source),
            "--out",
            str(out),
            "--cache-dir",
            str(cache),
            "--force-cpu",
            "--encoder",
            "libx265",
            "--record",
            str(record_path),
        ]
    )
    capsys.readouterr()
    assert status == 0
    output = out / "IMG_6702_corrected.mp4"
    output_names = [path.name for path in out.iterdir()]
    assert output_names == ["IMG_6702_corrected.mp4"]

    data = json.loads(record_path.read_text(encoding="ascii"))
    item_count = len(data["items"])
    assert item_count == 1
    item = data["items"][0]
    state = item["state"]
    assert state == "done with warnings"
    recorded_outputs = item["outputs"]
    assert recorded_outputs == ["IMG_6702_corrected.mp4"]
    # Keep assertion failures to counts/booleans; never display arbitrary warning text.
    warnings = item["warnings"]
    all_not_carried = all(warning.startswith("Not carried to the output: ") for warning in warnings)
    assert all_not_carried, "only not-carried data-track warnings are permitted"
    warning_count = len(warnings)
    mebx_count = warnings.count("Not carried to the output: data track mebx")
    # verify.not_carried emits one entry per missing track, with no deduplication.
    assert warning_count == 2
    assert mebx_count == 2

    items = _assert_v4(source, output)
    assert items["video frame count"]["source"] == 15
    assert items["video frame count"]["output"] == 15
    assert items["display orientation: display matrix (ffprobe side data)"]["status"] == "SAME"
