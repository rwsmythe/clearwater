"""End-to-end tests of the video sink (WP3.10): V4 on every sample, refusals, failures, safety.

Frames come from a test-side FFmpeg decode (``video_fidelity.decode_frames``) until WP3.9's
decoder is on main; the fidelity instrument (``tools/video_fidelity.py``) checks the outputs.
libx265 always runs; NVENC runs under ``gpu`` and skips where it is unavailable. Synthetic
clips are built under the session's temporary folder; the committed fixtures are read only.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
from collections.abc import Callable, Iterator
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import pytest

import video_fidelity as vf
from clearwater.color import planes_to_rgb, rgb_to_planes
from clearwater.interfaces.image import Frame
from clearwater.interfaces.settings import Settings
from clearwater.interfaces.video import EncoderCapability, Fault, ProbeResult, SinkReport
from clearwater.io.video import (
    FFmpegVideoSink,
    VideoEncodeError,
    detect_capabilities,
    nut,
    probe,
    resolve_encoder,
)
from clearwater.io.video import encode as encode_module
from clearwater.io.video.boxes import read_movie_boxes
from clearwater.io.video.verify import read_packet_table
from clearwater.jobs.naming import MediaKind, plan_output
from clearwater.jobs.safe_write import SafeWrite
from container_spike import compare

pytestmark = pytest.mark.usefixtures("ffmpeg_tools")

Sample = Callable[[str], Path]

DECODABLE = {
    "vid-hevc8-bt709-full": 8,
    "vid-hevc10": 10,
    "vid-untagged": 8,
    "vid-truncated": 8,
    "vid-vfr": 8,
    "vid-rotated": 8,
}


def _nvenc_ready() -> bool:
    return any(c.name == "hevc_nvenc" and c.available for c in detect_capabilities())


def _need(encoder: str) -> None:
    if encoder == "hevc_nvenc" and not _nvenc_ready():
        pytest.skip("NVENC is not available on this machine")


def _cases() -> list[Any]:
    cases = []
    for sample_id, depth in DECODABLE.items():
        for encoder in ("libx265", "hevc_nvenc"):
            marks = [pytest.mark.gpu] if encoder == "hevc_nvenc" else []
            for out_depth in sorted({depth, 10}):
                name = f"{sample_id}-{encoder}-{out_depth}"
                cases.append(pytest.param(sample_id, encoder, out_depth, marks=marks, id=name))
    return cases


# --- shared runs ------------------------------------------------------------------------------


class Runs:
    """Encodes and records cached for the session (each output is made once)."""

    def __init__(self, folder: Path) -> None:
        self.folder = folder
        self._done: dict[tuple[str, str, int], tuple[Path, vf.EncodeRun, dict[str, Any]]] = {}

    def get(
        self, source: Path, encoder: str, depth: int
    ) -> tuple[Path, vf.EncodeRun, dict[str, Any]]:
        key = (str(source), encoder, depth)
        if key not in self._done:
            out = self.folder / f"{source.stem}-{encoder}-{depth}-{len(self._done)}.mp4"
            run = vf.encode_file(source, out, encoder=encoder, bit_depth=depth)
            self._done[key] = (out, run, vf.fidelity_record(source, out, bit_depth=depth, run=run))
        return self._done[key]


@pytest.fixture(scope="session")
def runs(tmp_path_factory: pytest.TempPathFactory) -> Runs:
    return Runs(tmp_path_factory.mktemp("wp310-runs"))


def _ffmpeg(*args: str) -> None:
    subprocess.run(
        ["ffmpeg", "-nostdin", "-hide_banner", "-v", "error", "-y", *args],
        check=True,
        capture_output=True,
    )


class Clips:
    """Synthetic sources built once per session under the temporary folder."""

    def __init__(self, folder: Path) -> None:
        self.folder = folder

    def make(
        self,
        name: str,
        *,
        codec: str = "libx265",
        bframes: bool = False,
        offset: str = "0.5",
        rate: str = "30",
        size: str = "320x240",
        duration: str = "2",
        vf_chain: str | None = None,
        out_options: tuple[str, ...] = (),
        colour: tuple[str, str, str, str] = ("bt709", "bt709", "bt709", "tv"),
    ) -> Path:
        path = self.folder / f"{name}.mp4"
        if path.exists():
            return path
        extra = ["-vf", vf_chain, "-fps_mode", "passthrough"] if vf_chain else []
        extra += [] if bframes else ["-bf", "0"]
        extra += ["-x265-params", "log-level=error"] if codec == "libx265" else []
        primaries, transfer, matrix, range_ = colour
        _ffmpeg(
            "-f", "lavfi", "-i", f"testsrc2=size={size}:rate={rate}:duration={duration}",
            "-f", "lavfi", "-i", f"sine=frequency=440:sample_rate=48000:duration={duration}",
            *extra, "-c:v", codec, "-pix_fmt", "yuv420p",
            "-color_primaries", primaries, "-color_trc", transfer, "-colorspace", matrix,
            "-color_range", range_, "-c:a", "aac", "-output_ts_offset", offset,
            *out_options, str(path),
        )  # fmt: skip
        return path


@pytest.fixture(scope="session")
def clips(tmp_path_factory: pytest.TempPathFactory) -> Clips:
    return Clips(tmp_path_factory.mktemp("wp310-clips"))


def _items(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["name"]: item for item in record["items"]}


def _assert_v4(record: dict[str, Any]) -> None:
    summary = record["summary"]
    wrong = summary["different_items"]
    assert summary["mandatory_and_required_all_same"], (wrong["MANDATORY"], wrong[compare.REQUIRED])
    assert _items(record)[vf._ROSTER_ITEM]["status"] == "SAME"


def _write_all(
    sink: FFmpegVideoSink,
    source: Path,
    out: Path,
    *,
    encoder: str = "libx265",
    depth: int | None = None,
    provenance: dict[str, Any] | None = None,
    info: ProbeResult | None = None,
    frames: Iterator[Frame] | None = None,
) -> SinkReport:
    info = info or probe(source)
    out.write_bytes(b"")
    sink.open(
        info,
        out,
        encoder=encoder,
        quality="standard",
        bit_depth=depth or info.video.bit_depth,
        provenance=provenance,
    )
    for frame in frames if frames is not None else vf.decode_frames(source, info):
        sink.write(frame)
    return sink.close()


class _Planted(FFmpegVideoSink):
    """The product sink with a changed FFmpeg command (a planted wrong implementation)."""

    def __init__(self, change: Callable[[list[str]], list[str]]) -> None:
        super().__init__()
        self._change = change

    def _command(self, command: list[str]) -> list[str]:
        return self._change(list(command))


def _without(command: list[str], option: str, values: int = 1) -> list[str]:
    at = command.index(option)
    return command[:at] + command[at + 1 + values :]


def _replace(command: list[str], option: str, value: str) -> list[str]:
    command = list(command)
    command[command.index(option) + 1] = value
    return command


# --- V4 on every WP2.3 sample -----------------------------------------------------------------


@pytest.mark.parametrize(("sample_id", "encoder", "depth"), _cases())
def test_every_sample_keeps_every_mandatory_and_required_item(
    sample: Sample, runs: Runs, sample_id: str, encoder: str, depth: int
) -> None:
    _need(encoder)
    _, run, record = runs.get(sample(sample_id), encoder, depth)
    _assert_v4(record)
    assert _items(record)["video frame count"]["output"] == run.report.frames_written
    assert record["bit_depth"] == depth
    if sample_id == "vid-truncated":
        assert any("cut short" in w for w in run.report.warnings)
        assert any(n.startswith("D86") for n in record["summary"]["notes"])


def test_vfr_pts_are_exact(sample: Sample, runs: Runs) -> None:
    source = sample("vid-vfr")
    assert probe(source).video.vfr
    out, _, record = runs.get(source, "libx265", 8)
    pts = _items(record)["video per-frame pts (presentation, exact, full sequence)"]
    assert pts["status"] == "SAME"
    written = sorted(read_packet_table(out).video_pts)
    assert written == sorted(read_packet_table(source).video_pts)


def test_rotation_is_kept(sample: Sample, runs: Runs) -> None:
    out, _, _ = runs.get(sample("vid-rotated"), "libx265", 8)
    assert probe(out).video.rotation == 90


def test_untagged_source_is_tagged_bt709_limited_with_a_warning(sample: Sample, runs: Runs) -> None:
    out, run, _ = runs.get(sample("vid-untagged"), "libx265", 8)
    color = probe(out).video.color
    assert (color.primaries, color.transfer, color.matrix, color.range) == (
        "bt709",
        "bt709",
        "bt709",
        "limited",
    )
    assert not color.assumed
    assert any("assumed values" in w for w in run.report.warnings)


def test_ten_bit_source_stays_ten_bit(sample: Sample, runs: Runs) -> None:
    out, _, _ = runs.get(sample("vid-hevc10"), "libx265", 10)
    assert probe(out).video.bit_depth == 10


@pytest.mark.parametrize(("sample_id", "name"), [("vid-hlg", "HLG"), ("vid-pq", "PQ")])
def test_hdr_sources_are_refused_at_open(
    sample: Sample, tmp_path: Path, sample_id: str, name: str
) -> None:
    out = tmp_path / "out.mp4"
    out.write_bytes(b"")
    with pytest.raises(VideoEncodeError) as caught:
        FFmpegVideoSink().open(
            probe(sample(sample_id)), out, encoder="libx265", quality="standard",
            bit_depth=10, provenance=None,
        )  # fmt: skip
    assert caught.value.kind == "refused" and name in str(caught.value)
    assert out.stat().st_size == 0


# --- synthetic sources ------------------------------------------------------------------------


def test_start_offset_with_an_empty_edit(clips: Clips, runs: Runs) -> None:
    source = clips.make("offset")
    assert probe(source).edit_list[0].media_time_s is None
    out, _, record = runs.get(source, "libx265", 8)
    _assert_v4(record)
    assert probe(out).edit_list == probe(source).edit_list


@pytest.mark.parametrize(
    ("name", "options"),
    [
        ("bf-x264-offset", {"codec": "libx264", "bframes": True}),
        ("bf-x265-offset", {"codec": "libx265", "bframes": True}),
        (
            "bf-x264-ntsc",
            {"codec": "libx264", "bframes": True, "offset": "0", "rate": "30000/1001"},
        ),
    ],
)
def test_bframe_sources_by_presentation_effect(
    clips: Clips, runs: Runs, name: str, options: dict[str, Any]
) -> None:
    source = clips.make(name, **options)
    for encoder in ("libx265", *(["hevc_nvenc"] if _nvenc_ready() else [])):
        _, _, record = runs.get(source, encoder, 8)
        _assert_v4(record)
        items = _items(record)
        for exact_item in (
            "video per-frame pts (presentation, exact, full sequence)",
            "start offset: first video frame pts",
            "video stream duration",
            vf.EDIT_EFFECT,
        ):
            assert items[exact_item]["status"] == "SAME"
        as_written = items[vf.VIDEO_EDIT_AS_WRITTEN]
        if as_written["source"] != as_written["output"]:  # media_time differs: AD-22 says so
            assert as_written["note"].startswith("AD-22")
            assert as_written["note"] in record["summary"]["notes"]


@pytest.mark.parametrize("bframes", [False, True], ids=["plain", "bframes"])
def test_an_absent_edit_list_is_the_identity_with_a_note(
    clips: Clips, runs: Runs, bframes: bool
) -> None:
    source = clips.make(
        f"noedit-{bframes}", codec="libx264", bframes=bframes, offset="0",
        out_options=("-use_editlist", "0"),
    )  # fmt: skip
    assert probe(source).edit_list == ()
    _, _, record = runs.get(source, "libx265", 8)
    _assert_v4(record)
    note = _items(record)[vf.VIDEO_EDIT_AS_WRITTEN]["note"]
    assert note.startswith("AD-22 extended (Q-C)") and note in record["summary"]["notes"]


@pytest.mark.parametrize(
    ("name", "options"),
    [
        ("tc-offset", {"offset": "0.25", "out_options": ("-timecode", "01:00:00:00")}),
        (
            "tc-dropframe",
            {
                "rate": "30000/1001",
                "offset": "0",
                "out_options": ("-timecode", "16:31:28;19", "-video_track_timescale", "30000"),
            },
        ),
    ],
)
def test_the_timecode_track_is_regenerated(
    clips: Clips, runs: Runs, name: str, options: dict[str, Any]
) -> None:
    source = clips.make(name, **options)
    _, run, record = runs.get(source, "libx265", 8)
    _assert_v4(record)
    items = _items(record)
    tmcd = [i for n, i in items.items() if n.startswith("timecode track tmcd")]
    assert tmcd and all(i["status"] == "SAME" for i in tmcd)
    assert items["timecode value (stream tags)"]["status"] == "SAME"
    assert "timecode track" not in run.report.not_carried


def test_a_variable_rate_gap_with_an_offset(clips: Clips, runs: Runs) -> None:
    source = clips.make("vfr-gap", vf_chain="select='not(between(n,10,14))'")
    assert probe(source).video.vfr
    _, _, record = runs.get(source, "libx265", 8)
    _assert_v4(record)


def test_d76_from_a_bt601_source(clips: Clips, runs: Runs) -> None:
    source = clips.make(
        "bt601", codec="libx264", offset="0", colour=("smpte170m", "smpte170m", "smpte170m", "tv")
    )
    info = probe(source)
    assert info.video.color.matrix == "bt601"
    _, run, record = runs.get(source, "libx265", 10)
    _assert_v4(record)
    assert probe(Path(record["output"])).video.bit_depth == 10
    assert any("assumed values" in w for w in run.report.warnings)  # Q17: BT.709 primaries


@pytest.mark.slow
def test_a_short_5k_8_by_7_clip(clips: Clips, runs: Runs) -> None:
    source = clips.make("5k3", size="5312x4648", duration="0.1", offset="0")
    _, _, record = runs.get(source, "libx265", 8)
    _assert_v4(record)
    assert _items(record)["frame size and sample aspect ratio"]["output"][:2] == [5312, 4648]


def test_a_truncated_source_cuts_audio_at_the_readable_end(
    clips: Clips, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = clips.make("long-audio")
    info = probe(source)
    table = read_packet_table(source)
    ordered = sorted(table.video_pts)
    cut_pts = ordered[30]  # the first "unreadable" frame; a cut file lists nothing after it
    kept_pts = tuple(p for p in table.video_pts if p <= cut_pts)
    planted = replace(table, video_pts=kept_pts, video_corrupt_pts=(cut_pts,))
    monkeypatch.setattr(
        encode_module,
        "read_packet_table",
        lambda p: planted if p == source else read_packet_table(p),
    )
    fault = Fault("truncated", "warn", "cut short")
    info = replace(info, faults=(*info.faults, fault))
    frames = (f for f in vf.decode_frames(source, info) if f.pts_ticks < cut_pts)
    out = tmp_path / "out.mp4"
    report = _write_all(FFmpegVideoSink(), source, out, info=info, frames=frames)
    assert report.frames_written == 30
    end = cut_pts * info.video.time_base
    base = Fraction(1, 48000)
    source_audio = compare.stream_packets(source, info.audio[0].index, base)
    output_audio = compare.stream_packets(out, 1, base)
    kept = [p for p in source_audio if p.pts is not None and p.pts < end]
    assert [(p.pts, p.md5) for p in output_audio] == [(p.pts, p.md5) for p in kept]
    assert len(kept) < len(source_audio)


# --- the transport ----------------------------------------------------------------------------


class _Capture(FFmpegVideoSink):
    """Captures what FFmpeg receives (raw frames and their timing) in place of the encoder."""

    def __init__(self, folder: Path) -> None:
        super().__init__()
        self.raw = folder / "frames.raw"
        self.md5 = folder / "frames.md5"

    def _command(self, command: list[str]) -> list[str]:
        head = ["ffmpeg", "-nostdin", "-v", "error", "-y", "-bsf:v", nut.INPUT_BITSTREAM_FILTER]
        head += ["-f", "nut", "-i", "pipe:0", "-map", "0", "-c:v", "rawvideo", "-f", "rawvideo"]
        tail = ["-map", "0", "-c:v", "rawvideo", "-fps_mode", "passthrough"]
        tail += ["-enc_time_base:v", "demux", "-f", "framemd5"]
        return [*head, str(self.raw), *tail, str(self.md5)]

    def _verify(self, end: int) -> SinkReport:
        self.end = end
        return SinkReport(len(self._written), (), ())


@pytest.mark.parametrize(
    ("sample_id", "depth"),
    [("vid-vfr", 8), ("vid-hevc10", 10), ("vid-hevc8-bt709-full", 10)],
    ids=["8-bit", "10-bit", "d76-8-to-10"],
)
def test_ffmpeg_receives_the_quantised_frames_with_their_exact_pts(
    sample: Sample, tmp_path: Path, sample_id: str, depth: int
) -> None:
    source = sample(sample_id)
    info = probe(source)
    frames = list(vf.decode_frames(source, info))
    sink = _Capture(tmp_path)
    _write_all(sink, source, tmp_path / "unused.mp4", depth=depth, frames=iter(frames))
    expected = [rgb_to_planes(np.ascontiguousarray(f.pixels), bit_depth=depth) for f in frames]
    assert sink.raw.read_bytes() == b"".join(expected)
    rows = [
        [cell.strip() for cell in line.split(",")]
        for line in sink.md5.read_text().splitlines()
        if not line.startswith("#")
    ]
    pts = [f.pts_ticks for f in frames]
    assert [int(r[2]) for r in rows] == pts
    assert [int(r[3]) for r in rows] == [
        b - a for a, b in zip(pts, [*pts[1:], sink.end], strict=True)
    ]
    assert [r[5] for r in rows] == [hashlib.md5(e).hexdigest() for e in expected]
    if depth != info.video.bit_depth:  # DR-39 (a): the D76 RGB-side leg against AD-11 (V9)
        size = len(expected[0])
        worst, total, count = 0.0, 0.0, 0
        for frame, planes in zip(frames, expected, strict=True):
            back = planes_to_rgb(
                planes, width=info.video.width, height=info.video.height, bit_depth=depth
            )
            diff = np.abs(back.astype(np.float64) - frame.pixels.astype(np.float64))
            worst, total, count = (
                max(worst, float(diff.max())),
                total + float(diff.sum()),
                count + diff.size,
            )
            assert len(planes) == size
        assert worst <= 2 / 255 and total / count <= 0.2 / 255
        assert worst <= 0.13 / 255  # the calculated 0.123/255 (DR-39 (a))


# --- refusals at open -------------------------------------------------------------------------


@pytest.fixture
def no_ffmpeg_start(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("FFmpeg must not start for a refused open")

    monkeypatch.setattr(FFmpegVideoSink, "_start", refuse)


def _open(source: Path, out: Path, **changes: Any) -> None:
    options: dict[str, Any] = {
        "encoder": "libx265",
        "quality": "standard",
        "bit_depth": probe(source).video.bit_depth,
        "provenance": None,
    }
    options.update(changes)
    out.write_bytes(b"")
    FFmpegVideoSink().open(probe(source), out, **options)


@pytest.mark.usefixtures("no_ffmpeg_start")
@pytest.mark.parametrize(
    ("changes", "kind", "words"),
    [
        ({"encoder": "auto"}, "refused", "resolve"),
        ({"encoder": "h264_nvenc"}, "refused", "h264_nvenc"),
        ({"bit_depth": 12}, "refused", "bit depth 12"),
        ({"bit_depth": 8.0}, "refused", "bit depth 8.0"),
        ({"bit_depth": True}, "refused", "bit depth True"),
        ({"quality": "High"}, "refused", "quality level 'High'"),
        ({"quality": "best"}, "refused", "quality level 'best'"),
        ({"provenance": {1: "x"}}, "refused", "provenance"),
        ({"provenance": {"a": float("nan")}}, "refused", "provenance"),
        ({"provenance": {"a": "x" * 20000}}, "refused", "at most 16384"),
    ],
    ids=["auto", "unknown", "12", "float", "bool", "case", "level", "int-key", "nan", "16kib"],
)
def test_open_refuses_by_name(
    sample: Sample, tmp_path: Path, changes: dict[str, Any], kind: str, words: str
) -> None:
    out = tmp_path / "out.mp4"
    with pytest.raises(VideoEncodeError) as caught:
        _open(sample("vid-vfr"), out, **changes)
    assert caught.value.kind == kind and words in str(caught.value)
    assert out.stat().st_size == 0


@pytest.mark.usefixtures("no_ffmpeg_start")
def test_open_refuses_8_bit_output_for_a_10_bit_source(sample: Sample, tmp_path: Path) -> None:
    with pytest.raises(VideoEncodeError) as caught:
        _open(sample("vid-hevc10"), tmp_path / "out.mp4", bit_depth=8)
    assert caught.value.kind == "refused" and "D76" in str(caught.value)


@pytest.mark.usefixtures("no_ffmpeg_start")
def test_open_refuses_an_unavailable_encoder_or_depth_with_the_reason(
    sample: Sample, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    caps = (
        EncoderCapability("hevc_nvenc", False, "No NVIDIA graphics card was found.", (), True),
        EncoderCapability("libx265", True, None, (8,), False),
    )
    monkeypatch.setattr(FFmpegVideoSink, "capabilities", lambda self: caps)
    with pytest.raises(VideoEncodeError) as caught:
        _open(sample("vid-vfr"), tmp_path / "a.mp4", encoder="hevc_nvenc")
    assert caught.value.kind == "unavailable" and "No NVIDIA graphics card" in str(caught.value)
    with pytest.raises(VideoEncodeError) as caught:
        _open(sample("vid-vfr"), tmp_path / "b.mp4", bit_depth=10)
    assert caught.value.kind == "unavailable" and "10-bit" in str(caught.value)


@pytest.mark.usefixtures("no_ffmpeg_start")
def test_open_refuses_non_square_pixels(clips: Clips, tmp_path: Path) -> None:
    source = clips.make("sar", codec="libx264", offset="0", vf_chain="setsar=2/1")
    with pytest.raises(VideoEncodeError) as caught:
        _open(source, tmp_path / "out.mp4")
    assert caught.value.kind == "refused" and "non-square pixels" in str(caught.value)


def test_open_twice_is_refused(sample: Sample, tmp_path: Path) -> None:
    sink = FFmpegVideoSink()
    info = probe(sample("vid-vfr"))
    out = tmp_path / "out.mp4"
    out.write_bytes(b"")
    sink.open(info, out, encoder="libx265", quality="draft", bit_depth=8, provenance=None)
    try:
        with pytest.raises(VideoEncodeError) as caught:
            sink.open(info, out, encoder="libx265", quality="draft", bit_depth=8, provenance=None)
        assert caught.value.kind == "state"
    finally:
        sink.abort()
    assert not out.exists()


# --- write rules, failures and abort ----------------------------------------------------------


def _opened(source: Path, out: Path) -> tuple[FFmpegVideoSink, list[Frame]]:
    info = probe(source)
    frames = list(vf.decode_frames(source, info))
    out.write_bytes(b"")
    sink = FFmpegVideoSink()
    sink.open(info, out, encoder="libx265", quality="draft", bit_depth=8, provenance=None)
    return sink, frames


@pytest.mark.parametrize(
    ("plant", "words"),
    [
        (lambda f, fs: replace(f, time_base=Fraction(1, 90000)), "time base"),
        (lambda f, fs: fs[0], "does not follow"),
        (lambda f, fs: replace(f, pts_ticks=f.pts_ticks + 1), "not a pts of the source"),
        (lambda f, fs: replace(f, pixels=f.pixels[:-2]), "shape"),
        (lambda f, fs: replace(f, pixels=f.pixels.astype(np.float64)), "float32"),
        (lambda f, fs: replace(f, device="cuda:0"), "to_host"),
        (lambda f, fs: replace(f, pixels=np.full_like(f.pixels, np.nan)), "NaN"),
    ],
    ids=["time-base", "order", "foreign-pts", "shape", "dtype", "device", "nan"],
)
def test_write_refuses_a_bad_frame_and_deletes_the_output(
    sample: Sample, tmp_path: Path, plant: Callable[[Frame, list[Frame]], Frame], words: str
) -> None:
    out = tmp_path / "out.mp4"
    sink, frames = _opened(sample("vid-vfr"), out)
    sink.write(frames[0])
    sink.write(frames[1])
    with pytest.raises(VideoEncodeError) as caught:
        sink.write(plant(frames[2], frames))
    assert caught.value.kind == "frame" and words in str(caught.value)
    assert not out.exists()
    sink.abort()  # a no-op after a failure; never raises
    with pytest.raises(VideoEncodeError) as again:
        sink.write(frames[2])
    assert again.value.kind == "state"


def test_a_dead_encoder_is_seen_at_the_next_write(sample: Sample, tmp_path: Path) -> None:
    out = tmp_path / "out.mp4"
    sink, frames = _opened(sample("vid-vfr"), out)
    sink.write(frames[0])
    process = sink._process
    assert process is not None
    process.kill()
    process.wait()
    started = time.monotonic()
    with pytest.raises(VideoEncodeError) as caught:
        for frame in frames[1:]:
            sink.write(frame)
    assert caught.value.kind == "encoder_failed"
    assert time.monotonic() - started < 15
    assert not out.exists()


def test_an_encoder_error_carries_its_stderr(sample: Sample, tmp_path: Path) -> None:
    out = tmp_path / "out.mp4"
    sink = _Planted(lambda c: _replace(c, "-c:v", "no_such_encoder"))
    with pytest.raises(VideoEncodeError) as caught:
        _write_all(sink, sample("vid-vfr"), out)
    assert caught.value.kind == "encoder_failed"
    assert "no_such_encoder" in str(caught.value) and str(caught.value).isascii()
    assert not out.exists()


def test_close_without_frames_and_calls_out_of_order(sample: Sample, tmp_path: Path) -> None:
    out = tmp_path / "out.mp4"
    sink, frames = _opened(sample("vid-vfr"), out)
    with pytest.raises(VideoEncodeError) as caught:
        sink.close()
    assert caught.value.kind == "state" and "No frames" in str(caught.value)
    assert not out.exists()
    fresh = FFmpegVideoSink()
    for call in (lambda: fresh.write(frames[0]), fresh.close):
        with pytest.raises(VideoEncodeError) as caught:
            call()
        assert caught.value.kind == "state"
    fresh.abort()
    fresh.abort()


def test_abort_is_idempotent_and_deletes_only_out_path(sample: Sample, tmp_path: Path) -> None:
    out = tmp_path / "out.mp4"
    neighbour = tmp_path / "neighbour.mp4"
    neighbour.write_bytes(b"keep")
    sink, frames = _opened(sample("vid-vfr"), out)
    sink.write(frames[0])
    sink.abort()
    sink.abort()
    assert not out.exists() and neighbour.read_bytes() == b"keep"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["neighbour.mp4"]


def test_a_cleanup_error_never_replaces_the_original_error(
    sample: Sample, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "out.mp4"
    sink, frames = _opened(sample("vid-vfr"), out)

    def stuck(path: Path) -> None:
        raise PermissionError("the file is in use")

    monkeypatch.setattr(encode_module, "_remove", stuck)
    with pytest.raises(VideoEncodeError) as caught:
        sink.write(replace(frames[0], device="cuda:0"))
    assert caught.value.kind == "frame"
    assert any("in use" in note for note in getattr(caught.value, "__notes__", []))
    sink.abort()  # never raises, even now
    monkeypatch.undo()
    out.unlink(missing_ok=True)


# --- composition with the safe write (N8, 8.4) ------------------------------------------------


def _copy_source(sample: Sample, tmp_path: Path) -> tuple[Path, bytes, int]:
    folder = tmp_path / "media"
    folder.mkdir()
    source = folder / "GX000001.MP4"
    shutil.copyfile(sample("vid-vfr"), source)
    return source, source.read_bytes(), source.stat().st_mtime_ns


def test_safe_write_composition_commits_a_playable_file(sample: Sample, tmp_path: Path) -> None:
    source, data, mtime = _copy_source(sample, tmp_path)
    info = probe(source)
    plan = plan_output(source, Settings(), MediaKind.VIDEO)
    sink = FFmpegVideoSink()
    with SafeWrite(plan) as write:
        sink.open(info, write.temp_path, encoder="libx265", quality="draft", bit_depth=8,
                  provenance=None)  # fmt: skip
        for frame in vf.decode_frames(source, info):
            sink.write(frame)
        report = sink.close()
        final = write.commit()
    assert report.frames_written == info.video.nb_frames
    assert probe(final).video.nb_frames == info.video.nb_frames
    assert sorted(p.name for p in source.parent.iterdir()) == sorted([source.name, final.name])
    assert source.read_bytes() == data and source.stat().st_mtime_ns == mtime


def test_safe_write_composition_leaves_nothing_on_failure(sample: Sample, tmp_path: Path) -> None:
    source, data, mtime = _copy_source(sample, tmp_path)
    info = probe(source)
    plan = plan_output(source, Settings(), MediaKind.VIDEO)
    sink = FFmpegVideoSink()
    with pytest.raises(VideoEncodeError), SafeWrite(plan) as write:
        sink.open(info, write.temp_path, encoder="libx265", quality="draft", bit_depth=8,
                  provenance=None)  # fmt: skip
        for number, frame in enumerate(vf.decode_frames(source, info)):
            sink.write(replace(frame, device="cuda:0") if number == 5 else frame)
    assert [p.name for p in source.parent.iterdir()] == [source.name]
    assert source.read_bytes() == data and source.stat().st_mtime_ns == mtime


# --- provenance (D91) -------------------------------------------------------------------------


def _comment(path: Path) -> str | None:
    done = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-of",
            "json",
            "-show_entries",
            "format_tags=comment",
            str(path),
        ],
        capture_output=True,
        check=True,
    )
    tags = json.loads(done.stdout).get("format", {}).get("tags", {})
    return tags.get("comment")


def test_provenance_is_embedded_and_parseable(sample: Sample, tmp_path: Path) -> None:
    provenance = {
        "format_version": 1,
        "app_version": "0.1.0",
        "settings": {"video_encoder": "libx265", "quality_level": "standard"},
        "note": 'caf\u00e9 "quoted" back\\slash',
    }
    out = tmp_path / "out.mp4"
    _write_all(FFmpegVideoSink(), sample("vid-vfr"), out, provenance=provenance)
    text = _comment(out)
    assert text is not None and json.loads(text) == provenance


def test_no_provenance_leaves_no_comment_even_from_a_commented_source(
    clips: Clips, tmp_path: Path
) -> None:
    source = clips.make("commented", offset="0", out_options=("-metadata", "comment=old"))
    assert _comment(source) == "old"
    out = tmp_path / "out.mp4"
    _write_all(FFmpegVideoSink(), source, out)
    assert _comment(out) in (None, "")


# --- planted wrong implementations fail by name -----------------------------------------------


def _media_time_verbatim(source: Path, out: Path) -> None:
    """Rewrite the output's video media_time to the source's (the AD-22 alternative)."""
    data = bytearray(out.read_bytes())
    wanted = next(e.media_time_s for e in probe(source).edit_list if e.media_time_s is not None)
    scale = read_movie_boxes(out).video_timescale
    assert scale is not None
    at = data.index(b"elst")
    version = data[at + 4]
    count = int.from_bytes(data[at + 8 : at + 12], "big")
    entry = at + 12
    size = 20 if version == 1 else 12
    for _ in range(count):
        width = 8 if version == 1 else 4
        media = entry + width
        value = int.from_bytes(data[media : media + width], "big", signed=True)
        if value != -1:
            data[media : media + width] = int(wanted * scale).to_bytes(width, "big", signed=True)
        entry += size
    out.write_bytes(bytes(data))


def test_planted_cfr_is_caught(sample: Sample, tmp_path: Path) -> None:
    sink = _Planted(lambda c: [*_replace(c, "-fps_mode", "cfr")[:-3], "-r", "30", *c[-3:]])
    with pytest.raises(VideoEncodeError) as caught:
        _write_all(sink, sample("vid-vfr"), tmp_path / "out.mp4")
    assert caught.value.kind == "verify_failed" and "video" in str(caught.value)


def test_planted_zeroed_start_offset_is_caught(clips: Clips, tmp_path: Path) -> None:
    sink = _Planted(lambda c: _without(c, "-copyts", 0))
    with pytest.raises(VideoEncodeError) as caught:
        _write_all(sink, clips.make("offset"), tmp_path / "out.mp4")
    assert caught.value.kind == "verify_failed" and "video" in str(caught.value)


def test_planted_verbatim_media_time_is_caught(clips: Clips, tmp_path: Path) -> None:
    source = clips.make("bf-x264-offset", codec="libx264", bframes=True)
    out = tmp_path / "out.mp4"
    _write_all(FFmpegVideoSink(), source, out)
    _media_time_verbatim(source, out)
    record = vf.fidelity_record(source, out)
    items = _items(record)
    assert not record["summary"]["mandatory_all_same"]
    assert (
        items["video per-frame pts (presentation, exact, full sequence)"]["status"] == "DIFFERENT"
    )
    assert not items[vf.VIDEO_EDIT_AS_WRITTEN]["note"].startswith("AD-22")


def _no_colour(command: list[str]) -> list[str]:
    for option in ("-color_primaries", "-color_trc", "-colorspace", "-color_range"):
        command = _without(command, option)
    vf_at = command.index("-vf") + 1
    command[vf_at] = command[vf_at].partition(",setparams=")[0]
    return command


def test_planted_missing_colour_tags_are_caught(sample: Sample, tmp_path: Path) -> None:
    source = sample("vid-untagged")
    out = tmp_path / "out.mp4"
    _write_all(_Planted(_no_colour), source, out)
    items = _items(vf.fidelity_record(source, out))
    assert items["colour primaries"]["status"] == "DIFFERENT"
    assert items["colour transfer"]["status"] == "DIFFERENT"


def test_planted_limited_range_on_a_full_range_source_is_caught(
    sample: Sample, tmp_path: Path
) -> None:
    def to_tv(command: list[str]) -> list[str]:
        command = _replace(command, "-color_range", "tv")
        vf_at = command.index("-vf") + 1
        command[vf_at] = command[vf_at].replace("range=pc", "range=tv")
        return command

    source = sample("vid-hevc8-bt709-full")
    out = tmp_path / "out.mp4"
    _write_all(_Planted(to_tv), source, out)
    items = _items(vf.fidelity_record(source, out))
    assert items["colour range"]["status"] == "DIFFERENT"


def test_planted_dropped_rotation_is_caught(sample: Sample, tmp_path: Path) -> None:
    sink = _Planted(lambda c: _without(c, "-display_rotation"))
    with pytest.raises(VideoEncodeError) as caught:
        _write_all(sink, sample("vid-rotated"), tmp_path / "out.mp4")
    assert caught.value.kind == "verify_failed" and "display rotation" in str(caught.value)


def test_planted_audio_reencode_is_caught(sample: Sample, tmp_path: Path) -> None:
    source = sample("vid-vfr")
    out = tmp_path / "out.mp4"
    sink = _Planted(lambda c: _replace(c, "-c:a", "aac"))
    try:
        _write_all(sink, source, out)
    except VideoEncodeError as error:  # the count check may see it first
        assert error.kind == "verify_failed" and "audio" in str(error)
        return
    items = _items(vf.fidelity_record(source, out))
    audio = [i for n, i in items.items() if n.startswith(vf.AUDIO_PACKETS)]
    assert audio and any(i["status"] == "DIFFERENT" for i in audio)


def test_planted_8_bit_output_for_a_10_bit_source_is_caught(sample: Sample, tmp_path: Path) -> None:
    def eight(command: list[str]) -> list[str]:
        return _replace(_replace(command, "-pix_fmt", "yuv420p"), "-profile:v", "main")

    source = sample("vid-hevc10")
    out = tmp_path / "out.mp4"
    _write_all(_Planted(eight), source, out)
    items = _items(vf.fidelity_record(source, out))
    assert items["bit depth"]["status"] == "DIFFERENT"


# --- capabilities -----------------------------------------------------------------------------


def test_real_capabilities_and_the_auto_rule() -> None:
    caps = {c.name: c for c in detect_capabilities(refresh=True)}
    assert set(caps) == {"hevc_nvenc", "libx265"}
    assert caps["libx265"].available and caps["libx265"].bit_depths == (8, 10)
    assert not caps["libx265"].hw and caps["hevc_nvenc"].hw
    for cap in caps.values():
        assert cap.available == (cap.reason is None)
    resolved = resolve_encoder("auto", tuple(caps.values()))
    assert resolved == ("hevc_nvenc" if caps["hevc_nvenc"].available else "libx265")


@pytest.mark.gpu
def test_nvenc_is_detected_with_both_depths() -> None:
    if not _nvenc_ready():
        pytest.skip("NVENC is not available on this machine")
    nvenc = next(c for c in detect_capabilities() if c.name == "hevc_nvenc")
    assert nvenc.bit_depths == (8, 10)


# --- the real clip ----------------------------------------------------------------------------


@pytest.mark.footage
@pytest.mark.gpu
@pytest.mark.slow
def test_gx011627_through_the_sink_keeps_every_mandatory_and_required_item(
    tmp_path: Path,
) -> None:
    from local_config import FootageLookupError, find_footage_file, load_local_config

    if not _nvenc_ready():
        pytest.skip("NVENC is not available on this machine")
    config = load_local_config()
    try:
        source = find_footage_file("GX011627", config.footage_path)
    except FootageLookupError as error:
        if error.matches:
            raise
        pytest.skip("GX011627 is not in the footage folder")
    out = tmp_path / "GX011627-out.mp4"
    run = vf.encode_file(source, out, encoder="hevc_nvenc", quality="standard", bit_depth=8)
    record = vf.fidelity_record(source, out, bit_depth=8, run=run)
    _assert_v4(record)
    assert run.report.frames_written == 681
    os.remove(out)
