"""Photo check: what Clearwater's photo reader makes of real photos (WP3.6 task 8; WP3.6P).

Given photo files or folders (default: the configured footage folder, read only), writes one
JSON record per photo under ``<working folder>/wp3.6/photo-check/<run>/`` with the format, the
stored and decoded size, the bit depth, the HEIC primary-item layout (``irot``, ``imir``, the
EXIF tag, grid or not, auxiliary images), the ICC description and classification, the EXIF
field names, the read verdict and a round trip (a 16-bit PNG written next to the records,
re-read, and compared in samples, ICC and the D63 fields). Nothing is written outside the working
folder and nothing is ever written beside, or into, the source or the footage folder.

Run: ``uv run python tools/photo_check.py [PATH ...] [--config FILE] [--name RUN]``.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import time
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

if not __package__:
    # Script mode: sys.path[0] is tools/; the sibling packages are importable as is.
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pillow_heif

from clearwater.interfaces.image import Image
from clearwater.interfaces.photo import PhotoMetadata
from clearwater.io.photo import PhotoReadError, read_photo, write_photo
from clearwater.io.photo import exif as exif_tools
from clearwater.io.photo import icc as icc_tools
from clearwater.io.photo.heif_boxes import HeifLayoutError, read_layout
from clearwater.io.photo.reader import detect_format, has_dng_tag
from clearwater.io.photo.writer import built_in_profile
from local_config import LocalConfig, load_local_config
from spike_io.guard import OutputRefusedError, WriteGuard

PHOTO_SUFFIXES = {".jpg", ".jpeg", ".heic", ".heif", ".png", ".tif", ".tiff", ".dng"}
"""The extensions walked when a folder is given."""

WORK_SUBDIR = "wp3.6"
"""The folder inside the working folder that every output of this tool goes to."""

D63_CHANGED = {"IFD0.Orientation", "IFD0.Software", "Exif.ExifImageWidth", "Exif.ExifImageHeight"}
"""The EXIF fields a D63 write may change."""


def collect(paths: Iterable[Path]) -> list[Path]:
    """List the photo files named by files and folders (folders walked, sorted).

    Args:
        paths: Files and folders.

    Returns:
        Files whose extension is in :data:`PHOTO_SUFFIXES`, plus every file named directly.
    """
    found: list[Path] = []
    for path in paths:
        if path.is_dir():
            found.extend(
                sorted(
                    p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in PHOTO_SUFFIXES
                )
            )
        else:
            found.append(path)
    return found


def _heic_layout(data: bytes) -> dict[str, Any]:
    """Describe the primary item of a HEIC: layout from the boxes and the raw EXIF tag."""
    record: dict[str, Any] = {}
    try:
        layout = read_layout(data)
        record.update(
            primary_item=layout.primary_id,
            item_type=layout.item_type,
            grid=layout.is_grid,
            irot=layout.irot,
            imir=layout.imir,
            clap=layout.clap,
            ispe=layout.ispe,
            auxiliary_images=bool(layout.auxiliary_ids),
            auxiliary_ids=list(layout.auxiliary_ids),
            thumbnail_ids=list(layout.thumbnail_ids),
        )
    except HeifLayoutError as error:
        record["layout_error"] = str(error)
    try:
        heif = pillow_heif.open_heif(io.BytesIO(data), convert_hdr_to_8bit=False)
        raw = heif.info.get("exif")
        record["exif_orientation"] = exif_tools.orientation_of(
            exif_tools.strip_prefix(raw) if isinstance(raw, bytes) else None
        )
        record["nclx_profile"] = heif.info.get("nclx_profile")
        record["heif_bit_depth"] = heif.info.get("bit_depth")
        record["heif_thumbnails"] = len(heif.info.get("thumbnails", []))
        record["heif_depth_images"] = len(heif.info.get("depth_images", []))
    except Exception as error:  # a record of what the library said, never a crash
        record["pillow_heif_error"] = f"{type(error).__name__}: {error}"
    return record


def _color_record(image: Image) -> dict[str, Any]:
    icc = image.color.icc_profile
    record: dict[str, Any] = {
        "primaries": image.color.primaries,
        "transfer": image.color.transfer,
        "assumed": image.color.assumed,
        "bit_depth": image.color.bit_depth,
        "icc_present": icc is not None,
    }
    if icc is not None:
        record.update(
            icc_description=icc_tools.description(icc),
            icc_bytes=len(icc),
            icc_md5=hashlib.md5(icc).hexdigest(),
            icc_valid=icc_tools.is_valid_profile(icc),
        )
    return record


def round_trip(image: Image, meta: PhotoMetadata, out_png: Path) -> dict[str, Any]:
    """Write a 16-bit PNG, re-read it, and compare samples, ICC and the D63 fields.

    Args:
        image: The image read from the source.
        meta: Its metadata.
        out_png: Where to write the PNG (the caller has checked the path).

    Returns:
        A record with ``problems`` (empty when everything holds) and the figures measured.
    """
    write_photo(image, meta, out_png, bit_depth=16, provenance={"photo_check": True})
    again, again_meta = read_photo(out_png)
    problems: list[str] = []
    diff = np.abs(again.pixels.astype(np.float64) - image.pixels.astype(np.float64))
    exact = image.color.bit_depth in (8, 16)
    limit = 0.0 if exact else 0.5 / 65535 + 1e-7
    if diff.max() > limit:
        problems.append(f"samples differ by up to {diff.max():.3g} (allowed {limit:.3g})")
    chosen = built_in_profile(image.color)
    expected_icc = image.color.icc_profile if chosen is None else chosen[1]
    if again.color.icc_profile != expected_icc:
        problems.append("ICC profile bytes changed")
    if (again.color.primaries, again.color.transfer) != (
        image.color.primaries,
        image.color.transfer,
    ):
        problems.append("primaries or transfer changed")
    before, after = exif_tools.describe(meta.exif), exif_tools.describe(again_meta.exif)
    height, width = image.pixels.shape[:2]
    if after.get("IFD0.Orientation") != "1":
        problems.append("Orientation is not 1")
    if after.get("IFD0.Software") != exif_tools.SOFTWARE:
        problems.append("Software is not Clearwater")
    if (after.get("Exif.ExifImageWidth"), after.get("Exif.ExifImageHeight")) != (
        str(width),
        str(height),
    ):
        problems.append("pixel dimensions not updated")
    if again_meta.exif is not None and exif_tools.has_thumbnail(again_meta.exif):
        problems.append("thumbnail kept")
    lost = sorted(k for k in before if k not in D63_CHANGED and after.get(k) != before[k])
    if lost:
        problems.append(f"fields changed or lost: {lost}")
    return {
        "png": out_png.name,
        "max_abs_sample_difference": float(diff.max()),
        "exif_fields_before": len(before),
        "exif_fields_after": len(after),
        "maker_note_kept": ("Exif.MakerNote" in before) == ("Exif.MakerNote" in after),
        "gps_kept": all(k in after for k in before if k.startswith("GPS.")),
        "problems": problems,
    }


def inspect(path: Path, out_png: Path) -> dict[str, Any]:
    """Build the record of one photo (never raises for a bad photo).

    Args:
        path: The photo; opened read only.
        out_png: Where its round-trip PNG goes (checked by the caller).

    Returns:
        The JSON-ready record.
    """
    record: dict[str, Any] = {"file": path.name, "path": str(path)}
    try:
        data = path.read_bytes()
    except OSError as error:
        record["verdict"] = {"ok": False, "kind": "unreadable", "message": str(error)}
        return record
    record["bytes"] = len(data)
    record["detected_format"] = detect_format(data)
    record["dng"] = path.suffix.lower() == ".dng" or has_dng_tag(data)
    if record["detected_format"] == "heic":
        record["heic"] = _heic_layout(data)
    try:
        image, meta = read_photo(path)
    except PhotoReadError as error:
        record["verdict"] = {"ok": False, "kind": error.kind, "message": str(error)}
        return record
    height, width = image.pixels.shape[:2]
    stored = record.get("heic", {}).get("ispe")
    record.update(
        verdict={"ok": True},
        decoded_size=[width, height],
        stored_size=list(stored) if stored else None,
        source_format=meta.source_format,
        orientation_tag=meta.orientation,
        color=_color_record(image),
        exif_fields=sorted(exif_tools.describe(meta.exif)),
    )
    try:
        record["round_trip"] = round_trip(image, meta, out_png)
    except Exception as error:  # the record says what failed
        record["round_trip"] = {"problems": [f"{type(error).__name__}: {error}"]}
    return record


def make_guard(config: LocalConfig) -> WriteGuard:
    """Return the write guard of this tool: root ``<working folder>/wp3.6``, created.

    Args:
        config: The local configuration.

    Returns:
        The guard; every write is checked against it first.
    """
    root = Path(config.working_path).resolve() / WORK_SUBDIR
    guard = WriteGuard(root=root, footage=config.footage_path)
    guard.check(root)
    root.mkdir(parents=True, exist_ok=True)
    return guard


def run(
    photos: Sequence[Path], guard: WriteGuard, name: str | None = None
) -> tuple[Path, list[dict[str, Any]]]:
    """Inspect every photo and write the records and a summary.

    Args:
        photos: The photo files.
        guard: The write guard (:func:`make_guard`).
        name: The run's folder name (default: a time stamp).

    Returns:
        The run folder and the records.
    """
    run_name = name or time.strftime("%Y%m%d-%H%M%S")
    out = guard.folder("photo-check", run_name)
    records = []
    for index, photo in enumerate(photos):
        stem = f"{index:04d}-{photo.stem}"
        png = guard.check(out / f"{stem}.png")
        record = inspect(photo, png)
        guard.check(out / f"{stem}.json").write_text(
            json.dumps(record, indent=1, default=str) + "\n", encoding="utf-8"
        )
        records.append(record)
    summary = {
        "photos": len(records),
        "read_ok": sum(1 for r in records if r["verdict"]["ok"]),
        "refused": [
            {"file": r["file"], **{k: r["verdict"][k] for k in ("kind", "message")}}
            for r in records
            if not r["verdict"]["ok"]
        ],
        "round_trip_problems": {
            r["file"]: r["round_trip"]["problems"]
            for r in records
            if r.get("round_trip", {}).get("problems")
        },
    }
    guard.check(out / "summary.json").write_text(
        json.dumps(summary, indent=1) + "\n", encoding="utf-8"
    )
    return out, records


def main(argv: Sequence[str] | None = None) -> int:
    """Command line entry point; see the module docstring.

    Args:
        argv: Arguments (default: ``sys.argv``).

    Returns:
        0 when every readable photo round-trips cleanly, 1 when any problem is recorded,
        2 when no photo was found.
    """
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("paths", nargs="*", type=Path, help="photo files or folders")
    parser.add_argument("--config", type=Path, default=None, help="local configuration file")
    parser.add_argument("--name", default=None, help="run folder name")
    arguments = parser.parse_args(argv)
    config = load_local_config(arguments.config)
    guard = make_guard(config)
    roots = arguments.paths or [config.footage_path]
    photos = collect(roots)
    if not photos:
        print("no photos found in: " + ", ".join(str(r) for r in roots))
        return 2
    try:
        out, records = run(photos, guard, arguments.name)
    except OutputRefusedError as error:
        print(error)
        return 3
    print(out)
    failed = [r["file"] for r in records if r.get("round_trip", {}).get("problems")]
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
