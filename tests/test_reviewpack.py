"""WP5.3 review-pack contracts, using only planted inputs and committed fixtures.

These tests catch selection drift, unsafe output routing, incorrect source/corrected
pairing, loss of owner answers, misleading tallies and rotated viewing aids. The
single slow test drives the real headless runner and FFmpeg on a tiny selection.
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from fractions import Fraction
from html import unescape
from pathlib import Path

import pytest
from PIL import Image, ImageCms, PngImagePlugin

from local_config import FootageLookupError
from lookcheck.frames import OutputRoots
from lookcheck.frames import run_tool as media_tool
from reviewpack import build, page, select, sheet

FIXTURES = Path(__file__).parent / "fixtures"
HEADER = (
    "item",
    "group",
    "kind",
    "source_name",
    "corrected_name",
    "preferred",
    "halos",
    "banding",
    "color_errors",
    "shimmer",
    "flicker",
    "above_surface",
    "note",
    "viewing_aid_failed",
)
ARTIFACTS = ("halos", "banding", "color_errors", "shimmer", "flicker")
PRESET_SENTENCE = (
    "In v1 both starter presets carry AD-8's defaults, so the corrected items on this page "
    "are what both presets produce; at CP5 the owner may change either preset's values (AD-13)."
)
HEIC_NUMBERS = [
    "6690",
    "6691",
    "6692",
    "6693",
    "6694",
    "6695",
    "6696",
    "6697",
    "6698",
    "6699",
    "6700",
    "6701",
    "6703",
    "6705",
    "6706",
    "6707",
    "6708",
    "6709",
    "6710",
    "6711",
    "6712",
    "6713",
    "6714",
    "6715",
    "6718",
    "6719",
    "6720",
    "6721",
    "6722",
    "6723",
    "6724",
    "6725",
    "6726",
    "6730",
    "6732",
    "6737",
    "6739",
    "6740",
    "6743",
    "6744",
    "6746",
    "6747",
    "6748",
    "6749",
    "6750",
    "6752",
    "6753",
    "6754",
    "6755",
    "6756",
    "6757",
    "6758",
    "6759",
    "6761",
    "6763",
    "6764",
    "6765",
    "6766",
    "6767",
    "6768",
    "6769",
    "6770",
]
PZ_NAMES = {
    "IMG_6791.JPG",
    "IMG_6793.JPG",
    "IMG_6794.JPG",
    "IMG_6795.JPG",
    "IMG_6798.JPG",
    "IMG_6799.JPG",
    "IMG_6800.JPG",
    "IMG_6801.JPG",
    "IMG_6802.JPG",
}
PHONE_VIDEO_NUMBERS = (
    6702,
    6716,
    6717,
    6727,
    6728,
    6729,
    6731,
    6733,
    6734,
    6735,
    6736,
    6738,
    6741,
    6742,
    6745,
    6760,
    6762,
)


def _expected_inventory() -> dict[str, set[str]]:
    """Name expectations come from the inventory, not production selection code."""
    return {
        "P-A": {f"IMG_{n}.HEIC" for n in HEIC_NUMBERS} | {"IMG_6751.JPG", "IMG_6771.JPG"},
        "P-Z": PZ_NAMES,
        "V-S": {f"GX01{n:04d}.mp4" for n in range(1603, 1629)},
        "V-D": {
            "GX011589.mp4",
            "GX011590.mp4",
            "GX011591.mp4",
            "GX011592.mp4",
            "GX011593.mp4",
            "GX011598.mp4",
            "GX011600.mp4",
            "GX011601.mp4",
        },
        "V-P": {f"IMG_{n}.MOV" for n in PHONE_VIDEO_NUMBERS},
        "V-R": {"IMG_6704.MOV", "IMG_6772.MOV"},
        "V-Z": {"dp_color_video_1791675261.mp4", "compilation-20261010-1080p60.mp4"},
    }


@pytest.fixture
def roots(tmp_path: Path) -> OutputRoots:
    """Isolate writes from a planted, read-only-by-contract source folder."""
    source = tmp_path / "source"
    pack = tmp_path / "working" / "wp5.3"
    source.mkdir()
    pack.mkdir(parents=True)
    return OutputRoots(allowed=pack, footage=source)


def _item(
    stem: str = "IMG_6751", group: str = "P-A", kind: str = "photo", status: str = "done"
) -> dict:
    """Plant a pack item with names only, independent of the instrument's writers."""
    suffix = ".JPG" if kind == "photo" else (".MOV" if stem.startswith("IMG_") else ".mp4")
    corrected = f"{stem}_corrected.png" if kind == "photo" else f"{stem}_corrected.mp4"
    return {
        "item": stem,
        "group": group,
        "kind": kind,
        "source_name": stem + suffix,
        "corrected_name": corrected if status == "done" else "",
        "source_view_name": f"{stem}_neutral.png" if kind == "photo" else "",
        "source_thumb": f"{stem}_source.jpg",
        "corrected_thumb": f"{stem}_corrected.jpg",
        "pair_name": f"{stem}_pair.mp4" if kind == "video" else "",
        "stills": [],
        "status": status,
        "message": "Unsupported HLG transfer." if status == "refused" else "",
    }


def _csv(path: Path, rows: list[dict], header: tuple[str, ...] = HEADER) -> None:
    """Write an independent owner-sheet input, not using the writer under test."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)


def _row(subject: dict, **votes: str) -> dict:
    """Build a literal sheet row with empty judgements by default."""
    row = dict.fromkeys(HEADER, "")
    row.update({key: subject[key] for key in HEADER[:5]})
    row.update(votes)
    return row


def _plant_page_item(item: dict, roots: OutputRoots) -> None:
    """Plant linked artifacts without running correction or encoding."""
    if item["status"] != "done":
        return
    for name in (item["source_thumb"], item["corrected_thumb"]):
        path = roots.allowed / "thumbs" / name
        path.parent.mkdir(exist_ok=True)
        Image.new("RGB", (16, 12), "red").save(path)
    folder = "photos" if item["kind"] == "photo" else "clips"
    corrected = roots.allowed / folder / item["corrected_name"]
    corrected.parent.mkdir(exist_ok=True)
    if item["kind"] == "photo":
        Image.new("RGB", (16, 12), "blue").save(corrected)
        Image.new("RGB", (16, 12), "red").save(corrected.parent / item["source_view_name"])
    else:
        corrected.write_bytes(b"planted product link target")
        pairs = roots.allowed / "pairs"
        pairs.mkdir(exist_ok=True)
        (pairs / item["pair_name"]).write_bytes(b"planted viewing-aid link target")


def _presets(roots: OutputRoots) -> dict[str, dict]:
    """Plant AD-13 files with default-inheriting maps and stable timestamps."""
    folder = roots.allowed / "presets"
    folder.mkdir(exist_ok=True)
    result = {}
    for name in ("Snorkel (shallow)", "Scuba (deep)"):
        value = {
            "format_version": 1,
            "method": "c3",
            "parameters": {},
            "created": "2026-01-01T00:00:00+00:00",
            "app_version": "test",
        }
        (folder / f"{name}.json").write_text(json.dumps(value), encoding="utf-8")
        result[name] = value
    return result


def _runner_record(source: str, output: str = "", failure: str | None = None) -> dict:
    """Model the complete schema-1 record, including settings and null video facts."""
    state = "failed" if failure else "done"
    return {
        "schema": 1,
        "tool": "headless_export",
        "app_version": "test",
        "method": "c3",
        "parameters_from": "defaults",
        "settings": {
            "beside_source": False,
            "output_suffix": "_corrected",
            "png_bit_depth": 8,
            "provenance": True,
            "force_cpu": False,
            "video_encoder": "auto",
            "quality_level": "standard",
            "ten_bit_for_eight_bit": False,
            "cache_limit_bytes": 1_000_000,
        },
        "counts": {state: 1},
        "cancelled": False,
        "elapsed_s": 0.1,
        "items": [
            {
                "index": 1,
                "source": source,
                "kind": "photo",
                "state": state,
                "outputs": [output] if output else [],
                "warnings": [],
                "failure": failure,
                "device": "cpu",
                "elapsed_s": 0.1,
                "video": None,
            }
        ],
    }


def test_inventory_names_and_group_membership() -> None:
    """Catch omitted, extra or wrongly grouped commissioned names."""
    items = select.catalog()
    groups = {
        group: {item.name for item in items if item.group == group}
        for group in ("P-A", "P-Z", "V-S", "V-D", "V-P", "V-R", "V-Z")
    }
    assert groups == _expected_inventory()
    assert len(items) == len({item.name.casefold() for item in items}) == 128
    assert Counter(item.group for item in items) == {
        "P-A": 64,
        "P-Z": 9,
        "V-S": 26,
        "V-D": 8,
        "V-P": 17,
        "V-R": 2,
        "V-Z": 2,
    }
    assert sum(item.group in {"P-A", "V-S", "V-D", "V-P"} for item in items) == 115
    assert [item.name for item in items if item.group == "V-P"][-1] == "IMG_6762.MOV"


def test_items_resolve_exact_names_without_scene_classification(roots: OutputRoots) -> None:
    """Catch accidental glob expansion, basename substitution and cross-kind routing."""
    expected = _expected_inventory()
    for group, names in expected.items():
        folder = roots.footage / group
        folder.mkdir()
        for name in names:
            (folder / name).touch()
    (roots.footage / "uncommissioned.JPG").touch()
    resolved = select.items(root=roots.footage)
    assert len(resolved) == 128
    assert {item.name for item in resolved} == set().union(*expected.values())
    assert all(item.path.is_file() and item.path.name == item.name for item in resolved)
    assert all(item.stem == Path(item.name).stem for item in resolved)


def test_photo_resolver_case_insensitive_exact_commissioned_name(roots: OutputRoots) -> None:
    expected = roots.footage / "img_6751.jpg"
    expected.touch()
    (roots.footage / "IMG_6751-preview.JPG").touch()
    (roots.footage / "IMG_6751.mp4").touch()
    assert select.find_photo("IMG_6751.JPG", roots.footage) == expected


def test_photo_resolver_missing_refusal(roots: OutputRoots) -> None:
    with pytest.raises(FootageLookupError, match="not in the footage folder"):
        select.find_photo("IMG_6690.HEIC", roots.footage)


def test_photo_resolver_ambiguous_duplicate_in_two_folders(roots: OutputRoots) -> None:
    for folder in ("first", "second"):
        (roots.footage / folder).mkdir()
        (roots.footage / folder / "IMG_6751.JPG").touch()
    with pytest.raises(FootageLookupError, match="matches 2") as caught:
        select.find_photo("IMG_6751.JPG", roots.footage)
    assert {path.parent.name for path in caught.value.matches} == {"first", "second"}


def test_photo_resolver_prunes_directory_junction_or_link(roots: OutputRoots) -> None:
    """An alias to an external duplicate must neither escape nor cause ambiguity."""
    actual = roots.footage / "IMG_6751.JPG"
    actual.touch()
    elsewhere = roots.allowed / "outside-source"
    elsewhere.mkdir()
    (elsewhere / "IMG_6751.JPG").touch()
    link = roots.footage / "alias"
    if os.name == "nt":  # CHARC R0-1 explicitly requires the Windows junction control.
        done = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(elsewhere)],
            capture_output=True,
            check=False,
            timeout=10,
        )
        assert done.returncode == 0, "could not plant the required junction control"
        assert link.is_junction()
    else:
        link.symlink_to(elsewhere, target_is_directory=True)
        assert link.is_symlink()
    assert select.find_photo("IMG_6751.JPG", roots.footage) == actual


@pytest.mark.parametrize(
    "name", ["other.JPG", "../IMG_6751.JPG", "IMG_6751.png"], ids=["unknown", "path", "suffix"]
)
def test_photo_resolver_refuses_uncommissioned_or_path_name(roots: OutputRoots, name: str) -> None:
    with pytest.raises(ValueError):
        select.find_photo(name, roots.footage)


@pytest.mark.parametrize(
    ("group", "duration", "start", "length", "excerpt"),
    [
        ("V-D", 6.406, 0.0, 6.406, False),
        ("V-D", 42.342, 0.0, 42.342, False),
        ("V-S", 45.0, 0.0, 45.0, False),
        ("V-S", 45.001, 18.0004, 30.0, True),
        ("V-D", 1046.512, 418.6048, 30.0, True),
        ("V-Z", 179.930, 71.972, 30.0, True),
        ("V-P", 749.033333, 0.0, 749.033333, False),
        ("V-R", 44.0, 0.0, 44.0, False),
    ],
)
def test_excerpt_plan_boundaries_and_phone_rule(
    group: str, duration: float, start: float, length: float, excerpt: bool
) -> None:
    plan = select.excerpt_plan(group, duration)
    assert plan.start_s == pytest.approx(start)
    assert plan.duration_s == pytest.approx(length)
    assert plan.excerpt is excerpt


@pytest.mark.parametrize("duration", [0.0, -1.0, float("nan"), float("inf")])
def test_excerpt_plan_rejects_invalid_duration(duration: float) -> None:
    with pytest.raises(ValueError, match="duration"):
        select.excerpt_plan("V-S", duration)


def test_output_guard_refuses_footage_and_parent_escape(roots: OutputRoots) -> None:
    for target in (roots.footage / "bad.png", roots.allowed / ".." / "escaped.png"):
        with pytest.raises(ValueError):
            build.check_target(target, roots)
        assert not target.exists()
    assert (
        build.check_target(roots.allowed / "photos" / "ok.png", roots)
        == (roots.allowed / "photos" / "ok.png").resolve()
    )


def test_cli_refuses_working_folder_inside_footage_before_write(roots: OutputRoots) -> None:
    config = roots.allowed / "unsafe.toml"
    config.write_text(
        f"footage_path = {json.dumps(str(roots.footage))}\n"
        f"working_path = {json.dumps(str(roots.footage / 'bad-work'))}\n",
        encoding="utf-8",
    )
    assert build.main(["presets", "--config", str(config)]) == 2
    assert list(roots.footage.iterdir()) == []


@pytest.mark.parametrize("neutral", [False, True])
def test_photo_runner_arguments_pin_pose_and_preserve_defaults(
    roots: OutputRoots, neutral: bool
) -> None:
    source = roots.footage / "IMG_6751.JPG"
    argv = build.runner_arguments([source], group="P-A", roots=roots, neutral=neutral)
    assert "headless_export.py" in Path(argv[3]).name
    assert str(source) in argv
    assert argv[argv.index("--out") + 1] == str(roots.allowed / "photos")
    assert argv[argv.index("--bit-depth") + 1] == "8"
    assert argv[argv.index("--suffix") + 1] == ("_neutral" if neutral else "_corrected")
    assert ("--neutral" in argv) is neutral
    assert argv[argv.index("--settings-dir") + 1] == str(roots.allowed / "settings")
    assert argv[argv.index("--record") + 1] == str(
        roots.allowed / "records" / ("P-A-neutral.json" if neutral else "P-A.json")
    )
    assert not {
        "--method",
        "--parameters",
        "--no-provenance",
        "--encoder",
        "--quality",
        "--force-cpu",
        "--beside-source",
    }.intersection(argv)


def test_video_runner_arguments_use_checked_cache_and_explicit_cpu_only(
    roots: OutputRoots,
) -> None:
    source = roots.footage / "IMG_6702.MOV"
    argv = build.runner_arguments([source], group="V-P", roots=roots, force_cpu=True)
    assert argv[argv.index("--out") + 1] == str(roots.allowed / "clips")
    assert argv[argv.index("--cache-dir") + 1] == str(roots.allowed / "cache")
    assert "--force-cpu" in argv and "--neutral" not in argv
    assert "--encoder" not in argv and "--ten-bit" not in argv


def test_record_mapping_uses_numbered_product_output_and_retains_failures(
    roots: OutputRoots,
) -> None:
    record = _runner_record("IMG_6751.JPG", "IMG_6751_corrected_2.png")
    failed = _runner_record("IMG_6771.JPG", failure="IMG_6771.JPG cannot be read.")["items"][0]
    failed["index"] = 2
    record["items"].append(failed)
    record["counts"] = {"done": 1, "failed": 1}
    path = roots.allowed / "P-A.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    (roots.allowed / "photos").mkdir()
    Image.new("RGB", (8, 8)).save(roots.allowed / "photos" / "IMG_6751_corrected_2.png")
    mapped = build.read_runner_record(path, group="P-A", roots=roots)
    assert len(mapped) == 2
    assert mapped[0]["corrected_name"] == "IMG_6751_corrected_2.png"
    assert mapped[0]["status"] == "done"
    assert mapped[1]["status"] == "failed"
    assert mapped[1]["message"] == "IMG_6771.JPG cannot be read."


def test_stream_copy_arguments_preserve_all_streams_and_seek_before_input(
    roots: OutputRoots,
) -> None:
    source = roots.footage / "GX011625.mp4"
    dest = roots.allowed / "excerpts" / source.name
    argv = build.stream_copy_command(source, dest, start_s=199.3724, duration_s=30.0)
    assert argv.index("-ss") < argv.index("-i")
    assert float(argv[argv.index("-ss") + 1]) == pytest.approx(199.3724)
    assert argv[argv.index("-map") + 1] == "0"
    assert argv[argv.index("-c") + 1] == "copy"
    assert float(argv[argv.index("-t") + 1]) == 30.0
    assert argv[-1] == str(dest)


@pytest.mark.parametrize("mutation", ["stream-count", "codec-tag"])
def test_stream_copy_integrity_refuses_lost_stream_or_changed_tag(mutation: str) -> None:
    before = [
        {"codec_type": "video", "codec_name": "hevc", "codec_tag_string": "hvc1"},
        {"codec_type": "data", "codec_name": "bin_data", "codec_tag_string": "gpmd"},
    ]
    after = [dict(s) for s in before]
    if mutation == "stream-count":
        after.pop()
    else:
        after[1]["codec_tag_string"] = "mebx"
    with pytest.raises(ValueError, match=r"stream|codec"):
        build.validate_stream_copy(before, after)
    build.validate_stream_copy(before, [dict(s) for s in before])


def test_actual_excerpt_start_uses_source_packet_not_rebased_zero() -> None:
    source_packets = [
        {"codec_type": "video", "pts_time": "18.4", "data_hash": "SHA256:earlier"},
        {"codec_type": "video", "pts_time": "19.2", "data_hash": "SHA256:first-kept"},
    ]
    excerpt_packets = [
        {"codec_type": "video", "pts_time": "0.0", "data_hash": "SHA256:first-kept"},
    ]
    assert build.actual_excerpt_start(source_packets, excerpt_packets) == pytest.approx(19.2)


@pytest.mark.usefixtures("ffmpeg_tools")
def test_failed_stream_copy_never_falls_back_to_whole_source(
    roots: OutputRoots, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CHARC's A1 ruling supersedes the former whole-source fallback contract."""
    source = roots.footage / "GX011625.mp4"
    shutil.copyfile(FIXTURES / "video" / "hevc8-bt709-full.mp4", source)
    original = source.read_bytes()

    def failed_copy(argv, **kwargs):
        if Path(argv[0]).stem == "ffprobe":
            return media_tool(argv, **kwargs)
        assert "-c" in argv and argv[argv.index("-c") + 1] == "copy"
        return subprocess.CompletedProcess(argv, 1, b"", b"stream copy refused")

    monkeypatch.setattr(build, "run_tool", failed_copy)
    prepared = build.prepare_excerpt(source, start_s=0.6, duration_s=30.0, roots=roots)
    assert prepared["path"] is None
    assert prepared["excerpt"] is False
    assert prepared["status"] == "excerpt_failed"
    assert prepared["message"] == "stream copy refused"
    assert source.read_bytes() == original


@pytest.mark.usefixtures("ffmpeg_tools")
def test_rotation_adapter_extracts_oriented_fixture_dimensions(
    roots: OutputRoots, monkeypatch: pytest.MonkeyPatch
) -> None:
    commands = []

    def observed_tool(argv, **kwargs):
        commands.append(list(argv))
        return media_tool(argv, **kwargs)

    monkeypatch.setattr(build, "run_tool", observed_tool)
    target = roots.allowed / "rotated-view.png"
    frame = build.extract_view_frame(FIXTURES / "video" / "rotated.mp4", 0.0, target, roots=roots)
    with Image.open(frame) as image:
        assert image.size == (180, 320)  # Fixture is coded 320x180 with rotation 90.
    assert commands
    assert all(
        "-noautorotate" not in argv and "transpose" not in " ".join(argv) for argv in commands
    )


@pytest.mark.usefixtures("ffmpeg_tools")
def test_rotated_pair_autorotates_both_halves_with_equal_dimensions(
    roots: OutputRoots,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Real FFmpeg rendering proves both 90-degree inputs use their display pose."""
    source = FIXTURES / "video" / "rotated.mp4"
    dest = roots.allowed / "pairs" / "rotated_pair.mp4"
    commands = []

    def observed_tool(argv, **kwargs):
        commands.append(list(argv))
        return media_tool(argv, **kwargs)

    monkeypatch.setattr(build, "run_tool", observed_tool)
    result = build.make_pair(source, source, dest, roots=roots, force_cpu=True)
    assert result["source_size"] == result["corrected_size"] == (180, 320)
    assert result["pair_size"] == (182, 160)  # 90px halves plus the 2px separator.
    assert dest.is_file()
    done = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "json",
            str(dest),
        ],
        capture_output=True,
        check=True,
        timeout=30,
    )
    stream = json.loads(done.stdout)["streams"][0]
    assert (stream["width"], stream["height"]) == (182, 160)
    hstack = next(argv for argv in commands if "hstack" in " ".join(argv))
    assert hstack.count(str(source)) == 2
    assert "-noautorotate" not in hstack and "transpose" not in " ".join(hstack)


@pytest.mark.usefixtures("ffmpeg_tools")
def test_pair_refuses_unequal_display_dimensions_before_hstack(
    roots: OutputRoots, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An invalid pair must be rejected before any encoding subprocess is started."""
    calls = []

    def forbidden_render(argv, **kwargs):
        if any("hstack" in argument for argument in argv):
            calls.append(argv)
            pytest.fail("hstack subprocess ran before equal-display-size validation")
        return media_tool(argv, **kwargs)

    monkeypatch.setattr(build, "run_tool", forbidden_render)
    with pytest.raises(ValueError, match=r"dimension|size"):
        build.make_pair(
            FIXTURES / "video" / "rotated.mp4",
            FIXTURES / "video" / "hevc8-bt709-full.mp4",
            roots.allowed / "pairs" / "invalid.mp4",
            roots=roots,
            force_cpu=True,
        )
    assert calls == []
    assert not (roots.allowed / "pairs" / "invalid.mp4").exists()


def test_sheet_header_rows_exclude_failed_refused_and_not_built(roots: OutputRoots) -> None:
    items = [
        _item(),
        _item("IMG_6791", "P-Z"),
        _item("IMG_6702", "V-P", "video"),
        _item("IMG_6704", "V-R", "video", "refused"),
        _item("IMG_6771", "P-A", "photo", "failed"),
        _item("GX011604", "V-S", "video", "pending"),
    ]
    dest = roots.allowed / "review-sheet.csv"
    sheet.write_sheet(items, dest, roots=roots)
    with dest.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert tuple(reader.fieldnames) == HEADER
        rows = list(reader)
    assert [(r["item"], r["group"]) for r in rows] == [
        ("IMG_6751", "P-A"),
        ("IMG_6791", "P-Z"),
        ("IMG_6702", "V-P"),
    ]
    assert all(r["preferred"] == "" and all(r[k] == "" for k in ARTIFACTS) for r in rows)
    assert not any(str(roots.footage) in value for row in rows for value in row.values())


def test_sheet_preserves_answers_when_later_groups_arrive(roots: OutputRoots) -> None:
    dest = roots.allowed / "review-sheet.csv"
    first = _item()
    _csv(dest, [_row(first, preferred="yes", note="owner's answer, retained")])
    sheet.write_sheet([first, _item("IMG_6702", "V-P", "video")], dest, roots=roots)
    with dest.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2 and rows[0]["preferred"] == "yes"
    assert rows[0]["note"] == "owner's answer, retained"
    assert rows[1]["preferred"] == ""


def test_sheet_refuses_to_transfer_vote_to_regenerated_output(roots: OutputRoots) -> None:
    dest = roots.allowed / "review-sheet.csv"
    _csv(dest, [_row(_item(), preferred="yes")])
    before = dest.read_bytes()
    changed = _item()
    changed["corrected_name"] = "IMG_6751_corrected_2.png"
    with pytest.raises(ValueError, match=r"changed|identity|pair"):
        sheet.write_sheet([changed], dest, roots=roots)
    assert dest.read_bytes() == before


@pytest.mark.parametrize(
    "column",
    [
        "preferred",
        "halos",
        "banding",
        "color_errors",
        "shimmer",
        "flicker",
        "above_surface",
        "note",
        "viewing_aid_failed",
    ],
)
def test_any_owner_cell_protects_pair_but_aid_flag_is_not_an_answer(
    roots: OutputRoots, column: str
) -> None:
    """Artifact-only or note-only answers protect identity just like preference votes."""
    destination = roots.allowed / "review-sheet.csv"
    first = _item()
    _csv(destination, [_row(first, **{column: "yes"})])
    before = destination.read_bytes()
    changed = {**first, "corrected_name": "IMG_6751_corrected_2.png"}
    if column == "viewing_aid_failed":
        changed["viewing_aid_failed"] = True
        sheet.write_sheet([changed, _item("IMG_6771")], destination, roots=roots)
        with destination.open(newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert rows[0]["corrected_name"] == "IMG_6751_corrected_2.png"
        assert rows[0]["viewing_aid_failed"] == "yes"
    else:
        with pytest.raises(sheet.SheetConflictError) as conflict:
            sheet.write_sheet([changed, _item("IMG_6771")], destination, roots=roots)
        assert conflict.value.items == ("IMG_6751",)
        assert before in destination.read_bytes()
    assert sheet.tally(destination)["headline"]["available"] == 2


def test_tally_empty_sheet_is_zero_judged_without_verdict(roots: OutputRoots) -> None:
    path = roots.allowed / "empty.csv"
    _csv(path, [_row(_item())])
    result = sheet.tally(path)
    assert result["headline"]["judged"] == result["headline"]["preferred"] == 0
    text = sheet.format_tally(result)
    assert "headline: 0/0 = 0.0 %  (D65 bar 80 %)" in text
    # The required viewing_aid_failed field is a status flag, never a quality verdict.
    assert not re.search(r"\b(?:pass|fail|approved|rejected)\b", text.lower())


def test_tally_filled_headline_candidates_artifacts_and_above_surface(
    roots: OutputRoots,
) -> None:
    path = roots.allowed / "filled.csv"
    _csv(
        path,
        [
            _row(
                _item(),
                preferred="yes",
                halos="yes",
                above_surface="yes",
                note="Unicode: caf\u00e9",
            ),
            _row(_item("IMG_6771"), preferred="no", banding="yes"),
            _row(_item("IMG_6702", "V-P", "video"), preferred="undecided", shimmer="yes"),
            _row(_item("IMG_6716", "V-P", "video"), color_errors="yes", flicker="yes"),
            _row(_item("IMG_6791", "P-Z"), preferred="yes"),
            _row(_item("compilation-20261010-1080p60", "V-Z", "video"), preferred="yes"),
        ],
    )
    result = sheet.tally(path)
    assert result["headline"]["judged"] == 3
    assert result["headline"]["preferred"] == 1
    assert result["headline"]["above_surface"] == 1
    assert result["headline"]["artifacts"] == dict.fromkeys(ARTIFACTS, 1)
    assert result["groups"]["P-A"]["judged"] == 2
    assert result["groups"]["V-P"]["judged"] == 1
    assert result["candidates"]["judged"] == result["candidates"]["preferred"] == 2
    assert "headline: 1/3 = 33.3 %  (D65 bar 80 %)" in sheet.format_tally(result)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("preferred", "maybe"),
        ("halos", "no"),
        ("above_surface", "false"),
        ("group", "not-a-group"),
        ("item", "../secret"),
    ],
)
def test_tally_invalid_value_names_row(roots: OutputRoots, field: str, value: str) -> None:
    path = roots.allowed / "invalid.csv"
    _csv(path, [_row(_item(), **{field: value})])
    with pytest.raises(ValueError, match="row 2"):
        sheet.tally(path)


@pytest.mark.parametrize("fault", ["header", "duplicate", "extra-cell", "missing-cell"])
def test_tally_refuses_malformed_sheet(roots: OutputRoots, fault: str) -> None:
    path = roots.allowed / "bad-shape.csv"
    if fault == "header":
        _csv(path, [], header=tuple(key for key in HEADER if key != "preferred"))
    elif fault == "duplicate":
        _csv(path, [_row(_item()), _row(_item())])
    else:
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer)
        writer.writerow(HEADER)
        cells = [_row(_item())[key] for key in HEADER]
        writer.writerow([*cells, "extra"] if fault == "extra-cell" else cells[:-1])
        path.write_text(buffer.getvalue(), encoding="utf-8")
    with pytest.raises(ValueError, match=r"header|row"):
        sheet.tally(path)


def test_tally_cli_valid_scores_exit_zero_and_invalid_sheet_exit_two(
    roots: OutputRoots, capsys: pytest.CaptureFixture[str]
) -> None:
    path = roots.allowed / "owner.csv"
    _csv(path, [_row(_item(), preferred="no", halos="yes")])
    assert build.main(["tally", str(path)]) == 0
    assert "headline: 0/1 = 0.0 %  (D65 bar 80 %)" in capsys.readouterr().out
    _csv(path, [_row(_item(), preferred="maybe")])
    assert build.main(["tally", str(path)]) == 2
    assert "row 2" in "".join(capsys.readouterr())


def test_page_planted_groups_labels_presets_and_name_only_links(roots: OutputRoots) -> None:
    items = [
        _item(),
        _item("IMG_6791", "P-Z"),
        _item("IMG_6702", "V-P", "video"),
        _item("IMG_6704", "V-R", "video", "refused"),
    ]
    for item in items:
        _plant_page_item(item, roots)
    path = page.write_page(items, _presets(roots), roots=roots)
    html = path.read_text(encoding="utf-8")
    assert PRESET_SENTENCE in html
    assert "neutral" in html.lower() and "source" in html.lower() and "corrected" in html.lower()
    assert "viewing aid" in html.lower()
    assert "Unsupported HLG transfer." in html
    assert "IMG_6791" in html and "P-Z" in html and "V-R" in html
    assert all(word in html.lower() for word in ("halos", "banding", "color", "shimmer", "flicker"))
    assert "white_balance" in html and "3.0" in html and "0.0" in html
    assert str(roots.footage) not in html and str(roots.allowed) not in html
    assert page.check_links(path, roots=roots) == []


def test_page_escapes_refusal_text_instead_of_rendering_markup(roots: OutputRoots) -> None:
    item = _item("IMG_6704", "V-R", "video", "refused")
    item["message"] = '<script>alert("not HTML")</script>'
    path = page.write_page([item], _presets(roots), roots=roots)
    html = path.read_text(encoding="utf-8")
    assert "<script>" not in html and "&lt;script&gt;" in html


@pytest.mark.parametrize(
    "target",
    ["missing.png", "../outside.png", "https://example.test/x"],
    ids=["missing", "escape", "nonlocal"],
)
def test_page_check_detects_missing_escaping_and_nonlocal_links(
    roots: OutputRoots, target: str
) -> None:
    outside = roots.allowed.parent / "outside.png"
    outside.touch()
    path = roots.allowed / "index.html"
    path.write_text(f'<a href="{target}">item</a><img src="{target}">', encoding="utf-8")
    errors = page.check_links(path, roots=roots)
    assert errors and target in " ".join(errors)
    assert page.main(["--check", "--root", str(roots.allowed)]) == 2


def test_thumbnail_converts_embedded_p3_to_srgb_and_strips_other_metadata(
    roots: OutputRoots,
) -> None:
    source = FIXTURES / "stills" / "png" / "png8-gradient-display-p3.png"
    dest = roots.allowed / "thumbs" / "p3.jpg"
    with Image.open(source) as original:
        expected = ImageCms.profileToProfile(
            original.convert("RGB"),
            ImageCms.ImageCmsProfile(io.BytesIO(original.info["icc_profile"])),
            ImageCms.createProfile("sRGB"),
            outputMode="RGB",
        )
        expected = expected.resize((round(expected.width * 540 / expected.height), 540))
    assert page.thumbnail(source, dest, roots=roots) == dest
    with Image.open(dest) as thumb:
        assert min(thumb.size) == 540
        assert (
            "srgb"
            in ImageCms.getProfileDescription(
                ImageCms.ImageCmsProfile(io.BytesIO(thumb.info["icc_profile"]))
            ).lower()
        )
        for location in ((270, 270), (400, 200)):
            assert (
                max(
                    abs(a - b)
                    for a, b in zip(
                        thumb.getpixel(location), expected.getpixel(location), strict=True
                    )
                )
                <= 5
            )
        assert not thumb.getexif()


def test_thumbnail_without_icc_keeps_rgb_and_drops_text(roots: OutputRoots) -> None:
    source = roots.footage / "unprofiled.png"
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("private-test-tag", "must not be copied")
    Image.new("RGB", (80, 60), (60, 100, 140)).save(source, pnginfo=metadata)
    dest = roots.allowed / "thumbs" / "unprofiled.jpg"
    page.thumbnail(source, dest, roots=roots)
    with Image.open(dest) as thumb:
        assert thumb.size == (720, 540)
        assert "icc_profile" not in thumb.info and "private-test-tag" not in thumb.info
        assert (
            max(abs(a - b) for a, b in zip(thumb.getpixel((360, 270)), (60, 100, 140), strict=True))
            <= 2
        )


def test_pair_still_uses_source_left_corrected_right_and_separator(roots: OutputRoots) -> None:
    source = roots.allowed / "source.png"
    corrected = roots.allowed / "corrected.png"
    Image.new("RGB", (80, 60), "red").save(source)
    Image.new("RGB", (80, 60), "blue").save(corrected)
    dest = roots.allowed / "pairs" / "still.jpg"
    page.pair_still(source, corrected, dest, roots=roots)
    with Image.open(dest) as pair:
        assert pair.size == (2882, 1080)
        assert pair.getpixel((400, 400))[0] >= 245
        assert pair.getpixel((2400, 400))[2] >= 245
        assert min(pair.getpixel((1440, 400))) >= 230


def test_presets_export_product_starters_without_expanding_serialized_maps(
    roots: OutputRoots,
) -> None:
    exported = build.export_presets(roots=roots)
    assert set(exported) == {"Snorkel (shallow)", "Scuba (deep)"}
    for name, value in exported.items():
        actual = json.loads((roots.allowed / "presets" / f"{name}.json").read_text())
        assert actual == value
        assert actual["format_version"] == 1 and actual["method"] == "c3"
        assert actual["parameters"] == {}
        assert set(actual) == {"format_version", "method", "parameters", "created", "app_version"}
    assert list(roots.footage.iterdir()) == []


TINY_PHOTOS = [
    (FIXTURES / "stills" / "jpeg" / "jpeg-gradient-srgb.jpg", "IMG_6751.JPG", "P-A"),
    (FIXTURES / "stills" / "jpeg" / "jpeg-lowred-srgb.jpg", "IMG_6791.JPG", "P-Z"),
]
TINY_VIDEO = (FIXTURES / "video" / "hevc8-bt709-full.mp4", "GX011604.mp4", "V-S")


def _run_tiny_set(roots: OutputRoots, inputs: list[tuple[Path, str, str]]) -> dict[str, bytes]:
    """Plant ``inputs``, run ``build.main all`` over them on the CPU and check its links.

    Returns:
        Each planted source's bytes before the run, by name.
    """
    before = {}
    for source, name, _ in inputs:
        shutil.copyfile(source, roots.footage / name)
        before[name] = (roots.footage / name).read_bytes()
    config = roots.allowed.parent / "tiny.toml"
    config.write_text(
        f"footage_path = {json.dumps(str(roots.footage))}\n"
        f"working_path = {json.dumps(str(roots.allowed.parent))}\n",
        encoding="utf-8",
    )
    manifest = roots.allowed / "tiny-selection.json"
    manifest.write_text(
        json.dumps(
            [
                {"name": name, "group": group, "kind": "video" if group == "V-S" else "photo"}
                for _, name, group in inputs
            ]
        ),
        encoding="utf-8",
    )
    assert (
        build.main(
            [
                "all",
                "--config",
                str(config),
                "--manifest",
                str(manifest),
                "--force-cpu",
            ]
        )
        == 2  # R3-5: a tiny fixture leaves the other commissioned items pending.
    )
    assert page.check_links(roots.allowed / "index.html", roots=roots) == []
    return before


@pytest.mark.slow(reason="runs the headless runner")
def test_all_tiny_set_photos(roots: OutputRoots) -> None:
    """The photo half needs no FFmpeg, so it runs on a runner without it (WP6.5 A r11 #2)."""
    before = _run_tiny_set(roots, TINY_PHOTOS)
    for stem in ("IMG_6751", "IMG_6791"):
        assert (roots.allowed / "photos" / f"{stem}_corrected.png").is_file()
        assert (roots.allowed / "photos" / f"{stem}_neutral.png").is_file()
    for group in ("P-A", "P-Z"):
        record = json.loads((roots.allowed / "records" / f"{group}.json").read_text())
        assert record["settings"]["force_cpu"] is True
        assert record["parameters_from"] == "defaults"
        assert record["items"][0]["state"] in {"done", "done with warnings"}
    state = json.loads((roots.allowed / "records" / "pack.json").read_text())
    assert len(state["items"]) == 128
    # R3-5: the two photos leave 126 commissioned items pending.
    assert sum(item["status"] == "pending" for item in state["items"]) == 126
    with (roots.allowed / "review-sheet.csv").open(encoding="utf-8", newline="") as handle:
        assert len(list(csv.DictReader(handle))) == 2
    assert before == {name: (roots.footage / name).read_bytes() for _, name, _ in TINY_PHOTOS}


@pytest.mark.slow(reason="runs the headless runner and FFmpeg")
@pytest.mark.usefixtures("ffmpeg_tools")  # the clip needs FFmpeg; the photos run above too
def test_all_tiny_set(roots: OutputRoots) -> None:
    """Exercise all stages end to end while recording source byte immutability."""
    inputs = [*TINY_PHOTOS, TINY_VIDEO]
    before = _run_tiny_set(roots, inputs)
    for stem in ("IMG_6751", "IMG_6791"):
        assert (roots.allowed / "photos" / f"{stem}_corrected.png").is_file()
        assert (roots.allowed / "photos" / f"{stem}_neutral.png").is_file()
    assert (roots.allowed / "clips" / "GX011604_corrected.mp4").is_file()
    assert (roots.allowed / "pairs" / "GX011604_pair.mp4").is_file()
    assert len(list((roots.allowed / "pairs").glob("GX011604_*.jpg"))) == 3
    for group in ("P-A", "P-Z", "V-S"):
        record = json.loads((roots.allowed / "records" / f"{group}.json").read_text())
        assert record["settings"]["force_cpu"] is True
        assert record["parameters_from"] == "defaults"
        assert record["items"][0]["state"] in {"done", "done with warnings"}
    state = json.loads((roots.allowed / "records" / "pack.json").read_text())
    assert len(state["items"]) == 128
    # R3-5: the three-item fixture leaves 125 commissioned items pending.
    assert sum(item["status"] == "pending" for item in state["items"]) == 125
    video = next(item for item in state["items"] if item["item"] == "GX011604")
    assert [still["fraction"] for still in video["stills"]] == [0.1, 0.5, 0.9]
    assert all(still["source_pts_s"] == still["corrected_pts_s"] for still in video["stills"])
    tally = sheet.tally(roots.allowed / "review-sheet.csv")
    assert tally["headline"]["judged"] == tally["candidates"]["judged"] == 0
    with (roots.allowed / "review-sheet.csv").open(encoding="utf-8", newline="") as handle:
        assert len(list(csv.DictReader(handle))) == 3
    assert before == {name: (roots.footage / name).read_bytes() for _, name, _ in inputs}
    # F2: this non-keyframe copy must be accepted by the unmodified product.
    prepared = build.prepare_excerpt(
        roots.footage / "GX011604.mp4", start_s=0.6, duration_s=0.5, roots=roots
    )
    arguments = build.runner_arguments([prepared["path"]], group="V-S", roots=roots, force_cpu=True)
    arguments += ["--encoder", "libx265"]
    done = media_tool(arguments)
    assert done.returncode == 0, done.stderr.decode("utf-8", "replace")


@pytest.mark.parametrize("module", ["build", "page"])
def test_direct_cli_help_runs_without_pythonpath(module: str) -> None:
    """The dispatcher's CLI must be runnable from the worktree root."""
    environment = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    done = subprocess.run(
        [sys.executable, f"tools/reviewpack/{module}.py", "--help"],
        env=environment,
        capture_output=True,
        check=False,
        timeout=10,
    )
    assert done.returncode == 0, done.stderr.decode("utf-8", "replace")
    assert "usage:" in done.stdout.decode("utf-8", "replace")


def test_sheet_refuses_stale_row_after_item_becomes_unreviewable(roots: OutputRoots) -> None:
    """A failed rerun must not leave a vote linked to an absent page pair."""
    destination = roots.allowed / "review-sheet.csv"
    _csv(destination, [_row(_item(), preferred="yes")])
    before = destination.read_bytes()
    with pytest.raises(ValueError, match=r"changed|identity|pair|reviewable"):
        sheet.write_sheet([_item(status="failed")], destination, roots=roots)
    assert destination.read_bytes() == before


@pytest.mark.usefixtures("ffmpeg_tools")
def test_viewing_pts_uses_ticks_instead_of_rounded_decimal() -> None:
    """Decimal ffprobe time strings can round across a frame-selection boundary."""
    source = FIXTURES / "video" / "vfr.mp4"
    done = media_tool(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_frames",
            "-show_streams",
            "-show_entries",
            "stream=time_base:frame=best_effort_timestamp",
            "-of",
            "json",
            str(source),
        ]
    )
    assert done.returncode == 0
    value = json.loads(done.stdout)
    time_base = Fraction(value["streams"][0]["time_base"])
    pts = [int(frame["best_effort_timestamp"]) * time_base for frame in value["frames"]]
    # Select a frame whose exact rational timestamp has a repeating decimal.
    expected = next(p for p in pts if p > 0 and Fraction(f"{float(p):.6f}") != p)
    assert build._frame_time(source, float(expected) - 0.0001) == expected


@pytest.mark.usefixtures("ffmpeg_tools")
def test_stream_copy_success_records_a_matched_source_packet(roots: OutputRoots) -> None:
    """Check the real copy/probe join rather than only a planted packet mapping."""
    source = FIXTURES / "video" / "hevc8-bt709-full.mp4"
    prepared = build.prepare_excerpt(source, start_s=0.6, duration_s=1.0, roots=roots)
    assert prepared["excerpt"] is True
    assert prepared["planned_start_s"] == 0.6
    assert 0.0 <= prepared["actual_start_s"] <= 0.6
    assert prepared["duration_s"] > 0
    assert prepared["path"].is_relative_to(roots.allowed / "excerpts")


@pytest.mark.usefixtures("ffmpeg_tools")
def test_rotated_frame_at_nonzero_pts(roots: OutputRoots) -> None:
    """Showinfo's exact ticks must confirm a nonzero oriented extraction."""
    frame = build.extract_view_frame(
        FIXTURES / "video" / "rotated.mp4",
        0.6,
        roots.allowed / "later.png",
        roots=roots,
    )
    with Image.open(frame) as image:
        assert image.size == (180, 320)


@pytest.mark.usefixtures("ffmpeg_tools")
def test_refused_fixture_is_recorded_without_a_review_row(roots: OutputRoots) -> None:
    """A real HLG refusal must reach the page and stay outside the owner tally."""
    shutil.copyfile(FIXTURES / "video" / "hlg.mp4", roots.footage / "IMG_6704.MOV")
    config = roots.allowed / "refused.toml"
    config.write_text(
        f"footage_path = {json.dumps(str(roots.footage))}\n"
        f"working_path = {json.dumps(str(roots.allowed.parent))}\n",
        encoding="utf-8",
    )
    manifest = roots.allowed / "refused.json"
    manifest.write_text(json.dumps([{"name": "IMG_6704.MOV", "group": "V-R", "kind": "video"}]))
    args = ["--config", str(config), "--manifest", str(manifest), "--force-cpu"]
    assert build.main(["clips", "V-R", *args]) == 0
    assert build.main(["page", *args]) == 2
    state = json.loads((roots.allowed / "records" / "pack.json").read_text())
    assert len(state["items"]) == 128
    results = [item for item in state["items"] if item["status"] != "pending"]
    assert len(results) == 1 and results[0]["item"] == "IMG_6704"
    assert results[0]["status"] == "refused"
    assert "hlg" in results[0]["message"].lower()
    assert "HLG" in (roots.allowed / "index.html").read_text()
    with (roots.allowed / "review-sheet.csv").open(encoding="utf-8", newline="") as handle:
        assert list(csv.DictReader(handle)) == []


def test_tally_refuses_unrelated_corrected_filename(roots: OutputRoots) -> None:
    """A syntactically safe name must still belong to the named item's export."""
    path = roots.allowed / "wrong-pair.csv"
    _csv(path, [_row(_item(), corrected_name="IMG_6771_corrected.png")])
    with pytest.raises(ValueError, match="row 2"):
        sheet.tally(path)


def test_non_hlg_failure_in_refused_group_is_not_mislabelled(roots: OutputRoots) -> None:
    """Group membership cannot turn an unrelated export error into an HLG refusal."""
    path = roots.allowed / "V-R.json"
    path.write_text(json.dumps(_runner_record("IMG_6704.MOV", failure="Cannot read input.")))
    result = build.read_runner_record(path, group="V-R", roots=roots)
    assert result[0]["status"] == "failed"
    assert result[0]["message"] == "Cannot read input."


def test_sheet_write_failure_preserves_original_answers(
    roots: OutputRoots,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed write of the replacement CSV must preserve the existing owner's file."""
    destination = roots.allowed / "review-sheet.csv"
    _csv(destination, [_row(_item(), preferred="yes")])
    before = destination.read_bytes()
    original = OutputRoots.write_bytes

    def interrupted(self, target, data):
        original(self, target, b"partial")
        raise OSError("planted write interruption")

    monkeypatch.setattr(OutputRoots, "write_bytes", interrupted)
    with pytest.raises(OSError, match="planted"):
        sheet.write_sheet([_item(), _item("IMG_6791", "P-Z")], destination, roots=roots)
    assert destination.read_bytes() == before


def _facts(path: Path) -> dict:
    """Probe independent stream identities and packet payloads for excerpt controls."""
    done = media_tool(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-show_packets",
            "-show_data_hash",
            "sha256",
            "-of",
            "json",
            str(path),
        ]
    )
    assert done.returncode == 0, done.stderr.decode()
    return json.loads(done.stdout)


def _timecode_source(roots: OutputRoots) -> Path:
    """Plant video/audio/tmcd plus an opaque synthetic gpmd payload, without decoding."""
    base = roots.allowed / "tc-template.mp4"
    video_only = roots.allowed / "video-only.mp4"
    done = media_tool(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-i",
            str(FIXTURES / "video" / "hevc8-bt709-full.mp4"),
            "-map",
            "0:v:0",
            "-c",
            "copy",
            str(video_only),
        ]
    )
    assert done.returncode == 0, done.stderr.decode()
    done = media_tool(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-stream_loop",
            "2",
            "-i",
            str(video_only),
            "-stream_loop",
            "2",
            "-i",
            str(FIXTURES / "video" / "hevc8-bt709-full.mp4"),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c",
            "copy",
            "-timecode",
            "01:00:00:00",
            str(base),
        ]
    )
    assert done.returncode == 0, done.stderr.decode()
    opaque = roots.allowed / "opaque-gpmd.mp4"
    # This is an arbitrary four-byte data payload, not a real telemetry claim.
    opaque.write_bytes(base.read_bytes().replace(b"tmcd", b"gpmd"))
    source = roots.allowed / "tmcd-gpmd.mp4"
    done = media_tool(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-i",
            str(base),
            "-i",
            str(opaque),
            "-map",
            "0:v",
            "-map",
            "0:a",
            "-map",
            "1:d",
            "-c",
            "copy",
            "-map_metadata",
            "0",
            "-write_tmcd",
            "1",
            str(source),
        ]
    )
    assert done.returncode == 0, done.stderr.decode()
    return source


@pytest.mark.parametrize(
    ("start", "actual", "timecode"),
    [
        (0.6, 0.0, "01:00:00:00"),
        (2.1, 1.5015, "01:00:01:15"),
    ],
)
@pytest.mark.usefixtures("ffmpeg_tools")
def test_gopro_tmcd_excerpt_preserves_stream_roster_without_whole_fallback(
    roots: OutputRoots,
    start: float,
    actual: float,
    timecode: str,
) -> None:
    """Catch lost data packets, mux-order assumptions and unadvanced timecode."""
    source = _timecode_source(roots)
    original = source.read_bytes()
    before = _facts(source)
    prepared = build.prepare_excerpt(source, start_s=start, duration_s=0.5, roots=roots)
    assert prepared["excerpt"] is True
    assert prepared["path"] != source
    assert prepared["actual_start_s"] == pytest.approx(actual)
    after = _facts(prepared["path"])

    def key(s):
        return (s["codec_type"], s["codec_tag_string"])

    assert Counter(map(key, before["streams"])) == Counter(map(key, after["streams"]))
    for stream in after["streams"]:
        match = next(s for s in before["streams"] if key(s) == key(stream))
        if stream["codec_tag_string"] == "tmcd":
            assert stream["tags"]["timecode"] == timecode
            continue
        kept = [p["data_hash"] for p in after["packets"] if p["stream_index"] == stream["index"]]
        source_hashes = [
            p["data_hash"] for p in before["packets"] if p["stream_index"] == match["index"]
        ]
        assert kept, stream
        assert all(h in source_hashes for h in kept)
    assert source.read_bytes() == original


@pytest.mark.usefixtures("ffmpeg_tools")
def test_excerpt_copy_failure_is_recorded_skipped_and_exits_nonzero(
    roots: OutputRoots,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Catch silent fallback, accidental runner submission and missing not-built rows."""
    source = roots.footage / "GX011604.mp4"
    shutil.copyfile(FIXTURES / "video" / "hevc8-bt709-full.mp4", source)
    shutil.copyfile(FIXTURES / "video" / "hlg.mp4", roots.footage / "IMG_6704.MOV")
    config = roots.allowed / "failure.toml"
    config.write_text(
        f"footage_path = {json.dumps(str(roots.footage))}\n"
        f"working_path = {json.dumps(str(roots.allowed.parent))}\n",
        encoding="utf-8",
    )
    manifest = roots.allowed / "failure.json"
    manifest.write_text(
        json.dumps(
            [
                {"name": source.name, "group": "V-S", "kind": "video"},
                {"name": "IMG_6704.MOV", "group": "V-R", "kind": "video"},
            ]
        )
    )
    monkeypatch.setattr(select, "excerpt_plan", lambda *a: select.ExcerptPlan(0.6, 0.5, True))

    def fail_copy(argv, **kwargs):
        if Path(argv[0]).stem == "ffprobe":
            return media_tool(argv, **kwargs)
        if argv[0] == "uv":
            assert not any("GX011604" in arg for arg in argv), "failed item reached the runner"
            return media_tool(argv, **kwargs)
        assert argv[0] == "ffmpeg" and "copy" in argv, "failed item reached a clip piece"
        return subprocess.CompletedProcess(argv, 1, b"", b"detail\nplanted mux failure\n")

    monkeypatch.setattr(build, "run_tool", fail_copy)
    args = ["--config", str(config), "--manifest", str(manifest)]
    assert build.main(["clips", *args]) != 0
    state = json.loads((roots.allowed / "records" / "pack.json").read_text())
    results = {item["item"]: item for item in state["items"]}
    assert len(results) == 128
    assert results["GX011604"]["status"] == "excerpt_failed"
    assert results["GX011604"]["message"] == "planted mux failure"
    assert results["IMG_6704"]["status"] == "refused"  # A later group still runs.
    group = json.loads((roots.allowed / "records" / "V-S-excerpts.json").read_text())
    assert group["items"][0]["status"] == "excerpt_failed"
    assert not list((roots.allowed / "clips").glob("*.mp4"))
    assert build.main(["page", *args]) == 2  # R3-5: pending takes precedence.
    html = (roots.allowed / "index.html").read_text()
    assert "Not built" in html and source.name in html and "planted mux failure" in html
    assert list(csv.DictReader((roots.allowed / "review-sheet.csv").open())) == []


def test_stream_copy_command_rebases_preroll_for_product(roots: OutputRoots) -> None:
    args = build.stream_copy_command(
        FIXTURES / "video" / "hevc8-bt709-full.mp4",
        roots.allowed / "rebased.mp4",
        start_s=0.6,
        duration_s=0.5,
    )
    assert "-avoid_negative_ts" in args
    assert args[args.index("-avoid_negative_ts") + 1] == "make_zero"


@pytest.mark.usefixtures("ffmpeg_tools")
def test_excerpt_recorded_start_is_first_displayed_frame(roots: OutputRoots) -> None:
    """Packet pre-roll alone must not certify a trimmed-away display head."""
    source = FIXTURES / "video" / "hevc8-bt709-full.mp4"
    prepared = build.prepare_excerpt(source, start_s=0.6, duration_s=0.5, roots=roots)

    def first_hash(path, start):
        done = media_tool(
            [
                "ffmpeg",
                "-v",
                "error",
                "-ss",
                str(start),
                "-i",
                str(path),
                "-map",
                "0:v:0",
                "-frames:v",
                "1",
                "-f",
                "framemd5",
                "-",
            ]
        )
        assert done.returncode == 0
        return done.stdout.decode().splitlines()[-1].split(",")[-1].strip()

    assert first_hash(source, prepared["actual_start_s"]) == first_hash(prepared["path"], 0)


@pytest.mark.usefixtures("ffmpeg_tools")
def test_gpu_pair_has_explicit_quality_control(
    roots: OutputRoots,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Inspect the real GPU encoder boundary without scheduling a GPU encode."""
    source = FIXTURES / "video" / "hevc8-bt709-full.mp4"

    class InspectedError(Exception):
        pass

    def inspect(argv, **kwargs):
        if "hstack" not in " ".join(argv):
            return media_tool(argv, **kwargs)
        assert argv[argv.index("-c:v") + 1] == "hevc_nvenc"
        for flag, value in (
            ("-preset", "p5"),
            ("-tune", "hq"),
            ("-rc", "vbr"),
            ("-cq", "20"),
            ("-b:v", "0"),
        ):
            assert flag in argv
            assert argv[argv.index(flag) + 1] == value
        raise InspectedError

    monkeypatch.setattr(build, "run_tool", inspect)
    with pytest.raises(InspectedError):
        build.make_pair(source, source, roots.allowed / "gpu-pair.mp4", roots=roots)


def test_page_names_viewing_aid_quality(roots: OutputRoots) -> None:
    text = page.write_page([], {}, roots=roots).read_text()
    assert "NVENC" in text and "CQ 20" in text and "viewing aid" in text


def test_stream_identity_validation_allows_mux_reordering() -> None:
    streams = [
        {"codec_type": "video", "codec_name": "hevc", "codec_tag_string": "hvc1"},
        {"codec_type": "data", "codec_name": "bin_data", "codec_tag_string": "tmcd"},
        {"codec_type": "data", "codec_name": "bin_data", "codec_tag_string": "gpmd"},
    ]
    build.validate_stream_copy(streams, [streams[0], streams[2], streams[1]])


@pytest.mark.parametrize(
    ("label", "rate", "expected"),
    [
        ("00:00:59:29", Fraction(30), "00:01:00:00"),
        ("00:00:59;29", Fraction(30000, 1001), "00:01:00;02"),
        ("00:09:59;29", Fraction(30000, 1001), "00:10:00;00"),
        ("00:00:59;59", Fraction(60000, 1001), "00:01:00;04"),
        ("23:59:59;29", Fraction(30000, 1001), "00:00:00;00"),
    ],
)
def test_timecode_advancement_preserves_smpte_boundaries(label, rate, expected) -> None:
    """Advance one source frame across non-drop, drop-frame and day boundaries."""
    assert build._advance_timecode(label, float(1 / rate), rate) == expected


@pytest.mark.parametrize("kind", ["video", "audio", "data"])
@pytest.mark.usefixtures("ffmpeg_tools")
def test_excerpt_integrity_rejects_changed_non_tmcd_payload(
    roots: OutputRoots,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
) -> None:
    """A corrupt retained payload must become an item error, never a usable input."""
    source = _timecode_source(roots)

    def tampered_probe(argv, **kwargs):
        done = media_tool(argv, **kwargs)
        if (
            argv[0] == "ffprobe"
            and "-show_data_hash" in argv
            and Path(argv[-1]).parent == roots.allowed / "excerpts"
        ):
            value = json.loads(done.stdout)
            packet = next(p for p in value["packets"] if p["codec_type"] == kind)
            # The first data packet may be regenerated tmcd: choose gpmd by index.
            if kind == "data":
                facts = _facts(Path(argv[-1]))
                index = next(
                    s["index"] for s in facts["streams"] if s["codec_tag_string"] == "gpmd"
                )
                packet = next(p for p in value["packets"] if p["stream_index"] == index)
            packet["data_hash"] = "SHA256:planted-corruption"
            return subprocess.CompletedProcess(argv, 0, json.dumps(value).encode(), done.stderr)
        return done

    monkeypatch.setattr(build, "run_tool", tampered_probe)
    prepared = build.prepare_excerpt(source, start_s=0.6, duration_s=0.5, roots=roots)
    assert prepared["status"] == "excerpt_failed" and prepared["path"] is None
    assert "packet payloads" in prepared["message"]
    assert not list((roots.allowed / "excerpts").glob("*.mp4"))


@pytest.mark.usefixtures("ffmpeg_tools")
def test_earlier_excerpt_survives_failed_rerun_cleanup(
    roots: OutputRoots, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only the failed fresh attempt may be removed; an earlier excerpt stays intact."""
    source = roots.footage / "GX011604.mp4"
    shutil.copyfile(_timecode_source(roots), source)
    first = build.prepare_excerpt(source, start_s=0.6, duration_s=0.5, roots=roots)
    earlier = roots.allowed / "excerpts/GX011604.mp4"
    assert first["status"] == "ready" and first["path"] == earlier
    original = earlier.read_bytes()
    assert original

    def tampered_probe(argv, **kwargs):
        done = media_tool(argv, **kwargs)
        if (
            argv[0] == "ffprobe"
            and "-show_data_hash" in argv
            and Path(argv[-1]) == roots.allowed / "excerpts/GX011604-2.mp4"
        ):
            value = json.loads(done.stdout)
            packet = next(p for p in value["packets"] if p["codec_type"] == "video")
            packet["data_hash"] = "SHA256:planted-corruption"
            return subprocess.CompletedProcess(argv, 0, json.dumps(value).encode(), done.stderr)
        return done

    monkeypatch.setattr(build, "run_tool", tampered_probe)
    failed = build.prepare_excerpt(source, start_s=0.6, duration_s=0.5, roots=roots)
    assert failed["status"] == "excerpt_failed" and failed["path"] is None
    assert "packet payloads" in failed["message"]
    assert earlier.read_bytes() == original
    assert not (roots.allowed / "excerpts/GX011604-2.mp4").exists()
    assert list((roots.allowed / "excerpts").glob("*.mp4")) == [earlier]


def test_bom_sheet_tallies_and_preserves_owner_answers(roots: OutputRoots) -> None:
    path = roots.allowed / "bom.csv"
    _csv(path, [_row(_item(), preferred="yes", note="caf\u00e9")])
    path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
    assert sheet.tally(path)["headline"]["preferred"] == 1
    sheet.write_sheet([_item()], path, roots=roots)
    assert "caf\u00e9" in path.read_text(encoding="utf-8-sig")


def test_tally_discloses_partial_set_coverage(roots: OutputRoots) -> None:
    path = roots.allowed / "partial.csv"
    _csv(path, [_row(_item(), preferred="yes"), _row(_item("IMG_6771"))])
    result = sheet.tally(path)
    h = result["headline"]
    assert (h["expected"], h["available"], h["missing"], h["unjudged"]) == (115, 2, 113, 1)
    assert "expected=115" in sheet.format_tally(result)
    assert "headline: 1/1 = 100.0 %  (D65 bar 80 %)" in sheet.format_tally(result)


def test_page_shows_escaped_warnings_and_local_captions(roots: OutputRoots) -> None:
    subject = _item()
    subject["warnings"] = ["warning <unsafe>"]
    _plant_page_item(subject, roots)
    html = page.write_page([subject], {}, roots=roots).read_text()
    assert "warning &lt;unsafe&gt;" in html and "warning <unsafe>" not in html
    assert "<figcaption>Source</figcaption>" in html
    assert "<figcaption>Corrected</figcaption>" in html


@pytest.mark.usefixtures("ffmpeg_tools")
def test_unrotated_frame_cleans_owned_extraction_directory(roots: OutputRoots) -> None:
    build.extract_view_frame(
        FIXTURES / "video" / "hevc8-bt709-full.mp4",
        0,
        roots.allowed / "clean.png",
        roots=roots,
    )
    assert list(roots.allowed.glob(".frames-*")) == []


@pytest.mark.usefixtures("ffmpeg_tools")
def test_browser_sdr_transfer_policy_is_consistent(roots: OutputRoots) -> None:
    values = []
    for primary in ("bt709", "smpte432"):
        path = roots.allowed / f"{primary}.png"
        Image.new("RGB", (16, 16), (128, 128, 128)).save(path)
        build._browser_frame(path, {"color_primaries": primary, "color_transfer": "bt709"}, roots)
        with Image.open(path) as image:
            values.append(image.getpixel((8, 8)))
    assert values[0] == values[1] == (121, 121, 121)


@pytest.mark.usefixtures("ffmpeg_tools")
def test_pair_preserves_variable_presentation_intervals(roots: OutputRoots) -> None:
    source = FIXTURES / "video" / "vfr.mp4"
    pair = roots.allowed / "vfr-pair.mp4"
    build.make_pair(source, source, pair, roots=roots, force_cpu=True)

    def times(path):
        document = _facts(path)
        stream = next(s for s in document["streams"] if s["codec_type"] == "video")
        pts = sorted(
            Fraction(p["pts"]) * Fraction(stream["time_base"])
            for p in document["packets"]
            if p["codec_type"] == "video"
        )
        return [p - pts[0] for p in pts]

    assert times(pair) == times(source)


def _selection_args(roots: OutputRoots, items: list[dict]) -> list[str]:
    """Plant config and a commissioned manifest without resolving real footage."""
    config = roots.allowed / "control.toml"
    config.write_text(
        f"footage_path = {json.dumps(str(roots.footage))}\n"
        f"working_path = {json.dumps(str(roots.allowed.parent))}\n",
        encoding="utf-8",
    )
    manifest = roots.allowed / "selection.json"
    manifest.write_text(
        json.dumps(
            [
                {"name": item["source_name"], "group": item["group"], "kind": item["kind"]}
                for item in items
            ]
        ),
        encoding="utf-8",
    )
    return ["--config", str(config), "--manifest", str(manifest), "--force-cpu"]


def _fake_product(argv, **kwargs):
    """Replace only the expensive product subprocess, including its output/record writes."""
    if argv[0] != "uv":
        return media_tool(argv, **kwargs)
    sources = [Path(value) for value in argv[4 : argv.index("--out")]]
    folder = Path(argv[argv.index("--out") + 1])
    suffix = argv[argv.index("--suffix") + 1]
    document = None
    records = []
    for source in sources:
        photo = source.suffix.lower() == ".jpg"
        refused = source.stem == "IMG_6704"
        output = source.stem + suffix + (".png" if photo else ".mp4")
        record = _runner_record(
            source.name, "" if refused else output, "Unsupported HLG transfer." if refused else None
        )
        record["items"][0]["kind"] = "photo" if photo else "video"
        if not refused:
            if photo:
                Image.new("RGB", (16, 12), "blue").save(folder / output)
            else:
                shutil.copyfile(source, folder / output)
        document = record
        records.extend(record["items"])
    assert document is not None
    document["items"] = records
    document["counts"] = dict(Counter(item["state"] for item in records))
    Path(argv[argv.index("--record") + 1]).write_text(json.dumps(document), encoding="utf-8")
    return subprocess.CompletedProcess(
        argv, int(any(r["state"] == "failed" for r in records)), b"", b""
    )


@pytest.mark.parametrize("kind", ["photo", "video"])
def test_done_item_with_failed_aid_is_loud(
    request: pytest.FixtureRequest, roots: OutputRoots, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    """A failed aid must keep the product link and row while failing the attempted piece."""
    if kind == "video":
        request.getfixturevalue("ffmpeg_tools")
    first = _item() if kind == "photo" else _item("GX011604", "V-S", "video")
    later = _item("IMG_6771") if kind == "photo" else _item("IMG_6704", "V-R", "video", "refused")
    fixture = FIXTURES / (
        "stills/jpeg/jpeg-gradient-srgb.jpg" if kind == "photo" else "video/hevc8-bt709-full.mp4"
    )
    for item in (first, later):
        shutil.copyfile(fixture, roots.footage / item["source_name"])
    args = _selection_args(roots, [first, later])
    monkeypatch.setattr(build, "run_tool", _fake_product)
    real_thumbnail = page.thumbnail

    def fail_aid(*a, **kw):
        if kind == "photo" and first["item"] not in a[0].name:
            return real_thumbnail(*a, **kw)
        raise ValueError("planted aid failure")

    monkeypatch.setattr(
        page if kind == "photo" else build,
        "thumbnail" if kind == "photo" else "make_pair",
        fail_aid,
    )
    assert build.main(["photos" if kind == "photo" else "clips", *args]) == 1
    state = json.loads((roots.allowed / "records/pack.json").read_text())
    results = {item["item"]: item for item in state["items"]}
    assert len(results) == 128
    failed = results[first["item"]]
    assert failed["status"] == "done" and failed["viewing_aid_failed"] is True
    assert failed["aid_message"] == "planted aid failure"
    assert results[later["item"]]["status"] == ("done" if kind == "photo" else "refused")
    assert build.main(["page", *args]) == 2
    html = (roots.allowed / "index.html").read_text()
    not_built = html.split("<h2>Not built</h2>")[1]
    assert first["source_name"] in not_built and "planted aid failure" in not_built
    assert (
        f'href="{"photos" if kind == "photo" else "clips"}/{first["corrected_name"]}"' in not_built
    )
    assert page.check_links(roots.allowed / "index.html", roots=roots) == []
    with (roots.allowed / "review-sheet.csv").open(encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["item"] == first["item"] and rows[0]["viewing_aid_failed"] == "yes"
    assert rows[0]["preferred"] == ""
    # all must also finish its page and report the same attempted-item failure.
    assert build.main(["all", *args]) == 2  # Page reports the remaining catalog items.


def test_judged_aid_failure_keeps_votes_and_counts_normally(roots: OutputRoots) -> None:
    """The aid flag must never remove an available row or change D65's divisor."""
    first, failed = _item(), _item("IMG_6771")
    destination = roots.allowed / "review-sheet.csv"
    _csv(destination, [_row(first, preferred="yes"), _row(failed, preferred="no", note="owner")])
    failed.update(reviewable=False, viewing_aid_failed=True, aid_message="thumbnail failed")
    sheet.write_sheet([first, failed], destination, roots=roots)
    with destination.open(encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[1]["viewing_aid_failed"] == "yes" and rows[1]["note"] == "owner"
    result = sheet.tally(destination)
    assert result["headline"]["judged"] == 2 and result["headline"]["preferred"] == 1
    assert result["headline"]["viewing_aid_failed"] == 1
    assert result["headline"]["available"] == 2 and result["headline"]["missing"] == 113
    text = sheet.format_tally(result)
    assert "headline: 1/2 = 50.0 %  (D65 bar 80 %)" in text
    assert "viewing_aid_failed=1" in text


def test_page_lists_current_failures_even_when_sheet_identity_is_stale(roots: OutputRoots) -> None:
    """A sheet preservation error must not hide the current item failure inventory."""
    item = _item()
    _plant_page_item(item, roots)
    args = _selection_args(roots, [item])
    destination = roots.allowed / "review-sheet.csv"
    _csv(destination, [_row(item, preferred="yes")])
    before = destination.read_bytes()
    item.update(
        corrected_name="IMG_6751_corrected_2.png",
        viewing_aid_failed=True,
        reviewable=False,
        aid_message="current thumbnail failure",
    )
    (roots.allowed / "photos" / item["corrected_name"]).write_bytes(b"product")
    (roots.allowed / "records").mkdir()
    (roots.allowed / "records/pack.json").write_text(json.dumps({"schema": 1, "items": [item]}))
    assert build.main(["page", *args]) != 0
    assert destination.read_bytes() == before
    html = (roots.allowed / "index.html").read_text()
    assert "owner sheet retained" in html and "current thumbnail failure" in html
    assert "current thumbnail failure" in html.split("<h2>Not built</h2>")[1]


def test_clean_piece_does_not_inherit_old_failures(
    roots: OutputRoots, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A saved failed group must not turn a later accounted HLG refusal into failure."""
    failed = _item("GX011604", "V-S", "video", "excerpt_failed")
    refused = _item("IMG_6704", "V-R", "video", "refused")
    args = _selection_args(roots, [failed, refused])
    shutil.copyfile(FIXTURES / "video/hlg.mp4", roots.footage / refused["source_name"])
    records = roots.allowed / "records"
    records.mkdir()
    (records / "pack.json").write_text(json.dumps({"schema": 1, "items": [failed, refused]}))
    monkeypatch.setattr(build, "run_tool", _fake_product)
    assert build.main(["clips", "V-R", *args]) == 0
    assert "1 items accounted for" in capsys.readouterr().out
    # The rendered pack still reports its known failure, without running any item.
    assert build.main(["page", *args]) == 2  # Known failure plus unbuilt catalog items.
    assert build.main(["page", "--check", *args]) == 0


def test_pending_pack_is_not_reported_as_accounted_for(
    roots: OutputRoots, capsys: pytest.CaptureFixture[str]
) -> None:
    """An initial page must distinguish pending inventory from completed attempts."""
    args = _selection_args(roots, [_item()])
    assert build.main(["page", *args]) == 2
    text = capsys.readouterr().out
    assert "0 items accounted for" in text and "pending=128" in text


@pytest.mark.parametrize("bom", [False, True])
def test_page_rebuild_preserves_existing_bom_and_unicode_answers(
    roots: OutputRoots, bom: bool
) -> None:
    """Rebuilding the page must preserve the owner's chosen UTF-8 BOM form."""
    item = _item()
    _plant_page_item(item, roots)
    args = _selection_args(roots, [item])
    destination = roots.allowed / "review-sheet.csv"
    _csv(destination, [_row(item, preferred="yes", note="caf\u00e9, owner\nsecond line")])
    if bom:
        destination.write_bytes(b"\xef\xbb\xbf" + destination.read_bytes())
    (roots.allowed / "records").mkdir()
    (roots.allowed / "records/pack.json").write_text(json.dumps({"schema": 1, "items": [item]}))
    assert build.main(["page", *args]) == 2
    assert destination.read_bytes().startswith(b"\xef\xbb\xbf") is bom
    with destination.open(encoding="utf-8-sig", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert row["preferred"] == "yes" and row["note"] == "caf\u00e9, owner\nsecond line"


@pytest.mark.parametrize("fault_row", [1, 2, 3])
def test_non_utf8_sheet_names_csv_row_and_encoding(
    roots: OutputRoots, capsys: pytest.CaptureFixture[str], fault_row: int
) -> None:
    """Invalid UTF-8 must name the logical CSV row, including a multiline note."""
    destination = roots.allowed / "owner.csv"
    _csv(destination, [_row(_item(), note="two\nlines"), _row(_item("IMG_6771"), note="caf\u00e9")])
    data = destination.read_bytes()
    if fault_row == 1:
        data = data.replace(b"item", b"it\xe9m", 1)
    elif fault_row == 2:
        data = data.replace(b"two", b"tw\xe9", 1)
    else:
        data = data.replace("caf\u00e9".encode(), b"caf\xe9")
    destination.write_bytes(data)
    assert build.main(["tally", str(destination)]) == 2
    text = capsys.readouterr().err
    assert f"row {fault_row}" in text and "UTF-8" in text
    assert destination.read_bytes() == data


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "the EXIF block is damaged; it is not carried",
            "the EXIF block is damaged; it is not carried",
        ),
        ("GPS metadata was not carried", "GPS metadata was not carried"),
        (
            "EXIF GPSLatitude=21.3; the EXIF block is damaged",
            "[withheld]; the EXIF block is damaged",
        ),
        ("EXIF Orientation: 9", "[withheld]"),
        ("bad EXIF value 'private location'", "[withheld]"),
    ],
)
def test_metadata_filter_preserves_diagnostics_and_withholds_values(
    roots: OutputRoots, text: str, expected: str
) -> None:
    """The privacy projection must preserve value-free product diagnostics."""
    assert build._safe_text(text, roots) == expected


def test_invoke_never_rewrites_product_record_and_filters_only_projection(
    roots: OutputRoots, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The original runner bytes stay authoritative; only pack-facing text is filtered."""
    source = roots.footage / "IMG_6751.JPG"
    shutil.copyfile(FIXTURES / "stills/jpeg/jpeg-gradient-srgb.jpg", source)
    raw_record = _runner_record(source.name, failure="EXIF Orientation: 9")
    raw_record["items"][0]["warnings"] = ["the EXIF block is damaged; it is not carried"]
    raw_bytes = json.dumps(raw_record, separators=(",", ":")).encode() + b"\n"

    def product(argv, **kw):
        Path(argv[argv.index("--record") + 1]).write_bytes(raw_bytes)
        return subprocess.CompletedProcess(argv, 1, b"EXIF GPSLatitude=21.3\n", b"")

    monkeypatch.setattr(build, "run_tool", product)
    rows, code = build._invoke([source], "P-A", roots, neutral=False, force_cpu=True)
    assert code == 1 and (roots.allowed / "records/P-A.json").read_bytes() == raw_bytes
    assert rows[0]["message"] == "[withheld]"
    assert rows[0]["warnings"] == ["the EXIF block is damaged; it is not carried"]
    assert "21.3" not in (roots.allowed / "logs/P-A.log").read_text()


@pytest.mark.parametrize("state", ["not run", "cancelled"])
@pytest.mark.parametrize("message", [None, "runner supplied reason"])
def test_runner_unfinished_states_keep_status_and_reason(
    roots: OutputRoots, state: str, message: str | None
) -> None:
    """Runner cancellation facts must survive mapping and remain visible under Not built."""
    document = _runner_record("GX011604.mp4", failure=message)
    document["items"][0].update(state=state, kind="video", outputs=[])
    path = roots.allowed / "record.json"
    path.write_text(json.dumps(document))
    result = build.read_runner_record(path, group="V-S", roots=roots)[0]
    assert result["status"] == state
    if message:
        assert result["message"] == message
    else:
        assert result["message"] == f"runner reported {state}; no further reason was supplied"
    html = page.write_page([result], {}, roots=roots).read_text()
    not_built = html.split("<h2>Not built</h2>")[1]
    assert f": {state}" in not_built and result["message"] in not_built
    destination = roots.allowed / "sheet.csv"
    sheet.write_sheet([result], destination, roots=roots)
    assert sheet.tally(destination)["headline"]["available"] == 0


def test_page_explains_blank_undecided_exact_case_and_aid_flag(roots: OutputRoots) -> None:
    """The owner must be told which literal entries affect D65's numerator and divisor."""
    html = page.write_page([], {}, roots=roots).read_text()
    assert "blank means unjudged" in html
    assert "yes, no and undecided count as judged" in html
    assert "only yes counts as preferred" in html
    assert "exact lowercase" in html
    assert "viewing_aid_failed" in html and "count normally" in html


@pytest.mark.parametrize("failure", ["size", "encode", "browser", "photo"])
def test_failed_aid_removes_only_its_own_artifacts(
    request: pytest.FixtureRequest,
    roots: OutputRoots,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    """Failed size, pair, browser and thumbnail work must not leak or prune older files."""
    if failure != "photo":
        request.getfixturevalue("ffmpeg_tools")
    pairs = roots.allowed / "pairs"
    thumbs = roots.allowed / "thumbs"
    pairs.mkdir()
    thumbs.mkdir()
    old_pair = pairs / "GX011604_pair.mp4"
    old_pair.write_bytes(b"earlier successful aid")
    (thumbs / "earlier.jpg").write_bytes(b"older thumbnail")
    item = _item() if failure == "photo" else _item("GX011604", "V-S", "video")
    item.update(source_thumb="", corrected_thumb="", pair_name="", stills=[])
    product = roots.allowed / ("photos" if failure == "photo" else "clips") / item["corrected_name"]
    product.parent.mkdir()
    if failure == "photo":
        Image.new("RGB", (16, 12), "blue").save(product)
        Image.new("RGB", (16, 12), "red").save(product.parent / item["source_view_name"])
    else:
        shutil.copyfile(FIXTURES / "video/hevc8-bt709-full.mp4", product)
    before = {
        p.relative_to(roots.allowed): p.read_bytes()
        for p in roots.allowed.rglob("*")
        if p.is_file()
    }

    if failure == "size":

        def fail_size(source, time, destination, **kw):
            destination.write_bytes(b"partial frame")
            raise ValueError("planted size failure")

        monkeypatch.setattr(build, "extract_view_frame", fail_size)
    elif failure == "encode":

        def fail_encode(argv, **kw):
            if "-filter_complex" in argv:
                Path(argv[-1]).write_bytes(b"partial pair")
                return subprocess.CompletedProcess(argv, 1, b"", b"planted encoder failure")
            return media_tool(argv, **kw)

        monkeypatch.setattr(build, "run_tool", fail_encode)
    elif failure == "browser":

        def fail_browser(path, stream, roots):
            raise ValueError("planted browser failure")

        monkeypatch.setattr(build, "_browser_frame", fail_browser)
    else:
        real_thumbnail = page.thumbnail
        count = 0

        def fail_thumbnail(source, destination, **kw):
            nonlocal count
            count += 1
            if count == 2:
                destination.write_bytes(b"partial thumbnail")
                raise ValueError("planted thumbnail failure")
            return real_thumbnail(source, destination, **kw)

        monkeypatch.setattr(page, "thumbnail", fail_thumbnail)
    with pytest.raises(ValueError, match=r"planted|encode failed"):
        if failure == "photo":
            build._view_photo(item, roots)
        else:
            build._view_video(item, product, roots, force_cpu=True)
    after = {
        p.relative_to(roots.allowed): p.read_bytes()
        for p in roots.allowed.rglob("*")
        if p.is_file()
    }
    assert after == before
    assert item["source_thumb"] == item["corrected_thumb"] == item["pair_name"] == ""
    assert item["stills"] == []


def test_failed_browser_conversion_cleans_partial_srgb_file(
    roots: OutputRoots, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed conversion must remove its unique scratch PNG and retain its input."""
    path = roots.allowed / "frame.png"
    Image.new("RGB", (16, 12), "blue").save(path)
    before = path.read_bytes()

    def fail_conversion(argv, **kw):
        Path(argv[-1]).write_bytes(b"partial conversion")
        return subprocess.CompletedProcess(argv, 1, b"", b"planted conversion failure")

    monkeypatch.setattr(build, "run_tool", fail_conversion)
    with pytest.raises(ValueError, match="conversion"):
        build._browser_frame(path, {"color_primaries": "bt709", "color_transfer": "bt709"}, roots)
    assert path.read_bytes() == before
    assert list(roots.allowed.glob("*.png")) == [path]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("EXIF GPSLatitude; 21.3", "[withheld]"),
        (
            "the EXIF block is damaged (bad value 9); it is not carried",
            "the EXIF block is damaged ([withheld]); it is not carried",
        ),
        (
            "IMG_6751.JPG: the EXIF block is damaged; it is not carried",
            "IMG_6751.JPG: the EXIF block is damaged; it is not carried",
        ),
    ],
)
def test_metadata_filter_handles_uncertain_boundaries_and_embedded_details(
    roots: OutputRoots, text: str, expected: str
) -> None:
    """A semicolon must not leak a tag value; embedded details need only local withholding."""
    assert build._safe_text(text, roots) == expected


def test_original_sheet_header_migrates_without_losing_owner_answers(roots: OutputRoots) -> None:
    """The required new flag must extend an existing original CP5 sheet safely."""
    destination = roots.allowed / "review-sheet.csv"
    item = _item()
    row = _row(item, preferred="undecided", note="owner's earlier answer")
    del row["viewing_aid_failed"]
    _csv(destination, [row], header=HEADER[:-1])
    assert sheet.tally(destination)["headline"]["judged"] == 1
    item.update(reviewable=False, viewing_aid_failed=True, aid_message="pair unavailable")
    sheet.write_sheet([item], destination, roots=roots)
    with destination.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        migrated = next(reader)
        assert tuple(reader.fieldnames) == HEADER
    assert migrated["preferred"] == "undecided" and migrated["note"] == "owner's earlier answer"
    assert migrated["viewing_aid_failed"] == "yes"


@pytest.mark.parametrize("missing", [False, True])
def test_manifest_replaces_or_appends_without_pruning_catalog_state(
    roots: OutputRoots,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    missing: bool,
) -> None:
    """A one-item rerun must preserve all other rows and catalog-wide pending coverage."""
    selected = _item()
    args = _selection_args(roots, [selected])
    shutil.copyfile(
        FIXTURES / "stills/jpeg/jpeg-gradient-srgb.jpg", roots.footage / selected["source_name"]
    )
    original = [build._pending(item) for item in select.catalog()]
    position = next(i for i, item in enumerate(original) if item["item"] == "IMG_6751")
    if missing:
        original.pop(position)
    else:
        original[position] = {**selected, "old_attempt": True}
    records = roots.allowed / "records"
    records.mkdir()
    (records / "pack.json").write_text(json.dumps({"schema": 1, "items": original}))
    monkeypatch.setattr(build, "run_tool", _fake_product)
    assert build.main(["photos", *args]) == 0
    actual = json.loads((records / "pack.json").read_text())["items"]
    assert len(actual) == 128
    by_name = {item["item"]: item for item in actual}
    assert by_name["IMG_6751"]["status"] == "done"
    assert "old_attempt" not in by_name["IMG_6751"]
    unchanged = [item for item in original if item["item"] != "IMG_6751"]
    assert all(by_name[item["item"]] == item for item in unchanged)
    assert len(unchanged) == 127
    assert "pending=127" in capsys.readouterr().out


def test_missing_excerpt_error_is_appended_without_dropping_saved_rows(
    roots: OutputRoots,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An excerpt failure must be saved even when its item is absent in old state."""
    subject = _item("GX011604", "V-S", "video")
    args = _selection_args(roots, [subject])
    (roots.footage / subject["source_name"]).write_bytes(b"planted")
    saved = _item("IMG_6771", status="failed")
    records = roots.allowed / "records"
    records.mkdir()
    (records / "pack.json").write_text(json.dumps({"schema": 1, "items": [saved]}))
    monkeypatch.setattr(build, "_video", lambda source: {"duration_s": 60.0})
    monkeypatch.setattr(
        build,
        "prepare_excerpt",
        lambda *a, **kw: {
            "path": None,
            "excerpt": False,
            "status": "excerpt_failed",
            "message": "copy failed",
        },
    )
    assert build.main(["clips", "V-S", *args]) == 1
    rows = json.loads((records / "pack.json").read_text())["items"]
    assert len(rows) == 2 and rows[0] == saved
    assert rows[1]["item"] == "GX011604" and rows[1]["status"] == "excerpt_failed"


@pytest.mark.parametrize("fault", ["neutral", "icc"])
def test_photo_source_or_icc_aid_failure_keeps_product_and_continues(
    roots: OutputRoots,
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
) -> None:
    """Neutral export and real ICC transform failures must preserve done exports and rows."""
    first, later = _item(), _item("IMG_6771")
    args = _selection_args(roots, [first, later])
    for item in (first, later):
        shutil.copyfile(
            FIXTURES / "stills/jpeg/jpeg-gradient-srgb.jpg", roots.footage / item["source_name"]
        )

    def product(argv, **kwargs):
        done = _fake_product(argv, **kwargs)
        if argv[0] != "uv":
            return done
        neutral = "--neutral" in argv
        folder = Path(argv[argv.index("--out") + 1])
        if fault == "neutral" and neutral:
            record_path = Path(argv[argv.index("--record") + 1])
            document = json.loads(record_path.read_text())
            document["items"][0].update(
                state="failed", output_name=None, failure="neutral export failed"
            )
            document["counts"] = {"failed": 1, "done": 1}
            record_path.write_text(json.dumps(document))
            (folder / "IMG_6751_neutral.png").unlink()
            return subprocess.CompletedProcess(argv, 1, b"", b"")
        if fault == "icc" and not neutral:
            profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("LAB")).tobytes()
            Image.new("RGB", (16, 12), "blue").save(
                folder / "IMG_6751_corrected.png",
                icc_profile=profile,
            )
        return done

    monkeypatch.setattr(build, "run_tool", product)
    assert build.main(["photos", *args]) == 1
    rows = json.loads((roots.allowed / "records/pack.json").read_text())["items"]
    by_name = {row["item"]: row for row in rows}
    failed = by_name["IMG_6751"]
    assert failed["status"] == "done" and failed["viewing_aid_failed"] is True
    assert failed["reviewable"] is False and failed["aid_message"]
    assert not failed["aid_message"].startswith("; ")
    assert failed["corrected_name"] == "IMG_6751_corrected.png"
    assert (roots.allowed / "photos" / failed["corrected_name"]).is_file()
    assert by_name["IMG_6771"]["status"] == "done"
    assert by_name["IMG_6771"].get("viewing_aid_failed", False) is False
    assert build.main(["page", *args]) != 0
    html = (roots.allowed / "index.html").read_text()
    assert 'href="photos/IMG_6751_corrected.png"' in html.split("<h2>Not built</h2>")[1]
    if fault == "neutral":
        assert 'href="photos/IMG_6751_neutral.png"' not in html
        assert "neutral source view: neutral export failed" in html
    assert page.check_links(roots.allowed / "index.html", roots=roots) == []
    with (roots.allowed / "review-sheet.csv").open(encoding="utf-8-sig") as handle:
        sheet_rows = list(csv.DictReader(handle))
    assert len(sheet_rows) == 2
    assert sheet_rows[0]["item"] == "IMG_6751"
    assert sheet_rows[0]["viewing_aid_failed"] == "yes"


@pytest.mark.parametrize("fault", ["probe", "prepare"])
def test_clip_item_probe_or_prepare_fault_is_a_row_and_later_group_runs(
    request: pytest.FixtureRequest,
    roots: OutputRoots,
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
) -> None:
    """One malformed item's probe or packet facts must not abort later selected items."""
    if fault == "prepare":
        request.getfixturevalue("ffmpeg_tools")
    first = _item("GX011604", "V-S", "video")
    later = _item("IMG_6704", "V-R", "video", "refused")
    args = _selection_args(roots, [first, later])
    for item in (first, later):
        shutil.copyfile(
            FIXTURES / "video/hevc8-bt709-full.mp4", roots.footage / item["source_name"]
        )

    def video(source):
        if fault == "probe":
            raise ValueError(f'"{source}": invalid duration')
        return {"duration_s": 60.0}

    monkeypatch.setattr(build, "run_tool", _fake_product)
    monkeypatch.setattr(build, "_video", video)
    monkeypatch.setattr(
        build,
        "_packet_facts",
        lambda *a: [
            {"codec_type": "video", "flags": "K"},
        ],
    )
    assert build.main(["clips", *args]) == 1
    rows = json.loads((roots.allowed / "records/pack.json").read_text())["items"]
    by_name = {row["item"]: row for row in rows}
    failed = by_name["GX011604"]
    assert failed["status"] == ("failed" if fault == "probe" else "excerpt_failed")
    assert failed["message"] and str(roots.footage) not in failed["message"]
    assert by_name["IMG_6704"]["status"] == "refused"
    assert not (roots.allowed / "clips/GX011604_corrected.mp4").exists()
    if fault == "prepare":
        excerpt_rows = json.loads((roots.allowed / "records/V-S-excerpts.json").read_text())
        assert excerpt_rows["items"][0]["status"] == "excerpt_failed"


def test_page_and_tally_expose_catalog_pending_including_absent_refusals(
    roots: OutputRoots,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Missing saved rows and unrun HLG results must prevent a finished-pack exit."""
    args = _selection_args(roots, [_item()])
    records = roots.allowed / "records"
    records.mkdir()
    rows = [
        dict(build._pending(item), status="failed")
        for item in select.catalog()
        if item.group not in {"V-R", "V-Z"}
    ]
    rows.append(build._pending(next(item for item in select.catalog() if item.group == "V-Z")))
    state_path = records / "pack.json"
    state_path.write_text(json.dumps({"schema": 1, "items": rows}))
    assert build.main(["page", *args]) == 2
    assert "pending=4" in capsys.readouterr().out
    html = (roots.allowed / "index.html").read_text()
    header = html.split("<h2>Starter presets</h2>")[0]
    assert "Pending: 4" in header and "V-R=2" in header and "V-Z=2" in header
    assert page.check_links(roots.allowed / "index.html", roots=roots) == []
    assert build.main(["page", "--check", *args]) == 0
    assert build.main(["tally", str(roots.allowed / "review-sheet.csv")]) == 0
    text = capsys.readouterr().out
    assert "pack pending: 4" in text and "V-R=2" in text
    # V-R refusals are accounted results, not pending or review-sheet rows.
    for item in select.catalog():
        if item.group == "V-R":
            rows.append(dict(build._pending(item), status="refused", message="HLG refused"))
    state_path.write_text(json.dumps({"schema": 1, "items": rows}))
    assert build.main(["page", *args]) == 2
    assert "Pending: 2" in (roots.allowed / "index.html").read_text()
    assert build.main(["tally", str(roots.allowed / "review-sheet.csv")]) == 0
    text = capsys.readouterr().out
    assert "pack pending: 2" in text and "V-R=2" not in text
    with (roots.allowed / "review-sheet.csv").open() as handle:
        assert list(csv.DictReader(handle)) == []


@pytest.mark.parametrize(
    "text, expected",
    [
        (r"\Phone\IMG_6702.MOV: probe failed", "IMG_6702.MOV: probe failed"),
        ('"C:\\Program Files\\ffmpeg\\bin\\x.dll": load failed', '"x.dll": load failed'),
        ('"/opt/media tools/bin/ffmpeg": load failed', '"ffmpeg": load failed'),
        (r"C:\Program Files\ffmpeg\bin\x.dll: load failed", "x.dll: load failed"),
    ],
)
def test_diagnostics_collapse_folder_tokens_and_paths_with_spaces(
    roots: OutputRoots,
    text: str,
    expected: str,
) -> None:
    """External tool paths must reduce to file names without leaking folder tails."""
    assert build._safe_text(text, roots) == expected


def test_root_stripping_still_collapses_remaining_relative_folders(roots: OutputRoots) -> None:
    """Removing a configured root must not leave its Phone subfolder in a diagnostic."""
    text = str(roots.footage) + r"\Phone\IMG_6702.MOV: probe failed"
    assert build._safe_text(text, roots) == "IMG_6702.MOV: probe failed"


def test_excerpt_records_merge_two_manifest_runs_by_item(
    roots: OutputRoots,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A targeted rerun must retain the other excerpt row and replace its own facts."""
    items = [_item("GX011603", "V-S", "video"), _item("GX011604", "V-S", "video")]
    for item in items:
        (roots.footage / item["source_name"]).write_bytes(b"planted")
    monkeypatch.setattr(build, "_video", lambda source: {"duration_s": 60.0})
    attempt = 1

    def excerpt(source, **kwargs):
        return {
            "path": None,
            "excerpt": False,
            "status": "excerpt_failed",
            "message": f"copy attempt {attempt}",
            "planned_start_s": 24.0,
        }

    monkeypatch.setattr(build, "prepare_excerpt", excerpt)
    assert build.main(["clips", "V-S", *_selection_args(roots, items)]) == 1
    path = roots.allowed / "records/V-S-excerpts.json"
    first = json.loads(path.read_text())["items"]
    assert [row["item"] for row in first] == ["GX011603", "GX011604"]
    attempt = 2
    assert build.main(["clips", "V-S", *_selection_args(roots, items[1:])]) == 1
    second = json.loads(path.read_text())["items"]
    assert len(second) == 2 and second[0] == first[0]
    assert second[1]["item"] == "GX011604" and second[1]["message"] == "copy attempt 2"
    state = json.loads((roots.allowed / "records/pack.json").read_text())
    assert len(state["items"]) == 128


def test_excerpt_sidecar_names_fresh_file_after_targeted_rerun(
    roots: OutputRoots, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Excerpt sidecars must identify the same fresh media file as pack.json."""
    items = [_item("GX011603", "V-S", "video"), _item("GX011604", "V-S", "video")]
    for item in items:
        (roots.footage / item["source_name"]).write_bytes(b"planted excerpt input")
    monkeypatch.setattr(build, "_video", lambda source: {"duration_s": 60.0})

    def excerpt(source, *, roots, start_s, duration_s):
        target = build._fresh(roots.allowed / "excerpts" / source.name, roots)
        roots.mkdir(target.parent)
        roots.write_bytes(target, source.read_bytes())
        return {
            "path": target,
            "excerpt": True,
            "status": "ready",
            "message": "",
            "planned_start_s": start_s,
            "actual_start_s": start_s,
            "duration_s": duration_s,
        }

    monkeypatch.setattr(build, "prepare_excerpt", excerpt)
    monkeypatch.setattr(build, "run_tool", _fake_product)
    monkeypatch.setattr(build, "_view_video", lambda *a, **kw: None)
    assert build.main(["clips", "V-S", *_selection_args(roots, items)]) == 0
    assert build.main(["clips", "V-S", *_selection_args(roots, items[1:])]) == 0
    sidecar = json.loads((roots.allowed / "records/V-S-excerpts.json").read_text())["items"]
    state = json.loads((roots.allowed / "records/pack.json").read_text())["items"]
    assert len(sidecar) == 2 and len(state) == 128
    for row, expected in zip(sidecar, ("GX011603.mp4", "GX011604-2.mp4"), strict=True):
        assert row["excerpt"].get("name") == expected
        packed = next(item for item in state if item["item"] == row["item"])
        assert row["excerpt"]["name"] == packed["excerpt"]["name"]
        assert (roots.allowed / "excerpts" / expected).is_file()


def _complete_pack(roots: OutputRoots) -> tuple[dict, list[str]]:
    """Plant every commissioned result and its link targets without processing media."""
    rows = []
    for item in select.catalog():
        row = _item(item.stem, item.group, item.kind, "refused" if item.group == "V-R" else "done")
        row["source_name"] = item.name
        _plant_page_item(row, roots)
        rows.append(row)
    state = {"schema": 1, "items": rows}
    (roots.allowed / "records").mkdir()
    (roots.allowed / "records/pack.json").write_text(json.dumps(state))
    return state, _selection_args(roots, [_item()])


@pytest.mark.parametrize("answered", [False, True])
@pytest.mark.parametrize("available", [False, True])
def test_sheet_rerun_conflict_never_blocks_later_rows(
    roots: OutputRoots,
    capsys: pytest.CaptureFixture[str],
    answered: bool,
    available: bool,
) -> None:
    """Only answered stale pairs conflict; every rebuild still adds later items."""
    state, args = _complete_pack(roots)
    state["presets"] = _presets(roots)
    destination = roots.allowed / "review-sheet.csv"
    original = _item()
    # Preserve noncanonical CSV quoting and CRLF, including a multiline answer.
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADER, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerow(
            _row(original, note='owner says "keep",\r\nthis answer' if answered else "")
        )
    before = destination.read_bytes()
    original_record = before[before.index(b"\n") + 1 :]
    current = next(row for row in state["items"] if row["item"] == "IMG_6751")
    if available:
        current["corrected_name"] = "IMG_6751_corrected_2.png"
        _plant_page_item(current, roots)
        assert (roots.allowed / "photos/IMG_6751_corrected.png").is_file()
        assert (roots.allowed / "photos/IMG_6751_corrected_2.png").is_file()
    else:
        current.update(status="failed", corrected_name="", reviewable=False)
    path = roots.allowed / "records/pack.json"
    path.write_text(json.dumps(state))
    pack_before = path.read_bytes()

    assert build.main(["page", *args]) == (2 if answered else (0 if available else 1))
    output = capsys.readouterr()
    if available:
        assert (roots.allowed / "photos/IMG_6751_corrected.png").is_file()
        assert (roots.allowed / "photos/IMG_6751_corrected_2.png").is_file()
    with destination.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 126
    assert any(row["item"] == "IMG_6702" for row in rows)
    retained = next(row for row in rows if row["item"] == "IMG_6751")
    if answered or not available:
        assert retained == _row(
            original, note='owner says "keep",\r\nthis answer' if answered else ""
        )
        assert original_record in destination.read_bytes()
    else:
        assert retained["corrected_name"] == "IMG_6751_corrected_2.png"
    html = unescape((roots.allowed / "index.html").read_text())
    recovery = "blank that row's owner cells in the sheet to accept the new output"
    if answered:
        assert "IMG_6751" in output.err and "conflict" in output.err.lower()
        assert "IMG_6751" in html and "conflict" in html.lower()
        assert recovery in html and "restore the earlier output" in html
        assert recovery in (roots.allowed / "README.md").read_text()
        # Clearing owner answers accepts a regenerated pair on the next page.
        retained["note"] = ""
        _csv(destination, rows)
        assert build.main(["page", *args]) == (0 if available else 1)
        assert "conflict" not in capsys.readouterr().err.lower()
        assert recovery not in (roots.allowed / "index.html").read_text()
    else:
        assert "conflict" not in output.err.lower()
        assert recovery not in html
    assert path.read_bytes() == pack_before
    assert page.check_links(roots.allowed / "index.html", roots=roots) == []


@pytest.mark.parametrize("available", [False, True])
def test_page_conflict_section_and_stderr_identify_both_outputs(
    roots: OutputRoots, capsys: pytest.CaptureFixture[str], available: bool
) -> None:
    """Owner conflicts must expose judged/current output identities on both surfaces."""
    state, args = _complete_pack(roots)
    state["presets"] = _presets(roots)
    destination = roots.allowed / "review-sheet.csv"
    _csv(destination, [_row(_item(), preferred="yes")])
    before = destination.read_bytes()
    current = next(row for row in state["items"] if row["item"] == "IMG_6751")
    if available:
        current["corrected_name"] = "IMG_6751_corrected_2.png"
        _plant_page_item(current, roots)
    else:
        current.update(status="failed", corrected_name="", reviewable=False)
    (roots.allowed / "records/pack.json").write_text(json.dumps(state))
    assert build.main(["page", *args]) == 2
    stderr = capsys.readouterr().err
    line = next(line for line in stderr.splitlines() if "conflict" in line.lower())
    assert "IMG_6751_corrected.png" in line
    if available:
        assert "IMG_6751_corrected_2.png" in line
    else:
        assert "failed" in line and "(none)" in line
    assert "blank that row's owner cells" in line and "restore the earlier output" in line
    html = (roots.allowed / "index.html").read_text()
    assert '<section id="sheet-conflicts">' in html
    section = unescape(html.split('<section id="sheet-conflicts">', 1)[1].split("</section>", 1)[0])
    assert "IMG_6751" in section and "IMG_6751_corrected.png" in section
    if available:
        assert "IMG_6751_corrected_2.png" in section
        assert (roots.allowed / "photos/IMG_6751_corrected.png").is_file()
        assert (roots.allowed / "photos/IMG_6751_corrected_2.png").is_file()
    else:
        assert "failed" in section and "(none)" in section
    assert "blank that row's owner cells" in section and "restore the earlier output" in section
    assert before in destination.read_bytes()
    assert page.check_links(roots.allowed / "index.html", roots=roots) == []


def test_sheet_conflict_details_carry_judged_current_names_and_status(roots: OutputRoots) -> None:
    """A conflict exception must carry pair facts without changing its item-name API."""
    destination = roots.allowed / "review-sheet.csv"
    _csv(destination, [_row(_item(), preferred="yes"), _row(_item("IMG_6771"), note="keep")])
    changed = {**_item(), "corrected_name": "IMG_6751_corrected_2.png"}
    unavailable = {**_item("IMG_6771"), "status": "cancelled", "reviewable": False}
    with pytest.raises(sheet.SheetConflictError) as error:
        sheet.write_sheet([changed, unavailable], destination, roots=roots)
    assert set(error.value.items) == {"IMG_6751", "IMG_6771"}
    assert {row["item"]: dict(row) for row in error.value.details} == {
        "IMG_6751": {
            "item": "IMG_6751",
            "judged_name": "IMG_6751_corrected.png",
            "current_name": "IMG_6751_corrected_2.png",
            "current_status": "done",
        },
        "IMG_6771": {
            "item": "IMG_6771",
            "judged_name": "IMG_6771_corrected.png",
            "current_name": "IMG_6771_corrected.png",
            "current_status": "cancelled",
        },
    }


def test_page_has_visible_conflict_section_for_every_stale_item(roots: OutputRoots) -> None:
    """A generic item listing or README must not substitute for visible conflict entries."""
    items = [_item(), _item("IMG_6771")]
    destination = roots.allowed / "review-sheet.csv"
    _csv(destination, [_row(item, preferred="yes") for item in items])
    for item in items:
        item["corrected_name"] = item["item"] + "_corrected_2.png"
        _plant_page_item(item, roots)
    (roots.allowed / "records").mkdir()
    (roots.allowed / "records/pack.json").write_text(json.dumps({"schema": 1, "items": items}))
    assert build.main(["page", *_selection_args(roots, items)]) == 2
    html = (roots.allowed / "index.html").read_text()
    assert '<section id="sheet-conflicts">' in html
    section = unescape(html.split('<section id="sheet-conflicts">', 1)[1].split("</section>", 1)[0])
    assert section.count("<li>") == 2
    for name in ("IMG_6751", "IMG_6771"):
        assert name in section
        assert name + "_corrected.png" in section
        assert name + "_corrected_2.png" in section
    assert "blank that row's owner cells" in section and "restore the earlier output" in section


def test_conflict_section_escapes_every_displayed_fact(roots: OutputRoots) -> None:
    """Conflict facts must remain text even when a planted value contains HTML."""
    detail = {
        "item": "<item>",
        "judged_name": "<judged.png>",
        "current_name": "<current.png>",
        "current_status": "<cancelled>",
    }
    path = page.write_page([], {}, roots=roots, sheet_conflicts=[detail])
    section = (
        path.read_text().split('<section id="sheet-conflicts">', 1)[1].split("</section>", 1)[0]
    )
    for value in detail.values():
        assert value not in section
        assert value in unescape(section)


@pytest.mark.slow(reason="5.6-5.75 s under -n 4 at WP5.3 gate w53 (B-F4)")
@pytest.mark.parametrize("present", [0, 1])
def test_missing_starter_presets_are_pending_until_both_tables_exist(
    roots: OutputRoots,
    present: int,
) -> None:
    """Accounted media alone must not make a finished page without both starter tables."""
    state, args = _complete_pack(roots)
    if present:
        presets = _presets(roots)
        state["presets"] = {"Snorkel (shallow)": presets["Snorkel (shallow)"]}
        (roots.allowed / "records/pack.json").write_text(json.dumps(state))
    assert build.main(["page", *args]) == 2
    html = (roots.allowed / "index.html").read_text()
    assert "Pending presets:" in html.split("<h2>Starter presets</h2>")[0]
    assert "Scuba (deep)" in html.split("<h2>Starter presets</h2>")[0]
    assert PRESET_SENTENCE not in html
    assert page.check_links(roots.allowed / "index.html", roots=roots) == []
    assert build.main(["presets", *args]) == 0
    assert build.main(["page", *args]) == 0
    html = (roots.allowed / "index.html").read_text()
    assert html.count("<table>") == 2 and PRESET_SENTENCE in html


@pytest.mark.parametrize("saved", [False, True])
def test_page_never_creates_or_rewrites_pack_state(roots: OutputRoots, saved: bool) -> None:
    """Rendering may regenerate views but cannot write back a stale state snapshot."""
    args = _selection_args(roots, [_item()])
    path = roots.allowed / "records/pack.json"
    before = b'{ "schema": 1, "items": [] }\n'
    if saved:
        path.parent.mkdir()
        path.write_bytes(before)
    assert build.main(["page", *args]) == 2
    assert path.exists() is saved
    if saved:
        assert path.read_bytes() == before


def test_second_stage_refuses_held_lock_and_never_breaks_it(
    roots: OutputRoots,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A second writer must identify the holder and leave even an old lock untouched."""
    args = _selection_args(roots, [_item()])
    path = roots.allowed / ".reviewpack.lock"
    body = f"pid={os.getpid()}\nstarted=2026-01-01T00:00:00+00:00\n"
    with path.open("x", encoding="utf-8", newline="") as held:
        held.write(body)
        held.flush()
        assert build.main(["presets", *args]) == 2
        text = capsys.readouterr().err
        assert f"pid={os.getpid()}" in text and "2026-01-01T00:00:00+00:00" in text
        assert "stale" in text and "delete .reviewpack.lock" in text
        assert path.read_text() == body
        assert not (roots.allowed / "records/pack.json").exists()
        assert not (roots.allowed / "presets").exists()
    path.unlink()  # This test owns the planted lock; the instrument never broke it.
    assert build.main(["presets", *args]) == 0
    assert not path.exists()


@pytest.mark.parametrize(
    "text, expected",
    [
        ("time base 1/90000 is not 1/N ticks.", "time base 1/90000 is not 1/N ticks."),
        ("(ipco/ipma)", "(ipco/ipma)"),
        ("(moov/udta)", "(moov/udta)"),
        ("30000/1001 fps", "30000/1001 fps"),
        (r"\Phone\IMG_6702.MOV: probe failed", "IMG_6702.MOV: probe failed"),
        ('"C:\\Program Files\\ffmpeg\\bin\\x.dll": load failed', '"x.dll": load failed'),
        ('"/opt/media tools/bin/ffmpeg": load failed', '"ffmpeg": load failed'),
    ],
)
def test_path_privacy_preserves_product_ratios_and_box_names(
    roots: OutputRoots,
    text: str,
    expected: str,
) -> None:
    """Path redaction must distinguish real paths from product ratios and box names."""
    assert build._safe_text(text, roots) == expected


@pytest.mark.parametrize(
    "failure", [None, "Cannot read input.", "HLG decoder could not read input."]
)
def test_unexpected_refused_group_result_is_flagged_without_inventing_refusal(
    roots: OutputRoots,
    monkeypatch: pytest.MonkeyPatch,
    failure: str | None,
) -> None:
    """Done or unrelated failed V-R results must expose an expected-refusal regression."""
    subject = _item("IMG_6772", "V-R", "video")
    args = _selection_args(roots, [subject])
    shutil.copyfile(FIXTURES / "video/hevc8-bt709-full.mp4", roots.footage / subject["source_name"])

    def product(argv, **kwargs):
        done = _fake_product(argv, **kwargs)
        if argv[0] == "uv" and failure:
            path = Path(argv[argv.index("--record") + 1])
            record = json.loads(path.read_text())
            record["items"][0].update(state="failed", outputs=[], failure=failure)
            record["counts"] = {"failed": 1}
            path.write_text(json.dumps(record))
            return subprocess.CompletedProcess(argv, 1, b"", b"")
        return done

    monkeypatch.setattr(build, "run_tool", product)
    monkeypatch.setattr(build, "_view_video", lambda *a, **kw: None)
    assert build.main(["clips", "V-R", *args]) == 1
    rows = json.loads((roots.allowed / "records/pack.json").read_text())["items"]
    result = next(row for row in rows if row["item"] == "IMG_6772")
    assert result["status"] == ("failed" if failure else "done")
    assert result.get("expected_refusal_failed") is True
    assert result["message"] == (failure or "")
    assert build.main(["page", *args]) == 2
    assert "Expected HLG refusal" in (roots.allowed / "index.html").read_text()
    with (roots.allowed / "review-sheet.csv").open() as handle:
        assert list(csv.DictReader(handle)) == []


def test_missing_video_duration_type_error_is_caught_by_group_boundary(
    roots: OutputRoots,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An actual float(None) from _video must become a row and allow the next group."""
    first, later = _item("GX011604", "V-S", "video"), _item("IMG_6704", "V-R", "video")
    for item in (first, later):
        (roots.footage / item["source_name"]).write_bytes(b"planted")
    monkeypatch.setattr(build, "_probe", lambda *a: {"streams": [{"duration": None}]})
    monkeypatch.setattr(build, "run_tool", _fake_product)
    assert build.main(["clips", *_selection_args(roots, [first, later])]) == 1
    rows = json.loads((roots.allowed / "records/pack.json").read_text())["items"]
    by_item = {row["item"]: row for row in rows}
    assert by_item["GX011604"]["status"] == "failed"
    assert "NoneType" in by_item["GX011604"]["message"]
    assert by_item["IMG_6704"]["status"] == "refused"


@pytest.mark.parametrize("fault", ["zero_rate", "timeout"])
def test_zero_timecode_rate_or_runner_timeout_is_an_item_error_and_continues(
    request: pytest.FixtureRequest,
    roots: OutputRoots,
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
) -> None:
    """A zero-rate tmcd or raw subprocess timeout must not lose this or later groups."""
    if fault == "timeout":
        request.getfixturevalue("ffmpeg_tools")
    first, later = _item("GX011604", "V-S", "video"), _item("IMG_6704", "V-R", "video")
    for item in (first, later):
        shutil.copyfile(
            FIXTURES / "video/hevc8-bt709-full.mp4", roots.footage / item["source_name"]
        )
    if fault == "zero_rate":
        monkeypatch.setattr(build, "_video", lambda source: {"duration_s": 60.0})
        monkeypatch.setattr(
            build,
            "_probe",
            lambda *a: {
                "streams": [
                    {
                        "codec_type": "video",
                        "avg_frame_rate": "0/0",
                        "tags": {"timecode": "01:00:00:00"},
                    },
                    {"codec_type": "data", "codec_tag_string": "tmcd"},
                ]
            },
        )
        monkeypatch.setattr(
            build,
            "_packet_facts",
            lambda *a: [
                {"codec_type": "video", "flags": "K", "pts_time": "0"},
            ],
        )

    def product(argv, **kwargs):
        if fault == "timeout" and argv[0] == "uv" and any("GX011604" in arg for arg in argv):
            raise subprocess.TimeoutExpired(argv, 1)
        return _fake_product(argv, **kwargs)

    monkeypatch.setattr(build, "run_tool", product)
    assert build.main(["clips", *_selection_args(roots, [first, later])]) == 1
    rows = json.loads((roots.allowed / "records/pack.json").read_text())["items"]
    by_item = {row["item"]: row for row in rows}
    failed = by_item["GX011604"]
    assert failed["status"] == ("excerpt_failed" if fault == "zero_rate" else "failed")
    assert failed["message"] and str(roots.footage) not in failed["message"]
    assert by_item["IMG_6704"]["status"] == "refused"


def test_runner_records_append_fresh_snapshots_across_two_manifests(
    roots: OutputRoots,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raw product records remain byte-identical while targeted reruns append new records."""
    items = [_item(), _item("IMG_6771")]
    for item in items:
        shutil.copyfile(
            FIXTURES / "stills/jpeg/jpeg-gradient-srgb.jpg", roots.footage / item["source_name"]
        )
    monkeypatch.setattr(build, "run_tool", _fake_product)
    assert build.main(["photos", *_selection_args(roots, items)]) == 0
    records = roots.allowed / "records"
    before = {name: (records / name).read_bytes() for name in ("P-A.json", "P-A-neutral.json")}
    assert build.main(["photos", *_selection_args(roots, items[1:])]) == 0
    for name, data in before.items():
        assert (records / name).read_bytes() == data
        assert len(json.loads(data)["items"]) == 2
    for name in ("P-A-2.json", "P-A-neutral-2.json"):
        rows = json.loads((records / name).read_text())["items"]
        assert len(rows) == 1 and rows[0]["source"] == "IMG_6771.JPG"
    assert len(json.loads((records / "pack.json").read_text())["items"]) == 128


def test_stage_lock_releases_after_stage_exception(
    roots: OutputRoots,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The owning stage must remove its lock on an error as well as a normal return."""
    args = _selection_args(roots, [_item()])

    def fail(*a, **kw):
        assert (roots.allowed / ".reviewpack.lock").is_file()
        raise ValueError("planted stage failure")

    monkeypatch.setattr(build, "_build_groups", fail)
    assert build.main(["photos", *args]) == 2
    assert not (roots.allowed / ".reviewpack.lock").exists()
