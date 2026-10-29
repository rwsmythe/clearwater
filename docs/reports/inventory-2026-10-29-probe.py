"""Read selected Phone photo headers, video stream facts and as-written video edits.

Evidence for the 2026-10-29 inventory, not a product tool. Reads the configured
footage tree read-only, selecting Make, Model, Software, orientation, ColorSpace,
ICC description, primary HEIF properties, video colour/codec/timing facts,
encoder tags and video composition-offset tables. Never traverses private EXIF
sub-IFDs, camera notes, serial tags,
geographic tags or telemetry payloads; never decodes photo pixels or video frames.
Opaque header buffers may contain other metadata, which is neither interpreted
nor emitted. Only the selected facts are written, under this worktree's work/.

Run from the repository root with uv run python and this script's relative path.
"""

from __future__ import annotations

import json
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any

import pillow_heif
from PIL import Image

from clearwater.io.video import boxes

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import inventory  # noqa: E402 - reuse the frozen inventory's header-only helpers
from local_config import load_local_config  # noqa: E402

OUTPUT = ROOT / "work/inventory-1029/phone-probe.json"
TAGS = (
    "make,model,software,encoder,"
    "com.apple.quicktime.make,com.apple.quicktime.model,com.apple.quicktime.software"
)
ENTRIES = (
    "format=format_name:format_tags=major_brand,compatible_brands,"
    + TAGS
    + ":stream=index,codec_type,codec_name,codec_tag_string,width,height,pix_fmt,"
    "bits_per_raw_sample,r_frame_rate,avg_frame_rate,has_b_frames,"
    "color_primaries,color_transfer,color_space,color_range:stream_tags="
    + TAGS
    + ":stream_side_data=side_data_type,rotation,dv_version_major,dv_version_minor,"
    "dv_profile,dv_level,rpu_present_flag,el_present_flag,bl_present_flag,"
    "dv_bl_signal_compatibility_id"
)


def _payload(path: Path, wanted: bytes) -> bytes:
    """Read one bounded top-level header box, seeking over every other box."""
    with path.open("rb") as handle:
        total = path.stat().st_size
        position = 0
        while position + 8 <= total:
            handle.seek(position)
            size, kind = struct.unpack(">I4s", handle.read(8))
            header = 8
            if size == 1:
                (size,) = struct.unpack(">Q", handle.read(8))
                header = 16
            elif size == 0:
                size = total - position
            if size < header or position + size > total:
                raise ValueError("invalid top-level box size")
            if kind == wanted:
                if size - header > boxes.MAX_MOOV_BYTES:
                    raise ValueError("header exceeds supported bound")
                return handle.read(size - header)
            position += size
    raise ValueError("required header box absent")


def _photo(path: Path) -> dict[str, Any]:
    """Select permitted photo tags without loading pixel data."""
    with Image.open(path) as image:
        exif = image.getexif()
        orientation = image.info.get("original_orientation")
        if orientation is None:
            # The HEIF Pillow plugin can normalize/remove orientation in its EXIF
            # copy. Read the original bytes when its saved value is absent/None.
            raw_bytes = (
                pillow_heif.open_heif(path).info.get("exif")
                if image.format == "HEIF"
                else image.info.get("exif")
            )
            raw_exif = Image.Exif()
            if raw_bytes:
                raw_exif.load(raw_bytes)
            orientation = raw_exif.get(274)
        record = {
            "kind": "photo",
            "container": image.format,
            "codec": "JPEG",
            "width": image.width,
            "height": image.height,
            "bit_depth": inventory._photo_bit_depth(image, path),
            "icc_description": inventory._icc_description(image.info.get("icc_profile")),
            "exif_orientation": orientation,
            "Make": exif.get(271),
            "Model": exif.get(272),
            "Software": exif.get(305),
            "ColorSpace": exif.get_ifd(34665).get(40961),
            "irot_ccw_degrees": None,
            "nclx": None,
        }
        # Only the ColorSpace scalar is selected from the standard Exif IFD.
        # Neither its nested private IFDs nor any other tag value is accessed.
        if image.format == "HEIF":
            brand = _payload(path, b"ftyp")
            record["major_brand"] = brand[:4].decode("ascii")
            brands = [brand[i : i + 4] for i in range(8, len(brand), 4)]
            if any(b in {b"heic", b"heix", b"hevc", b"hevx"} for b in [*brands, brand[:4]]):
                record["codec"] = "HEVC"
            else:
                record["codec"] = "unidentified HEIF codec"
            meta = inventory._heif_meta_payload(path)
            for kind, start in inventory._primary_item_properties(meta):
                if kind == b"ispe":
                    record["width"], record["height"] = struct.unpack_from(">II", meta, start + 4)
                elif kind == b"irot":
                    record["irot_ccw_degrees"] = (meta[start] & 3) * 90
                elif kind == b"colr" and meta[start : start + 4] == b"nclx":
                    primaries, transfer, matrix = struct.unpack_from(">HHH", meta, start + 4)
                    record["nclx"] = {
                        "primaries": primaries,
                        "transfer": transfer,
                        "matrix": matrix,
                        "full_range": bool(meta[start + 10] & 128),
                    }
        return record


def _composition_offsets(data: bytes, mdia: tuple[int, int]) -> dict[str, Any]:
    """Summarize only the first video track's ctts entries, without media reads."""
    minf = boxes._find(data, *mdia, "minf")
    stbl = boxes._find(data, *minf, "stbl") if minf else None
    ctts = boxes._find(data, *stbl, "ctts") if stbl else None
    if ctts is None:
        return {
            "present": False,
            "version": None,
            "entry_count": 0,
            "negative_entries_by_version": False,
            "negative_signed32_offsets": False,
        }
    start, end = ctts
    if end - start < 8 or data[start] not in (0, 1):
        raise ValueError("invalid ctts header")
    version = data[start]
    (count,) = struct.unpack_from(">I", data, start + 4)
    if count * 8 > end - start - 8:
        raise ValueError("ctts entries exceed box bounds")
    form = ">Ii" if version == 1 else ">II"
    entries = [struct.unpack_from(form, data, start + 8 + i * 8) for i in range(count)]
    offsets = [offset for _samples, offset in entries]
    # Preserve version-defined values, plus the signed-32 interpretation ffprobe
    # uses for these QuickTime files even when their ctts version byte is zero.
    signed32 = [offset - 2**32 if offset >= 2**31 else offset for offset in offsets]
    return {
        "present": True,
        "version": version,
        "entry_count": count,
        "sample_count": sum(samples for samples, _offset in entries),
        "min_offset": min(offsets) if offsets else None,
        "max_offset": max(offsets) if offsets else None,
        "negative_entries_by_version": any(offset < 0 for offset in offsets),
        "signed32_min_offset": min(signed32) if signed32 else None,
        "signed32_max_offset": max(signed32) if signed32 else None,
        "negative_signed32_offsets": any(offset < 0 for offset in signed32),
    }


def _video_edits(path: Path) -> dict[str, Any]:
    """Select the first video track's raw edit entries using the product parsers."""
    moov = _payload(path, b"moov")
    movie = boxes._find(moov, 0, len(moov), "mvhd")
    movie_scale = boxes._timescale(moov, movie) if movie else None
    for kind, start, end in boxes._children(moov, 0, len(moov)):
        if kind != "trak":
            continue
        mdia = boxes._find(moov, start, end, "mdia")
        if mdia is None or boxes._handler(moov, mdia) != "vide":
            continue
        mdhd = boxes._find(moov, *mdia, "mdhd")
        edts = boxes._find(moov, start, end, "edts")
        elst = boxes._find(moov, *edts, "elst") if edts else None
        edits = boxes._edits(moov, elst) if elst else ()
        return {
            "movie_timescale": movie_scale,
            "video_timescale": boxes._timescale(moov, mdhd) if mdhd else None,
            "elst_version": moov[elst[0]] if elst else None,
            "segment_count": len(edits),
            "composition_offsets": _composition_offsets(moov, mdia),
            "segments": [
                {
                    "segment_duration": e.segment_duration,
                    "media_time": e.media_time,
                    "media_rate": str(e.media_rate),
                }
                for e in edits
            ],
        }
    raise ValueError("no video track")


def _video(path: Path) -> dict[str, Any]:
    """Request only permitted ffprobe fields and add the raw video edit list."""
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        ENTRIES,
        "-of",
        "json",
        str(path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=60)
    # stderr is never copied into the evidence: it can contain unselected metadata.
    data = json.loads(result.stdout)
    return {"kind": "video", **data, "video_edit_list": _video_edits(path)}


def main() -> None:
    """Probe Phone files and write deterministic selected evidence inside work/.

    Raises:
        ValueError: If an output would leave work/ or enter the source tree.
        OSError: If a header cannot be read or the output cannot be written.
        subprocess.SubprocessError: If ffprobe cannot complete successfully.
    """
    source = load_local_config().footage_path.resolve()
    target = OUTPUT.resolve()
    if not target.is_relative_to(ROOT / "work") or target.is_relative_to(source):
        raise ValueError("output must stay inside work/ and outside the source tree")
    pillow_heif.register_heif_opener()
    records = []
    for path in sorted((source / "Phone").iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() in inventory.PHOTO_EXTENSIONS:
            record = _photo(path)
        elif path.suffix.lower() in inventory.VIDEO_EXTENSIONS:
            record = _video(path)
        else:
            raise ValueError("unhandled Phone file extension")
        records.append({"path": path.relative_to(source).as_posix(), **record})
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(records, indent=2, ensure_ascii=True) + "\n", encoding="ascii", newline="\n"
    )
    print(f"Selected headers: {len(records)}; output: {target.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
