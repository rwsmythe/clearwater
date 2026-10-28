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
import os
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
from clearwater.config.presets import MAX_PRESET_BYTES
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
        ("[1, 2]", "expected a JSON object"),
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


# --- Reviewer A round 1 (F1-F4) -----------------------------------------------------------------


def _path_forms(folder: Path) -> list[str]:
    """Every spelling of a folder a text could carry, lower-cased (case-insensitive check)."""
    forms = set()
    for path in (folder, folder.resolve()):
        text = str(path)
        spellings = {text, text.replace("\\", "\\\\"), path.as_posix()}
        forms.update(spellings | {he.ascii_text(form) for form in spellings})  # escaped (G2)
    return sorted(form.lower() for form in forms)


def _no_full_path(text: str, folder: Path) -> bool:
    low = text.lower()
    return not any(form in low for form in _path_forms(folder))


def test_f1_a_d87_refusal_reaches_the_record_without_the_folder(
    sample, tmp_path: Path, out: Path, monkeypatch: pytest.MonkeyPatch, no_footage: None, capsys
) -> None:
    from clearwater.jobs import SpaceCheck

    monkeypatch.setattr(
        "clearwater.jobs.export.check_free_space",
        lambda folder, needed: SpaceCheck(folder=folder, needed=needed, free=0, ok=False),
    )
    record = tmp_path / "r.json"
    assert _main(sample(STILL), "--out", out, "--force-cpu", "--record", record) == 1
    failure = json.loads(record.read_text(encoding="ascii"))["items"][0]["failure"]
    assert failure.startswith(f"{STILL}.jpg: Not enough free space in out: need ")
    captured = capsys.readouterr()
    for text in (record.read_text(encoding="ascii"), captured.out, captured.err):
        assert _no_full_path(text, tmp_path)


def test_f1_no_full_path_in_the_process_output_or_the_record(sample, tmp_path: Path) -> None:
    out = tmp_path / "out"
    out.mkdir()
    settings = tmp_path / "settings"
    settings.mkdir()
    (settings / "settings.json").write_text("{not json", encoding="utf-8")  # a WARNING, renamed
    record = tmp_path / "r.json"
    code = (
        "import sys\n"
        f"sys.path.insert(0, {str(TOOLS)!r})\n"
        "import headless_export as he\n"
        "from clearwater.jobs import SpaceCheck\n"
        "import clearwater.jobs.export as export\n"
        "export.check_free_space = lambda f, n: SpaceCheck(folder=f, needed=n, free=0, ok=False)\n"
        "he.configured_footage_folder = lambda config=None: None\n"
        "print('STATUS', he.main(sys.argv[1:]))\n"
    )
    args = [str(sample(STILL)), "--out", str(out), "--force-cpu", "--settings-dir", str(settings)]
    done = subprocess.run(
        [sys.executable, "-c", code, *args, "--record", str(record)],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert "STATUS 1" in done.stdout, done.stderr
    assert "settings file settings" in done.stderr  # the planted WARNING was printed
    assert "Not enough free space in out" in done.stderr + done.stdout
    for text in (done.stdout, done.stderr, record.read_text(encoding="ascii")):
        assert _no_full_path(text, tmp_path)
    missing = subprocess.run(
        [sys.executable, "-c", code, str(sample(STILL)), "--out", str(out),
         "--parameters", str(tmp_path / "absent" / "p.json")],
        capture_output=True, text=True, timeout=300,
    )  # fmt: skip
    assert "STATUS 2" in missing.stdout and "p.json is not a readable parameter" in missing.stderr
    assert _no_full_path(missing.stdout + missing.stderr, tmp_path)


def test_f3_an_unsupported_settings_version_is_a_usage_refusal(
    sample, tmp_path: Path, out: Path, no_footage: None, capsys
) -> None:
    folder = tmp_path / "settings"
    folder.mkdir()
    (folder / "settings.json").write_text('{"format_version": 99}', encoding="utf-8")
    assert _main(sample(STILL), "--out", out, "--settings-dir", folder) == 2
    assert "--settings-dir settings cannot be used" in capsys.readouterr().err
    assert list(out.iterdir()) == []


def test_f2_a_record_that_is_not_json_is_refused(
    sample, tmp_path: Path, out: Path, no_footage: None, capsys
) -> None:
    record = out / f"{STILL}_corrected.png"
    assert _main(sample(STILL), "--out", out, "--force-cpu", "--record", record) == 2
    assert "--record file must end in .json" in capsys.readouterr().err
    assert list(out.iterdir()) == []


def test_f4_a_loaded_suffix_is_validated_before_anything_runs(
    sample, tmp_path: Path, out: Path, no_footage: None, capsys
) -> None:
    folder = tmp_path / "settings"
    save_settings(folder, Settings(output_suffix="a/b"))
    assert _main(sample(STILL), "--out", out, "--force-cpu", "--settings-dir", folder) == 2
    assert "forbidden characters" in capsys.readouterr().err
    assert list(out.iterdir()) == []


# --- Reviewer A round 2 (G1-G7) -----------------------------------------------------------------

WINDOWS = sys.platform == "win32"
EXTENDED = "\\\\?\\"  # the Windows extended-length prefix
LOCAL_SHARE = Path("\\\\localhost\\C$\\")  # the administrative share, where it is reachable


def _extended(path: Path) -> Path:
    return Path(EXTENDED + str(path.resolve()))


def _unc_extended(path: Path) -> Path | None:
    """``path`` on drive C spelled through ``localhost``'s ``C$`` share, extended; None if not."""
    resolved = path.resolve()
    if not WINDOWS or resolved.drive.upper() != "C:" or not LOCAL_SHARE.is_dir():
        return None
    return Path(EXTENDED + "UNC\\localhost\\C$\\" + str(resolved)[3:])


@pytest.mark.skipif(not WINDOWS, reason="the extended-length spellings exist only on Windows")
def test_g1_inside_sees_every_spelling_of_the_same_folder(tmp_path: Path) -> None:
    footage = tmp_path / "footage"
    (footage / "sub").mkdir(parents=True)
    assert he.inside(_extended(footage / "sub"), footage)
    assert he.inside(footage / "sub", _extended(footage))
    assert he.inside(_extended(footage / "sub" / "new.png"), footage)  # need not exist
    assert not he.inside(_extended(tmp_path / "footage2"), footage)
    assert he.plain_path(Path(EXTENDED + "UNC\\server\\share\\x")) == Path("\\\\server\\share\\x")
    assert he.plain_path(Path(EXTENDED + "C:\\x")) == Path("C:\\x")
    assert he.plain_path(Path("C:\\x")) == Path("C:\\x")
    unc = _unc_extended(footage / "sub")
    if unc is not None:  # the share and its extended spelling name the same folder
        assert he.inside(unc, footage)
        assert he.inside(Path(str(unc).replace(EXTENDED + "UNC", "\\")), footage)


@pytest.mark.skipif(not WINDOWS, reason="the extended-length spellings exist only on Windows")
@pytest.mark.parametrize("spelling", ["extended", "unc"])
def test_g1_main_refuses_every_footage_check_through_another_spelling(
    sample, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys, spelling: str
) -> None:
    footage = tmp_path / "footage"
    footage.mkdir()
    source = _copy(sample, STILL, footage)
    spelled = _extended(footage) if spelling == "extended" else _unc_extended(footage)
    if spelled is None:
        pytest.skip("the administrative share of drive C on localhost is not reachable")
    monkeypatch.setattr(he, "configured_footage_folder", lambda config=None: footage)
    out = tmp_path / "out"
    out.mkdir()
    assert _main(spelled / source.name, "--beside-source", "--force-cpu") == 2
    assert _main(source, "--out", spelled, "--force-cpu") == 2
    assert _main(source, "--out", out, "--force-cpu", "--record", spelled / "r.json") == 2
    assert _main(source, "--out", out, "--force-cpu", "--settings-dir", spelled) == 2
    assert capsys.readouterr().err.count("inside the footage folder") == 4
    assert sorted(p.name for p in footage.iterdir()) == [source.name] and list(out.iterdir()) == []
    monkeypatch.setattr(he, "configured_footage_folder", lambda config=None: spelled)
    assert _main(source, "--out", footage, "--force-cpu") == 2  # the configured side spelled
    assert sorted(p.name for p in footage.iterdir()) == [source.name]


@pytest.mark.skipif(not WINDOWS, reason="the extended-length spellings exist only on Windows")
def test_g1_the_redactor_hides_the_extended_spellings(tmp_path: Path) -> None:
    folder = tmp_path / "out"
    folder.mkdir()
    redact = he.Redactor([folder])
    texts = [str(_extended(folder)) + "\\a.png", repr(str(_extended(folder)))]
    unc = _unc_extended(folder)
    if unc is not None:
        share = str(unc).replace(EXTENDED + "UNC", "\\")
        texts += [str(unc), share]
        assert he.Redactor([Path(share)])(str(unc)) == he.Redactor([unc])(share) == "out"
    for text in texts:
        assert _no_full_path(redact(text), tmp_path)


def test_g2_a_non_ascii_folder_is_hidden_in_the_record_and_the_output(
    sample, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, no_footage: None, capsys
) -> None:
    from clearwater.jobs import SpaceCheck

    base = tmp_path / "priv\u00e9 \u6c34"
    out = base / "out"
    out.mkdir(parents=True)
    monkeypatch.setattr(
        "clearwater.jobs.export.check_free_space",
        lambda folder, needed: SpaceCheck(folder=folder, needed=needed, free=0, ok=False),
    )
    record = base / "r.json"
    assert _main(sample(STILL), "--out", out, "--force-cpu", "--record", record) == 1
    failure = json.loads(record.read_text(encoding="ascii"))["items"][0]["failure"]
    assert failure.startswith(f"{STILL}.jpg: Not enough free space in out: need ")
    captured = capsys.readouterr()
    for text in (record.read_text(encoding="ascii"), captured.out, captured.err):
        assert _no_full_path(text, base) and _no_full_path(text, tmp_path)


def test_g3_an_argument_error_names_no_full_path(sample, tmp_path: Path, capsys) -> None:
    out = tmp_path / "priv\u00e9"
    out.mkdir()
    assert _main(sample(STILL), "--out", out, "--bit-depth", out / "x") == 2
    err = capsys.readouterr().err
    assert "argument --bit-depth: invalid int value" in err and err.startswith("usage:")
    assert _no_full_path(err, tmp_path) and _no_full_path(err, out)
    assert _main("--out", out) == 2  # no source: argparse's own message
    assert "the following arguments are required: PATH" in capsys.readouterr().err


def test_g4_every_record_text_field_is_redacted(
    sample, tmp_path: Path, out: Path, no_footage: None
) -> None:
    record = tmp_path / "r.json"
    status = _main(
        sample(STILL), "--out", out, "--force-cpu", "--encoder", out, "--record", record
    )  # fmt: skip
    assert status == 0
    text = record.read_text(encoding="ascii")
    assert json.loads(text)["settings"]["video_encoder"] == "out"
    assert _no_full_path(text, tmp_path)


@pytest.mark.parametrize("fails", ["open", "write"])
def test_g6_a_record_that_cannot_be_written_exits_1_without_a_full_path(
    sample, tmp_path: Path, out: Path, monkeypatch: pytest.MonkeyPatch, no_footage, capsys, fails
) -> None:
    import builtins

    record = tmp_path / "r.json"

    class _Full:
        def __init__(self, handle) -> None:
            self._handle = handle

        def __enter__(self):
            return self

        def __exit__(self, *exc) -> None:
            self._handle.close()

        def write(self, text: str) -> int:
            self._handle.write(text[:10])  # a partial record, then the disk is full
            raise OSError(28, "No space left on device", str(record))

    def full_open(path, mode="r", *args, **kwargs):
        if fails == "open":
            raise OSError(28, "No space left on device", str(path))
        return _Full(builtins.open(path, mode, *args, **kwargs))

    monkeypatch.setattr(he, "open", full_open, raising=False)
    assert _main(sample(STILL), "--out", out, "--force-cpu", "--record", record) == 1
    captured = capsys.readouterr()
    assert "the --record file cannot be written" in captured.err
    assert _no_full_path(captured.out + captured.err, tmp_path)
    assert not record.exists()  # the partial record this run created is removed
    assert sorted(p.name for p in out.iterdir()) == [f"{STILL}_corrected.png"]  # exports kept


def test_g6_a_record_written_by_another_process_is_never_removed(
    sample, tmp_path: Path, out: Path, monkeypatch: pytest.MonkeyPatch, no_footage, capsys
) -> None:
    record = tmp_path / "r.json"

    def theirs(path, mode="r", *args, **kwargs):
        Path(path).write_text("theirs", encoding="ascii")  # appears just before the "x" open
        raise FileExistsError(17, "File exists", str(path))

    monkeypatch.setattr(he, "open", theirs, raising=False)
    assert _main(sample(STILL), "--out", out, "--force-cpu", "--record", record) == 1
    assert record.read_text(encoding="ascii") == "theirs"
    assert "appeared during the run" in capsys.readouterr().err


def test_g7_a_photo_warning_prints_no_tag_value() -> None:
    import logging

    log_filter = he._RedactingFilter(he.Redactor([]))

    def shown(logger: str, msg: str, *args: object) -> str:
        record = logging.LogRecord(logger, logging.WARNING, __file__, 1, msg, args, None)
        assert log_filter.filter(record)
        return record.getMessage()

    exif = "clearwater.io.photo.exif"
    text = shown(exif, "EXIF Orientation %r is not 1 to 8; taken as 1", "PRIVATE_EXIF_VALUE")
    assert text == "EXIF Orientation ... is not 1 to 8; taken as 1"
    text = shown(exif, "%s: the EXIF block is damaged (%s); it is not carried", "a.jpg", "PRIV")
    assert "PRIV" not in text and "damaged" in text
    reader = "clearwater.io.photo.reader"
    text = shown(reader, "%s: TIFF Orientation %r is not 1 to 8; taken as 1", "a.tif", "PRIVATE")
    assert text == "a.tif: TIFF Orientation ... is not 1 to 8; taken as 1"
    assert shown(reader, "%s: alpha channel dropped", "a.png") == "a.png: alpha channel dropped"


def test_g7_a_planted_exif_value_is_not_printed_by_the_runner(tmp_path: Path) -> None:
    import struct

    from PIL import Image

    source = tmp_path / "planted.jpg"
    value = b"PRIVATE_EXIF_VALUE\x00"  # Orientation (0x0112) stored as ASCII text: not 1 to 8
    ifd = struct.pack("<HHHII", 1, 0x0112, 2, len(value), 26) + struct.pack("<I", 0)
    block = b"Exif\x00\x00" + b"II*\x00" + struct.pack("<I", 8) + ifd + value
    Image.new("RGB", (32, 24), (40, 90, 120)).save(source, exif=block)
    out = tmp_path / "out"
    out.mkdir()
    code = (
        "import sys\n"
        f"sys.path.insert(0, {str(TOOLS)!r})\n"
        "import headless_export as he\n"
        "he.configured_footage_folder = lambda config=None: None\n"
        "print('STATUS', he.main(sys.argv[1:]))\n"
    )
    done = subprocess.run(
        [sys.executable, "-c", code, str(source), "--out", str(out), "--force-cpu"],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert "STATUS 0" in done.stdout, done.stderr
    assert "Orientation ... is not 1 to 8" in done.stderr  # the WARNING is printed
    assert "PRIVATE_EXIF_VALUE" not in done.stdout + done.stderr


# --- Reviewer A round 3 (H2, H3, H5) ------------------------------------------------------------


def test_h2_a_repr_of_an_escaped_folder_is_hidden(
    sample, tmp_path: Path, no_footage: None, capsys
) -> None:
    out = tmp_path / "privé" / "out"
    out.mkdir(parents=True)
    text = he.Redactor([out])(he._unknown_method(str(out), {"c3": None}))
    assert text == "unknown correction method 'out'; the methods are c3."
    assert _main(sample(STILL), "--out", out, "--method", out) == 2
    err = capsys.readouterr().err
    assert "unknown correction method 'out'" in err and _no_full_path(err, tmp_path)


def test_h3_the_library_run_prints_its_warnings_redacted(sample, tmp_path: Path) -> None:
    out = tmp_path / "out"
    out.mkdir()
    code = (
        "import sys\n"
        "from pathlib import Path\n"
        f"sys.path.insert(0, {str(TOOLS)!r})\n"
        "import headless_export as he\n"
        "from clearwater.config import new_parameter_set\n"
        "from clearwater.interfaces import Settings\n"
        "from clearwater.jobs import SpaceCheck\n"
        "import clearwater.jobs.export as export\n"
        "export.check_free_space = lambda f, n: SpaceCheck(folder=f, needed=n, free=0, ok=False)\n"
        "settings = Settings(output_folder=Path(sys.argv[2]), force_cpu=True)\n"
        "requests = he.requests_for([Path(sys.argv[1])], parameters=new_parameter_set('c3', {}),\n"
        "                           settings=settings)\n"
        "record = he.run(requests, footage_folder=None)\n"
        "print('STATE', record.report.items[0].state)\n"
    )
    done = subprocess.run(
        [sys.executable, "-c", code, str(sample(STILL)), str(out)],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert "STATE failed" in done.stdout, done.stderr
    assert "Not enough free space in out" in done.stderr  # the batch WARNING was printed
    assert _no_full_path(done.stdout + done.stderr, tmp_path)


def test_h5_a_non_finite_number_anywhere_in_a_parameter_file_is_refused(tmp_path: Path) -> None:
    preset = new_parameter_set("c3", {}).to_dict()
    text = json.dumps({**preset, "settings": {"bad": 0.5}}).replace("0.5", "NaN")
    path = tmp_path / "p.json"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(he.RunnerRefusalError, match=r"p\.json is not a readable parameter file"):
        he.read_parameter_file(path)


# --- round 4: write targets followed through links, the config path, importer parity ------------


def _symlink(target: Path, link: Path, *, directory: bool = False) -> None:
    """Create a symbolic link, or skip the test where this user cannot create one."""
    try:
        os.symlink(target, link, target_is_directory=directory)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"this user cannot create a symbolic link here: {type(exc).__name__}")


def test_i1_outputs_beside_a_linked_source_inside_the_footage_are_refused(
    sample, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    footage, outside = tmp_path / "footage", tmp_path / "outside"
    footage.mkdir()
    outside.mkdir()
    real = _copy(sample, STILL, outside, "real.jpg")
    link = footage / "linked.jpg"
    _symlink(real, link)  # the link is inside, its target outside: outputs go beside the link
    monkeypatch.setattr(he, "configured_footage_folder", lambda config=None: footage)
    assert _main(link, "--beside-source", "--force-cpu") == 2
    assert "inside the footage folder" in capsys.readouterr().err
    beside = he.requests_for(
        [link], parameters=new_parameter_set("c3", {}), settings=Settings(force_cpu=True)
    )
    with pytest.raises(he.RunnerRefusalError, match="outputs beside it are refused"):
        he.run(beside, footage_folder=footage)
    assert sorted(p.name for p in footage.iterdir()) == ["linked.jpg"]
    assert sorted(p.name for p in outside.iterdir()) == ["real.jpg"]


def test_i1_every_write_target_linked_into_the_footage_is_refused(
    sample, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    footage, out = tmp_path / "footage", tmp_path / "out"
    (footage / "sub").mkdir(parents=True)
    out.mkdir()
    linked_out = tmp_path / "linked-out"
    _symlink(footage / "sub", linked_out, directory=True)  # a folder link into the footage
    settings_dir = tmp_path / "settings"
    settings_dir.mkdir()
    save_settings(footage / "sub", Settings())
    _symlink(footage / "sub" / "settings.json", settings_dir / "settings.json")
    _symlink(footage / "sub" / "r.json", out / "r.json")  # a dangling link to a footage record
    source = sample(STILL)
    monkeypatch.setattr(he, "configured_footage_folder", lambda config=None: footage)
    before = sorted(p.name for p in (footage / "sub").iterdir())
    assert _main(source, "--out", linked_out, "--force-cpu") == 2
    assert _main(source, "--out", tmp_path, "--force-cpu", "--record", linked_out / "r.json") == 2
    assert _main(source, "--out", tmp_path, "--force-cpu", "--record", out / "r.json") == 2
    assert _main(source, "--out", tmp_path, "--force-cpu", "--settings-dir", linked_out) == 2
    assert _main(source, "--out", tmp_path, "--force-cpu", "--settings-dir", settings_dir) == 2
    err = capsys.readouterr().err
    assert err.count("inside the footage folder") == 5, err
    assert sorted(p.name for p in (footage / "sub").iterdir()) == before
    params = new_parameter_set("c3", {})
    requests = he.requests_for([source], parameters=params, settings=_cpu(linked_out))
    with pytest.raises(he.RunnerRefusalError, match="output folder is inside the footage"):
        he.run(requests, footage_folder=footage)
    assert not list(tmp_path.glob("*_corrected*.png"))


def test_i2_an_unreadable_local_configuration_names_no_full_path(
    sample, tmp_path: Path, out: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    config = tmp_path / "repo" / "clearwater.local.toml"
    config.parent.mkdir()
    config.write_text("footage_path = [\n", encoding="utf-8")
    monkeypatch.setattr(he, "default_config_path", lambda: config)
    assert _main(sample(STILL), "--out", out, "--force-cpu") == 2
    err = capsys.readouterr().err
    assert "local configuration cannot be read" in err and "clearwater.local.toml" in err
    assert _no_full_path(err, config.parent) and list(out.iterdir()) == []


def test_i3_a_parameter_file_against_the_method_schema_is_a_usage_refusal(
    sample, tmp_path: Path, out: Path, no_footage: None, capsys
) -> None:
    name = composition.correction_methods()["c3"].parameters[0].name
    preset = {**new_parameter_set("c3", {}).to_dict(), "parameters": {name: "invalid"}}
    path = tmp_path / "p.json"
    path.write_text(json.dumps(preset), encoding="utf-8")
    with pytest.raises(he.RunnerRefusalError, match=r"p\.json does not match method 'c3'"):
        he.parameters_for(file=path)
    assert _main(sample(STILL), "--out", out, "--force-cpu", "--parameters", path) == 2
    assert f"{name}: expected float, got str" in capsys.readouterr().err
    assert list(out.iterdir()) == []


def test_i4_a_parameter_file_over_the_importers_cap_is_refused(tmp_path: Path) -> None:
    preset = new_parameter_set("c3", {}).to_dict()
    path = tmp_path / "big.json"
    path.write_text(json.dumps({**preset, "source": {"name": "x" * MAX_PRESET_BYTES}}), "utf-8")
    with pytest.raises(he.RunnerRefusalError, match=f"the cap is {MAX_PRESET_BYTES} bytes"):
        he.read_parameter_file(path)
    path.write_text(json.dumps({**preset, "source": {"name": "x"}}), encoding="utf-8")
    assert he.read_parameter_file(path).method == "c3"
