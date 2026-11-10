"""Offline release-workflow contracts; actionlint and a real run belong to the seat.

The indentation checks deliberately cover this workflow's small YAML surface without
adding a YAML dependency. The embedded Python version gate is executed, not emulated.
No test calls a product entry point, builds an artifact or contacts GitHub.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import re
import shlex
import subprocess
import sys
import textwrap
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/release.yml"
MACOS_WORKFLOW = Path(
    os.environ.get("WP65_MACOS_WORKFLOW", ROOT / ".github/workflows/macos-build.yml")
)
PINS = {
    "actions/checkout": "11bd71901bbe5b1630ceea73d27597364c9af683",
    "astral-sh/setup-uv": "6b9c6063abd6010835644d4c2e1bef4cf5cd0fca",
    "actions/upload-artifact": "ea165f8d65b6e75b540449e92b4886f43607fa02",
    "actions/download-artifact": "d3f86a106a0bac45b974a628896c90dbdf5c8093",
    "softprops/action-gh-release": "72f2c25fcb47643c292f7107632f7a47c1df5cd8",
}


@pytest.fixture
def workflow():
    return WORKFLOW.read_text(encoding="utf-8") if WORKFLOW.is_file() else ""


def test_workflow_is_present(workflow):
    assert workflow, "the release workflow has not been implemented"


def step(workflow, name):
    match = re.search(
        rf"^      - name: {re.escape(name)}\n(.*?)(?=^      - |\Z)",
        workflow,
        re.MULTILINE | re.DOTALL,
    )
    assert match, f"missing workflow step {name}"
    return match[1]


def script(workflow, name):
    body = step(workflow, name).split("        run: |\n", 1)[1]
    return textwrap.dedent(body.rstrip())


def job(workflow, name):
    """One job's text: from its two-space header to the next job header (or the end)."""
    match = re.search(
        rf"^  {re.escape(name)}:\n(.*?)(?=^  [a-z][\w-]*:\n|\Z)",
        workflow,
        re.MULTILINE | re.DOTALL,
    )
    assert match, f"missing workflow job {name}"
    return match[1]


def test_every_action_is_one_of_the_seat_verified_sha_pins(workflow):
    uses = re.findall(r"^\s+(?:- )?uses: (\S+)", workflow, re.MULTILINE)
    # WP6.5: the macos job calls the repository's own reusable workflow (no ref to pin).
    assert [value for value in uses if value.startswith("./")] == [
        "./.github/workflows/macos-build.yml"
    ]
    uses = [value for value in uses if not value.startswith("./")]
    assert len(uses) == 7  # checkout in each job, a download per platform, the other three
    assert {value.split("@")[0] for value in uses} == set(PINS)
    for value in uses:
        action, sha = value.split("@")
        assert re.fullmatch(r"[a-f0-9]{40}", sha)
        assert sha == PINS[action]
    assert workflow.count("persist-credentials: false") == 2
    assert set(re.findall(r"secrets\.([\w]+)", workflow)) <= {"GITHUB_TOKEN"}


def test_setup_uv_pins_the_audited_uv_release(workflow):
    setup = step(workflow, "Set up uv")
    versions = re.findall(r'^          version: "([^"]+)"$', setup, re.MULTILINE)
    assert len(versions) == 1, "setup-uv must pin its version input"
    assert re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", versions[0])
    assert versions[0] == "0.10.9", "uv must match the audited laptop build input"


def test_setup_uv_disables_cache_and_verifies_the_seat_fetched_checksum(workflow):
    setup = step(workflow, "Set up uv")
    assert "enable-cache: false" in setup
    assert "checksum: f58dc40896000229db7c52b8bdd931394040ef2ad59abd1eda841f6d70b13d7a" in setup


def _git_stdout(args, tag_type="tag", peeled="a" * 40):
    """Supply Git output without importing Clearwater or contacting a remote."""
    if args[1:3] == ["cat-file", "-t"]:
        return tag_type
    if args[1:3] == ["cat-file", "tag"]:
        return (
            f"object {peeled}\ntype commit\ntag v1.1.0\n"
            "tagger Release test <release-test@example.invalid> 1700000000 +0000\n"
            "\nRelease 1.1.0\n"
        )
    if args[1] == "rev-parse":
        return peeled
    return ""


@pytest.mark.parametrize(
    "tag_type, peeled, allowed",
    [("tag", "a" * 40, True), ("commit", "a" * 40, False), ("tag", "b" * 40, False)],
)
def test_release_requires_annotated_tag_at_the_built_commit(
    workflow, tmp_path, monkeypatch, tag_type, peeled, allowed
):
    monkeypatch.setenv("GITHUB_REF", "refs/tags/v1.1.0")
    monkeypatch.setenv("GITHUB_SHA", "a" * 40)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_OUTPUT", str(tmp_path / "output"))
    monkeypatch.setitem(sys.modules, "clearwater", SimpleNamespace(__version__="1.1.0"))
    calls = []

    def git(args, **kwargs):
        assert kwargs == {"capture_output": True, "text": True, "check": True, "timeout": 30}
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, _git_stdout(args, tag_type, peeled), "")

    monkeypatch.setattr(subprocess, "run", git)
    code = compile(script(workflow, "Check release version"), "release-tag-gate", "exec")
    if allowed:
        exec(code, {})
        assert calls == [
            [
                "git",
                "-c",
                "http.lowSpeedLimit=1",
                "-c",
                "http.lowSpeedTime=20",
                "fetch",
                "--force",
                "--no-tags",
                "origin",
                "+refs/tags/v1.1.0:refs/tags/v1.1.0",
            ],
            ["git", "cat-file", "-t", "refs/tags/v1.1.0"],
            ["git", "cat-file", "tag", "refs/tags/v1.1.0"],
            ["git", "rev-parse", "refs/tags/v1.1.0^{commit}"],
        ]
    else:
        with pytest.raises(SystemExit):
            exec(code, {})
    assert "fetch-depth: 0" in step(workflow, "Checkout tagged source")


@pytest.mark.parametrize("tag_headers", ["tag v1.0.9", "", "tag v1.1.0\ntag v1.0.9"])
def test_tag_gate_refuses_wrong_or_missing_object_name(
    workflow, tmp_path, monkeypatch, tag_headers
):
    """A matching name in the message cannot substitute for the object's header."""
    output = tmp_path / "output"
    monkeypatch.setenv("GITHUB_REF", "refs/tags/v1.1.0")
    monkeypatch.setenv("GITHUB_SHA", "a" * 40)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setitem(sys.modules, "clearwater", SimpleNamespace(__version__="1.1.0"))

    def git(args, **kwargs):
        stdout = _git_stdout(args)
        if args[1:3] == ["cat-file", "tag"]:
            stdout = (
                f"object {'a' * 40}\ntype commit\n{tag_headers}\n"
                "tagger Release test <release-test@example.invalid> 1700000000 +0000\n"
                "\ntag v1.1.0\n"
            )
        return subprocess.CompletedProcess(args, 0, stdout, "")

    monkeypatch.setattr(subprocess, "run", git)
    code = compile(script(workflow, "Check release version"), "release-tag-name", "exec")
    with pytest.raises(
        SystemExit, match=re.escape("Annotated tag object's name does not match release tag v1.1.0")
    ):
        exec(code, {})
    assert not output.exists()


@pytest.mark.parametrize(
    "command,failure",
    [
        (
            ["fetch", "--force", "--no-tags", "origin", "+refs/tags/v1.1.0:refs/tags/v1.1.0"],
            "Release tag v1.1.0 could not be fetched from origin (missing or unavailable)",
        ),
        (
            ["cat-file", "-t", "refs/tags/v1.1.0"],
            "Cannot determine object type for release tag v1.1.0",
        ),
        (
            ["cat-file", "tag", "refs/tags/v1.1.0"],
            "Cannot read annotated object for release tag v1.1.0",
        ),
        (["rev-parse", "refs/tags/v1.1.0^{commit}"], "Cannot peel release tag v1.1.0 to a commit"),
    ],
    ids=["fetch", "object-type", "tag-object", "peel"],
)
@pytest.mark.parametrize("error", ["exit", "timeout", "os-error"])
def test_tag_gate_git_failures_are_named_refusals(
    workflow, tmp_path, monkeypatch, command, failure, error
):
    """Each Git failure path must stop publication without a process traceback."""
    output = tmp_path / "output"
    monkeypatch.setenv("GITHUB_REF", "refs/tags/v1.1.0")
    monkeypatch.setenv("GITHUB_SHA", "a" * 40)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setitem(sys.modules, "clearwater", SimpleNamespace(__version__="1.1.0"))
    reached = []

    def git(args, **kwargs):
        if args[-len(command) :] == command:
            reached.append(True)
            if error == "exit":
                raise subprocess.CalledProcessError(
                    128, args, stderr="earlier diagnostic\nfatal: planted failure\n \n"
                )
            if error == "timeout":
                raise subprocess.TimeoutExpired(
                    args, 30, stderr=b"earlier diagnostic\nfatal: planted timeout\n \n"
                )
            raise OSError("planted launch failure")
        return subprocess.CompletedProcess(args, 0, _git_stdout(args), "")

    monkeypatch.setattr(subprocess, "run", git)
    code = compile(script(workflow, "Check release version"), "release-git-failure", "exec")
    with pytest.raises(SystemExit) as refused:
        exec(code, {})
    assert reached == [True]
    assert str(refused.value).startswith(failure)
    if error != "os-error":
        assert str(refused.value).endswith(
            "fatal: planted " + ("failure" if error == "exit" else "timeout")
        )
        assert "earlier diagnostic" not in str(refused.value)
        assert "\n" not in str(refused.value)
    assert refused.value.__suppress_context__
    assert not output.exists()


def test_tag_gate_bounds_git_stderr_line(workflow, tmp_path, monkeypatch):
    """A large Git diagnostic keeps the final line within a bounded refusal."""
    monkeypatch.setenv("GITHUB_REF", "refs/tags/v1.1.0")
    monkeypatch.setitem(sys.modules, "clearwater", SimpleNamespace(__version__="1.1.0"))

    def git(args, **kwargs):
        raise subprocess.CalledProcessError(128, args, stderr="older\n" + "x" * 1000 + " END\n\n")

    monkeypatch.setattr(subprocess, "run", git)
    with pytest.raises(SystemExit) as error:
        exec(compile(script(workflow, "Check release version"), "release-stderr", "exec"), {})
    message = str(error.value)
    assert "could not be fetched" in message and message.endswith(" END")
    assert len(message) < 700 and "older" not in message and "\n" not in message


@pytest.mark.parametrize(
    "case", ["annotated", "lightweight", "wrong-commit", "mismatched-name", "deleted-origin"]
)
def test_real_git_gate_restores_checkout_overwrite_and_refuses_invalid_tags(
    workflow, tmp_path, case
):
    """Run the actual gate after checkout's forced tag-to-commit refspec."""
    env = {
        key: value for key, value in os.environ.items() if not key.startswith(("GIT_", "PYTHON"))
    }
    empty_config = tmp_path / "empty-config"
    empty_config.touch()
    templates = tmp_path / "templates"
    templates.mkdir()
    env.update(
        GIT_CONFIG_GLOBAL=str(empty_config),
        GIT_CONFIG_SYSTEM=str(empty_config),
        GIT_CONFIG_NOSYSTEM="1",
        GIT_TEMPLATE_DIR=str(templates),
        GIT_TERMINAL_PROMPT="0",
        GIT_AUTHOR_NAME="Release test",
        GIT_AUTHOR_EMAIL="release-test@example.invalid",
        GIT_COMMITTER_NAME="Release test",
        GIT_COMMITTER_EMAIL="release-test@example.invalid",
        GIT_ALLOW_PROTOCOL="file",
    )

    def git(cwd, *args):
        return subprocess.run(
            ["git", *args],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        ).stdout.strip()

    origin = tmp_path / "origin.git"
    seed = tmp_path / "seed"
    clone = tmp_path / "clone"
    git(tmp_path, "init", "--bare", str(origin))
    git(tmp_path, "init", str(seed))
    git(seed, "commit", "--allow-empty", "-m", "first")
    target = git(seed, "rev-parse", "HEAD")
    git(seed, "tag", "-a", "v1.1.0", "-m", "Release 1.1.0")
    git(seed, "tag", "v1.1.1")
    git(seed, "tag", "unrelated")
    git(seed, "commit", "--allow-empty", "-m", "second")
    other = git(seed, "rev-parse", "HEAD")
    git(seed, "remote", "add", "origin", str(origin))
    git(seed, "push", "origin", "HEAD:refs/heads/main", "--tags")
    git(tmp_path, "clone", "--branch", "main", str(origin), str(clone))
    unrelated_before = git(clone, "rev-parse", "refs/tags/unrelated")
    assert unrelated_before == target
    # The gate may refresh only its requested tag, never another release's ref.
    git(seed, "tag", "--force", "unrelated", other)
    git(seed, "push", "--force", "origin", "refs/tags/unrelated")
    assert git(origin, "rev-parse", "refs/tags/unrelated") == other
    ref = "refs/tags/v1.1.1" if case == "lightweight" else "refs/tags/v1.1.0"
    if case != "lightweight":
        assert git(clone, "cat-file", "-t", ref) == "tag"
    # Reproduce actions/checkout's overwrite, not an approximation of the gate.
    git(clone, "fetch", "--no-tags", "origin", f"+{target}:{ref}")
    assert git(clone, "cat-file", "-t", ref) == "commit"
    git(clone, "checkout", "--detach", target)
    if case == "mismatched-name":
        git(seed, "tag", "-a", "v1.0.9", target, "-m", "Another release")
        wrong_name = git(seed, "rev-parse", "refs/tags/v1.0.9")
        git(seed, "update-ref", ref, wrong_name)
        git(seed, "push", "--force", "origin", ref)
    elif case == "deleted-origin":
        git(seed, "push", "origin", f":{ref}")
    gate = clone / "version-gate.py"
    gate.write_text(script(workflow, "Check release version"), encoding="utf-8")
    # Only supply the package version: this never imports a product entry point.
    (clone / "clearwater.py").write_text('__version__ = "1.1.0"\n', encoding="utf-8")
    output = tmp_path / "output"
    env.update(
        GITHUB_REF=ref,
        GITHUB_SHA=other if case == "wrong-commit" else target,
        GITHUB_EVENT_NAME="push",
        REQUESTED_VERSION="",
        GITHUB_OUTPUT=str(output),
    )
    result = subprocess.run(
        [sys.executable, str(gate)],
        cwd=clone,
        env=env,
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )
    if case == "annotated":
        assert result.returncode == 0, result.stdout + result.stderr
        assert output.read_text() == "version=1.1.0\n"
        assert git(clone, "cat-file", "-t", ref) == "tag"
        assert git(clone, "rev-parse", ref + "^{commit}") == target
    else:
        assert result.returncode != 0
        expected = {
            "lightweight": "Release requires an ANNOTATED tag",
            "wrong-commit": "Annotated tag does not peel to the built commit",
            "mismatched-name": "Annotated tag object's name does not match release tag v1.1.0",
            "deleted-origin": (
                "Release tag v1.1.0 could not be fetched from origin (missing or unavailable)"
            ),
        }[case]
        assert expected in result.stderr
        assert not output.exists()
    assert "Traceback" not in result.stderr
    assert "CalledProcessError" not in result.stderr
    assert git(clone, "rev-parse", "refs/tags/unrelated") == unrelated_before


def test_sidecar_and_draft_body_record_the_built_commit(workflow):
    stage = script(workflow, "Stage release assets")
    assert 'Add-Content -LiteralPath "work/release/$name.zip.sha256"' in stage
    assert '"# source-commit: $env:GITHUB_SHA"' in stage
    notes = step(workflow, "Select release notes")
    assert "BUILT_COMMIT: ${{ github.sha }}" in notes
    assert "Source commit:" in script(workflow, "Select release notes")


def test_windows_job_uses_frozen_unsynced_managed_python(workflow):
    windows = job(workflow, "windows")
    assert re.search(
        r'    env:\n      UV_FROZEN: "1"\n      UV_NO_SYNC: "1"\n'
        r"      UV_PYTHON_PREFERENCE: only-managed\n",
        windows,
    )
    assert "uv sync --frozen --no-default-groups --group dev --extra gpu" in script(
        workflow, "Sync build environment"
    )


def test_windows_job_budget_is_two_hours(workflow):
    windows = job(workflow, "windows")
    assert "    timeout-minutes: 120\n" in windows


@pytest.mark.parametrize(
    "status, stdout, stderr, allowed",
    [
        (0, '{"isDraft": true}', "", True),
        (0, '{"isDraft": false}', "", False),
        (1, "", "release not found\n", True),
        (1, "", "HTTP 403: denied", False),
        (0, "not JSON", "", False),
        (0, "{}", "", False),
        (0, '{"isDraft": "true"}', "", False),
    ],
)
def test_release_guard_refuses_published_or_unverifiable_tag(
    workflow, monkeypatch, status, stdout, stderr, allowed
):
    guard = step(workflow, "Refuse a published release")
    assert "shell: python {0}" in guard
    assert "GH_TOKEN: ${{ github.token }}" in guard
    assert "TAG: ${{ github.ref_name }}" in guard
    names = re.findall(r"^      - name: (.+)", workflow, re.MULTILINE)
    assert names.index("Refuse a published release") < names.index("Create draft release")
    body = script(workflow, "Refuse a published release")
    assert "${{" not in body
    tag = "v1.1.0; literal tag argument"
    monkeypatch.setenv("TAG", tag)
    calls = []

    def view(args, **kwargs):
        assert kwargs == {"capture_output": True, "text": True, "timeout": 60, "check": False}
        calls.append(args)
        return subprocess.CompletedProcess(args, status, stdout, stderr)

    monkeypatch.setattr(subprocess, "run", view)
    code = compile(body, "release-draft-guard", "exec")
    if allowed:
        exec(code, {})
    else:
        with pytest.raises((SystemExit, ValueError)):
            exec(code, {})
    assert calls == [["gh", "release", "view", tag, "--json", "isDraft"]]
    checklist = (ROOT / "docs/release-checklist.md").read_text(encoding="utf-8")
    assert "never re-run the release job after publication" in checklist


def test_triggers_permissions_concurrency_and_release_are_bounded(workflow):
    assert 'tags: ["v*"]' in workflow
    assert "  workflow_dispatch:\n    inputs:\n      version:" in workflow
    assert "        required: true" in workflow
    assert "permissions:\n  contents: read\n" in workflow
    assert "group: release-${{ github.ref }}" in workflow
    release = job(workflow, "release")
    windows = job(workflow, "windows")
    assert "runs-on: windows-latest" in windows
    assert "contents: write" not in windows
    assert "    needs: [windows, macos]\n" in release
    assert "github.event_name == 'push' && startsWith(github.ref, 'refs/tags/v')" in release
    assert "    permissions:\n      contents: write" in release
    assert re.findall(r"^\s+draft: (\S+)", workflow, re.MULTILINE) == ["true"]
    assert "tag_name: ${{ github.ref_name }}" in release
    assert "fail_on_unmatched_files: true" in release
    assert not re.search(r"\bgit\s+(?:push|tag)\b|\bgh\s+workflow\s+run\b", workflow)


def test_parallel_tests_create_basetemp_parent_before_pytest(workflow):
    """A fresh checkout must create pytest's parent directory idempotently."""
    lines = script(workflow, "Run parallel tests").splitlines()
    pytest_index = next(i for i, line in enumerate(lines) if line.startswith("uv run pytest"))
    args = shlex.split(lines[pytest_index])
    basetemp = next(
        arg.removeprefix("--basetemp=") for arg in args if arg.startswith("--basetemp=")
    )
    parent = Path(basetemp).parent.as_posix()
    create_parent = [
        "New-Item",
        "-ItemType",
        "Directory",
        "-Force",
        "-Path",
        parent,
        "|",
        "Out-Null",
    ]
    assert create_parent in [shlex.split(line) for line in lines[:pytest_index]], (
        f"create {parent} with -Force before pytest uses --basetemp={basetemp}"
    )


def test_release_asset_staging_creates_directory_with_force(workflow):
    """Staging must also succeed when its destination directory already exists."""
    lines = script(workflow, "Stage release assets").splitlines()
    copy_index = next(i for i, line in enumerate(lines) if line.strip().startswith("Copy-Item"))
    assert [
        "New-Item",
        "-ItemType",
        "Directory",
        "-Force",
        "-Path",
        "work/release-assets",
        "|",
        "Out-Null",
    ] in [shlex.split(line) for line in lines[:copy_index]]


def test_order_parallel_marker_and_build_flags_match_local_contract(workflow):
    names = re.findall(r"^      - name: (.+)", workflow, re.MULTILINE)
    assert names[:8] == [
        "Checkout tagged source",
        "Set up uv",
        "Sync build environment",
        "Check release version",
        "Run parallel tests",
        "Build release folder and zip",
        "Stage release assets",
        "Upload release assets",
    ]
    assert "uv sync --frozen --no-default-groups --group dev --extra gpu" in workflow
    tests = script(workflow, "Run parallel tests")
    assert "Remove-Item Env:PYTEST_ADDOPTS -ErrorAction SilentlyContinue" in tests
    command = next(line for line in tests.splitlines() if line.startswith("uv run pytest"))
    args = shlex.split(command)
    marker = args[args.index("-m") + 1]
    canonical = re.search(r'-m "(not gpu[^"]+)"', (ROOT / "CLAUDE.md").read_text())
    assert canonical and marker == canonical[1]
    assert args == [
        "uv",
        "run",
        "pytest",
        "-q",
        "-rs",
        "-n",
        "4",
        "--timeout",
        "600",
        "-m",
        marker,
        "--basetemp=work/ci-parallel",
    ]
    assert "if ($LASTEXITCODE -ne 0)" in tests
    build = script(workflow, "Build release folder and zip")
    command = next(line for line in build.splitlines() if line.startswith("uv run python"))
    flags = set(re.findall(r"--[a-z][a-z0-9-]*", command))
    assert flags == {
        "--form",
        "--ffmpeg-from",
        "--ffmpeg-sha256",
        "--notices",
        "--smoke",
        "--zip",
        "--out",
    }
    spec = importlib.util.spec_from_file_location(
        "workflow_build_parser", ROOT / "tools/package/build.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Inspect argparse registrations, then actually parse all implemented flags.
    tree = ast.parse((ROOT / "tools/package/build.py").read_text())
    supported = {
        arg.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "add_argument"
        for arg in node.args
        if isinstance(arg, ast.Constant)
        and isinstance(arg.value, str)
        and arg.value.startswith("--")
    }
    # Every release flag is implemented; no pending flags remain.
    assert flags - supported == set()
    options = module.parse_args(
        [
            "--form",
            "onedir",
            "--ffmpeg-from",
            "https://example.invalid/archive.zip",
            "--ffmpeg-sha256",
            "a" * 64,
            "--notices",
            "--smoke",
            "--out",
            "work/release",
        ]
    )
    assert options.notices and options.smoke is True and options.form == "onedir"
    assert "if ($LASTEXITCODE -ne 0)" in build


def test_ffmpeg_and_assets_come_from_lock_and_build_outputs(workflow):
    build = script(workflow, "Build release folder and zip")
    assert "tools/package/ffmpeg.lock.json" in build and "ConvertFrom-Json" in build
    assert "--ffmpeg-from $lock.asset_url --ffmpeg-sha256 $lock.seat_sha256" in build
    lock = json.loads((ROOT / "tools/package/ffmpeg.lock.json").read_text())
    assert lock["asset_url"] not in workflow and lock["seat_sha256"] not in workflow
    assert "BtbN" not in workflow
    stage = script(workflow, "Stage release assets")
    assert "Clearwater-$env:RELEASE_VERSION-windows-onedir" in stage
    assert '"work/release/$name.zip"' in stage
    assert '"work/release/$name.zip.sha256"' in stage
    assert '"work/release/dist-onedir/$name/Clearwater/THIRD_PARTY_NOTICES.md"' in stage
    assert '"work/release-assets"' in stage
    upload = step(workflow, "Upload release assets")
    assert "if-no-files-found: error" in upload
    assert "path: work/release-assets/*" in upload
    download = step(workflow, "Download release assets")
    assert "name: windows-release" in upload and "name: windows-release" in download
    assert "path: work/release-assets" in download
    release = step(workflow, "Create draft release")
    assert "work/release-assets/*.zip\n" in release
    assert "work/release-assets/*.zip.sha256\n" in release
    assert "work/release-assets/THIRD_PARTY_NOTICES.md\n" in release
    assert "work/release-assets/THIRD_PARTY_NOTICES-macos.md" in release
    macos_download = step(workflow, "Download macOS release assets")
    assert "name: macos-release" in macos_download
    assert "path: work/release-assets" in macos_download


@pytest.mark.parametrize(
    "event,ref,requested,source,ok",
    [
        ("push", "refs/tags/v1.1.0", "", "1.1.0", True),
        ("workflow_dispatch", "refs/tags/v1.1.0", "1.1.0", "1.1.0", True),
        ("push", "refs/tags/v1.1.0", "", "1.0.0", False),
        ("workflow_dispatch", "refs/tags/v1.1.0", "1.0.0", "1.1.0", False),
        ("workflow_dispatch", "refs/heads/main", "1.1.0", "1.1.0", False),
        ("workflow_dispatch", "refs/tags/v1.1.0", "", "1.1.0", False),
        ("push", "refs/tags/v", "", "", False),
        ("push", "refs/tags/v1.1.0\nBAD=1", "", "1.1.0", False),
    ],
)
def test_embedded_version_gate_executes_and_fails_closed(
    workflow, tmp_path, monkeypatch, event, ref, requested, source, ok
):
    gate = step(workflow, "Check release version")
    assert "shell: uv run python {0}" in gate
    assert "REQUESTED_VERSION: ${{ inputs.version }}" in gate
    output = tmp_path / "output"
    monkeypatch.setenv("GITHUB_REF", ref)
    monkeypatch.setenv("GITHUB_SHA", "a" * 40)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda args, **kwargs: subprocess.CompletedProcess(args, 0, _git_stdout(args), ""),
    )
    monkeypatch.setenv("GITHUB_EVENT_NAME", event)
    monkeypatch.setenv("REQUESTED_VERSION", requested)
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setitem(sys.modules, "clearwater", SimpleNamespace(__version__=source))
    code = compile(script(workflow, "Check release version"), "release-version-gate", "exec")
    if ok:
        exec(code, {})
        assert output.read_text() == "version=1.1.0\n"
    else:
        with pytest.raises(SystemExit):
            exec(code, {})
        assert not output.exists()


@pytest.mark.parametrize("present", [False, True])
def test_release_notes_body_is_optional_and_version_specific(
    workflow, tmp_path, monkeypatch, present
):
    body = step(workflow, "Select release notes")
    assert "shell: python {0}" in body
    assert "RELEASE_VERSION: ${{ needs.windows.outputs.version }}" in body
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("RELEASE_VERSION", "1.1.0")
    monkeypatch.setenv("BUILT_COMMIT", "a" * 40)
    output = tmp_path / "output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    notes = tmp_path / "docs/release-notes-1.1.0.md"
    if present:
        notes.parent.mkdir()
        notes.write_text("release body")
    exec(compile(script(workflow, "Select release notes"), "release-body", "exec"), {})
    assert output.read_text() == "body_path=work/release-body.md\n"
    rendered = (tmp_path / "work/release-body.md").read_text()
    assert "a" * 40 in rendered and "Source commit:" in rendered
    assert ("release body" in rendered) == present
    assert "body_path: ${{ steps.notes.outputs.body_path }}" in workflow


def test_checklist_names_release_authority_build_inputs_and_stop_boundaries():
    text = (ROOT / "docs/release-checklist.md").read_text(encoding="utf-8")
    assert "checklist v2" in text
    assert "20260303" in text and "3.12.13" in text and "3.5.5" in text
    assert "native-licences/" in text and "rebuild FFmpeg in the fork" in text
    assert "CLEAN Windows user account" in text and "DRAFT" in text
    assert "The OWNER pushes" in text and "clicks **Publish release**" in text
    numbered = re.split(r"^\d+\. ", text, flags=re.MULTILINE)[1:]
    assert len(numbered) >= 10
    assert all("**STOP**" in item for item in numbered)
    assert "BEFORE the tag" in text


def test_checklist_requires_uv_agreement_and_native_reverification():
    text = (ROOT / "docs/release-checklist.md").read_text(encoding="utf-8")
    build_inputs = text.split("4. Verify build inputs", 1)[1].split("\n5.", 1)[0]
    assert "uv --version" in build_inputs and "0.10.9" in build_inputs
    assert "agree before the tag" in build_inputs
    assert "uv change requires native-licences re-verification" in build_inputs


def test_checklist_requires_native_text_checkout_guard():
    text = (ROOT / "docs/release-checklist.md").read_text(encoding="utf-8")
    assert "git checkout -- tools/package/native-licences" in text
    assert "working-tree byte guard is green" in text


def test_readme_gpu_recipe_names_split_streams_and_matches_guide_commands():
    readme = (ROOT / "tools/package/README.md").read_text(encoding="utf-8")
    recipe = readme.split("The normal path is", 1)[1].split("For the spike", 1)[0]
    guide = (ROOT / "docs/user-guide.md").read_text(encoding="utf-8")
    for operation in ("install", "remove"):
        command = (
            f"Start-Process -Wait -FilePath .\\Clearwater.exe "
            f"-ArgumentList '--{operation}-gpu-pack' "
            f"-RedirectStandardOutput {operation}.log -RedirectStandardError {operation}.err"
        )
        assert command in recipe and command in guide
        cmd_command = f'start /wait "" Clearwater.exe --{operation}-gpu-pack > {operation}.log 2>&1'
        assert cmd_command in recipe and cmd_command in guide
    assert "N13 licence notice is in `install.log`" in recipe
    assert "progress and the installation outcome are in `install.err`" in recipe
    assert "outcome is in `remove.err`" in recipe


def test_guide_leads_with_artifact_and_retains_gpu_terminal_outcomes():
    text = (ROOT / "docs/user-guide.md").read_text(encoding="utf-8")
    install = text.split("## 2. Install on Windows 11 (from 1.1.1)\n", 1)[1].split("\n## 3.", 1)[0]
    assert "Clearwater-1.1.1-windows-onedir.zip" in install
    assert install.index("Clearwater.exe") < install.index("uv sync")
    assert "Get-FileHash" in install and "More info" in install and "Run anyway" in install
    assert "unsigned" in install and "NVIDIA" in install and "restart" in install
    assert "install.err" in install and "outcome" in install
    assert "-ArgumentList '--remove-gpu-pack'" in install
    launch = text.split("## 3. First run:", 1)[1].split("\n1. Choose", 1)[0]
    assert launch.index("Clearwater.exe") < launch.index("uv run")
    troubleshooting = text.split("## 6.", 1)[1].split("## 7.", 1)[0]
    assert "if you moved it, put it back" in troubleshooting
    licence = text.split("## 8. Licence", 1)[1]
    assert "artifact" in licence and "THIRD_PARTY_NOTICES.md" in licence
    assert "separately installed" not in licence


def test_root_notices_distinguish_pyinstaller_terms_and_artifact_redistribution():
    text = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    pyinstaller = next(line for line in text.splitlines() if line.startswith("| pyinstaller |"))
    assert "GPL-2.0-or-later" in pyinstaller and "Bootloader Exception" in pyinstaller
    assert "Apache-2.0" in pyinstaller and "additional run-time modules" in pyinstaller
    python = next(line for line in text.splitlines() if line.startswith("| Python |"))
    assert "1.1.0" in python and "REDISTRIBUTES" in python and "1.0.0" in python
    assert "notice of record for the artifact" in text


# --- WP6.5: the macOS job (CHARC ruling Q5: ONE reusable macos-build.yml) -------------------

# sha256 of release.yml at 8ca7aeaf (before WP6.5's macOS job), by job() slice / header.
BASE_WINDOWS_JOB_SHA256 = "6e8a9ffdf2cc823164e6a3cb6f9883eb9503bb69d61c3a51446589b4cc6924e8"
BASE_RELEASE_JOB_SHA256 = "92048c38c8b0db52d6e7827b594bfcb499372cb23232746f2877eed7c89cba8e"
BASE_HEADER_SHA256 = "d10fcff8052da48b415463720c39b8b621a9d53533303b7d646e380a10c1a036"
CELL_EXCLUSION = "not test_python_m_clearwater_starts_the_shell_and_exits_0"
MACOS_UV_CHECKSUM = "a92f61e9ac9b0f29668c15f56152e4a60143fca148ff5bfadb86718472c3f376"
MACOS_JOB_CALL = """\
    needs: windows
    uses: ./.github/workflows/macos-build.yml
    with:
      release-version: ${{ needs.windows.outputs.version }}

"""
MACOS_DOWNLOAD = """\
      - name: Download macOS release assets
        uses: actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093 # v4.3.0
        with:
          name: macos-release
          path: work/release-assets

"""


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@pytest.fixture
def macos():
    return MACOS_WORKFLOW.read_text(encoding="utf-8") if MACOS_WORKFLOW.is_file() else ""


def test_windows_job_tag_gate_and_triggers_are_byte_identical(workflow):
    """Ruling 1: the windows job (the tag gate inside it) and the header are unchanged."""
    assert _sha(job(workflow, "windows")) == BASE_WINDOWS_JOB_SHA256
    assert _sha(workflow.split("\njobs:\n", 1)[0]) == BASE_HEADER_SHA256


def test_release_job_changes_are_exactly_the_ruled_ones(workflow):
    """needs both jobs, a second download, the macOS notices attached; nothing else."""
    jobs = workflow.split("\njobs:\n", 1)[1]
    assert re.findall(r"^  ([a-z][\w-]*):\n", jobs, re.MULTILINE) == [
        "windows",
        "macos",
        "release",
    ]
    assert job(workflow, "macos") == MACOS_JOB_CALL
    release = job(workflow, "release")
    assert release.count(MACOS_DOWNLOAD) == 1
    names = re.findall(r"^      - name: (.+)", release, re.MULTILINE)
    assert names.index("Download release assets") + 1 == names.index(
        "Download macOS release assets"
    )
    restored = (
        release.replace("    needs: [windows, macos]\n", "    needs: windows\n", 1)
        .replace(MACOS_DOWNLOAD, "", 1)
        .replace("            work/release-assets/THIRD_PARTY_NOTICES-macos.md\n", "", 1)
    )
    assert _sha(restored) == BASE_RELEASE_JOB_SHA256


def test_macos_workflow_triggers_and_has_no_release_or_tag_gate(macos):
    assert macos, "the macOS workflow has not been implemented"
    head = macos.split("\njobs:\n", 1)[0]
    assert (
        "on:\n  workflow_call:\n    inputs:\n      release-version:\n"
        "        description: Version verified by the calling release workflow's tag gate\n"
        "        required: true\n        type: string\n"
        '  workflow_dispatch:\n  push:\n    branches: ["macos-validation/**"]\n'
    ) in head
    assert "permissions:\n  contents: read\n" in head
    assert "tags:" not in head
    assert re.findall(r"^  ([a-z][\w-]*):\n", macos.split("\njobs:\n", 1)[1], re.MULTILINE) == [
        "macos"
    ]
    for forbidden in (
        "contents: write",
        "refs/tags",
        'GITHUB_REF"]',
        "cat-file",
        "action-gh-release",
        "gh release",
        "download-artifact",
        "secrets.",
    ):
        assert forbidden not in macos, forbidden
    assert not re.search(r"\bgit\s+(?:push|tag|fetch)\b|\bgh\s+workflow\s+run\b", macos)


def test_macos_workflow_pins_the_same_actions_and_the_darwin_uv(macos):
    uses = re.findall(r"^\s+(?:- )?uses: (\S+)", macos, re.MULTILINE)
    assert {value.split("@")[0] for value in uses} == {
        "actions/checkout",
        "astral-sh/setup-uv",
        "actions/upload-artifact",
    }
    for value in uses:
        action, sha = value.split("@")
        assert re.fullmatch(r"[a-f0-9]{40}", sha) and sha == PINS[action]
    assert macos.count("persist-credentials: false") == 1
    assert "fetch-depth: 0" in step(macos, "Checkout source")
    setup = step(macos, "Set up uv")
    assert re.findall(r'^          version: "([^"]+)"$', setup, re.MULTILINE) == ["0.10.9"]
    assert 'python-version: "3.12.13"' in setup and "enable-cache: false" in setup
    assert f"checksum: {MACOS_UV_CHECKSUM}" in setup


def test_macos_job_runner_budget_environment_and_cpu_only_sync(macos):
    macos_job = job(macos, "macos")
    assert "    runs-on: macos-26\n" in macos_job and "macos-latest" not in macos
    assert "    timeout-minutes: 180\n" in macos_job
    assert re.search(
        r'    env:\n      UV_FROZEN: "1"\n      UV_NO_SYNC: "1"\n'
        r"      UV_PYTHON_PREFERENCE: only-managed\n",
        macos_job,
    )
    assert re.search(r'^      MACOS_FFMPEG_BUNDLED: "(true|false)"$', macos_job, re.MULTILINE)
    assert "uv sync --frozen --no-default-groups --group dev\n" in script(
        macos, "Sync build environment"
    )
    assert "--extra gpu" not in macos and "continue-on-error" not in macos


def test_macos_job_steps_mirror_the_windows_order(macos):
    assert re.findall(r"^      - name: (.+)", macos, re.MULTILINE) == [
        "Checkout source",
        "Set up uv",
        "Sync build environment",
        "Check version and record the run",
        "Static checks",
        "Run parallel tests",
        "Run serial tests",
        "Build app bundle without FFmpeg",
        "Build release bundle and zip",
        "List the app bundle",
        "Record the Mach-O identities",
        "Run macOS tests on the built bundle",
        "Check macOS skip reasons",
        "Capture runner and encoder facts",
        "Stage release assets",
        "Upload release assets",
        "Upload evidence",
    ]
    assert script(macos, "Static checks").splitlines() == [
        "uv run mypy",
        "uv run mypy --platform darwin",
    ]


def _pytest(macos, name):
    lines = script(macos, name).splitlines()
    command = next(line for line in lines if line.startswith("uv run pytest"))
    return lines, shlex.split(command.split(" 2>&1 | tee ", 1)[0])


def test_macos_test_legs_follow_the_windows_gate_with_the_ruled_differences(macos):
    canonical = re.search(r'-m "(not gpu[^"]+)"', (ROOT / "CLAUDE.md").read_text())
    assert canonical
    lines, parallel = _pytest(macos, "Run parallel tests")
    assert lines[:2] == ["unset PYTEST_ADDOPTS", "mkdir -p work/evidence"]
    assert parallel == [
        *(["uv", "run", "pytest", "-q", "-rs", "-n", "3", "--timeout", "600", "-m"]),
        canonical[1] + " and not macos",
        "-k",
        CELL_EXCLUSION,
        "--basetemp=work/ci-parallel",
    ]
    lines, serial = _pytest(macos, "Run serial tests")
    assert lines[0] == "unset PYTEST_ADDOPTS"
    assert serial == [
        *(["uv", "run", "pytest", "-q", "-rs", "--timeout", "1200", "-m"]),
        "(gpu or footage or gui or slow) and not fullclip and not macos",
        "-k",
        CELL_EXCLUSION,
        "--basetemp=work/ci-serial",
    ]
    lines, leg = _pytest(macos, "Run macOS tests on the built bundle")
    assert lines[0] == "unset PYTEST_ADDOPTS"
    assert leg[:10] == [
        "uv",
        "run",
        "pytest",
        "-q",
        "-rs",
        "--timeout",
        "1200",
        "-m",
        "macos",
        "-k",
    ]
    assert leg[10] == "$selection" and f'selection="{CELL_EXCLUSION}"' in lines
    assert 'export CLEARWATER_MAC_BUNDLE="$bundle"' in lines
    assert 'export PATH="$bundle/Contents/MacOS:$PATH"' in lines
    assert any(line.endswith('-macos-onedir/Clearwater.app"') for line in lines)
    for line in macos.splitlines():
        if "uv run pytest" in line:
            assert "| tee work/evidence/" in line


# --- WP6.5 run 2 (CHARC option (i); A r8 fold, CHARC 7910e7df): the two modes ------------------

VALIDATION_CONTINUES = "${{ success() || (!cancelled() && !inputs.release-version) }}"
VALIDATION_CONTINUES_ON = "${{ !cancelled() && env.MACOS_FFMPEG_BUNDLED == 'true' }}"
RELEASE_UPLOAD = "inputs.release-version && env.MACOS_FFMPEG_BUNDLED == 'true'"
VALIDATION_CONTINUES_OFF = "${{ !cancelled() && env.MACOS_FFMPEG_BUNDLED != 'true' }}"
VALIDATION_ONLY = "${{ !cancelled() && !inputs.release-version }}"
"""Run 3 (CHARC's exact form): the app listing runs in validation mode only, after any failure."""
MACOS_STEP_CONDITIONS = {
    "Checkout source": None,
    "Set up uv": None,
    "Sync build environment": None,
    "Check version and record the run": None,
    "Static checks": None,
    "Run parallel tests": None,
    "Run serial tests": VALIDATION_CONTINUES,
    "Build app bundle without FFmpeg": VALIDATION_CONTINUES_OFF,
    "List the app bundle": VALIDATION_ONLY,
    "Record the Mach-O identities": VALIDATION_ONLY,
    "Build release bundle and zip": VALIDATION_CONTINUES_ON,
    "Run macOS tests on the built bundle": VALIDATION_CONTINUES,
    "Check macOS skip reasons": VALIDATION_CONTINUES,
    "Capture runner and encoder facts": VALIDATION_CONTINUES,
    "Stage release assets": "env.MACOS_FFMPEG_BUNDLED == 'true'",
    "Upload release assets": RELEASE_UPLOAD,
    "Upload evidence": "always()",
}
"""Every macOS step's ``if:`` exactly (None = no condition, i.e. ``success()``). With no
release-version input (validation mode) the serial leg, the bundle's macOS tests, the
skip-reason check and the facts capture run after an earlier failure, and the bundle build
without FFmpeg does while the switch is off. Staging/upload require success in
release mode; the bundled build also runs after a failure."""

RELEASE_WORKFLOW_SHA256 = "dd91eae3ccb63ca735dcb252375a8373ea946e87ba92803678e30c66352a8151"
"""sha256 of release.yml (text, LF) at 69538abe: run 2's fix leaves it byte-identical."""

MACOS_TEST_STEPS = (
    "Run parallel tests",
    "Run serial tests",
    "Run macOS tests on the built bundle",
)


def _conditions(macos):
    """Each step's ``if:`` (None when it has none), in workflow order."""
    found = {}
    for name in re.findall(r"^      - name: (.+)$", macos, re.MULTILINE):
        gates = re.findall(r"^        if: (.+)$", step(macos, name), re.MULTILINE)
        assert len(gates) <= 1, f"{name}: {gates}"
        found[name] = gates[0].strip() if gates else None
    return found


def _validation_violations(macos, workflow):
    """What breaks the run-2 ruling: a step condition other than ``MACOS_STEP_CONDITIONS``, a
    ``continue-on-error`` anywhere, a test step off the job's bash or without its ``| tee``,
    the job's bash default gone, or release.yml not byte-identical."""
    problems = []
    conditions = _conditions(macos)
    if conditions != MACOS_STEP_CONDITIONS:
        problems.extend(
            f"condition {name}: {conditions.get(name)!r}"
            for name in sorted(set(conditions) | set(MACOS_STEP_CONDITIONS))
            if conditions.get(name, "absent") != MACOS_STEP_CONDITIONS.get(name, "absent")
        )
    if "continue-on-error" in macos:
        problems.append("continue-on-error")
    for name in MACOS_TEST_STEPS:
        body = step(macos, name)
        if "shell:" in body or "| tee work/evidence/" not in body:
            problems.append(f"shell or tee: {name}")
    if not re.search(
        r"^    defaults:\n      run:\n        shell: bash\n", job(macos, "macos"), re.MULTILINE
    ):
        problems.append("job shell")
    if _sha(workflow) != RELEASE_WORKFLOW_SHA256:
        problems.append("release.yml changed")
    return problems


class UnknownExpressionError(ValueError):
    """An ``if:`` form the step evaluator does not know: refused, never guessed."""


EXPRESSION_TOKEN = re.compile(
    r"\s*(?:(?P<op>\|\||&&|==|!=|!|\(|\))"
    r"|(?P<string>'(?:[^']|'')*')"
    r"|(?P<name>[A-Za-z_][A-Za-z0-9_-]*(?:\.[A-Za-z_][A-Za-z0-9_-]*)*))"
)
STATUS_FUNCTIONS = ("success", "cancelled", "always")
"""The status functions the evaluator knows; ``failure()`` and every other function refuse."""
EXPRESSION_CONTEXTS = ("env", "inputs")
"""The contexts the evaluator knows (``env.X``, ``inputs.X``); every other context refuses."""


def _tokens(expression):
    """The tokens of one ``if:`` (its ``${{ }}`` wrapper removed), or UnknownExpressionError."""
    text = expression.strip()
    if text.startswith("${{"):
        if not text.endswith("}}"):
            raise UnknownExpressionError(expression)
        text = text[3:-2]
    found, position = [], 0
    text = text.rstrip()
    while position < len(text):
        match = EXPRESSION_TOKEN.match(text, position)
        if not match or match.end() == position:
            raise UnknownExpressionError(f"{expression!r} at {text[position:]!r}")
        kind = match.lastgroup
        found.append((kind, match[kind]))
        position = match.end()
    return found


def evaluate_if(expression, *, failed, env, inputs):
    """Evaluate one GitHub Actions step ``if:`` over {success, cancelled, always, env, inputs}.

    The job is never cancelled here. A condition without a status function is read as
    ``success() && (...)`` (GitHub's rule); None (no ``if:``) is ``success()``. Truthiness:
    None, False and ``''`` are false. Precedence is GitHub's: ``!`` binds tighter than ``==`` /
    ``!=``, which bind tighter than ``&&``, then ``||`` (A r9 minor); one comparison per
    operand pair (a chained one is refused). ``==`` / ``!=`` compare two strings
    case-insensitively; any other operand pair (a boolean such as ``!env.X``, or a null) is
    refused rather than coerced, as is any other function, context, operator or literal
    (UnknownExpressionError), so a condition outside these forms cannot slip past the model.

    Args:
        expression: The ``if:`` text, or None.
        failed: Whether an earlier step failed (``success()`` false, the job not cancelled).
        env: The job's ``env`` values.
        inputs: The workflow inputs (empty in a push / validation run).

    Returns:
        Whether the step runs.
    """
    tokens = _tokens(expression or "success()")
    at = 0

    def peek():
        return tokens[at] if at < len(tokens) else (None, None)

    def take(kind=None, value=None):
        nonlocal at
        token = peek()
        if token[0] is None or (kind and token[0] != kind) or (value and token[1] != value):
            raise UnknownExpressionError(
                f"{expression!r}: expected {value or kind}, got {token[1]}"
            )
        at += 1
        return token

    def truthy(value):
        return value not in (None, False, "")

    def primary():
        kind, value = peek()
        if (kind, value) == ("op", "("):
            take()
            result = disjunction()
            take("op", ")")
            return result
        if kind == "string":
            take()
            return value[1:-1].replace("''", "'")
        if kind == "name" and value in STATUS_FUNCTIONS:
            take()
            take("op", "(")
            take("op", ")")
            return {"success": not failed, "cancelled": False, "always": True}[value]
        if kind == "name" and value.split(".", 1)[0] in EXPRESSION_CONTEXTS and "." in value:
            take()
            context, key = value.split(".", 1)
            if "." in key:
                raise UnknownExpressionError(f"{expression!r}: nested {value}")
            return (env if context == "env" else inputs).get(key)
        raise UnknownExpressionError(f"{expression!r}: unknown {value!r}")

    def comparison():
        left = negation()
        kind, value = peek()
        if (kind, value) in (("op", "=="), ("op", "!=")):
            take()
            right = negation()
            if not (isinstance(left, str) and isinstance(right, str)):
                raise UnknownExpressionError(f"{expression!r}: compares {left!r} with {right!r}")
            equal = left.casefold() == right.casefold()
            return equal if value == "==" else not equal
        return left

    def negation():
        if peek() == ("op", "!"):
            take()
            return not truthy(negation())
        return primary()

    def conjunction():
        result = comparison()
        while peek() == ("op", "&&"):
            take()
            right = comparison()
            result = truthy(result) and truthy(right)
        return result

    def disjunction():
        result = conjunction()
        while peek() == ("op", "||"):
            take()
            right = conjunction()
            result = truthy(result) or truthy(right)
        return result

    value = disjunction()
    if at != len(tokens):
        raise UnknownExpressionError(f"{expression!r}: trailing {tokens[at][1]!r}")
    if not any(kind == "name" and name in STATUS_FUNCTIONS for kind, name in tokens):
        return (not failed) and truthy(value)
    return truthy(value)


MACOS_LOG = "work/evidence/macos.log"
MODE_CASES = {
    "release-all-success": ({"release-version": "1.2.0"}, "true", None),
    "release-failed-leg": ({"release-version": "1.2.0"}, "true", "Run parallel tests"),
    "validation-off-failed-leg": ({}, "false", "Run parallel tests"),
    "validation-on-failed-leg": ({}, "true", "Run parallel tests"),
}
"""(inputs, MACOS_FFMPEG_BUNDLED, the step that fails or None) per mode case."""

FIRST_SIX = [
    "Checkout source",
    "Set up uv",
    "Sync build environment",
    "Check version and record the run",
    "Static checks",
    "Run parallel tests",
]
MODE_REACHED = {
    "release-all-success": [
        *FIRST_SIX,
        "Run serial tests",
        "Build release bundle and zip",
        "Run macOS tests on the built bundle",
        "Check macOS skip reasons",
        "Capture runner and encoder facts",
        "Stage release assets",
        "Upload release assets",
        "Upload evidence",
    ],
    "release-failed-leg": [*FIRST_SIX, "Build release bundle and zip", "Upload evidence"],
    "validation-off-failed-leg": [
        *FIRST_SIX,
        "Run serial tests",
        "Build app bundle without FFmpeg",
        "List the app bundle",
        "Record the Mach-O identities",
        "Run macOS tests on the built bundle",
        "Check macOS skip reasons",
        "Capture runner and encoder facts",
        "Upload evidence",
    ],
    "validation-on-failed-leg": [
        *FIRST_SIX,
        "Run serial tests",
        "Build release bundle and zip",
        "List the app bundle",
        "Record the Mach-O identities",
        "Run macOS tests on the built bundle",
        "Check macOS skip reasons",
        "Capture runner and encoder facts",
        "Upload evidence",
    ],
}
"""The steps each mode case reaches, including F0-2b's build after a failed release leg."""


def _walk(macos, inputs, switch, failing):
    """The steps a run reaches, in order: each ``if:`` evaluated against the outcomes so far
    (a reached step succeeds unless it is ``failing``)."""
    env = {"MACOS_FFMPEG_BUNDLED": switch}
    reached, failed = [], False
    for name, condition in _conditions(macos).items():
        if evaluate_if(condition, failed=failed, env=env, inputs=inputs):
            reached.append(name)
            failed = failed or name == failing
    return reached


def _mode_violations(macos, case):
    """What breaks one mode case: the reached steps differ from ``MODE_REACHED``, or a
    reached step reads ``macos.log`` before any reached step has produced it."""
    inputs, switch, failing = MODE_CASES[case]
    reached = _walk(macos, inputs, switch, failing)
    problems = []
    if reached != MODE_REACHED[case]:
        problems.append(
            f"reached differs: missing {[n for n in MODE_REACHED[case] if n not in reached]}, "
            f"extra {[n for n in reached if n not in MODE_REACHED[case]]}"
        )
    produced = False
    for name in reached:
        body = step(macos, name)
        if f"tee {MACOS_LOG}" in body:
            produced = True
        elif MACOS_LOG in body and not produced:
            problems.append(f"{name} reads {MACOS_LOG} before any reached step produced it")
    return problems


def test_validation_mode_continues_after_a_failed_leg_and_still_fails_the_job(macos, workflow):
    """WP6.5 run 2 (CHARC option (i)): each step carries exactly its ruled condition; no
    step (no test step above all) has ``continue-on-error``, so a failed leg still fails the
    job; the test legs run in the job's ``bash`` (Actions runs it as ``bash --noprofile
    --norc -eo pipefail {0}``, so a failing pytest before ``| tee`` fails its step); and
    release.yml is unchanged."""
    assert _validation_violations(macos, workflow) == []


@pytest.mark.parametrize("case", list(MODE_CASES))
def test_both_modes_reach_the_ruled_steps_by_evaluation(macos, case):
    """A r8 fold (CHARC 7910e7df): the real ``if:`` expressions EVALUATED, step by step:
    (1) release, all success: the bundle tests (``macos.log``'s producer) run before the
    skip-reason check reads it, and staging and upload are reached; (2) release, a failed
    leg: the bundled build and evidence upload run, but staging/upload stay blocked;
    (3) validation, switch off, a failed
    leg: serial, the build without FFmpeg, the bundle tests, the skip reasons and the facts;
    (4) validation, switch on, a failed leg: the bundled build also runs, with no staging or
    upload."""
    assert _mode_violations(macos, case) == []


def test_the_a_r8_form_fails_release_all_success(macos):
    """The control: 2e98ca1c's conditions (the bundle tests and the facts keyed on the
    switch; the skip-reason check and the serial leg as then) skip ``macos.log``'s producer
    in a successful release run, and the walk reports it (A r8 MAJOR)."""
    old = macos
    for name, condition in {
        "Run serial tests": "${{ !cancelled() }}",
        "Run macOS tests on the built bundle": VALIDATION_CONTINUES_OFF,
        "Capture runner and encoder facts": VALIDATION_CONTINUES_OFF,
    }.items():
        head, tail = old.split(f"      - name: {name}\n", 1)
        tail = tail.replace(
            f"        if: {VALIDATION_CONTINUES}\n", f"        if: {condition}\n", 1
        )
        old = head + f"      - name: {name}\n" + tail
    head, tail = old.split("      - name: Check macOS skip reasons\n", 1)
    old = (
        head
        + "      - name: Check macOS skip reasons\n"
        + tail.replace(f"        if: {VALIDATION_CONTINUES}\n", "", 1)
    )
    problems = _mode_violations(old, "release-all-success")
    assert f"Check macOS skip reasons reads {MACOS_LOG} before any reached step produced it" in (
        problems
    )


@pytest.mark.parametrize(
    "expression",
    [
        "failure()",
        "${{ github.ref == 'refs/heads/main' }}",
        "${{ steps.version.outcome == 'success' }}",
        "contains(env.MACOS_FFMPEG_BUNDLED, 'true')",
        "${{ inputs.release-version == null }}",
        "${{ !cancelled() && env.X > 'a' }}",
        "${{ success() || }}",
        "${{ (success() }}",
        "${{ success() }",
    ],
)
def test_the_step_evaluator_refuses_forms_it_does_not_know(expression):
    """The evaluator's conservative refusal: an unknown function, context, operator or
    literal, a broken expression or wrapper raises instead of being read as true or false."""
    with pytest.raises(UnknownExpressionError):
        evaluate_if(expression, failed=False, env={"X": "b"}, inputs={})


@pytest.mark.parametrize("expression", ["!env.X == 'false'", "${{ !env.X == 'false' }}"])
def test_negation_binds_tighter_than_a_comparison_and_a_boolean_operand_is_refused(expression):
    """A r9 minor: GitHub reads ``!env.X == 'false'`` as ``(!env.X) == 'false'``, a boolean
    against a string; the evaluator refuses that comparison rather than emulate the coercion
    (it read ``!(env.X == 'false')`` before, True for X = 'true')."""
    with pytest.raises(UnknownExpressionError, match="compares False with 'false'"):
        evaluate_if(expression, failed=False, env={"X": "true"}, inputs={})


@pytest.mark.parametrize(("value", "runs"), [("a", False), ("A", False), ("b", True)])
def test_negation_of_a_parenthesized_comparison_is_evaluated(value, runs):
    """A r9 minor: ``!`` bound to a parenthesized comparison negates its result."""
    for expression in ("!(env.X == 'a')", "${{ !(env.X == 'a') }}"):
        assert evaluate_if(expression, failed=False, env={"X": value}, inputs={}) is runs
    assert evaluate_if("!(env.X == 'a')", failed=True, env={"X": "b"}, inputs={}) is False


@pytest.mark.parametrize(
    ("expression", "failed", "inputs", "runs"),
    [
        (None, False, {}, True),
        (None, True, {}, False),
        ("always()", True, {}, True),
        ("env.MACOS_FFMPEG_BUNDLED == 'true'", True, {}, False),  # implicit success()
        ("env.MACOS_FFMPEG_BUNDLED == 'TRUE'", False, {}, True),  # case-insensitive
        (VALIDATION_CONTINUES, True, {}, True),
        (VALIDATION_CONTINUES, True, {"release-version": ""}, True),
        (VALIDATION_CONTINUES, True, {"release-version": "1.2.0"}, False),
        (VALIDATION_CONTINUES, False, {"release-version": "1.2.0"}, True),
        (VALIDATION_CONTINUES_OFF, True, {}, False),
    ],
)
def test_the_step_evaluator_reads_the_known_forms(expression, failed, inputs, runs):
    """The evaluator on the forms the workflow uses (switch "true")."""
    env = {"MACOS_FFMPEG_BUNDLED": "true"}
    assert evaluate_if(expression, failed=failed, env=env, inputs=inputs) is runs


@pytest.mark.parametrize(
    ("plant", "expected"),
    [
        ("serial-gated-on-success", "condition Run serial tests: None"),
        (
            "capture-keyed-on-the-switch",
            f"condition Capture runner and encoder facts: {VALIDATION_CONTINUES_OFF!r}",
        ),
        ("continue-on-error", "continue-on-error"),
        ("test-step-own-shell", "shell or tee: Run parallel tests"),
        ("release-edited", "release.yml changed"),
    ],
)
def test_the_validation_guard_sees_each_planted_breach(macos, workflow, plant, expected):
    """The run-2 guard's controls: a condition moved, a ``continue-on-error`` on a test step,
    a test step given its own shell, or a byte of release.yml changed is each reported."""
    if plant == "serial-gated-on-success":
        macos = macos.replace(f"        if: {VALIDATION_CONTINUES}\n", "", 1)
    elif plant == "capture-keyed-on-the-switch":
        head, tail = macos.split("      - name: Capture runner and encoder facts", 1)
        tail = tail.replace(VALIDATION_CONTINUES, VALIDATION_CONTINUES_OFF, 1)
        macos = head + "      - name: Capture runner and encoder facts" + tail
    elif plant == "continue-on-error":
        macos = macos.replace(
            "      - name: Run serial tests\n",
            "      - name: Run serial tests\n        continue-on-error: true\n",
            1,
        )
    elif plant == "test-step-own-shell":
        macos = macos.replace(
            "      - name: Run parallel tests\n",
            "      - name: Run parallel tests\n        shell: sh\n",
            1,
        )
    else:
        workflow = workflow.replace("needs: [windows, macos]", "needs: [macos, windows]", 1)
    assert expected in _validation_violations(macos, workflow)


def test_macos_build_steps_are_gated_by_the_named_ffmpeg_switch(macos):
    """Before group 2a: the .app without FFmpeg; after: the release flags from the lock."""
    off = step(macos, "Build app bundle without FFmpeg")
    assert f"if: {VALIDATION_CONTINUES_OFF}" in off
    command = next(line for line in script(macos, "Build app bundle without FFmpeg").splitlines())
    assert command.startswith("uv run python tools/package/build.py --form onedir --out ")
    assert not re.search(r"--(ffmpeg|notices|smoke|zip)", command)
    on = script(macos, "Build release bundle and zip")
    assert f"if: {VALIDATION_CONTINUES_ON}" in step(macos, "Build release bundle and zip")
    flags = set(re.findall(r"--[a-z][a-z0-9-]*", on.splitlines()[-1]))
    assert flags == {
        "--form",
        "--ffmpeg-from",
        "--ffmpeg-sha256",
        "--notices",
        "--smoke",
        "--zip",
        "--out",
    }
    for name in ("Stage release assets", "Upload release assets"):
        condition = (
            RELEASE_UPLOAD
            if name == "Upload release assets"
            else "env.MACOS_FFMPEG_BUNDLED == 'true'"
        )
        assert f"if: {condition}" in step(macos, name)
    assert "if: always()" in step(macos, "Upload evidence")
    upload = step(macos, "Upload release assets")
    assert "name: macos-release" in upload and "if-no-files-found: error" in upload
    stage = script(macos, "Stage release assets")
    assert 'name="Clearwater-${RELEASE_VERSION}-macos"' in stage
    assert "/Contents/Resources/THIRD_PARTY_NOTICES.md" in stage
    assert "work/release-assets/THIRD_PARTY_NOTICES-macos.md" in stage
    assert "# source-commit: %s" in stage and "$GITHUB_SHA" in stage
    deselected = next(
        line
        for line in script(macos, "Run macOS tests on the built bundle").splitlines()
        if "and not videotoolbox" in line
    )
    for family in (
        "default_pipe_fidelity",
        "ffmpeg_text_and_redaction",
        "videotoolbox",
        "tool_and_worker_spawn",
        "test_macos_bundle_smoke[P16]",
        "test_macos_bundle_smoke[P57]",
    ):
        assert f"and not {family}" in deselected


@pytest.mark.parametrize(
    "requested, source, bundled, outcome",
    [
        ("", "1.2.0", "false", "validation"),
        ("", "1.2.0", "true", "validation"),
        ("1.2.0", "1.2.0", "true", "release"),
        ("1.2.0", "1.1.9", "true", "macOS build version differs"),
        ("1.2.0", "1.2.0", "false", "await WP6.5 group 2a"),
    ],
)
def test_macos_version_step_records_or_checks_the_release_version(
    macos, tmp_path, monkeypatch, requested, source, bundled, outcome
):
    gate = step(macos, "Check version and record the run")
    assert "shell: uv run python {0}" in gate
    assert "RELEASE_VERSION: ${{ inputs.release-version }}" in gate
    output = tmp_path / "output"
    interpreter = tmp_path / "python"
    interpreter.mkdir()
    (interpreter / "BUILD").write_text("20260303\n")
    monkeypatch.setattr(sys, "base_prefix", str(interpreter))
    monkeypatch.chdir(tmp_path)
    for name, value in {
        "RELEASE_VERSION": requested,
        "MACOS_FFMPEG_BUNDLED": bundled,
        "GITHUB_SHA": "a" * 40,
        "GITHUB_REF": "refs/heads/macos-validation/wp6.5",
        "GITHUB_OUTPUT": str(output),
        "ImageOS": "macos26",
        "ImageVersion": "20261026.0455.2",
    }.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setitem(sys.modules, "clearwater", SimpleNamespace(__version__=source))
    calls = []
    real_run = subprocess.run

    def sw_vers(args, **kwargs):
        # WP6.5 A-r6-2: only the step's own sw_vers call is the stand-in's. A cold
        # platform query in the step body (uname -> win32_ver -> `ver` when WMI is off)
        # reaches the real run instead of failing this call's kwargs assertion.
        if args != ["sw_vers"]:
            return real_run(args, **kwargs)
        calls.append(args)
        assert kwargs == {"capture_output": True, "text": True, "timeout": 30, "check": True}
        return subprocess.CompletedProcess(args, 0, "ProductName:\tmacOS\nBuildVersion:\t25G83\n")

    monkeypatch.setattr(subprocess, "run", sw_vers)
    code = compile(script(macos, "Check version and record the run"), "macos-version", "exec")
    if outcome in ("validation", "release"):
        exec(code, {})
        assert output.read_text() == f"version={source}\n"
        record = (tmp_path / "work/evidence/run-record.txt").read_text().splitlines()
        assert record[:3] == [
            f"mode: {outcome}",
            f"clearwater.__version__: {source}",
            "GITHUB_SHA: " + "a" * 40,
        ]
        assert "ImageVersion: 20261026.0455.2" in record and "BuildVersion:\t25G83" in record
        assert ("pbs BUILD: 20260303" in record) is (outcome == "validation")
        assert calls == [["sw_vers"]]
    else:
        with pytest.raises(SystemExit, match=outcome):
            exec(code, {})
        assert not output.exists() and calls == []


@pytest.mark.parametrize(
    "log, allowed",
    [
        ("12 passed, 30 deselected in 81.20s\n", True),
        (
            "SKIPPED [1] tests/test_wp321_bench.py:61: CUDA unavailable for device-frame "
            "benchmark: CPU: no CUDA device\n10 passed, 1 skipped in 9.01s\n",
            True,
        ),
        (
            "SKIPPED [2] tests/test_macos_portability.py:230: VideoToolbox unavailable on this "
            "Mac: no hardware session\n10 passed, 2 skipped in 9.01s\n",
            True,
        ),
        (
            "SKIPPED [1] tests/test_macos_portability.py:282: hdiutil could not create a APFS "
            "image: x\n10 passed, 1 skipped in 9.01s\n",
            False,
        ),
        (
            "SKIPPED [1] tests/test_macos_portability.py:1569: CLEARWATER_MAC_BUNDLE is not "
            "set: WP6.5 builds the app bundle\n3 passed, 1 skipped in 1.00s\n",
            False,
        ),
        ("1 failed, 3 passed in 1.00s\n", False),
        ("", False),
    ],
    ids=["clean", "cuda-absent", "vt-absent", "hdiutil", "bundle-unset", "failed", "empty"],
)
def test_macos_skip_allowlist_refuses_every_other_reason(
    macos, tmp_path, monkeypatch, log, allowed
):
    """Only the named VideoToolbox and CUDA availability reasons may skip the macOS leg."""
    assert "shell: uv run python {0}" in step(macos, "Check macOS skip reasons")
    monkeypatch.chdir(tmp_path)
    (tmp_path / "work/evidence").mkdir(parents=True)
    (tmp_path / "work/evidence/macos.log").write_text(log, encoding="utf-8")
    code = compile(script(macos, "Check macOS skip reasons"), "macos-skips", "exec")
    if allowed:
        exec(code, {})
    else:
        with pytest.raises(SystemExit, match="macOS leg: "):
            exec(code, {})


# --- WP6.5 run 3 (CHARC d6981092 items 6 and 7): the summary reading and the app listing --------

RUN_SUMMARIES = {
    # name: (the summary line exactly as the runner logged it, passed, failed)
    "run2-parallel": (
        "4 failed, 7762 passed, 1227 skipped, 1 warning in 187.60s (0:03:07)",
        7762,
        4,
    ),
    "run3-parallel": ("7827 passed, 1227 skipped, 1 warning in 248.53s (0:04:08)", 7827, 0),
    "run3-serial": (
        "15 failed, 518 passed, 784 skipped, 9286 deselected in 134.87s (0:02:14)",
        518,
        15,
    ),
    "run3-macos": ("1 failed, 133 passed, 10469 deselected in 65.12s (0:01:05)", 133, 1),
}
"""The real pytest summary lines of runs 2 (``42764505729``) and 3 (``42781244075``): run 2's
``parallel.log:1254``; run 3's ``parallel.log:887``, ``serial.log:930`` and ``macos.log:102``."""


def _skip_check(macos, tmp_path, monkeypatch, log):
    """Run the real "Check macOS skip reasons" script on ``log``; return its SystemExit or None."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "work/evidence").mkdir(parents=True, exist_ok=True)
    (tmp_path / "work/evidence/macos.log").write_text(log, encoding="utf-8")
    code = compile(script(macos, "Check macOS skip reasons"), "macos-skips", "exec")
    try:
        exec(code, {})
    except SystemExit as stop:
        return str(stop)
    return None


@pytest.mark.parametrize("name", list(RUN_SUMMARIES))
def test_the_skip_check_reads_the_real_run_summaries(macos, tmp_path, monkeypatch, capsys, name):
    """Run 3 item 6: the passed count is read from each real summary form; a failed count
    fails the step, saying so (run 3's ``1 failed, 133 passed`` was misread as "no passing
    summary line")."""
    line, passed, failed = RUN_SUMMARIES[name]
    stop = _skip_check(macos, tmp_path, monkeypatch, "....F..\n" + line + "\n")
    if failed:
        parts = line.split(" in ", 1)[0]
        assert stop == f"macOS leg: {failed} failed, 0 errors: {parts}"
    else:
        assert stop is None
        assert capsys.readouterr().out == f"macOS leg: {passed} passed; 0 skipped, all allowed\n"


@pytest.mark.parametrize(
    ("line", "outcome"),
    [
        ("2 skipped, 133 passed in 1.00s", None),
        ("133 passed, 3 deselected, 2 warnings in 1.00s", None),
        ("========= 133 passed, 1 xfailed in 1.00s =========", None),
        ("133 passed, 1 error in 1.00s", "macOS leg: 0 failed, 1 errors: 133 passed, 1 error"),
        (
            "2 errors, 1 failed, 5 passed in 1.00s",
            "macOS leg: 1 failed, 2 errors: 2 errors, 1 failed, 5 passed",
        ),
        ("3 deselected in 0.50s", "macOS leg: no test passed: 3 deselected"),
        ("no tests ran in 0.01s", "macOS leg: no pytest summary line in macos.log"),
    ],
    ids=["skipped-first", "warnings", "banner", "error", "errors-first", "none-passed", "no-tests"],
)
def test_the_skip_check_reads_any_summary_order(macos, tmp_path, monkeypatch, line, outcome):
    """Run 3 item 6: the parts in any order; any failed or error count fails, saying so."""
    assert _skip_check(macos, tmp_path, monkeypatch, line + "\n") == outcome


def test_the_skip_check_still_refuses_a_reason_outside_the_allowlist(macos, tmp_path, monkeypatch):
    """Run 3 item 6: a passing summary in another order does not admit another skip reason."""
    log = (
        "SKIPPED [2] tests/test_macos_portability.py:282: hdiutil could not create a APFS image\n"
        "2 skipped, 10 passed in 9.01s\n"
    )
    stop = _skip_check(macos, tmp_path, monkeypatch, log)
    assert stop == (
        "macOS leg: skip reasons outside the allowlist: hdiutil could not create a APFS image"
    )


LISTING = "work/evidence/app-listing.txt"


def test_the_app_listing_step_lists_the_bundle_and_every_mach_o_file(macos):
    """Run 3 item 7: after BOTH builds (A r11 #4), ``find -ls`` of the .app and ``otool -L``
    over every Mach-O file found by file type (an extensionless Mach-O counts), written into the
    evidence upload; a missing .app is said in the listing and the step exits 0."""
    names = re.findall(r"^      - name: (.+)$", macos, re.MULTILINE)
    assert names.index("List the app bundle") == names.index("Build release bundle and zip") + 1
    assert names.index("List the app bundle") > names.index("Build app bundle without FFmpeg")
    body = step(macos, "List the app bundle")
    assert f"        if: {VALIDATION_ONLY}\n" in body
    assert "continue-on-error" not in body and "shell:" not in body
    assert "RELEASE_VERSION: ${{ steps.version.outputs.version }}" in body
    lines = script(macos, "List the app bundle").splitlines()
    assert lines[:3] == [
        "mkdir -p work/evidence",
        f"listing={LISTING}",
        'app="work/release/dist-onedir/Clearwater-${RELEASE_VERSION}-macos-onedir/Clearwater.app"',
    ]
    assert lines[3:7] == [
        'if [ ! -d "$app" ]; then',
        '  echo "No app bundle at $app: nothing to list." > "$listing"',
        "  exit 0",
        "fi",
    ]
    text = "\n".join(lines)
    assert '  find "$app" -ls || echo "find -ls failed for $app"\n' in text
    # By file type, never by name: every regular file is asked, Mach-O ones get otool -L.
    assert 'done < <(find "$app" -type f -print0)' in text
    assert '    kind=$(file -b "$entry" || true)' in text
    assert "      Mach-O*)" in text
    assert '        otool -L "$entry" || echo "otool -L failed for $entry"' in text
    assert "-name" not in text and ".dylib" not in text and ".so" not in text
    assert lines[-1] == '} > "$listing" 2>&1'
    upload = step(macos, "Upload evidence")
    assert "path: work/evidence/\n" in upload and "if: always()" in upload


@pytest.mark.parametrize(
    ("mode", "inputs", "failed", "runs"),
    [
        ("validation", {}, False, True),
        ("validation", {}, True, True),
        ("validation", {"release-version": ""}, True, True),
        ("release", {"release-version": "1.2.0"}, False, False),
        ("release", {"release-version": "1.2.0"}, True, False),
    ],
    ids=[
        "validation-ok",
        "validation-failed",
        "validation-empty-input",
        "release-ok",
        "release-failed",
    ],
)
def test_the_app_listing_condition_by_mode(macos, mode, inputs, failed, runs):
    """Run 3 item 7: the listing's real ``if:`` evaluated in both modes, with and without an
    earlier failure, for both switch values: validation always lists; release never does."""
    condition = _conditions(macos)["List the app bundle"]
    assert condition == VALIDATION_ONLY
    for switch in ("false", "true"):
        env = {"MACOS_FFMPEG_BUNDLED": switch}
        assert evaluate_if(condition, failed=failed, env=env, inputs=inputs) is runs, mode


@pytest.mark.parametrize(
    ("switch", "built_by"),
    [("false", "Build app bundle without FFmpeg"), ("true", "Build release bundle and zip")],
    ids=["switch-off", "switch-on"],
)
@pytest.mark.parametrize("failing", [None, "Run parallel tests"], ids=["ok", "failed-leg"])
def test_the_app_listing_follows_whichever_build_ran(macos, switch, built_by, failing):
    """A r11 #4: validation mode, the real ``if:`` expressions EVALUATED step by step. With the
    switch on and every step green, the FFmpeg-ON build makes the .app and the listing is
    reached AFTER it (before this fold it ran first and found no bundle); with the switch off,
    after the build without FFmpeg. A failed leg still lists (the release build, gated on
    !cancelled(), is also reached). Release mode never lists."""
    reached = _walk(macos, {}, switch, failing)
    assert "List the app bundle" in reached
    later = reached[reached.index("List the app bundle") :]
    for name in ("Build app bundle without FFmpeg", "Build release bundle and zip"):
        assert name not in later
    assert built_by in reached
    assert reached.index(built_by) < reached.index("List the app bundle")
    assert "List the app bundle" not in _walk(macos, {"release-version": "1.2.0"}, switch, None)


# --- WP6.5 group 2a part 2: the switch's lock fields follow the macOS lock's shape ---------

MACOS_LOCK_FIXTURE = ROOT / "tests/ffmpeg_lock/ffmpeg-macos.fixture.json"


def _build_tool():
    path = ROOT / "tools/package/build.py"
    spec = importlib.util.spec_from_file_location("wp65_workflow_lock_build", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_macos_release_build_reads_the_macos_lock_fields_and_the_switch_is_on(macos):
    """The step reads asset_url / seat_sha256 from ffmpeg-macos.lock.json, the fields the
    validator's macOS shape names. F0-2b enables the switch after the darwin census lands."""
    build = _build_tool()
    lines = script(macos, "Build release bundle and zip").splitlines()
    assert lines[0] == "lock=tools/package/ffmpeg-macos.lock.json"
    assert build.FFMPEG_MACOS_LOCK_PATH.relative_to(ROOT).as_posix() == lines[0].split("=", 1)[1]
    read = re.findall(
        r"""json\.load\(open\(sys\.argv\[1\]\)\)\['(\w+)'\]\)" "\$lock"\)$""",
        "\n".join(lines),
        re.MULTILINE,
    )
    assert read == ["asset_url", "seat_sha256"]
    fields = set(build.FFmpegMacLock.__annotations__)
    assert set(read) <= fields
    fixture = json.loads(MACOS_LOCK_FIXTURE.read_text(encoding="utf-8"))
    assert set(fixture) == fields
    assert '--ffmpeg-from "$url" --ffmpeg-sha256 "$sha"' in lines[-1]
    assert fixture["asset_url"] not in macos and fixture["seat_sha256"] not in macos
    assert re.findall(r'^      MACOS_FFMPEG_BUNDLED: "(\w+)"$', macos, re.MULTILINE) == ["true"]
    real = build.load_macos_ffmpeg_lock()
    assert build.FFMPEG_MACOS_LOCK_PATH.is_file()
    assert real["asset_url"] not in macos and real["seat_sha256"] not in macos


# --- WP6.5 part 3c, CHARC's guard: the lock present with the switch OFF is inert -----------

SWITCH_GATES = {
    "": True,
    "always()": True,
    "${{ success() || (!cancelled() && !inputs.release-version) }}": True,
    "${{ !cancelled() && env.MACOS_FFMPEG_BUNDLED != 'true' }}": True,
    "${{ !cancelled() && !inputs.release-version }}": True,
    "env.MACOS_FFMPEG_BUNDLED == 'true'": False,
    VALIDATION_CONTINUES_ON: False,
    RELEASE_UPLOAD: False,
}
"""Each step condition the macOS job uses -> whether the step runs with the switch "false"."""

SWITCH_ON_ONLY = re.compile(
    r'^( *)if \[ "\$MACOS_FFMPEG_BUNDLED" = "true" \]; then\n.*?^\1fi\n', re.MULTILINE | re.DOTALL
)
"""A shell branch taken only when the switch reads "true" (removed from the OFF reading when
:func:`_off_reading` admits its shape)."""

SHELL_BRANCH_WORD = re.compile(r"(?<![\w$-])(?:if|then|else|elif|fi|case|esac)(?![\w-])")
"""A shell branching keyword as a word: inside a switch-true branch it marks an ``else`` /
``elif`` arm or a nested branch, the shapes the OFF reading refuses (A r6 minor 2)."""

ASSET_NEEDLES = (
    "--notices",
    "--zip",
    "--ffmpeg-from",
    "--ffmpeg-sha256",
    "ffmpeg-macos.lock.json",
    "asset_url",
    "seat_sha256",
    "releases/download",
    "curl ",
    "wget ",
    "gh release",
    "hide_banner",
)
"""What a step that runs with the switch OFF must not name: the release flags, the lock, its
asset, a download tool, or a run of the bundled tool."""


def _off_reading(body: str) -> tuple[str, list[str]]:
    """One step's text as the switch "false" runs it, and the switch branches it refuses.

    A switch-true branch is removed only in its one supported shape: the ``if [
    "$MACOS_FFMPEG_BUNDLED" = "true" ]; then`` line, plain commands, and the ``fi`` at the same
    indent. A branching keyword inside it (an ``else`` / ``elif`` arm, a nested ``if`` or
    ``case``) could hide commands that DO run with the switch OFF (A r6 minor 2: a download in
    an ``else`` arm passed when the whole block was stripped), so such a branch is not read: it
    is reported and left in the live text. A conservative refusal, not a shell evaluator.
    """
    refused: list[str] = []

    def strip(match: re.Match[str]) -> str:
        inner = "\n".join(match[0].splitlines()[1:-1])
        words = SHELL_BRANCH_WORD.findall(inner)
        if words:
            refused.append(f"unsupported switch branch shape (inner {sorted(set(words))})")
            return match[0]
        return ""

    return SWITCH_ON_ONLY.sub(strip, body), refused


def _switch_off_violations(macos: str, lock: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Read the macOS job as the switch's value runs it; return (violations, steps run)."""
    values = re.findall(r'^      MACOS_FFMPEG_BUNDLED: "(\w+)"$', macos, re.MULTILINE)
    problems = [] if values == ["false"] else [f"the switch reads {values}"]
    ran = []
    for name in re.findall(r"^      - name: (.+)$", macos, re.MULTILINE):
        body = step(macos, name)
        gate = re.search(r"^        if: (.+)$", body, re.MULTILINE)
        condition = gate[1].strip() if gate else ""
        if condition not in SWITCH_GATES:
            problems.append(f"{name}: unknown condition {condition!r}")
            continue
        if not SWITCH_GATES[condition]:
            continue
        ran.append(name)
        live, refused = _off_reading(body)
        problems.extend(f"{name}: {reason}" for reason in refused)
        for needle in (*ASSET_NEEDLES, lock["asset_name"], lock["release_tag"]):
            if needle in live:
                problems.append(f"{name}: {needle}")
    return problems, ran


def test_the_lock_with_the_switch_off_is_inert(macos):
    """CHARC's guard (part 3c): with the real lock committed and MACOS_FFMPEG_BUNDLED "false",
    no step that runs calls --notices on a bundle, reads the lock's asset or downloads it, and
    the one build it runs parses to no FFmpeg pair, no notices, no smoke and no zip. Read
    statically from the workflow text; the workflow is never run."""
    macos = macos.replace('MACOS_FFMPEG_BUNDLED: "true"', 'MACOS_FFMPEG_BUNDLED: "false"')
    build = _build_tool()
    lock = build.load_macos_ffmpeg_lock()
    problems, ran = _switch_off_violations(macos, lock)
    assert problems == []
    assert "Build app bundle without FFmpeg" in ran
    assert not {
        "Build release bundle and zip",
        "Stage release assets",
        "Upload release assets",
    } & set(ran)
    command = script(macos, "Build app bundle without FFmpeg").splitlines()[0]
    argv = shlex.split(command.split(" 2>&1", 1)[0])
    assert argv[:4] == ["uv", "run", "python", "tools/package/build.py"]
    args = build.parse_args(argv[4:])
    assert args.form == "onedir"
    assert args.ffmpeg_from is None and args.ffmpeg_sha256 is None
    assert not (args.notices or args.smoke or args.zip_release)
    capture, refused = _off_reading(step(macos, "Capture runner and encoder facts"))
    assert refused == []
    assert "$tool" not in capture


@pytest.mark.parametrize(
    "plant",
    [
        "switch-on",
        "off-step-notices",
        "release-step-ungated",
        "capture-runs-the-tool",
        "else-asset-download",
        "elif-arm",
        "nested-branch",
    ],
)
def test_the_switch_off_guard_sees_each_planted_breach(macos, plant):
    """The guard's controls: each planted breach of the OFF reading is reported.

    ``else-asset-download`` is A r6 minor 2's executed probe (a download of the lock's asset
    in an OFF ``else`` arm of the capture step's switch branch); ``elif-arm`` and
    ``nested-branch`` are the other shapes the OFF reading refuses."""
    macos = macos.replace('MACOS_FFMPEG_BUNDLED: "true"', 'MACOS_FFMPEG_BUNDLED: "false"')
    build = _build_tool()
    lock = build.load_macos_ffmpeg_lock()
    if plant == "switch-on":
        planted = macos.replace('MACOS_FFMPEG_BUNDLED: "false"', 'MACOS_FFMPEG_BUNDLED: "true"')
    elif plant == "off-step-notices":
        planted = macos.replace(
            "--form onedir --out work/release", "--form onedir --notices --out work/release", 1
        )
    elif plant == "release-step-ungated":
        gate = f"\n        if: {VALIDATION_CONTINUES_ON}\n"
        head, tail = macos.split("      - name: Build release bundle and zip", 1)
        planted = head + "      - name: Build release bundle and zip" + tail.replace(gate, "\n", 1)
    elif plant == "capture-runs-the-tool":
        planted = macos.replace('if [ "$MACOS_FFMPEG_BUNDLED" = "true" ]; then', "if true; then", 1)
    else:
        body = step(macos, "Capture runner and encoder facts")
        arm = {
            "else-asset-download": "          else\n",
            "elif-arm": '          elif [ -n "$RUNNER_TEMP" ]; then\n',
            "nested-branch": "            if true; then\n",
        }[plant]
        tail = "            fi\n" if plant == "nested-branch" else ""
        download = "            curl " + lock["asset_url"] + " -o /tmp/asset.zip\n"
        changed = body.replace("          fi\n", arm + download + tail + "          fi\n", 1)
        assert changed != body
        planted = macos.replace(body, changed, 1)
    assert planted != macos
    problems, _ran = _switch_off_violations(planted, lock)
    assert problems, plant
    if plant in {"else-asset-download", "elif-arm", "nested-branch"}:
        assert any("unsupported switch branch shape" in problem for problem in problems)
        assert any(problem.endswith(": curl ") for problem in problems)


# --- WP6.5 F0-2a (CHARC eb1fc893): the Mach-O identity evidence for F0-2b's census -----------

IDENTITIES = "work/evidence/macho-identities.txt"
IDENTITY_STEP = "Record the Mach-O identities"


def test_the_identity_step_is_pinned_after_the_listing_in_validation_mode(macos):
    """Right after the listing (so after whichever build ran), validation mode only, the
    build's own listing and ``macho:`` identity code, its file inside the evidence upload."""
    names = re.findall(r"^      - name: (.+)$", macos, re.MULTILINE)
    assert names.index(IDENTITY_STEP) == names.index("List the app bundle") + 1
    assert names.index(IDENTITY_STEP) + 1 == names.index("Run macOS tests on the built bundle")
    body = step(macos, IDENTITY_STEP)
    assert f"        if: {VALIDATION_ONLY}\n" in body
    assert "        shell: uv run python {0}\n" in body
    assert "RELEASE_VERSION: ${{ steps.version.outputs.version }}" in body
    assert "continue-on-error" not in body
    text = script(macos, IDENTITY_STEP)
    assert f'out = Path("{IDENTITIES}")' in text
    assert (
        'spec = importlib.util.spec_from_file_location("macho_build", "tools/package/build.py")'
        in text
    )
    # The build's own code: its non-following .app listing and the origin check's identity.
    assert "for path, kind in build._macos_app_entries(app):" in text
    assert "identity = build._macho_identity(data)" in text
    assert 'macho = "none" if identity is None else build._macho_digest(identity)' in text
    assert '["file", "-E", "-b", str(path)]' in text and 'startswith("Mach-O")' in text
    assert "build._macho_identity(data, bootloader=True)" in text
    assert "-name" not in text and ".dylib" not in text and "os.walk" not in text
    upload = step(macos, "Upload evidence")
    assert "path: work/evidence/\n" in upload and "if: always()" in upload


@pytest.mark.parametrize("switch", ["false", "true"])
@pytest.mark.parametrize("failing", [None, "Run parallel tests"], ids=["ok", "failed-leg"])
def test_the_identity_step_runs_in_validation_mode_only(macos, switch, failing):
    """Evaluated step by step: validation mode records after the listing, also after a failed
    leg; release mode (a release-version input) never reaches it."""
    reached = _walk(macos, {}, switch, failing)
    assert reached.index(IDENTITY_STEP) == reached.index("List the app bundle") + 1
    assert IDENTITY_STEP not in _walk(macos, {"release-version": "1.2.0"}, switch, failing)


def _run_identity_step(macos, tmp_path, monkeypatch, *, exit_code=0, file_error=False):
    """Execute the real script with ``file -E -b`` modelled by magic or a read error."""
    (tmp_path / "tools/package").mkdir(parents=True)
    (tmp_path / "tools/package/build.py").write_bytes(
        (ROOT / "tools/package/build.py").read_bytes()
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("RELEASE_VERSION", "1.2.0")
    monkeypatch.setenv("GITHUB_SHA", "b" * 40)
    asked = []

    def file_type(args, **kwargs):
        assert args[:3] == ["file", "-E", "-b"] and kwargs["timeout"] == 60
        asked.append(args[3])
        if file_error:
            return subprocess.CompletedProcess(args, 1, "cannot read", "permission denied")
        data = Path(args[3]).read_bytes()
        kind = "Mach-O 64-bit bundle arm64" if data[:4] == b"\xcf\xfa\xed\xfe" else "data"
        return subprocess.CompletedProcess(args, 0, kind + "\n", "")

    monkeypatch.setattr(subprocess, "run", file_type)
    try:
        exec(compile(script(macos, IDENTITY_STEP), "macho-identities", "exec"), {})
    except SystemExit as stop:
        assert stop.code == exit_code
    else:
        assert exit_code == 0
    return asked


def test_f02b_identity_step_reports_file_errors_without_hashing(macos, tmp_path, monkeypatch):
    """The file command's nonzero status reaches the named failure branch before reads."""
    app = tmp_path / "work/release/dist-onedir/Clearwater-1.2.0-macos-onedir/Clearwater.app"
    binary = app / "Contents/MacOS/Clearwater"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"unreadable stand-in")
    read = Path.read_bytes

    def guarded_read(path):
        assert path != binary, "the failed file query must prevent a hashing read"
        return read(path)

    monkeypatch.setattr(Path, "read_bytes", guarded_read)
    assert len(_run_identity_step(macos, tmp_path, monkeypatch, file_error=True)) == 1
    text = (tmp_path / IDENTITIES).read_text()
    assert "# file -b failed for Contents/MacOS/Clearwater\n" in text


@pytest.mark.parametrize("marker", [None, "20260303\n", "different-build\n"])
def test_f02b_version_evidence_records_build_marker(macos, tmp_path, monkeypatch, marker):
    """Validation evidence records the stripped interpreter marker, including its absence."""
    interpreter = tmp_path / "python"
    interpreter.mkdir()
    if marker is not None:
        (interpreter / "BUILD").write_text(marker)
    monkeypatch.setattr(sys, "base_prefix", str(interpreter))
    real_run = subprocess.run

    def sw_vers(args, **kwargs):
        if args != ["sw_vers"]:
            return real_run(args, **kwargs)
        return subprocess.CompletedProcess(args, 0, "macOS\n")

    monkeypatch.setattr(subprocess, "run", sw_vers)
    monkeypatch.setattr("platform.machine", lambda: "arm64")
    monkeypatch.chdir(tmp_path)
    for name, value in {
        "RELEASE_VERSION": "",
        "GITHUB_SHA": "a" * 40,
        "GITHUB_OUTPUT": str(tmp_path / "output"),
    }.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setitem(sys.modules, "clearwater", SimpleNamespace(__version__="1.2.0"))
    exec(compile(script(macos, "Check version and record the run"), "version-evidence", "exec"), {})
    expected = "absent" if marker is None else marker.strip()
    assert f"pbs BUILD: {expected}\n" in (tmp_path / "work/evidence/run-record.txt").read_text()


@pytest.mark.parametrize("release", [False, True], ids=["validation", "release"])
@pytest.mark.parametrize("failed", [False, True], ids=["success", "failed-leg"])
def test_f02b_release_assets_require_success_and_upload_requires_release(macos, release, failed):
    """Both modes build after failure; success gates staging and release mode gates upload."""
    inputs = {"release-version": "1.2.0"} if release else {}
    reached = _walk(macos, inputs, "true", "Run parallel tests" if failed else None)
    assert "Build release bundle and zip" in reached
    assert ("Stage release assets" in reached) is (not failed)
    assert ("Upload release assets" in reached) is (release and not failed)


def test_the_identity_step_records_each_mach_o_once_by_type(macos, tmp_path, monkeypatch):
    """The executed step: every regular Mach-O (an extensionless one included) gets path, size,
    sha256 and the build's ``macho:`` digest; data files are asked and skipped; a link is
    never asked or opened (the build's non-following listing)."""
    import test_tools_package_build as build_tests

    app = tmp_path / "work/release/dist-onedir/Clearwater-1.2.0-macos-onedir/Clearwater.app"
    files = {
        "Contents/MacOS/Clearwater": build_tests.macho(filetype=2),
        "Contents/Frameworks/libpython3.12.dylib": build_tests.built_native(),
        "Contents/Frameworks/numpy/_core/x.cpython-312-darwin.so": build_tests.built_native(2),
        "Contents/Resources/base_library.zip": b"PK\x05\x06" + bytes(18),
        "Contents/Info.plist": b"<plist/>",
    }
    for name, data in files.items():
        (app / name).parent.mkdir(parents=True, exist_ok=True)
        (app / name).write_bytes(data)
    build_tests._symlink(
        app / "Contents/Resources/libpython3.12.dylib",
        "../Frameworks/libpython3.12.dylib",
        folder=False,
    )
    asked = _run_identity_step(macos, tmp_path, monkeypatch)
    bundle = app.relative_to(tmp_path).as_posix()
    assert sorted(Path(path).as_posix() for path in asked) == [
        f"{bundle}/{name}" for name in sorted(files)
    ]
    lines = (tmp_path / IDENTITIES).read_text(encoding="utf-8").splitlines()
    assert lines[:2] == [
        f"# Mach-O identities of {Path(bundle)} at {'b' * 40}",
        "# path\tsize\tsha256\tmacho",
    ]
    expected = []
    for name in sorted(files):
        data = files[name]
        if data[:4] != b"\xcf\xfa\xed\xfe":
            continue
        identity = build_tests.build._macho_identity(data)
        assert identity is not None, name
        macho = build_tests.build._macho_digest(identity)
        assert macho.startswith("macho:")
        expected.append(f"{name}\t{len(data)}\t{hashlib.sha256(data).hexdigest()}\t{macho}")
    assert [line for line in lines[2:] if not line.startswith("#")] == expected and len(
        expected
    ) == 3
    identity = build_tests.build._macho_identity(
        files["Contents/MacOS/Clearwater"], bootloader=True
    )
    assert (
        "# bootloader\tContents/MacOS/Clearwater\t" + build_tests.build._macho_digest(identity)
        in lines
    )


def test_the_identity_step_says_when_there_is_no_bundle(macos, tmp_path, monkeypatch):
    asked = _run_identity_step(macos, tmp_path, monkeypatch)
    assert asked == []
    text = (tmp_path / IDENTITIES).read_text(encoding="utf-8")
    assert text.startswith("No app bundle at work") and text.endswith(": no identities.\n")


@pytest.mark.parametrize("kind", ["symlink", "junction"])
def test_identity_step_refuses_linked_app_root_before_any_follow(
    macos, tmp_path, monkeypatch, kind
):
    """A r1 F6: a root link must not be scanned, queried by is_dir, or hashed."""
    import test_tools_package_build as build_tests

    app = tmp_path / "work/release/dist-onedir/Clearwater-1.2.0-macos-onedir/Clearwater.app"
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "payload").write_bytes(build_tests.built_native())
    app.parent.mkdir(parents=True)
    if kind == "symlink":
        build_tests._symlink(app, str(outside), folder=True)
    else:
        # Model the Windows junction flag without invoking a shell or following a target.
        app.mkdir()
        original = Path.is_junction
        monkeypatch.setattr(Path, "is_junction", lambda p: p == app or original(p))
    original_is_dir = Path.is_dir

    def is_dir(path):
        assert path != app and path != app.relative_to(tmp_path), "followed linked app root"
        return original_is_dir(path)

    monkeypatch.setattr(Path, "is_dir", is_dir)
    # The workflow path is relative; the modeled junction flag recognises both forms.
    if kind == "junction":
        monkeypatch.setattr(Path, "is_junction", lambda p: p in (app, app.relative_to(tmp_path)))
    asked = _run_identity_step(macos, tmp_path, monkeypatch, exit_code=1)
    assert asked == []
    assert (tmp_path / IDENTITIES).read_text().startswith("Refused linked app bundle root:")
