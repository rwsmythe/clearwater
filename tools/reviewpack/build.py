"""Build CP5 evidence through the shipped headless runner, with no agent judgement."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
import time
import uuid
from collections import Counter, defaultdict
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import replace
from datetime import UTC, datetime
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

_PATH_EXTENSION = r"(?:heic|jpe?g|png|tiff?|mov|mp4|mkv|dll|exe|json|toml|log|py|csv|txt|dat|tmp)"


def _metadata_text(line: str) -> str:
    """Keep static metadata diagnostics; withhold unclassifiable value fragments."""
    if not re.search(r"\b(?:EXIF|GPS)\w*\b", line, re.I):
        return line
    fragments = []
    uncertain = False
    unclassified_tail = False
    for fragment in line.split(";"):
        if not re.search(r"\b(?:EXIF|GPS)\w*\b", fragment, re.I):
            fragments.append(fragment)
            if not re.fullmatch(
                r"\s*(?:it is not carried|orientation taken as 1)\.?\s*", fragment, re.I
            ):
                unclassified_tail = True
            continue
        # These value-free diagnostic forms carry no source tag contents. Unknown
        # forms are withheld rather than trying to infer where a tag value ends.
        candidate = re.sub(r"\([^()]*\)", "([withheld])", fragment)
        skeleton = candidate.replace("([withheld])", "").strip()
        static = re.fullmatch(
            r"(?:[A-Za-z0-9_.-]+\.(?:HEIC|JPG|PNG|TIFF?|MOV|MP4):\s*)?"
            r"(?:the )?(?:EXIF|GPS) (?:block|metadata|tags?) "
            r"(?:is damaged|is missing|is absent|was not carried|is not carried|"
            r"cannot be parsed|cannot be read|was dropped|is invalid)\.?",
            skeleton,
            re.I,
        ) or re.fullmatch(
            r"(?:no (?:EXIF|GPS) carried|BigTIFF cannot be read for EXIF)\.?", skeleton, re.I
        )
        if static:
            fragments.append(candidate)
        else:
            uncertain = True
            leading = fragment[: len(fragment) - len(fragment.lstrip())]
            fragments.append(leading + "[withheld]")
    if uncertain and unclassified_tail:
        return "[withheld]"
    return ";".join(fragments)


def _safe_text(value: object, roots: OutputRoots) -> str:
    text = str(value)
    # Diagnostics are kept name-only even when an external tool quotes a path.
    for root in (roots.footage, roots.allowed, Path(__file__).resolve().parents[2]):
        for spelling in (str(root), root.as_posix(), str(root).replace("\\", "\\\\")):
            text = re.sub(re.escape(spelling), "", text, flags=re.IGNORECASE)

    def basename(token: str) -> str:
        """Collapse path-like text while preserving ratios and container box names."""
        if not re.match(r"(?:[A-Za-z]:[\\/]|[\\/])", token) and not re.search(
            rf"[\\/].*\.{_PATH_EXTENSION}(?=$|[\s:;,\)\]])", token, re.I
        ):
            return token
        return re.split(r"[\\/]+", token)[-1] or "[path]"

    # A quoted span supplies a reliable boundary even for extensionless tools.
    text = re.sub(
        r"""(["'])([^"'\r\n]*[\\/][^"'\r\n]*)\1""",
        lambda match: match[1] + basename(match[2]) + match[1],
        text,
    )
    # Unquoted rooted paths can contain spaces; known file extensions bound them.
    text = re.sub(
        r"""(?:[A-Za-z]:[\\/]|\\\\|(?<!\w)/)[^\r\n"'<>]*?"""
        rf"\.{_PATH_EXTENSION}"
        r"(?=$|[\s:;,\)\]])",
        lambda match: basename(match.group()),
        text,
        flags=re.IGNORECASE,
    )
    # Root stripping can leave relative folders. Collapse only path-like tails;
    # product ratios and container box names must remain verbatim.
    text = re.sub(r"""[^\s"'<>]*[\\/][^\s"'<>]*""", lambda match: basename(match.group()), text)
    return (
        "\n".join(_metadata_text(line) for line in text.splitlines())
        .encode("ascii", "backslashreplace")
        .decode("ascii")
    )


def _json_write(path: Path, value: dict[str, Any], roots: OutputRoots) -> None:
    """Atomically persist item records with the same replace-or-append rule everywhere."""
    roots.check(path)
    if not isinstance(value.get("items"), list):
        raise ValueError("JSON item records require an items list")
    if path.exists():
        previous = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(previous, dict) or not isinstance(previous.get("items"), list):
            raise ValueError(f"{path.name}: invalid existing item record")
        merged = {**previous, **value, "items": list(previous["items"])}
        for item in value["items"]:
            _store_item(merged, item)
        value = merged
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


@contextmanager
def _aid_files(
    roots: OutputRoots, *, temporary: bool = False, result: dict[str, Any] | None = None
) -> Iterator[Callable[[Path], Path]]:
    """Track new aid paths only, removing scratch files and failed-attempt outputs."""
    paths: list[Path] = []
    completed = False

    def create(path: Path) -> Path:
        target = _fresh(path, roots)
        paths.append(target)
        return target

    try:
        yield create
        completed = True
    finally:
        if temporary or not completed:
            for path in reversed(paths):
                roots.remove(path)
        if not completed and result is not None:
            result.update(source_thumb="", corrected_thumb="", pair_name="", stills=[])
            result.pop("view_dimensions", None)


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


def _hlg_refusal(message: str) -> bool:
    """Recognize the product's HLG refusal, rather than any diagnostic mentioning HLG."""
    return any(
        text in message.lower()
        for text in (
            "this video uses hlg hdr, which clearwater does not support.",
            "unsupported hlg transfer.",
        )
    )


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
        if raw["state"] in {"not run", "cancelled"} and not message:
            message = f"runner reported {raw['state']}; no further reason was supplied"
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
                else (
                    raw["state"]
                    if raw["state"] in {"not run", "cancelled"}
                    else ("refused" if group == "V-R" and _hlg_refusal(message) else "failed")
                ),
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
        if group == "V-R" and result[-1]["status"] != "refused":
            result[-1]["expected_refusal_failed"] = True
            result[-1]["refusal_message"] = (
                f"Expected HLG refusal; product reported {result[-1]['status']}."
            )
    return result


def stream_copy_command(
    source: Path,
    destination: Path,
    *,
    start_s: float,
    duration_s: float,
    streams: Sequence[Mapping[str, Any]] | None = None,
    timecode: str | None = None,
) -> list[str]:
    """Build a stream-copy excerpt, regenerating an existing timecode track.

    Args:
        source: Read-only input.
        destination: Guarded excerpt target.
        start_s: Requested source start.
        duration_s: Requested excerpt length.
        streams: Probed roster; map every non-timecode stream explicitly.
        timecode: Advanced source timecode for FFmpeg's timecode writer.

    Returns:
        FFmpeg subprocess arguments.
    """
    args = [
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
    ]
    if streams is None:
        args += ["-map", "0"]
    else:
        for stream in streams:
            if stream.get("codec_tag_string") != "tmcd":
                args += ["-map", f"0:{stream['index']}"]
    args += ["-c", "copy", "-map_metadata", "0", "-avoid_negative_ts", "make_zero"]
    if timecode is not None:
        args += ["-timecode", timecode, "-write_tmcd", "1"]
    else:
        args += ["-write_tmcd", "0"]
    return [*args, str(destination)]


def validate_stream_copy(
    source_streams: Sequence[Mapping[str, Any]], excerpt_streams: Sequence[Mapping[str, Any]]
) -> None:
    """Reject stream-count or codec-tag changes in an excerpt.

    Args:
        source_streams: Selected source stream facts.
        excerpt_streams: Selected excerpt stream facts.
    """
    keys = ("codec_type", "codec_name", "codec_tag_string")
    if Counter(tuple(s.get(k) for k in keys) for s in source_streams) != Counter(
        tuple(s.get(k) for k in keys) for s in excerpt_streams
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


def _advance_timecode(value: str, seconds: float, rate: Fraction) -> str:
    """Advance SMPTE non-drop or 29.97/59.94 drop-frame labels by source frames."""
    match = re.fullmatch(r"(\d{2}):(\d{2}):(\d{2})([:;])(\d{2})", value)
    nominal = round(rate)
    if match is None or nominal <= 0:
        raise ValueError("invalid source timecode")
    h, m, s, separator, f = match.groups()
    hours, minutes, secs, frames = map(int, (h, m, s, f))
    if hours >= 24 or minutes >= 60 or secs >= 60 or frames >= nominal:
        raise ValueError("invalid source timecode fields")
    drop = 0
    if separator == ";":
        if rate not in {Fraction(30000, 1001), Fraction(60000, 1001)}:
            raise ValueError("unsupported drop-frame timecode rate")
        drop = 2 if nominal == 30 else 4
        if minutes % 10 and secs == 0 and frames < drop:
            raise ValueError("invalid dropped timecode label")
    total_minutes = hours * 60 + minutes
    count = (
        (hours * 3600 + minutes * 60 + secs) * nominal
        + frames
        - drop * (total_minutes - total_minutes // 10)
    )
    count += round(Fraction(str(seconds)) * rate)
    day = nominal * 86400 - drop * (1440 - 144)
    count %= day
    if drop:
        per_ten = nominal * 600 - drop * 9
        tens, remainder = divmod(count, per_ten)
        count += drop * 9 * tens
        if remainder >= drop:
            count += drop * ((remainder - drop) // (nominal * 60 - drop))
    total_seconds, frame = divmod(count, nominal)
    hour, remaining = divmod(total_seconds, 3600)
    minute, second = divmod(remaining, 60)
    return f"{hour:02d}:{minute:02d}:{second:02d}{separator}{frame:02d}"


def _packet_facts(source: Path, interval: str | None = None) -> list[dict[str, Any]]:
    options = ["-read_intervals", interval] if interval else []
    return list(
        _probe(
            source,
            *options,
            "-show_packets",
            "-show_data_hash",
            "sha256",
            "-show_entries",
            "packet=stream_index,codec_type,pts_time,data_hash,pos,flags",
        ).get("packets", [])
    )


def _matched_streams(
    before: Sequence[Mapping[str, Any]],
    after: Sequence[Mapping[str, Any]],
) -> list[tuple[Mapping[str, Any], Mapping[str, Any]]]:
    validate_stream_copy(before, after)
    groups: dict[tuple[str, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for stream in before:
        groups[
            tuple(str(stream.get(k)) for k in ("codec_type", "codec_name", "codec_tag_string"))
        ].append(stream)
    result = []
    for stream in after:
        key = tuple(str(stream.get(k)) for k in ("codec_type", "codec_name", "codec_tag_string"))
        result.append((groups[key].pop(0), stream))
    return result


def _verify_payloads(
    matches: Sequence[tuple[Mapping[str, Any], Mapping[str, Any]]],
    source_packets: Sequence[Mapping[str, Any]],
    packets: Sequence[Mapping[str, Any]],
) -> None:
    for before, after in matches:
        if before.get("codec_tag_string") == "tmcd":
            continue
        original = [p["data_hash"] for p in source_packets if p["stream_index"] == before["index"]]
        kept = [p["data_hash"] for p in packets if p["stream_index"] == after["index"]]
        if not kept or not any(original[i : i + len(kept)] == kept for i in range(len(original))):
            raise ValueError("excerpt changed non-timecode packet payloads or order")


def _displayed_start(source: Path, packets: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    """Identify the first actually displayed frame by its packet file position."""
    frames = _probe(
        source,
        "-select_streams",
        "v:0",
        "-read_intervals",
        "%+#32",
        "-show_frames",
        "-show_entries",
        "frame=pkt_pos,best_effort_timestamp_time",
    ).get("frames", [])
    if not frames:
        raise ValueError("excerpt has no displayed frame")
    first = frames[0]
    packet = next(
        (
            p
            for p in packets
            if p.get("codec_type") == "video" and str(p.get("pos")) == str(first.get("pkt_pos"))
        ),
        None,
    )
    video = [p for p in packets if p.get("codec_type") == "video"]
    if packet is None or float(first["best_effort_timestamp_time"]) != min(
        float(p["pts_time"]) for p in video
    ):
        raise ValueError("excerpt displayed start differs from retained video start")
    return packet


def prepare_excerpt(
    source: Path, *, start_s: float, duration_s: float, roots: OutputRoots
) -> dict[str, Any]:
    """Copy and validate an excerpt; return a loud item error on any failed check.

    Args:
        source: Read-only input.
        start_s: Planned start.
        duration_s: Planned duration.
        roots: Pack and source roots.

    Returns:
        Runtime excerpt path or None, measured timings, status and failure text.
    """
    destination = _fresh(roots.allowed / "excerpts" / source.name, roots)
    roots.mkdir(destination.parent)
    planned: dict[str, Any] = {
        "path": None,
        "excerpt": False,
        "status": "excerpt_failed",
        "planned_start_s": start_s,
        "actual_start_s": None,
        "planned_duration_s": duration_s,
        "duration_s": None,
    }
    try:
        before = _probe(source, "-show_streams")["streams"]
        packets = _packet_facts(source, f"{max(0, start_s - 30)}%{start_s + duration_s + 30}")
        video = next(s for s in before if s["codec_type"] == "video")
        keys = [
            float(p["pts_time"])
            for p in packets
            if p.get("codec_type") == "video"
            and "K" in p.get("flags", "")
            and float(p["pts_time"]) <= start_s + 1e-7
        ]
        if not keys:
            raise ValueError("no source keyframe for excerpt seek")
        selected = max(keys)
        has_timecode = any(s.get("codec_tag_string") == "tmcd" for s in before)
        timecode = None
        if has_timecode:
            tag = video.get("tags", {}).get("timecode")
            if tag is None:
                tag = next(
                    s.get("tags", {}).get("timecode")
                    for s in before
                    if s.get("codec_tag_string") == "tmcd"
                )
            timecode = _advance_timecode(str(tag), selected, Fraction(video["avg_frame_rate"]))
        done = run_tool(
            stream_copy_command(
                source,
                destination,
                start_s=start_s,
                duration_s=duration_s,
                streams=before,
                timecode=timecode,
            )
        )
        if done.returncode:
            lines = done.stderr.decode("utf-8", "replace").strip().splitlines()
            raise ValueError(lines[-1] if lines else "FFmpeg excerpt failed without stderr")
        after = _probe(destination, "-show_streams")["streams"]
        matches = _matched_streams(before, after)
        retained = _packet_facts(destination)
        _verify_payloads(matches, packets, retained)
        displayed = _displayed_start(destination, retained)
        # Repeated encoded packets can occur in a loop or a static scene. Bind
        # the hash match to the probed seek keyframe instead of choosing an
        # arbitrary equal payload elsewhere in the source interval.
        seek_packets = [
            p
            for p in packets
            if p.get("codec_type") == "video" and abs(float(p["pts_time"]) - selected) <= 1e-6
        ]
        actual = actual_excerpt_start(seek_packets, [displayed])
        if abs(actual - selected) > 1e-6:
            raise ValueError("actual displayed keyframe differs from timecode seek plan")
        if has_timecode:
            for stream in after:
                if (
                    stream.get("codec_type") == "video" or stream.get("codec_tag_string") == "tmcd"
                ) and stream.get("tags", {}).get("timecode") != timecode:
                    raise ValueError("regenerated timecode does not match actual source start")
        return {
            **planned,
            "path": destination,
            "excerpt": True,
            "status": "ready",
            "actual_start_s": actual,
            "duration_s": _video(destination)["duration_s"],
            "timecode": timecode,
            "message": "",
        }
    except (
        ValueError,
        KeyError,
        StopIteration,
        TypeError,
        ZeroDivisionError,
        subprocess.TimeoutExpired,
        OSError,
        ExtractError,
    ) as exc:
        if destination.exists():
            roots.check(destination).unlink()
        return {**planned, "message": _safe_text(exc, roots)}


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
        folder = check_target(target.parent / (".frames-" + uuid.uuid4().hex), roots)
        try:
            extracted = extract(source, [timestamp_s], folder, roots=roots)[0]
            roots.write_bytes(target, extracted.path.read_bytes())
        finally:
            if folder.exists():
                # This unique directory belongs to this extraction only. Remove
                # only files created by the helper, refusing any shared alias.
                for created in folder.iterdir():
                    if created.is_file() and created.suffix == ".png":
                        roots.remove(created)
                if not any(folder.iterdir()):
                    roots.check(folder).rmdir()
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
    with _aid_files(roots) as create, _aid_files(roots, temporary=True) as scratch:
        if destination.exists():
            raise ValueError("pair destination already exists")
        target = create(destination)
        roots.mkdir(target.parent)
        source_stream = _video(source)
        sizes = []
        # Decode with each input's default autorotate: actual display dimensions, not a
        # handwritten interpretation of its matrix, determine whether hstack is safe.
        for index, video in enumerate((source, corrected)):
            frame = scratch(roots.allowed / "pairs" / f".size-{uuid.uuid4().hex}-{index}.png")
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
            f":out_color_matrix={tags.color_space},setsar=1,"
            f"settb={source_stream['time_base']},setpts=PTS-STARTPTS"
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
            "-fps_mode",
            "passthrough",
            "-enc_time_base",
            "filter",
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
        else:
            args += ["-preset", "p5", "-tune", "hq", "-rc", "vbr", "-cq", "20", "-b:v", "0"]
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
    invocation_error = ""
    try:
        done = run_tool(arguments, timeout=24 * 3600)
    except (subprocess.TimeoutExpired, OSError, ExtractError) as exc:
        invocation_error = (
            f"runner timed out after {exc.timeout} seconds"
            if isinstance(exc, subprocess.TimeoutExpired)
            else _safe_text(exc, roots)
        )
        done = subprocess.CompletedProcess(arguments, 1, b"", invocation_error.encode("ascii"))
    # Never persist argument vectors (which carry source paths) or raw diagnostics.
    diagnostic = (done.stdout + b"\n" + done.stderr).decode("utf-8", "replace")
    roots.write_text(
        roots.allowed / "logs" / f"{record.stem}.log",
        f"exit_status={done.returncode}\nwall_s={time.monotonic() - started:.3f}\n"
        + _safe_text(diagnostic, roots)
        + "\n",
    )
    if record.exists() and not invocation_error:
        # CHARC R2 F3: retain the product's authoritative bytes; read_runner_record
        # projects safe diagnostics into the pack state, sheet and HTML instead.
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
                "message": invocation_error or "runner produced no record; see the group log",
            }
            for source in sources
        ]
    for result in results:
        result["runner_exit_status"] = done.returncode
    return results, done.returncode


def _view_photo(result: dict[str, Any], roots: OutputRoots) -> None:
    with _aid_files(roots, result=result) as create:
        for role, key in (("source", "source_view_name"), ("corrected", "corrected_name")):
            target = create(roots.allowed / "thumbs" / f"{Path(result[key]).stem}_{role}.jpg")
            page.thumbnail(roots.allowed / "photos" / result[key], target, roots=roots)
            result[f"{role}_thumb"] = target.name


def _browser_frame(path: Path, stream: Mapping[str, Any], roots: OutputRoots) -> None:
    """Convert explicitly tagged SDR primaries/transfer to sRGB for browser aids."""
    primaries = str(stream.get("color_primaries", "unknown"))
    transfer = str(stream.get("color_transfer", "unknown"))
    if primaries not in {"unknown", "unspecified"} and transfer not in {"unknown", "unspecified"}:
        with _aid_files(roots, temporary=True) as scratch:
            temporary = scratch(path.with_name(path.stem + "-srgb.png"))
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
    with _aid_files(roots, result=result) as create:
        corrected = roots.allowed / "clips" / result["corrected_name"]
        pair = create(roots.allowed / "pairs" / f"{result['item']}_pair.mp4")
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
                frame = create(roots.allowed / "pairs" / f".{result['item']}-{role}-{fraction}.png")
                extract_view_frame(video, float(pts), frame, roots=roots)
                _browser_frame(frame, stream, roots)
                frames.append(frame)
                if fraction == 0.5:
                    thumb = create(
                        roots.allowed
                        / "thumbs"
                        / f"{Path(result['corrected_name']).stem}_{role}.jpg"
                    )
                    page.thumbnail(frame, thumb, roots=roots)
                    result[f"{role}_thumb"] = thumb.name
            target = create(roots.allowed / "pairs" / f"{result['item']}_{int(fraction * 100)}.jpg")
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


def _store_item(state: dict[str, Any], result: dict[str, Any]) -> None:
    """Replace one saved item or append it; never filter the persisted inventory."""
    for position, previous in enumerate(state["items"]):
        if previous["item"] == result["item"]:
            state["items"][position] = result
            return
    state["items"].append(result)


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
        active_items = []
        excerpt_records = []
        for item in group_items:
            assert item.path is not None
            source = item.path
            prepared: dict[str, Any] = {
                "path": source,
                "excerpt": False,
                "actual_start_s": 0.0,
                "planned_start_s": 0.0,
            }
            try:
                if item.kind == "video" and group != "V-R":
                    plan = select.excerpt_plan(group, _video(source)["duration_s"])
                    prepared["duration_s"] = plan.duration_s
                    prepared["planned_duration_s"] = plan.duration_s
                    if plan.excerpt:
                        prepared = prepare_excerpt(
                            source, start_s=plan.start_s, duration_s=plan.duration_s, roots=roots
                        )
                        excerpt_record = {
                            **_pending(item),
                            "status": prepared["status"],
                            "message": prepared["message"],
                            "excerpt": {
                                key: value for key, value in prepared.items() if key != "path"
                            },
                        }
                        excerpt_records.append(excerpt_record)
                        if prepared["status"] == "excerpt_failed":
                            _store_item(state, excerpt_record)
                            continue
            except (
                ValueError,
                KeyError,
                StopIteration,
                TypeError,
                ZeroDivisionError,
                subprocess.TimeoutExpired,
                OSError,
                ExtractError,
            ) as exc:
                _store_item(
                    state,
                    {
                        **_pending(item),
                        "status": "failed",
                        "message": _safe_text(exc, roots),
                    },
                )
                continue
            sources.append(prepared["path"])
            preparations.append(prepared)
            active_items.append(item)
        if excerpt_records:
            _json_write(
                roots.allowed / "records" / f"{group}-excerpts.json",
                {"schema": 1, "tool": "reviewpack", "group": group, "items": excerpt_records},
                roots,
            )
        if not sources:
            _json_write(roots.allowed / "records" / "pack.json", state, roots)
            continue
        results, _ = _invoke(sources, group, roots, neutral=False, force_cpu=force_cpu)
        neutral_results = (
            _invoke(sources, group, roots, neutral=True, force_cpu=force_cpu)[0]
            if group.startswith("P-")
            else []
        )
        for index, (item, result, prepared) in enumerate(
            zip(active_items, results, preparations, strict=True)
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
                elif result["status"] == "done":
                    result["aid_message"] = "neutral source view: " + neutral["message"]
                    result["source_view_name"] = ""
                    result["reviewable"] = False
                    result["viewing_aid_failed"] = True
            if result["status"] == "done" and not result.get("viewing_aid_failed"):
                try:
                    if item.kind == "photo":
                        _view_photo(result, roots)
                    else:
                        _view_video(result, prepared["path"], roots, force_cpu=force_cpu)
                except (
                    ValueError,
                    KeyError,
                    StopIteration,
                    TypeError,
                    ZeroDivisionError,
                    subprocess.TimeoutExpired,
                    OSError,
                    ExtractError,
                    ImageCms.PyCMSError,
                ) as exc:
                    result["aid_message"] = _safe_text(exc, roots)
                    # Keep product success distinct from an incomplete viewing aid.
                    result["reviewable"] = False
                    result["viewing_aid_failed"] = True
            _store_item(state, result)
        _json_write(roots.allowed / "records" / "pack.json", state, roots)


def _failed(item: Mapping[str, Any]) -> bool:
    return item["status"] in {"failed", "excerpt_failed", "not run", "cancelled"} or bool(
        item.get("viewing_aid_failed")
        or item.get("aid_message")
        or item.get("expected_refusal_failed")
    )


@contextmanager
def _stage_lock(roots: OutputRoots) -> Iterator[None]:
    """Serialize stage writers; a held or stale lock is never automatically broken."""
    path = check_target(roots.allowed / ".reviewpack.lock", roots)
    roots.mkdir(path.parent)
    try:
        handle = path.open("x", encoding="utf-8", newline="\n")
    except FileExistsError:
        with path.open(encoding="utf-8", errors="replace") as held:
            holder = held.read(256)
        pid = re.search(r"^pid=(\d+)$", holder, re.M)
        started = re.search(r"^started=([0-9T:.+Z-]+)$", holder, re.M)
        raise ValueError(
            f"pack locked by pid={pid[1] if pid else 'unknown'} "
            f"started={started[1] if started else 'unknown'}; if stale, "
            "delete .reviewpack.lock manually before retrying"
        ) from None
    try:
        with handle:
            handle.write(f"pid={os.getpid()}\nstarted={datetime.now(UTC).isoformat()}\n")
        yield
    finally:
        roots.remove(path)


def _run_stages(args: argparse.Namespace, roots: OutputRoots) -> int:
    """Run stages under the single command lock; page never writes pack state."""
    stages = ("photos", "presets", "clips", "page") if args.stage == "all" else (args.stage,)
    state_path = roots.allowed / "records" / "pack.json"
    check_target(state_path, roots)
    state: dict[str, Any] = (
        json.loads(state_path.read_text(encoding="utf-8"))
        if state_path.exists()
        else {"schema": 1, "items": [_pending(item) for item in select.catalog()]}
    )
    attempted: set[str] = set()
    for stage in stages:
        if stage == "presets":
            state["presets"] = export_presets(roots=roots)
        elif stage == "page":
            sheet_error = None
            try:
                sheet.write_sheet(state["items"], roots.allowed / "review-sheet.csv", roots=roots)
            except (ValueError, OSError) as exc:
                sheet_error = exc
            page.write_page(
                state["items"],
                state.get("presets", {}),
                roots=roots,
                sheet_message=_safe_text(sheet_error, roots) if sheet_error else "",
            )
            if page.check_links(roots.allowed / "index.html", roots=roots):
                raise ValueError("generated page contains unresolved links")
            if sheet_error is not None:
                raise sheet_error
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
            _build_groups(selected, state, roots, force_cpu=args.force_cpu)
            attempted.update(item.stem for item in selected)
        if stage != "page":
            _json_write(state_path, state, roots)
    scope = [item for item in state["items"] if item["item"] in attempted]
    if args.stage == "page":
        scope = state["items"]
    accounted = sum(item["status"] != "pending" for item in scope)
    pending = len(select.pending_items(state["items"]))
    failures = sum(_failed(item) for item in scope)
    print(
        f"{args.stage}: completed; {accounted} items accounted for; "
        f"failed={failures}, pending={pending}"
    )
    if failures:
        print(
            "reviewpack: build/viewing-aid failures recorded; see Not built on the page",
            file=sys.stderr,
        )
    if "page" in stages and (
        pending or page.pending_presets(state.get("presets", {}), roots=roots)
    ):
        return 2
    if failures:
        return 1
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run a review-pack stage, all stages, or a strict owner-sheet tally.

    Args:
        argv: CLI arguments, or the process arguments when absent.

    Returns:
        Zero for completion, one for item failures, or two for pending pages or input errors.
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
        with _stage_lock(roots):
            return _run_stages(args, roots)
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
