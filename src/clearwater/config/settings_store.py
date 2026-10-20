"""The settings file: load and save IF-10 ``Settings`` in an app-data folder (D89, G13).

The document is ``settings.json`` in the folder the caller passes (the config folder from
:mod:`clearwater.config.paths`). Loading never needs the file to exist: first run is
``Settings()``, whose defaults live in the frozen dataclass and are not restated here. A
corrupt file is moved aside, never overwritten silently; a file from a newer Clearwater is
refused by name and left exactly as it was.
"""

from __future__ import annotations

import dataclasses
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from clearwater.interfaces import FormatError, Settings, UnsupportedFormatVersionError
from clearwater.interfaces.parameters import loads_object

from .atomic import atomic_write_text
from .keys import check_parameter_set_keys, check_string_keys
from .migration import MigrationRegistry, migrate
from .paths import SETTINGS_FILE_NAME

_log = logging.getLogger(__name__)

_PNG_BIT_DEPTHS = (8, 16)
_QUALITY_LEVELS = ("high", "standard", "draft")


def load_settings(folder: Path, *, migrations: MigrationRegistry | None = None) -> Settings:
    """Load the settings from ``folder``, or the defaults when there is no file (D89).

    A document of an older format version is migrated in memory and not rewritten. A field
    outside its allowed range (``png_bit_depth`` not 8 or 16, ``quality_level`` not
    high/standard/draft, ``cache_limit_bytes`` negative) takes its default with a logged
    warning. Encoder names are not checked here (D74).

    A file that cannot be read, is not valid JSON, or fails IF-10 (missing, unknown or
    wrong-type fields, non-string keys, a missing or non-integer ``format_version``) is renamed
    beside itself to ``settings.json.bad-<UTC stamp>``, a warning is logged, and ``Settings()``
    is returned. If the rename also fails the warning says so and ``Settings()`` is returned.

    Args:
        folder: The folder holding ``settings.json``.
        migrations: The migration steps; the product's (empty) registry when None.

    Returns:
        The stored settings, or ``Settings()`` on first run or after a corrupt file.

    Raises:
        UnsupportedFormatVersionError: The file carries an integer ``format_version`` that is
            newer than this Clearwater reads, or older with no migration step. The file is left
            untouched.
    """
    path = folder / SETTINGS_FILE_NAME
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return Settings()
    except (OSError, UnicodeDecodeError) as error:
        return _set_aside(path, f"cannot be read: {error}")
    try:
        settings = _decode(text, migrations)
    except UnsupportedFormatVersionError:
        raise
    except FormatError as error:
        return _set_aside(path, f"is not valid settings: {error}")
    return _with_valid_values(settings)


def save_settings(folder: Path, settings: Settings) -> Path:
    """Write the settings to ``folder/settings.json`` atomically (D89).

    The folder is created when missing. The file is written to a temporary sibling and moved
    into place, so a failure leaves the previous file intact.

    Args:
        folder: The folder holding ``settings.json``.
        settings: The settings to store, including ``last_parameters``.

    Returns:
        The path written.

    Raises:
        FormatError: ``last_parameters`` holds a non-string mapping key (DR-32) or a non-finite
            number.
        ValueError: ``last_parameters.created`` is not timezone-aware.
        OSError: The file cannot be written.
    """
    if settings.last_parameters is not None:
        check_parameter_set_keys(settings.last_parameters, "last_parameters")
    text = settings.to_json() + "\n"
    path = folder / SETTINGS_FILE_NAME
    atomic_write_text(path, text)
    return path


def _require_integer_version(data: dict[str, Any], where: str) -> None:
    """Treat a missing or non-integer ``format_version`` as a malformed file, not a newer one."""
    version = data.get("format_version")
    if isinstance(version, bool) or not isinstance(version, int):
        raise FormatError(f"{where} format_version {version!r} is missing or not an integer")


def _decode(text: str, migrations: MigrationRegistry | None) -> Settings:
    """Decode, migrate, key-check and build the settings from JSON text."""
    data = loads_object(text)
    _require_integer_version(data, "settings")
    data = migrate("settings", data, migrations)
    last = data.get("last_parameters")
    if isinstance(last, dict):
        _require_integer_version(last, "last_parameters")
        data = {**data, "last_parameters": migrate("preset", last, migrations)}
    check_string_keys(data, "settings")
    try:
        migrated_text = json.dumps(data, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise FormatError(f"migrated settings are not JSON: {error}") from error
    return Settings.from_json(migrated_text)


def _with_valid_values(settings: Settings) -> Settings:
    """Replace each out-of-range field by its default, logging a warning per field."""
    defaults = Settings()
    if settings.png_bit_depth not in _PNG_BIT_DEPTHS:
        _warn_out_of_range("png_bit_depth", settings.png_bit_depth, defaults.png_bit_depth)
        settings = dataclasses.replace(settings, png_bit_depth=defaults.png_bit_depth)
    if settings.quality_level not in _QUALITY_LEVELS:
        _warn_out_of_range("quality_level", settings.quality_level, defaults.quality_level)
        settings = dataclasses.replace(settings, quality_level=defaults.quality_level)
    if settings.cache_limit_bytes < 0:
        _warn_out_of_range(
            "cache_limit_bytes", settings.cache_limit_bytes, defaults.cache_limit_bytes
        )
        settings = dataclasses.replace(settings, cache_limit_bytes=defaults.cache_limit_bytes)
    return settings


def _warn_out_of_range(name: str, value: object, default: object) -> None:
    """Log that a settings field was out of range and its default is used."""
    _log.warning("settings: %s=%r is out of range; using the default %r", name, value, default)


def _set_aside(path: Path, reason: str) -> Settings:
    """Rename a bad settings file beside itself and return the defaults."""
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    target = path.with_name(f"{path.name}.bad-{stamp}")
    counter = 1
    while target.exists():
        counter += 1
        target = path.with_name(f"{path.name}.bad-{stamp}-{counter}")
    try:
        path.rename(target)
    except OSError as error:
        _log.warning(
            "settings file %s %s; it could not be set aside (%s); using defaults",
            path,
            reason,
            error,
        )
    else:
        _log.warning("settings file %s %s; moved to %s; using defaults", path, reason, target)
    return Settings()
