"""WP3.5: the dependency rule for ``clearwater.color`` (plan 8.1, frame rule 5)."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "clearwater" / "color"

FORBIDDEN_TOP = ["PIL", "av", "PySide6", "cupy", "cupyx"]
FORBIDDEN_PACKAGES = [
    "clearwater.io",
    "clearwater.core",
    "clearwater.methods",
    "clearwater.jobs",
    "clearwater.gui",
    "clearwater.config",
]


def test_import_loads_nothing_above_it_and_starts_no_process() -> None:
    code = (
        "import json, subprocess, sys\n"
        "def refuse(*a, **k):\n"
        "    raise AssertionError('a process was started')\n"
        "subprocess.Popen.__init__ = refuse\n"
        "import clearwater.color\n"
        "import clearwater.color.swscale, clearwater.color.samples\n"
        f"top = {FORBIDDEN_TOP!r}\n"
        f"packages = {FORBIDDEN_PACKAGES!r}\n"
        "bad = sorted(m for m in sys.modules if m.split('.')[0] in top\n"
        "             or any(m == p or m.startswith(p + '.') for p in packages))\n"
        "print(json.dumps(bad))\n"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", code], capture_output=True, text=True, timeout=120, check=False
    )
    assert result.returncode == 0, result.stderr[-2000:]
    assert json.loads(result.stdout.strip().splitlines()[-1]) == []


def test_sources_import_only_interfaces_stdlib_and_numpy() -> None:
    allowed = {"numpy", "clearwater"}
    for path in sorted(SRC.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                names = [node.module or ""]
            else:
                continue
            for name in names:
                top = name.split(".")[0]
                if top == "clearwater":
                    assert name.startswith(("clearwater.color", "clearwater.interfaces")), (
                        path.name,
                        name,
                    )
                else:
                    assert top in allowed | set(sys.stdlib_module_names) | {"__future__"}, (
                        path.name,
                        name,
                    )


def test_no_run_of_a_process_in_the_sources() -> None:
    for path in sorted(SRC.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        for word in ("subprocess", "os.system", "Popen"):
            assert word not in text, (path.name, word)
