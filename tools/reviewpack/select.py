"""Commissioned name-only selection and duration-based excerpt planning for CP5."""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, replace
from pathlib import Path

from local_config import FootageLookupError, find_footage_file, load_local_config

PHOTO_HEIC = tuple(
    f"IMG_{n}.HEIC"
    for n in (
        6690,
        6691,
        6692,
        6693,
        6694,
        6695,
        6696,
        6697,
        6698,
        6699,
        6700,
        6701,
        6703,
        6705,
        6706,
        6707,
        6708,
        6709,
        6710,
        6711,
        6712,
        6713,
        6714,
        6715,
        6718,
        6719,
        6720,
        6721,
        6722,
        6723,
        6724,
        6725,
        6726,
        6730,
        6732,
        6737,
        6739,
        6740,
        6743,
        6744,
        6746,
        6747,
        6748,
        6749,
        6750,
        6752,
        6753,
        6754,
        6755,
        6756,
        6757,
        6758,
        6759,
        6761,
        6763,
        6764,
        6765,
        6766,
        6767,
        6768,
        6769,
        6770,
    )
)
PHOTO_A = (*PHOTO_HEIC, "IMG_6751.JPG", "IMG_6771.JPG")
PHOTO_Z = tuple(f"IMG_{n}.JPG" for n in (6791, 6793, 6794, 6795, 6798, 6799, 6800, 6801, 6802))
VIDEO_S = tuple(f"GX01{n:04d}.mp4" for n in range(1603, 1629))
VIDEO_D = tuple(f"GX01{n:04d}.mp4" for n in (1589, 1590, 1591, 1592, 1593, 1598, 1600, 1601))
VIDEO_P = tuple(
    f"IMG_{n}.MOV"
    for n in (
        6702,
        6716,
        6717,
        6727,
        6728,
        6729,
        6731,
        6733,
        6734,
        6735,
        6736,
        6738,
        6741,
        6742,
        6745,
        6760,
        6762,
    )
)
VIDEO_R = ("IMG_6704.MOV", "IMG_6772.MOV")
VIDEO_Z = ("dp_color_video_1791675261.mp4", "compilation-20261010-1080p60.mp4")
GROUPS = ("P-A", "P-Z", "V-S", "V-D", "V-P", "V-R", "V-Z")


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
        return Path(self.name).stem


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
    return tuple(
        Item(name, group, "photo" if group.startswith("P-") else "video")
        for group, names in zip(
            GROUPS, (PHOTO_A, PHOTO_Z, VIDEO_S, VIDEO_D, VIDEO_P, VIDEO_R, VIDEO_Z), strict=True
        )
        for name in names
    )


def items(root: Path | None = None) -> tuple[Item, ...]:
    """Resolve the commissioned inventory through the permitted locators.

    Args:
        root: Explicit source root, or the local configuration's footage root.

    Returns:
        Items with resolved runtime source paths.
    """
    source_root = load_local_config().footage_path if root is None else root
    return tuple(
        replace(
            item,
            path=(
                find_photo(item.name, source_root)
                if item.kind == "photo"
                else find_footage_file(item.stem, source_root)
            ),
        )
        for item in catalog()
    )


def find_photo(name: str, root: Path) -> Path:
    """Resolve an exact commissioned photo name without following source links.

    Args:
        name: Commissioned HEIC or JPG name, matched case-insensitively.
        root: The source root to search read-only.

    Returns:
        The unique matching file.
    """
    if name.casefold() not in {n.casefold() for n in (*PHOTO_A, *PHOTO_Z)}:
        raise ValueError("photo name must be an exact commissioned HEIC or JPG name")
    if not root.is_dir():
        raise FootageLookupError("footage folder is missing or not a directory")

    def walk_error(error: OSError) -> None:
        raise FootageLookupError("cannot search the footage folder") from error

    found = []
    for folder, directories, filenames in os.walk(root, onerror=walk_error):
        directories[:] = [
            n
            for n in directories
            if not os.path.islink(os.path.join(folder, n))
            and not os.path.isjunction(os.path.join(folder, n))
        ]
        for filename in filenames:
            path = Path(folder, filename)
            if filename.casefold() == name.casefold() and not path.is_symlink() and path.is_file():
                found.append(path)
    matches = tuple(sorted(found))
    if not matches:
        raise FootageLookupError(f"{name} is not in the footage folder")
    if len(matches) > 1:
        raise FootageLookupError(
            f"{name} matches {len(matches)} files in the footage folder", matches
        )
    return matches[0]


def excerpt_plan(group: str, duration_s: float) -> ExcerptPlan:
    """Plan the brief's whole-clip or forty-percent stream-copy treatment.

    Args:
        group: Commissioned review group.
        duration_s: Positive finite probed duration.

    Returns:
        The planned source interval and whether to stream copy it.
    """
    if not math.isfinite(duration_s) or duration_s <= 0:
        raise ValueError("duration must be positive and finite")
    if group not in GROUPS or group.startswith("P-"):
        raise ValueError("excerpt plan requires a video group")
    if group in {"V-S", "V-D", "V-Z"} and duration_s > 45:
        return ExcerptPlan(0.4 * duration_s, 30.0, True)
    return ExcerptPlan(0.0, duration_s, False)
