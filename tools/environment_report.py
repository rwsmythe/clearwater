"""Record the machine's hardware and toolchain as a JSON report in the working folder.

Usage::

    uv run python tools/environment_report.py [--config PATH] [--out DIR]

The report lands in ``<working>/reports/environment-<YYYYMMDDTHHMMSSZ>.json``. A probe
that cannot run (tool absent, non-zero exit, unparsable output, timeout) yields
``null`` for its fields and a one-line reason under ``unavailable``; the report is
still written. Only portable standard-library and third-party calls are used.
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import cpuinfo
import psutil

from local_config import LocalConfigError, load_local_config

REPO_ROOT = Path(__file__).resolve().parent.parent
PROBE_TIMEOUT_SECONDS = 20.0
_MIB = 1024 * 1024
_GPU_KEYS = ("gpu_model", "gpu_memory_bytes", "gpu_driver_version")
_NVIDIA_SMI = [
    "nvidia-smi",
    "--query-gpu=name,memory.total,driver_version",
    "--format=csv,noheader,nounits",
]


class ProbeError(Exception):
    """A probe could not produce its value; the message is a one-line reason."""


def _run(command: list[str], cwd: Path | None = None) -> str:
    """Run a command without a shell and return its stripped standard output.

    Args:
        command: The program and its arguments.
        cwd: Working directory for the child process, if any.

    Returns:
        The standard output, stripped of surrounding whitespace.

    Raises:
        ProbeError: If the program is absent, times out, fails or prints nothing.
    """
    name = command[0]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=PROBE_TIMEOUT_SECONDS,
            check=False,
            cwd=cwd,
        )
    except FileNotFoundError:
        raise ProbeError(f"{name} not found") from None
    except subprocess.TimeoutExpired:
        raise ProbeError(f"{name} timed out after {PROBE_TIMEOUT_SECONDS:g} s") from None
    except OSError as exc:
        raise ProbeError(f"{name} could not run: {exc}") from None
    if result.returncode != 0:
        raise ProbeError(f"{name} exited with status {result.returncode}")
    output = result.stdout.strip()
    if not output:
        raise ProbeError(f"{name} printed nothing")
    return output


def _first_line(command: list[str], cwd: Path | None = None) -> str:
    return _run(command, cwd).splitlines()[0].strip()


def parse_nvidia_smi(output: str) -> tuple[str, int, str]:
    """Parse the first line of ``nvidia-smi`` CSV output.

    Args:
        output: Text of the form ``<name>, <memory MiB>, <driver version>``.

    Returns:
        The model name, the memory in bytes, and the driver version.

    Raises:
        ProbeError: If the first line does not have that form.
    """
    line = output.splitlines()[0] if output.strip() else ""
    parts = [part.strip() for part in line.rsplit(",", 2)]
    if len(parts) != 3 or not all(parts):
        raise ProbeError("nvidia-smi output could not be parsed")
    try:
        memory_mib = int(parts[1])
    except ValueError:
        raise ProbeError("nvidia-smi memory is not an integer") from None
    if memory_mib < 0:
        raise ProbeError("nvidia-smi memory is negative")
    return parts[0], memory_mib * _MIB, parts[2]


def _cpu_model() -> str:
    try:
        brand = cpuinfo.get_cpu_info().get("brand_raw")
    except Exception as exc:  # cpuinfo probes many sources and can fail in many ways.
        raise ProbeError(f"cpuinfo failed: {type(exc).__name__}") from None
    if not isinstance(brand, str) or not brand:
        raise ProbeError("cpuinfo reported no brand_raw")
    return brand


def _psutil_value(what: str, read: Callable[[], int | None]) -> int:
    """Read one psutil figure, turning any failure into a ``ProbeError``."""
    try:
        value = read()
    except Exception as exc:  # psutil raises OSError, RuntimeError and others.
        raise ProbeError(f"psutil could not read {what}: {type(exc).__name__}") from None
    if value is None:
        raise ProbeError(f"psutil could not read {what}")
    return value


def collect() -> dict[str, object]:
    """Probe the machine and return the report as a JSON-ready dictionary.

    Returns:
        The report; failed probes hold ``None`` and are explained in ``unavailable``.
    """
    unavailable: dict[str, str] = {}
    report: dict[str, object] = {
        "timestamp_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    def probe(keys: tuple[str, ...], produce: Callable[[], tuple[object, ...]]) -> None:
        try:
            values = produce()
        except ProbeError as exc:
            for key in keys:
                report[key] = None
                unavailable[key] = str(exc)
            return
        for key, value in zip(keys, values, strict=True):
            report[key] = value

    probe(("cpu_model",), lambda: (_cpu_model(),))
    probe(
        ("cpu_physical_cores",),
        lambda: (_psutil_value("physical cores", lambda: psutil.cpu_count(logical=False)),),
    )
    probe(
        ("cpu_logical_cores",),
        lambda: (_psutil_value("logical cores", lambda: psutil.cpu_count(logical=True)),),
    )
    probe(
        ("ram_total_bytes",),
        lambda: (_psutil_value("total memory", lambda: psutil.virtual_memory().total),),
    )
    probe(_GPU_KEYS, lambda: parse_nvidia_smi(_run(_NVIDIA_SMI)))
    report["os_name"] = platform.system()
    report["os_release"] = platform.release()
    report["os_version"] = platform.version()
    report["python_version"] = platform.python_version()
    report["python_executable"] = sys.executable
    probe(("uv_version",), lambda: (_first_line(["uv", "--version"]),))
    probe(("ffmpeg_version",), lambda: (_first_line(["ffmpeg", "-version"]),))
    probe(("clearwater_commit",), lambda: (_first_line(["git", "rev-parse", "HEAD"], REPO_ROOT),))
    report["unavailable"] = unavailable
    return report


def main(argv: list[str] | None = None) -> int:
    """Write the environment report and print its path.

    Args:
        argv: Command-line arguments; defaults to ``sys.argv[1:]``.

    Returns:
        0 on success, 2 when the working folder cannot be determined.
    """
    parser = argparse.ArgumentParser(description="Write an environment report JSON file.")
    parser.add_argument("--config", type=Path, help="local configuration file to read")
    parser.add_argument(
        "--out", type=Path, help="working folder to use instead of the configured one"
    )
    args = parser.parse_args(argv)

    if args.out is not None:
        working = args.out
    else:
        try:
            working = load_local_config(args.config).working_path
        except LocalConfigError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

    report = collect()
    stamp = str(report["timestamp_utc"]).replace("-", "").replace(":", "")
    reports_dir = working / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    target = reports_dir / f"environment-{stamp}.json"
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
