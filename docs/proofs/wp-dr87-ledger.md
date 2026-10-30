# WP-DR87 cumulative ledger

## Round 0 - dispatch-base map and requests (turn 1)

STOP / next-seat input: recommend confirming the final DR-94 additions as
**37724 ImageSourceData + 50740 DNGPrivateData**, with no further tags. Await
CHARC's round-0 ruling before building DR-94, as the dispatch requires. The
baseline timings and profile below are RUN REQUESTS, not executed results.
This turn yields before any product or test edit.

- Base verified: `00518bba0d90acb03707459862951e8365dd9bcb` (`00518bb`).
- Initial `git status --short`: empty. Branch/worktree supplied by dispatch:
  `wp-dr87`, `.worktrees/wp-dr87`; no other worktree accessed.
- Scope: DR-87 test fixture only; DR-93 one exception tuple; DR-94 two IFD0
  drop tags and associated comment/docstring; new EXIF tests; report/ledger.
- Protocol read: `docs/dispatch-recipe.md`, `APPLICATION.md`, `CLAUDE.md`,
  plan 4.1-4.5, spec 8.1/D63 and N1/N13, `docs/review-gate-clearwater.md`,
  `docs/model-prompting-standard.md`. The dispatch's explicit turn schedule,
  ownership, seat-only hardware/profile runs and depth limits govern this cell.
- No pytest, profile, GPU work, lint or type run performed in round 0. No
  benchmark improvement, new RED/GREEN outcome or reviewer convergence claimed.

### Re-located anchors on 00518bb

All line numbers in this section refer to the unmodified dispatch base.

| Mechanic / surface | Base location and observation |
| --- | --- |
| Stray interval and sampler interval | `tools/prototype/bench.py:153` `STRAY_SAMPLE_S = 10.0`; `:147` `GPU_SAMPLE_INTERVAL_S = 60.0`. |
| Whole-system stray scan | `bench.py:1305-1340` `stray_processes`; `:1322` resolves `None` to the current module constant at call time; `:1324-1327` primes process CPU counters; `:1330` sleeps; `:1332-1340` reads and filters them. Shortening the sleep does not remove process enumeration cost. |
| Core-mode stray calls | `bench.py:342,358` before/after the main loop; `:367,380` before/after the supplementary device-resident loop. A successful GPU core node makes four calls; CPU core makes two. |
| Clip-mode stray calls | `bench.py:810,853` in `_clip_pass` (`:735`). |
| Other caller (read-only) | `tools/spike_io/transport.py:1011` calls `bench.stray_processes()`. Not owned or changed. |
| Recorded stray keys | `bench.py:416-417` core ambient, `:367,380` resident window, `:892-893` clip ambient: `stray_processes_before` / `stray_processes_after`. |
| Fixture precedent | `tests/test_prototype_clip.py:58-61`: autouse `_short_stray_check`, patches `bench.STRAY_SAMPLE_S` to `0.2`. Docstring: "The stray-process check samples 10 s in a timed window; 0.2 s is enough for a test." |
| Target module has no fixture | `tests/test_prototype_backend.py`: no `@pytest.fixture` or `_short_stray_check` on this base. Copy the precedent exactly in the later build turn. |
| DR-87 node and markers | `test_prototype_backend.py:333-345`; `gpu` at `:333`, `requires_gpu` at `:334`, function at `:335`; two synthetic 128x72 c3 frames at `:336`, `bench.main` at `:337`. Serial gate leg. |
| Other in-process bench calls | `test_prototype_backend.py:389` documented CPU record; `:422` one-frame CPU record; `:465` bad arguments (parametrized); `:477` unusable GPU. The last two return before scanning. |
| Brief's stale additional callers | The brief's `:532,:536` are not additional `bench.main` calls on this base: `:532` starts a run.py test and `:536` starts another. `_run_backend` invokes `run.main` at `:523`; another `run.main` is at `:553`. This is anchor correction, not added scope. |
| Subprocess smoke | `test_prototype_backend.py:502-513` `test_bench_works_as_a_script`; `:504` CPU, 32x24, two frames, c3; `:505-510` child Python runs the actual script with a 120 s timeout. Unmarked, hence parallel gate leg. Parent monkeypatch cannot reach this child. |
| Core sampler actually used | `bench.py:340` constructs `_PeakRssSampler`; `:346` starts it; `:355` stops it. `_PeakRssSampler.stop` at `:1211-1215` sets the event, joins, then makes a final `_sample`. `_run` waits on the event at `:1219`; `_sample` is at `:1222`. |
| Card sampler and stop | `_GpuSampler` is at `bench.py:1270-1302`; its stop is `:1290-1293` (event + join); its worker waits on the event at `:1297`, then reads external GPU state at `:1298-1299`. |
| Card sampler's actual caller | `_GpuSampler()` occurs only at `bench.py:808` in `_clip_pass`; start `:814`, stop `:849`. `main` branches to clip mode only at `:297-298`. The DR-87 node selects core mode, so it does not instantiate this sampler. |
| Ratio assertion and calculation | `test_prototype_backend.py:345`; `bench.py:1020-1033` `_estimate_record`, specifically `:1031`: estimate MiB / `memory["gpu_pool_reserved_mb"]`. |
| Pool baseline and measurement | `_PoolTracker.__init__` `bench.py:1379-1385` gets the default pool, calls `free_all_blocks`, records used bytes, and installs its allocator; `record` `:1402-1417`, specifically `:1408`, reads `pool.total_bytes()` in MiB after the main loop. |
| Estimate's scope | `tools/prototype/backend.py:154-193` `memory_estimate_bytes`; constants `:39-41`. Shape-scaled working-set bound plus 1 MiB, not a bound on arbitrary allocations already alive in the process. |
| EXIF drop set | `src/clearwater/io/photo/exif.py:34-40`: comment `:34-35`, `_TIFF_STRUCTURE` `:36-40`; existing blobs at `:39`: 700 XMP, 33723 IPTC, 34377 Photoshop resources, 34675 ICC. Neither new tag nor PrintIM is present. |
| TIFF-to-EXIF route | `exif.py:353-383` `from_tiff`; dropped-blob docstring sentence `:356-358`; `:377` calls `_read_entries(data, _TIFF_STRUCTURE | {330})`; `:380` calls `_write_entries`; `:381` catches only `(ValueError, struct.error)`; `:382-383` warning then None. |
| Bounded DR-93 seam | `_write_entries` at `exif.py:203` is the private relocation writer called inside `from_tiff`'s try. Patching it to raise `MemoryError` reaches the exact missing exception handler without large allocations. |
| IFD0-only filtering | `_read_entries` at `exif.py:63`; `:115-116` skips drop-set entries only when `label == "IFD0"`, before value slicing at `:118-129`. Child EXIF/GPS/Interop traversal is unchanged by the requested additions. |
| Independent synthetic builders | `tests/test_io_photo_exif_bytes.py:17` `_fixture`; `:54` `_parse`; `:84` `_entry`; `:88` `_same`; `:112-137` `_tiff_fixture` builds a tiny valid TIFF and one pixel without product writers. |
| Existing TIFF tests | `test_io_photo_exif_bytes.py:354-364` raw Artist/ExposureTime retained, structure removed; `:367-370` no metadata -> None; `:373-378` BigTIFF warning/refusal. |
| Parametrized rewrite routes | `test_io_photo_exif_bytes.py:382` `route=["edit", "from_tiff"]`; `:447` same routes for damaged description/kept Make. These anchors are unchanged. |
| Debt provenance | `docs/debt-register.md:96` DR-87, `:100` DR-93, `:101` DR-94. Register is read-only to this package. |

### RED roster and preservation controls (not yet authored or run)

| Change | Planned node / check | Expected on base | Expected after authorized fix |
| --- | --- | --- | --- |
| DR-87 | Existing `tests/test_prototype_backend.py::test_bench_gpu_records_graphics_memory`, seat timing/profile | Normally passes, but four default 10 s sleeps plus whole-system scan cost; historical 64-80 s. This is a cost baseline, not a promised failing assertion. The unrelated ratio flake can fail independently. | Same assertions and keys; four 0.2 s sleeps in this module's in-process run. Actual before/after reduction must be measured; enumeration/shutdown costs remain. No new wall-clock assertion or test is authorized for DR-87. |
| DR-93 | New `tests/test_io_photo_exif_bytes.py::test_from_tiff_memory_error_returns_none_with_warning` | FAIL: monkeypatched `_write_entries` raises `MemoryError("synthetic rewrite exhaustion")`; it escapes the tuple at `exif.py:381`. | PASS: None and exactly one WARNING from `clearwater.io.photo.exif`, with unchanged template rendered as `TIFF tags cannot be read for EXIF (synthetic rewrite exhaustion); no EXIF carried`. |
| DR-94 | New `tests/test_io_photo_exif_bytes.py::test_from_tiff_drops_private_ifd0_blobs_and_keeps_metadata` | FAIL: valid IFD0 entries 37724 and 50740 are retained by the base drop set; assert absence of both in the independently parsed output. | PASS: both absent, Make and PrintIM still type/count/value byte-exact; structural tags absent as before. |

DR-93 test construction: use `_tiff_fixture` with a small valid Make entry, so
nonempty entries reach the writer. A local replacement for `_write_entries`
records that it was called and immediately raises the synthetic `MemoryError`.
Use `monkeypatch.setattr` for restoration, `caplog` at WARNING for the exact
logger, and check one call, None and one exact warning record. No hostile-size
TIFF or large allocation is needed: the requested behavior is the outer
exception boundary, and the replacement raises inside that try block. A normal
fixture prevents parser warnings from obscuring the once-only warning check.

DR-94 test construction: use the existing `_tiff_fixture` builder and a
per-test `tmp_path`. Put **both** ruled tags in the same IFD0 beside Make (271)
and PrintIM (50341). Use small, distinct out-of-line payloads (dozens of bytes),
UNDEFINED/type 7 for ImageSourceData and BYTE/type 1 for DNGPrivateData; Make is
ASCII/type 2 and PrintIM has opaque bytes. Independently parse via `_parse`,
assert neither ruled tag survives, and compare Make/PrintIM with `_same`.
Payload size is irrelevant to tag selection and stays bounded. The base
failure is unwanted tag retention, not malformed input or missing metadata.

The DR-94 preservation assertions are positive controls expected to pass on
the base as well. Existing tests cover Artist, Make/Model and other raw fields;
only the two ruled ids will be added to the product drop set. No existing test
assertion is edited. The light-run recipe in the brief (sandbox shim, marker
exclusions and worktree basetemp) applies when these tests are built.

### RUN REQUEST: R0 baseline timings and profile (orchestrator seat)

Run from this worktree in **Git Bash**, on the unchanged product/test base,
with no other heavy process running and outside WP4.3's exclusive windows.
The ledger-only commit may be HEAD: record its SHA and verify these source/test
files still match `00518bb`. These are seat commands, so **do not load the
sandbox shim**. No footage input, fullclip leg or full-suite gate is requested.

Expected scheduling allowance (estimates, not measurements): GPU node wall run
about 65-100 s; profiled GPU run about 80-120 s; child-script smoke about 25-60 s.
The fixed sleep floor for the child is 20 s. Total allowance about 3-5 min, one
run at a time. Record actual EXIT, pytest durations, external wall time and UTC
conditions. A skipped GPU node is not a valid before figure. Do not silently
retry or treat a ratio failure as a timing acceptance pass; return its log.

Preparation / conditions:

```bash
unset PYTEST_ADDOPTS
export QT_QPA_PLATFORM=offscreen
mkdir -p work/wp-dr87/r0
git rev-parse HEAD > work/wp-dr87/r0/base-head.txt
git diff 00518bb -- tools/prototype/bench.py tests/test_prototype_backend.py src/clearwater/io/photo/exif.py tests/test_io_photo_exif_bytes.py > work/wp-dr87/r0/base-source-diff.txt
date -u '+%Y-%m-%dT%H:%M:%SZ' > work/wp-dr87/r0/start-utc.txt
uv run python -c "import shutil, psutil; print('disk_free_bytes=', shutil.disk_usage('.').free); print('ram_available_bytes=', psutil.virtual_memory().available); assert psutil.virtual_memory().available >= 5*2**30" > work/wp-dr87/r0/preflight.txt 2>&1
```

Require empty `base-source-diff.txt`, successful preflight, and record the
operator-observed condition that no other heavy work is running. Check disk
headroom; this request grants no deletion. If a named basetemp/output already
exists, use a fresh suffixed name and report the substitution; do not delete it.

R0-A, normal GPU node (the acceptance baseline):

```bash
TIMEFORMAT='WALL_SECONDS=%3R'
date -u '+%Y-%m-%dT%H:%M:%SZ' > work/wp-dr87/r0/base-node-start-utc.txt
{ time uv run pytest -q tests/test_prototype_backend.py::test_bench_gpu_records_graphics_memory --durations=0 -p no:cacheprovider --basetemp=work/wp-dr87/r0/base-node-tmp > work/wp-dr87/r0/base-node.log 2>&1; } 2> work/wp-dr87/r0/base-node-wall.txt
printf 'EXIT=%s\n' "$?" > work/wp-dr87/r0/base-node-exit.txt
```

R0-B, separate cProfile execution of the same node:

```bash
date -u '+%Y-%m-%dT%H:%M:%SZ' > work/wp-dr87/r0/base-profile-start-utc.txt
{ time uv run python -m cProfile -o work/wp-dr87/r0/base-node.prof -m pytest -q tests/test_prototype_backend.py::test_bench_gpu_records_graphics_memory --durations=0 -p no:cacheprovider --basetemp=work/wp-dr87/r0/base-profile-tmp > work/wp-dr87/r0/base-profile.log 2>&1; } 2> work/wp-dr87/r0/base-profile-wall.txt
printf 'EXIT=%s\n' "$?" > work/wp-dr87/r0/base-profile-exit.txt
uv run python -c "import pstats; s=pstats.Stats('work/wp-dr87/r0/base-node.prof').strip_dirs().sort_stats('cumulative'); s.print_stats(15); s.print_stats(r'bench.py:.*\(stray_processes\)'); s.print_stats(r'bench.py:.*\(stop\)'); s.print_callers(r'bench.py:.*\(stop\)'); s.print_callees(r'bench.py:.*\(stop\)'); s.print_callees(r'bench.py:.*\(_sample\)')" > work/wp-dr87/r0/base-profile-top15-and-samplers.txt 2>&1
printf 'EXIT=%s\n' "$?" > work/wp-dr87/r0/base-profile-summary-exit.txt
```

Return the top-15 cumulative block and the bench-specific filtered blocks,
including call count / own time / cumulative time for each `stop`, its callers
and callees, `stray_processes`, and final `_sample`. Profile cumulative times
overlap and must not be added. cProfile observes the main thread; the `join`
time can expose waiting, but it does not profile the worker's Python execution.

R0-C, unmodified script smoke (parallel-leg residual cost):

```bash
date -u '+%Y-%m-%dT%H:%M:%SZ' > work/wp-dr87/r0/base-script-start-utc.txt
{ time uv run pytest -q tests/test_prototype_backend.py::test_bench_works_as_a_script --durations=0 -p no:cacheprovider --basetemp=work/wp-dr87/r0/base-script-tmp > work/wp-dr87/r0/base-script.log 2>&1; } 2> work/wp-dr87/r0/base-script-wall.txt
printf 'EXIT=%s\n' "$?" > work/wp-dr87/r0/base-script-exit.txt
```

| Seat result to return | Current state |
| --- | --- |
| GPU node pytest call duration / external wall / EXIT / UTC conditions | Pending R0-A; no new figure measured by cell. |
| Profile wall / EXIT / top-15 / stray count and cumulative time | Pending R0-B. |
| Exact `stop` function, callers/callees, join versus final-sample cost | Pending R0-B; source trace below rejects card-sampler attribution for this core path. |
| Child-script pytest duration / external wall / EXIT | Pending R0-C; parallel leg, 10 s sampling remains per Q1. |
| Remedy for residual child cost if material | Await measured result and CHARC ruling; no child bootstrap, tool flag or environment seam built. |

### Sampler observation and ratio observation

**[MINOR, evidence clarification; REASONED] Sampler attribution.** The historical
WP-T6 report (`docs/reports/wp-t6-gate-sizing.md:309-324`) records one enclosing
80.873235 s command, pytest 79.54 s, `bench.main` 78.325 s, four stray calls
59.501 s, and an unspecified `stop` 16.303 s. It describes shutdown/final
sampling without identifying `_GpuSampler.stop`. On the dispatch base this
core node reaches `_PeakRssSampler.stop` (`bench.py:355,1211`), which includes a
join and a final process-memory sample. `_GpuSampler` is only in the clip
path. Thus the brief's possible card-sampler attribution is not supported by
the call graph. It is not evidence of a 60 s uninterruptible sampler sleep:
both workers use interruptible `Event.wait`. R0-B must locate the actual
cost. No sampler change is owned or proposed before that result/ruling.

**[MINOR, pre-existing / observation-only; REASONED] Ratio flake.** The dispatch
reports the WP4.4 loaded gate failure `0.514 < 1.0`, followed by an alone pass.
`docs/proofs/wp4.4-accept.md:41-43` independently records the observation and
paired reruns (2 passed in 64.57 s; later 2 passed in 65.35 s). Those are paired
rerun totals, not a new isolated DR-87 duration.

The asserted ratio is the shape-based estimate divided by the **current
process's default CuPy pool reserved bytes**, read after the main loop and
before the resident loop (`bench.py:360-364,383,408,1031,1408`). It is neither
device-wide used memory nor the peak-used allocation count. The estimate is
for the current pipeline working set; the denominator includes all memory
acquired by that pool, including cached/rounded allocations and any still-live
allocations from earlier activity in the same pytest process. `_PoolTracker`
calls `free_all_blocks` first, but that frees free blocks, not live allocations;
CuPy also documents that split blocks cannot be released until merged. See
[CuPy MemoryPool reference](https://docs.cupy.dev/en/stable/reference/generated/cupy.cuda.MemoryPool.html).

Consequently a retained/split/rounded pool state larger than the small frame's
estimate can put this ratio below 1.0, even if the two-frame pipeline's own
increment fits. This is a plausible suite-state mechanism, **not a reproduced
root cause for the 0.514 event**. Another process's GPU usage is not directly
counted by this process-local pool denominator; loaded-host correlation alone
does not prove causation. Existing live objects, allocator state and pool
fragmentation at failure would be needed to establish it.

The Q1 fixture changes only the duration of stray CPU sampling. It does not
empty/isolate the GPU pool, alter the estimator or change the assertion. It
reduces elapsed exposure to unrelated concurrent activity but provides no
guarantee against this ratio failure and no direct correction of its pool
state. Recommendation: retain the granted fixture-only scope; if the seat
reproduces the flake, return the failing record and request a separate bounded
CHARC-authorized diagnosis of pool state/test isolation. No assertion or
`bench.py` edit is authorized here.

### DR-94 ruled list, sources and kept fields

No additional drop tag is proposed. The requested final list is exactly:

| IFD0 tag | Name / payload | Primary source | Disposition |
| --- | --- | --- | --- |
| 37724 / 0x935C | ImageSourceData: Photoshop layer/mask document data, UNDEFINED bytes | [Adobe Photoshop TIFF Technical Notes, March 22 2002, p. 11](https://alternatiff.com/resources/TIFFphotoshop.pdf#page=11); also [Adobe Photoshop File Formats, TIFF tags](https://www.adobe.com/devnet-apps/photoshop/fileformatashtml/) | Add to IFD0 drop set under Q2; editor image data, not an ordinary description/authorship/capture field. |
| 50740 / 0xC634 | DNGPrivateData: manufacturer-private raw-converter block, BYTE, usage IFD 0 | [Adobe DNG Specification 1.7.1.0, September 2023, p. 41](https://helpx.adobe.com/content/dam/help/en/camera-raw/digital-negative/jcr_content/root/content/flex/items/position/position-par/download_section_733958301/download-1/DNG_Spec_1_7_1_0.pdf#page=41) | Add under explicit Q2 ruling. This does not add DNG input support or change raw-input refusal. |

The Photoshop technical note and TIFF 6.0 document below are Adobe-authored
primary documents read from mirrors; Adobe's resource-page TIFF PDF links
were unavailable during this turn. The Adobe-hosted DNG PDF and Photoshop
HTML reference were accessible. No inference from an unauthored tag list is
needed for either addition.

Considered and kept (not added to the drop set):

| Tags | Names and reason / source |
| --- | --- |
| 50341 | PrintIM: explicitly KEPT by CHARC Q2, even though opaque/private in practice. Positive preservation control in the new synthetic test. |
| 270, 271, 272, 274, 305, 306, 315, 33432 | ImageDescription, Make, Model, Orientation, Software, DateTime, Artist, Copyright: metadata protected by the Locks; [TIFF 6.0, Section 8 and Appendix A](https://www.alternatiff.com/resources/TIFF6.pdf). Retained at `from_tiff`; existing downstream D63 edits of Orientation/Software remain unchanged. |
| 50255 | Photoshop Annotations: authored annotations, not a newly ruled drop tag; [Adobe Photoshop File Formats, TIFF tags](https://www.adobe.com/devnet-apps/photoshop/fileformatashtml/). Kept; no blanket removal of Photoshop/private tags. |

Existing 700/33723/34377/34675 exclusions remain as-is. No other tag is
selected for removal. The eventual comment and `from_tiff` sentence must name
the Photoshop image-source and DNG-private blobs distinctly from the existing
Photoshop resource blob, without claiming that arbitrary EXIF is discarded.

### Verification / review ledger

Round 0 is mapping and test design, not a Reviewer A round. No finding was
received from either reviewer. Counts below count reviewer findings only;
the two severity-tagged source observations above are disclosed separately.

| Round | Reviewer / transport | Critical / major / minor | In / out | NEW / REOPENED | Reverts | Product / test fixes | Verdict / evidence | Dispatcher depth |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | Not run; Claude opus/high pass scheduled by driver later | 0 / 0 / 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 | Map complete; baseline/profile and final Q2 ruling pending. No convergence claim. | Not supplied (fresh turn 1). |

Reviewer A uses `scripts/codex_cell.py review`, Claude opus/high, STRONG.
Durable reviewer evidence belongs at the orchestrator-managed
`C:\Users\rwsmy\clearwater-review-evidence\wp-dr87\rN\` and `reviewB\`;
this cell has not written there. Each adjudication turn changes only this
ledger and yields before remediation. The five-round gate and NEW blocking
criterion follow the seam fill, not an improvised round count.

| Turn / boundary | Dispatcher-read context depth | Action |
| --- | --- | --- |
| Turn 1 / round 0 | Not supplied; no estimate substituted | Yield this ledger. Record the dispatcher's reading on resume; evaluate around 200K and stop at a step boundary near 250K. |

Round-0 verification loop: suspected stale caller anchors and ambiguous
sampler attribution; confirmed the caller corrections by direct source search,
and rejected `_GpuSampler` as the core-node sampler by its sole instantiation
and `main`'s mode branch. Historical 16.303 s attribution remains pending the
seat profile. Confirmed the missing exception class and the two absent drop
ids by source inspection; their executable RED checks await the build turns.
No fixes applied and no final-state test claims made.

Round-0 bounded verification: `uv run --offline --no-sync python -` executed
only source AST checks and the isolated `_estimate_record` function (no GPU
imports), EXIT 0. Evidence: `work/wp-dr87/r0/ledger-check.txt`. Five checks
passed: ledger ASCII/LF/final newline; sole `_GpuSampler` construction in
`_clip_pass:808`; synthetic reserved-pool/estimate ratio 0.5; base exception
tuple excludes MemoryError; base drop set excludes 37724/50740/50341. The
ratio check demonstrates the denominator mechanism, not the historical flake's
cause. uv warned that the inherited main-tree `VIRTUAL_ENV` did not match the
project environment and was ignored; the checks completed in the project
environment. `git diff --check` exited 0; final status showed only this new
ledger. No code/test runner result is inferred from these document checks.

Locks honored this turn: only this owned ledger is added; product/tests,
frozen interfaces, `bench.py`, dependencies, spec/register and local config
remain untouched. No footage path accessed, no other worktree accessed, no
mailbox post, commit, GPU run, profile or deletion performed.
