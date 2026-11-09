"""WP6.5 A4: ``tests/conftest.py`` redirects ``HOME`` on POSIX, and only there.

On macOS Clearwater's settings and cache live under ``Path.home() / "Library"`` (on Linux
under the XDG folders), so the autouse fixture ``_posix_home_redirect`` points ``HOME`` and
``XDG_CONFIG_HOME`` / ``XDG_DATA_HOME`` / ``XDG_CACHE_HOME`` / ``XDG_STATE_HOME`` at a fresh
folder under the session temp root for every test function. The POSIX tests prove
``Path.home()``, ``os.path.expanduser("~")``, ``~/Library``, the four XDG names and
``app_locations()`` resolve inside that folder, and that a test's own ``monkeypatch`` still
wins; they skip on Windows by marker. The Windows test proves the fixture leaves ``HOME`` and
the XDG names as the session found them (Windows isolation runs through ``APPDATA`` /
``LOCALAPPDATA``).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from clearwater.config.paths import app_locations

HOME_AT_IMPORT = os.environ.get("HOME")
"""``HOME`` as collection found it, before any function-scoped fixture ran."""

XDG_NAMES = ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME")
"""The four XDG base-directory names the redirect sets (WP6.5 QA fix, CHARC ruling)."""

XDG_AT_IMPORT = {name: os.environ.get(name) for name in XDG_NAMES}
"""The XDG names as collection found them."""

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
    expected = {
        "XDG_CONFIG_HOME": home / ".config",
        "XDG_DATA_HOME": home / ".local" / "share",
        "XDG_CACHE_HOME": home / ".cache",
        "XDG_STATE_HOME": home / ".local" / "state",
    }
    assert set(expected) == set(XDG_NAMES)
    for name, folder in expected.items():
        assert Path(os.environ[name]) == folder, name
    locations = app_locations()
    if sys.platform == "darwin":
        assert locations.config_dir.is_relative_to(home / "Library")
        assert locations.cache_dir.is_relative_to(home / "Library")
    else:
        assert locations.config_dir.is_relative_to(home / ".config")
        assert locations.cache_dir.is_relative_to(home / ".cache")


@posix_only
def test_each_test_gets_its_own_home(tmp_path_factory: pytest.TempPathFactory) -> None:
    """A second test sees a fresh, empty folder (the first one's is not reused)."""
    _redirected_root(tmp_path_factory)


@posix_only
def test_a_tests_own_monkeypatch_still_wins(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A test that sets ``HOME`` or an XDG name itself sees its own value, not the redirect."""
    monkeypatch.setenv("HOME", str(tmp_path / "mine"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "mine-config"))
    assert Path.home() == tmp_path / "mine"
    assert os.environ["XDG_CONFIG_HOME"] == str(tmp_path / "mine-config")


@pytest.mark.skipif(sys.platform != "win32", reason="the Windows half of the A4 rule")
def test_windows_home_is_left_as_the_session_found_it() -> None:
    assert os.environ.get("HOME") == HOME_AT_IMPORT
    assert {name: os.environ.get(name) for name in XDG_NAMES} == XDG_AT_IMPORT
