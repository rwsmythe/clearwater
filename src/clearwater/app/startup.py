"""Start-up work (WP4.3): the write journal, the leftover clean-up and the start-up job bodies.

Spec D85 and 8.4: outputs are written to a temporary name and renamed on success, and the
leftovers of a crash are cleaned up on the next start. The folders scanned are the configured
output folder plus the folders of a small journal of in-flight writes (WP3.13 question 3 and
WP4.3 question 3 as ruled): each export job adds its destination folder before it can write a
temporary and removes it when it returns with that folder clean, so a crash (or a temporary that
could not be removed) leaves the entry and the next start scans that folder with WP3.13's
``remove_leftovers`` (unchanged), then clears the entries of the folders it left clean; an entry
stays until its folder's clean-up has succeeded (R1-3, ruling d530b564). A folder is never
scanned only because a source lies there. The cache folder is cleaned by the proxy cache's own
open.

Qt-free: the entry point (:mod:`clearwater.app.main`) runs these on the threads the round-0
table names; nothing here touches a Qt object.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
import uuid
from collections.abc import Callable, Iterable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from clearwater.config import atomic_write_text
from clearwater.interfaces import ArrayBackend, JobResult, Progress, Settings
from clearwater.jobs import LeftoverReport, is_temporary_name, remove_leftovers

from .composition import DeferredProxyCache

_LOG = logging.getLogger(__name__)

JOURNAL_FILE_NAME = "write-journal.json"
"""The journal's file name in ``Locations.config_dir``."""

JOURNAL_FORMAT_VERSION = 1
"""The journal's ``format_version``."""

type SelectBackend = Callable[[Settings, int, int, str], tuple[ArrayBackend, str]]
"""IF-2 ``select_backend(settings, height, width, method_id) -> (backend, reason)``."""


class WriteJournal:
    """The journal of in-flight writes: one entry per export job, its destination folder.

    The file is ``config_dir/write-journal.json``: ``{"format_version": 1, "entries": [{"id":
    "<hex>", "folder": "<absolute folder>"}]}``, written with ``config.atomic_write_text``. One
    process-local lock guards every read-modify-write (one application process per app-data
    folder, the declared envelope). A file that cannot be decoded (not UTF-8, not JSON, not a
    version-1 journal) is renamed beside itself to ``write-journal.json.bad-<UTC stamp>``,
    logged, and read as empty (ruling S6). A file that cannot be read (an ``OSError`` other than
    its absence) is never overwritten: :meth:`add` and :meth:`drop` raise with nothing written,
    so a retained entry is never lost to a doubtful read (R2-1, ruling 38a7c702), and
    :meth:`entries` logs it and reads it as empty.
    Thread-safe; the export jobs call it from their worker threads.

    Args:
        config_dir: The application's configuration folder (``Locations.config_dir``).
    """

    def __init__(self, config_dir: Path) -> None:
        """Create the journal over ``config_dir``; nothing is read until it is used."""
        self._path = config_dir / JOURNAL_FILE_NAME
        self._lock = threading.Lock()

    @property
    def path(self) -> Path:
        """The journal file."""
        return self._path

    def add(self, folder: Path) -> str:
        """Record a write about to start in ``folder``.

        Args:
            folder: The destination folder of the job's output.

        Returns:
            The entry's id, for :meth:`remove`.

        Raises:
            OSError: The journal cannot be read or written; nothing was written.
        """
        entry_id = uuid.uuid4().hex
        with self._lock:
            entries = self._read()
            entries.append({"id": entry_id, "folder": str(folder.absolute())})
            self._write(entries)
        return entry_id

    def remove(self, entry_id: str) -> None:
        """Remove one entry (the job returned: committed, failed or cancelled).

        Args:
            entry_id: What :meth:`add` returned.

        Raises:
            OSError: The journal cannot be read or written; nothing was written.
        """
        self._keep_only(lambda entry: entry["id"] != entry_id)

    def drop(self, entries: Iterable[tuple[str, Path]]) -> None:
        """Remove the entries matching these ``(id, folder)`` pairs; an absent pair is ignored.

        Matching the pair, not the id, keeps the entry of another folder that shares the id (a
        journal the program did not write: its ids are uuid4) when that folder's clean-up failed
        (R3-2, ruling d6e9abdf).

        Args:
            entries: The ``(id, folder)`` pairs to remove, as :meth:`entries` returns them.

        Raises:
            OSError: The journal cannot be read or written; nothing was written.
        """
        gone = set(entries)
        self._keep_only(lambda entry: (entry["id"], Path(entry["folder"])) not in gone)

    def _keep_only(self, keep: Callable[[dict[str, str]], bool]) -> None:
        """Rewrite the journal with the entries ``keep`` accepts; no write when none goes.

        Raises:
            OSError: The journal cannot be read or written; nothing was written.
        """
        with self._lock:
            entries = self._read()
            kept = [entry for entry in entries if keep(entry)]
            if len(kept) != len(entries):
                self._write(kept)

    def entries(self) -> tuple[tuple[str, Path], ...]:
        """Return ``(id, folder)`` of every entry, oldest first; none if the file cannot be read."""
        with self._lock:
            try:
                entries = self._read()
            except OSError as error:
                _LOG.warning("write journal %s could not be read: %s", self._path, error)
                return ()
            return tuple((entry["id"], Path(entry["folder"])) for entry in entries)

    def _read(self) -> list[dict[str, str]]:
        """Read the entries (under the lock); an undecodable file is set aside and read as empty.

        Raises:
            OSError: The file exists but cannot be read (R2-1: the caller writes nothing).
        """
        try:
            data = self._path.read_bytes()
        except FileNotFoundError:
            return []
        try:
            entries = _decode(json.loads(data.decode("utf-8")))
        except (UnicodeDecodeError, ValueError, RecursionError) as error:
            self._set_aside(str(error))
            return []
        return entries

    def _write(self, entries: Sequence[dict[str, str]]) -> None:
        """Write the entries atomically (under the lock)."""
        document = {"format_version": JOURNAL_FORMAT_VERSION, "entries": list(entries)}
        atomic_write_text(self._path, json.dumps(document, indent=2) + "\n")

    def _set_aside(self, reason: str) -> None:
        """Rename an undecodable journal beside itself (the settings file's form, ruling S6)."""
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        target = self._path.with_name(f"{self._path.name}.bad-{stamp}")
        counter = 1
        while target.exists():
            counter += 1
            target = self._path.with_name(f"{self._path.name}.bad-{stamp}-{counter}")
        try:
            self._path.rename(target)
        except OSError as error:
            _LOG.warning(
                "write journal %s is not readable (%s) and could not be set aside (%s)",
                self._path,
                reason,
                error,
            )
        else:
            _LOG.warning(
                "write journal %s is not readable (%s); moved to %s", self._path, reason, target
            )


def _decode(document: Any) -> list[dict[str, str]]:
    """Check the journal document's shape and return its entries.

    A folder the operating system refuses as a path (a NUL character, or on POSIX a string the
    file-system encoding cannot encode; ``os`` raises ``ValueError`` for both) is not a folder,
    so the file is set aside under S6 (R2-2).

    Raises:
        ValueError: Not a version-1 journal of entries with a string id and an absolute folder.
    """
    if not isinstance(document, dict) or document.get("format_version") != JOURNAL_FORMAT_VERSION:
        raise ValueError(f"not a format_version {JOURNAL_FORMAT_VERSION} write journal")
    entries = document.get("entries")
    if not isinstance(entries, list):
        raise ValueError("the journal has no entry list")
    decoded: list[dict[str, str]] = []
    for entry in entries:
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("id"), str)
            or not isinstance(entry.get("folder"), str)
            or not _is_path(entry["folder"])
            or not Path(entry["folder"]).is_absolute()
        ):
            raise ValueError("a journal entry is not an id and an absolute folder")
        decoded.append({"id": entry["id"], "folder": entry["folder"]})
    return decoded


def _is_path(text: str) -> bool:
    """Return True when the operating system accepts ``text`` as a path (R2-2)."""
    if "\x00" in text:
        return False
    try:
        os.fsencode(text)
    except UnicodeEncodeError:
        return False
    return True


def leftover_folders(settings: Settings, journal_folders: Iterable[Path]) -> tuple[Path, ...]:
    """Return the folders the start-up clean-up scans (question 3 as ruled), each once.

    Args:
        settings: The settings of the one settings read (``output_folder``).
        journal_folders: The folders of the journal's entries.

    Returns:
        ``Settings.output_folder`` (when set) and then every journal folder, in that order.
    """
    folders: list[Path] = []
    candidates = [] if settings.output_folder is None else [settings.output_folder]
    for folder in [*candidates, *journal_folders]:
        if folder not in folders:
            folders.append(folder)
    return tuple(folders)


def holds_leftovers(folder: Path) -> bool:
    """Return True unless ``folder`` is known to hold no temporary output file (D85).

    A folder that does not exist holds none. A folder that cannot be listed (an ``OSError``, or
    a ``ValueError`` for a path the operating system refuses, R2-2) may hold one, so it counts as
    holding one: its journal entry stays (R1-3, ruling d530b564).

    Args:
        folder: A journal entry's folder.

    Returns:
        True when the folder holds a regular file named like a temporary output, or cannot be
        listed; False when it is listed and holds none, or does not exist.
    """
    try:
        with os.scandir(folder) as entries:
            return any(
                is_temporary_name(entry.name) and entry.is_file(follow_symlinks=False)
                for entry in entries
            )
    except FileNotFoundError:
        return False
    except (OSError, ValueError):
        return True


def clean_leftovers(settings: Settings, journal: WriteJournal) -> LeftoverReport:
    """Remove the leftover temporaries of a crash, then clear the entries of the cleaned folders.

    Runs before any export or batch job can start (DR-35 (c)): the entry point calls it on the
    interface thread before it attaches the panels. Every removed file and every failure is
    logged (N9). An entry whose folder still holds a temporary afterwards (a removal failed, or
    the folder cannot be listed) stays and is scanned again at the next start (R1-3, ruling
    d530b564). An output folder that cannot be listed is logged (``holds_leftovers``' rule; a
    missing one holds nothing to log; B-7). A journal that cannot be read or written is logged
    and left as it is; its entries stay and are scanned again at the next start (R2-1, ruling
    38a7c702). A folder the operating system refuses as a path (a NUL character in
    ``output_folder``, say) is skipped and logged, so nothing here raises before the window shows
    (R3-1, ruling d6e9abdf); a journal entry with such a folder keeps its entry
    (``holds_leftovers``). An entry is cleared by its ``(id, folder)`` pair (R3-2).

    Args:
        settings: The settings of the one settings read.
        journal: The write journal.

    Returns:
        What ``remove_leftovers`` removed and could not remove.
    """
    entries = journal.entries()
    folders: list[Path] = []
    for folder in leftover_folders(settings, [folder for _, folder in entries]):
        if _is_path(str(folder)):
            folders.append(folder)
        else:
            _LOG.warning(
                "the leftover clean-up skips %r: the operating system refuses it as a folder",
                str(folder),
            )
    report = remove_leftovers(folders)
    for path in report.removed:
        _LOG.info("removed a leftover temporary file: %s", path)
    for path, error in report.failed:
        _LOG.warning("a leftover temporary file could not be removed: %s: %s", path, error)
    if settings.output_folder is not None and settings.output_folder in folders:
        try:
            with os.scandir(settings.output_folder):
                pass
        except FileNotFoundError:
            pass
        except (OSError, ValueError) as error:
            _LOG.warning(
                "the leftover clean-up could not list the output folder %s: %s",
                settings.output_folder,
                error,
            )
    unclean = {folder for folder in {folder for _, folder in entries} if holds_leftovers(folder)}
    for folder in sorted(unclean):
        _LOG.warning("the write journal keeps %s until its clean-up succeeds", folder)
    try:
        journal.drop((entry_id, folder) for entry_id, folder in entries if folder not in unclean)
    except OSError as error:
        _LOG.warning("the write journal could not be cleared: %s", error)
    return report


def cache_open_job(cache: DeferredProxyCache, limit_bytes: int) -> Callable[[Progress], JobResult]:
    """Return start-up job (i): open the application's one cache with the settings' limit.

    Args:
        cache: The application's cache handle.
        limit_bytes: ``Settings.cache_limit_bytes`` of the one settings read.

    Returns:
        A job whose result is ok, or failed with the open's reason (every cache member then
        refuses with it).
    """

    def job(progress: Progress) -> JobResult:
        started = time.perf_counter()
        failure = cache.open(limit_bytes)
        if failure is not None:
            _LOG.warning("the analysis cache could not be opened: %s", failure)
        return JobResult(failure is None, (), (), failure, "cpu", time.perf_counter() - started)

    return job


def device_probe_job(
    select_backend: SelectBackend, settings: Settings, method_id: str
) -> Callable[[Progress], JobResult]:
    """Return start-up job (iii): the graphics-card detection (AD-9, question 5 as ruled).

    The first selection imports CuPy, finds the device and runs its test kernel (about a second
    on the owner's laptop), so it runs off the interface thread. The reason is the result's
    ``device`` and is logged.

    Args:
        select_backend: The IF-2 selection (``engines.select_backend``).
        settings: The current settings (``force_cpu``).
        method_id: The default method's id (the estimate's method).

    Returns:
        A job whose result's ``device`` is the selection's AD-9 reason.
    """

    def job(progress: Progress) -> JobResult:
        started = time.perf_counter()
        _, reason = select_backend(settings, 1, 1, method_id)
        _LOG.info("device: %s", reason)
        return JobResult(True, (), (), None, reason, time.perf_counter() - started)

    return job
