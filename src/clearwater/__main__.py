"""``python -m clearwater`` and the packaged executable: start the GUI or the export worker.

The branches of this entry (WP6.1, AD-34):

- Frozen only, a MULTIPROCESSING re-entry (:func:`multiprocessing_reentry`: any argument in
  :data:`MULTIPROCESSING_FLAGS`) is refused first, before every other branch: one stderr line,
  status 2, no GUI (CHARC's ruling on Reviewer A r3 #3; ``freeze_support()`` is declined).
- Frozen only, ``<exe> --export-worker [args]`` runs :func:`clearwater.app.export_worker.main`
  with the remaining arguments. A packaged build spawns its video export worker this way,
  because its executable cannot run ``-m clearwater.app.export_worker``. This branch imports
  no Qt-bearing module (AD-31). It first moves the request pipe off the standard-input slot
  (:func:`isolate_worker_stdin`, CHARC's F-E ruling; TEMPORARY, see there). A source run
  sends ``--export-worker`` to the GUI, as 1.0.0 did (Reviewer A r3 #1); the source worker is
  ``python -m clearwater.app.export_worker``.
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

FLAG_LETTERS = frozenset("bBdEiIOPqsSuvx")
"""CPython 3.12's option letters that take no value (``python -h``); they may be clustered
(``-OO``, ``-Es``, ``-IIs``). ``-h``, ``-V`` and ``-?`` are not among them: a cluster holding one
is not a re-entry (it goes to the GUI)."""

VALUE_LETTERS = frozenset("WX")
"""CPython's option letters that take a value: the rest of the cluster (``-Xutf8``,
``-Wignore``) or, when nothing is attached, the next argument (``-X utf8``)."""

REENTRY_LETTERS = frozenset("mc")
"""The letters that end CPython's options: ``-m <module>`` and ``-c <code>``, the operand
attached (``-mfoo``, ``-cCODE``) or the next argument."""

MULTIPROCESSING_FLAGS = ("--multiprocessing-fork", "--multiprocessing-resource-tracker")
"""Arguments with which ``multiprocessing`` re-enters a frozen ``sys.executable`` for a child.

``--multiprocessing-fork`` is the one the bundled 3.12 standard library names
(``multiprocessing/spawn.py``'s ``get_command_line``, frozen form; a read of both bundles' frozen
code found no other ``--multiprocessing-`` string). ``--multiprocessing-resource-tracker`` is
refused too by CHARC's ruling on Reviewer A r3 #3.
"""

MULTIPROCESSING_REFUSAL = "multiprocessing children are not supported"
"""The one stderr line (after ``Clearwater: ``) of a refused multiprocessing re-entry."""

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
    first_plain = bool(entries) and not entries[0].startswith('"')  # which() cannot use quotes
    if len(others) == len(entries) - 1 and first_plain and _path_key(entries[0]) == wanted:
        return False
    env["PATH"] = os.pathsep.join([folder, *others])
    return True


def _path_key(entry: str) -> str:
    """Return a ``PATH`` entry in the form two entries naming one folder share.

    Surrounding double quotes (a quoted folder, as Windows allows in ``PATH``) are dropped first,
    so a quoted spelling of the executable's folder counts as the folder (Reviewer A r3 #6).
    """
    if len(entry) >= 2 and entry[0] == entry[-1] == '"':
        entry = entry[1:-1]
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

    CPython's option grammar (Reviewer A r3 #2 as CHARC ruled it): zero or more option
    arguments, each a cluster of :data:`FLAG_LETTERS` that may end with a
    :data:`VALUE_LETTERS` letter (its value attached, or the next argument), then the
    ``-m`` / ``-c`` letter (:data:`REENTRY_LETTERS`, possibly at the end of a cluster, its
    operand attached or the next argument). The options are dropped (the bootloader configures
    the frozen interpreter); an attached operand is split off. Anything else (``-I`` alone,
    ``-X`` without a value, ``-h``, ``--version``, ``-``, ``--``, ``-platform offscreen``, a
    file) is not a re-entry and goes to the GUI exactly as before.

    Args:
        arguments: The full command line, program name first.

    Returns:
        ``["-m" | "-c", <operand, when attached>, *the rest]``, or None.
    """
    index = 1
    while index < len(arguments):
        token = arguments[index]
        if len(token) < 2 or token[0] != "-" or token[1] == "-":
            return None
        index += 1
        for position in range(1, len(token)):
            letter = token[position]
            if letter in FLAG_LETTERS:
                continue
            rest = token[position + 1 :]
            if letter in REENTRY_LETTERS:
                return ["-" + letter, *([rest] if rest else []), *arguments[index:]]
            if letter in VALUE_LETTERS:
                if not rest:
                    if index >= len(arguments):
                        return None  # a value option with no value
                    index += 1  # its value is the next argument
                break
            return None  # not an interpreter option letter
    return None


def multiprocessing_reentry(arguments: Sequence[str]) -> bool:
    """Return whether a command line is ``multiprocessing`` re-entering the executable.

    Any argument after the program name that is one of :data:`MULTIPROCESSING_FLAGS` counts,
    wherever it stands, so no argument order routes around the refusal.

    Args:
        arguments: The full command line, program name first.

    Returns:
        True for a multiprocessing child's command line.
    """
    return any(argument in MULTIPROCESSING_FLAGS for argument in arguments[1:])


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
    if getattr(sys, "frozen", False):
        if multiprocessing_reentry(arguments):  # before every other dispatch (A r3 #3)
            return _refuse(MULTIPROCESSING_REFUSAL)
        if arguments[1:2] == [WORKER_FLAG]:  # frozen only: a source run is 1.0.0 (A r3 #1)
            # F-E: before the worker's first read and before anything that can spawn a child
            # (the loader, the worker import, its backend probe, any CuPy import).
            isolate_worker_stdin()
            gpu_pack.activate()
            from clearwater.app import export_worker

            return export_worker.main(arguments[2:])
        reentry = interpreter_reentry(arguments)
        if reentry is not None:
            return run_interpreter_option([arguments[0], *reentry])
        _start_logging()
    gpu_pack.activate()
    from clearwater.app.main import main as gui_main

    return gui_main(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
