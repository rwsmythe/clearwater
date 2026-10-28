"""WP4.1 headless runner (``tools/headless_export.py``): surface, refusals, cancel, records.

Covers task 5 and the register rows the runner touches: kind routing as the interface's (S3, with
the ``gui`` equality pin); settings and parameter sources (question 6, S7); exit statuses 0, 1
and 2 (question 5, S5); the schema-1 record with file names only; the footage refusals
(question 9, DR-37 (c)); no PySide6 in the runner's process and no CuPy with ``--force-cpu``; a
library cancel and Ctrl-C (D44, D45); one job at a time in order (DR-62); damaged photos as
failed items (DR-6, D81); the Windows device-name refusal verbatim (DR-35 (a)); and a video in
WP4.1 failing with ``UNAVAILABLE_TEXT`` (question 4).
"""

from __future__ import annotations

import json
import shutil
import signal
import subprocess
import sys
import threading
from pathlib import Path

import pytest

import headless_export as he
from clearwater.app import composition
from clearwater.config import new_parameter_set, save_settings
from clearwater.interfaces import JobResult, Settings
from clearwater.jobs.export_seam import CANCELLED, UNAVAILABLE_TEXT

TOOLS = Path(he.__file__).parent
STILL = "jpeg-gradient-srgb"


@pytest.fixture
def out(tmp_path: Path) -> Path:
    """An empty output folder under the test's temporary folder."""
    folder = tmp_path / "out"
    folder.mkdir()
    return folder


@pytest.fixture
def no_footage(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make ``main`` see no configured footage folder (the run's own check is tested apart)."""
    monkeypatch.setattr(he, "configured_footage_folder", lambda config=None: None)


def _copy(sample, sample_id: str, folder: Path, name: str | None = None) -> Path:
    source = sample(sample_id)
    target = folder / (name or source.name)
    shutil.copyfile(source, target)
    return target


def _main(*args: object, exports=None) -> int:
    return he.main([str(a) for a in args], exports=exports)


def _cpu(out: Path, **changes: object) -> Settings:
    return Settings(output_folder=out, force_cpu=True, **changes)


# --- routing ------------------------------------------------------------------------------------


def test_route_by_extension_as_the_interface_does() -> None:
    assert he.route(Path("a.JPG")) == "photo" and he.route(Path("b.heif")) == "photo"
    assert he.route(Path("c.dng")) == "photo"  # read and refused by the reader (D116)
    assert he.route(Path("GX010001.MP4")) == "video"
    assert he.route(Path("GX010001.THM")).startswith("GX010001.THM is a camera proxy")
    assert he.route(Path("GL010001.lrv")).startswith("GL010001.lrv is a camera proxy")
    assert he.route(Path("notes.txt")) == "notes.txt is not a supported photo or video file."


def test_requests_keep_the_order_and_refuse_through_a_refused_request() -> None:
    params = new_parameter_set("c3", {})
    paths = [Path("a.jpg"), Path("b.THM"), Path("c.mp4"), Path("d.txt")]
    requests = he.requests_for(paths, parameters=params, settings=Settings())
    assert [r.source for r in requests] == paths
    assert [type(r).__name__ for r in requests] == [
        "ExportRequest",
        "RefusedRequest",
        "ExportRequest",
        "RefusedRequest",
    ]
    assert [r.kind for r in requests] == ["photo", "photo", "video", "photo"]
    refused = requests[3]
    assert isinstance(refused, he.RefusedRequest) and refused.refusal == he.route(paths[3])


def test_refused_items_fail_and_the_batch_continues(sample, tmp_path: Path, out: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    good = _copy(sample, STILL, src)
    thm = src / "GX010001.THM"
    thm.write_bytes(b"\xff\xd8 a thumbnail")
    txt = src / "notes.txt"
    txt.write_bytes(b"text")
    requests = he.requests_for(
        [thm, txt, good], parameters=new_parameter_set("c3", {}), settings=_cpu(out)
    )
    record = he.run(requests, footage_folder=None)
    states = [item.state for item in record.report.items]
    assert states == ["failed", "failed", "done"]
    assert record.routes == ("refused", "refused", "photo")
    failures = [item.result.failure for item in record.report.items[:2]]
    assert failures == [he.route(thm), he.route(txt)]
    assert [item.result.device for item in record.report.items[:2]] == ["none", "none"]
    assert sorted(p.name for p in out.iterdir()) == [f"{STILL}_corrected.png"]


@pytest.mark.gui
def test_the_routing_tables_and_texts_equal_the_interfaces() -> None:
    from clearwater.gui import sources

    assert he.PHOTO_SUFFIXES == sources.PHOTO_SUFFIXES
    assert he.VIDEO_SUFFIXES == sources.VIDEO_SUFFIXES
    for name in ("a.jpg", "b.TIFF", "c.mp4", "d.dng", "GX010001.THM", "x.LRV", "e.txt", "f"):
        ours, theirs = he.route(Path(name)), sources.route(Path(name))
        assert ours == (theirs if isinstance(theirs, str) else theirs.text), name


# --- parameters and settings --------------------------------------------------------------------


def test_parameters_defaults_neutral_and_unknown_method() -> None:
    assert he.parameters_for().method == "c3" and he.parameters_for().parameters == {}
    neutral = he.parameters_for("ancuti2018", neutral=True)
    method = composition.correction_methods()["ancuti2018"]
    assert neutral.parameters == {p.name: p.neutral for p in method.parameters}
    with pytest.raises(he.RunnerRefusalError, match="unknown correction method 'c9'"):
        he.parameters_for("c9")


def test_a_parameter_file_is_read_with_its_provenance_dropped(tmp_path: Path) -> None:
    base = new_parameter_set("ancuti2018", {"blue_compensation": True})
    data = json.loads(base.to_json())
    data["source"] = {"name": "x.jpg"}
    data["settings"] = {"device": "GPU"}
    path = tmp_path / "provenance.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    read = he.parameters_for(file=path)
    assert read.method == "ancuti2018" and read.parameters == {"blue_compensation": True}
    assert read.source is None and read.settings is None
    with pytest.raises(he.RunnerRefusalError, match="--method cannot be combined"):
        he.parameters_for("c3", file=path)


@pytest.mark.parametrize(
    ("text", "match"),
    [
        ("{not json", "not a readable parameter file"),
        ("[1, 2]", "not a JSON object"),
        ('{"format_version": 99}', "not a readable parameter file"),
    ],
)
def test_an_unreadable_parameter_file_is_refused(tmp_path: Path, text: str, match: str) -> None:
    path = tmp_path / "p.json"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(he.RunnerRefusalError, match=match):
        he.parameters_for(file=path)


def test_settings_dir_is_loaded_and_flags_overlay_it(
    sample, tmp_path: Path, out: Path, no_footage: None
) -> None:
    folder = tmp_path / "settings"
    save_settings(folder, Settings(output_suffix="_wet", png_bit_depth=8, provenance=False))
    record = tmp_path / "r.json"
    status = _main(
        sample(STILL), "--out", out, "--force-cpu", "--settings-dir", folder,
        "--bit-depth", "16", "--cache-limit-bytes", "123", "--record", record,
    )  # fmt: skip
    assert status == 0
    settings = json.loads(record.read_text(encoding="ascii"))["settings"]
    assert settings["output_suffix"] == "_wet" and settings["provenance"] is False
    assert settings["png_bit_depth"] == 16 and settings["cache_limit_bytes"] == 123
    assert [p.name for p in out.iterdir()] == [f"{STILL}_wet.png"]


# --- exit statuses and the record ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("args", "text"),
    [
        (["--out", "{missing}"], "the --out folder does not exist"),
        (["--out", "{out}", "--suffix", "a/b"], "forbidden characters"),
        (["--out", "{out}", "--method", "c9"], "unknown correction method"),
        (["--out", "{out}", "--parameters", "{params}", "--method", "c3"], "--method cannot"),
        (["--out", "{out}", "--record", "{existing}"], "never overwritten"),
        (["--out", "{out}", "--settings-dir", "{missing}"], "--settings-dir folder does not"),
        (["--out", "{out}", "--cache-limit-bytes", "-1"], "must not be negative"),
    ],
)
def test_a_usage_refusal_exits_2_and_runs_nothing(
    sample, tmp_path: Path, out: Path, capsys, no_footage: None, args: list[str], text: str
) -> None:
    params = tmp_path / "params.json"
    params.write_text(new_parameter_set("c3", {}).to_json(), encoding="utf-8")
    existing = tmp_path / "existing.json"
    existing.write_text("keep", encoding="utf-8")
    values = {"missing": tmp_path / "nope", "out": out, "params": params, "existing": existing}
    status = _main(sample(STILL), *[a.format(**values) for a in args])
    assert status == 2
    assert text in capsys.readouterr().err
    assert list(out.iterdir()) == [] and existing.read_text(encoding="utf-8") == "keep"


@pytest.mark.parametrize(
    "args", [[], ["--out", "x", "--beside-source"], ["--parameters", "p", "--neutral"]]
)
def test_argument_errors_exit_2(sample, args: list[str], no_footage: None, capsys) -> None:
    assert _main(sample(STILL), *args) == 2
    assert "usage:" in capsys.readouterr().err


def test_help_exits_0(capsys) -> None:
    assert he.main(["--help"]) == 0
    assert "--cache-limit-bytes" in capsys.readouterr().out


def test_exit_0_when_all_done_and_1_when_any_failed(
    sample, tmp_path: Path, out: Path, no_footage: None, capsys
) -> None:
    assert _main(sample(STILL), "--out", out, "--force-cpu") == 0
    assert _main(sample(STILL), tmp_path / "missing.jpg", "--out", out, "--force-cpu") == 1
    lines = capsys.readouterr().out.splitlines()
    assert lines[-5:-1] == [
        "Batch of 2: 1 done, 1 failed",
        f"1. {STILL}.jpg: done",
        f"   saved {STILL}_corrected_2.png",
        "2. missing.jpg: failed",
    ]
    assert lines[-1].startswith("   failure: missing.jpg: PhotoReadError: missing.jpg cannot")


def test_the_record_has_schema_1_and_file_names_only(
    sample, tmp_path: Path, out: Path, no_footage: None
) -> None:
    record = tmp_path / "record.json"
    missing = tmp_path / "deep" / "missing.jpg"
    status = _main(
        sample(STILL), missing, tmp_path / "GX010001.MP4", "--out", out, "--force-cpu",
        "--neutral", "--no-provenance", "--record", record,
    )  # fmt: skip
    assert status == 1
    text = record.read_text(encoding="ascii")
    data = json.loads(text)
    assert data["schema"] == 1 and data["tool"] == "headless_export"
    assert data["method"] == "c3" and data["parameters_from"] == "neutral"
    assert data["counts"] == {
        "done": 1,
        "done with warnings": 0,
        "failed": 2,
        "cancelled": 0,
        "not run": 0,
    }
    assert data["cancelled"] is False
    items = data["items"]
    assert [i["source"] for i in items] == [f"{STILL}.jpg", "missing.jpg", "GX010001.MP4"]
    assert [i["kind"] for i in items] == ["photo", "photo", "video"]
    assert items[0]["outputs"] == [f"{STILL}_corrected.png"]
    assert items[0]["device"] == "CPU: forced" and items[0]["failure"] is None
    assert "missing.jpg cannot be read: the file does not exist" in items[1]["failure"]
    assert items[2]["failure"] == UNAVAILABLE_TEXT
    for folder in (tmp_path, sample(STILL).parent, Path.home()):
        for form in (str(folder), str(folder).replace("\\", "\\\\"), folder.as_posix()):
            assert form not in text


# --- footage refusals (question 9) --------------------------------------------------------------


def test_run_refuses_outputs_inside_the_footage_folder(sample, tmp_path: Path) -> None:
    footage = tmp_path / "Footage"
    (footage / "sub").mkdir(parents=True)
    source = _copy(sample, STILL, footage / "sub")
    params = new_parameter_set("c3", {})
    inside_out = he.requests_for([sample(STILL)], parameters=params, settings=_cpu(footage / "sub"))
    with pytest.raises(he.RunnerRefusalError, match="output folder is inside the footage"):
        he.run(inside_out, footage_folder=footage)
    beside = he.requests_for(
        [source], parameters=params, settings=Settings(output_folder=None, force_cpu=True)
    )
    with pytest.raises(he.RunnerRefusalError, match="outputs beside it are refused"):
        he.run(beside, footage_folder=footage)
    assert sorted(p.name for p in (footage / "sub").iterdir()) == [source.name]


def test_inside_is_resolved_and_not_a_name_prefix(tmp_path: Path) -> None:
    footage = tmp_path / "footage"
    footage.mkdir()
    assert he.inside(footage, footage) and he.inside(footage / "a" / ".." / "b.mp4", footage)
    assert not he.inside(tmp_path / "footage2" / "x", footage)
    assert not he.inside(tmp_path / "x", footage)


def test_main_refuses_the_configured_footage_folder(
    sample, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    footage = tmp_path / "footage"
    footage.mkdir()
    source = _copy(sample, STILL, footage)
    monkeypatch.setattr(he, "configured_footage_folder", lambda config=None: footage)
    assert _main(source, "--beside-source", "--force-cpu") == 2
    assert _main(source, "--out", footage, "--force-cpu") == 2
    out = tmp_path / "out"
    out.mkdir()
    assert _main(source, "--out", out, "--force-cpu", "--record", footage / "r.json") == 2
    assert _main(source, "--out", out, "--force-cpu", "--settings-dir", footage) == 2
    err = capsys.readouterr().err
    assert err.count("inside the footage folder") == 4
    assert sorted(p.name for p in footage.iterdir()) == [source.name] and list(out.iterdir()) == []
    assert _main(source, "--out", out, "--force-cpu") == 0  # reading footage is allowed


def test_the_configured_footage_folder_comes_from_the_local_config(tmp_path: Path) -> None:
    assert he.configured_footage_folder(tmp_path / "absent.toml") is None
    footage, work = tmp_path / "f", tmp_path / "w"
    footage.mkdir()
    work.mkdir()
    config = tmp_path / "clearwater.local.toml"
    config.write_text(f"footage_path = '{footage}'\nworking_path = '{work}'\n", encoding="utf-8")
    assert he.configured_footage_folder(config) == footage
    config.write_text("footage_path = [", encoding="utf-8")
    with pytest.raises(he.RunnerRefusalError, match="local configuration cannot be read"):
        he.configured_footage_folder(config)


# --- the process: no PySide6, no CuPy with --force-cpu -------------------------------------------


def test_the_runner_process_loads_no_pyside6_and_no_cupy_when_forced(sample, out: Path) -> None:
    code = (
        "import sys\n"
        f"sys.path.insert(0, {str(TOOLS)!r})\n"
        "import headless_export\n"
        "pyside = sorted(m for m in sys.modules if m.split('.')[0] in ('PySide6', 'shiboken6'))\n"
        f"status = headless_export.main([{str(sample(STILL))!r}, '--out', {str(out)!r},\n"
        "                               '--force-cpu'])\n"
        "bad = sorted(m for m in sys.modules\n"
        "             if m.split('.')[0] in ('PySide6', 'shiboken6', 'cupy', 'cupyx'))\n"
        "print('RESULT', status, ','.join(pyside), ','.join(bad))\n"
    )
    done = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True, timeout=300
    )
    assert done.stdout.splitlines()[-1].split(" ") == ["RESULT", "0", "", ""]
    assert [p.name for p in out.iterdir()] == [f"{STILL}_corrected.png"]


# --- cancel, Ctrl-C, order ----------------------------------------------------------------------


class _Ordered:
    """Wrap an ``ExportJobs`` and record when each job starts and ends, and on which thread."""

    def __init__(self, exports) -> None:
        self.exports = exports
        self.events: list[tuple[str, int, int]] = []

    def job(self, request):
        job = self.exports.job(request)
        index = len({e[1] for e in self.events}) + 1

        def run(progress) -> JobResult:
            self.events.append(("start", index, threading.get_ident()))
            try:
                return job(progress)
            finally:
                self.events.append(("end", index, threading.get_ident()))

        return run


def test_jobs_run_one_at_a_time_in_order_on_the_callers_thread(sample, tmp_path, out) -> None:
    sources = [_copy(sample, STILL, tmp_path, f"p{i}.jpg") for i in range(3)]
    exports = _Ordered(composition.export_jobs())
    params = new_parameter_set("c3", {})
    record = he.run(
        he.requests_for(sources, parameters=params, settings=_cpu(out)),
        exports=exports,
        footage_folder=None,
    )
    assert [item.state for item in record.report.items] == ["done"] * 3
    assert [(kind, index) for kind, index, _ in exports.events] == [
        ("start", 1), ("end", 1), ("start", 2), ("end", 2), ("start", 3), ("end", 3),
    ]  # fmt: skip
    assert {thread for *_, thread in exports.events} == {threading.get_ident()}


@pytest.mark.parametrize(("stage", "first"), [("committed", "done"), ("render", "cancelled")])
def test_a_library_cancel_stops_the_batch(sample, tmp_path, out, stage: str, first: str) -> None:
    sources = [_copy(sample, STILL, tmp_path, f"p{i}.jpg") for i in range(3)]
    progress = he.RunnerProgress()

    def hook(name: str) -> None:
        if name == stage:
            progress.cancel()

    record = he.run(
        he.requests_for(sources, parameters=new_parameter_set("c3", {}), settings=_cpu(out)),
        exports=composition.export_jobs(on_stage=hook),
        progress=progress,
        footage_folder=None,
    )
    assert [item.state for item in record.report.items] == [first, "not run", "not run"]
    expected = ["p0_corrected.png"] if first == "done" else []
    assert sorted(p.name for p in out.iterdir()) == expected  # no partial or temporary file
    assert he.exit_status(record) == 1 and he.record_object(record)["cancelled"] is True
    if first == "cancelled":
        assert record.report.items[0].result.failure is CANCELLED


def test_ctrl_c_cancels_the_batch_and_restores_the_handler(
    sample, tmp_path: Path, out: Path, no_footage: None
) -> None:
    sources = [_copy(sample, STILL, tmp_path, f"p{i}.jpg") for i in range(2)]
    before = signal.getsignal(signal.SIGINT)

    def hook(name: str) -> None:
        if name == "measure":
            signal.raise_signal(signal.SIGINT)

    record = tmp_path / "r.json"
    status = _main(
        *sources, "--out", out, "--force-cpu", "--record", record,
        exports=composition.export_jobs(on_stage=hook),
    )  # fmt: skip
    assert status == 1
    assert [i["state"] for i in json.loads(record.read_text(encoding="ascii"))["items"]] == [
        "cancelled",
        "not run",
    ]
    assert list(out.iterdir()) == []
    assert signal.getsignal(signal.SIGINT) is before


# --- damaged photos, device names, video ---------------------------------------------------------


def test_damaged_photos_are_failed_items_and_the_batch_continues(
    sample, tmp_path: Path, out: Path
) -> None:
    src = tmp_path / "src"
    src.mkdir()
    for sample_id, name in (("jpeg-gradient-srgb", "cut.jpg"), ("heic8-gradient-srgb", "cut.heic")):
        data = sample(sample_id).read_bytes()
        (src / name).write_bytes(data[: len(data) // 2])
    good = _copy(sample, STILL, src)
    requests = he.requests_for(
        [src / "cut.jpg", src / "cut.heic", good],
        parameters=new_parameter_set("c3", {}),
        settings=_cpu(out),
    )
    record = he.run(requests, footage_folder=None)
    assert [item.state for item in record.report.items] == ["failed", "failed", "done"]
    for item, name in zip(record.report.items[:2], ("cut.jpg", "cut.heic"), strict=True):
        assert item.result.failure.startswith(f"{name}: PhotoReadError: {name} cannot be read")
    assert sorted(p.name for p in out.iterdir()) == [f"{STILL}_corrected.png"]


def test_a_suffix_forming_a_device_name_is_refused_verbatim(
    sample, tmp_path: Path, out: Path, no_footage: None
) -> None:
    source = _copy(sample, STILL, tmp_path, "N.jpg")
    record = tmp_path / "r.json"
    assert _main(source, "--out", out, "--force-cpu", "--suffix", "UL", "--record", record) == 1
    item = json.loads(record.read_text(encoding="ascii"))["items"][0]
    assert item["failure"] == (
        "N.jpg: the output name NUL.png is a reserved device name on Windows; "
        "change the output suffix."
    )
    assert list(out.iterdir()) == []


def test_a_video_fails_unavailable_in_wp41(tmp_path: Path, out: Path) -> None:
    video = tmp_path / "GX010001.MP4"
    video.write_bytes(b"not decoded")
    requests = he.requests_for([video], parameters=new_parameter_set("c3", {}), settings=_cpu(out))
    record = he.run(requests, footage_folder=None)
    item = record.report.items[0]
    assert (item.state, item.result.failure, record.routes) == (
        "failed",
        UNAVAILABLE_TEXT,
        ("video",),
    )
    assert list(out.iterdir()) == []
