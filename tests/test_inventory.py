from __future__ import annotations

import csv
import dataclasses
import json
import os
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pillow_heif
import pytest
from PIL import Image, ImageCms

import inventory
from inventory import PhotoRecord, VideoRecord
from local_config import load_local_config

pillow_heif.register_heif_opener()

needs_ffmpeg = pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="ffmpeg/ffprobe not on PATH",
)


# Canned ffprobe documents: a trimmed, hand-built subset of the fields that
# `ffprobe -v error -print_format json -show_format -show_streams` prints. The field
# names and value shapes follow ffprobe 9.0.2 (checked against real 9.0.2 output).
def _ffprobe_doc(
    *, pix_fmt: str = "yuv420p", r_rate: str = "30/1", avg: str = "30/1", **extra: Any
) -> dict[str, Any]:
    video = {
        "index": 0,
        "codec_name": "h264",
        "codec_type": "video",
        "width": 3840,
        "height": 2160,
        "pix_fmt": pix_fmt,
        "r_frame_rate": r_rate,
        "avg_frame_rate": avg,
        "color_range": "tv",
        "color_space": "bt709",
        "color_transfer": "bt709",
        "color_primaries": "bt709",
        "duration": "12.5",
    }
    video.update(extra)
    return {
        "streams": [video, {"index": 1, "codec_type": "audio", "codec_name": "aac"}],
        "format": {"format_name": "mov,mp4,m4a,3gp,3g2,mj2", "duration": "12.6"},
    }


def _build(doc: dict[str, Any], name: str = "clip.mp4") -> VideoRecord:
    return inventory._video_from_ffprobe(Path(name), 123, doc, lrv_present=False)


def _make_video(path: Path, *extra: str) -> None:
    command = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i"]
    command += ["testsrc=duration=1:size=64x48:rate=10", *extra, str(path)]
    subprocess.run(command, check=True, capture_output=True, timeout=60)


def _snapshot(root: Path) -> dict[str, tuple[int, int]]:
    return {
        p.relative_to(root).as_posix(): (p.stat().st_size, p.stat().st_mtime_ns)
        for p in sorted(root.rglob("*"))
    }


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    """A footage tree with GoPro naming, sidecars, a real photo and unrelated files."""
    root = tmp_path / "footage"
    (root / "dive1").mkdir(parents=True)
    (root / "dive2").mkdir()
    for name in (
        "dive1/GX010001.MP4",
        "dive1/GX020001.MP4",
        "dive1/GL010001.LRV",
        "dive1/GX010001.THM",
        "dive1/GH010002.mp4",
        "dive2/GOPR0003.MP4",
        "dive2/GP010003.MP4",
        "dive2/GOPR0003.LRV",
        "dive2/notes.txt",
        "desktop.ini",
    ):
        (root / name).write_bytes(b"not really media")
    Image.new("RGB", (64, 48), (10, 120, 200)).save(root / "IMG_0001.HEIC", format="HEIF")
    return root


class TestParseGoproName:
    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("GX010001.MP4", (1, 1)),
            ("GX020001", (1, 2)),
            ("gh011234.mp4", (1234, 1)),
            ("GH120042.MP4", (42, 12)),
            ("GS010005.360", (5, 1)),
            ("GOPR0007.MP4", (7, 1)),
            ("GP010007.MP4", (7, 2)),
            ("GP020007.MP4", (7, 3)),
            ("IMG_0001.MOV", (None, None)),
            ("GX01000.MP4", (None, None)),
            ("GX0100012.MP4", (None, None)),
            ("XGX010001.MP4", (None, None)),
            ("GX010001_copy.MP4", (None, None)),
            ("", (None, None)),
        ],
    )
    def test_names(self, name: str, expected: tuple[int | None, int | None]) -> None:
        assert inventory.parse_gopro_name(name) == expected


class TestLrvBeside:
    def test_forms(self, tmp_path: Path) -> None:
        for name in ("GX010001.MP4", "GL010001.LRV", "GOPR0002.MP4", "gopr0002.lrv"):
            (tmp_path / name).write_bytes(b"")
        for name in ("GX010003.MP4", "IMG_1.MOV", "IMG_2.MOV", "GH010004.MP4", "GL010005.lrv"):
            (tmp_path / name).write_bytes(b"")
        (tmp_path / "IMG_1.lrv").write_bytes(b"")
        assert inventory.lrv_beside(tmp_path / "GX010001.MP4")  # GL form
        assert inventory.lrv_beside(tmp_path / "GOPR0002.MP4")  # same stem, case differs
        assert inventory.lrv_beside(tmp_path / "IMG_1.MOV")  # same stem
        assert not inventory.lrv_beside(tmp_path / "GX010003.MP4")
        assert not inventory.lrv_beside(tmp_path / "IMG_2.MOV")
        assert not inventory.lrv_beside(tmp_path / "GH010004.MP4")

    def test_other_directory_does_not_count(self, tmp_path: Path) -> None:
        (tmp_path / "a").mkdir()
        (tmp_path / "b").mkdir()
        (tmp_path / "a" / "GL010001.LRV").write_bytes(b"")
        assert not inventory.lrv_beside(tmp_path / "b" / "GX010001.MP4")

    def test_missing_directory_is_false(self, tmp_path: Path) -> None:
        assert not inventory.lrv_beside(tmp_path / "nope" / "GX010001.MP4")


class TestVideoFromFfprobe:
    def test_constant_rate_8_bit(self) -> None:
        record = _build(_ffprobe_doc(), "GX010004.MP4")
        assert record.codec == "h264"
        assert (record.width, record.height) == (3840, 2160)
        assert record.frame_rate == 30.0
        assert record.frame_rate_variable is False
        assert record.bit_depth == 8
        assert record.chroma_format == "4:2:0"
        assert record.color_primaries == "bt709"
        assert record.color_transfer == "bt709"
        assert record.color_matrix == "bt709"
        assert record.color_range == "tv"
        assert record.duration_seconds == 12.5
        assert record.rotation_degrees == 0
        assert record.tracks == ("0:video:h264", "1:audio:aac")
        assert (record.gopro_recording, record.gopro_chapter) == (4, 1)
        assert record.container == "mov,mp4,m4a,3gp,3g2,mj2"
        assert record.category == ""
        assert record.error is None

    def test_variable_frame_rate(self) -> None:
        record = _build(_ffprobe_doc(r_rate="60/1", avg="2997/100"))
        assert record.frame_rate_variable is True
        assert record.frame_rate == pytest.approx(29.97)

    def test_ntsc_rates_are_not_variable(self) -> None:
        record = _build(_ffprobe_doc(r_rate="30000/1001", avg="2997/100"))
        assert record.frame_rate_variable is False

    def test_variable_threshold_is_half_a_percent(self) -> None:
        assert _build(_ffprobe_doc(r_rate="1000/1", avg="996/1")).frame_rate_variable is False
        assert _build(_ffprobe_doc(r_rate="1000/1", avg="994/1")).frame_rate_variable is True

    def test_ten_bit(self) -> None:
        record = _build(_ffprobe_doc(pix_fmt="yuv420p10le", codec_name="hevc"))
        assert (record.codec, record.bit_depth, record.chroma_format) == ("hevc", 10, "4:2:0")

    @pytest.mark.parametrize("rate", ["0/0", "0/1", "30/0", "", "abc", "nan/1"])
    def test_unusable_rates_are_none(self, rate: str) -> None:
        record = _build(_ffprobe_doc(r_rate=rate, avg=rate))
        assert record.frame_rate is None
        assert record.frame_rate_variable is None

    def test_one_rate_unusable_leaves_variable_unknown(self) -> None:
        record = _build(_ffprobe_doc(r_rate="30/1", avg="0/0"))
        assert record.frame_rate is None
        assert record.frame_rate_variable is None

    @pytest.mark.parametrize(
        ("side_data", "expected"),
        [
            (-90, 90),
            (90, 270),
            (180, 180),
            (-180, 180),
            (0, 0),
            (-270, 270),
            (-89.6, 90),
            (-100, 90),
            (44, 0),
            (-46, 90),
        ],
    )
    def test_display_matrix_rotation(self, side_data: float, expected: int) -> None:
        extra = {"side_data_list": [{"side_data_type": "Display Matrix", "rotation": side_data}]}
        assert _build(_ffprobe_doc(**extra)).rotation_degrees == expected

    @pytest.mark.parametrize(("tag", "expected"), [("90", 90), ("270", 270), ("-90", 270)])
    def test_rotate_tag(self, tag: str, expected: int) -> None:
        assert _build(_ffprobe_doc(tags={"rotate": tag})).rotation_degrees == expected

    def test_display_matrix_wins_over_tag(self) -> None:
        extra = {"side_data_list": [{"rotation": -90}], "tags": {"rotate": "180"}}
        assert _build(_ffprobe_doc(**extra)).rotation_degrees == 90

    def test_no_video_stream_still_yields_a_row(self) -> None:
        doc = {"streams": [{"index": 0, "codec_type": "audio", "codec_name": "aac"}]}
        record = _build(doc)
        assert record.error == "no video stream"
        assert record.codec == ""
        assert record.rotation_degrees is None
        assert record.tracks == ("0:audio:aac",)

    @pytest.mark.parametrize("doc", [{}, {"streams": []}, {"streams": "x"}, {"streams": [3, None]}])
    def test_degenerate_documents(self, doc: dict[str, Any]) -> None:
        record = _build(doc)
        assert record.error == "no video stream"

    def test_cover_art_stream_is_not_the_video(self) -> None:
        doc = _ffprobe_doc()
        cover = {"index": 2, "codec_type": "video", "codec_name": "mjpeg", "width": 9}
        cover["disposition"] = {"attached_pic": 1}
        doc["streams"].insert(0, cover)
        assert _build(doc).codec == "h264"

    def test_duration_falls_back_to_container(self) -> None:
        doc = _ffprobe_doc()
        del doc["streams"][0]["duration"]
        assert _build(doc).duration_seconds == 12.6

    def test_missing_optional_fields_are_none(self) -> None:
        doc = {"streams": [{"index": 0, "codec_type": "video", "codec_name": "h264"}]}
        record = _build(doc)
        assert record.error is None
        assert record.width is None
        assert record.bit_depth is None
        assert record.chroma_format is None
        assert record.color_primaries is None
        assert record.duration_seconds is None
        assert record.container == ""

    def test_bits_per_raw_sample_is_a_fallback_only(self) -> None:
        assert _build(_ffprobe_doc(pix_fmt="weird", bits_per_raw_sample="12")).bit_depth == 12
        assert _build(_ffprobe_doc(pix_fmt="yuv420p", bits_per_raw_sample="10")).bit_depth == 8


class TestPixelFormats:
    @pytest.mark.parametrize(
        ("pix_fmt", "depth", "chroma"),
        [
            ("yuv420p", 8, "4:2:0"),
            ("yuvj420p", 8, "4:2:0"),
            ("yuv422p", 8, "4:2:2"),
            ("yuv444p", 8, "4:4:4"),
            ("yuv420p10le", 10, "4:2:0"),
            ("yuv422p10le", 10, "4:2:2"),
            ("yuva444p12le", 12, "4:4:4"),
            ("nv12", 8, "4:2:0"),
            ("p010le", 10, "4:2:0"),
            ("p210le", 10, "4:2:2"),
            ("p016le", 16, "4:2:0"),
            ("gray", 8, "4:0:0"),
            ("gray10le", 10, "4:0:0"),
            ("gbrp", 8, "4:4:4"),
            ("gbrp12le", 12, "4:4:4"),
            ("rgb24", 8, "4:4:4"),
        ],
    )
    def test_known(self, pix_fmt: str, depth: int, chroma: str) -> None:
        assert inventory._bit_depth(pix_fmt, None) == depth
        assert inventory._chroma_format(pix_fmt) == chroma

    def test_unknown(self) -> None:
        assert inventory._bit_depth("mystery", None) is None
        assert inventory._bit_depth(None, None) is None
        assert inventory._chroma_format("mystery") is None
        assert inventory._chroma_format(None) is None


class _FakeRun:
    def __init__(self, outcome: Any) -> None:
        self.outcome = outcome
        self.calls: list[tuple[list[str], dict[str, Any]]] = []

    def __call__(self, command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        self.calls.append((command, kwargs))
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        assert isinstance(self.outcome, subprocess.CompletedProcess)
        return self.outcome


def _completed(stdout: bytes = b"", stderr: bytes = b"", code: int = 0) -> Any:
    return subprocess.CompletedProcess([], code, stdout=stdout, stderr=stderr)


class TestProbeVideoFailures:
    @pytest.fixture
    def clip(self, tmp_path: Path) -> Path:
        path = tmp_path / "GX010009.MP4"
        path.write_bytes(b"12345")
        (tmp_path / "GL010009.LRV").write_bytes(b"")
        return path

    def test_command_has_timeout_and_no_shell(
        self, monkeypatch: pytest.MonkeyPatch, clip: Path
    ) -> None:
        fake = _FakeRun(_completed(json.dumps(_ffprobe_doc()).encode()))
        monkeypatch.setattr(inventory.subprocess, "run", fake)
        record = inventory.probe_video(clip)
        command, kwargs = fake.calls[0]
        assert command == [
            "ffprobe", "-v", "error", "-print_format", "json",
            "-show_format", "-show_streams", str(clip),
        ]  # fmt: skip
        assert kwargs["timeout"] == inventory.FFPROBE_TIMEOUT_SECONDS == 60.0
        assert not kwargs.get("shell")
        assert record.error is None
        assert record.size_bytes == 5
        assert record.lrv_present is True
        assert (record.gopro_recording, record.gopro_chapter) == (9, 1)

    @pytest.mark.parametrize(
        ("outcome", "message"),
        [
            (FileNotFoundError(), "ffprobe not found"),
            (subprocess.TimeoutExpired("ffprobe", 60), "timed out"),
            (PermissionError("denied"), "could not run"),
            (_completed(stderr=b"moov atom not found\nInvalid data", code=1), "moov atom"),
            (_completed(b"not json"), "not valid JSON"),
            (_completed(b"[1, 2]"), "not a JSON object"),
        ],
    )
    def test_failures_give_a_row(
        self, monkeypatch: pytest.MonkeyPatch, clip: Path, outcome: Any, message: str
    ) -> None:
        monkeypatch.setattr(inventory.subprocess, "run", _FakeRun(outcome))
        record = inventory.probe_video(clip)
        assert record.error is not None
        assert message in record.error
        assert "\n" not in record.error
        assert record.size_bytes == 5
        assert (record.gopro_recording, record.gopro_chapter) == (9, 1)
        assert record.lrv_present is True

    def test_error_keeps_the_reason_not_the_path(
        self, monkeypatch: pytest.MonkeyPatch, clip: Path
    ) -> None:
        stderr = f"{clip}: Invalid data found when processing input".encode()
        monkeypatch.setattr(
            inventory.subprocess, "run", _FakeRun(_completed(stderr=stderr, code=1))
        )
        record = inventory.probe_video(clip)
        assert record.error is not None
        assert str(clip) not in record.error
        assert "GX010009.MP4: Invalid data found when processing input" in record.error

    def test_long_path_cannot_push_the_reason_out(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        deep = tmp_path.joinpath(*["a-rather-long-folder-name"] * 12)
        deep.mkdir(parents=True)
        clip = deep / "GX010009.MP4"
        clip.write_bytes(b"12345")
        assert len(str(clip)) > 250
        stderr = f"{clip}: moov atom not found".encode()
        monkeypatch.setattr(
            inventory.subprocess, "run", _FakeRun(_completed(stderr=stderr, code=1))
        )
        record = inventory.probe_video(clip)
        assert record.error is not None
        assert "moov atom not found" in record.error
        assert len(record.error) <= 200

    def test_photo_error_drops_the_quoted_path(self, tmp_path: Path) -> None:
        deep = tmp_path.joinpath(*["a-rather-long-folder-name"] * 12)
        deep.mkdir(parents=True)
        path = deep / "bad.jpg"
        path.write_bytes(b"this is not an image" * 10)
        record = inventory.probe_photo(path)
        assert record.error is not None
        assert str(path) not in record.error
        assert str(path).replace("\\", "\\\\") not in record.error
        assert "cannot identify image file" in record.error
        assert "bad.jpg" in record.error

    def test_long_error_is_truncated(self, monkeypatch: pytest.MonkeyPatch, clip: Path) -> None:
        monkeypatch.setattr(
            inventory.subprocess, "run", _FakeRun(_completed(stderr=b"x" * 999, code=1))
        )
        record = inventory.probe_video(clip)
        assert record.error is not None
        assert len(record.error) <= 200

    def test_vanished_file_is_a_row_with_error(self, tmp_path: Path) -> None:
        record = inventory.probe_video(tmp_path / "gone.mp4")
        assert record.error is not None
        assert record.size_bytes == 0


@needs_ffmpeg
class TestProbeVideoReal:
    def test_plain_mp4(self, tmp_path: Path) -> None:
        path = tmp_path / "plain.mp4"
        _make_video(path, "-pix_fmt", "yuv420p")
        record = inventory.probe_video(path)
        assert record.error is None
        assert (record.codec, record.width, record.height) == ("h264", 64, 48)
        assert record.frame_rate == 10.0
        assert record.frame_rate_variable is False
        assert (record.bit_depth, record.chroma_format) == (8, "4:2:0")
        assert record.duration_seconds == pytest.approx(1.0, abs=0.2)
        assert record.rotation_degrees == 0
        assert record.tracks == ("0:video:h264",)
        assert record.size_bytes == path.stat().st_size
        assert "mp4" in record.container

    def test_ten_bit_hevc(self, tmp_path: Path) -> None:
        path = tmp_path / "ten.mp4"
        try:
            _make_video(
                path,
                "-c:v",
                "libx265",
                "-pix_fmt",
                "yuv420p10le",
                "-x265-params",
                "log-level=error",
            )
        except subprocess.CalledProcessError:
            pytest.skip("this ffmpeg build cannot encode 10-bit HEVC")
        record = inventory.probe_video(path)
        assert (record.codec, record.bit_depth) == ("hevc", 10)

    def test_mov(self, tmp_path: Path) -> None:
        path = tmp_path / "IMG_0001.MOV"
        _make_video(path, "-pix_fmt", "yuv420p")
        record = inventory.probe_video(path)
        assert record.error is None
        assert (record.gopro_recording, record.gopro_chapter) == (None, None)

    def test_truncated_file_is_a_row_with_error(self, tmp_path: Path) -> None:
        full = tmp_path / "full.mp4"
        _make_video(full, "-pix_fmt", "yuv420p")
        cut = tmp_path / "GX010001.MP4"
        cut.write_bytes(full.read_bytes()[:200])
        record = inventory.probe_video(cut)
        assert record.error is not None
        assert record.codec == ""
        assert (record.gopro_recording, record.gopro_chapter) == (1, 1)


def _save_with_exif(image: Image.Image, path: Path, orientation: int, **kwargs: Any) -> None:
    exif = Image.Exif()
    exif[0x0112] = orientation
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    image.save(path, exif=exif.tobytes(), icc_profile=profile, **kwargs)


def _heic_without_irot(path: Path, orientation: int) -> None:
    """Write a 64x48 HEIC whose EXIF says ``orientation`` but whose container has no irot."""
    low = Image.Exif()
    low[0x0112] = 1
    high = Image.Exif()
    high[0x0112] = orientation
    heif = pillow_heif.from_bytes("RGB", (64, 48), bytes(64 * 48 * 3))
    heif.info["exif"] = low.tobytes()
    heif.save(path)
    data = path.read_bytes()
    old, new = low.tobytes()[6:], high.tobytes()[6:]  # the TIFF part after "Exif\0\0"
    assert data.count(old) == 1
    assert b"irot" not in data
    path.write_bytes(data.replace(old, new))


class TestProbePhoto:
    def test_jpeg_with_orientation_and_profile(self, tmp_path: Path) -> None:
        path = tmp_path / "a.jpg"
        _save_with_exif(Image.new("RGB", (64, 48)), path, 6)
        record = inventory.probe_photo(path)
        assert record == PhotoRecord(
            path=path,
            size_bytes=path.stat().st_size,
            format="JPEG",
            width=64,
            height=48,
            bit_depth=8,
            color_profile="sRGB built-in",
            orientation=6,
        )

    def test_plain_jpeg_has_no_profile_or_orientation(self, tmp_path: Path) -> None:
        path = tmp_path / "a.jpeg"
        Image.new("RGB", (10, 20)).save(path)
        record = inventory.probe_photo(path)
        assert (record.color_profile, record.orientation) == (None, None)
        assert (record.width, record.height) == (10, 20)

    def test_png_8_and_16_bit(self, tmp_path: Path) -> None:
        eight = tmp_path / "eight.png"
        Image.new("RGB", (8, 8)).save(eight)
        sixteen = tmp_path / "sixteen.png"
        Image.new("I;16", (8, 8), 1000).save(sixteen)
        assert inventory.probe_photo(eight).bit_depth == 8
        assert inventory.probe_photo(sixteen).bit_depth == 16
        assert inventory.probe_photo(sixteen).format == "PNG"

    def test_tiff(self, tmp_path: Path) -> None:
        path = tmp_path / "a.tif"
        Image.new("RGB", (12, 7)).save(path)
        record = inventory.probe_photo(path)
        assert (record.format, record.bit_depth, record.width, record.height) == ("TIFF", 8, 12, 7)

    def test_heic_landscape(self, tmp_path: Path) -> None:
        path = tmp_path / "a.heic"
        _save_with_exif(Image.new("RGB", (64, 48)), path, 1, format="HEIF")
        record = inventory.probe_photo(path)
        assert record.error is None
        assert record.format == "HEIF"
        assert (record.width, record.height) == (64, 48)
        assert record.bit_depth == 8
        assert record.color_profile == "sRGB built-in"
        assert record.orientation == 1

    def test_heic_portrait_reports_stored_dimensions(self, tmp_path: Path) -> None:
        path = tmp_path / "p.heic"
        _save_with_exif(Image.new("RGB", (64, 48)), path, 6, format="HEIF")
        record = inventory.probe_photo(path)
        assert record.orientation == 6
        assert (record.width, record.height) == (64, 48)  # same convention as JPEG

    def test_heic_with_irot_is_swapped_back(self, tmp_path: Path) -> None:
        path = tmp_path / "irot.heic"
        _save_with_exif(Image.new("RGB", (64, 48)), path, 6, format="HEIF")
        assert b"irot" in path.read_bytes()
        assert inventory._heif_axes_swapped(path) is True
        with Image.open(path) as decoded:
            assert decoded.size == (48, 64)  # what the decoder reports after applying irot
        assert (inventory.probe_photo(path).width, inventory.probe_photo(path).height) == (64, 48)

    @pytest.mark.parametrize("orientation", [5, 6, 7, 8])
    def test_heic_with_exif_orientation_but_no_irot_is_not_swapped(
        self, tmp_path: Path, orientation: int
    ) -> None:
        path = tmp_path / "noirot.heic"
        _heic_without_irot(path, orientation)
        with Image.open(path) as decoded:
            assert decoded.size == (64, 48)  # nothing was rotated by the decoder
        assert inventory._heif_axes_swapped(path) is False
        record = inventory.probe_photo(path)
        assert (record.width, record.height) == (64, 48)
        assert record.orientation == orientation
        assert record.error is None

    def test_heic_half_turn_is_not_swapped(self, tmp_path: Path) -> None:
        path = tmp_path / "half.heic"
        _save_with_exif(Image.new("RGB", (64, 48)), path, 3, format="HEIF")
        assert b"irot" in path.read_bytes()
        assert inventory._heif_axes_swapped(path) is False
        assert (inventory.probe_photo(path).width, inventory.probe_photo(path).height) == (64, 48)

    def test_unparsable_heif_container_leaves_dimensions_as_decoded(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        path = tmp_path / "irot.heic"
        _save_with_exif(Image.new("RGB", (64, 48)), path, 6, format="HEIF")
        monkeypatch.setattr(inventory, "_heif_axes_swapped", lambda p: None)
        record = inventory.probe_photo(path)
        assert (record.width, record.height) == (48, 64)
        assert record.error is not None
        assert "rotation unreadable" in record.error

    def test_heif_parser_gives_none_for_other_files(self, tmp_path: Path) -> None:
        jpeg = tmp_path / "a.jpg"
        Image.new("RGB", (8, 8)).save(jpeg)
        junk = tmp_path / "junk.heic"
        junk.write_bytes(b"\x00\x00\x00\x10ftypheic" + b"\x00" * 40)
        heic = tmp_path / "a.heic"
        _save_with_exif(Image.new("RGB", (64, 48)), heic, 6, format="HEIF")
        cut = tmp_path / "cut.heic"
        cut.write_bytes(heic.read_bytes()[:60])
        for path in (jpeg, junk, cut, tmp_path / "missing.heic"):
            assert inventory._heif_axes_swapped(path) is None

    def test_jpeg_orientation_never_swaps(self, tmp_path: Path) -> None:
        path = tmp_path / "a.jpg"
        _save_with_exif(Image.new("RGB", (64, 48)), path, 8)
        record = inventory.probe_photo(path)
        assert (record.width, record.height, record.orientation) == (64, 48, 8)

    def test_heic_ten_bit(self, tmp_path: Path) -> None:
        path = tmp_path / "ten.heic"
        try:
            Image.new("I;16", (16, 16), 30000).save(path, format="HEIF", bit_depth=10)
        except Exception as exc:
            pytest.skip(f"cannot write 10-bit HEIC here: {exc}")
        record = inventory.probe_photo(path)
        assert record.bit_depth == 10
        assert record.error is None

    def test_heic_without_bit_depth_gets_a_reason(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        path = tmp_path / "a.heic"
        Image.new("RGB", (8, 8)).save(path, format="HEIF")
        monkeypatch.setattr(inventory, "_photo_bit_depth", lambda image, p: None)
        record = inventory.probe_photo(path)
        assert record.bit_depth is None
        assert record.error is not None
        assert "bit depth" in record.error
        assert record.format == "HEIF"

    def test_out_of_range_orientation_is_none(self, tmp_path: Path) -> None:
        path = tmp_path / "a.jpg"
        _save_with_exif(Image.new("RGB", (8, 8)), path, 9)
        assert inventory.probe_photo(path).orientation is None

    @pytest.mark.parametrize("name", ["bad.jpg", "bad.heic", "bad.png", "bad.tif"])
    def test_corrupt_file_is_a_row_with_error(self, tmp_path: Path, name: str) -> None:
        path = tmp_path / name
        path.write_bytes(b"this is not an image" * 10)
        record = inventory.probe_photo(path)
        assert record.error is not None
        assert "\n" not in record.error
        assert record.size_bytes == path.stat().st_size
        assert record.width is None

    def test_truncated_jpeg_header(self, tmp_path: Path) -> None:
        full = tmp_path / "full.jpg"
        Image.new("RGB", (64, 48)).save(full)
        cut = tmp_path / "cut.jpg"
        cut.write_bytes(full.read_bytes()[:5])
        assert inventory.probe_photo(cut).error is not None

    def test_vanished_file(self, tmp_path: Path) -> None:
        record = inventory.probe_photo(tmp_path / "gone.jpg")
        assert record.error is not None
        assert record.size_bytes == 0


class TestScan:
    def test_tree(self, tree: Path) -> None:
        result = inventory.scan_tree(tree)
        by_path = {r.path.as_posix(): r for r in result.records}
        assert [r.path.as_posix() for r in result.records] == sorted(by_path)
        assert sorted(by_path) == [
            "IMG_0001.HEIC",
            "dive1/GH010002.mp4",
            "dive1/GX010001.MP4",
            "dive1/GX020001.MP4",
            "dive2/GOPR0003.MP4",
            "dive2/GP010003.MP4",
        ]
        assert all(not r.path.is_absolute() for r in result.records)
        assert (result.ignored, result.sidecars, result.skipped) == (2, 3, 0)
        videos = {k: v for k, v in by_path.items() if isinstance(v, VideoRecord)}
        expected = {
            "dive1/GH010002.mp4": (2, 1, False),
            "dive1/GX010001.MP4": (1, 1, True),
            "dive1/GX020001.MP4": (1, 2, False),
            "dive2/GOPR0003.MP4": (3, 1, True),
            "dive2/GP010003.MP4": (3, 2, False),
        }
        assert {
            k: (v.gopro_recording, v.gopro_chapter, v.lrv_present) for k, v in videos.items()
        } == expected
        assert isinstance(by_path["IMG_0001.HEIC"], PhotoRecord)
        # GX020001 has no GL020001.LRV: only the first chapter pairs.
        assert by_path["IMG_0001.HEIC"].error is None
        assert all(v.category == "" for v in by_path.values())

    def test_scan_returns_the_records(self, tree: Path) -> None:
        records = inventory.scan(tree)
        assert [r.path for r in records] == [r.path for r in inventory.scan_tree(tree).records]

    def test_bad_video_does_not_abort(self, tree: Path) -> None:
        records = {r.path.as_posix(): r for r in inventory.scan(tree)}
        assert records["dive1/GX010001.MP4"].error is not None
        assert records["IMG_0001.HEIC"].error is None

    def test_unexpected_failure_becomes_a_row(
        self, tree: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def explode(path: Path) -> PhotoRecord:
            raise RuntimeError("boom")

        monkeypatch.setattr(inventory, "probe_photo", explode)
        records = {r.path.as_posix(): r for r in inventory.scan(tree)}
        assert records["IMG_0001.HEIC"].error == "unexpected failure: RuntimeError: boom"
        assert len(records) == 6

    def test_file_that_vanishes_is_skipped(
        self, tree: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        victim = tree / "dive2" / "GP010003.MP4"
        real_walk = os.walk

        def walk_then_delete(*args: Any, **kwargs: Any) -> Any:
            yield from real_walk(*args, **kwargs)
            victim.unlink()

        monkeypatch.setattr(inventory.os, "walk", walk_then_delete)
        result = inventory.scan_tree(tree)
        assert result.skipped == 1
        assert "dive2/GP010003.MP4" not in {r.path.as_posix() for r in result.records}
        assert len(result.records) == 5

    def test_extension_case_is_ignored(self, tmp_path: Path) -> None:
        (tmp_path / "A.JPG").write_bytes(b"x")
        (tmp_path / "B.Mov").write_bytes(b"x")
        (tmp_path / "C.Lrv").write_bytes(b"x")
        result = inventory.scan_tree(tmp_path)
        assert [r.path.name for r in result.records] == ["A.JPG", "B.Mov"]
        assert result.sidecars == 1

    def test_empty_folder(self, tmp_path: Path) -> None:
        result = inventory.scan_tree(tmp_path)
        assert result == inventory.ScanResult((), 0, 0, 0)

    def test_leaves_the_root_untouched(self, tree: Path) -> None:
        before = _snapshot(tree)
        inventory.scan(tree)
        assert _snapshot(tree) == before


def _records() -> list[inventory.Record]:
    video = _build(
        _ffprobe_doc(pix_fmt="yuv420p10le", codec_name="hevc", r_rate="60/1", avg="30/1")
    )
    video = dataclasses.replace(
        video, path=Path("dive1/GX010001.MP4"), lrv_present=True, gopro_recording=1, gopro_chapter=1
    )
    second = dataclasses.replace(video, path=Path("dive1/GX020001.MP4"), gopro_chapter=2)
    lone = dataclasses.replace(video, path=Path("dive1/GX010002.MP4"), gopro_recording=2)
    broken = inventory._failed_video(Path("dive2/GX010003.MP4"), 9, "ffprobe failed: bad")
    photo = PhotoRecord(
        path=Path("IMG_0001.HEIC"),
        size_bytes=77,
        format="HEIF",
        width=4032,
        height=3024,
        bit_depth=8,
        color_profile="Display P3",
        orientation=6,
    )
    return [photo, video, second, lone, broken]


class TestWriteInventory:
    def test_columns_cover_every_field_once(self) -> None:
        video = {f.name for f in dataclasses.fields(VideoRecord)}
        photo = {f.name for f in dataclasses.fields(PhotoRecord)}
        assert len(set(inventory.CSV_COLUMNS)) == len(inventory.CSV_COLUMNS)
        assert set(inventory.CSV_COLUMNS) == video | photo | {"kind"}
        assert inventory.CSV_COLUMNS[:5] == ("kind", "path", "category", "size_bytes", "error")
        video_order = [f.name for f in dataclasses.fields(VideoRecord)]
        rest = [c for c in inventory.CSV_COLUMNS[5:] if c in video]
        assert rest == [
            n for n in video_order if n not in {"path", "size_bytes", "category", "error"}
        ]
        assert inventory.CSV_COLUMNS[-3:] == ("format", "color_profile", "orientation")

    def test_csv_content(self, tmp_path: Path) -> None:
        csv_path, _ = inventory.write_inventory(_records(), tmp_path, stamp="20261014T120000Z")
        assert csv_path == tmp_path / "reports" / "inventory-20261014T120000Z.csv"
        raw = csv_path.read_bytes()
        assert raw.startswith(b"\xef\xbb\xbf")
        with csv_path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == 5
        assert list(rows[0]) == list(inventory.CSV_COLUMNS)
        assert [r["kind"] for r in rows] == ["photo", "video", "video", "video", "video"]
        assert all(r["category"] == "" for r in rows)
        photo, video, _, _, broken = rows
        assert photo["path"] == "IMG_0001.HEIC"
        assert (photo["width"], photo["height"], photo["bit_depth"]) == ("4032", "3024", "8")
        assert (photo["format"], photo["color_profile"], photo["orientation"]) == (
            "HEIF",
            "Display P3",
            "6",
        )
        assert photo["codec"] == "" and photo["tracks"] == ""
        assert video["path"] == "dive1/GX010001.MP4"
        assert video["frame_rate"] == "30"
        assert video["frame_rate_variable"] == "true"
        assert video["lrv_present"] == "true"
        assert video["tracks"] == "0:video:hevc;1:audio:aac"
        assert video["duration_seconds"] == "12.500"
        assert (video["gopro_recording"], video["gopro_chapter"]) == ("1", "1")
        assert video["format"] == "" and video["orientation"] == ""
        assert broken["error"] == "ffprobe failed: bad"
        assert broken["width"] == "" and broken["frame_rate_variable"] == ""

    def test_summary_content(self, tmp_path: Path) -> None:
        _, summary = inventory.write_inventory(
            _records(), tmp_path, ignored=3, skipped=1, sidecars=2, stamp="20261014T120000Z"
        )
        assert summary == tmp_path / "reports" / "inventory-20261014T120000Z-summary.md"
        text = summary.read_text(encoding="utf-8")
        assert "- Dimensions are as stored; apply the orientation column for display." in text
        assert "- Videos: 4" in text
        assert "- Photos: 1" in text
        assert "- Files with probe errors: 1" in text
        assert "- Ignored files (not media, not sidecars): 3" in text
        assert "- Sidecar files (.lrv, .thm; not rows): 2" in text
        assert "- Skipped (vanished before reading, or folder not listable): 1" in text
        assert "- 3840x2160 @ 30 hevc 10-bit 4:2:0: 3" in text
        assert "Variable frame rate: 3" in text
        assert "- 4032x3024: 1" in text
        assert "- HEIF: 1" in text
        assert "- dive1/recording 0001: chapters 1, 2" in text
        assert "recording 0002" not in text
        assert "- Videos with an .LRV sidecar: 3 of 4" in text
        assert "- dive2/GX010003.MP4: ffprobe failed: bad" in text

    def test_photo_sizes_count_only_photos_without_errors(self, tmp_path: Path) -> None:
        good = _records()[0]
        flawed = dataclasses.replace(
            good, path=Path("IMG_0002.HEIC"), width=1000, height=500, error="bit depth unavailable"
        )
        _, summary = inventory.write_inventory([good, flawed], tmp_path, stamp="20261014T120000Z")
        text = summary.read_text(encoding="utf-8")
        assert "- 4032x3024: 1" in text
        assert "1000x500" not in text
        assert "- Files with probe errors: 1" in text

    def test_summary_with_nothing(self, tmp_path: Path) -> None:
        _, summary = inventory.write_inventory([], tmp_path, stamp="20261014T120000Z")
        text = summary.read_text(encoding="utf-8")
        assert "- Videos: 0" in text
        assert text.count("- none") == 5

    def test_collisions_get_a_shared_suffix(self, tmp_path: Path) -> None:
        stamp = "20261014T120000Z"
        names = []
        for _ in range(3):
            csv_path, summary = inventory.write_inventory([], tmp_path, stamp=stamp)
            names.append((csv_path.name, summary.name))
        assert names == [
            ("inventory-20261014T120000Z.csv", "inventory-20261014T120000Z-summary.md"),
            ("inventory-20261014T120000Z-1.csv", "inventory-20261014T120000Z-1-summary.md"),
            ("inventory-20261014T120000Z-2.csv", "inventory-20261014T120000Z-2-summary.md"),
        ]

    def test_summary_collision_alone_moves_both_files(self, tmp_path: Path) -> None:
        reports = tmp_path / "reports"
        reports.mkdir()
        taken = reports / "inventory-20261014T120000Z-summary.md"
        taken.write_text("precious", encoding="utf-8")
        csv_path, summary = inventory.write_inventory([], tmp_path, stamp="20261014T120000Z")
        assert (csv_path.name, summary.name) == (
            "inventory-20261014T120000Z-1.csv",
            "inventory-20261014T120000Z-1-summary.md",
        )
        assert taken.read_text(encoding="utf-8") == "precious"
        assert not (reports / "inventory-20261014T120000Z.csv").exists()

    def test_existing_csv_is_never_overwritten(self, tmp_path: Path) -> None:
        reports = tmp_path / "reports"
        reports.mkdir()
        existing = reports / "inventory-20261014T120000Z.csv"
        existing.write_text("precious", encoding="utf-8")
        csv_path, summary = inventory.write_inventory([], tmp_path, stamp="20261014T120000Z")
        assert existing.read_text(encoding="utf-8") == "precious"
        assert (csv_path.name, summary.name) == (
            "inventory-20261014T120000Z-1.csv",
            "inventory-20261014T120000Z-1-summary.md",
        )

    def test_failed_csv_write_leaves_nothing_behind(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls = 0
        real = inventory._csv_row

        def fail_on_second(record: inventory.Record) -> dict[str, str]:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("disk full")
            return real(record)

        monkeypatch.setattr(inventory, "_csv_row", fail_on_second)
        with pytest.raises(OSError, match="disk full"):
            inventory.write_inventory(_records(), tmp_path, stamp="20261014T120000Z")
        assert list((tmp_path / "reports").iterdir()) == []

    def test_failure_publishing_the_summary_withdraws_the_csv(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        real = inventory._publish
        names = []

        def fail_on_summary(temp: Path, final: Path) -> None:
            names.append(final.name)
            if final.name.endswith("-summary.md"):
                raise OSError("disk full")
            real(temp, final)

        monkeypatch.setattr(inventory, "_publish", fail_on_summary)
        with pytest.raises(OSError, match="disk full"):
            inventory.write_inventory(_records(), tmp_path, stamp="20261014T120000Z")
        assert names == ["inventory-20261014T120000Z.csv", "inventory-20261014T120000Z-summary.md"]
        assert list((tmp_path / "reports").iterdir()) == []

    def test_final_names_appear_complete(self, tmp_path: Path) -> None:
        csv_path, summary = inventory.write_inventory(
            _records(), tmp_path, stamp="20261014T120000Z"
        )
        on_disk = sorted(p.name for p in (tmp_path / "reports").iterdir())
        assert on_disk == sorted([csv_path.name, summary.name])
        with csv_path.open(encoding="utf-8-sig", newline="") as handle:
            assert len(list(csv.DictReader(handle))) == 5

    def test_without_hard_links_the_copy_fallback_still_never_overwrites(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def no_links(src: Any, dst: Any) -> None:
            raise OSError("hard links not supported")

        monkeypatch.setattr(inventory.os, "link", no_links)
        stamp = "20261014T120000Z"
        reports = tmp_path / "reports"
        reports.mkdir()
        (reports / f"inventory-{stamp}.csv").write_text("precious", encoding="utf-8")
        csv_path, summary = inventory.write_inventory(_records(), tmp_path, stamp=stamp)
        assert (csv_path.name, summary.name) == (
            f"inventory-{stamp}-1.csv",
            f"inventory-{stamp}-1-summary.md",
        )
        assert (reports / f"inventory-{stamp}.csv").read_text(encoding="utf-8") == "precious"
        assert csv_path.read_bytes().startswith(b"\xef\xbb\xbf")
        assert sorted(p.name for p in reports.iterdir()) == sorted(
            [f"inventory-{stamp}.csv", csv_path.name, summary.name]
        )

    def test_default_stamp_is_utc_now(self, tmp_path: Path) -> None:
        before = datetime.now(UTC).replace(microsecond=0)
        csv_path, _ = inventory.write_inventory([], tmp_path)
        stamp = csv_path.stem.removeprefix("inventory-")
        parsed = datetime.strptime(stamp, "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
        assert before <= parsed <= datetime.now(UTC)

    def test_unwritable_working_folder_raises_oserror(self, tmp_path: Path) -> None:
        blocker = tmp_path / "blocker"
        blocker.write_text("a file, not a folder", encoding="utf-8")
        with pytest.raises(OSError):
            inventory.write_inventory([], blocker)


class TestMain:
    def test_end_to_end(
        self, tree: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        out = tmp_path / "work"
        before = _snapshot(tree)
        code = inventory.main(["--footage", str(tree), "--out", str(out)])
        captured = capsys.readouterr()
        assert code == 0
        assert _snapshot(tree) == before
        csv_files = sorted((out / "reports").glob("inventory-*.csv"))
        summaries = sorted((out / "reports").glob("inventory-*-summary.md"))
        assert len(csv_files) == len(summaries) == 1
        assert str(csv_files[0]) in captured.out
        assert str(summaries[0]) in captured.out
        assert "shallow with caustics" in captured.out
        assert "static shot" in captured.out
        captured.out.encode("ascii")
        with csv_files[0].open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == 6
        assert all(r["category"] == "" for r in rows)
        assert all("\\" not in r["path"] for r in rows)
        text = summaries[0].read_text(encoding="utf-8")
        assert "- dive1/recording 0001: chapters 1, 2" in text
        assert "- dive2/recording 0003: chapters 1, 2" in text
        assert "- Videos with an .LRV sidecar: 2 of 5" in text

    def test_config_is_not_read_when_both_paths_are_given(self, tree: Path, tmp_path: Path) -> None:
        code = inventory.main(
            [
                "--config",
                str(tmp_path / "missing.toml"),
                "--footage",
                str(tree),
                "--out",
                str(tmp_path / "w"),
            ]
        )
        assert code == 0

    def test_config_supplies_the_missing_path(self, tree: Path, tmp_path: Path) -> None:
        out = tmp_path / "configured-work"
        config = tmp_path / "local.toml"
        config.write_text(f"footage_path = '{tree}'\nworking_path = '{out}'\n", encoding="utf-8")
        assert inventory.main(["--config", str(config)]) == 0
        assert list((out / "reports").glob("inventory-*.csv"))
        other = tmp_path / "other-work"
        assert inventory.main(["--config", str(config), "--out", str(other)]) == 0
        assert list((other / "reports").glob("inventory-*.csv"))

    def test_missing_config_is_an_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        code = inventory.main(["--config", str(tmp_path / "missing.toml"), "--out", str(tmp_path)])
        err = capsys.readouterr().err
        assert code == 2
        assert err.startswith("error: ")
        assert len(err.strip().splitlines()) == 1

    def test_missing_footage_root(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        out = tmp_path / "work"
        code = inventory.main(["--footage", str(tmp_path / "absent"), "--out", str(out)])
        err = capsys.readouterr().err
        assert code == 2
        assert err.startswith("error: footage folder not found")
        assert len(err.strip().splitlines()) == 1
        assert not out.exists()

    def test_footage_root_that_is_a_file(self, tmp_path: Path) -> None:
        not_a_folder = tmp_path / "f"
        not_a_folder.write_bytes(b"")
        assert inventory.main(["--footage", str(not_a_folder), "--out", str(tmp_path / "w")]) == 2

    def test_working_folder_inside_footage_is_refused(
        self, tree: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        before = _snapshot(tree)
        for out in (tree, tree / "dive1", tree / "new"):
            assert inventory.main(["--footage", str(tree), "--out", str(out)]) == 2
        err = capsys.readouterr().err
        assert "outside the footage folder" in err
        assert _snapshot(tree) == before

    def test_reports_folder_linked_into_footage_is_refused(
        self, tree: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        work = tmp_path / "work"
        work.mkdir()
        try:
            os.symlink(tree / "dive1", work / "reports", target_is_directory=True)
        except OSError:
            pytest.skip("cannot create symbolic links here")
        before = _snapshot(tree)
        assert inventory.main(["--footage", str(tree), "--out", str(work)]) == 2
        assert "outside the footage folder" in capsys.readouterr().err
        assert _snapshot(tree) == before

    def test_unwritable_working_folder(
        self, tree: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        blocker = tmp_path / "blocker"
        blocker.write_text("a file", encoding="utf-8")
        code = inventory.main(["--footage", str(tree), "--out", str(blocker)])
        err = capsys.readouterr().err
        assert code == 2
        assert err.startswith("error: cannot write")
        assert len(err.strip().splitlines()) == 1

    def test_running_twice_keeps_both_reports(self, tree: Path, tmp_path: Path) -> None:
        out = tmp_path / "work"
        for _ in range(2):
            assert inventory.main(["--footage", str(tree), "--out", str(out)]) == 0
        assert len(list((out / "reports").glob("inventory-*.csv"))) == 2
        assert len(list((out / "reports").glob("inventory-*-summary.md"))) == 2

    @needs_ffmpeg
    def test_real_media_end_to_end(self, tmp_path: Path) -> None:
        root = tmp_path / "footage"
        (root / "dive").mkdir(parents=True)
        _make_video(root / "dive" / "GX010001.MP4", "-pix_fmt", "yuv420p")
        _make_video(root / "dive" / "GX020001.MP4", "-pix_fmt", "yuv420p")
        (root / "dive" / "GL010001.LRV").write_bytes(b"")
        _make_video(root / "IMG_0002.MOV", "-pix_fmt", "yuv420p")
        _save_with_exif(Image.new("RGB", (64, 48)), root / "IMG_0003.jpg", 1)
        (root / "dive" / "GX030001.MP4").write_bytes(b"cut off")
        out = tmp_path / "work"
        before = _snapshot(root)
        assert inventory.main(["--footage", str(root), "--out", str(out)]) == 0
        assert _snapshot(root) == before
        csv_path = next((out / "reports").glob("inventory-*.csv"))
        with csv_path.open(encoding="utf-8-sig", newline="") as handle:
            rows = {r["path"]: r for r in csv.DictReader(handle)}
        assert sorted(rows) == [
            "IMG_0002.MOV",
            "IMG_0003.jpg",
            "dive/GX010001.MP4",
            "dive/GX020001.MP4",
            "dive/GX030001.MP4",
        ]
        good = rows["dive/GX010001.MP4"]
        assert (good["codec"], good["width"], good["height"], good["error"]) == (
            "h264",
            "64",
            "48",
            "",
        )
        assert (good["gopro_recording"], good["gopro_chapter"], good["lrv_present"]) == (
            "1",
            "1",
            "true",
        )
        assert rows["dive/GX030001.MP4"]["error"] != ""
        assert rows["IMG_0003.jpg"]["orientation"] == "1"
        summary = next((out / "reports").glob("inventory-*-summary.md")).read_text(encoding="utf-8")
        assert "- 64x48 @ 10 h264 8-bit 4:2:0: 3" in summary
        assert "- dive/recording 0001: chapters 1, 2, 3" in summary


@pytest.mark.footage
def test_real_footage_has_one_row_per_media_file(tmp_path: Path) -> None:
    root = load_local_config().footage_path
    media = {
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file()
        and p.suffix.lower() in inventory.VIDEO_EXTENSIONS | inventory.PHOTO_EXTENSIONS
    }
    before = _snapshot(root)
    records = inventory.scan(root)
    assert {r.path.as_posix() for r in records} == media
    assert len(records) == len(media)
    assert _snapshot(root) == before
