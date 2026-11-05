# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 52** (session `clearwater-orchestrator-20261105-1241`). LIVE 2026-11-05 22:41Z. (Interim state, written mid-generation while t10 runs; the rollover overwrites it.)
- **CHARC is gen 17, `clearwater-charc-20261105-0602`.** Re-verify the name in `comms/.launch-sessions.json` before every cue.
- **Seat folder `work/orch-g52/`:** `gate.sh`, `watch2.sh` (seat path g52), `rules-block.md`, `textcheck2.py` (fits any turn's new native-licences files), `probe63c.py` (seat notices probe: `uv run --no-sync python -I work/orch-g52/probe63c.py <worktree> <fresh out dir> <relpath to append a byte to>`), dispatch-9 / dispatch-10 parts, the drains and the posts. Seat pytest logs under `work/orch-g52/seat63c/`.
- **State worktree:** `.worktrees/orch-state-g52`. **Review copy:** `.worktrees/wp6.3c-rA` (detached at `a268a8e0`, `.venv` synced, local toml copied; re-point it to the t10 head before Reviewer A).
- **Bash gauge at bring-up:** 29 ms. C: 2.6 T free.

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

**WP6.3c IN FLIGHT (Codex lane, both nets Claude).** Brief `docs/briefs/wp6.3c-brief.md` FINAL + tails through "Turn-9 ruling" (`70c85062`). Worktree `.worktrees/wp6.3c`; evidence `C:\Users\rwsmy\clearwater-review-evidence\wp6.3c\` (`cell\` dispatch / prompt / return / turn-N; `seat\`; `A\r1\review-prompt-r1.md` DRAFTED for t2-t9 -- update head + the limits sentence for t2-t10 before running).

| Turn | Commit | Content | Depth at yield |
| --- | --- | --- | --- |
| t1-t8 | `3cc66e24` | see gen 51's state (`c50f20dd`) | |
| t9 | `a268a8e0` | U-S1 originals (L-BFGS-B, MINPACK CRLF, SLSQP, ID 0.4, DCDFLIB), AOM + libyuv PATENTS, libaom fastfeat / vector / x86inc; 125 records; seat 617/1; seat probe `e0621121` 140 rows / 1,536 entries (= cell); `_slsqplib` +1 byte refused | 160,100 (fresh) |
| t10 | RUNNING (dispatched ~23:47Z, head `f516a0f3`) | the `limits` manifest list + rendered section "Components with no carried licence text, and limits", 17 entries (CHARC's 15 + COLAMD + BASICLU/IPX, told to CHARC) | |

Seat record for t9: `wp6.3c/seat/dr144-us1-patents.md` sha256 `437aa040...c97c` (46,939 bytes; texts under `dr144-texts/{lbfgsb,minpack,slsqp,id_dist,cdflib,aom,libyuv}`), by the gen-52 subagent `seat-us1-fetch` (stood down). **Rule (CHARC):** pin a seat record's hash in a dispatch only after the producing subagent has returned (t9's first launch was killed for this).

**NEXT, in order:**
1. t10 return -> seat QA (five modules outside the sandbox incl. `tests/test_release_workflow.py`; ruff / format / mypy x2; `probe63c.py` positive + negative on fresh stage-1d copies; text checks; codex_cell commit; blob CR check) -> post + cue CHARC.
2. Reviewer A r1 (Claude) over t2-t10: re-point `.worktrees/wp6.3c-rA` to the t10 head (`git -C ... checkout --detach <sha>`), base = `git merge-base main wp6.3c`, diff excluding `tools/package/native-licences` and `docs/proofs`, `codex_cell.py review --worktree <ABS copy> --base <sha> --prompt <A\r1 prompt> --out <A\r1>` in the background; check review.txt is a full report.
3. Q1 (fork run) with the owner via CHARC: then the re-pin turn (design items 3, 4, 6; strict lock schema, no legacy bypass), A delta, seat build proofs, B, harness, gate, accept.

**Dispatch notes:**
- Every WP6.3c turn is a FRESH session (each adds 85-200K).
- Dispatches are assembled as head + `work/orch-g51/rules-block.md` (the two verbatim CLAUDE.md rules + the QUIT_SCRIPT exception) + body, then the prompt = cell definition + the brief at the worktree's HEAD + dispatch, with `tr -d '\r'`.
- The cell's pytest runner removes `PYTHONPATH` before `pytest.main` (the plain `PYTHONPATH=scripts` form trips WP6.3b's `PYTHON*` refusal).
- **The per-row STOP rule** (from t7): one missing input leaves that row out under STOPPED ROWS; it is not a turn STOP.
- The seat re-runs `( cd .worktrees/wp6.3c && uv run --no-sync pytest -q -n 4 ... five modules ... )`; the real-git cases pass only outside the sandbox.

**Other standing items:**
- WP6.5 brief DRAFT `fea43245`.
- WP7.1 (Insta360 validation) after WP6.3c + 1.1.0.
- Push: CHARC batches the owner's push.
- Worktrees: main, `orch-state-g51` (remove it), `wp6.3c` (live), `wp6.3b`, `wp6.3b-rA`, `wp-dr125`, `wp6.1`, `wp6.2`, `wp6.3a`, `wp6.4`.
- **Prunes owed (the owner's word only; CHARC batches):**
  - gen 47-50 lists (`git show 24801a23:docs/orchestrator-state.md`);
  - `work/orch-g50/gate-p63b`, `work/orch-g51/gate-p63b2`, `work/orch-g51/seat63c/` (probe copies, about 2 GB);
  - the main-tree clone `work/wp6.3c/FFmpeg-Builds`, `work/orch-g51/bzip2`, `work/orch-g51/dr144*`;
  - `.worktrees/wp6.3b-rA`, `.worktrees/wp6.3b/work/g43-p63b*`.

### Gen-51 lessons

- **A new tracked file outside the instance prefixes fails ONLY the harness leg** (`.github/workflows/release.yml` at p63b2, after 40 minutes of green pytest legs). Run the harness on the package head before Reviewer B. WP6.3c's fill (seat clarification 7) binds it.
- **A Codex worktree's helper clone must live INSIDE the worktree** (its gitignored `work/`): the sandbox writes only the workdir. The cell edits files; the seat makes the commit and the `format-patch`.
- **The auto-mode classifier refuses running a downloaded build script** (`generate.sh`, as gen 48's). Read it statically, record that, and offer the owner a by-hand run.
- **A census subagent at the seat is the right tool for licence evidence** (gen 51 ran two: 240 + 170 blob-verified texts). Spot-check 3-4 of its claims in the binaries / against GitHub before relaying, and byte-check the cell's copied texts against the seat files after the cell turn.
- **A cell that meets one missing input stops the whole turn unless told otherwise** (t6 cost a turn over bzip2). Every data-loading dispatch now carries the per-row STOP rule.
- **A quoted heredoc still collapsed `\\U` in a Python string** (a dispatch-7 build script died on a `\U` escape). Write any backslash-bearing script with the Write tool. (Memory: bash-heredoc-backslash-collapse.)
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
