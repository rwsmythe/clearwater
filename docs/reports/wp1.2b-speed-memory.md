# WP1.2 Part B -- real footage speed and memory

Brief `docs/briefs/wp1.2b-brief.md` (FINAL `f7e4cac`), as amended by the orchestrator (CHARC
d40217a81696cc03: GX011625 is the long full clip; 4 h cap per window) and released best effort
by the owner (decision request e2c53e6a, CHARC d4188563639bc453). Spec v0.5.2. Ledger:
`docs/proofs/wp1.2b-ledger.md`. MiB = 2^20 bytes. Local time is HST (UTC-10).

**Read this first.** Every figure below was measured on a SHARED, NON-IDLE laptop. Other
projects' sessions ran 16-worker test batches on it every 15-20 minutes, at 30-100 % of a logical
CPU per worker. Windows Defender (MsMpEng) sat at about one logical CPU and the WMI provider host
at about 0.9 of one through most checks. The owner's words: "I am not concerned about
contaminated figures as the actual program itself will run in a non-ideal state. Best effort is
fine." The figures are therefore an UPPER BOUND on the cost on an idle machine. Each window says
whether it was contaminated, and contaminated figures are given as measured spread (min, median,
max), not discarded. Gate 1 (N6) and Gate 2 (N4) are CHARC's at WP1.6, with this caveat.

## 1. Results at a glance

| What | Figure | Against |
|---|---|---|
| Export, GX011627 (22.7 s, 681 frames), production-shaped, stray-clean run | 0.4856 s/frame, **14.55 min/min** | N6 3.3 min/min (0.1101 s/frame at 29.97 fps): **4.41x** |
| Export, GX011627, device-resident variant (supplementary; contaminated) | 0.3576 s/frame, 10.72 min/min | 3.25x |
| Export, GX011625 (498.4 s, 14,938 frames), full clip (contaminated) | 0.8386 s/frame, **25.13 min/min**, 3.48 h | 7.62x |
| Core alone, 4K GPU ancuti2018, real frames (claim 2) | 0.395 s (run of record); spread 0.375-0.618 s over 22 runs (18 probes, 4 claim-2 runs) | 3.6x on its own |
| Analysis pass, GX011625, software / `-hwaccel cuda` decode (contaminated) | 0.1190 / 0.1101 s/frame, 3.57 / 3.30 min/min | (no target; D109 is CHARC's call) |
| Analysis pass, GX011627, stray-clean re-run | 0.0707 s/frame, 2.12 min/min | -- |
| Peak RAM, GX011625 export (the process tree, FFmpeg included) | 3,682 MiB (Python alone 1,996) | N4 16 GB |
| Peak graphics memory, GX011625 export (device-wide, NVENC included) | 2,860 MiB (CuPy pool 1,709) | 8,188 MiB |
| Container of every export | MANDATORY and REQUIRED all SAME (`compare.py`) | WP1.5 |
| Largest photo (claim 5, second half) | PENDING: no photo in the inventory | D102 |

N6 is not met at 4K on this laptop under these conditions. That holds for the production-shaped
loop, for the device-resident variant, and for the core alone.

## 2. Instrument and method

**Code.**
- `tools/prototype/clip.py` (new): the analysis pass and the export loop.
- `tools/prototype/bench.py`: the real-frame source `--input`, the proxy study on real frames, and
  the whole-clip modes `analysis`, `end-to-end`, `decode-only`, `encode-only`, `passthrough`.
- `tests/test_prototype_clip.py`: 43 tests.
- No change to `pipeline.py`, `params.py`, `backend.py` or `pyproject.toml`.

**Clips** are named by stem and found with `find_footage_file`. The footage folder is input
only. Every output is under `C:\Users\rwsmy\clearwater\work\wp1.2b\`.

**The export loop**, the product's render pass. It is the first draft for WP2.1, WP3.14, WP3.9
and WP3.10.
1. FFmpeg decodes the source and converts it to RGB itself (`scale` with the stream's range and
   matrix, `accurate_rnd`). It writes `rgb24` (8-bit; `rgb48le` for 10-bit, which is not
   exercised here) to a raw pipe. The product does this conversion itself under WP3.5.
2. A reader thread reads whole frames from the pipe and converts each to float32 `k/255`.
3. The main thread runs `correct(frame, params, gpu, statistics=<frame i's smoothed statistics>)`,
   which copies the input to the device and every array of the result back, as WP1.2A timed it.
4. A writer thread rounds the output back to `uint8` and writes it to the encoder's pipe.
5. FFmpeg converts back to YCbCr 4:2:0 with the source's matrix and range. It encodes
   `hevc_nvenc` with WP1.5's settings (`p5`, `hq`, `vbr`, `cq 20`). It muxes with the source's
   audio and data streams copied, the metadata mapped, the colour tags set on the frames
   (`setparams`) and on the stream, and WP1.5's timestamp flags.

**Buffering.**
- Two float input buffers: one being filled, one in the core.
- Two output slots: a slot is taken before the core and given back once the frame is written.
- So at most two frames are in flight on each side.
- A 4K `rgb24` frame is 24,883,200 bytes.

**Frames and timestamps.** Frames are carried in decode order. The sources are constant-rate
from pts 0; that is checked, and a VFR or offset clip is refused. The frame boundaries are exact:
a short read is `PartialFrameError` and a wrong count is `FrameCountError`. Every 30th frame's
channel means, and the last frame's, are checked against the analysis record within 1e-8. That
was 24 checks on GX011627 and 499 on GX011625, all passed.

**The pipe.** FFmpeg writes a raw pipe in 32 KB blocks. A Windows anonymous pipe then carries
about 430 MB/s, about 57 ms per 4K frame. Measured in development: decoding to NUL takes
12.4 ms/frame. A writer using 1 MB / 25 MB blocks reaches 4.4 / 6.0 GB/s, that is 5.6 / 4.2 ms per
frame. Python's 25 MB writes into the encoder's pipe take about 3-5 ms (`write`, below). The pipe
was measured, not tuned (brief).

**The analysis pass** (spec 7.2 steps 1-2).
- The same decode and pipe, then each frame is copied to the GPU and area-averaged to the
  540-line proxy (`temporal.proxy`, a 4x4 block mean).
- The STAGED statistics of WP1.4 (D97) are computed with `median_gaussian` 2 s. That smoother is
  WP1.4's recommendation, PROVISIONAL per DR-25(3); the default is WP2.1's decision.
- `StagedStream` is `temporal.analyse_staged` in streaming form, bit-identical in tests. It holds
  at most 61 proxies instead of the clip: GX011625 would be 93 GB of float32 proxies.
- The render refuses a record from another file, frame count, pts list, parameter set, decode,
  smoother or statistic set.

**Timing bracket.** It runs from the moment the first decoded frame has been read whole to the
moment the encoding FFmpeg process has exited (the muxer has closed the file). For an analysis
it ends when the last statistic is computed. Minutes per minute = bracket / clip length
(frames x 1001/30000 s). The per-frame series, plus the tail after the last hand-off, close on
the bracket within `residual_s`. For example, the GX011627 export had a 0.008 s residual on 330.7 s.

**Ambient record (every window).**
- head SHA and changed files;
- the window's local start and end;
- the power scheme (Balanced, `381b4222-...`) and overlay (Best performance, in every record);
- AC power, battery 80 %;
- the card's SM clock, P-state, power draw and clock-event reasons at the loop's start and end,
  and every 60 s during whole-clip passes;
- a 10 s psutil stray-process check before and after each run, which always lists MsMpEng and
  WmiPrvSE;
- an advisory pre-window idle gate (`Get-Counter` total CPU and `nvidia-smi` utilisation, 6 x 10 s;
  records in `work/wp1.2b/gate/gate.jsonl`).

No sampler uses CIM or WMI (CHARC ruling f2d35c83 condition 2). Two once-per-record helpers that
did were replaced in `2c2856a`: py-cpuinfo ran `wmic`, and Python 3.12's `platform.platform()`
queries WMI.

**Contamination rule** (ruling f2d35c83 as released). Each window opens and closes with a probe:
GPU ancuti2018, 12 frames of GX011627. A window is contaminated if a probe drifts more than 5 % from
the baseline, 0.3948 s (W1c's 4K GPU ancuti2018 median), or if a stray check shows a non-system
process at 25 % or more of a logical CPU. A short window was re-run once when the gate opened
within 10 min. W2 and W5 are never re-run.

## 3. Windows

| Window | Time | Gate median CPU | Probes open / close (s) | Verdict | Re-run |
|---|---|---|---|---|---|
| W1a (before the release) | 17:54-18:07 | 16.9 % | 0.4167 / 0.4140 | contaminated (strays) | -- |
| W1b | 18:10-18:21 | 18.6 % | 0.4208 / 0.4993 | contaminated | -- |
| **W1c (claim 2, of record)** | 20:40-20:52 | 16.6 % | 0.3775 / 0.4242 | contaminated (strays from 20:47; close +7.4 %) | W1d |
| W1d | 20:55-21:11 | 21.2 % | 0.4515 / 0.5167 | contaminated throughout | none left |
| W2 (claim 4) | 21:13-22:14 | 99.3 % | 0.6026 / 0.4554 | contaminated | never |
| W3 | 22:16-22:20 | 74.4 % | 0.4241 / 0.6178 | contaminated | W3b |
| **W3b** | 22:29-22:32 | 23.8 % | 0.3801 / 0.4073 | **clean** | -- |
| W4 (claim 3 short + split) | 22:33-23:00 | 14.5 % | 0.3754 / 0.4853 | contaminated from 22:42; the production export row (22:34-22:40) stray-clean | gate failed twice in 10 min: none |
| W5 (claim 3 long, claim 5) | 23:09-03:00 | 81.4 % | 0.5750 / 0.3857 | contaminated | never |

All records are under `work/wp1.2b/`: `core/<window>/`, `bench/` (whole-clip runs, W4's in
`bench/W4/`) and `proxy/`. The 18 probes give a measured spread of the 4K GPU ancuti2018 core
over the block: 0.375-0.618 s, median 0.424 s.

## 4. Claim 1 -- modes and representative clips

From the inventory (`docs/reports/inventory-2026-10-18.md`):
- **3840x2160 @ 29.97 HEVC 8-bit 4:2:0** (34 files). Represented by GX011627 (Snorkel, 681
  frames): claim 2 reads frames 205-264, pts 205205..264264 at 1/30000 (6.840-8.809 s, from 30 %).
  GX011627 is also the short export. GX011625 (Snorkel, 14,938 frames, 498.43 s) is the long
  export AND the analysis-speed clip: one clip carries both legs (brief amendment).
- **1920x1080 @ 59.94 H.264 8-bit 4:2:0** (one file, `edits/compilation-20261010-1080p60`).
  Claim 2 only, a decode mode, frames 3236-3295, pts 3239236..3298295 at 1/60000 (53.987-54.972 s).
  Its N6 figure is the 60 fps one (0.0551 s/frame), measured at 1080p, not 4K.

No 5.3K, 10-bit, HDR or Log file exists, and GX011600 is not used (amendment).

## 5. Claim 2 -- per-frame core time on real frames

`bench.py --input`, timed `correct()` plus `synchronize()` per frame on host float32 frames,
the first frame discarded. "Clean" means no non-system process at 25 % or more in the run's two
stray checks. Spread = min / median / max over the four W1 attempts. Records:
`work/wp1.2b/core/W1{a-contaminated,b-contaminated,c,d}/`.

| Mode | Device | Method | N | Run of record W1c: median / p95 / drift | Spread over W1a-d (min / median / max) | Stray-clean medians | Part A synthetic | x 0.1101 s (W1c) |
|---|---|---|---|---|---|---|---|---|
| 4K | GPU | ancuti2018 | 60 | 0.3948 / 0.4361 / +7.1 % (clean) | 0.3948 / 0.4371 / 0.4851 | 0.4183, 0.4558, 0.3948 | 0.389 | 3.6x |
| 4K | GPU | c3 | 60 | 0.6391 / 0.6861 / +5.6 % (clean) | 0.6391 / 0.7777 / 0.8970 | 0.7077, 0.6391 | 0.652 | 5.8x |
| 4K | CPU | ancuti2018 | 10 | 12.61 / 13.41 (strays after) | 8.81 / 11.30 / 16.36 | 8.81 | 10.97 | 115x |
| 1080p60 | GPU | ancuti2018 | 60 | 0.0934 / 0.1090 / +0.4 % (strays) | 0.0934 / 0.0979 / 0.1396 | 0.1396, 0.0993 | -- | 1.7x of 0.0551 |
| 1080p60 | GPU | c3 | 60 | 0.1267 / 0.1416 / -1.8 % (strays) | 0.1223 / 0.1257 / 0.1820 | 0.1223 | -- | 2.3x of 0.0551 |
| 1080p60 | CPU | ancuti2018 | 10 | 2.489 / 4.455 (strays) | 1.956 / 2.263 / 5.480 | 2.037, 1.956 | -- | 45x of 0.0551 |

Device-resident (supplementary, same frames, W1c): 4K ancuti2018 0.2755 s, 4K c3 0.5135 s,
1080p ancuti2018 0.0605 s, 1080p c3 0.1231 s. Memory per 4K GPU run: CuPy pool reserved 1,712 MiB
(used 1,585), estimate 1,982 MiB (1.16x), Python RSS 3.0 GiB, of which 1.4 GiB is the 60 held
frames. At the end of the GPU loops the card ran at 1,500-2,475 MHz SM, P0, 34-67 W, with reasons
0x00 or 0x04 (power cap).

**Real content against the synthetic frame.**
- On the GPU the run-of-record medians are within 2 % of Part A (0.3948 vs 0.389; 0.6391 vs
  0.652). The real content does not change the GPU core cost measurably: every step is fixed-size
  work and no step depends on texture.
- The spread between attempts (up to +23 % for ancuti2018, +40 % for c3) is the machine, not the
  frames: the frames are identical in every attempt.
- On the CPU the one stray-clean 4K run was 8.81 s against 10.97 s synthetic. That is within the
  CPU spread here (8.8-16.4 s), so no content effect can be separated from load.

## 6. Claim 3 -- full clip end to end (N6 as written)

All rows: GPU, ancuti2018 at defaults, smoothing APPLIED from the analysis of the same clip and
decode (`median_gaussian` 2 s, PROVISIONAL per DR-25(3)), software decode, NVENC.

**Estimates recorded before the window opened** (ledger):
- GX011627: about 5.7 min.
- GX011625: 2.0 h. That is W4's 0.4856 s x 14,938, re-fixed from W1c's 0.3948 s (1.64 h for the
  core alone); the contaminated upper spread is 2.5 h.

The GX011625 run took 3.48 h, 1.7x its estimate (below).

| Clip | Row | Frames | Bracket | s/frame | min/min | x N6 | In-loop core median / p95 | Window | Record |
|---|---|---|---|---|---|---|---|---|---|
| GX011627 | production-shaped | 681 | 330.7 s | 0.4856 | 14.55 | 4.41 | 0.4664 / 0.6351 | W4, stray-clean (22:34-22:40) | `bench/W4/GX011627-end-to-end-ancuti2018-20261018-223431/` |
| GX011627 | device-resident (supplementary) | 681 | 243.5 s | 0.3576 | 10.72 | 3.25 | 0.3146 / 0.4652 | W4, contaminated | `bench/W4/GX011627-end-to-end-ancuti2018-20261018-224228/` |
| GX011625 | production-shaped (full clip) | 14,938 | 12,526.8 s (3 h 29 min) | 0.8386 | 25.13 | 7.62 | 0.7203 / 1.7474 | W5, contaminated | `bench/GX011625-end-to-end-ancuti2018-20261018-231103/` |

**Accounting** (GX011627 production row):
- main loop: wait for an output slot 0.0 s, wait for input 0.2 s, core 330.1 s;
- tail 0.33 s, startup 0.40 s, residual 0.008 s.
The decoder and encoder never held the loop up: the reader and writer threads ran beside the
core. The reader's pipe reads took a 0.096 s median, float conversion 0.033 s. The writer's
integer conversion took 0.065 s, its pipe write 0.003 s.

**GX011625 against GX011627** (0.84 vs 0.49 s/frame). The GX011625 run met the shared load in
nearly every stray check:
- Python batches were at 53-84 % per worker before and after the run.
- The card reported thermal slowdown (reasons 0x20 and 0x24), running at 750-2,460 MHz SM and
  71-91 °C in 205 samples.
- The core's median by quarter of the clip was 0.93, 0.74, 0.56 and 0.69 s.
- A snapshot during the run showed the GPU at 10 % utilisation at 2,460 MHz: the loop was waiting
  on the host, not on the card.
The full-clip figure is the sustained figure on this laptop as it was used that night. Spec 12
expects "sustained speed under heat may be lower than a single-frame timing suggests".

**In-loop core against claim 2** (0.4664 vs 0.3948 s, +18 %, both stray-clean). The cause is
attributed to concurrency. In the loop, the decoder (several CPU cores), the encoder and the two
conversion threads run beside `correct()` and compete for CPU, memory bandwidth and PCIe. The
device-resident row moves the same way: 0.3146 vs 0.2755 s, +14 %.

**The split on GX011627** (W4). The three stages run concurrently in the export, so the export
should fall between the largest stage and their sum. It does: 0.3948 <= **0.4856** <= 0.5205 s.
The pass-through rows ran under the shared load, so their figures are an upper bound.

| Pass | s/frame | min/min | Bracket | Notes |
|---|---|---|---|---|
| decode-only (decoder -> pipe -> reader) | 0.0886 | 2.66 | 60.4 s | pipe-bound: development 0.057 s; FFmpeg to NUL 0.0124 s |
| encode-only (raw spool -> writer -> NVENC -> mux) | 0.0371 | 1.11 | 25.3 s | the 16.9 GB spool was decoded before the window and deleted after |
| core alone (claim 2, W1c) | 0.3948 | -- | -- | |
| passthrough (decode + encode together, no core; supplementary) | 0.0880 | 2.64 | 59.9 s | equals decode-only: the encoder is hidden behind the decode pipe |

Every export's container was compared with its source (`compare.py`). All MANDATORY and REQUIRED
(D55/D114) items are SAME for GX011627 production and resident, GX011625, encode-only and
passthrough. The BEST-EFFORT differences are the 8 WP1.5 lists: timecode tag on the audio stream,
camera `udta` atoms, `ftyp` brands, container and stream tags, track flags, sample-entry child
boxes, and non-video edit lists as written. Compare records sit beside each output
(`<stem>_corrected.compare.json/.md`).

## 7. Claim 4 -- analysis speed (spec 7.2 decode pass + staged statistics)

GX011625, ancuti2018, 540-line proxy, STAGED, `median_gaussian` 2 s. W2, contaminated (Python
batches at 36-99 % before and after both runs), never re-run.

| Clip | Decode | Frames | Bracket | s/frame | min/min | Reader pipe read median | Main-loop work median | Measure s per stage (1/2/3) | Record |
|---|---|---|---|---|---|---|---|---|---|
| GX011625 | software | 14,938 | 1,777.2 s | 0.1190 | 3.57 | 0.106 | 0.074 | 372 / 311 / 302 | `bench/GX011625-analysis-ancuti2018-20261018-211458/` |
| GX011625 | `-hwaccel cuda` | 14,938 | 1,644.8 s | 0.1101 | 3.30 | 0.098 | 0.068 | 321 / 271 / 270 | `bench/GX011625-analysis-ancuti2018-20261018-214514/` |
| GX011627 | software (W3, contaminated) | 681 | 98.8 s | 0.1451 | 4.35 | 0.107 | 0.124 | 29 / 21 / 18 | `bench/GX011627-analysis-ancuti2018-20261018-221704/` |
| GX011627 | software (W3b, clean) | 681 | 48.2 s | 0.0707 | 2.12 | 0.067 | 0.050 | -- | `bench/GX011627-analysis-ancuti2018-20261018-222955/` |

- Hardware decode saves 7 % here. The pass is bound by the raw pipe (the reader's read takes
  longer than the main loop's work), and `-hwaccel cuda` only speeds the decode behind the pipe.
- At most 61 proxies are held: 3 stages x 30 frames of reach, plus 1.
- Smoothing costs 52-61 s per clip.
- Whether this is acceptable, and so whether D109 (sparse analysis) is named, is CHARC's call at
  WP1.6. The stray-clean GX011627 figure, 2.1 min/min, is the idle-machine indication.

## 8. Claim 5 -- memory (N4, V15)

From the GX011625 export (W5, the largest video mode: 4K 29.97 HEVC; no 5.3K exists).
RSS is sampled every 50 ms; device memory is CUDA `memGetInfo` every 50 ms.

| Figure | Value | Limit |
|---|---|---|
| Peak RSS, Python process | 1,996 MiB (OS peak working set 1,998) | |
| Peak RSS, process tree (Python + FFmpeg decoder + encoder, same samples) | **3,682 MiB** (children 1,740) | 16 GB (N4) |
| CuPy pool, reserved / peak used | 1,709 / 1,585 MiB | |
| `memory_estimate_bytes` (4K frame) | 1,982 MiB (1.16x the pool) | |
| Device-wide graphics memory, peak (context, NVENC, other processes) | **2,860 MiB** | 8,188 MiB |
| `nvidia-smi` used before / after | 165 / 2,019 MiB | |

The other passes:
- GX011627 export: tree 3,646 MiB, device 2,860 MiB.
- Analysis: tree 1,641-1,688 MiB, pool 688 MiB, device 1,828 MiB.

The estimate (1,982 MiB) is below the card's free memory, so the CPU fallback (D111) did not
engage for video.

**Largest photo: PENDING.** The inventory has no photo (the owner adds stills later), so this half
of claim 5 stays queued for the first photo in the inventory, not dropped (D102). Nothing was
substituted. That includes the `run.py --device gpu` reading, the estimate against the card's free
memory, and the forced `--device cpu` run.

## 9. Claim 6 -- proxy resolutions on real frames

20 consecutive GX011627 frames (pts 205205..224224), each statistic of `temporal.statistics_of`
at short sides 1080, 540 and 270 against the full frame (`temporal.proxy` block means), on the GPU.
Records: `work/wp1.2b/proxy/bench-gpu-GX011627-{ancuti2018,c3}-*.json`.

Cells: relative error mean / max over the 20 frames; then WP1.4's stability figure, the
relative step (mean |frame-to-frame change| / mean |value|), at that size.

| Statistic (ancuti2018) | 1080 | 540 | 270 | Relative step full / 1080 / 540 / 270 |
|---|---|---|---|---|
| compensation means (R) | 1e-10 / 1e-10 | 4e-11 / 1e-10 | 4e-11 / 1e-10 | 0.0074 at every size |
| white-balance means (R) | 1.1e-4 / 1.8e-4 | 3.5e-4 / 5.5e-4 | 7.7e-4 / 1.1e-3 | 0.0048 at every size |
| white-balance gains (R; B) | 7.3e-5; 3.3e-5 | 2.4e-4; 1.1e-4 | 5.3e-4; 2.4e-4 | 0.0043; 0.0042 |
| N{} low | **4.6 % / 6.2 %** | **14.1 % / 17.9 %** | **28.8 % / 33.2 %** | 0.0175 / 0.0152 / 0.0117 / 0.0102 |
| N{} high | **3.3 % / 4.4 %** | **11.2 % / 14.2 %** | **26.5 % / 30.3 %** | 0.0159 / 0.0143 / 0.0117 / 0.0090 |
| saliency input 1 L | 1.2e-4 | 4.4e-4 | 1.1e-3 | 0.0079-0.0080 |
| saliency input 2 L | 3.3e-3 | 7.7e-3 | 7.2e-3 | 0.0030 |

3C gives the same picture:
- N{} low 4.5 / 13.9 / 28.5 %, high 3.3 / 11.3 / 26.7 % (means);
- white-balance gains within 1.2e-3;
- steps within 0.0001 of Ancuti 2018's.

**Reading.**
- Means and gains survive any proxy size (area means preserve means).
- The N{} bounds do not: on real frames the 540-line proxy's bounds are 11-14 % narrower than
  the full frame's (WP1.4 measured 14 %, WP1.2A's synthetic 16 %), and 27-29 % at 270.
- Proxy bounds are steadier frame to frame (relative step 0.0117 at 540 against 0.0175 at full
  size): the proxy averages away the per-pixel noise that moves the percentiles.
- The WP2.1 question (WP1.4 section 8) stands with real-frame numbers: render with proxy bounds
  (stronger stretch, steadier) or measure N{} at render resolution.

## 10. Claim 7 -- optimisation candidates (listed, not done)

From the split and the rows above. These are CHARC's options for Gate 1; none was tried.

| # | Candidate | Targets | Cost / benefit estimate |
|---|---|---|---|
| 1 | Device-resident pipeline (copy back the output only) | the core's 15 D2H copies | Low cost (`correct()` returns device arrays; the render copies `output`). Measured -26 % end to end on GX011627 (0.4856 -> 0.3576 s/frame), -30 % on the core (0.3948 -> 0.2755). |
| 2 | Fewer intermediates materialised (no `Result` of 28 planes in the render) | allocations and copies inside the core | Moderate (a render-only path through the same functions, D107 keeps one code path). Bounded by #1's gain plus pool traffic; about 0.1 s/frame. |
| 3 | 3C large Gaussian by FFT or a recursive (IIR) filter | c3's sigma-108 Gaussian, 865 taps per axis | Moderate (numerical agreement to re-verify, D107/V-tests). c3 minus ancuti2018 is 0.24 s/frame at 4K (0.639 vs 0.395); most of it is this filter (Part A: about 97 ms per channel). |
| 4 | Pyramid memory (release the last input's pyramids during the collapse) | 13 1/3 of the 50 1/12 peak planes | Low. Memory only (up to -27 % of the peak, 1.7 -> 1.25 GiB at 4K); no speed. Matters for 5.3K and photos, not N6. |
| 5 | Decode/encode overlap with the core through pipelining | host-device copies and conversions in series with the kernels | Moderate (CUDA streams: upload frame i+1 and download frame i-1 while frame i computes). The decoder and encoder are already hidden behind the core (wait_input 0.2 s on 681 frames); what is left is the H2D/D2H inside `correct()`, the same 0.1-0.13 s as #1. |
| 6 | A raw transport with large writes (PyAV in-process decode/encode, or a pipe or socket written in 1 MB+ blocks) | the 32 KB pipe (decode-only 0.057-0.089 s/frame) | Low to moderate, WP2.1's transport choice (WP1.5 left PyAV against process-FFmpeg to WP2.1). Measured large-block pipe 4-6 ms/frame. It makes the analysis pass decode- and statistics-bound instead of pipe-bound (an estimated -20 to -30 % on analysis, from the clean GX011627 run: pipe read 0.067 s against 0.050 s of work per frame); little for export while the core dominates. |
| 7 | Sustained-thermal margin (laptop) | 0x20 thermal slowdown seen in W5 | Not a code change: the owner's power and cooling. The GX011625 core median moved 0.56-0.93 s across the clip. |

Even with #1, #3 and #5 together the 4K core stays near 0.2 s/frame (#1 alone gives 0.2755 s
device-resident). That is about 2x N6's 0.1101 s. N6 at 4K needs the Gate 1 options, or a change to
N6 (owner-reserved).

## 11. Deviations and notes

- **The long clip is GX011625, not GX011600** (amendment); GX011600 was never opened. GX011625
  carries claims 3 (long), 4 and 5 (video).
- **The analysis is a streaming form** of `analyse_staged` (bit-identical in tests). The batch form
  would need 93 GB for GX011625.
- **The analysis decodes `rgb24` through the export's pipe**, not 16-bit PNG as WP1.4 did. So the
  render and the analysis see the same bytes, and the per-frame witness can be exact.
- **The proxy and the statistics run on the GPU** (CuPy); WP1.4 built proxies in NumPy.
- **Encode-only is timed from a raw spool** decoded before the window (Reviewer A round 2). It
  stands beside the brief's "feed the decoded frames unchanged", which is the passthrough row.
- **10-bit and VFR paths are written but not exercised**: no such file exists. VFR and offset
  clips are refused.
- **The first per-frame window (W1, 17:26)** was discarded before the release (sibling load);
  W1a and W1b followed under the first ruling. All are kept in `work/wp1.2b/core/`.
- **The synthetic `--out` freedom in `bench.py`** is banked: Part A behaviour from `fedb8c9`,
  which unowned Part A tests rely on. Part B wrote no synthetic record.
