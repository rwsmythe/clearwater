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
The standard-library modules that only the pack imports are bundled as hidden imports (a scan
of the pack's ``.py`` files plus :data:`PACK_EXTENSION_STDLIB_NEEDS`), and the build fails if
any of them is missing from the bundle (:func:`missing_hidden_imports`; CHARC's F-C2 ruling).

Usage::

    uv run --no-sync python tools/package/build.py --form onedir
    uv run --no-sync python tools/package/build.py --form onefile --with-ffmpeg
    uv run --no-sync python tools/package/build.py --write-manifest <pack root>/<stamp>
    uv run --no-sync python tools/package/build.py --verify <pack root>/<stamp>

``--write-manifest`` writes ``manifest.json`` for a GPU pack filled by hand (the loader's
layout, :mod:`clearwater.gpu_pack`); the WP6.3 downloader will write the same file.
``--verify`` runs the FULL check on such a pack (every listed file's sha256 and size, plus the
loader's start-up checks) and lists each problem.

This is spike tooling (evidence, not product): see ``tools/package/README.md``.
"""

from __future__ import annotations

import argparse
import ast
import importlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path
from typing import Literal, NamedTuple, Protocol, cast

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
    "cudnn",
    "cufft",
    "curand",
    "cusolver",
    "cusparse",
    "cutensor",
    "nccl",
    "nvblas",
    "nvjitlink",
    "nvrtc",
    "nvtx",
)
"""CUDA library file-name prefixes (lower case) that must not be bundled.

Every DLL the locked pack wheels install starts with one of these (a test reads their
``RECORD`` files); ``cudnn``, ``cutensor``, ``nccl`` and ``nvtx`` are CuPy's optional CUDA
libraries, outside the lock (Reviewer A r2 #4).
"""

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

GPU_MODULE_NAMES: frozenset[str] = frozenset(n for n in FORBIDDEN_TOP_LEVEL if n != "tests")
"""Names (compared lower-case) that must not be ANY component of a bundled path or module."""

GPU_NAME_EXCEPTIONS: tuple[tuple[str, ...], ...] = (
    ("scipy", "_external", "array_api_compat", "cupy"),
)
"""Component prefixes whose LAST component may be a :data:`GPU_MODULE_NAMES` name.

SciPy's vendored ``array_api_compat`` ships its own ``cupy`` adapter subpackage inside the
scipy wheel. It is SciPy's code, not CuPy's (it imports ``cupy`` only when handed CuPy
arrays), so it is not GPU-pack content. Any other component of such a path is still checked.
"""

CUDA_LIBRARY = re.compile(
    r"(?:lib)?(?:" + "|".join(FORBIDDEN_LIBRARY_PREFIXES) + r")[^/\\]*\.(?:dll|so(?:\.\d+)*)"
)
"""A CUDA library file name, lower case: ``nvrtc64_120_0.dll``, ``libcudart.so.12`` (F11)."""

ZIP_SUFFIXES: tuple[str, ...] = (".zip", ".egg", ".whl")
"""File-name suffixes always opened as ZIP archives (other files are opened on their magic)."""

ZIP_MAGIC = b"PK\x03\x04"
"""The first bytes of a ZIP archive (a local file header)."""

MAX_ZIP_DEPTH = 4
"""How deep ZIP archives nested inside ZIP archives are opened."""

MODULE_SUFFIXES: tuple[str, ...] = (".py", ".pyc", ".pyd", ".so")
"""Suffixes of loose Python modules and extension modules (the allowlist applies to them)."""

_ALLOWED_FOLDED: frozenset[str] = frozenset(name.casefold() for name in ALLOWED_TOP_LEVEL)
_STDLIB_FOLDED: frozenset[str] = frozenset(name.casefold() for name in sys.stdlib_module_names)
"""The dependency allowlist and the stdlib names, case-folded as the GPU-name checks are
(Reviewer A r3 #9: ``pyside6/QtCore.pyd`` is ``PySide6/QtCore.pyd`` on Windows)."""

BOOT_MODULE_PREFIXES: tuple[str, ...] = ("pyimod", "pyiboot", "pyi_rth_")
"""PyInstaller's own boot modules, stored as CArchive module entries."""

PYINSTALLER_CONFIG_FOLDER = "pyinstaller-config"
"""The folder under the output folder for PyInstaller's cache (``PYINSTALLER_CONFIG_DIR``)."""


def app_version(init_file: Path | None = None) -> str:
    """Return ``clearwater.__version__`` as written in this tree's ``src``, without importing it.

    Parsing the file (rather than importing the package) writes no bytecode into ``src`` and
    cannot return an already-imported package's version (Reviewer A F8, F10).

    Args:
        init_file: The package's ``__init__.py``; this tree's when None.

    Returns:
        The version string, for example ``"1.0.0"``.

    Raises:
        ValueError: The file assigns no string ``__version__``.
    """
    path = REPO_ROOT / "src" / "clearwater" / "__init__.py" if init_file is None else init_file
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "__version__" for t in node.targets)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            return node.value.value
    raise ValueError(f"no string __version__ in {path}")


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


def pyinstaller_args(
    form: Form, *, out: Path, version: str, hidden: Sequence[str] = ()
) -> list[str]:
    """Return PyInstaller's command line for one form: the ONE spec of both forms.

    Args:
        form: ``"onedir"`` or ``"onefile"``; the only difference between the two lists.
        out: The output folder; ``dist-<form>``, ``build-<form>`` and ``spec-<form>`` go there.
        version: The application version (it names the release folder).
        hidden: Modules passed as ``--hidden-import`` (the GPU pack's standard-library needs,
            :func:`hidden_imports`), in the order given.

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
    for module in hidden:
        args += ["--hidden-import", module]
    return args


def split_name(name: str) -> list[str]:
    """Split a bundled path or archive entry name on either separator.

    Args:
        name: A relative path, a CArchive entry name (back slashes on Windows) or a ZIP
            member name.

    Returns:
        Its non-empty components.
    """
    return [part for part in re.split(r"[\\/]+", name) if part not in ("", ".")]


def name_violations(parts: Sequence[str], *, module_root: bool) -> list[str]:
    """Return the rules a bundled name breaks; every comparison is on lower-cased names.

    The rules:

    - ``gpu-module``: ANY component is (or starts with ``<name>.``) one of
      :data:`GPU_MODULE_NAMES` (Reviewer A F1, F2), except as :data:`GPU_NAME_EXCEPTIONS`
      allows;
    - ``gpu-metadata``: any component is GPU-pack distribution metadata;
    - ``tests``: the first component is the test suite;
    - ``cuda-library``: the last component is a CUDA library (:data:`CUDA_LIBRARY`);
    - when ``module_root`` (the name is relative to a folder on the frozen ``sys.path``) and
      the name is a loose module or an extension module (:data:`MODULE_SUFFIXES`):
      ``shadow`` for a ``clearwater`` subpackage (or a package ``io``) at the top level, and
      ``unexpected-module`` for a top-level name outside :data:`ALLOWED_TOP_LEVEL` and the
      standard library (Reviewer A F5).

    Args:
        parts: The name's components, relative to the bundle's root (the executable's
            ``_internal`` folder, the one-file archive, or a ZIP archive's root).
        module_root: Whether ``parts`` are relative to a folder on the frozen ``sys.path``.

    Returns:
        The broken rules, sorted; empty when the name is allowed.
    """
    lowered = [part.lower() for part in parts]
    if not lowered:
        return []
    rules: set[str] = set()
    stems = tuple(part.split(".", 1)[0] for part in lowered)
    excepted = {len(e) - 1 for e in GPU_NAME_EXCEPTIONS if stems[: len(e)] == e}
    for index, stem in enumerate(stems):
        if stem in GPU_MODULE_NAMES and index not in excepted:
            rules.add("gpu-module")
    for part in lowered:
        if part.endswith((".dist-info", ".egg-info")) and part.startswith(
            FORBIDDEN_DIST_INFO_PREFIXES
        ):
            rules.add("gpu-metadata")
    if lowered[0].split(".", 1)[0] == "tests":
        rules.add("tests")
    if CUDA_LIBRARY.fullmatch(lowered[-1]):
        rules.add("cuda-library")
    if module_root and lowered[-1].endswith(MODULE_SUFFIXES):
        top = parts[0] if len(parts) > 1 else parts[0].split(".", 1)[0]
        if top.lower() in SHADOW_NAMES or (top.lower() == "io" and len(parts) > 1):
            rules.add("shadow")
        elif top.casefold() not in _ALLOWED_FOLDED and top.casefold() not in _STDLIB_FOLDED:
            rules.add("unexpected-module")
    return sorted(rules)


def module_violations(module: str, *, allow_boot: bool = False) -> list[str]:
    """Return the rules a frozen module name (``a.b.c``) breaks: :func:`name_violations`.

    Args:
        module: A dotted module name from the PYZ or a CArchive module entry.
        allow_boot: Exempt PyInstaller's boot modules (:data:`BOOT_MODULE_PREFIXES`) from the
            dependency allowlist (``shadow``, ``unexpected-module``) ONLY; their names are still
            checked for GPU content (Reviewer A r2 #5).

    Returns:
        The broken rules, sorted.
    """
    parts = module.split(".")
    boot = allow_boot and module.startswith(BOOT_MODULE_PREFIXES)
    return name_violations([*parts[:-1], parts[-1] + ".pyc"], module_root=not boot)


def _is_zip_name(name: str) -> bool:
    """Return True when a name has a ZIP suffix (:data:`ZIP_SUFFIXES`)."""
    return name.lower().endswith(ZIP_SUFFIXES)


def zip_violations(
    source: Path | bytes, label: str, *, module_root: bool, depth: int = 0
) -> list[str]:
    """Return every rule broken by a ZIP archive's members, recursively, in memory.

    Nothing is extracted to disk: member names are read from the archive's directory, and a
    nested archive (a ZIP suffix, or a member starting with the ZIP magic) is read into
    memory and opened in turn, down to :data:`MAX_ZIP_DEPTH` (Reviewer A F3).

    Args:
        source: The archive: a file, or its bytes.
        label: How the archive is named in a violation (its bundle path).
        module_root: Whether the archive is itself on the frozen ``sys.path`` (a ZIP at the
            bundle's root, as ``base_library.zip``); nested archives never are.
        depth: The nesting depth of this archive.

    Returns:
        Violations as ``<label>!<member> (<rule>)``; an archive that cannot be read is a
        violation itself (``unreadable-zip``).
    """
    found: list[str] = []
    try:
        handle = zipfile.ZipFile(source if isinstance(source, Path) else io.BytesIO(source))
    except (zipfile.BadZipFile, OSError):
        return [f"{label} (unreadable-zip)"]
    with handle:
        for member in handle.namelist():
            parts = split_name(member)
            shown = f"{label}!{'/'.join(parts)}"
            found += [
                f"{shown} ({rule})" for rule in name_violations(parts, module_root=module_root)
            ]
            if member.endswith("/"):
                continue
            with handle.open(member) as data:
                nested = _is_zip_name(member) or data.read(len(ZIP_MAGIC)) == ZIP_MAGIC
            if nested:
                if depth + 1 > MAX_ZIP_DEPTH:
                    found.append(f"{shown} (zip-too-deep)")
                else:
                    found += zip_violations(
                        handle.read(member), shown, module_root=False, depth=depth + 1
                    )
    return found


def _starts_with_zip_magic(path: Path) -> bool:
    """Return True when a file begins with the ZIP magic."""
    with path.open("rb") as handle:
        return handle.read(len(ZIP_MAGIC)) == ZIP_MAGIC


def _bundle_parts(parts: Sequence[str]) -> tuple[list[str], bool]:
    """Strip the release folder's ``Clearwater/`` and ``_internal/`` from a dist path.

    Args:
        parts: The path's components relative to the release folder.

    Returns:
        (the components relative to ``_internal``, or to the folder beside the executable
        when the path is not under ``_internal``; whether it is under ``_internal``, the
        one-folder form's folder on the frozen ``sys.path``). The one-file form's ``sys.path``
        folder is its unpacked archive, checked by :func:`forbidden_entries`.
    """
    rest = list(parts)
    if len(rest) > 1 and rest[0] == APP_NAME:
        rest = rest[1:]
    if len(rest) > 1 and rest[0].lower() == "_internal":
        return rest[1:], True
    return rest, False


def forbidden_paths(root: Path) -> list[str]:
    """Return every bundled file or folder, or ZIP member, that breaks a bundle rule.

    Every path under ``root`` is checked by :func:`name_violations` on all its components;
    every ZIP archive (by suffix or magic) is opened in memory by :func:`zip_violations`.

    Args:
        root: The release folder.

    Returns:
        Violations as ``dist:<path> (<rule>)``, sorted; empty when clean.
    """
    found: list[str] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        parts, under_internal = _bundle_parts(relative.parts)
        is_file = path.is_file()
        # Every loose file meets the allowlist, wherever it sits: a module beside the
        # executable or at the release root is never legitimate (Reviewer A r2 #8).
        label = f"dist:{relative.as_posix()}"
        found += [f"{label} ({rule})" for rule in name_violations(parts, module_root=is_file)]
        if is_file and (_is_zip_name(path.name) or _starts_with_zip_magic(path)):
            found += zip_violations(path, label, module_root=under_internal and len(parts) == 1)
    return sorted(found)


class _Listing(Protocol):
    """The part of PyInstaller's ``ZlibArchiveReader`` the checks use."""

    toc: dict[str, object]


class _Package(Protocol):
    """The part of PyInstaller's ``CArchiveReader`` the checks use."""

    toc: dict[str, tuple[int, int, int, int, str]]

    def extract(self, name: str) -> bytes:
        """Return one entry's data, decompressed."""

    def open_embedded_archive(self, name: str) -> _Listing:
        """Return a reader of an embedded PYZ archive (its ``toc`` lists the modules)."""


def read_package(executable: Path) -> _Package:
    """Open the executable's package archive (PyInstaller's CArchive) for reading.

    Args:
        executable: The built executable.

    Returns:
        The reader.
    """
    readers = importlib.import_module("PyInstaller.archive.readers")
    return cast(_Package, readers.CArchiveReader(str(executable)))


def _pyz_modules(package: _Package, name: str) -> Iterator[str]:
    """Yield every module name in an embedded PYZ archive."""
    archive = package.open_embedded_archive(name)
    yield from (str(module) for module in archive.toc)


def forbidden_entries(executable: Path) -> list[str]:
    """Return every package-archive entry, frozen module or ZIP member that breaks a rule.

    The package archive (CArchive) is the executable's: the scripts and the PYZ in both
    forms, and every bundled binary and data file in the one-file form. Checked:

    - each entry's name, all components (:func:`name_violations`);
    - each PYZ module, all components, against the allowlist (:func:`module_violations`);
    - each module entry against the allowlist (PyInstaller's boot modules exempt from the
      allowlist only), and the script and run-time option entries by name;
    - each data or binary entry that is a ZIP archive (by suffix or magic), recursively and in
      memory (:func:`zip_violations`).

    Args:
        executable: The built executable.

    Returns:
        Violations as ``pkg:<entry> (<rule>)`` or ``pyz:<module> (<rule>)``, sorted.
    """
    readers = importlib.import_module("PyInstaller.archive.readers")
    package = read_package(executable)
    found: list[str] = []
    for name, entry in package.toc.items():
        typecode = entry[-1]
        parts = split_name(name)
        label = f"pkg:{'/'.join(parts)}"
        if typecode == readers.PKG_ITEM_PYZ:
            # the container's own name too (Reviewer A r3 #11), by name rules only
            found += [f"{label} ({rule})" for rule in name_violations(parts, module_root=False)]
            for module in _pyz_modules(package, name):
                found += [f"pyz:{module} ({rule})" for rule in module_violations(module)]
            continue
        if typecode in (readers.PKG_ITEM_PYMODULE, readers.PKG_ITEM_PYPACKAGE):
            module = name.replace("\\", ".").replace("/", ".")
            found += [f"{label} ({r})" for r in module_violations(module, allow_boot=True)]
            continue
        if typecode in (readers.PKG_ITEM_PYSOURCE, readers.PKG_ITEM_RUNTIME_OPTION):
            # The entry script and the run-time hooks (options are not files): no allowlist,
            # but their names are checked for GPU content like every entry's (r2 #5).
            found += [f"{label} ({rule})" for rule in name_violations(parts, module_root=False)]
            continue
        found += [f"{label} ({rule})" for rule in name_violations(parts, module_root=True)]
        if typecode in (readers.PKG_ITEM_BINARY, readers.PKG_ITEM_DATA, readers.PKG_ITEM_ZIPFILE):
            data = package.extract(name)
            if _is_zip_name(name) or data[: len(ZIP_MAGIC)] == ZIP_MAGIC:
                found += zip_violations(data, label, module_root=len(parts) == 1)
    return sorted(found)


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


def tool_file_name(tool: str, platform: str | None = None) -> str:
    """Return a tool's canonical file name: ``ffmpeg.exe`` on Windows, ``ffmpeg`` elsewhere.

    Args:
        tool: The tool's name.
        platform: A ``sys.platform`` value; the running one when None.

    Returns:
        The file name ``find_tool`` looks for beside the executable.
    """
    kind = sys.platform if platform is None else platform
    return f"{tool}.exe" if kind == "win32" else tool


def tool_version(path: Path) -> str:
    """Run a copied tool's ``-version`` from its own folder, with only that folder on PATH.

    Args:
        path: The copied tool.

    Returns:
        The first line of its output, for example ``ffmpeg version 9.0.2-full_build-...``.

    Raises:
        RuntimeError: The tool did not run, exited non-zero, or printed no ``version`` line.
    """
    env = {key: value for key, value in os.environ.items() if key.upper() != "PATH"}
    env["PATH"] = str(path.parent)
    try:
        done = subprocess.run(
            [str(path), "-version"],
            cwd=path.parent,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError(f"{path.name} -version did not run: {error}") from error
    first = done.stdout.splitlines()[0] if done.stdout else ""
    if done.returncode != 0 or " version " not in f" {first} ":
        raise RuntimeError(f"{path.name} -version failed (exit {done.returncode}): {first!r}")
    return first


def copy_ffmpeg(destination: Path, tools: Iterable[str] = FFMPEG_TOOLS) -> list[tuple[Path, str]]:
    """Copy the FFmpeg tools found on this machine's PATH beside the executable, and check them.

    Spike only: it proves the PATH-less run. The real bundle rule is WP6.3's. Each tool is
    copied under its canonical name (:func:`tool_file_name`), whatever the PATH entry's target
    is called, and must then run on its own (:func:`tool_version`; Reviewer A F7).

    Args:
        destination: The executable's folder.
        tools: The tool names to copy.

    Returns:
        (the copied file, its version line) for each tool.

    Raises:
        FileNotFoundError: A tool is not on the PATH.
        RuntimeError: A copied tool does not run from the destination folder.
    """
    copied: list[tuple[Path, str]] = []
    for tool in tools:
        found = shutil.which(tool)
        if found is None:
            raise FileNotFoundError(f"{tool} is not on the PATH")
        target = destination / tool_file_name(tool)
        shutil.copy2(Path(found).resolve(), target)
        copied.append((target, tool_version(target)))
    return copied


def wheel_file_tags(filename: str) -> frozenset[str]:
    """Return the ``python-abi-platform`` tags a wheel file name declares.

    A compressed tag set (``py2.py3-none-any``) expands to each of its tags.

    Args:
        filename: A wheel file name, ``<name>-<version>[-<build>]-<py>-<abi>-<plat>.whl``.

    Returns:
        The tags, for example ``{"py2-none-any", "py3-none-any"}``.

    Raises:
        ValueError: The name is not a wheel file name.
    """
    if not filename.endswith(".whl"):
        raise ValueError(f"not a wheel file name: {filename!r}")
    parts = filename[: -len(".whl")].split("-")
    if len(parts) < 5:
        raise ValueError(f"not a wheel file name: {filename!r}")
    pythons, abis, platforms = (part.split(".") for part in parts[-3:])
    return frozenset(f"{p}-{a}-{t}" for p in pythons for a in abis for t in platforms)


def installed_wheel_tags(dist_info: Path) -> frozenset[str]:
    """Return the tags an installed distribution's ``WHEEL`` file records.

    Args:
        dist_info: The distribution's ``.dist-info`` folder.

    Returns:
        The ``Tag:`` values.

    Raises:
        OSError: The ``WHEEL`` file cannot be read.
    """
    text = (dist_info / "WHEEL").read_text(encoding="utf-8")
    return frozenset(
        line.split(":", 1)[1].strip() for line in text.splitlines() if line.startswith("Tag:")
    )


def manifest_document(folder: Path) -> dict[str, object]:
    """Return the manifest for a pack folder filled by hand with the lock's wheels.

    Each distribution of :data:`clearwater.gpu_pack.LOCKED_DISTRIBUTIONS` must be installed in
    ``folder/site-packages`` at its locked version. Its wheel is the one locked wheel whose
    tags match the installed ``WHEEL`` file's; the manifest records that wheel's lock sha256
    and the sha256 of the installed ``RECORD`` file. Reads only.

    Args:
        folder: The pack folder, ``<pack root>/<stamp>``.

    Returns:
        The manifest (format, stamp, distributions).

    Raises:
        FileNotFoundError: A distribution's metadata folder or ``RECORD`` is missing.
        ValueError: No locked wheel, or more than one, matches an installed distribution.
    """
    from clearwater import gpu_pack

    site = folder / gpu_pack.SITE_PACKAGES_NAME
    rows: list[dict[str, str]] = []
    for locked in gpu_pack.LOCKED_DISTRIBUTIONS:
        dist_info = site / locked.dist_info_name
        record = dist_info / "RECORD"
        if not record.is_file():
            raise FileNotFoundError(f"{locked.name} {locked.version}: no {record}")
        tags = installed_wheel_tags(dist_info)
        matches = [w for w in locked.wheels if wheel_file_tags(w[0]) & tags]
        if len(matches) != 1:
            raise ValueError(f"{locked.name}: {len(matches)} locked wheels match {sorted(tags)}")
        wheel, sha256 = matches[0]
        rows.append(
            {
                "name": locked.name,
                "version": locked.version,
                "wheel": wheel,
                "wheel_sha256": sha256,
                "record_sha256": gpu_pack.file_sha256(record),
            }
        )
    return {"format": gpu_pack.MANIFEST_FORMAT, "stamp": gpu_pack.STAMP, "distributions": rows}


def write_manifest(folder: Path) -> Path:
    """Write ``manifest.json`` into a pack folder filled by hand (design item 2).

    Args:
        folder: The pack folder; its name must be :data:`clearwater.gpu_pack.STAMP`.

    Returns:
        The manifest's path.

    Raises:
        ValueError: The folder is not named for this build's stamp, or a wheel does not match.
        FileNotFoundError: A distribution is not installed.
    """
    from clearwater import gpu_pack

    if folder.name != gpu_pack.STAMP:
        raise ValueError(f"the pack folder must be named {gpu_pack.STAMP!r}, not {folder.name!r}")
    document = manifest_document(folder)
    path = folder / gpu_pack.MANIFEST_NAME
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


def verify_pack(folder: Path) -> list[str]:
    """Return every problem the FULL pack check finds in a pack folder filled by hand.

    The full check is :func:`clearwater.gpu_pack.pack_problems` with ``full=True``: the cheap
    start-up check (the manifest against the lock, each ``RECORD``'s sha256, the ``WHEEL``
    platform tags, every listed file's existence and size, no unlisted top-level entry) plus
    each listed file's sha256 against its ``RECORD`` row. Reads only.

    Args:
        folder: The pack folder, ``<pack root>/<stamp>``.

    Returns:
        The problems, in check order; empty when the pack is clean.
    """
    from clearwater import gpu_pack

    problems: list[str] = []
    try:
        problems.extend(gpu_pack.pack_problems(folder, full=True))
    except OSError as error:
        problems.append(f"pack unreadable: {type(error).__name__}")
    return problems


def pack_census(folder: Path) -> tuple[int, int, int]:
    """Count a pack's ``RECORD`` rows, and the files and bytes under its ``site-packages``.

    Args:
        folder: The pack folder.

    Returns:
        (rows in the eleven ``RECORD`` files that parse, files on disk, bytes on disk).

    Raises:
        OSError: A ``RECORD`` file cannot be read.
    """
    from clearwater import gpu_pack

    site = folder / gpu_pack.SITE_PACKAGES_NAME
    rows = 0
    for locked in gpu_pack.LOCKED_DISTRIBUTIONS:
        record = site / locked.dist_info_name / "RECORD"
        if record.is_file():
            parsed = gpu_pack.parse_record(record.read_text(encoding="utf-8"))
            rows += 0 if isinstance(parsed, str) else len(parsed)
    files = 0
    size = 0
    for parent, _dirs, names in os.walk(site):
        for name in names:
            files += 1
            size += os.stat(os.path.join(parent, name)).st_size
    return rows, files, size


def verify(folder: Path) -> int:
    """Run the full check on a hand-filled pack and print the result (``--verify``).

    Args:
        folder: The pack folder.

    Returns:
        0 with a one-line summary when the pack is clean; 1 with each problem listed.
    """
    from clearwater import gpu_pack

    problems = verify_pack(folder)
    if problems:
        print(f"verify {folder}: FAIL ({len(problems)} problems)")
        for problem in problems:
            print(f"  {problem}")
        return 1
    rows, files, size = pack_census(folder)
    print(
        f"verify {folder}: PASS ({len(gpu_pack.LOCKED_DISTRIBUTIONS)} distributions;"
        f" {rows} RECORD rows, each file's sha256 and size; {files} files,"
        f" {size / 2**20:.1f} MiB)"
    )
    return 0


# F-C2: the standard-library modules the GPU pack needs from the bundle.

PACK_EXTENSION_STDLIB_NEEDS: tuple[str, ...] = ("graphlib",)
"""Standard-library modules that only the pack's EXTENSION modules import (CHARC's F-C2).

No ``.py`` file of the pack names them, so :func:`scan_stdlib_imports` cannot find them:
``graphlib`` is imported by a CuPy extension module (measured in group 2b-2,
``t3c/import-gap.json``). The list is committed and edited by hand on a lock bump.
"""

ImportKind = Literal["builtin", "module", "package"]
"""How a standard-library module exists on the build platform."""


def stdlib_search_path() -> list[str]:
    """Return the build interpreter's standard-library folders (sources and extensions).

    Returns:
        The existing folders among ``sysconfig``'s ``stdlib`` and ``platstdlib``, their
        ``lib-dynload`` (POSIX) and ``<base prefix>/DLLs`` (Windows), without repeats.
    """
    import sysconfig

    folders: list[str] = []
    for key in ("stdlib", "platstdlib"):
        base = sysconfig.get_path(key)
        folders += [base, os.path.join(base, "lib-dynload")]
    folders.append(os.path.join(sys.base_prefix, "DLLs"))
    seen: list[str] = []
    for folder in folders:
        if os.path.isdir(folder) and folder not in seen:
            seen.append(folder)
    return seen


def stdlib_kind(name: str, search: Sequence[str] | None = None) -> ImportKind | None:
    """Return how the standard-library module ``name`` exists here, or None when it does not.

    Found WITHOUT importing anything: built-ins from ``sys.builtin_module_names``, the rest by
    ``importlib.machinery.PathFinder`` over :func:`stdlib_search_path`, one dotted part at a
    time (a part is looked for only inside a package found for the part before it).

    Args:
        name: A dotted module name whose top level is in ``sys.stdlib_module_names``.
        search: The standard-library folders; :func:`stdlib_search_path` when None.

    Returns:
        ``"builtin"``, ``"package"`` or ``"module"``; None when no such module exists here
        (not on this platform, or not a module at all).
    """
    import importlib.machinery

    parts = name.split(".")
    if len(parts) == 1 and name in sys.builtin_module_names:
        return "builtin"
    locations: list[str] | None = list(stdlib_search_path() if search is None else search)
    spec = None
    for index in range(len(parts)):
        if locations is None:
            return None
        spec = importlib.machinery.PathFinder.find_spec(".".join(parts[: index + 1]), locations)
        if spec is None:
            return None
        found = spec.submodule_search_locations
        locations = None if found is None else list(found)
    return "package" if locations is not None else "module"


class StdlibScan:
    """What :func:`scan_stdlib_imports` found.

    Attributes:
        modules: Each standard-library module that exists here -> where it is named
            (``<label>:<line>``).
        unavailable: Each standard-library name that does not exist on this platform (an
            import under a platform guard, such as ``fcntl`` on Windows) -> where named.
        unparsable: The files that could not be parsed (``<label>: <error>``).
    """

    def __init__(self) -> None:
        """Start an empty scan (a plain class: ``build.py`` is loaded by path in the tests)."""
        self.modules: dict[str, list[str]] = {}
        self.unavailable: dict[str, list[str]] = {}
        self.unparsable: list[str] = []


class HiddenImport(NamedTuple):
    """One member of the resolved hidden-import set.

    Attributes:
        name: The dotted module name passed to ``--hidden-import``.
        sources: ``"committed"`` (:data:`PACK_EXTENSION_STDLIB_NEEDS`) and / or ``"scan"``.
        named_by: The first three places the scan found it (``<dist>:<path>:<line>``).
        named: How many places the scan found it.
    """

    name: str
    sources: tuple[str, ...]
    named_by: tuple[str, ...] = ()
    named: int = 0


def _literal_import(call: ast.Call) -> str | None:
    """Return the module a literal ``importlib.import_module("x")`` / ``__import__("x")`` names.

    None for any other call: a non-literal argument or a relative name.
    """
    func = call.func
    named = (isinstance(func, ast.Name) and func.id in ("import_module", "__import__")) or (
        isinstance(func, ast.Attribute)
        and func.attr == "import_module"
        and isinstance(func.value, ast.Name)
        and func.value.id == "importlib"
    )
    if not named or not call.args:
        return None
    first = call.args[0]
    if not isinstance(first, ast.Constant) or not isinstance(first.value, str):
        return None
    return first.value if first.value and not first.value.startswith(".") else None


def import_candidates(tree: ast.AST) -> list[tuple[str, int, bool]]:
    """Return every absolute module name a parsed file may import, with its line.

    Rules (CHARC's F-C2 (b)): every ``import a.b`` and ``from a.b import c`` ANYWHERE in the
    tree (module level, functions, ``if`` / ``try`` blocks: conditional imports count);
    ``importlib.import_module("x")`` and ``__import__("x")`` with a string literal; relative
    imports (``from . import x``, ``import_module(".x", ...)``) are skipped, as is any
    non-literal dynamic import. ``from __future__ import x`` counts: it imports
    ``__future__`` at run time.

    Args:
        tree: A parsed module.

    Returns:
        (name, line, attribute_ok): ``attribute_ok`` marks ``a.b.c`` from ``from a.b import
        c``, which names a submodule only when one exists (else ``c`` is an attribute).
    """
    found: list[tuple[str, int, bool]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found += [(alias.name, node.lineno, False) for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.append((node.module, node.lineno, False))
            found += [
                (f"{node.module}.{alias.name}", node.lineno, True)
                for alias in node.names
                if alias.name != "*"
            ]
        elif isinstance(node, ast.Call):
            literal = _literal_import(node)
            if literal is not None:
                found.append((literal, node.lineno, False))
    return found


def _resolve(name: str, attribute_ok: bool, search: Sequence[str]) -> tuple[str | None, bool]:
    """Resolve one candidate to the standard-library module it needs.

    Returns:
        (module, available): the module (None when the candidate needs none: not the
        standard library, or an attribute), and whether it exists here. ``import os.path``
        resolves to ``os`` (``path`` is an attribute of a module that is not a package).
    """
    parts = name.split(".")
    if parts[0] not in sys.stdlib_module_names:
        return None, True
    if stdlib_kind(parts[0], search) is None:
        return (None, True) if attribute_ok else (parts[0], False)
    resolved = parts[0]
    for part in parts[1:]:
        kind = stdlib_kind(resolved, search)
        if kind != "package":
            return resolved, True  # the rest is an attribute (os.path)
        candidate = f"{resolved}.{part}"
        if stdlib_kind(candidate, search) is None:
            return (None if attribute_ok else candidate), attribute_ok
        resolved = candidate
    return (None if attribute_ok and resolved != name else resolved), True


def scan_stdlib_imports(
    files: Iterable[tuple[str, Path]], search: Sequence[str] | None = None
) -> StdlibScan:
    """Return the standard-library modules that the given ``.py`` files import.

    See :func:`import_candidates` for what counts as an import. Third-party names (a top level
    not in ``sys.stdlib_module_names``) are not reported. A ``from a import b`` adds ``a.b``
    only when ``a`` is a package with a submodule ``b``.

    Args:
        files: (label, path) of each ``.py`` file; the label names it in the result.
        search: The standard-library folders; :func:`stdlib_search_path` when None.

    Returns:
        The scan.
    """
    folders = list(stdlib_search_path() if search is None else search)
    scan = StdlibScan()
    resolved: dict[tuple[str, bool], tuple[str | None, bool]] = {}
    for label, path in files:
        try:
            tree = ast.parse(path.read_bytes(), filename=str(path))
        except (SyntaxError, ValueError, OSError) as error:
            scan.unparsable.append(f"{label}: {type(error).__name__}")
            continue
        for name, line, attribute_ok in import_candidates(tree):
            key = (name, attribute_ok)
            if key not in resolved:
                resolved[key] = _resolve(name, attribute_ok, folders)
            module, available = resolved[key]
            if module is not None:
                target = scan.modules if available else scan.unavailable
                target.setdefault(module, []).append(f"{label}:{line}")
    return scan


def pack_sources(names: Iterable[str] | None = None) -> list[tuple[str, Path]]:
    """Return every ``.py`` file the pack distributions install, from this environment.

    The distributions are the lock's pack set (:data:`clearwater.gpu_pack.LOCKED_DISTRIBUTIONS`,
    the set the manifest names), read from the build environment's installed copies through
    their ``RECORD`` (``importlib.metadata``).

    Args:
        names: Distribution names; the pack's eleven when None.

    Returns:
        (``<distribution>:<path in RECORD>``, absolute path) pairs, sorted.

    Raises:
        importlib.metadata.PackageNotFoundError: A distribution is not installed here.
        ValueError: A distribution lists no files, or (the pack's own set, ``names`` None)
            its installed version is not the lock's.
    """
    import importlib.metadata

    if names is None:
        sys.dont_write_bytecode = True  # importing clearwater must not write into src (F8)
        from clearwater import gpu_pack

        names = [locked.name for locked in gpu_pack.LOCKED_DISTRIBUTIONS]
        versions = {locked.name: locked.version for locked in gpu_pack.LOCKED_DISTRIBUTIONS}
    else:
        versions = {}
    rows: list[tuple[str, Path]] = []
    for name in names:
        distribution = importlib.metadata.distribution(name)
        expected = versions.get(name)
        if expected is not None and distribution.version != expected:
            # a stale build environment would describe other pack code (Reviewer A r3 #12)
            raise ValueError(f"{name}: installed {distribution.version}, the lock has {expected}")
        files = distribution.files
        if files is None:
            raise ValueError(f"{name}: no RECORD")
        for file in files:
            if file.suffix == ".py":
                rows.append(
                    (f"{name}:{file.as_posix()}", Path(str(distribution.locate_file(file))))
                )
    return sorted(rows)


def hidden_imports(
    scan: StdlibScan, committed: Sequence[str] = PACK_EXTENSION_STDLIB_NEEDS
) -> list[HiddenImport]:
    """Return the resolved hidden-import set: the scan's modules plus the committed list.

    Args:
        scan: :func:`scan_stdlib_imports` over :func:`pack_sources`.
        committed: The committed list (:data:`PACK_EXTENSION_STDLIB_NEEDS`).

    Returns:
        One entry per module name, sorted by name, each marked by its source(s).
    """
    rows: list[HiddenImport] = []
    for name in sorted(set(scan.modules) | set(committed)):
        places = scan.modules.get(name, [])
        sources = tuple(
            source
            for source, hit in (("committed", name in committed), ("scan", bool(places)))
            if hit
        )
        rows.append(HiddenImport(name, sources, tuple(places[:3]), len(places)))
    return rows


def _archive_module_names(names: Iterable[str]) -> set[str]:
    """Return the module names that ZIP member or file paths hold (``a/b.pyc`` -> ``a.b``)."""
    modules: set[str] = set()
    for name in names:
        parts = [p for p in name.replace("\\", "/").split("/") if p]
        if parts and parts[0] == "lib-dynload":
            parts = parts[1:]
        if not parts:
            continue
        stem, _, suffix = parts[-1].partition(".")
        if not suffix or "." + suffix.rsplit(".", 1)[-1] not in MODULE_SUFFIXES:
            continue
        dotted = [*parts[:-1]] if stem == "__init__" else [*parts[:-1], stem]
        if dotted:
            modules.add(".".join(dotted))
    return modules


def bundled_modules(executable: Path) -> set[str]:
    """Return every module name the built bundle can import, wherever PyInstaller put it.

    Looked in: the PYZ archive(s) inside the executable's package archive (pure-Python
    modules); the package archive's own module entries (``struct`` and PyInstaller's boot
    modules); ``base_library.zip`` (the boot-time standard library: ``_internal/`` in the
    one-folder form, a package-archive entry in the one-file form); the extension modules
    (``.pyd`` / ``.so``: files under ``_internal/`` in the one-folder form, binary entries of
    the package archive in the one-file form); and the interpreter's built-in modules (inside
    the bundled ``python3*.dll``, the same build as this interpreter's).

    Args:
        executable: The built executable.

    Returns:
        The dotted module names.
    """
    readers = importlib.import_module("PyInstaller.archive.readers")
    package = read_package(executable)
    modules: set[str] = set(sys.builtin_module_names)
    entries: list[str] = []
    for name, entry in package.toc.items():
        typecode = entry[-1]
        if typecode == readers.PKG_ITEM_PYZ:
            modules.update(_pyz_modules(package, name))
        elif typecode in (readers.PKG_ITEM_PYMODULE, readers.PKG_ITEM_PYPACKAGE):
            modules.add(name.replace("\\", ".").replace("/", "."))  # ``struct``, the boot modules
        elif name.replace("\\", "/").split("/")[-1] == "base_library.zip":
            with zipfile.ZipFile(io.BytesIO(package.extract(name))) as archive:
                modules |= _archive_module_names(archive.namelist())
        else:
            entries.append(name)
    modules |= _archive_module_names(entries)
    internal = executable.parent / "_internal"
    if internal.is_dir():
        files = [p.relative_to(internal).as_posix() for p in internal.rglob("*") if p.is_file()]
        modules |= _archive_module_names(files)
        base = internal / "base_library.zip"
        if base.is_file():
            with zipfile.ZipFile(base) as archive:
                modules |= _archive_module_names(archive.namelist())
    return modules


def missing_hidden_imports(
    executable: Path, wanted: Sequence[HiddenImport], bundled: set[str] | None = None
) -> list[str]:
    """Return each member of the hidden-import set that the bundle lacks, by name and source.

    Args:
        executable: The built executable.
        wanted: :func:`hidden_imports`.
        bundled: :func:`bundled_modules` (computed when None).

    Returns:
        ``hidden-import missing from the bundle: <name> (<sources>)`` lines, sorted.
    """
    have = bundled_modules(executable) if bundled is None else bundled
    return [
        f"hidden-import missing from the bundle: {row.name} ({'+'.join(row.sources)})"
        for row in wanted
        if row.name not in have
    ]


def write_hidden_import_report(
    path: Path, wanted: Sequence[HiddenImport], scan: StdlibScan, files: int
) -> Path:
    """Write the resolved hidden-import set as JSON (F-C2 (a): a lock bump shows its delta).

    Args:
        path: The report file.
        wanted: :func:`hidden_imports`.
        scan: The scan it came from (its unavailable names are recorded, not imported).
        files: How many ``.py`` files were scanned.

    Returns:
        ``path``.
    """
    document = {
        "committed": list(PACK_EXTENSION_STDLIB_NEEDS),
        "scanned_files": files,
        "hidden_imports": {
            row.name: {
                "sources": list(row.sources),
                "named_by": list(row.named_by),
                "named": row.named,
            }
            for row in wanted
        },
        "unavailable_here": {k: v[:3] for k, v in sorted(scan.unavailable.items())},
        "unparsable": scan.unparsable,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return path


def run_pyinstaller(args: Sequence[str]) -> None:
    """Run PyInstaller in this process: ``PyInstaller.__main__.run(args)``.

    Args:
        args: The command line (:func:`pyinstaller_args`).

    Raises:
        SystemExit: PyInstaller's own exit on a failed build (non-zero status).
    """
    main = importlib.import_module("PyInstaller.__main__")
    main.run(list(args))


def pyinstaller_config_dir(out: Path) -> Path:
    """Return the folder PyInstaller's cache goes to: under the output folder (F4).

    Args:
        out: The output folder.

    Returns:
        ``out / "pyinstaller-config"``.
    """
    return out / PYINSTALLER_CONFIG_FOLDER


def clean_release_dir(out: Path, form: Form, version: str) -> Path:
    """Delete the release folder of one form before it is built again (Reviewer A F6).

    Only the release folder under ``out`` is deleted, so nothing from an earlier build (such
    as FFmpeg copied by ``--with-ffmpeg``) survives into the new one.

    Args:
        out: The output folder.
        form: The PyInstaller form.
        version: The application version.

    Returns:
        The (now absent) release folder.

    Raises:
        ValueError: The release folder does not lie inside ``out``.
    """
    root = release_dir(out, form, version)
    if not root.resolve().is_relative_to(out.resolve()):
        raise ValueError(f"{root} is not inside {out}")
    if root.exists():
        shutil.rmtree(root)
    return root


def build(form: Form, *, out: Path, with_ffmpeg: bool = False) -> int:
    """Build one form, check it, and print its summary.

    PyInstaller's cache is kept under ``out`` (``PYINSTALLER_CONFIG_DIR``), so ``--clean``
    touches nothing outside the output folder, and the release folder is emptied first.

    Args:
        form: The PyInstaller form.
        out: The output folder.
        with_ffmpeg: Copy FFmpeg and ffprobe beside the executable after the build.

    Returns:
        0 when the build succeeded and the bundle holds nothing forbidden, else 1.
    """
    version = app_version()
    try:
        sources = pack_sources()
    except (ImportError, ValueError) as error:  # PackageNotFoundError is an ImportError
        print(f"FAILED: the pack sources cannot be scanned: {error}")
        return 1
    scan = scan_stdlib_imports(sources)
    wanted = hidden_imports(scan)
    report = write_hidden_import_report(
        out / f"hidden-imports-{form}.json", wanted, scan, len(sources)
    )
    print(f"build {form}: {len(wanted)} hidden imports from {len(sources)} pack files; {report}")
    for row in wanted:
        print(f"  hidden-import {row.name} ({'+'.join(row.sources)}; named {row.named}x)")
    if scan.unparsable:
        print(f"FAILED: {len(scan.unparsable)} pack files could not be scanned:")
        for line in scan.unparsable:
            print(f"  {line}")
        return 1
    os.environ["PYINSTALLER_CONFIG_DIR"] = str(pyinstaller_config_dir(out))
    root = clean_release_dir(out, form, version)
    args = pyinstaller_args(form, out=out, version=version, hidden=[row.name for row in wanted])
    print(f"build {form}: PYINSTALLER_CONFIG_DIR={os.environ['PYINSTALLER_CONFIG_DIR']}")
    print(f"build {form}: PyInstaller {' '.join(args)}", flush=True)
    start = time.monotonic()
    run_pyinstaller(args)
    wall = time.monotonic() - start
    executable = find_executable(root)
    if with_ffmpeg:
        for path, line in copy_ffmpeg(executable.parent):
            print(f"copied {path}: {line}")
    check_start = time.monotonic()
    bad = forbidden_paths(root) + forbidden_entries(executable)
    missing = missing_hidden_imports(executable, wanted)
    check_wall = time.monotonic() - check_start
    print(f"build {form}: wall {wall:.1f} s; executable {executable}")
    for name, size in size_by_top_level(executable):
        print(f"  size {size / 2**20:10.1f} MiB  {name}")
    print(f"  total {tree_size(root) / 2**20:.1f} MiB under {root}")
    print(f"  bundle checks took {check_wall:.1f} s")
    if missing:
        print(f"FAILED: the bundle lacks {len(missing)} of the pack's standard-library needs:")
        for line in missing:
            print(f"  {line}")
    if bad:
        print(f"FORBIDDEN in the bundle ({len(bad)}):")
        for name in bad[:50]:
            print(f"  {name}")
    if missing or bad:
        return 1
    print(f"hidden-import check: PASS ({len(wanted)} modules, each in the bundle)")
    print("bundle check: PASS (no " + ", ".join(FORBIDDEN_TOP_LEVEL) + " at any depth or in")
    print("  any ZIP; no CUDA library; every module's top-level name allowed)")
    return 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse the command line.

    Args:
        argv: The arguments; ``sys.argv[1:]`` when None.

    Returns:
        The parsed namespace (``form``, ``out``, ``with_ffmpeg``, ``write_manifest``,
        ``verify``).
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--form", choices=FORMS)
    action.add_argument("--write-manifest", type=Path, metavar="PACK_FOLDER")
    action.add_argument("--verify", type=Path, metavar="PACK_FOLDER")
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
    if options.write_manifest is not None:
        sys.dont_write_bytecode = True  # importing clearwater must not write into src (F8)
        path = write_manifest(Path(os.path.abspath(options.write_manifest)))
        print(f"wrote {path}")
        return 0
    if options.verify is not None:
        sys.dont_write_bytecode = True
        return verify(Path(os.path.abspath(options.verify)))
    out = Path(os.path.abspath(options.out))
    return build(cast(Form, options.form), out=out, with_ffmpeg=options.with_ffmpeg)


if __name__ == "__main__":
    raise SystemExit(main())
