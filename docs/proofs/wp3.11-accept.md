# WP3.11 accept record (orchestrator generation 10, 2026-10-26)

**Package:** WP3.11 analysis engine (`clearwater.analysis`: `proxy`, `smoothing`, `store`, `engine`;
`tools/step_aware_eval.py`), brief `docs/briefs/wp3.11-brief.md` (FINAL). Three seats (implementer-opus-high): cell 1
round 0, build, step-aware evaluation, R1 (359K at the pause); cell 2 after the pause: R1 remediation and V3-1
(171,115), R2 (202,325), R3 (237,310), final report (251,880); cell 3 Reviewer B remediations (90,601; 130,031 at
retirement). Every figure dispatcher-read at a yield.

**Candidate:** branch `wp3.11-mc`, the author branch `wp3.11` (`fb6fa5a`, base `de206e2`, 51 commits) STACKED on WP3.4's
candidate `c1bf077` for the gate (files disjoint), then rebased onto main `6b58619` for the merge; whole-diff patch-id
`4088add404f592408bd95797c03c5d92e3d08ac1` on `de206e2..wp3.11` and on the candidate range (identical).

**Footprint (checked at this seat):** owned files only: `src/clearwater/analysis/*`, `tests/test_analysis_*.py`,
`tools/step_aware_eval.py`, the report, the ledger. `interfaces/`, `cache/`, `methods/`, `gui/`, `io/`,
`pyproject.toml`, `uv.lock` untouched; no import of `io`, `cache`, `methods` or `gui` from `analysis`; every changed blob
LF.

**Y-1:** the report's Y-1 body is byte-identical to WP3.4's (`cmp` at this seat). **Y-2 store side:** `put` refuses
dtype kinds outside "iuf" (aligned with WP3.4 at this gate, bool refused, failing first).

**Results:** V3 (CHARC V3-1, AD-14 `b9f3d09`) asserted on the seeded jittering-patch clip, ratios 0.017-0.024 on L*,
a*, b*, contrast for both test-local methods; ad14-flicker meets AD-14 and records the V3 ratios 0.39-0.49 (with
WP1.4's 0.35-0.45, information for CP5 / WP4.2, owner-pending list). Step-aware evaluation re-run after F7: default
`median_gaussian` 2.0 s stands (candidates 1.7-5.4x flicker, 5-13x peak step); AD-3 PROVISIONAL until WP5.2.

## Nets

| Net | Result |
|---|---|
| Reviewer A (cells, STRONG, codex 0.162.1 / gpt-5.6-sol high) | R1 0/3/5, R2 0/2/0 (A1 NEW stale records under the new hash; A2 REOPENED no cancel during smoothing), R3 0/0/1 (terminating; docstring cleanup); evidence `clearwater-review-evidence\wp3.11\r1..r3` |
| Cell's window | full pytest at `d3e3c36`: 3789 passed, 1 failed (`test_gui_startup.py::test_shutdown_stops_every_worker_when_one_overruns_its_timeout`, WP3.16's timing test, outside the diff, under host load; 5/5 alone), 2 skipped |
| Reviewer B pass 1 (this seat, `0916646`, stacked) | NEW_CRITICAL_MAJOR_FOUND; banner gpt-5.6-sol / high, read-only; 0 `^ERROR`; 15 "succeeded in"; 452,647 tokens; withheld paths only as exclusions. #2 MAJOR (`1.0` -> `1` kept the old hash while the helper hash moved; CONFIRMED in the code), #1 cancel during the post-pass lookup (MINOR at the gate), #3/#4 test gaps, #5 out-of-envelope advisory -> ONE remediation by a fresh seat (`5fa4fae`, `661eed1`, `6833f15`, `7330842`, `7e025e5`) plus the raised `1` -> `True` case, ruled in and implemented as `same_value` (`68d5daa`; my literal ruling would have missed `True == 1.0`, the cell caught it). md5 `review-B.txt` 26077884371d... (`reviewB\md5sums.txt`) |
| Reviewer B pass 2 (this seat, `fe64c75`, the re-run) | NEW_CRITICAL_MAJOR_FOUND; 0 `^ERROR`; 12 "succeeded in"; 157,127 tokens. SECOND BLOCKING PASS, ADJUDICATED AT THE GATE: #1 MAJOR EXECUTED (signed zero: `0.0` -> `-0.0` equal by `same_value`, distinct in JSON) -> fixed `ef6c24d` (`float(v) + 0.0`), VERIFIED BY EXECUTION at this seat (canonical forms and `same_value` at depth); #4 test gap -> `1cb64c2` (plant shown); #2 (cancel during/after `mark_complete`) and #3 (`cancel()` takes no lock, can race the final publication) ACCEPTED AS LIMITS, report and docstring made precise (`aea94d5`, `c527ca5`, `fb6fa5a`) -> DR-47. md5 `review-B.txt` 99cde5c6786b... (`reviewB2\md5sums.txt`) |
| Candidate full pytest (this seat, stack top `f1c1bd8`) | CuPy 4200 passed, 2 skipped, 1935 s, exit 0 (the stack: WP3.9 + WP3.4 + WP3.11); no-CuPy NOT RUN TO THE END: stopped at ~5 % by Claude Code's low-memory reaper while the session was idle (not a test result; not restarted, per the reaper's rule). The brief requires no no-CuPy leg (`analysis` may not import `cupy`, brief line 124), and WP3.4's no-CuPy leg passed on the stack base `c1bf077` (3418 passed, 554 skipped) (offscreen) |
| Harness gate | 366 OK (1 skipped) on `228285a`; ruff clean, 201 formatted, mypy 117 clean. `228285a` (rebased onto main `6b58619`) differs from the tested stack top `f1c1bd8` in docs only (0 lines in src, tests, tools, pyproject, uv.lock) |

**Debt:** DR-23 CLOSES for the product; DR-25 (1), (2), (4)-(7) CLOSE for the store and smoother, (3) OPEN (WP5.2);
DR-41 not reopened; DR-45 (a) not reached (the engine's cancel sets an event; the job thread closes its own stream).
DR-47 NEW (B pass 1 #5 and pass 2 #2/#3, limits).

**Consumer notes:** WP3.18 (progress, cancel, the provisional-to-smoothed switch, `AnalysisState`); WP3.14 reads the
smoothed record per pts under `schema_hash` (numbers canonical: int and float equal, bool distinct, signed zero equal)
and waits for completion; a cancel can race completion (DR-47).
