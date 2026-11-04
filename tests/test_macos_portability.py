"""Native macOS portability tests (WP6.4 writes them; WP6.5 runs them on the owner's Mac).

Each M function takes a ``site`` parameter: the WP6.2 audit row whose mechanic it checks on a
real Mac (section 8's M references). Every test is marked ``macos`` and skipped off darwin by an
explicit platform skip (AD-36); the native interface rows also carry ``gui``. Nothing here
patches ``sys.platform``: the platform is the host's.

The rows shared with the Windows-side module re-run that module's case NATIVELY (the real APFS
volume, the real macOS ``realpath`` and ``normcase``, the real FFmpeg), then add the checks only
a Mac can make: a case-sensitive and an exFAT disk image (``hdiutil``, created and detached
under the test's temporary folder), real VideoToolbox encodes, a child in its own session, the
Cocoa platform. A runner without VideoToolbox (a CI Mac) passes M-CODEC and M-V4 on a PROVED
"unavailable" with its reason and the x265 fallback, and skips the VT-only cases with that
reason; it does not replace the owner's hardware evidence (audit section 8).

Isolation (CLAUDE.md's entry-point rule; DR-124): every child that imports the product runs
with HOME, APPDATA, LOCALAPPDATA and the XDG variables pointed at a disposable folder and a
bounded timeout; no test calls ``clearwater.__main__``, ``app.main`` or the export worker's
entry point; no test sends input to the desktop (native UI rows send Qt events to Clearwater's
own widgets only, and the interactive dialog checks are the owner's at WP6.5). Synthetic
footage only: the owner's footage folder is never read.
"""

from __future__ import annotations

import errno
import functools
import importlib
import json
import os
import shutil
import signal
import subprocess
import sys
import textwrap
import time
import unicodedata
from collections.abc import Iterator, Sequence
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


@pytest.fixture(scope="module")
def volumes(tmp_path_factory: pytest.TempPathFactory) -> Iterator[dict[str, Path]]:
    """Attach a case-sensitive APFS and an exFAT disk image under the temporary folder."""
    root = tmp_path_factory.mktemp("volumes")
    mounted: dict[str, Path] = {}
    try:
        for label, fs in (("sensitive", "Case-sensitive APFS"), ("exfat", "ExFAT")):
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
        mounted["insensitive"] = root / "default"
        mounted["insensitive"].mkdir()
        yield mounted
    finally:
        for label in ("sensitive", "exfat"):
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


def _open_fds() -> int:
    return len(os.listdir("/dev/fd"))


@pytest.mark.parametrize("site", ["P03", "P04", "T07", "T08", "X23", "X24"])
def test_macos_default_pipe_fidelity(
    site: str, caplog: pytest.LogCaptureFixture, tmp_path: Path
) -> None:
    """M-PIPE: the OS default pipe (Q2): no enlarged pipe, an INFO fallback, every frame and pts
    of a real decode, and no descriptor or child left after a cancelled one."""
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
        assert len(frames) == 30
        ticks = [f.pts_ticks for f in frames]
        assert ticks == sorted(ticks) and len(set(ticks)) == 30
        assert frames[0].pts == 0
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
        pytest.param(source, encoder, out, id=f"{source}-{encoder}-{out}")
        for source, depth in sources
        for encoder in (VT, X265)
        for out in sorted({depth, 10})
    ]


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
    if source_id == "sample:vid-rotated":
        assert probe(out).video.rotation == 90
    if source_id == "clip:offset":
        assert probe(out).edit_list == probe(source).edit_list


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
        hlg = _clip(tmp_path / "hlg.mp4", seconds=0.2, extra=["-color_trc", "arib-std-b67"])
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


@pytest.mark.parametrize("site", ["P64", "P69"])
def test_macos_videotoolbox_space_estimate(
    site: str, tmp_path: Path, volumes: dict[str, Path]
) -> None:
    """M-SPACE: a VT output's size against the D87 estimate; ENOSPC on a full disk image is
    disk-full; free bytes from the APFS volume (purgeable space not counted)."""
    from clearwater.interfaces import Settings
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
    _vt_or_skip()
    clip = _clip(tmp_path / "in.mp4", seconds=2.0)
    for quality in ("high", "standard", "draft"):
        out = tmp_path / f"{quality}.mp4"
        probe, _report = _encode(clip, out, encoder=VT, quality=quality, bit_depth=8)
        estimate = disk_space.estimate_video_bytes(
            clip.stat().st_size,
            Settings(quality_level=quality),  # type: ignore[arg-type]
            width=probe.video.width,
            height=probe.video.height,
            frame_rate=probe.video.frame_rate,
            duration_s=probe.duration_s,
        )
        assert out.stat().st_size <= estimate, (quality, out.stat().st_size, estimate)


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
    """P40 / P41 / P49 / P73: overwrite=False and rename into each folding name on APFS never
    replace another preset; its bytes stay unchanged."""
    from clearwater.config.presets import PresetError, PresetStore

    w_presets = importlib.import_module("test_config_presets")
    for label in ("insensitive", "sensitive"):
        folder = volumes[label] / "presets"
        for name in FOLDING_CORPUS:
            store = PresetStore(folder)
            other = store.save("Other", w_presets._set())
            before = other.read_bytes()
            store.save(name, w_presets._set())
            for twin in FOLDING_CORPUS:
                if twin != name and _fold(twin) == _fold(name):
                    with pytest.raises(PresetError):
                        store.save(twin, w_presets._set(), overwrite=False)
            with pytest.raises(PresetError):
                store.rename(name, "Other")
            assert other.read_bytes() == before
            shutil.rmtree(folder)


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
    shutil.rmtree(root)


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


def _fs_native_alias(site: str, tmp_path: Path) -> None:
    """T17 / T26-T29: a symlink alias, a case alias and a symlink-then-``..`` alias of the
    footage root are refused natively, before any write."""
    footage_guard = importlib.import_module("footage_guard")
    root = tmp_path / "Dive" / "Footage"
    (root / "clips").mkdir(parents=True)
    link = tmp_path / "alias"
    link.symlink_to(root, target_is_directory=True)
    for unsafe in (link / "out", tmp_path / "DIVE" / "FOOTAGE" / "out"):
        assert footage_guard.is_inside(unsafe, root), unsafe
        assert _w()._guard_refusals(site, root, unsafe)
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
        _fs_native_alias(site, tmp_path / "alias")
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
    "tools": [a.text() for a in tools.actions()],
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
