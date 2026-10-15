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
| 1 | `82c258b` | WSL / 0.162.1 | 0 | 0 | 7 | 6 of 7 | 7 | 0 | 0 | product (`pipeline.py`: length check of supplied triples) + tests + report text | (dispatcher fills) | banner OK (stderr); `^ERROR` 0; `ERROR codex_core` 0; footer 1; `^ succeeded in` 29; VERDICT anchored; `docs/proofs` hits all echoes or exclusion pathspecs, no withheld access | NO_NEW_CRITICAL_MAJOR |

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
