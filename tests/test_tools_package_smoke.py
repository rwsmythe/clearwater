"""Headless release checks against synthetic archives and Python process stubs only."""

from __future__ import annotations

import collections
import ctypes
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from types import SimpleNamespace

import psutil
import pytest

import test_tools_package_notices as support

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
time.sleep(config.get('startup_delay', 0))
if mode == 'hang':
    Path(config['pid']).write_text(str(os.getpid()))
    time.sleep(120)
if mode in {'leftover', 'fast-leftover'}:
    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(120)'],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             creationflags=subprocess.CREATE_NO_WINDOW)
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


def test_smoke_environment_strips_all_python_overrides(tmp_path, monkeypatch):
    """M12: no inherited Python search/configuration override reaches a frozen row."""
    variables = ("PYTHONPATH", "PYTHONHOME", "PYTHONUSERBASE", "PYTHONHASHSEED")
    for key in variables:
        monkeypatch.setenv(key, "foreign")
    env = load_smoke()._environment(tmp_path / "profile")
    assert not any(key.startswith("PYTHON") for key in env)


def test_safe_arguments_equal_the_eleven_headless_protocol_tuples():
    """An added non-headless row must fail even when its name looks harmless."""
    assert (
        frozenset(
            {
                ("-c", "pass"),
                ("-m", "http.server"),
                ("--multiprocessing-fork",),
                ("--multiprocessing-resource-tracker",),
                ("-R", "-c", "pass"),
                ("-t", "-m", "http.server"),
                ("-Rt", "-c", "pass"),
                ("--check-hash-based-pycs", "always", "-c", "pass"),
                ("--check-hash-based-pycs", "never", "-m", "http.server"),
                ("-m", "http.server", "--multiprocessing-fork"),
                ("--export-worker",),
            }
        )
        == load_smoke()._SAFE_ARGUMENTS
    )


def test_every_safe_argument_routes_to_refusal_or_worker_in_isolated_child(tmp_path):
    """Execute frozen routing in source with all GUI and worker effects stubbed."""
    arguments = sorted(load_smoke()._SAFE_ARGUMENTS)
    code = r"""
import importlib.abc, json, sys, types
class BlockQt(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name.split('.')[0] in ('PySide6', 'shiboken6'):
            raise AssertionError('Qt import attempted')
sys.meta_path.insert(0, BlockQt())
app = types.ModuleType('clearwater.app')
app.__path__ = []
gui = types.ModuleType('clearwater.app.main')
def gui_main(*args):
    raise AssertionError('GUI branch reached')
gui.main = gui_main
workers = []
def worker_main(args):
    workers.append(args)
    return 2
app.export_worker = types.SimpleNamespace(main=worker_main)
sys.modules['clearwater.app'] = app
sys.modules['clearwater.app.main'] = gui
from clearwater import __main__ as entry, gpu_pack
sys.frozen = True
entry.prepend_executable_folder = lambda: False
entry._configure_gpu_caches = lambda: None
entry._start_logging = lambda: None
entry._removal_pending = lambda **kwargs: False
gpu_pack.activate = lambda: None
gpu_pack.pending_removal_path = lambda: None
gpu_pack.pack_root = lambda: None
for arguments in json.loads(sys.argv[1]):
    before = len(workers)
    assert entry.main(['Clearwater.exe', *arguments]) == 2
    assert len(workers) - before == int(arguments == ['--export-worker'])
print('all headless tuples routed safely')
"""
    roots = (
        "APPDATA",
        "LOCALAPPDATA",
        "XDG_CONFIG_HOME",
        "XDG_CACHE_HOME",
        "XDG_DATA_HOME",
        "XDG_STATE_HOME",
        "HOME",
        "USERPROFILE",
    )
    env = {
        **os.environ,
        **{key: str(tmp_path / key) for key in roots},
        "QT_QPA_PLATFORM": "offscreen",
    }
    done = subprocess.run(
        [sys.executable, "-c", code, json.dumps(arguments)],
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert done.returncode == 0, done.stderr
    assert done.stdout == "all headless tuples routed safely\n"


def snapshot(folder):
    return {
        p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in folder.rglob("*")
        if p.is_file()
    }


def _bound_from_readiness(smoke, monkeypatch, marker):
    """Pause this fixture's row clock until ready, with a ten-second startup ceiling."""
    baseline = time.monotonic()
    ready = None

    def now():
        nonlocal ready
        current = time.monotonic()
        if ready is None and marker.exists():
            ready = current
        return baseline + (max(0, current - baseline - 10) if ready is None else current - ready)

    monkeypatch.setattr(smoke, "time", SimpleNamespace(monotonic=now, sleep=time.sleep))


@pytest.fixture
def synthetic(tmp_path, monkeypatch):
    if sys.platform != "win32":
        pytest.skip("Windows onedir artifact fixture")
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
            native_licences_path=release["native_surface"],
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

    def launch(executable, arguments, env):
        # Only substitute the native loader; supervision/capture/env/cwd remain real.
        assert executable.name in {"Clearwater.exe", "ffmpeg.exe", "ffprobe.exe"}
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
        env["STUB_CONFIG"] = str(config_path)
        env["STUB_EXE"] = str(executable)
        # Use the native interpreter directly, not Windows' venv redirector,
        # which adds an unrelated short-lived bootstrap parent to each stub.
        return [sys._base_executable, str(script), *arguments]

    monkeypatch.setattr(smoke, "_command", launch)

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
def test_timeout_and_surviving_child_fail_and_are_reaped(
    synthetic, tmp_path, monkeypatch, mode, message
):
    smoke, release, prepare, config = synthetic
    config["startup_delay"] = 1.25
    _bound_from_readiness(smoke, monkeypatch, Path(config["pid"]))
    prepare(mode)
    with pytest.raises(smoke.SmokeError, match="refuse-command.*" + message):
        smoke.run_smoke(
            release["folder"], out=tmp_path / "out", timeout=1 if mode == "hang" else 10
        )
    pid = int(Path(config["pid"]).read_text())
    assert not psutil.pid_exists(pid)


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
    monkeypatch.setattr(smoke, "_command", forbidden)
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
    assert "6 component rows" in output if not ffmpeg else "10 component rows" in output
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


class RescueJob:
    """Own a separate test job so RED cannot leave a synthetic sleeper behind."""

    def __init__(self):
        from ctypes import wintypes as w

        api = ctypes.WinDLL("kernel32", use_last_error=True)
        api.CreateJobObjectW.argtypes = [ctypes.c_void_p, w.LPCWSTR]
        api.CreateJobObjectW.restype = w.HANDLE
        api.SetInformationJobObject.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD]
        api.CloseHandle.argtypes = [w.HANDLE]
        self.api = api
        self.name = "Local\\ClearwaterSmokeTest-" + uuid.uuid4().hex
        self.handle = api.CreateJobObjectW(None, self.name)
        assert self.handle, ctypes.WinError(ctypes.get_last_error())
        # Windows x64 JOBOBJECT_EXTENDED_LIMIT_INFORMATION: LimitFlags at byte 16.
        limits = ctypes.create_string_buffer(144)
        ctypes.c_uint32.from_buffer(limits, 16).value = 0x2000
        assert api.SetInformationJobObject(self.handle, 9, limits, len(limits)), ctypes.WinError(
            ctypes.get_last_error()
        )

    def close(self):
        if self.handle:
            assert self.api.CloseHandle(self.handle)
            self.handle = None


JOB_STUB = r"""
import ctypes, json, os, subprocess, sys, time
from ctypes import wintypes as w
from pathlib import Path
config = json.loads(Path(os.environ['JOB_CONFIG']).read_text())
api = ctypes.WinDLL('kernel32', use_last_error=True)
api.GetCurrentProcess.restype = w.HANDLE
api.IsProcessInJob.argtypes = [w.HANDLE, w.HANDLE, ctypes.POINTER(w.BOOL)]
inside = w.BOOL()
assert api.IsProcessInJob(api.GetCurrentProcess(), None, ctypes.byref(inside))
Path(config['started']).write_text(json.dumps({'in_job': bool(inside.value)}))
rescue_name = config.get('rescue')
mode = config['mode']
if mode in {'escape', 'pipe-holder'}:
    # The intermediate and venv redirector both disappear before census. The
    # grandchild records its own native PID, avoiding the redirector's PID.
    sleeper = ('import os,time,ctypes,json; from ctypes import wintypes as w; '
               'from pathlib import Path; ')
    if rescue_name:
        # Every sleeper joins the test-owned rescue before it reports its PID.
        # The root/intermediate remain unchanged, preserving the escape chain.
        sleeper += ('a=ctypes.WinDLL("kernel32",use_last_error=True); '
                    'a.OpenJobObjectW.argtypes=[w.DWORD,w.BOOL,w.LPCWSTR]; '
                    'a.OpenJobObjectW.restype=w.HANDLE; '
                    'a.GetCurrentProcess.restype=w.HANDLE; '
                    'a.AssignProcessToJobObject.argtypes=[w.HANDLE,w.HANDLE]; '
                    'h=a.OpenJobObjectW(1,False,' + repr(rescue_name) + '); '
                    'assert h; assert a.AssignProcessToJobObject(h,a.GetCurrentProcess()); '
                    'a.CloseHandle.argtypes=[w.HANDLE]; a.CloseHandle(h); ')
    sleeper += ('k=ctypes.WinDLL("kernel32",use_last_error=True); '
                'k.GetStdHandle.argtypes=[w.DWORD]; k.GetStdHandle.restype=w.HANDLE; '
                'k.GetFileType.argtypes=[w.HANDLE]; '
                'Path(' + repr(config['pipes']) + ').write_text(json.dumps('
                '[k.GetFileType(k.GetStdHandle(n)) for n in (-11,-12)])); '
                'Path(' + repr(config['pid']) + ').write_text(str(os.getpid())); '
                'time.sleep(120)')
    middle = ('import subprocess,sys; subprocess.Popen([sys.executable,"-c",'
              + repr(sleeper) + ']' + (
                ',stdout=sys.stdout,stderr=sys.stderr' if mode == 'pipe-holder' else
                ',stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL') +
                ',close_fds=' + repr(mode != 'pipe-holder') +
                ',creationflags=subprocess.CREATE_NO_WINDOW)')
    subprocess.run([sys.executable, '-c', middle], check=True,
                   stdout=sys.stdout if mode == 'pipe-holder' else subprocess.DEVNULL,
                   stderr=sys.stderr if mode == 'pipe-holder' else subprocess.DEVNULL,
                   close_fds=mode != 'pipe-holder',
                   creationflags=subprocess.CREATE_NO_WINDOW)
    deadline = time.monotonic() + 10
    while not Path(config['pid']).exists():
        assert time.monotonic() < deadline
        time.sleep(.01)
elif mode == 'breakaway':
    try:
        child = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(120)'],
                                 creationflags=(subprocess.CREATE_BREAKAWAY_FROM_JOB |
                                                subprocess.CREATE_NO_WINDOW))
    except OSError as error:
        Path(config['breakaway']).write_text(str(error.winerror))
        print('breakaway denied WinError ' + str(error.winerror), file=sys.stderr)
        sys.exit(72)
    Path(config['pid']).write_text(str(child.pid))
    print('breakaway child created', file=sys.stderr)
    sys.exit(73)
print('Clearwater: -c is not supported', file=sys.stderr)
sys.exit(2)
"""


@pytest.fixture
def job_case(tmp_path, monkeypatch):
    if sys.platform != "win32":
        pytest.skip("Windows Job Object fixture")
    smoke = load_smoke()
    rescue = RescueJob()
    config = {
        "mode": "order",
        "rescue": rescue.name,
        "started": str(tmp_path / "started.json"),
        "pid": str(tmp_path / "pid.txt"),
        "pipes": str(tmp_path / "pipes.json"),
        "breakaway": str(tmp_path / "breakaway.txt"),
    }
    script = tmp_path / "job-stub.py"
    script.write_text(JOB_STUB)
    config_path = tmp_path / "job-config.json"
    monkeypatch.setenv("JOB_CONFIG", str(config_path))
    real_popen = subprocess.Popen

    def command(executable, arguments, env):
        return [sys.executable, str(script), *arguments]

    def legacy_loader(args, **kwargs):
        return real_popen(command(Path(args[0]), args[1:], kwargs["env"]), **kwargs)

    monkeypatch.setattr(smoke.subprocess, "Popen", legacy_loader)
    monkeypatch.setattr(smoke, "_command", command, raising=False)
    # This reproduction explicitly denies PPID observation. The ruled job
    # census must work even when every intermediate is already gone.
    monkeypatch.setattr(smoke, "_snapshot_children", lambda *a: None, raising=False)
    monkeypatch.setattr(smoke, "_live", lambda *a: [], raising=False)
    monkeypatch.setattr(smoke, "_cleanup", lambda *a: None, raising=False)

    def run(mode="order", bound=10):
        config["mode"] = mode
        config_path.write_text(json.dumps(config))
        marker = Path(config["pid"] if mode in {"escape", "pipe-holder"} else config["started"])
        _bound_from_readiness(smoke, monkeypatch, marker)
        results, errors = [], []

        def invoke():
            try:
                results.append(
                    smoke.run_row(
                        tmp_path / "Clearwater.exe",
                        smoke.SmokeRow(
                            "job-" + mode, ("-c", "pass"), "", 2, "Clearwater: -c is not supported"
                        ),
                        root=tmp_path / "profile",
                        timeout=bound,
                    )
                )
            except BaseException as error:
                errors.append(error)

        worker = threading.Thread(target=invoke, daemon=True)
        worker.start()
        startup_deadline = time.monotonic() + 10
        while worker.is_alive() and not marker.exists() and time.monotonic() < startup_deadline:
            time.sleep(0.01)
        worker.join(bound + 2)
        exceeded = worker.is_alive()
        if exceeded:
            rescue.close()  # also releases a mutant's unbounded pipe join
            worker.join(5)
        assert not worker.is_alive(), "row thread survived rescue job close"
        assert not exceeded, "row exceeded its bound while a grandchild held the pipes"
        if errors:
            raise errors[0]
        return results[0]

    try:
        yield smoke, config, run
    finally:
        rescue.close()  # the only RED cleanup kill path is this test's own job
        if Path(config["pid"]).exists():
            pid = int(Path(config["pid"]).read_text())
            deadline = time.monotonic() + 5
            while psutil.pid_exists(pid) and time.monotonic() < deadline:
                time.sleep(0.01)
            assert not psutil.pid_exists(pid)


@pytest.mark.parametrize("mode", ["escape", "pipe-holder"])
def test_job_census_catches_vanished_intermediate_and_bounds_pipe_holder(job_case, mode):
    smoke, config, run = job_case
    error = None
    try:
        run(mode)
    except smoke.SmokeError as caught:
        error = caught
    pid = int(Path(config["pid"]).read_text())
    # pid.txt proves readiness even if job close already killed the grandchild.
    assert error is not None, "row passed after the grandchild reported readiness"
    message = str(error)
    if mode == "pipe-holder":
        assert json.loads(Path(config["pipes"]).read_text()) == [3, 3], (
            "grandchild did not inherit both pipes"
        )
    assert "job-" + mode in message and "SURVIVORS" in message
    assert f"pid={pid}" in message and "image=" in message
    assert "python" in message.lower()
    assert not psutil.pid_exists(pid)


def test_root_is_assigned_to_its_own_job_before_resume(job_case, monkeypatch):
    smoke, config, run = job_case
    assert hasattr(smoke, "_kernel32"), "no native job setup exists"
    api = smoke._kernel32()
    create, resume, create_process = api.CreateJobObjectW, api.ResumeThread, api.CreateProcessW
    jobs = []
    checked = []

    def record_job(*args):
        handle = create(*args)
        jobs.append(handle)
        return handle

    def checked_resume(thread):
        from ctypes import wintypes as w

        api.GetProcessIdOfThread.argtypes = [w.HANDLE]
        api.GetProcessIdOfThread.restype = w.DWORD
        handle = api.OpenProcess(0x1000, False, api.GetProcessIdOfThread(thread))
        try:
            inside = w.BOOL()
            assert api.IsProcessInJob(handle, jobs[-1], ctypes.byref(inside))
            assert inside.value, "root resumed outside the row's own job"
            limits = ctypes.create_string_buffer(144)
            assert api.QueryInformationJobObject(jobs[-1], 9, limits, len(limits), None)
            flags = ctypes.c_uint32.from_buffer(limits, 16).value
            assert flags & 0x2000 and not flags & (0x800 | 0x1000)
            assert not Path(config["started"]).exists(), "root ran before assignment check"
            checked.append(True)
        finally:
            api.CloseHandle(handle)
        return resume(thread)

    def checked_create(*args):
        flags = args[5]
        assert flags & 0x4 and flags & 0x08000000 and flags & 0x80000
        assert not flags & 0x01000000  # no CREATE_BREAKAWAY_FROM_JOB
        return create_process(*args)

    monkeypatch.setattr(api, "CreateJobObjectW", record_job)
    monkeypatch.setattr(api, "ResumeThread", checked_resume)
    monkeypatch.setattr(api, "CreateProcessW", checked_create)
    run()
    assert checked == [True]
    assert json.loads(Path(config["started"]).read_text()) == {"in_job": True}


def test_breakaway_never_produces_a_clean_row(job_case):
    smoke, config, run = job_case
    with pytest.raises(smoke.SmokeError, match=r"job-breakaway.*(?:exit 72|SURVIVORS)"):
        run("breakaway")
    if Path(config["breakaway"]).exists():
        assert Path(config["breakaway"]).read_text() == "5"
    else:
        assert not psutil.pid_exists(int(Path(config["pid"]).read_text()))


@pytest.mark.parametrize(
    "function",
    [
        "CreateJobObjectW",
        "UpdateProcThreadAttribute",
        "CreateProcessW",
        "IsProcessInJob",
        "ResumeThread",
    ],
)
def test_job_creation_or_atomic_assignment_failure_is_named_and_never_runs_root(
    job_case, monkeypatch, function
):
    smoke, config, run = job_case
    assert hasattr(smoke, "_kernel32"), "no native job setup exists"

    def denied(*args):
        ctypes.set_last_error(5)
        return 0xFFFFFFFF if function == "ResumeThread" else 0

    monkeypatch.setattr(smoke._kernel32(), function, denied)
    with pytest.raises(smoke.SmokeError, match=r"job-order.*WinError 5"):
        run()
    assert not Path(config["started"]).exists()


NATIVE_GROUP_ROW = r"""
import subprocess, sys
if sys.argv[1] == "survivor":
    child = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(120)"],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    open(sys.argv[2], "w").write(str(child.pid))
print("export worker: no request document on stdin", file=sys.stderr)
sys.exit(2)
"""


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="native POSIX process-group proof (macOS runner); Windows proves it by stubs",
)
def test_non_windows_containment_never_silently_skips(tmp_path, monkeypatch):
    """darwin contains natively (a clean row; a survivor refused, then killed with its
    group); any other POSIX platform is refused by name, never run uncontained."""
    smoke = load_smoke()
    executable = tmp_path / "Clearwater" / "Clearwater"
    if sys.platform != "darwin":
        with pytest.raises(smoke.SmokeError, match=r"Linux is not a supported build host"):
            smoke._process(executable, [], stdin="", root=tmp_path, timeout=1, name="posix")
        return
    executable.parent.mkdir(parents=True)
    monkeypatch.setattr(
        smoke,
        "_command",
        lambda target, arguments, env: [sys.executable, "-c", NATIVE_GROUP_ROW, *arguments],
    )
    done = smoke._process(
        executable, ["clean"], stdin="", root=tmp_path / "a", timeout=10, name="a"
    )
    assert done.returncode == 2
    assert done.stderr == "export worker: no request document on stdin\n"
    marker = tmp_path / "grandchild.pid"
    with pytest.raises(smoke.SmokeError, match=r"b: SURVIVORS") as refused:
        smoke._process(
            executable,
            ["survivor", str(marker)],
            stdin="",
            root=tmp_path / "b",
            timeout=3,
            name="b",
        )
    pid = int(marker.read_text())
    # WP6.5 run 2: the census lists the live survivor in the message (the runner's log
    # then shows what remained; the cleanup's EPERM, if any, is printed with the listing)
    print(f"row b refused: {refused.value}", flush=True)
    assert f"pid {pid} " in str(refused.value)
    deadline = time.monotonic() + 5

    def gone() -> bool:
        try:
            return psutil.Process(pid).status() == psutil.STATUS_ZOMBIE
        except psutil.NoSuchProcess:
            return True

    while not gone():
        assert time.monotonic() < deadline, "the survivor outlived the group killpg"
        time.sleep(0.05)


# --- macOS process-group containment by stubs (WP6.5; AD-37) ----------------------------

STUB_KILL = 9


class FakeGroup:
    """A scripted process group: ``popen`` and ``killpg`` answer from its state."""

    def __init__(
        self,
        *,
        pid=4242,
        hangs=False,
        survivor=False,
        holds_pipes=False,
        immortal=False,
        zombies=(),
        probe_error=None,
        unsignalable=False,
    ):
        self.pid = pid
        self.root_alive = True
        self.members = survivor or holds_pipes
        self.hangs = hangs
        self.holds_pipes = holds_pipes
        self.immortal = immortal
        self.zombies = list(zombies)  # (pid, stat, comm) rows the census lists as dead
        self.probe_error = probe_error  # an exception the 0-signal probe raises while listed
        self.unsignalable = unsignalable  # the live survivor answers EPERM, never dies
        self.signals: list[tuple[int, int]] = []
        self.popen_calls: list[tuple[list[str], dict]] = []
        self.census_calls: list[int] = []
        self.input = None

    def popen(self, argv, **kwargs):
        self.popen_calls.append((argv, kwargs))
        return FakeProcess(self)

    def killpg(self, pgid, signal):
        assert pgid == self.pid
        self.signals.append((pgid, signal))
        if signal == STUB_KILL and not (self.immortal or self.unsignalable):
            self.root_alive = self.members = False
        if signal == 0 and self.unsignalable and self.members:
            raise PermissionError(1, "Operation not permitted")
        if signal == 0 and self.probe_error is not None and self.zombies:
            raise self.probe_error
        if signal == 0 and not (self.root_alive or self.members or self.zombies):
            raise ProcessLookupError(3, "No such process")

    def census(self, pgid):
        """The ``ps`` listing of the group: the live root and survivor, then the zombies."""
        assert pgid == self.pid
        self.census_calls.append(pgid)
        listed = []
        if self.root_alive:
            listed.append((self.pid, "Ss", "Clearwater"))
        if self.members:
            listed.append((self.pid + 1, "S", "survivor"))
        return [STUB_MEMBER(*row) for row in [*listed, *self.zombies]]


class FakeProcess:
    stdin = stdout = stderr = None

    def __init__(self, group):
        self.group = group
        self.pid = group.pid
        self.returncode = None

    def communicate(self, data, timeout):
        self.group.input = data
        if self.group.hangs:
            raise subprocess.TimeoutExpired("stub", timeout)
        self.group.root_alive = False
        self.returncode = 2
        if self.group.holds_pipes:
            raise subprocess.TimeoutExpired("stub", timeout)
        return b"", b"export worker: no request document on stdin\n"

    def poll(self):
        return None if self.group.root_alive else self.returncode

    def wait(self, timeout):
        if self.group.root_alive:
            raise subprocess.TimeoutExpired("stub", timeout)
        return self.returncode


def run_group(smoke, group, tmp_path, *, timeout=0.05, own_group=77):
    executable = tmp_path / "Clearwater" / "Clearwater"
    executable.parent.mkdir(parents=True, exist_ok=True)
    return smoke._group_contained_process(
        executable,
        ["--export-worker"],
        stdin="request",
        root=tmp_path / "row",
        timeout=timeout,
        name="worker",
        killpg=group.killpg,
        kill_signal=STUB_KILL,
        own_group=own_group,
        census=group.census,
        popen=group.popen,
    )


@pytest.fixture
def darwin_smoke(monkeypatch):
    smoke = load_smoke()
    monkeypatch.setattr(smoke.sys, "platform", "darwin")
    monkeypatch.setattr(smoke, "_GROUP_CLEANUP_SECONDS", 0.05)
    return smoke


def test_group_containment_clean_row_starts_a_new_session_and_censuses(
    darwin_smoke, tmp_path, capsys
):
    """start_new_session, redirected roots, system PATH, census then the bounded killpg."""
    group = FakeGroup()
    done = run_group(darwin_smoke, group, tmp_path)
    assert (done.returncode, done.stdout) == (2, "")
    assert done.stderr == "export worker: no request document on stdin\n"
    ((argv, kwargs),) = group.popen_calls
    assert argv[1:] == ["--export-worker"]
    assert kwargs["start_new_session"] is True
    assert kwargs["cwd"] == str(tmp_path / "Clearwater")
    env = kwargs["env"]
    assert env["HOME"] == str(tmp_path / "row" / "home")
    assert env["TMPDIR"] == env["TEMP"] == str(tmp_path / "row" / "temp")
    assert env["PATH"] == os.pathsep.join(("/usr/bin", "/bin"))
    assert group.input == b"request"
    assert group.signals == [(4242, 0), (4242, STUB_KILL), (4242, 0)]
    assert "worker: group census PASS (0 live processes; new session; group 4242)" in (
        capsys.readouterr().out
    )


@pytest.mark.parametrize(
    "scenario, message",
    [
        (
            {"survivor": True},
            r"worker: SURVIVORS \(process left in group 4242; members: pid 4243 S survivor\)",
        ),
        (
            {"holds_pipes": True},
            r"SURVIVORS \(process group 4242 holds the pipes after root exit; "
            r"members: pid 4243 S survivor\)",
        ),
        ({"hangs": True}, r"worker: timeout after 0\.05 s \(root still alive\)"),
    ],
    ids=["survivor", "survivor-holding-pipes", "root-hangs"],
)
def test_group_containment_fails_by_name_and_kills_the_group(
    darwin_smoke, tmp_path, scenario, message
):
    """Every failure is named, and the whole group gets SIGKILL before the row returns."""
    group = FakeGroup(**scenario)
    with pytest.raises(darwin_smoke.SmokeError, match=message):
        run_group(darwin_smoke, group, tmp_path)
    assert (4242, STUB_KILL) in group.signals
    assert group.signals[-1] == (4242, 0)
    assert not (group.root_alive or group.members)


def test_group_that_survives_killpg_is_a_named_failure(darwin_smoke, tmp_path):
    """The cleanup is bounded: a group that will not die fails the row by name."""
    group = FakeGroup(survivor=True, immortal=True)
    with pytest.raises(
        darwin_smoke.SmokeError,
        match=r"group 4242 did not terminate after killpg \(members: pid 4243 S survivor\)",
    ):
        run_group(darwin_smoke, group, tmp_path)


@pytest.mark.parametrize("pid", [77, 1, 0])
def test_group_containment_never_signals_its_own_or_a_system_group(darwin_smoke, tmp_path, pid):
    """A pid equal to this process's group (or 0 / 1) is refused before any signal."""
    group = FakeGroup(pid=pid)
    with pytest.raises(darwin_smoke.SmokeError, match=f"unsafe process group {pid}"):
        run_group(darwin_smoke, group, tmp_path, own_group=77)
    assert group.signals == []


STUB_MEMBER = collections.namedtuple("STUB_MEMBER", "pid stat comm")
"""A census row as the fake group lists it (the shape of ``smoke.GroupMember``)."""

ZOMBIE = (4250, "Z", "(python3.12)")
"""A dead member not yet reaped: listed by ``ps`` with state ``Z``."""


def test_group_probe_lookup_error_is_an_empty_group_without_a_census(darwin_smoke, tmp_path):
    """WP6.5 run 2 (item 4): ``ProcessLookupError`` from the probe = an empty group; the row
    passes and the census is not needed for it."""
    group = FakeGroup()
    done = run_group(darwin_smoke, group, tmp_path)
    assert done.returncode == 2
    assert group.signals == [(4242, 0), (4242, STUB_KILL), (4242, 0)]
    assert group.census_calls == []


@pytest.mark.parametrize("probe", ["answers", "eperm"])
def test_a_zombie_only_group_is_contained(darwin_smoke, tmp_path, capsys, probe):
    """WP6.5 run 2 (item 4): a zombie is not a survivor. A group whose listing holds only
    zombies is contained whether the probe answers or raises EPERM (macOS's answer for such
    a group, the runner's hypothesis); the EPERM case prints its listing, never silently."""
    error = PermissionError(1, "Operation not permitted") if probe == "eperm" else None
    group = FakeGroup(zombies=[ZOMBIE], probe_error=error)
    done = run_group(darwin_smoke, group, tmp_path)
    assert done.returncode == 2
    assert group.census_calls  # the listing decided, not the probe alone
    out = capsys.readouterr().out
    assert "worker: group census PASS (0 live processes; new session; group 4242)" in out
    if probe == "eperm":
        assert (
            "worker: process group 4242 answers EPERM with no live member "
            "(members: pid 4250 Z (python3.12)): contained"
        ) in out


def test_a_survivor_beside_zombies_is_survivors_with_the_listing(darwin_smoke, tmp_path):
    """WP6.5 run 2 (item 4): one live member among zombies is SURVIVORS, the live member
    and the zombies named in the message; the cleanup then kills the group."""
    group = FakeGroup(survivor=True, zombies=[ZOMBIE])
    with pytest.raises(
        darwin_smoke.SmokeError,
        match=r"worker: SURVIVORS \(process left in group 4242; "
        r"members: pid 4243 S survivor, pid 4250 Z \(python3\.12\)\)",
    ):
        run_group(darwin_smoke, group, tmp_path)
    assert (4242, STUB_KILL) in group.signals


def test_eperm_with_a_live_member_is_the_named_failure(darwin_smoke, tmp_path):
    """WP6.5 run 2 (item 4): EPERM from the probe while the census lists a LIVE member is
    its own named failure ("a member this process may not signal"), carrying the listing."""
    group = FakeGroup(survivor=True, unsignalable=True)
    with pytest.raises(
        darwin_smoke.SmokeError,
        match=r"worker: process group 4242 has a member this process may not signal "
        r"\(EPERM; members: pid 4243 S survivor\)",
    ) as refused:
        run_group(darwin_smoke, group, tmp_path)
    assert isinstance(refused.value.__cause__, PermissionError)


def test_another_probe_oserror_propagates(darwin_smoke, tmp_path):
    """WP6.5 run 2 (item 4): a probe error that is neither ``ProcessLookupError`` nor EPERM
    propagates (never a pass); ``_process`` names it as a containment failure."""
    group = FakeGroup(zombies=[ZOMBIE], probe_error=OSError(5, "Input/output error"))
    with pytest.raises(OSError, match="Input/output error") as raised:
        run_group(darwin_smoke, group, tmp_path)
    assert not isinstance(raised.value, darwin_smoke.SmokeError)
    assert not isinstance(raised.value, (ProcessLookupError, PermissionError))


PS_LISTING = """\
    1     1 Ss   /sbin/launchd
 4086  4086 Z    (python3.12)
 4087  4086 S    /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -c x
 4100  4100 R+   /bin/ps
 4101  4086 Z
"""


def test_group_census_reads_ps_by_group(tmp_path):
    """WP6.5 run 2 (item 4): the census keeps the group's rows of ``/bin/ps -A -o
    pid=,pgid=,stat=,comm=``, zombies included (an empty comm too); an unreadable line or a
    failed ``ps`` is a named error."""
    smoke = load_smoke()
    calls = []

    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0, PS_LISTING, "")

    members = smoke._group_census(4086, run=run)
    assert members == [
        smoke.GroupMember(4086, "Z", "(python3.12)"),
        smoke.GroupMember(
            4087, "S", "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -c x"
        ),
        smoke.GroupMember(4101, "Z", ""),
    ]
    assert [m.pid for m in smoke._live(members)] == [4087]
    assert calls[0][0] == ["/bin/ps", "-A", "-o", "pid=,pgid=,stat=,comm="]
    assert calls[0][1]["timeout"] == 10
    with pytest.raises(smoke.SmokeError, match=r"unreadable /bin/ps line 'x 1 S'"):
        smoke._group_census(
            1, run=lambda argv, **kw: subprocess.CompletedProcess(argv, 0, "x 1 S\n", "")
        )
    with pytest.raises(smoke.SmokeError, match=r"/bin/ps exited 1"):
        smoke._group_census(
            1, run=lambda argv, **kw: subprocess.CompletedProcess(argv, 1, "", "no")
        )


def _smoke_for(monkeypatch, platform):
    monkeypatch.setattr(sys, "platform", platform)
    return load_smoke()


def test_darwin_binds_the_group_containment_to_killpg(monkeypatch, tmp_path):
    """On darwin _contained_process passes os.killpg, SIGKILL and its own group."""
    import signal

    def killpg(pgid, sig):
        raise AssertionError("not reached: the containment is captured")

    monkeypatch.setattr(os, "killpg", killpg, raising=False)
    monkeypatch.setattr(os, "getpgrp", lambda: 31337, raising=False)
    monkeypatch.setattr(signal, "SIGKILL", STUB_KILL, raising=False)
    smoke = _smoke_for(monkeypatch, "darwin")
    seen = {}
    monkeypatch.setattr(smoke, "_group_contained_process", lambda *a, **kw: seen.update(kw))
    smoke._process(
        tmp_path / "Clearwater", ["-c", "pass"], stdin="", root=tmp_path, timeout=1, name="r"
    )
    assert seen["killpg"] is killpg
    assert (seen["kill_signal"], seen["own_group"]) == (STUB_KILL, 31337)
    assert seen["census"] is smoke._group_census
    assert not hasattr(smoke, "_kernel32")


def test_linux_containment_is_refused_by_name(monkeypatch, tmp_path):
    """Linux is not a build host: the smoke refuses rather than run uncontained."""
    smoke = _smoke_for(monkeypatch, "linux")
    with pytest.raises(smoke.SmokeError, match=r"r: process containment .*Linux is not"):
        smoke._process(tmp_path, [], stdin="", root=tmp_path, timeout=1, name="r")


# --- WP6.5 group 2a part 2 (G1-F4): the darwin smoke run path, by stubs --------------------

MACOS_LOCK_FIXTURE = ROOT / "tests" / "ffmpeg_lock" / "ffmpeg-macos.fixture.json"
CCALLBACK_SO = "_ccallback_c.cpython-312-darwin.so"

DARWIN_STUB = r"""
import json, os, sys
from pathlib import Path
config = json.loads(Path(os.environ['STUB_CONFIG']).read_text())
args = sys.argv[1:]
with Path(config['calls']).open('a') as stream:
    stream.write(json.dumps({'exe': os.environ['STUB_EXE'], 'args': args, 'cwd': os.getcwd(),
                             'env': dict(os.environ)}) + '\n')
mode = config.get('mode', '')
if args == ['-version']:
    version = config['version'] if mode != 'version' else 'WRONG'
    print(Path(os.environ['STUB_EXE']).name + ' version ' + version)
    print(config['configure'] if mode != 'configure' else 'configuration: wrong')
    sys.exit(0)
if args == ['-hide_banner', '-encoders']:
    rows = {'': ['hevc_videotoolbox', 'libx265'], 'encoders': ['libx265'],
            'nvenc': ['hevc_nvenc', 'libx265']}[mode if mode in ('encoders', 'nvenc') else '']
    print('\n'.join(' V..... ' + row + ' test' for row in rows))
    sys.exit(0)
if args == ['--export-worker']:
    # any _ccallback_c native present imports (a .pyd-only bundle reaches the target check)
    if not list((Path.cwd().parent / 'Frameworks/scipy/_lib').glob('_ccallback_c*')):
        log = Path(os.environ['HOME']) / 'Library/Application Support/Clearwater'
        log = log / 'logs/clearwater.log'
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
        print(message, file=sys.stderr)
        sys.exit(2)
raise RuntimeError('stub received an unexpected/GUI argument set')
"""


@pytest.fixture
def darwin_app(tmp_path, monkeypatch):
    """A synthetic Clearwater.app smoked under ``sys.platform == "darwin"`` by stubs.

    The darwin process-group containment itself is proved above by FakeGroup and on the
    runner natively; here ``_contained_process`` runs a Python stub in a bounded child so
    the darwin rows, their arguments, roots and expectations are exercised on Windows.
    """
    smoke = load_smoke()
    build = smoke._build_tool()
    lock = json.loads(MACOS_LOCK_FIXTURE.read_text(encoding="utf-8"))
    release = tmp_path / "release"
    app = release / "Clearwater.app"
    files = {
        "Contents/MacOS/Clearwater": b"bootloader",
        "Contents/MacOS/ffmpeg": b"mach-o ffmpeg",
        "Contents/MacOS/ffprobe": b"mach-o ffprobe",
        f"Contents/Frameworks/scipy/_lib/{CCALLBACK_SO}": b"synthetic required worker import",
        "Contents/Resources/ffmpeg-LICENSE.txt": b"GPL text",
        "Contents/Resources/THIRD_PARTY_NOTICES.md": b"NOTICES",
    }
    for name, data in files.items():
        (app / name).parent.mkdir(parents=True, exist_ok=True)
        (app / name).write_bytes(data)
    plans = []
    notices = SimpleNamespace(
        plan_notices=lambda folder: plans.append(folder) or SimpleNamespace(entries=[1], rows=[1]),
        render_notices=lambda plan: b"NOTICES",
    )
    monkeypatch.setattr(smoke, "_notices_tool", lambda: notices)
    monkeypatch.setattr(build, "forbidden_paths", lambda root: [])
    monkeypatch.setattr(build, "forbidden_entries", lambda executable: [])
    monkeypatch.setattr(build, "pack_sources", lambda: pytest.fail("darwin scanned the pack"))
    monkeypatch.setattr(build, "missing_hidden_imports", lambda executable, wanted: [])
    monkeypatch.setattr(build, "load_ffmpeg_lock", lambda: pytest.fail("Windows lock read"))
    monkeypatch.setattr(build, "load_macos_ffmpeg_lock", lambda: lock)
    script = tmp_path / "darwin_stub.py"
    script.write_text(DARWIN_STUB)
    config_path = tmp_path / "stub.json"
    config = {
        "calls": str(tmp_path / "calls.jsonl"),
        "version": lock["version"],
        "configure": lock["configure_line"],
        "refusals": REFUSALS,
    }

    def contained(executable, arguments, *, stdin, root, timeout, name):
        env = smoke._environment(root)
        env["STUB_CONFIG"] = str(config_path)
        env["STUB_EXE"] = str(executable)
        env["SYSTEMROOT"] = os.environ.get("SYSTEMROOT", "")  # the Windows host's interpreter
        return subprocess.run(
            [sys._base_executable, str(script), *arguments],
            input=stdin,
            capture_output=True,
            text=True,
            env=env,
            cwd=str(executable.parent),
            timeout=timeout,
            check=False,
        )

    monkeypatch.setattr(smoke, "_contained_process", contained)
    monkeypatch.setattr(smoke.sys, "platform", "darwin")

    def prepare(mode=""):
        config["mode"] = mode
        config_path.write_text(json.dumps(config))

    prepare()
    return SimpleNamespace(
        smoke=smoke, app=app, release=release, prepare=prepare, config=config, plans=plans
    )


def _calls(case):
    path = Path(case.config["calls"])
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def test_darwin_smoke_runs_every_row_on_the_app_and_preserves_its_bytes(
    darwin_app, tmp_path, capsys
):
    case = darwin_app
    before = snapshot(case.app)
    case.smoke.run_smoke(case.release, out=tmp_path / "out")
    assert snapshot(case.app) == before
    calls = _calls(case)
    macos = case.app / "Contents" / "MacOS"
    assert [call["args"] for call in calls[:10]] == [args for args, _ in REFUSALS]
    assert [Path(call["exe"]) for call in calls[:12]] == [macos / "Clearwater"] * 12
    planted = Path(calls[12]["exe"])
    assert planted.parts[-4:] == ("Clearwater.app", "Contents", "MacOS", "Clearwater")
    assert planted.is_relative_to(tmp_path / "out/smoke") and calls[12]["args"] == [
        "--export-worker"
    ]
    copy = planted.parents[2]
    assert not (copy / f"Contents/Frameworks/scipy/_lib/{CCALLBACK_SO}").exists()
    assert (copy / "Contents/MacOS/ffmpeg").is_file()
    assert [(Path(call["exe"]).name, call["args"]) for call in calls[13:]] == [
        ("ffmpeg", ["-version"]),
        ("ffprobe", ["-version"]),
        ("ffmpeg", ["-hide_banner", "-encoders"]),
    ]
    assert all(Path(call["exe"]).parent == macos for call in calls[13:])
    for call in calls:
        env = call["env"]
        assert env["PATH"] == os.pathsep.join(("/usr/bin", "/bin"))
        assert env["TMPDIR"] == env["TEMP"]
        for key in ("HOME", "TMPDIR", "XDG_CONFIG_HOME", "APPDATA"):
            assert Path(env[key]).is_relative_to(tmp_path / "out/smoke")
    logs = list((tmp_path / "out/smoke").rglob("clearwater.log"))
    assert len(logs) == 1 and logs[0].parts[-6:-1] == (
        "home",
        "Library",
        "Application Support",
        "Clearwater",
        "logs",
    )
    assert case.plans == [macos]
    output = capsys.readouterr().out
    for line in (
        "bundle: PASS",
        "hidden-imports: PASS",
        "notices: PASS",
        "planted-exception-log: PASS",
        "ffmpeg-version: PASS",
        "ffprobe-version: PASS",
        "ffmpeg-encoders: PASS (hevc_videotoolbox; libx265)",
        "smoke: PASS",
    ):
        assert line in output, line


def test_darwin_planted_log_is_the_products_macos_log_path(tmp_path):
    """The smoke's expected log is config.paths' darwin log file under the row's HOME."""
    from clearwater.config.paths import app_locations

    smoke = load_smoke()
    root = tmp_path / "planted-exception"
    expected = app_locations(platform="darwin", home=root / "home").log_file
    assert smoke._macos_log_file(root) == expected


@pytest.mark.parametrize("platform", ["win32", "darwin"])
def test_smoke_encoder_rows_are_the_products_roster(platform):
    """The -encoders row expects exactly the capability code's roster for the platform."""
    from clearwater.io.video.capability import encoder_roster

    assert load_smoke()._SMOKE_ENCODERS[platform] == encoder_roster(platform)


@pytest.mark.parametrize(
    "mode, row",
    [
        ("version", "ffmpeg-version"),
        ("configure", "ffmpeg-version"),
        ("encoders", "ffmpeg-encoders"),
        ("nvenc", "ffmpeg-encoders"),
        ("no-log", "planted-exception"),
    ],
)
def test_darwin_smoke_rows_fail_by_name(darwin_app, tmp_path, mode, row):
    darwin_app.prepare(mode)
    with pytest.raises(darwin_app.smoke.SmokeError, match=row):
        darwin_app.smoke.run_smoke(darwin_app.release, out=tmp_path / "out")


@pytest.mark.parametrize(
    "defect, message",
    [
        ("no-ffmpeg", "FFmpeg: the macOS bundle must carry ffmpeg and ffprobe"),
        ("no-ffprobe", "FFmpeg: the macOS bundle must carry ffmpeg and ffprobe"),
        ("exe-tools", "FFmpeg: the macOS bundle must carry ffmpeg and ffprobe"),
        ("no-so", "worker-empty: exit 1; expected 2"),  # the shipping worker cannot import
        ("two-so", "planted-exception: expected one required scipy._lib._ccallback_c"),
        ("pyd-only", "planted-exception: expected one required scipy._lib._ccallback_c"),
        ("no-notices", "notices: THIRD_PARTY_NOTICES.md is missing"),
        ("notices-in-macos", "notices: THIRD_PARTY_NOTICES.md is missing"),
        ("stale-notices", "notices: document differs"),
        ("no-frameworks", "inputs: the macOS smoke requires the Clearwater.app bundle"),
        ("onedir", "inputs: the macOS smoke requires the Clearwater.app bundle"),
    ],
)
def test_darwin_smoke_fails_closed(darwin_app, tmp_path, defect, message):
    case = darwin_app
    contents = case.app / "Contents"
    so = contents / f"Frameworks/scipy/_lib/{CCALLBACK_SO}"
    notices = contents / "Resources/THIRD_PARTY_NOTICES.md"
    target = case.release
    if defect == "no-ffmpeg":
        (contents / "MacOS/ffmpeg").unlink()
    elif defect == "no-ffprobe":
        (contents / "MacOS/ffprobe").unlink()
    elif defect == "exe-tools":
        for tool in ("ffmpeg", "ffprobe"):
            (contents / "MacOS" / tool).rename(contents / "MacOS" / f"{tool}.exe")
    elif defect == "no-so":
        so.unlink()
    elif defect == "two-so":
        so.with_name("_ccallback_c.cpython-313-darwin.so").write_bytes(b"x")
    elif defect == "pyd-only":
        so.rename(so.with_name("_ccallback_c.cp312-win_amd64.pyd"))
    elif defect == "no-notices":
        notices.unlink()
    elif defect == "notices-in-macos":
        notices.rename(contents / "MacOS/THIRD_PARTY_NOTICES.md")
    elif defect == "stale-notices":
        notices.write_bytes(b"OLD NOTICES")
    elif defect == "no-frameworks":
        shutil.rmtree(contents / "Frameworks")
    else:
        shutil.rmtree(case.app)
        target = tmp_path / "onedir"
        (target / "Clearwater").mkdir(parents=True)
        (target / "Clearwater/Clearwater").write_bytes(b"bootloader")
        (target / "Clearwater/_internal").mkdir()
    with pytest.raises(case.smoke.SmokeError, match=re.escape(message)):
        case.smoke.run_smoke(target, out=tmp_path / "out")
    if defect in {"no-notices", "notices-in-macos", "stale-notices", "no-frameworks", "onedir"}:
        assert _calls(case) == []


def test_darwin_planted_exception_never_deletes_through_a_link(darwin_app, tmp_path, monkeypatch):
    """A .so reached through a link is refused before the copy is touched."""
    case = darwin_app
    so = case.app / f"Contents/Frameworks/scipy/_lib/{CCALLBACK_SO}"
    real = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda self: self.name == CCALLBACK_SO or real(self))
    with pytest.raises(case.smoke.SmokeError, match="planted-exception: expected one required"):
        case.smoke.run_smoke(case.release, out=tmp_path / "out")
    assert so.is_file()


def test_smoke_on_linux_is_refused_by_name(monkeypatch, tmp_path):
    smoke = _smoke_for(monkeypatch, "linux")
    with pytest.raises(smoke.SmokeError, match=r"platform: .*Linux is not a supported build host"):
        smoke.run_smoke(tmp_path, out=tmp_path / "out")
