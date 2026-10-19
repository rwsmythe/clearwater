"""Scan the deep chapters for CANDIDATE frames of the three look check cases (WP1.3D).

Usage::

    uv run python tools/lookcheck/scan.py [--config FILE] [--chapters GX011589 ...] [--rescan]

Spec v0.5.3, section 12 names three cases the shallow pack could not show: gray-world on open
water, distance haze and deep-water noise. This tool PROPOSES candidate frames for them from
the eight ``SCUBA/`` chapters; the owner names what each frame shows at CP2. Nothing here
calls a frame "open water" or "haze" as a fact.

For each chapter one frame is extracted every :data:`SCAN_STEP_S` seconds from
:data:`SCAN_START_S` to the end (:func:`scan_timestamps`) at short side :data:`SCAN_SHORT_SIDE`
by FFmpeg's scaler: acceptable for RANKING, and never fed to the pipeline (the pipeline's
statistics come from an exact area mean, ``prototype.temporal.proxy``). On the display-encoded
RGB in [0, 1] each frame gets (:func:`measure_frame`):

* the depth index ``D = mean R / mean G`` (raw channel means; lower is deeper);
* the open-water fraction ``W``: the fraction of pixels whose BT.709 luma has a local standard
  deviation over a :data:`FLAT_BOX` x :data:`FLAT_BOX` box below :data:`FLAT_STD_MAX` AND whose
  blue or green exceeds red by at least :data:`WATER_MARGIN`;
* the haze index ``H``: the luma RMS contrast (standard deviation over the frame; lower is
  hazier).

A frame whose luma mean is below :data:`EXCLUDE_LUMA_LOW` or above :data:`EXCLUDE_LUMA_HIGH`
is excluded from every ranking, with the reason recorded (:func:`exclusion_reason`).

The candidates (:func:`select_candidates`) are, per case (:data:`CASES`), the best
:data:`CANDIDATES_PER_CASE` frames by the case's measure, taken in rank order subject to
:data:`CASE_MIN_SEPARATION_S` between two candidates of one chapter and
:data:`CASE_PER_CHAPTER` per chapter. Ties break by chapter name, then pts. The 8 deepest
frames overall (:func:`deepest_frames`) are WP1.4b's input.

Outputs, under ``<working folder>/wp1.3d/``: ``scan/<chapter>.json`` (the per-chapter cache),
``scan.json`` (every value, with the exclusion reasons and the distribution of ``W``) and
``deep-frames.json``. The footage folder is only ever an input. Exit status 0 on success; 2,
with a one-line ``error: ...`` on standard error, on a configuration, probe, path or FFmpeg
failure or when a case has fewer than :data:`CANDIDATES_PER_CASE` eligible frames.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import json
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy import ndimage

if not __package__:
    # Script mode (``python tools/lookcheck/scan.py``): sys.path[0] is tools/lookcheck, so put
    # the tools directory first to make the ``lookcheck`` and ``local_config`` modules importable.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from local_config import LocalConfigError, find_footage_file, load_local_config
from lookcheck.frames import (
    ExtractError,
    OutputRoots,
    extract,
    frame_stem,
    probe_stream,
    read_png16,
    tool_version,
)

SPEC_VERSION = "0.5.3"
WORK_SUBDIR = "wp1.3d"
"""The folder of the working folder that this package writes to."""

SCAN_CHAPTERS = (
    "GX011589",
    "GX011590",
    "GX011591",
    "GX011592",
    "GX011593",
    "GX011598",
    "GX011600",
    "GX011601",
)
"""The eight ``SCUBA/`` chapters (owner, CP1, 2026-10-19: ``SCUBA/`` is the deeper footage)."""

SCAN_START_S = 5.0
SCAN_STEP_S = 10.0
SCAN_END_MARGIN_S = 1.0
"""The last scan timestamp is at most this many seconds before the end of the chapter."""

SCAN_SHORT_SIDE = 540
LUMA_WEIGHTS = (0.2126, 0.7152, 0.0722)
"""BT.709 luma weights, applied to the display-encoded RGB."""

FLAT_BOX = 15
FLAT_STD_MAX = 0.01
WATER_MARGIN = 0.05
BOX_MODE = "reflect"
"""How the local standard deviation extends the frame past its edges (``scipy.ndimage``)."""

EXCLUDE_LUMA_LOW = 0.05
EXCLUDE_LUMA_HIGH = 0.95
HAZE_MAX_WATER_FRACTION = 0.5
"""Distance haze is ranked among frames whose ``W`` is below this, so open water does not take
the haze slots."""

CANDIDATES_PER_CASE = 4
CASE_MIN_SEPARATION_S = 30.0
CASE_PER_CHAPTER = 2
DEEPEST_COUNT = 8
DEEPEST_MIN_SEPARATION_S = 10.0
W_HISTOGRAM_BINS = 10
PARTIAL_BATCH = 10
"""Frames per extraction batch; after each batch the chapter's progress is saved, so that an
interrupted run resumes (``scan/<chapter>.partial.json``)."""
SCAN_SCHEMA = 1


class ScanError(Exception):
    """The scan cannot give what the brief asks for (for example too few eligible frames)."""


@dataclasses.dataclass(frozen=True)
class Measures:
    """What :func:`measure_frame` found on one frame.

    Attributes:
        luma_mean: Mean BT.709 luma, in [0, 1].
        depth_index: ``D = mean R / mean G``, or ``None`` when the green mean is zero.
        open_water: ``W``, the flat-and-blue-green fraction of the frame, in [0, 1].
        haze: ``H``, the luma standard deviation over the frame.
    """

    luma_mean: float
    depth_index: float | None
    open_water: float
    haze: float


@dataclasses.dataclass(frozen=True)
class Case:
    """One look check case and how its candidates are ranked.

    Attributes:
        name: Key used in ``deep-frames.json`` and on the page.
        label: The case as the spec's section 12 names it, for the reader.
        measure: The :class:`ScanRecord` attribute that ranks the case.
        descending: ``True`` when a higher value ranks first.
        rule: The ranking rule in words, for the page and the records.
        eligible: Extra condition on a frame (``None``: every non-excluded frame qualifies).
    """

    name: str
    label: str
    measure: str
    descending: bool
    rule: str
    eligible: Callable[[ScanRecord], bool] | None = None


@dataclasses.dataclass(frozen=True)
class ScanRecord:
    """One scanned frame: where it is, what was measured and whether it is excluded.

    Attributes:
        chapter: The source file's stem.
        frame: The frame's file stem (``<chapter>_<pts 0000.000>``), also its name at full
            resolution.
        grid_s: The scan timestamp this frame was asked for (the first frame at or after it).
        pts_ticks: The frame's exact pts in ticks of ``time_base``.
        time_base: The stream time base in seconds per tick.
        measures: The measures.
        excluded: The exclusion reason, or ``None`` when the frame takes part in rankings.
    """

    chapter: str
    frame: str
    grid_s: float
    pts_ticks: int
    time_base: Fraction
    measures: Measures
    excluded: str | None

    @property
    def pts(self) -> Fraction:
        """The exact presentation timestamp in seconds."""
        return self.pts_ticks * self.time_base

    @property
    def depth_index(self) -> float | None:
        """``D`` (see :class:`Measures`)."""
        return self.measures.depth_index

    @property
    def open_water(self) -> float:
        """``W`` (see :class:`Measures`)."""
        return self.measures.open_water

    @property
    def haze(self) -> float:
        """``H`` (see :class:`Measures`)."""
        return self.measures.haze

    def record(self) -> dict[str, Any]:
        """Return the record as a JSON-ready dictionary (the shape of ``scan.json`` entries).

        Returns:
            ``chapter``, ``frame``, ``grid_s``, the exact ``pts_ticks`` and ``time_base``,
            ``pts_seconds``, the four measures (``luma_mean``, ``D``, ``W``, ``H``) and
            ``excluded`` (the reason or ``null``).
        """
        return {
            "chapter": self.chapter,
            "frame": self.frame,
            "grid_s": self.grid_s,
            "pts_ticks": self.pts_ticks,
            "time_base": f"{self.time_base.numerator}/{self.time_base.denominator}",
            "pts_seconds": float(self.pts),
            "luma_mean": self.measures.luma_mean,
            "D": self.measures.depth_index,
            "W": self.measures.open_water,
            "H": self.measures.haze,
            "excluded": self.excluded,
        }

    @classmethod
    def from_record(cls, entry: Mapping[str, Any]) -> ScanRecord:
        """Rebuild a record from :meth:`record`'s dictionary (the per-chapter cache).

        Args:
            entry: A dictionary written by :meth:`record`.

        Returns:
            The record.
        """
        numerator, denominator = str(entry["time_base"]).split("/")
        return cls(
            chapter=str(entry["chapter"]),
            frame=str(entry["frame"]),
            grid_s=float(entry["grid_s"]),
            pts_ticks=int(entry["pts_ticks"]),
            time_base=Fraction(int(numerator), int(denominator)),
            measures=Measures(
                luma_mean=float(entry["luma_mean"]),
                depth_index=None if entry["D"] is None else float(entry["D"]),
                open_water=float(entry["W"]),
                haze=float(entry["H"]),
            ),
            excluded=None if entry["excluded"] is None else str(entry["excluded"]),
        )


def _not_open_water(record: ScanRecord) -> bool:
    """The distance haze eligibility: ``W`` below :data:`HAZE_MAX_WATER_FRACTION`."""
    return record.open_water < HAZE_MAX_WATER_FRACTION


CASES: tuple[Case, ...] = (
    Case(
        "deep-water-noise",
        "Deep-water noise",
        "depth_index",
        False,
        "candidate (lowest D)",
    ),
    Case(
        "open-blue-water",
        "Open blue water: gray-world on open water",
        "open_water",
        True,
        "candidate (highest W)",
    ),
    Case(
        "distance-haze",
        "Distance haze",
        "haze",
        False,
        f"candidate (lowest H among frames with W below {HAZE_MAX_WATER_FRACTION:g})",
        _not_open_water,
    ),
)
"""The three cases, in the order of the page. Ranking is by the named measure."""


# --- measures -------------------------------------------------------------------------------------


def scan_timestamps(duration_s: float) -> list[float]:
    """Return the scan timestamps of a chapter: every 10 s from 5 s to the end.

    Args:
        duration_s: The chapter duration in seconds.

    Returns:
        ``5, 15, 25, ...`` up to the last one that is at most :data:`SCAN_END_MARGIN_S` before
        the end (so that a frame exists at or after it).
    """
    out: list[float] = []
    moment = SCAN_START_S
    while moment <= duration_s - SCAN_END_MARGIN_S:
        out.append(moment)
        moment += SCAN_STEP_S
    return out


def luma_of(image: NDArray[np.float32]) -> NDArray[np.float64]:
    """Return the BT.709 luma of a display-encoded RGB image, float64.

    Args:
        image: The image, shape ``(H, W, 3)``.

    Returns:
        The luma, shape ``(H, W)``.
    """
    weights = np.array(LUMA_WEIGHTS, dtype=np.float64)
    out: NDArray[np.float64] = image.astype(np.float64) @ weights
    return out


def local_std(plane: NDArray[np.float64], box: int = FLAT_BOX) -> NDArray[np.float64]:
    """Return the standard deviation of a plane over a ``box`` x ``box`` window at each pixel.

    ``sqrt(E[x^2] - E[x]^2)`` with the box means of ``scipy.ndimage.uniform_filter`` in float64
    (:data:`BOX_MODE` at the edges), the variance clipped at zero against rounding.

    Args:
        plane: A 2-D float64 array.
        box: The window side in pixels.

    Returns:
        The local standard deviation, same shape.
    """
    mean = ndimage.uniform_filter(plane, size=box, mode=BOX_MODE)
    mean_square = ndimage.uniform_filter(plane * plane, size=box, mode=BOX_MODE)
    out: NDArray[np.float64] = np.sqrt(np.maximum(mean_square - mean * mean, 0.0))
    return out


def measure_frame(image: NDArray[np.float32]) -> Measures:
    """Compute ``D``, ``W``, ``H`` and the luma mean of one frame (module docstring).

    Args:
        image: The display-encoded RGB frame, float32 in [0, 1], shape ``(H, W, 3)``.

    Returns:
        The measures.
    """
    rgb = image.astype(np.float64)
    luma = luma_of(image)
    mean_r, mean_g = float(rgb[..., 0].mean()), float(rgb[..., 1].mean())
    flat = local_std(luma) < FLAT_STD_MAX
    bluish = np.maximum(rgb[..., 1], rgb[..., 2]) - rgb[..., 0] >= WATER_MARGIN
    return Measures(
        luma_mean=float(luma.mean()),
        depth_index=mean_r / mean_g if mean_g > 0.0 else None,
        open_water=float(np.mean(flat & bluish)),
        haze=float(luma.std()),
    )


def exclusion_reason(measures: Measures) -> str | None:
    """Return why a frame is excluded from every ranking, or ``None`` if it is not.

    Args:
        measures: The frame's measures.

    Returns:
        A reason naming the measure and the bound, or ``None``.
    """
    if measures.luma_mean < EXCLUDE_LUMA_LOW:
        return f"luma mean {measures.luma_mean:.4f} is below {EXCLUDE_LUMA_LOW}"
    if measures.luma_mean > EXCLUDE_LUMA_HIGH:
        return f"luma mean {measures.luma_mean:.4f} is above {EXCLUDE_LUMA_HIGH}"
    if measures.depth_index is None:
        return "green mean is zero (D is undefined)"
    return None


def scan_record(
    chapter: str, grid_s: float, pts_ticks: int, time_base: Fraction, image: NDArray[np.float32]
) -> ScanRecord:
    """Measure one frame and wrap the result with its place and exclusion.

    Args:
        chapter: The source file's stem.
        grid_s: The scan timestamp the frame was asked for.
        pts_ticks: The frame's exact pts in ticks of ``time_base``.
        time_base: The stream time base.
        image: The frame, float32 RGB in [0, 1].

    Returns:
        The record.
    """
    measures = measure_frame(image)
    return ScanRecord(
        chapter=chapter,
        frame=frame_stem(chapter, float(pts_ticks * time_base)),
        grid_s=grid_s,
        pts_ticks=pts_ticks,
        time_base=time_base,
        measures=measures,
        excluded=exclusion_reason(measures),
    )


# --- candidates -----------------------------------------------------------------------------------


def _sort_key(
    measure: str, descending: bool
) -> Callable[[ScanRecord], tuple[float, str, Fraction]]:
    """The ranking key: the measure (negated when higher ranks first), then chapter, then pts."""

    def key(record: ScanRecord) -> tuple[float, str, Fraction]:
        value = getattr(record, measure)
        return (-value if descending else value, record.chapter, record.pts)

    return key


def ranked(records: Sequence[ScanRecord], case: Case) -> list[ScanRecord]:
    """Return a case's eligible frames in rank order.

    Excluded frames never take part. Ties break by chapter name, then pts (ascending).

    Args:
        records: Every scanned frame.
        case: The case.

    Returns:
        The eligible frames, best first.
    """
    pool = [
        record
        for record in records
        if record.excluded is None and (case.eligible is None or case.eligible(record))
    ]
    return sorted(pool, key=_sort_key(case.measure, case.descending))


def pick(
    order: Sequence[ScanRecord],
    count: int,
    min_separation_s: float,
    per_chapter: int | None,
) -> list[ScanRecord]:
    """Take the best frames of a ranking that respect the spacing and per-chapter limits.

    Walks ``order`` and keeps a frame unless its chapter already has ``per_chapter`` of the
    kept frames or a kept frame of the same chapter has a scan timestamp (``grid_s``) less than
    ``min_separation_s`` away. The spacing is measured on the scan grid, not on the pts: the
    frames of one chapter are the first frames at or after grid points, so their pts differ from
    the grid by up to one frame period, which would make "30 s apart" depend on that jitter.
    Frames of different chapters are different recordings, so their times are not compared.

    Args:
        order: The ranking, best first.
        count: How many to take at most.
        min_separation_s: The least distance, on the scan grid, between two kept frames of one
            chapter.
        per_chapter: The most frames per chapter (``None``: no limit).

    Returns:
        The kept frames, in rank order (fewer than ``count`` if the ranking runs out).
    """
    kept: list[ScanRecord] = []
    for record in order:
        if len(kept) == count:
            break
        same = [other for other in kept if other.chapter == record.chapter]
        if per_chapter is not None and len(same) >= per_chapter:
            continue
        if any(abs(other.grid_s - record.grid_s) < min_separation_s for other in same):
            continue
        kept.append(record)
    return kept


def select_candidates(records: Sequence[ScanRecord]) -> dict[str, list[ScanRecord]]:
    """Pick the candidates of every case (module docstring).

    Args:
        records: Every scanned frame.

    Returns:
        Case name to its :data:`CANDIDATES_PER_CASE` candidates, best first.

    Raises:
        ScanError: A case has fewer than :data:`CANDIDATES_PER_CASE` frames that satisfy the
            rules (the bar is not lowered).
    """
    out: dict[str, list[ScanRecord]] = {}
    for case in CASES:
        chosen = pick(
            ranked(records, case), CANDIDATES_PER_CASE, CASE_MIN_SEPARATION_S, CASE_PER_CHAPTER
        )
        if len(chosen) < CANDIDATES_PER_CASE:
            raise ScanError(
                f"case {case.name}: only {len(chosen)} of {CANDIDATES_PER_CASE} candidates "
                "satisfy the spacing, per-chapter and exclusion rules"
            )
        out[case.name] = chosen
    return out


def deepest_frames(records: Sequence[ScanRecord]) -> list[ScanRecord]:
    """Return the :data:`DEEPEST_COUNT` deepest frames overall (lowest ``D``).

    The only spacing rule is :data:`DEEPEST_MIN_SEPARATION_S` between two frames of one chapter;
    there is no per-chapter limit. This is WP1.4b's input.

    Args:
        records: Every scanned frame.

    Returns:
        The frames, deepest first.

    Raises:
        ScanError: Fewer than :data:`DEEPEST_COUNT` frames qualify.
    """
    case = CASES[0]
    chosen = pick(ranked(records, case), DEEPEST_COUNT, DEEPEST_MIN_SEPARATION_S, None)
    if len(chosen) < DEEPEST_COUNT:
        raise ScanError(f"only {len(chosen)} of {DEEPEST_COUNT} deepest frames are available")
    return chosen


def serving_cases(candidates: Mapping[str, Sequence[ScanRecord]]) -> dict[str, list[str]]:
    """Return, per frame that is a candidate, the cases it is a candidate for (in case order).

    Args:
        candidates: The result of :func:`select_candidates`.

    Returns:
        Frame stem to the case names; a frame serving two cases has two names.
    """
    out: dict[str, list[str]] = {}
    for case in CASES:
        for record in candidates.get(case.name, ()):
            out.setdefault(record.frame, []).append(case.name)
    return out


def _entry(rank: int, record: ScanRecord, serves: Sequence[str]) -> dict[str, Any]:
    """One ranked entry of ``deep-frames.json``."""
    return {
        "rank": rank,
        "chapter": record.chapter,
        "frame": record.frame,
        "pts_ticks": record.pts_ticks,
        "time_base": f"{record.time_base.numerator}/{record.time_base.denominator}",
        "pts_seconds": float(record.pts),
        "grid_s": record.grid_s,
        "D": record.measures.depth_index,
        "W": record.measures.open_water,
        "H": record.measures.haze,
        "luma_mean": record.measures.luma_mean,
        "serves_cases": list(serves),
    }


def deep_frames_document(records: Sequence[ScanRecord], written: str) -> dict[str, Any]:
    """Build ``deep-frames.json``: the ranked candidates per case and the 8 deepest frames.

    Keys: ``schema``, ``spec``, ``written``, ``note`` (these are CANDIDATES), ``rules``,
    ``cases`` (case name to ``label``, ``rule`` and ``frames``, each frame with ``rank``,
    ``chapter``, ``frame``, ``pts_ticks``, ``time_base``, ``pts_seconds``, ``grid_s``, ``D``,
    ``W``, ``H``, ``luma_mean`` and ``serves_cases``) and ``deepest`` (the same entries, deepest
    first, ``serves_cases`` listing the cases the frame is also a candidate for).

    Args:
        records: Every scanned frame.
        written: The timestamp to record.

    Returns:
        The document.

    Raises:
        ScanError: A case or the deepest list cannot be filled.
    """
    candidates = select_candidates(records)
    serves = serving_cases(candidates)
    deepest = deepest_frames(records)
    return {
        "schema": SCAN_SCHEMA,
        "spec": SPEC_VERSION,
        "written": written,
        "note": "CANDIDATES proposed by the scan; the owner decides at CP2 what each shows",
        "rules": rules_record(),
        "cases": {
            case.name: {
                "label": case.label,
                "rule": case.rule,
                "frames": [
                    _entry(rank, record, serves[record.frame])
                    for rank, record in enumerate(candidates[case.name], start=1)
                ],
            }
            for case in CASES
        },
        "deepest": [
            _entry(rank, record, serves.get(record.frame, []))
            for rank, record in enumerate(deepest, start=1)
        ],
    }


def rules_record() -> dict[str, Any]:
    """Return the scan's fixed thresholds and rules as a JSON-ready dictionary."""
    return {
        "scan": {
            "start_s": SCAN_START_S,
            "step_s": SCAN_STEP_S,
            "end_margin_s": SCAN_END_MARGIN_S,
            "short_side": SCAN_SHORT_SIDE,
            "scaler": "FFmpeg (for ranking only; never fed to the pipeline)",
        },
        "luma_weights": list(LUMA_WEIGHTS),
        "open_water": {
            "box": FLAT_BOX,
            "box_mode": BOX_MODE,
            "luma_local_std_below": FLAT_STD_MAX,
            "blue_or_green_exceeds_red_by_at_least": WATER_MARGIN,
        },
        "exclusion": {
            "luma_mean_below": EXCLUDE_LUMA_LOW,
            "luma_mean_above": EXCLUDE_LUMA_HIGH,
        },
        "candidates": {
            "per_case": CANDIDATES_PER_CASE,
            "min_separation_s": CASE_MIN_SEPARATION_S,
            "separation_measured_on": "the scan grid, within one chapter",
            "per_chapter_per_case": CASE_PER_CHAPTER,
            "haze_eligible_below_W": HAZE_MAX_WATER_FRACTION,
            "ties": "chapter name, then pts, ascending",
            "rules": {case.name: case.rule for case in CASES},
        },
        "deepest": {"count": DEEPEST_COUNT, "min_separation_s": DEEPEST_MIN_SEPARATION_S},
    }


def water_histogram(records: Sequence[ScanRecord]) -> dict[str, Any]:
    """Return the distribution of ``W`` over the non-excluded frames, in tenths.

    Args:
        records: Every scanned frame.

    Returns:
        ``bins`` (lower edges 0.0, 0.1, ..., 0.9; the last bin includes 1.0), ``counts`` and the
        number of frames counted.
    """
    values = np.array([r.open_water for r in records if r.excluded is None], dtype=np.float64)
    edges = np.linspace(0.0, 1.0, W_HISTOGRAM_BINS + 1)
    counts, _ = np.histogram(values, bins=edges)
    return {
        "bins": [round(float(edge), 3) for edge in edges[:-1]],
        "counts": [int(count) for count in counts],
        "frames": int(values.size),
    }


def scan_document(
    records: Sequence[ScanRecord], chapters: Mapping[str, Mapping[str, Any]], written: str
) -> dict[str, Any]:
    """Build ``scan.json``: every value, the exclusions with their reasons, the rules.

    Args:
        records: Every scanned frame, in chapter then pts order.
        chapters: Per chapter, what was probed (``duration_s``, ``frames``).
        written: The timestamp to record.

    Returns:
        The document.
    """
    return {
        "schema": SCAN_SCHEMA,
        "spec": SPEC_VERSION,
        "written": written,
        "ffmpeg": tool_version("ffmpeg"),
        "rules": rules_record(),
        "chapters": {name: dict(info) for name, info in chapters.items()},
        "excluded": [
            {"frame": r.frame, "chapter": r.chapter, "reason": r.excluded}
            for r in records
            if r.excluded is not None
        ],
        "water_histogram": water_histogram(records),
        "frames": [r.record() for r in records],
    }


# --- running the scan -----------------------------------------------------------------------------


def _json_text(document: Mapping[str, Any]) -> str:
    """Serialise ``document`` as indented JSON; NaN and infinity are errors."""
    return json.dumps(document, indent=2, allow_nan=False) + "\n"


def _now() -> str:
    """The current UTC time to the second, ISO 8601."""
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


def scan_chapter(
    video: Path,
    roots: OutputRoots,
    scan_dir: Path,
    timestamps: Sequence[float] | None = None,
) -> dict[str, Any]:
    """Extract and measure the scan frames of one chapter; write its cache file.

    The 540-pixel frames are measured and then removed again (they are only for ranking, and
    the numbers are in the cache); the cache is ``scan_dir/<chapter>.json``. Frames are taken
    in batches of :data:`PARTIAL_BATCH` and the progress is saved after each batch, so a run
    that is stopped part way resumes from the last finished batch.

    Args:
        video: The chapter (read only).
        roots: The output safety roots.
        scan_dir: The scan folder (``<working folder>/wp1.3d/scan``).
        timestamps: The scan timestamps; ``None`` (the default) is :func:`scan_timestamps` of the
            chapter's duration. A subset is for tests: the cache then holds only those frames.

    Returns:
        The cache document: ``chapter``, ``duration_s``, ``frames`` (the records).

    Raises:
        lookcheck.frames.ExtractError: A probe or decode fails.
        lookcheck.frames.OutputPathError: An output path is refused.
    """
    info = probe_stream(video)
    wanted = scan_timestamps(info.duration_s) if timestamps is None else list(timestamps)
    work = scan_dir / "frames" / video.stem
    partial = scan_dir / f"{video.stem}.partial.json"

    def document_of(records: Sequence[ScanRecord]) -> dict[str, Any]:
        return {
            "schema": SCAN_SCHEMA,
            "chapter": video.stem,
            "duration_s": info.duration_s,
            "frame_rate": f"{info.frame_rate.numerator}/{info.frame_rate.denominator}",
            "frames": [r.record() for r in records],
        }

    records: list[ScanRecord] = []
    earlier = roots.check(partial)
    if earlier.is_file():  # an interrupted run: keep the frames it finished
        done = json.loads(earlier.read_text(encoding="utf-8"))["frames"]
        records = [ScanRecord.from_record(entry) for entry in done]
    finished = {record.grid_s for record in records}
    todo = [moment for moment in wanted if moment not in finished]
    for begin in range(0, len(todo), PARTIAL_BATCH):
        batch = todo[begin : begin + PARTIAL_BATCH]
        got = extract(video, batch, work, short_side=SCAN_SHORT_SIDE, roots=roots)
        for grid, frame in zip(batch, got, strict=True):
            records.append(
                scan_record(
                    video.stem, grid, frame.pts_ticks, frame.time_base, read_png16(frame.path)
                )
            )
            roots.remove(frame.path)
        roots.write_text(partial, _json_text(document_of(records)))
    records.sort(key=lambda record: record.grid_s)
    document = document_of(records)
    roots.write_text(scan_dir / f"{video.stem}.json", _json_text(document))
    roots.remove(partial)
    return document


def load_cache(roots: OutputRoots, scan_dir: Path, chapter: str) -> dict[str, Any] | None:
    """Return a chapter's cache document, or ``None`` when there is none.

    Args:
        roots: The output safety roots.
        scan_dir: The scan folder.
        chapter: The chapter stem.

    Returns:
        The document.
    """
    path = roots.check(scan_dir / f"{chapter}.json")
    if not path.is_file():
        return None
    document: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return document


def finish(roots: OutputRoots, scan_dir: Path) -> bool:
    """Write ``scan.json`` and ``deep-frames.json`` when every chapter has a cache file.

    Args:
        roots: The output safety roots.
        scan_dir: The scan folder.

    Returns:
        ``True`` when both files were written, ``False`` when a chapter is still missing.

    Raises:
        ScanError: A case or the deepest list cannot be filled.
    """
    caches = {chapter: load_cache(roots, scan_dir, chapter) for chapter in SCAN_CHAPTERS}
    if any(cache is None for cache in caches.values()):
        return False
    records = [
        ScanRecord.from_record(entry)
        for cache in caches.values()
        if cache is not None
        for entry in cache["frames"]
    ]
    chapters = {
        name: {"duration_s": cache["duration_s"], "frames": len(cache["frames"])}
        for name, cache in caches.items()
        if cache is not None
    }
    written = _now()
    deep = deep_frames_document(records, written)
    roots.write_text(
        roots.allowed / "scan.json", _json_text(scan_document(records, chapters, written))
    )
    roots.write_text(roots.allowed / "deep-frames.json", _json_text(deep))
    return True


def main(argv: Sequence[str] | None = None) -> int:
    """Run the scan (module docstring).

    Args:
        argv: Command-line arguments; defaults to ``sys.argv[1:]``.

    Returns:
        0 on success; 2, with a one-line error on standard error, on a configuration, probe,
        path or FFmpeg failure or when a case cannot be filled.
    """
    parser = argparse.ArgumentParser(description="Scan the deep chapters for case candidates.")
    parser.add_argument("--config", type=Path, help="local configuration file")
    parser.add_argument(
        "--chapters",
        nargs="+",
        choices=SCAN_CHAPTERS,
        default=list(SCAN_CHAPTERS),
        help="chapters to (re)scan if they have no cache (default: all)",
    )
    parser.add_argument("--rescan", action="store_true", help="scan even when a cache exists")
    args = parser.parse_args(argv)
    try:
        config = load_local_config(args.config)
        roots = OutputRoots.from_config(config, subdir=WORK_SUBDIR)
        scan_dir = roots.allowed / "scan"
        began = time.monotonic()
        for chapter in args.chapters:
            if not args.rescan and load_cache(roots, scan_dir, chapter) is not None:
                print(f"{chapter}: cached", file=sys.stderr)
                continue
            video = find_footage_file(chapter, config.footage_path)
            document = scan_chapter(video, roots, scan_dir)
            print(
                f"{chapter}: {len(document['frames'])} frames in {time.monotonic() - began:.0f} s",
                file=sys.stderr,
            )
        if finish(roots, scan_dir):
            print(roots.allowed / "deep-frames.json")
        else:
            print("not every chapter is scanned yet; scan.json not written", file=sys.stderr)
    except (LocalConfigError, ExtractError, ScanError, RuntimeError, OSError, ValueError) as exc:
        print(f"error: {' '.join(str(exc).split()) or type(exc).__name__}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
