"""Synthetic video fixtures made with the FFmpeg CLI (WP2.3 item 3).

Eight short clips (320 x 180, 45 frames at 30000/1001 fps, one AAC sine track, built from
``testsrc2``), each differing in the one thing it exercises: 8-bit BT.709 full range (the
HERO13 tagging), 10-bit, HLG, PQ, untagged (D54), truncated (D86), variable frame rate (D95,
D115) and rotated by a display matrix (D105). Software encoders only (libx265 and libx264, AAC),
so a machine without NVENC regenerates them. The untagged clip is H.264 because x265 always
writes a video signal type (with an explicit limited-range flag) into the stream; x264 writes
none. Every sample carries a measured fact record: the ffprobe stream fields, the video
signal-type syntax read from the bitstream (``trace_headers``), the packet pts list, and the
decoded-frame hashes. :func:`build` refuses to write a sample whose measurements differ from its
intent.

Encoder settings that make the clips repeatable: no B-frames, no x265 version SEI (``info=0``),
FFmpeg ``bitexact`` flags, no metadata copied. Byte-reproducibility is not claimed for other
FFmpeg builds; the decoded-frame hash is what a regeneration check compares.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

if not __package__:
    # Script mode: sys.path[0] is tools/fixtures; put tools first for the sibling packages.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fixtures import manifest
from spike_io.guard import WriteGuard

WIDTH = 320
"""Frame width of the video samples."""

HEIGHT = 180
"""Frame height of the video samples."""

FRAME_RATE = "30000/1001"
"""The nominal frame rate (the GoPro rate)."""

DURATION_S = 1.5
"""The duration of the constant-rate clips; at 30000/1001 fps that is 45 frames."""

FRAMES = 45
"""The frame count of the constant-rate clips."""

VFR_FRAMES = 30
"""The frame count of the variable-frame-rate clip."""

VFR_UNIT = 1001
"""Ticks (of the 30000 Hz track clock) in one nominal frame."""

TIMESCALE = 30000
"""The video track timescale of the VFR sample (ticks per second)."""

TRUNCATE_KEEP = 0.6
"""The fraction of the source file's bytes the truncated sample keeps."""

CUT_ROTATION = 90
"""The display-matrix rotation of the rotated sample, in degrees (FFmpeg convention)."""

ROTATE_SOURCE = "vid-hevc8-bt709-full"
"""The sample the rotated and the truncated samples are made from."""

SCRATCH = "_scratch"
"""The folder inside the output where intermediate files are made; removed afterwards."""

PIX_FMT_BITS = {"yuv420p": 8, "yuvj420p": 8, "yuv420p10le": 10}
"""Bit depth of the pixel formats ffprobe reports for these samples."""

COMMON_X265 = "log-level=error:info=0:bframes=0"
"""x265 parameters every sample shares."""

BITEXACT = ["-fflags", "+bitexact", "-flags:v", "+bitexact", "-flags:a", "+bitexact"]
"""FFmpeg flags that keep build strings and random ids out of the files."""


class GenerationError(Exception):
    """A sample could not be built, or what was built is not what was intended."""


@dataclass(frozen=True)
class Tags:
    """The colour description a sample is meant to carry, in ffprobe's names.

    Attributes:
        range: ``"pc"`` (full) or ``"tv"`` (limited).
        space: ``color_space`` (the matrix).
        transfer: ``color_transfer``.
        primaries: ``color_primaries``.
        params: The encoder parameters that write them (empty for untagged).
    """

    range: str
    space: str
    transfer: str
    primaries: str
    params: str


BT709_FULL = Tags(
    "pc", "bt709", "bt709", "bt709", "range=full:colorprim=bt709:transfer=bt709:colormatrix=bt709"
)
BT709_LIMITED = Tags(
    "tv", "bt709", "bt709", "bt709", "colorprim=bt709:transfer=bt709:colormatrix=bt709"
)
HLG = Tags(
    "tv",
    "bt2020nc",
    "arib-std-b67",
    "bt2020",
    "colorprim=bt2020:transfer=arib-std-b67:colormatrix=bt2020nc",
)
PQ = Tags(
    "tv",
    "bt2020nc",
    "smpte2084",
    "bt2020",
    "colorprim=bt2020:transfer=smpte2084:colormatrix=bt2020nc",
)
UNTAGGED = Tags("unknown", "unknown", "unknown", "unknown", "")

_IF_RANGE = {"pc": "full", "tv": "limited"}
"""ffprobe's ``color_range`` words in the ``ColorDescription.range`` words."""

D54_COLOR = {
    "primaries": "bt709",
    "transfer": "bt709",
    "matrix": "bt709",
    "range": "limited",
    "assumed": True,
}
"""What a probe should make of a stream with no colour tags (D54: BT.709 limited, assumed)."""


@dataclass(frozen=True)
class Spec:
    """The intent of one video sample.

    Attributes:
        sample_id: The manifest id.
        pix_fmt: The encoder pixel format.
        tags: The colour description.
        serves: Spec clauses and V-tests served.
        exercises: What a test uses the sample for.
        faults: ``(kind, severity)`` pairs the probe should report (WP2.2 names).
        rotation: The display-matrix rotation in degrees.
        vfr: Variable frame rate.
        truncated: The file has its tail cut off.
        codec: ``"hevc"`` (libx265) or ``"h264"`` (libx264).
    """

    sample_id: str
    pix_fmt: str
    tags: Tags
    serves: tuple[str, ...]
    exercises: str
    faults: tuple[tuple[str, str], ...] = ()
    rotation: int = 0
    vfr: bool = False
    truncated: bool = False
    codec: str = "hevc"


SPECS = (
    Spec(
        "vid-hevc8-bt709-full",
        "yuv420p",
        BT709_FULL,
        ("V4", "D54 (control: tagged)", "D55", "D105"),
        "8-bit HEVC 4:2:0 tagged BT.709 full range like the HERO13: a clean probe with no fault.",
    ),
    Spec(
        "vid-hevc10",
        "yuv420p10le",
        BT709_LIMITED,
        ("V4", "D114", "D55"),
        "10-bit HEVC 4:2:0 tagged BT.709 limited range: the 10-bit decode and output path.",
    ),
    Spec(
        "vid-hlg",
        "yuv420p10le",
        HLG,
        ("spec 6.5", "G10"),
        "HLG-tagged (arib-std-b67, bt2020) 10-bit HEVC: refused at probe.",
        faults=(("hlg", "refuse"),),
    ),
    Spec(
        "vid-pq",
        "yuv420p10le",
        PQ,
        ("spec 6.5", "G10"),
        "PQ-tagged (smpte2084, bt2020) 10-bit HEVC: refused at probe.",
        faults=(("pq", "refuse"),),
    ),
    Spec(
        "vid-untagged",
        "yuv420p",
        UNTAGGED,
        ("D54", "V4"),
        "H.264 with no video signal type in the stream and no colour box in the container: "
        "BT.709 limited is assumed and the user is warned. (x265 always writes a signal type, "
        "so this sample is H.264.)",
        faults=(("missing_tags", "warn"),),
        codec="h264",
    ),
    Spec(
        "vid-truncated",
        "yuv420p",
        BT709_FULL,
        ("D86", "V4"),
        "A valid clip with its tail bytes cut: the readable frames decode, the stream ends "
        "early and ffprobe reports a partial file.",
        faults=(("truncated", "warn"),),
        truncated=True,
    ),
    Spec(
        "vid-vfr",
        "yuv420p",
        BT709_FULL,
        ("V4", "D95", "D115"),
        "Variable frame rate: 30 frames whose durations are 1001, 1001 and 2002 ticks of a "
        "30000 Hz clock in turn.",
        vfr=True,
    ),
    Spec(
        "vid-rotated",
        "yuv420p",
        BT709_FULL,
        ("V4", "D105"),
        "A 90 degree display-matrix rotation on a landscape stream: the output keeps it.",
        rotation=CUT_ROTATION,
    ),
)
"""The video samples, in generation order (``vid-rotated`` is remuxed from ``vid-hevc8-...``)."""


# --- Running FFmpeg -----------------------------------------------------------------------


def tools_available() -> bool:
    """Return True when both ``ffmpeg`` and ``ffprobe`` are on the PATH."""
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def run_ffmpeg(guard: WriteGuard, argv: list[str], output: Path, cwd: Path) -> None:
    """Run FFmpeg with one output file, checked against the write guard first.

    ``argv`` is the command after ``ffmpeg -nostdin -hide_banner -loglevel error -y``; the output
    path is appended last, so it is the only file FFmpeg is told to write. FFmpeg runs with
    ``cwd`` as its working directory (a folder inside the output root).

    Args:
        guard: The write guard; ``output`` must resolve inside its root.
        argv: The input, filter and encoder arguments.
        output: The file to write.
        cwd: The working directory (inside the guard's root).

    Raises:
        GenerationError: FFmpeg exits non-zero.
    """
    guard.check(output)
    guard.check(cwd)
    command = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", *argv, str(output)]
    done = subprocess.run(command, cwd=cwd, capture_output=True, check=False)
    if done.returncode != 0:
        tail = done.stderr.decode("utf-8", "replace").strip()[-600:]
        raise GenerationError(f"ffmpeg failed ({done.returncode}) for {output.name}: {tail}")


def _lavfi_inputs(seconds: float) -> list[str]:
    """Return the ``testsrc2`` video and ``sine`` audio inputs."""
    return [
        "-f", "lavfi", "-i", f"testsrc2=size={WIDTH}x{HEIGHT}:rate={FRAME_RATE}:duration={seconds}",
        "-f", "lavfi", "-i", f"sine=frequency=440:sample_rate=48000:duration={DURATION_S}",
    ]  # fmt: skip


def _encode_args(spec: Spec) -> list[str]:
    """Return the encoder arguments of a sample."""
    if spec.codec == "h264":
        video_args = ["-c:v", "libx264", "-pix_fmt", spec.pix_fmt, "-x264-params", "bframes=0"]
    else:
        params = ":".join(part for part in (COMMON_X265, spec.tags.params) if part)
        video_args = ["-c:v", "libx265", "-pix_fmt", spec.pix_fmt, "-x265-params", params]
    return [
        "-map", "0:v:0", "-map", "1:a:0", *video_args,
        "-c:a", "aac", "-b:a", "64k", *BITEXACT, "-map_metadata", "-1", "-movflags", "+faststart",
    ]  # fmt: skip


def vfr_ticks(count: int = VFR_FRAMES) -> list[int]:
    """Return the intended pts list of the VFR sample, in 30000 Hz ticks.

    Durations cycle 1001, 1001, 2002: frame ``k`` is at ``1001 * (4 * (k // 3) + k % 3)``.

    Args:
        count: The number of frames.

    Returns:
        The pts of each frame.
    """
    return [VFR_UNIT * (4 * (k // 3) + k % 3) for k in range(count)]


# --- Measuring ----------------------------------------------------------------------------


def ffprobe_json(path: Path, *entries: str) -> tuple[dict[str, Any], list[str]]:
    """Run ffprobe and return its JSON and its normalised stderr lines."""
    command = ["ffprobe", "-v", "error", "-of", "json", *entries, str(path)]
    done = subprocess.run(command, capture_output=True, check=False)
    errors = [
        re.sub(r"\[[^\]@]+@ [0-9a-fA-F]+\] ", "", line).strip()
        for line in done.stderr.decode("utf-8", "replace").splitlines()
        if line.strip()
    ]
    return json.loads(done.stdout or b"{}"), errors


def _vui(path: Path) -> dict[str, int]:
    """Read the VUI colour syntax elements of the first HEVC access unit (``trace_headers``).

    Returns:
        The values of the elements that appear, by syntax-element name.
    """
    command = [
        "ffmpeg", "-nostdin", "-hide_banner", "-v", "verbose", "-i", str(path),
        "-map", "0:v:0", "-c:v", "copy", "-bsf:v", "trace_headers", "-frames:v", "1",
        "-f", "null", "-",
    ]  # fmt: skip
    done = subprocess.run(command, capture_output=True, check=False)
    wanted = (
        "video_signal_type_present_flag",
        "video_full_range_flag",
        "colour_description_present_flag",
        "colour_primaries",
        "transfer_characteristics",
        "matrix_coefficients",
    )
    found: dict[str, int] = {}
    for line in done.stderr.decode("utf-8", "replace").splitlines():
        match = re.search(r"\s(\w+)\s+[01]+ = (\d+)\s*$", line)
        if match and match.group(1) in wanted and match.group(1) not in found:
            found[match.group(1)] = int(match.group(2))
    return found


def decode_hashes(path: Path) -> dict[str, Any]:
    """Decode the video stream and hash each frame and the frame times.

    Uses ``ffmpeg -f framehash -hash sha256`` on the decoded frames in their native pixel
    format; reads what is readable (a truncated file ends early).

    Args:
        path: The video file.

    Returns:
        ``frames`` (count decoded), ``frames_sha256`` (SHA-256 of the per-frame hashes joined by
        newlines), ``pts_sha256`` (SHA-256 of the decoded pts, in ticks of the framehash time
        base, joined by commas) and ``time_base``.
    """
    command = [
        "ffmpeg", "-nostdin", "-hide_banner", "-v", "error", "-i", str(path),
        "-map", "0:v:0", "-f", "framehash", "-hash", "sha256", "-",
    ]  # fmt: skip
    done = subprocess.run(command, capture_output=True, check=False)
    hashes, pts, time_base = [], [], ""
    for line in done.stdout.decode("ascii", "replace").splitlines():
        if line.startswith("#tb"):
            time_base = line.split(":", 1)[1].strip()
        elif line and not line.startswith("#"):
            fields = [part.strip() for part in line.split(",")]
            pts.append(fields[2])
            hashes.append(fields[5])
    return {
        "frames": len(hashes),
        "frames_sha256": hashlib.sha256("\n".join(hashes).encode("ascii")).hexdigest(),
        "pts_sha256": hashlib.sha256(",".join(pts).encode("ascii")).hexdigest(),
        "time_base": time_base,
    }


def measure(path: Path) -> dict[str, Any]:
    """Measure a written video: ffprobe fields, VUI syntax, packet pts and decoded hashes.

    Args:
        path: The video file.

    Returns:
        The facts record stored in the manifest.
    """
    data, errors = ffprobe_json(path, "-show_streams", "-show_format")
    streams = data.get("streams", [])
    video = next(s for s in streams if s["codec_type"] == "video")
    audio = [s for s in streams if s["codec_type"] == "audio"]
    other = [s for s in streams if s["codec_type"] not in ("video", "audio")]
    rotation = 0
    for side in video.get("side_data_list", []):
        if side.get("side_data_type") == "Display Matrix":
            rotation = round(side["rotation"]) % 360
    packets, packet_errors = ffprobe_json(
        path, "-select_streams", "v:0", "-show_entries", "packet=pts"
    )
    errors = sorted(set(errors + packet_errors))  # reading the packets finds a cut-off tail
    ticks_per_second = int(video["time_base"].split("/")[1]) // int(
        video["time_base"].split("/")[0]
    )
    ticks = [int(p["pts"]) for p in packets.get("packets", []) if "pts" in p]
    durations = sorted({b - a for a, b in itertools.pairwise(ticks)})
    tag_text = json.dumps(
        [s.get("tags", {}) for s in streams] + [data.get("format", {}).get("tags", {})]
    )
    return {
        "container": data.get("format", {}).get("format_name"),
        "video": {
            "codec": video["codec_name"],
            "profile": video.get("profile"),
            "pix_fmt": video["pix_fmt"],
            "bit_depth": PIX_FMT_BITS[video["pix_fmt"]],
            "width": video["width"],
            "height": video["height"],
            "color_range": video.get("color_range", "unknown"),
            "color_space": video.get("color_space", "unknown"),
            "color_transfer": video.get("color_transfer", "unknown"),
            "color_primaries": video.get("color_primaries", "unknown"),
            "r_frame_rate": video["r_frame_rate"],
            "avg_frame_rate": video["avg_frame_rate"],
            "time_base": video["time_base"],
            "nb_frames": int(video["nb_frames"]) if "nb_frames" in video else None,
            "rotation": rotation,
            "vui": _vui(path),
        },
        "audio": [
            {
                "codec": a["codec_name"],
                "sample_rate": int(a["sample_rate"]),
                "channels": a["channels"],
            }
            for a in audio
        ],
        "data_streams": [s["codec_type"] for s in other],
        "has_location_tag": "location" in tag_text.lower(),
        "pts": {
            "ticks_per_second": ticks_per_second,
            "count": len(ticks),
            "ticks": ticks if len(ticks) <= 64 else None,
            "sha256": hashlib.sha256(",".join(map(str, ticks)).encode("ascii")).hexdigest(),
            "durations": durations,
            "variable": len(durations) > 1,
        },
        "decoded": decode_hashes(path),
        "ffprobe_errors": errors,
    }


# --- Intent against measurement -----------------------------------------------------------


def intended_frame_rate(spec: Spec) -> str:
    """Return the average frame rate ffprobe should report, as ``numerator/denominator``.

    A constant-rate clip is 30000/1001; the VFR clip's average is its frame count over its
    duration (the last pts plus one nominal frame), reduced.
    """
    if not spec.vfr:
        return FRAME_RATE
    rate = Fraction(VFR_FRAMES * TIMESCALE, vfr_ticks()[-1] + VFR_UNIT)
    return f"{rate.numerator}/{rate.denominator}"


def expectation(spec: Spec) -> dict[str, Any]:
    """Return the ``expect.probe`` block of a sample (``ProbeResult``, ``VideoStreamInfo`` names).

    Built from the intent, never from the file. HLG and PQ streams get no ``color``: they are
    refused at probe and never reach a ``ColorDescription``. An untagged stream is expected
    to come out with the D54 defaults and ``assumed`` True.
    """
    bits = PIX_FMT_BITS[spec.pix_fmt]
    video: dict[str, Any] = {
        "codec": spec.codec,
        "width": WIDTH,
        "height": HEIGHT,
        "bit_depth": bits,
        "frame_rate": intended_frame_rate(spec),
        "time_base": f"1/{TIMESCALE}",
        "nb_frames": VFR_FRAMES if spec.vfr else FRAMES,
        "rotation": spec.rotation,
        "vfr": spec.vfr,
    }
    if spec.tags is UNTAGGED:
        video["color"] = {**D54_COLOR, "bit_depth": bits}
    elif spec.tags in (BT709_FULL, BT709_LIMITED):
        video["color"] = {
            "primaries": spec.tags.primaries,
            "transfer": spec.tags.transfer,
            "matrix": spec.tags.space,
            "range": _IF_RANGE[spec.tags.range],
            "bit_depth": bits,
            "assumed": False,
        }
    return {
        "container": "mov,mp4,m4a,3gp,3g2,mj2",
        "video": video,
        "audio": [{"codec": "aac", "sample_rate": 48000, "channels": 1}],
        "data": [],
    }


def mismatches(spec: Spec, facts: dict[str, Any]) -> list[str]:
    """Compare measured facts with a sample's intent; return what differs.

    Args:
        spec: The intended sample.
        facts: The record :func:`measure` returned.

    Returns:
        One message per difference; empty when the file is what the spec says.
    """
    video = facts["video"]
    wrong = []

    def need(name: str, got: object, want: object) -> None:
        if got != want:
            wrong.append(f"{spec.sample_id}: {name} is {got!r}, intended {want!r}")

    need("codec", video["codec"], spec.codec)
    need("container", facts["container"], "mov,mp4,m4a,3gp,3g2,mj2")
    need("average frame rate", video["avg_frame_rate"], intended_frame_rate(spec))
    need("time base", video["time_base"], f"1/{TIMESCALE}")
    if not spec.truncated:
        need("container frame count", video["nb_frames"], VFR_FRAMES if spec.vfr else FRAMES)
    need("size", (video["width"], video["height"]), (WIDTH, HEIGHT))
    need("bit depth", video["bit_depth"], PIX_FMT_BITS[spec.pix_fmt])
    need("color_space", video["color_space"], spec.tags.space)
    need("color_transfer", video["color_transfer"], spec.tags.transfer)
    need("color_primaries", video["color_primaries"], spec.tags.primaries)
    need("rotation", video["rotation"], spec.rotation)
    need(
        "audio",
        [(a["codec"], a["sample_rate"], a["channels"]) for a in facts["audio"]],
        [("aac", 48000, 1)],
    )
    need("variable frame rate", facts["pts"]["variable"], spec.vfr)
    need("GPS or location tag", facts["has_location_tag"], False)
    need("data streams", facts["data_streams"], [])
    vui = video["vui"]
    if spec.tags is UNTAGGED:
        need("VUI video_signal_type_present_flag", vui.get("video_signal_type_present_flag"), 0)
        need(
            "VUI colour_description_present_flag", vui.get("colour_description_present_flag"), None
        )
        need("color_range", video["color_range"], "unknown")
    else:
        need("VUI colour_description_present_flag", vui.get("colour_description_present_flag"), 1)
        need(
            "VUI full range", vui.get("video_full_range_flag"), 1 if spec.tags.range == "pc" else 0
        )
        need("range", video["color_range"], spec.tags.range)
    if spec.vfr:
        need("pts ticks", facts["pts"]["ticks"], vfr_ticks())
        need("decoded frames", facts["decoded"]["frames"], VFR_FRAMES)
    elif spec.truncated:
        container = video["nb_frames"]
        decoded = facts["decoded"]["frames"]
        if not (container == FRAMES and 0 < decoded < container):
            wrong.append(
                f"{spec.sample_id}: container says {container} frames, {decoded} decode; "
                f"need {FRAMES} and a smaller non-zero count"
            )
        if not any("partial file" in line for line in facts["ffprobe_errors"]):
            wrong.append(f"{spec.sample_id}: ffprobe did not report a partial file")
    else:
        need("decoded frames", facts["decoded"]["frames"], FRAMES)
        need("ffprobe errors", facts["ffprobe_errors"], [])
    return wrong


# --- Building -----------------------------------------------------------------------------


def build(guard: WriteGuard, out: Path) -> list[manifest.Entry]:
    """Write every video sample under ``out/video`` and return the manifest entries.

    Needs ``ffmpeg`` and ``ffprobe`` on the PATH. Intermediate files go to ``out/_scratch`` and
    are removed.

    Args:
        guard: The write guard whose root is ``out``.
        out: The output folder.

    Returns:
        One entry per sample.

    Raises:
        GenerationError: FFmpeg is missing or fails, or a written file differs from its spec.
    """
    if not tools_available():
        raise GenerationError("ffmpeg and ffprobe must be on the PATH to build the video samples")
    folder = guard.check(out / "video")
    folder.mkdir(parents=True, exist_ok=True)
    scratch = guard.check(out / SCRATCH)
    scratch.mkdir(parents=True, exist_ok=True)
    entries: list[manifest.Entry] = []
    sources: dict[str, Path] = {}
    try:
        for spec in SPECS:
            target = folder / f"{spec.sample_id.removeprefix('vid-')}.mp4"
            extra: dict[str, Any] = {}
            if spec.vfr:
                setpts = "setpts=4*floor(N/3)+mod(N\\,3)"
                run_ffmpeg(
                    guard,
                    [*_lavfi_inputs(4), "-vf", setpts, "-fps_mode", "passthrough",
                     "-frames:v", str(VFR_FRAMES), "-video_track_timescale", str(TIMESCALE),
                     *_encode_args(spec)],
                    target, scratch,
                )  # fmt: skip
                extra["pts_ticks_intended"] = vfr_ticks()
            elif spec.rotation:
                run_ffmpeg(
                    guard,
                    ["-display_rotation", str(spec.rotation), "-i", str(sources[ROTATE_SOURCE]),
                     "-c", "copy", "-movflags", "+faststart", "-fflags", "+bitexact",
                     "-map_metadata", "-1"],
                    target, scratch,
                )  # fmt: skip
            elif spec.truncated:
                source = sources[ROTATE_SOURCE]
                data = source.read_bytes()
                kept = int(len(data) * TRUNCATE_KEEP)
                guard.check(target)
                target.write_bytes(data[:kept])
                extra.update(
                    cut_source=source.name,
                    source_bytes=len(data),
                    kept_bytes=kept,
                    cut_bytes=len(data) - kept,
                    kept_fraction=TRUNCATE_KEEP,
                )
            else:
                run_ffmpeg(
                    guard, [*_lavfi_inputs(DURATION_S), *_encode_args(spec)], target, scratch
                )
            sources[spec.sample_id] = target
            facts = measure(target)
            facts.update(extra)
            problems = mismatches(spec, facts)
            if problems:
                raise GenerationError("; ".join(problems))
            expected = manifest.expect(
                faults=[manifest.fault(kind, severity) for kind, severity in spec.faults],
                probe=expectation(spec),
            )
            entries.append(
                manifest.entry(
                    sample_id=spec.sample_id,
                    group="video",
                    kind="mp4",
                    storage="committed",
                    path=f"video/{target.name}",
                    serves=spec.serves,
                    exercises=spec.exercises,
                    expected=expected,
                    facts=facts,
                    file=target,
                    byte_reproducible=False,
                )
            )
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    return entries
