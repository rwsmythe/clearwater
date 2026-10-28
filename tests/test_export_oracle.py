"""Tests of the WP3.21 task 2 equality oracle ``tools/export_oracle.py`` (question 3).

No footage: the records are made from a WP2.3 sample on the CPU. Checked here: the record's
shape and cleanup, the base control (two records of the same code are tier 1), that a planted
change is classified by its size (tier 2 inside AD-11's bound, a fail outside it), that a
record, proxy or ``analyze`` difference fails whatever the frames show (ruling Q3), the 1 fps
keep interval, and the refusals of footage-folder paths.
"""

from __future__ import annotations

import dataclasses
import json
import shutil
from collections.abc import Mapping
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import pytest

import export_oracle as eo
from clearwater.interfaces import Image, Statistics
from clearwater.methods import available_methods
from local_config import LocalConfig

pytestmark = pytest.mark.usefixtures("ffmpeg_tools")

SAMPLE = "vid-hevc8-bt709-full"


class Shifted:
    """The c3 method with every rendered pixel moved by ``shift`` (clipped to [0, 1])."""

    def __init__(self, shift: float) -> None:
        self._inner = available_methods()["c3"]
        self.id, self.label = self._inner.id, self._inner.label
        self.parameters, self.stages = self._inner.parameters, self._inner.stages
        self._shift = np.float32(shift)

    def analyze(self, *args: Any) -> Statistics:
        return self._inner.analyze(*args)

    def closed_form(self, *args: Any) -> Statistics | None:
        return self._inner.closed_form(*args)

    def render(
        self, image: Image, params: Mapping[str, Any], statistics: Mapping[str, Statistics]
    ) -> Image:
        out = self._inner.render(image, params, statistics)
        moved = np.clip(np.asarray(out.pixels) + self._shift, 0, 1).astype(np.float32)
        return dataclasses.replace(out, pixels=moved)


@pytest.fixture(scope="module")
def base(sample_provider: Any, tmp_path_factory: pytest.TempPathFactory) -> Path:
    """One CPU record of the sample on the unchanged code (every frame kept)."""
    folder = tmp_path_factory.mktemp("oracle") / "base"
    eo.record_clip(eo.Job(sample_provider.path(SAMPLE), force_cpu=True, every_frame=True), folder)
    return folder


def test_a_record_holds_every_frame_record_call_and_proxy(base: Path) -> None:
    record = eo.load(base)
    assert record["ok"] and record["device"] == "CPU: forced"
    assert record["clip"] == "hevc8-bt709-full.mp4" and record["method"] == "c3"
    assert len(record["frames"]) == len(record["samples"]) == 45
    assert [pts for pts, _ in record["frames"]] == sorted(int(p) for p in record["renders"])
    assert len(record["analyses"]) == 2 * 45  # white_balance in the pass, then fusion
    assert {entry[0] for entry in record["analyses"]} == {"white_balance", "fusion"}
    assert len(record["proxies"]) == 45 and record["cache_complete"] is True
    assert record["source_statistics"] == {}  # c3 has no source-only stage
    assert record["repeated_renders"] == [] and record["closed_forms"] == []
    one = next(iter(record["renders"].values()))
    assert set(one["values"]) == {"white_balance", "fusion"}
    assert set(one["values"]["fusion"]) == {"bounds", "saliency_means"}
    assert not (base / "cache").exists() and not (base / "out").exists()
    kept = np.load(base / "frames" / record["samples"][str(record["frames"][0][0])])
    assert kept.dtype == np.float32 and kept.shape == (180, 320, 3)
    assert eo.array_digest(kept) == record["frames"][0][1]


def test_the_base_control_is_tier_1(base: Path, sample: Any, tmp_path: Path) -> None:
    again = tmp_path / "again"
    eo.record_clip(eo.Job(sample(SAMPLE), force_cpu=True, every_frame=True), again)
    result = eo.compare(base, again)
    assert result["verdict"] == "TIER1", result["reasons"]
    assert result["frames"] == 45 and result["frames_differing"] == 0


@pytest.mark.parametrize(
    ("shift", "verdict"),
    [(1e-4, "TIER2"), (1e-2, "FAIL")],
)
def test_a_planted_render_change_is_classified_by_its_size(
    base: Path, sample: Any, tmp_path: Path, shift: float, verdict: str
) -> None:
    folder = tmp_path / "shifted"
    eo.record_clip(
        eo.Job(sample(SAMPLE), force_cpu=True, every_frame=True),
        folder,
        methods={"c3": Shifted(shift)},  # type: ignore[dict-item]
    )
    result = eo.compare(base, folder)
    assert result["verdict"] == verdict, result["reasons"]
    assert result["frames_differing"] == result["frames_measured"] == 45
    assert result["max_abs"] == pytest.approx(shift, rel=0.05)
    if verdict == "FAIL":
        assert any("exceed AD-11" in reason for reason in result["reasons"])


def _mutated(base: Path, tmp_path: Path, change: Any) -> Path:
    folder = tmp_path / "mutated"
    shutil.copytree(base, folder)
    record = eo.load(folder)
    change(record)
    (folder / eo.RECORD).write_text(json.dumps(record), encoding="utf-8")
    return folder


@pytest.mark.parametrize(
    ("what", "reason"),
    [
        ("renders", "statistics records differ"),
        ("proxies", "proxies differ"),
        ("analyses", "analyze calls differ"),
    ],
)
def test_a_record_proxy_or_analyze_difference_fails_with_equal_frames(
    base: Path, tmp_path: Path, what: str, reason: str
) -> None:
    def change(record: dict[str, Any]) -> None:
        if what == "analyses":
            record["analyses"][0][3] = "0" * 64
        else:
            first = next(iter(record[what]))
            if what == "renders":
                record[what][first]["digest"] = "0" * 64
            else:
                record[what][first] = "0" * 64

    result = eo.compare(base, _mutated(base, tmp_path, change))
    assert result["frames_differing"] == 0  # the frames are the base's ...
    assert result["verdict"] == "FAIL"  # ... and the comparison fails all the same (Q3)
    assert any(reason in r for r in result["reasons"])


def test_a_differing_frame_without_a_sample_is_unmeasured(base: Path, tmp_path: Path) -> None:
    def change(record: dict[str, Any]) -> None:
        pts = record["frames"][3][0]
        record["frames"][3][1] = "0" * 64
        del record["samples"][str(pts)]

    result = eo.compare(base, _mutated(base, tmp_path, change))
    assert result["verdict"] == "TIER2"
    assert result["frames_differing"] == result["frames_unmeasured"] == 1


def test_one_frame_per_second_keeps_23_frames_of_gx011627() -> None:
    every = eo.sample_every(Fraction(30000, 1001), every_frame=False)
    assert every == 30 and len(range(0, 681, every)) == 23
    assert eo.sample_every(Fraction(30000, 1001), every_frame=True) == 1


def test_digests_see_dtype_shape_and_nesting() -> None:
    a = np.arange(6, dtype=np.float64)
    assert eo.array_digest(a) != eo.array_digest(a.astype(np.float32))
    assert eo.array_digest(a) != eo.array_digest(a.reshape(2, 3))
    assert eo.host(a) is a
    record = {"s": {"x": a}}
    assert eo.record_digest(record) == eo.record_digest({"s": {"x": a.copy()}})
    assert eo.record_digest(record) != eo.record_digest({"t": {"x": a}})
    values = eo.record_values({"s": {"x": np.array([0.1])}})
    assert values == {"s": {"x": {"shape": [1], "hex": [(0.1).hex()]}}}


# --- the command line ------------------------------------------------------------------------


@pytest.fixture
def folders(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> LocalConfig:
    config = LocalConfig(footage_path=tmp_path / "footage", working_path=tmp_path / "work")
    config.footage_path.mkdir()
    monkeypatch.setattr(eo, "load_local_config", lambda path=None: config)
    return config


def test_main_records_a_clip_by_stem_and_leaves_the_footage_alone(
    folders: LocalConfig, sample: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    clip = folders.footage_path / "GX000001.mp4"
    clip.write_bytes(sample(SAMPLE).read_bytes())
    footage = (clip.read_bytes(), clip.stat().st_mtime_ns)
    argv = ["record", "--clip", "GX000001", "--force-cpu", "--name", "ref"]
    assert eo.main(argv) == 0
    out = capsys.readouterr().out
    assert out.splitlines()[0].startswith("ORACLE GX000001.mp4 c3 CPU: forced: 45 frames")
    folder = folders.working_path / eo.SUBDIR / "ref"
    assert out.strip().splitlines()[-1] == f"RECORD {folder}"
    assert len(eo.load(folder)["samples"]) == 2  # pts index 0 and 30 at one per second
    assert (clip.read_bytes(), clip.stat().st_mtime_ns) == footage
    assert [p.name for p in folders.footage_path.iterdir()] == ["GX000001.mp4"]
    assert eo.main(argv) == 2  # never reuses a folder
    assert eo.main(["compare", str(folder), str(folder), "--require-tier1"]) == 0


def test_main_refuses_a_file_inside_the_footage_folder(
    folders: LocalConfig, capsys: pytest.CaptureFixture[str]
) -> None:
    clip = folders.footage_path / "GX000001.mp4"
    clip.write_bytes(b"x")
    assert eo.main(["record", "--file", str(clip)]) == 2
    assert "inside the footage folder" in capsys.readouterr().err
    assert not folders.working_path.exists()


def test_main_refuses_a_working_folder_inside_the_footage_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    footage = tmp_path / "footage"
    footage.mkdir()
    (footage / "GX000001.mp4").write_bytes(b"x")
    config = LocalConfig(footage_path=footage, working_path=footage / "work")
    monkeypatch.setattr(eo, "load_local_config", lambda path=None: config)
    assert eo.main(["record", "--clip", "GX000001"]) == 2
    assert "inside the footage folder" in capsys.readouterr().err
    assert [p.name for p in footage.iterdir()] == ["GX000001.mp4"]


def test_a_failed_job_keeps_its_record_and_exits_1(
    folders: LocalConfig, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    broken = tmp_path / "broken.mp4"
    broken.write_bytes(b"\x00" * 64)
    assert eo.main(["record", "--file", str(broken), "--force-cpu", "--name", "bad"]) == 1
    record = eo.load(folders.working_path / eo.SUBDIR / "bad")
    assert record["ok"] is False and record["failure"]
    assert "FAILED" in capsys.readouterr().out


def test_the_synthetic_clip_is_refused_when_its_bytes_are_not_the_recorded_ones(
    tmp_path: Path,
) -> None:
    clips = tmp_path / "clips"
    clips.mkdir()
    clip = clips / f"{eo.SYNTHETIC_4K}.mp4"
    clip.write_bytes(b"made once")
    with pytest.raises(eo.OracleError, match="no recorded digest"):
        eo.synthetic_4k(tmp_path)
    (clips / f"{clip.name}.sha256").write_text(eo.file_sha256(clip) + "\n", encoding="ascii")
    assert eo.synthetic_4k(tmp_path) == clip  # the recorded bytes: used, not regenerated
    clip.write_bytes(b"made again")
    with pytest.raises(eo.OracleError, match="SHA-256 differs"):
        eo.synthetic_4k(tmp_path)
