"""Generate inventory-driven notices for Clearwater onedir artifacts without running them.

This module inventories the on-disk files and embedded PYZ/boot entries, matches
installed RECORDs to the locked source-install audit, and refuses unsafe release
claims. Licence files are copied verbatim; audited upstream blocks are checked
against their recorded SHA-256 and byte count before reuse.
No bundled runtime package, product entry point or external binary is executed.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import re
import sys
import tempfile
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
    try:
        package = tool.read_package(executable)
    except RuntimeError as error:
        raise ValueError(f"notices: invalid executable archive: {error}") from error
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
    for entry in distribution.files or ():
        relative = str(entry).replace("\\", "/")
        if not any(
            token in relative.lower()
            for token in ("license", "licence", "copying", "copyright", "patents")
        ):
            continue
        if Path(relative).name == "LicenseRef-Qt-Commercial.txt":
            continue
        path = Path(str(distribution.locate_file(entry)))
        if not path.is_file() or not path.stat().st_size:
            raise ValueError(f"notices: {name} missing licence material: {relative}")
        found.append(LicenceInput(path))
    # This is only a reference: rendering must verify the stored hash/byte count
    # and preserve the granted upstream-copy provenance before copying any text.
    if name in {"pyside6-essentials", "shiboken6"} and not any(
        b"GNU LESSER GENERAL PUBLIC LICENSE" in item.path.read_bytes() for item in found
    ):
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
    result = _native_details(result, installed, audit_path)
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


def _component_material(
    dist: importlib.metadata.Distribution,
    audit: Path,
    tokens: tuple[str, ...],
    blocks: tuple[int, ...],
    version: str = "",
) -> tuple[LicenceInput, ...]:
    found = []
    for entry in dist.files or ():
        name = Path(str(entry)).name.casefold()
        if any(token in name for token in tokens) and any(
            token in name for token in ("license", "licence", "copying", "copyright")
        ):
            path = Path(str(dist.locate_file(entry)))
            if not path.is_file() or not path.stat().st_size:
                raise ValueError(f"notices: {tokens[0]} missing wheel licence material")
            found.append(LicenceInput(path))
    if found:
        return tuple(sorted(found))
    inputs = tuple(LicenceInput(audit, f"text-{number}") for number in blocks)
    for item in inputs:
        source, _data = _audited_material(item)
        # text-36 is shared LGPL text, not a claimed libheif/libde265 release.
        if (
            version
            and item.block_id != "text-36"
            and f"/{version}/" not in source
            and f"/v{version}/" not in source
        ):
            raise ValueError(f"notices: {tokens[0]} upstream source version differs from wheel")
    return inputs


def _native_details(
    rows: list[NoticeRow],
    installed: dict[str, importlib.metadata.Distribution],
    audit: Path,
) -> list[NoticeRow]:
    result: list[NoticeRow] = []
    for row in rows:
        if row.name == "Python" and any(
            Path(label.removeprefix("file:")).name.casefold().startswith(("libcrypto-", "libssl-"))
            for label in row.entries
            if label.startswith("file:")
        ):
            raise ValueError(
                "notices: OpenSSL missing redistributed licence/source material; "
                "the source-install Python audit does not supply it"
            )
        if row.name in {"pyside6-essentials", "shiboken6"}:
            for item in row.licence_inputs:
                if item.block_id == "text-36":
                    source, _data = _audited_material(item)
                    if f"/v{row.version}/" not in source:
                        raise ValueError("notices: Qt upstream source version differs from wheel")
            row = row._replace(
                licence="LGPL-3.0-only (Qt and Shiboken)",
                sources=(
                    *row.sources,
                    f"https://code.qt.io/cgit/qt/qtbase.git/tree/?h=v{row.version}",
                    f"https://code.qt.io/cgit/pyside/pyside-setup.git/tree/?h=v{row.version}",
                ),
                notes=(
                    *row.notes,
                    "Qt and Shiboken are redistributed dynamically linked. "
                    "Users may replace the Qt DLLs and binding libraries, relink them and "
                    "debug modifications, including reverse engineering for that purpose under "
                    "LGPL-3.0. Clearwater imposes no additional restriction. "
                    "Modified distributions must retain corresponding source and installation "
                    "information.",
                ),
            )
        if row.name in {"numpy", "scipy", "pillow"}:
            row = row._replace(
                notes=(
                    *row.notes,
                    "Bundled native libraries and their copyright notices, licence terms and "
                    "source attributions are redistributed in this artifact in the installed "
                    "aggregate texts below.",
                )
            )
        result.append(row)
        if row.name != "pillow-heif":
            continue
        dist = installed["pillow-heif"]
        manifests = [
            item.path for item in row.licence_inputs if item.path.name == "LICENSES_bundled.txt"
        ]
        if len(manifests) != 1:
            raise ValueError("notices: pillow-heif missing unique bundled-component manifest")
        manifest = manifests[0].read_text(encoding="utf-8")
        specs = (
            ("libheif", ("libheif",), (36, 39, 42), "LGPL-3.0-only"),
            ("libde265", ("libde265",), (36, 40, 43), "LGPL-3.0-only"),
            ("x265", ("x265",), (37, 38), "GPL-2.0-or-later"),
            (
                "MinGW-w64 runtime (Windows wheels only)",
                ("mingw", "winpthreads"),
                (41, 44),
                "GPL-3.0 with the GCC Runtime Library Exception; MIT / BSD for winpthreads",
            ),
        )
        for name, tokens, blocks, licence in specs:
            prefixes: tuple[str, ...] = tokens
            if name.startswith("MinGW"):
                prefixes = ("libgcc_s_seh-1", "libstdc++-6", "libwinpthread-1")
            elif name == "x265":
                prefixes = ("libx265",)
            labels = tuple(
                label
                for label in row.entries
                if label.startswith("file:")
                and Path(label.removeprefix("file:")).name.casefold().startswith(prefixes)
            )
            if not labels:
                continue
            section_match = re.search(
                r"(?ms)^Name: " + re.escape(name) + r"\n(.*?)(?=^Name: |\Z)", manifest
            )
            if section_match is None:
                raise ValueError(f"notices: pillow-heif missing source manifest for {name}")
            section = section_match[1]
            source_match = re.search(r"Source code: (https?://\S+)", section)
            version = "not named by wheel"
            notes: tuple[str, ...] = ()
            if source_match:
                source = source_match[1]
                version_match = re.search(r"/tree/v?([0-9][^/\s]*)$", source)
                if version_match is None:
                    raise ValueError(f"notices: {name} missing exact source version in manifest")
                version = version_match[1]
            else:
                details = re.search(r"For details, see (https?://\S+)", section)
                if not name.startswith("MinGW") or details is None:
                    raise ValueError(f"notices: {name} missing source material")
                source = details[1]
                notes = (
                    "For libgcc_s_seh-1.dll, libstdc++-6.dll and libwinpthread-1.dll, "
                    "the wheel does not name the toolchain release. "
                    "The source pointer is unversioned; "
                    "no version-matched source release is claimed.",
                )
            material = _component_material(
                dist, audit, tokens, blocks, "" if name.startswith("MinGW") else version
            )
            if licence.startswith("LGPL"):
                notes += (
                    "Users may replace and relink these LGPL libraries and debug modifications, "
                    "including reverse engineering for that purpose.",
                )
            result.append(
                NoticeRow(
                    "pillow-heif / " + ("MinGW runtime" if name.startswith("MinGW") else name),
                    version,
                    licence,
                    (source,),
                    labels,
                    material,
                    notes,
                )
            )
    return result


def _audited_material(item: LicenceInput) -> tuple[str, bytes]:
    text = item.path.read_text(encoding="utf-8")
    marker = f'<a id="{item.block_id}"></a>'
    if text.count(marker) != 1:
        raise ValueError(f"notices: missing or duplicate audit block {item.block_id}")
    section = text.split(marker, 1)[1].split('<a id="', 1)[0]
    metadata = re.search(
        r"Source: `([^`]+)`\. SHA-256: `([a-f0-9]{64})`\. UTF-8/LF bytes: (\d+)\.",
        section,
    )
    body = re.search(r"(?ms)^````text\n(.*?)^````[ \t]*$", section)
    if metadata is None or body is None:
        raise ValueError(f"notices: {item.block_id} missing hash/byte metadata or text")
    source, expected_hash, expected_size = metadata.groups()
    data = body[1].encode("utf-8")
    if len(data) != int(expected_size):
        raise ValueError(f"notices: {item.block_id} byte count differs from audit")
    if hashlib.sha256(data).hexdigest() != expected_hash:
        raise ValueError(f"notices: {item.block_id} SHA-256 hash differs from audit")
    return source, data


def _wheel_label(path: Path) -> str:
    # Keep local build/profile paths out of the distributable and its deterministic output.
    for index, part in enumerate(path.parts):
        if part.endswith(".dist-info"):
            return Path(*path.parts[index:]).as_posix()
    return path.name


def _cell(value: str) -> str:
    return value.replace("|", "&#124;").replace("\r", " ").replace("\n", " ")


def render_notices(plan: NoticePlan) -> bytes:
    """Render coverage, provenance and verbatim licence bytes deterministically.

    Installed wheel files retain even their embedded GPL texts unchanged. All
    FFmpeg rows share one dedicated FFmpeg licence block; it is absent when the
    release folder carries no FFmpeg. Audited upstream blocks are UTF-8/LF
    copies checked against both recorded integrity fields before use.

    Args:
        plan: An inventory-backed component plan from :func:`plan_notices`.

    Returns:
        The complete Markdown document, encoded as UTF-8 with unchanged input bytes.

    Raises:
        ValueError: Coverage/materials are missing, commercial Qt terms are
            requested, or an audited upstream block fails integrity checks.
        OSError: A licence input cannot be read.
    """
    validate_coverage(plan.entries, plan.rows)
    rows = sorted(plan.rows, key=lambda row: row.name.casefold())
    ffmpeg = any(row.name == "FFmpeg / ffprobe" for row in rows)
    header = [
        "# Clearwater artifact third-party notices",
        "",
        "Clearwater is GPL-2.0-or-later. Copyright and licence terms for each",
        "redistributed component are preserved below. Corresponding source is",
        "available at the versioned source links in each row; FFmpeg build recipes",
        "identify every linked repository and pin. Preserve these notices on redistribution.",
    ]
    if ffmpeg:
        header += [
            "The artifact is a combined work distributed under GPL-3.0 terms where",
            "FFmpeg requires them; Clearwater's or-later grant permits this combination.",
        ]
    header += [
        "",
        *plan.user_obtained,
        "",
        "## Redistributed components",
        "",
        f"Inventory: {len(plan.entries)} entries; {len(rows)} component rows.",
        "",
        "| Component | Version | Licence | Verdict | Corresponding source | Texts |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    materials: dict[LicenceInput, tuple[str, bytes]] = {}
    references: dict[LicenceInput, str] = {}
    for row in rows:
        if not row.licence_inputs:
            raise ValueError(f"notices: {row.name} missing licence material")
        for item in sorted(row.licence_inputs):
            if item in materials:
                continue
            if item.path.name.casefold() == "licenseref-qt-commercial.txt":
                raise ValueError("notices: commercial Qt licence must never be reproduced")
            if item.block_id:
                source, data = _audited_material(item)
                label = f"{row.name} {row.version}; {source}; the 1.0.0 audit's upstream copy"
            else:
                data = item.path.read_bytes()
                label = f"Installed wheel: {row.name} {row.version}; {_wheel_label(item.path)}"
                if item.path.name == "ffmpeg-LICENSE.txt":
                    label = f"Bundled FFmpeg: {row.version}; ffmpeg-LICENSE.txt"
                elif row.name in {"Clearwater", "Python"}:
                    label = f"Build source: {row.name} {row.version}; {item.path.name}"
            if not data:
                raise ValueError(f"notices: {row.name} missing licence material")
            materials[item] = (label, data)
            references[item] = f"licence-{len(materials)}"
        links = ", ".join(
            f"[{references[item]}](#{references[item]})" for item in row.licence_inputs
        )
        header.append(
            "| "
            + " | ".join(
                _cell(value)
                for value in (
                    row.name,
                    row.version,
                    row.licence,
                    row.verdict,
                    "; ".join(row.sources),
                    links,
                )
            )
            + " |"
        )
    header += ["", "## Component details and coverage", ""]
    for row in rows:
        header += [
            f"### {row.name}",
            "",
            *row.notes,
            "",
            "Bundled entries: " + ", ".join(f"`{entry}`" for entry in row.entries),
            "",
        ]
    header += ["## Full licence texts and provenance", ""]
    output = ["\n".join(header).encode("utf-8")]
    for item, (label, data) in materials.items():
        heading = "### " + label
        if item.path.name == "ffmpeg-LICENSE.txt" and not item.block_id:
            heading = "### Bundled FFmpeg GPL-3.0"
        # A fence longer than any backtick run keeps copied Markdown licence files intact.
        longest = max((len(run) for run in re.findall(rb"`+", data)), default=0)
        fence = b"`" * max(4, longest + 1)
        prefix = (
            f'\n<a id="{references[item]}"></a>\n\n{heading}\n\n'
            f"Source: {label}. SHA-256: `{hashlib.sha256(data).hexdigest()}`. "
            f"Bytes: {len(data)}.\n\n"
        ).encode()
        output += [
            prefix,
            fence + b"text\n",
            data,
            b"" if data.endswith(b"\n") else b"\n",
            fence + b"\n",
        ]
    return b"".join(output)


def write_notices(
    folder: Path,
    *,
    audit_path: Path = ROOT / "THIRD_PARTY_NOTICES.md",
    uv_lock_path: Path = ROOT / "uv.lock",
    ffmpeg_lock_path: Path = ROOT / "tools/package/ffmpeg.lock.json",
    distribution: Callable[
        [str], importlib.metadata.Distribution
    ] = importlib.metadata.distribution,
) -> Path:
    """Validate and atomically write the release folder's complete artifact notices.

    The generated file is attributed to Clearwater in its own coverage listing.
    First generation validates all inputs before reserving that output entry,
    then inventories it too. Repeated generation has identical bytes. Failures
    preserve an existing document and remove any newly reserved empty output.

    Args:
        folder: The onedir release folder or a parent containing its executable.
        audit_path: The source-install audit table and verified upstream texts.
        uv_lock_path: The locked distribution versions.
        ffmpeg_lock_path: The FFmpeg provenance and licence lock.
        distribution: Installed wheel metadata resolver.

    Returns:
        The written ``THIRD_PARTY_NOTICES.md`` beside Clearwater's executable.

    Raises:
        ValueError: The folder, coverage, versions or required materials are invalid.
        OSError: Required inputs or the output cannot be read or written.
    """

    def prepare() -> bytes:
        return render_notices(
            plan_notices(
                folder,
                audit_path=audit_path,
                uv_lock_path=uv_lock_path,
                ffmpeg_lock_path=ffmpeg_lock_path,
                distribution=distribution,
            )
        )

    document = prepare()
    executable = cast(Path, _build_tool().find_executable(folder))
    path = executable.parent / "THIRD_PARTY_NOTICES.md"
    reserved = False
    temporary: Path | None = None
    try:
        if not path.exists():
            with path.open("xb"):
                pass
            reserved = True
            document = prepare()
        with tempfile.NamedTemporaryFile(
            dir=path.parent.parent, suffix=".tmp", delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(document)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        reserved = False
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        if reserved:
            path.unlink(missing_ok=True)
    return path


def main(argv: Sequence[str] | None = None) -> int:
    """Generate notices from the command line without launching the artifact.

    Args:
        argv: Arguments, or ``sys.argv[1:]`` when omitted.

    Returns:
        Zero after writing, or one with a single ASCII-safe stderr line on failure.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--audit", type=Path, default=ROOT / "THIRD_PARTY_NOTICES.md")
    parser.add_argument("--uv-lock", type=Path, default=ROOT / "uv.lock")
    parser.add_argument("--ffmpeg-lock", type=Path, default=ROOT / "tools/package/ffmpeg.lock.json")
    options = parser.parse_args(argv)
    try:
        path = write_notices(
            options.folder,
            audit_path=options.audit,
            uv_lock_path=options.uv_lock,
            ffmpeg_lock_path=options.ffmpeg_lock,
            distribution=importlib.metadata.distribution,
        )
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        message = " ".join(str(error).split()).encode("ascii", "backslashreplace").decode("ascii")
        print(f"FAILED: artifact notices: {message}", file=sys.stderr)
        return 1
    print(f"wrote {path}".encode("ascii", "backslashreplace").decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
