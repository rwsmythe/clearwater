"""Prove the gate's thread timeout terminates a hung pytest process with a stack."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_inner(
    root: Path, sleep_seconds: float, *, fixture_sleep_seconds: float = 0.0
) -> tuple[subprocess.CompletedProcess[str], float]:
    """Run a sleeping test and a following sentinel test with the real gate ini."""
    root.mkdir()
    inner_test = root / "test_planted.py"
    fixture_source = (
        "import pytest\n\n\n"
        "@pytest.fixture(scope='session', autouse=True)\n"
        "def slow_session():\n"
        '    """Prove fixture setup is excluded from the function timeout."""\n'
        f"    time.sleep({fixture_sleep_seconds!r})\n\n\n"
        if fixture_sleep_seconds
        else ""
    )
    inner_test.write_text(
        '"""A planted hang followed by a process-survival sentinel."""\n'
        "import time\n"
        "from pathlib import Path\n\n\n"
        f"{fixture_source}def test_planted_sleep():\n"
        '    """Sleep for the duration chosen by the outer proof."""\n'
        f"    time.sleep({sleep_seconds!r})\n\n\n"
        "def test_after_sleep():\n"
        '    """Record whether this invocation survived the preceding test."""\n'
        "    Path(__file__).with_name('after-sleep-ran').write_text('ran')\n",
        encoding="utf-8",
    )
    env = {key: value for key, value in os.environ.items() if key != "PYTEST_ADDOPTS"}
    sandbox_args: list[str] = []
    if "sandbox_mkdir_shim" in sys.modules:
        env["PYTHONPATH"] = str(REPO_ROOT / "scripts")
        sandbox_args = ["-p", "sandbox_mkdir_shim"]
    started = time.monotonic()
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-c",
            str(REPO_ROOT / "pyproject.toml"),
            "--confcutdir",
            str(root),
            "--basetemp",
            str(root / "tmp"),
            "--timeout",
            "2",
            "-p",
            "no:cacheprovider",
            *sandbox_args,
            str(inner_test),
        ],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    elapsed = time.monotonic() - started
    (root / "pytest-output.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
    (root / "pytest-result.txt").write_text(
        f"exit={result.returncode}\nelapsed={elapsed:.3f}s\n", encoding="utf-8"
    )
    return result, elapsed


def test_thread_timeout_exits_with_stack_and_under_bound_control(tmp_path: Path) -> None:
    """Prove an over-bound sleep exits before its sentinel, while the control passes.

    Args:
        tmp_path: Isolated directory for both inner pytest invocations and their logs.
    """
    # On Windows, omitting timeout_method still falls back to thread (no SIGALRM).
    with ThreadPoolExecutor(max_workers=2) as executor:
        control_future = executor.submit(
            _run_inner, tmp_path / "control", 0.01, fixture_sleep_seconds=2.5
        )
        expired_future = executor.submit(_run_inner, tmp_path / "expired", 30.0)
        control, _ = control_future.result()
        expired, elapsed = expired_future.result()
    control_output = control.stdout + control.stderr
    expired_output = expired.stdout + expired.stderr

    assert control.returncode == 0, control_output
    assert "2 passed" in control_output, control_output
    assert (tmp_path / "control" / "after-sleep-ran").read_text() == "ran"
    assert expired.returncode != 0, expired_output
    assert elapsed < 15, f"Inner timeout took {elapsed:.3f} s; output:\n{expired_output}"
    assert "Timeout" in expired_output, expired_output
    assert "test_planted_sleep" in expired_output, expired_output
    assert not (tmp_path / "expired" / "after-sleep-ran").exists(), expired_output
