"""Build CP5 evidence through the shipped headless runner, with no agent judgement."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from typing import Any

if __package__ in {None, "", "tools.reviewpack"}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    __package__ = "reviewpack"

from PIL import Image, ImageCms

from local_config import LocalConfigError, find_footage_file, load_local_config
from lookcheck.frames import (
    ExtractError,
    OutputPathError,
    OutputRoots,
    colour_filter,
    extract,
    strip_ancillary_chunks,
    tags_from_stream,
)
from lookcheck.frames import run_tool as run_tool

from . import page, select, sheet


def _safe_text(value: object, roots: OutputRoots) -> str:
    text = str(value)
    # Diagnostics are kept name-only even when an external tool quotes a path.
    for root in (roots.footage, roots.allowed, Path(__file__).resolve().parents[2]):
        for spelling in (str(root), root.as_posix(), str(root).replace("\\", "\\\\")):
            text = re.sub(re.escape(spelling), "", text, flags=re.IGNORECASE)
    text = re.sub(r"(?:[A-Za-z]:[\\/]|\\\\)[^\s\"'<>]+", "[path]", text)
    text = re.sub(r"(?<![\w])/(?:[^\s/\"'<>]+/)+([^\s/\"'<>]+)", r"\1", text)
    return (
        "\n".join(
            "[metadata diagnostic withheld]" if re.search(r"\b(?:GPS|EXIF)\b", line, re.I) else line
            for line in text.splitlines()
        )
        .encode("ascii", "backslashreplace")
        .decode("ascii")
    )


def _json_write(path: Path, value: object, roots: OutputRoots) -> None:
    roots.check(path)
    temporary = path.with_name(f".{path.name}-{uuid.uuid4().hex}.tmp")
    try:
        roots.write_text(
            temporary, json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + "\n"
        )
        roots.rename(temporary, path)
    finally:
        if temporary.exists():
            roots.remove(temporary)


def _bare(value: object) -> str:
    name = str(value)
    if not name or name in {".", ".."} or any(c in name for c in ("/", "\\", ":", "\0")):
        raise ValueError("expected a bare file name")
    return name


def _fresh(path: Path, roots: OutputRoots) -> Path:
    check_target(path, roots)
    counter = 2
    target = path
    while target.exists():
        target = path.with_name(f"{path.stem}-{counter}{path.suffix}")
        check_target(target, roots)
        counter += 1
    return target


def _probe(source: Path, *options: str) -> dict[str, Any]:
    done = run_tool(["ffprobe", "-v", "error", *options, "-of", "json", str(source)])
    if done.returncode:
        raise ValueError(f"ffprobe failed for {source.name}")
    value = json.loads(done.stdout)
    if not isinstance(value, dict):
        raise ValueError("ffprobe returned a non-object")
    return value


def _video(source: Path) -> dict[str, Any]:
    document = _probe(
        source,
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,pix_fmt,time_base,avg_frame_rate,duration,color_range,"
        "color_space,color_transfer,color_primaries:stream_side_data=rotation:format=duration",
    )
    streams = document.get("streams", [])
    if not streams:
        raise ValueError(f"no video stream in {source.name}")
    stream: dict[str, Any] = streams[0]
    duration = stream.get("duration", document.get("format", {}).get("duration"))
    stream["duration_s"] = float(duration)
    if not math.isfinite(stream["duration_s"]) or stream["duration_s"] <= 0:
        raise ValueError("invalid video duration")
    return stream


def _rotated(stream: Mapping[str, Any]) -> bool:
    return any(float(side.get("rotation", 0)) % 360 for side in stream.get("side_data_list", []))


def _frame_time(source: Path, wanted: float) -> Fraction:
    frames = _probe(
        source,
        "-select_streams",
        "v:0",
        "-read_intervals",
        f"{max(0, wanted - 1):.9f}%{wanted + 2:.9f}",
        "-show_frames",
        "-show_entries",
        "frame=best_effort_timestamp:stream=time_base",
    ).get("frames", [])
    time_base = Fraction(_video(source)["time_base"])
    pts = sorted(
        int(frame["best_effort_timestamp"]) * time_base
        for frame in frames
        if "best_effort_timestamp" in frame
    )
    first = next((pts for pts in pts if float(pts) + 1e-7 >= wanted), None)
    if first is None:
        raise ValueError(f"no frame at requested timestamp in {source.name}")
    return first


def check_target(path: Path, roots: OutputRoots) -> Path:
    """Refuse a pack target outside its allowed root or within footage.

    Args:
        path: Target about to be written.
        roots: Allowed and footage roots.

    Returns:
        The safe resolved path.
    """
    try:
        return roots.check(path)
    except OutputPathError as exc:
        raise ValueError("output is outside the pack or within footage, or is shared") from exc


def runner_arguments(
    sources: Sequence[Path],
    *,
    group: str,
    roots: OutputRoots,
    neutral: bool = False,
    force_cpu: bool = False,
) -> list[str]:
    """Build a headless-export CLI invocation for a group and pose.

    Args:
        sources: Original or stream-copied inputs.
        group: Commissioned group.
        roots: Pack and source roots.
        neutral: Use the photo source-view pose.
        force_cpu: Explicit CPU override, used by the tiny integration test.

    Returns:
        The subprocess argument vector without shell quoting.
    """
    if group not in select.GROUPS:
        raise ValueError("unknown group")
    photo = group.startswith("P-")
    if neutral and not photo:
        raise ValueError("neutral source view applies only to photos")
    folder = check_target(roots.allowed / ("photos" if photo else "clips"), roots)
    settings = check_target(roots.allowed / "settings", roots)
    check_target(settings / "settings.json", roots)
    record = _fresh(
        roots.allowed / "records" / f"{group}{'-neutral' if neutral else ''}.json", roots
    )
    args = [
        "uv",
        "run",
        "python",
        "tools/headless_export.py",
        *(str(p) for p in sources),
        "--out",
        str(folder),
        "--suffix",
        "_neutral" if neutral else "_corrected",
        "--settings-dir",
        str(settings),
        "--record",
        str(record),
    ]
    if photo:
        args += ["--bit-depth", "8"]
    else:
        args += ["--cache-dir", str(check_target(roots.allowed / "cache", roots))]
    if neutral:
        args += ["--neutral"]
    if force_cpu:
        args += ["--force-cpu"]
    return args


def read_runner_record(path: Path, *, group: str, roots: OutputRoots) -> list[dict[str, Any]]:
    """Map runner facts into pack items without guessing numbered output names.

    Args:
        path: Existing runner JSON record.
        group: Group this invocation belongs to.
        roots: Pack and source roots.

    Returns:
        Name-only item results, including failed items.
    """
    check_target(path, roots)
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("schema") != 1 or record.get("tool") != "headless_export":
        raise ValueError("unrecognized runner record")
    result = []
    for raw in record["items"]:
        source = _bare(raw["source"])
        kind = "photo" if group.startswith("P-") else "video"
        outputs = [_bare(name) for name in raw["outputs"]]
        suffix = ".png" if kind == "photo" else ".mp4"
        primary = [name for name in outputs if Path(name).suffix.lower() == suffix]
        done = raw["state"] in {"done", "done with warnings"}
        message = _safe_text(raw.get("failure") or "", roots)
        if done:
            if len(primary) != 1:
                raise ValueError("completed runner item has no unique product output")
            folder = "photos" if kind == "photo" else "clips"
            target = check_target(roots.allowed / folder / primary[0], roots)
            if not target.is_file():
                raise ValueError("runner output named in record is missing")
        result.append(
            {
                "item": Path(source).stem,
                "group": group,
                "kind": kind,
                "source_name": source,
                "corrected_name": primary[0] if done else "",
                "source_view_name": "",
                "status": "done"
                if done
                else ("refused" if group == "V-R" and "hlg" in message.lower() else "failed"),
                "message": message,
                "warnings": [_safe_text(v, roots) for v in raw["warnings"]],
                "device": _safe_text(raw.get("device") or "", roots),
                "video": (
                    {
                        key: raw["video"].get(key)
                        for key in ("device_backend", "frame_device", "encoder", "decode_passes")
                    }
                    if isinstance(raw.get("video"), dict)
                    else None
                ),
                "elapsed_s": raw.get("elapsed_s"),
                "record_name": path.name,
                "source_thumb": "",
                "corrected_thumb": "",
                "pair_name": "",
                "stills": [],
            }
        )
    return result


def stream_copy_command(
    source: Path, destination: Path, *, start_s: float, duration_s: float
) -> list[str]:
    """Build the all-stream, input-seek excerpt command.

    Args:
        source: Read-only input.
        destination: Guarded excerpt target.
        start_s: Requested source start.
        duration_s: Requested excerpt length.

    Returns:
        FFmpeg subprocess arguments.
    """
    return [
        "ffmpeg",
        "-nostdin",
        "-hide_banner",
        "-v",
        "error",
        "-n",
        "-ss",
        str(start_s),
        "-i",
        str(source),
        "-t",
        str(duration_s),
        "-map",
        "0",
        "-c",
        "copy",
        str(destination),
    ]


def validate_stream_copy(
    source_streams: Sequence[Mapping[str, Any]], excerpt_streams: Sequence[Mapping[str, Any]]
) -> None:
    """Reject stream-count or codec-tag changes in an excerpt.

    Args:
        source_streams: Selected source stream facts.
        excerpt_streams: Selected excerpt stream facts.
    """
    keys = ("codec_type", "codec_name", "codec_tag_string")
    if len(source_streams) != len(excerpt_streams) or any(
        tuple(a.get(k) for k in keys) != tuple(b.get(k) for k in keys)
        for a, b in zip(source_streams, excerpt_streams, strict=True)
    ):
        raise ValueError("stream copy changed stream count or codec tags")


def actual_excerpt_start(
    source_packets: Sequence[Mapping[str, Any]], excerpt_packets: Sequence[Mapping[str, Any]]
) -> float:
    """Match the retained first video packet back to its source timestamp.

    Args:
        source_packets: Source packet timestamps and data hashes.
        excerpt_packets: Retained excerpt packets, possibly rebased to zero.

    Returns:
        Actual retained source start in seconds.
    """
    retained = next((p for p in excerpt_packets if p.get("codec_type") == "video"), None)
    if retained is None or not retained.get("data_hash"):
        raise ValueError("excerpt has no first video packet hash")
    matches = [
        p
        for p in source_packets
        if p.get("codec_type") == "video" and p.get("data_hash") == retained["data_hash"]
    ]
    if len(matches) != 1:
        raise ValueError("first retained video packet has no unique source match")
    value = float(matches[0]["pts_time"])
    if not math.isfinite(value):
        raise ValueError("invalid retained packet timestamp")
    return value


def prepare_excerpt(
    source: Path, *, start_s: float, duration_s: float, roots: OutputRoots
) -> dict[str, Any]:
    """Copy and validate an excerpt, falling back to the whole input on copy failure.

    Args:
        source: Read-only input.
        start_s: Planned start.
        duration_s: Planned duration.
        roots: Pack and source roots.

    Returns:
        Runtime input path, excerpt status, measured timings and any fallback text.
    """
    destination = _fresh(roots.allowed / "excerpts" / source.name, roots)
    roots.mkdir(destination.parent)
    done = run_tool(
        stream_copy_command(source, destination, start_s=start_s, duration_s=duration_s)
    )
    if done.returncode:
        if destination.exists():
            roots.check(destination).unlink()
        return {
            "path": source,
            "excerpt": False,
            "planned_start_s": start_s,
            "actual_start_s": 0.0,
            "planned_duration_s": duration_s,
            "duration_s": _video(source)["duration_s"],
            "message": "stream copy failed; whole source used",
        }
    options = ("-show_entries", "stream=codec_type,codec_name,codec_tag_string")
    before = _probe(source, *options)["streams"]
    after = _probe(destination, *options)["streams"]
    validate_stream_copy(before, after)
    packet_options = (
        "-select_streams",
        "v:0",
        "-show_packets",
        "-show_data_hash",
        "sha256",
        "-show_entries",
        "packet=codec_type,pts_time,data_hash",
    )
    retained = _probe(destination, "-read_intervals", "%+#1", *packet_options)["packets"]
    # Seek covers keyframe pre-roll without scanning/hashing the full owner clip.
    packets = _probe(
        source, "-read_intervals", f"{max(0, start_s - 30)}%{start_s + 30}", *packet_options
    )["packets"]
    actual = actual_excerpt_start(packets, retained)
    return {
        "path": destination,
        "excerpt": True,
        "planned_start_s": start_s,
        "actual_start_s": actual,
        "planned_duration_s": duration_s,
        "duration_s": _video(destination)["duration_s"],
        "message": "",
    }


def extract_view_frame(
    source: Path, timestamp_s: float, destination: Path, *, roots: OutputRoots
) -> Path:
    """Decode a viewing frame using FFmpeg's default display autorotation.

    Args:
        source: Video input.
        timestamp_s: Required presentation time.
        destination: Guarded PNG target.
        roots: Pack and source roots.

    Returns:
        The oriented PNG path.
    """
    target = check_target(destination, roots)
    roots.mkdir(target.parent)
    stream = _video(source)
    if not _rotated(stream):
        # The shared helper independently checks the decoded PTS and conversion tags.
        extracted = extract(
            source, [timestamp_s], target.parent / (".frames-" + uuid.uuid4().hex), roots=roots
        )[0]
        roots.write_bytes(target, extracted.path.read_bytes())
        roots.check(extracted.path).unlink()
        return destination
    pts = _frame_time(source, timestamp_s)
    tags = tags_from_stream(stream)
    done = run_tool(
        [
            "ffmpeg",
            "-nostdin",
            "-hide_banner",
            "-y",
            "-copyts",
            "-ss",
            f"{max(0, float(pts) - 1):.9f}",
            "-i",
            str(source),
            "-map",
            "0:v:0",
            "-an",
            "-sn",
            "-dn",
            "-vf",
            f"select='gte(t,{float(pts) - 1e-7:.9f})',showinfo,{colour_filter(tags)}",
            "-frames:v",
            "1",
            "-fps_mode",
            "passthrough",
            str(target),
        ]
    )
    stderr = done.stderr.decode("utf-8", "replace")
    ticks = re.findall(r"\bpts:\s*(-?\d+)", stderr)
    time_bases = re.findall(r"config in time_base:\s*([0-9/]+)", stderr)
    if (
        done.returncode
        or not ticks
        or not time_bases
        or int(ticks[0]) * Fraction(time_bases[0]) != pts
    ):
        raise ValueError("oriented extraction failed or decoded a different timestamp")
    roots.write_bytes(target, strip_ancillary_chunks(target.read_bytes()))
    return destination


def make_pair(
    source: Path,
    corrected: Path,
    destination: Path,
    *,
    roots: OutputRoots,
    force_cpu: bool = False,
) -> dict[str, Any]:
    """Render equal-display-size inputs as a side-by-side viewing-aid video.

    Args:
        source: Original video or stream-copied excerpt.
        corrected: Product output, read without modification.
        destination: Guarded pair-video target.
        roots: Pack and source roots.
        force_cpu: Use software encoding for the tiny fixture control.

    Returns:
        Oriented source, corrected and rendered pair dimensions.
    """
    target = check_target(destination, roots)
    roots.mkdir(target.parent)
    source_stream = _video(source)
    sizes = []
    # Decode with each input's default autorotate: actual display dimensions, not a
    # handwritten interpretation of its matrix, determine whether hstack is safe.
    for index, video in enumerate((source, corrected)):
        frame = roots.allowed / "pairs" / f".size-{uuid.uuid4().hex}-{index}.png"
        extract_view_frame(video, 0.0, frame, roots=roots)
        with Image.open(frame) as image:
            sizes.append(image.size)
        roots.check(frame).unlink()
    if sizes[0] != sizes[1]:
        raise ValueError("source and corrected display dimensions differ")
    width, height = sizes[0]
    half_w, half_h = max(2, (width // 2) // 2 * 2), max(2, (height // 2) // 2 * 2)
    tags = tags_from_stream(source_stream)
    # Normalize SAR and start time in both halves. Keep the source's colour tags
    # and frame rate; audio and metadata belong only to the product item of record.
    scale = (
        f"scale={half_w}:{half_h}:in_range={tags.color_range}"
        f":out_range={tags.color_range}:in_color_matrix={tags.color_space}"
        f":out_color_matrix={tags.color_space},setsar=1,setpts=PTS-STARTPTS"
    )
    filters = (
        f"[0:v:0]{scale},pad=iw+2:ih:0:0:white[left];"
        f"[1:v:0]{scale}[right];[left][right]hstack=inputs=2:shortest=1[out]"
    )
    args = [
        "ffmpeg",
        "-nostdin",
        "-hide_banner",
        "-v",
        "error",
        "-y",
        "-i",
        str(source),
        "-i",
        str(corrected),
        "-filter_complex",
        filters,
        "-map",
        "[out]",
        "-an",
        "-sn",
        "-dn",
        "-map_metadata",
        "-1",
        "-c:v",
        "libx265" if force_cpu else "hevc_nvenc",
        "-pix_fmt",
        "yuv420p",
        "-r",
        str(source_stream["avg_frame_rate"]),
        "-color_range",
        tags.color_range,
        "-colorspace",
        tags.color_space,
    ]
    for flag, value in (
        ("-color_trc", tags.color_transfer),
        ("-color_primaries", tags.color_primaries),
    ):
        if value != "unknown":
            args += [flag, value]
    if force_cpu:
        args += ["-preset", "ultrafast", "-x265-params", "log-level=error:pools=1"]
    args += ["-tag:v", "hvc1", "-movflags", "+faststart", str(target)]
    done = run_tool(args, timeout=24 * 3600)
    if done.returncode:
        raise ValueError("pair viewing-aid encode failed")
    result = _video(target)
    pair_size = (int(result["width"]), int(result["height"]))
    if pair_size != (half_w * 2 + 2, half_h):
        raise ValueError("pair encode dimensions differ from planned display dimensions")
    return {"source_size": sizes[0], "corrected_size": sizes[1], "pair_size": pair_size}


def export_presets(*, roots: OutputRoots) -> dict[str, dict[str, Any]]:
    """Export both product starter presets through a pack-local preset store.

    Args:
        roots: Pack and source roots.

    Returns:
        Preset name to the product-exported AD-13 object.
    """
    from clearwater.config import PresetStore
    from clearwater.config.presets import STARTER_SCUBA, STARTER_SNORKEL, STARTERS_MARKER_NAME

    store_folder = _fresh(roots.allowed / "settings" / "starter-store", roots)
    roots.mkdir(store_folder)
    check_target(store_folder / STARTERS_MARKER_NAME, roots)
    names = (STARTER_SNORKEL, STARTER_SCUBA)
    for name in names:
        check_target(store_folder / f"{name}.json", roots)
    store = PresetStore(store_folder)
    store.install_starters()
    result = {}
    for name in names:
        destination = check_target(roots.allowed / "presets" / f"{name}.json", roots)
        roots.mkdir(destination.parent)
        store.export_preset(name, destination, overwrite=True)
        result[name] = json.loads(destination.read_text(encoding="utf-8"))
    return result


def _preflight(roots: OutputRoots) -> None:
    """Refuse existing aliases/shared files before handing directories to writers."""
    check_target(roots.allowed, roots)
    if roots.allowed.exists():
        for path in roots.allowed.rglob("*"):
            check_target(path, roots)
    settings = check_target(roots.allowed / "settings" / "settings.json", roots)
    if settings.exists():
        raise ValueError(
            "pack settings.json exists; shipped defaults require an empty settings store"
        )


def _selection(manifest: Path | None, roots: OutputRoots) -> list[select.Item]:
    """Read a tiny name-only selection, or use the complete commissioned catalog."""
    catalog = select.catalog()
    if manifest is None:
        return list(catalog)
    check_target(manifest, roots)
    values = json.loads(manifest.read_text(encoding="utf-8"))
    if not isinstance(values, list) or not values:
        raise ValueError("manifest must be a nonempty name-only item list")
    expected = {item.name: item for item in catalog}
    selected = []
    seen = set()
    for value in values:
        if not isinstance(value, dict) or set(value) != {"name", "group", "kind"}:
            raise ValueError("manifest items require only name, group and kind")
        name = _bare(value["name"])
        item = expected.get(name)
        if (
            item is None
            or item.group != value["group"]
            or item.kind != value["kind"]
            or name in seen
        ):
            raise ValueError("manifest has an unknown, inconsistent or duplicate commissioned item")
        selected.append(item)
        seen.add(name)
    order = {item.name: i for i, item in enumerate(catalog)}
    return sorted(selected, key=lambda item: order[item.name])


def _pending(item: select.Item) -> dict[str, Any]:
    return {
        "item": item.stem,
        "group": item.group,
        "kind": item.kind,
        "source_name": item.name,
        "status": "pending",
        "message": "",
        "corrected_name": "",
        "source_view_name": "",
        "source_thumb": "",
        "corrected_thumb": "",
        "pair_name": "",
        "stills": [],
    }


def _invoke(
    sources: Sequence[Path],
    group: str,
    roots: OutputRoots,
    *,
    neutral: bool,
    force_cpu: bool,
) -> tuple[list[dict[str, Any]], int]:
    """Run one product batch and account for every supplied source, including failures."""
    for folder in ("photos", "clips", "settings", "records", "cache", "logs"):
        roots.mkdir(check_target(roots.allowed / folder, roots))
    arguments = runner_arguments(
        sources, group=group, roots=roots, neutral=neutral, force_cpu=force_cpu
    )
    record = Path(arguments[arguments.index("--record") + 1])
    started = time.monotonic()
    done = run_tool(arguments, timeout=24 * 3600)
    # Never persist argument vectors (which carry source paths) or raw diagnostics.
    diagnostic = (done.stdout + b"\n" + done.stderr).decode("utf-8", "replace")
    roots.write_text(
        roots.allowed / "logs" / f"{record.stem}.log",
        f"exit_status={done.returncode}\nwall_s={time.monotonic() - started:.3f}\n"
        + _safe_text(diagnostic, roots)
        + "\n",
    )
    if record.exists():
        # The runner already emits names only. Apply the instrument's diagnostic
        # policy as well, so metadata warnings never enter a CP5 evidence record.
        document = json.loads(record.read_text(encoding="utf-8"))
        for item_record in document.get("items", []):
            if item_record.get("failure") is not None:
                item_record["failure"] = _safe_text(item_record["failure"], roots)
            item_record["warnings"] = [
                _safe_text(warning, roots) for warning in item_record.get("warnings", [])
            ]
        _json_write(record, document, roots)
        results = read_runner_record(record, group=group, roots=roots)
        if len(results) != len(sources) or any(
            result["source_name"] != source.name
            for result, source in zip(results, sources, strict=True)
        ):
            raise ValueError("runner record does not match the ordered batch inputs")
    else:
        results = [
            {
                **_pending(
                    select.Item(source.name, group, "photo" if group.startswith("P-") else "video")
                ),
                "status": "failed",
                "message": "runner produced no record; see the group log",
            }
            for source in sources
        ]
    for result in results:
        result["runner_exit_status"] = done.returncode
    return results, done.returncode


def _view_photo(result: dict[str, Any], roots: OutputRoots) -> None:
    for role, key in (("source", "source_view_name"), ("corrected", "corrected_name")):
        name = f"{Path(result[key]).stem}_{role}.jpg"
        page.thumbnail(
            roots.allowed / "photos" / result[key], roots.allowed / "thumbs" / name, roots=roots
        )
        result[f"{role}_thumb"] = name


def _browser_frame(path: Path, stream: Mapping[str, Any], roots: OutputRoots) -> None:
    """Convert non-BT709 primaries to sRGB for browser JPEG derivatives only."""
    primaries = str(stream.get("color_primaries", "unknown"))
    if primaries not in {"bt709", "unknown", "unspecified"}:
        temporary = check_target(path.with_name(path.stem + "-srgb.png"), roots)
        transfer = str(stream.get("color_transfer", "bt709"))
        if transfer in {"unknown", "unspecified"}:
            transfer = "bt709"
        done = run_tool(
            [
                "ffmpeg",
                "-nostdin",
                "-v",
                "error",
                "-y",
                "-i",
                str(path),
                "-vf",
                f"zscale=primariesin={primaries}:transferin={transfer}:matrixin=gbr:"
                "rangein=full:primaries=bt709:transfer=iec61966-2-1:matrix=gbr:range=full",
                "-frames:v",
                "1",
                str(temporary),
            ]
        )
        if done.returncode:
            raise ValueError("video primary conversion for browser viewing failed")
        roots.write_bytes(path, temporary.read_bytes())
        roots.check(temporary).unlink()
    # Tag only the normalized browser derivative; source/product metadata is untouched.
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    with Image.open(path) as image:
        rgb = image.convert("RGB")
    rgb.info.clear()
    rgb.save(roots.check(path), icc_profile=profile)


def _view_video(
    result: dict[str, Any], source: Path, roots: OutputRoots, *, force_cpu: bool
) -> None:
    corrected = roots.allowed / "clips" / result["corrected_name"]
    pair = _fresh(roots.allowed / "pairs" / f"{result['item']}_pair.mp4", roots)
    dimensions = make_pair(source, corrected, pair, roots=roots, force_cpu=force_cpu)
    result["pair_name"] = pair.name
    result["view_dimensions"] = dimensions
    source_stream = _video(source)
    corrected_stream = _video(corrected)
    duration = min(source_stream["duration_s"], corrected_stream["duration_s"])
    for fraction in (0.1, 0.5, 0.9):
        wanted = duration * fraction
        source_pts = _frame_time(source, wanted)
        corrected_pts = _frame_time(corrected, float(source_pts))
        if abs(source_pts - corrected_pts) > Fraction(1, 1000000):
            raise ValueError("source and corrected viewing still PTS differ")
        frames = []
        for role, video, pts, stream in (
            ("source", source, source_pts, source_stream),
            ("corrected", corrected, corrected_pts, corrected_stream),
        ):
            frame = _fresh(
                roots.allowed / "pairs" / f".{result['item']}-{role}-{fraction}.png", roots
            )
            extract_view_frame(video, float(pts), frame, roots=roots)
            _browser_frame(frame, stream, roots)
            frames.append(frame)
            if fraction == 0.5:
                thumb = (
                    roots.allowed / "thumbs" / f"{Path(result['corrected_name']).stem}_{role}.jpg"
                )
                page.thumbnail(frame, thumb, roots=roots)
                result[f"{role}_thumb"] = thumb.name
        target = _fresh(
            roots.allowed / "pairs" / f"{result['item']}_{int(fraction * 100)}.jpg", roots
        )
        page.pair_still(frames[0], frames[1], target, roots=roots)
        result["stills"].append(
            {
                "name": target.name,
                "fraction": fraction,
                "source_pts_s": float(source_pts),
                "corrected_pts_s": float(corrected_pts),
            }
        )
        for frame in frames:
            roots.check(frame).unlink()


def _build_groups(
    items: Sequence[select.Item],
    state: dict[str, Any],
    roots: OutputRoots,
    *,
    force_cpu: bool,
) -> None:
    """Export each requested group and persist named results after each finished group."""
    resolved = []
    for item in items:
        source = (
            select.find_photo(item.name, roots.footage)
            if item.kind == "photo"
            else find_footage_file(item.stem, roots.footage)
        )
        if source.name.casefold() != item.name.casefold():
            raise ValueError("video locator returned a different commissioned extension")
        resolved.append(replace(item, path=source))
    for group in select.GROUPS:
        group_items = [item for item in resolved if item.group == group]
        if not group_items:
            continue
        sources = []
        preparations = []
        for item in group_items:
            assert item.path is not None
            source = item.path
            prepared: dict[str, Any] = {
                "path": source,
                "excerpt": False,
                "actual_start_s": 0.0,
                "planned_start_s": 0.0,
            }
            if item.kind == "video" and group != "V-R":
                plan = select.excerpt_plan(group, _video(source)["duration_s"])
                prepared["duration_s"] = plan.duration_s
                prepared["planned_duration_s"] = plan.duration_s
                if plan.excerpt:
                    prepared = prepare_excerpt(
                        source, start_s=plan.start_s, duration_s=plan.duration_s, roots=roots
                    )
            sources.append(prepared["path"])
            preparations.append(prepared)
        results, _ = _invoke(sources, group, roots, neutral=False, force_cpu=force_cpu)
        neutral_results = (
            _invoke(sources, group, roots, neutral=True, force_cpu=force_cpu)[0]
            if group.startswith("P-")
            else []
        )
        for index, (item, result, prepared) in enumerate(
            zip(group_items, results, preparations, strict=True)
        ):
            result.update(item=item.stem, source_name=item.name)
            result["excerpt"] = {key: value for key, value in prepared.items() if key != "path"}
            if prepared["excerpt"]:
                result["excerpt"]["name"] = prepared["path"].name
            if item.kind == "photo":
                neutral = neutral_results[index]
                result["neutral_record_name"] = neutral.get("record_name", "")
                result["neutral_exit_status"] = neutral["runner_exit_status"]
                if neutral["status"] == "done":
                    result["source_view_name"] = neutral["corrected_name"]
                else:
                    result["status"] = "failed"
                    result["message"] += "; neutral source view: " + neutral["message"]
            if result["status"] == "done":
                try:
                    if item.kind == "photo":
                        _view_photo(result, roots)
                    else:
                        _view_video(result, prepared["path"], roots, force_cpu=force_cpu)
                except (ValueError, OSError, ExtractError) as exc:
                    result["aid_message"] = _safe_text(exc, roots)
                    # Keep product success distinct from an incomplete viewing aid.
                    result["reviewable"] = False
            for position, previous in enumerate(state["items"]):
                if previous["item"] == item.stem:
                    state["items"][position] = result
                    break
        _json_write(roots.allowed / "records" / "pack.json", state, roots)


def main(argv: Sequence[str] | None = None) -> int:
    """Run a review-pack stage, all stages, or a strict owner-sheet tally.

    Args:
        argv: CLI arguments, or the process arguments when absent.

    Returns:
        Zero for a valid completed command, or an instrument error status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("photos", "clips", "presets", "page", "tally", "all"))
    parser.add_argument("subject", nargs="?")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--force-cpu", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    roots: OutputRoots | None = None
    try:
        if args.stage == "tally":
            if args.subject is None:
                raise ValueError("tally requires a sheet")
            print(sheet.format_tally(sheet.tally(Path(args.subject))))
            return 0
        config = load_local_config(args.config)
        roots = OutputRoots.from_config(config, subdir="wp5.3")
        check_target(roots.allowed, roots)
        _preflight(roots)
        if args.stage == "page" and args.check:
            errors = page.check_links(roots.allowed / "index.html", roots=roots)
            for error in errors:
                print(_safe_text(error, roots))
            return 2 if errors else 0
        stages = ("photos", "presets", "clips", "page") if args.stage == "all" else (args.stage,)
        state_path = roots.allowed / "records" / "pack.json"
        check_target(state_path, roots)
        state: dict[str, Any] = (
            json.loads(state_path.read_text(encoding="utf-8"))
            if state_path.exists()
            else {"schema": 1, "items": [_pending(item) for item in select.catalog()]}
        )
        for stage in stages:
            if stage == "presets":
                state["presets"] = export_presets(roots=roots)
            elif stage == "page":
                sheet.write_sheet(state["items"], roots.allowed / "review-sheet.csv", roots=roots)
                page.write_page(state["items"], state.get("presets", {}), roots=roots)
                if page.check_links(roots.allowed / "index.html", roots=roots):
                    raise ValueError("generated page contains unresolved links")
            else:
                selected = _selection(args.manifest, roots)
                selected = [
                    item
                    for item in selected
                    if item.kind == ("photo" if stage == "photos" else "video")
                ]
                if args.subject:
                    if stage != "clips" or args.subject not in select.GROUPS[2:]:
                        raise ValueError("clips requires a commissioned video group")
                    selected = [item for item in selected if item.group == args.subject]
                if args.manifest is not None:
                    names = {item.name for item in _selection(args.manifest, roots)}
                    state["items"] = [
                        item for item in state["items"] if item["source_name"] in names
                    ]
                _build_groups(selected, state, roots, force_cpu=args.force_cpu)
            _json_write(state_path, state, roots)
        print(f"{args.stage}: completed; {len(state['items'])} items accounted for")
        return 0
    except (ValueError, OSError, LocalConfigError, ExtractError) as exc:
        message = (
            _safe_text(exc, roots)
            if roots is not None
            else (str(exc) if args.stage == "tally" else "invalid local configuration")
        )
        print(f"reviewpack: {message}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
