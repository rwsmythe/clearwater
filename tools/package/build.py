r"""Build Clearwater with PyInstaller and optionally bundle the pinned release FFmpeg.

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
    uv run --no-sync python tools/package/build.py --write-manifest <pack root>/<stamp>
    uv run --no-sync python tools/package/build.py --verify <pack root>/<stamp>

``--write-manifest`` writes ``manifest.json`` for a GPU pack filled by hand (the loader's
layout, :mod:`clearwater.gpu_pack`); the WP6.3 downloader will write the same file.
``--verify`` runs the FULL check on such a pack (every listed file's sha256 and size, plus the
loader's start-up checks) and lists each problem.

``--ffmpeg-from URL --ffmpeg-sha256 HEX`` fetches only the archive named in
``ffmpeg.lock.json`` and verifies the bytes, extracted inventory and both tools'
version/configuration before accepting it. Local spikes use the same pinned HTTPS
fetch. See ``tools/package/README.md`` for the spike measurements.

``--notices`` generates the onedir artifact's inventory-backed
``THIRD_PARTY_NOTICES.md`` after the FFmpeg step. Missing material, uncovered
entries or GPL-incompatible bundled FFmpeg components fail the build.

``--smoke`` runs the headless onedir checks after a build; ``--smoke FOLDER``
checks an existing artifact without rebuilding. It requires generated notices.

``--zip`` publishes a deterministic onedir ZIP and LF-terminated sha256 sidecar
under ``--out`` after successful ``--notices --smoke`` and a verified FFmpeg bundle.
Metadata uses the checked-out source commit's UTC time, rounded down to the ZIP
format's two-second precision.
"""

from __future__ import annotations

import argparse
import ast
import base64
import hashlib
import importlib
import importlib.metadata
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import sysconfig
import time
import urllib.error
import urllib.request
import zipfile
from collections.abc import Iterable, Iterator, Sequence
from datetime import UTC, datetime
from http.client import HTTPMessage
from pathlib import Path
from typing import IO, Literal, NamedTuple, Protocol, TypedDict, cast
from urllib.parse import urlsplit

_TEST_ALLOW_FILE_URLS = False
_FFMPEG_REDIRECT_HOSTS = frozenset(
    {"github.com", "objects.githubusercontent.com", "release-assets.githubusercontent.com"}
)

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
    "cupy-cuda",
    "cuda-pathfinder",
    "cuda-toolkit",
    "nvidia-",
    "fastrlock",
)
"""PEP 503-normalized prefixes of GPU distribution metadata / data folders to exclude."""

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
        "--disable-windowed-traceback",
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
        if part.endswith((".dist-info", ".egg-info", ".data")):
            normalized = re.sub(r"[-_.]+", "-", part.rsplit(".", 1)[0])
            if normalized.startswith(FORBIDDEN_DIST_INFO_PREFIXES):
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
    options: list[str]

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
    # CArchiveReader separates runtime options from the TOC; each still meets the name rules.
    for option in package.options:
        parts = split_name(option)
        label = f"pkg:{'/'.join(parts)}"
        found += [f"{label} ({rule})" for rule in name_violations(parts, module_root=False)]
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
        if typecode == readers.PKG_ITEM_PYSOURCE:
            # The entry script and the run-time hooks: no allowlist,
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
    if sys.platform == "win32":
        suffix = ".exe"
    else:
        suffix = ""
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


class FFmpegSource(TypedDict):
    """An additional pinned repository, including whether this variant builds it."""

    repository: str
    pin: str
    pin_kind: str
    status: str
    licence: str
    licence_basis: str
    gpl3_compatible: str
    licence_note: str


class FFmpegComponent(TypedDict):
    """One source-pinned build stage; multiple configure flags belong to one stage."""

    stage: str
    name: str
    repository: str
    pin: str
    pin_kind: str
    extra_repositories: list[FFmpegSource]
    configure_flag: list[str] | None
    licence: str
    licence_basis: str
    gpl3_compatible: str
    licence_note: str


class FFmpegExcluded(TypedDict):
    """An unbuilt or source-free stage, retained to explain source-table omissions."""

    stage: str
    status: str
    reason: str


class FFmpegParentProvider(TypedDict):
    """The upstream build-script repository and its full pinned commit."""

    repository: str
    commit: str


class FFmpegGCC(TypedDict):
    """The measured compiler version, crosstool build and source commit."""

    version: str
    build: str
    commit: str


class FFmpegRustc(TypedDict):
    """The Rust compiler identity measured from the published asset and run."""

    version: str
    commit: str


class FFmpegToolchain(TypedDict):
    """Recorded toolchains and static-link flags of this asset, not future builds."""

    gcc: FFmpegGCC
    rustc: FFmpegRustc
    static_link_flags: list[str]


class FFmpegRuntimeText(TypedDict):
    """A filename and byte hash in the dedicated FFmpeg runtime text directory."""

    path: str
    sha256: str


class FFmpegRuntime(TypedDict):
    """A census-bound static runtime or crate with its source and notice evidence."""

    name: str
    version: str
    kind: str
    reached_via: str
    repository: str
    pin: str
    pin_kind: str
    source_url: str
    licence: str
    licence_basis: str
    gpl3_compatible: str
    licence_note: str
    texts: list[FFmpegRuntimeText]
    evidence: str
    basis: str
    basis_note: str
    chosen: str | None


class FFmpegLock(TypedDict):
    """The verified archive identity and per-stage corresponding-source record."""

    schema_version: int
    provider: str
    parent_provider: FFmpegParentProvider
    release_tag: str
    build_repository_commit: str
    asset_name: str
    asset_url: str
    size_bytes: int
    github_sha256: str
    seat_sha256: str
    ffmpeg_commit: str
    ffmpeg_ref: str
    ffmpeg_repository: str
    version: str
    configure_line: str
    licence: str
    archive_root: str
    extract_members: list[str]
    source_record_url: str
    retention_note: str
    components: list[FFmpegComponent]
    excluded: list[FFmpegExcluded]
    toolchain: FFmpegToolchain
    toolchain_runtime: list[FFmpegRuntime]


FFMPEG_LOCK_PATH = Path(__file__).with_name("ffmpeg.lock.json")
"""The release pin; local PATH copies never substitute for this record."""


FFMPEG_COMPATIBLE_LICENCES = frozenset(
    {
        "MIT",
        "Apache-2.0",
        "Apache-2.0 WITH LLVM-exception",
        "BSD-2-Clause",
        "BSD-3-Clause",
        "0BSD",
        "Zlib",
        "ISC",
        "Unicode-DFS-2016",
        "Unicode-3.0",
        "MPL-2.0",
        "CC0-1.0",
        "Unlicense",
        "BSL-1.0",
        "GPL-3.0-or-later WITH GCC-exception-3.1",
    }
)
"""CHARC's complete GPL-3.0-compatible runtime atom list; unknown atoms refuse."""


def _ffmpeg_licence_choices(expression: str) -> set[str]:
    # Recursive descent preserves SPDX precedence: WITH, AND, then OR. Unknown
    # atoms refuse even in an OR branch; a recorded alternative is never guessed.
    tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9.+-]*|[()]", expression)
    position = 0
    choices: set[str] = set()
    refusal = "FFmpeg lock: incompatible/invalid runtime licence expression"
    if not tokens or "".join(tokens) != re.sub(r"\s+", "", expression):
        raise ValueError(refusal)

    def primary() -> tuple[bool, str]:
        nonlocal position
        if position >= len(tokens):
            raise ValueError(refusal)
        token = tokens[position]
        position += 1
        if token == "(":
            compatible, label = either()
            if position >= len(tokens) or tokens[position] != ")":
                raise ValueError(refusal)
            position += 1
            return compatible, "(" + label + ")"
        if token in {"AND", "OR", "WITH", ")"}:
            raise ValueError(refusal)
        if position < len(tokens) and tokens[position] == "WITH":
            position += 1
            if position >= len(tokens):
                raise ValueError(refusal)
            token += " WITH " + tokens[position]
            position += 1
        if token not in FFMPEG_COMPATIBLE_LICENCES:
            raise ValueError(refusal)
        return True, token

    def both() -> tuple[bool, str]:
        nonlocal position
        compatible, label = primary()
        while position < len(tokens) and tokens[position] == "AND":
            position += 1
            other, right = primary()
            compatible = compatible and other
            label += " AND " + right
        return compatible, label

    def either() -> tuple[bool, str]:
        nonlocal position
        compatible, label = both()
        alternatives = [label]
        while position < len(tokens) and tokens[position] == "OR":
            position += 1
            other, right = both()
            compatible = compatible or other
            alternatives.append(right)
        if len(alternatives) > 1:
            choices.update(alternatives)
        return compatible, " OR ".join(alternatives)

    compatible, _ = either()
    if position != len(tokens) or not compatible:
        raise ValueError(refusal)
    return choices


def _ffmpeg_runtime(data: dict[str, object], config: str) -> None:
    toolchain = _ffmpeg_fields(data["toolchain"], set(FFmpegToolchain.__annotations__), "toolchain")
    for key, fields in (("gcc", FFmpegGCC.__annotations__), ("rustc", FFmpegRustc.__annotations__)):
        compiler = _ffmpeg_fields(toolchain[key], set(fields), f"toolchain {key}")
        for field in fields:
            text = _ffmpeg_text(compiler[field], f"toolchain {key} {field}")
            if field == "commit" and not re.fullmatch(r"[0-9a-f]{40}", text):
                raise ValueError(f"FFmpeg lock: invalid toolchain {key} commit")
    flags = toolchain["static_link_flags"]
    if (
        not isinstance(flags, list)
        or any(
            not isinstance(flag, str)
            or flag not in {"-static-libgcc", "-static-libstdc++", "-lgomp"}
            for flag in flags
        )
        or len(set(flags)) != len(flags)
    ):
        raise ValueError("FFmpeg lock: invalid static_link_flags")
    rows = data["toolchain_runtime"]
    if not isinstance(rows, list):
        raise ValueError("FFmpeg lock: toolchain_runtime must be a list")
    seen: set[tuple[str, str, str]] = set()
    checked: list[FFmpegRuntime] = []
    for item in rows:
        row = _ffmpeg_fields(item, set(FFmpegRuntime.__annotations__), "toolchain runtime")
        for key in set(FFmpegRuntime.__annotations__) - {"texts", "chosen", "licence_note"}:
            _ffmpeg_text(row[key], f"runtime {key}")
        note = row["licence_note"]
        if not isinstance(note, str) or any(c in note for c in "\r\n\x00"):
            raise ValueError("FFmpeg lock: invalid runtime licence_note")
        if row["kind"] not in {"rust-std", "cargo-crate", "gcc-runtime", "mingw-runtime"}:
            raise ValueError("FFmpeg lock: invalid runtime kind")
        if row["reached_via"] not in {"rav1e", "librsvg", "toolchain"}:
            raise ValueError("FFmpeg lock: invalid runtime reached_via")
        if row["pin_kind"] not in {"crate-sha256", "commit"}:
            raise ValueError("FFmpeg lock: invalid runtime pin_kind")
        length = 64 if row["pin_kind"] == "crate-sha256" else 40
        if re.fullmatch(r"[0-9a-f]{" + str(length) + "}", cast(str, row["pin"])) is None:
            raise ValueError("FFmpeg lock: invalid runtime pin")
        if row["basis"] not in {"compile-log", "lock-graph", "binary"}:
            raise ValueError("FFmpeg lock: invalid runtime basis")
        if row["gpl3_compatible"] != "yes":
            raise ValueError("FFmpeg lock: runtime gpl3_compatible must be yes")
        choices = _ffmpeg_licence_choices(cast(str, row["licence"]))
        if row["chosen"] is not None and (
            not isinstance(row["chosen"], str) or row["chosen"] not in choices
        ):
            raise ValueError("FFmpeg lock: invalid runtime chosen licence")
        identity = tuple(cast(str, row[key]) for key in ("name", "version", "reached_via"))
        triple = (identity[0], identity[1], identity[2])
        if triple in seen:
            raise ValueError("FFmpeg lock: duplicate toolchain runtime")
        seen.add(triple)
        if row["kind"] == "cargo-crate":
            if row["pin_kind"] != "crate-sha256":
                raise ValueError("FFmpeg lock: cargo-crate requires crate-sha256")
            if (
                row["source_url"]
                != f"https://static.crates.io/crates/{row['name']}/{row['name']}-{row['version']}.crate"
            ):
                raise ValueError("FFmpeg lock: cargo-crate source_url differs")
        rustc = cast(dict[str, str], toolchain["rustc"])
        gcc = cast(dict[str, str], toolchain["gcc"])
        if row["kind"] == "rust-std":
            if (
                row["repository"] == "https://github.com/rust-lang/rust"
                and row["pin"] != rustc["commit"]
            ):
                raise ValueError("FFmpeg lock: rust-std pin differs from toolchain")
            if row["name"] == "rust-std" and row["version"] != rustc["version"]:
                raise ValueError("FFmpeg lock: rust-std version differs from toolchain")
        if row["kind"] == "gcc-runtime" and (
            row["version"] != gcc["version"] or row["pin"] != gcc["commit"]
        ):
            raise ValueError("FFmpeg lock: gcc-runtime pin/version differs from toolchain")
        texts = row["texts"]
        if not isinstance(texts, list) or not texts:
            raise ValueError("FFmpeg lock: runtime texts must be nonempty")
        for item in texts:
            text_record = _ffmpeg_fields(
                item, set(FFmpegRuntimeText.__annotations__), "runtime text"
            )
            path = _ffmpeg_text(text_record["path"], "runtime text path")
            if any(c in path for c in ("/", "\\", ":", "..")) or path == ".":
                raise ValueError("FFmpeg lock: unsafe runtime text path")
            if (
                re.fullmatch(
                    r"[0-9a-f]{64}", _ffmpeg_text(text_record["sha256"], "runtime text sha256")
                )
                is None
            ):
                raise ValueError("FFmpeg lock: invalid runtime text sha256")
        checked.append(cast(FFmpegRuntime, row))
    for stage, switch in (("rav1e", "--enable-librav1e"), ("librsvg", "--enable-librsvg")):
        enabled = switch in config.split()
        stage_rows = [r for r in checked if r["reached_via"] == stage]
        if enabled and not (
            any(r["kind"] == "cargo-crate" for r in stage_rows)
            and any(r["kind"] == "rust-std" for r in checked)
        ):
            raise ValueError(f"FFmpeg lock: {stage} requires cargo-crate and rust-std")
        if stage_rows and not enabled:
            raise ValueError(f"FFmpeg lock: runtime stage {stage} is not enabled")
    for flag, name in (
        ("-static-libgcc", "libgcc"),
        ("-static-libstdc++", "libstdc++"),
        ("-lgomp", "libgomp"),
    ):
        if (flag in flags or (flag == "-lgomp" and flag in config)) and not any(
            r["name"] == name and r["kind"] == "gcc-runtime" for r in checked
        ):
            raise ValueError(f"FFmpeg lock: static flags require gcc-runtime {name}")


def _ffmpeg_fields(value: object, fields: set[str], context: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"FFmpeg lock: invalid {context} fields")
    return cast(dict[str, object], value)


def _ffmpeg_text(value: object, context: str) -> str:
    if not isinstance(value, str) or not value or any(c in value for c in "\r\n\x00"):
        raise ValueError(f"FFmpeg lock: invalid {context}")
    return value


def _ffmpeg_source(value: dict[str, object]) -> None:
    repository = _ffmpeg_text(value["repository"], "source repository")
    if not repository.startswith("https://"):
        raise ValueError("FFmpeg lock: source repository must use HTTPS")
    pin = _ffmpeg_text(value["pin"], "source pin")
    kind = value["pin_kind"]
    if not isinstance(kind, str) or kind not in {"commit", "tag", "svn-rev"}:
        raise ValueError("FFmpeg lock: invalid source pin kind")
    if kind == "commit" and not re.fullmatch(r"[0-9a-f]{40}", pin):
        raise ValueError("FFmpeg lock: invalid source commit")
    if kind == "svn-rev" and not re.fullmatch(r"[0-9]+", pin):
        raise ValueError("FFmpeg lock: invalid svn revision")
    licence = _ffmpeg_text(value["licence"], "licence")
    if licence == "UNVERIFIED" or value["licence_basis"] != "seat-verified":
        raise ValueError("FFmpeg lock: every licence must be seat-verified")
    compatible = value["gpl3_compatible"]
    if not isinstance(compatible, str) or compatible not in {"yes", "no"}:
        raise ValueError("FFmpeg lock: gpl3_compatible must be yes or no")
    _ffmpeg_text(value["licence_note"], "licence note")


def validate_ffmpeg_lock(value: object) -> FFmpegLock:
    """Validate archive identity, source rows and two-way configure-flag coverage.

    Stage licence identities must be seat-verified. Stage incompatibility remains
    data: a "no" row is accepted here and refused by artifact notices when bundled.
    Static runtime rows require compatible SPDX expressions, toolchain/source
    bindings and nonempty text identities. This validator is pure; notices checks
    runtime text files and their hashes at planning and again at rendering.
    ``configure_flag`` is null for dependencies or a list, since some stages
    contribute several switches (for example both opencore-amr codecs).

    Args:
        value: The decoded lock document.

    Returns:
        The same document, with its complete schema validated.

    Raises:
        ValueError: The schema, pin, hashes or configure coverage is inconsistent.
    """
    data = _ffmpeg_fields(value, set(FFmpegLock.__annotations__), "document")
    if type(data["schema_version"]) is not int or data["schema_version"] != 2:
        raise ValueError("FFmpeg lock: unsupported schema_version")
    if type(data["size_bytes"]) is not int or data["size_bytes"] <= 0:
        raise ValueError("FFmpeg lock: invalid size_bytes")
    for key in set(FFmpegLock.__annotations__) - {
        "schema_version",
        "size_bytes",
        "components",
        "excluded",
        "extract_members",
        "parent_provider",
        "toolchain",
        "toolchain_runtime",
    }:
        _ffmpeg_text(data[key], key)
    parent = _ffmpeg_fields(
        data["parent_provider"], set(FFmpegParentProvider.__annotations__), "parent_provider"
    )
    repository = _ffmpeg_text(parent["repository"], "parent repository")
    if repository != "BtbN/FFmpeg-Builds":
        raise ValueError("FFmpeg lock: invalid parent repository")
    if not re.fullmatch(r"[0-9a-f]{40}", _ffmpeg_text(parent["commit"], "parent commit")):
        raise ValueError("FFmpeg lock: invalid parent commit")
    _check_ffmpeg_asset_url(cast(str, data["asset_url"]))
    digest = cast(str, data["github_sha256"])
    if not re.fullmatch(r"[0-9a-f]{64}", digest) or digest != data["seat_sha256"]:
        raise ValueError("FFmpeg lock: sha256 readings differ or are not 64 hex digits")
    if not re.fullmatch(r"[0-9a-f]{40}", cast(str, data["build_repository_commit"])):
        raise ValueError("FFmpeg lock: invalid build repository commit")
    commit = cast(str, data["ffmpeg_commit"])
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("FFmpeg lock: invalid FFmpeg commit")
    if not re.match(r"n9\.", cast(str, data["version"])):
        raise ValueError("FFmpeg lock: FFmpeg major must be 9")
    version_commit = re.fullmatch(
        r"n9\.\d+\.\d+-\d+-g([0-9a-f]{7,40})-\d{8}", cast(str, data["version"])
    )
    if version_commit is None or not commit.startswith(version_commit.group(1)):
        raise ValueError("FFmpeg lock: version hash differs from the FFmpeg commit")
    if data["ffmpeg_ref"] != "release/9.0":
        raise ValueError("FFmpeg lock: FFmpeg ref must be release/9.0")
    if data["licence"] != "GPL-3.0-or-later":
        raise ValueError("FFmpeg lock: combined build must be GPL-3.0-or-later")
    if data["extract_members"] != ["bin/ffmpeg.exe", "bin/ffprobe.exe", "LICENSE.txt"]:
        raise ValueError("FFmpeg lock: extract_members must name only the two tools and licence")
    root = cast(str, data["archive_root"])
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", root) or root in {".", ".."}:
        raise ValueError("FFmpeg lock: invalid archive_root")
    if data["asset_name"] != root + ".zip":
        raise ValueError("FFmpeg lock: asset name must match archive_root")
    asset_url = cast(str, data["asset_url"])
    expected_url = f"https://github.com/{data['provider']}/releases/download/{data['release_tag']}/{data['asset_name']}"
    if asset_url != expected_url and not (
        _TEST_ALLOW_FILE_URLS and urlsplit(asset_url).scheme == "file"
    ):
        raise ValueError("FFmpeg lock: asset URL must match provider/release/asset")
    if (
        data["source_record_url"]
        != f"https://github.com/{data['provider']}/tree/{data['build_repository_commit']}"
    ):
        raise ValueError(
            "FFmpeg lock: source record URL must match provider/build commit tree root"
        )
    if commit[:8] not in cast(str, data["release_tag"]) or cast(
        str, data["build_repository_commit"]
    )[:7] not in cast(str, data["release_tag"]):
        raise ValueError("FFmpeg lock: release tag must name FFmpeg and build commits")
    config = cast(str, data["configure_line"])
    if not config.startswith("configuration: "):
        raise ValueError("FFmpeg lock: configure_line must include its printed prefix")
    tokens = set(config.split()[1:])
    if not {"--enable-gpl", "--enable-version3", "--enable-libx265"} <= tokens:
        raise ValueError("FFmpeg lock: GPL, version3 and libx265 are required")
    if {"--enable-nonfree", "--enable-libfdk-aac"} & tokens:
        raise ValueError("FFmpeg lock: nonfree or libfdk-aac is forbidden")
    if "--disable-libzvbi" not in tokens or "--enable-libzvbi" in tokens:
        raise ValueError("FFmpeg lock: zvbi must be disabled")
    dates = [
        token.removeprefix("--extra-version=")
        for token in config.split()
        if token.startswith("--extra-version=")
    ]
    if dates != [cast(str, data["version"])[-8:]]:
        raise ValueError("FFmpeg lock: version date must match --extra-version")
    components = data["components"]
    excluded = data["excluded"]
    if not isinstance(components, list) or not components or not isinstance(excluded, list):
        raise ValueError("FFmpeg lock: components/excluded must be lists")
    if not any(
        isinstance(row, dict) and row.get("stage") == "scripts.d/50-zvbi.sh" for row in excluded
    ) or any(
        isinstance(row, dict) and row.get("stage") == "scripts.d/50-zvbi.sh" for row in components
    ):
        raise ValueError("FFmpeg lock: zvbi must be present only in excluded")
    stages: set[str] = set()
    names: set[str] = set()
    covered: set[str] = set()
    for item in components:
        component = _ffmpeg_fields(item, set(FFmpegComponent.__annotations__), "component")
        _ffmpeg_source(component)
        stage = _ffmpeg_text(component["stage"], "component stage")
        name = _ffmpeg_text(component["name"], "component name")
        if stage in stages or name in names:
            raise ValueError("FFmpeg lock: duplicate component stage or name")
        stages.add(stage)
        names.add(name)
        flags = component["configure_flag"]
        if flags is not None:
            if not isinstance(flags, list) or not flags:
                raise ValueError("FFmpeg lock: configure_flag must be null or a nonempty list")
            for flag in flags:
                if not isinstance(flag, str) or not re.fullmatch(r"--enable-[a-z0-9-]+", flag):
                    raise ValueError("FFmpeg lock: invalid component configure flag")
                covered.add(flag)
        extras = component["extra_repositories"]
        if not isinstance(extras, list):
            raise ValueError("FFmpeg lock: extra_repositories must be a list")
        for extra in extras:
            source = _ffmpeg_fields(extra, set(FFmpegSource.__annotations__), "extra source")
            _ffmpeg_source(source)
            if not isinstance(source["status"], str) or source["status"] not in {
                "built",
                "downloaded-not-built",
            }:
                raise ValueError("FFmpeg lock: invalid extra source status")
    for item in excluded:
        row = _ffmpeg_fields(item, set(FFmpegExcluded.__annotations__), "excluded stage")
        for key in row:
            _ffmpeg_text(row[key], f"excluded {key}")
        stage = cast(str, row["stage"])
        if stage in stages:
            raise ValueError("FFmpeg lock: duplicate or built excluded stage")
        stages.add(stage)
    # These three switches select licence/system facilities, not source-pinned libraries.
    enabled = {token for token in tokens if token.startswith("--enable-")}
    external = enabled - {"--enable-gpl", "--enable-version3", "--enable-schannel"}
    if external != covered:
        raise ValueError(
            f"FFmpeg lock: configure coverage differs; unmapped={sorted(external - covered)}, "
            f"absent={sorted(covered - external)}"
        )
    _ffmpeg_runtime(data, config)
    return cast(FFmpegLock, data)


def load_ffmpeg_lock() -> FFmpegLock:
    """Read and validate the committed release pin.

    Returns:
        The verified-schema lock document.

    Raises:
        ValueError: The document is invalid.
        OSError: The document cannot be read.
    """
    return validate_ffmpeg_lock(json.loads(FFMPEG_LOCK_PATH.read_text(encoding="utf-8")))


def _ffmpeg_archive_members(
    archive: zipfile.ZipFile, lock: FFmpegLock
) -> dict[str, zipfile.ZipInfo]:
    seen: set[str] = set()
    found: dict[str, zipfile.ZipInfo] = {}
    wanted = {f"{lock['archive_root']}/{name}": name for name in lock["extract_members"]}
    for info in archive.infolist():
        name = info.orig_filename
        parts = name.rstrip("/").split("/")
        mode = info.external_attr >> 16
        if (
            not name
            or any(c in name for c in "\\:\x00")
            or name.startswith("/")
            or any(p in {"", ".", ".."} or p.endswith((" ", ".")) for p in parts)
            or any(ord(c) < 32 for c in name)
            or stat.S_ISLNK(mode)
            or stat.S_IFMT(mode) not in {0, stat.S_IFREG, stat.S_IFDIR}
        ):
            raise ValueError(f"FFmpeg archive: unsafe member {name!r}")
        normalized = name.rstrip("/").casefold()
        if normalized in seen:
            raise ValueError(f"FFmpeg archive: duplicate member {name!r}")
        seen.add(normalized)
        if name in wanted:
            if info.is_dir() or stat.S_ISDIR(mode):
                raise ValueError(f"FFmpeg archive: missing file (directory at {name!r})")
            found[wanted[name]] = info
    missing = set(lock["extract_members"]) - set(found)
    if missing:
        raise ValueError(f"FFmpeg archive: missing members {sorted(missing)}")
    return found


def _check_ffmpeg_asset_url(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme == "file" and _TEST_ALLOW_FILE_URLS:
        return
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError(f"FFmpeg asset URL must use HTTPS: {url}")


class _FFmpegRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Refuse redirects outside the pinned provider's HTTPS asset hosts."""

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: HTTPMessage,
        newurl: str,
    ) -> urllib.request.Request | None:
        parsed = urlsplit(newurl)
        if (
            parsed.scheme != "https"
            or parsed.hostname not in _FFMPEG_REDIRECT_HOSTS
            or parsed.port not in {None, 443}
            or parsed.username
            or parsed.password
        ):
            raise ValueError(f"FFmpeg redirect refused: {newurl}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _download_ffmpeg(url: str, sha256: str, out: Path, lock: FFmpegLock) -> Path:
    if url != lock["asset_url"]:
        raise ValueError("FFmpeg URL differs from the pinned asset URL")
    _check_ffmpeg_asset_url(url)
    if not re.fullmatch(r"[0-9a-f]{64}", sha256) or sha256 != lock["github_sha256"]:
        raise ValueError("FFmpeg sha256 argument differs from the lock")
    folder = out / "ffmpeg"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / lock["asset_name"]
    partial = target.with_suffix(".zip.part")
    if target.is_symlink() or partial.is_symlink():
        raise ValueError("FFmpeg download: unsafe output link")
    digest = hashlib.sha256()
    size = 0
    start = time.monotonic()
    try:
        opener = urllib.request.build_opener(_FFmpegRedirectHandler())
        with opener.open(url, timeout=60) as response, partial.open("wb") as stream:
            while chunk := response.read(1024 * 1024):
                size += len(chunk)
                if size > lock["size_bytes"]:
                    raise ValueError("FFmpeg download size exceeds lock (sha256 not accepted)")
                if time.monotonic() - start > 600:
                    raise RuntimeError("FFmpeg download exceeded 600 seconds")
                digest.update(chunk)
                stream.write(chunk)
        if digest.hexdigest() != sha256 or digest.hexdigest() != lock["seat_sha256"]:
            raise ValueError("FFmpeg download sha256 mismatch; archive was not opened")
        if size != lock["size_bytes"]:
            raise ValueError("FFmpeg download size differs from lock")
        partial.replace(target)
    finally:
        partial.unlink(missing_ok=True)
    return target


def _pinned_ffmpeg_version(path: Path, lock: FFmpegLock) -> str:
    env = {key: value for key, value in os.environ.items() if key.upper() != "PATH"}
    env["PATH"] = str(path.parent)
    flags = 0
    if sys.platform == "win32":
        flags = subprocess.CREATE_NO_WINDOW
    try:
        done = subprocess.run(
            [str(path), "-version"],
            cwd=path.parent,
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            creationflags=flags,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError(f"{path.name} -version did not run: {error}") from error
    lines = done.stdout.splitlines()
    tool = path.stem
    first = lines[0] if lines else ""
    if done.returncode != 0:
        raise RuntimeError(f"{path.name} -version failed (exit {done.returncode})")
    fields = first.split()
    if len(fields) < 3 or fields[:3] != [tool, "version", lock["version"]]:
        raise RuntimeError(f"{path.name}: version differs from the lock: {first!r}")
    configs = [line for line in lines if line.startswith("configuration:")]
    if configs != [lock["configure_line"]]:
        raise RuntimeError(f"{path.name}: configuration differs from the lock")
    return first


def bundle_ffmpeg(
    destination: Path,
    *,
    out: Path,
    url: str,
    sha256: str,
    verified_hashes: set[str] | None = None,
) -> list[tuple[Path, str]]:
    """Fetch the pinned archive, verify before opening, then copy and check its tools.

    Every archive member is inspected for unsafe paths, links and duplicates,
    including members that will not be extracted. Only the two tools and the
    GPL text are copied. The output contains a build/source provenance record.

    Args:
        destination: The built Clearwater executable's folder.
        out: The build output root; the archive is retained under ``ffmpeg/``.
        url: Must equal the committed lock's asset URL.
        sha256: Must equal both verified hash readings in the lock.
        verified_hashes: Optional in-memory output for extracted tool hashes, read
            from the verified archive streams. Updated only after both tools pass.
            Unextracted members and the non-native licence/build texts grant no trust.

    Returns:
        The two executable paths and their checked version lines.

    Raises:
        ValueError: The pin, download or ZIP inventory is unsafe or inconsistent.
        RuntimeError: Either tool fails its bounded version/configuration check.
        OSError: A download, extraction or provenance write fails.
        zipfile.BadZipFile: The verified bytes are not a valid ZIP.
    """
    lock = load_ffmpeg_lock()
    destination = destination.resolve()
    archive_path = _download_ffmpeg(url, sha256, out.resolve(), lock)
    tool_hashes: set[str] = set()
    with zipfile.ZipFile(archive_path) as archive:
        members = _ffmpeg_archive_members(archive, lock)
        targets = {
            "bin/ffmpeg.exe": destination / "ffmpeg.exe",
            "bin/ffprobe.exe": destination / "ffprobe.exe",
            "LICENSE.txt": destination / "ffmpeg-LICENSE.txt",
        }
        if any(path.is_symlink() for path in targets.values()):
            raise ValueError("FFmpeg extraction: unsafe output link")
        for name, path in targets.items():
            digest = hashlib.sha256()
            with archive.open(members[name]) as source, path.open("wb") as output:
                while chunk := source.read(1024 * 1024):
                    digest.update(chunk)
                    output.write(chunk)
            if name in {"bin/ffmpeg.exe", "bin/ffprobe.exe"}:
                tool_hashes.add(digest.hexdigest())
    provenance = destination / "ffmpeg-BUILD.txt"
    if provenance.is_symlink():
        raise ValueError("FFmpeg build record: unsafe output link")
    provenance.write_text(
        "\n".join(
            [
                f"Provider: {lock['provider']}",
                f"Parent provider: {lock['parent_provider']['repository']} @ "
                f"{lock['parent_provider']['commit']}",
                f"Release tag: {lock['release_tag']}",
                f"Asset: {lock['asset_name']}",
                f"SHA256: {lock['github_sha256']}",
                f"FFmpeg version: {lock['version']}",
                f"FFmpeg commit: {lock['ffmpeg_commit']}",
                f"FFmpeg ref: {lock['ffmpeg_ref']}",
                f"Build repository commit: {lock['build_repository_commit']}",
                f"Per-component source recipes: {lock['source_record_url']}",
                "Per-component pins and licence readings: "
                "tools/package/ffmpeg.lock.json in Clearwater source",
                lock["configure_line"],
                "",
            ]
        ),
        encoding="utf-8",
    )
    result = [
        (path, _pinned_ffmpeg_version(path, lock))
        for path in (destination / "ffmpeg.exe", destination / "ffprobe.exe")
    ]
    if verified_hashes is not None:
        verified_hashes.update(tool_hashes)
    return result


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
    from clearwater.gpu_pack_install import manifest_document as product_manifest_document

    return product_manifest_document(folder)


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
    from clearwater.gpu_pack_install import write_manifest as product_write_manifest

    return product_write_manifest(folder)


def verify_pack(folder: Path) -> list[str]:
    """Return every problem the FULL pack check finds in a pack folder filled by hand.

    The full check is :func:`clearwater.gpu_pack.pack_problems` with ``full=True``: the cheap
    start-up check (the manifest against the lock, each ``RECORD``'s sha256, the ``WHEEL``
    platform tags, every listed file's existence and size, no unlisted top-level entry) plus
    each listed file's sha256 against its ``RECORD`` row and a walk of every file under
    ``site-packages`` that lists each one no ``RECORD`` row names (Q2). Reads only.

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

    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True  # importing clearwater must not write into src (F8)
    try:
        if names is None:
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
                raise ValueError(
                    f"{name}: installed {distribution.version}, the lock has {expected}"
                )
            files = distribution.files
            if files is None:
                raise ValueError(f"{name}: no RECORD")
            for file in files:
                if file.suffix == ".py":
                    rows.append(
                        (f"{name}:{file.as_posix()}", Path(str(distribution.locate_file(file))))
                    )
        return sorted(rows)
    finally:
        sys.dont_write_bytecode = previous


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


class BuildEnvironmentError(ValueError):
    """The analysis environment cannot be constructed safely."""


def run_pyinstaller(args: Sequence[str]) -> None:
    """Run PyInstaller in this process: ``PyInstaller.__main__.run(args)``.

    Windows analysis sees only the interpreter root/DLLs, venv Scripts and
    Windows System32/root. PATH is restored even if importing/running analysis
    fails. POSIX loader paths/rpaths are unchanged; WP6.5 owns their native proof.

    Args:
        args: The command line (:func:`pyinstaller_args`).

    Raises:
        BuildEnvironmentError: Windows SYSTEMROOT is unset; no safe PATH can be formed.
        SystemExit: PyInstaller's own exit on a failed build (non-zero status).
    """
    original = os.environ.get("PATH")
    try:
        if sys.platform == "win32":
            system_root = os.environ.get("SYSTEMROOT")
            if not system_root:
                raise BuildEnvironmentError(
                    "SYSTEMROOT is unset; cannot sanitize the analysis PATH"
                )
            windows = Path(system_root)
            base = Path(sys.base_prefix)
            os.environ["PATH"] = os.pathsep.join(
                str(path)
                for path in (
                    base,
                    base / "DLLs",
                    Path(sys.prefix) / "Scripts",
                    windows / "System32",
                    windows,
                )
            )
        else:
            # POSIX dependency resolution uses loader paths/rpaths; this Windows
            # release fix does not change those. Native macOS proof is WP6.5's.
            pass
        main = importlib.import_module("PyInstaller.__main__")
        main.run(list(args))
    finally:
        if original is None:
            os.environ.pop("PATH", None)
        else:
            os.environ["PATH"] = original


def _is_native(name: str, data: bytes = b"") -> bool:
    return Path(name).suffix.casefold() in {".dll", ".pyd", ".exe", ".so", ".dylib"} or (
        data.startswith((b"MZ", b"\x7fELF"))
        or data[:4]
        in {
            b"\xfe\xed\xfa\xce",
            b"\xce\xfa\xed\xfe",
            b"\xfe\xed\xfa\xcf",
            b"\xcf\xfa\xed\xfe",
            b"\xca\xfe\xba\xbe",
            b"\xbe\xba\xfe\xca",
            b"\xca\xfe\xba\xbf",
            b"\xbf\xba\xfe\xca",
        }
    )


def _locked_native_distributions() -> list[importlib.metadata.Distribution]:
    import tomllib

    lock = tomllib.loads((REPO_ROOT / "uv.lock").read_text(encoding="utf-8"))
    versions: dict[str, set[str]] = {}
    for row in lock["package"]:
        versions.setdefault(re.sub(r"[-_.]+", "-", row["name"]).lower(), set()).add(row["version"])
    return list(trusted_distributions(versions).values())


def check_build_environment() -> None:
    """Refuse Python search overrides before reading build inputs.

    Raises:
        ValueError: A Python environment override is present, including an empty one.
    """
    for name in ("PYTHONPATH", "PYTHONHOME", "PYTHONUSERBASE"):
        if name in os.environ:
            raise ValueError(f"build environment: {name} is set")


def trusted_distributions(
    versions: dict[str, set[str]],
) -> dict[str, importlib.metadata.Distribution]:
    """Resolve locked distributions uniquely inside the build venv only.

    Args:
        versions: Normalized locked names and allowed versions.

    Returns:
        The installed locked distributions from purelib or platlib.

    Raises:
        ValueError: Python overrides, duplicate names, foreign roots or versions exist.
    """
    check_build_environment()
    paths = sysconfig.get_paths()
    roots = {Path(paths[key]).resolve() for key in ("purelib", "platlib")}
    candidates: dict[str, list[importlib.metadata.Distribution]] = {}
    for dist in importlib.metadata.distributions():
        name = re.sub(r"[-_.]+", "-", dist.metadata["Name"]).lower()
        if name in versions:
            candidates.setdefault(name, []).append(dist)
    result = {}
    for name, matches in candidates.items():
        if len(matches) != 1:
            raise ValueError(f"build environment: locked name {name} resolves more than once")
        dist = matches[0]
        if Path(str(dist.locate_file(""))).resolve() not in roots:
            raise ValueError(f"build environment: {name} is outside the build venv purelib/platlib")
        if dist.version not in versions[name]:
            raise ValueError(f"build environment: {name} version differs from uv.lock")
        result[name] = dist
    return result


def _record_native_hash(
    dist: importlib.metadata.Distribution, entry: importlib.metadata.PackagePath
) -> str:
    path = Path(str(dist.locate_file(entry)))
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    recorded = entry.hash
    encoded = base64.urlsafe_b64encode(bytes.fromhex(digest)).decode("ascii").rstrip("=")
    if (
        recorded is None
        or recorded.mode != "sha256"
        or recorded.value != encoded
        or entry.size != path.stat().st_size
    ):
        raise ValueError(f"native origin: installed file differs from locked wheel RECORD: {entry}")
    return digest


def _native_origin_hashes() -> set[str]:
    hashes = set()
    for path in Path(sys.base_prefix).rglob("*"):
        if path.is_file() and _is_native(path.name):
            with path.open("rb") as stream:
                hashes.add(hashlib.file_digest(stream, "sha256").hexdigest())
    for dist in _locked_native_distributions():
        for entry in dist.files or ():
            if _is_native(str(entry)):
                hashes.add(_record_native_hash(dist, entry))
    return hashes


def _locked_bootloader() -> Path:
    pyinstaller = importlib.import_module("PyInstaller")
    if sys.platform == "win32":
        basename = "runw.exe"
    elif sys.platform == "darwin":
        basename = "runw"
    else:
        basename = "run"
    relative = f"PyInstaller/bootloader/{pyinstaller.PLATFORM}/{basename}"
    for dist in _locked_native_distributions():
        if re.sub(r"[-_.]+", "-", dist.metadata["Name"]).lower() != "pyinstaller":
            continue
        for entry in dist.files or ():
            if str(entry).replace("\\", "/") == relative:
                _record_native_hash(dist, entry)
                return Path(str(dist.locate_file(entry)))
    raise ValueError("native origin: windowed bootloader missing from locked PyInstaller RECORD")


def _is_clearwater_bootloader(executable: Path) -> bool:
    # PE resources, timestamps, checksum and appended CArchive change at build
    # time. Compare all non-resource sections (including imports/relocations),
    # their addresses/flags and execution-critical headers; normalize ONLY debug
    # timestamps inside those sections. Resources can move the unchanged .reloc
    # section, so its address may change too. No other executable gets this exception.
    source = _locked_bootloader()
    if sys.platform == "win32":
        pefile = importlib.import_module("pefile")

        def identity(path: Path) -> object:
            with pefile.PE(str(path), fast_load=False) as pe:
                for entry in getattr(pe, "DIRECTORY_ENTRY_DEBUG", []):
                    entry.struct.TimeDateStamp = 0
                data = pe.write()
                sections = []
                for section in pe.sections:
                    if section.Name.rstrip(b"\0") == b".rsrc":
                        # Resource replacement is allowed, executable resources aren't.
                        if section.Characteristics & 0x20000000:
                            return None
                        continue
                    offset = section.PointerToRawData
                    sections.append(
                        (
                            section.Name,
                            0
                            if section.Name.rstrip(b"\0") == b".reloc"
                            else section.VirtualAddress,
                            section.Misc_VirtualSize,
                            section.SizeOfRawData,
                            section.Characteristics,
                            hashlib.sha256(
                                data[offset : offset + section.SizeOfRawData]
                            ).hexdigest(),
                        )
                    )
                headers = (
                    pe.FILE_HEADER.Machine,
                    pe.FILE_HEADER.Characteristics,
                    pe.OPTIONAL_HEADER.AddressOfEntryPoint,
                    pe.OPTIONAL_HEADER.ImageBase,
                    pe.OPTIONAL_HEADER.Subsystem,
                    pe.OPTIONAL_HEADER.DllCharacteristics,
                )
                directories = [
                    (i, 0 if i == 5 else item.VirtualAddress, item.Size)
                    for i, item in enumerate(pe.OPTIONAL_HEADER.DATA_DIRECTORY)
                    if i not in {2, 4}  # resource and certificate directories
                ]
                return headers, directories, sections

        try:
            expected = identity(source)
            return expected is not None and identity(executable) == expected
        except (ValueError, pefile.PEFormatError):
            return False
    else:
        # Refuse transformed Mach-O/ELF builds until WP6.5 proves their native
        # identity rule. A byte-identical bootloader prefix is accepted here.
        return executable.read_bytes().startswith(source.read_bytes())


def native_origin_violations(
    executable: Path, *, original_path: str, ffmpeg_hashes: Iterable[str] = ()
) -> list[str]:
    """Check every native against interpreter/locked RECORD bytes and the bootloader.

    The main Windows executable is compared to the RECORD-verified runw.exe's
    immutable PE sections, allowing resources, debug timestamps and an appended
    archive. Every other native must match a complete file hash. ZIPs (including
    nested ZIPs and CArchive members) are inspected without executing contents.
    Extracted FFmpeg tools additionally match hashes supplied in memory by the
    verified archive reader. Names and on-disk build records grant no exemption.

    Args:
        executable: Built Clearwater executable, whose folder is inventoried.
        original_path: Caller PATH before analysis, used only for diagnostics.
        ffmpeg_hashes: Trusted extracted tool identities from ``bundle_ffmpeg``;
            never hashes calculated from destination files or provenance texts.

    Returns:
        Named violations, with the first same-named original-PATH file if found.

    Raises:
        ValueError: A locked installed native differs from its RECORD.
        OSError: An input cannot be read.
        zipfile.BadZipFile: An archive is corrupt.
    """
    hashes = _native_origin_hashes() | set(ffmpeg_hashes)
    errors = []

    def inspect(label: str, name: str, data: bytes) -> None:
        if _is_native(name, data) and hashlib.sha256(data).hexdigest() not in hashes:
            likely = next(
                (
                    Path(part) / Path(name).name
                    for part in original_path.split(os.pathsep)
                    if part and (Path(part) / Path(name).name).is_file()
                ),
                None,
            )
            suffix = f"; likely PATH source: {likely}" if likely else ""
            errors.append(f"native origin unknown: {label}{suffix}")
        if name.lower().endswith(".zip") or data.startswith(b"PK\x03\x04"):
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                for member in archive.infolist():
                    if not member.is_dir():
                        inspect(
                            label + "!" + member.filename, member.filename, archive.read(member)
                        )

    if not _is_clearwater_bootloader(executable):
        errors.append(
            f"native origin: {executable.name} differs from locked PyInstaller bootloader"
        )
    for path in sorted(executable.parent.rglob("*")):
        if path.is_symlink():
            errors.append(f"native origin: linked file {path}")
        elif path.is_file() and path != executable:
            inspect(path.relative_to(executable.parent).as_posix(), path.name, path.read_bytes())
    package = read_package(executable)
    for name, entry in package.toc.items():
        if entry[-1] not in {"o", "z"}:
            inspect("pkg:" + name, name, package.extract(name))
    return errors


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
    as previously bundled FFmpeg) survives into the new one.

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


def write_artifact_notices(folder: Path) -> Path:
    """Generate the onedir artifact's inventory-backed notices after bundling FFmpeg.

    Args:
        folder: The folder containing the built executable and its dependencies.

    Returns:
        The generated artifact notices path.

    Raises:
        ValueError: Inventory, source provenance or licence materials are invalid.
        OSError: Inputs or the output cannot be read or written.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_clearwater_artifact_notices", Path(__file__).with_name("notices.py")
    )
    if spec is None or spec.loader is None:
        raise ValueError("cannot load the artifact notices generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return cast(Path, module.write_notices(folder))


def smoke_artifact(folder: Path, *, out: Path) -> int:
    """Run headless smoke checks and report a named failure as a non-zero status.

    Args:
        folder: The Windows onedir artifact or its parent wrapper.
        out: The evidence root, with disposable profiles under ``smoke/``.

    Returns:
        Zero on success, one on failed checks or unavailable inputs.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_clearwater_artifact_smoke", Path(__file__).with_name("smoke.py")
    )
    if spec is None or spec.loader is None:
        print("FAILED: smoke: cannot load headless checks")
        return 1
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        module.run_smoke(folder, out=out)
    except (OSError, RuntimeError, ValueError, KeyError, zipfile.BadZipFile) as error:
        message = " ".join(str(error).split()).encode("ascii", "backslashreplace").decode("ascii")
        print(f"FAILED: smoke: {message}")
        return 1
    return 0


def source_commit_epoch() -> int:
    """Read the checked-out source commit's UTC Unix time with a bounded Git query.

    Returns:
        The commit timestamp as whole seconds since the Unix epoch.

    Raises:
        ValueError: Git fails, times out or returns an invalid timestamp.
    """
    flags = 0
    if sys.platform == "win32":
        flags = subprocess.CREATE_NO_WINDOW
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "HEAD"],
            cwd=REPO_ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="ascii",
            timeout=20,
            check=True,
            creationflags=flags,
        )
        if not re.fullmatch(r"[0-9]+", result.stdout.strip()):
            raise ValueError("invalid commit timestamp")
        return int(result.stdout.strip())
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        raise ValueError(f"cannot read source commit time: {error}") from error


def _release_files(folder: Path) -> list[Path]:
    if folder.is_symlink() or folder.is_junction() or not folder.is_dir():
        raise ValueError("release ZIP requires a physical release folder without junctions")
    resolved = folder.resolve()
    pending = [folder]
    files = []
    while pending:
        for path in pending.pop().iterdir():
            if (
                path.is_symlink()
                or path.is_junction()
                or not path.resolve().is_relative_to(resolved)
            ):
                raise ValueError(
                    "release ZIP refuses linked/junction/outside member: "
                    f"{path.relative_to(folder)}"
                )
            if path.is_dir():
                pending.append(path)
            elif path.is_file():
                files.append(path)
            else:
                raise ValueError(f"release ZIP refuses special file: {path.relative_to(folder)}")
    return sorted(files, key=lambda path: path.relative_to(folder).as_posix())


def _release_snapshot(folder: Path) -> dict[str, tuple[str, int]]:
    snapshot = {}
    for path in _release_files(folder):
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        snapshot[path.relative_to(folder).as_posix()] = (digest, path.stat().st_size)
    return snapshot


def _check_release_snapshot(folder: Path, expected: dict[str, tuple[str, int]]) -> None:
    actual = _release_snapshot(folder)
    for name in sorted(expected.keys() | actual.keys()):
        if name not in expected:
            change = "added"
        elif name not in actual:
            change = "removed"
        elif actual[name] != expected[name]:
            change = "changed"
        else:
            continue
        raise ValueError(f"release folder {change} after pre-smoke snapshot: {name}")


def write_release_zip(folder: Path, *, out: Path, source_epoch: int) -> Path:
    """Archive a release wrapper with sorted files and fixed source-commit metadata.

    Only file members are emitted, under the wrapper's single top-level folder.
    Every member has a UTC DOS timestamp (two-second precision), Unix regular-file
    mode 0644 and no extra/comment metadata. File mtimes and modes are ignored.

    Args:
        folder: The onedir release wrapper, containing ``Clearwater/``.
        out: Output root for ``<folder name>.zip`` and its sha256 sidecar.
        source_epoch: Source/tag commit time in Unix seconds; explicit for testing.

    Returns:
        The ZIP path. Its ``.zip.sha256`` sidecar ends with LF.

    Raises:
        ValueError: The date is outside ZIP's range or the tree/output is unsafe.
        OSError: A file cannot be read or the output cannot be written.
    """
    # Check bounds before datetime conversion (including on Windows).
    if not 315532800 <= source_epoch < 4354819200:
        raise ValueError("ZIP date must be in 1980..2107 UTC")
    stamp = datetime.fromtimestamp(source_epoch, UTC)
    date_time = (
        stamp.year,
        stamp.month,
        stamp.day,
        stamp.hour,
        stamp.minute,
        stamp.second // 2 * 2,
    )
    files = _release_files(folder)
    if not files:
        raise ValueError("release ZIP requires a nonempty release folder")
    target = out / (folder.name + ".zip")
    sidecar = target.with_suffix(".zip.sha256")
    partial = target.with_suffix(".zip.part")
    partial_sidecar = sidecar.with_suffix(".sha256.part")
    outputs = (target, sidecar, partial, partial_sidecar)
    if any(
        path.is_symlink() or path.resolve().is_relative_to(folder.resolve()) for path in outputs
    ):
        raise ValueError("release ZIP output must be outside the release folder without links")
    out.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(partial, "w") as archive:
            for path in files:
                member = folder.name + "/" + path.relative_to(folder).as_posix()
                info = zipfile.ZipInfo(member, date_time=date_time)
                info.create_system = 3
                info.create_version = info.extract_version = 20
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                info.internal_attr = 0
                info.extra = info.comment = b""
                archive.writestr(
                    info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9
                )
        with partial.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        partial_sidecar.write_bytes(f"{digest}  {target.name}\n".encode("ascii"))
        partial.replace(target)
        partial_sidecar.replace(sidecar)
    finally:
        partial.unlink(missing_ok=True)
        partial_sidecar.unlink(missing_ok=True)
    return target


def build(
    form: Form,
    *,
    out: Path,
    ffmpeg_from: str | None = None,
    ffmpeg_sha256: str | None = None,
    notices: bool = False,
    smoke: bool = False,
    zip_release: bool = False,
) -> int:
    """Build one form, check it, and print its summary.

    PyInstaller's cache is kept under ``out`` (``PYINSTALLER_CONFIG_DIR``), so ``--clean``
    touches nothing outside the output folder, and the release folder is emptied first.

    Args:
        form: The PyInstaller form.
        out: The output folder.
        ffmpeg_from: The pinned archive URL for a release bundle.
        ffmpeg_sha256: Its verified sha256, also checked against the lock.
        notices: Generate the onedir artifact notices after the FFmpeg step.
        smoke: Run headless checks after notices, failing the build on a bad row.
        zip_release: Publish the onedir zip/sidecar only after notices and smoke pass.

    Returns:
        0 when the build succeeded and the bundle holds nothing forbidden, else 1.
    """
    try:
        if zip_release:
            target = out / (release_dir(out, form, app_version()).name + ".zip")
            for path in (target, target.with_suffix(".zip.sha256")):
                if not path.resolve().is_relative_to(out.resolve()):
                    raise ValueError("release ZIP cleanup must stay inside --out")
                path.unlink(missing_ok=True)
        check_build_environment()
    except (OSError, ValueError) as error:
        print(f"FAILED: {error}")
        return 1
    if (notices or smoke or zip_release) and form != "onedir":
        print("FAILED: --notices/--smoke/--zip require --form onedir")
        return 1
    if zip_release and not (notices and smoke):
        print("FAILED: --zip requires --notices and --smoke")
        return 1
    if zip_release and (ffmpeg_from is None or ffmpeg_sha256 is None):
        print("FAILED: --zip requires --ffmpeg-from and --ffmpeg-sha256")
        return 1
    if (ffmpeg_from is None) != (ffmpeg_sha256 is None):
        print("FAILED: --ffmpeg-from and --ffmpeg-sha256 must be provided together")
        return 1
    if ffmpeg_from is not None:
        try:
            lock = load_ffmpeg_lock()
            if ffmpeg_from != lock["asset_url"] or ffmpeg_sha256 != lock["github_sha256"]:
                raise ValueError("FFmpeg URL/sha256 differ from the lock")
        except (OSError, ValueError) as error:
            print(f"FAILED: {error}")
            return 1
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
    original_path = os.environ.get("PATH", "")
    try:
        run_pyinstaller(args)
    except BuildEnvironmentError as error:
        print(f"FAILED: PyInstaller: {error}".encode("ascii", "backslashreplace").decode("ascii"))
        return 1
    wall = time.monotonic() - start
    executable = find_executable(root)
    ffmpeg_hashes: set[str] = set()
    if ffmpeg_from is not None and ffmpeg_sha256 is not None:
        try:
            for path, line in bundle_ffmpeg(
                executable.parent,
                out=out,
                url=ffmpeg_from,
                sha256=ffmpeg_sha256,
                verified_hashes=ffmpeg_hashes,
            ):
                print(f"bundled {path}: {line}")
        except (
            OSError,
            ValueError,
            RuntimeError,
            zipfile.BadZipFile,
            urllib.error.URLError,
        ) as error:
            print(f"FAILED: FFmpeg bundle: {error}")
            return 1
    try:
        origin_errors = native_origin_violations(
            executable, original_path=original_path, ffmpeg_hashes=ffmpeg_hashes
        )
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print(f"FAILED: native origin: {error}".encode("ascii", "backslashreplace").decode("ascii"))
        return 1
    if origin_errors:
        for error_line in origin_errors:
            print(f"FAILED: {error_line}".encode("ascii", "backslashreplace").decode("ascii"))
        return 1
    print(
        "native origin check: PASS (interpreter, locked wheel RECORDs, "
        "verified FFmpeg and bootloader)"
    )
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
    if notices:
        try:
            print(f"wrote {write_artifact_notices(executable.parent)}")
        except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
            message = (
                " ".join(str(error).split()).encode("ascii", "backslashreplace").decode("ascii")
            )
            print(f"FAILED: artifact notices: {message}")
            return 1
    snapshot = None
    if zip_release:
        try:
            snapshot = _release_snapshot(root)
        except (OSError, ValueError) as error:
            print(f"FAILED: release zip: {error}")
            return 1
    if smoke:
        status = smoke_artifact(executable.parent, out=out)
        if status:
            return status
    if zip_release:
        try:
            assert snapshot is not None
            _check_release_snapshot(root, snapshot)
            print(f"wrote {write_release_zip(root, out=out, source_epoch=source_commit_epoch())}")
        except (OSError, ValueError, zipfile.BadZipFile, zipfile.LargeZipFile) as error:
            message = (
                " ".join(str(error).split()).encode("ascii", "backslashreplace").decode("ascii")
            )
            print(f"FAILED: release zip: {message}")
            return 1
    return 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse the command line.

    Args:
        argv: The arguments; ``sys.argv[1:]`` when None.

    Returns:
        The parsed namespace, including the paired release FFmpeg URL/hash options.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--form", choices=FORMS)
    action.add_argument("--write-manifest", type=Path, metavar="PACK_FOLDER")
    action.add_argument("--verify", type=Path, metavar="PACK_FOLDER")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--notices", action="store_true", help="generate onedir artifact notices")
    parser.add_argument(
        "--zip", dest="zip_release", action="store_true", help="zip a checked onedir release"
    )
    parser.add_argument(
        "--smoke",
        nargs="?",
        const=True,
        type=Path,
        metavar="FOLDER",
        help="headless checks after build, or check an existing folder without a build",
    )
    parser.add_argument("--ffmpeg-from", metavar="URL", help="fetch the pinned release archive")
    parser.add_argument("--ffmpeg-sha256", metavar="HEX", help="the lock's verified archive sha256")
    options = parser.parse_args(argv)
    standalone_smoke = isinstance(options.smoke, Path)
    if standalone_smoke and any(
        value is not None for value in (options.form, options.write_manifest, options.verify)
    ):
        parser.error("--smoke FOLDER cannot be combined with another action")
    if options.smoke is True and options.form != "onedir":
        parser.error("--smoke without FOLDER requires --form onedir")
    if not standalone_smoke and all(
        value is None for value in (options.form, options.write_manifest, options.verify)
    ):
        parser.error("choose --form, --write-manifest, --verify or --smoke FOLDER")
    if options.notices and options.form != "onedir":
        parser.error("--notices requires --form onedir")
    if options.zip_release and options.form != "onedir":
        parser.error("--zip requires --form onedir")
    if options.zip_release and not (options.notices and options.smoke is True):
        parser.error("--zip requires --notices and --smoke")
    if options.zip_release and (options.ffmpeg_from is None or options.ffmpeg_sha256 is None):
        parser.error("--zip requires --ffmpeg-from and --ffmpeg-sha256")
    if (options.ffmpeg_from is None) != (options.ffmpeg_sha256 is None):
        parser.error("--ffmpeg-from and --ffmpeg-sha256 must be provided together")
    if options.ffmpeg_from is not None:
        parsed = urlsplit(options.ffmpeg_from)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            parser.error("--ffmpeg-from requires an HTTPS URL")
    if options.ffmpeg_sha256 is not None and not re.fullmatch(
        r"[0-9a-f]{64}", options.ffmpeg_sha256
    ):
        parser.error("--ffmpeg-sha256 must be 64 lowercase hex digits")
    if options.form is None and options.ffmpeg_from is not None:
        parser.error("FFmpeg options require --form")
    return options


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
    if isinstance(options.smoke, Path):
        return smoke_artifact(Path(os.path.abspath(options.smoke)), out=out)
    return build(
        cast(Form, options.form),
        out=out,
        ffmpeg_from=options.ffmpeg_from,
        ffmpeg_sha256=options.ffmpeg_sha256,
        notices=options.notices,
        smoke=options.smoke is True,
        zip_release=options.zip_release,
    )


if __name__ == "__main__":
    raise SystemExit(main())
