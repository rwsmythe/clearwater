"""The statistics store (IF-4): conformance, the put checks (DR-25), schema hash, threads."""

from __future__ import annotations

import threading
from fractions import Fraction
from typing import Any

import numpy as np
import pytest

from clearwater.analysis import AnalysisStore, SchemaMismatchError, schema_hash, smooth_series
from clearwater.interfaces import StatisticsStore
from clearwater.interfaces.stubs import C3_STAGES, StubCorrectionMethod
from test_analysis_support import GrayWorld

TB = Fraction(1, 30000)


def _wb(value: float = 1.0) -> dict[str, Any]:
    return {"means": np.full(3, value), "gains": np.full(3, 2.0 * value)}


def _store() -> AnalysisStore:
    return AnalysisStore(C3_STAGES, "h1", TB)


def test_conforms_to_if4() -> None:
    """The store is an IF-4 ``StatisticsStore`` (mypy checks the signatures in ``store.py``)."""
    store = _store()
    assert isinstance(store, StatisticsStore)
    assert store.schema_hash == "h1"


@pytest.mark.parametrize(
    ("record", "match"),
    [
        ({"means": np.zeros(3)}, r"pts 7, stage 'white_balance': statistic 'gains' is missing"),
        ({**_wb(), "extra": np.zeros(1)}, r"statistic 'extra' is not declared"),
        (
            {"means": np.zeros(3), "gains": np.array([1.0, np.nan, 1.0])},
            r"'gains' holds a non-finite",
        ),
        (
            {"means": np.zeros(3), "gains": np.array([1.0, np.inf, 1.0])},
            r"'gains' holds a non-finite",
        ),
        ({"means": np.zeros(3), "gains": np.zeros(3, complex)}, r"'gains' has dtype complex"),
        ({"means": np.zeros(3), "gains": np.array(["a", "b", "c"])}, r"'gains' has dtype"),
        (
            {"means": np.zeros(3), "gains": np.array([True, False, True])},
            r"pts 7, stage 'white_balance': statistic 'gains' has dtype bool",
        ),
    ],
)
def test_put_refuses_a_bad_record_by_name(record: dict[str, Any], match: str) -> None:
    """DR-25 (1), (2), (5), (6): missing, extra, non-finite and non-real values are refused."""
    store = _store()
    with pytest.raises(ValueError, match=match):
        store.put(7, "white_balance", record)
    assert store.all_pts() == []


def test_put_accepts_integer_records() -> None:
    """Y-2's dtype rule is signed, unsigned or floating ("iuf"); integers are stored as float64."""
    store = _store()
    store.put(0, "white_balance", {"means": np.arange(3), "gains": np.ones(3, np.uint8)})
    record = store.raw(0, "white_balance")
    assert record["means"].dtype == np.float64 and record["means"].tolist() == [0.0, 1.0, 2.0]
    assert record["gains"].tolist() == [1.0, 1.0, 1.0]


def test_put_refuses_a_shape_change_even_after_invalidation() -> None:
    """A statistic's shape is fixed for the clip (DR-25 (2))."""
    store = _store()
    store.put(0, "white_balance", _wb())
    with pytest.raises(
        ValueError, match=r"pts 1001, stage 'white_balance': statistic 'means' has shape \(4,\)"
    ):
        store.put(1001, "white_balance", {"means": np.zeros(4), "gains": np.zeros(3)})
    store.invalidate_from("white_balance")
    with pytest.raises(ValueError, match="has shape"):
        store.put(1001, "white_balance", {"means": np.zeros(4), "gains": np.zeros(3)})


def test_put_refuses_unknown_stage_and_out_of_order_frames() -> None:
    """New pts must come in order; known pts may be rewritten in any order."""
    store = _store()
    with pytest.raises(ValueError, match="unknown stage 'nope'"):
        store.put(0, "nope", {})
    store.put(1001, "white_balance", _wb())
    store.put(2002, "white_balance", _wb())
    with pytest.raises(ValueError, match="not after the last stored pts 2002"):
        store.put(0, "white_balance", _wb())
    store.put(1001, "white_balance", _wb(3.0))  # a known pts, any order
    assert store.raw(1001, "white_balance")["means"].tolist() == [3.0, 3.0, 3.0]


def test_records_are_copies_and_float64() -> None:
    """Integer input is stored as float64; returned arrays are copies."""
    store = _store()
    gains = np.array([1, 2, 3])
    store.put(0, "white_balance", {"means": np.zeros(3, np.float32), "gains": gains})
    gains[0] = 99
    first = store.raw(0, "white_balance")
    assert first["gains"].dtype == np.float64 and first["gains"].tolist() == [1.0, 2.0, 3.0]
    first["gains"][0] = 42
    assert store.raw(0, "white_balance")["gains"][0] == 1.0
    with pytest.raises(KeyError):
        store.raw(0, "fusion")
    with pytest.raises(KeyError):
        store.smoothed(0, "white_balance")


def test_invalidate_from_drops_the_stage_and_every_later_one() -> None:
    """``invalidate_from`` drops raw and smoothed of the stage and later ones; the axis stays."""
    store = _store()
    for pts in (0, 1001):
        store.put(pts, "white_balance", _wb())
        store.put(pts, "fusion", {"bounds": np.zeros(2), "saliency_means": np.zeros((2, 3))})
    store.smooth("white_balance", ("means", "gains"), 2.0, "median_gaussian")
    store.invalidate_from("fusion")
    assert store.smoothed(0, "white_balance")["means"].tolist() == [1.0] * 3
    with pytest.raises(KeyError):
        store.raw(0, "fusion")
    store.invalidate_from("white_balance")
    with pytest.raises(KeyError):
        store.smoothed(0, "white_balance")
    assert store.all_pts() == []
    assert store.axis() == (0, 1001)
    with pytest.raises(ValueError, match="no statistics"):
        store.pts_range()
    store.put(1001, "white_balance", _wb())  # the axis survives: any order
    store.put(0, "white_balance", _wb())
    assert store.pts_range() == (0, 1001)
    with pytest.raises(ValueError, match="unknown stage"):
        store.invalidate_from("nope")


def test_smooth_over_pts_and_the_unsmoothed_names_are_copied() -> None:
    """``smooth`` smooths the named statistics over pts; other names are copied unchanged."""
    store = _store()
    rng = np.random.default_rng(0)
    raw = rng.normal(size=(50, 3))
    ticks = np.arange(50) * 1001
    for pts, value in zip(ticks, raw, strict=True):
        store.put(int(pts), "white_balance", {"means": value, "gains": value * 2})
    store.smooth("white_balance", ("means",), 2.0, "median_gaussian")
    expected = smooth_series(ticks, TB, raw, 2.0, "median_gaussian")
    got = np.array([store.smoothed(int(p), "white_balance")["means"] for p in ticks])
    assert np.array_equal(got, expected)
    assert np.array_equal(store.smoothed(int(ticks[3]), "white_balance")["gains"], raw[3] * 2)
    with pytest.raises(KeyError, match="no statistic 'bounds'"):
        store.smooth("white_balance", ("bounds",), 2.0, "median_gaussian")
    with pytest.raises(KeyError, match="no raw statistics for pts 0"):
        store.smooth("fusion", ("bounds",), 2.0, "median_gaussian")
    with pytest.raises(ValueError, match="unknown smoothing kind"):
        store.smooth("white_balance", ("means",), 2.0, "box")


def test_smooth_at_needs_the_whole_reach_and_matches_smooth() -> None:
    """The near phase's partial smoothing refuses a missing reach and equals the full result."""
    store = _store()
    ticks = [int(t) for t in np.arange(200) * 1001]
    rng = np.random.default_rng(1)
    values = rng.normal(size=(200, 3))
    for pts, value in zip(ticks, values, strict=True):
        store.put(pts, "white_balance", {"means": value, "gains": value})
    store.invalidate_from("white_balance")
    for index in range(70, 131):  # +-30 around 100: the reach of the output 100 alone
        store.put(ticks[index], "white_balance", {"means": values[index], "gains": values[index]})
    store.smooth_at(
        "white_balance", ("means", "gains"), 2.0, "median_gaussian", ticks[100], ticks[100]
    )
    with pytest.raises(KeyError, match="not stored"):
        store.smooth_at("white_balance", ("means",), 2.0, "median_gaussian", ticks[99], ticks[100])
    near = store.smoothed(ticks[100], "white_balance")["means"]
    with pytest.raises(KeyError):
        store.smoothed(ticks[99], "white_balance")
    full = smooth_series(ticks, TB, values, 2.0, "median_gaussian")
    assert np.array_equal(near, full[100])


def test_schema_hash_mismatch_is_refused() -> None:
    """DR-25 (4): a put or a read under another hash is refused."""
    store = _store()
    store.put(0, "white_balance", _wb(), schema_hash="h1")
    with pytest.raises(SchemaMismatchError):
        store.put(1001, "white_balance", _wb(), schema_hash="h2")
    with pytest.raises(SchemaMismatchError):
        store.raw(0, "white_balance", schema_hash="h2")
    store.smooth("white_balance", ("means", "gains"), 2.0, "median_gaussian")
    with pytest.raises(SchemaMismatchError):
        store.smoothed(0, "white_balance", schema_hash="h2")
    assert store.smoothed(0, "white_balance", schema_hash="h1")["means"].shape == (3,)
    store.schema_hash = "h2"
    with pytest.raises(SchemaMismatchError):
        store.raw(0, "white_balance", schema_hash="h1")


def test_schema_hash_binds_shaping_parameters_and_the_smoother() -> None:
    """Question 5: the hash changes with each shaping parameter and the smoother, not others."""
    method = GrayWorld()
    params = {"strength": 1.0, "gamma": 1.0, "unused": 0.0}
    base = schema_hash(method, params, "median_gaussian", 2.0)
    assert len(base) == 64 and int(base, 16) >= 0
    assert schema_hash(method, {**params, "strength": 0.5}, "median_gaussian", 2.0) != base
    assert schema_hash(method, {**params, "gamma": 2.0}, "median_gaussian", 2.0) != base
    assert schema_hash(method, {**params, "unused": 0.7}, "median_gaussian", 2.0) == base
    assert schema_hash(method, params, "median_bilateral", 2.0) != base
    assert schema_hash(method, params, "median_gaussian", 1.0) != base
    assert schema_hash(method, params, "median_gaussian", "2") == base
    missing = {"gamma": 1.0}
    none = {"gamma": 1.0, "strength": None}
    assert schema_hash(method, missing, "median_gaussian", 2.0) != schema_hash(
        method, none, "median_gaussian", 2.0
    )
    stub = StubCorrectionMethod()
    assert schema_hash(stub, {}, "median_gaussian", 2.0) != base
    with pytest.raises(ValueError, match="cannot be hashed"):
        schema_hash(method, {**params, "strength": float("nan")}, "median_gaussian", 2.0)


def test_one_writer_and_reader_threads() -> None:
    """One writer putting and smoothing while readers read raw, smoothed and the axis."""
    store = _store()
    stop = threading.Event()
    errors: list[BaseException] = []

    def reader() -> None:
        try:
            while not stop.is_set():
                axis = store.axis()
                if axis:
                    try:
                        record = store.smoothed(axis[len(axis) // 2], "white_balance")
                        assert record["means"].shape == (3,)
                    except KeyError:
                        pass
                    store.raw(axis[0], "white_balance")
                store.all_pts()
        except BaseException as exc:
            errors.append(exc)

    readers = [threading.Thread(target=reader) for _ in range(3)]
    for thread in readers:
        thread.start()
    try:
        for index in range(400):
            store.put(index * 1001, "white_balance", _wb(index))
            if index % 50 == 49:
                store.smooth("white_balance", ("means", "gains"), 2.0, "median_gaussian")
    finally:
        stop.set()
        for thread in readers:
            thread.join(10)
    assert not errors
    assert len(store.axis()) == 400
