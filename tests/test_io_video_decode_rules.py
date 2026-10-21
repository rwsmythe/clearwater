"""Rule tests of the video decode (WP3.9): the command, imports, and DR-36 (a).

- The decode command maps the first video stream only (no audio, subtitle or data stream: no
  ``gpmd`` or ``tmcd``), keeps the source timing (``-copyts``, ``-fps_mode passthrough``), the
  stored orientation (``-noautorotate``), reads a ``file:`` URL, and puts ``showinfo`` first.
- The decode runs no ffprobe and no open-ended ``-read_intervals``; ``src/`` does not import
  ``tools``.
- Importing ``clearwater.io.video`` loads nothing from the GUI, jobs, methods, core or analysis,
  nor PySide6 or cupy (plan 8.1).
- DR-36 (a): the probe's two structural log warnings name the file ASCII-safe.
"""

from __future__ import annotations

import importlib
import logging
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from clearwater.io.video import decode as decode_module
from clearwater.io.video import probe

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE = REPO_ROOT / "src" / "clearwater" / "io" / "video"
OWNED = [PACKAGE / "decode.py", PACKAGE / "pipes.py"]
SAMPLES = ["vid-hevc8-bt709-full", "vid-hevc10", "vid-untagged", "vid-vfr", "vid-rotated"]


@pytest.mark.usefixtures("ffmpeg_tools")
@pytest.mark.parametrize("sample_id", SAMPLES)
@pytest.mark.parametrize("cuda", [False, True])
def test_the_decode_command_maps_the_video_stream_only(
    sample_id: str, cuda: bool, sample: Callable[[str], Path]
) -> None:
    result = probe(sample(sample_id))
    command = decode_module.decode_command(
        result, ffmpeg=Path("ffmpeg"), cuda=cuda, seek="1.000000"
    )
    maps = [command[at + 1] for at, arg in enumerate(command) if arg == "-map"]
    assert maps == ["0:v:0"]
    for flag in ("-an", "-sn", "-dn", "-nostdin", "-noautorotate", "-copyts"):
        assert command.count(flag) == 1, flag
    assert command[command.index("-fps_mode") + 1] == "passthrough"
    assert command[command.index("-f") + 1] == "rawvideo" and command[-1] == "pipe:1"
    source = command[command.index("-i") + 1]
    assert source == f"file:{result.path.absolute()}"
    assert command.index("-ss") < command.index("-i")
    assert command[command.index("-vf") + 1].startswith("showinfo,scale=")
    assert ("-hwaccel" in command) is cuda
    assert "-hwaccel_output_format" not in command


@pytest.mark.parametrize("module", OWNED, ids=lambda p: p.name)
def test_the_decode_modules_name_no_other_stream_and_run_no_ffprobe(module: Path) -> None:
    text = module.read_text(encoding="utf-8")
    assert not re.search(r"0:[adst]\b|-map\s+0\b|\bgpmd\b|\btmcd\b|-read_intervals", text)
    assert '"ffprobe"' not in text


@pytest.mark.parametrize("module", OWNED, ids=lambda p: p.name)
def test_the_decode_modules_do_not_import_tools(module: Path) -> None:
    text = module.read_text(encoding="utf-8")
    assert not re.search(r"^\s*(from|import)\s+tools\b", text, re.MULTILINE)


def test_src_does_not_import_tools_anywhere() -> None:
    offenders = [
        p
        for p in (REPO_ROOT / "src").rglob("*.py")
        if re.search(r"^\s*(from|import)\s+tools\b", p.read_text(encoding="utf-8"), re.MULTILINE)
    ]
    assert offenders == []


def test_importing_the_package_loads_no_upper_layer_or_heavy_library() -> None:
    code = "\n".join(
        [
            "import sys, clearwater.io.video, clearwater.io.video.decode",
            "banned = ('clearwater.gui', 'clearwater.jobs', 'clearwater.methods',",
            "          'clearwater.core', 'clearwater.analysis', 'PySide6', 'cupy')",
            "print(','.join(sorted(m for m in sys.modules",
            "    if any(m == b or m.startswith(b + '.') for b in banned))))",
        ]
    )
    done = subprocess.run(
        [sys.executable, "-I", "-c", code], capture_output=True, text=True, check=True
    )
    assert done.stdout.strip() == ""


def test_the_only_os_specific_code_is_the_pipe() -> None:
    for module in OWNED:
        text = module.read_text(encoding="utf-8")
        hits = re.findall(r"sys\.platform|_winapi|msvcrt|os\.name|platform\.system", text)
        if module.name == "decode.py":
            assert hits == []
        else:
            assert sorted(set(hits)) == ["_winapi", "msvcrt", "sys.platform"]


# --- DR-36 (a) ----------------------------------------------------------------------------------


@pytest.mark.usefixtures("ffmpeg_tools")
def test_the_probe_names_a_non_ascii_file_ascii_safe_when_its_boxes_fail(
    sample: Callable[[str], Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    probe_module = importlib.import_module("clearwater.io.video.probe")
    copy = tmp_path / "é水.mp4"
    shutil.copyfile(sample("vid-hevc8-bt709-full"), copy)

    def broken(path: Path) -> object:
        raise probe_module.BoxError("planted")

    monkeypatch.setattr(probe_module, "read_movie_boxes", broken)
    with caplog.at_level(logging.WARNING, logger=probe_module.__name__):
        probe(copy)
    (message,) = [r.getMessage() for r in caplog.records]
    assert message.isascii() and "\\xe9\\u6c34.mp4" in message


@pytest.mark.usefixtures("ffmpeg_tools")
def test_the_probe_names_a_non_ascii_file_ascii_safe_when_its_gpmf_fails(
    sample: Callable[[str], Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    probe_module = importlib.import_module("clearwater.io.video.probe")
    copy = tmp_path / "é水.mp4"
    shutil.copyfile(sample("vid-hevc8-bt709-full"), copy)
    boxes = probe_module.MovieBoxes(
        movie_timescale=None, video_timescale=None, edits=(), gpmf=b"planted"
    )

    def malformed(data: bytes) -> object:
        raise probe_module.GPMFError("planted")

    monkeypatch.setattr(probe_module, "read_movie_boxes", lambda path: boxes)
    monkeypatch.setattr(probe_module, "parse_settings", malformed)
    with caplog.at_level(logging.WARNING, logger=probe_module.__name__):
        probe(copy)
    (message,) = [r.getMessage() for r in caplog.records]
    assert message.isascii() and "\\xe9\\u6c34.mp4" in message
