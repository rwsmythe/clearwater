from __future__ import annotations

import dataclasses
import importlib
import json
import logging
import subprocess
import sys
import types
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from scipy import ndimage

import test_prototype_pipeline as pipeline_tests
from prototype import bench, pipeline, run
from prototype.backend import CPU, memory_estimate_bytes, of, select_backend
from prototype.params import Params
from test_prototype_pipeline import _synthetic, _textured_scene, _write_input

_AUTO = select_backend("auto")
requires_gpu = pytest.mark.skipif(
    _AUTO.name != "gpu", reason=f"no CUDA device usable: {_AUTO.reason}"
)

# CPU versus GPU agreement of correct() outputs (brief, fixed at issue): float32.
AGREEMENT_MAX_ABS = 2e-5
AGREEMENT_MEAN_ABS = 2e-6
# The near-flat WP1.1 `_synthetic` pair (CHARC ruling on finding 1): its own bound.
NEAR_FLAT_MAX_ABS = 1e-4
NEAR_FLAT_MEAN_ABS = 1e-5
# The most values a pipeline function may move between host and device (scalar statistics).
TRANSFER_LIMIT = 16

METHODS = ["ancuti2018", "c3"]


@pytest.fixture(autouse=True)
def _short_stray_check(monkeypatch: pytest.MonkeyPatch) -> None:
    """The stray-process check samples 10 s in a timed window; 0.2 s is enough for a test."""
    monkeypatch.setattr(bench, "STRAY_SAMPLE_S", 0.2)


def _fake_cupy(count: Any = 1, kernel_error: Exception | None = None) -> types.SimpleNamespace:
    """A stand-in for the cupy module: a device count and a test kernel that may fail."""

    def get_device_count() -> int:
        if isinstance(count, Exception):
            raise count
        return int(count)

    def arange(*args: Any, **kwargs: Any) -> Any:
        if kernel_error is not None:
            raise kernel_error
        return np.arange(*args, **kwargs)

    runtime = types.SimpleNamespace(getDeviceCount=get_device_count)
    return types.SimpleNamespace(
        cuda=types.SimpleNamespace(runtime=runtime), arange=arange, float32=np.float32
    )


# --- backend selection (CPU only) -------------------------------------------------------


def test_select_cpu_is_numpy_and_scipy() -> None:
    backend = select_backend("cpu")
    assert backend is CPU
    assert backend.name == "cpu"
    assert backend.xp is np
    assert backend.ndimage is ndimage
    assert backend.reason == ""


def test_auto_without_cupy_falls_back_to_cpu_with_a_logged_reason(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setitem(sys.modules, "cupy", None)  # import cupy now raises ImportError
    with caplog.at_level(logging.INFO, logger="prototype.backend"):
        backend = select_backend("auto")
    assert backend.name == "cpu"
    assert backend.xp is np
    assert "cupy is not installed" in backend.reason
    assert backend.reason in caplog.text


@pytest.mark.parametrize(
    ("fake", "reason"),
    [
        (_fake_cupy(count=0), "reports no device"),
        (_fake_cupy(count=RuntimeError("cudaErrorNoDevice")), "did not answer"),
        (_fake_cupy(kernel_error=RuntimeError("Failed to find CUDA headers")), "test kernel"),
    ],
)
def test_auto_without_a_usable_device_falls_back_to_cpu(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    fake: types.SimpleNamespace,
    reason: str,
) -> None:
    monkeypatch.setitem(sys.modules, "cupy", fake)
    with caplog.at_level(logging.INFO, logger="prototype.backend"):
        backend = select_backend("auto")
    assert backend.name == "cpu"
    assert reason in backend.reason
    assert reason in caplog.text


def test_gpu_without_a_device_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "cupy", _fake_cupy(count=0))
    with pytest.raises(RuntimeError, match=r"no usable CUDA device: .*reports no device"):
        select_backend("gpu")
    monkeypatch.setitem(sys.modules, "cupy", None)
    with pytest.raises(RuntimeError, match="cupy is not installed"):
        select_backend("gpu")


def test_select_rejects_an_unknown_device() -> None:
    with pytest.raises(ValueError, match="device must be one of"):
        select_backend("tpu")


def test_of_numpy_is_cpu_and_round_trip_is_identity() -> None:
    array = np.arange(12, dtype=np.float32).reshape(2, 2, 3)
    assert of(array) is CPU
    assert CPU.to_device(array) is array
    assert CPU.to_host(array) is array
    CPU.synchronize()
    with pytest.raises(TypeError, match="numpy or cupy array"):
        of([1.0, 2.0])


def test_correct_with_the_cpu_backend_is_the_default_path() -> None:
    image = _synthetic(64, 96)
    for method in METHODS:
        params = Params(method=method)  # type: ignore[arg-type]
        implicit = pipeline.correct(image, params)
        explicit = pipeline.correct(image, params, CPU)
        np.testing.assert_array_equal(implicit.output, explicit.output)
        np.testing.assert_array_equal(implicit.input2, explicit.input2)


def test_pipeline_rejects_a_non_array() -> None:
    with pytest.raises(ValueError, match="float32"):
        pipeline.correct([[[0.5, 0.5, 0.5]]], Params(method="ancuti2018"))  # type: ignore[arg-type]


def test_normalisation_bounds_are_the_ones_fusion_inputs_uses() -> None:
    image = _textured_scene(64, 96)
    params = Params()
    low, high = pipeline.normalisation_bounds(image, params)
    blurred = ndimage.gaussian_filter(
        image, (0.005 * 64, 0.005 * 64, 0), mode="reflect", truncate=4.0
    )
    expected = np.percentile(image - blurred, [0.5, 99.5], method="linear")
    np.testing.assert_allclose([low, high], expected, rtol=0, atol=1e-7)
    assert low < 0.0 < high


# --- memory estimate (CPU only) ---------------------------------------------------------


def test_memory_estimate_is_monotone_in_pixel_count_and_positive() -> None:
    params = Params()
    assert memory_estimate_bytes((1, 1, 3), params) > 0
    shapes = [(1, 1, 3), (2, 1, 3), (72, 128, 3), (1080, 1920, 3), (2160, 3840, 3)]
    shapes += [(2988, 5312, 3), (6048, 8064, 3)]
    estimates = [memory_estimate_bytes(shape, params) for shape in shapes]
    assert estimates == sorted(estimates)
    assert len(set(estimates)) == len(estimates)
    # same pixel count, either orientation: same estimate
    assert memory_estimate_bytes((2160, 3840, 3), params) == memory_estimate_bytes(
        (3840, 2160, 3), params
    )


# --- GPU --------------------------------------------------------------------------------


def _output_difference(image: np.ndarray, method: str) -> np.ndarray:
    """|CPU output - GPU output| of correct() with the default Params of ``method``."""
    params = Params(method=method)  # type: ignore[arg-type]
    cpu_out = pipeline.correct(image, params).output
    gpu_out = pipeline.correct(image, params, select_backend("gpu")).output
    assert type(gpu_out) is np.ndarray
    return np.abs(cpu_out.astype(np.float64) - gpu_out)


@pytest.mark.gpu
@requires_gpu
@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("size", [(64, 96), (97, 65), (1024, 1536)])
def test_gpu_output_agrees_with_cpu(size: tuple[int, int], method: str) -> None:
    """The fixed tolerance, on WP1.1's textured scene at the two WP1.1 sizes and 1024 px."""
    difference = _output_difference(_textured_scene(*size), method)
    assert difference.max() <= AGREEMENT_MAX_ABS, float(difference.max())
    assert difference.mean() <= AGREEMENT_MEAN_ABS, float(difference.mean())


@pytest.mark.gpu
@requires_gpu
@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("size", [(64, 96), (97, 65)])
def test_gpu_output_on_near_flat_images_within_its_own_bound(
    size: tuple[int, int], method: str
) -> None:
    """WP1.1's near-flat ``_synthetic`` pair, under a wider documented bound (CHARC, F1).

    Attributed cause: cupyx's Gaussian filters accumulate float32 input in float32 where
    scipy accumulates in float64, so the high-pass ``I - G*I`` differs by about 1 ulp
    (1.2e-7); on these near-flat images the stretch N{} spans only about 0.0018 (0.0021 at
    97x65), so it amplifies that difference about 500-fold (measured max-abs 2.7e-5 to
    3.6e-5, mean-abs 3.3e-6 to 4.6e-6, over the fixed 2e-5 / 2e-6). The bound below still
    catches a regression of the GPU path here; the ill-conditioning is banked as DR-14.
    """
    difference = _output_difference(_synthetic(*size), method)
    assert difference.max() <= NEAR_FLAT_MAX_ABS, float(difference.max())
    assert difference.mean() <= NEAR_FLAT_MEAN_ABS, float(difference.mean())


@pytest.mark.gpu
@requires_gpu
def test_gpu_correct_returns_host_arrays_for_a_host_input() -> None:
    gpu = select_backend("gpu")
    image = _synthetic(64, 96)
    result = pipeline.correct(image, Params(method="c3"), gpu)
    arrays = [result.output, result.fused, result.compensated, result.white_balanced]
    arrays += [result.input1, result.input2]
    for group in dataclasses.astuple(result.weights):
        arrays += list(group)
    for array in arrays:
        assert type(array) is np.ndarray
        assert array.dtype == np.float32
    np.testing.assert_array_equal(image, _synthetic(64, 96))  # the input is not modified


def _forbid_array_transfers(cupy: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    """Make CuPy's Python transfer entry points raise when the pipeline moves an array.

    ``cupy.asnumpy`` (device to host, also behind ``Backend.to_host``) and ``cupy.asarray``
    / ``cupy.array`` given a NumPy array (host to device), called from
    ``prototype.pipeline`` or ``prototype.backend`` with more than ``TRANSFER_LIMIT``
    values, fail, so a step that computes on the host and returns a CuPy array fails
    here. Scalar statistics (channel means, percentile bounds, the gains) and the cached
    constants stay under the limit; cupyx's own uploads (its Gaussian kernel weights) are
    not from those modules. Blind spot: the Cython methods ``ndarray.get``,
    ``ndarray.set`` and ``ndarray.tolist`` cannot be patched.
    """

    def guard(original: Any, source: type) -> Any:
        def guarded(array: Any, *args: Any, **kwargs: Any) -> Any:
            caller = sys._getframe(1).f_globals.get("__name__", "")
            from_pipeline = caller in ("prototype.pipeline", "prototype.backend")
            if from_pipeline and isinstance(array, source) and array.size > TRANSFER_LIMIT:
                raise AssertionError(f"{caller} moved an array of {array.size} values")
            return original(array, *args, **kwargs)

        return guarded

    monkeypatch.setattr(cupy, "asnumpy", guard(cupy.asnumpy, cupy.ndarray))
    monkeypatch.setattr(cupy, "asarray", guard(cupy.asarray, np.ndarray))
    monkeypatch.setattr(cupy, "array", guard(cupy.array, np.ndarray))


@pytest.mark.gpu
@requires_gpu
def test_every_public_pipeline_function_keeps_cupy_arrays_on_the_device(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gpu = select_backend("gpu")
    cupy = gpu.xp
    params = Params(method="ancuti2018")
    image = gpu.to_device(_synthetic(64, 96))
    weight = gpu.to_device(np.random.default_rng(3).random((64, 96), dtype=np.float32))
    assert of(image) is gpu
    _forbid_array_transfers(cupy, monkeypatch)

    def check(array: Any, shape: tuple[int, ...]) -> None:
        assert isinstance(array, cupy.ndarray)  # no silent round trip to the host
        assert array.shape == shape
        assert array.dtype == np.float32

    shape, map_shape = (64, 96, 3), (64, 96)
    for step in (pipeline.compensate_ancuti2018, pipeline.compensate_c3, pipeline.white_balance):
        out, _ = step(image, params)
        check(out, shape)
    for out in pipeline.fusion_inputs(image, params):
        check(out, shape)
    weights = pipeline.weight_maps((image, image), params)
    for group in dataclasses.astuple(weights):
        for out in group:
            check(out, map_shape)
    check(pipeline.multiscale_fusion((image, image), (weight, 1.0 - weight), params), shape)
    for convert in (
        pipeline.rgb_to_ycbcr,
        pipeline.ycbcr_to_rgb,
        pipeline.srgb_to_lab,
    ):
        check(convert(image), shape)
    check(pipeline.luminance(image), map_shape)
    levels = pipeline.pyramid_levels(shape, 4)
    gaussian = pipeline.gaussian_pyramid(image, levels)
    laplacian = pipeline.laplacian_pyramid(image, levels)
    for level in [*gaussian, *laplacian]:
        assert isinstance(level, cupy.ndarray)
    check(pipeline.collapse_pyramid(laplacian), shape)
    check(pipeline.expand(gaussian[1], shape), shape)
    check(pipeline.expand(pipeline.gaussian_pyramid(weight, levels)[1], map_shape), map_shape)
    low, high = pipeline.normalisation_bounds(image, params)
    assert isinstance(low, float)
    assert isinstance(high, float)
    result = pipeline.correct(image, params)
    for array in [result.output, result.fused, result.compensated, result.white_balanced]:
        check(array, shape)
    check(result.weights.normalised[0], map_shape)


@pytest.mark.gpu
@requires_gpu
def test_gpu_backend_round_trip_and_cpu_backend_on_a_device_input() -> None:
    gpu = select_backend("gpu")
    host = _synthetic(32, 48)
    device = gpu.to_device(host)
    assert of(device) is gpu
    assert gpu.to_device(device) is device
    np.testing.assert_array_equal(gpu.to_host(device), host)
    assert CPU.to_device(device).__class__ is np.ndarray
    gpu.synchronize()
    # a device input with the CPU backend: computed on the host, returned on the device
    result = pipeline.correct(device, Params(method="ancuti2018"), CPU)
    assert isinstance(result.output, gpu.xp.ndarray)
    np.testing.assert_array_equal(
        gpu.to_host(result.output), pipeline.correct(host, Params(method="ancuti2018")).output
    )


@pytest.mark.gpu
@requires_gpu
def test_bench_gpu_records_graphics_memory(tmp_path: Path) -> None:
    args = ["--device", "gpu", "--size", "128x72", "--frames", "2", "--method", "c3"]
    assert bench.main([*args, "--out", str(tmp_path)]) == 0
    (path,) = tmp_path.glob("bench-gpu-128x72-c3-*.json")
    record = json.loads(path.read_text(encoding="utf-8"))
    memory = record["memory"]
    assert memory["gpu_pool_peak_used_mb"] > 0
    assert memory["gpu_pool_reserved_mb"] >= memory["gpu_pool_peak_used_mb"]
    assert record["device_resident"]["median_s"] is not None
    assert record["versions"]["cupy"]
    assert record["estimate"]["ratio_to_gpu_pool_reserved"] >= 1.0


# --- bench (CPU) ------------------------------------------------------------------------

BENCH_KEYS = {
    "label",
    "tool",
    "created",
    "device",
    "backend",
    "size",
    "shape",
    "method",
    "frames",
    "seed",
    "generator",
    "params",
    "timing",
    "device_resident",
    "memory",
    "estimate",
    "proxy",
    "versions",
    "machine",
    "ambient",
}
TIMING_KEYS = {
    "method",
    "per_frame_s",
    "warmup_discarded",
    "median_s",
    "p95_s",
    "first10_median_s",
    "last10_median_s",
    "drift",
    "budget_share_30fps",
    "budget_share_60fps",
}


def test_bench_writes_a_record_with_the_documented_keys(tmp_path: Path) -> None:
    args = ["--device", "cpu", "--size", "128x72", "--frames", "3", "--method", "ancuti2018"]
    out = tmp_path / "records"
    assert bench.main([*args, "--out", str(out), "--proxy", "36", "--note", "test"]) == 0
    (path,) = out.glob("bench-cpu-128x72-ancuti2018-*.json")
    record = json.loads(path.read_text(encoding="utf-8"))
    assert set(record) == BENCH_KEYS
    assert record["label"] == "SYNTHETIC"
    assert record["backend"] == "cpu"
    assert record["shape"] == [72, 128, 3]
    assert record["device_resident"] is None
    timing = record["timing"]
    assert set(timing) == TIMING_KEYS
    assert len(timing["per_frame_s"]) == 3
    assert timing["median_s"] == pytest.approx(float(np.median(timing["per_frame_s"][1:])))
    assert timing["budget_share_30fps"] == pytest.approx(timing["median_s"] / 0.111)
    assert record["memory"]["rss_peak_mb"] >= record["memory"]["rss_baseline_mb"] > 0
    assert record["estimate"]["bytes"] == memory_estimate_bytes((72, 128, 3), Params())
    full, proxy = record["proxy"]
    assert full["short_side"] == 72
    assert full["relative_error"]["input_means"] == [0.0, 0.0, 0.0]
    assert proxy["short_side"] == 36
    assert proxy["shape"] == [36, 64, 3]
    assert set(proxy["relative_error"]) == {
        "input_means",
        "compensated_means",
        "white_balance_gains",
        "normalisation_bounds",
    }
    assert record["ambient"]["note"] == "test"
    assert {"power_scheme", "power_overlay", "power_overlay_name"} <= set(record["ambient"])
    assert {"gpu_state_loop_start", "gpu_state_loop_end"} <= set(record["ambient"])


def test_bench_one_frame_has_no_steady_statistics(tmp_path: Path) -> None:
    args = ["--device", "cpu", "--size", "16x16", "--frames", "1", "--method", "c3"]
    assert bench.main([*args, "--out", str(tmp_path)]) == 0
    (path,) = tmp_path.glob("*.json")
    timing = json.loads(path.read_text(encoding="utf-8"))["timing"]
    assert len(timing["per_frame_s"]) == 1
    assert timing["median_s"] is None


def test_bench_timing_summary_discards_the_warm_up_frame() -> None:
    times = [10.0, *(1.0 for _ in range(10)), *(2.0 for _ in range(10))]
    record = bench._timing_record(times)
    assert record["median_s"] == pytest.approx(1.5)
    assert record["first10_median_s"] == pytest.approx(1.0)
    assert record["last10_median_s"] == pytest.approx(2.0)
    assert record["drift"] == pytest.approx(1.0)
    assert record["p95_s"] == pytest.approx(2.0)


@pytest.mark.parametrize(
    "change",
    [
        {"--device": "tpu"},
        {"--size": "4kk"},
        {"--size": "0x10"},
        {"--frames": "0"},
        {"--frames": "x"},
        {"--method": "bogus"},
        {"--proxy": "100"},
        {"--proxy": "0"},
        {"--out": None},
    ],
)
def test_bench_bad_arguments_exit_2(
    tmp_path: Path, change: dict[str, str | None], capsys: pytest.CaptureFixture[str]
) -> None:
    options: dict[str, str | None] = {
        "--device": "cpu",
        "--size": "128x72",
        "--frames": "2",
        "--method": "c3",
        "--out": str(tmp_path),
    }
    options |= change
    argv = [item for key, value in options.items() if value is not None for item in (key, value)]
    assert bench.main(argv) == 2
    err = capsys.readouterr().err
    assert err.startswith("error: ")
    assert len(err.strip().splitlines()) == 1
    assert not list(tmp_path.glob("*.json"))


def test_bench_unusable_gpu_exits_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setitem(sys.modules, "cupy", None)
    args = ["--device", "gpu", "--size", "16x16", "--frames", "1", "--method", "c3"]
    assert bench.main([*args, "--out", str(tmp_path)]) == 2
    assert "no usable CUDA device" in capsys.readouterr().err


def test_synthetic_frame_is_seeded_and_in_range() -> None:
    frame = bench.synthetic_frame(72, 128, seed=4)
    assert frame.shape == (72, 128, 3)
    assert frame.dtype == np.float32
    assert frame.min() >= 0.0
    assert frame.max() <= 1.0
    np.testing.assert_array_equal(frame, bench.synthetic_frame(72, 128, seed=4))
    assert not np.array_equal(frame, bench.synthetic_frame(72, 128, seed=5))
    means = frame.reshape(-1, 3).mean(axis=0)
    assert means[0] < means[1] and means[0] < means[2]  # a blue-green cast


def test_proxy_frame_area_averages_to_the_short_side() -> None:
    frame = bench.synthetic_frame(72, 128)
    proxy = bench.proxy_frame(frame, 36)
    assert proxy.shape == (36, 64, 3)
    expected = frame.reshape(36, 2, 64, 2, 3).mean(axis=(1, 3))
    np.testing.assert_allclose(proxy, expected, rtol=0, atol=1e-6)
    assert bench.proxy_frame(frame, 72) is frame


def test_bench_works_as_a_script(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parent.parent / "tools" / "prototype" / "bench.py"
    args = ["--device", "cpu", "--size", "32x24", "--frames", "2", "--method", "c3"]
    completed = subprocess.run(
        [sys.executable, str(script), *args, "--out", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stderr
    assert Path(completed.stdout.strip()).is_file()


# --- run.py --device ---------------------------------------------------------------------


def _run_backend(tmp_path: Path, *extra: str) -> str:
    source = _write_input(tmp_path)
    out = tmp_path / "out"
    assert (
        run.main(
            ["--in", str(source), "--out", str(out), "--method", "ancuti2018", "--dump", *extra]
        )
        == 0
    )
    weights = json.loads((out / "scene-ancuti2018-weights.json").read_text(encoding="utf-8"))
    return str(weights["backend"])


def test_run_defaults_to_the_cpu_and_records_the_backend(tmp_path: Path) -> None:
    assert _run_backend(tmp_path) == "cpu"


def test_run_auto_without_cupy_notes_the_cpu_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setitem(sys.modules, "cupy", None)
    assert _run_backend(tmp_path, "--device", "auto") == "cpu"
    assert "note: running on the CPU: cupy is not installed" in capsys.readouterr().err


@pytest.mark.parametrize("device", ["gpu", "tpu"])
def test_run_bad_or_unusable_device_exits_2(
    tmp_path: Path,
    device: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setitem(sys.modules, "cupy", None)
    source = _write_input(tmp_path)
    assert run.main(["--in", str(source), "--out", str(tmp_path), "--device", device]) == 2
    err = capsys.readouterr().err
    assert err.startswith("error: ")
    assert len(err.strip().splitlines()) == 1


@pytest.mark.gpu
@requires_gpu
def test_run_on_the_gpu_records_the_backend(tmp_path: Path) -> None:
    assert _run_backend(tmp_path, "--device", "gpu") == "gpu"


@pytest.mark.gpu
@requires_gpu
@pytest.mark.parametrize("method", METHODS)
def test_memory_estimate_bounds_the_measured_pool_peak(method: str) -> None:
    """At a size where the per-pixel term dominates, the estimate covers the pool's peak."""
    gpu = select_backend("gpu")
    frame = bench.synthetic_frame(1024, 1536)
    params = Params(method=method)  # type: ignore[arg-type]
    tracker = bench._PoolTracker(gpu)
    try:
        pipeline.correct(frame, params, gpu)
        gpu.synchronize()
    finally:
        tracker.close()
    reserved = int(gpu.xp.get_default_memory_pool().total_bytes())
    estimate = memory_estimate_bytes(frame.shape, params)
    assert estimate >= reserved >= tracker.peak_used
    assert estimate <= 1.5 * reserved  # an upper bound, not a loose one


def test_auto_falls_back_when_cupyx_does_not_import(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setitem(sys.modules, "cupy", _fake_cupy())
    monkeypatch.setitem(sys.modules, "cupyx.scipy.ndimage", None)
    with caplog.at_level(logging.INFO, logger="prototype.backend"):
        backend = select_backend("auto")
    assert backend.name == "cpu"
    assert "cupyx.scipy.ndimage did not import" in backend.reason
    with pytest.raises(RuntimeError, match="cupyx"):
        select_backend("gpu")


@pytest.mark.parametrize(
    "error",
    [
        OSError("DLL load failed while importing cuda"),
        RuntimeError("CUDA driver version is insufficient for CUDA runtime version"),
    ],
)
def test_auto_falls_back_when_cupy_fails_to_initialise(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, error: Exception
) -> None:
    """An installed CuPy whose import raises something other than ImportError (WP1.2R M1)."""
    real_import = importlib.import_module

    def import_module(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "cupy":
            raise error
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(importlib, "import_module", import_module)
    with caplog.at_level(logging.INFO, logger="prototype.backend"):
        backend = select_backend("auto")
    assert backend.name == "cpu"
    assert backend.xp is np
    assert str(error) in backend.reason
    assert backend.reason in caplog.text
    with pytest.raises(RuntimeError, match="no usable CUDA device") as raised:
        select_backend("gpu")
    assert str(error) in str(raised.value)


@pytest.mark.gpu
@requires_gpu
def test_scalar_reductions_accumulate_in_float64_on_the_gpu(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """WP1.2R M3: the GPU takes the same float64 accumulator through the same call."""
    pipeline_tests.assert_scalar_reductions_use_float64(select_backend("gpu"), monkeypatch)
