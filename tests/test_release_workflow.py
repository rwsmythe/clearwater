"""Offline release-workflow contracts; actionlint and a real run belong to the seat.

The indentation checks deliberately cover this workflow's small YAML surface without
adding a YAML dependency. The embedded Python version gate is executed, not emulated.
No test calls a product entry point, builds an artifact or contacts GitHub.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import re
import shlex
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
    output = tmp_path / "output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    notes = tmp_path / "docs/release-notes-1.1.0.md"
    if present:
        notes.parent.mkdir()
        notes.write_text("release body")
    exec(compile(script(workflow, "Select release notes"), "release-body", "exec"), {})
    assert output.read_text() == f"body_path={'docs/release-notes-1.1.0.md' if present else ''}\n"
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


def test_guide_leads_with_artifact_and_retains_gpu_terminal_outcomes():
    text = (ROOT / "docs/user-guide.md").read_text(encoding="utf-8")
    install = text.split("## 2. Install on Windows 11\n", 1)[1].split("\n## 3.", 1)[0]
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
