# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 50** (session `clearwater-orchestrator-20261105-0611`). LIVE 2026-11-05 16:11Z. Gen 49 (`clearwater-orchestrator-20261105-0315`) rolled clean at the 400K cap.
- **CHARC is gen 17, `clearwater-charc-20261105-0602`** (it went online 16:03Z after gen 16 `clearwater-charc-20261104-0738` rolled). Re-verify the name in `comms/.launch-sessions.json` before every cue.
- **Seat folder `work/orch-g50/`:** `gate.sh`, `watch2.sh` (re-pointed from g49), `crcheck.py`, `assemble.py`, the drains, posts and `dispatch-19-body.md`. The g49 tools (`smoke_uia.py`, `dll_origin.py`, `census_measure.py`) stay in `work/orch-g49/` and are used from there (copies for any run).
- **Gen 49's seat folder `work/orch-g49/`:**
  - `gate.sh`, `watch2.sh`, `crcheck.py`;
  - `assemble.py`, the dispatch assembler: `uv run --no-sync python work/orch-g49/assemble.py <body.md> <cell>\dispatch-N.md`. It joins the two CLAUDE.md rule lines from HEAD at `@@RULES@@` and asserts no CR / VT;
  - `smoke_uia.py`, the stage-1 smoke-under-UIA driver, written and NOT yet run. Run it from an md5-checked COPY; it has already been grepped clean for synthetic input;
  - `dll_origin.py` and `census_measure.py`, read-only native tools;
  - the drains, the posts, and `dispatch-N-body.md` for N = 12-18.

  Copy `gate.sh` / `watch2.sh` with `sed 's#orch-g49#orch-g50#g'`.
- **FRESH prompt** = `.claude/agents/implementer-codex-sol-high.md` + `docs/briefs/wp6.3b-brief.md` at HEAD + `dispatch-N.md`, joined, with `tr -d '\r'`. A **RESUMED prompt** is `dispatch-N.md` alone.
- **State worktree:** `.worktrees/orch-state-g50`. The successor removes it and adds its own.
- **Bash gauge at bring-up:** 25 ms (gen 50). C: 2.8 T free (the 4 TB NVMe migration is done; repo root unchanged).
- **Paces at 13:15Z:** Codex 7 % / 0.433, Claude 61 % / 1.362, so the lane is Codex. Re-read both at the next commission.

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

**GEN 50, 18:15Z: WP6.3b TURN 22 RUNNING** = the Reviewer B r1 REMEDIATION (FRESH Codex session; prompt `cell\prompt-22.md` = agent md + brief at main `569b2e6d` + `cell\dispatch-22.md`; brief tail "Reviewer B r1 rulings": MINORs 2-9 + advisories 10-12 in one turn, 13 / 14 report lines; **MAJOR 1 (embedded components in carried natives) CARVED to WP6.3c**: a register row at 6.3b's accept, owned by 6.3c, closed before the 1.1.0 draft; the accept record + AD-38 say the limit in words). If gen 50 dies with it running, re-run the same FRESH prompt (read `git -C .worktrees/wp6.3b status` first).
- **Gen-50 ledger since 17:05Z:** t20 `8938edd3` (the A r3 remediation; FRESH `01a1aca5`, 174K); rebuild `work\wp6.3b-stage1c` GREEN (origin PASS with A1's magic bytes; notices `3afe913e...`, coverage exact; `seat\dll-origin-stage1c.txt` clean); a pre-existing 1 s test-bound flake under host load (the owner gaming) -> t21 `91f90c8f` (FRESH `01a1acc4`, 92K; `job_case` bound 10 s; seat 686 + 1 skipped); **Reviewer B r1 FULL** over `50a25b3b..91f90c8f`: NEW_CRITICAL_MAJOR_FOUND, 1 MAJOR / 8 MINOR / 5 adv (`B\r1\review.txt`); CHARC ruled (A) + (B) + (C). Item 12's input: `seat\uv-0.10.9-checksum.md`.
- **NEXT after t22:** seat QA -> commit -> REBUILD (`work/wp6.3b-stage1d`) + `dll_origin` + `notices_cover` -> **Reviewer B r2 DELTA** over `91f90c8f..<t22 head>` (Claude, from `.worktrees/wp6.3b-rA`; form = `B\r1\review-prompt-B.md` trimmed to a delta) -> the gate (static, collect, parallel, serial, harness + darwin mypy + module-alone installer) -> the accept.

(Gen 50's 17:05Z line, done:) **WP6.3b TURN 20 RUNNING** (the Reviewer A r3 REMEDIATION, FRESH Codex session, prompt `cell\prompt-20.md` = agent md + brief at main `db675e17` + `cell\dispatch-20.md`; items k1, k2, F1-F4, A1, A3, A4, A2, the F5 report line: brief tail "Reviewer A r3 ruling"). If gen 50 dies with it running, re-run the same FRESH prompt (check `git -C .worktrees/wp6.3b status` first; discard nothing without reading it).
- **Done in gen 50:** t19 committed `65784337` (the data turn; the three kinds; seat QA 652+1 / 113, provenance and bound files equal the seat record). Order steps 2-4 GREEN at `65784337`: the rebuild from the FULL Git Bash PATH (`work\wp6.3b-stage1b`, origin check PASS, `dll_origin` clean), the smoke under UIA (`seat\smoke-uia\run1`, `windows_seen` []), the notices read in full (`seat\stage1b-notices-read.md`; coverage exact both ways, 1,536 entries; `work/orch-g50/notices_cover.py`). **Reviewer A r3 CONVERGED** (`A\r3\review.txt`, NO_NEW_CRITICAL_MAJOR); CHARC ruled the remediation (`db675e17`), no A r4.
- **NEXT after t20:** seat QA (the seven modules + the module-alone installer + ruff / format / both mypy, 0 CR) -> `codex_cell.py commit` -> REBUILD + notices (`work/wp6.3b-stage1c`, from the FULL PATH; then `dll_origin.py` + `notices_cover.py`; smoke again only if the diff touches `build.py`'s smoke path; A1's magic-byte check runs inside the build) -> **Reviewer B FULL** over `50a25b3b..<head>` (form `wp6.3a\B\r1\review-prompt-B.md`; ban `run_in_background`) -> the gate -> the accept (CHARC's items, plus the F5 register NOTE and the WP6.3c carve-out row naming 6.3c as owner).
- **WP6.3c:** owner ruled zvbi = self-build; brief DRAFT `a86e3c24`; dispatch AFTER 6.3b's accept; I fill Q1-Q4 (Q3 = any pending `--zip` / origin-source branch in 6.3b's accepted code, by file:line).

(Gen 50's t19 line, done:) RESUMED session `01a1ac75` (99K at its t18 yield) with `cell\dispatch-19.md` = dispatch 18's body unchanged + CHARC's **Turn-18 ruling** (main `5dd307d5`, option (b): THREE STRICT provenance kinds `release-archive` / `git-tree` / `proprietary-redistributable`) verbatim + item 0 (the schema, RED first). The seat VERIFIED every commit, tag object and in-tree path BEFORE the turn (read-only `gh api` / GitLab API) and wrote `seat\native-licences-provenance.md`, the cell's provenance input. Seat application, posted to CHARC (`f7aabe25`): tag + tag object are a PAIR, given only for ANNOTATED tags; array-api-extra `v0.10.1` is lightweight, so no tag fields. If gen 50 dies with the turn running, the turn dies too: re-run dispatch 19 resumed on `01a1ac75` (check `git -C .worktrees/wp6.3b status` first). The history below is gen 49's board, still the plan.

(Gen 49's line: turn 18's STOP was routed to CHARC; now RULED.) WP6.3b branch `wp6.3b` is at **`b6b1a286`** (turn 18, the data turn). The review copy `.worktrees/wp6.3b-rA` is at `fa0fded4`, has its own `.venv`, and its native-licences text is LF.

1. **WP6.3b: the Windows release path, minus the FFmpeg bundle.**
   - Brief `docs/briefs/wp6.3b-brief.md`, with EVERY rulings tail (CHARC):
     - Round-0, Turn-3, Turn-6, Turn-9;
     - Turn-11 (`1a8beb0d`, the Job Object);
     - Seat-proof split (`3d24e38d`): **6.3b accepts WHOLE; the FFmpeg bundle, `--zip`, the FFmpeg smoke / V4 / `hevc_nvenc` rows, the FFmpeg notices rows, the root FFmpeg row and the 1.1.0 draft release are CARVED OUT into WP6.3c**, which CHARC briefs after the owner's zvbi ruling;
     - Reviewer A r1 (`370ea0f9`);
     - Stage-1 (`df44eadb`);
     - Turn-17 (`cab1f2c1`, SciPy vendored code).
   - Evidence: `C:\Users\rwsmy\clearwater-review-evidence\wp6.3b\` (`cell\` turns 1-18; `A\r1`, `A\r2`; `seat\`).

   **Gen-49 turns.** The branch was REBASED onto main `50a25b3b` after t14 (head then `00b221cb`).

   | Turn | Commit | Content | Session |
   | --- | --- | --- | --- |
   | t12 | `52754527` | smoke rows under a Windows Job Object | `01a1abc1`, retired at 222,977 |
   | t13 | `b9a991e0` | `release.yml` (SHAs in `seat\action-shas.md`; FFmpeg params from the lock; `--zip` the pending flag; draft-only), checklist v2, guide, limited root notices | FRESH `01a1abf5` |
   | t14 | `1734a657` | uv pinned to 0.10.9; ADV-2 README | `01a1abf5`, 175,535 |
   | t15 | `b103acbc` | notices M2 + m1: PSF narrowing, a fail-closed native list, the basename + RECORD hash rule, `bundled_files` | FRESH `01a1ac23` |
   | t16 | `fa0fded4` | C1 helper, M1 fixture, m2 https + redirect allowlist, m3 pinned allowlist, m4 byte guard, m5 `UV_*` env, m6 published-release refusal, a7 120 min | `01a1ac23`, 213,705 |
   | t17 | `c3cf6f82` | sanitized PATH + post-build ORIGIN check; PyInstaller rth modules mapped; the schema (`version_evidence`, `co_licensed_with`, `text_source`); N1-N3, A1-A3 | FRESH `01a1ac5b`, 179,040 |
   | t18 | `b6b1a286` | REPORT-ONLY STOP: the manifest's per-row schema requires `source_tag_object`, `source_archive_url`, `source_archive_sha256` and `source_archive_size_bytes`, and the seat record lacks them (MSVC can never have them). The nine texts verified byte-equal; no rows committed. The data turn proper is NOT done. | FRESH `01a1ac75-de0a-7041-8df0-e31d0878fd82`, 99,129, RESUMABLE |

   **Reviewer A has CONVERGED on `fa0fded4`:** r2 returned NO_NEW_CRITICAL_MAJOR. t17 and t18 came after it, so **A r3 is a DELTA over `fa0fded4..<head>`**, as CHARC confirmed.
   - Use `codex_cell.py review` from `.worktrees/wp6.3b-rA`; re-point it with `git -C .worktrees/wp6.3b-rA checkout -q --detach <head>`, then check its native-licences text has 0 CR.
   - The forms are `A\r1\review-prompt-r1.md` (full) and `A\r2\review-prompt-r2.md` (delta). Ban `run_in_background`.

   **Stage-1 seat findings** (records in `seat\`; tools in `work/orch-g49/`):
   - The first build, from Git Bash's PATH (`work\wp6.3b-stage1\`), carried MSYS2 OpenSSL from `/mingw64/bin` and `ucrtbase` plus 40 `api-ms` forwarders from JDK 17's `bin`. The clean-PATH build (`work\wp6.3b-stage1-cleanpath\`) is clean. t17's sanitized PATH and origin check fix this inside `build.py`.
   - The census and every row input: `seat\native-licences-census.md`, `census-measure.json`, `native-licences-libffi.md`. Texts are in `work\wp6.3b-seat\native-licences\` (`fetched\`, `fetched\scipy-1.18.1\`).
   - **libffi is 3.4.7, NOT 3.4.6.** PBS's Windows build clones the `libffi` branch of `cpython-source-deps` at build time; CHARC accepted this correction.
   - **packaging.version's text is BSD-2**, although SciPy's `LICENSES_bundled.txt` labels it BSD-3.

   **REMAINING, in order** (CHARC-confirmed):
   0. **Turn 18's STOP:** on CHARC's ruling, either (a) the seat fetches each open-source component's release archive (libffi 3.4.7, Mesa 11.2.2, LLVM 3.6.2, the 4 vendored repos at their commits plus SciPy 1.18.1) and records URL, sha256, size and tag object; or (b) a ruled alternative provenance schema (a git commit as the source identity; MSVC as a proprietary row with no source). Then RESUME `01a1ac75` (99K) with the data; the dispatch-18 body applies unchanged.
   1. (Done in gen 49: t18 report-only commit `b6b1a286`.) For the REAL data turn: inspect `cell\turn-18.driver.stdout` / `return-18.md`, re-run at the seat (the 7-module set + the module-alone `tests/test_gpu_pack_install.py` + ruff / format / both mypy), check 0 CR, then `codex_cell.py commit`.
   2. **The CLEAN REBUILD** from the worktree: `( cd .worktrees/wp6.3b && uv run --no-sync python tools/package/build.py --form onedir --notices --out /c/Users/rwsmy/clearwater/work/wp6.3b-stage1b > ... 2>&1 )` in the background, with a stall Monitor. It must pass t17's origin check from Git Bash's FULL PATH, which is the point: the sanitizing must work without the seat clearing PATH.
      - Expect notices GREEN. Then run `dll_origin.py` on the result; no `git-mingw64-bin` / JDK origin may remain.
   3. **The smoke under UIA:** md5-copy `work/orch-g49/smoke_uia.py` and `C:\Users\rwsmy\clearwater-review-evidence\wp-dr125\frozen2\uia_watch.ps1` to `seat\smoke-uia\`, then run the copies:
      - `.worktrees/wp6.3b/.venv/Scripts/python.exe <copy>/smoke_uia.py <worktree> <release folder> <out> <copy>/uia_watch.ps1 <evidence>`;
      - expect `smoke_exit` 0, a positive control above 0 and `windows_seen` empty.
   4. **The notices read IN FULL** against the folder listing (every row has an entry, every entry a row); write the record in `seat\`.
   5. Reviewer A r3 (the delta), then **Reviewer B**: a FULL Claude pass at the seat over `50a25b3b..<head>`, form `wp6.3a\B\r1\review-prompt-B.md`, banning `run_in_background`.
   6. **The gate:** `bash work/<seat>/gate.sh .worktrees/wp6.3b <run-id> <legs...>` (two legs + harness) + `uv run --no-sync mypy --platform darwin` + the module-alone `tests/test_gpu_pack_install.py`. Then the accept record `docs/proofs/wp6.3b-accept.md`, then the rebase / ff to main.
   7. **CHARC's accept items:**
      - AD-38 (the flag, hook, workflow, bundle rule, native-licences surface, the lazy-import limit, the a5 `os._exit` line);
      - register rows: FFmpeg re-pin about 2028-10, the MinGW-runtime limitation, the WP6.3c carve-out, the WP6.1 spike PATH contamination (record), the 1.0.0 audit's SciPy vendored-code gap (record);
      - N13 for 1.1.0 waits for 6.3c.
2. **WP6.3c** (CHARC briefs it after the owner's zvbi ruling).
3. **WP6.5** (Mac validation): brief DRAFT `fea43245`. WP6.5's brief must carry the native darwin smoke containment (process group + `killpg`); the darwin branch refuses until then.
4. **Push:** main is ahead of `origin/main`. CHARC batches the owner's push.
5. **Worktrees:**
   - main, `orch-state-g49` (remove it), `wp6.3b` (live), `wp6.3b-rA` (detached review copy);
   - `wp-dr125`, `wp6.1`, `wp6.2`, `wp6.3a`, `wp6.4` (kept for the prunes).
6. **Prunes owed (the owner's word only; CHARC batches):**
   - gen 47's and gen 48's lists (in `git show e453d30b:docs/orchestrator-state.md`);
   - gen 49's own: `work/seat63b-t12..t17*`, `work/seat63b-m1`, `work/wp6.3b-stage1`, `work/wp6.3b-stage1-cleanpath` (keep until the accept), `work/c63b-*` in the worktree.

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
