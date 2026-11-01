"""WP5.1 acceptance helpers for the shipped runner and independent file readers.

All write locations are supplied by a node under its ``tmp_path``. These helpers
do not open the footage folder or change product behavior.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import re
import subprocess
import sys
import threading
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray
from PIL import Image as PILImage

import headless_export as he
import video_fidelity as vf
from clearwater.color import decode_filter
from clearwater.interfaces import CorrectionMethod, Image, Statistics
from clearwater.interfaces.video import VideoStreamInfo
from clearwater.io.video import find_tool
from clearwater.jobs.export_seam import ExportJobs
from container_spike import compare


@dataclass(frozen=True)
class RunnerResult:
    """One CLI invocation and its names-only record.

    Attributes:
        status: The actual exit status.
        record: The JSON record written by the shipped runner.
        stdout: The runner's printed summary.
        stderr: Its progress and warning text.
    """

    status: int
    record: dict[str, Any]
    stdout: str
    stderr: str


def assert_names_only(value: object, *, folders: Sequence[Path] = ()) -> None:
    """Reject absolute paths recursively in a record or a printed surface.

    Args:
        value: JSON-compatible data or printed text.
        folders: Known folders, including spellings a generic path check may miss.
    """
    if isinstance(value, Mapping):
        for key, entry in value.items():
            assert_names_only(key, folders=folders)
            assert_names_only(entry, folders=folders)
    elif isinstance(value, (list, tuple)):
        for entry in value:
            assert_names_only(entry, folders=folders)
    elif isinstance(value, str):
        assert not re.search(r"[A-Za-z]:[\\/]|\\\\|(?:^|[\s\"'=])/[\w.]", value), (
            "absolute path leaked into a record or printed surface"
        )
        normal = value.replace("\\", "/").casefold()
        for folder in folders:
            for spelling in (str(folder), str(folder.absolute())):
                assert spelling.replace("\\", "/").casefold() not in normal, (
                    "known folder leaked into a record or printed surface"
                )


def runner_arguments(
    sources: Sequence[Path], root: Path, *, out: Path | None = None, extra: Sequence[str] = ()
) -> list[str]:
    """Build CLI arguments with explicit scratch output, settings, cache and record.

    Args:
        sources: Read-only input files.
        root: A fresh invocation folder under the node's temporary root.
        out: Shared output folder for collision tests; otherwise ``root/out``.
        extra: Literal CLI options, including backend selection.

    Returns:
        Arguments for ``headless_export.main``.
    """
    root.mkdir(parents=True, exist_ok=True)
    output = root / "out" if out is None else out
    for folder in (output, root / "settings", root / "cache"):
        folder.mkdir(parents=True, exist_ok=True)
    return [
        *(str(source) for source in sources),
        "--out",
        str(output),
        "--settings-dir",
        str(root / "settings"),
        "--cache-dir",
        str(root / "cache"),
        "--record",
        str(root / "record.json"),
        *extra,
    ]


def runner_command(arguments: Sequence[str]) -> list[str]:
    """Return the shipped script's subprocess command using this interpreter.

    Args:
        arguments: Arguments from ``runner_arguments``.

    Returns:
        A shell-independent command vector.
    """
    return [sys.executable, str(Path(he.__file__).resolve()), *arguments]


def _result(status: int, sources: Sequence[Path], root: Path, out: Path | None) -> RunnerResult:
    record = json.loads((root / "record.json").read_text(encoding="utf-8"))
    stdout = (root / "stdout.log").read_text(encoding="utf-8")
    stderr = (root / "stderr.log").read_text(encoding="utf-8")
    folders = [root, root / "cache", root / "settings", out or root / "out"]
    folders.extend(source.parent for source in sources)
    assert_names_only([record, stdout, stderr], folders=folders)
    assert record["schema"] == 1
    assert [item["source"] for item in record["items"]] == [s.name for s in sources]
    for item in record["items"]:
        for name in [item["source"], *item["outputs"]]:
            assert name and "/" not in name and "\\" not in name
    return RunnerResult(status, record, stdout, stderr)


def run_main(
    sources: Sequence[Path],
    root: Path,
    *,
    out: Path | None = None,
    extra: Sequence[str] = ("--force-cpu",),
    exports: ExportJobs | None = None,
) -> RunnerResult:
    """Call the shipped ``main`` and validate its record and printed path redaction.

    Args:
        sources: Read-only input files.
        root: A fresh invocation folder under ``tmp_path``.
        out: An optional shared output folder.
        extra: CLI options; CPU is the default for light acceptance nodes.
        exports: Optional composition-root engine with a test recording seam.

    Returns:
        The actual status, record and printed text; failures are not softened.
    """
    args = runner_arguments(sources, root, out=out, extra=extra)
    with (
        (root / "stdout.log").open("w", encoding="utf-8") as stdout,
        (root / "stderr.log").open("w", encoding="utf-8") as stderr,
        contextlib.redirect_stdout(stdout),
        contextlib.redirect_stderr(stderr),
    ):
        status = he.main(args, exports=exports)
    return _result(status, sources, root, out)


def run_subprocess(
    sources: Sequence[Path], root: Path, *, extra: Sequence[str], timeout: float = 120
) -> RunnerResult:
    """Run the shipped process to completion with bounded waits and file-backed logs.

    Args:
        sources: Read-only input files.
        root: A fresh invocation folder under ``tmp_path``.
        extra: CLI options.
        timeout: Maximum seconds; ``subprocess.run`` kills and reaps on expiry.

    Returns:
        The same checked record as the in-process helper.
    """
    args = runner_arguments(sources, root, extra=extra)
    with (
        (root / "stdout.log").open("wb") as stdout,
        (root / "stderr.log").open("wb") as stderr,
    ):
        done = subprocess.run(
            runner_command(args), stdout=stdout, stderr=stderr, timeout=timeout, check=False
        )
    return _result(done.returncode, sources, root, None)


def only_output(result: RunnerResult, out: Path) -> Path:
    """Require one successful item and return its existing output under ``out``.

    Args:
        result: A completed runner invocation.
        out: Its output folder.

    Returns:
        The sole output file.
    """
    assert result.status == 0, result.record
    (item,) = result.record["items"]
    assert item["state"] in ("done", "done with warnings"), item
    (name,) = item["outputs"]
    assert isinstance(name, str)
    path = out / name
    assert path.is_file(), name
    return path


def file_md5(path: Path) -> str:
    """Hash a read-only file without loading it all into memory.

    Args:
        path: The file to read.

    Returns:
        Its hexadecimal MD5, used only for source/overwrite identity.
    """
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "md5").hexdigest()


def pillow_rgb(path: Path) -> NDArray[np.uint8]:
    """Read RGB8 pixels with Pillow, deliberately without EXIF transposition.

    Args:
        path: An output PNG or source still.

    Returns:
        An independent copy of the decoded RGB pixels.
    """
    with PILImage.open(path) as image:
        return np.array(image.convert("RGB"), dtype=np.uint8)


def _ffmpeg_raw(args: Sequence[str], scratch: Path) -> bytes:
    scratch.mkdir(parents=True, exist_ok=True)
    with (scratch / "decoded.raw").open("wb") as raw, (scratch / "ffmpeg.log").open("wb") as log:
        done = subprocess.run(
            [str(find_tool("ffmpeg")), "-nostdin", "-hide_banner", "-v", "error", *args],
            stdout=raw,
            stderr=log,
            timeout=120,
            check=False,
        )
    assert done.returncode == 0, "FFmpeg decode failed; see ffmpeg.log"
    return (scratch / "decoded.raw").read_bytes()


def ffmpeg_png_rgb(path: Path, scratch: Path, *, width: int, height: int) -> NDArray[np.uint8]:
    """Read a PNG with FFmpeg's RGB24 decoder, independently of Pillow.

    Args:
        path: The output PNG.
        scratch: Where raw pixels and FFmpeg stderr are written.
        width: Expected pixel width.
        height: Expected pixel height.

    Returns:
        The one decoded RGB8 frame, without a viewer-side EXIF transform.
    """
    data = _ffmpeg_raw(["-i", str(path), "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"], scratch)
    assert len(data) == width * height * 3, "PNG decode has unexpected geometry/frame count"
    return np.frombuffer(data, dtype=np.uint8).reshape(height, width, 3)


def assert_output_orientation(path: Path) -> None:
    """Require no pending output EXIF rotation, for honoring and ignoring viewers.

    Args:
        path: The output PNG.
    """
    with PILImage.open(path) as image:
        assert image.getexif().get(274) in (None, 1), "output EXIF Orientation is not upright"


def decode_video_rgb(
    path: Path, stream: VideoStreamInfo, scratch: Path, *, frames: int | None = None
) -> NDArray[np.float64]:
    """Decode unrotated video with the color-pair command, in 1/255 units.

    Args:
        path: A read-only source or output clip.
        stream: Source geometry and color convention, shared by the pair.
        scratch: Where the raw decode and stderr are written.
        frames: Optional leading-frame limit.

    Returns:
        ``(N, H, W, 3)`` RGB; 8-bit samples or 16-bit RGB scaled to 255.
    """
    deep = stream.bit_depth > 8
    vf_text = decode_filter(stream) + (",format=gbrp16le" if deep else "")
    args = [
        "-noautorotate",
        "-i",
        str(path),
        "-map",
        "0:v:0",
        "-an",
        "-sn",
        "-dn",
        "-vf",
        vf_text,
    ]
    if frames is not None:
        args += ["-frames:v", str(frames)]
    args += ["-fps_mode", "passthrough", "-f", "rawvideo", "pipe:1"]
    data = _ffmpeg_raw(args, scratch)
    dtype = np.dtype("<u2") if deep else np.dtype("u1")
    size = stream.width * stream.height * 3 * dtype.itemsize
    assert data and len(data) % size == 0, "empty or short video decode"
    planar = np.frombuffer(data, dtype=dtype).reshape(-1, 3, stream.height, stream.width)
    rgb = planar[:, [2, 0, 1]].transpose(0, 2, 3, 1).astype(np.float64)
    return rgb * (255.0 / 65535.0) if deep else rgb


def assert_fidelity(record: Mapping[str, Any]) -> None:
    """Require all mandatory/required comparisons and the instrument roster to agree.

    Args:
        record: ``video_fidelity.fidelity_record`` output.
    """
    summary = record["summary"]
    assert summary["mandatory_and_required_all_same"], summary["different_items"]
    items = {item["name"]: item for item in record["items"]}
    assert items[vf._ROSTER_ITEM]["status"] == compare.SAME


def fidelity_record(source: Path, output: Path, scratch: Path) -> dict[str, Any]:
    """Save the instrument's comparison with file names in place of its paths.

    Args:
        source: Read-only input clip.
        output: Exported clip under the node's temporary folder.
        scratch: Where the names-only fidelity JSON is saved.

    Returns:
        The unmodified comparisons, with only the two path fields redacted.
    """
    record = vf.fidelity_record(source, output)
    record.update(source=source.name, output=output.name)
    assert_names_only(record, folders=[source.parent, output.parent, scratch])
    scratch.mkdir(parents=True, exist_ok=True)
    (scratch / "fidelity.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def best_effort_presence(record: Mapping[str, Any]) -> dict[str, dict[str, bool]]:
    """Extract presence only, never metadata payloads, from best-effort comparisons.

    Args:
        record: The fidelity instrument's record.

    Returns:
        Creation-time, GPMF, timecode and camera-atom rows with source/output presence.
    """

    def present(value: Any) -> bool:
        if isinstance(value, Mapping):
            if "count" in value:
                return bool(value["count"])
            return any(present(entry) for entry in value.values())
        return bool(value) and value != "absent"

    prefixes = ("creation time:", vf.TELEMETRY_ITEM, "timecode", "camera atoms:")
    return {
        item["name"]: {side: present(item[side]) for side in ("source", "output")}
        for item in record["items"]
        if item["class"] == compare.BEST_EFFORT and item["name"].startswith(prefixes)
    }


def png_provenance(path: Path) -> dict[str, Any] | None:
    """Parse Clearwater's uncompressed PNG iTXt provenance with Pillow.

    Args:
        path: An output PNG.

    Returns:
        The parsed provenance or None, as in the existing WP4.1 reader.
    """
    with PILImage.open(path) as image:
        image.load()
        text = image.info.get("clearwater-provenance")
    result = None if text is None else cast(dict[str, Any], json.loads(text))
    assert_names_only(result, folders=[path.parent])
    return result


def video_provenance(path: Path, scratch: Path) -> dict[str, Any] | None:
    """Parse MP4 comment provenance with the existing sink test's ffprobe form.

    Args:
        path: An output MP4.
        scratch: Where the ffprobe JSON and stderr are written.

    Returns:
        The parsed comment object or None when absent/empty.
    """
    scratch.mkdir(parents=True, exist_ok=True)
    with (scratch / "probe.json").open("wb") as stdout, (scratch / "probe.log").open("wb") as log:
        done = subprocess.run(
            [
                str(find_tool("ffprobe")),
                "-v",
                "error",
                "-of",
                "json",
                "-show_entries",
                "format_tags=comment",
                str(path),
            ],
            stdout=stdout,
            stderr=log,
            timeout=60,
            check=False,
        )
    assert done.returncode == 0, "provenance probe failed; see probe.log"
    document = json.loads((scratch / "probe.json").read_bytes())
    text = document.get("format", {}).get("tags", {}).get("comment")
    result = None if not text else cast(dict[str, Any], json.loads(text))
    assert_names_only(result, folders=[path.parent])
    return result


class RenderDigests:
    """Delegate IF-3 while hashing the returned pixels by input pts before encoding.

    Attributes:
        renders: Pts ticks to dtype/shape/C-order SHA-256.
        devices: Devices actually used to render.
    """

    def __init__(self, inner: CorrectionMethod) -> None:
        """Wrap the product method without changing its parameters or algorithms."""
        self._inner = inner
        self.id, self.label = inner.id, inner.label
        self.parameters, self.stages = inner.parameters, inner.stages
        self.renders: dict[int, str] = {}
        self.devices: set[str] = set()
        self._lock = threading.Lock()

    def analyze(
        self, stage: str, image: Image, params: Mapping[str, Any], earlier: Mapping[str, Statistics]
    ) -> Statistics:
        """Delegate a real analysis stage unchanged."""
        return self._inner.analyze(stage, image, params, earlier)

    def closed_form(
        self,
        stage: str,
        params: Mapping[str, Any],
        earlier: Mapping[str, Statistics],
        measured: Statistics,
    ) -> Statistics | None:
        """Delegate the optional closed-form update unchanged."""
        return self._inner.closed_form(stage, params, earlier, measured)

    def render(
        self, image: Image, params: Mapping[str, Any], statistics: Mapping[str, Statistics]
    ) -> Image:
        """Digest returned pixels, rather than the oracle's input statistics."""
        result = self._inner.render(image, params, statistics)
        pts = getattr(image, "pts_ticks", None)
        assert pts is not None, "N10 video render is missing pts"
        pixels: Any = result.pixels
        get = getattr(pixels, "get", None)
        host = np.ascontiguousarray(get() if callable(get) else pixels)
        digest = hashlib.sha256(f"{host.dtype.str}{host.shape}".encode("ascii"))
        digest.update(memoryview(host).cast("B"))
        with self._lock:
            assert int(pts) not in self.renders, "N10 rendered duplicate pts"
            self.renders[int(pts)] = digest.hexdigest()
            self.devices.add(result.device)
        return result


# T9 fills the node addresses alongside the report, after those modules exist.
# An empty tuple is explicitly pending; it is never evidence of a passing test.
ACCEPTANCE_NODES: dict[str, tuple[str, ...]] = {
    **{f"V{number}": () for number in range(1, 19)},
    "N10": (),
    "D91": (),
}
