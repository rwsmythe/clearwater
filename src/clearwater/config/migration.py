"""``format_version`` migration for settings and preset documents (AD-13; WP3.15).

IF-9 and IF-10 read only :data:`~clearwater.interfaces.FORMAT_VERSION` (1). Before they are
called, a decoded document is brought up to that version one step at a time (version n to
n + 1) through a :class:`MigrationRegistry`. Only version 1 exists today, so the default
registry is empty; tests register a fake version 0 to prove the path. A version above the
current one is refused by name before any step runs, and nothing here touches a file, so a
refused file is never rewritten.
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from typing import Any, Literal

from clearwater.interfaces import FORMAT_VERSION, FormatError, UnsupportedFormatVersionError

type DocumentKind = Literal["settings", "preset"]
"""The two document families that carry a ``format_version``."""

type MigrationStep = Callable[[dict[str, Any]], dict[str, Any]]
"""A step takes a decoded document at version n and returns it at version n + 1."""


class MigrationRegistry:
    """The steps that bring older documents to the current format version."""

    def __init__(self) -> None:
        """Create an empty registry."""
        self._steps: dict[tuple[str, int], MigrationStep] = {}

    def register(self, kind: DocumentKind, from_version: int, step: MigrationStep) -> None:
        """Register the step that migrates ``kind`` documents from ``from_version``.

        Args:
            kind: ``"settings"`` or ``"preset"``.
            from_version: The version the step reads; it must produce ``from_version + 1``.
            step: The step. It receives a private copy it may modify.

        Raises:
            ValueError: A step is already registered for that kind and version.
        """
        key = (kind, from_version)
        if key in self._steps:
            raise ValueError(f"a {kind} migration from version {from_version} is registered")
        self._steps[key] = step

    def step_for(self, kind: DocumentKind, from_version: int) -> MigrationStep | None:
        """Return the step for ``kind`` documents at ``from_version``, or None."""
        return self._steps.get((kind, from_version))


DEFAULT_MIGRATIONS = MigrationRegistry()
"""The product's registry: empty while only format version 1 exists."""


def migrate(
    kind: DocumentKind,
    data: dict[str, Any],
    registry: MigrationRegistry | None = None,
) -> dict[str, Any]:
    """Bring a decoded document to the current ``format_version``.

    Args:
        kind: ``"settings"`` or ``"preset"``.
        data: The decoded document; never modified.
        registry: The steps to use; :data:`DEFAULT_MIGRATIONS` when None.

    Returns:
        ``data`` itself when it is already current, else a migrated copy at version 1.

    Raises:
        UnsupportedFormatVersionError: ``format_version`` is absent, not an integer, above the
            current version, or below it with no registered step to climb.
        FormatError: A step did not raise the version by exactly one.
    """
    steps = DEFAULT_MIGRATIONS if registry is None else registry
    version = data.get("format_version")
    if isinstance(version, bool) or not isinstance(version, int):
        raise UnsupportedFormatVersionError(f"format_version {version!r} is not supported")
    if version > FORMAT_VERSION:
        raise UnsupportedFormatVersionError(
            f"format_version {version} is newer than this Clearwater reads ({FORMAT_VERSION})"
        )
    current = data
    while version < FORMAT_VERSION:
        step = steps.step_for(kind, version)
        if step is None:
            raise UnsupportedFormatVersionError(
                f"no migration for {kind} format_version {version} to {version + 1}"
            )
        current = step(copy.deepcopy(current))
        new_version = current.get("format_version")
        if isinstance(new_version, bool) or new_version != version + 1:
            raise FormatError(
                f"the {kind} migration from version {version} produced {new_version!r}, "
                f"not {version + 1}"
            )
        version = version + 1
    return current
