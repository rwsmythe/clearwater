"""Rule tests of the photo package (WP3.6): layout, imports, dependencies, the real-photo leg.

- The package has the modules the ledger names and imports nothing from the GUI, jobs, methods,
  core, PySide6, cupy or av (plan 8.1, frame rule 5); ``src/`` does not import ``tools``.
- The dependency lines of ``pyproject.toml`` are exactly the WP3.6 grant (X-B3).
"""

from __future__ import annotations

import ast
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE = REPO_ROOT / "src" / "clearwater" / "io" / "photo"
FORBIDDEN_PREFIXES = (
    "clearwater.gui",
    "clearwater.jobs",
    "clearwater.methods",
    "clearwater.core",
    "PySide6",
    "cupy",
    "av",
    "tools",
)


def test_the_package_has_the_expected_modules() -> None:
    assert {p.name for p in PACKAGE.glob("*.py")} >= {
        "__init__.py",
        "color.py",
        "errors.py",
        "exif.py",
        "heif_boxes.py",
        "icc.py",
        "orientation.py",
        "png.py",
        "reader.py",
        "tiff.py",
        "writer.py",
    }


@pytest.mark.parametrize("module", sorted(PACKAGE.glob("*.py")), ids=lambda p: p.name)
def test_no_module_imports_a_forbidden_package(module: Path) -> None:
    tree = ast.parse(module.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names = [node.module]
        for name in names:
            top = name.split(".")[0]
            assert not any(
                name == bad or name.startswith(bad + ".") or top == bad
                for bad in FORBIDDEN_PREFIXES
            ), f"{module.name} imports {name}"


def test_importing_the_package_loads_nothing_forbidden() -> None:
    code = (
        "import sys, clearwater.io.photo\n"
        "bad = [m for m in sys.modules if m.split('.')[0] in {'PySide6', 'cupy', 'av'} "
        "or m.startswith(('clearwater.gui', 'clearwater.jobs', 'clearwater.methods', "
        "'clearwater.core'))]\n"
        "print(bad)\n"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", code], capture_output=True, text=True, check=True
    )
    assert result.stdout.strip() == "[]", result.stdout


def test_the_photo_sink_never_names_an_output_beside_the_source() -> None:
    text = (PACKAGE / "writer.py").read_text(encoding="utf-8") + (PACKAGE / "png.py").read_text(
        encoding="utf-8"
    )
    for token in ("with_suffix", "with_name", ".parent", "shutil", "os.rename", "os.replace"):
        assert token not in text, token


def test_the_dependency_lines_are_the_wp36_grant() -> None:
    config = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    runtime = config["project"]["dependencies"]
    dev = config["dependency-groups"]["dev"]

    def has(lines: list[str], name: str) -> bool:
        return any(line.replace(" ", "").lower().startswith(name + (">=")) for line in lines)

    for name in ("pillow", "pillow-heif", "tifffile"):
        assert has(runtime, name), name
        assert not has(dev, name), f"{name} must leave the dev group"
    tifffile_line = next(line for line in runtime if line.startswith("tifffile"))
    assert "<" in tifffile_line, "tifffile needs a bounded range"
    for banned in ("piexif", "imagecodecs", "pypng", "exiftool"):
        assert not any(banned in line.lower() for line in runtime + dev), banned
