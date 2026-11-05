"""Offline release-workflow contracts; actionlint and a real run belong to the seat.

The indentation checks deliberately cover this workflow's small YAML surface without
adding a YAML dependency. The embedded Python version gate is executed, not emulated.
No test calls a product entry point, builds an artifact or contacts GitHub.
"""

from __future__ import annotations

import ast
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


def test_every_action_is_one_of_the_seat_verified_sha_pins(workflow):
    uses = re.findall(r"^\s+(?:- )?uses: (\S+)", workflow, re.MULTILINE)
    assert len(uses) == 6  # checkout in each job, plus the other four actions
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
        calls.append(args)
        return subprocess.CompletedProcess(
            args, 0, tag_type if args[1] == "cat-file" else peeled, ""
        )

    monkeypatch.setattr(subprocess, "run", git)
    code = compile(script(workflow, "Check release version"), "release-tag-gate", "exec")
    if allowed:
        exec(code, {})
        assert calls == [
            [
                "git",
                "fetch",
                "--force",
                "--no-tags",
                "origin",
                "+refs/tags/v1.1.0:refs/tags/v1.1.0",
            ],
            ["git", "cat-file", "-t", "refs/tags/v1.1.0"],
            ["git", "rev-parse", "refs/tags/v1.1.0^{commit}"],
        ]
    else:
        with pytest.raises(SystemExit):
            exec(code, {})
    assert "fetch-depth: 0" in step(workflow, "Checkout tagged source")


@pytest.mark.parametrize("case", ["annotated", "lightweight", "wrong-commit"])
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
    git(seed, "commit", "--allow-empty", "-m", "second")
    other = git(seed, "rev-parse", "HEAD")
    git(seed, "remote", "add", "origin", str(origin))
    git(seed, "push", "origin", "HEAD:refs/heads/main", "--tags")
    git(tmp_path, "clone", "--branch", "main", str(origin), str(clone))
    ref = "refs/tags/v1.1.1" if case == "lightweight" else "refs/tags/v1.1.0"
    if case != "lightweight":
        assert git(clone, "cat-file", "-t", ref) == "tag"
    # Reproduce actions/checkout's overwrite, not an approximation of the gate.
    git(clone, "fetch", "origin", f"+{target}:{ref}")
    assert git(clone, "cat-file", "-t", ref) == "commit"
    git(clone, "checkout", "--detach", target)
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
        expected = (
            "Release requires an ANNOTATED tag"
            if case == "lightweight"
            else "Annotated tag does not peel to the built commit"
        )
        assert expected in result.stderr
        assert not output.exists()


def test_sidecar_and_draft_body_record_the_built_commit(workflow):
    stage = script(workflow, "Stage release assets")
    assert 'Add-Content -LiteralPath "work/release/$name.zip.sha256"' in stage
    assert '"# source-commit: $env:GITHUB_SHA"' in stage
    notes = step(workflow, "Select release notes")
    assert "BUILT_COMMIT: ${{ github.sha }}" in notes
    assert "Source commit:" in script(workflow, "Select release notes")


def test_windows_job_uses_frozen_unsynced_managed_python(workflow):
    windows = workflow.split("\n  windows:\n", 1)[1].split("\n  release:\n", 1)[0]
    assert re.search(
        r'    env:\n      UV_FROZEN: "1"\n      UV_NO_SYNC: "1"\n'
        r"      UV_PYTHON_PREFERENCE: only-managed\n",
        windows,
    )
    assert "uv sync --frozen --no-default-groups --group dev --extra gpu" in script(
        workflow, "Sync build environment"
    )


def test_windows_job_budget_is_two_hours(workflow):
    windows = workflow.split("\n  windows:\n", 1)[1].split("\n  release:\n", 1)[0]
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
    release = workflow.split("\n  release:\n", 1)[1]
    windows = workflow.split("\n  windows:\n", 1)[1].split("\n  release:\n", 1)[0]
    assert "runs-on: windows-latest" in windows
    assert "contents: write" not in windows
    assert "    needs: windows" in release
    assert "github.event_name == 'push' && startsWith(github.ref, 'refs/tags/v')" in release
    assert "    permissions:\n      contents: write" in release
    assert re.findall(r"^\s+draft: (\S+)", workflow, re.MULTILINE) == ["true"]
    assert "tag_name: ${{ github.ref_name }}" in release
    assert "fail_on_unmatched_files: true" in release
    assert not re.search(r"\bgit\s+(?:push|tag)\b|\bgh\s+workflow\s+run\b", workflow)


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
    # ONE explicit pending flag under the owner's zvbi HOLD; any second one fails.
    assert flags - supported == {"--zip"}
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
    assert "work/release-assets/THIRD_PARTY_NOTICES.md" in release


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
        lambda args, **kwargs: subprocess.CompletedProcess(
            args, 0, "tag" if args[1] == "cat-file" else "a" * 40, ""
        ),
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
    assert "native-licences/" in text and "2028-10" in text
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
    install = text.split("## 2. Install on Windows 11 (from 1.1.0)\n", 1)[1].split("\n## 3.", 1)[0]
    assert "Clearwater-1.1.0-windows-onedir.zip" in install
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
