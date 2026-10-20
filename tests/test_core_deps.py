"""WP3.1: the dependency rule (plan 8.1, frame rule 5, ruling 1.1) and CuPy being optional."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "clearwater"

FORBIDDEN_TOP = {"PIL", "av", "PySide6", "cupy", "cupyx"}
FORBIDDEN_PACKAGES = ("clearwater.io", "clearwater.jobs", "clearwater.gui", "clearwater.methods")


def run_python(code: str) -> str:
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=120, check=False
    )
    assert result.returncode == 0, result.stderr[-2000:]
    return result.stdout.strip().splitlines()[-1]


def test_import_loads_nothing_forbidden() -> None:
    code = (
        "import json, sys\n"
        "import clearwater.core\n"
        f"top = {sorted(FORBIDDEN_TOP)!r}\n"
        f"packages = {FORBIDDEN_PACKAGES!r}\n"
        "bad = sorted(m for m in sys.modules if m.split('.')[0] in top\n"
        "             or any(m == p or m.startswith(p + '.') for p in packages))\n"
        "print(json.dumps(bad))\n"
    )
    assert json.loads(run_python(code)) == []


def test_core_works_with_cupy_unimportable() -> None:
    code = (
        "import sys\n"
        "sys.modules['cupy'] = None\n"
        "sys.modules['cupyx'] = None\n"
        "import numpy as np\n"
        "from clearwater.core import NumpyBackend, select_backend, gaussian_pyramid\n"
        "from clearwater.interfaces.settings import Settings\n"
        "b = NumpyBackend()\n"
        "a = b.asarray(np.random.default_rng(0).random((9, 7, 3), dtype=np.float32))\n"
        "assert b.gaussian_blur(a, 1.0).dtype == np.float32\n"
        "assert len(gaussian_pyramid(b, a, 3)) == 3\n"
        "backend, reason = select_backend(Settings(), 2160, 3840, 'c3')\n"
        "print(backend.name + '|' + reason)\n"
    )
    assert run_python(code) == "numpy|CPU: CuPy not installed"


def violations(source: str, in_core: bool) -> list[str]:
    """The dependency-rule violations of one module's source."""
    found = []
    for node in ast.walk(ast.parse(source)):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names = [node.module]
        elif isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "import_module":
            names = [arg.value for arg in node.args if isinstance(arg, ast.Constant)]
        for name in names:
            top = str(name).split(".")[0]
            if top in {"cupy", "cupyx"} and not in_core:
                found.append(f"imports {name}")
            if top in {"prototype", "tools"}:
                found.append(f"imports {name}")
        if isinstance(node, ast.Attribute) and node.attr == "xp" and not in_core:
            found.append(f"reads .xp at line {node.lineno}")
    return found


def test_static_rule_over_src() -> None:
    problems = {}
    for path in sorted(SRC.rglob("*.py")):
        in_core = (SRC / "core") in path.parents
        found = violations(path.read_text(encoding="utf-8"), in_core)
        if found:
            problems[str(path.relative_to(SRC))] = found
    assert problems == {}
    assert (SRC / "core" / "backend.py").is_file()  # the walk saw the core package


def test_static_rule_catches_planted_violations() -> None:
    planted = (
        "import cupy\n"
        "from cupyx.scipy import ndimage\n"
        "import importlib\n"
        "m = importlib.import_module('cupy')\n"
        "from prototype import pipeline\n"
        "def f(backend):\n"
        "    return backend.xp.zeros(3)\n"
    )
    found = violations(planted, in_core=False)
    assert sorted(found) == [
        "imports cupy",
        "imports cupy",
        "imports cupyx.scipy",
        "imports prototype",
        "reads .xp at line 7",
    ]
    assert violations(planted, in_core=True) == ["imports prototype"]
