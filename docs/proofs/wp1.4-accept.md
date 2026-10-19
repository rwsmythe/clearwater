# WP1.4 — Accept record (noise and statistics experiments, shallow part)

**Accepted 2026-10-19 by the orchestrator** (generation 2, session
`clearwater-orchestrator-20261018-1442`), on CHARC's commission `0fd7c88ad56a7083` (the owner's
partial CP1 releases the shallow part) and rulings `35b13416` / `e5505505` (merge first; the
footage-layout skips go to WP-T2). Gate per `docs/review-gate-clearwater.md` Part 2.

| Item | Value |
|---|---|
| Brief | `docs/briefs/wp1.4-brief.md` (FINAL `9ed1a1c`); remediation `docs/briefs/wp1.4-remediation-brief.md` (`179fab0`). Spec v0.5.2. |
| Base SHA | `9ed1a1c` |
| Author head | `63d8422` (`wp14-cell`, implementer-opus-high; 384K at return, retired); after the remediation `45fd95b` (`wp14-fix`, implementer-sonnet-high; interrupted at the 10-15 restart, resumed 10-18, returned 2026-10-19 00:36Z). |
| Merged head | `91f5775` (`wp1.4-mc` = `wp1.4` rebased onto main `aea3cf2`; main fast-forwarded). |
| Byte identity | `git patch-id --stable` = `5b5b3108a4f1de61755b58293fb8b3d325a39b36` on `9ed1a1c..45fd95b`, on the B candidate `6b5ea91..911d837`, and on main `aea3cf2..91f5775`. The merged tree differs from the B-reviewed tree `911d837` only in `docs/orchestrator-state.md` and `docs/charc-state.md` (main-side state commits during the gate; `git diff --stat 911d837 91f5775`). |
| Reviewer A | Codex STRONG (gpt-5.6-sol / high), WSL, codex-cli 0.162.1. Round 1 converged at the author's seat; round 2 on the remediation delta `63d8422..865a054`: 2 majors (nested staged reach -> `staged_reach`; an optional witness made mandatory) and 3 minors, all fixed in `b3f48b1`; those fixes were not re-reviewed by A (one round only) and are covered by B's re-run below. Ledger `docs/proofs/wp1.4-ledger.md`; evidence `clearwater-review-evidence\wp1.4\r1\`, `\r2\`. |
| Reviewer B | My seat passes: pass 1 on `af98ca8`, BLOCKING; ONE remediation; re-run on `911d837`, BLOCKING; the second block was adjudicated at the gate (below). |
| Owned files | Exactly the brief's six: `tools/prototype/temporal.py` (new), `tools/prototype/pipeline.py` (the additive hook), `tools/statistics_experiments.py` (new), `tests/test_prototype_temporal.py` (new), `docs/reports/wp1.4-statistics.md` (new), `docs/proofs/wp1.4-ledger.md` (new). No dependency change (`pyproject.toml`, `uv.lock` untouched). |

## Reviewer B pass 1 (seat, generation 1), on candidate `af98ca8`

Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp1.4\reviewB\` (transcript md5
`f53b20991cea4218f27af4c41cb97354`). Four majors (white-balance means not recorded; clipped
fraction of samples, not pixels; `unflatten` accepting an unknown suffix; series applied by list
position), minors and advisories, twelve in all. Eleven were REMEDIATED through the ONE
remediation (findings table in the remediation brief); finding 12 (VFR timing) was BANKED out of
envelope as DR-23.

## Reviewer B re-run (seat, generation 2), on candidate `911d837`

Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp1.4\reviewB\rerun\` (`md5s.txt` there).
Prompt: pass 1's, rebased onto the new candidate, plus a "THIS IS THE RE-RUN" section naming the
twelve dispositions and the unreviewed round-2 fixes. Assertions:
- the banner reads gpt-5.6-sol / high (probe READY 00:45Z, same invocation);
- `^ERROR` 0; one `ERROR codex_core` hit, an echo of the prompt;
- footer 1; 31 `succeeded in`;
- an anchored `VERDICT: NEW_CRITICAL_MAJOR_FOUND`;
- no withheld access: every `docs/proofs`, ledger and evidence hit is an echo of the prompt or of
  a brief it was allowed to read; the footage paths appear only inside `excerpt.json` records it
  was allowed to read; it never listed the footage folder.

| File | md5 |
|---|---|
| prompt | `06629f458035b22f0fee50b35976ab96` |
| diff | `b606384f74910f6815e15b722cddce6a` |
| transcript | `322d7423d58082b3ae3abd6058de7543` |
| stderr | `30e50e5c06dc1366bd1027ea4ecd6265` |

B's executed audit found the records consistent: both excerpts aligned and finite (180 / 179
frames), the stored flat and staged series equal to the recorded 1 s Gaussian smoothing to
1.42e-14, every principal table equal to the JSON, the three witness entries identical, and the
three clips' read-back checks passing.

This is the package's SECOND blocking B, so it is adjudicated at the gate by irreversibility,
with no third remediation. **Common ground:** WP1.4 is an instrument whose outputs (records, the
report, the three CP2 clips) are already produced and verified; nothing it does is
irreversible; no product code, frozen interface or default changes; IF-3 and the product
smoother are WP2.1's, which reads DR-25 as input. Each finding was confirmed on the code at my
seat before disposition.

| # | Finding | Disposition |
|---|---|---|
| 1 | MAJOR (reasoned, confirmed `statistics_experiments.py:312`): `series_from_record` takes names from `entries[0]`; an unknown name on a later entry is dropped. | **NOT BLOCKING.** Needs a hand-altered record; the run's records carry one key set (B's audit). DR-25(1); report erratum (the "never silently dropped" sentence). |
| 2 | MAJOR (reasoned, confirmed `pipeline.py:566`): with gains supplied, means are ignored and not shape-checked. | **NOT BLOCKING.** The precedence is the remediation brief's permitted choice and is disclosed in the report's field table; identity holds either way (test 1). The missing shape check is DR-25(2); erratum to the "each supplied value replaces" sentence. |
| 3 | MAJOR (executed): no staged 2 s figure is edge-free on 6 s excerpts, yet ground 2 of the 2 s recommendation uses them. | **NOT BLOCKING, result-bearing.** The D98 comparison (1 s) stays edge-free. Grounds 1, 3 and 4 are filter properties; ground 2's size is provisional. Erratum gives the edge-free flat interior figures from `results.json` (2 s vs 1 s: 0.168 vs 0.183 on GX011627, 0.036 vs 0.048 on GX011625; 8 % and 25 % less). The default window is decided at WP2.1 (spec 14.1), not here. DR-25(3). |
| 4 | MAJOR (reasoned, confirmed `statistics_experiments.py:946`): a stale same-tick record with another smoother would render. | **NOT BLOCKING.** Needs a foreign record swapped into `work/wp1.4/`; the present records match the 1 s Gaussian (B's audit). DR-25(4); erratum to the "stale record" sentence. |
| 5 | MINOR: `measure()` accepts a one-input saliency record. | BANKED, DR-25(5). |
| 6 | MINOR: a NaN raw series fails after the staged write. | BANKED, DR-25(6) (the run exits non-zero). |
| 7 | ADVISORY, out of envelope: `Fraction(window_s)` binary-float off-by-one at other rates. | BANKED, DR-25(7). |

**Errata at the gate.** The report was corrected in four places, text only, with no code or
record change: the field-table sentence on supplied values (finding 2), the `unflatten`
paragraph (finding 1), the pts-keying paragraph (finding 4), and ground 2 of the smoothing
recommendation (finding 3). Each is marked "Erratum at the gate" in the report.

## Verification QA (orchestrator seat)

**Gate checks on the candidate `911d837`**, WinGet links on PATH:

```
uv run ruff check .            -> All checks passed!
uv run ruff format --check .   -> 92 files already formatted
uv run mypy                    -> Success: no issues found in 18 source files
uv run pytest -q -rs           -> 595 passed, 3 skipped, 1 warning
uv run pytest -q -m gpu        -> 24 passed, 574 deselected
python -m unittest discover -s tests/harness -> Ran 366 tests ... OK (skipped=1)
```

**Gate checks on main `91f5775`** after `uv sync`:

```
uv run ruff check .            -> All checks passed!
uv run ruff format --check .   -> 93 files already formatted
uv run mypy                    -> Success: no issues found in 18 source files
uv run pytest -q -rs           -> 595 passed, 3 skipped, 1 warning
uv run pytest -q -m gpu        -> 24 passed, 574 deselected
python -m unittest discover -s tests/harness -> Ran 366 tests ... OK (skipped=1)
```

**The three skips, verbatim** (CHARC `e5505505`: stated with their cause and closer):

```
SKIPPED [1] tests\test_container_spike.py:904: GX011628.MP4 is not in the footage folder
SKIPPED [1] tests\test_lookcheck.py:1291: GX011628.MP4 is not in the footage folder
SKIPPED [1] tests\test_prototype_temporal.py:841: GX011628.MP4 is not in the footage folder
```

Cause: the owner moved the chapters into `Snorkel\` and `SCUBA\` (lowercase `.mp4`) on
2026-10-18; the tests look for the file at the footage root. Two of the three predate WP1.4 and
skip on main before this merge as well. Not caused by this package. Closer: **WP-T2** (footage
locator, `docs/briefs/wp-t2-brief.md`), dispatched on main next; it restores 0 skipped before
WP1.2 Part B. Banked as DR-24. The remediation cell's own gate showed the same 3 skips
(551 passed, 3 skipped); its records comparison found the three CP2 clips' md5s unchanged
(`53f8c671`, `84a0e488`, `77e6a1ac`).

**Witness (the default path).** `correct()` from main `6b5ea91` and from the candidate, with
`statistics=None`, on a fixed synthetic 600 x 900 image (seed 12345): bit-identical in 6 of 6
cases (Ancuti 2018 blue off and on, and 3C; CPU and GPU), float32, `np.array_equal`. Script
`witness_r.py` (generation 1's, unchanged).

**Locks.** Only the six owned files changed (`git diff --name-only`); no dependency change. The
runner's writes go through `OutputRoots` checked paths under `work/wp1.4/` (claim 7; tested in
`test_prototype_temporal.py`, `_save_array` refusing a footage path), and neither B pass raised
a claim-7 finding.

**Records note.** The cell's first remediation return quoted 0.76 for the largest staged/flat
pixel difference; the records give 0.68 (GX011627) and 0.90 (GX011625). The report quotes the
records.

## Follow-ons

| Item | Disposition |
|---|---|
| The three footage skips; root-path resolution in `pack.py` and the WP1.4 runner | COMMISSIONED: WP-T2 (CHARC `35b13416`, `e5505505`, `59860def`). DR-24. |
| Root-path resolution in the WP1.5 spike CLI (`spike.py:880`) | BANKED, DR-26 (trigger: a spike re-run or WP3.10). |
| VFR smoothing by index (pass 1 finding 12) | BANKED, DR-23 (WP2.1; IF-3 keyed by pts, CHARC `0da890ba5a2eb047`). |
| B re-run findings 1-7 | BANKED, DR-25 (WP2.1; the smoothing default re-measured on an excerpt of at least 182 frames). |
| Gain-cap noise test (deep footage) | COMMISSIONED earlier as WP1.4b (CHARC `0fd7c88ad56a7083`); waits on the scuba look-check cases. |
| CP2 | The owner's look check: `work/wp1.4/GX011627/` staged, flat and unsmoothed clips (1 s Gaussian), beside WP1.3's pack. |

Branch `wp1.4` is kept (it holds the reviewed pre-rebase SHAs this record cites).
