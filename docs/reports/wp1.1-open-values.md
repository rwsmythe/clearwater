# WP1.1 -- open values of the reference pipeline prototype

Every value the two reference papers or the spec leave open, as set in
`tools/prototype/params.py` and `tools/prototype/pipeline.py`, with its source. This is an
input to WP2.1's architecture document. Sources: **paper** = [A18] Ancuti et al., "Color
Balance and Fusion for Underwater Image Enhancement", IEEE TIP 27(1), 2018, or [3C]
Ancuti et al., "Color Channel Compensation (3C)", IEEE TIP 29, 2020; **spec** = a value
fixed in `docs/underwater-correction-spec.md`; **WP1.1 choice** = set here, with the
reasoning given. Every WP1.1 choice is provisional: the look check (WP1.3) and the noise
and statistics work (WP1.4) may move it. Spatial values are fractions of the image's short
side (spec 6.6, D56), turned into pixels only by `spatial_sigma`.

## 1. Parameter defaults (`Params`)

| Field | Default | Source and reasoning |
|---|---|---|
| `method` | `ancuti2018` | WP1.1 choice. The spec names no default method; Ancuti 2018 is the primary method of [A18] and the one the gain-cap measurement (D100) needs. |
| `alpha` | 1.0 | paper ([A18]: alpha = 1). |
| `blue_compensation` | off | spec 6.3.1 ("off by default"). |
| `red_gain_cap`, `blue_gain_cap` | 2.0 each (`None` disables) | WP1.1 choice. Semantics per spec 6.3.1: alpha is reduced per image so that the mean added amount `alpha (mean_g - mean_c) mean((1 - I_c) I_g)` is at most `cap x mean_c`, i.e. the compensated channel mean is at most `(1 + cap)` times the original. 2.0 lets a typical shallow image compensate fully and limits a deep frame (red mean 0.05 under green 0.5 would otherwise gain about 4x its mean). Whether the caps stay at all is decided at the prototype gate (spec 6.3.1 Status, D100). Edge: a channel with mean 0 gets no compensation under a cap (the cap is 0 x 0). |
| `kappa`, `lambda_` | 1.0, 0.7 | paper ([3C] underwater defaults, via spec 6.3.2). |
| `c3_strength` | 1.0 | spec 6.3.2 / D48 (one slider scaling kappa and lambda together); the rule `effective = c3_strength x kappa` (and x lambda) is the WP1.1 reading of "scales kappa and lambda together from the 1.0/0.7 ratio". |
| `c3_kernel_fraction` | 0.05 (sigma of G{}) | WP1.1 choice. The paper asks for a Gaussian of large support; sigma = 5 % of the short side gives a 4-sigma support of +/-20 % of it (about 150 px sigma on a 3024 px iPhone short side). Larger kernels approach a global gray world and cost more on the CPU (separable filter, cost linear in sigma). |
| `c3_mask_threshold` | 0.85 | spec 6.3.2. |
| `c3_mask_smooth_fraction` | 0.01 | WP1.1 choice, converting a pixel value. Reviewer A (round 2) cites [3C] pp. 2657-58 as giving a default kernel size of 20 for the mask's Gaussian; WP1.1 has not checked this against the PDF (none is in the repository). A size of 20 px is a sigma of roughly 3-4 px if it is the kernel width (about 6 sigma) or 20 px if it is the sigma; fixed in pixels it is not resolution independent, so it has to become a fraction of the short side, which needs the paper's image size. 0.01 (6 px sigma on a 600 px short side, 30 px on a 3024 px photo) keeps the protected regions their size without a visible mask edge; WP1.3 checks it against the paper's value. |
| `white_balance_strength` | 1.0 | paper (full gray world). The interpolation is WP1.1's: requested gain `= 1 + s (g - 1)`, linear in the gain, so 0 is exactly no white balance. |
| `max_white_balance_gain` | 3.0 (must be >= 1) | WP1.1 choice (D99 asks for a maximum; spec 14.1 lists the default as open). A maximum below 1 is rejected: it would lower every gain, so strength 0 would no longer be neutral. After compensation the red gain of an ordinary image should stay well under 3, so the clamp is meant to bind on deep frames, where D99 wants it to; WP1.4's deep-frame noise measurement is the check. |
| `gamma` | 1.5 | WP1.1 choice; [A18] gives no value (spec 6.1 names exactly this gap). Input 1 is `I ** gamma`; [A18] motivates it by white-balanced images appearing too bright, so gamma > 1; 1.5 is a moderate darkening (0.5 -> 0.35). |
| `sharpen_strength` | 1.0 | paper ([A18] S). Interpolation `I + s (S - I)` is WP1.1's: 0 gives exactly `I`. |
| `sharpen_blur_fraction` | 0.005 | WP1.1 choice; [A18] does not give the Gaussian's size. About 15 px on a 3024 px short side: the unsharp mask lifts edges and mid-scale texture rather than noise. |
| `normalisation_low`, `normalisation_high` | 0.5, 99.5 (percentiles) | WP1.1 choice (spec 14.1 "robust statistic choices for normalization bounds"). [A18]'s N{} stretches to the full range (min/max); percentiles keep a few noisy or clipped pixels from setting the scale. |
| `laplacian_fraction` | 0.001 | WP1.1 choice; [A18] uses a per-pixel Laplacian. 0.001 of the short side is about 3 px on a 3024 px photo and 2 px on a 2160 px frame, near the paper's per-pixel scale on its test images while staying resolution independent. |
| `saliency_blur_fraction` | 0.003 | WP1.1 choice. Achanta et al. blur with a small binomial (about 1 px sigma) on images of about 300 px short side; 0.003 keeps that relative scale. |
| `weight_delta` | 0.1 | paper ([A18]; spec 6.2). K = number of inputs = 2. |
| `pyramid_min_level_size` | 16 px | WP1.1 choice. Depth: levels are added while the halved short side stays >= 16 px (`pyramid_levels`); a 3024 px short side gives 8 levels (coarsest 24 px), 2160 px gives 8 (17 px). A size in pixels means the coarsest level holds the whole scene at the same resolution (a short side of 16-30 px) whatever the image size; an image twice as large gets one more fine level, and level k of the small image matches level k + 1 of the large one, which is what resolution independence needs. |
| `blend_with_original` | 0.0 | WP1.1 choice of direction (spec 14.1): 0.0 = fully corrected, 1.0 = the original; `output = (1 - b) fused + b original`, linear in display-encoded values. At 1.0 the output is the input bit for bit. |

## 2. Method details the papers leave open

| Item | Value | Source and reasoning |
|---|---|---|
| Channel means for compensation | Over the whole image, all pixels equal weight; blue uses the original (uncompensated) means. | [A18] (image means). A whole-frame statistic (spec 7.1). |
| Clipping | Every step clips its output to [0, 1]. | WP1.1 choice; keeps every stage in the spec 6.4 range. Ancuti compensation with alpha <= 1 and mean_g > mean_c stays in range by construction; white-balance gains above 1 and 3C chroma shifts can leave it, and clip there. |
| Gray-world target | Mean of the three channel means (keeps mean brightness). | WP1.1 choice; [A18] says "Gray-World" without the target. |
| White-balance clamp | Upper clamp only (D99); gains below 1 are not clamped. A channel mean under 1e-6 is treated as 1e-6. | spec D99; floor is WP1.1's. |
| 3C working space | Full-range BT.709 YCbCr, zero-centred chroma (Cb, Cr in [-0.5, 0.5]); the matrix is written out in `RGB_TO_YCBCR` with its ITU-R BT.709-6 source. | spec D47; zero-centring is required for `C - k G{C}` to pull toward neutral. |
| 3C output | `RGB + YCBCR_TO_RGB @ (0, dCb, dCr)` (exactly the YCbCr round trip, since the transform is linear and Y is unchanged); masked pixels stay bit-identical. | WP1.1 implementation choice. |
| 3C correspondence | kappa -> Cr, lambda -> Cb, confirmed. | See `docs/reports/wp1.1-3c-correspondence.md`. |
| N{} (histogram stretch) | One shift and one scale for all three channels ([A18]: "a unique shifting and scaling factor"), bounds = the two percentiles above taken jointly over all pixels and channels of `I - G*I`, with linear interpolation between order statistics (NumPy `percentile`, `method="linear"`, the R-7 / Hyndman-Fan type 7 definition), values outside clipped. A flat high-pass (bounds closer than 1e-6) maps to 0.5. | [A18] for the form; percentiles and the flat case are WP1.1's. |
| Luminance for the weights | BT.709 luma `0.2126 R + 0.7152 G + 0.0722 B` on display-encoded values (the Y of the 3C matrix). | WP1.1 choice; [A18] says "luminance" without a definition. |
| Laplacian contrast | **Adaptation of the paper's equation, required by spec 6.6 (D56) and the brief's `laplacian_fraction`.** [A18]: `W_L = |Lap(L)|`, the absolute Laplacian of the luminance at the pixel scale (no spatial parameter). Spec 6.6 lists the Laplacian among the spatial parameters expressed as a fraction of the short side. Implemented: `|sigma^2 x Lap(G_sigma * L)|`, the paper's 5-point discrete Laplacian on the Gaussian-smoothed luma, times sigma^2 (scale normalisation, so the weight keeps its size relative to W_S and W_Sat across resolutions); the paper's form is the sigma -> 0 limit up to the factor sigma^2. The form of the adaptation (prefilter and sigma^2) is the WP1.1 choice; RULED by CHARC 2026-10-15 (ad686b8b65a71061): accepted as a spec-driven departure from [A18] (spec 6.6 / D56); the pixel form was rejected because it breaks V8 / F3. scipy's `gaussian_laplace` is not used: its sampled kernel is not zero-sum at small sigma and gave a flat image a nonzero weight (caught by `test_weight_maps_follow_their_definitions`). | spec 6.6 / D56; form ruled by CHARC. |
| Saliency conversion | sRGB EOTF and sRGB-to-XYZ matrix (IEC 61966-2-1:1999), CIELAB with the D65 white (CIE 15:2004); `W_S = ||mean Lab - blurred Lab|| / 100`. A Display P3 source is read as sRGB here (weight only; no colour management in scope). The /100 puts W_S on the same order as W_L and W_Sat (L\* spans [0, 1]) without a per-image normaliser, so it adds no flickering statistic; the mean Lab vector is the "saliency reference value" of spec 7.1. | Achanta et al. 2009 (form and Lab); scale and conversion standard are WP1.1's. |
| Saturation | `sqrt(((R - L)^2 + (G - L)^2 + (B - L)^2) / 3)`. | paper ([A18]). |
| Weight aggregation | `W_k = W_L + W_S + W_Sat` (sum), then `(W_k + delta) / (sum W_k + K delta)`. | paper ([A18]: the three maps are summed). |
| `weight_maps` signature | As built: `weight_maps(input_: Sequence[Image], params: Params) -> Weights`, taking ALL the fusion inputs (input 1, input 2) in order, not one input. The normalisation `(W_k + delta) / (sum_k W_k + K delta)` needs every input's aggregated weight at each pixel, and `Weights` returns the six raw maps together with the two normalised ones, so one call must see both inputs. | **Accepted brief-interface deviation** (the brief's signature names a single `input_`); prototype interface, not frozen. |
| Pyramid resampling | REDUCE: separable 5-tap binomial `[1 4 6 4 1] / 16`, symmetric borders (`d c b a | a b c d`), keep rows and columns 0, 2, 4, ... (odd n -> (n + 1) / 2). EXPAND: zero-insert at the even positions, same filter, divided by the filter applied to the sample indicator (exactly x4 in the interior; keeps constants constant at the borders). The Laplacian pyramid uses the same EXPAND for building and collapsing, so reconstruction is exact up to float round-off. | Burt and Adelson, the paper's practice; the border normalisation is WP1.1's. |
| Gaussian filters | `scipy.ndimage`, symmetric borders, truncated at 4 sigma, sigma = fraction x short side with no floor: a sigma well under 1 px gives a kernel close to the identity (exactly `[1]` under 1/8 px), the right limit for an image too small to hold that detail. | WP1.1 choice. |

## 3. Whole-frame statistics the prototype computes (for WP1.4 and spec 7.1, D97)

In chain order: compensation channel means (and the gain-cap effective alpha derived from
them; 3C has none, its local means are not whole-frame); white-balance channel means and
gains (on the compensated image); the two N{} bounds (on the white-balanced image); the mean
Lab vector of each fusion input (saliency reference). All are recorded on `Result`
(`CompensationInfo`, `WhiteBalanceInfo`) except the N{} bounds and the Lab means, which
are computed inside `fusion_inputs` and `weight_maps`.

## 4. The neutral set (V9) and the tolerances the tests state

**Neutral set** (`Params.neutral()`): `alpha = 0`, `c3_strength = 0`,
`white_balance_strength = 0`, `gamma = 1`, `sharpen_strength = 0`,
`blend_with_original = 0` (the identity comes from the steps, not from blending back).
Every step is then an identity: compensation adds `0 x ...`, the gains are 1, input 1 is
`I ** 1`, input 2 is `I + 0 x (S - I)`, and fusing two identical inputs reconstructs the
image whatever the weights. **No step is non-neutral** beyond float32 round-off in the
pyramid. Measured (2026-10-14, `measure.py` kept with the review evidence): maximum
absolute difference output vs input at most 1.19e-7 (one float32 step near 1) for both methods:
8.9e-8 on 64 x 96 and 1.19e-7 on 97 x 65 synthetic images (re-measured at the final head). **Stated tolerance: 1e-6** (the test
`test_neutral_params_reproduce_the_input`). After 16-bit export the difference is below
one code value.

**Resolution independence at 2x** (claim 3; `test_output_is_resolution_independent_at_2x`):
a band-limited 128 x 192 scene vs its 2x2 box downscale, both corrected with the same
`Params` (fractions raised so that every spatial scale is resolved on the 64 px short
side); compared: the box-downscaled large output vs the small output. **Stated tolerance:
mean absolute difference <= 0.01 and 99th percentile <= 0.02** (values in [0, 1]).
Measured: Ancuti 2018 mean 0.0026, p99 0.0050; 3C mean 0.0071, p99 0.0105. With spatial
parameters fixed in pixels instead of fractions (a `spatial_sigma` returning the same
pixel sigma for both sizes) the p99 is 0.041 (Ancuti 2018) and 0.064 (3C), so the test
distinguishes.

**With the default `Params`** (`test_default_params_are_resolution_independent_at_2x`): a
512 x 768 textured scene (the smooth scene modulated by a random texture of scale 0.01 of
the short side) vs its 2x2 box downscale. **Stated tolerance: mean <= 0.0015, p99 <=
0.005.** Measured: Ancuti 2018 mean 0.0004, p99 0.0022; 3C mean 0.0005, p99 0.0028. With
pixel sigmas pinned to the large image's, mean 0.0021 / 0.0046 and p99 0.0079 / 0.0192.

The scene includes a soft-edged bright disc (mean above 0.85, about 5 % of the pixels)
so that the 3C mask and its smoothing are exercised; pinning only the mask sigma in pixels
raises the 3C p99 to 0.015. With a hard-edged disc instead, the p99 rises to 0.008 (Ancuti
2018) and 0.012 (3C), with single edge pixels up to 0.31 apart: a box downscale of the
output is not the output of the box-downscaled edge once the nonlinear steps (clipping, the
N{} stretch) act on it.

**Stated floor for resolution independence at the defaults (not a test):** the default
`Params` are resolution independent only where their scales are resolved; the claim is
NOT made at or below a 128 px short side (the tested pair is 256 vs 512 px, textured
scene, see above). In the 64-128 px short-side
range (a 64 vs 128 px short side, smooth scene) the default sharpening and Laplacian sigmas
are under one pixel, the high-pass that N{} stretches is nearly empty, and the two outputs
differ at 2x by p99 0.06-0.07. Preview sizing (WP1.3, spec 6.6 / V8) must stay above this
floor; a screen-resolution preview (typically 1000 px or more on the short side) is well
above it.

## 5. Input and output of `run.py`

| Item | Value | Source and reasoning |
|---|---|---|
| Reading | Pillow; 8-bit values / 255, 16-bit grayscale / 65535; alpha dropped; EXIF orientation applied (the PNG written has no orientation tag). | brief (Pillow); orientation is WP1.1's. |
| Colour | Embedded ICC profile ignored, with a note on standard error; values used as display-encoded RGB. | brief (no colour management). |
| 16-bit RGB sources | Pillow 12.3 decodes 16-bit-per-channel RGB (48-bit PNG, 16-bit TIFF) to 8 bits; the run prints a warning and continues at 8-bit precision. | Pillow limitation within the granted dependencies; raised as an open question in the return report. |
| Output | 16-bit RGB PNG written directly (Pillow cannot write 16-bit RGB), values clipped and rounded to 0..65535, no ICC, gamma or colour chunk; `--dump` intermediates the same, weight maps as 16-bit gray, raw weights divided by their own maximum (recorded in `<stem>-<method>-weights.json`). | WP1.1 choice. |
