"""The dependency rule (plan 8.1, frame rule 5): ``clearwater.analysis`` loads no upper package."""

from __future__ import annotations

import subprocess
import sys

FORBIDDEN = (
    "clearwater.gui",
    "clearwater.jobs",
    "clearwater.io",
    "clearwater.methods",
    "clearwater.cache",
    "clearwater.core",
    "PySide6",
    "cupy",
    "PIL",
    "scipy",
)

PROBE = f"""
import sys
import clearwater.analysis
bad = sorted(m for m in sys.modules if m.startswith({FORBIDDEN!r}))
print("BAD:" + ",".join(bad))
"""


def test_importing_analysis_loads_no_forbidden_module() -> None:
    """A fresh interpreter importing ``clearwater.analysis`` loads none of the forbidden modules."""
    completed = subprocess.run(
        [sys.executable, "-c", PROBE], capture_output=True, text=True, check=True, timeout=120
    )
    line = next(text for text in completed.stdout.splitlines() if text.startswith("BAD:"))
    assert line == "BAD:", line


def test_the_probe_detects_a_forbidden_import() -> None:
    """The planted import of a forbidden package is reported (the probe distinguishes)."""
    planted = PROBE.replace("import clearwater.analysis", "import clearwater.cache")
    completed = subprocess.run(
        [sys.executable, "-c", planted], capture_output=True, text=True, check=True, timeout=120
    )
    assert "clearwater.cache" in completed.stdout
