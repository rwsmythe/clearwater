"""Shared pytest configuration: the footage guard and the footage-test skip.

Temp-root guard (WP-T1, closes DR-21). ``pytest --basetemp=<dir>`` deletes and
recreates ``<dir>``, and ``TMP``/``TEMP``/``TMPDIR``/``PYTEST_DEBUG_TEMPROOT``
decide where pytest makes its folders. Pointed at the owner's footage folder,
a run could delete or write footage. A ``pytest_configure`` hook (``tryfirst``)
therefore refuses to start (``pytest.UsageError``, exit code 4, message naming
the footage folder and the offending root) when the temp root would be:

* ``--basetemp``: inside the footage folder, equal to it, or an ancestor of it
  (pytest removes the whole basetemp tree, which would take the footage with it);
* otherwise the default temp root (``PYTEST_DEBUG_TEMPROOT`` if set, else the
  directory ``tempfile.gettempdir()`` would pick), inside or equal to the
  footage folder.

Paths are compared fully resolved (symlinks and junctions followed) and, on
Windows, case-insensitively. A legitimate basetemp, such as a folder under the
working folder, passes. The guard is inert, and silent, when there is no valid
local configuration: it never fails a run on a machine without footage.

The guard only runs when this file is loaded, that is, when the pytest arguments
(or ``testpaths``, when none are given) lie at or below ``tests/``. A run on a
path outside ``tests/``, with ``--noconftest`` or ``--confcutdir`` above this
folder, or from another rootdir, does not load it. See
``docs/reports/wp-t1-pytest-guard.md``.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from local_config import LocalConfigError, footage_available, load_local_config


def _canonical(path: str | os.PathLike[str]) -> Path:
    """Return ``path`` made absolute, fully resolved and case-normalised.

    Args:
        path: A path that need not exist.

    Returns:
        The path as ``os.path.abspath`` then ``Path.resolve`` leave it (pytest's own
        order for ``--basetemp``), normalised for case on Windows.

    Raises:
        OSError: If the path cannot be resolved.
        RuntimeError: If resolving meets a symlink loop.
    """
    resolved = Path(os.path.abspath(os.fspath(path))).resolve()
    return Path(os.path.normcase(str(resolved)))


def _inside_or_equal(candidate: Path, folder: Path) -> bool:
    """Report whether ``candidate`` equals ``folder`` or lies below it."""
    return candidate == folder or folder in candidate.parents


def _temp_root_candidates() -> list[str]:
    """Return the directories ``tempfile.gettempdir()`` may use, without touching disk.

    ``tempfile.gettempdir()`` itself probes by creating and deleting a file in
    each candidate in turn, which would write inside a footage folder named by
    ``TMPDIR``/``TEMP``/``TMP``. This mirrors its candidate list instead
    (``tempfile._candidate_tempdir_list``, Python 3.12), and every candidate is
    checked, which includes the one ``gettempdir()`` would pick.

    Returns:
        The cached ``tempfile.tempdir`` alone if already chosen, else every
        candidate.
    """
    if tempfile.tempdir:
        return [tempfile.tempdir]
    candidates = [value for name in ("TMPDIR", "TEMP", "TMP") if (value := os.getenv(name))]
    if os.name == "nt":
        candidates += [
            os.path.expanduser(r"~\AppData\Local\Temp"),
            os.path.expandvars(r"%SYSTEMROOT%\Temp"),
            r"c:\temp",
            r"c:\tmp",
            r"\temp",
            r"\tmp",
        ]
    else:
        candidates += ["/tmp", "/var/tmp", "/usr/tmp"]
    candidates.append(os.getcwd())
    return candidates


def _offending_root(config: pytest.Config, footage: Path) -> str | None:
    """Return a description of the temp root that threatens ``footage``, if any.

    Mirrors ``_pytest.tmpdir.TempPathFactory`` (pytest 8.4): ``__init__`` takes
    ``os.path.abspath(basetemp)``; ``getbasetemp`` removes and recreates a given
    basetemp, else uses ``PYTEST_DEBUG_TEMPROOT`` or ``tempfile.gettempdir()``
    as the root of ``pytest-of-<user>/``.

    Args:
        config: The pytest configuration.
        footage: The canonical footage folder.

    Returns:
        A short description of the offending root, or None when all is clear.
    """
    basetemp = config.option.basetemp
    if basetemp:
        root = _canonical(basetemp)
        if _inside_or_equal(root, footage) or _inside_or_equal(footage, root):
            return f"--basetemp {basetemp}"
        return None
    from_env = os.environ.get("PYTEST_DEBUG_TEMPROOT")
    if from_env:
        origin, roots = "PYTEST_DEBUG_TEMPROOT", [from_env]
    else:
        origin, roots = (
            "the default temp root (TMPDIR/TEMP/TMP or a system default)",
            (_temp_root_candidates()),
        )
    for root_text in roots:
        if _inside_or_equal(_canonical(root_text), footage):
            return f"{origin} {root_text}"
    return None


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """Refuse to start when pytest's temp root would lie in the footage folder.

    Runs before pytest's own ``pytest_configure`` builds the temp-path factory;
    pytest creates or clears nothing until the first ``tmp_path`` is requested.
    Inert without a valid local configuration.

    Args:
        config: The pytest configuration.

    Raises:
        pytest.UsageError: If the temp root equals, lies inside (or, for
            ``--basetemp``, contains) the configured footage folder, or cannot
            be resolved.
    """
    try:
        footage_raw = load_local_config().footage_path
    except (LocalConfigError, OSError):
        return
    try:
        footage = _canonical(footage_raw)
    except (OSError, RuntimeError):
        footage = Path(os.path.normcase(os.path.abspath(footage_raw)))
    try:
        offending = _offending_root(config, footage)
    except (OSError, RuntimeError) as exc:
        raise pytest.UsageError(
            f"footage guard: cannot resolve the pytest temp root ({exc}); "
            f"refusing to run with a footage folder configured at {footage_raw}"
        ) from None
    if offending is not None:
        raise pytest.UsageError(
            f"footage guard: refusing to run, {offending} is inside, equal to or above the "
            f"read-only footage folder {footage_raw}; pytest would write or delete there. "
            "Use a folder outside the footage folder (the working folder is fine)."
        )


def _footage_skip_reason() -> str | None:
    """Return why footage-marked tests must be skipped, or None when they can run.

    Returns:
        None if the footage folder is configured and present; otherwise a reason
        that distinguishes "not configured" from "configured but absent".
    """
    if footage_available():
        return None
    try:
        footage = load_local_config().footage_path
    except (LocalConfigError, OSError):
        return (
            "footage folder not configured; copy clearwater.local.example.toml "
            "to clearwater.local.toml and set footage_path"
        )
    return f"footage folder configured but absent: {footage}"


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip every ``footage``-marked test when no footage folder is available."""
    reason = _footage_skip_reason()
    if reason is None:
        return
    skip = pytest.mark.skip(reason=reason)
    for item in items:
        if "footage" in item.keywords:
            item.add_marker(skip)
