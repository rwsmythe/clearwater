"""The preset store: save, load, list, rename, delete, import, export and starters (G6).

A preset is one AD-13 JSON file ``<name>.json`` in the preset folder the caller passes: the
object has ``format_version``, ``method``, ``parameters``, ``created`` and ``app_version`` and
no name key, so the name is the file stem. A preset carries no provenance: the provenance keys
``source`` and ``settings`` are dropped on save and import (every other unknown key is still
refused by IF-9). Every operation takes names, never paths, except import and export, whose
other end is a file the user chose. Rename and delete act only on a regular, parseable preset
file inside the folder, so neither can reach another file.

This module imports no correction method: import validation uses the parameter schemas the
caller passes in.
"""

from __future__ import annotations

import dataclasses
import os
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from clearwater import __version__
from clearwater.interfaces import (
    FormatError,
    Parameter,
    ParameterProblem,
    ParameterSet,
    ParameterValue,
    validate_parameter_set,
)
from clearwater.interfaces.parameters import loads_object

from .atomic import atomic_write_text
from .keys import check_parameter_set_keys, check_string_keys
from .migration import MigrationRegistry, migrate

STARTER_SNORKEL = "Snorkel (shallow)"
"""The first starter preset's name (AD-13)."""

STARTER_SCUBA = "Scuba (deep)"
"""The second starter preset's name (AD-13)."""

STARTER_METHOD = "c3"
"""The method both starter presets use: the default, C3 (D16)."""

STARTERS_MARKER_NAME = ".starters-installed"
"""The preset-folder file recording that the starters were installed and are not re-created."""

MAX_PRESET_BYTES = 1024 * 1024
"""The largest preset file read (1 MiB); a bigger one is refused with its size and this cap."""

MAX_NAME_LENGTH = 100
"""The longest preset name, in characters."""

_SUFFIX = ".json"
_PROVENANCE_KEYS = ("source", "settings")
_FORBIDDEN_CHARACTERS = frozenset('<>:"/\\|?*')
_RESERVED_DEVICE_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}
    | {f"{device}{digit}" for device in ("COM", "LPT") for digit in "0123456789¹²³"}
)


class PresetError(Exception):
    """A preset operation was refused: a bad name, a name clash, or a missing or bad file."""


class PresetImportError(PresetError):
    """A preset file cannot be imported.

    Attributes:
        problems: Every disagreement with the method schema (empty when the file could not be
            read or parsed at all; the message then says why).
    """

    def __init__(self, message: str, problems: Sequence[ParameterProblem] = ()) -> None:
        """Create the error.

        Args:
            message: A user-readable summary.
            problems: The schema problems found.
        """
        super().__init__(message)
        self.problems = tuple(problems)


@dataclass(frozen=True)
class PresetEntry:
    """One file in the preset folder, as listed.

    Attributes:
        name: The preset name (the file stem).
        path: The file.
        parameter_set: The parsed preset, or None when the file is unreadable.
        error: Why the file is unreadable, or None. An unreadable file is left untouched.
    """

    name: str
    path: Path
    parameter_set: ParameterSet | None
    error: str | None


@dataclass(frozen=True)
class PresetImportResult:
    """The outcome of a successful import.

    Attributes:
        name: The name the preset was stored under (may carry a " (2)" style suffix).
        path: The stored file.
        parameter_set: The imported set, without provenance.
        provenance_dropped: True when the source file carried ``source`` or ``settings`` keys
            (a provenance sidecar) and they were not kept.
    """

    name: str
    path: Path
    parameter_set: ParameterSet
    provenance_dropped: bool


def validate_preset_name(name: str) -> str:
    r"""Check that a preset name is a safe file name on every operating system (N1).

    The rule is the same everywhere: 1 to 100 characters; no leading or trailing whitespace; no
    ``< > : " / \\ | ? *`` and no control characters; no trailing dot; not ``.`` or ``..``; not
    a Windows reserved device name (``CON``, ``PRN``, ``AUX``, ``NUL``, ``COM0``-``COM9``,
    ``LPT0``-``LPT9``, case-insensitive, also with an extension); encodable as UTF-8.

    Args:
        name: The proposed name.

    Returns:
        ``name`` unchanged.

    Raises:
        PresetError: The name breaks the rule; the message says which part.
    """
    if not name:
        raise PresetError("a preset name cannot be empty")
    if len(name) > MAX_NAME_LENGTH:
        raise PresetError(f"preset name is {len(name)} characters; the limit is {MAX_NAME_LENGTH}")
    if name != name.strip():
        raise PresetError("a preset name cannot start or end with whitespace")
    if name.endswith("."):
        raise PresetError("a preset name cannot end with a dot")
    if name in (".", ".."):
        raise PresetError(f"{name!r} is not a usable preset name")
    for character in name:
        if character in _FORBIDDEN_CHARACTERS or ord(character) < 32 or ord(character) == 127:
            raise PresetError(f"preset name cannot contain {character!r}")
    try:
        name.encode("utf-8")
    except UnicodeEncodeError as error:
        raise PresetError("preset name is not valid text") from error
    if name.split(".", 1)[0].rstrip(" ").upper() in _RESERVED_DEVICE_NAMES:
        raise PresetError(f"{name!r} is a reserved device name on Windows")
    return name


def new_parameter_set(
    method: str,
    parameters: Mapping[str, ParameterValue],
    *,
    now: datetime | None = None,
) -> ParameterSet:
    """Build a preset's parameter set stamped with the time and this Clearwater version.

    Args:
        method: The method id.
        parameters: The parameter values (may be partial).
        now: The creation time (timezone-aware); the current UTC time when None.

    Returns:
        The set, with no provenance.
    """
    return ParameterSet(
        method=method,
        parameters=dict(parameters),
        created=datetime.now(UTC) if now is None else now,
        app_version=__version__,
    )


def starter_presets(now: datetime | None = None) -> dict[str, ParameterSet]:
    """Return the two starter presets (AD-13): both the method defaults in v1.

    Each is ``ParameterSet("c3", {})``; IF-9 allows a partial set and the method default
    applies. Explicit values wait for the owner at CP5.

    Args:
        now: The creation time; the current UTC time when None.

    Returns:
        Name -> set for "Snorkel (shallow)" and "Scuba (deep)".
    """
    return {
        STARTER_SNORKEL: new_parameter_set(STARTER_METHOD, {}, now=now),
        STARTER_SCUBA: new_parameter_set(STARTER_METHOD, {}, now=now),
    }


def _name_key(name: str) -> str:
    """Return the key under which two names count as the same file on a lenient file system."""
    return unicodedata.normalize("NFC", name).casefold()


def _read_text(path: Path) -> str:
    """Read a preset file as UTF-8, refusing one over :data:`MAX_PRESET_BYTES`."""
    size = path.stat().st_size
    if size > MAX_PRESET_BYTES:
        raise FormatError(f"preset file is {size} bytes; the cap is {MAX_PRESET_BYTES} bytes")
    return path.read_text(encoding="utf-8")


class PresetStore:
    """The presets in one folder (G6).

    The folder is created on the first write; reads never create it.
    """

    def __init__(self, folder: Path, *, migrations: MigrationRegistry | None = None) -> None:
        """Create a store over ``folder``.

        Args:
            folder: The preset folder (``Locations.presets_dir`` in the product).
            migrations: The migration steps; the product's (empty) registry when None.
        """
        self._folder = folder
        self._migrations = migrations

    @property
    def folder(self) -> Path:
        """The preset folder."""
        return self._folder

    def list_presets(self) -> list[PresetEntry]:
        """List every ``*.json`` file in the folder, sorted by name (case-insensitive).

        An unreadable file (bad JSON, newer version, wrong shape, too large) is listed with
        ``error`` set and left untouched.

        Returns:
            The entries; empty when the folder does not exist.
        """
        if not self._folder.is_dir():
            return []
        entries = []
        for path in self._folder.iterdir():
            if path.suffix != _SUFFIX or not path.is_file():
                continue
            try:
                parameter_set, _ = self._read(path)
            except (FormatError, OSError, UnicodeDecodeError) as error:
                entries.append(PresetEntry(path.stem, path, None, str(error)))
            else:
                entries.append(PresetEntry(path.stem, path, parameter_set, None))
        return sorted(entries, key=lambda entry: (_name_key(entry.name), entry.name))

    def load(self, name: str) -> ParameterSet:
        """Load a preset by name.

        Args:
            name: The preset name.

        Returns:
            The set, without provenance.

        Raises:
            PresetError: The name is not valid, or no readable preset has that name.
        """
        return self._read_preset(self._path(name))

    def save(self, name: str, parameter_set: ParameterSet, *, overwrite: bool = False) -> Path:
        """Save a parameter set as a preset.

        Provenance (``source``, ``settings``) is not stored. The write is atomic. A name that
        matches an existing preset case-insensitively is refused unless ``overwrite`` is set,
        in which case that preset's file is replaced (an unreadable file is never replaced).

        Args:
            name: The preset name.
            parameter_set: The set to store.
            overwrite: Replace an existing preset of that name (the GUI's confirmation).

        Returns:
            The file written.

        Raises:
            PresetError: The name is not valid, or it exists and ``overwrite`` is false, or the
                existing file is not a readable preset.
            FormatError: A mapping key is not a string (DR-32) or a number is not finite.
            ValueError: ``created`` is not timezone-aware.
        """
        path = self._path(name)
        check_parameter_set_keys(parameter_set, "preset")
        existing = self._find(name)
        if existing is not None:
            if not overwrite:
                raise PresetError(f"a preset named {existing.stem!r} already exists")
            self._read_preset(existing)
            path = existing
        self._write(path, parameter_set)
        return path

    def rename(self, old: str, new: str) -> Path:
        """Rename a preset; its content is untouched.

        Args:
            old: The current name; it must be a readable preset.
            new: The new name; no other preset may match it case-insensitively.

        Returns:
            The new file.

        Raises:
            PresetError: A name is not valid, ``old`` is not a readable preset, or ``new`` is
                taken.
        """
        source = self._path(old)
        target = self._path(new)
        self._read_preset(source)
        for other in self._matches(new):
            if other.name != source.name:
                raise PresetError(f"a preset named {other.stem!r} already exists")
        if source.name != target.name:  # Windows paths compare case-insensitively
            os.rename(source, target)
        return target

    def delete(self, name: str) -> None:
        """Delete a preset.

        Args:
            name: The preset name; it must be a readable preset file.

        Raises:
            PresetError: The name is not valid or no readable preset has that name.
        """
        path = self._path(name)
        self._read_preset(path)
        path.unlink()

    def import_preset(
        self,
        source: Path,
        schemas: Mapping[str, Sequence[Parameter]],
        *,
        name: str | None = None,
    ) -> PresetImportResult:
        """Import a preset file into the store after validating it.

        The file is read (at most 1 MiB), migrated, key-checked, parsed and validated against
        the schema for its method. Every schema problem is reported together. Provenance keys
        are dropped and the result says so. A name that is taken becomes "name (2)", "name (3)"
        and so on.

        Args:
            source: The file to import.
            schemas: Method id -> that method's parameters (``CorrectionMethod.parameters``).
            name: The name to store under; the file's stem when None.

        Returns:
            The stored preset.

        Raises:
            PresetImportError: The file cannot be read or parsed, its method is not in
                ``schemas``, or it disagrees with the schema (``problems`` lists each).
            PresetError: The chosen name (or the file's stem) is not a valid preset name.
        """
        try:
            parameter_set, dropped = self._read(source)
        except (FormatError, OSError, UnicodeDecodeError) as error:
            raise PresetImportError(f"cannot import {source.name}: {error}") from error
        schema = schemas.get(parameter_set.method)
        if schema is None:
            known = ", ".join(sorted(schemas)) or "none"
            problem = ParameterProblem(
                "method_mismatch",
                None,
                f"unknown method {parameter_set.method!r} (known: {known})",
            )
            raise PresetImportError(problem.message, [problem])
        problems = validate_parameter_set(parameter_set, parameter_set.method, schema)
        if problems:
            raise PresetImportError(
                f"{source.name} does not match method {parameter_set.method!r}: "
                + "; ".join(problem.message for problem in problems),
                problems,
            )
        base = validate_preset_name(source.stem if name is None else name)
        chosen = base
        counter = 1
        while self._find(chosen) is not None:
            counter += 1
            chosen = validate_preset_name(f"{base} ({counter})")
        path = self._path(chosen)
        self._write(path, parameter_set)
        return PresetImportResult(chosen, path, parameter_set, dropped)

    def export_preset(self, name: str, destination: Path, *, overwrite: bool = False) -> Path:
        """Write a preset to a file the user chose, in the AD-13 form.

        Args:
            name: The preset name.
            destination: The file to write.
            overwrite: Replace an existing file (the GUI's confirmation).

        Returns:
            ``destination``.

        Raises:
            PresetError: The name is not a readable preset, or ``destination`` exists and
                ``overwrite`` is false, or it is a folder.
            FormatError: A mapping key is not a string (DR-32).
            OSError: The file cannot be written.
        """
        parameter_set = self.load(name)
        check_parameter_set_keys(parameter_set, "preset")
        if destination.is_dir():
            raise PresetError(f"{destination} is a folder")
        if destination.exists() and not overwrite:
            raise PresetError(f"{destination} already exists")
        atomic_write_text(destination, parameter_set.to_json() + "\n")
        return destination

    def install_starters(self, *, now: datetime | None = None) -> list[str]:
        """Install the starter presets on first run, once.

        Writes each starter that is not already a file, then records the marker
        ``.starters-installed`` last. With the marker present nothing happens, so a starter the
        user deleted is not brought back. Starters rename and delete like any preset.

        Args:
            now: The creation time stamped on the starters; the current UTC time when None.

        Returns:
            The names written this call (empty when already installed).
        """
        marker = self._folder / STARTERS_MARKER_NAME
        if marker.exists():
            return []
        installed = []
        for name, parameter_set in starter_presets(now).items():
            if self._find(name) is None:
                self._write(self._path(name), parameter_set)
                installed.append(name)
        atomic_write_text(marker, "1\n")
        return installed

    def _path(self, name: str) -> Path:
        """Return the file for a valid name; the name cannot leave the folder."""
        return self._folder / f"{validate_preset_name(name)}{_SUFFIX}"

    def _matches(self, name: str) -> list[Path]:
        """Return the preset files whose name matches ``name`` case-insensitively."""
        if not self._folder.is_dir():
            return []
        key = _name_key(name)
        return [
            path
            for path in self._folder.iterdir()
            if path.suffix == _SUFFIX and _name_key(path.stem) == key
        ]

    def _find(self, name: str) -> Path | None:
        """Return the existing file matching ``name`` case-insensitively, or None."""
        found = self._matches(name)
        return found[0] if found else None

    def _write(self, path: Path, parameter_set: ParameterSet) -> None:
        """Write a preset file without provenance."""
        clean = dataclasses.replace(parameter_set, source=None, settings=None)
        atomic_write_text(path, clean.to_json() + "\n")

    def _read(self, path: Path) -> tuple[ParameterSet, bool]:
        """Read, migrate and parse a preset file; return it and whether provenance was dropped."""
        data: dict[str, Any] = loads_object(_read_text(path))
        version = data.get("format_version")
        if isinstance(version, bool) or not isinstance(version, int):
            raise FormatError(f"format_version {version!r} is missing or not an integer")
        data = migrate("preset", data, self._migrations)
        check_string_keys(data, "preset")
        dropped = any(key in data for key in _PROVENANCE_KEYS)
        kept = {key: value for key, value in data.items() if key not in _PROVENANCE_KEYS}
        return ParameterSet.from_dict(kept), dropped

    def _read_preset(self, path: Path) -> ParameterSet:
        """Read a stored preset, refusing a missing, linked, unreadable or non-preset file."""
        if path.is_symlink() or not path.is_file():
            raise PresetError(f"no preset named {path.stem!r}")
        try:
            return self._read(path)[0]
        except (FormatError, OSError, UnicodeDecodeError) as error:
            raise PresetError(f"{path.stem!r} is not a readable preset: {error}") from error
