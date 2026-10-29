# WP-T6 accept record (orchestrator generation 21, 2026-10-29)

**Package:** WP-T6, Gate test sizing (AD-30).
- Brief: `docs/briefs/wp-t6-brief.md`, FINAL on CHARC `7458b470a82d2dc3`; its "Rulings" govern.
- Later rulings, each verbatim in the ledger:
  - `5b9dd6b0` (R-a..R-d);
  - `42a1be58` (R-e, the rung-3 V4 check);
  - round 0 `22065ec5` (all seven rows CUT, R4 to six frames);
  - re-seat `6f5ebd09`;
  - W2 controls `ce2069c5`;
  - W3 `c80aacc9` (branch (i));
  - Reviewer B dispositions `7c59772d`.
- The W3 Limit, in CHARC's words: "the trim form proves V4 MANDATORY and REQUIRED; three best-effort container items are proved by the fullclip form only".
- Dispatcher grant (CHARC concurred): `load_local_config` dropped from `tests/test_io_video_encode.py:48` (ruff F401 after the cuts).
- Lane: **CODEX**, `implementer-codex-sol-high` (`gpt-6.1-sol`/high), turns driven by `scripts/codex_cell.py`. Commits were made at the orchestrator's seat with the GPT-6.1 Sol footer.
  - Seat 1, session `01a18757-...`, retired at turn 5 (input depth 202,787 of 258,400).
  - Seat 2, session `01a18792-c6d5-71d2-b978-6c9adbb7591e`, ran turns 6-14 and stood down after turn 14. Its input depth was 81,979 at the end; the session compacted twice.
  - Codex pace was 0.51 at commission and 0.587 at 14:44Z on the accept day.
- Both nets are the Claude pass (`claude-opus-5-5`/high, read-only), the other model.
- Report: `docs/reports/wp-t6-gate-sizing.md`. Ledger: `docs/proofs/wp-t6-ledger.md`.

**Candidate:**
- **Gated tree:** branch `wp-t6-mc` at `a4472fb` (kept as `wp-t6-mc-gated`) = the author branch `wp-t6` `e2dc969` rebased onto main `5fdcda4` with `git -c core.autocrlf=false`. `git patch-id --stable` is `a7a7d115` on `6ecc4e5..e2dc969` and on `5fdcda4..a4472fb`, 21 commits each.
- **Merged tree:** `wp-t6-mc` = the author branch `4c6684c` (turn 14, docs only) rebased onto main `5e1fe8f` (a CHARC docs move), then this record.
- **Code identity with the gated tree:** the code patch-id (`-- src tests tools pyproject.toml`) is `2db04036` on `5fdcda4..a4472fb` and on `5e1fe8f..wp-t6-mc`. `git diff a4472fb wp-t6-mc` touches only `docs/reports/wp-t6-gate-sizing.md`, `docs/proofs/wp-t6-ledger.md` and main's `docs/charc-state.md`.

**Footprint (checked at this seat):**
- `tests/conftest.py`: ADDITIVE only (518 lines added, 0 changed); every pre-package line is byte-identical. Module-level imports added are stdlib only.
- `tests/test_jobs_export_video.py` (R1), `tests/test_io_video_encode.py` (R2, R3, and the F401 grant), `tests/test_color_roundtrip.py` (R4) and `tests/test_io_video_decode_hw.py` (R5-R7 and the parity test).
- `pyproject.toml`: the one `fullclip` marker line.
- The report and the ledger.

**Locks, all held:**
- Nothing under `src/` or `tools/`. `uv.lock` unchanged, no new dependency. No test deleted.
- Every changed blob has 0 CR bytes.
- The trim is written only under the session temp root and is removed at teardown.
- Every window wrote only under `work/`. The footage folder was read only.
- No `gpmd` content was decoded; data packets were compared by pts, size and hash only. No location tag value is in any committed file.

## Nets

| Net | Result |
|---|---|
| Reviewer A R1 (the Claude pass, on `6ecc4e5..04b01d2`; `clearwater-review-evidence\wp-t6\r1\`) | `NO_NEW_CRITICAL_MAJOR`: 0 / 0 / 3 minor + 8 advisory. ONE cleanup (turn 12: F3 cut-on-keyframe sub-result, F2 data count to T, F11 docstring, report wording), re-proved by W2b. Converged under Q11 with no round 2. md5 review `68b2ac99`. |
| **Reviewer B** (the Claude pass, a process at this seat, on `wp-t6-mc` `a4472fb`, base `5fdcda4`; prompt built neutrally from the brief; `clearwater-review-evidence\wp-t6\reviewB\`, `md5sums.txt`) | **`NO_NEW_CRITICAL_MAJOR`**: 0 / 0 / 1 minor + 9 advisory. Model ok, 36 turns, worktree clean after; 8 permission denials, all sandbox refusals and none a withheld path. B1 (the fixture checks the plan's own T; the parity test re-derives T and fails a later-keyframe plan in the same serial leg) is REPORT-ONLY with a report Limit; CHARC writes its DR row. B3 FIXED in the report (43.58 s). B4 DECLINED. B2/B9 REPORT-ONLY. B5-B8 out of envelope or stated Limits. B10: W2b's 60 passed stands. CHARC concurred with all of these (`7c59772d`). md5s: review `ff96cce0`, prompt `92d44bf8`, diff `953355a8`. |

## Windows at this seat (generation 21)

- **W2b** (`work/wp-t6/w2b.sh`, md5 `273352e4`; 14:27:13Z-14:28:28Z), on the cleaned checker. `W2b DONE`:
  - parity 1 passed;
  - guard 60 passed;
  - four controls each caught by name: re-encode by 4b/4d/4e; extra frame by 4b/4c; N=75 non-keyframe by `4c_cut_on_keyframe`; truncated data by the data-packet count to T;
  - cleanup clean.
- Earlier windows (W2 runs 1-3, W3 runs 1-2, W4: 7 fullclip passed in 1,556.05 s) are in the ledger.

## Gate (GATE_CHECKS on the gated tree `a4472fb`, `.worktrees/wp-t6-mc/work/gate-g1/`, 14:43:42Z-15:23:27Z)

The serial leg was held from 14:56Z to 15:00Z until the only other live cell (WP4.3 cell 4) was verified idle, so nothing else ran on the host during the timed leg.

- **Static:** `ruff check` passed; `ruff format --check` 267 files already formatted; `mypy` no issues in 141 source files.
- **Collections:** each EXIT 0; node-ID lines equal pytest's counts; no duplicates.
  - all **6457** = parallel **5313** + serial **1137** + fullclip **7**;
  - pairwise disjoint; the union equals all;
  - **against main's 6449:** the 7 removed IDs are exactly R1-R7 in their unparametrised form; the 15 added are their `[trim]`/`[full]`/`[first6]`/`[first30]` forms plus `test_the_gx011627_trim_is_a_stream_copy_of_the_source`.
- **PARALLEL** (`-n 4 -m "not gpu and not footage and not gui and not slow and not fullclip"`): **5312 passed, 1 skipped, EXIT 0, 714.41 s**. The skip is the standing `test_color_roundtrip.py:123` swscale yuvj refusal. 9.09 GB available before the leg.
- **SERIAL** (`-m "(gpu or footage or gui or slow) and not fullclip" --durations=0 --junitxml`), the AFTER figure: **1136 passed, 1 skipped, EXIT 0, 1,389.24 s** (junit 0 failures, 0 errors). The skip is the standing `test_photo_check.py:139` no-photos one. 9.66 GB available before the leg.
- **Q6 PASS (the report):** the seven CUT rows went from 1,567.37 s (setup+call) to 281.236 s (setup+call+teardown), a conservative reduction of **1,286.134 s**, against the 110 s bar. The serial leg wall went from 2,621.32 s to 1,389.24 s (−1,232.08 s, −47.00 %). The 900 s target was not reached (+489.24 s); it is informational under Q7.
- **Harness gate** (`uv run python -m unittest discover -s tests/harness`) on the gated tree: Ran 382 tests, OK (skipped=1). On the merged tree: see below.
- **CR blob check:** 0 CR bytes in every file of `git diff --name-only <main>..wp-t6-mc`.

## Owed at the accept (CHARC, per its standing list)

- The fill's GATE_CHECKS two-leg expressions gain `and not fullclip`, with the `fullclip` window form. CLAUDE.md and AD-28 figures: serial leg about 1,389 s, and the two-leg wall about 35 min.
- Q7's gap row, the row-10 DR row, and the DR-22/DR-66 notes.
- **B1's DR row:** trigger is the next touch of the `gx011627` fixture; the remedy is to pass `cut_text=None` beside the plan's T, or to assert the plan's T equals the derived one inside the fixture.
- Follow-on already listed by CHARC: the Codex micro-package on `tools/prototype/bench.py:1305` `stray_processes`.
