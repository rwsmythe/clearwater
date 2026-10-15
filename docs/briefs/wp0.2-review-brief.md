# WP0.2 — Independent review (Reviewer B) brief

**Issued by the orchestrator 2026-10-15.** Plan §4.5 item 7; `docs/review-gate-clearwater.md`
Part 2 item 2. You did NOT write WP0.2. Review it against its brief
(`C:\Users\rwsmy\clearwater\docs\briefs\wp0.2-brief.md`, FINAL) and the spec clauses it names --
never against the author's completion report, which you are not given.

| Field | Content |
|---|---|
| Artifact | Branch `wp0.2` in `C:\Users\rwsmy\clearwater\.worktrees\wp0.2`; base `b0287a2`; head = the branch tip named in your dispatch (verify with `git -C`). |
| Mode | READ-ONLY on the worktree: no edits, commits, staging or branch switches. Running tests and the tool is allowed. Outputs go to a temp folder or the evidence folder only. |
| Footage | `C:\Users\rwsmy\clearwater-footage` is READ-ONLY to you. If it exists, you may run the tool against it with `--out <tmp>`; never write, copy or rename anything under it. |
| Evidence | `C:\Users\rwsmy\clearwater-review-evidence\wp0.2\B\` (pass 1), `B2\` (a re-check pass, if one is ordered). |
| Withheld | `docs/proofs/wp0.2-ledger.md` and the `r1`/`r2` evidence folders (the author's loop). Do not read them. |
| Known, not a finding | The harness gate fails on main and at the base with `docs/debt-register.md` unaccounted. It is a pre-existing main-tree issue, routed to CHARC. Record the result, but do not count it against WP0.2. |

## Order of work

1. **Top-level claims first, end to end on running code.** Build a synthetic footage tree in a
   temp folder: GoPro-named MP4s made with `ffmpeg -f lavfi` (FFmpeg is at
   `C:\Users\rwsmy\AppData\Local\Microsoft\WinGet\Links`; prepend it to PATH), at least one
   multi-chapter recording, `.LRV`/`.THM` sidecars, a JPEG/PNG/HEIC set made with Pillow and
   pillow-heif, an ignored file, and a truncated MP4 standing in for a mid-download file. For
   each of the brief's five claims, run `uv run python tools/inventory.py --footage <tmp> --out
   <tmp2>` and measure the claim, recording each command and its output. Check the CSV's column
   order against the brief's "Decisions fixed at issue"; check the summary's modes, sizes,
   chaptered recordings, error-row count and ignored count against the tree you built; snapshot
   the footage tree before and after to prove nothing was written.
2. **Locks:** `git -C <worktree> diff --stat b0287a2..HEAD` touches only owned files; the
   `pyproject.toml` diff is the two dev-group grants; `uv.lock` adds only Pillow and pillow-heif
   (and nothing else, transitive included: report any); `tools/local_config.py` and
   `tools/environment_report.py` are unchanged; no `shell=True`, every ffprobe call has a timeout.
3. **Code-level review** of the diff against the brief's Interfaces section and test roster.
   Measure each departure from the brief's stated signatures or semantics, and say for each
   whether it is additive or changes a stated behaviour.
4. **Codex pass** (same tier as Reviewer A): fast, WSL, per-call
   `-m gpt-5.6-luna -c model_reasoning_effort=medium -s read-only --skip-git-repo-check`, cwd
   `/mnt/c/Users/rwsmy/clearwater/.worktrees/wp0.2`, diff pre-generated Windows-side with
   `git -C <worktree> diff -U8 b0287a2..HEAD -- . ':!uv.lock' ':!docs/proofs'`; WSL never runs
   git. Wrapper:
   `wsl.exe bash -ilc 'export PATH="$HOME/.local/node22/bin:$PATH"; cd <wsl worktree> && cat <prompt> <diff> | codex exec <flags> - > <transcript> 2>&1'`.
   Probe first through the exact invocation (one `^ succeeded in` line).
   - **Prompt, built neutrally:** the brief's claim list and the envelope (Windows 11, Python
     3.12 under uv, ffprobe/ffmpeg 9.0.2, GoPro MP4 H.264/HEVC 8/10-bit, iPhone HEIC/JPEG/MOV, a
     footage folder absent or mid-download; other cameras' naming, RAW and network paths are out
     of envelope -- ask the reviewer to TAG such findings); `CORRECTNESS REVIEW` /
     `WHAT TO EXAMINE` framing; "report every finding with a severity tag (critical/major/minor)";
     and the read-only-sandbox EXECUTED/REASONED paragraph verbatim as in
     `docs/briefs/wp0.1-review-brief.md` step 4. No ledger, no author notes.
   - **ONE pass.** Assert on the transcript (all `grep -a`): banner `gpt-5.6-luna` / `medium`;
     `^ERROR` and `ERROR codex_core` classified by provenance; `^tokens used` footer; an
     anchored VERDICT line; `^ succeeded in` count >= 1.
   - **Evidence:** copy the prompt, diff and transcript to the evidence folder with md5s.
5. **Reproduce before reporting:** every finding carries a reproduction (a command and its
   output) or is marked REASONED with the trace. Adjudicate each Codex finding (adopt with your
   own reproduction, or reject with a cited ground).

## Return (your FINAL message; it reaches the orchestrator directly; under about 60 lines)

Head SHA reviewed; claims 1–5 PASS/FAIL with the measuring command and output line; lock
results; departures from the brief (additive vs behaviour-changing); findings (severity, in/out
of envelope, EXECUTED/REASONED, reproduction, file:line); the Codex pass (banner, assertions,
verdict, evidence md5s); verdict NO_BLOCKING or BLOCKING. Never post to a mailbox.
