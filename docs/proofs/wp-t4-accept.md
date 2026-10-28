# WP-T4 accept record (orchestrator generation 14, 2026-10-28)

**Package:** WP-T4, parallel test workers.
- Brief: `docs/briefs/wp-t4-brief.md` (FINAL, CHARC `3c3c35d7e40b525e`; AD-28).
- Lane: **Codex**, `implementer-codex-sol-high` (gpt-6.1-sol / high, `codex exec` turns through `scripts/codex_cell.py`, one session `01a17c16-3707-7e30-b81b-ecb9320feb6b`, turns 1-8).
- Both nets: the **Claude pass** (`codex_cell.py review`, `claude -p --model opus --effort high`, read-only), the OTHER model from the implementer.
- Report: `docs/reports/wp-t4-parallel-tests.md`. Ledger: `docs/proofs/wp-t4-ledger.md`.

**Candidate:**
- Branch `wp-t4-mc`: the author branch `wp-t4` (`063b91f`, base `ba6e923`) rebased with `git -c core.autocrlf=false` onto main `f467a20` (`217f1a0`; this record and the fill edit on top). 8 commits.
- **`git patch-id --stable` `0984fd4b`** on `ba6e923..wp-t4` and on `f467a20..wp-t4-mc`. This is the id of record, per CHARC: turn 8 is docs only, so it changed the id from turn 7's `3aafebff`.
- **Code identity with the suite-gate head:** `git diff --stat 08e87f5 wp-t4-mc -- src tests tools pyproject.toml uv.lock` prints NOTHING (run against the rebased head `217f1a0`).
- Main's moves since the base touch no code: `git diff --stat ba6e923 f467a20 -- src tests tools pyproject.toml uv.lock` prints nothing.
- Commits since `08e87f5`: `063b91f` (turn 8, report and ledger only).

**Footprint (checked at this seat):** 9 files.
- `pyproject.toml`: the `dev` line `pytest-xdist>=3.6,<4`, plus its grant comment.
- `uv.lock`: +24 lines, 0 removed; pytest-xdist 3.8.0 and execnet 2.1.2, both `License-Expression: MIT`.
- `tests/fixture_plugin.py`: the cold-cache lock.
- `tests/test_fixture_cache_lock.py`: NEW.
- `tests/test_conftest_guard.py`: worker cases.
- `tests/conftest.py`: ONE module-docstring paragraph. The AST outside the docstring is unchanged, as the cell proved with `ast.dump`.
- `tests/test_io_video_encode_bench.py`: E1's `@pytest.mark.slow` and its comment.
- The report and the ledger.

Nothing under `src/`, `tools/` or `src/clearwater/interfaces/`. Every changed blob has 0 CR bytes. Nothing footage-derived is committed: the node ids carry only clip names already in committed reports, and no location tag appears.

## Nets

| Net | Result |
|---|---|
| Reviewer A R1 (the Claude pass, run by me between cell turns, `wp-t4\r1\`) | Head `5e6a8d3`: **0 / 0 / 6 / 5** (critical / major / minor / advisory), `VERDICT: NO_NEW_CRITICAL_MAJOR`. All seven claims hold: partition, lock, guard, dependency, sharing, E1 and figures. The lock tests (4 passed) and the guard tests (60 passed, `-n 2`) were EXECUTED. Run checks: `modelUsage` `claude-opus-5-5`; `is_error` false; 63 turns; worktree clean; 12 permission denials, all refused scratch writes. md5s in `r1\md5sums.txt` (`review.txt` `f6626815a4690d9a752465ad1afec7fe`). Zero new blocking, so the loop TERMINATED: one round plus the single cleanup (turn 7, `08e87f5`). Opus high replaced the brief's FAST tier (Sonnet medium); CHARC ACCEPTED this (`d1812275`) as a ledger line, not a precedent. |
| **Reviewer B** (the Claude pass at this seat, on the candidate, `wp-t4\reviewB\`) | Head `ed7eca9`: **0 / 0 / 4 / 4**, `VERDICT: NO_NEW_CRITICAL_MAJOR`. Run checks: `modelUsage` `claude-opus-5-5`; `is_error` false; 76 turns; worktree clean; 10 permission denials, all refused scratch writes; no withheld path read. md5s in `reviewB\md5sums.txt` (`review.txt` `f544e951a79fda4078517dc9586a1504`). **Reviewer B reasoned, not executed, on the lock and the guard, because its read-only sandbox refused writes under `work/`. That is acceptable here because Reviewer A executed both (4 and 60 passed) and the final legs are green** (CHARC `65874bf2`). |
| **Suite gate: the two legs** (this seat, head `08e87f5`, code-identical to the candidate; exclusive window 01:27:41Z-02:31:59Z, OPEN/CLOSE to CHARC) | PARALLEL `uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=work/wp-t4/final-parallel-tmp`: **4031 passed, 1 skipped**, 451.96 s, EXIT 0. SERIAL `uv run pytest -q -rs -m "gpu or footage or gui or slow" --basetemp=work/wp-t4/final-serial-tmp`: **1036 passed, 10 skipped, 4032 deselected**, 3405.58 s, EXIT 0. 4,032 + 1,046 = 5,078. Free memory before each leg at least 12.48 GiB. PARALLEL sampler: peak RSS 6,906,589,184 B; minimum available 6,779,842,560 B; GPU complete (rise 878 MiB). |
| Collection (candidate) | all 5078; parallel 4032 (1046 deselected); serial 1046 (4032 deselected). |
| Static (this seat, candidate) | `ruff check .` all checks passed; `ruff format --check .` 238 files already formatted; `mypy` no issues in 136 source files. |
| Harness gate (this seat, candidate with this record and the fill edit) | `uv run python -m unittest discover -s tests/harness`: Ran 382 tests, OK (skipped=1); ruff check and format re-run clean after the fill edit |

**Skips:** 9 of the 11 are `test_methods_assembly_v8.py:44`. The look-check frames are absent from a gate worktree's ignored `work/wp1.3/`; main's tree runs them. The other two are `test_color_roundtrip.py:121` and `test_photo_check.py:139`.

**Reviewer B: adjudicated AT THE GATE** (CHARC `65874bf2`, upheld in full).
- **B1 MINOR:** `test_prototype_clip.py`'s module-scoped `neutral_analysis` runs real device analysis for four unmarked parallel-leg tests. Added to the RAISED GPU finding (turn 8). Not fixed: marker meaning is out of scope.
- **B2 MINOR:** the parallel leg holds more timing bounds than the report listed. The report now carries the complete verified inventory as WATCH items for their owning packages (turn 8). The tightest are `test_io_video_encode_bench.py:125` (`1.0 <= strays < 1.5`) and `:258` (`< 1.0`). None failed in any of the seven measured parallel or baseline legs. Not edited.
- **B3 / B4 / B5 MINOR / MINOR / ADVISORY (gate-text gaps):** folded into the fill's GATE_CHECKS by this seat (below):
  - each leg's `-rs` skips are quoted and compared with the previous gate's;
  - `PYTEST_ADDOPTS` is unset, and the candidate's full collection is diffed against main's, with every removed ID explained;
  - each collection exits 0 and matches pytest's own count;
  - the gate runs from Git Bash, because a PowerShell 5.1 redirect writes UTF-16.
- **B6 ADVISORY:** a `KeyboardInterrupt` between acquiring the lock and entering `try` leaves the lock behind. Recorded under the m2 limit, with the same recovery.
- **B7 / B8 ADVISORY:** report corrections in turn 8 (`063b91f`): the w1 line citation and the candidate base.
- No B pass 2.

**Reviewer A R1 dispositions (turn 7, CHARC `d1812275`):**
- m1, m3, m4 and m6: FIXED in the report.
- m2: a stated LIMIT. Both lock messages name the lock path (`fixture_plugin.py:248`, `:254`), and the report's Limits section gives the 180 s / 900 s rules and the manual remedy.
- m5 (no test of a worker refusing independently): LIMIT, because a worker-only unsafe root is unreachable in envelope. It becomes CHARC's MINOR row.
- a1-a5: recorded; a3 is a WATCH item.

## Measurements (rung 4; exclusive windows, OPEN/CLOSE to CHARC; head `dd49a15` on `ba6e923`)

| Round | BASELINE (s) | PARALLEL (s) | SERIAL (s) | P+S (s) | Saving vs same-round BASELINE |
|---|---|---|---|---|---|
| r1 (19:09-21:29Z) | 4564.80 | 497.30 | 3335.36 | 3832.66 | 732.1 s, -16.0 % |
| r2 (21:30-23:47Z) | 4349.92 | 493.54 | 3372.59 | 3866.13 | 483.8 s, -11.1 % |
| Median | 4457.36 | 495.42 | 3353.98 | **3849.40 (about 64 min)** | |

- Every leg EXIT 0, and every round's counts reconcile: 5067/11 = 4031/1 + 1036/10.
- The two P+S totals differ by 0.87 %, so there was no third round (Q7, the 15 % rule).
- **Figures of record** (CHARC `144f9735`): the saving against the same round's baseline for both rounds, with the spread, and the median P+S as the one-line figure. These are suite wall times, not product (N6/V16) figures.
- PARALLEL is the stable fast part. SERIAL, at 73-78 % of BASELINE, is the gate's floor.
- N=4 held peak RSS at 6.97 / 6.85 / 6.91 GB (r1 / r2 / final), with minimum available 6.56 / 6.99 / 6.31 GiB against the 2 GiB floor.
- **Diagnostic legs (not rounds):**
  - D2, on the rebase onto `ba6e923`: a PARALLEL leg, 4031/1, green.
  - **D3, the serial expression with `--durations=0 --junitxml`:** 1036/10, 3,331.31 s, EXIT 0, CHARC-approved.
    - By marker (junit setup + call + teardown): gpu 586 tests / 1,843 s; footage 17 / 2,001 s; gui 441 / 68 s; slow 20 / 2,932 s.
    - 13 tests carry several markers. The de-duplicated total is 3,326.963 s over 1,046 cases, checked independently against the junit file at this seat. The residual is 4.35 s (0.13 %).
    - Four export bodies (WP3.14's and WP3.10's) take about 2,276 s, which is 68 % of the serial leg.
- **E1 is resolved:** it passed in every BASELINE and SERIAL leg and in D3. Its bound is unchanged.
- **GPU finding (RAISED, not fixed; marker meaning is out of scope):**
  - the nominal non-GPU leg rises +878 to +1,036 MiB;
  - the cause is three import-time `select_backend("auto")` probes (`test_prototype_backend.py:23`, `test_prototype_clip.py:41`, `test_prototype_temporal.py:47`) plus B1's module fixture.

## Cell depths (`depth_input_tokens`, dispatcher-read)

| Turn | Depth |
|---|---|
| 1-3 | not read as input depth. The `tokens_used` footers (73,551 / 119,645 / 220,811) are cumulative token use, not depth |
| 4 | 284,234 (from the session file; window 475,000) |
| 5 | 95,253 (after compaction) |
| 6 | 152,531 |
| 7 | 212,913 |
| 8 | 288,403 (the cell's final turn; past the 250K evaluation point with no further turns) |

**Session choice:** the cell continued in its session for the tabulation, the report and the reviews, in place of the planned fresh session. CHARC ruled it "a choice, not a necessity" once the depth fell to 95K, and the ledger records it.

## The fill change (this seat, at this accept)

`docs/review-gate-clearwater.md` GATE_CHECKS:
- the single `uv run pytest` sentence is replaced by the two-leg gate;
- the collection set checks and the full-collection diff against main;
- the skip comparison;
- `PYTEST_ADDOPTS` unset, run from Git Bash;
- fresh `--basetemp` paths under `work/`;
- the 5 GiB preflight;
- the new-test rules: per-test `tmp_path`; a new wall-clock bound is `slow` with a reason that names the bound and says "timing isolation, not duration"; sanity ceilings of ten times the expected figure or more are exempt and stay parallel. This rule is CHARC `65874bf2`, from Reviewer B finding B2;
- product timing and memory figures from serial runs only.

The CLAUDE.md Conventions line is CHARC's (owed).

## Owed by CHARC at QA (`19a075eb`)

- the CLAUDE.md Conventions line: the two-leg command and the median P+S of about 64 min beside the baseline spread;
- the HD-1 third data point (Codex lane, WP-T4): eight turns, the depths above, A one round, B clean at the gate, the walls;
- the suite-cost row (four export bodies = 68 % of the serial leg; their size is the lever; trigger: WP3.14's and WP3.10's next touches, or a suite-cost pass);
- the m5 MINOR row;
- the DR-58 (c) disposition: E1 resolved.

## Main gates

Merged with `git merge --ff-only wp-t4-mc` onto `f467a20`; main's head is this record's commit. Patch-id rechecked on main after the merge (`git diff f467a20 main~1 | git patch-id --stable` = `0984fd4b`).
