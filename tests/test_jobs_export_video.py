"""Video export end to end (WP3.14 ladder items 4 and 9): the product decoder, method and sink.

V4 runs every decodable WP2.3 video sample through :class:`~clearwater.jobs.ExportEngine` and
``tools/video_fidelity.py`` (DR-57 (a): the instrument hashes the audio payloads); the refused
samples fail readably with nothing written. DR-28 (1) (question 16): every frame written is the
render of its own decoded frame under its own pts's statistics (a full-coverage digest before
encode, against an independent decode, analysis and render), and a sampled decode of the output
puts each frame nearest its own corrected frame; planted wrong engines fail both by name. V11:
an encoder killed mid-stream, a cancel mid-encode and a killed export process leave no partial
output. libx265 always runs; NVENC runs under ``gpu``. Synthetic clips are built under the
session's temporary folder; the committed samples and the footage are read only.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import time
from collections.abc import Callable, Iterator
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pytest

import video_fidelity as vf
from clearwater.analysis import AnalysisEngine
from clearwater.cache import DiskProxyCache, cache_key
from clearwater.core import backend_for
from clearwater.interfaces import Frame, JobResult, ProbeResult, Settings
from clearwater.interfaces.stubs import StubProgress
from clearwater.io.video import FFmpegVideoSink, FFmpegVideoSource, detect_capabilities, probe
from clearwater.jobs import ExportEngine, effective_parameters, remove_leftovers
from clearwater.jobs import export as export_module
from clearwater.jobs.export_seam import CANCELLED, ExportRequest
from clearwater.jobs.safe_write import is_temporary_name
from clearwater.methods import available_methods
from container_spike import compare
from local_config import FootageLookupError, find_footage_file, load_local_config
from test_jobs_export_support import FakeSink, parameter_set, product_engine

pytestmark = pytest.mark.usefixtures("ffmpeg_tools")

Sample = Callable[[str], Path]

CPU = backend_for("cpu")
TESTS = Path(__file__).resolve().parent

DECODABLE = {
    "vid-hevc8-bt709-full": 8,
    "vid-hevc10": 10,
    "vid-untagged": 8,
    "vid-vfr": 8,
    "vid-rotated": 8,
    "vid-truncated": 8,
}
"""The decodable WP2.3 video samples and their bit depths (the output keeps the source's)."""

REFUSED = (
    "vid-hlg",
    "vid-pq",
    "gopro-lower-gl010001-lrv",
    "gopro-upper-gl010001-lrv",
    "gopro-lower-gx010001-thm",
    "gopro-upper-gx010001-thm",
)
"""Samples the engine refuses: HDR transfers (the probe's refuse faults) and sidecars (D83)."""


def _nvenc_ready() -> bool:
    return any(c.name == "hevc_nvenc" and c.available for c in detect_capabilities())


def _need(encoder: str) -> None:
    if encoder == "hevc_nvenc" and not _nvenc_ready():
        pytest.skip("NVENC is not available on this machine")


def _settings(folder: Path, encoder: str = "libx265", **values: Any) -> Settings:
    """Settings for an export into ``folder``; the CPU is forced for libx265 unless overridden."""
    values.setdefault("force_cpu", encoder == "libx265")
    return Settings(output_folder=folder, video_encoder=encoder, **values)  # type: ignore[arg-type]


def _export(
    engine: ExportEngine,
    source: Path,
    settings: Settings,
    progress: Any = None,
) -> JobResult:
    request = ExportRequest(source, "video", parameter_set("c3"), settings)
    return engine.job(request)(progress or StubProgress())


def _state(path: Path) -> tuple[bytes, int]:
    return path.read_bytes(), os.stat(path).st_mtime_ns


def _items(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["name"]: item for item in record["items"]}


def _assert_v4(record: dict[str, Any]) -> None:
    summary = record["summary"]
    wrong = summary["different_items"]
    assert summary["mandatory_and_required_all_same"], (wrong["MANDATORY"], wrong[compare.REQUIRED])
    assert _items(record)[vf._ROSTER_ITEM]["status"] == "SAME"


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
        size: str = "160x96",
        rate: str = "30",
        duration: str = "4",
        hue_rate: int = 60,
    ) -> Path:
        """Return an HEVC clip with sound whose colour cast turns ``hue_rate`` degrees a second."""
        path = self.folder / f"{name}.mp4"
        if path.exists():
            return path
        _ffmpeg(
            "-f", "lavfi", "-i", f"testsrc2=size={size}:rate={rate}:duration={duration}",
            "-f", "lavfi", "-i", f"sine=frequency=440:sample_rate=48000:duration={duration}",
            "-vf", f"hue=h=t*{hue_rate}", "-bf", "0",
            "-c:v", "libx265", "-x265-params", "log-level=error", "-pix_fmt", "yuv420p",
            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
            "-color_range", "tv", "-c:a", "aac", str(path),
        )  # fmt: skip
        return path


@pytest.fixture(scope="session")
def clips(tmp_path_factory: pytest.TempPathFactory) -> Clips:
    return Clips(tmp_path_factory.mktemp("wp314-clips"))


# --- V4 on every decodable sample, through the engine ----------------------------------------


def _cases() -> list[Any]:
    cases = []
    for sample_id in DECODABLE:
        for encoder in ("libx265", "hevc_nvenc"):
            marks = [pytest.mark.gpu] if encoder == "hevc_nvenc" else []
            cases.append(pytest.param(sample_id, encoder, marks=marks, id=f"{sample_id}-{encoder}"))
    return cases


@pytest.mark.parametrize(("sample_id", "encoder"), _cases())
def test_v4_every_decodable_sample_through_the_engine(
    sample: Sample, tmp_path: Path, sample_id: str, encoder: str
) -> None:
    _need(encoder)
    source = sample(sample_id)
    before = _state(source)
    out = tmp_path / "out"
    out.mkdir()
    engine = product_engine(tmp_path / "cache")
    result = _export(engine, source, _settings(out, encoder))

    assert result.ok, result.failure
    (output,) = result.outputs
    assert sorted(p.name for p in out.iterdir()) == [output.name]
    record = vf.fidelity_record(source, output, bit_depth=DECODABLE[sample_id])
    _assert_v4(record)
    if sample_id != "vid-truncated":
        assert _items(record)["video frame count"]["output"] == probe(source).video.nb_frames
    else:
        assert any("cut short" in w for w in result.warnings)  # D86
    if encoder == "libx265":
        assert result.device == "CPU: forced"
    assert _state(source) == before  # N8


@pytest.mark.parametrize("sample_id", REFUSED)
def test_refused_samples_fail_readably_with_nothing_written(
    sample: Sample, tmp_path: Path, sample_id: str
) -> None:
    source = sample(sample_id)
    before = _state(source)
    out = tmp_path / "out"
    out.mkdir()
    result = _export(product_engine(tmp_path / "cache"), source, _settings(out))
    assert not result.ok and result.failure is not CANCELLED
    assert result.failure is not None and result.failure.startswith(source.name)
    assert result.failure.isascii()
    assert result.outputs == ()
    assert list(out.iterdir()) == []
    assert not (tmp_path / "cache").exists() or list((tmp_path / "cache").iterdir()) == []
    assert _state(source) == before


@pytest.mark.slow
def test_v4_synthetic_5k3_8_7_clip(clips: Clips, tmp_path: Path) -> None:
    source = clips.make("gopro-5k3-8x7", size="5312x4648", rate="30000/1001", duration="0.3")
    out = tmp_path / "out"
    out.mkdir()
    result = _export(product_engine(tmp_path / "cache"), source, _settings(out))
    assert result.ok, result.failure
    (output,) = result.outputs
    _assert_v4(vf.fidelity_record(source, output, bit_depth=8))


# --- DR-28 (1): every frame rendered with its own statistics ----------------------------------


def _digest(pixels: Any) -> str:
    return hashlib.sha256(np.ascontiguousarray(pixels, dtype=np.float32).tobytes()).hexdigest()


def _reference(source: Path, cache_folder: Path) -> list[tuple[int, np.ndarray]]:
    """Decode, analyse and render the clip independently of the engine: ``(pts, corrected)``."""
    info = probe(source)
    method = available_methods()["c3"]
    params = effective_parameters(method, parameter_set("c3"))
    engine = AnalysisEngine(
        method=method,
        backend=CPU,
        cache=DiskProxyCache(cache_folder),
        key=cache_key(source),
        source=FFmpegVideoSource(),
        probe=info,
        params=params,
        hw_decode=False,
    )
    assert engine.analysis_job()(StubProgress()).ok
    corrected = []
    frames = FFmpegVideoSource().frames(info, hw_decode=False)
    try:
        for frame in frames:
            statistics = engine.smoothed_record(frame.pts_ticks, schema_hash=engine.schema_hash)
            image = replace(frame, pixels=CPU.asarray(frame.pixels, np.float32), device=CPU.device)
            rendered = method.render(image, params, statistics)
            host = np.asarray(CPU.to_host(rendered.pixels), np.float32)
            corrected.append((frame.pts_ticks, host))
    finally:
        frames.close()
    return corrected


def check_coverage(written: list[tuple[int, str]], reference: list[tuple[int, str]]) -> None:
    """Fail unless the written frames are exactly the reference's, pts by pts (DR-28 (1)).

    Args:
        written: ``(pts, digest)`` of every frame the engine handed to the sink, in order.
        reference: ``(pts, digest)`` of every independently corrected frame, in order.

    Raises:
        AssertionError: Naming the first kind of difference found.
    """
    pts = [p for p, _ in written]
    duplicated = sorted({p for p in pts if pts.count(p) > 1})
    if duplicated:
        raise AssertionError(f"DR-28 (1): a frame was written twice at pts {duplicated}")
    missing = sorted({p for p, _ in reference} - set(pts))
    if missing:
        raise AssertionError(f"DR-28 (1): no frame was written at pts {missing}")
    if pts != [p for p, _ in reference]:
        raise AssertionError("DR-28 (1): the frames were written out of pts order")
    other = [p for (p, got), (_, want) in zip(written, reference, strict=True) if got != want]
    if other:
        raise AssertionError(
            f"DR-28 (1): {len(other)} frames differ from their own render, first at pts {other[0]}"
        )


def check_sampled_order(output: Path, corrected: list[np.ndarray], every: int = 5) -> None:
    """Fail unless each sampled output frame is nearest its own corrected frame (Q16).

    Args:
        output: The exported file.
        corrected: The independently corrected frames, in order.
        every: The sampling step (the last frame is always sampled).

    Raises:
        AssertionError: A sampled frame is nearer a neighbour's corrected frame.
    """
    frames = FFmpegVideoSource().frames(probe(output), hw_decode=False)
    try:
        decoded = [np.asarray(f.pixels, np.float32) for f in frames]
    finally:
        frames.close()
    if len(decoded) != len(corrected):
        raise AssertionError(f"the output has {len(decoded)} frames, not {len(corrected)}")
    count = len(corrected)
    for i in sorted({*range(0, count, every), count - 1}):
        errors = {
            j: float(np.mean((decoded[i] - corrected[j]) ** 2))
            for j in (i - 1, i, i + 1)
            if 0 <= j < count
        }
        nearest = min(errors, key=errors.__getitem__)
        if nearest != i:
            raise AssertionError(
                f"output frame {i} is nearer corrected frame {nearest} than its own ({errors})"
            )


class _DigestSink(FFmpegVideoSink):
    """The product sink, recording ``(pts, digest)`` of every frame before it is encoded."""

    def __init__(self) -> None:
        super().__init__()
        self.written: list[tuple[int, str]] = []

    def write(self, frame: Frame) -> None:
        self.written.append((frame.pts_ticks, _digest(frame.pixels)))
        super().write(frame)


class _PlantedSource:
    """The product source; once armed (at the export phase) its frames are planted."""

    def __init__(self, plant: Callable[[list[Frame]], list[Frame]]) -> None:
        self._source = FFmpegVideoSource()
        self._plant = plant
        self.armed = False

    def probe(self, path: Path) -> ProbeResult:
        return self._source.probe(path)

    def frames(self, probe: ProbeResult, **options: Any) -> Iterator[Frame]:
        stream = self._source.frames(probe, **options)
        if not self.armed:
            return stream
        try:
            frames = list(stream)
        finally:
            stream.close()
        return iter(self._plant(frames))

    def arm(self, stage: str) -> None:
        if stage == "frames":
            self.armed = True


def _planted_engine(
    cache: Path, *, plant: Callable[[list[Frame]], list[Frame]], sink: Callable[[], Any]
) -> ExportEngine:
    source = _PlantedSource(plant)
    return ExportEngine(
        methods=available_methods(),
        video_source=source,
        sink_factory=sink,
        photo_reader=None,  # type: ignore[arg-type]
        photo_writer=None,  # type: ignore[arg-type]
        cache=DiskProxyCache(cache),
        cache_key=cache_key,
        select_backend=lambda settings, h, w, m: (CPU, "CPU: forced"),
        on_stage=source.arm,
    )


def _fake_digests(sink: FakeSink) -> list[tuple[int, str]]:
    return [(f.pts_ticks, _digest(f.pixels)) for f in sink.frames]


def test_dr28_every_frame_is_rendered_with_its_own_statistics(clips: Clips, tmp_path: Path) -> None:
    source = clips.make("dr28")
    sinks: list[_DigestSink] = []

    def sink() -> _DigestSink:
        sinks.append(_DigestSink())
        return sinks[-1]

    out = tmp_path / "out"
    out.mkdir()
    engine = product_engine(tmp_path / "cache", sink_factory=sink)
    result = _export(engine, source, _settings(out, quality_level="high"))
    assert result.ok, result.failure
    reference = _reference(source, tmp_path / "reference-cache")
    assert len(reference) == probe(source).video.nb_frames == 120
    check_coverage(sinks[0].written, [(p, _digest(c)) for p, c in reference])
    check_sampled_order(result.outputs[0], [c for _, c in reference])


@pytest.fixture(scope="module")
def dr28_reference(
    clips: Clips, tmp_path_factory: pytest.TempPathFactory
) -> tuple[Path, list[tuple[int, np.ndarray]]]:
    source = clips.make("dr28")
    return source, _reference(source, tmp_path_factory.mktemp("dr28-reference-cache"))


def _shifted_engine(shift: int, pts: list[int]) -> type[AnalysisEngine]:
    class Shifted(AnalysisEngine):
        """A planted engine pairing each frame with its neighbour's statistics."""

        def smoothed_record(self, pts_ticks: int, *, schema_hash: str | None = None) -> Any:
            at = min(max(pts.index(pts_ticks) + shift, 0), len(pts) - 1)
            return super().smoothed_record(pts[at], schema_hash=schema_hash)

    return Shifted


@pytest.mark.parametrize(
    ("plant", "words"),
    [
        ("statistics-pts+1", "differ from their own render"),
        ("statistics-pts-1", "differ from their own render"),
        ("dropped-frame", "no frame was written at pts"),
        ("duplicated-frame", "a frame was written twice"),
    ],
)
def test_dr28_planted_wrong_engines_fail_the_coverage_check(
    dr28_reference: tuple[Path, list[tuple[int, np.ndarray]]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    plant: str,
    words: str,
) -> None:
    source, reference = dr28_reference
    pts = [p for p, _ in reference]
    frame_plant: Callable[[list[Frame]], list[Frame]] = lambda frames: frames  # noqa: E731
    if plant.startswith("statistics"):
        shift = 1 if plant.endswith("+1") else -1
        monkeypatch.setattr(export_module, "AnalysisEngine", _shifted_engine(shift, pts))
    elif plant == "dropped-frame":
        frame_plant = lambda frames: frames[:40] + frames[41:]  # noqa: E731
    else:
        frame_plant = lambda frames: frames[:41] + frames[40:]  # noqa: E731
    sinks: list[FakeSink] = []

    def sink() -> FakeSink:
        sinks.append(FakeSink())
        return sinks[-1]

    engine = _planted_engine(tmp_path / "cache", plant=frame_plant, sink=sink)
    _export(engine, source, _settings(tmp_path))
    with pytest.raises(AssertionError, match=words):
        check_coverage(_fake_digests(sinks[0]), [(p, _digest(c)) for p, c in reference])


def test_dr28_a_planted_frame_swap_fails_the_sampled_order_check(
    dr28_reference: tuple[Path, list[tuple[int, np.ndarray]]], tmp_path: Path
) -> None:
    source, reference = dr28_reference

    def swap(frames: list[Frame]) -> list[Frame]:
        frames = list(frames)
        a, b = frames[40], frames[41]
        frames[40], frames[41] = replace(a, pixels=b.pixels), replace(b, pixels=a.pixels)
        return frames

    engine = _planted_engine(tmp_path / "cache", plant=swap, sink=FFmpegVideoSink)
    out = tmp_path / "out"
    out.mkdir()
    result = _export(engine, source, _settings(out, quality_level="high"))
    assert result.ok, result.failure
    with pytest.raises(AssertionError, match="output frame 40 is nearer corrected frame 41"):
        check_sampled_order(result.outputs[0], [c for _, c in reference])


# --- V11 and cancel with the product sink ---------------------------------------------------


class _KillingSink(FFmpegVideoSink):
    """The product sink whose encoder process is killed after the fifth frame."""

    def __init__(self) -> None:
        super().__init__()
        self.count = 0

    def write(self, frame: Frame) -> None:
        super().write(frame)
        self.count += 1
        if self.count == 5:
            process = self._process
            assert process is not None
            process.kill()
            process.wait()


def test_v11_an_encoder_killed_mid_stream_leaves_no_partial_output(
    clips: Clips, tmp_path: Path
) -> None:
    source = clips.make("dr28")
    before = _state(source)
    out = tmp_path / "out"
    out.mkdir()
    earlier = out / "earlier-output.mp4"
    earlier.write_bytes(b"an earlier output")
    engine = product_engine(tmp_path / "cache", sink_factory=_KillingSink)
    result = _export(engine, source, _settings(out))
    assert not result.ok and result.failure is not CANCELLED
    assert result.failure is not None and result.failure.startswith(source.name)
    assert result.outputs == ()
    assert sorted(p.name for p in out.iterdir()) == ["earlier-output.mp4"]
    assert earlier.read_bytes() == b"an earlier output"
    assert _state(source) == before


class _CancelAt:
    """A progress whose cancel flag rises once ``frames`` frames have been exported."""

    def __init__(self, frames: int) -> None:
        self._frames = frames
        self._cancelled = False

    def report(self, done: int, total: int | None, message: str) -> None:
        if message.startswith("Exporting") and done >= self._frames:
            self._cancelled = True

    def cancelled(self) -> bool:
        return self._cancelled


def test_a_cancel_mid_encode_leaves_nothing_and_keeps_earlier_outputs(
    clips: Clips, tmp_path: Path
) -> None:
    source = clips.make("dr28")
    out = tmp_path / "out"
    out.mkdir()
    earlier = out / "earlier-output.mp4"
    earlier.write_bytes(b"an earlier output")
    result = _export(
        product_engine(tmp_path / "cache"), source, _settings(out), progress=_CancelAt(10)
    )
    assert result.failure is CANCELLED and result.outputs == ()
    assert sorted(p.name for p in out.iterdir()) == ["earlier-output.mp4"]
    assert earlier.read_bytes() == b"an earlier output"


_CHILD = """
import sys
from pathlib import Path

from clearwater.interfaces import Settings
from clearwater.jobs.export_seam import CANCELLED, ExportRequest
from test_jobs_export_support import parameter_set, product_engine


class Progress:
    def report(self, done, total, message):
        if message.startswith("Exporting"):
            print(f"WROTE {done}", flush=True)

    def cancelled(self):
        return False


source, out, cache = (Path(a) for a in sys.argv[1:4])
settings = Settings(output_folder=out, video_encoder="libx265", force_cpu=True)
request = ExportRequest(source, "video", parameter_set("c3"), settings)
result = product_engine(cache).job(request)(Progress())
print(f"DONE {result.ok}", flush=True)
"""


@pytest.mark.slow
def test_v11_a_killed_export_process_leaves_only_a_temporary_that_is_cleaned_up(
    clips: Clips, tmp_path: Path
) -> None:
    source = clips.make("v11-kill", size="640x360", duration="8")
    before = _state(source)
    out = tmp_path / "out"
    out.mkdir()
    earlier = out / "earlier-output.mp4"
    earlier.write_bytes(b"an earlier output")
    script = tmp_path / "child.py"
    script.write_text(_CHILD, encoding="utf-8")
    env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(TESTS), str(TESTS.parent / "tools")])}
    child = subprocess.Popen(
        [sys.executable, str(script), str(source), str(out), str(tmp_path / "cache")],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        env=env,
    )
    try:
        assert child.stdout is not None
        for line in child.stdout:
            assert not line.startswith("DONE"), "the export finished before it was killed"
            if line.strip() == "WROTE 10":
                break
        else:
            pytest.fail("the export process ended before writing ten frames")
    finally:
        child.kill()
        child.wait()

    left = sorted(p.name for p in out.iterdir() if p != earlier)
    assert left and all(is_temporary_name(name) for name in left), left
    deadline = time.monotonic() + 30
    while True:  # the orphaned encoder holds the temporary until it sees the end of its input
        report = remove_leftovers([out])
        if not [p for p in out.iterdir() if p != earlier] or time.monotonic() > deadline:
            break
        time.sleep(0.5)
    assert not report.failed or not [p for p in out.iterdir() if p != earlier]
    assert sorted(p.name for p in out.iterdir()) == ["earlier-output.mp4"]
    assert earlier.read_bytes() == b"an earlier output"
    assert _state(source) == before


# --- the real clip (footage window) ------------------------------------------------------------


def _footage_clip(stem: str, root: Path) -> Path:
    """Return a footage clip; skip only when the folder was searched and the clip is not there."""
    try:
        return find_footage_file(stem, root)
    except FootageLookupError as error:
        if error.matches or error.__cause__ is not None or not root.is_dir():
            raise
        pytest.skip(f"{stem} is not in the footage folder")


@pytest.mark.footage
@pytest.mark.gpu
@pytest.mark.slow
def test_gx011627_through_the_engine_keeps_every_mandatory_and_required_item(
    tmp_path: Path,
) -> None:
    if not _nvenc_ready():
        pytest.skip("NVENC is not available on this machine")
    source = _footage_clip("GX011627", load_local_config().footage_path)
    out = tmp_path / "out"
    out.mkdir()
    settings = _settings(out, "hevc_nvenc", quality_level="standard", provenance=True)
    result = _export(product_engine(tmp_path / "cache"), source, settings)
    assert result.ok, result.failure
    (output,) = result.outputs
    try:
        _assert_v4(vf.fidelity_record(source, output, bit_depth=8))
    finally:
        os.remove(output)
