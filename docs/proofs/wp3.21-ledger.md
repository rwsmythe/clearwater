# WP3.21 ledger -- optimisation package

Cell `implementer-opus-high` (Claude lane), worktree `.worktrees/wp3.21`, branch `wp3.21`, base main
`d1e4537`. Brief `docs/briefs/wp3.21-brief.md` (FINAL, CHARC `b16da9c25ddfb8c8`). Reviewer A: Codex
`gpt-6.1-sol` / high, WSL, evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.21\rN\`.

## Depth readings (dispatcher-read, `scripts/cell_depth.py`)

| Yield | Moment | Depth |
|---|---|---|
| 1 | task 1 instrument + task 2 oracle built; WINDOW REQUEST | (dispatcher fills) |
| 1b | per-step GPU occupancy added; WINDOW REQUEST stands | (dispatcher fills) |
| 1 (read) | as given by the dispatcher at yield 1 | 269,898 (past the 250K evaluation point: run the window, write round 0, then re-seat) |
| 2 | round 0 yield | (dispatcher fills) |
| 2 (read) | cell 1 stood down after round 0 (re-seat) | 359,040 |
| 3 (read) | cell 2: #1 built, interim-1 WINDOW REQUEST (granted) | 287,974 (past the evaluation point: run the window, record, hand over to cell 3) |
| 3 (last) | cell 2 stood down after interim 1 (re-seat to cell 3) | 310,465 |
| 4 | cell 3: Q-R6 and #2 built; WINDOW REQUEST for #2's GX011627 oracle leg | (dispatcher fills) |
| 4 (read) | as given at the grant | 192,330 |
| 5 | cell 3: STOP, frame rule 5 (CuPy outside core) on #2 and the #3 draft | (dispatcher fills) |
| 5 (read) | cell 3 stood down after the STOP (re-seat to cell 4) | 251,077 |
| 6 | cell 4: #2 reworked under AD-29; WINDOW REQUEST for the GX011627 + synthetic 4K oracle legs | (dispatcher fills) |
| 6 (read) | as given at the grant | 148,982 |
| 7 | cell 4: STOP, AD-29 item 1 "the block sums with their quantise" (where #3's quantise lives) | (dispatcher fills) |
| 7 (read) | as given with the ruling (a) | 164,381 |
| 8 | cell 4: #3 built; WINDOW REQUEST for interim 2 (#1+#2+#3, device frames ON) | (dispatcher fills) |
| 8 (read) | as given at the interim-2 grant | 236,806 (the dispatcher: hand over after the window) |
| 9 | cell 4 stands down after interim 2; RESUME HERE (cell 5) | (dispatcher fills) |
| 9 (read) | cell 4's last reading at stand-down (given to cell 5) | 236,806 at yield 8; 257,383 final |
| 10 | cell 5: micro-timing instrument built; WINDOW REQUEST | (dispatcher fills) |
| 10 (read) | as given at the micro-timing grant | 87,298 |
| 11 | cell 5: WINDOW RELEASED (micro-timing); task 6 build-or-yield | (dispatcher fills) |
| 11 (read) | as given at the release acknowledgement (HOLD for CHARC on task 6) | 111,973 |
| 12 | cell 5: Q-R7 built in the hold | (dispatcher fills) |
| 12 (read) | as given with the task 6 GO relay | 141,332 |
| 13 | cell 5: STOP, a correction to the micro-timing's 5.3K memory figure before the task 6 build | (dispatcher fills) |

## RESUME HERE (cell 5, after cell 4's interim 2)

**State at hand-over** (cell 4 stood down after yield 9 on the dispatcher's instruction; depth at
yield 8 was 236,806): branch `wp3.21` on base `d1e4537`, NO rebase, worktree CLEAN at the ledger
head. Product commits, in order: #1 overlap `333ad3f` (interim 1); Q-R6 `82c6d38`; #2 `3da1e6f`
then its AD-29 rework `0cc11cd`; #3 `05ee507`; `export_bench --device-frames` `6e504fe`. Debt
CLOSED at the touch: the engine `import logging` (WP3.11 style) and DR-63 (`encode.py`
close/abort under `_phase_lock`). `color/samples.py` and `src/clearwater/interfaces/` equal
`d1e4537`.

**Oracle and interim record so far (every leg TIER1, max abs 0):** WP2.3 x10 for #1, #2 (AD-29)
and #3 (`--device-frames`, GPU and `--force-cpu` legs); GX011627 + synthetic 4K for #2 under
AD-29 (H9, H10); interim 2 (H11-H14): 15.37 min/min, frames phase 0.501 s/frame, three oracle
legs TIER1. The WP2.3 samples are 320x180 (k = 1): they pin routing, never `block_sums`; only
the 4K legs pin it (interim 2's H12-H14 are the only end-to-end pin for k > 1, CHARC
`fc6e2e64`).

**Carried FINDINGS for task 10's report:** the slow frames recur (interim 2: indices 323, 0,
387 at 0.965 / 0.955 / 0.947 s, median 0.483), so the report places them from the per-frame
record; interim 1's single 2.858 s max likewise. **Memory:** the graphics peak rose +0.26 GB
over interim 1 against #2's +0.13 GB estimate; re-derive the 5.3K estimate (was about 6.9 of
8 GB before the FFT) at task 6's memory re-read; a measured peak above AD-1's estimate is a STOP.

**AD-29 as ruled and amended (binding; decisions.md on main, `589f90e`, `ce55a95`, `e8c56eb`):**

1. Device methods live on `CupyBackend` (the GPU `CoreBackend` in `core/backend.py`), NOT on
   the shared base, so the CPU backend has none (CHARC confirmed, `ce55a95`): `planes_to_rgb`,
   `rgb_to_planes`, `block_sums`, under the comment "IF-2 device extensions: NOT part of the
   frozen ABC; provided by the GPU backend; absent on the CPU backend". IF-2 and `interfaces/`
   never change.
2. One `runtime_checkable` Protocol per consumer package, same names and signatures as
   `CupyBackend`'s: `clearwater.io.video.decode.DeviceFrameBackend` (encode imports it) and
   `clearwater.analysis.proxy.AnalysisDeviceBackend`. Every satisfaction test asserts BOTH that
   `CupyBackend` satisfies it AND that `NumpyBackend` does not (present for both). No consumer
   imports `core` or `cupy`, and none reads `.xp`.
3. Host path default and fallback by structure: `FFmpegVideoSource(device_backend=None)`,
   `FFmpegVideoSink(device_backend=None)`; None or the CPU backend runs the base's path (the
   sink refuses a device label with the base's `to_host` text; `test_io_video_encode.py`
   962/1101/1211/1259 UNCHANGED). Device frames only for `hw_decode=True` (the coupling is
   ACCEPTED; the report's Limits say a CPU backend with a hardware decoder is not a supported
   combination). The tools (`export_oracle.py --device-frames`, `export_bench.py
   --device-frames`) pass `select_backend`'s result.
4. Ruling (a), UPHELD by CHARC (`e8c56eb`): `CupyBackend.block_sums(a, k)` returns float64 host
   sums or None at the exactness bound (the bound in core); `analysis/proxy.py` keeps `_divide`
   and `quantise` (single source of the AD-5 rule); None takes the host reduction with identical
   bytes: a structural choice between two exact paths, NOT a D109 fallback. #3 is tier 1 or STOP.
5. `test_core_deps`, `test_color_deps`, `test_io_video_decode_rules`, `test_analysis_deps` join
   EVERY light run (in practice every `tests/*_deps.py` and `tests/*_rules.py`).
6. CHARC's WP4.2 register row at the accept binds the product's GPU job to
   `device_backend=<the GPU backend>`, with a test.

**Remaining order (CHARC-confirmed; each heavy run in its own granted window):**

1. **The 4K direct-vs-FFT blur micro-timing (Q-R5; NOT started).** Instrument plan:
   - Purpose: set Q-R1's provisional sigma threshold (32 px, may move only UPWARD) before task 6
     is built; the 3C render blurs at `c3_kernel_fraction x short side` (default 0.05: 108 px at
     4K, 54 px at 1080p; R0.4).
   - Home: `tools/` new files outside the owned list need a grant, so the recommended home is an
     UNCOMMITTED driver `work\wp3.21\blur_microtiming.py` (development evidence; if a committed
     tool is wanted, that is a question to the dispatcher first).
   - Body: the direct path is `CupyBackend.gaussian_blur`; the FFT path is R0.4's route
     prototyped in the driver (per axis, the SAME scipy kernel `_gaussian_kernel1d(sigma, 0,
     radius)` with `radius = int(4 * sigma + 0.5)`, reflect padding including repeated
     reflection, axis 0 then axis 1, `cupyx.scipy.fft`, float32).
   - Inputs: a real 4K frame of GX011627 (decoded through `FFmpegVideoSource`, path from
     `tools/local_config.find_footage_file`) and a 5.3K 8:7 synthetic frame. Shapes `(H, W, 3)`
     and `(H, W)`. Sigma ladder 8, 16, 24, 32, 48, 54, 64, 108, 128, 270.
   - Method: warm-up 3, then the median of 20 timed by `cupy.cuda.Event` pairs, synchronised. Also
     record each pair's max abs difference, to read against the 1e-5 bound early, and the peak
     GPU memory per sigma (the FFT's padded buffers are the 5.3K watch item).
   - Output: JSON under `work\wp3.21\microtiming\`. WINDOW REQUEST with the command, about 10 min.
2. **Task 6, the FFT Gaussian, under Q-R1 as RULED (CHARC `5b05c53d`):**
   - The gate lives INSIDE `gaussian_blur` in `core/backend.py`, identical for both backends:
     the FFT only when `min(H, W) >= 1080` AND `sigma >= threshold` (32, or higher from the
     micro-timing, never lower).
   - Tests: (a) a tripwire deriving the largest proxy short side from `analysis/proxy.py`'s own
     rule (`ceil(S / (S // 540))` <= 1079) and asserting it is below 1080; (b) a planted
     analysis-sized blur bit-identical to the direct path; (c) FFT vs direct within 1e-5 at 1080p
     and 4K; plus R0.4's step edges at every border and the 5.3K check. Deterministic on repeat.
     The memory peak is re-read (the 5.3K watch item; an AD-1 breach is a STOP to CHARC).
   - Then the oracle legs within tier 2 in a window: WP2.3 light, and GX011627 + synthetic 4K.
   - Plan the next handover in the ledger BEFORE the task 6 build if the depth reading passes
     about 250K.
3. **Task 7 and Q-R7:** the tool-side analysis-end stamp in `export_bench.py` (Q-R7: the
   overlap makes `on_stage("analysis")` -> `"open"` the LEAD; task 10 reports the analysis share
   as the lead plus the export's stall time). No product hook unless ruled. The `device_frames`
   header and the run's `device_backend` are already in (`6e504fe`). DR-40 (b) is recorded as
   measured-negligible per Q8.
4. **Reviewer A:**
   - Codex `gpt-6.1-sol` / high, at the cell's seat over WSL, probe first. Copy the runner and
     prompt shape from `C:\Users\rwsmy\clearwater-review-evidence\wp3.14\r2\`.
   - Evidence in `...\wp3.21\rN\` with md5s. The banner must read `gpt-6.1-sol`; a round under
     another pin is void.
   - The prompt withholds `docs/proofs/**` (`--glob '!docs/proofs/**'`) and
     `clearwater-review-evidence`, and forbids the footage folder. WHAT TO EXAMINE is the brief's
     list.
   - END THE TURN as soon as a round's verdict is adjudicated, before remediating. Keep the
     cumulative round ledger. STOP at round 5 for approval.
5. **The two-leg suite (GATE_CHECKS):** one window per leg, from Git Bash with
   `PYTEST_ADDOPTS` unset and `QT_QPA_PLATFORM=offscreen`, waited in the FOREGROUND:
   - `uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=work/<run>-parallel`
   - `uv run pytest -q -rs -m "gpu or footage or gui or slow" --basetemp=work/<run>-serial`
   - Output to files under `work/`; a reaped run is not a result.
6. **Task 10, the V16 re-measure, LAST** (CHARC `eab16ca8`):
   - `export_bench.py v16 --device-frames --subdir wp3.21/bench` on the final commit. GX011627
     rows first, GX011625 LAST, each block its own window.
   - The record header names the configuration: device frames ON, hw_decode ON, the backend,
     the cache state.
   - An OFF row on GX011627 c3 only if it fits the same window; never extend a window for it.
   - The report says in one sentence that no product code constructs the real source yet (the
     GUI's path is the stubs' until WP4.2). The `device_backend=None` default stays.
   - The table puts every row beside its baseline row.
7. **Report** `docs/reports/wp3.21-optimisation.md`, then the return report (under about 70
   lines, by SendMessage to the dispatcher).

**Standing rules (all binding):**

- Worktree `C:\Users\rwsmy\clearwater\.worktrees\wp3.21` only, by absolute paths or `git -C`.
  Never `cd` into the main tree, never edit it. Never `git stash`, `git clean -x`, merge or rebase.
- Commit by pathspec: `git -c core.autocrlf=false commit -m "...(wp3.21)..." -- <paths>`,
  conventional, with the `Co-Authored-By:` footer.
- Line endings: normalise each edited file with `sed -i 's/\r$//'` BEFORE scripted edits (the
  checkout is CRLF; the Edit tool writes CRLF), and prove 0 CR per committed blob.
- A sed over a glob can mark untouched CRLF files as modified (V30): restore them with
  `git checkout --`.
- Multi-line Python edits: write them to a scratchpad file and run that (bash heredocs holding
  some ledger text fail to parse).
- Footage `C:\Users\rwsmy\clearwater-footage\` is READ-ONLY, reached only through
  `tools/local_config.find_footage_file`; nothing footage-derived is committed. Never decode
  `gpmd`; never read or log a location tag.
- Nothing under `src/clearwater/interfaces/` changes. Edit only the brief's files plus the Q-R2
  grants (`io/video/decode.py`, `io/video/encode.py`); `color/samples.py` stays at base.
- No new dependency. No OS-specific code.
- Every heavy run is EXCLUSIVE and needs the dispatcher's grant: a WINDOW REQUEST with exact
  commands, durations and evidence paths; at least 5 GB free; one job at a time; then
  `WINDOW RELEASED: <summary>` with EXIT / COMPARE-EXIT and times. Oracle references are at
  `work\wp3.21\oracle\ref-*-a` (and `-b`). Wait in the FOREGROUND, one stage per Bash call.
- A non-TIER1 result in a window is a STOP (D109). Outside the tolerance, a needed change to an
  unowned file, a dependency, or an AD-1 breach is a STOP. A choice the brief or the rulings leave
  open is a STOP, with the recommended answer first.
- The light set always includes every `*_deps.py` / `*_rules.py`. Logs go to files; grep the
  summaries.
- Depth: the dispatcher reads `scripts/cell_depth.py` at each yield; record it. About 250K is
  the evaluation point; about 400K is a STOP at the step boundary with RESUME HERE.

## Re-seat: cell 5 (2026-10-28)

Cell 5 (`implementer-opus-high`) re-seats cell 4, which stood down at depth 236,806 (yield 8;
257,383 final) after #2 and #3 under AD-29 and interim 2. Branch `wp3.21` at `07778d2` on base
`d1e4537`, no rebase. Order: this record; the 4K direct-vs-FFT blur micro-timing (window); task 6
only on its reading; task 7 and Q-R7; Reviewer A; the two-leg suite; task 10 LAST.

### CHARC's interim-2 readings (`b4c143d7`, relayed by the orchestrator at the cell-5 dispatch)

1. The report records the frames-phase trio: 0.714 serial, 0.778 interim 1, 0.501 interim 2. The
   #2 / #3 split comes from task 10's OFF row if it fits; otherwise it stays unattributed.
2. The recurring ~0.96 s frames at indices 0, 323 and 387 (median 0.483) are a FINDING for task
   10's report to place with evidence: decoder seek or GOP boundary, sink write, cache flush, or
   GC. Frame 0 is the first-frame cost. 323 and 387 are 64 apart, so check them against the
   clip's GOP length (ffprobe keyframe flags, read-only) before guessing. No fix in this package
   unless the cause is in an owned file and the fix is one line.
3. +0.26 GB at 4K is inside AD-1. The report states the measured figure; the 5.3K row re-reads
   the estimate.
4. Task 6 goes ahead ONLY on the micro-timing's reading. The instrument must show the blur's share
   of render (now about 0.35 s/frame of the 0.501) BEFORE any FFT code is written. If the share is
   too small for the FFT to move the end-to-end figure by more than the oracle's tier-2 cost is
   worth, that is a YIELD to the dispatcher (taken to CHARC), not an automatic build.

### Q-R5 micro-timing (EXCLUSIVE window 2026-10-28, OPEN 08:43Z; development evidence)

Driver `work\wp3.21\blur_microtiming.py` (uncommitted; `--selftest` worst 6.0e-7 on small arrays
incl. repeated reflection). GPU events, warm-up 3, median of 20. Run 1 (`logs\microtiming-1.log`,
GX011627 frame 0, 4K) finished the render and 4K rows, then STOPPED by the cell in the 5.3K rows:
the instrument's cuFFT plan cache (one plan set per ladder shape, never freed) filled the card
(7,839 of 8,188 MiB) and paged (2-D medians of 4-9 s); its JSON was not written, the 4K figures
are the log's. Run 2 (`--only-53k`, plan cache and pool cleared per row; JSON
`microtiming\blur-microtiming-53k-20261028T090504Z.json`, 321 s, card 1.8 GB between rows).

- **Blur share of c3 render at 4K:** render 0.500 s (events); with the per-call wrapper 0.504 s,
  of which blur 0.360 s = **71.4 %**. Calls per frame: mask (H,W) sigma 21.6 0.020 s; Cb and Cr
  (H,W) sigma 108 0.099 + 0.100 s; sharpen (H,W,3) 10.8 0.032 s; Laplacian (H,W) 2.16 x2 0.003 s;
  saliency Lab (H,W,3) 6.48 x2 0.020 s.
- **Under the Q-R1 gate (min(H,W) >= 1080, sigma >= 32) only Cb and Cr switch:** direct 0.198 s
  -> per-axis FFT 0.0185 s, **saving 0.180 s/frame** (render 0.50 -> about 0.32). If the frames
  phase stays render-bound: 0.501 -> about 0.32 s/frame, whole job about 15.4 -> 10-11 min/min
  (projection, not a figure).
- **Threshold:** FFT wins from sigma 16 (RGB) / 8-24 (one plane) at 4K; 32 stays (moving it up
  only loses; the 21.6 mask call stays direct by the ruling's floor).
- **Bound:** max abs on [0, 1] data 2.2-3.1e-7 on the 4K render calls, <= 2.68e-6 on the 4K
  ladder, <= 2.92e-6 at 5.3K sigma 270 (per-axis and 2-D alike); every FFT row deterministic on
  repeat. (The Lab saliency call, below the gate, shows 6.1e-5 absolute on magnitudes ~100.)
- **5.3K memory (run 2):** one plane (the c3 Cb/Cr shape) sigma 232-270: peak +0.53-0.56 GiB per
  call over the input, of which the cached cuFFT plans hold 0.45-0.54 GiB AFTER the call; RGB
  sigma 270 +1.9 GiB (plans 1.6 GiB). R0.3 budgeted 0.3-0.5 GB transient: the plan workspace makes
  it about 0.55 GB and PERSISTENT while the plan cache holds it.

### Release and HOLD (orchestrator, after yield 11)

- Reported as CHARC `c07f38f9` asked: the gate-eligible calls (Cb, Cr) are **39.3 %** of the 4K
  render (0.198 of 0.504 s; all blur 71.4 %); projected **about 10.0 min/min at 4K against
  interim 2's 15.37** if the whole 0.180 s/frame reaches the critical path (10-11 if part of
  the frames phase is bound elsewhere). A projection, not a figure.
- Recommendation BUILD (gate 32, per-axis route); the orchestrator concurred and forwarded it.
  OPEN question **Q-C5a**, the cuFFT plan-cache policy: (a) RECOMMENDED, CuPy's default cache,
  counted in task 6's 5.3K memory re-read (an AD-1 breach a STOP with Q9's fallback); (b) free
  the plans per blur; (c) cap the cache's memsize (process-wide). Plus a maximum-parameter 5.3K
  row for the memory re-read (raised fractions can route RGB calls through the FFT, about
  +1.9 GiB at 5.3K). HOLD: no FFT product code until CHARC's go.

### Q-R7, as built in the hold (cell 5, `83349d7`)

- `tools/export_bench.py` `_OverlapStamps`: for the job's call only, wraps
  `AnalysisEngine.analysis_job` (stamps when the returned job returns, on the analysis thread)
  and `AnalysisEngine.smoothed_record` (times each frame-loop read: the wait for a final record
  plus the read, an upper bound on the stall) on the CLASS, restored in `finally`. No product
  hook. Record keys: `lead_s` (= the `analysis` phase), `analysis_end_s`, `record_reads`,
  `record_wait_s`, `record_wait_max_s`, `analysis_share_overlapped` ((lead + stall) / wall);
  `analysis_share` kept (now the lead's share). The row line adds "lead + stall".
- Tests (`tests/test_wp321_bench.py`, +4): a CPU run on the WP2.3 sample records the stamps
  (45 reads, the end inside the job, the share by its formula) and restores both methods; a
  fake clock pins the stall and end arithmetic; the methods are restored when the block raises;
  no analysis gives no end stamp. Light set (these + `test_export_bench.py` + every
  `*_deps.py` / `*_rules.py`): 102 passed. ruff, format, mypy (138 files) clean.
- Verification loop: suspected (1) the class patch leaking past the run -> pinned by two tests;
  (2) the read time counting the read itself -> documented as an upper bound, not fixed; (3)
  `prime_cache` (warm runs) stamped too -> rejected, the patch covers the job call only. Nothing
  new on a second pass.

### CHARC `8e103622` (relayed with the task 6 GO): TASK 6 GO and Q-C5a RULED

- **Task 6 GO.** Q-R1's gate exactly as ruled (min(H, W) >= 1080 AND sigma >= 32, inside
  `core/backend.py`, identical for both backends); the per-axis route; the 21.6 mask blur stays
  direct; the 2-D variant recorded, NOT built. Expected oracle: tier 2 on 1080p and 4K renders,
  tier 1 everywhere else (analysis, records, proxies); anything outside it a STOP.
- **Q-C5a (a), with two conditions.** (1) Job-boundary release: `CupyBackend` gains ONE method
  clearing the cuFFT plan cache and the pool's free blocks; `jobs/export.py` calls it at the END
  of every export job (success, failure, cancel) in the existing `finally`, never per frame;
  tested on the cancel and failure paths. (2) The plans are counted: the measured persistent plan
  figure per shape folds into `memory_estimate_bytes` for a GPU job whose clip meets the gate,
  beside the transient; the 5.3K re-read reports persistent and transient separately, at the
  default parameters.
- **Maximum-parameter 5.3K row: YES.** If it breaches the card, the gate ALSO keys on the
  PROJECTED plan-plus-buffer bytes for (H, W, sigma) against a FIXED budget constant in core
  (never live free memory); a call over the projection runs direct; the report states the
  constant and the pairs it excludes. A breach at DEFAULT parameters at 5.3K is a STOP to CHARC.
- **Estimate:** about 7.3 of 8 GB at 5.3K default is inside AD-1 on paper; task 10's 5.3K row is
  the measurement of record with the plans counted; a measured peak above AD-1's estimate is a
  STOP with direct-above-4K ready in the deterministic form above.

### STOP (cell 5, yield 13): the micro-timing's 5.3K memory figure was misread

- **The error.** The release said "+0.53-0.56 GiB per call, of which the cached plans hold
  0.45-0.54 GiB". The driver's `peak_extra_bytes` is taken AFTER the warm-up, when the plans
  already sit in the pool's used bytes, so it EXCLUDES them: the plans are IN ADDITION. One plane
  at 5.3K sigma 232-270 costs about 0.55 GiB transient PLUS about 0.5 GiB persistent plans, about
  1.05 GiB, not 0.55. Re-checked light at 1080p and 1440p (plans retained after the call
  20-129 MiB, transient 35-71 MiB, separate). The 5.3K default estimate becomes about 6.0 +
  0.78 + 0.55 + 0.5 = **about 7.8 of 8.0 GiB** (was 7.3).
- **Plan size is not a clean function of the shape** (1440x2560: 129 MiB at sigma 32, 83 at
  108; cuFFT's algorithm depends on the length), so "the measured figure per shape" cannot be
  folded by a formula without a table or a cuFFT size query.
- **Light prototype, chunked per-axis route** (the same kernel, padding and arithmetic per column
  or row; the transform over fixed batches of 512 lines): at 1440x2560 sigma 54 / 108, 2.68 /
  2.69 ms against 2.60 / 3.01 unchunked (direct 17.2 / 34.5); plans 36 / 33 MiB against 106 /
  83; peak including plans 84 MiB against 170 / 153; max abs identical (9.5e-7 / 1.25e-6).
  Chunking bounds both the plans and the transient by the batch, independent of the width.

## Re-seat: cell 2 (2026-10-28), rulings since round 0

Cell 2 re-seats cell 1 (last depth 359,040) on the same branch, no rebase. Rulings relayed by the
dispatcher (orchestrator generation 14):

- **Q-c (CHARC `a2ef1f64`, main `d3cd663`): RULED.** The c3 composed lead is 60 frames, +1 for
  at_end, DERIVED at run time from the stage graph. The planted test is a lead short by ONE at
  the derived bound.
- **Q-R2 (orchestrator): GRANTED** `src/clearwater/io/video/decode.py`,
  `src/clearwater/io/video/encode.py`, `src/clearwater/color/samples.py`, for #2 and #3 only, on
  conditions: IF-1 and IF-5 unchanged; `FFmpegVideoSource`'s device-frame mode opt-in at
  construction and off by default; the sink still refuses a `"cuda:0"` label on NumPy pixels and
  accepts only a real device array, so `tests/test_io_video_encode.py` 962, 1101, 1211, 1259 stay
  UNCHANGED (if one cannot, STOP); DR-63 closes at the `encode.py` touch; the `force_cpu` path
  gives the base's output (tier 1 on the WP2.3 CPU references); #2 and #3 land only AFTER #1 and
  its interim window.
- **Q-R3: ACCEPTED.** The analysis thread does not call `Progress.report`; its counts fold into
  the export thread's reports.
- **Q-R4: ACCEPTED.** "A planted unbounded queue" reads as "each thread holds at most one decoded
  frame, plus the watermark". A second held frame, or a watermark past its bound, fails by name.
- **Q-R5: ACCEPTED in principle.** One interim window after #1 and one after #2+#3 (each a
  GX011627 cold c3 export, about 12 min), plus a 4K direct-vs-FFT blur micro-timing; each
  requested separately.
- **Q-R1 (the FFT gate): OPEN with CHARC.** Task 6 does not start until the ruling is relayed.
  Superseded below (CHARC `5b05c53d`).

### CHARC rulings `5b05c53d` (relayed by the orchestrator after yield 3)

- **Q-R2..Q-R5: CONCURRED**, with one addition to Q-R2: before #3 (the device block mean) lands
  on the device-frame conversions, the oracle must exercise those conversions on GX011627, in a
  granted window.
- **Q-R1: RULED; task 6 unblocked** (still after #1-#3 and the micro-timing):
  - the FFT gate lives inside the IF-2 implementation in `src/clearwater/core/backend.py`,
    identically for both backends;
  - the FFT only when `min(H, W) >= 1080` AND `sigma >= 32` px; the sigma threshold is
    PROVISIONAL until the 4K micro-timing and may move only upward, never below 32;
  - required tests: (a) a tripwire deriving the largest possible proxy short side from
    `analysis/proxy.py`'s own rule and asserting it is below the 1080 gate; (b) a planted
    analysis-sized blur bit-identical to the direct path; (c) FFT against direct within 1e-5 at
    1080p and at 4K.
- **Recipe rule (main `3df4206`):** a granted heavy run waits in the FOREGROUND; never go idle on
  a background completion notice.

## Task 4 (#1): the overlap, as built (cell 2)

- **Engine** (`analysis/engine.py`): `analysis_job(stream=True)` (an engine's first job only;
  `set_parameters` then refused). The decode pass (and, for a complete cache entry, a per-frame
  first-stage pass over the stored proxies) calls `_advance` every `STREAM_STEP` = 16 first-stage
  records or 1/64 of the axis, whichever is more (the store's `smooth_at` copies the whole stage,
  so this keeps the copies O(n log n)). `_advance` finds, stage by stage, the last output whose
  `reach` ends on a record that is in and, on a decoded prefix, not on its last frame
  (`_usable_end`, the at_end margin); it measures the next stage up to there and smooths. It
  publishes `(ticks, raw, whole, final, state)` under a `Condition`. `_job` publishes
  `complete` after `_drive`, or `stopped` BEFORE `_unload` clears the store. The tail (the last
  ~61 frames) runs in the unchanged `_run_stages`, whose `_smooth_stage` starts after the
  streamed outputs; `mark_complete` stays where it was (V17).
- **The guard** is independent of the stream's derivation: a streamed `smoothed_record` waits
  until `final` covers the frame (or `complete`), then checks `composed_reach` (the stage chain
  composed from `(i, i)`) against `_usable_end` and raises `RenderBeforeFinalError` by name. The
  read happens under the condition, so a stopping analysis never clears the store under it.
  `lead_frames` = composed end - i + 1: 61 (c3), 91 (ancuti2018) at 30000/1001; 127 on a 60 fps
  axis (two stages); the stage chain is linear because `_measure` passes ALL earlier stages'
  smoothed records.
- **Export** (`jobs/export.py`): `_Analysis` runs the streamed job on thread `export-analysis`
  with `_Fold` as its progress (reports kept for the job's thread during the lead, dropped after;
  `cancelled()` delegates, as the watchdog does). `_analyse` starts it and waits for the LEAD (the
  first frame final, or the analysis ended; an analysis that ends inside its lead is checked
  there, exactly as before, so every clip shorter than the lead runs the WP3.14 order). The D87
  re-check and `open` follow the lead. `_write_frames` reads through the waiting
  `smoothed_record`; on `AnalysisStoppedError` it raises the analysis's own outcome via
  `_check_analysis`; after the last frame it joins A (`finish`) before `close`. A `finally` in
  `_video` stops and joins A on every path.
- **Debt (task 7, part):** the `import logging` in the decode pass's `finally` moved to a module
  `_LOG` (WP3.11 style debt CLOSES at this touch).
- **`tools/export_bench.py`:** `--subdir` (default `wp3.14/bench`, unchanged); refused outside
  the working folder (`bench_folder`, `tests/test_wp321_bench.py`).

### Existing-test constraints found in the build (all held, none edited)

- DR-28 `statistics-pts+1` plants an engine subclass whose `smoothed_record` reads the NEXT
  frame's record: this is why the wait lives INSIDE `smoothed_record` (a separate wait keyed on
  E's frame would meet a not-yet-final neighbour and fail with "no frame was written").
- DR-28 `dropped-frame` / `duplicated-frame` plant E's stream: the wait is keyed on pts, not on
  E's index, and E does not refuse repeats (the coverage checker must see them).
- The planted `_decode` rebuilds (`_bare_close_decode`, `_guard_only_while_...`) parse
  `_decode`'s source: the guarded close keeps its `if close is not None:` / `try:` shape.
- `test_planted_close_on_cancel_fails_by_name` reads the sink as `_write_frames`' 7th argument:
  the signature keeps its order (the 4th argument is now the `_Analysis` handle).

### Tests (`tests/test_wp321_overlap.py`, 21) and failing-first

21 passed. Against the base code (`git archive d1e4537` with this file, the lead functions
stubbed) **14 fail, 7 pass**: the seven that pass on the base pin invariants the serial job also
holds (cancel before start, during the lead, before commit; no thread at commit; one frame held;
the two planted-checker tests).
Light runs: `test_jobs_export.py` + engine/recompute/photo 148 passed; `test_jobs_export_video.py`
(DR-28 on 120 frames, i.e. overlapped; V11; the product-sink cancels) + oracle + bench + breakdown
79 passed (non-footage; 19 min); analysis + GUI analysis service 243 passed; bench 21 passed.

### Oracle, #1 against the base references (light: WP2.3, every frame)

Driver `work\wp3.21\oracle-overlap-wp23.sh`, log `work\wp3.21\logs\oracle-overlap-wp23.log`:
**10 of 10 TIER1** (hevc8-bt709-full, hevc10, vfr, rotated, truncated; GPU and `--force-cpu`;
digests, records, analyze calls, proxies all equal). These clips (24-45 frames) are shorter than
the lead, so they pin the streamed path's partial stage-1 measurement, not the overlap itself;
the overlap is pinned on GX011627 and the synthetic 4K clip in the interim window.

### Verification loop (cell 2)

| # | Item | Suspected | Confirmed | Rejected | Fixed |
|---|---|---|---|---|---|
| V11 | a wait keyed on E's frame breaks the DR-28 `+1` plant at the watermark boundary | yes | yes, by reading (W advances in steps; frame W-1's neighbour is not final) | - | the wait moved inside `smoothed_record` |
| V12 | a failing analysis clears the store while E reads (KeyError instead of the analysis's text) | yes | yes, by reading (`_unload` clears; E's read was outside any shared lock) | - | `stopped` published under the condition before `_unload`; the read under the same condition |
| V13 | the planted short lead first fired at frame 0 with 15 frames after it (start clipping), not at the bound | yes | yes (first run of the test) | - | the plant adds one only past the first advance; the test asserts "60 frames after it, lead 61" |
| V14 | `smooth_at` per frame copies the whole stage: O(n^2) on a long clip | yes | yes, by reading `_snapshot` | - | advance every max(16, n/64) records |
| V15 | warm per-frame `_measure` calls reset its closed-form memo (a different closed_form call multiset) | yes | yes, by reading | - | `memo` carried across calls (`_Stream.closed`) |
| V16 | lock order: E holds the condition and takes the engine and store locks | yes | - | rejected: the analysis thread never takes the condition while holding either lock (`_end_stream` and the publications run outside them) | - |

### Interim 1 (#1 only; development evidence, not of record; EXCLUSIVE window 2026-10-28)

Driver `C:\Users\rwsmy\clearwater\work\wp3.21\interim1.sh`; logs
`work\wp3.21\logs\interim1-{bench,oracle,synth4k,ancuti2018}.log`.

**Timing (H3)**, record `work\wp3.21\bench\export-bench-GX011627-20261028T061339Z.json`:

| GX011627 cold c3, hevc_nvenc, Standard | s/frame | min/min | per-frame median / p90 / max | lead (analysis -> open) | peak tree RSS | peak GPU memory |
|---|---|---|---|---|---|---|
| WP3.14 baseline | 1.061-1.065 | about 31.8 | - | whole analysis (about 31 %) | (WP3.14 report) | (WP3.14 report) |
| **#1 overlap** | **0.8100** | **24.28 (meets D106's interim 25)** | 0.7735 / 0.8208 / 2.8583 | **18.8 s** (stamps 1.61 -> 20.43 s; 3.4 % of the wall) | 3,987 MiB | 2,877.0 MiB |

Gain: -0.25 s/frame (-24 %). Wall 551.6 s; frames phase 529.95 s = 0.778 s/frame, against the
breakdown's serial frame path of 0.714: the analysis thread's host work (block_mean, conversions)
and its GPU work now share the CPU and the card with the export, about +0.06 s/frame of
contention; #3 is expected to remove most of that host share. Peak tree RSS at 433 s (two
decoders resident), inside R0.3's +0.5-0.8 GB estimate at 4K. The card was at 210 MHz in the
before/after snapshots, 51 -> 68 C.

**Oracle (H4-H6), every one TIER1 against the base reference `-a`:**

| Clip / method | Frames | Verdict | Oracle job wall, base a / b -> #1 |
|---|---|---|---|
| GX011627 c3 (23 frames kept; 1,362 analyze calls) | 681 | **TIER1** (0 differing; records, analyze calls, proxies equal) | 695.2 / 702.9 -> **587.2 s** |
| synthetic 4K c3 (120 frames, so overlapped: lead 61) | 120 | **TIER1** | 125.0 / 122.2 -> 117.6 s |
| GX011627 ancuti2018 (lead 91; 2,043 analyze calls) | 681 | **TIER1** | 513.1 / 508.6 -> 392.0 s |

### Rulings at the window grant

- **Q-R7: ACCEPTED** (orchestrator): report end-to-end s/frame plus the lead, with a tool-side
  analysis-end stamp in `export_bench` and no product hook (to build at task 10's touch of
  `export_bench.py`).
- **Q-R6:** RULED by CHARC `6acded46` (see RESUME HERE, first item). The current code runs the re-check
  after the lead.

## Re-seat: cell 3 (2026-10-28)

Cell 3 re-seats cell 2 (last depth 310,465) on the same branch at `106b29f`, no rebase. CHARC's
readings of interim 1 (`4dc2978b`, relayed by the orchestrator generation 15):

1. 24.28 min/min is INTERIM (one run, cold cache); the figures of record are task 10's, made
   LAST. 24.28 is not quoted as V16's result outside this ledger.
2. The frames phase is 0.778 s/frame overlapped against the serial path's 0.714: the analysis
   thread's contention (about 0.06 s/frame, about 8 %). #3 is the lever; the 0.714 / 0.778 pair
   is kept so task 10 can show what #3 recovered.
3. The single 2.858 s max frame (median 0.7735): task 10's report says where it fell (lead end,
   first sink write, or a decoder seek) if the per-frame record shows it. A one-off at the lead
   is expected; a recurring one is a finding.
4. Memory at interim 1: peak RSS 3,987 MiB, graphics 2,877 MiB at 4K, both inside AD-1.

Order of work (CHARC confirmed): Q-R6 as ruled; #2; a WINDOW REQUEST for #2's GX011627 oracle
leg; #3; the #2+#3 interim and the 4K blur micro-timing (separate windows); task 6; task 7 and
the Q-R7 stamp; Reviewer A; the two-leg suite (one window per leg); task 10 LAST.

### Q-R6, as built (cell 3)

- **Sized in one call:** IF-7's `ProxyCache.lookup(key).size_bytes` (the entry's pack plus
  auxiliary files; the stub sums its proxies and records). No STOP.
- `jobs/export.py`: `_Analysis.start` looks the entry up BEFORE the thread starts;
  `cache_growth_bytes(frames)` looks it up again after the lead and returns
  `ceil(grown x remaining / stored)` (grown = size growth since start, stored = pts added since
  start, remaining = clip frames - pts held); 0 for a complete entry, a missing one, or no growth.
  The re-check is `_check_space(needed + growth)`. Clip frames = `nb_frames`, else
  `ceil(duration_s x frame_rate)`. `disk_space.py` and the spec unchanged.
- The growth is added whether or not the cache shares the output's volume: IF-7 does not expose
  the cache root, and the ruling adds it unconditionally (conservative).
- `lookup` from the job's thread: a read under the store's lock; it refreshes the entry's
  last-use stamp and the eviction pin, as the engine's own `_load` lookup of the same key already
  does. No proxy or record store from E (one writer per key holds).
- Tests (`tests/test_wp321_overlap.py`, +2): the planted volume holding exactly the output's
  estimate refuses at the re-check with the growth equal to the extrapolation of the entry seen
  at the check, BEFORE the first rendered frame (no render, no `open`, thread joined, entry not
  complete, folder clean); a complete entry adds nothing. Failing-first against `104e4ab`'s
  `export.py`: the planted test fails (the job succeeded), the complete-entry test passes (an
  invariant). Light: overlap + `test_jobs_export.py` 111 passed; ruff, format, mypy clean.

## Task 5a (#2): device frame conversions, as built (cell 3)

- `color/samples.py`: `planes_to_rgb(..., xp=np)`; with CuPy it uploads the integer planes (25 MB
  at 4K 8-bit, not 99.5 MB float32) and divides on the device; `rgb_to_planes` quantises a CuPy
  array on the device (same clip, multiply, `rint`; the NaN refusal is a reduction read back as a
  bool) and downloads the planes (`asnumpy`, synchronous). The host path's arithmetic is
  unchanged. CuPy 14.2.0 / NumPy 2.5.4 promote `uint8|uint16 / float32` to float32 on both.
- `io/video/decode.py`: `FFmpegVideoSource(*, device_frames=False)` (OPT-IN, off by default).
  Device frames only for `frames(..., hw_decode=True)`; `hw_decode=False` always yields host
  frames. Device label `cuda:<getDevice()>`, as `CupyBackend` names it. IF-5 unchanged.
  **Design note for the dispatcher (not a STOP; one line to change if ruled otherwise):** IF-5's
  `frames` carries no backend, so `hw_decode` is the only per-call signal; the export and the
  engine pass `hw_decode = backend.device != "cpu"`, so a device-frame source yields device
  frames exactly when the job's backend is the GPU, and the `force_cpu` path is the base's.
- `io/video/encode.py`: `_payload` accepts a frame labelled `cuda:<n>` only when its pixels are a
  CuPy array ON device n (`_cupy_device`); a device label on host pixels is refused with the
  same `to_host` text (`test_io_video_encode.py` 962/1101/1211/1259 UNCHANGED, passing); a CuPy
  array labelled `cpu` or another device is refused; a float64 device frame is refused.
  **DR-63 CLOSED at this touch:** `close` sets `"closed"` only from `"open"` under a
  `_phase_lock` that `abort`'s transition also takes; `abort`'s docstring names the window.
- `jobs/export.py` `_write_frames`: a host frame goes to the sink on the host as before; a frame
  the source yielded on the device stays there (no `to_host` of the float32 render).
- `tools/export_oracle.py`: `--device-frames` (`Job.device_frames`), recorded with
  `sink_devices` (the `Frame.device` values the sink was given). Not a compare key.
- Not yet wired: `tools/export_bench.py` gains `--device-frames` at the #2+#3 interim's touch.
  The product has no real wiring of `FFmpegVideoSource` in `src/` (the GUI uses stubs).

Tests `tests/test_wp321_device_frames.py` (25, 22 `gpu`): exhaustive 8/10-bit codes and random
odd and 4K planes device = host bit for bit (the host buffer zeroed after the call); quantise
device = host bytes on every code's tie and its neighbours, the clip limits, +-inf and random
values; NaN and dtype refusals on the device; default off; `hw_decode=False` host with the mode
on; a device decode equals the host decode frame by frame on all five WP2.3 video samples;
the sink's device payload equals the host payload; a device-frame write closes and verifies; the
wrong-label, float64 and host-pixels refusals; DR-63 (an abort inside `close`'s window survives
it and a later abort retries; a clean close then abort keeps the output). **Failing-first**
against `82c6d38`'s three modules: 20 fail, 5 pass (invariants the base also holds: the two
wrong-label refusals, the host-pixels refusal, the device NaN/dtype refusal through NumPy's
dispatch, and the clean close).

Light runs: color, decode, encode (incl. 962/1101/1211/1259), oracle tool, jobs_export, overlap,
device frames: **554 passed, 1 skipped** (`-n 4`, `not footage and not slow`). Oracle on the
WP2.3 samples with `--device-frames`, every frame (`work\wp3.21\oracle-devframes-wp23.sh`, log
`logs\oracle-devframes-wp23.log`): **10 of 10 TIER1** (GPU legs against `ref-*-c3-gpu-a`, the
`--force-cpu` legs against `ref-*-c3-cpu-a`); `cand-devframes2-vfr-c3-gpu` records
`sink_devices ['cuda:0']`, the CPU leg `['cpu']`.

**Oracle on GX011627 (H7, H8; logs `logs\devframes-gx-{1,2}.log`), against the base `-a`:**
GX011627 c3 **TIER1** (681 frames, 0 differing; records, 1,362 analyze calls, proxies equal;
`sink_devices ['cuda:0']`; oracle job wall 408.0 s against #1's 587.2 s, development evidence
only); synthetic 4K c3 **TIER1** (120 frames; `['cuda:0']`; 89.0 s against 117.6 s). CHARC's
addition is met: the device-frame conversions are exercised on GX011627 before #3.

Memory (watch item): E's float32 frame was already uploaded per frame; new on the card are the
integer planes (transient, 25 MB at 4K, 74 MB at 5.3K 8-bit) and A's float32 frame (A was host;
99.5 MB at 4K, 296 MB at 5.3K) until #3. Estimate +0.13 GB at 4K, +0.4 GB at 5.3K over R0.3's
6.5 GB, so about 6.9 of 8 GB at 5.3K before the FFT. Host: about -0.1 GB per thread at 4K.

| # | Item | Suspected | Confirmed | Rejected | Fixed |
|---|---|---|---|---|---|
| V17 | the upload reads the decode's reused buffer after return (a corrupt next frame) | yes | - | rejected: a pageable-memory copy has consumed the buffer on return; the test zeroes the buffer after the call and the device copy holds | - |
| V18 | CuPy computes `uint / float32` in float64 then rounds (double rounding) | yes | - | rejected: result dtype float32 and every 8/10-bit code bit-equal (exhaustive test) | - |
| V19 | a non-CuPy device array (`__cuda_array_interface__`) reaches CuPy ops in the sink | yes | yes, by reading the first draft (any CUDA array accepted) | - | `_cupy_device`: CuPy arrays only, device id matched to the label |
| V20 | DR-63's check-then-set in `close` races `abort` without a lock | yes | yes, by reading | - | `_phase_lock` around both transitions |

## STOP (cell 3, yield 5): frame rule 5 forbids CuPy outside `clearwater.core`

Found while building #3. **`tests/test_core_deps.py::test_static_rule_over_src` (WP3.1, plan
8.1 frame rule 5) FAILS on the committed #2 (`3da1e6f`)**: `color/samples.py` and
`io/video/decode.py` each "imports cupy" (`importlib.import_module("cupy")`); the #3 draft adds
`analysis/proxy.py`. The rule: no module outside `core` imports `cupy`/`cupyx` or reads `.xp`
(static AST scan). Also binding: `test_color_deps` (color imports only `clearwater.color` and
`clearwater.interfaces`), `test_io_video_decode_rules` and `test_analysis_deps` (importing
`io.video` / `analysis` loads no `clearwater.core` and no `cupy`). Round 0's table (R0.1, R0.7)
did not list this rule; my #2 light run (554) did not include `test_core_deps`. Reproduction:
`uv run pytest tests/test_core_deps.py::test_static_rule_over_src` on `3da1e6f`.
The arithmetic stands (H7/H8 TIER1); the code's FORM breaks an existing test that stays
unchanged. The #3 draft (device block sums, exact; 42 device-frame tests pass) is saved
uncommitted and as `work\wp3.21\c3-draft-3-device-block-mean.patch`.

Options sent to the dispatcher (recommended first): (R) consumer-side structural protocols: core
implements device conversions on `CoreBackend` (granted `core/backend.py`); `io/video` and
`analysis` declare a local `runtime_checkable` Protocol for what they call and receive the
backend by injection (source and sink built with it, the engine's own backend), so CuPy stays in
core and no layer loads core; an interface between modules, hence CHARC's. (N) NumPy dispatch
(`like=`, `__array_function__`, the array's `.get()`): passes the scan's letter, not its intent.
(D) drop #2/#3 and revert `3da1e6f`'s product part.

### CHARC ruling `eab16ca8` (relayed after yield 4; crossed the yield-5 STOP)

- Q-device-frames RULED (a): task 10's V16 figure of record runs with `--device-frames` ON.
  The record header names the configuration (device frames ON, hw_decode ON, the backend, the
  cache state). The report says in one sentence that no product code constructs the real source
  yet (the GUI's path is the stubs' until WP4.2). The `device_frames=False` default stays.
- An OFF row on GX011627 c3 only if it fits the same task 10 window; never extend it for that.
  CHARC writes the WP4.2 register row at accept.
- The hw_decode coupling is ACCEPTED; the report's Limits states that a CPU backend with a
  hardware decoder is not a supported combination.
- A non-TIER1 in a window is a STOP (D109). Plan the handover in the ledger before the task 6
  build if the reading passes ~250K.
- The yield-5 STOP (frame rule 5) is NOT addressed by this ruling and still holds.

## Hand-over to cell 4 (SUPERSEDED by RESUME HERE (cell 5) above)

State at hand-over (cell 3 stood down at yield 5, depth 251,077): branch `wp3.21` on `d1e4537`,
no rebase; worktree CLEAN at the ledger head. Done and committed: #1 overlap (`333ad3f`,
interim 1), Q-R6 (`82c6d38`: D87 re-check after the lead adds the cache entry's extrapolated
growth), #2 (`3da1e6f`: device frame conversions, DR-63 closed, oracle `--device-frames` and
`sink_devices`). #2's GX011627 and synthetic 4K oracle legs are TIER1 (H7, H8). Task 7: the
engine `import logging` debt and DR-63 CLOSED.

**THE STOP (yield 5, reproduced by the orchestrator at its seat; posted to CHARC recommending
R).** `uv run pytest tests/test_core_deps.py::test_static_rule_over_src` FAILS on `3da1e6f`:
`color/samples.py` and `io/video/decode.py` "import cupy" (`importlib.import_module`); the #3
draft adds `analysis/proxy.py`. Plan 8.1 frame rule 5 (WP3.1): no module outside
`clearwater.core` imports `cupy`/`cupyx` or reads `.xp`. Also binding and UNCHANGED:
`test_color_deps` (color imports only `clearwater.color` / `clearwater.interfaces`),
`test_io_video_decode_rules` and `test_analysis_deps` (importing `io.video` / `analysis` loads
no `clearwater.core` and no `cupy`). IF-2 (frozen) cannot carry #2/#3: `asarray`/`to_host` are
float32 only (no integer upload, no float64 sums download, no device quantise). Do NOT start
product work until the ruling is relayed.

Options (recommended first):

- **(R) consumer-side structural Protocols, CuPy only in core.** Sketch:
  - `core/backend.py` (granted) gains device methods on `CoreBackend` (both backends, the NumPy
    one doing the host arithmetic): `planes_to_rgb(data, *, width, height, bit_depth)` (upload
    the integer planes, divide by `float32(2**n-1)` on the device), `rgb_to_planes(a, *,
    bit_depth) -> bytes` (clip, multiply, `rint` as SEPARATE kernels so no FMA contraction; NaN
    check by a reduction read back as a bool; download the planes), `block_sums(a, k)` (float64
    row-then-column sums on the device, downloaded; with the exactness check below).
  - `io/video` (decode, encode) and `analysis` each declare a small local
    `runtime_checkable` Protocol for exactly the methods they call; nobody imports core.
  - `FFmpegVideoSource(device_backend=None)` replaces `device_frames=True` (default off; device
    frames only for `hw_decode=True`, the ACCEPTED coupling); `FFmpegVideoSink(device_backend=
    None)` likewise for device frames; the tools pass `select_backend`'s result (bench, oracle;
    the oracle's `--device-frames` builds both with it). The engine uses its own injected
    backend when it satisfies the analysis Protocol.
  - `color/samples.py` REVERTS to the base (`git show d1e4537:src/clearwater/color/samples.py`).
  - IF-2 untouched, but a de facto widening of the backend contract between modules: CHARC's.
  - A NEW GX011627 oracle window for #2 before #3 lands (the code path changes).
- **(N) NumPy dispatch** (`np.asarray(planes, like=backend.asarray(...))`, NumPy calls that
  dispatch to CuPy, the array's `.get()`): passes the scan's letter, not its intent. Not
  recommended.
- **(D) drop #2/#3**: revert `3da1e6f`'s product part (keep DR-63's fix and the oracle flag if
  ruled separable); loses about 0.17 s/frame (#2) and the analysis contention (#3).

**The #3 draft** (uncommitted when the STOP landed; reverted from the tree) is at
`C:\Users\rwsmy\clearwater\work\wp3.21\c3-draft-3-device-block-mean.patch` (a `git diff`
against `3da1e6f`; files `analysis/proxy.py`, `analysis/engine.py`, `analysis/__init__.py`,
`tests/test_wp321_device_frames.py`). It passed 42 device-frame tests and 423 analysis/overlap/
export tests. What survives under (R):

- the exactness argument and check (`device_sums_are_exact`: max |v| <= 1, no NaN/inf, and
  `ceil(log2(k*k+1)) - (floor(log2(min nonzero |v|)) - 23) <= 53`; a frame that fails it is
  reduced on the host) and the row-then-column float64 sums (`sum(axis, dtype=float64)` on
  reshaped full blocks plus the edge row/column; memory 1/k of the frame in float64) MOVE into
  `CoreBackend.block_sums`;
- the host-side `_divide` split of `block_mean` (sums -> mean by counts, the same expression)
  STAYS in `proxy.py`, so the division and `quantise` are always the host's;
- `frame_pixels_for_proxy` STAYS in shape, but its CuPy test (`type(...).__module__`) becomes
  "the backend satisfies the analysis Protocol and `frame.device == backend.device`";
- the tests survive with their imports re-pointed: device block mean = host bit for bit at 4K
  (k=4), 5.3K 16:9 (k=5), 5.3K 8:7 (k=8), odd 1081x1923 (k=2, edges), 37x53 (k=1), 8 and 10
  bit; NaN/inf/>1/1e-30/1e-12 plants fall back and still equal the host; the bound's edge
  (k=5: 2**-25 admitted, 2**-26 refused); a GPU frame stays on the device, the CPU backend
  still refuses a device frame (TypeError).

**Light set, from now on:** EVERY `tests/test_*_deps.py` and `tests/test_*_rules.py` joins every
light run (`ls tests | grep -E '_(deps|rules)\.py$'`), with the touched modules' tests and the
`test_wp321_*` files.

**CHARC ruling `eab16ca8` for task 10 (binding):** the V16 figure of record runs with device
frames ON; the record header names the configuration (device frames ON, hw_decode ON, the
backend, the cache state); the report says in one sentence that no product code constructs the
real source yet (the GUI's path is the stubs' until WP4.2); an OFF row on GX011627 c3 only if it
fits the same window (never extend it); the report's Limits says a CPU backend with a hardware
decoder is not a supported combination; the device-frame default stays off. A non-TIER1 in any
window is a STOP (D109).

**Remaining order after the ruling:**

1. Implement the ruled route for #2 (under R: core methods, local Protocols, `device_backend=`,
   samples.py reverted), failing-first, the light set incl. every deps/rules test; WP2.3 oracle
   `--device-frames` legs (light), then a WINDOW for the GX011627 (+ synthetic 4K) #2 leg.
2. #3 (the device block mean) from the draft, tier 1 or STOP; light set; WP2.3 oracle.
3. Separate windows: the #2+#3 interim (GX011627 cold c3; `export_bench.py` gains the device
   option at this touch) and the 4K direct-vs-FFT blur micro-timing (Q-R5).
4. Task 6, the FFT Gaussian, under Q-R1 as RULED (CHARC `5b05c53d`): the gate inside
   `core/backend.py` for both backends; FFT only when `min(H, W) >= 1080` AND `sigma >= 32` px
   (provisional; may move only upward). Tests: (a) the proxy-size tripwire from
   `analysis/proxy.py`'s own rule, below 1080; (b) a planted analysis-sized blur bit-identical
   to the direct path; (c) FFT vs direct within 1e-5 at 1080p and 4K; plus R0.4's border and
   5.3K checks and the memory re-read (watch item: about 6.9 of 8 GB at 5.3K before the FFT).
   Plan the handover in the ledger before the task 6 build if the reading passes ~250K.
5. Task 7: the Q-R7 tool-side analysis-end stamp in `export_bench.py`; DR-40 (b) recorded
   measured-negligible per Q8.
6. Reviewer A (Codex `gpt-6.1-sol` / high, WSL, probe first, evidence
   `C:\Users\rwsmy\clearwater-review-evidence\wp3.21\rN\` with md5s, `--glob '!docs/proofs/**'`,
   the footage folder forbidden in the prompt).
7. The two-leg suite, one window per leg.
8. Task 10 LAST, per `eab16ca8`, GX011625 last, each block its own window.

### Open questions raised at yield 3 (recommended answer first)

- **Q-R6 (D87 re-check after the lead):** the second free-space check, which WP3.14 placed after
  the whole analysis "because the analysis cache may share the volume", now runs after the LEAD.
  On a clip shorter than the lead it is unchanged; on a longer one the cache goes on growing
  during the export. Recommended: accept (a disk full later is still caught and named by the
  existing D87 paths); alternative: add the remaining proxies' estimate to the re-check (needs
  an estimate `disk_space.py` does not have; not owned).
- **Q-R7 (bench stamps):** with the overlap `on_stage("analysis")` -> `"open"` is the lead, not
  the analysis. Recommended: task 10 reports the analysis share as the lead plus the export's
  stall time, and the bench gains a stamp of the analysis thread's end (the brief's "overlap
  stamps"); no product hook is added for it unless ruled.

## Re-seat: cell 4 (2026-10-28), AD-29 ruled

Cell 4 re-seats cell 3 (last depth 251,077) on the same branch at `e6d27a0`, no rebase. CHARC
RULED route (R), logged as **AD-29** (main `589f90e`; brief note "Layering tests in every light
run", main `e6f7193`):

1. Device methods on `CoreBackend` in `core/backend.py` ONLY: planes -> RGB, RGB -> planes, the
   block sums with their quantise; documented as "IF-2 device extensions: NOT part of the frozen
   ABC; provided by the GPU backend; absent on the CPU backend". IF-2 and `interfaces/` unchanged.
2. ONE `runtime_checkable` Protocol per consumer package naming exactly the methods it calls
   (same names and signatures as `CoreBackend`'s), with a test that the device `CoreBackend`
   satisfies it. No consumer imports `core`.
3. Host path default and fallback BY STRUCTURE: source and sink take `device_backend=<backend or
   None>` (replacing `device_frames=True`); `None`, or a backend not satisfying the Protocol (the
   CPU backend), runs the base's host path unchanged. The engine uses its injected backend when
   it satisfies the analysis Protocol. The tools pass `select_backend`'s result. The hw_decode
   coupling stands.
4. `color/samples.py` returns to the base (`d1e4537`).
5. #3's exactness argument lives in `core`; `analysis/proxy.py` calls through its Protocol only.
   #3 is tier 1 or STOP.
6. A NEW oracle window (GX011627 AND synthetic 4K) on the reworked #2 BEFORE #3; non-TIER1 is a
   STOP (D109).
7. `test_core_deps`, `test_color_deps`, `test_io_video_decode_rules`, `test_analysis_deps` join
   EVERY light run.
8. Task 10 per `eab16ca8`; CHARC's WP4.2 register row binds `device_backend=<the GPU backend>`.

**Rework form (cell 4's call):** follow-up commits on `3da1e6f`, not revert-and-rebuild, so
DR-63's fix, the oracle's `sink_devices` record and the device-frame tests keep their history;
the follow-up moves the CuPy code into `core`, restores `samples.py` and re-points the tests.

## Task 5a (#2) under AD-29, as built (cell 4, `0cc11cd`)

- `core/backend.py`: `CupyBackend.planes_to_rgb(data, *, width, height, bit_depth) -> Array`
  and `CupyBackend.rgb_to_planes(a, *, bit_depth) -> bytes`, under a comment block and module
  docstring paragraph naming them "IF-2 device extensions: NOT part of the frozen ABC; provided
  by the GPU backend; absent on the CPU backend". The arithmetic is cell 3's (`3da1e6f`), moved:
  the integer planes uploaded and divided by `float32(2**n-1)`; clip, multiply, `rint` as
  separate kernels, NaN by a reduction read back, planes downloaded synchronously. Refusals are
  `ValueError` (bit depth, size, NaN, non-float32 via `check_rgb`) and `TypeError` (not a CuPy
  array, or another device's). Core imports nothing from `color`.
- **Where the methods sit (reading of AD-29 items 1 and 3, not a choice):** on `CupyBackend`,
  the GPU `CoreBackend` in `core/backend.py`, NOT on the shared base class: AD-29 says "absent
  on the CPU backend" and requires the CPU backend NOT to satisfy the Protocol, which a method
  on the base would contradict (`NumpyBackend` subclasses it).
- `io/video/decode.py`: `DeviceFrameBackend`, the ONE `runtime_checkable` Protocol of
  `clearwater.io.video` (`device: str`, `planes_to_rgb`, `rgb_to_planes`; the decode calls the
  first, the sink the second). `FFmpegVideoSource(*, device_backend=None)`; device frames only
  for `hw_decode=True` AND `isinstance(backend, DeviceFrameBackend)`; else `FrameStream` is the
  base's call. `importlib`/CuPy gone from the module.
- `io/video/encode.py` imports the Protocol from `decode`. `FFmpegVideoSink(*,
  device_backend=None)` keeps the backend only if it satisfies the Protocol. `_payload`: a
  non-`cpu` label is refused with the BASE's text ("copy it to the host first
  (backend.to_host)") unless the sink has a device backend, the label equals its device and the
  pixels are not NumPy; then dtype/shape as before and `backend.rgb_to_planes`, its
  `TypeError`/`ValueError` mapped to `VideoEncodeError("frame")`. The host branch is the base's
  `rgb_to_planes(np.ascontiguousarray(...))`. DR-63's lock unchanged.
- `color/samples.py`: byte-identical to `d1e4537` (`git diff d1e4537 HEAD -- <f>` empty).
- `jobs/export.py`: unchanged by the rework (a frame the source yielded on the device stays
  there; host frames as the base).
- `tools/export_oracle.py`: probes with a plain source, then (with `--device-frames`) calls
  `select_backend(settings, H, W, method)` and builds the source and `RecordingSink` with
  `device_backend=` that result; `--force-cpu` gives the CPU backend, hence the host path by
  structure. The record keys are unchanged (`device_frames`, `sink_devices`).

Tests (`tests/test_wp321_device_frames.py`, 34 items, re-pointed and extended): the GPU backend
satisfies `DeviceFrameBackend` with `inspect.signature`-equal methods; the CPU backend has
neither method and does not satisfy it; the conversions equal the host's (every 8/10-bit code;
random odd and 4K planes with the buffer zeroed after the call; every tie and its neighbours,
the clip limits, +-inf, random); size, bit-depth, NaN, float64 and host-array refusals; source
default `None`; software decode host for none/CPU/GPU backends; a CPU-backend source with
`hw_decode=True` equals the base source frame for frame; device decode = host decode on all
five WP2.3 samples; the sink's device payload = host payload; a device write closes and
verifies; wrong-label, float64 refusals; a device label on host pixels refused with `to_host`
for none/CPU/GPU sinks; a sink with no or the CPU backend refuses a real device frame; DR-63
both tests. **Failing-first** against `e6d27a0` (cell 3's #2): 35 fail, 27 pass (of the
62-item run with the four layering tests): all 34 device-frames items fail (the DR-63 and
host-path items only on the new `device_backend=` keyword) plus
`test_core_deps.py::test_static_rule_over_src`.

Light run (`-n 4`, `not footage and not slow`): color, core, decode (incl. hw, lifecycle),
encode (incl. 962/1101/1211/1259 UNCHANGED), oracle tool, `test_jobs_export.py`,
`test_wp321_*`, EVERY `*_deps.py` / `*_rules.py` (7 files, incl. AD-29's four): **883 passed,
1 skipped** (`test_color_roundtrip.py:121`, the standing swscale skip), log
`work\c4-light1.log` (worktree). The four layering tests alone: 28 passed. ruff, format, mypy
strict clean.

Oracle, WP2.3 samples with `--device-frames`, every frame (driver
`work\wp3.21\oracle-ad29-wp23.sh`, log `logs\oracle-ad29-wp23.log`; records made on `4dd9280` +
the uncommitted rework, which is `0cc11cd`'s tree): **10 of 10 TIER1, max abs 0** (GPU legs vs
`ref-*-c3-gpu-a`, `--force-cpu` legs vs `ref-*-c3-cpu-a`); `sink_devices` `['cuda:0']` on every
GPU leg, `['cpu']` on every CPU leg.

| # | Item | Suspected | Confirmed | Rejected | Fixed |
|---|---|---|---|---|---|
| V21 | the CPU backend satisfies the Protocol through its `device` attribute (a data member) | yes | - | rejected: `isinstance(NumpyBackend(), DeviceFrameBackend)` is False (test) | - |
| V22 | a sink built with the CPU backend accepts a device frame | yes | - | rejected: the backend is kept only if it satisfies the Protocol; refused with `to_host` (test) | - |
| V23 | mypy narrows the device branch of `_payload` to unreachable (IF-1 types pixels as NumPy), hiding it from type checking | yes | yes (mypy `unreachable`) | - | `pixels: Any`; a non-array under a device label refused by `getattr(..., "dtype")`, not an AttributeError |
| V24 | a stale `device_frames=` / `xp=` caller left in `src`/`tools`/`tests` | yes | - | rejected: grep finds only the oracle's `Job.device_frames` flag, which now selects the backend | - |

**Orchestrator ruling at the yield-6 grant:** the device methods on `CupyBackend` rather than on
the `CoreBackend` base are ACCEPTED (a base method would make `NumpyBackend` satisfy the
Protocol, against AD-29 item 3); relayed to CHARC. **AD-29 item 6 MET:** the reworked #2 is
TIER1 on GX011627 and synthetic 4K (H9, H10) before #3.

**CHARC amendment of AD-29 (main `ce55a95`, relayed after yield 7):** the device methods on
`CupyBackend` are CONFIRMED. Every Protocol-satisfaction test asserts BOTH that `CupyBackend`
satisfies the Protocol AND that `NumpyBackend` does not (io.video: the pair in
`test_wp321_device_frames.py`; analysis: the same pair at #3). The yield-7 STOP (where #3's
quantise lives) is NOT addressed by this amendment and still holds.

## STOP (cell 4, yield 7) and ruling (a)

AD-29 item 1 named "the block sums with their quantise" in core; the RESUME-HERE sketch CHARC
ruled on kept the division and quantise on the host. **Orchestrator RULED (a)** (relayed to
CHARC; an amendment, if any, is relayed without waiting): `CupyBackend.block_sums(a, k)` returns
float64 host sums or None when the exactness bound fails, the bound in core; `proxy.py` keeps
`_divide` and `quantise` and calls `block_sums` only through its one Protocol,
`AnalysisDeviceBackend`, falling back to the host reduction on None. Reading: "the sums the
quantise consumes" (a second quantise in core would be a second source for the AD-5 rule).
Required tests: the Protocol pair both directions; the None path (a planted value failing the
bound takes the host path with the same bytes).

**CHARC UPHELD (a)** (relayed after yield 8; AD-29 text amended on main `e8c56eb`):
`CupyBackend.block_sums` returns float64 host sums, or None at the exactness bound; the
division and quantise stay single-sourced in `analysis/proxy.py`; None takes the host reduction
with identical bytes, a structural choice between two exact paths, NOT a D109 fallback. #3 is
tier 1 or STOP. As built in `05ee507`, no change needed.

## Task 5b (#3): the device block mean, as built (cell 4, `05ee507`)

- `core/backend.py`: `CupyBackend.block_sums(a, k) -> NDArray[float64] | None` (an IF-2 device
  extension, same comment block). Refuses `k < 1`, a non-float32 or non-`(H, W, C)` array
  (ValueError), a host array or another device's (TypeError). The bound (`_sums_are_exact`):
  `top = max(a.max(), -a.min())` (two reductions; a NaN propagates, so `not top <= 1` refuses
  NaN, infinities and magnitudes above 1); a zero frame is admitted; else the smallest non-zero
  magnitude by a CuPy `ReductionKernel` (no frame-sized temporary; `2` stands for "no value"
  since every magnitude is at most 1 there; `INFINITY` is undefined under NVRTC);
  `ceil(log2(k*k+1)) - (frexp_exp(min) - 1 - 23) <= 53`. The sums: rows
  (`reshape(full_rows, k, W, C).sum(axis=1, dtype=float64)` plus the edge row), then columns
  likewise; only the `(ceil(H/k), ceil(W/k), C)` float64 sums are downloaded (4K: 4 MB; the
  by-rows intermediate 50 MB at 4K, 74 MB at 5.3K 8:7 k=8, transient).
- The derivation (R0.6, re-checked): a finite non-zero float32 v with `2**e <= abs(v)` is a
  multiple of `2**(e-23)`; every other non-zero value in the frame is at least the smallest, so
  all are multiples of `2**(e_min-23)`; every partial sum of a block is a sum of a subset of its
  at most `k*k` values, each at most 1 in magnitude, so below `2**m`; float64 holds every
  multiple of `2**L` below `2**m` exactly when `m - L <= 53`; then any summation order gives the
  exact sum, which is also what the host's float64 `reduceat` gives. Subnormals take frexp's
  exponent, which only lowers L (refuses more). Decoded data: `e_min` -8 (8-bit) or -10
  (10-bit), `m` 5 (k=4), 5 (k=5), 7 (k=8): at most 7 + 33 = 40 bits.
- `analysis/proxy.py`: `AnalysisDeviceBackend` (`device: str`, `block_sums`); `block_mean`'s
  division split out as `_divide` (the same expression); `frame_block_mean(pixels, k, backend)`
  (host pixels: `block_mean`; device pixels: `block_sums` when the backend satisfies the
  Protocol and k > 1, `_divide` on the sums; else `block_mean(backend.to_host(pixels), k)`);
  `make_proxy(pixels, backend=None)` = `quantise(frame_block_mean(...))`;
  `frame_pixels_for_proxy(frame, backend)` keeps a frame on the backend's device when the
  backend satisfies the Protocol and the pixels are not NumPy, else `frame_pixels_on_host`.
  `analysis/__init__.py` exports the three new names. `analysis` imports no `core`, no `cupy`.
- `analysis/engine.py`: the decode pass calls `frame_pixels_for_proxy` and
  `make_proxy(pixels, self._backend)` (two lines).
- `tools/export_bench.py` (`6e504fe`): `--device-frames` (global option; `run_once(...,
  device_frames=)`): probes, `select_backend(settings, H, W, method)`, builds the source
  (`build_engine(..., device_backend)`) and `_BenchSink(device_backend)` with it; records
  `device_frames` (header and run) and `device_backend` (the backend's repr). `_BenchSink`
  re-runs `FFmpegVideoSink.__init__(self, device_backend=...)` after `vf._RecordingSink`'s
  (that class, not owned, builds the sink without one; nothing has run yet). A warm leg's
  cache priming stays on host frames (not measured; the proxies are identical either way).

Tests: `tests/test_wp321_device_proxy.py` (21): the Protocol pair (GPU satisfies with an
`inspect.signature`-equal `block_sums`; CPU has no `block_sums` and does not satisfy); device =
host bit for bit (float64 bytes) and the uint8 proxy byte for byte at 4K k=4, 5.3K 16:9 k=5,
5.3K 8:7 k=8, odd 1081x1923 k=2 (edge blocks), 37x53 k=1, 8 and 10 bit; the None path: NaN,
inf, 1.5, 1e-30, 1e-12 planted: `block_sums` is None and the result equals the host's (and the
proxy, for the finite plants); the bound's edge (k=5: `2**-25` admitted, `2**-26` refused), a
signed frame's sums equal NumPy's; refusals; the routing (a GPU frame stays, a host frame and
the CPU backend as before). `tests/test_wp321_bench.py` (+2): a `--device-frames` run gives the
sink device frames and records `CupyBackend`; with `--force-cpu` the sink gets only `cpu`
frames and the record names `NumpyBackend`. **Failing-first:** the proxy file against
`20ab3bb`'s analysis with core's `block_sums` already in place: 19 fail, 2 pass (the two
core-only tests: the bound's edge, the refusals). The bench pair: not run against the base
(the `device_frames` keyword is new; they cannot pass there).

Light run (`-n 4`, `not footage and not slow`; 35 files: analysis (all), core, GUI analysis
service, `test_jobs_export.py`, oracle tool, decode, encode, `test_wp321_*`, every
`*_deps`/`*_rules`): **1050 passed**, warnings only the standing CUDA_PATH one; log
`work\c4-light3.log` (worktree). Bench + layering: 51 passed. ruff, format, mypy strict clean.

Oracle, WP2.3 with `--device-frames` (`oracle-p3-wp23.sh`, `logs\oracle-p3-wp23.log`): **10 of
10 TIER1**, max abs 0. NOTE: the WP2.3 samples are 320x180 (k = 1), so they pin the routing,
not `block_sums`; the k > 1 path is pinned end to end only by the interim-2 oracle legs
(GX011627 k=4, synthetic 4K) in a window.

| # | Item | Suspected | Confirmed | Rejected | Fixed |
|---|---|---|---|---|---|
| V25 | `INFINITY` as the kernel's identity | yes | yes (NVRTC: identifier undefined) | - | `2` as "no value" (every magnitude at most 1 when it runs) |
| V26 | `cupy.max`/`min` skip NaN, so a NaN frame passes the bound | yes | - | rejected: NaN propagates (smoke run: max nan, min nan, bound False; the NaN plant test) | - |
| V27 | the bound's frame temporaries (2 x frame) breach the memory watch item at 5.3K | yes | yes, in the draft (`xp.abs`, `xp.where`: about 0.6 GB transient at 5.3K 8:7) | - | two reductions and a reduction kernel, no frame-sized temporary |
| V28 | mypy narrows `frame_pixels_for_proxy`'s device branch to unreachable | yes | yes | - | `pixels: Any` |
| V29 | a lone edge row/column when k divides neither side, or `full_rows == 0` (H < k) | yes | - | rejected for the edges (odd 1081x1923 test); H < k cannot reach k > 1 (k <= min(H, W) // 540), guarded by `if full_rows:` anyway | - |
| V30 | the CRLF normalisation rewrote `smoothing.py` / `store.py` (CRLF checkout) | yes | yes (status showed them modified, no content diff) | - | `git checkout --` both; never committed |

## Interim 2 (#1+#2+#3, device frames ON; development evidence, not of record; EXCLUSIVE window 2026-10-28)

Driver `work\wp3.21\interim2.sh` (interim 1's with `--device-frames`; 5 GiB check per step), logs
`work\wp3.21\logs\interim2-{1..4}.log`. Bench record
`work\wp3.21\bench\export-bench-GX011627-20261028T081448Z.json` (header and run
`device_frames: true`, `device_backend: CupyBackend(device='cuda:0')`).

| Figure (GX011627, cold c3, GPU, hw_decode, NVENC) | Interim 1 (#1) | Interim 2 (#1+#2+#3) |
|---|---|---|
| s/frame (whole job) | 0.810 (24.28 min/min at 30000/1001) | 0.5130 |
| min/min | 24.28 | **15.37** (meets D106 25) |
| lead (the `analysis` phase) | - | 5.28 s |
| frames phase s/frame | 0.778 (serial path 0.714) | **0.5014** (341.44 s / 681) |
| per frame median / p90 / max | 0.7735 / - / 2.858 | 0.4830 / 0.5341 / 0.9649 |
| peak tree RSS | 3,987 MiB | 3,393 MiB |
| peak GPU memory | 2,877 MiB | 3,138.0 MiB |

- Oracle: GX011627 c3, synthetic 4K c3, GX011627 ancuti2018 all **TIER1, max abs 0**, every
  sink frame on `cuda:0` (H12-H14). These pin #3's `block_sums` at k = 4 end to end (the WP2.3
  samples, k = 1, could not).
- What #2+#3 recovered: the frames phase 0.778 -> 0.501 s/frame, below the serial 0.714; #2 and
  #3 were not separated (one run).
- The top frames recur (index 323 0.965 s, index 0 0.955 s, index 387 0.947 s), not a one-off at
  the lead: task 10's report places them (CHARC `4dc2978b` point 3).
- Memory: GPU +261 MiB over interim 1 (device frames: integer planes and A's float32 frame on the
  card); host -594 MiB. Both inside AD-1. The 5.3K estimate (about 6.9 of 8 GB before the FFT)
  remains the watch item.
- INTERIM figures, one run, cold cache: never quoted as V16's result outside this ledger; the
  figures of record are task 10's.
- **This window (H12-H14) is the only end-to-end pin on `block_sums` for k > 1** (CHARC
  `fc6e2e64`: #3 as built is AD-29 as amended; step 1's timing is development evidence beside
  interim 1 and the 0.714 / 0.778 pair, not V16).
- **FINDING (orchestrator, under CHARC `4dc2978b` point 3):** the slow frames RECUR (indices
  323, 0, 387 at 0.965, 0.955, 0.947 s against a median of 0.483), not a one-off at the lead;
  task 10's report must place them (per-frame record).
- Graphics peak +0.26 GB over interim 1 against #2's estimate of +0.13 GB at 4K: the estimate
  was low by about 0.13 GB; the 5.3K row (about 6.9 of 8 GB before the FFT, now possibly
  higher) stays the watch item for task 6's memory re-read.

## Re-grounding (2026-10-27/28, against `d1e4537`)

Anchors checked against the code before use:

- `AnalysisEngine._decode` (`src/clearwater/analysis/engine.py:456-518`): per frame `next()` (FFmpeg
  pipe read + `planes_to_rgb` inside `FrameStream._frame`, `io/video/decode.py:490-504`), `_check`,
  `frame_pixels_on_host`, `make_proxy` (= `quantise(block_mean(pixels, proxy_factor(h, w)))`,
  `analysis/proxy.py:83-98`), `cache.store_proxy`, `cache.proxy`, `_image` (`proxy_image`: float32
  `/255` on the host, then `backend.asarray`), stage-1 `analyze`, `_measured.put`, `_store.put`,
  `_report`. Stage 2 onward run only after the whole pass (`_run_stages` -> `_measure` per stored
  proxy, then `_smooth_stage` in `SMOOTH_CHUNK` chunks).
- The WP3.11 style debt is at `engine.py:500` (`import logging` inside the decode pass's `finally`).
- `ExportEngine._write_frames` (`src/clearwater/jobs/export.py:741-780`): one thread, one frame in
  flight: `next()`, `smoothed_record`, `backend.asarray`, `render`, `to_host`, `sink.write`
  (`rgb_to_planes` inside `FFmpegVideoSink._payload`, `io/video/encode.py:905-943`; the sink refuses
  `device != "cpu"`, `encode.py:909`).
- c3 stages (`methods/ancuti_fusion.py:88-112`): `white_balance` (measured in the decode pass) then
  `fusion` (`depends_on_stages=("white_balance",)`). ancuti2018: `compensation` (source-only),
  `white_balance`, `fusion`.
- `smoothing.reach` (`analysis/smoothing.py:123-161`): Gaussian half-window `floor(window/2/tb)`
  then, for `median_gaussian`, the median's `floor(0.05 s/tb)`. At 30000/1001 and 2 s: 29 + 1 = 30
  frames per smoothing. Round 0 derives the composed lead from this (see the open items).
- `gaussian_blur` (`core/backend.py:274-295`): `ndimage.gaussian_filter(mode="reflect",
  truncate=GAUSSIAN_TRUNCATE)`. `memory_estimate_bytes` (`core/memory.py`): 50 1/12 planes x 1.25
  + 1 MiB.

## Per-step GPU occupancy: method and cadence (CHARC addition to task 1, relayed 2026-10-28)

`tools/analysis_breakdown.py` gives two occupancy figures beside each step's time:

1. **Device bound (exact, by construction).** Only `proxy_image`, `analyze`, `upload`, `render`
   and `to_host` issue CUDA work (`DEVICE_STEPS`), and each ends with a device synchronisation.
   Every other step is host work (NumPy, the JPEG codec, the pipes, the store), during which this
   process's stream is idle. `device_share_bound` = the sum of a phase's device-step means over
   its mean wall: the most its CUDA compute can have occupied the card.
2. **Sampled occupancy (statistical).** ONE `nvidia-smi --query-gpu=pci.bus_id,utilization.gpu,
   utilization.decoder,utilization.encoder,clocks.sm,power.draw --format=csv,noheader,nounits
   --loop-ms=200` process (5 Hz, no process start per reading), filtered to the CuPy device's
   PCI bus id. Each line is stamped with `time.perf_counter()` when it arrives and attributed to
   the step whose recorded interval holds the stamp (`occupancy_by_step`). A stamp inside a phase
   but in no step goes to that phase's `(loop)`. Limit: NVML's `utilization.gpu` averages over
   its own sample period (1/6 s to 1 s by product), so a reading partly covers the steps before
   the one it lands in. Per step it is a figure over many frames; the device bound is the exact
   one.
   - **Lightness:** one long-lived child process and one reader thread waking 5 times a second.
     WP3.10's `Telemetry` card readings (one `nvidia-smi` process start each) drop from every
     1 s to every 10 s (`TELEMETRY_GPU_S`); the memory sampling is unchanged (0.25 s).
   - **Not used:** CUDA events. Between synchronised steps the stream is idle, so an event pair
     measures the step's span, not the device's busy time.
   - **Dry run** (GPU, 45 frames of `vid-hevc8-bt709-full`): device bound 22.9 % of the decode
     pass and 64.2 % of the frame path at 320x180; the readings were attributed per step.

## Verification-loop record

| # | Item | Suspected | Confirmed | Rejected (false positive) | Fixed |
|---|---|---|---|---|---|
| V1 | breakdown: loop-closure lambdas in the replay loops (ruff B023 trap; a lambda capturing a loop variable) | yes | design smell (not a live bug: each lambda ran at once) | - | `StepClock.time(step, call, *args)`; no lambdas in loops |
| V2 | breakdown: both later-stage tables carried the whole later-stages wall | yes | yes (dry run: `stage:white_balance` and `stage:fusion` both 3.56 s) | - | per-stage (clock, start, end) |
| V3 | breakdown: first-call device set-up inflates the mean on short clips | yes | yes (dry run, 45 frames: analyze mean 0.168 s, median 0.003 s) | - | `first_wall_s` recorded apart; the mean stays the figure (it is the export's) |
| V4 | breakdown: a failing phase lost the telemetry and the earlier phases | yes | yes (record built inside `run`) | - | `run(..., record=)` filled in place; `finally` keeps telemetry and phases |
| V5 | breakdown: the equality check could pass both ways | yes | - | rejected: a planted 1e-12 change in stage-1 means fails it by name (`test_the_equality_check_fails_when_the_replica_differs`) | - |
| V6 | oracle: an unprobeable clip raised out of `record` (no record kept) | yes | yes, by reading: `source.probe` raises `VideoProbeError`, which `main` does not catch (fixed before the test first ran) | - | probe failure -> keep interval 1, the job reports the failure |
| V7 | oracle: `git_head` expression precedence (`a or b if c else d`) | yes | - | rejected: parses as intended; rewritten for clarity | rewritten |
| V8 | oracle: tier classification indiscriminate | yes | - | rejected: planted +1e-4 -> TIER2, +1e-2 -> FAIL; record/proxy/analyze mutations FAIL with equal frames | - |
| V9 | occupancy: per-step attribution needs step intervals; `planes_to_rgb` and `rgb_to_planes` are timed inside `next` / `write`, not as calls of their own | yes | yes (no interval existed for them) | - | placed by construction: `planes_to_rgb` at the end of `next` (`FrameStream._frame` runs after the read), `rgb_to_planes` at the start of `write` (`_payload` quantises before the pipe write) |
| V10 | occupancy: the bus-id filter would drop every reading (`nvidia-smi` writes `00000000:01:00.0`, CuPy `0000:01:00.0`) | yes | yes (both formats seen live) | - | `bus_key` normalises the domain padding; test |

## Heavy runs (EXCLUSIVE windows only)

| # | Window | Start | End | Command | Conditions | Free memory before | Peak RSS / graphics memory | Exit |
|---|---|---|---|---|---|---|---|---|
| H1 | task 1 (granted, CHARC OPEN) | 03:41:39Z | 03:57:05Z | `uv --directory <wt> run python tools/analysis_breakdown.py GX011627` | GPU backend, hw_decode, auto/NVENC, Standard; cProfile phase included; occupancy 5 Hz, telemetry 0.25 s / 10 s; nothing else heavy started by this cell | 11.3 GiB | tree RSS 2,870 MiB; graphics memory in use 2,421 MiB (device-wide) | 0 |
| H2 | task 2 (same window) | 04:30:37Z | 05:17:52Z | `bash work/wp3.21/oracle-base.sh` (26 records, 13 compares) | GPU (auto) and CPU (`--force-cpu`) legs as listed; serial | 11.13 GiB | not sampled (the oracle records equality, not memory) | 0 |

| H3 | interim 1 (#1), cell 2 | 06:13:38Z | 06:23:09Z | `interim1.sh 1`: `export_bench.py run GX011627 --cache cold --method c3 --subdir wp3.21/bench` | GPU, hw_decode, auto -> hevc_nvenc, Standard; telemetry 0.25 s / 1 s; strays: only this job | 12.0 GiB | tree RSS 3,987 MiB (python 1,370 + 3 ffmpeg: two decoders, one encoder); GPU memory 2,877.0 MiB | 0 |
| H4 | same window | 06:23:50Z | 06:33:43Z | `interim1.sh 2`: oracle record `cand-overlap-GX011627-c3` + compare | GPU (auto) | 12.05 GiB | not sampled | 0 |
| H5 | same window | 06:34:02Z | 06:36:04Z | `interim1.sh 3`: oracle record `cand-overlap-synth4k-c3` + compare | GPU (auto), sha256-guarded clip | 12.01 GiB | not sampled | 0 |
| H6 | same window | 06:36:30Z | 06:43:07Z | `interim1.sh 4`: oracle record `cand-overlap-GX011627-ancuti2018` + compare | GPU (auto) | 12.03 GiB | not sampled | 0 |
| H7 | #2 oracle (granted at yield 4), cell 3 | 07:08:29Z | 07:15:24Z | `oracle-devframes-gx.sh 1`: record `cand-devframes-GX011627-c3` (`--device-frames`) + compare | GPU (auto), device frames; strays: only this job | 11.96 GiB | not sampled | 0 (COMPARE-EXIT 0) |
| H8 | same window | 07:15:38Z | 07:17:11Z | `oracle-devframes-gx.sh 2`: record `cand-devframes-synth4k-c3` (`--device-frames`) + compare | GPU (auto), sha256-guarded clip | 12.19 GiB | not sampled | 0 (COMPARE-EXIT 0) |
| H9 | #2 under AD-29 (granted at yield 6), cell 4 | 07:46:59Z | 07:54:31Z | `oracle-ad29-gx.sh 1`: record `cand-ad29-GX011627-c3` (`--device-frames`) + compare vs `ref-GX011627-c3-a` | GPU (auto), device frames, head `867d5fb`; strays: 4 idle python (comms, 47-106 MB) | 11.43 GiB | not sampled | 0 (COMPARE-EXIT 0): TIER1, 681 frames, max abs 0; `sink_devices ['cuda:0']`; job wall 445.6 s |
| H10 | same window | 07:54:48Z | 07:56:21Z | `oracle-ad29-gx.sh 2`: record `cand-ad29-synth4k-c3` + compare vs `ref-synth4k-c3-a` | GPU (auto), sha256-guarded clip | 11.63 GiB | not sampled | 0 (COMPARE-EXIT 0): TIER1, 120 frames, max abs 0; `['cuda:0']`; 88.3 s |
| H11 | interim 2 (granted at yield 8; OPEN 08:14Z), cell 4 | 08:14:47Z | 08:20:59Z | `interim2.sh 1`: `export_bench.py run GX011627 --cache cold --method c3 --subdir wp3.21/bench --device-frames` | GPU `CupyBackend(device='cuda:0')`, device frames ON, hw_decode, auto -> hevc_nvenc, Standard, cold cache; telemetry 0.25 s / 1 s; strays: only this job (own python); product `0ed0672`, records stamp `23f8918` (ledger-only on top) | 11.45 GiB | tree RSS 3,393 MiB; GPU memory 3,138.0 MiB | 0 |
| H12 | same window | 08:21:15Z | 08:28:21Z | `interim2.sh 2`: oracle `cand-i2-GX011627-c3` (`--device-frames`) + compare vs `ref-GX011627-c3-a` | GPU (auto) | 11.68 GiB | not sampled | 0 (COMPARE-EXIT 0): TIER1, 681 frames, max abs 0; `['cuda:0']` |
| H13 | same window | 08:28:34Z | 08:30:01Z | `interim2.sh 3`: oracle `cand-i2-synth4k-c3` + compare vs `ref-synth4k-c3-a` | GPU (auto), sha256-guarded clip | 11.58 GiB | not sampled | 0 (COMPARE-EXIT 0): TIER1, 120 frames, max abs 0; `['cuda:0']` |
| H14 | same window | 08:30:05Z | 08:34:06Z | `interim2.sh 4`: oracle `cand-i2-GX011627-ancuti2018` + compare vs `ref-GX011627-ancuti2018-a` | GPU (auto) | 11.67 GiB | not sampled | 0 (COMPARE-EXIT 0): TIER1, 681 frames, max abs 0; `['cuda:0']` |

Light runs (no window): `vid-hevc8-bt709-full` dry runs of both tools on the GPU (breakdown:
residuals 0.01-0.05 %, replica equals engine on 180 records and 45 proxies; oracle base control
TIER1 on 45 frames); `tests/test_analysis_breakdown.py` 11 passed (18 with the occupancy tests), `tests/test_export_oracle.py`
14 passed.

## Task 1 result: the breakdown (GX011627, c3, GPU, hw_decode; EXCLUSIVE window 2026-10-28)

Record `C:\Users\rwsmy\clearwater\work\wp3.21\breakdown\breakdown-GX011627-c3-20261028T034140Z.json`
(log `work\wp3.21\logs\breakdown-GX011627.log`; cProfile `...-20261028T034140Z.prof` and
`-profile.txt` beside it). 681 frames, 3840x2160, 30000/1001. Ran 03:41:40Z-03:57:05Z, exit 0.

**CHECK (Q6 form)**: the sum of the step means against the mean per-frame wall is within 5 % in every
phase. Residuals: decode pass 1.07 %, stage fusion 0.43 %, frame path 0.91 %. **Replica equals
engine bit for bit**: 2,724 records (raw and smoothed, both stages) and 681 proxies.
The cProfile engine took 212.86 s with the profiler on, against the replica's 216.9 s; this is a
cross-check, not a figure of record.

Per-frame step means, in seconds. The occupancy columns come from the 5 Hz `nvidia-smi` sampler,
attributed to steps; they are statistical, because NVML averages over its own period.

| Phase / step | mean | median | p90 | total s | share of phase | sampled util % | SM MHz |
|---|---|---|---|---|---|---|---|
| **decode pass** (wall 0.29908 s/frame, 203.9 s) | | | | | | 22 (phase median) | **210** |
| decode_wait | 0.00403 | 0.00303 | 0.00445 | 2.7 | 1.3 % | 13 | 210 |
| planes_to_rgb (host) | 0.05324 | 0.04994 | 0.06254 | 36.3 | 17.8 % | 16 | 210 |
| **block_mean (host float64)** | **0.15230** | 0.14999 | 0.16539 | 103.7 | **50.9 %** | 19 | 210 |
| quantise | 0.00979 | 0.00890 | 0.01129 | 6.7 | 3.3 % | 22 | 210 |
| store_proxy (JPEG + write) | 0.00593 | 0.00552 | 0.00705 | 4.0 | 2.0 % | 20 | 210 |
| proxy (read + decode) | 0.01084 | 0.01014 | 0.01247 | 7.4 | 3.6 % | 25 | 210 |
| proxy_image (device) | 0.00705 | 0.00626 | 0.00745 | 4.8 | 2.4 % | 13 | 210 |
| analyze stage 1 (device) | 0.05262 | 0.04555 | 0.04799 | 35.8 | 17.6 % | 16 | 210 |
| store_puts, report, check, frame_pixels_on_host | 0.00008 | | | 0.1 | 0.0 % | | |
| **later stages** (fusion: 681 frames, 13.05 s; white_balance smoothing 0.007 s) | 0.01914 | | | 13.1 | | 50 | 2220-2290 |
| fusion: proxy / proxy_image / analyze (device) | 0.00382 / 0.00332 / 0.01184 | | | 2.6 / 2.3 / 8.1 | | 44-54 | 2220-2290 |
| **frame path** (wall 0.71423 s/frame, 487.9 s; close 0.607 s once) | | | | | | 100 (phase median) | 1635 |
| decode_wait | 0.00640 | 0.00491 | 0.00759 | 4.4 | 0.9 % | 89* | 1590 |
| planes_to_rgb (host) | 0.07689 | 0.07602 | 0.09172 | 52.4 | 10.8 % | 89* | 1605 |
| upload (device) | 0.01524 | 0.01315 | 0.02177 | 10.4 | 2.1 % | 78 | 1620 |
| **render (device)** | **0.50011** | 0.48836 | 0.49850 | 340.6 | **70.0 %** | 63 | 1650 |
| to_host (device) | 0.01299 | 0.01108 | 0.01868 | 8.8 | 1.8 % | 66 | 1650 |
| rgb_to_planes (host) | 0.08871 | 0.08733 | 0.10262 | 60.4 | 12.4 % | 90* | 1583 |
| sink_write rest (checks, pipe) | 0.00729 | 0.00579 | 0.00921 | 5.0 | 1.0 % | 94* | 1575 |

\* A host step's sampled utilisation inside the frame path is smeared by NVML's window: the render
dominates every frame. The device bound is the exact figure.

**Device bound** (the exact share of the mean wall spent in the CUDA steps): decode pass **20.0 %**,
fusion 79.2 %, frame path 74.0 %.

**The GPU-idle observation, explained**: the decode pass is 80 % host work. block_mean alone is
50.9 %; with planes_to_rgb, quantise and the proxy round trip the host share reaches 78 %. The card
therefore gets CUDA work at most 20 % of the time, in bursts of a few ms. At that duty cycle the
driver never leaves the idle clock (median SM **210 MHz** through the pass, 4.9 W), so the device
steps themselves run slowly. Stage 1's analyze on the 960x540 proxy takes 46 ms (median), while
fusion's analyze, which does more work, takes 8 ms once the card has boosted to 2220-2290 MHz in the
later stages (79 % device bound). WP3.14's GX011625 idle reading (210 MHz, 5.1 W) is this pattern.
**Named step: `block_mean`, the host float64 block mean of the 4K frame.**

Totals beside the baseline: analysis 0.299 + 0.019 = 0.318 s/frame (WP3.14 split ~0.31); frame path
0.714 (WP3.14 ~0.74); together 1.03 s/frame (WP3.14 1.061-1.065). The render takes 0.500 s here,
against 0.410 in WP3.4's core row; the SM ran at about 1650 MHz under a ~54 W draw.

## Task 2 result: the oracle base reference and CONTROL

Log `C:\Users\rwsmy\clearwater\work\wp3.21\logs\oracle-base.log` (driver `work\wp3.21\oracle-base.sh`).
Ran 04:30:37Z-05:17:52Z, exit 0, with 11.13 GiB available at the start. Every one of the 26 records
finished ok. Reference folders are `C:\Users\rwsmy\clearwater\work\wp3.21\oracle\ref-<clip>-<method>[-gpu|-cpu]-{a,b}`
(9.8 GB, nothing committed). The synthetic clip is `oracle\clips\synthetic-4k.mp4`, sha256
`4634ba019b12fd968988fe38c31548be54e51f499670406be4dce659847f5622` (recorded beside it; a mismatch is
refused, `772582e`).

**CONTROL: 13 of 13 TIER1** (`compare a b --require-tier1`: every frame digest, record, analyze call
and proxy equal; N10 holds on this device and on the CPU):

| Control | Frames | Verdict |
|---|---|---|
| hevc8-bt709-full c3 GPU / CPU | 45 / 45 | TIER1 / TIER1 |
| hevc10 c3 GPU / CPU | 45 / 45 | TIER1 / TIER1 |
| vfr c3 GPU / CPU | 30 / 30 | TIER1 / TIER1 |
| rotated c3 GPU / CPU | 45 / 45 | TIER1 / TIER1 |
| truncated c3 GPU / CPU | 24 / 24 | TIER1 / TIER1 |
| synthetic 4K c3 GPU (4 frames kept each) | 120 | TIER1 |
| GX011627 c3 GPU (23 kept; 1,362 analyze calls) | 681 | TIER1 |
| GX011627 ancuti2018 GPU (23 kept; 2,043 analyze calls) | 681 | TIER1 |

Oracle job walls (informative, with the recording overhead; not figures of record): GX011627 c3
695.2 / 702.9 s, ancuti2018 513.1 / 508.6 s, synthetic 4K 125.0 / 122.2 s.

## Round 0: the design table (task 3), written for a re-seated successor

### R0.1 Candidates in order of measured gain

| # | Candidate (task) | Measured basis | Expected saving | Oracle tier | Modules / grants | Tests that pin it |
|---|---|---|---|---|---|---|
| 1 | **Overlap the analysis with the export** (4) | analysis 0.318 s/frame = 31 % of the cold wall; the frame path alone 0.714 | the analysis leaves the critical path: end to end about 0.72-0.80 s/frame (21.6-24 min/min) instead of 1.03; plus a fixed start-up lead of 61 frames x the analysis rate (about 18 s now, about 6 s after #3) | **tier 1** (same arithmetic; only threads and order change) | `analysis/engine.py`, `jobs/export.py` (granted) | lead derivation; planted lead short by one fails by name; order; cancel at each phase; analysis failure mid-export; CPU path; every WP3.14 cancel/failure/D87/V11 test and WP3.11 `smooth_at` test unchanged |
| 2 | **Device-side frame conversions in the frame path** (5a) | planes_to_rgb 0.077 + rgb_to_planes 0.089 + upload 0.015 + to_host 0.013 = 0.194 s/frame, host | about 0.17 s/frame: upload the 8/10-bit planes (25/50 MB, not 99.5 MB float32), convert on the device; quantise on the device and download the planes | expected **tier 1** (see R0.6: float32 `k / (2^n-1)` and `rint(clip(x) * (2^n-1))` are correctly rounded IEEE on both; CuPy does not compile with fast math), else tier 2 | **ask:** `io/video/decode.py`, `io/video/encode.py` (DR-63 then CLOSES), `color/samples.py` | oracle legs tier 1; CPU fallback = base; existing decode/encode tests unchanged (R0.7) |
| 3 | **Device block mean and conversion in the analysis** (5b) | block_mean 0.152 + planes_to_rgb 0.053 + quantise 0.010 = 0.215 s/frame of host CPU, and the 210 MHz idle clock | after #1 it is off the critical path. It cuts CPU contention with the export thread and the start-up lead, and its device steps run at boost | **tier 1 required and provable** (R0.6: the float64 block sums are EXACT, so any order gives the same bytes) | `analysis/proxy.py`, `analysis/engine.py` (granted); uses #2's device frames | proxy bytes equal on every oracle clip and in a unit test on random 8/10-bit planes, 4K and 5.3K; `downscale` equality test unchanged |
| 4 | **3C Gaussian by FFT** (6) | render 0.500 s = 70 % of the frame path, but the blur's share of the render is NOT yet measured. At 4K the c3 kernel sigma is 0.05 x 2160 = 108 px, radius 432, 865 taps, two planes (Cb, Cr) x two passes | unknown until an interim timing (Q10 window): the blur's share of the render, direct against FFT | **tier 2** (render only; R0.4 keeps it out of the analysis) | `core/backend.py` (granted) | bound <= 1e-5 against the direct filter on 4K and 5.3K frames and step edges at every border; end-to-end tier 2; deterministic on repeat; memory re-read |
| - | DR-40 (b) constant uploads | WP3.4: 0.75 ms per c3 render = 0.15 % of this render (0.500 s), under Q8's 1 % | none | - | none (`methods/` not asked) | CHARC records it measured-negligible |

The order follows the figures: #1 first, which the brief also gives as the default. #2 and #3 share
the device-frame plumbing, so they are best built together after #1. #4 waits for its interim timing.
Expected end state if #1-#3 land: frame path about 0.53 s/frame (about 16 min/min), so the interim of
25 is met with margin. #4 is the route toward the ~10 aim.

### R0.2 The overlap design (question 2, ruling Q2 as corrected in `d3cd663`)

- **Two decoders, one thread each** (DR-45 (a)). The analysis thread A iterates and closes its own
  `FrameStream`. The job thread E iterates and closes the export stream, as `_write_frames` does today.
  No frame ring: each thread holds at most one decoded frame, so the bound holds by construction.
- **A runs the analysis as a stream** (an `analysis/engine.py` change, product-internal). After each
  decoded frame it advances, stage by stage, the outputs that have become FINAL:
  - stage-s raw is measured for frame i once the smoothed records of stages 0..s-1 are final at i;
  - stage-s smoothed is written for i (`smooth_at` over chunks) once stage-s raw covers
    `reach(i)` AND the decoded axis extends at least ONE frame past `reach(i).last` (the at_end
    boundary: `smooth_series` sets `at_end` when the reach ends on the axis's last index), or the
    stream has ended;
  - `smooth_at` over chunks equals the whole-clip `smooth` (WP3.11 claim 9), so every record is
    bit for bit the whole-clip record.
  - The final pass at the end of the stream completes every remaining output, then
    `mark_complete` (V17, unchanged: after the whole pass). A complete (warm) cache entry streams the
    later stages from the stored proxies the same way.
- **The lead is DERIVED at run time from the stage graph and the axis**, not configured. Every later
  stage is measured with all earlier stages' SMOOTHED records (`_measure`'s `earlier_stages =
  stages[:index]`), so the chain is linear. Frame i's last stage is final when the raw stage-0
  records reach `i + sum(reach_s) + 1` over pts.
  - For c3 at 30000/1001 with the 2 s `median_gaussian`: per smoothing 29 (Gaussian) + 1 (median) =
    30 frames, so the lead is 30 + 30 + 1 = **61** (Q-c, CHARC `a2ef1f64`; the 90 was a double count).
  - For ancuti2018 (three smoothed stages): 30 x 3 + 1 = **91**.
  - VFR holds because the reach is computed over pts.
- **E waits on a watermark**, under a `threading.Condition` owned by the engine. Before rendering pts
  p, E blocks until A has published "final through index >= idx(p)", or A has ended. If A failed or
  was cancelled, E raises with A's original text, or CANCELLED. E reads `smoothed_record` exactly as
  today.
  - A guard in E checks the watermark before each render: rendering before final raises by name. The
    planted test shortens the derived lead by ONE at the composed bound and must fail that guard
    (and, without the guard, give a record that differs from the whole-clip one).
- **One writer per cache key** (DR-62 not widened): only A writes the cache. E never calls a store
  method.
- **Cancel**: E's `progress.cancelled()` or the watchdog sets the engine's cancel, A stops within
  one frame, and E joins A before the sink's `abort`. Result `CANCELLED`, nothing on disk, cache entry
  not marked complete (as today).
- **Failure**:
  - A failure in A ends A; E wakes, joins A and raises `_FailureError(f"{name}: analysis failed:
    {A's text}")` (the `_check_analysis` text, unchanged).
  - A failure in E cancels and joins A, and E's original error stays the failure.
- **Order kept**: watchdog, `close`, the post-close cancel check and `commit` keep WP3.14's order.
  E's last frame needs A's final watermark, so A has ended before `close`, and E joins it there. No
  second thread is alive at the rename.
- **Progress**: A does not call the job's `Progress` from its thread. Its counts are folded into E's
  reports, because the IF-8 contract does not promise a thread-safe `report` (to verify, R0.8 Q-R3).
- **GPU**: both threads use CuPy's default stream and the shared memory pool, both thread-safe. Kernels
  are serialised on the device and their arithmetic is unchanged, so the result is tier 1.
- **CPU backend (D107)**: the same code. On the CPU, A and E share the cores; NumPy releases the GIL
  in large operations.

### R0.3 Memory budget (N4: 16 GB RAM, 8 GB card; AD-1; question 9)

- **Host, 4K.** Per thread, one decoded frame: planes buffer 24.9 MB, float32 99.5 MB.
  - A also holds `block_mean`'s float64 sums (49.8 MB row pass + 49.8 MB result) until #3 moves
    them to the device.
  - Add one FFmpeg decoder process (32 MiB pipe plus its own RSS, a few hundred MB).
  - Estimate about +0.5-0.8 GB over WP3.14's peak at 4K.
- **Host, 5.3K 8:7** (24.7 Mpix, 2.98x 4K): estimate +1.5-2.4 GB over the measured 6.2 GiB tree
  peak, so about 8.6 GiB, under 16.
- **Graphics card.**
  - E's render as today (AD-1 estimate 1,982 MiB at 4K; measured reserved peak about 1.7 GB).
  - A's analyze on the proxy: about 50 planes x 2 MB = 0.1 GB.
  - A second NVDEC session: a few hundred MB.
  - At 5.3K: 6.0 GiB measured + about 0.5 GB = about 6.5 of 8 GB.
- **FFT (#4).** Per blur call at 4K, one padded plane as complex64, (2160 + 864) x 1921 x 8 B = 46 MB
  per axis pass plus the cuFFT workspace: about 0.1-0.2 GB transient. At 5.3K (sigma 232, radius
  929) about 0.3-0.5 GB, so about 7.0 of 8 GB: tight. If the 5.3K row breaks the budget, Q9's
  fallback applies (direct filter above 4K).
- **`memory_estimate_bytes`** (AD-1) must stay at or above the measured reserved peak at 4K and
  5.3K. The FFT transient is not in its plane count. If the re-measure puts the reserved peak above
  the estimate, that is a STOP to CHARC (a formula change is CHARC's).

### R0.4 The 3C Gaussian route (question 4, ruling Q4) and a FINDING

- **Route.** Per axis, a 1-D linear convolution by FFT (`cupyx.scipy.fft` / `scipy.fft`, float32
  only) with the SAME kernel scipy builds: `_gaussian_kernel1d(sigma, 0, radius)` weights,
  `radius = int(4 * sigma + 0.5)`. The padding reproduces `mode="reflect"` (d c b a | a b c d),
  including repeated reflection when the radius exceeds the axis. Axis 0 then axis 1 per channel, as
  `gaussian_filter` does.
- **FINDING (needs a ruling, R0.8 Q-R1).** A pure sigma threshold cannot keep the FFT out of the
  analysis path, and ruling Q3 requires the analysis records to be tier 1 ALWAYS:
  - the proxy's short side is `ceil(S / (S // 540))`, which is at most 1,079 for every source;
  - the analysis blurs at `c3_kernel_fraction x short side`, up to 0.05 x 1079 = 54 px at the default
    and up to 0.25 x 1079 = 270 px at the parameter's maximum, which overlaps the render's 4K 108 px
    and 1080p 54 px.
  - Proposed gate: the FFT route only when `min(H, W) >= 1080` (no proxy can reach it, by the bound
    above) AND `sigma >= 32` px.
  - Effects: a 1080p and a 4K render use FFT (tier 2); every proxy, every photo proxy, and the
    small-image product-against-prototype bit-for-bit tests stay on the direct filter.
  - This is a shape-dependent route inside IF-2's `gaussian_blur`. Its contract ("symmetric borders,
    4-sigma truncation") is kept and only the rounding differs, but the gate is a choice the brief
    left open.
- **Bound.** <= 1e-5 max abs against the direct filter on [0, 1] float32 data (ruling Q3), measured
  on real 4K frames, 5.3K, and step edges at every border. A measured exceedance is a STOP with the
  figure.

### R0.5 Test list (new)

- `tests/test_wp321_overlap.py`:
  - the derived lead is 61 for c3 and 91 for ancuti2018 at 30000/1001, and correct on a VFR axis;
  - a planted lead short by ONE fails by name;
  - a planted unbounded or out-of-order render fails by name;
  - cancel before start, during the lead, mid-encode with a write blocked until `abort`, and
    immediately before `commit`;
  - an analysis failure injected mid-export keeps the analysis's own text;
  - an export failure joins A;
  - no thread alive at `commit`;
  - the CPU path;
  - the cache is marked complete only after the whole pass, and the export half writes no cache.
- `tests/test_wp321_device_frames.py` (if #2/#3 are granted): device conversions equal the host
  ones bit for bit (8-bit, 10-bit, random and edge codes); device block mean equals host
  `block_mean` + `quantise` byte for byte at 4K and 5.3K and with odd sizes; the sink accepts a real
  device array and still refuses a `"cuda:0"`-labelled NumPy frame.
- `tests/test_wp321_gaussian.py`: the FFT bound at every border with step edges, 4K and 5.3K shapes,
  both backends, deterministic on repeat; the gate never routes a proxy-sized image to the FFT.
- `tests/test_wp321_oracle_legs.py` (`footage`/`gpu`/`slow`): each oracle clip against the task-2
  reference, at the tier its change allows; skipped without the reference.
- Static: WP3.13's import test is run, not changed; no module opens a `gpmd` packet.

### R0.6 Why #2 and #3 can be tier 1 (derivations to re-check in the build)

- **Device block mean.** Float32 samples `k/255` (or `k/1023`) are at least 2^-8 (2^-10) for
  k >= 1 and carry 24 significant bits, so their ulp is at least 2^-31 (2^-33).
  - A block sum of 16 (4K) or 25 (5.3K) of them is below 32 and needs at most 38 bits, under float64's
    53. So the float64 sums are EXACT in any order.
  - The division by the count (16, or 25, or fewer at an edge) is a correctly rounded IEEE division on
    both sides.
  - Hence identical float64 means, identical `quantise` bytes, and an identical proxy.
- **Device conversions.**
  - `planes / float32(2^n-1)` is a single correctly rounded float32 division, and CuPy elementwise
    kernels do not use fast math by default.
  - `rint(clip(x, 0, 1) * float32(2^n-1))` is one multiply and round-half-even on both sides.
  - The NaN refusal stays a host check, on a reduction of the device array.

### R0.7 Existing tests the plan would change, with reasons

- **None for #1** (the overlap is internal to `_video`/`AnalysisEngine`; the public signatures stay;
  WP3.14's and WP3.11's tests run unchanged).
- **#2**: `tests/test_io_video_encode.py:962, 1101, 1211, 1259` frame the sink's refusal of a
  `device="cuda:0"` frame with NumPy pixels. The plan keeps that refusal (a mismatch between the label
  and the array) and accepts only a real device array, so these tests should stay unchanged. If one
  cannot, it goes to CHARC for a ruling, never edited.
- **#4**: none expected under R0.4's gate. Any product-against-prototype bit-for-bit test that lands
  above the gate is listed for a ruling.

### R0.8 Open questions (status)

| # | Question | Recommended | Status |
|---|---|---|---|
| Q-R1 | The FFT gate (R0.4): `min(H, W) >= 1080 and sigma >= 32` px, a shape gate inside IF-2's `gaussian_blur` | yes; it is the only gate that keeps every proxy (so every record) off the FFT by construction | OPEN (CHARC) |
| Q-R2 | Grants for #2/#3: `io/video/decode.py` (an opt-in device-frame mode of `FFmpegVideoSource`: upload the planes and convert on the device; the IF-5 protocol is unchanged, the mode is set at construction), `io/video/encode.py` (accept a real device array; DR-63 closes in the same touch), `color/samples.py` (device-capable conversions, the same arithmetic) | grant all three | OPEN (dispatcher) |
| Q-R3 | `Progress.report` from the analysis thread: fold A's counts into E's reports (no cross-thread `report`) | yes | OPEN (dispatcher; verify against IF-8's text in the build) |
| Q-R4 | The brief's "a planted unbounded queue fails by name": the design has no frame queue (two decoders, one frame per thread). The pinned bound becomes "each thread holds at most one decoded frame" plus the watermark | accept that reading | OPEN (dispatcher) |
| Q-R5 | An interim timing window (Q10) after #1, then after #2+#3, each a GX011627 cold c3 export (about 12 min), plus a short micro-timing of the c3 blur at 4K direct against FFT (a few minutes) to rank #4 | grant when asked | at each request |
| Q-c | composed lead | 60 + 1, derived (CHARC `a2ef1f64`, `d3cd663`) | RULED |
| Q-a / Q-b | output root; synthetic clip | owner `work\wp3.21\`; clip once with its sha256 (guard `772582e`) | RULED |

### R0.9 Handover state for a re-seated cell

- Branch `wp3.21` on `d1e4537`. Commits: `a586be2` breakdown, `c72507f` oracle, `bc7b58e` ledger,
  `947a5f8` occupancy, `4e664b9` ledger, `772582e` synthetic-clip guard, and this round-0 commit.
  NO product code yet. `d3cd663` on main corrects AD-7 and the brief text (docs only); do not rebase
  until the dispatcher says so.
- Tools:
  - `tools/analysis_breakdown.py` (the breakdown; re-run it after #1-#3 to show the new split);
  - `tools/export_oracle.py`, used as `record --clip/--file/--synthetic-4k --name ...`, then
    `compare REF CAND [--require-tier1]`;
  - the reference folders are `C:\Users\rwsmy\clearwater\work\wp3.21\oracle\ref-*-a`;
  - candidates are recorded under new names, for example `cand-<step>-GX011627-c3`.
- Next actions: dispatcher's answers to Q-R1..Q-R4, then task 4 (#1), then an interim window, then
  #2/#3, the interim window, the FFT micro-timing, #4, task 7 debt (`import logging` at
  `engine.py:500`), tests, the review loop, the suite window, and task 10.


## Review rounds (Reviewer A)

None yet (the loop runs after the build, task 9).

| Round | Critical | Major | Minor | In / out of envelope | New / reopened | Reverts | Product or test-only | Transport / CLI | Depth |
|---|---|---|---|---|---|---|---|---|---|
