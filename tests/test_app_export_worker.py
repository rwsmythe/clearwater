"""WP4.6 tests: the real export worker (``python -m clearwater.app.export_worker``) end to end.

Each test spawns a Python worker that imports clearwater and exports the committed fixture clip
``hevc8-bt709-full.mp4`` on the CPU (``force_cpu``, libx265), so every test here is ``slow``.
The parent side is ``ProcessExportJobs`` (its protocol tests, with fake children, are in
``test_jobs_export_process.py``). Outputs, caches and scratch folders go under ``tmp_path``.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from clearwater.app import composition
from clearwater.config.presets import new_parameter_set
from clearwater.interfaces import JobResult, Progress, Settings
from clearwater.io.video.probe import find_tool
from clearwater.jobs.export_process import WORKER_LOGGER, ProcessExportJobs
from clearwater.jobs.export_seam import CANCELLED, ExportRequest, unavailable_exports
from clearwater.jobs.safe_write import is_temporary_name

pytestmark = [
    pytest.mark.slow,  # spawns a Python worker that imports clearwater (several seconds)
    pytest.mark.usefixtures("ffmpeg_tools"),
]

CLIP = Path(__file__).resolve().parent / "fixtures" / "video" / "hevc8-bt709-full.mp4"
WORKER = [sys.executable, "-m", "clearwater.app.export_worker"]
QT_ROOTS = ("PySide6", "shiboken6")


class _Progress:
    """An IF-8 progress double: records reports, cancels after N reports when asked."""

    def __init__(self, *, cancel_after: int | None = None) -> None:
        self.reports: list[tuple[int, int | None, str]] = []
        self._cancel = threading.Event()
        self._after = cancel_after

    def report(self, done: int, total: int | None, message: str) -> None:
        self.reports.append((done, total, message))
        if self._after is not None and len(self.reports) >= self._after:
            self._cancel.set()

    def cancelled(self) -> bool:
        return self._cancel.is_set()


def _request(out: Path) -> ExportRequest:
    parameters = new_parameter_set("c3", {}, now=datetime(2026, 10, 30, tzinfo=UTC))
    settings = Settings(output_folder=out, force_cpu=True, video_encoder="libx265", provenance=True)
    return ExportRequest(source=CLIP, kind="video", parameters=parameters, settings=settings)


def _process_jobs(tmp_path: Path, command: list[str] = WORKER) -> ProcessExportJobs:
    return ProcessExportJobs(
        photo_exports=unavailable_exports(),
        cache_dir=tmp_path / "cache",
        app_version="9.9.9",
        command=command,
    )


def _export(tmp_path: Path, progress: Progress, command: list[str] = WORKER) -> JobResult:
    out = tmp_path / "out"
    out.mkdir(exist_ok=True)
    return _process_jobs(tmp_path, command).job(_request(out))(progress)


def _comment(path: Path) -> Any:
    done = subprocess.run(
        [
            str(find_tool("ffprobe")),
            *("-v", "error", "-of", "json", "-show_entries", "format_tags=comment"),
            str(path),
        ],
        capture_output=True,
        check=True,
    )
    return json.loads(done.stdout).get("format", {}).get("tags", {}).get("comment")


def _framemd5(path: Path) -> list[str]:
    done = subprocess.run(
        [
            str(find_tool("ffmpeg")),
            *("-v", "error", "-i", str(path)),
            *("-map", "0:v", "-f", "framemd5", "pipe:1"),
        ],
        capture_output=True,
        check=True,
        text=True,
    )
    return [line for line in done.stdout.splitlines() if not line.startswith("#")]


def _scratch(tmp_path: Path) -> list[Path]:
    folder = tmp_path / "cache" / "export"
    return sorted(folder.iterdir()) if folder.exists() else []


def _document(out: Path, scratch: Path, **changes: Any) -> dict[str, Any]:
    """A sound request document, by the protocol (``jobs/export_process.py``'s docstring)."""
    request = _request(out)
    document: dict[str, Any] = {
        "format_version": 1,
        "source": str(CLIP),
        "kind": "video",
        "parameters": request.parameters.to_dict(),
        "settings": json.loads(request.settings.to_json()),
        "cache_folder": str(scratch),
        "cache_limit_bytes": request.settings.cache_limit_bytes,
        "app_version": "9.9.9",
    }
    document.update(changes)
    return document


def test_the_worker_exports_the_fixture_clip(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO)
    progress = _Progress()
    result = _export(tmp_path, progress)
    assert result.ok, result.failure
    assert result.device.startswith("CPU"), result.device
    (output,) = result.outputs
    assert output.parent == tmp_path / "out" and output.is_file()
    assert sorted(p.name for p in (tmp_path / "out").iterdir()) == [output.name]
    assert not any(is_temporary_name(p.name) for p in (tmp_path / "out").iterdir())
    provenance = json.loads(_comment(output))
    assert provenance["app_version"] == "9.9.9"
    assert provenance["source"]["name"] == CLIP.name
    assert progress.reports, "no progress reached the parent"
    assert _scratch(tmp_path) == []  # the scratch folder is gone
    relogged = [r.getMessage() for r in caplog.records if r.name == WORKER_LOGGER]
    assert any(m.startswith("clearwater.jobs.export: export ") for m in relogged), relogged


def test_a_cancel_at_the_first_progress_leaves_nothing(tmp_path: Path) -> None:
    result = _export(tmp_path, _Progress(cancel_after=1))
    assert result.failure is CANCELLED
    assert result.outputs == ()
    assert list((tmp_path / "out").iterdir()) == []  # no output and no temporary
    assert _scratch(tmp_path) == []


@pytest.mark.parametrize(
    "case",
    [
        "empty input",
        "not JSON",
        "not one line of ASCII JSON",
        "a missing key",
        "an unknown key",
        "format_version 2",
        "bad parameters",
        "bad settings",
        "a source that is not a string",
        "a negative cache limit",
    ],
)
def test_a_malformed_request_exits_2_with_one_stderr_line(tmp_path: Path, case: str) -> None:
    out, scratch = tmp_path / "out", tmp_path / "scratch"
    sound = _document(out, scratch)
    missing = dict(sound)
    del missing["app_version"]
    line = {
        "empty input": b"",
        "not JSON": b"{not json\n",
        "not one line of ASCII JSON": b'{"format_version": 1, "s\xffource"}\n',
        "a missing key": json.dumps(missing).encode() + b"\n",
        "an unknown key": json.dumps({**sound, "extra": 1}).encode() + b"\n",
        "format_version 2": json.dumps({**sound, "format_version": 2}).encode() + b"\n",
        "bad parameters": json.dumps({**sound, "parameters": {"method": 3}}).encode() + b"\n",
        "bad settings": json.dumps({**sound, "settings": {"format_version": 1}}).encode() + b"\n",
        "a source that is not a string": json.dumps({**sound, "source": 7}).encode() + b"\n",
        "a negative cache limit": json.dumps({**sound, "cache_limit_bytes": -1}).encode() + b"\n",
    }[case]
    done = subprocess.run(WORKER, input=line, capture_output=True, timeout=120)
    assert done.returncode == 2, (case, done.stderr)
    assert done.stdout == b"", case
    lines = done.stderr.decode("ascii").splitlines()
    assert len(lines) == 1 and lines[0].startswith("export worker: "), (case, lines)
    assert not out.exists() and not scratch.exists()


def test_the_worker_imports_no_qt(tmp_path: Path) -> None:
    modules = tmp_path / "modules.txt"
    probe = (
        "import atexit, runpy, sys\n"
        "def record():\n"
        "    with open(sys.argv[1], 'w') as f:\n"
        "        f.write('\\n'.join(sorted(sys.modules)))\n"
        "atexit.register(record)\n"
        "runpy.run_module('clearwater.app.export_worker', run_name='__main__', alter_sys=True)\n"
    )
    command = [sys.executable, "-c", probe, str(modules)]
    result = _export(tmp_path, _Progress(), command)
    assert result.ok, result.failure
    loaded = modules.read_text().splitlines()
    assert "clearwater.jobs.export" in loaded  # the probe saw a whole job
    assert [m for m in loaded if m.split(".")[0] in QT_ROOTS] == []


def test_q9_the_worker_and_the_in_process_engine_encode_the_same_frames(tmp_path: Path) -> None:
    """N10 across the boundary: decoded frames equal (the file bytes differ between runs)."""
    inside_out = tmp_path / "inside"
    inside_out.mkdir()
    engine = composition.export_jobs(app_version="9.9.9", cache_folder=tmp_path / "inside-cache")
    inside = engine.job(_request(inside_out))(_Progress())
    child = _export(tmp_path, _Progress())
    assert inside.ok and child.ok, (inside.failure, child.failure)
    assert inside.device == child.device
    (a,), (b,) = inside.outputs, child.outputs
    frames_a, frames_b = _framemd5(a), _framemd5(b)
    assert len(frames_a) == len(frames_b) > 0
    assert frames_a == frames_b
