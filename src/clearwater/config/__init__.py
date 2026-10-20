"""Presets, settings and logging (WP3.15; plan 8.1 module ``config``).

Depends only on the standard library and :mod:`clearwater.interfaces` (IF-9, IF-10); it imports
nothing from ``core``, ``methods``, ``io``, ``jobs``, ``gui`` or any GPU or GUI library.
Round 0 ships :mod:`clearwater.config.paths`; the stores and the log follow.
"""

from __future__ import annotations

from .paths import (
    CACHE_FOLDER_NAME,
    LOG_FILE_NAME,
    LOG_FOLDER_NAME,
    POSIX_FOLDER_NAME,
    PRESETS_FOLDER_NAME,
    SETTINGS_FILE_NAME,
    WINDOWS_FOLDER_NAME,
    Locations,
    app_locations,
    ensure_directory,
)

__all__ = [
    "CACHE_FOLDER_NAME",
    "LOG_FILE_NAME",
    "LOG_FOLDER_NAME",
    "POSIX_FOLDER_NAME",
    "PRESETS_FOLDER_NAME",
    "SETTINGS_FILE_NAME",
    "WINDOWS_FOLDER_NAME",
    "Locations",
    "app_locations",
    "ensure_directory",
]
