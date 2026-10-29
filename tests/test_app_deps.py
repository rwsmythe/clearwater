"""Layering of ``clearwater.app`` (WP4.1; WP4.3 ruling Q15; CHARC ruling flag (3); spec 10.1).

The ONE ``clearwater.gui`` -> ``clearwater.app`` edge is ``gui/engines.py`` importing
``clearwater.app.composition``; ``app/`` holds exactly the root, its package file and WP4.3's
four modules; no ``clearwater.app`` module but ``main.py`` imports ``clearwater.gui``, PySide6 or
``shiboken6``; none imports ``cupy`` or ``cupyx``; and importing ``clearwater.app`` or
``clearwater.app.composition`` loads no PySide6 and no CuPy.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

import clearwater

SRC = Path(clearwater.__file__).parent
EDGE = ("engines.py", "clearwater.app.composition")


def _absolute(node: ast.ImportFrom, package: str) -> str:
    """Return the absolute module of an import, a relative one resolved inside ``package``."""
    if not node.level:
        return node.module or ""
    parts = package.split(".")
    base = ".".join(parts[: len(parts) - node.level + 1])
    return f"{base}.{node.module}" if node.module else base


def imported_modules(source: str, package: str) -> set[str]:
    """Return every module a source imports, relative imports resolved inside ``package``."""
    found: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = _absolute(node, package)
            found.add(module)
            found.update(f"{module}.{alias.name}" for alias in node.names)
    return found


def app_edges(gui_dir: Path) -> list[tuple[str, str]]:
    """Return ``(gui file, imported module)`` for every gui import of ``clearwater.app``.

    ``from clearwater.app import composition`` counts as importing ``clearwater.app.composition``;
    any other name imported from ``clearwater.app`` counts as importing the package.
    """
    edges: list[tuple[str, str]] = []
    for path in sorted(gui_dir.glob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            targets: list[str] = []
            if isinstance(node, ast.Import):
                targets = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                module = _absolute(node, "clearwater.gui")
                if module == "clearwater":
                    targets = [f"clearwater.{a.name}" for a in node.names if a.name == "app"]
                elif module == "clearwater.app":
                    targets = [
                        "clearwater.app.composition" if a.name == "composition" else module
                        for a in node.names
                    ]
                else:
                    targets = [module]
            edges.extend(
                (path.name, t)
                for t in targets
                if t == "clearwater.app" or t.startswith("clearwater.app.")
            )
    return sorted(set(edges))


def test_the_one_gui_to_app_edge_is_engines_to_the_root() -> None:
    assert app_edges(SRC / "gui") == [EDGE]


def test_a_planted_second_edge_is_reported(tmp_path: Path) -> None:
    (tmp_path / "engines.py").write_text(
        "from clearwater.app import composition\n", encoding="utf-8"
    )
    (tmp_path / "shell.py").write_text("import clearwater.app\n", encoding="utf-8")
    assert app_edges(tmp_path) == [EDGE, ("shell.py", "clearwater.app")]


APP_MODULES = [
    "__init__.py",
    "activity.py",
    "analysis_adapter.py",
    "composition.py",
    "main.py",
    "startup.py",
]
"""The ``clearwater.app`` modules: WP4.1's two and WP4.3's four (ruling Q2)."""


def test_no_app_module_but_main_imports_the_gui_or_qt_and_none_imports_cupy() -> None:
    paths = sorted((SRC / "app").glob("*.py"))
    assert [p.name for p in paths] == APP_MODULES
    for path in paths:
        names = imported_modules(path.read_text(encoding="utf-8"), "clearwater.app")
        gpu = sorted(n for n in names if n.split(".")[0] in ("cupy", "cupyx"))
        assert gpu == [], path.name
        if path.name == "main.py":
            continue
        bad = sorted(
            n
            for n in names
            if n.split(".")[0] in ("PySide6", "shiboken6")
            or n == "clearwater.gui"
            or n.startswith("clearwater.gui.")
        )
        assert bad == [], path.name


@pytest.mark.parametrize("module", ["clearwater.app", "clearwater.app.composition"])
def test_importing_the_app_loads_no_pyside6_and_no_cupy(module: str) -> None:
    code = (
        "import sys, importlib\n"
        f"importlib.import_module({module!r})\n"
        "bad = sorted(m for m in sys.modules\n"
        "             if m.split('.')[0] in ('PySide6', 'shiboken6', 'cupy', 'cupyx'))\n"
        "print(','.join(bad))\n"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True, timeout=120
    )
    assert out.stdout.strip() == ""


def test_the_load_check_sees_a_planted_qt_import() -> None:
    code = (
        "import sys\n"
        "import clearwater.app, PySide6.QtCore\n"
        "print(','.join(sorted(m for m in sys.modules if m.split('.')[0] == 'PySide6')))\n"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True, timeout=120
    )
    assert "PySide6.QtCore" in out.stdout
