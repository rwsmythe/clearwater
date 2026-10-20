# WP3.5 ledger -- video colour handling and chroma resampling

Cell wp35-cell (implementer-sonnet-high), worktree `.worktrees/wp3.5`, base main `2c5540a`
(FFmpeg 9.0.2 gyan build). Brief `docs/briefs/wp3.5-brief.md` FINAL, CHARC rulings
`53b752a4d7fac4fc`.

## Round 0 -- read and table (no product code)

Read: IF-1 `interfaces/image.py`, IF-5 `interfaces/video.py`, `io/video/probe.py`
(`_resolve_color` 271-307, `_colour_faults` 434-456, the `chroma_siting` read 627-634,
`_PIX_FMT` 65, `_bit_depth` 188-198), AD-10 and AD-11 (`docs/decisions.md` 19-20), WP2.1S
report section 2 (the `decode_command` and rows), WP1.5 report section 4 (`yuvj420p` / `pc`
fed to NVENC as `yuv420p` + `-color_range pc`), `tools/prototype/clip.py` `decode_command`.
Worktree status at start: clean.

### Per-sample table (probed with `clearwater.io.video.probe`, measured, not copied)

All eight declare chroma siting `left` and 320x180. Flags F =
`bicubic+accurate_rnd+full_chroma_int+bitexact` (AD-10).

| Sample | pix_fmt | bit | matrix / range | assumed | faults | decode filter | encode filter (bit_depth = source) |
|---|---|---|---|---|---|---|---|
| vid-hevc8-bt709-full | yuvj420p | 8 | bt709 / full | no | none | `scale=in_color_matrix=bt709:in_range=pc:in_chroma_loc=left:out_range=pc:flags=F,format=gbrp` | `scale=in_range=pc:out_color_matrix=bt709:out_range=pc:out_chroma_loc=left:flags=F,format=yuv420p` |
| vid-hevc10 | yuv420p10le | 10 | bt709 / limited | no | none | same with `in_range=tv`, `format=gbrp10le` | `out_range=tv`, `format=yuv420p10le` |
| vid-untagged | yuv420p | 8 | bt709 / limited | YES | `missing_tags` (warn) | `in_color_matrix=bt709:in_range=tv`, `format=gbrp` | `out_range=tv`, `format=yuv420p` |
| vid-rotated, vid-vfr, vid-truncated | yuvj420p | 8 | bt709 / full | no | (truncated: `truncated`) | as hevc8-bt709-full | as hevc8-bt709-full |
| vid-hlg, vid-pq | yuv420p10le | 10 | matrix unknown | no | `hlg` / `pq` (refuse) | never reach the module: `decode_filter` refuses matrix `unknown` by name | same |
| generated BT.601 (tmp_path, Q4) | yuv420p | 8 | bt601 / limited | likely yes (primaries `smpte170m` is "unexpected" to the probe) | `missing_tags` for primaries only | `in_color_matrix=smpte170m:in_range=tv` | `out_color_matrix=smpte170m:out_range=tv` |

The D76 path (8-bit source, 10-bit out): decode unchanged; the encoder takes `gbrp10le` (the
float frame is quantised at 10 bits) and `scale=in_range=<r>:out_color_matrix=..:out_range=..:
out_chroma_loc=left:flags=F,format=yuv420p10le`. A 10-bit source with an 8-bit output is
refused by name (that would truncate 10-bit data, spec 5.2).

### Proposed public API (`clearwater.color`; imports only `interfaces`, stdlib, NumPy)

`swscale.py`
- `SUPPORTED_PIX_FMTS`, `class ColorError(ValueError)` (named refusals, list the supported set)
- `decode_filter(stream: VideoStreamInfo) -> str`; `decode_pix_fmt(stream) -> str` (`gbrp` / `gbrp10le`)
- `encode_filter(stream, *, bit_depth: int) -> str`; `encode_pix_fmt(stream, *, bit_depth) -> str`
  (the Y'CbCr format: `yuvj` becomes the non-`j` form with range `pc`; 10-bit `yuv420p10le`)
- `rgb_pix_fmt(bit_depth: int) -> str` (the encoder's input RGB format; = `decode_pix_fmt` at the same depth)
- `ffmpeg_color_names(color: ColorDescription) -> Mapping[str, str]`: keys `color_primaries`,
  `color_trc`, `colorspace`, `color_range` (the names WP3.10 writes), unknown values omitted;
  `assumed` is not a key (WP3.10 reads `color.assumed`). Source values passed through unchanged.

`samples.py`
- `planes_to_rgb(data, *, width, height, bit_depth) -> NDArray[np.float32]` (G, B, R planes to (H, W, 3) RGB, `/ (2**n - 1)`)
- `rgb_to_planes(a, *, bit_depth) -> bytes` (clip to [0, 1], `* (2**n - 1)`, `numpy.rint`, uint8 / `<u2`, G, B, R)
- `rgb_frame_bytes(width, height, bit_depth) -> int`

### Answers to questions 2-6 (the rulings stand)

2. Rounding: clip, scale, `numpy.rint` (half to even); integer round trips exact at 8 and 10 bits.
3. Supported set `yuv420p`, `yuvj420p`, `yuv420p10le`; matrix must be `bt709` or `bt601`; anything else raises `ColorError` naming the supported set. `ColorDescription.transfer` and `.primaries` are never read by the arguments (6.5).
4. BT.601: the test generates a small clip in `tmp_path` with FFmpeg (`testsrc2`, libx264, explicit tags).
5. Footage row: one `footage` test on the first 30 frames of `GX011627` via `find_footage_file("GX011627")` (the stem carries no suffix).
6. Unknown siting is passed as `left` in both directions; the name table carries the assumed values through.

### STOP item 1 -- the V9 bound (AD-11) is not attainable by the brief's task 4 test (reproduced)

Task 4: decode to 8-bit planar RGB, through `samples.py`, encode to raw 8-bit Y'CbCr 4:2:0,
decode again, compare float RGB: max <= 2/255, mean <= 0.2/255. With exactly AD-10's flags and
this pair of arguments (scratch scripts, not committed; footage read-only via `find_footage_file`),
first frames only:

| Case | Intermediate | RGB max / mean (1/255 units) |
|---|---|---|
| GX011627 (4K, yuvj420p, bt709 full), 10 frames | yuv420p | 17 / 0.686 (p99.9 = 3, 0.28 % of samples > 2) |
| same | **yuv444p (no chroma resampling at all)** | **2 / 0.615** |
| same, bilinear or lanczos instead of bicubic (both directions) | yuv420p | 18 / 0.677 and 18 / 0.705 |
| vid-hevc8-bt709-full, 45 frames (testsrc2) | yuv420p | 83 / 2.02 |
| vid-hevc10, 45 frames (testsrc2) | yuv420p10le | 76.3 / 1.45 (in 1/255 units of the 10-bit data) |
| vid-untagged, 45 frames (testsrc2) | yuv420p | 98 / 1.94 |

Reading: (a) the **mean floor is quantisation, not resampling**: 8-bit RGB to 8-bit Y'CbCr and
back (no subsampling, so any arguments) gives mean 0.6/255; a mean of 0.2/255 cannot be met by
any swscale pair with an 8-bit Y'CbCr intermediate. (b) The **max** with 4:2:0 is set by content
with sharp saturated chroma edges (real footage 17, testsrc2 bars and text 76-98); the choice
of bicubic / bilinear / lanczos changes neither. (c) A range or matrix error, which AD-11 says
shows as >= 10/255, would still be visible in the MEAN of these runs (tens, against 0.6-2).
(d) Y'CbCr-side measure of the same pair (source planes vs re-encoded planes, 8-bit code
units, GX011627): Y max 21 mean 0.023; Cb max 14 mean 0.52; Cr max 14 mean 0.52.

Options (recommended first), for the dispatcher / CHARC (AD-11 is "tunable after WP5.1"):
1. **Split the test.** Keep AD-11's 2/255 and 0.2/255 where attainable: the `samples.py`
   float round trip and the decoded-RGB pre-encode side (quantisation only; exact at the
   integer level). For the swscale pair through 8-bit Y'CbCr, assert bounds set from this
   measurement and reported with it: on GX011627 first 30 frames mean <= 1.0/255 and p99.9 <=
   4/255; on the testsrc2 samples mean <= 3/255, max reported not asserted; planted
   range/matrix/accurate_rnd/siting defects must exceed these (checked at build; expected
   tens in the mean). Record the amendment proposal for AD-11 text (the V9 row).
2. Fix the intermediate at higher precision for the test only (decode and encode through
   `gbrp16le`/`yuv444p16le`): removes the quantisation floor but then does not test the real
   pair (8-bit planar RGB, 4:2:0).
3. Change the design (10-bit RGB planes for 8-bit sources): AD-10 territory, not this package.

No product code written; nothing outside the owned files changed.

### Other observations (not blocking)
- A BT.601 stream tagged `smpte170m` for all three fields resolves primaries `smpte170m` as
  "unexpected" (the probe's `_PRIMARIES` knows only bt709 and smpte432), so `assumed=True` and
  a `missing_tags` warning appear although the matrix is understood. That is WP3.7's D54
  per-field rule; flagged for the report only.
- `ColorDescription.bit_depth` and `VideoStreamInfo.bit_depth` are separate fields; the module
  reads the stream's and refuses a disagreement by name.

## Build (after the round-0 ruling) and cumulative Reviewer A ledger

Round-0 ruling (orchestrator, depth 90,237 / 23 turns): table accepted; STOP 1 is with CHARC;
build everything except the numeric bounds of the swscale-pair assertion, which are module
constants `PAIR_*` in `tests/test_color_roundtrip.py` marked pending the ruling. Built at
`91f94f4` (module), `675ef84` and `aa9acd0` (tests), report `docs/reports/wp3.5-video-colour.md`.
Decision taken in the build (new, flagged): `yuvj420p` with a limited range is refused by name,
because swscale reads a `yuvj` format as full range whatever `in_range` says (measured: flat
colours decode identically with `in_range=tv` and `pc`), so decode and encode would disagree.

| Round | Head | Crit | Major | Minor | In / out of envelope | New / reopened | Reverts | Fix type | Transport | Depth |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 3cadc37 | 0 | 0 | 7 | 3 in, 4 out | 7 new, 0 reopened | 0 | product (4 small guards) + tests + report, cleanup `3f27cd8`..`aa54804` and the bound change below | WSL codex, gpt-5.6-sol high, 141,016 tokens | (dispatcher fills) |

Round 1 transcript and adjudication: `C:\Users\rwsmy\clearwater-review-evidence\wp3.5\r1\`
(`review.txt`, `review.stderr.txt`, `adjudication.md`, `md5sums.txt`). Verdict
NO_NEW_CRITICAL_MAJOR; the 7 minors are fixed once in the cleanup, which opens no round.

## STOP 1 ruling (CHARC msg 229c326b43fb99f2, 2026-10-20 22:50Z, relayed by the orchestrator)

Option 1. V9 (AD-11 2/255 max, 0.2/255 mean) binds only the RGB-side legs: the `samples.py`
integer / float round trip and the decoded RGB before the encoder. The swscale pair through 8-bit
4:2:0 is a CHARACTERISATION test with regression bounds from the measurement: GX011627 first 30
frames mean <= 1.0/255 and p99.9 <= 4/255; testsrc2 samples mean <= 3/255, max reported, not
asserted. The planted range, matrix, accurate_rnd and siting defects must exceed the bounds by a
stated margin, and the report gives each defect's measured figure beside its bound. AD-11 is not
loosened; its V9 row carries a one-line clarification on main (`2ce4266`, not in this base). The
brief's task 4 wording is superseded by this ruling (no brief re-issue). Applied: constants
first `PAIR_MEAN_REAL = 1.0`, `PAIR_P999_REAL = 4.0`, `PAIR_MEAN_SYNTHETIC = 3.0`; superseded
the same day by the orchestrator's round-1 ruling with TIGHTER measured bounds, because a
synthetic mean of 3 lets accurate_rnd through (2.79-2.84 on testsrc2) and p99.9 4 on the footage
row catches the siting and accurate_rnd plants by only 1.25x (5 against 4): `PAIR_MEAN_REAL = 1.0`,
`PAIR_SHARE_OVER_2_REAL = 0.01`, `PAIR_MEAN_SYNTHETIC = 2.5`
(`tests/test_color_roundtrip.py`). The accurate_rnd defect also runs on the footage row (mean
1.14, share 7.35 % both halves; 0.80 and 4.07 % decode only). Per-defect margins are in the
report.

FINAL (orchestrator, after two crossed messages): the TIGHTER bounds stand (`0193b60`, head
`59e4281` content); `2a90ca3` that briefly restored the 1.0 / p99.9 4 / 3.0 constants was
reverted. The only addition since `59e4281` is the report's "Deliberate skip" section.

## Round-1 cleanup (all 7 minors, one pass, no new round)

1 truth cases added (10-bit BT.709 full, 10-bit BT.601 limited and full, 8-bit BT.709 full;
planted range misread now both ways); 2 `decode_file_frames` checks the FFmpeg exit status and a
short final frame, frame counts asserted in every row; 3 report sentence; 4 non-positive sizes and
empty arrays refused; 5 non-contiguous buffers refused; 6 `bt601` dropped from the primaries name
table; 7 rejected values formatted with `!a`. Fix type: product (4 small guards in `samples.py`
and `swscale.py`) plus tests and report.
