"""Headless release checks against synthetic archives and Python process stubs only."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import psutil
import pytest

import test_tools_package_notices as support

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows onedir smoke")

ROOT = Path(__file__).resolve().parents[1]

# Independent, literal protocol expectations: the stub never imports product code.
REFUSALS = [
    (["-c", "pass"], "Clearwater: -c is not supported"),
    (["-m", "http.server"], "Clearwater: -m 'http.server': no GPU pack is loaded"),
    (["--multiprocessing-fork"], "Clearwater: multiprocessing children are not supported"),
    (
        ["--multiprocessing-resource-tracker"],
        "Clearwater: multiprocessing children are not supported",
    ),
    (["-R", "-c", "pass"], "Clearwater: -c is not supported"),
    (["-t", "-m", "http.server"], "Clearwater: -m 'http.server': no GPU pack is loaded"),
    (["-Rt", "-c", "pass"], "Clearwater: -c is not supported"),
    (["--check-hash-based-pycs", "always", "-c", "pass"], "Clearwater: -c is not supported"),
    (
        ["--check-hash-based-pycs", "never", "-m", "http.server"],
        "Clearwater: -m 'http.server': no GPU pack is loaded",
    ),
    (
        ["-m", "http.server", "--multiprocessing-fork"],
        "Clearwater: multiprocessing children are not supported",
    ),
]

STUB = r"""
import json, os, subprocess, sys, time
from pathlib import Path
config = json.loads(Path(os.environ['STUB_CONFIG']).read_text())
args = sys.argv[1:]
with Path(config['calls']).open('a') as stream:
    stream.write(json.dumps({'args': args, 'cwd': os.getcwd(), 'env': dict(os.environ)}) + '\n')
mode = config.get('mode', '')
if mode == 'hang':
    Path(config['pid']).write_text(str(os.getpid()))
    time.sleep(120)
if mode in {'leftover', 'fast-leftover'}:
    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(120)'],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    Path(config['pid']).write_text(str(child.pid))
    if mode == 'leftover':
        time.sleep(.2)
if args == ['-version']:
    version = config['version'] if mode != 'version' else 'WRONG'
    print(Path(os.environ['STUB_EXE']).stem + ' version ' + version)
    print(config['configure'] if mode != 'configure' else 'configuration: wrong')
    sys.exit(0)
if args == ['-hide_banner', '-encoders']:
    lines = ' V..... libx265 test'
    print(' V..... hevc_nvenc test\n' + lines if mode != 'encoders' else lines)
    sys.exit(0)
if args == ['--export-worker']:
    if not (Path.cwd() / '_internal/scipy/_lib/_ccallback_c.pyd').exists():
        log = Path(os.environ['APPDATA']) / 'Clearwater/logs/clearwater.log'
        log.parent.mkdir(parents=True)
        if mode != 'no-log':
            log.write_text('Unhandled exception\nTraceback (most recent call last):\n'
                           'ImportError: _ccallback_c missing\n')
        print('Clearwater: unexpected error; see log: ' + str(log), file=sys.stderr)
        sys.exit(1)
    data = sys.stdin.read()
    message = 'no request document on stdin' if not data else 'the request is not UTF-8 JSON'
    print('export worker: ' + message, file=sys.stderr)
    sys.exit(2)
for expected, message in config['refusals']:
    if args == expected:
        if mode == 'stdout':
            print('unexpected protocol output')
        print(message, file=sys.stderr)
        if mode == 'two-lines':
            print('unexpected extra line', file=sys.stderr)
        sys.exit(9 if mode == 'wrong-status' else 2)
raise RuntimeError('stub received an unexpected/GUI argument set')
"""


def load_smoke():
    path = ROOT / "tools/package/smoke.py"
    assert path.is_file(), "headless smoke implementation is absent"
    spec = importlib.util.spec_from_file_location("wp63b_smoke_checks", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def snapshot(folder):
    return {
        p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in folder.rglob("*")
        if p.is_file()
    }


@pytest.fixture
def synthetic(tmp_path, monkeypatch):
    smoke = load_smoke()
    release = support.release.__wrapped__(tmp_path)
    folder = release["folder"]
    native = "scipy/_lib/_ccallback_c.pyd"
    (folder / "_internal/scipy/_lib").mkdir(parents=True)
    (folder / "_internal" / native).write_bytes(b"synthetic required worker import")
    release["distributions"]["scipy"] = support.installed(
        release["site"],
        "scipy",
        "1.17.0",
        {
            native: "synthetic required worker import",
            "scipy-1.17.0.dist-info/licenses/LICENSE.txt": "synthetic BSD text",
        },
    )
    with release["uv_lock"].open("a") as stream:
        stream.write('\n[[package]]\nname = "scipy"\nversion = "1.17.0"\n')
    with release["audit"].open("a") as stream:
        stream.write(
            "| scipy | 1.17.0 | BSD-3-Clause | COMPATIBLE | "
            "[Source](https://github.com/scipy/scipy/tree/v1.17.0) |\n"
        )
    # Keep the added audit row within the audit table.
    audit = release["audit"].read_text().replace("### Native components and conditions\n", "")
    release["audit"].write_text(audit + "### Native components and conditions\n")
    notices = support.load_notices()
    real_plan = notices.plan_notices

    def plan(target):
        return real_plan(
            target,
            audit_path=release["audit"],
            uv_lock_path=release["uv_lock"],
            ffmpeg_lock_path=release["ffmpeg_path"],
            distribution=release["distributions"].__getitem__,
        )

    monkeypatch.setattr(notices, "plan_notices", plan)
    monkeypatch.setattr(smoke, "_notices_tool", lambda: notices)
    monkeypatch.setattr(smoke._build_tool(), "pack_sources", lambda: [])
    monkeypatch.setattr(smoke._build_tool(), "hidden_imports", lambda scan: [])
    monkeypatch.setattr(smoke._build_tool(), "load_ffmpeg_lock", lambda: release["ffmpeg"])
    script = tmp_path / "stub.py"
    script.write_text(STUB)
    config_path = tmp_path / "stub.json"
    config = {
        "calls": str(tmp_path / "calls.jsonl"),
        "pid": str(tmp_path / "pid.txt"),
        "version": release["ffmpeg"]["version"],
        "configure": release["ffmpeg"]["configure_line"],
        "refusals": REFUSALS,
    }
    real_popen = subprocess.Popen

    def launch(args, **kwargs):
        # Only substitute the native loader; supervision/capture/env/cwd remain real.
        assert Path(args[0]).name in {"Clearwater.exe", "ffmpeg.exe", "ffprobe.exe"}
        env = kwargs["env"]
        assert env["PATH"] == str(Path(os.environ["SYSTEMROOT"]) / "System32")
        for key in (
            "APPDATA",
            "LOCALAPPDATA",
            "XDG_CONFIG_HOME",
            "XDG_CACHE_HOME",
            "HOME",
            "USERPROFILE",
            "TEMP",
            "TMP",
        ):
            assert Path(env[key]).is_relative_to(tmp_path / "out/smoke")
        assert kwargs["creationflags"] & subprocess.CREATE_NO_WINDOW
        env["STUB_CONFIG"] = str(config_path)
        env["STUB_EXE"] = args[0]
        # Use the native interpreter directly, not Windows' venv redirector,
        # which adds an unrelated short-lived bootstrap parent to each stub.
        return real_popen([sys._base_executable, str(script), *args[1:]], **kwargs)

    monkeypatch.setattr(smoke.subprocess, "Popen", launch)

    def prepare(mode="", ffmpeg=False):
        config["mode"] = mode
        config_path.write_text(json.dumps(config))
        if ffmpeg:
            support.add_ffmpeg(release)
        path = folder / "THIRD_PARTY_NOTICES.md"
        path.touch()
        path.write_bytes(notices.render_notices(plan(folder)))

    prepare()
    return smoke, release, prepare, config


@pytest.mark.parametrize(
    "mode, message", [("wrong-status", "exit 9"), ("two-lines", "stderr"), ("stdout", "stdout")]
)
def test_refusal_status_and_extra_stderr_fail_by_row_name(synthetic, tmp_path, mode, message):
    smoke, release, prepare, _ = synthetic
    prepare(mode)
    with pytest.raises(smoke.SmokeError, match="refuse-command.*" + message):
        smoke.run_smoke(release["folder"], out=tmp_path / "out")


@pytest.mark.parametrize(
    "mode, message",
    [("hang", "timeout"), ("leftover", "process left"), ("fast-leftover", "process left")],
)
def test_timeout_and_surviving_child_fail_and_are_reaped(synthetic, tmp_path, mode, message):
    smoke, release, prepare, config = synthetic
    prepare(mode)
    try:
        with pytest.raises(smoke.SmokeError, match="refuse-command.*" + message):
            smoke.run_smoke(release["folder"], out=tmp_path / "out", timeout=1)
        pid = int(Path(config["pid"]).read_text())
        assert not psutil.pid_exists(pid), psutil.Process(pid).as_dict(
            attrs=["pid", "ppid", "status", "cmdline"]
        )
    finally:
        # RED must also be bounded and leave no synthetic child behind.
        if Path(config["pid"]).exists():
            pid = int(Path(config["pid"]).read_text())
            if psutil.pid_exists(pid):
                child = psutil.Process(pid)
                children = child.children(recursive=True)
                for target in [*reversed(children), child]:
                    if target.is_running():
                        target.kill()
                _, alive = psutil.wait_procs([*children, child], timeout=5)
                assert not alive


@pytest.mark.parametrize(
    "args",
    [
        (),
        ("file.mp4",),
        ("--version",),
        ("-I",),
        ("--export-worker", "extra"),
        ("--install-gpu-pack",),
    ],
)
def test_gui_or_other_uncommissioned_arguments_are_refused_before_launch(
    tmp_path, monkeypatch, args
):
    smoke = load_smoke()

    def forbidden(*args, **kwargs):
        pytest.fail("unsafe argument set reached process launch")

    monkeypatch.setattr(smoke.subprocess, "Popen", forbidden)
    with pytest.raises(smoke.SmokeError, match=r"unsafe.*GUI"):
        smoke.run_row(
            tmp_path / "Clearwater.exe",
            smoke.SmokeRow("unsafe", args, "", 2, ""),
            root=tmp_path,
            timeout=1,
        )


@pytest.mark.parametrize("ffmpeg", [False, True])
def test_complete_smoke_preserves_shipping_bytes_and_checks_conditional_tools(
    synthetic, tmp_path, capsys, ffmpeg
):
    smoke, release, prepare, config = synthetic
    prepare(ffmpeg=ffmpeg)
    before = snapshot(release["folder"])
    smoke.run_smoke(release["folder"], out=tmp_path / "out")
    assert snapshot(release["folder"]) == before
    copies = list((tmp_path / "out/smoke").glob("*/planted/Clearwater"))
    assert len(copies) == 1
    assert not (copies[0] / "_internal/scipy/_lib/_ccallback_c.pyd").exists()
    assert (release["folder"] / "_internal/scipy/_lib/_ccallback_c.pyd").is_file()
    logs = list((tmp_path / "out/smoke").rglob("clearwater.log"))
    assert len(logs) == 1 and "ImportError" in logs[0].read_text()
    calls = [json.loads(line) for line in Path(config["calls"]).read_text().splitlines()]
    assert [call["args"] for call in calls[:10]] == [args for args, _ in REFUSALS]
    assert len(calls) == (16 if ffmpeg else 13)
    output = capsys.readouterr().out
    (tmp_path / "out/smoke-transcript.txt").write_text(output, encoding="utf-8")
    assert "notices: PASS" in output
    assert "6 component rows" in output if not ffmpeg else "8 component rows" in output
    assert "bundle: PASS" in output and "hidden-imports: PASS" in output
    assert "total" in output and "largest" in output
    assert ("FFmpeg: SKIP (not bundled)" in output) == (not ffmpeg)
    if ffmpeg:
        assert "ffmpeg-version: PASS" in output and "ffprobe-version: PASS" in output
        assert "hevc_nvenc" in output and "libx265" in output


@pytest.mark.parametrize(
    "mode, row",
    [
        ("configure", "ffmpeg-version"),
        ("version", "ffmpeg-version"),
        ("encoders", "ffmpeg-encoders"),
        ("no-log", "planted-exception"),
    ],
)
def test_bad_configuration_capabilities_or_missing_exception_log_fail(
    synthetic, tmp_path, mode, row
):
    smoke, release, prepare, _ = synthetic
    prepare(mode, ffmpeg=mode != "no-log")
    with pytest.raises(smoke.SmokeError, match=row):
        smoke.run_smoke(release["folder"], out=tmp_path / "out")


@pytest.mark.parametrize(
    "defect, row", [("cuda", "bundle"), ("hidden", "hidden-imports"), ("notices", "notices")]
)
def test_static_checks_reread_artifact_and_refuse_before_entry_launch(
    synthetic, tmp_path, defect, row
):
    smoke, release, _, config = synthetic
    if defect == "cuda":
        (release["folder"] / "_internal/cudart64_12.dll").write_bytes(b"forbidden")
    elif defect == "hidden":
        build = smoke._build_tool()
        build.hidden_imports = lambda scan: [build.HiddenImport("graphlib", ("scan",), 1)]
    else:
        path = release["folder"] / "THIRD_PARTY_NOTICES.md"
        path.write_text(path.read_text().replace("6 component rows", "999 component rows"))
    with pytest.raises(smoke.SmokeError, match=row):
        smoke.run_smoke(release["folder"], out=tmp_path / "out")
    assert not Path(config["calls"]).exists()


def test_smoke_cli_runs_existing_folder_without_building(monkeypatch, tmp_path):
    build = support.load_notices()._build_tool()

    def no_build(*args, **kwargs):
        pytest.fail("standalone smoke invoked PyInstaller")

    def smoke(folder, *, out):
        assert folder == tmp_path / "release" and out == tmp_path / "out"
        return 7

    monkeypatch.setattr(build, "run_pyinstaller", no_build)
    monkeypatch.setattr(build, "smoke_artifact", smoke, raising=False)
    assert build.main(["--smoke", str(tmp_path / "release"), "--out", str(tmp_path / "out")]) == 7
    with pytest.raises(SystemExit):
        build.parse_args(["--smoke"])
    with pytest.raises(SystemExit):
        build.parse_args(["--form", "onefile", "--smoke"])
