# WP1.1 — Accept record

**Accepted 2026-10-15 by the orchestrator** (session `clearwater-orchestrator-20261014-1258`),
on CHARC's commission `3f7c2f997b58c6d5`. Gate per `docs/review-gate-clearwater.md` Part 2.

| Item | Value |
|---|---|
| Brief | `docs/briefs/wp1.1-brief.md` (FINAL at `46a10b9`, amended `c9e7b58` on CHARC ruling `b24ccecab030aad9`); CHARC return rulings `ad686b8b65a71061` |
| Base SHA | `46a10b9` |
| Author head | `67e4789` (branch `wp1.1`, implementer-opus-high; depth 267K at first return) |
| Merged head | `9711faf` (branch `wp1.1-mc` = `wp1.1` rebased onto main `c8e5383`; main fast-forwarded) |
| Byte identity | `git patch-id --stable` = `2d285542c9c0cbbf5d3ea5e91a83aa4dda6ba8a3` before (46a10b9..67e4789) and after (c8e5383..9711faf) |
| Merge integration | Main's intervening commits are docs only (briefs, state pointers, `docs/debt-register.md` DR-11/DR-12); no file overlap with the arc; both gate surfaces ran on the merged head |
| Reviewer A | Codex STRONG tier (gpt-5.6-sol / high), WSL, codex-cli 0.162.1. r1 BLOCKING 0/4/2, r2 BLOCKING 0/1/5 (the major = Laplacian form, later ruled), r3 NO_NEW_CRITICAL_MAJOR 0/0/4 (converged). Ledger `docs/proofs/wp1.1-ledger.md`; the depth column is dispatcher-read and recorded here. |
| Reviewer B | Independent implementer-opus-high cell, brief `docs/briefs/wp1.1-review-brief.md`; depth 158K after pass 1. See the passes below. |
| Evidence | `C:\Users\rwsmy\clearwater-review-evidence\wp1.1\` — `probe`, `r1`–`r3`, `analysis` (A); `B`, `B2`, `B3` (B) |

**Reviewer B passes**

- **Pass 1** on `8e149db`: **NO_BLOCKING**.
  - All six claims pass.
  - Every step was checked against an independent float64 re-derivation (max diff ~1e-7).
  - The 3C correspondence was reproduced.
  - Two minors:
    - F1: no test pinned N{}'s single stretch across channels.
    - F2: stale 2x figures.
  - Its Codex leg read the withheld ledger (prompt omission), so that leg was not counted.
  - Author cleanup `48a1f7f`.
- **B2** on `48a1f7f`: **NO_BLOCKING**.
  - F1 and F2 resolved by reproduction; F1's new test kills the per-channel mutant.
  - Fresh Codex pass with an explicit withheld paragraph: 0 accesses in 39 `docs/proofs|wp1.1-ledger` hits. Prompt md5 `49930988c01d405f8f2556ed3fee7904`, transcript md5 `c42652fc50fc045796a4659cb59f789f`.
  - One new minor, F3: `c3_mask_threshold` was unbounded (-1 silently disabled 3C). Author fix `67e4789`.
- **B3** on `67e4789`: **NO_BLOCKING**.
  - F3 resolved: -1 and 2 exit 2; 0, 0.85 and 1 are accepted.
  - The new cases fail on an unfixed copy.

## Gate checks (orchestrator seat, merged head `9711faf`, main tree)

```
uv run ruff check .            -> All checks passed!
uv run ruff format --check .   -> 43 files already formatted
uv run mypy                    -> Success: no issues found in 8 source files
uv run pytest -q -rs           -> 280 passed, 1 skipped in 9.27s
   SKIPPED [1] tests\test_inventory.py:1125: footage folder not configured; ...  (footage folder absent)
python -m unittest discover -s tests/harness -> Ran 366 tests ... OK (skipped=1)
```

The same five gates were also green on the merge candidate before the fast-forward.

- **Locks** (verified by B, re-checked here):
  - The arc touches only owned files, and nothing under `src/`.
  - `pyproject.toml` changes are the `numpy>=2.1,<3` and `scipy>=1.14,<2` dev grants plus one mypy override naming `scipy`.
  - `uv.lock` adds only numpy and scipy.
  - There are no imports of `local_config`, `inventory` or `environment_report`, and none of OpenCV, scikit-image, CuPy or PyTorch.
  - The only `sys.path` change is the `__package__`-guarded bootstrap in `run.py`.
- **Witness (orchestrator reality check on main):** a synthetic 900x600 blue-green image (input channel means R 0.114, G 0.483, B 0.53).
  - `run.py --method ancuti2018` and `--method c3` each exit 0.
  - Each writes a PNG whose IHDR reads bit depth 16, colour type 2, 900x600.
  - Decoded means over the top rows are balanced: ancuti2018 R 0.30 / G 0.26 / B 0.36, c3 R 0.29 / G 0.28 / B 0.31.
  - `--set c3_mask_threshold=2` exits 2 with a one-line error.
- **Informal 4K run** (CHARC `b24ccecab030aad9`; INFORMAL, never a result):
  - 3840x2160 synthetic frame; both methods exit 0 with 16-bit output.
  - The pyramid is 8 levels, with a 17 px coarsest short side.
  - Wall clock was about 14 s (ancuti2018) and 26 s (c3) for the whole command.
- **Reports:** `docs/reports/wp1.1-open-values.md` and `docs/reports/wp1.1-3c-correspondence.md`.
  - The open-values report carries the three CHARC-required records: the Laplacian ruling, the `weight_maps` signature, and the thumbnail stated floor.
  - The correspondence report confirms kappa -> Cr and lambda -> Cb.

## Dispositions

| Item | Disposition |
|---|---|
| Laplacian contrast weight `|sigma^2 Lap(G_sigma * L)|` vs [A18]'s per-pixel form | RULED ACCEPTED by CHARC (`ad686b8b65a71061`), spec-driven departure (6.6 / D56); recorded in the open-values report |
| 16-bit RGB read at 8-bit precision; HEIC unreadable (Pillow-only grant) | BANKED DR-11 (CHARC; trigger WP1.3/WP1.4 commissioning). Codex raised it as major in B and B2; B rejected it as new blocking on that ground |
| [3C] mask kernel size 20 (cited by Codex, unverified) | BANKED DR-12 (trigger WP1.3 tuning) |
| B: at the default `laplacian_fraction` 0.001, W_L is ~1% of the aggregated weight on textured content (W_S ~0.08, W_Sat ~0.19); it equals the paper's form only near a 1000 px short side, so the contrast term is nearly inert | RAISED to CHARC as a WP1.3 calibration point (not an implementation defect) |
| Resolution independence at the defaults is not claimed at or below a 128 px short side (64–128 px: p99 0.06–0.07 at 2x) | Stated floor in the open-values report; WP1.3 preview sizing stays above it |
| `weight_maps` takes all fusion inputs (brief: one) | Accepted brief-interface deviation (CHARC note; prototype interfaces not frozen); recorded in the open-values report |
| `run.py` has no `# noqa: E402` (brief asked for it) | Accepted: ruff exempts imports after a `sys.path` change and would flag the suppression (RUF100); a comment explains it |
| Additive: EXIF orientation, alpha drop, 16-bit grayscale read, `Params` validation, extra `Result`/`Weights` fields, `weights.json` | Accepted; checked against the brief by B |
| B pass 1 Codex leg saw the withheld ledger | Process gap in my review brief (the Codex prompt must name withheld paths); B2 re-ran it clean. Fix carried into future review briefs |
