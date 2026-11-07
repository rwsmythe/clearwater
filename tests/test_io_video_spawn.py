"""WP4.3a: one windowless, FFREPORT-free launch policy for every product tool child."""

from __future__ import annotations

import ast
import importlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from clearwater.io.video import capability, pipes

SRC = Path(__file__).resolve().parents[1] / "src" / "clearwater"
PIPES = SRC / "io" / "video" / "pipes.py"
HELPER = "clearwater.io.video.pipes.tool_spawn_kwargs"


def _bindings(tree: ast.Module) -> dict[str, str]:
    """Resolve imports and chains of bound launch callables for the AST guard."""
    names = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names[alias.asname or alias.name.split(".")[0]] = (
                    alias.name if alias.asname else alias.name.split(".")[0]
                )
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            for alias in node.names:
                if alias.name == "*":
                    names.update(
                        {
                            name: f"{module}.{name}"
                            for module, name in _SPAWN_APIS
                            if module == node.module
                        }
                    )
                else:
                    names[alias.asname or alias.name] = f"{node.module}.{alias.name}"
    assignments = [node for node in ast.walk(tree) if isinstance(node, (ast.Assign, ast.AnnAssign))]
    for _ in range(len(assignments) + 1):
        changed = False
        for node in assignments:
            value = _qualified(node.value, names) if node.value is not None else ""
            if value.split(".")[0] not in {"subprocess", "os", "asyncio", "functools"}:
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, (ast.Name, ast.Attribute)):
                    target_name = ast.unparse(target)
                else:
                    continue
                if names.get(target_name) != value:
                    names[target_name] = value
                    changed = True
        if not changed:
            break
    return names


def _qualified(node: ast.expr, names: dict[str, str]) -> str:
    """Resolve dotted, getattr and partial callable references conservatively."""
    if isinstance(node, ast.Name):
        return names.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        qualified = f"{_qualified(node.value, names)}.{node.attr}"
        return names.get(qualified, qualified)
    if isinstance(node, ast.Call):
        function = _qualified(node.func, names)
        if function == "getattr" and len(node.args) >= 2:
            attribute = node.args[1]
            name = attribute.value if isinstance(attribute, ast.Constant) else "*"
            return f"{_qualified(node.args[0], names)}.{name}"
        if function == "functools.partial" and node.args:
            return _qualified(node.args[0], names)
    return ""


def _is_spawn(name: str) -> bool:
    """Identify process-launch APIs, including dynamic lookups of launch modules."""
    module, _, member = name.rpartition(".")
    if module == "subprocess":
        return member in {
            "run",
            "Popen",
            "call",
            "check_call",
            "check_output",
            "getoutput",
            "getstatusoutput",
            "*",
        }
    if module == "os":
        return member in {"system", "popen", "posix_spawn", "startfile", "*"} or member.startswith(
            ("spawn", "exec")
        )
    return module in {"asyncio", "asyncio.subprocess"} and (
        member.startswith("create_subprocess_") or member == "*"
    )


def _spawn_calls(tree: ast.Module) -> list[ast.Call]:
    """Find launches and launch-callable factories, even behind bound/imported aliases."""
    names = _bindings(tree)
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and (_is_spawn(_qualified(node.func, names)) or _is_spawn(_qualified(node, names)))
    ]


_SPAWN_APIS = (
    [
        ("subprocess", name)
        for name in (
            "run",
            "Popen",
            "call",
            "check_call",
            "check_output",
            "getoutput",
            "getstatusoutput",
        )
    ]
    + [
        ("os", name)
        for name in (
            "system",
            "popen",
            "posix_spawn",
            "startfile",
            "spawnl",
            "spawnle",
            "spawnlp",
            "spawnlpe",
            "spawnv",
            "spawnve",
            "spawnvp",
            "spawnvpe",
            "execl",
            "execle",
            "execlp",
            "execlpe",
            "execv",
            "execve",
            "execvp",
            "execvpe",
        )
    ]
    + [
        (module, name)
        for module in ("asyncio", "asyncio.subprocess")
        for name in ("create_subprocess_exec", "create_subprocess_shell")
    ]
)


@pytest.mark.parametrize(("module", "name"), _SPAWN_APIS)
@pytest.mark.parametrize(
    "form",
    ["direct", "module-alias", "from-alias", "bound", "attribute-bound", "getattr", "partial"],
)
def test_spawn_guard_detects_planted_bypasses(module: str, name: str, form: str) -> None:
    """Every supported launch spelling must be visible to the product-policy guard."""
    source = {
        "direct": f"import {module}\n{module}.{name}('tool')",
        "module-alias": f"import {module} as mod\nmod.{name}('tool')",
        "from-alias": f"from {module} import {name} as child\nchild('tool')",
        "bound": f"import {module}\nchild = {module}.{name}\nagain = child\nagain('tool')",
        "attribute-bound": f"import {module}\nself.child = {module}.{name}\nself.child('tool')",
        "getattr": f"import {module} as mod\ngetattr(mod, '{name}')('tool')",
        "partial": (
            f"import {module} as mod\nfrom functools import partial as bind\n"
            f"child = bind(mod.{name}, 'tool')\nchild()"
        ),
    }[form]
    assert _spawn_calls(ast.parse(source)), f"guard missed {form}: {module}.{name}"


@pytest.mark.parametrize(("module", "name"), _SPAWN_APIS)
def test_spawn_guard_detects_recognized_star_imports(module: str, name: str) -> None:
    """R2-1: star-imported names from the finite recognized API set cannot bypass the guard."""
    assert _spawn_calls(ast.parse(f"from {module} import *\n{name}('tool')"))


@pytest.mark.parametrize(
    "statement",
    [
        'kw["creationflags"] = 1',
        'kw["creationflags"]: int = 1',
        'kw["creationflags"] |= 1',
    ],
)
def test_flag_guard_rejects_subscript_stores(tmp_path: Path, monkeypatch, statement: str) -> None:
    """R2-1: a flag stored through a dict subscript outside the helper is rejected."""
    helper = tmp_path / "pipes.py"
    helper.write_text('def tool_spawn_kwargs():\n return {"creationflags": 0}\n', encoding="utf-8")
    (tmp_path / "bypass.py").write_text(f"kw = {{}}\n{statement}\n", encoding="utf-8")
    monkeypatch.setitem(globals(), "SRC", tmp_path)
    monkeypatch.setitem(globals(), "PIPES", helper)
    with pytest.raises(AssertionError, match="creationflags outside helper"):
        test_only_the_helper_sets_creationflags()


def test_every_product_spawn_uses_the_helper() -> None:
    """A forgotten launch site must fail even when it uses an import alias."""
    planted = ast.parse(
        "import subprocess as sp\n"
        "from subprocess import Popen as child\n"
        "sp.run(['tool'])\n"
        "child(['tool'])\n"
    )
    assert len(_spawn_calls(planted)) == 2
    offenders, count = [], 0
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = _bindings(tree)
        for call in _spawn_calls(tree):
            count += 1
            uses_helper = any(
                keyword.arg is None
                and isinstance(keyword.value, ast.Call)
                and _qualified(keyword.value.func, names) == HELPER
                for keyword in call.keywords
            )
            overrides_policy = any(
                keyword.arg in {"env", "creationflags"} for keyword in call.keywords
            )
            if not uses_helper or overrides_policy:
                offenders.append(f"{path.relative_to(SRC).as_posix()}:{call.lineno}")
    assert count == 8, f"expected the eight ruled product spawn sites, found {count}"
    assert not offenders, f"product spawns bypassing the shared policy: {offenders}"


def test_only_the_helper_sets_creationflags() -> None:
    """Window flags must be constructed once, inside the pipes helper only."""
    setters = []
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        helpers = [
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "tool_spawn_kwargs"
        ]
        allowed = set(ast.walk(helpers[0])) if path == PIPES and len(helpers) == 1 else set()
        for node in ast.walk(tree):
            sets_flag = isinstance(node, ast.keyword) and node.arg == "creationflags"
            if isinstance(node, ast.Subscript) and isinstance(node.ctx, ast.Store):
                sets_flag = (
                    isinstance(node.slice, ast.Constant) and node.slice.value == "creationflags"
                )
            if isinstance(node, ast.Dict):
                sets_flag = any(
                    isinstance(key, ast.Constant) and key.value == "creationflags"
                    for key in node.keys
                )
            if sets_flag:
                assert node in allowed, f"creationflags outside helper: {path}:{node.lineno}"
                setters.append(node)
    assert len(setters) == 1, "the helper must own the single creationflags setting"


def test_spawn_kwargs_windows_and_other_platforms(monkeypatch: pytest.MonkeyPatch) -> None:
    """Both platform branches clear FFREPORT without changing the parent or other values."""
    helper = getattr(pipes, "tool_spawn_kwargs", None)
    assert callable(helper), "pipes must expose the shared spawn policy"
    parent = {"PATH": "task-path", "KEEP": "retained", "FFREPORT": "a", "FfRePoRt": "b"}
    monkeypatch.setattr(os, "environ", parent)
    native = helper()
    expected_flag = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    assert native["creationflags"] == expected_flag
    assert native["env"] == {"PATH": "task-path", "KEEP": "retained"}
    with monkeypatch.context() as other:
        other.setattr(pipes.sys, "platform", "linux")
        portable = helper()
    assert portable["creationflags"] == 0
    assert portable["env"] == {"PATH": "task-path", "KEEP": "retained"}
    assert parent == {"PATH": "task-path", "KEEP": "retained", "FFREPORT": "a", "FfRePoRt": "b"}
    native["env"]["KEEP"] = "changed copy"
    assert portable["env"]["KEEP"] == "retained"
    assert helper()["env"]["KEEP"] == "retained"


def test_tool_env_delegates_to_spawn_helper(monkeypatch: pytest.MonkeyPatch) -> None:
    """The compatibility function must consume the same environment policy as launches."""
    wanted = {"KEEP": "shared policy"}

    def policy():
        return {"creationflags": 0, "env": wanted}

    monkeypatch.setattr(capability, "tool_spawn_kwargs", policy, raising=False)
    delegated = capability.tool_env() is wanted
    assert delegated, "tool_env must return the helper's environment"


@pytest.mark.parametrize("tool", ["ffmpeg", "ffprobe"])
@pytest.mark.usefixtures("ffmpeg_tools")
def test_ffreport_parent_does_not_make_a_child_report(
    tool: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Real tools write the positive-control report but never a policy-protected report."""
    executable = shutil.which(tool)
    assert executable is not None, f"{tool} is required for the FFREPORT regression"
    command = [executable, "-version"]
    monkeypatch.setenv("FFREPORT", "file=inherited-report.log:level=32")
    subprocess.run(command, cwd=tmp_path, capture_output=True, check=True, timeout=30)
    inherited = tmp_path / "inherited-report.log"
    assert inherited.is_file() and inherited.stat().st_size > 0, "positive control wrote no report"
    monkeypatch.setenv("FFREPORT", "file=protected-report.log:level=32")
    helper = getattr(pipes, "tool_spawn_kwargs", None)
    assert callable(helper), "the protected child needs the shared spawn policy"
    subprocess.run(command, cwd=tmp_path, capture_output=True, check=True, timeout=30, **helper())
    assert not (tmp_path / "protected-report.log").exists()
    assert sorted(path.name for path in tmp_path.iterdir()) == ["inherited-report.log"]


@pytest.mark.parametrize("limit", [None, 17])
def test_packet_listing_timeout_omits_tool_path(tmp_path: Path, monkeypatch, limit) -> None:
    """DR-81 (c): report the input name and current limit, never the ffprobe command."""
    verify = importlib.import_module("clearwater.io.video.verify")
    tool = tmp_path / "private-tools" / "ffprobe.exe"
    source = tmp_path / "private-inputs" / "input-\u00e9.mp4"
    monkeypatch.setattr(verify, "find_tool", lambda name: tool)
    if limit is not None:
        monkeypatch.setattr(verify, "READ_TIMEOUT_S", limit)

    def timeout(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr(verify.subprocess, "run", timeout)
    with pytest.raises(verify.VideoProbeError) as caught:
        verify._listing(source, ["-show_packets"], strict=True)
    text = str(caught.value)
    assert r"input-\xe9.mp4" in text and f"{verify.READ_TIMEOUT_S} s" in text
    assert "private-tools" not in text and "private-inputs" not in text
    assert str(tool) not in text and "-show_packets" not in text and text.isascii()


@pytest.mark.parametrize("limit", [None, 19])
def test_cuda_check_timeout_omits_command(tmp_path: Path, monkeypatch, limit) -> None:
    """DR-81 (d): CUDA probe timeout text uses its configured limit, not its command."""
    decode = importlib.import_module("clearwater.io.video.decode")
    tool = tmp_path / "private-tools" / "ffmpeg.exe"
    monkeypatch.setattr(decode, "find_tool", lambda name: tool)
    if limit is not None:
        monkeypatch.setattr(decode, "CUDA_CHECK_TIMEOUT_S", limit)

    def timeout(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr(decode.subprocess, "run", timeout)
    available, text = decode._check_cuda()
    assert not available and f"{decode.CUDA_CHECK_TIMEOUT_S} s" in text
    assert "private-tools" not in text and str(tool) not in text
    assert "-init_hw_device" not in text and text.isascii()


def test_cuda_check_oserror_omits_filename(tmp_path: Path, monkeypatch) -> None:
    """DR-81 (d): a spawn failure exposes its class and strerror, without filename."""
    decode = importlib.import_module("clearwater.io.video.decode")
    tool = tmp_path / "private-tools" / "ffmpeg.exe"
    monkeypatch.setattr(decode, "find_tool", lambda name: tool)

    def refused(command, **kwargs):
        raise FileNotFoundError(2, "tool unavailable", str(tool))

    monkeypatch.setattr(decode.subprocess, "run", refused)
    available, text = decode._check_cuda()
    assert not available
    assert text == "FileNotFoundError: tool unavailable"


def test_cuda_check_oserror_without_strerror_has_readable_fallback(
    tmp_path: Path, monkeypatch
) -> None:
    """F9: an absent strerror must use readable fixed text without exception paths."""
    decode = importlib.import_module("clearwater.io.video.decode")
    tool = tmp_path / "private-tools" / "ffmpeg.exe"
    monkeypatch.setattr(decode, "find_tool", lambda name: tool)

    def refused(command, **kwargs):
        raise OSError(5, None, str(tool))

    monkeypatch.setattr(decode.subprocess, "run", refused)
    available, text = decode._check_cuda()
    assert not available
    assert text == "OSError: an operating-system error"
