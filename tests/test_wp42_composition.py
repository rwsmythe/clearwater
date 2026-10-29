"""WP4.2 task 4: the composition root's video legs (``clearwater.app.composition``).

``export_jobs()`` returns the ``ExportEngine`` itself, over the real IF-5 source and sink
(:func:`~clearwater.app.composition.video_source`, :func:`~clearwater.app.composition.video_sink`,
built per video job on the job's backend, DR-67) and the real IF-7 cache over the caller's folder
with its registered default codec, keyed by that cache's own ``key_for`` (DR-41). Without a cache
folder a video request fails readably and writes nothing (round-0 ruling R0-Q1). The root
resolves no app-data folder (WP4.1 question 6), its new parameters are keyword-only and
defaulted, and no module under ``src/clearwater`` but the root constructs the real video source,
sink or cache (a static test with a planted control).
"""

from __future__ import annotations

import ast
import inspect
import os
from pathlib import Path

import pytest

import clearwater
from clearwater import app, core
from clearwater.app import composition
from clearwater.cache import DEFAULT_CODEC, DiskProxyCache, cache_key, codec_cache_version
from clearwater.config import new_parameter_set
from clearwater.interfaces import DEFAULT_CACHE_LIMIT_BYTES, Settings
from clearwater.interfaces.stubs import (
    StubProgress,
    StubProxyCache,
    StubVideoSink,
    StubVideoSource,
)
from clearwater.io.video import FFmpegVideoSink, FFmpegVideoSource
from clearwater.jobs import ExportEngine
from clearwater.jobs.export_seam import UNAVAILABLE_TEXT, ExportRequest

SRC = Path(clearwater.__file__).parent
VIDEO_BUILDERS = frozenset({"FFmpegVideoSource", "FFmpegVideoSink", "DiskProxyCache"})
DEFINING = {
    "io/video/decode.py": "FFmpegVideoSource",
    "io/video/encode.py": "FFmpegVideoSink",
    "cache/store.py": "DiskProxyCache",
}
"""Each class's own module, where its name may appear (its definition and its own uses)."""


def video_builders_outside_the_root(relative: str, source: str) -> list[str]:
    """Return ``"<file>:<line> <name>"`` for every use of a real video class outside the root.

    A use is a call or a reference by value (a class passed as a factory counts); imports and
    ``__all__`` strings are not uses; a name a class is imported under (``import ... as``) is the
    class. The root and each class's own module are not reported.
    """
    if relative == "app/composition.py":
        return []
    tree = ast.parse(source)
    aliases = {
        alias.asname: alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
        if alias.name in VIDEO_BUILDERS and alias.asname is not None
    }
    found: list[str] = []
    for node in ast.walk(tree):
        written = (
            node.id
            if isinstance(node, ast.Name)
            else node.attr
            if isinstance(node, ast.Attribute)
            else ""
        )
        name = aliases.get(written, written)
        if name in VIDEO_BUILDERS and DEFINING.get(relative) != name:
            found.append(f"{relative}:{node.lineno} {name}")  # type: ignore[union-attr]
    return sorted(found)


def _request(source: Path, out: Path) -> ExportRequest:
    settings = Settings(output_folder=out, force_cpu=True)
    return ExportRequest(source, "video", new_parameter_set("c3", {}), settings)


def test_export_jobs_returns_the_engine_over_the_real_video_collaborators(tmp_path: Path) -> None:
    engine = composition.export_jobs(cache_folder=tmp_path / "cache", cache_limit_bytes=12345)
    assert type(engine) is ExportEngine
    assert type(engine._video_source) is FFmpegVideoSource
    assert engine._video_source.device_backend is None  # it only probes
    assert engine._source_for is composition.video_source
    assert engine._sink_for is composition.video_sink
    assert engine._select_backend is core.select_backend
    cache = engine._cache
    assert type(cache) is DiskProxyCache
    assert cache._folder == tmp_path / "cache" and cache.limit_bytes() == 12345
    stubs = (StubVideoSource, StubVideoSink, StubProxyCache)
    for collaborator in (engine._video_source, engine._cache, engine._sink_factory()):
        assert not isinstance(collaborator, stubs)


def test_the_cache_has_the_registered_default_codec_and_keys_with_it(tmp_path: Path) -> None:
    """DR-41 consumer note: the default codec, and the key of the same codec's version."""
    engine = composition.export_jobs(cache_folder=tmp_path / "cache")
    cache = engine._cache
    assert cache._codec is DEFAULT_CODEC
    assert engine._cache_key == cache.key_for
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"bytes")
    key = engine._cache_key(source)
    assert key == cache_key(source) and key.cache_version == codec_cache_version(DEFAULT_CODEC)


@pytest.mark.parametrize("device", [None, "gpu"])
def test_the_video_builders_pass_the_device_backend_through(device: str | None) -> None:
    backend = None if device is None else core.backend_for("cpu")
    source = composition.video_source(backend)
    sink = composition.video_sink()
    assert type(source) is FFmpegVideoSource and source.device_backend is backend
    assert type(sink) is FFmpegVideoSink
    assert composition.video_source() is not composition.video_source()
    assert composition.video_sink() is not composition.video_sink()


def test_the_new_parameters_are_keyword_only_with_defaults() -> None:
    parameters = inspect.signature(composition.export_jobs).parameters
    for name in ("cache_folder", "cache_limit_bytes", "source_for", "sink_for"):
        assert parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
        assert parameters[name].default is not inspect.Parameter.empty
    assert parameters["cache_folder"].default is None
    assert parameters["cache_limit_bytes"].default == DEFAULT_CACHE_LIMIT_BYTES
    assert [p.kind for p in parameters.values()] == [inspect.Parameter.KEYWORD_ONLY] * len(
        parameters
    )
    for name in ("video_source", "video_sink", "proxy_cache"):
        assert getattr(app, name) is getattr(composition, name)


def test_without_a_cache_folder_a_video_fails_readably_and_writes_nothing(
    sample, tmp_path: Path
) -> None:
    out = tmp_path / "out"
    out.mkdir()
    source = sample("vid-hevc8-bt709-full")
    result = composition.export_jobs().job(_request(source, out))(StubProgress())
    assert not result.ok and result.outputs == ()
    assert result.failure is not None and result.failure != UNAVAILABLE_TEXT
    assert result.failure.startswith(source.name) and composition.VIDEO_NEEDS_A_CACHE in (
        result.failure
    )
    assert list(out.iterdir()) == []


def test_the_root_resolves_no_app_data_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import clearwater.config.paths as paths

    def refuse(*args: object, **kwargs: object) -> None:
        raise AssertionError("the root resolved the app-data folder")

    monkeypatch.setattr(paths, "app_locations", refuse)
    composition.export_jobs(cache_folder=tmp_path / "cache")
    composition.export_jobs()
    names = {
        node.id
        for node in ast.walk(ast.parse(Path(composition.__file__).read_text(encoding="utf-8")))
        if isinstance(node, ast.Name)
    }
    assert "app_locations" not in names
    assert not (tmp_path / "cache").exists()  # opened, not created (created on the first store)


def test_only_the_root_constructs_the_real_video_source_sink_and_cache() -> None:
    found: list[str] = []
    for path in sorted(SRC.rglob("*.py")):
        relative = path.relative_to(SRC).as_posix()
        found += video_builders_outside_the_root(relative, path.read_text(encoding="utf-8"))
    assert found == []


def test_the_video_static_check_reports_a_planted_construction() -> None:
    planted = (
        "from clearwater.io.video import FFmpegVideoSink, FFmpegVideoSource\n"
        "from clearwater import cache\n"
        "def wire():\n"
        "    return FFmpegVideoSource(), cache.DiskProxyCache(folder)\n"
        "ENGINE = dict(sink_factory=FFmpegVideoSink)\n"
    )
    assert video_builders_outside_the_root("gui/engines.py", planted) == [
        "gui/engines.py:4 DiskProxyCache",
        "gui/engines.py:4 FFmpegVideoSource",
        "gui/engines.py:5 FFmpegVideoSink",
    ]
    # A class's own module may name only that class.
    assert video_builders_outside_the_root("cache/store.py", planted) == [
        "cache/store.py:4 FFmpegVideoSource",
        "cache/store.py:5 FFmpegVideoSink",
    ]
    assert video_builders_outside_the_root("app/composition.py", planted) == []


def test_the_video_static_check_reports_an_aliased_construction() -> None:
    """Reviewer A R1 F4: a class imported under another name is still the class."""
    planted = (
        "from clearwater.io.video import FFmpegVideoSource as Source\n"
        "from clearwater.cache import DiskProxyCache as Cache\n"
        "def wire():\n"
        "    return Source(), Cache(folder)\n"
    )
    assert video_builders_outside_the_root("gui/engines.py", planted) == [
        "gui/engines.py:4 DiskProxyCache",
        "gui/engines.py:4 FFmpegVideoSource",
    ]


def test_each_export_jobs_call_opens_its_own_cache(tmp_path: Path) -> None:
    first = composition.export_jobs(cache_folder=tmp_path / "cache")
    second = composition.export_jobs(cache_folder=tmp_path / "cache")
    assert first._cache is not second._cache
    assert os.fspath(first._cache._folder) == os.fspath(second._cache._folder)
