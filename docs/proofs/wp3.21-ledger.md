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
