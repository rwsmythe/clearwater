"""Headless release checks against synthetic archives and Python process stubs only."""

from __future__ import annotations

import ctypes
import hashlib
import importlib.util
import json
import os
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


@pytest.mark.skipif(
    sys.platform == "win32", reason="POSIX process-group native proof belongs to WP6.5"
)
def test_non_windows_containment_never_silently_skips(tmp_path):
    smoke = load_smoke()
    with pytest.raises(smoke.SmokeError, match=r"WP6\.5"):
        smoke._process(tmp_path / "unused", [], stdin="", root=tmp_path, timeout=1, name="posix")
