"""``python -m clearwater`` and the packaged executable: start the GUI or the export worker.

The branches of this entry (WP6.1, AD-34):

- ``<entry> --export-worker [args]`` runs :func:`clearwater.app.export_worker.main` with the
  remaining arguments. A packaged (frozen) build spawns its video export worker this way,
  because its executable cannot run ``-m clearwater.app.export_worker``. This branch imports
  no Qt-bearing module (AD-31). Frozen only, it first moves the request pipe off the
  standard-input slot (:func:`isolate_worker_stdin`, CHARC's F-E ruling; TEMPORARY, see there).
- Frozen only, an INTERPRETER RE-ENTRY (:func:`interpreter_reentry`: ``-m`` / ``-c`` in any
  form CPython accepts, after interpreter flags; :func:`run_interpreter_option`): a library
  inside the GPU pack re-enters ``sys.executable -m <its module>`` (``cuda.pathfinder``'s
  canary probe), which a frozen build would otherwise send to the GUI. ``-m <module> [args]``
  runs the module when its top-level package resolves from the loaded pack, and is refused
  otherwise; ``-c`` is always refused. A refusal is one line on stderr and a non-zero exit,
  never a window: the executable is not a general Python interpreter (CHARC's F-D ruling and
  its widening at gen 15). This branch imports no Qt-bearing module either. A source run has
  no such branch.
- Anything else starts the GUI (:func:`clearwater.app.main.main`, WP4.3).

On every branch the GPU pack loader (:func:`clearwater.gpu_pack.activate`) runs before
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
import io
import os
import re
import sys
from collections.abc import MutableMapping, Sequence

from clearwater import gpu_pack

WORKER_FLAG = "--export-worker"
"""The first argument that selects the export worker branch."""

MODULE_OPTION = "-m"
"""The interpreter option a pack library re-enters the frozen executable with."""

COMMAND_OPTION = "-c"
"""The interpreter option a frozen build always refuses."""

REFUSED_STATUS = 2
"""The exit status of a refused ``-m`` / ``-c`` in a frozen build."""

REENTRY_ARGUMENT = re.compile(r"-([BdEhiIOPqsSuvVWxX]*)([mc])(.*)", re.DOTALL)
"""CPython's grammar for an argument that ends its options with ``-m`` or ``-c``.

Flag letters, then ``m`` or ``c``, then the attached operand (``-mfoo``, ``-Im``, ``-cCODE``).
Qt's word options (``-platform``, ``-style``, ``-reverse``, ``-widgetcount``) do not match;
``-qmljsdebugger=...`` does (``-q`` then ``-m``) and is refused: Clearwater has no QML.
"""

LEADING_FLAGS = frozenset({"-I", "-E", "-s", "-S", "-B", "-u", "-O", "-q"})
"""Interpreter flags that may come, alone, before a re-entry's ``-m`` / ``-c`` (dropped)."""

VALUED_FLAGS = frozenset({"-X", "-W"})
"""Interpreter flags that take the next argument as their value (both dropped)."""

STD_INPUT_HANDLE = -10
"""Win32's ``STD_INPUT_HANDLE`` (``(DWORD)-10``), the slot ``SetStdHandle`` re-points."""


def isolate_worker_stdin() -> bool:
    """Frozen worker only: read the request pipe privately; children inherit NUL (F-E).

    The export worker's cancel thread blocks reading its standard input (the request pipe)
    for the whole job. A child spawned with ``stdin=None`` inherits that pipe, and on Windows
    a Python child (``cuda.pathfinder``'s canary probe, ``sys.executable -m ...``) then hangs
    in its own start-up while the parent's read is pending (WP6.1 finding F-E). So the pipe is
    duplicated to a private descriptor (not inheritable, PEP 446) that becomes ``sys.stdin``,
    and descriptor 0 is pointed at the null device. On Windows the process's Win32
    standard-input handle is pointed there too with ``SetStdHandle``, because the windowed
    executable is a GUI-subsystem process whose C runtime does not update it on ``dup2``, and
    ``subprocess`` gives a child that handle (CHARC's ruling; the one N1 site, AD-34).

    Must run before the worker's first read and before anything that can spawn a child (the
    GPU pack loader, the worker import, its backend probe, any CuPy import). A source run is
    unchanged (1.0.0): nothing is duplicated and nothing re-pointed.

    TEMPORARY: DR-125's package moves this isolation into the worker itself, for source and
    frozen runs alike, and then removes this function from ``__main__``.

    Returns:
        True when the standard input was moved; False when not frozen, or when the process
        has no standard input to move.

    Raises:
        OSError: ``SetStdHandle`` failed (the Win32 slot would name a closed handle).
    """
    if not getattr(sys, "frozen", False):
        return False
    try:
        private = os.dup(0)  # PEP 446: the duplicate is not inheritable
    except OSError:
        return False  # no standard input at all: nothing a child could inherit
    null = os.open(os.devnull, os.O_RDONLY)
    try:
        if sys.platform == "win32":
            import ctypes
            import msvcrt

            os.dup2(null, 0)
            done = ctypes.windll.kernel32.SetStdHandle(
                ctypes.c_ulong(STD_INPUT_HANDLE & 0xFFFFFFFF),
                ctypes.c_void_p(msvcrt.get_osfhandle(0)),
            )
            if not done:
                raise ctypes.WinError()
        else:
            os.dup2(null, 0)
    finally:
        os.close(null)
    encoding = getattr(sys.stdin, "encoding", None) or "utf-8"
    sys.stdin = io.TextIOWrapper(open(private, "rb"), encoding=encoding)  # noqa: SIM115
    return True


def prepend_executable_folder(environ: MutableMapping[str, str] | None = None) -> bool:
    """In a frozen build, make the executable's folder the first ``PATH`` entry, once (D1).

    Tools are found with ``shutil.which`` (``PATH``), so a bundled ``ffmpeg`` beside the
    executable is found before any other. Every entry naming that folder (in any spelling:
    case, separators, a trailing separator) is removed and the folder is put first; the other
    entries keep their order (CHARC's ruling 4 on Reviewer A r2 #10: a ``PATH`` that already
    lists the folder BEHIND another FFmpeg folder must not let that FFmpeg win). Only this
    process's environment changes (``os.environ``, which the spawned export worker and its
    FFmpeg inherit); the user's persistent ``PATH`` is never written. Nothing changes in a
    source run, or when the folder is already the first entry and appears once. A spawned
    worker inherits its parent's ``PATH`` after PyInstaller's PySide6 run-time hook has put
    the bundle folders in front of it, so the worker moves the folder back to the front
    without adding it a second time.

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
    entries = current.split(os.pathsep) if current else []
    others = [entry for entry in entries if not entry or _path_key(entry) != wanted]
    if len(others) == len(entries) - 1 and entries and _path_key(entries[0]) == wanted:
        return False
    env["PATH"] = os.pathsep.join([folder, *others])
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


def _refuse(reason: str) -> int:
    """Write one line to stderr (when the process has one) and return the refusal status."""
    if sys.stderr is not None:  # a windowed frozen build started without pipes has none
        print(f"Clearwater: {reason}", file=sys.stderr)
    return REFUSED_STATUS


def interpreter_reentry(arguments: Sequence[str]) -> list[str] | None:
    """Return a frozen interpreter re-entry's arguments normalised, or None when it is not one.

    It is a re-entry when, after any :data:`LEADING_FLAGS` and :data:`VALUED_FLAGS` (with
    their values), the next argument matches :data:`REENTRY_ARGUMENT`. The flags are dropped
    (the bootloader configures the frozen interpreter); an attached operand is split off. Any
    other command line (``-I`` alone, ``-platform offscreen``, a file) is not a re-entry and
    goes to the GUI exactly as before.

    Args:
        arguments: The full command line, program name first.

    Returns:
        ``["-m" | "-c", <operand, when given>, *the rest]``, or None.
    """
    index = 1
    while index < len(arguments):
        if arguments[index] in LEADING_FLAGS:
            index += 1
        elif arguments[index] in VALUED_FLAGS and index + 1 < len(arguments):
            index += 2
        else:
            break
    if index >= len(arguments):
        return None
    match = REENTRY_ARGUMENT.fullmatch(arguments[index])
    if match is None:
        return None
    attached = match.group(3)
    return ["-" + match.group(2), *([attached] if attached else []), *arguments[index + 1 :]]


def run_interpreter_option(arguments: Sequence[str]) -> int:
    """Frozen ``<exe> -m <module> [args]`` / ``<exe> -c ...``: run a pack module, or refuse.

    ``-c`` is refused at once. For ``-m`` the GPU pack loader runs first; the module then runs
    (``runpy.run_module(module, run_name="__main__", alter_sys=True)``, with ``sys.argv`` =
    ``[<module's file>, *args]`` as CPython's ``-m`` gives it) only when the pack is loaded and
    the module's top-level package resolves from it (:func:`clearwater.gpu_pack.module_from_pack`).
    A missing module name, an absent or rejected pack, or any other module is refused. An
    exception escaping the module is printed to stderr and gives status 1 (as CPython does),
    so a windowed build shows no traceback dialog; ``SystemExit`` passes through.

    Args:
        arguments: The program name, then a re-entry as :func:`interpreter_reentry`
            normalises it: ``arguments[1]`` is ``-m`` or ``-c``.

    Returns:
        The exit status: the module's (0 when it returns), 1 on an exception, or
        :data:`REFUSED_STATUS`.
    """
    if arguments[1] == COMMAND_OPTION:
        return _refuse("-c is not supported")
    if len(arguments) < 3 or not arguments[2]:
        return _refuse("-m needs a module name")
    module = arguments[2]
    status = gpu_pack.activate()
    site = None if status is None or status.outcome != "loaded" else status.site_packages
    if site is None:
        return _refuse(f"-m {module!a}: no GPU pack is loaded")
    if not gpu_pack.module_from_pack(module, site):
        return _refuse(f"-m {module!a}: not a GPU pack module")
    import runpy
    import traceback

    sys.argv[:] = [arguments[0], *arguments[3:]]
    try:
        runpy.run_module(module, run_name="__main__", alter_sys=True)
    except SystemExit:
        raise
    except BaseException:
        if sys.stderr is not None:
            traceback.print_exc()
        return 1
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the export worker, a pack module (frozen re-entry) or the GUI, as arguments select.

    Args:
        argv: The full command line, program name first; ``sys.argv`` when None.

    Returns:
        The exit status of the branch run.
    """
    arguments = list(sys.argv if argv is None else argv)
    prepend_executable_folder()
    if arguments[1:2] == [WORKER_FLAG]:
        # F-E: before the worker's first read and before anything that can spawn a child
        # (the loader, the worker import, its backend probe, any CuPy import).
        isolate_worker_stdin()
        gpu_pack.activate()
        from clearwater.app import export_worker

        return export_worker.main(arguments[2:])
    if getattr(sys, "frozen", False):
        reentry = interpreter_reentry(arguments)
        if reentry is not None:
            return run_interpreter_option([arguments[0], *reentry])
        _start_logging()
    gpu_pack.activate()
    from clearwater.app.main import main as gui_main

    return gui_main(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
