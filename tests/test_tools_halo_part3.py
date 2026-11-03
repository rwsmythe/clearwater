"""Tests of ``tools/halo_part3.py`` (WP5.7 Part 3): synthetic frames on the CPU, no footage.

The V3 mode is checked against WP4.2's own module: its predicates are the suite's objects, its
figures equal ``_v3``'s on the same legs, the switch reaches both legs and is restored, and the
clips it builds equal the ``clips`` fixture's (``slow``: two lossless encodes). The N6 row runs
the bench inside the switch (the bench faked). The whole-set batch is checked on synthetic
items: the edge-band scan, the photo and video paths, the staged publication and the sheet.
"""

from __future__ import annotations

import csv
import json
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest
from scipy import ndimage

import halo_part3 as p3
import halo_probe as hp
import test_wp42_v3_product as wp42
from clearwater.interfaces import ColorDescription, Image
from clearwater.io.photo.png import write_png
from clearwater.methods import AncutiFusionMethod
from clearwater.methods import ancuti_fusion as product_ancuti
from clearwater.methods import fusion as product_fusion
from local_config import LocalConfig

wp42_clips = wp42.clips  # WP4.2's two fixtures, registered here under these names
wp42_ad14_mask = wp42.ad14_mask

SRGB = ColorDescription("bt709", "srgb", "identity", "full", 8, False, None)
ORIGINAL = (
    product_fusion.NORMALISATION_RANGE_FLOOR,
    product_ancuti.fusion_inputs,
    hp.fusion_inputs,
)


def _unswitched() -> bool:
    """True when every attribute the candidate's switches patch holds its original object."""
    floor, inputs, probe_inputs = ORIGINAL
    return (
        product_fusion.NORMALISATION_RANGE_FLOOR is floor
        and product_ancuti.fusion_inputs is inputs
        and hp.fusion_inputs is probe_inputs
    )


def _scene(height: int = 160, width: int = 220, *, seed: int = 7) -> np.ndarray:
    """Water with a gentle gradient and a dark disc (soft edge), a little noise."""
    yy, xx = np.mgrid[0:height, 0:width].astype(np.float64)
    rgb = np.stack([0.25 + 0.0004 * xx, 0.5 + 0.0003 * yy, 0.55 + 0.0002 * xx], axis=2)
    disc = np.hypot(xx - width * 0.6, yy - height / 2) <= height * 0.25
    rgb[disc] = [0.12, 0.2, 0.22]
    rgb = ndimage.gaussian_filter(rgb, (1.0, 1.0, 0))
    rgb = rgb + np.random.default_rng(seed).normal(0, 0.002, rgb.shape)
    return np.ascontiguousarray(rgb.clip(0, 1), dtype=np.float32)


def _image(pixels: np.ndarray) -> Image:
    return Image(pixels=pixels, device="cpu", color=SRGB, orientation_applied=True)


@pytest.fixture
def working(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A local configuration in ``tmp_path``; returns its working folder."""
    footage = tmp_path / "footage"
    footage.mkdir()
    work = tmp_path / "work"
    (work / "wp5.7").mkdir(parents=True)
    config = LocalConfig(footage_path=footage, working_path=work)
    monkeypatch.setattr(p3, "load_local_config", lambda path=None: config)
    monkeypatch.setattr(
        p3.headless_export, "configured_footage_folder", lambda config=None: footage
    )
    return work


# --- V3 -----------------------------------------------------------------------------------------


def _figures(clip: str, method: str, *, shift: float = 0.0) -> dict[str, Any]:
    """``_v3``-shaped figures equal to the record (``shift`` added to the first ratio)."""
    record = p3.V3_RECORD[(clip, method)]
    ratios = np.array(record["ratios"], dtype=np.float64)
    ratios[0] += shift
    return {
        "ad14_unsmoothed": record["ad14_unsmoothed"],
        "ad14_smoothed": record["ad14_smoothed"],
        "raw_ad14_smoothed": record["ad14_smoothed"],
        "raw_planted_ad14": 1.0,
        "v3_unsmoothed": np.ones(4),
        "v3_smoothed": ratios,
        "v3_planted": np.ones(4),
        "ratios": dict(zip(wp42.MEASURES, ratios.round(3).tolist(), strict=True)),
    }


def test_suite_is_the_wp42_module_itself() -> None:
    modules = p3.suite()
    assert modules.wp42 is wp42
    assert modules.wp42._v3 is wp42._v3 and modules.wp42._v3_holds is wp42._v3_holds
    assert modules.wp42._ad14_holds is wp42._ad14_holds
    assert modules.plugin.SampleProvider.__module__ == "fixture_plugin"


def test_verdict_reads_the_suites_predicates(monkeypatch: pytest.MonkeyPatch) -> None:
    modules = p3.suite()
    jitter = _figures("jitter", "c3")
    assert p3.v3_verdict(modules, "jitter", jitter)["verdict"] == "PASS"
    at_bound = {**jitter, "v3_smoothed": np.full(4, 0.25)}
    assert p3.v3_verdict(modules, "jitter", at_bound)["verdict"] == "PASS"
    over = {**jitter, "v3_smoothed": np.array([0.1, 0.1, 0.1, 0.26])}
    assert p3.v3_verdict(modules, "jitter", over)["checks"]["v3_holds"] is False
    ad14 = _figures("ad14", "c3")
    assert p3.v3_verdict(modules, "ad14", {**ad14, "raw_ad14_smoothed": 0.49999})["verdict"] == (
        "PASS"
    )
    assert p3.v3_verdict(modules, "ad14", {**ad14, "raw_ad14_smoothed": 0.5})["verdict"] == "FAIL"
    # ad14's V3 ratio over 25 % (b* 0.401) is recorded, not asserted: PASS on AD-14 alone
    assert p3.v3_verdict(modules, "ad14", ad14)["v3_within_25_percent"] is False
    # The bounds are the suite's objects, not retyped: replacing them changes the verdicts.
    monkeypatch.setattr(wp42, "_v3_holds", lambda smoothed, unsmoothed: False)
    monkeypatch.setattr(wp42, "_ad14_holds", lambda figure: True)
    assert p3.v3_verdict(modules, "jitter", jitter)["checks"]["v3_holds"] is False
    planted = p3.v3_verdict(modules, "ad14", ad14)["checks"]["planted_control_refused"]
    assert planted is False


def _fake_legs(monkeypatch: pytest.MonkeyPatch, calls: list[dict[str, Any]]) -> None:
    """Replace WP4.2's legs with seeded regions; each call records the switch state."""
    rng = np.random.default_rng(3)
    smoothed = [rng.random((50, 3)).astype(np.float32) for _ in range(90)]
    unsmoothed = [rng.random((50, 3)).astype(np.float32) for _ in range(90)]

    def smoothed_export(clip: Path, method: str, mask: Any, folder: Path) -> Any:
        calls.append({"leg": "smoothed", "unswitched": _unswitched()})
        return smoothed, folder / "out.mp4"

    def unsmoothed_leg(clip: Path, method: str, mask: Any, folder: Path) -> Any:
        calls.append({"leg": "unsmoothed", "unswitched": _unswitched()})
        return unsmoothed

    monkeypatch.setattr(wp42, "_smoothed_export", smoothed_export)
    monkeypatch.setattr(wp42, "_unsmoothed", unsmoothed_leg)
    monkeypatch.setattr(wp42, "_encoded", lambda output, mask: smoothed)


def test_measure_v3_at_the_shipped_defaults_equals_the_wp42_helper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[dict[str, Any]] = []
    _fake_legs(monkeypatch, calls)
    mask = np.ones(50, dtype=bool)
    ours = p3.measure_v3(p3.suite(), Path("c.mp4"), "c3", mask, tmp_path / "a", hp.Switches())
    theirs = wp42._v3(Path("c.mp4"), "c3", mask, tmp_path)
    assert ours.keys() == theirs.keys()
    for key, value in theirs.items():
        np.testing.assert_array_equal(
            np.asarray(ours[key], dtype=object), np.asarray(value, dtype=object)
        )
    assert all(call["unswitched"] for call in calls)


def test_the_switch_reaches_both_v3_legs_and_is_restored(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[dict[str, Any]] = []
    _fake_legs(monkeypatch, calls)
    switches = hp.parse_switches([p3.CANDIDATE, "range_floor=0.05"])
    p3.measure_v3(
        p3.suite(), Path("c.mp4"), "c3", np.ones(50, dtype=bool), tmp_path / "a", switches
    )
    assert [c["leg"] for c in calls] == ["smoothed", "unsmoothed"]
    assert not any(call["unswitched"] for call in calls)
    assert _unswitched()

    def failing(*args: Any) -> Any:
        assert not _unswitched()
        raise RuntimeError("leg failed")

    monkeypatch.setattr(wp42, "_unsmoothed", failing)
    with pytest.raises(RuntimeError, match="leg failed"):
        p3.measure_v3(
            p3.suite(), Path("c.mp4"), "c3", np.ones(50, dtype=bool), tmp_path / "b", switches
        )
    assert _unswitched()


def test_the_switch_changes_a_render_made_inside_a_v3_leg(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The legs render through the product's method by module lookup: a render made inside the
    # candidate's measure differs from the shipped one and equals the switched render.
    method = AncutiFusionMethod("c3")
    params = hp.resolve_parameters(method, [])
    image = _image(_scene())
    statistics = hp.photo_statistics(method, image, params)
    shipped = method.render(image, params, statistics).pixels
    seen: list[np.ndarray] = []

    _fake_legs(monkeypatch, [])
    legs = wp42._smoothed_export

    def smoothed_export(clip: Path, method_id: str, mask: Any, folder: Path) -> Any:
        seen.append(method.render(image, params, statistics).pixels)
        return legs(clip, method_id, mask, folder)

    monkeypatch.setattr(wp42, "_smoothed_export", smoothed_export)
    switches = hp.parse_switches([p3.CANDIDATE])
    p3.measure_v3(p3.suite(), Path("c.mp4"), "c3", np.ones(4, bool), tmp_path / "a", switches)
    with hp.applied(switches):
        switched = method.render(image, params, statistics).pixels
    assert float(np.abs(seen[0] - shipped).max()) > 1e-3
    np.testing.assert_array_equal(seen[0], switched)


def test_reproduction_tolerance_is_one_unit_in_the_last_printed_place() -> None:
    modules = p3.suite()
    assert p3.reproduction(modules, "jitter", "c3", _figures("jitter", "c3"))["reproduces"]
    near = _figures("jitter", "c3", shift=0.0009)
    near["ratios"]["L*"] = round(p3.V3_RECORD[("jitter", "c3")]["ratios"][0] + 0.0009, 4)
    assert p3.reproduction(modules, "jitter", "c3", near)["reproduces"]
    far = _figures("jitter", "c3")
    far["ratios"]["L*"] = round(p3.V3_RECORD[("jitter", "c3")]["ratios"][0] + 0.0011, 4)
    assert not p3.reproduction(modules, "jitter", "c3", far)["reproduces"]
    ad14 = {**_figures("ad14", "c3"), "ad14_smoothed": 0.0102 + 0.00011}
    assert not p3.reproduction(modules, "ad14", "c3", ad14)["reproduces"]


@pytest.mark.parametrize("reproduces", [True, False])
def test_run_v3_stops_before_the_candidate_unless_the_record_reproduces(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, reproduces: bool
) -> None:
    measured: list[tuple[str, str, bool]] = []

    def measure(modules: Any, clip: Path, method: str, mask: Any, folder: Path, sw: Any) -> Any:
        name = clip.stem
        measured.append((name, method, sw.active))
        return _figures(name, method, shift=0.0 if reproduces or sw.active else 0.01)

    monkeypatch.setattr(
        p3, "build_clips", lambda m, f, s: {c: Path(c + ".mp4") for c in p3.V3_CLIPS}
    )
    monkeypatch.setattr(p3, "v3_masks", lambda m, s: {c: None for c in p3.V3_CLIPS})
    monkeypatch.setattr(p3, "measure_v3", measure)
    switches = hp.parse_switches([p3.CANDIDATE])
    record, status = p3.run_v3(p3.suite(), tmp_path, switches, wp42.METHODS, lambda s: Path(s))
    shipped = [m for m in measured if not m[2]]
    assert len(shipped) == 4
    if reproduces:
        assert status == 0 and len(measured) == 8 and "stop" not in record
        table = p3.v3_table(record)
        assert table.count("| shipped |") == 4 and table.count("| candidate |") == 4
    else:
        assert status == p3.V3_STOP_EXIT and len(measured) == 4 and "STOP" in record["stop"]


# --- N6 -----------------------------------------------------------------------------------------


def test_counted_inputs_counts_the_calls_and_restores() -> None:
    method = AncutiFusionMethod("c3")
    params = hp.resolve_parameters(method, [])
    image = _image(_scene())
    statistics = hp.photo_statistics(method, image, params)
    with p3.counted_inputs() as counter:
        method.render(image, params, statistics)
    assert counter == {"calls": 1, "clip_in_effect": False} and _unswitched()
    with hp.applied(hp.parse_switches([p3.CANDIDATE])), p3.counted_inputs() as counter:
        method.render(image, params, statistics)
        method.analyze("fusion", image, params, statistics)
    assert counter == {"calls": 2, "clip_in_effect": True} and _unswitched()


@pytest.mark.parametrize("setting", p3.N6_SETTINGS)
def test_run_n6_runs_the_bench_of_record_inside_the_switch(
    working: Path, monkeypatch: pytest.MonkeyPatch, setting: str
) -> None:
    method = AncutiFusionMethod("c3")
    params = hp.resolve_parameters(method, [])
    image = _image(_scene())
    statistics = hp.photo_statistics(method, image, params)
    seen: dict[str, Any] = {}

    def bench_main(argv: list[str]) -> int:
        seen["argv"] = argv
        seen["unswitched"] = hp.fusion_inputs is ORIGINAL[2]  # the counter wraps the method's
        method.render(image, params, statistics)  # the engine's render, by module lookup
        folder = working / argv[argv.index("--subdir") + 1]
        (folder / "export-bench-GX011627-1.json").write_text("{}", encoding="utf-8")
        return 0

    monkeypatch.setattr(p3.export_bench, "main", bench_main)
    assert p3.run_n6(setting, "wp5.7/part3/n6", keep=False) == 0
    assert seen["argv"] == [
        "run", "GX011627", "--runs", "1", "--device-frames", "--subdir", "wp5.7/part3/n6",
    ]  # fmt: skip
    assert seen["unswitched"] is (setting == "shipped") and _unswitched()
    (sidecar,) = (working / "wp5.7" / "part3" / "n6").glob("n6-*.json")
    record = json.loads(sidecar.read_text(encoding="utf-8"))
    assert record["records"] == ["export-bench-GX011627-1.json"]
    assert record["fusion_inputs_calls"] == 1
    assert record["clip_in_effect"] is (setting == "candidate")


def _n6_run(folder: Path, index: int, setting: str, rate: float, *, calls: int = 700) -> None:
    name = f"export-bench-GX011627-{index}.json"
    run = {
        "ok": True,
        "frames": 681,
        "source_frames": 681,
        "wall_s": rate * 681 / (30000 / 1001) * 60 / 60,
        "total": {"min_per_min": rate},
        "memory_check": {"passes": True},
        "nvenc_proof": {"tied": True},
    }
    (folder / name).write_text(json.dumps({"runs": [run]}), encoding="utf-8")
    sidecar = {
        "setting": setting,
        "started": f"2026-11-03T00:0{index}:00+00:00",
        "export_bench_exit": 0,
        "records": [name],
        "fusion_inputs_calls": calls,
        "clip_in_effect": setting == "candidate",
    }
    (folder / f"n6-{setting}-{index}.json").write_text(json.dumps(sidecar), encoding="utf-8")


@pytest.mark.parametrize(("factor", "stop"), [(1.05, False), (1.12, True)])
def test_n6_summary_medians_effect_pairs_and_the_stop(
    tmp_path: Path, factor: float, stop: bool
) -> None:
    shipped = [10.9, 11.0, 10.8]
    for index, rate in enumerate(shipped):
        _n6_run(tmp_path, 2 * index, "shipped", rate)
        _n6_run(tmp_path, 2 * index + 1, "candidate", rate * factor)
    summary = p3.n6_summary(tmp_path)
    assert summary["valid"] and summary["medians"]["shipped"] == 10.9
    assert summary["effect"] == pytest.approx(factor - 1.0)
    assert summary["pair_ratios"] == pytest.approx([factor] * 3)
    assert summary["stop"] is stop
    assert ("STOP" in p3.n6_text(summary)) is stop


def test_n6_summary_refuses_a_run_the_switch_did_not_reach(tmp_path: Path) -> None:
    _n6_run(tmp_path, 0, "shipped", 10.9)
    _n6_run(tmp_path, 1, "candidate", 11.0, calls=0)
    assert not p3.n6_summary(tmp_path)["valid"]


# --- the edge-band scan -------------------------------------------------------------------------


def test_scan_finds_a_planted_ring_and_no_band_on_a_monotonic_remap() -> None:
    source = _scene(seed=1)
    height, width = source.shape[:2]
    yy, xx = np.mgrid[0:height, 0:width]
    distance = np.hypot(xx - width * 0.6, yy - height / 2) - height * 0.25
    ring = 0.08 * np.exp(-0.5 * ((distance - 4.0) / 1.5) ** 2)  # bright, on the water side
    shipped = (source + ring[..., None]).clip(0, 1).astype(np.float32)
    candidate = (source**0.8).astype(np.float32)
    scan = p3.scan_pair(source, shipped, candidate, sigma_px=2.0)
    assert scan["points"] > 0 and len(scan["sides"]) == 2 * scan["points"]
    rings = scan["summary"]["shipped"]
    assert rings["band"] >= 1 and rings["max_qualifying_band"] > 0.1
    assert scan["summary"]["candidate"]["band"] == 0
    assert scan["summary"]["candidate"]["max_qualifying_band"] == 0.0


def test_scan_points_are_strongest_first_one_per_cell_and_inside_the_margin() -> None:
    luma = hp.luma(_scene(seed=2))
    points, half = p3.scan_points(luma, 2.0)
    again, _ = p3.scan_points(luma, 2.0)
    assert points == again and 0 < len(points) <= p3.SCAN_POINTS and half == 16
    cells = {(int(y) // half, int(x) // half) for x, y, _, _ in points}
    assert len(cells) == len(points)
    margin = half + p3.SCAN_HALF_WIDTH + 2
    for x, y, ux, uy in points:
        assert margin <= x < luma.shape[1] - margin and margin <= y < luma.shape[0] - margin
        assert abs(np.hypot(ux, uy) - 1.0) < 1e-9
    assert p3.scan_points(luma[:20, :20], 2.0) == ([], 16)


# --- the whole set ------------------------------------------------------------------------------


def _pack(folder: Path, *, drop_from_sheet: str | None = None) -> Path:
    """A pack with 120 other done items, the six halo items and two refused ones."""
    names = [f"IMG_{i:04d}" for i in range(70)] + [f"GX{i:06d}" for i in range(50)]
    entries = [
        {"item": n, "group": "P-A" if n.startswith("IMG") else "V-S", "status": "done",
         "kind": "photo" if n.startswith("IMG") else "video", "source_name": n + ".x"}
        for n in [*names[:10], *p3.HALO_ITEMS, *names[10:]]
    ]  # fmt: skip
    entries += [{"item": f"R{i}", "status": "refused", "kind": "video"} for i in range(2)]
    (folder / "records").mkdir(parents=True)
    (folder / "records" / "pack.json").write_text(json.dumps({"items": entries}), "utf-8")
    with (folder / "review-sheet.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["item", "group"])
        for entry in entries:
            if entry["status"] == "done" and entry["item"] != drop_from_sheet:
                writer.writerow([entry["item"], entry.get("group")])
    return folder


def test_wholeset_items_are_the_judged_items_minus_the_six(tmp_path: Path) -> None:
    items = p3.wholeset_items(_pack(tmp_path / "a"))
    assert len(items) == 120 and not {i["item"] for i in items} & set(p3.HALO_ITEMS)
    assert items[0]["item"] == "IMG_0000" and items[10]["item"] == "IMG_0010"
    with pytest.raises(hp.ProbeError, match="review sheet"):
        p3.wholeset_items(_pack(tmp_path / "b", drop_from_sheet="IMG_0003"))


def test_item_source_reads_the_excerpt_the_pack_cut(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(p3.hp, "find_footage_photo", lambda stem, root: root / f"photo-{stem}")
    monkeypatch.setattr(p3, "find_footage_file", lambda stem, root: root / f"video-{stem}")
    footage, pack = tmp_path / "f", tmp_path / "p"
    photo = {"kind": "photo", "source_name": "IMG_1.HEIC"}
    cut = {
        "kind": "video",
        "source_name": "GX1.mp4",
        "excerpt": {"excerpt": True, "name": "GX1.mp4"},
    }
    whole = {"kind": "video", "source_name": "GX2.mp4", "excerpt": {"excerpt": False}}
    assert p3.item_source(photo, pack, footage) == footage / "photo-IMG_1"
    assert p3.item_source(cut, pack, footage) == pack / "excerpts" / "GX1.mp4"
    assert p3.item_source(whole, pack, footage) == footage / "video-GX2"


def test_process_photo_renders_both_ways_and_restores(tmp_path: Path) -> None:
    source = tmp_path / "scene.png"
    write_png(source, _scene(), bit_depth=16, icc=None, exif=None, provenance_json=None)
    folder = tmp_path / "item"
    folder.mkdir()
    method = AncutiFusionMethod("c3")
    switches = hp.parse_switches([p3.CANDIDATE])
    run = p3.process_photo(source, method, switches, folder, force_cpu=True)
    assert _unswitched()
    (frame,) = run["frames"]
    assert frame["whole_image"]["mean_abs_difference"] > 0.0
    assert frame["edge_scan"]["points"] > 0
    shipped, candidate = run["statistics"]["shipped"], run["statistics"]["candidate"]
    assert not np.array_equal(
        shipped["fusion"]["saliency_means"], candidate["fusion"]["saliency_means"]
    )
    assert {p.name for p in folder.iterdir()} == {"photo-shipped.png", "photo-candidate.png"}
    assert set(run["walls_s"]) == {
        "shipped_statistics_and_render", "shipped_render",
        "candidate_statistics_and_render", "candidate_render",
    }  # fmt: skip


def _fake_video(monkeypatch: pytest.MonkeyPatch, engines: list[Any]) -> None:
    """Five frames of the scene; an analysis that measures the proxy-free photo statistics."""
    method = AncutiFusionMethod("c3")
    pixels = _scene()
    video = SimpleNamespace(height=160, width=220, time_base=Fraction(1, 30), nb_frames=5)
    probe = SimpleNamespace(video=video, faults=(), path=Path("clip.mp4"))

    class Source:
        def probe(self, path: Path) -> SimpleNamespace:
            return probe

        def frames(self, probe: object, *, hw_decode: bool = False) -> Any:
            for pts in range(5):
                yield SimpleNamespace(
                    pts_ticks=pts, pixels=pixels, color=SRGB, orientation_applied=True
                )

    class Engine:
        def __init__(self, **kwargs: Any) -> None:
            self.params = kwargs["params"]
            self.store = SimpleNamespace(axis=lambda: list(range(5)))
            self.schema_hash = "h"
            self.statistics: Any = None
            self.unswitched: bool | None = None
            engines.append(self)

        def analysis_job(self) -> Any:
            def job(progress: Any) -> Any:
                self.unswitched = _unswitched()
                self.statistics = hp.photo_statistics(method, _image(pixels), self.params)
                return SimpleNamespace(ok=True, failure=None)

            return job

        def smoothed_record(self, pts: int, *, schema_hash: str) -> Any:
            return self.statistics

    monkeypatch.setattr(p3, "FFmpegVideoSource", Source)
    monkeypatch.setattr(p3, "AnalysisEngine", Engine)
    monkeypatch.setattr(p3, "DiskProxyCache", lambda folder: None)
    monkeypatch.setattr(p3, "cache_key", lambda path: "key")
    monkeypatch.setattr(p3, "expected_frames", lambda probe: 5)


def test_process_video_analyses_twice_and_renders_the_still_frames(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    engines: list[Any] = []
    _fake_video(monkeypatch, engines)
    folder = tmp_path / "item"
    folder.mkdir()
    renders: list[bool] = []
    timed = p3._timed_render

    def recorded(*args: Any) -> Any:
        renders.append(_unswitched())
        return timed(*args)

    monkeypatch.setattr(p3, "_timed_render", recorded)
    stills = [{"fraction": 0.1, "source_pts_s": 0.0}, {"fraction": 0.9, "source_pts_s": 0.12}]
    run = p3.process_video(
        Path("clip.mp4"),
        AncutiFusionMethod("c3"),
        hp.parse_switches([p3.CANDIDATE]),
        folder,
        stills=stills,
        cache_dir=tmp_path / "cache",
        force_cpu=True,
    )
    assert [e.unswitched for e in engines] == [True, False] and _unswitched()
    assert renders == [True, False, True, False]  # each frame: shipped unswitched, then candidate
    assert [f["pts_ticks"] for f in run["frames"]] == [0, 4]
    assert [f["tag"] for f in run["frames"]] == ["f10", "f90"]
    assert all(f["whole_image"]["mean_abs_difference"] > 0 for f in run["frames"])
    movement = run["statistics_movement"]
    assert movement["input2_saliency_max_abs"] > 0
    first_row = movement["statistics"]["fusion.saliency_means"]
    assert first_row["max_abs"] == pytest.approx(movement["input2_saliency_max_abs"])
    assert movement["statistics"]["white_balance.gains"]["max_abs"] == 0.0
    assert {p.name for p in folder.iterdir()} == {
        "f10-shipped.png", "f10-candidate.png", "f90-shipped.png", "f90-candidate.png",
    }  # fmt: skip


def test_run_item_publishes_on_success_skips_done_items_and_keeps_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(p3, "item_source", lambda item, pack, footage: Path("x.png"))

    def ok(path: Path, method: Any, switches: Any, folder: Path, *, force_cpu: bool) -> Any:
        (folder / "photo-shipped.png").write_bytes(b"x")
        return {"kind": "photo", "walls_s": {}, "frames": []}

    monkeypatch.setattr(p3, "process_photo", ok)
    items = tmp_path / "items"
    item = {"item": "IMG_1", "group": "P-A", "kind": "photo"}
    switches = hp.parse_switches([p3.CANDIDATE])
    assert p3.run_item(item, tmp_path, tmp_path, items, tmp_path / "c", switches) == "done"
    record = json.loads((items / "IMG_1" / "IMG_1.json").read_text(encoding="utf-8"))
    assert record["candidate"] == switches.describe() and record["method"] == "c3"
    assert p3.run_item(item, tmp_path, tmp_path, items, tmp_path / "c", switches) == "skipped"

    def broken(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("decode failed")

    monkeypatch.setattr(p3, "process_photo", broken)
    other = {**item, "item": "IMG_2"}
    result = p3.run_item(other, tmp_path, tmp_path, items, tmp_path / "c", switches)
    assert result == "FAILED: RuntimeError: decode failed"
    assert not (items / "IMG_2").exists() and len(list(items.glob(".IMG_2.failed-*"))) == 1


def _summary(name: str, kind: str, change: float, moved: float | None) -> dict[str, Any]:
    return {
        "item": name,
        "kind": kind,
        "mean_abs_difference": change,
        "input2_saliency_max_abs": moved,
    }


def test_select_contact_reserves_the_videos_whose_statistics_move_most() -> None:
    summaries = [_summary(f"V{i}", "video", 0.001 * i, float(i)) for i in range(8)]
    summaries += [_summary(f"P{i:02d}", "photo", 0.01 * i, None) for i in range(30)]
    chosen = p3.select_contact(summaries)
    assert chosen[:5] == ["V7", "V6", "V5", "V4", "V3"]
    assert chosen[5:] == [f"P{i:02d}" for i in range(29, 14, -1)]
    assert len(chosen) == p3.CONTACT_ITEMS


def test_build_sheet_from_item_records(working: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    engines: list[Any] = []
    _fake_video(monkeypatch, engines)
    out = working / "wp5.7" / "part3" / "wholeset"
    items = out / "items"
    items.mkdir(parents=True)
    source = working / "scene.png"
    write_png(source, _scene(), bit_depth=16, icc=None, exif=None, provenance_json=None)
    monkeypatch.setattr(p3, "item_source", lambda item, pack, footage: source)
    switches = hp.parse_switches([p3.CANDIDATE])
    for item in (
        {"item": "IMG_1", "group": "P-A", "kind": "photo"},
        {"item": "GX1", "group": "V-S", "kind": "video", "stills": []},
    ):
        result = p3.run_item(item, working, working, items, working / "c", switches, force_cpu=True)
        assert result == "done"
    record = p3.build_sheet(out, working)
    assert record["contact"] == ["GX1", "IMG_1"]
    (sheet,) = out.glob("sheet-*")
    assert {p.suffix for p in sheet.iterdir()} == {".html", ".json", ".tsv", ".png"}
    page = (sheet / "contact-sheet.html").read_text(encoding="ascii")
    assert "GX1" in page and page.count("(crop missing)") == 2 * len(p3.UNDECIDED_LINES)
    rows = (sheet / "summary.tsv").read_text(encoding="ascii").splitlines()
    assert len(rows) == 3


def test_main_refuses_outputs_outside_part3(working: Path) -> None:
    assert p3.main(["v3", "--out", str(working / "elsewhere")]) == 2
    assert p3.main(["n6", "--setting", "shipped", "--subdir", "wp5.7/other"]) == 2


@pytest.mark.slow
@pytest.mark.usefixtures("ffmpeg_tools")
def test_build_clips_and_masks_equal_wp42s_fixtures(
    tmp_path: Path,
    sample: Any,
    wp42_clips: dict[str, Path],
    wp42_ad14_mask: np.ndarray,
) -> None:
    # The clips are built by a copy of WP4.2's ``clips`` fixture body (pytest refuses a direct
    # call of a fixture): the result must equal the fixture's, frame for frame, and the masks.
    modules = p3.suite()
    ours = p3.build_clips(modules, tmp_path / "clips", sample)
    for name in p3.V3_CLIPS:
        mine, theirs = wp42._decoded(ours[name]), wp42._decoded(wp42_clips[name])
        assert len(mine) == len(theirs) == 90
        for a, b in zip(mine, theirs, strict=True):
            assert a.pts_ticks == b.pts_ticks
            np.testing.assert_array_equal(a.pixels, b.pixels)
    masks = p3.v3_masks(modules, sample)
    np.testing.assert_array_equal(masks["ad14"], wp42_ad14_mask)
    np.testing.assert_array_equal(masks["jitter"], wp42._jitter_mask())


def test_nearest_crop_reads_the_probe_tag_of_the_nearest_frame(tmp_path: Path) -> None:
    for name in ("t0022.155-output.png", "t0022.189-output.png", "t0022.155-output-marked.png"):
        (tmp_path / name).write_bytes(b"x")
    assert p3.nearest_crop(tmp_path, 22.1555).name == "t0022.155-output.png"
    assert p3.nearest_crop(tmp_path, 22.19).name == "t0022.189-output.png"
    assert not p3.nearest_crop(tmp_path, 23.0).exists()


def test_scan_regressions_lists_the_other_items_whose_scan_rises() -> None:
    def item(name: str, before: tuple[int, float], after: tuple[int, float]) -> dict[str, Any]:
        scan = [{"band": n, "max_qualifying_band": m} for n, m in (before, after)]
        return {"item": name, "scan_shipped": scan[0], "scan_candidate": scan[1]}

    summaries = [
        item("A", (1, 0.3), (2, 0.3)),
        item("B", (1, 0.3), (1, 0.4)),
        item("C", (2, 0.5), (0, 0.0)),
        item("D", (0, 0.0), (1, 0.2)),
    ]
    assert p3.scan_regressions(summaries, chosen=["D"]) == ["A", "B"]
