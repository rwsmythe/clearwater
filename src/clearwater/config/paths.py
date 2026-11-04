r"""Per-OS app-data locations: the one place that reads the environment for a folder.

D37 (presets), D71 (proxy cache), D88 and N9 (log) and D89 (settings) all store under "app
data". The convention for each OS is required portability behaviour, not an N1 exception
(AD-25(a), amended 2026-11-04 for macOS):

==========  ==========================================  ========================================
Platform    Settings, presets, log, write journal       Proxy cache, worker scratch (not roamed)
==========  ==========================================  ========================================
Windows     ``%APPDATA%\Clearwater``                     ``%LOCALAPPDATA%\Clearwater\cache``
macOS       ``~/Library/Application Support/Clearwater``  ``~/Library/Caches/Clearwater``
Elsewhere   ``$XDG_CONFIG_HOME/clearwater``             ``$XDG_CACHE_HOME/clearwater``
==========  ==========================================  ========================================

A variable that is unset, empty or not an absolute path is ignored (XDG: relative values are
invalid) and the home-folder fallback applies: ``~/AppData/Roaming`` and ``~/AppData/Local`` on
Windows, ``~/.config`` and ``~/.cache`` elsewhere. macOS reads no variable: its folders are under
the home folder, and the XDG variables do not apply there (no migration from ``~/.config``:
AD-25(a)). Nothing here creates a folder unless :func:`ensure_directory` is called; every store
and the log take their folder as an argument, so tests pass ``tmp_path`` and never resolve the
real locations.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

WINDOWS_FOLDER_NAME = "Clearwater"
"""The application folder name under the Windows app-data roots."""

POSIX_FOLDER_NAME = "clearwater"
"""The application folder name under the XDG roots (lower-case, the XDG convention)."""

MACOS_FOLDER_NAME = "Clearwater"
"""The application folder name under ``~/Library/Application Support`` and
``~/Library/Caches`` on macOS (AD-25(a) as amended)."""

SETTINGS_FILE_NAME = "settings.json"
"""The settings document inside the config folder (D89)."""

PRESETS_FOLDER_NAME = "presets"
"""The preset folder inside the config folder (D37)."""

LOG_FOLDER_NAME = "logs"
"""The log folder inside the config folder (D88)."""

LOG_FILE_NAME = "clearwater.log"
"""The current log file inside the log folder (D88)."""

CACHE_FOLDER_NAME = "cache"
"""The proxy-cache folder name under ``%LOCALAPPDATA%\\Clearwater`` on Windows (D71)."""


@dataclass(frozen=True)
class Locations:
    """The resolved app-data folders.

    Attributes:
        config_dir: The folder holding the settings file, the preset folder and the log folder.
        cache_dir: The folder for the proxy cache (WP3.12), kept out of roaming profiles.
    """

    config_dir: Path
    cache_dir: Path

    @property
    def settings_file(self) -> Path:
        """The settings document: ``config_dir/settings.json``."""
        return self.config_dir / SETTINGS_FILE_NAME

    @property
    def presets_dir(self) -> Path:
        """The preset folder: ``config_dir/presets``."""
        return self.config_dir / PRESETS_FOLDER_NAME

    @property
    def log_dir(self) -> Path:
        """The log folder: ``config_dir/logs``."""
        return self.config_dir / LOG_FOLDER_NAME

    @property
    def log_file(self) -> Path:
        """The current log file: ``log_dir/clearwater.log``."""
        return self.log_dir / LOG_FILE_NAME


def _absolute_from_environment(environ: Mapping[str, str], name: str) -> Path | None:
    """Return the variable as an absolute path, or None when unset, empty or relative."""
    value = environ.get(name, "")
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else None


def app_locations(
    *,
    environ: Mapping[str, str] | None = None,
    platform: str | None = None,
    home: Path | None = None,
) -> Locations:
    """Resolve the app-data folders for this machine (AD-25(a)). Creates nothing.

    This is the only function in ``clearwater.config`` that reads the environment or the home
    folder, and with :func:`rename_replaces` the only one that reads the platform. The keyword
    arguments exist so a test can resolve for another platform or a fake environment;
    production code passes none.

    Args:
        environ: The environment to read; ``os.environ`` when None.
        platform: A ``sys.platform`` value; the running one when None. ``"win32"`` selects the
            Windows convention, ``"darwin"`` the macOS Library folders, anything else the XDG
            one.
        home: The home folder used by the fallbacks and by macOS; ``Path.home()`` when None.

    Returns:
        The config and cache folders.
    """
    env = os.environ if environ is None else environ
    kind = sys.platform if platform is None else platform
    if kind == "win32":
        roaming = _absolute_from_environment(env, "APPDATA")
        local = _absolute_from_environment(env, "LOCALAPPDATA")
        if roaming is None or local is None:
            base = Path.home() if home is None else home
            roaming = roaming or base / "AppData" / "Roaming"
            local = local or base / "AppData" / "Local"
        found = Locations(
            config_dir=roaming / WINDOWS_FOLDER_NAME,
            cache_dir=local / WINDOWS_FOLDER_NAME / CACHE_FOLDER_NAME,
        )
    elif kind == "darwin":
        library = (Path.home() if home is None else home) / "Library"
        found = Locations(
            config_dir=library / "Application Support" / MACOS_FOLDER_NAME,
            cache_dir=library / "Caches" / MACOS_FOLDER_NAME,
        )
    else:
        config_root = _absolute_from_environment(env, "XDG_CONFIG_HOME")
        cache_root = _absolute_from_environment(env, "XDG_CACHE_HOME")
        if config_root is None or cache_root is None:
            base = Path.home() if home is None else home
            config_root = config_root or base / ".config"
            cache_root = cache_root or base / ".cache"
        found = Locations(
            config_dir=config_root / POSIX_FOLDER_NAME,
            cache_dir=cache_root / POSIX_FOLDER_NAME,
        )
    return found


def rename_replaces(platform: str | None = None) -> bool:
    """Tell whether ``os.rename`` silently replaces an existing target on a platform.

    False on Windows, where ``os.rename`` refuses an existing target; True elsewhere (POSIX
    ``rename``). The preset store asks here instead of reading the platform itself, so this
    module stays ``clearwater.config``'s one platform site (P73, DR-34(a)).

    Args:
        platform: A ``sys.platform`` value; the running one when None.

    Returns:
        Whether a rename can replace another file.
    """
    kind = sys.platform if platform is None else platform
    return kind != "win32"


def ensure_directory(path: Path) -> Path:
    """Create a folder (and its parents) if it is missing; the first-use creation rule.

    Args:
        path: The folder.

    Returns:
        ``path``, for chaining.

    Raises:
        OSError: The folder cannot be created, or ``path`` exists and is not a folder.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path
