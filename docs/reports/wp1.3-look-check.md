# WP1.3 -- Look check pack, shallow part (Gate result 3)

Material for CP2: the WP1.1 prototype run over the owner's four shallow chapters, under both
compensation methods (three variants), with the whole-frame statistics it measured, and one
6 s clip corrected frame by frame without smoothing so that the flicker can be seen (spec 7.1).
The owner judges it (D103, informal bar); this report records what was run, what the numbers
were and what bound, and ends with the sheet the owner fills. **No correction is judged here.**

Conditions: 2026-10-15 (UTC), Windows 11 laptop, RTX 4070 Laptop GPU (prototype
`--device gpu`, CuPy), FFmpeg and ffprobe `9.0.2-full_build-www.gyan.dev`, branch `wp1.3`.
The stills were produced by `4c37dc3` and the flicker clip by `c51b020` (the commands in
section 2); a first pack built at `5833dff` was rebuilt after Reviewer A's round 1 (section 8),
and every statistic in it came out identical to the digit. Footage folder read only; every output is under
`C:\Users\rwsmy\clearwater\work\wp1.3\` (below, `work\wp1.3\`). The `SCUBA` subfolder was not
touched. Elapsed times are informal, not results: stills 233 s (24 frames, 3 variants each,
GPU), flicker clip 453 s.

## 1. Where things are

| Path under `work\wp1.3\` | Content |
|---|---|
| `index.html` | the page to open: head (variants, the `Params` defaults, the pending cases), then one row per frame, source and three variants as 960x540 thumbnails linking to the full 16-bit PNGs; under each variant the pair link and a one-line statistics summary |
| `frames\` | 96 PNGs: 24 sources `GX0116xx_<pts 0000.000>.png` and 72 corrected `<frame>-<variant>.png`, 16-bit RGB, 3840x2160 (3.4 GB) |
| `pairs\` | 72 side-by-side JPEGs (source left, corrected right, each half 1920x1080, quality 92) |
| `thumbs\` | 96 JPEGs (short side 540) |
| `frames.json` | per source frame: exact pts (ticks, time base, exact fraction), size, colour tags, the FFmpeg command |
| `statistics.json` | per frame and variant: the prototype's `CompensationInfo` and `WhiteBalanceInfo`, the `Params` it ran with, the N{} bounds, whether anything bound |
| `flicker\GX011627_unsmoothed.mp4`, `GX011627_source.mp4` | the two 180-frame clips (section 5) |
| `flicker\statistics.json`, `statistics.png` | all 180 frames' statistics, the encode checks, the commands; the plot |
| `flicker\source\`, `flicker\corrected\` | first, middle and last frame PNG of each set (the rest deleted after both MP4s were encoded and verified) |
| `logs\` | run logs, gate logs |

Counts: 24 frames (6 per chapter at 5 %, 23 %, 41 %, 59 %, 77 % and 95 % of its duration),
3 variants, 72 corrected PNGs, 72 pairs, 180 flicker frames.

## 2. Instrument

`tools/lookcheck/frames.py` (reused by WP1.4) and `tools/lookcheck/pack.py`.

**Command lines.** Stills (one FFmpeg process per frame; the clip excerpt is one process):

```
ffmpeg -nostdin -hide_banner -nostats -y -noautorotate -copyts -ss <pts - half a frame> -i <chapter>
  -map 0:v:0 -an -sn -dn
  -vf showinfo,scale=in_range=full:in_color_matrix=bt709:out_range=full:flags=accurate_rnd,format=rgb48be
  -frames:v <1 | 180> -fps_mode passthrough -pred none <scratch>\f%06d.png
```

The range and matrix are the stream's tags as `ffprobe` read them: **`yuvj420p`, BT.709 matrix,
full range (`pc`), BT.709 primaries and transfer, on all four chapters, nothing assumed**
(`frames.json` `tags.assumed` is empty on every frame). The PNGs carry no colour chunk:
FFmpeg's `cICP`, `cHRM`, `gAMA` and `pHYs` chunks are stripped (pixels untouched), so that a
source frame and its corrected twin, which the prototype writes with none, display the same
way in a colour-managed viewer; the tags are in `frames.json`. Chroma is upsampled by the scaler's
default method; `accurate_rnd` changes only rounding (without it limited-range YUV came out
about 2 levels of 255 too dark in the control clip). The frame is the first at or after the
requested time; its exact pts is listed by `ffprobe -show_frames` over a read interval
(`ffprobe` starts that interval at the keyframe before it, so the frames are filtered by
exact tick) and **confirmed by the decode: FFmpeg's `showinfo` pts of the frames it wrote must
equal the probe's list, or nothing is kept.** Frame names carry the pts rounded to ms; the exact
tick count is in `frames.json`.

**Range control (test 1).** `tests/test_lookcheck.py` builds lossless HEVC clips whose four
quadrants hold four known RGB colours, stored as 8-bit BT.709 YUV in the full range and in the
limited range (the clip's frames are flagged with the range they are tagged with, so FFmpeg
converts nothing before the encoder), and extracts both: both match the known RGB within 1
level of 255 (measured worst: full 0.88, limited 0.70 with `accurate_rnd`; 3.0 without it). The
planted failures fail by name: limited-range data re-tagged full by a bitstream filter
(`test_a_range_tag_that_lies_makes_the_control_fail`, error over 5 levels) and a correctly tagged
limited clip decoded with a wrong range argument
(`test_extraction_follows_the_tags_it_is_given`). **Limit found on the way:** for a `yuvj`
pixel format (what FFmpeg's HEVC decoder reports for a full-range stream, so all four chapters)
the scaler takes the range from the pixel format and ignores `in_range`; the decoder sets the
format from the same tag and the extraction refuses a stream whose format and tag disagree, so
the full-range result rests on the decoder, proven by the full-range clip, not on the argument.

**Output-path checks.** Mirrored from WP1.5's `check_output_path` / `write_checked` in
`tools/lookcheck/frames.py` (`OutputRoots`, mirrored not imported: WP1.5's messages say "spike
folder"), checked on the resolved path before every FFmpeg run (all scratch names, the output
MP4), every PNG, JPEG, JSON and HTML write and every delete: inside `work\wp1.3\`, outside the
footage folder, no existing target with more than one hard link. `FFREPORT` is removed from
every FFmpeg and ffprobe environment.

**Record shape for WP1.4** (`frames.FrameFile`, `record()`): `path`, `source`, `chapter`,
`pts_ticks` (exact, int), `time_base` (`Fraction`), `pts` (exact `Fraction` of seconds), `width`,
`height`, `tags` (`StreamTags`: `pix_fmt`, `color_range`, `color_space`, `color_transfer`,
`color_primaries`, `assumed`), `command`. `extract(video, timestamps_s, out_dir, *,
short_side=None, roots=None)` returns one per timestamp; `excerpt(video, start_s, duration_s,
out_dir, *, short_side=None, roots=None, naming="pts")` returns every frame with pts in
`[start, start + duration)` in order (`naming="index"` writes `<chapter>_f0000.png`... for an
FFmpeg image-sequence input). `roots` defaults to the local configuration's `working\wp1.3` and
footage folder; WP1.4 passes its own. `read_png16(path)` reads these PNGs at full 16-bit
precision (Pillow reads 16-bit RGB at 8-bit).

## 3. Variants, defaults, statistics

All three run at the `Params()` defaults (the page lists every field): `ancuti2018`
(`--method ancuti2018`, blue off), `ancuti2018-blue` (`--blue`), `c3` (`--method c3`). The
`statistics.json` record per frame and variant holds the prototype's `compensation` and
`white_balance` records unchanged (every field), the `Params` the pipeline ran with, and
`normalisation` (the N{} bounds), recomputed with the prototype's `normalisation_bounds` on the
white-balanced image on the same device because they are not part of `Result`. `bound` says
whether a gain cap, the white-balance clamp or a collapsed N{} (spread under 1e-6) bound.
"Red gain" and "blue gain" below are the white-balance applied gains (R and B).

| Frame | pts (ticks at 1/30000) | A red | A blue | A+blue red | A+blue blue | 3C red | 3C blue | N{} low..high (A) | cap use |
|---|---|---|---|---|---|---|---|---|---|
| GX011625_0024.925 | 747747 | 1.08 | 1.03 | 1.10 | 1.00 | 0.99 | 1.01 | -0.026..0.032 | 0.11 |
| GX011625_0114.648 | 3439436 | 1.19 | 0.97 | 1.20 | 0.96 | 1.00 | 1.00 | -0.009..0.011 | 0.35 |
| GX011625_0204.371 | 6131125 | 1.21 | 0.96 | 1.22 | 0.95 | 1.00 | 0.99 | -0.016..0.019 | 0.40 |
| GX011625_0294.094 | 8822814 | 1.29 | 0.89 | 1.29 | 0.89 | 1.01 | 0.97 | -0.032..0.047 | 0.58 |
| GX011625_0383.817 | 11514503 | 1.16 | 0.94 | 1.16 | 0.94 | 1.00 | 0.99 | -0.059..0.067 | 0.15 |
| GX011625_0473.540 | 14206192 | 1.15 | 0.95 | 1.15 | 0.95 | 1.00 | 0.99 | -0.008..0.009 | 0.14 |
| GX011626_0012.279 | 368368 | 1.14 | 0.95 | 1.14 | 0.95 | 1.00 | 0.99 | -0.128..0.148 | 0.12 |
| GX011626_0056.390 | 1691690 | 1.08 | 1.02 | 1.10 | 1.00 | 1.00 | 1.01 | -0.122..0.153 | 0.09 |
| GX011626_0100.500 | 3015012 | 1.10 | 0.96 | 1.10 | 0.96 | 1.00 | 0.99 | -0.137..0.170 | 0.07 |
| GX011626_0144.611 | 4338334 | 1.25 | 0.89 | 1.24 | 0.89 | 1.01 | 0.97 | -0.104..0.140 | 0.26 |
| GX011626_0188.722 | 5661656 | 1.32 | 0.82 | 1.31 | 0.84 | 1.03 | 0.95 | -0.037..0.050 | 0.32 |
| GX011626_0232.833 | 6984978 | 1.34 | 0.83 | 1.32 | 0.85 | 1.02 | 0.95 | -0.086..0.133 | 0.30 |
| GX011627_0001.168 | 35035 | 1.02 | 1.12 | 1.04 | 1.07 | 0.99 | 1.04 | -0.229..0.256 | 0.08 |
| GX011627_0005.239 | 157157 | 0.99 | 1.16 | 1.01 | 1.09 | 0.98 | 1.05 | -0.216..0.242 | 0.09 |
| GX011627_0009.343 | 280280 | 1.09 | 1.01 | 1.10 | 0.99 | 1.00 | 1.01 | -0.171..0.195 | 0.08 |
| GX011627_0013.413 | 402402 | 1.14 | 0.92 | 1.14 | 0.93 | 1.01 | 0.98 | -0.155..0.187 | 0.10 |
| GX011627_0017.517 | 525525 | 1.22 | 0.89 | 1.22 | 0.90 | 1.01 | 0.97 | -0.103..0.151 | 0.20 |
| GX011627_0021.588 | 647647 | 1.32 | 0.83 | 1.31 | 0.84 | 1.02 | 0.95 | -0.021..0.032 | 0.33 |
| GX011628_0000.734 | 22022 | 1.23 | 0.85 | 1.21 | 0.86 | 1.02 | 0.95 | -0.035..0.045 | 0.13 |
| GX011628_0003.337 | 100100 | 1.30 | 0.81 | 1.28 | 0.83 | 1.03 | 0.94 | -0.036..0.053 | 0.21 |
| GX011628_0005.939 | 178178 | 1.33 | 0.81 | 1.31 | 0.82 | 1.03 | 0.94 | -0.023..0.029 | 0.28 |
| GX011628_0008.575 | 257257 | 1.31 | 0.82 | 1.29 | 0.83 | 1.03 | 0.94 | -0.033..0.043 | 0.24 |
| GX011628_0011.178 | 335335 | 1.31 | 0.81 | 1.30 | 0.83 | 1.03 | 0.94 | -0.036..0.047 | 0.24 |
| GX011628_0013.780 | 413413 | 1.38 | 0.80 | 1.36 | 0.81 | 1.03 | 0.93 | -0.024..0.025 | 0.42 |

"cap use" is the largest of mean added red (and, in the blue variant, blue) over that channel's
mean, the quantity the D50/D52 cap limits to 2.0; the largest observed is 0.58. The
"A+blue" columns are the `ancuti2018-blue` variant; "A" the plain one.

## 4. Observations (statistics only, no judgement)

- **Nothing bound on any of the 24 frames under any variant**: the Ancuti red cap (2.0) and
  blue cap never reduced alpha (effective alpha 1.00 everywhere, largest cap use 0.58 of 2.0);
  the white-balance clamp (3.0) never limited a gain (largest gain 1.38, smallest 0.80); N{}
  never collapsed. At the defaults the shallow footage sits well inside the caps and the clamp.
  Whether 2.0 and 3.0 are right for deeper footage is for the deeper part and WP2.1.
- **3C leaves almost nothing for the white balance to do** (gains 0.93 to 1.05): its channel
  means after compensation are already near equal (`means` in `statistics.json`), unlike
  `ancuti2018`, whose white balance gains reach 1.38 (red) and 0.80 (blue).
- **Blue compensation moves little on these frames**: in the `ancuti2018-blue` variant the
  blue white-balance gain is within 0.07 of the plain variant's on every frame; the largest
  change is on `GX011627_0001.168` and `0005.239` (blue gain 1.12 -> 1.07, 1.16 -> 1.09),
  the frames with the least blue.
- **The sharpening normalisation bounds N{} vary 30 fold across frames**: the spread of the
  high-pass percentiles (high minus low) runs from 0.016 (`GX011625_0473.540`, a hazy frame)
  to 0.485 (`GX011627_0001.168`, the sunlit reef floor); the narrowest are in the hazy first
  chapter (0.016 and 0.020), the widest (0.27 to 0.49) on sunlit frames of `GX011626` and
  `GX011627`. The stretch scales the high-pass by 1 over that spread, so low-texture frames get
  their detail amplified far more than sharp ones; nothing here shows whether that looks wrong.
  For DR-14 (the ill-conditioned N{} on low-texture frames): the smallest spread in the 24
  stills is 0.0165, about 9 times the 0.0018 near-flat synthetic of the debt entry and 16000
  times the 1e-6 flat floor; the smallest in the 180 flicker frames is 0.271. The floor never
  triggered.
- **Rounding of the instrument itself**: the 8-bit YUV round trip of the encodes biases R and
  B about -1 level of 255 and G +0.35 on a real frame (identical on both clips of section 5).

## 5. The flicker clip (also WP1.4's clip)

Source `GX011627.MP4` (3840x2160, HEVC, `yuvj420p`, BT.709 full range, 30000/1001 fps, stream
duration 22.7227 s). Excerpt: **start requested at 30 % of the duration = 6.81681 s, 6 s;
180 frames, pts ticks 205205 to 384384 at 1/30000 (6.840167 s to 12.812800 s), step 1001
ticks, none missing** (`flicker\statistics.json` `excerpt`). WP1.4 re-extracts exactly this
range with `frames.excerpt(GX011627.MP4, 0.30 * 22.7227, 6.0, ...)`, or by these ticks.

Every frame was extracted at full resolution (`excerpt`, `naming="index"`, command in
`flicker\statistics.json` `extract_command`), corrected at the `Params()` defaults with
`ancuti2018` (blue off) on the GPU, **unsmoothed**: its own statistics, nothing from any
neighbour (what the prototype does today). Both frame sets were encoded by one command shape
(`encode_commands` in the JSON): 16-bit RGB frames, `scale=out_color_matrix=bt709:out_range=full,
format=yuv420p`, `hevc_nvenc -preset p5 -tune hq -rc vbr -cq 20 -b:v 0 -pix_fmt yuv420p -profile:v
main`, tagged `bt709`/`bt709`/`bt709`/`pc` (on the frames by `setparams`, because the encoder
takes the colour description from the frames and `scale` sets only matrix and range, and by the
encoder options), `hvc1`, `-framerate 30000/1001`, no audio. The
"source" clip is the same decoded frames through the same command, so the two clips differ by
the correction and by the content-dependent error of a lossy encode (the colour tags, the
format and the timing are the same and are checked, below).

Checks (`flicker\statistics.json` `checks`): both clips one HEVC Main stream, `yuvj420p`,
3840x2160, range `pc`, matrix, primaries and transfer `bt709`, 180 frames, first pts 0, every
step 1001 ticks of 1/30000, no audio stream (`verify_clip`; it names each of those and a
stubbed ffprobe with a 10-bit, wrongly sized or wrongly tagged stream fails it); and frame 0 of
the encoded source clip, read back through `frames.extract`, differs from its PNG by 1.98 levels
mean absolute (bias -0.54), which a range or matrix error would exceed. An ad hoc
check (not recorded in the JSON) also read frames 90 and 179 back from each clip and compared
them with the kept PNGs: mean absolute difference 1.9 to 4.8 levels (a lossy encode), frame
order right.

**The flicker as numbers** (white-balance gains, effective alpha, N{} bounds against pts; the
plot is `flicker\statistics.png`, all 180 rows in the JSON):

| index | pts (s) | red gain | blue gain | effective alpha (red) | N{} low | N{} high |
|---|---|---|---|---|---|---|
| 0 | 6.840 | 1.030 | 1.096 | 1.00 | -0.212 | 0.259 |
| 15 | 7.341 | 1.075 | 1.044 | 1.00 | -0.229 | 0.267 |
| 30 | 7.841 | 1.080 | 1.035 | 1.00 | -0.225 | 0.259 |
| 45 | 8.342 | 1.048 | 1.052 | 1.00 | -0.203 | 0.234 |
| 60 | 8.842 | 1.068 | 1.036 | 1.00 | -0.199 | 0.227 |
| 75 | 9.343 | 1.089 | 1.013 | 1.00 | -0.171 | 0.195 |
| 90 | 9.843 | 1.159 | 0.953 | 1.00 | -0.172 | 0.187 |
| 105 | 10.344 | 1.188 | 0.918 | 1.00 | -0.148 | 0.163 |
| 120 | 10.844 | 1.166 | 0.926 | 1.00 | -0.166 | 0.190 |
| 135 | 11.345 | 1.184 | 0.910 | 1.00 | -0.130 | 0.150 |
| 150 | 11.845 | 1.157 | 0.920 | 1.00 | -0.148 | 0.170 |
| 165 | 12.346 | 1.178 | 0.907 | 1.00 | -0.144 | 0.167 |
| 179 | 12.813 | 1.185 | 0.899 | 1.00 | -0.147 | 0.177 |

| statistic over 180 frames | min | max | mean | std dev | largest frame-to-frame step |
|---|---|---|---|---|---|
| red gain | 1.030 | 1.192 | 1.125 | 0.052 | 0.0116 |
| blue gain | 0.896 | 1.096 | 0.975 | 0.061 | 0.0098 |
| effective alpha (red) | 1.000 | 1.000 | 1.000 | 0 | 0 |
| N{} low | -0.241 | -0.126 | -0.177 | 0.032 | 0.0125 |
| N{} high | 0.145 | 0.274 | 0.203 | 0.038 | 0.0136 |

Reading the numbers: over the 6 s the red gain drifts 1.03 to 1.19 and the blue 1.10 to 0.90
(the first frame looks down on the sunlit reef floor, the last is a side view with open blue
water filling the upper left, from the extracted frames), which is scene change; the
frame-to-frame jitter on top of it is small (largest step in red gain 0.0116, 1.0 %; mean
absolute red step 0.0031) and N{} jitters more (largest step 0.0136 on a mean spread of 0.38,
3.6 %). No cap,
no clamp and no collapse occurred in the 180 frames (`bound_counts` all 0). Whether that is
visible as flicker is the owner's call on the two clips.

## 6. Caustics note (per chapter; judged on the six stills of each, no judgement of the correction)

| Chapter | Caustics visible? | What the six stills show |
|---|---|---|
| GX011625 | no | hazy, turbid green water over reef; no dappled light |
| GX011626 | no | reef, fish and a snorkeler in blue water; light shafts in the open water, none on the reef floor |
| GX011627 | faint | sunlit reef floor with hard shadows from direct sun, then open blue water; no clear caustic network (the flicker clip's scene) |
| GX011628 | no | boat hull and snorkelers at the surface: sunbeams (light shafts) and surface glitter, no caustic network on any floor |

So CP1's "shallow" can be refined to "shallow with caustics" at most for `GX011627`, and only
faintly; none of the six stills of any chapter shows a clear caustic network. Six stills per
chapter is a sample; the flicker clip is the better place to look for moving caustics.

## 7. Not in this part (PENDING, named not approximated)

Deeper footage, open blue water (gray-world on open water, spec 12), distance haze (spec 12),
deep-water noise (spec 12), photos and the chaptered cases are not shown: the owner has not
sorted that footage (CP1 partial, 2026-10-15). No shallow frame was used to fake one.

One thing the owner may want to know when reading the open-water row: the six `GX011628`
stills (a boat hull and snorkelers over open water) are mostly blue water, and so are the closing
frames of the flicker clip. They are shallow-category frames (CP1), not the deep open-water
case, and the brief keeps that case PENDING. Their numbers are in section 3 (`GX011628`: red
gain 1.23 to 1.38, the highest of the pack, blue gain 0.80 to 0.85; nothing bound); whether to
record observations about them under the open-water row at CP2 is the owner's call.

## 8. Verification

(See the final report and `docs/proofs/wp1.3-ledger.md`; the gate lines are in the completion
message.)

## 9. CP2 sheet (the owner fills the last three columns)

| Case or artifact class | Observed (yes / no / pending) | Seriousness | Decision |
|---|---|---|---|
| Gray-world on open water (spec 12) | PENDING | | |
| Distance haze (spec 12) | PENDING | | |
| Deep-water noise (spec 12) | PENDING | | |
| Colour cast remaining | | | |
| Magenta push | | | |
| Over-sharpening halo | | | |
| Noise | | | |
| Clipping | | | |
| Flicker (the two clips in `work\wp1.3\flicker\`) | | | |
