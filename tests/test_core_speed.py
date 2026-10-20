"""WP3.1: the speed-row instrument ``tools/core_speed.py`` without footage or a GPU."""

from __future__ import annotations

import subprocess
from collections import Counter
from collections.abc import Callable
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
