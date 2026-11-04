# WP-T8 accept record (orchestrator generation 42, 2026-11-04)

**Package:** WP-T8, the tools and tests paydown: DR-119 (c)-(e), DR-120, DR-118, DR-116.
- **Brief:** `docs/briefs/wp-t8-brief.md` (FINAL by CHARC; round-0 ruling at main `92bea573`).
- **Lane: CODEX**, `implementer-codex-sol-high`, two sessions, seven turns. Both nets ran Claude through `scripts/codex_cell.py review`, the other model.
  - Session 1, `01a1a5ff-b019-7932-8300-7ff8bc4c66e5`: turns 1-3; retired at 240,799.
  - Session 2, `01a1a634-b204-7461-8583-978ef7876d56`: turns 4-7, fresh at turn 4; at **238,421** after turn 7, retired by the depth rule.
- **Report:** `docs/reports/wp-t8-paydown.md`.
- **Evidence:** `C:\Users\rwsmy\clearwater-review-evidence\wp-t8\`:
  - `cell`: dispatches 1-7, prompts, returns, transcripts;
  - `A\r1`, `B`;
  - `dr116\` (the analysis script and CSVs);
  - `seat\` (the seat's test logs);
  - `gate\` (gate `t8a`: summary, logs, junits).

**Candidate:** branch `wp-t8` at `ad385cbb`, with main merged in twice (`a844a37f` before Reviewer B; once more before this record), plus this record. **Footprint** (`git diff --name-only main...wp-t8`): the 12 owned paths, the report and this record. 0 CR in every changed blob.

The 12 owned paths:
- `src/clearwater/cache/store.py` (the one product edit);
- `tests/fixture_plugin.py`, `tests/test_cache_store.py`, `tests/test_fixtures.py`, `tests/test_core_speed.py`, `tests/test_export_bench.py`, `tests/test_tools_halo_part3.py`;
- `tools/core_speed.py`, `tools/export_bench.py`, `tools/halo_part3.py`, `tools/n6.py`;
- `docs/reports/wp-t8-paydown.md`.

## What it pays

| Row | Change | Test |
|---|---|---|
| DR-119 (c) | `tools/export_bench.py` writes its JSON record to a `mkstemp` name in the destination folder, then `os.replace`; the ROW line prints before the write (B4) | `test_export_bench.py` interrupt and blocked-write cases |
| DR-119 (d) | `tools/halo_part3.py` stages the V3 folder beside `<out>` and publishes it like the sheet; refuses `--cache-dir` inside `<out>/items`; `build_sheet`'s docstring names `sheet-<stamp>/sheet.json` | `test_tools_halo_part3.py` |
| DR-119 (e) | NEW `tools/n6.py`, ONE N6 constant (12 min/min, D106), shared by `export_bench.py` and `core_speed.py`, checked against the spec's N6 line; the stale 25 / 0.834 gone | `test_core_speed.py`, `test_export_bench.py` |
| DR-120 | `tests/fixture_plugin.py`: the generated-sample cache sits under `getbasetemp()` when `--basetemp` is given (every xdist worker inside its own root), else under the MAIN checkout's `work/fixtures/generated` found through git's common directory; if git discovery fails, a warning and the session basetemp (B1) | `test_fixtures.py` (additions) |
| DR-118 | `cache/store.py` `_entry_for_write` logs a WARNING naming the path and raises `OSError` on a pre-existing junction / symlink OR an existing non-directory at the entry path (round-0 ruling; the non-directory case would raise in `mkdir` anyway); the job fails readably, no caller loops | `test_cache_store.py` planted junction (2) and planted file (2) |
| DR-116 | the serial-leg cost table from the archived junits: +659.959 s = shared nodes +43.227, NEW nodes +616.724, removed -0.055, outside-testcase +0.063: new coverage, not a slowdown; the largest row is the real-photo leg (skip -> pass, +249.8 s) | analysis re-derived exactly by both nets |

## Nets

| Net | Result |
|---|---|
| Round 0 (turn 1) | Q1-Q3; Q3's premise corrected by CHARC (warn + `OSError`) |
| Groups 1-2 (turns 2-3) | `90fd9263`, `d558c48a` |
| Turn 4 (fresh session) | STOP on 3 `test_fixtures.py` audit tests. RULED a sandbox-only residual: the Codex sandbox's restricted process adds a `nul` open and one launch. Seat runs: main 3/3, worktree 3/3 once its EMPTY `.venv` was synced (gen 42, 10:58Z), the full set 488, and 3/3 with the sandbox shim |
| Turn 5 | the report `6d0a249a`; no reductions applied |
| Reviewer A round 1 (Claude, `6d0a249a`) | **NO_NEW_CRITICAL_MAJOR**: 488 passed, 9 mutation probes (8 caught; the non-directory clause survived = F1), every DR-116 figure re-derived. F1-F6 minor fixed at `0e784986`; F7 (V8 skips) -> DR-126; F8 declined with the reductions; F9-F11 noted |
| **Reviewer B** (Claude at the seat, `a844a37f`) | **NO_NEW_CRITICAL_MAJOR**: 493 passed; 10 mutations of F1 / F3 all caught; the headline recomputed with Decimal sums; callers of the refusal traced (no loop, one WARNING per job). B1 minor and B3 / B4 / B6 / B7 / B8 / B9 advisories applied at `ad385cbb` (read at the seat); B2 = DR-126's count (below); B5 noted |

## CHARC rulings in the package

- `658e4c90`: both DR-116 reductions DECLINED (at most 35 s, unmeasured, couples two acceptance checks). DR-116 CLOSES at the accept on the attribution, with the figure of record restated (1,273 tests / 2,049 s at p55). DR-86's candidates stay banked. No new suite-cost pass unless the serial leg crosses about 40 min.
- `7873d925`: the two V8 look-check source frames restored, md5-checked; DR-126 opened.

**V8 frames restored** (copied BACK from the archive; the D: copy kept). From `D:\clearwater-archive\work\wp1.3\frames\` into the main checkout's `work\wp1.3\frames\`, md5 equal to `D:\clearwater-archive\manifests\wp1.3.md5`:

| File | Bytes | md5 |
|---|---|---|
| `GX011625_0024.925.png` | 8,105,999 | `dab5821e630f7549ca840a23a51e8566` |
| `GX011625_0114.648.png` | 3,093,211 | `8ca1d0af0fbc79d65b1ad174d30c7187` |

Back in coverage at this gate, as the serial leg's 0 skips show:
- `tests/test_methods_assembly_v8.py`: 8 `test_v8_preview_against_the_downscaled_export[...]` and `test_v8_planted_range_error_fails`;
- `tests/test_wp41_v8.py::test_v8c_k_above_1_on_real_sized_content`;
- `tests/test_app_v8_v18.py::test_v8_photo_k_above_1_on_real_sized_content`.

That is ELEVEN nodes. Reviewer B (B2) counted p55's serial skips: all 11 were look-check-frame-absent, and the yuvj skip is in the PARALLEL leg. DR-126's "ten ... the eleventh is the yuvj case" reads eleven, all V8; CHARC to correct the row.

## Gate (`t8a`, on `ad385cbb`, alone on the machine, the stall watch on every leg)

| Check | Result |
|---|---|
| `df -h /c` | 80 GB free at the start, 77 GB at the end |
| static | ruff exit 0; format exit 0 (318 files); mypy exit 0 (159 source files) |
| collection identity | 6,806 + 1,273 + 7 = 8,086 = all; 0 duplicates; 0 differences |
| parallel | exit 0, 591 s: 6,805 passed, 1 skipped (`test_color_roundtrip.py:123`, the by-design yuvj case) |
| serial | exit 0, 2,163 s: **1,273 passed, 0 skipped** |
| fullclip | exit 0, 1,601 s: 7 passed |
| harness | below (no harness file changed; run on the record's head for the new `docs/proofs/` file) |
| footprint | the owned paths only; 0 CR |

Archive: `clearwater-review-evidence\wp-t8\gate\`.

## Dispositions (for CHARC at this accept)

- Close DR-119 in full, DR-120 and DR-118.
- DR-118's row records the failure mode: the job fails with a readable `OSError`, one WARNING per job.
- Close DR-116 on the attribution, and update DR-86 (figures in the report).
- Correct DR-126 to eleven nodes.
- Advisory B5 for the register, if wanted: concurrent developer runs (no basetemp, no xdist) in the main tree and in a worktree with a changed flicker generator can regenerate under each other.
- Advisory B6: `tools/fixtures/generate.py:12` and the manifest's `command` still document `--generated-out work/fixtures/generated`; documentation only.

## Merge

Harness gate on `8d2f3a52` (the accept record's commit `22df34c5` plus the merge of main `8e956d71`; the package's code unchanged since `ad385cbb`, the gate of record): `uv run python -m unittest discover -s tests/harness` -> Ran 423 tests, OK (skipped=1); no registration needed for the two new files (`docs/reports/`, `docs/proofs/` are instance-surface prefixes). `main` fast-forwarded to `wp-t8` by the orchestrator. The worktree `.worktrees/wp-t8` is released after the merge (its `work/` pruned only on the owner's word).
