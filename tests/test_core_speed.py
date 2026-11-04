"""WP3.1 and WP3.4: the speed-row instrument ``tools/core_speed.py`` without footage or a GPU."""

from __future__ import annotations

import re
import subprocess
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import scipy.ndimage

import clearwater.core
import core_speed
from clearwater.core import CoreBackend, NumpyBackend
from prototype import pipeline as proto
from prototype.params import Params

# The prototype functions whose calls make up the op mix, counted where the prototype looks
# them up (module globals, and the numpy / scipy.ndimage modules its backend hands out).
PROTOTYPE_OPS = (
    "_gaussian",
    "_binomial_blur",
    "expand",
    "_channel_means",
    "_cap_statistic",
    "_lab_mean",
    "luminance",
    "srgb_to_lab",
    "rgb_to_ycbcr",
    "ycbcr_to_rgb",
    "_high_pass_and_bounds",
    "high_pass_of",
)
PRODUCT_METHODS = (
    "gaussian_blur",
    "pyramid_reduce",
    "pyramid_expand",
    "rgb_to_ycbcr",
    "ycbcr_to_rgb",
    "percentile",
)
PRODUCT_HELPERS = ("channel_means", "mean", "luminance", "rgb_to_lab", "laplacian")


def counting(counts: Counter[str], name: str, function: Callable[..., Any]) -> Any:
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        counts[name] += 1
        return function(*args, **kwargs)

    return wrapper


def host_reads(counts: Counter[str], function: Callable[..., Any]) -> Any:
    """Wrap ``function`` so that reading its result back to Python counts as a host read.

    On the GPU, ``tolist()`` and ``float()`` of a statistic are device-to-host reads (sync
    points); the CPU stand-in counts them. Arithmetic on the result gives plain arrays.
    """

    class HostRead(np.ndarray):
        def tolist(self) -> Any:
            counts["proto host read"] += 1
            return np.asarray(self).tolist()

        def __float__(self) -> float:
            counts["proto host read"] += 1
            return float(np.asarray(self))

        def __array_ufunc__(self, ufunc: Any, method: str, *inputs: Any, **kwargs: Any) -> Any:
            plain = tuple(np.asarray(x) if isinstance(x, HostRead) else x for x in inputs)
            return getattr(ufunc, method)(*plain, **kwargs)

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return np.asarray(function(*args, **kwargs)).view(HostRead)

    return wrapper


@pytest.fixture
def counts(monkeypatch: pytest.MonkeyPatch) -> Counter[str]:
    counted: Counter[str] = Counter()
    for name in PROTOTYPE_OPS:
        monkeypatch.setattr(proto, name, counting(counted, f"proto {name}", getattr(proto, name)))
    # The prototype's statistics: every whole-frame mean, and the N{} percentiles.
    monkeypatch.setattr(proto, "_accumulate_mean", host_reads(counted, proto._accumulate_mean))
    percentile = host_reads(counted, np.percentile)
    monkeypatch.setattr(np, "percentile", counting(counted, "proto percentile", percentile))
    laplace = scipy.ndimage.laplace
    monkeypatch.setattr(scipy.ndimage, "laplace", counting(counted, "proto laplace", laplace))
    for name in PRODUCT_METHODS:
        method = getattr(CoreBackend, name)
        monkeypatch.setattr(CoreBackend, name, counting(counted, f"product {name}", method))
    for name in PRODUCT_HELPERS:
        helper = getattr(clearwater.core, name)
        monkeypatch.setattr(clearwater.core, name, counting(counted, f"product {name}", helper))
    return counted


def calls(counts: Counter[str], prefix: str) -> dict[str, int]:
    return {key: value for key, value in counts.items() if key.startswith(prefix)}


@pytest.mark.parametrize("method", core_speed.METHODS)
def test_op_mix_is_one_correct_call(counts: Counter[str], method: str) -> None:
    # Round 1 F4: the op mix makes every array operation one prototype correct() call makes
    # (default parameters), and the product path the same operations through IF-2 and the
    # clearwater.core helpers. Not counted: the per-pixel arithmetic between them.
    image = np.random.default_rng(3).random((96, 128, 3), dtype=np.float32)
    proto.correct(image, Params(method=method))
    in_correct = calls(counts, "proto ")
    counts.clear()
    core_speed.op_mix_prototype(image, method, Params())
    assert calls(counts, "proto ") == in_correct
    assert calls(counts, "product ") == {}
    counts.clear()
    backend = NumpyBackend()
    core_speed.op_mix_product(backend, backend.asarray(image), method, Params())
    # The module-level counters see the product's own numpy / scipy calls too; skip them.
    product = Counter(
        {key.removeprefix("product "): value for key, value in calls(counts, "product ").items()}
    )
    p = Counter({key.removeprefix("proto "): value for key, value in in_correct.items()})
    assert set(product) <= {*PRODUCT_METHODS, *PRODUCT_HELPERS}
    assert product["gaussian_blur"] == p["_gaussian"]
    assert product["pyramid_expand"] == p["expand"]
    assert product["pyramid_reduce"] == p["_binomial_blur"] - 2 * p["expand"]  # 2 per expand
    assert product["channel_means"] == p["_channel_means"] + p["_lab_mean"]
    assert product["mean"] == p["_cap_statistic"]
    assert product["luminance"] == p["luminance"]
    assert product["rgb_to_lab"] == p["srgb_to_lab"]
    assert product["rgb_to_ycbcr"] == p["rgb_to_ycbcr"]
    assert product["ycbcr_to_rgb"] == p["ycbcr_to_rgb"]
    assert product["percentile"] == p["percentile"]
    assert product["laplacian"] == p["laplace"]


def fake_run(returncode: int, stdout: str, stderr: str = "") -> Any:
    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, returncode, stdout, stderr)

    return run


def test_gpu_snapshot_reads_one_line(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(core_speed.subprocess, "run", fake_run(0, "2100, 8001, 61, 97, 3100, 80\n"))
    snapshot = core_speed.gpu_snapshot()
    assert snapshot["clocks.sm"] == "2100" and snapshot["power.draw"] == "80"


@pytest.mark.parametrize(
    ("returncode", "stdout", "stderr"),
    [(9, "", "NVIDIA-SMI has failed"), (0, "", ""), (6, "No devices were found\n", "")],
)
def test_gpu_snapshot_failure_is_recorded(
    monkeypatch: pytest.MonkeyPatch, returncode: int, stdout: str, stderr: str
) -> None:
    # Round 1 F7: a failing nvidia-smi neither raises nor passes for a reading.
    monkeypatch.setattr(core_speed.subprocess, "run", fake_run(returncode, stdout, stderr))
    snapshot = core_speed.gpu_snapshot()
    assert list(snapshot) == ["unavailable"]
    assert snapshot["unavailable"].startswith(f"nvidia-smi exit {returncode}")


def test_gpu_snapshot_without_nvidia_smi(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(command: list[str], **kwargs: Any) -> Any:
        raise FileNotFoundError(command[0])

    monkeypatch.setattr(core_speed.subprocess, "run", missing)
    assert core_speed.gpu_snapshot() == {"unavailable": "nvidia-smi did not run: FileNotFoundError"}


# -- WP3.4: the whole-core row, the memory leg, DR-37 (d) and (e) -------------------------------


@pytest.mark.parametrize(
    "stdout",
    ['{"streams": []}', "{}", '{"streams": [{"width": 3840}]}', "not json", '{"streams": null}'],
)
def test_probe_clip_without_a_video_stream_is_a_speed_error(
    monkeypatch: pytest.MonkeyPatch, stdout: str
) -> None:
    # DR-37 (d): an IndexError / KeyError there was not a SpeedError
    monkeypatch.setattr(core_speed.subprocess, "run", fake_run(0, stdout))
    with pytest.raises(core_speed.SpeedError, match="no usable video stream"):
        core_speed.probe_clip(core_speed.Path("clip.mp4"))


def test_probe_clip_reads_the_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    stdout = '{"streams": [{"width": 3840, "height": 2160, "nb_read_packets": "12"}]}'
    monkeypatch.setattr(core_speed.subprocess, "run", fake_run(0, stdout))
    clip = core_speed.probe_clip(core_speed.Path("clip.mp4"))
    assert (clip.width, clip.height, clip.frames) == (3840, 2160, 12)


def test_pci_key_compares_cupy_and_nvidia_smi_spellings() -> None:
    assert core_speed.pci_key("0000:01:00.0") == core_speed.pci_key("00000000:01:00.0")
    assert core_speed.pci_key("0000:01:00.0") != core_speed.pci_key("00000000:02:00.0")
    assert core_speed.pci_key("GPU-1234") is None


def test_gpu_snapshot_reads_the_cupy_device_row(monkeypatch: pytest.MonkeyPatch) -> None:
    # DR-37 (e): the row of the CuPy device's bus, not the first row
    rows = (
        "00000000:01:00.0, 1000, 1, 40, 5, 100, 10\n00000000:02:00.0, 2100, 2, 61, 97, 3100, 80\n"
    )
    monkeypatch.setattr(core_speed.subprocess, "run", fake_run(0, rows))
    snapshot = core_speed.gpu_snapshot("0000:02:00.0")
    assert snapshot["clocks.sm"] == "2100" and snapshot["pci.bus_id"] == "00000000:02:00.0"
    assert core_speed.gpu_snapshot("0000:01:00.0")["clocks.sm"] == "1000"
    missing = core_speed.gpu_snapshot("0000:03:00.0")
    assert missing == {"unavailable": "nvidia-smi has no row for PCI bus 0000:03:00.0"}


def test_proxy_is_the_s3_block_mean() -> None:
    from clearwater.gui.imaging import downscale, statistics_factor

    for shape in ((1080, 1920), (1081, 1923), (500, 700)):
        frame = np.random.default_rng(1).random((*shape, 3), dtype=np.float32)
        expected = downscale(frame, statistics_factor(*shape))
        assert core_speed.proxy_of(frame).tobytes() == expected.tobytes()
    assert core_speed.proxy_of(np.zeros((2160, 3840, 3), np.float32)).shape == (540, 960, 3)


def test_the_bar_is_d106_at_29_97_fps() -> None:
    """Both instruments label their figures with the spec's current N6 target (DR-119 e)."""
    spec = Path(__file__).resolve().parents[1] / "docs" / "underwater-correction-spec.md"
    prefix = "- **N6 Performance target (D106):**"
    line = next(
        (line for line in spec.read_text(encoding="utf-8").splitlines() if line.startswith(prefix)),
        None,
    )
    assert line is not None, f"N6 spec line not found; expected prefix: {prefix}"
    match = re.search(r"at most about ([0-9.]+) minutes", line)
    assert match is not None
    target = float(match.group(1))
    assert target == core_speed.D106_MINUTES_PER_MINUTE
    import export_bench

    assert target == export_bench.D106_MIN_PER_MIN
    assert pytest.approx(target / (30000 / 1001)) == core_speed.D106_SECONDS_PER_FRAME
    assert core_speed.minutes_per_minute(core_speed.D106_SECONDS_PER_FRAME) == pytest.approx(target)
    assert core_speed.minutes_per_minute(1.0) == pytest.approx(30000 / 1001)


def test_render_uploads_counted_and_the_backend_restored() -> None:
    from clearwater.methods import available_methods

    backend = clearwater.core.backend_for("cpu")
    frame = np.random.default_rng(2).random((40, 60, 3), dtype=np.float32)
    image = core_speed.as_image(backend, backend.asarray(frame))
    counts = {}
    for method_id, method in available_methods().items():
        records, seconds = core_speed.analyze_timed(method, image, lambda: None)
        assert list(seconds) == [stage.name for stage in method.stages]
        counts[method_id] = core_speed.count_render_uploads(method, image, records)
    # white-balance gains 1, saliency references 2, and c3's YCbCr inverse 1 (DR-40 b)
    assert counts == {"c3": 4, "ancuti2018": 3}
    assert "asarray" not in vars(backend)


def test_run_whole_keys_and_record(monkeypatch: pytest.MonkeyPatch) -> None:
    frames = [np.random.default_rng(i).random((60, 90, 3), dtype=np.float32) for i in range(3)]

    def decode(clip: Any, wanted: Any) -> Any:
        yield from ((index, frames[index]) for index in wanted)

    monkeypatch.setattr(core_speed, "decode", decode)
    monkeypatch.setattr(core_speed, "conditions", lambda moment, bus_id=None: {"moment": moment})
    clip = core_speed.ClipInfo(core_speed.Path("clip.mp4"), 90, 60, 3)
    record: dict[str, Any] = {"during": []}
    times = core_speed.run_whole(
        clip, clearwater.core.backend_for("cpu"), [0, 1, 2], 1, record, None
    )
    for method in core_speed.METHODS:
        for part in ("analyze", "render", "core", "prototype correct"):
            assert len(times[f"{method} {part}"]) == 2, (method, part)  # the warm-up dropped
        core_row = times[f"{method} core"]
        both = zip(times[f"{method} analyze"], times[f"{method} render"], strict=True)
        assert core_row == [a + r for a, r in both]
    assert len(times["c3 analyze fusion"]) == 2 and "c3 analyze compensation" not in times
    assert len(times["ancuti2018 analyze compensation"]) == 2
    assert record["render_uploads"] == {"cpu": {"c3": 4, "ancuti2018": 3}}
    assert record["three_value_upload"]["cpu"]["n"] == 200
    assert len(record["during"]) == 3


def test_fit_frame_pads_by_reflection() -> None:
    frame = np.arange(4 * 6 * 3, dtype=np.float32).reshape(4, 6, 3)
    out = core_speed.fit_frame(frame, 6, 8)
    assert out.shape == (6, 8, 3) and out.flags.c_contiguous
    assert np.array_equal(out[:4, :6], frame)
    assert np.array_equal(out[4, :6], frame[2]) and np.array_equal(out[:4, 6], frame[:, 4])
    assert core_speed.fit_frame(frame, 2, 3).shape == (2, 3, 3)


@pytest.mark.gpu
def test_pool_tracker_sees_an_allocation() -> None:
    from clearwater.core.backend import _probe_gpu

    gpu, reason = _probe_gpu()
    if gpu is None:
        pytest.skip(reason)
    import cupy

    tracker = core_speed.PoolTracker(cupy)
    try:
        block = cupy.zeros(1 << 20, dtype=cupy.float32)  # 4 MiB
        del block
    finally:
        tracker.close()
    assert tracker.peak_used >= 4 << 20 and tracker.peak_reserved >= tracker.peak_used
