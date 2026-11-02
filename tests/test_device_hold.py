"""Real cross-process device hold and release; no performance figure is recorded."""

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.gpu
SCRIPT = Path(__file__).resolve().parents[1] / "tools/device_hold.py"


def test_device_hold_releases_on_stop_file(tmp_path, monkeypatch):
    # Missing executable is the RED control, before any GPU initialisation.
    assert SCRIPT.is_file(), "device holder has not been built"
    # CuPy's compiler cache must also respect the cell's writable-root boundary.
    cache = tmp_path / "cupy-cache"
    cache.mkdir()
    monkeypatch.setenv("CUPY_CACHE_DIR", str(cache))
    from clearwater.core.backend import backend_for

    try:
        backend = backend_for("cuda:0")
    except (ImportError, RuntimeError) as error:
        pytest.skip(f"CUDA unavailable: {error}")
    backend.xp.cuda.runtime.free(0)
    before = backend.free_device_bytes()
    assert before is not None
    stop = tmp_path / "hold.stop"
    stdout_path = tmp_path / "holder.jsonl"
    stderr_path = tmp_path / "holder.stderr"
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        child = subprocess.Popen(
            [
                sys.executable,
                str(SCRIPT),
                "--mib",
                "256",
                "--stop-file",
                str(stop),
                "--timeout-s",
                "60",
            ],
            stdout=stdout,
            stderr=stderr,
        )
        try:
            deadline = time.monotonic() + 30
            while not stdout_path.read_bytes().endswith(b"\n"):
                assert child.poll() is None, stderr_path.read_text(encoding="utf-8")
                assert time.monotonic() < deadline, "holder readiness timeout"
                time.sleep(0.02)
            record = json.loads(stdout_path.read_text(encoding="utf-8"))
            assert record["held_bytes"] >= 256 * 2**20
            assert record["free_before"] - record["free_after"] >= 256 * 2**20
            held_free = backend.free_device_bytes()
            assert held_free is not None and before - held_free >= 256 * 2**20
            started = time.monotonic()
            stop.touch()
            child.wait(timeout=2)
            assert child.returncode == 0, stderr_path.read_text(encoding="utf-8")
            while True:
                recovered = backend.free_device_bytes()
                if recovered is not None and recovered >= before:
                    break
                assert time.monotonic() - started < 2, (before, held_free, recovered)
                time.sleep(0.01)
            assert time.monotonic() - started < 2
            assert len(stdout_path.read_text(encoding="utf-8").splitlines()) == 1
        finally:
            stop.touch(exist_ok=True)
            if child.poll() is None:
                try:
                    child.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=5)
