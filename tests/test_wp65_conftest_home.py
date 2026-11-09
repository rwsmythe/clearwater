"""WP6.5 A4: ``tests/conftest.py`` redirects ``HOME`` on POSIX, and only there.

On macOS Clearwater's settings and cache live under ``Path.home() / "Library"``, so the
autouse fixture ``_posix_home_redirect`` points ``HOME`` at a fresh folder under the session
temp root for every test function. The POSIX tests prove ``Path.home()``,
``os.path.expanduser("~")``, ``~/Library`` and ``app_locations()`` resolve inside that
folder; they skip on Windows by marker. The Windows test proves the fixture leaves ``HOME``
as the session found it (Windows isolation runs through ``APPDATA`` / ``LOCALAPPDATA``).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from clearwater.config.paths import app_locations

HOME_AT_IMPORT = os.environ.get("HOME")
"""``HOME`` as collection found it, before any function-scoped fixture ran."""

posix_only = pytest.mark.skipif(
    sys.platform == "win32", reason="the HOME redirect is POSIX-only (WP6.5 A4)"
)


def _redirected_root(factory: pytest.TempPathFactory) -> Path:
    """The redirect folder, checked to lie under the session temp root and be fresh."""
    home = Path(os.environ["HOME"])
    assert home.is_relative_to(factory.getbasetemp())
    assert home.name.startswith("home")
    assert home.is_dir()
    assert list(home.iterdir()) == []
    return home


@posix_only
def test_home_and_library_resolve_under_the_disposable_root(
    tmp_path_factory: pytest.TempPathFactory, tmp_path: Path
) -> None:
    home = _redirected_root(tmp_path_factory)
    assert os.environ["HOME"] != HOME_AT_IMPORT
    assert Path.home() == home
    assert Path(os.path.expanduser("~")) == home
    assert Path("~/Library").expanduser() == home / "Library"
    assert not home.is_relative_to(tmp_path)  # beside the test's tmp_path, not inside it
    locations = app_locations()
    if sys.platform == "darwin":
        assert locations.config_dir.is_relative_to(home / "Library")
        assert locations.cache_dir.is_relative_to(home / "Library")
    elif "XDG_CONFIG_HOME" not in os.environ and "XDG_CACHE_HOME" not in os.environ:
        assert locations.config_dir.is_relative_to(home)
        assert locations.cache_dir.is_relative_to(home)


@posix_only
def test_each_test_gets_its_own_home(tmp_path_factory: pytest.TempPathFactory) -> None:
    """A second test sees a fresh, empty folder (the first one's is not reused)."""
    _redirected_root(tmp_path_factory)


@pytest.mark.skipif(sys.platform != "win32", reason="the Windows half of the A4 rule")
def test_windows_home_is_left_as_the_session_found_it() -> None:
    assert os.environ.get("HOME") == HOME_AT_IMPORT
