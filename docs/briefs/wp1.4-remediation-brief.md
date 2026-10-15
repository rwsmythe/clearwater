# WP1.4 — Remediation brief (Reviewer B round 1)

**Issued by the orchestrator 2026-10-15.** This is the ONE bounded remediation that
`docs/review-gate-clearwater.md` Part 2 item 2 allows after a blocking Reviewer B. The author
cell is near its context cap (384K), so a fresh cell carries the author's loop forward on the
same branch.

**Read first:**
- the package brief, `docs/briefs/wp1.4-brief.md` (FINAL), with both "Decisions fixed at issue"
  blocks;
- the report as it stands, `docs/reports/wp1.4-statistics.md`;
- the ledger, `docs/proofs/wp1.4-ledger.md`;
- the spec, v0.5.2: 7.1-7.3, D97, D98.

| Field | Content |
|---|---|
| Worktree | `C:\Users\rwsmy\clearwater\.worktrees\wp1.4`, branch `wp1.4`, head `63d8422`. It holds a copied `clearwater.local.toml` (gitignored; never edit or commit it). |
| Files owned | The same six as the brief: `tools/prototype/temporal.py`, `tools/prototype/pipeline.py` (the additive hook ONLY), `tools/statistics_experiments.py`, `tests/test_prototype_temporal.py`, `docs/reports/wp1.4-statistics.md`, `docs/proofs/wp1.4-ledger.md`. Nothing else; `tools/lookcheck/` stays untouched. |
| Outputs | `C:\Users\rwsmy\clearwater\work\wp1.4\` only. The footage folder is READ-ONLY. |
| PATH | Prepend `/c/Users/rwsmy/AppData/Local/Microsoft/WinGet/Links` for every ffmpeg, ffprobe and pytest run. |
| Reviewer B evidence | `C:\Users\rwsmy\clearwater-review-evidence\wp1.4\reviewB\review-B.txt`. You may read it. |

## Findings to close (adjudicated at the gate seat)

| # | Reviewer B finding | Disposition: what to do |
|---|---|---|
| 1 | MAJOR (executed): the white-balance channel MEANS (claim 1, "white-balance means and gains") are not recorded; only the gains are. | **Fix.** Record the white-balance means per frame in the raw, staged and flat records, and the proxy-versus-full gap for them. They are RECORDED statistics; whether the hook also accepts them is your choice (a gain derives from them), but the hook's identity guarantee must hold either way. Re-run the analysis so the records carry them (see "Then"). |
| 2 | MAJOR: `clipped_fraction()` divides clipped SAMPLES by 3HW; the brief asks for the fraction of PIXELS clipped. | **Fix.** Report the pixel fraction (a pixel counts as clipped if any channel is clipped). Keep the per-sample fraction as a second, clearly named column if you want it. Correct the report's wording and every robust-table number from the re-run records. |
| 3 | MAJOR: `unflatten()` accepts a known prefix with an unknown suffix (`compensation_alpha.green`, an extra `white_balance_gains.X`) and silently drops it, so the pipeline measures its own value instead. | **Fix.** Refuse every name `flatten()` cannot produce, naming it. Tests: the two concrete inputs above each raise. |
| 4 | MAJOR: persisted series are applied by LIST POSITION. A reordered or stale record renders the wrong statistics, and the encode verification and read-back still pass. | **Fix.** Before analysing or rendering, check that each record's `pts_ticks` sequence equals the excerpt's, in order; refuse on any mismatch. Test: a record with its entries reversed (keeping their ticks) is refused. |
| 5 | MINOR: non-finite or impossible supplied values (`NaN` gains, reversed or NaN N{} bounds) are not refused. | **Fix.** The hook refuses a non-finite supplied value and `low > high` bounds, naming the field. Tests. |
| 6 | MINOR: the real-footage identity witness records `identical: false` or `missing: true` and carries on. | **Fix.** A witness that is missing or not identical FAILS the render step before any deletion. |
| 7 | MINOR (executed): the "edge-free" interior margin for `median_gaussian 4 s` is one frame too narrow (effective radius 60, margin 59). | **Fix.** The interior margin uses the effective radius of the whole filter chain. Recompute the interior columns from the records and correct the report. |
| 8 | MINOR (executed): smoothing prose misstates the records (4 of 32 reversals, not 2; largest gap 0.00156, not within 0.0015; the GX011625 ranking). | **Fix the text** from the records. |
| 9 | MINOR (executed): `source_referenced` is not recorded for the smoothing-candidate sequences. | **Fix:** record it for every sequence, or correct the report's "every sequence". Your choice; say which. |
| 10 | ADVISORY: tests admit wrong implementations. | **Add the cheap ones:** a blue-on positive control for the supplied blue alpha; value-level checks that fusion and C3 receive the SUPPLIED earlier-stage values; a proxy test over every block, not `[0,0]`. The rest is optional; list what you did not add. |
| 11 | ADVISORY: a 1-frame excerpt fails late. | **Fix:** refuse fewer than 2 frames up front (3 for an interior result), naming the minimum. |
| 12 | ADVISORY, out of envelope: VFR timing is not used by smoothing. | **No code.** One sentence in the limits; banked by the orchestrator. |

## Then

1. **Re-run the runner on both excerpts.**
   - First keep copies of the current JSON records in `work\wp1.4\logs\before-remediation\`.
   - The analysis and the robust study MUST be re-run (findings 1, 2, 7).
   - Re-render the three CP2 clips only if your change touches the render path's inputs. If you
     do, the existing clips must come out byte-identical (same md5); say which you did.
   - **Every number that is not meant to change must equal the kept copy:** the
     staged/flat/unsmoothed statistics, mismatch, flicker and render figures. Report the
     comparison.
2. **Report:** update every table and sentence the findings touch. Fill the ledger's
   context-depth column for the author cell (`wp14-cell`: 384K at return).
3. **Gates:**
   - `uv run ruff check .`
   - `uv run ruff format --check .`
   - `uv run mypy`
   - `uv run pytest -q -rs` (0 skipped; `footage` and `gpu` RUN)
   - `uv run pytest -q -m gpu`
4. **ONE Reviewer A round** on the delta `63d8422..HEAD`, per the brief's Review loop:
   - tier STRONG; WSL; codex-cli 0.162.1;
   - flags `-m gpt-5.6-sol -c model_reasoning_effort=high -s read-only --skip-git-repo-check`;
   - probe first; the diff Windows-side, excluding `uv.lock` and `docs/proofs`;
   - the withheld paths named, and the EXECUTED/REASONED paragraph verbatim;
   - the six assertions.

   Fix minors once. Append round 2 to the ledger; evidence to
   `C:\Users\rwsmy\clearwater-review-evidence\wp1.4\r2\` with md5s. A new critical or major
   found in this round is FIXED if this remediation introduced it; otherwise report it.
5. **Commit** by pathspec (`fix(wp1.4): ...`, `docs(wp1.4): ...`), with `Co-Authored-By:` naming
   the model you actually run as. Never `git stash`.

## STOP for

- any change to `correct()` beyond the additive hook;
- any change in the default path (`statistics=None`): my witness re-runs it bit for bit;
- a statistic, figure or clip that changes when it should not;
- any output outside `work\wp1.4\`;
- any dependency change.

## Return (your FINAL message, under about 60 lines)

- the new head and a per-commit list;
- each finding with what was done and the test that covers it;
- the records comparison (what changed, what stayed identical);
- the gate lines;
- round 2's result with its assertions;
- the locks.

**Working rules:** never use a bare `cd`; never post to a mailbox.
