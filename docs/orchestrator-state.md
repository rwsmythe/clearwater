# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 54** (session `clearwater-orchestrator-20261106-0045`). LIVE 2026-11-06 ~10:45Z. ROLLED at ~390K (the 400K cap's last clean boundary, CHARC-sanctioned: "hand over to gen 55 only at the rebuild's clean return with nothing running") at about 13:45Z. Nothing it started is running: no cell, no subagent (the `fb1-census` subagent returned and is idle), no review, no build, no gate (`tasklist`: no pytest / pyinstaller / codex exec / Clearwater.exe of ours; the two `codex.exe` are the owner's desktop app).
- **CHARC is gen 18, `clearwater-charc-20261105-1358`.** Re-verify the name in `comms/.launch-sessions.json` before every cue.
- **Seat folder `work/orch-g54/`:**
  - `gate.sh` (L = `work/orch-g54/gate-<run>`), `watch2.sh` (repointed to orch-g54), `build_uia.py` (gen 53's, unchanged);
  - `review63c-g54.py` (the review wrapper: excludes `native-licences`, `THIRD_PARTY_NOTICES.md` and `ffmpeg.lock.json` from the appended diff; the prompts tell the reviewer to read them on disk);
  - `fb1-census-prompt.md` (the census subagent's brief), dispatch-15/16/17 parts + prompts, commit-15/17/f6 messages, drains 1-8, posts, qa15/16/17 logs, build2 driver log.
- **State worktree:** `.worktrees/orch-state-g54` (remove it; add your own). **Review copy:** `.worktrees/wp6.3c-rA` (detached at `1623e3c6`, `.venv` synced).
- **Seat outputs (prune candidates after accept + 1.1.0, the owner's word only):** `work/wp6.3c-seat2` (build 2, ~800 MB; the one of record now), `work/wp6.3c-seat1` + `work/wp6.3c-seat-export1` (superseded build 1), `work/orch-g54/fb1/` (305 crate archives + extractions), `work/orch-g53/r2-asset` + `r2-extract`, `.worktrees/wp6.3c/work/seat63c-13..17`, `.worktrees/wp6.3c/work/c63c-*`.

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
- **Codex turns** (FILES CHANGED must be one literal path per line, or `codex_cell.py commit` refuses; commit by pathspec in the worktree then):
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
- **A bare `cd` moves the session's cwd.** Use ONLY `( cd X && ... )`, `git -C` and absolute paths. It slipped in every generation 47-54 (gen 54: three times); each was restored in the next call.
- **QUIT_SCRIPT exception (owner's word, CLAUDE.md `1a38c935`):** `tests/test_app_startup.py::test_python_m_clearwater_starts_the_shell_and_exits_0` runs at the SEAT in gate legs and seat re-runs only. Every cell run keeps `-k 'not test_python_m_clearwater_starts_the_shell_and_exits_0'`.
- **No `rm -rf` on a command-substituted path** (the safety check refuses it). Use fixed paths under `work/`, or leave the folder.
- **Running downloaded build scripts is refused** by the auto-mode classifier ("code from external"). Read them as text (gen 48's `scriptsd_static.py`).

### Live board (RESUME HERE)

**WP6.3c: ALL REVIEW NETS CONVERGED; SEAT BUILD 2 GREEN; GATE NOT YET RUN. Gate head `165acbdb`** (`.worktrees/wp6.3c`, branch `wp6.3c`, clean) = turn 17 `1623e3c6` + the seat's F6 docs `51b90eb0` + main `5801371d` (DR-150) merged. Codex lane, both nets Claude. Brief `docs/briefs/wp6.3c-brief.md` with its last sections "Reviewer B r1 rulings" and "F-B1 census rulings". Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp6.3c\` (`cell\`, `seat\`, `A\r1-r5\`, `B\r1-r2\`).

| Step | Commit / record | Content |
| --- | --- | --- |
| B r1 (gen 53) | `B\r1\review.txt` | NEW_CRITICAL_MAJOR: F-B1 (Rust std, rav1e / librsvg crates, GCC runtime statically linked, no notice rows) + F-B2..F-B10. CHARC ruling `395c5c12`: option A, fix before accept; new lock list `toolchain_runtime` |
| F-B1 census | `seat\fb1-census.md` `fb9c9463...`, `seat\fb1-rows.json` `2e7d796e...`, `seat\fb1-texts\index.json` `faabab36...` | Seat subagent (Claude). 232 rows (rust-std 4, cargo-crate 223, gcc-runtime 5; toolchain 19 / rav1e 65 / librsvg 148; basis compile-log 213 / lock-graph 13 / binary 6), 157 distinct texts, 305 / 305 crate archives = lock checksums; Rust 1.99.1 `58cf8f9c`, GCC 16.2.0 crosstool-NG 1.29.0.7 `78d4ac73`; MinGW CRT = the `mingw` stage row. CHARC reviewed: no finding; Unicode-3.0 COMPATIBLE; HP / SGI `stl_*` notices carried; host-only `cc` / `find-msvc-tools` / `shlex` excluded |
| t15 | `175b241c` (seat-committed by pathspec; `codex_cell.py commit` refused the cell's free-text folder line) | the `toolchain` object + 232 `toolchain_runtime` rows + 157 texts in `tools/package/native-licences/ffmpeg-toolchain/`; fail-closed validator (SPDX atom list, stage / flag coverage, pins); notices rows; F-B2/3/5/6/7/8 folds; F-B10 + census limits sentences. Seat: texts = census index, rows = census rows field by field. QA 777 / 1 |
| A r4 | `A\r4\review.txt` | NO_NEW_CRITICAL_MAJOR, 5 minors + 9 adv, folded in t16 (seat ruling; CHARC concurred, no A r5 over t16) |
| t16 | `fb759249` | the A r4 folds (directory set equality, non-crate provenance binding, writer test, non-empty static flags, ASCII-space parser, release-tag fullmatch, strict text names, crate source label, agreement test, path override). QA 800 / 1 |
| B r2 | `B\r2\review.txt` | NO_NEW_CRITICAL_MAJOR; **F-B1..F-B10 CLOSED** (F-B4 = DR-149); 3 minors + 7 adv; CHARC: fold all in t17 (register-row alternative declined), then A r5 over t17 only = A's FIFTH and final round |
| t17 | `1623e3c6` (+ seat-GRANTED `tests/test_tools_package_smoke.py:403` "8" -> "10 component rows") | census bound to the asset (`toolchain.census_build_commit` / `census_asset_sha256`); libgcc + libstdc++ required on `--enable-libx265`; bundle-time `/rustc/<commit>/` + GCC version byte check on the verified `ffmpeg.exe`; release-tag anchoring tests; `notices.py --root-annex [--write|--check]`; `linkage` {proven, superset}; `chosen: MIT` on language-tags + fast_float; backtrace gitlink `d902726a` bound. Seat: lock diff = exactly the permitted fields. QA **827 / 1**, annex `--check` 0 |
| A r5 (FINAL) | `A\r5\review.txt` | **NO_NEW_CRITICAL_MAJOR** (converged in five rounds). F1 minor (`chosen` not bound to the carried texts) + F2-F5 adv -> **DR-150** (CHARC, main `5801371d`: MUST close before the next FFmpeg re-pin or any 1.1.x; non-blocking for 1.1.0); F6 docs -> seat `51b90eb0` |
| seat build 2 | `seat\build2\record.md` | at `1623e3c6` under the UIA watch: exit 0, 184.6 s, no window; origin PASS; **notices PASS (1540 entries; 473 component rows)**; every smoke row PASS (ffmpeg / ffprobe version, `hevc_nvenc; libx265`); zip `19eaf7d8...a758` = sidecar. Supersedes build 1. Export proof `seat\export1` stands (FFmpeg bytes unchanged) |

**NEXT, in order (gen 55):**
1. **Harness on the gate head:** `( cd .worktrees/wp6.3c && uv run --no-sync python -m unittest discover -s tests/harness > <log> 2>&1 )`. New tracked files since the last harness run: `tools/package/native-licences/ffmpeg-toolchain/*` (under `tools/`, an instance prefix; t15's scope audit said no registration needed): CONFIRM with this run.
2. **The gate** on `165acbdb` (copy `work/orch-g54/gate.sh` to your seat folder and repoint `L`; `.worktrees/wp6.3c/clearwater.local.toml` is present (seat-checked at roll)): `bash work/<seat>/gate.sh wp6.3c <run-id> static collect parallel serial harness` (background, Bash `run_in_background`) + a Monitor on `watch2.sh <run-id>`, re-armed at its 30-minute expiry; `uv run mypy --platform darwin` beside it (W-STATIC). No fullclip. The serial leg runs the QUIT_SCRIPT test at the seat (recorded exception). No pytest elsewhere while serial runs.
3. **Cue CHARC** with the gate legs + harness; CHARC writes the accept. Then the merge to main (orchestrator), and the 1.1.0 release per `docs/release-checklist.md` (owner's word for tag / push).

**Other standing items:**
- WP6.5 (Mac validation; brief `7c99e6b0` has the Mac's details); WP7.1 (Insta360 validation) after WP6.3c + 1.1.0.
- Register rows of this package: DR-149 (F-B4, non-host natives of a carried parent), DR-150 (A r5 residuals). Both listed on the accept record.
- Push: CHARC batches the owner's push (Clearwater's own pushes and tags stay the owner's word).
- DR-148: before releasing a review copy, check for live processes under it.
- Worktrees: main, `orch-state-g54` (remove it), `wp6.3c` (gate head), `wp6.3c-rA` (review copy at `1623e3c6`), `wp6.3b`, `wp-dr125`, `wp6.1`, `wp6.3a`, `wp6.4`.
- **Prunes owed (the owner's word only; CHARC batches):** as gen 53's list (gate basetemps under `wp-dr125`, `wp6.1`, `wp6.3b`; `work/orch-g51/*`; the main-tree clone `work/wp6.3c/FFmpeg-Builds`; `work/orch-g52/seat63c/`, `us1/`), plus after WP6.3c's accept: `work/wp6.3b-stage1d`, the seat outputs listed above.

### Gen-54 lessons

- **A heredoc collapsed the backslashes in a Python string literal holding a Windows path** (`'C:\Users\...'` -> a `\U` escape SyntaxError): the dispatch-17 head fix failed, and because the Write of the fix and the turn launch went out in ONE parallel batch, turn 17 launched with a stale pointer (killed seconds in, relaunched; `cell\turn-17-aborted.*`). Fix dispatch text with the Write tool, and never launch a turn in the same batch as the edit it depends on.
- **`codex_cell.py commit` refuses a FILES CHANGED line that is not a literal path** (t15 wrote "folder/ -- 157 new texts;"; nothing was committed). Dispatches now say "one literal repository-relative path per line, nothing else". When it refuses, commit by pathspec inside the worktree (its own index).
- **A census subagent can finish before a mid-run addendum lands, then pick it up as a SECOND pass** (its first return lacked the `basis` field; the queued message re-woke it). Check every binding against the returned files, not the report's prose.
- **A cell that appends to a report with PowerShell `Add-Content` leaves a few CRLFs in an otherwise-LF file**: anchors built for one line-ending style miss. Inspect the tail bytes before a scripted edit; git normalises on commit (blob CR 0).
- **Ask whether a review finding needs a NEW field before ruling "key it on the existing one"**: B r2 adv 5 wanted the sentence "basis-dependent", but `basis: lock-graph` covered 11 linked std crates; t17 added `linkage`.
- **The bare-`cd` slip recurred three times in gen 54** (each restored in the next call or the same one). Only `( cd X && ... )`, `git -C` and absolute paths.

### Gen-53 lessons

- **Pinning a release TAG can fail against a build system's floating dependency pins.** BtbN's scripts track dependency HEADs, and FFmpeg's `n9.0.2` predates a fix those pins need. Pin the maintained branch at a full 40-hex commit (`git checkout --detach` after the clone), never a short sha or a tag, and check the binary's `-g` hash (F3b).
- **Check the reviewer MODEL in the brief's Lane row before naming it.** Gen 53 told CHARC "B (Codex)" three times for a Codex-lane package whose nets are both Claude. A seat-made artifact in a Codex-lane package then has NO cross-model reader unless one is added (CHARC ruled a read-only Codex read).
- **A substring licence check misfires on `--disable-*` flags** (`libfdk-aac` matched `--disable-libfdk-aac`). Test the ENABLE flag.
- **`grep -c $'\r'` inside a `for` loop in `$( )` counted lines and reported phantom CRs**, and once broke quoting. Count CR bytes with `work/orch-g53/crcheck.py`.
- **The bare-`cd` slip recurred four times in gen 53** (each restored in the next call, none during a write). Only `( cd X && ... )`, `git -C` and absolute paths; never `cd X 2>/dev/null;` "just to read".
- **A cell-written proof driver is cheap and safe when the seat freezes a copy and reads all of it before running** (export_proof: 1,006 lines; isolation before any product import; PATH limited to the bundle).

### Gen-52 lessons

- **The auto-mode classifier refuses outward and destructive acts even with the owner's recorded authorisation** ("Create Public Surface" on `gh repo fork`; "Irreversible Local Destruction" on the prune script). Do not work around it: write the exact commands / script, record them in the evidence folder, and ask the owner to type them with `!` in this pane (output lands in the session for the record). Tell CHARC in the same breath.
- **Pin a seat record's hash in a dispatch only after its producing subagent has RETURNED** (CHARC rule). t9's first launch was killed a minute in because the fetch subagent re-hashed the record after the dispatch pinned it; an addendum sent mid-run crossed with its reply.
- **An `ff-only` merge into the state worktree checks files out CRLF** (system `autocrlf=true`); a following `git -c core.autocrlf=false commit -- <file>` commits the CRLF working copy even when the edit itself was refused (`037a2e1f`, 151 CRs, fixed forward in `cd4cbef0`). Before committing a docs file from a worktree, WRITE its full LF bytes with Python (`git show <rev>:<path>` as the base) and check the blob's CR count after the commit; never let a chained commit run after a failed edit (use `&&` only after a step that exits non-zero on failure, and check the script's exit).
- **`codex_cell.py review` excludes only `docs/proofs` and `uv.lock`;** a package with a large data surface needs `work/orch-g52/review63c.py` (adds excludes) or the reviewer drowns in the manifest.
- **The bare-`cd` slip recurred twice in gen 52** (each restored in the next call). Only `( cd X && ... )`, `git -C` and absolute paths.
- **A cell dispatched before a ruling lands misses the ruling's additions** (t11 lacked CHARC's literal content-hashed test): check every ruling against the next return and fold the gap into a small fresh turn.

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
