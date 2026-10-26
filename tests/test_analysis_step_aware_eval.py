"""The step-aware evaluation instrument (``tools/step_aware_eval.py``) on a synthetic step clip.

The footage run is the dispatcher-windowed one; this drives the same code on small synthetic
proxies with a lighting step, on the CPU, with the footage loader replaced.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from numpy.typing import NDArray

import step_aware_eval as tool
from prototype import temporal
from prototype.backend import select_backend
from prototype.clip import make_params


def _clip() -> tuple[NDArray[np.uint8], NDArray[np.int64], Fraction]:
    """240 frames at 30000/1001 of a textured still whose light turns bluer at frame 120."""
    rng = np.random.default_rng(8)
    base = rng.uniform(0.2, 0.7, size=(54, 96, 3))
    frames = []
    for index in range(240):
        tint = np.array([0.9, 1.0, 1.0]) if index < 120 else np.array([0.6, 1.1, 1.3])
        noisy = base * tint * (1 + rng.normal(0, 0.01))
        frames.append(np.clip(np.floor(noisy * 255 + 0.5), 0, 255).astype(np.uint8))
    ticks = (np.arange(240) * 1001).astype(np.int64)
    return np.stack(frames), ticks, Fraction(1, 30000)


def _use_synthetic_clip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> NDArray[np.uint8]:
    """Point the instrument at the synthetic clip; the "excerpt" is frames 90..149 (2 s).

    c3's reach (60) fits inside the span, Ancuti's (90) reaches the first frame from the
    excerpt's first.
    """
    proxies, ticks, time_base = _clip()

    class Config:
        footage_path = tmp_path / "footage"

    monkeypatch.setattr(tool, "load_local_config", lambda: Config())
    monkeypatch.setattr(tool, "load_proxies", lambda out, root, log: (proxies, ticks, time_base))
    monkeypatch.setattr(tool, "EXCERPT_START_S", Fraction(90 * 1001, 30000))
    monkeypatch.setattr(tool, "EXCERPT_DURATION_S", Fraction(60 * 1001, 30000))
    monkeypatch.setattr(tool, "AWAY_S", 0.5)
    return proxies


def test_the_instrument_runs_on_a_synthetic_step(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The record holds every method and kind; the edge-free count and the step are found."""
    _use_synthetic_clip(tmp_path, monkeypatch)
    lines: list[str] = []
    record: dict[str, Any] = tool.evaluate(tmp_path / "out", "cpu", lines.append)
    assert record["excerpt_frames"] == 60 and record["span_frames"] == 240
    assert record["step_index_in_excerpt"] == 30
    assert set(record["methods"]) == {"c3", "ancuti2018"}
    # Edge-free per kind (R1 F8): the step-aware kinds read the whole series, so none is.
    c3, ancuti = (record["methods"][m]["kinds"] for m in ("c3", "ancuti2018"))
    assert c3["median_gaussian"]["edge_free_frames"] == 60
    assert 0 < ancuti["median_gaussian"]["edge_free_frames"] < 60
    assert c3["median_gaussian"]["reach_frames"] == [60, 60]
    for kind in ("median_gaussian_cut", "median_bilateral"):
        assert c3[kind]["edge_free_frames"] == ancuti[kind]["edge_free_frames"] == 0
        assert c3[kind]["reach_frames"] == [90, 90]
    for data in record["methods"].values():
        assert set(data["kinds"]) == set(tool.KINDS)
        for figures in data["kinds"].values():
            assert figures["flicker_away_from_step"] >= 0.0
            assert figures["rendered_step"]["luma"]["change_over_source"] is not None
    assert (tmp_path / "out" / "step-aware.json").exists()
    text = tool.table(record)
    assert text.count("\n") == 1 + 2 * len(tool.KINDS)
    assert "median_gaussian_cut" in text


def test_the_flicker_reference_is_the_mean_of_the_own_raw_statistics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WP1.4b's flicker reference: the excerpt's own raw statistics, averaged (R1 F7)."""
    proxies = _use_synthetic_clip(tmp_path, monkeypatch)
    references: dict[str, Any] = {}
    render = tool.render_signals

    def spy(
        proxies: NDArray[np.uint8], indices: Any, method: str, statistics: Any, backend: Any
    ) -> NDArray[np.float64]:
        references.setdefault(method, (statistics(indices[0]), statistics(indices[-1])))
        return render(proxies, indices, method, statistics, backend)

    monkeypatch.setattr(tool, "render_signals", spy)
    tool.evaluate(tmp_path / "out", "cpu", lambda text: None)
    backend = select_backend("cpu")
    for method in tool.METHODS:
        params = make_params(method, neutral=False)
        images = [tool.image(proxies, i) for i in range(90, 150)]
        own_raw = temporal.stack([temporal.statistics_of(im, params, backend) for im in images])
        expected = temporal.stack([temporal.constant_statistics(own_raw)])
        first, last = (temporal.stack([record]) for record in references[method])
        assert set(first) == set(expected) == set(last)
        for name, values in expected.items():
            np.testing.assert_allclose(first[name], values, rtol=1e-9, atol=1e-12, err_msg=name)
            np.testing.assert_array_equal(first[name], last[name])


def test_default_output_is_the_worktree_work_folder() -> None:
    """Outputs go under ``work/wp3.11`` of this tree, never the footage folder."""
    out = tool.default_out()
    assert out.parts[-3:] == ("work", "wp3.11", "step-aware")
