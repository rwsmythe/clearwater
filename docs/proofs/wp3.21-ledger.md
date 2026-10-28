# WP3.21 ledger -- optimisation package

Cell `implementer-opus-high` (Claude lane), worktree `.worktrees/wp3.21`, branch `wp3.21`, base main
`d1e4537`. Brief `docs/briefs/wp3.21-brief.md` (FINAL, CHARC `b16da9c25ddfb8c8`). Reviewer A: Codex
`gpt-6.1-sol` / high, WSL, evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.21\rN\`.

## Depth readings (dispatcher-read, `scripts/cell_depth.py`)

| Yield | Moment | Depth |
|---|---|---|
| 1 | task 1 instrument + task 2 oracle built; WINDOW REQUEST | (dispatcher fills) |
| 1b | per-step GPU occupancy added; WINDOW REQUEST stands | (dispatcher fills) |

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
| - | none yet | | | | | | | |

Light runs (no window): `vid-hevc8-bt709-full` dry runs of both tools on the GPU (breakdown:
residuals 0.01-0.05 %, replica equals engine on 180 records and 45 proxies; oracle base control
TIER1 on 45 frames); `tests/test_analysis_breakdown.py` 11 passed (18 with the occupancy tests), `tests/test_export_oracle.py`
14 passed.

## Review rounds (Reviewer A)

None yet (the loop runs after the build, task 9).

| Round | Critical | Major | Minor | In / out of envelope | New / reopened | Reverts | Product or test-only | Transport / CLI | Depth |
|---|---|---|---|---|---|---|---|---|---|
