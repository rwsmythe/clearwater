"""``python -m clearwater`` and the packaged executable: start the GUI or the export worker.

Two branches share this entry (WP6.1, AD-34):

- ``<entry> --export-worker [args]`` runs :func:`clearwater.app.export_worker.main` with the
  remaining arguments. A packaged (frozen) build spawns its video export worker this way,
  because its executable cannot run ``-m clearwater.app.export_worker``. This branch imports
  no Qt-bearing module (AD-31).
- Anything else starts the GUI (:func:`clearwater.app.main.main`, WP4.3).

On both branches the GPU pack loader (:func:`clearwater.gpu_pack.activate`) runs before
anything can import CuPy. In a frozen build the executable's own folder is first put at the
front of ``PATH``, so FFmpeg shipped beside the executable is found before any other.

Only the standard library and :mod:`clearwater.gpu_pack` are imported at module level; each
branch imports what it needs.
"""

from __future__ import annotations

import contextlib
import os
import sys
from collections.abc import MutableMapping, Sequence

from clearwater import gpu_pack

WORKER_FLAG = "--export-worker"
"""The first argument that selects the export worker branch."""


def prepend_executable_folder(environ: MutableMapping[str, str] | None = None) -> bool:
    """In a frozen build, put the executable's folder at the front of ``PATH`` (D1).

    Tools are found with ``shutil.which`` (``PATH``), so a bundled ``ffmpeg`` beside the
    executable is found first. Nothing changes when the folder is already the first entry
    (a spawned worker inherits its parent's ``PATH``) or in a source run.

    Args:
        environ: The environment to change; ``os.environ`` when None.

    Returns:
        True when ``PATH`` was changed.
    """
    if not getattr(sys, "frozen", False):
        return False
    env = os.environ if environ is None else environ
    folder = os.path.dirname(sys.executable)
    current = env.get("PATH", "")
    entries = current.split(os.pathsep) if current else []
    if entries and os.path.normcase(entries[0]) == os.path.normcase(folder):
        return False
    env["PATH"] = folder + os.pathsep + current if current else folder
    return True


def _start_logging() -> None:
    """Open the application's log file before the loader logs its line (D3).

    The shell's own later call for the same folder only updates the level. A failure is left
    to the shell, which reports it on its start-up line.
    """
    from clearwater.config.log import configure_logging
    from clearwater.config.paths import app_locations

    with contextlib.suppress(OSError):
        configure_logging(app_locations().log_dir)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the export worker or the GUI, as the arguments select.

    Args:
        argv: The full command line, program name first; ``sys.argv`` when None.

    Returns:
        The exit status of the branch run.
    """
    arguments = list(sys.argv if argv is None else argv)
    prepend_executable_folder()
    if arguments[1:2] == [WORKER_FLAG]:
        gpu_pack.activate()
        from clearwater.app import export_worker

        return export_worker.main(arguments[2:])
    _start_logging()
    gpu_pack.activate()
    from clearwater.app.main import main as gui_main

    return gui_main(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
