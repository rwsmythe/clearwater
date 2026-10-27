# WP3.10 -- Video encode, mux and timing (report)

**Status:** FINAL (seat 9), branch `wp3.10` on main `718324b` (WP3.9's decoder, WP3.4 and
WP3.11 merged); product head `e04a7cb`, the AD-12 mapping as RULED (CHARC `c1d67b39bb72cc1f`,
AD-12 amended on main `759f0d0`). Reviewer A rounds 1-10 are closed: the product converged at
round 4, the floor-row instrument at round 8, the NVENC rate ceiling at round 10; the mapping
commit is values-only and owed no round (the ruling). The footage legs ran in seat 7's and seat
8's footage windows, the floor row in seat 9's exclusive window (section 7). Round 0 (the pts-carrier spike, the design table, the rulings) is recorded in
`docs/proofs/wp3.10-ledger.md`; its evidence is `C:\Users\rwsmy\clearwater-review-evidence\wp3.10\r0\`.

## 1. What was built

| File | What it is |
|---|---|
| `src/clearwater/io/video/nut.py` | The pts carrier on the encode pipe: a stdlib NUT framer (main, stream and INFO packets; per frame a syncpoint and a checksummed frame header with the full pts), the one-byte END SENTINEL and the input bitstream filter `setts=duration=...,noise=drop=lt(size,2)`. Invariant: a real frame is never under 2 bytes (`frame_header` refuses it), so the drop removes the sentinel only. |
| `src/clearwater/io/video/capability.py` | D74: `detect_capabilities()` (the `-encoders` listing plus one one-frame test encode per encoder and bit depth to the null muxer, run in parallel, cached per process) and `resolve_encoder(setting, capabilities)`, the ONE `"auto"` rule (NVENC when available, else libx265); `tool_env()`, the environment of every FFmpeg and ffprobe process the detection and the sink start (`FFREPORT` removed, so no tool writes a report file of its own). |
| `src/clearwater/io/video/encode.py` | IF-5 `VideoSink`: `FFmpegVideoSink`; `VideoEncodeError(kind, message)`; `encode_command`; `provenance_comment`; `QUALITY_LEVELS`; `NVENC_CQ` / `X265_CRF` (AD-12: one value table per encoder); the NVENC rate ceiling `nvenc_rate` (`NVENC_BITS_PER_PIXEL`, `NVENC_RATE_SHARE`) and `level_warning` (AD-12 as amended, round 9). |
| `src/clearwater/io/video/verify.py` | The packet table (three ffprobe listings, no decode: the stream list, the video stream's packets, the audio streams' packets; a data track's packets are never listed) read from the source at `open` (tolerant of a cut-short file) and from the output at `close` (a non-zero ffprobe exit fails); `check_output` (D94 "verified"); `not_carried` (D105); `read_hevc_level` (the level and tier an HEVC file signals, read from its `hvcC`). |
| `src/clearwater/io/video/__init__.py` | Appended exports (X-V2): `FFmpegVideoSink`, `VideoEncodeError`, `QUALITY_LEVELS`, `detect_capabilities`, `resolve_encoder`; the module docstring's last sentence updated. |
| `tools/video_fidelity.py` | The V4 instrument (DR-18): `compare` and `encode` subcommands, reusing WP1.5's `compare.py` by import. |
| `tools/video_io_bench.py` | The export FLOOR row (Q11): WP3.9's `frames` straight into the sink, no correction; per-stage and per-frame times, min/min, the strays, clocks and temperatures, peak process-tree RSS and graphics memory, the NVENC proof; `run` and `floor` subcommands (section 7.3). |
| `tools/container_spike/spike.py` | DR-26 only (Q15): `_chapter` and the camera default resolve through `find_footage_file`. |
| `tests/test_io_video_encode_units.py`, `tests/test_io_video_encode.py`, `tests/test_io_video_encode_bench.py`, `tests/test_video_fidelity.py` | The tests (section 6). `tests/test_io_video_probe_rules.py`: this package's four module names added to the expected set (standing grant), nothing else. |


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
  NVENC:   -c:v hevc_nvenc -preset p5 -tune hq -rc vbr -b:v 0 -cq 22|26|30
           -maxrate <ceiling> -bufsize <ceiling> -tier main -level <L>  -pix_fmt yuv420p|p010le
  libx265: -c:v libx265 -preset medium -crf 21|26|30 -x265-params log-level=error -pix_fmt yuv420p|yuv420p10le
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

**The NVENC rate ceiling (AD-12 as amended, round 9; `nvenc_rate`).** Without a ceiling NVENC
signals HEVC level 5.0 and that level's Main-tier cap overrides `-cq`, so the three levels came
out at one rate on busy 4K (seat 7: GX011627 High / Standard / Draft 0.356 / 0.350 / 0.338 x
the camera's rate, PSNR flat 35.82 dB). The sink therefore sets `-maxrate` = 0.24 bit/pixel
(`NVENC_BITS_PER_PIXEL`, FINAL) x width x height x frame rate for High, a half for Standard and
a quarter for Draft (`NVENC_RATE_SHARE`), and `-bufsize` = the ceiling; for an HEVC source
signalling a Main-tier level the High ceiling is at most that level's Main-tier cap, so the
output never signals above the source, except a source whose own signalled level cannot hold
its picture (warned). Given `-maxrate` alone, NVENC silently switches to the
High tier once the ceiling passes the Main-tier cap of the level it picked, even with `-tier
main`, so `-tier main -level L` is set explicitly at the lowest Main-tier level that holds the
ceiling and the picture. GX011627 (3840x2160 at 30000/1001, source 6.0 Main): ceilings 59.66 /
29.83 / 14.92 Mb/s, signalled 5.2 / 5.1 / 5.0 Main. `-cq` decides calm scenes and the ceiling
binds busy ones. libx265 has no ceiling.

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
  so `abort` after a refused `open` deletes it. A refusal is final: the sink cannot be opened
  again (round-4 finding 3).
- **`write`** checks, by name: `device == "cpu"` (Q14), the source time base, an integer pts that
  is a pts of the source and later than the previous one, a float32 NumPy array of the source's
  `(height, width, 3)`, no NaN (`rgb_to_planes`); quantises at the OUTPUT depth from a
  C-contiguous array (DR-39 (b) not reopened); polls FFmpeg; sends the NUT frame header and the
  payload as two pipe writes.
- **`close`** first refuses, by name (`verify_failed`, "The video is incomplete"), frames that
  are not the source's whole readable video (`verify.missing_frames`, Reviewer B pass 1 #1): the
  pts written must be exactly the source's listed video pts in presentation order (sorted, so a
  B-frame decode-order listing, VFR and an empty-edit dwell need nothing special), for a
  `truncated` source only the packets listed before its first corrupt packet in file (decode)
  order, which is what WP3.9 decodes (with B-frames a P-frame before the cut can lie after
  B-frames listed after it; Reviewer B pass 2 #1, the gate fix; `_plan_tracks` cuts the tracks
  from the same set) (Q-B, the frames before the cut;
  `verify.readable_video_pts`), and for an `unreadable_tail` source every such pts up to the last
  one written (its decodable end cannot be told without decoding, D86). That is the ONE place a
  short output verifies: an early stop on an `unreadable_tail` source is the decoder's end, never
  a gap (orchestrator ruling on the Reviewer B pass 1 remediation). The message names the
  first missing pts and the counts, or the frames written past the readable end. The check runs
  BEFORE the sentinel, so FFmpeg never finishes an incomplete export, and on the sink's own state
  rather than on FFmpeg's output: what is missing is a caller fact, known before any output exists.
  Then `close` sends the sentinel at the end of the last frame (the next source pts, else the
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
- **Failure** when FFmpeg cannot be started (`encoder_failed`, the `OSError` as its cause;
  Reviewer B pass 1 #7), or anywhere in `open` after FFmpeg starts (starting the stderr thread --
  round-4 finding 1, now `encoder_failed` -- or sending the header), `write` or `close`: FFmpeg is killed, its
  pipes closed, `out_path` deleted, the ORIGINAL error raised; a cleanup error is attached as a
  note (`add_note`), never in its place (DR-20 (6)); `out_path` is deleted in a `finally`, so a
  process step that raises (FFmpeg not ending within 30 s) never skips the deletion (round-3
  finding 1). Every failure is final. **`abort`** is idempotent, never raises, deletes `out_path`
  and nothing else; after a failure or an earlier `abort` whose cleanup did not finish it repeats
  the cleanup (a second `abort` deletes what the first could not); after `close` it does nothing.
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
UUID and the encode window -- from just before FFmpeg starts to the moment the sink sees FFmpeg
exit, before the output is verified (round-4 finding 2; it used to run on through the
verification) -- the samples and the window on ONE monotonic clock (a sample counts
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

## 5. V4 per sample (libx265 always; NVENC on this laptop) -- every MANDATORY and REQUIRED item SAME (except the Edits compilation's two: section 9)

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
| GX011627 (product leg through WP3.9, NVENC 8-bit Standard) | SAME | -- | 46 items; DIFFERENT only BEST-EFFORT 8 (the round-0 eight: timecode value on stream tags, camera `udta` atoms, ftyp brands, container tags, stream tags, track layout, video sample-entry boxes, non-video edit lists as written); `gpmd` packet counts and creation time SAME; NVENC proof tied (seat 8 on `0b76301`; the mapping commit changes only the `-cq` value) |
| Edits compilation (1080p60 H.264, 10,800 frames, NVENC 8-bit Standard) | 2 MANDATORY DIFFERENT | -- | `mvhd` and the audio entry of the edit-list effect differ by 0.79 ms, under one 1 ms movie tick (section 9); every other item SAME; reorder delay 3003/60000 accepted with the AD-22 note (seat 7 on `5727842`) |

## 6. Tests

`tests/test_io_video_encode_units.py` 80, `tests/test_io_video_encode.py` 113 (2 `footage`),
`tests/test_io_video_encode_bench.py` 50, `tests/test_video_fidelity.py` 13 and
`tests/test_io_video_probe_rules.py` 26 (1 `footage`; this package's module names only). At
`e04a7cb`: the five modules `-m "not footage"` 274 passed, 3 deselected (5:35). At `4537881`
(Reviewer B pass 1 remediation): 279 passed, 3 deselected (6:33). The bench's two timing
assertions (the frame intervals against the stream stage, within 0.01 s) flaked under pytest
(1 run in 6 on `e04a7cb`): the stream also holds steps outside every interval where a thread
switch cost up to 0.035 s. Their tolerances now come from what they guard: half the shortest
planted strays pause (a pause left inside an interval still fails) and 0.1 s for the row (a
`close` counted into the stream still fails); both negative cases planted and shown failing.
The negatives are evidence (`reviewB-remed\`), not assertions: the row test does not itself
assert that `close` exceeds 0.1 s (Reviewer B pass 2 #5).
ruff, ruff format (211 files) and mypy strict (123 files) clean. The three `footage` tests passed at `0b76301` in
seat 8's footage window (the mapping commit touches no footage test). The full suite is the
orchestrator's stacked gate (seat 7's run on `5727842`: 4434 passed, 2 skipped). They include eight planted wrong implementations that fail by name (CFR on
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
listing an error; `abort` after a refused `open` deleting `out_path`. Reviewer B pass 1 added
a gap in the middle and an early stop refused at `close` (both DID NOT RAISE on `e04a7cb`), the
readable-pts rule on decode-order listings, a truncated cut and an unreadable tail, and FFmpeg
that cannot be started failing the sink for good (on `e04a7cb` `out_path` stayed). Round 9 added the NVENC
ceiling tests (the pixel-rate ceilings, the source's cap, the explicit level, the level warning,
a small-sample encode that signals the expected Main-tier level; each failing before the fix) and
round 10 pinned the footage test to the exact 5.2 / 5.1 / 5.0 Main; the AD-12 unit test pins all
six values of the ruled mapping.

## 7. AD-12 quality table, `QUALITY_RATIO` and the floor row

### 7.1 The mapping (RULED)

CHARC `c1d67b39bb72cc1f`, AD-12 amended on main `759f0d0`, FINAL; product commit `e04a7cb`.

| Level | NVENC `-cq` (`NVENC_CQ`) | NVENC ceiling (4K 29.97) | libx265 `-crf` (`X265_CRF`) | Target (AD-12) |
|---|---|---|---|---|
| High | 22 | 0.24 bit/pixel = 59.66 Mb/s | 21 | about the camera's rate on busy scenes |
| Standard | 26 | a half = 29.83 Mb/s | 26 | about half |
| Draft | 30 | a quarter = 14.92 Mb/s | 30 | about a quarter |

Measured through the product sink (output video bit rate as a multiple of the camera's, PSNR y
to the source; GX011627 busy, camera 55.53 Mb/s; GX011610 calm, 5.15 Mb/s, the lowest camera
rate among Snorkel clips under 1000 frames; evidence `s7-footage\` and `s8-footage\` under
`C:\Users\rwsmy\clearwater-review-evidence\wp3.10\`; nothing footage-derived committed). The
ruled values, seat 8 (the table patched in the driver process; NVENC at the High ceiling, so its
Standard and Draft columns show where `-cq` alone lands before the lower ceilings bind):

| Clip | Encoder | High | Standard | Draft |
|---|---|---|---|---|
| GX011627 | libx265 crf 21 / 26 / 30 | 1.073, 41.01 dB | 0.484, 37.77 dB | 0.246, 35.74 dB |
| GX011610 | libx265 crf 21 / 26 / 30 | 1.194, 51.86 dB | 0.539, 49.41 dB | 0.278, 47.46 dB |
| GX011627 | NVENC cq 22 / 26 / 30 (High ceiling) | 0.927, 39.65 dB | 0.638 (above the Standard ceiling) | 0.376 (above the Draft ceiling) |
| GX011610 | NVENC cq 22 / 26 / 30 | 2.65, 54.97 dB | 1.57, 53.22 dB | 0.94, 51.24 dB |

On the ruled code with its own ceilings (the floor row, 7.3, Standard): GX011627 NVENC 8-bit
0.492, NVENC 10-bit 0.496, libx265 0.484; GX011625 (calm 4K, camera 6.58 Mb/s) NVENC 8-bit 1.276.

Superseded figures, for the record: at 18 / 23 / 28, NVENC with the ceilings (seat 8) GX011627
1.018 / 0.515 / 0.258 (39.70 / 37.08 / 34.87 dB) and GX011610 4.099 / 2.274 / 1.228 (56.40 /
54.48 / 52.23 dB); libx265 (seat 7) GX011627 1.540 / 0.800 / 0.344 and GX011610 1.795 / 0.874 /
0.385, over the targets; NVENC without the ceiling (seat 7, the round-9 defect) 0.356 / 0.350 /
0.338 at a flat 35.82 dB. 10-bit costs 0-1 % over 8-bit at the same value.

### 7.2 `QUALITY_RATIO` (Q13; `jobs.disk_space` is WP3.13's file, not changed here)

Output FILE size over source file size; the constant is High 1.0 / Standard 0.5 / Draft 0.25
(times `MARGIN` 1.25; doubled for 10-bit). Measured at the ruled values:

- **Busy 4K** (GX011627): file to file from the floor row, Standard NVENC 8-bit 0.495, NVENC
  10-bit 0.498, libx265 0.486. High and Draft from the video-rate ratios in 7.1 (on this clip the
  file ratio ran within about 1 % of the video-rate ratio in every measured row): libx265 about 1.07
  / 0.25; NVENC about 0.93 / 0.26 (Draft ceiling-bound; cq 30 was not run under its own ceiling).
- **Calm** (GX011610, 5.15 Mb/s camera): from the video-rate ratios, libx265 about 1.19 / 0.54 /
  0.28 and NVENC about 2.65 / 1.57 / 0.94 (seat 8's calm file ratios ran 1-4 % under the
  video-rate ratios: audio and telemetry are a larger share). GX011625 (calm 4K, 6.58 Mb/s), NVENC
  Standard file to file: 1.264.
- **10-bit:** 0-1 % over 8-bit (NVENC Standard 0.498 against 0.495), not double.

The busy figures sit near the constant; calm footage runs up to 2.65 x the source at High, over
1.0 x 1.25. The orchestrator or WP3.14 updates the constant; DR-48's disposition is section 9's.

### 7.3 The export FLOOR row (Q11; exclusive, best effort)

Window CHARC `a2f398778e3a8c5c`, run 2026-10-27 01:09:42Z to 02:02:44Z on `e04a7cb`, alone on
the host (11.4 GB free memory before; the idle background processes recorded as strays when
busy). `uv run python tools/video_io_bench.py floor --dry-run --config <scratch>` then `floor
--config <scratch>`, exit 0; record `io-bench-floor-20261027T010942Z.json` under the worktree's
`work\wp3.10\bench\` (not committed). Every run decodes with CUDA (WP3.9 `frames`) at Standard.

| Run | Frames | s/frame | stream s/frame | min/min | per frame median / p90 / max | first frame s | peak tree RSS | peak GPU memory (device) | NVENC proof |
|---|---|---|---|---|---|---|---|---|---|
| GX011627 NVENC 8-bit (1/3) | 681 | 0.1540 | 0.1508 | 4.61 | 0.149 / 0.165 / 0.202 | 0.580 | 2044 MiB | 1083 MiB | tied |
| GX011627 NVENC 8-bit (2/3) | 681 | 0.1553 | 0.1529 | 4.65 | 0.151 / 0.171 / 0.197 | 0.459 | 2046 MiB | 1083 MiB | tied |
| GX011627 NVENC 8-bit (3/3) | 681 | 0.1555 | 0.1531 | 4.66 | 0.151 / 0.169 / 0.202 | 0.447 | 2048 MiB | 1083 MiB | tied |
| GX011625 NVENC 8-bit | 14,938 | 0.1552 | 0.1549 | 4.65 | 0.154 / 0.172 / 0.304 | 0.460 | 2065 MiB | 1083 MiB | tied |
| GX011627 libx265 8-bit | 681 | 0.2792 | 0.2736 | 8.37 | 0.270 / 0.342 / 0.432 | 0.476 | 3519 MiB | 611 MiB (decoder only) | none (no NVENC) |
| GX011627 NVENC 10-bit | 681 | 0.1742 | 0.1719 | 5.22 | 0.170 / 0.188 / 0.240 | 0.467 | 2401 MiB | 1375 MiB | tied |

`s/frame` = probe + `open` + the frame stream + `close`, over the frames; the strays pauses
(2.2-3.9 s each, every 300 frames) are kept out. Stages on GX011627 NVENC: probe 0.64-0.71 s,
`open` 0.34-0.86 s, `close` 0.59-0.63 s (libx265 2.85 s). Peak RSS members: Python 348-369 MiB,
the decoder's FFmpeg about 920 MiB, the encoder's 776-784 MiB (NVENC 8-bit), 1112 MiB (10-bit),
2233 MiB (libx265). Conditions: GPU 56-62 C, SM clock up to 1980 MHz under load, clock-event reasons
0x1 and 0x24 (0x24 also at idle before the first run); CPU 4001 MHz and 1.8-9.4 % total load
before and after every run. Strays: only `System` (25-34 % of one logical CPU) in most windows
and `SearchProtocolHost.exe` (43 %) once (NVENC 10-bit, first window).

**Against D106 at 4K:** WP3.4's c3 core takes 0.4392 s/frame of D106's 0.834, leaving about
0.395. The floor at NVENC 8-bit Standard is 0.154-0.156 s/frame (GX011627 x 3 and the full
14,938 frames of GX011625): it FITS, with about 0.24 s/frame to spare (sum 0.593-0.595 s/frame).
NVENC 10-bit (0.174, sum 0.613) and libx265 (0.279, sum 0.718) fit too. The sum is an estimate:
the core and the floor were timed apart, decode and encode run in their own FFmpeg processes and
may overlap with the core or contend with it for the GPU; the end-to-end row is WP3.14's (V16).

**After each strays pause** (raw `per_frame_s`, 59 pauses, 49 of them on GX011625): only the
first frame runs fast, and it is the one already set apart (`after_pause_frames`). It averaged
0.88-0.94 x the run's median on NVENC and 0.54 x on libx265; from the second frame on, the mean
is 0.91-1.09 x the median, inside the run's spread. Counting frames below the run's p10 from the
pause on: 0 or 1 at 57 pauses and 2 at 2 (GX011625; the second just under p10). Setting one frame
apart is enough; the figures above stand.

## 8. Debt and decided items

- **AD-22 / DR-15:** implemented; proven on synthetic libx264/libx265 B-frame clips (and the
  Edits compilation in round 0, by boxes); the iPhone leg stays OPEN (Q7).
- **DR-17:** CLOSED on `vid-untagged` (tagged, warned, both depths).
- **AD-12:** verified on footage and RULED (section 7.1).
- **DR-18:** (1)-(4) CLOSED by the instrument (section 4). (1) CLOSED on `tied`: every NVENC run
  in seat 7's and seat 8's footage windows and in the floor row was tied (GPU UUID, FFmpeg PID,
  encode window); a run the proof cannot tie carries the reason.
- **DR-48** (WP3.13's disk estimate): measured here (7.2); disposition ruled by CHARC (section 9).
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
- **WP3.14:** the sink deletes `out_path` on every failure from the moment it tries to start
  FFmpeg: FFmpeg that cannot be started, and any failure in `open` after that, in `write` or in
  `close`. A REFUSAL at `open` (an option, the source or the provenance refused before FFmpeg is
  started) leaves `out_path` as it was: the caller's `abort` deletes it (it was recorded first),
  or `SafeWrite` does. `SafeWrite.abort` tolerates the missing temporary. A cancel from another thread should call `abort` (it kills FFmpeg; the writing thread
  then sees `encoder_failed`).
- **WP4.3:** FFmpeg is started with `subprocess.Popen` directly; the shared CREATE_NO_WINDOW spawn
  helper (AD-23 extended) is WP4.3's.
- **`QUALITY_RATIO`** (`jobs.disk_space`, Q13): the measured ratios are in 7.2; the orchestrator
  or WP3.14 updates the constant, not this package.
- **The disk-estimate risk (DR-48):** a source-relative estimate under-states the output on calm,
  low-bit-rate footage (NVENC High 2.65 x a 5.15 Mb/s camera against 1.0 x 1.25), so D87's
  refusal could pass a write that fills the disk. CHARC ruled DR-48's disposition in the debt
  register on main (`759f0d0`) for WP3.14's brief: the larger of the source-relative estimate and
  the AD-12 ceiling for the level times the duration, times `MARGIN`, both encoders, without the
  10-bit doubling. No code of this package changes.
- **The NVENC ceiling out of envelope (dispatcher-ACCEPTED):** a ceiling above every Main-tier cap
  that holds the picture is cut to the highest such cap (6.2's 240 Mb/s); a picture no HEVC level
  holds is refused at `open`, by name. Neither occurs for GoPro or iPhone footage.
- **The level warning, every encoder:** `close` reads the level the output signals and warns when
  it is above an HEVC source's level or tier, libx265 outputs included (libx265 has no ceiling;
  GX011627's libx265 outputs signalled 5.0 Main, under the source's 6.0 Main).
- **Variable frame rate:** the pixel rate behind the NVENC ceiling uses the source's AVERAGE frame
  rate, so on a variable-rate source a stretch above the average gets the average's ceiling.
- **Out of envelope, not refused:** data tracks other than the HERO13 set (for example an iPhone
  `mebx` track) and audio codecs MP4 cannot hold are passed to the muxer, which fails
  (`encoder_failed`, with FFmpeg's message).
- **`FFREPORT` and the probe (banked, not this package's):** WP3.7's `probe.py` `_run_ffprobe`
  (`cc28699`) still inherits `FFREPORT`, so a probe run with it set writes an ffprobe report file
  into the working folder; the sink's own processes do not. The fix (`env=` from a shared helper)
  is WP3.7's file.
- **Movie duration on a coarse movie timescale:** the `mvhd` row is exact, so a source whose movie
  timescale cannot represent its presentation exactly reads DIFFERENT against an output whose
  timescale can. OBSERVED on the Edits compilation (movie timescale 1000; seat 7): `mvhd` and
  the audio entry of the edit-list effect, source 180.079 s (180079/1000) against output
  180.078209 s (7941449/44100). The output keeps the audio's exact length; the source's value is
  that length rounded UP to its 1 ms tick (0.79 ms, under one tick); the video effect is exact.
  This is the accepted "rounded UP" limitation; no code change (a later option: `-movie_timescale`
  set to the source's). iPhone (600) stays untested (DR-15's iPhone leg). GoPro (movie timescale
  30000) and every synthetic and fixture sample compare exactly.
- Only whole-clip exports are verified for the start offset: the sink copies audio and data whole,
  so an export that starts after the source's first frame is outside this package.
- **The floor-row instrument's limits:** RSS sampled (0.25 s nominal; the actual gaps in
  `gaps_s`); graphics memory device-wide (`memory.used`; per-process reads 0 or N/A under WDDM);
  the instrument loads the machine a little (`nvidia-smi` each second in its own thread, `pmon`
  each 0.5 s on NVENC, a strays reading of 2.2-3.9 s every 300 frames with the loop paused and
  the pause kept out of the figures); no CPU temperature on Windows; a process that starts and
  exits between two strays readings is not seen; only the first frame after a pause is set apart
  (enough, 7.3). Several NVIDIA GPUs (R5 #10, banked out of envelope): the GPU reading takes the
  first `nvidia-smi` line; adding `index` and `uuid` to the query would show a mismatch (noted,
  not built).
- **Pause and strays semantics (option B):** the `StrayWatch` is primed before the run, read after
  every `--strays-every` frames and once more right after `close` (first in the `finally`, also on
  a failure). A strays window covers the frames between two readings; the first also holds the
  setup before the probe, the last the rest of the stream and `close`. Each in-loop reading pauses
  the loop; the pause (`strays.pauses_s`, `stages_s.strays_pauses`) is kept out of every interval,
  stage and rate, and the frame right after it is set apart (`after_pause_frames`, `after_pause`),
  as the first frame is. The telemetry runs two threads (RSS, GPU), each on its own schedule with
  every sample timed; `offsets_s` places the telemetry's zero and the end of the strays priming on
  the run's clock.
- **`close` does not compare audio payload bytes (Reviewer B pass 1 #3, limit):** it checks every
  audio stream's packet pts and count, not the packet bytes. Audio is stream-copied (`-c:a copy`),
  so a payload change needs a command change; the V4 instrument (`tools/video_fidelity.py`)
  hashes the payloads.
- **A blocking stdin write has no deadline (Reviewer B pass 1 #4, limit; DR-28 (4)):** if a live
  FFmpeg stops reading, `write` (or the sentinel in `close`) blocks. The recovery is `abort` from
  another thread: it kills FFmpeg, the pipe breaks, and the writing thread sees `encoder_failed`.
- **`abort` cannot ensure FFmpeg ended if the kill itself fails (Reviewer B pass 1 #5, limit):**
  it never raises, so a failed kill or a wait past 30 s leaves FFmpeg running and possibly
  `out_path` held; a second `abort` repeats the cleanup. On Windows the kill of the sink's own
  child fails only on access denial.
- **`close` does not compare an audio track's edit-list duration or its last packet's duration
  (Reviewer B pass 2 #2, limit):** an audio tail trim shorter than one packet passes `close`.
  Non-video edit lists "as written" are a BEST-EFFORT row of the V4 instrument by design (round
  0); the audio start and `media_time` effect IS checked, through the packet pts (pass-1 #2
  reproduction).
- **Rotation is compared as an integer (Reviewer B pass 2 #4, limit):** `close` truncates the
  output's display rotation to an integer; the sink writes only the probe's integer rotation
  (`-display_rotation`), so a fractional rotation cannot come from it.
- **The floor row subtracts the strays pauses (Reviewer B pass 1 #9):** decode and encode go on
  during a pause, so subtracting the whole pause biases the floor low by the work done in it; the
  measured bound is about one frame per pause (7.3: only the first frame after a pause runs fast,
  and it is set apart): the time it saves is about 0.02-0.12 s per pause, at most about 0.0004
  s/frame over the 300 frames between two pauses.
- **Process note:** one run of the units module during the dispatcher's suite made sub-second
  FFmpeg reads (a hold breach in seat 8; noted, no harm).
