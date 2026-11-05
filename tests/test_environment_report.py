from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

import environment_report

EXPECTED_KEY_ORDER = [
    "report_version",
    "timestamp_utc",
    "cpu_model",
    "cpu_physical_cores",
    "cpu_logical_cores",
    "ram_total_bytes",
    "gpu_model",
    "gpu_memory_bytes",
    "gpu_driver_version",
    "os_name",
    "os_release",
    "os_version",
    "python_version",
    "python_executable",
    "uv_version",
    "ffmpeg_version",
    "clearwater_commit",
    "machine",
    "process_architecture",
    "correction_backend",
    "correction_backend_reason",
    "encoders",
    "unavailable",
]
EXPECTED_KEYS = set(EXPECTED_KEY_ORDER)
GPU_KEYS = ("gpu_model", "gpu_memory_bytes", "gpu_driver_version")


def _completed(stdout: str, returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess([], returncode, stdout=stdout, stderr="")


class FakeRun:
    """Stand-in for subprocess.run keyed on the program name."""

    def __init__(self, **by_program: Any) -> None:
        self.by_program = by_program

    def __call__(self, command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert kwargs.get("timeout"), "every subprocess call needs a timeout"
        assert not kwargs.get("shell"), "no shell"
        outcome = self.by_program[command[0]]
        if isinstance(outcome, Exception):
            raise outcome
        assert isinstance(outcome, subprocess.CompletedProcess)
        return outcome


@pytest.fixture(autouse=True)
def stub_cpuinfo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        environment_report.cpuinfo, "get_cpu_info", lambda: {"brand_raw": "Test CPU @ 1.0GHz"}
    )


@pytest.fixture(autouse=True)
def stub_trial_seam(monkeypatch: pytest.MonkeyPatch) -> None:
    """No test here runs the product's CuPy probe or its FFmpeg encoder trials."""
    monkeypatch.setattr(environment_report, "_correction_backend", lambda: ("numpy", "CPU: stub"))
    monkeypatch.setattr(environment_report, "_encoder_rows", lambda: [])


class _SysView:
    """The tool's view of ``sys`` with another ``platform``; every other name is the real one."""

    def __init__(self, platform: str) -> None:
        self.platform = platform

    def __getattr__(self, name: str) -> Any:
        return getattr(sys, name)


@pytest.fixture
def nvidia_platform(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run the tool's NVIDIA branch on every host (Reviewer B finding 2).

    On macOS the tool never runs ``nvidia-smi`` (AD-36), so the NVIDIA parsing cases give the
    tool a non-darwin platform there: ``linux``, rebinding only the tool's own ``sys`` name, so
    no other module sees it and no Windows code path is reached. Elsewhere nothing changes.
    The darwin control (``nvidia-smi`` never run) is W-TOOL's, in ``test_portability``.
    """
    if environment_report.sys.platform == "darwin":
        monkeypatch.setattr(environment_report, "sys", _SysView("linux"))


def _healthy() -> dict[str, Any]:
    return {
        "nvidia-smi": _completed("NVIDIA Test GPU, 8188, 560.94\n"),
        "uv": _completed("uv 0.10.0 (abc 2026-01-01)\n"),
        "ffmpeg": _completed("ffmpeg version 9.0.2-full_build\nbuilt with gcc\n"),
        "git": _completed("0123456789abcdef\n"),
    }


def _run_main(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, **overrides: Any) -> dict[str, Any]:
    programs = _healthy() | overrides
    monkeypatch.setattr(environment_report.subprocess, "run", FakeRun(**programs))
    assert environment_report.main(["--out", str(tmp_path)]) == 0
    files = list((tmp_path / "reports").glob("environment-*.json"))
    assert len(files) == 1
    data: dict[str, Any] = json.loads(files[0].read_text(encoding="utf-8"))
    return data


def test_report_has_every_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    data = _run_main(tmp_path, monkeypatch)
    assert set(data) == EXPECTED_KEYS
    assert list(data) == EXPECTED_KEY_ORDER
    if environment_report.sys.platform == "darwin":  # AD-36: NVIDIA not applicable, not run
        assert data["unavailable"] == dict.fromkeys(GPU_KEYS, environment_report._NOT_APPLICABLE)
    else:
        assert data["unavailable"] == {}
    assert data["report_version"] == 1
    assert next(iter(data)) == "report_version"
    assert data["cpu_model"] == "Test CPU @ 1.0GHz"
    assert data["uv_version"] == "uv 0.10.0 (abc 2026-01-01)"
    assert data["ffmpeg_version"] == "ffmpeg version 9.0.2-full_build"
    assert data["clearwater_commit"] == "0123456789abcdef"
    assert data["timestamp_utc"].endswith("Z")
    printed = capsys.readouterr().out.strip()
    assert Path(printed).parent == tmp_path / "reports"
    assert Path(printed).name.startswith("environment-")
    assert Path(printed).name.endswith("Z.json")


@pytest.mark.usefixtures("nvidia_platform")
def test_gpu_line_parses(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    data = _run_main(tmp_path, monkeypatch)
    assert data["gpu_model"] == "NVIDIA Test GPU"
    assert data["gpu_memory_bytes"] == 8188 * 1024 * 1024
    assert data["gpu_driver_version"] == "560.94"


@pytest.mark.usefixtures("nvidia_platform")
def test_gpu_uses_first_line_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    out = _completed("First GPU, 100, 1.0\nSecond GPU, 200, 2.0\n")
    data = _run_main(tmp_path, monkeypatch, **{"nvidia-smi": out})
    assert data["gpu_model"] == "First GPU"
    assert data["gpu_memory_bytes"] == 100 * 1024 * 1024


@pytest.mark.usefixtures("nvidia_platform")
def test_nvidia_smi_absent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    data = _run_main(tmp_path, monkeypatch, **{"nvidia-smi": FileNotFoundError("nvidia-smi")})
    for key in GPU_KEYS:
        assert data[key] is None
        assert data["unavailable"][key]
    assert set(data["unavailable"]) == set(GPU_KEYS)


@pytest.mark.usefixtures("nvidia_platform")
@pytest.mark.parametrize(
    "outcome",
    [
        _completed("garbage"),
        _completed("GPU, notanumber, 1.0"),
        _completed("GPU, -1, 1.0"),
        _completed("", 0),
        _completed("GPU, 100, 1.0", 9),
        subprocess.TimeoutExpired("nvidia-smi", 1),
    ],
)
def test_nvidia_smi_bad_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, outcome: Any
) -> None:
    data = _run_main(tmp_path, monkeypatch, **{"nvidia-smi": outcome})
    for key in GPU_KEYS:
        assert data[key] is None
        assert data["unavailable"][key]


@pytest.mark.usefixtures("nvidia_platform")
def test_ffmpeg_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    data = _run_main(tmp_path, monkeypatch, ffmpeg=_completed("", 1))
    assert data["ffmpeg_version"] is None
    assert "ffmpeg" in data["unavailable"]["ffmpeg_version"]
    assert data["gpu_model"] == "NVIDIA Test GPU"


def test_cpuinfo_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom() -> dict[str, Any]:
        raise RuntimeError("no cpu")

    monkeypatch.setattr(environment_report.cpuinfo, "get_cpu_info", boom)
    data = _run_main(tmp_path, monkeypatch)
    assert data["cpu_model"] is None
    assert "cpu_model" in data["unavailable"]


@pytest.mark.usefixtures("nvidia_platform")
def test_psutil_failures_degrade(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom() -> object:
        raise OSError("psutil boom")

    monkeypatch.setattr(environment_report.psutil, "virtual_memory", boom)
    monkeypatch.setattr(environment_report.psutil, "cpu_count", lambda logical=True: None)
    data = _run_main(tmp_path, monkeypatch)
    for key in ("ram_total_bytes", "cpu_physical_cores", "cpu_logical_cores"):
        assert data[key] is None
        assert data["unavailable"][key]
    assert data["gpu_model"] == "NVIDIA Test GPU"


def test_config_used_when_no_out(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    working = tmp_path / "work"
    config = tmp_path / "cfg.toml"
    config.write_text(
        f"footage_path = '{tmp_path / 'footage'}'\nworking_path = '{working}'\n", encoding="utf-8"
    )
    monkeypatch.setattr(environment_report.subprocess, "run", FakeRun(**_healthy()))
    assert environment_report.main(["--config", str(config)]) == 0
    assert len(list((working / "reports").glob("environment-*.json"))) == 1


def test_missing_config_without_out_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert environment_report.main(["--config", str(tmp_path / "absent.toml")]) == 2
    assert "clearwater.local.example.toml" in capsys.readouterr().err


def test_out_never_reads_the_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(path: Path | None = None) -> object:
        raise AssertionError("--out must not read the configuration")

    monkeypatch.setattr(environment_report, "load_local_config", boom)
    monkeypatch.setattr(environment_report.subprocess, "run", FakeRun(**_healthy()))
    assert environment_report.main(["--out", str(tmp_path)]) == 0


def test_run_decodes_undecodable_output_with_replacement() -> None:
    code = "import sys; sys.stdout.buffer.write(b'ab\\xff\\n')"
    assert environment_report._run([sys.executable, "-c", code]) == "ab\ufffd"


def test_same_second_reports_never_overwrite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        environment_report,
        "collect",
        lambda: {"timestamp_utc": "2026-01-02T03:04:05Z", "marker": 0},
    )
    for _ in range(3):
        assert environment_report.main(["--out", str(tmp_path)]) == 0
    names = sorted(p.name for p in (tmp_path / "reports").iterdir())
    assert names == [
        "environment-20260102T030405Z-1.json",
        "environment-20260102T030405Z-2.json",
        "environment-20260102T030405Z.json",
    ]


def test_unwritable_reports_dir_returns_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(environment_report.subprocess, "run", FakeRun(**_healthy()))
    (tmp_path / "reports").write_text("a file, not a directory", encoding="utf-8")
    assert environment_report.main(["--out", str(tmp_path)]) == 2
    err = capsys.readouterr().err.strip()
    assert err.startswith("error: ")
    assert "\n" not in err
