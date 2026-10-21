# WP3.2 — Accept record (channel compensation and white balance: `clearwater.methods.compensation`, `clearwater.methods.white_balance`)

**Accepted 2026-10-21 by the orchestrator** (generation 7, session
`clearwater-orchestrator-20261020-1419`). Gate per `docs/review-gate-clearwater.md` Part 2.
Tier STRONG. Wave 2, tranche A; stacked gate with WP3.3 and WP3.5 (this package merges third).
- Brief approval and rulings: CHARC `53b752a4d7fac4fc` (X-1..X-4, question 5 no record types).
  Round-0 (S-1..S-4) and round-1 rulings: orchestrator generation 6 (in the ledger). Reviewer B
  remediation rulings: orchestrator generation 7, with CHARC's addition (a Python int as well
  as `numpy.float64` for each parameter in the regression test).

| Item | Value |
|---|---|
| Brief | `docs/briefs/wp3.2-brief.md` (FINAL). Spec v0.5.4, architecture FINAL 1.0. |
| Base SHA | `2c5540a` |
| Author heads | `dfe65d5` (code `1fcb37d`; Reviewer A terminated at R1); `4b87fd8` (the ONE Reviewer B remediation: `2a1e3eb`, `03a0527`, `e580582`, `97ff0c3`, `dd47065`, ledger `b6668ca`, `736c581`, `0576b1e`, `4b87fd8`). |
| Cells and depth | **`wp32-cell`** (implementer-opus-high): 116,822 at the R0 yield; 218,176 at the R1 yield; 241,447 at the window yield; ended at a clean stop at the orchestrator's generation-6 rollover. **`wp32-rem`** (implementer-sonnet-high, the Reviewer B remediation on the same branch): 84,562 / 26 turns at its first return; 109,633 / 43 turns at its last return (retired). |
| Merged head | `wp3.2-mc2` = `4b87fd8` rebased onto `wp3.5-mc2` `80c1a12` (`8e66cbf`), then onto main after the WP3.5 accept, plus this record, the report erratum and DR-40; main fast-forwarded to the commit that adds this record. Reviewer B pass 1 ran on `wp3.2-mc` `4e56916` (the pre-remediation candidate on main `7b9fc6c`); the re-run on `8e66cbf`. CHARC held main. |
| Byte identity | `git patch-id --stable`: pre-remediation `d75d99d4d3f9...` on `2c5540a..dfe65d5` and on `7b9fc6c..4e56916`; final `0f9c0e0aac39...` on `2c5540a..4b87fd8`, on `80c1a12..8e66cbf` and on the final range. |
| Gates on the candidate | `ruff check` clean; `ruff format --check` 121 files; `mypy` strict 76 sources clean (on `8e66cbf`). Full pytest on the final stack top `8e66cbf` (all three packages): **2904 passed, 1 skipped, 1 warning (CuPy CUDA_PATH), 885 s, exit 0** (basetemp `work/pt-mc-normal`); with `cupy` and `cupyx` unimportable **2386 passed, 519 skipped, 585 s, exit 0** (basetemp `work/pt-mc-nocupy`). 2904 = main's 1844 + WP3.3's 389 + WP3.5's 120 (+1 skip) + WP3.2's 551. Earlier: on `b028fd0` (pre-remediation WP3.2 + WP3.3) 2616 passed, 693 s, exit 0. The cell's own runs: 2227 passed; 1938 passed / 289 skipped with CuPy unimportable (on `1fcb37d`); after the remediation, own tests 551 passed, and 308 passed / 243 skipped with CuPy unimportable (on `4b87fd8`). |
| Gates on main | Main fast-forwarded to `4b4da9b` (WP3.3 `09d1d11`, WP3.5 `55c266d`, WP3.2 `4b4da9b`); `uv sync`; `ruff check` clean; `ruff format --check` 121 files; `mypy` strict 76 sources clean; harness gate 366 OK (1 skipped); **full pytest 2904 passed, 1 skipped, 1 warning (CuPy CUDA_PATH), 812 s, exit 0** (basetemp `work/pt-main-wave2a`). This is the main gate for all three packages of the stack. |
| Reviewer A | gpt-5.6-sol / high, WSL, codex-cli 0.162.1. R1 on `bda5397`: 0 critical, 0 major, 4 minor (mixed-type keys, an overflowing derived sigma, two test gaps), fixed as the terminating cleanup (`da2693c`, `e4a0b55`, `5da9a91`). One `Reconnecting... 2/5` before the model's first output: a recovered retry. Terminated at R1. Evidence `clearwater-review-evidence\wp3.2\r1`. Ledger `docs/proofs/wp3.2-ledger.md`. |
| Reviewer B | Pass 1 on `4e56916`: `NEW_CRITICAL_MAJOR_FOUND` (1 major, 1 minor, 1 advisory), with ONE remediation (`4b87fd8`). Re-run on `8e66cbf`: `NO_NEW_CRITICAL_MAJOR` (1 minor, 1 advisory). |
| Witness | At this seat: pass-1 finding B-1 reproduced by execution on `4e56916` (`np.float64` parameters to `compensate_c3`: a float64 `add` intermediate, output 5.96e-08 from the Python-float call); on the final stack top the D99 clamp binds as specified (gray-world gains (300.3, 0.601, 0.751) applied (3.0, 0.601, 0.751), clamped (True, False, False)). |

## The package

`src/clearwater/methods/compensation.py`, `src/clearwater/methods/white_balance.py`,
`tests/test_methods_compensation.py`, `tests/test_methods_white_balance.py`; report
`docs/reports/wp3.2-compensation-white-balance.md`. No dependency, no interface change,
nothing in `clearwater.core` changed. Step functions (X-1): `cap_statistics` (MEASURE),
`effective_alphas` (closed form; red and blue caps separate, D52; None disables, D100 / AD-26),
`compensate_ancuti2018` (RENDER from supplied means and alphas), `compensate_c3` (RENDER; BT.709
full YCbCr whatever the source, D47; mask, kernels size-relative; no cap, D49),
`gray_world_gains`, `applied_gains` (closed form; the D99 clamp after the strength, with the
clamped flags), `apply_white_balance` (RENDER). 54 / 54 per-function rows bit-identical to the
prototype on CPU and GPU; CPU against GPU worst 3.58e-07 max / 6.44e-08 mean (3C). Every scalar
parameter is converted to a Python float before arithmetic (the remediation). X-4 (DR-19 items
1-2) in the report's "DR-19 rule" section, rule text identical to WP3.3's.

## Reviewer B

**Pass 1** on `4e56916`: `clearwater-review-evidence\wp3.2\reviewB\review-B.txt` (md5
`2a54758c7f6f3d3cbab8daf45eb41a45`; all md5s in `md5s.txt`). Assertions: banner gpt-5.6-sol /
high; `^ERROR` 0; `tokens used` present; 17 `succeeded in`; VERDICT anchored; withheld paths
appear only in exclusion globs. Findings:
- B-1 MAJOR in envelope (REASONED by B, CONFIRMED by execution at this seat): `compensate_c3`
  multiplied `kappa`, `lambda_`, `c3_strength` as given, so NumPy-float64 parameters made float64
  intermediates and a different float32 result; the remediation also found an `np.float64`
  `c3_mask_threshold` changing which pixels the mask protects (0.128 difference). Introduced by
  this package -> ONE remediation: `float(...)` on every scalar parameter of `compensate_c3`
  (2a1e3eb), of the two fractions in `_derived_sigma` (97ff0c3), of `applied_gains` and
  `effective_alphas` (dd47065, the same defect class found by the cell's audit); tests pass each
  parameter as `np.float64`, `np.float32` and a Python int, each failing on the unfixed code
  where the defect shows (6, 12 and 5 failing-before cases; the rest regression cases).
- B-2 MINOR: the report's V9 sentence claimed bit identity on every input; a `-0.0` input may
  return `+0.0`. Fixed in the report (03a0527).
- B-3 ADVISORY: no 10-bit-grid V1 input. Added to both test files (e580582).

**Re-run** on `8e66cbf`: `clearwater-review-evidence\wp3.2\reviewB2\review-B.txt` (md5
`767340a746e23adb3d5439ab6ec2d1d5`; `md5s.txt`). Assertions: banner gpt-5.6-sol / high;
`^ERROR` 0; `tokens used` present; 16 `succeeded in`; VERDICT anchored; withheld paths only in
exclusion globs. B-1..B-3 verified present. `VERDICT: NO_NEW_CRITICAL_MAJOR`. Dispositions:
- (1) MINOR (EXECUTED): the report's "own tests 383" gate line is stale after the remediation
  (551 now). ERRATUM.
- (2) ADVISORY: the remediation test cannot detect removal of the early `float(alpha)` alone
  (its caps bind, so alpha never reaches the result). BANKED DR-40 (a).

## Erratum at the gate

Appended to the report: after the Reviewer B remediation the own tests are 551 passed with CuPy
importable and 308 passed / 243 skipped with `cupy` and `cupyx` unimportable (on `4b87fd8`); the
earlier "383" line describes `1fcb37d`.

## Debt

- **DR-19** stays OPEN (WP3.4's schema); this package discharged items (1) and (2) for its
  parameters and (5) for its steps.
- **DR-38 (d)** (the `check_sigma` OverflowError root in the core) is recorded at the WP3.3
  accept; WP3.2 converts it (R1-2).
- **DR-40** NEW: (a) above; (b) N-1 of the round-0 table: `compensate_c3` uploads the 3x3
  inverse and `apply_white_balance` the three gains on every call (no `CoreBackend.constant`);
  trigger: WP3.4's whole-core speed row or WP3.21.
