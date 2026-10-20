"""WP2.2: each stub satisfies its protocol in name and in signature, and behaves trivially."""

from __future__ import annotations

import inspect
from collections.abc import Iterator
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from clearwater.interfaces import (
    ArrayBackend,
    CacheKey,
    ColorDescription,
    CorrectionMethod,
    Frame,
    Image,
    PhotoMetadata,
    PhotoSink,
    PhotoSource,
    ProbeResult,
    Progress,
    ProxyCache,
    Settings,
    StatisticsStore,
    VideoSink,
    VideoSource,
    VideoStreamInfo,
    stubs,
)
from clearwater.interfaces.stubs import (
    C3_STAGES,
    StubArrayBackend,
    StubCorrectionMethod,
    StubPhotoSink,
    StubPhotoSource,
    StubProgress,
    StubProxyCache,
    StubStatisticsStore,
    StubVideoSink,
    StubVideoSource,
)

COLOR = ColorDescription("bt709", "bt709", "bt709", "limited", 8, False, None)


def _image() -> Image:
    return Image(np.full((2, 3, 3), 0.5, np.float32), "cpu", COLOR, False)


def _frame(index: int, ticks: int) -> Frame:
    return Frame(
        np.zeros((2, 3, 3), np.float32),
        "cpu",
        COLOR,
        False,
        pts=Fraction(ticks, 30000),
        pts_ticks=ticks,
        time_base=Fraction(1, 30000),
        index=index,
    )


def _probe() -> ProbeResult:
    video = VideoStreamInfo(
        "hevc", 3, 2, 8, "yuv420p", "left", COLOR, Fraction(30), Fraction(1, 30000), 3, 0, False
    )
    return ProbeResult(Path("a.mp4"), "mov", Fraction(1), Fraction(0), video, (), (), (), (), None)


def _stubs() -> list[tuple[Any, type]]:
    return [
        (StubCorrectionMethod(), CorrectionMethod),
        (StubArrayBackend(), ArrayBackend),
        (StubStatisticsStore(), StatisticsStore),
        (StubVideoSource([], _probe()), VideoSource),
        (StubVideoSink(), VideoSink),
        (StubPhotoSource({}), PhotoSource),
        (StubPhotoSink(), PhotoSink),
        (StubProxyCache(), ProxyCache),
        (StubProgress(), Progress),
    ]


def protocol_members(protocol: type) -> list[str]:
    """The names a protocol requires (methods and data attributes)."""
    return sorted(protocol.__protocol_attrs__)


def missing_members(obj: object, protocol: type) -> list[str]:
    """The protocol members an object lacks."""
    return [name for name in protocol_members(protocol) if not hasattr(obj, name)]


def signature_differences(obj: object, protocol: type) -> list[str]:
    """Methods whose parameter names, order, kinds or defaults differ from the protocol's."""
    differences = []
    for name in protocol_members(protocol):
        wanted = vars(protocol).get(name)
        if not callable(wanted):
            continue  # a data attribute: nothing to compare
        if not callable(getattr(obj, name, None)):
            differences.append(name)
            continue
        have = inspect.signature(getattr(obj, name))
        want = inspect.signature(wanted)
        want_params = [p for p in want.parameters.values() if p.name != "self"]
        have_params = list(have.parameters.values())
        pairs_ok = len(want_params) == len(have_params) and all(
            (w.name, w.kind, w.annotation) == (h.name, h.kind, h.annotation)
            and (
                h.default is not inspect.Parameter.empty
                if w.default is Ellipsis
                else w.default == h.default
            )
            for w, h in zip(want_params, have_params, strict=True)
        )
        if not pairs_ok or want.return_annotation != have.return_annotation:
            differences.append(name)
    return differences


@pytest.mark.parametrize(("stub", "protocol"), _stubs(), ids=lambda v: type(v).__name__)
def test_stub_satisfies_its_protocol(stub: Any, protocol: type) -> None:
    assert isinstance(stub, protocol)
    assert missing_members(stub, protocol) == []
    assert signature_differences(stub, protocol) == []


def test_every_protocol_has_a_stub() -> None:
    covered = {protocol for _, protocol in _stubs()}
    assert covered == {
        CorrectionMethod,
        ArrayBackend,
        StatisticsStore,
        VideoSource,
        VideoSink,
        PhotoSource,
        PhotoSink,
        ProxyCache,
        Progress,
    }


def test_planted_stub_missing_a_method_fails_by_name() -> None:
    class Broken(StubArrayBackend):
        percentile = None  # type: ignore[assignment]

    class Missing:
        name = "numpy"
        device = "cpu"

    assert not isinstance(Missing(), ArrayBackend)
    assert "percentile" in missing_members(Missing(), ArrayBackend)

    class Renamed:
        def put(self, ticks: int, stage: str, raw: Any) -> None: ...

    assert "put" in signature_differences(Renamed(), StatisticsStore)

    class WrongDefault(StubVideoSource):
        def frames(  # type: ignore[override]
            self,
            probe: ProbeResult,
            *,
            hw_decode: bool,
            start_s: Fraction | None = Fraction(0),
            end_s: Fraction | None = None,
        ) -> Iterator[Frame]:
            yield from ()

    class WrongReturn(StubProxyCache):
        def limit_bytes(self) -> str:  # type: ignore[override]
            return "x"

    assert signature_differences(WrongDefault([], _probe()), VideoSource) == ["frames"]
    assert signature_differences(WrongReturn(), ProxyCache) == ["limit_bytes"]

    class RequiredDtype(StubArrayBackend):
        def asarray(self, a: Any, dtype: Any) -> Any:  # type: ignore[override]
            return a

    assert signature_differences(RequiredDtype(), ArrayBackend) == ["asarray"]
    assert Broken.percentile is None


def test_method_stub_has_real_c3_stages_and_zero_statistics() -> None:
    method = StubCorrectionMethod()
    assert method.id == "stub"
    assert [s.name for s in method.stages] == ["white_balance", "fusion"]
    assert method.stages == C3_STAGES
    for stage in method.stages:
        assert set(stage.smoothed) <= set(stage.statistics)
        assert all(dep in {"white_balance"} for dep in stage.depends_on_stages)
        stats = method.analyze(stage.name, _image(), {}, {})
        assert set(stats) == set(stage.statistics)
        assert all(not np.any(v) for v in stats.values())
    assert method.analyze("white_balance", _image(), {}, {})["gains"].shape == (3,)
    assert method.analyze("fusion", _image(), {}, {})["saliency_means"].shape == (2, 3)
    with pytest.raises(ValueError, match="compensation"):
        method.analyze("compensation", _image(), {}, {})
    assert method.closed_form("fusion", {}, {}, {}) is None


def test_method_stub_render_is_identity_and_refuses_a_missing_stage() -> None:
    method = StubCorrectionMethod()
    image = _image()
    everything = {s.name: method.analyze(s.name, image, {}, {}) for s in method.stages}
    assert method.render(image, {}, everything) is image
    del everything["fusion"]
    with pytest.raises(KeyError, match="fusion"):
        method.render(image, {}, everything)


def test_backend_stub_converts_and_refuses_algorithms() -> None:
    backend = StubArrayBackend()
    array = backend.asarray([[[1, 2, 3]]])
    assert array.dtype == np.float32
    assert backend.to_host(array).dtype == np.float32
    assert backend.free_device_bytes() is None
    with pytest.raises(ValueError, match="float32"):
        backend.asarray([1], np.float64)
    calls: dict[str, tuple[Any, ...]] = {
        "gaussian_blur": (array, 1.0),
        "pyramid_reduce": (array,),
        "pyramid_expand": (array, (2, 2)),
        "rgb_to_ycbcr": (array, "bt709", "full"),
        "ycbcr_to_rgb": (array, "bt709", "full"),
        "percentile": (array, [50.0]),
        "memory_estimate_bytes": (2, 2, "c3"),
    }
    for name, args in calls.items():
        with pytest.raises(NotImplementedError, match=rf"IF-2 {name}.*WP3\.1"):
            getattr(backend, name)(*args)


def test_stub_select_backend() -> None:
    forced = Settings(png_bit_depth=16, video_encoder="e", quality_level="q", force_cpu=True)
    backend, reason = stubs.select_backend(forced, 10, 10, "c3")
    assert isinstance(backend, ArrayBackend) and reason == "CPU: forced"
    assert (
        stubs.select_backend(
            forced.__class__(png_bit_depth=8, video_encoder="e", quality_level="q"), 1, 1, "c3"
        )[1]
        == "CPU: stub"
    )


def test_statistics_store_stub() -> None:
    store = StubStatisticsStore(schema_hash="h")
    assert store.schema_hash == "h"
    raw = {"means": np.array([1.0, 2.0, 3.0])}
    for ticks in (3000, 1000, 2000):
        store.put(ticks, "white_balance", raw)
        store.put(ticks, "fusion", {"bounds": np.array([0.0, 1.0])})
    raw["means"][0] = 99.0  # the store copied
    assert store.raw(1000, "white_balance")["means"][0] == 1.0
    assert list(store.all_pts()) == [1000, 2000, 3000]
    assert store.pts_range() == (1000, 3000)
    with pytest.raises(KeyError):
        store.raw(5, "white_balance")
    with pytest.raises(KeyError):
        store.smoothed(1000, "white_balance")
    store.smooth("white_balance", ["means"], 2.0, "median_gaussian")
    assert np.array_equal(store.smoothed(2000, "white_balance")["means"], [1.0, 2.0, 3.0])
    store.smooth("fusion", ["bounds"], 2.0, "median_gaussian")
    store.invalidate_from("fusion")
    with pytest.raises(KeyError):
        store.raw(1000, "fusion")
    with pytest.raises(KeyError):
        store.smoothed(1000, "fusion")
    assert store.raw(1000, "white_balance")  # earlier stage kept
    store.invalidate_from("white_balance")
    assert list(store.all_pts()) == []


def test_video_source_stub_serves_exact_pts() -> None:
    frames = [_frame(i, 1001 * i) for i in range(5)]
    source = StubVideoSource(frames, _probe())
    probe = source.probe(Path("anything.mp4"))
    assert list(source.frames(probe, hw_decode=False)) == frames
    window = list(
        source.frames(
            probe, hw_decode=True, start_s=Fraction(1001, 30000), end_s=Fraction(4004, 30000)
        )
    )
    assert [f.pts_ticks for f in window] == [1001, 2002, 3003]
    assert [f.pts for f in window] == [Fraction(t, 30000) for t in (1001, 2002, 3003)]


def test_video_sink_stub_records() -> None:
    sink = StubVideoSink()
    assert sink.capabilities()[0].available
    frame = _frame(0, 0)
    with pytest.raises(RuntimeError):
        sink.write(frame)
    sink.open(_probe(), Path("o.mp4"), encoder="stub", quality="q", bit_depth=10, provenance=None)
    sink.write(frame)
    assert sink.opened is not None and sink.opened["bit_depth"] == 10
    report = sink.close()
    assert report.frames_written == 1 and report.warnings == () and report.not_carried == ()
    sink.abort()
    assert sink.aborted


def test_photo_stubs() -> None:
    meta = PhotoMetadata("jpeg", None, 1)
    image = _image()
    source = StubPhotoSource({Path("a.jpg"): (image, meta)})
    assert source.read(Path("a.jpg")) == (image, meta)
    with pytest.raises(FileNotFoundError):
        source.read(Path("b.jpg"))
    sink = StubPhotoSink()
    sink.write(image, meta, Path("o.png"), bit_depth=16, provenance={"k": 1})
    assert sink.written[0]["bit_depth"] == 16 and sink.written[0]["out_path"] == Path("o.png")


def test_proxy_cache_stub() -> None:
    cache = StubProxyCache()
    key = CacheKey(10, 20, 1)
    assert cache.lookup(key) is None
    assert cache.limit_bytes() == 20 * 10**9
    proxy = np.arange(6, dtype=np.uint8).reshape(1, 2, 3)
    cache.store_proxy(key, 2000, proxy)
    cache.store_proxy(key, 1000, proxy)
    cache.store_source_statistics(key, "white_balance", 1000, {"means": np.zeros(3)})
    entry = cache.lookup(key)
    assert entry is not None
    assert entry.pts_ticks == (1000, 2000) and entry.stages == ("white_balance",)
    assert entry.size_bytes == 6 * 2 + 3 * 8
    assert np.array_equal(cache.proxy(key, 1000), proxy)
    with pytest.raises(KeyError):
        cache.proxy(key, 7)
    cache.set_limit_bytes(5)
    assert cache.limit_bytes() == 5
    cache.clear()
    assert cache.lookup(key) is None


def test_progress_stub_records_and_cancels() -> None:
    progress = StubProgress()
    progress.report(1, None, "a")
    progress.report(2, 10, "b")
    assert progress.reports == [(1, None, "a"), (2, 10, "b")]
    assert not progress.cancelled()
    progress.cancel()
    assert progress.cancelled()
