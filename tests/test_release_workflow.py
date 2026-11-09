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

import pytest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/release.yml"
MACOS_WORKFLOW = ROOT / ".github/workflows/macos-build.yml"
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


def test_macos_build_steps_are_gated_by_the_named_ffmpeg_switch(macos):
    """Before group 2a: the .app without FFmpeg; after: the release flags from the lock."""
    off = step(macos, "Build app bundle without FFmpeg")
    assert "if: env.MACOS_FFMPEG_BUNDLED != 'true'" in off
    command = next(line for line in script(macos, "Build app bundle without FFmpeg").splitlines())
    assert command.startswith("uv run python tools/package/build.py --form onedir --out ")
    assert not re.search(r"--(ffmpeg|notices|smoke|zip)", command)
    on = script(macos, "Build release bundle and zip")
    assert "if: env.MACOS_FFMPEG_BUNDLED == 'true'" in step(macos, "Build release bundle and zip")
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
        assert "if: env.MACOS_FFMPEG_BUNDLED == 'true'" in step(macos, name)
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

    def sw_vers(args, **kwargs):
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
    ids=["clean", "vt-absent", "hdiutil", "bundle-unset", "failed", "empty"],
)
def test_macos_skip_allowlist_refuses_every_other_reason(
    macos, tmp_path, monkeypatch, log, allowed
):
    """Only "VideoToolbox unavailable on this Mac: ..." may skip in the macOS leg."""
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


# --- WP6.5 group 2a part 2: the switch's lock fields follow the macOS lock's shape ---------

MACOS_LOCK_FIXTURE = ROOT / "tests/ffmpeg_lock/ffmpeg-macos.fixture.json"


def _build_tool():
    path = ROOT / "tools/package/build.py"
    spec = importlib.util.spec_from_file_location("wp65_workflow_lock_build", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_macos_release_build_reads_the_macos_lock_fields_and_the_switch_stays_off(macos):
    """The step reads asset_url / seat_sha256 from ffmpeg-macos.lock.json, the fields the
    validator's macOS shape names; the switch is OFF until part 3 writes the real lock."""
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
    assert re.findall(r'^      MACOS_FFMPEG_BUNDLED: "(\w+)"$', macos, re.MULTILINE) == ["false"]
    assert not (ROOT / "tools/package/ffmpeg-macos.lock.json").exists()
