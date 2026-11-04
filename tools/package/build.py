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
    uv run --no-sync python tools/package/build.py --write-manifest <pack root>/<stamp>

``--write-manifest`` writes ``manifest.json`` for a GPU pack filled by hand (the loader's
layout, :mod:`clearwater.gpu_pack`); the WP6.3 downloader will write the same file.

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
from typing import Literal, Protocol, cast

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
        elif top not in ALLOWED_TOP_LEVEL and top not in sys.stdlib_module_names:
            rules.add("unexpected-module")
    return sorted(rules)


def module_violations(module: str, *, allow_boot: bool = False) -> list[str]:
    """Return the rules a frozen module name (``a.b.c``) breaks: :func:`name_violations`.

    Args:
        module: A dotted module name from the PYZ or a CArchive module entry.
        allow_boot: Accept PyInstaller's boot modules (:data:`BOOT_MODULE_PREFIXES`).

    Returns:
        The broken rules, sorted.
    """
    if allow_boot and module.startswith(BOOT_MODULE_PREFIXES):
        return []
    parts = module.split(".")
    return name_violations([*parts[:-1], parts[-1] + ".pyc"], module_root=True)


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
        (the components relative to the bundle's root, whether they are under ``_internal``
        or the one-file release root, i.e. relative to a folder on the frozen ``sys.path``).
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
        rooted = under_internal and is_file
        label = f"dist:{relative.as_posix()}"
        found += [f"{label} ({rule})" for rule in name_violations(parts, module_root=rooted)]
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
    - each module entry (PyInstaller's boot modules allowed);
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
            for module in _pyz_modules(package, name):
                found += [f"pyz:{module} ({rule})" for rule in module_violations(module)]
            continue
        if typecode in (readers.PKG_ITEM_PYMODULE, readers.PKG_ITEM_PYPACKAGE):
            module = name.replace("\\", ".").replace("/", ".")
            found += [f"{label} ({r})" for r in module_violations(module, allow_boot=True)]
            continue
        if typecode in (readers.PKG_ITEM_PYSOURCE, readers.PKG_ITEM_RUNTIME_OPTION):
            continue  # the entry script and run-time hooks; options are not files
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
    os.environ["PYINSTALLER_CONFIG_DIR"] = str(pyinstaller_config_dir(out))
    root = clean_release_dir(out, form, version)
    args = pyinstaller_args(form, out=out, version=version)
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
    check_wall = time.monotonic() - check_start
    print(f"build {form}: wall {wall:.1f} s; executable {executable}")
    for name, size in size_by_top_level(executable):
        print(f"  size {size / 2**20:10.1f} MiB  {name}")
    print(f"  total {tree_size(root) / 2**20:.1f} MiB under {root}")
    print(f"  bundle checks took {check_wall:.1f} s")
    if bad:
        print(f"FORBIDDEN in the bundle ({len(bad)}):")
        for name in bad[:50]:
            print(f"  {name}")
        return 1
    print("bundle check: PASS (no " + ", ".join(FORBIDDEN_TOP_LEVEL) + " at any depth or in")
    print("  any ZIP; no CUDA library; every module's top-level name allowed)")
    return 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse the command line.

    Args:
        argv: The arguments; ``sys.argv[1:]`` when None.

    Returns:
        The parsed namespace (``form``, ``out``, ``with_ffmpeg``, ``write_manifest``).
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--form", choices=FORMS)
    action.add_argument("--write-manifest", type=Path, metavar="PACK_FOLDER")
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
    out = Path(os.path.abspath(options.out))
    return build(cast(Form, options.form), out=out, with_ffmpeg=options.with_ffmpeg)


if __name__ == "__main__":
    raise SystemExit(main())
