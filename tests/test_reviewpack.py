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
import shutil
import subprocess
import sys
from collections import Counter
from fractions import Fraction
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


def test_failed_stream_copy_falls_back_to_whole_source(
    roots: OutputRoots, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only the external copy fails; probe and fallback accounting stay real."""
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
    assert prepared["path"] == source
    assert prepared["excerpt"] is False
    assert "stream copy" in prepared["message"].lower()
    assert source.read_bytes() == original


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


def test_tally_empty_sheet_is_zero_judged_without_verdict(roots: OutputRoots) -> None:
    path = roots.allowed / "empty.csv"
    _csv(path, [_row(_item())])
    result = sheet.tally(path)
    assert result["headline"]["judged"] == result["headline"]["preferred"] == 0
    text = sheet.format_tally(result)
    assert "headline: 0/0 = 0.0 %  (D65 bar 80 %)" in text
    assert not any(word in text.lower() for word in ("pass", "fail", "approved", "rejected"))


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
        _csv(path, [], header=HEADER[:-1])
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


@pytest.mark.slow(reason="runs the headless runner and FFmpeg")
def test_all_tiny_set(roots: OutputRoots) -> None:
    """Exercise all stages end to end while recording source byte immutability."""
    inputs = [
        (FIXTURES / "stills" / "jpeg" / "jpeg-gradient-srgb.jpg", "IMG_6751.JPG", "P-A"),
        (FIXTURES / "stills" / "jpeg" / "jpeg-lowred-srgb.jpg", "IMG_6791.JPG", "P-Z"),
        (FIXTURES / "video" / "hevc8-bt709-full.mp4", "GX011604.mp4", "V-S"),
    ]
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
        == 0
    )
    assert page.check_links(roots.allowed / "index.html", roots=roots) == []
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
    video = next(item for item in state["items"] if item["kind"] == "video")
    assert [still["fraction"] for still in video["stills"]] == [0.1, 0.5, 0.9]
    assert all(still["source_pts_s"] == still["corrected_pts_s"] for still in video["stills"])
    tally = sheet.tally(roots.allowed / "review-sheet.csv")
    assert tally["headline"]["judged"] == tally["candidates"]["judged"] == 0
    with (roots.allowed / "review-sheet.csv").open(encoding="utf-8", newline="") as handle:
        assert len(list(csv.DictReader(handle))) == 3
    assert before == {name: (roots.footage / name).read_bytes() for _, name, _ in inputs}


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


def test_stream_copy_success_records_a_matched_source_packet(roots: OutputRoots) -> None:
    """Check the real copy/probe join rather than only a planted packet mapping."""
    source = FIXTURES / "video" / "hevc8-bt709-full.mp4"
    prepared = build.prepare_excerpt(source, start_s=0.6, duration_s=1.0, roots=roots)
    assert prepared["excerpt"] is True
    assert prepared["planned_start_s"] == 0.6
    assert 0.0 <= prepared["actual_start_s"] <= 0.6
    assert prepared["duration_s"] > 0
    assert prepared["path"].is_relative_to(roots.allowed / "excerpts")


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
    assert build.main(["page", *args]) == 0
    state = json.loads((roots.allowed / "records" / "pack.json").read_text())
    assert len(state["items"]) == 1
    assert state["items"][0]["status"] == "refused"
    assert "hlg" in state["items"][0]["message"].lower()
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
    original = OutputRoots.write_text

    def interrupted(self, target, text):
        original(self, target, "partial")
        raise OSError("planted write interruption")

    monkeypatch.setattr(OutputRoots, "write_text", interrupted)
    with pytest.raises(OSError, match="planted"):
        sheet.write_sheet([_item(), _item("IMG_6791", "P-Z")], destination, roots=roots)
    assert destination.read_bytes() == before
