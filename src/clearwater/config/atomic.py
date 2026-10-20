"""Atomic text-file writes: a crash leaves either the old file or the new one (WP3.15).

Shared by the settings save and the preset save and export, so there is one implementation.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def atomic_write_text(path: Path, text: str) -> None:
    r"""Write UTF-8 text to ``path`` through a temporary file in the same folder.

    The text goes to a temporary sibling (``<name>.<random>.tmp``), is flushed and synced, and
    is then moved over ``path`` with :func:`os.replace`. A failure before the replace leaves any
    previous ``path`` intact and removes the temporary file; a hard crash may leave the temporary
    file behind, which no store ever reads. The parent folder is created when missing.

    Args:
        path: The destination file; an existing file is replaced.
        text: The text to write; newlines are written as ``\n``.

    Raises:
        OSError: The folder cannot be created, or the temporary file cannot be written or moved.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f"{path.name}.", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
