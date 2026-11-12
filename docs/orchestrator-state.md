# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 72** (session `clearwater-orchestrator-20261111-1026`). LIVE 2026-11-11 20:27Z from gen 71's rollover `43a255e9`. **ROLLED ~01:25Z 2026-11-12 at the ~400K cap, with NOTHING it started still running.** Checked at roll: 0 guard / loop / gate processes, 0 clearwater pytest, 0 `codex exec`.
  - **Seat folder `work/orch-g72/`:**
    - drains 1-3; posts (`online.md`, `post-*.md`, `q-*.md`, `status-*.md`); `pending.md` (the running notes);
    - `read_run10.py` + `run10-reading.txt` (the run-10 reading);
    - `fill_sheet.py`, `append_ledger.py`, `ledger_dr165_seat.py` (seat ledger / sheet edits, LF bytes);
    - **`quiet-serial.sh <run-id> [N]`** (the guarded quiet serial leg) and **`retry-serial.sh`** (attempts g72q5..g72q12; edit the `for i` list to fresh ids before re-arming); `watch-retry.sh` (the Monitor form);
    - `qa-rA.sh` / `qa-gate-rA.sh <sha>` (seat QA + static / collect / harness / parallel from `wp6.5-rA`);
    - `wp6.5-mac-in/` (the staged Drive folder); `dr165/` (seat inputs: fork series, the asset's `versions.txt` and patch).
  - **Bash gauge:** 85 ms (PowerShell-measured).
- **NOTHING IS RUNNING.** No cell, Codex turn, review, gate, leg or loop.
  - Retired cell: `wp65-dr165` (353,277 at its final yield). Do not message it.
- **CHARC is gen 23, `clearwater-charc-20261111-0900`.** Re-verify the name in `comms/.launch-sessions.json` before every cue.

### PICKUP, in order

1. **Drain the inbox first.** CHARC may have answered `f8d4bacc` (the DR-165 gate), relayed the owner's sibling-pause word, or relayed the Drive word.
2. **THE QUIET SERIAL LEG ON `d4a1b507` IS STILL OWED** (CHARC `f67fa7f1` + `6899b0eb`; a precondition of the stage-1 close; option 3 refused).
   - The gate copy `wp6.5-rB` is detached at `d4a1b507`; do not move it.
   - **Re-arm at pickup** (CHARC: "re-arm the retry loop ... let it run overnight"):
     - set fresh ids in `work/orch-g72/retry-serial.sh`'s `for i` list (g72q1-g72q5 are used; use e.g. `g73q1`... by editing the `RUN` prefix, or `13 14 ...`);
     - then `bash work/orch-g72/retry-serial.sh > work/orch-g72/retry-serial.out 2>&1` in the background, plus a Monitor on `watch-retry.sh` (its glob is `gate-g72q*-d4a1b507`: widen it if you change the prefix).
   - **The guard (`quiet-serial.sh`):**
     - it starts a leg only after N=10 quiet 60 s samples: CPU < 35 %, no non-clearwater pytest, no seat work (a `codex exec ... read-only` review or a clearwater pytest), and no `work/orch-g72/HOLD` file;
     - it STOPS the leg (`taskkill /T`) when a sibling pytest shows on 2 consecutive samples;
     - logs: `work/orch-g72/guard-<run>.log`, summaries `work/orch-g64/gate-<run>/summary.txt`.
   - **Never edit `quiet-serial.sh` while an instance runs:** stop the loop with TaskStop, then `taskkill /T` the leftovers (TaskStop leaves the bash children), then edit and restart.
   - **On the owner's pause word** (CHARC relays): if a cell is mid-check, let it reach its yield first. Then make sure the loop is armed. It starts within ~10 min of quiet; for a faster start, run `quiet-serial.sh <id> 3` directly.
   - **When a leg completes green:** post the figures + the slowest ten to CHARC (`grep -A12 slowest serial.log`). That is the stage-1 close precondition.
   - A V7 failure on a QUIET leg is a finding to CHARC with the junit.
3. **The stage-1 close after the quiet leg** (CHARC orders it): the sheet is filled (`c6a1b9bb`), and the run-10 reading is posted (`ac92b486`) and in the ledger.
   - Hand-over of the Drive folder `work/orch-g72/wp6.5-mac-in/`: copy to `G:\My Drive\wp6.5-mac-in` ONLY on CHARC's relay of the owner's word.
   - The bundle artifact expired 2026-11-12 23:07Z, but the local copy is in `clearwater-review-evidence\wp6.5\runner\run-43115320682\macos-validation-bundle\` and in the staged folder.
4. **DR-165 (`wp6.5-dr165`, head `40de4915`):** both nets clean, QA green. The parallel leg had 3 load timeouts (`test_app_export_worker`), 3/3 alone. AWAIT CHARC's ruling on `f8d4bacc` (my recommendation: legs of record on a quiet machine with the WP6.5 accept gate, or back to back with the quiet `d4a1b507` leg). Its serial leg has not been run. It merges into `wp6.5` at the WP6.5 accept (the orchestrator merges); its proof on the real archive is the next runner run with the switch on.
5. **Accept items held** (for the WP6.5 accept):
   - a watched DR row for the load-sensitive V7 100 ms bounds (`test_app_v7::test_v7_a_b_analysis_and_scrubbing`, `test_gui_timeline::test_v7_interface_never_waits_more_than_100_ms_during_analysis_and_a_drag`) and the three export-worker 10 s child-start bounds;
   - DR-159 additions: the `docs/release-checklist.md:102` `-1` (the fork record is now a two-commit series), and CHARC's residual sentence for the lock-turn checklist item.
6. **"DR-164 verify" package** (defect ii): AFTER the WP6.5 accept (`cf8f3060` / `7da78562`).
7. **Paces at 23:20Z 2026-11-11:** Codex 8 %, pace 1.017 (resets 2026-11-18 10:08Z); Claude 3 %, pace 0.082 (resets 2026-11-16 10:00Z). The Claude figure dropped from gen 71's 77 % / 2.632, so treat it as possibly a probe anomaly and re-read before every dispatch.

### Standing facts for WP6.5 (each re-verifiable)

- **`wp6.5` head `c6a1b9bb`** (`git -C .worktrees/wp6.5 log --oneline -4`):
  - `c6a1b9bb`: the run-10 reading in the ledger, plus the run-sheet fills (version 1.1.1, commit `d4a1b507...`, 10a sha256 `903cf474...4fc0`, L1 run `43115320682`, step-30 wall 233.49 s with the DR-164 xfails, expected `D` 10808, DR-163 "closed by run 10", 10-bit "proven in run 10");
  - `d4a1b507`: the seat ledger append M1 / A2 / A3 (`b08a354a`);
  - `53095351` and below: as gen 71 recorded.
- **Runner branch of record:** `origin/macos-validation/wp6.5` = `d4a1b507` (CHARC pushed run 10). NEVER push any other ref for WP6.5.
- **Run 10 `43115320682` GREEN on `d4a1b507`** (22:52-23:07Z). Every reading line held (post `ac92b486`):
  - macOS leg 234 passed / 2 xfailed (exactly the DR-164 libx265 regular-final pair, with values 1.1 vs 1.0 s);
  - VT = x265 at 8 AND 10 bit;
  - smoke `n9.0.2-47-gb204e94e90-20261111`;
  - identities = run 7 + ffmpeg / ffprobe;
  - bundle zip sha256 `903cf47410e2e38fad1d7f5a61558594f0e3d3631668900d7bdf2b140f3a4fc0`, `# source-commit: d4a1b507...`.

  Evidence: `clearwater-review-evidence\wp6.5\runner\run-43115320682\`.
- **The gate on `53095351` / `d4a1b507`:** QA, static, collect (11,029), harness 423 and parallel 9,456 / 223 / 0 are of record from gen 71. Serial: only a LOADED run exists (1,322 / 2 V7 failures, 3,516 s; not of record); the V7 nodes pass 3/3 alone. The quiet leg is owed (PICKUP 2).
- **DR-165 commits** (`wp6.5-dr165`, from `c6a1b9bb`):
  - `e2e06854` build;
  - `f961b918` ledger;
  - `2595ab05` + `0579d7bd` (A r1 fold);
  - `4a40cb26` + `9b0f2b8b` (A r2);
  - `8ff54a0f` + `67d2c290` (A r3);
  - `40de4915` seat ledger (depths, stop rule `7283c16a`, residual sentence).

  Dispatch and returns: `clearwater-review-evidence\wp6.5\dr165\`. Worktree `.worktrees/wp6.5-dr165` (LF working copy: made by removing the tracked files and re-checking them out with `-c core.autocrlf=false -c core.eol=lf`).
- **Worktrees:** `wp6.5-rA` detached at `40de4915` (DR-165 review + QA copy); `wp6.5-rB` detached at `d4a1b507` (the serial-leg copy); `wp6.5-dr165`; plus gen 71's list. Any prune needs the owner's word.

### GEN-72 RECORD

- Online `bcf9e78f`.
- **Serial re-run on `53095351`:** under load, 2 V7 wall-clock failures. READY `04c290e9` (recommend push), and CHARC pushed run 10 (`f67fa7f1`: a quiet serial leg owed before the stage-1 close).
- **Ledger append** `d4a1b507` (M1 / A2 / A3, plus the `# source-commit:` line rule; line 5 concurred).
- **Run 10 GREEN;** reading `ac92b486`; ledger + sheet fills `c6a1b9bb`.
- **Quiet-leg attempts:** g72q stopped at 23:07Z and g72q2 at 23:41Z by `swing-trading` pytest. Query `46f9cdfb`; CHARC `6899b0eb`: option 3 refused, the owner is asked to pause the sibling, the loop runs overnight, the Drive folder is staged only.
- **DR-165:**
  - lane Claude by pace; cell `wp65-dr165` (sonnet-high) dispatched under an exclusive-window hold (no tests until released);
  - A r1-r3 each found a MAJOR in the `versions.txt` classifier and was folded (an allowlist, then exact full-line forms); stop-rule query, CHARC `7283c16a`;
  - A r4 clean; B clean; QA green; parallel had 3 load timeouts. Post `f8d4bacc`.

### Gen-72 lessons

- **A sibling harness can make a quiet leg impossible for hours** (`swing-trading` started a `pytest -n 8` every 5-15 min). A guard that STARTS only after N quiet samples and STOPS the leg on a sibling's return keeps an unrecorded figure out of the record. A 3-sample pre-check was too short; 10 was still not enough while the sibling was active. Ask the owner for a pause early.
- **A guard must also gate on the SEAT's own work:** a review's probes or a cell's pytest would contaminate the leg as surely as a sibling's. A HOLD file covers a live cell between its edits and its tests.
- **Never edit a running bash script** (bash reads it by offset): stop the loop, `taskkill /T` the leftovers, edit, restart.
- **A Windows worktree checkout is CRLF under the system `autocrlf=true`, and `checkout-index -f` does NOT rewrite files the index thinks are up to date.** Remove the tracked files, then `git -c core.autocrlf=false -c core.eol=lf checkout -- .`.
- **A classifier reviewed adversarially converges asymptotically** (three MAJORs, one per round, each a new record shape). Go to conservative refusal by round 2, to exact full-line forms by round 3, and ask the director for a stop rule as soon as the second round repeats the class.
- **An idle notification can truncate a cell's return:** read its last assistant text from the subagent transcript (`agent-a<name>-*.jsonl`) instead of messaging it, because a message re-wakes it.
- **`glob` skips dot-directories** (`.worktrees`): junit-history scans need the explicit `.worktrees/*/work/` pattern.

### GEN-71 RECORD

- Online `a33617b1`; CHARC acks `b06e7f6a`.
- **DR-164 census** (`cf8f3060`): 58 sources, 0 long terminal frames; ruled Phase 7 (`7da78562`).
- **Half B Claude A r1** NO_NEW_CRITICAL_MAJOR (2 MINOR + 4 ADV, carried into the lock turn, `e2b7e458`).
- **The sheet:** `wp65-sheet3` folded Codex r2 (`5940a484`); Codex r3 1 MAJOR (step 57 perl `-0777`, seat-applied `4830ec82`); r4 CLEAN; cherry-picked onto `wp6.5`.
- **Gate green on `bfff36cc`:** parallel 9,414 / 223 / 0 (673 s); serial 1,324 / 19 / 0 (2,261 s); identity 10,987; harness 423.
- **Q1-tool** (`6df71d1d`): one Codex turn, Claude A r1 clean; landed `e4fb0d4d`; sheet 34 / 37 filled (`4ff3ad5b`).
- **L2 + L4** at the seat (`4ff3ad5b`).
- **Fork dispatch** on the owner's word (`81814c85`): attempts 1-2 not acquired, attempt 3 (owner's early word) SUCCESS.
- **Lock turn:** B3 STOPPED on build-log noise; the seat classified every difference (`dr163\lock-stop\classify.txt`); CHARC `efa2de83` ruled five classes; B4 resumed and landed.
- **CHARC rolled gen 22 -> gen 23 at 19:00Z.**
- **Lock turn Claude A r1** NO_NEW_CRITICAL_MAJOR (1 MINOR + 3 ADV; `wp6.5\dr163\A-claude-lock\r1\review.txt`); CHARC `b08a354a`: M1 / A2 / A3 = the seat ledger append before READY; A1 = DR-165 (a 1.2.0 blocker, its own package after run 10).
- **Gate on `53095351`:** QA green; static / collect / harness / parallel green; serial STOPPED under external load (see PICKUP 1).

### Gen-71 lessons

- **A re-pin is a re-census when the validator ties census fields to identity fields** (`census_build_commit == build_repository_commit`): read the validator before briefing a "re-pin", and stage both builds' `build/` metadata and job logs for the cell.
- **A strict "anything else differs = STOP" rule fires on build-log noise** (curl meters, parallel-make order). Classify the differences at the seat (a multiset of lines with digits / hex masked) before asking for a ruling; it turned a vague STOP into a five-class ruling in one round.
- **Check the target ref before every push:** the runner branch is `macos-validation/<branch>`; a plain `git push origin <branch>` made a new public ref.
- **Read a sheet step's other options against the tool when filling a marker** (`--out` must exist; the default suffix): the fill is a claim.
- **The heredoc backslash collapse struck once** (a dispatch builder with a Windows path; nothing written); redone with the Write tool and `chr(92)`.
- **Another harness on this laptop can contaminate a gate leg** (gen 71: `swing-trading` ran three `pytest -n 8` suites during the serial leg; CPU at 100 %, a 300 s timeout, the parallel leg 57 % slower). Before every serial leg, check `Win32_Processor` LoadPercentage and look for sibling pytest processes; a leg run under that load is not of record.
- **Windows Python cannot open `/c/...` paths** from Git Bash variables: pass `C:/...` forms.

### GEN-70 RECORD

- Online `f6fd3f34`; CHARC ack `3f09fd9e`.
- **Rulings drained (all in `comms/orchestrator/read/`):**
  - `d94f38dd`: DR-163 = fork VT patch (b), two halves, Codex lane.
  - `c1b49908`: no version marker.
  - `792af2fd`: A r4 carried into half B.
  - `6688c6fd`: no run 10a; run 9 is the RED of record.
  - `fac58dc7`: sheet rulings.
  - `b80a8d7a`: DR-164 opened, strict xfails.
  - `cf8f3060`: DR-164 = movenc; census; verify package.
- **Post-run fold:** Codex turn 6 (fresh) -> `aca1ba7d` + `6879e2a2`. Claude A r4 FINDINGS: F1 MAJOR (run-10 reading) + ADV 2 / 3, carried into half B (CHARC). Seat QA on `6879e2a2` fully green.
- **DR-163 half A:**
  - Codex turn 1 STOPPED correctly: the fork's `build-macos.yml:236` version regex and Clearwater's macOS lock validator both pin an 8-digit suffix. The marker was withdrawn.
  - Turn 2: the patch (+10/-3, wrapper-wide).
  - The seat: FFmpeg commit `1f1fedd`; format-patch sha256 `b598505e...93c4f`, byte-equal applied to pristine; fork commit `5314a43`.
  - Claude A r1 NO_NEW_CRITICAL_MAJOR (3 ADV accepted). Pushed.
- **DR-163 half B:** turn 1 STOPPED on a NEW product defect.
  - The defect: libx265 output of a long-final-frame source, `mdhd` 1.0 s vs edit 1.1 s; V4 MANDATORY refuses, the sink accepts.
  - The seat reproduced it.
  - The NVENC probe keeps the duration on that fixture.
  - The read-only diagnosis attributes it to movenc's terminal decode delta (`movenc.c:7323`). Its `-debug_ts` prediction was CONFIRMED at the seat: the encoder emits 2048 on PTS 14848, sum 16896.
  - DR-164 was opened. Turn 2 resumed on the ruling.
- **The sheet:** `wp65-sheet1` S1 (`2dbd7453`; delivery gap, Q1-A gap, Gatekeeper all verified), then S2 fold (`275d1c61`). Codex r1: 1 CRITICAL + 6 MAJOR; `wp65-sheet2` fold (`1dea2984`). Codex r2: 3 MAJOR.

### Gen-70 lessons

- **A dispatch can carry a SUPERSEDED brief line** (the Gatekeeper "right-click-Open" came from a corrected note). Quote a brief by its CURRENT text, and grep for "CORRECTED" / "Superseded" around any line you lift.
- **"A marker in the version string" ran into two version validators, one per repository** (the fork's workflow regex and Clearwater's macOS lock validator). Before ruling or briefing an identity change, grep BOTH sides for the field's validators.
- **A probe that passes on one encoder can be a fixture coincidence:** NVENC kept the duration only because its long frame was also last in decode order. Ask the diagnostician "is the passing case structurally immune, or did the fixture miss the trigger?" before reporting reach.
- **A posted lead can be wrong in its attribution** (my "libx265-specific" was movenc). Report a probe's FACT ("NVENC keeps it on this fixture") apart from its INFERENCE.
- **Every run-sheet `rm` / redirect needs a variable guard,** and appends after a guarded command escape the guard (r1 CRITICAL, r2 MAJOR). Brief run-sheet authors with "every write sits INSIDE the guard's `&& { }`".
- **The bare-`cd` slip struck once** (`cd .worktrees/wp6.5 && ...` moved the session; restored in the next call; nothing written while moved; no cell live).

### GEN-69 RECORD

- Online `7aa0502e`; CHARC ack `83b4fa81`.
- **F0-2b A r1 fold:**
  - Query on the synthetic-Pillow premise -> `c1339c28` (the planner enforces `TCL_TK`).
  - Codex turn 3 -> `6a02f358` + `9a086f49`. A r2 and B both NO_NEW_CRITICAL_MAJOR.
  - Gate green (serial 2,125 s; slowest ten named). Ready post. Run 8 pushed (`d0d9b6dd`).
- **Run 8 FAILED, no STOP.** The table led to `ef405237`:
  - F8-1: the sysconfig `pyz:` module;
  - F8-2: the APFS link fixture;
  - F8-3: VT + VFR, DR-163;
  - F8-4: the P17 tag layer.
- **F8-3 lane:** `5f15d162` (read-only Codex, two halves). Half 1 predicted run 9 exactly.
- **Codex turns:** turn 4 (fold) -> `eb095682` + `04dfd101`; turn 5 (hook widened) -> `8417c0b8` + `6bf69487`.
- **Owner pause / resume.** A r3 and short B both NO_NEW_CRITICAL_MAJOR. Gate green (parallel 9,361; serial 1,963 s). Ready post `a2ddbbc7`.
- **Run 9 GREEN** (`cffbd052`). Half 2 confirmed the cause and recommended (b). Query `0429716d`.

### Gen-69 lessons

- **A fixture that stubs the very bytes a ruling's condition is about makes a test-only assertion circular.** Read the fixture's stubs before relaying a "the test also asserts X" condition; the check may belong in the planner, where the real run reads real bytes (`c1339c28`).
- **A real-bytes run reaches only as far as the first refusal.** Run 8 proved admission and nothing after `notices.py:2627`. Name the stages a failed run did NOT reach, so the next run reads them as first proofs.
- **A fix in ONE checker (`build.py`'s content check, run 5) did not reach its sibling (`notices.py`)** over the same PYZ. When a fix admits a name in one checker, grep every checker that classifies the same entries.
- **Test helpers can tag at the wrong layer:** `-color_trc` as an output option is not written into the stream by libx265 (`-x265-params` is). A seat repro with the laptop FFmpeg settled it in two runs.
- **A preregistered, falsifiable prediction from a read-only diagnosis, plus a test-only evidence hook, turned an unreproducible runner failure into a confirmed cause in ONE run.** Write the prediction BEFORE the evidence exists, and ask the diagnostician what else the hook should capture: half 1's additions were essential (raw tables, source evidence, capture before the cleanup).
- **An `ffprobe` packet table without `stream_index` interleaves audio:** the "last packet" can be audio. Read the last video sample from the raw `stts`.
- **A reviewer's `-k` can match a `gpu` test.** Every review prompt carries `-m "not gpu"`.
- **A dispatch can cross an owner's pause word in flight** (dispatch-5 launched a minute before the word). Report it at once with the stop option; CHARC ruled it work in flight.
- **`codex exec resume` takes no `-p` / `-s`;** use `-m` and `-c`. The first attempt failed on its arguments with nothing run.
- **The bare-`cd` slip struck once** (restored the next call; nothing written while moved; no cell live).

### GEN-68 RECORD

- Online `34378524`; CHARC ack `8593ed36`.
- **Claude A r2:** FINDINGS (1 MAJOR universal2 + 1 MINOR census shape + 3 ADV). Query `b2a91c5d`; CHARC ruled `7a363f94`.
- **Codex turn 4** (FRESH, dispatch-4, 13 min, depth 140,914) folded F1 / F2 / A1 / A2. The seat committed `ff2ed010` + `8955f790` (fyi `ab54935d`).
- **A r3:** NO_NEW_CRITICAL_MAJOR. **B:** NO_NEW_CRITICAL_MAJOR. Seat QA green on `5729dd63` and `8955f790`.
- **Gate** green on `8955f790`. Ready post `c154c0f4`.
- **Run 7:** CHARC pushed it (`baeaaf2e`). GREEN at 20:47Z; table `6d8db27f`.
- **Census:** `darwin-census` dispatched (query `9a7466f4`); CHARC ruled `da5a86b7`. Census returned; findings query `3b3c9211`; CHARC ruled `3fdf1fd3`.
- **F0-2b Codex turn 1** dispatched (status `f7546404`). It STOPPED on my text-reuse premise; I answered (11 new + 2 reused + 4 evidence-only, fyi `42efe4a6`). Turn 2 resumed and built everything (depth 292,827). The seat committed `3783b93a` + `aef6bb61` (status `2cf82275`).
- **Seat QA** green on `aef6bb61`. **Claude A r1:** 2 MAJOR + 3 ADV; query `2273c4d3`.

### Gen-68 lessons

- **A census's `reused_from` can point at seat EVIDENCE, not committed files** (4 of 6). The Codex cell's premise check caught it. Verify every "byte-identical to existing" against the committed tree before writing it into a dispatch.
- **"Verbatim" carried across platforms can make a statement false:** the U-T1 limit names the row that carries Tcl/Tk, and that row differs on macOS. When a ruling says "verbatim", check each statement's factual claims against the new platform.

- **The heredoc backslash collapse struck again** (`f02\\A-claude\\r3` became `\r3` -> CR, which the state script stripped). Repaired with a Write-tool script (`fix_state.py`). The bare-`cd` slip struck once (`cd <evidence> && ls`); the shell reset it, and nothing was written while moved.
- **Read the matcher before the census:** darwin hosts match by whole-file sha256 (`_embedded_claims`), but PyInstaller rewrites and re-signs every Mach-O. CHARC ruled that the rows bind the `macho:` identity. Read how a declaration is MATCHED before briefing the evidence that fills it.

- **`codex_cell.py review` marks a Claude review as failed (exit 1, `verdict_lines: []`) when the verdict line is numbered** (`` 1. `VERDICT: ...` ``). Read `review.txt` before treating it as failed. B's prompt now says "on its own line, unnumbered".
- **The gate's parallel half can run beside a read-only review process.** Hold the serial leg until the review has returned.

- **A normaliser's input class must match the real inputs.** The fold's identity test used a THIN origin; the real PySide6 / shiboken6 wheels are universal2. Ask "what does the real wheel look like" for every synthetic origin in a test.

### GEN-67 RECORD

- Online `419b5f88`; CHARC ack `7ec41241`.
- **Run-4 fix, closed over four review rounds:**

  | Round | Range | Result | Ruling / commits |
  | --- | --- | --- | --- |
  | A r3 | `eee896b6..6dc8c000` | F1-c MAJOR: a nested folder link was not re-rooted | `7a246dfd`; turn 6 resumed -> `a0d62fec` + `29f9305f` |
  | A r4 | | F1-d MAJOR: an aliased release root refused 20 legitimate links; plus a fan-out advisory | `37ba6ba9`; turn 7 FRESH -> `74d416d6` + `80d57f15` |
  | A r5 | | NO_NEW_CRITICAL_MAJOR | Ready; pushed; run 5 |

- **Run 5 (`42853872024`) FAILED outside the `.app`:**
  - 42 links in the COLLECT sibling `Clearwater/_internal/`;
  - `pyz:_sysconfigdata__darwin_darwin`.
  - Ruled `c6f26292`. Turn 8 FRESH -> `eb7b8949` + `200dffd8`.
  - A r6 NO_NEW_CRITICAL_MAJOR; pushed; **run 6 (`42865170579`) GREEN**, the first green macOS run (post `060c9bf0`).
- **F0-2:**
  - **Brief and round 0:** CHARC's brief `4d69b21b`. The seat's facts corrected its otool premise (the output is IN `app-listing.txt`; 493 entries, 155 Mach-O; census complete), and CHARC fixed the brief (`d72909a1`).
  - **Round-0 STOP:** `wp65-cell19`'s round 0 stopped on D1 (110 Windows-only embedded hosts; a Mac census needed). CHARC split it (`eb1fc893`, brief `299a37d9`).
  - **F0-2a:** cell19 built F0-2a to `701475de` (385K, retired). Codex A r1 found 4 MAJOR + 2 MINOR, incl. a Windows-behaviour leak via `home.suffix == ".app"`. CHARC ruled `698a6460` (census declaration as an object with evidence; one layout context; Codex lane by pace).
  - **The fold:** a fresh Codex session -> `db059efd` + `5729dd63`.
- CHARC rolled gen 21 -> gen 22 at ~18:00Z.

### Gen-67 lessons

- **A reviewer's rebuild covers only what the evidence captured.** Four review rounds rebuilt the `.app` from `app-listing.txt` (`find <root>/Clearwater.app -ls`) and never saw PyInstaller's COLLECT sibling beside it. Run 4's 50-line print cap hid the sibling's lines and the `pyz:` line. Before a "content check passes" claim, ask what the check walks against what the evidence lists, and read capped output to its end.
- **Judge what ships:** `release_zip_folder(root)` is the shipped folder. A check over the whole distpath judges build by-products.
- **A test-wide patch of the shared `subprocess` catches the stdlib's own cold `platform` query** (`win32_ver` -> `ver` when WMI is unavailable, as in the Codex sandbox). Two fixtures had it. A sandbox-only failure in that family is not a product defect; confirm it at the seat.
- **Check a director's premise at the seat before it reaches a cell.** The F0-2 brief said the `otool -L` output was missing; it was redirected into the listing file. Reading the step's redirect took one grep and saved a cell's round 0.
- **A key on a name suffix leaks across platforms** (`home.suffix == ".app"` reached a Windows folder named `X.app`). Platform-specific behaviour keys on one context computed once from the real layout AND the host platform.
- **The bare-`cd` slip struck once** (`cd .worktrees/wp6.5-rB && ...` to read a skip reason). It was restored in the next call; nothing was written while moved.

### GEN-66 RECORD

- Online `d2113e99`; ack `2d986fcf`.
- **WP6.5 A r14 fold:** `wp65-cell18` (dispatch-19, 19b, 19c; returns 24-26): M1 + its own residual (any link on a PATH candidate skips it), M2 recorder, A r15's three recorder gaps. A r15 query `e7a234d7` -> CHARC stop rule `d13c6ce4`; A r16 `NO_NEW_CRITICAL_MAJOR`; seat ledger `ae128116`. Ready `dc6fea0d`; CHARC pushed; **run 4** `42814037850` failed at the new content check (post `970b2a76`).
- **Run-4 fix:** ruling `200f9645`; Codex turn 1 STOPped on my dispatch's discovery wording, answered lexically (`forbidden_paths(root, *, app=None)`, `_macos_content_app`; fyi `44087186`); turns 2-3 -> `82b9ae3e` + `2f69ad1d`; A r1 FINDINGS (2 MAJOR + 1 MINOR) -> `0317f4cb`; turn 4 -> `1b6ec28d` + `eee896b6`; A r2 FINDINGS (F1-b MAJOR) -> `e162ad24`; turn 5 (FRESH session, `prompt-5.md`) -> `83df5ffe` + `6dc8c000`. Next: A r3 (not started).
- **WP7.1:** turn 16 section 9 (`ae62caef`), Claude A `NO_NEW_CRITICAL_MAJOR` (1 MINOR + 3 NIT), turn 17 fold (`0d459d9a`), rebase (range-diff all "="), two-leg gate green on `5f684e58` (parallel 8,442 / 207 / 0; serial 1,318 / 19 / 0; harness 423), ff main, post `4a03c3fb`; CHARC accepted `1b14aa9f`.

### Gen-66 lessons

- **Fold a cell's own declared residual before the next review round** (dispatch-19b): it closed in the same cell and saved a round.
- **A test instrument converges asymptotically:** ask the director for a stop rule (instrument-only findings become ledger advisories) as soon as the trend shows.
- **A dispatch's own wording can over-constrain a ruling:** "decide the form from the release folder's contents" forced a discovery call the onedir census forbade; the caller already held the answer lexically. Read the call sites before writing a "how" into a dispatch.
- **A per-name gate in a ruling is wrong in both directions** (`isidentifier()` let `foo-bar` through and the dotted skip let `foo.bar` through): ask for "judge it as its physical equivalent" first.
- **A cell's return can arrive in chat while its transcript's last text is mid-turn:** save the chat return.
- **The heredoc backslash collapse struck again** (a runner path became CR, a turn path became TAB in a state edit); repaired with a Write-tool script. Any Python holding a Windows path goes through the Write tool.

### GEN-65 RECORD

- **Online:** post `27ee1878`; CHARC ack `d9f82775`.
- **WP7.1 instrument:** A r4 (Claude) clean with zero findings; `wp7.1` ff to `65c28219`; post `19308fc6`. Look exhibits kept (`a4cd23fe`).
- **WP6.5 run 3** (`42781244075`): parallel clean; serial 15 failures (FFmpeg 5, GPU-pack 8, cache 2); the `.app` link rule; T14. Runner table built.
- **Run-3 group:** `wp65-cell16` (dispatch-17) returned `0a40c058`. Its S2 dispute was RIGHT; my run-3 premise was false (a grep for `sys.platform` missed the `pack_root()` gate). The DR row and the XS package were DROPPED.
- **Codex A r11:** FINDINGS, 1 MAJOR + 3 MINOR, all upheld; fold cell17 dispatched.
- **Window 3:**
  - the first launch refused `--timeout-s 3600` against the 7,408 s V4 bound (a staging defect; relaunched as `export-hevc62r2`);
  - the hold message to cell16 never reached it (QUEUED mid-turn), so the cell's pytest overlapped the export leg.

### Gen-65 lessons

- **An exclusive window is gated on the cell having YIELDED, never on a hold message or on "no pytest at launch".** A message to a mid-turn Agent-tool cell is queued and NOT delivered until its turn ends; it then re-wakes the cell after its return. This is the second occurrence after gen 61. Dispatch an exclusive window only with no cell live, or launch the cell after the window.
- **Read the product's gate before asserting a product defect:** "nothing checks the platform" came from a `sys.platform` grep. The real gate was `pack_root()`. Read the call path from the entry (menu action -> handler -> dialog -> plan) before posting a premise CHARC will rule on.
- **A staged seat script must be dry-checked against the driver's own argument checks** (`run_export.py:51` `v4_bound`) before a window. Gen 64 staged `--timeout-s 3600` for a leg whose inline V4 needs more than 7,408 s.
- **The heredoc backslash collapse struck again** (`\r` in a state-top path became CR); repaired with a Write-tool script. **The bare-`cd` slip struck twice** (into the look folder; into the wp7.1 worktree while cell16 was live); each was restored in the next call, and nothing was written while moved.

### GEN-64 RECORD

- **WP6.5:**
  - CHARC ruled the `69538abe` gate STANDS with DR-96. The owner said "push"; CHARC pushed and **run 2** (`42764505729`) ran: parallel 4 failed / 7762 passed / 1227 skipped (run 1: 63). The four: C2 (HEIC max 2-3 / p99 1), C16 (FFT max 1.79e-7, inside 1e-5), the NEW beat-file test, the NEW darwin containment EPERM. Serial and bundle steps were skipped.
  - CHARC ruled each item. `wp65-cell15` (dispatch-16) fixed all six (`2e98ca1c`).
  - **A r8 MAJOR:** CHARC's switch-keyed continuation skipped the bundle tests in RELEASE mode (`macos.log` missing). Re-ruled MODE-keyed (`success() || (!cancelled() && !inputs.release-version)`) with a four-case EVALUATED guard. Fold `eeefd4cf`.
  - **A r9 MINOR:** evaluator precedence; fold `a93a0ab7`. **A r10: zero findings.**
  - **Gate on `2e98ca1c`** from the detached `wp6.5-rB`: identity 10,574; parallel 9,020 / 210 / 0; serial 1,318 / 19 / 0. On `a93a0ab7`: release_workflow 122, harness 423 OK, actionlint clean, statics clean.
- **WP7.1:**
  - Plan R (V4-only on the retained outputs) was REFUSED: `frame_end` is called by `encode.py:1312`, so WP7.2 changed the EXPORT path.
  - The owner's "reading" became the instrument sub-package above.
- **Slips:**
  - one bare `cd` into `wp7.1-instrument` (restored the next call; nothing written; no live cell affected);
  - a seat QA basetemp without its parent (45 errors, re-run green);
  - my restated probe swapped the media and movie timescales (the Codex cell STOPPED correctly at I2).

### Gen-64 lessons

- **Read a diff by CALLER, not by file:** `verify.py` hosts both instrument helpers and the encoder's end-of-stream arithmetic (`frame_end`). "Only verify.py changed" did not mean "only the instrument changed". Grep the callers of every changed function before claiming a change's reach.
- **A ruling's WORDING can name the wrong axis** (the bundling switch instead of the run MODE); the reviewer caught it as a release-mode regression. When a ruling conditions on a flag, ask which axis the distinction really is, and check both modes of a workflow before relaying.
- **A gate leg must not run from a worktree a cell is editing:** run it from a detached copy at the gate sha (`wp6.5-rB`, with toml + `uv sync --frozen`). Then the cell folds in parallel, and the fold head re-runs only the touched ids (CHARC plan 2).
- **Do not run a Qt / GUI test module under xdist `-n`** at the seat: a 5-min timeout left a hung worker tree (`taskkill /T` on the pytest root).
- **The `codex_cell.py commit` parser refuses returns** whose block sits after prose in the same line run; commit by pathspec in the worktree, and count CRs per blob. The CRLF-checkout trap struck once more (I1: 1,600 CRs; amended before use).
- **When restating a reviewer's probe, copy its facts exactly** or point at the file: "timescale 30000" lost its "media" and cost a Codex turn.
- **A Claude review's `review.json` keeps only the final message:** its probe code is gone. Ask reviewers to inline the probe's inputs in the finding.

### Gen-63 lessons

- **An autouse fixture that requests `monkeypatch` reorders every test's teardown,** even when its body is a no-op on that platform: the requested fixture is set up earlier, so finalizers registered later run BEFORE the monkeypatch undo. An order-dependent defect like this hides from module runs and shows in the xdist leg. `-p <module>` preloads a module as a plugin, making such a failure deterministic.
- **Read the follow-up drivers' input gates before a FAIL verdict reaches them:** both `load_export` and `project_long` refused a V4-FAIL record. The pickup rule ("STOP if they refuse") caught it before any blind run.
- **A review transcript can contain OTHER sessions' transcripts** (B printed A's review files with `cat`): count `^session id:` headers before reading the "tokens used" count.
- **A cell's round 0 can show that a fix clears fewer rows than the brief's Done line assumed** (the source file's own movie-level roundings): the brief's STOP clause did its job. Amend the Done line by ruling, never silently.

### BINDING RULES CARRIED (each verbatim in `comms/orchestrator/read/` or CLAUDE.md)

- **DESKTOP INPUT RULE and ENTRY-POINT ISOLATION RULE (CLAUDE.md hardware section).** Paste BOTH VERBATIM into EVERY dispatch (current text: `clearwater-review-evidence\wp6.5\cell\dispatch-3.md`, with the QUIT_SCRIPT exception and the Mac HOME reading).
  - A cell-written GUI or proof script is reviewed at the seat: grep for SendKeys / AppActivate / SendInput / keybd_event / mouse_event / pyautogui / SetForegroundWindow.
  - Such a script is RUN AT THE SEAT FROM md5-CHECKED COPIES (WP7.1: `clearwater-review-evidence\wp7.1\seat\frozen-t6\MD5SUMS`; `md5sum -c` from the driver folder before each run).
- **No seat or review run executes the DR-125 "before" shape.**
- **EVERY CLAUDE REVIEW PROMPT BANS `run_in_background`** (and every Codex review prompt now says "no background execution; whole report in the FINAL message"). Check that `review.txt` is a full report before acting. Four "ERROR: Reconnecting... n/5" lines in `review.out` with one `tokens used` and a full report are a network blip, not a failed review.
- **Launch a Codex turn or review ONLY with the Bash tool's `run_in_background`, never a shell `&`.**
- **ROLLOVER TIMING (OWNER-RULED).** Below 400K a seat starts the next unit WHATEVER ITS SIZE; it rolls at the first clean boundary after 400K with nothing it started still running (a live Agent-tool cell dies with the pane: wait for its return). At or past the cap, dispatch nothing new.
- **NO PYTEST DURING A SERIAL OR FULLCLIP LEG** or a window; one heavy job at a time. **Never edit a worktree a gate is running from.** WP7.1's EXCLUSIVE legs (C/D/E) run only when no WP6.5 cell is running tests (CHARC).
- **TWO CODEX SESSIONS ARE ALLOWED** (CHARC `a6934b58`), on disjoint files.
- **Codex turns:** `uv run python scripts/codex_cell.py turn --worktree <ABS> --prompt <p> --evidence <dir> --turn N [--session=<id>] > <dir>\turn-N.driver.stdout 2>&1` with run_in_background; commit with `codex_cell.py commit --worktree <ABS> --return-file <return-N.md>` (it refuses a return without a parseable block: then `git -C <wt> add <file>` + commit by pathspec in the worktree). Depth = the footer's `depth_input_tokens`; evaluate ~200K, STOP ~250K; a resumed turn adds 30-40K: resume only below ~160K. FRESH prompt = `.claude/agents/implementer-codex-sol-high.md` + the brief at HEAD + every prior return and dispatch (2..N) + `dispatch-N.md`, joined, `tr -d '\r'`; RESUMED = `dispatch-N.md` alone. Never Write a dispatch and launch the turn that reads it in ONE batch. The first (non-resumed) turn needs an ABSOLUTE `--worktree`.
- **Claude cells (Agent tool):** depth with `uv run --no-sync python scripts/cell_depth.py --live 3 <name>` at dispatch, every yield, before any ruling; ~250K evaluate, ~400K STOP; build dispatches name a mid-turn yield at ~300K. A SendMessage to a cell that has already yielded RE-WAKES it (it re-sends its return): read depth first; if it has returned, do not message it. Their reviewer is CODEX: `cat review-prompt.md review-diff.txt | tr -d '\r' | codex exec -p strong -s read-only --skip-git-repo-check -o review.txt - > review.out 2>&1` from the DETACHED copy (`( cd <copy> && ... )`); assert banner `gpt-6.1-sol` / `high`, `grep -ac '^tokens used'` = 1, the verdict.
- **Claude review of a Codex cell:** `codex_cell.py review --worktree <DETACHED copy> --base <sha> --prompt <p> --out <dir>`, background, at the seat (forms `wp6.3a\B\r1\review-prompt-B.md`, `wp6.3a\B\delta2\review-prompt-delta2.md`).
- **A gate runs from a DETACHED copy at the gate sha when a cell may edit the package worktree** (gen 64; `wp6.5-rB`). Never run a Qt / GUI module under `-n` at the seat.
- **Gates:** `bash work/<seat>/gate.sh <worktree> <run-id> <legs...>` (background) + a Monitor on `watch2.sh <run-id> <summary line count>`, re-armed at 30 min; run `uv run mypy --platform darwin` beside the static leg. Copy the toml and `uv sync --frozen` in a new worktree first.
- **Backslash-bearing Python goes through the Write tool**, never a heredoc (it struck AGAIN in gen 60: `wp6.5\\A\\r1` in a heredoc became `\A` + CR; fixed forward `41ef6dd5`).
- **A bare `cd` moves the session's cwd.** ONLY `( cd X && ... )`, `git -C`, absolute paths. (Gen 60 slipped three times; each restored next call.)
- **role_mail subjects are capped at 120 chars** and a refused post writes nothing: read the `posted ->` line before cueing.
- **QUIT_SCRIPT exception:** `tests/test_app_startup.py::test_python_m_clearwater_starts_the_shell_and_exits_0` runs at the SEAT in gate legs only; every cell run (and the macOS job, F0-11) keeps `-k 'not test_python_m_clearwater_starts_the_shell_and_exits_0'`.
- **Running downloaded build scripts / binaries is refused** at this seat; read them as text (the seat's pinned actionlint 1.7.12 is the one standing tool).
- **CI-SHAPED REHEARSAL BEFORE EVERY TAG** (`work/orch-g58/rehearsal.py --runner-path`); **THE RELEASE SWEEP** before any Codex read of a bump; **RELEASE NOTES STATE BEHAVIOUR BY SHAPE** (DR-159 carries them into checklist v3).
- **A NEW WORKTREE'S `.venv` IS AN EMPTY SHELL** (`uv sync --frozen` first).
- **CLAUDE.md is CHARC's**; the orchestrator never appends to it.
- **Claude lane:** the ~95 % hold ended at the 2026-11-09 10:00Z weekly reset; read `scripts/usage_claude.py` before each Claude dispatch and report the share.

### Gen-61 lessons

- **A cell's return can arrive HOURS late, or never, as a chat message**: cell7 returned at 12:10Z and the seat sat idle until ~16:53Z; cell5's and cell8's chat returns were truncated. When a cell's depth is static and its commits have landed, read its LAST assistant text from `~/.claude/projects/C--Users-rwsmy-clearwater/<session>/subagents/agent-a<name>-*.jsonl` (python, last `assistant` text) and save it to the evidence folder.
- **A queued SendMessage re-wakes a cell after its return**: the CHARC addendum relayed to cell6 made it fold a SECOND time after its return (a new commit, a new helper sha) while the seat was preparing the delta read on the first. Before using a return's shas, re-read `git log` and the helper clone's reflog.
- **A cell asked to "hold tests" may not honour it within the leg**: cell8 kept working and ran its suites after leg 1 ended; nothing overlapped by luck. For an exclusive leg, gate on the cell having YIELDED (depth static across a turn boundary), not on a message.
- **GitHub can refuse a dispatch on a fork with "Actions has been disabled" (422) while `actions/permissions` says enabled**: the fork's web-only "enable workflows" state; and a macOS arm64 job can sit unacquired and be cancelled ("not acquired by Runner of type hosted") under capacity constraints. Neither spends the owner's dispatch; record both, ask CHARC before a re-run.
- **Conservative refusal beats emulation in a validator** (two Codex rounds on shell-pattern and byte-scan emulation; the third fold refused the hard classes outright and converged in one pass).
- **The heredoc backslash collapse struck twice more** (a `sed` replacement in a review prompt and a Python heredoc building this state block: `\r` -> CR, `\f` -> FF); repaired with Write-tool scripts. **The bare-`cd` slip struck twice** (into the transcripts folder; into a cell's scratch folder while the cell was live); each restored in the next call, nothing written while moved.

### Gen-60 lessons

- **A cell-written driver's acceptance check can be wrong about a product field's vocabulary:** run A's export succeeded and its driver failed on `device.startswith("cuda:")` (the product's field is the backend REASON, `"GPU"`). Before a long seat run, grep the product for every value a driver asserts on.
- **A driver's hard-coded sub-timeout is a second bound:** V4's `timeout=900` inside an 1,800 s outer bound killed A2. Read every `timeout=` in a seat driver, not only the CLI bound, and size each from the measured rate.
- **A round-0 premise of the brief can be false** (ProRes "admitted on paper"): the Codex cell's round 0 caught it with file:line; verify at the seat and route to CHARC before any build turn.
- **A SendMessage to a cell after it yielded re-wakes it** (wp65-cell2 re-sent its return twice). Read depth twice; if the return has landed, do not message.
- **Fold Reviewer A's findings into the NEXT group's fresh cell** (A r1's three findings rode into G2b's turn): one cell, one review round.
- **The bare-`cd` slip recurred three times in gen 60; the heredoc backslash collapse once; one refused over-length subject.**

### Gen-59 lessons

- **A ruling's wording can itself be false:** CHARC's A1 phrase went into a fix commit and the next read found it false. Verify supplied wording against the code BEFORE committing it.
- **A clause list in release notes is a magnet for findings:** three successive reads each found one false clause in one sentence. Propose the shape-only form as soon as a second round finds a clause.
- **Main moves under a release branch** (CHARC's state commits): rebase onto main, record `git range-diff` (all "=") and the tree diff, then ff.
- **Read the workflow's gate before planning a run on it:** WP6.5's stage-1 plan assumed a branch dispatch of `release.yml`; its version gate refuses any non-tag ref. Caught at the fill, ruled as Q5.
- **The runner's skip set can differ from the CI-shaped rehearsal's** by host facts the rehearsal cannot mimic (8.3 short names, the `C$` admin share): diff SKIPPED reasons, never assume (7515 / 1062 vs 7517 / 1060).
- **A harness run's tail can print "acked 1 message(s); moved inbox -> read."** It is fixture output; check the real inbox listing.
- **The heredoc backslash collapse struck again** (prune2's KEEP block). The Write tool is the only safe route for any Python with a Windows path.
- **The bare-`cd` slip recurred twice in gen 59** (`cd .worktrees/... &&` at the start of a command). Each was restored in the next call.

### Gen-58 lessons

- **A seat instrument goes INTO the environment under test, never around it.** The spy plugin, copied into the clone venv's site-packages and removed after (no PYTHONPATH), gave a leg identical in shape to the plain one: `7519 / 1058`, then `7517 / 1060`. Check that equality before reading the spy's list.
- **"Passes for the wrong reason" has one shape here:** a REAL tool call runs BEFORE the injected fault, fails when the tool is absent, and lands on the status the test expects. A guard is needed exactly when the asserts accept that status. Read the call order (file:line) for every spawning parameter, and guard per parameter.
- **A cell's collection run can fail on its OWN tooling.** The Codex turn-5 GUI-import block gave 27 collection errors and footer ERROR lines; its corrected runner collected 8,577. Read the transcript before treating footer ERROR lines as package failures.
- **`codex_cell.py commit` can refuse a well-formed return block** (`files_changed: []`). Commit by pathspec inside the worktree, with your own message.
- **Placeholders multiply:** the report had FOUR "(the seat fills)" lines, not the two the ruling named. `grep -n "seat fills"` before a seat fact commit.
- **A laptop floor and a CI-shaped floor differ by the toml-absent skips.** Here `8370 / 207` vs `8367 / 210`. Diff the `SKIPPED` reason lines to prove it; never assume.
- **A serial-leg flake gets: re-run alone 3x, the junit history (`g43-*-serial.xml` across worktrees), the package's footprint, then a CHARC ruling** (here DR-158 WATCH).
- **The heredoc collapse struck again:** a `\\n` inside a quoted heredoc Python literal became `\n`, so the assert missed. Any Python with a backslash goes through the Write tool.
- **The bare-`cd` slip recurred FOUR times in gen 58** (`cd <dir> && ...`; once a `cd <worktree> 2>/dev/null;` meant only to grep). Each was restored in the next call; nothing was written while the session was moved. Use `( cd X && ... )`, `git -C`, absolute paths, or the Grep / Read tools. Never type `cd` at the start of a Bash command other than the repo root.
- **A Codex read flags KEPT history strings as CRITICAL** when the prompt says "a wrong version string shipped is CRITICAL": `notices.py:2191` was ruled KEEP an hour earlier, and the read still made it F1. Sweep for version-bearing prose that RENDERS INTO THE ARTIFACT, not only for version pins, and settle it before the read.

### Gen-57 lessons

- **A release workflow that has never run on a runner fails on the runner's facts, not the laptop's.** v1.1.0's run died 3 s into the tests on `--basetemp=work/ci-parallel` (`work/` is gitignored; pytest does not create the parent). Then the seat's CI-shaped rehearsal found the toml class (12), and Reviewer A found the bigger one: the runner image has NO FFmpeg, and the rehearsal had inherited the laptop's PATH (152 more tests in 15 modules). A rehearsal is only CI-shaped when its PATH and GPU are too: drop every PATH entry holding ffmpeg / ffprobe and set `CUDA_VISIBLE_DEVICES=-1` (`work/orch-g57/rehearsal.py --runner-path`). Check the runner image's software list (`actions/runner-images` `images/windows/<image>-Readme.md`; the image name is in the run log's "Runner Image" group).
- **A causal split settles "what caused these N failures" in one minute:** re-run ONLY the failed node ids under each candidate cause alone (`work/orch-g57/cause_split.py`). Here: FFmpeg dropped -> the same 152; GPU hidden -> 152 pass.
- **A step timeout in a seat driver kills only the wrapper:** the 30-min sync limit killed PowerShell and left `uv sync` running as an orphan that finished the install. Size step limits for this laptop's link (the CUDA wheels took ~17 min), and look for orphans (`Get-CimInstance Win32_Process`) before re-running.
- **A no-log-growth stall alarm is wrong for `uv sync`** (it prints nothing while downloading). Read the process's write-transfer counter instead.
- **Builds are not byte-reproducible across trees** (zip `d233d8c0...` vs `2529b42f...` for the same commit; notices byte-identical). Compare member sets.
- **The bare-`cd` slip recurred twice in gen 57** (once `cd <state worktree> 2>/dev/null;` moved the session cwd into the worktree; once inside a background command, which did not move it). Only `( cd X && ... )`, `git -C` and absolute paths.

- **A seat instrument must not change the environment the tests check.** The spy run set `PYTHONPATH` to load its plugin, and `build.py` refuses a set PYTHONPATH: 253 failures that were the instrument's, not the package's. Install a seat plugin into the clone's venv instead, and compare the instrumented leg's summary with the plain leg's before reading anything from it.

### Gen-56 lessons

- **A harness gate run before `git add` cannot see a new file**: CHARC's notes file `docs/release-notes-1.1.0.md` reached main unregistered and failed the harness's tracked-files test on main for hours; seat QA on a package head found it. Register a new root/docs file in the same commit, and run the harness AFTER staging.
- **Release-notes claims need a reviewer claim table every round**: r4 found a sixth false claim ("licence and source" for every component, while the MSVC runtime carries terms only) after three rounds; the linked user guide also carried prerelease text ("not released yet") and a stale size. Ask the reviewer to grep the linked docs too.
- **Fold advisories from two nets in ONE turn** (CHARC ruled): running B on the same head as A's converged delta, then folding A r2 + B r1 together, saved a full turn + review round.
- **A seat-verifiable census can be staged into the Codex worktree's gitignored `work/`** (byte-compared file by file) when the sandbox cannot read the evidence folder; the cell then copies by a script verified against the census index, and the seat re-checks from the COMMITTED BLOBS (`qa_texts.py`).
- **The heredoc backslash collapse struck again** (`work\release-proof-gpu\roots` in a heredoc Python literal became CR bytes in the build record); caught by the edit notice and repaired with a Write-tool script. Any Windows path in Python goes through the Write tool or `chr(92)`.
- **The bare-`cd` slip recurred three times in gen 56** (`cd <worktree> && ...`, each restored in the next call; nothing written while moved).

### Gen-55 lessons

- **A version bump's own checks must include EVERY test that pins the app version**, not only the version test and the package modules: `tests/test_gpu_pack_install.py:340` pinned the User-Agent `Clearwater/1.0.0` and would have failed the tag build's parallel leg. Codex's read caught it. For any bump: `git grep -nE '"1\.0\.0"|/1\.0\.0'` over `tests src tools` (minus `native-licences`), and run `test_gpu_pack_install.py` alone.
- **Release notes need a claim-by-claim read against the code.** Three Codex rounds found five false or overstated claims in the notes (auto-restart, a menu ellipsis, start-up hashing, "every tool pinned", "with the licence texts"). The last one exposed a real N13 gap (FFmpeg's ~100 build-stage components carried no texts) and became WP6.3d. Ask the reviewer for a per-claim file:line table.
- **A licence census's real yield can be the record SET, not the texts**: pass 1 found shaderc's `git-sync-deps` sub-dependencies (glslang, SPIRV-Tools, SPIRV-Headers) statically linked with no lock rows at all. Brief every census to follow each stage's own fetch steps (DEPS, submodules, cargo, sync scripts).
- **A gate of record must not overlap a build**: an 11 s pytest ran while the release build was finishing (harmless, but against "one heavy job at a time"). Wait for the build's exit line.
- **The bare-`cd` slip recurred twice in gen 55** (each restored in the next call; nothing written while the session was moved).
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
