"""WP3.21 task 2: the equality oracle of the export engine (question 3, CHARC ruling Q3).

``record`` runs one product export job (:class:`clearwater.jobs.ExportEngine` over the product
collaborators, a COLD cache, encoder ``auto``, Standard) with two recording seams that change
nothing they pass on, and writes what the job produced to a reference folder:

- the method seam (a :class:`RecordingMethod` around the IF-3 method): the statistics record
  ``render`` receives for every frame, by pts (its digest and its values, exactly, as hex
  floats), and every ``analyze`` call as (stage, digest of the measured image, digest of the
  earlier records given, digest of the result) -- a multiset, so the comparison does not depend
  on the order the engine measures in;
- the sink seam (a :class:`RecordingSink` around the product sink): the SHA-256 of every
  pre-encode frame the sink receives (float32 pixels and pts), in order, and the full float32
  frame of one frame per second (every frame with ``--every-frame``) as ``.npy``;
- after the job, from its cache entry: the entry's completeness, the SHA-256 of every stored
  proxy (uint8, as read back) and the digest of every stored source statistic.

``compare`` sets a candidate's folder against a reference's. **Tier 1**: every frame digest,
statistics record, ``analyze`` call and proxy equal. **Tier 2** (AD-11's bound, a change that
alters the render arithmetic): the records, the ``analyze`` calls and the proxies still equal
(ruling Q3: tier 1 ALWAYS for them), and on every sampled frame whose digest differs the largest
absolute difference per channel at most 2e-3 and the mean absolute difference per channel at
most 2e-4; a differing frame without a sample is counted as unmeasured. Anything else **FAILS**.

The footage is reached only through ``local_config.find_footage_file`` and only read; a
``--file`` inside the footage folder is refused (use the stem). Every folder, cache, output and
the synthetic 4K clip go under the working folder (``wp3.21/oracle``); the cache and the output
are deleted after the record unless ``--keep`` is given. Nothing here is committed. Usage::

    uv run python tools/export_oracle.py record (--clip STEM | --file PATH | --synthetic-4k)
        [--method c3] [--force-cpu] [--every-frame] [--name NAME] [--keep] [--config FILE]
    uv run python tools/export_oracle.py compare REFERENCE CANDIDATE [--require-tier1]

``record`` exits 0 when the job finished ok, 1 when it failed (the folder keeps the record), 2 on
a usage, configuration or footage-lookup error. ``compare`` exits 0 for tier 1 or tier 2 (tier 1
with ``--require-tier1``), 1 otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from fractions import Fraction
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from numpy.typing import NDArray

from clearwater.cache import DiskProxyCache, cache_key
from clearwater.core import select_backend
from clearwater.interfaces import (
    CorrectionMethod,
    Frame,
    Image,
    JobResult,
    ParameterSet,
    ProbeResult,
    Settings,
    Statistics,
)
from clearwater.io.photo import PhotoReader, PhotoWriter
from clearwater.io.video import FFmpegVideoSink, FFmpegVideoSource, find_tool
from clearwater.jobs import ExportEngine
from clearwater.jobs.export_seam import ExportRequest
from clearwater.methods import available_methods
from local_config import LocalConfigError, find_footage_file, load_local_config

SUBDIR = Path("wp3.21") / "oracle"
"""Where the reference and candidate folders and the synthetic clip go, under the working
folder."""

TIER2_MAX_ABS = 2e-3
"""AD-11: the largest absolute difference per channel a tier-2 frame may show."""

TIER2_MEAN_ABS = 2e-4
"""AD-11: the mean absolute difference per channel a tier-2 frame may show."""

SYNTHETIC_4K = "synthetic-4k"
"""The clip name of the generated 4K clip (the owner's recording mode, 3840 x 2160 at 29.97)."""

SYNTHETIC_4K_SECONDS = 4
"""Its length: 120 frames, beyond c3's composed smoothing reach."""

RECORD = "oracle.json"
"""The record's file name inside a reference or candidate folder."""


class OracleError(RuntimeError):
    """A record cannot be made (an existing folder, a refused path, a clip that cannot be made)."""


# --- digests -----------------------------------------------------------------------------------


def host(pixels: Any) -> NDArray[Any]:
    """Return an array's values on the host (a CuPy array is copied down; NumPy is unchanged)."""
    get = getattr(pixels, "get", None)
    return np.asarray(get() if callable(get) and not isinstance(pixels, np.ndarray) else pixels)


def array_digest(values: Any) -> str:
    """SHA-256 of an array's dtype, shape and C-order bytes."""
    array = np.ascontiguousarray(host(values))
    digest = hashlib.sha256(f"{array.dtype.str}{array.shape}".encode("ascii"))
    digest.update(memoryview(array).cast("B"))
    return digest.hexdigest()


def record_digest(record: Mapping[str, Any]) -> str:
    """SHA-256 of a record: stage (or statistic) names in sorted order, nested, with each array.

    Args:
        record: Name -> array, or name -> such a mapping (a whole statistics record).

    Returns:
        The hex digest.
    """
    digest = hashlib.sha256()
    for name in sorted(record):
        value = record[name]
        digest.update(name.encode("utf-8") + b"\0")
        if isinstance(value, Mapping):
            digest.update(record_digest(value).encode("ascii"))
        else:
            digest.update(array_digest(value).encode("ascii"))
    return digest.hexdigest()


def record_values(record: Mapping[str, Statistics]) -> dict[str, dict[str, Any]]:
    """Return a record's values exactly: per stage and statistic, the shape and the hex floats."""
    return {
        stage: {
            name: {
                "shape": list(np.shape(value)),
                "hex": [float(x).hex() for x in np.asarray(host(value), np.float64).ravel()],
            }
            for name, value in sorted(statistics.items())
        }
        for stage, statistics in record.items()
    }


# --- the recording seams -----------------------------------------------------------------------


class RecordingMethod:
    """An IF-3 method that records what it is given and returns what the method returns.

    Attributes:
        renders: pts ticks -> (record digest, record values), one per rendered frame.
        analyses: Every ``analyze`` call as (stage, image digest, earlier digest, result digest).
        closed_forms: Every ``closed_form`` call, as ``analyses`` (the result digest or None).
        repeated_renders: pts rendered more than once (a fault the comparison reports).
    """

    def __init__(self, inner: CorrectionMethod) -> None:
        """Wrap ``inner``; its id, label, parameters and stages are this method's."""
        self._inner = inner
        self.id = inner.id
        self.label = inner.label
        self.parameters = inner.parameters
        self.stages = inner.stages
        self._lock = threading.Lock()
        self.renders: dict[int, tuple[str, dict[str, Any]]] = {}
        self.analyses: list[tuple[str, str, str, str]] = []
        self.closed_forms: list[tuple[str, str, str, str | None]] = []
        self.repeated_renders: list[int] = []

    def analyze(
        self,
        stage: str,
        image: Image,
        params: Mapping[str, Any],
        earlier: Mapping[str, Statistics],
    ) -> Statistics:
        """Measure through the wrapped method and record the call."""
        result = self._inner.analyze(stage, image, params, earlier)
        entry = (stage, array_digest(image.pixels), record_digest(earlier), record_digest(result))
        with self._lock:
            self.analyses.append(entry)
        return result

    def closed_form(
        self,
        stage: str,
        params: Mapping[str, Any],
        earlier: Mapping[str, Statistics],
        measured: Statistics,
    ) -> Statistics | None:
        """Answer through the wrapped method and record the call."""
        result = self._inner.closed_form(stage, params, earlier, measured)
        entry = (
            stage,
            record_digest(measured),
            record_digest(earlier),
            None if result is None else record_digest(result),
        )
        with self._lock:
            self.closed_forms.append(entry)
        return result

    def render(
        self, image: Image, params: Mapping[str, Any], statistics: Mapping[str, Statistics]
    ) -> Image:
        """Record the frame's statistics by pts, then render through the wrapped method."""
        pts = getattr(image, "pts_ticks", None)
        if pts is not None:
            entry = (record_digest(statistics), record_values(statistics))
            with self._lock:
                if int(pts) in self.renders:
                    self.repeated_renders.append(int(pts))
                self.renders[int(pts)] = entry
        return self._inner.render(image, params, statistics)


class RecordingSink(FFmpegVideoSink):
    """The product sink, recording the digest of every frame it is given before it writes it.

    Attributes:
        frames: (pts ticks, SHA-256 of the float32 pixels) per written frame, in order.
        samples: pts ticks -> the ``.npy`` file name of a kept frame.
        devices: The ``Frame.device`` values the sink was given (WP3.21 #2's evidence).
    """

    def __init__(self, folder: Path, every: int, *, device_backend: object | None = None) -> None:
        """Record into ``folder`` (the kept frames), keeping every ``every``-th frame.

        Args:
            folder: Where the ``.npy`` frames go (made on first use).
            every: Keep frames ``0, every, 2 * every, ...`` in write order; 1 keeps all.
            device_backend: The product sink's ``device_backend`` (AD-29; None: host only).
        """
        super().__init__(device_backend=device_backend)
        self._folder = folder
        self._every = max(1, every)
        self.frames: list[tuple[int, str]] = []
        self.samples: dict[int, str] = {}
        self.devices: set[str] = set()

    def write(self, frame: Frame) -> None:
        """Record the frame's digest (and keep it when due), then write it."""
        self.devices.add(frame.device)
        pixels = host(frame.pixels)
        pts = int(frame.pts_ticks)
        if len(self.frames) % self._every == 0:
            self._folder.mkdir(parents=True, exist_ok=True)
            name = f"{pts}.npy"
            np.save(self._folder / name, np.ascontiguousarray(pixels))
            self.samples[pts] = name
        self.frames.append((pts, array_digest(pixels)))
        super().write(frame)


class _Progress:
    """A Progress that never cancels."""

    def report(self, done: int, total: int | None, message: str) -> None:
        """Ignore a report."""

    def cancelled(self) -> bool:
        """Never cancel."""
        return False


# --- one record --------------------------------------------------------------------------------


def synthetic_4k(folder: Path) -> Path:
    """Return the synthetic 4K clip under ``folder``, generating it on first use.

    The owner's recording mode: HEVC 8-bit 4:2:0, BT.709 limited range, 3840 x 2160 at
    30000/1001 fps, :data:`SYNTHETIC_4K_SECONDS` long, with AAC sound; a moving test pattern
    whose hue turns, so the statistics change over time.

    Args:
        folder: The oracle folder.

    The clip's SHA-256 is written beside it (``.sha256``) when it is made; every later use
    checks the bytes against it, so the reference and every candidate run the same clip (a
    regenerated x265 clip is not guaranteed to be byte-identical; ruling Q-b).

    Returns:
        The clip.

    Raises:
        OracleError: FFmpeg could not make it, or the kept clip's bytes are not the recorded
            ones (or its digest file is missing).
    """
    path = folder / "clips" / f"{SYNTHETIC_4K}.mp4"
    recorded = path.with_name(f"{path.name}.sha256")
    if path.is_file():
        if not recorded.is_file():
            raise OracleError(
                f"{path} has no recorded digest ({recorded.name}); refusing to use it"
            )
        if file_sha256(path) != recorded.read_text(encoding="ascii").strip():
            raise OracleError(f"{path} is not the recorded clip (its SHA-256 differs); refusing")
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f"{path.stem}.partial.mp4")
    seconds = SYNTHETIC_4K_SECONDS
    command = [
        str(find_tool("ffmpeg")), "-nostdin", "-hide_banner", "-v", "error", "-y",
        "-f", "lavfi", "-i", f"testsrc2=size=3840x2160:rate=30000/1001:duration={seconds}",
        "-f", "lavfi", "-i", f"sine=frequency=440:sample_rate=48000:duration={seconds}",
        "-vf", "hue=h=t*40", "-c:v", "libx265", "-preset", "ultrafast",
        "-x265-params", "log-level=error", "-pix_fmt", "yuv420p",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-color_range", "tv", "-c:a", "aac", str(partial),
    ]  # fmt: skip
    done = subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True, check=False)
    if done.returncode != 0:
        partial.unlink(missing_ok=True)
        tail = done.stderr.decode("utf-8", errors="replace").strip()[-400:]
        raise OracleError(f"the synthetic 4K clip could not be made: {tail}")
    partial.replace(path)
    recorded.write_text(file_sha256(path) + "\n", encoding="ascii")
    return path


def file_sha256(path: Path) -> str:
    """Return the SHA-256 of a file's bytes (read in 8 MiB blocks)."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(8 * 1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def git_head() -> str | None:
    """Return the commit the tool runs from, or None outside a repository."""
    try:
        done = subprocess.run(
            ["git", "-C", str(Path(__file__).resolve().parent), "rev-parse", "HEAD"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if done.returncode != 0:
        return None
    return done.stdout.strip() or None


def sample_every(frame_rate: Fraction, every_frame: bool) -> int:
    """Return the sink's keep interval: 1, or one frame per second (``round(frame_rate)``)."""
    return 1 if every_frame else max(1, round(float(frame_rate)))


@dataclass(frozen=True)
class Job:
    """What one record runs.

    Attributes:
        source: The clip (read only).
        method: The method id.
        force_cpu: ``Settings.force_cpu``.
        every_frame: Keep every pre-encode frame, not one per second.
        device_frames: Build the video source and the sink with the backend the job selects
            (``device_backend``, WP3.21 #2, AD-29): device frames on the GPU backend, the host
            path on the CPU backend.
    """

    source: Path
    method: str = "c3"
    force_cpu: bool = False
    every_frame: bool = False
    device_frames: bool = False


def record_clip(
    job: Job,
    folder: Path,
    *,
    keep: bool = False,
    methods: Mapping[str, CorrectionMethod] | None = None,
) -> dict[str, Any]:
    """Run one export job of ``job.source`` and write its record into the new ``folder``.

    Args:
        job: What to run.
        folder: The record's folder; it must not exist.
        keep: Keep the cache folder and the output.
        methods: The IF-3 methods by id (the product's when None; tests plant others).

    Returns:
        The record (also written to ``folder / RECORD``).

    Raises:
        OracleError: ``folder`` exists.
    """
    try:
        folder.mkdir(parents=True)
    except FileExistsError as error:
        raise OracleError(f"{folder} exists; a record never reuses a folder") from error
    out_dir, cache_dir = folder / "out", folder / "cache"
    out_dir.mkdir()
    inner = (methods or available_methods())[job.method]
    method = RecordingMethod(inner)
    settings = Settings(output_folder=out_dir, force_cpu=job.force_cpu)
    try:
        probe: ProbeResult | None = FFmpegVideoSource().probe(job.source)
    except Exception:  # the job probes again and reports why the clip is unusable
        probe = None
    every = 1 if probe is None else sample_every(probe.video.frame_rate, job.every_frame)
    # AD-29: the source and the sink get the backend the job will select; the CPU backend has
    # no device extensions, so a --force-cpu leg stays on the host path by structure.
    device_backend = None
    if job.device_frames and probe is not None:
        device_backend, _reason = select_backend(
            settings, probe.video.height, probe.video.width, job.method
        )
    source = FFmpegVideoSource(device_backend=device_backend)
    sinks: list[RecordingSink] = []

    def sink() -> RecordingSink:
        sinks.append(RecordingSink(folder / "frames", every, device_backend=device_backend))
        return sinks[-1]

    cache = DiskProxyCache(cache_dir)
    engine = ExportEngine(
        methods={job.method: method},
        video_source=source,
        sink_factory=sink,
        photo_reader=PhotoReader(),
        photo_writer=PhotoWriter(),
        cache=cache,
        cache_key=cache_key,
        select_backend=select_backend,
    )
    parameters = ParameterSet(
        method=job.method, parameters={}, created=datetime.now(UTC), app_version="export-oracle"
    )
    began = time.perf_counter()
    result: JobResult = engine.job(ExportRequest(job.source, "video", parameters, settings))(
        _Progress()
    )
    wall = time.perf_counter() - began
    key = cache_key(job.source)
    entry = cache.lookup(key)
    proxies: dict[str, str] = {}
    source_statistics: dict[str, dict[str, str]] = {}
    if entry is not None:
        for pts in entry.pts_ticks:
            proxies[str(pts)] = array_digest(cache.proxy(key, pts))
        for stage in method.stages:
            if stage.source_only and stage.name in entry.stages:
                source_statistics[stage.name] = {
                    str(pts): record_digest(cache.source_statistics(key, stage.name, pts))
                    for pts in entry.pts_ticks
                }
    cache.close()
    recorder = sinks[-1] if sinks else None
    stat = job.source.stat()
    record: dict[str, Any] = {
        "clip": job.source.name,
        "source_bytes": stat.st_size,
        "source_mtime_ns": stat.st_mtime_ns,
        "method": job.method,
        "force_cpu": job.force_cpu,
        "device_frames": job.device_frames,
        "device": result.device,
        "git_head": git_head(),
        "made": datetime.now(UTC).isoformat(),
        "ok": result.ok,
        "failure": result.failure,
        "wall_s": wall,
        "sample_every": every,
        "frames": [[pts, digest] for pts, digest in (recorder.frames if recorder else [])],
        "samples": {str(pts): name for pts, name in (recorder.samples if recorder else {}).items()},
        "sink_devices": sorted(recorder.devices) if recorder else [],
        "renders": {
            str(pts): {"digest": digest, "values": values}
            for pts, (digest, values) in sorted(method.renders.items())
        },
        "repeated_renders": method.repeated_renders,
        "analyses": sorted([list(entry_) for entry_ in method.analyses]),
        "closed_forms": sorted([list(entry_) for entry_ in method.closed_forms], key=str),
        "cache_complete": entry is not None and entry.complete,
        "proxies": proxies,
        "source_statistics": source_statistics,
        "outputs": [str(path) for path in result.outputs] if keep else [],
    }
    (folder / RECORD).write_text(json.dumps(record, indent=1), encoding="utf-8")
    if not keep:
        shutil.rmtree(cache_dir, ignore_errors=True)
        shutil.rmtree(out_dir, ignore_errors=True)
    return record


# --- the comparison ----------------------------------------------------------------------------


def load(folder: Path) -> dict[str, Any]:
    """Read a folder's record."""
    data: dict[str, Any] = json.loads((folder / RECORD).read_text(encoding="utf-8"))
    return data


def frame_difference(reference: NDArray[Any], candidate: NDArray[Any]) -> dict[str, list[float]]:
    """Return the per-channel largest and mean absolute differences of two frames (float64)."""
    if reference.shape != candidate.shape:
        raise ValueError(f"frame shapes differ: {reference.shape} against {candidate.shape}")
    difference = np.abs(reference.astype(np.float64) - candidate.astype(np.float64))
    axes = tuple(range(difference.ndim - 1))
    return {
        "max_abs": [float(x) for x in difference.max(axis=axes)],
        "mean_abs": [float(x) for x in difference.mean(axis=axes)],
    }


def compare(reference_dir: Path, candidate_dir: Path) -> dict[str, Any]:
    """Compare a candidate's record with a reference's (tier 1, tier 2 or fail).

    Args:
        reference_dir: The reference folder.
        candidate_dir: The candidate folder.

    Returns:
        ``verdict`` (``"TIER1"``, ``"TIER2"`` or ``"FAIL"``), the ``reasons`` for a fail, the
        frame counts (``frames``, ``frames_differing``, ``frames_measured``,
        ``frames_unmeasured``), the largest per-channel figures over the measured frames
        (``max_abs``, ``mean_abs``) and the first differing pts.
    """
    ref, cand = load(reference_dir), load(candidate_dir)
    reasons: list[str] = []
    for field in ("clip", "source_bytes", "method", "force_cpu"):
        if ref[field] != cand[field]:
            reasons.append(f"{field} differs: {ref[field]!r} against {cand[field]!r}")
    if ref["device"].split(":")[0] != cand["device"].split(":")[0]:
        reasons.append(f"device differs: {ref['device']!r} against {cand['device']!r}")
    for name, record in (("reference", ref), ("candidate", cand)):
        if not record["ok"]:
            reasons.append(f"the {name} job failed: {record['failure']}")
        if record["repeated_renders"]:
            reasons.append(f"the {name} rendered pts {record['repeated_renders'][0]} twice")
    if not cand["cache_complete"] or not ref["cache_complete"]:
        reasons.append("a cache entry is not complete")
    for field, what in (
        ("renders", "statistics records"),
        ("proxies", "proxies"),
        ("source_statistics", "source statistics"),
    ):
        if ref[field] != cand[field]:
            keys = sorted(set(ref[field]) ^ set(cand[field]))
            keys += [k for k in ref[field] if k in cand[field] and ref[field][k] != cand[field][k]]
            reasons.append(f"{what} differ (first at {keys[0] if keys else '?'})")
    if Counter(map(tuple, ref["analyses"])) != Counter(map(tuple, cand["analyses"])):
        reasons.append("the analyze calls differ (stage, image, earlier records or result)")
    if Counter(map(tuple, ref["closed_forms"])) != Counter(map(tuple, cand["closed_forms"])):
        reasons.append("the closed_form calls differ")
    ref_frames = [tuple(f) for f in ref["frames"]]
    cand_frames = [tuple(f) for f in cand["frames"]]
    if [p for p, _ in ref_frames] != [p for p, _ in cand_frames]:
        reasons.append("the written frames' pts differ (count or order)")
    differing = [pts for (pts, a), (_, b) in zip(ref_frames, cand_frames, strict=False) if a != b]
    measured: list[dict[str, Any]] = []
    unmeasured = 0
    for pts in differing:
        name_ref, name_cand = ref["samples"].get(str(pts)), cand["samples"].get(str(pts))
        if name_ref is None or name_cand is None:
            unmeasured += 1
            continue
        figures = frame_difference(
            np.load(reference_dir / "frames" / name_ref),
            np.load(candidate_dir / "frames" / name_cand),
        )
        measured.append({"pts": pts, **figures})
    max_abs = max((max(m["max_abs"]) for m in measured), default=0.0)
    mean_abs = max((max(m["mean_abs"]) for m in measured), default=0.0)
    if differing and not measured:
        # A tier-2 verdict rests on the sampled frames; with none measured it has no figure.
        reasons.append(
            f"{len(differing)} frames differ and none was measured (no sampled frame among them)"
        )
    if differing and (max_abs > TIER2_MAX_ABS or mean_abs > TIER2_MEAN_ABS):
        reasons.append(
            f"frames exceed AD-11's bound: max abs {max_abs:.3g} (limit {TIER2_MAX_ABS:g}), "
            f"mean abs {mean_abs:.3g} (limit {TIER2_MEAN_ABS:g})"
        )
    verdict = "FAIL" if reasons else ("TIER2" if differing else "TIER1")
    return {
        "verdict": verdict,
        "reasons": reasons,
        "frames": len(cand_frames),
        "frames_differing": len(differing),
        "frames_measured": len(measured),
        "frames_unmeasured": unmeasured,
        "max_abs": max_abs,
        "mean_abs": mean_abs,
        "first_differing_pts": differing[:10],
        "measured": measured[:50],
    }


# --- the command line --------------------------------------------------------------------------


def refuse_inside(path: Path, footage: Path, what: str) -> None:
    """Refuse a path that is, or lies inside, the footage folder.

    Args:
        path: The path.
        footage: The footage folder.
        what: What the path is, for the message.

    Raises:
        OracleError: It does.
    """
    targets, roots = path_forms(path), path_forms(footage)
    if any(target == root or root in target.parents for target in targets for root in roots):
        raise OracleError(f"the {what} {path} lies inside the footage folder")


def path_forms(path: Path) -> tuple[Path, Path]:
    """Return a path's lexical and resolved absolute forms, case-normalised.

    The resolved form follows symbolic links and junctions in the existing part of the path, so
    an alias of the footage folder is caught as well as its own name (Reviewer A round 1, F7).

    Args:
        path: The path.

    Returns:
        The lexical form and the resolved form.
    """
    lexical = Path(os.path.normcase(os.path.abspath(path)))
    return lexical, Path(os.path.normcase(os.path.realpath(path)))


def record_name(name: str) -> str:
    """Return ``name`` if it is a plain folder name, one path component under the output folder.

    Args:
        name: The ``--name`` value.

    Returns:
        The name.

    Raises:
        OracleError: It is empty, ``.`` or ``..``, absolute, or holds a separator or a drive.
    """
    if name in {"", ".", ".."} or Path(name).name != name or Path(name).anchor:
        raise OracleError(f"the record name {name!r} is not a plain folder name")
    return name


def summary_line(record: Mapping[str, Any]) -> str:
    """Return a record's one-line summary."""
    head = f"ORACLE {record['clip']} {record['method']} {record['device']}"
    if not record["ok"]:
        return f"{head}: FAILED {record['failure']}"
    return (
        f"{head}: {len(record['frames'])} frames, {len(record['samples'])} kept, "
        f"{len(record['renders'])} records, {len(record['analyses'])} analyze calls, "
        f"{len(record['proxies'])} proxies, complete {record['cache_complete']}, "
        f"{record['wall_s']:.1f} s"
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Record a reference or a candidate, or compare two.

    Args:
        argv: The command-line arguments (``sys.argv[1:]`` when None).

    Returns:
        The exit status.
    """
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    rec = commands.add_parser("record", help="run one job and record it")
    which = rec.add_mutually_exclusive_group(required=True)
    which.add_argument("--clip", help="footage stem, for example GX011627")
    which.add_argument("--file", type=Path, help="a clip outside the footage folder")
    which.add_argument("--synthetic-4k", action="store_true", help="the generated 4K clip")
    rec.add_argument("--method", default="c3", choices=tuple(available_methods()))
    rec.add_argument("--force-cpu", action="store_true", help="force the CPU backend")
    rec.add_argument("--every-frame", action="store_true", help="keep every pre-encode frame")
    rec.add_argument(
        "--device-frames", action="store_true", help="decode to device frames (WP3.21 #2)"
    )
    rec.add_argument("--name", help="the record folder's name (default: clip-method-device-stamp)")
    rec.add_argument("--keep", action="store_true", help="keep the cache and the output")
    rec.add_argument("--config", type=Path, help="local configuration file to read")
    cmp = commands.add_parser("compare", help="compare a candidate with a reference")
    cmp.add_argument("reference", type=Path)
    cmp.add_argument("candidate", type=Path)
    cmp.add_argument("--require-tier1", action="store_true", help="tier 2 is a failure")
    args = parser.parse_args(argv)
    if args.command == "compare":
        result = compare(args.reference, args.candidate)
        print(
            f"VERDICT {result['verdict']}: {result['frames']} frames, "
            f"{result['frames_differing']} differing ({result['frames_measured']} measured, "
            f"{result['frames_unmeasured']} unmeasured); max abs {result['max_abs']:.3g}, "
            f"mean abs {result['mean_abs']:.3g}"
        )
        for reason in result["reasons"]:
            print(f"REASON {reason}")
        passed = result["verdict"] == "TIER1" or (
            result["verdict"] == "TIER2" and not args.require_tier1
        )
        return 0 if passed else 1
    try:
        config = load_local_config(args.config)
        out_dir = config.working_path / SUBDIR
        refuse_inside(out_dir, config.footage_path, "output folder")
        if args.name is not None:
            record_name(args.name)  # refused before anything is made
        if args.clip is not None:
            source = find_footage_file(args.clip, config.footage_path)
        elif args.file is not None:
            refuse_inside(args.file, config.footage_path, "file (use --clip)")
            if not args.file.is_file():
                raise OracleError(f"{args.file} is not a file")
            source = args.file
        else:
            source = synthetic_4k(out_dir)
        device = "cpu" if args.force_cpu else "auto"
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        name = record_name(args.name or f"{source.stem}-{args.method}-{device}-{stamp}")
        folder = out_dir / name
        refuse_inside(folder, config.footage_path, "record folder")
        record = record_clip(
            Job(source, args.method, args.force_cpu, args.every_frame, args.device_frames),
            folder,
            keep=args.keep,
        )
    except (LocalConfigError, ValueError, OSError, OracleError) as error:
        print(f"ERROR {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    print(summary_line(record))
    if args.synthetic_4k:
        print(f"CLIP {source} sha256 {file_sha256(source)}")
    print(f"RECORD {folder}")
    return 0 if record["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
