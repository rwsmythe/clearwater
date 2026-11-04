"""The tools' shared footage-folder containment check (WP6.4, DR-122).

The older tools compared a resolved, ``os.path.normcase``-d text against the footage folder's.
``normcase`` folds case on Windows only, so on a case-insensitive APFS volume a differently
cased spelling of the footage folder (``/Volumes/Dive/FOOTAGE`` for ``/Volumes/Dive/Footage``)
passed the text check and a tool could write into the read-only folder. :func:`is_inside`
decides by FILE IDENTITY wherever the path exists and by text only where it does not:

1. Both paths are resolved from their ORIGINAL spelling (links in their existing parts
   followed, then ``..`` applied to what a link led to, as POSIX does) and made absolute.
   Collapsing ``..`` first would be wrong on POSIX: with ``alias -> Footage/sub``,
   ``alias/../output`` is ``Footage/output``, not ``output`` beside ``alias`` (Reviewer A r2).
   Win32 itself collapses ``..`` before it follows a junction, so there the two orders agree.
2. Each is split into its nearest EXISTING ancestor (itself when it exists) and the lexical
   tail of names below it that do not exist yet.
3. ``path`` is inside ``root`` when the root's existing ancestor is, by identity
   (``os.path.samestat``), the path's existing ancestor or one of that ancestor's own
   ancestors, and the remaining names then begin with the root's tail (compared
   ``normcase``-d: the tail has no identity yet).

A plain text check (the old one, on the lexical and the resolved spellings) also runs first,
so nothing the old tools refused is accepted now. A file system that reports no file number
(``st_ino == 0``) falls back to the text check for that comparison. The product's own guards
are not this module's: the headless runner's ``tools/headless_export.inside`` and
``clearwater.jobs.naming.is_same_path`` are compared with it by a parity test
(``tests/test_portability.py``), never imported here.

The check is made once, before a write; a concurrent swap between the check and the write is
outside what it guards against (as before).
"""

from __future__ import annotations

import os
from pathlib import Path, PurePath


def _stat(path: PurePath) -> os.stat_result:
    """Return ``os.stat(path)`` (a seam: a W test replaces it with a fake identity table)."""
    return os.stat(path)


def _normcase(text: str) -> str:
    """Return ``os.path.normcase(text)``, the text form of the parts without identity (a seam)."""
    return os.path.normcase(text)


def _realpath(text: str) -> str:
    """Return ``os.path.realpath(text)`` (a seam a W test replaces).

    Windows' realpath also restores the on-disk case of the existing names, which macOS's does
    not, so a W test replaces it to reproduce a case-insensitive APFS volume.
    """
    return os.path.realpath(text)


def _absolute(path: Path) -> PurePath:
    """Return ``path`` resolved from its original spelling: links followed, then ``..``.

    ``realpath`` takes the names in order, so a ``..`` after a link leaves the link's TARGET,
    and makes a relative path absolute against the working folder itself.
    """
    return PurePath(_realpath(os.fspath(path)))


def _texts(path: Path) -> list[PurePath]:
    """Return the lexical and the resolved spellings of ``path``, ``normcase``-d.

    The lexical one (``..`` collapsed by text) is kept as a second candidate, so a path either
    spelling places inside is refused.
    """
    spellings = {os.path.abspath(path), str(_absolute(path))}
    return [PurePath(_normcase(text)) for text in spellings]


def _split_existing(path: PurePath) -> tuple[PurePath, os.stat_result, tuple[str, ...]] | None:
    """Return the nearest existing ancestor of ``path`` (or itself), its stat and the tail.

    Returns None when no ancestor can be read at all (an absent drive, for example).
    """
    tail: list[str] = []
    current = path
    while True:
        try:
            return current, _stat(current), tuple(reversed(tail))
        except (OSError, ValueError):
            if current.parent == current:
                return None
            tail.append(current.name)
            current = current.parent


def _same(a: PurePath, a_stat: os.stat_result, b: PurePath, b_stat: os.stat_result) -> bool:
    """Return whether two existing paths are one object (by text when there is no identity)."""
    if a_stat.st_ino and b_stat.st_ino:
        return os.path.samestat(a_stat, b_stat)
    return _normcase(str(a)) == _normcase(str(b))


def _starts_with(names: tuple[str, ...], prefix: tuple[str, ...]) -> bool:
    """Return whether ``names`` begins with ``prefix``, name by name, ``normcase``-d."""
    if len(names) < len(prefix):
        return False
    return all(_normcase(a) == _normcase(b) for a, b in zip(names, prefix, strict=False))


def is_inside(path: Path, root: Path) -> bool:
    """Return whether ``path`` is ``root`` or lies under it, however either is spelled.

    Args:
        path: The path to test (it need not exist).
        root: The folder (it need not exist; the footage folder normally does).

    Returns:
        True when ``path`` is, or lies inside, ``root``: by text on either spelling, or by the
        identity of the nearest existing ancestor followed by the lexical tail.
    """
    targets, roots = _texts(path), _texts(root)
    if any(t == r or r in t.parents for t in targets for r in roots):
        return True
    target = _split_existing(_absolute(path))
    base = _split_existing(_absolute(root))
    if target is None or base is None:
        return False
    target_existing, target_stat, target_tail = target
    base_existing, base_stat, base_tail = base
    for depth, candidate in enumerate((target_existing, *target_existing.parents)):
        try:
            candidate_stat = target_stat if depth == 0 else _stat(candidate)
        except (OSError, ValueError):
            continue
        if _same(candidate, candidate_stat, base_existing, base_stat):
            below = target_existing.parts[len(target_existing.parts) - depth :] if depth else ()
            return _starts_with((*below, *target_tail), base_tail)
    return False
