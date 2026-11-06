# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 53** (session `clearwater-orchestrator-20261105-1458`). LIVE 2026-11-06 ~01:00Z. ROLLED at the 400K cap at about 10:44Z, clean: nothing it started is running (no cell, no subagent, no review, no gate, no fork run; `tasklist` shows no pytest / pyinstaller / codex exec / Clearwater.exe of ours).
- **CHARC is gen 18, `clearwater-charc-20261105-1358`.** Re-verify the name in `comms/.launch-sessions.json` before every cue.
- **Seat folder `work/orch-g53/`:**
  - `gate.sh` (copied from g52), `watchrun.sh` / `watchrun2.sh` (the fork-run watchers);
  - `make-r2.py` (built the r2 fork commit in the clone with every binding of CHARC's ruling asserted; exported the patch);
  - `build_uia.py` (the FULL local release build under the read-only UIA window watch: `uv run --no-sync python work/orch-g53/build_uia.py <worktree> <NEW out> <uia_watch.ps1> <evidence dir>`; reads the URL and sha256 from the lock);
  - `export_proof.seat.py` (the bundled-FFmpeg proof: capability probe + one export through the FROZEN worker + encoder tag + V4; written by a Claude subagent, read in full by the seat, run from this copy: `( cd .worktrees/wp6.3c && uv run --no-sync python <abs>\export_proof.seat.py <Clearwater.exe> <source> <NEW out> --worktree <abs> --timeout 1200 --v4-timeout 1200 )`);
  - `seat-facts-r2.py` / `append-run2.py` (the asset facts), `crcheck.py` (CR bytes per blob: `python -I work/orch-g53/crcheck.py <repo> <rev...> -- <paths...>`);
  - dispatch-13 / 14 parts, prompts, drains 1-4, posts.
- **State worktree:** `.worktrees/orch-state-g53` (remove it; add your own). **Review copy:** `.worktrees/wp6.3c-rA` (detached at `80914e17`, `.venv` synced, local toml copied).
- **Seat outputs (prune candidates after accept + 1.1.0, the owner's word only):** `work/wp6.3c-seat1` (build 1, ~800 MB), `work/wp6.3c-seat-export1`, `work/orch-g53/r2-asset` + `r2-extract` (~550 MB), `.worktrees/wp6.3c/work/seat63c-13`, `seat63c-14`.

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
- **A bare `cd` moves the session's cwd.** Use ONLY `( cd X && ... )`, `git -C` and absolute paths. It slipped in every generation 47-53 (gen 53: four times); each was restored in the next call.
- **QUIT_SCRIPT exception (owner's word, CLAUDE.md `1a38c935`):** `tests/test_app_startup.py::test_python_m_clearwater_starts_the_shell_and_exits_0` runs at the SEAT in gate legs and seat re-runs only. Every cell run keeps `-k 'not test_python_m_clearwater_starts_the_shell_and_exits_0'`.
- **No `rm -rf` on a command-substituted path** (the safety check refuses it). Use fixed paths under `work/`, or leave the folder.
- **Running downloaded build scripts is refused** by the auto-mode classifier ("code from external"). Read them as text (gen 48's `scriptsd_static.py`).

### Live board (RESUME HERE)

**WP6.3c IN FLIGHT (Codex lane, BOTH NETS CLAUDE, brief line 8). Head `80914e17` (t14 `990f3cf5` + main merge), clean. Seat QA: five package modules 698 passed / 1 skipped with real git; ruff / format / mypy win32 + darwin clean; harness 423 OK.** Brief `docs/briefs/wp6.3c-brief.md` FINAL + tails, incl. the amendment after fork run 1 (`357a1fc2`, `34c2362a`). Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp6.3c\` (`cell\`, `seat\`, `A\r1-r3\`, `B\r1\`).

| Step | Commit / id | Content |
| --- | --- | --- |
| fork run 1 | run `42156511472`, fork `92d0b6a6` (branch `wp6.3c-nozvbi`, KEPT) | FAILED: the `n9.0.2` tag vs BtbN's openapv >= 1.1 (`oapvm_create`); FFmpeg's fix `a7502e5f` is on `release/9.0` after the tag. `seat\fork-run.md` |
| r2 patch (SEAT-made, Claude) | `40b8ae3b`, trailer `4687ff19`; fork commit `d77b8352` (branch `wp6.3c-nozvbi-r2`, the fork's default) | CHARC ruling d5893fca (option A): `build.sh` + ONE `git checkout --detach b204e94e90fca64045e9ca7dd44c65678c7eb29e`; addins upstream; TAGNAME `ffmpeg-9.0-gb204e94e-nozvbi-<sha7>` |
| fork run 2 | run `42180812511` | SUCCESS. Asset `ffmpeg-n9.0.2-47-gb204e94e90-win64-gpl-9.0.zip` 194,771,780 B, sha256 `3534afe3...0c20` three-way equal; F3 (lightweight tag on `d77b8352`) and F3b PASS. `seat\fork-run.md` "Run 2", `seat\fork-acts.md`, `seat\fork-recipe-r2.md`, `seat\actionlint.md` (clean) |
| t13 | `749fd30b` | lock schema 2 (fork asset; `ffmpeg_ref` + `ffmpeg_commit`; no `ffmpeg_tag`), strict validator, notices from the lock, minor 1, checklist / guide / report; seat-granted test line (`2028-10` -> "rebuild FFmpeg in the fork"). Depth 150K |
| A r3 | `A\r3\review.txt` | delta `5ecec475..f5658a05`: NO_NEW_CRITICAL_MAJOR; minors 1-5 + advisories 6-8 folded in t14; advisory 9 at the seat (`4687ff19`); advisory 10 CHARC (`34c2362a`). **CHARC: no A r4; A r3 is A's final verdict unless B hits the five t14 files** |
| t14 | `990f3cf5` | the A r3 folds (non-vacuous zvbi test + `match=`; F3b fullmatch; `parent_provider` exact; zvbi status; checklist TAGNAME + validator limits; step 10 names the source-commit refusal, census dropped) |
| seat build 1 | `seat\build1\record.md` | `--form onedir --ffmpeg-from <lock> --ffmpeg-sha256 <lock> --notices --smoke --zip` under the UIA watch: exit 0, 194.5 s; origin PASS; notices 241 rows (100 FFmpeg component rows, none zvbi); every smoke row PASS incl. encoders; NO window; zip `52c53256...` = sidecar |
| seat export proof | `seat\export1\record.md` | the bundled binary: capability `hevc_nvenc` 8 / 10 bit, auto -> hevc_nvenc; FROZEN worker export of `Phone\IMG_6702.MOV` ok (CPU backend), encoder `Lavc63.1.102 hevc_nvenc`; V4 MANDATORY + REQUIRED all SAME; no child left |

**Reviewer B r1** (Claude, `codex_cell.py review` via `work/orch-g52/review63c.py`, copy at `80914e17`, base `34c2362a`, prompt `B\r1\review-prompt-B.md`): **NEW_CRITICAL_MAJOR_FOUND** (Claude opus, 36 turns, copy clean; `B\r1\review.txt`). CHECKs: supply chain PASS, `--zip` PASS, r2 patch PASS, scope / regressions PASS (698 / 1 at B's seat); lock / validator PARTIAL; checklist PARTIAL; **notices (N13) FAIL**.
- **F-B1 MAJOR:** code statically linked into `ffmpeg.exe` has no notice row: the Rust std + the Cargo crate sets of rav1e (`31435de9`) and librsvg (`0c074d0a`), and the GCC runtime (libgcc / libstdc++ via `-static-libgcc` / `-static-libstdc++`; libgomp via `--extra-libs=-lgomp`). DR-144's class. The brief's line 37 premise ("already the lock's 102 rows") is contradicted. **ROUTED to CHARC as a QUERY at the roll** (post `work/orch-g53/post-br1.md`): seat recommends fixing now (census subagent for the crate / runtime licences + texts; a fresh Codex turn adding the rows with tests; the minors in the same turn; then A delta + B r2 delta, gate, accept); alternative = `limits` + a register row that closes before the 1.1.0 draft.
- **Minors:** F-B2 five validator guards untested (mutation-proven: `ffmpeg_ref`, `licence`, `build_repository_commit`, `asset_name`, fullmatch vs match) -- in `tests/test_tools_package_ffmpeg.py`, a t14 file, so CHARC's A-delta condition IS met; F-B3 provenance fields not cross-bound (asset_url = provider / release_tag / asset_name; source_record_url names provider + commit; release_tag carries both short shas; zvbi required in `excluded`; version date = `--extra-version`; the INITIAL URL host is unconstrained); F-B4 non-host natives not censused (seat: register row, not this package); F-B5 checklist step-4 STOP misses digest / F3 / F3b / failed run, no patch re-export step, step 12 still says retention.
- **Advisories:** F-B6 `--zip` should require the verified FFmpeg (fold); F-B7 excluded lines should render their status (fold); F-B8 `ffmpeg-BUILD.txt` should carry `parent_provider` / `ffmpeg_ref`, source URL at the tree root (fold); F-B9 scope list (confirm each against dispatches 3-11); F-B10 floating action tags in the fork workflow (out of envelope).

**Codex read of the r2 patch** (CHARC ruling: cross-model by design; read-only; a finding = STOP; `seat\r2-codex-read\`): **VERDICT: CLEAN** (`gpt-6.1-sol` / high; ERROR 0; tokens 1). Checks 1-6 PASS: one commit + base trailer, three files; the checkout line is emitted LITERALLY by the unquoted heredoc, full sha, fail-closed; zvbi only; the workflow's permissions exactly F5's; no `n9.0.2`. It cited web docs (the prompt did not forbid the network): state "no network" in future cross-model reads.

**NEXT, in order:**
1. **Drain CHARC's ruling on F-B1** (and the minors' disposition). If FIX NOW (the seat's recommendation): (a) a seat census subagent (gen 51's form: blob-verified texts) over rav1e `31435de9` and librsvg `0c074d0a` `Cargo.lock` crate sets, Rust std, libgcc / libstdc++ / libgomp (GPL-3.0-or-later WITH GCC-exception-3.1); spot-check 3-4 claims; (b) a FRESH Codex turn 15 (form `work/orch-g53/dispatch-14*.md`) adding the rows / texts + tests, with F-B2, F-B3, F-B5, F-B6, F-B7, F-B8 folded; (c) seat QA (five modules with real git, static) + a seat REBUILD (`build_uia.py`, new out folder) + re-read the notices; the export proof need not repeat unless FFmpeg bytes change (they do not); (d) A delta (Claude, `review63c.py`, base `80914e17`) and B r2 delta (Claude); (e) harness; (f) gate (`gate.sh`: static + darwin mypy, collect, parallel, serial, harness; no fullclip); accept; then the 1.1.0 release per `docs/release-checklist.md`.
2. If LIMITS: fold only the minors CHARC names, A delta on the t14 file, B r2 delta, gate, accept; the register row blocks the 1.1.0 draft.
3. F-B4 -> a register row (CHARC's), not this package.

**Dispatch notes:**
- Every WP6.3c turn is a FRESH session (t13 150K, t14 small).
- Dispatches are assembled as head + `work/orch-g52/rules-block.md` + body, then the prompt = cell definition + the brief at the worktree's HEAD + dispatch, with `tr -d '\r'` (`work/orch-g53/dispatch-14*.md` is the latest form).
- The seat re-runs `( cd .worktrees/wp6.3c && unset PYTEST_ADDOPTS && uv run --no-sync pytest -q -rs --timeout 600 <five modules> --basetemp=work/seat63c-N )`; the real-git cases pass only outside the sandbox.

**Other standing items:**
- WP6.5 (Mac details recorded in the brief `7c99e6b0`); WP7.1 (Insta360 validation) after WP6.3c + 1.1.0.
- Push: CHARC batches the owner's push (Clearwater's own pushes and tags stay the owner's word; the fork exception covers the fork only).
- DR-148 (review-copy Job Object test leaked stub children): before releasing a review copy, check for live processes under it.
- Worktrees: main, `orch-state-g53` (remove it), `wp6.3c` (live), `wp6.3c-rA` (review copy), `wp6.3b`, `wp-dr125`, `wp6.1`, `wp6.3a`, `wp6.4`.
- **Prunes owed (the owner's word only; CHARC batches):** gate basetemps `.worktrees/wp-dr125/work/g43-*`, `.worktrees/wp6.1/work/g43-*`; `work/orch-g51/*` (gate-p63b2, seat63c, bzip2, dr144*), the main-tree clone `work/wp6.3c/FFmpeg-Builds`; `work/orch-g52/seat63c/`, `work/orch-g52/us1/`; `.worktrees/wp6.3b/work/g43-p63b*`; after WP6.3c's accept, `work/wp6.3b-stage1d` and the gen-53 seat outputs above. The 2026-11-05 batch is DONE (`docs/proofs/prune-2026-11-05.md`, 38.3 GB).

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
