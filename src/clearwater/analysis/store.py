"""The statistics store of one clip (IF-4), keyed by pts ticks, and its schema hash.

:class:`AnalysisStore` satisfies :class:`clearwater.interfaces.statistics.StatisticsStore`. It
is columnar: one ascending pts axis (the clip's frames) and, per stage and statistic, a float64
array with one row per frame, so a 60-minute clip's statistics stay in megabytes. Every record
is checked at ``put`` (DR-25 (1), (2), (5), (6); Y-2). ``put``, ``raw`` and ``smoothed`` take
an optional keyword-only ``schema_hash`` and refuse a different one (DR-25 (4)); IF-4 itself is
unchanged.

Threading: one writer thread (the analysis job) and any number of reader threads. Every read
and write holds the store's lock; readers get copies. The smoothing arithmetic of
:meth:`AnalysisStore.smooth` runs outside the lock on a snapshot and is written back under it.
"""

from __future__ import annotations

import hashlib
import json
import threading
from collections.abc import Mapping, Sequence
from fractions import Fraction
from typing import TYPE_CHECKING, Any

import numpy as np
from numpy.typing import NDArray

from clearwater.interfaces import CorrectionMethod, Stage, Statistics, StatisticsStore

from .smoothing import exact_window, reach, smooth_series

_NUMERIC_KINDS = "iuf"
"""NumPy dtype kinds a statistic may have: signed, unsigned, floating (Y-2, as WP3.4's methods)."""


class SchemaMismatchError(ValueError):
    """A record was offered or asked for under a schema hash other than the store's."""


def shaping_parameters(method: CorrectionMethod) -> tuple[str, ...]:
    """Return the sorted names of every parameter some stage's statistics depend on.

    Args:
        method: The correction method.

    Returns:
        The sorted union of the stages' ``depends_on_parameters``.
    """
    return tuple(sorted({name for stage in method.stages for name in stage.depends_on_parameters}))


def _canonical(value: Any) -> Any:
    """Return ``value`` with every ``int`` or ``float`` (never a ``bool``) as its ``float``.

    Lists, tuples and dicts are walked; anything else is returned unchanged.

    Raises:
        OverflowError: An ``int`` too large for a ``float``.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, list | tuple):
        return [_canonical(item) for item in value]
    if isinstance(value, dict):
        return {key: _canonical(item) for key, item in value.items()}
    return value


def same_value(first: Any, second: Any) -> bool:
    """Return True when two parameter values are equal as :func:`schema_hash` hashes them.

    Both are passed through the hash's canonical form (every number as its ``float``) and then
    compared with their types, so ``1`` equals ``1.0`` but ``True`` never equals ``1`` (Python's
    ``True == 1.0`` would say otherwise).

    Args:
        first: One value.
        second: The other value.

    Returns:
        Whether the values hash the same.

    Raises:
        OverflowError: An ``int`` too large for a ``float``.
    """
    return _same_canonical(_canonical(first), _canonical(second))


def _same_canonical(first: Any, second: Any) -> bool:
    """Compare two canonical values, their types included, at every depth."""
    if type(first) is not type(second):
        return False
    if isinstance(first, list):
        return len(first) == len(second) and all(
            _same_canonical(a, b) for a, b in zip(first, second, strict=True)
        )
    if isinstance(first, dict):
        return first.keys() == second.keys() and all(
            _same_canonical(item, second[key]) for key, item in first.items()
        )
    return bool(first == second)


def schema_hash(
    method: CorrectionMethod,
    params: Mapping[str, Any],
    kind: str,
    window_s: float | Fraction | str,
) -> str:
    """Return the schema hash of a clip's statistics (IF-4 ``schema_hash``; question 5).

    A SHA-256 hex digest over canonical JSON of the method id, the value of every parameter
    named in any stage's ``depends_on_parameters`` (sorted by name, each as ``[name, present,
    value]`` so a missing name and a ``None`` value differ), the smoothing kind and the window
    as an exact decimal. A parameter no stage depends on does not change it. Every number (an
    ``int`` or a ``float``, at any depth, never a ``bool``) is hashed as its ``float`` value, so
    values that compare equal hash equal whatever their Python type (``1`` and ``1.0``, as a
    preset read from JSON may give), while ``True`` stays distinct from ``1``.

    Args:
        method: The correction method.
        params: The effective parameter values.
        kind: The smoothing kind.
        window_s: The smoothing window in seconds.

    Returns:
        64 lowercase hex digits.

    Raises:
        ValueError: A shaping parameter's value is not JSON-representable (or not finite).
    """
    try:
        entries = [
            [name, name in params, _canonical(params.get(name))]
            for name in shaping_parameters(method)
        ]
    except OverflowError as exc:
        raise ValueError(f"a shaping parameter cannot be hashed: {exc}") from exc
    document = {
        "method": method.id,
        "parameters": entries,
        "smoothing": {"kind": kind, "window_s": str(exact_window(window_s))},
    }
    try:
        text = json.dumps(document, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"a shaping parameter cannot be hashed: {exc}") from exc
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class _Table:
    """One stage's columns: per statistic a float64 ``(capacity, *shape)`` array, plus flags."""

    def __init__(self, names: Sequence[str], capacity: int) -> None:
        self.names = tuple(names)
        self.columns: dict[str, NDArray[np.float64]] = {}
        self.raw_present = np.zeros(capacity, dtype=bool)
        self.smoothed: dict[str, NDArray[np.float64]] = {}
        self.smoothed_present = np.zeros(capacity, dtype=bool)

    def grow(self, capacity: int) -> None:
        """Enlarge every column to ``capacity`` rows."""
        for table in (self.columns, self.smoothed):
            for name, column in table.items():
                grown = np.zeros((capacity, *column.shape[1:]), dtype=np.float64)
                grown[: len(column)] = column
                table[name] = grown
        for attr in ("raw_present", "smoothed_present"):
            flags = getattr(self, attr)
            grown_flags = np.zeros(capacity, dtype=bool)
            grown_flags[: len(flags)] = flags
            setattr(self, attr, grown_flags)


class AnalysisStore:
    """Per-frame statistics of one clip, raw and smoothed, keyed by pts ticks (IF-4)."""

    def __init__(self, stages: Sequence[Stage], schema_hash: str, time_base: Fraction) -> None:
        """Create an empty store.

        Args:
            stages: The method's stages, in order.
            schema_hash: The schema hash of the current parameters (:func:`schema_hash`).
            time_base: The clip's time base (seconds per tick), for smoothing over pts.

        Raises:
            ValueError: No stages, a repeated stage name, or a non-positive time base.
        """
        if not stages:
            raise ValueError("a method needs at least one stage")
        names = [stage.name for stage in stages]
        if len(set(names)) != len(names):
            raise ValueError(f"repeated stage names: {names}")
        if time_base <= 0:
            raise ValueError(f"the time base must be positive, got {time_base}")
        self._stages = {stage.name: stage for stage in stages}
        self._order = tuple(names)
        self._time_base = Fraction(time_base)
        self._hash = schema_hash
        self._lock = threading.RLock()
        self._version = 0
        self._reset()

    def _reset(self) -> None:
        """Drop the axis, the shapes and every record."""
        self._ticks: list[int] = []
        self._row: dict[int, int] = {}
        self._capacity = 0
        self._shapes: dict[tuple[str, str], tuple[int, ...]] = {}
        self._tables = {name: _Table(self._stages[name].statistics, 0) for name in self._order}

    # --- schema ---------------------------------------------------------------------------

    @property
    def schema_hash(self) -> str:
        """The schema hash the stored records were made under (DR-25 (4))."""
        with self._lock:
            return self._hash

    @schema_hash.setter
    def schema_hash(self, value: str) -> None:
        with self._lock:
            self._hash = value

    @property
    def time_base(self) -> Fraction:
        """The clip's time base (seconds per tick)."""
        return self._time_base

    def _check_hash(self, given: str | None, what: str) -> None:
        """Refuse a schema hash other than the store's."""
        if given is not None and given != self._hash:
            raise SchemaMismatchError(
                f"{what} under schema {given[:12]}..., the store holds {self._hash[:12]}..."
            )

    def _stage(self, stage: str) -> Stage:
        """Return a stage by name; ``ValueError`` for an unknown one."""
        try:
            return self._stages[stage]
        except KeyError:
            raise ValueError(f"unknown stage {stage!r}; stages: {', '.join(self._order)}") from None

    # --- writing --------------------------------------------------------------------------

    def put(
        self, pts_ticks: int, stage: str, raw: Statistics, *, schema_hash: str | None = None
    ) -> None:
        """Store the raw statistics of one stage for one frame, after checking them (Y-2).

        A pts not yet on the axis must lie after every pts on it (frames arrive in pts order);
        a pts already on the axis may be written in any order (the recompute re-measures near
        frames first). Smoothed values are not touched: :meth:`smooth` refreshes them.

        Args:
            pts_ticks: The frame's presentation time in ticks.
            stage: The stage name.
            raw: The measured statistics: exactly the stage's statistic names, each a finite
                real host array whose shape is fixed per name for the clip.
            schema_hash: When given, the hash the record was made under.

        Raises:
            SchemaMismatchError: ``schema_hash`` differs from the store's.
            ValueError: An unknown stage; a missing or extra statistic; a non-numeric,
                complex or non-host array; a shape change; a non-finite value; a new pts not
                after the axis's last (out of order or duplicate). The message names the pts,
                the stage and the statistic.
        """
        pts = int(pts_ticks)
        with self._lock:
            self._check_hash(schema_hash, f"a record for pts {pts}, stage {stage!r}")
            declared = self._stage(stage)
            arrays = self._checked(pts, declared, raw)
            row = self._row.get(pts)
            if row is None:
                if self._ticks and pts <= self._ticks[-1]:
                    raise ValueError(
                        f"pts {pts} (stage {stage!r}) is not after the last stored pts "
                        f"{self._ticks[-1]}: frames out of order or duplicated"
                    )
                row = self._append(pts)
            table = self._tables[stage]
            for name, value in arrays.items():
                column = table.columns.get(name)
                if column is None:
                    column = np.zeros((self._capacity, *value.shape), dtype=np.float64)
                    table.columns[name] = column
                column[row] = value
            table.raw_present[row] = True
            self._version += 1

    def _checked(self, pts: int, stage: Stage, raw: Statistics) -> dict[str, NDArray[np.float64]]:
        """Return float64 copies of a record's arrays after the Y-2 checks."""
        where = f"pts {pts}, stage {stage.name!r}"
        declared = set(stage.statistics)
        given = set(raw)
        missing = sorted(declared - given)
        if missing:
            raise ValueError(f"{where}: statistic {missing[0]!r} is missing")
        extra = sorted(str(name) for name in given - declared)
        if extra:
            raise ValueError(f"{where}: statistic {extra[0]!r} is not declared by the stage")
        arrays: dict[str, NDArray[np.float64]] = {}
        for name in stage.statistics:
            try:
                value = np.asarray(raw[name])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{where}: statistic {name!r} is not a host array: {exc}") from exc
            if value.dtype.kind not in _NUMERIC_KINDS:
                raise ValueError(
                    f"{where}: statistic {name!r} has dtype {value.dtype}, not a real number"
                )
            shape = tuple(value.shape)
            known = self._shapes.get((stage.name, name))
            if known is not None and known != shape:
                raise ValueError(
                    f"{where}: statistic {name!r} has shape {shape}, earlier frames {known}"
                )
            converted = value.astype(np.float64)
            if not np.all(np.isfinite(converted)):
                raise ValueError(f"{where}: statistic {name!r} holds a non-finite value")
            arrays[name] = converted
        for name, value in arrays.items():
            self._shapes.setdefault((stage.name, name), tuple(value.shape))
        return arrays

    def _append(self, pts: int) -> int:
        """Add a pts to the end of the axis, growing the columns when full."""
        row = len(self._ticks)
        if row >= self._capacity:
            self._capacity = max(64, self._capacity * 2)
            for table in self._tables.values():
                table.grow(self._capacity)
        self._ticks.append(pts)
        self._row[pts] = row
        return row

    # --- reading --------------------------------------------------------------------------

    def _record(
        self, pts_ticks: int, stage: str, smoothed: bool, schema_hash: str | None
    ) -> dict[str, NDArray[np.float64]]:
        """Return copies of one stored record; ``KeyError`` when absent."""
        with self._lock:
            self._check_hash(schema_hash, f"a read of pts {pts_ticks}, stage {stage!r}")
            self._stage(stage)
            row = self._row.get(int(pts_ticks))
            table = self._tables[stage]
            present = table.smoothed_present if smoothed else table.raw_present
            if row is None or not present[row]:
                what = "smoothed" if smoothed else "raw"
                raise KeyError(f"no {what} statistics for pts {pts_ticks}, stage {stage!r}")
            source = table.smoothed if smoothed else table.columns
            return {name: source[name][row].copy() for name in table.names}

    def raw(
        self, pts_ticks: int, stage: str, *, schema_hash: str | None = None
    ) -> dict[str, NDArray[np.float64]]:
        """Return the raw statistics of one stage for one frame.

        Args:
            pts_ticks: The frame's presentation time in ticks.
            stage: The stage name.
            schema_hash: When given, the hash the caller expects.

        Returns:
            Copies of the stored arrays (float64).

        Raises:
            KeyError: No raw statistics are stored for that frame and stage.
            SchemaMismatchError: ``schema_hash`` differs from the store's.
            ValueError: An unknown stage.
        """
        return self._record(pts_ticks, stage, False, schema_hash)

    def smoothed(
        self, pts_ticks: int, stage: str, *, schema_hash: str | None = None
    ) -> dict[str, NDArray[np.float64]]:
        """Return the smoothed statistics of one stage for one frame.

        Every statistic of the stage is returned: the smoothed names smoothed, the others as
        measured.

        Args:
            pts_ticks: The frame's presentation time in ticks.
            stage: The stage name.
            schema_hash: When given, the hash the caller expects.

        Returns:
            Copies of the stored arrays (float64).

        Raises:
            KeyError: The frame's smoothed statistics of that stage are not available.
            SchemaMismatchError: ``schema_hash`` differs from the store's.
            ValueError: An unknown stage.
        """
        return self._record(pts_ticks, stage, True, schema_hash)

    def has_smoothed(self, pts_ticks: int, stage: str) -> bool:
        """Return True when the frame's smoothed statistics of ``stage`` are available.

        Args:
            pts_ticks: The frame's presentation time in ticks.
            stage: The stage name.

        Returns:
            Whether :meth:`smoothed` would return a record.
        """
        with self._lock:
            row = self._row.get(int(pts_ticks))
            return row is not None and bool(
                self._tables[self._stage(stage).name].smoothed_present[row]
            )

    def ensure_axis(self, ticks: Sequence[int]) -> None:
        """Put the clip's frames on the axis ahead of their records (a reopened clip).

        Pts already on the axis are skipped; the others must be ascending and after the axis's
        last pts.

        Args:
            ticks: The clip's pts ticks, ascending.

        Raises:
            ValueError: A new pts is not after the last one (out of order or duplicated).
        """
        with self._lock:
            for tick in ticks:
                pts = int(tick)
                if pts in self._row:
                    continue
                if self._ticks and pts <= self._ticks[-1]:
                    raise ValueError(
                        f"pts {pts} is not after the last stored pts {self._ticks[-1]}: "
                        "frames out of order or duplicated"
                    )
                self._append(pts)
            self._version += 1

    def raw_missing(self, stage: str) -> list[int]:
        """Return the axis pts that hold no raw record of ``stage``, ascending.

        Args:
            stage: The stage name.

        Returns:
            The pts still to be measured.

        Raises:
            ValueError: An unknown stage.
        """
        with self._lock:
            table = self._tables[self._stage(stage).name]
            n = len(self._ticks)
            return [
                t for t, held in zip(self._ticks, table.raw_present[:n], strict=True) if not held
            ]

    def smoothed_complete(self, stage: str) -> bool:
        """Return True when every axis pts holds the smoothed record of ``stage``.

        Args:
            stage: The stage name.

        Returns:
            Whether the stage is smoothed for the whole clip (False on an empty axis).

        Raises:
            ValueError: An unknown stage.
        """
        with self._lock:
            table = self._tables[self._stage(stage).name]
            n = len(self._ticks)
            return n > 0 and bool(table.smoothed_present[:n].all())

    def axis(self) -> tuple[int, ...]:
        """Return the clip's frames since the last :meth:`clear`, ascending.

        A pts joins the axis when a record is put for it or when :meth:`ensure_axis` puts the
        frames of a reopened clip ahead of their records; :meth:`all_pts` is the subset that
        holds a raw record.
        """
        with self._lock:
            return tuple(self._ticks)

    def all_pts(self) -> Sequence[int]:
        """Return every pts holding at least one raw record, ascending."""
        with self._lock:
            n = len(self._ticks)
            held = np.zeros(n, dtype=bool)
            for table in self._tables.values():
                held |= table.raw_present[:n]
            return [tick for tick, keep in zip(self._ticks, held, strict=True) if keep]

    def pts_range(self) -> tuple[int, int]:
        """Return the first and last pts holding a raw record.

        Raises:
            ValueError: Nothing is stored.
        """
        pts = self.all_pts()
        if not pts:
            raise ValueError("no statistics are stored")
        return pts[0], pts[-1]

    # --- smoothing ------------------------------------------------------------------------

    def _snapshot(
        self, stage: str, names: Sequence[str]
    ) -> tuple[_Table, list[int], NDArray[np.bool_], dict[str, NDArray[np.float64]], int]:
        """Return the stage's table, the axis, the raw flags, copies of the columns, a version."""
        declared = self._stage(stage)
        for name in names:
            if name not in declared.statistics:
                raise KeyError(f"stage {stage!r} has no statistic {name!r}")
        table = self._tables[stage]
        n = len(self._ticks)
        present = table.raw_present[:n].copy()
        columns = {name: table.columns[name][:n].copy() for name in table.columns}
        return table, list(self._ticks), present, columns, self._version

    def smooth(self, stage: str, names: Sequence[str], window_s: float, kind: str) -> None:
        """Smooth the named statistics of a stage over pts for every frame (AD-3, D95).

        Every pts on the axis must hold the stage's raw record. The stage's other statistics
        are copied to the smoothed record unchanged.

        Args:
            stage: The stage name.
            names: The statistic names to smooth (a subset of the stage's statistics).
            window_s: The full window in seconds, over pts.
            kind: The smoothing kind (:data:`clearwater.analysis.smoothing.KINDS`).

        Raises:
            KeyError: A frame lacks the stage's raw record, or a name is not the stage's.
            ValueError: An unknown stage or kind, or an unusable window.
            RuntimeError: The stage was written while it was being smoothed (two writers).
        """
        with self._lock:
            table, ticks, present, columns, version = self._snapshot(stage, names)
            if ticks and not present.all():
                missing = ticks[int(np.argmin(present))]
                raise KeyError(f"stage {stage!r} has no raw statistics for pts {missing}")
        if not ticks:
            return
        results = {
            name: smooth_series(ticks, self._time_base, columns[name], window_s, kind)
            for name in names
        }
        with self._lock:
            self._write_smoothed(table, columns, results, 0, len(ticks) - 1, version)

    def smooth_at(
        self,
        stage: str,
        names: Sequence[str],
        window_s: float,
        kind: str,
        first_pts: int,
        last_pts: int,
    ) -> None:
        """Smooth a stage only for the frames from ``first_pts`` to ``last_pts`` (AD-7).

        The recompute's near phase: only the outputs in the interval are computed, and every
        raw record they read must be stored.

        Args:
            stage: The stage name.
            names: The statistic names to smooth.
            window_s: The full window in seconds, over pts.
            kind: The smoothing kind.
            first_pts: The first output pts (on the axis).
            last_pts: The last output pts (on the axis), not before ``first_pts``.

        Raises:
            KeyError: A pts is not on the axis, a name is not the stage's, or a raw record the
                outputs read is missing.
            ValueError: An unknown stage or kind, an unusable window, or a reversed interval.
            RuntimeError: The stage was written while it was being smoothed (two writers).
        """
        with self._lock:
            table, ticks, present, columns, version = self._snapshot(stage, names)
            try:
                lo, hi = self._row[int(first_pts)], self._row[int(last_pts)]
            except KeyError as exc:
                raise KeyError(f"pts {exc.args[0]} is not on the axis") from None
        if hi < lo:
            raise ValueError(f"reversed interval {first_pts}..{last_pts}")
        if ticks:
            first, last = reach(ticks, self._time_base, window_s, kind, lo, hi)
            if not present[first : last + 1].all():
                missing = ticks[first + int(np.argmin(present[first : last + 1]))]
                raise KeyError(
                    f"stage {stage!r}: pts {first_pts}..{last_pts} read the raw record of pts "
                    f"{missing}, which is not stored"
                )
        results = {
            name: smooth_series(ticks, self._time_base, columns[name], window_s, kind, (lo, hi))
            for name in names
        }
        with self._lock:
            self._write_smoothed(table, columns, results, lo, hi, version)

    def _write_smoothed(
        self,
        table: _Table,
        columns: Mapping[str, NDArray[np.float64]],
        results: Mapping[str, NDArray[np.float64]],
        lo: int,
        hi: int,
        version: int,
    ) -> None:
        """Write smoothed rows ``lo..hi`` (the others copied from raw); caller holds the lock."""
        if version != self._version:
            raise RuntimeError("the store was written while a stage was being smoothed")
        for name in table.names:
            target = table.smoothed.get(name)
            if target is None:
                target = np.zeros_like(table.columns[name])
                table.smoothed[name] = target
            target[lo : hi + 1] = results[name] if name in results else columns[name][lo : hi + 1]
        table.smoothed_present[lo : hi + 1] = True
        self._version += 1

    # --- invalidation ---------------------------------------------------------------------

    def invalidate_from(self, stage: str) -> None:
        """Drop the raw and smoothed statistics of ``stage`` and every later stage (AD-7).

        The pts axis stays (it is the clip's frame list).

        Args:
            stage: The first stage to invalidate.

        Raises:
            ValueError: An unknown stage.
        """
        with self._lock:
            self._stage(stage)
            for name in self._order[self._order.index(stage) :]:
                table = self._tables[name]
                table.raw_present[:] = False
                table.smoothed_present[:] = False
            self._version += 1

    def clear(self) -> None:
        """Drop everything: the axis, the statistic shapes and every record (unloaded state)."""
        with self._lock:
            self._reset()
            self._version += 1


if TYPE_CHECKING:
    # mypy checks that the store matches IF-4's signatures (as interfaces/stubs.py does).
    _store: StatisticsStore = AnalysisStore((), "", Fraction(1))
