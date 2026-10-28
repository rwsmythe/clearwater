"""WP3.21: ``tools/export_bench.py`` writes under a chosen folder of the working folder (Q7)."""

from __future__ import annotations

from pathlib import Path

import pytest

from export_bench import SUBDIR, bench_folder


def test_the_default_folder_is_unchanged(tmp_path: Path) -> None:
    assert bench_folder(tmp_path, SUBDIR) == (tmp_path / "wp3.14" / "bench").resolve()


def test_a_subdir_under_the_working_folder(tmp_path: Path) -> None:
    got = bench_folder(tmp_path, Path("wp3.21") / "bench")
    assert got == (tmp_path / "wp3.21" / "bench").resolve()


@pytest.mark.parametrize("subdir", ["..", "../elsewhere", "wp3.21/../../out"])
def test_a_subdir_leading_out_is_refused(tmp_path: Path, subdir: str) -> None:
    with pytest.raises(ValueError, match="not a folder under the working folder"):
        bench_folder(tmp_path / "work", Path(subdir))


def test_an_absolute_subdir_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not a folder under the working folder"):
        bench_folder(tmp_path, tmp_path / "abs")
