"""WP3.12 tests: the run identity of the AD-5 measured-test instrument (cache_store_test)."""

from __future__ import annotations

import concurrent.futures
import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

import cache_store_test as instrument
import clearwater.cache.codec as codec_module


def make_clip(
    folder: Path, *, stride: int = 8, seed: int = 0, reference: float = 0.5
) -> instrument.ClipData:
    """Return a tiny prepared clip: three 4 x 6 frames in a proxy file under ``folder``."""
    raw = np.random.default_rng(seed).integers(0, 256, (3, 4, 6, 3), dtype=np.uint8)
    path = folder / "proxy-TINY.u8"
    path.write_bytes(raw.tobytes())
    frames = np.fromfile(path, dtype=np.uint8).reshape(3, 4, 6, 3)
    refs = {0: {"means": np.asarray([reference, 0.25])}, 2: {"means": np.asarray([reference])}}
    return instrument.ClipData("TINY", frames, [0, 2], refs, stride, path)


@pytest.fixture
def counted_jobs(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    """Replace the statistics job by one that counts its calls (and measures only the mean)."""
    calls: list[int] = []

    def job(frame: Any) -> dict[str, Any]:
        calls.append(1)
        return {"means": np.asarray([float(frame.mean())])}

    monkeypatch.setattr(instrument, "_stats_job", job)
    return calls


def baseline(clip: instrument.ClipData, out: Path) -> dict[int, Any]:
    """Run ``baseline_stats`` on a thread pool."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return instrument.baseline_stats(clip, out, pool)


def test_the_identity_names_the_stride_the_proxies_and_the_jpeg_library(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    same = instrument.run_identity([make_clip(tmp_path)])
    assert same == instrument.run_identity([make_clip(tmp_path)])
    assert same != instrument.run_identity([make_clip(tmp_path, stride=4)])
    assert same != instrument.run_identity([make_clip(tmp_path, seed=1)])
    # the float-reference statistics are part of it: same 8-bit proxies, other reference
    assert same != instrument.run_identity([make_clip(tmp_path, reference=0.75)])
    monkeypatch.setattr(codec_module, "jpeg_identity", lambda: "pillow=0;libjpeg=0;turbo=0")
    assert same != instrument.run_identity([make_clip(tmp_path)])


def test_a_baseline_is_reused_only_by_the_run_that_measured_it(
    tmp_path: Path, counted_jobs: list[int]
) -> None:
    first = baseline(make_clip(tmp_path), tmp_path)
    assert len(counted_jobs) == 2
    again = baseline(make_clip(tmp_path), tmp_path)
    assert len(counted_jobs) == 2  # reused, not measured again
    assert again[0]["means"].tolist() == first[0]["means"].tolist()
    for other in (make_clip(tmp_path, stride=4), make_clip(tmp_path, seed=1)):
        with pytest.raises(SystemExit, match="another run"):
            baseline(other, tmp_path)
    assert len(counted_jobs) == 2


def test_a_baseline_without_an_identity_is_refused(tmp_path: Path, counted_jobs: list[int]) -> None:
    legacy = {"0": {"means": [0.5]}, "2": {"means": [0.5]}}  # the form written before identities
    (tmp_path / "baseline-TINY.json").write_text(json.dumps(legacy), encoding="utf-8")
    with pytest.raises(SystemExit, match="no run identity"):
        baseline(make_clip(tmp_path), tmp_path)
    assert counted_jobs == []


def test_results_are_read_back_only_by_the_run_that_wrote_them(tmp_path: Path) -> None:
    path = tmp_path / "results.json"
    mine = instrument.run_identity([make_clip(tmp_path)])
    assert instrument.read_results(path, mine) == []  # nothing yet
    rows = [{"candidate": "x", "clip": "TINY"}]
    instrument.write_results(path, mine, rows)
    assert instrument.read_results(path, mine) == rows
    with pytest.raises(SystemExit, match="another run"):
        instrument.read_results(path, instrument.run_identity([make_clip(tmp_path, seed=1)]))
    path.write_text(json.dumps(rows), encoding="utf-8")  # the form written before identities
    with pytest.raises(SystemExit, match="no run identity"):
        instrument.read_results(path, mine)
