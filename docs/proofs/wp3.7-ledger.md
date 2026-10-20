# WP3.7 ledger -- video probe and input validation

Cell: `implementer-sonnet-high`, worktree `.worktrees/wp3.7`, branch `wp3.7`, base `9735282`.
Tier STRONG. Brief `docs/briefs/wp3.7-brief.md` (FINAL; rulings 7.1-7.8, 7.3 amended).

## Round 0 -- mapping tables (no product code yet)

Grounded on the WP2.3 manifest (`tests/fixtures/manifest.json`), the sample files probed with
ffprobe 9.0.2 on this machine, and WP1.5 section 3.

### (c) The ffprobe command lines (all `-v error`, argv lists, no shell, timeout 120 s)

1. Container and streams: `ffprobe -v error -of json -show_format -show_streams <path>`.
   `side_data_list` (display matrix) is part of `-show_streams`; checked on `rotated.mp4`.
2. Video packets: `ffprobe -v error -of json -select_streams v:0 -show_entries
   packet=pts,duration,flags <path>`. Integer ticks only (`pts` is an integer in the JSON; `flags`
   carries `K` keyframe and `C` corrupt). No decode. Gives the VFR test, the readable packet count
   and the last keyframe.
3. Tail decode, only when the file is not already `truncated` (bounded to the last GOP):
   `ffprobe -v error -of json -select_streams v:0 -read_intervals <t_kf>% -show_entries
   frame=pts <path>`, where `<t_kf>` is the last keyframe's pts as a decimal rounded UP at the
   sixth place (a seek position only; no reported time is ever parsed from a decimal).
   stderr and the frame count are inspected, see `unreadable_tail`.

`ffprobe` is found by one locator in `probe.py` (`shutil.which`; absent: `VideoProbeError` with
kind `"missing_tool"` and an install hint). It also serves `ffmpeg` for WP3.9/3.10 (ruling 7.8);
it lives in `probe.py` because no separate locator file is in the brief's owned list.

Verified live: `rotated.mp4` side data `rotation: 90` with matrix `[0 -65536; 65536 0]`;
`truncated.mp4` prints `stream 0, offset 0x86a1: partial file` on stderr under `-v error`, lists
25 video packets (the 25th flagged `C`, ending exactly at EOF) against `nb_frames` 45; a copy of
`hevc8-bt709-full.mp4` with the last packet's payload overwritten decodes 44 of 45 frames and
prints `[hevc @ ...] alignment_bit_equal_to_one=0` under command 3, while the intact file prints
nothing and yields all frames of the interval.

### (a) Colour: ffprobe values to IF-1 (D54)

Absent keys, `unknown` and `unspecified` all count as MISSING. A recognised value maps; a present
but unrecognised value is UNEXPECTED. Each field is resolved on its own: missing or unexpected
takes its D54 value (BT.709 / BT.709 / BT.709 / limited), `assumed=True` if any field did, and
ONE `missing_tags` warning names the defaulted fields and says which were missing and which
unexpected.

| Field | ffprobe `color_*` value | IF-1 value |
|---|---|---|
| primaries | `bt709` | `bt709` |
| primaries | `smpte432` | `display-p3` |
| primaries | missing, or anything else (`bt2020`, `bt470bg`, `smpte170m`, `smpte431`, ...) | `bt709` (D54, assumed) |
| transfer | `bt709` | `bt709` |
| transfer | `iec61966-2-1` | `srgb` |
| transfer | `arib-std-b67` | HLG: refuse fault, `transfer="unknown"`, `assumed=False` (ruling 7.6) |
| transfer | `smpte2084` | PQ: same |
| transfer | missing, or anything else (`smpte170m`, `linear`, `gamma22`, `smpte240m`, log curves) | `bt709` (D54, assumed) |
| matrix | `bt709` | `bt709` |
| matrix | `smpte170m`, `bt470bg` | `bt601` |
| matrix | `gbr` | `identity` |
| matrix | missing, or anything else (`bt2020nc`, `bt2020c`, `smpte240m`, `ycgco`, `fcc`) | `bt709` (D54, assumed) |
| range | `pc` | `full` |
| range | `tv` | `limited` |
| range | missing and `pix_fmt` starts `yuvj` | `full`, NOT assumed, no `missing_tags` for range (ruling 7.3 amended) |
| range | missing, any other `pix_fmt` | `limited` (D54, assumed) |

`bit_depth` comes from `pix_fmt` (`yuv420p`/`yuvj420p` = 8; `yuv420p10le` = 10): regex
`^yuvj?4\d\dp(\d\d)?(le|be)?$`; no digits = 8. 8 and 10 only; any other pix_fmt or depth raises
`VideoProbeError` kind `"unsupported"` (5.2 names 8 and 10). 4:2:0, 4:2:2 and 4:4:4 are all passed
through; chroma handling is WP3.9/3.5's.

HLG/PQ result: the other colour fields carry what the tags say where the vocabulary has it, else
`"unknown"` (for the manifest samples: primaries `unknown`, matrix `unknown`, transfer `unknown`,
range `limited`, `assumed=False`); the `refuse` fault is the signal and the file is never decoded.

Resolved samples (expected): `hevc8-bt709-full`, `rotated`, `vfr`, `truncated` = bt709/bt709/bt709
full, not assumed; `hevc10` = bt709 limited, not assumed; `untagged` (H.264, `pix_fmt yuv420p`, no
colour keys) = bt709/bt709/bt709 limited, `assumed=True`, one `missing_tags`.

Other `VideoStreamInfo` fields: `codec` = `codec_name` (accepted `hevc`, `h264`); `chroma_siting` =
`chroma_location` as is, missing/`unspecified` = `"unknown"`; `frame_rate` = `avg_frame_rate`
as a `Fraction` of the rational string (`0/0` falls back to `(n-1)` frames over the pts span);
`time_base` = `Fraction` of the rational string; `nb_frames` = int or None (`N/A`, absent);
`rotation` below; `width`/`height` = the stream's `width`/`height` (the display size ffprobe
reports; for the manifest samples 320x180, with `coded_height` 184 ignored).

Container and codec gate (ruling 7.2): `format_name` must contain `mp4` or `mov` (ffprobe returns
`mov,mp4,m4a,3gp,3g2,mj2` for both) and the video codec be `hevc` or `h264`; else
`VideoProbeError` kind `"unsupported"`. More than one video stream (out of envelope): the first is
used. No video stream: `"unsupported"`.

Rotation (AD-20, counter-clockwise positive): the video stream's display-matrix side data
`rotation`, as an integer, normalised `% 360`; a value that is not a multiple of 90 rounds to the
nearest multiple of 90 (QUESTION Q1 below). No side data: 0. The mirrored case of a matrix
(negative determinant) is not representable in IF-5 and is ignored (out of envelope).

### (b) Faults: detection rule and severity

| Kind | Severity | Rule | Message (user-readable, G10, ASCII) |
|---|---|---|---|
| `hlg` | refuse | video `color_transfer == "arib-std-b67"` | "This video uses HLG HDR, which Clearwater does not support. Re-record in standard (SDR) mode." |
| `pq` | refuse | video `color_transfer == "smpte2084"` | same with "PQ (HDR10)" |
| `missing_tags` | warn | any of primaries / transfer / matrix / range defaulted per table (a); also raised by the GP-Log "no transfer tag on a Protune clip" case | "The video's colour tags are missing (or unexpected): <fields>. Clearwater assumes BT.709, limited range." (field list and defaults are named) |
| `gp_log` | warn | `GoProInfo` present and (`color_profile` non-empty and not in `NATURAL`/`FLAT`/`VIBRANT`, compared upper-case) OR (`protune is True` and the transfer tag is missing) | "This looks like a GoPro Log / Protune clip (<reason>). Clearwater does not convert it; the result may look wrong." |
| `truncated` | warn | `-show_packets` run (command 2) satisfies ANY: stderr names `partial file`; the readable video packet count is below `nb_frames`; the last packet carries the `C` flag | "The file is cut short: only <n> of <m> frames are readable. Clearwater will process up to the readable part." |
| `unreadable_tail` | warn | not `truncated`, and the bounded tail decode (command 3) writes any stderr line, or yields fewer frames than packets from the last keyframe on | "The end of the file cannot be decoded. Clearwater will process up to the last readable frame." |
| `sidecar` | exclude | extension `.lrv`/`.thm` (case-insensitive); produced by the filter, never by `probe` | "<name> is a camera proxy/thumbnail file and is not used as an input." |

`truncated` and `unreadable_tail` are mutually exclusive in a result (a cut file's tail is
`truncated`). Fault order in the tuple: hlg/pq, missing_tags, gp_log, truncated/unreadable_tail.
Intact manifest samples (hevc8, hevc10, rotated, vfr, untagged beyond its `missing_tags`) must
yield no `truncated`/`unreadable_tail`: the truncated sample is the only one, and the corrupted-
last-packet copy built in the test proves `unreadable_tail`.

`probe` on a `.lrv`/`.thm` path raises `VideoProbeError` kind `"sidecar"` without running ffprobe
(ruling 7.7). Unreadable file (ffprobe nonzero exit, empty or non-JSON output, no streams, no
`moov`): `VideoProbeError` kind `"unreadable"`, message "cannot be read at all" (5.4).
`VideoProbeError` is a single class in `io.video`, with a `kind` attribute (`unreadable`,
`unsupported`, `sidecar`, `missing_tool`).

### Timing rules (exact Fractions, no float)

- `time_base`, `avg_frame_rate`: `Fraction(str)` of the rational string. Every other time =
  integer ticks x a stream time base.
- `duration_s` = max over the video and audio streams of `duration_ts x time_base` (what
  ffprobe's `format.duration` is, minus its decimal rounding); fallback `(max pts + duration of
  that packet) x time_base` from command 2. Manifest: 45045/30000 = 3003/2000 s.
- `start_offset_s` = min over the video and audio streams of `start_pts x time_base`
  (ffprobe's `format.start_time`); 0 when no stream carries one.
- `AudioStreamInfo.start_s` = `start_pts x time_base`, 0 when absent.
- `EditEntry.segment_duration_s` = segment duration ticks / movie timescale (`mvhd`);
  `media_time_s` = media time ticks / media timescale (`mdhd` of the video trak), None for
  `media_time = -1`; `media_rate` = `Fraction(int32 media_rate, 65536)` (16.16 fixed).

### VFR rule (D95)

Sort the video packets' pts (presentation order, so B-frame reordering is irrelevant), take the
successive differences in integer ticks. CFR when there are zero or one difference value (every
step the same integer tick count); VFR otherwise. The LAST frame has no following frame, so its
own duration is NOT counted as a step (a differing last-sample duration alone does not flag VFR;
timing is preserved exactly either way). Fewer than 2 frames: CFR. Manifest: `vfr.mp4` steps
{1001, 2002} = VFR, `avg_frame_rate` 22500/1001; all others CFR with step 1001.

### (d) GPMF keys decoded (`gopro.py`, from `moov/udta/GPMF` only)

`FMWR` (type `c`) -> `firmware`; `PRTN` (type `c`, `Y`/`N`) -> `protune` (`Y` True, `N` False,
other None); `PTCL` (type `c`) -> `color_profile`. Strict KLV: 4-char key, type byte, size byte,
big-endian uint16 repeat; payload = size x repeat, padded to 4; every length checked against the
enclosing bound; nesting depth capped at 8; loop makes forward progress by >= 8 bytes. Type-0
items are STRUCTURAL: the walker enters them (WP1.5 found the keys in nested streams) but a leaf
is decoded only when its key is one of the three; every other leaf is skipped by its length, its
bytes never turned into text or numbers. First occurrence of each key wins. A malformed atom
gives `gopro=None` and a note (a `VideoProbeError`-free path: the note is carried as a module-
level logger warning, since `ProbeResult` has no notes field; QUESTION Q2). A file without a
`GPMF` atom gives `gopro=None`. Never touched: the `gpmd` track payload (the probe never reads
mdat), `ACCL GYRO GRAV CORI IORI GPS*`, `HDRV`, `BITR`, serial/identifier atoms.

`boxes.py` reads only `moov`: top-level boxes are walked by size (64-bit `largesize`, size 0 =
to end of file) without reading `mdat`; `moov` is read whole (cap 512 MiB); within it
`mvhd`, `trak/tkhd`, `trak/mdia/{mdhd,hdlr}`, `trak/edts/elst`, `udta/GPMF`. Child boxes are
bounds-checked against the parent, a box smaller than its header or past the parent ends the walk
with a `BoxError`, and the walk always advances.

### Open questions (answers assumed as written unless the dispatcher rules otherwise)

- **Q1.** Display matrix rotation that is not a multiple of 90 (or a mirrored matrix): IF-5 has
  no fault kind. Assumed: round to the nearest multiple of 90 and ignore a mirror (out of
  envelope). Alternative: refuse as `"unsupported"`.
- **Q2.** `ProbeResult` has no field for "GPMF atom malformed" (brief task 5: `gopro=None` "with a
  note"). Assumed: the note goes to a `logging` warning (message names the file, no atom bytes) and
  is returned nowhere; no fault is added (no FaultKind fits).
- **Q3.** `smpte170m`/`bt470bg` matrix maps to `bt601`; primaries `smpte170m`/`bt470bg` are treated
  as unexpected (assumed BT.709) rather than mapped, as IF-1 has no SD primaries value. Confirm.
- **Q4.** The brief's `truncated` sentence (sample table points past the end of the file) is
  implemented as "packet count below `nb_frames` / `C` flag / `partial file`" from ffprobe's own
  container walk, which is the same condition without a second sample-table parser. Confirm that
  this reading satisfies ruling 4.

### Round ledger

| Round | Counts (crit/major/minor) | In-env / out | NEW / REOPENED | Reverts | Fix type | Transport / CLI | Depth |
|---|---|---|---|---|---|---|---|
| 0 (mapping tables) | -- | -- | -- | -- | -- | -- | (dispatcher) |
