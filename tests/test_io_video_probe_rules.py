"""Rule tests of the video probe (WP3.7): the owner's IMU/GPS ruling, imports, the real clip.

- No module under ``clearwater.io.video`` names a sensor, location or telemetry-track token, or
  asks ffprobe for packet data, and ``src/`` does not import ``tools``.
- Importing the package loads nothing from the GUI, jobs, methods, PySide6 or cupy (plan 8.1).
- A real HERO13 chapter (``footage``-marked, read only) probes to the WP1.5 section 3 facts.
"""

from __future__ import annotations

import re
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

from clearwater.io.video import probe

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE = REPO_ROOT / "src" / "clearwater" / "io" / "video"

FORBIDDEN_TOKENS = re.compile(
    r"\b(ACCL|GYRO|GRAV|CORI|IORI|GPS\w*|gpmd|HDRV|BITR)\b", re.IGNORECASE
)
FORBIDDEN_COMMANDS = re.compile(r"-show_data|-show_frames|-count_frames|-show_packets|-dump")
_MP4_COPY_ALLOWLIST_LINE = 'MP4_DATA_CODEC_TAGS = frozenset({"gpmd"})'


def _assert_no_forbidden_tokens(module: Path, text: str) -> None:
    """Check tokens after excluding exactly one ruled encoder copy-allowlist line."""
    if module.name == "encode.py":
        # e3a7a4ea2dc9477f: GPMF rule - this stream-copy allowlist tag is never parsed.
        lines = text.splitlines()
        assert lines.count(_MP4_COPY_ALLOWLIST_LINE) == 1, (
            "exactly one allowlist definition required"
        )
        text = "\n".join(line for line in lines if line != _MP4_COPY_ALLOWLIST_LINE)
    assert FORBIDDEN_TOKENS.findall(text) == []


def test_the_package_exists_and_has_the_expected_modules() -> None:
    assert {p.name for p in PACKAGE.glob("*.py")} == {
        "__init__.py",
        "boxes.py",
        "capability.py",
        "decode.py",
        "encode.py",
        "gopro.py",
        "inputs.py",
        "nut.py",
        "pipes.py",
        "probe.py",
        "verify.py",
    }


@pytest.mark.parametrize("module", sorted(PACKAGE.glob("*.py")), ids=lambda p: p.name)
def test_no_module_names_an_imu_gps_or_telemetry_token(module: Path) -> None:
    text = module.read_text(encoding="utf-8")
    _assert_no_forbidden_tokens(module, text)
    assert FORBIDDEN_COMMANDS.findall(text) == []


@pytest.mark.parametrize("change", ["extra-token", "missing-line", "doubled-line"])
def test_encoder_token_guard_rejects_planted_changes(change: str) -> None:
    """Reject another forbidden token or a missing or repeated allowlist definition."""
    module = PACKAGE / "encode.py"
    text = module.read_text(encoding="utf-8")
    if change == "extra-token":
        text += "\n# gpmd planted guard control\n"
    elif change == "missing-line":
        text = text.replace(_MP4_COPY_ALLOWLIST_LINE + "\n", "")
    else:
        text += "\n" + _MP4_COPY_ALLOWLIST_LINE + "\n"
    message = None if change == "extra-token" else "exactly one allowlist definition required"
    with pytest.raises(AssertionError, match=message):
        _assert_no_forbidden_tokens(module, text)


@pytest.mark.parametrize("module", sorted(PACKAGE.glob("*.py")), ids=lambda p: p.name)
def test_no_module_imports_tools(module: Path) -> None:
    text = module.read_text(encoding="utf-8")
    assert not re.search(r"^\s*(from|import)\s+tools\b", text, re.MULTILINE)


def test_src_does_not_import_tools_anywhere() -> None:
    offenders = [
        p
        for p in (REPO_ROOT / "src").rglob("*.py")
        if re.search(r"^\s*(from|import)\s+tools\b", p.read_text(encoding="utf-8"), re.MULTILINE)
    ]
    assert offenders == []


def test_importing_the_package_loads_no_gui_jobs_methods_or_heavy_libraries() -> None:
    code = "\n".join(
        [
            "import sys, clearwater.io.video",
            "banned = ('clearwater.gui', 'clearwater.jobs', 'clearwater.methods',",
            "          'PySide6', 'cupy')",
            "print(','.join(sorted(m for m in sys.modules",
            "    if any(m == b or m.startswith(b + '.') for b in banned))))",
        ]
    )
    done = subprocess.run(
        [sys.executable, "-I", "-c", code], capture_output=True, text=True, check=True
    )
    assert done.stdout.strip() == ""


# --- the real clip ------------------------------------------------------------------------------


@pytest.mark.footage
def test_a_real_hero13_chapter_probes_to_the_recorded_facts() -> None:
    from local_config import FootageLookupError, find_footage_file, load_local_config

    config = load_local_config()
    try:
        path = find_footage_file("GX011627", config.footage_path)
    except FootageLookupError as error:
        if error.matches:
            raise
        pytest.skip("GX011627 is not in the footage folder")
    result = probe(path)
    video = result.video
    assert result.faults == ()
    assert (video.codec, video.width, video.height, video.bit_depth) == ("hevc", 3840, 2160, 8)
    assert video.pix_fmt == "yuvj420p"
    assert video.nb_frames == 681 and video.frame_rate == Fraction(30000, 1001)
    assert video.vfr is False and video.rotation == 0
    color = video.color
    assert (color.primaries, color.transfer, color.matrix) == ("bt709", "bt709", "bt709")
    assert (color.range, color.assumed) == ("full", False)
    assert video.chroma_siting == "left"
    assert result.start_offset_s == 0
    (edit,) = result.edit_list
    assert (edit.media_time_s, edit.media_rate) == (0, 1)
    assert edit.segment_duration_s == Fraction(681 * 1001, 30000)
    assert result.gopro is not None
    assert result.gopro.firmware == "H24.01.02.10.00"
    assert (result.gopro.protune, result.gopro.color_profile) == (True, "NATURAL")
    assert len(result.audio) == 1 and result.audio[0].sample_rate == 48000
    assert {d.codec_tag for d in result.data} == {"tmcd", "gpmd"}
