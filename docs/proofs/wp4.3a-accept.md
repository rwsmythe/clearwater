# WP4.3a accept record (orchestrator generations 22-23, 2026-10-29)

**Package:** WP4.3a, the spawn helper and import / redaction hardening.
- **Brief:** `docs/briefs/wp4.3a-brief.md`, FINAL on CHARC `8fb519bac1878075`; its Rulings govern.
- **Later rulings,** each verbatim in the ledger `docs/proofs/wp4.3a-ledger.md`:
  - `a2ef868a`: the B4 test grant and the redacting WARNING handler;
  - `d6e9abdf`: R1 F1 fixed at the real resolve; F4 GRANTED (the `--parameters` help line); **scope addition R3-1 (ii)**, where a path-valued settings field that cannot be a path takes its default through the per-field rule, never a set-aside.
- **Lane:** CODEX, `implementer-codex-sol-high` (`gpt-6.1-sol`/high), turns driven by `scripts/codex_cell.py`. Commits were made at this seat with the GPT-6.1 Sol footer.
  - Seat 1 retired at input depth 237,170 of 258,400.
  - Seat 2, session `01a18899-4b87-7f51-8850-3b34a92b7076`, ran turns 5-8 and retired at input depth 197,373.
- **Both nets** are the Claude pass (`claude-opus-5-5`/high, read-only), the other model.
- **Report:** `docs/reports/wp4.3a-hardening.md`.

**Candidate:**
- The author branch `wp4.3a` `b7317d7` (base `fe65e6a`, 10 commits) was rebased onto `inv-mc` `3186ea3` (main `27a11ae` plus the inventory refresh) as `stack-g22`, giving the stack top `8e1114a`.
- `git patch-id --stable` is `59a6c0d1` on `fe65e6a..wp4.3a` and on `3186ea3..8e1114a`.
- Every changed blob has 0 CR bytes (`work/gate-g22/cr.log` in the gate worktree).
- **Rebased onto WP4.5 (generation 23).** After the gate below went red on (b), WP4.5 landed
  on main first (`47a08ae`). `stack-g22` was then rebased onto `47a08ae`: the inventory part
  ends at `83668dd` and this package at `24d5a47`. `git patch-id --stable` is unchanged:
  inventory `f977203c` (`27a11ae..3186ea3` and `47a08ae..83668dd`), WP4.3a `59a6c0d1`
  (`3186ea3..8e1114a` and `83668dd..24d5a47`). The stack touches no WP4.5 file.

## Nets

| Net | Result |
|---|---|
| Reviewer A R1 (`fe65e6a..553d1f2`; `clearwater-review-evidence\wp4.3a\r1\`) | `NEW_CRITICAL_MAJOR_FOUND`: 1 major (F1, DR-81 (b) not guarded at the real resolve) / 2 minor / 6 advisory. FIX F1, F2, F3, F9; F4 granted and fixed; F5-F8 report-only Limits. Remediation `c9a7771`, `40eef4e`. md5 review `e5244b65`. |
| Reviewer A R2 (`fe65e6a..40eef4e`; `...\wp4.3a\r2\`) | **`NO_NEW_CRITICAL_MAJOR`**: 0 / 0 / 1 minor (F2 reopened partial) + 4 advisory. **CONVERGED.** One cleanup, `b7317d7`: guard forms widened and the report narrowed to what the guard proves; `OSError` in the settings path check; report and docstring text. The `_field_error` repr leak (pre-existing, frozen IF-10 text) is report-only, and CHARC banks it. md5 review `99cd27d9`. |
| **Reviewer B** (a process at this seat, on `stack-g22` `8e1114a`, base `3186ea3`; prompt built neutrally from the brief plus `d6e9abdf`'s grants, A's findings withheld; `...\wp4.3a\reviewB\`, `md5sums.txt`) | **`NO_NEW_CRITICAL_MAJOR`**: 0 / 0 / 1 minor + 3 advisory. Model ok, 45 turns, worktree clean after, 5 permission denials (sandbox, none a withheld path). Its own runs: 485 passed (package files) and 390 passed (`-n 4`, io/video and the runner). **B1 MINOR** (the `Redactor` misses a non-ASCII known folder spelled with mixed separators, then `repr` and `ascii_text`; no product route produces that spelling) becomes **DR-92** (CHARC). The advisories are record notes: the module docstring does not say the handler sits only on the `clearwater` logger; `test_io_video_spawn.py:306` asserts FFmpeg on PATH where the house pattern skips; `mypy --platform linux` flags `CREATE_NO_WINDOW` at `pipes.py:53` (out of envelope). md5 review `f0f6da17`. |

## Seat checks during the build

- The UNC nodes the sandbox cannot run passed 3 of 3 at this seat on `c9a7771` and on `b7317d7`.
- `ruff format --check` gave 269 at each turn.
- Task 6's light list on `553d1f2`: 884 passed, 12 footage deselected.

## Gate (GATE_CHECKS on `8e1114a`, `.worktrees/stack-g22/work/gate-g22/`, from 17:49:33Z)

- **Static:** `ruff check`, `ruff format --check`, `mypy` and the harness gate (`tests/harness`) each EXIT=0.
- **Collections:** all 6,763 = parallel 5,619 + serial 1,137 + fullclip 7.
- **Parallel leg:** **5,618 passed, 1 skipped, EXIT=0, 1,058.60 s.** The skip is the standing
  `test_color_roundtrip.py:123` swscale refusal.
- **Serial leg:** started 18:08:36Z, released only with every live seat verified idle (WP4.3 cell 6 read 245,094 three times across a turn boundary; both Codex sessions idle; Reviewer B returned). Result: **2 failed, 1,135 passed, EXIT=1, 1,879.08 s** (18:08:36Z-18:39:58Z). Both failures were
  dispositioned without a full serial re-run, under the OWNER's direction (2026-10-29 ~18:47Z,
  verbatim): "full re-run of the serial is not required once the issue with the round-trip test
  is identified and fixed and that test verifies passed (along with any test impacted by code
  changed by the fix)."
  - (a) `tests/test_io_video_encode_bench.py::test_run_once_records_the_row_and_deletes_the_output`:
    `-0.05 < telemetry_origin` read -0.0773, the DR-58 (c) load-sensitive bound. The
    orchestrator's own `du` size scan (18:03-18:16Z) overlapped the timed leg. It PASSED in
    isolation at 18:41Z (gen 22) and again on the rebased stack `24d5a47` (gen 23,
    21:17:11Z, 1 passed in 25.63 s). A load flake caused by the orchestrator's seat, not a
    package fault.
  - (b) `tests/test_photo_check.py::test_the_real_photo_leg_reads_and_round_trips_the_owners_photos`:
    `IMG_6791.JPG` `Exif.LensModel` changed. It failed on main `27a11ae` too (pre-existing; the
    owner's new Phone photos exposed it). Fixed by **WP4.5** (record
    `docs/proofs/wp4.5-accept.md`, main `47a08ae`), whose gate ran the full parallel leg and
    the impacted serial nodes. Re-run on the rebased stack `24d5a47`: **1 passed in
    260.24 s** (21:12:11Z-21:16:33Z).
- **Basetemps:** removed after this record (CHARC's disk rule, 2026-10-29). The gate logs are
  copied to `clearwater-review-evidence\stack-g22\`.

## Notes for CHARC's post-merge commit

- AD-13 note; AD-23 "applied by WP4.3a".
- Closures: DR-58 (b), DR-76, DR-77, DR-81 (a)-(d) plus the WARNING route, DR-85.
- New rows: DR-92 (Reviewer B1) and the IF-10 `_field_error` repr leak (trigger: the next IF-10 touch, or any consumer printing set-aside reasons unredacted).
- The brief's register table gains the R3-1 (ii) line.
- WP4.3's DR-85 `xfail(strict)` is dropped when WP4.3 rebases onto this merge.
