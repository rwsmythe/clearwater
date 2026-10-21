"""WP3.16 dependency rule (plan 8.1, frame rule 5, spec 10.1) and the AD-25 (a) source rules.

No ``clearwater.gui`` module imports ``clearwater.methods``, ``cupy`` or ``cupyx`` or touches
``CoreBackend.xp``; none uses ``QSettings``; and importing ``clearwater.core``, ``.config``,
``.jobs`` or ``.io`` still loads no PySide6.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import clearwater.gui

GUI_DIR = Path(clearwater.gui.__file__).parent
FORBIDDEN = ("clearwater.methods", "cupy", "cupyx")


def _modules() -> list[Path]:
    paths = sorted(GUI_DIR.glob("*.py"))
    assert len(paths) >= 10
    return paths


def test_no_gui_module_imports_methods_or_cupy() -> None:
    for path in _modules():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                names = [node.module] + [f"{node.module}.{a.name}" for a in node.names]
            for name in names:
                assert not any(name == f or name.startswith(f + ".") for f in FORBIDDEN), (
                    f"{path.name} imports {name}"
                )
            if isinstance(node, ast.ImportFrom) and node.module == "clearwater":
                assert all(a.name != "methods" for a in node.names), path.name
            if isinstance(node, ast.Attribute):
                assert node.attr != "xp", f"{path.name} touches .xp"


def _code_names(tree: ast.AST) -> set[str]:
    """Names, attributes, imported names and string constants that are not docstrings."""
    docstrings = {
        id(node.body[0].value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef)
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
    }
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            found.add(node.id)
        elif isinstance(node, ast.Attribute):
            found.add(node.attr)
        elif isinstance(node, ast.alias):
            found.add(node.name)
        elif (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstrings
        ):
            found.add(node.value)
    return found


def test_no_gui_module_uses_qsettings_or_resolves_app_data_itself() -> None:
    calls = 0
    for path in _modules():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = _code_names(tree)
        assert "QSettings" not in names, path.name
        assert not {"APPDATA", "LOCALAPPDATA", "XDG_CONFIG_HOME", "home", "environ"} & names, (
            path.name
        )
        calls += sum(
            1
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "app_locations"
        )
    assert calls == 1  # only run(), when no locations are given


def test_core_config_jobs_io_still_load_no_pyside6() -> None:
    code = (
        "import sys\n"
        "import clearwater.core, clearwater.config, clearwater.jobs, clearwater.io\n"
        "import clearwater.io.video\n"
        "bad = sorted(m for m in sys.modules if m.split('.')[0] in ('PySide6', 'shiboken6'))\n"
        "print(','.join(bad))\n"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True, timeout=120
    )
    assert out.stdout.strip() == ""


def test_importing_the_gui_loads_no_cupy() -> None:
    code = (
        "import sys\n"
        "import clearwater.gui, clearwater.gui.shell\n"
        "bad = sorted(m for m in sys.modules if m.split('.')[0] in ('cupy', 'cupyx'))\n"
        "print(','.join(bad))\n"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True, timeout=120
    )
    assert out.stdout.strip() == ""
