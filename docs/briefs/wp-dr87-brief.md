# WP-DR87 -- bench stray-check cost and two `from_tiff` debts (dispatch brief, DRAFT)

**Status:** DRAFT 2026-10-29 by the orchestrator (generation 24), from CHARC's order `d509a3c2` (gen 23's state, item 4: "DR-87 micro-package WITH DR-93 and DR-94 folded into its `exif.py` touch ... one Codex micro-package with two files, or two sequential ones. Your call"). The call: ONE package. CHARC rules this draft. Spec v0.5.7; no spec clause changes. Anchors read at main `5e3537d`; RE-LOCATE every line at round 0 on the dispatch base. Owner decisions: none.

| Field | Content |
|---|---|
| ID and title | WP-DR87 -- the bench stray-process check's fixed cost on the serial leg (DR-87); `from_tiff`'s `MemoryError` degradation (DR-93) and its drop set (DR-94) |
| Lane | **CODEX**: `implementer-codex-sol-high` (gpt-6.1-sol / high), `codex exec` turns driven by `scripts/codex_cell.py`. Paces at drafting (21:50Z): Codex **0.376** (8.0 % at 21.3 % of its window) vs Claude **1.423** (71 % at 49.9 %); the orchestrator re-reads both at dispatch. Queued behind WP4.4 (one Codex lane). The orchestrator commits each turn and runs every heavy, `gpu` or footage command the cell yields. |
| Tier and nets | Tier **STRONG** (`io/photo/exif.py` is product). Reviewer A = the Claude pass, `scripts/codex_cell.py review` (`claude -p --model opus --effort high`, read-only), between turns, to convergence, five-round gate (`docs/review-gate-clearwater.md` Part 1). Reviewer B = the Claude pass at the orchestrator's seat (Part 2). Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp-dr87\rN\`, `reviewB\`. |
| Base, worktree | Base = main at dispatch. Worktree `.worktrees/wp-dr87`, branch `wp-dr87`. |
| Goal | (1) `tests/test_prototype_backend.py::test_bench_gpu_records_graphics_memory` and its in-process `bench.main` siblings stop paying the 10 s whole-system stray-process sampling (four calls, about 60 s of the test's 64-80 s), with every figure `bench.py` records in a real run unchanged. (2) A `MemoryError` inside `from_tiff` degrades to no EXIF with the existing warning. (3) `from_tiff` drops the large private IFD0 blobs a TIFF editor writes, as it drops XMP, IPTC, Photoshop IRB and ICC today. |
| Files owned | `tests/test_prototype_backend.py` (one autouse fixture, Q1); `tools/prototype/bench.py` ONLY if Q1 is ruled (b); `src/clearwater/io/photo/exif.py` (`from_tiff`'s `except` clause and `_TIFF_STRUCTURE` with its comment and `from_tiff`'s docstring sentence that lists the dropped blobs); `tests/test_io_photo_exif_bytes.py` (new tests only); `docs/reports/wp-dr87.md`; `docs/proofs/wp-dr87-ledger.md`. |
| NOT owned | `src/clearwater/interfaces/` (IF-1..IF-10 FROZEN); every other `src/` module (`io/photo/reader.py`, `writer.py`, `png.py` included); every other existing test; `tools/spike_io/`; `pyproject.toml`, `uv.lock`; the spec; the register (CHARC closes the rows at the accept). |
| Done | Plan 4.5; ruff check, ruff format --check, mypy strict; the touched tests green; Reviewer A converged; Reviewer B returned; the standard two-leg gate at the orchestrator's seat (no fullclip leg); the serial-leg wall time of the DR-87 node before and after recorded in the report. No harness gate. |

## The debt rows (verbatim, `docs/debt-register.md:96`, `:100`, `:101`)

- **DR-87** (WP-T6 accept `fe65e6a`): "MINOR, tools cost on the serial leg: `test_prototype_backend.py::test_bench_gpu_records_graphics_memory` (two 128x72 frames) takes about 64-80 s, none of it in the test's own sizes; the profile names `tools/prototype/bench.py:1305` `stray_processes` at 59.5 s cumulative over four calls (whole-system process CPU sampling) and the sampler's `stop` at 16.3 s. The cost is a fixed sampling overhead independent of frame count." Trigger: "A Codex-lane micro-package on `tools/prototype/bench.py` (sample less often or skip the whole-system scan under a bench flag the test sets; the recorded figures unchanged), or the next touch of `bench.py`."
- **DR-93** (WP4.5 accept `47a08ae`, Reviewer B F2): "`from_tiff` catches `(ValueError, struct.error)` where the base caught `Exception`, so a `MemoryError` raised by the rewriter on a crafted TIFF of the F7 pattern (shared large values inflating on relocation) escapes `read_photo` instead of degrading to no EXIF with a warning." Trigger: "`from_tiff` catches `MemoryError` beside the two parser errors (not bare `Exception`, which the rewriter no longer needs), one RED test with a bounded synthetic trigger."
- **DR-94** (WP4.5 accept, Reviewer B F5, pre-existing since WP3.6): "`from_tiff`'s drop set `_TIFF_STRUCTURE` (`exif.py:36-40`) names XMP, IPTC, Photoshop IRB (34377) and ICC, but not Photoshop ImageSourceData (37724) or the other large private IFD0 blobs a TIFF editor writes ... No owner source is a TIFF." Trigger: "extend the drop set (37724 ImageSourceData and any other large private IFD0 blob tag the fix names), one test on a synthetic TIFF; the report lists the dropped tag ids."

## The code today (read at `5e3537d`)

- **Stray check:** `tools/prototype/bench.py:1305-1340` `stray_processes(threshold_percent=STRAY_CPU_PERCENT, interval_s=None)`; `None` reads the module constant `STRAY_SAMPLE_S = 10.0` (`:153`) at call time. Callers in `bench.py`: `:342`, `:358`, `:367`, `:380` (the device-resident leg) and `:810`, `:853` (the clip leg); also `tools/spike_io/transport.py:1011` (not owned). The recorded keys are `stray_processes_before` / `_after` (`:416-417`, `:892-893`).
- **The precedent:** `tests/test_prototype_clip.py:58-61` already shortens it for its file with an autouse fixture, `monkeypatch.setattr(bench, "STRAY_SAMPLE_S", 0.2)`, docstring "The stray-process check samples 10 s in a timed window; 0.2 s is enough for a test." `tests/test_prototype_backend.py` has no such fixture; its in-process `bench.main` callers are at `:337` (the DR-87 node, `gpu`), `:389`, `:422`, `:477`, `:532`, `:536`; `:502` `test_bench_works_as_a_script` runs a subprocess (a monkeypatch does not reach it).
- **GPU sampler:** `_GpuSampler` `:1270-1302`, interval `GPU_SAMPLE_INTERVAL_S = 60.0` (`:147`); `stop` sets the event and joins (`:1290-1293`). DR-87's 16.3 s in `stop` is unexplained by the code read: round 0 profiles it.
- **`from_tiff`:** `src/clearwater/io/photo/exif.py:353-383`; the `except (ValueError, struct.error)` at `:381` logs "TIFF tags cannot be read for EXIF (%s); no EXIF carried" and returns None. The drop set `_TIFF_STRUCTURE` `:34-40` (comment "TIFF structure and embedded blobs that are not EXIF fields"), passed with `{330}` at `:377`.
- **Tests:** `tests/test_io_photo_exif_bytes.py:354-376` (`from_tiff` filters structure; no metadata returns None) and the parametrised routes `:382`, `:447`.

## Locks

No frozen interface; no dependency; no OS-specific code; no write under the footage folder (every test synthetic, under `tmp_path`). DR-87: every figure a real `bench.py` run records is unchanged (`STRAY_SAMPLE_S` stays 10.0 at module level; no recorded key added, removed or renamed). DR-93: `MemoryError` joins the two parser errors in the one `except`; bare `Exception` is NOT caught; the warning text unchanged. DR-94: only tags that are image-structure or editor-private blobs, never a field the EXIF/TIFF tag reference lists as image description, authorship or capture metadata (Make, Model, Artist, Copyright, DateTime, ImageDescription, Software, Orientation and the like stay carried).

## Task ladder

1. **Read and map** the anchors on the dispatch base.
2. **Round 0 in the ledger (no code), then YIELD:** (a) the re-located anchors; (b) the RED list, each test with the failure expected on the base; (c) a RUN REQUEST for the DR-87 node's base wall time and profile at the orchestrator's seat (`uv run pytest -q tests/test_prototype_backend.py::test_bench_gpu_records_graphics_memory --durations=0 -p no:cacheprovider` plus a `cProfile` top-15 by cumulative time, outputs under `work/wp-dr87/r0/`), naming where `stop`'s 16.3 s sits; (d) the DR-94 tag list proposed under Q2, each tag with its name and source (TIFF 6.0, the Adobe Photoshop TIFF note, DNG 1.x), and the tags considered and kept.
3. **DR-87** as ruled Q1, then the RUN REQUEST for the after figure (same command).
4. **DR-93, RED first:** a test that makes the rewriter raise `MemoryError` through a bounded seam (monkeypatch the private helper `from_tiff` calls to raise it; no real allocation) and asserts `from_tiff` returns None and logs the warning once; it fails on the base with the escaping `MemoryError`. Then the `except` clause.
5. **DR-94, RED first:** a synthetic TIFF (built in the test as `test_io_photo_exif_bytes.py` builds its sources) whose IFD0 carries each ruled tag beside a kept field such as Make; assert the block from `from_tiff` has none of the ruled tags and still has Make byte-exact. Then the drop set, its comment and the docstring sentence.
6. **Report and ledger:** `docs/reports/wp-dr87.md` with the before/after wall time and profile lines of the DR-87 node (orchestrator's run, EXIT), the dropped tag ids with names, the RED/GREEN node ids, the rounds and the depth readings.
7. **Lint and types**, Reviewer A to convergence (yield after each round once adjudicated, before remediating), then the orchestrator's Reviewer B and the ONE two-leg gate.

Light runs (the cell's sandbox): `PYTHONPATH=scripts uv run pytest -q tests/test_io_photo_exif_bytes.py tests/test_prototype_backend.py --basetemp=work/wp-dr87/tmp -p sandbox_mkdir_shim -p no:cacheprovider -m "not gpu and not footage and not gui and not slow and not fullclip"`. The DR-87 node is `gpu`: a RUN REQUEST.

## Hardware flags

The before/after wall time of one `gpu` test is a tools-cost figure, not a timing row of the spec; it is run at the orchestrator's seat with nothing else heavy running (not EXCLUSIVE in the plan's sense).

## STOP for

A change to any figure `bench.py` records; an edit outside the owned list; catching bare `Exception`; a DR-94 tag that is an EXIF field under the Locks; a frozen interface; a dependency; any choice this brief leaves open.

## Return report

Commits by the orchestrator (`test(wp-dr87): ...`, `fix(wp-dr87): ...`, `docs(wp-dr87): ...`), by pathspec, `-c core.autocrlf=false`, LF blobs, the GPT-6.1 Sol footer. The final turn names: the per-change list, the light runs read off the final state, the before/after figures, Reviewer A's rounds and verdict, each lock honoured on disk, the added node ids, any deviation or STOP.

## Questions for CHARC (recommended answer first)

- **Q1. DR-87's fix: test-side or tool-side?** Recommended (a): the autouse fixture of `tests/test_prototype_clip.py:58-61`, copied into `tests/test_prototype_backend.py` (same docstring), so every in-process `bench.main` there samples 0.2 s; `bench.py` is not touched and its recorded figures are unchanged by construction. `test_bench_works_as_a_script` (subprocess) keeps the 10 s sampling; round 0 reports its wall time and leg, and if it is material the cell proposes a remedy for your ruling rather than building one. If round 0 places DR-87's 16.3 s in `stop` in the sampler, the cell reports it and builds nothing for it unless you rule. Alternative (b): a `bench.py` flag or environment variable that skips the whole-system scan, set by the tests (touches a tool, adds a branch that real runs must never take).
- **Q2. DR-94's tag list.** Recommended: 37724 (ImageSourceData, Photoshop layer data) and 50740 (DNGPrivateData), the two large private IFD0 blobs; the round-0 note may propose others with their source, and you rule the final list there. Kept explicitly: 50341 (PrintIM, an EXIF-carried field in practice) and every tag the Locks name. Alternative: 37724 only, as the row's minimum.
- **Q3. One package or two.** Recommended: one (this brief): two files, three DRs, one Reviewer A loop, one Reviewer B and one two-leg gate (about 35 min of gate wall time saved against two). Alternative: DR-87 alone first (tools tier), then DR-93/94 (STRONG).
