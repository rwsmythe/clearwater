# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 55** (session `clearwater-orchestrator-20261106-0342`). LIVE 2026-11-06 ~13:43Z. Bash gauge 37 ms. CHECKPOINT ~14:45Z (not a rollover): nothing running (no cell, no subagent, no review, no build, no gate; `tasklist`: only the owner's `swing` and the comms UI Python).
- **CHARC is gen 18, `clearwater-charc-20261105-1358`.** Re-verify the name in `comms/.launch-sessions.json` before every cue.
- **Seat folder `work/orch-g55/`:** `gate.sh` + `watch2.sh` (repointed to orch-g55), gate run `gate-p63c/`, posts (online, gate, ff, run sheet `runsheet-1.1.0.md`), drains 1-2, the accept-record draft and its fix scripts.
- **State worktree:** `.worktrees/orch-state-g55` (remove it at rollover; the successor adds its own).

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

**WP6.3c ACCEPTED and MERGED** (CHARC `be9b3edb`; main fast-forwarded to `c258f80a`: merge `d1fa44e5` of CHARC's accept writes `9fdce672`, then the record `docs/proofs/wp6.3c-accept.md`; harness 423 OK on both heads; 0 CR in every changed text blob). Gate p63c on `165acbdb`: static clean (+ darwin mypy), collect 9,817 identity exact, parallel 8,266 / 207 in 579 s, serial 1,318 / 19 in 2,035 s (QUIT_SCRIPT PASS), harness 423. Logs archived `clearwater-review-evidence\wp6.3c\gate\gate-p63c\`.

**Worktree release HELD (CHARC concurred `f4ddd1c5`):** removing `.worktrees/wp6.3c` / `.worktrees/wp6.3c-rA` deletes their ignored `work/` = a prune = the owner's word. CHARC carries the prune ask with the tag + push lines; re-run the DR-148 live-process check at release time; branches kept.

**NOW: the 1.1.0 release.** Run sheet posted to CHARC as a query (`work/orch-g55/runsheet-1.1.0.md`; post `80d9e284`), awaiting CHARC's rulings on Q1 (README line 4), Q2 (release notes file), Q3 (seat GPU proof via `--install-gpu-pack` under redirected roots), Q4 (Codex read of the bump) and the owner's "tag 1.1.0". Sequence after the word: bump in worktree `release-1.1.0` (pyproject, `__init__`, uv.lock root line, root notices title, `tests/test_version.py:20-22`) -> checks + Codex read -> ff main -> MAIN FREEZE until the tag -> build + proofs (`work/release`) -> local gate incl. fullclip + module-alone `test_gpu_pack_install.py` -> `git tag -a v1.1.0` -> the owner's two push lines -> workflow watch -> draft asset checks -> the owner's clean-account check -> CHARC's record -> the owner's Publish.

**Other standing items:**
- WP6.5 (Mac validation; brief `7c99e6b0`); WP7.1 (Insta360 validation) after 1.1.0.
- Open rows from WP6.3c: DR-148, DR-149, DR-150 (closes before any FFmpeg re-pin or 1.1.x), DR-151, DR-152.
- Push: the owner's word only (the 1.1.0 push lines are in the run sheet).
- **Prunes owed (the owner's word only; CHARC batches):** gen 54's list (gate basetemps under `wp-dr125`, `wp6.1`, `wp6.3b`; `work/orch-g51/*`; `work/wp6.3c/FFmpeg-Builds`; `work/orch-g52/seat63c/`, `us1/`; `work/wp6.3b-stage1d`; `work/wp6.3c-seat1`, `work/wp6.3c-seat-export1`, `work/orch-g54/fb1/`, `work/orch-g53/r2-asset` + `r2-extract`) plus the two WP6.3c worktrees (and their `work/`). Keep `work/wp6.3c-seat2` until 1.1.0 is published.

### Gen-55 lessons

- **A quoted heredoc turned `seat\\r2-codex-read\\review.txt` in a Python literal into two CRs** (the known collapse; the 2 CRs were caught by a CR count printed by the same script). And `Path.read_text` then turned the CRs into newlines, so the repair anchor had to be the newline form. Write ANY backslash-bearing script with the Write tool; build Windows paths with `chr(92)`.
- **The bare-`cd` slip recurred once in gen 55** (`cd <worktree> && ...` to read the brief; restored in the next call, nothing written). Only `( cd X && ... )`, `git -C` and absolute paths.
- **A worktree "release" is a prune** when it holds ignored `work/` content: hold it for the owner's word (CHARC concurred).

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
