# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 52** (session `clearwater-orchestrator-20261105-1241`). LIVE 2026-11-05 22:41Z. ROLLED at the 400K cap at about 00:58Z, clean: nothing it started is running (no cell, no subagent, no review, no gate; `tasklist` shows no pytest / pyinstaller / codex exec of ours -- the two `codex.exe` app-server / exec-server processes started 11-04 20:39 are the OWNER's Codex desktop app, not ours).
- **CHARC is gen 18, `clearwater-charc-20261105-1358`** (gen 17 rolled 11-05 ~23:58Z). Re-verify the name in `comms/.launch-sessions.json` before every cue.
- **Seat folder `work/orch-g52/`:**
  - `gate.sh`, `watch2.sh` (seat path g52), `rules-block.md`;
  - `probe63c.py` (seat notices probe: `uv run --no-sync python -I work/orch-g52/probe63c.py <worktree ABS> <fresh out dir ABS> <relpath to append a byte to>`; positive + negative on fresh stage-1d copies; prints rows / entries / sha256);
  - `review63c.py` (wraps `scripts/codex_cell.py review`, adding `:!tools/package/native-licences` to the diff excludes -- the manifest is ~10K lines; the reviewer reads it in the copy);
  - `textcheck2.py` (new native-licences files vs the seat texts);
  - `prune.py` (the owner-approved prune, READY, refused to the seat by the auto-mode classifier; see NEXT);
  - dispatch-9..12 parts, the drains, the posts; seat pytest logs + probe copies under `work/orch-g52/seat63c/`.
  Copy `gate.sh` / `watch2.sh` with `sed 's#orch-g52#orch-g53#g'`.
- **State worktree:** `.worktrees/orch-state-g52` (remove it; add your own). **Review copy:** `.worktrees/wp6.3c-rA` (detached at `5ecec475`, `.venv` synced, local toml copied).
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

**WP6.3c IN FLIGHT (Codex lane, both nets Claude). Head `5ecec475`, clean, seat-verified (five modules 678 passed / 1 skipped incl. the five real-git cases; ruff / format / mypy win32 + darwin; seat notices probe `a50bc116...a2be`, 140 rows / 1,536 entries / 17 limits).** Brief `docs/briefs/wp6.3c-brief.md` FINAL + tails through "Reviewer A r1 rulings" (`cd4cbef0`). Worktree `.worktrees/wp6.3c`; evidence `C:\Users\rwsmy\clearwater-review-evidence\wp6.3c\` (`cell\` dispatch / prompt / return / turn-N; `seat\`; `A\r1\`, `A\r2\`).

| Turn | Commit | Content | Depth at yield (fresh sessions) |
| --- | --- | --- | --- |
| t1-t8 | `3cc66e24` | see gen 51's state (`c50f20dd`) | |
| t9 | `a268a8e0` | U-S1 originals, AOM + libyuv PATENTS, libaom third_party; DR-144 loading complete | 160,100 |
| t10 | `559621f7` | `limits` manifest list + rendered section "Components with no carried licence text, and limits" (17 entries) | 136,472 |
| seat | `4e154032` | fork patch re-exported: fork commit `92d0b6a6` with a top-level `permissions:` block (contents + packages write), CHARC ruling | |
| t11 | `7fa3d1c9` | A r1 remediation: F1 MAJOR (parent_version on 110 hosts; absent-with-parent and moved refuse), F2, F4, F6, F7, F8, F10-F14; scope STOP on the smoke fixture | 215,739 |
| t12 | `5ecec475` | the STOP granted (smoke fixture uses the synthetic surface, 6 / 8 rows) + CHARC's literal content-hashed `libx265-*.dll` rename test | 104,916 |

**Reviewer A:** r1 (t2-t10, base `70c85062`) `A\r1\review.txt`: NEW_CRITICAL_MAJOR_FOUND (F1 MAJOR + F2-F14), ruled (brief tail). r2 DELTA (t11-t12, base `4e154032`, head `5ecec475`) `A\r2\review.txt`: NO_NEW_CRITICAL_MAJOR (Claude opus, 26 turns, copy clean). **A CONVERGED on t2-t12.** Fold into the re-pin turn: minor 1 -- `notices.py:595` `_check_embedded_parents` trusts the declared parent NAME: a host whose `parent` is not a locked runtime distribution (or `python`) skips the version / absent checks (probe: parent `numpy-typo` absent -> no refusal); refuse "declared parent unknown to this build; re-census required" + one test. Advisories (optional): F4 cleanup runs before the form / flag checks (`build.py:2305`); F7 `write_release_zip` re-reads members without comparing to the snapshot (`build.py:2264`, out of envelope). Posted to CHARC at the roll.

**The fork (Q1 ANSWERED by the owner, CLAUDE.md input `92871252`: `rwsmythe/FFmpeg-Builds`, the seat authorised to fork / push / dispatch).** The seat's `gh repo fork` was REFUSED by the auto-mode classifier ("Create Public Surface"); NOT worked around. The owner types five `!` lines in the orchestrator pane: the FINAL recipe is `wp6.3c\seat\fork-recipe.md` (fork; push `92d0b6a63034510ce553ae88ec13228ee766ddd3` to `refs/heads/wp6.3c-nozvbi`; default branch; enable Actions; `gh workflow run build.yml --ref wp6.3c-nozvbi -f doRelease=true -f buildOnly=false`). As of the roll the fork did NOT exist (`gh api repos/rwsmythe/FFmpeg-Builds` -> 404). The pushed commit lives in the clone `.worktrees/wp6.3c/work/wp6.3c/FFmpeg-Builds` (HEAD `92d0b6a6`, parent `5031c6f1`); `tools/package/ffmpeg-fork.patch` at `4e154032` is its format-patch (sha256 `583199a3...17f7`). F3 ruling (BINDING at the re-pin): the release tag MUST peel to the run's `head_sha`, else STOP; F5 (top-level, not per-job permissions): a limits sentence in the report + AD-38.

**NEXT, in order:**
1. **A r2's verdict** (above). If NEW_CRITICAL_MAJOR: adjudicate, post to CHARC, a fresh remediation turn (dispatch form: `work/orch-g52/dispatch-11-*.md`), seat QA, A r3 delta. If NO_NEW_CRITICAL_MAJOR: A has converged on t2-t12; fold any minors into the re-pin turn.
2. **When the fork exists** (the owner's `!` lines; watch with `gh run list -R rwsmythe/FFmpeg-Builds`): cue CHARC at once ("the moment the fork exists"); watch the run (hours) with a background until-loop on `gh run view <id> --json status,conclusion`; record in `wp6.3c\seat\`: run URL, job log, asset name / size, GitHub per-asset digest, computed sha256, `checksums.sha256` line (three-way), the release tag peeling to `head_sha` (F3), `ffmpeg -version` / `-encoders` (hevc_nvenc, libx265) / archive listing (LICENSE.txt GPL-3.0), the `n9.0.2` commit. Then the re-pin turn (design items 3, 4, 6; strict lock schema, no legacy bypass; the F5 limits sentence), A delta, the seat build proofs (`--form onedir --ffmpeg-from <lock url> --ffmpeg-sha256 <hex> --notices --smoke --zip`, 25 GB free, full Git Bash PATH as 6.3b; V4 on a bundled-binary export; the notices read in full; the smoke under `work/orch-g49/smoke_uia.py`), Reviewer B, the harness on the head BEFORE B, the gate (`gate.sh`: static + darwin mypy, collect, parallel, serial, harness; no fullclip), accept.
3. **The prune (owner-approved, CHARC batch):** READY at `work/orch-g52/prune.py` (guards keep `work/wp6.3b-stage1d(.log)`, `work/wp6.3b-seat`, `work/wp6.3c`, `.worktrees/wp6.3c*`; releases `.worktrees/wp6.2` and `.worktrees/wp6.3b-rA` with `git worktree remove`, branches kept; logs `work/orch-g52/prune-log.jsonl`). The seat's run was REFUSED by the classifier ("Irreversible Local Destruction"); the owner was asked to type `! uv run --no-sync python -I work/orch-g52/prune.py`. When `prune-log.jsonl` exists, write `docs/proofs/prune-2026-11-05.md` (each item, bytes, files, C: free before / after; mapping: wp-dr125 builds = `.worktrees/wp-dr125/work/wp6.1` + `work/wp-dr125/frozen-runs`; wp6.1 builds / pack = `.worktrees/wp6.1/work/wp6.1`; the wp6.4-rA leftovers already gone; gate basetemps in those worktrees NOT in the batch) and register it in `tests/harness/genericity_lists.py` if `docs/proofs/` needs it (check how prune-2026-11-04 is registered).

**Dispatch notes:**
- Every WP6.3c turn is a FRESH session (each adds 85-200K).
- Dispatches are assembled as head + `work/orch-g52/rules-block.md` (the two verbatim CLAUDE.md rules + the QUIT_SCRIPT exception) + body, then the prompt = cell definition + the brief at the worktree's HEAD + dispatch, with `tr -d '\r'`.
- The cell's pytest runner removes `PYTHONPATH` before `pytest.main` (the plain `PYTHONPATH=scripts` form trips WP6.3b's `PYTHON*` refusal).
- **The per-row STOP rule** (from t7): one missing input leaves that row out under STOPPED ROWS; it is not a turn STOP.
- The seat re-runs `( cd .worktrees/wp6.3c && uv run --no-sync pytest -q -n 4 ... five modules ... )`; the real-git cases pass only outside the sandbox.

**Other standing items:**
- WP6.5 brief DRAFT `fea43245` (the owner's Mac details "later tonight", 11-05).
- WP7.1 (Insta360 validation) after WP6.3c + 1.1.0.
- Push: CHARC batches the owner's push (Clearwater's own pushes and tags stay the owner's word; the fork exception covers the fork only).
- Worktrees: main, `orch-state-g52` (remove it), `wp6.3c` (live), `wp6.3c-rA` (review copy), `wp6.3b`, `wp-dr125`, `wp6.1`, `wp6.3a`, `wp6.4`; `wp6.2`, `wp6.3b-rA` and `.worktrees/wp6.3a-rA` go with the prune.
- **Prunes owed after this batch (the owner's word only; CHARC batches):** gate basetemps in `.worktrees/wp-dr125/work/g43-*` and `.worktrees/wp6.1/work/g43-*` (~3.7 GB); `work/orch-g51/gate-p63b2`, `work/orch-g51/seat63c/`, `work/orch-g51/bzip2`, `work/orch-g51/dr144*`, the main-tree clone `work/wp6.3c/FFmpeg-Builds`; `work/orch-g52/seat63c/` (probe copies, ~2 GB), `work/orch-g52/us1/`; `.worktrees/wp6.3b/work/g43-p63b*`; after WP6.3c's accept, `work/wp6.3b-stage1d`.

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
