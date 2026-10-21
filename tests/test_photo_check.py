"""Tests of the photo check instrument (WP3.6 task 8): records, the write guard, the real leg."""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

import photo_check
from clearwater.io.photo import write_photo
from local_config import footage_available, load_local_config

SAMPLE_IDS = [
    "heic-ad24-both",
    "heic-ad24-exif-only",
    "png16-gradient-display-p3",
    "jpeg-orient-port-o6",
    "tiff8-lowred-none",
    "dng-by-extension",
]


def _config(tmp_path: Path) -> tuple[Path, Path, Path]:
    footage, work = tmp_path / "footage", tmp_path / "work"
    footage.mkdir()
    config = tmp_path / "local.toml"
    config.write_text(f"footage_path = '{footage}'\nworking_path = '{work}'\n", encoding="utf-8")
    return config, footage, work


def _snapshot(folder: Path) -> list[tuple[str, int, int]]:
    return sorted(
        (str(p.relative_to(folder)), p.stat().st_size, p.stat().st_mtime_ns)
        for p in folder.rglob("*")
        if p.is_file()
    )


def _records(run: Path) -> dict[str, dict[str, Any]]:
    return {
        json.loads(p.read_text(encoding="utf-8"))["file"]: json.loads(p.read_text(encoding="utf-8"))
        for p in sorted(run.glob("[0-9]*.json"))
    }


def test_the_records_hold_what_the_ledger_promises(
    tmp_path: Path, sample: Callable[[str], Path]
) -> None:
    config, footage, work = _config(tmp_path)
    for sample_id in SAMPLE_IDS:
        shutil.copy2(sample(sample_id), footage / sample(sample_id).name)
    cut = footage / "cut.jpg"
    cut.write_bytes(sample("jpeg-uniform-none").read_bytes()[:300])
    before = _snapshot(footage)
    assert photo_check.main(["--config", str(config), "--name", "t"]) == 0
    assert _snapshot(footage) == before, "the footage folder must not change"
    run = work / "wp3.6" / "photo-check" / "t"
    records = _records(run)
    heic = records["heic-ad24-both.heic"]
    assert heic["verdict"] == {"ok": True}
    assert heic["detected_format"] == "heic" and heic["source_format"] == "heic"
    layout = heic["heic"]
    assert (layout["irot"], layout["exif_orientation"], layout["grid"]) == (270, 6, False)
    assert layout["auxiliary_images"] is False and layout["ispe"] == [64, 96]
    assert heic["decoded_size"] == [96, 64] and heic["stored_size"] == [64, 96]
    assert records["heic-ad24-exif-only.heic"]["heic"]["irot"] is None
    p3 = records["png16-gradient-display-p3.png"]
    assert p3["color"]["primaries"] == "display-p3" and p3["color"]["bit_depth"] == 16
    assert p3["color"]["icc_description"] == "Clearwater synthetic Display P3"
    assert p3["round_trip"]["problems"] == []
    assert p3["round_trip"]["max_abs_sample_difference"] == 0.0
    jpeg = records["jpeg-orient-port-o6.jpg"]
    assert jpeg["orientation_tag"] == 6 and "IFD0.Orientation" in jpeg["exif_fields"]
    assert jpeg["round_trip"]["problems"] == []
    dng = records["dng-by-extension.dng"]
    assert dng["dng"] is True
    assert dng["verdict"]["ok"] is False and dng["verdict"]["kind"] == "unsupported"
    assert records["cut.jpg"]["verdict"]["kind"] == "unreadable"
    summary = json.loads((run / "summary.json").read_text(encoding="utf-8"))
    assert summary["photos"] == len(SAMPLE_IDS) + 1 and summary["round_trip_problems"] == {}
    assert {r["file"] for r in summary["refused"]} == {"dng-by-extension.dng", "cut.jpg"}


def test_every_output_stays_under_the_working_folder(
    tmp_path: Path, sample: Callable[[str], Path]
) -> None:
    config, footage, work = _config(tmp_path)
    shutil.copy2(sample("png8-uniform-none"), footage / "a.png")
    photo_check.main(["--config", str(config), "--name", "t"])
    assert {p.name for p in tmp_path.iterdir()} == {"footage", "work", "local.toml"}
    assert all(p.is_relative_to(work / "wp3.6") for p in work.rglob("*") if p.is_file())


def test_a_run_name_that_escapes_the_working_folder_is_refused(
    tmp_path: Path, sample: Callable[[str], Path]
) -> None:
    config, footage, _work = _config(tmp_path)
    shutil.copy2(sample("png8-uniform-none"), footage / "a.png")
    assert photo_check.main(["--config", str(config), "--name", "../../escape"]) == 3
    assert not (tmp_path / "escape").exists()


def test_no_photos_is_a_distinct_exit_code(tmp_path: Path) -> None:
    config, footage, _work = _config(tmp_path)
    (footage / "clip.mp4").write_bytes(b"x")
    assert photo_check.main(["--config", str(config)]) == 2


def test_a_round_trip_problem_is_recorded_not_swallowed(
    tmp_path: Path, sample: Callable[[str], Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    config, footage, work = _config(tmp_path)
    shutil.copy2(sample("png16-gradient-srgb"), footage / "a.png")

    def as_8_bit(image: Any, meta: Any, out: Path, *, bit_depth: int, provenance: Any) -> None:
        write_photo(image, meta, out, bit_depth=8, provenance=provenance)

    monkeypatch.setattr(photo_check, "write_photo", as_8_bit)
    assert photo_check.main(["--config", str(config), "--name", "t"]) == 1
    record = _records(work / "wp3.6" / "photo-check" / "t")["a.png"]
    assert any("samples differ" in p for p in record["round_trip"]["problems"])


@pytest.mark.footage
def test_the_real_photo_leg_reads_and_round_trips_the_owners_photos() -> None:
    if not footage_available():
        pytest.skip("no footage folder")
    config = load_local_config()
    photos = photo_check.collect([config.footage_path])
    if not photos:
        pytest.skip("the footage folder has no photos yet (WP3.6P is queued)")
    before = _snapshot(config.footage_path)
    guard = photo_check.make_guard(config)
    run, records = photo_check.run(photos, guard, "pytest-real-photos")
    assert _snapshot(config.footage_path) == before
    assert run.is_relative_to(config.working_path)
    for record in records:
        assert record["verdict"]["ok"] or record["verdict"]["kind"] in ("unsupported", "unreadable")
        if record["verdict"]["ok"]:
            assert record["round_trip"]["problems"] == [], record["file"]
