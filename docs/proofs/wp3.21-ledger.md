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
| 14 | cell 5: task 6 gate, route and job-end release built (`7061699`); batching and the estimate fold wait on the yield-13 STOP | (dispatcher fills) |
| 13 (read) | as given with the STOP acknowledgement | 163,071 |
| 14 (read) | as given with the placement ruling and the seat plan | 232,900 |
| 15 | cell 5: batched route and the estimate's bound built (`17743ec`); WINDOW REQUEST (memory re-read) | (dispatcher fills) |
| 15 (read) | as given at the memory re-read grant | 289,841 |
| 16 | cell 5: WINDOW RELEASED (memory re-read); WINDOW REQUEST (oracle legs) | (dispatcher fills) |
| 16 (read) | as given at the gx grant | 298,494 |
| 17-19 (read) | at the synth and gxa grants | 310,029; 312,501 |
| 20 | cell 5 stands down after the oracle legs; RESUME HERE (cell 6) | (dispatcher fills) |
| 21 | cell 6: Reviewer A round 1 adjudicated (`b1bb9cc`) | 140,415 |
| 22 | cell 6: Reviewer A round 2 adjudicated, loop terminates (`047656f`) | 179,866 |
| 23 | cell 6: cleanup committed (`1df2626`); WINDOW REQUEST (parallel leg) | 215,100 |
| 24 | cell 6: WINDOW RELEASED (parallel leg); WINDOW REQUEST (serial leg) | 227,414 |
| 25 | cell 6: serial leg 1 FAILED; STOP; RESUME HERE (cell 7) | (dispatcher fills) |
| 26 | cell 7: ruling (A) fix built (`57a7a2e`); WINDOW REQUEST (serial leg 2) | 97,433 |
| 27 | cell 7: WINDOW RELEASED (serial leg 2 green); WINDOW REQUEST (task 10 block 1) | 123,491 |
| 28 | cell 7: WINDOW RELEASED (task 10 block 1); WINDOW REQUEST (block 2, 5.3K) | 154,676 (at the grant) |
| 29 | cell 7: block 2 5.3K GPU peak above both bounds; STOP | 167,263 (at the HOLD) |
| 30 | cell 7: option (A) driver drafted in the HOLD (not run) | 180,200 (at the (A) grant) |
| 31 | cell 7: WINDOW RELEASED (attribution); split table to CHARC | (not given) |
| 32 | cell 7: HOLD for the fix ruling; RESUME HERE (cell 8) written | 223,058 |
| 33 | cell 7: part 2 built (`b5a383c`); light STOP on the (b3) form | (not given) |
| 34 | cell 7: (b3) built (`9a4256b`); WINDOW REQUEST (block 2 re-run) | (dispatcher fills) |

## RESUME HERE (cell 6, after cell 5)

**State at hand-over:** branch `wp3.21` on base `d1e4537`, NO rebase, worktree CLEAN at the
ledger head. Cell 5's commits: ledger `650a693`..; Q-R7 bench stamps `83349d7`; task 6 gate,
route and job-end release `7061699`; batched route and the GPU estimate's bound `17743ec`.
`interfaces/` and `color/samples.py` equal `d1e4537`. Tasks 1-7 are DONE (task 7: the engine
`import logging` and DR-63 closed by cells 3/4; DR-40 (b) measured-negligible per Q8; Q-R7 is the
bench's tool-side stamps). The cell-5 sections below ("Re-seat: cell 5" onward, before
"Re-seat: cell 2") hold the evidence; read "Task 6 under (A), as built" and "Task 6 memory
re-read" if a task needs them.

**Task 6 as built (CHARC `5b05c53d` Q-R1, `8e103622`, `1db8547f` (A), `72becf26`):**
`core/backend.py` `fft_route` (min(H, W) >= 1080 and sigma >= 32, both backends), per-axis
float32 rfft in batches of at most 512 lines (last batch = final positions), EVEN transform
length (cuFFT odd lengths are batch-position dependent: the FINDING); `fft_memory_bound_bytes`
added by `CupyBackend.memory_estimate_bytes`; `CupyBackend.release_fft_plans` called once per job
from `ExportEngine._run`'s `finally` through `jobs.export.JobDeviceBackend` (AD-29). Tests:
`tests/test_wp321_fft_gaussian.py` (44, one `footage`), `tests/test_wp321_fft_release.py` (9),
`tests/test_wp321_bench.py` (+4 for Q-R7).

**Quantised difference (CHARC `173aa880`, mandatory): DONE** by the sink's own rule (float32 clip,
scale, round half to even; checked in `rgb_to_planes`): 8-bit 14,858 of 572,313,600 values
changed, 10-bit 60,692, max 1 code value each (see "Task 6 oracle legs"). The report states the
rule is the product's.

**Oracle legs for task 6: DONE, every leg as expected** (see "Task 6 oracle legs" below):
WP2.3 x10 TIER1 (max abs 0); GX011627 c3 TIER2 (max abs 7.06e-6, records, proxies and analyze
calls equal); synthetic 4K c3 TIER2 (2.44e-6); GX011627 ancuti2018 TIER1 (0). The report uses
CHARC's wording for the pixel change (quoted there), never "no exported pixel changes".
CHARC `16a8ee8a`: the even transform length is ACCEPTED as a numeric detail of the ruled path
(in the report AND the route's docstring, which `17743ec` already has; the pinned tests are the
tripwire); the `select_backend` query is RULED (a), below.

**Remaining order (each heavy run in its own granted window):**

1. **Reviewer A** (brief "Review loop"): Codex `gpt-6.1-sol` / high at the cell's seat over WSL,
   probe first; copy the runner and prompt shape from
   `C:\Users\rwsmy\clearwater-review-evidence\wp3.14\r2\`; evidence
   `C:\Users\rwsmy\clearwater-review-evidence\wp3.21\rN\` with md5s; the banner must read
   `gpt-6.1-sol` (else the round is void); `--glob '!docs/proofs/**'`, withhold
   `clearwater-review-evidence`, forbid the footage folder; WHAT TO EXAMINE is the brief's list
   (add: the FFT gate and batching, the even-length rule, the bound, the release paths). END THE
   TURN once a round's verdict is adjudicated, before remediating; keep the cumulative round
   ledger; STOP at round 5 for approval. Fill: `docs/review-gate-clearwater.md` Part 1.
2. **The two-leg suite** (GATE_CHECKS), one window per leg, from Git Bash, `PYTEST_ADDOPTS`
   unset, `QT_QPA_PLATFORM=offscreen`, foreground, output under `work/`:
   `uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=work/<run>-parallel`
   then `uv run pytest -q -rs -m "gpu or footage or gui or slow" --basetemp=work/<run>-serial`.
3. **Task 10, the V16 re-measure, LAST** (CHARC `eab16ca8`): `tools/export_bench.py v16
   --device-frames --subdir wp3.21/bench` on the final commit; GX011627 rows first, GX011625
   LAST, each block its own window. Header: device frames ON, hw_decode ON, the backend, the
   cache state. OFF row on GX011627 c3 only if it fits the same window (it gives the #2 / #3
   split, CHARC `b4c143d7` 1). The report: the frames-phase trio (0.714 serial, 0.778 interim 1,
   0.501 interim 2) plus task 10's; the stubs sentence (no product code constructs the real
   source yet; the GUI's path is the stubs' until WP4.2); the hw_decode limit sentence (a CPU
   backend with a hardware decoder is not supported); every row beside its baseline row; the
   analysis share from the Q-R7 keys (`lead_s` + `record_wait_s`, `analysis_share_overlapped`).
   **Memory method (binding, CHARC `1db8547f`): every peak with the plan cache and the pool
   cleared first.** The 5.3K row is the measurement of record with the plans counted against
   the GPU estimate (5.3K: 6,281 MiB = 5,897 + 384); a peak above it is a STOP to CHARC.
   FINDING to place (CHARC `b4c143d7` 2): the recurring ~0.96 s frames (interim 2 indices 0, 323,
   387; median 0.483); check 323 / 387 (64 apart) against GX011627's GOP via ffprobe keyframe
   flags (read-only) before naming decoder seek, sink write, cache flush or GC; no fix unless the
   cause is in an owned file and one line.
4. **Report** `docs/reports/wp3.21-optimisation.md` (claims, evidence paths, limits, baseline
   beside result; plan size follows transform length, not shape, is the reason the bound is per
   line length; the odd-length cuFFT finding; the micro-timing and memory re-read tables), then
   the return report (under about 70 lines, by SendMessage to the dispatcher).

**RULED (CHARC `16a8ee8a`) (a):** `select_backend` stays on AD-1's BASE estimate;
`CupyBackend.memory_estimate_bytes` (base + bound) is the figure the re-read and task 10 check
against. If task 10's 5.3K peak exceeds base x 1.25, that is the ruled STOP, and (b), folding the
bound into the selection, becomes the fix. Do NOT change `test_core_select.py`. **Out of scope:** the GUI preview's plans (CHARC's register row,
binding WP4.3, written at the accept).

**Standing rules (all binding):** worktree only, absolute paths or `git -C` or a `( cd ... )`
subshell, never a bare `cd`; never edit the main tree; never `git stash`, `git clean -x`, merge
or rebase. Commit by pathspec `git -c core.autocrlf=false commit -m "...(wp3.21)..." -- <paths>`
with the `Co-Authored-By:` footer; new files need `git add -- <file>` first; normalise each
edited file with `sed -i 's/\r$//'` and prove 0 CR (and no control characters: a Python
literal `\b` in a ledger script became a backspace once) per committed blob. Scripts holding
ledger text: write them with the Write tool under a private scratchpad folder (bash heredocs
fail on some text). Footage READ-ONLY, only through `find_footage_file`; nothing
footage-derived committed; never decode `gpmd`, never read a location tag. Nothing under
`src/clearwater/interfaces/` changes; edit only the brief's files and the Q-R2 grants. No new
dependency, no OS-specific code. Every heavy run EXCLUSIVE with the dispatcher's grant (WINDOW
REQUEST with commands, durations, evidence; at least 5 GB free; one job at a time; WINDOW
RELEASED after); wait in the FOREGROUND, one stage per call. Non-TIER1 where tier 1 is expected,
anything outside tier 2, an AD-1 breach, an unowned-file change: STOP. The light set always
includes every `*_deps.py` / `*_rules.py`. Depth: record the dispatcher's figure at each yield;
about 250K the evaluation point, about 400K STOP with a RESUME HERE.

## RESUME HERE (cell 5, after cell 4's interim 2) -- SUPERSEDED by RESUME HERE (cell 6) above

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

### Task 6, the parts the STOP cannot change (cell 5, `7061699`)

The orchestrator's nudge (the GO, sent before it saw the yield-13 STOP) said proceed; the cell
built what the STOP's answer cannot change and held the rest.

- **`core/backend.py`:** `FFT_MIN_SHORT_SIDE = 1080`, `FFT_MIN_SIGMA = 32.0`, `fft_route(h, w,
  sigma)` (shape and sigma only, never the device or free memory); `gaussian_kernel` (scipy's
  `_gaussian_kernel1d` weights, pinned equal by a test); `reflect_index` (numpy's `symmetric`
  pad, repeated reflection included); `CoreBackend._fft_correlate` (per axis: reflect-pad by
  index, `rfft` at `next_fast_len(n + 2r)`, times the kernel's spectrum, `irfft`, crop; float32);
  `gaussian_blur` routes by `fft_route`, identical for both backends. `NumpyBackend.fft =
  scipy.fft`; `CupyBackend.fft` a cached property importing `cupyx.scipy.fft` at first use (an
  eager import broke `test_core_select.py`'s fake `importlib`, 7 failures, fixed without editing
  the test). `CupyBackend.release_fft_plans()` (an IF-2 device extension under the AD-29
  comment): clears the calling thread's cuFFT plan cache and the pool's free blocks.
- **`jobs/export.py`:** `JobDeviceBackend` (`runtime_checkable` Protocol, the jobs package's own);
  `_Run.backend` set at backend selection in `_video` and `_photo`; `_run`'s try gains a
  `finally` calling `_release_fft_plans(run.backend)` once per job on every path (a raising
  release is logged, never the job's outcome). **Placement note for the orchestrator:** the
  ruling named "the existing `finally`" (`_video`'s, around `analysis.stop()`); that one does not
  cover photo jobs (a 12 MP photo meets the gate), so the release sits in `_run`, which wraps
  both; it still runs after `_video`'s `finally` has joined the analysis thread.
- **Tests** (`tests/test_wp321_fft_gaussian.py`, `tests/test_wp321_fft_release.py`): the gate's
  boundaries and the route taken (a spy on `_fft_correlate`); the kernel equals scipy's; the
  reflect index equals numpy's; (a) the largest proxy short side over S <= 200,000 is 1079 by
  `proxy_factor`, and `block_mean` at S = 1079 and 1619 agrees; (b) a (1079, 1920, 3) step-edge
  blur at sigma 54 and 270 is bit-identical to the direct filter, CPU and GPU; (c) within 1e-5 and
  deterministic: 1080p (one plane 54, RGB 32, sigma 300 with repeated reflection), 4K (one
  plane 108, RGB 32; CPU `slow`), 5.3K one plane 232.4 (GPU), and GX011627 frame 0 (`gpu`,
  `footage`); release: the CPU backend lacks the Protocol, the GPU backend has it and empties
  its plan cache; a video job releases once after the sink's close; failure, cancel, a failure
  before backend selection (none), a raising release (the job stays ok), photo ok and photo
  cancelled after render (once each).
- **Light set:** analysis, core, jobs, methods and `test_wp321_*` files plus every `*_deps.py` /
  `*_rules.py`, `-n 4 -m "not slow and not footage and not gui"`: 2,156 passed (GPU cases at 4K
  and 5.3K included). Slow non-footage `test_methods_assembly_v8.py` (V8 preview against the
  downscaled export) and the 4K CPU bound cases: 7 passed. ruff, format, mypy clean;
  `interfaces/` and `color/samples.py` equal `d1e4537`.
- **Held for the STOP's answer:** the batching (A), the `memory_estimate_bytes` fold
  (condition 2), the 4K and 5.3K memory re-read and the oracle legs (windows).
- **Open item:** a GUI preview of 1080 or more on its short side also meets the gate; its plans
  stay cached on the GUI's thread (no job end releases them). Not this package's surface (Q-C5a
  is the export job's); recorded for the orchestrator.

### CHARC `1db8547f`: the yield-13 STOP RULED (A), chunked per-axis (relayed)

1. The batch is a FIXED constant in core, 512 lines; the last batch is the FINAL 512 lines (one
   plan set per axis); overlapping lines recomputed, not blended. REQUIRED test: chunked
   bit-identical to unchunked per-axis on line counts NOT multiples of 512 along BOTH axes, at
   1080p, 4K and 5.3K 8:7 (synthetic, GPU). Oracle expectation unchanged (tier 2 on renders,
   tier 1 elsewhere).
2. Q-C5a (2) restated as a BOUND: with the batch fixed, plan-plus-transient depends only on the
   transform (line) length and the batch; measure at 1080p, 4K, 5.3K along both axes with the
   plan cache AND the pool cleared first; `memory_estimate_bytes` for a gated GPU job adds the
   bound for the clip's LONGER side; a test asserts each measured peak is under it.
3. Condition (1) unchanged; the fixed-budget projection rule for the max-parameter row stands.
   **Binding for task 6 AND task 10: every peak is taken with the plan cache and the pool
   cleared first.** The report gives plan size following transform length, not shape, as the
   reason the bound is per line length. Task 10's 5.3K row is the measurement of record; a
   peak above AD-1's estimate is a STOP. Each heavy run is its own WINDOW REQUEST.

### Task 6 under (A), as built (cell 5, `17743ec`)

- **Batching.** `FFT_BATCH_LINES = 512` lines (1-D transforms) per batch: `512 // C` positions
  along the other spatial axis, each with its C channels (so a batch never exceeds 512 lines
  and the bound holds for RGB calls too); `fft_batch_starts` steps by the batch and makes the
  last batch the final positions.
- **FINDING (fixed in the route): odd FFT lengths are batch-position dependent in cuFFT.** The
  first build was bit-identical at 1080p but NOT at 4K / 5.3K (1 ulp on the last batch's rows).
  Isolated: `cupyx.scipy.fft.rfft` at length 4725 (odd; cupyx's `next_fast_len` includes 7) of
  rows `[1649:2161]` differs from the same rows of the whole-array transform; at an even start
  or an even length it is equal. Over ten lengths, every odd one (4725, 6561) was
  position-dependent and every even one position-independent. The route now takes the
  smallest EVEN fast length; then chunked equals unchunked bit for bit on every required shape,
  CPU and GPU (pinned by tests).
- **The bound.** `fft_memory_bound_bytes(h, w) = 48 B x 512 x length` with `length` the power
  of two at or above `longer + 2 * (shorter + 1)` (every spatial fraction of both methods is at
  most 0.25, so every gated radius is at most the short side plus one); 0 below the gate's
  shape. 96 / 192 / 384 MiB at 1080p / 4K / 5.3K. `CupyBackend.memory_estimate_bytes` = AD-1's
  base + the bound; `NumpyBackend`'s unchanged.
- **Measured (plans and pool cleared first; FFT-specific = peak - base - the two passes'
  full-size outputs, which the direct filter also allocates):**

| size | sigma (fraction) | C | FFT-specific peak | plans held after | bound |
|---|---|---|---|---|---|
| 1080p | 54 (0.05) | 1 / 3 | 34 / 33 MiB | 15 MiB | 96 MiB |
| 1080p | 270 (0.25) | 1 / 3 | 45 / 52 MiB | 13 MiB | 96 MiB |
| 4K | 108 (0.05) | 1 / 3 | 67 / 67 MiB | 30 MiB | 192 MiB |
| 4K | 540 (0.25) | 1 / 3 | 89 / 105 MiB | 25 MiB | 192 MiB |
| 5.3K | 232 (0.05) | 1 / 3 | 111 / 124 MiB | 54 MiB | 384 MiB |
| 5.3K | 1162 (0.25) | 1 / 3 | 227 / 255 MiB | 112 MiB | 384 MiB |

  Ratio to `512 x length x 4 B` at most 8.91; the constant is 12 samples. Against the unbatched
  route at 5.3K (about 1.05 GiB per one-plane call) the batched one needs 0.11 GiB.
- **Tests (+ to `tests/test_wp321_fft_gaussian.py`):** the batch starts; chunked bit-identical
  to unchunked (`FFT_BATCH_LINES` patched to 10**9) at (1080, 1920), (1081, 1923, 3), (2160,
  3840), (2161, 3843, 3), (4648, 5312), (4649, 5313) sigma 1162 on the GPU, the first two on the
  CPU; the bound 0 below the gate and the CPU estimate unchanged; per size, fractions 0.05 and
  0.25, C 1 and 3: the GPU estimate is base + bound and the measured peak (plans and pool
  cleared first) is under the bound. Task 6 tests 43 passed; light set 2,169 passed; slow V8
  and 4K CPU bound 7 passed; ruff, format, mypy clean.
- **OPEN (for the orchestrator): `select_backend` still decides on AD-1's base estimate.**
  It calls `memory.memory_estimate_bytes`, not the backend's method; folding the bound into the
  decision changes `test_core_select.py`'s pinned 4K figures (its "1,982 MiB exceeds free 1,981
  MiB" threshold and IF-2's own example text), which only a ruling may change. Recommended:
  leave the decision on the base (the bound is at most 384 MiB at 5.3K under the 1.25 margin)
  and let task 10's measured 5.3K peak against the GPU estimate settle it.

### Orchestrator answer to yield 14, and CHARC `72becf26`

- The release in `_run`'s `finally` is ACCEPTED (orchestrator) and CONCURRED (CHARC `72becf26`):
  it covers every export job, photos included; it runs after `_video` joins the analysis
  thread; a raising release never replaces the outcome. Task 6's gate, route and release are as
  ruled.
- **OPEN, OUT OF SCOPE:** the GUI preview's FFT plans (a preview of 1080 or more on its short side
  meets the gate; no job end releases its thread's plans). ACCEPTED as CHARC's register row,
  binding WP4.3, written at the accept. Not this package's to fix.
- **Seat plan:** finish (a) the batching, (b) the estimate fold and its bound test with the light
  set (both done, `17743ec`), (c) the memory re-read and the oracle legs in windows, recorded;
  after the WINDOW RELEASED write RESUME HERE for cell 6 (Reviewer A, the two-leg suite, task
  10) and stand down. CHARC's seat rule: past about 330K before the memory re-read window, the
  handover comes FIRST and cell 6 runs the window.

### Task 6 memory re-read (EXCLUSIVE window, OPEN 09:47:52Z (orchestrator correction); development evidence)

Driver `work\wp3.21\fft_memory.py` (uncommitted), log `logs\fft-memory-1.log`, JSON
`microtiming\fft-memory-GX011627-20261028T094758Z.json`, EXIT 0. c3 render, plans and pool
cleared before each peak (the binding method); "max" = all five spatial fractions at their
maxima. The peak is over the input frame; the estimate is the GPU backend's (base + bound).

| input | parameters | render peak | persistent plans | transient | estimate (base + bound) | render FFT / direct |
|---|---|---|---|---|---|---|
| 4K GX011627 frame 0 | default | 908 MiB | 30 MiB | 878 MiB | 2,174 (1,982 + 192) | 0.207 / 0.388 s |
| 4K GX011627 frame 0 | max | 947 MiB | 69 MiB | 878 MiB | 2,174 | - |
| 5.3K 8:7 synthetic | default | 2,710 MiB | 97 MiB | 2,614 MiB | 6,281 (5,897 + 384) | 0.777 / 2.930 s |
| 5.3K 8:7 synthetic | max | 2,798 MiB | 184 MiB | 2,614 MiB | 6,281 | - |

- Every peak plus its input is under the GPU estimate; the max-fraction 5.3K row is inside the
  card by a wide margin, so the fixed-budget projection rule is not triggered.
- Render-level saving at 4K: -0.181 s/frame (0.388 -> 0.207), the micro-timing's -0.180
  projection confirmed on the product render; at 5.3K -2.15 s/frame. These are render figures
  (one frame, median of 10), not the job's; task 10 has the figures of record.
- At 5.3K the mask blur (0.01 x 4648 = 46.5 px) also meets the gate, hence 97 MiB of plans.

### Task 6 oracle legs (cell 5; each heavy leg its own EXCLUSIVE window; development evidence)

Script `work\wp3.21\oracle-fft.sh` (uncommitted, `--device-frames`, candidates `cand-fft-*`
against the `ref-*-a` base references), logs `work\wp3.21\logs\oracle-fft-<step>.log`.

| step | window | clip | expected | verdict | max abs / mean abs |
|---|---|---|---|---|---|
| wp23 | light, 09:50:52-09:51:57Z | WP2.3 x5 x {GPU, CPU} | TIER1 | TIER1 x10 | 0 / 0 |
| gx | OPEN 09:50:27Z; ran 09:52:10-09:56:36Z | GX011627 c3 | TIER2 | TIER2, 681 frames, 23 measured | 7.06e-6 / 7.95e-7 |
| synth | OPEN 09:57:36Z; ran 09:57:48-09:58:46Z | synthetic 4K c3 | TIER2 | TIER2, 120 frames, 4 measured | 2.44e-6 / 2.62e-7 |
| gxa | OPEN 09:59:11Z; ran 09:59:27-10:03:22Z | GX011627 ancuti2018 | TIER1 | TIER1, 681 frames | 0 / 0 |

- Every EXIT and COMPARE-EXIT 0. For gx and synth (no `--require-tier1`), a TIER2 verdict implies
  equal statistics records, proxies, source statistics, analyze and closed_form calls and frame
  pts (each difference is a FAIL reason, `tools/export_oracle.py` 555-594); checked directly for
  gx on the two `oracle.json` files: renders 681 equal, proxies 681 equal, source statistics
  equal, analyze calls 1,362 equal, pts equal. Only the frames differ.
- **Quantised difference (MANDATORY, CHARC `173aa880`; light, cell 5)** on gx's 23 sampled float32
  frames (572,313,600 channel values), by the PRODUCT's rule: the sink's quantiser
  (`CupyBackend.rgb_to_planes`, the device twin of `clearwater.color.rgb_to_planes`, D39) clips
  to [0, 1] in float32, scales by `float32(2**b - 1)` and rounds HALF TO EVEN (`rint`), checked
  in the code (`core/backend.py` `rgb_to_planes`). It is NOT AD-5's `floor(x * 255 + 0.5)` (that
  rule is the analysis proxy's).
  - **8-bit: 14,858 values changed (2.60e-5), max 1 code value.**
  - **10-bit: 60,692 values changed (1.06e-4), max 1 code value.**
  - For reference, by AD-5's rule in float64: 8-bit 14,856, 10-bit 60,459, max 1 (an earlier
    float32 AD-5 run gave 14,793 at 8-bit; superseded by the product-rule figures above).
- **Report wording (CHARC, relayed):** the oracle compares FLOAT32 pre-encode frames, so the
  report never says "no exported pixel changes"; it says: "the render differs by at most 7.06e-6
  (about 0.002 of an 8-bit code value) before quantisation; after quantisation a pixel changes
  by at most one code value, and only where the float sits within that distance of a rounding
  boundary; not measured on the encoded output." (The quantised figure above may be added.)

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

Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.21\rN\` (prompt, diff, transcript,
adjudication, repro, md5s). Runner copied from WP3.14 r2; WSL, codex-cli 0.162.1.

| Round | Critical | Major | Minor | In / out of envelope | New / reopened | Reverts | Product or test-only | Transport / CLI | Depth |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | 6 reported; 1 confirmed blocking (F5), F2 pending a ruling | 5 reported (+ F3, F6, F7 adjudicated minor) | in: F1-F9; out: F10, F11 (banked) | all NEW | 0 | PRODUCT (F5 `jobs/export.py`, `9d73fe4`) + tests | WSL, 0.162.1, gpt-6.1-sol high | 140,415 |
| 2 | 0 | 0 | 1 (test helper race) | in | NEW | 0 | test-only (cleanup) | WSL, 0.162.1, gpt-6.1-sol high | 179,866 |

### Round 1 (cell 6; HEAD `aa06584`, diff `d1e4537..aa06584` without `docs/proofs`)

Probe 10:07:51Z READY; review exit 0 10:34:00Z; banner `gpt-6.1-sol` / high; tokens 230,580;
62 `succeeded in`; VERDICT `NEW_CRITICAL_MAJOR_FOUND`. ERROR lines: 7 background model-list
refresh timeouts (`codex_models_manager`, also in the probe; not transport), the rest echoed
source. Round COUNTS. Pre-run: ruff, format, mypy clean; light set 2,641 passed (420 s).

- F1 (MAJOR) analysis failure vs a blocked write: REJECTED (the double's write blocks forever;
  the product write blocks only on FFmpeg back-pressure; E sees A's text at its next record).
- F2 (MAJOR) `sink.abort()` before A is joined: CONFIRMED against R0.2's design TEXT, no
  guarantee broken; proposed MINOR, keep abort-first and correct the text (QUESTION to the
  dispatcher; alternative: move `analysis.stop()` before `sink.abort()` in `_video`).
- F3 (MAJOR) expired 60 s join: MINOR, banked (a stall >= 60 s inside one frame; the base's
  serial job hangs on the same stall; WP3.14's envelope names it out); report Limits.
- F4 (MAJOR) complete entry after a cancel: REJECTED (V17; the base's documented behaviour;
  my prompt over-stated claim 2).
- F5 (MAJOR) D87 growth 0 on a resumed incomplete entry: CONFIRMED MAJOR, in envelope
  (repro `growth_bytes 0 frames_remaining 100`; byte-identical `store_proxy` adds nothing).
- F6 (MAJOR) oracle TIER2 with no measured frame: CONFIRMED MINOR (tool; no recorded verdict
  affected). F7 junction aliasing: MINOR, DR-22 precedent, harden in cleanup. F8 `--name`
  escape: MINOR. F9 test sleeps: MINOR. F10, F11: OUT-OF-ENVELOPE, banked.
- Remediation plan (next turn, after the dispatcher's word): F5 in `jobs/export.py`
  (extrapolate from the entry's bytes per stored frame when the lead stored nothing new) with
  a failing-first test; F2 per the ruling; the minors once in the terminating round.

Dispatcher rulings on round 1 (relayed at the r1 yield, depth 140,415): F5 CONFIRMED
BLOCKING, fix as adjudicated with a failing-first retry test; F2 RULED (a): keep abort-first,
MINOR, correct the design text in the report, pin abort -> A joined -> release with one test;
F1/F4 rejected and F3 banked to Limits accepted; F6-F9 to the terminating round's cleanup;
F10/F11 banked.

Remediation `9d73fe4`: `_Analysis.cache_growth_bytes` scales the entry's own bytes per stored
frame when the lead stored nothing new; tests
`test_the_re_check_on_a_retry_over_an_incomplete_entry_scales_its_own_bytes` (FAILED on the
r1 engine: `0 == 23,040`) and `test_a_failing_job_aborts_then_joins_the_analysis_then_releases`
(an event holds A alive until the abort; passes on both, it pins the ruled order). Overlap file
25 passed; the two tests x6 passed; ruff, format, mypy clean; light set 2,643 passed (426 s).

### Round 2 (cell 6; HEAD `9d73fe4`, diff `aa06584..9d73fe4`, scoped)

Exit 0 10:57:28Z; banner `gpt-6.1-sol` / high; tokens 75,977; 18 `succeeded in`; VERDICT
`NO_NEW_CRITICAL_MAJOR`; 3 background model-list refresh timeouts (not transport). Round COUNTS.

- r2 F1 (MINOR, EXECUTED): `_analysis_decoded` iterates `source.threads` while E's stream
  registers its tag: CONFIRMED, test-only; snapshot under the source's lock in cleanup.
- The reviewer's probes confirmed the growth arithmetic (10 cases, 23,040 bytes) and the order
  abort -> join -> release.
- **ZERO NEW BLOCKING: the loop TERMINATES at round 2.** Cleanup (once, never another round):
  r2 F1; r1 F6, F7, F8, F9.

### Cleanup (terminating round, once; dispatcher GO at depth 179,866; `1df2626`)

Tools and tests only; every new test run failing-first against the previous tools (12 failed,
the measured-sample TIER2 case passed on both).

- r1 F6: `export_oracle.compare` adds a FAIL reason when frames differ and none was measured
  (`test_differing_frames_with_none_measured_fail`; the unmeasured test now pairs one unmeasured
  frame with a measured one and stays TIER2). **No recorded verdict changes:** every recorded
  TIER2 leg measured frames (gx 23 of 681 differing, synth 4 of 120); every TIER1 leg had no
  differing frame, where the new reason cannot apply.
- r1 F7: `export_oracle.refuse_inside` (via `path_forms`) and `analysis_breakdown.refuse_inside`
  compare the lexical AND the `os.path.realpath` forms (a link or junction to the footage
  folder is refused); tests patch `realpath` to alias a folder (portable, no link created).
- r1 F8: `export_oracle.record_name`: `--name` must be one plain component (not empty, `.`,
  `..`, absolute, a drive, or holding a separator), checked before anything is made.
- r1 F9: the planted short lead, the blocked write and the analysis-failure-mid-export tests
  hold the analysis with an EVENT (`_hold_analysis`, released by the abort or by five
  rendered frames), never a sleep. Residual, banked: the 2 ms pacing sleep stays in the rig
  for the overlap-observation tests (equality, warm, CPU path); a race there fails loudly
  (`the export started only after ...`), never passes vacuously.
- r2 F1: `_Streams` registers each stream's thread under its lock and `_analysis_decoded`
  snapshots threads and events under the same lock.
- Gates: ruff, format, mypy clean; the five barrier tests x5 passed; light set (every
  `*_deps.py` / `*_rules.py`) 2,655 passed (455 s).

**Reviewer A: CONVERGED at round 2** (r1: 1 confirmed blocking, fixed in product code;
r2: 0 blocking). Banked for the report's Limits: r1 F3 (an analysis stalled >= 60 s inside one
frame), F2 (abort-first, ruled (a); the design text corrected in the report), F10, F11 (out of
envelope), the F9 residual pacing sleep.

## Two-leg suite (GATE_CHECKS; cell 6)

### Parallel leg (EXCLUSIVE window, OPEN 11:13:30Z per the orchestrator; HEAD `012641e`)

`( cd <worktree> && unset PYTEST_ADDOPTS && export QT_QPA_PLATFORM=offscreen && uv run pytest
-q -rs -n 4 -m "not gpu and not footage and not gui and not slow"
--basetemp=work/wp321-suite-parallel > work/wp321-suite-parallel.log 2>&1; echo EXIT=... >
work/wp321-suite-parallel.done )`, started 11:13:42Z, done marker `EXIT=0 2026-10-28T11:23:18Z`.

- **4,147 passed, 1 skipped, 5 warnings in 575.06 s**; collected 4,148 of 5,259 (1,111
  deselected; `--collect-only` with the same marker).
- The one skip, pre-existing (WP3.14 and WP-T4 ledgers carry it):
  `tests\test_color_roundtrip.py:121: swscale reads a yuvj format as full whatever in_range
  says (refused instead)`.

### Oracle-candidate cleanup (orchestrator grant at the parallel-leg OPEN)

Deleted under `C:\Users\rwsmy\clearwater\work\wp3.21\oracle\` (superseded by `cand-fft-*`),
27 folders, about 11 GB: `cand-devframes-{GX011627-c3, synth4k-c3, hevc10-c3-cpu/gpu,
hevc8-bt709-full-c3-cpu/gpu, rotated-c3-cpu/gpu, truncated-c3-cpu/gpu, vfr-c3-cpu/gpu}` (12),
`cand-ad29-*` the same 12, `cand-i2-{GX011627-ancuti2018, GX011627-c3, synth4k-c3}` (3). List in
`work\wp3.21\logs\c6-oracle-cleanup.txt`. Not touched: every `ref-*` (26), every `cand-fft-*`
(13), and `cand-devframes2-*`, `cand-overlap-*`, `cand-p3-*` (outside the grant's globs). C:
free 26 GB before (19 GB at the request), **37 GB after**.

**Orchestrator's record (serial grant, item 2):** the superseded candidates were deleted WHOLE
under the orchestrator's ORIGINAL grant; its amendment (keep each `oracle.json`) crossed the
delete (the orchestrator's slip, as it records). The verdict lines survive in
`work\wp3.21\logs\{devframes-gx,ad29-gx,interim2}-*.log` (and the WP2.3 legs in
`oracle-{ad29,devframes}-wp23.log`); every `ref-*` and `cand-fft-*` folder is intact.

**Amendment arrived AFTER the delete (orchestrator, keep `oracle.json` and small text files):**
the whole folders were already removed (`rm -rf`, not recoverable), so the 27 `oracle.json`
records behind H7-H14 are LOST. What survives (uncommitted, under `work\wp3.21\`): the run logs
with each leg's `ORACLE` summary and `VERDICT` line -- `logs\oracle-ad29-wp23.log` and
`logs\oracle-devframes-wp23.log` (10 + 10, all TIER1 max abs 0), `logs\ad29-gx-{1,2}.log`,
`logs\devframes-gx-{1,2}.log`, `logs\interim2-{2,3,4}.log` (each one VERDICT, TIER1, 681 or
120 frames, 0 differing), and the driver scripts `oracle-ad29-*.sh`, `oracle-devframes-*.sh`,
`interim2.sh`. The `ref-*` references the legs compared against are intact, so any leg can be
re-recorded from its script if a record is needed.

### Serial leg (EXCLUSIVE window, OPEN 11:25:28Z per the orchestrator; HEAD `fc947b5`)

`( cd <worktree> && unset PYTEST_ADDOPTS && export QT_QPA_PLATFORM=offscreen && uv run pytest
-q -rs -m "gpu or footage or gui or slow" --basetemp=work/wp321-suite-serial > ... )`, started
11:26:05Z, done marker `EXIT=1 2026-10-28T12:09:30Z`; log `work\wp321-suite-serial.log` (worktree).

- **1 failed, 1,109 passed, 1 skipped, 4,148 deselected in 2,603.17 s** (collected 1,111).
- Skip: `tests\test_photo_check.py:139: the footage folder has no photos yet (WP3.6P is
  queued)`. Against WP-T4's accepted serial leg (1,036 passed, 10 skipped): its other 9 skips
  were `test_methods_assembly_v8.py:44` (look-check frames absent from a gate worktree); this
  worktree's `clearwater.local.toml` points `working_path` at the main tree's `work\`, where
  `wp1.3\frames` exist, so the 9 V8 tests RAN and passed. 1,111 vs 1,046 collected: the
  package's own gpu/footage/slow tests plus what merged after WP-T4.
- **FAILED `tests/test_prototype_backend.py::test_bench_gpu_records_graphics_memory`**
  (`:345`, `assert 0.133 >= 1.0` on `estimate.ratio_to_gpu_pool_reserved`). Alone it passes
  (60 s). **Cause, reproduced:** the product's FFT route (task 6) leaves cuFFT plans in the
  calling thread's plan cache, holding pool blocks that `free_all_blocks` cannot free, until a
  job end calls `release_fft_plans`. `test_methods_assembly_v8.py` (gpu/slow, 1080 x 1920 crops,
  so the gate routes its blurs to the FFT) runs earlier on pytest's main thread; the prototype
  bench then counts those plans as its reserved pool. Repro 1:
  `pytest -m "gpu or slow" tests/test_methods_assembly_v8.py <the test>` -> 9 passed, 1 failed
  (`0.139`), log `work\c6-proto2.log`. Repro 2 (`C:\Users\rwsmy\clearwater\work\wp3.21\proto_plans_repro.py`):
  fresh ratio 1.669 (reserved 1.9 MiB); after one 4K FFT blur 0.100 (32.1 MiB); after
  `release_fft_plans` 1.668 (1.9 MiB).
- This is the suite-level face of the out-of-scope GUI-preview plan item (CHARC register row,
  WP4.3): any non-job caller keeps its thread's plans. The failing test, the V8 test, the
  prototype bench and `tests/conftest.py` are all unowned; **STOP** to the dispatcher with
  options (recommended first): (A) grant an autouse fixture in `tests/conftest.py` that, after
  each test, calls `release_fft_plans` on the GPU backend only if `cupy` is already imported
  (no import otherwise); (B) product, owned `core/backend.py`: no plan outlives a
  `gaussian_blur` call (plans built per call; costs plan creation per blur, needs a timing
  window, and moots `release_fft_plans`); (C) a CHARC ruling on the existing test.

## RESUME HERE (cell 7, after cell 6) -- SUPERSEDED by RESUME HERE (cell 8) at the end

**State:** branch `wp3.21` on base `d1e4537`, NO rebase; worktree CLEAN at the ledger head.
Cell 6's commits: r1 ledger `b1bb9cc`; F5 fix + order test `9d73fe4`; r2 ledger `047656f`;
cleanup `1df2626`; ledgers `012641e`, `fc947b5`, `f141354`, `70ae22d`, this one.
**Reviewer A CONVERGED at round 2** (sections "Round 1", "Round 2", "Cleanup" above;
evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.21\r1\`, `r2\`). Banked for the report's Limits:
r1 F3 (analysis stalled >= 60 s in one frame), F2 abort-first (ruled (a): correct R0.2's
"E joins A before the sink's abort" in the report; the order abort -> A joined -> release is
pinned), F10, F11 (out of envelope), the F9 residual 2 ms pacing sleep.
**Suite:** parallel leg PASSED (4,147 / 1 skipped, the accepted `test_color_roundtrip.py:121`);
serial leg 1 FAILED, the STOP above. On the dispatcher's ruling: apply it, re-run what the
ruling names (at least the V8 + prototype pair, then the serial leg in a window).
**Then:** task 10 (RESUME HERE (cell 6) item 3, unchanged), the report (item 4: add Reviewer A's
rounds, the corrected R0.2 order, the Limits above, and the plan-cache finding), the return
report. Standing rules: as in RESUME HERE (cell 6). Never write `\a`, `\b` etc. in a non-raw
Python literal in ledger scripts (a BEL slipped in at `f141354`, fixed `70ae22d`).

## Cell 7: the serial-leg fix under CHARC ruling (A) (`21e6d24562923b10`)

**Ruling (A), conditions in substance:** `tests/conftest.py` GRANTED for ONE autouse fixture that
releases the FFT plans after each test; it imports nothing new, acts only when `cupy` is already
in `sys.modules`, releases through `core`'s own `release_fft_plans`, never touches `cupy`; the
footage guard and the WP-T4 docstring paragraph untouched, the AST outside the fixture unchanged
(proved by `ast.dump`); a test pins it; the V8 + prototype pair re-run light; the serial leg
again in its own window; the parallel leg's collection checked, not re-run. (B) and (C) refused.

**Built (`57a7a2e`):** `tests/conftest.py` gains `_release_fft_plans` (autouse,
`request.addfinalizer`); at teardown it reads `sys.modules` (a local `import sys`, a builtin
already loaded) and acts only when `cupy` and `clearwater.core.backend` are both loaded and
`_probe_gpu` has been called once (`cache_info().currsize`), then calls the probed
`CupyBackend.release_fft_plans()`. The cache is per thread, not per backend object, so this also
clears plans another `CupyBackend` made on pytest's thread. Not covered: a process that makes
plans through a directly built `CupyBackend` (only `tools/core_speed.py` does) before any probe.
Pin: `tests/test_wp321_conftest_release.py` (2 `gpu` tests in file order: the first leaves plans
on the thread, the second asserts none at its start).

**Evidence (worktree `work\`):**

- Failing first, base conftest, HEAD `ea78946`: `pytest -q -rs -m "gpu or slow"
  tests/test_methods_assembly_v8.py tests/test_prototype_backend.py::test_bench_gpu_records_graphics_memory`
  -> **1 failed, 9 passed in 100.81 s**, `assert 0.13908809301536113 >= 1.0` at `:345`
  (`c7-pair-before.log`, 12:25:41Z-12:27:23Z).
- With the fixture: the same pair -> **10 passed in 101.33 s** (`c7-pair-after.log`,
  12:28:50Z-12:30:32Z).
- The pin with the fixture disabled (base conftest restored for the run, then the new file back,
  `cmp` equal): **1 failed, 1 passed**, `assert (6 == 0)` (six cached Plan1d)
  (`c7-pin-disabled.log`); with it: passed in the light set.
- AST (`c7-ast-proof.txt`): base `d1e4537` vs new with the one `FunctionDef` removed, 20
  top-level nodes each, `ast.dump` equal, module docstring equal (EXIT 0).
- Light set: `test_wp321_conftest_release.py`, `test_wp321_fft_release.py` and the seven
  `*_deps.py` / `*_rules.py` -> **86 passed** (`c7-light.log`). Static: ruff check, ruff format
  --check (249 files), mypy (138 source files) clean (`c7-static.log`).
- Collection (condition 3): parallel set `4148/5261 collected (1113 deselected)`, node ids
  IDENTICAL to cell 6's `wp321-collect-parallel.log` (4148/5259; `diff` of the sorted ids empty,
  `c7-collect-parallel.diff`), so the parallel leg is not re-run. Serial set `1113/5261`
  (`c7-collect-serial.txt`): cell 6's 1,111 plus the pin's 2.
- Disk 36 GB free on C:, RAM 10 GB free at 12:31Z.

**For the record (CHARC, in its words):** the serial leg's single skip against WP-T4's ten is
explained because this worktree's `working_path` points at the main tree's `work/`, so the
look-check frames exist and the nine V8 tests RAN and passed; the collection 1,111 against 1,046
is this package's tests plus those nine.

### Serial leg 2 (EXCLUSIVE window, GRANTED 12:33Z; HEAD `afad7af`)

`( cd <worktree> && unset PYTEST_ADDOPTS && export QT_QPA_PLATFORM=offscreen && uv run pytest
-q -rs -m "gpu or footage or gui or slow" --basetemp=work/wp321-suite-serial2 > ... )`, started
12:33:42Z, done marker `EXIT=0 2026-10-28T13:18:05Z`; log `work\wp321-suite-serial2.log`.

- **1,112 passed, 1 skipped, 4,148 deselected, 1 warning in 2,661.52 s (0:44:21)**; collected
  1,113 (serial leg 1's 1,111 plus the pin's 2). No failure: the bench test now passes after
  the V8 file in the same process.
- Skip: `tests\test_photo_check.py:139: the footage folder has no photos yet (WP3.6P is queued)`.
- With the parallel leg's 4,147 passed / 1 skipped (node ids unchanged), the two-leg suite is
  GREEN at `afad7af`.

### Task 10 preparation: GX011627's GOP (light, read-only, 13:20Z)

`ffprobe -select_streams v:0 -show_entries packet=pts,flags` on the clip through
`find_footage_file` (video stream only; no tag read), script in the session scratchpad, output
`work\wp3.21\logs\c7-gop-GX011627.txt`: 681 packets, decode order equals presentation order (no
B-frames), keyframes every 30 frames (0, 30, ..., 660). **Frame 0 is a keyframe; 323 and 387 are
NOT** (nearest 300/330 and 360/390), and 64 is not a multiple of the GOP. So decoder seeking or
keyframe decode does not explain 323 / 387; the placement waits on task 10's per-frame records.

## Task 10: the V16 re-measure (EXCLUSIVE windows; figures of record)

Code at `57a7a2e` (the last code commit; the branch head carries ledger commits only). Records
under `C:\Users\rwsmy\clearwater\work\wp3.21\bench\`, logs and summaries under the worktree's
`work\wp3.21\logs\c7-v16-*`. Summaries by a scratchpad script (`v16_rows.py`) reading the JSON.
Header for every row below unless stated: device frames ON (`--device-frames`), hw_decode ON
(the job sets it for a GPU backend), backend `CupyBackend(device='cuda:0')`, result device GPU,
encoder auto (`hevc_nvenc`, NVENC proof tied) unless libx265, Standard, 8-bit.

### Block 1: GX011627 (window GRANTED 13:23Z; ran 13:23:17Z-13:52:07Z, EXIT 0; OFF row 13:52:23Z-13:59:15Z, EXIT 0)

`tools/export_bench.py v16 --device-frames --subdir wp3.21/bench --clip GX011627` (record
`export-bench-v16-gx011627-20261028T132317Z.json`, log `c7-v16-gx27.log`, summary
`c7-v16-gx27-summary.txt`); then the OFF row `run GX011627 --runs 1 --cache cold --method c3
--subdir wp3.21/bench` (no `--device-frames`; record `export-bench-GX011627-20261028T135223Z.json`,
`c7-v16-gx27-off*.{log,txt}`). One process per command (the OFF row a fresh process).

| row | s/frame | min/min | per-frame median / p90 / max | first | lead s / record wait s / share | peak RSS MiB | peak GPU MiB |
|---|---|---|---|---|---|---|---|
| c3 cold 1 | 0.3195 | 9.57 | 0.2895 / 0.3219 / 0.6018 | 0.812 | 5.36 / 10.73 / 7.39 % | 3,394 | 3,244 |
| c3 cold 2 | 0.3264 | 9.78 | 0.2966 / 0.3316 / 0.6244 | 0.733 | 5.04 / 11.38 / 7.39 % | 3,417 | 3,142 |
| c3 cold 3 | 0.3310 | 9.92 | 0.3016 / 0.3339 / 0.6878 | 0.807 | 5.27 / 11.50 / 7.44 % | 3,396 | 3,130 |
| c3 warm (cache complete at start) | 0.3022 | 9.06 | 0.2963 / 0.3185 / 0.3585 | 0.694 | 1.56 / 0.10 / 0.81 % | 2,456 | 2,601 (a) |
| ancuti2018 cold | 0.2917 | 8.74 | 0.2553 / 0.2708 / 1.2119 | 0.611 | 7.74 / 15.42 / 11.66 % | 3,396 | 3,014 |
| c3 libx265 cold (NVENC not tied, as expected) | 0.4869 | 14.59 | 0.4257 / 0.5518 / 3.5933 | 0.775 | 5.39 / 1.56 / 2.10 % | 4,963 | 2,761 |
| c3 cold, device frames OFF | 0.5757 | 17.25 | 0.5363 / 0.5737 / 3.0895 | 1.073 | 19.72 / 8.77 / 7.27 % | 4,017 | 2,925 |

- **Every NVENC row meets D106's interim 25 min/min; cold c3 at 4K meets the ~10 min/min aim**
  (9.57-9.92; baseline 31.8-31.9). Clocks before each run SM 210 MHz idle (the first run 1,980,
  from the GOP probe), temperatures 52-69 C, memory.used 248-335 MiB between runs. Strays: none
  except the libx265 row (`System` 41.5 % CPU, kept as spread) and the OFF row (`System` 29.1 %).
- (a) **Warm row, method RULED (a) (CHARC FINAL `522229f57cbc6870`, 13:24Z):** its GPU peak is
  the product's own state after an analysis, pool and all; the prime makes no FFT plans (its
  proxies are below the 1080 gate); the bench ran unchanged, (b) not taken. The STOP check stays
  on the cold rows.
- ON vs OFF on cold c3 (#2 device frames + #3 device block mean, which need device frames): 0.3195-0.3310
  against 0.5757 s/frame, about -0.25 s/frame; the OFF row's lead is 19.7 s against 5.0-5.4 s
  (the host block mean in the analysis pass).

**The recurring slow frames, placed (CHARC `b4c143d7` 2):** the GOP check (above) rules out
keyframes for 323 / 387. In every cold device-frames row the slow frames (> 1.6 x median) recur
EVERY 16 FRAMES (c3: 19, 35, 51, ..., 611 in all three runs, about 0.52-0.69 s against a median
of 0.29-0.30; ancuti2018: 5, 21, 37, ..., 581) and STOP at the frame where the analysis thread
returned (the frame whose interval ends after `analysis_end_s`: 611 in each c3 run, 581 for
ancuti2018). The warm row (no analysis decode pass to wait on) has NONE besides frame 0. The
record wait (the frame loop's time inside `smoothed_record`) sums to 10.7-11.5 s, about the
excess of those 37 frames (37 x ~0.27 s). Cause: `analysis/engine.py` `STREAM_STEP = 16`, the
streamed analysis advances its smoothed records every 16 first-stage records; with the FFT the
frame loop now outruns the analysis (c3: analysis ends at 197-205 s of a 218-225 s job), so the
export waits at each advance. Interim 2's 323 and 387 are on this cycle (19 + 16 k). Frame 0 is
the first-frame cost (keyframe, plan creation, NVENC start). **No fix:** a smaller step would not
make the analysis faster (the job is analysis-bound during the overlap; the step only sets the
grain of the waits, at most one step of about 4.6 s at the end) and would add the store's whole-axis copies
per advance (`smooth_at`, the constant's docstring); the next gain is the analysis pass itself (a report finding).

### Block 2: synthetic 5.3K 8:7 c3 cold (window GRANTED 14:03Z; ran 14:03:10Z-14:06:51Z, EXIT 0)

`v16 --device-frames --subdir wp3.21/bench --clip synthetic-5k3` (a fresh process, its first
job; record `export-bench-v16-synthetic-5k3-20261028T140310Z.json`, log `c7-v16-5k3.log`,
summary `c7-v16-5k3-summary.txt`, GPU timeline `c7-v16-5k3-gpu-timeline.txt`).

| row | frames | s/frame | min/min | per-frame median / p90 / max | first | peak RSS | peak GPU |
|---|---|---|---|---|---|---|---|
| baseline (WP3.14) | 150 | 4.5389 | 136.03 | 3.714 / 4.006 / 4.438 | - | 6,354 MiB | 6,104 MiB |
| WP3.21 | 150 | 1.1830 | 35.46 | 1.0691 / 1.1167 / 1.6372 | 1.973 | 7,405 MiB | **7,854 MiB** |

- Phases: probe 6.18, lead 6.96, open 0.59, frames 162.73, close 0.94 s; the analysis thread
  returned at 78.9 s (frame 57); record wait 0.03 s. Peak tree RSS at 48 s: python 1,227 MiB +
  three `ffmpeg.exe` of 2,086 / 2,006 / 2,086 MiB (N4's 16 GB held).
- **GPU (nvidia-smi `memory.used`, device-wide, 1 s samples; idle before 248 MiB):** 2,110 at
  12 s; **7,853-7,854 from 18 s to about 55 s** (the overlap: both decoders, the analysis thread
  and the render); 6,718 at 60 s, 6,606 at 72-78 s, **6,598 plateau from about 84 s** (frames
  only, after the analysis returned); 5,462 from about 162 s. The card has 8 GB (8,188 MiB).
- **STOP (the ruled test, conservative reading, confirmed by the dispatcher at the grant):**
  7,854 MiB is above the GPU estimate 6,281 (5,897 + 384) by 1,573 MiB and above base x 1.25
  (7,371) by 483 MiB; with the 248 MiB idle offset removed it is 7,606, still above both. The
  frames-only plateau (6,598; 6,350 less idle) is also above 6,281. Against the baseline's 6,104:
  x 1.29. The 4K rows are likewise above their baseline (3,130-3,244 against 2,409 MiB, x 1.30-1.35),
  not a ruled STOP. Not attributed yet between CuPy's pool (render, the analysis thread's device
  frames, FFT plans and buffers) and the FFmpeg decoders' and NVENC's own device memory.

**HOLD (dispatcher, after the STOP):** no code change, no window, block 3 held; CHARC has the
options with (A) recommended. In the hold the (A) driver was DRAFTED, not run:
`C:\Users\rwsmy\clearwater\work\wp3.21\memory_attribution.py` (uncommitted; ruff clean). It runs
ONE job through `export_bench.run_once` (the same engine, collaborators, telemetry and record) on
the synthetic 5.3K clip, with in-process samplers: CuPy's default pool `used_bytes` /
`total_bytes` and `cudaMemGetInfo` every 0.1 s, `nvidia-smi --query-compute-apps` every 1 s, each
`gaussian_blur`'s per-thread plan cache, and the engine's stages on the same clock. It places
every sample in a phase (lead / overlap / frames only / close) and summarises, at the
device-wide peak: pool total and used, and the residual (device used - idle - pool total = the
FFmpeg decoders', NVENC's and the extra CUDA contexts' share). `--off` runs the host-frame path
for the same split. Output `work\wp3.21\attribution\`.

### Attribution run, option (A) (CHARC FINAL `e166515f`; window GRANTED 14:12Z; ran 14:14-14:26:51Z)

Driver `C:\Users\rwsmy\clearwater\work\wp3.21\memory_attribution.py` (uncommitted, ruff clean; no
product change). It runs ONE job through `export_bench.run_once` on the synthetic 5.3K clip and
samples in process through the probed backend's `xp`: pool `used_bytes` / `total_bytes`
(cached = total - used) every 0.1 s and after each `planes_to_rgb` / `block_sums` /
`gaussian_blur` / `rgb_to_planes` call with the calling thread's name and plan-cache bytes; each
second `nvidia-smi --query-compute-apps` (WDDM printed `[N/A]` for every pid, so per-pid figures
are ABSENT) and the device-wide `memory.used` (the bench's figure) with the pool read at the same
instant. FFmpeg's share is therefore the **REMAINDER = device-wide - device-wide after this
process's probe (its context) - pool total**. (`cudaMemGetInfo` under WDDM reported 1,121 MiB
used at idle: a per-process budget view, kept as `wddm_used_mib`, not used.) Self-check on the
WP2.3 `hevc8-bt709-full` sample: PASS (`c7-attr-selfcheck3.log`). Logs `c7-attr-{on,off}.log`,
records `work\wp3.21\attribution\attribution-{on-20261028T141721Z,off-20261028T142102Z}.json`.
Both jobs ok, 150 frames; ON 1.257 s/frame (hooks included), OFF 2.154; analysis returned at
91.0 s (ON) / 202.3 s (OFF). FFmpeg children: two `-hwaccel` decoders and one NVENC encoder.

Device frames ON (MiB; device-wide from nvidia-smi, idle after the probe 246):

| moment | device-wide | pool used | pool cached | pool total | plans (in the pool) | REMAINDER (FFmpeg + non-pool) |
|---|---|---|---|---|---|---|
| peak (overlap, 43.5 s) | **7,921** | 3,181 | 1,246 | 4,427 | 97 | 3,248 |
| overlap plateau (median) | 7,905 | 1,838 | 2,553 | 4,427 | 97 | 3,232 |
| frames-only plateau (median) | 7,113 | 944 | 3,483 | 4,427 | 97 | 2,440 |
| overlap - frames only (median) | +792 | +894 | -930 | 0 | 0 | **+792** |
| overlap - frames only (max) | +808 | +2,019 | -283 | 0 | 0 | +1,237 |

Device frames OFF (idle after the probe 261):

| moment | device-wide | pool used | pool cached | pool total | plans | REMAINDER |
|---|---|---|---|---|---|---|
| peak (overlap, 128.2 s) | **7,593** | 666 | 2,962 | 3,628 | 97 | 3,704 |
| overlap plateau (median) | 7,563 | 662 | 2,966 | 3,628 | 97 | 3,674 |
| frames-only plateau (median) | 6,337 | 662 | 2,966 | 3,628 | 97 | 2,448 |
| overlap - frames only (median) | +1,226 | 0 | 0 | 0 | 0 | **+1,226** |

Pool by thread (the 0.1 s and per-call reads): ON pool-used peak 4,005 MiB in the overlap
(analysis thread's calls saw up to 3,570, the render thread's 2,342); OFF 2,540-2,640.
Baselines beside: WP3.14 5.3K 6,104 MiB device-wide (one decoder, no overlap, host frames, the
direct Gaussian); cell 5's 5.3K render pool peak 2,710 MiB (2,798 at the max fractions).

**The split, read (CHARC's ask 3):**
- The overlap's increment over the frames-only plateau is the analysis half's DECODER: it is
  all REMAINDER (OFF +1,226, the pool unchanged; ON +792 median / +1,237 max) and it disappears
  when the analysis decoder exits. The analysis half's device frames and block sums add POOL
  (ON pool total 4,427 against OFF 3,628, about +800; pool used +894 median in the overlap), not
  device-wide on top, because the pool holds what it grew to.
- The frames-only plateau (ON 7,113; OFF 6,337) is pool total 4,427 / 3,628 + remainder about
  2,445 (the export decoder, NVENC, this process's non-pool memory) + idle; of the pool, 3,483 /
  2,966 MiB is CACHED (free blocks the job never returns until its end).
- Against 6,281 at the ON peak (excess 1,640): pool cached 1,246, the analysis decoder about
  790-1,240, the analysis device frames about 800 of pool. Even OFF (no device frames) the peak
  7,593 breaches both bounds: the decoder term alone does. The estimate counts no FFmpeg memory
  (export decoder + NVENC about 2.4 GB here) and AD-1's figure is the render's arrays.
- **Against AD-1's own definition** (`core/memory.py` module docstring: the estimate is of the
  render's arrays, checked against "the pool's reserved peak"; "the CUDA context and library
  workspaces are not counted"; the decoders and the encoder do not exist when the backend is
  chosen): the 5.3K **pool reserved peak is 4,427 MiB ON / 3,628 OFF, UNDER the GPU estimate
  6,281 (x 0.70 / x 0.58) and under the base 5,897.** The breach exists only in the device-wide
  figure the ruled test used, and is FFmpeg's (about 2.4 GB for the export decoder and NVENC,
  plus about 0.8-1.25 GB for the overlap's analysis decoder) plus the context, on top of the pool.
- **Per thread (CHARC's ask 1), stated plainly:** CuPy's default pool is ONE pool shared by
  every thread of the process; no per-thread pool figure is obtainable through the backend. The
  nearest proxy, an ATTRIBUTION BY TIMING, NOT A MEASUREMENT (scratchpad `pool_growth.py`,
  `work\wp3.21\logs\c7-attr-pool-growth.txt`, from the recorded per-call reads): each rise in the
  pool total between two consecutive backend-call reads is credited to the thread whose call
  ended the interval. ON: analysis thread 3,297 MiB (lead 824, overlap 2,473), render thread
  1,130 (overlap); OFF: analysis 1,080 (lead 44, overlap 1,036), render 2,547. Order-dependent:
  a thread that grows the pool first leaves free blocks the other reuses uncounted.

## RESUME HERE (cell 8, after cell 7)

**State:** branch `wp3.21` on base `d1e4537`, NO rebase; worktree CLEAN at the ledger head. Last
CODE commit `57a7a2e` (the ruling (A) conftest fixture + its pin); everything after is ledger.
Cell 7's commits: `57a7a2e`, ledgers `afad7af` .. this one. Reviewer A CONVERGED at round 2
(cell 6). **Two-leg suite GREEN at `afad7af`** (parallel 4,147 / 1 skip, collection unchanged by
the fixture; serial leg 2 1,112 / 1 skip, "Serial leg 2" above). A code change from the fix
ruling re-opens what the ruling names (at least the light set, oracle legs if the render or
analysis path moves, and the suite legs per the fill).

**Task 10 so far ("Task 10" sections above):** block 1 GX011627 DONE (cold c3 9.57-9.92 min/min,
warm 9.06 with its memory method RULED (a), ancuti2018 8.74, libx265 14.59, OFF row 17.25; the
recurring slow frames PLACED: `STREAM_STEP = 16` analysis advances, no fix). Block 2 5.3K: speed
35.46 min/min [136.03], GPU peak 7,854 MiB device-wide above 6,281 and 7,371: **STOP, open.**
Attribution (A) DONE: pool reserved peak 4,427 ON / 3,628 OFF (under the estimate on AD-1's own
definition); the breach is FFmpeg (export decoder + NVENC about 2.4 GB, the overlap's analysis
decoder about 0.8-1.25 GB) plus pool-cached; per-thread pool not measurable (timing proxy given).
**Waiting on CHARC:** the fix ((b3) AD-1 overlap/FFmpeg term is the dispatcher's and cell 7's
reading, pool-cached secondary: (b4) bounded pool or `free_all_blocks` at the analysis-end
boundary) and the instrument for the re-run's STOP test. `core/memory.py` is CHARC's by Q9;
do not change `test_core_select.py` (ruling `16a8ee8a`).

**Then, in order:** the ruled fix (its own gates); re-run block 2 (5.3K) in a window with the
named instrument; block 3 GX011625 LAST in its own window (about 1.5-2.5 h; command as block 1
with `--clip GX011625`, wait by bounded foreground polls of a `.done` marker); the report
`docs/reports/wp3.21-optimisation.md` per RESUME HERE (cell 6) item 4 plus: Reviewer A's rounds,
the corrected R0.2 order (abort -> A joined -> release), the banked Limits (r1 F3, F2, F10, F11,
the F9 residual 2 ms pacing sleep), the plan-cache finding and the conftest fix, the Limits
sentence CHARC ruled ("any caller outside an export job keeps its thread's cuFFT plans until
something calls the release"; the GUI preview is the product case, WP4.3 register row; test
isolation is the fixture; tools exit their process), CHARC's pixel-change wording (never "no
exported pixel changes"), the warm-row label, the STREAM_STEP placement (the job is
analysis-bound during the overlap: the analysis pass is the next target), the 5.3K attribution
and its ruling; then the return report (under about 70 lines) by SendMessage.

**Evidence not committed:** `C:\Users\rwsmy\clearwater\work\wp3.21\bench\` (V16 records),
`...\attribution\` and the driver `work\wp3.21\memory_attribution.py`; worktree
`work\wp3.21\logs\c7-*` (summaries, GOP check, timelines). Standing rules: RESUME HERE (cell 6).

## The task 10 fix (CHARC FINAL `cadc39fc8a199a57`, 14:32Z): (b3) + one boundary free

Ruled: (1) `core/memory.py` gains `job_device_memory_estimate_bytes` = pool estimate (base + FFT
bound) + context + decoders x NVDEC + NVENC, terms per hardware session at the clip's size, from
this attribution; the overlap counts TWO decoders; `select_backend` UNCHANGED; the GPU job
REPORTS it and the STOP test compares the device-wide peak against it. (2) One pool free at the
analysis-end boundary in `jobs/export.py`. (3) The re-run's STOP test names both instruments:
device-wide `memory.used` against the new total (idle offset stated) AND the in-process pool
reserved peak against 6,281. (b2), (b4) not taken. Cell 7 builds the fix and re-runs block 2,
then hands over to cell 8. A light STOP first on the form of the (b3) terms (CHARC's under Q9).

### Part 2, as built (`b5a383c`)

`_Analysis._run`'s `finally` calls `_release_fft_plans(self._backend)` (the job end's entry,
never raises) before `_fold.end()`: once per video job when the analysis thread returns, on
every path, on that thread (its plan cache is empty; the render thread's plans stay). The job's
end still releases on its own thread. `_Analysis` takes the backend (private class). Docstrings:
module, `JobDeviceBackend`, `_release_fft_plans`, `_Analysis`. Tests (this package's own files):
`test_wp321_fft_release.py` -- the double records each release's thread; the video tests expect
`["export-analysis", <job thread>]` (renamed "... at both boundaries"); NEW `gpu`
`test_the_analysis_end_boundary_frees_the_pools_cached_blocks` (plants a 64 MiB cached block on
the analysis thread just before the boundary, real GPU backend: cached after < before, job ok,
45 frames). `test_wp321_overlap.py` F2 order test: the double tells the boundary apart; expected
`[("abort", True), ("boundary", True), ("release", False)]`, so abort -> A joined -> release
stays pinned. Light set (`c7-p2-light.log`): the wp321 release and overlap files, the five
`test_jobs_*` export/batch files (WP3.14's cancel, failure, D87, V11 tests unchanged) and the
seven layering files -> 251 passed, 1 failed (the F2 order test, by the boundary's new release,
expected); after its update the order test + the release file -> 11 passed (`c7-p2-fix.log`).
ruff check, ruff format --check (249), mypy (138) clean (`c7-p2-static.log`).

### Light STOP: the form of the NVDEC / NVENC terms (proposed, for CHARC)

Constants from the attribution (MiB): NVDEC per session = the overlap increment, max of ON
1,237 / OFF 1,256 -> **1,256**; NVENC = frames-only remainder (one decoder + NVENC), max ON
2,440 / OFF 2,448 -> 2,448 - 1,256 = **1,192**; context = device-wide after the probe minus before
(246 - 131, 261 - 146) = 115 -> **128**. At 5.3K (24,690,176 px): NVDEC 53.3 B/px, NVENC 50.6 B/px.

| form | 5.3K, 2 dec + NVENC | 4K, 2 dec + NVENC | 4K, 1 dec + NVENC | 4K, 2 dec, libx265 |
|---|---|---|---|---|
| (S) scaled by pixels: 54 B/px per decoder, 51 B/px NVENC, + 128 | 10,153 | 3,560 | 3,133 | 3,156 |
| (F) fixed per session: 1,256 per decoder, 1,192 NVENC, + 128 | 10,113 | 6,006 | 4,750 | 4,814 |

Checks (device-wide peaks; the 4K idle before each run 248-329): 5.3K ON 7,921 / OFF 7,593 /
block 2 7,854 under both forms; 4K c3 cold 3,130-3,244, ancuti 3,014, warm 2,601, OFF 2,925
under (S) 3,560 by 316-959 raw (more with the idle removed); libx265 2,761 under 3,156; WP3.14's
one-decoder 4K 2,409 under 3,133. (S) is the recommendation: NVDEC/NVENC surfaces scale with
the frame, the envelope's sizes are 4K and 5.3K only, and (F) overstates 4K by about 2.8 GB.
Caveats: one anchor (5.3K) cannot separate a fixed per-process part from the per-pixel part, so
(S) may under-count a frame much smaller than 4K (out of the envelope); and either form puts
the 5.3K job at about 10.1 GB, above the 8 GB card (8,188 MiB), because the pool part (6,281)
is loose against the measured pool peak (4,427); `select_backend` is unchanged, so nothing
selects differently.

### Scaling RULED (CHARC FINAL `7f58cfc1`; supersedes the light STOP above): part 1 as built (`9a4256b`)

Ruled form: `session_term(kind) = floor + per_pixel x (w x h)` for NVDEC and NVENC, fitted from
the two measured sizes with the same device-wide instrument; the context a separate constant
(about 250, after the probe); rounded UP; the fit and residual in the docstring; 1080p an
extrapolation; every measured device-wide peak covered, each asserted by a test, else a STOP.

**The fit.** 5.3K (attribution): NVDEC 1,256, NVENC 1,192 (above). 4K: the cold rows' max
3,244 - the 4K pool 947 - context 261 = 2,036 for two decoders + NVENC, split in the 5.3K
proportion: NVDEC 690.4, NVENC 655.2. "The pool at its 4K figure" read as the one MEASURED 4K
pool figure, cell 5's render pool peak at the max fractions (947 MiB, "Task 6 memory re-read");
the 4K job pool with device frames is unmeasured. Sensitivity (disclosed): with the 4K pool
ESTIMATE (2,174) the floors come out NEGATIVE (-222 / -211 MiB, a line that is negative at
1080p), and with a 4K job pool scaled from 5.3K's job/render ratio (about 1,545) the floors are
99 / 94; the measured 947 gives the largest floors (the most conservative extrapolation below
4K). Solved: NVDEC 404.3 MiB + 36.17 B/px, NVENC 383.7 MiB + 34.33 B/px; constants **NVDEC 416 MiB +
37 B/px, NVENC 384 MiB + 35 B/px, context 272 MiB** (261 rounded up). Residuals of the rounded
line: NVDEC +31 (5.3K) / +18 (4K) MiB, NVENC +16 / +6. 1080p (extrapolated): NVDEC 489, NVENC 453.

**Built:** `core/memory.py` `session_bytes(kind, h, w)`, `job_device_memory_estimate_bytes(h, w,
pool_estimate_bytes, *, decoders, nvenc)` and the constants (the pool estimate passed in: the
module stays free of the backend; `select_backend` and `core/__init__.py` untouched).
`tools/export_bench.py`: the backend is selected for every run (the same call as the job's;
`--device-frames` still decides the source's and the sink's), `_PoolPeak` samples the pool's
`total_bytes` through `backend.xp` every 0.1 s (no pool on the CPU backend), and the record's
`memory_check` holds (i) the device-wide peak against the job estimate (decoders 2 cold, 1 over
a complete entry; NVENC when the sink encoded with it) with the idle before stated, (ii) the
pool reserved peak against the backend's pool estimate, and `passes`; the row line ends with
both. NOT built: a product-side report of the figure (IF-8's `JobResult` is frozen and
`clearwater.jobs` imports nothing from `clearwater.core`), so the record is where it is reported.

**Check table** (MiB; pool estimate 5.3K 6,281, 4K 2,174; every row asserted in
`tests/test_wp321_job_memory.py`):

| row | decoders / NVENC | job estimate | peak | margin |
|---|---|---|---|---|
| 5.3K attribution ON | 2 / yes | 10,336 | 7,921 | 2,415 |
| 5.3K attribution OFF | 2 / yes | 10,336 | 7,593 | 2,743 |
| 5.3K block 2 | 2 / yes | 10,336 | 7,854 | 2,482 |
| 5.3K WP3.14 baseline | 1 / yes | 9,049 | 6,104 | 2,945 |
| 4K c3 cold (3 runs) | 2 / yes | 4,524 | 3,130-3,244 | 1,280-1,394 |
| 4K warm | 1 / yes | 3,815 | 2,601 | 1,214 |
| 4K ancuti2018 | 2 / yes | 4,524 | 3,014 | 1,510 |
| 4K libx265 | 2 / no | 3,863 | 2,761 | 1,102 |
| 4K device frames OFF | 2 / yes | 4,524 | 2,925 | 1,599 |
| 4K WP3.14 c3 / libx265 | 1 / yes, no | 3,815 / 3,155 | 2,409 / 1,937 | 1,406 / 1,218 |

Every row covered. Tests: `test_wp321_job_memory.py` (26: the fitted points, the 13 rows, the
sum, 1080p, refusals, the bench check on both instruments and its CPU no-op). Light set
(`c7-b3-light.log`): it, `test_export_bench.py` (WP3.14's, unchanged), `test_wp321_bench.py`,
`test_core_select.py`, `test_core_backend.py` and the seven layering files -> 225 passed.
ruff check, ruff format --check (250), mypy (138) clean (`c7-b3-static.log`).
