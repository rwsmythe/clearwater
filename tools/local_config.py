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

VIDEO_EXTENSIONS = frozenset({".mp4", ".mov", ".360"})
"""Lower-case suffixes of the video files Clearwater reads (the one definition)."""


class LocalConfigError(Exception):
    """The local configuration is missing or invalid; the message names the template."""


class FootageLookupError(LocalConfigError):
    """A footage file could not be found, or not uniquely, by its stem.

    Attributes:
        matches: Every matching file, sorted; empty when nothing matched (and when the
            footage folder itself could not be searched).
    """

    def __init__(self, message: str, matches: tuple[Path, ...] = ()) -> None:
        """Store the message and the matching paths.

        Args:
            message: The one-line description.
            matches: The matching files; empty when none.
        """
        super().__init__(message)
        self.matches = matches


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
    except UnicodeDecodeError:
        raise _fail(config_path, "file must be UTF-8 text (not UTF-16)") from None
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


def _check_stem(stem: str) -> None:
    """Refuse anything that is not a bare file stem (empty, a path, or carrying a video suffix)."""
    separators = {"/", "\\", os.sep} | ({os.altsep} if os.altsep else set())
    if not stem or any(sep in stem for sep in separators):
        raise ValueError(f"footage stem must be a bare file stem, got {stem!r}")
    if Path(stem).suffix.lower() in VIDEO_EXTENSIONS:
        raise ValueError(f"footage stem must not carry a video suffix, got {stem!r}")


def _raise_walk_error(error: OSError) -> None:
    """Turn a directory the walk could not read into a lookup failure (never a silent skip)."""
    raise FootageLookupError(f"cannot search the footage folder: {error}") from error


def find_footage_file(stem: str, root: Path | None = None) -> Path:
    """Find the one video file with the given stem anywhere under the footage folder.

    The walk is recursive. A file matches when its stem equals ``stem`` case-insensitively
    (``str.casefold`` on both) and its lower-cased suffix is in :data:`VIDEO_EXTENSIONS`,
    so ``GX011628`` matches ``Snorkel/GX011628.mp4`` and ``GX011628.MP4`` but never a
    ``.LRV``, ``.THM``, ``.json`` or ``.png`` of that stem, nor a longer stem. The walk
    never leaves ``root``: it does not descend into a directory symlink or a Windows
    junction, and it skips a matching file that is a symlink. It never writes, never
    changes the working directory, and keeps no state between calls; the outcome does not
    depend on the order the file system lists entries in.

    Args:
        stem: The bare file stem, e.g. ``"GX011628"``: not empty, no path separator, no
            video suffix.
        root: The folder to search; defaults to ``load_local_config().footage_path``.

    Returns:
        ``root / <relative path of the match>`` (not resolved).

    Raises:
        ValueError: ``stem`` is not a bare stem.
        LocalConfigError: ``root`` was not given and the configuration does not load.
        FootageLookupError: ``root`` is missing, not a directory or unreadable (``matches``
            empty); no file matches (message contains "not in the footage folder",
            ``matches`` empty); or two or more match (the message names every match
            relative to ``root``, ``matches`` holds them sorted).
    """
    _check_stem(stem)
    search = load_local_config().footage_path if root is None else root
    if not search.is_dir():
        raise FootageLookupError(f"footage folder {search} is missing or not a directory")
    wanted = stem.casefold()
    found: list[str] = []
    for folder, dirnames, filenames in os.walk(search, onerror=_raise_walk_error):
        # os.walk(followlinks=False) still descends into Windows junctions: prune them here.
        dirnames[:] = [
            name
            for name in dirnames
            if not os.path.islink(os.path.join(folder, name))
            and not os.path.isjunction(os.path.join(folder, name))
        ]
        for name in filenames:
            path = Path(folder, name)
            if path.suffix.lower() not in VIDEO_EXTENSIONS or path.stem.casefold() != wanted:
                continue
            if path.is_symlink() or not path.is_file():
                continue
            found.append(path.relative_to(search).as_posix())
    found.sort()
    matches = tuple(search / relative for relative in found)
    if not matches:
        raise FootageLookupError(f"{stem} is not in the footage folder {search}")
    if len(matches) > 1:
        names = ", ".join(found)
        raise FootageLookupError(
            f"{stem} matches {len(matches)} files in the footage folder {search}: {names}",
            matches,
        )
    return matches[0]
