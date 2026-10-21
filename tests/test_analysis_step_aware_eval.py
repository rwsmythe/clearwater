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
import step_aware_eval as tool
from numpy.typing import NDArray


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


def test_the_instrument_runs_on_a_synthetic_step(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The record holds every method and kind; the edge-free count and the step are found."""
    proxies, ticks, time_base = _clip()

    class Config:
        footage_path = tmp_path / "footage"

    monkeypatch.setattr(tool, "load_local_config", lambda: Config())
    monkeypatch.setattr(tool, "load_proxies", lambda out, root, log: (proxies, ticks, time_base))
    # The "excerpt" is frames 90..149 (2 s): c3's reach (60) fits inside the span, Ancuti's (90)
    # reaches the first frame from the excerpt's first.
    monkeypatch.setattr(tool, "EXCERPT_START_S", Fraction(90 * 1001, 30000))
    monkeypatch.setattr(tool, "EXCERPT_DURATION_S", Fraction(60 * 1001, 30000))
    monkeypatch.setattr(tool, "AWAY_S", 0.5)
    lines: list[str] = []
    record: dict[str, Any] = tool.evaluate(tmp_path / "out", "cpu", lines.append)
    assert record["excerpt_frames"] == 60 and record["span_frames"] == 240
    assert record["step_index_in_excerpt"] == 30
    assert set(record["methods"]) == {"c3", "ancuti2018"}
    assert record["methods"]["c3"]["edge_free_frames"] == 60
    assert record["methods"]["ancuti2018"]["edge_free_frames"] < 60
    for data in record["methods"].values():
        assert set(data["kinds"]) == set(tool.KINDS)
        for figures in data["kinds"].values():
            assert figures["flicker_away_from_step"] >= 0.0
            assert figures["rendered_step"]["luma"]["change_over_source"] is not None
    assert (tmp_path / "out" / "step-aware.json").exists()
    text = tool.table(record)
    assert text.count("\n") == 1 + 2 * len(tool.KINDS)
    assert "median_gaussian_cut" in text


def test_default_output_is_the_worktree_work_folder() -> None:
    """Outputs go under ``work/wp3.11`` of this tree, never the footage folder."""
    out = tool.default_out()
    assert out.parts[-3:] == ("work", "wp3.11", "step-aware")
