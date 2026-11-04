"""WP3.15: the per-OS app-data resolver (AD-25(a)) and the dependency rule for ``config``."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from clearwater.config.paths import Locations, app_locations, ensure_directory


def _win_env(tmp_path: Path) -> dict[str, str]:
    return {"APPDATA": str(tmp_path / "Roaming"), "LOCALAPPDATA": str(tmp_path / "Local")}


def test_windows_uses_appdata_and_localappdata(tmp_path: Path) -> None:
    found = app_locations(environ=_win_env(tmp_path), platform="win32", home=tmp_path / "h")
    assert found.config_dir == tmp_path / "Roaming" / "Clearwater"
    assert found.cache_dir == tmp_path / "Local" / "Clearwater" / "cache"
    assert found.settings_file == found.config_dir / "settings.json"
    assert found.presets_dir == found.config_dir / "presets"
    assert found.log_dir == found.config_dir / "logs"
    assert found.log_file == found.config_dir / "logs" / "clearwater.log"


def test_windows_falls_back_to_home_when_unset_empty_or_relative(tmp_path: Path) -> None:
    home = tmp_path / "home"
    for env in ({}, {"APPDATA": "", "LOCALAPPDATA": ""}, {"APPDATA": "rel", "LOCALAPPDATA": "rel"}):
        found = app_locations(environ=env, platform="win32", home=home)
        assert found.config_dir == home / "AppData" / "Roaming" / "Clearwater"
        assert found.cache_dir == home / "AppData" / "Local" / "Clearwater" / "cache"


def test_windows_mixed_one_variable_set(tmp_path: Path) -> None:
    home = tmp_path / "home"
    env = {"APPDATA": str(tmp_path / "R")}
    found = app_locations(environ=env, platform="win32", home=home)
    assert found.config_dir == tmp_path / "R" / "Clearwater"
    assert found.cache_dir == home / "AppData" / "Local" / "Clearwater" / "cache"


@pytest.mark.parametrize("platform", ["linux"])
def test_xdg_variables_win_elsewhere(tmp_path: Path, platform: str) -> None:
    env = {"XDG_CONFIG_HOME": str(tmp_path / "cfg"), "XDG_CACHE_HOME": str(tmp_path / "cch")}
    found = app_locations(environ=env, platform=platform, home=tmp_path / "h")
    assert found.config_dir == tmp_path / "cfg" / "clearwater"
    assert found.cache_dir == tmp_path / "cch" / "clearwater"


def test_xdg_fallbacks_and_relative_values_ignored(tmp_path: Path) -> None:
    home = tmp_path / "home"
    for env in ({}, {"XDG_CONFIG_HOME": "rel/cfg", "XDG_CACHE_HOME": ""}):
        found = app_locations(environ=env, platform="linux", home=home)
        assert found.config_dir == home / ".config" / "clearwater"
        assert found.cache_dir == home / ".cache" / "clearwater"


def test_resolver_creates_nothing(tmp_path: Path) -> None:
    found = app_locations(environ=_win_env(tmp_path), platform="win32", home=tmp_path)
    assert not found.config_dir.exists()
    assert not found.cache_dir.exists()
    assert list(tmp_path.iterdir()) == []


def test_default_arguments_read_the_process_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", str(tmp_path / "A"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "L"))
    found = app_locations()
    assert found == Locations(
        config_dir=tmp_path / "A" / "Clearwater", cache_dir=tmp_path / "L" / "Clearwater" / "cache"
    )


def test_ensure_directory_creates_parents_and_is_idempotent(tmp_path: Path) -> None:
    target = tmp_path / "a" / "b" / "c"
    assert ensure_directory(target) == target
    assert target.is_dir()
    assert ensure_directory(target) == target


def test_ensure_directory_refuses_a_file(tmp_path: Path) -> None:
    blocker = tmp_path / "blocker"
    blocker.write_text("x", encoding="utf-8")
    with pytest.raises(OSError):
        ensure_directory(blocker)


def test_importing_config_loads_no_forbidden_module() -> None:
    code = (
        "import sys, clearwater.config\n"
        "bad = [m for m in sys.modules if m.split('.')[0] in {'PySide6', 'cupy'} "
        "or m.startswith(('clearwater.gui', 'clearwater.jobs', 'clearwater.methods', "
        "'clearwater.core', 'clearwater.io'))]\n"
        "print(bad)\n"
        "raise SystemExit(1 if bad else 0)\n"
    )
    done = subprocess.run(
        [sys.executable, "-I", "-c", code], capture_output=True, text=True, check=False
    )
    assert done.returncode == 0, done.stdout + done.stderr
