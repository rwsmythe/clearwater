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

Depth at step-2D end: DISPATCHER TO FILL
