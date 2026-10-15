# WP1.2R -- cumulative round ledger (Reviewer A)

Brief: `docs/briefs/wp1.2r-brief.md` (base `fb36e00`). Tier STRONG. Transport WSL, codex-cli 0.162.1,
`-m gpt-5.6-sol -c model_reasoning_effort=high -s read-only --skip-git-repo-check`. Evidence (outside every repo):
`C:\Users\rwsmy\clearwater-review-evidence\wp1.2r\r1\` (prompt, diff, transcript `review.txt` and `review.stderr.txt`,
adjudication, md5s in `md5s.txt`).

| Round | Candidate head | Critical | Major | Minor | Advisory | In-envelope / out | NEW / REOPENED | Reverts | Fixes changed | Context depth |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `6aa7337` | 0 | 1 | 1 | 3 | 5 / 0 | 5 NEW / 0 | 0 | product code (findings 1, 2) and tests (3, 4a, 4b) | (dispatcher) |

Round 1 assertions: banner `gpt-5.6-sol` / `high` PASS; `^ERROR` 0 and `ERROR codex_core` 0 PASS; `^tokens used` 1 PASS;
anchored `VERDICT: NEW_CRITICAL_MAJOR_FOUND` PASS; `^ succeeded in` 20 PASS; `docs/proofs|wp1.2r-ledger` 2 hits, both
the echoed prompt (pathspec and WITHHELD paragraph), no read PASS.

Findings and dispositions (full text in the evidence folder):

1. MAJOR in-envelope REASONED: a finite sigma of about 5e307 (129x129, `sharpen_blur_fraction=4e305`) passes
   `check_derived_values` and overflows SciPy's `int(4 * sigma + 0.5)`; uncaught by `run.main`. Confirmed (base:
   `OverflowError`). Fixed in `cecf973`: filter support beyond 2**23 px is rejected, naming the parameter.
2. MINOR in-envelope EXECUTED: `Params(gamma=10**400)` raised `OverflowError`. Fixed in `cecf973`.
3. ADVISORY: the M3 test would not catch an inline cap statistic. Confirmed by mutation; fixed (test).
4. ADVISORY: M1 covered `OSError` only; `sharpen_strength` range untested. Fixed (tests).

One round only, per the brief; no second round was run on the fix commit.
