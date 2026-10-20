"""Output naming (spec 8.3; D34, D35, D36, D84).

Turns a source path and the settings into a final output path that collides with nothing on
disk. The module writes nothing: it only asks the filesystem whether a candidate name is taken.
Safe writing (the temporary name, the rename, the clean-up) is in :mod:`clearwater.jobs.safe_write`.

Numbering: the unnumbered name is number 1; a clash moves to ``_2``, ``_3``, ... appended after
the suffix (``IMG_1234_corrected_2.png``). Whether a name is taken is decided by the filesystem
(``os.path.lexists``), never by comparing strings, so a case-insensitive volume treats
``img_1234_corrected.PNG`` as a clash with ``IMG_1234_corrected.png``. Names planned earlier in the
same run but not yet on disk are held in a :class:`Reservations` registry, compared case-folded on
every platform: on a case-sensitive volume that can skip one number needlessly, but it can never
allow two jobs the same name.
"""

from __future__ import annotations

import enum
import os
import re
import threading
from dataclasses import dataclass, replace
from pathlib import Path

from clearwater.interfaces.settings import Settings

TEMP_MARKER = ".clearwater-partial"
"""The marker placed before the extension of every temporary output (spec 8.4, D85)."""

PHOTO_EXTENSION = ".png"
"""The extension every photo output gets (spec 8.3)."""

_FORBIDDEN_SUFFIX_CHARS = frozenset('/\\:*?"<>|')
_TEMP_NAME = re.compile(re.escape(TEMP_MARKER) + r"(?:\.[^./\\]+)?\Z", re.IGNORECASE)


class MediaKind(enum.Enum):
    """The kind of source, which decides the output extension."""

    VIDEO = "video"
    PHOTO = "photo"


def validate_suffix(suffix: str) -> None:
    """Check that an output suffix is a single portable name fragment.

    Args:
        suffix: The suffix from the settings (D36); may be empty.

    Raises:
        ValueError: If the suffix contains a path separator, a character Windows forbids in
            names, a control character, ``..``, a trailing dot or space, or the temporary
            marker (which would make final outputs look like temporaries to the clean-up).
    """
    bad = sorted(
        {c for c in suffix if c in _FORBIDDEN_SUFFIX_CHARS or ord(c) < 32},
        key=ord,
    )
    if bad:
        raise ValueError(f"output suffix {suffix!r} contains forbidden characters {bad!r}")
    if ".." in suffix:
        raise ValueError(f"output suffix {suffix!r} must not contain '..'")
    if suffix.endswith((".", " ")):
        raise ValueError(f"output suffix {suffix!r} must not end with a dot or a space")
    if TEMP_MARKER in suffix.casefold():
        raise ValueError(f"output suffix {suffix!r} must not contain {TEMP_MARKER!r}")


def is_temporary_name(name: str) -> bool:
    """Tell whether a file name matches the temporary-name pattern.

    The pattern is a non-empty base, then ``.clearwater-partial``, then nothing or exactly one
    extension (``GX010123_corrected.clearwater-partial.MP4``), compared case-insensitively because
    a case-insensitive volume may report the name in any case.

    Args:
        name: A bare file name (no directory part).

    Returns:
        True if the name is a Clearwater temporary output name.
    """
    if not name or "/" in name or "\\" in name:
        return False
    match = _TEMP_NAME.search(name)
    return match is not None and match.start() > 0


def temporary_path(final: Path) -> Path:
    """Return the temporary path belonging to a final output path.

    Args:
        final: A final output path (numbered or not).

    Returns:
        The same folder and name with ``.clearwater-partial`` inserted before the extension, so
        the writer still sees the right extension.
    """
    return final.with_name(final.stem + TEMP_MARKER + final.suffix)


def _path_key(path: Path) -> str:
    """Return the conservative comparison key for a path: absolute, normcased, case-folded."""
    return os.path.normcase(os.path.abspath(path)).casefold()


def is_same_path(a: Path, b: Path) -> bool:
    """Tell whether two paths name the same file, for the source guard.

    Uses ``os.path.samefile`` when both exist (the filesystem decides, including case folding and
    links); otherwise compares the absolute paths normcased and case-folded.

    Args:
        a: The first path.
        b: The second path.

    Returns:
        True if the paths are the same file or, when one does not exist, the same name.
    """
    try:
        if a.exists() and b.exists():
            return os.path.samefile(a, b)
    except OSError:
        pass
    return _path_key(a) == _path_key(b)


class Reservations:
    """A thread-safe registry of output names planned but not yet on disk.

    A batch plans several outputs before any is written; each planned name is held here so a
    later plan or a commit-time renumbering cannot choose it. Names are compared by their
    absolute, case-folded form.
    """

    def __init__(self) -> None:
        """Create an empty registry."""
        self._lock = threading.Lock()
        self._held: dict[str, Path] = {}

    def try_reserve(self, path: Path) -> bool:
        """Hold a name unless an equal name is already held.

        Args:
            path: The final output path to hold.

        Returns:
            True if the name is now held by the caller, False if it was already held.
        """
        key = _path_key(path)
        with self._lock:
            if key in self._held:
                return False
            self._held[key] = path
            return True

    def release(self, path: Path) -> None:
        """Release a name this caller holds; a name not held (or held as another path) is left.

        Args:
            path: The exact path passed to :meth:`try_reserve`.
        """
        key = _path_key(path)
        with self._lock:
            held = self._held.get(key)
            if held is not None and str(held) == str(path):
                del self._held[key]

    def __contains__(self, path: object) -> bool:
        """Tell whether an equal name is held."""
        if not isinstance(path, Path):
            return False
        with self._lock:
            return _path_key(path) in self._held

    def __len__(self) -> int:
        """Return the number of names held."""
        with self._lock:
            return len(self._held)


@dataclass(frozen=True)
class OutputPlan:
    """One planned final output name.

    Attributes:
        source: The source file this output is made from; it is never written, renamed or
            deleted, and no final path may equal it.
        folder: The folder the output goes in.
        base: The source stem plus the suffix.
        extension: The output extension with its dot (may be empty).
        number: 1 for the unnumbered name, N >= 2 for ``<base>_N``.
    """

    source: Path
    folder: Path
    base: str
    extension: str
    number: int = 1

    @property
    def path(self) -> Path:
        """The final output path for this number."""
        stem = self.base if self.number == 1 else f"{self.base}_{self.number}"
        return self.folder / (stem + self.extension)

    def numbered(self, number: int) -> OutputPlan:
        """Return the same plan at another collision number.

        Args:
            number: 1 for the unnumbered name, N >= 2 for ``_N``.

        Returns:
            A new plan.

        Raises:
            ValueError: If ``number`` is below 1.
        """
        if number < 1:
            raise ValueError(f"collision number must be >= 1, got {number}")
        return replace(self, number=number)


def _base_plan(source: Path, settings: Settings, kind: MediaKind) -> OutputPlan:
    """Build the unnumbered plan (no filesystem access)."""
    validate_suffix(settings.output_suffix)
    folder = source.parent if settings.output_folder is None else settings.output_folder
    extension = PHOTO_EXTENSION if kind is MediaKind.PHOTO else source.suffix
    return OutputPlan(
        source=source,
        folder=folder,
        base=source.stem + settings.output_suffix,
        extension=extension,
    )


def final_output_path(source: Path, settings: Settings, kind: MediaKind) -> Path:
    """Return the unnumbered final output path (spec 8.3), touching no filesystem.

    ``GX010123.MP4`` becomes ``GX010123_corrected.MP4``; ``IMG_1234.HEIC`` becomes
    ``IMG_1234_corrected.png``.

    Args:
        source: The source file path.
        settings: The settings (``output_folder``, ``output_suffix``).
        kind: Video keeps the source extension exactly; a photo gets ``.png``.

    Returns:
        The path before any collision numbering.

    Raises:
        ValueError: If the suffix is not a portable name fragment.
    """
    return _base_plan(source, settings, kind).path


def is_taken(plan: OutputPlan) -> bool:
    """Tell whether a planned name is unusable on disk right now.

    A name is taken when the final name exists (including a dangling symlink), the matching
    temporary name exists (another job's or a crash leftover), or the name is the source.

    Args:
        plan: The candidate.

    Returns:
        True if the candidate must not be used.
    """
    path = plan.path
    return (
        os.path.lexists(path)
        or os.path.lexists(temporary_path(path))
        or is_same_path(path, plan.source)
    )


def plan_output(
    source: Path,
    settings: Settings,
    kind: MediaKind,
    reservations: Reservations | None = None,
) -> OutputPlan:
    """Plan the final output name for a source (D34, D35, D36, D84).

    Tries the unnumbered name, then ``_2``, ``_3``, ... and returns the first candidate that is
    free on disk, has no temporary on disk, is not the source and (when ``reservations`` is
    given) is not held by another plan. The returned name is reserved in ``reservations``.

    Args:
        source: The source file path.
        settings: The settings (``output_folder``, ``output_suffix``).
        kind: Video keeps the source extension; a photo gets ``.png``.
        reservations: The run's registry, or None for a one-off plan with no reservation.

    Returns:
        The plan; read ``plan.path`` for the final path.

    Raises:
        ValueError: If the suffix is invalid or a candidate name would itself look like a
            temporary (a source literally named with the temporary marker and an empty suffix).
    """
    plan = _base_plan(source, settings, kind)
    while True:
        if is_temporary_name(plan.path.name):
            raise ValueError(f"output name {plan.path.name!r} matches the temporary-name pattern")
        if not is_taken(plan) and (reservations is None or reservations.try_reserve(plan.path)):
            return plan
        plan = plan.numbered(plan.number + 1)
