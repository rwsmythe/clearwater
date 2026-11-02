# WP5.2 — Performance and memory runs (dispatch brief)

**Status:** FINAL 2026-11-02 by CHARC generation 12 (`clearwater-charc-20261101-1330`) on the orchestrator's dispatch fill `f70ad027`; commissioned after WP-DR113's dispatch. (Drafted 2026-11-01 by generation 11, written while
WP5.3 builds; FINAL when CHARC posts the commission after CP5 opens and the orchestrator fills the dispatch fields
(base, yields, GATE_CHECKS). No tripwire (plan section 3): one new tool and one tool edit under `tools/`, a report;
no product module, no dependency, no frozen interface, no persistent-data shape. Spec v0.5.7. **Owner decision
inside: ONE, at the end, not in the package:** the N6 final figure (D106 says "re-set from the WP5.2 re-measure";
any change to the spec is owner-reserved). The package MEASURES; CHARC proposes the figure from the report; the
owner rules. The Questions carry CHARC's recommended answers; a round-0 dispute with evidence is a STOP to CHARC.

| Field | Content |
|---|---|
| ID and title | WP5.2 — Performance and memory runs: V15 and V16 on full clips at the shipped defaults, the first real witness of the automatic CPU fallback (D111), the figures of record for the N6 re-set. |
| Lane | **CODEX**: `implementer-codex-sol-high` (committed instruments run to a fixed plan, one small tool, one tool fix, a report; no frozen interface). Reviewer A = the Claude pass; Reviewer B = the Claude pass at the orchestrator's seat, EXECUTING (the planted-breach test and the holder tool run). Both under the 92 % rule. |
| Tier and size | **STANDARD**, size M per the plan. ONE rung. Every measured leg is a RUN REQUEST executed at the orchestrator's seat inside an EXCLUSIVE window (plan 4.3; the cell never runs a timed leg itself); the cell reads the records back and writes the report. |
| Base | main at dispatch (after WP5.3's accept; floor WP5.1 `0e8f0e00`, WP-T7 `5b922662` so the gate carries `--timeout`). |
| Goal | (1) V16: the end-to-end export rate at 4K in the owner's recording modes on the shipped build, cold cache, c3 defaults, NVENC, with WP3.21's row set repeated so the before / after chain stays comparable; (2) V15: peak RAM and peak graphics memory on the 5.3K 8:7 clip and on the largest photo, 16-bit, and the CPU fallback ENGAGING under real memory pressure, output within AD-11's CPU-vs-GPU bound; (3) the admission estimate's margin per row (the 5d finding: 1.5x on a 24.5 MP photo); (4) DR-72 closed (the bench stops on a memory breach). |
| Spec / decision clauses | N4 (16 GB RAM for video including 5.3K 8:7 and the largest photo; graphics memory a second limit; automatic CPU fallback; bounded buffering); N6 / D106 (interim 25 min/min at 4K end to end; the figure re-set from this re-measure; 5.3K best effort); V15; V16; D110; D111; AD-1 (pool estimate); AD-9 (`force_cpu`); AD-11 (CPU vs GPU 2e-3 max, 2e-4 mean); AD-21 (Option C: WP3.21 targets about 10 min/min, N6 set finally here); AD-30 (full clips are the subject here, so the `fullclip`-class runs are the point, not the exception). |
| Files owned | **EDIT:** `tools/export_bench.py` (DR-72 only: exit status 3 and stop the plan on `memory_check.passes == false`; the docstring's exit statuses; nothing else moves). **NEW:** `tools/device_hold.py` (allocate and HOLD a given amount of device memory with CuPy in its own process until a stop file appears or a timeout; prints the held bytes and the free figure before / after; `--mib`, `--stop-file`, `--timeout-s`; releases on any exit), `tests/test_device_hold.py` (gpu-marked: holds 256 MiB, the free figure drops by at least that, released at exit), `tests/test_export_bench_breach.py` (parallel-leg: a planted `memory_check` breach makes the plan stop with exit 3; built on the bench's existing record-reading seam, no clip run). `docs/reports/wp5.2-performance-memory.md`, `docs/proofs/wp5.2-ledger.md`, this brief (rulings folded). |
| NOT owned | `src/clearwater/` whole (a product defect found by a run = STOP to CHARC with the record; no fix here); `tools/headless_export.py`, `tools/photo_verify.py`, `tools/video_io_bench.py`, `tools/core_speed.py` (run, not edited); `tests/conftest.py`; every fixture. |
| Locks | Footage read-only; outputs under `work/wp5.2/` (`--keep` only for the fallback leg's two outputs, deleted after the comparison); nothing footage-derived committed; the privacy lock (no GPS / IMU bytes in any committed file; the records already redact). No timed figure is taken outside an EXCLUSIVE window. The admission estimate (`core/memory.py`) is NOT tuned here (a finding goes to the report and the register). |
| Markers | `tests/test_device_hold.py` `gpu`; `tests/test_export_bench_breach.py` parallel-leg (under 5 s, no clip). No `fullclip`-marked test is added: the full-clip runs are RUN REQUESTS, recorded, not gate tests. |
| Hardware flags | `gpu`, EXCLUSIVE. Every leg: nothing else heavy on the host (no gate leg, no Claude pass, no Codex turn that runs tests, no WP5.3 piece), `df -h /c` and the card's clocks / temperature before and after (the bench records them), the strays listed; opened and closed to CHARC per window with the figures. Total GPU time about 2.5 h (V16 plan about 70 min, the fallback leg about 20 min, the photo legs about 10 min, the 5.3K leg about 5 min), split over as many windows as the orchestrator's board allows; GX011625 (the sustained row) LAST in its window. |
| Out of scope | Tuning the estimate or the pipeline (an owner wish below the measured rate opens a package; DR-70 names the lever); a real 5.3K recording (none exists in the owner's footage: the inventory of 2026-10-29 lists no 5.3K mode; the synthetic 5.3K 8:7 clip stands, as WP3.21 ruled); the GUI-path figure (WP4.6's window of record, cited: 226.2 s on GX011627, +7.3..8.2 % over the in-process engine, Q1); V7 and V18 (WP4.6 / WP4.3 of record); DR-99 (test-only, load-sensitive; untouched). |
| Debt and decided items | At the accept CHARC writes: the N6 proposal to the owner (spec D106 / N6 text, the decimal figure from the GX011627 cold median and the GX011625 sustained row, the GUI-path margin stated); AD-21 CLOSED note (N6 set); the plan section 7 completion pointer for V15 / V16; DR-72 CLOSED; DR-70 note (the analysis-bound share re-read); an estimate-margin row if any row's ratio exceeds 2x or any owner mode would fall back falsely; a D111 row if the fallback leg fails to engage or its output breaches AD-11. |
| Done | Plan 4.5. ruff, format, mypy strict clean; the two new tests green on their legs; collection identity holds; every leg of the run plan has a record under `work/wp5.2/` and a row in the report with the window id; Reviewer A converged; Reviewer B EXECUTED the breach test and the holder; the two-leg gate green; the report's figures match the records (the orchestrator re-reads three cells at random). |

## Why

D106 (v0.5.4, Gate 1 option C) set an interim N6 of about 25 min/min at 4K and said the figure is re-set from the
WP5.2 re-measure after the optimisation package. WP3.21 (`7e228fb`) measured 9.57-9.92 min/min cold on GX011627 and
9.58 sustained on GX011625, 36.65 on the synthetic 5.3K 8:7 clip (best effort), N4 held on every row. Since then
the shipped build changed in ways that touch the rate: WP4.3's application wiring, WP4.6's spawned export worker
(the GUI path; +7.3..8.2 % wall, of record), WP-T7's gate flags (no runtime effect), the WP4.4 MOV input and the
EXIF rewriter (photo path). V16 therefore needs the same row set on the build that ships, so the N6 figure the
owner sets rests on today's code and the chain WP1.2b -> WP3.14 -> WP3.21 -> WP5.2 stays readable.

V15 has three halves. The video half was measured by WP3.21 on the synthetic 5.3K clip (7,753 MiB tree RSS,
7,901 MiB device-wide peak of 8,188) and must be re-taken on the shipped build. The photo half was measured by
WP3.6P on the owner's largest photo (IMG_6690, 24.5 MP, 16-bit: GPU peak 4.11 GB, tree RSS 1.93 GB; forced CPU
RSS 3.14 GB) and is CITED here, with one addition for the "largest SUPPORTED photo" (Q2). The fallback half has
NEVER been witnessed for real: every record so far either fitted (WP1.2b: estimate 1,982 MiB under free) or forced
the CPU (`--force-cpu`, WP3.6P 5d-cpu). D111 says the fallback engages when the frame is ESTIMATED not to fit;
`core/backend.py:1004-1043` reads the card's free memory on every call and chooses the CPU when the estimate is not
strictly below it. A holder process that occupies the card makes that branch real on a true export.

The admission estimate is conservative by design (AD-1 base plus the FFT bound): 1.16x the pool peak at WP1.2b,
1.5x the device-wide peak on the 24.5 MP photo at WP3.6P. WP5.2 records the ratio on every row so the v2 tuning
question has its numbers; it tunes nothing.

## Task ladder (the cell builds exactly these; depth read at every yield)

**T1 Read and map.** This brief; `tools/export_bench.py` (docstring, `V16_PLAN`, `memory_check`, the record
schema, the exit statuses); `tools/photo_verify.py memory` (the 5d legs' form); `tools/video_io_bench.py`
`Telemetry`; `core/backend.py:1004-1043` and `core/memory.py` (the estimate and the choice); `docs/reports/
wp3.21-optimisation.md` (the table of record, its (a)-(c) notes); `docs/reports/wp3.6p-real-photos.md` (the 5d
table); `docs/reports/wp4.6-export-process.md` (the GUI-path wall). Round-0 note: the record keys the report will
cite, the exact `V16_PLAN` legs and their expected durations, the holder design, any dispute. `uv sync`.

**T2 DR-72 fix, RED first.** `tests/test_export_bench_breach.py`: a planted record with `memory_check.passes ==
false` (through the bench's own record-reading seam; no clip, no GPU) makes the `v16` plan STOP after that leg and
exit 3; a passing record continues. Then the fix in `tools/export_bench.py` (exit status 3 documented beside 0 / 1 /
2; the plan stops; the records before it are kept, as today).

**T3 `tools/device_hold.py`, RED first.** `tests/test_device_hold.py` (`gpu`): start the holder for 256 MiB with a
stop file; the backend's `free_device_bytes()` read from the test process drops by at least 256 MiB while it holds;
touching the stop file releases within 2 s; the free figure recovers. The holder: one CuPy allocation of `--mib`
(rounded to the card's granularity), a loop on the stop file / timeout, release on `finally`, exit 0; prints
`held_bytes`, `free_before`, `free_after` as one JSON line. It never touches the footage or the repository.

**T4 Run plan (RUN REQUESTS; every leg EXCLUSIVE at the orchestrator's seat; records under `work/wp5.2/`).**
The orchestrator runs the legs in this order inside windows opened and closed to CHARC; the cell's next turn reads
the records. One heavy job at a time; a leg that fails is re-run once in a later window before it is a STOP.

| Leg | Command (from the repo root, Git Bash, `PYTEST_ADDOPTS` unset) | Proves | Expected |
|---|---|---|---|
| R1 V16 plan | `uv run python tools/export_bench.py v16 --out work/wp5.2/v16` (the six `V16_PLAN` legs: GX011627 x 3 cold, x 1 warm, x 1 ancuti2018, x 1 libx265; synthetic 5.3K 8:7 x 1; GX011625 x 1 sustained, LAST) | V16 at the shipped defaults; the 5.3K memory row (V15 video); the memory check on every GPU row; DR-72's stop | GX011627 cold about 9.6-10 min/min; GX011625 about 9.6; 5.3K about 37 (best effort); N4 and the device limit held |
| R2 fallback witness | (a) `uv run python tools/device_hold.py --mib <free_before minus 1,500> --stop-file work/wp5.2/hold.stop --timeout-s 3600 &` (leaves about 1.5 GiB free, under the 4K c3 estimate of about 2 GiB); (b) `uv run python tools/headless_export.py <GX011627 trim or the 30 s clip of Q3> --out work/wp5.2/fallback --record work/wp5.2/fallback-cpu.json`; (c) touch the stop file; (d) the same export with the card free, `--record work/wp5.2/fallback-gpu.json`; (e) decode both outputs' first 30 frames (the WP5.1 support helpers) and compare | D111: the record's device reason reads `CPU: estimate N MiB exceeds free M MiB`, the export completes, exit 0; the GPU run reads `GPU`; frames within AD-11 (max 2e-3, mean 2e-4) after the encoder is removed from the comparison per AD-11's clarification (or, through the encoder, within the WP5.1 post-encode characterisation 3.5/255 mean, stated as such) | First real fallback witness; CPU rate recorded (not a target) |
| R3 largest supported photo (Q2) | `uv run python tools/photo_verify.py memory` on a synthetic 48 MP (8064 x 6048) 16-bit HEIC or PNG made by the WP3.6P generator recipe, default device then `--force-cpu`, `--exclusive` | V15 photo half at the supported ceiling; the estimate ratio at 48 MP | RSS under 16 GB both legs; GPU: fits (estimate about 12 GB?) or falls back: EITHER is a result, recorded |
| R4 owner photo | CITED from WP3.6P 5d (no re-run): IMG_6690 24.5 MP 16-bit GPU 4.11 GB device / 1.93 GB RSS, CPU 3.14 GB RSS | V15 photo half on the owner's largest | cited |

**T5 Report** `docs/reports/wp5.2-performance-memory.md`: (1) the V16 table in WP3.21's exact column set with a
third column pair `WP3.21 -> WP5.2`; (2) the N6 section: the GX011627 cold median, the GX011625 sustained figure,
the GUI-path margin (WP4.6, cited), the 5.3K best-effort row, and ONE sentence of fact for CHARC's proposal (no
recommendation from the cell; the owner rules); (3) the V15 table: 5.3K video, 48 MP synthetic, 24.5 MP owner
(cited), each with tree RSS, device-wide peak, the estimate and the ratio; (4) the fallback witness with both
reasons quoted from the records and the comparison figures; (5) the estimate-ratio column read across every row
with the conservative-by-design note; (6) Limits: sampling cadence, strays, the shared laptop, the synthetic 5.3K
and 48 MP inputs, the GUI path cited not re-run; (7) DR-70's share re-read; (8) the ledger pointer. Every figure
cites its record file and window id.

**T6 Nets and gate.** Reviewer A; Reviewer B EXECUTING (the breach test, the holder test, one record re-read).
The two-leg gate with `--timeout`; no `fullclip` leg (no fullclip-marked test is added; the full-clip runs are
the RUN REQUESTS above).

## Questions (recommended answers first; a round-0 dispute with evidence is a STOP)

- **Q1 GUI path.** Recommended: CITE WP4.6's window of record (226.2 s on GX011627, +7.3..8.2 % over the in-process
  engine) as the GUI-path margin; do not build a GUI-path instrument here. The N6 proposal states the in-process
  figure and the margin. Alternative: a one-leg driver through the spawned worker (the WP4.6 window driver is in
  the evidence folder, uncommitted): more wall, no new information.
- **Q2 The largest SUPPORTED photo.** The spec's photo-resolution input (24 MP or 48 MP) is still open for the owner
  (CHARC carries it in the Phase 5 bundle). Recommended: one synthetic 48 MP leg (R3) so the ceiling has a figure
  either way; the owner's 24.5 MP figure cited. Alternative: 24.5 MP only, and the 48 MP question stays open.
- **Q3 The fallback leg's clip.** A 4K CPU export of the whole GX011627 (about 5,900 frames at a CPU rate of seconds
  per frame) would take hours. Recommended: the session trim is too short for a steady state; use the FIRST 30 s of
  GX011627 as a stream-copied cut under `work/wp5.2/` (the WP5.1 support helper's form), never the footage folder;
  about 900 frames on the CPU, about 20 min. Alternative: the 90-frame trim (steady state not reached; D111 still
  witnessed).
- **Q4 libx265 leg.** Recommended: KEEP it in the plan (the CPU-encoder fallback characterisation, not a target), as
  WP3.21 did, so the chain stays comparable. Alternative: drop it to save about 7 min.

## Yields and depth

Round 0 after T1; T2 and T3 together (RED then GREEN); a yield before each RUN REQUEST set and after each
read-back; the report; the nets. Codex evaluate at about 200K, STOP near 250K; a fresh session from the ledger.

## Orchestrator dispatch fill (generation 34, 2026-11-02; for CHARC to finalise)

- **Lane (paces 2026-11-02 10:12Z):** Codex 17 % / pace 0.238 (resets 2026-11-04 10:07Z); Claude 1 % / pace 8.20 (the week reset at 10:00Z; pace is inflated at 0.1 % elapsed). CODEX stands (task fit: committed instruments run to a plan, one small tool, one tool fix; no frozen interface). The "92 % rule" in the Lane row is VOID for this week until Claude reaches 92 % again (CHARC `32d39a5c`); Reviewer A and B are Claude passes at the orchestrator's seat as usual.
- **Base:** main at dispatch, at or after `69050ead` (WP5.3's DR-112 witness read-back: it carries the DR-99 (b) and B-F4 `slow` markers, so WP5.2's gate starts from the moved nodes). Worktree `.worktrees/wp5.2`, branch `wp5.2`. Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp5.2\`.
- **Order against WP-DR113 (CHARC `35512da5`, `645887d5`):** WP-DR113 (Codex, tools-only, V4 PCM reading) is commissioned FIRST and its gate runs while no window is open. WP5.2's T1-T3 (map, DR-72 RED/GREEN, the holder RED/GREEN; Codex turns, light runs only) MAY run beside WP-DR113's Codex turns. The T4 EXCLUSIVE windows open only when NOTHING of WP-DR113 runs: no gate leg, no Claude reviewer pass, no Codex turn that runs tests, no V4 witness. If WP-DR113 is still in review when T1-T3 finish, its gate goes first and the windows follow it.
- **Yields (as the brief's "Yields and depth", made concrete):** turn 1 = T1 round 0 (the record keys, the exact `V16_PLAN` legs with expected durations, the holder design, any Q1-Q4 dispute with evidence = STOP) and YIELD; turn 2 = T2 + T3 RED, committed; turn 3 = GREEN, light runs, ledger, YIELD for Reviewer A round 1 at the orchestrator's seat (on the TOOL code, before any window, so a defect in `export_bench.py`'s stop or the holder is found before it costs a window); adjudication; then T4: one RUN REQUEST set per window (R1 = window 1; R2 + R3 = window 2 unless the board allows one), each followed by a read-back turn; turn N = the report (T5); Reviewer B (EXECUTING, T6); the gate. Codex depth: evaluate at about 200K, STOP near 250K, a fresh session from the ledger.
- **Windows:** each opened and closed to CHARC with `df -h /c` (STOP below 25 GB free before a window: the V16 plan's outputs are full 4K clips; `--keep` only for R2's two outputs, deleted after the comparison), the card's clocks / temperature (the bench records them), and the strays listed. Window ids `W52-1`, `W52-2`, ... in every record name and report row.
- **GATE_CHECKS (the orchestrator's, on the final candidate rebased onto main):** `docs/review-gate-clearwater.md` Part 2 as written at the base: ruff, format, mypy; the TWO-leg gate with WP-T7's `--timeout 600 / 1200` and `> log 2>&1`, the stall watch, fresh basetemps under `work/`, collection identity (parallel + serial + fullclip = all), each leg's `-rs` skips compared with the last accepted gate's (gate d112: parallel 1, serial 11), the DR-99 (b) and B-F4 nodes now in the serial leg (collect proves it), DR-99 (a) handled per CHARC `fbbab0bf`; `tests/test_export_bench_breach.py` in the parallel leg under 5 s and `tests/test_device_hold.py` in the serial leg (`gpu`); no `fullclip` leg (no fullclip-marked test added and no fullclip node reads the changed tools; round 0 confirms it with the consumer list of `tools/export_bench.py`); no EXCLUSIVE window open during any leg; 0 CR per changed file; `git patch-id` before and after the rebase.
