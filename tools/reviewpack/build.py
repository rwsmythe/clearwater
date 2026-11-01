"""Product-runner orchestration and viewing adapters for WP5.3 (RED skeleton)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from lookcheck.frames import OutputRoots
from lookcheck.frames import run_tool as run_tool


def check_target(path: Path, roots: OutputRoots) -> Path:
    """Refuse a pack target outside its allowed root or within footage.

    Args:
        path: Target about to be written.
        roots: Allowed and footage roots.

    Returns:
        The safe resolved path.
    """
    raise NotImplementedError("check_target")


def runner_arguments(
    sources: Sequence[Path],
    *,
    group: str,
    roots: OutputRoots,
    neutral: bool = False,
    force_cpu: bool = False,
) -> list[str]:
    """Build a headless-export CLI invocation for a group and pose.

    Args:
        sources: Original or stream-copied inputs.
        group: Commissioned group.
        roots: Pack and source roots.
        neutral: Use the photo source-view pose.
        force_cpu: Explicit CPU override, used by the tiny integration test.

    Returns:
        The subprocess argument vector without shell quoting.
    """
    raise NotImplementedError("runner_arguments")


def read_runner_record(path: Path, *, group: str, roots: OutputRoots) -> list[dict[str, Any]]:
    """Map runner facts into pack items without guessing numbered output names.

    Args:
        path: Existing runner JSON record.
        group: Group this invocation belongs to.
        roots: Pack and source roots.

    Returns:
        Name-only item results, including failed items.
    """
    raise NotImplementedError("read_runner_record")


def stream_copy_command(
    source: Path, destination: Path, *, start_s: float, duration_s: float
) -> list[str]:
    """Build the all-stream, input-seek excerpt command.

    Args:
        source: Read-only input.
        destination: Guarded excerpt target.
        start_s: Requested source start.
        duration_s: Requested excerpt length.

    Returns:
        FFmpeg subprocess arguments.
    """
    raise NotImplementedError("stream_copy_command")


def validate_stream_copy(
    source_streams: Sequence[Mapping[str, Any]], excerpt_streams: Sequence[Mapping[str, Any]]
) -> None:
    """Reject stream-count or codec-tag changes in an excerpt.

    Args:
        source_streams: Selected source stream facts.
        excerpt_streams: Selected excerpt stream facts.
    """
    raise NotImplementedError("validate_stream_copy")


def actual_excerpt_start(
    source_packets: Sequence[Mapping[str, Any]], excerpt_packets: Sequence[Mapping[str, Any]]
) -> float:
    """Match the retained first video packet back to its source timestamp.

    Args:
        source_packets: Source packet timestamps and data hashes.
        excerpt_packets: Retained excerpt packets, possibly rebased to zero.

    Returns:
        Actual retained source start in seconds.
    """
    raise NotImplementedError("actual_excerpt_start")


def prepare_excerpt(
    source: Path, *, start_s: float, duration_s: float, roots: OutputRoots
) -> dict[str, Any]:
    """Copy and validate an excerpt, falling back to the whole input on copy failure.

    Args:
        source: Read-only input.
        start_s: Planned start.
        duration_s: Planned duration.
        roots: Pack and source roots.

    Returns:
        Runtime input path, excerpt status, measured timings and any fallback text.
    """
    raise NotImplementedError("prepare_excerpt")


def extract_view_frame(
    source: Path, timestamp_s: float, destination: Path, *, roots: OutputRoots
) -> Path:
    """Decode a viewing frame using FFmpeg's default display autorotation.

    Args:
        source: Video input.
        timestamp_s: Required presentation time.
        destination: Guarded PNG target.
        roots: Pack and source roots.

    Returns:
        The oriented PNG path.
    """
    raise NotImplementedError("extract_view_frame")


def make_pair(
    source: Path,
    corrected: Path,
    destination: Path,
    *,
    roots: OutputRoots,
    force_cpu: bool = False,
) -> dict[str, Any]:
    """Render equal-display-size inputs as a side-by-side viewing-aid video.

    Args:
        source: Original video or stream-copied excerpt.
        corrected: Product output, read without modification.
        destination: Guarded pair-video target.
        roots: Pack and source roots.
        force_cpu: Use software encoding for the tiny fixture control.

    Returns:
        Oriented source, corrected and rendered pair dimensions.
    """
    raise NotImplementedError("make_pair")


def export_presets(*, roots: OutputRoots) -> dict[str, dict[str, Any]]:
    """Export both product starter presets through a pack-local preset store.

    Args:
        roots: Pack and source roots.

    Returns:
        Preset name to the product-exported AD-13 object.
    """
    raise NotImplementedError("export_presets")


def main(argv: Sequence[str] | None = None) -> int:
    """Run a review-pack stage, all stages, or a strict owner-sheet tally.

    Args:
        argv: CLI arguments, or the process arguments when absent.

    Returns:
        Zero for a valid completed command, or an instrument error status.
    """
    raise NotImplementedError("main")
