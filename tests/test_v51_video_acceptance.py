"""V4/V6/V9/V10 and D91 acceptance through the shipped headless runner.

Committed containers are used unchanged under CHARC's R0-4 sizing ruling.
Each node names the export defect it catches; planted wrong results exercise
green-on-arrival oracles without changing product code or committed fixtures.
"""

from __future__ import annotations

import copy
import itertools
import json
import shutil
from collections.abc import Callable, Iterator, Mapping, Sequence
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from numpy.typing import NDArray

import clearwater
import video_fidelity as vf
from acceptance_support import (
    RenderDigests,
    RunnerResult,
    assert_fidelity,
    assert_names_only,
    best_effort_presence,
    decode_video_rgb,
    fidelity_record,
    file_md5,
    only_output,
    run_main,
    video_provenance,
)
from clearwater import core
from clearwater.app import composition
from clearwater.interfaces import Settings
from clearwater.io.video import probe
from clearwater.methods import available_methods
from container_spike import compare

type Sample = Callable[[str], Path]
type RecordProperty = Callable[[str, object], None]

FIXTURES = ("hevc8-bt709-full", "hevc10", "untagged", "vfr", "rotated")
CPU = ("--force-cpu", "--encoder", "libx265")
RUNNER_POSTENCODE_MEAN = 3.5
"""Runner characterisation bound in 1/255 units, set on 2026-11-01 (CHARC 2bd14e3a).

Measured means: 2.79-2.95 at 8 bits, 2.47 at 10 bits, with shipped libx265
quality standard. This sits above PAIR_MEAN_SYNTHETIC 2.5 for the encoder-free
pair in test_color_roundtrip.py; it does not change AD-11's pre-encode bound.
Maximum error is recorded, not bounded.
"""

pytestmark = pytest.mark.usefixtures("ffmpeg_tools")


@pytest.fixture(autouse=True)
def guard_video_sources(sample: Sample) -> Iterator[None]:
    """Fail if any committed video source changes, including on an assertion failure."""
    paths = [sample(f"vid-{name}") for name in (*FIXTURES, "truncated", "hlg", "pq")]
    before = {path: file_md5(path) for path in paths}
    try:
        yield
    finally:
        for path, digest in before.items():
            assert file_md5(path) == digest, f"video source changed: {path.name}"


def _items(record: Mapping[str, Any]) -> dict[str, Any]:
    return {item["name"]: item for item in record["items"]}


def _fidelity_control(record: dict[str, Any], record_property: RecordProperty) -> None:
    wrong = copy.deepcopy(record)
    wrong["summary"]["mandatory_and_required_all_same"] = False
    wrong["summary"]["different_items"][compare.MANDATORY] = ["video frame count"]
    _items(wrong)["video frame count"].update(status=compare.DIFFERENT, output=-1)
    with pytest.raises(AssertionError, match="video frame count"):
        assert_fidelity(wrong)
    wrong = copy.deepcopy(record)
    _items(wrong)[vf._ROSTER_ITEM]["status"] = compare.DIFFERENT
    with pytest.raises(AssertionError):
        assert_fidelity(wrong)
    record_property(
        "mutation_probe", "mandatory frame-count difference and missing roster rejected"
    )


def _assert_exact_pts(source: Sequence[Fraction | None], output: Sequence[Fraction | None]) -> None:
    assert source and all(value is not None for value in source), "source pts missing"
    assert source == output, "VFR per-frame pts changed"


@pytest.mark.slow(reason="FFmpeg encode")
@pytest.mark.parametrize("name", FIXTURES)
def test_v4_runner_preserves_fixture_fidelity(
    sample: Sample, tmp_path: Path, record_property: RecordProperty, name: str
) -> None:
    """Catch changed mandatory/required container facts through the shipped runner."""
    source, root = sample(f"vid-{name}"), tmp_path / "runner"
    result = run_main([source], root, extra=CPU)
    output = only_output(result, root / "out")
    record = fidelity_record(source, output, tmp_path / "comparison")
    assert_fidelity(record)
    assert _items(record)["video frame count"]["output"] == probe(source).video.nb_frames
    assert result.record["items"][0]["video"]["frame_device"] == "cpu"
    assert result.record["items"][0]["video"]["encoder"] == "libx265"
    record_property("fidelity", record["summary"])
    _fidelity_control(record, record_property)
    if name == "vfr":
        # Inspect every exact rational timestamp, not just a count or rounded duration.
        src, out = vf.gather(source).pts, vf.gather(output).pts
        _assert_exact_pts(src, out)
        assert (
            len({b - a for a, b in itertools.pairwise(src) if a is not None and b is not None}) > 1
        )
        wrong = list(out)
        assert wrong[-1] is not None
        wrong[-1] += Fraction(1, 1_000_000)
        with pytest.raises(AssertionError, match="VFR per-frame pts changed"):
            _assert_exact_pts(src, wrong)
        record_property("exact_pts", [str(value) for value in out])
        record_property("pts_mutation_probe", "one rational timestamp changed by 1 us rejected")


def _assert_d86(result: RunnerResult) -> None:
    assert result.status == 0, result.record
    first, second = result.record["items"]
    assert first["state"] == "done with warnings" and first["failure"] is None
    assert any(
        "cut short" in text and "last readable frame" in text for text in first["warnings"]
    ), "D86 readable-prefix warning missing"
    assert second["state"] in ("done", "done with warnings") and second["failure"] is None
    assert first["outputs"] and second["outputs"], "batch did not continue"


@pytest.mark.slow(reason="FFmpeg encode")
def test_v4_truncated_runner_batch_obeys_d86(
    sample: Sample, tmp_path: Path, record_property: RecordProperty
) -> None:
    """Catch a refused readable prefix, a missing D86 warning or a stopped batch."""
    sources = [sample("vid-truncated"), sample("vid-hevc8-bt709-full")]
    root = tmp_path / "runner"
    result = run_main(sources, root, extra=CPU)
    _assert_d86(result)
    output = root / "out" / result.record["items"][0]["outputs"][0]
    record = fidelity_record(sources[0], output, tmp_path / "comparison")
    assert_fidelity(record)
    count = _items(record)["video frame count"]
    assert count["source"] == count["output"] == 24, "readable-prefix frame count changed"
    assert any("D86" in note for note in record["summary"]["notes"])
    assert (root / "out" / result.record["items"][1]["outputs"][0]).is_file()
    record_property("readable_frames", count["output"])
    _fidelity_control(record, record_property)
    wrong = copy.deepcopy(result.record)
    wrong["items"][0]["warnings"] = []
    with pytest.raises(AssertionError, match="D86 readable-prefix warning missing"):
        _assert_d86(RunnerResult(0, wrong, "", ""))
    wrong = copy.deepcopy(result.record)
    wrong["items"][1]["state"] = "not run"
    with pytest.raises(AssertionError):
        _assert_d86(RunnerResult(0, wrong, "", ""))
    record_property("batch_mutation_probe", "missing D86 warning and unrun following item rejected")


def _assert_gpmd(record: Mapping[str, Any]) -> None:
    rows = [item for item in record["items"] if item["name"].startswith(vf.TELEMETRY_ITEM)]
    assert rows, "GPMF comparison missing"
    for item in rows:
        assert item["status"] == compare.SAME, "GPMF packets changed"
        assert item["source"]["count"] > 0, "source GPMF absent"
        assert item["output"]["count"] == item["source"]["count"], "GPMF not carried"


@pytest.mark.footage
@pytest.mark.slow(reason="FFmpeg encode")
def test_v4_real_trim_records_best_effort_presence(
    gx011627_trim: tuple[Path, int], tmp_path: Path, record_property: RecordProperty
) -> None:
    """Catch lost GPMF or mandatory facts; record other best-effort metadata presence."""
    source, expected_frames = gx011627_trim
    before = file_md5(source)
    try:
        root = tmp_path / "runner"
        # The shipped selector uses the GPU if usable, otherwise its CPU fallback.
        result = run_main([source], root, extra=("--encoder", "libx265"))
        output = only_output(result, root / "out")
        record = fidelity_record(source, output, tmp_path / "comparison")
        presence = best_effort_presence(record)
        for name in presence:
            wrong_presence = copy.deepcopy(record)
            wrong_presence["items"] = [
                item for item in wrong_presence["items"] if item["name"] != name
            ]
            with pytest.raises(AssertionError, match="best-effort presence must contain all seven"):
                best_effort_presence(wrong_presence)
        absent = copy.deepcopy(record)
        for item in absent["items"]:
            if item["name"] in presence:
                item.update(source=False, output=False)
        assert all(not any(row.values()) for row in best_effort_presence(absent).values())
        record_property(
            "presence_mutation_probe", "each missing row rejected; all-False rows accepted"
        )
        record_property("best_effort_presence", json.dumps(presence, sort_keys=True))
        record_property("device", result.record["items"][0]["device"])
        record_property("video", result.record["items"][0]["video"])
        assert_fidelity(record)
        assert _items(record)["video frame count"]["output"] == expected_frames
        _assert_gpmd(record)
        _fidelity_control(record, record_property)
        wrong = copy.deepcopy(record)
        for item in wrong["items"]:
            if item["name"].startswith(vf.TELEMETRY_ITEM):
                item.update(output={"count": 0}, status=compare.DIFFERENT)
        with pytest.raises(AssertionError, match="GPMF packets changed"):
            _assert_gpmd(wrong)
        record_property("gpmd_mutation_probe", "dropped telemetry rejected")
    finally:
        assert file_md5(source) == before, "real trim changed"


def _assert_hdr_batch(result: RunnerResult, names: Sequence[str]) -> None:
    assert result.status == 1, result.record
    hlg, pq, done = result.record["items"]
    for item, name, transfer in zip((hlg, pq), names, ("HLG", "PQ (HDR10)"), strict=True):
        assert item["state"] == "failed" and item["outputs"] == []
        text = item["failure"]
        assert text.startswith(name) and text.isascii()
        # probe.py's transfer-specific refusal, not merely any failed export.
        assert f"uses {transfer} HDR" in text and "standard (SDR) mode" in text, text
    assert done["state"] in ("done", "done with warnings") and done["failure"] is None
    assert done["outputs"], "SDR item after HDR refusals was not exported"


@pytest.mark.slow(reason="FFmpeg encode")
def test_v6_hdr_refusals_do_not_stop_batch(
    sample: Sample, tmp_path: Path, record_property: RecordProperty
) -> None:
    """Catch a generic HDR error, accidental HDR acceptance or failure to continue D81."""
    sources = [sample(f"vid-{name}") for name in ("hlg", "pq", "hevc8-bt709-full")]
    root = tmp_path / "runner"
    result = run_main(sources, root, extra=CPU)
    names = [source.name for source in sources[:2]]
    _assert_hdr_batch(result, names)
    assert (
        sorted(path.name for path in (root / "out").iterdir())
        == result.record["items"][2]["outputs"]
    )
    for index in (0, 1):
        wrong = copy.deepcopy(result.record)
        wrong["items"][index]["failure"] = f"{names[index]}: generic failure"
        with pytest.raises(AssertionError):
            _assert_hdr_batch(RunnerResult(1, wrong, "", ""), names)
    wrong = copy.deepcopy(result.record)
    wrong["items"][2]["state"] = "not run"
    with pytest.raises(AssertionError):
        _assert_hdr_batch(RunnerResult(1, wrong, "", ""), names)
    record_property("mutation_probe", "generic HLG/PQ refusals and stopped batch rejected")


@pytest.mark.slow(reason="FFmpeg encode")
def test_v6_untagged_runner_warns_bt709_limited(
    sample: Sample, tmp_path: Path, record_property: RecordProperty
) -> None:
    """Fail when the real untagged export record omits the D54 colour assumption."""
    source, root = sample("vid-untagged"), tmp_path / "runner"
    result = run_main([source], root, extra=CPU)
    only_output(result, root / "out")
    warnings = result.record["items"][0]["warnings"]
    record_property("warnings", warnings)
    _assert_untagged_warning(warnings)
    with pytest.raises(AssertionError, match=r"D54 BT\.709/limited warning missing"):
        _assert_untagged_warning([])
    record_property("mutation_probe", "missing untagged warning rejected")


def _assert_untagged_warning(warnings: Sequence[str]) -> None:
    assert any("BT.709" in text and "limited" in text for text in warnings), (
        f"D54 BT.709/limited warning missing from untagged item: {warnings!r}"
    )


def _assert_postencode(source: NDArray[np.float64], output: NDArray[np.float64]) -> None:
    assert source.shape == output.shape, "post-encode frame geometry/count changed"
    mean = float(np.abs(source - output).mean())
    assert mean <= RUNNER_POSTENCODE_MEAN, (
        f"RUNNER_POSTENCODE_MEAN exceeded: {mean:.9f}/255 > {RUNNER_POSTENCODE_MEAN}/255"
    )


def _assert_tags_and_rotation(record: Mapping[str, Any]) -> None:
    items = _items(record)
    for name in (
        *vf.COLOUR_ITEMS,
        "display orientation: display matrix (ffprobe side data)",
        "display orientation: video tkhd matrix",
    ):
        assert items[name]["status"] == compare.SAME, f"colour/orientation changed: {name}"


@pytest.mark.slow(reason="FFmpeg encode")
@pytest.mark.parametrize("name", ("hevc8-bt709-full", "untagged", "rotated", "hevc10"))
def test_v9_neutral_runner_postencode(
    sample: Sample, tmp_path: Path, record_property: RecordProperty, name: str
) -> None:
    """Catch a neutral post-encode RGB error above 3.5/255 or changed colour/rotation tags."""
    source, root = sample(f"vid-{name}"), tmp_path / "runner"
    result = run_main([source], root, extra=(*CPU, "--neutral"))
    output = only_output(result, root / "out")
    stream = probe(source).video
    src = decode_video_rgb(source, stream, tmp_path / "source-decode")
    out = decode_video_rgb(output, stream, tmp_path / "output-decode")
    assert src.shape == out.shape, "post-encode frame geometry/count changed"
    difference = np.abs(src - out)
    record_property("mean_abs_255", float(difference.mean()))
    record_property("max_abs_255", float(difference.max()))
    if name == "hevc8-bt709-full":
        planted = out.copy()
        planted[..., 0] += 8.0
        planted_mean = float(np.abs(src - planted).mean())
        record_property("planted_red_offset_mean_255", planted_mean)
        record_property("planted_red_offset_margin_255", planted_mean - RUNNER_POSTENCODE_MEAN)
        with pytest.raises(AssertionError, match="RUNNER_POSTENCODE_MEAN exceeded"):
            _assert_postencode(src, planted)
        record_property(
            "pixel_mutation_probe", "+8/255 on the decoded output's red channel rejected"
        )
    _assert_postencode(src, out)
    record = fidelity_record(source, output, tmp_path / "comparison")
    _assert_tags_and_rotation(record)
    if name == "rotated":
        assert probe(output).video.rotation == stream.rotation != 0
    for tag in (*vf.COLOUR_ITEMS, "display orientation: video tkhd matrix"):
        wrong = copy.deepcopy(record)
        _items(wrong)[tag]["status"] = compare.DIFFERENT
        with pytest.raises(AssertionError, match="colour/orientation changed"):
            _assert_tags_and_rotation(wrong)
    record_property("mutation_probe", "changed colour/rotation tags rejected")
    if name == "hevc8-bt709-full":
        # One additional characterisation only: quality high has no numeric bound here.
        high_root = tmp_path / "quality-high"
        high_result = run_main([source], high_root, extra=(*CPU, "--neutral", "--quality", "high"))
        high_output = only_output(high_result, high_root / "out")
        high = decode_video_rgb(high_output, stream, tmp_path / "quality-high-decode")
        high_difference = np.abs(src - high)
        record_property("quality_standard_mean_255", float(difference.mean()))
        record_property("quality_high_mean_255", float(high_difference.mean()))
        record_property("quality_high_max_255", float(high_difference.max()))


def _assert_output_names(outputs: Sequence[Path], expected: Sequence[str]) -> None:
    assert [output.name for output in outputs] == list(expected), "video numbering sequence changed"
    assert all(output.is_file() for output in outputs), "numbered output missing"


@pytest.mark.slow(reason="FFmpeg encode")
def test_v10_repeated_video_exports_are_numbered(
    sample: Sample, tmp_path: Path, record_property: RecordProperty
) -> None:
    """Catch overwritten or incorrectly numbered results on repeated runner invocations."""
    source, out = sample("vid-hevc8-bt709-full"), tmp_path / "out"
    first = only_output(run_main([source], tmp_path / "first", out=out, extra=CPU), out)
    before = file_md5(first)
    second = only_output(run_main([source], tmp_path / "second", out=out, extra=CPU), out)
    expected = [f"{source.stem}_corrected.mp4", f"{source.stem}_corrected_2.mp4"]
    _assert_output_names([first, second], expected)
    assert file_md5(first) == before, "earlier video output overwritten"
    assert sorted(path.name for path in out.iterdir()) == sorted(expected)
    with pytest.raises(AssertionError, match="video numbering sequence changed"):
        _assert_output_names([first, first], expected)
    record_property("mutation_probe", "reused first output name rejected")


@pytest.mark.slow(reason="FFmpeg encode")
def test_v10_existing_video_output_is_unchanged(
    sample: Sample, tmp_path: Path, record_property: RecordProperty
) -> None:
    """Catch replacement of a pre-existing file even when it is not a valid MP4."""
    source, out = sample("vid-hevc8-bt709-full"), tmp_path / "out"
    out.mkdir()
    planted = out / f"{source.stem}_corrected.mp4"
    planted.write_bytes(np.random.default_rng(51).bytes(4096))
    before = file_md5(planted)
    output = only_output(run_main([source], tmp_path / "runner", out=out, extra=CPU), out)
    expected = [f"{source.stem}_corrected_2.mp4"]
    _assert_output_names([output], expected)
    assert file_md5(planted) == before, "pre-existing video output overwritten"
    assert sorted(path.name for path in out.iterdir()) == sorted([planted.name, output.name])
    with pytest.raises(AssertionError, match="video numbering sequence changed"):
        _assert_output_names([planted], expected)
    record_property("mutation_probe", "collision using planted first output rejected")


@pytest.mark.slow(reason="FFmpeg encode")
def test_v10_mov_mp4_share_one_numbering_sequence(
    sample: Sample, tmp_path: Path, record_property: RecordProperty
) -> None:
    """Catch separate MOV/MP4 numbering or a MOV output extension through main."""
    source = sample("vid-hevc8-bt709-full")
    inputs = tmp_path / "sources"
    inputs.mkdir()
    sources = [inputs / "clip.mp4", inputs / "clip.mov"]
    for path in sources:
        shutil.copyfile(source, path)
    before = {path: file_md5(path) for path in sources}
    try:
        root = tmp_path / "runner"
        result = run_main(sources, root, extra=CPU)
        assert result.status == 0, result.record
        outputs = [root / "out" / item["outputs"][0] for item in result.record["items"]]
        expected = ["clip_corrected.mp4", "clip_corrected_2.mp4"]
        _assert_output_names(outputs, expected)
        assert sorted(path.name for path in (root / "out").iterdir()) == expected
        with pytest.raises(AssertionError, match="video numbering sequence changed"):
            _assert_output_names([outputs[0], outputs[1].with_suffix(".mov")], expected)
        record_property("mutation_probe", "MOV output extension/separate sequence rejected")
    finally:
        for path, digest in before.items():
            assert file_md5(path) == digest, f"scratch source changed: {path.name}"


def _assert_provenance(
    value: Mapping[str, Any] | None, source: Path, parameters: Mapping[str, Any]
) -> None:
    assert value is not None, "default video provenance absent"
    assert value["app_version"] == clearwater.__version__, "provenance app_version changed"
    assert value["method"] == "c3" and value["parameters"] == parameters, (
        "provenance parameters changed"
    )
    assert value["source"]["name"] == source.name, "provenance source name changed"
    assert_names_only(value, folders=[source.parent])
    assert value["settings"]["encoder"] == "libx265"
    assert value["settings"]["quality"] == "standard"
    assert value["settings"]["bit_depth"] == 8


@pytest.mark.slow(reason="FFmpeg encode")
@pytest.mark.parametrize("mode", ("default", "off"))
def test_d91_video_provenance(
    sample: Sample, tmp_path: Path, record_property: RecordProperty, mode: str
) -> None:
    """Catch missing/default or unwanted/disabled provenance and wrong request fields."""
    source, root = sample("vid-hevc8-bt709-full"), tmp_path / "runner"
    flags = CPU if mode == "default" else (*CPU, "--no-provenance")
    # Neutral values make the full requested parameter mapping explicit.
    result = run_main([source], root, extra=(*flags, "--method", "c3", "--neutral"))
    output = only_output(result, root / "out")
    value = video_provenance(output, tmp_path / "provenance")
    parameters = {p.name: p.neutral for p in available_methods()["c3"].parameters}
    if mode == "off":
        _assert_no_provenance(value)
        with pytest.raises(AssertionError, match="disabled video provenance still present"):
            _assert_no_provenance({"app_version": clearwater.__version__})
        record_property("mutation_probe", "unwanted provenance rejected")
    else:
        _assert_provenance(value, source, parameters)
        assert value is not None
        for key, replacement in (("app_version", "wrong"), ("parameters", {})):
            wrong = dict(value, **{key: replacement})
            with pytest.raises(AssertionError, match=f"provenance {key} changed"):
                _assert_provenance(wrong, source, parameters)
        wrong = copy.deepcopy(value)
        wrong["source"]["name"] = str(source.resolve())
        with pytest.raises(AssertionError, match="provenance source name changed"):
            _assert_provenance(wrong, source, parameters)
        record_property(
            "mutation_probe", "wrong version/parameters and path-bearing source rejected"
        )


def _assert_no_provenance(value: Mapping[str, Any] | None) -> None:
    assert value is None, "disabled video provenance still present"


def _render_run(source: Path, root: Path, *, force_cpu: bool) -> tuple[Path, RenderDigests]:
    root.mkdir(parents=True, exist_ok=True)
    recording = RenderDigests(available_methods()["c3"])
    flags = CPU if force_cpu else ("--encoder", "libx265")
    # Exclude created-time provenance from the file-byte characterisation on both runs.
    with composition.proxy_cache(root / "cache") as cache:
        exports = composition.export_jobs(methods={recording.id: recording}, cache=cache)
        result = run_main([source], root, extra=(*flags, "--no-provenance"), exports=exports)
        output = only_output(result, root / "out")
    assert result.record["items"][0]["device"] == ("CPU: forced" if force_cpu else "GPU")
    assert recording.devices == ({"cpu"} if force_cpu else {"cuda:0"})
    return output, recording


def _source_ticks(source: Path) -> set[int]:
    stream = probe(source).video
    times = vf.gather(source).pts
    assert times and all(value is not None for value in times), "N10 source pts missing"
    ticks = [value / stream.time_base for value in times if value is not None]
    assert all(tick.denominator == 1 for tick in ticks), "N10 source pts are not whole ticks"
    assert len(ticks) == stream.nb_frames and len(set(ticks)) == len(ticks)
    return {int(tick) for tick in ticks}


def _assert_render_repeat(
    first: Mapping[int, str], second: Mapping[int, str], expected: set[int]
) -> None:
    assert expected and set(first) == set(second) == expected, "N10 render pts coverage differs"
    assert first == second, "N10 pre-encode render digests differ"


def _record_repeat(
    outputs: tuple[Path, Path],
    recordings: tuple[RenderDigests, RenderDigests],
    expected: set[int],
    record_property: RecordProperty,
) -> None:
    first, second = recordings
    _assert_render_repeat(first.renders, second.renders, expected)
    record_property("render_frame_count", len(first.renders))
    record_property("render_digests", json.dumps(first.renders, sort_keys=True))
    record_property("render_devices", sorted(first.devices))
    # File identity is observed, never required (N10 binds the pre-encode pixels).
    record_property(
        "output_files_byte_identical", outputs[0].read_bytes() == outputs[1].read_bytes()
    )
    wrong = dict(second.renders)
    wrong[min(expected)] = "planted changed digest"
    with pytest.raises(AssertionError, match="N10 pre-encode render digests differ"):
        _assert_render_repeat(first.renders, wrong, expected)
    wrong = dict(second.renders)
    wrong.pop(min(expected))
    with pytest.raises(AssertionError, match="N10 render pts coverage differs"):
        _assert_render_repeat(first.renders, wrong, expected)
    record_property("mutation_probe", "changed render digest and missing pts rejected")


@pytest.mark.slow(reason="FFmpeg encode")
def test_n10_video_cpu_render_digests_repeat(
    sample: Sample, tmp_path: Path, record_property: RecordProperty
) -> None:
    """Catch per-pts pre-encode pixel changes on repeated identical CPU exports."""
    source = sample("vid-hevc8-bt709-full")
    expected = _source_ticks(source)
    first, recording_a = _render_run(source, tmp_path / "first", force_cpu=True)
    second, recording_b = _render_run(source, tmp_path / "second", force_cpu=True)
    _record_repeat((first, second), (recording_a, recording_b), expected, record_property)


def _assert_cpu_gpu_first_frame(cpu: NDArray[np.float32], gpu: NDArray[np.float32]) -> None:
    assert cpu.shape == gpu.shape, "N10 CPU/GPU first-frame geometry differs"
    difference = np.abs(cpu.astype(np.float64) - gpu.astype(np.float64))
    assert float(difference.max()) <= 2e-3, "N10 CPU/GPU pre-encode first-frame max exceeds 2e-3"
    assert float(difference.mean()) <= 2e-4, "N10 CPU/GPU pre-encode first-frame mean exceeds 2e-4"


@pytest.mark.gpu
@pytest.mark.slow(reason="FFmpeg encode")
def test_n10_video_gpu_render_digests_repeat_and_match_cpu(
    sample: Sample, tmp_path: Path, record_property: RecordProperty
) -> None:
    """Catch GPU repeat drift or pre-encode first-frame values outside AD-11 bounds."""
    pytest.importorskip("cupy")
    source = sample("vid-hevc8-bt709-full")
    stream = probe(source).video
    _, reason = core.select_backend(Settings(), stream.height, stream.width, "c3")
    if reason != "GPU":
        pytest.skip(f"no usable CUDA device: {reason}")
    expected = _source_ticks(source)
    first, recording_a = _render_run(source, tmp_path / "first", force_cpu=False)
    second, recording_b = _render_run(source, tmp_path / "second", force_cpu=False)
    _record_repeat((first, second), (recording_a, recording_b), expected, record_property)
    cpu_output, cpu_recording = _render_run(source, tmp_path / "cpu", force_cpu=True)
    assert cpu_recording.first_frame is not None and recording_a.first_frame is not None
    cpu_pts, cpu = cpu_recording.first_frame
    gpu_pts, gpu = recording_a.first_frame
    assert cpu_pts == gpu_pts == min(expected), "N10 CPU/GPU captured different first-frame pts"
    difference = np.abs(cpu.astype(np.float64) - gpu.astype(np.float64))
    record_property("cpu_gpu_preencode_first_frame_pts_ticks", cpu_pts)
    record_property("cpu_gpu_preencode_first_frame_max", float(difference.max()))
    record_property("cpu_gpu_preencode_first_frame_mean", float(difference.mean()))
    _assert_cpu_gpu_first_frame(cpu, gpu)
    with pytest.raises(AssertionError, match="N10 CPU/GPU pre-encode first-frame max exceeds"):
        _assert_cpu_gpu_first_frame(cpu, cpu + 0.003)
    sparse = cpu.copy()
    sparse[..., 0] += 0.001
    with pytest.raises(AssertionError, match="N10 CPU/GPU pre-encode first-frame mean exceeds"):
        _assert_cpu_gpu_first_frame(cpu, sparse)
    record_property("cpu_gpu_mutation_probe", "above-max and above-mean first frames rejected")
    decoded_cpu = decode_video_rgb(cpu_output, stream, tmp_path / "cpu-decode", frames=1)
    decoded_gpu = decode_video_rgb(first, stream, tmp_path / "gpu-decode", frames=1)
    assert decoded_cpu.shape == decoded_gpu.shape, (
        "N10 CPU/GPU decoded first-frame geometry differs"
    )
    decoded_difference = np.abs(decoded_cpu - decoded_gpu) / 255.0
    record_property("cpu_gpu_decoded_first_frame_max", float(decoded_difference.max()))
    record_property("cpu_gpu_decoded_first_frame_mean", float(decoded_difference.mean()))
    record_property(
        "cpu_gpu_decoded_first_frame_equal", bool(np.array_equal(decoded_cpu, decoded_gpu))
    )
    record_property(
        "cpu_gpu_decoded_first_frame_within_one_code", bool(decoded_difference.max() <= 1.0 / 255.0)
    )
