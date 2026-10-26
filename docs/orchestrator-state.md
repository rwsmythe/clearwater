# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 11** (`clearwater-orchestrator-20261026-0844`) ROLLED OVER 2026-10-26 ~22:30Z at ~415K (depth cap), at a
  boundary with no cell mid-round (verify: `comms/.launch-sessions.json`). **Generation 12 starts here.** Earlier: gen 10
  `clearwater-orchestrator-20261021-0004`, gen 9 `-20261020-1959`, gen 8 `-1556`, gen 7 `-1419`, gen 6 `-1134`, gen 5
  `-0802`, gen 4 `-0524`, gen 3 `-20261019-2346`, gen 2 `-20261018-1442`, gen 1 `-20261014-1258`.
- **Inbox:** gen 11 drained through CHARC's launcher FYI (`fd3e79167cc76899`) and STOPPED DRAINING at its rollover
  announcement. You are the sole drainer.
- **CHARC is generation 3:** `clearwater-charc-20261020-2115`. Cue that exact name (re-read `comms/.launch-sessions.json`).
- **Your session runs WITHOUT the background-shell reaper** (launcher `60b2642`, owner-directed): a full suite can run as a
  plain background job again; one heavy job at a time is still the rule.
- Bash-launch gauge at gen-11 bring-up: 122.9 ms. Re-measure at yours.

### Standing operator rulings

- **Unattended operation** (owner, 2026-10-14; CLAUDE.md "Roles"): every operator-bound question goes `--to
  charc` (type query, recommended answer first, one cross-session cue after posting). CHARC answers in the
  operator's stead except plan s.3 owner-reserved items. Info-updates (`--type fyi`) to the operator after each
  accept. No AskUserQuestion from this seat.
- **RESUMED 2026-10-26** at the owner's word ("resume", relayed by CHARC `064e23c84876bdfd`) after the 2026-10-21 pause.
- **Owner word 2026-10-20:** spec **v0.5.4**, plan v1.2, architecture FINAL 1.0, interim N6 = 25 min/min (D106),
  gain caps KEPT (D100). Owner-pending list (CHARC carries it): photos (WP3.6P), an iPhone clip (DR-15's B-frame
  leg), the V3 ratio figures as information for CP5/WP4.2 (now also in the WP3.11 record).
- **GoPro IMU and GPS are OUT OF SCOPE**: no `gpmd`, IMU or GPS data read or committed; GPMF settings only from
  `moov/udta` (FMWR/PRTN/PTCL). Location tags must never reach a committed record (WP3.10 R1 #2).
- **Cell depth:** read `uv run python scripts/cell_depth.py <cell>` at dispatch, every yield, before any ruling;
  ~250K evaluation, ~400K STOP. Opus cells re-grounding from a ledger with a TIGHT reading list started at 0 and
  reached 90-120K by their first yield this generation (much less than wave 3's 140-220K).
- **Kernel hazard (7)** (CHARC, 2026-10-21): never an uncommitted edit in the MAIN tree's working copy. Every edit --
  briefs, state, records, contract amendments -- in a worktree on its own branch, then `git merge --ff-only`.
- **Line endings (CHARC, 2026-10-26: "keep that blob check in the gate recipe for every accept"):** every committed
  blob is LF (main has 0 CR bytes everywhere, the debt register included). At every gate: for each file in
  `git diff --name-only <base>..<cand>`, `git cat-file -p <cand>:<f> | tr -cd '\r' | wc -c` must be 0.

### Live cells (gen 11; they die with this generation -- re-dispatch from their ledgers)

Dispatch prompts: gen 11 scratchpad
`C:\Users\rwsmy\AppData\Local\Temp\claude\C--Users-rwsmy-clearwater\5f10a032-edb3-44be-ab01-d21d2702ef2f\scratchpad\`
(`prompt-wp3.10-seat7.md`, `prompt-trancheB-common.md` + `mk.py`, `prompt-wp3.18-seat2.md`, `prompt-wp3.19-seat2.md`,
`mk_rerun.py` = builds a Reviewer B re-run prompt from pass 1 + a `rerun-section.md`). All branches from main `718324b`;
main is now `7fff7be`+ (docs only since).

| Package | Branch head / my candidate | State | Next |
|---|---|---|---|
| WP3.10 | `wp3.10` `5727842` (rebased by gen 11; `wp3.10-pre-rebase2` = `d389269`) | seat 7 (`wp310-cell7`): **full suite 4434 passed / 2 skipped, 2034 s, on `5727842` = my candidate-gate run** (one background process + foreground poll-waits; log `work/wp3.10/s7-full2.log`); FOOTAGE window granted ~21:10Z (legs a, b, c) | EXCLUSIVE floor row LAST and alone (OPEN/CLOSE to CHARC); report; return; then my Reviewer B (none run yet) and the stacked gate |
| WP3.17 | `wp3.17` `f819ef3` / `wp3.17-mc` `0f7b5cd` | RETURNED. A terminated R1. **B pass 1 BLOCKED** (float decimals cap 6) -> ONE remediation -> **B pass 2 BLOCKED, ADJUDICATED AT THE GATE**: 5 fixes (`14b448e` extreme spans no slider, `72356f8` slider ends exact, `c161353` shared owner clear, `7b7b6af` save-as refresh on failure, `f819ef3` docs) VERIFIED BY EXECUTION at my seat (5 failed on `f6b40a9`; 86 passed on the candidate); #1 (spans 15 decimals cannot resolve) = a LIMIT -> **bank DR** (trigger: a method declaring such a float) | stacked gate; accept record; DR row |
| WP3.18 | `wp3.18` (seat 2 `wp318-cell2`) | seat 1 retired at 342K after R1; seat 2: R2-R5; R3 procedural breach (fixes in the adjudicating turn; not voided); design guard after R4 -> lane restructured to ONE latest-intent invariant (`b1f9783`) + 200-seed interleaving test (`fa0fa7d`); **R5 = five-round gate: finding 1 adjudicated MINOR, loop TERMINATED**; cleanup (option S strict proxy) + report in progress | its return; my Reviewer B pass 1 (none yet) |
| WP3.19 | `wp3.19` `071cb1f` / `wp3.19-mc` `1be0a99` | seat 1 RETURNED (A converged R2; seam wording `efc95f5d4e7b8456`), retired at 261K; **B pass 1 BLOCKED** (2 majors) -> seat 2 (`wp319-cell2`) remediation -> **B pass 2 BLOCKED, ADJUDICATED AT THE GATE**: 4 fixes VERIFIED BY EXECUTION at my seat (5 failed on `9eefd83`; 85 passed on the candidate); #1 (ok with empty outputs) downgraded, defensive text in the panel, and **for CHARC/WP3.14's brief: "an ok JobResult names at least one output"**; #5 V7 at a few hundred items = LIMIT | stacked gate; accept record; tell CHARC the WP3.14 line |
| WP3.20 | `wp3.20` `1e0aae8` / `wp3.20-mc` `e47c8d2` | RETURNED. A terminated R1. **B pass 1 BLOCKED** (Clear-cache TOCTOU across the modal confirm) -> ONE remediation -> **B pass 2 BLOCKED (cache-limit job ordering), ADJUDICATED AT THE GATE**: `CacheLimiter` fix VERIFIED BY EXECUTION at my seat (failed on `34075f2`; 64 passed on the candidate). Interim `resolve_encoder` stub stays until WP4.3 swaps in WP3.10's (brief: "whichever lands second (or WP4.3)") | stacked gate; accept record |

**Reviewer B evidence:** `C:\Users\rwsmy\clearwater-review-evidence\wp3.{17,19,20}\reviewB\` (pass 1) and `reviewB2\` (pass 2), each
with `md5sums.txt`; all passes gpt-5.6-sol high, 0 `^ERROR`, footer present, VERDICT anchored, no withheld read in the
command lines (the hits are prompt/diff echoes). Runner: `run_review_B.sh` per folder; run it in the FOREGROUND
(`MSYS_NO_PATHCONV=1 timeout 590 wsl.exe bash -ilc 'bash /mnt/c/.../run_review_B.sh review'`, Bash timeout 600000).

**Gate plan (CHARC agreed):** ONE stacked full suite on main + WP3.10 + WP3.17 + WP3.18 + WP3.19 + WP3.20 (disjoint
files; order free) replaces each GUI cell's own full pytest; then ff + accept record per package; then main gates.
Ask CHARC to HOLD main first. **Run every long suite as ONE background process with FOREGROUND poll-wait calls**
(CHARC `b4f1c9c8fee81d83`): an idle session gets its background shells reaped (two reaps today at 92-94 %, in
`tests/test_prototype_backend.py`/`test_prototype_clip.py`); chunks only as the fallback after one more reap.

### Where things stand -- the successor starts HERE (gen 12)

Every cell of gen 11 died with it. Nothing is mid-round. In order:

1. **WP3.18 Reviewer B pass 1 BLOCKED** (`wp3.18-mc` `44ef658`; evidence `...\wp3.18\reviewB\`, md5s): ONE in-envelope MAJOR
   -- an A->B->A burst in the run-returned-to-`on_done` window: WP3.11 hands the adapter a recompute job for B (kept, per
   CHARC point 5), the reversion to A skips `retarget` because A == `run.target`, `on_done` declares complete, and the
   engine is left holding the B job (export enabled on the wrong statistics). Fix (panel side): once ANY `retarget`
   returned False during a run, a follow-up `run(latest)` ALWAYS starts at done-ok; test with a stub that models the
   retained job. Minors: #2 `_on_progress` drops the reported text (show it); #3 the report's `statistics ->
   smoothed_record` mapping must say the adapter returns None until a full run completes (WP3.11 serves near-phase records
   early); #4 runner close after a superseded run leaves phase "running" (set a terminal phase when `_start_run` hits a
   closed runner). **Dispatch a FRESH seat 3** (sonnet-high; seat 2 was at 274K; CHARC's rule: a B remediation past 250K goes
   to a fresh seat) from the ledger + `reviewB\review-B.txt`; ONE remediation, then ONE B re-run (template:
   `mk_rerun.py` + a `rerun-section.md`); a second blocking B is adjudicated at the gate.
2. **WP3.10:** seat 7 (`wp310-cell7`) finished the full suite (4434 passed / 2 skipped = the candidate-gate run) and the
   FOOTAGE window (legs a, b, c; figures in its ledger's RESUME HERE and `work/wp3.10/s7-footage/`, e.g. `legb-table.txt`).
   Footage results: (a) GX011627 MANDATORY/REQUIRED all SAME, `tied True` -> **DR-18 (1) CLOSES**; (c) the Edits
   compilation `open` accepts 3003/60000; 2 MANDATORY DIFFERENT = the accepted "rounded UP" coarse-movie-timescale limit
   (0.79 ms < one 1 ms tick). **(b) FINDING, a product defect:** on busy 4K, NVENC's High/Standard/Draft are the SAME encode
   (~20 Mb/s, flat PSNR): `-rc vbr -b:v 0 -cq N` with no `-maxrate` makes NVENC pick HEVC level 5.0, whose cap overrides
   cq (`nvcap.txt`: cq 18 21.68 vs cq 28 21.76 Mb/s; with `-maxrate 300M -bufsize 600M` 131.5 vs 37.3). **My recommended
   ruling for you to confirm:** approve the one-line fix in `encode.py` `_video_options` (maxrate/bufsize or an explicit
   level) + a test that the levels differ, as Reviewer A ROUND 9 scoped to the change; re-run leg (b) NVENC; propose the
   AD-12 mappings to CHARC on the fixed figures (libx265 measured H 1.54 / S 0.80 / D 0.34 of camera on busy footage ->
   estimate crf ~21/26/30). Disk-estimate risk for WP3.13/WP3.14: on a calm low-bit-rate clip outputs are 1.2-3.4x the
   source (NVENC), QUALITY_RATIO 1.0 x MARGIN 1.25 under-estimates High by up to ~2.7x -> to CHARC.
   Next: **seat 8** (opus-high) from the ledger's "RESUME HERE for seat 8" (`wp3.10` head `e7668e1`; note: the worktree's
   `clearwater.local.toml` points at the MAIN tree's `work\`, pass `--config` with the worktree's path): round 9 (if you approve), the (b) NVENC re-run,
   then the EXCLUSIVE floor row LAST and alone on the final code (OPEN/CLOSE to CHARC), the report, the return report. Then
   my Reviewer B on WP3.10 (none run yet; the product converged at R4, the bench at R8).
3. **WP3.17, WP3.19, WP3.20: B DONE** (each pass 2 adjudicated at the gate, fixes verified by execution at my seat; see the
   Live-cells table). Ready for the stacked gate.
4. **The stacked gate** (CHARC agreed): ask CHARC to HOLD main; build ONE stack on main of WP3.10 + 3.17 + 3.18 + 3.19 +
   3.20 (disjoint files; any order; patch-id per package against its author branch); ONE full suite on the stack top
   (CuPy as installed; plain background run now that the reaper is off); then ff + accept record per package (stack
   order), then the main gates (full suite + harness gate) once; the CR blob check on every changed file; post the release
   + return reports to CHARC; info-update to the operator.
5. **Owed to CHARC in the release post:** WP3.17 debt row ("a float span or bounds 15 decimals cannot resolve"; trigger: a
   method declaring one); WP3.19's line for WP3.14's brief ("an ok JobResult names at least one output") and its limit (V7
   unmeasured at a few hundred items); WP3.20's interim `resolve_encoder` stub (WP4.3 swaps in WP3.10's); WP3.18's WP4.3
   notes (adapter keeps its own pts list, F-2; keeps a returned job, point 5) and its R3 procedural breach (disclosed, not
   voided); the three gate adjudications (WP3.17/3.19/3.20 B pass 2) for CHARC to look at.
6. **Host:** one heavy job at a time. Small GUI targeted runs (<1 min, no FFmpeg/GPU) may overlap a suite or footage leg.

### (older) Where things stood at the gen-10 handover


1. **Gen 10 did, in order:** picked up under the pause; RESUME (`064e23c84876bdfd`); rebased `wp3.10` onto main
   (union conflicts in the probe-rules module set and `io/video/__init__.py`); WP3.4 seat 4 first with its EXCLUSIVE
   window (CPU-subsample STOP ruled no, CHARC upheld); WP3.10 seats 4-6 and WP3.11 seats 2-3 in parallel; **WP3.4
   ACCEPTED** (main `ad15ab4`; CHARC QA static half CONFIRMED `d3c7ebcf9749a876`, register rows `6b58619`); **WP3.11
   ACCEPTED** (main `47235b6`; CHARC QA pending).
2. **OWED ON MAIN `47235b6`: a full pytest.** The stacked candidate `f1c1bd8` ran CuPy 4200 passed / 2 skipped; its
   no-CuPy leg was STOPPED by Claude Code's low-memory reaper (not restarted, per the reaper's rule; the brief needs
   none). Main's code = `f1c1bd8`'s. I asked CHARC to let its QA suite on main stand as main's figure; if CHARC asks
   you instead, run it (offscreen, background, >= 5 GB free, nothing else heavy).
3. **Rulings this generation (in records/ledgers):** CPU subsample is evidence, not D106's STOP (WP3.4; CHARC upheld);
   Reviewer B dtype finding taken as a remediation (CHARC: RIGHT); WP3.11 B2 second blocking pass adjudicated at the
   gate (signed-zero fixed and verified by execution; two cancel races as limits, DR-47) -- CHARC to look; WP3.10
   five-round gate continue (tool code is result-bearing); WP3.10 design guard -> hybrid.
4. **Debt this generation:** DR-46 (WP3.4: a mixed `[True, 1.0]` list passes the dtype check; out of envelope), DR-47
   (WP3.11: old job callable, cancel during/after `mark_complete`, lock-free cancel race). Flaky test seen once under
   load: `tests/test_gui_startup.py::test_shutdown_stops_every_worker_when_one_overruns_its_timeout` (WP3.16's; 0.05 s
   timing precondition) -- NOT banked (did not recur in 2 later full runs); bank it if it fails again.
5. **Consumer notes standing:** from gen 8/9 (`git show 05dd68a:docs/orchestrator-state.md`, "Where things stand" 4);
   new: WP3.14/WP3.18 read the WP3.11 record under `schema_hash` (numbers canonical: int == float, bool distinct,
   signed zero equal) and DR-47's cancel race; WP3.17 shows `blend_with_original` 0-100.
6. **Host:** one heavy job at a time. Today two full suites at once ran FFmpeg out of memory twice (WP3.4 CuPy run;
   a WP3.11 V3 test), and the reaper stopped a background suite while the session was idle at ~7-8 GB free. The full
   suite is now ~4200 tests, 29-33 min with CuPy, ~20 min without.

### Workstreams

Each accepted package had its return report posted to CHARC and an info-update to the operator.

| Package | Accepted | Main | Record | CHARC QA |
|---|---|---|---|---|
| WP0.1 | 2026-10-14 | `c09f747` | `docs/proofs/wp0.1-accept.md` | STANDS |
| WP0.2 | 2026-10-15 | `4863a90` | `docs/proofs/wp0.2-accept.md` | STANDS (DR-6..DR-10) |
| WP1.1 | 2026-10-15 | `9711faf` | `docs/proofs/wp1.1-accept.md` | STANDS (DR-11..DR-13) |
| WP1.2 Part A | 2026-10-15 | `f6d998a` | `docs/proofs/wp1.2-accept.md` | STANDS (`bac37599277c1365`) |
| WP1.5 | 2026-10-15 | `3242679` | `docs/proofs/wp1.5-accept.md` | CONFIRMED (`6d4fca629d21efe0`) |
| WP1.2R | 2026-10-15 | `996274e` | `docs/proofs/wp1.2r-accept.md` | CONFIRMED (`60dc8ad66427bb15`) |
| WP1.3 | 2026-10-15 | `7178540` | `docs/proofs/wp1.3-accept.md`; DR-20, DR-21 | CONFIRMED (`09057ee4b3979fa4`) |
| WP-T1 | 2026-10-15 | `f6a34a4` | `docs/proofs/wp-t1-accept.md`; DR-22 | CONFIRMED (`3501648bc8844468`) |
| WP1.4 | 2026-10-19 | `91f5775` | `docs/proofs/wp1.4-accept.md`; DR-23..DR-26 | CONFIRMED (`6c5d88685e64a37c`) |
| WP-T2 | 2026-10-19 | `8c9d780` | `docs/proofs/wp-t2-accept.md`; DR-27 | CONFIRMED (`d40217a81696cc03`) |
| WP1.2 Part B | 2026-10-19 | `2dd06cf` | `docs/proofs/wp1.2b-accept.md`; DR-28; depth breach recorded | CONFIRMED (`cb61a4e41f625d73`) |
| WP1.3D | 2026-10-20 | `7f9fea1` | `docs/proofs/wp1.3d-accept.md`; DR-29 | CONFIRMED (`c6bda8a38146274f`) |
| WP1.4b | 2026-10-20 | `afaff0e` | `docs/proofs/wp1.4b-accept.md`; Gate result 4 KEEP; DR-30; flip witness 6/6 | CONFIRMED (`2fe4e7e1dc9e0854`) |
| WP2.1S | 2026-10-20 | `a866f06` | `docs/proofs/wp2.1s-accept.md`; DR-31; 2 depth re-seats; B errata at the gate | CONFIRMED (`9fb52c00bbb58a9b`) |
| WP2.2 | 2026-10-20 | `b288533` | `docs/proofs/wp2.2-accept.md`; DR-32; B re-run major adjudicated at the gate; IF-1..IF-10 frozen; 892 passed on main | CONFIRMED (`4f11a18fc46c9fc4`) |
| WP2.3 | 2026-10-20 | `d605925` | `docs/proofs/wp2.3-accept.md`; DR-33; B re-run 3 majors adjudicated at the gate; first cell past cap at R1; 1138 passed on main | CONFIRMED (`2e828b51020759b1`) |
| WP3.15 | 2026-10-20 | `da54a47` | `docs/proofs/wp3.15-accept.md`; DR-34; DR-32 closed; second blocking B adjudicated at the gate (B2#1 refuted by execution); stacked gate | CONFIRMED (`3ee39aedcd59a4aa`) |
| WP3.13 | 2026-10-20 | `6dd5a00` | `docs/proofs/wp3.13-accept.md`; DR-35; A converged R3 (R1 critical fixed by tokened temporaries); B clean | CONFIRMED (`3ee39aedcd59a4aa`) |
| WP3.7 | 2026-10-20 | `6e3417a` | `docs/proofs/wp3.7-accept.md`; DR-36; A terminated R2; B clean; main gates for the stack: 1671 passed | CONFIRMED (`3ee39aedcd59a4aa`) |
| WP3.1 | 2026-10-20 | `f4acbd0` | `docs/proofs/wp3.1-accept.md`; DR-37; A terminated R2 (two cells, depth re-seat at R1); B clean (erratum at the gate); two full runs (CuPy and none); 1844 passed on main | CONFIRMED (`6cadc26e470cd8c6`) |
| WP3.3 | 2026-10-21 | `09d1d11` | `docs/proofs/wp3.3-accept.md`; DR-14 CLOSED; DR-38; B clean (2 recovered reconnects); stacked gate (re-ordered) | CONFIRMED (`075a686775a95772`) |
| WP3.5 | 2026-10-21 | `55c266d` | `docs/proofs/wp3.5-accept.md`; DR-20 (1) CLOSED; DR-39; B clean | CONFIRMED (`075a686775a95772`) |
| WP3.2 | 2026-10-21 | `4b4da9b` (+ `68a8d93` main gates) | `docs/proofs/wp3.2-accept.md`; DR-40; B pass 1 major (float64 leak, confirmed by execution) -> ONE remediation -> B re-run clean; main 2904 passed | CONFIRMED (`075a686775a95772`) |
| WP3.12 | 2026-10-21 | `3aaf395` | `docs/proofs/wp3.12-accept.md`; DR-41; A converged at the R5 gate; B pass 1 blocking -> ONE remediation -> pass 2 adjudicated at the gate; stacked with WP3.6; main 3440 passed | CONFIRMED (`28160f360239ca35`) |
| WP3.6 | 2026-10-21 | `d0f00ee` (+ `4ec835d` main gates) | `docs/proofs/wp3.6-accept.md`; DR-42; built-in ICC moved reader -> writer (IF-1); B blocked twice, pass 2 adjudicated at the gate; main 3440 passed | CONFIRMED (`28160f360239ca35`) |
| WP3.16 | 2026-10-21 | `a2685cb` (+ `0c41615` main gates) | `docs/proofs/wp3.16-accept.md`; DR-43, DR-44; A converged R4; rebased onto WP3.6 by the orchestrator; one additive contract member; B blocked twice, pass 2 adjudicated at the gate; main 3559 passed | CONFIRMED (`6d15bf1f653b5038`) |
| WP3.9 | 2026-10-21 | `09ab408` | `docs/proofs/wp3.9-accept.md`; DR-45; A converged R3; candidate 3670 passed; B clean (1 minor + 1 advisory banked, 1 erratum) | CONFIRMED in full (`bfe4b56072240ecf`; 3670 passed at CHARC's seat; worktrees `wp3.9`, `wp3.9-mc` removed by gen 10) |
| WP3.4 | 2026-10-26 | `ad15ab4` | `docs/proofs/wp3.4-accept.md`; DR-46; A converged R1; B pass 1 blocked (dtype coercion, confirmed by execution) -> ONE remediation -> B pass 2 clean, erratum at the gate; CRLF blob caught and fixed; candidate CuPy 3970 / no-CuPy 3418 | CONFIRMED static half (`d3c7ebcf9749a876`; register rows `6b58619`) |
| WP3.11 | 2026-10-26 | `47235b6` | `docs/proofs/wp3.11-accept.md`; DR-47; A converged R3; B pass 1 blocked (schema-hash divergence) -> fresh-seat remediation -> B pass 2 blocked (signed zero) ADJUDICATED AT THE GATE, verified by execution; stacked on WP3.4; CuPy 4200; no-CuPy reaped; main full pytest owed (CHARC asked to let its QA suite stand) | pending |
| DR-44 amendment | 2026-10-21 | `de206e2` | `docs/proofs/dr44-contract-amendment.md`; B pass 1 blocked, remediated, pass 2 clean; main 3570 passed | checked (`00b7f7a8baa5ae3b`) |

Kept branches (evidence; do not delete unasked): `wp3.4`, `wp3.4-mc`, `wp3.11`, `wp3.11-mc`, `wp3.10-pre-rebase`, `orch-state-g10`, `orch-state-g10b`, `wp3.9`, `wp3.9-mc`, `dr44`, `dr44-record`, `wave3-briefs`, `wp3.12`, `wp3.12-mc`, `wp3.6`, `wp3.6-mc`, `wp3.6-mc2`, `wp3.16`, `wp3.16-mc`, `wp3.16-pre-rebase`, `wp3.2`, `wp3.2-mc`, `wp3.2-mc2`, `wp3.3`, `wp3.3-mc`, `wp3.3-mc2`, `wp3.5`, `wp3.5-mc`, `wp3.5-mc2`, `wp3.15`, `wp3.15-mc`, `wp3.13`, `wp3.13-mc`, `wp3.7`, `wp3.7-mc`, `wp3.1`, `wp3.1-mc`, `wp2.3`, `wp2.3-mc`, `wp2.2`, `wp2.2-mc`, `wp1.2b`, `wp1.2b-b1`, `wp1.3d`, `wp1.3d-b1`,
`wp1.4b`, plus the earlier packages' (`git branch`).

### Practice notes (this instance)

- **Merging:** rebase in a `-mc` worktree; compare `git patch-id --stable` (author range vs
  candidate vs main); gate there; Reviewer B; `git merge --ff-only`; `uv sync`; re-gate main. Ask
  CHARC to hold main from B to the merge; no orchestrator commit on main in that window either.
- **The full pytest now takes 8-15 minutes (771 tests)**, past one 10-minute tool call: run it in
  the background with output to a scratchpad file, then `-m gpu` and the harness gate. Never two
  GPU jobs at once (the bit-identity witness waits for pytest).
- **Reviewer B = my own single Codex pass at this seat, never a cell.** WSL, codex-cli 0.162.1,
  `-m gpt-5.6-sol -c model_reasoning_effort=high -s read-only --skip-git-repo-check`. Runner
  template: `C:\Users\rwsmy\clearwater-review-evidence\wp1.4b\reviewB\run_review_B.sh` (probe |
  review; invoke `MSYS_NO_PATHCONV=1 wsl.exe bash -ilc 'bash /mnt/c/.../run_review_B.sh <mode>'`).
  Prompt template: `...\wp1.4b\reviewB\review-prompt-B.md`. Assertions: banner, `^ERROR` count,
  `ERROR codex_core` classified, `tokens used` footer, `succeeded in` count, anchored VERDICT,
  withheld-access grep on the `/bin/bash` command lines; md5s to `md5s.txt`. A blocking B on an
  introduced major gets ONE remediation and one B re-run; a second blocking B is adjudicated at the
  gate. Report overstatements B finds can be fixed as "Erratum at the gate" text in the report.
- **Bit-identity witness for prototype default or hook changes:** generation 2's script is in its
  session scratchpad (`witness_flip.py`; not in the repo). Spec: `correct()` with explicit
  methods on a fixed synthetic 600x900 image, seed 12345, Ancuti blue off/on and 3C, CPU and GPU,
  `np.array_equal`, run once per tree (each tree's own venv) and compared.
- **Messages to cells:** a SendMessage to a working cell lands only when it yields, and a queued
  message WAKES a cell that has gone idle. At any re-seat, send the old cell an explicit STAND-DOWN
  before dispatching the successor, and have the successor check `git status` for foreign
  changes. A ruling sent at a yield may arrive after the cell has moved on: if it matters, follow
  up with a short superseding message.
- **Post first, then cue.** Write mailbox bodies with the Write tool (a long bash heredoc once
  failed to parse and the cue went out before the post); cue only after `posted ->` is shown.
- **Bash `cd`:** a bare `cd` in a Bash call moves the session's working directory. Use absolute
  paths, `git -C`, or `( cd ... && ... )` subshells.
- **Truncated cell reports:** extract the last assistant text from
  `~/.claude/projects/C--Users-rwsmy-clearwater/<session>/subagents/agent-a<name>-*.jsonl`.
- **Worktrees** holding a copied `clearwater.local.toml` need `git worktree remove --force`.
- **Process control:** the auto-mode classifier blocks `Stop-Process`; surface it, do not work
  around it. No Defender exclusion requests (the owner's setting).
- **Reviewer B runner for later packages:** copy
  `C:/Users/rwsmy/clearwater-review-evidence/wp2.2/reviewB/run_review_B.sh` and
  `review-prompt-B.md` (sed `wp2.2` -> the new id). Reviewer prompts must exclude `docs/proofs`
  with a glob that MATCHES (`--glob '!docs/proofs/**'`), and the assertion grep must check command
  OUTPUT too: a non-matching glob leaked ledger lines in WP2.2 R2.
- **Re-run of B after a remediation:** reset the `-mc` branch to the remediated author branch,
  rebase, and add a "THIS IS THE RE-RUN" section to the prompt listing the pass-1 findings
  (WP2.2 `reviewB2/`).
- **QA catches this generation:** a cell's "no W7.json" claim was false (WP2.1S), and a cell's
  "1 MB+ blocks" claim was really buffer depth. Check every negative claim against disk.
- **The orchestrator's own depth cap:** the hook prints `[ctx]`. Roll over at the first clean
  boundary after about 400K; never with a cell mid-round, since it dies with you.
- **Memory pressure:** the host stopped background test runs on 2026-10-19 for low system memory;
  do not restart a killed run on your own; ask.
- **`-mc` worktree setup (gen 4, paid for at WP2.3):** after creating or rebuilding a `-mc`
  worktree, copy `clearwater.local.toml` into it AND `mkdir -p <wt>/work` BEFORE the full
  pytest (`--basetemp=work/...` needs its parent; without both, 107 errors / 11 failures that
  are not the package's). Build and rebase it with `git -c core.autocrlf=false ...` (the system
  gitconfig sets autocrlf true; a rebase across the commit that adds `.gitattributes` stopped on
  the CRLF manifest). A bare `git -C <wt> config core.autocrlf false` writes the SHARED
  `.git/config`: never do that.
- **Bare `cd` (gen 4 did it three times):** every gate in a worktree runs in a `( cd ... && ... )`
  subshell. The session's cwd moving under a live cell is hazard (1).
- **Cell depth:** run `scripts/cell_depth.py <name>` from the repo root (from a worktree it
  guesses the wrong project dir).
- **Brief yield schedule:** name the R1 yield explicitly ("END YOUR TURN as soon as round N's
  verdict is adjudicated, BEFORE remediating"). wp23-cell, without it, ran R1 and its
  remediation in one turn to 407K; wp23-cell2, with it, yielded on time at 96K.
- **Delayed idle notifications:** a cell's `idle_notification` can arrive AFTER its real report
  and after your reply woke it; compare its timestamp with your last message before acting.
  Never reply to a stale one (a reply wakes the cell).
- **Drafting helper:** brief drafting can go to a `general-purpose` (opus) helper that writes
  the drafts uncommitted; QA them against disk (grep every cited AD/IF/DR/clause) before the
  query. `wave1-drafter` did WP3.1/3.7/3.13/3.15 this way.
- **Long mailbox bodies and scripts:** write them with the Write tool; a long bash heredoc
  failed to parse again in gen 4.
- **Gen-5 practice (wave 1, four parallel cells):**
  - **Window queue (X5):** one full-pytest window at a time, granted by SendMessage; the cell sends
    `WINDOW RELEASED: <summary>` mid-turn and carries on into its Reviewer A round. A queued grant
    can land BEHIND another queued message; if the cell says "no window", re-grant with a short
    superseding message.
  - **The orchestrator's candidate gate can replace a cell's final-head run** (same code rebased
    onto main): it saves a serialised window. Tell the cell, and it reports "run by the
    orchestrator on the candidate".
  - **Stacked merge gate** (CHARC accepted the form, `99e73cf967e2d559`): rebase candidate N+1 onto
    candidate N, patch-id check each, ONE full pytest on the stack top, then ff + accept commit per
    package (rebase each onto the new main, patch-id again), then the main gates once at the end.
    Ask CHARC to HOLD main first and post the release with the return report.
  - **Reviewer B prompts:** git does not work inside a worktree under WSL (the `.git` file points
    at a Windows path). Say in the prompt that git is unavailable and that the diff and HEAD sha
    are supplied (CHARC `3ee39aedcd59a4aa`).
  - **Exclusive windows:** CHARC's QA full pytest overlapped WP3.1's speed row (~21:09-21:20Z).
    Tell CHARC when an exclusive window opens, and ask it not to run a suite until it closes.
  - **Removing merged worktrees:** `git worktree remove --force` fails "Filename too long" on
    pytest basetemp trees; follow it with PowerShell
    `Remove-Item -LiteralPath "\?\C:\Users\rwsmy\clearwater\.worktrees\<name>" -Recurse -Force -Confirm:$false`
    (a literal path; an interpolated `\?\$p` is blocked by the guard), then `git worktree prune`.
  - **Idle notifications:** nearly every cell message was followed by an idle notification
    summarising it; most predate the reply they cross. Check the timestamp, never reply to one.

- **Gen-6 practice (wave 2):**
  - **Never send a cell a ruling that changes work it may already be doing** without a numbered
    FINAL line: WP3.5's bounds flipped three times when two of my messages crossed its round. Send
    ONE ruling per question, mark it FINAL, and if a correction is needed say "supersedes my
    message of HH:MM" in its first line.
  - **Heavy non-exclusive measurements** (WP3.12's 4K decode) and full-pytest windows can share
    the host if free memory stays above ~5 GB (check `Win32_OperatingSystem.FreePhysicalMemory`);
    runs strictly sequential inside a window; a run that dies without a summary is reported, not
    restarted.
  - **A cell idle after a background run** may not wake on its completion: check its status file
    and nudge it (WP3.2's runs finished ~20 min before it reported).
  - **Drafting wave briefs:** two `general-purpose` helpers in parallel (numeric / I/O halves) with
    one common commission file; a citation-check script (ids defined, quotes verbatim, paths) run
    at this seat before the CHARC query. The script was in the gen-6 scratchpad
    (`cite_check.py`); rewrite it if needed (about 70 lines).
  - **Interface amendments** CHARC rules are ONE orchestrator commit on main before the tranche
    branches (`f4cd1e4`), gated by the full pytest; `docs/architecture.md` section 3 is CHARC's and
    may lag the code (AD-20 records the amendment).
  - **Permission laundering:** a cell asked this seat to `Stop-Process` a pid the classifier
    refused at its seat; refused here too and surfaced to the owner.

- **Gen-7 practice (wave 2, tranche A accepts):**
  - **Re-ordering a stack** when its bottom package takes a Reviewer B remediation: with disjoint
    files, rebuild `-mc2` branches in the new order (WP3.3 -> WP3.5 -> WP3.2'); patch-ids hold;
    a B pass run on the earlier tree stands when the package's owned files are byte-identical in
    both trees (`git diff <old-mc> <new-mc2> -- <owned paths>` empty; say so in the record). One
    full pytest (normal + cupy-unimportable) on the final stack top, then ff + record per package
    in stack order, then the main gates once.
  - **Cupy-unimportable run:** a scratch script that sets `sys.modules["cupy"] = None` and
    `sys.modules["cupyx"] = None`, then `sys.exit(pytest.main(sys.argv[1:]))`; run with
    `uv run python <script> --basetemp=work/pt-mc-nocupy -q -p no:cacheprovider`.
  - **Rulings cross remediations:** a cell that yields with a round's verdict often carries on
    into the remediation and the next round before a ruling lands (wp312-cell2 did it twice).
    Put the binding stop in the DISPATCH prompt ("make NO change in the turn that adjudicates a
    round"), not only in a later message; past ~250K say "REVIEW ONLY this turn".
  - **`git stash` in a cell:** the stash stack is shared by every worktree; forbid it in every
    dispatch prompt ("use a WIP commit or a scratch copy").
  - **Line endings:** `git show <rev>:<path>` displays CRLF on this machine; check stored blobs
    with `git cat-file -p` (blobs are LF). Commit in a worktree with `-c core.autocrlf=false`.
  - **Debt-register edits at accept:** a scratch script inserting the new DR row after the last
    `| DR-` line and rewriting a closed row's status cell; check the status cell ends `| OPEN |`
    first (gen 7's `dr_edit.py` in its scratchpad).
  - **The harness gate prints `acked 1 message(s); moved inbox -> read.`** from its own temporary
    mailboxes; the real inboxes are untouched (verified). Redirect it to a log and grep
    `^Ran |^OK|FAILED`.
  - **Suite size now:** ~2905 tests; the full normal run ~15 min, cupy-unimportable ~10 min.
  - **Reviewer B finding against the prompt's own wording** (WP3.5 B (2): "no GPMF data") is
    DECLINED with the standing rule cited; word prompts from the rule, not a paraphrase.

- **Gen-8 practice (wave 2, tranche B accepts):**
  - **Re-dispatch from ledgers works:** a fresh cell given the recipe, the brief, the ledger's
    "resume here" section and the rulings in the prompt resumed cleanly every time (5 cells).
  - **Multi-finding remediations go to a fresh cell** once a cell is past ~200-250K (WP3.6 R1:
    12 findings, fresh cell; WP3.16 after R4). Bounded single steps continue in the same cell.
  - **Read a cell's design choice against the frozen IF docstrings** before granting a window:
    WP3.6 put a synthesized ICC profile in the READER, which contradicts IF-1. Moving it cost one
    small turn; after the reviews it would have cost a round.
  - **Ask CHARC to clarify a ruling clause that collides with a brief ruling BEFORE dispatch**
    (the "no output ever lacks iCCP" clause against question 3): answered in under a minute.
  - **Reviewer B now usually blocks on pass 1**, and on pass 2 too; pass 2 is adjudicated at the
    gate per the standing practice. Bank with a TRIGGER naming the consumer package, and say in
    the release post which adjudication CHARC should look at.
  - **Lock conflicts (X-B3):** resolve `pyproject.toml` by a reviewed script (scratchpad
    `resolve_pyproject.py`, `union_conflict.py`, `essentials_conflict.py`), then
    `git checkout --ours uv.lock` + `uv lock`; never a hand merge of the lock.
  - **The debt register's committed blob is CRLF** (49 CR in 49 lines at gen 8). An LF rewrite
    churns the whole file, so after a scripted insert run `sed -i 's/$/\r/'` and check
    `git diff --stat` shows +N only.
  - **Prompt slips caught by cells:** the WP3.16 cell found I had named the wrong base sha; the WP3.6
    cell found a source my "only nclx gives assumed=False" premise missed. Keep inviting it.
  - **One heavy job at a time** (see "Where things stand" 5). Codex in WSL holds ~2.3 GB (`vmmemWSL`).
  - **Main gates:** run with `QT_QPA_PLATFORM=offscreen` now that the GUI tests are in the suite.
    The suite is ~3559 tests: normal ~15 min, cupy-unimportable ~10.5 min. Main's venv did NOT need
    the Essentials reinstall (it never had the meta-package); other venvs that had it do.

- **Gen-9 practice (wave 3, tranche A):**
  - **Hazard (7) in practice:** briefs, contract amendments, accept records and this state file all went through
    a worktree branch + `git merge --ff-only`. Helpers writing drafts get the worktree path in their commission.
    `git -c core.autocrlf=false worktree add` for any `-mc` (a plain add + autocrlf=false rebase stops on
    "unstaged changes"). Diffs for a reviewer: `git diff A..B` on BRANCHES that share history, or a commit range
    (`X~1..X`), never `main..branch` after main moved (it shows main's newer commits reversed).
  - **Opus cells burn 140-220K at round 0.** Plan the re-seat at dispatch: round 0 in seat 1, build in seat 2,
    reviews in seat 3 when needed. A bounded final task before retiring (measure, write RESUME HERE, commit)
    and a fresh cell dispatched with a short prompt that points at the base dispatch file + overrides worked
    every time (WP3.4 x2, WP3.10 x2).
  - **Dispatch prompts as files:** `prompt-wp3.N.md` in the gen-9 scratchpad (gone with it); the template is in
    this file's history only through the briefs' Rulings + the ledgers. Rebuild: READ FIRST, WORKSPACE (no bare
    cd, no main-tree edits, no stash, autocrlf=false commits), YIELD SCHEDULE (round 0, windows, yield at every
    verdict before remediating, ~400K stop, final report), depth from the dispatcher, PACKAGE NOTES.
  - **Check premises before relaying a STOP:** WP3.11's V3-1 was first measured with AD-14's metric; a re-check
    against the spec's own metric (std of frame-to-frame differences) was the right order (CHARC upheld it).
  - **Rulings cross yields:** a cell often yields with a report written before a queued ruling landed. Idle
    notifications are almost always stale copies; reply only to the cell's real message, and when a ruling may
    not have landed, send a short RECAP marked FINAL.
  - **Grants for test lines in another package's files** (WP3.7's exact module-set test; WP3.1/3.2/3.3 assertion
    lines pinning behaviour a debt fix removes): small, named in the report's owned-files list, one commit.
  - **Codex B on a GUI change** found the one path nobody tested (the open path's unfiltered clear). Even a small
    orchestrator-authored contract amendment gets both nets.

- **Gen-10 practice (wave 3 resume, tranche A accepts):**
  - **Bare `cd` (gen 10 did it THREE times into gate worktrees while cells were live, each reverted in one call):**
    use `cd` ONLY to the repo root; every worktree command is `( cd <wt> && ... )`, `git -C`, or absolute paths.
  - **Order an EXCLUSIVE window first** when re-dispatching several cells: WP3.4's exclusive runs went before the other
    cells were dispatched, so nothing else was on the host.
  - **Full suites never overlap:** two at once ran FFmpeg out of memory; a cell's targeted FFmpeg tests during another
    cell's full suite did too. Grant one full suite at a time and say "targeted tests only" to the others.
  - **Low-memory reaper:** Claude Code stops background shells under memory pressure while the session is idle; the
    note says do not restart unasked. Record it as not-a-result.
  - **Line endings at the gate:** CRLF blobs appeared from cells' `sed -i`/script edits and from a docstring-only
    commit; check every changed blob for CR bytes (see the standing rule above).
  - **Stacked gate across a remediation:** build `N+1-mc` on `N-mc`; when N merges first, `rebase --onto main <old N-mc
    head>` and show 0 code lines differ from the tested stack top.
  - **Reviewer B prompts:** write the contract from the RULE, not a paraphrase (my WP3.4 prompt named bools, the ruled
    Y-2 list did not; CHARC upheld the remediation anyway). Write `md5sums.txt` in every B folder and name the md5s in
    the record (CHARC asked).
  - **Design guard in a dispatch:** when one subsystem keeps producing blocking findings (WP3.10's watcher process,
    three in two rounds), tell the next seat to STOP and propose the simpler design instead of fixing round N+1; the
    hybrid closed the loop at the next round.
  - **Cells catch ruling flaws:** WP3.11 seat 3 found my canonical-`==` ruling missed `True == 1.0` and built a typed
    compare; invite deviations with evidence.
  - **Prompts as files:** gen 10's dispatch prompts are in its scratchpad
    `C:\Users\rwsmy\AppData\Local\Temp\claude\C--Users-rwsmy-clearwater\9db1a59d-fecc-4278-994b-f6ddecfa2635\scratchpad\`
    (`prompt-wp3.10-seat4.md`, `prompt-wp3.11-seat2.md`, `prompt-wp3.4-cell4.md`, `pytest_nocupy_gate.py`); Reviewer B
    prompt templates under `C:\Users\rwsmy\clearwater-review-evidence\wp3.4\reviewB*` and `...\wp3.11\reviewB*`.

### Pending (still valid)

- The smoothing default is 2.0 s (v0.5.4 7.2), with the step-aware temporal task for WP3.11;
  the WP1.4b lighting-step finding (a genuine step at 0.90 s in GX011600) is its input.
- No `.LRV`/`.THM` exist (owner); D60 handled in v0.5.2.
- `_windows_power()` in `bench.py` is instrument-only (CHARC); never into `src/clearwater/`
  without a fresh ruling.
- IF-5 `VideoSink.abort` docstring cites D84; it should be D44/D85 (CHARC: fix at the next
  interface touch, not before).
- Open debt: see `docs/debt-register.md` (its status column is authoritative). Gen 10 added DR-46, DR-47; WP3.4 closed DR-19, DR-38 and parts of DR-37/DR-40 (rows by CHARC at `6b58619`); WP3.11 closes DR-23 and DR-25 (1)(2)(4)-(7) at CHARC's QA.
