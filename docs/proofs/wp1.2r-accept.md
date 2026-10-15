# WP1.2R — Accept record (prototype remediation, retroactive Reviewer B)

**Accepted 2026-10-15 by the orchestrator** (session `clearwater-orchestrator-20261014-1258`),
on CHARC's confirmation `2b3066dac88ed847`. Gate per `docs/review-gate-clearwater.md` Part 2
(corrected `30483f2`). This package closes the retroactive seat-run Reviewer B over
`tools/prototype` (WP1.1 + WP1.2A); see the addenda to `wp1.1-accept.md` and
`wp1.2-accept.md`.

| Item | Value |
|---|---|
| Brief | `docs/briefs/wp1.2r-brief.md` (FINAL `fb36e00`). |
| Base SHA | `fb36e00` |
| Author head | `5dc578e` (branch `wp1.2r`, implementer-sonnet-high; depth 219K at return) |
| Merged head | `996274e` (`wp1.2r-mc` = `wp1.2r` rebased onto main `42b0d61`; main fast-forwarded). CHARC's spec v0.5.2 commit `9042ae0` (text only) landed on top afterwards. |
| Byte identity | `git patch-id --stable` = `8aa61b19e5d9546c6450800ce830c1d74b5ee2d2` before (`fb36e00..5dc578e`), on the reviewed candidate (`5b4551b..a68ed93`) and after (`42b0d61..996274e`). The two candidates differ only in their base: one state-pointer commit (`docs/orchestrator-state.md`). |
| Reviewer A | Codex STRONG (gpt-5.6-sol / high), WSL, codex-cli 0.162.1. One round, as the brief ordered. r1 on `6aa7337`: `NEW_CRITICAL_MAJOR_FOUND`, 1 major + 1 minor + 3 advisories. The major was a finite sigma (~5e307) that passed the new check and then overflowed SciPy, the same class as M2. It was fixed in `cecf973` with the 2**23 px support bound; the minor and advisories were fixed too. No round 2 (by the brief), so `cecf973` was first reviewed by Reviewer B. Ledger `docs/proofs/wp1.2r-ledger.md`; evidence `clearwater-review-evidence\wp1.2r\r1\`. |
| Reviewer B | The orchestrator's own pass, on candidate `a68ed93`. Evidence `C:\Users\rwsmy\clearwater-review-evidence\prototype-retroB\rerun\`. See below. |

## Findings closed (from the retroactive Reviewer B)

| # | Fix | Covering test (fails on the pre-fix code) |
|---|---|---|
| M1 | `_probe_gpu` catches any exception at `import cupy`, logs the reason verbatim and falls back to the CPU. | `test_auto_falls_back_when_cupy_fails_to_initialise` (OSError, RuntimeError) |
| M2 | `Params` rejects controls beyond float32 range, and the products `c3_strength*kappa`, `c3_strength*lambda_` and `2*weight_delta`, naming the field. `check_derived_values()` rejects a non-finite or non-positive spatial sigma, or a 4-sigma support beyond 2**23 px. It is called at the top of `correct()` and by `run.py` before `correct()` (exit 2, one line). | the derived-value tests through `check_derived_values`, `correct()` and `run.main` |
| M3 | Implements CHARC's ruling (option (a)). The float64 accumulators sit in one `xp`-generic helper `_accumulate_mean`, used by `_cap_statistic`, `_channel_means` and `_lab_mean`. Every result is cast before it touches image data. The cell's sweep found one more site: `xp.percentile` in `_high_pass_and_bounds` interpolates in float64 on both NumPy and CuPy and returns Python floats; this is documented. The interpretation note is in `wp1.1-open-values.md`. | `assert_scalar_reductions_use_float64` on the CPU and under `gpu`; it fails with a float32 accumulator and with the cap statistic inlined |
| m5 | The report column becomes "Peak RSS (sampled at 50 ms)", with a note on the 4.2/5.4/9.4 MiB gap to the OS peak; the contradicting "agrees" wording is fixed. No figure changed. | — (report) |
| m7 | The blue gain cap (D52) binds independently of the red cap. | `test_blue_gain_cap_binds_independently_of_the_red_cap`; it fails on both mutants |

- **Tests are additions only:** `git diff --stat fb36e00..5dc578e` over the two test files shows +41 and +195, with 0 lines removed (checked at this seat).
- **Deviation, ACCEPTED at this seat.** `pipeline.py` gained a behavioural line, the `check_derived_values` call in `correct()`, beyond "docstrings plus a no-behaviour hook". The brief's own M2 test required `correct()` to raise, so the file restriction I wrote was too narrow. The line affects only invalid input; the bit-identity witness below shows valid outputs unchanged.

## Reviewer B (orchestrator seat), on candidate `a68ed93`

Assertions:
- the banner reads gpt-5.6-sol / high;
- `^ERROR` 0;
- footer 1;
- 31 `succeeded in` lines;
- an anchored `VERDICT: NEW_CRITICAL_MAJOR_FOUND`.

`ERROR codex_core` hits:
- three echoes of brief and doc text;
- one genuine `codex_core::tools::router` line: Codex's sandbox policy rejected an `rm -f` in its own scratch command. That is a tool-policy line, not a transport or content-filter line, so the pass is not disqualified.

Accesses: `rg` with `!docs/proofs/**` globs, and git metadata under `.git/worktrees/`. Neither read a withheld file. The pass is valid.

md5s:

| File | md5 |
|---|---|
| prompt | `a6cea61d00d53c6535241f4c6b8a4046` |
| diff | `9987d4e706d5fc1e47d6902b0c2c9e44` |
| transcript | `f1cc6cf8ae3da62a1b3765573320e7b7` |
| stderr | `9647729a93015a524a5cf4fe4bfb8dde` |

| # | Finding | Disposition |
|---|---|---|
| 1 | MAJOR, reasoned: `check_derived_values` validates the C3 fractions on an Ancuti run, so `c3_kernel_fraction=1e6` now rejects an Ancuti run that used to ignore it. | **This is the second blocking B, so it is adjudicated at the gate by irreversibility. NOT BLOCKING; ACCEPTED.** The `Params` contract has always validated every field whatever the method: the base already rejected `c3_kernel_fraction <= 0` under `ancuti2018` (`fb36e00:tools/prototype/params.py`). Rejecting an unusable C3 value follows that convention; it does not reject valid input. It fails safe (a named one-line error, never a wrong image), it is reversible, and it is prototype-only. Recorded in **DR-19(1)**. |
| 2 | minor: a profile or precision note can precede the one-line error. | BANKED, DR-19(2). |
| 3 | minor: the support-bound boundary differs from SciPy's rounding by up to half a pixel. | BANKED, DR-19(3). |
| 4 | minor: `_check_image` `min`/`max` are absent from the M3 note; the percentile dtype is asserted only at the output. | BANKED, DR-19(4). `min`/`max` are exact operations with no accumulation, so the ruling's intent is unaffected. |
| 5 | minor: new tests pass named wrong implementations. | BANKED, DR-19(5); the list is in the transcript. |

Also confirmed by B: the tests are additions only; the RSS gaps and rows agree with the JSON; M1 catches `Exception`; m7's mutants are caught.

## Verification QA (orchestrator seat)

**Gate checks**, on candidate `a68ed93` and again on main `996274e` after `uv sync`:

```
uv run ruff check .            -> All checks passed!
uv run ruff format --check .   -> 64 files already formatted
uv run mypy                    -> Success: no issues found in 13 source files
uv run pytest -q -rs           -> 443 passed, 1 warning (0 skipped)
uv run pytest -q -m gpu        -> 20 passed, 423 deselected
python -m unittest discover -s tests/harness -> Ran 366 tests ... OK (skipped=1)
```

**Witness: the arithmetic is unchanged.**
- The input is a fixed 900x600 textured synthetic image (seed 12345).
- `correct()` ran from main's `tools/prototype` (`5b4551b`) and from the candidate's (`a68ed93`; import path confirmed as the candidate's, `check_derived_values` present).
- Cases: Ancuti 2018 with blue compensation off and on, and 3C; each on the CPU and on the GPU.
- The `output` is **bit-identical** in all six cases.
- Script: `scratchpad\witness_r.py`; outputs `w_main.npz` and `w_cand.npz` (session scratchpad).

**Locks:**
- Only owned files changed.
- `bench.py`, `pyproject.toml`, `uv.lock` and `src/` are untouched.
- No footage writes.
