# WP1.3D -- Look check pack, deep part (Gate result 3, deep rows)

Material for CP2: the deep half of the look check. The WP1.1 prototype run over the owner's eight
`SCUBA/` chapters (deeper, about 20 m; CP1, owner 2026-10-19) under three variants in the order
**c3** (the default method since spec v0.5.3, D16 amended), `ancuti2018` (blue off) and
`ancuti2018-blue`; the three spec section 12 cases the shallow pack could not show, proposed as
**CANDIDATE** frames by a documented scan; and one 6 s deep clip in motion at the provisional smoothing.
The owner judges it (D103, informal bar); this report records what was run, what the numbers were and
what bound, and ends with the sheet the owner fills. **No correction is judged here, and no candidate
is called open water, haze or noise as a fact: the scan proposes, the owner names.**

Conditions: 2026-10-19/20 (UTC), Windows 11 laptop, RTX 4070 Laptop GPU (prototype `--device gpu`,
CuPy), FFmpeg and ffprobe `9.0.2-full_build-www.gyan.dev`, spec v0.5.3, branch `wp1.3d` (base
`c80725b`). Footage folder read only; every file the package's FFmpeg runs and writers produce is under
`C:\Users\rwsmy\clearwater\work\wp1.3d\` (below, `work\wp1.3d\`). (Python bytecode, the pytest cache and the
CuPy kernel cache belong to the interpreter and the libraries and are not there.)

**Defaults, not tuning.** Every variant runs at the `Params()` defaults with only `method` (and
`blue_compensation` for the third) set. `Params().method` still reads `ancuti2018` on main at this
package's base; WP1.4b flips it. Because every variant sets its method explicitly, the flip does not
change this pack.

## 1. Where things are

| Path under `work\wp1.3d\` | Content |
|---|---|
| `index.html` | the page to open: head (variants, the `Params` defaults, the candidate rule, pending items), the deep clip, the 48 chapter stills, then one section per case with its 4 candidates; thumbnails (960x540) link to the full 16-bit PNGs; under each variant the pair link and a one-line statistics summary |
| `frames\` | 240 PNGs: 60 sources `<chapter>_<pts>.png` and 180 corrected `<frame>-<variant>.png`, 16-bit RGB, 3840x2160 (9,847,522,080 bytes, 9.85 GB) |
| `pairs\` | 180 side-by-side JPEGs (source left, corrected right, each half 1920x1080, quality 92) |
| `thumbs\` | 240 JPEGs (short side 540) |
| `frames.json`, `statistics.json` | per source frame the exact pts, size, colour tags and the FFmpeg command; per frame and variant the prototype's compensation and white-balance records, the `Params` it ran with, the N{} bounds and whether anything bound |
| `scan.json`, `scan\` | every scanned frame with chapter, pts, `D`, `W`, `H`, luma mean and the exclusion reason (none excluded); the per-chapter caches the scan resumes from |
| `deep-frames.json` | the ranked candidates per case and the 8 deepest frames (WP1.4b's input) |
| `clip\GX011600_c3.mp4`, `GX011600_ancuti2018.mp4`, `GX011600_source.mp4` | the three 179-frame clips (section 6) |
| `clip\statistics.json`, `statistics-c3.png`, `statistics-ancuti2018.png` | all 179 frames' raw and smoothed statistics and render records, the encode checks, the per-frame read-back of the three clips, the commands; the plots |
| `clip\source\`, `clip\corrected-c3\`, `clip\corrected-ancuti2018\` | first, middle and last frame PNG of each set (the rest deleted after the three MP4s were encoded and verified) |
| `*.log`, `clip-tables.txt`, `stills-observations.txt` | run logs and scratch tabulations |

Counts: 48 chapter stills (6 per chapter at 5 %, 23 %, 41 %, 59 %, 77 % and 95 % of its duration), 12 case
candidates re-extracted at full resolution (3 cases x 4; no frame serves two cases and none coincides
with a chapter still), 3 variants, 180 corrected PNGs, 180 pairs, 179 clip frames.

## 2. The case scan (claim 1)

One frame every 10 s from 5 s to the end of each chapter (the last grid point at least 0.25 s before the end), short side 540, extracted with
`frames.extract(..., short_side=540)`. **That 540 frame comes from FFmpeg's scaler: it is used for RANKING only
and is never fed to the pipeline** (the pipeline and the clip statistics use the full-resolution frame and, for
the clip, an exact 4x4 area mean in NumPy). Measures on the display-encoded RGB in [0, 1]:

- `D` = mean R / mean G (lower = deeper, red absorbed).
- `W` = fraction of pixels whose BT.709 luma local standard deviation over a 15x15 box (edges reflected) is below 0.01
  AND whose blue or green exceeds red by at least 0.05.
- `H` = luma RMS contrast (standard deviation of luma over the frame; lower = hazier).
- Exclusion: luma mean below 0.05 or above 0.95. **0 of the 290 frames were excluded** (`scan.json` `excluded` is empty).
  (A frame with a zero green mean, for which `D` is undefined, is also excluded by name, as a division
  guard; none occurred.)

**The scan was run several times** (after the cache of each chapter was made to carry its rules and grid, review round 1; and
after the last grid point was allowed up to 0.25 s before the chapter end instead of 1 s, review round 4, which added the
525 s frame of `GX011598`). The earlier runs' files are kept in `work\wp1.3d\scan-before-cache-identity\` and
`work\wp1.3d\scan-before-end-margin\`. The last run added 1 frame(s) (GX011598_0525.024) and its other 289 records equal the previous run's value for value: True; `deep-frames.json` equals the previous run's apart from `written` and `rules.scan.end_margin_s` (1.0 then, 0.25 now): True, so the candidate lists and the eight deepest frames are unchanged.

The thresholds are fixed by the brief. Over the 290 frames: `D` from 0.209 to 1.097
(median 0.638); `H` from 0.038 to 0.318
(median 0.192); `W` from 0.000 to 0.954
(median 0.101). The distribution of `W` (what the threshold picked):

| W from | 0.0 | 0.1 | 0.2 | 0.3 | 0.4 | 0.5 | 0.6 | 0.7 | 0.8 | 0.9 |
|---|---|---|---|---|---|---|---|---|---|---|
| frames | 145 | 40 | 34 | 24 | 19 | 8 | 7 | 8 | 3 | 2 |

Chapters (`GX011589` is a 6.4 s chapter and gives one scan frame, at 5 s):

| Chapter | duration (s) | scanned frames |
|---|---|---|
| GX011589 | 6.4 | 1 |
| GX011590 | 103.2 | 10 |
| GX011591 | 138.2 | 14 |
| GX011592 | 42.3 | 4 |
| GX011593 | 556.5 | 56 |
| GX011598 | 525.3 | 53 |
| GX011600 | 1046.5 | 105 |
| GX011601 | 470.9 | 47 |

The scan frames are on a 10 s grid, so a candidate's pts is the grid time plus the offset to the first decoded frame at or after the grid point
(`pts_ticks` is exact). **Spacing** (30 s between two candidates of the same case, 10 s on the deepest list) is
measured on the GRID and WITHIN one chapter: a pts-based measure would make "30 s" ambiguous by one frame
period, and candidates of different chapters are different recordings and are not compared with each other.

## 3. Candidates (claim 2) -- CANDIDATES, not findings

For each case 4 candidates, ranked: deep-water noise = lowest `D`; open blue water = highest `W`; distance haze =
lowest `H` among frames with `W` below 0.5 (so open water does not take the haze slots). At least 30 s apart
within a chapter, at most 2 per chapter per case, ties by chapter name then pts. Four were found for every case
without lowering any bar. **The owner decides at CP2 whether each one shows the case.** Two things the numbers
say and nothing else: the lowest-`D` frame (`GX011600_0665.031`, `D` = 0.209) is also a
frame with a high `W` (0.708), a measure value, not a description of the frame; no frame
serves two cases.

**Candidates for deep-water noise** -- candidate (lowest D)

| Rank | Frame | pts (ticks at 1/30000) | D | W | H | also serves |
|---|---|---|---|---|---|---|
| 1 | `GX011600_0665.031` | 19950931 | 0.209 | 0.708 | 0.047 | - |
| 2 | `GX011600_0965.031` | 28950922 | 0.236 | 0.153 | 0.207 | - |
| 3 | `GX011591_0095.028` | 2850848 | 0.296 | 0.325 | 0.204 | - |
| 4 | `GX011593_0065.032` | 1950949 | 0.367 | 0.757 | 0.038 | - |

**Candidates for open blue water** -- candidate (highest W)

| Rank | Frame | pts (ticks at 1/30000) | D | W | H | also serves |
|---|---|---|---|---|---|---|
| 1 | `GX011593_0255.021` | 7650643 | 0.577 | 0.954 | 0.039 | - |
| 2 | `GX011593_0105.005` | 3150147 | 0.563 | 0.888 | 0.049 | - |
| 3 | `GX011600_0845.011` | 25350325 | 0.595 | 0.860 | 0.059 | - |
| 4 | `GX011600_0735.001` | 22050028 | 0.427 | 0.749 | 0.083 | - |

**Candidates for distance haze** -- candidate (lowest H among frames with W below 0.5)

| Rank | Frame | pts (ticks at 1/30000) | D | W | H | also serves |
|---|---|---|---|---|---|---|
| 1 | `GX011589_0005.005` | 150150 | 0.726 | 0.457 | 0.050 | - |
| 2 | `GX011593_0025.025` | 750750 | 0.585 | 0.367 | 0.053 | - |
| 3 | `GX011600_0885.017` | 26550524 | 0.757 | 0.171 | 0.064 | - |
| 4 | `GX011591_0055.022` | 1650649 | 0.639 | 0.354 | 0.067 | - |

The 8 deepest frames overall by `D` (10 s rule, no per-chapter limit; WP1.4b's input, `deep-frames.json`
`deepest`):

| Rank | Frame | pts (ticks at 1/30000) | D | W | H | in a candidate list |
|---|---|---|---|---|---|---|
| 1 | `GX011600_0665.031` | 19950931 | 0.209 | 0.708 | 0.047 | candidate: deep-water noise |
| 2 | `GX011600_0965.031` | 28950922 | 0.236 | 0.153 | 0.207 | candidate: deep-water noise |
| 3 | `GX011600_0815.014` | 24450426 | 0.258 | 0.387 | 0.137 | - |
| 4 | `GX011591_0095.028` | 2850848 | 0.296 | 0.325 | 0.204 | candidate: deep-water noise |
| 5 | `GX011600_0975.007` | 29250221 | 0.362 | 0.328 | 0.074 | - |
| 6 | `GX011600_0125.025` | 3750747 | 0.365 | 0.031 | 0.215 | - |
| 7 | `GX011593_0065.032` | 1950949 | 0.367 | 0.757 | 0.038 | candidate: deep-water noise |
| 8 | `GX011600_0275.008` | 8250242 | 0.369 | 0.054 | 0.167 | - |

## 4. Variants, defaults, statistics (claim 3)

Variants, in order: `c3` (`--method c3`), `ancuti2018` (`--method ancuti2018`, blue off), `ancuti2018-blue`
(`--method ancuti2018 --blue`). All at the `Params()` defaults (the page lists every field). The statistics
record per frame and variant holds the prototype's `compensation` and `white_balance` records unchanged, the
`Params` the pipeline ran with, and `normalisation` (the N{} bounds), recomputed with the prototype's
`normalisation_bounds` on the white-balanced image on the same device because they are not part of `Result`.
`bound` says whether a gain cap (effective alpha below the requested alpha), the white-balance clamp or a
collapsed N{} (spread under 1e-6) bound. "R" and "B" are the white-balance applied gains; "A" is
`ancuti2018`, "A+blue" `ancuti2018-blue`; "A alpha R" is the effective red alpha after the D50 cap.

| Frame | role | c3 R | c3 B | A R | A B | A alpha R | A+blue R | A+blue B | N{} spread c3 / A / A+blue |
|---|---|---|---|---|---|---|---|---|---|
| `GX011589_0000.334` | chapter still | 1.04 | 0.92 | 1.43 | 0.78 | 1.00 | 1.41 | 0.79 | 0.210 / 0.229 / 0.229 |
| `GX011589_0001.502` | chapter still | 1.03 | 0.94 | 1.31 | 0.82 | 1.00 | 1.29 | 0.83 | 0.213 / 0.221 / 0.223 |
| `GX011589_0002.636` | chapter still | 1.02 | 0.95 | 1.26 | 0.84 | 1.00 | 1.25 | 0.85 | 0.248 / 0.253 / 0.256 |
| `GX011589_0003.804` | chapter still | 1.02 | 0.95 | 1.24 | 0.83 | 1.00 | 1.23 | 0.85 | 0.295 / 0.296 / 0.300 |
| `GX011589_0004.938` | chapter still | 1.03 | 0.94 | 1.24 | 0.82 | 1.00 | 1.23 | 0.84 | 0.259 / 0.256 / 0.260 |
| `GX011589_0006.106` | chapter still | 1.03 | 0.94 | 1.28 | 0.80 | 1.00 | 1.27 | 0.82 | 0.263 / 0.263 / 0.267 |
| `GX011590_0005.172` | chapter still | 1.02 | 0.95 | 1.25 | 0.84 | 1.00 | 1.24 | 0.85 | 0.222 / 0.232 / 0.232 |
| `GX011590_0023.757` | chapter still | 1.00 | 1.01 | 1.10 | 1.01 | 1.00 | 1.11 | 0.99 | 0.325 / 0.326 / 0.326 |
| `GX011590_0042.309` | chapter still | 1.01 | 0.99 | 1.14 | 0.94 | 1.00 | 1.14 | 0.94 | 0.582 / 0.579 / 0.579 |
| `GX011590_0060.894` | chapter still | 1.01 | 0.98 | 1.17 | 0.91 | 1.00 | 1.17 | 0.92 | 0.389 / 0.391 / 0.391 |
| `GX011590_0079.446` | chapter still | 1.01 | 0.97 | 1.22 | 0.89 | 1.00 | 1.21 | 0.89 | 0.442 / 0.444 / 0.445 |
| `GX011590_0098.031` | chapter still | 1.00 | 1.00 | 1.12 | 0.98 | 1.00 | 1.13 | 0.97 | 0.457 / 0.458 / 0.458 |
| `GX011591_0006.940` | chapter still | 1.04 | 0.92 | 1.39 | 0.76 | 1.00 | 1.38 | 0.77 | 0.217 / 0.212 / 0.216 |
| `GX011591_0031.798` | chapter still | 1.01 | 0.98 | 1.18 | 0.93 | 1.00 | 1.18 | 0.93 | 0.268 / 0.272 / 0.272 |
| `GX011591_0056.690` | chapter still | 1.02 | 0.96 | 1.27 | 0.85 | 1.00 | 1.26 | 0.86 | 0.170 / 0.172 / 0.173 |
| `GX011591_0081.548` | chapter still | 1.04 | 0.92 | 1.73 | 0.73 | 1.00 | 1.72 | 0.74 | 0.226 / 0.227 / 0.226 |
| `GX011591_0106.440` | chapter still | 1.04 | 0.92 | 1.51 | 0.76 | 1.00 | 1.50 | 0.77 | 0.288 / 0.303 / 0.303 |
| `GX011591_0131.298` | chapter still | 1.01 | 0.99 | 1.18 | 0.93 | 1.00 | 1.18 | 0.93 | 0.511 / 0.515 / 0.515 |
| `GX011592_0002.135` | chapter still | 1.00 | 1.00 | 1.14 | 0.97 | 1.00 | 1.15 | 0.96 | 0.410 / 0.413 / 0.412 |
| `GX011592_0009.743` | chapter still | 1.01 | 0.98 | 1.19 | 0.91 | 1.00 | 1.19 | 0.91 | 0.422 / 0.426 / 0.426 |
| `GX011592_0017.384` | chapter still | 1.03 | 0.96 | 1.19 | 0.88 | 1.00 | 1.18 | 0.89 | 0.602 / 0.614 / 0.615 |
| `GX011592_0024.992` | chapter still | 1.02 | 0.96 | 1.24 | 0.86 | 1.00 | 1.23 | 0.87 | 0.553 / 0.566 / 0.566 |
| `GX011592_0032.633` | chapter still | 1.01 | 1.00 | 1.10 | 0.99 | 1.00 | 1.10 | 0.98 | 0.626 / 0.626 / 0.626 |
| `GX011592_0040.240` | chapter still | 1.03 | 0.95 | 1.33 | 0.82 | 1.00 | 1.32 | 0.83 | 0.261 / 0.269 / 0.271 |
| `GX011593_0027.828` | chapter still | 1.04 | 0.91 | 1.34 | 0.77 | 1.00 | 1.33 | 0.78 | 0.440 / 0.405 / 0.409 |
| `GX011593_0127.995` | chapter still | 1.04 | 0.92 | 1.40 | 0.77 | 1.00 | 1.39 | 0.78 | 0.252 / 0.244 / 0.247 |
| `GX011593_0228.161` | chapter still | 1.02 | 0.95 | 1.26 | 0.83 | 1.00 | 1.25 | 0.84 | 0.176 / 0.179 / 0.181 |
| `GX011593_0328.328` | chapter still | 1.04 | 0.92 | 1.44 | 0.76 | 1.00 | 1.41 | 0.78 | 0.427 / 0.441 / 0.441 |
| `GX011593_0428.495` | chapter still | 1.02 | 0.96 | 1.12 | 0.88 | 1.00 | 1.11 | 0.89 | 0.635 / 0.642 / 0.641 |
| `GX011593_0528.661` | chapter still | 1.02 | 0.96 | 1.06 | 0.88 | 1.00 | 1.06 | 0.89 | 0.082 / 0.083 / 0.082 |
| `GX011598_0026.293` | chapter still | 1.01 | 0.97 | 1.24 | 0.89 | 1.00 | 1.23 | 0.90 | 0.603 / 0.585 / 0.586 |
| `GX011598_0120.854` | chapter still | 1.03 | 0.95 | 1.39 | 0.82 | 1.00 | 1.38 | 0.83 | 0.417 / 0.432 / 0.433 |
| `GX011598_0215.415` | chapter still | 1.01 | 0.97 | 1.27 | 0.88 | 1.00 | 1.27 | 0.89 | 0.258 / 0.262 / 0.262 |
| `GX011598_0309.943` | chapter still | 1.00 | 1.01 | 1.10 | 1.01 | 1.00 | 1.11 | 0.99 | 0.231 / 0.234 / 0.234 |
| `GX011598_0404.504` | chapter still | 1.05 | 0.92 | 1.40 | 0.79 | 1.00 | 1.38 | 0.80 | 0.609 / 0.606 / 0.605 |
| `GX011598_0499.065` | chapter still | 1.02 | 0.98 | 1.08 | 0.95 | 1.00 | 1.07 | 0.95 | 0.370 / 0.365 / 0.366 |
| `GX011600_0052.352` | chapter still | 1.02 | 0.96 | 1.35 | 0.88 | 1.00 | 1.34 | 0.88 | 0.565 / 0.616 / 0.616 |
| `GX011600_0240.707` | chapter still | 1.02 | 0.97 | 1.33 | 0.89 | 1.00 | 1.33 | 0.89 | 0.614 / 0.635 / 0.635 |
| `GX011600_0429.095` | chapter still | 1.03 | 0.95 | 1.40 | 0.83 | 1.00 | 1.39 | 0.84 | 0.358 / 0.372 / 0.372 |
| `GX011600_0617.450` | chapter still | 1.02 | 0.95 | 1.50 | 0.83 | 1.00 | 1.49 | 0.84 | 0.448 / 0.488 / 0.487 |
| `GX011600_0805.838` | chapter still | 1.02 | 0.97 | 1.23 | 0.88 | 1.00 | 1.22 | 0.89 | 0.308 / 0.317 / 0.317 |
| `GX011600_0994.193` | chapter still | 1.02 | 0.97 | 1.26 | 0.88 | 1.00 | 1.25 | 0.89 | 0.502 / 0.494 / 0.494 |
| `GX011601_0023.557` | chapter still | 1.00 | 0.99 | 1.24 | 0.95 | 1.00 | 1.25 | 0.94 | 0.472 / 0.503 / 0.504 |
| `GX011601_0108.342` | chapter still | 1.00 | 1.01 | 1.12 | 1.02 | 1.00 | 1.13 | 0.99 | 0.636 / 0.640 / 0.639 |
| `GX011601_0193.093` | chapter still | 1.00 | 1.01 | 1.11 | 1.02 | 1.00 | 1.13 | 1.00 | 0.608 / 0.612 / 0.612 |
| `GX011601_0277.878` | chapter still | 0.99 | 1.02 | 1.04 | 1.04 | 1.00 | 1.05 | 1.02 | 0.741 / 0.740 / 0.740 |
| `GX011601_0362.629` | chapter still | 1.00 | 1.01 | 1.05 | 1.02 | 1.00 | 1.06 | 1.01 | 0.685 / 0.685 / 0.684 |
| `GX011601_0447.414` | chapter still | 1.00 | 1.00 | 1.16 | 0.97 | 1.00 | 1.17 | 0.96 | 0.702 / 0.682 / 0.680 |
| `GX011600_0665.031` | candidate: deep-water noise #1 | 1.05 | 0.90 | 1.58 | 0.73 | 0.94 | 1.57 | 0.74 | 0.219 / 0.240 / 0.240 |
| `GX011600_0965.031` | candidate: deep-water noise #2 | 1.03 | 0.94 | 1.50 | 0.82 | 1.00 | 1.49 | 0.83 | 0.524 / 0.524 / 0.525 |
| `GX011591_0095.028` | candidate: deep-water noise #3 | 1.07 | 0.89 | 2.02 | 0.70 | 1.00 | 1.99 | 0.71 | 0.262 / 0.291 / 0.288 |
| `GX011593_0065.032` | candidate: deep-water noise #4 | 1.06 | 0.88 | 1.64 | 0.70 | 1.00 | 1.61 | 0.71 | 0.110 / 0.129 / 0.130 |
| `GX011593_0255.021` | candidate: open blue water #1 | 1.04 | 0.93 | 1.36 | 0.78 | 1.00 | 1.34 | 0.79 | 0.028 / 0.031 / 0.031 |
| `GX011593_0105.005` | candidate: open blue water #2 | 1.04 | 0.92 | 1.39 | 0.76 | 1.00 | 1.38 | 0.77 | 0.083 / 0.084 / 0.086 |
| `GX011600_0845.011` | candidate: open blue water #3 | 1.00 | 1.00 | 1.17 | 0.99 | 1.00 | 1.18 | 0.97 | 0.087 / 0.088 / 0.088 |
| `GX011600_0735.001` | candidate: open blue water #4 | 1.05 | 0.91 | 1.51 | 0.74 | 1.00 | 1.49 | 0.75 | 0.133 / 0.144 / 0.146 |
| `GX011589_0005.005` | candidate: distance haze #1 | 1.03 | 0.94 | 1.25 | 0.82 | 1.00 | 1.23 | 0.84 | 0.300 / 0.298 / 0.303 |
| `GX011593_0025.025` | candidate: distance haze #2 | 1.05 | 0.91 | 1.41 | 0.74 | 1.00 | 1.40 | 0.75 | 0.382 / 0.341 / 0.343 |
| `GX011600_0885.017` | candidate: distance haze #3 | 1.03 | 0.94 | 1.23 | 0.82 | 1.00 | 1.22 | 0.83 | 0.183 / 0.189 / 0.191 |
| `GX011591_0055.022` | candidate: distance haze #4 | 1.02 | 0.96 | 1.25 | 0.86 | 1.00 | 1.24 | 0.87 | 0.193 / 0.195 / 0.196 |

## 5. Observations (claim 7: statistics only, no judgement)

Counts over the 60 stills (48 chapter stills and 12 candidates), per variant:

- **c3**: red gain cap bound on 0 of 60 frames (none); blue gain cap on 0; white-balance clamp on 0; N{} collapsed on 0; N{} spread below 0.02 on 0 (smallest 0.0276 at `GX011593_0255.021`, largest 0.741 at `GX011601_0277.878`); applied red gain 0.99 to 1.07, blue gain 0.88 to 1.02.
- **ancuti2018**: red gain cap bound on 1 of 60 frames (`GX011600_0665.031` (alpha 0.94)); blue gain cap on 0; white-balance clamp on 0; N{} collapsed on 0; N{} spread below 0.02 on 0 (smallest 0.0307 at `GX011593_0255.021`, largest 0.740 at `GX011601_0277.878`); applied red gain 1.04 to 2.02, blue gain 0.70 to 1.04.
- **ancuti2018-blue**: red gain cap bound on 1 of 60 frames (`GX011600_0665.031` (alpha 0.94)); blue gain cap on 0; white-balance clamp on 0; N{} collapsed on 0; N{} spread below 0.02 on 0 (smallest 0.0307 at `GX011593_0255.021`, largest 0.740 at `GX011601_0277.878`); applied red gain 1.05 to 1.99, blue gain 0.71 to 1.02.

N{} range below 0.02 is the DR-14 territory WP1.4 described (an ill-conditioned stretch on low-texture frames).
The floor of 1e-6 (collapse) never triggered in any variant on the stills. What "bound" means for a gain cap
here is only that the D50 cap lowered alpha; whether that matters visually is the owner's.

## 6. The deep clip in motion (claim 5)

Chapter `GX011600`, centred on the deepest candidate (`GX011600_0665.031`, lowest `D`): start 662.031 s,
6 s, 179 frames, first pts 662.0614 s (tick 19861842), last pts
668.0007 s (tick 20040020), time base 1/30000, frame rate 30000/1001. Every
frame extracted at full resolution. Statistics measured on the exact 4x4 NumPy area-mean proxy of each frame
(`prototype.temporal.proxy`; FFmpeg's scaler is not used), analysed STAGED (D97, `temporal.analyse_staged`) and smoothed
with the centred Gaussian at 2.0 s (the PROVISIONAL default, DR-25(3)); each frame is then corrected from its
smoothed statistics for `c3` and `ancuti2018`. Encoded with NVENC, BT.709 full-range tags as the source, the
source's frame rate, no audio, by `encode_clip` and checked by `verify_clip`; `GX011600_source.mp4` is the
untouched source cut by the same frames.

**How the render is called.** The clip calls `prototype.pipeline.correct(..., statistics=)` directly instead of
`temporal.render`, to keep the `Result` for the bound record. `temporal.render` is that call returning only the
image; a test (`test_correct_with_supplied_statistics_equals_temporal_render_bit_for_bit`) shows the two give
bit-identical output on a synthetic frame with the same supplied statistics (c3 and ancuti2018).

**Red and blue white-balance gains, effective alpha and bound flags against pts** (every 15th frame; the raw
columns are the unsmoothed gray-world gains of the same frame, the others the applied gains from the smoothed
statistics; all 179 frames are in `clip\statistics.json`):

| frame | pts (s) | c3 R | c3 B | c3 raw R / B | A R | A B | A raw R / B | A alpha R | A bound |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 662.061 | 1.015 | 0.970 | 1.014 / 0.971 | 1.295 | 0.881 | 1.303 / 0.881 | 1.0000 | none |
| 15 | 662.562 | 1.020 | 0.966 | 1.017 / 0.966 | 1.267 | 0.880 | 1.276 / 0.876 | 1.0000 | none |
| 30 | 663.062 | 1.039 | 0.957 | 1.034 / 0.958 | 1.267 | 0.878 | 1.238 / 0.879 | 0.9842 | red cap |
| 45 | 663.563 | 1.047 | 0.939 | 1.032 / 0.948 | 1.489 | 0.829 | 1.521 / 0.831 | 0.8287 | red cap |
| 60 | 664.063 | 1.044 | 0.915 | 1.044 / 0.910 | 1.724 | 0.754 | 1.825 / 0.735 | 0.6735 | red cap |
| 75 | 664.564 | 1.050 | 0.900 | 1.051 / 0.898 | 1.690 | 0.729 | 1.651 / 0.729 | 0.8117 | red cap |
| 90 | 665.064 | 1.051 | 0.898 | 1.052 / 0.896 | 1.604 | 0.733 | 1.622 / 0.730 | 0.9285 | red cap |
| 105 | 665.565 | 1.048 | 0.905 | 1.048 / 0.904 | 1.509 | 0.748 | 1.500 / 0.746 | 0.9904 | red cap |
| 120 | 666.065 | 1.041 | 0.916 | 1.041 / 0.916 | 1.437 | 0.766 | 1.440 / 0.765 | 1.0000 | red cap |
| 135 | 666.566 | 1.037 | 0.925 | 1.037 / 0.926 | 1.398 | 0.781 | 1.391 / 0.784 | 1.0000 | none |
| 150 | 667.066 | 1.033 | 0.932 | 1.034 / 0.929 | 1.368 | 0.794 | 1.386 / 0.788 | 1.0000 | none |
| 165 | 667.567 | 1.028 | 0.943 | 1.027 / 0.944 | 1.293 | 0.822 | 1.294 / 0.823 | 1.0000 | none |
| 178 | 668.001 | 1.025 | 0.950 | 1.024 / 0.952 | 1.235 | 0.844 | 1.219 / 0.849 | 1.0000 | none |

Series over the 179 frames, min / mean / max / largest frame-to-frame step of the APPLIED gain:
c3 red 1.015 / 1.038 / 1.052 / 0.0016, c3 blue 0.897 / 0.930 / 0.970 / 0.0017; ancuti2018 red
1.235 / 1.444 / 1.734 / 0.0218, ancuti2018 blue 0.728 / 0.798 / 0.881 / 0.0057. The raw (unsmoothed)
c3 red gain has a largest step of 0.0443 and the raw ancuti2018 red gain
0.1401.

**What bound in the clip.** `c3`: gain cap on 0 / 0 frames (red / blue), white-balance clamp on
0, N{} collapsed on 0; N{} spread 0.212 to 0.409 (below 0.02 on 0).
`ancuti2018`: the D50 red cap lowered the smoothed alpha below 1.0 (by more than 1e-9) on 104 frames
(alpha down to 0.673; frames 17 to 120 of 0 to 178), blue cap
0, white-balance clamp on 0, N{} collapsed
0; N{} spread 0.206 to 0.396 (below 0.02 on 0). A gain cap counts as
bound here when the smoothed alpha is below the requested 1.0 by more than 1e-9: a Gaussian-smoothed constant 1.0
comes out as 0.9999999999999999 and an exact comparison flagged every frame (found on the first full render of
this clip, fixed by `DEEP_CAP_TOLERANCE`, a test shows the strict shallow behaviour is unchanged).

**Encode and read-back (deviation, ruled).** The read-back checks that each encoded frame is the right frame in
the right order, not fidelity: every frame of the encoded clip is converted back and compared at 1/8 size with its own
PNG and with the PNGs of its neighbours. The shallow clip's bound on the difference to the own PNG is 3.0 levels
(`READBACK_MAX_OWN`, still used by `flicker`). On the deep footage a lossy NVENC CQ 20 encode exceeds it on
some frames, so the deep clip uses `DEEP_READBACK_MAX_OWN` = 5.0. Measured on this run (levels of 255):

| Clip | own min / mean / max (levels) | frames over 3.0 | smallest neighbour margin (frame) | channel bias R, G, B | frames read |
|---|---|---|---|---|---|
| c3 | 1.00 / 1.92 / 3.85 | 28 | 2.15 (105) | -0.72, +0.33, -0.82 | 179 of 179 |
| ancuti2018 | 1.01 / 1.94 / 3.85 | 25 | 2.09 (105) | -0.77, +0.33, -0.75 | 179 of 179 |
| source | 0.60 / 1.42 / 3.03 | 2 | 1.63 (117) | -0.78, +0.34, -0.87 | 179 of 179 |

Every frame is still closer to its own PNG than to a neighbour's (the margin is positive everywhere, smallest as
tabulated), the channel bias is within the unchanged 2.0 bound, and the neighbour test is unchanged.

## 7. Not in this part (PENDING, named not approximated)

- Photos (iPhone): none supplied.
- Chaptered recordings across a chapter boundary: none in the `SCUBA/` set (inventory 2026-10-18).
- Any default change, tuning, re-run at other parameters, the gain-cap noise measurement and the `Params()` flip: WP1.4b and WP2.1.
- Timing: no timing or memory figure is reported as a result (the package is not exclusive; the commands print elapsed seconds on the console, which are not results).

Known limits of the working-folder controls (banked, outside the declared envelope: one operator running the documented
steps in order on an untampered working folder; none changes what the page or the clip show in that case):

- A scan-cache or clip-render source is identified by the footage file's name and byte count only (SHA-256 of the
  24.1 GB set, 24,122,034,711 bytes, was judged out of proportion); a different file of the same size would pass. An interrupted scan that is resumed after its source file was replaced keeps the rows already saved (a partial is not checked against the byte count; a finished cache is). The PNGs and MP4s of the clip
  are bound by SHA-256 between render, encode and page.
- A hand-edited scan record whose values are in range and self-consistent cannot be told from a measured one.
- The 6 s duration, the proxy text and the start of the clip are not re-derived from the source at encode time, so a
  render made programmatically with another duration would be linked as the deep clip (the page's own command always
  renders 6 s).

## 8. Verification

Gate on the head named in the ledger (full run, `footage` and `gpu` tests RUN, none skipped):

- `uv run ruff check .`: all checks passed. `uv run ruff format --check .`: 110 files already formatted.
- `uv run mypy`: success, no issues in 20 source files.
- `uv run pytest -q --basetemp=work/pytest-wp1.3d`: **734 passed**, 1 warning (CuPy "CUDA path could not be detected"),
  447.6 s. No test skipped. `tests/test_lookcheck.py` is unchanged and `tools/prototype/`,
  `tools/lookcheck/frames.py`, `pyproject.toml` and `src/` are untouched (`git diff --stat c80725b..HEAD` lists
  `tools/lookcheck/scan.py`, `tools/lookcheck/pack.py`, `tests/test_lookcheck_deep.py`, this report and the ledger only).
- Harness files (`scripts/`, `.claude/`, kernel docs, `tests/harness/`) untouched, so the harness gate is not re-run.
- Tests of this package: `tests/test_lookcheck_deep.py` (the brief's tests 1-5 and 7; the scan cache identity; the
  clip steps' input checks; the bit-identity of `correct(..., statistics=)` against `temporal.render`; the flicker
  3.0 bound; the cap tolerance).

Review (Reviewer A, STRONG tier: WSL, codex-cli 0.162.1, `-m gpt-5.6-sol -c model_reasoning_effort=high -s read-only`),
one round per row; evidence under `C:\Users\rwsmy\clearwater-review-evidence\wp1.3d\rN\`:

| Round | Findings (severity, in or out of envelope) | Fixed in | Verdict |
|---|---|---|---|
| 1 | 2 major in envelope (a scan cache without identity could certify a stale or incomplete scan; the clip's encode and page steps trusted whatever PNGs and MP4s were on disk); 3 minor (a usage docstring that named the wrong output folder; a zero-green frame is excluded by a rule the brief does not name, out of envelope; the footage and gpu tests skip when their inputs are absent, out of envelope) | `81187ee`, `018f3a8`, `2883592`; the zero-green rule is now stated in section 2; the skip behaviour is the repository's test convention, checked at the gate | NEW_CRITICAL_MAJOR_FOUND |
| 2 | 3 major in envelope (the scan cache lacked source and record identity; `deep-frames.json` was not tied to `scan.json`; the clip's frames, statistics and MP4s were not bound to one render); 2 minor (a scan grid point in the last second omitted by the 1 s end margin, out of envelope; a page pts printed without the time-base numerator) | `82343ad` and the commit after it (cache source size and per-record checks; `deep-frames.json` rebuilt from `scan.json`; SHA-256 of every clip PNG and MP4) | NEW_CRITICAL_MAJOR_FOUND |
| 3 | 2 major in envelope (a candidate and the footage described in look terms in the report, against the rule that the scan proposes and the owner names; the clip's N{} ranges recorded from a recomputation on the full-resolution frame, not the smoothed proxy bounds the render applied); 3 minor in envelope (elapsed-time figures against "no timing recorded"; a file-name pattern naming `GX0115xx`; "nearest frame" where extraction takes the first frame at or after the grid point). 2 major OUT-OF-ENVELOPE (source identity is the byte count only; the 6 s duration is not re-checked at encode) | `37ff131` (clip records the applied N{} bounds, test) and the regenerated report (wording, timing sentence, file pattern, grid-point sentence; the two out-of-envelope majors are disclosed in section 7) | NEW_CRITICAL_MAJOR_FOUND |
| 4 | 1 major in envelope (the scan grid stopped 1 s before a chapter end and so omitted the 525 s point of `GX011598`, 525.3248 s long; the earlier statement that no chapter had such a point was wrong); 2 minor in envelope (the "no timing recorded" sentence beside console elapsed prints; two docs-only commits without the `Co-Authored-By` footer, disclosed, history not rewritten) | `6d5ccab` (grid reaches 0.25 s before the end, test; the scan was re-run: 290 frames, the 289 earlier records equal, candidate lists and deepest list unchanged) and the regenerated report | NEW_CRITICAL_MAJOR_FOUND |
| 5 | 0 in envelope; 1 major OUT-OF-ENVELOPE (an interrupted scan resumed after the source file was replaced keeps the saved rows: the partial is not checked against the source's byte count; disclosed in section 7) | no code change; the disclosure in section 7 widened | NO_NEW_IN_ENVELOPE_BLOCKING (the reviewer's line reads NEW_CRITICAL_MAJOR_FOUND for the out-of-envelope finding; the round converges by the orchestrator's envelope ruling) |

## 9. CP2 deep sheet (to be filled from the owner's words)

Candidate files are under `work\wp1.3d\frames\` (`<frame>.png` source, `<frame>-c3.png`, `-ancuti2018.png`,
`-ancuti2018-blue.png`); the clip files are `work\wp1.3d\clip\GX011600_c3.mp4`, `GX011600_ancuti2018.mp4`,
`GX011600_source.mp4`.

| Case or artifact class | Observed (yes / no / pending) | Seriousness | Decision |
|---|---|---|---|
| Gray-world on open water (spec 12): candidates `GX011593_0255.021`, `GX011593_0105.005`, `GX011600_0845.011`, `GX011600_0735.001` | PENDING | | |
| Distance haze (spec 12): candidates `GX011589_0005.005`, `GX011593_0025.025`, `GX011600_0885.017`, `GX011591_0055.022` | PENDING | | |
| Deep-water noise (spec 12): candidates `GX011600_0665.031`, `GX011600_0965.031`, `GX011591_0095.028`, `GX011593_0065.032` | PENDING | | |
| Colour cast remaining | PENDING | | |
| Magenta / red push | PENDING | | |
| Over-sharpening halo | PENDING | | |
| Noise (stills) | PENDING | | |
| Noise in motion (the clip) | PENDING | | |
| Clipping | PENDING | | |
| Flicker (the clip, smoothed at 2.0 s) | PENDING | | |
