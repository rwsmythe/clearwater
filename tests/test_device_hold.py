"""Holder readiness, stop latency and device-wide memory recovery (WDDM ruling)."""

import json
import math
import subprocess
import sys
import time
from pathlib import Path

import pytest

from video_fidelity import _nvidia_smi

pytestmark = pytest.mark.gpu
SCRIPT = Path(__file__).resolve().parents[1] / "tools/device_hold.py"


def _device_used_mib():
    text = _nvidia_smi(["--id=0", "--query-gpu=memory.used", "--format=csv,noheader,nounits"])
    if text is None:
        pytest.skip("nvidia-smi is not available; cannot verify device-wide memory")
    used = float(text.strip())
    assert math.isfinite(used) and used >= 0, text
    return used


def test_device_hold_releases_on_stop_file(tmp_path, monkeypatch):
    # Missing executable is the RED control, before any GPU initialisation.
    assert SCRIPT.is_file(), "device holder has not been built"
    # CuPy's compiler cache must also respect the cell's writable-root boundary.
    cache = tmp_path / "cupy-cache"
    cache.mkdir()
    monkeypatch.setenv("CUPY_CACHE_DIR", str(cache))
    # WDDM may report another process's live allocation as free to this process.
    # The independent witness is device-wide used memory, not parent memGetInfo.
    before = _device_used_mib()
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
            deadline = time.monotonic() + 5
            while True:
                held_used = _device_used_mib()
                if held_used - before >= 200:
                    break
                assert child.poll() is None, stderr_path.read_text(encoding="utf-8")
                assert time.monotonic() < deadline, (before, held_used, record)
                time.sleep(0.05)
            started = time.monotonic()
            stop.touch()
            child.wait(timeout=2)
            assert child.returncode == 0, stderr_path.read_text(encoding="utf-8")
            assert time.monotonic() - started < 2
            deadline = time.monotonic() + 5
            while True:
                recovered = _device_used_mib()
                # Device-wide readings include unrelated processes: allow 100 MiB drift.
                if recovered <= before + 100:
                    break
                assert time.monotonic() < deadline, (before, held_used, recovered)
                time.sleep(0.05)
            lines = stdout_path.read_text(encoding="utf-8").splitlines()
            assert len(lines) == 2
            assert json.loads(lines[1]) == {"stopped": "stop-file"}
        finally:
            stop.touch(exist_ok=True)
            if child.poll() is None:
                try:
                    child.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=5)
