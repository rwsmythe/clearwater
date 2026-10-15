# WP1.4 -- Noise and statistics experiments, shallow part (Gate result 5)

Spec v0.5.2. Brief `docs/briefs/wp1.4-brief.md`. This part delivers Gate result 5 (D98, staged
versus flat) and the design evidence for plan section 9 rows "Smoothing filter type and default
window", "Robust statistics for normalization bounds" and "Stage definitions per compensation
method". **The gain-cap noise test (D100, Gate result 4) is NOT in this part**: it needs a deep
frame and is WP1.4b. No default was changed; every recommendation below is for CP2 and WP2.1.

## 1. Where things are

Code: `tools/prototype/temporal.py` (statistics, staged and flat analysis, smoothers, flicker
measure, step response, robust candidates), the additive hook in `tools/prototype/pipeline.py`
(`Statistics`, `correct(..., statistics=...)`), the runner `tools/statistics_experiments.py`
(phases `extract`, `analyse`, `render`), tests `tests/test_prototype_temporal.py`.

Records, all under `C:\Users\rwsmy\clearwater\work\wp1.4\` (`<x>` = `GX011627` or `GX011625`):

| Record | Holds |
|---|---|
| `<x>\excerpt.json` | source, start, frame rate, time base, colour tags, the FFmpeg extract command, every frame's exact pts (`pts_ticks`, `pts_exact`, `pts_seconds`) |
| `<x>\statistics-raw.json` | every frame's own statistics, unsmoothed: `proxy` (both methods), and for `GX011627` also `full` (the full frame) |
| `<x>\statistics-staged.json` | the STAGED analysis (Gaussian 1.0 s): per method the smoothed series and, per stage, the series that stage measured before smoothing |
| `<x>\statistics-flat.json` | the FLAT analysis (Gaussian 1.0 s) |
| `<x>\results.json` | mismatch (flat minus staged), proxy minus full (`GX011627`), flicker (per method: unsmoothed, staged, flat, linear trend; per-step series), proxy render differences, the 12 smoothing candidates, the 6 robust candidates, the synthetic near-flat frames |
| `<x>\flicker.png` | the per-step flicker of the unsmoothed, staged and flat proxy renders (Ancuti 2018) against pts |
| `GX011627\render.json` | the three full-resolution renders: encode commands, the WP1.3 checks of each clip, the witness against WP1.3's frames, full-resolution differences and flicker |
| `GX011627\clips\GX011627_{unsmoothed,staged,flat}.mp4` | the CP2 clips |
| `<x>\frames\`, `GX011627\renders\<version>\` | the first, middle and last full-resolution PNG of each set (the rest removed once the clips were verified) |
| `<x>\proxies.npy` | the 960x540 proxies (float32), the input of `analyse` |

Commands: `uv run python tools/statistics_experiments.py extract`, then `analyse`, then `render`
(GPU: the RTX 4070; FFmpeg 9.0.2 from the WinGet links folder on PATH).

## 2. Instrument

**Excerpts.** `GX011627`: WP1.3's flicker excerpt, `frames.excerpt(video, 0.30 * 22.7227, 6.0)`,
180 frames, pts ticks 205205..384384 at 1/30000, step 1001 (6.840 s to 12.813 s). The runner
asserts these ticks (a mismatch is a STOP). `GX011625`: 6 s from 50 % of its 498.43 s stream, 179
frames, ticks 7477470..7655648 (249.249 s to 255.188 s). It pans from a coral head into hazy, almost
featureless water; frame 178 is the low-texture end. Both are `yuvj420p` with BT.709 matrix,
primaries and transfer, full range, nothing assumed (`excerpt.json` `tags`). D54's fallback is not
implemented in this path (DR-20); the tags are recorded, not re-derived.

**Proxy (7.3).**
- Every frame is decoded at full resolution to 16-bit PNG and read with `frames.read_png16`.
- The proxy is an area average computed in NumPy: each 4x4 block of the 3840x2160 frame is replaced
  by its mean (float64 accumulation, cast to float32), giving 960x540 (`temporal.proxy`).
- FFmpeg's scaler is not used for it (its default is bicubic).
- Every statistic below is measured on proxies unless marked "full".

**The `Statistics` record (first draft of IF-3's analyse/render split; WP2.1 reads it).**
`prototype.pipeline.Statistics` holds, per frame, every whole-frame scalar of spec 7.1 in the form
the step consumes it. Every field is optional (`None`: the step measures it).

| Field | Stage | Scalars | Consumed by |
|---|---|---|---|
| `compensation_means` | compensation (Ancuti 2018 only) | R, G, B means of the input | the [A18] equations and the gain cap |
| `compensation_alpha` | compensation (Ancuti 2018 only) | effective alpha per compensated channel, after the cap | the [A18] equations (the cap is then not re-evaluated) |
| `white_balance_gains` | white balance | gray-world gains `target / mean_c`, before strength and clamp | `white_balance`, which applies `white_balance_strength` and the D99 clamp to the supplied gains |
| `normalisation_bounds` | fusion | N{} low and high | `fusion_inputs` (the flat-image rule applies to the supplied bounds) |
| `saliency_means` | fusion | the Lab mean of fusion input 1 and of input 2 | the saliency weight |

- `correct(image, params, backend=None, statistics=None)`: with `None` the code path is the
  accepted one. With a record, each supplied value replaces the measurement where the step would
  make it.
- `temporal.statistics_of(frame, params)` returns the frame's own record. Feeding it back gives a
  bit-identical `Result` (every array and both step records) on the CPU and on the GPU, for Ancuti
  2018 blue off and on and for 3C, also after a JSON round trip (test 1).
- In JSON a record is flattened to named scalars (`white_balance_gains.R`,
  `normalisation_bounds.low`, `saliency_means.input2.b`, ...; `temporal.flatten`). Python's float
  repr round-trips exactly.

**Staged and flat (D97, D98).**
- RAW statistics of a frame: its own chain, every stage measured on the frame corrected with its OWN
  unsmoothed earlier stages (`statistics_of`, what `correct()` does).
- FLAT (`temporal.analyse_flat`): every raw scalar smoothed independently.
- STAGED (`temporal.analyse_staged`), per stage in the method's order: every proxy is measured with
  the SMOOTHED statistics of all earlier stages supplied, so the stage sees the frame corrected
  with them. The stage's scalars are then smoothed and supplied to the later stages. A test spies on
  the measurement and asserts that stage k receives exactly the smoothed fields of the stages before
  it.
- Stage 1 is measured on the raw frame in both analyses, so its mismatch is zero by construction.
- Within the fusion stage, the saliency mean of input 2 is measured on input 2 built with the
  frame's own N{} bounds (the brief's three stages; section 7 discusses a fourth).

**Smoothers (14.1, D95).** Centred, symmetric kernels over the `2h + 1` frames within half the
window of the centre, `h = floor(window / 2 * frame rate)` in exact rational arithmetic; weights sum
to 1. At 30000/1001 fps a 1.0 s window gives h = 14, 29 taps.
- `moving_average`: equal weights.
- `gaussian`: `exp(-t^2 / (2 s^2))` with `s = (window / 2) / sqrt(2 ln 100)`, so the kernel falls
  to 1 % of its peak at `t = window / 2`: the window is the kernel's full width at 1 %. At 1.0 s,
  `s` = 0.165 s; the outermost tap (14 frames = 0.467 s) is 1.8 % of the peak.
- `median_gaussian`: a centred running median over 0.1 s (3 frames at 29.97 fps), which removes a
  single bad frame, then the `gaussian`.
- Past the ends of an excerpt the end value is held (`nearest`). That is a property of a 6 s
  excerpt, not of the product, which smooths over the whole clip. It is why the flicker is also
  reported over the INTERIOR frames: those at least 2.0 s from either end, where even a 4 s window
  fits (61 steps).
- The comparison of section 3 uses `gaussian` 1.0 s, as the brief fixes.

**Flicker measure: an instrument of this package, NOT V3.** V3 (D112) is measured later, on a
synthetic clip, in the region the disturbance does not touch; this measure is evidence on real
footage only.
- Signals of a proxy: its R, G and B means and its BT.709 luma mean.
- Each sequence of proxies is rendered (the full pipeline, `correct()` through the hook) with the
  statistics under test. The SAME proxies are rendered once more with CONSTANT statistics (each
  scalar's mean over the method's raw series): the reference.
- Per frame step t and signal: `|(s[t+1] - s[t]) - (r[t+1] - r[t])|` in 8-bit levels. The
  tabulated figure is the mean over the steps and the four signals (`temporal.flicker`).
- The content's own change passes through both renders alike and cancels to first order. A test
  renders moving content with constant statistics 3 % apart: the measure keeps under 6 % of the
  content's change.
- The same reference and the same step sets are used for every sequence of a method and excerpt.
- Limits: (a) a second-order term remains: content change times the difference between the frame's
  statistics and the constant ones. (b) A WANTED slow change of the statistics, following a real
  scene change, is counted as well as jitter; the `linear trend` row (each raw scalar replaced by
  its least-squares straight line over the excerpt: drift, no jitter) shows the size of that part.
  (c) Means only: a change that keeps the means (a local shimmer) is not seen.
- The brief's suggested form (mean |step| of the rendered frames minus that of the source) is
  recorded as `source_referenced` for every sequence. It is not the tabulated measure, because a
  correction gain different from 1 scales the content change and leaves it in the difference: it is
  negative on every sequence here.

**Responsiveness** (`temporal.step_response`, a 30 s series, 0 then 1):
- `t90`: the time from the step instant (the midpoint between the last 0 and the first 1) to the
  first frame at or above 0.9.
- `rise`: from the first frame at or above 0.1 (a centred filter starts before the step) to that one.
- `outlier`: the response at a single frame of 1 in zeros.
- `gain`: the amplitude passed of a unit sinusoid at 0.5, 1 and 2 Hz, fitted over the interior.

**Robust candidates for N{} (14.1, DR-14).** On the high-pass `I - G*I` of each frame's own
white-balanced proxy (Ancuti 2018), over all pixels and channels (`temporal.robust_bounds`):
- min/max ([A18]); linear-interpolation percentiles 0.5/99.5 (the default), 1/99, 2/98;
- a trimmed standard deviation: the values below the 1st and above the 99th percentile dropped,
  `m +- k s` from the mean and population standard deviation of the rest, k = 2.5 and 3.

Measured per candidate:
- the relative step: mean |frame-to-frame change| of a bound over its mean magnitude (the jitter);
- the coefficient of variation over the excerpt (the brief's measure; it also counts the scene drift);
- the fraction of values the stretch clips;
- the effect on the result: the proxy rendered with the candidate's bounds (everything else its own)
  against the default render, mean |difference| in 8-bit levels;
- the smallest range (high minus low), and whether the 1e-6 flat floor triggered;
- the same ranges on two synthetic 960x540 frames: a near-flat one (RGB 0.10/0.45/0.55 plus Gaussian
  noise of sd 0.002, seed 0) and an exactly flat one.

## 3. Result: staged versus flat (D98, Gate result 5)

Gaussian 1.0 s, both methods, both excerpts. **Mismatch, flat minus staged, Ancuti 2018 (blue off)**
(`results.json` `mismatch_flat_minus_staged`: mean signed, largest absolute, frame and pts of the
largest):

| Statistic | GX011627 mean | max | frame | GX011625 mean | max | frame |
|---|---|---|---|---|---|---|
| `white_balance_gains.R` | -0.00013 | 0.00191 | 0 (6.840 s) | -0.00005 | 0.00229 | 178 (255.188 s) |
| `white_balance_gains.G` | +0.00002 | 0.00081 | 0 (6.840 s) | +0.00001 | 0.00064 | 178 (255.188 s) |
| `white_balance_gains.B` | +0.00002 | 0.00100 | 0 (6.840 s) | +0.00001 | 0.00064 | 178 (255.188 s) |
| `normalisation_bounds.low` | +0.00002 | 0.00017 | 0 (6.840 s) | +0.00000 | 0.00001 | 84 (252.052 s) |
| `normalisation_bounds.high` | -0.00001 | 0.00020 | 25 (7.674 s) | -0.00000 | 0.00002 | 82 (251.985 s) |
| `saliency_means.input1.L` | +0.00016 | 0.11165 | 0 (6.840 s) | -0.00022 | 0.02912 | 131 (253.620 s) |
| `saliency_means.input1.a` | -0.01048 | 0.18750 | 45 (8.342 s) | +0.00131 | 0.26646 | 178 (255.188 s) |
| `saliency_means.input1.b` | +0.01237 | 0.65261 | 0 (6.840 s) | -0.00176 | 0.09992 | 105 (252.752 s) |
| `saliency_means.input2.L` | -0.00015 | 0.06157 | 0 (6.840 s) | -0.00028 | 0.01298 | 131 (253.620 s) |
| `saliency_means.input2.a` | -0.00261 | 0.08996 | 85 (9.676 s) | +0.00076 | 0.11096 | 178 (255.188 s) |
| `saliency_means.input2.b` | +0.00562 | 0.28552 | 0 (6.840 s) | -0.00073 | 0.04268 | 105 (252.752 s) |

- Stage 1 (`compensation_means.*`, `compensation_alpha.red`): 0 on every frame of both excerpts.
  It is measured on the raw frame in both analyses; the gain cap never bound (alpha 1.00 throughout).
- The white-balance gains differ by at most 0.0023 (0.2 % of a gain near 1.1).
- The N{} bounds differ by at most 0.0002, on a spread of 0.33 (`GX011627`).
- The saliency references differ by at most 0.65 on the Lab scale of 0..100 (the weight divides by 100).
- 3C: the white balance is its first stage, so its gains do not differ at all; its fusion scalars
  differ by at most 0.00005 (N{}) and 0.20 (Lab) (`mismatch_flat_minus_staged.c3`).

**Residual flicker** (section 2's measure; 8-bit levels, all steps / interior steps; `results.json`
`flicker`) and how far apart the staged and flat proxy renders are (`staged_vs_flat_render`: mean
|difference| over all frames / the largest frame mean / the largest single value, levels):

| Excerpt | Method | unsmoothed | staged | flat | linear trend | staged vs flat render |
|---|---|---|---|---|---|---|
| GX011627 | ancuti2018 | 0.236 / 0.256 | 0.134 / 0.182 | 0.130 / 0.180 | 0.090 / 0.090 | 0.058 / 0.144 / 0.68 |
| GX011627 | c3 | 0.077 / 0.078 | 0.034 / 0.048 | 0.034 / 0.047 | 0.024 / 0.025 | 0.003 / 0.007 / 0.11 |
| GX011625 | ancuti2018 | 0.151 / 0.134 | 0.067 / 0.050 | 0.064 / 0.048 | 0.029 / 0.026 | 0.032 / 0.155 / 0.90 |
| GX011625 | c3 | 0.123 / 0.095 | 0.045 / 0.022 | 0.045 / 0.022 | 0.018 / 0.015 | 0.001 / 0.005 / 0.05 |

Full resolution (`GX011627`, `render.json`):
- The staged and flat renders differ by 0.058 levels on average (largest frame mean 0.144, frame 0;
  largest single value 0.76) (`full_resolution_differences.staged_vs_flat`).
- The flicker measure on the full-resolution renders (the same definition, the reference rendered
  at full resolution) gives 0.235 / 0.133 / 0.129 for unsmoothed / staged / flat (interior 0.256 /
  0.181 / 0.179), within 0.002 of the proxy figures (`full_resolution_flicker`).
- The unsmoothed render's frames 0, 90 and 179 are bit-identical to WP1.3's kept frames
  (`wp13_witness`, largest difference 0): the hook fed full-frame statistics reproduces WP1.3's clip.
- Each of the three clips passes WP1.3's checks (`checks`): one HEVC Main stream, `yuvj420p`,
  3840x2160, `pc` and `bt709` tags, 180 frames at 1001-tick steps, no audio; every frame read back
  (worst own difference 2.85 / 2.93 / 2.93 levels, smallest neighbour margin 7.60 / 8.04 / 8.01).
- Staged and flat each differ from the unsmoothed clip by 0.94 and 0.96 levels on average (largest
  single value 11.1 and 11.3). That combines the smoothing and the proxy gap of section 6, which
  this part does not separate (section 8).

**Do I expect the difference to be visible? No.**
- On both excerpts and both methods, the staged and flat renders differ by under a tenth of an 8-bit
  level on average (0.058 and 0.032 for Ancuti 2018; 0.003 and 0.001 for 3C).
- At the single worst pixel of the worst frame they differ by under one level (0.68 and 0.90). The
  clips are 8-bit, so a difference under one level changes a displayed pixel by at most one code.
- Their residual flicker is the same to within 3 %: flat is the lower one, 0.130 against 0.134 and
  0.064 against 0.067. Both are far below the unsmoothed render (0.236 and 0.151).
- The reason is in the mismatch table. The earlier stages change slowly (the red gain moves by 0.003
  per frame on average on `GX011627`), so the frame a later stage sees changes little whether or not
  the earlier stages were smoothed.
- The owner decides at CP2 on `GX011627_staged.mp4` against `GX011627_flat.mp4`. Plan section 10
  row 5: no visible difference means a method may declare one stage; IF-3 stays staged.

## 4. Result: smoothing candidates (14.1 "Temporal smoothing filter type and default window")

Each candidate in both schemes on Ancuti 2018 (blue off); flicker in 8-bit levels (`results.json`
`smoothing`). The step figures are the filter's own, the same for both excerpts at 29.97 fps.
Unsmoothed: 0.236 (`GX011627`) and 0.151 (`GX011625`); linear trend 0.090 and 0.029.

| Candidate | taps | t90 (s) | rise 10-90 (s) | outlier | gain 0.5 / 1 / 2 Hz | GX011627 staged / flat | interior staged | GX011625 staged / flat | interior staged |
|---|---|---|---|---|---|---|---|---|---|
| moving_average 0.5 s | 15 | 0.22 | 0.40 | 0.067 | 0.901 / 0.637 / 0.001 | 0.136 / 0.132 | 0.184 | 0.070 / 0.067 | 0.053 |
| moving_average 1 s | 29 | 0.42 | 0.80 | 0.034 | 0.657 / 0.033 / 0.033 | 0.110 / 0.106 | 0.172 | 0.057 / 0.054 | 0.040 |
| moving_average 2 s | 59 | 0.82 | 1.60 | 0.017 | 0.016 / 0.016 / 0.016 | 0.084 / 0.081 | 0.146 | 0.045 / 0.043 | 0.033 |
| moving_average 4 s | 119 | 1.62 | 3.20 | 0.008 | 0.007 / 0.007 / 0.007 | 0.079 / 0.078 | 0.091 | 0.034 / 0.032 | 0.029 |
| gaussian 0.5 s | 15 | 0.12 | 0.20 | 0.162 | 0.968 / 0.877 / 0.589 | 0.159 / 0.156 | 0.194 | 0.085 / 0.082 | 0.069 |
| gaussian 1 s | 29 | 0.22 | 0.40 | 0.081 | 0.878 / 0.590 / 0.115 | 0.134 / 0.130 | 0.182 | 0.067 / 0.064 | 0.050 |
| gaussian 2 s | 59 | 0.45 | 0.87 | 0.041 | 0.589 / 0.115 / 0.001 | 0.106 / 0.102 | 0.167 | 0.053 / 0.050 | 0.037 |
| gaussian 4 s | 119 | 0.85 | 1.67 | 0.020 | 0.116 / 0.001 / 0.001 | 0.081 / 0.080 | 0.140 | 0.042 / 0.041 | 0.031 |
| median_gaussian 0.5 s | 15 | 0.12 | 0.20 | 0.000 | 0.968 / 0.876 / 0.582 | 0.158 / 0.155 | 0.193 | 0.084 / 0.081 | 0.068 |
| median_gaussian 1 s | 29 | 0.22 | 0.40 | 0.000 | 0.878 / 0.589 / 0.114 | 0.133 / 0.129 | 0.182 | 0.067 / 0.064 | 0.050 |
| median_gaussian 2 s | 59 | 0.45 | 0.87 | 0.000 | 0.589 / 0.115 / 0.001 | 0.106 / 0.101 | 0.167 | 0.053 / 0.050 | 0.037 |
| median_gaussian 4 s | 119 | 0.85 | 1.67 | 0.000 | 0.116 / 0.001 / 0.000 | 0.081 / 0.080 | 0.140 | 0.042 / 0.041 | 0.031 |

Reading:
- At the same responsiveness, the moving average and the Gaussian leave the same flicker: the 0.5 s
  average and the 1 s Gaussian both reach 90 % in 0.22 s and leave 0.136 and 0.134.
- The moving average's frequency response has side lobes. The 1 s average passes 3 % at 1 Hz AND at
  2 Hz; the 0.5 s average passes 64 % at 1 Hz and 0.1 % at 2 Hz. Which flicker frequencies survive
  depends on the window irregularly. The Gaussian's attenuation rises monotonically with frequency.
- The median before the Gaussian costs nothing measurable here (the same flicker to the third
  decimal) and removes a single-frame outlier entirely (outlier response 0, against 0.041 for the
  2 s Gaussian).
- Flat and staged rank the candidates the same way.
- Longer windows keep lowering the flicker, but less and less (staged Gaussian): from 1 s to 2 s by
  21 % and 20 %, from 2 s to 4 s by 23 % and 21 %, while the time to 90 % doubles each step
  (0.22, 0.45, 0.85 s). At 4 s much of what remains is the wanted drift (the linear-trend figure).

**Recommendation: `median_gaussian` (a 3-frame median, then the Gaussian of section 2), default
window 2.0 s** (s = 0.33 s; 90 % of a step after 0.45 s; 10-90 % rise 0.87 s). Grounds:
1. Among the windows that still follow a turn, it passes the least caustic-rate jitter: 11.5 % at
   1 Hz and 0.1 % at 2 Hz, where 1.0 s passes 59 % and 11.5 %.
2. It leaves 0.106 and 0.053 levels, against 0.236 and 0.151 unsmoothed (45 % and 35 %): about a
   fifth less than 1.0 s.
3. A diver turning from sand to blue water in about a second is followed within half a second; 4.0 s
   lags 0.85 s and smears the turn over 1.7 s.
4. The median makes a single corrupt or flash frame vanish, at no measured cost.

The comparison clips of section 3 use 1.0 s (fixed by the brief), so the owner sees the 1.0 s result
at CP2, not this recommendation. WP2.1 and CP2 decide.

## 5. Result: robust statistics for the N{} bounds (14.1, DR-14)

Ancuti 2018 (blue off), proxies, before any smoothing (`results.json` `robust`). Relative step and
CV are low / high bound; clipped is mean / max %; effect is mean / max levels; smallest range is
`GX011627` / `GX011625`; near-flat is the synthetic near-flat frame's range; floor counts the frames
of both excerpts where the 1e-6 floor triggered.

| Candidate | rel. step GX011627 | rel. step GX011625 | CV GX011627 | CV GX011625 | clipped GX011627 | clipped GX011625 | effect GX011627 | effect GX011625 | smallest range | near-flat | floor |
|---|---|---|---|---|---|---|---|---|---|---|---|
| min/max | 0.0477 / 0.0482 | 0.0636 / 0.0846 | 0.172 / 0.140 | 0.322 / 0.341 | 0.00 / 0.00 | 0.00 / 0.00 | 3.04 / 4.81 | 3.44 / 13.25 | 0.6010 / 0.1352 (frame 168) | 0.0279 | 0 |
| p0.5/p99.5 (default) | 0.0120 / 0.0122 | 0.0185 / 0.0218 | 0.183 / 0.188 | 0.383 / 0.402 | 1.00 / 1.00 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.2405 / 0.0147 (frame 178) | 0.0132 | 0 |
| p1/p99 | 0.0122 / 0.0127 | 0.0187 / 0.0219 | 0.192 / 0.200 | 0.397 / 0.418 | 2.00 / 2.00 | 2.00 / 2.00 | 0.81 / 1.03 | 1.48 / 3.45 | 0.2028 / 0.0110 (frame 178) | 0.0115 | 0 |
| p2/p98 | 0.0127 / 0.0132 | 0.0193 / 0.0215 | 0.207 / 0.218 | 0.408 / 0.435 | 4.00 / 4.00 | 4.00 / 4.00 | 1.95 / 2.47 | 3.77 / 7.01 | 0.1638 / 0.0085 (frame 178) | 0.0097 | 0 |
| trimmed mean +- 2.5 sd | 0.0141 / 0.0141 | 0.0192 / 0.0190 | 0.273 / 0.274 | 0.392 / 0.392 | 5.55 / 6.86 | 6.40 / 7.02 | 3.43 / 4.05 | 6.11 / 8.09 | 0.1381 / 0.0081 (frame 178) | 0.0100 | 0 |
| trimmed mean +- 3 sd | 0.0141 / 0.0141 | 0.0192 / 0.0190 | 0.273 / 0.274 | 0.392 / 0.392 | 3.24 / 4.60 | 5.12 / 5.62 | 2.62 / 3.43 | 5.35 / 6.50 | 0.1657 / 0.0097 (frame 178) | 0.0120 | 0 |

Reading:
- min/max jitters three to four times as much from frame to frame as any other candidate: relative
  step 0.048 against 0.012 on `GX011627`, 0.064 and 0.085 against 0.019 and 0.022 on `GX011625`. It
  follows single extreme pixels.
- Its lower CV over the excerpt is the scene drift, which every candidate follows. That is why the
  step, not the CV, is the stability figure here.
- The three percentile pairs jitter alike and clip exactly their tails. The trimmed forms jitter
  slightly more, clip a varying 3 to 7 %, and move the result by 2.6 to 6.1 levels on average.
- **DR-14 on real footage.** The last frame of `GX011625` (hazy, almost featureless water) has a
  default N{} range of 0.0147, against 0.24 on the textured `GX011627` and 0.0132 on the synthetic
  near-flat frame. The stretch there multiplies the high-pass by about 68.
- The 1e-6 floor triggered on no real frame and not on the near-flat synthetic one; only an exactly
  flat frame reaches it (range 3e-8 to 8e-8, `robust.synthetic`). The floor guards a division by
  zero, not the ill-conditioning DR-14 describes.

**Recommendation: keep the 0.5/99.5 percentiles (the default) and add a floor on the range (high
minus low) far above 1e-6, its value to be set from open-water and deep frames (WP1.4b, CP2).**
Grounds:
1. The default has the smallest frame-to-frame step of every candidate on both excerpts and clips a
   fixed 1 % by construction; no other candidate is more stable.
2. min/max is three to four times noisier; the trimmed forms are not more stable and change the
   look by several levels.
3. No candidate addresses the near-flat case: every candidate but min/max has its smallest range on
   frame 178 of `GX011625`, between 0.008 and 0.015; min/max's smallest (0.135, frame 168) is held up
   by single extreme pixels, the outlier problem. A floor on the range is the lever for DR-14.

This part does not set the floor: no default change, and no open-water or deep frame is sorted yet.

## 6. Proxy versus full frame (`GX011627`, raw statistics)

`results.json` `proxy_minus_full` (proxy minus full; mean signed / largest absolute):

| Statistic | Ancuti 2018 mean | max | 3C mean | max |
|---|---|---|---|---|
| `compensation_means.R` | -0.00000 | 0.00000 | -- | -- |
| `white_balance_gains.R` | -0.00020 | 0.00041 | +0.00010 | 0.00043 |
| `white_balance_gains.G` | +0.00007 | 0.00016 | +0.00033 | 0.00106 |
| `white_balance_gains.B` | +0.00008 | 0.00018 | -0.00045 | 0.00124 |
| `normalisation_bounds.low` | +0.02709 | 0.04661 | +0.02752 | 0.04681 |
| `normalisation_bounds.high` | -0.02522 | 0.04334 | -0.02748 | 0.04567 |
| `saliency_means.input1.L` | +0.00083 | 0.02679 | -0.00779 | 0.01948 |
| `saliency_means.input2.L` | -0.39688 | 0.63730 | -0.34475 | 0.55734 |
| `saliency_means.input2.a` | +0.03749 | 0.06972 | +0.02079 | 0.04124 |

- The area average keeps the channel means exactly (differences at float rounding).
- The white-balance gains agree to 0.0004 (Ancuti 2018) and 0.0012 (3C).
- **The N{} bounds do not.** The proxy's high-pass spread averages 0.328 against 0.381 on the full
  frame (14 % narrower; from `statistics-raw.json`). The full frame's high-pass holds detail and
  noise above the proxy's resolution, even though the blur scales with the short side.
- Rendering a full-resolution frame with bounds measured on its proxy therefore stretches input 2
  about 16 % harder than its own bounds would; the saliency reference of input 2 follows (0.4 in L).
- This extends WP1.2A's synthetic finding to real footage. It is an open question for WP2.1
  (section 8).

## 7. Stage definitions (plan section 9 row "Stage definitions per compensation method")

Proposed for IF-3 from these measurements. Every statistic measured was smoothed here without harm
(the column says what a smoothed stage holds).

| Method | Stage | Statistics (all smoothable) | Measured on | Invalidated by a change of |
|---|---|---|---|---|
| ancuti2018 | 1 compensation | R, G, B means; effective alpha per compensated channel | the source proxy | the means: nothing (source-only, cacheable, 7.3); alpha: `alpha`, the caps, `blue_compensation`, in closed form from the means and the source-only cap statistic `mean((1 - I_c) I_g)`, so no re-measure |
| ancuti2018 | 2 white balance | gray-world gains R, G, B; strength and the D99 clamp applied after smoothing (closed form) | the proxy compensated with smoothed stage 1 | stage 1's parameters (`alpha`, caps, `blue_compensation`, `method`); NOT `white_balance_strength` or `max_white_balance_gain` (closed form) |
| ancuti2018 | 3 fusion | N{} low and high; Lab mean of input 1 and of input 2 | the proxy corrected with smoothed stages 1 and 2 | everything above, plus `white_balance_strength` and `max_white_balance_gain` (the white-balanced image changes); N{} also by `sharpen_blur_fraction` and the two percentiles; input 1's Lab mean by `gamma`; input 2's by `sharpen_strength` and N{} |
| c3 | 1 white balance | gray-world gains R, G, B | the proxy compensated by 3C (local means only, no whole-frame statistic) | `kappa`, `lambda_`, `c3_strength`, `c3_kernel_fraction`, `c3_mask_threshold`, `c3_mask_smooth_fraction` |
| c3 | 2 fusion | as Ancuti 2018 stage 3 | the proxy corrected with smoothed stage 1 | as Ancuti 2018 stage 3, with the 3C parameters in place of stage 1's |

- A fourth stage for the saliency references (input 2's Lab mean measured on input 2 built with the
  SMOOTHED N{} bounds) is not indicated. The whole staged-versus-flat difference, which contains this
  in-stage effect and every other, is under a tenth of an 8-bit level (section 3).
- Live-preview recompute (7.3): stage 1's means are source-only and can be cached with the proxies.
  Every other statistic depends on parameters; a parameter change re-measures from the first stage
  it invalidates, within the smoothing window of the displayed frame (a 2.0 s window reaches 29
  frames each side at 29.97 fps).

## 8. Limits, deviations, open questions

- **Flicker measure limits** (section 2): drift is counted with jitter; a second-order content
  residue remains; means only. Not V3.
- **Excerpt edges:** 6 s excerpts with the end value held; the interior column is the edge-free
  comparison. The product smooths over the whole clip.
- **Unsmoothed clip against the smoothed ones:** the unsmoothed clip uses each frame's FULL-frame
  statistics (WP1.3's clip, the brief's definition); the staged and flat clips use PROXY statistics.
  So they differ by the smoothing AND by the proxy gap of section 6 (a stronger N{} stretch). Staged
  against flat is a clean comparison: both come from proxies.
- **Smoothing study scope:** the flicker of the 12 candidates is for Ancuti 2018 only (the render
  method); the staged and flat statistics and flicker are for both methods.
- **Open question for WP2.1, proxy gap:** N{} bounds measured on a 540-line proxy are 14 % narrower
  than on the 4K frame. Options: measure N{} at render resolution; scale the proxy bounds by a
  calibrated factor; or accept the proxy look as the definition. Not decided here.
- **Open question for WP2.1, smoothing alpha:** the effective alpha was smoothed as a value. The
  alternative is to smooth the means and the source-only cap statistic and derive alpha from them.
  The two are indistinguishable here (the cap never bound on shallow footage); WP1.4b's deep frames
  decide.
- **Devices:** every measurement and render ran on the RTX 4070. The identity (test 1) holds on each
  device separately, not across devices (CPU and GPU agree within WP1.2A's bounds).

## 9. Verification

- Gates on the worktree head: `uv run ruff check .` all checks passed; `uv run ruff format --check .`
  82 files already formatted; `uv run mypy` no issues in 18 source files; `uv run pytest -q -rs`
  539 passed, 0 skipped (FFmpeg on PATH, footage configured, GPU present); `-m gpu` 24 passed;
  `-m footage` 4 passed.
- Tests of this package (`tests/test_prototype_temporal.py`, the brief's numbering): (1) identity on
  CPU and GPU for Ancuti 2018 blue off and on and 3C, also after a JSON round trip, with a positive
  control per supplied field; (3) the 3-frame sequence, flat minus staged equal to the hand formula
  (-0.01115 on the red gain, staged higher); (4) every filter centred at every window, the window
  converted from seconds; (5) flicker zero on constant and positive on alternating sequences, and the
  content-cancellation control; (6) the candidates on `arange(1001) / 1000` and on a flat array;
  (7) the runner on 10 frames of `GX011628.MP4` writes its records. (2): the existing prototype and
  look-check tests are unchanged (`git diff 9ed1a1c..HEAD` touches no existing test file).
- Real-footage witness of the identity: section 3, `wp13_witness`.
- No file under the footage folder was written: every write goes through `OutputRoots.check`
  (`test_the_runner_writes_only_inside_its_folder`), and the runner's only FFmpeg outputs are the
  checked frame scratch folders and clips.
