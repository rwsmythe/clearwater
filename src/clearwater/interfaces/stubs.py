"""In-memory stubs, one per interface protocol, for building before dependencies exist.

Every stub is deterministic and does no I/O and no GPU work. Behaviour is trivial: a stub
records, copies or returns what it was given. Anything that needs an algorithm raises
:class:`NotImplementedError` naming the interface and the work package that implements it.
The ``if TYPE_CHECKING`` block at the end assigns each stub to a variable of its protocol type,
so mypy (which checks ``src/clearwater``) proves the signatures match.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from fractions import Fraction
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
from numpy.typing import ArrayLike, DTypeLike, NDArray

from .backend import ArrayBackend
from .cache import CacheEntry, CacheKey, ProxyCache
from .image import Array, Frame, Image
from .jobs import Progress
from .method import CorrectionMethod, Parameter, Stage, Statistics
from .photo import PhotoMetadata, PhotoSink, PhotoSource
from .settings import DEFAULT_CACHE_LIMIT_BYTES, Settings
from .statistics import StatisticsStore
from .video import EncoderCapability, ProbeResult, SinkReport, VideoSink, VideoSource

C3_STAGES: tuple[Stage, ...] = (
    Stage(
        name="white_balance",
        statistics=("means", "gains"),
        smoothed=("means", "gains"),
        depends_on_parameters=(
            "kappa",
            "lambda_",
            "c3_strength",
            "c3_kernel_fraction",
            "c3_mask_threshold",
            "c3_mask_smooth_fraction",
        ),
        depends_on_stages=(),
        source_only=False,
    ),
    Stage(
        name="fusion",
        statistics=("bounds", "saliency_means"),
        smoothed=("bounds", "saliency_means"),
        depends_on_parameters=(
            "white_balance_strength",
            "max_white_balance_gain",
            "sharpen_blur_fraction",
            "normalisation_low",
            "normalisation_high",
            "gamma",
            "sharpen_strength",
        ),
        depends_on_stages=("white_balance",),
        source_only=False,
    ),
)
"""The c3 method's stage list (PROPOSED, WP2.2 round 1), after AD-6 and WP1.4 section 7.

Stage 1, ``white_balance``: the channel means and gray-world gains of the proxy compensated by
3C (3C has no whole-frame compensation statistic). Stage 2, ``fusion``: the N{} bounds and the
saliency Lab means of the two fusion inputs. Every statistic is smoothable (AD-6); strength and
the D99 clamp apply after smoothing, in closed form, so they invalidate the fusion stage only
through the white-balanced image. Neither stage is source-only (c3 has no whole-frame
statistic that depends on the source file alone, WP1.4 section 7).
"""

C3_STAGE_NAMES: tuple[str, ...] = tuple(stage.name for stage in C3_STAGES)
"""The c3 stage names in order."""

_C3_SHAPES: dict[str, tuple[int, ...]] = {
    "means": (3,),
    "gains": (3,),
    "bounds": (2,),
    "saliency_means": (2, 3),
}


class StubCorrectionMethod:
    """A method with id ``"stub"`` and the real c3 stage list; ``render`` is the identity (IF-3).

    ``analyze`` returns zeros of the declared statistic names (shapes: ``means`` and ``gains``
    ``(3,)``, ``bounds`` ``(2,)``, ``saliency_means`` ``(2, 3)``) so Phase 3 analysis code is
    exercised against the true shape. ``render`` returns its input unchanged but refuses a
    missing stage, as IF-3 says.

    Attributes:
        id: ``"stub"``.
        label: ``"Stub"``.
        parameters: Empty; the parameters are WP3.2's.
        stages: :data:`C3_STAGES` (AD-6, WP1.4 section 7).
    """

    id: str = "stub"
    label: str = "Stub"

    def __init__(self) -> None:
        """Create the stub."""
        self.parameters: tuple[Parameter, ...] = ()
        self.stages: tuple[Stage, ...] = C3_STAGES

    def analyze(
        self,
        stage: str,
        image: Image,
        params: Mapping[str, Any],
        earlier: Mapping[str, Statistics],
    ) -> Statistics:
        """Return zeros for every statistic of ``stage``.

        Args:
            stage: The stage name.
            image: Ignored.
            params: Ignored.
            earlier: Ignored.

        Returns:
            Zero float64 arrays keyed by the stage's statistic names.

        Raises:
            ValueError: ``stage`` is not one of the stub's stages.
        """
        for known in self.stages:
            if known.name == stage:
                return {name: np.zeros(_C3_SHAPES[name]) for name in known.statistics}
        raise ValueError(f"unknown stage {stage!r}")

    def render(
        self,
        image: Image,
        params: Mapping[str, Any],
        statistics: Mapping[str, Statistics],
    ) -> Image:
        """Return ``image`` unchanged.

        Args:
            image: The image.
            params: Ignored.
            statistics: Must hold every stage of the method.

        Returns:
            ``image`` itself.

        Raises:
            KeyError: A stage is missing from ``statistics``.
        """
        for stage in self.stages:
            if stage.name not in statistics:
                raise KeyError(f"missing statistics for stage {stage.name!r}")
        return image

    def closed_form(
        self,
        stage: str,
        params: Mapping[str, Any],
        earlier: Mapping[str, Statistics],
        measured: Statistics,
    ) -> Statistics | None:
        """Return None: the stub has no closed form for any stage."""
        return None


class StubArrayBackend:
    """A NumPy-identity backend; image operations raise NotImplementedError (IF-2, WP3.1).

    Attributes:
        name: ``"numpy"``.
        device: ``"cpu"``.
    """

    name: str = "numpy"
    device: str = "cpu"

    def asarray(self, a: ArrayLike, dtype: DTypeLike = np.float32) -> Array:
        """Convert to a float32 NumPy array.

        Args:
            a: The input.
            dtype: Must be float32.

        Returns:
            ``a`` as float32.

        Raises:
            ValueError: ``dtype`` is not float32.
        """
        if np.dtype(dtype) != np.float32:
            raise ValueError(f"the backend array type is float32, not {np.dtype(dtype)}")
        return np.asarray(a, dtype=np.float32)

    def to_host(self, a: Array) -> NDArray[Any]:
        """Return ``a`` as float32 on the host (the identity on CPU)."""
        return np.asarray(a, dtype=np.float32)

    def gaussian_blur(self, a: Array, sigma_px: float) -> Array:
        """Not implemented (IF-2; WP3.1)."""
        raise NotImplementedError("IF-2 gaussian_blur is implemented by WP3.1")

    def pyramid_reduce(self, a: Array) -> Array:
        """Not implemented (IF-2; WP3.1)."""
        raise NotImplementedError("IF-2 pyramid_reduce is implemented by WP3.1")

    def pyramid_expand(self, a: Array, shape: tuple[int, int]) -> Array:
        """Not implemented (IF-2; WP3.1)."""
        raise NotImplementedError("IF-2 pyramid_expand is implemented by WP3.1")

    def rgb_to_ycbcr(self, a: Array, matrix: str, range_: str) -> Array:
        """Not implemented (IF-2; WP3.1)."""
        raise NotImplementedError("IF-2 rgb_to_ycbcr is implemented by WP3.1")

    def ycbcr_to_rgb(self, a: Array, matrix: str, range_: str) -> Array:
        """Not implemented (IF-2; WP3.1)."""
        raise NotImplementedError("IF-2 ycbcr_to_rgb is implemented by WP3.1")

    def percentile(self, a: Array, q: Sequence[float]) -> Array:
        """Not implemented (IF-2; WP3.1)."""
        raise NotImplementedError("IF-2 percentile is implemented by WP3.1")

    def memory_estimate_bytes(self, height: int, width: int, method_id: str) -> int:
        """Not implemented (IF-2; WP3.1)."""
        raise NotImplementedError("IF-2 memory_estimate_bytes is implemented by WP3.1")

    def free_device_bytes(self) -> int | None:
        """Return None: there is no device memory on CPU."""
        return None


def select_backend(
    settings: Settings, height: int, width: int, method_id: str
) -> tuple[ArrayBackend, str]:
    """Return a :class:`StubArrayBackend` and a reason (stub of IF-2 ``select_backend``).

    Args:
        settings: The application settings (``force_cpu``).
        height: Ignored.
        width: Ignored.
        method_id: Ignored.

    Returns:
        A stub backend, with ``"CPU: forced"`` when ``settings.force_cpu`` else ``"CPU: stub"``.
    """
    return StubArrayBackend(), "CPU: forced" if settings.force_cpu else "CPU: stub"


class StubStatisticsStore:
    """A dict-backed statistics store keyed by pts ticks; ``smooth`` copies raw to smoothed (IF-4).

    Attributes:
        schema_hash: The value given at construction.
    """

    def __init__(
        self,
        stage_order: Sequence[str] = C3_STAGE_NAMES,
        schema_hash: str = "",
    ) -> None:
        """Create an empty store.

        Args:
            stage_order: The method's stage names, in order, for ``invalidate_from``.
            schema_hash: The schema hash to report.
        """
        self._stage_order = tuple(stage_order)
        self.schema_hash = schema_hash
        self._raw: dict[tuple[int, str], dict[str, NDArray[Any]]] = {}
        self._smoothed: dict[tuple[int, str], dict[str, NDArray[Any]]] = {}

    def put(self, pts_ticks: int, stage: str, raw: Statistics) -> None:
        """Store a copy of the raw statistics."""
        self._raw[pts_ticks, stage] = {name: np.array(value) for name, value in raw.items()}

    def raw(self, pts_ticks: int, stage: str) -> Statistics:
        """Return the raw statistics; raises KeyError if absent."""
        return self._raw[pts_ticks, stage]

    def smoothed(self, pts_ticks: int, stage: str) -> Statistics:
        """Return the smoothed statistics; raises KeyError until ``smooth`` has run."""
        return self._smoothed[pts_ticks, stage]

    def smooth(self, stage: str, names: Sequence[str], window_s: float, kind: str) -> None:
        """Copy the raw statistics of ``stage`` to smoothed, for every stored pts.

        Args:
            stage: The stage name.
            names: Statistic names; each must exist in the stage's raw statistics.
            window_s: Ignored.
            kind: Ignored.

        Raises:
            KeyError: A name is not in a stored raw record.
        """
        for (pts_ticks, stored_stage), raw in list(self._raw.items()):
            if stored_stage != stage:
                continue
            for name in names:
                if name not in raw:
                    raise KeyError(name)
            self._smoothed[pts_ticks, stage] = {n: np.array(v) for n, v in raw.items()}

    def invalidate_from(self, stage: str) -> None:
        """Drop ``stage`` and every later stage from both raw and smoothed.

        Args:
            stage: The first stage to drop.

        Raises:
            ValueError: ``stage`` is not in the stage order.
        """
        dropped = set(self._stage_order[self._stage_order.index(stage) :])
        for table in (self._raw, self._smoothed):
            for key in [key for key in table if key[1] in dropped]:
                del table[key]

    def pts_range(self) -> tuple[int, int]:
        """Return the first and last stored pts; raises ValueError when empty."""
        pts = self.all_pts()
        return pts[0], pts[-1]

    def all_pts(self) -> Sequence[int]:
        """Return the stored pts ticks in ascending order."""
        return sorted({pts_ticks for pts_ticks, _ in self._raw})


class StubVideoSource:
    """Serves the frames given at construction, with their exact pts (IF-5)."""

    def __init__(self, frames: Sequence[Frame], probe_result: ProbeResult) -> None:
        """Create the source.

        Args:
            frames: The frames to serve, in decode order.
            probe_result: What ``probe`` returns.
        """
        self._frames = tuple(frames)
        self._probe = probe_result

    def probe(self, path: Path) -> ProbeResult:
        """Return the probe result given at construction, whatever ``path`` is."""
        return self._probe

    def frames(
        self,
        probe: ProbeResult,
        *,
        hw_decode: bool,
        start_s: Fraction | None = None,
        end_s: Fraction | None = None,
    ) -> Iterator[Frame]:
        """Yield the frames with ``start_s <= pts < end_s``; ``hw_decode`` is ignored."""
        for frame in self._frames:
            if start_s is not None and frame.pts < start_s:
                continue
            if end_s is not None and frame.pts >= end_s:
                continue
            yield frame


class StubVideoSink:
    """Records what it receives (IF-5).

    Attributes:
        opened: The keyword arguments of ``open`` (plus ``probe`` and ``out_path``), or None.
        frames: The frames written, in order.
        aborted: True after ``abort``.
        closed: True after ``close``.
    """

    def __init__(self) -> None:
        """Create a sink that has not been opened."""
        self.opened: dict[str, Any] | None = None
        self.frames: list[Frame] = []
        self.aborted = False
        self.closed = False

    def capabilities(self) -> tuple[EncoderCapability, ...]:
        """Return one available software encoder named ``"stub"`` (8 and 10 bit)."""
        return (EncoderCapability("stub", True, None, (8, 10), False),)

    def open(
        self,
        probe: ProbeResult,
        out_path: Path,
        *,
        encoder: str,
        quality: str,
        bit_depth: int,
        provenance: Mapping[str, Any] | None,
    ) -> None:
        """Record the arguments."""
        self.opened = {
            "probe": probe,
            "out_path": out_path,
            "encoder": encoder,
            "quality": quality,
            "bit_depth": bit_depth,
            "provenance": provenance,
        }

    def write(self, frame: Frame) -> None:
        """Record a frame; raises RuntimeError before ``open``."""
        if self.opened is None:
            raise RuntimeError("write before open")
        self.frames.append(frame)

    def close(self) -> SinkReport:
        """Return a report of the frames recorded, with no warnings and nothing uncarried."""
        self.closed = True
        return SinkReport(frames_written=len(self.frames), warnings=(), not_carried=())

    def abort(self) -> None:
        """Mark the sink aborted (a real sink removes the partial output)."""
        self.aborted = True


class StubPhotoSource:
    """Serves the photos given at construction, by path (IF-6)."""

    def __init__(self, photos: Mapping[Path, tuple[Image, PhotoMetadata]]) -> None:
        """Create the source.

        Args:
            photos: Path -> (image, metadata).
        """
        self._photos = dict(photos)

    def read(self, path: Path) -> tuple[Image, PhotoMetadata]:
        """Return the photo for ``path``; raises FileNotFoundError when there is none."""
        try:
            return self._photos[path]
        except KeyError:
            raise FileNotFoundError(str(path)) from None


class StubPhotoSink:
    """Records the photos it is asked to write (IF-6).

    Attributes:
        written: One dict per ``write`` call, holding its arguments.
    """

    def __init__(self) -> None:
        """Create a sink with nothing written."""
        self.written: list[dict[str, Any]] = []

    def write(
        self,
        image: Image,
        meta: PhotoMetadata,
        out_path: Path,
        *,
        bit_depth: int,
        provenance: Mapping[str, Any] | None,
    ) -> None:
        """Record the arguments."""
        self.written.append(
            {
                "image": image,
                "meta": meta,
                "out_path": out_path,
                "bit_depth": bit_depth,
                "provenance": provenance,
            }
        )


class StubProxyCache:
    """A dict-backed proxy cache (IF-7); the size limit is stored, not enforced."""

    def __init__(self) -> None:
        """Create an empty cache with the default limit (D71)."""
        self._limit = DEFAULT_CACHE_LIMIT_BYTES
        self._proxies: dict[CacheKey, dict[int, NDArray[np.uint8]]] = {}
        self._stats: dict[CacheKey, dict[tuple[str, int], dict[str, NDArray[Any]]]] = {}

    def lookup(self, key: CacheKey) -> CacheEntry | None:
        """Return an entry describing what is stored for ``key``, or None."""
        proxies = self._proxies.get(key, {})
        stats = self._stats.get(key, {})
        if not proxies and not stats:
            return None
        size = sum(p.nbytes for p in proxies.values()) + sum(
            v.nbytes for s in stats.values() for v in s.values()
        )
        return CacheEntry(
            key=key,
            pts_ticks=tuple(sorted(proxies)),
            stages=tuple(sorted({stage for stage, _ in stats})),
            size_bytes=size,
        )

    def store_proxy(self, key: CacheKey, pts_ticks: int, proxy: NDArray[np.uint8]) -> None:
        """Store a copy of the proxy."""
        self._proxies.setdefault(key, {})[pts_ticks] = np.array(proxy)

    def proxy(self, key: CacheKey, pts_ticks: int) -> NDArray[np.uint8]:
        """Return the proxy; raises KeyError if absent."""
        return self._proxies[key][pts_ticks]

    def store_source_statistics(
        self, key: CacheKey, stage: str, pts_ticks: int, stats: Statistics
    ) -> None:
        """Store a copy of the statistics."""
        self._stats.setdefault(key, {})[stage, pts_ticks] = {
            name: np.array(value) for name, value in stats.items()
        }

    def limit_bytes(self) -> int:
        """Return the stored limit."""
        return self._limit

    def set_limit_bytes(self, n: int) -> None:
        """Store the limit (nothing is evicted)."""
        self._limit = n

    def clear(self) -> None:
        """Drop everything."""
        self._proxies.clear()
        self._stats.clear()


class StubProgress:
    """Records reports; cancellable by a flag (IF-8).

    Attributes:
        reports: The ``(done, total, message)`` of every ``report`` call.
    """

    def __init__(self) -> None:
        """Create a progress recorder that is not cancelled."""
        self.reports: list[tuple[int, int | None, str]] = []
        self._cancelled = False

    def report(self, done: int, total: int | None, message: str) -> None:
        """Record a report."""
        self.reports.append((done, total, message))

    def cancelled(self) -> bool:
        """Return True once :meth:`cancel` has been called."""
        return self._cancelled

    def cancel(self) -> None:
        """Set the cancel flag."""
        self._cancelled = True


if TYPE_CHECKING:
    # mypy checks src/clearwater but not tests/: these assignments prove, at type-check time,
    # that every stub matches the signatures of its protocol.
    _method: CorrectionMethod = StubCorrectionMethod()
    _backend: ArrayBackend = StubArrayBackend()
    _store: StatisticsStore = StubStatisticsStore()
    _cache: ProxyCache = StubProxyCache()
    _progress: Progress = StubProgress()
    _video_sink: VideoSink = StubVideoSink()
    _photo_sink: PhotoSink = StubPhotoSink()

    def _sources(probe: ProbeResult) -> tuple[VideoSource, PhotoSource]:
        return StubVideoSource((), probe), StubPhotoSource({})
