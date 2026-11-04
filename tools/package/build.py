r"""Build Clearwater with PyInstaller in the one-folder or the one-file form (WP6.1 spike).

One argument list (:func:`pyinstaller_args`) serves both forms; they differ only in
``--onedir`` / ``--onefile``. The build runs in this process through
``PyInstaller.__main__.run(args)`` (the owner's TTS160 reference shape). Outputs go under the
working folder given by ``--out`` (default ``<repo>/work/wp6.1``)::

    dist-<form>/Clearwater-<version>-<platform>-<form>/   the release folder
        onedir:  Clearwater/Clearwater.exe and Clearwater/_internal/
        onefile: Clearwater.exe
    build-<form>/                                         PyInstaller's work folder
    spec-<form>/Clearwater.spec                           the generated spec

The GPU support (CuPy, ``cuda-pathfinder`` and the NVIDIA wheels) is NEVER bundled (the
owner's D-C amendment; spec N14): it is excluded here and the build fails if any of it, or
the test suite, reaches the dist or the frozen-module archive (:func:`forbidden_entries`).

Usage::

    uv run --no-sync python tools/package/build.py --form onedir
    uv run --no-sync python tools/package/build.py --form onefile --with-ffmpeg

This is spike tooling (evidence, not product): see ``tools/package/README.md``.
"""

from __future__ import annotations

import argparse
import importlib
import os
import shutil
import sys
import time
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Literal, cast

Form = Literal["onedir", "onefile"]
"""The two PyInstaller forms the spike measures."""

FORMS: tuple[Form, ...] = ("onedir", "onefile")
"""Every supported form, in build order."""

APP_NAME = "Clearwater"
"""The executable's name (``Clearwater.exe`` on Windows)."""

REPO_ROOT = Path(__file__).resolve().parents[2]
"""The repository (or worktree) root: this file is ``<root>/tools/package/build.py``."""

ENTRY_SCRIPT = REPO_ROOT / "src" / "clearwater" / "__main__.py"
"""The frozen entry: ``python -m clearwater``'s own module, run as the script."""

DEFAULT_OUT = REPO_ROOT / "work" / "wp6.1"
"""The default output folder (gitignored ``work/``)."""

FORBIDDEN_TOP_LEVEL: tuple[str, ...] = (
    "cupy",
    "cupyx",
    "cupy_backends",
    "cuda",
    "nvidia",
    "fastrlock",
    "tests",
)
"""Top-level names that must not reach the dist or the frozen-module archive."""

FORBIDDEN_DIST_INFO_PREFIXES: tuple[str, ...] = (
    "cupy_cuda",
    "cuda_pathfinder",
    "cuda_toolkit",
    "nvidia_",
    "fastrlock",
)
"""Distribution metadata folders (``<name>-<version>.dist-info``) that must not be bundled."""

FORBIDDEN_LIBRARY_PREFIXES: tuple[str, ...] = (
    "cublas",
    "cudart",
    "cufft",
    "curand",
    "cusolver",
    "cusparse",
    "nvjitlink",
    "nvrtc",
)
"""CUDA library file-name prefixes (lower case) that must not be bundled."""

SHADOW_NAMES: tuple[str, ...] = (
    "analysis",
    "app",
    "cache",
    "color",
    "config",
    "core",
    "gui",
    "interfaces",
    "jobs",
    "methods",
)
"""``clearwater`` subpackage names that must never be frozen as TOP-LEVEL modules.

The archive holds them only as ``clearwater.<name>``. A top-level copy would mean the
analysis had ``src/clearwater`` itself on its search path; there, ``clearwater.io`` would also
shadow the standard library's ``io``.
"""

EXCLUDED_MODULES: tuple[str, ...] = (
    # The GPU pack: never in the bundle (D-C). CuPy is imported only through
    # importlib.import_module("cupy"), which the analysis cannot see. But SciPy's vendored
    # array_api_compat has function-level "import cupy" statements, which it follows.
    "cupy",
    "cupyx",
    "cupy_backends",
    "cuda",
    "nvidia",
    "fastrlock",
    # The test suite and the repository's tools.
    "tests",
    "tools",
    # The dev group (pyproject.toml [dependency-groups] dev).
    "pytest",
    "_pytest",
    "pluggy",
    "xdist",
    "execnet",
    "pytest_timeout",
    "pytestqt",
    "mypy",
    "mypyc",
    "ruff",
    "psutil",
    "cpuinfo",
    "av",
    # The comms group (the harness's mail UI).
    "fastapi",
    "starlette",
    "uvicorn",
    "jinja2",
    "httpx",
    "httpcore",
    "multipart",
    "python_multipart",
    # Development-environment packages outside the product's dependency closure (uv.lock:
    # pyyaml comes through the comms group, typing-extensions through the dev tools). numpy
    # and SciPy import them only optionally (numpy.__config__, TYPE_CHECKING blocks).
    "yaml",
    "_yaml",
    "typing_extensions",
    # Not used by the application.
    "tkinter",
)
"""Modules passed to ``--exclude-module``."""

ALLOWED_TOP_LEVEL: frozenset[str] = frozenset(
    {
        "clearwater",
        # The product's runtime dependency closure in uv.lock (pyproject.toml [project]).
        "numpy",
        "scipy",
        "PIL",
        "pillow_heif",
        "_pillow_heif",
        "tifffile",
        "PySide6",
        "shiboken6",
        # PyInstaller's own run-time helper module.
        "_pyi_rth_utils",
    }
)
"""The only non-standard-library top-level modules the frozen-module archive may hold."""

FFMPEG_TOOLS: tuple[str, ...] = ("ffmpeg", "ffprobe")
"""The FFmpeg command-line tools copied beside the executable by ``--with-ffmpeg``."""


def app_version() -> str:
    """Return ``clearwater.__version__`` read from this tree's ``src``.

    Returns:
        The version string, for example ``"1.0.0"``.
    """
    source = str(REPO_ROOT / "src")
    if source not in sys.path:
        sys.path.insert(0, source)
    module = importlib.import_module("clearwater")
    return str(module.__version__)


def platform_tag(platform: str | None = None) -> str:
    """Return the release-name platform word for a ``sys.platform`` value.

    Args:
        platform: A ``sys.platform`` value; the running one when None.

    Returns:
        ``"windows"``, ``"macos"`` or ``"linux"`` (any other value is returned unchanged).
    """
    kind = sys.platform if platform is None else platform
    return {"win32": "windows", "darwin": "macos", "linux": "linux"}.get(kind, kind)


def release_name(form: Form, version: str, platform: str | None = None) -> str:
    """Return the release folder name ``Clearwater-<version>-<platform>-<form>``.

    Args:
        form: The PyInstaller form.
        version: The application version.
        platform: A ``sys.platform`` value; the running one when None.

    Returns:
        The name, for example ``"Clearwater-1.0.0-windows-onedir"``.
    """
    return f"{APP_NAME}-{version}-{platform_tag(platform)}-{form}"


def release_dir(out: Path, form: Form, version: str) -> Path:
    """Return the folder the build writes the release into.

    Args:
        out: The output folder.
        form: The PyInstaller form.
        version: The application version.

    Returns:
        ``out/dist-<form>/<release name>``.
    """
    return out / f"dist-{form}" / release_name(form, version)


def pyinstaller_args(form: Form, *, out: Path, version: str) -> list[str]:
    """Return PyInstaller's command line for one form: the ONE spec of both forms.

    Args:
        form: ``"onedir"`` or ``"onefile"``; the only difference between the two lists.
        out: The output folder; ``dist-<form>``, ``build-<form>`` and ``spec-<form>`` go there.
        version: The application version (it names the release folder).

    Returns:
        The arguments for ``PyInstaller.__main__.run``.

    Raises:
        ValueError: ``form`` is not one of :data:`FORMS`.
    """
    if form not in FORMS:
        raise ValueError(f"unknown form {form!r}; expected one of {FORMS}")
    args = [
        str(ENTRY_SCRIPT),
        f"--{form}",
        "--name",
        APP_NAME,
        "--windowed",
        "--noconfirm",
        "--clean",
        "--paths",
        str(REPO_ROOT / "src"),
        "--distpath",
        str(release_dir(out, form, version)),
        "--workpath",
        str(out / f"build-{form}"),
        "--specpath",
        str(out / f"spec-{form}"),
    ]
    for module in EXCLUDED_MODULES:
        args += ["--exclude-module", module]
    return args


def _is_forbidden_name(name: str) -> bool:
    """Return True when a dotted module name or a top-level bundle entry is forbidden.

    Args:
        name: A dotted module name, or the first part of a bundled path (a package folder, a
            ``.dist-info`` folder or a DLL).

    Returns:
        True for a :data:`FORBIDDEN_TOP_LEVEL` module, GPU-pack metadata or a CUDA library.
    """
    top = name.split(".", 1)[0]
    if top in FORBIDDEN_TOP_LEVEL:
        return True
    lowered = name.lower()
    if lowered.endswith(".dist-info") and lowered.startswith(FORBIDDEN_DIST_INFO_PREFIXES):
        return True
    return lowered.endswith((".dll", ".so")) and lowered.startswith(FORBIDDEN_LIBRARY_PREFIXES)


def _bundle_top(parts: Sequence[str]) -> str | None:
    """Return the first part of a bundled path below the executable's folder and ``_internal``.

    Args:
        parts: The path's parts relative to the release folder (or a package-archive name's).

    Returns:
        That first part, or None for the executable's folder or ``_internal`` itself.
    """
    rest = list(parts)
    if rest and rest[0] == APP_NAME:
        rest = rest[1:]
    if rest and rest[0] == "_internal":
        rest = rest[1:]
    return rest[0] if rest else None


def forbidden_paths(root: Path) -> list[str]:
    """Return every bundled file or folder whose top-level entry is forbidden.

    Args:
        root: The release folder.

    Returns:
        The offending paths relative to ``root`` (POSIX form), sorted; empty when clean.
    """
    found: list[str] = []
    for path in root.rglob("*"):
        top = _bundle_top(path.relative_to(root).parts)
        if top is not None and _is_forbidden_name(top):
            found.append(path.relative_to(root).as_posix())
    return sorted(found)


def archive_names(executable: Path) -> tuple[list[str], list[str]]:
    """Return the executable's embedded package entries and its frozen-module names.

    The executable carries PyInstaller's package archive (the CArchive). Its entries are the
    bundled binaries and data in the one-file form, and the scripts in both forms. Among them,
    the ``PYZ`` holds every frozen module.

    Args:
        executable: The built executable.

    Returns:
        (package entry names, PYZ module names).
    """
    readers = importlib.import_module("PyInstaller.archive.readers")
    package = readers.CArchiveReader(str(executable))
    entries = [str(name) for name in package.toc]
    modules: list[str] = []
    for name, entry in package.toc.items():
        if entry[-1] == readers.PKG_ITEM_PYZ:
            modules += [str(module) for module in package.open_embedded_archive(name).toc]
    return entries, modules


def forbidden_entries(executable: Path) -> list[str]:
    """Return every archive entry or frozen module that must not be in the bundle.

    The checks:

    - a forbidden top-level name (:data:`FORBIDDEN_TOP_LEVEL`) or GPU-pack metadata;
    - a ``clearwater`` subpackage frozen at the top level (:data:`SHADOW_NAMES`);
    - an ``io`` with submodules (as ``clearwater.io`` has), not the stdlib's flat module;
    - a non-standard-library top-level module outside :data:`ALLOWED_TOP_LEVEL` (a package
      that leaked in from the development environment).

    Args:
        executable: The built executable.

    Returns:
        The offending names, each prefixed ``pkg:``, ``pyz:`` or ``pyz-unexpected:``; empty
        when clean.
    """
    entries, modules = archive_names(executable)
    bad = [f"pkg:{e}" for e in entries if _is_forbidden_name(_bundle_top(Path(e).parts) or "")]
    bad += [f"pyz:{m}" for m in modules if _is_forbidden_name(m)]
    bad += [f"pyz:{m}" for m in modules if m.split(".", 1)[0] in SHADOW_NAMES]
    bad += [f"pyz:{m}" for m in modules if m.startswith("io.")]
    tops = {m.split(".", 1)[0] for m in modules}
    unexpected = tops - ALLOWED_TOP_LEVEL - sys.stdlib_module_names
    bad += [f"pyz-unexpected:{t}" for t in unexpected]
    return sorted(bad)


def find_executable(root: Path) -> Path:
    """Return the built executable under a release folder.

    Args:
        root: The release folder.

    Returns:
        The executable's path.

    Raises:
        FileNotFoundError: No executable named :data:`APP_NAME` is there.
    """
    suffix = ".exe" if sys.platform == "win32" else ""
    for candidate in (root / APP_NAME / f"{APP_NAME}{suffix}", root / f"{APP_NAME}{suffix}"):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"no {APP_NAME}{suffix} under {root}")


def tree_size(path: Path) -> int:
    """Return the total size in bytes of a file, or of every file under a folder.

    Args:
        path: A file or a folder.

    Returns:
        The size in bytes.
    """
    if path.is_file():
        return path.stat().st_size
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def size_by_top_level(executable: Path) -> list[tuple[str, int]]:
    """Return the bundle's size by top-level entry beside the executable, largest first.

    For the one-folder form, this covers the executable and each entry of its
    ``_internal`` folder. For the one-file form, it covers the executable itself and anything
    copied beside it.

    Args:
        executable: The built executable.

    Returns:
        (relative name, bytes) pairs.
    """
    home = executable.parent
    rows: list[tuple[str, int]] = []
    for entry in sorted(home.iterdir()):
        if entry.name == "_internal" and entry.is_dir():
            rows += [(f"_internal/{e.name}", tree_size(e)) for e in sorted(entry.iterdir())]
        else:
            rows.append((entry.name, tree_size(entry)))
    return sorted(rows, key=lambda row: (-row[1], row[0]))


def copy_ffmpeg(destination: Path, tools: Iterable[str] = FFMPEG_TOOLS) -> list[Path]:
    """Copy the FFmpeg tools found on this machine's PATH beside the executable.

    Spike only: it proves the PATH-less run. The real bundle rule is WP6.3's.

    Args:
        destination: The executable's folder.
        tools: The tool names to copy.

    Returns:
        The copied files.

    Raises:
        FileNotFoundError: A tool is not on the PATH.
    """
    copied: list[Path] = []
    for tool in tools:
        found = shutil.which(tool)
        if found is None:
            raise FileNotFoundError(f"{tool} is not on the PATH")
        source = Path(found).resolve()
        target = destination / source.name
        shutil.copy2(source, target)
        copied.append(target)
    return copied


def run_pyinstaller(args: Sequence[str]) -> None:
    """Run PyInstaller in this process: ``PyInstaller.__main__.run(args)``.

    Args:
        args: The command line (:func:`pyinstaller_args`).

    Raises:
        SystemExit: PyInstaller's own exit on a failed build (non-zero status).
    """
    main = importlib.import_module("PyInstaller.__main__")
    main.run(list(args))


def build(form: Form, *, out: Path, with_ffmpeg: bool = False) -> int:
    """Build one form, check it, and print its summary.

    Args:
        form: The PyInstaller form.
        out: The output folder.
        with_ffmpeg: Copy FFmpeg and ffprobe beside the executable after the build.

    Returns:
        0 when the build succeeded and the bundle holds nothing forbidden, else 1.
    """
    version = app_version()
    args = pyinstaller_args(form, out=out, version=version)
    print(f"build {form}: PyInstaller {' '.join(args)}", flush=True)
    start = time.monotonic()
    run_pyinstaller(args)
    wall = time.monotonic() - start
    root = release_dir(out, form, version)
    executable = find_executable(root)
    if with_ffmpeg:
        for path in copy_ffmpeg(executable.parent):
            print(f"copied {path}")
    bad = forbidden_paths(root) + forbidden_entries(executable)
    print(f"build {form}: wall {wall:.1f} s; executable {executable}")
    for name, size in size_by_top_level(executable):
        print(f"  size {size / 2**20:10.1f} MiB  {name}")
    print(f"  total {tree_size(root) / 2**20:.1f} MiB under {root}")
    if bad:
        print(f"FORBIDDEN in the bundle ({len(bad)}):")
        for name in bad[:50]:
            print(f"  {name}")
        return 1
    print("forbidden-module check: PASS (none of " + ", ".join(FORBIDDEN_TOP_LEVEL) + ";")
    print("  non-stdlib top-level modules all in ALLOWED_TOP_LEVEL)")
    return 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse the command line.

    Args:
        argv: The arguments; ``sys.argv[1:]`` when None.

    Returns:
        The parsed namespace (``form``, ``out``, ``with_ffmpeg``).
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--form", choices=FORMS, required=True)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--with-ffmpeg", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the build script.

    Args:
        argv: The arguments; ``sys.argv[1:]`` when None.

    Returns:
        The exit status.
    """
    options = parse_args(argv)
    out = Path(os.path.abspath(options.out))
    return build(cast(Form, options.form), out=out, with_ffmpeg=options.with_ffmpeg)


if __name__ == "__main__":
    raise SystemExit(main())
