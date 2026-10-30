"""WP3.6P instrument controls; owner I/O is isolated in one footage-marked node.

FFmpeg's default HEIF decode honours irot, not an EXIF-only Orientation. The
generated upright scene independently witnesses that limitation. These tests
never compensate FFmpeg's output by applying another transform.
"""

from __future__ import annotations

import hashlib
import io
import json
import shutil
import zlib
from dataclasses import replace
from pathlib import Path

import numpy as np
import photo_verify as pv
import pytest
from PIL import ExifTags
from PIL import Image as PILImage
from PIL.TiffImagePlugin import IFDRational

import headless_export as he
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

    def record(self):
        return {
            "rss_baseline_bytes": 1000,
            "rss_tree_peak_bytes": 9000,
            "os_peak_working_set_bytes": None,
            "device_used_baseline_bytes": 2000,
            "device_used_peak_bytes": 5000,
            "rss_samples": 3,
            "device_samples": 2,
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
