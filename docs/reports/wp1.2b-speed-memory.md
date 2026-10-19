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

**Remediation after Reviewer B** (brief `docs/briefs/wp1.2b-remediation-brief.md`).
- NO timed window was re-run, and no window record was rewritten.
- Every change either corrects text against the existing records, adds an UNTIMED verification
  on the existing outputs (the output witness, section 6), or changes code outside the timing
  bracket: the export's temporary name, the record provenance checks, and `decode_frames`'
  standard error.
- The per-frame spreads come from the records by `work/wp1.2b/remediation/per_frame_spread.py`
  (output `per_frame_spread.md` / `.json` beside it).

## 1. Results at a glance

| What | Figure | Against |
|---|---|---|
| Export, GX011627 (22.7 s, 681 frames), production-shaped; W4 contaminated, this row's stray checks clean | 0.4856 s/frame, **14.55 min/min** (per frame 0.378 / 0.466 / 1.064 s) | N6 3.3 min/min (0.1101 s/frame at 29.97 fps): **4.41x** |
| Export, GX011627, device-resident variant (supplementary; contaminated) | 0.3576 s/frame, 10.72 min/min (per frame 0.246 / 0.324 / 1.173 s) | 3.25x |
| Export, GX011625 (498.4 s, 14,938 frames), full clip (contaminated) | 0.8386 s/frame, **25.13 min/min**, 3.48 h (per frame 0.406 / 0.720 / 4.162 s) | 7.62x |
| Core alone, 4K GPU ancuti2018, real frames (claim 2) | 0.395 s (run of record); spread 0.375-0.618 s over 22 runs (18 probes, 4 claim-2 runs) | 3.6x on its own |
| Analysis pass, GX011625, software / `-hwaccel cuda` decode (contaminated) | 0.1190 / 0.1101 s/frame, 3.57 / 3.30 min/min (per frame 0.053 / 0.105 / 1.363 and 0.039 / 0.099 / 0.891 s) | (no target; D109 is CHARC's call) |
| Analysis pass, GX011627, re-run W3b (contaminated) | 0.0707 s/frame, 2.12 min/min (per frame 0.033 / 0.067 / 0.467 s) | -- |
| Peak RAM, GX011625 export (the process tree, FFmpeg included) | 3,682 MiB (Python alone 1,996) | N4 16 GB |
| Peak graphics memory, GX011625 export (device-wide, NVENC included) | 2,860 MiB (CuPy pool 1,709) | 8,188 MiB |
| Container of every export | MANDATORY and REQUIRED all SAME (`compare.py`) | WP1.5 |
| Output witness (untimed, after the exports): 24 frames per export against `correct(source i, statistics i)` | order correct on all 48 frames; GOP-start rule: GX011625 24 of 24, GX011627 23 of 24 (frame 503 at -3.35 dB); section 6 | -- |
| Largest photo (claim 5, second half) | PENDING: no photo in the inventory | D102 |

N6 is not met at 4K on this laptop under these conditions. That holds for the production-shaped
loop, for the device-resident variant, and for the core alone.

"Per frame" is the min / median / max of the row's per-frame time from its own record (the
main loop's wait_output + wait_input + core per frame; the warm-up excluded in claim 2), beside
the bracket figure, which stays the headline.

## 2. Instrument and method

**Code.**
- `tools/prototype/clip.py` (new): the analysis pass and the export loop.
- `tools/prototype/bench.py`: the real-frame source `--input`, the proxy study on real frames, and
  the whole-clip modes `analysis`, `end-to-end`, `decode-only`, `encode-only`, `passthrough`.
- `tests/test_prototype_clip.py`: 44 tests.
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
a short read is `PartialFrameError` and a wrong count is `FrameCountError`.

**In-loop witness (decode side).** It covers that the render's INPUT matches the analysis's
input: on every 30th frame and the last, the reader thread compares the decoded float frame's
channel means with the analysis record's, within 1e-8. That was 24 checks on GX011627 and 499 on
GX011625, all passed. It does NOT cover anything after the correction: the order of frames
through the writer, the integer conversion, the encoder or the muxer. Those are covered after
the export by the untimed output witness (section 6).

**The pipe.** FFmpeg writes a raw pipe in 32 KB blocks, and a Windows anonymous pipe carries
those slowly.

Record `work/wp1.2b/transport/transport-20261019.json` (instrument `transport.py` beside it), on
GX011627:
- conditions: 2026-10-19 03:25:50-03:27:11, head `13a498f`, clean tree, Best performance;
- stray checks: WmiPrvSE 60-73 % and, after, `vmmemWSL` 85 %;
- card: P8 -> P3.

| Measurement | Result |
|---|---|
| FFmpeg decoding with the export's conversion to NUL (no pipe) | 16.2 ms per frame |
| The same decode through the raw pipe into Python | 93.6 ms per frame, 266 MB/s, 517,560 reads, none over 32,768 bytes |
| A Python child writing 60 frames in 32 KB blocks | 91.9 ms per 4K frame |
| The same, in 1 MB / 25 MB blocks | 5.4 / 4.0 ms per 4K frame (4.6 / 6.2 GB/s) |

Python's 25 MB writes into the encoder's pipe take about 3-5 ms per frame (`write`, below). The
pipe was measured, not tuned (brief).

**The analysis pass** (spec 7.2 steps 1-2).
- The same decode and pipe, then each frame is copied to the GPU and area-averaged to the
  540-line proxy (`temporal.proxy`, a 4x4 block mean).
- The STAGED statistics of WP1.4 (D97) are computed with `median_gaussian` 2 s. That smoother is
  WP1.4's recommendation, PROVISIONAL per DR-25(3); the default is WP2.1's decision.
- `StagedStream` is `temporal.analyse_staged` in streaming form, bit-identical in tests. It holds
  at most 61 proxies instead of the clip: GX011625 would be 93 GB of float32 proxies.
- The render refuses a record from another file, frame count, pts list, parameter set, decode,
  smoother or statistic set. Since the remediation (B5) it also refuses another time base, frame
  rate, bit depth or full decode command. The records of both exports pass these checks: the
  output witness runs `check_statistics_record` on them.

**Timing bracket.** It runs from the moment the first decoded frame has been read whole to the
moment BOTH FFmpeg child processes have been reaped. The decoder's exit status is collected
first, then the encoder's; the encoder exits after its muxer has closed the file. Which child
actually exited first, and the gap between them, was NOT recorded; the records hold only the
tail (last frame queued -> both reaped), 0.33 s on the GX011627 export and 0.99 s on GX011625.
For an analysis the bracket ends when the decoder has been reaped and the last statistic
computed.

**Export file (remediation B4).** Since the remediation the export writes `<stem>.partial.mp4`
and renames it to the final name only after a successful pass, after the bracket has closed. It
never overwrites an existing final file and removes the partial file on any failure. The timed
runs predate this change. The rename lies outside the bracket, so no timed figure moves. Minutes per minute = bracket / clip length
(frames x 1001/30000 s). The per-frame series, plus the tail after the last hand-off, close on
the bracket within `residual_s`. For example, the GX011627 export had a 0.008 s residual on 330.7 s.

**Ambient record (every window).**
- head SHA and changed files;
- the window's local start and end;
- the power scheme (Balanced, `381b4222-...`) and overlay (Best performance, in every record);
- AC power, battery 80-82 % (per record);
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
| W3b (re-run) | 22:29-22:32 | 23.8 % | 0.3801 / 0.4073 | contaminated: the closing probe's stray check after it shows `python.exe` PID 17192 at 53.0 % (no record ties that PID to the instrument; it appears in this record only) | none left |
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

| Mode | Device | Method | N | Run of record W1c (contaminated window): median / p95 / drift; per frame min / median / max | Spread over W1a-d (min / median / max) | Stray-clean medians | Part A synthetic | x 0.1101 s (W1c) |
|---|---|---|---|---|---|---|---|---|
| 4K | GPU | ancuti2018 | 60 | 0.3948 / 0.4361 / +7.1 % (row's strays clean); 0.3701 / 0.3948 / 0.4500 | 0.3948 / 0.4371 / 0.4851 | 0.4183, 0.4558, 0.3948 | 0.389 | 3.6x |
| 4K | GPU | c3 | 60 | 0.6391 / 0.6861 / +5.6 % (row's strays clean); 0.6155 / 0.6391 / 0.6973 | 0.6391 / 0.7777 / 0.8970 | 0.7077, 0.6391 | 0.652 | 5.8x |
| 4K | CPU | ancuti2018 | 10 | 12.61 / 13.41 (strays after); 12.34 / 12.61 / 13.64 | 8.81 / 11.30 / 16.36 | 8.81 | 10.97 | 115x |
| 1080p60 | GPU | ancuti2018 | 60 | 0.0934 / 0.1090 / +0.4 % (strays); 0.0854 / 0.0934 / 0.1284 | 0.0934 / 0.0979 / 0.1396 | 0.1396, 0.0993 | -- | 1.7x of 0.0551 |
| 1080p60 | GPU | c3 | 60 | 0.1267 / 0.1416 / -1.8 % (strays); 0.1157 / 0.1267 / 0.1562 | 0.1223 / 0.1257 / 0.1820 | 0.1223 | -- | 2.3x of 0.0551 |
| 1080p60 | CPU | ancuti2018 | 10 | 2.489 / 4.455 (strays); 2.366 / 2.489 / 4.541 | 1.956 / 2.263 / 5.480 | 2.037, 1.956 | -- | 45x of 0.0551 |

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

| Clip | Row | Frames | Bracket | s/frame | min/min | x N6 | Per frame min / median / max | Window | Record |
|---|---|---|---|---|---|---|---|---|---|
| GX011627 | production-shaped | 681 | 330.7 s | 0.4856 | 14.55 | 4.41 | 0.378 / 0.466 / 1.064 | W4 (contaminated window; this row's stray checks clean, 22:34-22:40) | `bench/W4/GX011627-end-to-end-ancuti2018-20261018-223431/` |
| GX011627 | device-resident (supplementary) | 681 | 243.5 s | 0.3576 | 10.72 | 3.25 | 0.246 / 0.324 / 1.173 | W4, contaminated | `bench/W4/GX011627-end-to-end-ancuti2018-20261018-224228/` |
| GX011625 | production-shaped (full clip) | 14,938 | 12,526.8 s (3 h 29 min) | 0.8386 | 25.13 | 7.62 | 0.406 / 0.720 / 4.162 | W5, contaminated | `bench/GX011625-end-to-end-ancuti2018-20261018-231103/` |

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
The full-clip figure is the sustained figure on this laptop as it was used that night. Spec 12
expects "sustained speed under heat may be lower than a single-frame timing suggests".

**In-loop core against claim 2** (0.4664 vs 0.3948 s, +18 %; both rows' own stray checks
clean, both windows contaminated).

HYPOTHESIS, not established: the difference comes from concurrency. In the loop, the decoder
(several CPU cores), the encoder and the two conversion threads run beside `correct()` and
compete for CPU, memory bandwidth and PCIe. What supports it: the device-resident row moves the
same way, 0.3146 vs 0.2755 s, +14 %.

The confirming run, not made here: the core timed inside the loop with the decoder and encoder
replaced by in-memory frames (no concurrent processes), against claim 2 in the same window.

**The split on GX011627** (W4). The three stages run concurrently in the export, so the export
should fall between the largest stage and their sum. It does: 0.3948 <= **0.4856** <= 0.5205 s.
The pass-through rows ran under the shared load, so their figures are an upper bound.

| Pass (all W4, contaminated) | s/frame | min/min | Bracket | Notes (per frame min / median / max) |
|---|---|---|---|---|
| decode-only (decoder -> pipe -> reader) | 0.0886 | 2.66 | 60.4 s | 0.0003 / 0.0858 / 0.1986; | pipe-bound: the transport record gives 0.0936 through the pipe against 0.0162 to NUL |
| encode-only (raw spool -> writer -> NVENC -> mux) | 0.0371 | 1.11 | 25.3 s | 0.0015 / 0.0343 / 0.8140; the 16.9 GB spool was decoded before the window and deleted after |
| core alone (claim 2, W1c) | 0.3948 | -- | -- | |
| passthrough (decode + encode together, no core; supplementary) | 0.0880 | 2.64 | 59.9 s | 0.0019 / 0.0845 / 1.3111; equals decode-only: the encoder is hidden behind the decode pipe |

Every export's container was compared with its source (`compare.py`). All MANDATORY and REQUIRED
(D55/D114) items are SAME for GX011627 production and resident, GX011625, encode-only and
passthrough. The BEST-EFFORT differences are the 8 WP1.5 lists: timecode tag on the audio stream,
camera `udta` atoms, `ftyp` brands, container and stream tags, track flags, sample-entry child
boxes, and non-video edit lists as written. Compare records sit beside each output
(`<stem>_corrected.compare.json/.md`).

**Output witness** (remediation B3; untimed, run on the existing exports after the event;
`clip.py witness`; records `output-witness.json` in each run folder).

For 24 frame indices spread over each clip, the first and last included, the witness:
- decodes output frame i;
- recomputes the expected frame through the export's own conversions:
  `correct(source frame i, params, statistics = the analysis record's smoothed statistics i)`;
- scores own_i = PSNR(output i, expected i), whole-frame 8-bit RGB.

It covers what the in-loop witness does not: the writer, the integer conversion, the encoder and
the muxer.

The pass criterion, and how it was reached, stated plainly:
1. The first criterion was an absolute 28 dB floor, from WP1.5's identity re-encode of GX011627
   (Y 32.27 dB at worst).
   - It failed GX011627 frame 30 at 27.79 dB.
   - A reproduction showed the encoder's own loss on that frame, encoding the expected frames
     alone through the export's chain, is 28.76 dB
     (`work/wp1.2b/remediation/frame30_repro.json`).
   - The orchestrator replaced the criterion BEFORE re-scoring.
2. The second criterion was relative per frame: own_i >= ref_i - 2.0 dB, with ref_i from the
   expected frames i-1, i, i+1 encoded alone.
   - It failed 18 of 24 frames on GX011627 and 13 of 24 on GX011625.
   - Order was correct on every row.
   - That reference was unrepresentative: the export has a 250-frame GOP (I-frames at 0, 250, 500
     on GX011627) with B and P frames, and the 3-frame reference codes frame i next to a fresh
     I-frame (`remediation/gx011627-out-pict-types.txt`, `gop_reference_repro.json`).
   - The orchestrator replaced the reference BEFORE re-scoring.
3. ADOPTED: ref_i from a GOP-start reference.
   - The expected frames from the export's GOP start (the last I-frame at or before i, from the
     OUTPUT's picture types read with ffprobe) through i+1 are encoded through the export's own
     encode chain, then decoded; ref_i = PSNR(decoded expected i, expected i).
   - Pass: own_i >= ref_i - 2.0 dB and own_i >= 20 dB (a sanity floor), and own_i strictly
     above its PSNR against the expected frames i-1 and i+1 (order).
   - The planted controls fail by name under it: a frame swap raises `OutputOrderError`; a
     30-frame statistics shift raises `OutputMismatchError`.

Each row of the records keeps all three verdicts (`first_floor_ok`, `relative3_ok`, `match_ok`
with `ref_db`), so nothing is hidden. The first two records are kept too, as
`output-witness-first-criterion-28dB.json` and `output-witness-relative-3frame-reference.json`.

| Export | Frames | Order (strict) | GOP-start rule | own - ref (min .. max) | own_i | best neighbour | 28 dB criterion | 3-frame criterion |
|---|---|---|---|---|---|---|---|---|
| GX011627 (W4 production) | 24 | all correct | 23 of 24; frame 503 (a B-frame 3 after the I-frame at 500) at 35.39 dB against ref 38.74 (-3.35 dB) | -3.35 .. +0.05 dB | 27.79-39.67 dB | 28.3 dB (frame 680) | fails frame 30 | fails 18 |
| GX011625 (W5) | 24 | all correct | **24 of 24** | -1.73 .. +0.31 dB | 29.67-42.68 dB | 34.2 dB | passes | fails 13 |

GX011627 frame 503 is reported as measured, as the orchestrator ruled (no further stop on a
witness frame with the order correct). The frame is in its right place (own 35.39 dB against
22.3 dB for its best neighbour) and corrected with its own statistics. It scores 3.35 dB below a
reference that encoded only frames 500-504 from a fresh start. That reference's encoder history
differs from the export's, which had coded 500 frames before. That cause is a HYPOTHESIS, not
established here.

## 7. Claim 4 -- analysis speed (spec 7.2 decode pass + staged statistics)

GX011625, ancuti2018, 540-line proxy, STAGED, `median_gaussian` 2 s. W2, contaminated (Python
batches at 36-99 % before and after both runs), never re-run.

| Clip | Decode | Frames | Bracket | s/frame | min/min | Reader pipe read median | Main-loop work median | Measure s per stage (1/2/3) | Record |
|---|---|---|---|---|---|---|---|---|---|
| GX011625 | software (W2, contaminated) | 14,938 | 1,777.2 s | 0.1190 | 3.57 | 0.106 | 0.074 | 372 / 311 / 302 | `bench/GX011625-analysis-ancuti2018-20261018-211458/` |
| GX011625 | `-hwaccel cuda` (W2, contaminated) | 14,938 | 1,644.8 s | 0.1101 | 3.30 | 0.098 | 0.068 | 321 / 271 / 270 | `bench/GX011625-analysis-ancuti2018-20261018-214514/` |
| GX011627 | software (W3, contaminated) | 681 | 98.8 s | 0.1451 | 4.35 | 0.107 | 0.124 | 29 / 21 / 18 | `bench/GX011627-analysis-ancuti2018-20261018-221704/` |
| GX011627 | software (W3b re-run, contaminated) | 681 | 48.2 s | 0.0707 | 2.12 | 0.067 | 0.050 | -- | `bench/GX011627-analysis-ancuti2018-20261018-222955/` |

- Hardware decode saves 7 % here. The pass is bound by the raw pipe (the reader's read takes
  longer than the main loop's work), and `-hwaccel cuda` only speeds the decode behind the pipe.
- At most 61 proxies are held: (stages - 1) x reach + 1 = (3 - 1) x 30 + 1.
- Smoothing costs 52-61 s per clip.
- Whether this is acceptable, and so whether D109 (sparse analysis) is named, is CHARC's call at
  WP1.6. No analysis row is clean under the contamination rule. The GX011627 re-run (W3b,
  2.1 min/min) had the least load of them, but its window is contaminated (a 53 % `python.exe`
  in its last stray check). It is not an idle-machine figure either: its gate read 23.8 % total
  CPU, and WmiPrvSE ran at 86-88 % of a CPU.

Per-frame spread (min / median / max, s, from each record):

| Row | Per frame |
|---|---|
| GX011625 software | 0.053 / 0.105 / 1.363 |
| GX011625 `-hwaccel cuda` | 0.039 / 0.099 / 0.891 |
| GX011627 W3 | 0.039 / 0.129 / 1.458 |
| GX011627 W3b | 0.033 / 0.067 / 0.467 |

## 8. Claim 5 -- memory (N4, V15)

From the GX011625 export (W5, the largest video mode: 4K 29.97 HEVC; no 5.3K exists).
RSS and device memory (CUDA `memGetInfo`) are sampled by one thread. It waits 50 ms between
samples, and each sample also lists the children and reads the device, so the actual mean
interval was longer: 81 ms in this run (154,868 samples over 12,526.8 s), 62-81 ms across the
whole-clip runs (`per_frame_spread.md`, last column). A peak shorter than that can be missed.

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

The table above is a selection; the appendix at the end lists every statistic of both
methods, with absolute differences beside the relative ones. 3C:
- N{} low 4.5 / 13.9 / 28.5 %, high 3.3 / 11.3 / 26.7 % (means);
- white-balance means and gains within 5.3e-4 at 1080, 1.8e-3 at 540 and 3.3e-3 at 270 (largest:
  the blue white-balance mean).

**Reading.**
- The RGB channel means survive any proxy size (relative error 1e-10): area means preserve means.
- The white-balance means and gains stay close (largest relative error over the 20 frames):
  - Ancuti 2018: 1.8e-4 at 1080, 5.5e-4 at 540, 1.1e-3 at 270.
  - 3C, whose local compensation is not linear: 5.3e-4, 1.8e-3, 3.3e-3.
- The Lab saliency means move more in relative terms where a component lies near 0.
  - Input 2's `b` at 540: Ancuti 2018 1.9e-1 mean, 1.2 max; 3C 1.1e-1 mean.
  - Input 2's `a` at 540: 4.6e-2 and 7.4e-2.
  - In absolute terms all are small on the Lab scale of 0-100 (the weight divides by 100): at
    540, L 0.35-0.40, a 0.03-0.04, b 0.015-0.017 mean; at most 0.54 L and 0.10 a at 270.
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
| 6 | A raw transport with large writes (PyAV in-process decode/encode, or a pipe or socket written in 1 MB+ blocks) | the 32 KB pipe (decode-only 0.089-0.094 s/frame against 0.016 s decoding to NUL) | Low to moderate, WP2.1's transport choice (WP1.5 left PyAV against process-FFmpeg to WP2.1). The transport record gives 4.0-5.4 ms/frame for 1 MB+ blocks. ESTIMATE: it would make the analysis pass decode- and statistics-bound instead of pipe-bound, about -20 to -30 % on analysis. That rests on the GX011627 W3b run (contaminated): pipe read 0.067 s against 0.050 s of work per frame. Little for export while the core dominates. |
| 7 | Sustained-thermal margin (laptop) | 0x20 thermal slowdown seen in W5 | Not a code change: the owner's power and cooling. The GX011625 core median moved 0.56-0.93 s across the clip. |

ESTIMATE, not a measured combination. The candidates do not add:
- #3 applies to c3 only. It does nothing for ancuti2018, the default.
- #1 and #5 overlap: both remove the host-device copies, #1 by not making them, #5 by hiding
  them.

| Method | Measured, device-resident (#1) | Estimate with #5 on top | Estimate with #3 | N6 |
|---|---|---|---|---|
| ancuti2018 | 0.2755 s (W1c) | at most the part of 0.2755 that is copies (#5 hides what #1 did not remove: the input upload and the output download, about 0.02-0.03 s at PCIe 4.0 speeds); so about 0.25 s | -- | 0.1101 s; about 2.3x |
| c3 | 0.5135 s | about 0.49 s | minus up to 0.24 s, about 0.25-0.29 s | about 2.3-2.6x |

Confirming them needs the changes themselves (WP2.1/WP3.1). Either way, N6 at 4K needs the
Gate 1 options or a change to N6 (owner-reserved).

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

### Appendix -- claim 6, every statistic (generated from the two records)

Per cell: relative error mean / max over the 20 frames (|proxy - full| / |full|); the
absolute difference mean / max in the statistic's own unit (Lab units for saliency means,
whose a and b components lie near 0, so their relative errors are inflated); the relative step
at that size. `full` is the 2160-line frame.

**ancuti2018** (`proxy/bench-gpu-GX011627-ancuti2018-20261019-030141.json`)

| Statistic | full: step | 1080: rel / abs / step | 540: rel / abs / step | 270: rel / abs / step |
|---|---|---|---|---|
| `compensation_means.R` | 0.0074 | 9.7e-11/1.4e-10 / 4.4e-11/6.2e-11 / 0.0074 | 4.1e-11/1.0e-10 / 1.8e-11/4.7e-11 / 0.0074 | 3.9e-11/1.0e-10 / 1.8e-11/4.6e-11 / 0.0074 |
| `compensation_means.G` | 0.0047 | 2.1e-11/7.3e-11 / 1.2e-11/4.1e-11 / 0.0047 | 2.7e-11/7.3e-11 / 1.5e-11/4.2e-11 / 0.0047 | 4.5e-11/1.2e-10 / 2.6e-11/6.9e-11 / 0.0047 |
| `compensation_means.B` | 0.0079 | 1.1e-10/1.6e-10 / 5.6e-11/8.4e-11 / 0.0079 | 5.5e-11/1.2e-10 / 2.7e-11/5.8e-11 / 0.0079 | 5.1e-11/1.5e-10 / 2.5e-11/7.0e-11 / 0.0079 |
| `compensation_alpha.red` | 0.0000 | 0.0e+00/0.0e+00 / 0.0e+00/0.0e+00 / 0.0000 | 0.0e+00/0.0e+00 / 0.0e+00/0.0e+00 / 0.0000 | 0.0e+00/0.0e+00 / 0.0e+00/0.0e+00 / 0.0000 |
| `white_balance_means.R` | 0.0048 | 1.1e-04/1.8e-04 / 5.2e-05/8.9e-05 / 0.0048 | 3.5e-04/5.5e-04 / 1.7e-04/2.7e-04 / 0.0048 | 7.7e-04/1.1e-03 / 3.8e-04/5.4e-04 / 0.0048 |
| `white_balance_means.G` | 0.0047 | 2.1e-11/7.3e-11 / 1.2e-11/4.1e-11 / 0.0047 | 2.7e-11/7.3e-11 / 1.5e-11/4.2e-11 / 0.0047 | 4.5e-11/1.2e-10 / 2.6e-11/6.9e-11 / 0.0047 |
| `white_balance_means.B` | 0.0079 | 1.1e-10/1.6e-10 / 5.6e-11/8.4e-11 / 0.0079 | 5.5e-11/1.2e-10 / 2.7e-11/5.8e-11 / 0.0079 | 5.1e-11/1.5e-10 / 2.5e-11/7.0e-11 / 0.0079 |
| `white_balance_gains.R` | 0.0043 | 7.3e-05/1.2e-04 / 7.9e-05/1.3e-04 / 0.0043 | 2.4e-04/3.8e-04 / 2.6e-04/4.0e-04 / 0.0043 | 5.3e-04/7.5e-04 / 5.7e-04/8.0e-04 / 0.0043 |
| `white_balance_gains.G` | 0.0005 | 3.3e-05/5.6e-05 / 3.0e-05/5.0e-05 / 0.0005 | 1.1e-04/1.7e-04 / 9.8e-05/1.5e-04 / 0.0005 | 2.4e-04/3.4e-04 / 2.2e-04/3.0e-04 / 0.0005 |
| `white_balance_gains.B` | 0.0042 | 3.3e-05/5.6e-05 / 3.5e-05/5.8e-05 / 0.0042 | 1.1e-04/1.7e-04 / 1.1e-04/1.8e-04 / 0.0042 | 2.4e-04/3.4e-04 / 2.5e-04/3.5e-04 / 0.0042 |
| `normalisation_bounds.low` | 0.0175 | 4.6e-02/6.2e-02 / 1.0e-02/1.5e-02 / 0.0152 | 1.4e-01/1.8e-01 / 3.0e-02/4.3e-02 / 0.0117 | 2.9e-01/3.3e-01 / 6.2e-02/8.1e-02 / 0.0102 |
| `normalisation_bounds.high` | 0.0159 | 3.2e-02/4.4e-02 / 8.3e-03/1.2e-02 / 0.0143 | 1.1e-01/1.4e-01 / 2.9e-02/3.9e-02 / 0.0117 | 2.6e-01/3.0e-01 / 6.7e-02/8.3e-02 / 0.0090 |
| `saliency_means.input1.L` | 0.0079 | 1.2e-04/2.0e-04 / 5.2e-03/7.7e-03 / 0.0080 | 4.4e-04/6.9e-04 / 1.8e-02/2.7e-02 / 0.0080 | 1.0e-03/1.6e-03 / 4.4e-02/6.5e-02 / 0.0080 |
| `saliency_means.input1.a` | 0.0501 | 1.1e-03/2.0e-03 / 6.3e-03/1.3e-02 / 0.0502 | 3.5e-03/7.4e-03 / 1.9e-02/3.8e-02 / 0.0505 | 7.2e-03/2.0e-02 / 3.5e-02/6.5e-02 / 0.0511 |
| `saliency_means.input1.b` | 0.0352 | 5.1e-03/8.8e-03 / 7.7e-03/1.5e-02 / 0.0349 | 1.3e-02/2.3e-02 / 2.0e-02/3.9e-02 / 0.0349 | 2.0e-02/3.5e-02 / 3.1e-02/5.9e-02 / 0.0353 |
| `saliency_means.input2.L` | 0.0030 | 3.3e-03/4.5e-03 / 1.7e-01/2.4e-01 / 0.0030 | 7.7e-03/9.6e-03 / 4.0e-01/5.1e-01 / 0.0030 | 7.2e-03/1.0e-02 / 3.8e-01/5.4e-01 / 0.0031 |
| `saliency_means.input2.a` | 0.0481 | 1.7e-02/2.7e-02 / 1.4e-02/2.4e-02 / 0.0473 | 4.6e-02/7.1e-02 / 3.9e-02/6.6e-02 / 0.0463 | 7.7e-02/1.3e-01 / 6.5e-02/1.0e-01 / 0.0457 |
| `saliency_means.input2.b` | 0.0813 | 6.0e-02/3.9e-01 / 4.5e-03/6.2e-03 / 0.0843 | 1.9e-01/1.2e+00 / 1.5e-02/1.9e-02 / 0.0914 | 4.1e-01/2.6e+00 / 3.1e-02/4.1e-02 / 0.1032 |

**c3** (`proxy/bench-gpu-GX011627-c3-20261019-030334.json`)

| Statistic | full: step | 1080: rel / abs / step | 540: rel / abs / step | 270: rel / abs / step |
|---|---|---|---|---|
| `white_balance_means.R` | 0.0043 | 1.4e-04/2.2e-04 / 7.5e-05/1.2e-04 / 0.0043 | 4.5e-04/6.7e-04 / 2.5e-04/3.7e-04 / 0.0043 | 8.9e-04/1.2e-03 / 4.9e-04/6.7e-04 / 0.0043 |
| `white_balance_means.G` | 0.0043 | 6.1e-05/1.1e-04 / 3.4e-05/5.9e-05 / 0.0043 | 2.1e-04/3.4e-04 / 1.2e-04/1.9e-04 / 0.0043 | 4.3e-04/6.0e-04 / 2.4e-04/3.4e-04 / 0.0043 |
| `white_balance_means.B` | 0.0051 | 2.8e-04/5.3e-04 / 1.5e-04/2.9e-04 / 0.0051 | 1.0e-03/1.8e-03 / 5.3e-04/9.6e-04 / 0.0051 | 2.1e-03/3.3e-03 / 1.1e-03/1.8e-03 / 0.0051 |
| `white_balance_gains.R` | 0.0005 | 2.3e-05/3.6e-05 / 2.3e-05/3.5e-05 / 0.0005 | 6.8e-05/1.1e-04 / 6.8e-05/1.1e-04 / 0.0005 | 1.3e-04/2.5e-04 / 1.3e-04/2.5e-04 / 0.0004 |
| `white_balance_gains.G` | 0.0006 | 1.8e-04/3.2e-04 / 1.8e-04/3.1e-04 / 0.0006 | 6.2e-04/1.0e-03 / 6.1e-04/1.0e-03 / 0.0006 | 1.3e-03/1.9e-03 / 1.2e-03/1.8e-03 / 0.0006 |
| `white_balance_gains.B` | 0.0011 | 1.6e-04/3.2e-04 / 1.7e-04/3.3e-04 / 0.0011 | 5.9e-04/1.1e-03 / 6.0e-04/1.1e-03 / 0.0011 | 1.2e-03/2.1e-03 / 1.3e-03/2.1e-03 / 0.0010 |
| `normalisation_bounds.low` | 0.0176 | 4.5e-02/6.1e-02 / 9.8e-03/1.5e-02 / 0.0156 | 1.4e-01/1.8e-01 / 3.0e-02/4.3e-02 / 0.0117 | 2.9e-01/3.3e-01 / 6.1e-02/8.0e-02 / 0.0114 |
| `normalisation_bounds.high` | 0.0154 | 3.3e-02/4.4e-02 / 8.5e-03/1.2e-02 / 0.0143 | 1.1e-01/1.4e-01 / 2.9e-02/4.0e-02 / 0.0114 | 2.7e-01/3.1e-01 / 6.9e-02/8.6e-02 / 0.0087 |
| `saliency_means.input1.L` | 0.0064 | 6.5e-05/9.4e-05 / 2.8e-03/4.0e-03 / 0.0064 | 2.1e-04/2.9e-04 / 9.2e-03/1.2e-02 / 0.0064 | 6.4e-04/8.0e-04 / 2.8e-02/3.4e-02 / 0.0064 |
| `saliency_means.input1.a` | 0.0400 | 2.8e-03/4.0e-03 / 1.6e-03/2.8e-03 / 0.0400 | 1.7e-02/2.6e-02 / 9.7e-03/1.5e-02 / 0.0403 | 5.3e-02/8.0e-02 / 3.0e-02/4.6e-02 / 0.0414 |
| `saliency_means.input1.b` | 0.0098 | 2.7e-04/7.3e-04 / 1.3e-04/3.5e-04 / 0.0098 | 8.3e-03/1.2e-02 / 3.9e-03/5.3e-03 / 0.0099 | 4.0e-02/5.2e-02 / 1.9e-02/2.4e-02 / 0.0105 |
| `saliency_means.input2.L` | 0.0027 | 2.9e-03/3.9e-03 / 1.6e-01/2.1e-01 / 0.0026 | 6.6e-03/8.8e-03 / 3.5e-01/4.7e-01 / 0.0026 | 5.2e-03/9.3e-03 / 2.7e-01/4.8e-01 / 0.0028 |
| `saliency_means.input2.a` | 0.0157 | 2.8e-02/3.9e-02 / 9.8e-03/1.5e-02 / 0.0154 | 7.4e-02/1.1e-01 / 2.6e-02/4.1e-02 / 0.0167 | 1.2e-01/1.6e-01 / 4.2e-02/6.0e-02 / 0.0183 |
| `saliency_means.input2.b` | 0.0143 | 3.7e-02/4.9e-02 / 5.6e-03/7.1e-03 / 0.0130 | 1.1e-01/1.5e-01 / 1.7e-02/2.2e-02 / 0.0111 | 2.1e-01/2.6e-01 / 3.2e-02/3.8e-02 / 0.0106 |
