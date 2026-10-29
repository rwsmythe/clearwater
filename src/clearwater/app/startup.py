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
    logged, and read as empty (ruling S6); a file that cannot be read is logged and read as
    empty.
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
            OSError: The journal cannot be written.
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
            OSError: The journal cannot be written.
        """
        self.drop((entry_id,))

    def drop(self, entry_ids: Iterable[str]) -> None:
        """Remove the entries with these ids; an unknown id is ignored.

        Args:
            entry_ids: The ids to remove.

        Raises:
            OSError: The journal cannot be written.
        """
        gone = set(entry_ids)
        with self._lock:
            entries = self._read()
            kept = [entry for entry in entries if entry["id"] not in gone]
            if len(kept) != len(entries):
                self._write(kept)

    def entries(self) -> tuple[tuple[str, Path], ...]:
        """Return ``(id, folder)`` of every entry, oldest first."""
        with self._lock:
            return tuple((entry["id"], Path(entry["folder"])) for entry in self._read())

    def _read(self) -> list[dict[str, str]]:
        """Read the entries (under the lock); an unreadable file is set aside and read as empty."""
        try:
            data = self._path.read_bytes()
        except FileNotFoundError:
            return []
        except OSError as error:
            _LOG.warning("write journal %s could not be read: %s", self._path, error)
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
            or not Path(entry["folder"]).is_absolute()
        ):
            raise ValueError("a journal entry is not an id and an absolute folder")
        decoded.append({"id": entry["id"], "folder": entry["folder"]})
    return decoded


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

    A folder that does not exist holds none. A folder that cannot be listed may hold one, so it
    counts as holding one: its journal entry stays (R1-3, ruling d530b564).

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
    except OSError:
        return True


def clean_leftovers(settings: Settings, journal: WriteJournal) -> LeftoverReport:
    """Remove the leftover temporaries of a crash, then clear the entries of the cleaned folders.

    Runs before any export or batch job can start (DR-35 (c)): the entry point calls it on the
    interface thread before it attaches the panels. Every removed file and every failure is
    logged (N9). An entry whose folder still holds a temporary afterwards (a removal failed, or
    the folder cannot be listed) stays and is scanned again at the next start (R1-3, ruling
    d530b564). A journal that cannot be written afterwards is logged; the entries stay and are
    scanned again at the next start.

    Args:
        settings: The settings of the one settings read.
        journal: The write journal.

    Returns:
        What ``remove_leftovers`` removed and could not remove.
    """
    entries = journal.entries()
    folders = leftover_folders(settings, [folder for _, folder in entries])
    report = remove_leftovers(folders)
    for path in report.removed:
        _LOG.info("removed a leftover temporary file: %s", path)
    for path, error in report.failed:
        _LOG.warning("a leftover temporary file could not be removed: %s: %s", path, error)
    unclean = {folder for folder in {folder for _, folder in entries} if holds_leftovers(folder)}
    for folder in sorted(unclean):
        _LOG.warning("the write journal keeps %s until its clean-up succeeds", folder)
    try:
        journal.drop(entry_id for entry_id, folder in entries if folder not in unclean)
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
