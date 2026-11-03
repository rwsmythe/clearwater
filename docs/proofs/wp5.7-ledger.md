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
