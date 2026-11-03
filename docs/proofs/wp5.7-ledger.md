# WP5.7 halo investigation -- cell ledger

Cell: implementer-opus-high (Claude). Brief `docs/briefs/wp5.7-brief.md` (FINAL at `717265c7`);
dispatch `clearwater-review-evidence/wp5.7/cell/dispatch-1.md` (Part 1). Worktree
`.worktrees/wp5.7`, branch `wp5.7`, base `3de1ef68`. Outputs under the working folder
`work/wp5.7/` (resolved through `tools/local_config`).

## Round 0

The brief's design read against the code at `3de1ef68`:

1. `methods/fusion.py` `fusion_inputs` (:138-181) is spec 6.2 step 3 as written: input 2 =
   `clip(I + s * ((I + N{I - G*I}) / 2 - I))`, `N{x} = clip((x - low) / (high - low), 0, 1)` on
   SUPPLIED bounds, widened to `NORMALISATION_RANGE_FLOOR = 0.02` (:64, AD-4 / DR-14) when
   closer. The bounds are measured by `normalisation_bounds` (:101) on the ANALYSIS PROXY
   (AD-4): the photo path block-means to a short side of about 540 px (`analysis/proxy.py:60`).
2. `weight_maps` (:293-354) is step 4 as written: `W_k = W_L + W_S + W_Sat`,
   `Wbar_k = (W_k + delta) / (sum W + K delta)`, delta = `weight_delta` (default 0.1, the paper's).
3. `multiscale_fusion` (:357-410) is step 5: `pyramid_levels` (`core/ops.py:64`) halves while the
   short side stays at least `pyramid_min_level_size` (16): 7-9 levels on the six items, coarsest
   level 17-24 px, one coarsest pixel = 64-256 source px.
4. `ancuti_fusion.render` (:245-298) order: compensate, white balance, `fusion_inputs`,
   `weight_maps`, `multiscale_fusion`, `blend_with_original`. `headless_export` drives
   `jobs/export.py`: photos measure every stage on the block-mean proxy and render at full
   resolution (:756-797); videos run `AnalysisEngine` and render each frame from
   `smoothed_record` (:1083-1102). The probe follows both paths; every rendered frame's `output`
   equals `render`'s bit for bit (`render_check_equal` true on all 112 rendered frames: 3
   photos, 109 video frames).
5. No implementation divergence from spec 6.2 / 6.6 found in the reading (no outcome-B
   candidate from the code alone).
6. Q1 (band statistics plus crops; no owner viewing): accepted. Q2 (photos first): accepted; the
   photos were run first, then the three videos, because the dispatch's Part 1 item 3 names all
   six. Q3: Part 3, no comment.
7. Shipped defaults used (the CP5 pairs: `headless_export` records `parameters_from: defaults`,
   method `c3`, all four groups): sharpen_strength 1.0, sharpen_blur_fraction 0.005,
   normalisation 0.5 / 99.5, gamma 1.5, laplacian_fraction 0.001, saliency_blur_fraction 0.003,
   weight_delta 0.1, pyramid_min_level_size 16, blend 0, white_balance_strength 1, max gain 3.
8. Time mapping (not a dispute): the compilation's CP5 pair was rendered from the pack's EXCERPT
   (`work/wp5.3/records/V-Z-excerpts.json`: actual start 70.904167 s, 31.1311 s long; the pair
   clip is 31.13 s), so the owner's "about 27 seconds" is excerpt time, source time about 97.9 s.
   The probe reads that excerpt in place (read-only) so the analysis input is the one the pack
   analysed. GX011627 was whole (22.72 s); IMG_6738's pair is the whole 1.63 s clip.
9. The owner's "halo around turtle on the right side" (IMG_6739) is read as the turtle that sits
   on the right of the frame; lines on its outline (shell edge, flipper) and one on its right
   flank (which has no clean edge: see the table).

No STOP: no Q disputed.

## Part 1

### Built

- `tools/halo_probe.py`: the instrument. `staged_render` yields every 6.2 intermediate
  (source, compensated, balanced, high_pass, stretched N{}, input1, input2, the three weights
  and Wbar of each input, the counterfactual single-scale blend `naive`, fused, output) through
  the product's own functions in `render`'s order, then the attribution terms
  `collapse(G_l{Wbar_k} * L_l{I_k})` per input k and level l (they sum to the fused image).
  Per line: profiles of Y, R, G, B at 1 px steps (half width 4, bilinear); two metrics:
  `water` (the table's: the line STARTS in open water; the start side's deviation from its
  linear plateau fit, over the signed contrast, minus the source's; positive = outward ring,
  negative = inward glow; FWHM and the run above the threshold) and `two_sided` (overshoot /
  undershoot against both plateau fits). Threshold 10 % of the edge contrast; a source contrast
  under 0.02 is flagged `weak_edge`. The record also carries the N{} bounds used and the bounds
  the full-resolution image would give (a diagnostic). 16-bit PNG crops per stage, 8-bit marked
  views, one JSON per run. Writes refused inside the footage folder (`write_target_refusal`).
- `tests/test_tools_halo_probe.py`: 17 parallel-leg tests, CPU, synthetic. Each band test has a
  twin of the other sign: a clean step and a clean disc on a strong gradient give no band
  (< 0.02), the unsharp-masked ones give the analytic overshoot (C (1 - Phi(0.5 / sigma)),
  within 8 %) and a FWHM of about 0.73 sigma, doubling with sigma; an inward glow is signed
  inward; a constant-plateau reading of the gradient is shown to be wrong; the staged render
  equals `render` and its terms add up to the fused deviation; the CLI writes 16-bit crops,
  refuses an overwrite, a footage-folder output, a bad line, method or region. A metric that
  measured nothing fails the unsharp twins; one that always measured a band fails the clean
  twins (by construction of the asserts; no separate mutation run was made).

### Commands (from the worktree, Git Bash, `PYTEST_ADDOPTS` unset)

| Command | Exit |
|---|---|
| `uv run python tools/halo_probe.py IMG_6739 --line 1700,2500,2200,2500 --line 1560,2300,1810,2300 --line 2900,2300,2450,2300 --margin 120` | 0 |
| `uv run python tools/halo_probe.py IMG_6743 --line 2450,600,1850,600 --line 835,1008,1132,670 --margin 120` | 0 |
| `uv run python tools/halo_probe.py IMG_6744 --line 1300,950,1300,450 --line 2550,200,2100,200 --margin 120` | 0 |
| `uv run python tools/halo_probe.py IMG_6738 --line 1130,1296,900,1296 --line 1056,600,1056,430 --start 0 --end 1.7 --crop-at 0.17 --crop-at 0.83 --crop-at 1.47 --margin 120 --cache-dir <work>/wp5.7/scratch/cache` | 0 |
| `uv run python tools/halo_probe.py GX011627 --line 3300,420,3700,40 --start 21.7 --end 22.7 --crop-at 21.8 --crop-at 22.2 --crop-at 22.6 --margin 150 --cache-dir <same>` | 0 |
| `uv run python tools/halo_probe.py --source <work>/wp5.3/excerpts/compilation-20261010-1080p60.mp4 --name compilation-20261010-1080p60 --line 230,200,275,95 --line 380,330,450,225 --line 340,225,368,160 --start 27.0 --end 27.5 --crop-at 27.0 --crop-at 27.5 --margin 150 --cache-dir <same> --replace` | 0 |
| `uv run ruff check .` / `uv run ruff format --check .` / `uv run mypy` | 0 / 0 / 0 |
| `uv run pytest -q tests/test_tools_halo_probe.py --basetemp=.worktrees/wp5.7/work/c57-3` | 0 (17 passed) |

All renders on the GPU (`device: GPU`). Video statistics: the probe's own real analysis run
(`AnalysisEngine.analysis_job()` over the whole clip, smoothing defaults, as
`ExportEngine._analyse` builds it), then `smoothed_record` per frame; frames decoded by
`FFmpegVideoSource` (software decode; the export's CUDA decode yields the same frames by the
source's contract). Free disk before the runs: 83 GB.

### The stage table (luma; line coordinates in source pixels; video frames in coded orientation)

Band = the `water` metric of the FUSED stage in image units (0-1) and over the source's edge
contrast; + outward ring, - inward glow. sigma = the sharpening sigma; "coarsest" = one
coarsest-level pixel in source px. Attribution: the fused deviation at the band's peak carried
by input 2's terms (k2) vs input 1's (k1), and input 2's largest levels.

| Item | Region (line) | First stage > 10 % | Fused band abs / x C | FWHM px | FWHM / sigma | FWHM / coarsest | k2 / k1 at peak (top k2 levels) | Wbar2 edge / plateau | N{} range proxy / full-res |
|---|---|---|---|---|---|---|---|---|---|
| IMG_6739 | shell left edge (1700,2500 -> 2200,2500) | input2 | +0.079 / 1.17 | 15 | 0.99 | 0.117 (128) | -0.075 / +0.004 (l3, l2, l0) | 0.65 / 0.51 | 0.0512 / 0.0772 |
| IMG_6739 | flipper (1560,2300 -> 1810,2300) | input2 (weak edge) | +0.017 / 1.08 | 2 | 0.13 | 0.016 | -0.027 / -0.004 | 0.48 / 0.50 | same |
| IMG_6739 | right flank (2900,2300 -> 2450,2300) | input1 (no clean edge) | +0.196 / 4.23, peak 124 px off the edge | 7 | 0.46 | 0.055 | +0.170 / +0.044 | 0.42 / 0.54 | same |
| IMG_6743 | object tip (2450,600 -> 1850,600) | input2 | +0.176 / 1.50 | 32 | 1.49 | 0.125 (256) | +0.181 / -0.008 (l4, l3, l5) | 0.63 / 0.52 | 0.0206 / 0.0332 |
| IMG_6743 | lower edge (835,1008 -> 1132,670) | input2 | +0.181 / 2.34 | 22 | 1.03 | 0.086 | +0.183 / -0.004 (l3, l4, l2) | 0.61 / 0.56 | same |
| IMG_6744 | lower edge (1300,950 -> 1300,450) | input2 | +0.172 / 2.38 | 16 | 0.75 | 0.062 (256) | +0.174 / +0.002 (l3, l2, l4) | 0.67 / 0.58 | 0.0183 (floor binds) / 0.0321 |
| IMG_6744 | tip (2550,200 -> 2100,200) | input2 | -0.132 / 0.89 | 4 | 0.19 | 0.016 | -0.183 / -0.017 (l0, l1, l2) | 0.71 / 0.55 | same |
| IMG_6738 | fin and turtle flipper, 49 frames x 2 lines | input2 on 83 / 83 strong frame-lines | median 0.071; 0.833 s flipper +0.155 / 1.38 | median 5; 12 at 0.833 s | 1.67 at 0.833 s | 0.188 (64) | +0.169 / -0.002 at 0.833 s (l2, l3, l1) | 0.60 / 0.57 | 0.0234-0.0239 / 0.0208-0.0230 |
| GX011627 | fin edge, top right (3300,420 -> 3700,40), 30 frames 21.7-22.7 s | input2 on 12 / 14 strong frame-lines | median 0.153; 22.122 s +0.163 / 1.86 | median 18; 21 at 22.122 s | 1.94 | 0.164 (128) | +0.187 / -0.003 at 22.122 s (l3, l4, l2) | 0.68 / 0.48 | 0.0361 / 0.0333 |
| compilation (excerpt) | shin, upper left (340,225 -> 368,160), 27.0-27.5 s | input2 on 54 / 56 strong frame-lines (3 lines) | 27.010 s +0.182 / 2.93 | 7 | 1.30 | 0.109 (64) | +0.222 / +0.017 (l1, l2, l0) | 0.65 / - | 0.0319 / 0.0365 |

Per-frame rows: `work/wp5.7/part1/table-photos.txt`, `table-videos.txt` (IMG_6738,
GX011627) and `table-compilation.txt`; every number above is read from the run JSONs.

### Hypothesis verdict

- **Sharpened input carries the band: CONFIRMED and REFINED, on all six items.** On the tabled
  clean lines compensation and white balance add nothing (excess 0.00-0.02 of C) and input 1
  nothing (at most 0.01 of C); input 2 is the first stage over 10 % on every one (abs band
  0.13-0.31). Over all non-weak frame-lines the largest excesses before input 2 are 0.00
  (compensated), 0.14 (balanced) and 0.28 (input1), on the lines without a clean edge (IMG_6739
  right flank) and the 2 of 14 GX011627 frames whose first stage is not input2. The refinement: the band's height is set by the N{} STRETCH, not by
  the edge. The bounds measured on these frames are very narrow (range 0.018-0.051 on the
  photos, 0.023-0.036 on the videos; on IMG_6744 the 0.02 floor binds, below the 0.028-0.64
  span WP1.4b measured), so the stretched high-pass saturates at 0 or 1 within about 1-2
  sigma of any edge stronger than about 0.02, and input 2 there is `I / 2` or `(I + 1) / 2`:
  a near-constant ring whatever the edge contrast. Hence fused bands of 1-4x the source
  contrast on these low-contrast underwater edges.
- **Laplacian weight favours input 2 at the edge: CONFIRMED.** Wbar2 is 0.60-0.71 at the edge
  against 0.47-0.58 on the water plateau; the fused band is 59-68 % of input 2's, and over 90 %
  of the fused deviation at the peak is carried by input 2's terms.
- **Shallow pyramid leaves a band at the coarsest scale: REJECTED.** The pyramids are deep (7-9
  levels, coarsest 17-24 px); the band's FWHM is 0.02-0.19 of one coarsest pixel; the
  attribution sits in input 2's levels 0-5 (1-32 px scales, matching 1-2 sharpening sigmas) and
  the coarsest levels carry about 0. The counterfactual single-scale blend (`naive`) has a band
  of the same size: the band is in the inputs, not made by the blending.
- **Observation for Part 2 (not a ruling):** the photo bounds measured on the proxy are 0.57-0.66
  of the range the full-resolution image would give (IMG_6743 0.0206 vs 0.0332; IMG_6744 0.0183
  vs 0.0321; IMG_6739 0.0512 vs 0.0772), so a full-resolution photo is stretched about 1.5-1.75x
  harder than its own distribution; on the tabled video frames the two agree within 15 % (the video
  bounds are proxy-measured too, then smoothed; that the codec has already removed the fine
  noise the block mean removes from a photo is a reading, not tested). This is AD-4's
  design (bounds from the analysis proxy), not a spec 6.2 divergence. The same saturation
  amplifies noise and, on the GoPro frames, compression blocks in open water (visible in the
  GX011627 marked crops).

### Not reproduced, and why

- IMG_6739 right flank: no clean edge there (the flank is motion-blurred into a darker water
  strip); the line's band peaks 124 px from its nominal edge with input 1 first: not read as
  the owner's halo. The turtle's outline halo is reproduced on the shell edge.
- IMG_6739 flipper and IMG_6744 tip lines: weak or thin bands (flipper contrast 0.016 < 0.02).
- GX011627 21.7-22.1 s: the fin has not reached the line (weak-edge frames); the band appears
  from 22.12 s on (the fin enters the corner from about 21.8 s); after 22.49 s the fin covers the
  line's water side and the reading turns inward.
- Compilation: the legs move fast; the fixed lines hold the shin edge at 27.0-27.2 s only.

### Files under `work/wp5.7/`

`part1/<item>/` for the six items (`<item>.json`, 16-bit stage crops `photo-<stage>.png` or
`t<time>-<stage>.png`, `*-marked.png` with the lines, overviews), `part1/logs/<item>.log`,
`part1/table-*.txt`; `scratch/` (smoke runs, the analysis cache `scratch/cache` reused by the
video runs).

Depth at part-1 end: 290,002 (scripts/cell_depth.py, current = peak, 116 turns, read by the orchestrator at the Part 1 yield 2026-11-03)

## Step 2A (fresh cell; Reviewer A round 0 remediation)

Dispatch `clearwater-review-evidence/wp5.7/cell/dispatch-2.md` (orchestrator gen 36). Fresh cell
(implementer-opus-high) on head `1e9909f4` (main `7395906b`). Instrument commit `cec81506`.

### The band, as now defined (module docstring of `tools/halo_probe.py`)

On the water side of a line (from the end of the start plateau to the source's edge), a stage's
OUTWARD overshoot is its rise past its own water-plateau line away from the object, zero where it
does not pass the line; the source's is measured the same way. The excess at each sample is the
stage's overshoot minus the source's, over ONE common contrast, the source's signed water
contrast C; the band is the largest excess (0 when none is positive). A band QUALIFIES only on a
non-weak edge (|C| >= 0.02) when at least 3 consecutive samples around its peak each exceed both
the 10 % threshold and 3 x the water-side uncertainty there: the stage's and the source's
`water_uncertainty` in quadrature over |C|, i.e. the plateau fit's residual RMS plus the error of
its line extrapolated to that sample, with an AR(1) effective sample count. Verdicts: `band`,
`undecided` (weak edge, or over the threshold without qualifying), `none`. The first-stage
selector names the first product stage whose band qualifies; `undecided` when none does but one
is undecided. Widths: interpolated crossings at the line's real sample spacing.

Why the extrapolation term: a fixed 3 x residual RMS let correlated plateau noise qualify in 10-37
% of 300 seeds (noise 5 % of C, correlation 1-4 px; up to 29-sample runs), because the line fit
absorbs low-frequency noise and its extrapolation over the zone adds error the RMS does not see.
With the term: 0-4 % (correlation up to 4 px), 7-13 % at 8 px (a lag-1 AR(1) under-counts long
correlation): a stated limit.

### Dispositions (Reviewer A round 0, Codex gpt-6.1-sol / high, `NEW_CRITICAL_MAJOR_FOUND`)

| # | Sev | Finding | What changed (`cec81506`) | Tests |
|---|---|---|---|---|
| 1 | MAJOR | band = per-profile normalised deviation difference; object-side changes and gamma read as bands | `water_band` rewritten as above (outward overshoot vs the source's, over the source's C); `normalised_water_side` removed; an inward spread is no band | object-plateau control (was 0.4751); gamma on a monotonic step through the real c3 staged render (input1 was 0.1193) |
| 2 | MAJOR | attribution measured raw deviations, not the detected quantity; pre-clip terms | `staged_render` also yields `srcterm_k<k>_l<l>` (the source's Laplacian bands under the same weight pyramids; they add up to the source since sum Wbar = 1) and `prefused` (multiscale_fusion's sum before the clip); `attribute_band` splits the fused band's excess at its peak exactly: per (k, l) `sign (dev(term) - [s] dev(srcterm)) / abs(C)` (`[s]` = 1 when the source is outward at the peak) plus the clip's share `sign (dev(fused) - dev(prefused)) / abs(C)`; the record carries terms, per input, per level, clip, residual and the raw shares | per-input and per-level sums + clip = band within 1e-4 of C on a scene where the clip does not bind (residual about 5e-8); the raw (unsubtracted) sum misses by 0.061 (> 100 x the tolerance) |
| 3 | MAJOR | noise and weak edges decide the first stage | the qualification rule above; weak edge -> `undecided`; `first_stage` reads qualifying bands only; `unqualified_exceedances` recorded | 1-sample spike (10.25 %, support 1, undecided); correlated plateau noise (a 0.20-of-C excursion, undecided) with a real ring through it qualifying; weak edge undecided; selector undecided on the spike and on a weak edge |
| 4 | MAJOR | writes not confined | `--name` must be a plain stem (`_check_name`: no separator, drive or stream `:`, `..`, control character, leading or trailing dot or space); out, cache and the record path must be `inside` `<working>/wp5.7` and pass `write_target_refusal`; refused before any write | 7 bad names; out or cache outside wp5.7, a `..` escape, `work/wp5.3/records` |
| 5 | MINOR | strip and interpolation silently clamped at the crop | `line_profile` refuses a strip that leaves the array; `_check_region` checks every line's whole strip (`strip_bounds`) inside the region | strip off the array (row -1, column 60); strip leaving the region; a line on the image's top row |
| 6 | MINOR | render equality recorded, not enforced | a render mismatch or `clip(prefused) != fused` raises `ProbeFailedError`: exit 1, no record | a drifted render -> exit 1, no JSON |
| 7 | MINOR | no test of `first_stage_over_threshold` | `first_stage` public; the record field is its result | a band planted in each of the 6 product stages alone (a constant selector fails 5 of 6); a band persisting from each stage on; none -> None |
| 8 | MINOR | video completeness | `expected_frames=expected_frames(probe)` passed to `AnalysisEngine` (as `jobs/export.py` passes it); every selected pts must be rendered or `ProbeFailedError` | fake source and engine: the count reaches the engine; a skipped selected frame fails |
| 9 | ADVISORY | integer widths, 1 px spacing assumed | `_width` interpolates the crossings; `sample_spacing = length / round(length)` applied to fwhm, extent and peak distance (water and two-sided) | Gaussian ring FWHM 5.89 (was 5); a spacing of 2 doubles the widths |

Fix 6, second part (which intermediates are recomputed): every saved stage comes from ONE pass of
`staged_render`, whose `output` is compared bit for bit with `method.render` and whose `fused`
equals `clip(prefused)` bit for bit (both enforced). `render` exposes no intermediate, so equality
with the product's internal arrays rests on calling the same functions, in `render`'s order, with
`render`'s arguments. Recomputed outside the product's own call: `high_pass` (the same call
`fusion_inputs` makes), `stretched` (formed as `fusion_inputs` forms N{}; test: input2 =
clip((balanced + stretched) / 2) at strength 1), the three weight components (the product's
`laplacian_weight`, `saliency_weight` and `saturation_weight` called separately; `wbar_k` is
`weight_maps`' own output), the attribution terms (checked through `prefused`), `naive` (a
counterfactual) and the full-resolution bounds (a diagnostic).

### RED (the new tests against `1e9909f4`'s probe): 31 failed, 12 passed

`DID NOT RAISE ValueError` (strip); `KeyError 'verdict'` / `'qualifies'` / `'support_samples'`
(new fields); `assert 0.47506491051416905 < 1e-09` (object plateau); `AssertionError: input1 /
assert 0.11934356334726515 < 0.01` (gamma); `assert False` (noise precondition); `assert 5 ==
5.887 +- 0.15` (width); `AttributeError: no attribute 'first_stage'` (x 8); `assert 0 == (2 * 3)`
(source terms); `assert 0 == 2` (names `../escape`, `C:escape`, `..`, empty, absolute; a strip
leaving the region); `FileNotFoundError ... o\a\b.json` (names `a/b`, `a\b`); out-outside
AssertionError; `assert 0 == 1` (render drift); `KeyError 'expected_frames'`; `AttributeError:
no attribute 'ProbeFailure'` (skipped frame). Log `work/c57-2a-red.log` in the worktree.

### GREEN (`cec81506`)

`uv run pytest -q tests/test_tools_halo_probe.py` 43 passed (1.7 s); `ruff check .` All checks
passed; `ruff format --check .` 313 files already formatted; `mypy` Success, no issues in 157
source files. Two test calibrations after the first green attempt (test-only): the noise
control's amplitude and seed (the first draft's noise did not cross 10 %), and the attribution
scene (sharpening fraction 0.03 so the ring spans more than 3 samples on a 128-px frame; the
in-camera halo sigma 6).

### Re-measurement (corrected instrument; the same items, lines, margins and frames; GPU)

Commands: Part 1's six, each with `--out <work>/wp5.7/part1r/<item>` (cache `scratch/cache`
reused). Exit 0 on all six, so every frame's render check and prefused check held: IMG_6739 8
s, IMG_6743 14 s, IMG_6744 14 s, IMG_6738 44 s, compilation 100 s, GX011627 114 s. Free disk
83 GB. Records `part1r/<item>/<item>.json`, rows `part1r/table-<item>.txt`, logs
`part1r/logs/`. Sensitivity (photos only, half width 12): `part1r/sensitivity-hw12/`.

The re-issued stage table (luma; "first qualifying" = the selector; "first over 10 %" = the
first product stage whose band exceeds the threshold, qualifying or not; band = the fused
stage's, over the source's C and absolute; k2 / k1 = the per-input shares of the fused band at
its peak):

| Item | Region (line) | First qualifying | First over 10 % | Fused band x C / abs (verdict) | FWHM px | / sigma | / coarsest | k2 / k1 (top k2 levels) | Wbar2 edge / plateau | N{} range proxy / full |
|---|---|---|---|---|---|---|---|---|---|---|
| IMG_6739 | shell left edge | **undecided** (input2: level 1.49 vs band 1.82, support 2) | input2 | 1.04 / 0.071 (undecided) | 14.7 | 0.97 | 0.115 (128) | +1.107 / -0.063 (l3, l2, l0) | 0.65 / 0.51 | 0.0512 / 0.0772 |
| IMG_6739 | flipper | **undecided** (weak edge, C 0.016) | input2 | 1.55 / 0.025 | 2.1 | 0.14 | 0.017 | +1.525 / +0.021 | 0.48 / 0.50 | same |
| IMG_6739 | right flank (no clean edge) | input2 (peak 124 px off the edge) | input1 (0.31, undecided) | 3.07 / 0.142 (band) | 7.1 | 0.47 | 0.055 | +2.959 / +0.113 (l1, l0, l2) | 0.42 / 0.54 | same |
| IMG_6743 | object tip | input2 | input2 | 1.48 / 0.174 (band) | 31.7 | 1.48 | 0.124 (256) | +1.543 / -0.064 (l4, l3, l5) | 0.63 / 0.52 | 0.0206 / 0.0332 |
| IMG_6743 | lower edge | input2 | input2 | 2.32 / 0.179 (band) | 22.1 | 1.03 | 0.086 | +2.369 / -0.048 (l3, l4, l2) | 0.61 / 0.56 | same |
| IMG_6744 | lower edge | **undecided** (fused: level 2.39 vs band 2.38; input2: level 3.88 vs band 3.66) | input2 | 2.38 / 0.172 (undecided) | 7.8 | 0.36 | 0.030 (256) | +2.387 / -0.007 (l3, l2, l4) | 0.67 / 0.58 | 0.0183 (floor) / 0.0321 |
| IMG_6744 | tip | **undecided** | input2 | 0.80 / 0.118 (undecided), outward, 35 px off the edge | 4.7 | 0.22 | 0.018 | +0.830 / -0.032 (l4, l3, l1) | 0.71 / 0.55 | same |
| IMG_6738 | fin, flipper; 49 frames x 2 lines (83 non-weak) | input2 14, **fused 3, input1 2**, undecided 59, none 5 | input2 71, input1 7, none 5 | median 0.54, max 5.40; 0.833 s flipper 1.45 / 0.163 (band) | 9.6 at 0.833 s | 1.34 | 0.150 (64) | +1.439 / +0.007 (l2, l1, l3) | 0.60 / 0.57 | 0.0234-0.0239 / 0.0208-0.0230 |
| GX011627 | fin edge; 30 frames (14 non-weak) | input2 7, **fused 2**, undecided 5 | input1 8, input2 6 | median 1.14, max 7.42; 22.122 s 1.84 / 0.162 (band) | 20.3 | 1.88 | 0.159 (128) | +1.797 / +0.046 (l3, l4, l2) | 0.68 / 0.48 | 0.0349-0.0361 / 0.0318-0.0341 |
| compilation (excerpt) | 3 lines, 27.0-27.5 s (56 non-weak) | input2 4, **fused 2**, undecided 35, none 15 | input2 38, input1 3, none 15 | median 0.42, max 6.77; 27.010 s shin 3.22 / 0.200 (band) | 6.2 | 1.15 | 0.097 (64) | +3.165 / +0.054 (l1, l0, l2) | 0.65 / 0.51 | 0.0315-0.0319 / 0.0365-0.0369 |

No compensated or balanced band qualifies on any frame-line (the largest is 0.05 of C). Every
qualifying fused band is carried by input 2's terms: input 2's share of the band at the peak is
0.89-1.55 (above 1 where input 1's share is negative); the clip's share is 0.000 everywhere;
attribution residuals at most 6e-6 of C.

### What changed from Part 1, item by item

- IMG_6739: shell edge input2 -> undecided (band 1.04 vs 1.17; input 2's own plateau noise,
  sigma 0.023 against the source's 0.002, lifts the level); flipper -> undecided (a weak edge
  now forces it); right flank input1 -> input2 (input 1's 0.31 no longer qualifies; still not the
  owner's halo, peak 124 px off the edge).
- IMG_6743: unchanged (input2 on both lines; 1.48 / 2.32 vs 1.50 / 2.34; FWHM 31.7 / 22.1 vs 32 /
  22).
- IMG_6744: lower edge input2 -> undecided (by 0.01 of C: band 2.38 vs level 2.39); tip: Part 1's
  INWARD -0.89 is no band by the new definition; the new metric finds an outward ring of 0.80, 35
  px from the edge, undecided. Half width 12 resolves the lower edge to input2 (2.11, band).
- IMG_6738: Part 1 input2 on 83 / 83 -> input2 14, fused 3, input1 2, undecided 59, none 5. The
  featured flipper frame (0.833 s) stands: input2, 1.45 (was 1.38).
- GX011627: Part 1 input2 on 12 / 14 -> input2 7, fused 2, undecided 5. 22.122 s stands: input2,
  1.84 (was 1.86).
- Compilation: Part 1 input2 on 54 / 56 -> input2 4, fused 2, undecided 35, none 15. The 27.010 s
  shin stands: input2, 3.22 (was 2.93).

### Hypothesis verdicts (re-issued)

- **The sharpened input carries the band:** CONFIRMED where the instrument decides: the first
  qualifying stage is input 2 on every decided photo line and on 25 video frame-lines; input 2's
  terms carry 0.89-1.55 of every qualifying fused band (including the 7 named `fused`). NOT
  decided on IMG_6744 (both lines) and the IMG_6739 shell at half width 4: see the STOP.
- **The Laplacian weight favours input 2 at the edge:** CONFIRMED (unchanged: Wbar2 0.60-0.71 at
  the edge against 0.47-0.58 on the water plateau).
- **A shallow pyramid:** REJECTED (stands: FWHM 0.017-0.26 of a coarsest pixel; attribution in
  levels 0-5; clip share 0).
- **The N{} saturation refinement:** stands, with a second face: input 2's (and the fused) water
  plateau is 10-20 x noisier than the source's (sigma 0.02-0.07 vs 0.002-0.003), which is what
  makes many frame-lines undecided.

### STOP (dispatch step 3: a stage other than input 2 now carries the band on some items)

- **S1 (instrument; disposition 1 not fully met). A monotonic remap of a source that already
  overshoots still reports a band.** IMG_6738 0.633 s and 0.700 s, line 2: input 1 qualifies
  (0.288, 0.162) because gamma's local gain (1.16 at the water level 0.60) multiplies the
  source's own in-camera overshoot (0.073 and 0.055 abs): the input1 / balanced overshoot ratio
  is 1.19, the plateau-measured gain 1.17. Synthetic repro: source = unsharp(0.6 / 0.2 step,
  sigma 8), stage = source^1.5 -> band 0.1185 (a linear gain of 1.2 -> 0.0950; identity ->
  0.0000). The same effect is behind the input1 "first over 10 %" counts (GoPro in-camera
  sharpening). Needs a ruling on how the source's overshoot is credited through a stage's tone
  gain (no stage-agnostic local-gain estimate works for input 2, whose plateau gain on noise is
  about 10-20).
- **S2 (selector). `fused` is named first on 7 video frame-lines** where input 2 exceeds but stays
  under its own (noisier) level and the fused band qualifies; attribution puts 0.92-1.10 of each
  such fused band in input 2's terms. Ruling: per-stage first qualifying (as built), or
  attribution-informed.
- **S3 (noise rule vs strip width).** At half width 4 the stated rule leaves IMG_6744 wholly, the
  IMG_6739 shell, and 59 / 83, 5 / 14 and 35 / 56 of the video frame-lines undecided; half width
  12 resolves IMG_6744's lower edge (input2) but not the curved shell edge (0.73, undecided) and
  turns the right flank undecided. The factor (3), the extrapolation term and the strip width
  are the cell's choices: a ruling before Part 2 measures candidates with them.

### Round ledger (cumulative)

| Round | Reviewer | Critical | Major | Minor | Advisory | In-envelope / out | NEW / REOPENED | Reverts | Fixes: instrument / test-only / product |
|---|---|---|---|---|---|---|---|---|---|
| 0 | A (Codex, at the orchestrator's seat) | 0 | 4 | 4 | 1 | 9 / 0 | 9 / 0 | 0 | 9 / 0 / 0 |

Depth at step-2A end: 262949 (scripts/cell_depth.py, wp57-cell2, read by the orchestrator at the step-2A yield 2026-11-03)

## Step 2B (fresh cell; S1-S3 rulings)

Dispatch `clearwater-review-evidence/wp5.7/cell/dispatch-3.md` (orchestrator gen 37). Fresh cell
(implementer-opus-high) on head `03b2614e` (main `0cafb374`; step 2A's instrument `648eb963`).
CHARC's rulings (main `b4f9b99a`, in the brief) as implemented:

- **S1 [instrument], implemented.** The pointwise stages, white-balanced and input 1, are
  measured against the SOURCE REMAPPED through that stage's own pointwise operation; every other
  stage (compensated, input 2, `naive`, fused, output) at face value against the source. The
  definition (module docstring of `tools/halo_probe.py`, `stage_band`): the excess at each
  water-side sample is the stage's outward overshoot past its own water-plateau line minus the
  REFERENCE's, over the SOURCE's signed water contrast C (the common denominator and the
  weak-edge test are unchanged); the reference is the source for a face-value stage and, for a
  pointwise stage, the source remapped as the product remaps that stage: `remap_balanced` =
  `AncutiFusionMethod._white_balance` applied to the SOURCE pixels with the same record the
  render used (the frame's gray-world gains, smoothed for video, through the strength and the
  D99 clamp, then `clip(a * gains)`; nothing re-estimated), and `remap_input1` =
  `clip(remap_balanced ** gamma)` with the render's `gamma`, as `fusion_inputs` forms input 1,
  so the two remaps chain as the product chains them. The uncertainty is the stage's and the
  reference's `water_uncertainty` in quadrature; the qualifying rule (S3) is unchanged.
  `staged_render` yields the two references after `output` (the pipeline order of the product
  stages is untouched); they are profiled on every channel and saved as crops
  (`<frame>-remap_balanced.png`, `<frame>-remap_input1.png`); every luma and channel band
  records `reference` (`remapped_source` or `source`). Record schema 3.
- **Compensated is not pointwise for the method measured.** 3C (`compensate_c3`, the shipped
  default `c3`, every run of this package) is local: the chroma correction is a Gaussian mean of
  Cb / Cr under a Gaussian-smoothed mask (`methods/compensation.py:250-253`). Not a STOP: S1 is
  not extended. For the record only: the OTHER method's compensation, Ancuti 2018
  (`compensate_ancuti2018`), IS a per-pixel operation of the frame's own statistics (channel
  means and alphas); no run of this package uses it, and the probe reads it at face value.
- **S2 [selector], implemented.** Two columns per line: `first_stage_over_threshold` (the first
  qualifying stage, as built) and `attributed_stage` (`attributed_stage`): the input whose terms
  carry the larger share of the qualifying FUSED band at its peak (`attribute_band`'s
  `per_input`, step 2A's attribution). Rule: fused verdict `none` -> `none`; fused `undecided`
  -> `undecided`; a qualifying fused band -> `input1` or `input2` by the larger share, except
  `undecided` on a tie (the two shares within `ATTRIBUTION_TIE` = 1e-4 of C, the float32
  summation-order scale) or when neither share is positive (the clip would carry it; the clip's
  share was 0.000 on every step-2A line). The summary line prints `attributed=`.
- **S3 [noise rule]: no code change** (factor 3, the extrapolation term, AR(1) effective count;
  half width 4 of record, half width 12 as the photo sensitivity column; `undecided` is reported
  as such).

### RED (the new tests against `03b2614e`'s probe): 8 failed, 41 passed

Log `work/c57-2b-red.log` in the worktree.

- `test_s1_controls_through_the_real_staged_render[None]`: `AssertionError: input1` /
  `assert 0.11854498960215555 < 0.0001` (the sharpened 0.6 / 0.2 step, sigma 8, through the real
  c3 render at the shipped defaults: gamma 1.5 charged to input 1 at face value).
- `test_s1_controls_through_the_real_staged_render[1.2]`: `AssertionError: balanced` /
  `assert 0.0950130770721173 < 0.0001` (the same with the white-balance gains replaced by 1.2;
  this probe also named `input1` first there).
- `test_s1_pointwise_remap_of_a_sharpened_source_is_no_band[input1 / balanced]` (1-D, x^1.5 and
  a 1.2 gain): `AttributeError: module 'halo_probe' has no attribute 'stage_band'` (x 2), after
  the face-value preconditions 0.1185 and 0.0950 passed.
- `test_s2_fused_first_and_input2_attributed`: `AttributeError: ... no attribute
  'attributed_stage'`, after its preconditions passed on this probe (input 2 exceeds and is
  undecided, the fused band qualifies, `first_stage` = `fused`).
- `test_s2_attributed_stage_rule_on_ties_and_unqualified_bands`: the same AttributeError.
- `test_attribution_adds_up_to_the_detected_added_band`, `test_main_on_a_synthetic_photo`:
  `KeyError: 'attributed_stage'` (the record's new column).

### GREEN

`uv run pytest -q tests/test_tools_halo_probe.py` 49 passed (2.0 s); `uv run ruff check .` All
checks passed; `uv run ruff format --check .` 313 files already formatted; `uv run mypy`
Success, no issues found in 157 source files. One test-only calibration before RED was taken:
the S2 scene's input-2 noise was first the correlated (Gaussian, sigma 2) plateau noise of the
step-2A noise test, through which the input-2 ring QUALIFIED (the ring rides the noise's own
excursion); it is now sample-to-sample noise of +-0.04 (amplified grain), which lifts input 2's
level to 0.34 of C and breaks its support (1 sample), while the fused ring (0.25 of C) qualifies.
Two docstring sentences from step 2A were corrected against the code ("a monotonic remap
reports no band" holds only for a source with no overshoot).

Depth at mid-build yield 1: 176,019 (scripts/cell_depth.py, read by the orchestrator at the mid-build yield 2026-11-03)

### Re-run (step 3; instrument `d2afd75b`; GPU; outputs `work/wp5.7/part1s/`)

All six items and the half-width-12 photo sensitivity, the same lines, margins and frames as step
2A, one process at a time (`uv --directory <worktree> run python tools/halo_probe.py ...`, the
commands of the mid-build yield; cache `scratch/cache` reused; the compilation read in place
from `work/wp5.3/excerpts/`). Every run exit 0 on the GPU, so every frame's render check and
prefused check held: IMG_6739 34 s, IMG_6743 22 s, IMG_6744 17 s, IMG_6738 48 s, compilation
107 s, GX011627 126 s; hw12 9 / 16 / 17 s (396 s in all; IMG_6739's first run carries the
process warm-up). Free disk 82 GB before, 79 GB after. Records `part1s/<item>/<item>.json`
(schema 3), rows `part1s/table-<item>.txt`, logs `part1s/logs/` (`runs.txt` the walls),
hw12 `part1s/sensitivity-hw12/`; the comparison against `part1r` (a scratch tabulator, not
committed) `part1s/table-2b.txt`. Determinism: every fused and input-2 band equals step 2A's
exactly (max difference 0), so only the pointwise stages and the new column moved.

### The re-issued stage table (luma, half width 4 of record; hw12 = the photo sensitivity)

"First qualifying" = the selector; "attributed" = S2; "first over 10 %" = the first product
stage whose band exceeds the threshold, qualifying or not; counts over the non-weak frame-lines.
The fused band, widths, k2 / k1 shares, Wbar and N{} columns of step 2A's table are unchanged
(identical numbers) and are not repeated.

| Item | Region (line) | First qualifying | Attributed | First over 10 % | Fused band x C / abs (verdict) | Pointwise bands (balanced / input1) | hw12: first / attributed |
|---|---|---|---|---|---|---|---|
| IMG_6739 | shell left edge | undecided | undecided | input2 | 1.04 / 0.071 (undecided) | 0.000 / 0.020 | undecided / undecided |
| IMG_6739 | flipper (weak, C 0.016) | undecided | undecided | input2 | 1.55 / 0.025 (undecided) | 0.000 / 0.099 (undecided, weak) | undecided / undecided |
| IMG_6739 | right flank (no clean edge) | input2 | input2 | **input2** (was input1) | 3.07 / 0.142 (band) | 0.000 / 0.064 (was 0.052 / 0.309) | undecided / undecided |
| IMG_6743 | object tip | input2 | input2 | input2 | 1.48 / 0.174 (band) | 0.000 / 0.017 | input2 / input2 |
| IMG_6743 | lower edge | input2 | input2 | input2 | 2.32 / 0.179 (band) | 0.000 / 0.015 | input2 / input2 |
| IMG_6744 | lower edge | undecided | undecided | input2 | 2.38 / 0.172 (undecided) | 0.000 / 0.024 | input2 / input2 |
| IMG_6744 | tip | undecided | undecided | input2 | 0.80 / 0.118 (undecided) | 0.000 / 0.003 | undecided / undecided |
| IMG_6738 | 49 frames x 2 lines (83 non-weak) | input2 16, fused 3, undecided 59, none 5 (was input2 14, fused 3, **input1 2**) | input2 17, undecided 57, none 9 | input2 70, input1 8, none 5 (was 71 / 7 / 5) | 17 band, 57 undecided, 9 none; 0.833 s flipper 1.45 / 0.163 (band) | max balanced 0.005; input1 0.26, none qualifies | - |
| GX011627 | 30 frames (14 non-weak) | input2 7, fused 2, undecided 5 (unchanged) | input2 9, undecided 3, none 2 | input2 14 (was input1 8, input2 6) | 9 band, 3 undecided, 2 none; 22.122 s 1.84 / 0.162 (band) | none over 0.05 on non-weak lines | - |
| compilation (excerpt) | 3 lines (56 non-weak) | input2 4, fused 2, undecided 35, none 15 (unchanged) | input2 5, undecided 36, none 15 | input2 40, input1 1, none 15 (was 38 / 3 / 15) | 5 band, 36 undecided, 15 none; 27.010 s shin 3.22 / 0.200 (band) | input1 max 0.106 (undecided) | - |

No compensated, balanced or input-1 band qualifies on any frame-line, at half width 4 or 12
(largest non-weak: compensated 0.000, balanced 0.005, input1 0.261, all `none` or `undecided`).
Every qualifying fused band (34 at half width 4: 3 photo lines + 17 + 9 + 5 video frame-lines;
3 photo lines at half width 12) is attributed to input 2: input 2's terms carry 0.89-1.10 of each
band at its peak, the clip's share 0.000. Undecided counts (S3, not evidence either way): first qualifying 1 + 2
photo lines (IMG_6739 shell, IMG_6744 both; plus the weak flipper), 59 / 83, 5 / 14, 35 / 56
video frame-lines; at hw12 4 of 7 photo lines.

### What changed from step 2A, line by line

- **Input 1 named first (S1's target): gone.** IMG_6738 0.633 s and 0.700 s line 2: input1
  (0.288, 0.162, band) -> input1 0.194 and 0.137, undecided (support 0, under their levels
  0.205 / 0.143); the first qualifying stage is now input2 on both (fused 1.97 / 2.44, band,
  attributed input2).
- **"First over 10 %" = input1 that VANISHED** (non-weak): IMG_6739 right flank (0.309 ->
  0.064); IMG_6738 line 2 at 0.000 s (0.136 -> 0.000), 0.567 s (0.148 -> 0.096), 0.600 s (0.114 ->
  0.070), line 1 at 1.567 s (0.156 -> 0.000); GX011627 all eight (22.356, 22.389, 22.422, 22.456,
  22.489, 22.623, 22.656, 22.689 s: 0.10-0.25 -> 0.009-0.045); the compilation 27.010 s line 3
  (0.163 -> 0.028) and 27.094 s line 3 (0.197 -> 0.008). Every one now reads input2 first over 10
  %. The two weak GX011627 lines whose first over 10 % was `balanced` (21.755 s 0.103, 22.189 s
  0.113) now read 0.000 and 0.014 there.
- **"First over 10 %" = input1 that SURVIVED, or appeared** (non-weak; none qualifies, so the
  first-qualifying column does not change): survived IMG_6738 0.633 s and 0.700 s line 2 (above),
  1.600 s line 2 (0.249 -> 0.159, level 0.878); compilation 27.027 s line 1 (0.141 -> 0.106, level
  1.354). Appeared IMG_6738 line 2 at 0.433, 0.467, 0.500, 0.667, 0.767 s (0.03-0.09 -> 0.11-0.26;
  support 0-1, under their levels). These are a REAL input-1 contribution relative to the ruled
  reference, reported, not suppressed. Its cause, reproduced on the records
  (`profiles_Y`): input1 - remap_input1 = gamma(gains * compensated) - gamma(gains * source) by
  construction, i.e. 3C's chroma change, which leaves the compensated luma equal to the source's
  (difference 0.0000 along these lines) and the balanced luma within 1e-4 of its reference, made
  luma-visible by input 1's PER-CHANNEL gamma. At the appearing peaks the source's own outward
  luma overshoot (0.10-0.22 of C) is carried into input 1 at x 1.25-1.28 (water luma 0.56-0.59),
  while the remap reference, the per-channel gamma of the uncompensated, cast source, carries
  only 0.002-0.058 of C there; on these weak-contrast edges (C 0.028-0.077) the residual
  reads 0.11-0.26 of C. A reference chained from the COMPENSATED image instead of the source
  would read 0 for both pointwise stages by construction; the ruling names the source, so that is
  CHARC's call, not made here.
- **S2 on the lines named `fused` first:** all seven are attributed to input 2 (IMG_6738 0.500,
  0.667, 0.967 s line 2; GX011627 22.489, 22.589 s; the compilation 27.010 s and 27.044 s line 1).
- **Featured frames: no verdict changed.** IMG_6738 0.833 s line 2: input2 first, attributed
  input2, fused 1.45 / 0.163 band (input1 0.018 -> 0.066). GX011627 22.122 s: input2, input2,
  1.84 / 0.162 band (input1 0.061 -> 0.004). Compilation 27.010 s line 3: input2, input2, 3.22 /
  0.200 band (its first over 10 % input1 0.163 -> input2).
- **Weak-edge frame-lines** (never decided): the first-over-10 % stage moved on 19 of them
  (IMG_6738 4, GX011627 8, the compilation 7), between none, input1, balanced and input2 either
  way.
- **hw12 (photos):** as step 2A: IMG_6743 both and IMG_6744's lower edge input2 (attributed
  input2); the IMG_6739 shell and right flank, IMG_6744's tip undecided.

### Hypothesis verdicts (re-issued)

- **The sharpened input carries the band: CONFIRMED** on every decided line: the first
  qualifying stage is input 2 on every decided photo line and on 27 video frame-lines (was 25:
  the two IMG_6738 input-1 lines resolved to input 2), `fused` on 7 more, and every qualifying
  fused band (34 at half width 4, 3 photo lines at 12) is ATTRIBUTED to input 2 (its terms
  0.89-1.10 of the band). Not decided: IMG_6744 both lines and the IMG_6739 shell at half width
  4 (IMG_6744's lower edge decides input2 at 12).
- **No pointwise or compensation stage carries a qualifying band** (S1 applied): the input-1
  residuals over 10 % are the 3C x per-channel-gamma interaction above, none qualifying.
- **The Laplacian weight favours input 2 at the edge: CONFIRMED** (unchanged).
- **A shallow pyramid: REJECTED** (unchanged).
- **The N{} saturation refinement: stands** (unchanged).

### STOP check (dispatch step 3)

No STOP: no input-1 or white-balanced band qualifies on any line; every qualifying fused band is
attributed to input 2; no featured frame changed its verdict. Reported, not a STOP: input-1 bands
over 10 % (never qualifying) survive or appear on 9 non-weak lines, cause above.

Depth at step-2B end: 221229 (scripts/cell_depth.py, wp57-cell3, read by the orchestrator at the step-2B yield 2026-11-03)

## Step 2C (Reviewer A round 1 remediation)

Dispatch `clearwater-review-evidence/wp5.7/cell/dispatch-4.md` (orchestrator gen 37), the same
cell (wp57-cell3) resumed on head `1e166e26`. Reviewer A round 1 (Codex gpt-6.1-sol / high,
read-only, at the orchestrator's seat, on `1e166e26`): `NEW_CRITICAL_MAJOR_FOUND`, nothing
against the measurement (it confirmed S1's gains and gamma, S2's rule, the full-frame equality
checks, no 6.2 / 6.6 divergence).

### Dispositions

| # | Sev | Finding | What changed | Tests |
|---|---|---|---|---|
| 1 | MAJOR | crops and overviews written into `out` unchecked; a link planted there (to a CP5 PNG or a footage file) is truncated through `write_png`'s `"wb"` | every output file is created inside a FRESH staging folder `.<out>.staging-<UTC stamp>` beside `out`, made with an exclusive `mkdir` (fails on any existing name); the record opened with `"x"`; the staging, failed and replaced sibling names pass the same `inside(<working>/wp5.7)` and `write_target_refusal` checks as `out`; `out` itself must lie strictly below `wp5.7`; publication = renaming the staging folder to `out` | a prior `out` whose `photo-source.png` is a hard link, and (second case) a symbolic link, to `<work>/wp5.3/pair.png`: after `--replace` the target is unchanged and `out` holds a fresh PNG (both cases ran; neither skipped) |
| 2 | MINOR | a failed `--replace` mixed new crops with the old record | a failed or refused run publishes nothing and leaves `out` untouched: an EMPTY staging folder is removed (`os.rmdir`, removes nothing else); one holding partial output is KEPT, renamed `.<out>.failed-<stamp>` (no deletion code); `--replace` on success renames the existing `out` aside to the kept sibling `<out>.replaced-<stamp>`, then the staging folder to `out` (a failed second rename undoes the first); an existing `out` (or link of that name) without `--replace` is refused (exit 2) | a failed `--replace` (render drift, a different margin so the crops would differ) leaves the prior folder byte-identical, publishes nothing, keeps one `.out.failed-*` without a record; a fresh failed run leaves no `out`; a refusal inside the run (region) leaves no folder; a successful `--replace` keeps exactly one `out.replaced-*` with its record |
| 3 | MINOR | Windows device names pass `--name` | `_check_name` refuses `WINDOWS_DEVICE_NAMES` (CON, PRN, AUX, NUL, CONIN$, CONOUT$, COM1-9, LPT1-9 and the superscript-digit forms) on every OS, any case, with or without an extension, trailing spaces before the dot ignored | 10 names (`NUL`, `nul`, `CON`, `prn.json`, `Aux.txt`, `COM1`, `com9.x`, `LPT1`, `lpt9`, `NUL .x`): exit 2, no `out` |
| 4 | MINOR (test only) | no test exercises a binding clip | a dark-water scene (water 0.02, bright disc 0.5) whose fused dark ring is cut at 0 at the band peak | the clip's share -0.016 of C (`< -100 x` tolerance) and per-input + clip and per-level + clip = the band within 1e-4; one-off mutation probe (the record's `clip` forced to 0): `assert 0.0 < (-100 * 0.0001)`, FAILED (log `work/c57-2c-mutation.log`) |

No measurement code changed (the band, record and crop values are untouched: the record assembly
moved into `_record` unchanged); the smoke run below confirms it byte for byte.

### RED (the new tests against `1e166e26`'s probe): 16 failed, 48 passed

Log `work/c57-2c-red.log` in the worktree.

- planted link, hard and symbolic: `assert b'\x89PNG\r\n...' == b'CP5 evidence, read-only'` (the
  protected file truncated and rewritten through the link) x 2.
- failed `--replace`: `AssertionError: assert {...} == {...}` / `Differing items:
  {'photo-wbar_2.png': ...} {'photo-input2.png': ...}` (new crops beside the old record).
- fresh failed run, and the existing render-drift test: `assert not True` / `where True =
  .../wp5.7/fresh').exists` and `.../wp5.7/o').exists` (a failed run left its folder).
- device names x 10: `assert 0 == 2` (accepted, the record written to the device, exit 0).
- the synthetic-photo test: `assert 0 == 1` / `where 0 = len([])` (no kept `out.replaced-*`).
- the binding-clip test PASSES on `1e166e26` (finding 4 is test-only); its RED is the mutation
  probe above.

### GREEN

`uv run pytest -q tests/test_tools_halo_probe.py` 64 passed (3.7 s); `uv run ruff check .` All
checks passed; `uv run ruff format --check .` 313 files already formatted; `uv run mypy`
Success, no issues found in 157 source files.

### Smoke run (the real tool, GPU)

`uv --directory <worktree> run python tools/halo_probe.py IMG_6743 --line 2450,600,1850,600
--line 835,1008,1132,670 --margin 120 --out <work>/wp5.7/smoke-2c/IMG_6743`, then the same with
`--replace`: exit 0 / 17 s, exit 0 / 17 s. `smoke-2c/` then holds `IMG_6743/` (the second
publication) and `IMG_6743.replaced-20261103T084724801016Z/` (the first, kept), each with the
same 25 files (`IMG_6743.json`, 2 overviews, 22 stage crops including `photo-remap_*`), and no
staging or failed folder. Both records equal `part1s/IMG_6743/IMG_6743.json` in every field but
`started` / `finished` (0 differences; 128 band fields each), and every PNG is byte-identical to
part1s'. Free disk 65 GB at the smoke (79 GB at step 2B's end; the drop is not this step's: the
smoke wrote 174 MB, two publications of 87 MB).

### Round ledger (cumulative)

| Round | Reviewer | Critical | Major | Minor | Advisory | In-envelope / out | NEW / REOPENED | Reverts | Fixes: instrument / test-only / product |
|---|---|---|---|---|---|---|---|---|---|
| 0 | A (Codex, at the orchestrator's seat) | 0 | 4 | 4 | 1 | 9 / 0 | 9 / 0 | 0 | 9 / 0 / 0 |
| 1 | A (Codex, at the orchestrator's seat) | 0 | 1 | 3 | 0 | 4 / 0 | 4 / 0 | 0 | 3 / 1 / 0 |

Depth at step-2C end: 275495 (scripts/cell_depth.py, wp57-cell3, read by the orchestrator at the step-2C yield 2026-11-03)

## Step 2D (Reviewer A round 2 remediation)

Dispatch `clearwater-review-evidence/wp5.7/cell/dispatch-6.md` (orchestrator gen 37), the same
cell (wp57-cell3) resumed on head `1e6cb6c8`, its last step. Reviewer A round 2 (Codex,
read-only, at the orchestrator's seat, on `1e6cb6c8`): `NEW_CRITICAL_MAJOR_FOUND`; it confirmed
step 2C changed no measurement function (AST comparison), the metric, S1, S2, the qualification
rule, the full-frame equality checks and the binding-clip control, and no product divergence
(no outcome B). Dispositions are the orchestrator's (binding).

### Dispositions

| # | Sev | Finding | Disposition / what changed | Tests |
|---|---|---|---|---|
| 1 | MAJOR, out of envelope (adjudicated) | checked ancestors can change between validation and the writes (a concurrent process renames `wp5.7\part1` and installs a junction at its old path; or plants a hard link in the fresh staging folder before a PNG write) | no code change; a stated limit (below, and in the module docstring's publication paragraph) | - |
| 2 | MINOR | a failed rollback can leave `out` absent and say nothing useful; an interrupt during the publish rename skipped the rollback | `_publish` rolls back for ANY exception (`BaseException`, re-raised after); when the rollback fails too it raises `RollbackError` (an `OSError`) naming the publish failure, the rollback failure and the kept `<out>.replaced-<stamp>` folder holding the old publication; `main` prints it and exits 1 (the staging folder retired to `.<out>.failed-<stamp>`) | injected failures (`Path.rename` patched for the two renames onto `out` only): publish OSError + rollback OSError -> exit 1, the message holds `publish-boom`, `undo-boom` and the kept folder's name, the kept folder byte-identical to the old publication; publish interrupt (KeyboardInterrupt) -> re-raised, `out` byte-identical, no kept folder; publish interrupt + rollback OSError -> exit 1, the message holds `KeyboardInterrupt`, `undo-boom` and the kept folder |
| 3 | MINOR | a cache folder inside the publication or staging tree defeats isolation | `_cache_conflict`, at start-up (exit 2, before any write): `--cache-dir` equal to, inside or containing `out`, or inside any sibling `<out>.*` / `.<out>.*` (the staging, failed and replaced folders of any run), resolved and case-normalised. Five existing refusal tests used `--cache-dir <wp5.7>` (which contains their `out`) and would now be refused for that reason: changed to `<wp5.7>/c` so each still tests its own refusal | 5 cases (`out`, `out/c`, `wp5.7` itself, `out.replaced-<stamp>/c`, `.out.staging-x`): exit 2 and `wp5.7` left empty |
| 4 | MINOR (test only) | the S1 tests cannot tell the source reference from the compensated one (achromatic controls; 3C an identity there) | a CHROMATIC control (`_scene`, where 3C moves pixels by more than 1e-3): `remap_balanced` = `clip(source * gains)` with the gains computed in the test from the record (strength, then the D99 clamp) and `remap_input1` = `clip(that ** gamma)`, within 1e-6; and the stage images differ from both by more than 1e-3 | one-off mutation probe (`staged_render` yielding `balanced` / `input1` as the references): `Mismatched elements: 36864 / 36864 (100%)`, `Max absolute difference among violations: 0.30065252`, FAILED, while the four achromatic S1 tests still pass under it (log `work/c57-2d-mutation.log`) |
| 5 | ADVISORY, out of envelope | on POSIX `Path.rename` can replace an existing empty directory, so the collision refusals are Windows guarantees | no code change; a stated limit (below) | - |

No measurement code changed: the edits are the publish rollback, the cache rule, a docstring and
tests; no band, record or crop value can move (no STOP; no GPU run).

### Limits (the write path; out of the instrument's envelope, a seat-run tool on the owner's single-user laptop)

- Confinement is checked at start-up and holds against pre-existing files and links; it does not
  pin ancestors against a concurrent process that swaps a directory for a junction during the run
  (out of envelope), nor against one that plants a link in the fresh staging folder before a write.
- On POSIX `Path.rename` can replace an existing EMPTY directory, so the publish-time collision
  refusals (an `out` that appeared during the run, the rollback) are Windows guarantees.

### RED (the new tests against `1e6cb6c8`'s probe)

Logs `work/c57-2d-red.log` and `work/c57-2d-red2.log` in the worktree (the old probe restored
into the working copy for the run, then the new one copied back and compared byte for byte).

- `test_main_interrupted_publish_rolls_back[True]`: the injected KeyboardInterrupt escaped
  `main` (no rollback, no message) and ended the pytest session: `!!! KeyboardInterrupt !!!` at
  the injected raise, 2 failed / 51 passed before it. Run again with that node deselected: 7
  failed, 65 passed:
- `test_main_failed_publish_and_failed_rollback_names_both_and_the_kept_folder`: `assert
  'publish-boom' in 'halo_probe: FAILED to publish: undo-boom (partial output kept in
  .out.failed-...)'` (the rollback's error replaced the original; the old publication's folder
  not named).
- `test_main_interrupted_publish_rolls_back[False]`: `assert {} == {'overview-ou...` (`out`
  absent after the interrupt: the old publication left aside).
- `test_main_refuses_a_cache_folder_in_the_publication_tree` x 5: `assert 0 == 2` (accepted).
- the chromatic S1 control PASSES on `1e6cb6c8` (finding 4 is test-only); its RED is the
  mutation probe above.

### GREEN

`uv run pytest -q tests/test_tools_halo_probe.py` 73 passed (5.7 s); `uv run ruff check .` All
checks passed; `uv run ruff format --check .` 313 files already formatted; `uv run mypy`
Success, no issues found in 157 source files.

### Round ledger (cumulative)

| Round | Reviewer | Critical | Major | Minor | Advisory | In-envelope / out | NEW / REOPENED | Reverts | Fixes: instrument / test-only / product |
|---|---|---|---|---|---|---|---|---|---|
| 0 | A (Codex, at the orchestrator's seat) | 0 | 4 | 4 | 1 | 9 / 0 | 9 / 0 | 0 | 9 / 0 / 0 |
| 1 | A (Codex, at the orchestrator's seat) | 0 | 1 | 3 | 0 | 4 / 0 | 4 / 0 | 0 | 3 / 1 / 0 |
| 2 | A (Codex, at the orchestrator's seat) | 0 | 1 (out of envelope by adjudication) | 3 | 1 (out of envelope) | 3 / 2 | 5 / 0 | 0 | 2 / 1 / 0 |

Depth at step-2D end: 309001 (scripts/cell_depth.py, wp57-cell3, read by the orchestrator at the step-2D yield 2026-11-03; cell stood down)

## Part 2

Dispatch `clearwater-review-evidence/wp5.7/cell/dispatch-5.md` (orchestrator gen 37). Fresh cell
(implementer-opus-high) on head `1bd99a4e`.

### Step 0 (Reviewer A round 3: record and fix its two minors)

Reviewer A round 3 (Codex, read-only, at the orchestrator's seat, on `1bd99a4e`; transcript
withheld): an AST comparison confirms no measurement function changed since round 1; S1, S2,
attribution with the clip, qualification and the full-frame equality checks hold; relative
paths, trailing separators, case variants and an 8.3 short name behave in the cache check; no
product divergence. Dispositions are the orchestrator's (binding).

| # | Sev | Finding | Disposition / what changed | Tests |
|---|---|---|---|---|
| 1 | MAJOR, out of envelope (adjudicated) | a junction pre-planted INSIDE the cache folder under an exact cache-entry name (`e_<size>_<mtime_ns>_<version>`): discovery skips it, but the product's cache store (`src/clearwater/cache/store.py` `_entry_for_write`) reuses the pathname and writes through it | no code change (a deliberately planted junction, a hostile local actor; the product's cache store, not owned here); a stated limit below; routed to CHARC by the orchestrator as a possible product debt item | - |
| 2 | MINOR | the first publication rename (`out.rename(replaced)`) sat outside the rollback guard: an interrupt just after it left `out` absent, no rollback, no message | `_publish`: both renames inside one guard; the rollback reads the folders to tell "renamed aside" (`out` absent, the stamped `replaced` present: rename it back) from "not yet renamed" (`out` present: move nothing), then re-raises | an interrupt injected at the `out -> replaced` rename, after it took effect and before: `out` byte-identical, the interrupt re-raised, no replaced folder, the staging folder retired |
| 3 | MINOR | after an interrupt during publication `main` caught only `OSError`, so the staging folder was not retired | `main` retires the staging folder (`_abandon`: `.<out>.failed-<stamp>`) on ANY exception from `_publish`, then exits 1 for an `OSError` (as before) or re-raises the original; `_abandon` leaves a staging folder that is already gone (the publish completed) alone | the round-2 interrupt test now also asserts no `.out.staging-*` remains and one `.out.failed-*` holds the unpublished record |

No measurement code changed (the publish path and `_abandon` only; no GPU run).

Limits, added: the analysis cache's writes go through the product's cache store, which does not
refuse a junction pre-planted under a cache-entry name (out of envelope; routed to CHARC).

RED (the new tests against `1bd99a4e`'s probe, restored into the working copy for the run and
the new probe copied back, compared byte for byte; log `work/c57-p2-step0-red.log` in the
worktree): 3 failed, 1 passed.
- `test_main_interrupt_at_the_aside_rename_rolls_back_only_what_moved[True]`: `assert {} ==
  {'overview-ou...` (`out` absent after the interrupt).
- `...[False]` and `test_main_interrupted_publish_rolls_back[False]`: `AssertionError: assert not
  [WindowsPath('.../.out.staging-...')]` (the staging folder not retired).
- `test_main_interrupted_publish_rolls_back[True]` passes on both (its rollback-failure path
  already exited 1 through the `OSError` branch).

GREEN: `uv run pytest -q tests/test_tools_halo_probe.py` 75 passed (7.6 s); `uv run ruff check .`
All checks passed; `uv run ruff format --check .` 313 files already formatted; `uv run mypy`
Success, no issues found in 157 source files.

Round ledger (cumulative):

| Round | Reviewer | Critical | Major | Minor | Advisory | In-envelope / out | NEW / REOPENED | Reverts | Fixes: instrument / test-only / product |
|---|---|---|---|---|---|---|---|---|---|
| 0 | A (Codex, at the orchestrator's seat) | 0 | 4 | 4 | 1 | 9 / 0 | 9 / 0 | 0 | 9 / 0 / 0 |
| 1 | A (Codex, at the orchestrator's seat) | 0 | 1 | 3 | 0 | 4 / 0 | 4 / 0 | 0 | 3 / 1 / 0 |
| 2 | A (Codex, at the orchestrator's seat) | 0 | 1 (out of envelope by adjudication) | 3 | 1 (out of envelope) | 3 / 2 | 5 / 0 | 0 | 2 / 1 / 0 |
| 3 | A (Codex, at the orchestrator's seat) | 0 | 1 (out of envelope by adjudication) | 2 | 0 | 2 / 1 | 3 / 0 | 0 | 2 / 0 / 0 |

Reviewer A CONVERGED at round 3 (no in-envelope critical or major).

### Step 1 (the candidate settings, the switches)

Every setting is in the direction that should shrink the band; at least one modest and one strong
per candidate, in CHARC's order. Folder `work/wp5.7/part2/<setting>/<item>`.

| Order | Candidate | Settings (folder) | Why these | How applied |
|---|---|---|---|---|
| - | shipped defaults | `defaults` | the baseline of the schema-4 record and a determinism check against `part1s` (every band must equal it) | no override |
| 1 | (a) sharpening strength (6.7 Basic; default 1.0) | 0.75 (`a-0.75`), 0.5 (`a-0.5`), 0.25 (`a-0.25`) | input 2 = `I + s (S - I)`, so its added band scales about linearly with s: 0.75 modest, 0.25 strong (the fused bands are 1.0-3.2 x C, so only a strong step can bring them near the 0.10 threshold) | `--param sharpen_strength=` |
| 2 | (e1) N{} percentiles (6.7 Advanced; 0.5 / 99.5) | 0.1 / 99.9 (`e1-0.1`), 0.01 / 99.99 (`e1-0.01`), 0 / 100 (`e1-0`) | a wider percentile pair widens the measured range and lowers the stretch; 0.1 / 99.9 modest, 0 / 100 (min / max of the high-pass) the strongest the schema allows | `--param normalisation_low= --param normalisation_high=` |
| 3 | (e2) N{} range floor (AD-4 / DR-14; 0.02) | 0.05 (`e2-0.05`), 0.1 (`e2-0.1`), 0.2 (`e2-0.2`) | the measured proxy ranges are 0.018-0.051 (photos) and 0.023-0.036 (videos): 0.05 binds on every item but IMG_6739 (0.0512) and caps the stretch at 20 x; 0.1 and 0.2 cap it at 10 x and 5 x (WP1.4b measured ranges up to 0.64 on other footage, where these floors would not bind) | switch `range_floor=F`: a scoped patch of `clearwater.methods.fusion.NORMALISATION_RANGE_FLOOR`, which `_floored` reads at call time, so `fusion_inputs` sees it in `render`, in `analyze` (input 2's saliency mean) and in the staged render |
| 4 | (d) input 2 clipped to a local range (algorithm change in `fusion_inputs`) | half window 1 sigma (strong: a tight window) and 3 sigma (modest), per reference: `d-<ref>-1`, `d-<ref>-3` | the ring sits 1-2 sharpening sigmas from the edge (the fused FWHM of the step-2A table is 0.14-1.88 sigma), so a 1-sigma window sees only water there; a 3-sigma window spans the edge and clips less | switch `clip_overshoot=REF:R`: a scoped patch of `ancuti_fusion.fusion_inputs` (the name `render` and `analyze` call) and of the probe's `fusion_inputs` (the name `staged_render` calls) with `clipped_fusion_inputs`, which calls the product's `fusion_inputs` and clips input 2 per channel to the min / max of the reference over a square window of half side `round(R x sigma)` px (edges replicated). **The reference is a STOP question (below).** |
| 5 | (e3) N{} bounds on the full-resolution frame (AD-4) | one setting (`e3-full`) | binary: proxy or full resolution | photos: switch `full_res_bounds`: the white-balance record is measured on the proxy as shipped, the bounds are the full-resolution white-balanced image's percentiles (`_full_bounds`, the Part 1 diagnostic), and the fusion stage is then measured on the proxy with `ancuti_fusion.normalisation_bounds` patched to return them (so input 2's saliency mean follows the new bounds, as the product would measure it). Video: refused for now (question below). |
| 6 | (b) pyramid minimum level size (6.7 Advanced; 16) | 8 (`b-8`), 4 (`b-4`) | one and two levels deeper (the hypothesis was rejected in Part 1; measured for completeness) | `--param pyramid_min_level_size=` |
| 7 | (c) weight regularisation delta (0.1, the paper's) | 0.3 (`c-0.3`), 1.0 (`c-1.0`) | a larger delta pulls both normalised weights toward 1/2, lowering input 2's edge preference (Wbar2 0.60-0.71 at the edge); 1.0 is the schema's maximum | `--param weight_delta=`: **a premise correction**: delta is ALREADY a method parameter (`methods/schema.py` `_WEIGHT_DELTA`, Advanced panel, 0.001-1.0, default 0.1, "paper value 0.1"), so no switch is needed and the brief's "selectable with the paper's value kept" condition already holds. A delta above 1.0 would need a switch: not proposed. |

The render-equality check under a switch: the candidate's analysis (the photo proxy statistics, or
the whole-clip `AnalysisEngine` run), the staged render and the product's `render` all run inside
`applied(switches)`, so `render_check_equal` compares the staged render with the product's render
under the SAME switch; the shipped-defaults baseline (statistics and render) runs outside it.
`applied` restores every patched attribute to its original object on any exit (tests below).

The whole-image change (`whole_image`, schema 4): every run whose parameters or switches differ
from the shipped defaults also renders the item at the shipped defaults, unswitched (photo: its own
proxy statistics; video: a second whole-clip analysis), and records per frame: the per-channel
mean and its shift, the clipped-pixel fraction (any channel at 0 or 1) of both, the mean and the
99th percentile of the absolute per-value difference, and V3's four per-frame measures (mean L*,
a*, b*, standard deviation of L*, as `tests/test_analysis_v3.py` forms them, but over the WHOLE
frame) of both. Part 3's edge-band scan does not exist yet: not used. Flicker on GX011627's last
second (step 3): the standard deviation of the frame-to-frame differences of each measure over
the 30 frames 21.7-22.7 s, candidate against the baseline from the same run: a whole-frame
temporal diagnostic, NOT V3 (corrected at step 3R: V3 needs an untouched region of a synthetic
clip and a smoothed against unsmoothed comparison; see half 2's (ii)). The statistics column
(cache invalidation): the record carries both the candidate's and the baseline's smoothed
`bounds` and `saliency_means` per frame.

### STOP questions (dispatch: ambiguous -> ask, never guess)

**Q-d (the reference of candidate (d)). "Clipping input 2's overshoot to the local range of input
1" read literally clips input 2 to the local range of `I ** gamma`; but input 2 is not near input 1
anywhere, so the literal reading moves input 2 on every flat region, not only at edges.**
Reproduction (CPU, synthetic water with a gentle gradient, a dark disc, noise 0.004; shipped
defaults; scratch `d_repro.py`, not committed): input 2's mean on open water far from the edge and
the whole-output mean absolute change, per reading:

| Reading (reference) | Input 2 on open water (R, G, B), shift vs shipped | Output mean abs change | Input 2 / fused band x C on the edge line |
|---|---|---|---|
| shipped (no clip) | 0.466, 0.466, 0.467 | - | 0.884 / 0.514 |
| `input1` (literal), 1 sigma | -0.176, -0.176, -0.175 | 0.093 | 0.002 / 0.000 |
| `input1` (literal), 3 sigma | -0.173 | 0.091 | 0.007 / 0.003 |
| `balanced` (the white-balanced I), 1 sigma | -0.030 | 0.024 | 0.006 / 0.003 |
| `balanced`, 3 sigma | -0.028 | 0.022 | 0.013 / 0.005 |
| `unsharpened` (input 2 with a zero high-pass), 1 sigma | 0.000 | 0.017 | 0.006 / 0.000 |
| `unsharpened`, 3 sigma | 0.000 | 0.017 | 0.011 / 0.000 |

Why: input 2 = `(I + N{hp}) / 2`, and on a flat region N{hp} sits near N{0} (about 0.5), so input
2 is about `(I + 0.5) / 2`: neither `I ** gamma` (literal) nor `I` lies near it, and clipping to
their local range pulls the whole of input 2 toward them (a tone change, not an overshoot clip).
The `unsharpened` reference is input 2's own form without the high-pass, so it equals input 2 on
flat regions and clips only what the sharpening adds beyond the local extremes (the classic
clamped unsharp mask, the overshoot control of sharpening tools); its residual 0.017 output change
is the amplified-noise texture it also limits. All three are built (`--switch
clip_overshoot=input1|balanced|unsharpened:R`). RECOMMENDED: measure `unsharpened` as (d) of
record; the literal `input1` and `balanced` as two extra rows (4 photo settings, about 5 min) so
the ruling is informed by the real items; or CHARC names one.

**Q-e3v (candidate (e3) on video).** On a video the bounds are per-frame statistics measured on
the proxy and then smoothed (spec 7, IF-3). Proposed design (not built until ruled): (1) the
shipped-defaults analysis (already run as the baseline) gives each frame's smoothed white-balance
record; (2) a full-resolution decode pass over the WHOLE clip measures each frame's bounds on the
frame compensated and white-balanced with that record (as the fusion stage measures them on the
proxy); (3) a second analysis run with `ancuti_fusion.normalisation_bounds` patched to return that
frame's full-resolution bounds (keyed by the pts the engine reads its proxy for), so the engine
measures input 2's saliency mean on the proxy with them and smooths both as shipped. Cost: one
extra full-resolution decode and compensation per frame (GX011627 about 680 4K frames, the
compilation excerpt about 1,870 1080p frames). Alternative: drop (e3) on video by the step-3 rule
(not allowed if it shrinks a photo band) or state it unmeasured (then it is not proposable as a
default). RECOMMENDED: build the design above at step 3 if (e3) shrinks a decided photo band.

### RED (the new tests against `22817c9f`'s probe; log `work/c57-p2-switch-red.log` in the worktree): 11 failed, 75 passed

`AttributeError: module 'halo_probe' has no attribute 'Switches'` (x 6: the floor switch, the
three clip references, the clean-step ring, the video baseline), `... 'parse_switches'`, `...
'whole_image'`, `KeyError: 'baseline_statistics'` (the whole-image record), `SystemExit: 2` x 2
(`--switch` unknown: full_res_bounds, a bad switch). The old probe restored into the working copy
for the run, the new one copied back and compared byte for byte.

Tests added (11, parallel leg, CPU, synthetic): switch parsing and refusals (9 bad forms); (e2) the
floor reaches `render` AND `analyze` (input 2's saliency mean moves) with the staged render equal
to the product's, restored after a normal exit and after an exception; (d) for each reference,
input 2 lies within the reference's local min / max (scipy recomputation in the test), the staged
output equals `render`'s under the switch, the clip binds, restored on exit; (d) on a clean
softened step input 2's ring is over 0.1 unswitched and under 0.01 clipped (`unsharpened`, 1
sigma); `whole_image` on constructed arrays (clipped fraction, mean shift, mean abs difference;
zeros against itself); `main` at defaults (no baseline, zero change) and at `sharpen_strength=0.5`
(the baseline equals the defaults run's own statistics and means); (e3) the record's bounds equal
the full-resolution diagnostic and differ from the proxy baseline (proxy forced to a 2 x 2 block
mean), restored after `main`; a bad switch exits 2 with no output; the video path analyses the
baseline unswitched (floor 0.02) and the candidate switched (0.3), records the baseline statistics
and the change, and refuses `full_res_bounds`.

### GREEN

`uv run pytest -q tests/test_tools_halo_probe.py` 86 passed (9.7 s); `uv run ruff check .` All
checks passed; `uv run ruff format --check .` 313 files already formatted; `uv run mypy` Success,
no issues found in 157 source files.

### Photo commands (step 2; not run before the dispatcher resumes the cell)

`bash C:/Users/rwsmy/clearwater/work/wp5.7/part2/run-photos.sh [SETTING ...]` (not committed; in
the outputs folder): `df` check first (exits 3 under 25 GB), then for each setting in the order of
the table and each of IMG_6739, IMG_6743, IMG_6744, one process at a time on the GPU:

    uv --directory <worktree> run python tools/halo_probe.py <item> <Part 1 lines> --margin 120 \
        --out <work>/wp5.7/part2/<setting>/<item> <--param ... | --switch ...>

with the Part 1 lines (IMG_6739 `1700,2500,2200,2500`, `1560,2300,1810,2300`,
`2900,2300,2450,2300`; IMG_6743 `2450,600,1850,600`, `835,1008,1132,670`; IMG_6744
`1300,950,1300,450`, `2550,200,2100,200`). 21 settings x 3 photos = 63 runs (17 settings, 51 runs,
if Q-d is ruled to one reference). Estimate: `part1s` took 17-34 s per photo; the baseline render
adds about 3-5 s: about 25 s a run, so about 26 min for all 21 settings (about 21 min for 17).

Depth at mid-build yield 1: 241011 (scripts/cell_depth.py, wp57-cell4, read by the orchestrator at the yield 2026-11-03)

### Rulings on the yield-1 questions (CHARC msg 8d65e90c, relayed by the orchestrator)

- **Q-d:** (d) of record = the `unsharpened` reference; the `input1` (literal) and `balanced`
  references are measured and reported as rows (all 21 photo settings).
- **Q-e3v:** build (e3) on video ONLY if it shrinks a decided photo band; otherwise state it
  UNMEASURED on video (then not proposable as a default).
- **(c) premise correction accepted:** `weight_delta` via `--param` 0.3 / 1.0.

### Step 2 (photos; head `c65332be`; GPU; outputs `work/wp5.7/part2/<setting>/<item>`)

`bash work/wp5.7/part2/run-photos.sh` in three chunks (6, 8 and 7 settings): 63 runs, every one
exit 0 (so every render check and prefused check held under its switch), 9-21 s a run, 18 min
in all (09:44:41Z-10:02:28Z); free disk 71 GB before, 71 GB after. Walls `part2/logs/runs.txt`,
the full per-line table `part2/table-photos.txt` (a scratch tabulator, not committed).
Determinism: the `defaults` runs equal `part1s` on every water band of every stage and channel
(max difference 0).

The candidate table (photos). The DECIDED lines of the Part 1 table of record are IMG_6739 line
3 (right flank), IMG_6743 lines 1 and 2; IMG_6744 has none. Cells: the fused luma band x C, its
verdict (`*` band, `?` undecided, `-` none) and the fused FWHM in px. Every qualifying fused band
in the table is attributed to input 2 (no other attributed stage on any line, so no STOP).
"Undecided" = lines whose fused verdict is undecided, out of 3 / 2 / 2. Whole-image change
against the shipped defaults (each run's own baseline render): the mean absolute per-value
difference per photo (6739 / 6743 / 6744), the largest per-channel mean shift over the three,
and the 99th-percentile difference (largest). The clipped-pixel fraction moves by at most 0.0004
on any run (IMG_6739 0.0004 shipped; the others 0.0000 shipped and switched): not tabled.

| Setting | 6739 L3 | 6743 L1 | 6743 L2 | Undecided 6739/6743/6744 | Mean abs change | Max mean shift | p99 |
|---|---|---|---|---|---|---|---|
| shipped | 3.07* w7 | 1.48* w32 | 2.32* w22 | 2/0/2 | - | - | - |
| (a) 0.75 | 2.27* w7 | 1.05* w31 | 1.63* w22 | 2/0/2 | .010/.017/.017 | .004 | .048 |
| (a) 0.5 | 1.52? | 0.66* w31 | 1.00? | 3/1/2 | .020/.033/.034 | .007 | .092 |
| (a) 0.25 | 0.82? | 0.30* w26 | 0.43? | 3/1/2 | .030/.048/.049 | .010 | .131 |
| (e1) 0.1/99.9 | 1.93? | 1.43* w28 | 1.98* w12 | 3/0/2 | .021/.031/.025 | .016 | .093 |
| (e1) 0.01/99.99 | 0.77? | 0.94* w25 | 0.97* w11 | 3/0/2 | .039/.049/.054 | .039 | .154 |
| (e1) 0/100 | 0.21? | 0.44* w23 | 0.43? | 2/1/2 | .065/.062/.071 | .060 | .198 |
| (e2) 0.05 | 3.07* w7 (floor not binding: range 0.0512) | 1.20* w27 | 1.48* w11 | 2/0/2 | .000/.037/.039 | .005 | .104 |
| (e2) 0.1 | 1.73? | 0.61* w24 | 0.61* w11 | 3/0/2 | .019/.050/.051 | .007 | .139 |
| (e2) 0.2 | 0.70? | 0.26* w22 | 0.24? | 3/1/1 | .029/.056/.057 | .009 | .156 |
| **(d) unsharpened 1 sigma** | 0.24? | 0.03- | 0.03- | 2/0/0 | .034/.059/.060 | .013 | .173 |
| **(d) unsharpened 3 sigma** | 0.24? | 0.05- | 0.06- | 3/0/0 | .032/.057/.058 | .012 | .171 |
| (d) balanced 1 sigma (row) | 0.75? | 0.11? | 0.11? | 2/2/1 | .030/.055/.056 | .012 | .161 |
| (d) balanced 3 sigma (row) | 0.93? | 0.17? | 0.26? | 3/2/1 | .025/.052/.053 | .011 | .158 |
| (d) input1 1 sigma (row) | 0.54? | 0.11? | 0.07- | 2/1/0 | .058/.067/.069 | .054 | .216 |
| (d) input1 3 sigma (row) | 0.35? | 0.10- | 0.12? | 3/1/1 | .052/.063/.065 | .049 | .212 |
| (e3) full-res bounds | 2.33? | 1.32* w30 | 2.00* w17 | 3/0/2 | .013/.024/.024 | .002 | .064 |
| (b) 8 | 3.10* | 1.47* (1.4749) | 2.33* | 2/0/2 | .001/.001/.001 | .000 | .004 |
| (b) 4 | 3.10* | 1.48* (1.4755) | 2.33* | 2/0/2 | .002/.002/.002 | .000 | .007 |
| (c) 0.3 | 2.94* | 1.30* | 2.04* | 2/0/2 | .003/.005/.005 | .004 | .024 |
| (c) 1.0 | 2.83* | 1.16* | 1.84* | 2/0/2 | .005/.009/.009 | .006 | .039 |

Readings (measurement, not a look judgement):

- **(d) `unsharpened` leaves no qualifying fused band on the three photos, but shows a band
  ABSENT (`none`) on only two of the three decided lines** (corrected at step 3R; this line first
  said "removes every qualifying fused band", counting `undecided` as removal). Over the decided
  lines, band / none / undecided = 0 / 2 / 1 at 1 and at 3 sigma: IMG_6743 both lines `none`
  (0.03-0.06 x C); IMG_6739 line 3 0.24 x C `undecided`, which by S3 is not evidence either way
  (IMG_6744's two lines, never decided, go to `none`). Its whole-image change is NOT small by
  these figures: mean abs 0.032-0.060 (8-15 / 255), p99 0.17, a largest channel-mean shift 0.013.
  The change is mostly input 2's amplified noise and fine texture, which the clip also limits
  everywhere (the synthetic reproduction of Q-d showed the same kind: 0 plateau shift, 0.017 output
  change from texture). So the stop-early condition ("removes every qualifying band ... with a
  whole-image change you can state as small") is NOT met; the videos are unmeasured too.
- Every other candidate scales the band down with its strength and none reaches the threshold on
  IMG_6743 at the settings tried: (a) 0.25 leaves 0.30 x C; (e2) 0.2 leaves 0.26; (e1) 0 / 100
  leaves 0.44 (and shifts the channel means up to 0.060). At equal band reduction, (a) and (e2)
  cost the least whole-image change (for example IMG_6743 L1 at about 0.6-0.66 x C: (a) 0.5 mean
  abs 0.033, (e2) 0.1 0.050; at about 0.26-0.30: (a) 0.25 0.048, (e2) 0.2 0.056).
- Several candidates turn decided lines undecided (a cost, not a cure): (a) 0.5 / 0.25, (e1),
  (e2) 0.1 / 0.2, (e3) on IMG_6739 line 3 (its band falls under its own noise level); (d)
  `balanced` turns both IMG_6743 lines undecided at 0.11-0.26.
- (d) `input1` (literal) shifts the channel means by about 0.05 on every photo (the tone change
  the Q-d reproduction predicted) and makes a broad new feature on IMG_6739 line 1 at 3 sigma
  (2.29 x C, FWHM 134 px, undecided).
- (e3) shrinks the decided IMG_6743 bands (1.48 -> 1.32, 2.32 -> 2.00) at a small whole-image
  cost (mean abs 0.013-0.024, channel-mean shift 0.002), so by Q-e3v it IS built for video at step
  3.
- (b) moves nothing material (the pyramid hypothesis stays rejected): IMG_6743 L1 falls by 0.004 x
  C (0.3 %), the other decided bands rise by up to 0.03 x C. (c) shrinks every band by 4-22 % at a small
  whole-image cost (mean abs at most 0.009).

### Videos (step 3; not run)

In contention: every candidate. Only one that made NO decided photo band smaller may be dropped,
and every candidate made at least one smaller: (b) only by IMG_6743 L1's 0.004 x C (1.4787 ->
1.4749 / 1.4755), which is within the literal rule; CHARC may judge that negligible and drop (b).

Command (not committed; outputs folder): `bash C:/Users/rwsmy/clearwater/work/wp5.7/part2/run-videos.sh
SETTING ...` (`df` check first, exits 3 under 25 GB): per setting, IMG_6738, GX011627 and the
compilation excerpt (read in place from `work/wp5.3/excerpts/`), the Part 1 lines, times, crops
and margins, the analysis cache `scratch/cache`, `--out part2/<setting>/<item>`. `e3-full` needs
the video (e3) build first (Q-e3v design: one full-resolution decode pass over each whole clip).

Estimate: `part1s` took 48 + 126 + 107 = 281 s for the three; a non-default run adds the baseline's
second whole-clip analysis and one baseline render per frame (110 frames): about 6-7 min a
setting. All 21 settings about 2.3 h; plus (e3) on video (its build, then a full-resolution pass:
about 680 4K and 1,870 1080p frames, perhaps 10-15 min). A reduced set (defaults; (a) 0.5, 0.25;
(e1) 0.01, 0/100; (e2) 0.1, 0.2; (d) unsharpened 1, 3; (e3); (b) 4; (c) 1.0: 12 settings) about
80 min plus (e3).

Depth at mid-build yield 2: 268700 (scripts/cell_depth.py, wp57-cell4, read by the orchestrator at the yield 2026-11-03)

### Step 3, half 1: (e3) on video (head `daa5df3a`)

Orchestrator's video set (within the drop rule; every candidate represented): defaults; (a) 0.5,
0.25; (e1) 0.01 / 99.99, 0 / 100; (e2) 0.1, 0.2; (d) unsharpened 1 and 3 sigma; (e3); (b) 4;
(c) 1.0 (12 settings).

Built per CHARC's Q-e3v design (`full_res_bounds_by_pts`, `_PtsRecordingCache`, `applied`'s
`bounds` now also a function): (1) the white balance comes from a completed analysis under the run's
parameters (the shipped-defaults baseline analysis when the run is (e3) alone, else an extra
analysis under the other switches); (2) one software-decode pass over the WHOLE clip measures each
frame's bounds on the full-resolution frame compensated and white-balanced with that frame's
smoothed record (`_full_bounds`, the Part 1 diagnostic); (3) the candidate analysis runs with
`ancuti_fusion.normalisation_bounds` patched to return the bounds of the frame whose proxy the
engine read last (`AnalysisEngine._measure` reads `cache.proxy(key, pts)` immediately before
`analyze`; the probe wraps the cache to record that pts), so the engine measures input 2's
saliency mean with them on the proxy and smooths both as shipped. A measurement with no recorded
pts, or one the pass did not deliver, fails the run (`ProbeFailedError`). The record carries
`full_res_bounds_frames`. Not exercised on a real clip in half 1 (no GPU render; the first real
run is the `e3-full` setting of the batch).

RED (the two new tests against `daa5df3a`'s probe; log `work/c57-p2-e3v-red.log` in the worktree):
2 failed, 86 passed, both `halo_probe.ProbeError: --switch full_res_bounds is built for photos
only`. Tests: with five frames that differ and the proxy forced to a 2 x 2 block mean, each
frame's smoothed fusion bounds equal that frame's full-resolution bounds and differ from the
proxy-measured baseline's and from every other frame's, two engines (the baseline reused for the
white balance), the patch restored; an analysis that reads no proxy fails with "no
full-resolution bounds" and the patch is restored. The step-1 video test's refusal assertion is
removed (the refusal is gone).

GREEN: `uv run pytest -q tests/test_tools_halo_probe.py` 88 passed (12.7 s); `uv run ruff check .`
All checks passed; `uv run ruff format --check .` 313 files already formatted; `uv run mypy`
Success, no issues found in 157 source files.

Video command (half 2, one setting per foreground call, each well under 10 min):
`bash C:/Users/rwsmy/clearwater/work/wp5.7/part2/run-videos.sh <setting>` for defaults a-0.5
a-0.25 e1-0.01 e1-0 e2-0.1 e2-0.2 d-unsharpened-1 d-unsharpened-3 e3-full b-4 c-1.0. Estimate
about 6-7 min a setting (the baseline's second whole-clip analysis and one baseline render per
frame on top of `part1s`' 281 s): about 75-85 min for the twelve, plus about 5-10 min for the
`e3-full` full-resolution pass (a second whole-clip decode of each item).

Depth at mid-build yield 2b: 286396 (scripts/cell_depth.py, wp57-cell4, read by the orchestrator at the yield 2026-11-03)

### Step 3, half 2: the video batch and the candidate table

Dispatch `clearwater-review-evidence/wp5.7/cell/dispatch-7.md` (orchestrator gen 38). Fresh cell
`wp57-cell5` (implementer-opus-high) on head `9ffca3cf`. No GPU run, no render, no pytest: every
figure below is read from the batch's JSON records by a scratch tabulator
(`work/c57-p2h2/tabulate.py` in the worktree, not committed; its output
`work/c57-p2h2/table-videos.txt`, 309 lines, every number below is from it or from
`part2/table-photos.txt`).

**The batch.** `run-videos.sh` ran at the orchestrator's seat 12:17:17Z-13:40:36Z, free C: 64 GB
before (60 GB after). `part2/logs/runs-video.txt`: 36 runs (12 settings x 3 items), every one
`exit=0`, walls 57-301 s. Each log ends on a normal summary line and holds no `Traceback`,
`FAILED` or `error`; each `part2/<setting>/<item>/<item>.json` exists; no staging or failed
folder is left. In every record every frame has `render_check_equal` and `prefused_check_equal`
true (render difference 0.0), and its frames are the `part1s` frames, pts for pts (49 / 30 / 30).

**Determinism.** The `defaults` video records equal `part1s` on every water band of every stage
and channel: max difference 0 over every numeric field (IMG_6738 3,136 band records, GX011627
960, the compilation 2,880), and the smoothed statistics are equal too (max difference 0). In
every candidate run the baseline render (shipped defaults, unswitched, from its own second
analysis) has per-frame channel means equal to the `defaults` run's own (max difference 0).

**The measured set.** "Decided" = the frame-lines whose FUSED luma verdict is `band` in the
Part 1 table of record (`part1s`): IMG_6738 17, GX011627 9, the compilation 5 (31; all
attributed input 2). The selector's decided count is 19 / 9 / 6: on two IMG_6738 lines and one
compilation line input 2 qualifies but the fused band is undecided; those, and any band a
candidate creates elsewhere, are covered by the "all non-weak" counts. Featured frames: IMG_6738
0.833 s line 2; GX011627 22.122 s (its one line); the compilation 27.010 s line 1 (as the
dispatches name it: 3.87 x C / 0.131, first qualifying `fused`) AND line 3 (the shin of the
Part 1 table and of step 2B's "featured frames", 3.22 / 0.200): both are tabled (see the open
question in the return report).

#### The video candidate table

Per item: the decided frame-lines' fused verdicts after the candidate (band / undecided / none);
the largest fused band x C over them and the largest absolute band; the median fused FWHM (px)
over those still `band`; the undecided count over ALL non-weak frame-lines (83 / 14 / 56) and
any NEW qualifying band (a non-decided line that qualifies under the candidate); the whole-image
change against the run's own shipped-defaults render (the mean over the frames of the mean
absolute per-value difference; the largest per-channel mean shift over frames and channels; the
largest per-frame 99th percentile). The clipped-pixel fraction moves by at most 0.0004 on any
frame of any run (baseline 0.0001-0.0004): not tabled. Every qualifying fused band in every run
is attributed to input 2.

| Setting | Item | Decided: b / u / n | Max x C / abs | FWHM | Undecided (non-weak); new | Mean abs | Max shift | p99 |
|---|---|---|---|---|---|---|---|---|
| shipped | 6738 | 17 / 0 / 0 | 5.40 / .196 | 9.7 | 57; - | - | - | - |
| shipped | GX | 9 / 0 / 0 | 7.42 / .162 | 15.9 | 3; - | - | - | - |
| shipped | comp | 5 / 0 / 0 | 6.77 / .200 | 6.2 | 36; - | - | - | - |
| (a) 0.5 | 6738 | 13 / 4 / 0 | 2.41 / .086 | 9.4 | 39; 1 (1.333 s L2, 0.25) | .0169 | .0105 | .073 |
| (a) 0.5 | GX | 6 / 3 / 0 | 3.39 / .076 | 16.1 | 6; 0 | .0180 | .0180 | .068 |
| (a) 0.5 | comp | 3 / 2 / 0 | 3.11 / .093 | 6.7 | 32; 0 | .0231 | .0351 | .086 |
| (a) 0.25 | 6738 | 7 / 9 / 1 | 1.13 / .042 | 13.0 | 29; 0 | .0248 | .0158 | .104 |
| (a) 0.25 | GX | 1 / 8 / 0 | 1.64 / .037 | 18.9 | 10; 0 | .0267 | .0272 | .097 |
| (a) 0.25 | comp | 2 / 3 / 0 | 1.51 / .046 | 11.6 | 24; 0 | .0343 | .0539 | .123 |
| (e1) 0.01/99.99 | 6738 | 13 / 4 / 0 | 1.90 / .117 | 8.9 | 33; 0 | .0205 | .0189 | .094 |
| (e1) 0.01/99.99 | GX | 7 / 2 / 0 | 3.27 / .076 | 9.3 | 2; 2 (22.623 s 0.32, 22.689 s 0.38) | .0182 | .0187 | .089 |
| (e1) 0.01/99.99 | comp | 2 / 3 / 0 | 2.27 / .141 | 10.1 | 27; 0 | .0147 | .0078 | .100 |
| (e1) 0/100 | 6738 | 10 / 6 / 1 | 0.92 / .056 | 9.1 | 19; 0 | .0260 | .0252 | .114 |
| (e1) 0/100 | GX | 2 / 5 / 2 | 1.19 / .028 | 9.7 | 7; 0 | .0261 | .0283 | .106 |
| (e1) 0/100 | comp | 1 / 4 / 0 | 0.91 / .057 | 3.2 | 13; 0 | .0226 | .0216 | .134 |
| (e2) 0.1 | 6738 | 11 / 5 / 1 | 1.15 / .072 | 8.9 | 22; 0 | .0194 | .0057 | .101 |
| (e2) 0.1 | GX | 9 / 0 / 0 | 5.56 / .121 | 10.4 | 0; 2 (22.623 s 0.55, 22.689 s 0.71) | .0120 | .0078 | .074 |
| (e2) 0.1 | comp | 2 / 3 / 0 | 2.29 / .142 | 10.1 | 24; 0 | .0143 | .0056 | .100 |
| (e2) 0.2 | 6738 | 4 / 10 / 3 | 0.52 / .030 | 8.9 | 16; 0 | .0219 | .0068 | .115 |
| (e2) 0.2 | GX | 7 / 2 / 0 | 2.37 / .055 | 9.2 | 3; 1 (22.689 s, 0.27) | .0153 | .0106 | .102 |
| (e2) 0.2 | comp | 1 / 4 / 0 | 1.13 / .070 | 3.2 | 13; 0 | .0169 | .0066 | .121 |
| **(d) unsharpened 1 sigma** | 6738 | 0 / 3 / 14 | 0.20 / .006 | - | 3; 0 | .0240 | .0096 | .126 |
| **(d) unsharpened 1 sigma** | GX | 0 / 5 / 4 | 0.29 / .012 | - | 5; 0 | .0153 | .0046 | .121 |
| **(d) unsharpened 1 sigma** | comp | 1 / 1 / 3 | 0.21 / .009 | 6.6 | 1; 0 | .0185 | .0050 | .140 |
| **(d) unsharpened 3 sigma** | 6738 | 1 / 5 / 11 | 0.38 / .014 | 4.8 | 8; 0 | .0226 | .0090 | .123 |
| **(d) unsharpened 3 sigma** | GX | 0 / 5 / 4 | 0.66 / .022 | - | 5; 0 | .0143 | .0042 | .117 |
| **(d) unsharpened 3 sigma** | comp | 0 / 3 / 2 | 0.51 / .012 | - | 7; 0 | .0174 | .0046 | .137 |
| (e3) full-res bounds | 6738 | 16 / 1 / 0 | 5.71 / .202 | 9.9 | 59; 1 (1.333 s L2, 0.63) | .0022 | .0005 | .011 |
| (e3) full-res bounds | GX | 9 / 0 / 0 | 7.75 / .169 | 15.9 | 3; 0 | .0056 | .0059 | .007 |
| (e3) full-res bounds | comp | 5 / 0 / 0 | 6.93 / .205 | 6.2 | 36; 0 | .0032 | .0034 | .009 |
| (b) 4 | 6738 | 17 / 0 / 0 | 5.41 / .196 | 9.8 | 57; 0 | .0016 | .0002 | .007 |
| (b) 4 | GX | 9 / 0 / 0 | 7.42 / .161 | 15.9 | 3; 0 | .0009 | .0001 | .005 |
| (b) 4 | comp | 5 / 0 / 0 | 6.76 / .200 | 6.2 | 36; 0 | .0008 | .0001 | .004 |
| (c) 1.0 | 6738 | 14 / 3 / 0 | 4.59 / .164 | 10.0 | 57; 1 (1.333 s L2, 0.47) | .0035 | .0019 | .020 |
| (c) 1.0 | GX | 8 / 1 / 0 | 6.50 / .144 | 15.9 | 5; 0 | .0020 | .0010 | .019 |
| (c) 1.0 | comp | 3 / 2 / 0 | 5.87 / .172 | 7.1 | 37; 0 | .0025 | .0072 | .018 |

The two (d) residuals: 1 sigma, the compilation 27.010 s line 3, 0.15 x C / 0.009 (shipped 3.22 /
0.200; level 0.12, support 4); 3 sigma, IMG_6738 0.700 s line 2, 0.19 x C / 0.014 (shipped 2.44 /
0.182; level 0.17, support 4). Both attributed to input 2.

The featured frame-lines (fused band x C / abs, verdict `*` band, `?` undecided, `-` none):

| Setting | 6738 0.833 s L2 | GX 22.122 s | comp 27.010 s L1 | comp 27.010 s L3 |
|---|---|---|---|---|
| shipped | 1.45 / .163 * | 1.84 / .162 * | 3.87 / .131 * | 3.22 / .200 * |
| (a) 0.5 | 0.65 / .073 * | 0.86 / .076 * | 1.73 / .059 ? | 1.50 / .093 * |
| (a) 0.25 | 0.30 / .034 * | 0.42 / .037 ? | 0.81 / .028 ? | 0.75 / .046 * |
| (e1) 0.01/99.99 | 0.61 / .068 * | 0.52 / .045 ? | 0.92 / .031 ? | 2.27 / .141 * |
| (e1) 0/100 | 0.29 / .033 * | 0.19 / .017 ? | 0.38 / .013 ? | 0.91 / .057 * |
| (e2) 0.1 | 0.38 / .043 * | 0.88 / .077 * | 1.01 / .034 ? | 2.29 / .142 * |
| (e2) 0.2 | 0.16 / .018 ? | 0.37 / .033 ? | 0.46 / .016 ? | 1.13 / .070 * |
| (d) unsharpened 1 sigma | 0.03 / .004 - | 0.04 / .003 - | 0.05 / .002 - | 0.15 / .009 * |
| (d) unsharpened 3 sigma | 0.06 / .006 - | 0.04 / .003 - | 0.04 / .001 - | 0.19 / .012 ? |
| (e3) full-res bounds | 1.47 / .165 * | 1.92 / .169 * | 3.95 / .134 * | 3.31 / .205 * |
| (b) 4 | 1.44 / .162 * | 1.83 / .161 * | 3.86 / .131 * | 3.22 / .200 * |
| (c) 1.0 | 1.15 / .129 * | 1.64 / .144 * | 3.17 / .107 ? | 2.77 / .172 * |

#### The video consequence (CHARC's condition)

(i) Statistics / cache invalidation. Code path: the `c3` stages (`methods/ancuti_fusion.py`
`C3_STAGES`) are `white_balance` (means, gains) and `fusion` (bounds, saliency means of the two
inputs), both smoothed; `fusion` depends on `_FUSION_PARAMETERS` (white-balance strength and
cap, `sharpen_blur_fraction`, `normalisation_low` / `_high`, `gamma`, `sharpen_strength`), and
`analyze` measures `normalisation_bounds` on the proxy then forms the inputs with `fusion_inputs`
(so the range floor and (d)'s clip reach input 2's saliency mean). The engine's change detection
(`analysis/engine.py` `set_parameters`, and `analysis/store.py` `schema_hash`) sees only those
named parameters. For `c3` the disk cache (`cache/store.py`) holds the proxies only (no
source-only stage), and no candidate changes a proxy. Confirmed from the records: each candidate
run's per-frame smoothed `statistics` against its `baseline_statistics` (largest absolute
difference over the frames of the three items; white-balance records and input 1's saliency
mean are unchanged, 0, in every run):

| Candidate | Fusion statistics changed (records) | Through the engine's change detection | Cache invalidation |
|---|---|---|---|
| (a) sharpening strength | input 2 saliency mean 2.25-7.45 (Lab); bounds 0 | yes: a fusion parameter (schema hash) | YES (fusion stage recomputed; proxies kept) |
| (e1) N{} percentiles | bounds 0.030-0.221; input 2 saliency mean 1.05-5.25 | yes: a fusion parameter | YES (as (a)) |
| (e2) range floor | input 2 saliency mean 0.44-2.74; bounds 0 (the floor widens them downstream, in `fusion_inputs`) | no: a module constant (AD-4 / DR-14), not in the hash | YES: the statistics change, but no parameter names it, so no live change would trigger a recompute; shipped, it changes every analysis from then on (no persisted statistic depends on it: the `c3` disk cache holds proxies only) |
| (d) clip to the unsharpened range | input 2 saliency mean 0.15-0.29; bounds 0 | no: an algorithm change in `fusion_inputs` | YES (as (e2)) |
| (e3) full-resolution bounds | bounds 0.0010-0.0016; input 2 saliency mean 0.17-1.17 | no: changes where the bounds are measured (AD-4) | YES, and the analysis needs a full-resolution decode pass per clip (the proxy is no longer the sole measurement input) |
| (b) pyramid minimum level | none (0) | not a dependency of any stage | NO |
| (c) weight delta | none (0) | not a dependency of any stage | NO |

(ii) Flicker on GX011627's last second: **UNMEASURED by V3 for every candidate** (corrected at
step 3R, Reviewer A round 4 finding 1; this paragraph first called the figures below V3's). What
the records do hold is a **whole-frame temporal diagnostic (not V3)**: per frame the record's
`whole_image.v3_measures` (the WHOLE-frame mean L*, a*, b* and the standard deviation of L* of the
render; `tools/halo_probe.py` `whole_image`) for the candidate, and `baseline_v3_measures` for the
run's own shipped-defaults render; per measure the population standard deviation of the 29
frame-to-frame differences over the 30 frames 21.7217-22.6893 s (`np.std(np.diff(m, axis=0),
axis=0)`); the figure is candidate / baseline. Baseline values (Lab units): 0.0805, 0.0119, 0.0390,
0.1192. It is NOT V3 (spec V3, D112): V3 measures a region the disturbance never touches, on a
synthetic clip, excludes whole-frame means (per-frame gray world forces them toward gray), and
compares smoothed against per-frame (unsmoothed) statistics; here the whole frame is reduced, the
fin's entry and the camera's motion enter the frame-to-frame differences, local flicker can cancel
spatially, and the comparison is candidate against shipped defaults, both smoothed. A second
diagnostic, statistics-level: the standard deviation of the frame-to-frame differences of the
smoothed N{} range (high - low) over the same frames, baseline 0.000476. AD-14's local figure
(mean absolute frame-to-frame pixel difference in a region) is not in the records.

| Candidate (setting on video) | Whole-frame temporal diagnostic (not V3) ratio: mean L* / a* / b* / std L* | Smoothed-range diagnostic ratio |
|---|---|---|
| (a) 0.5 | 1.10 / 1.12 / 1.07 / 1.10 | 1.00 |
| (a) 0.25 | 1.17 / 1.17 / 1.11 / 1.15 | 1.00 |
| (e1) 0.01/99.99 | 1.48 / 0.98 / 1.00 / 1.11 | 1.42 |
| (e1) 0/100 | 1.60 / 1.00 / 1.00 / 1.13 | 1.61 |
| (e2) 0.1 | 0.95 / 0.97 / 0.99 / 1.07 | 1.00 |
| (e2) 0.2 | 0.98 / 0.98 / 0.99 / 1.09 | 1.00 |
| (d) unsharpened 1 sigma | 1.02 / 1.00 / 1.00 / 1.11 | 1.00 |
| (d) unsharpened 3 sigma | 1.02 / 0.97 / 0.99 / 1.11 | 1.00 |
| (e3) full-res bounds | 1.03 / 1.01 / 1.00 / 1.00 | 1.14 |
| (b) 4 | 1.00 / 1.00 / 1.00 / 1.00 | 1.00 |
| (c) 1.0 | 0.98 / 0.98 / 0.95 / 0.98 | 1.00 |

The photo-only settings (a) 0.75, (e1) 0.1/99.9, (e2) 0.05, (d) `balanced` and `input1` at 1 and
3 sigma, (b) 8, (c) 0.3 were not run on video (the orchestrator's set): their statistics column
follows their family's code path (YES for (a), (e1), (e2), (d); NO for (b), (c)); they have
neither V3 nor the diagnostic (the diagnostic by `bash work/wp5.7/part2/run-videos.sh <setting>`,
about 5-7 min a setting at this batch's walls).

**The measurement that would establish V3 for a candidate** (not run; step 3R). V3 is defined on
a synthetic clip (D112): the product-method V3 of WP4.2 (`tests/test_wp42_v3_product.py`) on its
two clips, the jittering-patch clip (V3's 25 % asserted; measured region the upper half, which the
patch never touches) and `ad14-flicker` (AD-14's bound asserted, V3's four ratios recorded;
measured region `ad14-mask`): per frame the mean L*, a*, b* and the standard deviation of L* of
the output IN THAT REGION, flicker = the standard deviation of their frame-to-frame differences,
the smoothed leg (`smoothed_record`) against the per-frame leg (`provisional_record` of a second
analysis). Runs: those two clips, each leg, under each of the 11 candidate settings run on video
and at the shipped defaults (the candidate's V3 ratios and AD-14 figure set beside the defaults').
The probe (or a new instrument) NEEDS A CHANGE: WP4.2's test renders through the composition
root's export, in the spawned export worker (AD-31), at the shipped defaults
(`new_parameter_set(method_id, {})`), so neither a `--param` override nor the probe's in-process
switches reach it; a probe mode would run `AnalysisEngine` in-process as the video path already
does, render each frame from `smoothed_record` and from `provisional_record` under `applied`
and the candidate's parameters, and report V3's four ratios and AD-14's figure in the masked
region (with tests). GPU time (an estimate from the clip sizes, not a measurement): each clip is
90 frames (960 x 540 and 480 x 270 in `tests/test_analysis_v3.py`), two analyses and two 90-frame render legs, about 1 min a
clip a setting, about 25 min for the 12 settings x 2 clips, plus the build. GX011627's last second
itself cannot carry V3: V3 on real footage needs a truly static clip (spec V3, last line) and that
second has the fin entering and the camera moving; there the real-footage flicker is the owner's
V2 judgement (a look item), not a cell measurement.

#### STOP check (dispatch-5)

No STOP. Every qualifying fused band under every video setting (and every photo setting, step 2)
is attributed to input 2; no attributed stage other than input 2 occurs on any frame-line. No
divergence from spec 6.2 / 6.6 was found (nothing was built in this half), so nothing looks like
outcome B.

#### The full candidate table (photos and video)

(Rewritten at step 3R, Reviewer A round 4 finding 2: the "qualify" counts are now the THREE-WAY
split of the decided set, band / none / undecided; S3: `undecided` is not evidence either way, so
only `none` shows a band absent.) Photos: the 3 decided photo lines (IMG_6739 L3, IMG_6743 L1,
L2) and the photo mean absolute change (6739 / 6743 / 6744; step 2's table). Video: the 31
decided frame-lines (plus NEW qualifying bands on lines not decided at the shipped defaults), the
video mean absolute change (6738 / GX / comp) and the largest p99. Consequence: (i) statistics
change; (ii) V3 flicker, and beside it the whole-frame temporal diagnostic (not V3) on GX011627,
mean L* / std L*. Recomputed from the records by `work/c57-p2h2/threeway.py` (scratch, in the
worktree; output `threeway.txt`); the video splits equal half 2's per-item b / u / n column on
every row.

| Setting | Photo b / n / u (of 3) | Photo mean abs | Video b / n / u (of 31) (+ new) | Video mean abs | Video p99 | (i) | (ii) V3 | Diagnostic (not V3) |
|---|---|---|---|---|---|---|---|---|
| shipped | 3 / 0 / 0 | - | 31 / 0 / 0 | - | - | - | - | - |
| (a) 0.75 | 3 / 0 / 0 | .010/.017/.017 | not run | - | - | YES | UNMEASURED | - |
| (a) 0.5 | 1 / 0 / 2 | .020/.033/.034 | 22 / 0 / 9 (+1) | .017/.018/.023 | .086 | YES | UNMEASURED | 1.10 / 1.10 |
| (a) 0.25 | 1 / 0 / 2 | .030/.048/.049 | 10 / 1 / 20 | .025/.027/.034 | .123 | YES | UNMEASURED | 1.17 / 1.15 |
| (e1) 0.1/99.9 | 2 / 0 / 1 | .021/.031/.025 | not run | - | - | YES | UNMEASURED | - |
| (e1) 0.01/99.99 | 2 / 0 / 1 | .039/.049/.054 | 22 / 0 / 9 (+2) | .021/.018/.015 | .100 | YES | UNMEASURED | 1.48 / 1.11 |
| (e1) 0/100 | 1 / 0 / 2 | .065/.062/.071 | 13 / 3 / 15 | .026/.026/.023 | .134 | YES | UNMEASURED | 1.60 / 1.13 |
| (e2) 0.05 | 3 / 0 / 0 | .000/.037/.039 | not run | - | - | YES | UNMEASURED | - |
| (e2) 0.1 | 2 / 0 / 1 | .019/.050/.051 | 22 / 1 / 8 (+2) | .019/.012/.014 | .101 | YES | UNMEASURED | 0.95 / 1.07 |
| (e2) 0.2 | 1 / 0 / 2 | .029/.056/.057 | 12 / 3 / 16 (+1) | .022/.015/.017 | .121 | YES | UNMEASURED | 0.98 / 1.09 |
| **(d) unsharpened 1 sigma** | **0 / 2 / 1** | .034/.059/.060 | **1 / 21 / 9** | .024/.015/.019 | .140 | YES | UNMEASURED | 1.02 / 1.11 |
| **(d) unsharpened 3 sigma** | **0 / 2 / 1** | .032/.057/.058 | **1 / 17 / 13** | .023/.014/.017 | .137 | YES | UNMEASURED | 1.02 / 1.11 |
| (d) balanced 1 sigma (row) | 0 / 0 / 3 | .030/.055/.056 | not run | - | - | YES | UNMEASURED | - |
| (d) balanced 3 sigma (row) | 0 / 0 / 3 | .025/.052/.053 | not run | - | - | YES | UNMEASURED | - |
| (d) input1 1 sigma (row) | 0 / 1 / 2 | .058/.067/.069 | not run | - | - | YES | UNMEASURED | - |
| (d) input1 3 sigma (row) | 0 / 1 / 2 | .052/.063/.065 | not run | - | - | YES | UNMEASURED | - |
| (e3) full-res bounds | 2 / 0 / 1 | .013/.024/.024 | 30 / 0 / 1 (+1) | .002/.006/.003 | .011 | YES | UNMEASURED | 1.03 / 1.00 |
| (b) 8 | 3 / 0 / 0 | .001/.001/.001 | not run | - | - | NO | UNMEASURED | - |
| (b) 4 | 3 / 0 / 0 | .002/.002/.002 | 31 / 0 / 0 | .002/.001/.001 | .007 | NO | UNMEASURED | 1.00 / 1.00 |
| (c) 0.3 | 3 / 0 / 0 | .003/.005/.005 | not run | - | - | NO | UNMEASURED | - |
| (c) 1.0 | 3 / 0 / 0 | .005/.009/.009 | 25 / 0 / 6 (+1) | .004/.002/.003 | .020 | NO | UNMEASURED | 0.98 / 0.98 |

The video split per item (IMG_6738 of 17 / GX011627 of 9 / the compilation of 5, band / none /
undecided): (a) 0.5 13/0/4, 6/0/3, 3/0/2; (a) 0.25 7/1/9, 1/0/8, 2/0/3; (e1) 0.01 13/0/4, 7/0/2,
2/0/3; (e1) 0 10/1/6, 2/2/5, 1/0/4; (e2) 0.1 11/1/5, 9/0/0, 2/0/3; (e2) 0.2 4/3/10, 7/0/2, 1/0/4;
(d) 1 sigma 0/14/3, 0/4/5, 1/3/1; (d) 3 sigma 1/11/5, 0/4/5, 0/2/3; (e3) 16/0/1, 9/0/0, 5/0/0; (b)
4 17/0/0, 9/0/0, 5/0/0; (c) 1.0 14/0/3, 8/0/1, 3/0/2.

#### Readings (measurement, not a look judgement; rewritten at step 3R)

- **No candidate is proposed as a default: V3 flicker is UNMEASURED for every candidate**
  (dispatch-5's rule, applied literally: an unmeasured candidate is not proposed as a default).
  The measurement that would establish it is stated under (ii) above. (d) is an algorithm change,
  not a default; the same measurement is owed before it is ruled.
- **No setting shows the band absent on all six items.** (d) `unsharpened` 1 sigma gives the most
  demonstrated `none` lines: photos 0 band / 2 none / 1 undecided (IMG_6739 L3 0.24 x C is
  undecided); video 1 band / 21 none / 9 undecided of 31. At 3 sigma: photos 0 / 2 / 1; video 1 /
  17 / 13. The one video band left: 1 sigma, the compilation shin 27.010 s line 3 (the featured
  frame of record), 0.15 x C / 0.009 abs; 3 sigma, IMG_6738 0.700 s line 2, 0.19 / 0.014; 4.5-7.7
  % of that line's shipped absolute band. The featured frame-lines under 1 sigma: IMG_6738 0.833 s
  `none`, GX011627 22.122 s `none`, the compilation 27.010 s line 3 `band` (0.15); under 3 sigma:
  `none`, `none`, `undecided` (0.19). The next most `none` lines are (e1) 0/100 and (e2) 0.2 (3 of
  31 on video, 0 of 3 on photos). Every other candidate demonstrates at most 1 `none` on video and
  none on photos except the (d) `input1` rows (1 of 3 photo lines). The (d) `balanced` rows reach
  zero qualifying photo bands by `undecided` alone (0 / 0 / 3), which demonstrates nothing.
- (d)'s whole-image change on video is smaller than on the photos: mean absolute 0.014-0.024
  (about 3.6-6.1 / 255) against 0.032-0.060, the largest channel-mean shift 0.010, p99 0.12-0.14;
  the whole-frame temporal diagnostic (not V3) on GX011627 1.02 (mean L*) and 1.11 (std L*). The
  render cost of the clip (a windowed min / max per channel per frame, a window of 23 or 65 px at
  4K) is not timed (no exclusive run): its N6 effect is UNMEASURED.
- The parameter candidates scale the band down with their strength and none reaches the
  threshold at the settings tried; what they turn off the `band` verdict goes mostly to
  `undecided`, not `none`: at the strongest settings, photos 1 band / 0 none / 2 undecided for
  each of (a) 0.25, (e1) 0/100, (e2) 0.2, and video 10 / 1 / 20, 13 / 3 / 15 and 12 / 3 / 16, at a
  video whole-image change (mean absolute 0.015-0.034) about equal to (d)'s. The whole-frame
  diagnostic (not V3) on GX011627 rises 10-17 % under (a) and up to 60 % on mean L* under (e1) (its
  0 / 100 bounds are the high-pass extremes; its smoothed N{} range diagnostic is 1.42-1.61 x the
  shipped one); (e2) leaves it at 0.95-0.98 on mean L*.
- **(e3) does not shrink the band on video; it grows it slightly** (decided maxima 5.40 -> 5.71,
  7.42 -> 7.75, 6.77 -> 6.93; featured 1.45 -> 1.47, 1.84 -> 1.92, 3.22 -> 3.31; 30 / 0 / 1): the
  video full-resolution ranges are NARROWER than the proxy's (mean over the frames IMG_6738 0.0218
  vs 0.0236, GX011627 0.0373 vs 0.0374, the compilation 0.0276 vs 0.0289), the opposite of the
  photos (1.5-1.75 x wider), consistent with Part 1's "video bounds agree within 15 %". Its
  whole-image change is mostly a uniform offset (GX011627 mean absolute 0.0056 with p99 0.0071): an
  asymmetric bounds change moves N{0}, so input 2 shifts on flat water.
- (b) moves nothing material (31 / 0 / 0; the decided maxima and the featured lines within 0.01 x
  C; statistics identical). (c) 1.0 shrinks the decided maxima and the featured lines by 12-21 %
  and turns 6 of the 31 decided lines undecided (25 / 0 / 6), none to `none`, at a whole-image
  change of at most 0.0035 mean absolute.
- New qualifying bands are lines that were `undecided` at the shipped defaults and qualify under a
  candidate that lowers the noise level more than the band (IMG_6738 1.333 s line 2, GX011627
  22.623 / 22.689 s); each is attributed to input 2. Turning decided lines undecided is a cost, not
  a cure, as in step 2.

#### (d) as an amendment of the paper (rewritten at step 3R)

Ancuti 2018's input 2 is `S = (I + N{I - G*I}) / 2` with N{} ONE global linear stretch of the
high-pass (spec 6.2 step 3; here the 0.5 / 99.5 percentile bounds measured on the analysis proxy,
floored at 0.02 by AD-4 / DR-14, smoothed for video). (d) adds a LOCAL, nonlinear step the paper
does not have: input 2 clipped per pixel and channel to the minimum and maximum, over a window of
half side 1 or 3 sharpening sigmas, of the unsharpened form `(I + N{0}) / 2` (the clamped unsharp
mask). No 6.7 parameter reaches it; adopting it changes the definition of input 2 in spec 6.2
step 3 (a spec change, owner-reserved) and adds a code path to `fusion_inputs`; it is not a defect
fix (no divergence from 6.2 was found, so it is not outcome B as the brief defines it).

What the owner's choice trades, from the figures (demonstrated `none` counted apart from `not
qualifying`): a PARAMETER default ((a) 6.7 Basic, (e1) 6.7 Advanced; (e2) is an AD-4 constant, not
a user parameter) keeps the paper's input 2 and the spec text, and the user can reverse it per
item ((a), (e1)); but at the strongest settings tried it demonstrates the band absent on NO
decided photo line (1 band / 0 none / 2 undecided) and on 1-3 of 31 decided video frame-lines
(10-13 still qualify, 15-20 undecided), at a whole-image change of the same order as (d)'s (photo
mean absolute 0.029-0.071, video 0.015-0.034), with the whole-frame diagnostic (not V3) on
GX011627 up 10-60 % under (a) / (e1). The ALGORITHM change (d) `unsharpened` 1 sigma demonstrates
the band absent on 2 of 3 decided photo lines and 21 of 31 decided video frame-lines, leaves one
video band (0.15 x C) and 1 + 9 undecided, at a whole-image change of photo mean absolute
0.032-0.060 and video 0.014-0.024 (the diagnostic 1.02 on mean L*, 1.11 on std L*); it departs
from the paper, needs a spec 6.2 amendment, changes the cached fusion statistics (input 2's
saliency mean) without a parameter to invalidate them by, and its render cost is unmeasured. For
both, V3 flicker is UNMEASURED, so neither is proposable until it is measured. The owner's eye is
the oracle for both; the cell does not judge the look, and CHARC rules the candidate.

Featured compilation frame of record (the orchestrator's ruling on the cell's open question,
2026-11-03): 27.010 s **line 3** (the shin; Part 1's table and step 2B's featured frames, 3.22 /
0.200 shipped). Dispatches 5 and 7 named line 1 in error (the dispatcher's slip); both lines are
tabled above, so no measurement is lost.

Depth at Part 2 return: 207,413 (scripts/cell_depth.py, wp57-cell5, read twice by the orchestrator
at the return 2026-11-03; peak 207,413, 31 turns)

### Step 3R (Reviewer A round 4 remediation)

Dispatch `clearwater-review-evidence/wp5.7/cell/dispatch-8.md` (orchestrator gen 38), the same
cell (wp57-cell5) resumed on head `94416785`. Reviewer A round 4 (Codex, read-only, at the
orchestrator's seat, on `94416785`; transcript withheld): `NEW_CRITICAL_MAJOR_FOUND`. It confirmed
by recomputation the records' checks, the determinism, the baselines, the input-2 attribution of
every qualifying fused band, both (d) residuals, the GX011627 window, the switches (applied,
scoped, restored), the (d) windows and reference, (e3) frame identity, the cache column, (d) as an
amendment, and no product divergence. Dispositions are the orchestrator's (binding).

| # | Sev | Finding | Disposition / what changed | Tests |
|---|---|---|---|---|
| 1 | MAJOR | the "flicker ratios" are not V3: whole-frame Lab (`whole_image`), while V3 measures an untouched region of a synthetic clip, excludes whole-frame means and compares smoothed with unsmoothed | conclusions: the column renamed "whole-frame temporal diagnostic (not V3)" everywhere, with its definition; (ii) restated as UNMEASURED by V3 for every candidate, with the measurement that would establish it (regions, statistics, runs, the probe change, a GPU estimate); dispatch-5's rule applied: no candidate is proposed as a default | none (ledger only; no run) |
| 2 | MAJOR | "removes every qualifying photo band" counted `undecided` as removal (S3: not evidence) | conclusions: every table and reading of the candidates now gives the three-way split band / none / undecided over the decided set, photos and video, recomputed from the records (`work/c57-p2h2/threeway.py`, scratch); the "which candidate" reading and the (d) trade rewritten on demonstrated `none`; the most `none` lines: (d) `unsharpened` 1 sigma | none (ledger only) |
| 3 | MINOR | an interrupt after the final rename leaves `out` = new and `<out>.replaced-<stamp>` = old; the docstring's "publishes nothing and leaves `out` untouched" is then false | the commit boundary stated in the module docstring's publication paragraph, in `_publish`'s docstring and in the Limits below; no behaviour change | `test_main_interrupt_after_the_final_rename_keeps_both_publications[True / False]`: the interrupt injected immediately after `staging -> out` took effect: re-raised; `out` is the new publication (its record's `started` differs from the old one's); with `--replace` exactly one `out.replaced-*`, byte-identical to the old publication; no staging or failed folder |
| 4 | ADVISORY | the switch test does not show the baseline RENDER ran unswitched; nothing for the clip | test only | `test_run_video_renders_the_baseline_with_no_switch[e2 / d]` and `test_run_photo_renders_the_baseline_with_no_switch[e2 / d]`: `method.render` wrapped to record each call's switch state and output; the baseline renders (the calls given the shipped-defaults statistics object; for the photo, the one `photo_statistics` result measured with every patched object original) ran with every patched object original and equal the test's own unswitched render bit for bit; the candidate's renders ran switched; one baseline render per frame |

Edited in place (step 3R): step 1's whole-image paragraph (the flicker figure named a whole-frame
temporal diagnostic, not V3); step 2's first reading ("Only (d) `unsharpened` removes every
qualifying fused band" -> the three-way statement); half 2's (ii) paragraph and its table (V3 ->
the whole-frame temporal diagnostic (not V3), UNMEASURED by V3, the measurement that would
establish it); half 2's full candidate table (the counts -> band / none / undecided; the (ii)
column -> UNMEASURED with the diagnostic beside it), the readings and the (d)-as-amendment trade.
Half 2's video candidate table and featured-frame table are unchanged (they already split band /
undecided / none per item and per featured line). The reviewer's video band / undecided table was
not in my dispatch (the transcript is withheld); my recomputation is the one in the full table,
and it equals half 2's per-item column on every row: any difference from the reviewer's is for
the dispatcher to set against the review.

The corrected summary (band / none / undecided over the decided set; photos of 3, video of 31):

| Setting | Photos | Video |
|---|---|---|
| (a) 0.5 | 1 / 0 / 2 | 22 / 0 / 9 |
| (a) 0.25 | 1 / 0 / 2 | 10 / 1 / 20 |
| (e1) 0.01/99.99 | 2 / 0 / 1 | 22 / 0 / 9 |
| (e1) 0/100 | 1 / 0 / 2 | 13 / 3 / 15 |
| (e2) 0.1 | 2 / 0 / 1 | 22 / 1 / 8 |
| (e2) 0.2 | 1 / 0 / 2 | 12 / 3 / 16 |
| (d) unsharpened 1 sigma | 0 / 2 / 1 | 1 / 21 / 9 |
| (d) unsharpened 3 sigma | 0 / 2 / 1 | 1 / 17 / 13 |
| (e3) full-res bounds | 2 / 0 / 1 | 30 / 0 / 1 |
| (b) 4 | 3 / 0 / 0 | 31 / 0 / 0 |
| (c) 1.0 | 3 / 0 / 0 | 25 / 0 / 6 |

V3 flicker: UNMEASURED for every candidate; no candidate is proposed as a default.

Limits, added (the write path): the commit point of a publication is the final rename (the
staging folder to `out`); an interrupt delivered after it took effect, before the call returns,
leaves the new publication in `out` and (with `--replace`) the old one whole in
`<out>.replaced-<stamp>`, and is re-raised; nothing is lost and no staging or failed folder is
left, but the run is published although it ended in an interrupt.

No measurement code changed: the probe's diff is two docstring passages; no band, record, crop
or whole-image value can move (no STOP; no GPU run, no render).

RED (against `94416785`'s probe, restored into the working copy for the run, then the new probe
copied back and compared byte for byte; logs in the worktree's `work/`): the six new tests PASS
on `94416785` (`c57-p2r-red-old.log`: 6 passed), as expected (finding 3 adds no behaviour,
finding 4 is test-only). Their REDs are one-off mutation probes (`work/c57-p2h2/mutate.py`,
never committed):
- mutant A, the baseline render moved inside `applied(switches)` (video and photo paths):
  `c57-p2r-mutA.log`, 4 failed (`test_run_video_renders_the_baseline_with_no_switch[e2]`, `[d]`,
  `test_run_photo_renders_the_baseline_with_no_switch[e2]`, `[d]`), each at `assert
  call["unswitched"]` (`assert False`).
- mutant B, a blind rollback in `_publish` (puts the old publication back whenever the replaced
  folder exists): `c57-p2r-mutB.log`, `test_main_interrupt_after_the_final_rename_keeps_both_publications[True]`
  FAILED, `Failed: DID NOT RAISE <class 'KeyboardInterrupt'>` (the rollback hit the new `out`:
  `halo_probe: FAILED to publish: publishing failed (KeyboardInterrupt()) and putting the old
  publication back failed (FileExistsError(17, ...))`, exit 1); `[False]` passed.
After the probes the probe file was restored and `cmp` found it byte-identical to the edited one.

GREEN: `uv run pytest -q tests/test_tools_halo_probe.py --basetemp=.worktrees/wp5.7/work/c57-p2r-6`
94 passed (7.8 s); `uv run ruff check .` All checks passed; `uv run ruff format --check .` 313
files already formatted; `uv run mypy` Success, no issues found in 157 source files. One lint
slip before GREEN (a test line of 101 characters, E501) was fixed.

Round ledger (cumulative):

| Round | Reviewer | Critical | Major | Minor | Advisory | In-envelope / out | NEW / REOPENED | Reverts | Fixes: instrument / test-only / product |
|---|---|---|---|---|---|---|---|---|---|
| 0 | A (Codex, at the orchestrator's seat) | 0 | 4 | 4 | 1 | 9 / 0 | 9 / 0 | 0 | 9 / 0 / 0 |
| 1 | A (Codex, at the orchestrator's seat) | 0 | 1 | 3 | 0 | 4 / 0 | 4 / 0 | 0 | 3 / 1 / 0 |
| 2 | A (Codex, at the orchestrator's seat) | 0 | 1 (out of envelope by adjudication) | 3 | 1 (out of envelope) | 3 / 2 | 5 / 0 | 0 | 2 / 1 / 0 |
| 3 | A (Codex, at the orchestrator's seat) | 0 | 1 (out of envelope by adjudication) | 2 | 0 | 2 / 1 | 3 / 0 | 0 | 2 / 0 / 0 |
| 4 | A (Codex, at the orchestrator's seat) | 0 | 2 | 1 | 1 | 4 / 0 | 4 / 0 | 0 | 1 (docstring + test) / 1 / 0; plus 2 conclusions (ledger) |

Rounds 0-4 are five review rounds; the next review is round 5, the round the five-round gate
names (approval to continue, the dispatcher's).

Depth at step-3R end: 303,358 (scripts/cell_depth.py, wp57-cell5, read by the orchestrator at the yield 2026-11-03; past the re-seat line: Part 3 goes to a fresh cell from this ledger)

#### Addendum: CHARC's candidate ruling C1-C6 (dispatch-8a) -- planning for C3, C4 and Part 3

Step 3R changed NO Part 2 figure: every band, verdict, width, whole-image and diagnostic number is
the half-2 figure; 3R re-labelled the diagnostic and re-counted the same verdicts three ways (band
/ none / undecided), so C1-C6 stand on unchanged figures. C2's "nine video and one photo undecided
lines under (d) 1 sigma" are, from the records (`work/c57-p2h2/undecided.py`, scratch): IMG_6738
0.433, 0.467, 0.633 s line 2; GX011627 22.155, 22.356, 22.389, 22.422, 22.456 s; the compilation
27.027 s line 1; IMG_6739 line 3 (photo). Planning only below: nothing built, nothing run.

**C3 sizing (V3-regional flicker on GX011627's last second, (d) 1 sigma and the shipped
defaults).**
- The acceptance suite's V3 statistic: `tests/acceptance_support.py:564` maps V3 to
  `tests/test_wp42_v3_product.py`; the statistic is `_figures` (`test_wp42_v3_product.py:227`):
  per frame the measured region clipped to [0, 1], Lab (`lab`, `tests/test_analysis_v3.py:121`),
  the four measures (mean L*, a*, b*, std L*; `MEASURES`), flicker = `np.std(np.diff(...))` per
  measure, and AD-14's figure (the mean absolute frame-to-frame difference, /255); the acceptance
  rule is `_v3_holds` (`:358`, smoothed <= 0.25 x unsmoothed per measure). The legs: smoothed =
  the frames rendered from the smoothed records; unsmoothed = the same decoded frames rendered by
  the same method with `AnalysisEngine.provisional_record(pts)` (`:296-336`; engine
  `analysis/engine.py:552`, measured on the stored proxy on the caller's thread, so a module
  switch applies to it).
- Applied to GX011627: the probe's window (the 30 frames 21.7217-22.6893 s). Region (proposed;
  confirmed by eye on the three crop overviews at the run and recorded with a crop): source px
  `64,64,1024,512` (coded orientation), the upper-left open water; on the `part1s` overviews at
  21.788 and 22.589 s it holds open water and drifting particles, while the swimmer's limb enters
  only the top right (x above about 2,900 px). Four legs per frame: (d) smoothed (the run's
  `rendered`), (d) unsmoothed (`method.render` with the candidate engine's `provisional_record`,
  inside `applied`), defaults smoothed (the run's baseline render), defaults unsmoothed (the
  baseline engine's `provisional_record`, unswitched). ONE probe run under `--switch
  clip_overshoot=unsharpened:1` carries both (its baseline is the shipped defaults). Figures: per
  setting the four smoothed / unsmoothed ratios and AD-14's figures, `_v3_holds` per setting, and
  (d)'s ratios against the defaults'. Limit (stated, not removed): the camera moves (the reef and
  fish shift), so the region is not static as V3 asks of a real clip (spec V3, last line); the
  motion is common to both legs of a setting, so it pulls both ratios toward 1 and compresses the
  (d) / defaults difference; V3's 25 % is a synthetic-clip threshold, here informative unless
  CHARC rules it binding.
- Instrument change: `tools/halo_probe.py` gains `--v3-region X,Y,W,H` (video only; refused for a
  photo or a region outside the frame). Per selected frame it keeps the four legs' regions on
  the host (1024 x 512 x 3 float32 = 6.3 MB, x 30 frames x 4 legs = about 0.75 GB), then computes
  the figures with the acceptance suite's OWN `_figures` and `_v3_holds`, loaded lazily with
  `importlib` from the repository's `tests/` folder (never re-implemented), and records
  `v3_regional` (region, frames, per leg AD-14 and the four flickers, the ratios, the holds).
- Tests (parallel leg, synthetic, the fake video and engine of the existing tests): the
  record's figures equal `_figures` applied by the test to regions it renders itself; the
  unsmoothed legs use `provisional_record` (a fake engine whose provisional records vary per
  frame, smoothed constant: unsmoothed flicker > smoothed); the baseline legs run unswitched and
  the candidate legs switched (round 4's recorder); the statistic used IS the acceptance suite's
  object (identity); refusals (photo, region out of frame). Mutation probes: the whole frame for
  the region, and the smoothed record for the unsmoothed leg, must each fail a test.
- GPU time: the (d) GX011627 run took 177 s in the batch; the two extra renders per frame (30 x 2
  at 4K) and 60 provisional records add about 20-40 s: about 4 min, one run.
- Command: `uv --directory <worktree> run python tools/halo_probe.py GX011627 --line
  3300,420,3700,40 --start 21.7 --end 22.7 --crop-at 21.8 --crop-at 22.2 --crop-at 22.6 --margin
  150 --cache-dir <work>/wp5.7/scratch/cache --switch clip_overshoot=unsharpened:1 --v3-region
  64,64,1024,512 --out <work>/wp5.7/part3/v3/GX011627`.

**C4 sizing (one timed EXCLUSIVE row: GX011627 export under (d) 1 sigma against the shipped
defaults, D106 min/min).**
- Instrument of record: `tools/export_bench.py` (WP3.14; WP5.2's W52-1 row of record, report
  `docs/reports/wp5.2-performance-memory.md` section 1: GPU, device frames ON, auto -> hevc_nvenc,
  Standard, cold cache, 681 frames at 30000/1001). D106 min/min = `wall_s / frames *
  frame_rate` (seconds of processing per second of source; the record's `total.min_per_min`).
- It takes the (d) switch WITHOUT editing `src/` or `export_bench.py`: `build_engine`
  (`tools/export_bench.py:419`) builds `ExportEngine` IN-PROCESS (the GUI's spawned export
  worker, AD-31, is not on this path), and the export renders through `method.render`
  (`jobs/export.py:1102`) and analyses through `analyze`, both of which call
  `ancuti_fusion.fusion_inputs`, the attribute `halo_probe.applied` patches. A seat script (under
  `work/wp5.7/n6/`, outside the owned paths, uncommitted and quoted in the ledger; or a committed
  home if the dispatcher grants one) calls `export_bench.main(["run", "GX011627", "--runs", "1",
  "--device-frames", "--subdir", "wp5.7/n6/<tag>"])` per run, the (d) runs inside
  `applied(Switches(clip_reference="unsharpened", clip_radius_sigma=1.0))` with a call counter
  on the clipped function (asserted at least 681 calls in a (d) run and none in a shipped run;
  the original restored after each). Caveat: the timed (d) is the instrument's implementation
  (`backend.ndimage` minimum / maximum filters, a 23 x 23 window at 4K), not an optimised product
  one.
- Order and repeats: cold, alternating S1 D1 S2 D2 S3 D3 (W52-1's three cold rows; alternation
  shares drift and heat between the two). Arithmetic: N6 effect = median(D) / median(S) - 1, with
  the three pairwise ratios D_i / S_i beside; over 10 % is a STOP before the proposal (C4). Spread
  caveat: W52-1's three cold rows spanned 10.77-11.78 min/min (9.4 %), the size of the threshold;
  a result within about 5 points of 10 % is not decidable at n = 3, and then CHARC may add a
  further S / D pair or two.
- Window: W52-1's cold rows took 0.36-0.39 s/frame x 681 = 245-268 s, plus setup: about 4.5-5 min
  a run, 6 runs about 30 min. Disk: `export_bench` checks the source size plus its margin and
  deletes each run's output and cache unless `--keep`.

**Part 3 plan (the whole set under (d) 1 sigma against the shipped defaults).**
- Items: the 120 non-halo CP5 items of `work/wp5.3/review-sheet.csv` (read-only): 70 photos (P-A
  61, P-Z 9) and 50 videos (V-D 8, V-P 16, V-S 25, V-Z 1). Sources: the footage folder through
  `find_footage_file` (read-only); the items the pack excerpted (`records/V-D-excerpts.json` 6,
  `V-S-excerpts.json` 11) read in place from `work/wp5.3/excerpts/`, as the probe read the
  compilation, so the analysis input is the one the pack paired (to be confirmed against
  `tools/reviewpack` at the build).
- What is rendered: per photo the full image twice (shipped defaults, unswitched, from its proxy
  statistics; (d), switched, from its own); per video the frames at the pack's three still
  positions (10 / 50 / 90 %, the `pairs/<item>_10|50|90.jpg` stills), each from a whole-clip (or
  excerpt) analysis per setting (the probe's run_video discipline: baseline analysis unswitched,
  candidate switched, the render-equality check under the switch).
- What is recorded (one JSON per item): `whole_image` per render pair (mean absolute and p99
  difference, per-channel mean shift, clipped fraction of both, V3's four whole-frame measures);
  the EDGE-BAND SCAN of each render (new; a design for the build, Reviewer A to check): strong
  source edges = local maxima of the source luma's gradient magnitude at the sharpening sigma
  with a profile contrast |C| >= 0.05, sampled on a grid of about 2 sigma; at each a
  perpendicular profile (half width 4, +-6 sigma), the outward overshoot excess over the source
  on each side over |C| (the water metric's arithmetic, both sides); per render the count, the
  99th percentile and maximum excess and the fraction over 0.10; the per-render wall (indicative,
  C4) and the per-item analysis walls.
- Contact sheet: `work/wp5.7/part3/contact/index.html` and one side-by-side PNG per item (shipped
  | (d), the 50 % still for a video), for the 20 items with the largest whole-image mean absolute
  difference, plus ANY item whose edge-scan maximum or p99 rises under (d) (a regression), each
  with its figures; no preference judgement.
- The ten undecided lines' crops (C2): the photo (IMG_6739 line 3) from Part 2's own crops
  (`part2/defaults/IMG_6739/photo-*.png` and `part2/d-unsharpened-1/IMG_6739/photo-*.png`, no
  run); the nine video lines by six probe runs (defaults and `--switch
  clip_overshoot=unsharpened:1` for IMG_6738, GX011627 and the compilation, Part 1's lines,
  `--crop-at` at the nine times) into `work/wp5.7/part3/undecided/<setting>/<item>`; the report
  shows shipped vs (d) at each and says in words that undecided is not removal.
- Builds before the window (each RED / GREEN, Reviewer A): `--v3-region` (C3); the whole-set
  scan mode with the edge-band scan, the walls and the 8-bit views, and the contact-sheet builder
  (Part 3), all in `tools/halo_probe.py` with tests in `tests/test_tools_halo_probe.py`; the C4
  seat script.
- Batch estimate: photos about 10 s an item (two proxy analyses, two full-resolution renders, two
  scans; CP5 took 4.7 s an item for one render) = about 12 min; videos dominated by the two
  analyses per clip: from the batch, a first 4K analysis about 2.6 s and a second (proxies
  cached) about 1 s per source second; the 50 videos are about 900-1,065 s of source (CP5's
  11,600 s of export at about 11 min/min, fewer where the excerpt is used) = about 55-65 min; six
  renders and scans per video about 3 min. Part 3 batch about 70-80 min (range 1-1.5 h); the
  first items' walls refine it.
- Free disk: the proxy cache for about 30,000-40,000 frames at about 56 KB a frame (the scratch
  cache: 145 MB for 2,600 frames) = about 2 GB; item records and 8-bit views about 0.5 GB; the
  undecided-crop runs about 0.3 GB; C3 about 0.1 GB; C4's outputs are transient. About 4-5 GB in
  all: start the window at 30 GB free or more (the 25 GB STOP); 57 GB free at this step.

**The single exclusive window, in order (the orchestrator's seat, nothing else heavy):**
1. `df -h /c` (30 GB or more), the host idle.
2. C4: the six alternating cold exports, about 30 min (first, on a cool idle host).
3. C3: the V3-regional probe run, about 4 min.
4. The undecided-line crops: six probe runs, about 13 min (the batch's walls: defaults 57 + 140 +
   114 s, (d) 73 + 177 + 173 s).
5. Part 3: the whole-set batch, about 70-80 min, per-item walls recorded.
6. The contact sheet (CPU), a few minutes.
Total about 2-2.2 h; plan for 2.5 h.

Depth at the step-3R addendum: 379,559 (scripts/cell_depth.py, wp57-cell5, read by the orchestrator 2026-11-03; the cell is stood down)

## Part 3 (build to the window)

Dispatch `clearwater-review-evidence/wp5.7/cell/dispatch-9.md` (orchestrator gen 38). Fresh cell
`wp57-cell6` (implementer-opus-high) on head `4afa2af0`; the branch also carries `368b02d2` (the
previous cell's step-3R addendum: planning written before Q2). This build follows dispatch-9 and
CHARC's C1-C6 / Q1-Q2 where the addendum differs: C3 is measured on WP4.2's two synthetic clips
(Q2), not on GX011627's last second; the instruments live in a NEW module beside the probe. No GPU
run, no render, no footage write: build, synthetic tests, and read-only pre-checks only.

### Built

Owned paths: NEW `tools/halo_part3.py`, NEW `tests/test_tools_halo_part3.py` (parallel leg except
one `slow` test), this ledger. `tools/halo_probe.py` is unchanged; Part 3 reuses its `applied`,
`parse_switches`, `Switches`, `whole_image`, `photo_statistics`, `resolve_parameters`,
`find_footage_photo`, `water_band`, `line_profile`, `profile_fits`, `sample_spacing`, `luma` by
import. No `src/` edit, no default changed, no dependency.

- **`v3` (C3 as amended, Q2).** WP4.2's OWN code does the measuring: `suite()` appends the
  repository's `tests/` folder to `sys.path` and imports `test_wp42_v3_product` (and the suite's
  `fixture_plugin`) by name; `measure_v3` calls its `_v3(clip, method, mask, folder)` inside
  `halo_probe.applied(switches)`. Both legs are WP4.2's: the smoothed leg is an export through the
  composition root's engine IN THIS PROCESS (its recording sink keeps each frame's region
  pre-encode), the per-frame leg renders each decoded frame from `provisional_record` of a second
  in-process `AnalysisEngine`; so the switch reaches both legs' analyses and renders. The
  statistic (`_figures`), the planted controls and the encoded characterisation are WP4.2's.
  PASS / FAIL (`v3_verdict`) repeats the two acceptance tests' assertions with the suite's
  predicates `_v3_holds` (V3 25 %) and `_ad14_holds` (AD-14 0.5/255), imported, not retyped (the
  suite has no named bound constants: the bounds live inside those two functions): the jittering
  clip asserts V3, `ad14-flicker` asserts AD-14 and records V3's ratios (CHARC V3-1). The clips:
  `build_clips` is the body of WP4.2's `clips` fixture (pytest refuses a direct fixture call), on
  the shared samples through the suite's `SampleProvider` (generated samples cached under the
  run's folder); `v3_masks` is the `ad14_mask` fixture body plus `_jitter_mask()`; a `slow` test
  checks both equal the fixtures frame for frame. Methods: WP4.2's `METHODS` (c3, the shipped
  default, and ancuti2018; (d) patches the shared `fusion_inputs`), so the reproduction check
  covers all four rows of record. Order: the shipped leg on both clips and methods first; it must
  REPRODUCE WP4.2's figures of record (`V3_RECORD`, the report's "V3 ratios" table) within ONE
  UNIT in the record's last printed place (AD-14 figures 1e-4 /255, ratios 1e-3); otherwise exit
  4 (an instrument STOP) and the (d) leg is not run. Output `v3.json` and the side-by-side
  `v3-table.md` (each clip and method: shipped beside (d), AD-14 per-frame -> smoothed, the four
  ratios, the asserted bound's verdict, V3 at 25 %).
- **`n6` / `n6-summary` (C4): the path of the instrument of record, not a substitute harness.**
  `tools/export_bench.py` (V16 / N6 of record, WP5.2 W52-1) builds `ExportEngine` in its own
  process (`build_engine`; the GUI's spawned worker, AD-31, is not on this path, nor was it on
  N6's figures of record), and the engine's analysis thread and renders call
  `ancuti_fusion.fusion_inputs`, the attribute `applied` patches. `run_n6` calls
  `export_bench.main(["run", "GX011627", "--runs", "1", "--device-frames", "--subdir",
  "wp5.7/part3/n6"])` (W52-1's form, one run) inside `applied` for (d), outside for the shipped
  defaults, with `counted_inputs()` around the method's `fusion_inputs` in both settings (the
  per-call overhead is common): the sidecar `n6-<setting>-<stamp>.json` records the bench's exit,
  its new record, the call count and whether the clip was in effect. `n6-summary`: per run D106
  min/min (the bench's `total.min_per_min` = `wall_s / frames * frame_rate`), the median per
  setting, effect = median(d) / median(shipped) - 1, the three adjacent-pair ratios, validity
  (every run ok, all frames, calls > 0, the clip in effect exactly on the (d) runs) and the STOP
  (effect over 10 %, exit 4). A failed bench memory check (exit 3; (d) adds about three
  full-resolution arrays per render) still leaves the run timed and recorded; it is reported per
  run, not hidden. Caveat: the timed (d) is the instrument's clip (`backend.ndimage` minimum /
  maximum filters, a 23 x 23 window at 4K), not an optimised product implementation.
- **Whole set (Part 3; C1, C2, C3 (3)).** `wholeset_items`: the pack manifest
  `work/wp5.3/records/pack.json`, the items whose status is `done` (126; the two `V-R` HLG items
  are `refused`), which must equal the review sheet's 126 judged items, minus the six halo items:
  120 (checked; 70 photos, 50 videos). Sources: photos through `find_footage_photo`; a video the
  pack excerpted from `work/wp5.3/excerpts/<name>` (read in place, as the owner saw it), else
  through `find_footage_file`. Per photo: the shipped-defaults proxy statistics and render
  (unswitched), then (d)'s statistics and render (switched). Per video: two whole-clip analyses
  (shipped unswitched, (d) switched; the analysis cache `part3/cache`), then the frames at the
  pack's three still times (10 / 50 / 90 %, `stills[].source_pts_s`) rendered from each
  analysis's smoothed records. Recorded per image: `whole_image` ((d) against shipped: mean
  absolute and p99 difference, per-channel mean shift, both clipped fractions, the whole-frame
  measures), the edge-band scan of both renders, the render walls (the download included, so the
  device is synchronised; indicative only) and, for videos, both analysis walls; saved: both
  renders as full-resolution 8-bit PNGs (`<tag>-shipped.png`, `<tag>-candidate.png`). Per video:
  `statistics_movement`, per smoothed statistic the largest change over every frame and both
  settings' temporal spread (the standard deviation of the frame-to-frame differences); its
  headline is input 2's row of the fusion saliency means. Items publish by a staged rename; a
  failed item is kept as `.<item>.failed-<stamp>` and the batch goes on; an existing item is
  skipped (resumable).
- **The edge-band scan (the brief's Part 3 statistic; the cell's design, for Reviewer A).** On
  the source's BT.709 luma (Gaussian 1 px), the Sobel gradient; candidates at or above its 99.5th
  percentile inside a margin that keeps every profile in the image; strongest first, at most one
  per square cell of the line half-length, at most 48. Through each point a line along the
  gradient, half-length 8 sharpening sigmas, measured from BOTH ends (each end once the start,
  i.e. the side measured) with the probe's own `water_band` of the render's luma against the
  source's (half width 4, threshold 0.10): the same sides for both renders. Per render: the sides
  by verdict (band / none / undecided; undecided never counts as removal), the largest
  qualifying band and the largest band.
- **Sheet (`wholeset-sheet`).** `summary.tsv` (one row per item), `sheet.json`, and
  `contact-sheet.html` with side-by-side previews (shipped | (d), 1200 px a half; links to the
  full-resolution PNGs). The 20: first the 5 video items whose input-2 saliency mean moves most
  (C3 (3)), then the largest whole-image mean absolute change; each item's frame is its largest
  change. After the 20, every other item whose edge scan RISES under (d) (more qualifying sides or
  a larger qualifying band), with its figures (the addendum's regression rule, kept). C2's crops:
  the 11 lines that are not `none` under (d) 1 sigma in Part 2's records (`UNDECIDED_LINES`:
  IMG_6739 line 3 (photo; Part 2's own crops, read only); IMG_6738 0.433 / 0.467 / 0.633 s line 2;
  GX011627 22.155 / 22.356 / 22.389 / 22.422 / 22.456 s; the compilation 27.027 s line 1; plus the
  one remaining BAND, the compilation 27.010 s line 3), shipped beside (d), from the window's probe
  runs. The previews show 8-bit values, NOT display-converted (the CP5 pack converts video stills
  BT.1886 -> sRGB); both halves alike.

### RED / GREEN

RED (the new module absent, as at `4afa2af0`; the module moved aside for the run, restored and
compared byte for byte; log `work/c57-p3/red.log` in the worktree): `ModuleNotFoundError: No
module named 'halo_part3'`, 1 collection error. Mutation probes (scratch, restored, `cmp`
identical): (A) `measure_v3`, `run_n6` and the video candidate render each taken out of `applied`:
3 failed (`test_the_switch_reaches_both_v3_legs_and_is_restored`,
`test_the_switch_changes_a_render_made_inside_a_v3_leg`,
`test_run_n6_runs_the_bench_of_record_inside_the_switch[candidate]`); the video-render mutant was
NOT caught, so the video test gained a per-render switch recorder; (B) the video render alone out
of `applied`: 1 failed (`test_process_video_analyses_twice_and_renders_the_still_frames`). One
defect found by the tests and fixed before GREEN: the statistics-movement headline read column 1
of the flattened (2 x 3) saliency record (input 1's a*), not input 2's row.

GREEN: `uv run pytest -q tests/test_tools_halo_part3.py tests/test_tools_halo_probe.py` 121 passed
(27 new, the `slow` clip-equality test included, 4.7 s); `uv run ruff check .` All checks passed;
`uv run ruff format --check .` 315 files already formatted; `uv run mypy` Success, no issues found
in 158 source files. Both new files ASCII, 0 CR.

### Read-only pre-checks (no render)

`wholeset-list` on the real pack: 120 items (exit 0); every source resolves to an existing file
(70 photos 0.12 GB, 50 videos 5.4 GB of source); IMG_6762 is 1920 x 1080, 22,471 frames (the
longest item, run last). Free C: 56 GB.

### The window (the orchestrator's seat; one piece per call; check each before the next)

`bash C:/Users/rwsmy/clearwater/work/wp5.7/part3/run-part3.sh <piece>` (not committed; `bash -n`
clean, LF; each piece checks `df` first and exits 3 under 25 GB; logs `part3/logs/`, walls
`part3/logs/runs.txt`):
1. `v3`: about 4 min (sample generation and two lossless encodes, then 8 `_v3` legs; WP4.2's GPU
   file took 91 s for 6 tests). Check: exit 0; the four `shipped` lines say "reproduces record:
   yes" (else exit 4 = STOP, instrument; (d) not run); `part3/v3/v3-table.md`.
2. `n6` (EXCLUSIVE, nothing else on the host): S D S D S D, one process each, about 4.5-5 min a
   run, about 30 min; the last pair kept (`--keep`: the GX011627 export under each setting, for
   viewing), then `n6-summary`. Check: six `ROW` lines with `tied True`; the summary `VALID True`;
   the effect; a `STOP` line (exit 4) when over 10 %; any `memory_check False` reported.
3. `crops`: six probe runs, about 13-15 min (Part 2's walls for these items 57-177 s a run).
   Check: six `exit=0` in `runs.txt`; `part3/crops/<setting>/<item>/t*-output.png`.
4. `photos`: 70 items in one process, about 15-25 min. Check: 70 `done`, no `FAILED`.
5. `videos`: 50 items, one process each, IMG_6762 last; two analyses plus three stills per item:
   about 1.5-3 min a 4K excerpt, under 1 min a phone clip, IMG_6762 about 10-15 min: about
   90-120 min. Check: 50 `done` lines; `df` before each item.
6. `sheet`: a few minutes. Check: `SHEET 120 items`; `part3/wholeset/sheet-<stamp>/`.
Total about 2.5-3 h (the brief's "about 1 h" was CP5's pace for one render; here two analyses and
two renders per item, plus the scan).

Disk (estimates): the analysis cache about 2-3 GB (CP5's pack cache was 2.5 GB); the 8-bit renders
about 6 GB (140 photo renders about 13 MB each; about 200 4K stills about 15 MB; phone stills about
3 MB); N6 transient per run plus the kept pair about 1 GB; crops about 0.6 GB; V3 about 0.1 GB:
about 10 GB in all; 56 GB free now, so about 46 GB at the end against the 25 GB STOP.

### The step-3R addendum: what this build adopted (orchestrator's correction to dispatch-9)

- C3 (`--v3-region` on GX011627's last second): NOT built, superseded by CHARC's Q2 (V3 on
  WP4.2's two synthetic clips); GX011627's last second stays a Limits note. Its pointers to the
  acceptance statistic (`_figures`, `_v3_holds`, `provisional_record`) are what `v3` reuses, by
  calling WP4.2's own `_v3`.
- C4: ADOPTED (export_bench in-process, the switch reaching `fusion_inputs` with no `src/` edit,
  six alternating cold runs, the median ratio with the pair ratios beside, the decidability
  caveat). Amended: the runner is a committed `n6` subcommand, not an uncommitted seat script, so it
  carries tests; the call counter runs in BOTH settings (equal overhead) and records whether the
  clip was in effect instead of asserting a count.
- Part 3: ADOPTED (the 120 items, the excerpts read in place, the three stills, the edge-band scan,
  the contact sheet with the regression rule, the six crop runs). Amended: the scan's points are the
  top 0.5 % gradient pixels one per cell (not grid local maxima with |C| >= 0.05), measured with the
  probe's own `water_band` (its weak-edge, noise and support rules) so a side is band / none /
  undecided as Part 1's lines are; the 20 reserve 5 places for the videos whose statistics move
  most (C3 (3), dispatch-9), then the largest change; a video's sheet frame is its largest change,
  not always the 50 % still; crops go to `part3/crops/`.

### Open questions for the dispatcher (the cell's recommended answer first)

1. The edge-band scan is built because the brief's Part 3 names it ("the maximum edge-band
   overshoot found by scanning strong edges"); dispatch-9 step 3 does not list it. Recommended:
   keep it (the brief's statistic; its design above, for Reviewer A).
2. V3 runs both of WP4.2's methods (c3 and ancuti2018) so all four rows of record are reproduced.
   Recommended: keep (about 2 min); c3 is the shipped default of record.
3. N6: each run its own process (every run starts cold in its process, as W52-1's first row did),
   alternating S / D. Recommended: as built; CHARC may add a pair if the effect lands within a few
   points of 10 % (W52-1's three cold rows spanned 9.4 %).

Depth at mid-build yield: 364,008 (scripts/cell_depth.py, wp57-cell6, read by the orchestrator at the yield 2026-11-03; near the 400K stop: the report goes to a fresh cell)

### Part 3 results

Dispatch `clearwater-review-evidence/wp5.7/cell/dispatch-10.md` (orchestrator gen 38, binding;
started by gen 39). Fresh cell `wp57-cell7` (implementer-opus-high) on head `60357596`. No GPU
run, no render, no pytest, no instrument change: every figure below is read from the window's
records (READ-ONLY, `work/wp5.7/part3/`) by scratch tabulators in the worktree
(`work/c57-p3r/tabulate.py`, `crops.py`, `newband.py`, `siderise.py`, not committed; outputs
`table.txt`, `crops.txt`, `siderise.txt` beside them). CHARC's rulings C1-C6, Q1 / Q2 and the C4
STOP ruling are quoted in the dispatch and applied as written.

#### The window as run (the orchestrator's seat; `part3/logs/runs.txt`)

| Piece | Window (Z, 2026-11-03) | Outcome |
|---|---|---|
| `v3` | 15:08-15:11 (190 s) | exit 0; the four shipped rows "reproduces record: yes" (condition 2 met); table `part3/v3/v3-table.md` |
| `n6` | 15:11-15:40 | six runs S D S D S D, all exit 0 (walls 263-305 s), memory_check True, tied True, 1,362 `fusion_inputs` calls per run, the clip in effect on the (d) runs only; `n6-summary` exit 4 = the C4 STOP (effect over 10 %; routed, ruled by CHARC 4c60bacc3de85d88) |
| `crops` | 15:40-15:49 | six probe runs exit 0 (20-147 s) |
| `photos` | first attempt 15:49, exit 2 in 1 s; re-run 15:50-15:58 (512 s) | first attempt: a SEAT FIX (below); re-run exit 0, 70 `done`, no `FAILED` or `Traceback` in the log |
| `videos` | 15:59-20:27 | 50 / 50 exit 0, one process each, IMG_6762 last (4,441 s); 50 `done` lines, no `FAILED` or `Traceback` in any log; no staging or failed item folder left |
| `sheet` | 20:28 (24 s) | exit 0, "SHEET 120 items; contact: IMG_6762, GX011601, GX011600, GX011590, GX011625, IMG_6751, IMG_6758, IMG_6753, IMG_6755, IMG_6754, IMG_6757, IMG_6746, IMG_6759, IMG_6756, IMG_6752, IMG_6768, IMG_6770, IMG_6767, IMG_6769, IMG_6761" |

Free C: 56 GB at 15:08Z, 55 GB at the crops and photos, 52 GB at the first video, 47 GB from
GX011601 on, 46 GB at 20:28Z (the 25 GB STOP never near).

**The seat fix (a limit of `wholeset-list`).** `wholeset-list` prints its ids with `print`, which
on Windows writes CRLF; `mapfile -t` in `run-part3.sh` kept the CR, so every id was refused
before any write (exit 2 in 1 s, nothing published). The orchestrator added `| tr -d '\r'` to the
photo and video list lines of `work/wp5.7/part3/run-part3.sh` (the original kept as
`run-part3.sh.orig`; `diff`: lines 90 and 99 only; both copies durable in
`clearwater-review-evidence/wp5.7/part3/`). Follow-up note only (no committed fix in this
package): `wholeset-list` should write LF (a list meant for a shell pipe), or its consumers strip
CR; recommended the former.

#### V3 (C3 / Q2; WP4.2's two synthetic clips; `part3/v3/v3-table.md`, durable `clearwater-review-evidence/wp5.7/v3/`)

| Clip | Method | Setting | AD-14 /255 per-frame -> smoothed | V3 ratio L* / a* / b* / contrast | Asserted bound | V3 <= 25 % |
|---|---|---|---|---|---|---|
| jitter | c3 | shipped | 0.1006 -> 0.0017 | 0.018 / 0.014 / 0.026 / 0.016 | V3: PASS | yes |
| jitter | c3 | (d) | 0.0569 -> 0.0009 | 0.016 / 0.014 / 0.026 / 0.020 | V3: PASS | yes |
| jitter | ancuti2018 | shipped | 0.1055 -> 0.0017 | 0.012 / 0.016 / 0.024 / 0.012 | V3: PASS | yes |
| jitter | ancuti2018 | (d) | 0.0660 -> 0.0010 | 0.011 / 0.016 / 0.024 / 0.022 | V3: PASS | yes |
| ad14 | c3 | shipped | 0.0416 -> 0.0102 | 0.053 / 0.200 / 0.401 / 0.072 | AD-14: PASS | no |
| ad14 | c3 | (d) | 0.0331 -> 0.0087 | 0.037 / 0.198 / 0.408 / 0.316 | AD-14: PASS | no |
| ad14 | ancuti2018 | shipped | 0.0388 -> 0.0067 | 0.061 / 0.257 / 0.497 / 0.071 | AD-14: PASS | no |
| ad14 | ancuti2018 | (d) | 0.0298 -> 0.0057 | 0.080 / 0.257 / 0.502 / 0.387 | AD-14: PASS | no |

(d) passes every clip's asserted bound; the shipped leg reproduced WP4.2's four rows of record
(`v3.log`: "reproduces record: yes" x 4), so condition 2 is met. Not buried: on `ad14-flicker` the
CONTRAST ratio rises under (d) (c3 0.072 -> 0.316; ancuti2018 0.071 -> 0.387); that clip's
asserted bound is AD-14 (passes: c3 0.0331 -> 0.0087 /255 against shipped 0.0416 -> 0.0102), and
its a* / b* ratios are already over 25 % at the shipped defaults (c3 0.200 / 0.401), as AD-14's
2026-10-21 extension records. On the jittering clip the contrast ratio also rises (c3 0.016 ->
0.020; ancuti2018 0.012 -> 0.022), within 25 %.

#### N6 (C4; `tools/export_bench.py` in-process, GX011627, W52-1's form; `part3/logs/n6-*.log`, durable `clearwater-review-evidence/wp5.7/part3/`)

| Run | Setting | min/min | wall s (bench) | s/frame | memory_check | tied | calls | clip |
|---|---|---|---|---|---|---|---|---|
| 1 | shipped | 10.9467 | 248.7 | 0.3653 | True | True | 1,362 | False |
| 2 | (d) | 12.4234 | 282.3 | 0.4145 | True | True | 1,362 | True |
| 3 | shipped | 10.8630 | 246.8 | 0.3625 | True | True | 1,362 | False |
| 4 | (d) | 12.4346 | 282.5 | 0.4149 | True | True | 1,362 | True |
| 5 | shipped | 11.0729 | 251.6 | 0.3695 | True | True | 1,362 | False |
| 6 | (d) | 12.6115 | 286.6 | 0.4208 | True | True | 1,362 | True |

681 frames each. Medians: shipped 10.9467, (d) 12.4346 min/min; effect = 12.4346 / 10.9467 - 1 =
+13.59 %; pair ratios 1.1349, 1.1447, 1.1389; `VALID True`; `STOP: the N6 effect is over 10 %`
(exit 4). The shipped median reproduces W52-1's cold median of record (10.89) within 0.5 %. Peak
GPU memory shipped 3,692-3,756 MiB, (d) 3,760-3,840 MiB of 4,065.4 (all `ok`). CHARC's STOP ruling:
the binding figure is N6 itself (about 12 min/min, D106, spec v0.5.8): (d) as measured (12.43) is
OVER N6 on the clip of record and NOT adoptable in v1.0.x on cost alone; the headroom for any
implementation of the clip is about 1.0 min/min = about +9.6 % on GX011627 (12 / 10.95 = 1.096).
The cost is the instrument's clip (per-channel 23 x 23 `ndimage` minimum / maximum at 4K,
unoptimised); a separable or fused min / max is a candidate at an UNMEASURED cost. Observation (not
owned, a follow-up): `tools/export_bench.py:99` still holds `D106_MIN_PER_MIN = 25.0` (the interim
figure of 0.5.4), so every ROW line prints "meets D106 25", (d)'s 12.43 included; the min/min
figures are unaffected (`total.min_per_min`), only the verdict label is stale against spec v0.5.8.

#### The C2 crops (the ten undecided lines and the one remaining band; shipped vs (d) 1 sigma)

From the six crop runs (`part3/crops/<setting>/<item>/`, every frame's render and prefused check
equal) and, for the photo, Part 2's records. Every video crop-run band equals Part 2's record for
the same pts exactly (both settings), so the crops show the frames Part 2 measured. Fused luma band
x C, verdict, attributed stage; "undecided" is NOT removal (S3: not evidence either way).

| Item, time, line | Shipped | (d) 1 sigma | Shipped crop | (d) crop |
|---|---|---|---|---|
| IMG_6739 photo, line 3 (right flank) | 3.07 band, input2 | 0.24 undecided | `part2/defaults/IMG_6739/photo-output.png` | `part2/d-unsharpened-1/IMG_6739/photo-output.png` |
| IMG_6738 0.433 s, line 2 | 3.26 band, input2 | 0.17 undecided | `part3/crops/shipped/IMG_6738/t0000.433-output.png` | `part3/crops/candidate/IMG_6738/t0000.433-output.png` |
| IMG_6738 0.467 s, line 2 | 5.40 band, input2 | 0.20 undecided | `.../shipped/IMG_6738/t0000.467-output.png` | `.../candidate/IMG_6738/t0000.467-output.png` |
| IMG_6738 0.633 s, line 2 | 1.97 band, input2 | 0.11 undecided | `.../shipped/IMG_6738/t0000.633-output.png` | `.../candidate/IMG_6738/t0000.633-output.png` |
| GX011627 22.155 s | 3.85 band, input2 | 0.10 undecided | `.../shipped/GX011627/t0022.155-output.png` | `.../candidate/GX011627/t0022.155-output.png` |
| GX011627 22.356 s | 7.42 band, input2 | 0.18 undecided | `.../shipped/GX011627/t0022.356-output.png` | `.../candidate/GX011627/t0022.356-output.png` |
| GX011627 22.389 s | 4.41 band, input2 | 0.14 undecided | `.../shipped/GX011627/t0022.389-output.png` | `.../candidate/GX011627/t0022.389-output.png` |
| GX011627 22.422 s | 4.01 band, input2 | 0.15 undecided | `.../shipped/GX011627/t0022.422-output.png` | `.../candidate/GX011627/t0022.422-output.png` |
| GX011627 22.456 s | 6.76 band, input2 | 0.29 undecided | `.../shipped/GX011627/t0022.456-output.png` | `.../candidate/GX011627/t0022.456-output.png` |
| compilation 27.027 s, line 1 | 6.77 band, input2 | 0.21 undecided | `.../shipped/compilation-20261010-1080p60/t0027.027-output.png` | `.../candidate/compilation-20261010-1080p60/t0027.027-output.png` |
| compilation 27.010 s, line 3 (the shin; the remaining BAND) | 3.22 band, input2 | 0.15 band, input2 | `.../shipped/compilation-20261010-1080p60/t0027.010-output.png` | `.../candidate/compilation-20261010-1080p60/t0027.010-output.png` |

Reading (measurement): under (d) every one of the eleven falls to 0.10-0.29 x C from 1.97-7.42
(2.5-5.6 % of the shipped band on the ten video lines, 7.7 % on IMG_6739); ten are undecided, which shows neither a band
nor its absence; the shin keeps a qualifying band of 0.15 x C, attributed to input 2. Each run
folder also holds the stage crops, `*-output-marked.png` and the overviews.

#### The whole set (120 items; `part3/wholeset/items/<item>/<item>.json`; sheet `part3/wholeset/sheet-20261103T202754214375Z/`)

Per item (the full 120-row table is `summary.tsv` in the sheet folder and `work/c57-p3r/table.txt`
in the worktree): whole-image change ((d) against shipped, the largest over the item's frames: the
mean absolute and 99th-percentile per-value difference, the largest per-channel mean shift, the
clipped fractions of both); the edge-band scan of both renders (48 strongest-edge points per image,
two sides each, band / none / undecided summed over the item's frames, the largest qualifying band
x C); the input-2 saliency movement (videos); the walls. Photos: 1 image each (70). Videos: the
pack's three still positions, 10 / 50 / 90 % (150 frames from 51,445 analysed).

| | Photos (70) | Videos (50; 150 frames) |
|---|---|---|
| Mean abs change: min / median / max | 0.0082 / 0.0215 / 0.0856 | 0.0086 / 0.0172 / 0.0293 |
| p99 abs change: min / median / max | 0.0869 / 0.1249 / 0.1847 | 0.0910 / 0.1201 / 0.1413 |
| Largest channel-mean shift: median / max | 0.0037 / 0.0189 | 0.0028 / 0.0109 |
| Clipped fraction, shipped -> (d): max | 0.0041 -> 0.0000 | 0.0047 -> 0.0000 |
| Scan sides b / n / u, shipped | 248 / 1,709 / 4,763 (of 6,720) | 963 / 3,894 / 9,543 (of 14,400) |
| Scan sides b / n / u, (d) | 13 / 3,403 / 3,304 | 39 / 8,196 / 6,165 |
| Items with a qualifying side, shipped -> (d) | 50 -> 11 | 49 -> 18 |
| Largest qualifying band x C, shipped -> (d) | 13.79 -> 2.57 | 15.20 -> 2.05 |
| Side transitions band -> band / none / undecided | 12 / 105 / 131 | 37 / 567 / 359 |
| Side transitions undecided -> band / none / undecided | 1 / 1,626 / 3,136 | 2 / 3,813 / 5,728 |
| Side transitions none -> none / undecided | 1,672 / 37 | 3,816 / 78 |
| Whole-frame std L*, (d) / shipped per frame: min / median / max | 0.189 / 0.895 / 0.980 | 0.522 / 0.895 / 1.006 |
| Whole-frame mean L* shift (d) - shipped: min / median / max | -2.09 / -0.34 / +0.06 | -1.12 / -0.17 / +0.08 |
| Input-2 saliency mean moved (smoothed, Lab): min / median / max | - | 0.070 / 0.167 / 0.684 |

Group medians of the mean absolute change: P-A 0.0224 (61), P-Z 0.0091 (9); V-D 0.0131 (8), V-P
0.0158 (16), V-S 0.0186 (25), V-Z 0.0145 (1). Per video, the smoothed statistics other than input
2's saliency means are unchanged by (d) (white-balance means and gains, fusion bounds: largest
change 0.0 over all 50), as Part 2's cache column states.

**Which items' scans RISE under (d).** By the sheet's rule (more qualifying sides, or a larger
largest qualifying band, than at the shipped defaults): NONE of the 120 (`scan_regressions: []`;
no item and no frame rises by either test). Below the item rule, at the side level (every one
disclosed): 3 sides qualify only under (d) (undecided at the shipped defaults): GX011610 f90 side
83 (1.68 -> 0.21 x C) and IMG_6716 f50 side 24 (3.56 -> 1.26), each a SMALLER band that now
clears its noise level, and IMG_6800 (photo) side 5 at (5343, 4032), 0.11 -> 0.56 x C, a band that
RISES. Over all sides, the band is larger under (d) on 154 of 6,720 photo and 380 of 14,400 video
sides; on 180 of them (57 photo, 123 video) the (d) band is 0.10 x C or more on a non-weak edge:
115 of those go none -> undecided, 64 stay undecided, 1 goes undecided -> band (IMG_6800 above).

**Walls (indicative only; not N6 figures).** Photos: 510 s for 70 items (4.2-15.9 s an item);
render walls shipped 0.58-7.43 s, (d) 0.53-4.11 s (the download included). Videos: shipped analyses
12,146 s in all, (d) analyses 1,543 s; the (d) analysis runs second and reads the proxies the
shipped analysis cached, so the two analysis walls are not comparable. IMG_6762 (1920 x 1080,
22,471 frames): 4,439 s (shipped analysis 3,382 s, (d) 695 s).

#### The contact sheet's 20, and how chosen

`part3/wholeset/sheet-20261103T202754214375Z/contact-sheet.html` (side-by-side previews shipped |
(d), 1200 px a half, links to the full-resolution 8-bit PNGs in the item folders; 8-bit values,
NOT display-converted, both halves alike). Rule (`select_contact`): first the 5 videos whose
smoothed input-2 saliency mean moves most (C3 (3)), then the 15 largest whole-image mean absolute
changes among the rest; each item shown at its frame of largest change. No scan regression to add.

| # | Item | Group | Frame | Mean abs | p99 | Max shift | Input-2 saliency moved | Scan b / n / u shipped -> (d) |
|---|---|---|---|---|---|---|---|---|
| 1 | IMG_6762 | V-P | f90 | 0.0191 | 0.1254 | 0.0086 | 0.684 | 60/82/146 -> 1/204/83 |
| 2 | GX011601 | V-D | f10 | 0.0135 | 0.0956 | 0.0024 | 0.409 | 3/163/122 -> 0/225/63 |
| 3 | GX011600 | V-D | f10 | 0.0127 | 0.1016 | 0.0025 | 0.329 | 2/109/177 -> 0/173/115 |
| 4 | GX011590 | V-D | f90 | 0.0187 | 0.1110 | 0.0028 | 0.302 | 3/114/171 -> 0/177/111 |
| 5 | GX011625 | V-S | f10 | 0.0172 | 0.1268 | 0.0045 | 0.267 | 15/55/218 -> 0/128/160 |
| 6 | IMG_6751 | P-A | photo | 0.0856 | 0.1526 | 0.0092 | - | 0/0/96 -> 0/0/96 |
| 7 | IMG_6758 | P-A | photo | 0.0700 | 0.1842 | 0.0166 | - | 0/0/96 -> 0/1/95 |
| 8 | IMG_6753 | P-A | photo | 0.0687 | 0.1800 | 0.0179 | - | 0/0/96 -> 0/1/95 |
| 9 | IMG_6755 | P-A | photo | 0.0679 | 0.1834 | 0.0189 | - | 0/0/96 -> 0/3/93 |
| 10 | IMG_6754 | P-A | photo | 0.0674 | 0.1847 | 0.0189 | - | 0/0/96 -> 0/3/93 |
| 11 | IMG_6757 | P-A | photo | 0.0662 | 0.1800 | 0.0184 | - | 0/1/95 -> 0/3/93 |
| 12 | IMG_6746 | P-A | photo | 0.0649 | 0.1716 | 0.0103 | - | 0/2/94 -> 0/10/86 |
| 13 | IMG_6759 | P-A | photo | 0.0641 | 0.1780 | 0.0170 | - | 0/0/96 -> 0/2/94 |
| 14 | IMG_6756 | P-A | photo | 0.0636 | 0.1777 | 0.0174 | - | 0/0/96 -> 0/0/96 |
| 15 | IMG_6752 | P-A | photo | 0.0631 | 0.1780 | 0.0168 | - | 0/0/96 -> 0/0/96 |
| 16 | IMG_6768 | P-A | photo | 0.0526 | 0.1625 | 0.0154 | - | 1/4/91 -> 0/19/77 |
| 17 | IMG_6770 | P-A | photo | 0.0462 | 0.1446 | 0.0120 | - | 0/2/94 -> 0/10/86 |
| 18 | IMG_6767 | P-A | photo | 0.0432 | 0.1564 | 0.0136 | - | 1/10/85 -> 0/42/54 |
| 19 | IMG_6769 | P-A | photo | 0.0431 | 0.1417 | 0.0123 | - | 2/4/90 -> 0/18/78 |
| 20 | IMG_6761 | P-A | photo | 0.0403 | 0.1492 | 0.0109 | - | 0/2/94 -> 0/17/79 |

The 21st by mean absolute change: IMG_6766 (0.0395). The sixth to eighth videos by input-2
saliency movement: GX011621 0.241, GX011592 0.239, GX011616 0.227.

#### Readings (measurement, not a look judgement)

- **The scanned band falls set-wide under (d).** Qualifying sides 963 -> 39 (video) and 248 -> 13
  (photo); items with a qualifying side 49 -> 18 and 50 -> 11; the largest qualifying band 15.2 ->
  2.1 and 13.8 -> 2.6 x C. Of the shipped qualifying sides, 567 / 963 (video) and 105 / 248 (photo)
  go to `none`, 359 and 131 to `undecided` (not removal), 37 and 12 stay `band`. No item's scan
  rises by the sheet's rule; at the side level one band rises (IMG_6800, 0.11 -> 0.56 x C) and 115
  sides go from none to undecided.
- **(d) also changes texture set-wide, most on a group of P-A photos.** The whole-frame standard
  deviation of L* falls on every photo ((d) / shipped 0.19-0.98, median 0.895) and on 149 of 150
  video frames (0.52-1.006; the one exception IMG_6742 f10, 13.75 -> 13.83); the mean L* falls slightly (median -0.34 photo, -0.17 video). The
  largest whole-image changes are ten P-A photos (IMG_6746, IMG_6751-IMG_6759; mean absolute
  0.063-0.086, about 16-22 / 255) whose scan is undecided on 94-96 of 96 sides at the shipped
  defaults and whose std L* falls to 0.19-0.45 of shipped (IMG_6751 11.75 -> 2.57, IMG_6752 7.67 ->
  1.45): consistent with Part 1's reading that the saturated N{} stretch amplifies noise and fine
  texture, which the clip limits everywhere; whether that is the look the owner preferred is the
  owner's judgement (the contact sheet's photos 6-20). std L* does not separate noise from
  texture.
- **CHARC's addendum (msg 61fa577714607f97, relayed by the orchestrator): stated as an
  OBSERVATION.** CHARC viewed the sheet and saw the clip visibly soften fine texture wherever
  the local range is narrow, not only at halo edges: the fabric pattern on item 01, IMG_6762, and
  the grain on item 06, IMG_6751. The sighting is CHARC's; the cell has no eye on it. CHARC's
  counts were verified against the records and agree: 963 -> 39 over 50 videos, 248 -> 13 over
  70 photos, and a clipped fraction of 0 under (d). The measurement columns from the records:
  IMG_6762 f90 mean abs 0.0191, p99 0.1254, std L* 18.37 -> 17.93 (only 2.4 %: a local texture
  loss does not show in the whole-frame measure), input-2 saliency 0.684; IMG_6751 mean abs
  0.0856, p99 0.1526, std L* 11.75 -> 2.57. No preference judgement.
- **No clipping under (d)** on any image (shipped up to 0.0047): input 2 is held inside the local
  range of its unsharpened form, which lies in [0, 1].
- **The cached statistics.** Only input 2's smoothed saliency mean moves (0.070-0.684 Lab; largest
  IMG_6762); every white-balance record and the fusion bounds are unchanged, as Part 2's (i)
  column states for (d).
- **No STOP.** No record exposes an instrument defect: every item `done` and published, every crop
  run's render and prefused checks equal, the crop bands equal Part 2's records, the V3 shipped leg
  reproduced the record. The stale `D106 25` label (above) is outside the owned files.

Depth at Part 3 yield: DISPATCHER TO FILL
