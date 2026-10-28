"""Shared pytest configuration: the footage guard and the footage-test skip.

Temp-root guard (WP-T1, closes DR-21). ``pytest --basetemp=<dir>`` deletes and
recreates ``<dir>``, and ``TMP``/``TEMP``/``TMPDIR``/``PYTEST_DEBUG_TEMPROOT``
decide where pytest makes its folders. Pointed at the owner's footage folder,
a run could delete or write footage. A ``pytest_configure`` hook (``tryfirst``)
therefore refuses to start (``pytest.UsageError``, exit code 4, message naming
the footage folder and the offending root) when the temp root would be:

* ``--basetemp``: inside the footage folder, equal to it, or an ancestor of it
  (pytest removes the whole basetemp tree, which would take the footage with it);
* otherwise the default temp root (``PYTEST_DEBUG_TEMPROOT`` if set, else the one
  directory ``tempfile.gettempdir()`` would pick), inside or equal to the footage
  folder, or when pytest's own ``pytest-of-<user>`` folder under that root (or any
  other ``pytest-of-*`` entry there) is, or leads into, the footage folder.

Paths are compared fully resolved (symlinks and junctions followed; a Windows
extended-length prefix removed) and, on Windows, case-insensitively, then by file
identity (``os.path.samefile``) for any existing ancestor. A legitimate basetemp,
such as a folder under the working folder, passes. The guard is inert, and silent,
when there is no valid local configuration (none, an invalid one, no footage key):
it never fails a run on a machine without footage. A configured footage folder that
does not exist is NOT inert: it may be a disconnected drive, so the guard stays
active (fail safe). If a check it needs cannot be made (an error resolving the temp
root or pytest's own ``pytest-of-<user>`` folder), the guard refuses and says so.

Scope of the guarantee: the guard refuses before pytest creates or clears any
temporary FOLDER; not the TEMP-variable file writes. Pytest starts output capture
before it loads any conftest, and capture (and ``tempfile``'s writability probe)
makes short-lived, randomly named files in the ``TMPDIR``/``TEMP``/``TMP``
directory. A guard in this file cannot stop that, so with those variables pointing
into the footage folder, or with ``TMP`` there next to any other setting, such files
come and go before the refusal; nothing existing is touched (DR-22).

Ordering: this hook runs before pytest's temp-path factory is built
(``_pytest/tmpdir.py`` ``pytest_configure``), and pytest creates or clears a temp
folder only when the first ``tmp_path`` is requested (``getbasetemp``). The cache
provider's ``--cache-clear`` clears only ``.pytest_cache`` subfolders and runs after
this hook (a conftest registers after the built-in plugins and later-registered
hooks run first); tests pin both.

With pytest-xdist 3.8.0 local popen workers, the controller guard configures
before session startup launches workers. ``xdist/workermanage.py:337-341``
derives each worker's ``popen-gwN`` basetemp below the controller's basetemp;
``xdist/remote.py:400,420-427`` assigns it before the worker configures its
plugins and runs this guard again. Controller refusal therefore precedes
worker temp-root creation; the worker checks its assigned child root as well.

When the guard loads (pytest 8.4.2, ``_pytest/config/__init__.py``
``_set_initial_conftests`` and ``_try_load_conftest``): for every existing path
argument (``testpaths`` when none is given) pytest loads the conftest files found at
or above it, up to ``--confcutdir`` (default: the ini file's folder), and in the
``test*`` subfolders of an argument that is a folder. So ``pytest``, ``pytest tests``,
``pytest tests/x.py`` and ``pytest .`` at the repository root load this file;
``pytest tools`` does not. ``--noconftest`` suppresses it; so does a ``--confcutdir``
below ``tests/``; ``--rootdir`` alone and ``-p no:conftest`` do not. With another
ini file (``-c``) that lacks ``pythonpath = ["tools"]`` the import below fails
(out of envelope). See ``docs/reports/wp-t1-pytest-guard.md``.
"""

from __future__ import annotations

import getpass
import os
import tempfile
from pathlib import Path

import pytest

from local_config import LocalConfigError, footage_available, load_local_config

pytest_plugins = (
    ["fixture_plugin"] if Path(__file__).with_name("fixture_plugin.py").is_file() else []
)

_PYTEST_OF = "pytest-of-"


def _canonical(path: str | os.PathLike[str]) -> Path:
    """Return ``path`` made absolute, fully resolved and case-normalised.

    Args:
        path: A path that need not exist.

    Returns:
        The path as ``os.path.abspath`` then ``Path.resolve`` leave it (pytest's own
        order for ``--basetemp``), with any Windows extended-length prefix removed and
        the case normalised on Windows.

    Raises:
        OSError: If the path cannot be resolved.
        RuntimeError: If resolving meets a symlink loop.
    """
    text = str(Path(os.path.abspath(os.fspath(path))).resolve())
    if os.name == "nt":
        # resolve() keeps an extended-length prefix that was in the input; strip it to compare.
        # Other forms (\\?\Volume{GUID}\...) stay as they are; samefile() covers them.
        extended, unc = "\\\\?\\", "\\\\?\\UNC\\"
        if text.startswith(unc):
            text = "\\\\" + text[len(unc) :]
        elif text.startswith(extended) and text[4:5].isalpha() and text[5:6] == ":":
            text = text[len(extended) :]
    return Path(os.path.normcase(text))


def _inside_or_equal(candidate: Path, folder: Path) -> bool:
    """Report whether ``candidate`` equals ``folder`` or lies below it.

    The canonical-path comparison is backed by file identity: an existing
    ancestor of ``candidate`` (or ``candidate`` itself) that is the same file as
    ``folder`` counts, which catches spellings the text comparison misses (8.3
    short names, subst or mapped drives, bind mounts).
    """
    if candidate == folder or folder in candidate.parents:
        return True
    for ancestor in (candidate, *candidate.parents):
        try:
            if os.path.samefile(ancestor, folder):
                return True
        except OSError:
            continue  # absent (a not-yet-existing tail) or unreadable
    return False


def _holds_pytest_of(root: Path, folder: Path) -> bool:
    """Report whether ``folder`` lies inside ``root/pytest-of-*``, where pytest writes."""
    try:
        parts = folder.relative_to(root).parts
    except ValueError:
        return False
    return bool(parts) and os.path.normcase(parts[0]).startswith(_PYTEST_OF)


def _pytest_user() -> str:
    """Return the user name pytest puts in ``pytest-of-<user>`` (``tmpdir.py`` ``get_user``)."""
    try:
        return getpass.getuser() or "unknown"
    except (ImportError, OSError, KeyError):
        return "unknown"


def _pytest_of_child_in(root: Path, footage: Path) -> Path | None:
    """Return a ``root/pytest-of-*`` entry that is, or leads into, ``footage``, if any.

    pytest writes its numbered folders into ``root/pytest-of-<user>``
    (``tmpdir.py:160``; ``pytest-of-unknown`` is its fallback, ``:165``). Those two
    children are checked DIRECTLY, listed or not, so a link there is found even when
    the root cannot be listed or the link's spelling differs in case. An error
    resolving them propagates: the check could not be made. Any other ``pytest-of-*``
    entry found by listing the root is a best-effort extra; a listing error is ignored.

    Args:
        root: The canonical temp root.
        footage: The canonical footage folder.

    Returns:
        The offending entry, or None.

    Raises:
        OSError: If pytest's own child cannot be resolved.
        RuntimeError: If resolving it meets a symlink loop.
        ValueError: If a path is not usable.
    """
    direct = [root / f"{_PYTEST_OF}{name}" for name in (_pytest_user(), "unknown")]
    for child in direct:
        if _inside_or_equal(_canonical(child), footage):
            return child
    try:
        listed = [c for c in root.iterdir() if os.path.normcase(c.name).startswith(_PYTEST_OF)]
    except OSError:
        return None
    for child in listed:
        try:
            if _inside_or_equal(_canonical(child), footage):
                return child
        except (OSError, RuntimeError, ValueError):
            continue
    return None


def _temp_root_candidates() -> list[str]:
    """Return the temp-root candidates to check, without touching disk.

    ``tempfile.gettempdir()`` picks the first candidate in which it can create and
    delete a probe file, which would write inside a footage folder named by
    ``TMPDIR``/``TEMP``/``TMP``. The guard mirrors the candidate list
    (``tempfile._candidate_tempdir_list``, Python 3.12) and approximates the probe
    with "an existing directory that ``os.access`` accepts for writing", stopping
    there. Candidates before the chosen one are still returned, so the approximation
    can only over-refuse, never miss the root CPython would use.

    Returns:
        The cached ``tempfile.tempdir`` alone if already chosen, else every
        candidate up to and including the first usable one.
    """
    if tempfile.tempdir is not None:
        return [os.fsdecode(tempfile.tempdir)]
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
    chosen: list[str] = []
    for candidate in candidates:
        chosen.append(candidate)
        if os.path.isdir(candidate) and os.access(candidate, os.W_OK):
            break
    return chosen


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
            "a default temp-root candidate (TMPDIR/TEMP/TMP or a system default)",
            _temp_root_candidates(),
        )
    for root_text in roots:
        root = _canonical(root_text)
        # pytest makes pytest-of-<user>/ under the root, so a footage folder there is hit too.
        if _inside_or_equal(root, footage) or _holds_pytest_of(root, footage):
            return f"{origin} {root_text}"
        if (child := _pytest_of_child_in(root, footage)) is not None:
            return (
                f"{origin} {root_text} (its {child.name} entry is or leads into the footage folder)"
            )
    return None


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """Refuse to start when pytest's temp root would lie in the footage folder.

    Runs before pytest's own ``pytest_configure`` builds the temp-path factory, and
    so before the first ``tmp_path`` creates or clears any temp folder (see the
    module docstring for what this does not cover). Inert without a valid local
    configuration.

    Args:
        config: The pytest configuration.

    Raises:
        pytest.UsageError: If the temp root equals, lies inside (or, for
            ``--basetemp``, contains) the configured footage folder, or the check
            could not be made (an error resolving the temp root).
    """
    try:
        footage_raw = load_local_config().footage_path
    except (LocalConfigError, OSError):
        return
    try:
        footage = _canonical(footage_raw)
    except ValueError:
        return  # not a usable path (embedded NUL): an invalid configuration, so inert
    except (OSError, RuntimeError):
        # Unresolvable (e.g. a symlink loop): compare its absolute spelling and file identity.
        footage = Path(os.path.normcase(os.path.abspath(footage_raw)))
    try:
        offending = _offending_root(config, footage)
    except (OSError, RuntimeError, ValueError) as exc:
        raise pytest.UsageError(
            f"footage guard: the check could not be made (cannot resolve the pytest temp "
            f"root: {exc}); refusing to run with a footage folder configured at {footage_raw}"
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
        that distinguishes "not configured" from "configured but not an existing folder".
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
    return f"footage folder configured but not an existing folder: {footage}"


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip every ``footage``-marked test when no footage folder is available."""
    reason = _footage_skip_reason()
    if reason is None:
        return
    skip = pytest.mark.skip(reason=reason)
    for item in items:
        if "footage" in item.keywords:
            item.add_marker(skip)
