"""The one write guard of the WP2.1S tools: every file they write is checked here first.

A target is written only if its fully resolved path (links and junctions followed) lies
inside the guard's root, does not lie inside the footage folder, and is not an existing
regular file with more than one hard link (writing it would also change the other names).
The root is ``<working folder>/wp2.1s`` for the tools (:meth:`WriteGuard.for_config`) and
pytest's basetemp for test fixtures. The check is made immediately before each write; it
does not hold a lock, so a link planted between the check and the write is not caught.
"""

from __future__ import annotations

import os
import stat
import sys
from dataclasses import dataclass
from pathlib import Path

if not __package__:
    # Script mode: sys.path[0] is tools/spike_io; put tools first for the sibling packages.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from local_config import LocalConfig

WORK_SUBDIR = "wp2.1s"
"""The folder inside the working folder that every output of this package goes to."""

REASONS = ("footage", "outside", "hard-link")
"""The reasons a write is refused, each named in :class:`OutputRefusedError`."""


class OutputRefusedError(Exception):
    """A write target the guard refuses.

    Attributes:
        reason: One of :data:`REASONS`.
        target: The target as given.
    """

    def __init__(self, reason: str, target: Path, detail: str) -> None:
        """Record the reason and the target, with a message naming both."""
        super().__init__(f"refused ({reason}): {target}: {detail}")
        self.reason = reason
        self.target = target


def _real(path: Path) -> Path:
    """Return ``path`` absolute with every link and junction in it followed."""
    return Path(os.path.realpath(path))


@dataclass(frozen=True)
class WriteGuard:
    """The allowed root and the footage folder.

    Attributes:
        root: Every write must resolve inside this folder. Taken as given, so pass it
            resolved: a root that is relative or holds a link refuses every target.
        footage: No write may resolve inside this folder (``None``: none configured).
            Resolved here, so a link in the configured path cannot hide the folder.
    """

    root: Path
    footage: Path | None = None

    def __post_init__(self) -> None:
        """Resolve the footage folder."""
        if self.footage is not None:
            object.__setattr__(self, "footage", _real(self.footage))

    @classmethod
    def for_config(cls, config: LocalConfig) -> WriteGuard:
        """Return the guard of the tools: root ``<working folder>/wp2.1s``, created.

        The root is the working folder resolved, joined with ``wp2.1s`` WITHOUT resolving
        that last name: if ``wp2.1s`` is itself a link or junction, every target resolves
        elsewhere and is refused.

        Args:
            config: The local configuration.

        Returns:
            The guard.

        Raises:
            OutputRefusedError: The root lies inside the footage folder or is a link.
        """
        root = _real(config.working_path) / WORK_SUBDIR
        guard = cls(root=root, footage=config.footage_path)
        guard.check(root)
        root.mkdir(parents=True, exist_ok=True)
        if _real(root) != root:
            raise OutputRefusedError("outside", root, f"resolves to {_real(root)}")
        return guard

    def check(self, target: Path) -> Path:
        """Return ``target`` if writing it is allowed; refuse it by reason otherwise.

        Args:
            target: The file (or folder) about to be written or created.

        Returns:
            ``target`` unchanged.

        Raises:
            OutputRefusedError: ``footage`` (resolves inside the footage folder), ``outside``
                (resolves outside the root) or ``hard-link`` (an existing regular file with
                more than one link).
        """
        resolved = _real(target)
        if self.footage is not None and resolved.is_relative_to(self.footage):
            raise OutputRefusedError("footage", target, f"resolves to {resolved}")
        if not resolved.is_relative_to(self.root):
            raise OutputRefusedError(
                "outside", target, f"resolves to {resolved}, not in {self.root}"
            )
        try:
            status = os.stat(resolved)
        except FileNotFoundError:
            return target
        if stat.S_ISREG(status.st_mode) and status.st_nlink > 1:
            raise OutputRefusedError("hard-link", target, f"{status.st_nlink} links")
        return target

    def folder(self, *parts: str) -> Path:
        """Create (if needed) and return a folder under the root, checked before and after.

        Args:
            *parts: The folder's names below the root.

        Returns:
            The folder.

        Raises:
            OutputRefusedError: The folder resolves outside the root or inside the footage folder.
        """
        path = self.root.joinpath(*parts)
        self.check(path)
        path.mkdir(parents=True, exist_ok=True)
        return self.check(path)
