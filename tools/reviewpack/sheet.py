"""Owner-review CSV writing and judgement-free tallying for WP5.3 (RED skeleton)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from lookcheck.frames import OutputRoots


def write_sheet(
    items: Sequence[Mapping[str, Any]], destination: Path, *, roots: OutputRoots
) -> Path:
    """Write or extend the review sheet without losing existing owner answers.

    Args:
        items: Persisted item results, including unreviewable states.
        destination: Guarded CSV target.
        roots: Pack and source roots.

    Returns:
        The sheet path.
    """
    raise NotImplementedError("write_sheet")


def tally(path: Path) -> dict[str, Any]:
    """Strictly read the filled CSV and count groups, headline and candidates.

    Args:
        path: Owner sheet to read without modifying it.

    Returns:
        Preference, artifact and above-surface counts with no quality verdict.
    """
    raise NotImplementedError("tally")


def format_tally(result: Mapping[str, Any]) -> str:
    """Format numeric results with D65's bar and no judgement words.

    Args:
        result: Parsed tally counts.

    Returns:
        Console-safe tally lines.
    """
    raise NotImplementedError("format_tally")
