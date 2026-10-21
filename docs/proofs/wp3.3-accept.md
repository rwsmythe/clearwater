# WP3.3 — Accept record (fusion inputs, weights and multiscale blending: `clearwater.methods.fusion`)

**Accepted 2026-10-21 by the orchestrator** (generation 7, session
`clearwater-orchestrator-20261020-1419`). Gate per `docs/review-gate-clearwater.md` Part 2.
Tier STRONG. Wave 2, tranche A; stacked gate with WP3.5 and WP3.2 (this package merges first).
- Brief approval and rulings: CHARC `53b752a4d7fac4fc` (ruling 3.1, the floor form: symmetric
  widening about the midpoint to a range of 0.02; X-1..X-4). Round-0, round-1 and round-2
  rulings: orchestrator generation 6 (in the ledger).

| Item | Value |
|---|---|
| Brief | `docs/briefs/wp3.3-brief.md` (FINAL). Spec v0.5.4, architecture FINAL 1.0, AD-4 as amended 2026-10-20. |
| Base SHA | `2c5540a` |
| Author head | `b6c47db` (code `d8532dd`; Reviewer A converged at R2; terminating cleanup `4e2e836`). No Reviewer B remediation. |
| Cell and depth | **`wp33-cell`** (implementer-opus-high): 119,733 at the R0 yield; 257,103 at the R1 yield (the ~250K evaluation point; continued: one bounded remediation and one round left); 304,760 at the R2 yield (terminating cleanup, gates and report only remained). Ended at a clean stop at the orchestrator's generation-6 rollover. |
| Merged head | `wp3.3-mc2` = `b6c47db` rebased onto main `7b9fc6c` (`f9f1ae1`), plus this record, the report erratum and DR-38; main fast-forwarded to the commit that adds this record. The first stack built it on WP3.2's candidate (`wp3.3-mc` `b028fd0`, where Reviewer B ran); WP3.2 then took a Reviewer B remediation, so the stack was re-ordered WP3.3 -> WP3.5 -> WP3.2. The package's files are byte-identical in both trees (`git diff wp3.3-mc wp3.3-mc2 -- <owned paths>` empty). CHARC held main. |
| Byte identity | `git patch-id --stable` = `3aeed691cfc8...` on `2c5540a..b6c47db`, on `4e56916..b028fd0` (the B tree), on `7b9fc6c..f9f1ae1` (the merge candidate) and on the final range. |
| Gates on the candidate | `ruff check` clean; `ruff format --check` clean; `mypy` strict clean (on every stack top: 113 files / 73 sources on `b028fd0`, 117 / 74 on `80c1a12`, 121 / 76 on `8e66cbf`). Full pytest: on the first stack top `b028fd0` (WP3.2 + WP3.3) **2616 passed, 1 warning (CuPy CUDA_PATH), 693 s, exit 0**; on `80c1a12` (WP3.3 + WP3.5) **2353 passed, 1 skipped (WP3.5's deliberate yuvj plant), 892 s, exit 0**; on the final stack top `8e66cbf` (all three) **2904 passed, 1 skipped, 1 warning (CuPy CUDA_PATH), 885 s, exit 0** (basetemp `work/pt-mc-normal` in `.worktrees/wp3.2-mc2`); with `cupy` and `cupyx` unimportable (`sys.modules[...] = None`, then `pytest.main`) **2386 passed, 519 skipped, 585 s, exit 0** (basetemp `work/pt-mc-nocupy`). 2904 = main's 1844 + WP3.3's 389 + WP3.5's 120 (+1 skip) + WP3.2's 551. The cell's own final-head runs on `d8532dd`: 2233 passed; 1958 passed / 275 skipped with CuPy unimportable. |
| Gates on main | Recorded in the WP3.2 accept record (`docs/proofs/wp3.2-accept.md`), the last of the stack: the main gates run once on the merged top. |
| Reviewer A | gpt-5.6-sol / high, WSL, codex-cli 0.162.1. R1 on `8643ba1`: 1 major (the CPU/GPU test compared only three outputs while the report claimed every intermediate) and 3 minor, all fixed (be0b145, aa5c003, d637dcc, 66220b0), each test failing on the unfixed code; plus the `check_sigma` OverflowError guard (0f4121f) and a floor-collapse refusal found at remediation (ec5d2e5). R2 on `77110f7`: 1 minor (out of envelope: a huge supplied saliency mean overflows), fixed as the terminating cleanup (4e2e836). Terminated at R2. Evidence `clearwater-review-evidence\wp3.3\r1`, `r2`. Ledger `docs/proofs/wp3.3-ledger.md`. |
| Reviewer B | ONE pass on `b028fd0`: `NO_NEW_CRITICAL_MAJOR` (2 minor, 2 advisory). |
| Witness | At this seat on the final stack top: an exactly flat 0.4 image gives bounds (0, 0) and input 2 = 0.45 everywhere (the floor keeps the prototype's 0.5 stretch); the normalised weights of two inputs sum to 1 within 1.19e-7; two identical inputs fuse back to the input within 3.0e-5/255. |

## The package

`src/clearwater/methods/fusion.py` and `tests/test_methods_fusion.py`,
`tests/test_methods_fusion_prototype.py`; report `docs/reports/wp3.3-fusion.md`. No dependency,
no interface change, nothing in `clearwater.core` changed. Step functions on an IF-2 backend
(backend first, array second, keyword-only parameters without defaults, names = the prototype
`Params` fields): `high_pass`, `normalisation_bounds` (MEASURE: joint 0.5 / 99.5 percentiles,
two floats), `fusion_inputs` (RENDER from supplied bounds, the AD-4 floor by symmetric
widening, `NORMALISATION_RANGE_FLOOR = 0.02`), `saliency_reference` (MEASURE), `laplacian_weight`,
`saliency_weight`, `saturation_weight`, `weight_maps` (normalised maps, `(W + delta) / (sum W +
K delta)`, K = input count), `multiscale_fusion`. Bit-identical to the prototype on the same
device except input 2 under measured bounds (float32 bounds, R0-8; within AD-11, maximum
reported); CPU against GPU within AD-11. X-4 (DR-19 items 1-2) stated in the report's "DR-19
rule" section; its rule text (a)-(d) is word for word WP3.2's (checked at the gate; only the
cross-reference and the per-package application paragraph differ); the X-4 message format and
the OverflowError guard are the same in both modules.

## Reviewer B

ONE pass on `b028fd0`. `clearwater-review-evidence\wp3.3\reviewB\review-B.txt`; md5s in
`md5s.txt` beside it (review-B.txt `c1abd08f62ed154ede8ac3237e3fb9ce`). Assertions: banner
gpt-5.6-sol / high; `^ERROR` 2 lines, `Reconnecting... 2/5` and `3/5` before the model's first
output, followed by a normal run to the verdict: RECOVERED RETRIES (the WP3.15 B2 and WP3.2 R1
adjudication, upheld by CHARC), not disqualifying; `tokens used` footer present; 10
`succeeded in`; VERDICT anchored; every withheld-path mention on a command line is an exclusion
glob (`-g '!docs/proofs/**'`, `-g '!**/clearwater-review-evidence/**'`). No numeric execution
(no NumPy in the sandbox): all REASONED. `VERDICT: NO_NEW_CRITICAL_MAJOR`. Dispositions:
- (1) MINOR in envelope: `sharpen_strength = 0` maps a `-0.0` input to `+0.0`, so the report's
  V9 "bit for bit" holds for values, not for the sign of zero. ERRATUM (no visual effect; the
  prototype does the same).
- (2) MINOR in envelope: the report's Gate 1 claim says "two reads in all"; the two-input
  measure path makes three (one bounds read, one `channel_means` per input). ERRATUM; the test
  checks each read's location, not the per-frame count. BANKED in DR-38 (a) as a test gap for
  WP3.4, which owns the stage order.
- (3) ADVISORY: no direct test of all-black / all-white grey inputs, where every raw weight is
  0 and the regularisation alone gives `1/K`. BANKED DR-38 (b).
- (4) ADVISORY, out of envelope: a `(0, 1, 3)` array passes `check_rgb`; `saliency_reference`
  returns NaNs. BANKED DR-38 (c) (the core's `check_rgb` accepts empty spatial dimensions).

## Erratum at the gate

Appended to the report (section "Erratum at the gate"): claim 6's bit identity is of values (a
`-0.0` input may return `+0.0`); claim 9's "two reads in all" reads "one bounds read and one
`channel_means` read per input, three on the two-input path".

## Debt

- **DR-14 CLOSED** by this accept (AD-4's floor, ruling 3.1; the near-flat 0.0018 case bounded
  to 50x; tests in claims 2-3 of the report).
- **DR-19** stays OPEN (WP3.4's schema); this package discharged items (1) and (2) for its
  parameters, (3) does not recur, (4) is held by the core's input checks and R0-8, (5) by its
  planted-defect tests.
- **DR-13** stays OPEN (record in the report: the W_L share at the default; no recalibration).
- **DR-38** NEW: Reviewer B (2)-(4) above, and (d) the core root of WP3.2 R1-2 / WP3.3 R1:
  `clearwater.core.check_sigma` raises OverflowError (not ValueError) for a finite sigma whose
  `int(4 * sigma + 0.5)` overflows; both packages convert it; trigger: the next package that
  touches `clearwater.core` (WP3.4 or WP3.21).

## Follow-ons

- Consumer notes for WP3.4 and WP3.21 (report "Sync points"): the measure order inside the
  fusion stage (the saliency mean of input 2 depends on that frame's bounds); the double
  high-pass on the measure path; three host reads per frame on the two-input path.
- WP3.11 measures on the stored proxy only (AD-5 as ruled).
