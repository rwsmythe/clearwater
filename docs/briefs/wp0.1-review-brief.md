# WP0.1 — Independent review (Reviewer B) brief

**Issued by the orchestrator 2026-10-14.** Plan §4.5 item 7; `docs/review-gate-clearwater.md`
Part 2 item 2. You did NOT write WP0.1. Review it against its brief
(`docs/briefs/wp0.1-brief.md`, FINAL, including the `report_version` amendment) and the spec
clauses it names -- never against the author's completion report, which you are not given.

| Field | Content |
|---|---|
| Artifact | Branch `wp0.1` in `C:\Users\rwsmy\clearwater\.worktrees\wp0.1`; base `214f2b2`; head = the branch tip when you start (record its SHA). |
| Mode | READ-ONLY on the worktree. Do not edit, commit, stage, or switch branches there. Running the test suite and the tool is allowed (caches are gitignored). Outputs go to a temp folder or the evidence folder only. |
| Files owned | None in any repo tree. Your evidence goes to `C:\Users\rwsmy\clearwater-review-evidence\wp0.1\B\`. |
| Out of scope | Fixing anything; reviewing files outside the arc's diff except as context; the harness (`scripts/`, `.claude/`, `tests/harness/`). |

## Order of work

1. **Top-level claims first, end to end on the running code.** For each of the brief's five
   "Required end state" claims, measure it against the live tree and record the command and its
   output: e.g. load a tmp copy of the template with absolute paths substituted; run
   `uv run python tools/environment_report.py --out <tmp>` and check every key of the brief's
   table, in order, with `report_version` first; check the `null` + `unavailable` behaviour by
   running with a PATH that hides `nvidia-smi` and `ffmpeg`; grep the arc for `wmic`, `winreg`,
   `shell=True`, WMI; run ruff check, ruff format --check, mypy, pytest from the worktree.
2. **Locks:** the diff `git -C <worktree> diff --stat 214f2b2..HEAD` touches only the brief's
   owned files; the `pyproject.toml` diff is limited to items (a)–(d) of the brief; no
   dependency beyond `psutil` and `py-cpuinfo` (read `uv.lock` diff); no `clearwater.local.toml`
   created; nothing under `C:\Users\rwsmy\clearwater-footage\` touched.
3. **Code-level review** of the diff against the brief's Interfaces section and test roster:
   missing tests from the roster, wrong error cases, docstrings (Google style on every public
   function, class and module; comments true to the code).
4. **Codex pass** (same tier as Reviewer A): fast, WSL, per-call
   `-m gpt-5.6-luna -c model_reasoning_effort=medium -s read-only --skip-git-repo-check`, cwd the
   worktree (`/mnt/c/Users/rwsmy/clearwater/.worktrees/wp0.1`), diff pre-generated Windows-side
   (`git -C <worktree> diff -U8 214f2b2..HEAD`), WSL never runs git. Wrapper:
   `wsl.exe bash -ilc 'export PATH="$HOME/.local/node22/bin:$PATH"; cd <wsl worktree> && cat <prompt> <diff> | codex exec <flags> - > <transcript> 2>&1'`.
   Probe first through the exact invocation (one `^ succeeded in` line). Build the prompt
   NEUTRALLY from the brief's claim list, the envelope (Windows 11, one NVIDIA card or none,
   Python 3.12 under uv, nvidia-smi and FFmpeg present or absent; other OSes and multi-GPU are
   out of envelope -- ask the reviewer to TAG such findings), `CORRECTNESS REVIEW` /
   `WHAT TO EXAMINE` framing, "report every finding with a severity tag (critical/major/minor)",
   and this paragraph verbatim: "You are in a read-only sandbox. You may be unable to run the
   test suite. If a command fails for that reason, SAY SO EXPLICITLY next to the finding it
   bears on, and mark that finding REASONED rather than EXECUTED. Do NOT silently fall back to
   inferring behaviour from the diff and reporting it with the confidence of a measurement. Tag
   EVERY finding EXECUTED or REASONED -- including the ones you never attempted to execute --
   and for an EXECUTED tag show the probe and its output in the transcript." Do not include any
   prior review ledger or the author's notes. Run ONE pass. Assert on the transcript (all
   `grep -a`): banner model `gpt-5.6-luna` and effort `medium`; `^ERROR` and `ERROR codex_core`
   lines classified by provenance; `^tokens used` footer; an anchored VERDICT line;
   `^ succeeded in` count >= 1. Copy prompt, diff and transcript to the evidence folder with md5s.
5. **Reproduce before reporting:** every finding you report (yours or Codex's) carries a
   reproduction (a command and its output) or is explicitly marked REASONED with the trace.

## Return (your FINAL message; you are a subagent and it reaches the orchestrator directly)

Head SHA reviewed; per claim 1–5 PASS/FAIL with the measuring command and output line; lock
results; findings list (severity, in/out of envelope, EXECUTED/REASONED, reproduction, file:line);
the Codex pass (banner, assertions, verdict, evidence paths with md5s); and a verdict:
NO_BLOCKING (zero in-envelope critical/major) or BLOCKING with the list. Never post to a
mailbox.
