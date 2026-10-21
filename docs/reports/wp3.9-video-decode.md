# WP3.9 -- Video decode (report)

Package: `clearwater.io.video.decode` (`FFmpegVideoSource`, `FrameStream`, `VideoDecodeError`,
`cuda_decode_available`, `decode_command`, `seek_position`) and `clearwater.io.video.pipes`
(`BIG_PIPE_BYTES`, `open_frame_pipe`). Brief `docs/briefs/wp3.9-brief.md` (FINAL); round-0
rulings in `docs/proofs/wp3.9-ledger.md`. FFmpeg 9.0.2 (gyan), Windows 11, Python 3.12.

## What it does

`FFmpegVideoSource.probe(path)` delegates to WP3.7's `probe`. `frames(probe, *, hw_decode,
start_s=None, end_s=None)` checks at once (a `"refuse"` fault raises `VideoDecodeError("refused")`
before any process starts; `ColorError` for a stream outside WP3.5's set; `VideoProbeError
("missing_tool")` without `ffmpeg`) and returns a `FrameStream`; FFmpeg starts at the first
`next()`. One FFmpeg process per call (AD-2):

```
ffmpeg -nostdin -hide_banner -nostats -loglevel repeat+level+info [-hwaccel cuda]
       -noautorotate -copyts [-ss S] -i file:<absolute path> -map 0:v:0 -an -sn -dn
       -vf showinfo,<decode_filter(probe.video)> -fps_mode passthrough -f rawvideo pipe:1
```

- **pts.** `showinfo` (first in the chain) logs each frame's number and pts on standard error
  before the frame reaches the pipe. A daemon thread drains standard error into a queue; the
  reader reads one whole frame (`rgb_frame_bytes`) and then takes the next pts. The filter's
  input time base must equal `probe.video.time_base`; the frame numbers must run 0, 1, 2, ...;
  each pts must be an integer and strictly greater than the last. A repeat, a decrease, `NOPTS`,
  a gap, a frame without a line, or a line without a frame after a normal exit is
  `VideoDecodeError("pts")`, never dropped (DR-20 (2)). `-copyts` keeps the source's pts;
  `-fps_mode passthrough` neither drops nor repeats a frame.
- **Frame.** `pixels = planes_to_rgb(...)` (float32 `(H, W, 3)` RGB, `[0, 1]`, 10-bit kept as
  10-bit), `device "cpu"`, `color = probe.video.color` (the probe's, D54 included; no ffprobe
  run), `orientation_applied False` (pixels as stored, `-noautorotate`), `pts = pts_ticks *
  time_base` (exact `Fraction`), `index` 0-based over the frames this iterator yields.
- **Seeking.** The first frame yielded is the first with `pts >= start_s`; none with
  `pts >= end_s` is yielded. FFmpeg's input `-ss` counts from the container start under
  `-copyts`, so `S = start_s - 1/frame_rate - start_offset_s`, floored to a microsecond, passed
  only when positive; frames before `start_s` are discarded by exact pts in Python. `end_s` is
  applied in Python only.
- **Pipe (AD-23).** `open_frame_pipe()` creates a 32 MiB anonymous pipe on Windows
  (`_winapi.CreatePipe`); when that fails, or off Windows, it returns None, the reason is logged
  once per process, and the decoder uses `subprocess.PIPE`. Nothing else is OS-specific.
- **CUDA (Q8, premise corrected at round 0, reproduced).** `-hwaccel cuda` on FFmpeg 9.0.2 exits
  127 with no frames when no CUDA device exists (FFmpeg only falls back by itself when a device
  exists but cannot decode the stream). So `cuda_decode_available()` runs `ffmpeg -init_hw_device
  cuda` on a tiny generated input once per process; without CUDA, `hw_decode=True` decodes in
  software and the reason is logged once.
- **Ends and errors (spec 5.4, D86).** At the end of the output FFmpeg is reaped. Exit 0: the
  iterator ends (a pts line left over is `"pts"`; `[error]` lines are logged once as a WARNING
  with an ASCII-safe tail). Nonzero exit: on a file the probe flagged `truncated` or
  `unreadable_tail` the iterator ends (logged at INFO); on a clean file `VideoDecodeError
  ("unreadable")` after the last good frame, with the tail logged. A frame cut short is
  `"unreadable"` on any file. FFmpeg that cannot be started is `"unreadable"`. Every `"pts"`
  error logs FFmpeg's ASCII-safe tail too.
- **Lifecycle and bound (N4).** `close()` kills FFmpeg, reaps it, closes the pipe and joins the
  thread (bounded waits); `weakref.finalize` does the same for an iterator dropped without
  `close()` (the thread holds no reference to the iterator). A close from another thread ends
  the reader with `StopIteration`; no frame is returned after `close()` has returned. Per iterator, Python holds one raw frame buffer and the frame
  being built; FFmpeg is held back by the pipe.

## Evidence

| Claim | Test |
|---|---|
| Every decodable sample: frame count, tick list (truncated: first 24), pts hash = `facts.pts.sha256` (DR-36 (b)), size, bit depth, colour | `test_io_video_decode.py::test_every_decodable_sample_*`, `::test_the_decoded_ticks_hash_*` |
| Pixels equal an independent FFmpeg run of the same filter (V4 / V9 decode leg) | `::test_the_pixels_equal_an_independent_ffmpeg_run` |
| 10-bit stays 10-bit | `::test_ten_bit_stays_ten_bit` |
| `vid-vfr` exactly its 30 intended pts; `vid-truncated` 24 then a clean end; HLG/PQ refused before a process starts; `vid-rotated` 320 x 180 as stored | `::test_the_vfr_*`, `::test_the_truncated_*`, `::test_hlg_and_pq_*`, `::test_the_rotated_*` |
| Never re-probed: an altered range changes the pixels as an independent run with that range | `::test_the_colour_description_given_is_used_and_nothing_is_re_probed` |
| Seeking at every pts, between, before, after; `end_s` exclusive; a file starting at 2 s | `::test_start_*`, `::test_end_is_exclusive`, `::test_seeking_is_exact_on_a_file_that_does_not_start_at_zero` |
| DR-39 (c): `yuvj420p` + BT.601 full; a `center` siting | `::test_a_yuvj420p_bt601_*`, `::test_a_non_left_chroma_siting_*` |
| DR-20 (3): a folder named with `%` and non-ASCII characters | `::test_a_path_with_percent_*` |
| Lifecycle: close after one frame, dropped iterator, planted FFmpeg death, close from another thread | `test_io_video_decode_lifecycle.py` |
| pts faults and the end table, with a stand-in FFmpeg | `test_io_video_decode_lifecycle.py::test_a_bad_pts_*` and neighbours |
| AD-23: one constant; 16 MiB fit without a reader; the large pipe used; forced fallback identical on every sample, reason logged once | `test_io_video_decode_lifecycle.py::test_the_pipe_*`, `::test_the_large_pipe_*`, `::test_the_forced_fallback_*` |
| Q8: CUDA hidden -> software, same frames, logged once | `::test_hw_decode_without_cuda_*` |
| Command maps `0:v:0` only, no other stream; no ffprobe; imports; OS-specific code only in `pipes.py`; DR-36 (a) | `test_io_video_decode_rules.py` |
| `gpu`: CUDA bytes and pts equal software on every sample; `footage`: GX011627 681 frames, pts `k x 1001`, per-frame hashes equal an independent run, also through the forced default pipe and CUDA | `test_io_video_decode_hw.py` |

## Files outside the package

- `src/clearwater/io/video/probe.py`: only the two DR-36 (a) log lines (Q9 grant).
- `tests/test_io_video_probe_rules.py`: only `"decode.py"` and `"pipes.py"` added to the expected
  module set (orchestrator grant, 2026-10-21; WP3.10 adds its own names the same way).

## Debt

- DR-36 (a) CLOSED: `probe.py` `_movie`'s two warnings name the file through `_name(path)`
  (`ascii_text`); the second is wrapped over three lines by the formatter.
- DR-36 (b) CLOSED: the decoded tick list hashes to `facts.pts.sha256` on every intact sample.
- DR-39 (c) PARTLY: the two decode rows above; the D76 rows are WP3.10's.
- DR-20 (3), (5) PARTLY for the decode command: `file:` URLs; `0:v:0` is the probe's stream; a
  cover-art first stream stays out of envelope (DR-20 (5) open for the probe side).
- DR-28 (4) PARTLY (decode side): a dead FFmpeg surfaces at the next `next()`.

## Review adjudications

- Reviewer A r1 #1 (MAJOR as raised; rejected on behaviour, confirmed by the orchestrator): a short
  read on a probe-flagged file raises `"unreadable"`. D86's clean stop at the readable end is FFmpeg
  exiting 0 at a frame boundary on a truncated input (executed on `vid-truncated`: 24 frames,
  exit 0); a short read means FFmpeg died inside a frame write, and every complete frame has been
  delivered before the raise.
- Reviewer A r2 #1 (MAJOR, confirmed and fixed): a `close()` from another thread during the lazy
  FFmpeg start could leave the process and thread running; the start now runs under the shutdown
  lock and starts nothing once closed.

## Limits

- `[error]` lines with exit 0 on a clean file are logged, not raised: reasoned (decoders log
  errors on legitimate streams), not reproduced.
- The seek offset assumes FFmpeg's container start is not later than the probe's
  `start_offset_s` (the earliest audio or video start): reasoned from libavformat; executed on a
  file starting at 2 s; every in-envelope file starts at 0.
- On a probe-flagged file, a nonzero FFmpeg exit at a frame boundary ends the iterator; frames
  FFmpeg had decoded but not yet written when it failed are not recovered. A frame cut short is
  `"unreadable"` on every file, flagged or not (FFmpeg died inside a write; it ends a truncated
  input at a frame boundary with exit 0), after every complete frame has been delivered.
- The FFmpeg child is started without `CREATE_NO_WINDOW`, as WP3.7's ffprobe calls are; a
  console window may flash under a windowed GUI on Windows (banked by the orchestrator for
  WP4.3; OS-specific, outside AD-23).
- AD-23's figure is for 8-bit 4K; a 10-bit 4K frame is larger than the buffer (correct either
  way, not re-timed). Linux `F_SETPIPE_SZ` is not implemented (the default pipe is used).
