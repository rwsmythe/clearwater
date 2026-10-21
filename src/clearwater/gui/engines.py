"""The engines the shell runs on: stubs for tests, and what is merged for a manual run.

Until WP4.3 wires the real engines, :func:`default_engines` uses the merged
``clearwater.io.video.probe`` and ``clearwater.core.select_backend`` and the
``clearwater.interfaces.stubs`` for everything else (photo reading WP3.6, decode WP3.9, encode
WP3.10, cache WP3.12, the correction method WP3.4).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from fractions import Fraction
from pathlib import Path

from clearwater import core
from clearwater.interfaces import (
    ArrayBackend,
    ColorDescription,
    CorrectionMethod,
    Fault,
    Frame,
    Image,
    PhotoMetadata,
    ProbeResult,
    Settings,
    VideoStreamInfo,
)
from clearwater.interfaces.stubs import (
    StubCorrectionMethod,
    StubPhotoSource,
    StubProxyCache,
    StubVideoSink,
    StubVideoSource,
)
from clearwater.interfaces.stubs import select_backend as stub_select_backend
from clearwater.io.video import probe as video_probe_file

from .contract import Engines, SelectBackend

STUB_ERA_METHOD_ID = "c3"
"""The method id whose memory estimate stands in for a method ``clearwater.core`` does not know.

The default method (D16). Used only by :func:`stub_era_select_backend` (round-0 ruling S1).
"""

VIDEO_TIME_BASE = Fraction(1, 90000)
"""The time base of :func:`stub_probe` results: 90 kHz, the MP4 video convention."""


def stub_probe(
    path: Path,
    *,
    width: int = 64,
    height: int = 48,
    faults: Sequence[Fault] = (),
    color: ColorDescription | None = None,
) -> ProbeResult:
    """Build a plausible probe result for tests and for the stub video source.

    Args:
        path: The probed path.
        width: Coded width in pixels.
        height: Coded height in pixels.
        faults: The faults to report.
        color: The stream colour tags; BT.709 limited, tagged, when None.

    Returns:
        An 8-bit HEVC MP4 at 30 frames per second, 10 s, no audio.
    """
    tags = color or ColorDescription("bt709", "bt709", "bt709", "limited", 8, False, None)
    video = VideoStreamInfo(
        codec="hevc",
        width=width,
        height=height,
        bit_depth=8,
        pix_fmt="yuv420p",
        chroma_siting="left",
        color=tags,
        frame_rate=Fraction(30),
        time_base=VIDEO_TIME_BASE,
        nb_frames=300,
        rotation=0,
        vfr=False,
    )
    return ProbeResult(
        path=path,
        container="mov,mp4,m4a,3gp,3g2,mj2",
        duration_s=Fraction(10),
        start_offset_s=Fraction(0),
        video=video,
        audio=(),
        data=(),
        edit_list=(),
        faults=tuple(faults),
        gopro=None,
    )


def stub_era_select_backend(
    settings: Settings, height: int, width: int, method_id: str
) -> tuple[ArrayBackend, str]:
    """``clearwater.core.select_backend`` for the stub era (round-0 ruling S1; WP4.3 removes it).

    The real selection raises ``ValueError`` for a method id it has no memory estimate for, and
    the only method merged before WP3.4 is the stub (id ``"stub"``). An id outside
    ``clearwater.core.METHOD_IDS`` is therefore estimated as :data:`STUB_ERA_METHOD_ID`; a known
    id passes through unchanged. ``clearwater.core`` itself is not changed.

    Args:
        settings: The application settings (``force_cpu``).
        height: Frame height in pixels.
        width: Frame width in pixels.
        method_id: The correction method id.

    Returns:
        The backend and the AD-9 reason, as ``clearwater.core.select_backend`` returns them.
    """
    known = method_id if method_id in core.METHOD_IDS else STUB_ERA_METHOD_ID
    return core.select_backend(settings, height, width, known)


def stub_engines(
    *,
    photos: Mapping[Path, tuple[Image, PhotoMetadata]] | None = None,
    frames: Sequence[Frame] = (),
    video_probe: Callable[[Path], ProbeResult] | None = None,
    methods: Mapping[str, CorrectionMethod] | None = None,
    select_backend: SelectBackend | None = None,
) -> Engines:
    """Build engines from the interface stubs (tests).

    Args:
        photos: Path -> photo for the stub photo source; none when None.
        frames: The frames the stub video source serves (for every probed file).
        video_probe: The probe; one that returns :func:`stub_probe` of the path when None.
        methods: The methods, default first; ``{"stub": StubCorrectionMethod()}`` when None.
        select_backend: The selection; the stub's (``"CPU: stub"``/``"CPU: forced"``) when None.

    Returns:
        The engines.
    """
    probe = video_probe or stub_probe
    return Engines(
        photo_source=StubPhotoSource(photos or {}),
        video_probe=probe,
        video_source=StubVideoSource(frames, stub_probe(Path("stub.mp4"))),
        video_sink=StubVideoSink(),
        cache=StubProxyCache(),
        methods=dict(methods) if methods is not None else {"stub": StubCorrectionMethod()},
        select_backend=select_backend or stub_select_backend,
    )


def default_engines() -> Engines:
    """Build the engines for a manual run before WP4.3: merged probe and selection, stubs else.

    A photo cannot be read yet (the stub photo source holds none) and a probed video yields no
    frame (the stub video source holds none), so both are refused with a G10 message.

    Returns:
        The engines.
    """
    return Engines(
        photo_source=StubPhotoSource({}),
        video_probe=video_probe_file,
        video_source=StubVideoSource((), stub_probe(Path("stub.mp4"))),
        video_sink=StubVideoSink(),
        cache=StubProxyCache(),
        methods={"stub": StubCorrectionMethod()},
        select_backend=stub_era_select_backend,
    )
