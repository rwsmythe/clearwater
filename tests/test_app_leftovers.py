"""WP4.3: the write journal and the leftover clean-up (D85, 8.4, V11; question 3 as ruled; S6).

The journal (``config_dir/write-journal.json``, format version 1) holds one destination folder
per in-flight export; start-up scans ``Settings.output_folder`` plus the journal's folders with
WP3.13's ``remove_leftovers`` and clears the scanned entries; an undecodable journal is set
aside and read as empty (S6). V11's leg on the running shell: a planted temporary in a journal
folder and in the output folder is removed at the next start, and a non-matching file is kept.
The footage-absence test (question 3): start-up never scans a folder only because a source lies
there, and a configured footage folder is in no computed set.
"""

# ``make_app`` is imported from test_app_startup and used as a parameter.
# ruff: noqa: F401, F811

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import pytest

import gui_support
from clearwater.app import startup
from clearwater.app.startup import JOURNAL_FILE_NAME, WriteJournal, clean_leftovers
from clearwater.config import save_settings
from clearwater.jobs import new_token, temporary_path
from clearwater.jobs import safe_write as safe_write_module
from test_app_startup import app_data, cpu_settings, make_app, wait_started


def _temporary(folder: Path, name: str = "clip_corrected.mp4") -> Path:
    """Plant a file named like a temporary output of ``folder / name``."""
    path = temporary_path(folder / name, new_token())
    path.write_bytes(b"partial")
    return path


def test_the_journal_records_one_absolute_folder_per_entry(tmp_path: Path) -> None:
    journal = WriteJournal(tmp_path / "config")
    first = journal.add(tmp_path / "a")
    second = journal.add(tmp_path / "b")
    assert first != second
    assert journal.entries() == ((first, tmp_path / "a"), (second, tmp_path / "b"))
    document = json.loads((tmp_path / "config" / JOURNAL_FILE_NAME).read_text(encoding="utf-8"))
    assert document == {
        "format_version": 1,
        "entries": [
            {"id": first, "folder": str(tmp_path / "a")},
            {"id": second, "folder": str(tmp_path / "b")},
        ],
    }
    journal.remove(first)
    assert journal.entries() == ((second, tmp_path / "b"),)
    journal.remove("unknown")
    assert journal.entries() == ((second, tmp_path / "b"),)


@pytest.mark.parametrize(
    "data",
    [
        b"not json",
        b'{"format_version": 2, "entries": []}',
        b'{"format_version": 1, "entries": [{"id": "x", "folder": "relative"}]}',
        b'{"format_version": 1, "entries": "none"}',
        b"[" * 100000,
        b"\xff",
        b'{"format_version": 1, "entries": [{"id": "\xe9", "folder": "/x"}]}',
        b'{"format_version": 1, "entries": [{"id": "x", "folder": "@ABS@\\u0000folder"}]}',
    ],
    ids=["text", "version", "relative", "shape", "deep", "not-utf8", "latin1-inside", "nul-folder"],
)
def test_an_undecodable_journal_is_set_aside_and_read_as_empty(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, data: bytes
) -> None:
    """Ruling S6: renamed ``write-journal.json.bad-<UTC stamp>``, logged, read as empty.

    The encoding failures (R1-1, ruling d530b564) take the same set-aside as the decode ones, and
    so does an absolute folder the operating system refuses as a path (R2-2: a NUL character;
    ``@ABS@`` stands for an absolute folder under ``tmp_path``).
    """
    config = tmp_path / "config"
    config.mkdir()
    absolute = json.dumps(str(tmp_path))[1:-1].encode("ascii")
    (config / JOURNAL_FILE_NAME).write_bytes(data.replace(b"@ABS@", absolute))
    journal = WriteJournal(config)
    with caplog.at_level(logging.WARNING, logger=startup.__name__):
        assert journal.entries() == ()
    aside = [p.name for p in config.iterdir()]
    assert len(aside) == 1 and aside[0].startswith(f"{JOURNAL_FILE_NAME}.bad-")
    assert "is not readable" in caplog.text
    journal.add(tmp_path / "out")  # a fresh journal is written beside the one set aside
    assert len(journal.entries()) == 1


def test_an_undecodable_journal_still_lets_the_output_folder_be_scanned(tmp_path: Path) -> None:
    config, out = tmp_path / "config", tmp_path / "out"
    config.mkdir()
    out.mkdir()
    (config / JOURNAL_FILE_NAME).write_text("{", encoding="utf-8")
    planted = _temporary(out)
    report = clean_leftovers(cpu_settings(output_folder=out), WriteJournal(config))
    assert report.removed == (planted,) and not planted.exists()


def test_a_journal_folder_the_os_refuses_lets_the_start_up_proceed(tmp_path: Path) -> None:
    """R2-2: a NUL character in a journal folder is set aside (S6); the output folder is scanned."""
    config, out = tmp_path / "config", tmp_path / "out"
    config.mkdir()
    out.mkdir()
    entry = {"id": "x", "folder": str(tmp_path / "bad\x00folder")}
    document = {"format_version": 1, "entries": [entry]}
    (config / JOURNAL_FILE_NAME).write_text(json.dumps(document), encoding="utf-8")
    planted = _temporary(out)
    report = clean_leftovers(cpu_settings(output_folder=out), WriteJournal(config))
    assert report.removed == (planted,) and not planted.exists()
    assert [p.name.startswith(f"{JOURNAL_FILE_NAME}.bad-") for p in config.iterdir()] == [True]
    assert startup.holds_leftovers(tmp_path / "bad\x00folder")  # unlistable: the entry would stay


def test_an_output_folder_the_os_refuses_is_skipped_and_logged(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """R3-1 (ruling d6e9abdf): a NUL in ``output_folder`` is skipped and logged; nothing raises.

    The bad ``Settings`` is built directly, so the test holds whatever the settings store does
    with such a field at its source (WP4.3a's per-field default).
    """
    journaled = tmp_path / "journaled"
    journaled.mkdir()
    journal = WriteJournal(tmp_path / "config")
    journal.add(journaled)
    planted = _temporary(journaled)
    bad = tmp_path / "bad\x00folder"
    with caplog.at_level(logging.WARNING, logger=startup.__name__):
        report = clean_leftovers(cpu_settings(output_folder=bad), journal)
    assert report.removed == (planted,) and not planted.exists()
    assert journal.entries() == ()  # the journal's folders are still scanned and cleared
    assert "skips" in caplog.text and repr(str(bad)) in caplog.text


class _FailsOnIteration:
    """A listing that opens, then refuses its first entry (Windows can deny at either step)."""

    def __init__(self, error: OSError) -> None:
        self.error = error

    def __enter__(self) -> _FailsOnIteration:
        return self

    def __exit__(self, *_exc: object) -> None:
        return None

    def __iter__(self) -> _FailsOnIteration:
        return self

    def __next__(self) -> os.DirEntry[str]:
        raise self.error


_LIST = "could not list the output folder"
_KEEP = "the write journal keeps"


@pytest.mark.parametrize(
    ("fault", "journaled", "expected"),
    [
        ("open", False, [_LIST]),
        ("iterate", False, [_LIST]),
        ("open", True, [_LIST, _KEEP]),
        ("missing", False, []),
        (None, False, []),
    ],
    ids=[
        "unlistable",
        "unlistable-on-iteration",
        "unlistable-and-journaled",
        "missing",
        "listable",
    ],
)
def test_an_output_folder_that_cannot_be_listed_is_logged_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    fault: str | None,
    journaled: bool,
    expected: list[str],
) -> None:
    """B-7: an unlistable ``output_folder`` logs one warning; a missing one has nothing to log.

    The rule is ``holds_leftovers``': an ``OSError`` (or ``ValueError``) means the folder cannot
    be listed, a ``FileNotFoundError`` means it holds nothing. A denial on opening the listing
    and one on reading its first entry are both unlistable (cell 13, item 1). An output folder
    that is also a journal folder logs two facts, each once: the folder cannot be listed, and
    its entry stays (CHARC ruling b0d679b0, item 2).
    """
    out = tmp_path / "out"
    out.mkdir()
    journal = WriteJournal(tmp_path / "c")
    if journaled:
        journal.add(out)
    real = os.scandir

    def scandir(path: os.PathLike[str] | str) -> object:
        if Path(path) == out and fault is not None:
            if fault == "iterate":
                return _FailsOnIteration(PermissionError("access is denied"))
            raise PermissionError("access is denied") if fault == "open" else FileNotFoundError()
        return real(path)

    monkeypatch.setattr(os, "scandir", scandir)
    with caplog.at_level(logging.WARNING, logger=startup.__name__):
        report = clean_leftovers(cpu_settings(output_folder=out), journal)
    assert report.removed == () and report.failed == ()
    warnings = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == len(expected), caplog.text
    for line in expected:
        assert [m for m in warnings if line in m and str(out) in m] != [], (line, caplog.text)
        assert sum(line in m for m in warnings) == 1, (line, caplog.text)


def _refuse_reading(monkeypatch: pytest.MonkeyPatch, journal: WriteJournal) -> None:
    """Plant a read denial of the journal file (a scanner's lock, say); other reads proceed."""
    real = Path.read_bytes

    def read_bytes(self: Path) -> bytes:
        if self == journal.path:
            raise PermissionError("the journal is locked")
        return real(self)

    monkeypatch.setattr(Path, "read_bytes", read_bytes)


def test_a_journal_that_cannot_be_read_is_never_overwritten(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """R2-1 (ruling 38a7c702): on a doubtful read ``add`` and ``drop`` raise and write nothing."""
    journal = WriteJournal(tmp_path / "config")
    kept = journal.add(tmp_path / "a")
    before = journal.path.read_bytes()
    with monkeypatch.context() as patch:
        _refuse_reading(patch, journal)
        with pytest.raises(OSError, match="the journal is locked"):
            journal.add(tmp_path / "b")
        with pytest.raises(OSError, match="the journal is locked"):
            journal.drop([(kept, tmp_path / "a")])
        with caplog.at_level(logging.WARNING, logger=startup.__name__):
            assert journal.entries() == ()
        assert "could not be read" in caplog.text
    assert journal.path.read_bytes() == before
    assert journal.entries() == ((kept, tmp_path / "a"),)


def test_a_start_up_over_an_unreadable_journal_logs_and_keeps_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """R2-1: start-up still scans the output folder; the journal file is kept unchanged."""
    out, journaled = tmp_path / "out", tmp_path / "journaled"
    out.mkdir()
    journaled.mkdir()
    journal = WriteJournal(tmp_path / "config")
    kept = journal.add(journaled)
    before = journal.path.read_bytes()
    planted = _temporary(out)
    with monkeypatch.context() as patch:
        _refuse_reading(patch, journal)
        with caplog.at_level(logging.WARNING, logger=startup.__name__):
            report = clean_leftovers(cpu_settings(output_folder=out), journal)
    assert report.removed == (planted,)
    assert "could not be cleared" in caplog.text
    assert journal.path.read_bytes() == before
    assert journal.entries() == ((kept, journaled),)


def test_the_folder_set_is_the_output_folder_then_the_journals_each_once(tmp_path: Path) -> None:
    out, other = tmp_path / "out", tmp_path / "other"
    assert startup.leftover_folders(cpu_settings(output_folder=out), [other, out, other]) == (
        out,
        other,
    )
    assert startup.leftover_folders(cpu_settings(), [other]) == (other,)
    assert startup.leftover_folders(cpu_settings(), []) == ()


def test_the_clean_up_removes_temporaries_keeps_the_rest_and_clears_the_journal(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    out, journaled, unrelated = tmp_path / "out", tmp_path / "journaled", tmp_path / "source"
    for folder in (out, journaled, unrelated):
        folder.mkdir()
    journal = WriteJournal(tmp_path / "config")
    journal.add(journaled)
    removed = {_temporary(out), _temporary(journaled, "IMG_1_corrected.png")}
    kept = [out / "clip_corrected.mp4", journaled / "notes.txt", _temporary(unrelated)]
    for path in kept[:2]:
        path.write_bytes(b"keep")
    with caplog.at_level(logging.INFO, logger=startup.__name__):
        report = clean_leftovers(cpu_settings(output_folder=out), journal)
    assert set(report.removed) == removed and report.failed == ()
    assert all(not p.exists() for p in removed) and all(p.exists() for p in kept)
    assert journal.entries() == ()
    assert all(str(p) in caplog.text for p in removed)  # N9


def test_a_folder_whose_clean_up_failed_keeps_its_entry_until_it_succeeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R1-3 (ruling d530b564): an entry stays until its folder's clean-up has succeeded."""
    locked, clean = tmp_path / "locked", tmp_path / "clean"
    for folder in (locked, clean):
        folder.mkdir()
    journal = WriteJournal(tmp_path / "config")
    kept_id = journal.add(locked)
    journal.add(clean)
    planted = _temporary(locked)
    real_unlink = os.unlink

    def refuse(path: str) -> None:
        if Path(path) == planted:
            raise PermissionError("in use")
        real_unlink(path)

    monkeypatch.setattr(safe_write_module.os, "unlink", refuse)
    report = clean_leftovers(cpu_settings(), journal)
    assert [path for path, _ in report.failed] == [planted] and planted.exists()
    assert journal.entries() == ((kept_id, locked),)  # the clean folder's entry is cleared
    monkeypatch.setattr(safe_write_module.os, "unlink", real_unlink)
    report = clean_leftovers(cpu_settings(), WriteJournal(tmp_path / "config"))  # the next start
    assert report.removed == (planted,) and not planted.exists()
    assert journal.entries() == ()


def test_entries_sharing_an_id_are_cleared_folder_by_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R3-2 (ruling d6e9abdf, MINOR): start-up drops an entry by its (id, folder) pair.

    Two entries with one id (a journal the program did not write: its ids are uuid4), the first
    folder's removal refused: that folder's entry remains, the clean folder's entry goes.
    """
    locked, clean = tmp_path / "locked", tmp_path / "clean"
    for folder in (locked, clean):
        folder.mkdir()
    config = tmp_path / "config"
    config.mkdir()
    entries = [{"id": "dup", "folder": str(locked)}, {"id": "dup", "folder": str(clean)}]
    document = {"format_version": 1, "entries": entries}
    (config / JOURNAL_FILE_NAME).write_text(json.dumps(document), encoding="utf-8")
    journal = WriteJournal(config)
    planted = _temporary(locked)
    real_unlink = os.unlink

    def refuse(path: str) -> None:
        if Path(path) == planted:
            raise PermissionError("in use")
        real_unlink(path)

    monkeypatch.setattr(safe_write_module.os, "unlink", refuse)
    report = clean_leftovers(cpu_settings(), journal)
    assert [path for path, _ in report.failed] == [planted] and planted.exists()
    assert journal.entries() == (("dup", locked),)


# V11 and the footage-absence test on the running shell.


@pytest.mark.gui
def test_v11_leftovers_of_a_crash_are_removed_at_the_next_start(make_app, qtbot, tmp_path) -> None:
    out, source_folder = tmp_path / "out", tmp_path / "sources"
    out.mkdir()
    source_folder.mkdir()
    config = app_data(tmp_path).config_dir
    WriteJournal(config).add(source_folder)  # a crashed default-location export (D34)
    in_out = _temporary(out)
    in_journal = _temporary(source_folder, "IMG_7_corrected.png")
    keep = [out / "clip_corrected.mp4", source_folder / "IMG_7.HEIC"]
    for path in keep:
        path.write_bytes(b"keep")
    application = make_app(cpu_settings(output_folder=out))
    assert set(application.leftovers.removed) == {in_out, in_journal}
    assert not in_out.exists() and not in_journal.exists()
    assert all(p.exists() for p in keep)
    assert application.journal.entries() == ()
    wait_started(qtbot, application)


@pytest.mark.gui
def test_a_settings_file_with_an_output_folder_the_os_refuses_still_starts(
    make_app, qtbot, tmp_path
) -> None:
    """R3-1 (ruling d6e9abdf): start-up over a settings file whose ``output_folder`` holds a NUL.

    The window shows and the journal's folder is cleaned, whether the settings store keeps the
    field (the clean-up skips it) or replaces it by its default (WP4.3a's source-side fix).
    """
    journaled = tmp_path / "journaled"
    journaled.mkdir()
    config = app_data(tmp_path).config_dir
    WriteJournal(config).add(journaled)
    planted = _temporary(journaled)
    save_settings(config, cpu_settings())
    path = config / "settings.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["output_folder"] = str(tmp_path / "bad\x00folder")
    path.write_text(json.dumps(data), encoding="utf-8")
    application = make_app()
    assert application.window.isVisible()
    assert application.leftovers.removed == (planted,) and not planted.exists()
    assert application.journal.entries() == ()
    wait_started(qtbot, application)


@pytest.mark.gui
def test_start_up_never_scans_a_folder_because_a_source_lies_there(
    make_app, qtbot, tmp_path, monkeypatch, sample
) -> None:
    """Sources in a stand-in footage folder, outputs elsewhere: the footage folder is not read."""
    footage, out = tmp_path / "footage", tmp_path / "out"
    footage.mkdir()
    out.mkdir()
    clip = footage / "GX010001.MP4"
    clip.write_bytes(sample("vid-hevc8-bt709-full").read_bytes())
    planted = _temporary(footage, "GX010001_corrected.MP4")
    first = make_app(cpu_settings(output_folder=out), where=tmp_path / "one")
    wait_started(qtbot, first)
    from test_app_startup import open_source, wait_analysis

    open_source(qtbot, first, clip)
    wait_analysis(qtbot, first)
    first.window.shell_actions.export.trigger()
    qtbot.waitUntil(lambda: (out / "GX010001_corrected.MP4").exists(), timeout=120000)
    qtbot.waitUntil(lambda: first.window.jobs.active() == 0, timeout=30000)
    first.window.close()
    scanned: list[Path] = []
    real_scandir = os.scandir

    def spy(path: os.PathLike[str] | str) -> object:
        scanned.append(Path(path))
        return real_scandir(path)

    monkeypatch.setattr(safe_write_module.os, "scandir", spy)
    second = make_app(cpu_settings(output_folder=out), where=tmp_path / "one")
    assert out in scanned  # the output folder is scanned (the cache's own open lists its folder)
    assert planted.exists()
    assert not [p for p in scanned if p == footage or footage in p.parents]
    wait_started(qtbot, second)


def test_a_configured_footage_folder_is_in_no_computed_folder_set(tmp_path: Path) -> None:
    """When ``clearwater.local.toml`` names the footage folder, no scanned folder lies in it."""
    from local_config import LocalConfigError, load_local_config

    try:
        footage = load_local_config().footage_path.resolve()
    except (LocalConfigError, OSError):
        pytest.skip("no clearwater.local.toml names a footage folder here")
    out = tmp_path / "out"
    journal = WriteJournal(tmp_path / "config")
    journal.add(out)
    folders = startup.leftover_folders(
        cpu_settings(output_folder=out), [f for _, f in journal.entries()]
    )
    for folder in folders:
        resolved = folder.resolve()
        assert resolved != footage and footage not in resolved.parents
