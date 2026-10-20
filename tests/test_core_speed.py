"""WP3.1: the speed-row instrument ``tools/core_speed.py`` without footage or a GPU."""

from __future__ import annotations

import subprocess
from typing import Any

import pytest

import core_speed


def fake_run(returncode: int, stdout: str, stderr: str = "") -> Any:
    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, returncode, stdout, stderr)

    return run


def test_gpu_snapshot_reads_one_line(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(core_speed.subprocess, "run", fake_run(0, "2100, 8001, 61, 97, 3100, 80\n"))
    snapshot = core_speed.gpu_snapshot()
    assert snapshot["clocks.sm"] == "2100" and snapshot["power.draw"] == "80"


@pytest.mark.parametrize(
    ("returncode", "stdout", "stderr"),
    [(9, "", "NVIDIA-SMI has failed"), (0, "", ""), (6, "No devices were found\n", "")],
)
def test_gpu_snapshot_failure_is_recorded(
    monkeypatch: pytest.MonkeyPatch, returncode: int, stdout: str, stderr: str
) -> None:
    # Round 1 F7: a failing nvidia-smi neither raises nor passes for a reading.
    monkeypatch.setattr(core_speed.subprocess, "run", fake_run(returncode, stdout, stderr))
    snapshot = core_speed.gpu_snapshot()
    assert list(snapshot) == ["unavailable"]
    assert snapshot["unavailable"].startswith(f"nvidia-smi exit {returncode}")


def test_gpu_snapshot_without_nvidia_smi(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(command: list[str], **kwargs: Any) -> Any:
        raise FileNotFoundError(command[0])

    monkeypatch.setattr(core_speed.subprocess, "run", missing)
    assert core_speed.gpu_snapshot() == {"unavailable": "nvidia-smi did not run: FileNotFoundError"}
