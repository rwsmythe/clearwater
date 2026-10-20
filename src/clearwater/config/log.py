"""The rotating application log (D88, N9).

One ``RotatingFileHandler`` on the ``clearwater`` logger, so every ``clearwater.<module>``
logger writes to ``clearwater.log`` in the folder the caller passes (the log folder from
:mod:`clearwater.config.paths`). The file is UTF-8, rotates at 1 MiB and keeps 5 backups, so the
log occupies at most six files of 1 MiB. The module is named ``log`` so it does not shadow the
standard library's ``logging``.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .paths import LOG_FILE_NAME, ensure_directory

LOGGER_NAME = "clearwater"
"""The root of the application's logger hierarchy."""

DEFAULT_MAX_BYTES = 1024 * 1024
"""The size at which the log file rotates: 1 MiB."""

DEFAULT_BACKUP_COUNT = 5
"""How many rotated files are kept."""

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
"""The line format: ISO time, level, logger name, message."""


class _IsoFormatter(logging.Formatter):
    """A formatter whose time is local ISO-8601 with milliseconds and the UTC offset."""

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:  # noqa: N802
        """Return the record's creation time, for example ``2026-10-20T12:30:15.123+02:00``."""
        return (
            datetime.fromtimestamp(record.created).astimezone().isoformat(timespec="milliseconds")
        )


class _ClearwaterHandler(RotatingFileHandler):
    """The handler :func:`configure_logging` owns; its type lets a second call find it."""


def configure_logging(
    folder: Path,
    *,
    level: int = logging.INFO,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
) -> Path:
    """Attach the rotating file handler to the ``clearwater`` logger (idempotent).

    A second call for the same file only updates the level. A call for another folder replaces
    the handler, closing the old one. The folder is created when missing. The logger keeps
    ``propagate`` at its default, so a host that configures the root logger still sees records.

    Args:
        folder: The log folder.
        level: The logger level (INFO by default).
        max_bytes: The size at which the file rotates; at least 1.
        backup_count: The rotated files kept; at least 1.

    Returns:
        The log file path.

    Raises:
        ValueError: ``max_bytes`` or ``backup_count`` is below 1 (that would disable rotation
            and let the log grow without bound).
        OSError: The folder or file cannot be created.
    """
    if max_bytes < 1 or backup_count < 1:
        raise ValueError("max_bytes and backup_count must be at least 1")
    path = ensure_directory(folder) / LOG_FILE_NAME
    logger = logging.getLogger(LOGGER_NAME)
    current = [h for h in logger.handlers if isinstance(h, _ClearwaterHandler)]
    if len(current) == 1 and current[0].baseFilename == os.path.abspath(path):
        logger.setLevel(level)
        return path
    shutdown_logging()
    handler = _ClearwaterHandler(
        path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    handler.setFormatter(_IsoFormatter(LOG_FORMAT))
    logger.addHandler(handler)
    logger.setLevel(level)
    return path


def shutdown_logging() -> None:
    """Remove and close the handler :func:`configure_logging` attached, if any.

    Releases the log file (Windows cannot delete an open file); a later
    :func:`configure_logging` call attaches a fresh handler.
    """
    logger = logging.getLogger(LOGGER_NAME)
    for handler in list(logger.handlers):
        if isinstance(handler, _ClearwaterHandler):
            logger.removeHandler(handler)
            handler.close()
