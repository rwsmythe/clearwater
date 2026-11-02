# WP-D112 accept record (orchestrator generation 34, 2026-11-02)

**Package:** WP-D112, the post-encode audio check reads a raw PCM stream by its sample extent and timeline, not its packet list (DR-112: the product refused 9 of 17 owner iPhone MOVs in WP5.3's `clips V-P` although their audio was carried byte-identical).
- **Brief:** `docs/briefs/wp-d112-brief.md` (FINAL on CHARC `4bff0b93`; the Reviewer A round 1 ruling `b44b0ee7` and the `encode.py` grant `81ebcf52` folded on the branch).
- **Lane: CODEX**, `implementer-codex-sol-high`, three sessions, seven turns (session 1 `01a19964-...` turns 1-2; session 2 `01a1997a-...` turns 3-4, retired at 184,370; session 3 `01a19b24-11a5-7512-b1a1-ade19f406611` turns 5-7, at **172,713** after turn 7). Both nets Claude (`claude -p --model opus --effort high`), the other model.
- **Report:** `docs/reports/wp-d112-pcm-audio.md`. **Ledger:** `docs/proofs/wp-d112-ledger.md`. **Evidence:** `C:\Users\rwsmy\clearwater-review-evidence\wp-d112\` (`cell`, `r1`, `r2`, `B`).

**Candidate:** branch `wp-d112`, rebased onto main `1972429b` and gated as **`5080d652`**; `git patch-id --stable` over the 13 package commits equal before and after the rebase (`work/orch-g34/d112-patchid-before.txt`, `-after.txt`). This record's commit adds this file and the report's Reviewer B section and F-B4 Limit (docs only); the harness leg re-ran on it (below).

**Footprint** (`git diff --name-only main..wp-d112`, 12 paths plus this record): `src/clearwater/io/video/verify.py` (the PCM rule); `src/clearwater/io/video/encode.py` (exactly the six granted lines: the D86 partial-frame warning after `check_output`); `tools/fixtures/video.py` (the `_build_pcm` recipe); NEW `tests/fixtures/video/pcm-irregular.mov` (binary, `-text`; rebuilt byte-identical by Reviewer B, 219,463 bytes) and its `tests/fixtures/manifest.json` entry; `tests/test_io_video_encode_units.py`, `tests/test_io_video_encode.py`; the four granted manifest consumers' edits (`tests/test_fixtures.py`, `tests/test_jobs_naming.py`); the brief, report and ledger. No frozen interface, no `probe.py`, `jobs/`, `app/`, `gui/`, no dependency. Every changed text blob 0 CR and ASCII.

## Nets

| Net | Result |
|---|---|
| Round 0 (turn 1) | anchors, manifest consumers, sample-count source; turn-2 rulings (both totals; four granted consumer edits). |
| Reviewer A round 1 (`bd655a07`; `...\r1\`) | **NEW_CRITICAL_MAJOR_FOUND**: F1 MAJOR (a truncated source under D86 refused although every readable sample was carried), F2 MINOR (no pts check after the first packet), F3 ADVISORY. CHARC `b44b0ee7`: F1 the D86-only exception with a warning (grant `81ebcf52`: one bounded `encode.py` edit), F2 run equality in source ticks, F3 banked. Remediated in turn 5 (RED 13 failed / 7 passed, then GREEN). |
| Reviewer A round 2 (`78d2a03e`; `...\r2\`; started early on the OWNER's override, ~07:45Z, verbatim "I am going to override.  Start the 2nd round.") | **NO_NEW_CRITICAL_MAJOR**, CONVERGED; 5 advisories: 4 adopted as a test-only real-sink row (turn 7), 1-3 report Limits, 5 a report sentence. |
| **Reviewer B** (Claude pass at the orchestrator's seat on `f7f2cce9`; `...\B\`) | **NO_NEW_CRITICAL_MAJOR**, 35 turns, `is_error` false, worktree clean after. F-B1 MINOR (in envelope, outside the package: the V4 instrument still compares PCM per packet) -> DR row + a small Codex follow-on (CHARC ruling, 2026-11-02T08:03:39Z); F-B2 / F-B3 / F-B4 banked (two notes under the DR-112 close; F-B4 a report Limit). |

## Gate

The THREE-leg gate (fullclip triggered: the fullclip nodes reach the changed check), WP-T7's flags and redirects (`work/orch-g34/gate.sh`), on `5080d652`, run id `d112`, Git Bash, `PYTEST_ADDOPTS` unset, `QT_QPA_PLATFORM=offscreen`; no window open, no build piece and no Claude reviewer pass running during any leg; stall watch armed throughout (no stall). C: 97 GB free at the start, 84 GB at the end.
- **Static:** `ruff check` passed; `ruff format --check` 306 files already formatted; `mypy` no issues in 154 source files.
- **Collection:** all **7,786** = parallel 6,511 + serial 1,268 + fullclip 7; no duplicates; union identical to collect-all.
- **PARALLEL** (`-n 4 --timeout 600`): **1 failed, 6,509 passed, 1 skipped**, EXIT 1, 832 s. The skip is the standing swscale refusal (`test_color_roundtrip.py:123`). The failure: `tests/test_io_video_encode_bench.py::test_a_frames_release_is_not_timed_as_its_write`, `median(write_s) < 0.15` read 0.28437 (the node ran 64.7 s under `-n 4`); outside the package's files (the bench module unchanged since WP-T4 `85b09a7d`). Re-run ALONE after every leg ended: 3 of 3 PASS on `wp-d112` (25.3 / 19.9 / 17.7 s) and 3 of 3 PASS on `.worktrees/wp5.3` = main's code `91db201b` (24.1 / 18.2 / 20.6 s). Disposition (CHARC ruling 2026-11-02T09:51:52Z): **DR-99 (b)**, a second load-sensitive wall-clock bound in the same bench module, not a new row; paydown a `slow` marker with its reason on that node in the WP5.3 witness read-back turn beside B-F4. Log md5 `dcf242363a7aeb79262f8f708e8e7231`. The new rows under `-n 4`: trimmed-presentation 4.56 / 4.46 s, truncated 2.80-3.02 s.
- **SERIAL** (`--timeout 1200`, alone on the host): **1,257 passed, 11 skipped, 0 failed**, EXIT 0, 2,760 s (w53 2,752 s; WP5.1 2,039 s). The 11 skips are the standing look-check frames archived to D: (as w53). The 300 s faulthandler dump on `test_the_real_photo_leg_reads_and_round_trips_the_owners_photos` is informational (the same dump in w53, 364 s there). Log md5 `aee68c8ad8a9faf252f6ff1a76afc560`.
- **FULLCLIP** (`--timeout 2400`): **7 passed**, EXIT 0, 2,635 s (longer than WP-T6's ~26 min; noted). Log md5 `b68b2c84ca6c9c1af914eef503696885`.
- **Harness gate:** 382 tests OK (1 skipped), 45 s on `5080d652`; re-run on this record's commit (below the Merge heading).

## Dispositions (CHARC's at this accept)

- DR-112 CLOSED by WP-D112, with the experiment's facts; notes F-B4 (a PCM source whose timescale is not 1/sample_rate now refuses) and F-B3 (an earlier frame-aligned packet declaring more than it stores refuses a faithful copy; malformed source, per the ruled wording).
- AD-30 NOTE: the new committed fixture `vid-pcm-irregular`; the D86 exception and run equality.
- F3 noted (the branch is chosen by the source codec; the compressed path is locked).
- NEW DR row for F-B1 (the V4 instrument's PCM reading), paid by a small Codex follow-on after the WP5.3 witness and before the Phase 5 gate report.
- DR-99 (b) recorded (the parallel-leg bench flake above); DR-99 (a) unchanged.
- Fullclip 2,635 s vs ~26 min at WP-T6: noted in the Phase 5 gate report, no row.

## Merge

`main` fast-forwarded to the rebased package plus this record's commit, by the orchestrator. The worktree `.worktrees/wp-d112` is released after the merge (its `work/` pruned only on the owner's word). NEXT: the WP5.3 `clips V-P` re-run from `.worktrees/wp5.3` rebased over this main, the DR-112 witness.
