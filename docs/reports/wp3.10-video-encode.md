# WP3.10 -- Video encode, mux and timing (report)

**Status:** DRAFT (seat 3, after the Reviewer A round-1 remediation), branch `wp3.10` from main
`de206e2`. The synthetic and fixture legs are
complete; the footage legs (the GX011627 product leg through WP3.9's decoder, the AD-12 quality
table, the export FLOOR speed row) wait for WP3.9 on main (brief question 12) and are marked
PENDING below. Round 0 (the pts-carrier spike, the design table, the rulings) is recorded in
`docs/proofs/wp3.10-ledger.md`; its evidence is `C:\Users\rwsmy\clearwater-review-evidence\wp3.10\r0\`.

## 1. What was built

| File | What it is |
|---|---|
| `src/clearwater/io/video/nut.py` | The pts carrier on the encode pipe: a stdlib NUT framer (main, stream and INFO packets; per frame a syncpoint and a checksummed frame header with the full pts), the one-byte END SENTINEL and the input bitstream filter `setts=duration=...,noise=drop=lt(size,2)`. Invariant: a real frame is never under 2 bytes (`frame_header` refuses it), so the drop removes the sentinel only. |
| `src/clearwater/io/video/capability.py` | D74: `detect_capabilities()` (the `-encoders` listing plus one one-frame test encode per encoder and bit depth to the null muxer, run in parallel, cached per process) and `resolve_encoder(setting, capabilities)`, the ONE `"auto"` rule (NVENC when available, else libx265); `tool_env()`, the environment of every FFmpeg and ffprobe process the detection and the sink start (`FFREPORT` removed, so no tool writes a report file of its own). |
| `src/clearwater/io/video/encode.py` | IF-5 `VideoSink`: `FFmpegVideoSink`; `VideoEncodeError(kind, message)`; `encode_command`; `provenance_comment`; `QUALITY_LEVELS` / `QUALITY_VALUE` (AD-12). |
| `src/clearwater/io/video/verify.py` | The packet table (three ffprobe listings, no decode: the stream list, the video stream's packets, the audio streams' packets; a data track's packets are never listed) read from the source at `open` (tolerant of a cut-short file) and from the output at `close` (a non-zero ffprobe exit fails); `check_output` (D94 "verified"); `not_carried` (D105). |
| `src/clearwater/io/video/__init__.py` | Appended exports (X-V2): `FFmpegVideoSink`, `VideoEncodeError`, `QUALITY_LEVELS`, `detect_capabilities`, `resolve_encoder`; the module docstring's last sentence updated. |
| `tools/video_fidelity.py` | The V4 instrument (DR-18): `compare` and `encode` subcommands, reusing WP1.5's `compare.py` by import. |
| `tools/container_spike/spike.py` | DR-26 only (Q15): `_chapter` and the camera default resolve through `find_footage_file`. |
| `tests/test_io_video_encode_units.py`, `tests/test_io_video_encode.py`, `tests/test_video_fidelity.py` | The tests (section 6). `tests/test_io_video_probe_rules.py`: this package's four module names added to the expected set (standing grant), nothing else. |

`tools/video_io_bench.py` (the speed row) is PENDING: it runs WP3.9's `frames` into this sink.

## 2. The encode command (one FFmpeg process; each option's reason)

```
ffmpeg -nostdin -hide_banner -nostats -loglevel error -y          # -y: SafeWrite's temporary exists, empty
  -copyts                                                         # pts as written: start offset kept
  -noautorotate [-display_rotation <probe rotation>]              # matrix kept, CCW positive (AD-20)
  -bsf:v "setts=duration=if(eq(NEXT_PTS\,NOPTS)\,DURATION\,NEXT_PTS-PTS),noise=drop=lt(size\,2)"
  -f nut -i pipe:0                                                # input 0: the frames (NUT carrier)
  [-to <readable end - input start>] -i <source, absolute>        # input 1: tracks, metadata
  -map 0:v:0 -map 1:<each audio> -map 1:<each data stream except tmcd>
  -vf "<encode_filter(stream, bit_depth)>,setparams=color_primaries=..:color_trc=..:colorspace=..:range=.."
  NVENC:   -c:v hevc_nvenc -preset p5 -tune hq -rc vbr -b:v 0 -cq 18|23|28  -pix_fmt yuv420p|p010le
  libx265: -c:v libx265 -preset medium -crf 18|23|28 -x265-params log-level=error -pix_fmt yuv420p|yuv420p10le
  -profile:v main|main10
  -color_primaries .. -color_trc .. -colorspace .. -color_range ..    # D55; D54 assumed values tagged (DR-17)
  -tag:v hvc1 -fps_mode passthrough -enc_time_base:v demux -video_track_timescale <tb den>
  -c:a copy -c:d copy                                             # audio and data tracks never decoded
  -map_metadata 1 -map_metadata:s:v:0 1:s:v:0                     # creation time, timecode tag
  -write_tmcd 1                                                   # the timecode track is regenerated
  -metadata comment=<provenance JSON | empty>                     # D91; empty clears a source comment
  -movflags +negative_cts_offsets -f mp4 <out_path, absolute>
```

The process runs with `tool_env()` (no `FFREPORT`), as do the test encodes and the ffprobe
listings.

The truncation `-to` is relative to the input's earliest stream start: FFmpeg 9.0.2 applies an
input `-to` under `-copyts` from that start (measured: `-to 1.0` on a file starting at 0.4787 s
kept audio packets with dts below 1.4787 s).

## 3. The sink's rules

- **`open`** refuses before FFmpeg starts, naming the cause (`VideoEncodeError` kind
  `refused` / `unavailable` / `missing_tool`): a `"refuse"` probe fault (HLG, PQ); `"auto"`; an
  encoder not in (`hevc_nvenc`, `libx265`) or unavailable (with the D74 reason); a bit depth not
  an `int` in {8, 10} (so `8.0` and `True` are refused, DR-39 (d) not reopened), not allowed by
  D76 (`encode_pix_fmt`), or not available for the encoder; a quality not in
  `high`/`standard`/`draft`; a provenance object with a non-string key (`check_string_keys`), a
  value JSON cannot hold (NaN and infinity included), or JSON over 16 KiB; a time base not 1/N; a
  non-square sample aspect ratio (**P8, RULED by CHARC: refused at open, by name**; a ratio that
  cannot be seen is treated as 1:1; `VideoStreamInfo` gains no field; read from the sink's own
  ffprobe listing; GoPro and iPhone sources are square); an edit list other than the reproduced
  forms; a video pts below 0 (legal ISO without an edit list; NUT pts are unsigned). Reproduced
  forms: absent; one media segment (identity or the reorder delay); an empty edit then one media
  segment; every rate 1; the media segment's `media_time` equal to the track's earliest
  composition time from its sample table (equal = AD-22's identity-by-effect form, for example
  the Edits compilation's 3003/60000; anything else is a trim, refused by name -- round-2 #2,
  which closed a keyframe-aligned head trim that passed the next check; not applied when the
  sample table cannot be read); no head trim (first pts = the empty edit's dwell); no tail trim.
  Anything else is refused by name. The NUT stream header is built before FFmpeg starts (a
  header that cannot be built is a refusal, nothing running), and `out_path` is recorded first,
  so `abort` after a refused `open` deletes it.
- **`write`** checks, by name: `device == "cpu"` (Q14), the source time base, an integer pts that
  is a pts of the source and later than the previous one, a float32 NumPy array of the source's
  `(height, width, 3)`, no NaN (`rgb_to_planes`); quantises at the OUTPUT depth from a
  C-contiguous array (DR-39 (b) not reopened); polls FFmpeg; sends the NUT frame header and the
  payload as two pipe writes.
- **`close`** sends the sentinel at the end of the last frame (the next source pts, else the
  presentation end: the edit list's segment sum, or `start_pts + duration_ts` without one). The
  next pts comes from the source's own sample table (`stts` + `ctts` from `moov`, mapped onto the
  listed pts by the one offset every listed packet shows, `verify.read_sample_table`): a cut
  file's listing stops at the cut, its `moov` does not, so the last readable frame ends at the
  next sample's pts, exact in ticks (round-2 S1; `verify.readable_end`, which the instrument
  uses too). A truncated source whose sample table cannot be read and whose listing names no
  later frame is refused at `open`, by name. Then it
  closes stdin, waits with polling (`POLL_S` 0.2 s; backstop 1800 s), checks the exit status, then
  reads the output back and checks: frame count and every pts against the pts written, the video
  start, the video edit list against the written start and end (its `media_time` is checked
  through its effect: the demuxer applies it to every pts compared, so a wrong one fails the pts
  check), the display rotation, and every audio stream's packet pts against the source's -- all
  of them, or for a truncated source exactly the source's packets before the cut (a packet within
  2 us of the cut may go either way: FFmpeg reads `-to` and the input start in microseconds).
  A mismatch is `verify_failed`. Returns `SinkReport(frames_written, warnings, not_carried)`.
- **Failure** anywhere in `open` after FFmpeg starts (sending the header), `write` or `close`: FFmpeg is killed, its
  pipes closed, `out_path` deleted, the ORIGINAL error raised; a cleanup error is attached as a
  note (`add_note`), never in its place (DR-20 (6)). Every failure is final. **`abort`** is
  idempotent, never raises, deletes `out_path` and nothing else.
- **Threads:** the caller's thread writes stdin; one daemon thread drains stderr into an 8 KiB
  tail (ASCII-escaped in messages); stdout is discarded. A dead encoder is seen at the next write
  or inside the wait (DR-28 (4)).
- **Warnings:** D54 assumed tags (with the values written); a truncated source (tracks cut at the
  readable end); an unreadable tail (the tracks kept whole and running longer than the video;
  Q-B, reaches `SinkReport`). **`not_carried`:** creation date and time, the camera firmware tag,
  the timecode track, each non-timecode data track (or a sample-count shortfall, from the stream
  list's `nb_frames`; the track's packets are never listed), and the camera settings atoms
  (`moov/udta`) whenever the source has GoPro settings (Q10: not attempted).

## 4. The fidelity instrument (`tools/video_fidelity.py`, V4, DR-18)

WP1.5's 41 items plus five (the movie duration, `mvhd` over its timescale, the presentation form,
MANDATORY and exact; the AAC decoder configuration; priming and packet side data; frames with no
pts; the roster), with the product readings: colour rows against the D54-resolved
description, the raw tag beside it (Q-E); pixel format and bit depth against the selected depth
(D76); the video edit list "as written" SAME with a note where only the composition-offset
convention differs (AD-22) or where an absent source list became an identity list (AD-22
extended, Q-C) -- every note is listed in `summary.notes`, never silent; the effect item models an
absent list as the identity from media time 0; a cut-short source is compared on its readable
part (D86): the video ends at the readable end (`verify.readable_end`, the sink's own rule:
the next pts in the source's sample table) and, for a truncated file, each copied track at
the end of its last packet before it; the video duration, the video edit list as written (the
source's `media_time` and rate kept, AD-22's reading applied to the cut list), the video and
audio presentation effect, the movie duration and the copied packets are all the source's cut
there. DR-18: (1) NVENC proof from `nvidia-smi pmon` samples tied to the FFmpeg PID, the GPU
UUID and the encode window, the samples and the window on ONE monotonic clock (a sample counts
when its `nvidia-smi` call overlaps the window), `tied` only when the GPU those samples name
resolves to a UUID (round-2 #3), or the reason it is not tied (for example an encode shorter
than the sampling period, or a GPU index with no UUID); DR-18 (1) closes only on `tied`; (2) AAC configuration, priming and side data compared, MANDATORY; (3) a roster
invariant -- a missing or unexpected item makes a MANDATORY item DIFFERENT; (4) decoded frames with
no pts counted in both files. The telemetry data track's values are reduced to packet counts in
the record; no payload, digest or decoded value is kept. Every location-like tag value (keys
naming a location, ISO 6709, GPS, coordinates, latitude or longitude, or the QuickTime `xyz`
atom) and the digest of a location-like `udta` atom are replaced by a fixed marker as soon as
the facts are read, before any comparison: only their presence is compared, and no location
value reaches an item or a record (tested with a planted `location` tag; WP1.5's own record
carries it, the instrument's does not).

## 5. V4 per sample (libx265 always; NVENC on this laptop) -- every MANDATORY and REQUIRED item SAME

| Source | 8-bit out | 10-bit out | Notes |
|---|---|---|---|
| `vid-hevc8-bt709-full` | SAME | SAME (D76) | full range kept (`pc`) |
| `vid-hevc10` | refused (D76) | SAME | stays 10-bit |
| `vid-untagged` | SAME | SAME (D76, limited) | tagged bt709 / limited with the warning (DR-17) |
| `vid-truncated` | SAME (readable part) | SAME | warning; tracks cut at the readable end, 0.8008 s |
| `vid-vfr` | SAME | SAME | pts exact (D115) |
| `vid-rotated` | SAME | SAME | rotation 90 kept |
| `vid-hlg`, `vid-pq` | refused at open | refused | by name |
| synthetic offset + empty edit | SAME | -- | edit list equal as written |
| synthetic B-frames (x264 offset, x265 offset, x264 30000/1001) | SAME | -- | AD-22 note where `media_time` differs |
| synthetic absent edit list (plain, B-frames) | SAME | -- | Q-C note |
| synthetic timecode (offset; drop-frame) | SAME | -- | `tmcd` regenerated identical |
| synthetic VFR gap with offset | SAME | -- | |
| synthetic BT.601 | -- | SAME (D76) | BT.709 primaries with the warning (Q17) |
| synthetic 5.3K 8:7 (`slow`) | SAME | -- | |
| GX011627 (product leg through WP3.9) | PENDING | -- | round 0 (test-side decode): 41 items, M+R all SAME |

## 6. Tests

`tests/test_io_video_encode_units.py` 53, `tests/test_io_video_encode.py` 92 (+1 `footage`),
`tests/test_video_fidelity.py` 12 -- all passing on the branch (targeted runs, `-m "not
footage"`; the full suite waits for a window). They include eight planted wrong implementations that fail by name (CFR on
`vid-vfr`, start offset zeroed, `media_time` copied verbatim, colour tags omitted, `tv` on a `pc`
source, rotation dropped, audio re-encoded, 8-bit for a 10-bit source), the sentinel positive
control (a one-byte real frame is caught by the sink's check and by the instrument), the
transport through a capture seam (the bytes FFmpeg receives equal `rgb_to_planes` of the frames,
the pts and durations exact), DR-39 (a) asserted on the RGB side against AD-11 (max at most
0.13/255), the safe-write composition (no partial and no final on failure; the source
byte-identical with its mtime unchanged), and refusals before FFmpeg starts. The round-1
remediation added a test per accepted finding, each failing on the pre-remediation code: no
data-track packet listed; a location value never in the record; the `mvhd` row catching a planted
duration; the cut-short reading catching a planted video `media_time`, video rate, audio duration
and audio `media_time`; a cut audio stream accepting exactly the source's packets before the cut;
one clock for the NVENC proof; negative pts refused at `open`; no `FFREPORT` file from the
detection, the encoder or the listings; the header built before FFmpeg starts; a failed output
listing an error; `abort` after a refused `open` deleting `out_path`.

## 7. AD-12 quality table and the speed row -- PENDING (WP3.9)

## 8. Debt and decided items

- **AD-22 / DR-15:** implemented; proven on synthetic libx264/libx265 B-frame clips (and the
  Edits compilation in round 0, by boxes); the iPhone leg stays OPEN (Q7).
- **DR-17:** CLOSED on `vid-untagged` (tagged, warned, both depths).
- **DR-18:** (1)-(4) CLOSED by the instrument (section 4); (1) has a recorded reason when no
  sample sees the encoder.
- **DR-20 (4)** CLOSED for the product: the instrument's colour rows compare with the resolved
  description and a field it leaves `unknown` is DIFFERENT, never skipped; a `yuvj420p` output
  tagged `tv` fails the range row (and `encode_filter` refuses `yuvj420p` with a limited range
  at `open`). **(6)** CLOSED: a cleanup error is a note on the original error. **(7)** not this
  package's (WP3.13 / WP3.14). Observed, not claimed: the sink refuses duplicate or
  non-monotonic pts (cf. (2)) and names the muxer (`-f mp4`), so a `%` in a path is never an
  image-sequence pattern (cf. (3)).
- **DR-26:** CLOSED (Q15 grant).
- **DR-28 (4):** the encoder is polled on every write and wait. Limit: a live FFmpeg that stops
  reading blocks the pipe write (no timeout on a blocking write).
- **DR-39 (a)** CLOSED; **(b), (d)** not reopened; **(c)** PARTLY (D76 from limited-range and
  BT.601 sources, encoded and checked).

## 9. Consumer notes and limits

- **IF-9 / WP3.14:** provenance JSON over 16 KiB is refused at `open` (it travels on the command
  line); WP3.14 should keep provenance well under that.
- **WP3.14:** the sink deletes `out_path` on any failure; `SafeWrite.abort` tolerates the missing
  temporary. A cancel from another thread should call `abort` (it kills FFmpeg; the writing thread
  then sees `encoder_failed`).
- **WP4.3:** FFmpeg is started with `subprocess.Popen` directly; the shared CREATE_NO_WINDOW spawn
  helper (AD-23 extended) is WP4.3's.
- **`QUALITY_RATIO`** (`jobs.disk_space`, Q13): the measured ratios go into section 7.
- **Out of envelope, not refused:** data tracks other than the HERO13 set (for example an iPhone
  `mebx` track) and audio codecs MP4 cannot hold are passed to the muxer, which fails
  (`encoder_failed`, with FFmpeg's message).
- **`FFREPORT` and the probe (banked, not this package's):** WP3.7's `probe.py` `_run_ffprobe`
  (`cc28699`) still inherits `FFREPORT`, so a probe run with it set writes an ffprobe report file
  into the working folder; the sink's own processes do not. The fix (`env=` from a shared helper)
  is WP3.7's file.
- **Movie duration on a coarse movie timescale:** the `mvhd` row is exact. A source whose movie
  timescale cannot represent its presentation exactly (iPhone's 600 is the likely case) would read
  DIFFERENT against an output whose timescale can; untested (no iPhone clip; DR-15's iPhone leg).
  GoPro (movie timescale 30000) and every synthetic and fixture sample compare exactly.
- Only whole-clip exports are verified for the start offset: the sink copies audio and data whole,
  so an export that starts after the source's first frame is outside this package.
