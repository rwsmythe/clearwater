"""WP2.1S licence evidence (claim 3, spec N13): read from the installed artefacts only.

Every fact this module records comes from the installed packages or the FFmpeg executable on
PATH, never from documentation:

- each candidate distribution's metadata (``License-Expression`` or ``License``) and the
  licence files its ``.dist-info`` ships;
- pillow-heif's ``LICENSES_bundled.txt`` (the native libraries its wheel bundles);
- PyAV's bundled FFmpeg: each library's ``configuration`` and ``license`` strings
  (``av._core.library_meta``), the build flags that decide its licence (``--enable-gpl``,
  ``--enable-version3``, ``--enable-nonfree``), the codecs and hardware devices it carries,
  the DLLs in ``av.libs``, and any licence wording found inside the bundled x264 and x265
  DLLs;
- the FFmpeg CLI build in use: ``ffmpeg -version``'s configuration line and ``ffmpeg -L``.

Run from the repository root: ``uv run python tools/spike_io/licences.py``; the record
``licences.json`` goes to ``<working folder>/wp2.1s/``. This is evidence for WP2.1, not
legal advice.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import re
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import av
import av._core
from av.codec.hwaccel import hwdevices_available

if not __package__:
    # Script mode: sys.path[0] is tools/spike_io; put tools first for the sibling packages.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from local_config import load_local_config

WORK_SUBDIR = "wp2.1s"
"""The folder inside the working folder that every output of this package goes to."""

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
    rb"[ -~]{0,80}(?:GPL|General Public License|Copyleft|copyleft)[ -~]{0,80}"
)


def distribution(name: str) -> dict[str, Any]:
    """Return a distribution's version, licence metadata and shipped licence files."""
    meta = importlib.metadata.metadata(name)
    files = importlib.metadata.files(name) or []
    licence_files = sorted(
        str(f)
        for f in files
        if ".dist-info" in str(f) and re.search(r"LICEN[CS]E|COPYING", str(f), re.IGNORECASE)
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
    package = Path(str(importlib.metadata.distribution("pillow-heif").locate_file("")))
    return {
        "file": str(path),
        "header": header,
        "entries": entries,
        "native_files": sorted(p.name for p in package.glob("libheif*")),
    }


def pyav_ffmpeg() -> dict[str, Any]:
    """Read PyAV's bundled FFmpeg: version, per-library licence and configuration, codecs."""
    meta = av._core.library_meta
    configuration = str(meta["libavutil"]["configuration"])
    flags = configuration.split()
    libs = Path(av.__file__).resolve().parent.parent / "av.libs"
    dlls = sorted(p.name for p in libs.glob("*.dll")) if libs.is_dir() else []
    wording: dict[str, list[str]] = {}
    for prefix in ("libx264", "libx265"):
        for dll in libs.glob(f"{prefix}*.dll"):
            found = {
                m.group().decode("ascii").strip()
                for m in _LICENCE_WORDING.finditer(dll.read_bytes())
            }
            wording[dll.name] = sorted(found)[:10]
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
    }


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
        "ffmpeg_cli": ffmpeg_cli(),
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Command line: write ``licences.json`` to ``<working folder>/wp2.1s/``."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--config", type=Path, default=None, help="local configuration file")
    arguments = parser.parse_args(argv)
    config = load_local_config(arguments.config)
    out = config.working_path / WORK_SUBDIR
    footage = config.footage_path.resolve()
    if out.resolve() == footage or footage in out.resolve().parents:
        raise SystemExit(f"{out} is inside the footage folder")
    out.mkdir(parents=True, exist_ok=True)
    path = out / "licences.json"
    path.write_text(json.dumps(collect(), indent=1) + "\n", encoding="utf-8")
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
