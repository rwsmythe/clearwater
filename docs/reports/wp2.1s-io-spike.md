# WP2.1S -- transport and photo I/O spike

Evidence for WP2.1 (plan section 8.3): it closes AD-2 (frame transport) and AD-17 (16-bit PNG +
ICC + EXIF), and confirms or corrects AD-18 (licences). Brief `docs/briefs/wp2.1s-brief.md`
(FINAL, `aa1f5f0`). Instrument `tools/spike_io/transport.py`. Every record is under
`C:\Users\rwsmy\clearwater\work\wp2.1s\` (not committed). The footage folder was input only.

**Status of this text:** claim 1 (transport) is complete. Claim 2 (photo I/O) and claim 3
(licences) are PENDING. They follow in a later commit.

## 1. Results at a glance (transport)

- **Every row is the SAME WORK.** All 18 transport forms decode the same 681 frames to the same
  bytes as row a: per-frame SHA-256 over the whole clip. Every pts side channel delivers 681/681
  pts exactly as ffprobe lists them.
- **The 32 KB writes are fixed in FFmpeg; the cure is on the reading side.** FFmpeg's own AVIO
  statistics show 32,741-byte writes on average whatever the knob: `-avioflags direct`, the pipe
  protocol's `-blocksize`, or both. That is 517,560 writes for the clip. What removes the
  bottleneck is the pipe's buffer. A 32 MiB anonymous pipe takes the decode from 55.9 to 16.1
  ms/frame, which is about FFmpeg's own decode-plus-conversion speed (13.5 ms to the null muxer).
  This buffer is a Windows platform tuning with an automatic, byte-identical fallback to the
  default pipe (section 6).
- **Best rows (median s/frame, clean windows):**

  | Row | ms/frame |
  |---|---|
  | b-cuda (32 MiB pipe, `-hwaccel cuda`) | 13.0 |
  | b (32 MiB pipe) | 16.1 |
  | s (loopback TCP socket) | 24.3 |
  | c-cuda-auto (PyAV, CUDA decode) | 42.4 |
  | c-auto (PyAV, `thread_type="AUTO"`) | 43.0 |
  | a (today's pipe) | 55.9 |
  | c (PyAV default threading) | 76.0 |

  The side channel (`showinfo`) costs 0.6-1.0 ms/frame on the fast rows.
- **Analysis-pass PROJECTION** with Part B's 0.050 s/frame of work (contaminated):

  | Row | Serial sum (s/frame, min/min) | Overlapped with a reader thread (s/frame, min/min) |
  |---|---|---|
  | b+pts | 0.067 (2.01) | 0.050 (1.50) |
  | b-cuda+pts | 0.064 (1.91) | 0.050 (1.50) |
  | today's pipe | 0.106 (3.17) | 0.056 (1.67) |

  Part B measured 0.0707 on this pipe (2.12 min/min).
- **AD-10's flag set against today's chain** (expected, not a defect; CHARC `871d4f17e78c10b3`):
  max absolute difference 19, mean 0.50 per sample (section 4).
- **Row a does not reproduce Part B's 93.6 ms/frame.** It measures 55.9 ms/frame here, in a clean
  window (section 3).

## 2. Instrument and method

**Rows** (`ROWS` in `transport.py`). Every FFmpeg row runs `clip.decode_command(source)` as
merged: the tag-driven `scale` with `in_range`, `in_color_matrix`, `out_range=full` and
`flags=accurate_rnd`, to `rgb24`, with `-noautorotate`, `-map 0:v:0` and `-fps_mode
passthrough`. The only changes are those named in the row. Every FFmpeg command writes to
`pipe:1` or a loopback socket and opens no output file. Calibration row n uses `-f null -`, which
opens nothing.

| Row | Transport |
|---|---|
| a | `decode_command` as-is through CPython's default anonymous pipe (`subprocess.PIPE`), read with `clip.read_frame` (`readinto` into one buffer from `clip.frame_buffer`) |
| a-direct / a-blocksize / a-direct-blocksize | row a plus `-avioflags direct`, plus `-blocksize 33554432`, or plus both, as output options |
| b-1m, b | row a's command into an anonymous pipe created with a 1 MiB / 32 MiB buffer (`_winapi.CreatePipe(None, size)`), read the same way |
| b-direct-blocksize | b plus both FFmpeg knobs |
| b-cuda | b plus `-hwaccel cuda` (`decode_command(hwaccel="cuda")`) |
| b-fallback+pts | b+pts with the large pipe forced to fail (`force_fallback`): the transport falls back to the default pipe automatically (identity only, untimed) |
| s | row a's command with output `tcp://127.0.0.1:<port>`. This process listens (SO_RCVBUF 32 MiB requested) and reads with `clip.read_frame` on `socket.makefile("rb", buffering=0)` |
| c, c-auto | PyAV 16.1.0 (bundled FFmpeg 8.0.1), software decode, PyAV's default threading (SLICE, 16 threads) / `thread_type="AUTO"`. Each frame is converted by `VideoFrame.reformat(format="rgb24", src_colorspace="itu709", dst_colorspace="itu601", src_color_range="JPEG", dst_color_range="JPEG", interpolation=SWS_ACCURATE_RND)`, then `to_ndarray()` |
| c-cuda, c-cuda-auto | as c / c-auto with `HWAccel("cuda", allow_software_fallback=False)`; frames arrive as `nv12` in system memory |
| `+pts` | an FFmpeg row with `showinfo` first in the chain (`decode_command(showinfo=True)`, log level `info`). Standard error is drained into memory by a thread and parsed after the run with `clip.SHOWINFO_PATTERN` |

**PyAV's conversion: one documented flag change.** PyAV applies the matrix and range
(`sws_setColorspaceDetails`) only when the source and destination colourspaces or ranges differ
(`av/video/reformatter.pyx`, `_reformat`). With `src_colorspace="itu709", dst_colorspace="itu709"`
it keeps swscale's defaults. Across 5 frames that left 117,178,039 samples different, max 20.
For an RGB destination swscale does not use the destination matrix, so the instrument names a
different one (`itu601`). That is the one documented change, and the bytes then match row a on
every frame. `interpolation` takes swscale's integer flags, so `SWS_ACCURATE_RND` (0x40000)
mirrors `flags=accurate_rnd`.

**Timing.**
- **The bracket** opens just before the FFmpeg process is spawned, or before `av.open`. It
  closes when the last frame is whole in its C-contiguous `uint8` `(2160, 3840, 3)` array in
  this process. Shape, dtype and contiguity are checked on every frame. s/frame = bracket / 681.
- **Each frame's interval** runs from the end of the previous frame's handling to its arrival.
- **The witness** is a SHA-256 of every 30th frame and the last: 24 frames, compared with row a's
  reference hash. It is left out of the bracket, so the bracket is the sum of the intervals.
  For pipe rows FFmpeg blocks on the full pipe while a frame is hashed. For PyAV rows the
  decoder threads may run ahead during a hash: at most 24 x ~15 ms, under 0.6 ms/frame.
- **Pipe rows yield one reused buffer.** PyAV's `to_ndarray()` returns a fresh C-contiguous array
  that views PyAV's frame buffer.
- **The per-frame maximum** in every row is the first frame: FFmpeg or PyAV start-up,
  115-356 ms.

**Identity** (`identity` command, untimed, outside the windows).
- `reference.json` holds ffprobe's per-frame pts (`-show_entries frame=pts`; equal to the packet
  pts list) and row a's 681 per-frame SHA-256 hashes.
- `identity-<row>.json` hashes every frame of a row, compares frame count, hashes and pts with
  the reference, and records the AVIO write statistics at log level `verbose`.
- A row whose bytes differ is re-decoded in lockstep with row a (`lockstep_difference`).

**Windows** (`window` command, plan 4.3, owner's best-effort ruling).
- Before each window: Part B's advisory idle gate (`work/wp2.1s/idle_gate.ps1`, md5
  `cf3a33c0ab7da54bf7a8a4386f632e90`, identical to `work/wp1.2b/gate/idle_gate.ps1`).
- An opening and a closing probe: row a on its first 120 frames.
- A 10 s psutil stray check (`bench.stray_processes`) between consecutive steps. The check after
  one run is the check before the next; nothing runs between them.
- Ambient at start and end: head and changed files, local time, power scheme and overlay, AC and
  battery (`bench._windows_power`, `psutil`). The card's state (`bench._gpu_state`, P-state and SM
  clock) at the start and end of the window and of every run.
- No sampler uses CIM or WMI.
- **Contamination rule:** the closing probe drifts more than 10 % from the opening one, or a stray
  check lists a process outside `SYSTEM_PROCESSES` (the Windows processes listed in the
  instrument) at 25 % or more of one logical CPU.
- Rows were run in blocks (three runs of one row, then the next), not interleaved.

## 3. Row a against Part B (the discrepancy)

| | Part B (transport record 2026-10-19 03:25) | This spike (clean windows, 2026-10-20) |
|---|---|---|
| Through the pipe into Python | 93.6 ms/frame | 55.9 ms/frame (row a, W2: 55.20 / 55.87 / 55.98); a+pts 55.7 (W3); knob variants 54.7-54.9 (W1) |
| Reads | 517,560, none over 32,768 bytes | 517,560, none over 32,768 bytes (identical) |
| Decode + conversion, no pipe | 16.2 ms/frame to NUL | 13.45 ms/frame to the null muxer (13.24-13.93, W2) |
| Stray checks | WmiPrvSE 60-73 %; after, vmmemWSL 85 % | no non-system process at 25 % or more in any window |

Contention, measured (`work/wp2.1s/attribution.py`, record `transport/attribution.json`;
row a, 120 frames, outside the windows; the busy loops are this script's own child processes):

| Busy loops (one logical CPU each) | 0 | 2 | 4 | 0 again |
|---|---|---|---|---|
| s/frame | 0.0571 | 0.0623 (+9 %) | 0.0653 (+14 %) | 0.0574 |

CPU contention slows the 32 KB pipe and explains part of the gap. **The remainder is
UNEXPLAINED.** The null-muxer calibration is 17 % faster than Part B's NUL figure; row a is 40 %
faster.

**Consequence for the gate report.** Part B's "decode-only 0.089-0.094 s/frame, pipe-bound" and
its -20 to -30 % analysis estimate (candidate #6) rest on the contaminated 93.6 ms figure. The
projection rows of section 5 replace that estimate. CHARC adds the dated supersession note to the
gate report on accept; this report does not edit it.

## 4. Claim 1 -- transport, decode to NumPy (GX011627, 681 frames, 3840x2160 `rgb24`)

Rows of record from the planned windows. "Per frame" is the run of record's (the median run's)
min / median / max interval. The max is the first frame's start-up.

| Row | s/frame median (min-max), 3 runs | Per frame min / median / max (ms) | Same work | Reads observed (FFmpeg writes) | pts exact (side channel; cost) | WP1.5 section 8 muxer options | Window |
|---|---|---|---|---|---|---|---|
| a | 0.05587 (0.05520-0.05598) | 47.2 / 55.3 / 336.3 | SAME (681/681 hashes) | 517,560 reads, all <= 32,768 B (writes 32,741 B mean) | 681/681 via a+pts | encode side unchanged: decode-only, encode stays one FFmpeg process | W2 |
| a+pts | 0.05567 (0.05525-0.05656) | 47.3 / 54.7 / 355.8 | SAME | as a | 681/681, showinfo on stderr; cost -0.2 ms (noise) | unchanged | W3 |
| b | 0.01611 (0.01598-0.01646) | 3.4 / 15.7 / 281.1 | SAME | 89,593 reads, median 131,072 B, largest 24,883,200 B (a whole frame); 4.3 % of bytes in reads >= 1 MiB (writes 32,741 B mean) | 681/681 via b+pts | unchanged | W4 |
| b+pts | 0.01706 (0.01700-0.01721) | 3.3 / 16.4 / 276.2 | SAME | 88,205 reads, median 131,072 B, largest 24,883,200 B | 681/681, showinfo; cost +0.95 ms | unchanged | W4 |
| b-cuda | 0.01299 (0.01296-0.01357) | 3.3 / 13.0 / 234.8 | SAME | 86,376 reads, median 98,304 B, largest 24,883,200 B | 681/681 via b-cuda+pts | unchanged | W4 |
| b-cuda+pts | 0.01364 (0.01348-0.01364) | 3.2 / 13.6 / 245.5 | SAME | 91,140 reads, median 98,304 B | 681/681, showinfo; cost +0.65 ms | unchanged | W4 |
| s | 0.02430 (0.02416-0.02445) | 4.9 / 24.0 / 295.2 | SAME | 164,923 reads, median 65,536 B, largest 24,883,200 B (writes 32,741 B mean) | 681/681 via s+pts | unchanged | W5 |
| s+pts | 0.02507 (0.02470-0.02588) | 5.6 / 24.8 / 328.8 | SAME | 170,048 reads, median 65,536 B | 681/681, showinfo; cost +0.77 ms | unchanged | W5 |
| c (PyAV, default SLICE) | 0.07597 (0.07497-0.07625) | 45.3 / 77.7 / 207.4 | SAME | in-process (no transport) | 681/681, decoder `frame.pts`; no extra cost (an attribute read) | unchanged: PyAV decode, FFmpeg-process encode | W5 |
| c-auto | 0.04297 (0.04223-0.04355) | 29.6 / 43.3 / 204.1 | SAME | in-process | 681/681, `frame.pts` | unchanged | W6 |
| c-cuda | 0.04773 (0.04740-0.04828) | 34.4 / 49.0 / 114.7 | SAME | in-process (`nv12` frames downloaded) | 681/681, `frame.pts` | unchanged | W6 |
| c-cuda-auto | 0.04242 (0.04221-0.04264) | 29.3 / 43.2 / 213.3 | SAME | in-process | 681/681, `frame.pts` | unchanged | W6 |
| n (calibration) | 0.01345 (0.01324-0.01393) | -- | no frames reach Python | -- | -- | -- | W2 |

- **No row FAILS IF-1.** Every FFmpeg row delivers exact pts through `showinfo`, and
  `-copyts` is not needed: GX011627 starts at pts 0. For a clip with a non-zero start time
  (out of envelope) `-copyts` would apply. Every PyAV row delivers `frame.pts` exactly. The
  showinfo frame numbers ran 0..680 without a gap.
- **Witness in the timed runs:** 24 frames per run matched the reference in every run of every
  row. The full per-frame identity is in `identity-<row>.json`.
- **Block sizes, row b.** The brief asks for "1 MB+ blocks". What is observed is FFmpeg still
  writing 32 KB, with the large pipe buffer letting it run ahead. Reads coalesce to a median of
  128 KB and up to a whole frame, but only 4-6 % of bytes arrive in reads of 1 MiB or more. The
  speed comes from decoupling, not from large writes.
- **Exploration (W1, one run each):** a-direct 54.71, a-blocksize 54.88, a-direct-blocksize
  54.69, b-1m 16.54, b 17.22, b-direct-blocksize 17.45 ms/frame. Every one has 32,741-byte
  writes (identity records). A 1 MiB pipe buffer is enough. Row a already reads with `readinto`
  into a preallocated frame buffer, so "readinto alone" is row a.
- **PyAV is not decode-bound.** c-cuda-auto runs no faster than c-auto. That is consistent with
  the per-frame `reformat` in this process being the limit. INFERENCE: the conversion was not
  timed separately.
- **c-cuda:** the wheel's FFmpeg build carries CUDA (`hwdevices_available()`: cuda, dxva2, qsv,
  d3d11va, d3d12va, amf). Its decoders include `hevc` and `hevc_cuvid`.

**AD-10 swscale flags (untimed evidence).** Row a-ad10 is row a with
`flags=accurate_rnd+full_chroma_int+bitexact` (AD-10's set) in place of `flags=accurate_rnd`.
Between the two sets, over the whole clip (`identity-a-ad10.json`, lockstep against row a): max
absolute difference 19, mean absolute difference 0.50 per sample (681 of 681 frames differ, 44.4 %
of samples). Per CHARC `871d4f17e78c10b3` the difference is expected: AD-10's set is the
product's set.

## 5. Analysis-pass PROJECTION

PROJECTION = a row's decode-to-NumPy (median) + Part B's measured per-frame work: proxy plus
staged statistics, **0.050 s/frame (W3b, contaminated)**. That work figure may be inflated in the
same way as Part B's pipe figure. Part B's analysis loop reads in a thread (`clip._Reader`), so
decode can overlap the work. The sum is the serial bound and the max is the overlapped bound.
Minutes per minute = s/frame x 29.97.

| Row | Decode (s/frame) | PROJECTION serial: s/frame (min/min) | PROJECTION overlapped: s/frame (min/min) |
|---|---|---|---|
| a | 0.0559 | 0.1059 (3.17) | 0.0559 (1.67) |
| a+pts | 0.0557 | 0.1057 (3.17) | 0.0557 (1.67) |
| b | 0.0161 | 0.0661 (1.98) | 0.0500 (1.50) |
| b+pts | 0.0171 | 0.0671 (2.01) | 0.0500 (1.50) |
| b-cuda | 0.0130 | 0.0630 (1.89) | 0.0500 (1.50) |
| b-cuda+pts | 0.0136 | 0.0636 (1.91) | 0.0500 (1.50) |
| s | 0.0243 | 0.0743 (2.23) | 0.0500 (1.50) |
| s+pts | 0.0251 | 0.0751 (2.25) | 0.0500 (1.50) |
| c | 0.0760 | 0.1260 (3.78) | 0.0760 (2.28) |
| c-auto | 0.0430 | 0.0930 (2.79) | 0.0500 (1.50) |
| c-cuda | 0.0477 | 0.0977 (2.93) | 0.0500 (1.50) |
| c-cuda-auto | 0.0424 | 0.0924 (2.77) | 0.0500 (1.50) |

- **Part B's measured analysis:** 0.0707 s/frame on GX011627, today's pipe, software decode
  (2.12 min/min). On GX011625 it was 0.1190 / 0.1101. The GX011627 figure lies between this
  spike's two bounds for row a (0.0559 overlapped, 0.1059 serial).
- **Overlap is shared CPU, not free.** PyAV's decode and conversion run in the same process as
  the work, and FFmpeg's in a child process. Both compete with the work for CPU.
- **Export:** the core dominates (Part B section 10, #6), so the transport changes the export by
  at most its decode share. No export projection is made.

## 6. Portability (N1) and AD-2 evidence

- **The 32 MiB pipe buffer is a Windows platform tuning** (acceptable under N1 on two conditions,
  CHARC `871d4f17e78c10b3`; AD-23 on accept). It uses `_winapi.CreatePipe(None, nSize)`, a
  private CPython module, plus `msvcrt.open_osfhandle`. CPython's `subprocess.PIPE` passes 0,
  the system default.
  - **(a) Automatic portable fallback, demonstrated.** When the large pipe cannot be created
    (`_big_pipe` raises `OSError`), `Transport._ffmpeg_frames` falls back to CPython's default
    pipe and records why (`pipe_fallback`). Row b-fallback+pts forces that failure. Its
    identity run (`identity-b-fallback+pts.json`): `pipe_fallback` = "OSError: large pipe
    creation forced to fail", reads at most 32,768 bytes (the default pipe), 681/681 frame
    hashes equal to row a's, 681/681 pts exact against ffprobe. The fallback's speed is row a's
    transport: a+pts 55.7 ms/frame (W3). PyAV is the other portable path (same bytes, exact pts,
    42.4-76.0 ms/frame).
  - **(b) One named constant.** `BIG_PIPE_BYTES` (`tools/spike_io/transport.py`), with its
    measurement in its docstring: 16.11 ms/frame (W4) against 55.87 ms on the default pipe
    (W2); 1 MiB gave 16.54 ms (W1, one run; the exploration row's own constant
    `EXPLORE_PIPE_BYTES`).
- **Portable equivalent:** on Linux, `fcntl(F_SETPIPE_SZ)`, capped for unprivileged processes by
  `/proc/sys/fs/pipe-max-size` (1 MiB by default). The instrument does this off Windows, untested
  here. Its speed is UNKNOWN (out of envelope). macOS has no pipe-size control: UNKNOWN.
- **Do the portable transports reach the same speed?** Not on this machine:

  | Transport | Decode (ms/frame) | Against b's 16.1 ms |
  |---|---|---|
  | TCP socket (portable API) | 24.3 | +51 % |
  | PyAV, best form (portable wheel) | 42.4 | +163 % |

  In the overlapped projection, b, s and c-auto all reach the 0.050 s/frame work bound.
- **Other Windows-only elements of the instrument:** the idle gate (PowerShell) and the power-plan
  reading (`bench._windows_power`).
- **AD-2 evidence:**
  - Every candidate delivers the same bytes and exact pts.
  - The fastest is the FFmpeg-process pipe with a large buffer: 16.1 ms software, 13.0 ms
    `-hwaccel cuda`, against 55.9 ms today. It is Windows-specific as built.
  - The TCP socket is portable at 24.3 ms.
  - PyAV in-process is 42-43 ms in its best forms.
  - All are decode-only, so WP1.5 section 8's muxer options stay reachable on the unchanged
    FFmpeg-process encode side.

## 7. Windows and records

| Window | Plan | Local (2026-10-20) | Idle gate median CPU / GPU | Probes open / close (s/frame) | Drift | Verdict |
|---|---|---|---|---|---|---|
| W1 | explore | 00:26-00:31 | 4.4 % / 0 % | 0.0567 / 0.0574 | +1.2 % | clean |
| W2 | pipes-a | 00:32-00:37 | 6.4 % / 0 % | 0.0570 / 0.0594 | +4.1 % | clean |
| W3 | pipes-apts | 00:40-00:44 | 9.4 % / 0 % | 0.0579 / 0.0587 | +1.4 % | clean |
| W4 | pipes-b | 00:45-00:50 | 4.25 % / 0 % | 0.0573 / 0.0577 | +0.7 % | clean |
| W5 | others-s | 00:52-00:59 | 4.4 % / 0 % | 0.0550 / 0.0560 | +1.9 % | clean |
| W6 | others-c | 01:00-01:07 | 5.6 % / 0 % | 0.0539 / 0.0558 | +3.6 % | clean |

- **Conditions in every window:**
  - head clean: W1-W2 `088d7a2`, W3-W6 `427651b`, which differs only by the ledger;
  - power scheme Balanced with overlay Best performance;
  - AC power, battery 79-80 %;
  - card P8 / 210 MHz SM at window start and end (P0-P5 during W4's CUDA rows).
- **Stray checks:** WmiPrvSE reached 56.9 % (W3 start) and System 23 %, both system processes. No
  non-system process reached 25 %. No re-run was needed.
- **Records:** `work/wp2.1s/transport/`:
  - `reference.json`, `identity-<row>.json` (18 rows);
  - `W1.json`-`W6.json` (every run's intervals and ambient);
  - `summary.json`, `attribution.json`;
  - `gate.jsonl`, plus logs in `work/wp2.1s/logs/`.
- **Machine time for the transport leg:** about 60 min of the 2 h cap: about 20 min untimed
  (exploration, reference, identity; 3.5 min of it for the fallback and AD-10 mean re-runs after
  the CHARC rulings), 39 min in windows (six windows, with their idle gates) and 1 min for
  attribution.

## 8. Claim 2 -- photo I/O

PENDING.

## 9. Claim 3 -- licence positions

PENDING.
