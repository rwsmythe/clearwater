"""WP4.1 composition root (``clearwater.app.composition``): fresh real components, the routing.

Covers task 3: every function returns a fresh real component; ``"c3"`` is first (D16); the
selection is ``clearwater.core.select_backend`` itself; ``export_jobs`` exports a photo through
the real reader, method and writer and runs a video as the real video job (WP4.2); importing
the root loads no PySide6 or CuPy and builds nothing (WP4.3, DR-84: also no video source, sink
or proxy cache, with a planted control); and no other module under ``src/clearwater`` constructs
the real photo engines (a static test with a planted control). WP4.3 adds the application's one
cache, opened later (``proxy_cache_opener``; ruling S1 (a)), and ``export_jobs(cache=...)``
(ruling Q16).
"""

from __future__ import annotations

import ast
import subprocess
import sys
import threading
from pathlib import Path

import pytest

import clearwater
from clearwater import core
from clearwater.app import composition
from clearwater.cache import DiskProxyCache
from clearwater.config import new_parameter_set
from clearwater.interfaces import JobResult, ProxyCache, Settings
from clearwater.interfaces.stubs import StubProgress
from clearwater.io.photo import PhotoReader, PhotoWriter
from clearwater.jobs.export_seam import ExportRequest
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
        "proxy_cache",
        "video_sink",
        "video_source",
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


def test_a_video_request_runs_the_real_video_job(tmp_path: Path) -> None:
    out = tmp_path / "out"
    out.mkdir()
    source = tmp_path / "GX010001.MP4"
    source.write_bytes(b"not read")
    request = ExportRequest(source, "video", new_parameter_set("c3", {}), _settings(out))
    result = composition.export_jobs(cache_folder=tmp_path / "cache").job(request)(StubProgress())
    assert (result.ok, result.outputs) == (False, ())
    assert result.failure == (
        "GX010001.MP4: GX010001.MP4 cannot be read as a video file; it may be damaged or not a "
        "video."
    )
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


def _import_witness(planted: str = "") -> str:
    """Import the root with every real constructor instrumented; return what was built or loaded.

    Instrumented: the photo reader, writer, methods and export engine (WP4.1), and the video
    source, sink and proxy cache (DR-84). ``planted`` runs after the instruments, before the
    import, as a module of the package doing work at import time would.
    """
    code = (
        "import sys\n"
        "import clearwater.io.photo.reader as r, clearwater.jobs.export as e\n"
        "import clearwater.io.photo.writer as w, clearwater.methods as m\n"
        "import clearwater.io.video as v, clearwater.cache as c\n"
        "built = []\n"
        "r.PhotoReader.__init__ = lambda self, *a, **k: built.append('reader')\n"
        "e.ExportEngine.__init__ = lambda self, *a, **k: built.append('engine')\n"
        "w.PhotoWriter.__init__ = lambda self, *a, **k: built.append('writer')\n"
        "m.available_methods = lambda *a, **k: built.append('methods') or {}\n"
        "v.FFmpegVideoSource.__init__ = lambda self, *a, **k: built.append('video_source')\n"
        "v.FFmpegVideoSink.__init__ = lambda self, *a, **k: built.append('video_sink')\n"
        "c.DiskProxyCache.__init__ = lambda self, *a, **k: built.append('proxy_cache')\n"
        f"{planted}"
        "import clearwater.app, clearwater.app.composition\n"
        "bad = sorted(m for m in sys.modules\n"
        "             if m.split('.')[0] in ('PySide6', 'shiboken6', 'cupy', 'cupyx'))\n"
        "gui = sorted(m for m in sys.modules if m.startswith('clearwater.gui'))\n"
        "print(','.join(bad + gui + built))\n"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True, timeout=120
    )
    return out.stdout.strip()


def test_importing_the_root_builds_nothing_and_loads_no_qt_or_cupy() -> None:
    assert _import_witness() == ""


@pytest.mark.parametrize(
    ("planted", "seen"),
    [
        ("v.FFmpegVideoSource()\n", "video_source"),
        ("v.FFmpegVideoSink()\n", "video_sink"),
        ("c.DiskProxyCache(None)\n", "proxy_cache"),
    ],
    ids=["source", "sink", "cache"],
)
def test_the_witness_sees_a_planted_import_time_construction(planted: str, seen: str) -> None:
    """DR-84: each video constructor is instrumented, so a construction at import is reported."""
    assert _import_witness(planted) == seen


# WP4.3: the application's one cache (ruling S1 (a), its conditions 1-4) and Q16.


def _in_thread(call, *args):
    """Start ``call(*args)`` on a thread; return the thread and a box for its result or error."""
    box: dict[str, object] = {}

    def body() -> None:
        try:
            box["value"] = call(*args)
        except Exception as exc:
            box["error"] = exc

    thread = threading.Thread(target=body, daemon=True)
    thread.start()
    return thread, box


def test_the_handle_is_an_if7_cache_that_waits_for_its_open(tmp_path: Path) -> None:
    handle = composition.proxy_cache_opener(tmp_path / "cache")
    assert isinstance(handle, ProxyCache)
    assert handle.opened() is None and handle.failure() is None and not handle.wait_open(0)
    thread, box = _in_thread(handle.limit_bytes)
    thread.join(0.3)
    assert thread.is_alive(), "a member did not wait for the open"
    assert handle.open(7 * 10**9) is None
    thread.join(5)
    assert box == {"value": 7 * 10**9}
    assert isinstance(handle.opened(), DiskProxyCache)
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"x")
    assert handle.key_for(source) == handle.opened().key_for(source)
    assert handle.lookup(handle.key_for(source)) is None
    with pytest.raises(RuntimeError, match="opened once"):
        handle.open(1)


def test_a_limit_or_clear_asked_during_the_open_is_applied_after_it(tmp_path: Path) -> None:
    """Condition 3: the settings dialog's calls made before the open completes are queued."""
    handle = composition.proxy_cache_opener(tmp_path / "cache")
    limit, limit_box = _in_thread(handle.set_limit_bytes, 5 * 10**9)
    clear, clear_box = _in_thread(handle.clear)
    limit.join(0.2)
    clear.join(0.2)
    assert limit.is_alive() and clear.is_alive()
    assert handle.open(20 * 10**9) is None
    limit.join(5)
    clear.join(5)
    assert limit_box == {"value": None} and clear_box == {"value": None}
    assert handle.limit_bytes() == 5 * 10**9  # the dialog's limit, not the open's


def test_a_failed_open_refuses_every_member_readably(tmp_path: Path) -> None:
    """Condition 2: a failed open never hangs or re-raises a traceback; members refuse."""
    handle = composition.proxy_cache_opener(tmp_path / "cache")
    reason = handle.open(-1)
    assert reason == "the cache limit is not negative" and handle.failure() == reason
    expected = f"the analysis cache could not be opened: {reason}"
    for call in (
        lambda: handle.key_for(tmp_path),
        lambda: handle.lookup(None),
        lambda: handle.proxy(None, 0),
        lambda: handle.set_limit_bytes(1),
        handle.clear,
    ):
        with pytest.raises(RuntimeError) as caught:
            call()
        assert str(caught.value) == expected
    assert handle.limit_bytes() == 0  # the refusing cache's form


def test_fail_ends_the_wait_when_no_open_runs(tmp_path: Path) -> None:
    handle = composition.proxy_cache_opener(tmp_path / "cache")
    thread, box = _in_thread(handle.clear)
    handle.fail("the window closed before the cache was opened")
    thread.join(5)
    assert not thread.is_alive()
    assert "the window closed before the cache was opened" in str(box["error"])


def test_export_jobs_shares_the_given_cache_and_opens_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Q16: one instance; ``cache_folder`` and ``cache`` together are refused."""
    disk = DiskProxyCache(tmp_path / "cache")
    handle = composition.proxy_cache_opener(tmp_path / "cache2")
    opened: list[Path] = []
    monkeypatch.setattr(composition, "proxy_cache", lambda folder, *a: opened.append(folder))
    for cache in (disk, handle):
        engine = composition.export_jobs(cache=cache)
        assert engine._cache is cache
        assert engine._cache_key == cache.key_for  # keyed by the cache's own key_for (DR-41)
    assert opened == []
    with pytest.raises(ValueError, match="not both"):
        composition.export_jobs(cache=disk, cache_folder=tmp_path / "cache")


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
