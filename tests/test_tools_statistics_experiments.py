"""Synthetic routing, extraction and window-study checks for WP-DR25.

All paths belong to ``tmp_path``. Decode, probing, device selection and image
processing are replaced at their external boundaries; flicker and JSON writing
remain real so a wrong trimming slice changes an observable recorded figure.
"""

from __future__ import annotations

import dataclasses
import json
import subprocess
import sys
import types
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest

import statistics_experiments as runner
from local_config import LocalConfig
from lookcheck.frames import FrameFile, OutputRoots, StreamInfo, tags_from_stream
from prototype.backend import CPU
from prototype.pipeline import Statistics

RATE = Fraction(30000, 1001)
BASE_RUNNER_BLOB = "74019b47e56bb1b1d7d0ad0c15b3615150ba8925"
PRE_R1_RUNNER_BLOB = "5bada347da89885c93453b57a2cc03053e4de4c2"
DEFAULT_SPECS = (
    ("GX011627", "GX011627", 0.30, 6.0, True, True, (205205, 384384, 1001)),
    ("GX011625", "GX011625", 0.50, 6.0, False, False, None),
)
LONG_SPECS = (
    ("GX011627-long", "GX011627", 0.30, 20.0, False, False, None),
    ("GX011625-long", "GX011625", 0.50, 20.0, False, False, None),
)


def _revision_runner(blob_id):
    """Load a historical instrument blob without depending on a rebased commit's reachability."""
    repository = Path(__file__).resolve().parents[1]
    object_type = subprocess.run(
        ["git", "cat-file", "-t", blob_id],
        cwd=repository,
        capture_output=True,
        encoding="utf-8",
        timeout=10,
        check=False,
    )
    assert object_type.returncode == 0 and object_type.stdout.strip() == "blob", (
        f"Historical instrument blob {blob_id} is missing or is not a blob; "
        "fetch the repository history containing the pinned instrument before running these tests."
    )
    source = subprocess.check_output(
        ["git", "cat-file", "blob", blob_id],
        cwd=repository,
        encoding="utf-8",
        timeout=10,
    )
    module = types.ModuleType(f"statistics_experiments_{blob_id}")
    module.__file__ = runner.__file__
    module.__package__ = "tools"
    sys.modules[module.__name__] = module
    exec(compile(source, f"git-blob:{blob_id}", "exec"), module.__dict__)
    return module


@pytest.fixture(scope="module")
def base_runner():
    """Generate default-path golden records from the fixed WP1.4 base blob."""
    module = _revision_runner(BASE_RUNNER_BLOB)
    yield module
    del sys.modules[module.__name__]


@pytest.fixture(scope="module")
def pre_r1_runner():
    """Keep all unaffected long measurements pinned to the diagnosis instrument blob."""
    module = _revision_runner(PRE_R1_RUNNER_BLOB)
    yield module
    del sys.modules[module.__name__]


@pytest.mark.parametrize("blob_id", [BASE_RUNNER_BLOB, PRE_R1_RUNNER_BLOB])
def test_revision_runner_loads_blob_without_resolving_commit(blob_id, monkeypatch):
    """Load each historical source directly from its rebase-stable blob."""
    # Restore any fixture's existing registration even when tests run in a different order.
    monkeypatch.setitem(sys.modules, f"statistics_experiments_{blob_id}", None)
    module = _revision_runner(blob_id)
    assert callable(module.run_experiments)
    assert module.RENDER_METHOD == "ancuti2018"


def test_revision_runner_refuses_missing_blob_with_clear_message():
    """Explain a missing history prerequisite before trying to execute its source."""
    missing = "0" * 40
    with pytest.raises(AssertionError, match=f"Historical instrument blob {missing} is missing"):
        _revision_runner(missing)


def _take_documents(folder):
    """Read whole JSON documents, excluding only written; remove them to prevent stale passes."""
    documents = {}
    for path in folder.glob("*.json"):
        document = json.loads(path.read_text(encoding="utf-8"))
        document.pop("written")
        documents[path.name] = document
        path.unlink()
    return documents


def _defaults():
    return runner.EXCERPTS, runner.WORK_SUBDIR, runner.RENDER_METHOD


def _dispatch(tmp_path, monkeypatch, phase, *, long=False):
    """Exercise main's real selection and output-root construction against phase spies."""
    config = LocalConfig(footage_path=tmp_path / "footage", working_path=tmp_path / "work")
    before = _defaults()
    found = []
    calls = []
    monkeypatch.setattr(runner, "load_local_config", lambda path: config)
    monkeypatch.setattr(runner, "select_backend", lambda device: CPU)

    def lookup(chapter, footage):
        assert footage == config.footage_path
        found.append(chapter)
        return footage / f"{chapter}.mp4"

    def extract(spec, footage, roots, backend):
        assert footage == config.footage_path and backend is CPU
        calls.append((dataclasses.astuple(spec), roots.allowed))

    def analyse(folder, roots, backend):
        assert folder.parent == roots.allowed and backend is CPU
        return {"folder": folder}

    def experiments(folder, roots, backend, analyses, *, long=False):
        assert analyses == {"folder": folder} and backend is CPU
        calls.append((folder.name, roots.allowed, long))

    def render(spec, footage, roots, backend, witness):
        assert footage == config.footage_path and backend is CPU
        assert witness == config.working_path / "wp1.3" / "flicker" / "corrected"
        calls.append((dataclasses.astuple(spec), roots.allowed))

    monkeypatch.setattr(runner, "find_footage_file", lookup)
    monkeypatch.setattr(runner, "extract_excerpt", extract)
    monkeypatch.setattr(runner, "analyse_statistics", analyse)
    monkeypatch.setattr(runner, "run_experiments", experiments)
    monkeypatch.setattr(runner, "render_clips", render)
    argv = [phase, "--device", "cpu"] + (["--long"] if long else [])
    assert runner.main(argv) == 0
    assert _defaults() == before
    assert tuple(dataclasses.astuple(spec) for spec in runner.EXCERPTS) == DEFAULT_SPECS
    assert runner.WORK_SUBDIR == "wp1.4" and runner.RENDER_METHOD == "ancuti2018"
    return calls, found, config.working_path


@pytest.mark.parametrize("phase", ["extract", "analyse", "render"])
def test_default_cli_keeps_original_specs_root_and_render_selection(tmp_path, monkeypatch, phase):
    calls, found, work = _dispatch(tmp_path, monkeypatch, phase)
    if phase == "analyse":
        assert calls == [(spec[0], work / "wp1.4", False) for spec in DEFAULT_SPECS]
        assert found == []
    else:
        specs = DEFAULT_SPECS if phase == "extract" else DEFAULT_SPECS[:1]
        assert calls == [(spec, work / "wp1.4") for spec in specs]
        assert found == [spec[1] for spec in specs]


@pytest.mark.parametrize("phase", ["extract", "analyse"])
def test_long_cli_selects_long_specs_and_separate_root_without_mutating_defaults(
    tmp_path, monkeypatch, phase
):
    calls, found, work = _dispatch(tmp_path, monkeypatch, phase, long=True)
    assert tuple(dataclasses.astuple(spec) for spec in runner.LONG_EXCERPTS) == LONG_SPECS
    if phase == "extract":
        assert calls == [(spec, work / "wp-dr25") for spec in LONG_SPECS]
        assert found == ["GX011627", "GX011625"]
    else:
        assert calls == [(spec[0], work / "wp-dr25", True) for spec in LONG_SPECS]
        assert found == []


def test_long_render_is_refused_before_configuration_or_device_access(monkeypatch, capsys):
    def must_not_run(*args, **kwargs):
        raise AssertionError("render --long must fail before accessing configuration or devices")

    monkeypatch.setattr(runner, "load_local_config", must_not_run)
    monkeypatch.setattr(runner, "select_backend", must_not_run)
    assert runner.main(["render", "--long"]) == 2
    assert "--long supports extract and analyse only" in capsys.readouterr().err


def _extract(
    tmp_path, monkeypatch, spec, duration, stream_duration="present", *, instrument=runner
):
    """Keep extraction's real records and writers, with three tiny decoded frames."""
    runner = instrument
    footage = tmp_path / "footage"
    video = footage / f"{spec.chapter}.mp4"
    roots = OutputRoots(allowed=tmp_path / "work", footage=footage)
    tags = tags_from_stream(
        {
            "pix_fmt": "yuvj420p",
            "color_range": "pc",
            "color_space": "bt709",
            "color_primaries": "bt709",
            "color_transfer": "bt709",
        }
    )
    info = StreamInfo(4, 4, Fraction(1, 30000), RATE, duration, tags)
    decoded = []

    def decode(source, start, duration_s, folder, *, roots, naming):
        assert source == video and naming == "index"
        assert folder == roots.allowed / spec.name / "frames"
        decoded.append((start, duration_s))
        return [
            FrameFile(folder / f"f{n}.png", video, n * 1001, info.time_base, 4, 4, tags, ("stub",))
            for n in range(3)
        ]

    monkeypatch.setattr(runner, "find_footage_file", lambda chapter, root: video)
    monkeypatch.setattr(runner, "probe_stream", lambda source: info)

    def duration_probe(arguments):
        assert spec.name.endswith("-long"), "default extraction must not re-probe duration"
        assert arguments == [
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=duration:format=duration",
            str(video),
        ]
        stream = {"duration": str(duration)} if stream_duration == "present" else {}
        if stream_duration == "N/A":
            stream["duration"] = "N/A"
        return {"streams": [stream], "format": {"duration": str(duration)}}

    if hasattr(runner, "run_ffprobe"):  # The WP1.4 base has no additional duration probe.
        monkeypatch.setattr(runner, "run_ffprobe", duration_probe)
    monkeypatch.setattr(runner, "excerpt", decode)
    monkeypatch.setattr(runner, "read_png16", lambda path: np.zeros((4, 4, 3), dtype=np.float32))
    monkeypatch.setattr(runner.temporal, "proxy", lambda image: image[:1, :1])
    monkeypatch.setattr(runner.temporal, "statistics_of", lambda *args: Statistics())
    monkeypatch.setattr(runner, "tool_version", lambda program: "stub")
    document = runner.extract_excerpt(spec, footage, roots, CPU)
    persisted = json.loads((roots.allowed / spec.name / "excerpt.json").read_text(encoding="utf-8"))
    assert document == persisted
    return document, decoded


@pytest.mark.parametrize(
    ("duration", "start"), [(22.7227, 11.36135), (10.0, 5.0)], ids=["fits", "short-unclamped"]
)
def test_default_extract_keeps_start_and_record_schema(
    tmp_path, monkeypatch, base_runner, duration, start
):
    with monkeypatch.context() as base_patches:
        _extract(tmp_path, base_patches, base_runner.EXCERPTS[1], duration, instrument=base_runner)
    expected = _take_documents(tmp_path / "work" / "GX011625")
    assert set(expected) == {"excerpt.json", "statistics-raw.json"}
    document, decoded = _extract(tmp_path, monkeypatch, runner.EXCERPTS[1], duration)
    assert _take_documents(tmp_path / "work" / "GX011625") == expected
    assert decoded == [(start, 6.0)]
    assert document["start_s"] == start
    assert document["start_fraction"] == 0.50
    assert "requested_start_s" not in document
    assert "duration_source" not in document
    assert document["stream_duration_s"] == duration


@pytest.mark.parametrize("stream_duration", ["present", None, "N/A"])
@pytest.mark.parametrize(
    ("spec", "duration", "requested", "actual"),
    [
        (LONG_SPECS[0], 22.7227, 6.81681, 2.7227),
        (LONG_SPECS[1], 498.43, 249.215, 249.215),
    ],
    ids=["clamped", "fits"],
)
def test_long_extract_records_requested_and_clamped_start(
    tmp_path, monkeypatch, spec, duration, requested, actual, stream_duration
):
    before = _defaults()
    document, decoded = _extract(
        tmp_path, monkeypatch, runner.ExcerptSpec(*spec), duration, stream_duration
    )
    assert decoded[0][0] == pytest.approx(actual)
    assert decoded[0][1] == 20.0
    assert document["requested_start_s"] == pytest.approx(requested)
    assert document["start_s"] == pytest.approx(actual)
    assert document["start_fraction"] == spec[2]
    assert document["stream_duration_s"] == duration
    assert document["duration_source"] == (
        "stream" if stream_duration == "present" else "container"
    )
    assert _defaults() == before


def _window_study(
    tmp_path,
    monkeypatch,
    count,
    *,
    long=False,
    instrument=runner,
    save_analyses=False,
    crossing_method=None,
    reject_crossed_trend=False,
):
    """Leave trimming/flicker/JSON real; supply marked signals instead of rendering images."""
    runner = instrument
    roots = OutputRoots(allowed=tmp_path / "work", footage=tmp_path / "footage")
    folder = roots.allowed / "synthetic"
    entries = [
        {"index": n, "pts_ticks": n * 1001, "pts_seconds": n / float(RATE)} for n in range(count)
    ]
    raw = {
        name: {
            "normalisation_bounds.low": np.full(count, key, dtype=np.float64),
            "normalisation_bounds.high": np.full(count, key + 1, dtype=np.float64),
        }
        for name, key in (("ancuti2018", 3), ("c3", 5))
    }
    if crossing_method is not None:
        # Eight ordered measurements: a fast narrowing then a plateau. OLS overshoots
        # at indices 6 and 7: lows=7.25/15.5, highs=-7.25/-15.5, although each
        # input low is below high. Multiple crossings witness the count and full list.
        assert count == 8
        raw[crossing_method] = {
            "normalisation_bounds.low": np.array([-100.0, *([-1.0] * 7)]),
            "normalisation_bounds.high": np.array([100.0, *([1.0] * 7)]),
        }
    loaded = runner.Loaded(
        folder,
        {"frames": entries, "excerpt": "synthetic", "frame_rate": "30000/1001"},
        np.zeros((count, 1, 1, 3), dtype=np.float32),
        RATE,
        raw,
        {},
    )
    step_levels = np.ones(count - 1)
    step_levels[:180] = 100.0
    step_levels[count - 181 :] = 100.0
    staged_calls = []
    flat_calls = []

    def staged(proxies, params, smoother, rate, backend):
        assert len(proxies) == count and rate == RATE and backend is CPU
        staged_calls.append((params.method, smoother.label))
        return {"staged": np.ones(count)}, {}

    def flat(series, smoother, rate):
        assert rate == RATE
        method = next(name for name in raw if series is raw[name])
        flat_calls.append((method, smoother.label))
        return {"flat": np.ones(count)}

    def signals(proxies, params, series, backend, constant=None):
        if reject_crossed_trend and series is not None and "normalisation_bounds.low" in series:
            assert np.all(
                series["normalisation_bounds.low"] <= series["normalisation_bounds.high"]
            ), "attempted to render a crossed trend"
        method_key = {"ancuti2018": 2, "c3": 7}[params.method]
        if constant is not None:
            # Reference slopes witness the actual raw method used to construct Statistics.
            levels = np.full(count - 1, method_key * constant.normalisation_bounds[0])
        else:
            if series is None:
                series_key = 23  # unsmoothed
            elif "staged" in series:
                series_key = 11
            elif "flat" in series:
                series_key = 17
            else:
                series_key = 29  # linear trend
            levels = step_levels + method_key * series_key
        return np.repeat(np.r_[0.0, np.cumsum(levels / 255.0)][:, None], 4, axis=1)

    monkeypatch.setattr(runner, "load_excerpt", lambda path: loaded)
    monkeypatch.setattr(runner, "_signals", signals)
    monkeypatch.setattr(runner, "_mismatch_record", lambda *args: {})
    monkeypatch.setattr(runner, "_render_difference", lambda *args: {})
    monkeypatch.setattr(runner, "robust_study", lambda *args: {})
    monkeypatch.setattr(runner, "plot_series", lambda *args: b"stub")
    monkeypatch.setattr(runner.temporal, "analyse_staged", staged)
    monkeypatch.setattr(runner.temporal, "analyse_flat", flat)
    monkeypatch.setattr(runner.temporal, "step_response", lambda *args: {})
    analyses = {kind: {name: {kind: np.ones(count)} for name in raw} for kind in ("staged", "flat")}
    if save_analyses:
        analyses = runner.analyse_statistics(folder, roots, CPU)
        staged_calls.clear()
        flat_calls.clear()
    before = _defaults()
    kwargs = {"long": True} if long else {}
    document = runner.run_experiments(folder, roots, CPU, analyses, **kwargs)
    assert _defaults() == before
    persisted = json.loads((folder / "results.json").read_text(encoding="utf-8"))
    assert document == persisted
    return document, staged_calls, flat_calls, step_levels


def test_default_window_study_keeps_one_method_and_fixed_margin(tmp_path, monkeypatch, base_runner):
    with monkeypatch.context() as base_patches:
        _window_study(tmp_path, base_patches, 600, instrument=base_runner, save_analyses=True)
    expected = _take_documents(tmp_path / "work" / "synthetic")
    assert set(expected) == {"statistics-staged.json", "statistics-flat.json", "results.json"}
    document, staged_calls, flat_calls, _ = _window_study(
        tmp_path, monkeypatch, 600, save_analyses=True
    )
    assert _take_documents(tmp_path / "work" / "synthetic") == expected
    labels = [
        f"{kind} {window:g} s"
        for kind in ("moving_average", "gaussian", "median_gaussian")
        for window in (0.5, 1.0, 2.0, 4.0)
    ]
    assert staged_calls == flat_calls == [("ancuti2018", label) for label in labels]
    assert list(document["smoothing"]) == labels
    assert document["interior_margin_frames"] == 60
    assert document["interior_steps"] == [60, 539]
    assert runner._interior(180, RATE) == slice(60, 119)
    for candidate in document["smoothing"].values():
        for kind in ("staged", "flat"):
            record = candidate[kind]
            offset = {"staged": 16, "flat": 28}[kind]
            assert record["interior"] == pytest.approx(24239 / 479 + offset)
            assert "per_step" not in record and "edge_free_frames" not in record


@pytest.mark.parametrize("method", ["ancuti2018", "c3"])
def test_long_crossed_trend_is_unavailable_without_rendering_or_changing_other_records(
    tmp_path, monkeypatch, pre_r1_runner, method
):
    with monkeypatch.context() as before_patches:
        before, *_ = _window_study(
            tmp_path,
            before_patches,
            8,
            long=True,
            instrument=pre_r1_runner,
            crossing_method=method,
        )
    before.pop("written")
    _take_documents(tmp_path / "work" / "synthetic")
    actual, *_ = _window_study(
        tmp_path,
        monkeypatch,
        8,
        long=True,
        crossing_method=method,
        reject_crossed_trend=True,
    )
    actual.pop("written")
    row = actual["flicker"][method].pop("linear_trend")
    assert set(row) == {"available", "reason", "crossing"}
    assert row["available"] is False
    assert row["reason"] == "fitted normalisation_bounds.low exceeds normalisation_bounds.high"
    assert set(row["crossing"]) == {"count", "frames"}
    assert row["crossing"]["count"] == 2
    assert row["crossing"]["frames"] == [
        {
            "index": 6,
            "pts_ticks": 6006,
            "pts_seconds": 6 / float(RATE),
            "low": pytest.approx(7.25),
            "high": pytest.approx(-7.25),
        },
        {
            "index": 7,
            "pts_ticks": 7007,
            "pts_seconds": 7 / float(RATE),
            "low": pytest.approx(15.5),
            "high": pytest.approx(-15.5),
        },
    ]
    before["flicker"][method].pop("linear_trend")
    assert actual == before


@pytest.mark.parametrize("method", ["ancuti2018", "c3"])
def test_default_crossed_trend_record_matches_wp14_base(tmp_path, monkeypatch, base_runner, method):
    # The signal boundary accepts the fit here so the historical default routing
    # and full payload can be compared. A guard leaked out of --long changes it.
    with monkeypatch.context() as base_patches:
        _window_study(
            tmp_path,
            base_patches,
            8,
            instrument=base_runner,
            save_analyses=True,
            crossing_method=method,
        )
    expected = _take_documents(tmp_path / "work" / "synthetic")
    _window_study(tmp_path, monkeypatch, 8, save_analyses=True, crossing_method=method)
    assert _take_documents(tmp_path / "work" / "synthetic") == expected


def test_long_ordered_trend_keeps_full_record_unchanged(tmp_path, monkeypatch, pre_r1_runner):
    with monkeypatch.context() as before_patches:
        _window_study(tmp_path, before_patches, 600, long=True, instrument=pre_r1_runner)
    expected = _take_documents(tmp_path / "work" / "synthetic")
    document, *_ = _window_study(tmp_path, monkeypatch, 600, long=True, reject_crossed_trend=True)
    assert _take_documents(tmp_path / "work" / "synthetic") == expected
    for method in ("ancuti2018", "c3"):
        assert "available" not in document["flicker"][method]["linear_trend"]
        assert len(document["flicker"][method]["linear_trend"]["per_step"]) == 599


@pytest.mark.parametrize("method", ["ancuti2018", "c3"])
def test_long_equal_trend_bounds_remain_available(tmp_path, monkeypatch, method):
    """Keep a trend with one exactly equal bound pair available for each method."""
    linear_trend = runner.temporal.linear_trend
    witnessed = []

    def trend_with_one_tie(series):
        trend = linear_trend(series)
        if series["normalisation_bounds.low"][0] == {"ancuti2018": 3, "c3": 5}[method]:
            low = trend["normalisation_bounds.low"]
            high = trend["normalisation_bounds.high"]
            # Plant an exact tie after the real fit, avoiding OLS roundoff at equality.
            high[3] = low[3]
            assert np.flatnonzero(low == high).tolist() == [3]
            witnessed.append(3)
        return trend

    monkeypatch.setattr(runner.temporal, "linear_trend", trend_with_one_tie)
    document, *_ = _window_study(tmp_path, monkeypatch, 8, long=True, reject_crossed_trend=True)
    assert witnessed == [3]
    row = document["flicker"][method]["linear_trend"]
    assert "available" not in row
    assert len(row["per_step"]) == 7
    assert row["all"] == pytest.approx(np.mean(row["per_step"]))


@pytest.mark.parametrize("count", [600, 599])
def test_long_window_study_records_both_methods_reaches_counts_and_auditable_steps(
    tmp_path, monkeypatch, count
):
    document, staged_calls, flat_calls, step_levels = _window_study(
        tmp_path, monkeypatch, count, long=True
    )
    assert set(document["smoothing"]) == {"c3", "ancuti2018"}
    assert sorted(staged_calls) == sorted(flat_calls)
    assert len(staged_calls) == len(set(staged_calls)) == 24
    # Literal radii independently derived at 30000/1001 fps, including the median's +1.
    radii = {
        "moving_average": {0.5: 7, 1.0: 14, 2.0: 29, 4.0: 59},
        "gaussian": {0.5: 7, 1.0: 14, 2.0: 29, 4.0: 59},
        "median_gaussian": {0.5: 8, 1.0: 15, 2.0: 30, 4.0: 60},
    }
    for method, stages in (("c3", 2), ("ancuti2018", 3)):
        reference = document["flicker"][method]["reference"]
        assert reference["normalisation_bounds.low"] == {"c3": 5, "ancuti2018": 3}[method]
        # Independent literal witnesses: method * series key - method * raw-reference key.
        # Ancuti: 2*11-2*3=16, 2*17-2*3=28; c3: 7*11-7*5=42, 7*17-7*5=84.
        offsets = {"ancuti2018": {"staged": 16, "flat": 28}, "c3": {"staged": 42, "flat": 84}}
        unsmoothed = document["flicker"][method]["unsmoothed"]["per_step"]
        np.testing.assert_allclose(unsmoothed, step_levels + {"ancuti2018": 40, "c3": 126}[method])
        candidates = document["smoothing"][method]
        assert len(candidates) == 12
        for kind, windows in radii.items():
            for window, radius in windows.items():
                label = f"{kind} {window:g} s"
                assert (method, label) in staged_calls
                for analysis, reach in (("staged", stages * radius), ("flat", radius)):
                    record = candidates[label][analysis]
                    assert record["reach_frames"] == reach
                    assert record["edge_free_frames"] == count - 2 * reach
                    assert record["edge_free_steps"] == count - 1 - 2 * reach
                    assert record["interior_steps"] == [reach, count - 1 - reach]
                    assert len(record["per_step"]) == count - 1
                    keyed_steps = step_levels + offsets[method][analysis]
                    np.testing.assert_allclose(record["per_step"], keyed_steps)
                    expected = float(keyed_steps[reach : count - 1 - reach].mean())
                    assert record["interior"] == pytest.approx(expected)
                    trimmed = record["per_step"][reach : count - 1 - reach]
                    assert np.mean(trimmed) == pytest.approx(record["interior"])
    # The old 60-frame margin includes marker steps; the 180-frame staged reach excludes them.
    wide = document["smoothing"]["ancuti2018"]["median_gaussian 4 s"]
    assert wide["staged"]["interior"] == pytest.approx(17.0)
    assert wide["flat"]["interior"] > 78.0
