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
    "text",
    [
        "not json",
        '{"format_version": 2, "entries": []}',
        '{"format_version": 1, "entries": [{"id": "x", "folder": "relative"}]}',
        '{"format_version": 1, "entries": "none"}',
        "[" * 100000,
    ],
    ids=["text", "version", "relative", "shape", "deep"],
)
def test_an_undecodable_journal_is_set_aside_and_read_as_empty(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, text: str
) -> None:
    """Ruling S6: renamed ``write-journal.json.bad-<UTC stamp>``, logged, read as empty."""
    config = tmp_path / "config"
    config.mkdir()
    (config / JOURNAL_FILE_NAME).write_text(text, encoding="utf-8")
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
