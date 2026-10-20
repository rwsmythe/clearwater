"""Presets, settings and logging (WP3.15; plan 8.1 module ``config``).

Depends only on the standard library and :mod:`clearwater.interfaces` (IF-9, IF-10); it imports
nothing from ``core``, ``methods``, ``io``, ``jobs``, ``gui`` or any GPU or GUI library.

======================  ==========================================================
Module                  Contents
======================  ==========================================================
``paths``               per-OS app-data locations (AD-25(a))
``settings_store``      load and save the settings file (D89, G13)
``presets``             the preset store and the starter presets (G6, D37, D38)
``migration``           ``format_version`` migration registry
``keys``                the DR-32 string-key check
``atomic``              atomic text-file writes
``log``                 the rotating log (D88, N9)
======================  ==========================================================
"""

from __future__ import annotations

from .atomic import atomic_write_text
from .keys import check_parameter_set_keys, check_string_keys
from .log import configure_logging, shutdown_logging
from .migration import DEFAULT_MIGRATIONS, MigrationRegistry, migrate
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
from .presets import (
    PresetEntry,
    PresetError,
    PresetImportError,
    PresetImportResult,
    PresetStore,
    new_parameter_set,
    starter_presets,
    validate_preset_name,
)
from .settings_store import load_settings, save_settings

__all__ = [
    "CACHE_FOLDER_NAME",
    "DEFAULT_MIGRATIONS",
    "LOG_FILE_NAME",
    "LOG_FOLDER_NAME",
    "POSIX_FOLDER_NAME",
    "PRESETS_FOLDER_NAME",
    "SETTINGS_FILE_NAME",
    "WINDOWS_FOLDER_NAME",
    "Locations",
    "MigrationRegistry",
    "PresetEntry",
    "PresetError",
    "PresetImportError",
    "PresetImportResult",
    "PresetStore",
    "app_locations",
    "atomic_write_text",
    "check_parameter_set_keys",
    "check_string_keys",
    "configure_logging",
    "ensure_directory",
    "load_settings",
    "migrate",
    "new_parameter_set",
    "save_settings",
    "shutdown_logging",
    "starter_presets",
    "validate_preset_name",
]
