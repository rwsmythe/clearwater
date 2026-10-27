"""Photo export end to end (WP3.14 ladder items 3 and 9): the product reader, method and writer.

One WP2.3 sample of each still family goes through :class:`~clearwater.jobs.ExportEngine` to an
8- and a 16-bit PNG on the CPU backend. The statistics the job measures equal the preview's
(``clearwater.gui.imaging.measure_statistics``, AD-4, V8) bit for bit; provenance is present and
parseable when on and absent when off. The committed samples are read only; every output goes to
the test's temporary folder.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from PIL import Image as PILImage

from clearwater.interfaces import CorrectionMethod, Image, Settings, Stage, Statistics
from clearwater.interfaces.stubs import StubProgress
from clearwater.io.photo import PhotoReader
from clearwater.io.photo.png import PROVENANCE_KEYWORD
from clearwater.jobs import ExportEngine, effective_parameters
from clearwater.jobs.export_seam import ExportRequest
from test_jobs_export_support import parameter_set, product_engine

Sample = Callable[[str], Path]

FAMILIES = (
    "jpeg-gradient-srgb",
    "heic8-gradient-srgb",
    "heic10-gradient-display-p3",
    "png8-gradient-srgb",
    "png16-gradient-srgb",
    "tiff8-gradient-srgb",
    "jpeg-orient-port-o6",
)
"""One sample per WP2.3 still family, plus the rotated portrait (EXIF orientation 6)."""


def _settings(folder: Path, bit_depth: int, *, provenance: bool = True) -> Settings:
    return Settings(
        output_folder=folder, png_bit_depth=bit_depth, provenance=provenance, force_cpu=True
    )


def _export(
    engine: ExportEngine, source: Path, settings: Settings, method: str = "c3"
) -> tuple[Any, Path]:
    request = ExportRequest(source, "photo", parameter_set(method), settings)
    result = engine.job(request)(StubProgress())
    assert result.ok, result.failure
    assert len(result.outputs) == 1
    return result, result.outputs[0]


def _png_bit_depth(path: Path) -> int:
    data = path.read_bytes()
    assert data[12:16] == b"IHDR"
    return data[24]


def _provenance(path: Path) -> dict[str, Any] | None:
    with PILImage.open(path) as image:
        text = image.text.get(PROVENANCE_KEYWORD)
    return None if text is None else json.loads(text)


@pytest.mark.parametrize("bit_depth", [8, 16])
@pytest.mark.parametrize("sample_id", FAMILIES)
def test_each_still_family_exports_to_png(
    sample: Sample, tmp_path: Path, sample_id: str, bit_depth: int
) -> None:
    source = sample(sample_id)
    before = (source.read_bytes(), os.stat(source).st_mtime_ns)
    out_folder = tmp_path / "out"
    out_folder.mkdir()
    engine = product_engine(tmp_path / "cache")
    result, output = _export(engine, source, _settings(out_folder, bit_depth))

    assert output.parent == out_folder
    assert output.suffix == ".png"
    assert output.name.startswith(source.stem)
    assert sorted(p.name for p in out_folder.iterdir()) == [output.name]
    assert _png_bit_depth(output) == bit_depth
    image, _ = PhotoReader().read(source)
    with PILImage.open(output) as written:
        assert written.size == (image.pixels.shape[1], image.pixels.shape[0])
    assert result.device == "CPU: forced"
    assert (source.read_bytes(), os.stat(source).st_mtime_ns) == before  # N8

    provenance = _provenance(output)
    assert provenance is not None
    assert provenance["method"] == "c3"
    assert provenance["source"]["name"] == source.name
    assert provenance["source"]["width"] == image.pixels.shape[1]
    assert provenance["settings"] == {"png_bit_depth": bit_depth, "device": "CPU: forced"}
    assert str(source.parent) not in json.dumps(provenance)


def test_provenance_is_absent_when_off(sample: Sample, tmp_path: Path) -> None:
    source = sample("png8-gradient-srgb")
    engine = product_engine(tmp_path / "cache")
    _, output = _export(engine, source, _settings(tmp_path, 8, provenance=False))
    assert _provenance(output) is None


class _Recording:
    """A method wrapper recording what each stage's ``analyze`` returned (the job's statistics)."""

    def __init__(self, method: CorrectionMethod) -> None:
        self._method = method
        self.measured: dict[str, Statistics] = {}

    @property
    def id(self) -> str:
        return self._method.id

    @property
    def parameters(self) -> Any:
        return self._method.parameters

    @property
    def stages(self) -> tuple[Stage, ...]:
        return tuple(self._method.stages)

    def analyze(
        self, stage: str, image: Image, params: Mapping[str, Any], earlier: Mapping[str, Statistics]
    ) -> Statistics:
        result = self._method.analyze(stage, image, params, earlier)
        self.measured[stage] = result
        return result

    def render(
        self, image: Image, params: Mapping[str, Any], statistics: Mapping[str, Statistics]
    ) -> Image:
        return self._method.render(image, params, statistics)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._method, name)


def _assert_equal_statistics(
    got: Mapping[str, Statistics], expected: Mapping[str, Statistics]
) -> None:
    assert list(got) == list(expected)
    for stage, values in expected.items():
        assert sorted(got[stage]) == sorted(values), stage
        for key, array in values.items():
            a, b = np.asarray(got[stage][key]), np.asarray(array)
            assert a.dtype == b.dtype, (stage, key)
            assert a.shape == b.shape, (stage, key)
            assert np.array_equal(a, b, equal_nan=True), (stage, key)


def _large_png(folder: Path) -> Path:
    """Write a 1131 x 1700 16-bit PNG: proxy factor 2 with a partial last block row."""
    from clearwater.interfaces import PhotoMetadata
    from clearwater.io.photo import PhotoWriter
    from test_analysis_support import COLOR

    rng = np.random.default_rng(14)
    pixels = rng.uniform(0.05, 0.95, (1131, 1700, 3)).astype(np.float32)
    pixels[..., 0] *= 0.4  # an underwater-like red deficit
    path = folder / "large.png"
    PhotoWriter().write(
        Image(pixels, "cpu", COLOR, True), PhotoMetadata("png", None, 1), path,
        bit_depth=16, provenance=None,
    )  # fmt: skip
    return path


@pytest.mark.gui
@pytest.mark.parametrize("sample_id", ["jpeg-gradient-srgb", "heic10-gradient-display-p3", "large"])
def test_photo_statistics_equal_the_previews_bit_for_bit(
    sample: Sample, tmp_path: Path, sample_id: str
) -> None:
    from clearwater.analysis import proxy_factor
    from clearwater.core import backend_for
    from clearwater.gui.imaging import measure_statistics
    from clearwater.methods import available_methods

    source = _large_png(tmp_path) if sample_id == "large" else sample(sample_id)
    c3 = available_methods()["c3"]
    method = _Recording(c3)
    engine = product_engine(tmp_path / "cache", methods={"c3": method})
    out = tmp_path / "out"
    out.mkdir()
    _export(engine, source, _settings(out, 16))

    image, _ = PhotoReader().read(source)
    params = effective_parameters(c3, parameter_set("c3"))
    expected = measure_statistics(c3, backend_for("cpu"), image, params)
    _assert_equal_statistics(method.measured, expected)

    if sample_id == "large":
        assert proxy_factor(*image.pixels.shape[:2]) == 2
        # Control: statistics measured on the full image instead of the proxy are told apart.
        full: dict[str, Statistics] = {}
        for stage in c3.stages:
            full[stage.name] = c3.analyze(stage.name, image, params, dict(full))
        with pytest.raises(AssertionError):
            _assert_equal_statistics(method.measured, full)
