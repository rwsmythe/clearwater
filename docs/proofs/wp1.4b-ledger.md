# WP1.4b ledger -- gain-cap noise test and deep-frame statistics

Brief: `docs/briefs/wp1.4b-brief.md` (FINAL). Base `db751cb`. Branch `wp1.4b`, worktree
`.worktrees/wp1.4b`. Spec v0.5.3. Cell: implementer-opus-high (Claude Opus 5.5).

## Commits

| Commit | What |
|---|---|
| `b23bad9` | Claim 1: `Params().method` defaults to `"c3"`; docstring sentence. `tools/prototype/params.py` only. |
| `fddc4e3` | Claim 1: pins. 62 test sites name `method="ancuti2018"` (or `--method ancuti2018`); `run.py` help names c3 as the default; guard tests. |
| (WIP) | Claims 2, 2a, 3-6, 10 code: `tools/noise_experiments.py`, `tools/camera_state.py`, tests; this ledger. |

## Claim 1 -- the flip's site list

Rule applied: a test site is pinned when its `Params` reaches a function that reads
`params.method` (`pipeline.correct`, `temporal.measure` / `statistics_of` /
`analyse_staged` / `white_balanced_high_pass`, the `clip` pipeline, `run.py`), so the suite
exercises the same paths as before the flip. Sites whose functions never read the method
(the step functions, `Params` validation, `memory_estimate_bytes`) are not touched.

- `tests/test_lookcheck.py`: 2 (`test_bound_flags_report_...`: failed after the flip).
- `tests/test_prototype_backend.py`: 5 (3 run.py `--method ancuti2018`: failed; 141, 268, 326, 329 reach `correct`).
- `tests/test_prototype_pipeline.py`: 9 (3 run.py argv: failed; 156/158/160, 503-505 `correct`).
- `tests/test_prototype_clip.py`: 20 (every clip-pipeline site; 3 `Params.neutral()` as `dataclasses.replace(..., method="ancuti2018")`).
- `tests/test_prototype_temporal.py`: 25. `tests/test_lookcheck_deep.py`: 1.
- Tools: none needed. `statistics_experiments.py` (`METHODS` dict names both), `clip.py`
  (`--method` default `"ancuti2018"` explicit), `bench.py` (`--method` required), `pack.py`
  (every variant names its method; `"defaults"` records `Params()` as it is) already name it.
- `tools/prototype/run.py`: follows `Params()`; usage line and `--method` / `--blue` help
  name c3 as the default and list ancuti2018 / ancuti2018-blue (guard ii).
- Open item (not mine to edit): `Params.neutral()` docstring "The method stays the default;
  `dataclasses.replace(Params.neutral(), method="c3")` is neutral too" is still true but now
  reads oddly (c3 IS the default).

Suite after the pins: 375 + 289 + 124 passed across three foreground groups (the whole
suite exceeds one 10-minute call), 0 failed, 0 skipped.

## Verification loop (suspect -> confirm -> fix)

| # | Suspected | Confirmed? | Fix |
|---|---|---|---|
| 1 | Tests passing under c3 silently changed coverage | Yes (e.g. temporal staged tests ran c3's 2-stage chain) | Pinned by the method-reader rule above |
| 2 | Float pts could make `extract` pick the next frame | Possible (limit_denominator rounding) | Ask for `pts - 1e-4 s`; pts checked against the list |
| 3 | Haar plane test exact zero on float plane | Rounding 1e-16 | Integer plane in the test |
| 4 | Source sigma_R = 0 makes amplification divide by zero | Yes, on real deep frames | Ratio recorded as `None`; **STOP raised (below)** |

## STOP (2026-10-19): the defined noise measure reads 0 on every deep frame

Evidence: `work/wp1.4b/stop/` (`diag.py`, `diag-output.txt` md5 be6c2ce0...,
`probe.py`, `probe-output.txt` md5 3e3a008c...). On all 8 deep frames the Donoho estimate on
the fixed flat tiles is exactly 0 for R, G and B of the SOURCE, and 0 for the output red under
Ancuti cap off / 2 / 0.5 and c3: 63-99 % of the HH1 coefficients in those tiles are exactly 0
(8-bit HEVC has flattened the flat regions), and the source red there is crushed (tile mean
0.005-0.06 on six frames, one distinct value per tile). Immerkaer on the same tiles is
non-zero and moves with the settings (frame 0665: output R 0.203 / 0.195 / 0.085 / 0.003
code values for cap off / 2 / 0.5 / c3). The synthetic validation tests (1-4) all pass; the
premise that fails is the data, not the code. Awaiting the dispatcher's ruling.

## Review rounds (Reviewer A)

None yet (the review runs on the finished package).

## NEXT STEPS

1. Apply the dispatcher's ruling on the noise measure (the STOP above).
2. `uv run python tools/noise_experiments.py grid` one frame per call (13 frames; frames
   and `frames.json` already extracted in `work/wp1.4b/`).
3. `... smoothing` (claim 10; the cap binds on 104/179 smoothed frames per WP1.3D).
4. `... summarise`; write `docs/reports/wp1.4b-gain-cap-noise.md` from `summary.json`.
5. Full suite in groups; Reviewer A loop (STRONG) per brief.
