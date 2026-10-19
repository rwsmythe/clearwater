"""Tests for the WP1.3D deep look check: the case scan (``lookcheck.scan``) and the ``deep``
command of ``lookcheck.pack``. Synthetic except where marked ``footage``."""

from __future__ import annotations

import json
import shutil
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from local_config import FootageLookupError, find_footage_file, load_local_config
from lookcheck import frames, scan
from lookcheck.frames import OutputRoots

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
    cached = scan.load_cache(roots, roots.allowed / "scan", chapter.stem)
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
