"""Tests for the WP1.3D deep look check: the case scan (``lookcheck.scan``) and the ``deep``
command of ``lookcheck.pack``. Synthetic except where marked ``footage``."""

from __future__ import annotations

import dataclasses
import hashlib
import itertools
import json
import shutil
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from local_config import FootageLookupError, find_footage_file, load_local_config
from lookcheck import frames, pack, scan
from lookcheck.frames import OutputRoots
from prototype.backend import CPU
from prototype.params import Params

WIDTH, HEIGHT = 64, 48
TIME_BASE = Fraction(1, 30000)


def _flat(colour: tuple[float, float, float], width: int = WIDTH) -> np.ndarray[Any, Any]:
    """A uniform float32 frame of ``colour``."""
    return np.full((HEIGHT, width, 3), colour, dtype=np.float32)


def _luma(colour: tuple[float, float, float]) -> float:
    """BT.709 luma of a colour, computed by hand (the weights are written out here)."""
    return 0.2126 * colour[0] + 0.7152 * colour[1] + 0.0722 * colour[2]


# --- test 1: the measures ----------------------------------------------------------------------


def test_a_uniform_frame_has_the_hand_computed_measures() -> None:
    colour = (0.2, 0.4, 0.6)
    measures = scan.measure_frame(_flat(colour))
    assert measures.depth_index == pytest.approx(0.2 / 0.4, abs=1e-6)
    assert measures.open_water == 1.0  # flat, and blue exceeds red by 0.4
    assert measures.haze == pytest.approx(0.0, abs=1e-6)
    assert measures.luma_mean == pytest.approx(_luma(colour), abs=1e-6)


def test_a_half_flat_frame_has_the_water_fraction_the_box_geometry_gives() -> None:
    boundary = WIDTH // 2
    water = (0.2, 0.4, 0.6)
    image = _flat(water)
    rows, columns = np.indices((HEIGHT, WIDTH - boundary))
    checker = ((rows + columns) % 2).astype(np.float32)  # black and white squares
    image[:, boundary:] = checker[..., None]
    measures = scan.measure_frame(image)
    # A pixel is flat only when its 15x15 box lies in the left half: columns 0 .. boundary - 8.
    assert measures.open_water == pytest.approx((boundary - 7) / WIDTH, abs=1e-9)
    left, right = _luma(water), 0.5
    mean = (left + right) / 2
    variance = (left**2 + 0.5) / 2 - mean**2  # the checker's luma is 0 or 1: E[x^2] = 0.5
    assert measures.haze == pytest.approx(variance**0.5, abs=1e-5)
    # D from the raw channel means: R = (0.2 + 0.5) / 2, G = (0.4 + 0.5) / 2.
    assert measures.depth_index == pytest.approx(0.35 / 0.45, abs=1e-5)


def test_a_known_contrast_frame_has_that_luma_contrast() -> None:
    image = _flat((0.25, 0.25, 0.25))
    image[:, WIDTH // 2 :] = 0.75
    measures = scan.measure_frame(image)
    assert measures.haze == pytest.approx(0.25, abs=1e-6)
    assert measures.open_water == 0.0  # gray: neither blue nor green exceeds red
    assert measures.depth_index == pytest.approx(1.0, abs=1e-6)


@pytest.mark.parametrize(("margin", "expected"), [(0.04, 0.0), (0.06, 1.0)])
def test_the_water_colour_condition_is_a_margin_of_five_hundredths(
    margin: float, expected: float
) -> None:
    assert scan.measure_frame(_flat((0.3, 0.3, 0.3 + margin))).open_water == expected
    assert scan.measure_frame(_flat((0.3, 0.3 + margin, 0.3))).open_water == expected


def test_a_flat_dark_rock_is_not_open_water() -> None:
    rock = _flat((0.40, 0.30, 0.20))  # flat, but red exceeds both blue and green
    assert scan.measure_frame(rock).open_water == 0.0


def test_the_local_std_of_a_two_valued_plane_matches_a_brute_force_box() -> None:
    rng = np.random.default_rng(3)
    plane = rng.random((20, 24))
    got = scan.local_std(plane, 5)
    padded = np.pad(plane, 2, mode="symmetric")  # scipy's "reflect" repeats the edge sample
    expected = np.empty_like(plane)
    for row in range(plane.shape[0]):
        for column in range(plane.shape[1]):
            expected[row, column] = padded[row : row + 5, column : column + 5].std()
    assert np.allclose(got, expected, atol=1e-12)


def test_the_scan_timestamps_run_every_ten_seconds_from_five_to_the_end() -> None:
    assert scan.scan_timestamps(4.0) == []
    assert scan.scan_timestamps(25.0) == [5.0, 15.0]
    assert scan.scan_timestamps(26.0) == [5.0, 15.0, 25.0]
    # a grid point in the last second is kept (GX011598 is 525.3248 s long: 525.0 s is on the grid)
    assert scan.scan_timestamps(525.3248)[-1] == 525.0
    assert scan.scan_timestamps(25.1) == [5.0, 15.0]  # but not one with under a quarter second left


# --- test 2: the exclusion rule -----------------------------------------------------------------


def test_a_near_black_frame_is_excluded_by_name_and_never_ranked() -> None:
    black = scan.scan_record("GXBLACK", 5.0, 150150, TIME_BASE, _flat((0.01, 0.02, 0.03)))
    bright = scan.scan_record("GXBRIGHT", 5.0, 150150, TIME_BASE, _flat((0.98, 0.99, 0.99)))
    fine = scan.scan_record("GXFINE", 5.0, 150150, TIME_BASE, _flat((0.2, 0.4, 0.6)))
    assert black.excluded is not None and "below 0.05" in black.excluded
    assert bright.excluded is not None and "above 0.95" in bright.excluded
    assert fine.excluded is None
    assert black.frame == "GXBLACK_0005.005"
    for case in scan.CASES:
        names = [record.frame for record in scan.ranked([black, bright, fine], case)]
        # the flat blue frame is open water (W = 1), so it is no distance haze candidate
        assert names == ([] if case.name == "distance-haze" else [fine.frame]), case.name
    document = scan.scan_document([black, bright, fine], {}, "now")
    assert {entry["frame"] for entry in document["excluded"]} == {black.frame, bright.frame}
    reasons = {entry["frame"]: entry["reason"] for entry in document["excluded"]}
    assert reasons[black.frame] == black.excluded


def test_a_frame_with_no_green_is_excluded_not_a_division_by_zero() -> None:
    record = scan.scan_record("GXRED", 5.0, 150150, TIME_BASE, _flat((0.9, 0.0, 0.0)))
    assert record.excluded is not None and "green" in record.excluded
    assert record.measures.depth_index is None
    assert json.dumps(record.record(), allow_nan=False)


# --- test 3: the candidate picker ---------------------------------------------------------------


def _rec(
    chapter: str,
    grid_s: float,
    *,
    depth: float = 0.8,
    water: float = 0.0,
    haze: float = 0.2,
    excluded: str | None = None,
) -> scan.ScanRecord:
    """A constructed scan record (the pts follows the grid by one frame period)."""
    ticks = round((grid_s + 0.0334) * 30000)
    return scan.ScanRecord(
        chapter=chapter,
        frame=frames.frame_stem(chapter, float(ticks * TIME_BASE)),
        grid_s=grid_s,
        pts_ticks=ticks,
        time_base=TIME_BASE,
        measures=scan.Measures(0.4, depth, water, haze),
        excluded=excluded,
    )


def _names(records: list[scan.ScanRecord]) -> list[tuple[str, float]]:
    return [(r.chapter, r.grid_s) for r in records]


def test_the_picker_honours_the_per_chapter_limit_and_the_spacing() -> None:
    order = [
        _rec("A", 5.0, depth=0.10),
        _rec("A", 15.0, depth=0.11),  # 10 s from A@5: too close
        _rec("A", 35.0, depth=0.12),  # exactly 30 s from A@5: allowed
        _rec("A", 95.0, depth=0.13),  # a third of chapter A: over the limit
        _rec("B", 5.0, depth=0.14),  # chapter B has its own clock
        _rec("B", 25.0, depth=0.15),  # 20 s from B@5: too close
        _rec("B", 55.0, depth=0.16),
    ]
    got = scan.pick(order, 4, scan.CASE_MIN_SEPARATION_S, scan.CASE_PER_CHAPTER)
    assert _names(got) == [("A", 5.0), ("A", 35.0), ("B", 5.0), ("B", 55.0)]
    only_two = scan.pick(order, 2, scan.CASE_MIN_SEPARATION_S, scan.CASE_PER_CHAPTER)
    assert _names(only_two) == [("A", 5.0), ("A", 35.0)]
    unlimited = scan.pick(order, 8, 10.0, None)
    assert _names(unlimited) == [
        ("A", 5.0),
        ("A", 15.0),
        ("A", 35.0),
        ("A", 95.0),
        ("B", 5.0),
        ("B", 25.0),
        ("B", 55.0),
    ]


def test_ties_break_by_chapter_name_then_pts_in_both_directions() -> None:
    records = [
        _rec("B", 5.0, depth=0.3, water=0.7),
        _rec("A", 65.0, depth=0.3, water=0.7),
        _rec("A", 5.0, depth=0.3, water=0.7),
        _rec("A", 25.0, depth=0.1, water=0.9),
    ]
    deep_case, water_case, _haze_case = scan.CASES
    for case, first in ((deep_case, ("A", 25.0)), (water_case, ("A", 25.0))):
        got = scan.ranked(records, case)
        assert _names(got) == [first, ("A", 5.0), ("A", 65.0), ("B", 5.0)], case.name
    reverse = scan.ranked(list(reversed(records)), water_case)
    assert _names(reverse) == _names(scan.ranked(records, water_case))  # input order is irrelevant


def test_the_cases_rank_by_their_measures() -> None:
    deep_case, water_case, haze_case = scan.CASES
    records = [
        _rec("A", 5.0, depth=0.9, water=0.2, haze=0.30),
        _rec("A", 15.0, depth=0.5, water=0.9, haze=0.05),  # open water: not a haze candidate
        _rec("B", 5.0, depth=0.7, water=0.6, haze=0.10),  # W = 0.6 is not below 0.5
        _rec("B", 15.0, depth=0.6, water=0.4, haze=0.08),
        _rec("C", 5.0, depth=0.1, water=0.99, haze=0.01, excluded="luma mean 0.01 is below 0.05"),
    ]
    assert _names(scan.ranked(records, deep_case)) == [
        ("A", 15.0),
        ("B", 15.0),
        ("B", 5.0),
        ("A", 5.0),
    ]
    assert _names(scan.ranked(records, water_case)) == [
        ("A", 15.0),
        ("B", 5.0),
        ("B", 15.0),
        ("A", 5.0),
    ]
    assert _names(scan.ranked(records, haze_case)) == [("B", 15.0), ("A", 5.0)]


def test_a_case_with_too_few_eligible_frames_is_an_error_not_a_lower_bar() -> None:
    records = [
        _rec(chapter, 5.0 + 10.0 * k, depth=0.3 + 0.01 * k, water=0.9)  # all open water
        for chapter in ("A", "B", "C", "D")
        for k in range(12)
    ]
    with pytest.raises(scan.ScanError, match="distance-haze"):
        scan.select_candidates(records)


# --- test 4: deep-frames.json -------------------------------------------------------------------


def _ranking_records() -> list[scan.ScanRecord]:
    """Four chapters of 12 frames each, built so that every case has a clear order."""
    out = []
    for number, chapter in enumerate(("GXA", "GXB", "GXC", "GXD")):
        for step in range(12):
            out.append(
                _rec(
                    chapter,
                    5.0 + 10.0 * step,
                    depth=0.2 + 0.01 * number + 0.05 * step,
                    water=(0.3 + 0.01 * step) if step % 2 else 0.9 - 0.01 * number,
                    haze=0.1 + 0.01 * step + 0.001 * number,
                )
            )
    return out


def test_deep_frames_json_has_the_documented_keys_and_ordering() -> None:
    records = _ranking_records()
    document = scan.deep_frames_document(records, "2026-10-19T00:00:00+00:00")
    assert list(document) == ["schema", "spec", "written", "note", "rules", "cases", "deepest"]
    assert document["spec"] == "0.5.3" and "CANDIDATES" in document["note"]
    assert list(document["cases"]) == ["deep-water-noise", "open-blue-water", "distance-haze"]
    entry_keys = [
        "rank",
        "chapter",
        "frame",
        "pts_ticks",
        "time_base",
        "pts_seconds",
        "grid_s",
        "D",
        "W",
        "H",
        "luma_mean",
        "serves_cases",
    ]
    for body in document["cases"].values():
        assert list(body) == ["label", "rule", "frames"]
        assert [e["rank"] for e in body["frames"]] == [1, 2, 3, 4]
        assert all(list(e) == entry_keys for e in body["frames"])
    deep = document["cases"]["deep-water-noise"]["frames"]
    assert [e["D"] for e in deep] == sorted(e["D"] for e in deep)
    water = document["cases"]["open-blue-water"]["frames"]
    assert [e["W"] for e in water] == sorted((e["W"] for e in water), reverse=True)
    assert all(e["W"] < 0.5 for e in document["cases"]["distance-haze"]["frames"])
    haze = document["cases"]["distance-haze"]["frames"]
    assert [e["H"] for e in haze] == sorted(e["H"] for e in haze)
    assert len(document["deepest"]) == 8
    assert all(list(e) == entry_keys for e in document["deepest"])
    assert [e["D"] for e in document["deepest"]] == sorted(e["D"] for e in document["deepest"])
    # the first frame of the deepest list is the first deep-water noise candidate
    assert document["deepest"][0]["frame"] == deep[0]["frame"]
    assert json.dumps(document, allow_nan=False)


def test_a_frame_serving_two_cases_says_so_in_both_entries() -> None:
    records = [
        _rec("A", 5.0, depth=0.1, water=0.9, haze=0.30),  # best deep and best water at once
        *[
            _rec("A", 5.0 + 60.0 * k, depth=0.5 + k * 0.01, water=0.1, haze=0.2)
            for k in range(1, 4)
        ],
        *[_rec("B", 5.0 + 60.0 * k, depth=0.7 + k * 0.01, water=0.8, haze=0.2) for k in range(4)],
        *[_rec("C", 5.0 + 60.0 * k, depth=0.9 + k * 0.01, water=0.1, haze=0.1) for k in range(4)],
    ]
    document = scan.deep_frames_document(records, "now")
    first_deep = document["cases"]["deep-water-noise"]["frames"][0]
    first_water = document["cases"]["open-blue-water"]["frames"][0]
    assert first_deep["frame"] == first_water["frame"] == records[0].frame
    assert first_deep["serves_cases"] == ["deep-water-noise", "open-blue-water"]
    assert first_water["serves_cases"] == ["deep-water-noise", "open-blue-water"]
    assert document["deepest"][0]["serves_cases"] == ["deep-water-noise", "open-blue-water"]


def test_the_deepest_list_has_a_ten_second_rule_and_no_per_chapter_limit() -> None:
    records = [_rec("A", 5.0 + 10.0 * k, depth=0.1 + 0.01 * k) for k in range(10)]
    got = scan.deepest_frames(records)
    assert _names(got) == [("A", 5.0 + 10.0 * k) for k in range(8)]
    with pytest.raises(scan.ScanError):
        scan.deepest_frames(records[:7])


def test_the_water_histogram_counts_only_the_frames_that_take_part() -> None:
    records = [
        _rec("A", 5.0, water=0.0),
        _rec("A", 15.0, water=0.05),
        _rec("A", 25.0, water=0.95),
        _rec("A", 35.0, water=1.0),
        _rec("A", 45.0, water=0.5, excluded="luma mean 0.99 is above 0.95"),
    ]
    histogram = scan.water_histogram(records)
    assert histogram["frames"] == 4
    assert histogram["counts"] == [2, 0, 0, 0, 0, 0, 0, 0, 0, 2]
    assert histogram["bins"][:3] == [0.0, 0.1, 0.2]


def test_the_scan_record_survives_the_cache_round_trip() -> None:
    record = _rec("GXA", 15.0, depth=0.42, water=0.25, haze=0.07)
    again = scan.ScanRecord.from_record(json.loads(json.dumps(record.record())))
    assert again == record


# --- test 7: the footage smoke test ---------------------------------------------------------------


@pytest.mark.footage
def test_the_scan_runs_on_one_deep_chapter_at_three_timestamps(tmp_path: Path) -> None:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        pytest.skip("ffmpeg/ffprobe not on PATH")
    config = load_local_config()
    try:
        chapter = find_footage_file(scan.SCAN_CHAPTERS[1], config.footage_path)
    except FootageLookupError as exc:
        if exc.matches:  # an ambiguous footage folder is a defect, never a skip
            raise
        pytest.skip(f"{scan.SCAN_CHAPTERS[1]} is not in the footage folder")
    roots = OutputRoots(allowed=tmp_path / "wp1.3d", footage=config.footage_path)
    document = scan.scan_chapter(chapter, roots, roots.allowed / "scan", [5.0, 15.0, 25.0])
    assert len(document["frames"]) == 3
    for entry in document["frames"]:
        assert entry["pts_seconds"] >= entry["grid_s"]
        assert 0.0 <= entry["W"] <= 1.0 and entry["H"] >= 0.0
        assert entry["D"] is None or entry["D"] > 0.0
        assert entry["excluded"] is None or isinstance(entry["excluded"], str)
    cached = scan.load_cache(roots, roots.allowed / "scan", chapter.stem, whole=False)
    assert cached == document
    leftover = list((roots.allowed / "scan" / "frames").rglob("*.png"))
    assert leftover == []  # the ranking frames are removed once measured


# --- the interrupted scan resumes --------------------------------------------------------------


def _synthetic_clip(path: Path, seconds: int) -> None:
    """A small tagged HEVC clip (testsrc2) of ``seconds`` seconds at 10 fps."""
    path.parent.mkdir(parents=True, exist_ok=True)
    done = frames.run_tool(
        [
            *("ffmpeg", "-nostdin", "-hide_banner", "-y", "-loglevel", "error"),
            *("-f", "lavfi", "-i", f"testsrc2=size=256x144:rate=10:duration={seconds}"),
            *("-c:v", "libx265", "-crf", "12", "-x265-params", "log-level=error"),
            *("-pix_fmt", "yuv420p", "-color_range", "tv", "-colorspace", "bt709"),
            *("-color_primaries", "bt709", "-color_trc", "bt709", str(path)),
        ]
    )
    assert done.returncode == 0, done.stderr.decode(errors="replace")[-300:]


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not on PATH")
def test_an_interrupted_chapter_scan_resumes_and_matches_an_uninterrupted_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    footage = load_local_config().footage_path
    roots = OutputRoots(allowed=tmp_path / "wp1.3d", footage=footage)
    clip = tmp_path / "wp1.3d" / "GXSYN.mp4"
    _synthetic_clip(clip, 36)  # scan timestamps 5, 15, 25 and 35
    whole = scan.scan_chapter(clip, roots, roots.allowed / "whole")
    assert [entry["grid_s"] for entry in whole["frames"]] == [5.0, 15.0, 25.0, 35.0]
    monkeypatch.setattr(scan, "PARTIAL_BATCH", 1)
    real_extract = scan.extract
    calls: list[int] = []

    def failing(*args: Any, **kwargs: Any) -> Any:
        calls.append(1)
        if len(calls) == 3:
            raise frames.ExtractError("interrupted")
        return real_extract(*args, **kwargs)

    monkeypatch.setattr(scan, "extract", failing)
    scan_dir = roots.allowed / "resumed"
    with pytest.raises(frames.ExtractError, match="interrupted"):
        scan.scan_chapter(clip, roots, scan_dir)
    assert not (scan_dir / "GXSYN.json").exists()
    saved = json.loads((scan_dir / "GXSYN.partial.json").read_text(encoding="utf-8"))
    assert [entry["grid_s"] for entry in saved["frames"]] == [5.0, 15.0]
    monkeypatch.setattr(scan, "extract", real_extract)
    resumed = scan.scan_chapter(clip, roots, scan_dir)
    assert resumed == whole
    assert not (scan_dir / "GXSYN.partial.json").exists()


# --- the scan cache is never trusted blindly ---------------------------------------------------


def _cache_frame(grid_s: float, **changes: Any) -> dict[str, Any]:
    """A self-consistent cached frame record of chapter GXSYN, with ``changes`` applied."""
    entry = _rec("GXSYN", grid_s).record()
    entry.update(changes)
    return entry


def _cache_document(**changes: Any) -> dict[str, Any]:
    """A usable cache document for a 16 s chapter (grid 5 s and 15 s), with ``changes`` applied."""
    document: dict[str, Any] = {
        "schema": scan.SCAN_SCHEMA,
        "spec": scan.SPEC_VERSION,
        "chapter": "GXSYN",
        "source": {"file": "GXSYN.mp4", "bytes": 1234},
        "duration_s": 16.0,
        "frame_rate": "10/1",
        "rules": scan.rules_record(),
        "timestamps": [5.0, 15.0],
        "frames": [_cache_frame(5.0), _cache_frame(15.0)],
    }
    document.update(changes)
    return document


def _write_cache(tmp_path: Path, document: dict[str, Any]) -> tuple[OutputRoots, Path]:
    roots = OutputRoots(allowed=tmp_path / "wp1.3d", footage=load_local_config().footage_path)
    scan_dir = roots.allowed / "scan"
    roots.write_text(scan_dir / "GXSYN.json", json.dumps(document))
    return roots, scan_dir


def test_a_usable_cache_loads_and_every_kind_of_unusable_one_is_refused(tmp_path: Path) -> None:
    roots, scan_dir = _write_cache(tmp_path, _cache_document())
    assert scan.load_cache(roots, scan_dir, "GXSYN") is not None
    assert scan.load_cache(roots, scan_dir, "GXNONE") is None
    rules = scan.rules_record()
    rules["open_water"]["luma_local_std_below"] = 0.5  # type: ignore[index]
    stale = {
        "other rule set": _cache_document(rules=rules),
        "no rules recorded": {k: v for k, v in _cache_document().items() if k != "rules"},
        "another chapter": _cache_document(chapter="GXOTHER"),
        "a frame missing": _cache_document(frames=[_cache_frame(5.0)]),
        "not the whole grid": _cache_document(timestamps=[5.0], frames=[_cache_frame(5.0)]),
        "other schema": _cache_document(schema=scan.SCAN_SCHEMA + 1),
        "no source recorded": {k: v for k, v in _cache_document().items() if k != "source"},
        "a record of another chapter": _cache_document(
            frames=[_cache_frame(5.0, chapter="GXOTHER"), _cache_frame(15.0)]
        ),
        "a record whose name does not follow its pts": _cache_document(
            frames=[_cache_frame(5.0, frame="GXSYN_0099.000"), _cache_frame(15.0)]
        ),
        "a record taken before its grid point": _cache_document(
            frames=[_cache_frame(5.0, pts_ticks=1), _cache_frame(15.0)]
        ),
        "a measure out of range": _cache_document(
            frames=[_cache_frame(5.0, W=1.5), _cache_frame(15.0)]
        ),
        "an exclusion that does not follow": _cache_document(
            frames=[_cache_frame(5.0, excluded="luma mean 0.01"), _cache_frame(15.0)]
        ),
        "a record that cannot be read": _cache_document(
            frames=[{"grid_s": 5.0}, _cache_frame(15.0)]
        ),
    }
    for label, document in stale.items():
        roots, scan_dir = _write_cache(tmp_path / label.replace(" ", "-"), document)
        with pytest.raises(scan.ScanError, match="not usable"):
            scan.load_cache(roots, scan_dir, "GXSYN")
    # the footage file must be the one the cache was made from
    roots, scan_dir = _write_cache(tmp_path / "size", _cache_document())
    assert scan.load_cache(roots, scan_dir, "GXSYN", source_bytes=1234) is not None
    with pytest.raises(scan.ScanError, match="1234-byte file"):
        scan.load_cache(roots, scan_dir, "GXSYN", source_bytes=999)
    # a deliberate subset (the test scans) loads only when the caller says so
    roots, scan_dir = _write_cache(
        tmp_path / "subset", _cache_document(timestamps=[5.0], frames=[_cache_frame(5.0)])
    )
    assert scan.load_cache(roots, scan_dir, "GXSYN", whole=False) is not None


def test_finish_refuses_a_stale_cache_instead_of_writing_scan_json(tmp_path: Path) -> None:
    roots, scan_dir = _write_cache(tmp_path, _cache_document(frames=[_cache_frame(5.0)]))
    stale = scan_dir / f"{scan.SCAN_CHAPTERS[0]}.json"
    roots.write_text(stale, json.dumps(_cache_document(chapter=scan.SCAN_CHAPTERS[0], frames=[])))
    with pytest.raises(scan.ScanError, match="not usable"):
        scan.finish(roots, scan_dir)
    assert not (roots.allowed / "scan.json").exists()
    assert not (roots.allowed / "deep-frames.json").exists()


def test_discard_cache_removes_the_cache_and_the_interrupted_run_file(tmp_path: Path) -> None:
    roots, scan_dir = _write_cache(tmp_path, _cache_document())
    roots.write_text(scan_dir / "GXSYN.partial.json", "{}")
    scan.discard_cache(roots, scan_dir, "GXSYN")
    assert not list(scan_dir.glob("GXSYN*.json"))
    scan.discard_cache(roots, scan_dir, "GXSYN")  # a missing file is not an error


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not on PATH")
def test_an_interrupted_run_file_from_other_rules_is_discarded_not_resumed(tmp_path: Path) -> None:
    footage = load_local_config().footage_path
    roots = OutputRoots(allowed=tmp_path / "wp1.3d", footage=footage)
    clip = tmp_path / "wp1.3d" / "GXSYN.mp4"
    _synthetic_clip(clip, 6)  # one scan timestamp, 5 s
    clean = scan.scan_chapter(clip, roots, roots.allowed / "clean")
    scan_dir = roots.allowed / "stale"
    foreign = dict(clean, rules={}, frames=[dict(clean["frames"][0], D=9.9, W=0.0, H=9.9)])
    roots.write_text(scan_dir / "GXSYN.partial.json", json.dumps(foreign))
    resumed = scan.scan_chapter(clip, roots, scan_dir)
    assert resumed == clean
    assert resumed["frames"][0]["D"] != 9.9


# --- test 5: the deep pack ------------------------------------------------------------------------


def _deep_entry(rank: int, serves: list[str]) -> dict[str, Any]:
    """A deep-frames.json entry with the keys the page reads."""
    return {"rank": rank, "D": 0.4321, "W": 0.25, "H": 0.0789, "serves_cases": serves}


def _deep_roots(root: Path) -> OutputRoots:
    """Roots whose allowed folder is ``root/work/wp1.3d``, with the real footage folder."""
    return OutputRoots(allowed=root / "work" / "wp1.3d", footage=load_local_config().footage_path)


@pytest.fixture(scope="module")
def deep_pack(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    """Build a deep pack from two frames of a synthetic clip on the CPU: one chapter still and
    one candidate that serves two cases."""
    root = tmp_path_factory.mktemp("deep")
    roots = _deep_roots(root)
    clip = roots.check(roots.allowed / "GXSYN.mp4")
    _synthetic_clip(clip, 2)
    still, candidate = frames.extract(clip, [0.1, 0.9], roots.allowed / "frames", roots=roots)
    both = ["deep-water-noise", "open-blue-water"]
    candidates = {
        "deep-water-noise": [(candidate, _deep_entry(1, both))],
        "open-blue-water": [(candidate, _deep_entry(1, both))],
    }
    link = roots.allowed / "clip" / "GXSYN_c3.mp4"
    document = pack.build_deep_pack([still], candidates, roots.allowed, roots, CPU, [link])
    return {"roots": roots, "still": still, "candidate": candidate, "document": document}


def test_the_deep_variants_are_c3_then_ancuti2018_then_the_blue_one() -> None:
    variants = pack.deep_variants()
    assert [v.name for v in variants] == ["c3", "ancuti2018", "ancuti2018-blue"]
    assert [(v.params.method, v.params.blue_compensation) for v in variants] == [
        ("c3", False),
        ("ancuti2018", False),
        ("ancuti2018", True),
    ]
    assert variants[0].params == dataclasses.replace(Params(), method="c3")
    # the shallow pack's order is unchanged
    assert [v.name for v in pack.default_variants()] == ["ancuti2018", "ancuti2018-blue", "c3"]


def test_the_deep_pack_has_its_layout_and_the_index_names_every_file(
    deep_pack: dict[str, Any],
) -> None:
    roots: OutputRoots = deep_pack["roots"]
    root = roots.allowed
    names = ["c3", "ancuti2018", "ancuti2018-blue"]
    document = deep_pack["document"]
    assert list(document["variants"]) == names
    # two frames: the candidate serving two cases is corrected once
    assert [e["frame"] for e in document["frames"]] == [
        deep_pack["still"].path.stem,
        deep_pack["candidate"].path.stem,
    ]
    for frame in (deep_pack["still"], deep_pack["candidate"]):
        stem = frame.path.stem
        assert (root / "frames" / f"{stem}.png").is_file()
        assert (root / "thumbs" / f"{stem}.jpg").is_file()
        for name in names:
            assert (root / "frames" / f"{stem}-{name}.png").is_file()
            assert (root / "thumbs" / f"{stem}-{name}.jpg").is_file()
            assert (root / "pairs" / f"{stem}-{name}.jpg").is_file()
    for name in ("frames.json", "statistics.json", "index.html"):
        assert (root / name).is_file()
    page = (root / "index.html").read_text(encoding="utf-8")
    pack_files = sorted(
        path.relative_to(root).as_posix()
        for folder in ("frames", "thumbs", "pairs")
        for path in (root / folder).rglob("*")
        if path.is_file()
    )
    assert pack_files
    for name in [*pack_files, "frames.json", "statistics.json"]:
        assert f'"{name}"' in page, f"{name} is not named in index.html"
    assert "http://" not in page and "https://" not in page


def test_the_deep_page_head_sections_and_wording(deep_pack: dict[str, Any]) -> None:
    page = (deep_pack["roots"].allowed / "index.html").read_text(encoding="utf-8")
    # variants in the stated order, as column headers
    columns = [page.index(f"<th>{name}</th>") for name in ("c3", "ancuti2018", "ancuti2018-blue")]
    assert columns == sorted(columns)
    for field in dataclasses.fields(Params):
        assert f"<td>{field.name}</td>" in page
    for variant in pack.deep_variants():
        assert variant.flags in page
    # the rule of claim 2 is on the page, and candidates are called candidates
    for case in scan.CASES:
        assert case.rule in page and case.label in page
    assert "CANDIDATES" in page and "30 s apart" in page and "ties break by chapter name" in page
    assert "also a candidate for open-blue-water" in page  # on the deep-water-noise caption
    assert "also a candidate for deep-water-noise" in page  # and on the other case's
    assert "D 0.432, W 0.250, H 0.0789" in page
    # the chapter stills come first, then the case sections in case order
    assert page.index("Chapter stills") < page.index("Case candidates")
    assert page.index(scan.CASES[0].label + "</h3>") < page.index(scan.CASES[1].label + "</h3>")
    assert "Params() default method" in page  # the explicit-method note
    assert "PENDING: Photos" in page
    assert 'href="clip/GXSYN_c3.mp4"' in page


def test_a_candidate_that_is_also_a_still_is_corrected_once(tmp_path: Path) -> None:
    roots = _deep_roots(tmp_path)
    clip = roots.check(roots.allowed / "GXSYN.mp4")
    _synthetic_clip(clip, 2)
    (frame,) = frames.extract(clip, [0.5], roots.allowed / "frames", roots=roots)
    candidates = {"distance-haze": [(frame, _deep_entry(1, ["distance-haze"]))]}
    document = pack.build_deep_pack([frame], candidates, roots.allowed, roots, CPU)
    assert [e["frame"] for e in document["frames"]] == [frame.path.stem]


def test_a_pts_is_written_with_its_whole_time_base() -> None:
    assert pack.tick_text(10010, Fraction(1, 30000)) == "10010 / 30000"
    assert pack.tick_text(10010, Fraction(1001, 30000)) == "10010 x 1001 / 30000"


def test_the_clip_window_is_centred_and_kept_inside_the_chapter() -> None:
    assert pack.clip_window(50.0, 100.0) == 47.0
    assert pack.clip_window(1.0, 100.0) == 0.0  # clamped to the start
    assert pack.clip_window(99.0, 100.0) == 94.0  # clamped so the excerpt ends with the chapter
    assert pack.clip_window(3.0, 6.4) == pytest.approx(0.0)  # a chapter hardly longer than 6 s
    assert pack.clip_window(2.0, 4.0) == 0.0  # a chapter shorter than the excerpt


def test_the_deep_smoother_is_the_provisional_centred_gaussian_at_two_seconds() -> None:
    assert (pack.DEEP_SMOOTHER.kind, pack.DEEP_SMOOTHER.window_s) == ("gaussian", 2.0)
    assert pack.DEEP_CLIP_SECONDS == 6.0 and pack.DEEP_CLIP_VARIANTS == ("c3", "ancuti2018")


@pytest.mark.parametrize("method", ["c3", "ancuti2018"])
def test_correct_with_supplied_statistics_equals_temporal_render_bit_for_bit(method: str) -> None:
    """The clip calls ``pipeline.correct(..., statistics=)`` to keep the Result; its image is the
    same as ``temporal.render``'s for the same supplied statistics."""
    from prototype import temporal
    from prototype.pipeline import correct

    rng = np.random.default_rng(7)
    base = np.array([0.15, 0.45, 0.50], dtype=np.float32)
    images = [
        np.clip(base + 0.2 * rng.random((HEIGHT, WIDTH, 3), dtype=np.float32), 0, 1).astype(
            np.float32
        )
        for _ in range(5)
    ]
    params = dataclasses.replace(Params(), method=method)
    smoothed, _measured = temporal.analyse_staged(
        images, params, pack.DEEP_SMOOTHER, Fraction(30000, 1001), CPU
    )
    for index, image in enumerate(images):
        statistics = temporal.at(smoothed, index)
        direct = correct(image, params, CPU, statistics=statistics)
        assert np.array_equal(direct.output, temporal.render(image, params, statistics, CPU))


def test_a_smoothed_alpha_one_ulp_below_one_is_not_a_bound_cap_but_a_real_cap_is() -> None:
    """A Gaussian-smoothed constant 1.0 is 0.9999999999999999: not a gain cap. The strict default
    (the shallow pack's) is unchanged."""
    from prototype import temporal
    from prototype.pipeline import correct

    rng = np.random.default_rng(3)
    image = np.clip(
        np.array([0.2, 0.5, 0.5], dtype=np.float32) + 0.1 * rng.random((HEIGHT, WIDTH, 3)), 0, 1
    ).astype(np.float32)
    params = dataclasses.replace(Params(), method="ancuti2018")
    smoothed, _ = temporal.analyse_staged(
        [image] * 3, params, pack.DEEP_SMOOTHER, Fraction(30000, 1001), CPU
    )
    base = temporal.at(smoothed, 1)

    def record(alpha: float, tolerance: float | None) -> bool:
        statistics = dataclasses.replace(base, compensation_alpha={"red": alpha})
        result = correct(image, params, CPU, statistics=statistics)
        if tolerance is None:
            return bool(pack.statistics_record(result, CPU)["bound"]["red_gain_cap"])
        return bool(pack.statistics_record(result, CPU, tolerance)["bound"]["red_gain_cap"])

    one_ulp_below = 1.0 - 2.0**-53
    assert one_ulp_below < 1.0
    assert record(one_ulp_below, None) is True  # strict default: the shallow behaviour
    assert record(one_ulp_below, pack.DEEP_CAP_TOLERANCE) is False
    assert record(0.99, pack.DEEP_CAP_TOLERANCE) is True  # a real cap still counts
    assert record(1.0, None) is False


def test_statistics_record_takes_the_applied_normalisation_bounds_when_given() -> None:
    """A clip frame records the N{} pair the render applied, not a recomputation on the frame;
    without it the shallow behaviour (a recomputation) is unchanged."""
    from prototype.pipeline import correct, normalisation_bounds

    rng = np.random.default_rng(5)
    image = (0.2 + 0.5 * rng.random((HEIGHT, WIDTH, 3))).astype(np.float32)
    result = correct(image, Params(), CPU)
    low, high = normalisation_bounds(CPU.to_device(result.white_balanced), result.params)
    recomputed = pack.statistics_record(result, CPU)["normalisation"]
    assert (recomputed["low"], recomputed["high"]) == (low, high)
    applied = pack.statistics_record(result, CPU, applied_normalisation=(0.25, 0.75))
    assert applied["normalisation"] == {"low": 0.25, "high": 0.75, "collapsed": False}
    assert (low, high) != (0.25, 0.75)
    flat = pack.statistics_record(result, CPU, applied_normalisation=(0.5, 0.5))
    assert flat["normalisation"]["collapsed"] is True
    assert flat["bound"]["normalisation_collapsed"] is True and flat["bound"]["any"] is True


def test_the_flicker_path_keeps_the_shallow_readback_bound_of_three_levels() -> None:
    """Only the deep clip passes the wider own-PNG bound; the flicker defaults are unchanged."""
    import inspect

    assert pack.READBACK_MAX_OWN == 3.0 and pack.DEEP_READBACK_MAX_OWN == 5.0
    for function in (pack.readback_clip, pack.encode_verified_pair):
        assert inspect.signature(function).parameters["max_own"].default == 3.0
    assert "max_own" not in inspect.getsource(pack.run_flicker)
    deep = inspect.signature(pack.encode_deep_clip).parameters["max_own"]
    assert deep.default == pack.DEEP_READBACK_MAX_OWN


def test_deep_frames_must_agree_with_scan_json(tmp_path: Path) -> None:
    roots = _deep_roots(tmp_path)
    chapters = ("GXA", "GXB", "GXC", "GXD")
    records = [
        _rec(chapter, 5.0 + 10.0 * n, depth=0.3 + 0.01 * n + 0.001 * k, water=0.02 * n)
        for k, chapter in enumerate(chapters)
        for n in range(10)
    ]
    written = "2026-10-20T00:00:00+00:00"
    document = scan.deep_frames_document(records, written)
    roots.write_text(roots.allowed / "deep-frames.json", json.dumps(document))
    with pytest.raises(frames.ExtractError, match="does not exist"):
        pack._load_deep_frames(roots)  # scan.json missing
    scanned = {"frames": [r.record() for r in records]}
    roots.write_text(roots.allowed / "scan.json", json.dumps(scanned))
    assert pack._load_deep_frames(roots)["deepest"][0]["frame"] == document["deepest"][0]["frame"]
    altered = json.loads(json.dumps(document))
    altered["cases"]["deep-water-noise"]["frames"][0]["D"] = 0.0001
    roots.write_text(roots.allowed / "deep-frames.json", json.dumps(altered))
    with pytest.raises(frames.ExtractError, match="does not match"):
        pack._load_deep_frames(roots)
    # a scan.json from other frames
    roots.write_text(roots.allowed / "deep-frames.json", json.dumps(document))
    other = {
        "frames": [
            _rec(chapter, 5.0 + 10.0 * n, depth=0.9 - 0.01 * n - 0.001 * k).record()
            for k, chapter in enumerate(chapters)
            for n in range(10)
        ]
    }
    roots.write_text(roots.allowed / "scan.json", json.dumps(other))
    with pytest.raises(frames.ExtractError, match="does not match"):
        pack._load_deep_frames(roots)


# --- the clip's render, encode and page steps only accept what belongs together ------------------


EMPTY_SHA = hashlib.sha256(b"").hexdigest()


def _clip_document(stem: str = "GXFAKE", count: int = 3, **changes: Any) -> dict[str, Any]:
    """A statistics document for a ``count``-frame clip of the deep variants, not yet encoded."""
    variants = {}
    for variant in pack.deep_variants():
        if variant.name not in pack.DEEP_CLIP_VARIANTS:
            continue
        variants[variant.name] = {
            "params": dataclasses.asdict(variant.params),
            "frames": [
                {
                    "index": n,
                    "pts_ticks": 1001 * n,
                    "source_file": f"{stem}_f{n:04d}.png",
                    "source_sha256": EMPTY_SHA,
                    "corrected_file": f"{stem}_f{n:04d}-{variant.name}.png",
                    "corrected_sha256": EMPTY_SHA,
                }
                for n in range(count)
            ],
        }
    document: dict[str, Any] = {
        "chapter": stem,
        "centre_s": 3.95,
        "source_bytes": 77,
        "analysis": "STAGED (spec D97)",
        "checks": None,
        "smoother": {"kind": pack.DEEP_SMOOTHER.kind, "window_s": pack.DEEP_SMOOTHER.window_s},
        "excerpt": {"frames": count},
        "variants": variants,
    }
    document.update(changes)
    return document


def _touch_sets(clip_dir: Path, document: dict[str, Any]) -> None:
    """Create the empty PNG files the document names."""
    for name, body in document["variants"].items():
        for row in body["frames"]:
            for folder, file in (
                (f"corrected-{name}", row["corrected_file"]),
                ("source", row["source_file"]),
            ):
                (clip_dir / folder).mkdir(parents=True, exist_ok=True)
                (clip_dir / folder / file).write_bytes(b"")


def test_clip_inputs_that_belong_together_have_no_problem_and_every_mismatch_is_named(
    tmp_path: Path,
) -> None:
    document = _clip_document()
    _touch_sets(tmp_path, document)
    assert pack.clip_inputs_problem(document, "GXFAKE", tmp_path) is None
    assert "chapter" in str(pack.clip_inputs_problem(document, "GXOTHER", tmp_path))
    assert "already encoded" in str(
        pack.clip_inputs_problem(dict(document, checks={"c3": {"ok": True}}), "GXFAKE", tmp_path)
    )
    wrong_smoother = dict(document, smoother={"kind": "gaussian", "window_s": 1.0})
    assert "smoother" in str(pack.clip_inputs_problem(wrong_smoother, "GXFAKE", tmp_path))
    extra = dict(document, variants={**document["variants"], "c3x": document["variants"]["c3"]})
    assert "variants" in str(pack.clip_inputs_problem(extra, "GXFAKE", tmp_path))
    params = _clip_document()
    params["variants"]["c3"]["params"]["gamma"] = 9.0
    assert "parameters" in str(pack.clip_inputs_problem(params, "GXFAKE", tmp_path))
    shifted = _clip_document()
    shifted["variants"]["ancuti2018"]["frames"][1]["pts_ticks"] = 7
    assert "pts" in str(pack.clip_inputs_problem(shifted, "GXFAKE", tmp_path))
    assert pack.clip_inputs_problem(document, "GXFAKE", tmp_path, 77) is None
    assert "rendered from" in str(pack.clip_inputs_problem(document, "GXFAKE", tmp_path, 78))
    assert "STAGED" in str(
        pack.clip_inputs_problem(dict(document, analysis="flat"), "GXFAKE", tmp_path)
    )
    (tmp_path / "source" / "GXFAKE_f0001.png").write_bytes(b"replaced")  # same name, other bytes
    assert "not the file the render read" in str(
        pack.clip_inputs_problem(document, "GXFAKE", tmp_path)
    )
    (tmp_path / "corrected-c3" / "GXFAKE_f0002-c3.png").write_bytes(b"replaced")
    assert "not the file the render wrote" in str(
        pack.clip_inputs_problem(document, "GXFAKE", tmp_path)
    )
    (tmp_path / "corrected-c3" / "GXFAKE_f0002-c3.png").write_bytes(b"")
    (tmp_path / "source" / "GXFAKE_f0001.png").unlink()
    assert "source PNGs" in str(pack.clip_inputs_problem(document, "GXFAKE", tmp_path))
    (tmp_path / "source" / "GXFAKE_f0001.png").write_bytes(b"")
    (tmp_path / "corrected-c3" / "GXFAKE_f0009-c3.png").write_bytes(b"")  # a stale extra frame
    assert "corrected-c3" in str(pack.clip_inputs_problem(document, "GXFAKE", tmp_path))


def test_encode_deep_clip_refuses_stale_inputs_before_it_runs_any_tool(tmp_path: Path) -> None:
    roots = _deep_roots(tmp_path)
    clip_dir = roots.allowed / "clip"
    video = tmp_path / "GXFAKE.mp4"  # never opened: the refusal comes first
    with pytest.raises(frames.ExtractError, match="render the deep clip first"):
        pack.encode_deep_clip(video, roots, clip_dir)
    video.write_bytes(b"x" * 77)  # a stand-in of the recorded size; never decoded
    document = _clip_document(checks={"c3": {"ok": True}})
    _touch_sets(clip_dir, document)
    roots.write_text(clip_dir / "statistics.json", json.dumps(document))
    with pytest.raises(frames.ExtractError, match="already encoded"):
        pack.encode_deep_clip(video, roots, clip_dir)
    document = _clip_document()
    _touch_sets(clip_dir, document)
    roots.write_text(clip_dir / "statistics.json", json.dumps(dict(document, source_bytes=5)))
    with pytest.raises(frames.ExtractError, match="rendered from"):  # another source video
        pack.encode_deep_clip(video, roots, clip_dir)


def test_clear_clip_removes_clips_statistics_and_frames_only(tmp_path: Path) -> None:
    roots = _deep_roots(tmp_path)
    clip_dir = roots.allowed / "clip"
    document = _clip_document()
    _touch_sets(clip_dir, document)
    for name in ("GXFAKE_c3.mp4", "GXFAKE_source.mp4", "statistics.json", "statistics-c3.png"):
        (clip_dir / name).write_bytes(b"x")
    (clip_dir / "keep.txt").write_bytes(b"x")
    pack.clear_clip(roots, clip_dir)
    assert [p.name for p in clip_dir.rglob("*") if p.is_file()] == ["keep.txt"]
    pack.clear_clip(roots, roots.allowed / "nowhere")  # a missing folder is fine


def test_the_page_links_only_a_verified_clip_of_the_current_deepest_frame(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    roots = _deep_roots(tmp_path)
    clip_dir = roots.allowed / "clip"
    assert pack.clip_files(roots, clip_dir) == []  # no clip was ever rendered
    deepest = {"chapter": "GXFAKE", "frame": "GXFAKE_3.950", "pts_seconds": 3.95}
    monkeypatch.setattr(pack, "_load_deep_frames", lambda _roots: {"deepest": [deepest]})
    ok = {label: {"ok": True} for label in ("c3", "ancuti2018", "source", "readback")}
    clip_dir.mkdir(parents=True, exist_ok=True)
    for name in ("GXFAKE_c3.mp4", "GXFAKE_ancuti2018.mp4", "GXFAKE_source.mp4"):
        (clip_dir / name).write_bytes(b"x")

    def write(**changes: Any) -> None:
        roots.write_text(clip_dir / "statistics.json", json.dumps(_clip_document(**changes)))

    write()  # rendered, not encoded
    with pytest.raises(frames.ExtractError, match="not encoded"):
        pack.clip_files(roots, clip_dir)
    write(checks=dict(ok, readback={"ok": False}))
    with pytest.raises(frames.ExtractError, match="did not hold"):
        pack.clip_files(roots, clip_dir)
    write(checks=ok, centre_s=1.0)  # cut around another frame than the current deepest
    with pytest.raises(frames.ExtractError, match="render it again"):
        pack.clip_files(roots, clip_dir)
    write(checks={"c3": {"ok": True}})  # a check record missing is not a pass
    with pytest.raises(frames.ExtractError, match="missing or did not hold"):
        pack.clip_files(roots, clip_dir)
    write(checks={})
    with pytest.raises(frames.ExtractError, match="missing or did not hold"):
        pack.clip_files(roots, clip_dir)
    write(checks=ok)  # checks fine, but the MP4s were never bound to them
    with pytest.raises(frames.ExtractError, match="not the file that was verified"):
        pack.clip_files(roots, clip_dir)
    bound = {
        label: {"sha256": hashlib.sha256(b"x").hexdigest()}
        for label in ("c3", "ancuti2018", "source")
    }
    write(checks=ok, clips=bound)
    assert [p.name for p in pack.clip_files(roots, clip_dir)] == [
        "GXFAKE_c3.mp4",
        "GXFAKE_ancuti2018.mp4",
        "GXFAKE_source.mp4",
    ]
    (clip_dir / "GXFAKE_source.mp4").write_bytes(b"swapped after the checks")
    with pytest.raises(frames.ExtractError, match="not the file that was verified"):
        pack.clip_files(roots, clip_dir)
    (clip_dir / "GXFAKE_source.mp4").unlink()
    with pytest.raises(frames.ExtractError, match="is missing"):
        pack.clip_files(roots, clip_dir)


# --- the deep clip -------------------------------------------------------------------------------


@pytest.mark.gpu
@pytest.mark.slow
def test_the_deep_clip_is_staged_smoothed_encoded_checked_and_pruned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from prototype import temporal
    from prototype.backend import select_backend

    try:
        backend = select_backend("gpu")
    except RuntimeError as exc:
        pytest.skip(f"no usable graphics card: {exc}")
    roots = _deep_roots(tmp_path)
    clip = roots.check(roots.allowed / "GXDEEP.mp4")
    clip.parent.mkdir(parents=True, exist_ok=True)
    done = frames.run_tool(
        [
            *("ffmpeg", "-nostdin", "-hide_banner", "-y", "-loglevel", "error"),
            *("-f", "lavfi", "-i", "testsrc2=size=1920x1080:rate=30000/1001:duration=4"),
            *("-vf", "format=yuv420p,setparams=range=full:colorspace=bt709"),
            *("-c:v", "libx265", "-crf", "20", "-x265-params", "log-level=error"),
            *("-pix_fmt", "yuv420p", "-color_range", "pc", "-colorspace", "bt709"),
            *("-color_primaries", "bt709", "-color_trc", "bt709", str(clip)),
        ]
    )
    assert done.returncode == 0, done.stderr.decode(errors="replace")[-300:]
    calls: list[tuple[list[Any], str, Any]] = []
    real = temporal.analyse_staged

    def spy(images: Any, params: Any, smoother: Any, rate: Any, backend_: Any = None) -> Any:
        calls.append((list(images), params.method, smoother))
        return real(images, params, smoother, rate, backend_)

    monkeypatch.setattr(temporal, "analyse_staged", spy)
    clip_dir = roots.allowed / "clip"
    rendered = pack.render_deep_clip(clip, 3.95, roots, backend, clip_dir, seconds=0.4)
    # the statistics are on disk before any encode, and the PNG sets are complete
    assert rendered["checks"] is None and rendered["encode_commands"] is None
    on_disk = json.loads((clip_dir / "statistics.json").read_text(encoding="utf-8"))
    assert on_disk["checks"] is None and list(on_disk["variants"]) == ["c3", "ancuti2018"]
    assert not list(clip_dir.glob("*.mp4"))
    count = rendered["excerpt"]["frames"]
    for folder in ("source", "corrected-c3", "corrected-ancuti2018"):
        assert len(list((clip_dir / folder).glob("*.png"))) == count
    document = pack.encode_deep_clip(clip, roots, clip_dir)
    assert 11 <= count <= 12  # 0.4 s at 30000/1001
    duration = frames.probe_stream(clip).duration_s
    start = document["excerpt"]["start_s"]  # centred on 3.95 s would run past the end: clamped
    assert start == pack.clip_window(3.95, duration, 0.4) == pytest.approx(duration - 0.4)
    assert document["analysis"].startswith("STAGED")
    assert document["smoother"] == {"kind": "gaussian", "window_s": 2.0}
    assert all(check["ok"] for label, check in document["checks"].items() if label != "readback")
    assert document["checks"]["readback"]["ok"]
    for label in ("c3", "ancuti2018", "source"):  # the deep bound, not the shallow clip's
        assert document["checks"]["readback"][label]["thresholds"]["max_own"] == 5.0
    for name in ("GXDEEP_c3.mp4", "GXDEEP_ancuti2018.mp4", "GXDEEP_source.mp4", "statistics.json"):
        assert (clip_dir / name).is_file()
    deepest = {"chapter": "GXDEEP", "frame": "GXDEEP_3.950", "pts_seconds": 3.95}
    monkeypatch.setattr(pack, "_load_deep_frames", lambda _roots: {"deepest": [deepest]})
    assert [p.name for p in pack.clip_files(roots, clip_dir)] == [
        "GXDEEP_c3.mp4",
        "GXDEEP_ancuti2018.mp4",
        "GXDEEP_source.mp4",
    ]
    assert not list(clip_dir.glob("*.partial.mp4"))
    for folder in ("source", "corrected-c3", "corrected-ancuti2018"):
        assert len(list((clip_dir / folder).glob("*.png"))) == 3  # first, middle, last
    # the statistics came from the exact NumPy proxy, analysed STAGED, once per method
    assert [(method, smoother.kind, smoother.window_s) for _, method, smoother in calls] == [
        ("c3", "gaussian", 2.0),
        ("ancuti2018", "gaussian", 2.0),
    ]
    middle = count // 2
    source = frames.read_png16(clip_dir / "source" / f"GXDEEP_f{middle:04d}.png")
    expected = source.reshape(540, 2, 960, 2, 3).mean(axis=(1, 3), dtype=np.float64)
    for images, _method, _smoother in calls:
        assert len(images) == count and images[middle].shape == (540, 960, 3)
        assert np.array_equal(images[middle], expected.astype(np.float32))
    reread = json.loads((clip_dir / "statistics.json").read_text(encoding="utf-8"))
    assert list(reread["variants"]) == ["c3", "ancuti2018"]
    for name, body in reread["variants"].items():
        rows = body["frames"]
        assert len(rows) == count
        assert [r["index"] for r in rows] == list(range(count))
        steps = {b["pts_ticks"] - a["pts_ticks"] for a, b in itertools.pairwise(rows)}
        assert steps == {1001}
        assert body["params"]["method"] == name
        raw = [r["raw"]["white_balance_gains.R"] for r in rows]
        smoothed = [r["smoothed"]["white_balance_gains.R"] for r in rows]
        assert raw != smoothed, "control: smoothing must change the gain series"
        assert set(rows[0]["rendered"]) >= {"red_gain", "blue_gain", "bound", "compensation"}
        for row in rows:  # the N{} bounds recorded are the smoothed proxy ones the render applied
            assert (
                row["rendered"]["normalisation"]["low"]
                == row["smoothed"]["normalisation_bounds.low"]
            )
            assert (
                row["rendered"]["normalisation"]["high"]
                == row["smoothed"]["normalisation_bounds.high"]
            )
    alpha = reread["variants"]["ancuti2018"]["frames"][0]["rendered"]["compensation"]["effective"]
    assert "red" in alpha
