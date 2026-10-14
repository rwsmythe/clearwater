"""Loader for the uncommitted local configuration file (``clearwater.local.toml``).

The file names two absolute paths: the read-only footage folder and the working
folder that receives every output. The committed template is
``clearwater.local.example.toml``. Nothing here requires either path to exist.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

TEMPLATE_NAME = "clearwater.local.example.toml"
CONFIG_NAME = "clearwater.local.toml"
_KEYS = ("footage_path", "working_path")


class LocalConfigError(Exception):
    """The local configuration is missing or invalid; the message names the template."""


@dataclass(frozen=True)
class LocalConfig:
    """The validated local configuration.

    Attributes:
        footage_path: Absolute path of the read-only footage folder.
        working_path: Absolute path of the working folder for all outputs.
    """

    footage_path: Path
    working_path: Path


def default_config_path() -> Path:
    """Return the default configuration path, ``<repo root>/clearwater.local.toml``.

    The repository root is located from this file's own location, never from the
    current working directory.

    Returns:
        The path of the (possibly absent) local configuration file.
    """
    return Path(__file__).resolve().parent.parent / CONFIG_NAME


def _fail(path: Path, problem: str) -> LocalConfigError:
    return LocalConfigError(f"{path}: {problem} (see {TEMPLATE_NAME} for the expected format)")


def _read_path(data: dict[str, object], key: str, path: Path) -> Path:
    value = data.get(key)
    if value is None:
        raise _fail(path, f"missing key '{key}'")
    if not isinstance(value, str):
        raise _fail(path, f"key '{key}' must be a string")
    result = Path(value)
    if not result.is_absolute():
        raise _fail(path, f"key '{key}' must be an absolute path, got '{value}'")
    return result


def load_local_config(path: Path | None = None) -> LocalConfig:
    """Load and validate the local configuration.

    Neither configured path is required to exist.

    Args:
        path: Configuration file to read; defaults to ``default_config_path()``.

    Returns:
        The validated configuration.

    Raises:
        LocalConfigError: If the file is missing or is not valid TOML, a key is
            missing or not a string, a path is relative, or the working folder
            equals or lies inside the footage folder.
    """
    config_path = default_config_path() if path is None else path
    try:
        with config_path.open("rb") as handle:
            data = tomllib.load(handle)
    except FileNotFoundError:
        raise _fail(config_path, "file not found") from None
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise _fail(config_path, f"cannot read as TOML: {exc}") from None
    footage, working = (_read_path(data, key, config_path) for key in _KEYS)
    # Compare lexically normalised paths: neither folder has to exist yet.
    footage_norm = Path(os.path.normpath(footage))
    working_norm = Path(os.path.normpath(working))
    if working_norm == footage_norm or footage_norm in working_norm.parents:
        raise _fail(config_path, "working_path must lie outside footage_path")
    return LocalConfig(footage_path=footage, working_path=working)


def footage_available(path: Path | None = None) -> bool:
    """Report whether the configured footage folder exists.

    Args:
        path: Configuration file to read; defaults to ``default_config_path()``.

    Returns:
        True only when the configuration loads and ``footage_path`` is an
        existing directory. Never raises.
    """
    try:
        return load_local_config(path).footage_path.is_dir()
    except (LocalConfigError, OSError):
        return False
