"""Native macOS portability tests (WP6.4 writes them; WP6.5 runs them on the owner's Mac).

Each M function takes a ``site`` parameter: the WP6.2 audit row whose mechanic it checks on a
real Mac (section 8's M references). Every test is marked ``macos`` and skipped off darwin by an
explicit platform skip (AD-36); the native interface rows also carry ``gui``. Nothing here
patches ``sys.platform``: the platform is the host's.

The rows shared with the Windows-side module re-run that module's case NATIVELY (the real APFS
volume, the real macOS ``realpath`` and ``normcase``, the real FFmpeg), then add the checks only
a Mac can make: a case-insensitive APFS, a case-sensitive APFS and an exFAT disk image
(``hdiutil``, created and detached under the test's temporary folder; a case check never relies
on the host temporary volume's case behaviour), real VideoToolbox encodes, a child in its own
session, the Cocoa platform. A runner without VideoToolbox (a CI Mac) passes M-CODEC and M-V4
on a PROVED "unavailable" with its reason and the x265 fallback, and skips the VT-only cases
with that reason; it does not replace the owner's hardware evidence (audit section 8).

Isolation (CLAUDE.md's entry-point rule; DR-124): every child that imports the product runs
with HOME, APPDATA, LOCALAPPDATA and the XDG variables pointed at a disposable folder and a
bounded timeout; no test calls ``clearwater.__main__``, ``app.main`` or the export worker's
entry point; no test sends input to the desktop (native UI rows send Qt events to Clearwater's
own widgets only, and the interactive dialog checks are the owner's at WP6.5). Synthetic
footage only: the owner's footage folder is never read.
"""

from __future__ import annotations

import contextlib
import errno
import functools
import hashlib
import importlib
import json
import os
import re
import shutil
import signal
import struct
import subprocess
import sys
import textwrap
import time
import unicodedata
import warnings
from collections.abc import Iterator, Sequence
from fractions import Fraction
from itertools import pairwise
from pathlib import Path
from typing import Any

import pytest

MACOS_ONLY = pytest.mark.skipif(sys.platform != "darwin", reason="macOS native leg (WP6.5)")
pytestmark = [pytest.mark.macos, MACOS_ONLY]

REPO = Path(__file__).parents[1]
TIMEOUT_S = 120
VT = "hevc_videotoolbox"
X265 = "libx265"
BUNDLE_VARIABLE = "CLEARWATER_MAC_BUNDLE"
"""The path of WP6.5's ``Clearwater.app``; the M-BUNDLE rows skip with a reason when unset."""


def _w() -> Any:
    """The Windows-side module, whose cases the shared rows re-run natively."""
    return importlib.import_module("test_portability")


def _isolated_env(root: Path, **extra: str) -> dict[str, str]:
    """A child environment whose every profile root is under ``root`` (entry-point rule)."""
    home = root / "home"
    home.mkdir(parents=True, exist_ok=True)
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("XDG_")}
    env.update(
        HOME=str(home),
        USERPROFILE=str(home),
        APPDATA=str(root / "appdata"),
        LOCALAPPDATA=str(root / "localappdata"),
        XDG_CONFIG_HOME=str(root / "xdg-config"),
        XDG_CACHE_HOME=str(root / "xdg-cache"),
        XDG_DATA_HOME=str(root / "xdg-data"),
        PYTHONPATH=os.pathsep.join([str(REPO / "src"), str(REPO / "tools")]),
    )
    env.update(extra)
    return env


def _python(code: str, root: Path, *, timeout: int = TIMEOUT_S, **extra: str) -> Any:
    """Run ``code`` in an isolated child Python and return its last stdout line as JSON."""
    done = subprocess.run(
        [sys.executable, "-c", textwrap.dedent(code)],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=_isolated_env(root, **extra),
        cwd=root,
        check=False,
    )
    assert done.returncode == 0, done.stderr[-2000:]
    return json.loads(done.stdout.strip().splitlines()[-1])


def _ffmpeg() -> Path:
    from clearwater.io.video import find_tool

    return find_tool("ffmpeg")


def _run(argv: Sequence[str], *, timeout: int = TIMEOUT_S) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(argv), stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout
    )


def _lavfi(source: str, seconds: float) -> str:
    """The lavfi source text: the geometry joins ``source``'s own options with ``:``.

    ``color=c=0x204060`` already has an option, so ``=size=...`` would make the size part of
    the colour value (Reviewer A r2 item 4); a bare ``testsrc2`` takes ``=``.
    """
    separator = ":" if "=" in source else "="
    return f"{source}{separator}size=1280x720:rate=30000/1001:duration={seconds}"


def _clip(
    path: Path, *, seconds: float = 1.0, source: str = "testsrc2", extra: Sequence[str] = ()
) -> Path:
    """Write a synthetic HEVC (x265) clip: ``source`` at 1280x720, 30000/1001, ``seconds`` long.

    ``extra`` holds OUTPUT options only (they follow the input); an input option such as
    ``-display_rotation`` goes through :func:`_remux`, before its ``-i``.
    """
    done = _run(
        [
            str(_ffmpeg()),
            "-nostdin",
            "-hide_banner",
            "-v",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            _lavfi(source, seconds),
            "-c:v",
            X265,
            "-x265-params",
            "log-level=error",
            "-pix_fmt",
            "yuv420p",
            "-tag:v",
            "hvc1",
            *extra,
            str(path),
        ]
    )
    assert done.returncode == 0, done.stderr[-1000:]
    return path


def _remux(source: Path, path: Path, *, input_options: Sequence[str]) -> Path:
    """Copy ``source``'s streams into ``path`` with ``input_options`` BEFORE its ``-i``.

    The order ``tools/fixtures/video.py`` builds its rotated sample with: ``-display_rotation``
    is an input option, so it must precede the input it applies to.
    """
    done = _run(
        [
            str(_ffmpeg()),
            "-nostdin",
            "-hide_banner",
            "-v",
            "error",
            "-y",
            *input_options,
            "-i",
            str(source),
            "-c",
            "copy",
            str(path),
        ]
    )
    assert done.returncode == 0, done.stderr[-1000:]
    return path


def _ffprobe_json(path: Path, *arguments: str) -> dict[str, Any]:
    from clearwater.io.video import find_tool

    done = _run([str(find_tool("ffprobe")), "-v", "error", "-of", "json", *arguments, str(path)])
    assert done.returncode == 0, done.stderr[-1000:]
    data: dict[str, Any] = json.loads(done.stdout)
    return data


@functools.cache
def _native_capabilities() -> tuple[Any, ...]:
    from clearwater.io.video import capability

    return capability._detect(_ffmpeg(), capability.encoder_roster())


def _capability(name: str) -> Any:
    return next(c for c in _native_capabilities() if c.name == name)


def assert_proved_unavailable(row: Any) -> None:
    """An unavailable encoder is PROVED so: a non-empty ASCII reason and no bit depth (A r2 11)."""
    assert not row.available
    assert isinstance(row.reason, str) and row.reason.strip() and row.reason.isascii(), row
    assert tuple(row.bit_depths) == (), row


def assert_advertised(row: Any) -> None:
    """An available encoder advertises a non-empty subset of the product's depths (8, 10)."""
    assert row.available and row.bit_depths, row
    assert set(row.bit_depths) <= {8, 10} and list(row.bit_depths) == sorted(row.bit_depths), row


def assert_unadvertised_refused(row: Any) -> None:
    """Each depth an available encoder does NOT advertise is refused by the sink by name (AD-35
    permits a working 8-bit VideoToolbox without a 10-bit one); nothing is encoded."""
    from clearwater.io.video.encode import FFmpegVideoSink, VideoEncodeError

    for depth in sorted({8, 10} - set(row.bit_depths)):
        with pytest.raises(VideoEncodeError) as caught:
            FFmpegVideoSink()._check_options(row.name, "standard", depth)
        assert caught.value.kind == "unavailable" and f"{depth}-bit" in str(caught.value)


def _vt_or_skip() -> Any:
    """Return VideoToolbox's row; skip a VT-only case where VT is PROVED unavailable."""
    vt = _capability(VT)
    if not vt.available:
        assert_proved_unavailable(vt)
        pytest.skip(f"VideoToolbox unavailable on this Mac: {vt.reason}")
    assert_advertised(vt)
    return vt


def _encode(source: Path, out: Path, *, encoder: str, quality: str, bit_depth: int) -> Any:
    """Decode ``source`` on the CPU and re-encode it unchanged through the product's sink."""
    from clearwater.io.video import FFmpegVideoSink, FFmpegVideoSource

    reader = FFmpegVideoSource()
    probe = reader.probe(source)
    sink = FFmpegVideoSink()
    sink.open(probe, out, encoder=encoder, quality=quality, bit_depth=bit_depth, provenance=None)
    for frame in reader.frames(probe, hw_decode=False):
        sink.write(frame)
    return probe, sink.close()


# --- volumes ---------------------------------------------------------------------------------


_IMAGES = (("insensitive", "APFS"), ("sensitive", "Case-sensitive APFS"), ("exfat", "ExFAT"))
"""The disk images ``volumes`` attaches: (label, ``hdiutil -fs`` name); APFS is case-insensitive."""


@pytest.fixture(scope="module")
def volumes(tmp_path_factory: pytest.TempPathFactory) -> Iterator[dict[str, Path]]:
    """Attach a case-insensitive APFS, a case-sensitive APFS and an exFAT disk image.

    Every image is created explicitly (Reviewer B finding 5): the host temporary volume's case
    behaviour is never relied on, so the case-alias checks run on ``insensitive`` and the
    distinct-name controls on ``sensitive`` whatever the host's volume is.
    """
    root = tmp_path_factory.mktemp("volumes")
    mounted: dict[str, Path] = {}
    try:
        for label, fs in _IMAGES:
            image, mount = root / f"{label}.dmg", root / label
            created = _run(
                [
                    "hdiutil",
                    "create",
                    "-size",
                    "64m",
                    "-fs",
                    fs,
                    "-volname",
                    f"cw{label}",
                    str(image),
                ]
            )
            if created.returncode != 0:
                pytest.skip(
                    f"hdiutil could not create a {fs} image: {created.stderr.strip()[-200:]}"
                )
            attached = _run(
                ["hdiutil", "attach", "-nobrowse", "-mountpoint", str(mount), str(image)]
            )
            if attached.returncode != 0:
                pytest.skip(
                    f"hdiutil could not attach the {fs} image: {attached.stderr.strip()[-200:]}"
                )
            mounted[label] = mount
        yield mounted
    finally:
        for label, _fs in _IMAGES:
            if label in mounted:
                _run(["hdiutil", "detach", "-force", str(mounted[label])])


def _case_insensitive(folder: Path) -> bool:
    probe = folder / "CaseProbe.tmp"
    probe.write_bytes(b"x")
    try:
        return (folder / "caseprobe.tmp").exists()
    finally:
        probe.unlink()


# --- M-STATIC --------------------------------------------------------------------------------

STATIC_FILES = {
    "P02": "src/clearwater/io/video/pipes.py",
    "P58": "src/clearwater/gpu_pack.py",
    "P65": "src/clearwater/io/video/pipes.py",
    "T03": "tools/prototype/bench.py",
    "T05": "tools/prototype/bench.py",
    "T09": "tools/spike_io/transport.py",
    "T49": "tools/prototype/bench.py",
    "T50": "tools/prototype/bench.py",
    "T51": "tools/spike_io/transport.py",
}


@functools.cache
def _native_mypy(cache: str) -> tuple[int, str]:
    done = subprocess.run(
        [sys.executable, "-m", "mypy", "--cache-dir", cache],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=900,
        cwd=REPO,
        check=False,
    )
    return done.returncode, done.stdout + done.stderr


@pytest.mark.parametrize("site", sorted(STATIC_FILES))
def test_macos_static_target_policy(site: str, tmp_path_factory: pytest.TempPathFactory) -> None:
    """M-STATIC: the strict mypy gate on the full ``files`` set, natively (darwin target, no
    ``--platform`` spoofing), is clean, and the site's guard is in the AD-36 statement form."""
    status, output = _native_mypy(str(tmp_path_factory.getbasetemp() / "mypy-cache"))
    relative = STATIC_FILES[site]
    assert relative.replace("/", os.sep) not in output and relative not in output, output[-2000:]
    assert status == 0 and "Success: no issues found" in output, output[-2000:]
    source = (REPO / relative).read_text(encoding="utf-8")
    assert _w().guard_form_offenders(source, relative) == []


# --- M-PATH ----------------------------------------------------------------------------------


def _path_native(site: str, tmp_path: Path) -> None:
    result = _python(
        """
        import json
        from pathlib import Path
        from clearwater.config.paths import app_locations
        from clearwater.app.startup import JOURNAL_FILE_NAME, WriteJournal
        from clearwater import gpu_pack
        found = app_locations()
        journal = WriteJournal(found.config_dir)
        print(json.dumps({
            "home": str(Path.home()),
            "config": str(found.config_dir),
            "cache": str(found.cache_dir),
            "journal": str(journal.path), "pack": gpu_pack.pack_root() is None,
        }))
        """,
        tmp_path,
    )
    home = Path(result["home"])
    assert home == tmp_path / "home"  # HOME is the only root on macOS (no XDG, no migration)
    assert Path(result["config"]) == home / "Library" / "Application Support" / "Clearwater"
    assert Path(result["cache"]) == home / "Library" / "Caches" / "Clearwater"
    assert Path(result["journal"]).parent == Path(result["config"])  # P25 / P26
    assert result["pack"] is True  # P56: no GPU pack on macOS
    assert not (tmp_path / "xdg-config").exists() and not (tmp_path / "appdata").exists()


PATH_SITES = ("P01", "P25", "P26", "P56", "X13", "X14", "X15", "X16")


@pytest.mark.parametrize("site", PATH_SITES)
def test_macos_app_locations_and_isolation(
    site: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """M-PATH: the Library roots from the real HOME resolution, in a child redirected to a
    disposable home; the injected Windows-side case natively; nothing created by resolving."""
    _path_native(site, tmp_path / "native")
    (tmp_path / "w").mkdir()  # the W case lists its scratch folder at the end (A r2 item 3)
    with pytest.MonkeyPatch.context() as w_patch:  # the W stubs end before the native half
        _w().PATH_CASES[site](w_patch, tmp_path / "w")
    if site in ("X15", "X16"):  # the start-up tests' own redirection resolves under the sentinel
        from clearwater.config.paths import app_locations

        monkeypatch.setenv("HOME", str(tmp_path / "sentinel"))
        assert app_locations().config_dir.is_relative_to(tmp_path / "sentinel")


# --- M-SPAWN ---------------------------------------------------------------------------------


def _spawn_session(tmp_path: Path) -> None:
    """P74: Ctrl+C to a parent's process group leaves the tool child alone; the child exits on
    its parent's death through its closed pipe (not raise_signal: a real os.killpg)."""
    marker = tmp_path / "child.txt"
    parent_code = f"""
        import subprocess, sys, time
        from clearwater.io.video.pipes import tool_spawn_kwargs
        child = subprocess.Popen(
            [sys.executable, "-c",
             "import sys; sys.stdin.read(); open({str(marker)!r}, 'w').write('eof')"],
            stdin=subprocess.PIPE, **tool_spawn_kwargs())
        print(child.pid, flush=True)
        time.sleep(60)
    """
    parent = subprocess.Popen(
        [sys.executable, "-c", textwrap.dedent(parent_code)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        text=True,
        env=_isolated_env(tmp_path),
        start_new_session=True,  # isolates the TEST's own process group from the SIGINT
    )
    try:
        assert parent.stdout is not None
        child = int(parent.stdout.readline())
        assert os.getsid(child) == child != os.getsid(parent.pid)  # its own session (AD-37)
        os.killpg(parent.pid, signal.SIGINT)
        parent.wait(timeout=30)
        deadline = time.monotonic() + 30
        while not (marker.exists() and marker.read_text() == "eof"):  # EOF, not SIGINT
            assert time.monotonic() < deadline, "the child outlived its parent"
            time.sleep(0.1)
    finally:
        if parent.poll() is None:
            parent.kill()
            parent.wait(timeout=30)


def _spawn_extensionless(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """X27: an extensionless executable on the PATH is found and run."""
    from clearwater.io.video import find_tool

    tools = tmp_path / "bin"
    tools.mkdir()
    stub = tools / "ffprobe"
    stub.write_text("#!/bin/sh\necho stub-ffprobe\n", encoding="ascii")
    stub.chmod(0o755)
    monkeypatch.setenv("PATH", str(tools) + os.pathsep + os.environ.get("PATH", ""))
    found = find_tool("ffprobe")
    assert found == stub and _run([str(found)]).stdout.strip() == "stub-ffprobe"


@pytest.mark.parametrize("site", ["P02", "P58", "P74", "X26", "X27"])
def test_macos_tool_and_worker_spawn(
    site: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """M-SPAWN: zero flags and a new session natively, FFREPORT stripped, no Windows DLL call."""
    from clearwater import gpu_pack
    from clearwater.io.video import pipes

    monkeypatch.setenv("FFREPORT", "file=leak.log")
    kwargs = pipes.tool_spawn_kwargs()
    assert (kwargs["creationflags"], kwargs["start_new_session"]) == (0, True)  # P02 / X26
    assert not any(key.upper() == "FFREPORT" for key in kwargs["env"])
    if site == "P58":
        assert not hasattr(os, "add_dll_directory") and gpu_pack.pack_root() is None
    if site == "P74":
        _spawn_session(tmp_path)
    if site == "X27":
        _spawn_extensionless(tmp_path, monkeypatch)
    child = subprocess.run(
        [sys.executable, "-c", "import os; print(os.getsid(0) == os.getpid())"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=TIMEOUT_S,
        **kwargs,  # type: ignore[arg-type]
    )
    assert child.stdout.strip() == "True"


# --- M-PIPE ----------------------------------------------------------------------------------

PIPE_FRAMES = 30
"""Frames in M-PIPE's one-second 30000/1001 clip."""

PIPE_STEP = Fraction(1001, 30000)
"""Seconds between two frames of that clip (it starts at 0, constant rate)."""


def _open_fds() -> int:
    return len(os.listdir("/dev/fd"))


def _file_decode(probe: Any, path: Path) -> bytes:
    """The product's own decode command with its raw output sent to a FILE instead of the pipe.

    The bytes the default pipe must carry, without a pipe in between (the reference of P04).
    """
    from clearwater.io.video import decode

    command = decode.decode_command(probe, ffmpeg=_ffmpeg(), cuda=False)
    assert command[-1] == "pipe:1", command
    done = _run([*command[:-1], "-y", f"file:{path}"])
    assert done.returncode == 0, done.stderr[-1000:]
    return path.read_bytes()


def _probe_pts(clip: Path) -> list[int]:
    """Each decoded frame's pts in stream ticks, read by ffprobe (no product code)."""
    data = _ffprobe_json(clip, "-select_streams", "v:0", "-show_entries", "frame=pts")
    return [int(frame["pts"]) for frame in data["frames"]]


def pipe_fidelity_failures(
    frames: Sequence[Any], reference: bytes, reference_pts: Sequence[int], video: Any
) -> list[str]:
    """Return what the frames read through the default pipe get wrong (empty when none).

    Args:
        frames: The product's frames, read through the pipe.
        reference: The same decode written to a file (:func:`_file_decode`).
        reference_pts: ffprobe's pts of each frame, in stream ticks.
        video: The probe's video stream (geometry and bit depth of the raw frames).

    Returns:
        One line per wrong count, frame payload or presentation time.
    """
    import numpy as np

    from clearwater.color import planes_to_rgb

    failures = []
    if len(frames) != PIPE_FRAMES or len(reference_pts) != PIPE_FRAMES:
        failures.append(f"count: {len(frames)} frames, {len(reference_pts)} pts, not 30")
    if not frames or len(reference) % len(frames):
        return [*failures, f"reference: {len(reference)} bytes for {len(frames)} frames"]
    size = len(reference) // len(frames)
    for i, frame in enumerate(frames):
        expected = planes_to_rgb(
            reference[i * size : (i + 1) * size],
            width=video.width,
            height=video.height,
            bit_depth=video.bit_depth,
        )
        if not np.array_equal(np.asarray(frame.pixels), expected):
            failures.append(f"frame {i}: the pixels differ from the file decode")
        if i < len(reference_pts) and frame.pts_ticks != reference_pts[i]:
            failures.append(f"frame {i}: pts_ticks {frame.pts_ticks} != {reference_pts[i]}")
        if frame.pts != i * PIPE_STEP:
            failures.append(f"frame {i}: pts {frame.pts} != {i * PIPE_STEP}")
    return failures


@pytest.mark.parametrize("site", ["P03", "P04", "T07", "T08", "X23", "X24"])
def test_macos_default_pipe_fidelity(
    site: str, caplog: pytest.LogCaptureFixture, tmp_path: Path
) -> None:
    """M-PIPE: the OS default pipe (Q2): no enlarged pipe, an INFO fallback; every frame of a
    real decode byte-identical to the same decode written to a file, at ffprobe's exact pts
    and the clip's exact constant step; no descriptor or child left after a cancelled one."""
    import fcntl
    import logging

    from clearwater.io.video import FFmpegVideoSource, pipes

    pipes._fallback_logged = False
    with caplog.at_level(logging.INFO):
        assert pipes.open_frame_pipe() is None  # P03 / X23: the default pipe on macOS
    assert [r.levelno for r in caplog.records if r.name == pipes._log.name] == [logging.INFO]
    assert getattr(fcntl, "F_SETPIPE_SZ", None) is None  # T08: no Linux pipe tuning here
    clip = _clip(tmp_path / "clip.mp4", seconds=1.0)
    reader = FFmpegVideoSource()
    probe = reader.probe(clip)
    if site in ("P04", "T07"):
        frames = list(reader.frames(probe, hw_decode=False))
        reference = _file_decode(probe, tmp_path / "reference.raw")
        assert pipe_fidelity_failures(frames, reference, _probe_pts(clip), probe.video) == []
    if site == "X24":
        before = _open_fds()
        stream = reader.frames(probe, hw_decode=False)
        next(stream)
        stream.close()  # type: ignore[attr-defined]
        assert _open_fds() <= before
        assert _run(["pgrep", "-P", str(os.getpid()), "ffmpeg"]).stdout.strip() == ""


# --- M-DEVICE --------------------------------------------------------------------------------


def _cpu_correct(tmp_path: Path) -> Any:
    return _python(
        """
        import json, importlib.util
        import numpy as np
        from clearwater.core import select_backend
        from clearwater.interfaces import Settings
        backend, reason = select_backend(Settings(), 2160, 3840, "c3")
        forced = select_backend(Settings(force_cpu=True), 2160, 3840, "c3")[1]
        print(json.dumps({"cupy": importlib.util.find_spec("cupy") is not None,
                          "backend": backend.name, "reason": reason, "forced": forced,
                          "free": backend.free_device_bytes()}))
        """,
        tmp_path,
    )


@pytest.mark.parametrize(
    "site", ["P05", "P18", "P19", "P20", "P21", "P22", "P23", "T42", "T43", "X44"]
)
def test_macos_cpu_without_cuda(site: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """M-DEVICE: a clean CPU-only environment (no CuPy installed, AD-36), the macOS AD-9 reason,
    force CPU, no device figure, and the Windows-side case natively. The Mac CPU output versus
    the Windows references within AD-11's tolerances is WP6.5's comparison (report limits)."""
    result = _cpu_correct(tmp_path / "child")
    assert result == {
        "cupy": False,
        "backend": "numpy",
        "reason": "CPU: graphics-card processing is not available on macOS",
        "forced": "CPU: forced",
        "free": None,
    }
    with pytest.MonkeyPatch.context() as w_patch:  # the W stubs end before the native half
        _w().DEVICE_CASES[site](w_patch, tmp_path)
    if site == "T42":
        argv = [
            sys.executable,
            str(REPO / "tools" / "device_hold.py"),
            "--mib",
            "1",
            "--stop-file",
            str(tmp_path / "stop"),
            "--timeout-s",
            "5",
        ]
        done = _run(argv, timeout=60)
        assert done.returncode != 0 and "cupy" in (done.stdout + done.stderr).casefold()
    if site == "X44":
        done = _run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                "-m",
                "not gpu",
                "--basetemp",
                str(tmp_path / "core"),
                str(REPO / "tests" / "test_core_backend.py"),
            ],
            timeout=900,
        )
        assert done.returncode == 0, done.stdout[-2000:]


# --- M-TEXT ----------------------------------------------------------------------------------


def _native_showinfo(tmp_path: Path) -> list[str]:
    done = _run(
        [
            str(_ffmpeg()),
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "level+info",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=64x64:rate=30000/1001:duration=0.2",
            "-vf",
            "showinfo",
            "-f",
            "null",
            "-",
        ]
    )
    assert done.returncode == 0, done.stderr[-1000:]
    return done.stderr.splitlines()


@pytest.mark.parametrize("site", ["P06", "P08", "P10", "P66", "P72", "T25", "X25", "X45"])
def test_macos_ffmpeg_text_and_redaction(
    site: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """M-TEXT: the pinned Mac build's real listing, showinfo and failure tails; native paths."""
    from clearwater.io.video import capability, decode

    if site == "P06":
        lines = _native_showinfo(tmp_path)
        assert any(decode._SHOWINFO_CONFIG.match(line) for line in lines)
        assert len([line for line in lines if decode._SHOWINFO_FRAME.match(line)]) >= 5
    elif site == "P08":
        names, error = capability._listed(_ffmpeg())
        assert error is None and X265 in names  # VT listed or not, the parse reads the build
    elif site == "P10":
        for row in _native_capabilities():
            assert (row.reason or "").isascii() and "NVIDIA" not in (row.reason or "")
    elif site == "P72":
        plain = _clip(tmp_path / "plain.mp4", seconds=0.2)
        rotated = _remux(plain, tmp_path / "rotated.mp4", input_options=["-display_rotation", "90"])
        from clearwater.io.video import probe

        assert probe(rotated).video.rotation in (90, 270)
    elif site == "T25":
        he = importlib.import_module("headless_export")
        folder = tmp_path / unicodedata.normalize("NFD", "caf\u00e9 dives")
        folder.mkdir()
        real = folder.resolve()  # /private/var/... on macOS
        text = f"{real}/GX01.MP4 failed; {folder}/GX01.MP4"
        redacted = he.Redactor([folder])(text)
        assert str(real) not in redacted and str(folder) not in redacted
    else:
        with pytest.MonkeyPatch.context() as w_patch:  # the W stubs end before the native half
            _w().TEXT_CASES[site](w_patch, tmp_path)
        if site == "X45":
            support = importlib.import_module("acceptance_support")
            with pytest.raises(AssertionError):
                support.assert_names_only(f"wrote {tmp_path.resolve()}/x.mp4")


# --- M-CODEC ---------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "site", ["P07", "P09", "P11", "P14", "P55", "P62", "T33", "T34", "T35", "T37", "T44", "X43"]
)
def test_macos_videotoolbox_capabilities(
    site: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """M-CODEC: the real VT / x265 trials (8 / 10-bit), the auto rule and explicit choices; a
    proved unavailable VT keeps the x265 fallback."""
    from clearwater.io.video import capability
    from clearwater.io.video.encode import FFmpegVideoSink, VideoEncodeError

    rows = _native_capabilities()
    assert tuple(r.name for r in rows) == (VT, X265) == capability.ENCODERS  # P07 / X43
    vt, x265 = rows
    assert x265.available and x265.bit_depths == (8, 10)  # T44: x265 everywhere
    assert vt.hw
    if vt.available:
        assert_advertised(vt)
        assert_unadvertised_refused(vt)
    else:
        assert_proved_unavailable(vt)  # T44: a reason, no depth, before the x265 fallback
    auto = capability.resolve_encoder("auto", rows)
    assert auto == (VT if vt.available else X265)  # P11
    sink = FFmpegVideoSink()
    with pytest.raises(VideoEncodeError) as caught:  # P62: a saved NVENC choice on a Mac
        sink._check_options("hevc_nvenc", "standard", 8)
    assert caught.value.kind == "unavailable"
    if site in ("P09", "P14"):
        _vt_or_skip()
        for depth in vt.bit_depths:
            argv = capability.trial_encode_command(_ffmpeg(), VT, depth)
            assert argv[argv.index("-allow_sw") + 1] == "0"
            assert _run(argv).returncode == 0
        clip = _clip(tmp_path / "in.mp4", seconds=0.5)
        for depth in vt.bit_depths:  # the ADVERTISED depths only (A r2 item 5)
            _probe, report = _encode(
                clip, tmp_path / f"out-{depth}.mp4", encoder=VT, quality="standard", bit_depth=depth
            )
            assert report.frames_written == 15
    elif site in ("P55", "T33", "T34", "T35", "T37"):
        with pytest.MonkeyPatch.context() as w_patch:  # the W stubs end before the native half
            _w().CODEC_CASES[site](w_patch, tmp_path)


# --- M-RATE ----------------------------------------------------------------------------------


def _bitrate(path: Path) -> float:
    data = _ffprobe_json(path, "-show_entries", "format=bit_rate,duration")
    return float(data["format"]["bit_rate"])


@pytest.mark.parametrize("site", ["P12", "P13", "P59", "P60", "P61"])
def test_macos_videotoolbox_quality_controls(
    site: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """M-RATE: both Q1 candidates on a busy and a calm SDR clip: the output's rate stays under
    the ceiling R, the profile follows the depth; the figures are recorded for WP6.5's
    EXCLUSIVE measurement (this test bounds them, it does not choose a candidate)."""
    from clearwater.io.video import encode

    vt = _vt_or_skip()
    assert_unadvertised_refused(vt)
    figures = {}
    for label, source in (("busy", "testsrc2"), ("calm", "color=c=0x204060")):
        clip = _clip(tmp_path / f"{label}.mp4", seconds=2.0, source=source)
        for candidate in ("A", "B"):
            monkeypatch.setattr(encode, "VT_RATE_CONTROL", candidate)
            for depth in vt.bit_depths:  # the ADVERTISED depths only (A r2 item 5)
                out = tmp_path / f"{label}-{candidate}-{depth}.mp4"
                probe, report = _encode(clip, out, encoder=VT, quality="draft", bit_depth=depth)
                ceiling = encode.rate_ceiling(
                    probe.video.width, probe.video.height, probe.video.frame_rate, "draft", None
                ).bits_per_second
                rate = _bitrate(out)
                stream = _ffprobe_json(
                    out, "-select_streams", "v:0", "-show_entries", "stream=profile"
                )
                assert stream["streams"][0]["profile"] == ("Main 10" if depth == 10 else "Main")
                assert rate <= ceiling * 1.10, (label, candidate, depth, rate, ceiling)
                figures[label, candidate, depth] = (rate, ceiling, report.frames_written)
    (tmp_path / "figures.json").write_text(json.dumps({str(k): v for k, v in figures.items()}))


# --- M-V4 ------------------------------------------------------------------------------------

V4_SAMPLES = {
    "vid-hevc8-bt709-full": 8,
    "vid-hevc10": 10,
    "vid-untagged": 8,
    "vid-truncated": 8,
    "vid-vfr": 8,
    "vid-rotated": 8,
    "vid-pcm-irregular": 8,
}
"""The WP2.3 samples (``tools/fixtures/video.py``) the Windows V4 test encodes, with each one's
source depth (``test_io_video_encode.DECODABLE``): VFR ticks and durations, a display-matrix
rotation, 10-bit, untagged (D54), truncated (D86), irregular PCM audio; AAC on the others."""

V4_CLIPS: dict[str, dict[str, Any]] = {
    "offset": {},
    "bf-x264-offset": {"codec": "libx264", "bframes": True},
    "bf-x265-offset": {"codec": "libx265", "bframes": True},
    "bf-x264-ntsc": {"codec": "libx264", "bframes": True, "offset": "0", "rate": "30000/1001"},
    "vfr-gap": {"vf_chain": "select='not(between(n,10,14))'"},
}
"""The synthetic sources the Windows V4 tests build with ``test_io_video_encode.Clips``: a start
offset with an empty edit, B-frame composition offsets (AD-22), a variable-rate gap; 8-bit."""

V4_EXACT_ITEMS = (
    "video per-frame pts (presentation, exact, full sequence)",
    "start offset: first video frame pts",
    "video stream duration",
)
"""The timing items the Windows B-frame test requires SAME (with the instrument's edit effect)."""


def _v4_cases() -> list[Any]:
    sources = [(f"sample:{k}", d) for k, d in V4_SAMPLES.items()]
    sources += [(f"clip:{k}", 8) for k in V4_CLIPS]
    return [
        pytest.param(
            source,
            encoder,
            out,
            id=f"{source}-{encoder}-{out}",
        )
        for source, depth in sources
        for encoder in (VT, X265)
        for out in sorted({depth, 10})
    ]


def _timing_boxes(path: Path) -> dict[str, Any]:
    """Read raw video timing using product walkers; parse only the missing header durations.

    ``read_movie_boxes`` supplies timescales and raw edits. ``verify`` supplies the moov,
    bounded child walk and table reader. The product has no mvhd/mdhd/tkhd duration reader;
    the small read-only parser here handles their version-0/1 payloads. ctts version 0 is
    UNSIGNED (unlike version 1); retain that distinction rather than normalising offsets.
    """
    from clearwater.io.video import verify
    from clearwater.io.video.boxes import BoxError, read_movie_boxes

    boxes = read_movie_boxes(path)
    moov = verify._moov(path)
    if moov is None:
        raise BoxError("timing evidence: no moov")
    media = verify._video_media(moov)
    if media is None:
        raise BoxError("timing evidence: no video track")
    track = next(
        (start, end)
        for kind, start, end in verify._boxes(moov, 0, len(moov))
        if kind == b"trak" and verify._child(moov, (start, end), b"mdia") == media
    )
    minf = verify._child(moov, media, b"minf")
    stbl = verify._child(moov, minf, b"stbl") if minf else None
    stts = verify._child(moov, stbl, b"stts") if stbl else None
    entries = list(verify._table_entries(moov, stts, ">II")) if stts else []
    ctts = verify._child(moov, stbl, b"ctts") if stbl else None
    ctts_version = moov[ctts[0]] if ctts and ctts[1] > ctts[0] else None
    if ctts is not None and ctts_version not in (0, 1):
        raise BoxError("timing evidence: ctts of unknown version")
    offsets = (
        list(verify._table_entries(moov, ctts, ">Ii" if ctts_version == 1 else ">II"))
        if ctts
        else []
    )
    stsz = verify._child(moov, stbl, b"stsz") if stbl else None
    if stsz is not None and stsz[1] - stsz[0] < 12:
        raise BoxError("timing evidence: stsz too short")
    sample_count = struct.unpack_from(">I", moov, stsz[0] + 8)[0] if stsz else None
    edts = verify._child(moov, track, b"edts")
    elst = verify._child(moov, edts, b"elst") if edts else None

    def duration(span: tuple[int, int] | None, *, track_header: bool = False) -> Any:
        if span is None:
            return None
        start, end = span
        if end - start < 4 or moov[start] not in (0, 1):
            raise BoxError("timing evidence: duration header too short or of unknown version")
        version = moov[start]
        # FullBox + creation/modification + (track ID/reserved OR timescale).
        offset = start + 4 + (16 if version else 8) + (8 if track_header else 4)
        size = 8 if version else 4
        if offset + size > end:
            raise BoxError("timing evidence: duration past the end of its header")
        return {
            "version": version,
            "ticks": struct.unpack_from(">Q" if version else ">I", moov, offset)[0],
        }

    return {
        "movie_timescale": boxes.movie_timescale,
        "media_timescale": boxes.video_timescale,
        "elst_version": moov[elst[0]] if elst else None,
        "elst": [
            {
                "segment_duration": e.segment_duration,
                "media_time": e.media_time,
                "rate": str(e.media_rate),
            }
            for e in boxes.edits
        ],
        "durations": {
            "mvhd": duration(verify._child(moov, (0, len(moov)), b"mvhd")),
            "mdhd": duration(verify._child(moov, media, b"mdhd")),
            "tkhd": duration(verify._child(moov, track, b"tkhd"), track_header=True),
        },
        "stts": entries,
        "ctts": {"version": ctts_version, "entries": offsets},
        "sample_count": sum(count for count, _ in entries),
        "stsz_sample_count": sample_count,
    }


def _packet_timing(path: Path) -> tuple[list[tuple[int, int, int]], Fraction]:
    """Read VIDEO packets only, retaining their source clock and positive durations."""
    from clearwater.io.video import find_tool

    done = _run([
        str(find_tool("ffprobe")), "-v", "error", "-select_streams", "v:0",
        "-show_entries", "packet=pts,dts,duration:stream=time_base", "-of", "json", str(path),
    ])  # fmt: skip
    assert done.returncode == 0, done.stderr
    data = json.loads(done.stdout)
    return (
        [(int(p["pts"]), int(p["dts"]), int(p["duration"])) for p in data["packets"]],
        Fraction(data["streams"][0]["time_base"]),
    )


def _expected_timing(packets: Sequence[tuple[int, int, int]], tb: Fraction) -> dict[str, Any]:
    """Derive the presentation span from a source packet table, never its average rate."""
    ordered = sorted(packets)
    assert ordered and tb > 0
    assert all(duration > 0 for _, _, duration in ordered), "nonpositive source duration"
    pts = [p for p, _, _ in ordered]
    assert len(set(pts)) == len(pts), "duplicate source PTS"
    first = pts[0] * tb
    end = max((p + duration) * tb for p, _, duration in ordered)
    return {"pts": [p * tb for p in pts], "first": first, "end": end, "span": end - first}


def _assert_timing_span(
    raw: dict[str, Any], expected: dict[str, Any], *, reordered: bool = False
) -> None:
    """Check totals and edit effects, allowing x265's reordered stts/ctts run shapes."""
    media, movie = raw["media_timescale"], raw["movie_timescale"]
    decode_ticks = sum(n * delta for n, delta in raw["stts"])
    if not reordered:
        assert decode_ticks == expected["span"] * media
    assert raw["sample_count"] == raw["stsz_sample_count"] == len(expected["pts"])
    for header, ticks in (
        ("mdhd", decode_ticks),
        ("tkhd", expected["end"] * movie),
        ("mvhd", expected["end"] * movie),
    ):
        assert raw["durations"][header]["ticks"] == ticks, header
    edits = []
    if expected["first"]:
        edits.append({"segment_duration": expected["first"] * movie, "media_time": -1, "rate": "1"})
    edits.append({"segment_duration": expected["span"] * movie, "media_time": 0, "rate": "1"})
    assert raw["elst"] == edits


def _assert_vt_vfr_timing(
    source_id: str,
    raw: dict[str, Any],
    pts: Sequence[int],
    tb: Fraction,
    evidence: str,
) -> None:
    """Pin the four DR-163 outputs, including the last VIDEO sample from raw stts."""
    if source_id == "sample:vid-vfr":
        entries = [(2, 1001), (1, 2002)] * 10
        wanted_pts = [1001 * (4 * (n // 3) + n % 3) for n in range(30)]
        first, end, media, movie = 0, 40040, 30000, 240000
        last = (38038, 38038, 2002)
    else:
        assert source_id == "clip:vfr-gap"
        entries = [(9, 512), (1, 3072), (45, 512)]
        wanted_pts = [7680 + n * 512 for n in range(60) if n not in range(10, 15)]
        first, end, media, movie = 7680, 38400, 15360, 384000
        last = (37888, 37888, 512)
    assert (raw["media_timescale"], raw["movie_timescale"]) == (media, movie)
    assert tb == Fraction(1, media)
    assert raw["stts"] == entries, "DR-163: raw video stts differs from source durations"
    assert raw["ctts"] == {"version": None, "entries": []}
    assert sorted(pts) == wanted_pts
    written = re.findall(r"^written pts: (.*)$", evidence, re.MULTILINE)
    assert len(written) == 1 and json.loads(written[0]) == wanted_pts
    assert re.findall(r"^sentinel pts: (.*)$", evidence, re.MULTILINE) == [str(end)]
    assert evidence.splitlines()[0] == "error: verification passed"
    deltas = [delta for count, delta in raw["stts"] for _ in range(count)]
    # No ctts: raw decode and presentation times coincide; do not read an audio tail line.
    last_dts = first + sum(deltas[:-1])
    assert (last_dts, last_dts, deltas[-1]) == last
    _assert_timing_span(
        raw,
        {
            "pts": wanted_pts,
            "first": Fraction(first, media),
            "end": Fraction(end, media),
            "span": Fraction(end - first, media),
        },
    )


def _encoder_packets(log: str) -> list[tuple[int, int, bool]]:
    """Parse debug_ts at the encoder boundary; benchmark action identifies flush receives.

    FFmpeg b204e94e fftools/ffmpeg_enc.c:612,654-658,704-710 logs pkt->duration
    after receive_packet and BEFORE sch_enc_send (:718). The benchmark's encode/flush
    action is printed at :657 (ffmpeg.c:551-565). libavformat/mux.c:1102 calls
    guess_pkt_duration later. stats_enc_post has no duration field in this revision.
    """
    packets = []
    flushing = None
    for line in log.splitlines():
        action = re.search(r"bench:.*\b(encode|flush)_video 0\.0\b", line)
        if action:
            flushing = action[1] == "flush"
        if "encoder -> type:video " in line:
            packet = re.search(r"pkt_pts:(-?\d+)\b.*?\bduration:(\d+)\b", line)
            assert packet is not None, f"malformed encoder packet: {line}"
            assert flushing is not None, "encoder packet without receive action"
            packets.append((int(packet[1]), int(packet[2]), flushing))
    assert packets, "no encoder-boundary video packets"
    return packets


def _assert_encoder_durations(log: str, expected: Sequence[tuple[int, int]]) -> None:
    """Require exact positive durations associated by PTS, including delayed flush output."""
    packets = _encoder_packets(log)
    actual = sorted((pts, duration) for pts, duration, _ in packets)
    assert actual == sorted(expected), (
        f"DR-163 encoder boundary: expected {sorted(expected)}; got {actual}"
    )
    assert any(flushed for _, _, flushed in packets), "DR-163: no packet observed during flush"


def _write_vt_failure(
    output: Path,
    destination: Path,
    *,
    first: int,
    end: int,
    time_base: Fraction,
    error: str,
    source: Path | None = None,
    recipe: str | None = None,
    written_pts: Sequence[int] = (),
    frame_rate: Fraction | None = None,
    encode_argv: Sequence[str] = (),
) -> None:
    """Record finished output (VT success/refusal or x265 control) before any sink cleanup.

    The watched synthetic clips are small. Keep a named truncation diagnostic if unexpected
    metadata exceeds the 192 KiB evidence budget; neither a huge tag nor an external reader
    error should hide the original encode refusal. ``end`` is the sentinel actually sent by
    ``_end_stream``; ``written_pts`` excludes that sentinel, as the sink's own list does.
    """
    from clearwater.io.video import find_tool
    from clearwater.io.video.boxes import read_movie_boxes

    destination.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"error: {error}",
        f"written first: {first}; end: {end}; time_base: {time_base}",
        f"written first seconds: {first * time_base}; end seconds: {end * time_base}",
    ]
    if source is not None:
        lines += [
            "written pts: " + json.dumps(list(written_pts)),
            f"sentinel pts: {end}",
            f"source probe.video.frame_rate: {frame_rate}",
            "encode argv: " + json.dumps(list(encode_argv)),
        ]
        try:
            with source.open("rb") as handle:
                digest = hashlib.file_digest(handle, "sha256").hexdigest()
            lines.append(
                "source identity: "
                + json.dumps(
                    {
                        "path": str(source),
                        "sha256": digest,
                        "size_bytes": source.stat().st_size,
                        "recipe": recipe,
                    }
                )
            )
        except Exception as diagnostic_error:
            lines.append(
                f"source identity failed: {type(diagnostic_error).__name__}: {diagnostic_error}"
            )
    # Leave a named diagnostic even if a reader fails; never hide the encode refusal.
    paths = [("output", output)] + ([("source", source)] if source is not None else [])
    for label, path in paths:
        lines.append(f"{label} ffprobe (format, streams, packets):")
        try:
            done = _run(
                [
                    str(find_tool("ffprobe")),
                    "-v",
                    "error",
                    "-show_entries",
                    "format:stream:packet=pts,dts,duration,flags",
                    "-of",
                    "compact",
                    str(path),
                ]
            )
            lines.extend([f"ffprobe returncode: {done.returncode}", done.stdout, done.stderr])
        except Exception as diagnostic_error:
            lines.append(
                f"{label} ffprobe failed: {type(diagnostic_error).__name__}: {diagnostic_error}"
            )
        try:
            lines.append(f"{label} read_movie_boxes: {read_movie_boxes(path)!r}")
            raw = _timing_boxes(path)
            lines.append(f"{label} boxes: " + json.dumps(raw))
            entries = raw["stts"]
            lines.append(f"last stts (count, delta): {entries[-1] if entries else None}")
        except Exception as diagnostic_error:
            lines.append(
                f"{label} evidence read failed: "
                f"{type(diagnostic_error).__name__}: {diagnostic_error}"
            )
    data = ("\n".join(lines) + "\n").encode("utf-8")
    limit = 192 * 1024
    if len(data) > limit:
        marker = b"\n# EVIDENCE TRUNCATED: exceeded 192 KiB budget\n"
        data = data[: limit - len(marker)].decode("utf-8", errors="ignore").encode("utf-8") + marker
    destination.write_bytes(data)


def _capture_vt_failure(
    monkeypatch: pytest.MonkeyPatch,
    case_id: str,
    root: Path,
    *,
    source: Path | None = None,
    recipe: str | None = None,
) -> None:
    """Capture verification failures AND successful VT/x265 VFR cases before cleanup.

    Observe ``_start``'s final argv without altering it. The original verification result or
    exception is preserved; diagnostic failures add a note to the original encode exception
    or warn after successful verification.
    No encoder argv/logging option changes, packet tracing or product edits are involved.
    """
    from clearwater.io.video import FFmpegVideoSink, VideoEncodeError

    original = FFmpegVideoSink._verify
    safe_id = re.sub(r"[^A-Za-z0-9_.-]", "_", case_id)
    commands: dict[int, list[str]] = {}
    if source is not None:
        start = FFmpegVideoSink._start

        def record_start(sink: Any, command: list[str]) -> Any:
            commands[id(sink)] = list(command)
            return start(sink, command)

        monkeypatch.setattr(FFmpegVideoSink, "_start", record_start)

    def capture(sink: Any, end: int, error: str) -> None:
        extra = (
            {}
            if source is None
            else {
                "source": source,
                "recipe": recipe,
                "written_pts": tuple(sink._written),
                "frame_rate": sink._probe.video.frame_rate,
                "encode_argv": commands.get(id(sink), ()),
            }
        )
        _write_vt_failure(
            sink._out_path,
            root / f"f8-3-{safe_id}.txt",
            first=min(sink._written),
            end=end,
            time_base=sink._probe.video.time_base,
            error=error,
            **extra,
        )

    def verify(sink: Any, end: int) -> Any:
        try:
            result = original(sink, end)
        except VideoEncodeError as error:
            try:
                capture(sink, end, str(error))
            except Exception as diagnostic_error:
                error.add_note(f"DR-163 evidence capture failed: {diagnostic_error!r}")
            raise
        if source is not None:
            try:
                capture(sink, end, "verification passed")
            except Exception as diagnostic_error:
                warnings.warn(
                    f"DR-163 evidence capture failed for {case_id}: {diagnostic_error!r}",
                    stacklevel=2,
                )
        return result

    monkeypatch.setattr(FFmpegVideoSink, "_verify", verify)


def _v4_clips(tmp_path_factory: pytest.TempPathFactory) -> Any:
    """The Windows V4 tests' clip builder, on one folder per session."""
    folder = tmp_path_factory.getbasetemp() / "m-v4-clips"
    folder.mkdir(exist_ok=True)
    return importlib.import_module("test_io_video_encode").Clips(folder)


def _v4_source(source_id: str, sample: Any, tmp_path_factory: pytest.TempPathFactory) -> Path:
    kind, name = source_id.split(":", 1)
    if kind == "sample":
        path: Path = sample(name)
        return path
    built: Path = _v4_clips(tmp_path_factory).make(name, **V4_CLIPS[name])
    return built


def v4_failures(
    source_id: str, record: dict[str, Any], frames_written: int, warnings: Sequence[str]
) -> list[str]:
    """Return what the V4 record of one corpus encode gets wrong (empty when it passes).

    The full instrument's verdict (every mandatory and required item SAME, the roster whole),
    the frame count, and the per-source checks the Windows V4 tests make on the same source.
    """
    vf = importlib.import_module("video_fidelity")
    items = {item["name"]: item for item in record["items"]}
    summary = record["summary"]
    failures = []
    if not summary["mandatory_and_required_all_same"]:
        failures.append(f"V4: {summary['different_items']}")
    if items.get(vf._ROSTER_ITEM, {}).get("status") != "SAME":
        failures.append("V4: the item roster is not whole")
    if items.get("video frame count", {}).get("output") != frames_written:
        failures.append("V4: the frame count differs from the frames written")
    exact: tuple[str, ...] = ()
    if source_id.startswith("clip:bf-"):  # as test_bframe_sources_by_presentation_effect
        exact = (*V4_EXACT_ITEMS, vf.EDIT_EFFECT)
    elif source_id in ("sample:vid-vfr", "clip:vfr-gap"):  # as test_vfr_pts_are_exact
        exact = V4_EXACT_ITEMS[:1]
    for name in exact:
        if items.get(name, {}).get("status") != "SAME":
            failures.append(f"V4: {name} is not SAME")
    if source_id.startswith("clip:bf-"):
        written = items.get(vf.VIDEO_EDIT_AS_WRITTEN, {})
        if written.get("source") != written.get("output"):  # media_time differs: AD-22 says so
            note = str(written.get("note", ""))
            if not note.startswith("AD-22") or note not in summary["notes"]:
                failures.append("AD-22: a changed edit list without its note")
    if source_id == "sample:vid-truncated":
        if not any("cut short" in w for w in warnings):
            failures.append("D86: no cut-short warning")
        if not any(str(n).startswith("D86") for n in summary["notes"]):
            failures.append("D86: no D86 note")
    return failures


@pytest.mark.parametrize(("source_id", "encoder", "depth"), _v4_cases())
def test_macos_videotoolbox_v4_corpus(
    source_id: str,
    encoder: str,
    depth: int,
    sample: Any,
    tmp_path: Path,
    tmp_path_factory: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """M-V4 (P15) over the Windows V4 corpus: each source through the product sink with each
    encoder at each depth it ADVERTISES, judged by the full instrument
    (``video_fidelity.fidelity_record``); an unadvertised depth is a refusal, never an encode."""
    from clearwater.io.video import probe
    from clearwater.io.video.verify import read_packet_table

    vf = importlib.import_module("video_fidelity")
    row = _capability(encoder)
    if encoder == X265:
        assert row.available and row.bit_depths == (8, 10)  # both x265 depths, always
    elif not row.available:
        assert_proved_unavailable(row)
        pytest.skip(f"VideoToolbox unavailable on this Mac: {row.reason}")
    assert_advertised(row)
    if depth not in row.bit_depths:
        assert_unadvertised_refused(row)
        return
    source = _v4_source(source_id, sample, tmp_path_factory)
    out = tmp_path / "out.mp4"
    if source_id in {"sample:vid-vfr", "clip:vfr-gap"}:
        recipe = (
            f"{source_id} (tools/fixtures/video.py)"
            if source_id.startswith("sample:")
            else f"{source_id} (test_io_video_encode.Clips.make; kwargs={V4_CLIPS['vfr-gap']!r})"
        )
        _capture_vt_failure(
            monkeypatch,
            f"{source_id}-{encoder}-{depth}",
            REPO / "work/evidence",
            source=source,
            recipe=recipe,
        )
    run = vf.encode_file(source, out, encoder=encoder, bit_depth=depth)
    record = vf.fidelity_record(source, out, bit_depth=depth, run=run)
    assert record["bit_depth"] == depth
    assert v4_failures(source_id, record, run.report.frames_written, run.report.warnings) == []
    assert probe(out).video.bit_depth == depth
    if source_id in ("sample:vid-vfr", "clip:vfr-gap"):
        assert probe(source).video.vfr
        assert sorted(read_packet_table(out).video_pts) == sorted(
            read_packet_table(source).video_pts
        )
        if encoder == VT:
            evidence = (
                REPO
                / "work/evidence"
                / (f"f8-3-{source_id.replace(':', '_')}-{encoder}-{depth}.txt")
            )
            _assert_vt_vfr_timing(
                source_id,
                _timing_boxes(out),
                read_packet_table(out).video_pts,
                probe(out).video.time_base,
                evidence.read_text(encoding="utf-8"),
            )
    if source_id == "sample:vid-rotated":
        assert probe(out).video.rotation == 90
    if source_id == "clip:offset":
        assert probe(out).edit_list == probe(source).edit_list


def _duration_source(name: str, tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build regressions test-side with Clips.make's output BSF escape hatch."""
    options: dict[str, Any] = {"offset": "0", "duration": "0.2", "size": "64x48"}
    if name == "regular-final":
        # Regular PTS (0..29)/30, but the final packet lasts FOUR periods.
        options["duration"] = "1"
        options["out_options"] = ("-bsf:v", r"setts=duration=if(eq(N\,29)\,4\,DURATION)")
    else:
        assert name == "early-long"
        # (0,100,101,102,103,104)/30. An average substituted at the penultimate
        # packet exceeds the true end 105/30 even if the last duration is repaired.
        options["vf_chain"] = r"setpts=if(eq(N\,0)\,0\,N+99)"
    return _v4_clips(tmp_path_factory).make(f"dr163-{name}", **options)


DR164_REASON = "DR-164: libx265 reordered output loses a long final frame duration"


class _DR164DurationMismatchError(AssertionError):
    """The watched V4 duration mismatch, after all other timing checks have passed."""


def _duration_cases() -> list[Any]:
    """Keep only the two DR-164 controls xfailed; all VT and early-long rows are ordinary."""
    return [
        pytest.param(
            name, encoder, depth, id=f"{depth}-{encoder}-{name}",
            marks=pytest.mark.xfail(
                strict=True, reason=DR164_REASON, raises=_DR164DurationMismatchError
            ) if name == "regular-final" and encoder == X265 else (),
        )
        for depth in (8, 10)
        for encoder in (VT, X265)
        for name in ("regular-final", "early-long")
    ]  # fmt: skip


def _assert_duration_v4(record: dict[str, Any], failures: Sequence[str], *, watched: bool) -> None:
    """Permit the DR-164 exception only for the sole mandatory/required duration failure."""
    if not failures:
        return
    blocking = [
        item["name"]
        for item in record["items"]
        if item["status"] == "DIFFERENT"
        and (item["class"] == "MANDATORY" or item["class"].startswith("REQUIRED"))
    ]
    if watched and blocking == ["video stream duration"] and len(failures) == 1:
        assert failures[0].startswith("V4: "), failures
        assert "video stream duration" in failures[0], failures
        item = next(i for i in record["items"] if i["name"] == "video stream duration")
        raise _DR164DurationMismatchError(
            f"DR-164: V4 video stream duration differs: source={item['source']}; "
            f"output={item['output']}"
        )
    assert not failures, failures


@pytest.mark.parametrize(("name", "encoder", "depth"), _duration_cases())
def test_macos_duration_regression(
    name: str,
    encoder: str,
    depth: int,
    tmp_path: Path,
    tmp_path_factory: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Preserve source-derived timing for unusual final and long-early/short-tail spans."""
    vf = importlib.import_module("video_fidelity")
    row = _capability(encoder)
    if encoder == X265:
        assert row.available and row.bit_depths == (8, 10)
    elif not row.available:
        assert_proved_unavailable(row)
        pytest.skip(f"VideoToolbox unavailable on this Mac: {row.reason}")
    assert_advertised(row)
    if depth not in row.bit_depths:
        assert_unadvertised_refused(row)
        return
    source = _duration_source(name, tmp_path_factory)
    packets, tb = _packet_timing(source)
    expected = _expected_timing(packets, tb)
    ordered = sorted(packets)
    steps = [b[0] - a[0] for a, b in pairwise(ordered)]
    if name == "regular-final":
        assert len(ordered) == 30
        assert len(set(steps)) == 1 and ordered[-1][2] != steps[-1]
    else:
        assert len(ordered) == 6
        assert steps[0] > sum(steps[1:]) and len(set(steps[1:])) == 1
        average = expected["span"] / len(ordered)
        assert ordered[-2][0] * tb + average > expected["end"]
    out = tmp_path / "duration.mp4"
    case_id = f"clip:{name}-{encoder}-{depth}"
    _capture_vt_failure(
        monkeypatch,
        case_id,
        REPO / "work/evidence",
        source=source,
        recipe=f"test-side _duration_source({name!r}); Clips.make output BSF / setpts",
    )
    run = vf.encode_file(source, out, encoder=encoder, bit_depth=depth)
    record = vf.fidelity_record(source, out, bit_depth=depth, run=run)
    failures = v4_failures("clip:" + name, record, run.report.frames_written, run.report.warnings)
    evidence = REPO / "work/evidence" / f"f8-3-clip_{name}-{encoder}-{depth}.txt"
    # Require the verify hook's file; opening in append mode must not create a missing one.
    captured = evidence.read_bytes()
    evidence.write_bytes(
        captured
        + (
            "V4 failures: " + json.dumps(failures) + "\nV4 record: " + json.dumps(record) + "\n"
        ).encode("utf-8")
    )
    assert record["bit_depth"] == depth
    output_packets, output_tb = _packet_timing(out)
    assert _expected_timing(output_packets, output_tb)["pts"] == expected["pts"]
    raw = _timing_boxes(out)
    _assert_timing_span(raw, expected, reordered=encoder == X265)
    if encoder == VT:
        assert raw["ctts"] == {"version": None, "entries": []}
        deltas = [d for n, d in raw["stts"] for _ in range(n)]
        assert [d * Fraction(1, raw["media_timescale"]) for d in deltas] == [
            d * tb for _, _, d in ordered
        ]
    _assert_duration_v4(record, failures, watched=name == "regular-final" and encoder == X265)


@pytest.mark.parametrize("depth", [8, 10])
def test_macos_vt_encoder_boundary_durations(depth: int, tmp_path: Path) -> None:
    """Unequal frame durations must reach the VT packets before mux guessing, flush included."""
    from clearwater.io.video import nut

    row = _capability(VT)
    if not row.available:
        assert_proved_unavailable(row)
        pytest.skip(f"VideoToolbox unavailable on this Mac: {row.reason}")
    assert_advertised(row)
    if depth not in row.bit_depths:
        assert_unadvertised_refused(row)
        return
    source = tmp_path / "unequal.nut"
    # A timestamped input and terminal sentinel, using the same input BSF as the sink.
    # This is a DIRECT test invocation, never an intercepted/modified product command.
    expected = [(0, 2), (2, 5), (7, 1), (8, 4)]
    payload = bytes(64 * 48 * 3 * (2 if depth == 10 else 1))
    with source.open("wb") as handle:
        handle.write(
            nut.stream_header(
                width=64,
                height=48,
                bit_depth=depth,
                time_base=Fraction(1, 30),
                frame_rate=Fraction(10),
            )
        )
        for pts, _ in expected:
            handle.write(nut.frame_header(pts, len(payload)))
            handle.write(payload)
        handle.write(nut.sentinel(12))
    command = [
        str(_ffmpeg()),
        "-nostdin",
        "-hide_banner",
        "-nostats",
        "-loglevel",
        "verbose",
        "-debug_ts",
        "-benchmark_all",
        "-y",
        "-bsf:v",
        nut.INPUT_BITSTREAM_FILTER,
        "-f",
        "nut",
        "-i",
        str(source),
        "-map",
        "0:v:0",
        "-an",
        "-vf",
        "format=" + ("p010le" if depth == 10 else "nv12"),
        "-c:v",
        VT,
        "-allow_sw",
        "1",
        "-realtime",
        "0",
        "-bf",
        "2",
        "-b:v",
        "1M",
        "-fps_mode",
        "passthrough",
        "-enc_time_base:v",
        "demux",
        "-f",
        "null",
        "-",
    ]
    done = _run(command)
    evidence = REPO / "work/evidence" / f"dr163-encoder-boundary-{depth}.txt"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(json.dumps(command) + "\n" + done.stderr, encoding="utf-8")
    assert done.returncode == 0, done.stderr[-4000:]
    _assert_encoder_durations(done.stderr, expected)


def _negative_timestamps_refused(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """The Windows V4 test's negative-timestamp source (no edit list, every pts shifted below
    zero, as legal ISO allows) is refused at open by name for each available encoder, before
    FFmpeg starts and with nothing written."""
    from dataclasses import replace

    from clearwater.io.video import FFmpegVideoSink, VideoEncodeError, probe
    from clearwater.io.video import encode as encode_module
    from clearwater.io.video.verify import read_packet_table

    source = _v4_clips(tmp_path_factory).make(
        "noedit-False", codec="libx264", bframes=False, offset="0",
        out_options=("-use_editlist", "0"),
    )  # fmt: skip
    table = read_packet_table(source)
    planted = replace(table, video_pts=tuple(p - 1024 for p in table.video_pts))
    monkeypatch.setattr(
        encode_module, "read_packet_table", lambda p, **k: planted if p == source else None
    )

    def refuse(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("FFmpeg must not start for a refused open")

    monkeypatch.setattr(FFmpegVideoSink, "_start", refuse)
    for row in _native_capabilities():
        if not row.available:
            continue
        out = tmp_path / f"negative-{row.name}.mp4"
        out.write_bytes(b"")
        with pytest.raises(VideoEncodeError) as caught:
            FFmpegVideoSink().open(
                probe(source), out, encoder=row.name, quality="standard",
                bit_depth=row.bit_depths[0], provenance=None,
            )  # fmt: skip
        assert caught.value.kind == "refused" and "negative timestamps" in str(caught.value)
        assert out.stat().st_size == 0


@pytest.mark.parametrize("site", ["P15", "P17", "T36", "X42"])
def test_macos_videotoolbox_v4(
    site: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """M-V4: HLG refused (P17), the historical labels (T36), each encoder's PROVED capability
    and the unadvertised-depth refusal, the negative-timestamp refusal (P15 / X42). The
    encodes and the full comparator are :func:`test_macos_videotoolbox_v4_corpus`'s."""
    from clearwater.io.video import probe as probe_file

    if site == "P17":  # HLG is refused before decode or encode, VT available or not
        hlg = _clip(
            tmp_path / "hlg.mp4",
            seconds=0.2,
            extra=[
                "-x265-params",
                "log-level=error:colorprim=bt2020:transfer=arib-std-b67:colormatrix=bt2020nc",
            ],
        )
        result = probe_file(hlg)
        assert any(f.severity == "refuse" for f in result.faults)
        return
    if site == "T36":
        assert _w().labelled_rows("video_fidelity.py") and shutil.which("nvidia-smi") is None
    vt, x265 = _capability(VT), _capability(X265)
    assert x265.available and x265.bit_depths == (8, 10)
    if vt.available:
        assert_advertised(vt)
        assert_unadvertised_refused(vt)
    else:
        assert_proved_unavailable(vt)  # A r2 item 11: a reason and no depth before the skip
    if site in ("P15", "X42"):
        _negative_timestamps_refused(monkeypatch, tmp_path, tmp_path_factory)


# --- M-SPACE ---------------------------------------------------------------------------------


SPACE_QUALITIES = ("high", "standard", "draft")
"""The D75 quality levels M-SPACE encodes at."""


@pytest.mark.parametrize("site", ["P64", "P69"])
def test_macos_videotoolbox_space_estimate(
    site: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, volumes: dict[str, Path]
) -> None:
    """M-SPACE: VT outputs under both Q1 rate candidates, at every ADVERTISED depth and every
    quality, each within the D87 estimate; ENOSPC on a full disk image is disk-full; free
    bytes from the APFS volume (purgeable space not counted)."""
    from clearwater.interfaces import Settings
    from clearwater.io.video import encode
    from clearwater.jobs import disk_space
    from clearwater.jobs.safe_write import is_disk_full

    if site == "P69":
        target = volumes["exfat"] / "fill.bin"
        with pytest.raises(OSError) as caught, target.open("wb") as handle:
            while True:
                handle.write(b"\0" * (1 << 20))
                handle.flush()
        assert is_disk_full(caught.value), caught.value
        target.unlink()
        check = disk_space.check_free_space(volumes["insensitive"], 1)
        assert check.ok and check.free == shutil.disk_usage(volumes["insensitive"]).free
        return
    vt = _vt_or_skip()
    assert_unadvertised_refused(vt)
    clip = _clip(tmp_path / "in.mp4", seconds=2.0)
    measured = {}
    for candidate in ("A", "B"):
        monkeypatch.setattr(encode, "VT_RATE_CONTROL", candidate)
        for depth in vt.bit_depths:
            for quality in SPACE_QUALITIES:
                out = tmp_path / f"{candidate}-{depth}-{quality}.mp4"
                probe, _report = _encode(clip, out, encoder=VT, quality=quality, bit_depth=depth)
                estimate = disk_space.estimate_video_bytes(
                    clip.stat().st_size,
                    Settings(quality_level=quality),  # type: ignore[arg-type]
                    width=probe.video.width,
                    height=probe.video.height,
                    frame_rate=probe.video.frame_rate,
                    duration_s=probe.duration_s,
                )
                measured[candidate, depth, quality] = (out.stat().st_size, estimate)
    over = {key: sizes for key, sizes in measured.items() if sizes[0] > sizes[1]}
    assert over == {}, over
    expected = {(c, d, q) for c in ("A", "B") for d in vt.bit_depths for q in SPACE_QUALITIES}
    assert set(measured) == expected


# --- M-FS ------------------------------------------------------------------------------------


def _fs_identity(volumes: dict[str, Path]) -> None:
    """P29 / P30 / P44 / P45: one object, two spellings vs two objects, on both APFS modes."""
    batch_panel = importlib.import_module("clearwater.gui.batch_panel")
    from clearwater.jobs.naming import is_same_path

    insensitive, sensitive = volumes["insensitive"], volumes["sensitive"]
    assert _case_insensitive(insensitive) and not _case_insensitive(sensitive)
    (insensitive / "clip.MP4").write_bytes(b"1")
    assert batch_panel._key(insensitive / "clip.MP4") == batch_panel._key(insensitive / "CLIP.mp4")
    assert is_same_path(insensitive / "clip.MP4", insensitive / "CLIP.mp4")
    (sensitive / "clip.MP4").write_bytes(b"1")
    (sensitive / "CLIP.mp4").write_bytes(b"2")
    assert batch_panel._key(sensitive / "clip.MP4") != batch_panel._key(sensitive / "CLIP.mp4")
    assert not is_same_path(sensitive / "clip.MP4", sensitive / "CLIP.mp4")
    labels = batch_panel.item_labels(
        [batch_panel.BatchItem(sensitive / n, "video") for n in ("clip.MP4", "CLIP.mp4")]
    )
    assert len(set(labels)) == 2


FOLDING_CORPUS = ("\u0131", "I", "\u00df", "SS", "caf\u00e9", "cafe\u0301", "Look", "LOOK")
"""DR-34(a)'s corpus: dotless i, sharp s, NFC / NFD, plain case."""


def _fold(name: str) -> str:
    return unicodedata.normalize("NFC", name).casefold()


def _fs_presets(volumes: dict[str, Path]) -> None:
    """P40 / P41 / P49 / P73: on both APFS modes, ``overwrite=False`` saves and renames INTO
    each folding-corpus name (U+0131, U+00DF, NFC / NFD, case) never replace the occupant; its
    bytes and the renamed preset's stay unchanged, and a free name takes the bytes it held."""
    from dataclasses import replace

    from clearwater.config.presets import PresetError, PresetStore

    w_presets = importlib.import_module("test_config_presets")
    occupant_set = w_presets._set()
    mover_set = replace(occupant_set, parameters={"strength": 0.75, "steps": 2, "enabled": True})
    for label in ("insensitive", "sensitive"):
        for name in FOLDING_CORPUS:
            folder = volumes[label] / "presets"
            store = PresetStore(folder)
            occupant = store.save(name, occupant_set)
            mover = store.save("Mover", mover_set)
            held, moving = occupant.read_bytes(), mover.read_bytes()
            assert held != moving  # the two files are told apart by their bytes
            twins = [t for t in FOLDING_CORPUS if _fold(t) == _fold(name)]
            for twin in twins:  # the occupied name itself and each name that folds onto it
                if twin != name:
                    with pytest.raises(PresetError):
                        store.save(twin, w_presets._set(), overwrite=False)
                with pytest.raises(PresetError):
                    store.rename("Mover", twin)
                assert occupant.read_bytes() == held, (label, name, twin)
                assert mover.read_bytes() == moving, (label, name, twin)
            moved = store.rename("Mover", "Fresh")  # the control: a free name is taken
            assert moved.read_bytes() == moving and not mover.exists()
            assert occupant.read_bytes() == held
            shutil.rmtree(folder)


def _vanished_entry(function: Any, path: str, error: BaseException) -> None:
    """``shutil.rmtree``'s ``onexc`` for T14's exFAT folder: a listed entry may be gone.

    On exFAT macOS removes a file's AppleDouble ``._`` companion together with the file, so a
    companion the folder scan listed can be missing at its own unlink (runner run 3,
    ``macos.log``). Exactly ``FileNotFoundError`` from the unlink of a listed entry is
    swallowed; every other error, and a ``FileNotFoundError`` from any other call (the
    folder's own removal, its listing), is raised again.

    Args:
        function: The call that failed (``os.unlink`` for a listed non-folder entry).
        path: The path it was called on.
        error: The exception it raised.

    Raises:
        BaseException: ``error`` itself, unless it is a vanished listed entry.
    """
    if function is os.unlink and isinstance(error, FileNotFoundError):
        return
    raise error


def _fs_appledouble(volumes: dict[str, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    """T14: macOS writes ``._`` files on exFAT; the inventory counts them apart, never as clips."""
    inventory = _w()._stub_probes(monkeypatch)
    root = volumes["exfat"] / "footage"
    root.mkdir()
    clip = root / "clip.MP4"
    clip.write_bytes(b"x")
    done = _run(["xattr", "-w", "com.clearwater.test", "1", str(clip)])
    assert done.returncode == 0, done.stderr
    assert (root / "._clip.MP4").exists()  # the AppleDouble companion is real on exFAT
    result = inventory.scan_tree(root)
    assert [r.path.name for r in result.records] == ["clip.MP4"] and result.appledouble >= 1
    shutil.rmtree(root, onexc=_vanished_entry)


def _fs_exfat_links(volumes: dict[str, Path]) -> None:
    """P48 / P73: exFAT refuses hard links; the no-replace fallbacks still never replace."""
    from clearwater.jobs import safe_write

    folder = volumes["exfat"] / "links"
    folder.mkdir()
    temp, final = folder / "a.tmp", folder / "a.mp4"
    temp.write_bytes(b"1")
    with pytest.raises(OSError) as caught:
        os.link(temp, folder / "b.mp4")
    assert caught.value.errno in (
        errno.EPERM,
        errno.ENOTSUP,
        errno.EOPNOTSUPP,
        errno.EMLINK,
        errno.EXDEV,
    )
    assert safe_write._install(temp, final) and final.read_bytes() == b"1"
    temp.write_bytes(b"2")
    assert not safe_write._install(temp, final) and final.read_bytes() == b"1"
    shutil.rmtree(folder)


def _fs_native_alias(site: str, tmp_path: Path, volumes: dict[str, Path]) -> None:
    """T17 / T26-T29: symlink, case and symlink-then-``..`` aliases of the root are refused.

    Natively, before any write. The case alias runs on the case-insensitive image and its
    distinct-name control on the case-sensitive one (Reviewer B finding 5), never on the host
    temporary volume.
    """
    footage_guard = importlib.import_module("footage_guard")
    root = tmp_path / "Dive" / "Footage"
    (root / "clips").mkdir(parents=True)
    link = tmp_path / "alias"
    link.symlink_to(root, target_is_directory=True)
    case_base = volumes["insensitive"] / f"alias-{site}"
    case_root = case_base / "Dive" / "Footage"
    (case_root / "clips").mkdir(parents=True)
    for unsafe, guarded in (
        (link / "out", root),
        (case_base / "DIVE" / "FOOTAGE" / "out", case_root),
    ):
        assert footage_guard.is_inside(unsafe, guarded), unsafe
        assert _w()._guard_refusals(site, guarded, unsafe)
    shutil.rmtree(case_base)
    distinct_base = volumes["sensitive"] / f"alias-{site}"
    distinct_root = distinct_base / "Dive" / "Footage"
    (distinct_root / "clips").mkdir(parents=True)
    (distinct_base / "DIVE" / "FOOTAGE").mkdir(parents=True)  # another folder on this volume
    for other in (distinct_base / "DIVE" / "FOOTAGE" / "out", distinct_base / "dive" / "out"):
        assert not footage_guard.is_inside(other, distinct_root), other
    shutil.rmtree(distinct_base)
    assert not footage_guard.is_inside(tmp_path / "Dive" / "Footage-out", root)
    # A r2 item 1, natively: a real symlink to a sub-folder, then ``..`` (the kernel's order).
    folder = tmp_path / "dotdot"
    linked, unsafe, links = _w().link_topology(folder)
    for alias, target in links.items():
        alias.symlink_to(target, target_is_directory=True)
    assert os.path.realpath(unsafe) == str((linked / "output").resolve())
    before = _w().tree(folder)
    assert _w()._guard_refusals(site, linked, unsafe)
    assert _w().tree(folder) == before  # refused before any write
    assert footage_guard.is_inside(unsafe, linked)


def _fs_finder_slash(tmp_path: Path) -> None:
    """P70: a Finder-typed ``/`` is stored as ``:``; the output plan refuses it, naming it."""
    from clearwater.interfaces import Settings
    from clearwater.jobs import naming

    source = tmp_path / "dive:01.MP4"  # what Finder stores for "dive/01.MP4"
    source.write_bytes(b"x")
    with pytest.raises(naming.OutputNameError, match="contains ':'"):
        naming.final_output_path(source, Settings(), naming.MediaKind.VIDEO)


def _fs_native(
    site: str, request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Run the row's Mac-only check (the disk images attach only for the rows needing them)."""
    if site in ("P29", "P30", "P44", "P45", "X29"):
        _fs_identity(request.getfixturevalue("volumes"))
    elif site in ("P40", "P41", "P49", "P73"):
        _fs_presets(request.getfixturevalue("volumes"))
    elif site == "T14":
        _fs_appledouble(request.getfixturevalue("volumes"), monkeypatch)
    elif site == "P48":
        _fs_exfat_links(request.getfixturevalue("volumes"))
    elif site in ("T17", "T26", "T27", "T28", "T29"):
        _fs_native_alias(site, tmp_path / "alias", request.getfixturevalue("volumes"))
    elif site == "P70":
        _fs_finder_slash(tmp_path)


FS_SITES = [
    "P28",
    "P29",
    "P30",
    "P39",
    "P40",
    "P41",
    "P42",
    "P43",
    "P44",
    "P45",
    "P46",
    "P47",
    "P48",
    "P49",
    "P50",
    "P51",
    "P52",
    "P53",
    "P54",
    "P67",
    "P68",
    "P70",
    "P73",
    "T14",
    "T15",
    "T16",
    "T17",
    "T18",
    "T19",
    "T20",
    "T21",
    "T22",
    "T23",
    "T24",
    "T26",
    "T27",
    "T28",
    "T29",
    "T30",
    "T31",
    "T32",
    "T45",
    "T46",
    "T47",
    "T48",
    "T52",
    "X19",
    "X20",
    "X22",
    "X29",
    "X46",
]


@pytest.mark.parametrize("site", FS_SITES)
def test_macos_filesystem_semantics(
    site: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    request: pytest.FixtureRequest,
) -> None:
    """M-FS: the Windows-side case on the native APFS volume, then the Mac-only check where the
    row has one (both APFS case modes, exFAT, the DR-34(a) corpus, Finder's ``:``)."""
    (tmp_path / "w").mkdir()
    with pytest.MonkeyPatch.context() as w_patch:  # the W stubs end before the native half
        _w().FS_CASES[site](w_patch, tmp_path / "w")
    _fs_native(site, request, monkeypatch, tmp_path)


def test_the_exfat_cleanup_swallows_only_a_vanished_listed_entry() -> None:
    """Run 3 item 5: ``_vanished_entry`` swallows exactly ``FileNotFoundError`` from an unlink;
    another ``OSError``, or a ``FileNotFoundError`` from another call, propagates unchanged."""
    _vanished_entry(os.unlink, "footage/._clip.MP4", FileNotFoundError(2, "gone"))
    for function, error in (
        (os.unlink, PermissionError(13, "denied")),
        (os.unlink, OSError(5, "input/output error")),
        (os.rmdir, FileNotFoundError(2, "the folder itself")),
        (os.lstat, FileNotFoundError(2, "a listed folder")),
        (os.scandir, FileNotFoundError(2, "the listing")),
    ):
        with pytest.raises(type(error)) as caught:
            _vanished_entry(function, "footage/x", error)
        assert caught.value is error


def test_the_exfat_cleanup_removes_a_pair_that_vanishes_together(
    tmp_path: Path, monkeypatch
) -> None:
    """Run 3 item 5: a file and its ``._`` companion removed together (exFAT's behaviour,
    simulated): plain ``rmtree`` raises run 3's ``FileNotFoundError``; with the ``onexc`` the
    folder is gone."""
    real_unlink = os.unlink
    partners = {"clip.MP4": "._clip.MP4", "._clip.MP4": "clip.MP4"}

    def unlink_pair(path: Any, *, dir_fd: int | None = None) -> None:
        real_unlink(path, dir_fd=dir_fd)
        partner = partners.get(os.path.basename(os.fspath(path)))
        if partner is not None:
            with contextlib.suppress(FileNotFoundError):
                real_unlink(os.path.join(os.path.dirname(os.fspath(path)), partner), dir_fd=dir_fd)

    for onexc in (None, _vanished_entry):
        root = tmp_path / ("plain" if onexc is None else "tolerant")
        root.mkdir()
        (root / "clip.MP4").write_bytes(b"x")
        (root / "._clip.MP4").write_bytes(b"x")
        with monkeypatch.context() as patch:
            patch.setattr(os, "unlink", unlink_pair)
            if onexc is None:
                with pytest.raises(FileNotFoundError):
                    shutil.rmtree(root)
            else:
                shutil.rmtree(root, onexc=onexc)
        assert root.exists() is (onexc is None)


# --- M-GUARD ---------------------------------------------------------------------------------


def _guard_native(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Native topologies against the temp-root guard and footage_guard; the footage unchanged."""
    import tempfile

    conftest = sys.modules.get("conftest") or importlib.import_module("conftest")
    footage_guard = importlib.import_module("footage_guard")
    footage = tmp_path / "Footage"
    (footage / "clips").mkdir(parents=True)
    (footage / "clips" / "GX01.MP4").write_bytes(b"synthetic")
    before = sorted(p.relative_to(footage).as_posix() for p in footage.rglob("*"))
    link = tmp_path / "link"
    link.symlink_to(footage, target_is_directory=True)
    loop = tmp_path / "loop"
    loop.symlink_to(loop)
    hard = tmp_path / "hard.MP4"
    os.link(footage / "clips" / "GX01.MP4", hard)
    aliases = [link / "basetemp", footage / "x"]
    if _case_insensitive(tmp_path):
        aliases.append(tmp_path / "FOOTAGE" / "basetemp")
    for inside in aliases:
        assert footage_guard.is_inside(inside, footage), inside
        assert conftest._inside_or_equal(conftest._canonical(inside), conftest._canonical(footage))
    assert not footage_guard.is_inside(loop / "x", footage)  # a loop is bounded, not inside
    assert hard.stat().st_nlink == 2  # a hard-linked name outside is the runner's refusal (X35)
    monkeypatch.setattr(tempfile, "tempdir", None)
    monkeypatch.setenv("TMPDIR", str(footage))
    assert conftest._temp_root_candidates()[0] == str(footage)
    assert after_unchanged(footage, before)


def after_unchanged(footage: Path, before: list[str]) -> bool:
    return sorted(p.relative_to(footage).as_posix() for p in footage.rglob("*")) == before


GUARD_SITES = [
    "X01",
    "X02",
    "X03",
    "X04",
    "X05",
    "X06",
    "X07",
    "X08",
    "X09",
    "X10",
    "X11",
    "X12",
    "X17",
    "X18",
    "X21",
    "X30",
    "X31",
    "X32",
    "X33",
    "X34",
    "X35",
    "X36",
    "X37",
    "X38",
]


@pytest.mark.parametrize("site", GUARD_SITES)
def test_macos_footage_guard_and_helpers(
    site: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """M-GUARD: TMPDIR / TEMP / TMP / basetemp, symlinks, hard links, loops and case aliases on
    the native volume; the Windows-only controls skip here and their guard check still holds."""
    with pytest.MonkeyPatch.context() as w_patch:  # the W stubs end before the native half
        _w().GUARD_CASES[site](w_patch, tmp_path)
    _guard_native(tmp_path / "native", monkeypatch)


# --- M-TOOL ----------------------------------------------------------------------------------

TOOL_SITES = [
    "T01",
    "T02",
    "T03",
    "T04",
    "T05",
    "T06",
    "T09",
    "T10",
    "T11",
    "T12",
    "T13",
    "T38",
    "T39",
    "T40",
    "T41",
]


def _tool_native(site: str, tmp_path: Path) -> None:
    import platform

    environment_report = importlib.import_module("environment_report")
    if site in ("T01", "T02"):
        report = environment_report.collect()
        assert report["os_name"] == "Darwin" and report["machine"] == platform.machine()
        assert str(report["process_architecture"]).startswith("macosx-")
        assert report["gpu_model"] is None
        assert report["unavailable"]["gpu_model"].startswith("not applicable on this platform")
        assert report["correction_backend"] == "numpy"
        assert [e["name"] for e in report["encoders"]] == [VT, X265]
    elif site in ("T03", "T05"):
        bench = importlib.import_module("prototype.bench")
        assert set(bench._windows_power().values()) == {None}
        assert bench._platform_name() == platform.platform()
    elif site == "T04":
        assert importlib.import_module("prototype.bench")._cpu_brand()
    elif site == "T09":
        transport = importlib.import_module("spike_io.transport")
        assert transport.idle_gate(tmp_path / "gate.ps1", tmp_path)["ran"] is False
    elif site in ("T13", "T38", "T39", "T40", "T41"):
        assert shutil.which("nvidia-smi") is None  # every NVIDIA reading is an honest absence


@pytest.mark.parametrize("site", TOOL_SITES)
def test_macos_tool_reporting(site: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """M-TOOL: native environment facts, CPU tools without NVIDIA dependencies, the licence
    scan's Mach-O forms (candidate DR 3: expected to fail until that DR lands)."""
    if site in ("T11", "T12"):
        licences = importlib.import_module("spike_io.licences")
        if not {".so", ".dylib"} <= set(licences._CODE_SUFFIXES):
            pytest.xfail("candidate DR 3: the licence scan lacks the Mach-O library forms")
    with pytest.MonkeyPatch.context() as w_patch:  # the W stubs end before the native half
        _w().TOOL_CASES[site](w_patch, tmp_path)
    _tool_native(site, tmp_path)


# --- M-GUI (native Cocoa, in a child) --------------------------------------------------------

COCOA_PROBE = """
import json, sys
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QGuiApplication, QKeySequence, QWheelEvent
from PySide6.QtWidgets import QApplication, QFileDialog
app = QApplication(sys.argv)
from clearwater.core import backend
from clearwater.gui import sources, stub_engines
from clearwater.gui.preview import PreviewWidget
from clearwater.gui.settings_dialog import AUTO_TEXT, auto_tooltip
from clearwater.gui.shell import MainWindow
from clearwater.config.paths import app_locations
from clearwater.io.video.capability import detect_capabilities
window = MainWindow(stub_engines(), app_locations())
window.show()
app.processEvents()
menus = [a.text() for a in window.menuBar().actions()]
tools = window.menuBar().actions()[2].menu()
widget = PreviewWidget()
steps = []
widget.zoom_in = lambda: steps.append("in")
widget.zoom_out = lambda: steps.append("out")
for dy, phase in ((40, Qt.ScrollPhase.ScrollBegin), (40, Qt.ScrollPhase.ScrollUpdate),
                  (40, Qt.ScrollPhase.ScrollMomentum), (-120, Qt.ScrollPhase.NoScrollPhase)):
    widget.wheelEvent(QWheelEvent(QPointF(5, 5), QPointF(5, 5), QPoint(0, 0), QPoint(0, dy),
        Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier, phase, False))
caps = detect_capabilities()
dialog = QFileDialog()
print(json.dumps({
    "platform": QGuiApplication.platformName(),
    "menus": menus,
    "tools": [a.text() for a in tools.actions() if a.isVisible()],
    "zoom": window.view_actions["zoom_in"].shortcut().toString(
        QKeySequence.SequenceFormat.NativeText),
    "dpr": window.devicePixelRatioF(),
    "reason": backend._probe_gpu()[1],
    "auto": AUTO_TEXT, "tip": auto_tooltip(caps),
    "rows": [c.name for c in caps],
    "steps": steps,
    "native_dialog": not dialog.testOption(QFileDialog.Option.DontUseNativeDialog),
    "filter": sources.file_filter(),
}))
window.close()
"""


@functools.cache
def _cocoa(root: str) -> dict[str, Any]:
    result: dict[str, Any] = _python(COCOA_PROBE, Path(root), QT_QPA_PLATFORM="cocoa")
    return result


GUI_SITES = [
    "P22",
    "P27",
    "P31",
    "P32",
    "P33",
    "P34",
    "P35",
    "P36",
    "P37",
    "P38",
    "P63",
    "P71",
    "X39",
    "X40",
    "X41",
]


@pytest.mark.gui
@pytest.mark.parametrize("site", GUI_SITES)
def test_macos_native_gui_contract(site: str, tmp_path_factory: pytest.TempPathFactory) -> None:
    """M-GUI: the Cocoa platform's menus (the Settings / Quit application-menu merge and the
    Tools menu left), Command shortcuts, the Retina ratio, the VT-aware automatic label and the
    AD-9 reason, trackpad momentum, native dialogs. Qt events go to Clearwater's own widgets
    only; picking files in the native dialogs is the owner's hand check at WP6.5 (no
    synthetic desktop input)."""
    facts = _cocoa(str(tmp_path_factory.getbasetemp() / "cocoa"))
    assert facts["platform"] == "cocoa"  # X39: the native leg is not the offscreen one
    if site == "P22":
        assert facts["reason"] == "CPU: graphics-card processing is not available on macOS"
    elif site == "P31":
        assert facts["menus"][:2] == ["&File", "&View"] and facts["tools"] == ["&Settings..."]
    elif site == "P32":
        assert "\u2318" in facts["zoom"]  # Command, not Ctrl
    elif site in ("P33", "P34", "P35", "P36", "P27"):
        assert facts["native_dialog"] and "*.mp4" in facts["filter"]
    elif site in ("P37", "P63", "X41"):
        assert facts["auto"] == "Automatic (the hardware encoder when available)"
        assert facts["rows"] == [VT, X265]
        assert "VideoToolbox" in facts["tip"] or facts["tip"] == "Uses libx265."
    elif site in ("P38", "X40"):
        assert facts["dpr"] >= 1.0
    elif site == "P71":
        assert facts["steps"] == ["in", "out"]


# --- M-BUNDLE --------------------------------------------------------------------------------


def _bundle() -> Path:
    value = os.environ.get(BUNDLE_VARIABLE)
    if not value:
        pytest.skip(f"{BUNDLE_VARIABLE} is not set: WP6.5 builds the app bundle")
    bundle = Path(value)
    assert (bundle / "Contents" / "MacOS").is_dir(), bundle
    return bundle


@pytest.mark.gui
@pytest.mark.parametrize("site", ["P16", "P24", "P57", "X28"])
def test_macos_bundle_smoke(site: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """M-BUNDLE: the bundle's own FFmpeg runs with no PATH, and the frozen worker command
    re-enters ``Contents/MacOS``. Launching the bundle from Finder / Terminal, Dock Quit,
    Cmd-Q and logout during an export are the owner's hand checks at WP6.5 (no frozen run here
    without the isolation rule's redirection; no synthetic desktop input)."""
    bundle = _bundle()
    macos = bundle / "Contents" / "MacOS"
    executables = [p for p in macos.iterdir() if p.is_file() and os.access(p, os.X_OK)]
    if site in ("P16", "P57"):
        tools = {p.name: p for p in bundle.rglob("ff*") if p.name in ("ffmpeg", "ffprobe")}
        assert set(tools) == {"ffmpeg", "ffprobe"}, sorted(tools)
        for tool in tools.values():
            done = subprocess.run(
                [str(tool), "-hide_banner", "-version"],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_S,
                env={"PATH": "", "HOME": str(tmp_path)},
            )
            assert done.returncode == 0 and done.stdout.startswith(f"{tool.name} version")
        return
    from clearwater.app.composition import process_export_jobs

    main = next(p for p in executables if p.name.lower().startswith("clearwater"))
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(main))
    jobs = process_export_jobs(photo_exports=object(), cache_dir=tmp_path)  # type: ignore[arg-type]
    assert list(jobs._command) == [str(main), "--export-worker"]  # type: ignore[attr-defined]
    assert Path(jobs._command[0]).parent == macos  # type: ignore[attr-defined]
