"""Dummy files for the sidecar and DNG tests (WP2.3 item 4).

- GoPro-style names (D83): ``GX010001.MP4``, ``GX020001.MP4``, ``GL010001.LRV``,
  ``GX010001.THM`` and their lower-case forms, as tiny text placeholders. Upper and lower case
  go in separate folders because NTFS and git on Windows treat the names as one. Chapter
  handling is deferred to v2 (spec v0.5.3), so the names exist only to be excluded or listed;
  the ``.MP4`` placeholders are not videos and must not be probed.
- DNG (D116, AD-17): a minimal TIFF carrying the ``DNGVersion`` tag (50706), once named
  ``.dng`` and once named ``.tif`` (refusal by extension and by the tag), plus a ``.dng`` with no
  tag (refusal by extension alone).
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import numpy as np
from PIL import Image, TiffImagePlugin

if not __package__:
    # Script mode: sys.path[0] is tools/fixtures; put tools first for the sibling packages.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fixtures import manifest
from spike_io.guard import WriteGuard

DNG_VERSION_TAG = 50706
"""The TIFF tag number of ``DNGVersion``."""

DNG_VERSION = (1, 4, 0, 0)
"""The ``DNGVersion`` value written (DNG 1.4.0.0)."""

GOPRO_NAMES = ("GX010001.MP4", "GX020001.MP4", "GL010001.LRV", "GX010001.THM")
"""The GoPro-style names; the lower-case variants are these lower-cased."""

SIDECAR_SUFFIXES = (".lrv", ".thm")
"""The suffixes D83 excludes (compared lower-case)."""


def placeholder_bytes(name: str) -> bytes:
    """Return the text a placeholder of this name holds.

    There is no line break in it, so git's CRLF conversion (``core.autocrlf``) cannot change
    the bytes on a Windows checkout.
    """
    return f"Clearwater test placeholder for {name}. Not a video.".encode("ascii")


def tiff_bytes(*, dng: bool) -> bytes:
    """Return a minimal 8 x 8 grey TIFF, with or without the ``DNGVersion`` tag.

    Args:
        dng: Write the ``DNGVersion`` tag (50706).

    Returns:
        The TIFF file's bytes.
    """
    directory = TiffImagePlugin.ImageFileDirectory_v2()
    if dng:
        directory[DNG_VERSION_TAG] = DNG_VERSION
    buffer = io.BytesIO()
    Image.fromarray(np.full((8, 8), 128, dtype=np.uint8)).save(buffer, "TIFF", tiffinfo=directory)
    return buffer.getvalue()


def dng_tag(path: Path) -> tuple[int, ...] | None:
    """Return the ``DNGVersion`` tag of a TIFF read back with Pillow, or None."""
    with Image.open(path) as image:
        value = image.tag_v2.get(DNG_VERSION_TAG) if hasattr(image, "tag_v2") else None
    return tuple(int(v) for v in value) if value is not None else None


def _write(guard: WriteGuard, out: Path, relative: str, data: bytes) -> Path:
    """Write ``data`` to ``out / relative`` through the guard."""
    path = guard.check(out / relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def build(guard: WriteGuard, out: Path) -> list[manifest.Entry]:
    """Write the placeholders and the DNG files under ``out``; return their entries.

    Args:
        guard: The write guard whose root is ``out``.
        out: The output folder.

    Returns:
        One entry per file.
    """
    entries: list[manifest.Entry] = []
    for case, names in (
        ("upper", GOPRO_NAMES),
        ("lower", tuple(name.lower() for name in GOPRO_NAMES)),
    ):
        for name in names:
            relative = f"files/gopro-{case}/{name}"
            file = _write(guard, out, relative, placeholder_bytes(name))
            sidecar = name.lower().endswith(SIDECAR_SUFFIXES)
            entries.append(
                manifest.entry(
                    sample_id=f"gopro-{case}-{name.lower().replace('.', '-')}",
                    group="files",
                    kind="placeholder",
                    storage="committed",
                    path=relative,
                    serves=["D83"],
                    exercises=(
                        f"The sidecar name {name}: excluded from the input list."
                        if sidecar
                        else f"The input name {name}: listed as an input (the file is a text "
                        "placeholder, not a video; do not probe it)."
                    ),
                    expected=manifest.expect(
                        faults=[manifest.fault("sidecar", "exclude")] if sidecar else []
                    ),
                    facts={
                        "name": name,
                        "case": case,
                        "sidecar": sidecar,
                        "is_video": False,
                    },
                    file=file,
                    byte_reproducible=True,
                )
            )
    refusal = {"clause": "D116", "by": "extension"}
    for sample_id, relative, tagged, by, serves in (
        ("dng-by-extension", "files/dng/dng-by-extension.dng", True, "extension", "D116"),
        ("dng-by-tag", "files/dng/dng-by-tag.tif", True, "tag", "D116 (AD-17)"),
        ("dng-extension-only", "files/dng/dng-extension-only.dng", False, "extension", "D116"),
    ):
        file = _write(guard, out, relative, tiff_bytes(dng=tagged))
        measured = dng_tag(file)
        entries.append(
            manifest.entry(
                sample_id=sample_id,
                group="files",
                kind="dng" if relative.endswith(".dng") else "tiff",
                storage="committed",
                path=relative,
                serves=[serves],
                exercises=(
                    f"A DNG refused by its {by}"
                    + (
                        ": a .dng file whose content is a TIFF with the DNGVersion tag."
                        if sample_id == "dng-by-extension"
                        else ": a .tif file carrying the DNGVersion tag (50706)."
                        if sample_id == "dng-by-tag"
                        else " alone: a .dng file with no DNGVersion tag."
                    )
                ),
                expected=manifest.expect(refusal={**refusal, "by": by}),
                facts={
                    "dng_version": list(measured) if measured is not None else None,
                    "dng_version_tag": DNG_VERSION_TAG,
                    "width": 8,
                    "height": 8,
                },
                file=file,
                byte_reproducible=True,
            )
        )
    return entries
