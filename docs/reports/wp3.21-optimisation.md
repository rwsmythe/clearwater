# WP3.21 report: the optimisation package

Package WP3.21 (plan section 6, Phase 3; spec v0.5.5 D106, N3, N4, N6 interim, N10, V4, V8, V16; architecture FINAL 1.0
AD-1, AD-5, AD-7 as read at ruling Q2, AD-11, AD-20, AD-28, AD-29). Brief `docs/briefs/wp3.21-brief.md` (FINAL, CHARC
`b16da9c25ddfb8c8`, Q1-Q10). Base main `d1e4537`, branch `wp3.21`, last code commit `227ed32`. Ledger
`docs/proofs/wp3.21-ledger.md` (every figure below is recorded there with its moment, window and evidence path).

**Files.** NEW: `tools/analysis_breakdown.py` (task 1), `tools/export_oracle.py` (task 2), tests
`tests/test_analysis_breakdown.py`, `test_export_oracle.py` and `test_wp321_{overlap, device_frames, device_proxy,
fft_gaussian, fft_release, bench, job_memory, conftest_release}.py`, this report and the ledger. EDITED under Q1:
`src/clearwater/analysis/engine.py`, `analysis/proxy.py`, `jobs/export.py`, `core/backend.py`, `tools/export_bench.py`.
EDITED under later grants:
- `src/clearwater/io/video/decode.py` and `io/video/encode.py` (Q-R2, the orchestrator; DR-63 closed at the touch);
- `src/clearwater/core/memory.py` (CHARC FINAL `cadc39fc8a199a57`, the task 10 fix; Q9 reserved it to CHARC);
- `tests/conftest.py`, one autouse fixture (CHARC ruling (A) `21e6d24562923b10`);
- `src/clearwater/analysis/__init__.py`, six additive re-exports for #3 (`05ee507`). This file was outside the brief's
  owned list and was edited without a grant; CHARC GRANTED it retroactively (`407750217110613c`). The ungranted edit
  is a MINOR ledger finding: it should have been a STOP.

`src/clearwater/color/samples.py` was granted (Q-R2), edited for #2 and REVERTED under AD-29: it equals `d1e4537`, as
does everything under `src/clearwater/interfaces/` (IF-1..IF-10 unchanged). No other module, no existing test file
(apart from the fixture) and no dependency changed; no OS-specific code. No module opens a `gpmd` packet; no location
tag is read.

## Result

**Cold c3 at 4K meets D106's interim 25 min/min and the ~10 min/min aim.** These are the V16 figures of record, from
`tools/export_bench.py v16 --device-frames` on the final code in EXCLUSIVE windows:
- GX011627: 9.57-9.92 min/min (baseline 31.80-31.93);
- GX011625, sustained: 9.58 min/min (baseline 31.26).

Every 4K NVENC row meets 25. The 5.3K 8:7 row went from 136.03 to 36.65 min/min (best effort, D106). N4 held on every row.
The exported pixels: the render differs by at most 7.06e-6 before quantisation (tier 2, AD-11); the statistics records
and the proxies are bit-identical (tier 1) on every leg.

## Task 1: where the cold export spent its time (the breakdown)

`tools/analysis_breakdown.py GX011627` (record `work\wp3.21\breakdown\breakdown-GX011627-c3-20261028T034140Z.json`)
drives the product functions in the pass's order with its own clock. Its records equal the engine's bit for bit (2,724
records, 681 proxies). The sum of the step means is within 5 % of the mean per-frame wall in every phase (residuals
1.07 / 0.43 / 0.91 %). Per frame on the base engine, in seconds:

| Phase | wall s/frame | named steps (mean s) | device bound |
|---|---|---|---|
| decode pass (analysis) | 0.299 | **block_mean (host float64) 0.152 (50.9 %)**, planes_to_rgb 0.053, analyze 0.053, quantise 0.010, proxy round trip 0.017 | 20.0 % |
| later stages (fusion) | 0.019 | analyze 0.012 | 79.2 % |
| frame path | 0.714 | **render 0.500 (70.0 %)**, rgb_to_planes 0.089, planes_to_rgb 0.077, upload 0.015, to_host 0.013 | 74.0 % |

The GPU sat at its idle clock (SM 210 MHz) through the analysis pass (WP3.14's observation) because the pass is 80 %
host work: the card gets CUDA work at most 20 % of the time and never boosts.

## What was applied, in order, with each step's measured gain

| # | Change (task) | Gain as measured (GX011627 cold c3) | Oracle tier |
|---|---|---|---|
| 1 | Overlap the analysis with the export (4): two decoders, one thread each; the lead derived from the stage graph (c3 61 frames, ancuti2018 91 at 30000/1001) | interim 1: 1.063 -> 0.810 s/frame (-24 %); frames phase 0.778 (serial path 0.714: the analysis thread's contention) | tier 1 |
| 2 | Device frame conversions in the frame path (5a): upload the integer planes, convert and quantise on the device (AD-29) | with #3, interim 2: 0.810 -> 0.513 s/frame; frames phase 0.778 -> 0.501 | tier 1 |
| 3 | Device block mean in the analysis (5b): exact float64 block sums on the device (AD-29 ruling (a)) | (with #2); the lead 18.8 -> 5.3 s | tier 1 |
| 4 | 3C Gaussian by FFT (6): per-axis float32 rfft of the same truncated kernel, reflect padding reproduced | task 10: 0.513 (interim 2) -> 0.3195-0.3310 s/frame; render 0.388 -> 0.207 s at 4K | tier 2 (renders only) |

The frames-phase trio and task 10: **0.714** serial (the breakdown), **0.778** interim 1 (#1), **0.501** interim 2
(#1-#3), and **0.308-0.320** in task 10 (#1-#4; GX011625 0.319). The #2/#3 against #4 split comes from task 10's
device-frames OFF row (below): ON 0.3195-0.3310 against OFF 0.5757 s/frame, so #2+#3 together are about
-0.25 s/frame with the FFT in place. #2 and #3 are not separated (they share the device frames).

DR-40 (b) (per-call constant uploads, 0.15 % of the 0.500 s render, under Q8's 1 %) was recorded as measured-negligible;
`methods/` was not asked for. D109 (sparse analysis) was not used.

## Design as built

**The overlap (#1, `analysis/engine.py`, `jobs/export.py`).**
- `analysis_job(stream=True)` runs the analysis on thread `export-analysis`, iterating and closing its own decoder
  (DR-45 (a) not reached). It advances every `max(STREAM_STEP, raw // STREAM_SHARE)` first-stage records
  (16, and 1/64 of the records in).
- `smoothed_record` waits until the frame's record is final and checks the composed reach. Rendering before final
  raises `RenderBeforeFinalError` by name: the planted lead short by one at the derived bound fails.
- `mark_complete` stays after the whole pass (V17), and only the analysis thread writes the cache (DR-62 not widened).
- The D87 re-check runs after the lead and adds the cache entry's extrapolated growth (Q-R6). On a retry over an
  incomplete entry it scales the entry's own bytes per stored frame (Reviewer A r1 F5).
- **The order on failure and cancel, corrected (Reviewer A r1 F2, ruled (a)).** Round 0's design text said "E joins A
  before the sink's abort"; that is not what was built. The built and pinned order is: the sink's `abort` first, then
  the analysis thread joined, then the plan release. Abort-first releases the encoder at once, and the watchdog cannot
  join A before its abort by design. Every observable guarantee holds: CANCELLED or the failure text, nothing on disk,
  A joined before `_video` returns, and no rename on that path. A test pins abort -> A joined -> release.

**Device frames (#2) and the device block mean (#3), AD-29.**
- The device methods `planes_to_rgb`, `rgb_to_planes`, `block_sums` and `release_fft_plans` live on `CupyBackend`
  only, as IF-2 device extensions; IF-2 is unchanged and the CPU backend has none of them.
- Each consumer declares its own `runtime_checkable` Protocol (`DeviceFrameBackend` in `io.video.decode`,
  `AnalysisDeviceBackend` in `analysis.proxy`, `JobDeviceBackend` in `jobs.export`). No consumer imports `core` or
  `cupy`, and frame rule 5 holds.
- `FFmpegVideoSource(device_backend=None)` and `FFmpegVideoSink(device_backend=None)` default to the host path. The
  sink still refuses a device label on host pixels (`test_io_video_encode.py` 962/1101/1211/1259 unchanged).
- `block_sums` returns exact float64 sums, or None past the exactness bound
  (`ceil(log2(k*k+1)) - (e_min - 23) <= 53`; then the host reduces). The division and `quantise` stay on the host
  in `proxy.py`.
- No product code constructs the real source yet: the GUI's path is the stubs' until WP4.2 (CHARC's WP4.2 register row
  binds the product's GPU job to `device_backend=<the GPU backend>`). The V16 rows run with device frames ON through
  the bench.

**The FFT Gaussian (#4, `core/backend.py`).**
- The gate lives inside `gaussian_blur`, identical for both backends: the FFT route only when `min(H, W) >= 1080` and
  `sigma >= 32`. No proxy can reach it (the largest proxy short side is 1,079, pinned by a tripwire test), so every
  analysis blur stays direct and every record stays tier 1. At 4K only the Cb and Cr blurs (sigma 108) switch.
- The route uses the same kernel (`radius = int(4 sigma + 0.5)`, scipy's weights) with scipy's `mode="reflect"`
  padding, including repeated reflection. Per axis it runs float32 `rfft`, times the kernel's spectrum, `irfft` and
  crops.
- Transforms run in batches of at most `FFT_BATCH_LINES = 512` lines, the last batch being the final positions.
  Chunked output equals unchunked bit for bit on line counts that are not multiples of 512, at 1080p, 4K and 5.3K.
- **FINDING (fixed in the route): odd FFT lengths are batch-position dependent in cuFFT.** `cupyx.scipy.fft.rfft` at
  length 4725 differs by 1 ulp between a batch's rows and the same rows of the whole-array transform. Every odd length
  tried was position-dependent and every even one position-independent. The route therefore takes the smallest EVEN
  fast length (also in the route's docstring; the pinned tests are the tripwire).
- **Plan size follows the transform length, not the shape.** A 1440x2560 plane held 129 MiB of plans at sigma 32 and
  83 MiB at sigma 108, because cuFFT's algorithm depends on the length. That is why the memory bound is per line
  length: `fft_memory_bound_bytes = 48 B x 512 x length`, with `length` the power of two at or above
  `longer + 2 (shorter + 1)`. The bound is 96 / 192 / 384 MiB at 1080p / 4K / 5.3K.
- `CupyBackend.memory_estimate_bytes` = AD-1's base + the bound. `select_backend` stays on AD-1's base (CHARC
  `16a8ee8a` (a); `test_core_select.py` unchanged).
- The job releases its plans at the end of every export job (`ExportEngine._run`'s `finally`, photos included) and,
  since the task 10 fix, also on the analysis thread when it returns (part 2, the boundary free).

**The task 10 fix (CHARC FINAL `cadc39fc8a199a57`, `7f58cfc1`, `3f17304438bc2555`).** `core/memory.py` gains
`session_bytes(kind, h, w)` and `job_device_memory_estimate_bytes(h, w, pool_estimate_bytes, *, decoders, nvenc)`:
the pool estimate (base + FFT bound) + the context + decoders x NVDEC + NVENC. Each session term is
`floor + per_pixel x (w x h)`, fitted exactly from the measured 5.3K and 4K attributions and rounded UP:

| term | measured 5.3K / 4K (MiB) | fitted | rounded (in `core/memory.py`) | residual 4K / 5.3K | 1080p (extrapolated) |
|---|---|---|---|---|---|
| NVDEC per decoder | 1,256.0 / 472.0 | 75.4 MiB + 50.14 B/px | **80 MiB + 51 B/px** | +11.4 / +24.9 | 181 |
| NVENC | 1,192.3 / 642.4 | 364.2 MiB + 35.17 B/px | **368 MiB + 36 B/px** | +10.4 / +23.4 | 439 |
| context | largest after-probe reading 261 | - | **272 MiB** | - | - |

CHARC's reading (msg `e2c24dee`): the NVDEC per-pixel figure (51 B/px, about 34 NV12 frames of surfaces per decoder) and
the NVENC floor (368 MiB) are the physical shape the ruling expected. That is the evidence that the fit is a model and
not a curve through two points. The overlap counts TWO decoders and a job over a complete cache entry counts one.
`select_backend` is unchanged (AD-1 untouched).

**IF-8 reporting deviation (ACCEPTED, CHARC `49b70b95`).** The GPU job does not report the job total itself, because
IF-8's `JobResult` is FROZEN; that is the blocker (`clearwater.jobs` sitting above `clearwater.core` is not forbidden
by the architecture). The bench record reports the job total and carries the STOP test, and no frozen interface is
touched. Showing the figure folds into CHARC's WP4.3 register row.

**Which instrument binds where** (CHARC `3f17304438bc2555` (2), in the docstring and the record):
- At 4K, (i) binds: the device-wide `memory.used` peak against the job estimate.
- At 5.3K the job total (10,331 MiB) exceeds the 8 GB card because its pool part is the selection bound, loose by
  design. The binding 5.3K check is therefore (ii), the pool's reserved peak against the pool estimate, together with
  the covered-row tests; (i) is recorded there.

**The post-convergence change.** Reviewer A converged at round 2 on `9d73fe4` (cleanup `1df2626`). After that came the
conftest fixture `57a7a2e` and the task 10 fix:
- part 2, the boundary free: `b5a383c`;
- part 1, the job estimate and the bench's two-instrument check: `9a4256b`, with the which-binds note `3c2fdf6`;
- the measured fit: `227ed32`.

Together they form the diff `afad7af..227ed32` (`jobs/export.py`, `core/memory.py`, `tools/export_bench.py`,
`test_wp321_fft_release.py`, `test_wp321_job_memory.py`, `test_wp321_overlap.py`), which goes to the orchestrator's
Reviewer B with that range named. Its tests:
- `test_wp321_job_memory.py` (27): every measured device-wide peak covered (14 rows), each session term covering its
  fitted point, the four-term sum, 1080p, refusals, and the bench check failing on either instrument;
- `test_wp321_fft_release.py`: the video-job release tests now expect two releases (the analysis end, on
  `export-analysis`, and the job end). `test_the_analysis_end_boundary_frees_the_pools_cached_blocks` (gpu) plants a
  64 MiB cached block before the boundary and sees it freed.
- The F2 order test in `test_wp321_overlap.py` tells the boundary apart and still pins abort -> A joined -> release.
- One name is misleading: `test_a_video_job_releases_at_the_analysis_end_and_after_every_frame` asserts two releases,
  the analysis end and the job end ("after every frame" means after the last frame). CHARC: a MINOR, renamed in
  Reviewer B's cleanup if B lists it, otherwise a MINOR row at the accept.

## Equality (the oracle, task 2; ruling Q3)

`tools/export_oracle.py` records an export (every frame digest, the raw and smoothed statistics records, the analyze
calls, the proxies and 1 fps float32 frames) and compares two records. The base references `ref-*-a` / `-b` were
recorded on `d1e4537` with CONTROL 13 of 13 TIER1 (N10 holds on this device and on the CPU).

| Change | WP2.3 samples (x5, GPU and `--force-cpu`) | GX011627 c3 | synthetic 4K c3 | GX011627 ancuti2018 |
|---|---|---|---|---|
| #1 overlap | TIER1 x10 | TIER1 | TIER1 | TIER1 |
| #2 (AD-29), `--device-frames` | TIER1 x10 | TIER1 | TIER1 | - |
| #1-#3 (interim 2) | TIER1 x10 | TIER1 | TIER1 | TIER1 |
| #4 FFT, `--device-frames` | TIER1 x10 (below the gate) | **TIER2**, max abs 7.06e-6, mean 7.95e-7 | **TIER2**, 2.44e-6 / 2.62e-7 | TIER1 (no gated blur) |

Every TIER2 leg had records, proxies, source statistics, analyze calls and pts equal; only frames differ. In CHARC's
wording, the render differs by at most 7.06e-6 (about 0.002 of an 8-bit code value) before quantisation; after
quantisation a pixel changes by at most one code value, and only where the float sits within that distance of a
rounding boundary; this was not measured on the encoded output. By the product's own quantiser (`rgb_to_planes`:
float32 clip, scale, round half to even), 14,858 of 572,313,600 values change at 8-bit and 60,692 at 10-bit, each by
at most 1 code value. As corroboration, the ancuti2018 output has exactly the baseline's size
(85,727,426 B), while the c3 output is 85,988,986 B against 85,975,154.

The FFT bound (Q3: max abs 1e-5 on [0, 1] float32 data against the direct filter) measured 2.2-3.1e-7 on the 4K render
calls, <= 2.68e-6 on the 4K ladder and <= 2.92e-6 at 5.3K sigma 270, with step edges at every border. It is
deterministic on repeat.

## V16, the re-measure (task 10; EXCLUSIVE windows, figures of record)

Every row was run with device frames ON, hw_decode ON, backend `CupyBackend(device='cuda:0')`, encoder auto ->
`hevc_nvenc` (NVENC proof tied) unless libx265, Standard and 8-bit. Records are under
`C:\Users\rwsmy\clearwater\work\wp3.21\bench\` (`export-bench-v16-gx011627-20261028T132317Z.json`,
`export-bench-GX011627-20261028T135223Z.json` (OFF row), `export-bench-v16-synthetic-5k3-20261028T151748Z.json`,
`export-bench-v16-gx011625-20261028T162727Z.json`); nothing footage-derived is committed. Code: block 1 on `57a7a2e`,
blocks 2 (re-run) and 3 on `227ed32`. The 4K rows of block 1 are not re-run after the fix (CHARC): the fix changes no render
arithmetic, and their memory is re-stated against the new job total below. In each cell, `before -> after`:

| Row | s/frame | min/min (D106 25) | per frame median / p90 / max | lead + stall share | peak tree RSS MiB | peak GPU MiB (device-wide) |
|---|---|---|---|---|---|---|
| GX011627 c3 cold 1 | 1.0654 -> **0.3195** | 31.93 -> **9.57** | 0.740 / 0.767 / 0.888 -> 0.290 / 0.322 / 0.602 | 30.4 % -> 7.39 % | 2,819 -> 3,394 | 2,409 -> 3,244 |
| GX011627 c3 cold 2 | 1.0611 -> **0.3264** | 31.80 -> **9.78** | 0.739 / 0.763 / 0.850 -> 0.297 / 0.332 / 0.624 | 30.4 % -> 7.39 % | 2,848 -> 3,417 | 2,409 -> 3,142 |
| GX011627 c3 cold 3 | 1.0631 -> **0.3310** | 31.86 -> **9.92** | 0.743 / 0.766 / 0.872 -> 0.302 / 0.334 / 0.688 | 30.2 % -> 7.44 % | 2,850 -> 3,396 | 2,409 -> 3,130 |
| GX011627 c3 warm (a) | 0.7743 -> 0.3022 | 23.21 -> 9.06 | 0.745 / 0.773 / 0.874 -> 0.296 / 0.319 / 0.359 | 3.6 % -> 0.81 % | 2,852 -> 2,456 | 2,409 -> 2,601 |
| GX011627 ancuti2018 cold | 0.7202 -> 0.2917 | 21.58 -> 8.74 | 0.423 / 0.452 / 0.583 -> 0.255 / 0.271 / 1.212 | 40.9 % -> 11.66 % | 2,834 -> 3,396 | 2,409 -> 3,014 |
| GX011627 c3 libx265 cold | 1.1877 -> 0.4869 | 35.60 -> 14.59 | 0.861 / 0.951 / 1.192 -> 0.426 / 0.552 / 3.593 | 26.5 % -> 2.10 % | 4,109 -> 4,963 | 1,937 -> 2,761 |
| GX011627 c3 cold, device frames OFF | (c3 cold 1.061-1.065) -> 0.5757 | -> 17.25 | -> 0.536 / 0.574 / 3.090 | -> 7.27 % | -> 4,017 | -> 2,925 |
| synthetic 5.3K 8:7 c3 cold | 4.5389 -> **1.2229** | 136.03 -> **36.65** | 3.714 / 4.006 / 4.438 -> 1.074 / 1.178 / 4.654 (b) | 16.6 % -> - | 6,354 -> 7,753 | 6,104 -> 7,901 |
| GX011625 c3 cold, sustained | 1.0429 -> **0.3195** | 31.26 -> **9.58** | 0.737 / 0.769 / 1.437 -> 0.299 / 0.337 / 4.117 | 29.8 % -> 5.75 % | 2,903 -> 3,653 (c) | 2,450 -> 3,277 |

- The baseline's "analysis share" was the whole analysis; after the overlap the share is the Q-R7 keys,
  `analysis_share_overlapped` = (`lead_s` + `record_wait_s`) / wall. Lead / record wait, in seconds:
  - c3 cold: 5.36 / 10.73, 5.04 / 11.38, 5.27 / 11.50;
  - warm: 1.56 / 0.10;
  - ancuti2018: 7.74 / 15.42;
  - libx265: 5.39 / 1.56;
  - OFF: 19.72 / 8.77;
  - GX011625: 4.90 / 269.68.
- (a) **The warm row** (cache complete at start) measures the product's own state after an analysis, pool and all; the
  prime makes no FFT plans, because its proxies are below the 1080 gate (CHARC FINAL `522229f57cbc6870`, method (a)).
  The memory STOP check stays on the cold rows.
- (b) **The 5.3K row** is the block 2 re-run on `227ed32`, the figure of record. The first block 2 run (35.46 min/min,
  peak 7,854 MiB) was the memory STOP below. The re-run's frame-16 max (4.654 s) fell during the overlap, not at the
  analysis-end boundary (frame 57). A `System` stray ran at 38.6 % CPU over the run, so the max is kept as spread, not
  placed.
- (c) GX011625's peak tree RSS (3,653 MiB at 1,972 s) includes five `msedge.exe` members (287 MiB) that the job did
  not start. The job's own processes total 3,366 MiB (python 751, three `ffmpeg.exe` 917 / 780 / 918). The figure is
  recorded as read.
- libx265 is the CPU fallback encoder (the NVENC proof is not tied, as expected) and not a target; a `System` stray
  ran at 41.5 % on that row and 29.1 % on the OFF row, kept as spread.
- GX011625 output 1,794,734,980 B (baseline 1,794,336,305), every frame written; the two standing D86 warnings (camera
  firmware tag, udta atoms) as designed.

**Where the slow frames fall (the STREAM_STEP placement; CHARC `b4c143d7` 2).**
- On GX011627 the keyframes are every 30 frames (ffprobe flags, read-only), so interim 2's 323 / 387 are not
  keyframes.
- In every cold device-frames row the slow frames recur on the streamed analysis's advance:
  - GX011627 c3: 19 + 16 k; ancuti2018: 5 + 16 k. They stop at the frame where the analysis thread returned.
  - GX011625: 261 frames above 1.6 x the median. They fall at 51 + 16 k up to frame 1,011 (mean 0.56 s), then every
    `max(16, raw // 64)` records. The gap grows to 229 frames and each wait to 3-4 s (max 4.117 s at frame 13,109).
  - Their excess over the median (269.39 s) equals the record wait (269.68 s).
  - The warm row has none besides frame 0. Frame 0 is the first-frame cost (keyframe, plan creation, NVENC start).
- With the FFT the frame loop outruns the analysis, so **the job is analysis-bound during the overlap**. On GX011625
  the analysis returned at 4,690.6 s, at frame 14,655 of 14,938; the analysis runs at about 0.314 s/frame against a
  frame-path median of 0.299.
- The step only sets the grain of the waits, not the wall, so there is no fix. A smaller step would add the store's
  whole-axis copies per advance. **The analysis pass is the next target.**
- Off the cycle, GX011625 shows six short bursts of 2-6 frames at 0.5-0.7 s, not placed (spread).

**Conditions.**
- Block 1, 13:23:17Z-13:52:07Z, and the OFF row, 13:52:23Z-13:59:15Z: SM 210 MHz idle before each run (1,980 before
  the first), 52-69 C.
- Block 2 re-run: 15:17:48Z-15:21:22Z.
- Block 3: 16:27:27Z-17:47:22Z. First hour 85 C / SM 1,845 MHz / 64.8 W; software thermal slowdown in about half the
  samples, power cap in the rest. After that, 79 C / 1,575 MHz / 54.8 W; peak 95 C (baseline 82 C / 1,590 MHz,
  peak 93 C). Frames-phase median 0.2951 s in the first hour, 0.3066 in the last quarter. Stray: `System` 26.8 % CPU
  over the run, kept as spread.
- Telemetry errors 0 on every row; the NVENC proof is tied on every NVENC row.

## Memory (N4 and AD-1)

**N4 held.** The peak tree RSS is 7,753 MiB on the 5.3K row of record against 16 GB, and the device-wide graphics peak is at most
7,921 MiB (5.3K attribution) on the 8 GB card (8,188 MiB).

**The FFT memory re-read** (task 6, plans and pool cleared before each peak, the binding method):

| input | parameters | render peak | persistent plans | estimate (base + bound) | render FFT / direct |
|---|---|---|---|---|---|
| 4K GX011627 frame 0 | default / max fractions | 908 / 947 MiB | 30 / 69 MiB | 2,174 (1,982 + 192) | 0.207 / 0.388 s |
| 5.3K 8:7 synthetic | default / max fractions | 2,710 / 2,798 MiB | 97 / 184 MiB | 6,281 (5,897 + 384) | 0.777 / 2.930 s |

The batched route's FFT-specific peaks were 34-255 MiB, every one under the bound (96 / 192 / 384). Unbatched, one
5.3K plane took about 1.05 GiB.

**The 5.3K STOP and its attribution.**
- Block 2's first run peaked at 7,854 MiB device-wide. That is above the GPU estimate (6,281) and above base x 1.25
  (7,371), so it was a STOP to CHARC.
- The attribution run (option (A), CHARC FINAL `e166515f`) sampled CuPy's pool in process and `nvidia-smi` device-wide
  on one clock. The excess was not the render's arrays; the pool's reserved peak was 4,427 MiB ON / 3,628 OFF, under
  6,281. It was:
  - the FFmpeg sessions: the export decoder plus NVENC about 2.4 GB, and the overlap's analysis decoder
    +792 MiB (median) to +1,237 MiB (max);
  - the CUDA context;
  - the pool's cached free blocks (3,483 MiB of the frames-only plateau).
- AD-1's estimate is defined over the render's arrays and checked against the pool's reserved peak. It counts no
  FFmpeg memory.
- The 4K attribution gave the second fit point: peak 3,054 MiB, overlap increment 472.0 MiB.
- CHARC's reading of the part-2 boundary free: it returned about 150 MiB at 4K (frames-only pool total 1,204 after the
  analysis end), against the 5.3K plateau's 3,483 MiB cached share. The free helps most where the pool grew most.

**Every peak against the ruled instruments.** In MiB, the 4K block-1 rows are re-stated against the new job total and
not re-run; the pool instrument (ii) was not sampled in their records (it was built after them).

| Row | decoders / NVENC | (i) device-wide peak / job estimate | margin | (ii) pool reserved peak / pool estimate |
|---|---|---|---|---|
| GX011625 c3 cold (block 3) | 2 / yes | **3,277.0 / 4,065.4 PASS** (idle before 248.0) | 788 | **1,510.8 / 2,173.8 PASS** |
| 5.3K block 2 re-run | 2 / yes | 7,901 / 10,330.8 (recorded) (idle before 256) | 2,430 | **4,311.7 / 6,281.4 PASS (binding)** |
| 5.3K block 2 first run / attribution ON / OFF | 2 / yes | 7,854 / 7,921 / 7,593 against 10,331 | 2,410-2,738 | - / 4,427 / 3,628 against 6,281 |
| 4K GX011627 attribution | 2 / yes | 3,054 / 4,065 | 1,011 | 1,353 (pool total at the peak) |
| 4K c3 cold x3 | 2 / yes | 3,130-3,244 / 4,065 | 821-935 | not sampled |
| 4K warm | 1 / yes | 2,601 / 3,582 | 981 | not sampled |
| 4K ancuti2018 | 2 / yes | 3,014 / 4,065 | 1,051 | not sampled |
| 4K libx265 | 2 / no | 2,761 / 3,413 | 652 | not sampled |
| 4K device frames OFF | 2 / yes | 2,925 / 4,065 | 1,140 | not sampled |
| WP3.14 baseline 4K c3 / libx265; 5.3K | 1 / yes, no; 1 / yes | 2,409 / 3,582; 1,937 / 2,929; 6,104 / 9,050 | 992-2,946 | - |

Every measured device-wide peak is covered, each asserted by a test (`test_wp321_job_memory.py`).

## The micro-timing (Q-R5; development evidence)

Measured on GX011627 frame 0 at 4K, with GPU events, the median of 20:
- **The c3 render's blur.** The blur is 71.4 % of the render (0.360 of 0.504 s): mask sigma 21.6 0.020 s; Cb and Cr
  sigma 108 0.099 + 0.100 s; sharpen sigma 10.8 0.032 s; Laplacian x2 0.003 s; saliency x2 0.020 s.
- **Under the gate only Cb and Cr switch.** They go from 0.198 s direct to 0.0185 s by the per-axis FFT, saving
  0.180 s/frame; the product render confirmed it (0.388 -> 0.207 s).
- **The threshold.** At 4K the FFT wins from sigma 16 (RGB) and 8-24 (one plane), so 32 stays (it may only move up).
- **The plan cache.** The unbatched 5.3K plans filled the card in run 1 (7,839 of 8,188 MiB). This gave the batching
  and the plan release.

## Tests

The new tests, 211 collected (68 in the serial set: `gpu`, `footage`, `gui` or `slow`):

| File | Tests | Pins |
|---|---|---|
| `test_wp321_overlap.py` | 25 | the derived lead (61, 91, VFR); a lead short by one fails by name; one frame per thread; out-of-order render; cancel before start, during the lead, mid-encode with a write blocked until `abort`, before `commit`; analysis failure mid-export keeps its text; export failure joins A; no thread at commit; the CPU path; cache complete only after the pass; the D87 growth (Q-R6, r1 F5); abort -> A joined -> release |
| `test_wp321_device_frames.py` | 34 | device conversions = host bit for bit (exhaustive 8/10-bit codes, ties, clip limits); refusals; device decode = host decode on the WP2.3 samples; sink device payload = host payload; DR-63 |
| `test_wp321_device_proxy.py` | 21 | the Protocol pair; device block mean = host at 4K k=4, 5.3K k=5 and k=8, odd edges, k=1, 8/10-bit; the exactness bound's edge; NaN / inf / >1 / tiny plants fall back to the host |
| `test_wp321_fft_gaussian.py` | 35 | the gate's boundaries; the proxy tripwire (<= 1079); analysis-sized blur bit-identical; kernel = scipy's; reflect = numpy's; FFT within 1e-5 at 1080p, 4K, 5.3K and on GX011627 frame 0; chunked = unchunked; the bound and the GPU estimate |
| `test_wp321_fft_release.py` | 10 | the release at the analysis end and the job end on success, failure and cancel; photos; a raising release; the boundary frees cached blocks (gpu) |
| `test_wp321_job_memory.py` | 27 | the session fit, every measured peak covered, the bench's two-instrument check |
| `test_wp321_bench.py` | 12 | `--subdir`, the Q-R7 stamps, `--device-frames` |
| `test_wp321_conftest_release.py` | 2 | the conftest fixture leaves no plan on pytest's thread |
| `test_analysis_breakdown.py`, `test_export_oracle.py` | 19, 26 | the instruments: dry runs, record shape, the 5 % check, tier classification, refusal of a footage-folder output (lexical and `realpath`), `--name` as one component |

No existing test file was edited, apart from the ruled `tests/conftest.py` fixture. These all pass unchanged:
WP3.14's cancel / failure / D87 / V11 tests, WP3.11's `smooth_at` tests, `test_core_select.py`,
`test_io_video_encode.py` 962/1101/1211/1259, every `*_deps.py` / `*_rules.py`, and WP3.13's import test
(`clearwater.jobs` loads no GUI, methods, PySide6 or CuPy at import). Failing-first was recorded for each new
behaviour (ledger).

**The plan-cache finding and the conftest fix.** Serial leg 1 failed `test_prototype_backend.py::
test_bench_gpu_records_graphics_memory` (ratio 0.133). The product's FFT route leaves cuFFT plans in the calling
thread's plan cache until a job end releases them. `test_methods_assembly_v8.py`'s 1080p blurs ran earlier on
pytest's thread, and the prototype bench then counted their plans as its reserved pool. Ruling (A) added one autouse
fixture to `tests/conftest.py`. After each test it calls `release_fft_plans` on the probed GPU backend, and only when
`cupy` and `clearwater.core.backend` are already loaded; it imports nothing new. Outside the fixture the conftest's AST
is unchanged (`ast.dump`), and `test_wp321_conftest_release.py` pins the fixture. Test isolation is the fixture; the
tools exit their process.

## Gates

- `uv run ruff check .` clean, `uv run ruff format --check .` 250 files formatted, `uv run mypy` 138 source files no
  issues, all on the final head (`work\wp3.21\logs\c8-static.log`).
- **Collection** on the final code: 5,289 tests in all, parallel set 4,175 plus serial set 1,114. No duplicates, an
  empty intersection, and the union equals all. Against cell 7's sets, +27 in `test_wp321_job_memory.py` and +1 gpu
  in `test_wp321_fft_release.py`; three release tests were renamed by part 2. No other test id was removed.
- **The two-leg suite, GREEN on `227ed32`**, from Git Bash with `PYTEST_ADDOPTS` unset and
  `QT_QPA_PLATFORM=offscreen`, each leg in its own EXCLUSIVE window:
  - parallel (`-n 4`): 4,174 passed, 1 skipped in 488.09 s. The skip is `test_color_roundtrip.py:121` (swscale yuvj),
    as in every previous leg.
  - serial: 1,113 passed, 1 skipped, 4,175 deselected in 2,685.30 s. The skip is `test_photo_check.py:139` (no photos
    yet).
  - Against WP-T4's ten serial skips: this worktree's `working_path` points at the main tree's `work/`, so the nine
    V8 look-check tests RAN and passed (CHARC's record).
  - Logs: `work\c8-suite-{parallel,serial}.log` (worktree).
- Earlier legs: cell 6's parallel leg was 4,147 passed / 1 skipped, and its serial leg 1 failed (the plan-cache
  finding above). Cell 7's serial leg 2 was 1,112 passed / 1 skipped on `afad7af`.

## Reviewer A (STRONG; WSL codex-cli 0.162.1, `gpt-6.1-sol` high; evidence `clearwater-review-evidence\wp3.21\r1`, `r2`)

| Round | Diff | Verdict | Critical / Major / Minor (reported) | Adjudicated |
|---|---|---|---|---|
| 1 | `d1e4537..aa06584` | NEW_CRITICAL_MAJOR_FOUND | 0 / 6 / 5 | F5 CONFIRMED BLOCKING (D87 growth 0 on a retry over an incomplete entry; fixed `9d73fe4` with a failing-first test); F2 ruled (a) MINOR (abort-first kept, the design text corrected above, the order pinned); F1, F4 rejected; F3 banked; F6-F9 MINOR (cleanup); F10, F11 out of envelope, banked |
| 2 | `aa06584..9d73fe4` | NO_NEW_CRITICAL_MAJOR | 0 / 0 / 1 | r2 F1 (test helper race) MINOR, cleanup |

The loop CONVERGED at round 2. The cleanup `1df2626` (tools and tests only, once) fixed:
- r1 F6: an oracle TIER2 with no measured frame now FAILs; no recorded verdict changes.
- r1 F7: the footage refusal compares the lexical and the `realpath` forms.
- r1 F8: `--name` must be a single path component.
- r1 F9: event-held analysis in the planted tests.
- r2 F1: the stream registry is read under its lock.

The post-convergence diff (`afad7af..227ed32`) goes to Reviewer B (the orchestrator's seat pass).

## Debt dispositions

- **WP3.11 style debt** (the in-block `import logging` in the decode pass's `finally`): CLOSED, moved to a module
  `_LOG`.
- **DR-63** (`encode.py` `close`): CLOSED at the Q-R2 touch. `close` sets `"closed"` only from `"open"`, under a
  `_phase_lock` that `abort`'s transition also takes, and `abort`'s docstring names the window. A test covers it.
- **DR-40 (b)**: measured-negligible (0.15 % of the render, under Q8's 1 %); stays CHARC's to record at the next
  `methods/` touch.
- **Not reached or not widened:** DR-62 (only the analysis thread writes the cache), DR-45 (a) (each stream is iterated
  and closed by one thread), DR-47.
- **Not this package's:** DR-64.

## Limits

- **A CPU backend with a hardware decoder is not a supported combination** (the hw_decode coupling, accepted by CHARC).
  Device frames are produced only for `hw_decode=True` with a GPU backend, and the `force_cpu` path is the base's.
- **cuFFT plans outside an export job.** In CHARC's words, any caller outside an export job keeps its thread's cuFFT
  plans until something calls the release. The GUI preview is the product case (a preview of 1080 or more on its
  short side meets the gate): CHARC's WP4.3 register row. Test isolation is the conftest fixture; the tools exit
  their process.
- **The analysis stall join** (r1 F3, out of envelope). An analysis stalled for 60 s or more inside one frame (a hung
  decoder or store) lets the 60 s join expire, and A can outlive the job. The base's serial job hangs on the same
  stall, and WP3.14's envelope names it out.
- **Abort-first** (r1 F2, ruled (a)): the order is abort -> A joined -> release (above), not round 0's text.
- **Out of envelope, banked:**
  - r1 F10: the FFT batch cap is exceeded for more than 512 channels; product images have 1 or 3.
  - r1 F11: a cancelled streamed engine retained on a later `stream=False` job; the export uses one fresh engine per
    job.
- **Test pacing** (r1 F9 residual): the 2 ms pacing sleep stays in the rig for the overlap-observation tests (equality,
  warm, CPU path). A race there fails loudly, never passes vacuously.
- **The job-memory fit has two anchors** (4K, 5.3K). 1080p is an extrapolation (NVDEC 181, NVENC 439 MiB), and a
  frame much smaller than 4K is out of the envelope.
- **The 5.3K job total exceeds the card.** The job estimate at 5.3K is above the 8 GB card because its pool part is
  the selection bound, loose by design (measured 4,427 against 6,281). The binding 5.3K check is the pool instrument;
  `select_backend` selects exactly as before.
- **Where the figures were measured.** Timing figures come from one laptop in EXCLUSIVE windows, best effort; the
  strays are recorded and contaminated rows kept as spread. Device-wide memory is `nvidia-smi` `memory.used` under
  WDDM, and per-process figures are unavailable (`[N/A]`).

## Open items

- **V4 SAME through `tools/video_fidelity.py` on the optimised engine** (the brief's Done clause: the WP2.3 samples and
  GX011627) is NOT in this package's record. No cell ran it, and no RESUME HERE named it. The bench deletes its outputs
  unless `--keep` is given, so there is no output to compare yet. Raised to the dispatcher with a proposed window; this
  report is amended with the result if it is granted.
- Reviewer B on the merge candidate (the orchestrator's seat), with the post-convergence range `afad7af..227ed32`
  named.
- CHARC's register rows at the accept: WP4.2 (the product's GPU job built with `device_backend=<the GPU backend>`) and
  WP4.3 (the GUI preview's FFT plans; showing the job's device-wide figure, the IF-8 deviation).
- The next speed target is the analysis pass: the job is analysis-bound during the overlap at about 0.314 s/frame.
  N6's figure is re-set at WP5.2 (D106).
