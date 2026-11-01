"""WP3.6P instrument controls; owner I/O is isolated in one footage-marked node.

FFmpeg's default HEIF decode honours irot, not an EXIF-only Orientation. The
generated upright scene independently witnesses that limitation. These tests
never compensate FFmpeg's output by applying another transform.
"""

from __future__ import annotations

import hashlib
import io
import json
import logging
import shutil
import struct
import sys
import time
import zlib
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pillow_heif
import pytest
from PIL import ExifTags
from PIL import Image as PILImage
from PIL.TiffImagePlugin import IFDRational
from pillow_heif.constants import HeifCompressionFormat
from pillow_heif.misc import CtxEncode

import headless_export as he
import photo_verify as pv
from clearwater.app import composition
from clearwater.config import new_parameter_set
from clearwater.core.memory import memory_estimate_bytes
from clearwater.io.photo import PhotoReader, PhotoWriter
from local_config import LocalConfig, footage_available, load_local_config
from spike_io import photo as spike
from spike_io.guard import OutputRefusedError

AD24_CASES = ("both", "irot-only", "exif-only", "neither")
CLASS_COUNTS = {
    "HEIC-0": 23,
    "HEIC-90": 3,
    "HEIC-180": 20,
    "HEIC-270": 16,
    "JPG-A": 2,
    "JPG-Z": 8,
    "JPG-M": 1,
}


@pytest.fixture
def configured(tmp_path):
    footage = tmp_path / "private-input"
    (footage / "Phone").mkdir(parents=True)
    working = tmp_path / "working"
    working.mkdir()
    config = LocalConfig(footage_path=footage, working_path=working)
    return config, pv.make_guard(config)


def _upright():
    return spike.upright_image(8, 96, 64).astype(np.float64)


def _png_chunks(path):
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    chunks = []
    at = 8
    while at < len(data):
        length = int.from_bytes(data[at : at + 4], "big")
        chunks.append((data[at + 4 : at + 8], data[at + 8 : at + 8 + length]))
        at += length + 12
    return chunks


def _icc(path):
    profiles = [body for kind, body in _png_chunks(path) if kind == b"iCCP"]
    assert len(profiles) <= 1
    if not profiles:
        return None
    _, compressed = profiles[0].split(b"\0", 1)
    assert compressed[0] == 0
    return zlib.decompress(compressed[1:])


def _only_png(guard):
    paths = list(guard.root.rglob("*.png"))
    assert len(paths) == 1
    return paths[0]


@pytest.mark.parametrize("case", AD24_CASES)
def test_ffmpeg_default_decode_records_irot_only_rule(sample, configured, case, record_property):
    _, guard = configured
    source = sample(f"heic-ad24-{case}")
    pixels = pv.ffmpeg_decode(source, guard.check(guard.root / "oracle.png"), guard)
    # The tag-only file's stored pixels are a CCW quarter-turn of the upright scene.
    expected = np.rot90(_upright(), 1) if case == "exif-only" else _upright()
    scores = pv.compare_poses(pixels, expected)
    assert scores["orientation_ok"], f"ffmpeg_irot_only_rule: {case}"
    assert scores["upright_mean_255"] < 6.0
    assert scores["nearest_other_mean_255"] > 10.0
    record_property(
        "ffmpeg_transform_rule",
        {
            "case": case,
            "honours_irot": True,
            "honours_exif_only": False,
            "pose": "stored" if case == "exif-only" else "upright",
            "scores": scores,
        },
    )


@pytest.mark.parametrize("case", AD24_CASES)
def test_orientation_matches_generated_upright(sample, configured, case):
    _, guard = configured
    source = sample(f"heic-ad24-{case}")
    image, _ = PhotoReader().read(source)
    known_pose = pv.compare_poses(image.pixels * 255, _upright())
    assert known_pose["orientation_ok"], f"generated_upright: {case}"
    assert known_pose["winning_pose"] == 1
    assert len(known_pose["scores_by_pose"]) == 8
    assert len(known_pose["shape_mismatches"]) == 4
    record = pv.verify_orientation(source, guard, photo_class="HEIC-0")
    # Do not turn FFmpeg's tag-only output into an allegedly independent upright oracle.
    assert record["orientation_ok"] is (case != "exif-only")
    assert record["oracle_kind"] == "ffmpeg-default"
    assert "thumbnail_witness" in record


def test_orientation_rejects_exif_always(sample, configured, monkeypatch):
    _, guard = configured
    source = sample("heic-ad24-both")
    read = pv.read_photo

    def always(path):
        image, meta = read(path)
        return replace(image, pixels=np.ascontiguousarray(np.rot90(image.pixels, -1))), meta

    monkeypatch.setattr(pv, "read_photo", always)
    record = pv.verify_orientation(source, guard, photo_class="HEIC-270")
    assert not record["orientation_ok"]
    assert "orientation_upright" in record["failed_checks"], "heic-ad24-both"


def test_orientation_rejects_exif_never(sample, configured):
    _, guard = configured
    source = sample("heic-ad24-exif-only")
    correct, _ = PhotoReader().read(source)
    never = np.rot90(correct.pixels * 255, 1)
    scores = pv.compare_poses(never, _upright())
    assert not scores["orientation_ok"]
    assert "orientation_upright" in scores["failed_checks"], "heic-ad24-exif-only"
    ffmpeg = pv.ffmpeg_decode(source, guard.root / "tag-only.png", guard)
    # This planted bug AGREES with FFmpeg: the generated scene is the necessary witness.
    assert pv.compare_poses(never, ffmpeg)["orientation_ok"]


def test_thumbnail_disagreement_is_recorded_but_never_the_pass_criterion(
    sample, configured, monkeypatch
):
    _, guard = configured
    monkeypatch.setattr(pv, "thumbnail_decode", lambda _source: np.rot90(_upright(), 2))
    record = pv.verify_orientation(sample("heic-ad24-both"), guard, photo_class="HEIC-270")
    assert record["orientation_ok"]
    assert record["thumbnail_witness"]["available"]
    assert not record["thumbnail_witness"]["orientation_ok"]


@pytest.mark.parametrize("depth", [8, 16])
@pytest.mark.parametrize(
    "sample_id",
    [
        "heic8-gradient-none",
        "png16-lowred-display-p3",
        "jpeg-gradient-none",
    ],
)
def test_export_v5_v9(sample, configured, sample_id, depth):
    _, guard = configured
    source = sample(sample_id)
    original, _ = PhotoReader().read(source)
    record = pv.verify_export(
        source, guard, photo_class="JPG-A", bit_depth=depth, force_cpu=True, keep=True
    )
    assert record["v5_ok"] and record["v9_ok"] and record["d53_ok"]
    assert record["device_reason"] == "CPU: forced"
    assert record["output_depth"] == depth
    assert record["quantised_max_255"] <= 2.0
    assert record["quantised_mean_255"] <= 0.2
    if depth == 16 or original.color.bit_depth == 8:
        assert record["raw_max_255"] <= 2.0
        assert record["raw_mean_255"] <= 0.2
    output = _only_png(guard)
    assert _png_chunks(output)[0][1][8] == depth
    profile = _icc(output)
    if sample_id.startswith("heic"):
        assert profile is not None
        assert hashlib.md5(profile).hexdigest() == "ca34a0279325928fc9fd3fc7eff99eb9"
    else:
        assert profile == original.color.icc_profile
    if sample_id.startswith("jpeg"):
        assert not record["icc_expected_present"]
        assert record["assumed"]
    assert record["png_bytes"] == output.stat().st_size
    assert record["png_md5"] == hashlib.md5(output.read_bytes()).hexdigest()


def test_export_rejects_off_neutral_gamma(sample, configured):
    _, guard = configured
    parameters = he.parameters_for(neutral=True)
    off = new_parameter_set("c3", {**parameters.parameters, "gamma": 1.5})
    record = pv.verify_export(
        sample("png16-lowred-display-p3"),
        guard,
        photo_class="JPG-A",
        bit_depth=16,
        force_cpu=True,
        keep=True,
        parameters=off,
    )
    assert not record["v9_ok"]
    assert "v9_identity" in record["failed_checks"]


class DropIccp(PhotoWriter):
    def write(self, image, meta, out_path, *, bit_depth, provenance):
        super().write(image, meta, out_path, bit_depth=bit_depth, provenance=provenance)
        data = Path(out_path).read_bytes()
        kept = [data[:8]]
        at = 8
        while at < len(data):
            stop = at + 12 + int.from_bytes(data[at : at + 4], "big")
            if data[at + 4 : at + 8] != b"iCCP":
                kept.append(data[at:stop])
            at = stop
        Path(out_path).write_bytes(b"".join(kept))


def test_export_rejects_dropped_iccp(sample, configured):
    _, guard = configured
    record = pv.verify_export(
        sample("png16-lowred-display-p3"),
        guard,
        photo_class="JPG-A",
        bit_depth=16,
        force_cpu=True,
        keep=True,
        exports=composition.export_jobs(writer=DropIccp()),
    )
    assert not record["v5_ok"] and not record["d53_ok"]
    assert "v5_icc_equal" in record["failed_checks"]


def _private_jpeg(config):
    source = config.footage_path / "Phone" / "synthetic-private.JPG"
    exif = PILImage.Exif()
    exif.load(spike.source_exif(6, 96, 64))
    exif[271] = "WP36P_PRIVATE_CAMERA_SENTINEL"
    exif[34853] = {
        1: "N",
        2: (IFDRational(12), IFDRational(34), IFDRational(56)),
        27: b"ASCII\0\0\0WP36P_PRIVATE_GPS_SENTINEL",
    }
    thumb = io.BytesIO()
    PILImage.fromarray(np.zeros((8, 12, 3), dtype=np.uint8)).save(thumb, "JPEG")
    block = spike.add_thumbnail(exif.tobytes(), thumb.getvalue())
    PILImage.fromarray(spike.upright_image(8, 96, 64)).save(source, "JPEG", exif=block)
    return source


def test_export_d63_and_kept_exif(configured):
    config, guard = configured
    source = _private_jpeg(config)
    record = pv.verify_export(
        source, guard, photo_class="JPG-Z", bit_depth=16, force_cpu=True, keep=True
    )
    for key in (
        "orientation_normal",
        "software_ok",
        "dimensions_ok",
        "thumbnail_absent",
        "kept_fields_equal",
        "gps_kept",
    ):
        assert record[key], key
    assert record["gps_ifd_present"] and not record["sanitise_dropped"]
    assert record["v5_ok"]
    with PILImage.open(_only_png(guard)) as written:
        exif = written.getexif()
        assert exif[274] == 1
        assert str(exif[305]).rstrip("\0") == "Clearwater"
        assert not exif.get_ifd(ExifTags.IFD.IFD1)
        dimensions = exif.get_ifd(34665)
        assert (dimensions[40962], dimensions[40963]) == written.size
        assert exif[271] == "WP36P_PRIVATE_CAMERA_SENTINEL"


class DropKeptExif(PhotoWriter):
    def write(self, image, meta, out_path, *, bit_depth, provenance):
        super().write(
            image, replace(meta, exif=None), out_path, bit_depth=bit_depth, provenance=provenance
        )


def test_export_rejects_lost_kept_exif(configured):
    config, guard = configured
    record = pv.verify_export(
        _private_jpeg(config),
        guard,
        photo_class="JPG-Z",
        bit_depth=8,
        force_cpu=True,
        keep=True,
        exports=composition.export_jobs(writer=DropKeptExif()),
    )
    assert not record["v5_ok"]
    assert "v5_kept_exif" in record["failed_checks"]


def test_summary_and_stdout_exclude_private_values(configured, capsys):
    config, guard = configured
    source = _private_jpeg(config)
    before = source.read_bytes()
    record = pv.verify_export(
        source, guard, photo_class="JPG-Z", bit_depth=8, force_cpu=True, keep=True
    )
    contaminated = {
        **record,
        "path": str(source),
        "Make": "WP36P_PRIVATE_CAMERA_SENTINEL",
        "failure": "WP36P_PRIVATE_GPS_SENTINEL",
        "exif_values": {"GPS": "private"},
        "unexpected": {"source_path": str(source)},
        "software_seen": "WP36P_PRIVATE_CAMERA_SENTINEL",
        "d63_defects": [
            {"field": str(source), "defect": "value"},
            {"field": "IFD0.Software", "defect": "WP36P_PRIVATE_GPS_SENTINEL"},
        ],
        "sampling_cadence_s": {"device": {"min": str(source)}, "private": str(source)},
    }
    summary = pv.summarise([contaminated], command="export")
    pv.print_summary(summary)
    text = json.dumps(summary, ensure_ascii=True) + capsys.readouterr().out
    for secret in (
        "WP36P_PRIVATE_CAMERA_SENTINEL",
        "WP36P_PRIVATE_GPS_SENTINEL",
        str(config.footage_path),
        str(config.footage_path).replace("\\", "\\\\"),
    ):
        assert secret not in text
    assert "exif_values" not in text and "source_path" not in text
    assert source.read_bytes() == before
    assert all(p.is_relative_to(guard.root) for p in guard.root.rglob("*"))


def test_export_deletes_only_measured_nonrepresentative_png(sample, configured):
    _, guard = configured
    kept = guard.check(guard.root / "unrelated-evidence.txt")
    kept.write_text("keep", encoding="ascii")
    record = pv.verify_export(
        sample("jpeg-gradient-none"),
        guard,
        photo_class="JPG-Z",
        bit_depth=8,
        force_cpu=True,
        keep=False,
    )
    assert record["v5_ok"] and record["v9_ok"]
    assert record["png_bytes"] > 0 and len(record["png_md5"]) == 32
    assert not record["retained"] and not list(guard.root.rglob("*.png"))
    assert kept.read_text(encoding="ascii") == "keep"


def test_all_records_and_runner_targets_stay_guarded(sample, configured, monkeypatch):
    config, guard = configured
    checked = []
    original_check = type(guard).check

    def check(self, path):
        result = original_check(self, path)
        checked.append(Path(path))
        return result

    monkeypatch.setattr(type(guard), "check", check)
    source = sample("jpeg-gradient-none")
    pv.verify_export(source, guard, photo_class="JPG-Z", bit_depth=8, force_cpu=True, keep=True)
    assert checked
    assert all(p.resolve().is_relative_to(guard.root) for p in checked)
    with pytest.raises(OutputRefusedError):
        pv.ffmpeg_decode(sample("heic-ad24-both"), config.footage_path / "escaped.png", guard)
    assert not (config.footage_path / "escaped.png").exists()


class StubMemorySampler:
    def __init__(self, *args, **kwargs):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def attach(self, runner):
        pass

    def record(self):
        return {
            "rss_baseline_bytes": 1000,
            "rss_tree_peak_bytes": 9000,
            "os_peak_working_set_bytes": None,
            "device_used_baseline_bytes": 2000,
            "device_used_peak_bytes": 5000,
            "rss_samples": 3,
            "device_samples": 2,
            "rss_active_samples": 2,
            "device_active_samples": 2,
            "sample_intervals_s": {"rss": 0.05, "device": 0.2},
            "sampler_errors": [],
        }


def test_memory_records_sampler_facts(sample, configured, monkeypatch):
    _, guard = configured
    monkeypatch.setattr(pv, "MemorySampler", StubMemorySampler)
    monkeypatch.setattr(
        pv,
        "device_memory",
        lambda: {
            "free_bytes": 7000,
            "total_bytes": 12000,
            "used_bytes": 5000,
        },
    )
    source = sample("jpeg-gradient-none")
    image, _ = PhotoReader().read(source)
    record = pv.verify_memory(source, guard, photo_class="JPG-Z", force_cpu=True)
    height, width = image.pixels.shape[:2]
    assert record["estimate_bytes"] == memory_estimate_bytes(height, width, "c3")
    assert record["device_free_before_bytes"] == 7000
    assert record["estimate_exceeds_free_before"]
    assert record["device_reason"] == "CPU: forced" and record["forced_cpu"]
    assert not record["automatic_fallback"]
    assert record["rss_tree_peak_bytes"] == 9000
    assert record["device_used_peak_bytes"] == 5000
    assert record["rss_samples"] == 3 and record["device_samples"] == 2
    assert record["ram_limit_bytes"] == 16_000_000_000
    assert record["device_limit_bytes"] == 8188 * 2**20
    assert record["runner_exit"] == 0


def test_memory_default_records_actual_runner_reason(sample, configured, monkeypatch):
    _, guard = configured
    monkeypatch.setattr(pv, "MemorySampler", StubMemorySampler)
    monkeypatch.setattr(
        pv,
        "device_memory",
        lambda: {
            "free_bytes": 7000,
            "total_bytes": 12000,
            "used_bytes": 5000,
        },
    )

    def cpu_runner(source, out, record_path, settings_dir, *, bit_depth, force_cpu, neutral):
        # Use the real runner on CPU; emulate the no-CUDA selection of another host.
        assert not force_cpu and not neutral
        settings = he.Settings(output_folder=out, force_cpu=True, png_bit_depth=bit_depth)
        requests = he.requests_for([source], parameters=he.parameters_for(), settings=settings)
        result = he.run(requests, footage_folder=None)
        raw = he.record_object(result)
        raw["items"][0]["device"] = "CPU: no CUDA device"
        record_path.write_text(json.dumps(raw), encoding="ascii")
        return he.exit_status(result), raw

    monkeypatch.setattr(pv, "launch_runner", cpu_runner)
    record = pv.verify_memory(
        sample("jpeg-gradient-none"), guard, photo_class="JPG-Z", force_cpu=False
    )
    assert record["device_reason"] == "CPU: no CUDA device"
    assert record["automatic_fallback"] and not record["forced_cpu"]
    assert record["device_free_before_bytes"] == 7000
    assert record["rss_tree_peak_bytes"] == 9000 and record["runner_exit"] == 0


def test_memory_missing_device_samples_cannot_pass(sample, configured, monkeypatch):
    _, guard = configured

    class MissingDevice(StubMemorySampler):
        def record(self):
            return {
                **super().record(),
                "device_used_peak_bytes": None,
                "device_samples": 0,
                "sampler_errors": ["device_unavailable"],
            }

    monkeypatch.setattr(pv, "MemorySampler", MissingDevice)
    monkeypatch.setattr(pv, "device_memory", lambda: None)
    record = pv.verify_memory(
        sample("jpeg-gradient-none"), guard, photo_class="JPG-Z", force_cpu=True
    )
    assert record["device_used_peak_bytes"] is None
    assert record["device_within_limit"] is None
    assert "memory_device_measurement" in record["failed_checks"]


def _class_map(tmp_path):
    classes = {}
    for category, count in CLASS_COUNTS.items():
        suffix = ".HEIC" if category.startswith("HEIC") else ".JPG"
        files = [f"synthetic-{category}-{i}{suffix}" for i in range(count)]
        classes[category] = {"files": files, "representative": files[0]}
    path = tmp_path / "class-map.json"
    path.write_text(json.dumps({"schema": 1, "classes": classes}), encoding="ascii")
    return path, classes


@pytest.mark.parametrize("damage", ["traversal", "duplicate", "wrong-count", "unknown-class"])
def test_class_map_rejects_unsafe_or_incomplete_inventory(tmp_path, damage):
    path, classes = _class_map(tmp_path)
    if damage == "traversal":
        classes["JPG-A"]["files"][0] = "../escaped.JPG"
    elif damage == "duplicate":
        classes["JPG-A"]["files"][1] = classes["JPG-A"]["files"][0]
    elif damage == "wrong-count":
        classes["JPG-Z"]["files"].pop()
    else:
        classes["UNKNOWN"] = classes.pop("JPG-M")
    path.write_text(json.dumps({"schema": 1, "classes": classes}), encoding="ascii")
    with pytest.raises(ValueError):
        pv.load_class_map(path)


def test_class_map_and_summary_keep_candidate_rows_separate(tmp_path):
    path, _ = _class_map(tmp_path)
    mapping = pv.load_class_map(path)
    assert len(mapping["classes"]["JPG-Z"]["files"]) == 8
    assert len(mapping["classes"]["JPG-M"]["files"]) == 1
    records = [
        {
            "file": f"synthetic-{group}.JPG",
            "class": f"JPG-{group}",
            "read_ok": True,
            "assumed": assumed,
            "sanitise_dropped": False,
            "v9_ok": True,
            "quantised_max_255": error,
        }
        for group, assumed, error in (("A", False, 0.1), ("Z", True, 1.5), ("M", True, 0.7))
    ]
    summary = pv.summarise(records, command="export")
    assert summary["classes"]["JPG-A"]["assumed_count"] == 0
    assert summary["classes"]["JPG-Z"]["assumed_count"] == 1
    assert summary["classes"]["JPG-M"]["assumed_count"] == 1
    assert "JPG-Z/M" not in summary["classes"]
    assert "quantised_max_255" not in summary  # no pooled candidate metric


def test_cli_summary_and_record_files_stay_private_and_guarded(configured, tmp_path, capsys):
    config, guard = configured
    private = _private_jpeg(config)
    class_path, classes = _class_map(tmp_path)
    chosen = classes["JPG-Z"]["representative"]
    # Complete synthetic inventory; only the selected JPEG is decoded by this command.
    for group in classes.values():
        for name in group["files"]:
            shutil.copyfile(private, config.footage_path / "Phone" / name)
    config_path = tmp_path / "synthetic.local.toml"
    config_path.write_text(
        f"footage_path = '{config.footage_path}'\nworking_path = '{config.working_path}'\n",
        encoding="ascii",
    )
    before = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (config.footage_path / "Phone").iterdir()
    }
    status = pv.main(
        [
            "export",
            "--config",
            str(config_path),
            "--class-map",
            str(class_path),
            "--name",
            "privacy-cli",
            "--files",
            chosen,
            "--bit-depth",
            "8",
            "--force-cpu",
        ]
    )
    captured = capsys.readouterr()
    assert status == 0
    summaries = list(guard.root.rglob("summary.json"))
    assert len(summaries) == 1
    summary = json.loads(summaries[0].read_text(encoding="ascii"))
    text = captured.out + captured.err + json.dumps(summary, ensure_ascii=True)
    for value in (
        "WP36P_PRIVATE_CAMERA_SENTINEL",
        "WP36P_PRIVATE_GPS_SENTINEL",
        str(config.footage_path),
        str(config.footage_path).replace("\\", "\\\\"),
    ):
        assert value not in text
    assert summary["selected"] == 1 and summary["attempted"] == 1
    assert summary["classes"]["JPG-Z"]["assumed_count"] == 1
    assert all(p.is_relative_to(config.working_path / "wp3.6p") for p in summaries)
    after = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (config.footage_path / "Phone").iterdir()
    }
    assert after == before


@pytest.mark.footage  # Serial leg: reads four owner HEICs and launches independent decodes.
def test_owner_heic_orientation_four_irot_classes(tmp_path):
    if not footage_available():
        pytest.skip("no footage folder")
    config = load_local_config()
    guard = pv.make_guard(LocalConfig(config.footage_path, tmp_path / "working"))
    for name, photo_class in (
        ("IMG_6703.HEIC", "HEIC-0"),
        ("IMG_6718.HEIC", "HEIC-90"),
        ("IMG_6690.HEIC", "HEIC-180"),
        ("IMG_6720.HEIC", "HEIC-270"),
    ):
        source = config.footage_path / "Phone" / name
        assert source.is_file(), name
        record = pv.verify_orientation(source, guard, photo_class=photo_class)
        assert record["read_ok"] and record["orientation_ok"], name
        assert record["oracle_kind"] == "ffmpeg-default"
        assert record["upright_mean_255"] < 6.0, name
        assert record["nearest_other_mean_255"] > 10.0, name
        assert "thumbnail_witness" in record


# Reviewer A round 1 controls. Each names the verification defect it catches.
def test_r1_size_is_checked_before_pose_reduction(sample, configured, monkeypatch):
    _, guard = configured
    read = pv.read_photo

    def half(path):
        image, meta = read(path)
        return replace(image, pixels=np.ascontiguousarray(image.pixels[::2, ::2])), meta

    monkeypatch.setattr(pv, "read_photo", half)
    record = pv.verify_orientation(
        sample("heic-ad24-both"), guard, photo_class="HEIC-270", max_side=32
    )
    assert not record["orientation_ok"], "wrong-size product read passed"
    assert "orientation_size" in record["failed_checks"]
    assert record["decoded_size"] != record["oracle_size"]


def _r1_replace_exif(path, mutate):
    chunks = []
    for kind, body in _png_chunks(path):
        if kind == b"eXIf":
            body = mutate(body)
        chunks.append(
            len(body).to_bytes(4, "big")
            + kind
            + body
            + (zlib.crc32(kind + body) & 0xFFFFFFFF).to_bytes(4, "big")
        )
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"".join(chunks))


def _r1_root_entry(block, tag):
    order = "<" if block[:2] == b"II" else ">"
    root = struct.unpack_from(order + "I", block, 4)[0]
    count = struct.unpack_from(order + "H", block, root)[0]
    for index in range(count):
        at = root + 2 + 12 * index
        if struct.unpack_from(order + "H", block, at)[0] == tag:
            return order, at
    raise AssertionError("test entry missing")


@pytest.mark.parametrize("damage", ["rational-bytes", "added-field", "interop-value"])
def test_r1_kept_exif_is_byte_exact_in_both_directions(configured, damage):
    config, guard = configured
    source = config.footage_path / "Phone" / "byte-control.JPG"
    exif = PILImage.Exif()
    exif[282] = IFDRational(72, 1)
    if damage == "interop-value":
        exif.get_ifd(34665)[40965] = {1: "R98", 2: b"0100"}
    # Start with the D63 fields already laid out, so a coarse pointer-offset
    # false failure cannot hide a byte-fidelity mutant. Expected mutations below
    # are still independently specified raw entry changes, not writer results.
    block = pv.exif_tools.edit(exif.tobytes(), 96, 64)
    PILImage.fromarray(spike.upright_image(8, 96, 64)).save(source, exif=b"Exif\0\0" + block)

    class Mutated(PhotoWriter):
        def write(self, image, meta, out_path, *, bit_depth, provenance):
            super().write(image, meta, out_path, bit_depth=bit_depth, provenance=provenance)

            def mutate(block):
                if damage == "rational-bytes":
                    data = bytearray(block)
                    order, at = _r1_root_entry(data, 282)
                    offset = struct.unpack_from(order + "I", data, at + 8)[0]
                    struct.pack_into(order + "II", data, offset, 144, 2)
                    return bytes(data)
                if damage == "interop-value":
                    assert b"0100" in block
                    return block.replace(b"0100", b"0200")
                exif = pv.exif_tools.load(block)
                exif[315] = "synthetic-added-field"
                return pv.exif_tools.strip_prefix(exif.tobytes())

            _r1_replace_exif(Path(out_path), mutate)

    record = pv.verify_export(
        source,
        guard,
        photo_class="JPG-A",
        bit_depth=16,
        force_cpu=True,
        keep=True,
        exports=composition.export_jobs(writer=Mutated()),
    )
    assert not record["v5_ok"], f"byte-level EXIF mutation passed: {damage}"
    assert "v5_kept_exif" in record["failed_checks"]
    expected = {
        "rational-bytes": "IFD0.282",
        "added-field": "IFD0.315",
        "interop-value": "Interop.2",
    }
    assert expected[damage] in record["changed_kept_fields"]
    assert "text_kept_fields_equal" in record
    assert record["text_kept_fields_equal"] is (damage != "added-field")


def test_r1_source_exif_parse_failure_cannot_pass(configured, monkeypatch):
    config, guard = configured
    source = _private_jpeg(config)
    raw = pv._raw_exif(source.read_bytes(), "jpeg")
    describe = pv.exif_tools.describe

    def fail_source(block):
        if block == raw:
            raise ValueError("synthetic parse failure")
        return describe(block)

    monkeypatch.setattr(pv.exif_tools, "describe", fail_source)
    record = pv.verify_export(
        source,
        guard,
        photo_class="JPG-Z",
        bit_depth=8,
        force_cpu=True,
        exports=composition.export_jobs(writer=DropKeptExif()),
    )
    assert not record["v5_ok"], "present unparsed EXIF passed vacuously"
    assert "v5_kept_exif" in record["failed_checks"]


def _r1_stub_memory(monkeypatch, *, os_peak=None, active=2, free=7000, reason="CPU: forced"):
    class Sampler(StubMemorySampler):
        def record(self):
            return {
                **super().record(),
                "os_peak_working_set_bytes": os_peak,
                "rss_active_samples": active,
                "device_active_samples": active,
            }

    monkeypatch.setattr(pv, "MemorySampler", Sampler)
    monkeypatch.setattr(
        pv,
        "device_memory",
        lambda: {"free_bytes": free, "total_bytes": free + 5000, "used_bytes": 5000},
    )
    monkeypatch.setattr(pv, "launch_runner", lambda *a, **k: (0, {"items": [{"device": reason}]}))


def test_r1_os_peak_also_enforces_ram_limit(sample, configured, monkeypatch):
    _, guard = configured
    _r1_stub_memory(monkeypatch, os_peak=20_000_000_000)
    record = pv.verify_memory(
        sample("jpeg-gradient-none"), guard, photo_class="JPG-Z", force_cpu=True
    )
    assert not record["ram_within_limit"], "OS peak above limit was ignored"
    assert "memory_ram_limit" in record["failed_checks"]


def test_r1_baseline_and_final_are_not_active_samples(sample, configured, monkeypatch):
    _, guard = configured
    _r1_stub_memory(monkeypatch, active=0)
    record = pv.verify_memory(
        sample("jpeg-gradient-none"), guard, photo_class="JPG-Z", force_cpu=True
    )
    assert "memory_rss_measurement" in record["failed_checks"], "no active RSS sample passed"
    assert "memory_device_measurement" in record["failed_checks"]


def test_r1_sampler_counts_only_live_runner_samples(sample, configured, monkeypatch):
    _, guard = configured

    class Process:
        def memory_info(self):
            return SimpleNamespace(rss=1000)

        def children(self, recursive):
            return []

    monkeypatch.setattr(pv.psutil, "Process", lambda _: Process())
    monkeypatch.setattr(
        pv, "device_memory", lambda: {"free_bytes": 7000, "total_bytes": 12000, "used_bytes": 5000}
    )
    record = pv.verify_memory(
        sample("jpeg-gradient-none"), guard, photo_class="JPG-Z", force_cpu=True
    )
    assert record.get("rss_active_samples", 0) > 0, "runner lifetime was not sampled"
    assert record.get("device_active_samples", 0) > 0
    assert not record["failed_checks"]


def test_r1_memory_scope_is_explicit(sample, configured, monkeypatch):
    _, guard = configured
    _r1_stub_memory(monkeypatch)
    record = pv.verify_memory(
        sample("jpeg-gradient-none"), guard, photo_class="JPG-Z", force_cpu=True
    )
    assert record.get("rss_scope") == "tool-runner-tree-including-sampler-children"


def test_r1_estimate_fit_is_strict(sample, configured, monkeypatch):
    _, guard = configured
    image, _ = PhotoReader().read(sample("jpeg-gradient-none"))
    h, w = image.pixels.shape[:2]
    estimate = memory_estimate_bytes(h, w, "c3")
    _r1_stub_memory(monkeypatch, free=estimate)
    record = pv.verify_memory(
        sample("jpeg-gradient-none"), guard, photo_class="JPG-Z", force_cpu=True
    )
    assert record.get("estimate_fits_free_before") is False, "equality must not fit"
    assert record["estimate_exceeds_free_before"] is False


@pytest.mark.parametrize(
    "reason,capacity",
    [("CPU: no CUDA device", False), ("CPU: estimate 3 MiB exceeds free 2 MiB", True)],
)
def test_r1_capacity_fallback_is_distinct(sample, configured, monkeypatch, reason, capacity):
    _, guard = configured
    _r1_stub_memory(monkeypatch, reason=reason)
    record = pv.verify_memory(sample("jpeg-gradient-none"), guard, photo_class="JPG-Z")
    assert record.get("memory_capacity_fallback") is capacity
    assert record["automatic_fallback"]


def _r1_cli(config, tmp_path, command, selected, **kwargs):
    path, classes = _class_map(tmp_path)
    config_path = tmp_path / "r1.local.toml"
    config_path.write_text(
        f"footage_path = '{config.footage_path}'\nworking_path = '{config.working_path}'\n",
        encoding="ascii",
    )
    args = [
        command,
        "--config",
        str(config_path),
        "--class-map",
        str(path),
        "--name",
        "r1",
        "--files",
        *selected(classes),
    ]
    if command == "export":
        args += ["--bit-depth", "8", "--force-cpu"]
    return pv.main(args), classes


def test_r1_inconclusive_continues_without_becoming_a_pass(
    configured, tmp_path, monkeypatch, capsys, sample
):
    monkeypatch.chdir(tmp_path)
    config, _ = configured
    seen = []
    symmetric = np.broadcast_to(np.linspace(0, 255, 64)[:, None, None], (64, 96, 3)).copy()
    source = sample("heic-ad24-neither")

    def orientation(path, run_guard, **kwargs):
        seen.append(path.name)
        if len(seen) == 1:
            image, meta = PhotoReader().read(source)
            with pytest.MonkeyPatch.context() as patch:
                patch.setattr(
                    pv,
                    "read_photo",
                    lambda _: (replace(image, pixels=symmetric.astype(np.float32) / 255), meta),
                )
                patch.setattr(pv, "ffmpeg_decode", lambda *a: symmetric)
                return pv.verify_orientation(path, run_guard, **kwargs)
        return {
            "file": path.name,
            "class": kwargs["photo_class"],
            "read_ok": True,
            "orientation_ok": True,
            "failed_checks": [],
        }

    # Keep header/class checking real: selected synthetic HEICs have identity layouts.
    _, classes = _class_map(tmp_path)
    for name in classes["HEIC-0"]["files"][:2]:
        shutil.copyfile(source, config.footage_path / "Phone" / name)
    real_verify = pv.verify_orientation

    def routed(path, run_guard, **kwargs):
        # Avoid recursion while retaining the real discrimination/status logic.
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(pv, "verify_orientation", real_verify)
            return orientation(path, run_guard, **kwargs)

    monkeypatch.setattr(pv, "verify_orientation", routed)
    status, _ = _r1_cli(config, tmp_path, "orientation", lambda c: c["HEIC-0"]["files"][:2])
    summary = json.loads(capsys.readouterr().out)
    assert len(seen) == 2, "inconclusive frame hid later inputs"
    assert status == 1 and not summary["complete"]
    row = summary["classes"]["HEIC-0"]
    assert row["orientation_inconclusive_count"] == 1
    assert row["orientation_ok_passed"] == 1 and row["orientation_ok_failed"] == 0
    assert len(row["orientation_inconclusive_files"]) == 1
    assert row["orientation_inconclusive_files"] == classes["HEIC-0"]["files"][:1]


def test_r1_owner_map_rejects_wrong_irot(configured, tmp_path, capsys, monkeypatch, sample):
    monkeypatch.chdir(tmp_path)
    config, _ = configured
    _, classes = _class_map(tmp_path)
    name = classes["HEIC-180"]["representative"]
    shutil.copyfile(sample("heic-ad24-both"), config.footage_path / "Phone" / name)
    status, _ = _r1_cli(
        config, tmp_path, "orientation", lambda c: [c["HEIC-180"]["representative"]]
    )
    summary = json.loads(capsys.readouterr().out)
    assert status == 1, "wrong irot was accepted into an owner class"
    assert "class_layout" in summary["records"][0]["failed_checks"]


def _r1_generated_heic(guard, orientation, *, grid=True, thumbnail=True):
    upright = spike.upright_image(8, 384, 256)
    stored = spike.stored_image(upright, orientation)
    h, w = stored.shape[:2]
    path = guard.check(guard.root / f"generated-{orientation}-{grid}-{thumbnail}.heic")
    encoder = CtxEncode(HeifCompressionFormat.HEVC, quality=100, chroma="444")
    encoder.add_image(
        (w, h),
        "RGB",
        np.ascontiguousarray(stored).tobytes(),
        image_orientation=orientation,
        primary=True,
        exif=spike.source_exif(orientation, w, h),
        tile_size=128 if grid else 0,
        thumbnails=[192] if thumbnail else [],
    )
    encoder.save(str(path))
    return path, upright.astype(np.float64)


@pytest.mark.parametrize("orientation,irot", [(1, 0), (8, 90), (3, 180), (6, 270)])
def test_r1_real_grid_rotations_and_thumbnail_class_counts(configured, orientation, irot):
    _, guard = configured
    source, upright = _r1_generated_heic(guard, orientation)
    layout = pv.read_layout(source.read_bytes())
    assert layout.is_grid and layout.item_type == "grid", "control must be a real grid"
    assert (layout.irot or 0) == irot
    decoded = pv.ffmpeg_decode(source, guard.root / "grid-oracle.png", guard)
    assert pv.compare_poses(decoded, upright)["orientation_ok"], (
        "FFmpeg grid rotation disagrees with generated scene"
    )
    record = pv.verify_orientation(source, guard, photo_class=f"HEIC-{irot}")
    assert record["orientation_ok"]
    summary = pv.summarise([record], command="orientation")
    row = summary["classes"][f"HEIC-{irot}"]
    assert row.get("thumbnail_available_count") == 1, "thumbnail evidence is missing from class row"
    assert row["thumbnail_concordant_count"] == 1
    assert row["thumbnail_discordant_count"] == 0
    if irot == 180:
        mutant = pv.compare_poses(np.rot90(decoded, 2), upright)
        assert "orientation_upright" in mutant["failed_checks"]


def test_r1_real_thumbnail_item_is_decoded(configured):
    _, guard = configured
    source, _ = _r1_generated_heic(guard, 3)
    assert len(pv.read_layout(source.read_bytes()).thumbnail_ids) == 1
    thumbnail = pv.thumbnail_decode(source)
    assert thumbnail is not None and list(thumbnail.shape[:2]) == [128, 192]
    record = pv.verify_orientation(source, guard, photo_class="HEIC-180")
    assert record["thumbnail_witness"]["available"]
    assert record["thumbnail_witness"]["orientation_ok"], (
        "real thumbnail could not be compared at a common size"
    )


def test_r1_decoder_versions_are_safe_and_reproducible(sample, configured):
    _, guard = configured
    record = pv.verify_orientation(sample("heic-ad24-both"), guard, photo_class="HEIC-270")
    versions = record.get("decoder_versions", {})
    assert set(versions) == {"ffmpeg", "pillow_heif", "libheif"}, (
        "decoder versions were not recorded"
    )
    assert versions["pillow_heif"] == pillow_heif.__version__
    assert versions["libheif"] == pillow_heif.libheif_version()
    contaminated = {
        **record,
        "decoder_versions": {**versions, "ffmpeg": "private/path GPS sentinel"},
    }
    safe = pv.summarise([contaminated], command="orientation")
    assert "private/path" not in json.dumps(safe)


@pytest.mark.parametrize("order,header", [("<", b"II"), (">", b"MM")])
def test_r1_raw_inventory_preserves_types_counts_duplicates_and_pointer_types(order, header):
    # Independently laid-out classic TIFF: IFD0 at 8, Exif at 50, Interop at 80.
    def entry(tag, kind, count, payload):
        return struct.pack(order + "HHI", tag, kind, count) + payload

    def pointer(offset):
        return struct.pack(order + "I", offset)

    raw = (
        header
        + struct.pack(order + "HI", 42, 8)
        + struct.pack(order + "H", 3)
        + entry(271, 2, 4, b"AB\0\0") * 2
        + entry(34665, 4, 1, pointer(50))
        + pointer(0)
        + struct.pack(order + "H", 2)
        + entry(40962, 4, 1, pointer(96))
        + entry(40965, 4, 1, pointer(80))
        + pointer(0)
        + struct.pack(order + "H", 1)
        + entry(2, 7, 4, b"0100")
        + pointer(0)
    )
    inventory = pv._entry_inventory(raw)
    assert set(inventory) == {("IFD0", 271), ("IFD0", 34665), ("Exif", 40965), ("Interop", 2)}
    assert dict(inventory[("IFD0", 271)]) == {(2, 4, b"AB\0\0"): 2}
    assert dict(inventory[("Interop", 2)]) == {(7, 4, b"0100"): 1}
    for at, kind, count in ((10, 7, 4), (10, 2, 3), (34, 13, 1)):
        mutant = bytearray(raw)
        struct.pack_into(order + "HI", mutant, at + 2, kind, count)
        assert pv._entry_inventory(bytes(mutant)) != inventory
    # Relocating children is legal; changing their pointer type is not.
    relocated = bytearray(raw[:50] + b"padding!" + raw[50:])
    struct.pack_into(order + "I", relocated, 42, 58)
    struct.pack_into(order + "I", relocated, 58 + 2 + 12 + 8, 88)
    assert pv._entry_inventory(bytes(relocated)) == inventory
    # IFD1 is explicitly discarded, even when its pointer cannot be followed.
    thumbnail = bytearray(raw)
    struct.pack_into(order + "I", thumbnail, 46, 99999)
    assert pv._entry_inventory(bytes(thumbnail)) == inventory


def test_r1_no_source_exif_is_distinct_from_parse_failure(configured):
    config, guard = configured
    source = config.footage_path / "Phone" / "no-exif.JPG"
    PILImage.fromarray(spike.upright_image(8, 96, 64)).save(source)
    record = pv.verify_export(source, guard, photo_class="JPG-Z", bit_depth=8, force_cpu=True)
    assert not record["raw_exif_present"] and record["kept_exif_parse_ok"]
    assert record["v5_ok"] and record["kept_fields_equal"]


def test_r1_owner_map_rejects_jpeg_as_heic(configured, tmp_path, capsys, monkeypatch, sample):
    monkeypatch.chdir(tmp_path)
    config, _ = configured
    _, classes = _class_map(tmp_path)
    source = sample("jpeg-gradient-none")
    name = classes["HEIC-0"]["representative"]
    shutil.copyfile(source, config.footage_path / "Phone" / name)
    status, _ = _r1_cli(config, tmp_path, "orientation", lambda c: [c["HEIC-0"]["representative"]])
    summary = json.loads(capsys.readouterr().out)
    assert status == 1 and "class_layout" in summary["records"][0]["failed_checks"]


def test_r1_gps_kept_uses_byte_fidelity(configured):
    config, guard = configured
    source = _private_jpeg(config)

    class GpsBytes(PhotoWriter):
        def write(self, image, meta, out_path, *, bit_depth, provenance):
            super().write(image, meta, out_path, bit_depth=bit_depth, provenance=provenance)

            def mutate(block):
                data = bytearray(block)
                order, pointer_at = _r1_root_entry(data, 34853)
                gps = struct.unpack_from(order + "I", data, pointer_at + 8)[0]
                count = struct.unpack_from(order + "H", data, gps)[0]
                for index in range(count):
                    at = gps + 2 + index * 12
                    if struct.unpack_from(order + "H", data, at)[0] == 2:
                        offset = struct.unpack_from(order + "I", data, at + 8)[0]
                        n, d = struct.unpack_from(order + "II", data, offset)
                        struct.pack_into(order + "II", data, offset, n * 2, d * 2)
                        return bytes(data)
                raise AssertionError("test GPS entry missing")

            _r1_replace_exif(Path(out_path), mutate)

    record = pv.verify_export(
        source,
        guard,
        photo_class="JPG-Z",
        bit_depth=8,
        force_cpu=True,
        exports=composition.export_jobs(writer=GpsBytes()),
    )
    assert not record["gps_kept"], "text-equal GPS bytes were incorrectly called kept"
    assert "GPS.2" in record["changed_kept_fields"] and not record["v5_ok"]


def test_r1_known_os_limit_failure_survives_missing_active_samples(sample, configured, monkeypatch):
    _, guard = configured
    _r1_stub_memory(monkeypatch, active=0, os_peak=20_000_000_000)
    record = pv.verify_memory(
        sample("jpeg-gradient-none"), guard, photo_class="JPG-Z", force_cpu=True
    )
    assert "memory_ram_limit" in record["failed_checks"], (
        "known OS limit breach was hidden by missing samples"
    )
    assert "memory_rss_measurement" in record["failed_checks"]
    assert record["ram_within_limit"] is False


@pytest.mark.parametrize("kind", ["png", "jpeg", "heic"])
@pytest.mark.parametrize("damage", ["drop", "swap"])
def test_r2_source_icc_is_independent_of_reader(sample, configured, monkeypatch, kind, damage):
    _, guard = configured
    source = sample(
        {
            "png": "png16-lowred-display-p3",
            "jpeg": "jpeg-gradient-display-p3",
            "heic": "heic8-gradient-display-p3",
        }[kind]
    )
    if kind == "heic":
        container = pillow_heif.open_heif(source)
        info = container[container.primary_index].info
        assert info["icc_profile_type"] in ("prof", "rICC")
        expected = info["icc_profile"]
    else:
        with PILImage.open(source) as header:
            expected = header.info["icc_profile"]
    with PILImage.open(sample("png8-gradient-srgb")) as header:
        replacement = header.info["icc_profile"]
    original = PhotoReader.read

    def corrupt(self, path):
        image, meta = original(self, path)
        color = replace(
            image.color,
            icc_profile=None if damage == "drop" else replacement,
            primaries="bt709",
            transfer="srgb",
            assumed=damage == "drop",
        )
        return replace(image, color=color), meta

    monkeypatch.setattr(PhotoReader, "read", corrupt)
    record = pv.verify_export(
        source, guard, photo_class="JPG-A", bit_depth=16, force_cpu=True, keep=True
    )
    assert _icc(_only_png(guard)) != expected, "reader mutation did not reach the real writer"
    assert not record["v5_ok"] and not record["d53_ok"], "reader-corrupted ICC passed V5/D53"
    assert "v5_icc_equal" in record["failed_checks"]
    assert record["source_icc_md5"] == hashlib.md5(expected).hexdigest()
    assert record["source_icc_present"]


def _r2_nclx(config, primaries):
    path = config.footage_path / "Phone" / f"nclx-{primaries}.heic"
    pixels = spike.upright_image(8, 32, 24)
    pillow_heif.encode(
        "RGB",
        (32, 24),
        pixels.tobytes(),
        str(path),
        quality=95,
        nclx_profile={
            "color_primaries": primaries,
            "transfer_characteristics": 13,
            "matrix_coefficients": 6,
            "full_range_flag": 1,
        },
    )
    return path


@pytest.mark.parametrize("primaries", [1, 12])
def test_r2_nclx_builtin_cannot_be_suppressed_by_reader(configured, monkeypatch, primaries):
    config, guard = configured
    source = _r2_nclx(config, primaries)
    original = PhotoReader.read

    def untagged(self, path):
        image, meta = original(self, path)
        return replace(
            image,
            color=replace(
                image.color, icc_profile=None, assumed=True, primaries="bt709", transfer="srgb"
            ),
        ), meta

    monkeypatch.setattr(PhotoReader, "read", untagged)
    record = pv.verify_export(
        source, guard, photo_class="HEIC-0", bit_depth=16, force_cpu=True, keep=True
    )
    assert _icc(_only_png(guard)) is None
    assert not record["v5_ok"] and not record["d53_ok"], "lost nclx silently removed D53 built-in"
    assert "v5_icc_equal" in record["failed_checks"]


@pytest.mark.parametrize(
    "primaries,digest",
    [(1, "ca34a0279325928fc9fd3fc7eff99eb9"), (12, "ee27975c71b9ed10be950a696f6fe6f4")],
)
def test_r2_nclx_builtin_matches_independent_contract(configured, primaries, digest):
    config, guard = configured
    record = pv.verify_export(
        _r2_nclx(config, primaries),
        guard,
        photo_class="HEIC-0",
        bit_depth=16,
        force_cpu=True,
        keep=True,
    )
    assert hashlib.md5(_icc(_only_png(guard))).hexdigest() == digest
    assert record["v5_ok"] and record["d53_ok"]


def _r2_directory(block, label):
    order = "<" if block[:2] == b"II" else ">"
    root = struct.unpack_from(order + "I", block, 4)[0]
    if label == "Exif":
        _, entry = _r1_root_entry(block, 34665)
        root = struct.unpack_from(order + "I", block, entry + 8)[0]
    count = struct.unpack_from(order + "H", block, root)[0]
    return (
        order,
        root,
        [bytearray(block[root + 2 + i * 12 : root + 14 + i * 12]) for i in range(count)],
    )


def _r2_d63_mutation(block, label, tag, damage):
    data = bytearray(block)
    order, _, entries = _r2_directory(block, label)
    index = next(
        i for i, entry in enumerate(entries) if struct.unpack_from(order + "H", entry)[0] == tag
    )
    entry = entries[index]
    kind = struct.unpack_from(order + "H", entry, 2)[0]
    value = int.from_bytes(entry[8 : 10 if kind == 3 else 12], "little" if order == "<" else "big")
    if damage == "type":
        struct.pack_into(order + "H", entry, 2, 4 if tag == 274 else 1)
        entry[8:12] = struct.pack(order + "I", value) if tag == 274 else bytes([value, 0, 0, 0])
    elif damage == "count":
        struct.pack_into(order + "H", entry, 2, 3)
        struct.pack_into(order + "I", entry, 4, 2)
        entry[8:12] = struct.pack(order + "HH", 1, 1)
    elif damage == "duplicate":
        entries.insert(index, bytearray(entry))
    elif damage == "missing":
        entries.pop(index)
    elif damage in {"version", "tab-version"}:
        value = b"Clearwater 0.5.7\0" if damage == "version" else b"Clearwater\t0.5.7\0"
        struct.pack_into(order + "I", entry, 4, len(value))
        struct.pack_into(order + "I", entry, 8, len(data))
        data.extend(value)
    elif damage == "extra-nul":
        value = b"Clearwater\0\0"
        struct.pack_into(order + "I", entry, 4, len(value))
        struct.pack_into(order + "I", entry, 8, len(data))
        data.extend(value)
    elif damage == "short":
        struct.pack_into(order + "H", entry, 2, 3)
        entry[8:12] = struct.pack(order + "H", value) + bytes(2)
    else:
        raise AssertionError("unknown test mutation")
    new_directory = len(data)
    data.extend(struct.pack(order + "H", len(entries)) + b"".join(entries) + bytes(4))
    if label == "IFD0":
        struct.pack_into(order + "I", data, 4, new_directory)
    else:
        _, pointer = _r1_root_entry(data, 34665)
        struct.pack_into(order + "I", data, pointer + 8, new_directory)
    return bytes(data)


class D63Mutation(PhotoWriter):
    def __init__(self, label, tag, damage):
        self.label, self.tag, self.damage = label, tag, damage

    def write(self, image, meta, out_path, *, bit_depth, provenance):
        super().write(image, meta, out_path, bit_depth=bit_depth, provenance=provenance)
        _r1_replace_exif(
            out_path, lambda block: _r2_d63_mutation(block, self.label, self.tag, self.damage)
        )


@pytest.mark.parametrize(
    "label,tag,field,check,damage",
    [
        ("IFD0", 274, "IFD0.Orientation", "v5_orientation", "type"),
        ("IFD0", 274, "IFD0.Orientation", "v5_orientation", "duplicate"),
        ("IFD0", 274, "IFD0.Orientation", "v5_orientation", "count"),
        ("IFD0", 274, "IFD0.Orientation", "v5_orientation", "missing"),
        ("IFD0", 305, "IFD0.Software", "v5_software", "extra-nul"),
        ("IFD0", 305, "IFD0.Software", "v5_software", "missing"),
        ("Exif", 40962, "Exif.ExifImageWidth", "v5_dimensions", "type"),
        ("Exif", 40963, "Exif.ExifImageHeight", "v5_dimensions", "duplicate"),
        ("Exif", 40962, "Exif.ExifImageWidth", "v5_dimensions", "count"),
        ("Exif", 40963, "Exif.ExifImageHeight", "v5_dimensions", "missing"),
    ],
)
@pytest.mark.filterwarnings("ignore:Metadata Warning, tag 274 had too many entries:UserWarning")
def test_r2_d63_structure_rejects_malformed_entries(
    sample, configured, label, tag, field, check, damage
):
    _, guard = configured
    record = pv.verify_export(
        sample("jpeg-gradient-none"),
        guard,
        photo_class="JPG-Z",
        bit_depth=8,
        force_cpu=True,
        exports=composition.export_jobs(writer=D63Mutation(label, tag, damage)),
    )
    assert not record["v5_ok"] and check in record["failed_checks"], (
        "malformed D63 structure passed V5"
    )
    expected = "count" if damage == "extra-nul" else damage
    assert {"field": field, "defect": expected} in record.get("d63_defects", []), (
        "D63 field/defect not recorded"
    )


@pytest.mark.parametrize(
    "damage,text", [("version", "Clearwater 0.5.7"), ("tab-version", "Clearwater\t0.5.7")]
)
def test_r2_software_version_uses_derived_count_and_records_string(
    sample, configured, damage, text
):
    _, guard = configured
    record = pv.verify_export(
        sample("jpeg-gradient-none"),
        guard,
        photo_class="JPG-Z",
        bit_depth=8,
        force_cpu=True,
        keep=True,
        exports=composition.export_jobs(writer=D63Mutation("IFD0", 305, damage)),
    )
    assert record["v5_ok"], "valid Software version suffix was rejected"
    assert record.get("software_seen") == text
    assert record.get("d63_defects") == []


def test_r2_dimensions_may_use_short(sample, configured):
    _, guard = configured
    record = pv.verify_export(
        sample("jpeg-gradient-none"),
        guard,
        photo_class="JPG-Z",
        bit_depth=8,
        force_cpu=True,
        exports=composition.export_jobs(writer=D63Mutation("Exif", 40962, "short")),
    )
    assert record["v5_ok"]


def test_r2_gps_pointer_is_part_of_kept_boolean(configured):
    config, guard = configured
    block = b"II" + struct.pack("<HIH", 42, 8, 1)
    block += struct.pack("<HHIII", 34853, 4, 1, 26, 0) + struct.pack("<HI", 0, 0)
    source = config.footage_path / "Phone" / "empty-gps.jpg"
    PILImage.new("RGB", (16, 12), (32, 64, 96)).save(source, exif=b"Exif\0\0" + block)
    record = pv.verify_export(source, guard, photo_class="JPG-Z", bit_depth=8, force_cpu=True)
    assert "IFD0.34853" in record["changed_kept_fields"] and not record["v5_ok"]
    assert not record["gps_kept"], "lost empty GPS pointer was called kept"
    assert record["gps_ifd_present"], "an empty source GPS IFD was reported absent"


@pytest.mark.parametrize("duration,gap", [(0.3, 0.5), (0.9, 1.1)])
def test_r2_device_cadence_includes_sample_duration(monkeypatch, duration, gap):
    clock = [0.0]

    class Process:
        def memory_info(self):
            return SimpleNamespace(rss=1000)

        def children(self, recursive):
            return []

    class Stop:
        calls = 0

        def wait(self, interval):
            self.calls += 1
            clock[0] += interval
            return self.calls > 2

    def device():
        clock[0] += duration
        return {"free_bytes": 7000, "total_bytes": 12000, "used_bytes": 5000}

    monkeypatch.setattr(time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(pv, "device_memory", device)
    sampler = pv.MemorySampler(Process())
    sampler._stop = Stop()
    sampler._loop(0.2, sampler._gpu)
    record = pv._safe_record(sampler.record())
    cadence = record.get("sampling_cadence_s", {}).get("device", {})
    assert cadence.get("mean") == pytest.approx(gap), "device cadence missing or nominal"
    assert cadence["min"] == pytest.approx(gap) and cadence["max"] == pytest.approx(gap)
    assert cadence["gap_count"] == 2
    assert record["sampler_elapsed_s"] == pytest.approx(3 * (duration + 0.2))
    assert record["sample_interval_kind"] == "wait-after-sample"


def test_r2_sampler_elapsed_finishes_at_stop(monkeypatch):
    clock = [10.0]

    class Process:
        def memory_info(self):
            return SimpleNamespace(rss=1000)

        def children(self, recursive):
            return []

    monkeypatch.setattr(time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(
        pv, "device_memory", lambda: {"free_bytes": 7000, "total_bytes": 12000, "used_bytes": 5000}
    )
    sampler = pv.MemorySampler(Process())
    sampler.start()
    try:
        clock[0] = 12.0
        sampler.attach(SimpleNamespace(poll=lambda: None))
        clock[0] = 20.0
    finally:
        sampler.stop()
    clock[0] = 30.0
    assert sampler.record()["sampler_elapsed_s"] == 10.0, (
        "elapsed time stopped at runner attachment"
    )


def test_r2_overlapping_sample_completions_keep_chronological_cadence(monkeypatch):
    clock = [0.0]
    calls = [0]

    class Process:
        def memory_info(self):
            return SimpleNamespace(rss=1000)

        def children(self, recursive):
            return []

    def device():
        calls[0] += 1
        if calls[0] == 2:
            # Re-enter the real sampler to complete a later-started observation
            # first, as attach() and the background thread can do concurrently.
            clock[0] = 1.0
            sampler._gpu()
            clock[0] = 1.5
        return {"free_bytes": 7000, "total_bytes": 12000, "used_bytes": 5000}

    monkeypatch.setattr(time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(pv, "device_memory", device)
    sampler = pv.MemorySampler(Process())
    clock[0] = 0.5
    sampler._gpu()
    cadence = sampler.record()["sampling_cadence_s"]["device"]
    assert cadence["min"] == cadence["mean"] == cadence["max"] == 0.5, (
        "completion order corrupted chronological sample gaps"
    )


# Reviewer A round 3 terminating clean-up controls.
@pytest.mark.parametrize(
    "label,fixture,observed",
    [
        ("JPG-A", "jpeg-gradient-none", "JPG-Z/M"),
        ("JPG-Z", "jpeg-gradient-display-p3", "JPG-A"),
        ("JPG-M", "jpeg-gradient-display-p3", "JPG-A"),
    ],
)
def test_r3_jpeg_icc_class_mismatch_is_refused(
    configured, tmp_path, capsys, sample, label, fixture, observed
):
    config, _ = configured
    _, classes = _class_map(tmp_path)
    name = classes[label]["representative"]
    shutil.copyfile(sample(fixture), config.footage_path / "Phone" / name)
    status, _ = _r1_cli(config, tmp_path, "export", lambda c: [c[label]["representative"]])
    record = json.loads(capsys.readouterr().out)["records"][0]
    assert status == 1, "ICC-mislabelled JPEG was pooled into its declared class"
    assert record["file"] == name and record["class"] == label
    assert record.get("observed_class") == observed, "refusal omitted both class facts"
    assert record["failed_checks"] == ["class_layout"]


@pytest.mark.parametrize(
    "label,fixture",
    [
        ("JPG-A", "jpeg-gradient-display-p3"),
        ("JPG-Z", "jpeg-gradient-none"),
        ("JPG-M", "jpeg-gradient-none"),
    ],
)
def test_r3_jpeg_icc_class_positive(sample, label, fixture):
    assert pv._owner_class_matches(sample(fixture), label)


@pytest.mark.parametrize("damage", ["nan", "rgba", "runtime"])
def test_r3_orientation_product_failure_labels(sample, configured, monkeypatch, damage):
    _, guard = configured
    original = pv.read_photo

    def broken(path):
        if damage == "runtime":
            raise RuntimeError("private synthetic read error")
        image, meta = original(path)
        pixels = image.pixels.copy()
        if damage == "nan":
            pixels[0, 0, 0] = np.nan
        else:
            pixels = np.concatenate([pixels, pixels[:, :, :1]], axis=2)
        return replace(image, pixels=pixels), meta

    monkeypatch.setattr(pv, "read_photo", broken)
    try:
        record = pv.verify_orientation(sample("heic-ad24-both"), guard, photo_class="HEIC-270")
    except RuntimeError:
        pytest.fail("unexpected product-read exception escaped its step")
    expected = "product_read_failed" if damage == "runtime" else "product_pixels_failed"
    assert record.get("failure_code") == expected, "product failure blamed on oracle or runner"
    assert record["failed_checks"] == (["read_failed"] if damage == "runtime" else [expected])
    assert not record.get("orientation_ok", False)


@pytest.mark.parametrize(
    "step,code",
    [
        ("ffmpeg_decode", "oracle_failed"),
        ("compare_poses", "orientation_comparison_failed"),
    ],
)
def test_r3_orientation_step_failure_labels(sample, configured, monkeypatch, step, code):
    _, guard = configured

    def broken(*args, **kwargs):
        raise ValueError("private synthetic step error")

    monkeypatch.setattr(pv, step, broken)
    record = pv.verify_orientation(sample("heic-ad24-both"), guard, photo_class="HEIC-270")
    assert record.get("failure_code") == code, "comparison failure blamed on oracle"
    assert record["failed_checks"] == [code]


@pytest.mark.parametrize("step", ["_png_metadata", "read_photo"])
def test_r3_output_parse_failure_label(sample, configured, monkeypatch, step):
    _, guard = configured
    original = getattr(pv, step)

    def broken(path):
        if step == "_png_metadata" or Path(path).suffix.lower() == ".png":
            raise ValueError("private synthetic output parse error")
        return original(path)

    monkeypatch.setattr(pv, step, broken)
    record = pv.verify_export(
        sample("jpeg-gradient-none"), guard, photo_class="JPG-Z", bit_depth=8, force_cpu=True
    )
    assert record.get("failure_code") == "output_parse_failed", "output parse blamed on runner"
    assert record["runner_exit"] == 0 and record["retained"]
    assert record["failed_checks"] == ["output_parse_failed"]
    assert not record["v5_ok"] and not record["v9_ok"] and not record["d53_ok"]


def test_r3_orientation_command_unexpected_failure_label(
    sample, configured, tmp_path, capsys, monkeypatch
):
    config, _ = configured
    _, classes = _class_map(tmp_path)
    name = classes["HEIC-0"]["representative"]
    shutil.copyfile(sample("heic-ad24-neither"), config.footage_path / "Phone" / name)

    def broken(*args, **kwargs):
        raise RuntimeError("private synthetic orientation error")

    monkeypatch.setattr(pv, "verify_orientation", broken)
    status, _ = _r1_cli(config, tmp_path, "orientation", lambda c: [name])
    record = json.loads(capsys.readouterr().out)["records"][0]
    assert status == 1 and record.get("failure_code") == "orientation_failed", (
        "orientation command exception blamed on runner"
    )
    assert record["failed_checks"] == ["orientation_failed"]


def test_r3_orientation_explicit_jpeg_is_refused(sample, configured, tmp_path, capsys, monkeypatch):
    config, _ = configured
    _, classes = _class_map(tmp_path)
    heic = classes["HEIC-0"]["representative"]
    jpeg = classes["JPG-Z"]["representative"]
    shutil.copyfile(sample("heic-ad24-neither"), config.footage_path / "Phone" / heic)
    shutil.copyfile(sample("jpeg-gradient-none"), config.footage_path / "Phone" / jpeg)
    seen = []
    monkeypatch.setattr(
        pv,
        "verify_orientation",
        lambda *a, **k: (
            seen.append(a[0].name)
            or {
                "file": a[0].name,
                "class": k["photo_class"],
                "read_ok": True,
                "orientation_ok": True,
                "failed_checks": [],
            }
        ),
    )
    status, _ = _r1_cli(config, tmp_path, "orientation", lambda c: [heic, jpeg])
    summary = json.loads(capsys.readouterr().out)
    assert status == 2 and not seen, "explicit JPEG was silently skipped"
    record = summary["records"][0]
    assert record["file"] == jpeg and record["class"] == "JPG-Z"
    assert (
        record.get("refusal_reason")
        == "orientation requires HEIC; explicitly selected JPEG refused"
    )
    assert record["failed_checks"] == ["invalid_request"]


# CHARC 2aaa7e0a: one-pixel odd 4:2:0 oracle equivalence, no wider tolerance.
def _r9_odd_grid(guard, *, orientation=1, chroma="420", width=257, height=192):
    stored = np.repeat(
        np.random.default_rng(921).integers(16, 240, (height, width, 1), dtype=np.uint8),
        3,
        axis=2,
    )
    path = guard.check(guard.root / "odd-grid.heic")
    encoder = CtxEncode(HeifCompressionFormat.HEVC, quality=100, chroma=chroma)
    encoder.add_image(
        (width, height),
        "RGB",
        stored.tobytes(),
        image_orientation=orientation,
        primary=True,
        tile_size=128,
        exif=spike.source_exif(orientation, width, height),
    )
    encoder.save(str(path))
    container = pillow_heif.open_heif(path)
    assert container[container.primary_index].info["chroma"] == int(chroma)
    layout = pv.read_layout(path.read_bytes())
    assert layout.is_grid and layout.item_type == "grid"
    return path, stored if orientation == 1 else np.rot90(stored, -1)


@pytest.mark.parametrize("orientation,axis", [(1, 1), (6, 0)])
def test_r9_real_odd_420_grid_uses_last_edge(configured, orientation, axis, record_property):
    _, guard = configured
    source, known = _r9_odd_grid(guard, orientation=orientation)
    record = pv.verify_orientation(
        source, guard, photo_class="HEIC-0" if axis == 1 else "HEIC-270", max_side=4096
    )
    assert record.get("orientation_ok"), "odd 4:2:0 grid refused as " + str(
        record.get("failure_code")
    )
    oracle = np.asarray(
        PILImage.open(next(guard.root.rglob("oracle.png"))).convert("RGB"), dtype=float
    )
    first = np.take(known, range(1, known.shape[axis]), axis=axis).astype(float)
    last = np.take(known, range(known.shape[axis] - 1), axis=axis).astype(float)
    first_error, last_error = float(abs(first - oracle).mean()), float(abs(last - oracle).mean())
    assert last_error < 6 and first_error > 10
    assert record["oracle_size_rounded"] is True
    assert record["oracle_crop_edge"] == "last", "real FFmpeg drop-edge disagrees with construction"
    assert record["oracle_size"][1 - axis] == record["decoded_size"][1 - axis] - 1
    record_property(
        "odd_420_real_edge",
        {"edge": "last", "first_mean_255": first_error, "last_mean_255": last_error},
    )


@pytest.mark.parametrize("axis,orientation", [(1, 1), (0, 6)])
@pytest.mark.parametrize("edge", ["first", "last"])
def test_r9_both_crop_edges_before_all_poses(configured, monkeypatch, axis, orientation, edge):
    _, guard = configured
    source, _ = _r9_odd_grid(guard, orientation=orientation)
    image, _ = PhotoReader().read(source)
    pixels = image.pixels * 255
    indices = range(1, pixels.shape[axis]) if edge == "first" else range(pixels.shape[axis] - 1)
    planted = np.take(pixels, indices, axis=axis)
    monkeypatch.setattr(pv, "ffmpeg_decode", lambda *a: planted)
    record = pv.verify_orientation(source, guard, photo_class="HEIC-0", max_side=4096)
    assert record.get("orientation_ok"), "permitted one-pixel crop did not compare"
    assert record.get("oracle_size_rounded") is True
    assert record.get("oracle_crop_edge") == edge, "wrong planted crop edge selected"
    assert len(record["scores_by_pose"]) == 8 and len(record["shape_mismatches"]) == 4
    assert record["winning_pose"] == 1 and record["upright_mean_255"] < 0.01
    assert record["nearest_other_mean_255"] > 10
    row = pv.summarise([record], command="orientation")["classes"]["HEIC-0"]
    assert row.get("oracle_size_rounded_count") == 1
    assert row.get("oracle_crop_edge_counts") == {
        "first": int(edge == "first"),
        "last": int(edge == "last"),
    }


@pytest.mark.parametrize("damage", ["two-pixels", "tile"])
def test_r9_decode_rejects_larger_size_difference(configured, monkeypatch, damage):
    _, guard = configured
    source, _ = _r9_odd_grid(guard)
    run = pv.subprocess.run

    def corrupted(args, **kwargs):
        done = run(args, **kwargs)
        if args[0] == "ffmpeg" and "-i" in args:
            path = Path(args[-1])
            with PILImage.open(path) as opened:
                pixels = np.asarray(opened.convert("RGB"))
            # The real decode is 256 wide; source is 257. Make it two short
            # or one 128x128 tile, independently of the instrument's size gate.
            pixels = pixels[:, :255] if damage == "two-pixels" else pixels[:128, :128]
            PILImage.fromarray(pixels).save(path)
        return done

    monkeypatch.setattr(pv.subprocess, "run", corrupted)
    record = pv.verify_orientation(source, guard, photo_class="HEIC-0")
    assert record.get("failure_code") == "oracle_failed"
    assert record["failed_checks"] == ["oracle_failed"] and not record["orientation_ok"]
    assert record.get("oracle_size_rounded") is not True


@pytest.mark.parametrize(
    "damage", ["444", "even", "two-axes", "larger", "unknown-chroma", "product-extra"]
)
def test_r9_near_misses_still_fail(configured, monkeypatch, damage):
    _, guard = configured
    source, _ = _r9_odd_grid(
        guard,
        chroma="444" if damage == "444" else "420",
        width=256 if damage in {"even", "product-extra"} else 257,
    )
    image, meta = PhotoReader().read(source)
    pixels = image.pixels * 255
    reference = pixels[:, :-1]
    if damage == "product-extra":
        reference = pixels
        image = replace(image, pixels=np.pad(image.pixels, ((0, 0), (0, 1), (0, 0))))
    elif damage == "two-axes":
        reference = reference[:-1]
    elif damage == "larger":
        reference = np.pad(pixels, ((0, 0), (0, 1), (0, 0)))
    if damage == "unknown-chroma":
        open_heif = pillow_heif.open_heif

        def unknown(*args, **kwargs):
            container = open_heif(*args, **kwargs)
            container[container.primary_index].info.pop("chroma", None)
            return container

        monkeypatch.setattr(pillow_heif, "open_heif", unknown)
    monkeypatch.setattr(pv, "read_photo", lambda _: (image, meta))
    monkeypatch.setattr(pv, "ffmpeg_decode", lambda *a: reference)
    record = pv.verify_orientation(source, guard, photo_class="HEIC-0")
    assert not record["orientation_ok"] and "orientation_size" in record["failed_checks"]
    assert record.get("oracle_size_rounded") is not True


def test_r9_unrounded_summary_and_projection(sample, configured):
    _, guard = configured
    record = pv.verify_orientation(sample("heic-ad24-both"), guard, photo_class="HEIC-270")
    assert record["orientation_ok"] and record.get("oracle_size_rounded") is False
    row = pv.summarise([record], command="orientation")["classes"]["HEIC-270"]
    assert row.get("oracle_size_rounded_count") == 0
    assert row.get("oracle_crop_edge_counts") == {"first": 0, "last": 0}
    safe = pv._safe_record({"oracle_size_rounded": "private", "oracle_crop_edge": "private/path"})
    assert "oracle_size_rounded" not in safe and "oracle_crop_edge" not in safe


# Reviewer B: reject shared decoder size loss and silence DEBUG EXIF values.
@pytest.mark.parametrize("orientation,axis", [(1, 1), (6, 0)])
def test_b1_product_crop_matching_oracle_still_fails_primary_size(
    configured, monkeypatch, orientation, axis
):
    _, guard = configured
    source, _ = _r9_odd_grid(guard, orientation=orientation)
    label = "HEIC-0" if orientation == 1 else "HEIC-270"
    intact = pv.verify_orientation(source, guard, photo_class=label, max_side=4096)
    assert intact["orientation_ok"] and intact["oracle_size_rounded"] is True
    assert intact["oracle_crop_edge"] == "last"
    image, meta = PhotoReader().read(source)
    pixels = np.take(image.pixels, range(image.pixels.shape[axis] - 1), axis=axis)
    monkeypatch.setattr(pv, "read_photo", lambda _: (replace(image, pixels=pixels), meta))
    damaged = pv.verify_orientation(source, guard, photo_class=label, max_side=4096)
    assert damaged["decoded_size"] == damaged["oracle_size"]
    assert not damaged["orientation_ok"], (
        "product crop matching FFmpeg escaped independent primary-size check"
    )
    assert "orientation_size" in damaged["failed_checks"]
    assert damaged["oracle_size_rounded"] is False


def test_b2_debug_export_never_logs_private_exif(configured, tmp_path, capsys, caplog):
    config, _ = configured
    _, classes = _class_map(tmp_path)
    name = classes["JPG-Z"]["representative"]
    source = config.footage_path / "Phone" / name
    secrets = {key: "B2_PRIVATE_" + key for key in ("MAKE", "MODEL", "SOFTWARE", "SERIAL", "GPS")}
    exif = PILImage.Exif()
    exif[271], exif[272], exif[305] = secrets["MAKE"], secrets["MODEL"], secrets["SOFTWARE"]
    exif[274] = 1
    exif[34665] = {42033: secrets["SERIAL"]}
    exif[34853] = {
        1: "N",
        2: (IFDRational(12), IFDRational(34), IFDRational(56)),
        27: b"ASCII\0\0\0" + secrets["GPS"].encode("ascii"),
    }
    PILImage.fromarray(spike.upright_image(8, 96, 64)).save(source, "JPEG", exif=exif)
    caplog.set_level(logging.DEBUG, logger="PIL.TiffImagePlugin")
    with caplog.at_level(logging.DEBUG):
        handler = logging.StreamHandler(sys.stderr)
        logging.getLogger().addHandler(handler)
        try:
            status, _ = _r1_cli(config, tmp_path, "export", lambda c: [name])
        finally:
            logging.getLogger().removeHandler(handler)
    streams = capsys.readouterr()
    summary = json.loads(streams.out)
    assert status == 0 and summary["records"][0]["v5_ok"]
    leaked_channels = [
        channel
        for channel, text in (
            ("caplog", caplog.text),
            ("raw stderr", streams.err),
            ("stdout", streams.out),
        )
        if any(secret in text for secret in secrets.values())
    ]
    assert not leaked_channels, "DEBUG EXIF sentinels reached " + ", ".join(leaked_channels)


@pytest.mark.parametrize(
    "stage,code", [("class", "class_check_failed"), ("verify", "verify_failed")]
)
def test_b3_export_exception_names_actual_step(
    configured, tmp_path, sample, capsys, monkeypatch, stage, code
):
    config, _ = configured
    _, classes = _class_map(tmp_path)
    names = classes["JPG-Z"]["files"][:2]
    for name in names:
        shutil.copyfile(sample("jpeg-gradient-none"), config.footage_path / "Phone" / name)

    def broken(*args):
        raise RuntimeError("synthetic private error")

    monkeypatch.setattr(pv, "_owner_class_matches" if stage == "class" else "_base", broken)
    status, _ = _r1_cli(config, tmp_path, "export", lambda c: names)
    summary = json.loads(capsys.readouterr().out)
    assert status == 1 and summary["attempted"] == 1 and not summary["complete"]
    record = summary["records"][0]
    assert record["failure_code"] == code, "exception attributed to a runner that never ran"
    assert record["failed_checks"] == [code] and "runner_exit" not in record
