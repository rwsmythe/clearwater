"""Video decode (WP3.9) on the graphics card and on a real HERO13 clip.

- ``gpu``: ``hw_decode=True`` gives the same bytes and pts as software decode on every decodable
  sample (WP2.1S: every transport form decodes the same frames to the same bytes).
- ``footage``: GX011627 (681 frames, pts 0 to 680 x 1001 at 1/30000; read only) decodes to
  every frame's pts and a per-frame hash equal to an independent FFmpeg run, through the large
  pipe, through the forced default pipe (AD-23) and, with ``gpu``, through CUDA decode.
"""

from __future__ import annotations

import hashlib
import subprocess
from collections.abc import Callable, Iterator
from fractions import Fraction
from pathlib import Path

import pytest

from clearwater.color import decode_filter, rgb_frame_bytes, rgb_to_planes
from clearwater.interfaces.image import Frame
from clearwater.interfaces.video import ProbeResult
from clearwater.io.video import FFmpegVideoSource, pipes, probe
from clearwater.io.video import decode as decode_module

pytestmark = pytest.mark.usefixtures("ffmpeg_tools")

SOURCE = FFmpegVideoSource()
DECODABLE = [
    "vid-hevc8-bt709-full",
    "vid-hevc10",
    "vid-untagged",
    "vid-truncated",
    "vid-vfr",
    "vid-rotated",
]
FOOTAGE_FRAMES = 681


def needs_cuda() -> None:
    """Skip the calling test when FFmpeg cannot create a CUDA device."""
    if not decode_module.cuda_decode_available():
        pytest.skip("CUDA decode is not available")


def hashes(frames: Iterator[Frame]) -> list[tuple[int, str]]:
    """Each frame's pts and the SHA-256 of its integer planes."""
    return [
        (
            frame.pts_ticks,
            hashlib.sha256(
                rgb_to_planes(frame.pixels, bit_depth=frame.color.bit_depth)
            ).hexdigest(),
        )
        for frame in frames
    ]


@pytest.mark.gpu
@pytest.mark.parametrize("sample_id", DECODABLE)
def test_cuda_decode_gives_the_software_bytes_and_pts(
    sample_id: str, sample: Callable[[str], Path]
) -> None:
    needs_cuda()
    result = probe(sample(sample_id))
    stream = SOURCE.frames(result, hw_decode=True)
    assert isinstance(stream, decode_module.FrameStream)
    assert "-hwaccel" in stream._command
    assert hashes(stream) == hashes(SOURCE.frames(result, hw_decode=False))


# --- the real clip ------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def footage() -> ProbeResult:
    """GX011627's probe result (read only); skips when the clip is absent."""
    from local_config import FootageLookupError, find_footage_file, load_local_config

    config = load_local_config()
    try:
        path = find_footage_file("GX011627", config.footage_path)
    except FootageLookupError as error:
        if error.matches:
            raise
        pytest.skip("GX011627 is not in the footage folder")
    return probe(path)


@pytest.fixture(scope="module")
def footage_reference(footage: ProbeResult) -> list[str]:
    """Per-frame SHA-256 of an independent FFmpeg run of the same filter, streamed."""
    video = footage.video
    size = rgb_frame_bytes(video.width, video.height, video.bit_depth)
    command = [
        "ffmpeg", "-nostdin", "-v", "error", "-noautorotate", "-i", str(footage.path),
        "-map", "0:v:0", "-vf", decode_filter(video), "-fps_mode", "passthrough",
        "-f", "rawvideo", "pipe:1",
    ]  # fmt: skip
    digests: list[str] = []
    with subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.DEVNULL) as process:
        assert process.stdout is not None
        while chunk := process.stdout.read(size):
            assert len(chunk) == size
            digests.append(hashlib.sha256(chunk).hexdigest())
    assert process.returncode == 0
    return digests


def check_footage(frames: Iterator[Frame], reference: list[str]) -> None:
    """Compare a footage decode with the reference, frame by frame."""
    got = hashes(frames)
    assert [pts for pts, _ in got] == [k * 1001 for k in range(FOOTAGE_FRAMES)]
    assert [digest for _, digest in got] == reference


@pytest.mark.footage
@pytest.mark.slow
def test_the_real_clip_decodes_to_its_pts_and_the_reference_bytes(
    footage: ProbeResult, footage_reference: list[str]
) -> None:
    assert footage.video.time_base == Fraction(1, 30000)
    assert len(footage_reference) == FOOTAGE_FRAMES
    check_footage(SOURCE.frames(footage, hw_decode=False), footage_reference)


@pytest.mark.footage
@pytest.mark.slow
def test_the_real_clip_through_the_forced_default_pipe_is_identical(
    footage: ProbeResult, footage_reference: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(size: int) -> tuple[int, int]:
        raise OSError("forced failure")

    monkeypatch.setattr(pipes, "_create_pipe", fail)
    check_footage(SOURCE.frames(footage, hw_decode=False), footage_reference)


@pytest.mark.footage
@pytest.mark.gpu
@pytest.mark.slow
def test_the_real_clip_through_cuda_decode_is_identical(
    footage: ProbeResult, footage_reference: list[str]
) -> None:
    needs_cuda()
    check_footage(SOURCE.frames(footage, hw_decode=True), footage_reference)
