"""The input filter that excludes camera sidecars (WP3.7, D83, AD-19).

GoPro writes a low-resolution proxy (``.LRV``) and a thumbnail (``.THM``) beside each recording.
They are not inputs. The match is on the extension alone, case-insensitive, and never opens the
file.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from clearwater.interfaces.video import Fault

SIDECAR_SUFFIXES = frozenset({".lrv", ".thm"})
"""The lower-case extensions of the sidecar files that are excluded from input (D83)."""


@dataclass(frozen=True)
class InputSelection:
    """The result of filtering candidate input paths.

    Attributes:
        inputs: The paths that remain inputs, in the order given.
        excluded: Each excluded sidecar with its ``sidecar`` fault, in the order given.
    """

    inputs: tuple[Path, ...]
    excluded: tuple[tuple[Path, Fault], ...]


def is_sidecar(path: Path) -> bool:
    """Return whether a path names a camera sidecar (``.LRV`` or ``.THM``, any case).

    Args:
        path: The candidate path; the file is not opened.

    Returns:
        True for a sidecar.
    """
    return path.suffix.lower() in SIDECAR_SUFFIXES


def sidecar_fault(path: Path) -> Fault:
    """Build the ``sidecar`` fault for an excluded path (D83).

    Args:
        path: The excluded sidecar.

    Returns:
        A fault of kind ``sidecar`` and severity ``exclude`` with a user-readable message.
    """
    return Fault(
        kind="sidecar",
        severity="exclude",
        message=(
            f"{path.name} is a camera proxy or thumbnail file, not a video to correct. "
            "It was left out of the inputs."
        ),
    )


def filter_inputs(paths: Iterable[Path]) -> InputSelection:
    """Split candidate input paths into inputs and excluded sidecars (D83).

    Args:
        paths: The candidate paths.

    Returns:
        The inputs and, for each excluded sidecar, its fault.
    """
    inputs: list[Path] = []
    excluded: list[tuple[Path, Fault]] = []
    for path in paths:
        if is_sidecar(path):
            excluded.append((path, sidecar_fault(path)))
        else:
            inputs.append(path)
    return InputSelection(tuple(inputs), tuple(excluded))
