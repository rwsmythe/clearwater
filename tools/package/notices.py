"""Plan inventory-driven notices for Clearwater onedir artifacts without running them.

This module inventories the on-disk files and embedded PYZ/boot entries, matches
installed RECORDs to the locked source-install audit, and refuses unsafe release
claims. Text rendering and the build command's writer are a separate build rung.
No bundled runtime package, product entry point or external binary is executed.
"""

from __future__ import annotations

import importlib.metadata
import importlib.util
import json
import re
import sys
import tomllib
import zipfile
from collections import defaultdict
from collections.abc import Callable, Sequence
from functools import cache
from pathlib import Path
from types import ModuleType
from typing import Any, NamedTuple, cast

ROOT = Path(__file__).resolve().parents[2]
SOURCE_URL = "https://github.com/rwsmythe/clearwater"
GPU_NAMES = frozenset({"cuda-pathfinder", "cuda-toolkit", "cupy-cuda12x"})


class LicenceInput(NamedTuple):
    """A real input file or a rooted upstream-audit block, never memory-written text."""

    path: Path
    block_id: str = ""


class NoticeRow(NamedTuple):
    """One redistributed component, its evidence entries and required text inputs."""

    name: str
    version: str
    licence: str
    sources: tuple[str, ...]
    entries: tuple[str, ...]
    licence_inputs: tuple[LicenceInput, ...]
    notes: tuple[str, ...] = ()
    verdict: str = "Redistributed in this artifact"


class NoticePlan(NamedTuple):
    """Validated entry coverage plus separately obtained component statements."""

    entries: tuple[str, ...]
    rows: tuple[NoticeRow, ...]
    user_obtained: tuple[str, ...]


class _AuditRow(NamedTuple):
    name: str
    version: str
    licence: str
    sources: tuple[str, ...]


class _Entry(NamedTuple):
    label: str
    name: str
    kind: str


@cache
def _build_tool() -> ModuleType:
    # A sibling load works for both a direct tools script and pytest's path import.
    spec = importlib.util.spec_from_file_location(
        "_clearwater_notices_build", Path(__file__).with_name("build.py")
    )
    if spec is None or spec.loader is None:
        raise ValueError("notices: cannot load the package inventory tool")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _audit_rows(path: Path) -> dict[str, _AuditRow]:
    content = path.read_text(encoding="utf-8")
    try:
        section = content.split("## Runtime dependency audit", 1)[1].split("###", 1)[0]
    except IndexError as error:
        raise ValueError("notices: missing Runtime dependency audit table") from error
    rows: dict[str, _AuditRow] = {}
    for line in section.splitlines():
        if not line.startswith("| "):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 5 or cells[0] == "Component" or cells[0].startswith("---"):
            continue
        name, version, licence, _verdict, source = cells
        key = _normalize(name)
        if key in rows:
            raise ValueError(f"notices: duplicate audit row {name}")
        urls = tuple(re.findall(r"\]\((https?://[^)]+)\)", source))
        rows[key] = _AuditRow(name, version, licence, urls)
    if "python" not in rows:
        raise ValueError("notices: missing Python audit row")
    return rows


def _locked_versions(path: Path) -> dict[str, set[str]]:
    document = tomllib.loads(path.read_text(encoding="utf-8"))
    versions: dict[str, set[str]] = defaultdict(set)
    for package in document.get("package", []):
        if isinstance(package.get("name"), str) and isinstance(package.get("version"), str):
            versions[_normalize(package["name"])].add(package["version"])
    return dict(versions)


def _module_name(path: str) -> str | None:
    parts = path.replace("\\", "/").split("/")
    if not parts or not parts[-1].endswith((".py", ".pyc", ".pyd", ".so")):
        return None
    stem = parts[-1].split(".", 1)[0]
    return ".".join(parts[:-1] if stem == "__init__" else [*parts[:-1], stem])


def _inventory(folder: Path) -> tuple[list[_Entry], Path]:
    tool = _build_tool()
    executable = cast(Path, tool.find_executable(folder))
    home = executable.parent
    if not (home / "_internal").is_dir():
        raise ValueError("notices: expected an onedir folder with _internal")
    entries: list[_Entry] = []
    for path in sorted(home.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"notices: unsafe linked entry {path.name}")
        if not path.is_file():
            continue
        name = path.relative_to(home).as_posix()
        entries.append(_Entry("file:" + name, name, "file"))
        if name == "_internal/base_library.zip":
            with zipfile.ZipFile(path) as archive:
                for member in sorted(archive.namelist()):
                    if member.endswith("/"):
                        continue
                    module = _module_name(member)
                    if module is None:
                        raise ValueError(f"notices: unknown base-library entry {member}")
                    entries.append(_Entry("base:" + member, module, "module"))
    package = tool.read_package(executable)
    for name, data in sorted(package.toc.items()):
        typecode = data[-1]
        if typecode == "z":
            entries.append(_Entry("archive:" + name, name, "container"))
            archive = package.open_embedded_archive(name)
            for module in sorted(archive.toc):
                entries.append(_Entry("pyz:" + module, module, "module"))
        elif typecode in {"m", "M", "s"}:
            entries.append(_Entry("archive:" + name, name, "module"))
        else:
            entries.append(_Entry("archive:" + name, name, "file"))
    return entries, home


def _licence_inputs(
    distribution: importlib.metadata.Distribution, name: str, audit: Path
) -> tuple[LicenceInput, ...]:
    found: list[LicenceInput] = []
    commercial = False
    for entry in distribution.files or ():
        relative = str(entry).replace("\\", "/")
        if not any(
            token in relative.lower()
            for token in ("license", "licence", "copying", "copyright", "patents")
        ):
            continue
        if Path(relative).name == "LicenseRef-Qt-Commercial.txt":
            commercial = True
            continue
        path = Path(str(distribution.locate_file(entry)))
        if not path.is_file() or not path.stat().st_size:
            raise ValueError(f"notices: {name} missing licence material: {relative}")
        found.append(LicenceInput(path))
    # This is only a reference: rendering must verify the stored hash/byte count
    # and preserve the granted upstream-copy provenance before copying any text.
    if name in {"pyside6-essentials", "shiboken6"} and (commercial or not found):
        if '<a id="text-36"></a>' not in audit.read_text(encoding="utf-8"):
            raise ValueError(f"notices: {name} missing licence material: audit text-36")
        found.append(LicenceInput(audit, "text-36"))
    if not found:
        raise ValueError(f"notices: {name} missing licence material")
    return tuple(sorted(set(found)))


def _python_file_names() -> set[str]:
    base = Path(sys.base_prefix)
    return {
        path.name.casefold()
        for folder in (base, base / "DLLs")
        for path in folder.glob("*")
        if path.is_file() and path.suffix.lower() in {".dll", ".pyd", ".so"}
    }


def _ffmpeg_rows(home: Path, lock_path: Path) -> list[NoticeRow]:
    tools = [home / "ffmpeg.exe", home / "ffprobe.exe"]
    material = [home / "ffmpeg-BUILD.txt", home / "ffmpeg-LICENSE.txt"]
    if not any(path.exists() for path in tools):
        if any(path.exists() for path in material):
            raise ValueError("notices: FFmpeg missing executable pair beside provenance/licence")
        return []
    missing = [path.name for path in (*tools, *material) if not path.is_file()]
    if missing:
        raise ValueError("notices: FFmpeg missing " + ", ".join(missing))
    lock = cast(
        dict[str, Any],
        _build_tool().validate_ffmpeg_lock(json.loads(lock_path.read_text(encoding="utf-8"))),
    )
    incompatible: list[str] = []
    for component in lock["components"]:
        if component["gpl3_compatible"] == "no":
            incompatible.append(component["name"])
        for extra in component["extra_repositories"]:
            if extra["gpl3_compatible"] == "no":
                incompatible.append(f"{component['name']} / {extra['repository']} @ {extra['pin']}")
    if incompatible:
        raise ValueError("notices: FFmpeg GPL-3.0-incompatible: " + "; ".join(incompatible))
    text = material[0].read_text(encoding="utf-8")
    expected = {
        "Provider": lock["provider"],
        "Release tag": lock["release_tag"],
        "Asset": lock["asset_name"],
        "SHA256": lock["github_sha256"],
        "FFmpeg version": lock["version"],
        "FFmpeg commit": lock["ffmpeg_commit"],
        "Build repository commit": lock["build_repository_commit"],
        "Per-component source recipes": lock["source_record_url"],
    }
    lines = text.splitlines()
    for key, value in expected.items():
        if [line for line in lines if line.startswith(key + ": ")] != [key + ": " + value]:
            raise ValueError(f"notices: FFmpeg build provenance differs: {key}")
    if [line for line in lines if line.startswith("configuration:")] != [lock["configure_line"]]:
        raise ValueError("notices: FFmpeg build provenance differs: configuration")
    if not material[1].stat().st_size:
        raise ValueError("notices: FFmpeg missing licence material")
    entries = tuple("file:" + path.name for path in (*tools, *material))
    inputs = (LicenceInput(material[1]),)
    rows = [
        NoticeRow(
            "FFmpeg / ffprobe",
            lock["version"],
            lock["licence"],
            (f"{lock['ffmpeg_repository']} @ {lock['ffmpeg_commit']}", lock["source_record_url"]),
            entries,
            inputs,
        )
    ]
    for component in lock["components"]:
        rows.append(
            NoticeRow(
                "FFmpeg component: " + component["name"],
                component["pin"],
                component["licence"],
                (f"{component['repository']} @ {component['pin']}",),
                entries,
                inputs,
                (component["licence_note"],),
            )
        )
        for index, extra in enumerate(component["extra_repositories"], 2):
            if extra["status"] == "built":
                rows.append(
                    NoticeRow(
                        f"FFmpeg component: {component['name']} / repository {index}",
                        extra["pin"],
                        extra["licence"],
                        (f"{extra['repository']} @ {extra['pin']}",),
                        entries,
                        inputs,
                        (extra["licence_note"],),
                    )
                )
    return rows


def validate_coverage(entries: Sequence[str], rows: Sequence[NoticeRow]) -> None:
    """Refuse uncovered entries, duplicate rows or claims about absent files/modules.

    User-obtained statements are separate from redistributed rows and therefore
    cannot disguise a missing redistributed entry or an invented component.

    Args:
        entries: Every physical/archive/module inventory label.
        rows: The component claims to validate against that inventory.

    Raises:
        ValueError: Coverage is incomplete or a row claims an absent entry.
    """
    actual = set(entries)
    if len(actual) != len(entries):
        raise ValueError("notices: duplicate inventory entry")
    covered: set[str] = set()
    names: set[str] = set()
    for row in rows:
        if row.name in names:
            raise ValueError(f"notices: duplicate component row {row.name}")
        names.add(row.name)
        if not row.entries or not set(row.entries) <= actual:
            raise ValueError(f"notices: {row.name} claims an absent bundled entry")
        if not row.licence or not row.sources:
            raise ValueError(f"notices: {row.name} missing licence or source material")
        covered.update(row.entries)
    if missing := actual - covered:
        raise ValueError("notices: uncovered bundled entries: " + ", ".join(sorted(missing)))


def plan_notices(
    folder: Path,
    *,
    audit_path: Path = ROOT / "THIRD_PARTY_NOTICES.md",
    uv_lock_path: Path = ROOT / "uv.lock",
    ffmpeg_lock_path: Path = ROOT / "tools/package/ffmpeg.lock.json",
    distribution: Callable[
        [str], importlib.metadata.Distribution
    ] = importlib.metadata.distribution,
) -> NoticePlan:
    """Inventory an onedir folder and select only the rows supported by its contents.

    Pure modules are matched to wheel RECORD paths; native/data entries must
    match a RECORD path or an unambiguous native basename. Standard-library
    binaries are matched to this build interpreter. Artifact code and bundled
    runtime packages are not imported; no external process is started.

    Args:
        folder: The release folder or its executable's immediate folder.
        audit_path: The source-install audit's runtime table and audited texts.
        uv_lock_path: The build's locked distribution versions.
        ffmpeg_lock_path: The FFmpeg identity and verified source/licence rows.
        distribution: Installed-metadata resolver, also usable with fixture wheels.

    Returns:
        Validated coverage rows and explicitly user-obtained component statements.

    Raises:
        ValueError: An entry is unknown, a version/material is missing, or a
            bundled FFmpeg repository is GPL-3.0-incompatible.
        OSError: Required files cannot be read.
    """
    entries, home = _inventory(folder)
    ffmpeg = _ffmpeg_rows(home, ffmpeg_lock_path)
    audit = _audit_rows(audit_path)
    versions = _locked_versions(uv_lock_path)
    runtime = {
        key: row
        for key, row in audit.items()
        if key not in GPU_NAMES
        and not key.startswith("nvidia-")
        and key not in {"python", _normalize("FFmpeg / ffprobe")}
    }
    installed: dict[str, importlib.metadata.Distribution] = {}
    paths: dict[str, set[str]] = defaultdict(set)
    basenames: dict[str, set[str]] = defaultdict(set)
    modules: dict[str, set[str]] = defaultdict(set)
    for name in (*runtime, "pyinstaller", "pyinstaller-hooks-contrib"):
        try:
            dist = distribution(name)
        except (importlib.metadata.PackageNotFoundError, KeyError):
            continue
        installed[name] = dist
        for path in dist.files or ():
            relative = str(path).replace("\\", "/")
            paths[relative.casefold()].add(name)
            if Path(relative).suffix.lower() in {".dll", ".pyd", ".so", ".dylib"}:
                basenames[Path(relative).name.casefold()].add(name)
            if module := _module_name(relative):
                modules[module].add(name)
                if name in {"pyinstaller", "pyinstaller-hooks-contrib"}:
                    modules[Path(relative).stem].add(name)
    selected: dict[str, list[str]] = defaultdict(list)
    ffmpeg_labels = {entry for row in ffmpeg for entry in row.entries}
    python_names = _python_file_names()
    for entry in entries:
        if entry.label in ffmpeg_labels:
            continue
        name = entry.name
        if (
            name in {"Clearwater.exe", "__main__", "clearwater.__main__", "THIRD_PARTY_NOTICES.md"}
            or name.startswith("clearwater.")
            or name == "clearwater"
        ):
            selected["clearwater"].append(entry.label)
            if name == "Clearwater.exe":
                selected["pyinstaller"].append(entry.label)
            continue
        if entry.kind == "container":
            selected["pyinstaller"].append(entry.label)
            continue
        if name == "_internal/base_library.zip" or (
            entry.kind == "module" and name.split(".")[0] in sys.stdlib_module_names
        ):
            selected["python"].append(entry.label)
            continue
        if entry.kind == "module":
            owners = modules.get(name, set())
        else:
            relative = name.removeprefix("_internal/")
            owners = paths.get(relative.casefold(), set())
            if not owners:
                owners = basenames.get(Path(relative).name.casefold(), set())
            if (
                not owners
                and "/" not in relative
                and Path(relative).name.casefold() in python_names
            ):
                selected["python"].append(entry.label)
                continue
        if len(owners) != 1:
            raise ValueError(f"notices: unknown or ambiguous bundled entry {entry.label}")
        owner = next(iter(owners))
        if owner in {"pyinstaller", "pyinstaller-hooks-contrib"} and (
            name.startswith("pyi_rth_") or name.startswith("_pyi_rth_utils")
        ):
            owner += "-runtime"
        selected[owner].append(entry.label)
    result: list[NoticeRow] = list(ffmpeg)
    for name, labels in sorted(selected.items()):
        if name == "clearwater":
            result.append(
                NoticeRow(
                    "Clearwater",
                    cast(str, _build_tool().app_version()),
                    "GPL-2.0-or-later",
                    (SOURCE_URL,),
                    tuple(sorted(labels)),
                    (LicenceInput(ROOT / "LICENSE"),),
                )
            )
            continue
        if name == "python":
            row = audit["python"]
            version = ".".join(map(str, sys.version_info[:3]))
            if row.version.split()[0] != version:
                raise ValueError("notices: Python version differs from the audited interpreter")
            python_licence = Path(sys.base_prefix) / "LICENSE.txt"
            if not python_licence.is_file():
                raise ValueError("notices: Python missing licence material")
            if not row.sources:
                raise ValueError("notices: Python missing source material")
            result.append(
                NoticeRow(
                    "Python",
                    version,
                    row.licence,
                    row.sources,
                    tuple(sorted(labels)),
                    (LicenceInput(python_licence),),
                )
            )
            continue
        base = name.removesuffix("-runtime")
        dist = installed[base]
        version = dist.version
        if versions.get(base) != {version}:
            raise ValueError(f"notices: {base} version differs from uv.lock")
        inputs = _licence_inputs(dist, base, audit_path)
        if base in {"pyinstaller", "pyinstaller-hooks-contrib"}:
            runtime_kind = name.endswith("-runtime")
            title = "PyInstaller run-time hooks" if runtime_kind else "PyInstaller bootloader"
            if base.endswith("contrib"):
                title = "PyInstaller contributed run-time hooks"
            licence = "Apache-2.0" if runtime_kind else "GPL-2.0-or-later WITH Bootloader Exception"
            source = "https://github.com/pyinstaller/" + (
                "pyinstaller-hooks-contrib" if base.endswith("contrib") else "pyinstaller"
            )
            result.append(
                NoticeRow(
                    title,
                    version,
                    licence,
                    (source + "/tree/v" + version,),
                    tuple(sorted(labels)),
                    inputs,
                )
            )
            continue
        row = runtime[base]
        if row.version != version:
            raise ValueError(f"notices: {base} version differs from the runtime audit")
        if not row.sources:
            raise ValueError(f"notices: {base} missing source material")
        result.append(
            NoticeRow(base, version, row.licence, row.sources, tuple(sorted(labels)), inputs)
        )
    inventory_labels = tuple(sorted(entry.label for entry in entries))
    ordered = tuple(sorted(result, key=lambda row: row.name.casefold()))
    validate_coverage(inventory_labels, ordered)
    statements = [
        "GPU pack: user-obtained, not redistributed; CuPy and CUDA retain their publishers' terms."
    ]
    if not ffmpeg:
        statements.append(
            "FFmpeg / ffprobe: user-obtained, not redistributed; "
            "obtain licence and source from its publisher."
        )
    return NoticePlan(inventory_labels, ordered, tuple(statements))
