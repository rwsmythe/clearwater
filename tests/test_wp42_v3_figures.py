"""WP4.2 Reviewer B remediation (B1, B2): the V3 figures file's creation.

``CLEARWATER_WP42_V3_FIGURES`` names the figures file of a recorded V3 run
(``tests/test_wp42_v3_product.py``). Its one creation helper, ``create_figures_file``, passes
the path through the runner's footage check (``headless_export.write_target_refusal``) before
anything is created, refuses the switch when no footage folder is configured, and creates the
file exclusively; every later line goes through the one handle it returns. Unmarked: these run
in the parallel leg (no GPU, no FFmpeg, no footage).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from test_wp42_v3_product import _keep, create_figures_file


@pytest.fixture
def footage(tmp_path: Path) -> Path:
    """A stand-in footage folder under ``tmp_path`` (never the configured one)."""
    folder = tmp_path / "footage"
    folder.mkdir()
    return folder


def test_an_existing_file_is_refused_and_left_unchanged(tmp_path: Path, footage: Path) -> None:
    target = tmp_path / "out" / "figures.txt"
    target.parent.mkdir()
    target.write_bytes(b"planted\n")
    with pytest.raises(pytest.fail.Exception, match="existing file"):
        create_figures_file(target, footage, "cpu")
    assert target.read_bytes() == b"planted\n"


def test_a_path_inside_the_footage_folder_is_refused_and_nothing_is_created(
    footage: Path,
) -> None:
    target = footage / "records" / "figures.txt"
    with pytest.raises(pytest.fail.Exception, match="is refused"):
        create_figures_file(target, footage, "cpu")
    assert list(footage.iterdir()) == []


def test_a_dangling_link_is_refused(tmp_path: Path, footage: Path) -> None:
    # On Windows ``open(link, "xb")`` follows a dangling symbolic link and creates its target,
    # so the footage check's link rule (ii) is what refuses it.
    nowhere = tmp_path / "nowhere.txt"
    link = tmp_path / "figures.txt"
    try:
        os.symlink(nowhere, link)
    except OSError as exc:
        pytest.skip(f"the OS refused to create a symbolic link: {exc}")
    with pytest.raises(pytest.fail.Exception, match="is refused"):
        create_figures_file(link, footage, "cpu")
    assert not os.path.lexists(nowhere)
    assert os.path.islink(link)


def test_no_configured_footage_folder_refuses_the_switch(tmp_path: Path) -> None:
    target = tmp_path / "out" / "figures.txt"
    with pytest.raises(pytest.fail.Exception, match="no footage folder"):
        create_figures_file(target, None, "cpu")
    assert not (tmp_path / "out").exists()


def test_a_fresh_path_gets_the_backend_line_then_each_line(tmp_path: Path, footage: Path) -> None:
    target = tmp_path / "new" / "figures.txt"
    with create_figures_file(target, footage, "cuda:0") as handle:
        _keep(handle, "ad14-flicker c3 | a")
        _keep(handle, "jitter c3 | b")
    assert target.read_bytes() == b"backend: cuda:0\nad14-flicker c3 | a\njitter c3 | b\n"
