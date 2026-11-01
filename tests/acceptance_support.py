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


def _test_nodes(module: str, *functions: str) -> tuple[str, ...]:
    return tuple(f"tests/{module}.py::{function}" for function in functions)


# Function addresses represent every parameterized instance of that function.
# T9 validates these without executing the referenced tests or spawning pytest.
# The final gate checks expanded collection identity; T10 uses this same roster.
ACCEPTANCE_NODES: dict[str, tuple[str, ...]] = {
    "V1": (
        *_test_nodes(
            "test_methods_compensation",
            "test_ancuti_chain_matches_prototype",
            "test_ancuti_render_matches_prototype_on_supplied_values",
            "test_c3_matches_prototype",
            "test_c3_matches_prototype_off_default",
            "test_uniform_image",
            "test_near_zero_red_cap_binds_and_none_compensates",
            "test_cap_binding_not_binding_and_none",
            "test_blue_off_leaves_blue_and_green_unchanged",
            "test_c3_mask_below_at_and_above_threshold",
        ),
        *_test_nodes(
            "test_methods_white_balance",
            "test_measure_closed_form_and_render_match_prototype",
            "test_near_zero_red_hits_the_floor_and_the_clamp",
            "test_clamp_binds_as_d99_says",
        ),
        *_test_nodes(
            "test_methods_fusion_prototype",
            "test_fusion_inputs_with_supplied_bounds",
            "test_weights",
            "test_multiscale_fusion",
        ),
        *_test_nodes("test_methods_fusion", "test_v1_edge_cases"),
        *_test_nodes(
            "test_methods_assembly", "test_v1_stage_measured_with_the_supplied_earlier_records"
        ),
        *_test_nodes(
            "test_methods_assembly_prototype",
            "test_analyze_against_statistics_of",
            "test_render_against_correct_with_the_same_record",
            "test_cpu_against_gpu_within_ad11",
        ),
    ),
    "V2": (),
    "V3": _test_nodes(
        "test_wp42_v3_product",
        "test_the_lossless_clips_decode_inside_wp39s_envelope",
        "test_ad14_bound_with_the_product_method",
        "test_v3_ratio_on_the_jittering_patch_clip_with_the_product_method",
    ),
    "V4": (
        *_test_nodes(
            "test_v51_video_acceptance",
            "test_v4_runner_preserves_fixture_fidelity",
            "test_v4_truncated_runner_batch_obeys_d86",
            "test_v4_real_trim_records_best_effort_presence",
        ),
        *_test_nodes(
            "test_wp42_video_path",
            "test_v4_through_the_composition_on_the_cpu",
            "test_v4_through_the_composition_on_the_gpu_with_device_frames",
        ),
        *_test_nodes(
            "test_jobs_export_video",
            "test_v4_every_decodable_sample_through_the_engine",
            "test_v4_synthetic_5k3_8_7_clip",
            "test_gx011627_through_the_engine_keeps_every_mandatory_and_required_item",
        ),
    ),
    "V5": (
        *_test_nodes("test_wp41_photo_path", "test_v5_bit_depth_icc_exif_and_provenance"),
        *_test_nodes(
            "test_v51_photo_acceptance",
            "test_v5_jpeg_two_readers_and_pose",
            "test_v5_heic_two_readers_and_ad24",
        ),
    ),
    "V6": (
        *_test_nodes(
            "test_v51_video_acceptance",
            "test_v6_hdr_refusals_do_not_stop_batch",
            "test_v6_untagged_runner_warns_bt709_limited",
            "test_v4_truncated_runner_batch_obeys_d86",
        ),
        *_test_nodes(
            "test_v51_shell_acceptance", "test_v6_real_untagged_shell_warns_bt709_limited"
        ),
        *_test_nodes(
            "test_headless_export",
            "test_refused_items_fail_and_the_batch_continues",
            "test_damaged_photos_are_failed_items_and_the_batch_continues",
        ),
        *_test_nodes(
            "test_app_wiring",
            "test_g10_damaged_unsupported_and_untagged_inputs_get_a_readable_message",
        ),
    ),
    "V7": _test_nodes(
        "test_app_v7",
        "test_v7_a_b_analysis_and_scrubbing",
        "test_v7_c_e_export_and_a_full_render_during_it",
        "test_v7_d_a_batch_of_300_stills",
        "test_v7_f_start_up_with_a_slow_cache_open",
    ),
    "V8": (
        *_test_nodes(
            "test_app_v8_v18",
            "test_v8_photo_preview_at_1_1_and_k_2_and_4_against_the_downscaled_export",
            "test_v8_photo_k_above_1_on_real_sized_content",
            "test_dr75_an_nclx_only_p3_photo_is_displayed_through_the_profile_its_export_embeds",
            "test_v8_video_pre_encode_through_the_harness_on_the_shells_frame",
        ),
        *_test_nodes("test_methods_assembly_v8", "test_v8_preview_against_the_downscaled_export"),
    ),
    "V9": (
        *_test_nodes("test_wp41_photo_path", "test_v9_neutral_is_the_identity"),
        *_test_nodes(
            "test_wp42_video_path", "test_v9_neutral_parameters_reproduce_the_decoded_source"
        ),
        *_test_nodes("test_v51_video_acceptance", "test_v9_neutral_runner_postencode"),
        *_test_nodes("test_color_roundtrip", "test_pair_round_trip_per_sample"),
    ),
    "V10": (
        *_test_nodes(
            "test_wp41_photo_path",
            "test_v10_cross_format_clash_is_numbered",
            "test_v10_an_existing_output_is_never_overwritten",
            "test_v10_custom_suffix",
        ),
        *_test_nodes(
            "test_v51_video_acceptance",
            "test_v10_repeated_video_exports_are_numbered",
            "test_v10_existing_video_output_is_unchanged",
            "test_v10_mov_mp4_share_one_numbering_sequence",
        ),
    ),
    "V11": (
        *_test_nodes(
            "test_v51_photo_acceptance",
            "test_v11_png_disk_full_removes_partial_output",
            "test_v11_photo_crash_leftovers_are_cleaned_at_start",
            "test_d85_same_file_cleanup_preserves_installed_final",
        ),
        *_test_nodes(
            "test_jobs_export_video",
            "test_v11_an_encoder_killed_mid_stream_leaves_no_partial_output",
            "test_a_cancel_mid_encode_leaves_nothing_and_keeps_earlier_outputs",
            "test_a_cancel_during_the_product_sinks_close_is_aborted_and_leaves_nothing",
            "test_v11_a_killed_export_process_leaves_only_a_temporary_that_is_cleaned_up",
        ),
        *_test_nodes(
            "test_jobs_export",
            "test_cancel_at_each_phase_leaves_nothing",
            "test_disk_full_from_the_sink_is_named_and_leaves_nothing",
        ),
        *_test_nodes(
            "test_app_leftovers", "test_v11_leftovers_of_a_crash_are_removed_at_the_next_start"
        ),
    ),
    "V12": (),
    "V13": _test_nodes("test_config_presets", "test_v13_export_then_import_reproduces_the_set"),
    "V14": (),
    "V15": (),
    "V16": (),
    "V17": (
        *_test_nodes(
            "test_wp42_video_path", "test_v17_a_reopen_skips_the_decode_and_renders_the_same_frames"
        ),
        *_test_nodes(
            "test_analysis_engine",
            "test_a_complete_entry_skips_the_decode_pass_and_gives_the_same_statistics",
        ),
    ),
    "V18": (
        *_test_nodes(
            "test_v51_shell_acceptance", "test_v18_real_trim_preview_precedes_analysis_and_updates"
        ),
        *_test_nodes(
            "test_app_v8_v18",
            "test_v18_a_corrected_frame_shows_before_the_analysis_completes_and_updates_after",
        ),
    ),
    "N10": (
        *_test_nodes(
            "test_wp41_photo_path",
            "test_n10_the_same_still_twice_is_identical",
            "test_gpu_export_reports_gpu_and_matches_the_cpu",
        ),
        *_test_nodes("test_methods_assembly_prototype", "test_same_device_twice_is_bit_identical"),
        *_test_nodes(
            "test_v51_video_acceptance",
            "test_n10_video_cpu_render_digests_repeat",
            "test_n10_video_gpu_render_digests_repeat_and_match_cpu",
        ),
    ),
    "D91": (
        *_test_nodes("test_wp41_photo_path", "test_v5_bit_depth_icc_exif_and_provenance"),
        *_test_nodes("test_v51_video_acceptance", "test_d91_video_provenance"),
    ),
}

ACCEPTANCE_NON_NODE_REASONS: dict[str, str] = {
    "V2": "Owner visual review at CP5 is pending; no automated preference oracle.",
    "V12": "Chapter grouping is deferred to v2 (spec 0.5.3).",
    "V14": "Six prototype results and decisions are cited in docs/reports/wp1.6-gate-report.md.",
    "V15": "Memory figures belong to WP5.2 and are pending; no WP5.1 measurement node.",
    "V16": "Performance figures belong to WP5.2 and are pending; no WP5.1 measurement node.",
}
