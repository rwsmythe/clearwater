# WP-D54 accept record (orchestrator generation 30, 2026-11-01)

**Package:** WP-D54, the encoder's assumed-colour-tags warning names BT.709 and the resolved range in words (spec 5.4 / D54 / V6), found by WP5.1's G4 (T6-1).
- **Brief:** `docs/briefs/wp-d54-brief.md` (FINAL on CHARC `3a1497d6`; the text `377fcd25`; amended by the round-1 ruling `26f0d3d0` (two-branch sentence by the resolved range) and the Reviewer B ruling `ff35ab68`, both folded on the branch).
- **Lane: CODEX**, `implementer-codex-sol-high`, one session (`01a19680-681b-7e73-9fa1-893bc1fdefaa`), five turns; depth after turn 5: 159,066 of 475,000. Both nets Claude (`claude -p --model opus --effort high`), the other model.
- **Report:** `docs/reports/wp-d54-warning-words.md`. **Ledger:** `docs/proofs/wp-d54-ledger.md`. **Evidence:** `C:\Users\rwsmy\clearwater-review-evidence\wp-d54\` (`cell`, `r1`, `B`, the rulings). The report and ledger name the pre-rebase commit ids; the map is below.

**Candidate:** branch `wp-d54` rebased onto main `1271cf6d` = **`e043141f`** plus this record. The gate ran on the same patch rebased onto `1a6c7649` (`fcb96280`); main's later commits (`55d91489`, `0eaba2f8`, `c81831f9`, `fe9dcfe1`, `1271cf6d`) touch only `docs/charc-state.md` and `docs/debt-register.md`. `git patch-id --stable` over the package diff excluding the brief: **`c0c944a44e84`** on the author branch (`819d0efe..0a14874a`), on `fcb96280` and on `e043141f`.

**Commit map (author branch -> gated -> merged):** RED `549b4ca4` -> `28c9a11a` -> `d9b67b37`; fix `4aae3824` -> `6e27ac98` -> `691ac34d`; clean-up `5fa56fc4` -> `5691944f` -> `16703d89`; report `cc9f3d44` -> `f48cbc8b` -> `12d83a1e`; Reviewer B rows `0a14874a` -> `1767de3c` -> `ac0eff78`.

**Footprint** (`git diff --name-only main..e043141f`, 5 paths): `src/clearwater/io/video/encode.py` (the helper `_assumed_color_warning` and its one call site), `tests/test_io_video_encode.py`, the brief, the ledger, the report; plus this record. No `probe.py`, `jobs/export.py`, `gui/`, interface, dependency or lock change. Every changed blob has 0 CR bytes (5 of 5 checked).

## The sentence (two branches by the resolved range)

LIMITED: "The source's colour tags are missing or unexpected; Clearwater assumed BT.709 colours and limited range for the missing or unexpected ones, and the output is tagged with these values (<computed codes>)." FULL (a range tagged `pc` or derived from a `yuvj` format, never defaulted): the same without "and limited range". The parenthesis is computed from the probe's description as before.

## Nets

| Net | Result |
|---|---|
| Reviewer A round 1 (Claude pass, `clearwater-review-evidence\wp-d54\r1\`) | Converged in one round; the clean-up (`5fa56fc4`, CHARC `26f0d3d0`: the range clause follows the resolved range; rows pin the parenthesis and one warning) as the terminating step. |
| **Reviewer B** (Claude pass at my seat on `cc9f3d44`, base `819d0efe`; the report and ledger WITHHELD via `run_review_B.py`; `clearwater-review-evidence\wp-d54\B\`) | **NO_NEW_CRITICAL_MAJOR**; model `claude-opus-5-5`, `is_error` false, 25 turns, worktree clean; EXECUTED first: 100 passed, 19 deselected. F1 MINOR (no SINK-level test reached the FULL branch; B's planted `_prepare` wrapper passed the file) and F2 ADVISORY (no "no warning when not assumed" row): FIXED by turn 5 (`0a14874a`, two sink-path rows). F3 / F5 advisory: notes for DR-102. F4 OUT OF ENVELOPE (the probe's open-path `missing_tags` text says "limited range" for an untagged `yuvj` source whose resolved range is FULL): DR-107 (CHARC). No B re-run for the test-only turn (CHARC `ff35ab68`). |

**Verification QA at my seat (the evidence `ff35ab68` asks for):** B's two mutants applied in-process to `FFmpegVideoSink._prepare` over the whole light file on `0a14874a` (`uv run pytest -q tests/test_io_video_encode.py -m "not gpu and not footage and not gui and not fullclip"`, plugin `d54_mutant.py`): `drop_full` (remove the colour warning when the resolved range is full) -> **1 failed** (`test_d54_sink_preparation_warns_once_for_assumed_yuvj_full_range`), 101 passed, 19 deselected in 112.93 s; `warn_tagged` (add a colour warning for a non-assumed source) -> **1 failed** (`test_d54_sink_preparation_does_not_warn_for_tagged_source`), 101 passed, 19 deselected in 106.20 s. Unmutated: 102 passed (the cell's run; the gate below).

## Gate

The ONE two-leg gate on `fcb96280` (base main `1a6c7649`), run id `g30-wpd54`, Git Bash, `PYTEST_ADDOPTS` unset, `clearwater.local.toml` copied, C: 171 GB free at the start, 168 GB before serial attempt 2.
- **Static:** `ruff check` passed; `ruff format --check` 292 files already formatted; `mypy` no issues in 148 source files; 0 CR in every changed blob.
- **Collection:** all **7,381** = parallel 6,133 + serial 1,241 + fullclip 7.
- **PARALLEL:** **6,132 passed, 1 skipped**, EXIT 0, 413 s (10:57Z). The skip is the standing swscale refusal. Log md5 `4e400f5ffc8c874ebfff027d9e3eefe7`. Two Codex adjudication turns (WP5.1 t11, WP5.3 t6) overlapped it.
- **SERIAL attempt 1: HUNG** at node 242, `tests/test_gui_export_panel.py::test_failure_is_an_error_naming_the_file_with_owner_export` (inside `rig.wait_export_idle()`, offscreen, no child process) from ~11:09Z until found at 17:18Z; killed 17:21Z. Two Codex remediation turns (WP5.1 t12, WP5.3 t7) were running their light suites at the hang. The module alone passed 3/3 (37 passed, ~5.6 s each). No stack (a py-spy attach was refused by the permission layer). Log md5 `cd96ca565b7bb6454ae951d0cd2bd9ec`. **DR-108** (the deadlock) and **DR-109** (no per-test timeout; WP-T7 commissioned) by CHARC at `c81831f9`; the gate-side six-hour watch miss is recorded in DR-108. Not this package's footprint.
- **SERIAL attempt 2 (of record), ALONE on the host** (CHARC's standing rule from `97d5abbf`: no other pytest during a serial leg), with a 5-minute stall watch: **1,230 passed, 11 skipped, 0 failed**, EXIT 0, 1,606 s (17:21:17Z-17:48:04Z). The 11 skips are the standing look-check frames archived to D: (`test_app_v8_v18.py:134` 1, `test_methods_assembly_v8.py:44` 5 + 4, `test_wp41_v8.py:193` 1), the same 11 as WP4.6's gate. The DR-99 node passed. Log md5 `9dcc4eb9917cd1c825787a296f62e185`; junit `work/g30-wpd54-serial2.xml` in the worktree.
- **FULLCLIP:** not run (the brief asks none). **Harness gate:** not required (no `scripts/`, `.claude/`, kernel doc or `tests/harness/` change).

**WITNESS:** after this merge, WP5.1's `tests/test_v51_video_acceptance.py::test_v6_untagged_runner_warns_bt709_limited` on the `wp5.1` worktree rebased over the merged main, at my seat (not a figure of record); the result is posted to CHARC with this accept.

## Dispositions

- **CHARC's at this accept:** DR-102 CLOSED (the D54 wording defect; both branches named; F2 / F3 / F5 as notes); NEW DR-107 (F4, the probe's open-path text for a full-range `yuvj` source; trigger: the next touch of `io/video/probe.py`).
- Limits carried in the report: the sentence does not name which fields were assumed (IF-1 `ColorDescription` carries only `assumed`); the probe's own `missing_tags` fault is still not forwarded (one warning, by ruling).

## Merge

`main` fast-forwarded to `e043141f` plus this record's commit, by the orchestrator. The worktree `.worktrees/wp-d54` is kept until CHARC's accept-side commit lands.
