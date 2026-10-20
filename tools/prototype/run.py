"""Run the reference pipeline prototype on one image and write the corrected PNG.

Usage::

    uv run python tools/prototype/run.py --in FILE --out DIR [--method c3|ancuti2018]
        [--blue] [--neutral] [--dump] [--set NAME=VALUE ...] [--device cpu|gpu|auto]

``--method`` defaults to the :class:`Params` default, ``c3`` (spec v0.5.3 D16); the
options are ``c3``, ``ancuti2018``, and ``ancuti2018`` with ``--blue`` (ancuti2018-blue).

The image is read with Pillow into float32 RGB in [0, 1]. Colour management is out of
scope: an embedded ICC profile is ignored (a note says so) and the values are used as
display-encoded RGB in the source's primaries; the EXIF orientation is applied, since
the PNG written carries no orientation tag; an alpha channel is dropped. Pillow reads
8 bits per channel for RGB, so a 16-bit-per-channel RGB source is reduced to 8-bit
precision on read (a warning says so); 16-bit grayscale keeps its precision.

The result is written as ``<out>/<stem>-<method>.png``, 16 bits per channel RGB, with
no ICC profile and no other colour metadata. ``--neutral`` starts from
:meth:`Params.neutral`; ``--blue`` turns on Ancuti 2018 blue compensation (3C ignores it);
each ``--set NAME=VALUE`` overrides one :class:`Params` field (``none`` disables a gain
cap; booleans take ``true`` or ``false``), applied after ``--method``, ``--blue`` and
``--neutral``. ``--dump`` also writes every intermediate as a 16-bit PNG,
``<out>/<stem>-<method>-<stage>.png``, and the two info records as JSON. The raw weight
maps are written divided by their own maximum, recorded in ``<stem>-<method>-weights.json``,
which also names the backend the pipeline ran on.

``--device`` chooses that backend (:func:`prototype.backend.select_backend`): ``cpu``, the
default, so that the same image gives the same PNG on every machine (the GPU result
agrees with it only within float32 tolerance, which can move a 16-bit value by one);
``gpu``, an error without a usable device; or ``auto``, the graphics card when CuPy and a
CUDA device are usable and the CPU otherwise, with a note saying why.

Exit status 0 on success; 2, with a one-line ``error: ...`` on standard error, on a bad
argument (including a value whose derived sigma overflows at the image's size, which names
the parameter), an unusable device, an unreadable image or an output that cannot be
written.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import struct
import sys
import typing
import zlib
from collections.abc import Sequence
from pathlib import Path
from typing import Any, NoReturn

import numpy as np
from numpy.typing import NDArray
from PIL import Image as PILImage
from PIL import ImageOps

if not __package__:
    # Script mode (``python tools/prototype/run.py``): sys.path[0] is tools/prototype, so
    # put the tools directory first to make the ``prototype`` package importable.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# These imports must follow the script-mode sys.path bootstrap above. No `noqa: E402` is
# needed: ruff exempts imports that follow a `sys.path` modification (and flags an unused
# suppression as RUF100).
from prototype.backend import DEVICES, Backend, select_backend
from prototype.params import METHODS, Params
from prototype.pipeline import Result, check_derived_values, correct

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_TRUE = frozenset({"true", "1", "yes", "on"})
_FALSE = frozenset({"false", "0", "no", "off"})


class _UsageError(Exception):
    """A bad command-line argument; reported as one line with exit status 2."""


class _Parser(argparse.ArgumentParser):
    """An argument parser that raises :class:`_UsageError` instead of exiting."""

    def error(self, message: str) -> NoReturn:
        """Raise the parse error instead of printing usage and exiting.

        Args:
            message: The parser's error message.

        Raises:
            _UsageError: Always.
        """
        raise _UsageError(message)


def read_image(path: Path) -> tuple[NDArray[np.float32], list[str]]:
    """Read an image with Pillow into display-encoded float32 RGB in [0, 1].

    No colour management: an embedded ICC profile is ignored. The EXIF orientation is
    applied. 16-bit grayscale (Pillow modes ``I;16*`` and ``I``) is scaled by 1/65535 and
    repeated over three channels; every other mode is converted to 8-bit RGB by Pillow
    (dropping alpha) and scaled by 1/255.

    Args:
        path: The image file.

    Returns:
        The image, shape ``(H, W, 3)``, and one-line notes for the user (ignored
        profile, 16-bit RGB read at 8-bit precision).

    Raises:
        OSError: The file cannot be opened or decoded (includes Pillow's
            ``UnidentifiedImageError``).
        ValueError: Pillow cannot convert the image mode.
        PIL.Image.DecompressionBombError: The image exceeds Pillow's pixel limit.
    """
    notes: list[str] = []
    with PILImage.open(path) as opened:
        if opened.info.get("icc_profile"):
            notes.append("note: embedded ICC profile ignored; values used as display-encoded RGB")
        if opened.mode in ("RGB", "RGBA") and any(";16" in str(tile.args) for tile in opened.tile):
            notes.append("warning: 16-bit RGB source read at 8-bit precision (Pillow limitation)")
        image = ImageOps.exif_transpose(opened)
        if image.mode.startswith("I;16") or image.mode == "I":
            gray = np.asarray(image, dtype=np.float64) / 65535.0
            values = np.repeat(np.clip(gray, 0.0, 1.0)[..., None], 3, axis=2)
        else:
            values = np.asarray(image.convert("RGB"), dtype=np.float64) / 255.0
    return values.astype(np.float32), notes


def write_png16(path: Path, array: NDArray[np.float32]) -> None:
    """Write an ``(H, W, 3)`` RGB or ``(H, W)`` gray array in [0, 1] as a 16-bit PNG.

    The PNG is written directly (PNG specification, ISO/IEC 15948: IHDR with bit depth
    16 and colour type 2 or 0, one zlib-compressed IDAT with filter type 0 on every row,
    IEND), because Pillow cannot write 16-bit RGB. Values are clipped to [0, 1] and
    rounded to the nearest of 0..65535. No ICC profile, gamma or other colour chunk is
    written: the values are display-encoded and untagged.

    Args:
        path: The file to write (overwritten if present).
        array: The values, float32.

    Raises:
        ValueError: ``array`` is not ``(H, W)`` or ``(H, W, 3)``.
        OSError: The file cannot be written.
    """
    if array.ndim == 2:
        colour_type = 0
    elif array.ndim == 3 and array.shape[2] == 3:
        colour_type = 2
    else:
        raise ValueError(f"cannot write an array of shape {array.shape} as PNG")
    height, width = array.shape[0], array.shape[1]
    samples = np.round(np.clip(array, 0.0, 1.0) * 65535.0).astype(">u2")
    rows = samples.reshape(height, -1).view(np.uint8)
    scanlines = np.zeros((height, rows.shape[1] + 1), dtype=np.uint8)
    scanlines[:, 1:] = rows
    header = struct.pack(">IIBBBBB", width, height, 16, colour_type, 0, 0, 0)
    with path.open("wb") as handle:
        handle.write(_PNG_SIGNATURE)
        handle.write(_png_chunk(b"IHDR", header))
        handle.write(_png_chunk(b"IDAT", zlib.compress(scanlines.tobytes(), 6)))
        handle.write(_png_chunk(b"IEND", b""))


def main(argv: Sequence[str] | None = None) -> int:
    """Correct one image and write the result (and, with ``--dump``, every intermediate).

    Args:
        argv: Command-line arguments; defaults to ``sys.argv[1:]``.

    Returns:
        0 on success; 2 on a bad argument, an unusable device, an unreadable image or an
        unwritable output, with a one-line error on standard error.
    """
    parser = _Parser(description="Run the WP1.1 reference correction pipeline on one image.")
    parser.add_argument("--in", dest="input", type=Path, required=True, help="image to correct")
    parser.add_argument("--out", type=Path, required=True, help="folder for the output")
    parser.add_argument(
        "--method",
        choices=METHODS,
        help="compensation method (default c3; ancuti2018, or ancuti2018 with --blue)",
    )
    parser.add_argument(
        "--blue", action="store_true", help="Ancuti 2018 blue compensation (ancuti2018-blue)"
    )
    parser.add_argument("--neutral", action="store_true", help="start from Params.neutral()")
    parser.add_argument("--dump", action="store_true", help="write every intermediate")
    parser.add_argument(
        "--set", dest="overrides", action="append", default=[], metavar="NAME=VALUE"
    )
    parser.add_argument(
        "--device",
        choices=DEVICES,
        default="cpu",
        help="where to run (default cpu, for the same result on every machine; gpu is opt-in)",
    )
    try:
        args = parser.parse_args(argv)
        params = _build_params(args)
        backend = select_backend(args.device)
    except (_UsageError, RuntimeError) as exc:
        print(f"error: {_one_line(exc)}", file=sys.stderr)
        return 2
    if backend.reason:
        print(f"note: running on the CPU: {backend.reason}", file=sys.stderr)

    source: Path = args.input
    try:
        image, notes = read_image(source)
    except (OSError, ValueError, PILImage.DecompressionBombError) as exc:
        print(f"error: cannot read image {source.name}: {_one_line(exc)}", file=sys.stderr)
        return 2
    for note in notes:
        print(note, file=sys.stderr)
    try:
        check_derived_values(image.shape, params)  # a finite fraction can overflow at this size
    except ValueError as exc:
        print(f"error: {_one_line(exc)}", file=sys.stderr)
        return 2

    result = correct(image, params, backend)
    out_dir: Path = args.out
    stem = f"{source.stem}-{params.method}"
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = out_dir / f"{stem}.png"
        write_png16(output_path, result.output)
        if args.dump:
            _write_dump(out_dir, stem, result, backend)
    except OSError as exc:
        print(f"error: cannot write to {out_dir}: {_one_line(exc)}", file=sys.stderr)
        return 2
    print(output_path)
    return 0


def _build_params(args: argparse.Namespace) -> Params:
    """Build the parameter set from the parsed arguments.

    Raises:
        _UsageError: An override is malformed or a value is out of range.
    """
    changes: dict[str, Any] = {}
    if args.method is not None:
        changes["method"] = args.method
    if args.blue:
        changes["blue_compensation"] = True
    for override in args.overrides:
        name, value = _parse_override(override)
        changes[name] = value
    base = Params.neutral() if args.neutral else Params()
    try:
        return dataclasses.replace(base, **changes)
    except ValueError as exc:
        raise _UsageError(str(exc)) from exc


def _parse_override(text: str) -> tuple[str, object]:
    """Parse one ``NAME=VALUE`` override into a field name and a typed value.

    Raises:
        _UsageError: Unknown field or a value that does not parse as the field's type.
    """
    name, sep, raw = text.partition("=")
    hints = typing.get_type_hints(Params)
    if not sep or name not in hints:
        raise _UsageError(f"--set expects NAME=VALUE with a Params field, got {text!r}")
    hint = hints[name]
    raw = raw.strip()
    try:
        if hint is bool:
            if raw.lower() in _TRUE:
                return name, True
            if raw.lower() in _FALSE:
                return name, False
            raise ValueError("expected true or false")
        if hint is int:
            return name, int(raw)
        if hint is float:
            return name, float(raw)
        if hint == float | None:
            return name, None if raw.lower() == "none" else float(raw)
    except ValueError as exc:
        raise _UsageError(f"--set {name}: bad value {raw!r} ({exc})") from exc
    return name, raw


def _write_dump(out_dir: Path, stem: str, result: Result, backend: Backend) -> None:
    """Write every intermediate of ``result`` as a 16-bit PNG plus the JSON records."""
    stages = {
        "compensated": result.compensated,
        "white-balanced": result.white_balanced,
        "input1": result.input1,
        "input2": result.input2,
        "fused": result.fused,
    }
    for stage, array in stages.items():
        write_png16(out_dir / f"{stem}-{stage}.png", array)
    weights = result.weights
    scales: dict[str, float] = {}
    raw_maps = {"laplacian": weights.laplacian, "saliency": weights.saliency}
    raw_maps |= {"saturation": weights.saturation, "aggregated": weights.aggregated}
    for kind, maps in raw_maps.items():
        for index, weight in enumerate(maps, start=1):
            label = f"{kind}{index}"
            scale = float(weight.max())
            scales[label] = scale
            scaled = weight / np.float32(scale) if scale > 0.0 else weight
            write_png16(out_dir / f"{stem}-weight-{label}.png", scaled)
    for index, weight in enumerate(weights.normalised, start=1):
        write_png16(out_dir / f"{stem}-weight-normalised{index}.png", weight)
    _write_json(out_dir / f"{stem}-compensation.json", dataclasses.asdict(result.compensation))
    _write_json(out_dir / f"{stem}-white-balance.json", dataclasses.asdict(result.white_balance))
    weights_record = {
        "scale_divided_by": scales,
        "params": dataclasses.asdict(result.params),
        "backend": backend.name,
    }
    _write_json(out_dir / f"{stem}-weights.json", weights_record)


def _write_json(path: Path, record: dict[str, Any]) -> None:
    """Write ``record`` as indented UTF-8 JSON."""
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    """One PNG chunk: length, type, data and the CRC-32 of type and data."""
    crc = zlib.crc32(kind + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", crc)


def _one_line(exc: BaseException) -> str:
    """The exception's message on one line (its class name when the message is empty)."""
    return " ".join(str(exc).split()) or type(exc).__name__


if __name__ == "__main__":
    raise SystemExit(main())
