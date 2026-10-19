# WP1.4 -- Reviewer A cumulative round ledger

Cell: implementer (Opus 5.5), worktree `.worktrees/wp1.4`, branch `wp1.4`, base `9ed1a1c`.
Reviewer A: Codex CLI via WSL, codex-cli 0.162.1, per call `-m gpt-5.6-sol -c model_reasoning_effort=high
-s read-only --skip-git-repo-check`, tier STRONG (brief). Run script
`C:\Users\rwsmy\clearwater-review-evidence\wp1.4\run_round.sh` (stdout and stderr split, a done marker
written last). Probe before round 1 through the same invocation: banner v0.162.1 / gpt-5.6-sol / high,
one `^ succeeded in`, `^tokens used` present (`r1\probe-transcript.txt`, `r1\probe.stderr.txt`).
Evidence (outside every repo tree): `C:\Users\rwsmy\clearwater-review-evidence\wp1.4\r1\` (prompt, diff,
transcript stdout and stderr, adjudication, md5sums.txt). The diff was generated Windows-side
(`git -C <worktree> diff -U8 9ed1a1c..HEAD -- . ':!uv.lock' ':!docs/proofs'`).

| Round | Head reviewed | Transport / CLI | Critical | Major | Minor | In envelope | NEW | REOPENED | Reverts | Fix kind | Context depth (dispatcher) | Mechanical assertions | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `82c258b` | WSL / 0.162.1 | 0 | 0 | 7 | 6 of 7 | 7 | 0 | 0 | product (`pipeline.py`: length check of supplied triples) + tests + report text | 384K at return (`wp14-cell`) | banner OK (stderr); `^ERROR` 0; `ERROR codex_core` 0; footer 1; `^ succeeded in` 29; VERDICT anchored; `docs/proofs` hits all echoes or exclusion pathspecs, no withheld access | NO_NEW_CRITICAL_MAJOR |
| 2 (remediation delta `63d8422..865a054`) | `865a054` | WSL / 0.162.1 | 0 | 2 | 3 | 5 of 5 | 5 | 0 | 0 | product (`statistics_experiments.py`: `staged_reach`, mandatory witness) + tests (duplicate helper removed, nested-reach test) + report text | (dispatcher fills; remediation cell `wp14-fix`) | banner OK (stderr 4, 8); `^ERROR` 0 real (one echo of the brief's text); `ERROR codex_core` 0; footer 1; `^ succeeded in` 35; VERDICT anchored; `docs/proofs` hits all echoes, no withheld access | NEW_CRITICAL_MAJOR_FOUND (two majors, both fixed by the cell, no further round: the brief allows one) |

Round 1 summary (full adjudication `r1\adjudication-r1.md`): five report sentences the records made
false or did not support (the default's stability ground had an exception on `GX011625`'s high bound;
"within 3 %" was 4.0 %; the median-versus-Gaussian "third decimal"; the interior margin is 59 frames,
1.97 s, not 2.0 s; "at most one code" in the clips rested on unencoded renders), all fixed in
`451818b`; a positive-control test that did not prove the consuming step (two mutants now fail it),
fixed in `d446698`; and an out-of-envelope missing length check on supplied triples, fixed in
`d446698` because it is inside the hook and cheap.

Convergence: round 1 had zero NEW blocking findings, so the loop terminated (fill Part 1
`ROUND_TERMINATION`); the minors were fixed once in that round's cleanup and opened no round.
FIVE_ROUND_GATE not reached. Gates after the cleanup (`451818b`): ruff check passed; ruff format 82
files formatted; mypy no issues in 18 source files; pytest 540 passed, 0 skipped (footage and GPU run).

## Verification loop (cell's own; suspect -> confirm independently -> fix -> repeat)

| # | Suspected | Confirmed? | How | Disposition |
|---|---|---|---|---|
| 1 | the hook changes the `statistics=None` path | no | base `9ed1a1c` pipeline vs head, 900x600 textured scene (seed 12345), Ancuti blue off and on and 3C, CPU and GPU: `output` bit-identical in all six | none needed (orchestrator re-runs WP1.2R's witness at the gate) |
| 2 | the hook fed the frame's own statistics is not bit-identical on real 4K footage | no | the unsmoothed render's frames 0, 90, 179 against WP1.3's kept frames: largest difference 0 (`render.json` `wp13_witness`) | none needed |
| 3 | the content-cancellation test was tautological (`np.roll` keeps every channel mean) | yes | content change 0.03 levels per step | fixed: crops of a wider scene (1.69 levels per step) |
| 4 | the step test's `t10 = -t90` was wrong for a discrete crossing | yes | 29-tap average: first frame >= 0.1 at -11.5 frames, >= 0.9 at 12.5 | fixed the expectation |
| 5 | the flicker measure counts a wanted drift as flicker | yes | 4 s smoothing leaves 0.08 on `GX011627` | disclosed as a limit; `linear_trend` row added to quantify it |
| 6 | the coefficient of variation of the bounds measures the scene drift, not the jitter | yes | min/max has the lowest CV and the highest step | relative step added; the recommendation rests on it |
| 7 | the staged-versus-flat visibility claim needs a direct image comparison, not statistics only | yes | -- | per-frame render differences added (proxy and full resolution) |
| 8 | report wording ("four times", "61 steps", min/max's smallest range on frame 178) | yes | records | fixed before round 1 |
| 9 | a proxy test with a non-integral factor (junk lines) | yes | would raise | removed before the first run |
| 10 | doubled line counts after a scripted edit | no (CRLF working tree, `core.autocrlf=true`) | `od -c` | none |

Full pass after round 1's cleanup: nothing new.

Commits: `2ecac9a` feat (hook + temporal + tests), `ca06066` feat (runner + test 7), `08bfbdb` feat (drift
floor, render differences, bound step), `3e2652b` feat (report), `82c258b` docs (interior counts),
`d446698` fix (round 1: triples, positive controls), `451818b` docs (round 1: report corrections); this
ledger follows.

## Remediation after the blocking Reviewer B round 1 (cell `wp14-fix`, 2026-10-15 to 2026-10-18)

Brief `docs/briefs/wp1.4-remediation-brief.md` (twelve findings, adjudicated at the gate seat). Commits `5c6f340` (code and
tests: findings 1-7, 9-11), `865a054` (report), and the round-2 fix commit that follows. Records re-run on both excerpts;
comparison against the kept copies in `work\wp1.4\logs\before-remediation\`: every pre-existing statistic, mismatch, proxy gap,
all-step flicker, step response and render figure equal; `proxies.npy`, the kept frames and the three CP2 clips byte-identical
(md5 unchanged); the only differences are the added `white_balance_means.*`, the robust `clipped_*` keys (pixels and samples),
the `interior` flicker figures and `interior_steps` (margin 60), `source_referenced` on the smoothing sequences, and
`render.json`'s three interior figures.

### Round 2 (Reviewer A on the delta `63d8422..865a054`)

Round 2 summary (full adjudication `r2\adjudication-r2.md`, evidence
`C:\Users\rwsmy\clearwater-review-evidence\wp1.4\r2\` with `md5sums.txt`): major 1, the 60-frame interior margin covers one
filter chain and not the nested staged analysis (reach = stages x radius; a new test shows it exactly) -- fixed as text and
instrument, the staged interior cells of 2 s and 4 s windows marked `*`; major 2, `render_clips(witness=None)` skipped the gate
-- the witness is now required; minors: a duplicated test helper (removed), "keyed by pts" worded as a fact (now a
recommendation), "stage 1 means are source-only" false for 3C (qualified). Reviewer A's own audits (records, before/after, report
numbers) were clean. No second round (the brief allows one).

Gates after the round-2 fixes: ruff check passed; ruff format 83 files formatted; mypy no issues in 18 source files; pytest 551
passed, 3 skipped (the owner moved the footage into `Snorkel\` and `SCUBA\` while the remediation ran, so the tests that open
`GX011628.MP4` at the footage root skip; test 7's body passes against `Snorkel\GX011628.mp4`); `-m gpu` 24 passed.

### Verification loop (remediation)

| # | Suspected | Confirmed? | How | Disposition |
|---|---|---|---|---|
| R1 | the first `unflatten` fix still admits `input01`, `input0` or a numbering gap | no | cases in `test_unflatten_refuses_every_name_flatten_cannot_produce` | refused |
| R2 | gains derived from supplied means differ from measured ones | no | `test_supplied_white_balance_means_give_the_gray_world_gains` (bit-identical on the frame's own means) | none |
| R3 | the re-extract changes the decode (frames, proxies) | no | md5 of `proxies.npy` and the kept frames equal before and after | none |
| R4 | the re-render changes the CP2 clips | no | the three clip md5s equal before and after | none |
| R5 | `render_clips` can skip the witness | yes | Reviewer A major 2 | fixed |
| R6 | the staged interior is not edge-free | yes | Reviewer A major 1; test of the nested reach | fixed (text, instrument) |

A full pass after the fixes found nothing new.
