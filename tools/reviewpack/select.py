"""Commissioned item selection and excerpt planning for WP5.3 (RED skeleton)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Item:
    """A commissioned input, optionally resolved under the configured source root.

    Attributes:
        name: Exact commissioned source file name.
        group: Commissioned review group.
        kind: Photo or video.
        path: Runtime source path, absent before resolution.
        excerpt: Whether the probed item uses an excerpt.
    """

    name: str
    group: str
    kind: str
    path: Path | None = None
    excerpt: bool = False

    @property
    def stem(self) -> str:
        """Return the item's file stem.

        Returns:
            The source name without its suffix.
        """
        raise NotImplementedError("Item.stem")


@dataclass(frozen=True)
class ExcerptPlan:
    """A duration-derived whole-input or stream-copy plan.

    Attributes:
        start_s: Planned source start in seconds.
        duration_s: Planned length in seconds.
        excerpt: Whether a stream-copied excerpt is required.
    """

    start_s: float
    duration_s: float
    excerpt: bool


def catalog() -> tuple[Item, ...]:
    """Return the commissioned inventory without opening any source folder.

    Returns:
        The complete ordered tuple, with the long phone item last in V-P.
    """
    raise NotImplementedError("catalog")


def items(root: Path | None = None) -> tuple[Item, ...]:
    """Resolve the commissioned inventory through the permitted locators.

    Args:
        root: Explicit source root, or the local configuration's footage root.

    Returns:
        Items with resolved runtime source paths.
    """
    raise NotImplementedError("items")


def find_photo(name: str, root: Path) -> Path:
    """Resolve an exact commissioned photo name without following source links.

    Args:
        name: Commissioned HEIC or JPG name, matched case-insensitively.
        root: The source root to search read-only.

    Returns:
        The unique matching file.
    """
    raise NotImplementedError("find_photo")


def excerpt_plan(group: str, duration_s: float) -> ExcerptPlan:
    """Plan the brief's whole-clip or forty-percent stream-copy treatment.

    Args:
        group: Commissioned review group.
        duration_s: Positive finite probed duration.

    Returns:
        The planned source interval and whether to stream copy it.
    """
    raise NotImplementedError("excerpt_plan")
