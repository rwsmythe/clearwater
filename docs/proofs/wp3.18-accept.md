# WP3.18 accept record (orchestrator generation 12, 2026-10-26)

**Package:** WP3.18 timeline and analysis (`clearwater.gui.analysis_service`: the `ClipAnalysis` seam and its stub;
`clearwater.gui.timeline`: `TimelinePanel`, `install_timeline`), brief `docs/briefs/wp3.18-brief.md` (FINAL; CHARC
rulings `53d1d906e47fe2c9`; Q-A RULED (C) `bdbd8323ceace897`, AD-7 amended `8c67a6d`: `retarget`). Three seats
(implementer-sonnet-high, STRONG): seat 1 round 0 (177,692 at the round-0 yield) and R1 (342,258 at the round-1
yield, stop); seat 2 R2 remediation (147,490 at the round-2 yield) to R4 (186,125 at the round-4 yield) and R5 closing
(274K at retirement, generation 11); seat 3 Reviewer B pass-1 remediation (92,378 at its return, dispatcher-read).

**Candidate:** author branch `wp3.18` (`b6673df`, base `718324b`, 35 commits); merge candidate `wp3.18-mc` (`88371de`,
base `db17e5b`, 35 commits). Gate: stacked branch `stackB` = main `ccaecd7` + WP3.17 + WP3.19 + WP3.20 + WP3.18
(cherry-picked ranges, file sets disjoint; head `d71d994` at drafting); every owned file byte-identical in `stackB`,
`wp3.18-mc` and `wp3.18` (`git diff`, 0 lines). Merged: one `git merge --ff-only` of `stackB-acc` onto main; this record's own commit follows the package's last commit.

**Footprint (checked at this seat):** owned files only: `src/clearwater/gui/analysis_service.py`,
`src/clearwater/gui/timeline.py`, `tests/test_gui_analysis_service.py`, `tests/test_gui_timeline.py`, the report
`docs/reports/wp3.18-timeline-analysis.md`, the ledger. `interfaces/`, `gui/__init__.py`, `contract.py`,
`pyproject.toml`, `uv.lock` untouched; 0 CR bytes in every owned blob.

**Results:** V18 leg (corrected frame before completion, smoothed after), G5/D70 progress and Cancel, D72 scrub of
stored proxies with the exact pts committed on release, DR-44 (a) consumer side, AD-15 states, Q-B method change as
"superseded". After four rounds of lane-ordering defects the orchestrator ordered a design guard: the lane became one
latest-intent rule (`b1f9783`) with a seeded interleaving test, 200 seeds x 28 steps (`fa0fa7d`; failed on `732872e`
at seed 0; five planted panels fail by their own reasons). V7 maxima 14, 23, 39 ms (seat 1), 12, 13 ms (seat 2),
informational. Targeted: 82 passed.

## Nets

| Net | Result |
|---|---|
| Reviewer A (cells, STRONG, WSL codex-cli 0.162.1 / gpt-5.6-sol high) | R1 3 MAJOR (F1, F2, F4; F3 rejected, F5/F6 MINOR) + 5 MINOR; R2 1 MAJOR (#3) + 3 MINOR (#1 limit, #2 rejected); R3 1 MAJOR (defect of the R2 #3 fix) + 1 MINOR; R4 1 MAJOR (a press without a move); R5 0 blocking (finding 1 MINOR by effect) + 3 test-side: LOOP TERMINATED at the five-round gate, cleanup `b50a36e` (option S). R3 PROCEDURAL BREACH (remediated `c471bca`, `732872e` in the verdict turn), disclosed, not voided: each fix reproduced first, with a failing-before test. Evidence `clearwater-review-evidence\wp3.18\r1..r5` |
| Reviewer B pass 1 (this seat, `44ef658` = `579321a` rebased; kept as branch `wp3.18-mc1`) | NEW_CRITICAL_MAJOR_FOUND; banner gpt-5.6-sol / high, read-only; 0 `^ERROR`; 14 "succeeded in"; 225,709 tokens. #1 MAJOR (A->B->A burst in the run-returned-to-`on_done` window declared complete while the engine held B's job), #2, #3, #4 MINOR -> seat 3: `a49c36a` (#1), `6f5fd11` (#2), `f50aee0` (#4), `bd2d70b` (style), `fd0745a` (#3 report mapping). md5 `review-B.txt` e74f7a60e097... (`reviewB\md5sums.txt`) |
| Reviewer B pass 2 (this seat, `d8f3859`) | NO_NEW_CRITICAL_MAJOR; banner gpt-5.6-sol / high, read-only; 0 `^ERROR`; 16 "succeeded in"; 189,459 tokens. 5 MINOR + 1 ADVISORY, disposed as the report's "Erratum at the gate" (`b6673df`; candidate `88371de`), no code change. VERIFIED BY EXECUTION at the orchestrator's seat: the 7 new tests failed on `579321a` (7 failed / 55 passed), 82 passed on the candidate. md5 `review-B.txt` 4429508c9608... (`reviewB2\md5sums.txt`) |
| Candidate full pytest (this seat, stack top `d71d994` = main `ccaecd7` + WP3.17 + WP3.19 + WP3.20 + WP3.18) | 4501 passed, 2 skipped, 1579 s, exit 0 (CuPy as installed, offscreen, one background process; log `.worktrees/stackB/work/g12-full.log`). This is also main's figure by code identity: main after the merge differs from `d71d994` in the four accept records only |
| Harness gate | 366 OK (1 skipped) on `d71d994`; ruff clean, 217 formatted, mypy 126 clean; CR check 0 on every changed blob |

**Debt:** DR-44 (a) and (b) ADDRESSED for this package; DR-44 (c) WP4.3's; DR-23 not reopened; DR-47 shape kept (late
cancel reads "cancelled"). Rows by CHARC at QA (test-only limits): the stub `statistics()` reader/worker race (can
return the previous run's statistics when a new `run` starts mid-read); the interleaving oracle does not reject a
transient intermediate `set_position` while the slider is up (it proves the final state and every statistics pairing).

**Consumer notes:** WP4.3 builds the adapter per the report's mapping: F-2 (`DiskProxyCache.lookup` on the main thread
via `pts()`) -> the adapter keeps its own pts list, refreshed by a worker, and re-measures V7; `retarget` point 5: a
job returned by `engine.set_parameters` is KEPT, `retarget` returns False and the next `run()` executes it; the
corrected `run` mapping: a kept job takes priority (offer the latest parameters, run the kept job, clear it); the
factory reads live `Settings` through a closure. WP3.20's dialog relies on `Session.set_analysis` phases.
