"""Generate inventory-driven notices for Clearwater onedir artifacts without running them.

This module inventories the on-disk files and embedded PYZ/boot entries, matches
installed RECORDs to the locked source-install audit, and refuses unsafe release
claims. Third-party licence files are copied verbatim; Clearwater's own licence
is LF-normalized for checkout-independent output. Audited upstream blocks are checked
against their recorded SHA-256 and byte count before reuse.
Declared embedded components bind exact carried-host identities and source pins,
retain their parent's attribution and cannot fall back to parent-only coverage.
No bundled runtime package, product entry point or external binary is executed.
"""

from __future__ import annotations

import argparse
import base64
import fnmatch
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import re
import ssl
import sys
import tempfile
import tomllib
import zipfile
from collections import defaultdict
from collections.abc import Callable, Sequence
from datetime import date
from functools import cache
from pathlib import Path
from types import ModuleType
from typing import Any, NamedTuple, cast
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
SOURCE_URL = "https://github.com/rwsmythe/clearwater"
GPU_NAMES = frozenset({"cuda-pathfinder", "cuda-toolkit", "cupy-cuda12x"})
# Match case-insensitive basenames at every depth before consulting wheel RECORDs.
# The wildcard also catches versioned and delvewheel hash-suffixed runtime names.
THIRD_PARTY_NATIVE_PATTERNS = (
    "vcruntime140*.dll",
    "msvcp140*.dll",
    "vcomp140*.dll",
    "vccorlib140*.dll",
    "vcamp140*.dll",
    "msvcr*.dll",
    "mfc140*.dll",
    "d3dcompiler_*.dll",
    "concrt140.dll",
    "ucrtbase.dll",
    "api-ms-win-*.dll",
    "opengl32sw.dll",
    "libffi*.dll",
    "sqlite3.dll",
    "tcl*.dll",
    "tk*.dll",
    "libcrypto-*.dll",
    "libssl-*.dll",
)
_PROVENANCE_FIELDS = frozenset(
    {
        "provenance_kind",
        "upstream_repository",
        "source_repository",
        "source_commit",
        "source_tag",
        "source_tag_object",
        "source_path",
        "source_archive_url",
        "source_archive_sha256",
        "source_archive_size_bytes",
        "licence_urls",
        "text_source",
        "text_kind",
        "text_lines",
        "attribution",
        "carried_notice",
        "text_file",
        "text_sha256",
        "text_size_bytes",
    }
)


class _TextExcerpt(NamedTuple):
    """A complete source blob and its one-based, inclusive excerpt range."""

    path: Path
    sha256: str
    size_bytes: int
    git_blob_sha1: str
    lines: tuple[int, int]


class LicenceInput(NamedTuple):
    """A real input file or a rooted upstream-audit block, never memory-written text."""

    path: Path
    block_id: str = ""
    sha256: str = ""
    size_bytes: int = 0
    provenance: str = ""
    context: str = ""
    excerpt: _TextExcerpt | None = None
    git_blob_sha1: str = ""
    reference: bool = False
    encoding: str = ""


def _licence_order(item: LicenceInput) -> tuple[list[str], LicenceInput]:
    r"""The sort key of a row's licence texts: Windows path order on every host (WP6.5 C15).

    ``sorted`` on :class:`LicenceInput` compares the ``Path`` first, and ``pathlib`` compares
    paths case-insensitively on Windows only (``WindowsPath`` lower-cases the whole string and
    splits it at ``\``; ``PosixPath`` keeps the case), so the notices' text numbering
    depended on the host. This key is that Windows comparison spelled host-independently:
    the path's ``as_posix()`` lower-cased and split at ``/`` (on Windows the very list
    ``WindowsPath`` compares, so the committed annex keeps its bytes), then the input itself
    for the remaining fields (and, off Windows, the case of an otherwise equal path).

    Args:
        item: One licence input of a row.

    Returns:
        The key ``sorted`` orders the row's texts by.
    """
    return item.path.as_posix().lower().split("/"), item


class NativeFile(NamedTuple):
    """A seat-measured binary identity, selected by basename or relative-path glob."""

    name: str
    relpath_glob: str
    sha256: str
    size_bytes: int
    version_evidence: tuple[str, str] | tuple[()] = ()


class NativeLicence(NamedTuple):
    """A verified native or vendored licence and its strict source/terms provenance."""

    component: str
    bundled_version_source: str
    upstream_version: str
    upstream_repository: str
    source_tag: str
    source_commit: str
    source_archive_url: str
    source_archive_sha256: str
    spdx: str
    licence_input: LicenceInput
    interpreter_release: str
    python_version: str
    bundled_files: tuple[NativeFile, ...]
    version_evidence: tuple[str, str]
    co_licensed_with: tuple[str, ...]
    provenance_kind: str
    source_path: str
    source_urls: tuple[str, ...]
    vendored_distribution: str
    vendored_distribution_version: str
    bundled_modules: tuple[str, ...]
    text_source: LicenceInput | None
    text_source_lines: tuple[int, ...]
    embedded_in: tuple[str, ...]
    attribution_input: LicenceInput | None = None


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


class NoticeLimit(NamedTuple):
    """A verbatim limits statement bound to declared, census-verified host paths."""

    component: str
    hosts: tuple[str, ...]
    statement: str


class NoticePlan(NamedTuple):
    """Validated entry coverage plus separately obtained component statements."""

    entries: tuple[str, ...]
    rows: tuple[NoticeRow, ...]
    user_obtained: tuple[str, ...]
    limits: tuple[NoticeLimit, ...] = ()


class _AuditRow(NamedTuple):
    name: str
    version: str
    licence: str
    sources: tuple[str, ...]


class _Entry(NamedTuple):
    label: str
    name: str
    kind: str


class _EmbeddedHost(NamedTuple):
    """An exact carried-host identity and its independently declared source set."""

    relpath: str
    sha256: str
    size_bytes: int
    parent: str
    parent_version: str
    components: tuple[tuple[str, str], ...]


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


def _native_text(path: Path, sha256: str, size: int, context: str = "") -> bytes:
    prefix = "notices: " + context
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{prefix}native licence text missing or linked: {path.name}")
    data = path.read_bytes()
    if len(data) != size:
        raise ValueError(f"{prefix}native licence text byte count differs: {path.name}")
    if hashlib.sha256(data).hexdigest() != sha256:
        raise ValueError(f"{prefix}native licence text SHA-256 hash differs: {path.name}")
    return data


def _source_identity(row: dict[str, Any]) -> str:
    return json.dumps({key: row[key] for key in _PROVENANCE_FIELDS if key in row}, sort_keys=True)


def _git_text_lines(row: dict[str, Any]) -> dict[str, Any] | None:
    source = row.get("text_lines")
    if "text_lines" not in row:
        return None
    if (
        row.get("provenance_kind") != "git-tree"
        or row.get("text_kind") != "excerpt"
        or not row.get("source_path")
        or not isinstance(source, dict)
        or set(source) != {"file", "lines", "git_blob_sha1", "sha256", "size_bytes"}
        or not _exact_host_path(source.get("file"))
        or "/" in source["file"]
        or source["file"] == "manifest.json"
        or not isinstance(source.get("lines"), list)
        or len(source["lines"]) != 2
        or any(type(line) is not int for line in source["lines"])
        or not 1 <= source["lines"][0] <= source["lines"][1]
        or not isinstance(source.get("git_blob_sha1"), str)
        or re.fullmatch(r"[0-9a-f]{40}", source["git_blob_sha1"]) is None
        or not isinstance(source.get("sha256"), str)
        or re.fullmatch(r"[0-9a-f]{64}", source["sha256"]) is None
        or type(source.get("size_bytes")) is not int
        or source["size_bytes"] <= 0
    ):
        raise ValueError("notices: native git-tree text_lines missing/invalid")
    return cast(dict[str, Any], source)


def _licence_bytes(item: LicenceInput) -> bytes:
    data = _native_text(item.path, item.sha256, item.size_bytes, item.context)
    if item.git_blob_sha1:
        digest = hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data)
        if digest.hexdigest() != item.git_blob_sha1:
            raise ValueError(f"notices: {item.context}attribution Git blob SHA-1 differs")
    source = item.excerpt
    if source is not None:
        blob = _native_text(source.path, source.sha256, source.size_bytes, item.context)
        digest = hashlib.sha1(b"blob " + str(len(blob)).encode("ascii") + b"\0" + blob)
        if digest.hexdigest() != source.git_blob_sha1:
            raise ValueError(f"notices: {item.context}source Git blob SHA-1 differs")
        lines = _lf_lines(blob)
        first, last = source.lines
        if last > len(lines) or b"".join(lines[first - 1 : last]) != data:
            raise ValueError(f"notices: {item.context}excerpt differs from source line range")
    return data


def _lf_lines(data: bytes) -> list[bytes]:
    parts = data.split(b"\n")
    return [part + b"\n" for part in parts[:-1]] + ([parts[-1]] if parts[-1] else [])


def _single_line_text(value: object) -> bool:
    return bool(
        isinstance(value, str)
        and value
        and value == value.strip()
        and not any(
            ord(char) < 32 or 127 <= ord(char) <= 159 or char in "\u2028\u2029" for char in value
        )
    )


def _attribution_spec(row: dict[str, Any]) -> dict[str, Any] | None:
    item = row.get("attribution")
    if "attribution" not in row:
        return None
    if (
        row.get("provenance_kind") != "git-tree"
        or not isinstance(item, dict)
        or set(item) != {"file", "sha256", "size_bytes", "git_blob_sha1", "source_path"}
        or not _exact_host_path(item.get("file"))
        or "/" in item["file"]
        or item["file"] == "manifest.json"
        or not _exact_host_path(item.get("source_path"))
        or not isinstance(item.get("sha256"), str)
        or re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) is None
        or not isinstance(item.get("git_blob_sha1"), str)
        or re.fullmatch(r"[0-9a-f]{40}", item["git_blob_sha1"]) is None
        or type(item.get("size_bytes")) is not int
        or item["size_bytes"] <= 0
    ):
        raise ValueError("notices: native git-tree attribution missing/invalid")
    return cast(dict[str, Any], item)


def _exact_host_path(value: object) -> bool:
    return bool(
        isinstance(value, str)
        and value
        and value == value.strip()
        and not any(char in value for char in "\\:?*[]")
        and all(part not in {"", ".", ".."} for part in value.split("/"))
    )


def _embedded_declarations(document: dict[str, Any]) -> tuple[_EmbeddedHost, ...]:
    values = document.get("embedded_hosts", [])
    if not isinstance(values, list):
        raise ValueError("notices: embedded_hosts must be a list")
    result: list[_EmbeddedHost] = []
    seen: set[str] = set()
    for item in values:
        if (
            not isinstance(item, dict)
            or set(item)
            != {"relpath", "sha256", "size_bytes", "parent", "parent_version", "components"}
            or not _exact_host_path(item.get("relpath"))
            or not isinstance(item.get("sha256"), str)
            or re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) is None
            or type(item.get("size_bytes")) is not int
            or item["size_bytes"] <= 0
            or not isinstance(item.get("parent"), str)
            or re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", item["parent"]) is None
            or not _single_line_text(item.get("parent_version"))
            or not isinstance(item.get("components"), list)
            or not item["components"]
        ):
            raise ValueError("notices: embedded host declaration is invalid")
        if item["relpath"].casefold() in seen:
            raise ValueError("notices: embedded host declaration is duplicate")
        seen.add(item["relpath"].casefold())
        components: list[tuple[str, str]] = []
        for reference in item["components"]:
            if (
                not isinstance(reference, dict)
                or set(reference) != {"component", "source"}
                or not isinstance(reference.get("component"), str)
                or not reference["component"].strip()
                or reference["component"] != reference["component"].strip()
                or reference["component"] in {name for name, _pin in components}
                or not isinstance(reference.get("source"), dict)
                or set(reference["source"]) - _PROVENANCE_FIELDS
            ):
                raise ValueError(
                    f"notices: embedded {item['relpath']} component declaration invalid"
                )
            try:
                if "carried_notice" in reference["source"]:
                    _carried_notice(reference["source"], source_only=True)
                else:
                    _provenance(reference["source"])
            except ValueError as error:
                raise ValueError(
                    f"notices: embedded {item['relpath']} "
                    f"component {reference['component']}: {error}"
                ) from error
            components.append((reference["component"], _source_identity(reference["source"])))
        result.append(
            _EmbeddedHost(
                item["relpath"],
                item["sha256"],
                item["size_bytes"],
                item["parent"],
                item["parent_version"],
                tuple(components),
            )
        )
    return tuple(result)


def _limit_declarations(
    document: dict[str, Any], hosts: tuple[_EmbeddedHost, ...]
) -> tuple[NoticeLimit, ...]:
    values = document.get("limits", [])
    if not isinstance(values, list):
        raise ValueError("notices: limits must be a list")
    declared = {host.relpath for host in hosts}
    seen: set[str] = set()
    result: list[NoticeLimit] = []
    for item in values:
        if (
            not isinstance(item, dict)
            or set(item) != {"component", "hosts", "statement"}
            or any(not _single_line_text(item.get(key)) for key in ("component", "statement"))
            or not isinstance(item.get("hosts"), list)
            or not item["hosts"]
            or any(not _exact_host_path(host) for host in item["hosts"])
        ):
            raise ValueError("notices: limits entry schema is invalid")
        paths = item["hosts"]
        if paths != sorted(paths) or len({path.casefold() for path in paths}) != len(paths):
            raise ValueError("notices: limits hosts must be sorted and duplicate-free")
        for path in paths:
            if path not in declared:
                raise ValueError(f"notices: limits {item['component']} host {path} is undeclared")
        if item["component"] in seen:
            raise ValueError("notices: limits has duplicate component names")
        seen.add(item["component"])
        result.append(NoticeLimit(item["component"], tuple(paths), item["statement"]))
    return tuple(sorted(result))


def _carried_notice(row: dict[str, Any], *, source_only: bool = False) -> dict[str, Any]:
    value = row.get("carried_notice")
    fields = {
        "component",
        "upstream_version",
        "spdx",
        "version_evidence",
        "embedded_in",
        "carried_notice",
    }
    if (
        set(row) != ({"carried_notice"} if source_only else fields)
        or not isinstance(value, dict)
        or set(value) != {"row", "inputs"}
        or not isinstance(value.get("row"), str)
        or not value["row"].strip()
        or value["row"] != value["row"].strip()
        or not isinstance(value.get("inputs"), list)
        or not value["inputs"]
    ):
        raise ValueError("notices: embedded carried notice reference is invalid")
    identities = set()
    for item in value["inputs"]:
        if (
            not isinstance(item, dict)
            or set(item) != {"sha256", "size_bytes"}
            or not isinstance(item.get("sha256"), str)
            or re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) is None
            or type(item.get("size_bytes")) is not int
            or item["size_bytes"] <= 0
        ):
            raise ValueError("notices: embedded carried notice input identity is invalid")
        identity = (item["sha256"], item["size_bytes"])
        if identity in identities:
            raise ValueError("notices: embedded carried notice has duplicate inputs")
        identities.add(identity)
    if not source_only:
        if any(
            not isinstance(row[key], str) or not row[key].strip() or row[key] != row[key].strip()
            for key in ("component", "upstream_version", "spdx")
        ):
            raise ValueError("notices: embedded carried notice metadata is invalid")
        evidence = row["version_evidence"]
        if (
            not isinstance(evidence, dict)
            or set(evidence) != {"method", "value"}
            or not isinstance(evidence.get("method"), str)
            or evidence.get("method")
            not in {"embedded_string", "interpreter_build_record", "vendored_in_tree_path"}
            or not isinstance(evidence.get("value"), str)
            or not evidence["value"].strip()
        ):
            raise ValueError("notices: embedded carried notice version evidence is invalid")
    return cast(dict[str, Any], value)


def _embedded_bindings(row: dict[str, Any], hosts: tuple[_EmbeddedHost, ...]) -> tuple[str, ...]:
    if "embedded_in" not in row:
        return ()
    values = row["embedded_in"]
    if (
        not isinstance(values, list)
        or not values
        or any(not _exact_host_path(value) for value in values)
        or len({value.casefold() for value in values}) != len(values)
        or set(row)
        & {
            "bundled_files",
            "bundled_modules",
            "bundled_version_source",
            "vendored_distribution",
            "vendored_distribution_version",
            "co_licensed_with",
        }
    ):
        raise ValueError(
            "notices: embedded_in requires unique exact hosts and no other binding kind"
        )
    for value in values:
        if not any(
            host.relpath == value and row["component"] in {name for name, _pin in host.components}
            for host in hosts
        ):
            raise ValueError(
                f"notices: embedded {value} component {row['component']} is undeclared"
            )
    return tuple(values)


def _embedded_claims(
    entries: list[_Entry], home: Path, hosts: tuple[_EmbeddedHost, ...], document: dict[str, Any]
) -> tuple[dict[str, list[tuple[str, str]]], dict[str, _EmbeddedHost]]:
    claims: dict[str, list[tuple[str, str]]] = defaultdict(list)
    carried: dict[str, _EmbeddedHost] = {}
    rows = (
        {
            row.get("component"): row
            for row in document.get("components", [])
            if isinstance(row, dict) and isinstance(row.get("component"), str)
        }
        if isinstance(document.get("components"), list)
        else {}
    )
    inventory = {entry.name.casefold(): entry for entry in entries if entry.kind == "file"}
    identities: dict[tuple[str, int], list[_EmbeddedHost]] = defaultdict(list)
    for host in hosts:
        identities[(host.sha256, host.size_bytes)].append(host)
    sizes = {size for _digest, size in identities}
    for candidate in inventory.values():
        path = home / candidate.name
        size = path.stat().st_size
        if size not in sizes:
            continue
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        matching = identities.get((digest, size), [])
        if matching and candidate.name.casefold() not in {
            host.relpath.casefold() for host in matching
        }:
            raise ValueError(
                f"notices: embedded {matching[0].relpath} moved to undeclared path "
                f"{candidate.name}; re-census required"
            )
    for host in hosts:
        entry = inventory.get(host.relpath.casefold())
        if entry is None:
            continue
        data = (home / entry.name).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if (digest, len(data)) != (host.sha256, host.size_bytes):
            raise ValueError(
                f"notices: embedded {entry.name} identity differs: expected SHA-256 {host.sha256} "
                f"size {host.size_bytes}; actual SHA-256 {digest} size {len(data)}; "
                "re-census required"
            )
        for component, pin in host.components:
            row = rows.get(component)
            if (
                row is None
                or not isinstance(row.get("embedded_in"), list)
                or host.relpath not in row["embedded_in"]
            ):
                raise ValueError(
                    f"notices: embedded {entry.name} component {component} "
                    "missing licence row/binding"
                )
            if _source_identity(row) != pin:
                raise ValueError(
                    f"notices: embedded {entry.name} component {component} source pin differs"
                )
            claims[component].append((entry.label, digest))
        carried[entry.label] = host
    return claims, carried


def _check_embedded_parents(
    hosts: tuple[_EmbeddedHost, ...],
    carried: dict[str, _EmbeddedHost],
    selected: dict[str, list[str]],
    installed: dict[str, importlib.metadata.Distribution],
    runtime: set[str],
) -> None:
    carried_paths = {host.relpath for host in carried.values()}
    for host in hosts:
        if host.parent != "python" and host.parent not in runtime:
            raise ValueError(
                f"notices: embedded {host.relpath} parent {host.parent}: "
                "declared parent unknown to this build; re-census required"
            )
        if not selected.get(host.parent):
            continue
        if host.parent == "python":
            marker = Path(sys.base_prefix) / "BUILD"
            release = marker.read_text(encoding="utf-8").strip() if marker.is_file() else "unknown"
            version = (
                ".".join(map(str, sys.version_info[:3])) + f" (python-build-standalone {release})"
            )
        else:
            version = installed[host.parent].version
        if version != host.parent_version:
            raise ValueError(
                f"notices: embedded {host.relpath} parent {host.parent} version differs: "
                f"expected {host.parent_version}; actual {version}; re-census required"
            )
        if host.relpath not in carried_paths:
            raise ValueError(
                f"notices: embedded {host.relpath} absent while parent {host.parent} "
                "is carried; re-census required"
            )


def _https_url(value: object) -> bool:
    if not isinstance(value, str) or value != value.strip():
        return False
    url = urlsplit(value)
    return bool(
        url.scheme == "https"
        and url.hostname
        and not (url.username or url.password or url.query or url.fragment)
    )


def _provenance(row: dict[str, Any]) -> tuple[str, tuple[str, ...]]:
    kind = row.get("provenance_kind")
    text_lines = _git_text_lines(row)
    _attribution_spec(row)
    archive = {
        "upstream_repository",
        "source_tag",
        "source_tag_object",
        "source_commit",
        "source_archive_url",
        "source_archive_sha256",
        "source_archive_size_bytes",
        "source_path",
    }
    tree = {"source_repository", "source_commit", "source_tag", "source_tag_object", "source_path"}
    proprietary = {"licence_urls", "text_source"}
    all_fields = archive | tree | proprietary
    if kind not in ("release-archive", "git-tree", "proprietary-redistributable"):
        raise ValueError("notices: native provenance_kind missing/unknown")
    allowed = archive if kind == "release-archive" else tree if kind == "git-tree" else proprietary
    if (set(row) & all_fields) - allowed:
        raise ValueError("notices: native provenance mixes fields of different kinds")
    if (
        kind != "proprietary-redistributable"
        and row.get("text_kind") == "excerpt"
        and text_lines is None
    ):
        raise ValueError(
            "notices: native provenance excerpt requires proprietary kind or text_lines"
        )
    if kind == "proprietary-redistributable":
        source = row.get("text_source")
        urls = row.get("licence_urls")
        if (
            row.get("text_kind") != "excerpt"
            or not isinstance(source, dict)
            or set(source) != {"file", "lines", "sha256", "size_bytes"}
            or source.get("file") != "<build interpreter>/LICENSE.txt"
            or not isinstance(source.get("sha256"), str)
            or re.fullmatch(r"[0-9a-f]{64}", source["sha256"]) is None
            or type(source.get("size_bytes")) is not int
            or source["size_bytes"] <= 0
            or not isinstance(urls, list)
            or len(urls) < 2
            or any(not _https_url(url) for url in urls)
            or len(set(urls)) != len(urls)
        ):
            raise ValueError(
                "notices: native proprietary provenance needs hashed excerpt and licence URLs"
            )
        return (
            f"proprietary redistributable; audited text source SHA-256 {source['sha256']}; "
            f"source bytes {source['size_bytes']}",
            tuple(urls),
        )
    required = (
        archive - {"source_path"}
        if kind == "release-archive"
        else {"source_repository", "source_commit"}
    )
    if not required <= set(row):
        raise ValueError("notices: native provenance missing source fields")
    for key in required - {"source_archive_size_bytes"}:
        if not isinstance(row[key], str) or not row[key] or row[key] != row[key].strip():
            raise ValueError(f"notices: native provenance invalid {key}")
    for key, length in (
        ("source_commit", 40),
        ("source_tag_object", 40),
        ("source_archive_sha256", 64),
    ):
        if key in row and (
            not isinstance(row[key], str)
            or re.fullmatch(r"[0-9a-f]{" + str(length) + "}", row[key]) is None
        ):
            raise ValueError(f"notices: native provenance invalid {key}")
    path = row.get("source_path", "")
    if "source_path" in row and (
        not isinstance(path, str)
        or not path
        or path != path.strip()
        or "\\" in path
        or ":" in path
        or any(part in {"", ".", ".."} for part in path.split("/"))
    ):
        raise ValueError("notices: native provenance unsafe source_path")
    if kind == "release-archive":
        if (
            not _https_url(row["upstream_repository"])
            or not _https_url(row["source_archive_url"])
            or type(row["source_archive_size_bytes"]) is not int
            or row["source_archive_size_bytes"] <= 0
        ):
            raise ValueError("notices: native provenance invalid archive URL/size")
        repository_url = row["upstream_repository"]
        if urlsplit(repository_url).hostname == "github.com":
            repository_url += "/tree/" + row["source_tag"]
        return (
            f"upstream tag {row['source_tag']}, commit {row['source_commit']}; "
            f"source archive {row['source_archive_url']}; "
            f"published SHA-256 {row['source_archive_sha256']}"
            + (f"; archive member {path}" if path else ""),
            (repository_url, row["source_archive_url"]),
        )
    if not _https_url(row["source_repository"]):
        raise ValueError("notices: native provenance invalid source_repository")
    if ("source_tag" in row) != ("source_tag_object" in row):
        raise ValueError("notices: native provenance requires tag/object pair")
    if "source_tag" in row and (
        not isinstance(row["source_tag"], str)
        or not row["source_tag"].strip()
        or row["source_tag"] != row["source_tag"].strip()
    ):
        raise ValueError("notices: native provenance invalid source_tag")
    label = f"git tree {row['source_repository']} at commit {row['source_commit']}"
    if "source_tag" in row:
        label += f"; annotated tag {row['source_tag']}, object {row['source_tag_object']}"
    if path:
        label += f"; in-tree path {path}"
    if text_lines is not None:
        label += (
            f"; Git blob SHA-1 {text_lines['git_blob_sha1']}; "
            f"verbatim excerpt, lines {text_lines['lines'][0]}-{text_lines['lines'][1]}"
        )
    return label, (
        row["source_repository"] + "/tree/" + row["source_commit"] + ("/" + path if path else ""),
    )


def _native_document(folder: Path) -> dict[str, Any]:
    manifest = folder / "manifest.json"
    if folder.is_symlink() or manifest.is_symlink() or not manifest.is_file():
        raise ValueError("notices: native licence manifest missing or linked")
    try:
        document = json.loads(manifest.read_text(encoding="utf-8"))
    except ValueError as error:
        raise ValueError("notices: native licence manifest is not valid JSON") from error
    if (
        not isinstance(document, dict)
        or not {"schema_version", "interpreter_build", "components"} <= set(document)
        or set(document)
        - {
            "schema_version",
            "interpreter_build",
            "components",
            "vendored_paths",
            "embedded_hosts",
            "limits",
        }
        or type(document.get("schema_version")) is not int
        or document["schema_version"] != 1
        or not isinstance(document.get("components"), list)
    ):
        raise ValueError("notices: native licence manifest schema is invalid")
    return document


def load_native_licences(folder: Path) -> tuple[NativeLicence, ...]:
    """Validate the committed seat-fetched native licence surface, without fetching.

    Every component needs one strict provenance kind: release-archive (published
    archive hash/size, source tag identity and optional member source_path),
    git-tree (exact repository commit,
    optional paired annotated tag and an in-tree path for a subtree), or
    proprietary-redistributable (hashed interpreter excerpt and licence URLs).
    All kinds require version evidence and a real text with matching hash/size.
    Every file other than the manifest needs a component reference. Symlinks,
    unsafe paths, duplicate components, unknown keys and mixed provenance fail.
    A row needs a supported version source, bundled_files or vendored module
    bindings. Declared vendored paths require their own block when carried. Each
    identity has exactly one name or relpath_glob, a SHA-256 and a positive byte
    count; matching is case-insensitive. Globs are relative to the executable's
    folder, and fnmatch's ``*`` crosses ``/``. Use relpath_glob when binding
    several copies of one basename. Co-licensed shared hashes require mutual
    links, with every linked row present for each carried file.
    File bindings may include per-file PE version evidence (required for the
    proprietary runtime). Version sources alone never claim bundled files.
    OpenSSL additionally checks the build interpreter's OpenSSL, CPython and
    build-release versions; proprietary excerpts bind to its actual LICENSE.txt.
    Optional embedded_hosts declares exact relative host paths, hashes, sizes,
    normalized parent owners and required component/source records. Component
    rows use embedded_in (a list of declared paths) instead of another binding
    kind. Carried hosts require all rows and matching source pins before parent
    ownership is considered; absent hosts produce no embedded claims.
    Optional limits is a list of exact component/hosts/statement objects.
    Component and statement are nonempty, unpadded strings; hosts is a nonempty,
    sorted, duplicate-free list of declared embedded host paths. Component names
    are unique. Planning retains only carried hosts after the same identity
    checks as embedded rows; all-absent statements are omitted. Limits carry no
    text file or provenance kind and do not replace a component's text row.
    Git-tree excerpts require text_kind="excerpt" and text_lines: file (a local
    full-blob filename), lines (one-based inclusive pair), git_blob_sha1, sha256
    and size_bytes. The complete blob and exact slice are checked at load and
    render; source_path identifies that blob in the pinned tree.
    Optional git-tree attribution supplies file, sha256, size_bytes,
    git_blob_sha1 and source_path for a separate, verbatim copyright input
    from the same pinned tree. It is checked and rendered with the terms.
    An embedded carried_notice reference instead has exactly component,
    upstream_version, spdx, version_evidence, embedded_in and carried_notice.
    The reference has row (an existing carried notice row) and inputs (unique
    sha256/size_bytes pairs). It cannot mix source/text fields or chain to
    another reference. Its independent host declaration pins this reference
    in source instead of a provenance kind. Planning resolves it against the
    original carried row and rendering rechecks every reused input. Such
    references create no local text file or additional provenance kind.

    Args:
        folder: The committed native-licences folder, or a local test copy.

    Returns:
        Verified local native inputs. Carried-notice references are validated
        here and resolved during planning. Bundled versions are checked
        separately when the inventory carries the associated binaries.

    Raises:
        ValueError: Schema, provenance, file coverage or text integrity is invalid.
        OSError: An input cannot be read.
    """
    document = _native_document(folder)
    _vendored_declarations(document)
    embedded_hosts = _embedded_declarations(document)
    _limit_declarations(document, embedded_hosts)
    build = document.get("interpreter_build")
    if (
        not isinstance(build, dict)
        or set(build) != {"provider", "release", "python_version"}
        or build.get("provider") != "python-build-standalone"
        or not isinstance(build.get("release"), str)
        or re.fullmatch(r"[0-9]{8}", build["release"]) is None
        or not isinstance(build.get("python_version"), str)
        or re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", build["python_version"]) is None
    ):
        raise ValueError("notices: native licence interpreter build record is invalid")
    string_fields = (
        "component",
        "upstream_version",
        "spdx",
        "text_file",
        "text_sha256",
        "fetch_date",
        "fetched_by",
    )
    result: list[NativeLicence] = []
    components: set[str] = set()
    files = {"manifest.json"}
    claims: dict[str, set[str]] = defaultdict(set)
    for row in document["components"]:
        if isinstance(row, dict) and "carried_notice" in row:
            _carried_notice(row)
            if row["component"] in components:
                raise ValueError("notices: native licence manifest has duplicate component rows")
            components.add(row["component"])
            if not _embedded_bindings(row, embedded_hosts):
                raise ValueError("notices: embedded carried notice requires host bindings")
            continue
        if not isinstance(row, dict) or any(
            not isinstance(row.get(key), str) or not row[key] or row[key] != row[key].strip()
            for key in string_fields
        ):
            raise ValueError("notices: native licence row has missing/invalid string fields")
        allowed = {
            *string_fields,
            "text_size_bytes",
            "source_archive_size_bytes",
            "bundled_version_source",
            "bundled_files",
            "version_evidence",
            "co_licensed_with",
            "text_kind",
            "text_source",
            "provenance_kind",
            "upstream_repository",
            "source_repository",
            "source_tag",
            "source_tag_object",
            "source_commit",
            "source_path",
            "source_archive_url",
            "source_archive_sha256",
            "licence_urls",
            "vendored_distribution",
            "vendored_distribution_version",
            "bundled_modules",
            "embedded_in",
            "text_lines",
            "attribution",
        }
        if set(row) - allowed:
            raise ValueError("notices: native licence row has unknown keys")
        provenance, source_urls = _provenance(row)
        evidence = row.get("version_evidence")
        if (
            not isinstance(evidence, dict)
            or set(evidence) != {"method", "value"}
            or not isinstance(evidence.get("method"), str)
            or evidence.get("method")
            not in {
                "pe_file_version",
                "interpreter_build_record",
                "embedded_string",
                "ssl.OPENSSL_VERSION",
                "vendored_submodule_commit",
                "vendored_in_tree_path",
            }
            or not isinstance(evidence.get("value"), str)
            or not evidence["value"].strip()
            or evidence["value"] != evidence["value"].strip()
        ):
            raise ValueError("notices: native version_evidence is missing/invalid")
        links = row.get("co_licensed_with", [])
        if (
            not isinstance(links, list)
            or any(
                not isinstance(link, str)
                or not link.strip()
                or link != link.strip()
                or link == row["component"]
                for link in links
            )
            or len(set(links)) != len(links)
        ):
            raise ValueError("notices: native co_licensed_with is invalid")
        kind = row.get("text_kind", "full")
        source = row.get("text_source")
        if not isinstance(kind, str) or kind not in {"full", "excerpt"}:
            raise ValueError("notices: native text_kind is invalid")
        if ((kind == "excerpt" and "text_lines" not in row) or source is not None) and (
            not isinstance(source, dict)
            or set(source) not in ({"file", "lines"}, {"file", "lines", "sha256", "size_bytes"})
            or not isinstance(source.get("file"), str)
            or not source["file"].strip()
            or not isinstance(source.get("lines"), list)
            or len(source["lines"]) != 2
            or any(type(line) is not int for line in source["lines"])
            or not 1 <= source["lines"][0] <= source["lines"][1]
        ):
            raise ValueError("notices: native excerpt text_source is missing/invalid")
        version_source = row.get("bundled_version_source", "")
        if "bundled_version_source" in row and (
            row["component"] != "OpenSSL" or version_source != "ssl.OPENSSL_VERSION"
        ):
            raise ValueError(
                "notices: native licence row has an unsupported version-source binding"
            )
        bindings = _native_file_bindings(row, claims)
        if "co_licensed_with" in row and not bindings:
            raise ValueError("notices: native co_licensed_with requires non-empty file bindings")
        module_bindings = _vendored_bindings(row, document)
        embedded_in = _embedded_bindings(row, embedded_hosts)
        if not version_source and not bindings and not module_bindings and not embedded_in:
            raise ValueError("notices: native licence row missing version/file binding")
        if row["component"] in components:
            raise ValueError("notices: native licence manifest has duplicate component rows")
        components.add(row["component"])
        if re.fullmatch(r"[0-9a-f]{64}", row["text_sha256"]) is None:
            raise ValueError("notices: native licence row has invalid text_sha256")
        if type(row.get("text_size_bytes")) is not int or row["text_size_bytes"] <= 0:
            raise ValueError("notices: native licence row has invalid text_size_bytes")
        if row["component"] == "OpenSSL" and (
            row["provenance_kind"] != "release-archive"
            or re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+[a-z]?", row["upstream_version"]) is None
            or row["source_tag"] != "openssl-" + row["upstream_version"]
            or row["spdx"] != "Apache-2.0"
        ):
            raise ValueError(
                "notices: native OpenSSL provenance/version/licence fields are invalid"
            )
        if row["fetched_by"] != "seat":
            raise ValueError("notices: native licence input must be fetched by seat")
        try:
            if date.fromisoformat(row["fetch_date"]).isoformat() != row["fetch_date"]:
                raise ValueError("not ISO date")
        except ValueError as error:
            raise ValueError("notices: native licence row has invalid fetch_date") from error
        filename = row["text_file"]
        if filename in {".", "..", "manifest.json"} or "/" in filename or "\\" in filename:
            raise ValueError("notices: native licence row has unsafe text_file")
        path = folder / filename
        context = (
            f"embedded {', '.join(embedded_in)} component {row['component']}: "
            if embedded_in
            else ""
        )
        files.add(filename)
        provenance = (
            f"Seat-verified native input: {row['component']} {row['upstream_version']}; "
            + provenance
            + f"; fetched by seat on {row['fetch_date']}"
        )
        if source is not None:
            provenance += (
                f"; verbatim {kind} from {source['file']}, "
                f"lines {source['lines'][0]}-{source['lines'][1]}"
            )
        text_lines = _git_text_lines(row)
        excerpt = None
        if text_lines is not None:
            files.add(text_lines["file"])
            excerpt = _TextExcerpt(
                folder / text_lines["file"],
                text_lines["sha256"],
                text_lines["size_bytes"],
                text_lines["git_blob_sha1"],
                (text_lines["lines"][0], text_lines["lines"][1]),
            )
        licence_input = LicenceInput(
            path,
            sha256=row["text_sha256"],
            size_bytes=row["text_size_bytes"],
            provenance=provenance,
            context=context,
            excerpt=excerpt,
        )
        _licence_bytes(licence_input)
        attribution = _attribution_spec(row)
        attribution_input = None
        if attribution is not None:
            files.add(attribution["file"])
            attribution_input = LicenceInput(
                folder / attribution["file"],
                sha256=attribution["sha256"],
                size_bytes=attribution["size_bytes"],
                provenance=(
                    f"Seat-verified attribution: {row['component']}; "
                    f"{row['source_repository']} at commit {row['source_commit']}; "
                    f"in-tree path {attribution['source_path']}; "
                    f"Git blob SHA-1 {attribution['git_blob_sha1']}"
                ),
                context=context,
                git_blob_sha1=attribution["git_blob_sha1"],
            )
            _licence_bytes(attribution_input)
        result.append(
            NativeLicence(
                row["component"],
                version_source,
                row["upstream_version"],
                cast(str, row.get("upstream_repository", row.get("source_repository", ""))),
                row.get("source_tag", ""),
                row.get("source_commit", ""),
                row.get("source_archive_url", ""),
                row.get("source_archive_sha256", ""),
                row["spdx"],
                licence_input,
                build["release"],
                build["python_version"],
                bindings,
                (evidence["method"], evidence["value"]),
                tuple(links),
                row["provenance_kind"],
                row.get("source_path", ""),
                source_urls,
                row.get("vendored_distribution", ""),
                row.get("vendored_distribution_version", ""),
                module_bindings,
                LicenceInput(
                    Path(sys.base_prefix) / "LICENSE.txt",
                    sha256=source["sha256"],
                    size_bytes=source["size_bytes"],
                )
                if row["provenance_kind"] == "proprietary-redistributable" and source is not None
                else None,
                tuple(source["lines"]) if source is not None else (),
                embedded_in,
                attribution_input,
            )
        )
    by_name = {record.component: record for record in result}
    for record in result:
        for link in record.co_licensed_with:
            if link not in by_name or record.component not in by_name[link].co_licensed_with:
                raise ValueError("notices: native co_licensed_with has dangling/asymmetric link")
            if {(b.sha256, b.size_bytes) for b in record.bundled_files} != {
                (b.sha256, b.size_bytes) for b in by_name[link].bundled_files
            }:
                raise ValueError("notices: native co-licensed rows must bind the same file hashes")
    for owners in claims.values():
        if len(owners) > 1 and any(
            owners != {owner, *by_name[owner].co_licensed_with} for owner in owners
        ):
            raise ValueError(
                "notices: native manifest has duplicate file claim without co-licensing"
            )
    # FFmpeg stage/runtime texts have their own lock and integrity checks in
    # _ffmpeg_rows. Other unclaimed files/directories still fail closed here.
    actual = {
        path.name
        for path in folder.iterdir()
        if not (path.name in {"ffmpeg-toolchain", "ffmpeg-components"} and path.is_dir())
    }
    if actual != files:
        raise ValueError(
            "notices: native licence files without manifest rows: "
            + ", ".join(sorted(actual - files))
        )
    return tuple(result)


def _vendored_declarations(document: dict[str, Any]) -> tuple[tuple[str, str, str], ...]:
    values = document.get("vendored_paths", [])
    if not isinstance(values, list):
        raise ValueError("notices: vendored paths must be a list")
    result: list[tuple[str, str, str]] = []
    for item in values:
        if (
            not isinstance(item, dict)
            or set(item) != {"distribution", "module", "component"}
            or any(
                not isinstance(item.get(key), str)
                or not item[key].strip()
                or item[key] != item[key].strip()
                for key in item
            )
        ):
            raise ValueError("notices: vendored path declaration is invalid")
        distribution, module, component = item["distribution"], item["module"], item["component"]
        if _normalize(distribution) != distribution or not all(
            part.isidentifier() for part in module.split(".")
        ):
            raise ValueError("notices: vendored distribution/module declaration is invalid")
        if any(
            module == previous
            or module.startswith(previous + ".")
            or previous.startswith(module + ".")
            for _dist, previous, _component in result
        ):
            raise ValueError("notices: vendored path declarations overlap")
        result.append((distribution, module, component))
    return tuple(result)


def _vendored_bindings(row: dict[str, Any], document: dict[str, Any]) -> tuple[str, ...]:
    fields = {"vendored_distribution", "vendored_distribution_version", "bundled_modules"}
    required = fields - {"bundled_modules"}
    if not set(row) & fields:
        return ()
    if (
        not required <= set(row)
        or not isinstance(row["vendored_distribution"], str)
        or _normalize(row["vendored_distribution"]) != row["vendored_distribution"]
        or not isinstance(row["vendored_distribution_version"], str)
        or not row["vendored_distribution_version"].strip()
        or row["vendored_distribution_version"] != row["vendored_distribution_version"].strip()
        or row["version_evidence"]["method"]
        not in {"vendored_submodule_commit", "vendored_in_tree_path"}
        or not isinstance(row.get("bundled_modules", []), list)
        or (not row.get("bundled_modules") and not row.get("bundled_files"))
    ):
        raise ValueError("notices: vendored block binding/version evidence invalid")
    roots = [
        module
        for dist, module, component in _vendored_declarations(document)
        if dist == row["vendored_distribution"] and component == row["component"]
    ]
    bindings = row.get("bundled_modules", [])
    if (
        not roots
        or any(
            not isinstance(pattern, str)
            or not any(
                pattern == root
                or (
                    pattern.startswith(root + ".")
                    and re.fullmatch(r"[A-Za-z0-9_.*]+", pattern) is not None
                )
                for root in roots
            )
            for pattern in bindings
        )
        or len(set(bindings)) != len(bindings)
    ):
        raise ValueError("notices: vendored module glob outside its declared path")
    return tuple(bindings)


def _check_vendored_version(
    record: NativeLicence,
    installed: dict[str, importlib.metadata.Distribution],
    versions: dict[str, set[str]],
    runtime: dict[str, _AuditRow],
) -> None:
    distribution = record.vendored_distribution
    dist = installed.get(distribution)
    if (
        dist is None
        or distribution not in runtime
        or dist.version != record.vendored_distribution_version
        or versions.get(distribution) != {dist.version}
        or runtime[distribution].version != dist.version
    ):
        raise ValueError(f"notices: vendored distribution version differs: {distribution}")
    if (
        record.provenance_kind == "git-tree"
        and not record.source_path
        and any(
            source == record.upstream_repository
            or source.startswith(record.upstream_repository + "/")
            for source in runtime[distribution].sources
        )
    ):
        raise ValueError("notices: vendored in-tree provenance requires source_path")


def _binding_matches(binding: NativeFile, name: str) -> bool:
    return bool(
        (binding.name and Path(name).name.casefold() == binding.name.casefold())
        or (
            binding.relpath_glob
            and fnmatch.fnmatchcase(name.casefold(), binding.relpath_glob.casefold())
        )
    )


def _vendored_claims(
    entries: list[_Entry],
    records: tuple[NativeLicence, ...],
    declarations: tuple[tuple[str, str, str], ...],
    modules: dict[str, set[str]],
    directories: dict[str, set[str]],
    installed: dict[str, importlib.metadata.Distribution],
    versions: dict[str, set[str]],
    runtime: dict[str, _AuditRow],
) -> dict[str, list[str]]:
    claims: dict[str, list[str]] = defaultdict(list)
    by_name = {record.component: record for record in records}
    for entry in entries:
        if entry.kind == "file" and entry.label.startswith("file:"):
            for distribution, prefix, component in declarations:
                if not entry.name.startswith("_internal/" + prefix.replace(".", "/") + "/"):
                    continue
                record = by_name.get(component)
                if (
                    record is None
                    or record.vendored_distribution != distribution
                    or not any(
                        _binding_matches(binding, entry.name) for binding in record.bundled_files
                    )
                ):
                    raise ValueError(f"notices: vendored path missing licence block: {entry.label}")
                _check_vendored_version(record, installed, versions, runtime)
                # _native_rows verifies the hash/size and assigns this file once.
        if entry.kind != "module":
            continue
        for distribution, prefix, component in declarations:
            if entry.name != prefix and not entry.name.startswith(prefix + "."):
                continue
            record = by_name.get(component)
            if (
                record is None
                or record.vendored_distribution != distribution
                or not any(
                    fnmatch.fnmatchcase(entry.name, pattern) for pattern in record.bundled_modules
                )
            ):
                raise ValueError(f"notices: vendored path missing licence block: {entry.label}")
            owners = modules.get(entry.name, directories.get(entry.name, set()))
            if owners != {distribution}:
                raise ValueError(
                    f"notices: vendored module has unknown/ambiguous RECORD owner: {entry.label}"
                )
            _check_vendored_version(record, installed, versions, runtime)
            claims[component].append(entry.label)
    for record in records:
        if record.vendored_distribution and any(
            entry.kind == "file"
            and entry.label.startswith("file:")
            and any(_binding_matches(binding, entry.name) for binding in record.bundled_files)
            for entry in entries
        ):
            _check_vendored_version(record, installed, versions, runtime)
    return dict(claims)


def _native_file_bindings(
    row: dict[str, Any], claims: dict[str, set[str]]
) -> tuple[NativeFile, ...]:
    if "bundled_files" not in row:
        return ()
    files = row["bundled_files"]
    if not isinstance(files, list) or not files:
        raise ValueError("notices: native bundled_files must be a non-empty list")
    result = []
    for item in files:
        if not isinstance(item, dict) or set(item) - {"version_evidence"} not in (
            {"name", "sha256", "size_bytes"},
            {"relpath_glob", "sha256", "size_bytes"},
        ):
            raise ValueError("notices: native file binding has unknown/missing keys or selectors")
        selector = item.get("name", item.get("relpath_glob"))
        if (
            not isinstance(selector, str)
            or not selector
            or selector != selector.strip()
            or "\\" in selector
            or ":" in selector
            or any(part in {"", ".", ".."} for part in selector.split("/"))
            or ("name" in item and any(char in selector for char in "/?*[]"))
        ):
            raise ValueError("notices: native file binding has unsafe name/relpath_glob")
        sha256 = item["sha256"]
        size = item["size_bytes"]
        if not isinstance(sha256, str) or re.fullmatch(r"[0-9a-f]{64}", sha256) is None:
            raise ValueError("notices: native file binding has invalid sha256")
        if type(size) is not int or size <= 0:
            raise ValueError("notices: native file binding has invalid size_bytes")
        if row["component"] != "OpenSSL" and any(
            token in selector.casefold() for token in ("libcrypto-", "libssl-")
        ):
            raise ValueError("notices: native OpenSSL bindings require the OpenSSL row")
        # Record overlaps; cross-row validation requires explicit co-licensing.
        for key in ("selector:" + selector.casefold(), "hash:" + sha256):
            claims[key].add(row["component"])
        evidence = item.get("version_evidence")
        required = row.get("provenance_kind") == "proprietary-redistributable"
        if (required or evidence is not None) and (
            not isinstance(evidence, dict)
            or set(evidence) != {"method", "value"}
            or evidence.get("method") != "pe_file_version"
            or not isinstance(evidence.get("value"), str)
            or not evidence["value"].strip()
            or evidence["value"] != evidence["value"].strip()
        ):
            raise ValueError("notices: native file version_evidence missing/invalid")
        binding = NativeFile(
            item.get("name", ""),
            item.get("relpath_glob", ""),
            sha256,
            size,
            (evidence["method"], evidence["value"]) if evidence else (),
        )
        if binding in result:
            raise ValueError("notices: native manifest has duplicate file binding")
        result.append(binding)
    return tuple(result)


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
    if sys.platform == "darwin":
        # WP6.5 (G1-F2): the build's ONE macOS link rule; a link is never followed, and an
        # admitted link carries no bytes of its own (its target is inventoried where it is).
        root, contents = tool._macos_layout(executable)
        paths = [path for path, _ in tool._macos_entries(home)]
    else:
        paths = sorted(home.rglob("*"))
    for path in paths:
        if path.is_symlink():
            if sys.platform == "darwin":
                problem = tool.macos_link_problem(root, contents, path)
                if problem is None:
                    continue
                raise ValueError(f"notices: unsafe linked entry {path.name}: {problem}")
            else:
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


def _python_file_names() -> dict[str, str]:
    # Only standard-library extension modules and CPython's own DLLs have PSF
    # coverage here. Being shipped in the interpreter's DLLs folder is not a licence.
    base = Path(sys.base_prefix)
    paths = [
        *base.joinpath("DLLs").glob("*.pyd"),
        base / "python3.dll",
        base / f"python3{sys.version_info.minor}.dll",
    ]
    return {
        path.name.casefold(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
        if path.is_file()
    }


def _is_python_binary(relative: str, stdlib: dict[str, str], path: Path) -> bool:
    if "/" in relative:
        return False
    filename = relative.casefold()
    return filename in stdlib and hashlib.sha256(path.read_bytes()).hexdigest() == stdlib[filename]


def _ffmpeg_rows(
    home: Path,
    lock_path: Path,
    native_licences_path: Path = ROOT / "tools/package/native-licences",
) -> list[NoticeRow]:
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
        _build_tool().validate_ffmpeg_lock(
            json.loads(lock_path.read_text(encoding="utf-8")),
            component_texts_path=native_licences_path / "ffmpeg-components",
        ),
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
        "Parent provider": (
            f"{lock['parent_provider']['repository']} @ {lock['parent_provider']['commit']}"
        ),
        "Release tag": lock["release_tag"],
        "Asset": lock["asset_name"],
        "SHA256": lock["github_sha256"],
        "FFmpeg version": lock["version"],
        "FFmpeg commit": lock["ffmpeg_commit"],
        "FFmpeg ref": lock["ffmpeg_ref"],
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
    parent = lock["parent_provider"]
    notes = (
        f"Provider: {lock['provider']} @ {lock['build_repository_commit']}; "
        f"built from {parent['repository'].split('/')[0]}'s scripts at {parent['commit'][:8]} "
        "with the zvbi stage disabled; "
        f"FFmpeg {lock['ffmpeg_ref']} at {lock['ffmpeg_commit'][:8]} "
        f"(parent repository: {parent['repository']}).",
        *(
            f"{'Build stage' if row['status'] in {'BUILT', 'ENTRY'} else 'Excluded'} "
            f"{row['stage']} ({row['status']}): {row['reason']}"
            for row in lock["excluded"]
        ),
    )
    rows = [
        NoticeRow(
            "FFmpeg / ffprobe",
            lock["version"],
            lock["licence"],
            (f"{lock['ffmpeg_repository']} @ {lock['ffmpeg_commit']}", lock["source_record_url"]),
            entries,
            inputs,
            notes,
        )
    ]
    rows.extend(_ffmpeg_component_rows(lock, entries, native_licences_path))
    rows.extend(_ffmpeg_runtime_rows(lock, entries, native_licences_path))
    return rows


def _ffmpeg_component_rows(
    lock: dict[str, Any], entries: tuple[str, ...], native_licences_path: Path
) -> list[NoticeRow]:
    rows: list[NoticeRow] = []
    for component in lock["components"]:
        sources = [("FFmpeg component: " + component["name"], component)]
        sources.extend(
            (f"FFmpeg component: {component['name']} / repository {index}", extra)
            for index, extra in enumerate(component["extra_repositories"], 2)
        )
        for title, record in sources:
            if not record.get("texts"):
                raise ValueError(f"notices: {title}: missing component texts")
            source = f"{record['repository']} @ {record['pin']}"
            inputs = []
            for text in record["texts"]:
                path = native_licences_path / "ffmpeg-components" / text["path"]
                inputs.append(
                    LicenceInput(
                        path,
                        sha256=text["sha256"],
                        size_bytes=path.stat().st_size,
                        context=title + ": ",
                        provenance=f"{title}; {source}; text {text['path']}",
                        encoding=text.get("encoding", ""),
                    )
                )
            notes = [record["licence_note"]]
            if record.get("chosen"):
                notes.append("licence chosen: " + record["chosen"])
            if record.get("status", "built") != "built":
                notes.append("Source status: " + record["status"])
            if record.get("via"):
                notes.append("Fetched via: " + record["via"])
            rows.append(
                NoticeRow(
                    title,
                    record["pin"],
                    record["licence"],
                    (source,),
                    entries,
                    tuple(inputs),
                    tuple(notes),
                    verdict=(
                        "Redistributed in this artifact"
                        if record.get("status", "built") == "built"
                        else "Source fetched by the build; not compiled into this artifact "
                        "(notice carried by over-inclusion)"
                    ),
                )
            )
    return rows


def _ffmpeg_runtime_rows(
    lock: dict[str, Any], entries: tuple[str, ...], native_licences_path: Path
) -> list[NoticeRow]:
    rows: list[NoticeRow] = []
    toolchain_path = native_licences_path / "ffmpeg-toolchain"
    expected_names = {t["path"] for r in lock["toolchain_runtime"] for t in r["texts"]}
    actual_names = (
        {path.name for path in toolchain_path.iterdir()} if toolchain_path.is_dir() else set()
    )
    if actual_names != expected_names:
        raise ValueError("notices: FFmpeg toolchain runtime text directory differs from lock")
    for runtime in lock["toolchain_runtime"]:
        title = (
            f"FFmpeg toolchain runtime: {runtime['name']} {runtime['version']} "
            f"({runtime['reached_via']})"
        )
        sources = (
            (
                f"{runtime['source_url']} (crate archive sha256 {runtime['pin']})",
                runtime["repository"],
            )
            if runtime["pin_kind"] == "crate-sha256"
            else (f"{runtime['repository']} @ {runtime['pin']}", runtime["source_url"])
        )
        runtime_inputs = []
        for text in runtime["texts"]:
            path = toolchain_path / text["path"]
            context = title + ": "
            if not path.is_file() or path.is_symlink():
                raise ValueError(f"notices: {context}missing/unsafe text {text['path']}")
            data = path.read_bytes()
            if not data or hashlib.sha256(data).hexdigest() != text["sha256"]:
                raise ValueError(f"notices: {context}text hash differs: {text['path']}")
            runtime_inputs.append(
                LicenceInput(
                    path,
                    sha256=text["sha256"],
                    size_bytes=len(data),
                    context=context,
                    provenance=(f"{title}; {'; '.join(sources)}; text {text['path']}"),
                )
            )
        runtime_notes = [runtime["licence_note"]] if runtime["licence_note"] else []
        if runtime["chosen"]:
            runtime_notes.append("licence chosen: " + runtime["chosen"])
        if runtime["licence"] == "MPL-2.0":
            runtime_notes.append("MPL-2.0 (secondary licence: GPL-3.0 permitted, section 3.3)")
        runtime_notes.extend(
            (
                (
                    "carried as a superset of the static link; linkage not proven"
                    if runtime["linkage"] == "superset"
                    else "statically linked into ffmpeg.exe / ffprobe.exe by the fork build at "
                    + lock["build_repository_commit"]
                ),
                f"Census basis: {runtime['basis']}; {runtime['basis_note']}",
                "Source evidence: " + runtime["evidence"],
            )
        )
        rows.append(
            NoticeRow(
                title,
                runtime["version"],
                runtime["licence"],
                sources,
                entries,
                tuple(runtime_inputs),
                tuple(runtime_notes),
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
    native_licences_path: Path = ROOT / "tools/package/native-licences",
    distribution: Callable[[str], importlib.metadata.Distribution] | None = None,
) -> NoticePlan:
    """Inventory an onedir folder and select only the rows supported by its contents.

    Pure modules match wheel RECORD paths; namespace modules match unique,
    exact RECORD directory prefixes. Declared vendored paths need their own
    version-bound licence blocks. Native/data entries must match a RECORD path
    or a flattened, SHA-256-verified native basename.
    Independently licensed natives need their own exact-byte manifest row.
    Declared embedded hosts require their measured identity and every embedded
    source/text row before interpreter or RECORD ownership is considered. Their
    parent must still cover the host, with explicit component attributions.
    Only stdlib extensions and CPython DLLs use the PSF fallback. Artifact code and bundled
    runtime packages are not imported; no external process is started.

    Args:
        folder: The release folder or its executable's immediate folder.
        audit_path: The source-install audit's runtime table and audited texts.
        uv_lock_path: The build's locked distribution versions.
        ffmpeg_lock_path: The FFmpeg identity and verified source/licence rows.
        native_licences_path: The committed seat-verified native licence inputs.
        distribution: Explicit fixture resolver; None uses unique build-venv metadata.

    Returns:
        Validated coverage rows and explicitly user-obtained component statements.

    Raises:
        ValueError: An entry is unknown, a version/material is missing, or a
            bundled FFmpeg repository is GPL-3.0-incompatible.
        OSError: Required files cannot be read.
    """
    _build_tool().check_build_environment()
    entries, home = _inventory(folder)
    ffmpeg = _ffmpeg_rows(home, ffmpeg_lock_path, native_licences_path)
    audit = _audit_rows(audit_path)
    versions = _locked_versions(uv_lock_path)
    if distribution is None:
        trusted = cast(
            dict[str, importlib.metadata.Distribution],
            _build_tool().trusted_distributions(versions),
        )
        distribution = trusted.__getitem__
    # Read declarations independently: a removed row/text must not let parent
    # RECORD/interpreter ownership absorb a carried host's embedded terms.
    document = _native_document(native_licences_path)
    embedded_hosts = _embedded_declarations(document)
    embedded_claims, carried_hosts = _embedded_claims(entries, home, embedded_hosts, document)
    native_records = load_native_licences(native_licences_path)
    declarations = _vendored_declarations(document)
    runtime = {
        key: row
        for key, row in audit.items()
        if key not in GPU_NAMES
        and not key.startswith("nvidia-")
        and key not in {"python", _normalize("FFmpeg / ffprobe")}
    }
    installed: dict[str, importlib.metadata.Distribution] = {}
    paths: dict[str, set[str]] = defaultdict(set)
    basenames: dict[str, list[tuple[str, str]]] = defaultdict(list)
    modules: dict[str, set[str]] = defaultdict(set)
    directories: dict[str, set[str]] = defaultdict(set)
    for name in (*runtime, "pyinstaller", "pyinstaller-hooks-contrib"):
        try:
            dist = distribution(name)
        except (importlib.metadata.PackageNotFoundError, KeyError):
            continue
        installed[name] = dist
        for path in dist.files or ():
            relative = str(path).replace("\\", "/")
            paths[relative.casefold()].add(name)
            parts = relative.split("/")
            for length in range(1, len(parts)):
                if all(part.isidentifier() for part in parts[:length]):
                    directories[".".join(parts[:length])].add(name)
            if Path(relative).suffix.lower() in {".dll", ".pyd", ".so", ".dylib"}:
                record_hash = path.hash
                sha256 = record_hash.value if record_hash and record_hash.mode == "sha256" else ""
                basenames[Path(relative).name.casefold()].append((name, sha256))
            if module := _module_name(relative):
                modules[module].add(name)
                if name in {"pyinstaller", "pyinstaller-hooks-contrib"} and (
                    (
                        parts[:-1] == ["PyInstaller", "loader"]
                        and Path(relative).stem.startswith(("pyimod", "pyiboot"))
                    )
                    or (
                        len(parts) >= 2
                        and parts[-2] == "rthooks"
                        and Path(relative).stem.startswith("pyi_rth_")
                    )
                ):
                    modules[Path(relative).stem].add(name)
                if (
                    name == "pyinstaller"
                    and relative.startswith("PyInstaller/fake-modules/")
                    and (
                        runtime_module := _module_name(
                            relative.removeprefix("PyInstaller/fake-modules/")
                        )
                    )
                ):
                    modules[runtime_module].add(name)
    module_claims = _vendored_claims(
        entries, native_records, declarations, modules, directories, installed, versions, runtime
    )
    native_rows = _native_rows(entries, home, native_records, module_claims, embedded_claims)
    native_labels = {label for row in native_rows for label in row.entries} - carried_hosts.keys()
    selected: dict[str, list[str]] = defaultdict(list)
    ffmpeg_labels = {entry for row in ffmpeg for entry in row.entries}
    python_names = _python_file_names()
    unknown: list[str] = []
    for entry in entries:
        if entry.label in ffmpeg_labels or entry.label in native_labels:
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
            owners = modules.get(name, directories.get(name, set()))
        else:
            relative = name.removeprefix("_internal/")
            filename = Path(relative).name.casefold()
            if any(
                fnmatch.fnmatchcase(filename, pattern) for pattern in THIRD_PARTY_NATIVE_PATTERNS
            ):
                component = "OpenSSL " if filename.startswith(("libcrypto-", "libssl-")) else ""
                unknown.append(f"{component}missing native licence row/material: {entry.label}")
                continue
            owners = paths.get(relative.casefold(), set())
            if not owners and name.startswith("_internal/") and "/" not in relative:
                candidates = basenames.get(filename, [])
                if candidates:
                    digest = (
                        base64.urlsafe_b64encode(
                            hashlib.sha256((home / name).read_bytes()).digest()
                        )
                        .decode("ascii")
                        .rstrip("=")
                    )
                    owners = {owner for owner, sha256 in candidates if sha256 == digest}
            if (
                not owners
                and name.startswith("_internal/")
                and _is_python_binary(relative, python_names, home / name)
            ):
                selected["python"].append(entry.label)
                continue
        if len(owners) != 1:
            unknown.append(f"unknown or ambiguous bundled entry {entry.label}")
            continue
        owner = next(iter(owners))
        if owner in {"pyinstaller", "pyinstaller-hooks-contrib"} and (
            name.startswith("pyi_rth_") or name.startswith("_pyi_rth_utils")
        ):
            owner += "-runtime"
        selected[owner].append(entry.label)
    _check_embedded_parents(
        embedded_hosts, carried_hosts, selected, installed, set(runtime) & set(versions)
    )
    if unknown:
        raise ValueError("notices: " + "; ".join(unknown))
    result: list[NoticeRow] = [*ffmpeg, *native_rows]
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
    result.extend(_carried_notice_rows(document, embedded_claims, result))
    for label, host in carried_hosts.items():
        parents = [
            row for row in result if _normalize(row.name) == host.parent and label in row.entries
        ]
        if len(parents) != 1:
            raise ValueError(
                f"notices: embedded {host.relpath} missing/ambiguous "
                f"parent attribution: {host.parent}"
            )
    result = [
        row._replace(
            notes=(
                *row.notes,
                *(
                    f"Embedded components in {host.relpath} "
                    "(source pins and texts in component rows): "
                    + ", ".join(name for name, _pin in host.components)
                    for label, host in sorted(carried_hosts.items())
                    if _normalize(row.name) == host.parent and label in row.entries
                ),
            )
        )
        for row in result
    ]
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
    # Select only hosts that passed the existing census preflight. Declarations
    # alone do not assert redistribution, just as for embedded component rows.
    carried_paths = {
        host.relpath: label.removeprefix("file:") for label, host in carried_hosts.items()
    }
    limits = tuple(
        limit._replace(
            hosts=tuple(
                sorted(carried_paths[path] for path in limit.hosts if path in carried_paths)
            )
        )
        for limit in _limit_declarations(document, embedded_hosts)
        if any(path in carried_paths for path in limit.hosts)
    )
    return NoticePlan(inventory_labels, ordered, tuple(statements), limits)


def _carried_notice_rows(
    document: dict[str, Any],
    claims: dict[str, list[tuple[str, str]]],
    rows: list[NoticeRow],
) -> list[NoticeRow]:
    result = []
    # Resolve only against original, actually carried rows; references cannot
    # chain or use an absent distribution as a source of redistribution terms.
    for record in document["components"]:
        if "carried_notice" not in record or not claims.get(record["component"]):
            continue
        reference = _carried_notice(record)
        context = (
            f"embedded {', '.join(record['embedded_in'])} "
            f"component {record['component']} carried notice: "
        )
        candidates = [row for row in rows if row.name == reference["row"]]
        if len(candidates) != 1:
            raise ValueError(f"notices: {context}missing/ambiguous source row {reference['row']}")
        source = candidates[0]
        inputs = []
        for expected in reference["inputs"]:
            matches = []
            for item in source.licence_inputs:
                try:
                    data = (
                        _audited_material(item)[1]
                        if item.block_id
                        else _licence_bytes(item)
                        if item.sha256
                        else item.path.read_bytes()
                    )
                except (ValueError, OSError) as error:
                    raise ValueError(f"notices: {context}{error}") from error
                if (hashlib.sha256(data).hexdigest(), len(data)) == (
                    expected["sha256"],
                    expected["size_bytes"],
                ):
                    matches.append(item)
            if len(matches) != 1:
                raise ValueError(
                    f"notices: {context}missing/ambiguous input identity in {source.name}"
                )
            inputs.append(
                matches[0]._replace(
                    reference=True,
                    sha256=expected["sha256"],
                    size_bytes=expected["size_bytes"],
                    context=context,
                    provenance=(
                        matches[0].provenance
                        or f"Reused carried notice: {source.name}; " + _wheel_label(matches[0].path)
                    )
                    if not matches[0].block_id
                    else matches[0].provenance,
                )
            )
        result.append(
            NoticeRow(
                record["component"],
                record["upstream_version"],
                record["spdx"],
                source.sources,
                tuple(sorted(label for label, _digest in claims[record["component"]])),
                tuple(inputs),
                (
                    f"Reused carried notice: {source.name}; exact input SHA-256 and size "
                    "checked; original provenance retained.",
                    "Version evidence: " + record["version_evidence"]["value"],
                ),
            )
        )
    return result


def _native_rows(
    entries: list[_Entry],
    home: Path,
    records: tuple[NativeLicence, ...],
    module_claims: dict[str, list[str]] | None = None,
    embedded_claims: dict[str, list[tuple[str, str]]] | None = None,
) -> list[NoticeRow]:
    selected: dict[str, list[tuple[str, str]]] = defaultdict(list)
    errors: list[str] = []
    by_name = {record.component: record for record in records}
    for component, labels in (module_claims or {}).items():
        selected[component].extend((label, "") for label in labels)
    for component, identities in (embedded_claims or {}).items():
        selected[component].extend(identities)
    for entry in entries:
        if entry.kind != "file" or not entry.label.startswith("file:"):
            continue
        matches = [
            (record, binding)
            for record in records
            for binding in record.bundled_files
            if _binding_matches(binding, entry.name)
        ]
        if not matches:
            continue
        if Path(entry.name).name.casefold().startswith(("libcrypto-", "libssl-")) and any(
            record.component != "OpenSSL" for record, _binding in matches
        ):
            errors.append(f"OpenSSL native binding claimed by another component: {entry.label}")
            continue
        data = (home / entry.name).read_bytes()
        sha256 = hashlib.sha256(data).hexdigest()
        if any(
            len(data) != binding.size_bytes or sha256 != binding.sha256
            for _record, binding in matches
        ):
            errors.append(f"native file identity hash/size differs: {entry.label}")
            continue
        owners = {record.component for record, _binding in matches}
        if any(owners != {owner, *by_name[owner].co_licensed_with} for owner in owners):
            errors.append(
                f"native file has incomplete/duplicate co-licensed component claims: {entry.label}"
            )
            continue
        for owner in owners:
            selected[owner].append((entry.label, sha256))
    if errors:
        raise ValueError("notices: " + "; ".join(errors))
    result = []
    for record in records:
        matched = sorted(selected.get(record.component, []))
        if not matched:
            continue
        if record.component == "OpenSSL":
            _check_openssl_version(record)
        if record.provenance_kind == "proprietary-redistributable":
            _check_proprietary_source(record)
        notes = [
            (
                "Redistributed embedded component; exact host identities "
                "and source pin bind these terms."
                if record.embedded_in
                else (
                    "The Windows download redistributes the interpreter's native libraries; "
                    "the 1.0.0 source install did not."
                )
                if record.bundled_version_source
                else "Redistributed vendored component; inventory below binds the source pin. "
                if record.vendored_distribution
                else "Redistributed native component; exact file identities below bind "
                "the recorded upstream version."
            ),
            "Version evidence: " + ": ".join(record.version_evidence),
        ]
        if record.embedded_in:
            notes.append("Embedded text provenance: " + record.licence_input.provenance)
        if record.provenance_kind == "proprietary-redistributable":
            notes.append(
                "Proprietary redistributable; URLs identify licence and redistribution "
                "terms, not corresponding source."
            )
        if record.source_archive_sha256:
            notes.append("Published source archive SHA-256: " + record.source_archive_sha256)
        if record.co_licensed_with:
            notes.append(
                "Co-licensed with (all rows required): " + ", ".join(record.co_licensed_with)
            )
        if record.bundled_version_source:
            notes.append(
                "Build input: python-build-standalone "
                + record.interpreter_release
                + "; CPython "
                + record.python_version
                + "; version source: "
                + record.bundled_version_source
            )
        notes.extend(
            f"Bundled file {label}; SHA-256: {sha256}" for label, sha256 in matched if sha256
        )
        notes.extend(
            f"File version evidence: {binding.relpath_glob or binding.name}; "
            + ": ".join(binding.version_evidence)
            for binding in record.bundled_files
            if binding.version_evidence
        )
        result.append(
            NoticeRow(
                record.component,
                record.upstream_version,
                record.spdx,
                record.source_urls,
                tuple(label for label, _sha256 in matched),
                (record.licence_input, record.attribution_input)
                if record.attribution_input is not None
                else (record.licence_input,),
                tuple(notes),
            )
        )
    return result


def _check_proprietary_source(record: NativeLicence) -> None:
    source = record.text_source
    if source is None:
        raise ValueError("notices: proprietary text source missing")
    try:
        data = _native_text(source.path, source.sha256, source.size_bytes)
    except ValueError as error:
        raise ValueError(
            "notices: proprietary text source differs from build interpreter"
        ) from error
    first, last = record.text_source_lines
    excerpt = b"".join(_lf_lines(data)[first - 1 : last])
    if excerpt != record.licence_input.path.read_bytes():
        raise ValueError("notices: proprietary excerpt differs from build interpreter text source")


def _check_openssl_version(record: NativeLicence) -> None:
    if record.bundled_version_source != "ssl.OPENSSL_VERSION":
        raise ValueError("notices: OpenSSL missing ssl.OPENSSL_VERSION binding")
    if record.version_evidence != ("ssl.OPENSSL_VERSION", ssl.OPENSSL_VERSION):
        raise ValueError("notices: OpenSSL version_evidence differs from build interpreter")
    reading = re.match(r"^OpenSSL ([0-9]+\.[0-9]+\.[0-9]+[a-z]?)(?:\s|$)", ssl.OPENSSL_VERSION)
    if reading is None or reading[1] != record.upstream_version:
        raise ValueError("notices: OpenSSL bundled version differs from native licence manifest")
    if ".".join(map(str, sys.version_info[:3])) != record.python_version:
        raise ValueError(
            "notices: OpenSSL interpreter version differs from native licence manifest"
        )
    build_marker = Path(sys.base_prefix) / "BUILD"
    if (
        not build_marker.is_file()
        or build_marker.read_text(encoding="utf-8").strip() != record.interpreter_release
    ):
        raise ValueError(
            "notices: OpenSSL interpreter build release differs from native licence manifest"
        )


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
    """Render coverage, provenance and byte-checked licence texts deterministically.

    Installed wheel files retain even their embedded GPL texts unchanged. All
    FFmpeg stage/runtime rows carry their own texts; the aggregate row carries
    the dedicated FFmpeg licence block. Declared stage encodings are losslessly
    transcoded to UTF-8 with the original encoding and hash directly under the
    heading. Audited upstream blocks are UTF-8/LF copies checked against both
    recorded integrity fields before use.
    Embedded rows share one block per distinct text hash/size, but each input is
    rechecked before sharing and each row retains its own source attribution.
    Carried limits follow the component details in component/host order, with
    statements preserved verbatim. Empty limits add no output bytes.

    Args:
        plan: An inventory-backed component plan from :func:`plan_notices`.

    Returns:
        The complete Markdown document with declared stage encodings transcoded
        to UTF-8 and other input bytes unchanged.

    Raises:
        ValueError: Coverage/materials are missing, commercial Qt terms are
            requested, an audited upstream block fails integrity checks, or the
            complete document is not strict UTF-8 (with byte offset and source).
        OSError: A licence input cannot be read.
    """
    validate_coverage(plan.entries, plan.rows)
    rows = sorted(plan.rows, key=lambda row: row.name.casefold())
    ffmpeg = any(row.name == "FFmpeg / ffprobe" for row in rows)
    header = [
        "# Clearwater artifact third-party notices",
        "",
        "Clearwater is GPL-2.0-or-later. Copyright and licence terms for each",
        "redistributed component are preserved below. Source links identify exact",
        "releases and commits; FFmpeg build recipes identify linked repositories and pins.",
        "Proprietary redistributables carry licence/redistribution terms, with no source claim.",
        "Preserve these notices on redistribution.",
    ]
    if ffmpeg:
        header += [
            "The artifact is a combined work distributed under GPL-3.0 terms where",
            "FFmpeg requires them; Clearwater's or-later grant permits this combination.",
        ]
    if any(row.name.startswith(("FFmpeg component:", "FFmpeg toolchain runtime:")) for row in rows):
        header += [
            "FFmpeg build-component and toolchain-runtime texts are labelled with "
            "a representative file name from the census; byte-identical texts are "
            "shared across components, so a label may name another component's copy "
            "of the same text."
        ]
    header += [
        "",
        *plan.user_obtained,
        "",
        "## Redistributed components",
        "",
        f"Inventory: {len(plan.entries)} entries; {len(rows)} component rows.",
        "",
        "| Component | Version | Licence | Verdict | Corresponding source / terms | Texts |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    materials: dict[LicenceInput, tuple[str, bytes]] = {}
    references: dict[LicenceInput, str] = {}
    embedded_texts: dict[tuple[str, int], LicenceInput] = {}
    for row in rows:
        if not row.licence_inputs:
            raise ValueError(f"notices: {row.name} missing licence material")
        for item in sorted(row.licence_inputs, key=_licence_order):
            if item in materials:
                continue
            if item.path.name.casefold() == "licenseref-qt-commercial.txt":
                raise ValueError("notices: commercial Qt licence must never be reproduced")
            if item.block_id:
                try:
                    source, data = _audited_material(item)
                except (ValueError, OSError) as error:
                    if item.context:
                        raise ValueError(f"notices: {item.context}{error}") from error
                    raise
                label = f"{row.name} {row.version}; {source}; the 1.0.0 audit's upstream copy"
            elif item.provenance:
                data = _licence_bytes(item)
                label = item.provenance
            else:
                data = _licence_bytes(item) if item.context else item.path.read_bytes()
                if row.name == "Clearwater":
                    data = data.replace(b"\r\n", b"\n")
                label = f"Installed wheel: {row.name} {row.version}; {_wheel_label(item.path)}"
                if item.path.name == "ffmpeg-LICENSE.txt":
                    label = f"Bundled FFmpeg: {row.version}; ffmpeg-LICENSE.txt"
                elif row.name in {"Clearwater", "Python"}:
                    label = f"Build source: {row.name} {row.version}; {item.path.name}"
            if not data:
                raise ValueError(f"notices: {row.name} missing licence material")
            identity = (hashlib.sha256(data).hexdigest(), len(data))
            if item.context and identity != (item.sha256, item.size_bytes):
                raise ValueError(f"notices: {item.context}text identity differs")
            previous = embedded_texts.get(identity)
            if previous is not None and (item.context or previous.context):
                if previous.reference and not item.reference:
                    # Keep the existing anchor/order but restore the original
                    # wheel/audit label when a reference sorted before it.
                    materials[previous] = (label, data)
                    embedded_texts[identity] = item
                references[item] = references[previous]
                continue
            embedded_texts[identity] = item
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
    if plan.limits:
        header += ["## Components with no carried licence text, and limits", ""]
        for limit in sorted(plan.limits):
            header += [
                "Component: " + limit.component,
                "Hosts: " + ", ".join("file:" + host for host in sorted(limit.hosts)),
                limit.statement,
                "",
            ]
    header += ["## Full licence texts and provenance", ""]
    output = ["\n".join(header).encode("utf-8")]
    offset = len(output[0])
    emitted_blocks: list[tuple[int, int, str]] = []
    for item, (label, data) in materials.items():
        heading = "### " + label
        if item.encoding:
            heading += (
                f"\ntranscoded from {item.encoding}; original file sha256 "
                + hashlib.sha256(data).hexdigest()
            )
        if item.path.name == "ffmpeg-LICENSE.txt" and not item.block_id:
            heading = "### Bundled FFmpeg GPL-3.0"
        # A fence longer than any backtick run keeps copied Markdown licence files intact.
        longest = max((len(run) for run in re.findall(rb"`+", data)), default=0)
        fence = b"`" * max(4, longest + 1)
        hash_label = "Original SHA-256" if item.encoding else "SHA-256"
        size_label = "Original bytes" if item.encoding else "Bytes"
        prefix = (
            f'\n<a id="{references[item]}"></a>\n\n{heading}\n\n'
            f"Source: {label}. {hash_label}: `{hashlib.sha256(data).hexdigest()}`. "
            f"{size_label}: {len(data)}.\n\n"
        ).encode()
        block = [
            prefix,
            fence + b"text\n",
            data.decode(item.encoding).encode("utf-8") if item.encoding else data,
            b"" if data.endswith(b"\n") else b"\n",
            fence + b"\n",
        ]
        output += block
        end = offset + sum(map(len, block))
        emitted_blocks.append((offset, end, f"{label}; file {item.path.name}"))
        offset = end
    rendered = b"".join(output)
    try:
        rendered.decode("utf-8")
    except UnicodeDecodeError as error:
        source = next(
            (label for start, end, label in emitted_blocks if start <= error.start < end),
            "document header",
        )
        raise ValueError(
            f"notices: rendered document is not strict UTF-8 at byte offset {error.start}; "
            f"source: {source}"
        ) from error
    return rendered


def write_notices(
    folder: Path,
    *,
    audit_path: Path = ROOT / "THIRD_PARTY_NOTICES.md",
    uv_lock_path: Path = ROOT / "uv.lock",
    ffmpeg_lock_path: Path = ROOT / "tools/package/ffmpeg.lock.json",
    native_licences_path: Path = ROOT / "tools/package/native-licences",
    distribution: Callable[[str], importlib.metadata.Distribution] | None = None,
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
        native_licences_path: The committed seat-verified native licence inputs.
        distribution: Explicit fixture resolver; None uses unique build-venv metadata.

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
                native_licences_path=native_licences_path,
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


def render_root_annex(
    *,
    audit_path: Path = ROOT / "THIRD_PARTY_NOTICES.md",
    ffmpeg_lock_path: Path = ROOT / "tools/package/ffmpeg.lock.json",
    native_licences_path: Path = ROOT / "tools/package/native-licences",
) -> bytes:
    """Regenerate stage/runtime annexes using the artifact's checked row renderer.

    The root links exact upstream bytes; artifacts transcode declared encodings.
    Existing root audit material is preserved with LF line endings and an annex pointer
    added to the aggregate FFmpeg row. No binary or product code is executed.

    Args:
        audit_path: Root audit document whose generated annex is replaced.
        ffmpeg_lock_path: Source and runtime census lock.
        native_licences_path: Surface containing the locked runtime texts.

    Returns:
        The complete root document with a deterministic, LF-encoded annex.

    Raises:
        ValueError: A lock, runtime text, aggregate row or annex marker is invalid.
        OSError: An input cannot be read.
    """
    lock = cast(
        dict[str, Any],
        _build_tool().validate_ffmpeg_lock(
            json.loads(ffmpeg_lock_path.read_text(encoding="utf-8")),
            component_texts_path=native_licences_path / "ffmpeg-components",
        ),
    )
    entries = (
        "file:ffmpeg.exe",
        "file:ffprobe.exe",
        "file:ffmpeg-BUILD.txt",
        "file:ffmpeg-LICENSE.txt",
    )
    rows = tuple(
        _ffmpeg_component_rows(lock, entries, native_licences_path)
        + _ffmpeg_runtime_rows(lock, entries, native_licences_path)
    )
    rendered = render_notices(NoticePlan(entries, rows, ()))
    suffix = rendered.split(b"## Redistributed components\n", 1)[1]
    # Four synthetic inventory labels support the shared renderer, but are not
    # a root-source installation inventory and must not be printed as one.
    suffix = re.sub(rb"\nInventory: [^\n]*\n", b"", suffix, count=1)
    # Runtime aliases win shared hashes, retaining the existing runtime links.
    by_hash = {
        item.sha256: item.path.relative_to(native_licences_path).as_posix()
        for row in rows
        for item in row.licence_inputs
    }
    anchors = {
        anchor.decode(): by_hash[digest.decode()]
        for anchor, digest in re.findall(
            rb'<a id="(licence-\d+)"></a>.*?SHA-256: `([a-f0-9]{64})`', rendered, re.S
        )
    }
    suffix = suffix.split(b"## Full licence texts and provenance", 1)[0]
    for anchor, name in anchors.items():
        suffix = suffix.replace(
            f"(#{anchor})".encode(),
            f"(tools/package/native-licences/{name})".encode(),
        )
    suffix += (
        b"## Stage and runtime licence text files\n\n"
        b"These links preserve exact upstream bytes independently of "
        b"Markdown checkout line endings.\n\n"
    )
    for digest, name in sorted(by_hash.items()):
        path = native_licences_path / name
        suffix += (
            f"- [{Path(name).name}](tools/package/native-licences/{name}); "
            f"SHA-256: `{digest}`; bytes: {path.stat().st_size}.\n"
        ).encode()
    marker = b"<!-- WP6.3c generated FFmpeg toolchain runtime census -->"
    original = audit_path.read_bytes().replace(b"\r\n", b"\n")
    if original.count(marker) != 1:
        raise ValueError("notices: root annex marker must occur once")
    prefix = original.split(marker, 1)[0].rstrip()
    old_pointer = b"[Toolchain-runtime annex](#ffmpeg-toolchain-runtime-census)"
    pointer = (
        b"[Build-component and toolchain-runtime annex]"
        b"(#ffmpeg-build-components-and-toolchain-runtime-census)"
    )
    lines = prefix.splitlines()
    indices = [i for i, line in enumerate(lines) if line.startswith(b"| FFmpeg / ffprobe |")]
    if len(indices) != 1:
        raise ValueError("notices: root FFmpeg row must occur once")
    index = indices[0]
    lines[index] = lines[index].replace(old_pointer, pointer)
    if pointer not in lines[index]:
        lines[index] = lines[index].rstrip(b" |") + b"; " + pointer + b" |"
    header = (
        b"\n\n## FFmpeg build components and toolchain runtime census\n\n"
        b"This section applies to the FFmpeg bundled in the Windows download, "
        b"not to user-obtained tools.\n"
        b"Rows and links to licence texts are generated by "
        b"`python tools/package/notices.py --root-annex --write`\n"
        b"using the artifact notices renderer and `tools/package/ffmpeg.lock.json` "
        b"and include every stage source record carrying texts.\n"
        b"Over-inclusion is permitted: reached_via: toolchain rows retained "
        b"with both Rust stages disabled produce extra notices.\n"
        b"Shared texts use a representative file name from the census; "
        b"byte-identical texts are shared across components.\n"
    )
    return b"\n".join(lines) + b"\n\n" + marker + header + suffix


def main(argv: Sequence[str] | None = None) -> int:
    """Generate artifact notices or write/check the root annex without execution.

    ``--root-annex`` defaults to checking; ``--write`` regenerates the root
    document. The artifact mode requires a folder and writes its notices file.

    Args:
        argv: Arguments, or ``sys.argv[1:]`` when omitted.

    Returns:
        Zero after writing/checking, or one with an ASCII-safe failure line.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("folder", type=Path, nargs="?")
    parser.add_argument(
        "--root-annex",
        action="store_true",
        help="regenerate/check the root runtime annex (default: check)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--audit", type=Path, default=ROOT / "THIRD_PARTY_NOTICES.md")
    parser.add_argument("--uv-lock", type=Path, default=ROOT / "uv.lock")
    parser.add_argument("--ffmpeg-lock", type=Path, default=ROOT / "tools/package/ffmpeg.lock.json")
    options = parser.parse_args(argv)
    if options.root_annex and options.folder is not None:
        parser.error("--root-annex does not accept an artifact folder")
    if not options.root_annex and (options.folder is None or options.write or options.check):
        parser.error("artifact notices requires a folder; --write/--check require --root-annex")
    try:
        if options.root_annex:
            document = render_root_annex(
                audit_path=options.audit, ffmpeg_lock_path=options.ffmpeg_lock
            )
            if options.write:
                options.audit.write_bytes(document)
            elif options.audit.read_bytes().replace(b"\r\n", b"\n") != document:
                raise ValueError("root annex differs; run --root-annex --write")
            print("root annex written" if options.write else "root annex matches")
            return 0
        path = write_notices(
            options.folder,
            audit_path=options.audit,
            uv_lock_path=options.uv_lock,
            ffmpeg_lock_path=options.ffmpeg_lock,
        )
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        message = " ".join(str(error).split()).encode("ascii", "backslashreplace").decode("ascii")
        print(f"FAILED: artifact notices: {message}", file=sys.stderr)
        return 1
    print(f"wrote {path}".encode("ascii", "backslashreplace").decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
