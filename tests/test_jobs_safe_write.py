"""WP3.13 tests: safe writing and leftover clean-up (spec 8.4; D44, D85, D87)."""

from __future__ import annotations

import errno
import os
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

from clearwater.interfaces.settings import Settings
from clearwater.jobs import (
    LeftoverReport,
    MediaKind,
    MissingFolderError,
    OutputPlan,
    Reservations,
    SafeWrite,
    SafeWriteError,
    SafeWriteState,
    is_disk_full,
    plan_output,
    remove_leftovers,
    temporary_path,
)
from clearwater.jobs import safe_write as sw

SOURCE_BYTES = b"SOURCE-VIDEO-BYTES"


class CancelledError(Exception):
    """Stands for a user cancel raised inside the write block."""


@pytest.fixture
def source(tmp_path: Path) -> Iterator[Path]:
    """A source video whose bytes and mtime must be identical after every scenario."""
    path = tmp_path / "GX010123.MP4"
    path.write_bytes(SOURCE_BYTES)
    before = (path.read_bytes(), path.stat().st_mtime_ns, path.stat().st_size)
    yield path
    after = (path.read_bytes(), path.stat().st_mtime_ns, path.stat().st_size)
    assert after == before, "the source file was modified"


def _plan(source: Path, reservations: Reservations | None = None) -> OutputPlan:
    return plan_output(source, Settings(), MediaKind.VIDEO, reservations)


def _names(folder: Path) -> list[str]:
    return sorted(p.name for p in folder.iterdir())


# --- the happy path --------------------------------------------------------------------------


def test_commit_renames_temporary_to_final(source: Path) -> None:
    plan = _plan(source)
    with SafeWrite(plan) as write:
        assert write.temp_path.parent == source.parent
        assert write.temp_path.name == "GX010123_corrected.clearwater-partial.MP4"
        assert write.temp_path.exists()
        write.temp_path.write_bytes(b"OUT")
        final = write.commit()
    assert final == source.parent / "GX010123_corrected.MP4"
    assert final.read_bytes() == b"OUT"
    assert _names(source.parent) == ["GX010123.MP4", "GX010123_corrected.MP4"]
    assert write.state is SafeWriteState.COMMITTED
    assert not write.temp_leftover


def test_block_without_commit_aborts(source: Path) -> None:
    with SafeWrite(_plan(source)) as write:
        write.temp_path.write_bytes(b"partial")
    assert _names(source.parent) == ["GX010123.MP4"]
    assert write.state is SafeWriteState.ABORTED


# --- abort: exception, cancel, ENOSPC --------------------------------------------------------


def test_exception_inside_block_removes_temporary_and_propagates(source: Path) -> None:
    with pytest.raises(RuntimeError, match="boom"), SafeWrite(_plan(source)) as write:
        write.temp_path.write_bytes(b"partial")
        raise RuntimeError("boom")
    assert _names(source.parent) == ["GX010123.MP4"]


def test_cancel_removes_temporary(source: Path) -> None:
    with pytest.raises(CancelledError), SafeWrite(_plan(source)) as write:
        write.temp_path.write_bytes(b"partial")
        raise CancelledError
    assert _names(source.parent) == ["GX010123.MP4"]


def test_explicit_abort_for_cancel(source: Path) -> None:
    write = SafeWrite(_plan(source))
    write.begin()
    write.temp_path.write_bytes(b"partial")
    assert write.abort() is True
    assert _names(source.parent) == ["GX010123.MP4"]


def test_simulated_enospc_leaves_nothing(source: Path) -> None:
    def writer(path: Path) -> None:
        path.write_bytes(b"half of the frames")
        raise OSError(errno.ENOSPC, "No space left on device")

    with pytest.raises(OSError, match="No space") as caught, SafeWrite(_plan(source)) as write:
        writer(write.temp_path)
    assert is_disk_full(caught.value)
    assert _names(source.parent) == ["GX010123.MP4"]


def test_enospc_during_commit_leaves_nothing(source: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def full(temp: Path, final: Path) -> bool:
        raise OSError(errno.ENOSPC, "No space left on device")

    monkeypatch.setattr(sw, "_install", full)
    with pytest.raises(OSError) as caught, SafeWrite(_plan(source)) as write:
        write.temp_path.write_bytes(b"data")
        write.commit()
    assert is_disk_full(caught.value)
    assert _names(source.parent) == ["GX010123.MP4"]


def test_is_disk_full_classification() -> None:
    assert is_disk_full(OSError(errno.ENOSPC, "x"))
    assert not is_disk_full(OSError(errno.EACCES, "x"))
    assert not is_disk_full(ValueError("x"))
    winerror = OSError(0, "x")
    winerror.winerror = 112  # type: ignore[attr-defined]
    assert is_disk_full(winerror)


def test_abort_is_idempotent_and_survives_a_sink_that_removed_the_partial(source: Path) -> None:
    write = SafeWrite(_plan(source))
    write.begin()
    write.temp_path.unlink()  # VideoSink.abort already removed it
    assert write.abort() is True
    assert write.abort() is True
    assert _names(source.parent) == ["GX010123.MP4"]


def test_abort_after_commit_never_touches_the_final(source: Path) -> None:
    write = SafeWrite(_plan(source))
    write.begin()
    write.temp_path.write_bytes(b"OUT")
    final = write.commit()
    assert write.abort() is True
    assert final.read_bytes() == b"OUT"


def test_abort_before_begin_does_not_delete_a_foreign_temporary(source: Path) -> None:
    plan = _plan(source)
    stale = source.parent / "GX010123_corrected.clearwater-partial.MP4"
    stale.write_bytes(b"someone else's")
    write = SafeWrite(plan)
    assert write.abort() is True
    assert stale.read_bytes() == b"someone else's"


def test_abort_that_cannot_remove_reports_false(
    source: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write = SafeWrite(_plan(source))
    write.begin()

    def locked(self: Path, missing_ok: bool = False) -> None:
        raise PermissionError(errno.EACCES, "in use")

    monkeypatch.setattr(Path, "unlink", locked)
    assert write.abort() is False
    assert write.temp_leftover
    assert isinstance(write.abort_error, PermissionError)
    monkeypatch.undo()
    assert remove_leftovers([source.parent]).removed == (write.temp_path,)


# --- begin: folder, source guard, stale temporary ----------------------------------------------


def test_missing_output_folder_raises_and_creates_nothing(source: Path, tmp_path: Path) -> None:
    settings = Settings(output_folder=tmp_path / "unplugged" / "card")
    plan = plan_output(source, settings, MediaKind.VIDEO)
    before = _names(tmp_path)
    with pytest.raises(MissingFolderError, match="unplugged"), SafeWrite(plan):
        pytest.fail("the block must not run")
    assert _names(tmp_path) == before
    assert not (tmp_path / "unplugged").exists()
    assert isinstance(MissingFolderError("x"), SafeWriteError)


def test_begin_refuses_the_source_path(source: Path) -> None:
    # The empty-suffix case in the source folder, built by hand so planning cannot hide it.
    plan = OutputPlan(source, source.parent, source.stem, source.suffix)
    assert plan.path == source
    with pytest.raises(SafeWriteError, match="source"):
        SafeWrite(plan).begin()
    assert _names(source.parent) == ["GX010123.MP4"]


def test_begin_refuses_the_source_path_case_variant_when_source_missing(tmp_path: Path) -> None:
    source = tmp_path / "GX010123.MP4"  # not on disk: lexical comparison
    plan = OutputPlan(source, tmp_path, "gx010123", ".mp4")
    with pytest.raises(SafeWriteError, match="source"):
        SafeWrite(plan).begin()


def check_source_guard_refuses(folder: Path) -> None:
    """Shared check: an empty suffix in the source folder must be refused at begin."""
    src = folder / "CLIP.MP4"
    src.write_bytes(SOURCE_BYTES)
    plan = OutputPlan(src, folder, src.stem, src.suffix)
    with pytest.raises(SafeWriteError, match="source"):
        SafeWrite(plan).begin()


def test_source_guard_check_passes_for_the_real_guard(tmp_path: Path) -> None:
    check_source_guard_refuses(tmp_path)


def test_planted_missing_source_guard_fails_by_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sw, "is_same_path", lambda a, b: False)
    with pytest.raises(pytest.fail.Exception):  # pytest.raises inside the check fails
        check_source_guard_refuses(tmp_path)


def test_commit_never_lands_on_the_source_name(source: Path) -> None:
    # Planned at _corrected; the next candidates are skipped, never the source itself.
    plan = OutputPlan(source, source.parent, "GX010123_corrected", ".MP4")
    (source.parent / "GX010123_corrected.MP4").write_bytes(b"taken")
    with SafeWrite(plan) as write:
        write.temp_path.write_bytes(b"OUT")
        assert write.commit().name == "GX010123_corrected_2.MP4"


def test_stale_temporary_at_planned_number_gives_a_bump_not_a_failure(source: Path) -> None:
    stale = source.parent / "GX010123_corrected.clearwater-partial.MP4"
    stale.write_bytes(b"crash leftover")
    plan = _plan(source)
    assert plan.number == 2
    with SafeWrite(plan) as write:
        write.temp_path.write_bytes(b"OUT")
        assert write.commit().name == "GX010123_corrected_2.MP4"
    assert stale.read_bytes() == b"crash leftover"


def test_begin_on_a_real_race_raises_file_exists(source: Path) -> None:
    plan = _plan(source)
    temporary_path(plan.path).write_bytes(b"appeared after planning")
    with pytest.raises(FileExistsError):
        SafeWrite(plan).begin()
    assert temporary_path(plan.path).read_bytes() == b"appeared after planning"


def test_begin_twice_and_commit_out_of_order(source: Path) -> None:
    write = SafeWrite(_plan(source))
    with pytest.raises(SafeWriteError):
        write.commit()
    write.begin()
    with pytest.raises(SafeWriteError):
        write.begin()
    write.abort()
    with pytest.raises(SafeWriteError):
        write.commit()


def test_commit_with_missing_temporary_raises_and_context_cleans(source: Path) -> None:
    with pytest.raises(SafeWriteError, match="missing"), SafeWrite(_plan(source)) as write:
        write.temp_path.unlink()
        write.commit()
    assert _names(source.parent) == ["GX010123.MP4"]


# --- commit: the final name appeared after planning ---------------------------------------------


def test_final_name_taken_since_planning_moves_to_next_number(source: Path) -> None:
    plan = _plan(source)
    existing = plan.path
    with SafeWrite(plan) as write:
        existing.write_bytes(b"someone else's output")
        write.temp_path.write_bytes(b"OUT")
        final = write.commit()
    assert final.name == "GX010123_corrected_2.MP4"
    assert final.read_bytes() == b"OUT"
    assert existing.read_bytes() == b"someone else's output"


def test_commit_skips_names_held_by_other_jobs(source: Path) -> None:
    reservations = Reservations()
    plan_a = _plan(source, reservations)
    plan_b = _plan(source, reservations)  # _2, held
    assert plan_b.number == 2
    plan_a.path.write_bytes(b"appeared after planning")
    with SafeWrite(plan_a, reservations) as write:
        write.temp_path.write_bytes(b"OUT")
        assert write.commit().name == "GX010123_corrected_3.MP4"
    assert plan_b.path in reservations  # still held for its own job
    assert len(reservations) == 1


def test_reservations_released_on_abort(source: Path) -> None:
    reservations = Reservations()
    with pytest.raises(CancelledError), SafeWrite(_plan(source, reservations), reservations):
        raise CancelledError
    assert len(reservations) == 0


# --- the rename is never an overwrite ------------------------------------------------------------


def check_install_never_replaces(install: Callable[[Path, Path], bool], folder: Path) -> None:
    """Shared check: installing onto an existing name reports False and keeps its bytes."""
    temp = folder / "t.tmp"
    final = folder / "f.out"
    temp.write_bytes(b"NEW")
    final.write_bytes(b"EXISTING")
    assert install(temp, final) is False
    assert final.read_bytes() == b"EXISTING"
    assert temp.read_bytes() == b"NEW"
    final.unlink()
    assert install(temp, final) is True
    assert final.read_bytes() == b"NEW"
    assert not temp.exists()


def test_install_never_replaces_link_path(tmp_path: Path) -> None:
    check_install_never_replaces(sw._install, tmp_path)


def test_install_never_replaces_rename_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def no_links(src: object, dst: object) -> None:
        raise OSError(errno.EPERM, "links not supported on this volume")

    monkeypatch.setattr(os, "link", no_links)
    check_install_never_replaces(sw._install, tmp_path)


def test_install_fallback_when_rename_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Windows refuses os.rename over an existing file even when the re-check was passed.
    temp = tmp_path / "t.tmp"
    final = tmp_path / "f.out"
    temp.write_bytes(b"NEW")

    def no_links(src: object, dst: object) -> None:
        raise OSError(errno.EPERM, "links not supported")

    def refusing(src: object, dst: object) -> None:
        raise FileExistsError(errno.EEXIST, "exists")

    monkeypatch.setattr(os, "link", no_links)
    monkeypatch.setattr(os, "rename", refusing)
    assert sw._install(temp, final) is False
    assert temp.read_bytes() == b"NEW"


def test_planted_overwriting_rename_fails_by_name(tmp_path: Path) -> None:
    def overwriting(temp: Path, final: Path) -> bool:
        os.replace(temp, final)
        return True

    with pytest.raises(AssertionError):
        check_install_never_replaces(overwriting, tmp_path)


def test_commit_fallback_end_to_end(source: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def no_links(src: object, dst: object) -> None:
        raise OSError(errno.EPERM, "links not supported")

    monkeypatch.setattr(os, "link", no_links)
    plan = _plan(source)
    with SafeWrite(plan) as write:
        plan.path.write_bytes(b"appeared")
        write.temp_path.write_bytes(b"OUT")
        assert write.commit().name == "GX010123_corrected_2.MP4"
    assert plan.path.read_bytes() == b"appeared"


def test_temporary_unlink_failure_after_link_leaves_correct_final(
    source: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sw, "_unlink_quietly", lambda path: False)
    with SafeWrite(_plan(source)) as write:
        write.temp_path.write_bytes(b"OUT")
        final = write.commit()
    assert write.temp_leftover
    assert write.abort() is False
    assert final.read_bytes() == b"OUT"
    report = remove_leftovers([source.parent])
    assert report.removed == (write.temp_path,)
    assert final.read_bytes() == b"OUT"


# --- leftovers: crash simulation ----------------------------------------


def _scatter(folder: Path) -> dict[str, bytes]:
    keep = {
        "GX010123.MP4": b"cam",
        "GX010123.LRV": b"lrv",
        "IMG_1234.HEIC": b"heic",
        "IMG_1234_corrected.png": b"png",
        "GX010123_corrected.MP4": b"out",
        "notes.txt": b"n",
        ".clearwater-partial": b"no base",
        "a.clearwater-partial.b.MP4": b"two dots",
    }
    for name, data in keep.items():
        (folder / name).write_bytes(data)
    return keep


def check_cleanup(cleanup: Callable[[list[Path]], object], folder: Path) -> None:
    """Shared check: only temporary files go; everything else stays byte-identical."""
    keep = _scatter(folder)
    temps = [
        "GX020001_corrected.clearwater-partial.MP4",
        "IMG_9_corrected.clearwater-partial.png",
        "noext.CLEARWATER-PARTIAL",
    ]
    for name in temps:
        (folder / name).write_bytes(b"partial")
    (folder / "dir_corrected.clearwater-partial.MP4").mkdir()
    cleanup([folder])
    assert sorted(p.name for p in folder.iterdir() if p.is_file()) == sorted(keep)
    for name, data in keep.items():
        assert (folder / name).read_bytes() == data
    assert (folder / "dir_corrected.clearwater-partial.MP4").is_dir()


def test_crash_leftover_is_removed_and_nothing_else(tmp_path: Path) -> None:
    check_cleanup(remove_leftovers, tmp_path)


def test_crash_simulation_end_to_end(source: Path) -> None:
    write = SafeWrite(_plan(source))
    write.begin()
    write.temp_path.write_bytes(b"half written when the process died")
    # no abort: the process "crashes" here
    report = remove_leftovers([source.parent])
    assert isinstance(report, LeftoverReport)
    assert report.removed == (write.temp_path,)
    assert report.failed == ()
    assert _names(source.parent) == ["GX010123.MP4"]


def test_planted_cleanup_deleting_a_non_temporary_fails_by_name(tmp_path: Path) -> None:
    def delete_everything(folders: list[Path]) -> None:
        for folder in folders:
            for entry in folder.iterdir():
                if entry.is_file():
                    entry.unlink()

    with pytest.raises(AssertionError):
        check_cleanup(delete_everything, tmp_path)


def test_cleanup_is_not_recursive_and_skips_missing_folders(tmp_path: Path) -> None:
    sub = tmp_path / "sub"
    sub.mkdir()
    nested = sub / "x.clearwater-partial.MP4"
    nested.write_bytes(b"nested")
    top = tmp_path / "y.clearwater-partial.MP4"
    top.write_bytes(b"top")
    report = remove_leftovers([tmp_path, tmp_path / "missing"])
    assert report.removed == (top,)
    assert nested.exists()


def test_cleanup_never_follows_a_symlink(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    target = outside / "precious.txt"
    target.write_bytes(b"keep me")
    folder = tmp_path / "folder"
    folder.mkdir()
    link = folder / "evil.clearwater-partial.MP4"
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not available")
    dirlink = folder / "dir.clearwater-partial.MP4"
    try:
        dirlink.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("directory symlinks not available")
    report = remove_leftovers([folder])
    assert report.removed == ()
    assert target.read_bytes() == b"keep me"
    assert link.is_symlink()
    assert (outside / "precious.txt").exists()


def test_cleanup_records_a_failure_and_goes_on(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "a.clearwater-partial.MP4").write_bytes(b"1")
    (tmp_path / "b.clearwater-partial.MP4").write_bytes(b"2")
    real_unlink = os.unlink

    def flaky(path: str | os.PathLike[str], *args: object, **kwargs: object) -> None:
        if str(path).endswith("a.clearwater-partial.MP4"):
            raise PermissionError(errno.EACCES, "in use")
        real_unlink(path)

    monkeypatch.setattr(os, "unlink", flaky)
    report = remove_leftovers([tmp_path])
    assert [p.name for p in report.removed] == ["b.clearwater-partial.MP4"]
    assert [p.name for p, _ in report.failed] == ["a.clearwater-partial.MP4"]
