"""WP3.13 tests: output naming (spec 8.3; D34, D35, D36, D84)."""

from __future__ import annotations

import json
import os
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
    assert out.name == "clip_corrected.mp4"


def test_mp4_extension_case_is_preserved() -> None:
    out = final_output_path(Path("clip.Mp4"), Settings(), MediaKind.VIDEO)
    assert out.name == "clip_corrected.Mp4"


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


def test_final_name_that_looks_temporary_moves_to_the_next_number(tmp_path: Path) -> None:
    source = _touch(tmp_path / "x.clearwater-partial-0123456789ab.HEIC")
    plan = plan_output(source, Settings(output_suffix=""), MediaKind.PHOTO)
    assert plan.path.name == "x.clearwater-partial-0123456789ab_2.png"
    assert not is_temporary_name(plan.path.name)
    out = final_output_path(source, Settings(output_suffix=""), MediaKind.PHOTO)
    assert out == plan.path


def test_stem_and_suffix_that_spell_a_temporary_are_never_returned(tmp_path: Path) -> None:
    # Round 3: each part is valid alone; together they spell a temporary name.
    source = _touch(tmp_path / "holiday.clearwater.HEIC")
    settings = Settings(output_suffix="-partial-0123456789ab")
    validate_suffix(settings.output_suffix)
    assert is_temporary_name("holiday.clearwater-partial-0123456789ab.png")
    expected = tmp_path / "holiday.clearwater-partial-0123456789ab_2.png"
    out = final_output_path(source, settings, MediaKind.PHOTO)
    assert out == expected
    assert not is_temporary_name(out.name)
    plan = plan_output(source, settings, MediaKind.PHOTO)
    assert plan.path == expected
    assert not is_temporary_name(plan.path.name)


@pytest.mark.parametrize("number", range(2, 40))
def test_numbered_names_never_match_the_temporary_pattern(number: int) -> None:
    plan = OutputPlan(
        Path("s.HEIC"), Path("."), "holiday.clearwater-partial-0123456789ab", ".png", number
    )
    assert not is_temporary_name(plan.path.name)


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


def _directory_alias(target: Path, alias: Path) -> bool:
    """Make ``alias`` another name for the folder ``target``; False if the volume cannot."""
    try:
        alias.symlink_to(target, target_is_directory=True)
        return True
    except (OSError, NotImplementedError):
        pass
    if sys.platform == "win32":
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(alias), str(target)], capture_output=True, check=False
        )
        return result.returncode == 0 and alias.exists()
    return False


def test_final_output_path_is_never_the_source_through_a_folder_alias(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    source = _touch(real / "GX010123.MP4", b"src")
    alias = tmp_path / "alias"
    if not _directory_alias(real, alias):
        pytest.skip("this volume can make neither a directory symlink nor a junction")
    settings = Settings(output_suffix="", output_folder=alias)
    out = final_output_path(source, settings, MediaKind.VIDEO)
    assert out == alias / "GX010123_2.MP4"
    assert plan_output(source, settings, MediaKind.VIDEO).path == alias / "GX010123_2.MP4"
    assert source.read_bytes() == b"src"


# --- WP4.2b: composed output names stay portable components (DR-80) ---------------------------


@pytest.mark.parametrize("planner", [final_output_path, _real], ids=["final", "plan"])
@pytest.mark.parametrize("kind", [MediaKind.PHOTO, MediaKind.VIDEO], ids=["photo", "video"])
@pytest.mark.parametrize("name", ["c:x.jpg", "carrier:x.jpg"])
def test_composed_output_name_is_refused(tmp_path, planner, kind, name):
    """Refuse drive-relative and stream output names without exposing their folders."""
    source = Path(f"{tmp_path}{os.sep}{name}")
    assert source.name == name
    settings = Settings(output_folder=tmp_path / "out")

    with pytest.raises(ValueError) as error:
        planner(source, settings, kind)

    assert isinstance(error.value, clearwater.jobs.OutputNameError)
    text = str(error.value)
    assert name in text
    assert str(tmp_path) not in text
    assert str(settings.output_folder) not in text


@pytest.mark.parametrize("planner", [final_output_path, _real], ids=["final", "plan"])
def test_video_extension_stream_is_refused(tmp_path, planner):
    """Check the retained video extension as part of the composed name."""
    source = Path(f"{tmp_path}{os.sep}x.mp4:s")
    assert source.name == "x.mp4:s"
    settings = Settings(output_folder=tmp_path / "out")

    with pytest.raises(ValueError) as error:
        planner(source, settings, MediaKind.VIDEO)

    assert isinstance(error.value, clearwater.jobs.OutputNameError)
    text = str(error.value)
    assert source.name in text
    assert str(tmp_path) not in text
    assert str(settings.output_folder) not in text


@pytest.mark.parametrize("planner", [final_output_path, _real], ids=["final", "plan"])
@pytest.mark.parametrize("kind", [MediaKind.PHOTO, MediaKind.VIDEO], ids=["photo", "video"])
@pytest.mark.parametrize("beside", [False, True], ids=["out", "beside"])
@pytest.mark.parametrize(
    "fixture_path",
    [
        entry["path"]
        for entry in json.loads(
            (Path(__file__).parent / "fixtures" / "manifest.json").read_text(encoding="utf-8")
        )["samples"]
    ],
)
def test_wp23_fixture_names_keep_output_paths(tmp_path, planner, kind, beside, fixture_path):
    """Keep every manifest filename's default-suffix path unchanged."""
    source = tmp_path / "source" / fixture_path
    folder = source.parent if beside else tmp_path / "out"
    settings = Settings(output_folder=None if beside else folder)
    extension = ".png" if kind is MediaKind.PHOTO else source.suffix
    expected = folder / f"{source.stem}_corrected{extension}"

    assert planner(source, settings, kind) == expected


# --- WP4.4 QuickTime sources produce MP4 (spec 8.3, 0.5.7) -------------------------------


@pytest.mark.parametrize("planner", [final_output_path, _real], ids=["final", "plan"])
@pytest.mark.parametrize("name", ["IMG_6702.MOV", "x.mov", "x.Mov"])
@pytest.mark.parametrize("suffix", ["_corrected", "_fixed", ""], ids=["default", "edited", "empty"])
@pytest.mark.parametrize("beside", [False, True], ids=["out", "beside"])
def test_mov_output_extension(tmp_path, planner, name, suffix, beside):
    source = tmp_path / name
    folder = tmp_path if beside else tmp_path / "out"
    settings = Settings(output_folder=None if beside else folder, output_suffix=suffix)
    assert planner(source, settings, MediaKind.VIDEO) == folder / f"{source.stem}{suffix}.mp4"


def test_mov_and_mp4_share_collision_sequence(tmp_path: Path) -> None:
    reservations = Reservations()
    settings = Settings(output_folder=tmp_path)
    mov = plan_output(tmp_path / "IMG_1.MOV", settings, MediaKind.VIDEO, reservations)
    mp4 = plan_output(tmp_path / "IMG_1.mp4", settings, MediaKind.VIDEO, reservations)
    assert mov.path == tmp_path / "IMG_1_corrected.mp4"
    assert mp4.path == tmp_path / "IMG_1_corrected_2.mp4"


@pytest.mark.parametrize("temporary", [False, True], ids=["final", "temporary"])
def test_mov_collision_uses_mapped_extension(tmp_path: Path, temporary: bool) -> None:
    taken = tmp_path / (
        "IMG_1_corrected.clearwater-partial-0123456789ab.mp4"
        if temporary
        else "IMG_1_corrected.mp4"
    )
    taken.write_bytes(b"occupied")
    output = plan_output(tmp_path / "IMG_1.MOV", Settings(), MediaKind.VIDEO)
    assert output.path == tmp_path / "IMG_1_corrected_2.mp4"
    assert taken.read_bytes() == b"occupied"


@pytest.mark.parametrize("planner", [final_output_path, _real], ids=["final", "plan"])
def test_mov_temporary_path_uses_mp4(tmp_path, planner):
    final = planner(tmp_path / "IMG_6702.MOV", Settings(), MediaKind.VIDEO)
    temporary = temporary_path(final, "0123456789ab")
    assert temporary.name == "IMG_6702_corrected.clearwater-partial-0123456789ab.mp4"


@pytest.mark.parametrize("planner", [final_output_path, _real], ids=["final", "plan"])
def test_mov_extension_stream_is_refused(tmp_path, planner):
    source = tmp_path / "x.mov:s"
    with pytest.raises(clearwater.jobs.OutputNameError):
        planner(source, Settings(output_folder=tmp_path / "out"), MediaKind.VIDEO)


@pytest.mark.parametrize(
    ("first", "second", "expected_first", "expected_second"),
    [
        ("IMG_1.MOV", "IMG_1.MP4", "IMG_1_corrected.mp4", "IMG_1_corrected_2.MP4"),
        ("IMG_1.MP4", "IMG_1.MOV", "IMG_1_corrected.MP4", "IMG_1_corrected_2.mp4"),
    ],
    ids=["mov-first", "mp4-first"],
)
def test_mov_and_uppercase_mp4_share_run_registry(
    tmp_path: Path, first: str, second: str, expected_first: str, expected_second: str
) -> None:
    """Number suffix-case collisions in either order using one run registry."""
    reservations = Reservations()
    settings = Settings(output_folder=tmp_path)
    one = plan_output(tmp_path / first, settings, MediaKind.VIDEO, reservations)
    two = plan_output(tmp_path / second, settings, MediaKind.VIDEO, reservations)
    assert one.path == tmp_path / expected_first
    assert two.path == tmp_path / expected_second


@pytest.mark.parametrize("temporary", [False, True], ids=["final", "temporary"])
def test_mov_collision_with_uppercase_mp4_on_disk(tmp_path: Path, temporary: bool) -> None:
    """Keep an existing uppercase MP4 final or partial intact and choose _2.mp4."""
    final = tmp_path / "IMG_2_corrected.MP4"
    taken = temporary_path(final, "0123456789ab") if temporary else final
    taken.write_bytes(b"occupied")
    output = plan_output(tmp_path / "IMG_2.MOV", Settings(), MediaKind.VIDEO, Reservations())
    assert output.path == tmp_path / "IMG_2_corrected_2.mp4"
    assert taken.read_bytes() == b"occupied"
