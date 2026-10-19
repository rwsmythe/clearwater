"""Tests of ``prototype.clip`` (the whole-clip runner) and of ``bench.py``'s real-frame modes.

WP1.2 Part B. The synthetic clips are built with FFmpeg under pytest's temporary folder,
which plays the working folder (``<tmp>/work/wp1.2b``) beside an empty test footage
folder; only the ``footage`` test reads the owner's footage, by stem, as an input.
"""

from __future__ import annotations

import dataclasses
import io
import json
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from container_spike import compare, spike
from local_config import find_footage_file, load_local_config
from lookcheck.frames import OutputPathError, OutputRoots
from prototype import bench, clip, temporal
from prototype.backend import select_backend
from prototype.params import Params
from prototype.pipeline import correct

pytestmark = pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="ffmpeg/ffprobe not on PATH",
)

GPU = select_backend("auto")
requires_gpu = pytest.mark.skipif(GPU.name != "gpu", reason=f"no CUDA device usable: {GPU.reason}")

PSNR_FLOOR_DB = 40.0
"""The neutral export's Y PSNR against its source must reach this (the encode's floor).
Measured on the synthetic clip at the WP1.5 NVENC settings (cq 20): Y 49.2 dB, U 43.5,
V 41.4. The same output shifted by one frame scores Y 23.7 dB, so a misaligned export
falls far below the floor. The frames fed to the encoder are the decoded source bytes
exactly (the identity test below); the loss is the encode's own."""

CLIP_FRAMES = 60
"""Frames of the synthetic clip: 2 s at 30000/1001 fps."""


# --- fixtures ---------------------------------------------------------------------------------


def _ffmpeg(output: Path, *arguments: str) -> Path:
    """Run FFmpeg writing ``output`` (inside the test tree only)."""
    subprocess.run(
        ["ffmpeg", "-nostdin", "-hide_banner", "-v", "error", "-y", *arguments, str(output)],
        check=True,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        env=compare.tool_env(),
    )
    return output


def _synthetic(path: Path, offset: str | None = None) -> Path:
    """60 frames of 960x540 testsrc2 at 30000/1001 fps + 2 s of sine: HEVC 8-bit 4:2:0 + AAC.

    BT.709 full range, as the owner's GoPro chapters. The short side is the analysis proxy's
    (540), so the proxy is the frame itself (a whole factor of 1).
    """
    shift = [] if offset is None else ["-output_ts_offset", offset]
    return _ffmpeg(
        path,
        "-f",
        "lavfi",
        "-i",
        f"testsrc2=size=960x540:rate=30000/1001,trim=end_frame={CLIP_FRAMES}",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=440:sample_rate=48000:duration=2",
        "-c:v",
        "libx265",
        "-x265-params",
        "log-level=error",
        "-bf",
        "0",
        "-pix_fmt",
        "yuvj420p",
        "-color_primaries",
        "bt709",
        "-color_trc",
        "bt709",
        "-colorspace",
        "bt709",
        "-color_range",
        "pc",
        "-c:a",
        "aac",
        *shift,
    )


@pytest.fixture(scope="module")
def roots(tmp_path_factory: pytest.TempPathFactory) -> OutputRoots:
    """The test working folder ``<tmp>/work/wp1.2b`` and an empty test footage folder."""
    base = tmp_path_factory.mktemp("clip")
    (base / "footage").mkdir()
    (base / "work" / clip.WORK_SUBDIR).mkdir(parents=True)
    return OutputRoots(allowed=base / "work" / clip.WORK_SUBDIR, footage=base / "footage")


@pytest.fixture(scope="module")
def config(roots: OutputRoots) -> Path:
    """A local configuration naming the test footage and working folders."""
    path = roots.allowed.parent.parent / "clearwater.local.toml"
    path.write_text(
        f"footage_path = '{roots.footage}'\nworking_path = '{roots.allowed.parent}'\n",
        encoding="utf-8",
    )
    assert load_local_config(path).working_path == roots.allowed.parent
    return path


@pytest.fixture(scope="module")
def synthetic(roots: OutputRoots) -> Path:
    """The synthetic source clip, under the test working folder like every other output."""
    folder = roots.allowed / "clips"
    folder.mkdir()
    return _synthetic(folder / "synthetic.mp4")


@pytest.fixture(scope="module")
def other(roots: OutputRoots) -> Path:
    """A second synthetic clip (another file, so another identity)."""
    return _synthetic(roots.allowed / "clips" / "other.mp4")


# --- the streaming staged analysis --------------------------------------------------------------


def _frames(count: int) -> list[Any]:
    """A drifting, flickering sequence of small frames (each its own seed)."""
    frames = []
    for index in range(count):
        frame = bench.synthetic_frame(72, 128, seed=index)
        gain = np.float32(1.0 + 0.05 * np.sin(index / 3.0) + 0.002 * index)
        frames.append(np.clip(frame * gain, 0.0, 1.0).astype(np.float32))
    return frames


@pytest.mark.parametrize("method", ["ancuti2018", "c3"])
@pytest.mark.parametrize(
    "smoother",
    [
        temporal.Smoother("median_gaussian", 0.3),  # reach 5 frames: the stream lags and drops
        temporal.Smoother("gaussian", 0.5),
        temporal.Smoother("median_gaussian", 2.0),  # reach 30 > the 24 frames: all held
    ],
    ids=lambda smoother: smoother.label.replace(" ", "-"),
)
def test_staged_stream_equals_analyse_staged_bit_for_bit(
    method: str, smoother: temporal.Smoother
) -> None:
    params = clip.make_params(method, neutral=False)
    rate = Fraction(30000, 1001)
    images = _frames(24)
    expected_smoothed, expected_measured = temporal.analyse_staged(images, params, smoother, rate)
    stream = clip.StagedStream(params, smoother, rate, select_backend("cpu"))
    for image in images:
        stream.push(image)
    smoothed, measured = stream.finish()
    assert list(smoothed) == list(expected_smoothed)
    for name, values in expected_smoothed.items():
        np.testing.assert_array_equal(smoothed[name], values, err_msg=name)
    assert list(measured) == list(expected_measured)
    for stage, series in expected_measured.items():
        for name, values in series.items():
            np.testing.assert_array_equal(measured[stage][name], values, err_msg=name)
    stages = len(temporal.STAGES[method])
    assert stream.peak_held <= min(24, (stages - 1) * stream.radius + 2)


def test_staged_stream_with_a_window_off_by_one_differs() -> None:
    """Positive control: the equality above sees a smoothing window one frame short."""
    params = Params()
    rate = Fraction(30000, 1001)
    smoother = temporal.Smoother("median_gaussian", 0.3)
    images = _frames(24)
    expected, _ = temporal.analyse_staged(images, params, smoother, rate)
    stream = clip.StagedStream(params, smoother, rate, select_backend("cpu"))
    stream._radius -= 1  # planted: the window misses one frame each side
    for image in images:
        stream.push(image)
    smoothed, _ = stream.finish()
    assert any(not np.array_equal(smoothed[name], expected[name]) for name in expected)


def test_staged_stream_refuses_too_few_frames() -> None:
    stream = clip.StagedStream(
        Params(), clip.SMOOTHER, Fraction(30000, 1001), select_backend("cpu")
    )
    stream.push(_frames(1)[0])
    with pytest.raises(ValueError, match="at least 2 frames"):
        stream.finish()


# --- raw pipe frame boundaries ------------------------------------------------------------------


def test_frame_bytes_is_the_raw_rgb_frame_size() -> None:
    assert clip.frame_bytes(3840, 2160, 8) == 3840 * 2160 * 3
    assert clip.frame_bytes(3840, 2160, 10) == 3840 * 2160 * 3 * 2
    with pytest.raises(clip.ClipError, match="bit depth 12"):
        clip.frame_bytes(16, 16, 12)


def test_read_frame_reads_exact_frames_and_refuses_a_partial_one() -> None:
    size = clip.frame_bytes(4, 2, 8)
    stream = io.BytesIO(bytes(range(size * 3)) if size * 3 < 256 else bytes(size * 3))
    buffer = np.empty((2, 4, 3), np.uint8)
    assert [clip.read_frame(stream, buffer) for _ in range(4)] == [True, True, True, False]
    with pytest.raises(clip.PartialFrameError, match="the frame boundaries are wrong"):
        clip.read_frame(io.BytesIO(bytes(size * 3 + 1)), buffer) and clip.read_frame(
            io.BytesIO(b"\x00"), buffer
        )


@pytest.mark.parametrize("delta", [1, -1])
def test_a_frame_size_off_by_one_fails_by_name(delta: int) -> None:
    """Planted off-by-one: a frame one byte too long or short never reads the pipe cleanly."""
    size = clip.frame_bytes(4, 2, 8)
    stream = io.BytesIO(bytes(size * 3))
    buffer = np.empty(size + delta, np.uint8)
    with pytest.raises(clip.PartialFrameError):
        while clip.read_frame(stream, buffer):
            pass


def test_a_planted_frame_size_error_is_refused_before_the_pipe_is_read(
    synthetic: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = clip.open_source(synthetic)
    real = clip.frame_bytes
    monkeypatch.setattr(clip, "frame_bytes", lambda w, h, d: real(w, h, d) + 1)
    with pytest.raises(clip.PipeError, match="frame size mismatch"):
        clip.frame_buffer(source)


def test_a_frame_count_other_than_the_source_is_refused(synthetic: Path, tmp_path: Path) -> None:
    source = clip.open_source(synthetic)
    short = dataclasses.replace(source, pts_ticks=source.pts_ticks[:-1])  # planted: one too few
    with pytest.raises(clip.FrameCountError, match=f"has {CLIP_FRAMES - 1}"):
        clip.decode_only(short, tmp_path / "decode.log")
    result = clip.decode_only(source, tmp_path / "decode.log")
    assert result.timing.frames == CLIP_FRAMES


# --- the source and the commands -------------------------------------------------------------


def test_open_source_reads_a_constant_rate_clip(synthetic: Path) -> None:
    source = clip.open_source(synthetic)
    assert source.frame_count == CLIP_FRAMES
    assert source.info.frame_rate == Fraction(30000, 1001)
    step = 1 / (source.info.frame_rate * source.info.time_base)
    assert source.pts_ticks == tuple(index * int(step) for index in range(CLIP_FRAMES))
    assert source.bit_depth == 8
    assert source.pipe_format == "rgb24"
    assert source.footage_seconds == Fraction(CLIP_FRAMES * 1001, 30000)


def test_open_source_refuses_an_offset_clip(roots: OutputRoots) -> None:
    shifted = _synthetic(roots.allowed / "clips" / "shifted.mp4", offset="0.5")
    with pytest.raises(clip.ClipError, match="constant-rate from 0"):
        clip.open_source(shifted)


def test_resolve_clip_refuses_a_path_inside_the_footage_folder(roots: OutputRoots) -> None:
    inside = roots.footage / "GX019999.mp4"
    inside.write_bytes(b"")
    try:
        with pytest.raises(clip.ClipError, match="name footage clips by stem"):
            clip.resolve_clip(str(inside), roots.footage)
        assert clip.resolve_clip("GX019999", roots.footage) == inside
    finally:
        inside.unlink()


def test_the_commands_write_only_the_checked_output(synthetic: Path, roots: OutputRoots) -> None:
    source = clip.open_source(synthetic)
    decode = clip.decode_command(source, "cuda", 10, seek_ticks=1001, showinfo=True)
    assert decode[-3:] == ["-f", "rawvideo", "pipe:1"]
    assert "-y" not in decode
    output = roots.allowed / "render" / "x_corrected.mp4"
    encode = clip.encode_command(source, output, 10)
    assert encode[-1] == str(output)
    assert encode.count("-y") == 1
    inputs = [encode[i + 1] for i, item in enumerate(encode) if item == "-i"]
    assert inputs == ["pipe:0", str(synthetic)]
    for flag in ("-report", "-passlogfile", "-vstats_file", "-dump_attachment"):
        assert flag not in decode and flag not in encode
    with pytest.raises(OutputPathError):
        clip.output_paths(roots, roots.footage, ["x.mp4"])
    with pytest.raises(OutputPathError):
        clip.output_paths(roots, roots.allowed.parent / "elsewhere", ["x.mp4"])


def test_neutral_conversion_round_trips_every_8_bit_value() -> None:
    values = np.arange(256, dtype=np.uint8).repeat(3).reshape(16, 16, 3)
    image = clip.to_float(values, np, 8)
    assert image.dtype == np.float32
    out = np.empty_like(values)
    clip.to_integer(image, out, np.empty(values.shape, np.float32))
    np.testing.assert_array_equal(out, values)
    neutral = correct(image, Params.neutral()).output
    clip.to_integer(neutral, out, np.empty(values.shape, np.float32))
    np.testing.assert_array_equal(out, values)


# --- the bench's real-frame source -----------------------------------------------------------


def test_bench_reads_one_frame_at_the_exact_pts(synthetic: Path, config: Path) -> None:
    source = clip.open_source(synthetic)
    every, _ = clip.decode_frames(source, 0, CLIP_FRAMES)
    real = bench.load_real_frames(str(synthetic), 1, 0.5, config)
    first = real.record["first_index"]
    expected = next(
        i
        for i, ticks in enumerate(source.pts_ticks)
        if ticks * source.info.time_base >= source.footage_seconds / 2
    )
    assert first == expected == 30
    assert real.record["pts_ticks"] == [source.pts_ticks[first]]
    (frame,) = real.frames
    np.testing.assert_array_equal(frame, every[first])
    assert not np.array_equal(frame, every[first - 1])
    assert not np.array_equal(frame, every[first + 1])


def test_decode_frames_refuses_frames_past_the_end(synthetic: Path) -> None:
    source = clip.open_source(synthetic)
    with pytest.raises(clip.ClipError, match="outside"):
        clip.decode_frames(source, CLIP_FRAMES - 1, 2)


def test_bench_core_mode_on_real_frames_records_the_input_and_proxies(
    synthetic: Path, config: Path, tmp_path: Path
) -> None:
    argv = ["--device", "cpu", "--method", "ancuti2018", "--input", str(synthetic)]
    argv += ["--frames", "3", "--proxy", "270", "--proxy", "135", "--config", str(config)]
    assert bench.main([*argv, "--out", str(tmp_path)]) == 0
    (path,) = tmp_path.glob("bench-cpu-synthetic-ancuti2018-*.json")
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["label"] == "REAL"
    assert record["shape"] == [540, 960, 3]
    assert record["input"]["first_index"] == 18
    assert len(record["input"]["pts_ticks"]) == 3
    assert len(record["timing"]["per_frame_s"]) == 3
    full, half, quarter = record["proxy"]
    assert [full["short_side"], half["short_side"], quarter["short_side"]] == [540, 270, 135]
    assert quarter["shape"] == [135, 240, 3]
    assert full["relative_error"]["normalisation_bounds.low"] == {"mean": 0.0, "max": 0.0}
    assert set(half["relative_step"]) == set(full["statistics"])
    assert record["ambient"]["head"]["head"]
    assert isinstance(record["ambient"]["stray_processes_before"], list)


def test_bench_refuses_a_proxy_that_is_not_a_whole_factor(
    synthetic: Path, config: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    argv = ["--device", "cpu", "--method", "c3", "--input", str(synthetic), "--frames", "1"]
    argv += ["--proxy", "100", "--config", str(config), "--out", str(tmp_path)]
    assert bench.main(argv) == 2
    assert "whole-factor" in capsys.readouterr().err


# --- the export loop -------------------------------------------------------------------------


@pytest.fixture(scope="module")
def neutral_analysis(synthetic: Path, roots: OutputRoots) -> Path:
    """The neutral analysis record of the synthetic clip (on the GPU when one is usable)."""
    source = clip.open_source(synthetic)
    params = clip.make_params("ancuti2018", neutral=True)
    return clip.run_analyse(source, params, GPU, roots, None, "none", None)


def test_the_analysis_record_holds_one_entry_per_frame(neutral_analysis: Path) -> None:
    record = json.loads(neutral_analysis.read_text(encoding="utf-8"))
    assert record["frames_analysed"] == CLIP_FRAMES
    assert len(record["pts_ticks"]) == CLIP_FRAMES
    assert len(record["frame_means"]) == CLIP_FRAMES
    assert all(len(values) == CLIP_FRAMES for values in record["smoothed"].values())
    assert record["smoother"]["kind"] == "median_gaussian"
    assert record["smoother"]["window_s"] == 2.0
    assert "PROVISIONAL" in record["smoother"]["note"]
    assert len(clip.per_frame_statistics(record)) == CLIP_FRAMES


@pytest.mark.gpu
@requires_gpu
def test_neutral_export_is_an_identity_with_the_container_the_same(
    synthetic: Path, roots: OutputRoots, neutral_analysis: Path
) -> None:
    source = clip.open_source(synthetic)
    params = clip.make_params("ancuti2018", neutral=True)
    run_path = clip.run_render(
        source, params, GPU, roots, neutral_analysis, None, "none", False, None, True
    )
    run = json.loads(run_path.read_text(encoding="utf-8"))
    assert run["frames_written"] == CLIP_FRAMES
    assert run["witness_frames_checked"] == 3  # frames 0, 30 and 59
    summary = run["compare"]
    assert summary["mandatory_and_required_all_same"], summary["different_items"]
    output = Path(run["output"])
    probe = compare.run_ffprobe(["-show_streams", "-select_streams", "v:0", str(output)])
    assert probe["streams"][0]["codec_name"] == "hevc"
    psnr = spike.identity_psnr(synthetic, output)
    assert float(psnr["y"]) >= PSNR_FLOOR_DB, psnr
    timing = run["timing"]
    assert timing["frames"] == CLIP_FRAMES
    assert timing["bracket_s"] >= timing["main_loop_sum_s"] > 0


@pytest.mark.gpu
@requires_gpu
def test_the_export_feeds_the_encoder_the_decoded_bytes_under_neutral_parameters(
    synthetic: Path, roots: OutputRoots, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = clip.open_source(synthetic)
    decoded, _ = clip.decode_frames(source, 0, CLIP_FRAMES)
    written: list[bytes] = []
    original = clip._Writer.run

    def spy(self: Any) -> None:
        stream = self._stream

        class Tee:
            def write(self, data: memoryview) -> int:
                written.append(bytes(data))
                return int(stream.write(data))

            def close(self) -> None:
                stream.close()

        self._stream = Tee()
        original(self)

    monkeypatch.setattr(clip._Writer, "run", spy)
    folder = roots.allowed / "identity"
    output, *logs = clip.output_paths(roots, folder, ["s_corrected.mp4", "d.log", "e.log"])
    clip.export(source, output, Params.neutral(), None, GPU, (logs[0], logs[1]))
    assert len(written) == CLIP_FRAMES
    for index, frame in enumerate(decoded):
        assert written[index] == frame.tobytes(), f"frame {index}"


@pytest.mark.gpu
@requires_gpu
def test_a_shifted_witness_stops_the_render(
    synthetic: Path, roots: OutputRoots, neutral_analysis: Path
) -> None:
    """Planted misalignment: the record's frame means moved by one frame are caught by name."""
    record = json.loads(neutral_analysis.read_text(encoding="utf-8"))
    means = record["frame_means"]
    shifted = [means[1], *means[1:]]
    source = clip.open_source(synthetic)
    folder = roots.allowed / "witness"
    output, *logs = clip.output_paths(roots, folder, ["s_corrected.mp4", "d.log", "e.log"])
    statistics = clip.per_frame_statistics(record)
    with pytest.raises(clip.StatisticsMismatchError, match="frame 0: channel means"):
        clip.export(source, output, Params.neutral(), statistics, GPU, (logs[0], logs[1]), shifted)


def test_a_record_of_another_clip_or_other_settings_is_refused(
    synthetic: Path, other: Path, neutral_analysis: Path
) -> None:
    record = json.loads(neutral_analysis.read_text(encoding="utf-8"))
    neutral = clip.make_params("ancuti2018", neutral=True)
    source = clip.open_source(synthetic)
    clip.check_statistics_record(record, source, neutral, "none", None)
    with pytest.raises(clip.StatisticsMismatchError, match="another file"):
        clip.check_statistics_record(record, clip.open_source(other), neutral, "none", None)
    with pytest.raises(clip.StatisticsMismatchError, match="other parameters"):
        clip.check_statistics_record(record, source, Params(), "none", None)
    with pytest.raises(clip.StatisticsMismatchError, match="hwaccel"):
        clip.check_statistics_record(record, source, neutral, "cuda", None)
    with pytest.raises(clip.StatisticsMismatchError, match="analysed 60 frames"):
        clip.check_statistics_record(record, source, neutral, "none", 30)
    tampered = dict(record, pts_ticks=[0, *record["pts_ticks"][:-1]])
    with pytest.raises(clip.StatisticsMismatchError, match="pts list"):
        clip.check_statistics_record(tampered, source, neutral, "none", None)


@pytest.mark.gpu
@requires_gpu
def test_bench_whole_clip_modes_record_their_pass(
    synthetic: Path, config: Path, roots: OutputRoots
) -> None:
    common = ["--device", "gpu", "--method", "ancuti2018", "--input", str(synthetic)]
    common += ["--config", str(config)]
    records = {}
    for mode in ("analysis", "decode-only", "passthrough"):
        assert bench.main(["--mode", mode, *common]) == 0
        (path,) = (roots.allowed / "bench").glob(f"synthetic-{mode}-*/bench-*.json")
        records[mode] = json.loads(path.read_text(encoding="utf-8"))
    analysis = Path(records["analysis"]["analysis_record"])
    assert bench.main(["--mode", "end-to-end", *common, "--statistics", str(analysis)]) == 0
    (path,) = (roots.allowed / "bench").glob("synthetic-end-to-end-*/bench-*.json")
    records["end-to-end"] = json.loads(path.read_text(encoding="utf-8"))
    for mode, record in records.items():
        assert record["frames"] == CLIP_FRAMES, mode
        assert record["timing"]["bracket_s"] > 0, mode
        assert record["n6"]["budget_seconds_per_frame"] == pytest.approx(3.3 * 1001 / 30000)
        assert record["memory"]["gpu_pool_reserved_mb"] >= 0, mode
        assert record["ambient"]["head"]["head"], mode
    for mode in ("passthrough", "end-to-end"):
        assert records[mode]["compare"]["mandatory_and_required_all_same"], mode
    assert records["end-to-end"]["run"]["witness_frames_checked"] == 3


# --- the owner's footage ---------------------------------------------------------------------


@pytest.mark.footage
@pytest.mark.gpu
@requires_gpu
def test_footage_smoke_gx011628(tmp_path: Path) -> None:
    """The first 30 frames of chapter GX011628 analysed and exported at the defaults."""
    footage = load_local_config().footage_path
    source = clip.open_source(find_footage_file("GX011628", footage))
    assert source.frame_count == 434
    roots = OutputRoots(allowed=tmp_path / "work" / clip.WORK_SUBDIR, footage=footage)
    params = Params()
    analysis = clip.run_analyse(source, params, GPU, roots, None, "none", 30)
    run_path = clip.run_render(source, params, GPU, roots, analysis, None, "none", False, 30, False)
    run = json.loads(run_path.read_text(encoding="utf-8"))
    assert run["frames_written"] == 30
    output = Path(run["output"])
    facts = compare.gather(output)
    base = source.info.time_base
    assert facts.pts == [ticks * base for ticks in source.pts_ticks[:30]]
    items = compare.compare_facts(compare.gather(source.path), facts)
    required = [item for item in items if item.item_class == compare.REQUIRED]
    assert required and all(item.status == compare.SAME for item in required), [
        item.name for item in required if item.status != compare.SAME
    ]
