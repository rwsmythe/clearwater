"""Verify real-photo orientation, runner exports and memory without publishing EXIF values.

The product read uses pillow-heif / libheif through ``clearwater.io.photo``.
The independent oracle uses the FFmpeg CLI's DEFAULT composed-primary decode,
as delivered: no stream map, no noautorotate, no additional EXIF/irot transform.
The fixtures demonstrate that FFmpeg honours irot and ignores EXIF-only rotation.
The libheif thumbnail is recorded as a second item witness, never a pass criterion.

CLI subcommands require a schema-1 class map and local configuration. Outputs
are guarded below <working>/wp3.6p; sources are read only. Export uses neutral
parameters, memory uses c3 defaults in a fresh runner process. Memory's CLI
requires --exclusive to declare the dispatcher's exclusive measurement window.
Only explicitly allowed facts are printed or written to summary/record JSON.
Raw subprocess logs remain local guarded evidence, never part of that summary.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import logging
import math
import os
import re
import subprocess
import sys
import threading
import uuid
import zlib
from collections.abc import Iterator, Mapping, Sequence
from contextvars import ContextVar
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, NoReturn

import numpy as np
import pillow_heif
import psutil
from numpy.typing import NDArray
from PIL import Image as PILImage

import headless_export as he
from clearwater.core.memory import memory_estimate_bytes
from clearwater.interfaces import Image, ParameterSet, PhotoMetadata, Settings
from clearwater.io.photo import PhotoReadError, read_photo
from clearwater.io.photo import exif as exif_tools
from clearwater.io.photo import icc as icc_tools
from clearwater.io.photo.heif_boxes import read_layout
from clearwater.io.photo.p3_profile import display_p3_profile
from clearwater.io.photo.reader import detect_format
from clearwater.io.photo.srgb_profile import srgb_profile
from clearwater.jobs.export_seam import ExportJobs
from fixtures.stills import heif_primary_properties
from local_config import LocalConfig, load_local_config
from spike_io.guard import OutputRefusedError, WriteGuard

type Record = dict[str, Any]
type Pixels = NDArray[Any]

_CLASSES = {
    "HEIC-0": 23,
    "HEIC-90": 3,
    "HEIC-180": 20,
    "HEIC-270": 16,
    "JPG-A": 2,
    "JPG-Z": 8,
    "JPG-M": 1,
}
_D63 = {"IFD0.Orientation", "IFD0.Software", "Exif.ExifImageWidth", "Exif.ExifImageHeight"}
_RAM_LIMIT = 16_000_000_000
_DEVICE_LIMIT = 8188 * 2**20
_DISK_LIMIT = 20_000_000_000
_ACTIVE_GUARD: ContextVar[WriteGuard | None] = ContextVar("photo_verify_guard", default=None)
_CHECKS = frozenset(
    {
        "read_failed",
        "oracle_failed",
        "orientation_upright",
        "orientation_discrimination",
        "runner_failed",
        "v5_bit_depth",
        "v5_icc_equal",
        "v5_orientation",
        "v5_software",
        "v5_dimensions",
        "v5_thumbnail",
        "v5_kept_exif",
        "v9_identity",
        "d53_primaries",
        "memory_device_measurement",
        "memory_rss_measurement",
        "memory_ram_limit",
        "memory_device_limit",
        "class_layout",
        "invalid_request",
        "output_refused",
    }
)
_BOOL_FIELDS = frozenset(
    [
        "read_ok",
        "grid",
        "raw_exif_present",
        "exif_present",
        "sanitise_dropped",
        "gps_ifd_present",
        "gps_kept",
        "maker_note_present",
        "maker_note_kept",
        "assumed",
        "icc_present",
        "icc_valid",
        "orientation_ok",
        "v5_ok",
        "d53_ok",
        "v9_ok",
        "retained",
        "orientation_normal",
        "software_ok",
        "dimensions_ok",
        "thumbnail_absent",
        "icc_expected_present",
        "icc_equal",
        "primaries_equal",
        "transfer_equal",
        "kept_fields_equal",
        "force_cpu",
        "forced_cpu",
        "automatic_fallback",
        "estimate_exceeds_free_before",
        "exclusive",
    ]
)
_NUMBER_FIELDS = frozenset(
    [
        "schema",
        "source_bytes",
        "source_bit_depth",
        "orientation_tag",
        "irot",
        "imir",
        "auxiliary_count",
        "thumbnail_count",
        "icc_bytes",
        "field_count_before",
        "field_count_after",
        "winning_pose",
        "upright_mean_255",
        "nearest_other_mean_255",
        "margin_255",
        "requested_depth",
        "output_depth",
        "png_bytes",
        "runner_exit",
        "quantised_max_255",
        "quantised_mean_255",
        "raw_max_255",
        "raw_mean_255",
        "estimate_bytes",
        "device_free_before_bytes",
        "device_total_bytes",
        "rss_baseline_bytes",
        "rss_tree_peak_bytes",
        "os_peak_working_set_bytes",
        "device_used_baseline_bytes",
        "device_used_peak_bytes",
        "rss_samples",
        "device_samples",
        "ram_limit_bytes",
        "device_limit_bytes",
    ]
)
_ENUMS = {
    "command": {"orientation", "export", "memory"},
    "class": set(_CLASSES),
    "candidate_group": {"none", "Z", "M"},
    "source_format": {"heic", "jpeg", "png", "tiff"},
    "primaries": {"bt709", "display-p3", "bt2020", "unknown"},
    "transfer": {"srgb", "bt709", "unknown"},
    "oracle_kind": {"ffmpeg-default"},
    "method": {"c3"},
    "primary_type": {"grid", "hvc1", "av01", "iden"},
    "failure_code": {
        "unreadable",
        "unsupported",
        "oracle_failed",
        "runner_failed",
        "invalid_request",
        "output_refused",
        "thumbnail_unavailable",
    },
}
_CPU_REASONS = {
    "CPU: forced",
    "CPU: CuPy not installed",
    "CPU: CuPy failed to load",
    "CPU: no CUDA device",
    "CPU: CUDA device unusable",
}


def _name(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", value) or value in {".", ".."}:
        raise ValueError("unsafe name")
    return value


def _folder(guard: WriteGuard, label: str) -> Path:
    return guard.folder(_name(label) + "-" + uuid.uuid4().hex[:12])


def _write_json(path: Path, value: object, guard: WriteGuard) -> None:
    guard.check(path).write_text(
        json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + "\n", encoding="ascii"
    )


def _disk_check(root: Path, budget: int = 0) -> int:
    free = int(psutil.disk_usage(str(root)).free)
    if free < _DISK_LIMIT + budget:
        raise OutputRefusedError("outside", root, "insufficient free disk")
    return free


@contextlib.contextmanager
def _quiet_logs() -> Iterator[None]:
    previous = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        yield
    finally:
        logging.disable(previous)


def make_guard(config: LocalConfig) -> WriteGuard:
    """Create this instrument's write guard below the configured working folder.

    Args:
        config: The local read-only footage and working paths.

    Returns:
        A guard rooted at working/wp3.6p, with that directory created.
    """
    root = config.working_path.resolve() / "wp3.6p"
    guard = WriteGuard(root=root, footage=config.footage_path)
    guard.check(root)
    root.mkdir(parents=True, exist_ok=True)
    return guard


def load_class_map(path: Path) -> Record:
    """Validate a complete seven-class, names-only inventory map.

    Args:
        path: JSON input containing schema 1 and the seven classes.

    Returns:
        The validated JSON map.

    Raises:
        ValueError: The schema, names, representatives or counts are invalid.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(data, dict)
        or set(data) != {"schema", "classes"}
        or type(data["schema"]) is not int
        or data["schema"] != 1
    ):
        raise ValueError("invalid class map")
    classes = data["classes"]
    if not isinstance(classes, dict) or set(classes) != set(_CLASSES):
        raise ValueError("invalid classes")
    seen: set[str] = set()
    for label, expected in _CLASSES.items():
        group = classes[label]
        if not isinstance(group, dict) or set(group) != {"files", "representative"}:
            raise ValueError("invalid class entry")
        files = group["files"]
        if not isinstance(files, list) or len(files) != expected:
            raise ValueError("invalid class count")
        for file in files:
            if not isinstance(file, str):
                raise ValueError("invalid file name")
            _name(file)
            suffixes = {".heic", ".heif"} if label.startswith("HEIC") else {".jpg", ".jpeg"}
            if file.casefold() in seen or Path(file).suffix.lower() not in suffixes:
                raise ValueError("duplicate or wrong format")
            seen.add(file.casefold())
        if group["representative"] not in files:
            raise ValueError("invalid representative")
    return dict(data)


def ffmpeg_decode(source: Path, out_png: Path, guard: WriteGuard) -> Pixels:
    """Decode FFmpeg's default composed HEIC primary, without another transform.

    Args:
        source: Read-only HEIC source.
        out_png: New PNG path inside the guard.
        guard: Authority for every output including subprocess stderr.

    Returns:
        RGB pixels in 0..255, exactly in FFmpeg's delivered pose.

    Raises:
        ValueError: Decoding failed or did not deliver the primary dimensions.
        OutputRefusedError: The output is outside the write guard.
    """
    guard.check(out_png)
    if out_png.exists():
        raise ValueError("oracle output exists")
    guard.check(out_png.parent).mkdir(parents=True, exist_ok=True)
    props = heif_primary_properties(source.read_bytes())
    width, height = props["ispe"]
    expected = (height, width) if props["irot"] in (90, 270) else (width, height)
    args = [
        "ffmpeg",
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "error",
        "-n",
        "-i",
        str(source),
        "-frames:v",
        "1",
        "-update",
        "1",
        "-map_metadata",
        "-1",
        "-pix_fmt",
        "rgb24",
        str(out_png),
    ]
    done = subprocess.run(args, capture_output=True, timeout=120, check=False)
    guard.check(out_png.with_suffix(".stderr")).write_bytes(done.stderr)
    if done.returncode != 0:
        raise ValueError("oracle decode failed")
    with PILImage.open(out_png) as image:
        if image.size != expected:
            raise ValueError("oracle primary size mismatch")
        return np.asarray(image.convert("RGB")).copy()


def _small(pixels: Pixels, max_side: int) -> Pixels:
    if pixels.ndim != 3 or pixels.shape[2] != 3 or not np.isfinite(pixels).all():
        raise ValueError("invalid RGB samples")
    image = PILImage.fromarray(np.clip(np.rint(pixels), 0, 255).astype(np.uint8))
    image.thumbnail((max_side, max_side), PILImage.Resampling.LANCZOS)
    return np.asarray(image, dtype=np.float64)


def compare_poses(pixels: Pixels, reference: Pixels, *, max_side: int = 256) -> Record:
    """Compare all eight dihedral poses with explicit upright/discrimination bounds.

    Args:
        pixels: Observed RGB in 0..255.
        reference: Independent reference RGB in 0..255.
        max_side: Bound for the aspect-preserving comparison images.

    Returns:
        All scores in 1/255 units, mismatched shapes and named failures.
    """
    if max_side < 1:
        raise ValueError("invalid comparison size")
    got, ref = _small(pixels, max_side), _small(reference, max_side)
    poses = [
        ref,
        np.fliplr(ref),
        np.rot90(ref, 2),
        np.flipud(ref),
        np.swapaxes(ref, 0, 1),
        np.rot90(ref, -1),
        np.flip(np.swapaxes(ref, 0, 1), axis=(0, 1)),
        np.rot90(ref, 1),
    ]
    scores = {
        str(i): float(np.abs(got - pose).mean()) if got.shape == pose.shape else None
        for i, pose in enumerate(poses, 1)
    }
    comparable = {int(k): v for k, v in scores.items() if v is not None}
    upright = scores["1"]
    others = [v for k, v in scores.items() if k != "1" and v is not None]
    nearest = min(others) if others else None
    winner = min(comparable, key=lambda k: comparable[k]) if comparable else None
    failures = []
    if upright is None or upright >= 6.0:
        failures.append("orientation_upright")
    if nearest is None or nearest <= 10.0 or winner != 1:
        failures.append("orientation_discrimination")
    return {
        "scores_by_pose": scores,
        "shape_mismatches": [int(k) for k, v in scores.items() if v is None],
        "winning_pose": winner,
        "upright_mean_255": upright,
        "nearest_other_mean_255": nearest,
        "margin_255": None if nearest is None or upright is None else nearest - upright,
        "orientation_ok": not failures,
        "failed_checks": failures,
    }


def thumbnail_decode(source: Path) -> Pixels | None:
    """Read the primary's first thumbnail with libheif's item transforms.

    Args:
        source: Read-only HEIC source.

    Returns:
        RGB in 0..255, or None when the primary has no thumbnail.
    """
    heif = pillow_heif.open_heif(str(source), convert_hdr_to_8bit=False)
    primary = heif[heif.primary_index]
    if not primary.info.get("thumbnails"):
        return None
    return np.asarray(primary.get_thumbnail(0).to_pillow().convert("RGB")).copy()


def _raw_exif(data: bytes, kind: str | None) -> bytes | None:
    if kind == "heic":
        raw = pillow_heif.open_heif(io.BytesIO(data), convert_hdr_to_8bit=False).info.get("exif")
    else:
        with PILImage.open(io.BytesIO(data)) as opened:
            raw = opened.info.get("exif")
    return exif_tools.strip_prefix(raw) if isinstance(raw, bytes) and raw else None


def _base(source: Path, photo_class: str) -> tuple[Record, Image, PhotoMetadata, bytes | None]:
    _name(source.name)
    if photo_class not in _CLASSES:
        raise ValueError("invalid class")
    with _quiet_logs():
        data = source.read_bytes()
        kind = detect_format(data)
        raw = _raw_exif(data, kind)
        image, meta = read_photo(source)
        try:
            fields = exif_tools.describe(raw)
        except Exception:
            # Raw presence and sanitise_dropped still distinguish damaged metadata.
            fields = {}
    height, width = image.pixels.shape[:2]
    color = image.color
    profile = color.icc_profile
    record: Record = {
        "schema": 1,
        "file": source.name,
        "class": photo_class,
        "candidate_group": photo_class[-1] if photo_class in {"JPG-Z", "JPG-M"} else "none",
        "read_ok": True,
        "source_format": meta.source_format,
        "source_bytes": len(data),
        "decoded_size": [width, height],
        "stored_size": [height, width] if meta.orientation in (5, 6, 7, 8) else [width, height],
        "source_bit_depth": color.bit_depth,
        "orientation_tag": meta.orientation,
        "primaries": color.primaries,
        "transfer": color.transfer,
        "assumed": color.assumed,
        "icc_present": profile is not None,
        "raw_exif_present": raw is not None,
        "exif_present": meta.exif is not None,
        "sanitise_dropped": raw is not None and meta.exif is None,
        "fields_before": sorted(fields),
        "field_count_before": len(fields),
        "gps_ifd_present": any(k.startswith("GPS.") for k in fields),
        "maker_note_present": "Exif.MakerNote" in fields,
        "failed_checks": [],
    }
    if profile is not None:
        record.update(
            icc_description=icc_tools.description(profile),
            icc_bytes=len(profile),
            icc_md5=hashlib.md5(profile).hexdigest(),
            icc_valid=icc_tools.is_valid_profile(profile),
        )
    if kind == "heic":
        layout = read_layout(data)
        record.update(
            primary_type=layout.item_type,
            grid=layout.is_grid,
            irot=layout.irot,
            imir=layout.imir,
            clap=layout.clap,
            ispe=layout.ispe,
            stored_size=layout.ispe,
            auxiliary_count=len(layout.auxiliary_ids),
            thumbnail_count=len(layout.thumbnail_ids),
        )
    return record, image, meta, raw


def _failure(source: Path, photo_class: str, code: str, check: str) -> Record:
    return {
        "file": source.name,
        "class": photo_class,
        "read_ok": False,
        "failure_code": code,
        "failed_checks": [check],
    }


def verify_orientation(
    source: Path, guard: WriteGuard, *, photo_class: str, max_side: int = 256
) -> Record:
    """Compare a product read with FFmpeg and record the non-gating thumbnail witness.

    Args:
        source: Read-only HEIC input.
        guard: Guard for all oracle and safe-record outputs.
        photo_class: Inventory class for separate reporting.
        max_side: Aspect-preserving comparison size bound.

    Returns:
        A safe per-photo record; failures contain fixed codes, never exception text.
    """
    folder = _folder(guard, source.stem)
    try:
        record, image, _, _ = _base(source, photo_class)
    except (PhotoReadError, OSError, ValueError):
        return _failure(source, photo_class, "unreadable", "read_failed")
    record["oracle_kind"] = "ffmpeg-default"
    record["command"] = "orientation"
    try:
        reference = ffmpeg_decode(source, folder / "oracle.png", guard)
        record.update(compare_poses(image.pixels * 255, reference, max_side=max_side))
        record["oracle_size"] = [reference.shape[1], reference.shape[0]]
    except (OSError, ValueError, subprocess.SubprocessError):
        record.update(
            orientation_ok=False, failure_code="oracle_failed", failed_checks=["oracle_failed"]
        )
    witness: Record = {"available": False}
    try:
        thumbnail = thumbnail_decode(source)
        if thumbnail is not None:
            witness = {
                "available": True,
                "size": [thumbnail.shape[1], thumbnail.shape[0]],
                **compare_poses(image.pixels * 255, thumbnail, max_side=max_side),
            }
    except Exception:  # ancillary evidence must never replace the primary criterion
        witness["failure_code"] = "thumbnail_unavailable"
    record["thumbnail_witness"] = witness
    safe = _safe_record(record)
    _write_json(folder / "record.json", safe, guard)
    return safe


def _png_metadata(path: Path) -> tuple[int, bytes | None, bytes | None]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not PNG")
    chunks: dict[bytes, bytes] = {}
    at = 8
    while at < len(data):
        length = int.from_bytes(data[at : at + 4], "big")
        kind, body = data[at + 4 : at + 8], data[at + 8 : at + 8 + length]
        stop = at + 12 + length
        if stop > len(data) or len(kind) != 4:
            raise ValueError("truncated PNG")
        if zlib.crc32(kind + body) & 0xFFFFFFFF != int.from_bytes(data[stop - 4 : stop], "big"):
            raise ValueError("PNG CRC")
        if kind in {b"IHDR", b"iCCP", b"eXIf"}:
            if kind in chunks:
                raise ValueError("duplicate PNG metadata")
            chunks[kind] = body
        at = stop
    ihdr = chunks.get(b"IHDR", b"")
    if len(ihdr) != 13:
        raise ValueError("missing IHDR")
    profile = None
    if b"iCCP" in chunks:
        _, payload = chunks[b"iCCP"].split(b"\0", 1)
        if not payload or payload[0] != 0:
            raise ValueError("invalid iCCP")
        profile = zlib.decompress(payload[1:])
    return ihdr[8], profile, chunks.get(b"eXIf")


def _expected_icc(image: Image, meta: PhotoMetadata) -> bytes | None:
    color = image.color
    if color.icc_profile is not None:
        return color.icc_profile
    if meta.source_format == "heic" and not color.assumed and color.transfer == "srgb":
        if color.primaries == "bt709":
            return srgb_profile()
        if color.primaries == "display-p3":
            return display_p3_profile()
    return None


def _device_reason(raw: object) -> str | None:
    if not isinstance(raw, str):
        return None
    if raw == "GPU" or raw in _CPU_REASONS:
        return raw
    if re.fullmatch(r"CPU: estimate [0-9,]+ MiB exceeds free [0-9,]+ MiB", raw):
        return raw
    return None


def _export_checks(
    record: Record,
    image: Image,
    meta: PhotoMetadata,
    raw_exif: bytes | None,
    output: Path,
    depth: int,
) -> None:
    output_depth, profile, block = _png_metadata(output)
    with _quiet_logs():
        again, _ = read_photo(output)
        try:
            before = exif_tools.describe(raw_exif)
        except Exception:
            before = {}
        after = exif_tools.describe(block)
    height, width = image.pixels.shape[:2]
    expected = _expected_icc(image, meta)
    lost = sorted(k for k in before if k not in _D63 and before[k] != after.get(k))
    record.update(
        output_depth=output_depth,
        icc_expected_present=expected is not None,
        icc_equal=profile == expected,
        orientation_normal=after.get("IFD0.Orientation") == "1",
        software_ok=after.get("IFD0.Software") == exif_tools.SOFTWARE,
        dimensions_ok=(after.get("Exif.ExifImageWidth"), after.get("Exif.ExifImageHeight"))
        == (str(width), str(height)),
        thumbnail_absent=block is not None and not exif_tools.has_thumbnail(block),
        kept_fields_equal=not lost,
        changed_kept_fields=lost,
        fields_after=sorted(after),
        field_count_after=len(after),
        maker_note_kept=all(after.get(k) == v for k, v in before.items() if k == "Exif.MakerNote"),
        gps_kept=all(after.get(k) == v for k, v in before.items() if k.startswith("GPS.")),
        primaries_equal=image.color.primaries == again.color.primaries,
        transfer_equal=image.color.transfer == again.color.transfer,
    )
    checks = {
        "v5_bit_depth": depth == output_depth,
        "v5_icc_equal": record["icc_equal"],
        "v5_orientation": record["orientation_normal"],
        "v5_software": record["software_ok"],
        "v5_dimensions": record["dimensions_ok"],
        "v5_thumbnail": record["thumbnail_absent"],
        "v5_kept_exif": not lost and not record["sanitise_dropped"],
    }
    record["v5_ok"] = all(checks.values())
    record["d53_ok"] = bool(
        profile == expected and record["primaries_equal"] and record["transfer_equal"]
    )
    failures = [k for k, passed in checks.items() if not passed]
    if not record["d53_ok"]:
        failures.append("d53_primaries")
    pixels = image.pixels.astype(np.float64)
    if again.pixels.shape == pixels.shape:
        top = (1 << depth) - 1
        reference = np.rint(np.clip(pixels, 0, 1) * top) / top
        quantised = np.abs(reference - again.pixels) * 255
        raw = np.abs(pixels - again.pixels) * 255
        qm, qa, rm, ra = (
            float(quantised.max()),
            float(quantised.mean()),
            float(raw.max()),
            float(raw.mean()),
        )
        record.update(quantised_max_255=qm, quantised_mean_255=qa, raw_max_255=rm, raw_mean_255=ra)
        record["v9_ok"] = (
            qm <= 2
            and qa <= 0.2
            and ((depth < 16 and image.color.bit_depth > 8) or (rm <= 2 and ra <= 0.2))
        )
    else:
        record["v9_ok"] = False
    if not record["v9_ok"]:
        failures.append("v9_identity")
    record["failed_checks"] = failures


def verify_export(
    source: Path,
    guard: WriteGuard,
    *,
    photo_class: str,
    bit_depth: int,
    force_cpu: bool = False,
    keep: bool = False,
    parameters: ParameterSet | None = None,
    exports: ExportJobs | None = None,
) -> Record:
    """Export through the runner and measure V5/D53/V9 before optional PNG deletion.

    Args:
        source: Read-only source photo.
        guard: Authority for records, logs and PNG targets/deletion.
        photo_class: Inventory class; Z and M remain separate.
        bit_depth: Requested PNG depth, 8 or 16.
        force_cpu: Override default selection for synthetic checks.
        keep: Retain this successfully measured representative PNG.
        parameters: Optional planted control; default is the neutral c3 set.
        exports: Optional runner engine for a planted writer control.

    Returns:
        A safe record; failed exports retain their diagnostic PNG.
    """
    if bit_depth not in (8, 16):
        raise ValueError("invalid bit depth")
    try:
        width, height = _dimensions(source)
    except (OSError, ValueError):
        return _failure(source, photo_class, "unreadable", "read_failed")
    _disk_check(guard.root, width * height * 6)
    folder = _folder(guard, source.stem)
    try:
        record, image, meta, raw = _base(source, photo_class)
    except (PhotoReadError, OSError, ValueError):
        return _failure(source, photo_class, "unreadable", "read_failed")
    record.update(command="export", requested_depth=bit_depth, retained=False)
    out = guard.folder(folder.name, "out")
    settings = Settings(output_folder=out, png_bit_depth=bit_depth, force_cpu=force_cpu)
    requests = he.requests_for(
        [source], parameters=parameters or he.parameters_for(neutral=True), settings=settings
    )
    with _quiet_logs():
        result = he.run(
            requests,
            exports=exports,
            footage_folder=guard.footage,
            parameters_from="neutral" if parameters is None else "given",
        )
    _write_json(folder / "runner.json", he.record_object(result), guard)
    item = result.report.items[0]
    record["runner_exit"] = he.exit_status(result)
    record["device_reason"] = None if item.result is None else _device_reason(item.result.device)
    if record["runner_exit"] != 0 or item.result is None or len(item.result.outputs) != 1:
        record.update(failure_code="runner_failed", failed_checks=["runner_failed"])
    else:
        output = guard.check(item.result.outputs[0])
        record.update(
            png_bytes=output.stat().st_size, png_md5=hashlib.md5(output.read_bytes()).hexdigest()
        )
        try:
            _export_checks(record, image, meta, raw, output, bit_depth)
        except (OSError, ValueError, PhotoReadError, zlib.error):
            record.update(v5_ok=False, v9_ok=False, d53_ok=False, failed_checks=["runner_failed"])
        record["retained"] = keep or bool(record["failed_checks"])
        if not record["retained"]:
            guard.check(output).unlink()
    safe = _safe_record(record)
    _write_json(folder / "record.json", safe, guard)
    return safe


def device_memory() -> dict[str, int] | None:
    """Read device-zero free/total/used bytes through nvidia-smi, without identifiers.

    Returns:
        Device-wide memory in bytes, or None when the sampler is unavailable.
    """
    try:
        done = subprocess.run(
            [
                "nvidia-smi",
                "--id=0",
                "--query-gpu=memory.free,memory.total,memory.used",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if done.returncode != 0:
            return None
        values = [int(float(v.strip()) * 2**20) for v in done.stdout.strip().split(",")]
        if len(values) != 3 or any(v < 0 for v in values):
            return None
        return dict(zip(("free_bytes", "total_bytes", "used_bytes"), values, strict=True))
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


class MemorySampler:
    """Sample simultaneous process-tree RSS and device-wide used bytes on separate threads."""

    def __init__(self, process: Any) -> None:
        """Prepare samplers and take the pre-run baseline.

        Args:
            process: psutil root process; its descendants include the runner.
        """
        self._process = process
        self._stop = threading.Event()
        self._errors: set[str] = set()
        self._rss_samples = 0
        self._device_samples = 0
        self._rss_peak: int | None = None
        self._device_peak: int | None = None
        self._os_peak: int | None = None
        self._rss()
        self._gpu()
        self._baseline = self._rss_peak
        self._device_baseline = self._device_peak
        self._threads = [
            threading.Thread(target=self._loop, args=(0.05, self._rss), daemon=True),
            threading.Thread(target=self._loop, args=(0.2, self._gpu), daemon=True),
        ]

    def _loop(self, interval: float, sample: Any) -> None:
        while not self._stop.wait(interval):
            sample()

    def _rss(self) -> None:
        try:
            processes = [self._process, *self._process.children(recursive=True)]
            total = 0
            for process in processes:
                try:
                    info = process.memory_info()
                    total += int(info.rss)
                    peak = getattr(info, "peak_wset", None)
                    if peak is not None:
                        self._os_peak = max(self._os_peak or 0, int(peak))
                except psutil.NoSuchProcess:
                    continue
            self._rss_peak = max(self._rss_peak or 0, total)
            self._rss_samples += 1
        except psutil.Error:
            self._errors.add("rss_unavailable")

    def _gpu(self) -> None:
        memory = device_memory()
        if memory is None:
            self._errors.add("device_unavailable")
            return
        self._device_peak = max(self._device_peak or 0, memory["used_bytes"])
        self._device_samples += 1

    def start(self) -> None:
        """Start both sampling threads before the runner is launched."""
        for thread in self._threads:
            thread.start()

    def stop(self) -> None:
        """Join the threads and take final RSS/device readings."""
        self._stop.set()
        for thread in self._threads:
            thread.join()
        self._rss()
        self._gpu()

    def record(self) -> Record:
        """Return sampled peaks and availability without process or device identifiers.

        Returns:
            Simultaneous tree RSS, the maximum observed individual-process OS peak,
            device peaks, sample counts/intervals and fixed sampler error codes.
        """
        return {
            "rss_baseline_bytes": self._baseline,
            "rss_tree_peak_bytes": self._rss_peak,
            "os_peak_working_set_bytes": self._os_peak,
            "device_used_baseline_bytes": self._device_baseline,
            "device_used_peak_bytes": self._device_peak,
            "rss_samples": self._rss_samples,
            "device_samples": self._device_samples,
            "sample_intervals_s": {"rss": 0.05, "device": 0.2},
            "sampler_errors": sorted(self._errors),
        }


def launch_runner(
    source: Path,
    out: Path,
    record_path: Path,
    settings_dir: Path,
    *,
    bit_depth: int,
    force_cpu: bool,
    neutral: bool,
) -> tuple[int, Record]:
    """Launch a fresh product runner with guarded output, record, settings and logs.

    Args:
        source: Read-only source photo.
        out: Guarded output folder.
        record_path: Guarded new runner record path.
        settings_dir: Guarded isolated settings directory.
        bit_depth: PNG depth.
        force_cpu: Whether to pass --force-cpu.
        neutral: Whether to pass --neutral (False for memory measurements).

    Returns:
        The process exit code and local runner JSON. Callers project safe facts.

    Raises:
        ValueError: No active caller write guard was supplied or a target exists.
    """
    guard = _ACTIVE_GUARD.get()
    if guard is None:
        raise ValueError("runner requires caller guard")
    for folder in (out, settings_dir):
        guard.check(folder).mkdir(parents=True, exist_ok=True)
    guard.check(record_path)
    if record_path.exists():
        raise ValueError("runner record exists")
    args = [
        sys.executable,
        str(Path(__file__).with_name("headless_export.py")),
        str(source),
        "--out",
        str(out),
        "--record",
        str(record_path),
        "--settings-dir",
        str(settings_dir),
        "--bit-depth",
        str(bit_depth),
    ]
    if force_cpu:
        args.append("--force-cpu")
    if neutral:
        args.append("--neutral")
    with (
        guard.check(record_path.with_suffix(".stdout")).open("wb") as stdout,
        guard.check(record_path.with_suffix(".stderr")).open("wb") as stderr,
    ):
        done = subprocess.run(args, stdout=stdout, stderr=stderr, check=False)
    raw = json.loads(record_path.read_text(encoding="utf-8")) if record_path.exists() else {}
    return done.returncode, raw if isinstance(raw, dict) else {}


def _dimensions(source: Path) -> tuple[int, int]:
    data = source.read_bytes()
    if detect_format(data) == "heic":
        props = heif_primary_properties(data)
        size = props["ispe"]
        return int(size[0]), int(size[1])
    with PILImage.open(io.BytesIO(data)) as opened:
        return opened.size


def verify_memory(
    source: Path,
    guard: WriteGuard,
    *,
    photo_class: str,
    force_cpu: bool = False,
    bit_depth: int = 16,
    exclusive: bool = False,
) -> Record:
    """Measure a fresh non-neutral c3 runner with RSS/device samplers.

    Args:
        source: Read-only input; only its header size is read in the parent.
        guard: Write boundary for the runner, settings, logs and safe record.
        photo_class: Reporting class.
        force_cpu: Explicit CPU leg after the default-device leg.
        bit_depth: PNG depth, normally 16.
        exclusive: Dispatcher's declaration of the exclusive seat window.

    Returns:
        Estimate, pre-run free memory, actual device reason, peaks and limitations.
    """
    width, height = _dimensions(source)
    _disk_check(guard.root, width * height * 6)
    folder = _folder(guard, source.stem)
    out = guard.folder(folder.name, "out")
    settings = guard.folder(folder.name, "settings")
    runner_record = guard.check(folder / "runner.json")
    memory = device_memory()
    estimate = memory_estimate_bytes(height, width, "c3")
    record: Record = {
        "schema": 1,
        "command": "memory",
        "file": source.name,
        "class": photo_class,
        "method": "c3",
        "stored_size": [width, height],
        "force_cpu": force_cpu,
        "forced_cpu": force_cpu,
        "exclusive": exclusive,
        "estimate_bytes": estimate,
        "device_free_before_bytes": None if memory is None else memory["free_bytes"],
        "device_total_bytes": None if memory is None else memory["total_bytes"],
        "estimate_exceeds_free_before": None if memory is None else estimate > memory["free_bytes"],
        "ram_limit_bytes": _RAM_LIMIT,
        "device_limit_bytes": _DEVICE_LIMIT,
        "measured_at_utc": datetime.now(UTC).isoformat(),
        "failed_checks": [],
    }
    sampler = MemorySampler(psutil.Process(os.getpid()))
    token = _ACTIVE_GUARD.set(guard)
    sampler.start()
    try:
        exit_code, raw = launch_runner(
            source,
            out,
            runner_record,
            settings,
            bit_depth=bit_depth,
            force_cpu=force_cpu,
            neutral=False,
        )
    finally:
        sampler.stop()
        _ACTIVE_GUARD.reset(token)
    record.update(sampler.record())
    items = raw.get("items", [])
    reason = _device_reason(items[0].get("device")) if len(items) == 1 else None
    record.update(
        runner_exit=exit_code,
        device_reason=reason,
        read_ok=exit_code == 0,
        automatic_fallback=bool(reason and reason.startswith("CPU:") and reason != "CPU: forced"),
    )
    failures = []
    if exit_code != 0 or reason is None:
        failures.append("runner_failed")
    for prefix, peak, count, limit in (
        ("ram", "rss_tree_peak_bytes", "rss_samples", _RAM_LIMIT),
        ("device", "device_used_peak_bytes", "device_samples", _DEVICE_LIMIT),
    ):
        measured = record.get(peak)
        if measured is None or record.get(count, 0) <= 0:
            record[prefix + "_within_limit"] = None
            failures.append(
                "memory_rss_measurement" if prefix == "ram" else "memory_device_measurement"
            )
        else:
            record[prefix + "_within_limit"] = measured <= limit
            if measured > limit:
                failures.append("memory_ram_limit" if prefix == "ram" else "memory_device_limit")
    if (memory is None or "device_unavailable" in record.get("sampler_errors", [])) and (
        "memory_device_measurement" not in failures
    ):
        failures.append("memory_device_measurement")
    if (
        "rss_unavailable" in record.get("sampler_errors", [])
        and "memory_rss_measurement" not in failures
    ):
        failures.append("memory_rss_measurement")
    record["failed_checks"] = failures
    safe = _safe_record(record)
    _write_json(folder / "record.json", safe, guard)
    return safe


def _number(value: object) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _safe_record(record: Mapping[str, Any]) -> Record:
    safe: Record = {}
    for key in _BOOL_FIELDS:
        if type(record.get(key)) is bool:
            safe[key] = record[key]
    for key in _NUMBER_FIELDS:
        value = record.get(key)
        if key in record and (value is None or _number(value)):
            safe[key] = value
    for key in ("ram_within_limit", "device_within_limit", "estimate_exceeds_free_before"):
        if key in record and (record[key] is None or type(record[key]) is bool):
            safe[key] = record[key]
    for key, values in _ENUMS.items():
        if isinstance(record.get(key), str) and record[key] in values:
            safe[key] = record[key]
    file = record.get("file")
    if isinstance(file, str):
        with contextlib.suppress(ValueError):
            safe["file"] = _name(file)
    reason = _device_reason(record.get("device_reason"))
    if "device_reason" in record:
        safe["device_reason"] = reason
    for key in ("icc_md5", "png_md5"):
        if isinstance(record.get(key), str) and re.fullmatch(r"[a-f0-9]{32}", record[key]):
            safe[key] = record[key]
    if isinstance(record.get("icc_description"), str):
        safe["icc_description"] = record["icc_description"][:1024]
    stamp = record.get("measured_at_utc")
    if isinstance(stamp, str) and re.fullmatch(r"[0-9T:.+Z-]+", stamp):
        safe["measured_at_utc"] = stamp
    for key in ("stored_size", "decoded_size", "clap", "ispe", "oracle_size", "size"):
        value = record.get(key)
        if (
            isinstance(value, (tuple, list))
            and len(value) == 2
            and all(type(v) is int and v > 0 for v in value)
        ):
            safe[key] = list(value)
    for key in ("fields_before", "fields_after", "changed_kept_fields"):
        value = record.get(key)
        if isinstance(value, list):
            safe[key] = [
                v
                for v in value
                if isinstance(v, str)
                and re.fullmatch(r"(?:IFD0|Exif|GPS|Interop)\.[A-Za-z0-9_]+", v)
            ]
    failures = record.get("failed_checks")
    if isinstance(failures, list):
        safe["failed_checks"] = [v for v in failures if isinstance(v, str) and v in _CHECKS]
    scores = record.get("scores_by_pose")
    if isinstance(scores, dict):
        safe["scores_by_pose"] = {
            str(i): scores[str(i)]
            for i in range(1, 9)
            if str(i) in scores and (scores[str(i)] is None or _number(scores[str(i)]))
        }
    shapes = record.get("shape_mismatches")
    if isinstance(shapes, list):
        safe["shape_mismatches"] = [v for v in shapes if type(v) is int and 1 <= v <= 8]
    witness = record.get("thumbnail_witness")
    if isinstance(witness, dict):
        safe["thumbnail_witness"] = {
            "available": witness.get("available") is True,
            **_safe_record({k: v for k, v in witness.items() if k != "thumbnail_witness"}),
        }
    intervals = record.get("sample_intervals_s")
    if isinstance(intervals, dict):
        safe["sample_intervals_s"] = {
            k: intervals[k]
            for k in ("rss", "device")
            if _number(intervals.get(k)) and intervals[k] > 0
        }
    errors = record.get("sampler_errors")
    if isinstance(errors, list):
        safe["sampler_errors"] = [
            v for v in errors if v in {"device_unavailable", "rss_unavailable"}
        ]
    return safe


def summarise(
    records: Sequence[Mapping[str, Any]],
    *,
    command: str,
    selected: int | None = None,
    selected_by_class: Mapping[str, int] | None = None,
) -> Record:
    """Project explicit safe fields and aggregate each inventory class separately.

    Args:
        records: Raw measured records; unexpected keys are discarded recursively.
        command: orientation, export or memory.
        selected: Requested input count, including not-yet-attempted inputs.
        selected_by_class: Requested counts by class when a run stops early.

    Returns:
        ASCII-serialisable summary without paths, EXIF values or pooled Z/M metrics.
    """
    if command not in {"orientation", "export", "memory"}:
        raise ValueError("invalid command")
    safe_records = [_safe_record(record) for record in records]
    classes: Record = {}
    for label in _CLASSES:
        group = [r for r in safe_records if r.get("class") == label]
        requested = len(group) if selected_by_class is None else selected_by_class.get(label, 0)
        if not group and not requested:
            continue
        row: Record = {
            "selected": requested,
            "attempted": len(group),
            "read_ok": sum(r.get("read_ok") is True for r in group),
            "read_failed": sum(r.get("read_ok") is not True for r in group),
            "assumed_count": sum(r.get("assumed") is True for r in group),
            "sanitise_drop_count": sum(r.get("sanitise_dropped") is True for r in group),
        }
        for field in ("orientation_ok", "v5_ok", "d53_ok", "v9_ok"):
            row[field + "_passed"] = sum(r.get(field) is True for r in group)
            row[field + "_failed"] = sum(r.get(field) is False for r in group)
        for field in ("quantised_max_255", "quantised_mean_255", "raw_max_255", "raw_mean_255"):
            values = [r[field] for r in group if _number(r.get(field))]
            if values:
                row[field + "_worst"] = max(values)
                row[field + "_photos"] = len(values)
        for field, keys in (
            ("layout_counts", ("grid", "irot", "imir", "auxiliary_count", "thumbnail_count")),
            ("colour_counts", ("primaries", "transfer", "assumed", "icc_present")),
        ):
            counts: Record = {}
            for record in group:
                key = json.dumps({k: record[k] for k in keys if k in record}, sort_keys=True)
                counts[key] = counts.get(key, 0) + 1
            row[field] = counts
        classes[label] = row
    wanted = len(records) if selected is None else selected
    return {
        "schema": 1,
        "command": command,
        "selected": wanted,
        "attempted": len(records),
        "complete": wanted == len(records)
        and all(r.get("read_ok") is True and not r.get("failed_checks") for r in safe_records),
        "classes": classes,
        "records": safe_records,
    }


def print_summary(summary: Mapping[str, Any]) -> None:
    """Print only a fresh safe projection, never arbitrary caller-provided keys.

    Args:
        summary: A measured summary. Records are projected again at this boundary.
    """
    classes = summary.get("classes", {})
    selected_by_class = (
        {
            label: row["selected"]
            for label, row in classes.items()
            if label in _CLASSES
            and isinstance(row, dict)
            and type(row.get("selected")) is int
            and row["selected"] >= 0
        }
        if isinstance(classes, dict)
        else None
    )
    clean = summarise(
        summary.get("records", []),
        command=summary["command"],
        selected=summary.get("selected"),
        selected_by_class=selected_by_class,
    )
    for key in ("disk_free_before_bytes", "disk_free_after_bytes", "exit_code"):
        if _number(summary.get(key)):
            clean[key] = summary[key]
    if clean.get("exit_code", 0) != 0:
        clean["complete"] = False
    print(json.dumps(clean, ensure_ascii=True, allow_nan=False))


class _UsageError(ValueError):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise _UsageError("invalid request")


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(description=__doc__.splitlines()[0] if __doc__ else "Photo verification")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("orientation", "export", "memory"):
        command = commands.add_parser(name)
        command.add_argument("--config", type=Path)
        command.add_argument("--class-map", type=Path, required=True)
        command.add_argument("--name", required=True)
        command.add_argument("--files", nargs="+")
        if name in {"export", "memory"}:
            command.add_argument(
                "--bit-depth", type=int, choices=(8, 16), default=16, required=name == "export"
            )
            command.add_argument("--force-cpu", action="store_true")
        if name == "export":
            command.add_argument("--representatives-only", action="store_true")
        if name == "memory":
            command.add_argument("--file")
            command.add_argument("--exclusive", action="store_true")
        if name == "orientation":
            command.add_argument("--max-side", type=int, default=256)
    return parser


def _selection(
    args: argparse.Namespace, mapping: Record, config: LocalConfig
) -> list[tuple[Path, str, bool]]:
    chosen: list[tuple[Path, str, bool]] = []
    requested = args.files or ([args.file] if args.command == "memory" and args.file else None)
    known = {file for group in mapping["classes"].values() for file in group["files"]}
    if requested and (len(set(requested)) != len(requested) or not set(requested) <= known):
        raise ValueError("unlisted input")
    phone = config.footage_path / "Phone"
    for label, group in mapping["classes"].items():
        if args.command == "orientation" and not label.startswith("HEIC"):
            continue
        for file in group["files"]:
            representative = file == group["representative"]
            if requested and file not in requested:
                continue
            if args.command == "export" and args.representatives_only and not representative:
                continue
            path = phone / _name(file)
            if not path.resolve().is_relative_to(phone.resolve()):
                raise ValueError("input escaped Phone")
            chosen.append((path, label, representative))
    if not chosen or (args.command == "memory" and len(chosen) != 1):
        raise ValueError("invalid selection size")
    return chosen


def main(argv: Sequence[str] | None = None) -> int:
    """Run the guarded instrument and print a safe summary on every normal exit.

    Args:
        argv: CLI arguments; defaults to sys.argv.

    Returns:
        0 for all checks passing, 1 for a photo/check failure, 2 for invalid input,
        or 3 for a disk/write-guard refusal. Raw errors are never printed.
    """
    command = "export"
    records: list[Record] = []
    summary_path: Path | None = None
    guard: WriteGuard | None = None
    selected: list[tuple[Path, str, bool]] = []
    before: int | None = None
    try:
        args = _parser().parse_args(argv)
        command = args.command
        config = load_local_config(args.config)
        guard = make_guard(config)
        before = _disk_check(guard.root)
        mapping = load_class_map(args.class_map)
        selected = _selection(args, mapping, config)
        if command == "memory" and not args.exclusive:
            raise ValueError("memory requires exclusive window")
        if command == "orientation" and not 1 <= args.max_side <= 4096:
            raise ValueError("invalid comparison bound")
        name = _name(args.name)
        folder = guard.root / command / name
        guard.check(folder)
        if folder.exists():
            raise ValueError("run exists")
        budget = 0
        for source, _, representative in selected:
            try:
                width, height = _dimensions(source)
            except (OSError, ValueError):
                continue  # record this failed input in the per-photo pass
            size = width * height * (3 if command == "orientation" else 6) + height + 65536
            if command != "export" or (representative and args.bit_depth == 16):
                budget += size
        _disk_check(guard.root, budget)
        folder = guard.folder(command, name)
        run_guard = WriteGuard(root=folder, footage=config.footage_path)
        summary_path = guard.check(folder / "summary.json")
        for source, label, representative in selected:
            try:
                if command == "orientation":
                    record = verify_orientation(
                        source, run_guard, photo_class=label, max_side=args.max_side
                    )
                elif command == "export":
                    record = verify_export(
                        source,
                        run_guard,
                        photo_class=label,
                        bit_depth=args.bit_depth,
                        force_cpu=args.force_cpu,
                        keep=representative and args.bit_depth == 16,
                    )
                else:
                    record = verify_memory(
                        source,
                        run_guard,
                        photo_class=label,
                        bit_depth=args.bit_depth,
                        force_cpu=args.force_cpu,
                        exclusive=args.exclusive,
                    )
            except OutputRefusedError:
                raise
            except Exception:
                record = _failure(source, label, "runner_failed", "runner_failed")
            records.append(record)
            if record.get("failed_checks") or not record.get("read_ok"):
                break
        status = (
            0
            if len(records) == len(selected)
            and all(not r.get("failed_checks") and r.get("read_ok") for r in records)
            else 1
        )
    except OutputRefusedError:
        status = 3
    except Exception:  # never expose local-config paths or tag values through CLI tracebacks
        status = 2
    counts = {label: sum(label == item[1] for item in selected) for label in _CLASSES}
    summary = summarise(records, command=command, selected=len(selected), selected_by_class=counts)
    summary["exit_code"] = status
    summary["complete"] = status == 0 and summary["complete"]
    if before is not None and guard is not None:
        summary["disk_free_before_bytes"] = before
        with contextlib.suppress(OSError):
            summary["disk_free_after_bytes"] = int(psutil.disk_usage(str(guard.root)).free)
    if summary_path is not None and guard is not None:
        try:
            _write_json(summary_path, summary, guard)
        except (OSError, OutputRefusedError):
            status = 3
            summary["exit_code"] = status
    print_summary(summary)
    return status


if __name__ == "__main__":
    sys.exit(main())
