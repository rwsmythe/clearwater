# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 51** (session `clearwater-orchestrator-20261105-0932`). LIVE 2026-11-05 19:32Z. ROLLED at the 400K cap at about 22:35Z, clean: nothing it started is running (no cell, no subagent, no gate; `tasklist` shows no pytest / pyinstaller).
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

**WP6.3b ACCEPTED: main `34965dc5`** (gate `p63b2` green; the seat's `dc088f60` registered `.github/workflows/release.yml`). CHARC wrote AD-38 and DR-141..DR-147 at `c54b6f80`.

**WP6.3c IN FLIGHT (Codex lane, both nets Claude). Head `3cc66e24`, clean.**
- Brief `docs/briefs/wp6.3c-brief.md` (on main): FINAL `b1a53c06` + rulings tails. The worktree has up to `d613a556` merged; **merge main again before the next dispatch** to pick up `c916f1f7`, the wheels rulings.
  - Round-0: `f395a0b1`.
  - The DR-144 census rulings: `d613a556`.
  - The DR-144 wheels rulings: `c916f1f7`.
- Worktree `.worktrees/wp6.3c` (local toml copied; `uv sync --frozen --extra gpu` done). Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp6.3c\` (`cell\` dispatch / prompt / return / turn 1-8; `seat\`).
- **Fork clone (gitignored, inside the worktree so the sandbox can write it):** `.worktrees/wp6.3c/work/wp6.3c/FFmpeg-Builds`, `core.autocrlf false`. Base BtbN `5031c6f1`; the seat's fork commit is `9e8207b`, exported as `tools/package/ffmpeg-fork.patch` (`713d89b0`; `.gitattributes` `-text`, CHARC-confirmed).
- **Q1 (fork name; whose clicks) is WITH THE OWNER via CHARC.** CHARC posts the answer. The fork run, real asset, re-pin and seat build wait on it. **Q1 is now the critical path.**

| Turn | Commit | Content | Session, depth at yield |
| --- | --- | --- | --- |
| t1 round 0 | none | read-back; 4 STOPs, all ruled as recommended (`f395a0b1`) | `01a1ad64`, 202,602 |
| t2 | `1fe53812` | `--with-ffmpeg` retired; the fork's 3 files (seat commit `9e8207b`, patch `713d89b0`) | `01a1ad6c`, 148,454 |
| t3 | `cbb25494` | `--zip` (`write_release_zip`, `source_commit_epoch`) + the verified-archive FFmpeg origin source + `.gitattributes` | `01a1ad7c`, 117,753 |
| t4 | `b56a04e0` | the tag gate's hardening (B r3 adv 1 / 2 / 3 / 5); the seat's real-git RED / GREEN in `seat\t4-real-git-proof.md` | `01a1ad89`, 85,393 |
| t5 | `fda8ee21` | the DR-144 mechanism (`embedded_hosts`, `embedded_in`); probe notices unchanged `3afe913e...` | `01a1ad90`, 129,126 |
| t6 | `6841797e` | report-only STOP: bzip2 had no upstream pin (seat resolved: `seat\dr144-bzip2-provenance.md`) | `01a1ad9f`, 145,524 |
| t7 | `ec59bd66` | CPython + Qt / shiboken rows: 60 rows / 17 hosts / 93 texts; `text_lines` field; probe `520df27e...` | `01a1ada5`, 202,689 |
| t8 | `3cc66e24` | Pillow / pillow-heif / numpy / SciPy: 43 component records, 93 host declarations, 53 texts; probe 128 rows / 103 embedded / `e4d9cd34...` | `01a1adc8`, 192,208 |

Seat QA of every turn: the outside-sandbox re-run of the five package modules (latest at t8: 604 passed / 1 skipped), ruff, format, mypy win32 + darwin, 0 CR in the committed blobs. From t5: positive and negative notices probes on fresh copies of `work\wp6.3b-stage1d`. From t7: every new text byte-checked against the seat-verified files (`work/orch-g51/textcheck.py`, `excerptcheck.py`, `textcheck2.py`).

**NEXT (gen 52), in order:**
1. **Seat fetches for the t8 STOPPED ROWS, per CHARC's `c916f1f7`.** Read the ruling text first.
   - **U-S1:** the ten rewritten SciPy originals' PUBLISHED licences (L-BFGS-B BSD-3; MINPACK; SLSQP, NNLS, LSODA, VODE, FITPACK, and the originals behind ID, CDFLIB and QUADPACK). Carry the ones that publish a licence; the public-domain / no-restriction netlib ones become limits lines.
   - **U-P2:** the AOM PATENTS (`aomedia.googlesource.com/aom`, the libaom 3.14.1 tag) and the libyuv PATENTS (`chromium.googlesource.com/libyuv`, Pillow's pinned commit), via googlesource `?format=TEXT`, recording commit + blob.
   - The Tcl/Tk header: a limits line.

   The remaining STOPPED / UNSURE items are in t8's report section ("Turn 8"), `docs/reports/wp6.3c-ffmpeg-bundle.md:1019`.

   Use a seat subagent (the form gen 51 used: read-only, `gh api` / googlesource GETs, byte-exact saves with blob checks, an LF record in `wp6.3c\seat\`). Then a cell turn (t9) loads those rows with the per-row STOP rule.
2. **When Q1 lands:** the owner forks + pushes `9e8207b`'s patch + dispatches the fork workflow (or authorises the seat in words). The seat records the run, the three-way digest, `-version` / `-encoders` and the archive listing. Then the cell turn for the re-pin + notices FFmpeg rows + root notices FFmpeg row + checklist / guide (design items 3, 4, 6), activating the strict lock schema with NO legacy bypass left.
3. **Convergence → Reviewer A** (Claude, `codex_cell.py review` on a detached `.worktrees/wp6.3c-rA`, prompt banning `run_in_background`) → the seat proofs:
   - the real build `--form onedir --ffmpeg-from <lock url> --ffmpeg-sha256 <hex> --notices --smoke --zip` (25 GB free; full Git Bash PATH as in 6.3b);
   - V4 on a bundled-binary export, and the `hevc_nvenc` capability line;
   - the notices read in full;
   - the smoke under the UIA watch (`work/orch-g49/smoke_uia.py`).

   Then Reviewer B, the harness on the head BEFORE B (seat clarification 7), and the gate (`work/orch-g52/gate.sh`: static + darwin mypy, collect, parallel, serial, harness; no fullclip).

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
