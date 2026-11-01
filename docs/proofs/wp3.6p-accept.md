# WP3.6P accept record (orchestrator generation 32, 2026-11-01)

**Package:** WP3.6P, real-photo verification on the owner's 73 phone photos: AD-24 on real Apple HEIC against an independent FFmpeg oracle, V5 / D53 / V9 on the RUNNER's output, the Result 2 photo memory leg, the pre-corrected Z/M group reported separately.
- **Brief:** `docs/briefs/wp3.6p-brief.md` (FINAL on CHARC `2e95deaf`; every later ruling folded on the branch, the last CHARC `dbf02ad7` and `e0c7b856`).
- **Lane: CODEX**, `implementer-codex-sol-high`, three sessions, twelve turns (session 1 retired at 240,970 after turn 3; session 2 at 187,455 after turn 7; session 3 compacted after turn 10, 129,440 of 258,400 after turn 12). Both nets Claude (`claude -p --model opus --effort high`), the other model.
- **Report:** `docs/reports/wp3.6p-real-photos.md`. **Ledger:** `docs/proofs/wp3.6p-ledger.md`. **Evidence:** `C:\Users\rwsmy\clearwater-review-evidence\wp3.6p\` (`cell`, `r0-run`, `r1`, `r2`, `r3`, `B`, the rulings).

**Candidate:** branch `wp3.6p` rebased onto main `8e4550e7` = **`6e4b68cc`** plus this record (author head `775a0697` on `c3bf602f`; gated as `33a828f0` on `60a72672`, main's one later commit touches only `docs/charc-state.md`). `git patch-id --stable`: the 13 package commits carry the same 13 patch ids on the author branch, on `33a828f0` and on `6e4b68cc`; the whole package diff is `730f64a12dc2`.

**Footprint** (`git log --name-only main..6e4b68cc`, 5 paths): NEW `tools/photo_verify.py` (subcommands `orientation`, `export`, `memory`), NEW `tests/test_photo_verify.py`, `docs/reports/wp3.6p-real-photos.md`, `docs/proofs/wp3.6p-ledger.md`, `docs/briefs/wp3.6p-brief.md` (rulings folded); plus this record. No `src/` file, no frozen interface, no existing test, no dependency. Every changed blob has 0 CR bytes.

## Nets

| Net | Result |
|---|---|
| Reviewer A round 1 (turns 4-5) | NEW_CRITICAL_MAJOR_FOUND: 2 MAJOR, 6 MINOR, 8 ADVISORY; 13 tool fix groups RED first; CHARC R1-QA/QB ruled. |
| Reviewer A round 2 (turns 6-7) | NEW_CRITICAL_MAJOR_FOUND: 1 MAJOR, 1 MINOR, 8 ADVISORY; 4 tool fix groups and 1 test-only group RED first; CHARC R2-QA ruled. |
| Reviewer A round 3 (turn 8) | **NO_NEW_CRITICAL_MAJOR**, 9 ADVISORY (3 fixed, RED first); executions refused, so CHARC ruled convergence CONDITIONAL on an EXECUTING Reviewer B (`650bea20`). Turn 9 (CHARC `2aaa7e0a`, the odd-width 4:2:0 size equivalence, both crop edges) RED first. |
| **Reviewer B** (Claude pass at the orchestrator's seat on `bf29c8a3`; `clearwater-review-evidence\wp3.6p\B\`) | **NO_NEW_CRITICAL_MAJOR**, 27 turns, `is_error` false, worktree clean; EXECUTED per `650bea20`: E1 `117 passed, 1 deselected`; E2 the planted reader (drop and swap at the product reader, the tool's source reader and the PNG iCCP read) fails `v5_icc_equal` + `d53_primaries` in 18/18 patched runs and passes unpatched; E3 each class mislabel fails `class_layout`. 2 MINOR + 3 ADVISORY, fixed in turn 12 (`775a0697`): B-1 the product size checked against the independent primary size in both branches; B-2 (privacy lock) the EXIF parses quiet under a DEBUG logging config; B-3 a class-check exception carries its own label; B-4 (`clap` ignored, fails closed) and B-5 (tests without the FFmpeg skip fixture) Limits. Seat-verified: the three new tests FAIL on `bf29c8a3`'s tool by name, then `122 passed, 1 deselected`; the 5b-r2 records show `decoded_size` = `ispe` on all 62, so no seat run is affected. No second B (fix-and-test only). |

## Seat runs of record (ledger "Seat-run ledger")

- **5a** `photo_check.py`: 73 read, 0 refused, 0 round-trip problems, 73 ok.
- **5b-r2** orientation (AD-24): 62 HEIC attempted, 0 read failures, **50 pass / 12 inconclusive / 0 fail** (HEIC-0 14 pass, 7 of them by the ruled rounded-size equivalence, / 9 inconclusive; HEIC-90 3/0; HEIC-180 20/0; HEIC-270 13/3); the 12 inconclusive on scene texture, none discordant.
- **5c-8** (representatives) and **5c-16** (all 73, EXCLUSIVE 18:19:13Z-18:27:21Z, 487.7 s): V5 / D53 / V9 pass in all seven classes (HEIC-0 23, HEIC-90 3, HEIC-180 20, HEIC-270 16, JPG-A 2, JPG-Z 8, JPG-M 1), Z and M reported separately.
- **5d** memory, IMG_6690 16-bit, EXCLUSIVE: default GPU device peak 4.11 GB, RSS 1.93 GB, 11.3 s, estimate 6.13 GB; forced CPU RSS 3.14 GB, 58.4 s.
- **q4** the owner-HEIC four-irot test: 1 passed, not skipped.

## Gate

The ONE two-leg gate WITH WP-T7's flags and redirects (`work/orch-g32/gate.sh`; no fullclip leg, the brief asks none), on `33a828f0` (the same patch as the candidate below, which differs only by main's later `docs/charc-state.md` commit), Git Bash, `PYTEST_ADDOPTS` unset, `QT_QPA_PLATFORM=offscreen`, C: 164 GB free at the start, 162 GB at the end; logs `work/orch-g32/gate-p36/` and `gate-p36s/`.
- **Static:** `ruff check` passed; `ruff format --check` 295 files already formatted; `mypy` no issues in 149 source files; 0 CR in every changed blob.
- **Collection:** all **7,505** = parallel 6,256 + serial 1,242 + fullclip 7; no duplicates; union identical to collect-all.
- **Harness gate** (not required by the brief; run): `Ran 382 tests ... OK (skipped=1)`.
- **PARALLEL** (`-n 4 --timeout 600`, stall-watched): **6,255 passed, 1 skipped**, EXIT 0, 481 s (20:02Z-20:10Z). The skip is the standing swscale refusal. Reviewer B of WP5.3 (a Claude pass with its own light pytest) overlapped it. Log md5 `eaf102d16f40372083f601e22fbad8d2`.
- **SERIAL** (`--timeout 1200`, ALONE on the host per the standing rule, stall-watched; no stall reported): **1,231 passed, 11 skipped, 0 failed**, EXIT 0, 1,823 s (20:10:18Z-20:40:42Z). The 11 skips are the standing look-check frames archived to D: (`test_app_v8_v18.py:134` 1, `test_methods_assembly_v8.py:44` 5 + 4, `test_wp41_v8.py:193` 1), the same 11 as WP-T7's gate. The DR-99 node passed. No timeout fired. Log md5 `61fa0d3300c1029ab2dcb7404b8ea361`; junit `work/g32-p36s-serial.xml` in the worktree.

## Dispositions (CHARC's at this accept, per `948caa09`)

- AD-24 status CONFIRMED on 50 discriminating real HEICs across all four irot classes (62/62 attempted, 0 discordant, 12 inconclusive; the tag-only branch unwitnessed).
- DR-42 (a)/(c) and DR-43 notes; a NEW row for EXIF ColorSpace read as untagged; Result 2 photo row closed.
- Two spec items for the owner's next bundle: D63's "provisional" wording; the photo resolution line (24.5 MP max on the owner's photos).
- The B-1 size comparison and the B-2 privacy fix are in the footprint, not rows.

## Merge

`main` fast-forwarded to `6e4b68cc` plus this record's commit, by the orchestrator. The worktree `.worktrees/wp3.6p` is kept until CHARC's accept-side commit lands.
