"""Safe writing (spec 8.4; D44, D85, D87).

A job writes its output to a temporary name in the destination folder and the file is renamed to
its final name only on success (:class:`SafeWrite`). Cancel, failure and an exception inside the
``with`` block all delete the temporary. Leftovers from a crash are removed by
:func:`remove_leftovers`. Nothing in this module writes, renames or deletes the source file, and
no final name is ever replaced.

The no-replace rename (DR-16, AD-25b) is one portable algorithm with a documented platform
difference. :func:`os.link` followed by ``os.unlink`` is tried first: every platform's ``link``
refuses to create a name that already exists, so there is no check-then-act window. Where links
are unsupported (exFAT, FAT) the fallback re-checks the final name and calls :func:`os.rename`.
Windows refuses to rename over an existing file, which is the guarantee there. POSIX ``rename``
replaces silently, so on a POSIX volume without links a file created between the re-check and the
rename could be replaced; that residual race needs a second writer in the same folder at the same
instant and is outside the single-owner threat model (DR-16). ``os.replace`` and ``shutil.move``
are never used.
"""

from __future__ import annotations

import enum
import errno
import os
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from typing import Self

from .naming import (
    OutputPlan,
    Reservations,
    is_same_path,
    is_temporary_name,
    new_token,
    temporaries_of,
    temporary_path,
)

_WINERROR_DISK_FULL = 112
_WINERROR_HANDLE_DISK_FULL = 39


class SafeWriteError(OSError):
    """A safe-write rule was broken (missing folder, missing temporary, source path, bad state)."""


class MissingFolderError(SafeWriteError):
    """The output folder does not exist (an unplugged card or drive, or a stale setting)."""


class SafeWriteState(enum.Enum):
    """The lifecycle state of a :class:`SafeWrite`."""

    NEW = "new"
    OPEN = "open"
    COMMITTED = "committed"
    ABORTED = "aborted"


def is_disk_full(exc: BaseException) -> bool:
    """Tell whether an exception means the volume ran out of space (D87).

    Args:
        exc: An exception caught around a write.

    Returns:
        True for an ``OSError`` carrying ``ENOSPC``, ``EDQUOT`` or Windows error 112 or 39.
    """
    if not isinstance(exc, OSError):
        return False
    codes = {errno.ENOSPC, getattr(errno, "EDQUOT", errno.ENOSPC)}
    winerror = getattr(exc, "winerror", None)
    return exc.errno in codes or winerror in (_WINERROR_DISK_FULL, _WINERROR_HANDLE_DISK_FULL)


def _unlink_quietly(path: Path) -> bool:
    """Remove a file; return True if it is gone afterwards."""
    try:
        path.unlink()
    except FileNotFoundError:
        return True
    except OSError:
        return not os.path.lexists(path)
    return True


def _install(temp: Path, final: Path) -> bool:
    """Move the temporary to the final name without ever replacing an existing file.

    Args:
        temp: The temporary file.
        final: The final name to take.

    Returns:
        True if the final name now holds the file, False if the name is already taken.
    """
    link = getattr(os, "link", None)
    if link is not None:
        try:
            link(temp, final)
        except FileExistsError:
            return False
        except OSError:
            pass  # Links unsupported on this volume (exFAT, FAT): use the rename fallback.
        else:
            _unlink_quietly(temp)
            return True
    if os.path.lexists(final):
        return False
    try:
        os.rename(temp, final)
    except FileExistsError:
        return False
    return True


class SafeWrite:
    """Write one output to a temporary name, then rename it to the final name on success.

    Used as a context manager::

        with SafeWrite(plan, reservations) as write:
            sink.open(write.temp_path, ...)   # the writer truncates (FFmpeg gets ``-y``)
            ...
            write.commit()

    Leaving the block without ``commit()``, or by an exception (cancel, failure, ``ENOSPC``),
    aborts: the temporary is deleted. ``abort()`` is idempotent and never deletes a committed
    final file.

    Attributes:
        plan: The current plan; ``commit()`` may advance its collision number.
    """

    def __init__(self, plan: OutputPlan, reservations: Reservations | None = None) -> None:
        """Prepare a write; nothing is created until :meth:`begin`.

        Args:
            plan: The planned final name (from :func:`~clearwater.jobs.naming.plan_output`).
            reservations: The registry the plan was made with, so a commit-time renumbering
                avoids names other jobs hold; None if none is used.
        """
        self.plan = plan
        self._reservations = reservations
        self._temp = temporary_path(plan.path, new_token())
        self._state = SafeWriteState.NEW
        self._created = False
        self._held = [plan.path]
        self._temp_leftover = False
        self._abort_error: OSError | None = None

    @property
    def state(self) -> SafeWriteState:
        """The lifecycle state."""
        return self._state

    @property
    def temp_path(self) -> Path:
        """The temporary path the writer writes to (valid from :meth:`begin`)."""
        return self._temp

    @property
    def final_path(self) -> Path:
        """The current final path; after a commit, the name actually used."""
        return self.plan.path

    @property
    def temp_leftover(self) -> bool:
        """True if the temporary could not be removed (left for the next-start clean-up)."""
        return self._temp_leftover

    @property
    def abort_error(self) -> OSError | None:
        """The error that stopped :meth:`abort` removing the temporary, if any."""
        return self._abort_error

    def begin(self) -> Path:
        """Create the empty temporary in the destination folder and return its path.

        The name carries this write's random token and the file is created exclusively, so no
        other job or crash leftover can already hold it. The writer must open the path for
        writing with truncation.

        Returns:
            The temporary path.

        Raises:
            SafeWriteError: If already begun, or the final path is the source.
            MissingFolderError: If the output folder does not exist (nothing is created).
            FileExistsError: If the temporary name exists (a real race).
        """
        if self._state is not SafeWriteState.NEW:
            raise SafeWriteError(f"begin() in state {self._state.value}")
        self._guard_source(self.plan)
        folder = self.plan.folder
        if not folder.is_dir():
            raise MissingFolderError(f"output folder does not exist: {folder}")
        fd = os.open(self._temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
        self._created = True  # before the close: a failing close must still be cleaned up
        os.close(fd)
        self._state = SafeWriteState.OPEN
        return self._temp

    def commit(self) -> Path:
        """Rename the temporary to the final name, never replacing an existing file.

        The final name is re-checked at this moment. If it was taken since planning (on disk or
        in the registry), the next collision number is used. The writer must have closed the
        temporary first; on Windows a still-open temporary survives the link step as a leftover.

        Returns:
            The final path actually used.

        Raises:
            SafeWriteError: If not begun or already finished, or the temporary is missing.
            OSError: If the rename fails for any reason other than a taken name.
        """
        if self._state is not SafeWriteState.OPEN:
            raise SafeWriteError(f"commit() in state {self._state.value}")
        if not os.path.lexists(self._temp):
            raise SafeWriteError(f"temporary output is missing: {self._temp}")
        start = self.plan
        plan = start
        while True:
            if plan is start:
                self._guard_source(plan)
                claimed = True
            else:
                claimed = not is_same_path(plan.path, plan.source) and self._claim(plan)
            if (
                claimed
                and not os.path.lexists(plan.path)
                and not self._foreign_temporary(plan.path)
                and _install(self._temp, plan.path)
            ):
                break
            plan = plan.numbered(plan.number + 1)
        self.plan = plan
        self._created = False
        self._temp_leftover = os.path.lexists(self._temp)
        self._state = SafeWriteState.COMMITTED
        self._release()
        return plan.path

    def abort(self) -> bool:
        """Delete the temporary; safe to call at any time and more than once.

        Never raises for a removal problem (it runs inside exception handlers); a temporary that
        cannot be removed is left for :func:`remove_leftovers`. After a commit it removes
        nothing and never touches the final file.

        Returns:
            True if no temporary of this write remains, False if one could not be removed.
        """
        if self._state is SafeWriteState.COMMITTED:
            return not self._temp_leftover
        self._state = SafeWriteState.ABORTED
        self._release()
        if not self._created:
            return True
        try:
            self._temp.unlink()
        except FileNotFoundError:
            pass
        except OSError as exc:
            self._abort_error = exc
        gone = not os.path.lexists(self._temp)
        self._created = not gone
        self._temp_leftover = not gone
        return gone

    def __enter__(self) -> Self:
        """Begin the write and return self.

        If ``begin()`` fails the write is aborted first (Python does not call ``__exit__`` when
        ``__enter__`` raises), so the registry holds nothing for it.
        """
        try:
            self.begin()
        except BaseException:
            self.abort()
            raise
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Abort unless committed; never suppresses the exception."""
        if self._state is SafeWriteState.OPEN:
            self.abort()

    def _guard_source(self, plan: OutputPlan) -> None:
        """Refuse a final path that is the source (mandatory, N8)."""
        if is_same_path(plan.path, plan.source):
            raise SafeWriteError(f"output path is the source file: {plan.path}")

    def _foreign_temporary(self, final: Path) -> bool:
        """Tell whether a temporary of another write exists for this final name."""
        own = self._temp.name.casefold()
        return any(t.name.casefold() != own for t in temporaries_of(final))

    def _claim(self, plan: OutputPlan) -> bool:
        """Reserve a bumped candidate; True if free to try (always True without a registry)."""
        if self._reservations is None:
            return True
        if self._reservations.try_reserve(plan.path):
            self._held.append(plan.path)
            return True
        return False

    def _release(self) -> None:
        """Release every name this write holds in the registry."""
        if self._reservations is not None:
            for path in self._held:
                self._reservations.release(path)
        self._held = []


@dataclass(frozen=True)
class LeftoverReport:
    """The outcome of :func:`remove_leftovers`.

    Attributes:
        removed: Temporary files that were deleted.
        failed: Temporary files that could not be deleted, each with the error text.
    """

    removed: tuple[Path, ...]
    failed: tuple[tuple[Path, str], ...]


def remove_leftovers(folders: list[Path] | tuple[Path, ...]) -> LeftoverReport:
    """Delete leftover temporary outputs (spec 8.4: cleaned up on the next start).

    Only regular files whose name matches the temporary pattern are removed. Folders, symlinks
    (their targets are never reached) and every other file are left alone. The scan is not
    recursive. A missing folder is skipped; a per-file problem is recorded, not raised. Call it
    only while no job is writing in those folders.

    Args:
        folders: The folders to scan.

    Returns:
        What was removed and what could not be.
    """
    removed: list[Path] = []
    failed: list[tuple[Path, str]] = []
    for folder in folders:
        try:
            entries = list(os.scandir(folder))
        except OSError:
            continue
        for entry in entries:
            if not is_temporary_name(entry.name):
                continue
            try:
                if not entry.is_file(follow_symlinks=False):
                    continue
                os.unlink(entry.path)
            except OSError as exc:
                failed.append((Path(entry.path), str(exc)))
            else:
                removed.append(Path(entry.path))
    return LeftoverReport(removed=tuple(removed), failed=tuple(failed))
