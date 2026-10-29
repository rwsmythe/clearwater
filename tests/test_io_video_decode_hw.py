"""Video decode (WP3.9) on the graphics card and on a real HERO13 clip.

- ``gpu``: ``hw_decode=True`` gives the same bytes and pts as software decode on every decodable
  sample (WP2.1S: every transport form decodes the same frames to the same bytes).
- ``footage``: the GX011627 trim (the whole clip, 681 frames, in the ``fullclip`` form) decodes to
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
def footage(gx011627: tuple[Path, int]) -> ProbeResult:
    """Return the selected read-only GX011627 source's probe result.

    Args:
        gx011627: The trim or full source and its independently asserted count.

    Returns:
        The selected source's probe result.
    """
    return probe(gx011627[0])


@pytest.fixture(scope="module")
def footage_frames(gx011627: tuple[Path, int]) -> int:
    """Return the selected GX011627 count independently of probe metadata.

    Args:
        gx011627: The trim or full source and its independently asserted count.

    Returns:
        The selected source's asserted frame count.
    """
    return gx011627[1]


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


def check_footage(frames: Iterator[Frame], reference: list[str], count: int) -> None:
    """Compare a footage decode with the reference, frame by frame.

    Args:
        frames: The product decoder's frames.
        reference: Independent per-frame digests of the selected source.
        count: The selected source's asserted frame count.
    """
    got = hashes(frames)
    assert [pts for pts, _ in got] == [k * 1001 for k in range(count)]
    assert [digest for _, digest in got] == reference


@pytest.mark.footage
@pytest.mark.slow
def test_the_real_clip_decodes_to_its_pts_and_the_reference_bytes(
    footage: ProbeResult, footage_reference: list[str], footage_frames: int
) -> None:
    assert footage.video.time_base == Fraction(1, 30000)
    assert len(footage_reference) == footage_frames
    check_footage(SOURCE.frames(footage, hw_decode=False), footage_reference, footage_frames)


@pytest.mark.footage
@pytest.mark.slow
def test_the_real_clip_through_the_forced_default_pipe_is_identical(
    footage: ProbeResult,
    footage_reference: list[str],
    footage_frames: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(size: int) -> tuple[int, int]:
        raise OSError("forced failure")

    monkeypatch.setattr(pipes, "_create_pipe", fail)
    check_footage(SOURCE.frames(footage, hw_decode=False), footage_reference, footage_frames)


@pytest.mark.footage
@pytest.mark.gpu
@pytest.mark.slow
def test_the_real_clip_through_cuda_decode_is_identical(
    footage: ProbeResult, footage_reference: list[str], footage_frames: int
) -> None:
    needs_cuda()
    check_footage(SOURCE.frames(footage, hw_decode=True), footage_reference, footage_frames)


@pytest.mark.footage
@pytest.mark.slow
def test_the_gx011627_trim_is_a_stream_copy_of_the_source(
    gx011627_trim: tuple[Path, int],
) -> None:
    """Recheck every guarded trim property through the fixture's shared checker.

    Args:
        gx011627_trim: The checked session trim and source-derived frame count.
    """
    from conftest import _gx011627_source, gx011627_trim_checks

    trim, count = gx011627_trim
    record = gx011627_trim_checks(_gx011627_source(), trim, count)
    for name in ("4a", "4b", "4c", "4d", "4e"):
        assert record["checks"][name] == "PASS", name
    assert all(item["equal"] for item in record["data_packet_checks"]), "data packets"
