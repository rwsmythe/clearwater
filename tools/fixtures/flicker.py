"""The AD-14 synthetic flicker clip and its measured-region mask (WP2.3 item 2; V3, D112).

The clip is one procedural still repeated for 90 frames at 30000/1001 fps with a bright disc of
10 % of the frame area sweeping left to right. The metric of V3 is measured in the upper half of
the frame, which the disc never enters, so whatever changes there from frame to frame is the
correction's flicker and not the disturbance. The still is fully procedural (ruling 1): seeded
noise tuned to the whole-frame statistics WP1.3 measured on the owner's shallow clip
(``docs/reports/wp1.3-look-check.md`` section 5, ``flicker/statistics.json`` per-frame
``compensation.channel_means`` and ``normalisation``): channel means R 0.426, G 0.572, B 0.546
(the 180 frames' means) and a sharpening-normalisation spread N{} of 0.27 to 0.52 (mean 0.38,
report section 5 "The flicker as numbers"). No owner pixel is used.

The disc is a 10 % disc, which is 257 pixels across at 960 x 540: it cannot fit inside the lower
third (180 rows). Its centre row is therefore 405, the middle of the lower half, and it spans rows
277 to 532. The lower third holds its centre; the upper half, the measured region, is never
touched. The clip is lossless (FFV1 RGB in Matroska), so the decoded frames are exactly
the frames rendered here and their hash is the manifest's identity check.
"""

from __future__ import annotations

import functools
import hashlib
import math
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray
from PIL import Image

if not __package__:
    # Script mode: sys.path[0] is tools/fixtures; put tools first for the sibling packages.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fixtures import manifest, video
from spike_io.guard import WriteGuard

WIDTH = 960
"""Frame width (ruling 2)."""

HEIGHT = 540
"""Frame height (ruling 2)."""

FRAMES = 90
"""The frame count (AD-14)."""

FRAME_RATE = "30000/1001"
"""The frame rate (AD-14: 29.97 fps)."""

DISC_FRACTION = 0.10
"""The disc's area as a fraction of the frame (AD-14)."""

DISC_CENTRE_ROW = 405
"""The disc centre's row: the middle of the lower half, inside the lower third."""

DISC_COLOUR = (250, 246, 232)
"""The disc's colour (a bright warm white)."""

REGION_ROWS = HEIGHT // 2
"""The measured region is the rows ``0 .. REGION_ROWS - 1`` (the upper half)."""

SEED = 7
"""The texture seed."""

TARGET_MEANS = (0.426, 0.574, 0.548)
"""The channel means the texture is built around (WP1.3's 180 flicker frames: 0.426, 0.572, 0.546;
the green and blue offsets of 0.002 make up for the clipped highlights)."""

CHANNEL_GAINS = (0.8, 1.0, 1.1)
"""How strongly each channel follows the structure (red follows least, as under water)."""

DEPTH_SLOPE = (0.03, 0.04, 0.05)
"""Top-to-bottom brightness change per channel (the surface is brighter)."""

PATCH_AMPLITUDE = 0.43
"""Half-height of the sharp-edged patches; tuned so that the N{} spread is about 0.38."""

PATCH_STEEPNESS = 20.0
"""How hard the patch edges are (``tanh`` slope)."""

SOFT_AMPLITUDE = 0.08
"""Amplitude of the soft, large-scale shading."""

DETAIL_AMPLITUDE = 0.03
"""Amplitude of the fine detail layer."""

GRAIN = 0.03
"""Standard deviation of the per-pixel noise (fraction of full scale)."""

PATCH_SCALES = ((10, 16, 1.0), (22, 36, 0.8), (48, 80, 0.7), (96, 160, 0.7))
"""Noise-grid cells (rows, columns) and weight of each patch layer."""

MASK_PATH = "flicker/ad14-mask.png"
"""Where the mask lives, relative to the committed root."""

CLIP_PATH = "flicker/ad14-flicker.mkv"
"""Where the clip lives, relative to the generated root."""

CLIP_ID = "ad14-flicker"
"""The manifest id of the clip."""


def smooth_noise(
    rng: np.random.Generator, height: int, width: int, cells_y: int, cells_x: int
) -> NDArray[np.float64]:
    """Return smooth value noise on a ``cells_y x cells_x`` lattice (bilinear, smoothstep).

    Args:
        rng: The seeded generator.
        height: Output rows.
        width: Output columns.
        cells_y: Lattice cells down the image.
        cells_x: Lattice cells across the image.

    Returns:
        A ``(height, width)`` float64 field (standard-normal lattice values, interpolated).
    """
    grid = rng.standard_normal((cells_y + 2, cells_x + 2))
    ys = np.linspace(0, cells_y, height, endpoint=False)
    xs = np.linspace(0, cells_x, width, endpoint=False)
    y0, x0 = np.floor(ys).astype(int), np.floor(xs).astype(int)
    ty, tx = ys - y0, xs - x0
    ty, tx = ty * ty * (3 - 2 * ty), tx * tx * (3 - 2 * tx)
    top = grid[np.ix_(y0, x0)] * (1 - tx)[None, :] + grid[np.ix_(y0, x0 + 1)] * tx[None, :]
    bottom = (
        grid[np.ix_(y0 + 1, x0)] * (1 - tx)[None, :] + grid[np.ix_(y0 + 1, x0 + 1)] * tx[None, :]
    )
    field: NDArray[np.float64] = top * (1 - ty)[:, None] + bottom * ty[:, None]
    return field


def _unit(field: NDArray[np.float64]) -> NDArray[np.float64]:
    """Return a field with zero mean and unit standard deviation."""
    centred = field - field.mean()
    return centred / centred.std()


def texture(width: int = WIDTH, height: int = HEIGHT) -> NDArray[np.uint8]:
    """Return the procedural reef-like still, ``uint8`` RGB.

    Soft shading, sharp-edged patches at four scales (rock, coral and sand edges), a fine detail
    layer and per-pixel grain, around a top-bright depth gradient; every channel follows the same
    structure with its own gain.

    Args:
        width: Width in pixels.
        height: Height in pixels.

    Returns:
        A ``(height, width, 3)`` array.
    """
    rng = np.random.default_rng(SEED)
    shading = np.zeros((height, width))
    for k in range(4):
        shading += 0.6**k * smooth_noise(rng, height, width, 3 * 2**k, 5 * 2**k)
    soft = _unit(shading)
    patches = np.zeros((height, width))
    for cells_y, cells_x, weight in PATCH_SCALES:
        patches += weight * np.tanh(
            PATCH_STEEPNESS * _unit(smooth_noise(rng, height, width, cells_y, cells_x))
        )
    patches -= patches.mean()
    patches /= np.abs(patches).max()
    detail = _unit(smooth_noise(rng, height, width, 135, 240))
    depth = np.linspace(0.5, -0.5, height)[:, None]
    out = np.empty((height, width, 3))
    for c in range(3):
        structure = SOFT_AMPLITUDE * soft + PATCH_AMPLITUDE * patches + DETAIL_AMPLITUDE * detail
        out[..., c] = (
            TARGET_MEANS[c]
            + DEPTH_SLOPE[c] * depth
            + CHANNEL_GAINS[c] * structure
            + GRAIN * rng.standard_normal((height, width))
        )
    return np.round(np.clip(out, 0.0, 1.0) * 255).astype(np.uint8)


@functools.cache
def still() -> NDArray[np.uint8]:
    """Return the clip's still (:func:`texture` at 960 x 540), computed once and read-only."""
    image = texture()
    image.setflags(write=False)
    return image


def disc_radius(width: int = WIDTH, height: int = HEIGHT) -> float:
    """Return the radius of a disc covering ``DISC_FRACTION`` of the frame area."""
    return math.sqrt(DISC_FRACTION * width * height / math.pi)


def disc_centre_x(
    index: int, frames: int = FRAMES, width: int = WIDTH, height: int = HEIGHT
) -> float:
    """Return the disc centre's column in frame ``index``: a left-to-right sweep, fully inside."""
    radius = disc_radius(width, height)
    return radius + (width - 2 * radius) * index / (frames - 1)


def disc_mask(index: int, width: int = WIDTH, height: int = HEIGHT) -> NDArray[np.bool_]:
    """Return the disc's pixels in frame ``index`` (pixel centres at ``+ 0.5``).

    Args:
        index: The frame number, 0 to ``FRAMES - 1``.
        width: Frame width.
        height: Frame height.

    Returns:
        A boolean ``(height, width)`` array, True where the disc is.
    """
    radius = disc_radius(width, height)
    cx = disc_centre_x(index, FRAMES, width, height)
    ys = np.arange(height)[:, None] + 0.5
    xs = np.arange(width)[None, :] + 0.5
    inside: NDArray[np.bool_] = (xs - cx) ** 2 + (ys - DISC_CENTRE_ROW) ** 2 <= radius**2
    return inside


def region_mask(width: int = WIDTH, height: int = HEIGHT) -> NDArray[np.bool_]:
    """Return the measured region (the upper half) as a boolean mask."""
    mask = np.zeros((height, width), dtype=np.bool_)
    mask[: height // 2] = True
    return mask


def frames(base: NDArray[np.uint8] | None = None) -> Iterator[NDArray[np.uint8]]:
    """Yield the 90 frames: the still with the disc drawn at its position.

    Args:
        base: The still; :func:`still` when None.

    Yields:
        Each frame, ``(HEIGHT, WIDTH, 3)`` ``uint8``.
    """
    source = base if base is not None else still()
    for index in range(FRAMES):
        frame = source.copy()
        frame[disc_mask(index, source.shape[1], source.shape[0])] = DISC_COLOUR
        yield frame


def frames_sha256() -> str:
    """Return the SHA-256 of all 90 frames' ``rgb24`` bytes, in order (no FFmpeg involved)."""
    digest = hashlib.sha256()
    for frame in frames():
        digest.update(frame.tobytes())
    return digest.hexdigest()


def decode_sha256(path: Path) -> tuple[int, str]:
    """Decode a clip to ``rgb24`` with FFmpeg and hash it as :func:`frames_sha256` does.

    Args:
        path: The clip.

    Returns:
        The decoded frame count and the SHA-256 of all decoded bytes.

    Raises:
        video.GenerationError: FFmpeg fails or the byte count is not a whole number of frames.
    """
    command = [
        "ffmpeg", "-nostdin", "-hide_banner", "-v", "error", "-i", str(path),
        "-map", "0:v:0", "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ]  # fmt: skip
    digest = hashlib.sha256()
    total = 0
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
        stdout = process.stdout
        if stdout is None:
            raise video.GenerationError("no stdout pipe")
        for block in iter(lambda: stdout.read(1 << 20), b""):
            digest.update(block)
            total += len(block)
        stderr = process.stderr.read() if process.stderr else b""
    if process.returncode != 0 or total % (WIDTH * HEIGHT * 3):
        raise video.GenerationError(f"decoding {path.name} failed: {stderr.decode()[-300:]}")
    return total // (WIDTH * HEIGHT * 3), digest.hexdigest()


def write_clip(guard: WriteGuard, path: Path) -> None:
    """Encode the flicker clip losslessly (FFV1 RGB, Matroska) from rendered frames.

    Args:
        guard: The write guard; ``path`` must resolve inside its root.
        path: The output file.

    Raises:
        video.GenerationError: FFmpeg is missing or fails.
    """
    if not video.tools_available():
        raise video.GenerationError("ffmpeg must be on the PATH to build the flicker clip")
    guard.check(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WIDTH}x{HEIGHT}",
        "-framerate", FRAME_RATE, "-i", "pipe:0",
        "-an", "-c:v", "ffv1", "-level", "3", "-g", "1", "-slices", "4", "-slicecrc", "1",
        "-pix_fmt", "gbrp", *video.BITEXACT, "-map_metadata", "-1", str(path),
    ]  # fmt: skip
    with subprocess.Popen(
        command, stdin=subprocess.PIPE, stderr=subprocess.PIPE, cwd=path.parent
    ) as process:
        stdin = process.stdin
        if stdin is None:
            raise video.GenerationError("no stdin pipe")
        try:
            for frame in frames():
                stdin.write(frame.tobytes())
        finally:
            stdin.close()
        stderr = process.stderr.read() if process.stderr else b""
    if process.returncode != 0:
        raise video.GenerationError(f"ffmpeg failed for {path.name}: {stderr.decode()[-400:]}")


def measure_clip(path: Path) -> dict[str, Any]:
    """Measure a written clip with ffprobe and a decode.

    Args:
        path: The clip.

    Returns:
        ffprobe's stream fields, the decoded frame count and hash, and the packet pts list's hash
        (Matroska times are in milliseconds, so the 30000/1001 rate is the stream's declared one).
    """
    data, errors = video.ffprobe_json(path, "-show_streams", "-show_format")
    stream = next(s for s in data["streams"] if s["codec_type"] == "video")
    packets, _ = video.ffprobe_json(path, "-select_streams", "v:0", "-show_entries", "packet=pts")
    ticks = [int(p["pts"]) for p in packets["packets"]]
    count, digest = decode_sha256(path)
    return {
        "container": data["format"]["format_name"],
        "codec": stream["codec_name"],
        "pix_fmt": stream["pix_fmt"],
        "width": stream["width"],
        "height": stream["height"],
        "r_frame_rate": stream["r_frame_rate"],
        "avg_frame_rate": stream["avg_frame_rate"],
        "time_base": stream["time_base"],
        "decoded_frames": count,
        "decoded_rgb24_sha256": digest,
        "packet_pts_count": len(ticks),
        "packet_pts_sha256": hashlib.sha256(",".join(map(str, ticks)).encode("ascii")).hexdigest(),
        "ffprobe_errors": errors,
    }


def normalisation_spread(image: NDArray[np.uint8]) -> float:
    """Return the N{} spread of a still: WP1.3's whole-frame statistic, measured by the prototype.

    The still is compensated (Ancuti 2018, red only) and white-balanced at the ``Params()``
    defaults, and the spread is the high bound minus the low bound of the sharpening
    normalisation (``prototype.pipeline.normalisation_bounds``), the quantity WP1.3 reports as
    "N{} low..high" (report section 5).

    Args:
        image: A ``(height, width, 3)`` ``uint8`` RGB still.

    Returns:
        The spread, in fractions of full scale.
    """
    from prototype import pipeline
    from prototype.params import Params

    params = Params()
    unit = (image / np.float32(255)).astype(np.float32)
    compensated, _ = pipeline.compensate_ancuti2018(unit, params)
    balanced, _ = pipeline.white_balance(compensated, params)
    low, high = pipeline.normalisation_bounds(balanced, params)
    return float(high - low)


WP1_3_REFERENCE = {
    "source": "docs/reports/wp1.3-look-check.md section 5 (flicker clip, 180 frames of GX011627)",
    "channel_means": [0.426, 0.572, 0.546],
    "normalisation_spread_range": [0.27, 0.52],
    "normalisation_spread_mean": 0.38,
}
"""The WP1.3 statistics the texture is tuned to (quoted from the report, not measured here)."""


def design_facts() -> dict[str, Any]:
    """Return the facts of the design, measured from the rendered pixels.

    Returns:
        The still's channel means, the disc's radius, area fraction, row span and clearance from
        the measured region over all 90 frames, and whether the region is identical in every
        frame.
    """
    base = still()
    region = region_mask()
    pixels, top, bottom, entered, differs = [], [], [], 0, 0
    for index, frame in enumerate(frames(base)):
        mask = disc_mask(index)
        rows = np.flatnonzero(mask.any(axis=1))
        pixels.append(int(mask.sum()))
        top.append(int(rows[0]))
        bottom.append(int(rows[-1]))
        entered += int((mask & region).sum())
        differs += int((frame[region] != base[region]).sum())
    means = (base.reshape(-1, 3).mean(axis=0) / 255).round(4).tolist()
    return {
        "frames": FRAMES,
        "frame_rate": FRAME_RATE,
        "width": WIDTH,
        "height": HEIGHT,
        "texture_channel_means": means,
        "texture_normalisation_spread": round(normalisation_spread(base), 3),
        "wp1_3_reference": WP1_3_REFERENCE,
        "disc_radius_px": round(disc_radius(), 3),
        "disc_pixels_min": min(pixels),
        "disc_pixels_max": max(pixels),
        "disc_area_fraction_min": round(min(pixels) / (WIDTH * HEIGHT), 5),
        "disc_area_fraction_max": round(max(pixels) / (WIDTH * HEIGHT), 5),
        "disc_centre_row": DISC_CENTRE_ROW,
        "disc_first_row": min(top),
        "disc_last_row": max(bottom),
        "region_rows": [0, REGION_ROWS - 1],
        "disc_pixels_in_region": entered,
        "region_pixels_changed_between_frames": differs,
        "lower_third_first_row": 2 * HEIGHT // 3,
        "frames_rgb24_sha256": frames_sha256(),
    }


def write_mask(guard: WriteGuard, path: Path) -> None:
    """Write the measured-region mask: 255 in the upper half, 0 elsewhere (8-bit grey PNG).

    Args:
        guard: The write guard.
        path: The output file.
    """
    guard.check(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(region_mask().astype(np.uint8) * 255).save(path, "PNG")


def build_mask(guard: WriteGuard, out: Path) -> manifest.Entry:
    """Write the mask under ``out`` and return its manifest entry.

    Args:
        guard: The write guard whose root is ``out``.
        out: The committed-fixtures output folder.

    Returns:
        The entry.
    """
    file = out / MASK_PATH
    write_mask(guard, file)
    with Image.open(file) as image:
        values = np.asarray(image)
        facts = {
            "width": image.width,
            "height": image.height,
            "mode": image.mode,
            "region_rows": [0, REGION_ROWS - 1],
            "region_pixels": int((values == 255).sum()),
            "outside_pixels": int((values == 0).sum()),
        }
    return manifest.entry(
        sample_id="ad14-mask",
        group="flicker",
        kind="mask",
        storage="committed",
        path=MASK_PATH,
        serves=["V3", "D112", "AD-14"],
        exercises="The measured region of the flicker clip: 255 in the upper half, 0 elsewhere; "
        "the disc never enters it.",
        expected=manifest.expect(),
        facts=facts,
        file=file,
        byte_reproducible=True,
    )


def build_clip(guard: WriteGuard, out: Path) -> manifest.Entry:
    """Write the clip under ``out``, verify it, and return its manifest entry.

    Args:
        guard: The write guard whose root is ``out``.
        out: The generated-fixtures output folder.

    Returns:
        The entry.

    Raises:
        video.GenerationError: The decoded frames do not hash to the rendered frames, or the
            stream is not 90 frames of FFV1 at 30000/1001.
    """
    file = out / CLIP_PATH
    write_clip(guard, file)
    design = design_facts()
    measured = measure_clip(file)
    wrong = []
    if measured["decoded_rgb24_sha256"] != design["frames_rgb24_sha256"]:
        wrong.append("the decoded frames are not the rendered frames")
    for name, want in (("codec", "ffv1"), ("decoded_frames", FRAMES), ("r_frame_rate", FRAME_RATE)):
        if measured[name] != want:
            wrong.append(f"{name} is {measured[name]!r}, intended {want!r}")
    if design["disc_pixels_in_region"] or design["region_pixels_changed_between_frames"]:
        wrong.append("the disc enters the measured region")
    if wrong:
        raise video.GenerationError("; ".join(wrong))
    return manifest.entry(
        sample_id=CLIP_ID,
        group="flicker",
        kind="mkv",
        storage="generated",
        path=CLIP_PATH,
        serves=["V3", "D112", "D64", "AD-14"],
        exercises="The V3 clip: 90 frames at 30000/1001 of one still with a 10 % bright disc "
        "sweeping the lower half; measure frame-to-frame flicker only inside ad14-mask.",
        expected=manifest.expect(
            probe={
                "container": "matroska,webm",
                "video": {
                    "codec": "ffv1",
                    "width": WIDTH,
                    "height": HEIGHT,
                    "frame_rate": FRAME_RATE,
                    "vfr": False,
                },
            }
        ),
        facts={"design": design, "stream": measured},
        file=file,
        byte_reproducible=False,
        command="uv run python tools/fixtures/generate.py --group flicker "
        "--out work/fixtures/scratch --generated-out work/fixtures/generated",
    )
