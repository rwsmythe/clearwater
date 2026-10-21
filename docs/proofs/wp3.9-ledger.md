# WP3.9 ledger -- video decode

Cell: `implementer-opus-high` (wp39-cell1), worktree `.worktrees/wp3.9`, branch `wp3.9`, base
`de206e2`. Tier STRONG. Brief `docs/briefs/wp3.9-brief.md` (FINAL; CHARC rulings
`53d1d906e47fe2c9`: Q1-Q9 as drafted).

## Round 0 -- design table (2026-10-21, no product code yet)

Grounded on main `de206e2`, FFmpeg 9.0.2 (gyan) on this machine, the WP2.3 samples and the
GX011627 stream table (ffprobe, read only). Reproduction scripts and outputs: session scratchpad
`r0/` (`chk.py`, `pathchk.py`); every claim below marked EXECUTED was run there.

### 1. The FFmpeg command (argv list, no shell, `stdin=DEVNULL`)

```
ffmpeg -nostdin -hide_banner -nostats -loglevel repeat+level+info
       [-hwaccel cuda]                      # hw_decode=True and CUDA present (item 8)
       -noautorotate -copyts [-ss <S>]      # -ss only for a start_s with S > 0 (item 3)
       -i file:<absolute path>
       -map 0:v:0 -an -sn -dn
       -vf showinfo,<clearwater.color.decode_filter(probe.video)>
       -fps_mode passthrough -f rawvideo pipe:1
```

| Option | Reason |
|---|---|
| `-nostdin`, `stdin=DEVNULL` | never reads the console |
| `-hide_banner -nostats` | stderr carries only the side channel and messages; no `\r` progress lines |
| `-loglevel repeat+level+info` | `showinfo` logs at info; `level` prefixes `[info]`/`[warning]`/`[error]`, so the logged error tail excludes the info dump (stream metadata); `repeat` stops FFmpeg folding repeated lines |
| `-hwaccel cuda` (no `-hwaccel_output_format`) | frames downloaded to system memory, same filter (WP3.5) |
| `-noautorotate` | pixels as stored (D105; `orientation_applied=False`) |
| `-copyts` | source pts unchanged; a non-zero start stays non-zero (D94) |
| `-i file:<path>` | no protocol parsing of `C:`, no `%` expansion (DR-20 (3)) |
| `-map 0:v:0 -an -sn -dn` | the stream WP3.7's probe describes (first video stream, Q5); no audio, `gpmd`, `tmcd` mapped |
| `-vf showinfo,...` | pts side channel FIRST, then WP3.5's filter unchanged |
| `-fps_mode passthrough` | explicit: no frame dropped or duplicated |
| `-f rawvideo pipe:1` | planar `gbrp` / `gbrp10le` to the AD-23 pipe |

EXECUTED: on every decodable sample the `showinfo` pts equal `facts.pts.ticks` (first
`decoded.frames` for `vid-truncated`), strictly increasing, byte count = frames x
`rgb_frame_bytes` (`chk.py`: hevc10 45, hevc8 45, rotated 45, truncated 24 exit 0, untagged 45,
vfr 30). Software and `-hwaccel cuda` give identical bytes (md5) on hevc8 (`nv12` download),
hevc10 (`p010le`), untagged. A copy under `a%d b%05d <e-acute><CJK>/clip%03d.mp4` decodes via
`file:` (30 frames).

### 2. The pts side channel and pairing (Q4)

- A daemon drain thread reads stderr line by line (UTF-8, `replace`). It parses
  `config in time_base: N/D` (must equal `probe.video.time_base`, else `"pts"` error) and each
  `[Parsed_showinfo_0 @ ...] [info] n: <n> pts: <p>` line into a `queue.SimpleQueue`; keeps the
  last 20 non-info lines (bounded deque) for the error tail; posts an EOF sentinel.
- The consumer reads exactly `rgb_frame_bytes` into one reusable buffer, THEN takes the next pts
  from the queue (blocking until a line or the sentinel). Causality: `showinfo` logs frame n in
  the filter graph before the frame reaches the muxer that writes its bytes, so line n precedes
  frame n's bytes; the wait only covers the drain thread's lag. A 60 s guard raises `"pts"`.
- Checks, each an error by name, never a drop (DR-20 (2)): `n` contiguous from 0; `pts` an
  integer (`NOPTS` -> `"pts"`); strictly increasing; a missing line at stderr EOF -> `"pts"`;
  lines left over at stdout EOF (orphan) -> `"pts"`. No ffprobe run in `frames`.

### 3. Seeking (Q6) -- premise correction

- `start_s`: Python guard yields the first frame with `pts >= start_s` (exact `Fraction`). Seek
  arg `S = start_s - 1/probe.video.frame_rate - probe.start_offset_s`, floored to a microsecond;
  `-ss` passed only when `S > 0`.
- PREMISE: the brief/prototype method ("input `-ss` a little before `start_s` plus `-copyts`")
  omits that under `-copyts` FFmpeg's input `-ss` is RELATIVE TO THE CONTAINER START. EXECUTED:
  a copy of hevc8 with its start moved to 2 s (`-output_ts_offset 2`): `-ss 0.5` -> first pts
  75015 (2.5 s), `-ss 2.5` -> 0 frames. Hence the `- start_offset_s` term. `-seek_timestamp 1`
  (absolute seek) is unusable: on the zero-start hevc8 it yields 0 frames with 2 errors (EXECUTED).
- Why the target is never after `start_s`: FFmpeg's container start is the earliest audio/video
  start (data streams may only pull it earlier), so it is <= `probe.start_offset_s` (min of
  video/audio `start_pts`, WP3.7). REASONED from libavformat `update_stream_timings`, not
  executed beyond the 2 s copy. In-envelope files (HERO13, WP2.3) all start at 0 (EXECUTED on
  GX011627: every stream `start_pts=0`).
- EXECUTED (hevc8, frame pts 22022 = 0.7340667 s): `-ss 0.733066`, `0.734066` and `0.734067`
  all deliver 22022 first (FFmpeg keeps a frame 0.3 us before its target); FFmpeg's accurate
  seek trims before `showinfo` (n restarts at 0); a past-the-end `-ss` exits 0 with no frame.
- `end_s` exclusive: stop at the first frame with `pts >= end_s` (pts strictly increasing), then
  shut FFmpeg down; no `-to`/`-t`. `end_s <= start_s` or `start_s` past the end -> nothing.

### 4. Pipe, threads, bound, lifecycle

- `pipes.py`: `BIG_PIPE_BYTES = 1 << 25` (docstring: WP2.1S row `b` 16.11 ms/frame vs 55.87 ms
  row `a`, W4/W2, GX011627). `open_frame_pipe(size=BIG_PIPE_BYTES) -> tuple[int, int] | None`:
  on `win32` `_winapi.CreatePipe(None, size)` + `msvcrt.open_osfhandle`; on `OSError`, or off
  Windows, `None` with the reason logged once per process. No `F_SETPIPE_SZ` code. Decode uses
  the fds (parent closes its write end after `Popen`) or `stdout=PIPE` on `None`. Forced-failure
  tests monkeypatch the private creator to raise `OSError`, so the real fallback path runs.
- Threads: the caller's thread reads stdout (no stdout thread; back-pressure through the pipe);
  one drain thread on stderr (FFmpeg never blocks on stderr). Python-side bound per iterator
  (N4): one raw buffer (<= 49.8 MB, 10-bit 4K) + the float32 frame being built (<= 99.5 MB);
  pipe <= 32 MiB; the pts queue is small ints, ahead only by FFmpeg's in-flight frames.
- `frames()` validates at call (refuse fault, `decode_filter`/`ColorError`, `find_tool`) and
  returns an iterator object with `close()`; FFmpeg starts at the first `next()`.
- Exhaustion: wait for exit (bounded, then kill), join the drain thread (bounded), classify.
  `close()`: idempotent kill + reap + close fds + join, bounded. GC: `weakref.finalize` runs the
  same shutdown (the drain thread holds only a small state object, never the iterator). Any
  raise shuts down first; `next()` after close/raise -> `StopIteration`.

### 5. Errors (Q3) -- what ends cleanly vs raises

`VideoDecodeError(kind, message)` in `decode.py` (exported), kinds `"refused"`, `"unreadable"`,
`"pts"`; ASCII-safe message naming `ascii_text(path.name)`. Missing ffmpeg: `VideoProbeError
("missing_tool")` (`find_tool`), at call. Stream outside WP3.5's set: `ColorError`, at call.

| At stdout EOF / failure | probe flagged `truncated`/`unreadable_tail` | probe clean |
|---|---|---|
| whole frames, exit 0 | ends | ends |
| whole frames, exit nonzero | ends (warning is the probe's fault; tail logged) | `"unreadable"` after the last good frame, tail logged |
| partial frame (short read) | `"unreadable"` | `"unreadable"` |
| any pts check of item 2 | `"pts"` | `"pts"` |
| exit 0 with `[error]` lines | logged | logged (question B) |

### 6. `Frame` values (Q7)

`pixels = planes_to_rgb(buffer, ...)` (a new array; the buffer is reused), `device="cpu"`,
`color=probe.video.color`, `orientation_applied=False`, `pts_ticks` from `showinfo`,
`time_base=probe.video.time_base`, `pts=pts_ticks*time_base` (exact), `index` 0-based over the
frames this iterator yields.

### 7. Names and files

Class `FFmpegVideoSource` in `src/clearwater/io/video/decode.py`; `pipes.py`; append
`FFmpegVideoSource`, `VideoDecodeError` (+ one docstring sentence) to `io/video/__init__.py`;
`probe.py:423` and `:430` `path.name` -> `_name(path)` (`ascii_text`, DR-36 (a)). Tests:
`tests/test_io_video_decode.py` (samples, pixels, seeking, D54, DR-39 (c), paths),
`tests/test_io_video_decode_lifecycle.py` (close, GC, death, AD-23 fallback),
`tests/test_io_video_decode_rules.py` (static, imports, DR-36 (a)),
`tests/test_io_video_decode_hw.py` (`gpu`, `footage`). Never-re-probed test alters
`vid-untagged` (yuv420p) range limited->full: altering hevc8's `yuvj420p` to limited is refused
by WP3.5's `_check` by design, so it cannot carry the test.

### 8. Questions / STOPs

- **A (STOP, Q8 premise false).** "`-hwaccel cuda` ... FFmpeg falls back to software decode by
  itself" does not hold when no CUDA device exists. EXECUTED: `CUDA_VISIBLE_DEVICES=-1 ffmpeg
  -hwaccel cuda -i hevc8...` -> `cuInit ... CUDA_ERROR_NO_DEVICE`, `Hardware device setup failed
  for decoder`, exit 127, 0 bytes (same with `-hwaccel_device 7`). FFmpeg's own fallback only
  covers a device that exists but cannot decode the stream. Recommended: a per-process cached
  CUDA check (`ffmpeg -hide_banner -v error -init_hw_device cuda -f lavfi -i color=s=64x64:d=0.1
  -f null -`: exit 0 real, 127 hidden, EXECUTED); unavailable -> software decode, logged once;
  test with `CUDA_VISIBLE_DEVICES=-1`. Alternative: retry in software when an hw decode exits
  nonzero before its first frame.
- **B (choice left open).** FFmpeg exit 0 with `[error]` lines on a probe-clean file (concealed
  corruption). Recommended: log (WARNING, ASCII tail), do not raise -- decoders also log errors
  on legitimate streams (REASONED, not reproduced here); raising would fail a whole export.
- **C (window).** The `footage` and `gpu` legs decode GX011627 (681 x 4K) about four times
  (software, forced fallback, independent reference, CUDA). Not timing; streamed, low memory.
  Recommended: they run only inside a granted window (with or as the full pytest).
- Observation, not acted on: like WP3.7's ffprobe calls, the FFmpeg child gets no
  `CREATE_NO_WINDOW` (a console may flash under a windowed GUI on Windows); that would be
  OS-specific code beyond AD-23, so it is not added here.

### 9. Round-0 rulings (orchestrator, FINAL, 2026-10-21)

Table APPROVED as written, the seek correction included. A: Q8 premise corrected at round 0,
reproduced; ruled the cached CUDA check (no retry path), test with `CUDA_VISIBLE_DEVICES=-1`.
B: ruled as recommended (one WARNING, no raise; Limits says reasoned, not reproduced). C: the
footage and gpu legs run only in a granted window. CREATE_NO_WINDOW: banked by the orchestrator
for WP4.3; one Limits line. Raised during the build (message to the dispatcher, ruling pending):
WP3.7's `tests/test_io_video_probe_rules.py::test_the_package_exists_and_has_the_expected_modules`
pins the module set of `io/video` and fails with `decode.py` and `pipes.py` (requested: a
two-line grant).

## Round ledger

| Round | Crit | Major | Minor | In-env | Out-env | NEW | REOPENED | Reverts | Fix kind | Depth |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 (design) | - | - | - | - | - | - | - | - | - | 139,790 |
