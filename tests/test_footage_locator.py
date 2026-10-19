"""Tests of ``local_config.find_footage_file`` (WP-T2, the footage locator).

Every test builds a FAKE footage tree under pytest's ``tmp_path``; none reads the real
``clearwater.local.toml`` or names the real footage folder (``_fake_root`` asserts it).
The lettered tests follow the brief (``docs/briefs/wp-t2-brief.md``, claim 4).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

import inventory
import local_config
import statistics_experiments as runner
from local_config import FootageLookupError, find_footage_file

STEM = "GX011628"


def _fake_root(tmp_path: Path) -> Path:
    """Create and return an empty fake footage folder, proving it lies under ``tmp_path``."""
    root = tmp_path / "footage"
    root.mkdir()
    root.resolve().relative_to(tmp_path.resolve())
    return root


def _touch(root: Path, relative: str, data: bytes = b"x") -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _make_dir_link(link: Path, target: Path, kind: str) -> None:
    """Create a directory symlink or a Windows junction, or skip where the OS refuses."""
    if kind == "symlink":
        try:
            link.symlink_to(target, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            pytest.skip(f"this OS refuses to create a directory symlink here: {exc}")
        return
    if sys.platform != "win32":
        pytest.skip("junctions exist only on Windows")
    done = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(target)],
        capture_output=True,
        text=True,
        check=False,
    )
    if done.returncode != 0:
        pytest.skip(f"mklink /J was refused: {done.stdout.strip()} {done.stderr.strip()}")
    assert os.path.isjunction(link)


# --- (a) nested match -----------------------------------------------------------------------


def test_a_nested_match_is_found_from_the_root(tmp_path: Path) -> None:
    root = _fake_root(tmp_path)
    _touch(root, "Snorkel/GX011628.mp4")
    _touch(root, "Snorkel/GX011627.mp4")
    _touch(root, "SCUBA/deep/GX011629.mp4")
    assert find_footage_file(STEM, root) == root / "Snorkel" / "GX011628.mp4"
    assert find_footage_file("GX011629", root) == root / "SCUBA" / "deep" / "GX011629.mp4"


# --- (b) case -------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("stem", "name"),
    [("gx011628", "GX011628.MP4"), ("GX011628", "gx011628.mp4"), ("Gx011628", "gX011628.Mp4")],
)
def test_b_case_of_stem_and_suffix_does_not_matter(tmp_path: Path, stem: str, name: str) -> None:
    root = _fake_root(tmp_path)
    expected = _touch(root, f"edits/{name}")
    assert find_footage_file(stem, root) == expected


# --- (c) ambiguity --------------------------------------------------------------------------


def test_c_two_files_with_one_stem_are_an_error_naming_both(tmp_path: Path) -> None:
    root = _fake_root(tmp_path)
    _touch(root, "Snorkel/GX011628.mp4")
    _touch(root, "SCUBA/GX011628.MP4")
    with pytest.raises(FootageLookupError) as info:
        find_footage_file(STEM, root)
    assert len(info.value.matches) == 2
    assert info.value.matches == (
        root / "SCUBA" / "GX011628.MP4",
        root / "Snorkel" / "GX011628.mp4",
    )
    assert "SCUBA/GX011628.MP4" in str(info.value)
    assert "Snorkel/GX011628.mp4" in str(info.value)


def test_c_the_same_stem_with_two_extensions_is_ambiguous(tmp_path: Path) -> None:
    root = _fake_root(tmp_path)
    _touch(root, "GX011628.mp4")
    _touch(root, "GX011628.mov")
    with pytest.raises(FootageLookupError) as info:
        find_footage_file(STEM, root)
    assert len(info.value.matches) == 2


# --- (d) zero match -------------------------------------------------------------------------


def test_d_no_match_is_an_error_with_no_matches(tmp_path: Path) -> None:
    root = _fake_root(tmp_path)
    _touch(root, "Snorkel/GX011627.mp4")
    with pytest.raises(FootageLookupError) as info:
        find_footage_file(STEM, root)
    assert "not in the footage folder" in str(info.value)
    assert STEM in str(info.value) and str(root) in str(info.value)
    assert info.value.matches == ()
    assert isinstance(info.value, local_config.LocalConfigError)


# --- (e) sidecars ---------------------------------------------------------------------------

_SIDECARS = ("GL011628.LRV", "GX011628.LRV", "GX011628.THM", "GX011628.json", "GX011628.png")


def test_e_sidecars_are_ignored_beside_the_video(tmp_path: Path) -> None:
    root = _fake_root(tmp_path)
    video = _touch(root, "GX011628.mp4")
    for name in _SIDECARS:
        _touch(root, name)
    assert find_footage_file(STEM, root) == video


def test_e_sidecars_alone_are_no_match(tmp_path: Path) -> None:
    root = _fake_root(tmp_path)
    for name in _SIDECARS:
        _touch(root, name)
    with pytest.raises(FootageLookupError) as info:
        find_footage_file(STEM, root)
    assert info.value.matches == ()


# --- (f) prefixes and longer names ----------------------------------------------------------


def test_f_a_prefix_or_a_suffixed_stem_is_not_a_match(tmp_path: Path) -> None:
    root = _fake_root(tmp_path)
    _touch(root, "GX0116280.mp4")
    _touch(root, "GX011628_corrected.mp4")
    _touch(root, "XGX011628.mp4")
    with pytest.raises(FootageLookupError) as info:
        find_footage_file(STEM, root)
    assert info.value.matches == ()


def test_f_a_directory_named_like_a_video_is_not_a_match(tmp_path: Path) -> None:
    root = _fake_root(tmp_path)
    (root / "GX011628.mp4").mkdir()
    with pytest.raises(FootageLookupError) as info:
        find_footage_file(STEM, root)
    assert info.value.matches == ()
    real = _touch(root, "GX011628.mp4/inside/GX011628.mp4")
    assert find_footage_file(STEM, root) == real


# --- (g) never leaves the root --------------------------------------------------------------


@pytest.mark.parametrize("kind", ["symlink", "junction"])
def test_g_a_directory_link_out_of_the_root_is_not_followed(tmp_path: Path, kind: str) -> None:
    root = _fake_root(tmp_path)
    outside = tmp_path / "outside"
    _touch(outside, "GX011628.mp4")
    _make_dir_link(root / "linked", outside, kind)
    assert (root / "linked" / "GX011628.mp4").is_file()  # the link works...
    with pytest.raises(FootageLookupError) as info:
        find_footage_file(STEM, root)  # ...but the walk does not use it
    assert info.value.matches == ()


def test_g_a_file_symlink_named_like_a_video_is_not_a_match(tmp_path: Path) -> None:
    root = _fake_root(tmp_path)
    target = _touch(tmp_path / "outside", "real.mp4")
    try:
        (root / "GX011628.mp4").symlink_to(target)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"this OS refuses to create a file symlink here: {exc}")
    with pytest.raises(FootageLookupError) as info:
        find_footage_file(STEM, root)
    assert info.value.matches == ()


def test_g_a_real_file_beside_a_link_is_still_found(tmp_path: Path) -> None:
    root = _fake_root(tmp_path)
    outside = tmp_path / "outside"
    _touch(outside, "GX011628.mp4")
    _make_dir_link(root / "linked", outside, "symlink")
    real = _touch(root, "Snorkel/GX011628.mp4")
    assert find_footage_file(STEM, root) == real


# --- (h) bad stems --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "stem", ["", "a/b", "a\\b", "GX011628.MP4", "gx011628.mov", "x.360", "/GX011628"]
)
def test_h_a_stem_that_is_not_bare_is_refused(tmp_path: Path, stem: str) -> None:
    root = _fake_root(tmp_path)
    _touch(root, "GX011628.mp4")
    with pytest.raises(ValueError, match="stem"):
        find_footage_file(stem, root)


# --- (i) missing root -----------------------------------------------------------------------


def test_i_a_missing_root_is_a_lookup_error(tmp_path: Path) -> None:
    missing = tmp_path / "no-such-footage"
    with pytest.raises(FootageLookupError, match="no-such-footage") as info:
        find_footage_file(STEM, missing)
    assert info.value.matches == ()
    assert not missing.exists()


def test_i_a_root_that_is_a_file_is_a_lookup_error(tmp_path: Path) -> None:
    file_root = _touch(tmp_path, "footage.txt")
    with pytest.raises(FootageLookupError, match=r"footage\.txt") as info:
        find_footage_file(STEM, file_root)
    assert info.value.matches == ()


# --- (j) read-only --------------------------------------------------------------------------


def _snapshot(root: Path) -> dict[str, bytes | None]:
    """Every entry under ``root`` (relative, sorted): file bytes, or None for a folder."""
    state: dict[str, bytes | None] = {}
    for path in sorted(root.rglob("*")):
        state[path.relative_to(root).as_posix()] = path.read_bytes() if path.is_file() else None
    return state


def test_j_lookups_neither_write_nor_change_the_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fake_root(tmp_path)
    _touch(root, "Snorkel/GX011628.mp4", b"one")
    _touch(root, "SCUBA/GX011630.MP4", b"two")
    _touch(root, "SCUBA/GX011630.mov", b"three")
    _touch(root, "GX011628.LRV", b"four")
    (root / "empty").mkdir()
    before = _snapshot(root)
    work = tmp_path / "cwd"
    work.mkdir()
    monkeypatch.chdir(work)
    find_footage_file(STEM, root)
    find_footage_file("gx011628", root)
    for stem in ("GX011630", "NOPE"):
        with pytest.raises(FootageLookupError):
            find_footage_file(stem, root)
    with pytest.raises(ValueError, match="stem"):
        find_footage_file("a/b", root)
    assert _snapshot(root) == before
    assert list(work.iterdir()) == []
    assert Path.cwd().samefile(work)
    assert sorted(entry.name for entry in tmp_path.iterdir()) == ["cwd", "footage"]


# --- (k) one definition ---------------------------------------------------------------------


def test_k_video_extensions_has_one_definition() -> None:
    assert inventory.VIDEO_EXTENSIONS is local_config.VIDEO_EXTENSIONS
    assert frozenset({".mp4", ".mov", ".360"}) == local_config.VIDEO_EXTENSIONS


# --- (l) the WP1.4 runner refuses before it writes ------------------------------------------


def _fake_config(tmp_path: Path, root: Path) -> tuple[Path, Path]:
    work = tmp_path / "work"
    work.mkdir()
    config = tmp_path / "clearwater.local.toml"
    config.write_text(
        f"footage_path = '{root}'\nworking_path = '{work}'\n",
        encoding="utf-8",
    )
    return config, work


@pytest.mark.parametrize(
    ("phase", "present", "missing"),
    [
        ("extract", "GX011627", "GX011625"),
        ("extract", "GX011625", "GX011627"),
        ("render", "GX011625", "GX011627"),
    ],
)
def test_l_the_runner_refuses_a_missing_chapter_before_writing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    phase: str,
    present: str,
    missing: str,
) -> None:
    root = _fake_root(tmp_path)
    _touch(root, f"Snorkel/{present}.mp4")
    config, work = _fake_config(tmp_path, root)

    def must_not_run(*args: object, **kwargs: object) -> None:
        raise AssertionError("a phase ran although a chapter is missing")

    monkeypatch.setattr(runner, "extract_excerpt", must_not_run)
    monkeypatch.setattr(runner, "render_clips", must_not_run)
    before = _snapshot(root)
    code = runner.main([phase, "--config", str(config), "--device", "cpu"])
    err = capsys.readouterr().err
    assert code == 2
    assert f"{missing} is not in the footage folder" in err
    assert err.startswith("error: ")
    assert list(work.iterdir()) == []  # nothing, not even work/wp1.4
    assert _snapshot(root) == before


def test_l_the_runner_refuses_an_ambiguous_chapter(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _fake_root(tmp_path)
    _touch(root, "Snorkel/GX011627.mp4")
    _touch(root, "SCUBA/GX011627.MP4")
    _touch(root, "Snorkel/GX011625.mp4")
    config, work = _fake_config(tmp_path, root)
    code = runner.main(["extract", "--config", str(config), "--device", "cpu"])
    err = capsys.readouterr().err
    assert code == 2
    assert "GX011627 matches 2 files" in err
    assert list(work.iterdir()) == []
