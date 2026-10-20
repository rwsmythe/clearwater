# WP1.4b -- Gain-cap noise test and deep-frame statistics

**Spec:** v0.5.3. **Brief:** `docs/briefs/wp1.4b-brief.md` (FINAL, with amendment claim 10b,
`42662d2`). **Branch:** `wp1.4b` (base `db751cb`). **Instrument:** `tools/noise_experiments.py`,
`tools/camera_state.py`. **Records** (working folder, never committed): `work/wp1.4b/frames.json`,
`grid/*.json`, `grid.json`, `summary.json`, `index.html` (the crop page), `smoothing.json`,
`lighting-step.json`, `lighting-step-*.png`, `smoothing-alpha.png`, `quantised-regime.json`. Every figure below is read
from one of these records.

## Summary

- **Gate result 4 (D100): KEEP the caps.** At the default cap 2.0 the red cap binds on 1 of 8 deep
  frames and changes nothing measurable (output red noise within 0.015 code values of cap off).
  Tighter caps RAISE red noise wherever the source red has a baseline (8 of 8 deep frames on the
  red-lit tiles), as the spec expects. They LOWER it only where the source red is crushed to a
  near-constant (4 of 8 frames on the flattest tiles), because there the output red noise is
  green noise carried in by the compensation term, which the cap limits. There the source red reads
  below the quantisation floor; this is an exception to D100, not a contradiction of it. Totals
  with the camera's own red gain: Ancuti 4.2-13.8x, c3 3.2-5.1x (claim 7).
- **The clamp (D99):** 3.0 never binds on the deep frames under either method (1000 never binds
  either). Lowering it to 1.5 binds on 5 of 8 frames under Ancuti 2018, leaves a residual cast
  down to R/G 0.80, and cuts red noise by less than 1 % (median). Recommend keeping 3.0 for WP2.1.
- **N{} range floor (DR-14):** the measured ranges are 0.028 to 0.64. Recommend a floor of
  **0.02** (largest stretch 50x) as a collapse guard that binds on none of the measured frames.
- **Claim 10:** smooth the capped alpha as a value (A, what `temporal` does today). Deriving
  it from smoothed means (B) gives 24 % more flicker (0.483 against 0.388).
- **Claim 10b:** the step at about 1 s is **genuine, not an edge effect** of the 6 s excerpt.
  Widening the excerpt backwards by 3 s moves no applied gain by more than 0.014. Neither a
  window reset at the step nor a 0.5 s window makes the rendered step smaller, and both add
  flicker.
- **The noise measure** is Immerkaer's estimator, as ruled after the STOP. Donoho's median
  collapses on these frames: up to 99 % of the HH1 coefficients in the flat tiles are exactly 0.
  On deep 8-bit HEVC frames, what the measure reads is mostly compression artefact carried into
  red, not sensor grain. The crops are the direct evidence.

## Claim 1 -- the default flip

`b23bad9` changes `Params.method` to `"c3"`, alone, with the docstring sentence "Default `"c3"`:
spec v0.5.3 D16 (amended after CP2 2026-10-19)". `fddc4e3` adds the pins and guards. Pinning
rule: a test site is pinned when its `Params` reaches a function that reads `params.method`
(`pipeline.correct`, `temporal.measure` / `statistics_of` / `analyse_staged` /
`white_balanced_high_pass`, the clip pipeline, `run.py`). Each pin only names
`method="ancuti2018"` (or `--method ancuti2018`); no expected value changed.

| File | Sites | Reason |
|---|---|---|
| `tests/test_lookcheck.py` | 2 | bound-flag test failed after the flip |
| `tests/test_prototype_backend.py` | 5 | 1 `run.py` argv line (its 3 parametrised cases failed); 4 reach `correct` |
| `tests/test_prototype_pipeline.py` | 9 | 3 `run.py` argv (failed); 6 reach `correct` |
| `tests/test_prototype_clip.py` | 20 | every clip-pipeline site (3 as `dataclasses.replace(Params.neutral(), method="ancuti2018")`) |
| `tests/test_prototype_temporal.py` | 28 | staged and statistics sites (they would silently have run c3's 2-stage chain); 3 of them (the `VARIANTS` registry's two Ancuti entries and the staged-reach loop) were found by Reviewer A round 1 (CR-01) and pinned in the round's fix, with a guard test |
| `tests/test_lookcheck_deep.py` | 1 | reaches `correct` |
| `tools/prototype/run.py` | help text | follows `Params()` (c3); the usage and `--method` / `--blue` help name c3 as the default and list ancuti2018 / ancuti2018-blue (guard ii) |

No tool needed pinning. `statistics_experiments.py` (the `METHODS` dict), `clip.py` (`--method`
default `"ancuti2018"`), `bench.py` (`--method` required) and `pack.py` (every variant) already
name the method. New guards: `test_the_default_method_is_c3`,
`test_run_without_a_method_follows_the_params_default`,
`test_run_help_names_c3_as_the_default_and_lists_the_options`. Open item, not this package's to
edit: the `Params.neutral()` docstring ("The method stays the default; `replace(..., method="c3")`
is neutral too") is still true but now reads oddly.

## Claims 2 and 2a -- frames and camera state

The 8 deepest frames of `work/wp1.3d/deep-frames.json`, its 4 open-water candidates and the
shallow reference (`GX011627` at 205205 ticks), all at 3840x2160 as 16-bit PNG. Each pts is
checked against the list. Camera state is the nearest-in-time GPMF sample: the six keys are
decoded and every other key is skipped by length, undecoded. Timing rule: sample `i` of `n` in
a stream of duration `T` sits at `i * T / n`; ISOE is one sample per frame. The gpmd extracts
stay in `work/wp1.4b/gpmd/` and are never committed.

| Deep frame | D | ISOE | SHUT (ms) | WRGB red |
|---|---|---|---|---|
| GX011600_0665.031 | 0.209 | 100 | 2.09 | 4.85 |
| GX011600_0965.031 | 0.236 | 156 | 2.25 | 3.69 |
| GX011600_0815.014 | 0.258 | 100 | 0.94 | 3.69 |
| GX011591_0095.028 | 0.296 | 793 | 8.33 | 3.78 |
| GX011600_0975.007 | 0.362 | 100 | 1.32 | 3.93 |
| GX011600_0125.025 | 0.365 | 100 | 1.52 | 3.21 |
| GX011593_0065.032 | 0.367 | 177 | 0.92 | 3.95 |
| GX011600_0275.008 | 0.369 | 100 | 2.21 | 3.12 |
| shallow GX011627@205205 | -- | 100 | 3.75 | 2.54 |

## Claim 4 -- the noise measure (as ruled after the STOP)

**What happened.** The brief's primary measure was Donoho's `median(|HH1|) / 0.6745` on the
fixed flat tiles. It read exactly 0 for the source on all 8 deep frames, because 63-99 % of the
HH1 coefficients in those tiles are exactly 0: 8-bit HEVC has flattened them. The orchestrator
ruled on the STOP (ledger):

- **Primary:** Immerkaer's fast estimator per 64x64 tile, `sqrt(pi/2) / (6 (W-2)(H-2)) * sum |I * N|`,
  taken as the median over the tiles.
- **Cross-check:** Donoho, recorded beside it with the fraction of exactly-zero HH1 coefficients.
- **Tile sets.** Two fixed sets, both formed from the SOURCE and used for every setting of a
  frame:
  - `flat`: the 25 % of tiles with the lowest luma gradient energy, as the brief defines it.
  - `red_lit`: the 25 % flattest of the tiles whose source red mean is at least 16/255. A frame
    gets no `red_lit` set when the selection holds fewer than 8 tiles. No frame fell short (the
    smallest set has 146 tiles).
- **Comparison.** Settings are compared on the absolute output `sigma_R` in 8-bit code values.
  `sigma_out / sigma_src` is given only where the source figure is above 0.

**Validation** (`tests/test_noise_experiments.py`, all passing):

1. A known Gaussian sigma of 0.002, 0.01 or 0.03 is recovered within 10 % on a smooth gradient,
   by both estimators.
2. A noise-free gradient reads below 0.0005.
3. A sharp edge does not inflate the estimate (the selection excludes edge tiles).
4. A gain `g` scales the estimate by `g` within 5 %.
5. **The regime that defeated Donoho:** Gaussian noise of 0.25 code values quantised to 8 bits.
   More than 50 % of the HH1 coefficients are 0, and Donoho reads exactly 0. Immerkaer stays
   within 15 % of the true sigma of the quantised error (3 seeds).
   - Why 15 %: Immerkaer's `sqrt(pi/2)` conversion is exact for a Gaussian mask response.
     Mostly-zero quantised noise gives a heavier-tailed response, so the estimator under-reads,
     by 9-11 % here over 20 seeds (`quantised-regime.json`).
   - The bias grows with the zero fraction: -22 to -25 % at 70-71 % zeros and -40 to -44 % at 84-85 % on a flat
     field. A second test therefore pins only the ORDER of five noise levels in that deepest
     regime. Immerkaer keeps the order there; Donoho reads only 0 or the quantisation level.
   - The renders are float, so a pure gain scales Immerkaer exactly. The bias therefore does
     not distort amplifications.

**Donoho as the cross-check.**

- On the deep outputs it reads 0.000-0.010 code values on the flat tiles: collapsed.
- Its source reading is either 0 or 0.738, the quantisation level (half a code value over
  0.6745). This includes the shallow reference's 0.738, against Immerkaer's 0.447.
- It ranks the 25 settings differently from Immerkaer on 7 of the 9 frames: 4-60 of 300 pairs
  discordant, with 28-200 tied pairs. It cannot validate a ranking on these frames.
- The two tile sets also rank the settings differently on 5 of 9 frames (up to 116 of 300
  pairs, on GX011600_0665). The cap acts in opposite directions on them (claim 7).

**Limits.**

- The source is 8-bit HEVC. On deep frames the source red in the flattest tiles is often a
  single value per tile. Its Immerkaer figure is 0.000-0.031 code values on 4 frames, against
  0.12-0.20 for green.
- **The quantisation floor.** Immerkaer, too, reads about 0 on a tile that HEVC has flattened to
  a constant. Where BOTH estimators read below 0.05 code values (`QUANTISATION_FLOOR_8BIT`, a
  twentieth of the 8-bit step), the reading means "below the quantisation floor", never "no
  noise".
  - This applies to the source red on the flat tiles of 0665, 0815, 0965 and 0975.
  - It applies to the corrected red on those flat tiles under c3 and, on 0665, 0815 and 0965,
    under Ancuti cap 0.5 at some clamp.
  - It applies to nothing on the `red_lit` tiles.
  - The crop page marks such readings. A 0.000 below is such a reading.
- That is why the red-baseline set (`red_lit`, source red mean at least 16/255) leads every table
  below: it is the set on which the grid is readable.
- So what the measure reads in the corrected red there is mostly green-channel noise and
  compression structure carried into red, then stretched. It is not sensor grain.
- The estimate is spatial, not temporal.
- The crops are the owner's direct evidence.

## Claim 7 -- Gate result 4 (D100)

Ancuti 2018 with blue off at the default clamp 3.0, and 3C as the reference. Each cell is the
median over the 8 deep frames, with [min-max]. Amplification is over frames whose source figure
is above 0 (n given). The green fraction is the share of the compensated red mean that came
from the green term.

**`red_lit` tiles** (a red baseline exists):

| Setting | sigma_R out (8-bit) | amplification (n) | red WB gain | total red gain (context) | residual R/G | green fraction | cap bound | ISOE (context) | camera WRGB red (context) |
|---|---|---|---|---|---|---|---|---|---|
| cap off | 0.736 [0.539-0.993] | 2.43 [1.64-4.50] (8) | 1.52 [1.36-2.02] | 5.98 [4.24-7.64] | 1.00 [0.94-1.04] | 0.46 [0.36-0.68] | 0/8 | 100 [100-793] | 3.73 [3.12-4.85] |
| cap 2.0 (default) | 0.736 [0.553-0.993] | 2.43 [1.64-4.50] (8) | 1.54 [1.36-2.02] | 5.98 [4.24-7.68] | 1.00 [0.94-1.04] | 0.46 [0.36-0.67] | 1/8 | 100 [100-793] | 3.73 [3.12-4.85] |
| cap 1.0 | 0.783 [0.652-0.993] | 2.50 [1.64-4.50] (8) | 1.72 [1.36-2.21] | 6.55 [4.24-10.72] | 1.01 [0.94-1.05] | 0.46 [0.36-0.50] | 3/8 | 100 [100-793] | 3.73 [3.12-4.85] |
| cap 0.5 | 0.938 [0.717-1.035] | 2.84 [1.78-5.15] (8) | 1.97 [1.56-2.84] | 7.60 [4.87-13.75] | 1.02 [0.93-1.08] | 0.33 [0.33-0.33] | 8/8 | 100 [100-793] | 3.73 [3.12-4.85] |
| c3 | 0.481 [0.370-0.718] | 1.53 [1.15-3.25] (8) | 1.05 [1.02-1.07] | 3.95 [3.20-5.10] | 1.00 [0.99-1.00] | n/a | n/a | 100 [100-793] | 3.73 [3.12-4.85] |
| shallow, every Ancuti cap | 0.565 | 1.20 | 1.03 | 2.61 | 1.01 | 0.05 | 0/1 | 100 | 2.54 |
| shallow, c3 | 0.549 | 1.16 | 0.99 | 2.50 | 1.00 | n/a | n/a | 100 | 2.54 |

- The context columns are the same 8 frames in every row; per frame they are in the claim 2a
  table.
- **Total red gain** is the camera's applied white-balance red gain (WRGB red, already baked into
  the 8-bit source) times our white-balance red gain, per frame (`summary.json`,
  `total_red_gain`). It is the gain the eye and the artefacts see.
- Every cap setting sits on top of the camera's 3.1-4.9x. At cap 0.5 the total reaches 13.75x on
  GX011600_0665 (4.85 x 2.84).

**`flat` tiles** (the brief's set):

| Setting | sigma_R out (8-bit) | amplification (n) | red WB gain |
|---|---|---|---|
| cap off | 0.324 [0.084-0.999] | 3.77 [1.66-132.79] (6) | 1.52 |
| cap 2.0 (default) | 0.324 [0.084-0.999] | 3.77 [1.66-127.72] (6) | 1.54 |
| cap 1.0 | 0.324 [0.075-0.999] | 3.77 [1.66-85.92] (6) | 1.72 |
| cap 0.5 | 0.296 [0.043-1.036] | 3.86 [1.76-55.34] (6) | 1.97 |
| c3 | 0.127 [0.000-0.724] | 1.51 [1.16-3.27] (6) | 1.05 |
| shallow, every Ancuti cap / c3 | 0.536 / 0.514 | 1.20 / 1.15 | 1.03 / 0.99 |

- The c3 minimum of 0.000 is below the quantisation floor (Limits, claim 4), as is the cap-0.5
  minimum of 0.043 (GX011600_0815).
- The flat-set amplifications above 50 come from source figures of 0.002-0.03 code values, which
  are below the quantisation floor. They are ratios over almost nothing; the absolute column is
  the comparison.

**Cap off against cap 0.5, per deep frame** (relative change of the output `sigma_R`):

| Frame | red gain off -> 0.5 | `red_lit` | `flat` |
|---|---|---|---|
| GX011600_0665.031 | 1.53 -> 2.84 | +74.7 % | -58.3 % |
| GX011600_0965.031 | 1.50 -> 2.29 | +35.2 % | -58.2 % |
| GX011600_0815.014 | 1.70 -> 2.32 | +18.1 % | -49.5 % |
| GX011591_0095.028 | 2.02 -> 2.09 | +1.7 % | +0.6 % |
| GX011600_0975.007 | 1.44 -> 1.73 | +10.8 % | -26.6 % |
| GX011600_0125.025 | 1.41 -> 1.59 | +8.0 % | +6.0 % |
| GX011593_0065.032 | 1.64 -> 1.85 | +3.7 % | +3.7 % |
| GX011600_0275.008 | 1.36 -> 1.56 | +5.2 % | +2.8 % |

**Does it agree with the spec's expectation?** The spec expects a tighter cap to raise the
white-balance gain on the noisy red, and so to raise noise.

- **Yes, wherever the source red has a baseline:** 8 of 8 frames on the `red_lit` tiles (+1.7 %
  to +74.7 %).
- **No, only where the source red is crushed:** on the `flat` tiles of the 4 frames whose source
  red there is below the quantisation floor (0665, 0965, 0815, 0975), the tighter cap lowers the
  output red noise by 27-58 %. On 0815 the cap-0.5 output itself falls below the floor (0.043).
- **Spec-bearing?** The grid does NOT confirm the early signal, a tighter cap lowering red noise,
  as a general result. D100's expectation holds wherever red has a baseline. The opposite
  direction is confined to crushed-red regions, where the source red reads below the
  quantisation floor.
  - This is reported for CHARC and the WP1.6 gate as an exception, with its mechanism. It does
    not contradict D100.
- **The mechanism the data support.** Ancuti's compensation adds `alpha (G-mean - R-mean)(1 - R) G`
  to red. Where the source red is a constant, the output red's noise is that term's green noise:
  - It scales with alpha. On 0665, alpha goes 0.94 -> 0.235 and `sigma_R` 0.195 -> 0.085, while
    the red gain rises 1.58 -> 2.84 and multiplies a red with almost no noise of its own.
  - The green fraction falls from 0.46-0.68 to 0.33.
- **The earlier early signal** ("a tighter cap lowers output red noise") is confirmed only for
  crushed-red regions, not in general.

**Does the amplification track the camera's ISO or the pipeline's own red gain?** Spearman rank
correlation over the deep frames, Ancuti default:

| Tile set | n | pipeline red gain | N{} stretch | ISOE | camera WRGB red |
|---|---|---|---|---|---|
| `red_lit` | 8 | 0.83 | 0.95 | 0.60 | 0.81 |
| `flat` | 6 | 0.43 | 0.71 | -0.03 | 0.89 |

- The amplification tracks the pipeline's own gains, the N{} stretch most closely of all. It
  does not track the ISO: 5 of the 8 frames are at ISO 100 and they span amplifications from 1.64
  to 3.03.
- The camera's WRGB red gain also correlates, because it grows with red loss, just as the
  pipeline's red gain does. With 8 frames these are collinear and cannot be separated.

**Recommendation: KEEP the caps** (the decision is the gate's at WP1.6; dropping them is a spec
change and the owner's).

- At the default 2.0 they are nearly inert on deep footage: they bind on 1 of 8 frames, the noise
  stays within 0.015 code values (largest 0.0147, `red_lit`), and the cast is unchanged.
- They remain D100's only fidelity lever: tighter caps cap the green-derived share at 0.33.
- Tightening them is NOT a noise control. On every region with a red baseline it raises red
  noise, as the spec expects.
- 3C, now the default, has no caps. It is the lowest-noise setting on every deep frame:
  `red_lit` median 0.481 against 0.736.

## Claim 5 -- residual cast

The residual R/G and B/G are within 0.93-1.08 for every cap at the default clamp (tables
above). The caps barely move the gray-world residual, because the white balance restores the
means whatever the cap did. Only the clamp leaves a cast (claim 8).

## Claim 8 -- the clamp on deep footage (D99, 14.1)

Medians over the 8 deep frames with [min-max]; amplification over the frames whose source
figure is above 0 (all 8 on `red_lit`, 6 on `flat`).

| Setting | clamp bound (red) | sigma_R `red_lit` | amplification `red_lit` | sigma_R `flat` | amplification `flat` | residual R/G | residual B/G |
|---|---|---|---|---|---|---|---|
| c3, clamp 1.5 | 0/8 | 0.481 [0.370-0.718] | 1.53 [1.15-3.25] | 0.127 [0.000-0.724] | 1.51 [1.16-3.27] | 1.00 [0.99-1.00] | 1.00 [0.99-1.01] |
| c3, clamp 2 | 0/8 | 0.481 [0.370-0.718] | 1.53 [1.15-3.25] | 0.127 [0.000-0.724] | 1.51 [1.16-3.27] | 1.00 [0.99-1.00] | 1.00 [0.99-1.01] |
| c3, clamp 3 | 0/8 | 0.481 [0.370-0.718] | 1.53 [1.15-3.25] | 0.127 [0.000-0.724] | 1.51 [1.16-3.27] | 1.00 [0.99-1.00] | 1.00 [0.99-1.01] |
| c3, clamp 5 | 0/8 | 0.481 [0.370-0.718] | 1.53 [1.15-3.25] | 0.127 [0.000-0.724] | 1.51 [1.16-3.27] | 1.00 [0.99-1.00] | 1.00 [0.99-1.01] |
| c3, clamp 1000 | 0/8 | 0.481 [0.370-0.718] | 1.53 [1.15-3.25] | 0.127 [0.000-0.724] | 1.51 [1.16-3.27] | 1.00 [0.99-1.00] | 1.00 [0.99-1.01] |
| Ancuti cap 2, clamp 1.5 | 5/8 | 0.731 [0.520-0.939] | 2.28 [1.64-4.26] | 0.279 [0.075-0.950] | 3.34 [1.66-119.77] | 0.96 [0.80-1.01] | 1.00 [0.98-1.01] |
| Ancuti cap 2, clamp 2 | 1/8 | 0.736 [0.553-0.993] | 2.43 [1.64-4.50] | 0.322 [0.084-0.999] | 3.76 [1.66-127.72] | 1.00 [0.93-1.04] | 1.00 [0.98-1.01] |
| Ancuti cap 2, clamp 3 | 0/8 | 0.736 [0.553-0.993] | 2.43 [1.64-4.50] | 0.324 [0.084-0.999] | 3.77 [1.66-127.72] | 1.00 [0.94-1.04] | 1.00 [0.98-1.01] |
| Ancuti cap 2, clamp 5 | 0/8 | 0.736 [0.553-0.993] | 2.43 [1.64-4.50] | 0.324 [0.084-0.999] | 3.77 [1.66-127.72] | 1.00 [0.94-1.04] | 1.00 [0.98-1.01] |
| Ancuti cap 2, clamp 1000 | 0/8 | 0.736 [0.553-0.993] | 2.43 [1.64-4.50] | 0.324 [0.084-0.999] | 3.77 [1.66-127.72] | 1.00 [0.94-1.04] | 1.00 [0.98-1.01] |

The `flat` minima of 0.000 (c3) are below the quantisation floor; the `red_lit` columns lead.

- The clamp at 1000 never bound.
- Under 3C the red white-balance gain stays at or below 1.07, and no clamp in the grid ever
  binds.
- **Recommendation for WP2.1: keep 3.0** (no default change here).
  - It binds on none of these deep frames under either method, so it costs no fidelity. It
    leaves headroom over the largest red gain seen (2.84, Ancuti cap 0.5 on 0665).
  - On this evidence the clamp is not an effective deep-water noise control. At 1.5 it cuts the
    median red noise by under 1 %, while leaving a visible residual cast (R/G 0.80 on
    GX011591_0095).

## Claim 9 -- the N{} range floor (DR-14)

N{} range (high - low) and the stretch (1 / range), at the defaults:

| Frames | Ancuti 2018 range | stretch | c3 range | stretch |
|---|---|---|---|---|
| deep (8) | 0.350 [0.129-0.638] | 2.88 [1.57-7.75] | 0.355 [0.110-0.579] | 2.82 [1.73-9.07] |
| open water (4) | 0.086 [0.031-0.144] | 11.6 [6.95-32.6] | 0.085 [0.028-0.133] | 11.7 [7.51-36.3] |
| shallow (1) | 0.471 | 2.12 | 0.474 | 2.11 |

The smallest range, 0.028 (c3, GX011593_0255.021), stretches 36x. It takes that frame's source
red noise of 0.13 code values to 1.46 in the output, on the `flat` tiles.

**Proposal: a floor of 0.02** (largest stretch 50x). It is far above 1e-6, as WP1.4 asked, and
below every range measured here, so it binds on none of these frames. It acts only as the
collapse guard DR-14 needs. Whether a higher floor is wanted is a look decision, which needs
open-water crops: these were not in this package's crop set. For example, 0.05 (stretch at most
20) would bind on 1 of the 4 open-water frames. No default change.

## Claim 10 -- the capped alpha under smoothing

Data: the WP1.3D deep clip (179 frames, GX011600 from 662.06 s), Ancuti at the defaults, 2.0 s
centred Gaussian, staged, on the 540 NumPy proxy. The per-frame cap binds on **46 of 179 frames
(25.7 %)**, above the 10 % floor, so the claim ran.

| | (A) alpha smoothed as a value | (B) alpha derived from smoothed means and cap statistic |
|---|---|---|
| frames with alpha below 0.999 | 93 | 33 |
| minimum alpha | 0.673 | 0.712 |
| flicker (8-bit levels) | **0.388** | 0.483 |

The 0.999 threshold counts the frames where the cap acts. A's Gaussian also leaves the far
frames within 1e-15 of 1, so a strict "below 1" counts all 179 frames.

- `|alpha_A - alpha_B|`: mean 0.033, max 0.291 (frame 53).
- Rendered proxies `|A - B|`: mean 1.32 levels, the worst frame 11.9.
- Why B behaves differently: it applies the cap's `min()` after smoothing. Its alpha therefore
  stays at 1 longer, then dips later and more steeply, which re-introduces the kink that
  smoothing removed.
- **Recommendation: keep (A)**, which is what `temporal` does today. The question closes for
  WP2.1 on this clip; one clip is the evidence.

## Claim 10b -- the lighting step in the deep clip

- **Where the step is.** Detector: the largest two-sided difference of 0.5 s means of the source
  luma. It puts the step at frame 27, **0.90 s into the excerpt** (pts 662.962 s). That matches
  the owner's "about 1 s".
- **The source across the step** (+-1 s): luma +49.9 levels, R -37.6, G +70.2, B +106.0. The
  scene goes from reddish rock to blue water.
- **Raw statistics across the step**, from WP1.3D's recorded raw series (staged: each stage
  measured with the smoothed earlier stages):
  - Ancuti: red white-balance gain +0.51 and alpha -0.49 (the cap starts binding about 0.6 s
    after the luma step, at frame 46). Measured with each frame's own alpha instead, the red
    gain steps by +0.68.
  - c3: red gain +0.03 and blue gain -0.05 (the same under both measurements).
  - Both: the N{} stretch rises by about 1.0, from 2.9 to 3.8.
- The recomputed 2 s series equal WP1.3D's recorded smoothed series exactly (largest difference
  0 for every traced statistic), so the applied figures below are the rendered clip's.

**Edge effect or genuine step? GENUINE.** The excerpt was widened backwards by 3 s (90 frames
re-extracted by pts, contiguous with the excerpt). That is more than the 2 s window's 1 s reach.
The analysis was then re-run.

- Over the excerpt's first second, the largest change in any applied value is: red gain 0.014,
  other gains 0.005 or less, N{} bounds 0.0022 or less, stretch 0.031.
- After the first second, the changes are 0.0003 or less (the largest is the stretch's
  0.00023, Ancuti).
- The applied step across the cut is unchanged (Ancuti red gain +0.407 narrow, +0.393 wide).
- The flicker is unchanged: 0.388 against 0.389 (Ancuti), 0.097 against 0.097 (c3).
- So the truncated window at the excerpt's start is not what the owner saw. The step is the
  scene's, and the correction follows it.

**What the correction does to the step.** Rendered frame means against the source's, change
across +-1 s, 2 s window:

| Method | R | G | B | luma |
|---|---|---|---|---|
| c3 | 1.25x | 0.64x | 0.44x | 0.92x |
| Ancuti | 1.13x | 0.79x | 0.55x | 1.07x |

- The rendered luma step matches the source's (0.92-1.07x).
- The red fall is larger than the source's (1.13-1.25x), while the green and blue rises are
  smaller.
- The applied N{} stretch rises by about 0.9 (+32 %) across the step, and Ancuti's red gain by
  +0.41 (+32 %).

**The two remedies**, on the widened sequence, evaluated on the original 179 frames:

| Option | c3 flicker | c3 peak step | Ancuti flicker | Ancuti peak step | applied red gain change (Ancuti) | rendered luma / source |
|---|---|---|---|---|---|---|
| 2 s (as rendered) | 0.097 | 0.75 | 0.388 | 3.78 | +0.407 | 0.92 / 1.07 |
| (a) 2 s, reset at the detected step | 0.099 | 2.30 (at the step) | 0.394 | 3.79 | +0.392 | 0.92 / 1.07 |
| (b) 0.5 s | 0.163 | 1.49 | 0.478 | 11.61 | +0.640 | 0.92 / 1.00 |

- **(a) The reset** leaves the size of the step unchanged and concentrates the statistics'
  change into one jump at the step: c3's peak per-step flicker triples.
- **(b) The 0.5 s window** smooths less: Ancuti's red gain step grows from +0.41 to +0.64.
  That is above the recorded staged raw step (+0.51) and close to the own-statistics step
  (+0.68), because the shorter window also smooths the alpha that the white balance is measured
  after. It adds 68 % (c3) and 23 % (Ancuti) flicker, and Ancuti's peak per-step flicker is
  three times higher.
- **Neither remedy makes the step materially smaller.**
  - The reset changes no rendered ratio.
  - The 0.5 s window brings Ancuti's luma ratio from 1.07 to 1.00, and leaves c3's at 0.92.
    In exchange, Ancuti's red-gain step grows to +0.64 and its flicker rises.
  - c3's rendered luma step is smaller than the source's under every option (0.92x).
  - On this clip the 2 s window remains the better of the three: it has the lowest flicker and
    the lowest peak per-step flicker.
- The visible difference from the source is in colour: red falls further, and the stretch rises.
  Softening that is a temporal-design question for Phase 2, not a smoothing-window one.
- The 2 s default stays PROVISIONAL per DR-25(3).
- For DR-25(3): on this clip, the start-edge effect of the staged 2 s analysis is confined to the
  first second and does not change the flicker figure. The end edge was not widened.

## What the owner should look for on the crop page (`work/wp1.4b/index.html`)

The page has 9 frames (8 deep, 1 shallow). Each frame has a flat and a textured 512x512 crop at
100 %. The columns are the source and 7 settings, each shown as RGB and as the red channel alone.
Each caption gives `sigma_R` on both tile sets, the red gain, and what bound.

1. **The red-channel row of the flat crops** on the four crushed-red frames (0665, 0965, 0815,
   0975):
   - The source red is near-black and featureless there.
   - Look at what texture appears in the corrected red: green-channel grain and HEVC block
     structure carried across.
   - Compare cap off, cap 2 and cap 0.5. The tighter cap should look calmer there.
2. **The textured crops**, where red has a baseline: cap 0.5 should look grainier in red than
   cap off.
3. **c3 against Ancuti:** c3 should look the calmest in red on every frame.
4. **Whether any of these differences is visible at 100 %:** the measured figures are fractions
   of a code value.

## Deviations and open items

1. **The noise measure.** It is the ruled Immerkaer-primary measure, not the brief's Donoho, and
   it adds the `red_lit` set (STOP and ruling: ledger).
   - The "fewer than 8" bar is applied to the SELECTED set, with the eligible count recorded
     beside it.
   - Open-water frames get no crops, as the brief defines (claim 6 names deep and shallow).
2. **Extra camera-state context.** SHUT is shown as context. All six keys are read; YAVG and
   UNIF are in `frames.json` only.
3. **Two docstrings in other packages' files are stale after the flip.** The brief's lock
   allows only pinning edits there, so they are raised, not fixed:
   - The `Params.neutral()` docstring reads oddly.
   - `tools/statistics_experiments.py:1028` (`render_clips`) says the frames are corrected at
     "``Params()`` defaults (``ancuti2018``, blue off)". The code pins Ancuti through
     `METHODS[RENDER_METHOD]`, so only the sentence is stale (Reviewer A round 1, CR-04).
4. **Claim 10b's widened excerpt** is a new 3 s extract at the 540 proxy. It is cached in
   `work/wp1.4b/clip/lead-in.npy`; the full-resolution PNGs were deleted once proxied.
5. **Open question for the dispatcher: `tools/prototype/clip.py --method`** (Reviewer A round 2,
   CR-02).
   - The tool's `--method` defaults to `"ancuti2018"`, a pre-existing explicit default, and its
     help does not name c3.
   - Read literally, guard (ii) ("every CLI help text show c3 as the default") covers it. But
     claim 1 names `clip.py` among the tools that pin `ancuti2018` so that a re-run reproduces
     the reports.
   - Changing its default or help text is more than naming the method in another package's
     file, so it is left as it is, pending a ruling.
