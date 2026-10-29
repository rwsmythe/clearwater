"""WP4.3a: one windowless, FFREPORT-free launch policy for every product tool child."""

from __future__ import annotations

import ast
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
    """Resolve normal and aliased imports used by the spawn-policy AST checks."""
    names = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names[alias.asname or alias.name.split(".")[0]] = (
                    alias.name if alias.asname else alias.name.split(".")[0]
                )
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            for alias in node.names:
                names[alias.asname or alias.name] = f"{node.module}.{alias.name}"
    return names


def _qualified(node: ast.expr, names: dict[str, str]) -> str:
    """Return an expression's imported dotted name, or an empty string."""
    if isinstance(node, ast.Name):
        return names.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        return f"{_qualified(node.value, names)}.{node.attr}"
    return ""


def _spawn_calls(tree: ast.Module) -> list[ast.Call]:
    """Find subprocess run/Popen calls, including module and direct-import aliases."""
    names = _bindings(tree)
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and _qualified(node.func, names) in {"subprocess.run", "subprocess.Popen"}
    ]


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
    assert count > 0
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
