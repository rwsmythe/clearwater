# WP-T4: parallel test workers

Status: rung 4 measured; Reviewer A round 1 adjudicated in one cleanup.
Reviewer A found zero new critical/major findings; its loop terminates per the
fill. Final settled-head two-leg gates, Reviewer B and acceptance remain pending.
Package diff base: `ba6e923`; measurement head: `dd49a15` (all six windows and
D3). Measurements were read from the worktree evidence, not copied from a
prompt. They describe the owner's Windows 11 / NTFS laptop, Python 3.12,
pytest 8.4.2, pytest-xdist 3.8.0 with local execnet popen workers and headless
Qt (`QT_QPA_PLATFORM=offscreen`). These are suite wall-time figures on the
same quiet host, not product timing figures (N6/V16). Product timing and memory
figures are obtained serially in their own windows.
The dispatcher granted each window and ran it alone, outside the sandbox and
without its mkdir shim. No heavy run was started by this cell.

## Result and limits

The two-leg suite preserved all selected tests and checks and saved **732.13 s
(16.04%)** in round 1 and **483.78 s (11.12%)** in round 2. The savings span
248.34 s and **4.92 percentage points**; they are not a stable single percentage.
BASELINE fell **4.71%** between rounds while PARALLEL+SERIAL rose **0.87%**.
The actual within-round comparison is retained below, rather than averaging
away the baseline drift. No third round is required by FINAL Q7; D2/D3 are
not rounds and do not participate in that decision.

The two-leg suite is bounded by the serial set: **SERIAL is 73.07% and 77.53%
of its same-round BASELINE**, about 73-77%. Changing which offscreen `gui`
cases or `slow` cases without a device remain serial is follow-on work for
the owner, with caution about their contracts and resource use. WP-T4 changes
no marker meaning and makes no further marker changes. In particular, a
large CPU-only synthetic export body remains slow/serial under today's rules.

N=4 is AD-28's cap. Both measured parallel legs passed, using at most
**6,967,926,784 B (6.49 GiB)** summed pytest-tree RSS and leaving at least
**7,047,557,120 B (6.56 GiB)** system memory available. Every preflight exceeded
5 GiB and every available-memory sample exceeded 2 GiB. This supports N=4 on
this measured host given the observed 11-16% whole-suite saving; it does not
establish N=4 as optimal on other hardware, authorize N>4, or provide an N=2
comparison. Product timing and memory figures are obtained serially in their
own N6/V16 windows; the suite wall-time figures here remain valid suite figures.

## Changes and dependencies

- `pyproject.toml`: only the dev-group grant comment and
  `"pytest-xdist>=3.6,<4",`; `uv.lock` adds pytest-xdist 3.8.0 and execnet 2.1.2.
  No existing version changes, no package removals; pytest stays 8.4.2.
- `tests/test_conftest_guard.py`: 16 worker cases, including the destructive
  positive control, real refusal checks and safe worker-plugin/temp-root proof.
- `tests/fixture_plugin.py`: serialize the shared generated cache around
  check/regenerate/re-verify; `tests/test_fixture_cache_lock.py`: four process,
  timeout, stale-lock and release regression tests. WP-T3's `verify_generated`
  and its surrounding block were not edited.
- `tests/test_io_video_encode_bench.py`: E1's required slow mark and exact
  reason comment; test body/bound unchanged.
- `tests/conftest.py`: one module-docstring paragraph about worker startup;
  no executable AST change. This report and the cumulative ledger complete
  the package's owned documentation. No product/src/tools/harness edit.

Installed metadata quotations: pytest-xdist 3.8.0 METADATA:6 states
`License-Expression: MIT`; execnet 2.1.2 METADATA:7 states
`License-Expression: MIT`. Both are the named granted additions. Independent
TOML comparison against `ba6e923:uv.lock` confirms exactly those additions
(`work/wp-t4/turn6-scope-e1.log`). Repeated `pytest --version --version` listed
xdist, and the unchanged dependency-grant test passed in turn 2.

## Partition proof and collection accounting

The original dispatch base collected 4768 tests: 3762 parallel + 1006 serial.
Accepted intervening work and WP-T4's added cases changed that suite. Current
collection on `f8b8f4b`, unchanged in content on `dd49a15`, is:

| Partition | IDs | Other partition deselected |
|---|---|---|
| All | 5078 | 0 |
| PARALLEL: not gpu and not footage and not gui and not slow | 4032 | 1046 |
| SERIAL: gpu or footage or gui or slow | 1046 | 4032 |

Sorted raw node sets have no duplicates; intersection and union symmetric
difference are both empty: **4032 + 1046 = 5078**. `turn5-intersection.setdiff`
and `turn5-union-difference.setdiff` under `work/wp-t4/` are empty. The original
rung-0 GNU sort/comm proof was run successfully by the dispatcher after the
sandbox's mapping denial; current sets were independently compared in Python.
Strict-marker collection passes. Literal escapes within parameter IDs are
preserved; path normalization must not alter those escapes.

Against turn-4 after-E1 lists, all changed IDs are accounted for:

| File under tests/ | All added / removed | Parallel added / removed | Serial added / removed |
|---|---|---|---|
| test_export_bench.py | 15 / 0 | 15 / 0 | 0 / 0 |
| test_gui_settings_dialog.py | 27 / 0 | 0 / 0 | 27 / 0 |
| test_jobs_batch.py | 4 / 0 | 4 / 0 | 0 / 0 |
| test_jobs_disk_space.py | 9 / 4 | 9 / 4 | 0 / 0 |
| test_jobs_export.py | 88 / 0 | 88 / 0 | 0 / 0 |
| test_jobs_export_photo.py | 18 / 0 | 15 / 0 | 3 / 0 |
| test_jobs_export_video.py | 32 / 0 | 23 / 0 | 9 / 0 |
| Total | 193 / 4 | 154 / 4 | 39 / 0 |

The four removals are main's superseded disk-estimate oracles, replaced by
WP3.14's DR-48 ratio/ceiling rules; the ledger names every removed ID. Existing
common IDs have zero partition transfers. Exact lists remain in
`work/wp-t4/turn5-*.{nodes,added.nodes,removed.nodes}` with JSON accounting.
New per-marker collections on **dd49a15**, before the docstring edit, identify
586 gpu, 17 footage, 441 gui and 20 slow IDs. Their union equals all 1046
serial IDs exactly; the marker lists are `work/wp-t4/turn6-<marker>.nodes`.

For **each** measured round: passed 4031+1036=5067; skipped 1+10=11;
failed/errors/xfailed/xpassed all 0+0=0. BASELINE is 5067 passed + 11 skipped
=5078; PARALLEL is 4032 outcomes and SERIAL is 1046. No test was lost.
Nine skips are absent look-check frames under the worktree's ignored
`work/wp1.3/` (`test_methods_assembly_v8.py:44`). The two remaining skip reasons
are the existing swscale/full-range refusal (`test_color_roundtrip.py:121`)
and no available photos (`test_photo_check.py:139`). PARALLEL has the swscale
skip; SERIAL has the other ten. These environment skips are consistent across
rounds and partitions. The dispatcher reports main's working tree has the
look-check frames and shows two skips; this cell did not execute main's suite.

## Footage guard evidence under workers

The new tests use fake footage/work trees beneath each test's `tmp_path` and
never the real footage folder. Existing planted bytes are checked unchanged
on refusal, with no `popen-gw*` entry under fake footage:

| Case | Coverage / observed result |
|---|---|
| w1 control, guard absent | Real `-n 2 --basetemp=<fake footage>` run deletes both planted files. The deliberately false unchanged-bytes assertion failed at `tests/test_conftest_guard.py:213`; final control expects the deletion. |
| w2 guard present | Nine equivalent/inside/ancestor basetemp targets refuse on the controller before workers exist, with exit 4, `footage guard` and folder name in stderr; planted bytes unchanged. |
| w3 guard present | PYTEST_DEBUG_TEMPROOT inside fake footage, TMP/TEMP/TMPDIR separately and together: five controller-refusal cases with the same exit/content/byte checks. |
| w4 safe work folder | Exit 0 with both worker IDs recorded, worker basetemp under controller root and guard module registered as a plugin on each worker. |

Each new case passed alone; whole file **60 passed**, including the original
cases. The dispatcher independently ran the committed file without the sandbox
shim: **60 passed in 49.64 s**, exit 0. The sandbox's mkdir shim accommodates
Windows owner-only temp ACLs; miniature child pytest inherited it only in the
sandbox run. The guard code itself remains unchanged.

Installed-source anchors (xdist 3.8.0 / pytest 8.4.2):

- `xdist/workermanage.py:333,337-341,349`: use controller args, obtain its
  basetemp and send `<controller-root>/popen-gwN` to each local worker.
- `xdist/remote.py:400,420-427`: assign worker `config.option.basetemp` and
  workerinput before entering pytest's command-line main/configure phase.
- `_pytest/main.py:285-287` and `_pytest/config/__init__.py:1119`: configure
  precedes session startup. `xdist/dsession.py:83-90` starts workers during
  session startup; the controller's guard therefore refuses before xdist
  clears/creates its root. Static hook ordering shows worker configure receives
  the assigned child root; w4 establishes worker plugin registration, not an
  independently observed worker-originated refusal.
- Current `tests/conftest.py:260-261` is the tryfirst guard. Q2 adds one
  module-docstring paragraph only. ASTs with that docstring removed are equal
  (`work/wp-t4/turn6-conftest-ast.log`, exit 0); no guard behavior was changed.

Worker-refusal coverage LIMIT (m5): w2/w3 refuse on the controller, so their
no-worker-directory assertions follow before any worker exists. No case makes
a worker refuse independently; a regression that made only that worker hook
inert would be unobserved. Within the declared local popen envelope a worker-only unsafe root is unreachable: xdist assigns a child of the controller root
only after that root was guarded and freshly created. A planted unsafe child
would require changed worker options or filesystem interference outside that
envelope. This cleanup records the limit rather than adding such a test.

The guard's existing DR-22 limits still apply: capture/tempfile probes can
write transient files before conftest loads, and explicit bypass/configuration
limits are not expanded by worker coverage.

## Cold-cache race, violators and exception list

Static reading found the normal cold gate worktree exposes one shared
`work/fixtures/generated` cache to multiple workers. The deterministic
reproduction used two processes, real manifest/FFmpeg verification, synchronized
cold misses and an injected two-second generator delay. One competing writer
held a partial clip while the other verified it. Against unlocked code, two
generators ran and real verification failed (`KeyError('streams')`); the committed
regression now re-established against byte-exact `ba6e923` plugin code fails
at **`tests/test_fixture_cache_lock.py:132`**, the `all(record["ok"]...)`
assertion. The staged test is byte-identical to the committed test. Its two
child exit codes are 0, two records exist and two generator calls are recorded;
one provider reports real partial-clip verification failure. Evidence:
`work/wp-t4/turn7-m1-stage.log` and `turn7-m1-red.log` (expected EXIT=1).
The original `turn3-regression-red.log` reports that same assertion at line 131
in an earlier pre-commit variant; its exact old bytes were not retained. The
old report carried that line forward as though it described the committed
variant. This corrects the citation without changing the test. Current lock
code remains green: four tests pass (`turn7-lock-green.log`, EXIT=0).
The actual cache
probe asserted exact resolved worktree containment before deleting only this
worktree's generated-cache directory. No footage or sibling directory was used.

The stdlib exclusive-create sibling lock covers recheck, generation and final
verification; after acquiring, `SampleProvider.path` re-verifies and reuses a
completed clip. Wait is bounded to 180 s with 50 ms polling. At age >=900 s it
fails with owner-confirmed cleanup instructions; age never authorizes stealing
an active lock. PID ownership is recorded and release occurs in `finally`.
A killed holder may require manual verified cleanup. No new dependency or
OS-specific liveness code was added. The locked actual cold-cache probe had
two successful providers and exactly one generator call. Four lock tests
passed, and eight related tests passed at `-n 4`. Red/green logs and exact
commands are in the ledger and `work/wp-t4/turn3-*.log`.

Recorded lock limits from Reviewer A (no code change in this cleanup):

- m2: a hard-killed holder leaves its lock. A caller waits up to 180 s until
  the 900 s stale threshold, then errors immediately until owner-confirmed
  cleanup; later tests can repeat those waits. PID is recorded in the file,
  but timeout/stale messages do not print PID or age. Recovery requires
  inspecting that lock and confirming the holder has stopped. Rules stay
  180 s / 900 s; no unsafe age-only stealing or OS-specific liveness is added.
- a1: the writer lock is not a reader lease. If two successive transient
  verification failures cause regeneration of a valid clip, an already-ready
  reader can encounter the in-place rewrite. This rare scenario remains a
  limit; no atomic-publication/tools or reader-lifetime change is made.
- a2: deleting a live holder's lock contrary to its cleanup instruction can
  make `finally: lock.unlink()` raise FileNotFoundError and mask the original
  result. A tolerant unlink is optional; it is not added in this cleanup.
- a4: the race regression proves one generation after re-verify, not that final
  verify stays lexically inside the lock. A safe lock/re-verify variant with
  final verify outside could pass; this is a coverage limit, not a failing
  safety property demonstrated by the test.
- a5: lock release relies on Windows 11 / NTFS POSIX-style deletion making
  the name reusable while a waiter's stat handle may be open. Older
  delete-pending filesystem semantics can yield PermissionError; this is
  an explicit operating-envelope dependency, not a portability claim.

D1, D2 and both measured parallel legs had **zero failures and zero violators**.
No test was relabelled to hide a worker failure. Static checks found no new
shared writable path/fixed port in added job tests; session synthetic clips
and references use worker-local `tmp_path_factory`. Shared sample generation
uses the lock. CPU selectors/forced-CPU settings cover new real CPU exports;
new real NVENC cases already carry gpu marks. The added WP3.14 cancellation
cases with a three-second bound remain reported watch items, not demonstrated
violators. The GUI-analysis-service <0.2 s watch case is actually unmarked
and remains in PARALLEL; it passed both measured legs. WP3.14/WP3.20R findings
belong to their owner's next touch and are not edited by this cell.

| WP-T4 exception (complete list) | Reason | Remedy |
|---|---|---|
| `tests/test_io_video_encode_bench.py::test_run_once_records_the_row_and_deletes_the_output` | timing bound, DR-58 (c); stays serial | `@pytest.mark.slow` plus exact reason comment; body and -0.05 telemetry-origin bound unchanged |

One node moved, no whole file, no xdist_group/loadgroup, no marker definition
changed. E1's initial light serial sandbox run failed its existing timing
bound; it was raised, not fixed or relaxed. Quiet-seat evidence now resolves
that item: both BASELINE and SERIAL logs in both rounds are exhaustive green
runs whose complete skip lists exclude E1. Quiet `-q` logs do not print an
individual PASS line, so this confirmation uses collected membership, exact
outcome totals and skip lists rather than inventing one. D3 explicitly records
E1 as a passing JUnit testcase, **19.306 s** total / **19.30 s** call in durations.

## Rung-4 windows and medians

All times below are the wrappers' **WALL_SECONDS**, not pytest's internal
elapsed string. Commands are copied from each `-command.txt`. Free memory
is GiB; RSS is the sampler's summed pytest process tree (workers and their
children), with available memory from psutil. Parallel sampler EXIT=0 in both
rounds; recorded sampler snapshot SHA-256 is
`64a57c731a09a7eca1e4c6f5b882975888ca0233434cc02b2c69e0dbc7ee0854`.

| Window | Start UTC | End UTC | Exact recorded command | N | Outcomes | Wall seconds | Exit | Free before GiB | Parallel peak RSS / min available B; GPU baseline/peak/rise |
|---|---|---|---|---|---|---|---|---|---|
| r1 baseline | 2026-10-27T19:09:09.9423940Z | 2026-10-27T20:25:14.7409654Z | `uv run pytest -q -rs --basetemp=work/wp-t4/r4-r1-baseline-tmp` | 1 | 5067 passed, 11 skipped, 2 warnings | 4564.795251 | 0 | 12.454144 | not sampled |
| r1 parallel | 2026-10-27T20:25:16.5545092Z | 2026-10-27T20:33:33.8627916Z | `uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=work/wp-t4/r4-r1-parallel-tmp` | 4 | 4031 passed, 1 skipped, 5 warnings | 497.303585 | 0 / sampler 0 | 12.627064 | 6,967,926,784 / 7,047,557,120; complete; GPU 134/1037/+903 MiB |
| r1 serial | 2026-10-27T20:33:35.5773853Z | 2026-10-27T21:29:10.9443000Z | `uv run pytest -q -rs -m "gpu or footage or gui or slow" --basetemp=work/wp-t4/r4-r1-serial-tmp` | 1 | 1036 passed, 10 skipped, 4032 deselected, 1 warning | 3335.364086 | 0 | 12.748402 | not sampled |
| r2 baseline | 2026-10-27T21:30:32.8419642Z | 2026-10-27T22:43:02.7659107Z | `uv run pytest -q -rs --basetemp=work/wp-t4/r4-r2-baseline-tmp` | 1 | 5067 passed, 11 skipped, 2 warnings | 4349.919173 | 0 | 12.545288 | not sampled |
| r2 parallel | 2026-10-27T22:43:03.8385947Z | 2026-10-27T22:51:17.3838295Z | `uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=work/wp-t4/r4-r2-parallel-tmp` | 4 | 4031 passed, 1 skipped, 5 warnings | 493.541237 | 0 / sampler 0 | 12.853287 | 6,854,651,904 / 7,504,404,480; complete; GPU 138/1049/+911 MiB |
| r2 serial | 2026-10-27T22:51:18.9534591Z | 2026-10-27T23:47:31.5505229Z | `uv run pytest -q -rs -m "gpu or footage or gui or slow" --basetemp=work/wp-t4/r4-r2-serial-tmp` | 1 | 1036 passed, 10 skipped, 4032 deselected, 1 warning | 3372.593689 | 0 | 12.952400 | not sampled |

| Round | BASELINE s | PARALLEL s | SERIAL s | P+S s | Saving s | Saving % | SERIAL / BASELINE |
|---|---|---|---|---|---|---|---|
| 1 | 4564.80 | 497.30 | 3335.36 | 3832.67 | 732.13 | 16.04% | 73.07% |
| 2 | 4349.92 | 493.54 | 3372.59 | 3866.13 | 483.78 | 11.12% | 77.53% |
| Median (two rounds) | 4457.36 | 495.42 | 3353.98 | 3849.40 | see each round | see each round | see each round |

P+S difference is **33.467256 s**: **0.8732%** using r1 as denominator,
**0.8657%** using r2. Both are below 15%; no r3 is requested or included.
Windows are interleaved B/P/S, sequential and on the same quiet host. These
are suite wall-time figures, not N6/V16 product timing or memory figures. R1 has 498 RSS observations / 499 GPU queries; r2 has 494 /
495. Neither has GPU gaps, RSS access denied, a <2 GiB sample or remaining
child PIDs. Maximum RSS interval is 1.156 s / 1.110 s. R1 has two successful
slow GPU reads (longest 0.953 s, maximum observation age 1.343 s); r2 has
none (longest 0.141 s, maximum age 0.406 s). The scratch sampler uses a
one-second RSS loop and independent GPU-query thread with a fixed five-second
timeout, records actual query times/age, and preserves genuine query errors.
Its code/data stay under work and are not committed. D1's old five GPU gaps
void a complete GPU figure there; D2 validated the corrected sampler and is
still diagnostic only.

## D3 diagnostic: serial cost by marker and ten longest tests

D3 ran separately on `dd49a15`, not as a third round:

`uv run pytest -q -rs -m "gpu or footage or gui or slow" --durations=0 --junitxml=work/wp-t4/d3-serial-junit.xml --basetemp=work/wp-t4/d3-serial-tmp`

Start **2026-10-27T23:47:41.3884587Z**, end **2026-10-28T00:43:12.7028183Z**, wall
**3331.3104851 s**, EXIT **0**, free-before
**12.675758 GiB**; 1036 passed, 10 skipped, 4032 deselected.

The four marker collections use `--collect-only -q --strict-markers` with
`-m gpu`, `-m footage`, `-m gui`, `-m slow` on dd49a15. All exit 0; the
sandbox-only shim/cache environment is recorded in the ledger. Each JUnit
case maps uniquely to a collected serial ID, including class/parameter IDs;
all 1046 cases match exactly. Per-marker time is the sum of each testcase's
JUnit `time` (setup + call + teardown), **not an independent marker run**.
A multi-marked testcase contributes its whole time under every carried marker.

| Marker | IDs (skipped) | Sum of JUnit testcase seconds |
|---|---|---|
| gpu | 586 (4) | 1843.366 |
| footage | 17 (1) | 2001.211 |
| gui | 441 (0) | 67.769 |
| slow | 20 (5) | 2931.947 |
| Of which in two or more markers (counted once here) | 13 | 2011.870 |
| De-duplicated SERIAL total | 1046 (10) | 3326.963 |

There are **8 two-marker and 5 three-marker cases**. The overlap row is their
unique combined cost, not an amount to subtract once from the four marker
rows. Those rows sum to **6844.293 s**; repeated memberships contribute
**3517.330 s** beyond the de-duplicated **3326.963 s**. D3 wall is
**3331.3104851 s**; residual **4.3474851 s (0.1305%)** covers unassigned
launch/collection/session-hook/reporting/teardown overhead and timing precision.
Fixture setup/teardown attributed to a testcase is already inside its JUnit
time, including module/session fixtures; it is not added to the residual.

The ten longest cases by JUnit time follow. Phase values are the rounded
`--durations=0` output (two decimals); pytest still hid phases below 0.005 s
without `-vv`. Such phases are shown **<0.005**, never invented as zero.
Consequently rounded phase sums need not equal JUnit's three-decimal total.

| Rank / node ID | Markers | JUnit total s | Setup s | Call s | Teardown s | Cost |
|---|---|---|---|---|---|---|
| 1. `tests/test_jobs_export_video.py::test_v4_synthetic_5k3_8_7_clip` | slow | 870.740 | 0.01 | 870.73 | <0.005 (hidden) | Body |
| 2. `tests/test_jobs_export_video.py::test_gx011627_through_the_engine_keeps_every_mandatory_and_required_item` | gpu, footage, slow | 725.154 | <0.005 (hidden) | 725.15 | <0.005 (hidden) | Body |
| 3. `tests/test_io_video_encode.py::test_gx011627_nvenc_levels_give_distinct_sizes` | gpu, footage, slow | 472.503 | <0.005 (hidden) | 472.50 | <0.005 (hidden) | Body |
| 4. `tests/test_io_video_encode.py::test_gx011627_through_the_sink_keeps_every_mandatory_and_required_item` | gpu, footage, slow | 207.834 | 0.01 | 207.83 | <0.005 (hidden) | Body |
| 5. `tests/test_color_roundtrip.py::test_pair_round_trip_on_the_owners_main_case` | footage, slow | 161.405 | 0.01 | 161.40 | <0.005 (hidden) | Body |
| 6. `tests/test_io_video_decode_hw.py::test_the_real_clip_decodes_to_its_pts_and_the_reference_bytes` | footage, slow | 140.412 | 41.90 | 98.51 | <0.005 (hidden) | Body + module-fixture setup |
| 7. `tests/test_io_video_decode_hw.py::test_the_real_clip_through_the_forced_default_pipe_is_identical` | footage, slow | 126.265 | <0.005 (hidden) | 126.26 | <0.005 (hidden) | Body |
| 8. `tests/test_io_video_decode_hw.py::test_the_real_clip_through_cuda_decode_is_identical` | gpu, footage, slow | 94.030 | <0.005 (hidden) | 94.03 | <0.005 (hidden) | Body |
| 9. `tests/test_prototype_backend.py::test_bench_gpu_records_graphics_memory` | gpu | 59.999 | <0.005 (hidden) | 60.00 | <0.005 (hidden) | Body |
| 10. `tests/test_prototype_clip.py::test_bench_whole_clip_modes_record_their_pass` | gpu | 58.139 | 0.01 | 58.13 | <0.005 (hidden) | Body |

All ten are dominated by test-body/call cost. The sixth additionally charges
**41.90 s** of setup: `tests/test_io_video_decode_hw.py:75-107` defines the
module-scoped footage probe and independent FFmpeg `footage_reference` hash
fixture, consumed first by that test. This is a fixture-scope/placement question
for the owner, distinct from its **98.51 s** body cost; it is already shared
across the module, not a claim that every test repeats it. Other top-ten setup
phases are <=0.01 s and all teardowns are hidden below 0.005 s. The dominant
870.73 s synthetic export and the other long call phases belong to their tests.
No fixture, test body or marker is changed on this evidence.

JUnit XML and durations text remain only under `work/wp-t4/`; no raw XML,
full durations listing, hostname, absolute footage path or image/metadata is
committed. Privacy check `turn6-privacy-check.log` validates all ten node IDs
against an ASCII test-name grammar, rejects path/coordinate/location tokens,
and verifies the only embedded footage clip name, `gx011627`, already occurs
in committed reports (`git grep -i gx011627 HEAD -- docs/reports`). The report
carries only the requested aggregate tables, ten node IDs and phase values.

Follow-on for CHARC at accept: the first four export test bodies in the table
sum to **2276.21 s**, about **68.3% of D3's serial wall**. These WP3.14/WP3.10
bodies' size is the lever for the owner; it is distinct from the setup/fixture
question above. CHARC owns writing D3's register row at accept; this report
does not claim that row already exists and makes no test or marker change.

## Raised GPU finding

Graphics-card memory activity reproduces with complete observations in **D2,
r1 and r2**, peaks **1036 / 1037 / 1049 MiB** (rises **1036 / 903 / 911 MiB**
from baselines **0 / 134 / 138 MiB**). The verified module-import probes are
`tests/test_prototype_backend.py:23`, `tests/test_prototype_clip.py:41` and
`tests/test_prototype_temporal.py:47`, each calling `select_backend("auto")`.
All reach `prototype.backend.select_backend` -> `_probe_gpu` -> actual CuPy
allocation/kernel at `tools/prototype/backend.py:211`. Fixing only one module
would leave the other probes. Modules import before marker deselection in
each worker, so the nominal non-GPU expression does not prevent that probe.
Static inspection found no new unmarked GPU execution path in the added job
tests. System-wide memory samples cannot attribute every MiB exclusively to
that probe. The finding remains raised; **marker meaning and a GPU-probe
redesign are outside WP-T4**. These are sampled peaks, not continuous maxima.

## Verification and remaining acceptance

The cumulative ledger records suspected, independently confirmed, rejected
false-positive and fixed items: deterministic cache race fixed; guard bypass
suspect rejected by positive/negative controls; collection accounting verified;
scratch verifier escape error corrected; old sampler timeout fixed in scratch;
GPU import use raised; E1 sandbox timing failure resolved by quiet-seat runs;
new cancellation bounds retained as watch items. No product-code fix, dependency
beyond the named pair, other-package test edit or unexplained deviation occurred.
The turn-6 AST proof confirms the conftest change is documentation only.

Turn-6 static gates all EXIT=0: `uv run ruff check .` passes;
`uv run ruff format --check .` reports **238 files already formatted**;
`uv run mypy` reports **no issues in 136 source files**. Evidence is
`work/wp-t4/turn6-{ruff-check,ruff-format,mypy}.log`. `git diff --check`,
AST/privacy/scope and table checks are recorded in the final verification log.

Turn-7 cleanup static gates also all EXIT=0: ruff check passes, ruff format
reports **238 files already formatted**, and mypy finds **no issues in 136
source files** (`work/wp-t4/turn7-{ruff-check,ruff-format,mypy}.log`). Current
lock tests are **4 passed**; all/P/S strict collections remain
**5078 / 4032 / 1046**, with raw node sets unchanged and exact partition proof.
There is no changed Python/test file in the cleanup; the test run verifies
m1's current green. Final scope/runner/privacy checks and diff whitespace
validation are in `work/wp-t4/turn7-final-check.log`.

Reviewer A ran on `5e6a8d3` through the driver's pinned Claude Opus/high
invocation (modelUsage claude-opus-5-5), read-only. Its verdict is
`VERDICT: NO_NEW_CRITICAL_MAJOR`; all seven CLAIMS_FIRST checks hold.
The six minor and five advisory findings are individually adjudicated in the
ledger: four documentation findings fixed, seven limits/watch items recorded.
There are zero new blocking findings, so the loop terminates after round 1
and this single cleanup; no round 2 is requested. The reviewer independently
ran four lock tests and 60 guard tests under workers. Driver assertions and
permission-denial provenance are recorded in the ledger. Final PARALLEL and
SERIAL runs are now requested on the committed cleanup head because files
changed after rung 4; those final legs have not run. The harness gate is not required for this
package's owned files. Final acceptance and changes to the fill/CLAUDE.md belong
to the orchestrator. Open items: final two-leg gates, Reviewer B at the
orchestrator's seat, return/owner acceptance, and the recorded limits and
GPU/serial-set/other-package timing follow-ons.

## Gate text for the orchestrator

Exact measured PARALLEL/SERIAL commands are in the six-window table, copied
from the corresponding command files. For example, r1 executed:

```text
uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=work/wp-t4/r4-r1-parallel-tmp
uv run pytest -q -rs -m "gpu or footage or gui or slow" --basetemp=work/wp-t4/r4-r1-serial-tmp
```

R2 used the same expressions with its own `r4-r2-...-tmp` roots, exactly as
tabulated. Both legs run separately with `QT_QPA_PLATFORM=offscreen`, on one
quiet host/window at a time; any explicit basetemp must be a fresh working-folder path, never footage. Do not replay a measured evidence prefix.

Proposed replacement for GATE_CHECKS's `uv run pytest` sentence (orchestrator
edits the fill, keeping its other hardware and harness requirements):

> Set `QT_QPA_PLATFORM=offscreen`; choose a new RUN identifier for each gate.
> Every execution and collection leg must use its own fresh `--basetemp`
> path under `work/`, never footage; replace RUN consistently in the examples.
> Before each heavy leg check at least 5 GiB available with
> `uv run python -c "import psutil; assert psutil.virtual_memory().available >= 5*2**30"`.
> Run `uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=work/pytest-gate-RUN-parallel`,
> then `uv run pytest -q -rs -m "gpu or footage or gui or slow" --basetemp=work/pytest-gate-RUN-serial`,
> one heavy job at a time. Collect all and both expressions with the three
> concrete commands below. Retain only node-ID lines (starting `tests/` and
> containing `::`), excluding headers/summaries/warnings; require duplicate-free
> lists, empty parallel/serial intersection, union equal to all, and
> parallel count + serial count = all count. Require green execution legs and
> passed + skipped + xfailed + xpassed in each leg to equal its selected count,
> with zero failures/errors. Recollect for later packages; do not freeze the
> WP-T4 counts. Product timing and memory figures from serial runs only, in
> their own N6/V16 windows. New parallel-leg tests: per-test `tmp_path`, no
> shared path; an exception is `slow` with a reason. Preserve the footage
> guard. Where a sampler is available, stop/report if N=4 sampling falls below
> 2 GiB available; the scratch sampler is not a committed gate prerequisite.
>
> `uv run pytest --collect-only -q --basetemp=work/pytest-gate-RUN-collect-all > work/pytest-gate-RUN-all.txt`
>
> `uv run pytest --collect-only -q -m "not gpu and not footage and not gui and not slow" --basetemp=work/pytest-gate-RUN-collect-parallel > work/pytest-gate-RUN-parallel.txt`
>
> `uv run pytest --collect-only -q -m "gpu or footage or gui or slow" --basetemp=work/pytest-gate-RUN-collect-serial > work/pytest-gate-RUN-serial.txt`

All commands above use committed dependencies, pytest and the standard library;
no uncommitted helper is required. `work/` and the fresh evidence names must
exist/be reserved as appropriate before redirecting; choose a different RUN
rather than overwriting prior evidence. On this head the required collection
arithmetic is **4032+1046=5078**, with the exact raw-set proof in the ledger.

Proposed one-line CLAUDE.md Conventions pointer (CHARC writes it):

> Run the two-leg pytest gate in `docs/review-gate-clearwater.md` GATE_CHECKS (WP-T4/AD-28: median suite P+S wall 3,849 s, about 64 min; same-round savings 16.0% / 11.1%; measurements and limits in `docs/reports/wp-t4-parallel-tests.md`); product timing and memory figures from serial runs only.

CHARC's suite figures of record (`144f9735`) are the same-round comparisons
**-16.0% / -11.1%** with a **4.9 percentage-point spread**, a baseline move of
**4.7%** versus P+S under **1%**, and median P+S **3849.40 s (64.16 min)**.
The PARALLEL leg is stable and fast: **493.54-497.30 s** (about 494-497 s);
SERIAL is the floor: **3335.36-3372.59 s** (about 3335-3373 s). These are
suite wall-time figures on the same quiet host, not product timing figures
(N6/V16). Product timing and memory figures are obtained serially in their own
windows. This cell edits neither destination and creates no docs/testing.md.
