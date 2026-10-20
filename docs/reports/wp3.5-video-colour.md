# WP3.5 -- Video colour handling and chroma resampling

Module `clearwater.color` (`src/clearwater/color/`: `swscale.py`, `samples.py`). Spec v0.5.4 6.5,
D39, D54, D55, D76, D114; AD-10, AD-11, AD-19. FFmpeg 9.0.2 (gyan build). Tests
`tests/test_color_*.py`. Ledger `docs/proofs/wp3.5-ledger.md`.

## Claims

1. **The argument pair is inverse by construction.** `decode_filter(stream)` and
   `encode_filter(stream, bit_depth=)` are built from the same three values of the stream's
   resolved colour description (matrix, range, chroma siting), with AD-10's flags
   `bicubic+accurate_rnd+full_chroma_int+bitexact` in both. No primaries, transfer or gamut
   option is ever produced (6.5). Evidence: `test_color_swscale.py` (exact strings per WP2.3
   sample; 16 planted wrong arguments each caught by the pair check).
2. **Samples convert exactly.** `planes_to_rgb` / `rgb_to_planes` take FFmpeg's planar G, B, R
   frames (`gbrp`, `gbrp10le`) to IF-1 float32 and back; every 8- and 10-bit code round-trips
   exactly; quantisation (clip, scale, `numpy.rint`) happens only on the way out (D39).
   Evidence: `test_color_samples.py`.
3. **Decode is right, not merely inverse.** Flat colours whose Y'CbCr codes are computed from the
   matrix definition decode to within 1.0/255 (8-bit) and 0.73/255 (10-bit), for BT.709 and
   BT.601, limited and full, at 8 and 10 bits (`yuvj420p` for the 8-bit BT.709 full case, too).
   Planted: range misread 12-20 (limited read as full 19-20, full read as limited 12);
   BT.601/BT.709 swapped 15-17; `accurate_rnd` dropped 2.0 (8-bit limited); plane order 100+.
   (`test_color_roundtrip.py`.)
4. **D54 is consumed, not redone (DR-20 item 1).** `vid-untagged` probes to BT.709 / limited,
   `assumed=True`, one `missing_tags` fault; its decode/encode arguments say BT.709 and `tv`; a
   `yuvj` stream with no tags at all is full range with no range in the warning and decodes as
   `pc`. The name table passes the assumed values through for WP3.10 (DR-17).
5. **The pair through 8-bit 4:2:0 Y'CbCr (V9, decoded-RGB side, encoder excluded)** is a
   characterisation test (CHARC ruling on the V9 bound, 2026-10-20; AD-11 carries a one-line
   clarification on main, `2ce4266`). AD-11's 2/255 max and 0.2/255 mean bind the RGB-side legs
   (the `samples.py` round trip and the decoded RGB before the encoder), which are exact. They
   are not attainable for the pair itself: with a 4:4:4 intermediate (no chroma resampling)
   GX011627 gives max 2 and mean 0.615/255, so quantisation alone sets the floor. The pair's
   regression bounds are GX011627, first 30 frames: mean <= 1.0/255 and p99.9 <= 4/255; the
   `testsrc2` samples: mean <= 3/255, max reported and not asserted. The ruling supersedes the
   brief's task 4 wording on the bound (recorded in the ledger).

## Public API

`swscale`: `decode_filter`, `decode_pix_fmt`, `encode_filter(stream, *, bit_depth)`,
`encode_pix_fmt`, `rgb_pix_fmt(bit_depth)`, `ffmpeg_color_names(color)` (keys `color_primaries`,
`color_trc`, `colorspace`, `color_range`; unknown values omitted), `ColorError`, `SWSCALE_FLAGS`,
`SUPPORTED_PIX_FMTS`, `SUPPORTED_MATRICES`, `DEFAULT_SITING`. `samples`: `planes_to_rgb`,
`rgb_to_planes`, `rgb_frame_bytes`. Supported: `yuv420p`, `yuvj420p`, `yuv420p10le`; matrix
BT.709 or BT.601; any named siting (`unknown` -> `left`). Refused by name (`ColorError`): other
pixel formats, other matrices (including the `unknown` the probe leaves on an HLG/PQ file),
a bit depth that disagrees between pixel format, stream and description, a siting value FFmpeg does not name, a range other than full or limited, an output depth other than the source's (or 10 for 8-bit, D76), and `yuvj420p` with a
limited range (swscale reads `yuvj` as full whatever `in_range` says, so decode and encode would
disagree; measured: flat colours on a yuvj420p stream decode identically with `in_range=tv` or `pc`).

## Measured round trip (1/255 units, RGB max / mean / p99.9 / share over 2/255)

| Row | Frames | Max | Mean | p99.9 | >2 | Bound asserted |
|---|---|---|---|---|---|---|
| GX011627 (4K, yuvj420p, BT.709 full) | 30 | 17 | 0.687 | 3.0 | 0.72 % | mean <= 1.0, p99.9 <= 4 |
| vid-hevc8-bt709-full | 45 | 83 | 2.023 | - | 19.96 % | mean <= 3 |
| vid-hevc10 | 45 | 76.3 | 1.455 | - | 13.53 % | mean <= 3 |
| vid-untagged | 45 | 98 | 1.941 | - | 15.03 % | mean <= 3 |
| generated BT.601 | 45 | 97 | 1.817 | - | 14.94 % | mean <= 3 |
| D76: vid-hevc8-bt709-full, 10-bit out | 45 | 65.2 | 1.587 | - | 16.60 % | mean <= 3 |

The synthetic samples are `testsrc2` (saturated bars and text), whose chroma edges set the max.
The p99.9 figure is the upper edge of a 1/16 bin. The regression rows (rotated, vfr, truncated,
12 frames each) are asserted against the same synthetic bound.

## Planted defects through the round trip (bound and measured figure per defect)

The defect must exceed the bound on at least one of mean or p99.9; the margin is the figure
beside the bound. Real footage row (GX011627, 30 frames; bounds mean 1.0, p99.9 4):

| Defect | Mean | p99.9 | Exceeds by |
|---|---|---|---|
| product (no defect) | 0.687 | 3.0 | within both |
| encode range written the wrong way | 5.32 | 20 | mean 5.3x, p99.9 5x |
| encode matrix BT.601 for BT.709 | 2.98 | 10 | mean 3.0x, p99.9 2.5x |
| `accurate_rnd` dropped in both halves | 1.14 | 5 | mean 1.14x, p99.9 1.25x |
| `accurate_rnd` dropped in the first decode only | 0.80 | 6 | p99.9 1.5x |
| siting `center` in the encode | 0.71 | 5 | p99.9 1.25x |
| siting `topleft` in the encode | 0.74 | 5 | p99.9 1.25x |

`testsrc2` rows (bound: mean 3):

| Defect (encode side) | hevc8 | hevc10 | untagged | BT.601 clip |
|---|---|---|---|---|
| product | 2.02 | 1.46 | 1.94 | 1.82 |
| range written the wrong way | 13.37 | 5.65 | 5.70 | - |
| matrix swapped | 8.76 | 7.46 | 7.85 | 7.85 (BT.709 for BT.601) |

On the synthetic rows `accurate_rnd` (2.79-2.84 in both halves) and siting (2.3-2.5) stay under
the bound of 3; they are caught on the real-footage row above, by the flat-colour decode truth
(`accurate_rnd`, 2.0 against 1.0) and at argument level. `out_range` has no pixel effect for an
RGB destination (swscale ignores it) and is argument-level only.

## Limits

Declared envelope only (4:2:0 SDR, 8/10-bit, BT.709/BT.601, Windows 11, FFmpeg 9.0.2). No timing
figure. Footage row reads `GX011627` read-only (first 30 frames, about 3.5 minutes for the test with its six
planted variants). The module does not read primaries or transfer for the arguments.

## For other packages

- WP3.9: frame size `rgb_frame_bytes`; `decode_filter` serves software and `-hwaccel cuda`.
- WP3.10: the encoder's input RGB is `rgb_pix_fmt(output depth)`; the float frame is quantised at
  the OUTPUT depth (`rgb_to_planes(..., bit_depth=10)` for D76); NVENC wants `p010le` for 10-bit
  (convert from `yuv420p10le` there); tags from `ffmpeg_color_names` plus `color.assumed`.
- WP3.7's owner: a BT.601 stream tagged `smpte170m` for primaries resolves primaries as
  "unexpected" (`_PRIMARIES` knows bt709 and smpte432), so `assumed=True` and a `missing_tags`
  warning appear although the matrix is understood. Consumer note only; `io/video` untouched.
