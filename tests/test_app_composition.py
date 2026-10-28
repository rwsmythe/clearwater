"""WP4.1 composition root (``clearwater.app.composition``): fresh real components, the routing.

Covers task 3: every function returns a fresh real component; ``"c3"`` is first (D16); the
selection is ``clearwater.core.select_backend`` itself; ``export_jobs`` exports a photo through
the real reader, method and writer and fails a video with ``UNAVAILABLE_TEXT`` writing nothing
(question 4); importing the root loads no PySide6 or CuPy and builds nothing; and no other module
under ``src/clearwater`` constructs the real photo engines (a static test with a planted control).
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

import clearwater
from clearwater import core
from clearwater.app import composition
from clearwater.config import new_parameter_set
from clearwater.interfaces import JobResult, Settings
from clearwater.interfaces.stubs import StubProgress
from clearwater.io.photo import PhotoReader, PhotoWriter
from clearwater.jobs.export_seam import UNAVAILABLE_TEXT, ExportRequest
from clearwater.methods import AncutiFusionMethod

SRC = Path(clearwater.__file__).parent
BUILDERS = frozenset({"ExportEngine", "PhotoReader", "PhotoWriter", "available_methods"})
ALLOWED = {
    ("io/photo/reader.py", "read_photo", "PhotoReader"),
    ("io/photo/writer.py", "write_photo", "PhotoWriter"),
}
"""The defining modules' own conveniences, excepted by name (task 3)."""


def builders_outside_the_root(relative: str, source: str) -> list[str]:
    """Return ``"<file>:<line> <name>"`` for every call that builds a real photo engine.

    Calls inside ``app/composition.py`` and the :data:`ALLOWED` conveniences are not reported.
    """
    if relative == "app/composition.py":
        return []
    found: list[str] = []

    def visit(node: ast.AST, function: str) -> None:
        for child in ast.iter_child_nodes(node):
            inner = function
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                inner = child.name
            if isinstance(child, ast.Call):
                func = child.func
                name = (
                    func.id
                    if isinstance(func, ast.Name)
                    else func.attr
                    if isinstance(func, ast.Attribute)
                    else ""
                )
                if name in BUILDERS and (relative, function, name) not in ALLOWED:
                    found.append(f"{relative}:{child.lineno} {name}")
            visit(child, inner)

    visit(ast.parse(source), "")
    return found


def _settings(out: Path, **changes: object) -> Settings:
    return Settings(output_folder=out, force_cpu=True, **changes)


def _run(request: ExportRequest) -> JobResult:
    return composition.export_jobs().job(request)(StubProgress())


def test_each_call_returns_fresh_real_components() -> None:
    assert isinstance(composition.photo_reader(), PhotoReader)
    assert isinstance(composition.photo_writer(), PhotoWriter)
    assert composition.photo_reader() is not composition.photo_reader()
    assert composition.photo_writer() is not composition.photo_writer()
    first, second = composition.correction_methods(), composition.correction_methods()
    assert list(first) == ["c3", "ancuti2018"]
    assert all(isinstance(m, AncutiFusionMethod) for m in first.values())
    assert all(first[key] is not second[key] for key in first)
    assert composition.export_jobs() is not composition.export_jobs()


def test_the_selection_is_core_select_backend_itself() -> None:
    assert composition.backend_selector() is core.select_backend


def test_the_package_exports_the_root() -> None:
    import clearwater.app as app

    assert app.__all__ == [
        "backend_selector",
        "correction_methods",
        "export_jobs",
        "photo_reader",
        "photo_writer",
    ]
    assert all(getattr(app, name) is getattr(composition, name) for name in app.__all__)


def test_a_photo_is_exported_through_the_real_engine(sample, tmp_path: Path) -> None:
    out = tmp_path / "out"
    out.mkdir()
    source = sample("jpeg-gradient-srgb")
    result = _run(ExportRequest(source, "photo", new_parameter_set("c3", {}), _settings(out)))
    assert result.ok, result.failure
    assert result.device == "CPU: forced"
    assert [p.name for p in result.outputs] == ["jpeg-gradient-srgb_corrected.png"]
    image, _ = PhotoReader().read(result.outputs[0])
    assert image.pixels.shape == (64, 96, 3)


def test_a_video_request_fails_unavailable_and_writes_nothing(tmp_path: Path) -> None:
    out = tmp_path / "out"
    out.mkdir()
    source = tmp_path / "GX010001.MP4"
    source.write_bytes(b"not read")
    result = _run(ExportRequest(source, "video", new_parameter_set("c3", {}), _settings(out)))
    assert (result.ok, result.failure, result.outputs) == (False, UNAVAILABLE_TEXT, ())
    assert list(out.iterdir()) == [] and sorted(p.name for p in tmp_path.iterdir()) == [
        "GX010001.MP4",
        "out",
    ]


def test_a_malformed_request_is_refused_by_the_engine(tmp_path: Path) -> None:
    request = ExportRequest(tmp_path / "a.jpg", "audio", new_parameter_set("c3", {}), Settings())
    with pytest.raises(ValueError, match="unknown export kind"):
        composition.export_jobs().job(request)


def test_the_overrides_replace_their_default(sample, tmp_path: Path) -> None:
    seen: list[str] = []
    stages: list[str] = []

    def select(settings: Settings, height: int, width: int, method_id: str):
        seen.append(method_id)
        return core.backend_for("cpu"), "CPU: test"

    class Writer(PhotoWriter):
        calls = 0

        def write(self, *args, **kwargs):
            Writer.calls += 1
            super().write(*args, **kwargs)

    out = tmp_path / "out"
    out.mkdir()
    methods = {"ancuti2018": composition.correction_methods()["ancuti2018"]}
    jobs = composition.export_jobs(
        app_version="9.9.9",
        writer=Writer(),
        methods=methods,
        select_backend=select,
        on_stage=stages.append,
    )
    request = ExportRequest(
        sample("png8-uniform-srgb"), "photo", new_parameter_set("ancuti2018", {}), _settings(out)
    )
    result = jobs.job(request)(StubProgress())
    assert result.ok, result.failure
    assert result.device == "CPU: test" and seen == ["ancuti2018"] and Writer.calls == 1
    assert stages == ["read", "measure", "render", "write", "committed"]
    refused = jobs.job(
        ExportRequest(request.source, "photo", new_parameter_set("c3", {}), _settings(out))
    )(StubProgress())
    assert not refused.ok and "unknown correction method 'c3'" in (refused.failure or "")


def test_importing_the_root_builds_nothing_and_loads_no_qt_or_cupy() -> None:
    code = (
        "import sys\n"
        "import clearwater.io.photo.reader as r, clearwater.jobs.export as e\n"
        "built = []\n"
        "orig_r, orig_e = r.PhotoReader.__init__, e.ExportEngine.__init__\n"
        "r.PhotoReader.__init__ = lambda self, *a, **k: built.append('reader')\n"
        "e.ExportEngine.__init__ = lambda self, *a, **k: built.append('engine')\n"
        "import clearwater.app, clearwater.app.composition\n"
        "bad = sorted(m for m in sys.modules\n"
        "             if m.split('.')[0] in ('PySide6', 'shiboken6', 'cupy', 'cupyx'))\n"
        "gui = sorted(m for m in sys.modules if m.startswith('clearwater.gui'))\n"
        "print(','.join(bad + gui + built))\n"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True, timeout=120
    )
    assert out.stdout.strip() == ""


def test_only_the_root_constructs_the_real_photo_engines() -> None:
    found: list[str] = []
    for path in sorted(SRC.rglob("*.py")):
        relative = path.relative_to(SRC).as_posix()
        found += builders_outside_the_root(relative, path.read_text(encoding="utf-8"))
    assert found == []


def test_the_static_check_reports_a_planted_construction() -> None:
    planted = (
        "from clearwater.jobs import ExportEngine\n"
        "from clearwater import methods\n"
        "def wire():\n"
        "    return ExportEngine(), methods.available_methods()\n"
        "def read_photo():\n"
        "    return PhotoReader()\n"
    )
    assert builders_outside_the_root("gui/engines.py", planted) == [
        "gui/engines.py:4 ExportEngine",
        "gui/engines.py:4 available_methods",
        "gui/engines.py:6 PhotoReader",
    ]
    # The convenience exception holds only for its own name in its own module.
    assert builders_outside_the_root("io/photo/reader.py", planted) == [
        "io/photo/reader.py:4 ExportEngine",
        "io/photo/reader.py:4 available_methods",
    ]
    assert builders_outside_the_root("app/composition.py", planted) == []
