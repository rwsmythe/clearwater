# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 50** (session `clearwater-orchestrator-20261105-0611`). LIVE 2026-11-05 16:11Z; ROLLED at the 400K cap at ~19:35Z. **The roll is clean: nothing it started is running.** Gate `p63b` was ABORTED at 19:30Z (see the board); its `gate.sh` / `watch2.sh` / pytest trees were killed with `taskkill /T` and confirmed gone. Re-check with `tasklist | grep -i -E 'pytest|pyinstaller'`; the only `codex.exe` processes are the owner's desktop app.
- **CHARC is gen 17, `clearwater-charc-20261105-0602`.** Re-verify the name in `comms/.launch-sessions.json` before every cue.
- **Seat folder `work/orch-g50/`:**
  - `gate.sh`, `watch2.sh`, `crcheck.py`, `assemble.py`;
  - `notices_cover.py`: the read-only notices coverage check (files, PYZ, both ways). Usage: `<venv python> -I work/orch-g50/notices_cover.py <Clearwater folder> <build-onedir/Clearwater>`;
  - the drains, the posts, `rollstate.py`, and `dispatch-19..23-body.md` / `-filled.md`;
  - **`wp6.3b-accept-draft.md`: the accept record, DRAFTED.** Fill `@@FOOTPRINT@@`, `@@GATE@@` and `@@MERGE@@`.

  The g49 tools (`smoke_uia.py`, `dll_origin.py`, `census_measure.py`) stay in `work/orch-g49/`. Copy `gate.sh` / `watch2.sh` with `sed 's#orch-g50#orch-g51#g'`.
- **FRESH prompt** = `.claude/agents/implementer-codex-sol-high.md` + the brief at HEAD + `dispatch-N.md`, joined, with `tr -d '\r'`. A **RESUMED prompt** is `dispatch-N.md` alone.
- **State worktree:** `.worktrees/orch-state-g50`. The successor removes it and adds its own.
- **Bash gauge at bring-up:** 25 ms (gen 50). C: about 2.6 T free.
- **Paces:** last read by gen 49 at 13:15Z (Codex 0.433 / Claude 1.362). Re-read both at the next commission (WP6.3c).
- **Host load:** the owner was running World of Warcraft during gen 50 (CPU about 34 %; suites about 2x slower). That is why t21 and t22 widened the smoke-test bounds.

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

**WP6.3b: BOTH NETS CONVERGED; THE GATE IS OWED.**
- **Head `260c63ae`** (turn 23), branch `wp6.3b`, clean. Review copy `.worktrees/wp6.3b-rA` is detached at `260c63ae`.
- **Gate `p63b` was ABORTED:** the parallel leg had 12 failures (10 failed + 2 errors), ALL `LocalConfigError: .worktrees/wp6.3b/clearwater.local.toml: file not found`. Every earlier package worktree (wp-dr125, wp6.1, wp6.3a, wp6.4) had a copy of the uncommitted root `clearwater.local.toml`; wp6.3b never got one. That is an environment gap, NOT code. The serial leg was killed at its start. Summary: `work/orch-g50/gate-p63b/summary.txt`.

**GEN 51, DO THIS FIRST, in order:**
1. **Copy the local config:** `cp clearwater.local.toml .worktrees/wp6.3b/clearwater.local.toml` (it is gitignored and uncommitted; never commit it). Confirm `git -C .worktrees/wp6.3b status --short` is still empty.
2. **The gate, run alone:** `bash work/orch-g51/gate.sh wp6.3b p63b2 static collect parallel serial harness` (background), plus a Monitor on `watch2.sh p63b2 0`; re-arm it at 30 min.
   - Afterwards: `( cd .worktrees/wp6.3b && uv run --no-sync mypy --platform darwin )` and the module-alone `tests/test_gpu_pack_install.py` (both green at the seat on `260c63ae`: 166 files clean; 113 passed).
   - **The QUIT_SCRIPT test runs in the serial leg** (the seat exception).
   - Expect the parallel leg at about 8,143 tests (p63b had 7,921 passed + 210 skipped + the 12 config failures). The serial leg has 1,337 tests.
   - Collection identity was already green in p63b: 9,487 = 8,143 + 1,337 + 7, 0 duplicates.
3. **The accept:**
   - Fill `work/orch-g50/wp6.3b-accept-draft.md`:
     - `@@FOOTPRINT@@` = `git -C .worktrees/wp6.3b diff --name-only 50a25b3b..260c63ae` (34 paths);
     - `@@GATE@@` = the p63b2 figures (and one line on p63b's abort);
     - `@@MERGE@@`.
   - Write it as `docs/proofs/wp6.3b-accept.md` IN THE WORKTREE, after merging main into `wp6.3b` (main has only CHARC / orchestrator docs since `50a25b3b`; check with `git diff --stat 50a25b3b..main -- src tests tools`).
   - Run the harness gate there (`docs/proofs/` is an instance-surface prefix; no registration needed).
   - Commit; blob-check 0 CR; `git merge --ff-only wp6.3b` on main.
   - Copy `work/orch-g51/gate-p63b2/` to `C:\Users\rwsmy\clearwater-review-evidence\wp6.3b\gate\`.
4. **The accept post to CHARC** with the main hash. CHARC writes AD-38 and the register rows on it (list in the draft's Dispositions; CHARC ruled all of them already), and corrects CLAUDE.md's stale "v1.0.0 not pushed" line. Cue `clearwater-charc-20261105-0602`.
5. **Then WP6.3c** (brief DRAFT `a86e3c24` + CHARC's notes: MAJOR 1's embedded-components item; B r3 adv 1 / 2 / 3 / 5; B r2 adv 5).
   - Fill Q1-Q4 when you reach it. Q3 = any pending `--zip` / origin-source branch in 6.3b's accepted code, by file:line: grep `build.py` for `--zip`, `with_ffmpeg`, `ffmpeg_from`, `pending`.
   - Read both paces at commission.

**Gen-50 ledger (WP6.3b, all committed on `wp6.3b`; evidence `C:\Users\rwsmy\clearwater-review-evidence\wp6.3b\`):**

| Turn | Commit | Content | Session, depth at yield |
| --- | --- | --- | --- |
| t19 | `65784337` | the data turn under the Turn-18 ruling: THREE strict provenance kinds; libffi, MSVC (11 files), Mesa + LLVM, the five SciPy blocks, the namespace mapping; the seat provenance record `seat\native-licences-provenance.md` | RESUMED `01a1ac75`, 170,321, retired |
| t20 | `8938edd3` | the A r3 remediation: k1, k2 (the project LICENSE LF-normalised), F1-F4, A1 (magic bytes), A3, A4 | FRESH `01a1aca5`, 174,245 |
| t21 | `91f90c8f` | `job_case` bound 1 -> 10 s (the load flake) | FRESH `01a1acc4`, 91,904 |
| t22 | `4e848bf2` | the B r1 remediation, items 2-12: venv-only trust + the `PYTHON*` refusal; the stem rule; the presenter bounded on every path; real pipe holding; bounds; the win32 skip; the tag gate; the guide's "from 1.1.0" sections; mutant tests; `BuildEnvironmentError`; `setup-uv` cache off + checksum | FRESH `01a1ace3`, 180,046 |
| t23 | `260c63ae` | the B r2 remediation: re-fetch the annotated tag after checkout; the real-git test (the seat ran it OUTSIDE the sandbox: RED at `4e848bf2`, GREEN 3 of 3, `seat\t23-real-git-proof.md`); MINOR 2, adv 3, adv 7 | FRESH `01a1ad0c`, 111,793 |

**Nets:**
- A r3 `65784337` NO_NEW (k1, k2, F1-F5, A1-A4);
- B r1 FULL `91f90c8f` NEW_MAJOR (MAJOR 1 embedded components -> CARVED to WP6.3c; 8 MINOR);
- B r2 delta `4e848bf2` NEW_MAJOR (the checkout tag overwrite, seat-confirmed from `actions/checkout@11bd7190` source);
- **B r3 delta `260c63ae` NO_NEW_CRITICAL_MAJOR** (6 adv: 1, 2, 3, 5 to 6.3c; 4 a record line; 6 corrected in the accept record).

**Seat proofs:**
- rebuilds `work/wp6.3b-stage1b` / `1c` / `1d` from the FULL Git Bash PATH: origin PASS, `dll_origin` 0 foreign;
- notices `3afe913e...` (1c = 1d), coverage exact (1,536 entries / 25 rows);
- smoke under UIA `seat\smoke-uia\run1` (`windows_seen` []).

**Seat QA at `260c63ae`:** seven modules 714 passed + 1 skipped; installer alone 113; ruff, format, mypy win32 + darwin clean; 0 CR.

**Other standing items:**
- **WP6.5** brief DRAFT `fea43245` (+ CHARC's notes: A r3 F5 darwin PATH / Mach-O origin rule; B r2 adv 4 notices skip; the darwin smoke containment).
- **Push:** main is ahead of `origin/main`; CHARC batches the owner's push.
- **Worktrees:** main, `orch-state-g50` (remove it), `wp6.3b` (live), `wp6.3b-rA` (review copy), `wp-dr125`, `wp6.1`, `wp6.2`, `wp6.3a`, `wp6.4` (kept for the prunes).
- **Prunes owed (the owner's word only; CHARC batches):**
  - gen 47 / 48 lists (in `git show e453d30b:docs/orchestrator-state.md`);
  - gen 49's (`work/seat63b-t12..t17*`, `work/seat63b-m1`, `work/wp6.3b-stage1`, `work/wp6.3b-stage1-cleanpath`);
  - gen 50's (`work/wp6.3b-stage1b`, `1c`, `1d` and their `.log`s, `work/seat63b-t19..t23`, `work/orch-g50/gate-p63b`, `work/c63b-*` in the worktree, and `.worktrees/wp6.3b-rA` after the accept).

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
