"""The fixture manifest: schema, builders and validator (WP2.3 item 5).

``manifest.json`` names every sample, what it is meant to exercise, and the facts measured when
it was generated. The fault vocabulary is WP2.2's (``clearwater.interfaces.video.Fault``): a
sample may only expect a fault kind and severity that module defines, and
:func:`validate` says so by name when it does not.

Top level::

    {"schema": 1, "limits": {"max_file_bytes": ..., "max_total_bytes": ...},
     "samples": [<entry>, ...], "omitted": [{"what": ..., "reason": ...}, ...]}

One ``<entry>`` (every key is required)::

    id               unique, lower-case words joined by hyphens
    group            one of GROUPS
    kind             the file kind, for example "png", "jpeg", "mp4", "dng", "placeholder"
    storage          "committed" (a file under tests/fixtures) or "generated" (made on demand)
    path             relative to tests/fixtures (committed) or to the generated root (generated)
    command          null for committed; the exact regeneration command for generated
    serves           the spec clauses and V-tests the sample serves
    exercises        one sentence: what a test uses it for
    expect           {"faults": [{"kind", "severity"}, ...],   WP2.2 Fault names
                      "refusal": null | {"clause", "by"},       photo refusals (no Fault kind)
                      "photo": null | {"metadata": {PhotoMetadata fields},
                                       "image": {"orientation_applied", "color": {ColorDescription
                                       fields}}},
                      "probe": null | {ProbeResult fields: "container", "audio": [{AudioStreamInfo
                                       fields}], "data", "video": {VideoStreamInfo fields, "color":
                                       {ColorDescription fields}}}}
                     Every key under "photo" and "probe" is a field name of the WP2.2 dataclass it
                     describes; :func:`validate` refuses any other. Where a field holds bytes
                     (``icc_profile``, ``exif``) the manifest names the profile ("srgb",
                     "display-p3") or says "present"; a fraction is written "numerator/denominator".
    facts            what was measured from the written file (ffprobe, Pillow, bytes)
    size             bytes of the file as generated
    md5              hex digest when byte-reproducible, else null
    byte_reproducible  whether regeneration gives the same bytes in the declared envelope
"""

from __future__ import annotations

import dataclasses
import hashlib
import re
import typing
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

from clearwater.interfaces.image import ColorDescription, Image
from clearwater.interfaces.photo import PhotoMetadata
from clearwater.interfaces.video import (
    AudioStreamInfo,
    Fault,
    FaultKind,
    ProbeResult,
    VideoStreamInfo,
)

SCHEMA = 1
"""The manifest schema version."""

MAX_FILE_BYTES = 2_000_000
"""No committed file may be larger (ruling 4: 2 MB, taken as decimal megabytes)."""

MAX_TOTAL_BYTES = 10_000_000
"""The committed fixtures folder must stay under this total (ruling 4: 10 MB)."""

GROUPS = ("stills", "flicker", "video", "files")
"""The sample groups, one generator module each."""

STORAGES = ("committed", "generated")
"""Where a sample lives: in the repository, or made on demand into the working folder."""

ID_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
"""What a sample id looks like."""

ENTRY_KEYS = (
    "id",
    "group",
    "kind",
    "storage",
    "path",
    "command",
    "serves",
    "exercises",
    "expect",
    "facts",
    "size",
    "md5",
    "byte_reproducible",
)
"""The keys every entry carries."""

EXPECT_KEYS = ("faults", "refusal", "photo", "probe")
"""The keys of an entry's ``expect`` block."""

type Entry = dict[str, Any]
"""One manifest entry (see the module docstring)."""


def fault_kinds() -> tuple[str, ...]:
    """Return the fault kinds ``clearwater.interfaces`` defines (IF-5 ``FaultKind``)."""
    return tuple(typing.get_args(FaultKind.__value__))


def fault_severities() -> tuple[str, ...]:
    """Return the fault severities ``clearwater.interfaces`` defines (IF-5 ``Fault``)."""
    return tuple(typing.get_args(typing.get_type_hints(Fault)["severity"]))


def md5_of(path: Path) -> str:
    """Return the MD5 hex digest of a file.

    Args:
        path: The file.

    Returns:
        The digest. MD5 is an identity check here, not a security control.
    """
    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def fault(kind: str, severity: str) -> dict[str, str]:
    """Return one expected fault in the manifest's form.

    Args:
        kind: A ``FaultKind`` name.
        severity: ``"refuse"``, ``"warn"`` or ``"exclude"``.

    Returns:
        ``{"kind": ..., "severity": ...}``.
    """
    return {"kind": kind, "severity": severity}


def expect(
    *,
    faults: Sequence[Mapping[str, str]] = (),
    refusal: Mapping[str, str] | None = None,
    photo: Mapping[str, Any] | None = None,
    probe: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return an entry's ``expect`` block.

    Args:
        faults: The probe faults the sample should produce (WP2.2 names).
        refusal: For a photo refused outright (no ``Fault`` kind exists for photos): the
            decision clause and how it is recognised.
        photo: The ``PhotoMetadata`` facts a reader should report.
        probe: The ``VideoStreamInfo`` / ``ProbeResult`` facts a probe should report.

    Returns:
        The block, with every key present.
    """
    return {
        "faults": [dict(item) for item in faults],
        "refusal": dict(refusal) if refusal is not None else None,
        "photo": dict(photo) if photo is not None else None,
        "probe": dict(probe) if probe is not None else None,
    }


def entry(
    *,
    sample_id: str,
    group: str,
    kind: str,
    storage: str,
    path: str,
    serves: Sequence[str],
    exercises: str,
    expected: Mapping[str, Any],
    facts: Mapping[str, Any],
    file: Path,
    byte_reproducible: bool,
    command: str | None = None,
) -> Entry:
    """Build one manifest entry from a written file.

    Args:
        sample_id: The sample id.
        group: One of :data:`GROUPS`.
        kind: The file kind.
        storage: One of :data:`STORAGES`.
        path: The path as the manifest records it (relative, forward slashes).
        serves: The spec clauses and V-tests served.
        exercises: What a test uses the sample for.
        expected: The ``expect`` block (:func:`expect`).
        facts: What was measured from the written file.
        file: The file as written; its size (and md5, when reproducible) are read here.
        byte_reproducible: Whether regeneration gives the same bytes.
        command: The regeneration command, for a generated sample.

    Returns:
        The entry.
    """
    return {
        "id": sample_id,
        "group": group,
        "kind": kind,
        "storage": storage,
        "path": path,
        "command": command,
        "serves": list(serves),
        "exercises": exercises,
        "expect": dict(expected),
        "facts": dict(facts),
        "size": file.stat().st_size,
        "md5": md5_of(file) if byte_reproducible else None,
        "byte_reproducible": byte_reproducible,
    }


def build(entries: Sequence[Entry], omitted: Sequence[Mapping[str, str]]) -> dict[str, Any]:
    """Assemble the manifest.

    Args:
        entries: The entries; sorted by id here so the file does not depend on run order.
        omitted: Samples the brief asked for that could not be produced, each with a reason.

    Returns:
        The manifest dictionary.
    """
    return {
        "schema": SCHEMA,
        "limits": {"max_file_bytes": MAX_FILE_BYTES, "max_total_bytes": MAX_TOTAL_BYTES},
        "samples": sorted(entries, key=lambda item: str(item["id"])),
        "omitted": [dict(item) for item in omitted],
    }


def _bad_path(path: object) -> bool:
    """Return True when ``path`` is not a clean relative forward-slash path."""
    if not isinstance(path, str) or not path or "\\" in path:
        return True
    pure = PurePosixPath(path)
    return pure.is_absolute() or ".." in pure.parts or re.match(r"^[A-Za-z]:", path) is not None


def _field_names(cls: type) -> set[str]:
    """Return the field names of a WP2.2 dataclass."""
    return {field.name for field in dataclasses.fields(cls)}


def _unknown_keys(label: str, where: str, block: object, cls: type) -> list[str]:
    """Return one problem per key of ``block`` that is not a field of ``cls``."""
    if not isinstance(block, dict):
        return [f"{label}: {where} is not an object"]
    allowed = _field_names(cls)
    return [
        f"{label}: {where} key {key!r} is not a {cls.__name__} field ({', '.join(sorted(allowed))})"
        for key in block
        if key not in allowed
    ]


def _problems_of_names(label: str, block: dict[str, Any]) -> list[str]:
    """Return the key-name problems of the ``photo`` and ``probe`` parts of an ``expect``."""
    problems: list[str] = []
    photo = block.get("photo")
    if isinstance(photo, dict):
        problems += [
            f"{label}: photo key {key!r} is neither 'metadata' nor 'image'"
            for key in photo
            if key not in ("metadata", "image")
        ]
        problems += _unknown_keys(label, "photo.metadata", photo.get("metadata", {}), PhotoMetadata)
        image = photo.get("image", {})
        problems += _unknown_keys(label, "photo.image", image, Image)
        if isinstance(image, dict) and "color" in image:
            problems += _unknown_keys(label, "photo.image.color", image["color"], ColorDescription)
    probe = block.get("probe")
    if isinstance(probe, dict):
        problems += _unknown_keys(label, "probe", probe, ProbeResult)
        video = probe.get("video")
        if video is not None:
            problems += _unknown_keys(label, "probe.video", video, VideoStreamInfo)
            if isinstance(video, dict) and "color" in video:
                problems += _unknown_keys(
                    label, "probe.video.color", video["color"], ColorDescription
                )
        audio = probe.get("audio", [])
        if not isinstance(audio, list):
            problems.append(f"{label}: probe.audio is not a list")
        else:
            for item in audio:
                problems += _unknown_keys(label, "probe.audio[]", item, AudioStreamInfo)
    return problems


def _problems_of_expect(label: str, block: object) -> list[str]:
    """Return the problems of one ``expect`` block."""
    if not isinstance(block, dict):
        return [f"{label}: expect is not an object"]
    problems = [f"{label}: expect lacks {key!r}" for key in EXPECT_KEYS if key not in block]
    problems += [
        f"{label}: expect has unknown key {key!r}" for key in block if key not in EXPECT_KEYS
    ]
    faults = block.get("faults", [])
    if not isinstance(faults, list):
        return [*problems, f"{label}: expect.faults is not a list"]
    for item in faults:
        if not isinstance(item, dict) or set(item) != {"kind", "severity"}:
            problems.append(f"{label}: fault {item!r} is not {{kind, severity}}")
            continue
        if item["kind"] not in fault_kinds():
            problems.append(
                f"{label}: fault kind {item['kind']!r} is not defined by clearwater.interfaces "
                f"(IF-5 FaultKind: {', '.join(fault_kinds())})"
            )
        if item["severity"] not in fault_severities():
            problems.append(
                f"{label}: fault severity {item['severity']!r} is not defined by "
                f"clearwater.interfaces ({', '.join(fault_severities())})"
            )
    for key in ("refusal", "photo", "probe"):
        if block.get(key) is not None and not isinstance(block[key], dict):
            problems.append(f"{label}: expect.{key} is neither null nor an object")
    return [*problems, *_problems_of_names(label, block)]


def _problems_of_entry(item: object, position: int) -> list[str]:
    """Return the problems of one entry; ``position`` labels an entry with no usable id."""
    if not isinstance(item, dict):
        return [f"sample #{position}: not an object"]
    label = f"sample {item.get('id', f'#{position}')!r}"
    problems = [f"{label}: lacks {key!r}" for key in ENTRY_KEYS if key not in item]
    problems += [f"{label}: has unknown key {key!r}" for key in item if key not in ENTRY_KEYS]
    if problems:
        return problems
    if not isinstance(item["id"], str) or not ID_PATTERN.match(item["id"]):
        problems.append(f"{label}: id is not lower-case words joined by hyphens")
    if item["group"] not in GROUPS:
        problems.append(f"{label}: group {item['group']!r} is not one of {GROUPS}")
    if item["storage"] not in STORAGES:
        problems.append(f"{label}: storage {item['storage']!r} is not one of {STORAGES}")
    if _bad_path(item["path"]):
        problems.append(f"{label}: path {item['path']!r} is not a clean relative path")
    if item["storage"] == "generated" and not (
        isinstance(item["command"], str) and item["command"]
    ):
        problems.append(f"{label}: a generated sample needs its regeneration command")
    if item["storage"] == "committed" and item["command"] is not None:
        problems.append(f"{label}: a committed sample has no command")
    serves = item["serves"]
    if not (isinstance(serves, list) and serves and all(isinstance(s, str) for s in serves)):
        problems.append(f"{label}: serves must be a non-empty list of strings")
    if not (isinstance(item["exercises"], str) and item["exercises"]):
        problems.append(f"{label}: exercises must be a sentence")
    if not isinstance(item["facts"], dict):
        problems.append(f"{label}: facts is not an object")
    if not (isinstance(item["size"], int) and not isinstance(item["size"], bool)):
        problems.append(f"{label}: size is not an integer")
    elif item["size"] < 0:
        problems.append(f"{label}: size is negative")
    elif item["storage"] == "committed" and item["size"] > MAX_FILE_BYTES:
        problems.append(f"{label}: committed size {item['size']} exceeds {MAX_FILE_BYTES}")
    reproducible = item["byte_reproducible"]
    if not isinstance(reproducible, bool):
        problems.append(f"{label}: byte_reproducible is not a boolean")
    md5 = item["md5"]
    if reproducible is True and not (isinstance(md5, str) and re.fullmatch(r"[0-9a-f]{32}", md5)):
        problems.append(f"{label}: a byte-reproducible sample needs a 32-digit md5")
    if reproducible is False and md5 is not None:
        problems.append(f"{label}: md5 is given for a sample that is not byte-reproducible")
    return [*problems, *_problems_of_expect(label, item["expect"])]


def validate(manifest: object) -> list[str]:
    """Check a manifest against the schema; return every problem found, by sample id.

    Args:
        manifest: The parsed ``manifest.json``.

    Returns:
        One message per problem; an empty list when the manifest is valid.
    """
    if not isinstance(manifest, dict):
        return ["manifest is not an object"]
    problems = []
    if manifest.get("schema") != SCHEMA:
        problems.append(f"schema is {manifest.get('schema')!r}, expected {SCHEMA}")
    limits = manifest.get("limits")
    if limits != {"max_file_bytes": MAX_FILE_BYTES, "max_total_bytes": MAX_TOTAL_BYTES}:
        problems.append(f"limits are {limits!r}, not the ruling-4 limits")
    samples = manifest.get("samples")
    if not isinstance(samples, list) or not samples:
        return [*problems, "samples is not a non-empty list"]
    seen: set[str] = set()
    for position, item in enumerate(samples):
        problems += _problems_of_entry(item, position)
        sample_id = item.get("id") if isinstance(item, dict) else None
        if isinstance(sample_id, str):
            if sample_id in seen:
                problems.append(f"sample {sample_id!r}: duplicate id")
            seen.add(sample_id)
    omitted = manifest.get("omitted")
    if not isinstance(omitted, list) or not all(
        isinstance(o, dict) and set(o) == {"what", "reason"} for o in omitted
    ):
        problems.append("omitted is not a list of {what, reason}")
    return problems


def check_files(manifest: Mapping[str, Any], root: Path) -> list[str]:
    """Check the committed files of a manifest against a folder.

    Every committed entry's file must exist, have the recorded size, and (when the entry is
    byte-reproducible) the recorded md5; no file in the folder may be unlisted (except
    ``manifest.json``), and none may exceed the size limits.

    Args:
        manifest: A valid manifest.
        root: The folder holding the committed fixtures.

    Returns:
        One message per problem; an empty list when the folder matches.
    """
    problems = []
    listed: set[str] = {"manifest.json"}
    total = 0
    for item in manifest["samples"]:
        if item["storage"] != "committed":
            continue
        listed.add(item["path"])
        file = root / item["path"]
        if not file.is_file():
            problems.append(f"sample {item['id']!r}: {item['path']} is missing")
            continue
        if file.stat().st_size != item["size"]:
            problems.append(
                f"sample {item['id']!r}: {item['path']} is {file.stat().st_size} bytes, "
                f"the manifest says {item['size']}"
            )
        elif item["byte_reproducible"] and md5_of(file) != item["md5"]:
            problems.append(f"sample {item['id']!r}: {item['path']} does not match its md5")
    for file in sorted(root.rglob("*")):
        if not file.is_file():
            continue
        relative = file.relative_to(root).as_posix()
        size = file.stat().st_size
        total += size
        if relative not in listed:
            problems.append(f"{relative}: not listed in the manifest")
        if size > MAX_FILE_BYTES:
            problems.append(f"{relative}: {size} bytes exceeds the {MAX_FILE_BYTES} byte limit")
    if total >= MAX_TOTAL_BYTES:
        problems.append(f"the folder totals {total} bytes, not under {MAX_TOTAL_BYTES}")
    return problems
