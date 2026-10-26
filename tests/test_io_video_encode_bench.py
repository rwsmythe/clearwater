"""Tests of the export floor-row instrument ``tools/video_io_bench.py`` (WP3.10, ruling Q11).

No footage: the runs use a WP2.3 sample and a footage folder made under ``tmp_path``. The
timing figures themselves are taken only in an exclusive window; here the record's shape, its
arithmetic, the cleanup and the command line are checked.
"""

from __future__ import annotations

import json
import math
import multiprocessing
import shutil
import subprocess
import sys
import threading
import time
from fractions import Fraction
from pathlib import Path
from typing import Any

import psutil
import pytest

import video_io_bench as bench
from clearwater.io.video import FFmpegVideoSink, VideoEncodeError, detect_capabilities
from local_config import LocalConfig

pytestmark = pytest.mark.usefixtures("ffmpeg_tools")

FAST = (0.02, 0.5, 1.0)
SAMPLE = "vid-hevc8-bt709-full"


def _ffmpeg_children() -> list[int]:
    return [
        child.pid
        for child in psutil.Process().children(recursive=True)
        if "ffmpeg" in child.name().lower()
    ]


def _tree(process: subprocess.Popen[bytes]) -> set[int]:
    # a venv's python.exe on Windows may be a launcher whose child is the interpreter
    return {process.pid} | {c.pid for c in psutil.Process(process.pid).children(recursive=True)}


def _busy_child() -> subprocess.Popen[bytes]:
    return subprocess.Popen(
        [sys.executable, "-c", "import time\nend = time.time() + 30\nwhile time.time() < end: pass"]
    )


# --- arithmetic and readings -----------------------------------------------------------------


def test_rate_is_seconds_per_frame_and_minutes_per_minute() -> None:
    figures = bench.rate(60.0, 300, Fraction(30000, 1001))
    assert figures["s_per_frame"] == pytest.approx(0.2)
    # 300 frames at 30000/1001 fps are 10.01 s of footage: 60 s / 10.01 s
    assert figures["min_per_min"] == pytest.approx(60.0 / 10.01)


def test_summarise() -> None:
    assert bench.summarise([]) is None
    row = bench.summarise([0.3, 0.1, 0.2, 0.4, 0.5])
    assert row is not None
    assert (row["n"], row["median"], row["min"], row["max"]) == (5, 0.3, 0.1, 0.5)
    assert row["mean"] == pytest.approx(0.3)


def test_floor_plan_is_ruling_q11() -> None:
    assert [
        (leg.clip, leg.encoder, leg.bit_depth, leg.runs, leg.quality) for leg in bench.FLOOR_PLAN
    ] == [
        ("GX011627", "hevc_nvenc", 8, 3, "standard"),
        ("GX011625", "hevc_nvenc", 8, 1, "standard"),
        ("GX011627", "libx265", 8, 1, "standard"),
        ("GX011627", "hevc_nvenc", 10, 1, "standard"),
    ]


def test_gpu_reading_parses_one_line(monkeypatch: pytest.MonkeyPatch) -> None:
    fields = bench._GPU_QUERY.split(",")
    line = ", ".join(str(n) for n in range(len(fields)))

    def run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args, 0, line + "\n", "")

    monkeypatch.setattr(bench.subprocess, "run", run)
    reading = bench.gpu_reading()
    assert reading == {field: str(n) for n, field in enumerate(fields)}
    assert bench.memory_used_mib(reading) == float(fields.index("memory.used"))


@pytest.mark.parametrize(("code", "out"), [(9, ""), (0, "")])
def test_gpu_reading_failure_is_recorded(
    monkeypatch: pytest.MonkeyPatch, code: int, out: str
) -> None:
    def run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args, code, out, "no device")

    monkeypatch.setattr(bench.subprocess, "run", run)
    reading = bench.gpu_reading()
    assert list(reading) == ["unavailable"]
    assert bench.memory_used_mib(reading) is None


def test_gpu_reading_without_nvidia_smi(monkeypatch: pytest.MonkeyPatch) -> None:
    def run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise FileNotFoundError("nvidia-smi")

    monkeypatch.setattr(bench.subprocess, "run", run)
    assert bench.gpu_reading() == {"unavailable": "nvidia-smi did not run: FileNotFoundError"}


def test_conditions_strays_window_is_the_one_second(monkeypatch: pytest.MonkeyPatch) -> None:
    def slow_reading() -> dict[str, str]:
        time.sleep(2.0)
        return {"unavailable": "planted slow nvidia-smi"}

    monkeypatch.setattr(bench, "gpu_reading", slow_reading)
    record = bench.conditions("before")
    assert record["moment"] == "before" and record["gpu"]["unavailable"]
    assert 1.0 <= record["strays"]["seconds"] < 1.5  # not the GPU or CPU readings (round 5 #4)


def test_tree_rss_counts_children_and_leaves_out_the_excluded() -> None:
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        total, members = bench.tree_rss()
        assert child.pid in {m["pid"] for m in members}
        assert total == sum(m["rss"] for m in members)
        _, without = bench.tree_rss({child.pid})
        assert child.pid not in {m["pid"] for m in without}
    finally:
        child.kill()
        child.wait()


def test_stray_watch_marks_the_runs_own_processes() -> None:
    mine, other = _busy_child(), _busy_child()
    try:
        time.sleep(0.5)
        watch = bench.StrayWatch(mine.pid)
        time.sleep(1.5)
        busy = {entry["pid"]: entry for entry in watch.window()["busy"]}
        own = [busy[pid]["own"] for pid in _tree(mine) if pid in busy]
        strays = [busy[pid] for pid in _tree(other) if pid in busy]
        assert own == [True]
        assert [entry["own"] for entry in strays] == [False]
        assert strays[0]["cpu"] >= bench.STRAY_CPU_PERCENT
    finally:
        for process in (mine, other):
            process.kill()
            process.wait()


def test_stray_watch_charges_a_process_started_inside_the_window() -> None:
    watch = bench.StrayWatch()
    child = _busy_child()  # started after the watch was primed (round 5 #2)
    try:
        time.sleep(2.0)
        busy = {entry["pid"]: entry for entry in watch.window()["busy"]}
        seen = [busy[pid] for pid in _tree(child) if pid in busy]
        assert len(seen) == 1
        assert seen[0]["new"] is True and seen[0]["own"] is True
        assert seen[0]["cpu"] >= bench.STRAY_CPU_PERCENT and seen[0]["alive_s"] > 0
        time.sleep(1.0)
        again = {entry["pid"]: entry for entry in watch.window()["busy"]}
        assert seen[0]["pid"] in again and "new" not in again[seen[0]["pid"]]
    finally:
        child.kill()
        child.wait()


@pytest.mark.parametrize("periods", [(0.0, 1.0, 1.0), (0.1, -1.0, 1.0), (0.1, 1.0, math.inf)])
def test_telemetry_refuses_a_period_that_is_not_positive(
    periods: tuple[float, float, float],
) -> None:
    memory, gpu, strays = periods
    with pytest.raises(ValueError, match="positive"):
        bench.Telemetry(memory_every=memory, gpu_every=gpu, strays_every=strays)


def test_telemetry_watcher_starts_reports_and_stops() -> None:
    telemetry = bench.Telemetry(memory_every=0.05, gpu_every=1.0, strays_every=0.5)
    telemetry.start()
    watcher = telemetry._watcher
    assert watcher is not None and watcher.is_alive()
    time.sleep(8)  # one window reads every process: about 2.5 s on the owner's laptop
    record = telemetry.stop()
    assert record["errors"] == []
    assert len(record["strays"]) >= 2  # at least one period and the last window at the stop
    assert [w.get("final", False) for w in record["strays"]][-2:] == [False, True]
    assert record["rss_samples"] > 5
    assert watcher.pid not in {m["pid"] for m in record["peak_tree_rss_members"]}
    assert not watcher.is_alive()


class _FakeWatch:
    """A :class:`bench.StrayWatch` that numbers its windows instead of reading processes."""

    def __init__(self, root: int) -> None:
        self.count = 0

    def window(self) -> dict[str, Any]:
        self.count += 1
        return {"seconds": 0.01, "busy": [], "n": self.count}


def test_the_watchers_last_window_alone_is_tagged_final(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bench, "StrayWatch", _FakeWatch)
    mine, theirs = multiprocessing.Pipe()
    loop = threading.Thread(target=bench.stray_loop, args=(theirs, 0.01, 0))
    loop.start()
    assert mine.recv() == "ready"
    time.sleep(0.2)
    mine.send("stop")
    windows = []
    while not windows or not windows[-1].get("final"):
        assert mine.poll(5)
        windows.append(mine.recv())
    loop.join(5)
    assert not loop.is_alive() and not mine.poll(0.1)
    assert len(windows) >= 2 and [w["n"] for w in windows] == list(range(1, len(windows) + 1))
    assert [w.get("final", False) for w in windows] == [False] * (len(windows) - 1) + [True]


class _ScriptedPipe:
    """The parent's end of the watcher pipe, played from a script (round 6 #1)."""

    def __init__(self, queued: list[dict[str, Any]], after_stop: list[dict[str, Any]]) -> None:
        self.queue = list(queued)
        self.after_stop = after_stop
        self.lock = threading.Lock()
        self.sent: list[Any] = []

    def send(self, obj: Any) -> None:
        self.sent.append(obj)

        def later() -> None:
            time.sleep(0.5)  # the watcher finishes the window it is computing
            with self.lock:
                self.queue.extend(self.after_stop)

        threading.Thread(target=later, daemon=True).start()

    def poll(self, timeout: float | None = 0.0) -> bool:
        end = time.monotonic() + (timeout or 0.0)
        while True:
            with self.lock:
                if self.queue:
                    return True
            if time.monotonic() >= end:
                return False
            time.sleep(0.01)

    def recv(self) -> Any:
        with self.lock:
            return self.queue.pop(0)

    def close(self) -> None:
        pass


class _FakeWatcher:
    """A started watcher seen from the parent (no process: nothing to join)."""

    pid = None
    exitcode = None

    def is_alive(self) -> bool:
        return True


def _scripted_telemetry(pipe: _ScriptedPipe) -> bench.Telemetry:
    telemetry = bench.Telemetry(memory_every=0.05, gpu_every=10.0, strays_every=30.0)
    telemetry._watcher, telemetry._connection = _FakeWatcher(), pipe  # type: ignore[assignment]
    return telemetry


def test_stop_keeps_a_queued_window_and_the_final_one_after_it() -> None:
    periodic = {"seconds": 30.0, "busy": []}
    final = {"seconds": 12.0, "busy": [{"name": "late-stray"}], "final": True}
    pipe = _ScriptedPipe([periodic], [final])
    record = _scripted_telemetry(pipe).stop()
    assert pipe.sent == ["stop"]
    assert [w["seconds"] for w in record["strays"]] == [30.0, 12.0]  # round 6 #1
    assert record["strays"][-1]["busy"] == [{"name": "late-stray"}]
    assert record["errors"] == []


def test_a_final_window_that_does_not_come_is_recorded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bench, "_WATCHER_WAIT_S", 1.0)
    pipe = _ScriptedPipe([{"seconds": 30.0, "busy": []}], [])
    began = time.monotonic()
    record = _scripted_telemetry(pipe).stop()
    assert time.monotonic() - began < 5
    assert [w["seconds"] for w in record["strays"]] == [30.0]
    assert record["errors"] == ["the strays watcher sent no final window within 1 s"]


@pytest.mark.parametrize("seen_by", ["sampling", "stop"])
def test_a_watcher_that_dies_mid_run_is_recorded_and_not_waited_for(
    monkeypatch: pytest.MonkeyPatch, seen_by: str
) -> None:
    monkeypatch.setattr(bench, "_WATCHER_WAIT_S", 30.0)  # the start's wait, and stop's
    memory_every = 0.05 if seen_by == "sampling" else 30.0  # 30 s: the thread never looks again
    telemetry = bench.Telemetry(memory_every=memory_every, gpu_every=60.0, strays_every=60.0)
    telemetry.start()
    watcher = telemetry._watcher
    assert watcher is not None and watcher.pid is not None
    psutil.Process(watcher.pid).kill()
    watcher.join(10)
    if seen_by == "sampling":
        deadline = time.monotonic() + 5
        while not telemetry.errors and time.monotonic() < deadline:
            time.sleep(0.05)
        assert telemetry.errors and telemetry.errors[0].startswith("the strays watcher ended at")
        samples = telemetry.rss_samples
        time.sleep(0.5)
        assert telemetry.rss_samples > samples  # the memory sampling goes on (round 6 #2)
    began = time.monotonic()
    record = telemetry.stop()
    assert time.monotonic() - began < 10  # not the 30 s wait
    assert sorted(e.split(" (")[0].split(" at ")[0] for e in record["errors"]) == [
        "the strays watcher ended",
        "the strays watcher was not alive",
    ]
    assert record["rss_samples"] > 0


class _RecordingContext:
    """A multiprocessing context that remembers the pipes and processes it makes."""

    def __init__(self, real: Any) -> None:
        self.real = real
        self.ends: list[Any] = []
        self.processes: list[Any] = []

    def Pipe(self) -> tuple[Any, Any]:  # noqa: N802 - the multiprocessing name
        ends = self.real.Pipe()
        self.ends.extend(ends)
        return ends

    def Process(self, *args: Any, **kwargs: Any) -> Any:  # noqa: N802 - the multiprocessing name
        process = self.real.Process(*args, **kwargs)
        self.processes.append(process)
        return process


@pytest.mark.parametrize("failure", ["no ready", "start raises"])
def test_a_watcher_that_fails_to_start_is_ended_and_its_pipe_closed(
    monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    contexts: list[_RecordingContext] = []
    real = multiprocessing.get_context

    def get_context(method: str) -> _RecordingContext:
        contexts.append(_RecordingContext(real(method)))
        return contexts[-1]

    monkeypatch.setattr(bench.multiprocessing, "get_context", get_context)
    if failure == "no ready":
        monkeypatch.setattr(bench, "_WATCHER_WAIT_S", 0.001)  # far shorter than a spawn
    else:

        def poll(self: Any, timeout: float | None = None) -> bool:
            raise OSError("planted")

        monkeypatch.setattr(type(real("spawn").Pipe()[0]), "poll", poll)
    telemetry = bench.Telemetry(memory_every=0.05, gpu_every=5.0, strays_every=5.0)
    telemetry.start()
    monkeypatch.undo()
    try:
        assert len(telemetry.errors) == 1 and "watcher" in telemetry.errors[0]  # round 5 #9
        (context,) = contexts
        assert [end.closed for end in context.ends] == [True, True]
        assert [process.exitcode is not None for process in context.processes] == [True]
    finally:
        record = telemetry.stop()
    assert record["rss_samples"] > 0 and record["strays"] == []


# --- one run ---------------------------------------------------------------------------------


@pytest.fixture
def quick(monkeypatch: pytest.MonkeyPatch) -> None:
    """Skip the before / after conditions (seconds each); the first run test keeps them."""
    monkeypatch.setattr(bench, "conditions", lambda moment: {"moment": moment})


def test_run_once_records_the_row_and_deletes_the_output(sample: Any, tmp_path: Path) -> None:
    source = sample(SAMPLE)
    before = (source.read_bytes(), source.stat().st_mtime_ns)
    output = tmp_path / "out" / "row.mp4"
    record = bench.run_once(
        source,
        output,
        encoder="libx265",
        quality="draft",
        bit_depth=None,
        hw_decode=False,
        keep=False,
        periods=FAST,
    )
    assert not output.exists()
    assert (source.read_bytes(), source.stat().st_mtime_ns) == before
    frames = record["frames"]
    assert frames > 2
    assert record["sink_report"]["frames_written"] == frames
    assert len(record["per_frame_s"]) == frames
    assert record["per_frame"]["n"] == frames - 1
    assert record["decode_wait"]["n"] == record["write"]["n"] == frames - 1
    triples = zip(record["per_frame_s"], record["decode_wait_s"], record["write_s"], strict=True)
    for number, (interval, wait, write) in enumerate(triples):
        # an interval is its wait and its write plus microseconds of bookkeeping (round 5 #1);
        # the first one also holds the decoder's start
        assert wait + write <= interval + 2e-5
        assert number == 0 or interval - (wait + write) < 0.005
    stages = record["stages_s"]
    assert stages["total"] == pytest.approx(
        stages["probe"] + stages["open"] + stages["stream"] + stages["close"]
    )
    rate = Fraction(record["frame_rate"])
    assert record["total"]["s_per_frame"] == pytest.approx(stages["total"] / frames)
    assert record["total"]["min_per_min"] == pytest.approx(stages["total"] / float(frames / rate))
    assert sum(record["per_frame_s"]) == pytest.approx(stages["stream"], abs=0.01)
    assert record["decode"]["cuda"] is False and "-hwaccel" not in record["decode"]["command"]
    assert "libx265" in record["encode_command"]
    assert record["nvenc_proof"] == {"tied": False, "reason": "not an NVENC encode (libx265)"}
    assert record["output_bytes"] > 0 and record["output_video_bit_rate"] > 0
    telemetry = record["telemetry"]
    assert telemetry["errors"] == []
    assert telemetry["periods_s"] == {"memory": 0.02, "gpu": 0.5, "strays": 1.0}
    names = [m["name"] for m in telemetry["peak_tree_rss_members"]]
    assert any("ffmpeg" in name for name in names)
    assert telemetry["peak_tree_rss_bytes"] > 0 and telemetry["strays"]
    assert record["before"]["moment"] == "before" and record["after"]["moment"] == "after"
    assert _ffmpeg_children() == []


@pytest.mark.usefixtures("quick")
def test_run_once_keeps_the_output_when_asked(sample: Any, tmp_path: Path) -> None:
    output = tmp_path / "kept.mp4"
    record = bench.run_once(
        sample(SAMPLE),
        output,
        encoder="libx265",
        quality="draft",
        bit_depth=10,
        hw_decode=False,
        keep=True,
        periods=FAST,
    )
    assert record["output"] == str(output) and output.stat().st_size == record["output_bytes"]
    assert record["bit_depth"] == 10


@pytest.mark.usefixtures("quick")
def test_an_existing_output_is_refused_and_left_alone(sample: Any, tmp_path: Path) -> None:
    output = tmp_path / "taken.mp4"
    output.write_bytes(b"someone else's")
    with pytest.raises(bench.BenchError, match="never overwrites"):
        bench.run_once(
            sample(SAMPLE),
            output,
            encoder="libx265",
            quality="draft",
            bit_depth=None,
            hw_decode=False,
            keep=False,
            periods=FAST,
        )
    assert output.read_bytes() == b"someone else's"


@pytest.mark.usefixtures("quick")
def test_a_failing_write_deletes_the_output_and_ends_both_ffmpegs(
    sample: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real = FFmpegVideoSink.write

    def write(self: FFmpegVideoSink, frame: Any) -> None:
        if len(self._written) == 2:
            raise VideoEncodeError("frame", "planted")
        real(self, frame)

    monkeypatch.setattr(bench._BenchSink, "write", write)
    output = tmp_path / "failed.mp4"
    with pytest.raises(VideoEncodeError, match="planted"):
        bench.run_once(
            sample(SAMPLE),
            output,
            encoder="libx265",
            quality="draft",
            bit_depth=None,
            hw_decode=False,
            keep=True,
            periods=FAST,
        )
    assert not output.exists()
    assert _ffmpeg_children() == []


@pytest.mark.usefixtures("quick")
def test_a_failing_probe_deletes_the_created_output(tmp_path: Path) -> None:
    source = tmp_path / "not-a-video.mp4"
    source.write_bytes(b"\x00" * 64)
    output = tmp_path / "never.mp4"
    with pytest.raises(Exception, match=r"(?i)probe|ffprobe|video|read"):
        bench.run_once(
            source,
            output,
            encoder="libx265",
            quality="draft",
            bit_depth=None,
            hw_decode=False,
            keep=True,
            periods=FAST,
        )
    assert not output.exists()


@pytest.mark.gpu
@pytest.mark.usefixtures("quick")
def test_an_nvenc_run_records_a_proof_tied_or_with_its_reason(sample: Any, tmp_path: Path) -> None:
    nvenc = {c.name: c for c in detect_capabilities()}["hevc_nvenc"]
    if not nvenc.available:
        pytest.skip(f"NVENC is not available: {nvenc.reason}")
    record = bench.run_once(
        sample(SAMPLE),
        tmp_path / "nvenc.mp4",
        encoder="hevc_nvenc",
        quality="draft",
        bit_depth=None,
        hw_decode=True,
        keep=False,
        periods=FAST,
    )
    # a sub-second encode is often missed by pmon, so `tied` is not asserted here; it is
    # established on footage in the window (DR-18 (1); round 5 #7)
    proof = record["nvenc_proof"]
    assert isinstance(proof["tied"], bool) and proof["pid"] is not None
    assert proof["window_s"] > 0 and proof["samples"] >= 1
    assert proof["tied"] or proof["reason"]
    assert "hevc_nvenc" in record["encode_command"]
    assert not (tmp_path / "nvenc.mp4").exists()


# --- the command line ------------------------------------------------------------------------


@pytest.fixture
def folders(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, quick: None) -> LocalConfig:
    config = LocalConfig(footage_path=tmp_path / "footage", working_path=tmp_path / "work")
    config.footage_path.mkdir()
    monkeypatch.setattr(bench, "load_local_config", lambda path=None: config)
    return config


def _snapshot(folder: Path) -> dict[str, tuple[bytes, int]]:
    return {
        str(p.relative_to(folder)): (p.read_bytes(), p.stat().st_mtime_ns)
        for p in sorted(folder.rglob("*"))
        if p.is_file()
    }


def test_the_options_follow_the_subcommand(
    folders: LocalConfig, sample: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    (folders.footage_path / "GX000003.mp4").write_bytes(sample(SAMPLE).read_bytes())
    argv = ["run", "GX000003", "--encoder", "libx265", "--quality", "draft", "--keep"]
    argv += ["--software-decode", "--memory-every", "0.05", "--gpu-every", "2"]
    argv += ["--strays-every", "1"]  # as the usage shows them (round 5 #6)
    assert bench.main(argv) == 0
    out = capsys.readouterr().out
    record = json.loads(Path(out.strip().splitlines()[-1].removeprefix("RECORD ")).read_text())
    run = record["runs"][0]
    assert Path(run["output"]).is_file() and run["decode"]["hw_decode_asked"] is False


@pytest.mark.parametrize("value", ["0", "-0.5", "nan", "inf", "soon"])
@pytest.mark.parametrize("option", ["--memory-every", "--gpu-every", "--strays-every"])
def test_a_bad_period_is_a_usage_error(
    folders: LocalConfig, option: str, value: str, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as stop:  # round 5 #3
        bench.main(["floor", "--dry-run", option, value])
    assert stop.value.code == 2
    assert "positive number of seconds" in capsys.readouterr().err


def test_floor_dry_run_resolves_every_clip(
    folders: LocalConfig, capsys: pytest.CaptureFixture[str]
) -> None:
    for stem in ("GX011627", "GX011625"):
        (folders.footage_path / f"{stem}.MP4").write_bytes(b"")
    assert bench.main(["floor", "--dry-run"]) == 0
    plan = [line for line in capsys.readouterr().out.splitlines() if line.startswith("PLAN")]
    assert plan == [
        "PLAN GX011627 x3 hevc_nvenc 8-bit standard",
        "PLAN GX011625 x1 hevc_nvenc 8-bit standard",
        "PLAN GX011627 x1 libx265 8-bit standard",
        "PLAN GX011627 x1 hevc_nvenc 10-bit standard",
    ]
    assert not list((folders.working_path / bench.SUBDIR).glob("*"))


def test_a_missing_clip_is_a_usage_error(
    folders: LocalConfig, capsys: pytest.CaptureFixture[str]
) -> None:
    assert bench.main(["floor", "--dry-run"]) == 2
    assert "not in the footage folder" in capsys.readouterr().err


def test_too_little_disk_is_a_usage_error(
    folders: LocalConfig, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (folders.footage_path / "GX000001.mp4").write_bytes(b"x" * 1000)

    def usage(path: Any) -> Any:
        return type("Usage", (), {"free": bench.DISK_MARGIN_BYTES})()

    monkeypatch.setattr(bench.shutil, "disk_usage", usage)
    assert bench.main(["run", "GX000001"]) == 2
    assert "BenchError" in capsys.readouterr().err


def test_run_writes_the_record_and_leaves_the_footage_alone(
    folders: LocalConfig, sample: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    clip = folders.footage_path / "Snorkel" / "GX000001.mp4"
    clip.parent.mkdir()
    clip.write_bytes(sample(SAMPLE).read_bytes())
    footage = _snapshot(folders.footage_path)
    argv = ["run", "GX000001", "--encoder", "libx265", "--quality", "draft", "--runs", "2"]
    argv += ["--software-decode", "--memory-every", "0.05", "--strays-every", "1"]
    assert bench.main(argv) == 0
    out = capsys.readouterr().out
    rows = [line for line in out.splitlines() if line.startswith("ROW GX000001.mp4 libx265")]
    assert len(rows) == 2
    path = Path(out.strip().splitlines()[-1].removeprefix("RECORD "))
    assert path.parent == folders.working_path / bench.SUBDIR
    record = json.loads(path.read_text(encoding="utf-8"))
    assert len(record["runs"]) == 2 and "failed" not in record
    assert [p.suffix for p in path.parent.iterdir()] == [".json"]  # outputs deleted
    assert _snapshot(folders.footage_path) == footage


def test_the_disk_is_checked_before_every_run_and_earlier_runs_are_kept(
    folders: LocalConfig,
    sample: Any,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (folders.footage_path / "GX000004.mp4").write_bytes(sample(SAMPLE).read_bytes())
    real = shutil.disk_usage
    calls: list[Path] = []

    def usage(path: Any) -> Any:
        calls.append(Path(path))
        if len(calls) <= 2:  # the check before any run and the one before run 1
            return real(path)
        return type("Usage", (), {"free": bench.DISK_MARGIN_BYTES})()

    monkeypatch.setattr(bench.shutil, "disk_usage", usage)
    argv = ["run", "GX000004", "--encoder", "libx265", "--quality", "draft", "--runs", "2"]
    assert bench.main([*argv, "--keep", "--strays-every", "1"]) == 1  # round 5 #5 and #8
    captured = capsys.readouterr()
    assert "FAILED BenchError" in captured.err and len(calls) == 3
    path = Path(captured.out.strip().splitlines()[-1].removeprefix("RECORD "))
    record = json.loads(path.read_text(encoding="utf-8"))
    assert len(record["runs"]) == 1 and Path(record["runs"][0]["output"]).is_file()
    assert record["failed"]["error"].startswith("BenchError")


def test_a_failed_run_keeps_the_record_and_exits_1(
    folders: LocalConfig, capsys: pytest.CaptureFixture[str]
) -> None:
    (folders.footage_path / "GX000002.mp4").write_bytes(b"\x00" * 64)
    assert bench.main(["run", "GX000002", "--encoder", "libx265", "--strays-every", "1"]) == 1
    out = capsys.readouterr().out
    path = Path(out.strip().splitlines()[-1].removeprefix("RECORD "))
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["runs"] == [] and record["failed"]["clip"] == "GX000002"
    assert [p.suffix for p in path.parent.iterdir()] == [".json"]
