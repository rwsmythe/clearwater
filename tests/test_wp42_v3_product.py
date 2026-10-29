"""WP4.2 task 7: V3 with the product methods, through the composed engine (question 5).

Measured pre-encode, on the frames the sink receives from an export through the composition root
(the product's decode, analysis, smoothing and render), against the per-frame (unsmoothed) leg:
the same decoded frames rendered by the same method on the same backend with each frame's own
statistics (``AnalysisEngine.provisional_record`` of a second analysis over the same source and
probe; round-0 ruling R0-Q5 (a)). The clips are encoded in-test under the session's temporary
folder as LOSSLESS 8-bit 4:2:0 HEVC MP4 with BT.709 tags, so the encoder adds no flicker to a
static region; ruling R0-Q5's condition is the first test: the lossless clips decode through
``FFmpegVideoSource`` inside WP3.9's envelope with every frame. On ``ad14-flicker`` (with
``ad14-mask``) AD-14's bound (under 0.5/255 after smoothing) is ASSERTED and V3's four ratios are
RECORDED (CHARC ruling V3-1); on WP3.11's jittering-patch clip V3's 25 % is ASSERTED. c3 and
ancuti2018 at their defaults, on the GPU job with device frames (the product's job on this
machine; ``gpu``), or all on the CPU job when ``CLEARWATER_WP42_V3_BACKEND=cpu`` (the recorded CPU
run); ``CLEARWATER_WP42_V3_FIGURES`` names a new figures file that the run creates exclusively,
after the runner's footage check, and writes through one held handle, its backend on the first
line. The encoded output's figures are recorded beside, as characterisation. Each
acceptance check reads the unrounded figure and has a planted control through the same
measurement: a 1/255 flicker on every other smoothed frame for AD-14's bound, and the smoothed
and per-frame frames interleaved for V3's ratio; both must be refused. A product-method miss is
a STOP (D96 and the threshold are the owner's).
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from typing import Any, BinaryIO

import numpy as np
import pytest
from numpy.typing import NDArray
from PIL import Image as PILImage

import headless_export
from clearwater.analysis import AnalysisEngine
from clearwater.app import composition
from clearwater.cache import DiskProxyCache
from clearwater.config import new_parameter_set
from clearwater.core import backend_for
from clearwater.interfaces import ArrayBackend, Frame, Settings
from clearwater.interfaces.stubs import StubProgress
from clearwater.io.video import FFmpegVideoSource, probe
from clearwater.jobs import effective_parameters
from clearwater.jobs.export_seam import ExportRequest
from test_analysis_v3 import MEASURES, jitter_clip, lab

pytestmark = [pytest.mark.usefixtures("ffmpeg_tools"), pytest.mark.gpu, pytest.mark.slow]

Sample = Callable[[str], Path]
METHODS = ("c3", "ancuti2018")
JITTER_REGION_ROWS = 270 // 2
"""The jittering-patch clip's measured region: its upper half (WP3.11's ``REGION_ROWS``)."""
BACKEND_VARIABLE = "CLEARWATER_WP42_V3_BACKEND"
"""Set to ``cpu`` to run every leg on the CPU job (the recorded CPU run, CHARC
``2a336830303f3a2d``); unset, the legs run on the GPU job with device frames (the suite's form)."""
FIGURES_VARIABLE = "CLEARWATER_WP42_V3_FIGURES"
"""When set, the path of a NEW figures file: a ``backend:`` line, then each test's figures line."""


def create_figures_file(path: Path, footage_folder: Path | None, backend: str) -> BinaryIO:
    """Create the run's figures file exclusively and return its one open handle.

    The path passes the runner's footage check (``headless_export.write_target_refusal``)
    before anything is created; the switch is refused when no footage folder is configured (it
    exists only for recorded runs on the owner's laptop). The file is then opened with ``"xb"``,
    so an existing file is refused and left as it was, and the ``backend:`` line is written.

    Args:
        path: The figures file to create.
        footage_folder: The configured footage folder, or None when there is none.
        backend: The legs' backend device, written on the first line.

    Returns:
        The open handle; every later figures line is written through it.

    Raises:
        pytest.fail.Exception: The switch is refused (no footage folder, the footage check, or
            an existing file); nothing is created then.
        OSError: The ``backend:`` line cannot be written; the handle is closed first.
    """
    if footage_folder is None:
        pytest.fail(f"{FIGURES_VARIABLE} is refused: no footage folder is configured")
    reason = headless_export.write_target_refusal(path, footage_folder)
    if reason is not None:
        pytest.fail(f"{FIGURES_VARIABLE} is refused: {path.name} {reason}")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        handle = path.open("xb")
    except FileExistsError:
        pytest.fail(f"{FIGURES_VARIABLE} names an existing file; each run writes a new one")
    try:
        handle.write(f"backend: {backend}\n".encode("ascii"))
        handle.flush()
    except BaseException:
        handle.close()
        raise
    return handle


@pytest.fixture(scope="module")
def figures_file() -> Iterator[BinaryIO | None]:
    """The run's figures file, held open for the module; None when not asked for.

    Created by :func:`create_figures_file` (footage check, then exclusive creation); every
    figures line goes through this one handle, which is closed at teardown.
    """
    named = os.environ.get(FIGURES_VARIABLE)
    if not named:
        yield None
        return
    try:
        footage = headless_export.configured_footage_folder()
    except headless_export.RunnerRefusalError as exc:
        pytest.fail(f"{FIGURES_VARIABLE} is refused: {exc}")
    with create_figures_file(Path(named), footage, _backend().device) as handle:
        yield handle


def _keep(figures_file: BinaryIO | None, line: str) -> None:
    """Write one figures line through the run's figures handle, when there is one."""
    if figures_file is not None:
        figures_file.write(f"{line}\n".encode("ascii"))
        figures_file.flush()


def _encode_lossless(args: list[str], target: Path, *, stdin: bytes | None = None) -> Path:
    """Encode to a lossless 8-bit 4:2:0 HEVC MP4 with BT.709 tags (limited range)."""
    command = [
        "ffmpeg", "-nostdin", "-hide_banner", "-v", "error", "-y", *args,
        "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
        "-c:v", "libx265", "-bf", "0", "-x265-params",
        "lossless=1:log-level=error:colorprim=bt709:transfer=bt709:colormatrix=bt709:range=limited",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-color_range", "tv", "-an", str(target),
    ]  # fmt: skip
    subprocess.run(command, input=stdin, check=True, capture_output=True)
    return target


@pytest.fixture(scope="module")
def clips(sample: Sample, tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    """The two clips as lossless MP4s, built once per module."""
    folder = tmp_path_factory.mktemp("wp42-v3")
    ad14 = _encode_lossless(["-i", str(sample("ad14-flicker"))], folder / "ad14-flicker.mp4")
    _, images, _ = jitter_clip()
    height, width = images[0].shape[:2]
    raw = b"".join(np.ascontiguousarray(image).tobytes() for image in images)
    jitter = _encode_lossless(
        [
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{width}x{height}",
            "-framerate", "30000/1001", "-i", "-",
        ],
        folder / "jitter.mp4",
        stdin=raw,
    )  # fmt: skip
    return {"ad14": ad14, "jitter": jitter}


@pytest.fixture(scope="module")
def ad14_mask(sample: Sample) -> NDArray[np.bool_]:
    with PILImage.open(sample("ad14-mask")) as image:
        return np.asarray(image.convert("L")) > 127


def _jitter_mask() -> NDArray[np.bool_]:
    mask = np.zeros((270, 480), dtype=bool)
    mask[:JITTER_REGION_ROWS] = True
    return mask


def _decoded(path: Path) -> list[Frame]:
    reader = FFmpegVideoSource()
    stream = reader.frames(reader.probe(path), hw_decode=False)
    try:
        return list(stream)
    finally:
        stream.close()


# --- R0-Q5's condition: the lossless clips are inside WP3.9's envelope ----------------------------


def test_the_lossless_clips_decode_inside_wp39s_envelope(clips: dict[str, Path]) -> None:
    for name, frames, size in (("ad14", 90, (540, 960)), ("jitter", 90, (270, 480))):
        info = probe(clips[name])
        assert [f for f in info.faults if f.severity == "refuse"] == [], info.faults
        assert info.faults == ()  # no D86 fault, no assumed tag
        video = info.video
        assert (video.codec, video.bit_depth, video.pix_fmt) == ("hevc", 8, "yuv420p")
        assert (video.height, video.width) == size and video.nb_frames == frames
        assert (video.color.primaries, video.color.transfer, video.color.matrix) == (
            "bt709",
            "bt709",
            "bt709",
        )
        decoded = _decoded(clips[name])
        assert len(decoded) == frames
        assert all(f.pixels.shape == (*size, 3) for f in decoded)


# --- the measurement --------------------------------------------------------------------------


def _backend() -> Any:
    """The legs' backend: the CPU when :data:`BACKEND_VARIABLE` is ``cpu``, else the GPU."""
    if os.environ.get(BACKEND_VARIABLE) == "cpu":
        return backend_for("cpu")
    try:
        return backend_for("cuda:0")
    except Exception as exc:  # no usable CUDA device here
        pytest.skip(f"no CUDA backend: {exc}")


def _region(frame: Frame, mask: NDArray[np.bool_]) -> NDArray[np.float32]:
    """The measured region of a frame's pixels, on the host (a device frame is downloaded)."""
    pixels = (
        frame.pixels if frame.device == "cpu" else backend_for(frame.device).to_host(frame.pixels)
    )
    return np.asarray(pixels, dtype=np.float32)[mask]


def _figures(regions: list[NDArray[np.float32]]) -> tuple[float, NDArray[np.float64]]:
    """AD-14's figure and V3's flicker per measure, from each frame's measured region.

    AD-14's figure is the mean absolute frame-to-frame difference in the region, in /255; V3's
    flicker is the standard deviation of the frame-to-frame changes of each per-frame measure
    (mean L*, a*, b*, and the standard deviation of L*), as WP3.11's ``flicker`` measures them.
    """
    previous: NDArray[np.float64] | None = None
    differences, measures = [], []
    for out in regions:
        region = np.asarray(out, dtype=np.float64)
        if previous is not None:
            differences.append(float(np.mean(np.abs(region - previous))) * 255.0)
        previous = region
        values = lab(np.clip(region, 0.0, 1.0))
        measures.append([*values.mean(axis=0), float(np.std(values[:, 0]))])
    return float(np.mean(differences)), np.std(np.diff(np.array(measures), axis=0), axis=0)


class _Recording:
    """A real sink keeping the measured region of every frame it receives (pre-encode)."""

    def __init__(self, inner: Any, mask: NDArray[np.bool_]) -> None:
        self.inner = inner
        self.mask = mask
        self.regions: list[NDArray[np.float32]] = []
        self.devices: set[str] = set()

    def capabilities(self) -> Any:
        return self.inner.capabilities()

    def open(self, *args: Any, **kwargs: Any) -> None:
        self.inner.open(*args, **kwargs)

    def write(self, frame: Frame) -> None:
        self.devices.add(frame.device)
        self.regions.append(_region(frame, self.mask))
        self.inner.write(frame)

    def close(self) -> Any:
        return self.inner.close()

    def abort(self) -> None:
        self.inner.abort()


def _smoothed_export(
    clip: Path, method: str, mask: NDArray[np.bool_], folder: Path
) -> tuple[list[NDArray[np.float32]], Path]:
    """Export through the composed engine (the legs' backend); return the regions and the output."""
    device = _backend().device
    sinks: list[_Recording] = []

    def sink_for(device: ArrayBackend | None) -> Any:
        sinks.append(_Recording(composition.video_sink(device), mask))
        return sinks[-1]

    out = folder / f"out-{method}"
    out.mkdir()
    exports = composition.export_jobs(cache_folder=folder / f"cache-{method}", sink_for=sink_for)
    settings = Settings(output_folder=out, video_encoder="auto", force_cpu=device == "cpu")
    request = ExportRequest(clip, "video", new_parameter_set(method, {}), settings)
    result = exports.job(request)(StubProgress())
    assert result.ok, result.failure
    job = "CPU" if device == "cpu" else "GPU"
    assert result.device.startswith(job) and sinks[0].devices == {device}, result.device
    return sinks[0].regions, result.outputs[0]


def _unsmoothed(
    clip: Path, method_id: str, mask: NDArray[np.bool_], folder: Path
) -> list[NDArray[np.float32]]:
    """Render each decoded frame with its own (provisional) statistics, as the export would.

    The same decode (device frames on the job's backend), method, parameters and backend as the
    composed job; only the records differ (round-0 ruling R0-Q5 (a)).
    """
    gpu = _backend()
    hw_decode = gpu.device != "cpu"  # as the export job decides it
    method = composition.correction_methods()[method_id]
    info = probe(clip)
    params = effective_parameters(method, new_parameter_set(method_id, {}))
    cache = DiskProxyCache(folder / f"unsmoothed-cache-{method_id}")
    source = composition.video_source(gpu)
    engine = AnalysisEngine(
        method=method,
        backend=gpu,
        cache=cache,
        key=cache.key_for(clip),
        source=source,
        probe=info,
        params=params,
        hw_decode=hw_decode,
    )
    result = engine.analysis_job()(StubProgress())
    assert result.ok, result.failure
    regions = []
    stream = source.frames(info, hw_decode=hw_decode)
    try:
        for frame in stream:
            assert frame.device == gpu.device
            record = engine.provisional_record(frame.pts_ticks)
            assert record is not None
            on_device = replace(frame, pixels=gpu.asarray(frame.pixels, np.float32))
            rendered = method.render(on_device, params, record)
            regions.append(_region(replace(frame, pixels=rendered.pixels), mask))
    finally:
        stream.close()  # type: ignore[attr-defined]
        cache.close()
    return regions


def _encoded(output: Path, mask: NDArray[np.bool_]) -> list[NDArray[np.float32]]:
    reader = FFmpegVideoSource()
    stream = reader.frames(reader.probe(output), hw_decode=False)
    try:
        return [_region(frame, mask) for frame in stream]
    finally:
        stream.close()  # type: ignore[attr-defined]


def _line(name: str, figures: dict[str, Any]) -> str:
    shown = {k: v for k, v in figures.items() if not k.startswith(("v3_", "raw_"))}
    return f"{name}: " + "; ".join(f"{key} {value}" for key, value in shown.items())


def _ad14_holds(figure: float) -> bool:
    """AD-14's acceptance: the mean abs frame-to-frame difference under 0.5/255 (unrounded)."""
    return figure < 0.5


def _v3_holds(smoothed: NDArray[np.float64], unsmoothed: NDArray[np.float64]) -> bool:
    """V3's acceptance: per measure, the smoothed flicker at most 25 % of the per-frame one."""
    return bool(np.all(smoothed <= 0.25 * unsmoothed))


def _planted(
    smoothed: list[NDArray[np.float32]], unsmoothed: list[NDArray[np.float32]]
) -> tuple[list[NDArray[np.float32]], list[NDArray[np.float32]]]:
    """Two wrong renders of the clip that the acceptance checks must refuse (planted controls).

    AD-14's: the smoothed frames with 1/255 added to every other frame (a flicker of 1/255 in the
    region, twice the bound). V3's: the smoothed and the per-frame legs' frames interleaved, as an
    export that loses its smoothing on every other frame would render them.
    """
    flickered = [region + np.float32((i % 2) / 255.0) for i, region in enumerate(smoothed)]
    interleaved = [
        u if i % 2 else s for i, (s, u) in enumerate(zip(smoothed, unsmoothed, strict=True))
    ]
    return flickered, interleaved


def _v3(clip: Path, method: str, mask: NDArray[np.bool_], folder: Path) -> dict[str, Any]:
    smoothed_regions, output = _smoothed_export(clip, method, mask, folder)
    unsmoothed_regions = _unsmoothed(clip, method, mask, folder)
    assert len(smoothed_regions) == len(unsmoothed_regions) == 90
    flickered, interleaved = _planted(smoothed_regions, unsmoothed_regions)
    legs = (smoothed_regions, unsmoothed_regions, _encoded(output, mask), flickered, interleaved)
    with ThreadPoolExecutor(len(legs)) as pool:  # NumPy releases the GIL: the legs in parallel
        (
            (smoothed, v3_smoothed),
            (unsmoothed, v3_unsmoothed),
            (encoded, v3_encoded),
            (planted_ad14, _),
            (_, v3_planted),
        ) = pool.map(_figures, legs)
    return {
        "ad14_unsmoothed": round(unsmoothed, 4),
        "ad14_smoothed": round(smoothed, 4),
        "ad14_encoded": round(encoded, 4),
        "raw_ad14_smoothed": smoothed,  # the acceptance reads the unrounded figure (R1 F2)
        "raw_planted_ad14": planted_ad14,
        "v3_unsmoothed": v3_unsmoothed,
        "v3_smoothed": v3_smoothed,
        "v3_planted": v3_planted,
        "ratios": dict(
            zip(MEASURES, np.round(v3_smoothed / v3_unsmoothed, 3).tolist(), strict=True)
        ),
        "encoded_ratios": dict(
            zip(MEASURES, np.round(v3_encoded / v3_unsmoothed, 3).tolist(), strict=True)
        ),
        "ad14_planted": round(planted_ad14, 4),
        "planted_ratios": dict(
            zip(MEASURES, np.round(v3_planted / v3_unsmoothed, 3).tolist(), strict=True)
        ),
    }


@pytest.mark.parametrize("method", METHODS)
def test_ad14_bound_with_the_product_method(
    clips: dict[str, Path],
    ad14_mask: NDArray[np.bool_],
    tmp_path: Path,
    method: str,
    record_property: Callable[[str, object], None],
    figures_file: BinaryIO | None,
) -> None:
    """AD-14: under 0.5/255 after smoothing, ASSERTED; V3's four ratios RECORDED (V3-1)."""
    _backend()
    figures = _v3(clips["ad14"], method, ad14_mask, tmp_path)
    print(_line(f"ad14-flicker {method}", figures))
    _keep(figures_file, _line(f"ad14-flicker {method}", figures))
    record_property("v3", _line(method, figures))
    assert np.all(np.isfinite(list(figures["ratios"].values())))
    assert not _ad14_holds(figures["raw_planted_ad14"]), figures["raw_planted_ad14"]  # control
    assert _ad14_holds(figures["raw_ad14_smoothed"]), figures


@pytest.mark.parametrize("method", METHODS)
def test_v3_ratio_on_the_jittering_patch_clip_with_the_product_method(
    clips: dict[str, Path],
    tmp_path: Path,
    method: str,
    record_property: Callable[[str, object], None],
    figures_file: BinaryIO | None,
) -> None:
    """V3: per measure, the smoothed flicker <= 25 % of the per-frame, ASSERTED."""
    _backend()
    figures = _v3(clips["jitter"], method, _jitter_mask(), tmp_path)
    print(_line(f"jitter {method}", figures))
    _keep(figures_file, _line(f"jitter {method}", figures))
    record_property("v3", _line(method, figures))
    unsmoothed = figures["v3_unsmoothed"]
    assert np.all(unsmoothed > 0)
    # The planted control: every other frame rendered without smoothing, through the same
    # measurement and acceptance, is refused.
    assert not _v3_holds(figures["v3_planted"], unsmoothed), figures["v3_planted"] / unsmoothed
    assert _v3_holds(figures["v3_smoothed"], unsmoothed), figures["ratios"]


def test_the_acceptance_reads_the_unrounded_figures(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reviewer A R1 F2: a figure just under the bound is accepted (it is not rounded first)."""
    import sys

    module = sys.modules[__name__]
    regions = [np.zeros(3, dtype=np.float32)] * 90
    monkeypatch.setattr(module, "_smoothed_export", lambda *args: (regions, Path("out.mp4")))
    monkeypatch.setattr(module, "_unsmoothed", lambda *args: regions)
    monkeypatch.setattr(module, "_encoded", lambda *args: regions)
    monkeypatch.setattr(module, "_figures", lambda legs: (0.49999, np.ones(4)))
    figures = _v3(Path("clip.mp4"), "c3", np.ones(3, dtype=bool), Path("."))
    assert figures["ad14_smoothed"] == 0.5  # the shown figure is rounded
    assert _ad14_holds(figures["raw_ad14_smoothed"])
    assert not _ad14_holds(0.5) and _v3_holds(np.full(4, 0.25), np.ones(4))
    assert not _v3_holds(np.array([0.1, 0.1, 0.1, 0.26]), np.ones(4))
