"""WP4.1 V8 legs through the composition root and the runner (question 7; AD-11 as amended).

(a) The statistics the root's photo job measures equal ``gui.imaging.measure_statistics`` on the
image ``default_engines()`` reads, bit for bit (the 540 block-mean basis, WP3.16 Q5). (b) k = 1
is EXACT: ``render_host`` at k = 1 equals the job's pre-write pixels bit for bit, and the written
16-bit PNG equals them within half a 16-bit step. (c) k > 1 on real-sized content: the centre
1080 x 1920 crop of a WP1.3 look-check frame (the working folder's ``wp1.3/frames``; skipped
without them), exported through the runner, preview against the downscaled output: mean <=
1/255, p99 <= 2/255 at k = 2 and <= 4/255 at k = 4; p99.9 and max recorded, never asserted.
``gui.imaging`` imports PySide6, so every leg is ``gui``; (c) is also ``slow``. The leg through
the running shell is WP4.3's. Each leg has a planted control.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import headless_export as he
import numpy as np
import pytest
from test_wp41_photo_path import Recording, export, only_output

from clearwater.app import composition
from clearwater.core import backend_for
from clearwater.interfaces import ColorDescription, Image, PhotoMetadata
from clearwater.io.photo import PhotoReader
from clearwater.jobs import effective_parameters

pytestmark = pytest.mark.gui

FRAMES = ("GX011625_0024.925", "GX011625_0114.648")
"""The look-check frames ``tests/test_methods_assembly_v8.py`` reads."""

MEAN_BOUND = 1.0 / 255.0
P99_BOUND = {2: 2.0 / 255.0, 4: 4.0 / 255.0}
HALF_STEP_16 = 0.5 / 65535.0
BT709_16 = ColorDescription("bt709", "bt709", "bt709", "full", 16, False, None)


class RecordingMethod:
    """An IF-3 method that delegates to a real one and keeps the statistics it measured."""

    def __init__(self, inner: Any) -> None:
        self.inner = inner
        self.id = inner.id
        self.parameters = inner.parameters
        self.stages = inner.stages
        self.measured: dict[str, Any] = {}

    def analyze(self, stage: str, proxy: Image, params: Any, earlier: Any) -> Any:
        result = self.inner.analyze(stage, proxy, params, earlier)
        self.measured[stage] = result
        return result

    def render(self, image: Image, params: Any, statistics: Any) -> Image:
        return self.inner.render(image, params, statistics)


def equal_statistics(got: Any, expected: Any) -> bool:
    """Bit-for-bit equality of nested statistics (arrays compared exactly)."""
    if isinstance(expected, dict):
        return (
            isinstance(got, dict)
            and set(got) == set(expected)
            and all(equal_statistics(got[k], expected[k]) for k in expected)
        )
    if isinstance(expected, list | tuple):
        return len(got) == len(expected) and all(
            equal_statistics(a, b) for a, b in zip(got, expected, strict=True)
        )
    if isinstance(expected, np.ndarray) or isinstance(got, np.ndarray):
        a, b = np.asarray(got), np.asarray(expected)
        return a.dtype == b.dtype and a.shape == b.shape and bool(np.array_equal(a, b))
    return bool(got == expected)


def large_png(folder: Path) -> Path:
    """A 1131 x 1700 16-bit PNG (proxy factor 2, a partial last block row) under ``folder``."""
    rng = np.random.default_rng(14)
    pixels = rng.uniform(0.05, 0.95, (1131, 1700, 3)).astype(np.float32)
    pixels[..., 0] *= 0.4
    path = folder / "large.png"
    composition.photo_writer().write(
        Image(pixels, "cpu", BT709_16, True), PhotoMetadata("png", None, 1), path,
        bit_depth=16, provenance=None,
    )  # fmt: skip
    return path


def _source(sample, tmp_path: Path, sample_id: str) -> Path:
    if sample_id == "large":
        folder = tmp_path / "src"
        folder.mkdir()
        return large_png(folder)
    return sample(sample_id)


def _preview_inputs(source: Path) -> tuple[Any, Image, dict[str, Any], dict[str, Any]]:
    """What the GUI preview uses: ``default_engines()``'s reader and method, its statistics."""
    from clearwater.gui.engines import default_engines
    from clearwater.gui.imaging import measure_statistics

    engines = default_engines()
    c3 = engines.methods["c3"]
    image, _ = engines.photo_source.read(source)
    params = effective_parameters(c3, he.parameters_for())
    return c3, image, params, measure_statistics(c3, backend_for("cpu"), image, params)


@pytest.mark.parametrize("sample_id", ["jpeg-gradient-srgb", "heic10-gradient-display-p3", "large"])
def test_v8a_job_statistics_equal_the_previews(sample, tmp_path: Path, sample_id: str) -> None:
    source = _source(sample, tmp_path, sample_id)
    recording = RecordingMethod(composition.correction_methods()["c3"])
    out = tmp_path / "out"
    out.mkdir()
    only_output(export([source], out, exports=composition.export_jobs(methods={"c3": recording})))
    c3, image, params, expected = _preview_inputs(source)
    assert list(recording.measured) == [stage.name for stage in c3.stages]
    assert equal_statistics(recording.measured, expected)
    if sample_id == "large":  # planted: statistics of the full image, not the 540 proxy
        full: dict[str, Any] = {}
        for stage in c3.stages:
            full[stage.name] = c3.analyze(stage.name, image, params, dict(full))
        assert not equal_statistics(recording.measured, full)


class OneStepOff(Recording):
    """Planted writer double: records, then writes with one sample raised by one 16-bit step."""

    def write(self, image, meta, out_path, *, bit_depth, provenance) -> None:  # noqa: D102
        pixels = np.array(image.pixels, dtype=np.float32, copy=True)
        pixels[0, 0, 0] = min(1.0, pixels[0, 0, 0] + 1.0 / 65535.0)
        changed = Image(pixels, image.device, image.color, image.orientation_applied)
        super().write(changed, meta, out_path, bit_depth=bit_depth, provenance=provenance)


def _k1(source: Path, out: Path, writer: Recording) -> tuple[np.ndarray, np.ndarray, Path]:
    """Export ``source`` at 16 bit through ``writer``; return preview, pre-write and output."""
    from clearwater.gui.imaging import render_host

    output = only_output(
        export([source], out, exports=composition.export_jobs(writer=writer), png_bit_depth=16)
    )
    c3, image, params, statistics = _preview_inputs(source)
    preview = render_host(c3, backend_for("cpu"), image.pixels, image.color, params, statistics)
    return preview, writer.pixels[0], output


def _within_half_step(written: Path, reference: np.ndarray) -> bool:
    pixels, _ = PhotoReader().read(written)
    diff = np.abs(pixels.pixels.astype(np.float64) - reference.astype(np.float64))
    return float(diff.max()) <= HALF_STEP_16 * (1 + 1e-6)


@pytest.mark.parametrize("sample_id", ["jpeg-gradient-srgb", "png16-lowred-srgb", "large"])
def test_v8b_k1_is_exact(sample, tmp_path: Path, sample_id: str) -> None:
    source = _source(sample, tmp_path, sample_id)
    out = tmp_path / "out"
    out.mkdir()
    preview, written_pixels, output = _k1(source, out, Recording())
    assert preview.dtype == written_pixels.dtype and np.array_equal(preview, written_pixels)
    assert _within_half_step(output, preview)


def test_v8b_planted_one_step_off_fails(sample, tmp_path: Path) -> None:
    out = tmp_path / "out"
    out.mkdir()
    preview, _, output = _k1(sample("png16-lowred-srgb"), out, OneStepOff())
    assert not _within_half_step(output, preview)


def _crop(stem: str) -> np.ndarray:
    """The centre 1080 x 1920 crop of a look-check frame, or skip when it is absent."""
    from local_config import load_local_config
    from lookcheck.frames import read_png16

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


def _v8c_figures(preview: np.ndarray, export_down: np.ndarray) -> dict[str, float]:
    diff = np.abs(preview.astype(np.float64) - export_down.astype(np.float64))
    return {
        "mean": float(diff.mean()),
        "p99": float(np.percentile(diff, 99.0)),
        "p99.9": float(np.percentile(diff, 99.9)),
        "max": float(diff.max()),
    }


def _within_v8(figures: dict[str, float], k: int) -> bool:
    return figures["mean"] <= MEAN_BOUND and figures["p99"] <= P99_BOUND[k]


@pytest.mark.slow
def test_v8c_k_above_1_on_real_sized_content(tmp_path: Path, record_property) -> None:
    from clearwater.gui.imaging import downscale, measure_statistics, render_host

    crops = [_crop(stem) for stem in FRAMES]
    src = tmp_path / "src"
    src.mkdir()
    sources = []
    for stem, pixels in zip(FRAMES, crops, strict=True):
        path = src / f"{stem.replace('.', '_')}.png"
        composition.photo_writer().write(
            Image(pixels.astype(np.float32), "cpu", BT709_16, True), PhotoMetadata("png", None, 1),
            path, bit_depth=16, provenance=None,
        )  # fmt: skip
        sources.append(path)
    out = tmp_path / "out"
    out.mkdir()
    items = export(sources, out, png_bit_depth=16)
    assert [item.state for item in items] == ["done", "done"]
    cpu = backend_for("cpu")
    c3 = composition.correction_methods()["c3"]
    params = effective_parameters(c3, he.parameters_for())
    images = [PhotoReader().read(path)[0] for path in sources]
    stats = [measure_statistics(c3, cpu, image, params) for image in images]
    written = [PhotoReader().read(item.result.outputs[0])[0].pixels for item in items]
    for index, (image, statistics, output) in enumerate(zip(images, stats, written, strict=True)):
        for k in (2, 4):
            preview = render_host(
                c3, cpu, downscale(image.pixels, k), image.color, params, statistics
            )
            figures = _v8c_figures(preview, downscale(output, k))
            record_property(f"v8c-{FRAMES[index]}-k{k}", {n: v * 255 for n, v in figures.items()})
            assert _within_v8(figures, k), (FRAMES[index], k, {n: v * 255 for n, v in figures.items()})
            # Planted: the preview rendered with the other frame's statistics misses the bound.
            other = render_host(
                c3, cpu, downscale(image.pixels, k), image.color, params, stats[1 - index]
            )
            assert not _within_v8(_v8c_figures(other, downscale(output, k)), k), (FRAMES[index], k)
