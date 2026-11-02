# WP-DR113 accept record (orchestrator generation 35, 2026-11-02)

**Package:** WP-DR113, the V4 fidelity instrument reads a raw PCM audio stream by its sample extent and timeline runs (a fourth equivalence beside WP4.4's three), so a faithful re-chunked PCM export reads SAME (DR-113: WP-D112's Reviewer B finding F-B1; the instrument still compared PCM per packet and read the owner's faithful IMG_6731 export DIFFERENT on two MANDATORY items).
- **Brief:** `docs/briefs/wp-dr113-brief.md` (FINAL `dc018f25`; CHARC no-tripwire ruling `001d01e4`).
- **Lane: CODEX**, `implementer-codex-sol-high`, two sessions, five turns (session 1 `01a19bc4-...` turns 1-2, retired at 216,276; session 2 `01a19bd8-3481-7ec3-b790-975d7bc645a2` turns 3-5, at **169,816** after turn 5). Both nets Claude (`claude -p --model opus --effort high`), the other model.
- **Report:** `docs/reports/wp-dr113-v4-pcm.md`. **Ledger:** `docs/proofs/wp-dr113-ledger.md`. **Evidence:** `C:\Users\rwsmy\clearwater-review-evidence\wp-dr113\` (`cell`, `r1`, `B`).

**Candidate:** branch `wp-dr113`, rebased onto main `6aa77d61` and gated as **`2ef05dd9`**; `git patch-id --stable` over the 7 package commits equal before and after the rebase (`work/orch-g35/dr113-patchid-before.txt`, `-after.txt`). This record's commit adds this file and fills the report's GREEN witness, Reviewer B and Gate lines and its B-A3 Limit (docs only); the harness leg re-ran on it (below).

**Footprint** (`git diff --name-only main..wp-dr113`, 8 paths plus this record): `tools/container_spike/compare.py` (the PCM packet item, its width table and helpers); `tools/video_fidelity.py` (`_cut_items`' audio branch, the side-data item, `notes` with stream keys); `tests/test_container_spike_compare_equivalences.py` (53 new nodes, the agreement rows; the shared `_facts` helper gained `"sample_fmt": "s16"`, disclosed); `tests/test_video_fidelity.py` (7); `tests/test_io_video_encode.py` (the real-sink derivative row, 5 parametrisations); the brief, report and ledger. All owned files; no product module, no fixture, no dependency, no frozen interface. Every changed text blob 0 CR and ASCII.

## Nets

| Net | Result |
|---|---|
| Round 0 (turn 1) | anchors, consumers, note form, width table, RED list; orchestrator rulings R0-1..R0-3 (ledger). |
| RED -> GREEN | `a7e99af0` (28 of 57 new nodes RED, 29 baseline GREEN) -> `b48c94b3` (all 57 pass). |
| Reviewer A round 1 (`b48c94b3`; `...\r1\`) | **NO_NEW_CRITICAL_MAJOR**, CONVERGED; 2 MINOR, 6 ADVISORY. Terminating clean-up turn 4 (`586d08f2`): M1 disclosed; M2 agreement rows added (first pts + 1, shift-after-30, all-zero, negative / missing / fractional evidence); A4 note wording and A5 stream keys adopted; A3, A6, A7 report Limits; A8 measured (real-sink rows 2.8-3.5 s, no `slow` marker). |
| **Reviewer B** (Claude pass at the orchestrator's seat on `fc167059`; `...\B\`) | **NO_NEW_CRITICAL_MAJOR**, 45 turns, `is_error` false, worktree clean after; light run 121 passed. Base-vs-head on the committed AAC fixtures: items, notes and records identical; on `pcm-irregular.mov` only the two target items changed. 5 ADVISORY, 0 MINOR: B-A1 a PCM source whose output has NO matching audio track reads DIFFERENT (correct) with the unknown-width note; B-A2 side-data refusal notes carry no stream key (cosmetic; the item's name identifies the track); B-A3 the side-data rule reads source rows inside the readable window only for a cut source (defensible: the later packets are never copied); B-A4 the agreement rows omit WP-D112's cut-window shapes (straddle, after-window missing, one-fewer at 55/70/85 %, same-prefix, slack), probed through both readings: all agree except the disclosed A6 slack case; B-A5 the `rate` and `channels` controls pass on any DIFFERENT and do not pin the PCM item's refusal. All BANKED (report Limits line added for B-A3; the rest notes under the DR-113 close). |

## Gate

The THREE-leg gate (fullclip per the brief's GATE_CHECKS: the fullclip nodes build V4 records through `fidelity_record`, so they reach the changed reading), WP-T7's flags and redirects (`work/orch-g35/gate.sh`), on `2ef05dd9`, run id `dr113`, Git Bash, `PYTEST_ADDOPTS` unset, `QT_QPA_PLATFORM=offscreen`; no window open and no build piece during any leg; during the PARALLEL leg only WP5.2's ledger-only Codex turn ran (no pytest); serial and fullclip alone on the host; stall watch armed throughout (no stall). C: 89 GB free at the start.
- **Static:** `ruff check` passed; `ruff format --check` 306 files already formatted; `mypy` no issues in 154 source files.
- **Collection:** all **7,851** = parallel 6,573 + serial 1,271 + fullclip 7; no duplicates; union identical to collect-all.
- **PARALLEL** (`-n 4 --timeout 600`): **6,572 passed, 1 skipped, 0 failed**, EXIT 0, 511 s. The skip is the standing swscale refusal (`test_color_roundtrip.py:123`), as at d112. Log md5 `c1a75c32ea508c045f85c9ed89a70f3f`.
- **SERIAL** (`--timeout 1200`): **1,260 passed, 11 skipped, 0 failed**, EXIT 0, 2,036 s. The 11 skips are the standing look-check frames archived to D: (as d112). Log md5 `78766a2637d82daa78ca86e7c1b32670`.
- **FULLCLIP** (`--timeout 2400`): **7 passed**, EXIT 0, 1,595 s (d112 2,635 s; WP-T6 about 26 min). A faulthandler stack dump at the long node is informational (as at d112). Log md5 `3e6324435dc036cfaa89346cefce0bc5`. C: 84 GB free at the end (12:43:58Z).
- **Harness gate:** 382 tests OK (1 skipped), 23 s on `2ef05dd9`; re-run on this record's commit (below the Merge heading).

## Dispositions (for CHARC at this accept)

- DR-113 CLOSES with the GREEN witness below (CHARC's act); notes B-A1, B-A2, B-A4, B-A5 (banked advisories) and the report's Limits (F-B2 no sample-content comparison; A3; A6; A7).
- No new DR row proposed.

## GREEN witness (DR-113's close evidence)

At the orchestrator's seat, 2026-11-02 ~12:50Z, from `.worktrees/wp-dr113` at the gated candidate `2ef05dd9` (the instrument's code is that of this merge): `uv run python tools/video_fidelity.py compare C:\Users\rwsmy\clearwater-footage\Phone\IMG_6731.MOV C:\Users\rwsmy\clearwater\work\wp5.3\clips\IMG_6731_corrected.mp4 --out C:\Users\rwsmy\clearwater\work\wp3.10\dr113-green` = **EXIT 0; 46 items; DIFFERENT by class MANDATORY 0, REQUIRED 0, BEST-EFFORT 9; MANDATORY + REQUIRED all SAME; notes 1** (`PCM: compared by sample extent and timeline runs; packets 100 -> 99 [soun#0]`). Against the RED of record (`work\wp3.10\dr113-red`: MANDATORY DIFFERENT 2, BEST-EFFORT 9) the 46 item names are identical and exactly two statuses changed, DIFFERENT -> SAME: `audio packets passed through (pts, duration, size, MD5) [soun#0]` and `audio priming and packet side data`. The nine BEST-EFFORT differences are unchanged. Record md5s: `.compare.json` `d7f214df0696ce541815585849f1ebe2`, `.compare.md` `71fb308a0c056f77b102bcf7908bc97f`. The report's section 'The finding it pays' carries the same figures.

## Merge

`main` fast-forwarded to the rebased package plus this record's commit, by the orchestrator. The worktree `.worktrees/wp-dr113` is released after the merge (its `work/` pruned only on the owner's word). NEXT: CHARC closes DR-113 on the GREEN witness above; WP5.2's EXCLUSIVE windows may open (nothing of WP-DR113 runs).
