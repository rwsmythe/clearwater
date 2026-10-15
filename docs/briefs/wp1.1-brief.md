# WP1.1 — Reference pipeline prototype (dispatch brief, DRAFT)

**Status:** draft by CHARC, 2026-10-15, commissioned to the orchestrator, which issues the
FINAL brief in the plan's section 4.6 format. Needs no footage: it runs on one image, and the
tests use synthetic images. Prototype code is evidence, not product (plan section 6, Phase 1):
it lives under `tools/prototype/`; Phase 3 may reuse it only under the full definition of done.

| Field | Content |
|---|---|
| ID and title | WP1.1 — Reference pipeline prototype |
| Goal | A script-level, CPU, NumPy implementation of the whole correction pipeline (spec section 6.2 and 6.3) on one image, faithful to the two reference papers, with every open value recorded, so WP1.2 (CPU/GPU variant and timing), WP1.3 (look check) and WP1.4 (noise and statistics) have one reference to build on. |
| Spec clauses | 6.1 (the papers are authoritative over the spec's summaries); 6.2 (the five pipeline steps, the gain clamp D99, the weight regularisation delta = 0.1, K = 2); 6.3.1 (Ancuti 2018 red and optional blue compensation, alpha, the gain caps D50/D52/D100); 6.3.2 (3C in BT.709 YCbCr on display-encoded values D47, kappa = 1.0 / lambda = 0.7, mask M, large-support Gaussian); 6.4 (float32 in [0, 1]); 6.6 and D56 (spatial parameters as a fraction of the short side; pyramid depth by minimum coarsest-level size); 6.7 (the full v1 parameter list); 14.1 (the open values this package must set and record). Plan section 6 WP1.1. |
| Depends on | WP0.1 (merged). Not on WP0.2 or CP1. |
| Files owned | `tools/prototype/__init__.py`, `tools/prototype/params.py`, `tools/prototype/pipeline.py`, `tools/prototype/run.py`, `tests/test_prototype_pipeline.py`, `docs/reports/wp1.1-open-values.md`, `docs/reports/wp1.1-3c-correspondence.md`, `docs/proofs/wp1.1-ledger.md`, `uv.lock`, and in `pyproject.toml` ONLY the dependency grants below plus, if and only if mypy strict rejects an untyped import, a `[[tool.mypy.overrides]]` entry naming exactly that module. |
| Interfaces consumed | None. Must not import `tools/local_config.py`, `tools/inventory.py` or `tools/environment_report.py`. |
| Interfaces provided | See "Interfaces" below. These are PROTOTYPE interfaces: not frozen; WP2.1 freezes the product's. |
| Dependencies | Grants (dev group, CHARC-approved; product adoption is decided at WP2.1 and WP1.2): `numpy` (BSD-3) for arrays, `scipy` (BSD-3) for `scipy.ndimage` Gaussian filtering and resampling, `Pillow` (already granted in WP0.2) for reading and writing the image. Nothing else: no OpenCV, no scikit-image, no CuPy, no PyTorch (WP1.2 owns the GPU question). |
| Tests | `tests/test_prototype_pipeline.py` on synthetic images only (gradients, flat fields, a known colour cast, a tiny noise field); roster below. No `footage`, `gpu` or `slow` marks. |
| Hardware flags | None. No timing or memory figure is a RESULT of this package (plan section 4.3; WP1.2 measures). The return report may mention elapsed time informally, labelled as such. |
| Out of scope | GPU execution (WP1.2); any timing or memory claim (WP1.2); the look check on real footage (WP1.3); staged statistics, temporal smoothing, video (Phase 3); colour management beyond "display-encoded RGB in, same values out" (the PNG written carries no ICC profile and says so in its docstring); the product's parameter schema and GUI; chroma handling; any file under `src/clearwater/`. |
| Done | Plan section 4.5; the four gates and the harness gate green on the final head; both report documents complete; the return report lists every open value set, with its source. |

## Interfaces

`tools/prototype/params.py`

- `@dataclass(frozen=True) class Params` covering EVERY spec section 6.7 control plus the open
  values of section 14.1 that this pipeline needs, each with a default and a docstring line
  naming its source (paper value, spec value, or "WP1.1 choice, see open-values report"):
  `method: Literal["ancuti2018", "c3"]`; `alpha: float` (1.0); `blue_compensation: bool` (False);
  `red_gain_cap: float`, `blue_gain_cap: float` (the "set multiple of the channel's original mean",
  section 6.3.1; `None` disables; defaults are WP1.1 choices); `kappa: float` (1.0), `lambda_: float`
  (0.7), `c3_strength: float` (1.0, scales kappa and lambda together); `c3_kernel_fraction: float`
  (Gaussian sigma for G{} as a fraction of the short side), `c3_mask_threshold: float` (0.85),
  `c3_mask_smooth_fraction: float`; `white_balance_strength: float` (1.0 = full gray-world,
  0.0 = none), `max_white_balance_gain: float` (D99); `gamma: float` (fusion input 1);
  `sharpen_strength: float`, `sharpen_blur_fraction: float`; `normalisation_low: float`,
  `normalisation_high: float` (percentiles for the histogram stretch N{}); `laplacian_fraction`,
  `saliency_blur_fraction` (weight-map spatial parameters); `weight_delta: float` (0.1);
  `pyramid_min_level_size: int`; `blend_with_original: float` (0.0 = fully corrected; the direction
  is a WP1.1 choice recorded for V9).
- `Params.neutral() -> Params`: the parameter set under which the pipeline is as close to identity
  as the method allows (needed by V9 later); the report states how close, measured on a synthetic
  image, and which steps cannot be neutral (fusion of two identical inputs is identity; gamma = 1,
  sharpening 0, white balance 0, compensation 0).

`tools/prototype/pipeline.py` (all arrays `numpy.typing.NDArray[np.float32]`, shape `(H, W, 3)`,
display-encoded RGB in [0, 1]; every function pure; no I/O)

- `compensate_ancuti2018(image, params) -> tuple[Image, CompensationInfo]` — red (and blue when
  enabled) per section 6.3.1; `CompensationInfo` records the channel means, the requested and the
  effective alpha per channel after the gain cap, and the mean added amount.
- `compensate_c3(image, params) -> tuple[Image, CompensationInfo]` — section 6.3.2 in BT.709
  YCbCr (full-range equations on [0, 1] values; the matrix is written out in the module with its
  source); mask M as specified; Gaussian with the configured fraction.
- `white_balance(image, params) -> tuple[Image, WhiteBalanceInfo]` — gray-world gains toward the
  channel mean, scaled by `white_balance_strength`, each gain clamped to `max_white_balance_gain`
  (D99); the info records raw and clamped gains and which channels were clamped.
- `fusion_inputs(image, params) -> tuple[Image, Image]` — input 1 = gamma; input 2 =
  `(I + N{I - G*I}) / 2` with N{} the percentile stretch of section 6.2, bounds from the whole
  image.
- `weight_maps(input_, params) -> Weights` — Laplacian contrast (absolute of the Laplacian of the
  luminance), saliency per Achanta et al. 2009 (frequency-tuned: the norm of the Gaussian-blurred
  Lab image minus the Lab mean; the cell writes the conversion it uses and its source), saturation
  (the paper's definition: deviation of R, G, B from the luminance); the three combined per input,
  then normalised across the two inputs with `(W_k + delta) / (sum W_k + K * delta)`.
- `multiscale_fusion(inputs, weights, params) -> Image` — Laplacian pyramid of each input, Gaussian
  pyramid of each normalised weight, level-wise blend, collapse. Pyramid depth from
  `pyramid_min_level_size`. Resampling by a fixed documented method (a 5-tap binomial kernel with
  symmetric borders is the paper's practice; state what is used).
- `correct(image, params) -> Result` — runs the five steps and the final blend with the original;
  `Result` carries `output` plus every intermediate (compensated, white-balanced, input 1, input 2,
  the six raw weight maps, the two normalised weights) and the two info records, so WP1.3 and
  WP1.4 can inspect any stage.
- `spatial_sigma(image_shape, fraction) -> float` — the single place that turns a fraction of the
  short side into pixels (D56).

`tools/prototype/run.py` — `main(argv) -> int`: `--in FILE`, `--out DIR`, `--method ancuti2018|c3`,
`--blue`, `--neutral`, `--dump` (write every intermediate as PNG and the two info records as JSON),
and one `--set name=value` per parameter override. Reads with Pillow into float32 [0, 1] RGB
(ignoring any embedded profile and saying so), writes `<out>/<stem>-<method>.png` as 16-bit RGB.
Exit 0; 2 on a bad argument or unreadable image, with a one-line error.

## Required end state (the claim list)

1. `uv run python tools/prototype/run.py --in <photo> --out <dir> --method ancuti2018` and
   `--method c3` each write a corrected 16-bit PNG; `--dump` writes every intermediate.
2. The Ancuti 2018 and 3C equations in `pipeline.py` match spec sections 6.3.1 and 6.3.2 symbol for
   symbol, and the fusion steps match section 6.2, with the two papers taken as authoritative
   where the spec summarises (section 6.1). Each function's docstring cites the equation.
3. Every spatial parameter is a fraction of the short side and passes through `spatial_sigma`;
   the same `Params` on an image and on its 2x downscale produce visually matching output (test:
   the downscaled output and the output of the downscaled input agree within a stated tolerance).
4. `docs/reports/wp1.1-3c-correspondence.md` confirms (or corrects) kappa -> Cr and lambda -> Cb
   (spec 14.1): derive from the paper's a*/b* roles and the BT.709 YCbCr definition, and show the
   effect on a synthetic red-deficient image.
5. `docs/reports/wp1.1-open-values.md` lists EVERY value the papers or the spec leave open (spec
   14.1's "default values where the papers leave them unspecified" and the gain cap multiples, the
   normalisation percentiles, the saliency conversion, the pyramid resampling kernel, the blend
   direction, the neutral set), the value chosen, and its source or reasoning. This report is the
   input to WP2.1's architecture document.
6. Docstrings complete (Google style); ruff, ruff format, mypy strict (on `tools/prototype/`) and
   pytest green; harness gate green; the dependency grants are the only `pyproject.toml` change
   beyond an optional mypy override.

## Test roster (`tests/test_prototype_pipeline.py`, synthetic only)

- Shapes, dtype float32 and range [0, 1] preserved by every stage, on a 64x96 and a 97x65 image
  (odd sizes exercise the pyramid).
- Pyramid identity: `multiscale_fusion([A, A], weights)` equals A within 1e-5 for any weights;
  `multiscale_fusion([A, B], [1, 0])` equals A within 1e-4 (the collapse reconstructs).
- Normalised weights sum to 1 at every pixel.
- Red compensation is identity when mean R equals mean G; adds a positive amount when R < G; the
  gain cap limits the mean added amount to the configured multiple.
- 3C on a neutral gray image is identity; on a red-deficient image it raises Cr; the mask leaves
  pixels with mean(R, G, B) > 0.85 unchanged.
- White balance: gray-world gains computed correctly on a flat colour field; the D99 clamp holds
  the gain at the maximum and the info record says so.
- `Params.neutral()` output equals the input within the tolerance the report states.
- Resolution independence (claim 3) at 2x.
- `run.py` end to end on a generated PNG in tmp: file written, 16-bit, right shape; `--dump` writes
  the intermediates; bad arguments give exit 2.

## Declared operating envelope

CPU only, Windows 11, Python 3.12 under uv, one image at a time up to a 48-megapixel photo or a
5.3K frame (it may be slow; no timing claim). sRGB or Display P3 display-encoded 8- or 16-bit input
treated as values in [0, 1] without colour management. Linear-light inputs, HDR transfer
functions, video and the GPU are out of envelope.

## Notes for the cell

- The reference papers are the authority (spec 6.1). The research notes
  (`docs/underwater-imagery-correction-research.md`) are background only and carry no formulas.
  Where you rely on your knowledge of a paper's equation, write the equation in the docstring
  with the paper and section; where you cannot recall a value, choose, record it in the open-values
  report as a WP1.1 choice, and move on. Do not stop for an open value; DO stop for a formula you
  cannot reconstruct.
- `uv sync` in the worktree; commit by pathspec; `feat(wp1.1): ...` with the `Co-Authored-By:`
  footer; never a bare `cd`.
- STOP and return on: any dependency beyond the grants; a spec clause that contradicts a paper
  (report both texts; CHARC rules); a need to touch a file outside the owned list.
