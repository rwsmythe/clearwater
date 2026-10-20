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
   BT.601, limited and full. Planted: range read as full 19-20; BT.601/BT.709 swapped 15-17;
   `accurate_rnd` dropped 2.0 (8-bit limited); plane order 100+. (`test_color_roundtrip.py`.)
4. **D54 is consumed, not redone (DR-20 item 1).** `vid-untagged` probes to BT.709 / limited,
   `assumed=True`, one `missing_tags` fault; its decode/encode arguments say BT.709 and `tv`; a
   `yuvj` stream with no tags at all is full range with no range in the warning and decodes as
   `pc`. The name table passes the assumed values through for WP3.10 (DR-17).
5. **The pair through 8-bit 4:2:0 Y'CbCr (V9, decoded-RGB side, encoder excluded)** is measured
   below. AD-11's 2/255 and 0.2/255 are met by the RGB-side legs (exact). They are not attainable
   for the pair itself: with a 4:4:4 intermediate (no chroma resampling) GX011627 gives max 2 and
   mean 0.615/255. The bounds asserted for the pair are measured regression bounds, pending the
   CHARC ruling on STOP 1 (ledger).

## Public API

`swscale`: `decode_filter`, `decode_pix_fmt`, `encode_filter(stream, *, bit_depth)`,
`encode_pix_fmt`, `rgb_pix_fmt(bit_depth)`, `ffmpeg_color_names(color)` (keys `color_primaries`,
`color_trc`, `colorspace`, `color_range`; unknown values omitted), `ColorError`, `SWSCALE_FLAGS`,
`SUPPORTED_PIX_FMTS`, `SUPPORTED_MATRICES`, `DEFAULT_SITING`. `samples`: `planes_to_rgb`,
`rgb_to_planes`, `rgb_frame_bytes`. Supported: `yuv420p`, `yuvj420p`, `yuv420p10le`; matrix
BT.709 or BT.601; any named siting (`unknown` -> `left`). Refused by name (`ColorError`): other
pixel formats, other matrices (including the `unknown` the probe leaves on an HLG/PQ file),
a bit depth that disagrees between pixel format, stream and description, an unknown siting or
range, an output depth other than the source's (or 10 for 8-bit, D76), and `yuvj420p` with a
limited range (swscale reads `yuvj` as full whatever `in_range` says, so decode and encode would
disagree; measured: flat colours on a yuvj420p stream decode identically with `in_range=tv` or `pc`).

## Measured round trip (1/255 units, RGB max / mean / share over 2/255)

| Row | Frames | Max | Mean | >2 |
|---|---|---|---|---|
| GX011627 (4K, yuvj420p, BT.709 full) | 30 | 17 | 0.687 | 0.72 % |
| vid-hevc8-bt709-full | 45 | 83 | 2.023 | 19.96 % |
| vid-hevc10 | 45 | 76.3 | 1.455 | 13.53 % |
| vid-untagged | 45 | 98 | 1.941 | 15.03 % |
| generated BT.601 | 45 | 97 | 1.817 | 14.94 % |
| D76: vid-hevc8-bt709-full, 10-bit out | 45 | 65.2 | 1.587 | 16.60 % |

The synthetic samples are `testsrc2` (saturated bars and text), whose chroma edges set the max.

## Planted defects through the round trip (mean, 1/255; product value in brackets)

| Defect (encode side unless said) | GX011627 | hevc8 | hevc10 | untagged |
|---|---|---|---|---|
| range written the wrong way | 5.32 (0.69) | 13.37 (2.02) | 5.65 (1.46) | 5.70 (1.94) |
| BT.601 for BT.709 | 2.98 | 8.76 | 7.46 | 7.85 |
| `accurate_rnd` dropped in both halves | not run | 2.79 | 1.46 (no effect) | 2.84 |
| siting `center` | 0.706, >2 = 1.67 % | 2.45 | 2.29 | 2.33 |

Siting and `out_range` cannot be seen reliably in the bound (siting moves the mean by 3-20 %;
swscale ignores `out_range` for an RGB destination) and are caught at argument level.

## Limits

Declared envelope only (4:2:0 SDR, 8/10-bit, BT.709/BT.601, Windows 11, FFmpeg 9.0.2). No timing
figure. Footage row reads `GX011627` read-only (first 30 frames, about 95 s for the test with its
three planted variants). The module does not read primaries or transfer for the arguments.

## For other packages

- WP3.9: frame size `rgb_frame_bytes`; `decode_filter` serves software and `-hwaccel cuda`.
- WP3.10: the encoder's input RGB is `rgb_pix_fmt(output depth)`; the float frame is quantised at
  the OUTPUT depth (`rgb_to_planes(..., bit_depth=10)` for D76); NVENC wants `p010le` for 10-bit
  (convert from `yuv420p10le` there); tags from `ffmpeg_color_names` plus `color.assumed`.
- WP3.7's owner: a BT.601 stream tagged `smpte170m` for primaries resolves primaries as
  "unexpected" (`_PRIMARIES` knows bt709 and smpte432), so `assumed=True` and a `missing_tags`
  warning appear although the matrix is understood. Consumer note only; `io/video` untouched.
