# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 51** (session `clearwater-orchestrator-20261105-0932`). LIVE 2026-11-05 19:32Z. This file is a mid-generation CHECKPOINT unless the line below says ROLLED.
- **CHARC is gen 17, `clearwater-charc-20261105-0602`.** Re-verify the name in `comms/.launch-sessions.json` before every cue.
- **Seat folder `work/orch-g51/`:**
  - `gate.sh`, `watch2.sh` (gen-50 copies with the seat path changed);
  - `fill.py` (the 6.3b accept fill), `fill63c.py`, `rollstate.py`, `state-board.md`;
  - the drains and the posts.

  The g50 tools (`notices_cover.py`, `crcheck.py`, `assemble.py`) stay in `work/orch-g50/`; the g49 tools (`smoke_uia.py`, `dll_origin.py`, `census_measure.py`) stay in `work/orch-g49/`. Copy `gate.sh` / `watch2.sh` with `sed 's#orch-g51#orch-g52#g'`.
- **FRESH prompt** = `.claude/agents/implementer-codex-sol-high.md` + the brief at the worktree's HEAD + `dispatch-N.md`, joined, with `tr -d '\r'`. A **RESUMED prompt** is `dispatch-N.md` alone.
- **State worktree:** `.worktrees/orch-state-g51`. The successor removes it and adds its own.
- **Bash gauge at bring-up:** 40 ms. C: about 2.6 T free.
- **Paces** (20:23Z): Codex 10 % / 0.49; Claude 66 % / 1.346.

### BINDING RULES CARRIED (each verbatim in `comms/orchestrator/read/` or CLAUDE.md)

- **DESKTOP INPUT RULE and ENTRY-POINT ISOLATION RULE (CLAUDE.md hardware section).** Paste BOTH VERBATIM into EVERY dispatch (current text: `clearwater-review-evidence\wp6.3b\cell\dispatch-11.md`, with the QUIT_SCRIPT exception).
  - A cell-written GUI or proof script is reviewed at the seat: grep for SendKeys / AppActivate / SendInput / keybd_event / mouse_event / pyautogui / SetForegroundWindow.
  - Such a script is RUN AT THE SEAT FROM md5-CHECKED COPIES.
- **No seat or review run executes the DR-125 "before" shape:** a daemon blocked on `sys.stdin.buffer` at interpreter exit, or the OLD worker at `73453bdc`.
- **EVERY CLAUDE REVIEW PROMPT BANS `run_in_background`.** `codex_cell.py review` keeps only the reviewer's LAST message. Check that `review.txt` is a full report before acting.
- **Launch a Codex turn or review ONLY with the Bash tool's `run_in_background`, never a shell `&`.**
- **ROLLOVER TIMING (OWNER-RULED).** Below 400K a seat starts the next unit WHATEVER ITS SIZE; it rolls at the first clean boundary after 400K with nothing it started still running. At or past the cap, dispatch nothing new.
- **NO ROLLOVER WHILE A JOB RUNS (OWNER, 2026-11-02).**
- **NO PYTEST DURING A SERIAL OR FULLCLIP LEG** or a window; one heavy job at a time (gate, build, seat run). **Never edit a worktree a gate is running from** (gen 47 held two granted test edits until p64-s ended).
- **TWO CODEX SESSIONS ARE ALLOWED** (CHARC `a6934b58`), on disjoint files.
- **Codex turns:**
  - Run a turn with `uv run python scripts/codex_cell.py turn --worktree <ABS> --prompt <p> --evidence <dir> --turn N [--session=<id>] > <dir>\turn-N.driver.stdout 2>&1`, with run_in_background.
  - Commit with `codex_cell.py commit --worktree <ABS> --return-file <return-N.md>`.
  - Depth = the footer's `depth_input_tokens`; evaluate at about 200K, STOP near 250K.
  - FRESH prompt = `.claude/agents/implementer-codex-sol-high.md` + the brief at HEAD + `dispatch-N.md`, joined, with `tr -d '\r'`.
  - A RESUMED session's prompt = `dispatch-N.md` alone, with `tr -d '\r'`.
  - Never send the Write of a dispatch and the turn that reads it in ONE parallel batch.
- **Claude cells (Agent tool):** read depth with `uv run --no-sync python scripts/cell_depth.py --live 3 <name>` at dispatch, every yield and before any ruling; about 250K = evaluate, about 400K = STOP. Their reviewer is CODEX. Reviewer A: `cat review-prompt.md review-diff.txt | tr -d '\r' | codex exec -p strong -s read-only --skip-git-repo-check -o review.txt - > review.out 2>&1` from the DETACHED copy (`( cd <copy> && ... )`). Assertions: banner `gpt-6.1-sol` / `high`, `grep -ac '^ERROR'` = 0, `grep -ac '^tokens used'` = 1, the verdict.
- **Claude review of a Codex cell:** `codex_cell.py review --worktree <DETACHED copy> --base <sha> --prompt <p> --out <dir>`, in the background at the seat. Forms: `wp6.3a\B\r1\review-prompt-B.md` (full B), `wp6.3a\B\delta2\review-prompt-delta2.md` (a delta).
- **Gates:** `bash work/<seat>/gate.sh <worktree> <run-id> <legs...>` (background), plus a Monitor on `watch2.sh <run-id> <summary line count>`. Re-arm the Monitor at its 30-minute expiry. gate.sh's static leg runs win32 mypy only: run `uv run mypy --platform darwin` beside it (W-STATIC since WP6.4's accept).
- **Backslash-bearing Python is written with the Write tool**, never a heredoc or `sed -i` (gen 47's `sed` edit of a `\r` assert silently did nothing).
- **A bare `cd` moves the session's cwd.** Use ONLY `( cd X && ... )`, `git -C` and absolute paths. Gen 47 slipped once (`cd .worktrees/wp6.3a && grep ...`), restored in the next call.
- **QUIT_SCRIPT exception (owner's word, CLAUDE.md `1a38c935`):** `tests/test_app_startup.py::test_python_m_clearwater_starts_the_shell_and_exits_0` runs at the SEAT in gate legs and seat re-runs only. Every cell run keeps `-k 'not test_python_m_clearwater_starts_the_shell_and_exits_0'`.
- **No `rm -rf` on a command-substituted path** (the safety check refuses it). Use fixed paths under `work/`, or leave the folder.
- **Running downloaded build scripts is refused** by the auto-mode classifier ("code from external"). Read them as text (gen 48's `scriptsd_static.py`).

### Live board (RESUME HERE)

**WP6.3b ACCEPTED: main `34965dc5`** (record `docs/proofs/wp6.3b-accept.md`; gate `p63b2` green: parallel 7,936 / 207, serial 1,318 / 19, harness 423 after the seat's `dc088f60` registration of `.github/workflows/release.yml`). CHARC wrote AD-38 and DR-141..DR-147 at `c54b6f80`.

**WP6.3c IN FLIGHT (Codex lane, both nets Claude).**
- Brief `docs/briefs/wp6.3c-brief.md`: FINAL `b1a53c06` + Round-0 rulings `f395a0b1`.
- Worktree `.worktrees/wp6.3c`, branch `wp6.3c`. It has the local toml copied in and `uv sync --frozen --extra gpu` done.
- Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp6.3c\` (`cell\`, `seat\`, `A\`, `B\`, `gate\`).
- **Fork clone (gitignored, INSIDE the worktree so the sandbox can write it):** `.worktrees/wp6.3c/work/wp6.3c/FFmpeg-Builds`, `core.autocrlf false`. Base BtbN `5031c6f1`; the seat's fork commit is `9e8207b`. (A second clone `work/wp6.3c/FFmpeg-Builds` in the main tree is unused: a prune item.)
- **Q1 (fork name; whose clicks) is WITH THE OWNER via CHARC.** CHARC posts the answer. The fork run, real asset, re-pin and seat build wait on it.

| Turn | Commit | Content | Session, depth at yield |
| --- | --- | --- | --- |
| t1 round 0 | none | read-back; 4 STOP points, all ruled as recommended (`f395a0b1`) | `01a1ad64`, 202,602 |
| t2 | `1fe53812` | `--with-ffmpeg` retired; the fork's 3 files (seat-committed `9e8207b`, patch `713d89b0`) | `01a1ad6c`, 148,454 |
| t3 | (running at this write) | `--zip` + the verified-archive FFmpeg origin source + `.gitattributes` `ffmpeg-fork.patch -text` (seat-noted; CHARC may strike) | fresh |

**Remaining split (the cell's round-0 plan, CHARC-confirmed):**
- t4: the tag-gate hardening, B r3 adv 1 / 2 / 3 / 5 + real-git cases; the seat runs RED / GREEN outside the sandbox.
- t5: the DR-144 synthetic mechanism.
- t6: the DR-144 production records (needs the seat census).
- t7: the real re-pin + notices / docs (needs Q1 + the fork run).
- t8: convergence, then Reviewer A (Claude, `codex_cell.py review` on a detached `.worktrees/wp6.3c-rA`), then the seat proofs (real build `--notices --smoke --zip`, V4, `hevc_nvenc`, notices read), Reviewer B, the gate (static + darwin mypy, collect, parallel, serial, harness; no fullclip).

**Seat state:**
- t2 seat QA: 494 passed / 1 skipped outside the sandbox (real-git included); ruff, format, mypy x2 clean. Record `seat\t2-fork-checks.md`.
- `actionlint` on the fork workflow: clean.
- **`generate.sh` was REFUSED by the auto-mode classifier** (Code from External); a static proof is recorded instead. The owner may run it by hand.
- **DR-144 census subagent** (Claude, background, read-only) writes `seat\dr144-census.md` and `seat\dr144-texts\`. CHECK ITS RECORD before feeding t5 / t6. If this generation rolls before it returns, it dies with the pane: re-launch it from the same brief (`work/orch-g51/` has none; the brief is in this generation's transcript only, so re-brief from the CHARC addition in the WP6.3c brief).

**Dispatch notes:**
- Every WP6.3c turn so far is a FRESH session (each turn adds about 150-200K).
- The cell's pytest runner: start with `PYTHONPATH=scripts`, import pytest, REMOVE `PYTHONPATH`, then `pytest.main(-p sandbox_mkdir_shim -p no:cacheprovider ...)`. The plain `PYTHONPATH=scripts uv run pytest` form trips WP6.3b's `PYTHON*` refusal.
- The seat re-runs the modules outside the sandbox with `-n 4`, from `( cd .worktrees/wp6.3c && ... )`.

**Other standing items:**
- WP6.5 brief DRAFT `fea43245` (Mac inputs ruled).
- WP7.1 (Insta360 validation) brief is on main; CHARC commissions it after WP6.3c + 1.1.0.
- Push: CHARC batches the owner's push.
- Worktrees: main, `orch-state-g51` (yours to remove at rollover), `wp6.3c` (live), `wp6.3b`, `wp6.3b-rA`, `wp-dr125`, `wp6.1`, `wp6.2`, `wp6.3a`, `wp6.4` (kept for the prunes).
- **Prunes owed (the owner's word only; CHARC batches):**
  - gen 47-50 lists (see `git show 24801a23:docs/orchestrator-state.md`);
  - plus `work/orch-g50/gate-p63b`, `work/orch-g51/gate-p63b2`, the main-tree clone `work/wp6.3c/FFmpeg-Builds`, `.worktrees/wp6.3b-rA`, and `.worktrees/wp6.3b/work/g43-p63b*`.

### Gen-51 lessons

- **A new tracked file outside the instance prefixes fails ONLY the harness leg** (`.github/workflows/release.yml` at p63b2, after 40 minutes of green pytest legs). Run the harness on the package head before Reviewer B. WP6.3c's fill (seat clarification 7) binds it.
- **A Codex worktree's helper clone must live INSIDE the worktree** (its gitignored `work/`): the sandbox writes only the workdir. The cell edits files; the seat makes the commit and the `format-patch`.
- **The auto-mode classifier refuses running a downloaded build script** (`generate.sh`, as gen 48's). Read it statically and record that; offer the owner a by-hand run.
- **The bare-`cd` slip recurred twice in gen 51** (each restored in the next call). Only `( cd X && ... )`.

### Gen-50 lessons

- **A package worktree needs the uncommitted `clearwater.local.toml` copied in before its first GATE.** Its absence passes every cell run and every seven-module re-run, then fails 12 tests in the parallel leg. Copy it when the worktree is created.
- **A load-sensitive test bound shows up when the owner's desktop is busy.** Before calling a failure a defect, re-run it alone, and at the previous head in the review copy.
- **Codex's sandbox cannot run real-git tests** (Win32 error 5). Plan the seat run of the RED and GREEN from a throwaway detached worktree (`git worktree add --detach`, copy the new test in, run, `git worktree remove --force`).
- **A REASONED MAJOR about a third-party action is settled cheaply** by reading its source at the pinned SHA with a read-only `gh api repos/<o>/<r>/contents/<path>?ref=<sha>`.
- **`grep -c $'\r'` in this Git Bash counts LINES, not CR bytes** (a false CRLF alarm at t19). Count bytes in Python.
- **`mkdir -p` the basetemp's parent before a seat pytest run** (a FileNotFoundError at setup looked like a test failure).

### Gen-49 lessons

- **PyInstaller collects DLLs through PATH.** A Git Bash build bundles `/mingw64/bin`'s OpenSSL and any JDK's UCRT. Hash-bind every native, and sanitize PATH inside the build.
- **Python's `Path.write_text` writes CRLF on Windows** (state commit `6d2be2e5` carried 128 CRs). Use `write_bytes` or `newline='\n'`. The memory file is updated.
- **A heredoc turns `\a` into BEL** (a state line said `seat<BEL>ction-shas`). Write backslash paths with the Write tool, or as `chr(92)` in Python.
- **The bare-`cd` slip recurred four times this generation** (each restored in the next call). The safe forms are `( cd X && ... )`, `git -C` and absolute paths.
- **The `rm` safety check refuses `rm $VAR/$VAR`.** Use a literal absolute path.
- **A resumed Codex session is cheaper only while depth is below about 150K.** A turn that adds about 40-60K needs a fresh session at 175K and above.
- **Read the third-party trees yourself.** SciPy's own `LICENSES_bundled.txt` omits cobyqa and mislabels packaging; PBS's `downloads.py` libffi pin is not what its Windows build uses.

### Gen-48 lessons

- **A cell's own worktree hides CRLF hazards.** Codex writes new files with LF, and the system `core.autocrlf=true` (Git for Windows' etc/gitconfig) converts them only on a FRESH checkout. Test every byte-pinned file from a fresh detached checkout before trusting the cell's green.
- **Licence detectors over-match.** "(at your option) any later version" is in every GPL text's appendix, and "noncommercial" is in GPL-2 section 3(c). The project's own grant is in its source headers.
- **Debian-style `License: GPL-2` means GPL-2.0-only.** Read the per-file stanzas in `COPYING.md`.
- **A string scan of a stripped static binary cannot prove an object absent:** `vbi.c` showed 0 hits while certainly linked. Trace the call graph from a linked unit instead.
- **A Python print to a redirected file is block-buffered,** so a long script shows nothing until it exits. Add `flush=True` when you need progress.
- **The bare-`cd` slip recurred three times this generation** (each restored in the next call). Prefix with `cd /c/Users/rwsmy/clearwater &&` and use subshells for everything else.

### Earlier generations' lessons

They are in `git log -p -- docs/orchestrator-state.md` (gen 47's state at `26be709f`, gen 46's at `5b6d422f`). The binding ones are in the rules block above.
