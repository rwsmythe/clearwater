"""``python -m clearwater`` and the packaged executable: start the GUI or the export worker.

Two branches share this entry (WP6.1, AD-34):

- ``<entry> --export-worker [args]`` runs :func:`clearwater.app.export_worker.main` with the
  remaining arguments. A packaged (frozen) build spawns its video export worker this way,
  because its executable cannot run ``-m clearwater.app.export_worker``. This branch imports
  no Qt-bearing module (AD-31).
- Anything else starts the GUI (:func:`clearwater.app.main.main`, WP4.3).

On both branches the GPU pack loader (:func:`clearwater.gpu_pack.activate`) runs before
anything can import CuPy. In a frozen build the executable's own folder is first put at the
front of ``PATH``, so FFmpeg shipped beside the executable is found before any other, and the
GUI branch opens the log file before the loader logs its line. A source run
(``python -m clearwater``) does neither, exactly as 1.0.0: the loader is a no-op there and the
shell configures logging itself.

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
    executable is found first. Nothing changes in a source run, or when the folder is already
    ANY entry of ``PATH`` (Reviewer A r2 #10): a spawned worker inherits its parent's
    ``PATH``, and before the entry runs PyInstaller's PySide6 run-time hook puts the bundle
    folder, and PySide6's own start-up its package folder, in front of it, so a first-entry
    test would add it a second time.

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
    wanted = _path_key(folder)
    if any(_path_key(entry) == wanted for entry in current.split(os.pathsep) if entry):
        return False
    env["PATH"] = folder + os.pathsep + current if current else folder
    return True


def _path_key(entry: str) -> str:
    """Return a ``PATH`` entry in the form two entries naming one folder share."""
    return os.path.normcase(os.path.normpath(entry))


def _start_logging() -> None:
    """In a frozen build, open the log file before the loader logs its line (D3).

    Called on the frozen GUI branch only (Reviewer A r2 #6): a source run creates no log
    folder before Qt starts, as in 1.0.0.

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
    if getattr(sys, "frozen", False):
        _start_logging()
    gpu_pack.activate()
    from clearwater.app.main import main as gui_main

    return gui_main(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
