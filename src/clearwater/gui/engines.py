"""The engines the shell runs on: stubs for tests, and the real engines of the application.

:func:`default_engines` takes every engine from the composition root
(:mod:`clearwater.app.composition`): the photo reader and the correction methods (WP4.1), the
IF-2 selection, and, given the app-data locations, the video source, sink and the one proxy
cache (WP4.3); without locations the video legs stay the ``clearwater.interfaces.stubs`` ones.
This module is the one ``clearwater.gui`` module importing ``clearwater.app``.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from fractions import Fraction
from pathlib import Path

from clearwater.app import composition
from clearwater.config import Locations
from clearwater.interfaces import (
    ColorDescription,
    CorrectionMethod,
    Fault,
    Frame,
    Image,
    PhotoMetadata,
    ProbeResult,
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


def default_engines(*, locations: Locations | None = None) -> Engines:
    """Build the real engines from the composition root (WP4.3, rulings Q11 and Q17, S1 (a)).

    The photo reader, the methods (``"c3"`` first, D16) and the IF-2 selection
    (``composition.backend_selector()``) always come from the root. Given ``locations``, the
    video source and sink are the root's and the cache is the application's one cache over
    ``locations.cache_dir`` (``composition.proxy_cache_opener``), NOT yet open: the caller's
    start-up opens it once, with the limit of the one settings read, and every cache member
    waits for that. Without ``locations`` the video legs are the stubs: no cache is opened and
    nothing is written under app data, and a probed video yields no frame, so it is refused with
    a G10 message.

    Args:
        locations: The app-data folders, or None for the engines without real video legs.

    Returns:
        The engines.
    """
    if locations is None:
        return Engines(
            photo_source=composition.photo_reader(),
            video_probe=video_probe_file,
            video_source=StubVideoSource((), stub_probe(Path("stub.mp4"))),
            video_sink=StubVideoSink(),
            cache=StubProxyCache(),
            methods=composition.correction_methods(),
            select_backend=composition.backend_selector(),
        )
    return Engines(
        photo_source=composition.photo_reader(),
        video_probe=video_probe_file,
        video_source=composition.video_source(),
        video_sink=composition.video_sink(),
        cache=composition.proxy_cache_opener(locations.cache_dir),
        methods=composition.correction_methods(),
        select_backend=composition.backend_selector(),
    )
