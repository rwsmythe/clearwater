"""Name-only HTML pages and colour-managed viewing images for WP5.3 (RED skeleton)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from lookcheck.frames import OutputRoots


def write_page(
    items: Sequence[Mapping[str, Any]],
    presets: Mapping[str, Mapping[str, Any]],
    *,
    roots: OutputRoots,
) -> Path:
    """Write the grouped CP5 page with escaped labels and pack-relative links.

    Args:
        items: Persisted item results.
        presets: Product-exported preset objects.
        roots: Pack and source roots.

    Returns:
        The written index path.
    """
    raise NotImplementedError("write_page")


def check_links(path: Path, *, roots: OutputRoots) -> list[str]:
    """Find missing or unsafe href and src targets in a generated page.

    Args:
        path: Page to inspect.
        roots: Pack and source roots.

    Returns:
        Descriptions of every unresolved or nonlocal link.
    """
    raise NotImplementedError("check_links")


def thumbnail(source: Path, destination: Path, *, roots: OutputRoots) -> Path:
    """Make a short-side-540 JPEG, converting embedded ICC colour to sRGB.

    Args:
        source: Viewing PNG, with or without an embedded ICC profile.
        destination: Guarded thumbnail target.
        roots: Pack and source roots.

    Returns:
        The thumbnail path.
    """
    raise NotImplementedError("thumbnail")


def pair_still(source: Path, corrected: Path, destination: Path, *, roots: OutputRoots) -> Path:
    """Write a source-left/corrected-right JPEG with short-side-1080 halves.

    Args:
        source: Source viewing PNG.
        corrected: Matching corrected viewing PNG.
        destination: Guarded pair-still target.
        roots: Pack and source roots.

    Returns:
        The pair-still path.
    """
    raise NotImplementedError("pair_still")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the stand-alone page link checker.

    Args:
        argv: Link-check arguments or process arguments when absent.

    Returns:
        Zero for resolved links or two for a failed check.
    """
    raise NotImplementedError("page.main")
