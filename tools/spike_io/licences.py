"""WP2.1S licence evidence (claim 3, spec N13): read from the installed artefacts only.

Every fact this module records comes from the installed packages or the FFmpeg executable on
PATH, never from documentation:

- each candidate distribution's metadata (``License-Expression`` or ``License``) and the
  names of the licence files its ``.dist-info`` ships (listed, not read);
- pillow-heif's ``LICENSES_bundled.txt`` (the native libraries its wheel bundles);
- PyAV's bundled FFmpeg: each library's ``configuration`` and ``license`` strings
  (``av._core.library_meta``), the build flags that decide its licence (``--enable-gpl``,
  ``--enable-version3``, ``--enable-nonfree``), the codecs and hardware devices it carries,
  the DLLs in ``av.libs`` and the wheel's ``DELVEWHEEL`` provenance file, and every licence
  string found inside the bundled x264, x265, libavcodec and libavutil DLLs (libavcodec's
  and libavutil's own licence strings are the scan's positive control);
- whether PyAV can open and use the libx264, libx265 and NVENC encoders: a few synthetic frames
  are encoded to memory, and the encoder's self-identification in the bitstream is recorded;
- the FFmpeg CLI build in use: ``ffmpeg -version``'s configuration line and ``ffmpeg -L``.

Run from the repository root: ``uv run python tools/spike_io/licences.py``; the record
``licences.json`` goes to ``<working folder>/wp2.1s/``. This is evidence for WP2.1, not
legal advice.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import io
import json
import re
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

import av
import av._core
from av.codec.hwaccel import hwdevices_available
from av.video.stream import VideoStream

if not __package__:
    # Script mode: sys.path[0] is tools/spike_io; put tools first for the sibling packages.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from local_config import load_local_config
from spike_io.guard import WriteGuard

DISTRIBUTIONS = ("av", "pillow", "pillow-heif", "numpy", "cupy-cuda12x", "scipy")
"""The Python distributions whose licence metadata is recorded."""

LICENCE_FLAGS = ("--enable-gpl", "--enable-version3", "--enable-nonfree")
"""The FFmpeg configure flags that decide the build's licence."""

CODECS = (
    "hevc",
    "h264",
    "hevc_nvenc",
    "h264_nvenc",
    "hevc_cuvid",
    "h264_cuvid",
    "libx264",
    "libx265",
)
"""The codecs whose presence in PyAV's bundled FFmpeg is recorded."""

_LICENCE_WORDING = re.compile(
    rb"(?<=\x00)[ -~]{0,120}(?:GPL|General Public License|Copyleft|copyleft)[ -~]{0,120}(?=\x00)"
)
"""A licence word inside a NUL-terminated printable string (a C string constant). Requiring the
NULs keeps out the bytes ``GPL`` that occur by chance inside machine code."""

ENCODERS = ("libx264", "libx265", "h264_nvenc", "hevc_nvenc")
"""The encoders :func:`pyav_encoders` opens and uses."""

ENCODE_SIZE = (256, 192)
"""Synthetic frame size for the encoder probe (NVENC refuses 64 x 48 with EINVAL)."""

ENCODE_FRAMES = 5
"""Frames encoded per encoder."""

_ENCODER_ID = re.compile(rb"x26[45] [ -~]{0,160}")


def distribution(name: str) -> dict[str, Any]:
    """Return a distribution's version, licence metadata and the names of its licence files.

    A licence file is a ``.dist-info`` file whose own name says LICENSE, LICENCE or COPYING;
    the files are listed by name, not read.
    """
    meta = importlib.metadata.metadata(name)
    files = importlib.metadata.files(name) or []
    licence_files = sorted(
        str(f)
        for f in files
        if ".dist-info" in str(f) and re.search(r"LICEN[CS]E|COPYING", f.name, re.IGNORECASE)
    )
    licence = meta.get("License") or ""
    return {
        "version": importlib.metadata.version(name),
        "license_expression": meta.get("License-Expression"),
        "license_field_first_line": licence.splitlines()[0] if licence else None,
        "license_classifiers": [c for c in meta.get_all("Classifier") or [] if "License" in c],
        "licence_files": licence_files,
    }


def _installed(name: str, relative: str) -> Path:
    """Return the path of a file a distribution installed (by its RECORD path)."""
    for entry in importlib.metadata.files(name) or []:
        if str(entry).replace("\\", "/") == relative:
            return Path(str(entry.locate()))
    raise FileNotFoundError(f"{name} did not install {relative}")


def pillow_heif_bundled() -> dict[str, Any]:
    """Parse pillow-heif's ``LICENSES_bundled.txt``: its header and one entry per library."""
    path = _installed("pillow-heif", "pillow_heif-1.8.1.dist-info/licenses/LICENSES_bundled.txt")
    text = path.read_text(encoding="utf-8")
    header = [line for line in text.split("\n\n", 1)[0].splitlines() if line.strip()]
    entries = []
    for block in text.split("\n\n"):
        fields = dict(
            line.split(": ", 1) for line in block.splitlines() if ": " in line and line[0] != " "
        )
        if "Name" in fields:
            entries.append({k: fields.get(k) for k in ("Name", "License", "Files")})
    # Every native file the wheel installed, by its RECORD (a name glob would miss some).
    native = [
        entry
        for entry in importlib.metadata.files("pillow-heif") or []
        if str(entry).lower().endswith((".dll", ".pyd", ".so", ".dylib"))
    ]
    return {
        "file": str(path),
        "header": header,
        "entries": entries,
        "native_files": sorted(str(entry) for entry in native),
        "native_files_present": all(Path(str(entry.locate())).is_file() for entry in native),
    }


def pyav_ffmpeg() -> dict[str, Any]:
    """Read PyAV's bundled FFmpeg: version, per-library licence and configuration, codecs."""
    meta = av._core.library_meta
    configuration = str(meta["libavutil"]["configuration"])
    flags = configuration.split()
    libs = Path(av.__file__).resolve().parent.parent / "av.libs"
    dlls = sorted(p.name for p in libs.glob("*.dll")) if libs.is_dir() else []
    wording: dict[str, list[str]] = {}
    for prefix in ("libx264", "libx265", "avcodec", "avutil"):
        for dll in libs.glob(f"{prefix}*.dll"):
            found = {
                m.group().decode("ascii").strip()
                for m in _LICENCE_WORDING.finditer(dll.read_bytes())
            }
            wording[dll.name] = sorted(found)[:10]
    delvewheel = Path(str(importlib.metadata.distribution("av").locate_file(""))) / (
        f"av-{av.__version__}.dist-info/DELVEWHEEL"
    )
    return {
        "av_version": av.__version__,
        "ffmpeg_version": av.ffmpeg_version_info,
        "library_licence": {name: str(info["license"]) for name, info in meta.items()},
        "same_configuration_everywhere": len({str(i["configuration"]) for i in meta.values()}) == 1,
        "licence_flags": {flag: flag in flags for flag in LICENCE_FLAGS},
        "external_libraries": sorted(
            f.split("=")[0] for f in flags if f.startswith("--enable-lib")
        ),
        "nvidia": {
            flag: flag in flags
            for flag in ("--enable-nvenc", "--enable-nvdec", "--enable-cuda-llvm")
        },
        "configuration": configuration,
        "codecs": {name: name in av.codecs_available for name in CODECS},
        "hwdevices": list(hwdevices_available()),
        "bundled_dlls": dlls,
        "dll_licence_wording": wording,
        "dist_info_licence_files": distribution("av")["licence_files"],
        "text_files": wheel_text_files("av"),
        "delvewheel": delvewheel.read_text(encoding="utf-8").splitlines()
        if delvewheel.is_file()
        else None,
        "library_versions": {name: list(v) for name, v in av.library_versions.items()},
    }


_CODE_SUFFIXES = (".py", ".pyi", ".pyx", ".pxd", ".pyd", ".pyc", ".dll", ".exe", ".c", ".h")
_TERMS = ("FFmpeg", "LGPL", "GPL", "General Public License", "x264", "x265")


def wheel_text_files(name: str) -> dict[str, Any]:
    """Read every non-code file a distribution installed and count licence-relevant terms.

    Args:
        name: The distribution.

    Returns:
        Per file (by RECORD path): its first non-empty line and how often each of
        ``FFmpeg``, ``LGPL``, ``GPL``, ``General Public License``, ``x264`` and ``x265`` occurs
        (case-sensitive; ``GPL`` also counts inside ``LGPL``).
    """
    out: dict[str, Any] = {}
    for entry in importlib.metadata.files(name) or []:
        if str(entry).endswith(_CODE_SUFFIXES):
            continue
        path = Path(str(entry.locate()))
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        first = next((line.strip() for line in text.splitlines() if line.strip()), "")
        out[str(entry).replace("\\", "/")] = {
            "first_line": first[:120],
            "terms": {term: text.count(term) for term in _TERMS},
        }
    return out


def pyav_encoders() -> dict[str, Any]:
    """Open each of :data:`ENCODERS` in PyAV and encode a few synthetic frames to memory.

    Returns:
        Per encoder: ``opens`` (``av.codec.Codec(name, "w")``), ``packets`` and ``bytes``
        written, the encoder's self-identification found in the bitstream (x264 and x265
        write one), or the error.
    """
    import numpy as np

    width, height = ENCODE_SIZE
    out: dict[str, Any] = {}
    for name in ENCODERS:
        record: dict[str, Any] = {}
        try:
            record["opens"] = av.codec.Codec(name, "w").long_name
        except Exception as error:  # the error is the finding
            record["opens"] = f"{type(error).__name__}: {error}"
            out[name] = record
            continue
        buffer = io.BytesIO()
        try:
            container = av.open(
                buffer, "w", format="hevc" if "265" in name or "hevc" in name else "h264"
            )
            stream = cast(VideoStream, container.add_stream(name, rate=30))
            stream.width, stream.height, stream.pix_fmt = width, height, "yuv420p"
            packets = 0
            for i in range(ENCODE_FRAMES):
                frame = av.VideoFrame.from_ndarray(
                    np.full((height, width, 3), i * 40, np.uint8), format="rgb24"
                )
                for packet in stream.encode(frame):
                    container.mux(packet)
                    packets += 1
            for packet in stream.encode():
                container.mux(packet)
                packets += 1
            container.close()
        except Exception as error:  # the error is the finding
            record["encode"] = f"{type(error).__name__}: {error}"
            out[name] = record
            continue
        data = buffer.getvalue()
        found = _ENCODER_ID.search(data)
        record.update(
            {
                "encode": "ok",
                "packets": packets,
                "bytes": len(data),
                "self_identification": found.group().decode("ascii") if found else None,
            }
        )
        out[name] = record
    return out


def ffmpeg_cli() -> dict[str, Any]:
    """Read the FFmpeg CLI on PATH: version line, configuration flags and ``-L`` text."""
    version = subprocess.run(
        ["ffmpeg", "-hide_banner", "-version"], capture_output=True, text=True, check=True
    ).stdout.splitlines()
    licence = subprocess.run(
        ["ffmpeg", "-hide_banner", "-L"], capture_output=True, text=True, check=True
    ).stdout
    configuration = next((line for line in version if line.startswith("configuration:")), "")
    flags = configuration.split()
    return {
        "version_line": version[0] if version else "",
        "licence_flags": {flag: flag in flags for flag in LICENCE_FLAGS},
        "libx264": "--enable-libx264" in flags,
        "libx265": "--enable-libx265" in flags,
        "licence_text": " ".join(licence.split())[:400],
    }


def collect() -> dict[str, Any]:
    """Return the whole licence record."""
    return {
        "distributions": {name: distribution(name) for name in DISTRIBUTIONS},
        "pillow_heif_bundled": pillow_heif_bundled(),
        "pyav_ffmpeg": pyav_ffmpeg(),
        "pyav_encoders": pyav_encoders(),
        "ffmpeg_cli": ffmpeg_cli(),
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Command line: write ``licences.json`` to ``<working folder>/wp2.1s/``."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--config", type=Path, default=None, help="local configuration file")
    arguments = parser.parse_args(argv)
    guard = WriteGuard.for_config(load_local_config(arguments.config))
    path = guard.root / "licences.json"
    guard.check(path).write_text(json.dumps(collect(), indent=1) + "\n", encoding="utf-8")
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
