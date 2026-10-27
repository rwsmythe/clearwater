"""Driver for the Codex implementer lane (stdlib only): turn, commit, review.

The orchestrator runs a Codex implementer cell as `codex exec` PROCESSES in a
git worktree (design pass: docs/proofs/harness-dual-model-implementers.md,
Stage 0 facts of 2026-10-27). This script pins the three operations so no seat
improvises the flags:

``turn``
    One cell turn. The first turn pipes the staged preamble + brief into
    ``codex exec``; a later turn resumes the session. EVERY turn carries the
    model, effort, the unelevated Windows sandbox mode and the writable roots as
    ``-c`` overrides (``codex exec resume`` takes no ``-m``/``-s``/``--add-dir``;
    a turn without the overrides silently runs on the global config's model).
    The transcript and the ``-o`` return file land in the evidence folder; the
    banner assertions (model, effort, sandbox line, session id), the anchored
    ``^ERROR`` lines, the ``tokens used`` footer and the return file's
    ``FILES CHANGED`` / ``COMMIT`` block are printed as one JSON object.

``commit``
    The sandbox protects ``.git``, so the cell cannot commit. This reads the
    return file's ``FILES CHANGED`` block and ``COMMIT`` subject and commits
    exactly those paths by pathspec with the attribution footer naming the
    model (owner-approved form, 2026-10-27).

``review``
    The Claude reviewer pass for the Codex lane (Reviewer A between turns, run
    by the driver; Reviewer B at the orchestrator's seat): the pre-generated
    diff against the base plus the staged prompt piped into ``claude -p`` with
    a read-only tool policy and JSON output. Asserts the model from the result's
    ``modelUsage`` and that the worktree is clean afterwards.

Nothing here names the application; the pinned values are substrate facts.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import time
from typing import Any

CODEX_MODEL = "gpt-6.1-sol"
CODEX_EFFORT = "high"
WINDOWS_SANDBOX = "unelevated"
DEFAULT_WRITABLE_ROOTS = (os.path.join(os.environ.get("LOCALAPPDATA", ""), "uv"),)
CODEX_FOOTER = "Co-Authored-By: GPT-6.1 Sol via Codex <noreply@openai.com>"

CLAUDE_MODEL = "opus"
CLAUDE_MODEL_PREFIX = "claude-opus"
CLAUDE_EFFORT = "high"
CLAUDE_ALLOWED = (
    "Read,Grep,Glob,Bash(git diff:*),Bash(git log:*),Bash(git show:*),Bash(git status:*),"
    "Bash(git cat-file:*),Bash(git branch:*),Bash(uv run:*),Bash(python:*),"
    "Bash(.venv/Scripts/python.exe:*),Bash(grep:*),Bash(ls:*),Bash(timeout:*)"
)
CLAUDE_DISALLOWED = "Edit,Write,NotebookEdit,Agent,WebFetch,WebSearch"
DIFF_EXCLUDES = (":!docs/proofs", ":!uv.lock")


# ----------------------------------------------------------------- parsing --
def parse_banner(transcript: str) -> dict[str, Any]:
    """Extract the banner fields, the anchored ERROR lines and the tokens footer."""

    def field(name: str) -> str | None:
        m = re.search(rf"^{re.escape(name)}:\s*(.+?)\s*$", transcript, flags=re.M)
        return m.group(1) if m else None

    errors = [ln for ln in transcript.splitlines() if ln.startswith("ERROR")]
    tokens = None
    m = re.search(r"^tokens used\s*\n\s*([\d,]+)", transcript, flags=re.M)
    if m:
        tokens = int(m.group(1).replace(",", ""))
    return {
        "model": field("model"),
        "effort": field("reasoning effort"),
        "sandbox": field("sandbox"),
        "session_id": field("session id"),
        "error_lines": errors,
        "tokens_used": tokens,
        "succeeded_in": len(re.findall(r"^\s*succeeded in \d", transcript, flags=re.M)),
    }


def parse_return(text: str) -> dict[str, Any]:
    """Extract the FILES CHANGED paths, the COMMIT subject and VERDICT lines."""
    files: list[str] = []
    m = re.search(r"^FILES CHANGED:\s*\n((?:\s*-\s+.*\n?)+)", text, flags=re.M)
    if m:
        for ln in m.group(1).splitlines():
            ln = ln.strip()
            if ln.startswith("-"):
                path = ln[1:].strip().strip("`")
                if path:
                    files.append(path.replace("\\", "/"))
    c = re.search(r"^COMMIT:\s*(.+?)\s*$", text, flags=re.M)
    return {
        "files_changed": files,
        "commit_subject": c.group(1) if c else None,
        "verdict_lines": re.findall(r"^VERDICT:.*$", text, flags=re.M),
    }


def build_turn_command(
    *,
    worktree: str,
    session_id: str | None,
    return_file: str,
    model: str = CODEX_MODEL,
    effort: str = CODEX_EFFORT,
    writable_roots: tuple[str, ...] = DEFAULT_WRITABLE_ROOTS,
) -> list[str]:
    """The pinned ``codex exec`` (first turn) or ``codex exec resume`` (later) command."""
    roots = json.dumps([r.replace("\\", "/") for r in writable_roots])
    overrides = [
        "-c",
        f'model="{model}"',
        "-c",
        f"model_reasoning_effort={effort}",
        "-c",
        f'windows.sandbox="{WINDOWS_SANDBOX}"',
        "-c",
        f"sandbox_workspace_write.writable_roots={roots}",
    ]
    if session_id:
        return ["codex", "exec", "resume", session_id, *overrides, "-o", return_file, "-"]
    return [
        "codex",
        "exec",
        "-C",
        worktree,
        *overrides,
        "-s",
        "workspace-write",
        "--skip-git-repo-check",
        "-o",
        return_file,
        "-",
    ]


def build_review_command(*, model: str = CLAUDE_MODEL, effort: str = CLAUDE_EFFORT) -> list[str]:
    """The pinned read-only ``claude -p`` reviewer command (stdin = prompt + diff)."""
    return [
        "claude",
        "-p",
        "--model",
        model,
        "--effort",
        effort,
        "--no-session-persistence",
        "--disallowedTools",
        CLAUDE_DISALLOWED,
        "--allowedTools",
        CLAUDE_ALLOWED,
        "--output-format",
        "json",
    ]


# ----------------------------------------------------------------- running --
def _run_to_file(cmd: list[str], stdin_path: str, out_path: str, cwd: str) -> int:
    env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDECODE")}
    env.pop("CLAUDE_CODE_ENTRYPOINT", None)
    with open(stdin_path, "rb") as fin, open(out_path, "wb") as fout:
        proc = subprocess.run(
            cmd,
            stdin=fin,
            stdout=fout,
            stderr=subprocess.STDOUT,
            cwd=cwd,
            env=env,
            shell=os.name == "nt",
        )
    return proc.returncode


def cmd_turn(args: argparse.Namespace) -> int:
    """Run one cell turn and print the assertions as JSON."""
    ev = pathlib.Path(args.evidence)
    ev.mkdir(parents=True, exist_ok=True)
    n = args.turn
    transcript = ev / f"turn-{n}.txt"
    return_file = ev / f"return-{n}.md"
    roots = tuple(args.add_dir) if args.add_dir else DEFAULT_WRITABLE_ROOTS
    cmd = build_turn_command(
        worktree=args.worktree,
        session_id=args.session,
        return_file=str(return_file),
        model=args.model,
        effort=args.effort,
        writable_roots=roots,
    )
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    rc = _run_to_file(cmd, args.prompt, str(transcript), args.worktree)
    text = transcript.read_text("utf-8", errors="replace")
    banner = parse_banner(text)
    ret = (
        parse_return(return_file.read_text("utf-8", errors="replace"))
        if return_file.exists()
        else {}
    )
    out = {
        "turn": n,
        "started": started,
        "exit": rc,
        "transcript": str(transcript),
        "return_file": str(return_file) if return_file.exists() else None,
        "model_ok": banner["model"] == args.model,
        "effort_ok": banner["effort"] == args.effort,
        "sandbox_ok": bool(banner["sandbox"] and banner["sandbox"].startswith("workspace-write")),
        **banner,
        **ret,
    }
    print(json.dumps(out))
    return 0 if rc == 0 and out["model_ok"] and out["effort_ok"] and out["sandbox_ok"] else 1


def cmd_commit(args: argparse.Namespace) -> int:
    """Commit the turn's FILES CHANGED by pathspec with the model's footer."""
    ret = parse_return(pathlib.Path(args.return_file).read_text("utf-8", errors="replace"))
    files = ret["files_changed"]
    subject = args.subject or ret["commit_subject"]
    if not files or not subject:
        print(json.dumps({"error": "no FILES CHANGED block or COMMIT subject", **ret}))
        return 1
    git = ["git", "-C", args.worktree]
    subprocess.run([*git, "add", "--", *files], check=True)
    subprocess.run(
        [*git, "commit", "-q", "-m", subject, "-m", args.footer, "--", *files], check=True
    )
    sha = subprocess.run(
        [*git, "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    print(json.dumps({"committed": sha, "files": files, "subject": subject}))
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    """Run the Claude reviewer pass on the worktree's diff against the base."""
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    diff = out / "review-diff.txt"
    with open(diff, "wb") as f:
        subprocess.run(
            [
                "git",
                "-C",
                args.worktree,
                "diff",
                "-U8",
                f"{args.base}..HEAD",
                "--",
                ".",
                *DIFF_EXCLUDES,
            ],
            stdout=f,
            check=True,
        )
    combined = out / "review-input.txt"
    combined.write_bytes(pathlib.Path(args.prompt).read_bytes() + b"\n" + diff.read_bytes())
    result_json = out / "review.json"
    rc = _run_to_file(
        build_review_command(model=args.model, effort=args.effort),
        str(combined),
        str(result_json),
        args.worktree,
    )
    summary: dict[str, Any] = {"exit": rc, "diff": str(diff), "json": str(result_json)}
    try:
        data = json.loads(result_json.read_text("utf-8", errors="replace"))
        text = data.get("result", "")
        (out / "review.txt").write_text(text, "utf-8", newline="\n")
        models = list(data.get("modelUsage", {}).keys())
        summary.update(
            {
                "models": models,
                "model_ok": any(m.startswith(CLAUDE_MODEL_PREFIX) for m in models),
                "effort_requested": args.effort,
                "num_turns": data.get("num_turns"),
                "is_error": data.get("is_error"),
                "permission_denials": len(data.get("permission_denials", [])),
                "verdict_lines": re.findall(r"^VERDICT:.*$", text, flags=re.M),
                "review_txt": str(out / "review.txt"),
            }
        )
    except (OSError, ValueError) as exc:
        summary["error"] = f"{type(exc).__name__}: {exc}"
    status = subprocess.run(
        ["git", "-C", args.worktree, "status", "--porcelain"], capture_output=True, text=True
    ).stdout
    summary["worktree_clean_after"] = status.strip() == ""
    print(json.dumps(summary))
    ok = (
        rc == 0
        and summary.get("model_ok")
        and summary["worktree_clean_after"]
        and summary.get("verdict_lines")
    )
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    """Command-line entry."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("turn", help="run one Codex cell turn (first or resumed)")
    t.add_argument("--worktree", required=True)
    t.add_argument(
        "--prompt",
        required=True,
        help="staged file piped to stdin (preamble + brief, or the next prompt)",
    )
    t.add_argument("--evidence", required=True, help="folder for turn-N.txt and return-N.md")
    t.add_argument("--turn", type=int, required=True)
    t.add_argument("--session", default=None, help="session id to resume (omit on the first turn)")
    t.add_argument("--model", default=CODEX_MODEL)
    t.add_argument("--effort", default=CODEX_EFFORT)
    t.add_argument("--add-dir", action="append", help="extra writable root (default: the uv cache)")
    t.set_defaults(fn=cmd_turn)

    c = sub.add_parser("commit", help="commit a turn's FILES CHANGED by pathspec")
    c.add_argument("--worktree", required=True)
    c.add_argument("--return-file", required=True)
    c.add_argument("--subject", default=None, help="override the COMMIT subject")
    c.add_argument("--footer", default=CODEX_FOOTER)
    c.set_defaults(fn=cmd_commit)

    r = sub.add_parser("review", help="run the Claude reviewer pass on the worktree diff")
    r.add_argument("--worktree", required=True)
    r.add_argument("--base", required=True)
    r.add_argument("--prompt", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--model", default=CLAUDE_MODEL)
    r.add_argument("--effort", default=CLAUDE_EFFORT)
    r.set_defaults(fn=cmd_review)

    args = ap.parse_args(argv)
    return int(args.fn(args))


if __name__ == "__main__":
    sys.exit(main())
