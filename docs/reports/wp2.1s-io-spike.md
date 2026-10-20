# WP2.1S -- transport and photo I/O spike

Evidence for WP2.1 (plan section 8.3): it closes AD-2 (frame transport) and AD-17 (16-bit PNG +
ICC + EXIF), and confirms or corrects AD-18 (licences). Brief `docs/briefs/wp2.1s-brief.md`
(FINAL, `aa1f5f0`). Instruments `tools/spike_io/transport.py` (claim 1), `tools/spike_io/photo.py`
(claim 2) and `tools/spike_io/licences.py` (claim 3). Every record is under
`C:\Users\rwsmy\clearwater\work\wp2.1s\` (not committed). The footage folder was input only.

**Status of this text:** claims 1, 2 and 3 are complete.

## 1. Results at a glance

- **Every row is the SAME WORK.** All 23 transport forms decode the same 681 frames to the same
  bytes as row a: per-frame SHA-256 over the whole clip. The one exception is a-ad10, AD-10's
  flag set, which is a bytes finding by design. Every pts side channel delivers 681/681 pts
  exactly as ffprobe lists them. That includes the five exploration knob forms, each checked
  through its own `+pts` identity row.
- **The 32 KB writes are fixed in FFmpeg; the cure is on the reading side.** FFmpeg's own AVIO
  statistics show 32,741-byte writes on average whatever the knob: `-avioflags direct`, the pipe
  protocol's `-blocksize`, or both. That is 517,560 writes for the clip. What removes the
  bottleneck is the pipe's buffer. A 32 MiB anonymous pipe takes the decode from 55.9 to 16.1
  ms/frame, which is about FFmpeg's own decode-plus-conversion speed (13.5 ms to the null muxer).
  This buffer is a Windows platform tuning with an automatic, byte-identical fallback to the
  default pipe (section 6).
- **Best rows (median s/frame, clean windows).** The bracket leaves the witness hashes out while
  the producer keeps working, so it is a lower bound. The wall time including the hashes is an
  upper bound (section 2):

  | Row | ms/frame (bracket) | Upper bound (wall with hashes) |
  |---|---|---|
  | b-cuda (32 MiB pipe, `-hwaccel cuda`) | 13.0 | 13.5 |
  | b (32 MiB pipe) | 16.1 | 16.7 |
  | s (loopback TCP socket) | 24.3 | 24.8 |
  | c-cuda-auto (PyAV, CUDA decode) | 42.4 | 42.8 |
  | c-auto (PyAV, `thread_type="AUTO"`) | 43.0 | 43.3 |
  | a (today's pipe) | 55.9 | 56.3 |
  | c (PyAV default threading) | 76.0 | 76.3 |

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
- **Photo (claim 2, synthetic only; section 8).**
  - Pillow 12.3.0 cannot write a 16-bit RGB PNG: it writes 8 bits. The stdlib writer
    (zlib + struct, EXIF built by Pillow's `Image.Exif`) does. PyAV re-reads every 16-bit sample
    exactly; Pillow re-reads the `iCCP` and `eXIf` bytes identical. Pillow writes the 8-bit PNG
    with ICC and EXIF correctly.
  - HEIC: pillow-heif returns the ICC profile byte-identical and every EXIF field written. libheif
    applies the container's `irot`, never EXIF. `open_heif` hands over the file's Orientation tag
    unchanged, so honouring it rotates twice. The Pillow opener resets the tag to 1, which loses
    the rotation of a file that has the tag but no `irot`. PROVISIONAL until an owner photo is
    read.
  - PyAV 16.1.0 crashes the process when a PNG frame's ICC side data has been touched and the
    frame is freed.
- **Licences (claim 3; section 9).** PyAV's bundled FFmpeg 8.0.1 reports "LGPL version 3 or later"
  and is configured without `--enable-gpl`, yet bundles libx264 and libx265, and both work as
  encoders from PyAV, as does NVENC (section 9.1). No file in the wheel mentions LGPL or GPL.
  The gyan FFmpeg CLI is GPL version 3 or later, not 2 (CORRECTS AD-18). NumPy's expression is wider than BSD-3
  (CORRECTS AD-18). Pillow, pillow-heif and its bundled libraries, and CuPy CONFIRM AD-18.

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
- **The bracket** opens just before the FFmpeg process is spawned, or before `av.open`. So it
  includes process start-up or container opening: this report reads the brief's "first byte
  requested" as the request that starts the decoder. The bracket closes when the last frame is
  whole in its C-contiguous `uint8` `(2160, 3840, 3)` array in this process. Shape, dtype and contiguity are checked on every frame. s/frame = bracket / 681.
- **Each frame's interval** runs from the end of the previous frame's handling to its arrival.
- **The witness** is a SHA-256 of every 30th frame and the last: 24 frames, compared with row a's
  reference hash. It is left out of the bracket, so the bracket is the sum of the intervals.
- **The producer does not stop during a hash.**
  - FFmpeg keeps writing into the pipe or socket buffer. The 32 MiB pipe holds more than one
    24,883,200-byte frame.
  - PyAV's decoder threads keep decoding.
  - Work done during a hash therefore falls outside the bracket. The bracket is a LOWER bound
    on the decode-to-NumPy time without hashing.
  - `wall_s_with_witness` is an UPPER bound. It is the wall time from the bracket's start to the
    last frame's arrival. It includes 23 of the 24 witness hashes: the last frame is hashed
    after it arrives, and that hash affects no arrival.
  - The two differ by 0.35-0.58 ms/frame, about the hashing time (`summary.json`,
    `wall_with_witness_s_per_frame`). Medians, bracket to upper bound, in ms/frame:

    | Row | Bracket | Upper bound |
    |---|---|---|
    | b | 16.11 | 16.69 |
    | b+pts | 17.06 | 17.62 |
    | b-cuda | 12.99 | 13.48 |
    | b-cuda+pts | 13.64 | 14.15 |
    | s | 24.30 | 24.81 |
    | s+pts | 25.07 | 25.57 |
    | a | 55.87 | 56.30 |
    | a+pts | 55.67 | 56.07 |
    | c | 75.97 | 76.32 |
    | c-auto | 42.97 | 43.34 |
    | c-cuda | 47.73 | 48.09 |
    | c-cuda-auto | 42.42 | 42.78 |

  - The side-channel costs below compare brackets, so both sides carry the same bias.
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
  `-copyts` is not needed: GX011627 starts at pts 0.
  - The five exploration knob forms (a-direct, a-blocksize, a-direct-blocksize, b-1m,
    b-direct-blocksize) were checked by untimed `+pts` identity rows
    (`identity-<form>+pts.json`, 2026-10-20 01:51-01:54). Each gave the same 681 hashes and
    681/681 pts exact.
  - a-ad10 is an untimed bytes finding. Its pts were not checked. For a clip with a non-zero start time
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
- **The witness bias:** with the upper bounds of section 2, each serial PROJECTION rises by
  0.35-0.58 ms/frame (b+pts 0.0676, b-cuda+pts 0.0641). The overlapped bounds of the
  large-buffer rows stay at the 0.050 s/frame work figure.
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
  here.
  - If `F_SETPIPE_SZ` fails (for example a 32 MiB request above the unprivileged maximum), the
    pipe is closed and the transport falls back to the default pipe, recording why.
  - Its speed is UNKNOWN (out of envelope). macOS has no pipe-size control: UNKNOWN.
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
  - The timed figures are brackets, which are lower bounds. Each upper bound is 0.35-0.58
    ms/frame higher (section 2).
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
  - `reference.json`, `identity-<row>.json` (23 rows; the five knob `+pts` rows were added
    after the windows, untimed);
  - `W1.json`-`W6.json` (every run's intervals and ambient);
  - `summary.json`, `attribution.json`;
  - `gate.jsonl`, plus logs in `work/wp2.1s/logs/`.
- **Machine time for the transport leg:** about 60 min of the 2 h cap: about 20 min untimed
  (exploration, reference, identity; 3.5 min of it for the fallback and AD-10 mean re-runs after
  the CHARC rulings), 39 min in windows (six windows, with their idle gates) and 1 min for
  attribution.

## 8. Claim 2 -- photo I/O

Instrument `tools/spike_io/photo.py`, run `uv run python tools/spike_io/photo.py run`. Record
`work/wp2.1s/photo/photo.json`, with the fixtures beside it. Tests `tests/test_spike_io_photo.py`
(40 cases). Every image is synthetic. No owner photo exists and none was downloaded.

- **Libraries, as installed:**
  - Pillow 12.3.0;
  - pillow-heif 1.8.1, with libheif 1.23.6. Its HEIC encoder is x265 4.3+1 and its decoder is
    libde265 1.1.3;
  - PyAV 16.1.0, bundling FFmpeg 8.0.1.
- **The profile** (`display_p3_profile`) is built in code. It is an ICC v4.3 matrix/TRC display
  profile, 664 bytes: Display P3 primaries, the sRGB tone curve as a `para` curve, and Bradford
  D65-to-D50 adaptation recorded in `chad`. It opens in `ImageCms` (LittleCMS) with its
  description. The test undoes the `chad` matrix as LittleCMS reads it and recovers the P3
  primaries to within 0.001. No profile file is committed.
- **The fixture image** is 64 x 48, with ramps that tell all eight orientations apart. A HEIC
  decode is lossy (quality 95), so its pose is the closest of three candidates, within a mean
  error of 8/255:
  - `upright`: rotated once, which is correct;
  - `stored`: not rotated;
  - `twice`: the rotation applied twice.

### 8.1 HEIC read (pillow-heif)

pillow-heif's own encoder wrote every fixture. Each fixture embeds the profile and an EXIF
block with Make, Model, DateTime, Orientation, DateTimeOriginal, FNumber, the pixel dimensions
and a GPS latitude reference.

There are three layouts:
- **public:** `pillow_heif.encode`. It writes an `irot` from the EXIF Orientation and keeps the
  tag. This is the layout an iPhone writes (INFERENCE: no owner photo has been read).
- **exif-only:** the tag, with no `irot`.
- **irot-only:** `irot`, with the tag set to 1.

The public API cannot write one without the other. exif-only and irot-only use pillow-heif's
PRIVATE `misc.CtxEncode` (`image_orientation`).

Two read paths:
- **raw:** `pillow_heif.open_heif`.
- **plugin:** `Image.open` through pillow-heif's Pillow opener.

"Honour the tag" means a consumer then applies the Orientation it was handed:
`apply_orientation` for raw, `ImageOps.exif_transpose` for the plugin.

| Fixture | `irot` in `ipco` | EXIF tag in file | ICC identical (raw / plugin) | raw pixels | raw, tag honoured | plugin tag / `original_orientation` | plugin, tag honoured |
|---|---|---|---|---|---|---|---|
| 8-bit public, o1 | none | 1 | yes / yes | upright | upright | 1 / None | upright |
| 8-bit public, o6 | 270 (anticlockwise) | 6 | yes / yes | upright | **twice** | 1 / 6 | upright |
| 8-bit public, o8 | 90 | 8 | yes / yes | upright | **twice** | 1 / 8 | upright |
| 8-bit exif-only, o6 | none | 6 | yes / yes | **stored** | upright | 1 / 6 | **stored (rotation lost)** |
| 8-bit irot-only, o6 | 270 | 1 | yes / yes | upright | upright | 1 / None | upright |
| 10-bit public, o1 / o6 / o8 | none / 270 / 90 | 1 / 6 / 8 | yes / yes | upright | upright / **twice** / **twice** | 1 / None, 6, 8 | upright |

- **ICC:** byte-identical on both paths, in every case.
- **EXIF read, every case:** every field written comes back, with its value: IFD0 Make, Model,
  DateTime and Orientation; Exif DateTimeOriginal, FNumber, PixelXDimension and
  PixelYDimension; GPS LatitudeRef.
  - Through `open_heif`, every field and value equals what was written.
  - Through the plugin, the only change is Orientation, reset to 1 where the tag was 6 or 8.
  - Recorded as `exif_fields_raw_equal` and `exif_fields_plugin_mismatch`; tested on all eight
    fixtures.
- **Mechanism:** libheif applies the container's `irot`. It does not apply EXIF: the exif-only
  file comes back unrotated.
- **Is the Orientation tag still there after the read?**
  - `open_heif`: yes, unchanged (6 or 8), on pixels already rotated. Honouring it is the double
    rotation D63 warns of.
  - The Pillow opener: it resets the tag to 1 and keeps the old value in
    `info["original_orientation"]`. Its rule assumes an `irot` always matches the tag. On the
    exif-only file it resets the tag although nothing was rotated, so the rotation is lost.
- **Recommendation for WP2.1 (REASONED, not measured on a real photo):**
  - Take rotation from the container transform as libheif applies it.
  - Never re-apply EXIF Orientation after a HEIC decode.
  - Detect a tag without an `irot` and decide that case explicitly. `heif_transforms` reads
    `irot`/`imir` from `ipco` but does NOT read `ipma`, which assigns properties to items. It is
    valid only for one-item files like these fixtures. A real iPhone HEIC (a grid, thumbnails,
    auxiliary images) needs the primary item's `ipma` entries.
- **Bit depth:**
  - A 10-bit file reports `bit_depth` 10.
  - `open_heif` returns 8-bit `RGB` by default (`convert_hdr_to_8bit=True`).
  - With `convert_hdr_to_8bit=False` it returns `RGB;16` `uint16`, with the 10-bit samples
    shifted left by 6 (maximum 65472 = 1023 << 6).
  - The option is `open_heif`'s `convert_hdr_to_8bit`.
- **PROVISIONAL:** every HEIC verdict stands until an owner iPhone HEIC is read (out of
  envelope).

### 8.2 16-bit and 8-bit PNG write with ICC and EXIF

- **Pillow cannot write a 16-bit RGB PNG** (`pillow_png16_attempt`, test
  `test_pillow_cannot_write_16bit_rgb_png`).
  - `Image.fromarray` on an `(h, w, 3)` `uint16` array raises `TypeError: Cannot handle this
    data type: (1, 1, 3), <u2`.
  - `Image.frombytes(..., "RGB;16B")` gives mode `RGB`. The PNG Pillow saves from it, with the
    profile and EXIF, has `IHDR` bit depth 8.
  - AD-17's Pillow path therefore fails for 16 bits.
- **The ruling-1b alternative works.** `encode_png16` writes `IHDR` (16-bit, colour type 2),
  `iCCP` (profile deflated), `eXIf`, `IDAT` and `IEND` with zlib and struct. The EXIF is
  Pillow's `Image.Exif.tobytes()` without its `Exif\0\0` prefix. No piexif and no pypng.
- **The EXIF written is the D63 set** (`edit_exif`). The source block carries:
  - Orientation 6;
  - an IFD1 with an 8 x 6 JPEG thumbnail, appended by `add_thumbnail`, since Pillow's writer
    cannot write IFD1;
  - pixel dimensions 48 x 64.

  The edited block has Orientation 1, no IFD1, pixel dimensions 64 x 48 and Software
  `Clearwater`. Make, Model, DateTime, DateTimeOriginal, FNumber and GPS LatitudeRef are kept.
  Pillow's EXIF writer drops IFD1 by construction, because it cannot write it.

**Verification by a reader other than the writer:**

| Property | 16-bit PNG (stdlib writer) | Verified by | 8-bit PNG (Pillow writer) | Verified by |
|---|---|---|---|---|
| Samples exact | yes: 0 of 9,216 differ, `rgb48be` | PyAV (FFmpeg's PNG decoder, written separately from the writer) | yes: 0 differ, `rgb24` | PyAV; the test's own stdlib decoder (handles all five PNG filter types) |
| `iCCP` bytes = source profile | yes | Pillow (`info["icc_profile"]`) | yes | stdlib walker `png_chunks`; the test's own walker |
| `eXIf` as written, D63 checks pass | yes / yes | Pillow (`info["exif"]`, `getexif()`) | yes / yes | `png_chunks`; the test's own walker |
| Chunk order | IHDR, iCCP, eXIf, IDAT, IEND | Pillow's `PngStream` | IHDR, iCCP, eXIf, IDAT, IEND | `png_chunks`; the test's own walker |
| Pillow's own read of the samples | 8-bit `RGB`: truncated (top-right 255, 0, 51) | Pillow | -- | -- |

- **Chunk placement:** `iCCP` comes before `IDAT` in both files. `eXIf` also comes before
  `IDAT` in both: the stdlib writer puts it there, and Pillow writes it there itself. Pillow's
  reader finds the `eXIf` in both.
- **Planted defects fail by name** (`failures` / `exif_problems`):
  - a wrong ICC byte gives `["iccp_identical_pillow"]` on the 16-bit file and
    `["iccp_identical_stdlib"]` on the 8-bit file;
  - 16-bit samples truncated to 8 bits give `["values_exact_pyav"]`;
  - a stale Orientation gives `["Orientation"]`;
  - unedited source EXIF gives `Orientation, IFD1, PixelXDimension, PixelYDimension, Software`.
- **PyAV defect (found here; matters if WP2.1 adopts PyAV).**
  - With PyAV 16.1.0, touching `frame.side_data` on a PNG frame that carries an ICC profile
    makes the process crash when the frame is freed. Even `len(frame.side_data)` does it. The
    crash is an access violation, exit 139.
  - Reproduction: `av.open(<png>, format="png_pipe")`, take the first frame, call
    `len(frame.side_data)`, then `del frame; gc.collect()`.
  - It happens on both written PNGs.
  - A synthetic H.264 MP4's DISPLAYMATRIX and SEI side data read and free cleanly (exit 0).
  - So `pyav_png` reads samples only, and ICC is verified by Pillow and the stdlib walkers.
- **exiftool is absent** (`which exiftool`: none on PATH, 2026-10-20). It was not installed
  (ruling 2).
- **N1:** the photo leg is pure Python on the installed wheels and has no Windows-only element.
  The PyAV crash was seen on Windows; other systems are UNKNOWN.

**AD-17 evidence:**
- Pillow writes 8-bit PNG with ICC and EXIF, but cannot write 16-bit RGB PNG.
- The stdlib zlib + struct writer with Pillow-built EXIF writes 16-bit RGB with `iCCP` and the
  D63 `eXIf`. PyAV confirmed the samples exact, and Pillow confirmed the ICC, EXIF and order.
- Pillow's EXIF writer covers the D63 subset, so piexif is not needed.
- pillow-heif reads HEIC ICC and EXIF intact. Its two read paths treat orientation
  differently, as above.

## 9. Claim 3 -- licence positions

Read by `tools/spike_io/licences.py` (record `work/wp2.1s/licences.json`) from:
- the installed distributions' metadata, and the names of their `.dist-info` licence files
  (listed, not read; `LICENSES_bundled.txt` is the one licence file read);
- pillow-heif's `LICENSES_bundled.txt`;
- PyAV's `av._core.library_meta`, `av.codecs_available` and `hwdevices_available()`;
- the DLLs in `av.libs`;
- `ffmpeg -version` and `ffmpeg -L`.

The "GPL-2.0-or-later compatibility" column is REASONED from those strings. It is evidence for
WP2.1, to be confirmed at WP5.5, and not legal advice. It assumes the FSF's reading:
- LGPL-3.0 and GPL-3.0 code may be combined with Clearwater's GPL-2.0-or-later code only when
  the combination is conveyed under GPL-3.0;
- "or later" permits that.

| Name | Version | License (as read) | GPL-2.0-or-later compatibility | One-line reason | AD-18 |
|---|---|---|---|---|---|
| PyAV | 16.1.0 | BSD-3-Clause (`License-Expression`) | yes | permissive | NEW |
| FFmpeg bundled in the PyAV wheel | 8.0.1 | every library reports "LGPL version 3 or later"; configuration has `--enable-version3`, NO `--enable-gpl`, NO `--enable-nonfree`; `--enable-libx264 --enable-libx265`, with `libx264-165` and `libx265` DLLs in `av.libs`, and PyAV opens and uses both encoders (section 9.1); every non-code file in the wheel was read: none mentions LGPL or GPL (PyAV's `LICENSE.txt` is BSD-3-Clause) | LGPL-3 libraries: yes (CHARC); the x264/x265 inside: UNKNOWN | the libraries report LGPL-3, yet x264 and x265 are compiled in and usable; the C-string scan finds no licence string in their DLLs, so their licence cannot be read from the artefact, and neither can the licence of the build as a whole | NEW |
| Its codecs and devices | 8.0.1 | `hevc`, `h264` decoders; `hevc_nvenc`, `h264_nvenc` (open and encode, section 9.1); `hevc_cuvid`, `h264_cuvid` decoders; `--enable-nvenc --enable-nvdec`; hwdevices cuda, dxva2, qsv, d3d11va, d3d12va, amf | UNKNOWN | the NVENC/NVDEC headers' licence (AD-18: MIT) is not readable from this artefact | NEW |
| pillow-heif | 1.8.1 | source BSD-3-Clause; `LICENSES_bundled.txt`: "License for pillow-heif binary wheels: GPLv2, due to base library licenses" | UNKNOWN | the binary wheel bundles LGPLv3 libheif and libde265 with x265, and its "GPLv2" may or may not mean "or later" (row below) | CONFIRMED (BSD-3 source); the wheel-level GPLv2 is NEW |
| libheif (in pillow-heif) | 1.23.6 | LGPLv3 (`LICENSES_bundled.txt`) | yes-if | LGPL-3: conveyed under GPL-3.0 | CONFIRMED |
| libde265 (in pillow-heif) | 1.1.3 | LGPLv3 | yes-if | as libheif | CONFIRMED |
| x265 (in pillow-heif) | 4.3+1 | GPLv2 ("or later" not stated in the file) | UNKNOWN | if GPL-2.0-only, it cannot be combined with LGPL-3 libheif under GPL-3.0; the file does not say which | CONFIRMED (as "GPL-2") |
| MinGW-w64 runtime (listed by pillow-heif for Windows wheels) | -- | GPL-3.0-with-GCC-exception (libgcc, libstdc++), MIT and BSD (libwinpthread); no separate runtime DLL is in this wheel | yes | the runtime exception covers linking | NEW |
| Pillow | 12.3.0 | MIT-CMU | yes | permissive | CONFIRMED |
| NumPy | 2.5.4 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | yes | all permissive | CORRECTED (AD-18: BSD-3) |
| SciPy | 1.18.1 | BSD 3-clause text in `License`; classifier "BSD License" | yes | permissive | CONFIRMED |
| CuPy (`cupy-cuda12x`) | 14.2.0 | MIT | yes | permissive; the CUDA runtime files in `[ctk]` were not read here (UNKNOWN; AD-18's EULA rule is untouched) | CONFIRMED |
| FFmpeg CLI (gyan 9.0.2 full) | 9.0.2 | `--enable-gpl --enable-version3`, no `--enable-nonfree`; libx264 and libx265 enabled; `ffmpeg -L`: "GNU General Public License ... either version 3 of the License, or (at your option) any later version" | yes-if | GPL-3.0-or-later: conveyed under GPL-3.0 (or run as a separate program the user installs) | CORRECTED (AD-18: GPL-2.0-or-later) |

- **PyAV's bundled FFmpeg (ruling 1a), stated as read.**
  - libavutil reports "LGPL version 3 or later", and the configuration carries no `--enable-gpl`.
  - Yet libx264 and libx265 are configured in and bundled as DLLs.
  - The build is not `nonfree`. It carries `hevc`, `h264`, `hevc_nvenc`, `h264_nvenc` and the
    `cuda` hwaccel.
  - If PyAV ships, this build ships. It brings x264 and x265. No file in the wheel mentions LGPL
    or GPL, and the C-string scan finds no licence string in their DLLs (section 9.1).
- **pillow-heif's wheel holds one native file, `libheif-*.dll`.** `LICENSES_bundled.txt` names
  separate `libde265`, `libx265` and MinGW runtime files that this Windows wheel does not have. INFERENCE: they
  are linked into the libheif DLL.

### 9.1 PyAV's bundled FFmpeg: encoders, the configuration and the licence strings

Asked by CHARC for AD-18 and AD-2. Everything here is read from the installed wheel or measured
with it (`licences.py`, record `work/wp2.1s/licences.json`). The licence is not adjudicated
beyond what the artefacts show.

- **The configuration string, exactly as `av._core.library_meta` reports it.** It is identical
  for all seven libraries:

  ```
  --disable-static --enable-shared --libdir=/c/cibw/vendor/lib --prefix=/c/cibw/vendor --disable-programs --disable-doc --disable-libxml2 --disable-lzma --disable-libtheora --disable-libfreetype --disable-libfontconfig --disable-libbluray --disable-libopenjpeg --enable-mediafoundation --enable-version3 --disable-alsa --disable-gnutls --enable-libaom --enable-libdav1d --enable-libmp3lame --enable-libopencore-amrnb --enable-libopencore-amrwb --enable-libopus --enable-libspeex --enable-libsvtav1 --enable-libvorbis --enable-libvpx --enable-libwebp --enable-libopenh264 --disable-libxcb --enable-zlib --enable-libx264 --enable-libx265 --enable-nvenc --enable-nvdec --enable-amf --enable-libvpl --disable-encoder='avui,dca,mlp,opus,s302m,sonic,sonic_ls,truehd,vorbis' --disable-decoder=sonic --disable-libjack --disable-indev=jack
  ```

- **The licence call** (`library_meta[...]["license"]`) returns "LGPL version 3 or later" for
  libavutil, libavcodec, libavformat, libavdevice, libavfilter, libswscale and libswresample.
- **`av.library_versions`:** libavutil 60.8.100, libavcodec 62.11.100, libavformat 62.3.100,
  libavdevice 62.1.100, libavfilter 11.4.100, libswscale 9.1.100, libswresample 6.1.100. FFmpeg
  is 8.0.1 (`av.ffmpeg_version_info`).
- **NVENC and NVDEC (CHARC's question a): present and usable.**
  - `hevc_nvenc` and `h264_nvenc` open (`av.codec.Codec(name, "w")`). Each encoded 5 synthetic
    256 x 192 frames to memory: 5 packets, 364 and 481 bytes.
  - At 64 x 48 both refused with `avcodec_open2` EINVAL, below NVENC's minimum size.
  - The `hevc_cuvid` and `h264_cuvid` decoders open, and the `cuda` hwaccel is listed.
  - Rows c-cuda and c-cuda-auto decoded the whole clip through it (section 4).
- **libx264 and libx265 (CHARC's question b): present and usable as encoders from PyAV.**
  - Both open for writing, and each encoded 5 synthetic 256 x 192 frames to memory: 5 packets,
    1,212 and 2,575 bytes.
  - Each encoder wrote its own identification into the bitstream:
    - x264: "x264 - core 165 - H.264/MPEG-4 AVC codec - Copyleft 2003-2025 -
      http://www.videolan.org/x264.html";
    - x265: "x265 (build 215) - 4.1+1-1d117be:[Windows][GCC 15.2.0][64 bit]
      8bit+10bit+12bit - H.265/HEVC codec - Copyright 2013-2018 (c) Multicoreware, Inc".
  - This x265 is 4.1+1. pillow-heif's is 4.3+1, a separate copy.
- **The bundled DLLs.** `av.libs` holds 31 DLLs and nothing else:
  - FFmpeg's avcodec, avdevice, avfilter, avformat, avutil, swresample and swscale;
  - libx264-165 and libx265;
  - libaom, libdav1d, libSvtAv1Enc, libvpx, libwebp, libwebpmux, libsharpyuv, libopenh264,
    libmp3lame, libopus, libvorbis, libvorbisenc, libogg, libspeex, libopencore-amrnb,
    libopencore-amrwb, libvpl, libiconv and zlib1;
  - the MinGW runtime: libgcc_s_seh-1, libstdc++-6 and libwinpthread-1.
- **Where the DLLs came from:** the wheel's `DELVEWHEEL` file says delvewheel 1.11.2 repaired
  the wheel with `--add-path C:\cibw\vendor\bin`, the configure `--prefix` above.
- **Licence files and texts in the wheel.** Every non-code file the wheel installed was read
  (`wheel_text_files`): the `.dist-info` files (`METADATA`, `RECORD`, `WHEEL`, `DELVEWHEEL`,
  `INSTALLER`, `REQUESTED`, `entry_points.txt`, `top_level.txt`), `licenses/LICENSE.txt`,
  `licenses/AUTHORS.rst` and `av/py.typed`.
  - `LICENSE.txt` is PyAV's BSD-3-Clause text.
  - `AUTHORS.rst` lists contributors.
  - No file contains "LGPL", "GPL" or "General Public License".
  - "FFmpeg" appears only in `METADATA`'s description of PyAV, twice. "x264" and "x265" appear
    only in `RECORD`, as the DLL file names.
  - So no file in the wheel states a licence for FFmpeg or for any of the 31 DLLs.
- **Licence strings inside the DLLs.** The scan looks for "GPL", "General Public License" or
  "Copyleft" inside a NUL-terminated printable ASCII string of up to about 240 characters.
  - It finds "libavcodec license: LGPL version 3 or later" in avcodec and "libavutil license:
    LGPL version 3 or later" in avutil. These are the scan's positive control.
  - It finds no string matching it in libx264 or libx265. UTF-16 strings, longer strings and
    other licence wording are not searched.
  - A looser scan does find the bytes `GPL` in both, but inside machine code (for example
    `...A\x0f\x11GPL\x8b...`), not in any string.
- **Reconciling the contradiction, as far as the artefact goes.**
  - The artefact shows three facts together:
    - no `--enable-gpl` in the configuration;
    - an "LGPL version 3 or later" licence string in every library;
    - libx264 and libx265 compiled in, bundled and working as encoders.
  - Why they coexist cannot be read from the wheel: UNKNOWN.
  - CHARC's note gives the premise that FFmpeg's configure normally refuses `--enable-libx264`
    and `--enable-libx265` without `--enable-gpl`. The artefact neither confirms nor explains
    that premise for this build.
- **Bearing on AD-2 (finding only).**
  - Measured: this wheel gives a PyAV encode path libx264, libx265, `h264_nvenc` and
    `hevc_nvenc`.
  - On CHARC's premise, a PyAV build without libx264 and libx265 would leave software HEVC and
    H.264 encoding to the separate FFmpeg process. Whether such a build keeps NVENC cannot be
    read from this wheel.
  - The decode-only candidates of claim 1 are unaffected: their encode side is the FFmpeg
    process either way.
