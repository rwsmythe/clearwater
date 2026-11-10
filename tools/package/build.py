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
``ffmpeg.lock.json`` (on macOS ``ffmpeg-macos.lock.json``, WP6.5) and verifies the
bytes, extracted inventory and both tools' version/configuration before accepting it
(on macOS read from the tools' bytes, then placed into the ``.app``). Local spikes use
the same pinned HTTPS fetch. See ``tools/package/README.md`` for the spike measurements.

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
import functools
import hashlib
import importlib
import importlib.metadata
import io
import json
import os
import re
import shutil
import stat
import struct
import subprocess
import sys
import sysconfig
import time
import urllib.error
import urllib.request
import zipfile
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from datetime import UTC, datetime
from http.client import HTTPMessage
from pathlib import Path, PurePosixPath
from typing import IO, Literal, NamedTuple, NotRequired, Protocol, TypedDict, cast, overload
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

MACOS_APP = f"{APP_NAME}.app"
"""The macOS release item: PyInstaller's BUNDLE, the one top-level entry of the macOS zip."""

MACOS_CODESIGN = "/usr/bin/codesign"
"""Apple's signing tool, by absolute path (as PyInstaller's ``utils/osx.py`` runs it)."""
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


def release_zip_name(form: Form, version: str, platform: str | None = None) -> str:
    """Return the release ZIP's stem (without ``.zip``).

    Args:
        form: The PyInstaller form.
        version: The application version.
        platform: A ``sys.platform`` value; the running one when None.

    Returns:
        Windows: the release folder's name (``Clearwater-<version>-windows-onedir``,
        unchanged). macOS: ``Clearwater-<version>-macos``, whose ONE top-level item is
        ``Clearwater.app`` (WP6.5, owner "2. app").
    """
    kind = sys.platform if platform is None else platform
    if kind == "darwin":
        return f"{APP_NAME}-{version}-{platform_tag(kind)}"
    else:
        return release_name(form, version, kind)


def release_zip_folder(root: Path) -> Path:
    """Return the folder the release ZIP packs: the wrapper on Windows, the ``.app`` on macOS.

    Args:
        root: The release folder (:func:`release_dir`).

    Returns:
        ``root`` on Windows; ``root / "Clearwater.app"`` on macOS.
    """
    if sys.platform == "darwin":
        return root / MACOS_APP
    else:
        return root


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
        candidates: tuple[Path, ...] = ()
    else:
        suffix = ""
        # WP6.5 (owner "2. app"): the macOS release is the BUNDLE; the onedir folder
        # PyInstaller also leaves beside it is not shipped.
        candidates = (root / MACOS_APP / "Contents" / "MacOS" / APP_NAME,)
    for candidate in (
        *candidates,
        root / APP_NAME / f"{APP_NAME}{suffix}",
        root / f"{APP_NAME}{suffix}",
    ):
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
    texts: list[FFmpegComponentText]
    chosen: NotRequired[str | None]


class FFmpegComponent(TypedDict):
    """A source-pinned component; a stage may also fetch additional components."""

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
    texts: list[FFmpegComponentText]
    chosen: NotRequired[str | None]
    status: NotRequired[str]
    via: NotRequired[str]


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
    backtrace_commit: str


class FFmpegToolchain(TypedDict):
    """Recorded toolchains and static-link flags of this asset, not future builds."""

    gcc: FFmpegGCC
    rustc: FFmpegRustc
    static_link_flags: list[str]
    census_build_commit: str
    census_asset_sha256: str


class FFmpegRuntimeText(TypedDict):
    """A filename and byte hash in the corresponding FFmpeg text directory."""

    path: str
    sha256: str


class FFmpegComponentText(FFmpegRuntimeText):
    """Exact source bytes with an optional, lossless artifact display encoding."""

    encoding: NotRequired[str]


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
    linkage: str


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


class FFmpegBuildScript(TypedDict):
    """The vendored build-script repository the macOS recipe runs, at its full commit."""

    repository: str
    commit: str


class FFmpegMacText(TypedDict):
    """A macOS component or runtime text: its file, byte hash and source member.

    ``member`` is the path inside the pinned source (``<top>/<path>`` in a tarball, the
    tree path at a commit); a line-range excerpt appends ``#L<first>-<last>``.
    """

    path: str
    sha256: str
    member: str


class FFmpegMacComponent(TypedDict):
    """A macOS FFmpeg component in the Windows row shape (texts carry their member).

    ``pin_kind`` is ``sha256`` (``repository`` = the pinned download URL, ``pin`` = its
    runner-verified digest) or ``commit``; ``status`` is ``built`` (the default) or
    ``built-not-linked``; ``extra_repositories`` is always empty (one source per stage).
    """

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
    texts: list[FFmpegMacText]
    chosen: NotRequired[str | None]
    status: NotRequired[str]


class FFmpegMacToolchain(TypedDict):
    """The Apple toolchain of THIS asset; ``compiler`` is the marker the tools carry."""

    compiler: str
    xcode: str
    sdk: str
    target: str
    deployment_target: str
    census_build_commit: str
    census_asset_sha256: str


class FFmpegMacRuntime(TypedDict):
    """The Apple clang runtime row (compiler-rt builtins, libc++ portions; G2a-F5)."""

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
    texts: list[FFmpegMacText]
    evidence: str
    basis: str
    basis_note: str
    chosen: str | None
    linkage: str


class FFmpegMacCensus(TypedDict):
    """Where the complete census was read: the run's job log (step and lines) and the zip."""

    state: str
    job_url: str
    log: str
    linkage_step: str
    linkage_lines: str
    version_lines: str
    toolchain_step: str
    toolchain_lines: str
    external_libraries: str


class FFmpegMacLock(TypedDict):
    """The macOS arm64 FFmpeg pin (WP6.5): the fork's release asset and its provenance.

    A SECOND lock document beside the Windows one, validated by the same
    :func:`validate_ffmpeg_lock` under ``platform="darwin"``; ``platform`` is its
    discriminator (the Windows document carries no such field). ``census`` is
    ``"pending"`` (``components``, ``toolchain`` and ``toolchain_runtime`` then stay
    empty) or a :class:`FFmpegMacCensus` naming the run-log step and lines the complete
    census rows were read from (WP6.5 part 3).
    """

    schema_version: int
    platform: str
    census: str | FFmpegMacCensus
    provider: str
    build_script: FFmpegBuildScript
    release_tag: str
    build_repository_commit: str
    build_run_url: str
    asset_name: str
    asset_url: str
    size_bytes: int
    github_sha256: str
    seat_sha256: str
    ffmpeg_ref: str
    ffmpeg_commit: str
    ffmpeg_repository: str
    version: str
    configure_line: str
    licence: str
    archive_root: str
    extract_members: list[str]
    source_record_url: str
    retention_note: str
    macos_deployment_target: str
    runner_label: str
    runner_image_version: str
    components: list[FFmpegMacComponent]
    excluded: list[FFmpegExcluded]
    toolchain: FFmpegMacToolchain | None
    toolchain_runtime: list[FFmpegMacRuntime]


FFMPEG_LOCK_PATH = Path(__file__).with_name("ffmpeg.lock.json")
"""The release pin; local PATH copies never substitute for this record."""

FFMPEG_MACOS_LOCK_PATH = Path(__file__).with_name("ffmpeg-macos.lock.json")
"""The macOS arm64 release pin (WP6.5 part 3 writes it from the fork run)."""

FFMPEG_MACOS_PLATFORM = "macos-arm64"
"""The macOS lock's ``platform`` discriminator."""

FFMPEG_MACOS_PROVIDER = "rwsmythe/FFmpeg-Builds"
"""The owner's fork, the only macOS provider (AD-38 (9); WP6.5 group 2a)."""

FFMPEG_MACOS_BUILD_SCRIPT = "https://git.martin-riedl.de/ffmpeg/build-script.git"
"""The build script the fork's macOS recipe vendors (ledger ``## Group 2a`` 4a.1)."""

FFMPEG_MACOS_DEPLOYMENT_TARGET = "14.0"
"""``MACOSX_DEPLOYMENT_TARGET`` of the recipe: the PySide6 / shiboken6 wheel floor."""

FFMPEG_MACOS_RUNNER_LABEL = "macos-26"
"""The ruled GitHub arm64 runner label (round-0 ruling Q1)."""

FFMPEG_MACOS_TOOLS = ("ffmpeg", "ffprobe")
"""The two Mach-O tools of the macOS asset, at ``bin/`` (no ``.exe``)."""

FFMPEG_MACOS_EXCLUDED_STAGES = frozenset(
    {
        "SKIP_ZVBI",
        "SKIP_DECKLINK",
        "SKIP_LIBKLVANC",
        "SKIP_RAV1E",
        "SKIP_SRT",
        "SKIP_ZIMG",
        "SKIP_LIBBLURAY",
        "SKIP_SNAPPY",
        "SKIP_LIBVMAF",
        "SKIP_AOM",
        "SKIP_DAV1D",
        "SKIP_OPEN_H264",
        "SKIP_OPEN_JPEG",
        "SKIP_SVT_AV1",
        "SKIP_LIBTHEORA",
        "SKIP_VPX",
        "SKIP_VVENC",
        "SKIP_LIBWEBP",
        "SKIP_LAME",
        "SKIP_OPUS",
        "SKIP_LIBVORBIS",
    }
)
"""The macOS lock's ``excluded`` stages, EXACTLY: the fork recipe's component skips.

The ``-SKIP_<NAME>=YES`` switches ``tools/package/ffmpeg-fork-macos.patch`` passes to the
build script, less ``SKIP_TEST`` and ``SKIP_BUNDLE`` (not components). Held here, not read
from the patch, so the validator needs nothing but the lock; a test binds this set to the
patch, so a recipe change that is not mirrored here fails the suite.
"""

FFMPEG_MACOS_REQUIRED_SWITCHES = ("gpl", "version3", "libx265")
"""The configure switches the macOS line MUST enable (AD-38 (2) plus ``version3``)."""

_LIBX265_ENCODER_OFF = frozenset(
    {
        "--disable-encoders",
        "--disable-everything",
        "--disable-all",
        "--disable-avcodec",
        "--enable-random",
        "--disable-random",
    }
)
"""Configure options that can switch the libx265 ENCODER off with ``--enable-libx265`` left on.

FFmpeg's configure (at ``b204e94e``, its ``for opt do`` loop): ``--disable-encoders`` unsets
the encoder list, ``--disable-everything`` every component list, ``--disable-all`` those and
the libraries (libavcodec among them), ``--disable-avcodec`` the library itself, and
``--enable-random`` / ``--disable-random`` (with or without ``=<lists>``) toggle components
at random. ``--disable-encoder=<value>`` is judged by :data:`_LITERAL_ENCODER_LIST`.
"""

_CONFIGURE_ARGUMENT = re.compile(
    r"(?P<name>(?:--)?[A-Za-z0-9][A-Za-z0-9_-]*)"
    r"(?:=(?P<value>'(?:[^']|'\\'')*'|[A-Za-z0-9_/.+-]*))?"
)
"""One argument as FFmpeg's configure PRINTS it (its ``FFMPEG_CONFIGURATION``, at ``b204e94e``).

configure joins its arguments with single spaces, each as ``l`` (up to and including the
first ``=``, as given) plus ``sh_quote`` of the rest: as is when every byte is in
``[A-Za-z0-9_/.+-]``, else inside ``'...'`` with each ``'`` written ``'\\''``. An argument
without ``=`` is quoted whole, so a quoted option NAME (``'--disable-libx265 '``, which
configure's ``eval`` still applies) does not match and the line is refused.
"""

_LITERAL_ENCODER_LIST = re.compile(r"[A-Za-z0-9_]+(?:,[A-Za-z0-9_]+)*")
"""The only ``--disable-encoder=`` value admitted: a comma list of literal names (A4-F1).

configure turns the value into ONE shell ``case`` pattern (each ``,`` becomes
``_encoder|``, then ``_encoder`` is appended once) and evaluates it with ``eval``, so
``*``, ``?``, ``[...]`` (with POSIX classes), ``|``, ``\\`` and quoting all carry shell
semantics. Those are NOT reproduced: any other value is refused, whatever it would match
(``libx265|aac`` matches nothing in configure and is still refused). For a literal list the
pattern is ``<a>_encoder|<b>_encoder|...``, which reaches ``libx265_encoder`` only through
the item ``libx265``, refused by name.
"""

FFMPEG_COMPONENT_TEXTS_PATH = Path(__file__).with_name("native-licences") / "ffmpeg-components"
"""The byte-preserved component texts, covered exactly by the release lock."""

FFMPEG_MACOS_TEXTS_PATH = Path(__file__).with_name("native-licences") / "ffmpeg-macos-components"
"""The macOS lock's texts (components and the toolchain runtime), covered exactly by it."""

FFMPEG_MACOS_COMPONENTS = frozenset(
    {
        "fontconfig",
        "freetype",
        "fribidi",
        "harfbuzz",
        "libass",
        "libogg",
        "libxml2",
        "openssl",
        "sdl",
        "x264",
        "x265",
        "zlib",
    }
)
"""The components the fork's macOS build compiled, EXACTLY (a complete census names each).

The zip's ``build/versions.txt`` less FFmpeg and the build tools (nasm, ninja, pkg-config,
cmake, meson); one ``build/logs/build-<name>.log`` each. A missing or invented row fails.
"""

FFMPEG_MACOS_UNLINKED = frozenset({"libogg"})
"""Components the build compiled but FFmpeg does not link (absent from its library list)."""

FFMPEG_MACOS_NON_LIBRARY_SWITCHES = frozenset(
    {"--enable-gpl", "--enable-version3", "--enable-gray"}
)
"""The macOS line's licence / feature switches, which name no source-pinned library."""

FFMPEG_MACOS_COMPILER = re.compile(r"Apple clang version (\d+\.\d+\.\d+) \((clang-\d+(?:\.\d+)*)\)")
"""The Apple toolchain marker: clang's version line, compiled into FFmpeg as ``CC_IDENT``."""

FFMPEG_MACOS_LLVM_REPOSITORY = "https://github.com/llvm/llvm-project"
"""Upstream of the Apple clang runtime row's licence text (Apple publishes no per-build tree)."""


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
"""CHARC's runtime atoms; every expression requires a compatible selection."""


FFMPEG_COMPONENT_COMPATIBLE_LICENCES = FFMPEG_COMPATIBLE_LICENCES | frozenset(
    {
        "GPL-2.0-or-later",
        "GPL-3.0-or-later",
        "LGPL-2.0-or-later",
        "LGPL-2.1-or-later",
        "LGPL-2.1-only",
        "LGPL-3.0-or-later",
        "BSD-3-Clause-Clear",
        "BSD-2-Clause-Patent",
        "FTL",
        "Libpng-2.0",
        "MIT-Modern-Variant",
        "WTFPL",
        "ZPL-2.1",
        "LicenseRef-mingw-w64-public-domain",
        "LicenseRef-gnulib-permissive",
        "GPL-3.0-or-later WITH Bison-exception-2.2",
        "AML-glslang",
        "MIT-Khronos-old",
        "LicenseRef-PFFFT-modified-BSD",
        "ISC-Veillard",
    }
)
"""CHARC's component atoms (rulings B S1 and C1-C2); the runtime list is separate."""


def _ffmpeg_licence_choices(
    expression: str,
    atoms: frozenset[str] = FFMPEG_COMPATIBLE_LICENCES,
    population: str = "runtime",
) -> set[str]:
    """Return compatible complete selections, preserving every AND obligation.

    A non-null ``chosen`` must equal one returned selection exactly, for example
    ``MIT AND BSD-3-Clause`` for ``(Apache-2.0 OR MIT) AND BSD-3-Clause``;
    the single branch atom ``MIT`` is not a complete selection. AND takes a
    cartesian product of alternatives, so repeated OR factors grow choices
    exponentially. Non-OR expressions return no choices to select explicitly.

    Args:
        expression: The complete SPDX-style expression to parse.
        atoms: Compatible atoms for this population.
        population: Label used in refusal messages.

    Returns:
        Complete compatible selections when the expression contains OR.

    Raises:
        ValueError: The expression is malformed or has no compatible selection.
    """
    # Parse every branch, even an unchosen one: OR-any cannot hide bad syntax.
    # Compatible selections distribute AND over OR, preserving every obligation.
    tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9.+-]*|[()]", expression)
    position = 0
    has_or = False
    refusal = f"FFmpeg lock: incompatible/invalid {population} licence expression"
    if (
        not tokens
        or any(c.isspace() and c != " " for c in expression)
        or "".join(tokens) != "".join(expression.split(" "))
    ):
        raise ValueError(refusal)

    def identifier(token: str) -> bool:
        return (
            token not in {"AND", "OR", "WITH"}
            and re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9.+-]*[A-Za-z0-9])?", token) is not None
        )

    def primary() -> set[str]:
        nonlocal position
        if position >= len(tokens):
            raise ValueError(refusal)
        token = tokens[position]
        position += 1
        if token == "(":
            selections = either()
            if position >= len(tokens) or tokens[position] != ")":
                raise ValueError(refusal)
            position += 1
            return selections
        if not identifier(token):
            raise ValueError(refusal)
        if position < len(tokens) and tokens[position] == "WITH":
            position += 1
            if position >= len(tokens) or not identifier(tokens[position]):
                raise ValueError(refusal)
            token += " WITH " + tokens[position]
            position += 1
        return {token} if token in atoms else set()

    def both() -> set[str]:
        nonlocal position
        selections = primary()
        while position < len(tokens) and tokens[position] == "AND":
            position += 1
            other = primary()
            selections = {left + " AND " + right for left in selections for right in other}
        return selections

    def either() -> set[str]:
        nonlocal position, has_or
        selections = both()
        while position < len(tokens) and tokens[position] == "OR":
            position += 1
            has_or = True
            selections.update(both())
        return selections

    selections = either()
    if position != len(tokens) or not selections:
        raise ValueError(refusal)
    return selections if has_or else set()


def _ffmpeg_runtime(data: dict[str, object], config: str) -> None:
    toolchain = _ffmpeg_fields(data["toolchain"], set(FFmpegToolchain.__annotations__), "toolchain")
    for field, identity_field in (
        ("census_build_commit", "build_repository_commit"),
        ("census_asset_sha256", "github_sha256"),
    ):
        if toolchain[field] != data[identity_field]:
            raise ValueError(
                f"FFmpeg lock: {field} differs from {identity_field}; re-census required"
            )
    for key, fields in (("gcc", FFmpegGCC.__annotations__), ("rustc", FFmpegRustc.__annotations__)):
        compiler = _ffmpeg_fields(toolchain[key], set(fields), f"toolchain {key}")
        for field in fields:
            text = _ffmpeg_text(compiler[field], f"toolchain {key} {field}")
            if field.endswith("commit") and not re.fullmatch(r"[0-9a-f]{40}", text):
                raise ValueError(f"FFmpeg lock: invalid toolchain {key} {field}")
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
        if row["linkage"] not in {"proven", "superset"}:
            raise ValueError("FFmpeg lock: invalid runtime linkage")
        if row["linkage"] == "superset" and row["basis"] == "compile-log":
            raise ValueError("FFmpeg lock: superset linkage cannot have compile-log basis")
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
            if not cast(str, row["repository"]).startswith(("https://", "http://")):
                raise ValueError("FFmpeg lock: cargo-crate repository must use HTTP(S)")
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
                row["name"] in {"compiler_builtins", "libm"}
                and row["repository"] != "https://github.com/rust-lang/rust"
            ):
                raise ValueError(f"FFmpeg lock: {row['name']} requires rust-lang/rust repository")
            if row["repository"] not in {
                "https://github.com/rust-lang/rust",
                "https://github.com/rust-lang/backtrace-rs",
            }:
                raise ValueError("FFmpeg lock: invalid rust-std repository")
            if (
                row["repository"] == "https://github.com/rust-lang/rust"
                and row["pin"] != rustc["commit"]
            ):
                raise ValueError("FFmpeg lock: rust-std pin differs from toolchain")
            if row["name"] == "rust-std" and row["version"] != rustc["version"]:
                raise ValueError("FFmpeg lock: rust-std version differs from toolchain")
            if row["name"] == "backtrace" and row["pin"] != rustc["backtrace_commit"]:
                raise ValueError("FFmpeg lock: backtrace pin differs from toolchain gitlink")
        if row["kind"] == "mingw-runtime":
            stages = cast(list[FFmpegComponent], data["components"])
            if not any(
                stage["name"] == "mingw" and stage["repository"] == row["repository"]
                for stage in stages
            ):
                raise ValueError("FFmpeg lock: mingw-runtime repository differs from mingw stage")
        if row["kind"] == "gcc-runtime":
            if row["repository"] != "https://github.com/gcc-mirror/gcc":
                raise ValueError("FFmpeg lock: invalid gcc-runtime repository")
            if row["version"] != gcc["version"] or row["pin"] != gcc["commit"]:
                raise ValueError("FFmpeg lock: gcc-runtime pin/version differs from toolchain")
        if row["kind"] != "cargo-crate":
            base = f"{row['repository']}/tree/{row['pin']}"
            source_url = cast(str, row["source_url"])
            if source_url != base and not source_url.startswith(base + "/"):
                raise ValueError("FFmpeg lock: runtime source_url differs from repository/pin")
        texts = row["texts"]
        if not isinstance(texts, list) or not texts:
            raise ValueError("FFmpeg lock: runtime texts must be nonempty")
        for item in texts:
            text_record = _ffmpeg_fields(
                item, set(FFmpegRuntimeText.__annotations__), "runtime text"
            )
            path = _ffmpeg_text(text_record["path"], "runtime text path")
            if (
                any(c in path for c in ("/", "\\", ":", ".."))
                or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]*[A-Za-z0-9]", path) is None
            ):
                raise ValueError("FFmpeg lock: unsafe runtime text path")
            if (
                re.fullmatch(
                    r"[0-9a-f]{64}", _ffmpeg_text(text_record["sha256"], "runtime text sha256")
                )
                is None
            ):
                raise ValueError("FFmpeg lock: invalid runtime text sha256")
        # Only single-text OR rows are decidable here without guessing which
        # alternative a shared filename represents. This verified combined text
        # explicitly carries MIT, Apache-2.0 and its LLVM exception in full.
        combined_terms = {
            "ab6eec6caf0fa5775e411c7a8bc6a45c4ef2956b0980b157ab74fc5cd62a928b": {
                "MIT",
                "Apache-2.0",
                "Apache-2.0 WITH LLVM-exception",
            }
        }
        if len(texts) == 1 and choices and row["chosen"] is None:
            carried = cast(dict[str, str], texts[0])
            terms = {term for choice in choices for term in choice.split(" AND ")}
            if not terms <= combined_terms.get(carried["sha256"], set()):
                raise ValueError("FFmpeg lock: one-text OR licence requires chosen")
        checked.append(cast(FFmpegRuntime, row))
    for stage, switch in (("rav1e", "--enable-librav1e"), ("librsvg", "--enable-librsvg")):
        enabled = switch in config.split()
        if enabled and not flags:
            raise ValueError("FFmpeg lock: Rust stages require nonempty static_link_flags")
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
    if "--enable-libx265" in config.split():
        for name in ("libgcc", "libstdc++"):
            if not any(r["name"] == name and r["kind"] == "gcc-runtime" for r in checked):
                raise ValueError(f"FFmpeg lock: libx265 requires gcc-runtime {name}")


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


def _ffmpeg_component_fields(item: object, *, extra: bool = False) -> dict[str, object]:
    fields = set(FFmpegSource.__annotations__ if extra else FFmpegComponent.__annotations__)
    optional = {"texts", "chosen"} if extra else {"texts", "chosen", "status", "via"}
    if not isinstance(item, dict) or not fields - optional <= set(item) <= fields:
        raise ValueError(f"FFmpeg lock: invalid {'extra source' if extra else 'component'} fields")
    return cast(dict[str, object], item)


def _ffmpeg_component_obligations(row: dict[str, object]) -> None:
    status = row.get("status", "built")
    if not isinstance(status, str) or status not in {"built", "downloaded-not-built"}:
        raise ValueError("FFmpeg lock: invalid component status")
    choices = _ffmpeg_licence_choices(
        cast(str, row["licence"]), FFMPEG_COMPONENT_COMPATIBLE_LICENCES, "component"
    )
    chosen = row.get("chosen")
    if chosen is not None and (not isinstance(chosen, str) or chosen not in choices):
        raise ValueError("FFmpeg lock: invalid component chosen licence")
    texts = row.get("texts")
    if not isinstance(texts, list) or not texts:
        raise ValueError("FFmpeg lock: component texts must be nonempty")
    for item in texts:
        fields = set(FFmpegRuntimeText.__annotations__)
        if not isinstance(item, dict) or not fields <= set(item) <= fields | {"encoding"}:
            raise ValueError("FFmpeg lock: invalid component text fields")
        text = cast(dict[str, object], item)
        if "encoding" in text and (
            not isinstance(text["encoding"], str) or text["encoding"] not in {"latin-1", "cp1252"}
        ):
            raise ValueError("FFmpeg lock: invalid component text encoding")
        path = _ffmpeg_text(text["path"], "component text path")
        if (
            any(c in path for c in ("/", "\\", ":", ".."))
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]*[A-Za-z0-9]", path) is None
        ):
            raise ValueError("FFmpeg lock: unsafe component text path")
        if (
            re.fullmatch(r"[0-9a-f]{64}", _ffmpeg_text(text["sha256"], "component text sha256"))
            is None
        ):
            raise ValueError("FFmpeg lock: invalid component text sha256")


def _ffmpeg_component_texts(components: list[FFmpegComponent], folder: Path) -> None:
    encodings: dict[str, str | None] = {}
    for component in components:
        for row in (component, *component["extra_repositories"]):
            for text in row["texts"]:
                name, encoding = text["path"], text.get("encoding")
                if name in encodings and encodings[name] != encoding:
                    raise ValueError(f"FFmpeg lock: conflicting component text encodings: {name}")
                encodings[name] = encoding
    expected: set[str] = set()
    for component in components:
        for row in (component, *component["extra_repositories"]):
            for text in row["texts"]:
                path = folder / text["path"]
                if not path.is_file() or path.is_symlink():
                    raise ValueError(f"FFmpeg lock: component text missing/unsafe: {text['path']}")
                data = path.read_bytes()
                if hashlib.sha256(data).hexdigest() != text["sha256"]:
                    raise ValueError(f"FFmpeg lock: component text sha256 mismatch: {text['path']}")
                if "encoding" in text:
                    try:
                        data.decode("utf-8")
                    except UnicodeDecodeError:
                        pass
                    else:
                        raise ValueError(
                            "FFmpeg lock: component text encoding declared for strict UTF-8: "
                            + text["path"]
                        )
                encoding = text.get("encoding", "utf-8")
                try:
                    decoded = data.decode(encoding)
                    if decoded.encode(encoding) != data:
                        raise ValueError("encoding does not round-trip")
                except (UnicodeError, ValueError) as error:
                    refusal = (
                        "encoding cannot round-trip"
                        if "encoding" in text
                        else "is not strict UTF-8"
                    )
                    raise ValueError(
                        f"FFmpeg lock: component text {refusal}: {text['path']}"
                    ) from error
                if "encoding" in text and any("\u0080" <= c <= "\u009f" for c in decoded):
                    raise ValueError(
                        "FFmpeg lock: component text transcode contains C1 controls: "
                        + text["path"]
                    )
                expected.add(text["path"])
    actual = {path.name for path in folder.iterdir()} if folder.is_dir() else set()
    if actual != expected:
        raise ValueError("FFmpeg lock: component text directory differs from lock")


def _sh_quote(value: str) -> str:
    r"""``value`` as FFmpeg's configure ``sh_quote`` prints it (at ``b204e94e``).

    Each ``'`` becomes ``'\''``; the result is printed as is when every byte is in
    ``[A-Za-z0-9_/.+-]`` (the empty string included) and inside ``'...'`` otherwise.
    """
    escaped = value.replace("'", "'\\''")
    if re.fullmatch(r"[A-Za-z0-9_/.+-]*", escaped):
        return escaped
    return f"'{escaped}'"


def _configure_arguments(body: str) -> list[tuple[str, str, str | None]] | None:
    """``(argument, name, unquoted value or None)`` per printed argument, or None.

    ``body`` is the printed configuration without its ``configuration: `` prefix; None
    when it is not exactly arguments of :data:`_CONFIGURE_ARGUMENT` joined by single
    spaces (an empty argument, a tab, a quote outside a value, an unbalanced quote), or
    when a value is not spelled as ``sh_quote`` spells it (:func:`_sh_quote`; A r5: a
    value configure prints bare, given redundant quotes, ``--extra-version='20261110'``).
    """
    arguments: list[tuple[str, str, str | None]] = []
    position = 0
    while True:
        match = _CONFIGURE_ARGUMENT.match(body, position)
        if match is None or match.end() == position:
            return None
        value = match["value"]
        if value is not None:
            if value.startswith("'"):
                value = value[1:-1].replace("'\\''", "'")
            if _sh_quote(value) != match["value"]:
                return None
        arguments.append((match.group(), match["name"], value))
        position = match.end()
        if position == len(body):
            return arguments
        if body[position] != " ":
            return None
        position += 1


def _macos_configure_problem(config: str, version: str) -> str | None:
    """The AD-38 (2) MUST / MUST NOT rules, plus no zvbi / DeckLink, for the macOS line.

    The line must be configure's PRINTED form (:data:`_CONFIGURE_ARGUMENT`), so every
    argument configure applied is one argument here and none hides inside a quote. A
    required switch must be ENABLED and never disabled. FFmpeg's configure applies its
    options left to right and the last ``--enable-X`` / ``--disable-X`` wins, so a
    disabling counterpart after the enable defeats it; this rule refuses the counterpart
    ANYWHERE in the line (before or after), so the verdict never depends on option order
    (the recipe's line carries none). The libx265 encoder must also stay selectable: an
    option that can switch it off with the library left on (:data:`_LIBX265_ENCODER_OFF`)
    is refused, and so is every ``--disable-encoder=`` value that is not a literal list or
    that names ``libx265`` (:data:`_LITERAL_ENCODER_LIST`: conservative refusal, configure's
    shell-pattern semantics are not emulated). ``extra-version`` is counted in every
    spelling configure's ``*)`` branch takes (``--`` optional, ``-`` and ``_`` alike).
    """
    if not config.startswith("configuration: "):
        return "configure_line must include its printed prefix"
    arguments = _configure_arguments(config.removeprefix("configuration: "))
    if arguments is None:
        return "configure_line is not configure's printed form (single spaces, sh_quote)"
    tokens = [argument for argument, _name, _value in arguments]
    required = {f"--enable-{name}" for name in FFMPEG_MACOS_REQUIRED_SWITCHES}
    if not required <= set(tokens):
        return "GPL, version3 and libx265 are required"
    disabled = [f"--disable-{name}" for name in FFMPEG_MACOS_REQUIRED_SWITCHES]
    for token, option, value in arguments:
        if token in disabled:
            return f"a required switch is disabled ({token})"
        if option in _LIBX265_ENCODER_OFF:
            return f"the libx265 encoder can be disabled ({token})"
        if option == "--disable-encoder" and (
            value is None
            or not _LITERAL_ENCODER_LIST.fullmatch(value)
            or "libx265" in value.split(",")
        ):
            return (
                f"the libx265 encoder can be disabled ({token}): only a literal list of "
                "encoder names not naming libx265 is admitted"
            )
    if any(
        token in {"--enable-nonfree", "--enable-libzvbi", "--enable-decklink"} or "libfdk" in token
        for token in tokens
    ):
        return "nonfree, libfdk, zvbi or decklink is forbidden"
    dates = [
        value or ""
        for _token, name, value in arguments
        if name.removeprefix("--").replace("_", "-") == "extra-version"
    ]
    if dates != [version[-8:]]:
        return "version date must match --extra-version (exactly one, in any spelling)"
    return None


def _macos_texts(texts: object, context: str) -> list[FFmpegMacText]:
    """Check one row's text records (:class:`FFmpegMacText`); the bytes are checked later."""
    if not isinstance(texts, list) or not texts:
        raise ValueError(f"FFmpeg lock: {context} texts must be nonempty")
    for item in texts:
        record = _ffmpeg_fields(item, set(FFmpegMacText.__annotations__), f"{context} text")
        path = _ffmpeg_text(record["path"], f"{context} text path")
        if (
            any(c in path for c in ("/", "\\", ":", ".."))
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]*[A-Za-z0-9]", path) is None
        ):
            raise ValueError(f"FFmpeg lock: unsafe {context} text path")
        if not re.fullmatch(r"[0-9a-f]{64}", _ffmpeg_text(record["sha256"], f"{context} sha256")):
            raise ValueError(f"FFmpeg lock: invalid {context} text sha256")
        member, _, lines = _ffmpeg_text(record["member"], f"{context} text member").partition("#")
        if (
            member.startswith("/")
            or "\\" in member
            or any(part in {"", ".", ".."} for part in member.split("/"))
        ):
            raise ValueError(f"FFmpeg lock: unsafe {context} text member")
        excerpt = re.fullmatch(r"L([0-9]+)-([0-9]+)", lines) if lines else None
        if lines and (
            excerpt is None
            or int(excerpt[1]) > int(excerpt[2])
            or not path.endswith(f"-L{excerpt[1]}-{excerpt[2]}.txt")
        ):
            raise ValueError(f"FFmpeg lock: invalid {context} text excerpt")
    return cast(list[FFmpegMacText], texts)


def _macos_census_source(data: dict[str, object]) -> None:
    """The complete census's source block: the run's job log, its step and line ranges."""
    census = _ffmpeg_fields(data["census"], set(FFmpegMacCensus.__annotations__), "census")
    for key in census:
        _ffmpeg_text(census[key], f"census {key}")
    if census["state"] != "complete":
        raise ValueError("FFmpeg lock: census state must be complete")
    run = re.escape(cast(str, data["build_run_url"]))
    if not re.fullmatch(run + r"/job/[0-9]+", cast(str, census["job_url"])):
        raise ValueError("FFmpeg lock: census job_url must be a job of the build run")
    for key in ("linkage_lines", "version_lines", "toolchain_lines"):
        span = re.fullmatch(r"([0-9]+)-([0-9]+)", cast(str, census[key]))
        if span is None or int(span[1]) > int(span[2]):
            raise ValueError(f"FFmpeg lock: invalid census {key}")
    if not re.fullmatch(
        r"build/logs/build-ffmpeg\.log:[0-9]+-[0-9]+", cast(str, census["external_libraries"])
    ):
        raise ValueError("FFmpeg lock: invalid census external_libraries")


def _macos_census_components(data: dict[str, object], config: str) -> list[FFmpegMacComponent]:
    """The component rows (Windows row shape) and the two-way configure coverage."""
    components = data["components"]
    if not isinstance(components, list) or not components:
        raise ValueError("FFmpeg lock: census complete: components must be a nonempty list")
    names: set[str] = set()
    covered: set[str] = set()
    for item in components:
        row = _ffmpeg_component_fields(item)
        if "via" in row:
            raise ValueError("FFmpeg lock: invalid component fields (via is Windows-only)")
        name = _ffmpeg_text(row["name"], "component name")
        if name in names:
            raise ValueError(f"FFmpeg lock: duplicate component {name}")
        names.add(name)
        if row["stage"] != f"build-{name}":
            raise ValueError(f"FFmpeg lock: {name}: stage must be build-{name} (its zip log)")
        repository = _ffmpeg_text(row["repository"], "component repository")
        pin = _ffmpeg_text(row["pin"], "component pin")
        if not repository.startswith("https://"):
            raise ValueError(f"FFmpeg lock: {name}: source repository must use HTTPS")
        if row["pin_kind"] == "sha256":
            if not re.fullmatch(r"[0-9a-f]{64}", pin):
                raise ValueError(f"FFmpeg lock: {name}: invalid tarball sha256 pin")
        elif row["pin_kind"] == "commit":
            if not re.fullmatch(r"[0-9a-f]{40}", pin):
                raise ValueError(f"FFmpeg lock: {name}: invalid source commit")
        else:
            raise ValueError(f"FFmpeg lock: {name}: pin_kind must be sha256 or commit")
        if row["extra_repositories"] != []:
            raise ValueError(f"FFmpeg lock: {name}: extra_repositories must be empty")
        if row["licence_basis"] != "pinned-source-text" or row["gpl3_compatible"] != "yes":
            raise ValueError(
                f"FFmpeg lock: {name}: licence_basis must be pinned-source-text and "
                "gpl3_compatible yes"
            )
        _ffmpeg_text(row["licence_note"], "component licence note")
        choices = _ffmpeg_licence_choices(
            _ffmpeg_text(row["licence"], "licence"),
            FFMPEG_COMPONENT_COMPATIBLE_LICENCES,
            "component",
        )
        chosen = row.get("chosen")
        if chosen is not None and (not isinstance(chosen, str) or chosen not in choices):
            raise ValueError("FFmpeg lock: invalid component chosen licence")
        _macos_texts(row.get("texts"), f"component {name}")
        status = row.get("status", "built")
        if (
            not isinstance(status, str)
            or status not in {"built", "built-not-linked"}
            or (status == "built-not-linked") != (name in FFMPEG_MACOS_UNLINKED)
        ):
            raise ValueError(f"FFmpeg lock: {name}: invalid component status {status!r}")
        flags = row["configure_flag"]
        if flags is not None:
            if not isinstance(flags, list) or not flags or status != "built":
                raise ValueError(f"FFmpeg lock: {name}: configure_flag must be null or nonempty")
            for flag in flags:
                if not isinstance(flag, str) or not re.fullmatch(r"--enable-[a-z0-9-]+", flag):
                    raise ValueError("FFmpeg lock: invalid component configure flag")
                if flag in covered:
                    raise ValueError(f"FFmpeg lock: configure flag {flag} mapped twice")
                covered.add(flag)
    if names != FFMPEG_MACOS_COMPONENTS:
        raise ValueError(
            "FFmpeg lock: components must be exactly the build's; "
            f"missing {sorted(FFMPEG_MACOS_COMPONENTS - names)}, "
            f"unknown {sorted(names - FFMPEG_MACOS_COMPONENTS)}"
        )
    arguments = _configure_arguments(config.removeprefix("configuration: ")) or []
    enabled = {token for token, _name, _value in arguments if token.startswith("--enable-")}
    external = enabled - FFMPEG_MACOS_NON_LIBRARY_SWITCHES
    if external != covered:
        raise ValueError(
            f"FFmpeg lock: configure coverage differs; unmapped={sorted(external - covered)}, "
            f"absent={sorted(covered - external)}"
        )
    return cast(list[FFmpegMacComponent], components)


def _macos_census_toolchain(data: dict[str, object]) -> FFmpegMacToolchain:
    """The Apple toolchain object, bound to THIS asset and the lock's deployment target."""
    toolchain = _ffmpeg_fields(
        data["toolchain"], set(FFmpegMacToolchain.__annotations__), "toolchain"
    )
    for key in toolchain:
        _ffmpeg_text(toolchain[key], f"toolchain {key}")
    for key, pattern in (
        ("compiler", FFMPEG_MACOS_COMPILER.pattern),
        ("xcode", r"[0-9]+(?:\.[0-9]+)* \([0-9A-Za-z]+\)"),
        ("sdk", r"[0-9]+\.[0-9]+(?:\.[0-9]+)?"),
        ("target", r"arm64-apple-darwin[0-9]+(?:\.[0-9]+)*"),
    ):
        if not re.fullmatch(pattern, cast(str, toolchain[key])):
            raise ValueError(f"FFmpeg lock: invalid toolchain {key}")
    for field, identity in (
        ("deployment_target", "macos_deployment_target"),
        ("census_build_commit", "build_repository_commit"),
        ("census_asset_sha256", "github_sha256"),
    ):
        if toolchain[field] != data[identity]:
            raise ValueError(f"FFmpeg lock: toolchain {field} differs from {identity}; re-census")
    return cast(FFmpegMacToolchain, toolchain)


def _macos_census_runtime(
    data: dict[str, object], toolchain: FFmpegMacToolchain
) -> list[FFmpegMacRuntime]:
    """The ONE Apple clang runtime row (G2a-F5; CHARC R2), bound to the toolchain object."""
    rows = data["toolchain_runtime"]
    if not isinstance(rows, list) or len(rows) != 1:
        raise ValueError("FFmpeg lock: census complete: exactly one toolchain_runtime row")
    row = _ffmpeg_fields(rows[0], set(FFmpegMacRuntime.__annotations__), "toolchain runtime")
    for key in set(FFmpegMacRuntime.__annotations__) - {"texts", "chosen"}:
        _ffmpeg_text(row[key], f"runtime {key}")
    marker = FFMPEG_MACOS_COMPILER.fullmatch(toolchain["compiler"])
    assert marker is not None  # checked by _macos_census_toolchain
    expected = {
        "kind": "apple-clang-runtime",
        "reached_via": "toolchain",
        "pin_kind": "toolchain-marker",
        "pin": toolchain["compiler"],
        "version": marker[2],
        "name": (
            f"Apple clang {marker[1]} ({marker[2]}), Xcode {toolchain['xcode'].split()[0]}, "
            f"SDK {toolchain['sdk']}, deployment target {toolchain['deployment_target']}"
        ),
        "repository": FFMPEG_MACOS_LLVM_REPOSITORY,
        "licence": "Apache-2.0 WITH LLVM-exception",
        "licence_basis": "upstream-text",
        "gpl3_compatible": "yes",
        "linkage": "inferred",
        "basis": "toolchain-marker",
        "chosen": None,
    }
    for key, value in expected.items():
        if row[key] != value:
            raise ValueError(f"FFmpeg lock: runtime {key} must be {value!r}")
    if not re.fullmatch(
        re.escape(FFMPEG_MACOS_LLVM_REPOSITORY) + r"/tree/[0-9a-f]{40}",
        cast(str, row["source_url"]),
    ):
        raise ValueError("FFmpeg lock: runtime source_url must be an llvm-project commit tree")
    _macos_texts(row["texts"], "runtime")
    return cast(list[FFmpegMacRuntime], rows)


def _macos_census_texts(
    components: list[FFmpegMacComponent], runtime: list[FFmpegMacRuntime], folder: Path
) -> None:
    """Every text's bytes against the lock; the folder holds EXACTLY the lock's texts."""
    expected: dict[str, str] = {}
    for row in (*components, *runtime):
        for text in row["texts"]:
            if expected.setdefault(text["path"], text["sha256"]) != text["sha256"]:
                raise ValueError(f"FFmpeg lock: text {text['path']} carries two digests")
    for name, digest in expected.items():
        path = folder / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"FFmpeg lock: macOS text missing/unsafe: {name}")
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError(f"FFmpeg lock: macOS text sha256 mismatch: {name}")
        try:
            data.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(f"FFmpeg lock: macOS text is not strict UTF-8: {name}") from error
    actual = {path.name for path in folder.iterdir()} if folder.is_dir() else set()
    if actual != set(expected):
        raise ValueError(
            "FFmpeg lock: macOS text directory differs from lock; "
            f"unlisted {sorted(actual - set(expected))}, missing {sorted(set(expected) - actual)}"
        )


def _validate_macos_ffmpeg_lock(value: dict[str, object], texts: Path) -> FFmpegMacLock:
    """Validate the macOS lock (:class:`FFmpegMacLock`), its census rows against ``texts``."""
    data = _ffmpeg_fields(value, set(FFmpegMacLock.__annotations__), "macOS document")
    if type(data["schema_version"]) is not int or data["schema_version"] != 2:
        raise ValueError("FFmpeg lock: unsupported schema_version")
    if type(data["size_bytes"]) is not int or data["size_bytes"] <= 0:
        raise ValueError("FFmpeg lock: invalid size_bytes")
    for key in set(FFmpegMacLock.__annotations__) - {
        "schema_version",
        "size_bytes",
        "census",
        "build_script",
        "extract_members",
        "components",
        "excluded",
        "toolchain",
        "toolchain_runtime",
    }:
        _ffmpeg_text(data[key], key)
    text = cast(dict[str, str], data)
    if text["provider"] != FFMPEG_MACOS_PROVIDER:
        raise ValueError("FFmpeg lock: the macOS provider must be the owner's fork")
    script = _ffmpeg_fields(
        data["build_script"], set(FFmpegBuildScript.__annotations__), "build_script"
    )
    if script["repository"] != FFMPEG_MACOS_BUILD_SCRIPT:
        raise ValueError("FFmpeg lock: invalid build script repository")
    if not isinstance(script["commit"], str) or not re.fullmatch(r"[0-9a-f]{40}", script["commit"]):
        raise ValueError("FFmpeg lock: invalid build script commit")
    _check_ffmpeg_asset_url(text["asset_url"])
    digest = text["github_sha256"]
    if not re.fullmatch(r"[0-9a-f]{64}", digest) or digest != text["seat_sha256"]:
        raise ValueError("FFmpeg lock: sha256 readings differ or are not 64 hex digits")
    build_commit = text["build_repository_commit"]
    if not re.fullmatch(r"[0-9a-f]{40}", build_commit):
        raise ValueError("FFmpeg lock: invalid build repository commit")
    commit, version = text["ffmpeg_commit"], text["version"]
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("FFmpeg lock: invalid FFmpeg commit")
    if not re.match(r"n9\.", version):
        raise ValueError("FFmpeg lock: FFmpeg major must be 9")
    version_commit = re.fullmatch(r"n9\.\d+\.\d+-\d+-g([0-9a-f]{7,40})-\d{8}", version)
    if version_commit is None or not commit.startswith(version_commit.group(1)):
        raise ValueError("FFmpeg lock: version hash differs from the FFmpeg commit")
    if text["ffmpeg_ref"] != "release/9.0":
        raise ValueError("FFmpeg lock: FFmpeg ref must be release/9.0")
    if text["ffmpeg_repository"] != "https://github.com/FFmpeg/FFmpeg.git":
        raise ValueError("FFmpeg lock: FFmpeg repository must be the recipe's GitHub mirror")
    if text["licence"] != "GPL-3.0-or-later":
        raise ValueError("FFmpeg lock: combined build must be GPL-3.0-or-later")
    if data["extract_members"] != [*(f"bin/{tool}" for tool in FFMPEG_MACOS_TOOLS), "LICENSE.txt"]:
        raise ValueError("FFmpeg lock: extract_members must name only the two tools and licence")
    # The fork names the archive from the build's describe token (the version without
    # its date): a Windows-shaped root, name or URL can never pass for the macOS asset.
    root = text["archive_root"]
    if root != f"ffmpeg-{version[:-9]}-macos-arm64-gpl-9.0":
        raise ValueError("FFmpeg lock: archive_root must be the macOS arm64 asset of version")
    if text["asset_name"] != root + ".zip":
        raise ValueError("FFmpeg lock: asset name must match archive_root")
    provider = text["provider"]
    expected_url = (
        f"https://github.com/{provider}/releases/download/{text['release_tag']}/{root}.zip"
    )
    if text["asset_url"] != expected_url and not (
        _TEST_ALLOW_FILE_URLS and urlsplit(text["asset_url"]).scheme == "file"
    ):
        raise ValueError("FFmpeg lock: asset URL must match provider/release/asset")
    if text["source_record_url"] != f"https://github.com/{provider}/tree/{build_commit}":
        raise ValueError(
            "FFmpeg lock: source record URL must match provider/build commit tree root"
        )
    if not re.fullmatch(
        rf"https://github\.com/{re.escape(provider)}/actions/runs/[0-9]+", text["build_run_url"]
    ):
        raise ValueError("FFmpeg lock: build run URL must name a run of the provider")
    if not re.fullmatch(
        rf"ffmpeg-9\.0-g{commit[:8]}-macos-arm64-nozvbi-{build_commit[:7]}", text["release_tag"]
    ):
        raise ValueError("FFmpeg lock: release tag must name FFmpeg and build commits")
    problem = _macos_configure_problem(text["configure_line"], version)
    if problem is not None:
        raise ValueError(f"FFmpeg lock: {problem}")
    if text["macos_deployment_target"] != FFMPEG_MACOS_DEPLOYMENT_TARGET:
        raise ValueError("FFmpeg lock: the macOS deployment target must be 14.0")
    if text["runner_label"] != FFMPEG_MACOS_RUNNER_LABEL:
        raise ValueError("FFmpeg lock: the runner label must be macos-26")
    if not re.fullmatch(r"[0-9]{8}\.[0-9]+\.[0-9]+", text["runner_image_version"]):
        raise ValueError("FFmpeg lock: invalid runner_image_version")
    excluded = data["excluded"]
    if not isinstance(excluded, list):
        raise ValueError("FFmpeg lock: components/excluded must be lists")
    stages: set[str] = set()
    for item in excluded:
        row = _ffmpeg_fields(item, set(FFmpegExcluded.__annotations__), "excluded stage")
        for key in row:
            _ffmpeg_text(row[key], f"excluded {key}")
        stage = cast(str, row["stage"])
        if not re.fullmatch(r"SKIP_[A-Z0-9_]+", stage):
            raise ValueError("FFmpeg lock: invalid excluded stage (a recipe SKIP_ switch)")
        if stage in stages:
            raise ValueError("FFmpeg lock: duplicate excluded stage")
        if row["status"] != "not-built(disabled)":
            raise ValueError("FFmpeg lock: excluded status must be not-built(disabled)")
        stages.add(stage)
    if not {"SKIP_ZVBI", "SKIP_DECKLINK"} <= stages:
        raise ValueError("FFmpeg lock: SKIP_ZVBI and SKIP_DECKLINK must be excluded")
    if stages != FFMPEG_MACOS_EXCLUDED_STAGES:
        raise ValueError(
            "FFmpeg lock: excluded stages must be exactly the recipe's component skips; "
            f"missing {sorted(FFMPEG_MACOS_EXCLUDED_STAGES - stages)}, "
            f"unknown {sorted(stages - FFMPEG_MACOS_EXCLUDED_STAGES)}"
        )
    if data["census"] == "pending":
        if (
            data["components"] != []
            or data["toolchain_runtime"] != []
            or data["toolchain"] is not None
        ):
            raise ValueError(
                "FFmpeg lock: census pending: components, toolchain and toolchain_runtime stay "
                "empty"
            )
        return cast(FFmpegMacLock, data)
    if not isinstance(data["census"], dict):
        raise ValueError("FFmpeg lock: census must be pending or a complete census object")
    _macos_census_source(data)
    components = _macos_census_components(data, text["configure_line"])
    toolchain = _macos_census_toolchain(data)
    runtime = _macos_census_runtime(data, toolchain)
    _macos_census_texts(components, runtime, texts)
    return cast(FFmpegMacLock, data)


@overload
def validate_ffmpeg_lock(
    value: object,
    *,
    component_texts_path: Path | None = ...,
    platform: Literal["win32"] = ...,
) -> FFmpegLock: ...


@overload
def validate_ffmpeg_lock(
    value: object,
    *,
    component_texts_path: Path | None = ...,
    platform: Literal["darwin"],
) -> FFmpegMacLock: ...


@overload
def validate_ffmpeg_lock(
    value: object,
    *,
    component_texts_path: Path | None = ...,
    platform: str,
) -> FFmpegLock | FFmpegMacLock: ...


def validate_ffmpeg_lock(
    value: object,
    *,
    component_texts_path: Path | None = None,
    platform: str = "win32",
) -> FFmpegLock | FFmpegMacLock:
    """Validate archive identity, source rows and two-way configure-flag coverage.

    Stage licence identities must be seat-verified and their expressions must
    have a compatible selection. An explicit "no" compatibility verdict is
    refused by artifact notices when bundled.
    Static runtime rows require compatible SPDX expressions, toolchain/source
    bindings and nonempty text identities. Component texts are byte-checked here
    against the dedicated directory, including exact filename set equality and
    strict UTF-8 or a declared, lossless encoding from the closed set, with
    consistent declarations across references and no C1 controls in transcodes.
    Declarations on already-valid UTF-8 texts are refused;
    notices checks text identity again at rendering.
    ``configure_flag`` is null for dependencies or a list, since some stages
    contribute several switches (for example both opencore-amr codecs).

    ``platform`` selects the lock (WP6.5): ``"win32"`` (the default) the Windows lock,
    whose document carries no ``platform`` field and whose rules are unchanged;
    ``"darwin"`` the macOS lock (:class:`FFmpegMacLock`), whose ``platform`` must read
    ``macos-arm64``. A lock of the other platform is refused before any other rule.

    Args:
        value: The decoded lock document.
        component_texts_path: Directory containing exactly the component texts; None
            reads the platform's folder (:data:`FFMPEG_COMPONENT_TEXTS_PATH`, or
            :data:`FFMPEG_MACOS_TEXTS_PATH` for ``darwin``) at call time.
        platform: The ``sys.platform`` value the lock is for.

    Returns:
        The same document, with its complete schema validated.

    Raises:
        ValueError: The schema, pin, hashes or configure coverage is inconsistent, or the
            lock is not the named platform's.
    """
    if platform == "darwin":
        if not isinstance(value, dict) or value.get("platform") != FFMPEG_MACOS_PLATFORM:
            raise ValueError(f"FFmpeg lock: not a macOS lock (platform {FFMPEG_MACOS_PLATFORM!r})")
        return _validate_macos_ffmpeg_lock(
            cast(dict[str, object], value),
            FFMPEG_MACOS_TEXTS_PATH if component_texts_path is None else component_texts_path,
        )
    if platform != "win32":
        raise ValueError(f"FFmpeg lock: no FFmpeg lock for platform {platform!r}")
    if isinstance(value, dict) and "platform" in value:
        raise ValueError(f"FFmpeg lock: a {value['platform']!r} lock is not the Windows lock")
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
    if (
        re.fullmatch(
            rf"ffmpeg-9\.0-g{commit[:8]}-nozvbi-{cast(str, data['build_repository_commit'])[:7]}",
            cast(str, data["release_tag"]),
        )
        is None
    ):
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
    if any(
        isinstance(row, dict)
        and row.get("stage") == "scripts.d/50-zvbi.sh"
        and row.get("status") != "not-built(disabled)"
        for row in excluded
    ):
        raise ValueError("FFmpeg lock: zvbi exclusion status must be not-built(disabled)")
    stages: set[str] = set()
    names: set[str] = set()
    covered: set[str] = set()
    for item in components:
        component = _ffmpeg_component_fields(item)
        _ffmpeg_source(component)
        _ffmpeg_component_obligations(component)
        stage = _ffmpeg_text(component["stage"], "component stage")
        name = _ffmpeg_text(component["name"], "component name")
        via = component.get("via")
        if via is not None and (
            via != "shaderc git-sync-deps"
            or stage != "scripts.d/47-vulkan/50-shaderc.sh"
            or not any(
                isinstance(parent, dict)
                and parent.get("name") == "shaderc"
                and parent.get("stage") == stage
                for parent in components
            )
        ):
            raise ValueError("FFmpeg lock: invalid component via")
        if (stage in stages and via is None) or name in names:
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
            source = _ffmpeg_component_fields(extra, extra=True)
            _ffmpeg_source(source)
            _ffmpeg_component_obligations(source)
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
    _ffmpeg_component_texts(
        cast(list[FFmpegComponent], components),
        FFMPEG_COMPONENT_TEXTS_PATH if component_texts_path is None else component_texts_path,
    )
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


def load_macos_ffmpeg_lock() -> FFmpegMacLock:
    """Read and validate the macOS release pin (``ffmpeg-macos.lock.json``).

    Returns:
        The verified-schema macOS lock document.

    Raises:
        ValueError: The document is invalid or not a macOS lock.
        OSError: The document cannot be read.
    """
    return validate_ffmpeg_lock(
        json.loads(FFMPEG_MACOS_LOCK_PATH.read_text(encoding="utf-8")), platform="darwin"
    )


def _ffmpeg_archive_members(
    archive: zipfile.ZipFile, lock: FFmpegLock | FFmpegMacLock
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


def _macos_archive_members(
    archive: zipfile.ZipFile, lock: FFmpegMacLock
) -> dict[str, zipfile.ZipInfo]:
    """The shared inventory, then the macOS layout rule: every member under the root.

    :func:`_ffmpeg_archive_members` (shared with Windows, unchanged) inspects every member
    and finds the three to extract; the macOS path additionally refuses any member,
    extracted or not, that does not lie under ``<archive_root>/`` (the fork packages ONE
    root folder; a stray top-level member means the asset is not the recipe's zip).
    """
    found = _ffmpeg_archive_members(archive, lock)
    prefix = lock["archive_root"] + "/"
    outside = [info.orig_filename for info in archive.infolist()]
    outside = [name for name in outside if not name.startswith(prefix)]
    if outside:
        raise ValueError(f"FFmpeg archive: member(s) outside the archive root: {outside[:5]}")
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


def _download_ffmpeg(url: str, sha256: str, out: Path, lock: FFmpegLock | FFmpegMacLock) -> Path:
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


def _check_ffmpeg_toolchain_markers(path: Path, lock: FFmpegLock) -> None:
    # The overlap retains complete markers (including the GCC version delimiter)
    # even when any byte falls across a read boundary. Never load the 166 MB tool.
    toolchain = lock["toolchain"]
    gcc = toolchain["gcc"]
    gcc_marker = f"GCC: ({gcc['build']}) {gcc['version']}".encode("ascii")
    markers = {"GCC: " + gcc["version"]: re.compile(re.escape(gcc_marker) + rb"[\x00\r\n \t]")}
    if {"--enable-librav1e", "--enable-librsvg"} & set(lock["configure_line"].split()):
        rust_marker = f"/rustc/{toolchain['rustc']['commit']}/"
        markers[rust_marker] = re.compile(re.escape(rust_marker.encode("ascii")))
    overlap = max(len(gcc_marker) + 1, 48)
    tail = b""
    with path.open("rb") as stream:
        while markers and (chunk := stream.read(1024 * 1024)):
            block = tail + chunk
            markers = {
                label: pattern for label, pattern in markers.items() if not pattern.search(block)
            }
            tail = block[-overlap:]
    if markers:
        raise ValueError(f"{path.name}: missing " + ", ".join(markers) + " toolchain marker")


_FFMPEG_BARE_VERSION = re.compile(
    rb"(?<![\x20-\x7e])(?:n[0-9]{1,5}\.[0-9]{1,5}|N-[0-9]{1,10}-g[0-9a-f]"
    rb"|git-[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9a-f]"
    rb"|[0-9]{1,5}\.[0-9]{1,5}(?:\.[0-9]{1,5})?(?:-[!-~]{0,128})?-[0-9]{8}(?![0-9]))"
)
"""Where ``FFMPEG_VERSION`` begins as a C string of its own (A3-F2: detected, then judged).

Every form ``ffbuild/version.sh`` (at ``b204e94e``) can produce, any major, with or without
``-<extra-version>``: a release tag describe (``n9.0.2-47-g<hash>``, ``n8.0.1``), master's
``N-<count>-g<hash>``, a shallow clone's ``git-YYYY-MM-DD-<hash>``, and a numeric RELEASE /
VERSION file followed by an extra-version date (``9.0.1-20261110``). Only the START is
matched, after a byte that is not printable ASCII (or at the file start); the candidate is
then the WHOLE C string around it (:func:`_c_string`), so a trailing word, a control byte or
a missing NUL makes it another string, never the token. A bare numeric ``x.y.z`` without
that date cannot be told apart from another library's version string; the banner form
(:data:`_FFMPEG_BANNER_VERSION`) sees it.
"""

_FFMPEG_BANNER_VERSION = re.compile(
    rb"(?i:ffmpeg) version (?=[0-9]|n[0-9]|N-[0-9]|git-[0-9]|[0-9a-f]{7,40}(?![0-9A-Za-z]))"
)
"""libav*'s ``av_*_ffversion[] = "FFmpeg version " FFMPEG_VERSION`` arrays (``version.c``).

They are ``const char[]`` data: the byte BEFORE them can be anything (a real arm64 ffmpeg
has them after ``\\xff\\xff\\xff\\xff``, ``CJQ`` and table bytes), so their start is not
judged; the token runs from the end of this prefix to the array's terminating NUL, judged
whole (:func:`_c_string_end`). The token must start as one of version.sh's forms does (a
digit, n<digit>, N-<digit>, git-<digit>, or a bare describe hash), so prose such as
libavutil's "Update your FFmpeg version to the newest one" is not a version.
"""

_FFMPEG_CONFIGURE_SWITCH = re.compile(
    rb"(?<![^\x00 ])(?:--(?:enable|disable)-(?:gpl|version3|nonfree|libx26[45])(?![^\x00 =])"
    rb"|(?:--)?(?:extra[-_]version|pkg[-_]config[-_]flags)=)"
)
"""An FFmpeg-only configure switch as a whole space-separated token (A4-F2's detector).

A C string carrying one is an FFmpeg configuration candidate, whatever its first argument
(``cc=clang`` included): the licence switches, the libx264 / libx265 switches, and
``extra-version`` / ``pkg-config-flags`` in every spelling configure's ``*)`` branch takes.
Other components' build configurations carry none (a real arm64 ffmpeg holds libvpx's
``--prefix=... --disable-unit-tests``, and an encoder's help text names its own
``--enable-rate-guide-deltaq``) and are left alone by this stated rule. LIMIT: an FFmpeg
configuration with none of these switches (an LGPL build without the recipe's flags) is not
seen; that build's own ``FFmpeg version`` arrays still are.
"""

_FFMPEG_STRING_LIMIT = 8192
"""The longest C string (bytes, without its NUL) a version or configuration candidate may be.

A candidate whose C string has no NUL within this bound on either side is OVERSIZED and
refused, never truncated into a plausible prefix. The recipe's configure line is under
1 KiB.
"""

_MH_EXECUTE = 2
_PLATFORM_MACOS = 1
_LC_VERSION_MIN_COMMANDS = frozenset({0x24, 0x25, 0x2F, 0x30})
"""LC_VERSION_MIN_MACOSX / _IPHONEOS / _TVOS / _WATCHOS: the pre-LC_BUILD_VERSION forms."""

_MACOS_TOOL_COMMANDS_LIMIT = 1024 * 1024
"""The largest load-command table a tool may declare (FFmpeg's is a few KiB)."""


def _macos_version_word(text: str) -> int | None:
    """``"14.0"`` as Mach-O's ``xxxx.yy.zz`` nibble word, or None when not a version."""
    match = re.fullmatch(r"([0-9]{1,5})\.([0-9]{1,3})(?:\.([0-9]{1,3}))?", text)
    if match is None:
        return None
    major, minor, patch = (int(part or 0) for part in match.groups())
    if major > 0xFFFF or minor > 0xFF or patch > 0xFF:
        return None
    return major << 16 | minor << 8 | patch


def _macos_version_text(word: int) -> str:
    patch = word & 0xFF
    return f"{word >> 16}.{word >> 8 & 0xFF}" + (f".{patch}" if patch else "")


def _macos_tool_image(path: Path) -> bytes:
    """A tool's Mach-O header plus its WHOLE declared load-command table, bounded.

    The table is read only when ``sizeofcmds`` lies within the file and within
    :data:`_MACOS_TOOL_COMMANDS_LIMIT`; otherwise the 32-byte header alone is returned,
    which :func:`_macos_tool_problem` refuses as a malformed table.
    """
    size = path.stat().st_size
    with path.open("rb") as stream:
        image = stream.read(32)
        if len(image) == 32 and image[:4] == _MACHO_MAGIC_64:
            (sizeofcmds,) = struct.unpack_from("<I", image, 20)
            if 32 + sizeofcmds <= size and sizeofcmds <= _MACOS_TOOL_COMMANDS_LIMIT:
                image += stream.read(sizeofcmds)
    return image


def _macos_tool_problem(image: bytes, deployment_target: str) -> str | None:
    """Why a tool is not a thin arm64 macOS executable built for the lock's target, or None.

    ``image`` is the header and the whole load-command table (:func:`_macos_tool_image`).
    The table is parsed and bounded by :func:`_macho_parse` (``sizeofcmds`` inside the
    image, every ``cmdsize`` at least 8, a multiple of 8 and inside the table, the commands
    exactly filling it). Then exactly ONE ``LC_BUILD_VERSION`` (well formed: ``cmdsize`` =
    24 + 8 per tool entry) with platform macOS and ``minos`` EQUAL to
    ``deployment_target`` (the recipe sets ``MACOSX_DEPLOYMENT_TARGET`` to exactly that
    value, so an equal ``minos`` is the evidence that the binary is the recipe's build; a
    lower one would also run, but would contradict the lock's record), and no
    ``LC_VERSION_MIN_*`` command (the older form, refused: the recipe's toolchain emits
    ``LC_BUILD_VERSION`` only, and two deployment records could disagree).
    """
    if len(image) < 32 or image[:4] != _MACHO_MAGIC_64:
        return "not a thin arm64 Mach-O executable (magic)"
    cputype, _subtype, filetype = struct.unpack_from("<iiI", image, 4)
    if cputype != _MACHO_CPU_ARM64 or filetype != _MH_EXECUTE:
        return f"not a thin arm64 Mach-O executable (cpu {cputype:#x}, filetype {filetype})"
    parsed = _macho_parse(image)
    if parsed is None:
        return "malformed or truncated Mach-O load-command table"
    if any(cmd in _LC_VERSION_MIN_COMMANDS for cmd, _ in parsed.commands):
        return "an LC_VERSION_MIN_* command is present (LC_BUILD_VERSION only)"
    builds = [body for cmd, body in parsed.commands if cmd == _LC_BUILD_VERSION]
    if len(builds) != 1:
        return f"expected exactly one LC_BUILD_VERSION, found {len(builds)}"
    body = builds[0]
    if len(body) < 24:
        return "malformed LC_BUILD_VERSION"
    platform, minos, _sdk, ntools = struct.unpack_from("<IIII", body, 8)
    if len(body) != 24 + 8 * ntools:
        return "malformed LC_BUILD_VERSION (cmdsize differs from its tool entries)"
    if platform != _PLATFORM_MACOS:
        return f"LC_BUILD_VERSION platform {platform} is not macOS"
    expected = _macos_version_word(deployment_target)
    if expected is None or minos != expected:
        return (
            f"LC_BUILD_VERSION minos {_macos_version_text(minos)} differs from the lock's "
            f"deployment target {deployment_target}"
        )
    return None


class _ScanBlock(NamedTuple):
    """One block of :func:`_scan_blocks`: judge the positions in ``[first, stop)``."""

    data: bytes
    first: int
    stop: int
    at_start: bool
    """``data[0]`` is the file's first byte."""
    at_end: bool
    """``data`` ends where the file ends."""


def _scan_blocks(path: Path, context: int) -> Iterator[_ScanBlock]:
    """Read ``path`` in 1 MiB blocks; every byte position is judged in exactly one block.

    A judged position has at least ``context`` bytes of the block before it (or the file
    start) and at least ``context`` after it (or the file end), so a bounded C string
    around it is always seen WHOLE: each block carries the previous block's unjudged tail
    plus ``context`` bytes of look-behind.
    """
    size = 1024 * 1024
    if not 0 < context < size // 2:
        raise ValueError(f"scan context {context} out of range")
    with path.open("rb") as stream:
        data, first, at_start = stream.read(size), 0, True
        while True:
            following = stream.read(size)
            stop = len(data) if not following else len(data) - context
            yield _ScanBlock(data, first, max(first, stop), at_start, not following)
            if not following:
                return
            keep = max(0, stop - context)
            data, first, at_start = data[keep:] + following, stop - keep, at_start and keep == 0


def _c_string_start(block: _ScanBlock, position: int) -> int | None:
    """Where the C string holding ``position`` begins, or None when oversized.

    The byte after the previous NUL, or the file start; None when neither lies within
    :data:`_FFMPEG_STRING_LIMIT` bytes before ``position``.
    """
    low = max(0, position - _FFMPEG_STRING_LIMIT - 1)
    nul = block.data.rfind(b"\0", low, position)
    if nul >= 0:
        return nul + 1
    return 0 if block.at_start and low == 0 else None


def _c_string_end(block: _ScanBlock, start: int) -> tuple[bytes, str]:
    """``(content, problem)`` of the C string from ``start``: problem ``""`` when complete.

    Complete = a NUL within :data:`_FFMPEG_STRING_LIMIT` bytes; ``"unterminated"`` when the
    file ends first; ``"oversized"`` otherwise (content then truncated at the bound).
    """
    high = start + _FFMPEG_STRING_LIMIT + 1
    nul = block.data.find(b"\0", start, high)
    if nul >= 0:
        return block.data[start:nul], ""
    if block.at_end and len(block.data) < high:
        return block.data[start:], "unterminated"
    return block.data[start : start + _FFMPEG_STRING_LIMIT], "oversized"


def _c_string(block: _ScanBlock, position: int) -> tuple[bytes, str]:
    """``(content, problem)`` of the WHOLE C string holding ``position`` (both ends judged)."""
    start = _c_string_start(block, position)
    if start is None:
        low = max(0, position - _FFMPEG_STRING_LIMIT)
        return block.data[low : low + _FFMPEG_STRING_LIMIT], "oversized"
    return _c_string_end(block, start)


def _candidate_text(content: bytes, problem: str) -> str:
    """A candidate as printable ASCII for an error message (``problem`` appended)."""
    if len(content) > 96:  # both ends: a difference is often at the end
        content = content[:60] + b"..." + content[-32:]
    return repr(content.decode("ascii", "backslashreplace")) + (f" ({problem})" if problem else "")


def _macos_ffmpeg_version(path: Path, lock: FFmpegMacLock) -> str:
    """Read the F3b version token and the configure line from a tool's bytes; never run it.

    FFmpeg compiles ``FFMPEG_VERSION`` and ``FFMPEG_CONFIGURATION`` in as plain C strings
    (``fftools/opt_common.c`` prints them through the ``"%s version %s"`` format;
    ``av_version_info`` and the ``*_configuration`` functions return them; each library's
    ``version.c`` carries ``"FFmpeg version " FFMPEG_VERSION`` as a ``const char[]``).
    DETECTION is separate from validation (A3-F2), and every candidate is a COMPLETE C
    string compared in full (A4-F3): a NUL (or the file start) before it, a NUL after it,
    at most :data:`_FFMPEG_STRING_LIMIT` bytes, never a printable prefix. Version
    candidates: every C string that begins with a version.sh form
    (:data:`_FFMPEG_BARE_VERSION`, judged whole), and the token part of every
    ``FFmpeg version`` array (:data:`_FFMPEG_BANNER_VERSION`, from the prefix to its NUL).
    Configuration candidates: every C string carrying an FFmpeg-only configure switch
    (:data:`_FFMPEG_CONFIGURE_SWITCH`), whatever its first argument (A4-F2); it must also
    be valid UTF-8 (configure prints the arguments as given, so a UTF-8 path is part of ONE
    string; undecodable evidence is refused as such). Then exactly ONE distinct version
    candidate must exist and be the lock's token, complete; and exactly one configuration
    candidate, the lock's configure line, complete. An unterminated (at the file end) or
    oversized candidate is never the token or the line. Conflicting evidence is refused,
    never filtered away. Read in 1 MiB blocks (:func:`_scan_blocks`). LIMITS: an FFmpeg
    configuration with none of the FFmpeg-only switches is not seen (its build's version
    arrays still are), nor is a bare ``x.y.z`` version with no extra-version outside the
    ``FFmpeg version`` arrays.

    Raises:
        RuntimeError: The version candidates or the configuration differ from the lock.
        OSError: The file cannot be read.
    """
    body = lock["configure_line"].removeprefix("configuration: ").encode("utf-8")
    versions: set[tuple[bytes, str]] = set()
    configurations: set[tuple[bytes, str]] = set()
    for block in _scan_blocks(path, _FFMPEG_STRING_LIMIT + 32):
        # Matches are searched from ``first`` to the block's end (a lookahead must see the
        # real next byte) and kept when they START before ``stop``.
        for match in _FFMPEG_BARE_VERSION.finditer(block.data, block.first):
            if match.start() < block.stop:
                versions.add(_c_string(block, match.start()))
        for match in _FFMPEG_BANNER_VERSION.finditer(block.data, block.first):
            if match.start() < block.stop:
                versions.add(_c_string_end(block, match.end()))
        for match in _FFMPEG_CONFIGURE_SWITCH.finditer(block.data, block.first):
            if match.start() >= block.stop:
                continue
            content, problem = _c_string(block, match.start())
            if not problem:
                try:
                    content.decode("utf-8")
                except UnicodeDecodeError:
                    problem = "not UTF-8"
            configurations.add((content, problem))
    if versions != {(lock["version"].encode("ascii"), "")}:
        found = sorted(_candidate_text(*candidate) for candidate in versions)
        raise RuntimeError(f"{path.name}: version token(s) {found} differ from the lock")
    if configurations != {(body, "")}:
        found = sorted(_candidate_text(*candidate) for candidate in configurations)
        raise RuntimeError(
            f"{path.name}: configuration differs from the lock "
            f"({len(configurations)} distinct configuration string(s): {found})"
        )
    return f"{path.name} version {lock['version']} (read from the binary)"


def _check_macos_toolchain_marker(path: Path, lock: FFmpegMacLock) -> None:
    r"""The Apple analogue of :func:`_check_ffmpeg_toolchain_markers`: the census compiler.

    FFmpeg's configure records ``$cc --version``'s first line as ``CC_IDENT`` and
    ``fftools/opt_common.c`` prints it through ``"%sbuilt with %s\n"`` (the run's
    ``built with Apple clang version ...`` line), so the toolchain object's ``compiler``
    must occur as a COMPLETE C string: a non-printable byte (or the file start) before it
    and a NUL after it. Read in 1 MiB blocks (:func:`_scan_blocks`); never run. A lock
    whose census is pending carries no toolchain and is not checked (``build()`` refuses
    ``--notices`` / ``--zip`` for it, so such a bundle is never released).

    Raises:
        ValueError: The marker is absent.
        OSError: The file cannot be read.
    """
    toolchain = lock["toolchain"]
    if toolchain is None:
        return
    marker = toolchain["compiler"].encode("ascii")
    pattern = re.compile(rb"(?<![\x20-\x7e])" + re.escape(marker) + rb"\x00")
    for block in _scan_blocks(path, len(marker) + 2):
        for match in pattern.finditer(block.data, block.first):
            if match.start() < block.stop:
                return
    raise ValueError(f"{path.name}: missing the Apple toolchain marker {toolchain['compiler']!r}")


def _bundle_macos_ffmpeg(
    destination: Path,
    *,
    out: Path,
    url: str,
    sha256: str,
    verified_hashes: set[str] | None,
) -> list[tuple[Path, str]]:
    """``bundle_ffmpeg``'s darwin path: verify, stage, check, then place into the ``.app``.

    The order of the Windows path (the pin, then the download verified before the archive
    is opened, then every member inspected) with these macOS differences: every member
    must lie under ``<archive_root>/`` (:func:`_macos_archive_members`); the tools are
    the Mach-O ``bin/ffmpeg`` / ``bin/ffprobe``; they are STAGED under
    ``<out>/ffmpeg/<archive_root>.verified`` and given mode 0755 there (``zipfile`` drops
    the archive's modes, G2a-F4), the texts 0644; each must be a thin arm64 executable
    whose load commands record the lock's deployment target (:func:`_macos_tool_problem`);
    and their version and configuration are read from their bytes
    (:func:`_macos_ffmpeg_version`), never by running them (the smoke runs them on the
    Mac runner). Only after both pass are they placed by
    :func:`place_macos_tools` (tools to ``Contents/MacOS``, texts to ``Contents/Resources``)
    before :func:`seal_macos_bundle`. Each tool must also carry the census's Apple
    toolchain marker (:func:`_check_macos_toolchain_marker`, the Windows
    :func:`_check_ffmpeg_toolchain_markers` analogue) before anything is placed.
    """
    lock = load_macos_ffmpeg_lock()
    destination = destination.resolve()
    bundle = destination.parent.parent
    if (
        destination.name != "MacOS"
        or destination.parent.name != "Contents"
        or bundle.suffix != ".app"
    ):
        raise ValueError(f"macOS FFmpeg goes into Contents/MacOS of a built .app: {destination}")
    texts = ("ffmpeg-LICENSE.txt", "ffmpeg-BUILD.txt")
    for target in (
        *(destination / tool for tool in FFMPEG_MACOS_TOOLS),
        *(bundle / "Contents" / "Resources" / name for name in texts),
    ):
        if target.is_symlink() or target.exists():
            raise ValueError(f"tool placement: {target} already exists")
    archive_path = _download_ffmpeg(url, sha256, out.resolve(), lock)
    staging = archive_path.parent / (lock["archive_root"] + ".verified")
    if staging.is_symlink():
        raise ValueError("FFmpeg staging: unsafe output link")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir()
    tool_hashes: set[str] = set()
    with zipfile.ZipFile(archive_path) as archive:
        members = _macos_archive_members(archive, lock)
        targets = {
            **{f"bin/{tool}": staging / tool for tool in FFMPEG_MACOS_TOOLS},
            "LICENSE.txt": staging / "ffmpeg-LICENSE.txt",
        }
        for name, path in targets.items():
            digest = hashlib.sha256()
            with archive.open(members[name]) as source, path.open("wb") as output:
                while chunk := source.read(1024 * 1024):
                    digest.update(chunk)
                    output.write(chunk)
            path.chmod(0o644 if name == "LICENSE.txt" else 0o755)
            if name != "LICENSE.txt":
                tool_hashes.add(digest.hexdigest())
    result = []
    for tool in FFMPEG_MACOS_TOOLS:
        problem = _macos_tool_problem(
            _macos_tool_image(staging / tool), lock["macos_deployment_target"]
        )
        if problem is not None:
            raise ValueError(f"{tool}: {problem}")
        result.append((destination / tool, _macos_ffmpeg_version(staging / tool, lock)))
        _check_macos_toolchain_marker(staging / tool, lock)
    record = staging / "ffmpeg-BUILD.txt"
    record.write_text(
        "\n".join(
            [
                f"Provider: {lock['provider']}",
                f"Build script: {lock['build_script']['repository']} @ "
                f"{lock['build_script']['commit']}",
                f"Release tag: {lock['release_tag']}",
                f"Asset: {lock['asset_name']}",
                f"SHA256: {lock['github_sha256']}",
                f"FFmpeg version: {lock['version']}",
                f"FFmpeg commit: {lock['ffmpeg_commit']}",
                f"FFmpeg ref: {lock['ffmpeg_ref']}",
                f"Build repository commit: {lock['build_repository_commit']}",
                f"Build run: {lock['build_run_url']}",
                f"Per-component source recipes: {lock['source_record_url']}",
                "Per-component pins and licence readings: "
                "tools/package/ffmpeg-macos.lock.json in Clearwater source",
                f"macOS deployment target: {lock['macos_deployment_target']}",
                f"Runner: {lock['runner_label']} image {lock['runner_image_version']}",
                lock["configure_line"],
                "",
            ]
        ),
        encoding="utf-8",
    )
    record.chmod(0o644)
    place_macos_tools(
        bundle,
        {tool: staging / tool for tool in FFMPEG_MACOS_TOOLS},
        {name: staging / name for name in texts},
    )
    if verified_hashes is not None:
        verified_hashes.update(tool_hashes)
    return result


def bundle_ffmpeg(
    destination: Path,
    *,
    out: Path,
    url: str,
    sha256: str,
    verified_hashes: set[str] | None = None,
    platform: str = "win32",
) -> list[tuple[Path, str]]:
    """Fetch the pinned archive, verify before opening, then copy and check its tools.

    Every archive member is inspected for unsafe paths, links and duplicates,
    including members that will not be extracted. Only the two tools and the
    GPL text are copied. The output contains a build/source provenance record.
    ``platform="darwin"`` takes the macOS lock and path (:func:`_bundle_macos_ffmpeg`);
    the default is the Windows path, unchanged.

    Args:
        destination: The built Clearwater executable's folder (on darwin the ``.app``'s
            ``Contents/MacOS``).
        out: The build output root; the archive is retained under ``ffmpeg/``.
        url: Must equal the committed lock's asset URL.
        sha256: Must equal both verified hash readings in the lock.
        verified_hashes: Optional in-memory output for extracted tool hashes, read
            from the verified archive streams. Updated only after both tools pass.
            Unextracted members and the non-native licence/build texts grant no trust.
        platform: ``"win32"`` or ``"darwin"``: whose lock and tools.

    Returns:
        The two executable paths and their checked version lines.

    Raises:
        ValueError: The pin, download, ZIP inventory or compiler markers differ, or the
            platform has no bundling path.
        RuntimeError: Either tool fails its bounded version/configuration check.
        OSError: A download, extraction or provenance write fails.
        zipfile.BadZipFile: The verified bytes are not a valid ZIP.
    """
    if platform == "darwin":
        return _bundle_macos_ffmpeg(
            destination, out=out, url=url, sha256=sha256, verified_hashes=verified_hashes
        )
    if platform != "win32":
        raise ValueError(f"no FFmpeg bundling for platform {platform!r}")
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
    _check_ffmpeg_toolchain_markers(destination / "ffmpeg.exe", lock)
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


DARWIN_ANALYSIS_SYSTEM_PATH = ("/usr/bin", "/bin", "/usr/sbin", "/sbin")
"""The system part of the macOS analysis PATH (``codesign``, ``lipo``, ``install_name_tool``)."""


def run_pyinstaller(args: Sequence[str]) -> None:
    """Run PyInstaller in this process: ``PyInstaller.__main__.run(args)``.

    Windows analysis sees only the interpreter root/DLLs, venv Scripts and
    Windows System32/root. macOS analysis (WP6.5, the AD-36 form) sees only the
    interpreter ``bin``, the venv ``bin``, ``/usr/bin``, ``/bin``, ``/usr/sbin`` and
    ``/sbin``; every ``DYLD_*`` variable is removed and the two dyld fallbacks are
    pinned to the system locations, because PyInstaller resolves Mach-O
    dependencies through macholib's ``dyld_find``, which reads them (its default
    library fallback includes ``/usr/local/lib``). PATH and the ``DYLD_*`` set are
    restored even if importing/running analysis fails. Any other platform is
    refused: Clearwater is built on Windows and macOS only.

    Args:
        args: The command line (:func:`pyinstaller_args`).

    Raises:
        BuildEnvironmentError: Windows SYSTEMROOT is unset (no safe PATH can be
            formed), or the platform is neither Windows nor macOS.
        SystemExit: PyInstaller's own exit on a failed build (non-zero status).
    """
    original = os.environ.get("PATH")
    dyld_saved: dict[str, str] | None = None
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
        elif sys.platform == "darwin":
            dyld_saved = {k: v for k, v in os.environ.items() if k.startswith("DYLD_")}
            for name in dyld_saved:
                del os.environ[name]
            os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = "/usr/lib"
            os.environ["DYLD_FALLBACK_FRAMEWORK_PATH"] = "/System/Library/Frameworks"
            os.environ["PATH"] = os.pathsep.join(
                (
                    str(Path(sys.base_prefix) / "bin"),
                    str(Path(sys.prefix) / "bin"),
                    *DARWIN_ANALYSIS_SYSTEM_PATH,
                )
            )
        else:
            raise BuildEnvironmentError(
                f"platform {sys.platform!r}: no sanitized analysis environment; "
                "Clearwater builds on Windows and macOS only (Linux is not supported)"
            )
        main = importlib.import_module("PyInstaller.__main__")
        main.run(list(args))
    finally:
        if original is None:
            os.environ.pop("PATH", None)
        else:
            os.environ["PATH"] = original
        if dyld_saved is not None:
            for name in [k for k in os.environ if k.startswith("DYLD_")]:
                del os.environ[name]
            os.environ.update(dyld_saved)


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
    if sys.platform == "darwin":
        hashes |= _macos_origin_identities()
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


# macOS origin identity (WP6.5, CHARC note 2; ledger section 6). PyInstaller rewrites
# every collected Mach-O (``set_dylib_dependency_paths``: dylib names to
# ``@rpath/<basename>``, every LC_RPATH replaced by one ``@loader_path(/..)*``), thins a
# fat input to the target slice and ad-hoc re-signs it, so a whole-file hash refuses every
# macOS build. The identity below is computed with ``struct`` only (macholib is
# darwin-only in uv.lock, so the Windows tests could not use it).

_MACHO_MAGIC_64 = b"\xcf\xfa\xed\xfe"
_MACHO_FAT_LAYOUTS = {b"\xca\xfe\xba\xbe": (">iiIII", 20), b"\xca\xfe\xba\xbf": (">iiQQII", 32)}
_MACHO_MAX_SLICES = 16
_MACHO_CPU_ARM64 = 0x0100000C
_LC_SYMTAB = 0x2
_LC_LOAD_DYLIB = 0xC
_LC_ID_DYLIB = 0xD
_LC_SEGMENT_64 = 0x19
_LC_UUID = 0x1B
_LC_CODE_SIGNATURE = 0x1D
_LC_VERSION_MIN_MACOSX = 0x24
_LC_BUILD_VERSION = 0x32
_LC_LOAD_WEAK_DYLIB = 0x80000018
_LC_RPATH = 0x8000001C
_LC_REEXPORT_DYLIB = 0x8000001F
_LC_LOAD_UPWARD_DYLIB = 0x80000023
_MACHO_LOAD_COMMANDS = frozenset(
    {_LC_LOAD_DYLIB, _LC_LOAD_WEAK_DYLIB, _LC_REEXPORT_DYLIB, _LC_LOAD_UPWARD_DYLIB}
)
_MACHO_UNKNOWN = "unknown"


class _MachO(NamedTuple):
    cputype: int
    cpusubtype: int
    filetype: int
    flags: int
    header_end: int
    commands: tuple[tuple[int, bytes], ...]


class _MachOIdentity(NamedTuple):
    canonical: tuple[object, ...]
    linkedit: bytes
    rpaths: tuple[str, ...]
    names: tuple[tuple[int, str], ...]


def _macho_slices(data: bytes) -> list[bytes]:
    """Return a Mach-O file's thin images: itself if thin 64-bit, each slice if fat."""
    if data[:4] == _MACHO_MAGIC_64:
        return [data]
    layout = _MACHO_FAT_LAYOUTS.get(data[:4])
    if layout is None or len(data) < 8:
        return []
    form, size = layout
    (count,) = struct.unpack_from(">I", data, 4)
    table_end = 8 + count * size
    if not 0 < count <= _MACHO_MAX_SLICES or table_end > len(data):
        return []
    slices = []
    for index in range(count):
        fields = struct.unpack_from(form, data, 8 + index * size)
        offset, length = int(fields[2]), int(fields[3])
        if offset < table_end or offset + length > len(data):
            return []
        slices.append(data[offset : offset + length])
    return slices


def _macho_parse(image: bytes) -> _MachO | None:
    if len(image) < 32 or image[:4] != _MACHO_MAGIC_64:
        return None
    _, cputype, cpusubtype, filetype, count, size, flags, _ = struct.unpack_from(
        "<IiiIIIII", image, 0
    )
    end = 32 + size
    if end > len(image):
        return None
    offset = 32
    commands = []
    for _ in range(count):
        if offset + 8 > end:
            return None
        cmd, cmdsize = struct.unpack_from("<II", image, offset)
        if cmdsize < 8 or cmdsize % 8 or offset + cmdsize > end:
            return None
        commands.append((cmd, image[offset : offset + cmdsize]))
        offset += cmdsize
    if offset != end:
        return None
    return _MachO(cputype, cpusubtype, filetype, flags, end, tuple(commands))


def _macho_string(body: bytes, minimum: int) -> str | None:
    if len(body) < minimum:
        return None
    (offset,) = struct.unpack_from("<I", body, 8)
    if not minimum <= offset < len(body):
        return None
    try:
        return body[offset:].split(b"\0", 1)[0].decode("utf-8")
    except UnicodeDecodeError:
        return None


def _macho_system_path(name: str) -> bool:
    """Whether PyInstaller leaves this dependency name as written (its system exemption)."""
    return (
        name.startswith("/System/")
        or (name.startswith("/usr/") and not name.startswith("/usr/local/"))
        or "/Library/Frameworks/Tcl.framework/" in name
        or "/Library/Frameworks/Tk.framework/" in name
    )


def _macho_identity(image: bytes, *, bootloader: bool = False) -> _MachOIdentity | None:
    """Normalise a thin arm64 Mach-O image to what PyInstaller does not change.

    Kept: the header's CPU type / subtype, file type and flags; every load command in
    order, byte for byte, except: LC_CODE_SIGNATURE and LC_RPATH dropped (listed apart),
    each dylib command's name reduced to its basename (system names kept whole), and
    ``__LINKEDIT``'s vmsize / filesize zeroed; every segment's file bytes (a segment that
    holds the header from its first section on, with the padding before it required zero);
    ``__LINKEDIT`` up to the code signature (returned apart), less only PROVEN alignment
    padding: fewer than 16 zero bytes between the string table's declared end and the
    signature (WP6.5 A r1 #2; every string-table byte, terminators included, stays). The
    image must END where its segments end and the signature must lie inside
    ``__LINKEDIT`` (A r1 #3: no unexplained trailing bytes). For the bootloader, also
    zeroed: LC_SYMTAB strsize, LC_UUID, the SDK of LC_BUILD_VERSION / LC_VERSION_MIN_MACOSX
    (PyInstaller's ``fix_exe_for_code_signing``, ``update_exe_identifier`` and
    ``set_macos_sdk_version``).

    Args:
        image: One thin image.
        bootloader: Apply the bootloader's three extra normalisations.

    Returns:
        The identity, or ``None`` for anything not a well-formed thin arm64 image.
    """
    parsed = _macho_parse(image)
    if parsed is None or parsed.cputype != _MACHO_CPU_ARM64:
        return None
    signature: tuple[int, int] | None = None
    strings: int | None = None
    for cmd, body in parsed.commands:
        if cmd == _LC_CODE_SIGNATURE and len(body) >= 16:
            signature = cast(tuple[int, int], struct.unpack_from("<II", body, 8))
        elif cmd == _LC_SYMTAB and len(body) >= 24:
            stroff, strsize = struct.unpack_from("<II", body, 16)
            strings = stroff + strsize
    canonical: list[object] = [
        ("header", parsed.cputype, parsed.cpusubtype, parsed.filetype, parsed.flags)
    ]
    rpaths: list[str] = []
    names: list[tuple[int, str]] = []
    linkedit = None
    end = 0
    for cmd, body in parsed.commands:
        if cmd == _LC_CODE_SIGNATURE:
            continue
        if cmd == _LC_RPATH:
            path = _macho_string(body, 12)
            if path is None:
                return None
            rpaths.append(path)
        elif cmd in _MACHO_LOAD_COMMANDS or cmd == _LC_ID_DYLIB:
            name = _macho_string(body, 24)
            if name is None:
                return None
            names.append((cmd, name))
            kept = cmd != _LC_ID_DYLIB and _macho_system_path(name)
            canonical.append(
                ("dylib", cmd, name if kept else PurePosixPath(name).name, body[12:24])
            )
        elif cmd == _LC_SEGMENT_64:
            if len(body) < 72:
                return None
            segname, _, _, fileoff, filesize, _, _, nsects, _ = struct.unpack_from(
                "<16sQQQQiiII", body, 8
            )
            stop = fileoff + filesize
            if 72 + nsects * 80 != len(body) or stop > len(image):
                return None
            end = max(end, stop)
            if segname.rstrip(b"\0") == b"__LINKEDIT":
                if linkedit is not None:
                    return None
                content = stop
                if signature is not None:
                    dataoff, datasize = signature
                    if not fileoff <= dataoff <= dataoff + datasize <= stop:
                        return None  # a signature outside __LINKEDIT is not PyInstaller's
                    content = dataoff
                if strings is not None and fileoff <= strings <= content:
                    gap = image[strings:content]
                    if len(gap) < 16 and not gap.strip(b"\0"):
                        content = strings  # alignment padding only: may go with the signature
                linkedit = image[fileoff:content]
                sizes_zeroed = body[:32] + bytes(8) + body[40:48] + bytes(8) + body[56:]
                canonical.append(("segment", sizes_zeroed))
                continue
            start = fileoff
            padding = True
            if filesize and fileoff < parsed.header_end:
                offsets = [
                    struct.unpack_from("<I", body, 72 + index * 80 + 48)[0]
                    for index in range(nsects)
                ]
                start = min((o for o in offsets if o >= parsed.header_end), default=stop)
                if start > stop:
                    return None
                padding = not image[parsed.header_end : start].strip(b"\0")
            canonical.append(
                ("segment", body, start, padding, hashlib.sha256(image[start:stop]).hexdigest())
            )
        else:
            if bootloader and cmd == _LC_SYMTAB and len(body) >= 24:
                body = body[:20] + bytes(4)
            elif bootloader and cmd == _LC_UUID and len(body) >= 24:
                body = body[:8] + bytes(16)
            elif bootloader and cmd == _LC_BUILD_VERSION and len(body) >= 24:
                body = body[:16] + bytes(4) + body[20:]
            elif bootloader and cmd == _LC_VERSION_MIN_MACOSX and len(body) >= 16:
                body = body[:12] + bytes(4) + body[16:]
            canonical.append(("command", cmd, body))
    if linkedit is None or end != len(image):
        return None
    return _MachOIdentity(tuple(canonical), linkedit, tuple(rpaths), tuple(names))


def _macho_digest(identity: _MachOIdentity) -> str:
    linkedit = hashlib.sha256(identity.linkedit).hexdigest()
    return "macho:" + hashlib.sha256(repr((identity.canonical, linkedit)).encode()).hexdigest()


def _macho_origin_identities(data: bytes) -> set[str]:
    """Identities an ORIGINAL contributes: each thin arm64 image (a fat file's arm64 slice)."""
    return {
        _macho_digest(identity)
        for image in _macho_slices(data)
        if (identity := _macho_identity(image)) is not None
    }


def _macos_origin_identities() -> set[str]:
    """Whole-file hashes and Mach-O identities of every interpreter / locked-wheel Mach-O.

    Unlike the suffix-only scan in :func:`_native_origin_hashes`, a file counts by its first
    bytes too (``.framework`` binaries carry no suffix). Locked-wheel files are verified
    against their RECORD first.

    Returns:
        ``sha256`` hex digests and ``macho:`` identities.
    """
    identities: set[str] = set()

    def head(path: Path) -> bytes:
        with path.open("rb") as stream:
            return stream.read(4)

    for path in Path(sys.base_prefix).rglob("*"):
        if path.is_file() and not path.is_symlink() and _is_native(path.name, head(path)):
            data = path.read_bytes()
            identities.add(hashlib.sha256(data).hexdigest())
            identities |= _macho_origin_identities(data)
    for dist in _locked_native_distributions():
        for entry in dist.files or ():
            path = Path(str(dist.locate_file(entry)))
            if path.is_file() and _is_native(str(entry), head(path)):
                identities.add(_record_native_hash(dist, entry))
                identities |= _macho_origin_identities(path.read_bytes())
    return identities


def macho_built_problem(data: bytes, origins: set[str], depth: int) -> str | None:
    """Say why a built Mach-O is not admitted on macOS, or ``None`` when it is.

    Admitted: a thin arm64 image whose identity (:func:`_macho_identity`) is an original's,
    whose non-system dependency names and own id are all ``@rpath/<basename>``, and whose
    LC_RPATH set is exactly ``@loader_path`` plus one ``/..`` per folder between it and the
    contents root (PyInstaller's ``target_rpath``; none at all is allowed only when no
    dependency needs ``@rpath``).

    Args:
        data: The built file's bytes.
        origins: Whole-file hashes and ``macho:`` identities of the trusted originals.
        depth: Folders between the file and the contents root (0 = directly in it).

    Returns:
        ``None`` (admitted), ``"unknown"`` (no trusted original), or the named violation.
    """
    identity = _macho_identity(data)
    if identity is None or _macho_digest(identity) not in origins:
        return _MACHO_UNKNOWN
    for cmd, name in identity.names:
        if cmd == _LC_ID_DYLIB or not _macho_system_path(name):
            rest = name.removeprefix("@rpath/")
            if rest == name or not rest or "/" in rest:
                return f"dylib name {name!r} is not @rpath/<basename>"
    expected = "@loader_path" + "/.." * depth
    needs_rpath = any(
        cmd != _LC_ID_DYLIB and not _macho_system_path(name) for cmd, name in identity.names
    )
    if identity.rpaths != (expected,) and (needs_rpath or identity.rpaths):
        return f"LC_RPATH {list(identity.rpaths)} is not the one {expected!r} of its location"
    return None


def _is_macos_bootloader(executable: Path, source: Path) -> bool:
    actual = _macho_identity(executable.read_bytes(), bootloader=True)
    if actual is None:
        return False
    for image in _macho_slices(source.read_bytes()):
        expected = _macho_identity(image, bootloader=True)
        if (
            expected is not None
            and expected.canonical == actual.canonical
            and expected.rpaths == actual.rpaths
            and actual.linkedit.startswith(expected.linkedit)
        ):
            return True
    return False


def framework_link_problem(link: PurePosixPath, target: str) -> str | None:
    """Say why a link in a macOS release is refused, or ``None`` for a framework link.

    Pure (path strings only). Admitted are exactly the links PyInstaller's
    ``collect_files_from_framework_bundles`` makes in a collected ``.framework``:
    ``<fw>/Versions/Current`` naming a sibling version folder, and a top-level
    ``<fw>/<name>`` naming ``Versions/Current/<name>``. Anything else (absolute,
    escaping, outside a ``.framework``, another shape) is refused.

    Args:
        link: The link's path relative to the release root (POSIX).
        target: The link's text as stored.

    Returns:
        ``None`` when admitted, else the reason.
    """
    if not target or target.startswith("/") or "\\" in target or ":" in target:
        return f"link target {target!r} is absolute or not POSIX"
    parts = link.parts
    tops = [index for index, part in enumerate(parts[:-1]) if part.endswith(".framework")]
    if not tops:
        return "link outside a .framework"
    inner = parts[tops[-1] + 1 :]
    if inner == ("Versions", "Current"):
        if "/" in target or target in {".", "..", "Current"}:
            return f"Versions/Current target {target!r} is not a sibling version folder"
        return None
    if len(inner) == 1 and target == f"Versions/Current/{inner[0]}":
        return None
    return f"link {'/'.join(inner)!r} -> {target!r} is not a framework structure link"


def _macos_layout(executable: Path) -> tuple[Path, Path]:
    """The walk root and the contents root: the ``.app`` and its Frameworks, or onedir's."""
    if executable.parent.name == "MacOS" and executable.parent.parent.name == "Contents":
        return executable.parents[2], executable.parent.parent / "Frameworks"
    return executable.parent, executable.parent / "_internal"


_APP_FOLDERS = ("Frameworks", "Resources", "MacOS")


def _macos_bundle_folders(root: Path) -> tuple[Path, ...]:
    """``Contents/Frameworks``, ``Contents/Resources`` and ``Contents/MacOS`` of a ``.app``."""
    if root.suffix != ".app":
        return ()
    return tuple(root / "Contents" / name for name in _APP_FOLDERS)


def _walk_error(error: OSError) -> None:
    """``os.walk``'s ``onerror``: a folder that cannot be read fails the walk (A r1 #1)."""
    raise error


def _macos_entries(root: Path) -> list[tuple[Path, str]]:
    """Every non-folder entry under ``root``, sorted, never descending into a linked folder.

    A folder that cannot be listed (the root included) raises instead of silently dropping
    its subtree from the origin check, the ZIP and the notices (WP6.5 A r1 #1).

    Returns:
        ``(path, kind)`` pairs, kind ``link`` (a symlink or junction, file or folder),
        ``file`` or ``special``.

    Raises:
        OSError: A folder under ``root`` (or ``root`` itself) cannot be listed.
    """
    entries = []
    for parent, folders, files in os.walk(root, onerror=_walk_error, followlinks=False):
        for name in [*folders, *files]:
            path = Path(parent) / name
            if path.is_symlink() or path.is_junction():
                entries.append((path, "link"))
                if name in folders:
                    folders.remove(name)  # never walk through a link (a junction included)
            elif path.is_file():
                entries.append((path, "file"))
            elif not path.is_dir():
                entries.append((path, "special"))
    return sorted(entries, key=lambda item: item[0].relative_to(root).as_posix())


def _within(path: Path, folders: Iterable[Path]) -> bool:
    return any(path != folder and path.is_relative_to(folder) for folder in folders)


_MACOS_LINK_HOPS = 8
"""The longest link chain a ``.app`` admits (PyInstaller's BUNDLE makes two hops)."""


def _not_posix_relative(target: str) -> bool:
    """Whether a link's stored text is empty, absolute or not POSIX."""
    return not target or target.startswith("/") or "\\" in target or ":" in target


def _macos_link_chain_problem(root: Path, physical: Path) -> str | None:
    """Inside a ``.app``: follow a link chain hop by hop; say why it is refused, or ``None``.

    Every hop's stored text must be relative POSIX text, every hop must land inside the
    bundle's real ``Contents`` folder, and the chain must end in a regular file there within
    :data:`_MACOS_LINK_HOPS` hops; a junction, a loop, a missing end or a folder end is
    refused. Folder links inside a hop's path are resolved physically (they are not hops);
    only a link at the hop's final name is a further hop. The message lists every hop.

    Args:
        root: The ``.app`` folder.
        physical: The first link, a physical path under ``root``.

    Returns:
        ``None`` when the chain is admitted, else the reason with the full chain.
    """
    real_root = Path(os.path.realpath(root))
    bundle = Path(os.path.realpath(root / "Contents"))
    hops: list[str] = []

    def refused(reason: str) -> str:
        return f"link chain {reason}: {'; '.join(hops)}"

    def shown(real: Path) -> str:
        """A hop's real path, relative to the real ``.app`` when it lies inside it."""
        return (
            real.relative_to(real_root).as_posix() if real.is_relative_to(real_root) else str(real)
        )

    start = Path(os.path.realpath(physical.parent)) / physical.name
    # A link seen through a linked folder arrives as its real path (macos_link_view).
    current = physical
    label = physical.relative_to(root).as_posix() if physical.is_relative_to(root) else shown(start)
    seen = {start}
    for _ in range(_MACOS_LINK_HOPS):
        if current.is_junction():
            hops.append(f"{label} (junction)")
            return refused("meets a junction")
        target = os.readlink(current)
        hops.append(f"{label} -> {target!r}")
        if _not_posix_relative(target):
            return refused(f"hop target {target!r} is absolute or not POSIX")
        named = current.parent / target
        if named.name in {"", ".", ".."}:
            hop = Path(os.path.realpath(named))
        else:
            hop = Path(os.path.realpath(named.parent)) / named.name
        label = shown(hop)
        if not hop.is_relative_to(bundle):
            hops.append(label)
            return refused("leaves the bundle")
        if hop in seen:
            hops.append(label)
            return refused("loops")
        seen.add(hop)
        if hop.is_symlink() or hop.is_junction():
            current = hop
            continue
        hops.append(label)
        if not hop.exists():
            return refused("ends in a missing entry")
        if not hop.is_file():
            return refused("does not end in a regular file")
        return None
    hops.append(label)
    return refused(f"is longer than {_MACOS_LINK_HOPS} hops")


def _macos_link_class_problem(
    root: Path, contents: Path, physical: Path, location: Path
) -> str | None:
    """Classify one link: ``physical`` is resolved, ``location`` is where it counts as sitting."""
    if physical.is_junction():
        return "junction"
    target = os.readlink(physical)
    if _not_posix_relative(target):
        return f"link target {target!r} is absolute or not POSIX"
    # Resolve from the link's own (physical) folder: the walk never enters a linked folder.
    named = physical.parent / target
    in_app = root.suffix == ".app"
    to_a_link = named.is_symlink() or named.is_junction()
    if in_app and to_a_link:
        chain = _macos_link_chain_problem(root, physical)
        if chain is not None:
            return chain
    resolved = Path(os.path.realpath(named))
    if not resolved.is_relative_to(Path(os.path.realpath(root))):
        return "link resolves outside the release folder"
    if not resolved.exists():
        return "dangling link"
    if to_a_link and not in_app:
        return "link to a link (one hop only)"
    framework = framework_link_problem(PurePosixPath(location.relative_to(root).as_posix()), target)
    if framework is None:
        return None
    real_contents = Path(os.path.realpath(contents))
    if (
        location.parent == contents
        and PurePosixPath(target).name == location.name
        and resolved.is_file()
        and resolved.is_relative_to(real_contents)
    ):
        return None  # (B) PyInstaller's bindepend top-level link to a collected dependency
    folders = _macos_bundle_folders(root)
    real_folders = [Path(os.path.realpath(folder)) for folder in folders]
    if (
        _within(location, folders)
        and _within(resolved, real_folders)
        and (resolved.is_file() or resolved.is_dir())
    ):
        return None  # (C) BUNDLE's cross-link (or its dotted-folder link)
    return f"{framework}; not a top-level dependency link or a bundle cross-link"


def macos_link_view(path: Path) -> list[tuple[PurePosixPath, Path, str]]:
    """The entries a folder link shows: ``(path under the link, physical entry, kind)``.

    Args:
        path: An admitted link (:func:`macos_link_problem`).

    Returns:
        Every non-folder entry under the link's folder target (never through a further
        link), or nothing when the target is a file.

    Raises:
        OSError: A folder under the target cannot be listed.
    """
    resolved = Path(os.path.realpath(path))
    if not resolved.is_dir():
        return []
    return [
        (PurePosixPath(entry.relative_to(resolved).as_posix()), entry, kind)
        for entry, kind in _macos_entries(resolved)
    ]


def macos_link_problem(root: Path, contents: Path, path: Path) -> str | None:
    """Say why a link in a macOS release is refused, or ``None`` when it is admitted.

    THE one link rule (WP6.5, G1-F1 as ruled), shared by the origin check, the release ZIP
    and the artifact notices. Every link must be relative POSIX text, resolve (from its own
    physical folder) inside ``root`` to something that exists, and name a target that is
    NOT itself a link (one hop). Inside a ``.app`` only (WP6.5 run 3, ruling (b)), a link
    whose target is a link is read as a CHAIN instead: it is admitted when every hop is
    relative POSIX text, every hop lands inside the bundle's ``Contents`` folder, and the
    chain ends in a regular file there within :data:`_MACOS_LINK_HOPS` hops (PyInstaller's
    ``Contents/Resources`` cross-link to a ``Contents/Frameworks`` bindepend link); a
    chain that leaves the bundle, loops, ends missing or in a folder, or meets a junction
    or an absolute or non-POSIX hop is refused with every hop named. Outside a ``.app``
    (onedir) a link to a link is refused as before. Then exactly three classes are
    admitted, read on the link's final target:

    - the framework-structure links (:func:`framework_link_problem`);
    - (B) PyInstaller's bindepend top-level link: directly in the contents root, named
      exactly as its target's basename, resolving inside the contents root to a regular
      file (which the walk origin-checks in its own right);
    - (C) a ``.app`` BUNDLE cross-link: located under ``Contents/Frameworks``,
      ``Contents/Resources`` or ``Contents/MacOS`` and resolving under one of them to a
      regular file or a folder (PyInstaller's ``building/osx.py`` cross-links and its
      dotted-folder links). A folder target is walked and every link in it is checked as
      if it sat at this link's location (never entered further); a special file there is
      refused. Its files are origin-checked by the caller (:func:`macos_link_view`).

    Everything else (a junction, an absolute or escaping target, a link to a link outside
    a ``.app`` or a refused chain inside one, any other shape) is refused.

    Args:
        root: The release root (the ``.app``, or the folder holding ``_internal``).
        contents: The contents root (``Contents/Frameworks`` or ``_internal``).
        path: The link, a physical path under ``root``.

    Returns:
        ``None`` when admitted, else the reason.

    Raises:
        OSError: A folder under a folder target cannot be listed.
    """
    problem = _macos_link_class_problem(root, contents, path, path)
    if problem is not None:
        return problem
    for relative, entry, kind in macos_link_view(path):
        if kind == "special":
            return f"special file {relative} under the linked folder"
        if kind == "link":
            nested = _macos_link_class_problem(
                root, contents, entry, path.joinpath(*relative.parts)
            )
            if nested is not None:
                return f"{relative} under the linked folder: {nested}"
    return None


def _macos_contents(root: Path) -> Path:
    """The contents root of a release folder: a ``.app``'s Frameworks, else onedir's."""
    if root.suffix == ".app":
        return root / "Contents" / "Frameworks"
    return root / APP_NAME / "_internal"


def _macos_depth(root: Path, contents: Path, location: Path) -> int | None:
    """Folders between ``location`` and its contents root, or ``None`` outside it.

    In a ``.app``, ``Contents/Resources`` mirrors ``Contents/Frameworks`` (BUNDLE's
    cross-links keep the relative path), so a file seen there has the same depth.
    """
    for folder in (contents, *_macos_bundle_folders(root)[1:2]):
        if location.is_relative_to(folder):
            return len(location.relative_to(folder).parts) - 1
    return None


def place_macos_tools(
    bundle: Path, executables: Mapping[str, Path], texts: Mapping[str, Path] | None = None
) -> list[Path]:
    """Copy verified tools INTO a ``.app`` before it is sealed (:func:`seal_macos_bundle`).

    Executables go to ``Contents/MacOS`` (beside the bootloader: AD-34 (2) puts the frozen
    executable's folder first on PATH, so the bundled FFmpeg is found first) with mode
    0755; texts (licences, the build record) go to ``Contents/Resources`` with mode 0644,
    because ``Contents/MacOS`` may hold only code under the bundle's seal. Bytes are copied
    unchanged, so the origin check's whole-file hashes from the verified archive still
    apply. The macOS FFmpeg itself is WP6.5 group 2a's.

    Args:
        bundle: The built ``Clearwater.app``.
        executables: Bundle file name -> the verified tool on disk.
        texts: Bundle file name -> a text file on disk.

    Returns:
        The written paths, executables first.

    Raises:
        ValueError: The bundle is not a ``.app``, a name is not a plain file name, or a
            destination exists or is a link.
        OSError: A copy fails.
    """
    if bundle.suffix != ".app" or not (bundle / "Contents" / "MacOS").is_dir():
        raise ValueError(f"tool placement needs a built .app bundle: {bundle}")
    written = []
    for folder, files, mode in (
        (bundle / "Contents" / "MacOS", executables, 0o755),
        (bundle / "Contents" / "Resources", texts or {}, 0o644),
    ):
        for name, source in sorted(files.items()):
            if not name or PurePosixPath(name).name != name or "\\" in name or name in {".", ".."}:
                raise ValueError(f"tool placement: {name!r} is not a plain file name")
            target = folder / name
            if target.is_symlink() or target.exists():
                raise ValueError(f"tool placement: {target} already exists")
            folder.mkdir(exist_ok=True)
            shutil.copyfile(source, target)
            target.chmod(mode)
            written.append(target)
    return written


def seal_macos_bundle(
    bundle: Path,
    *,
    run: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    timeout: float = 300,
) -> None:
    """Ad-hoc re-sign a ``.app`` after everything was placed in it, then verify the seal.

    PyInstaller signs the bundle when it builds it (``building/osx.py`` ``assemble``), so
    anything written afterwards (the FFmpeg tools, the notices) breaks the seal. The bundle
    is re-signed WITHOUT ``--deep`` (nested code keeps its bytes, so the origin check's
    hashes and identities still hold) and then ``codesign --verify --deep --strict``
    must pass. Bounded, never a shell, ``/usr/bin/codesign`` by path.

    Args:
        bundle: The built ``Clearwater.app``.
        run: The process runner (a stub in tests).
        timeout: Seconds allowed for each ``codesign`` call.

    Raises:
        RuntimeError: ``codesign`` fails, cannot start or times out (named).
        ValueError: ``bundle`` is not a ``.app`` folder.
    """
    if bundle.suffix != ".app" or not bundle.is_dir():
        raise ValueError(f"bundle seal needs a built .app bundle: {bundle}")
    commands = (
        [MACOS_CODESIGN, "--sign", "-", "--force", "--timestamp=none", str(bundle)],
        [MACOS_CODESIGN, "--verify", "--deep", "--strict", "--verbose=2", str(bundle)],
    )
    for command in commands:
        try:
            result = run(
                command,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise RuntimeError(f"bundle seal: {' '.join(command[:2])}: {error}") from error
        if result.returncode != 0:
            lines = [line.strip() for line in (result.stderr or "").splitlines() if line.strip()]
            detail = f": {lines[-1][-300:]}" if lines else ""
            raise RuntimeError(
                f"bundle seal: {' '.join(command[:2])} exited {result.returncode}{detail}"
            )


def _macos_native_origin_violations(
    executable: Path, *, original_path: str, ffmpeg_hashes: Iterable[str]
) -> list[str]:
    hashes = _native_origin_hashes() | set(ffmpeg_hashes)
    errors = []
    root, contents = _macos_layout(executable)

    def unknown(label: str, name: str) -> str:
        likely = next(
            (
                Path(part) / Path(name).name
                for part in original_path.split(os.pathsep)
                if part and (Path(part) / Path(name).name).is_file()
            ),
            None,
        )
        suffix = f"; likely PATH source: {likely}" if likely else ""
        return f"native origin unknown: {label}{suffix}"

    def inspect(label: str, name: str, data: bytes, depth: int | None) -> None:
        if _is_native(name, data) and hashlib.sha256(data).hexdigest() not in hashes:
            problem = _MACHO_UNKNOWN if depth is None else macho_built_problem(data, hashes, depth)
            if problem == _MACHO_UNKNOWN:
                errors.append(unknown(label, name))
            elif problem is not None:
                errors.append(f"native origin: {label}: {problem}")
        if name.lower().endswith(".zip") or data.startswith(b"PK\x03\x04"):
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                for member in archive.infolist():
                    if not member.is_dir():
                        inspect(
                            label + "!" + member.filename,
                            member.filename,
                            archive.read(member),
                            None,
                        )

    if not _is_clearwater_bootloader(executable):
        errors.append(
            f"native origin: {executable.name} differs from locked PyInstaller bootloader"
        )
    for path, kind in _macos_entries(root):
        label = path.relative_to(root).as_posix()
        if kind == "link":
            problem = macos_link_problem(root, contents, path)
            if problem is not None:
                errors.append(f"native origin: linked file {path}: {problem}")
                continue
            # A folder link's files are checked as if they sat at the link's location.
            for relative, shown, shown_kind in macos_link_view(path):
                if shown_kind == "file":
                    seen = path.joinpath(*relative.parts)
                    depth = _macos_depth(root, contents, seen)
                    inspect(f"{label}/{relative}", shown.name, shown.read_bytes(), depth)
        elif kind == "file" and path != executable:
            depth = _macos_depth(root, contents, path)
            inspect(label, path.name, path.read_bytes(), depth)
    package = read_package(executable)
    for name, entry in package.toc.items():
        if entry[-1] not in {"o", "z"}:
            inspect("pkg:" + name, name, package.extract(name), len(PurePosixPath(name).parts) - 1)
    return errors


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
    elif sys.platform == "darwin":
        # PyInstaller thins, unsigns, re-identifies (LC_UUID), appends the PKG inside
        # __LINKEDIT and re-signs the bootloader: compare the normalised arm64 image.
        return _is_macos_bootloader(executable, source)
    else:
        # Refuse transformed ELF builds (no Linux build is supported). A
        # byte-identical bootloader prefix is accepted here.
        return executable.read_bytes().startswith(source.read_bytes())


def native_origin_violations(
    executable: Path, *, original_path: str, ffmpeg_hashes: Iterable[str] = ()
) -> list[str]:
    """Check every native against interpreter/locked RECORD bytes and the bootloader.

    The main Windows executable is compared to the RECORD-verified runw.exe's
    immutable PE sections, allowing resources, debug timestamps and an appended
    archive. Every other native must match a complete file hash. On macOS (WP6.5)
    the bootloader and every Mach-O PyInstaller transformed are compared by their
    normalised arm64 identity instead (:func:`_macho_identity`,
    :func:`macho_built_problem`), and only framework links are admitted
    (:func:`framework_link_problem`); the ``.app`` bundle is walked whole. ZIPs (including
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
    if sys.platform == "darwin":
        return _macos_native_origin_violations(
            executable, original_path=original_path, ffmpeg_hashes=ffmpeg_hashes
        )
    else:
        return _pe_native_origin_violations(
            executable, original_path=original_path, ffmpeg_hashes=ffmpeg_hashes
        )


def _pe_native_origin_violations(
    executable: Path, *, original_path: str, ffmpeg_hashes: Iterable[str]
) -> list[str]:
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
        folder: The Windows onedir artifact, the macOS ``.app``'s release folder or
            ``Contents/MacOS``, or a parent wrapper.
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
    if sys.platform == "darwin":
        return _macos_release_files(folder)
    else:
        return _release_files_without_links(folder)


def _macos_release_files(folder: Path) -> list[Path]:
    """The ZIP members of a macOS release: files plus admitted framework links (F0-9).

    A link is a member AS a link (never followed); any other link, a junction or a
    special file is refused, as on Windows.
    """
    if folder.is_symlink() or folder.is_junction() or not folder.is_dir():
        raise ValueError("release ZIP requires a physical release folder without junctions")
    resolved = folder.resolve()
    contents = _macos_contents(folder)
    members = []
    for path, kind in _macos_entries(folder):
        relative = path.relative_to(folder)
        if kind == "link":
            problem = macos_link_problem(folder, contents, path)
            if problem is not None:
                raise ValueError(
                    f"release ZIP refuses linked/junction/outside member: {relative} ({problem})"
                )
        elif kind == "special":
            raise ValueError(f"release ZIP refuses special file: {relative}")
        elif not path.resolve().is_relative_to(resolved):
            raise ValueError(f"release ZIP refuses linked/junction/outside member: {relative}")
        members.append(path)
    return members


def _release_files_without_links(folder: Path) -> list[Path]:
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
        if path.is_symlink():
            snapshot[path.relative_to(folder).as_posix()] = ("link:" + os.readlink(path), 0)
            continue
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


def write_release_zip(
    folder: Path, *, out: Path, source_epoch: int, name: str | None = None
) -> Path:
    """Archive a release wrapper with sorted files and fixed source-commit metadata.

    Only file members are emitted, under the wrapper's single top-level folder.
    Every member has a UTC DOS timestamp (two-second precision), Unix regular-file
    mode 0644 and no extra/comment metadata. File mtimes and modes are ignored.
    On macOS (WP6.5) a link the shared rule admits (:func:`macos_link_problem`) is
    stored AS a link: Unix mode ``S_IFLNK | 0755``, uncompressed, its content the link
    text; and a file whose mode carries an execute bit (PyInstaller's ``chmod 0755`` of
    every Mach-O it collects, the bundled tools) is stored 0755, so it is executable
    after unzip. Windows members are unchanged (0644, the mode never read).

    Args:
        folder: The release folder: the onedir wrapper containing ``Clearwater/``, or on
            macOS the ``Clearwater.app`` itself (its one top-level item).
        out: Output root for ``<name>.zip`` and its sha256 sidecar.
        source_epoch: Source/tag commit time in Unix seconds; explicit for testing.
        name: The archive's stem; the folder's name when None.

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
    target = out / ((folder.name if name is None else name) + ".zip")
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
                info.internal_attr = 0
                info.extra = info.comment = b""
                if path.is_symlink():
                    info.external_attr = (stat.S_IFLNK | 0o755) << 16
                    link = os.readlink(path).encode("utf-8")
                    archive.writestr(info, link, compress_type=zipfile.ZIP_STORED)
                else:
                    if sys.platform == "darwin":
                        executable = path.stat().st_mode & 0o111
                        mode = 0o755 if executable else 0o644
                    else:
                        mode = 0o644
                    info.external_attr = (stat.S_IFREG | mode) << 16
                    archive.writestr(
                        info,
                        path.read_bytes(),
                        compress_type=zipfile.ZIP_DEFLATED,
                        compresslevel=9,
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
            target = out / (release_zip_name(form, app_version()) + ".zip")
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
            # WP6.5: darwin bundles from the macOS lock; every other host keeps the
            # Windows lock (Linux is refused before PyInstaller by run_pyinstaller).
            lock: FFmpegLock | FFmpegMacLock = (
                load_macos_ffmpeg_lock() if sys.platform == "darwin" else load_ffmpeg_lock()
            )
            if ffmpeg_from != lock["asset_url"] or ffmpeg_sha256 != lock["github_sha256"]:
                raise ValueError("FFmpeg URL/sha256 differ from the lock")
            if lock.get("census") == "pending" and (notices or zip_release):
                raise ValueError(
                    "macOS FFmpeg lock census pending: --notices / --zip await the "
                    "census rows (WP6.5 part 3)"
                )
        except (OSError, ValueError) as error:
            print(f"FAILED: {error}")
            return 1
    version = app_version()
    if sys.platform == "darwin":
        # AD-33: no GPU pack on macOS (a CPU-only sync installs none of its distributions),
        # so there is no pack code whose standard-library needs the bundle must carry.
        sources: list[tuple[str, Path]] = []
    else:
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
        # The Windows call is unchanged; darwin names its platform (the .app's MacOS folder).
        fetch: Callable[..., list[tuple[Path, str]]] = bundle_ffmpeg
        if sys.platform == "darwin":
            fetch = functools.partial(bundle_ffmpeg, platform="darwin")
        try:
            for path, line in fetch(
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
    if sys.platform == "darwin":
        # WP6.5: everything placed after PyInstaller signed the .app (FFmpeg, notices) is
        # sealed now; the re-signed bootloader is origin-checked again after the seal.
        try:
            seal_macos_bundle(_macos_layout(executable)[0])
            print("bundle seal: PASS (ad-hoc re-sign; codesign --verify --deep --strict)")
            origin_errors = native_origin_violations(
                executable, original_path=original_path, ffmpeg_hashes=ffmpeg_hashes
            )
        except (OSError, RuntimeError, ValueError, zipfile.BadZipFile) as error:
            reason = " ".join(str(error).split())
            print(f"FAILED: {reason}".encode("ascii", "backslashreplace").decode("ascii"))
            return 1
        if origin_errors:
            for error_line in origin_errors:
                line = f"FAILED: after seal: {error_line}"
                print(line.encode("ascii", "backslashreplace").decode("ascii"))
            return 1
    else:
        pass
    zip_folder = release_zip_folder(root)
    snapshot = None
    if zip_release:
        try:
            snapshot = _release_snapshot(zip_folder)
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
            _check_release_snapshot(zip_folder, snapshot)
            archive = write_release_zip(
                zip_folder,
                out=out,
                source_epoch=source_commit_epoch(),
                name=release_zip_name(form, version),
            )
            print(f"wrote {archive}")
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
