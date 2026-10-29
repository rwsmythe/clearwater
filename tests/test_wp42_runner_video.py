"""WP4.2 task 5: the headless runner's video legs (``tools/headless_export.py``).

A CPU video run through ``main``; ``--cache-dir`` required for a video item and refused when it
does not exist (round-0 ruling R0-Q3); every write the video legs plan goes through the one
predicate, ``write_target_refusal`` (CHARC ``870c8ddeb64b4e12``): ``--out``, ``--beside-source``
and ``--cache-dir`` inside a stand-in footage folder, directly and through a junction, and a
video source whose stem carries ``:`` (the video half of DR-78's coverage, through WP4.2a's
``check_outputs``); exit statuses 0, 1 and 2; two files give two outputs and two cache entries;
the record's additive ``"video"`` object (CHARC ``881cc956f1335e7e`` A: its four fields, null
for a photo or a caller's engine, ``decode_passes`` counted, fewer on a reopen, V17); names
only; and a ``--force-cpu`` video run that loads no PySide6 or CuPy.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

import headless_export as he
from clearwater.config import new_parameter_set
from clearwater.interfaces import Settings
from clearwater.interfaces.stubs import StubProgress
from clearwater.jobs.export_seam import ExportRequest

pytestmark = pytest.mark.usefixtures("ffmpeg_tools")

TOOLS = Path(he.__file__).parent
CLIP = "vid-hevc8-bt709-full"
OTHER = "vid-rotated"
WINDOWS = os.name == "nt"


@pytest.fixture
def no_footage(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make ``main`` see no configured footage folder."""
    monkeypatch.setattr(he, "configured_footage_folder", lambda config=None: None)


@pytest.fixture
def folders(tmp_path: Path) -> dict[str, Path]:
    """An empty output folder, an empty cache folder and a source folder."""
    made = {name: tmp_path / name for name in ("out", "cache", "src")}
    for folder in made.values():
        folder.mkdir()
    return made


def _main(*args: object) -> int:
    return he.main([str(a) for a in args])


def _copy(sample: Any, sample_id: str, folder: Path, name: str | None = None) -> Path:
    source = sample(sample_id)
    target = folder / (name or source.name)
    shutil.copyfile(source, target)
    return target


def _record(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="ascii"))


def _entries(cache: Path) -> list[str]:
    return sorted(p.name for p in cache.iterdir() if p.is_dir())


def _junction(target: Path, link: Path) -> None:
    """Create a directory junction, or skip the test where none can be created."""
    if not WINDOWS:
        pytest.skip("directory junctions exist only on Windows")
    done = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True, check=False
    )
    if done.returncode != 0 or not link.is_dir():
        pytest.skip("a directory junction cannot be created here")


def _no_full_path(text: str, *folders: Path) -> bool:
    for folder in folders:
        for form in (str(folder), str(folder).replace("\\", "\\\\"), folder.as_posix()):
            if form in text:
                return False
    return True


# --- a video run through main -------------------------------------------------------------------


def test_a_cpu_video_run_through_main_records_its_video_facts_and_a_reopen_skips_the_decode(
    sample, tmp_path: Path, folders: dict[str, Path], no_footage: None, capsys
) -> None:
    out, cache = folders["out"], folders["cache"]
    source = _copy(sample, CLIP, folders["src"])
    common = ("--out", out, "--force-cpu", "--encoder", "libx265", "--cache-dir", cache)
    assert _main(source, *common, "--record", tmp_path / "first.json") == 0
    assert _main(source, *common, "--record", tmp_path / "second.json") == 0

    first, second = _record(tmp_path / "first.json"), _record(tmp_path / "second.json")
    assert first["schema"] == 1 and [i["kind"] for i in first["items"]] == ["video"]
    item = first["items"][0]
    assert item["state"] == "done" and item["device"] == "CPU: forced"
    assert item["outputs"] == ["hevc8-bt709-full_corrected.mp4"]
    assert list(item)[-1] == "video"  # additive: the WP4.1 fields first, in their order
    assert item["video"] == {
        "device_backend": None,
        "frame_device": "cpu",
        "encoder": "libx265",
        "decode_passes": 2,
    }
    again = second["items"][0]
    assert again["outputs"] == ["hevc8-bt709-full_corrected_2.mp4"]
    assert again["video"]["decode_passes"] == 1  # V17: the complete entry skips the decode pass
    assert sorted(p.name for p in out.iterdir()) == [
        "hevc8-bt709-full_corrected.mp4",
        "hevc8-bt709-full_corrected_2.mp4",
    ]
    assert len(_entries(cache)) == 1
    text = (tmp_path / "first.json").read_text(encoding="ascii") + capsys.readouterr().out
    assert _no_full_path(text, tmp_path, cache, out)


def test_two_files_give_two_outputs_and_two_cache_entries(
    sample, tmp_path: Path, folders: dict[str, Path], no_footage: None
) -> None:
    out, cache = folders["out"], folders["cache"]
    sources = [_copy(sample, CLIP, folders["src"]), _copy(sample, OTHER, folders["src"])]
    record = tmp_path / "r.json"
    status = _main(
        *sources, "--out", out, "--force-cpu", "--encoder", "libx265", "--cache-dir", cache,
        "--record", record,
    )  # fmt: skip
    assert status == 0
    items = _record(record)["items"]
    assert [i["state"] for i in items] == ["done", "done"]
    assert [i["video"]["decode_passes"] for i in items] == [2, 2]
    assert sorted(p.name for p in out.iterdir()) == [
        "hevc8-bt709-full_corrected.mp4",
        "rotated_corrected.mp4",
    ]
    assert len(_entries(cache)) == 2


def test_exit_statuses_of_video_runs(
    sample, tmp_path: Path, folders: dict[str, Path], no_footage: None
) -> None:
    out, cache = folders["out"], folders["cache"]
    source = _copy(sample, CLIP, folders["src"])
    broken = folders["src"] / "broken.mp4"
    broken.write_bytes(b"not a video")
    common = ("--out", out, "--force-cpu", "--encoder", "libx265")
    assert _main(source, *common, "--cache-dir", cache) == 0
    assert _main(broken, *common, "--cache-dir", cache) == 1
    assert _main(source, *common) == 2  # no --cache-dir with a video item
    assert _main(source, *common, "--cache-dir", tmp_path / "missing") == 2
    assert sorted(p.name for p in out.iterdir()) == ["hevc8-bt709-full_corrected.mp4"]
    assert not (tmp_path / "missing").exists()


def test_a_video_without_cache_dir_is_refused_with_nothing_run(
    sample, folders: dict[str, Path], no_footage: None, capsys
) -> None:
    source = _copy(sample, CLIP, folders["src"])
    photo = _copy(sample, "jpeg-gradient-srgb", folders["src"])
    assert _main(photo, source, "--out", folders["out"], "--force-cpu") == 2
    err = capsys.readouterr().err
    assert "--cache-dir is required when an item is a video." in err
    assert list(folders["out"].iterdir()) == []
    assert _main(source, "--out", folders["out"], "--cache-dir", folders["out"] / "x") == 2
    assert "the --cache-dir folder does not exist." in capsys.readouterr().err


def test_a_photo_item_records_no_video_object(
    sample, tmp_path: Path, folders: dict[str, Path], no_footage: None
) -> None:
    photo = _copy(sample, "jpeg-gradient-srgb", folders["src"])
    record = tmp_path / "r.json"
    assert _main(photo, "--out", folders["out"], "--force-cpu", "--record", record) == 0
    (item,) = _record(record)["items"]
    assert item["kind"] == "photo" and item["video"] is None


class _Opening:
    """A sink double whose ``open`` succeeds or raises."""

    def __init__(self, refuse: bool) -> None:
        self.refuse = refuse

    def open(self, *args: object, **kwargs: object) -> None:
        if self.refuse:
            raise RuntimeError("the encoder cannot be opened")


@pytest.mark.parametrize("refuse", [True, False])
def test_the_encoder_is_recorded_only_once_the_sink_has_opened(refuse: bool) -> None:
    """Reviewer A R1 F1: ``"encoder"`` stays null when the wrapped sink's ``open`` raises."""
    facts = he._video_facts()
    sink = he._ObservedSink(_Opening(refuse), facts)  # type: ignore[arg-type]
    options: dict[str, Any] = {"quality": "standard", "bit_depth": 8, "provenance": None}
    if refuse:
        with pytest.raises(RuntimeError, match="cannot be opened"):
            sink.open(None, Path("out.mp4"), encoder="libx265", **options)  # type: ignore[arg-type]
        assert facts["encoder"] is None
    else:
        sink.open(None, Path("out.mp4"), encoder="libx265", **options)  # type: ignore[arg-type]
        assert facts["encoder"] == "libx265"


# --- the library run ----------------------------------------------------------------------------


def _requests(source: Path, out: Path | None) -> list[ExportRequest]:
    settings = Settings(output_folder=out, force_cpu=True, video_encoder="libx265")
    return he.requests_for([source], parameters=new_parameter_set("c3", {}), settings=settings)


def test_run_needs_a_cache_folder_for_a_video_unless_the_engine_is_given(
    sample, folders: dict[str, Path]
) -> None:
    source = _copy(sample, CLIP, folders["src"])
    with pytest.raises(he.RunnerRefusalError, match="a video item needs a cache folder"):
        he.run(_requests(source, folders["out"]), footage_folder=None)
    assert list(folders["out"].iterdir()) == []

    class Engine:
        def job(self, request: ExportRequest) -> Any:
            from clearwater.app import composition

            return composition.export_jobs(cache_folder=folders["cache"]).job(request)

    record = he.run(_requests(source, folders["out"]), footage_folder=None, exports=Engine())
    assert record.report.items[0].state == "done"
    assert he.record_object(record)["items"][0]["video"] is None  # a caller's engine: unobserved


def test_run_records_the_video_facts_and_shows_the_cache_folder_by_name(
    sample, folders: dict[str, Path]
) -> None:
    source = _copy(sample, CLIP, folders["src"])
    record = he.run(
        _requests(source, folders["out"]), footage_folder=None, cache_folder=folders["cache"]
    )
    assert record.video == (
        {"device_backend": None, "frame_device": "cpu", "encoder": "libx265", "decode_passes": 2},
    )
    assert folders["cache"] in record.folders
    text = he.record_json(record)
    assert _no_full_path(text, folders["cache"], folders["out"], folders["src"])


# --- the one write-target predicate on the video legs ---------------------------------------------


def test_every_video_write_target_inside_the_footage_is_refused(
    sample, tmp_path: Path, folders: dict[str, Path], monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    footage = tmp_path / "footage"
    (footage / "sub").mkdir(parents=True)
    inside = _copy(sample, CLIP, footage)
    source = _copy(sample, CLIP, folders["src"])
    monkeypatch.setattr(he, "configured_footage_folder", lambda config=None: footage)
    before = sorted(p.name for p in footage.rglob("*"))
    out, cache = folders["out"], folders["cache"]
    assert _main(source, "--out", footage / "sub", "--force-cpu", "--cache-dir", cache) == 2
    assert _main(inside, "--beside-source", "--force-cpu", "--cache-dir", cache) == 2
    assert _main(source, "--out", out, "--force-cpu", "--cache-dir", footage / "sub") == 2
    err = capsys.readouterr().err
    assert err.count("inside the footage folder") == 3, err
    assert "the --cache-dir path is inside the footage folder" in err
    assert sorted(p.name for p in footage.rglob("*")) == before
    assert list(out.iterdir()) == [] and list(cache.iterdir()) == []
    with pytest.raises(he.RunnerRefusalError, match="the cache folder is inside the footage"):
        he.run(_requests(source, out), footage_folder=footage, cache_folder=footage / "sub")


def test_every_video_write_target_linked_into_the_footage_is_refused(
    sample, tmp_path: Path, folders: dict[str, Path], monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    footage = tmp_path / "footage"
    (footage / "sub").mkdir(parents=True)
    _copy(sample, CLIP, footage / "sub")
    link = tmp_path / "link"
    _junction(footage / "sub", link)
    source = _copy(sample, CLIP, folders["src"])
    monkeypatch.setattr(he, "configured_footage_folder", lambda config=None: footage)
    before = sorted(p.name for p in footage.rglob("*"))
    out, cache = folders["out"], folders["cache"]
    linked_source = link / source.name
    assert _main(source, "--out", link, "--force-cpu", "--cache-dir", cache) == 2
    assert _main(linked_source, "--beside-source", "--force-cpu", "--cache-dir", cache) == 2
    assert _main(source, "--out", out, "--force-cpu", "--cache-dir", link) == 2
    err = capsys.readouterr().err
    assert err.count("inside the footage folder") == 3, err
    assert sorted(p.name for p in footage.rglob("*")) == before
    assert list(out.iterdir()) == [] and list(cache.iterdir()) == []


def test_a_video_source_whose_stem_carries_a_colon_is_refused_by_check_outputs(
    tmp_path: Path, folders: dict[str, Path]
) -> None:
    footage = tmp_path / "footage"
    footage.mkdir()
    stand_in = folders["src"] / "carrier:clip.mp4"  # a stand-in name, never created
    requests = _requests(stand_in, folders["out"])
    assert requests[0].kind == "video"
    with pytest.raises(he.RunnerRefusalError, match="single portable name component"):
        he.check_outputs(requests, footage)
    with pytest.raises(he.RunnerRefusalError, match="single portable name component"):
        he.run(requests, footage_folder=footage, cache_folder=folders["cache"])
    assert list(folders["out"].iterdir()) == [] and list(folders["cache"].iterdir()) == []


# --- the runner process -------------------------------------------------------------------------


def test_a_forced_cpu_video_run_loads_no_pyside6_and_no_cupy(
    sample, folders: dict[str, Path]
) -> None:
    source = _copy(sample, CLIP, folders["src"])
    args = [str(source), "--out", str(folders["out"]), "--force-cpu", "--encoder", "libx265"]
    args += ["--cache-dir", str(folders["cache"])]
    code = (
        "import sys\n"
        f"sys.path.insert(0, {str(TOOLS)!r})\n"
        "import headless_export\n"
        "headless_export.configured_footage_folder = lambda config=None: None\n"
        f"status = headless_export.main({args!r})\n"
        "bad = sorted(m for m in sys.modules\n"
        "             if m.split('.')[0] in ('PySide6', 'shiboken6', 'cupy', 'cupyx'))\n"
        "print('RESULT', status, ','.join(bad))\n"
    )
    done = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True, timeout=300
    )
    assert done.stdout.splitlines()[-1].split(" ") == ["RESULT", "0", ""]
    assert [p.name for p in folders["out"].iterdir()] == ["hevc8-bt709-full_corrected.mp4"]


def test_the_video_job_of_a_main_run_is_the_composed_engine(
    sample, folders: dict[str, Path], no_footage: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``run`` builds the root's engine with the cache folder and the first item's limit."""
    from clearwater.app import composition

    seen: dict[str, Any] = {}
    real = composition.export_jobs

    def recording(**kwargs: Any) -> Any:
        seen.update(kwargs)
        return real(**kwargs)

    monkeypatch.setattr(composition, "export_jobs", recording)
    source = _copy(sample, CLIP, folders["src"])
    common = ("--out", folders["out"], "--force-cpu", "--encoder", "libx265")
    assert (
        _main(source, *common, "--cache-dir", folders["cache"], "--cache-limit-bytes", 10**9) == 0
    )
    assert seen["cache_folder"] == folders["cache"] and seen["cache_limit_bytes"] == 10**9
    job = composition.export_jobs(cache_folder=folders["cache"]).job(
        _requests(source, folders["out"])[0]
    )
    assert job(StubProgress()).ok
