"""WP3.13 tests: output naming (spec 8.3; D34, D35, D36, D84)."""

from __future__ import annotations

import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

import clearwater.jobs
from clearwater.interfaces.settings import Settings
from clearwater.jobs import (
    MediaKind,
    OutputPlan,
    Reservations,
    final_output_path,
    is_temporary_name,
    new_token,
    plan_output,
    scan_temporaries,
    temporaries_of,
    temporary_path,
    validate_suffix,
)

Planner = Callable[[Path, Settings, MediaKind], Path]


def _touch(path: Path, data: bytes = b"x") -> Path:
    path.write_bytes(data)
    return path


def _case_insensitive(folder: Path) -> bool:
    probe = _touch(folder / "CaseProbe.tmp")
    try:
        return (folder / "caseprobe.tmp").exists()
    finally:
        probe.unlink()


def _real(source: Path, settings: Settings, kind: MediaKind) -> Path:
    return plan_output(source, settings, kind).path


# --- 8.3 examples, literally ---------------------------------------------------------------


def test_example_video_keeps_extension() -> None:
    out = final_output_path(Path("GX010123.MP4"), Settings(), MediaKind.VIDEO)
    assert out.name == "GX010123_corrected.MP4"


def test_example_photo_becomes_png() -> None:
    out = final_output_path(Path("IMG_1234.HEIC"), Settings(), MediaKind.PHOTO)
    assert out.name == "IMG_1234_corrected.png"


def test_video_extension_case_is_preserved() -> None:
    out = final_output_path(Path("clip.mov"), Settings(), MediaKind.VIDEO)
    assert out.name == "clip_corrected.mov"


def test_same_folder_as_source_by_default(tmp_path: Path) -> None:
    out = final_output_path(tmp_path / "a" / "GX010123.MP4", Settings(), MediaKind.VIDEO)
    assert out.parent == tmp_path / "a"


def test_output_folder_setting(tmp_path: Path) -> None:
    settings = Settings(output_folder=tmp_path / "out")
    out = final_output_path(tmp_path / "in" / "IMG_1.HEIC", settings, MediaKind.PHOTO)
    assert out == tmp_path / "out" / "IMG_1_corrected.png"


def test_edited_suffix() -> None:
    out = final_output_path(Path("v.MP4"), Settings(output_suffix="_fixed"), MediaKind.VIDEO)
    assert out.name == "v_fixed.MP4"


def test_empty_suffix_never_yields_the_source(tmp_path: Path) -> None:
    source = _touch(tmp_path / "GX010123.MP4", b"src")
    plan = plan_output(source, Settings(output_suffix=""), MediaKind.VIDEO)
    assert plan.path == tmp_path / "GX010123_2.MP4"
    assert plan.path != source


def test_empty_suffix_missing_source_still_not_the_source(tmp_path: Path) -> None:
    source = tmp_path / "GX010123.MP4"  # does not exist on disk
    plan = plan_output(source, Settings(output_suffix=""), MediaKind.VIDEO)
    assert plan.path != source


def test_empty_suffix_photo_in_other_extension_keeps_plain_name(tmp_path: Path) -> None:
    source = _touch(tmp_path / "IMG_1.HEIC")
    plan = plan_output(source, Settings(output_suffix=""), MediaKind.PHOTO)
    assert plan.path == tmp_path / "IMG_1.png"


# --- collision numbering (D35, D84) ---------------------------------------------------------


def check_numbering(planner: Planner, folder: Path) -> None:
    """Shared check: the first numbered name is _2, then _3."""
    source = _touch(folder / "GX010123.MP4")
    settings = Settings()
    first = planner(source, settings, MediaKind.VIDEO)
    assert first.name == "GX010123_corrected.MP4"
    _touch(first)
    second = planner(source, settings, MediaKind.VIDEO)
    assert second.name == "GX010123_corrected_2.MP4"
    _touch(second)
    assert planner(source, settings, MediaKind.VIDEO).name == "GX010123_corrected_3.MP4"


def test_collisions_one_to_n(tmp_path: Path) -> None:
    check_numbering(_real, tmp_path)


def test_collisions_many(tmp_path: Path) -> None:
    source = _touch(tmp_path / "IMG_1.HEIC")
    settings = Settings()
    names = []
    for _ in range(12):
        path = plan_output(source, settings, MediaKind.PHOTO).path
        names.append(path.name)
        _touch(path)
    assert names[0] == "IMG_1_corrected.png"
    assert names[1:] == [f"IMG_1_corrected_{n}.png" for n in range(2, 13)]


def test_planted_numbering_from_one_fails_by_name(tmp_path: Path) -> None:
    def from_one(source: Path, settings: Settings, kind: MediaKind) -> Path:
        base = source.stem + settings.output_suffix
        path = source.parent / (base + source.suffix)
        n = 0
        while path.exists():
            n += 1
            path = source.parent / f"{base}_{n}{source.suffix}"
        return path

    with pytest.raises(AssertionError):
        check_numbering(from_one, tmp_path)


def test_cross_format_photo_clash(tmp_path: Path) -> None:
    heic = _touch(tmp_path / "IMG_1234.HEIC")
    jpg = _touch(tmp_path / "IMG_1234.JPG")
    reservations = Reservations()
    first = plan_output(heic, Settings(), MediaKind.PHOTO, reservations)
    second = plan_output(jpg, Settings(), MediaKind.PHOTO, reservations)
    assert first.path.name == "IMG_1234_corrected.png"
    assert second.path.name == "IMG_1234_corrected_2.png"


def test_cross_format_clash_against_disk_without_registry(tmp_path: Path) -> None:
    heic = _touch(tmp_path / "IMG_1234.HEIC")
    jpg = _touch(tmp_path / "IMG_1234.JPG")
    _touch(plan_output(heic, Settings(), MediaKind.PHOTO).path)
    assert plan_output(jpg, Settings(), MediaKind.PHOTO).path.name == "IMG_1234_corrected_2.png"


def _case_clash(planner: Planner, folder: Path) -> None:
    """Shared check: a case-variant name on disk is a clash decided by the filesystem."""
    _touch(folder / "img_1234_corrected.PNG")
    source = _touch(folder / "IMG_1234.HEIC")
    got = planner(source, Settings(), MediaKind.PHOTO)
    assert got.name == "IMG_1234_corrected_2.png"


def test_case_insensitive_clash(tmp_path: Path) -> None:
    if not _case_insensitive(tmp_path):
        pytest.skip("case-sensitive volume: no case-insensitive clash to detect")
    _case_clash(_real, tmp_path)


def test_planted_string_compare_collision_fails_by_name(tmp_path: Path) -> None:
    if not _case_insensitive(tmp_path):
        pytest.skip("case-sensitive volume: string compare cannot be told from the filesystem")

    def string_compare(source: Path, settings: Settings, kind: MediaKind) -> Path:
        plan = OutputPlan(source, source.parent, source.stem + settings.output_suffix, ".png")
        names = {p.name for p in source.parent.iterdir()}
        while plan.path.name in names:
            plan = plan.numbered(plan.number + 1)
        return plan.path

    with pytest.raises(AssertionError):
        _case_clash(string_compare, tmp_path)


# --- reservations and temporaries -----------------------------------------------------------


def test_in_run_reservations_count_as_taken(tmp_path: Path) -> None:
    source = _touch(tmp_path / "GX010123.MP4")
    reservations = Reservations()
    paths = [plan_output(source, Settings(), MediaKind.VIDEO, reservations).path for _ in range(3)]
    assert [p.name for p in paths] == [
        "GX010123_corrected.MP4",
        "GX010123_corrected_2.MP4",
        "GX010123_corrected_3.MP4",
    ]
    assert len(reservations) == 3
    assert all(p in reservations for p in paths)


def test_reservations_compare_case_folded(tmp_path: Path) -> None:
    reservations = Reservations()
    assert reservations.try_reserve(tmp_path / "A_corrected.png")
    assert not reservations.try_reserve(tmp_path / "a_CORRECTED.PNG")


def test_release_only_by_the_exact_holder(tmp_path: Path) -> None:
    reservations = Reservations()
    assert reservations.try_reserve(tmp_path / "A.png")
    reservations.release(tmp_path / "a.png")  # equal key, not the same path
    assert (tmp_path / "A.png") in reservations
    reservations.release(tmp_path / "A.png")
    assert len(reservations) == 0


def test_without_registry_nothing_is_reserved(tmp_path: Path) -> None:
    source = _touch(tmp_path / "GX010123.MP4")
    a = plan_output(source, Settings(), MediaKind.VIDEO)
    b = plan_output(source, Settings(), MediaKind.VIDEO)
    assert a.path == b.path


def test_other_jobs_temporary_counts_as_taken(tmp_path: Path) -> None:
    source = _touch(tmp_path / "GX010123.MP4")
    stale = _touch(tmp_path / "GX010123_corrected.clearwater-partial-0123456789ab.MP4")
    plan = plan_output(source, Settings(), MediaKind.VIDEO)
    assert plan.path.name == "GX010123_corrected_2.MP4"
    assert stale.exists()


def test_dangling_symlink_counts_as_taken(tmp_path: Path) -> None:
    source = _touch(tmp_path / "GX010123.MP4")
    link = tmp_path / "GX010123_corrected.MP4"
    try:
        link.symlink_to(tmp_path / "nowhere")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not available")
    assert plan_output(source, Settings(), MediaKind.VIDEO).path.name == "GX010123_corrected_2.MP4"


# --- temporary-name pattern -----------------------------------------------------------------


def test_temporary_path_pattern() -> None:
    final = Path("D:/out/GX010123_corrected.MP4")
    assert temporary_path(final, "0123456789ab").name == (
        "GX010123_corrected.clearwater-partial-0123456789ab.MP4"
    )
    assert temporary_path(Path("IMG_1_corrected_2.png"), "fedcba987654").name == (
        "IMG_1_corrected_2.clearwater-partial-fedcba987654.png"
    )


def test_tokens_are_random_hex() -> None:
    tokens = {new_token() for _ in range(50)}
    assert len(tokens) == 50
    assert all(re.fullmatch(r"[0-9a-f]{12}", t) for t in tokens)


@pytest.mark.parametrize(
    "name",
    [
        "GX010123_corrected.clearwater-partial-0123456789ab.MP4",
        "IMG_1_corrected.clearwater-partial-0123456789ab.png",
        "clip.CLEARWATER-PARTIAL-0123456789AB.mp4",
        "noext.clearwater-partial-0123456789ab",
    ],
)
def test_temporary_names_match(name: str) -> None:
    assert is_temporary_name(name)


@pytest.mark.parametrize(
    "name",
    [
        "GX010123.MP4",
        "GX010123.LRV",
        "GX010123.THM",
        "GOPR0001.JPG",
        "IMG_1234.HEIC",
        "IMG_1234_corrected.png",
        "IMG_1234_corrected_2.png",
        ".clearwater-partial-0123456789ab",
        "a.clearwater-partial-0123456789ab.b.MP4",
        "a.clearwater-partial_corrected.MP4",
        "a.clearwater-partialx.MP4",
        "holiday.clearwater-partial.png",
        "holiday.clearwater-partial-.png",
        "holiday.clearwater-partial-0123456789a.png",
        "holiday.clearwater-partial-0123456789abc.png",
        "holiday.clearwater-partial-0123456789ag.png",
        "",
    ],
)
def test_other_names_do_not_match(name: str) -> None:
    assert not is_temporary_name(name)


def test_final_name_that_looks_temporary_is_refused(tmp_path: Path) -> None:
    source = _touch(tmp_path / "x.clearwater-partial-0123456789ab.HEIC")
    with pytest.raises(ValueError, match="temporary"):
        plan_output(source, Settings(output_suffix=""), MediaKind.PHOTO)


@pytest.mark.parametrize(
    "suffix",
    ["/x", "a\\b", "a:b", "a*", "a?", 'a"', "a<", "a>", "a|", "a\x00", "a\n", "..", "x..y", "x.",
     "x ", "_corrected.clearwater-partial", "_x.CLEARWATER-Partial"],
)  # fmt: skip
def test_bad_suffix_is_refused(suffix: str) -> None:
    with pytest.raises(ValueError, match="suffix"):
        validate_suffix(suffix)
    with pytest.raises(ValueError, match="suffix"):
        final_output_path(Path("a.MP4"), Settings(output_suffix=suffix), MediaKind.VIDEO)


@pytest.mark.parametrize("suffix", ["", "_corrected", "-v2", "_fixed 1", ".fixed"])
def test_good_suffix_is_accepted(suffix: str) -> None:
    validate_suffix(suffix)


def test_numbered_rejects_zero() -> None:
    plan = OutputPlan(Path("a.MP4"), Path("."), "a_corrected", ".MP4")
    with pytest.raises(ValueError):
        plan.numbered(0)


# --- the module does not touch the source or write -------------------------------------------


def test_planning_writes_nothing_and_leaves_source_alone(tmp_path: Path) -> None:
    source = _touch(tmp_path / "GX010123.MP4", b"payload")
    before = (source.read_bytes(), source.stat().st_mtime_ns)
    for _ in range(3):
        plan_output(source, Settings(), MediaKind.VIDEO)
    assert (source.read_bytes(), source.stat().st_mtime_ns) == before
    assert [p.name for p in tmp_path.iterdir()] == ["GX010123.MP4"]


# --- dependency rule (plan 8.1, frame rule 5) --------------------------------------------------


def test_importing_jobs_loads_no_gui_methods_or_heavy_libraries() -> None:
    src = str(Path(clearwater.jobs.__file__).resolve().parents[2])
    code = (
        "import sys; sys.path.insert(0, sys.argv[1]); import clearwater.jobs; "
        "bad = sorted(m for m in sys.modules if m.split('.')[0] in ('PySide6', 'cupy') "
        "or m.startswith(('clearwater.gui', 'clearwater.methods'))); "
        "print('BAD', bad)"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", code, src], capture_output=True, text=True, check=True
    )
    assert result.stdout.strip() == "BAD []"


# --- round 1 findings -------------------------------------------------------------------------


def test_final_output_path_is_never_the_source_for_an_empty_suffix(tmp_path: Path) -> None:
    source = tmp_path / "GX010123.MP4"
    out = final_output_path(source, Settings(output_suffix=""), MediaKind.VIDEO)
    assert out != source
    assert out == tmp_path / "GX010123_2.MP4"
    # The output folder spelled with different case is still the source's folder.
    shouted = Settings(output_suffix="", output_folder=Path(str(tmp_path).upper()))
    assert final_output_path(source, shouted, MediaKind.VIDEO) == shouted.output_folder / (
        "GX010123_2.MP4"
    )
    elsewhere = Settings(output_suffix="", output_folder=tmp_path / "out")
    assert (
        final_output_path(source, elsewhere, MediaKind.VIDEO) == tmp_path / "out" / "GX010123.MP4"
    )


def test_user_file_with_the_old_marker_form_is_not_a_temporary(tmp_path: Path) -> None:
    user = _touch(tmp_path / "holiday.clearwater-partial.png")
    assert not is_temporary_name(user.name)
    assert scan_temporaries(tmp_path) == {}


def test_scan_groups_temporaries_by_final_name_case_insensitively(tmp_path: Path) -> None:
    a = _touch(tmp_path / "IMG_1_corrected.clearwater-partial-0123456789ab.png")
    b = _touch(tmp_path / "img_1_CORRECTED.clearwater-partial-FEDCBA987654.PNG")
    c = _touch(tmp_path / "IMG_1_corrected_2.clearwater-partial-0123456789ab.png")
    _touch(tmp_path / "IMG_1_corrected.png")
    found = scan_temporaries(tmp_path)
    assert sorted(found) == ["img_1_corrected.png", "img_1_corrected_2.png"]
    assert sorted(found["img_1_corrected.png"]) == sorted([a, b])
    assert temporaries_of(tmp_path / "IMG_1_corrected.png") == found["img_1_corrected.png"]
    assert temporaries_of(tmp_path / "IMG_1_corrected_2.png") == [c]
    assert temporaries_of(tmp_path / "IMG_1_corrected_3.png") == []
    assert scan_temporaries(tmp_path / "missing") == {}


def test_planning_skips_a_name_whatever_the_tokens_of_its_temporaries(tmp_path: Path) -> None:
    source = _touch(tmp_path / "IMG_1.HEIC")
    _touch(tmp_path / "IMG_1_corrected.clearwater-partial-aaaaaaaaaaaa.png")
    _touch(tmp_path / "IMG_1_corrected_2.clearwater-partial-bbbbbbbbbbbb.png")
    assert plan_output(source, Settings(), MediaKind.PHOTO).path.name == "IMG_1_corrected_3.png"
