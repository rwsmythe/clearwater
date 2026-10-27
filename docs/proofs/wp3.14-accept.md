# WP3.14 accept record (orchestrator generation 14, 2026-10-27)

**Package:** WP3.14 export jobs and batch, brief `docs/briefs/wp3.14-brief.md` (FINAL, CHARC `3c3c35d7e40b525e`; Q2
AMENDED by CHARC `e7d25105`, in the brief at `2fea775`). Lane: **Claude**, `implementer-opus-high`, four seats (cells
1-4). Both nets are the CODEX pass (gpt-6.1-sol / high, read-only). Report `docs/reports/wp3.14-export-batch.md`;
ledger `docs/proofs/wp3.14-ledger.md`.

**Candidate:** branch `wp3.14-mc`, the author branch `wp3.14` (`1449a77`, base `9753b7b`) rebased with
`git -c core.autocrlf=false` onto main `bdb63cc` (`2b27454`, full pytest and static) and again onto `fed6900` (`c9da9ce`; this record on top);
26 commits; `git patch-id --stable` `9ef47483` on `9753b7b..wp3.14` and on both candidate ranges. `git diff 2b27454
c9da9ce -- src tests tools` touches `tests/harness/test_codex_cell.py` only (CHARC's harness item; excluded from pytest),
so the suite ran on this code. Reviewer B pass 1 ran on
`b830412` (author `dc76d92`), pass 2 on `99171df` (author `b4259cc`); the commits since pass 2 are the gate fix
`bcc7fa3` (below) and docs only (`2e1dc11`, `1449a77`).

**Footprint (checked at this seat):** `src/clearwater/jobs/` `export.py`, `batch.py`, `provenance.py` (new),
`disk_space.py`, `__init__.py`; `tools/export_bench.py` (new); tests `test_jobs_export.py`,
`test_jobs_export_support.py`, `test_jobs_export_photo.py`, `test_jobs_export_video.py`, `test_jobs_batch.py`,
`test_jobs_disk_space.py`, `test_export_bench.py`; the report and the ledger; and ONE GRANTED edit outside the package
(below). 16 files. Nothing under `src/clearwater/interfaces/`, `pyproject.toml`, `uv.lock`; `io/video/encode.py` NOT
edited (Q2 amended condition 3). Every changed blob has 0 CR bytes. Nothing footage-derived committed; no location tag in
any committed record.

**GRANTED edit outside the package:** `src/clearwater/analysis/engine.py` (origin WP3.11), the decode pass's `finally`
close only (`d501754`; CHARC `d9154e06`, Reviewer B pass 1 B1 (b)): a raising `close()` is a WARNING log line and the
original outcome is kept. **Style debt (CHARC `58cb06ed`, no DR row):** the fix imports `logging` inside the `except`
block; move the import to the module header at WP3.11's next touch of `analysis/engine.py`.

## Nets

| Net | Result |
|---|---|
| Reviewer A R1 (Codex pass at the cell's seat, `wp3.14\r1\`) | head `7bb5d85`: 0 / 2 / 6, all in envelope, all new; `NEW_CRITICAL_MAJOR_FOUND`. F2-F8 fixed failing-first (`095a345`, `02324a7`); F1 (a) fixed; F1 (b) (watchdog through `close()`) needed Q2 AMENDED (CHARC `e7d25105`), built in `c3a2fc9` with its five conditions |
| Reviewer A R2 (`wp3.14\r2\`) | head `c3a2fc9`: 0 / 1 / 7. G1 (a)/(b) and G2 ruled NOT DEFECTS (a `BaseException` propagates by design; reproduction `r2\f1-repro.txt`), CHARC told; ZERO new blocking: the loop TERMINATED, no R3. G3-G8 fixed once as cleanup (`756da22`, `04822ef`) |
| **Reviewer B pass 1** (Codex at this seat, `wp3.14\reviewB\`) | on `b830412`: `VERDICT: BLOCKING (2 critical/major)`; banner gpt-6.1-sol / high / read-only; 0 `^ERROR`; 19 "succeeded in"; tokens 167,472; no withheld path read. md5s `reviewB\md5sums.txt` (`review-B.txt` `112631230b6dfae2b2f326ae285cdfcc`) |
| **Reviewer B pass 2** (`wp3.14\reviewB2\`, the ONE re-run) | on `99171df`: BLOCKING, 1 major (F1) + 2 minor + 1 advisory; all four pass 1 remedies HOLD; banner gpt-6.1-sol / high / read-only; 0 `^ERROR`; 36 "succeeded in"; tokens 186,894. md5s `reviewB2\md5sums.txt` (`review-B.txt` `9a621a5261b56026b54553595377248f`) |
| Candidate full pytest (this seat, `2b27454`, offscreen, main's configuration) | 5056 passed, 2 skipped (the two standing skips: `test_color_roundtrip.py:121`, `test_photo_check.py:139`; the 9 `test_methods_assembly_v8` look-check skips of the cell's worktree now RUN), 4568.09 s, EXIT=0 (17:30Z-18:46Z) |
| Static (this seat, `2b27454`) | ruff clean; format 237; mypy 136 clean |
| Harness gate (this seat) | 382 OK (skipped 1), on `c9da9ce` |

**Reviewer B pass 1 rulings (orchestrator, upheld by CHARC `c9838cd`):**
- B1 MAJOR (EXECUTED): in the cold analysis pass a method failure or a cancel followed by a raising stream `close()`
  became "analysis failed: OSError: ...". Split: (a) the cancel half FIXED in `export.py` (a cancel is read from
  `progress.cancelled()`, not the failure constant); (b) the method-failure half FIXED by the granted `engine.py` edit
  above.
- B2 MAJOR (every V16 row OWED): DECLINED as sequencing. V16 is ladder item 10, run LAST in exclusive windows after the
  B pass; the rows are now recorded (below).
- B3 MINOR: a raising callback after `commit()` failed the job. FIXED: post-commit hooks guarded (WARNING), the result
  stays ok, the claim text made true.
- B4 ADVISORY: `Fraction(1.10)` gained a byte. FIXED: exact Fractions, oracle independent.

**Reviewer B pass 2: adjudicated AT THE GATE** (the second blocking B, per the standing practice; CHARC UPHELD,
`58cb06ed`):
- F1 MAJOR (EXECUTED): no cancel check between the photo path's "Writing" report and `SafeWrite`/the writer; a cancel
  then a writer ENOSPC returned a disk-full failure in place of `CANCELLED` (nothing left on disk; the label wrong).
  **Gate fix `bcc7fa3`:** `_check_cancel` after the report, and the amended-Q2 rule on the photo path (an `Exception`
  from begin/write/commit while `cancelled()` is True becomes `CANCELLED`, its text on an INFO line). **Verified by
  execution at this seat:** with the pre-fix `export.py` (`b4259cc`) swapped into the candidate, both new tests FAIL
  with B's exact defect ("the photo writer ran after a cancel"; "failure is not the CANCELLED constant: '... disk full
  ...'"); restored, they pass (touched files 128 passed; ruff, format, mypy clean).
- F2 MINOR (the per-item D87 batch test could pass on a provenance `TypeError`): FIXED. F3 ADVISORY (no clean-path test
  for the granted close guard): ADDED with a planted control. F4 MINOR (the report's scope line denied the `engine.py`
  edit): FIXED (`2e1dc11`).
- No B pass 3.

## V16 (ladder item 10; exclusive windows, OPEN/CLOSE posted to CHARC)

Block 1 11:33:36Z-12:57:47Z, block 2 13:05:12Z-17:25:11Z, head `2e1dc11` (product identical to the candidate). Every run
ok, every frame written, exit 0; no foreign stray process; 0 telemetry errors.

| Run | s/frame | min/min (D106 interim 25) | Analysis share | Peak RSS / GPU |
|---|---|---|---|---|
| GX011627 c3 cold x3 | 1.061-1.065 | 31.8-31.9 **MISS** | 30 % | 2.8 / 2.4 GiB |
| GX011627 c3 warm | 0.774 | 23.2 meets | 3.6 % | 2.8 / 2.4 GiB |
| GX011627 ancuti2018 cold | 0.720 | 21.6 meets | 41 % | 2.8 / 2.4 GiB |
| GX011627 c3 libx265 cold | 1.188 | 35.6 **MISS** | 27 % | 4.0 / 1.9 GiB |
| synthetic 5.3K 8:7 c3 cold | 4.539 | 136 **MISS** | 17 % | 6.2 / 6.0 GiB |
| GX011625 c3 cold, sustained (14,938 frames, 4 h 20 min) | 1.043 | 31.26 **MISS** | 29.8 % | 2.9 / 2.4 GiB |

**D106's interim 25 min/min is MISSED on cold c3 at 4K, as measured (31.3-31.9 min/min).** CHARC `7ce2b89f` and
`6801b8bc`: a measured figure for WP3.21, NOT a stop and NOT a product defect (V16 is tunable; D106 names WP3.21 and
the WP5.2 re-measure; the brief's item 10 is best effort and its Done clause is "the V16 row recorded in an exclusive
window", met). Carried forward as WP3.21's baseline:
1. The split: cold c3 = the analysis pass (about 30 %) + the frame path at about 0.74 s/frame; warm c3 and ancuti2018
   meet. The frame path alone is within D106 at 4K; the cold miss is the analysis pass plus the c3 cost (consistent with
   WP3.10's floor row). **WP3.21's first question:** where the analysis pass spends its ~0.31 s/frame (decode,
   host-side statistics, upload), measured before any device-resident work. Through GX011625's 77-minute analysis phase
   the GPU sat at idle clocks (median SM 210 MHz, 5.1 W): the pass is not GPU-bound. Then D106's list: overlap with
   export, device-resident analysis, the 3C Gaussian.
2. libx265 (35.6, a 14.0 s close against about 0.6 s with NVENC): the CPU fallback path, not the measured mode; no action.
3. 5.3K 8:7: "supported, best-effort on speed" (D106); N4's 16 GB respected; first frame 10.6 s.
- The two "Not carried to the output" warnings per output (firmware tag, camera settings atoms) are D86 / WP3.10 sink
  behaviour as designed.
- GX011625 thermals did not degrade (frames-phase median 0.755 s/frame first hour, 0.726 last hour); GPU peak 93 C.
- D87 at Standard: GX011627 105,909,120 B, GX011625 2,323,157,760 B (both ceiling-bound); each covers its output.

## Cell depths (dispatcher-read, `scripts/cell_depth.py`)

| Seat | Depth |
|---|---|
| Cell 1 (round 0 through dispatch of A) | 238,362 at retirement (164,553 at the round-0 yield) |
| Cell 2 | about 208K at retirement |
| Cell 3 (R1, R2, cleanup, report) | 123,184 at R1; 255,161 at R2; 302,881 at retirement (168 turns) |
| Cell 4 (B remediation, gate fix, V16, FINAL) | 38,603; 146,307; 183,062; 202,398; 218,272; 235,023 at the FINAL return (133 turns) |

## Debt and owed rows (CHARC at QA)

- NEW row: serialise a GUI recompute against a running export (Q5; trigger WP4.3).
- CHARC's MINOR row against `io/video/encode.py`: `close` should set `"closed"` only from `"open"` (Q2 amended,
  condition 3).
- CHARC's DR row on the sink's phase write window; DR-35 (a) text.
- Flag (i): spec 10.2's N6 body against D106 (CHARC's v0.5.6 candidate). Flag (ii): WP3.13's batch-sum sentence is
  superseded by WP3.14 (the note is in the report's D87 section).
- Style debt (no row): the in-block `import logging` in `analysis/engine.py`, for WP3.11's next touch.
- Dispositions as the report states them (register rows by CHARC): DR-48 CLOSED; DR-35 (b) CLOSED, (a) a readable
  refusal on every OS; DR-57 (a) ADDRESSED, (b) CLOSED, (c) CLOSED as a stated limit; DR-28 (1), (2), (3) CLOSED;
  DR-20 (7) CLOSED; DR-45 (a) and DR-47 not reached, DR-45 (b) WP4.2's.

## Main gates

Main after the ff merge = `c9da9ce` + this record (docs only): the candidate's full pytest stands as main's figure by
code identity; the harness gate re-run on main: 382 OK (skipped 1).
