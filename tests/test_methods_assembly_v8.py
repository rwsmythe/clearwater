"""WP3.4: V8 at method level -- the preview against the downscaled export (AD-11 as amended).

AD-11 (amended 2026-10-21, CHARC): k = 1 is EXACT; for k > 1 on real-sized content (at least
1080p) the mean absolute difference is within 1/255 and the 99th percentile within 2/255 at
k = 2 and 4/255 at k = 4. The 99.9th percentile and the maximum are characterisation (the
report's table), never asserted. Small stills and synthetic noise are outside V8's domain.

The content is the two centre 1080 x 1920 crops of the GX011625 look-check frames the round-0
figures were measured on (the working folder's ``wp1.3/frames``; the test skips without them).
Both renders use the crop's own statistics (AD-4: the same records for preview and export) and
the preview's own path, ``clearwater.gui.imaging``'s ``downscale`` and ``render_host``.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import numpy as np
import pytest

from clearwater.core import CoreBackend, NumpyBackend
from clearwater.core.backend import _probe_gpu
from clearwater.gui.imaging import downscale, preview_export_difference, render_host
from clearwater.interfaces.image import Image
from local_config import load_local_config
from lookcheck.frames import read_png16
from test_methods_assembly import COLOR, analyze_all, as_image, method

FRAMES = ("GX011625_0024.925", "GX011625_0114.648")
METHOD_IDS = ("c3", "ancuti2018")
MEAN_BOUND = 1.0 / 255.0
P99_BOUND = {2: 2.0 / 255.0, 4: 4.0 / 255.0}


def crop(stem: str) -> np.ndarray:
    """The centre 1080 x 1920 crop of a look-check frame, or skip when it is absent."""
    try:
        frames = load_local_config().working_path / "wp1.3" / "frames"
    except Exception as exc:  # no local configuration: the frames cannot be found
        pytest.skip(f"no local configuration: {exc}")
    path = Path(frames) / f"{stem}.png"
    if not path.is_file():
        pytest.skip(f"look-check frame absent: {path}")
    frame = read_png16(path)
    top, left = frame.shape[0] // 2 - 540, frame.shape[1] // 2 - 960
    return np.ascontiguousarray(frame[top : top + 1080, left : left + 1920])


def differences(
    m: object, backend: CoreBackend, pixels: np.ndarray, stats: object
) -> dict[int, np.ndarray]:
    """|preview - downscaled export| per k, float64, in [0, 1] units."""
    export = render_host(m, backend, pixels, COLOR, {}, stats)  # type: ignore[arg-type]
    out = {}
    for k in (1, 2, 4):
        preview = render_host(m, backend, downscale(pixels, k), COLOR, {}, stats)  # type: ignore[arg-type]
        out[k] = np.abs(preview.astype(np.float64) - downscale(export, k).astype(np.float64))
    return out


def check_v8(diffs: dict[int, np.ndarray]) -> None:
    assert float(diffs[1].max()) == 0.0, "k = 1 is exact"
    for k in (2, 4):
        mean = float(diffs[k].mean())
        p99 = float(np.percentile(diffs[k], 99.0))
        assert mean <= MEAN_BOUND, (k, mean * 255)
        assert p99 <= P99_BOUND[k], (k, p99 * 255)


def backend_named(device: str) -> CoreBackend:
    if device == "numpy":
        return NumpyBackend()
    gpu, reason = _probe_gpu()
    if gpu is None:
        pytest.skip(reason)
    return gpu


DEVICES = [
    pytest.param("numpy", marks=pytest.mark.slow, id="cpu"),
    pytest.param("cupy", marks=pytest.mark.gpu, id="gpu"),
]


@pytest.mark.parametrize("device", DEVICES)
@pytest.mark.parametrize("method_id", METHOD_IDS)
@pytest.mark.parametrize("stem", FRAMES)
def test_v8_preview_against_the_downscaled_export(stem: str, method_id: str, device: str) -> None:
    backend = backend_named(device)
    pixels = crop(stem)
    m = method(method_id)
    stats = analyze_all(m, as_image(pixels, backend), {})
    diffs = differences(m, backend, pixels, stats)
    check_v8(diffs)
    # the GUI's own V8 harness gives the same figures at k = 2
    host_image = Image(pixels=pixels, device="cpu", color=COLOR, orientation_applied=True)
    harness = preview_export_difference(m, backend, host_image, {}, stats, 2)
    assert harness.mean_abs == pytest.approx(float(diffs[2].mean()), rel=1e-12)
    assert harness.max_abs == float(diffs[2].max())


@pytest.mark.slow
def test_v8_planted_range_error_fails() -> None:
    """V8 distinguishes: a preview read as limited range misses the mean bound."""
    pixels = crop(FRAMES[0])
    backend = NumpyBackend()
    m = method("c3")
    stats = analyze_all(m, as_image(pixels, backend), {})
    diffs = differences(m, backend, pixels, stats)
    check_v8(diffs)
    export = render_host(m, backend, pixels, COLOR, {}, stats)
    wrong: Callable[[np.ndarray], np.ndarray] = lambda a: (a * 219.0 + 16.0) / 255.0  # noqa: E731
    planted = dict(diffs)
    for k in (2, 4):
        preview = render_host(m, backend, downscale(pixels, k), COLOR, {}, stats)
        planted[k] = np.abs(wrong(preview.astype(np.float64)) - downscale(export, k))
    with pytest.raises(AssertionError):
        check_v8(planted)
