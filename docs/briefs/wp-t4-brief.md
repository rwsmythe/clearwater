# WP-T4 -- Parallel test workers (dispatch brief, FINAL)

**Status:** FINAL 2026-10-27 (CHARC `3c3c35d7e40b525e`); written by a drafting helper for the orchestrator (generation 12)
at CHARC's ruling `6f725eee`. Approved; base = the main commit named in the dispatch prompt. Source: the owner's commission (2026-10-27, "commission it"), CHARC commission
`f0741947`, AD-28 (`docs/decisions.md`). Spec **v0.5.5**; no spec clause changes. Tests, a
dependency and a report only: no product code, nothing under `src/clearwater/interfaces/`
(frozen) or `src/`.

- Cell: `implementer-sonnet-high` (Claude lane) or `implementer-codex-sol-high` (Codex lane),
  chosen at dispatch by the pace tiebreak (R3); the brief works for either. Dispatched THIRD,
  after the calibration pair; its figures go to HD-1 as a third data point outside the pair.
- Worktree `.worktrees/wp-t4`, branch `wp-t4`.
- Lane differences: Claude lane commits itself; Codex lane ends every turn with a FILES CHANGED
  block and the orchestrator commits (`.claude/agents/implementer-codex-sol-high.md`).

**Why.** "The full suite runs serial: `uv run pytest`, 4,768 tests collected on this base, 27-45
min per gate run" (AD-28: WP3.10 candidate 2715 s, tranche B 1579 s, WP3.11 1935 s). AD-28
splits it into two legs: a PARALLEL leg (`pytest-xdist`, N <= 4) over the tests carrying none of
`gpu`, `footage`, `gui`, `slow`, and a SERIAL leg over the rest unchanged. This package installs
the dependency, makes the parallel partition safe under workers, proves the footage guard holds
under workers, and measures the saving. Timing, memory and exclusive-window figures stay serial
(AD-28: "a figure produced under workers is not a figure of record").

| Field | Content |
|---|---|
| ID and title | WP-T4 -- parallel test workers (AD-28) |
| Goal | Gate suite wall-clock falls without weakening a single check: the two legs together run exactly the tests the serial suite runs, the parallel leg is green three times running at `-n 4`, and the temp-root footage guard (WP-T1, DR-21/22) refuses on workers as on the controller. |
| Files owned | `pyproject.toml` (the `dev` dependency group ONLY: one line plus its grant comment) and `uv.lock`; test files under `tests/` that the parallel runs show must change (test-only, each listed in the report); `tests/test_conftest_guard.py` (new worker cases); `tests/conftest.py` (ONE docstring paragraph only, Q2); `tests/fixture_plugin.py` (only if rung 3 reproduces the cold-cache race, Q3); `docs/reports/wp-t4-parallel-tests.md` (NEW); `docs/proofs/wp-t4-ledger.md` (NEW). NOTHING else. |
| NOT owned | `docs/review-gate-clearwater.md` (the orchestrator edits GATE_CHECKS at accept), `CLAUDE.md` (CHARC adds one pointer line at accept), `docs/testing.md` (not created: Q1), `tests/harness/`, `tools/`, `scripts/`, `.claude/`, `src/`; any test file owned by a package in flight at dispatch (the dispatch row names them; a violator there is RAISED in the report, never edited). |
| Interfaces consumed | none. |
| Dependencies | ONE grant: `pytest-xdist` in the `dev` group (AD-28, MIT, N13 check done by CHARC). Its transitive `execnet` (not in `uv.lock` today) arrives with it (Q4). Nothing else; no `pytest-randomly`, no `pytest-timeout`, no `psutil` change (already in `dev`). |
| Hardware flags | Heavy windows, NOT `exclusive` in the plan 4.3 sense (no figure of record), but every full or parallel run is ONE heavy job: the orchestrator grants each window, nothing else heavy runs, free memory >= 5 GB checked before each run (rung 0 gives the command). |
| Done | Plan 4.5; `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`, and BOTH legs green (these ARE the pytest gate here); report and ledger written; the harness gate is NOT required (nothing in `scripts/`, `.claude/`, kernel docs or `tests/harness/` is owned). |

## Task ladder

Run the build cycle (produce, validate, converge; `docs/dispatch-recipe.md` section 2) per rung.
The two legs, verbatim (WinGet links on PATH as usual; `QT_QPA_PLATFORM=offscreen`):

    PARALLEL  uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow"
    SERIAL    uv run pytest -q -rs -m "gpu or footage or gui or slow"
    BASELINE  uv run pytest -q -rs          (no -n)

Route every run to a file under `work/wp-t4/` (`> file 2>&1; echo EXIT=$? >> file`) and read the
summary lines only. Copy the main tree's `clearwater.local.toml` into the worktree first
(orchestrator; the footage tests skip and look-check tests fail without it).

**Rung 0 -- facts and partition proof (light, no window).**
1. `uv sync`. Record the base SHA and `git status` clean.
2. Collection counts, recorded in the report (measured on main `87b8b34`): all 4,768; parallel
   leg 3,762 (1,006 deselected); serial leg 1,006 = `gpu` 579, `footage` 16, `gui` 411, `slow`
   16 (these sum to 1,022: 16 tests carry two markers). The ruling `6f725eee` quotes 4,766;
   report any difference you find on your base.
3. Partition proof: write the node-id lists of all, parallel and serial with
   `--collect-only -q` to `work/wp-t4/`; `sort` and `comm` show parallel and serial are disjoint
   and their union is the full list.
   CHECK: both `comm` outputs empty, counts add (3,762 + 1,006 = 4,768 on this base).

**Rung 1 -- the dependency (commission item 1).**
1. Add `"pytest-xdist>=3.6,<4",` to the `dev` group of `pyproject.toml` with a one-line comment in
   the file's grant style: `# WP-T4 (AD-28, CHARC grant; MIT): parallel test workers.` Run
   `uv lock` WITHOUT `--upgrade`, then `uv sync`. If `uv lock` cannot reach the index (a Codex
   sandbox may not), yield with the pyproject edit and the exact command; the orchestrator runs it.
2. CHECK: `git diff --stat` shows `pyproject.toml` (that hunk only) and `uv.lock`; the lock diff
   ADDS packages only: `pytest-xdist` and `execnet`; no existing package changes version
   (`pytest` stays 8.4.2). `uv run pytest --version` lists the xdist plugin. Quote both licences
   from the installed metadata. `tests/test_io_photo_rules.py::test_the_dependency_lines_are_the_wp36_grant`
   still passes (it bans only four named packages).

**Rung 2 -- the guard holds on workers (commission item 4).** Read first (cite file:line in the
report): how the installed xdist gives a worker its `basetemp` (`xdist/workermanage.py`,
`xdist/remote.py`) and the order against the guard's `pytest_configure` in `tests/conftest.py`.
The existing 26 test functions of `tests/test_conftest_guard.py` run the miniature repository WITHOUT `-n`,
so they do not cover workers; add cases there, reusing `_build`, `_run`, `_assert_refused`,
`_snapshot`, `_assert_under` (every path under the test's `tmp_path`; never the real footage):
- (w1) control: guard absent (`guard=False`), `-n 2`, `--basetemp=<fake footage>`: the planted
  files are gone (the harm is real under workers; the refusals below then prove something).
- (w2) guard present, `-n 2`, `--basetemp` equal to, inside and above the fake footage (reuse
  the existing parametrized targets that matter): exit code 4, `footage guard` and the folder
  named in stderr, planted bytes unchanged, no `popen-gw*` entry under the fake footage.
- (w3) guard present, `-n 2`, `PYTEST_DEBUG_TEMPROOT` inside it, and `TMP`/`TEMP`/`TMPDIR`
  inside it: refused as (w2).
- (w4) guard present, `-n 2`, `--basetemp` inside the fake WORKING folder: exit 0 AND the run
  really used workers: a mini test records `PYTEST_XDIST_WORKER`, the worker's
  `config.option.basetemp` (under the controller's basetemp) and that the guard module is a
  registered plugin on the worker, into a file the test then reads.
CHECK: each new case run alone and the whole file pass; (w1) fails the "bytes unchanged"
assertion if run against the guard-less tree (name the failing line in the ledger as the positive
control). If execution shows the guard does NOT hold on a worker, STOP with the reproduction
(a `conftest.py` code change is not owned, Q2).

**Rung 3 -- find and fix the violators (commission item 3).** A violator is a parallel-leg test
that fails, errors or hangs under `-n 4` and passes serially (confirm by re-running its node ids
alone, serial). A test that fails serially too is NOT a violator: record it as pre-existing and
raise it; do not fix it.
1. Static pass first (light), results into the ledger: tests that write outside their own
   `tmp_path` (the real `work/`, `load_local_config().working_path`, `REPO_ROOT / "work"`); module
   or session state that assumes one process; fixed ports or file names; tests that depend on
   another test's side effects or on order (xdist reorders). Known item:
   `tests/fixture_plugin.py:41` `GENERATED_DIR = REPO_ROOT / "work" / "fixtures" / "generated"`
   is ONE cache shared by every worker, and `SampleProvider.path` (`:167-205`) regenerates the
   89 MB `ad14-flicker.mkv` into it (`generate.generate(...)` at `:197`) when it is absent or
   stale. A fresh worktree has no `work/`, so a gate run starts cold: N workers can generate the
   same file at once. Tests using it: `rg "ad14-flicker" tests` (at least
   `tests/test_analysis_v3.py`, `tests/test_fixtures.py`).
2. Cold-cache probe (cheap): delete ONLY the worktree's own `work/fixtures/generated/` (assert the
   path is inside the worktree first), then run the flicker-using test files at `-n 4`. If the
   race reproduces (a corrupt or half-written clip, a failed hash check, a file-in-use error),
   fix it in `tests/fixture_plugin.py` (Q3): serialize check-and-regenerate with a stdlib
   exclusive-create lock file beside the cache, re-verify after acquiring it, a bounded wait and
   a stale-lock rule; add a test that fails without the lock (two processes, cold cache). If it
   does not reproduce in three tries, record the tries, leave the plugin unchanged and say the
   gate relies on timing luck.
3. Window runs: PARALLEL leg at `-n 4`; classify the failures; fix each violator test-only (a
   per-test `tmp_path`, a unique name, no shared path); repeat until a run has ZERO failures.
   Order of remedies: (1) fix the test; (2) `@pytest.mark.slow` with a one-line reason comment;
   (3) `@pytest.mark.xdist_group("<name>")` ONLY if tests must share a worker, which also makes the
   parallel command `-n 4 --dist loadgroup` (AD-28 says no `xdist_group` unless a test proves it
   needs one). A needed product or `tools/` change is a STOP with a reproduction.
4. Mandatory exception E1 (DR-58 (c), commission: "the timing-bound test stays serial"):
   `tests/test_io_video_encode_bench.py::test_run_once_records_the_row_and_deletes_the_output`
   (`:272`, bound `-0.05 < offsets["telemetry_origin"]` at `:321`) gets `@pytest.mark.slow` with
   the reason "timing bound, DR-58 (c); stays serial". Do not widen the bound. Watch list, treated
   like any other test if it fails: `tests/test_gui_analysis_service.py:199` (`< 0.2` s bound,
   unmarked, so it is in the parallel leg).
   CHECK: the exception list (test id, reason, remedy) is complete in the ledger and the report;
   `--strict-markers` still passes (`slow` is registered in `pyproject.toml`; confirm xdist
   registers `xdist_group` before using it); no marker's meaning changed. More than 20 tests moved out, or a whole file: yield (Q5).

**Rung 4 -- settled rounds, timing, memory (commission items 2 and 5).** On the frozen tree run
three ROUNDS, interleaved so host drift hits both arms alike. A round is: BASELINE, then PARALLEL,
then SERIAL, each its own window and file. Before each run: `uv run python -c "import
psutil;print(psutil.virtual_memory().available/2**30)"` must print >= 5. During every PARALLEL
run a stdlib-plus-psutil sampler (kept in `work/wp-t4/`, not committed; say what it does in the
report) polls once a second: the summed RSS of the pytest process tree, the system's available
memory, and GPU memory if `nvidia-smi` is present.
CHECK:
- all three PARALLEL legs have zero failures (a failure restarts the three rounds after a fix);
- per round, PARALLEL + SERIAL outcome counts add to the BASELINE's (passed, skipped, failed,
  xfailed) and 3,762 + 1,006 = the collected total;
- the BASELINE passes unchanged (the new `slow` marks do not remove a test from the suite);
- report medians of wall-clock for BASELINE and for PARALLEL + SERIAL, each leg separately, with
  start times and the conditions ("same quiet host, not a figure of record");
- the peak summed RSS and the minimum available memory at N=4; any sample below 2 GB available is
  a failed run to report (Q8), not a reason to lower N yourself;
- any GPU-memory rise during the PARALLEL leg means an unmarked test uses the graphics card: report
  it as a finding (marker meaning is out of scope), do not fix it;
- N and why: N=4 is the AD-28 cap; justify from the measured saving and the memory peak.
  An optional extra PARALLEL run at N=2 only if the orchestrator grants a window.

**Rung 5 -- report, gate text, ledger, gates.**
1. `docs/reports/wp-t4-parallel-tests.md`: claims; the partition proof; the guard evidence (rung
   2, with the xdist source lines); the violators found (suspected / confirmed / rejected / fixed)
   and the exception list; the figures table (rung 4); the N rationale; the pre-existing failures
   raised; limits; and a section "Gate text for the orchestrator": the exact two-leg commands as
   executed, a proposed replacement for the fill's GATE_CHECKS `uv run pytest` sentence (the legs,
   "figures from serial runs only", "new parallel-leg tests: per-test `tmp_path`, no shared path;
   an exception is `slow` with a reason"), and the one-line CLAUDE.md pointer. The cell edits
   neither file.
2. `docs/proofs/wp-t4-ledger.md`: the verification-loop record, one row per heavy run (start, end,
   command, N, counts, exit, free memory before, peak), the review rounds, depth readings.
3. Final head: ruff check, ruff format --check, mypy, then BOTH legs green once more if any file
   changed after the last round.

## Declared operating envelope

Windows 11, Python 3.12, pytest 8.4.2 (`uv.lock`), pytest-xdist 3.x with `execnet` popen workers,
`-n 4`, the owner's laptop, NTFS, headless Qt (`QT_QPA_PLATFORM=offscreen`). Out of envelope:
`-n auto` or N above 4, `--dist` modes other than `load` and `loadgroup`, remote or ssh workers,
another OS, the two legs running together or beside another heavy job, `pytest-randomly`, and the
guard's documented limits (DR-22).

## Review loop (Reviewer A) -- per `docs/review-gate-clearwater.md` Part 1

- **Tier FAST** (Q6: tests, a dependency line and a report; no shipped output). Never tier the
  rigor. Round policy is the fill's (zero new blocking terminates; five-round gate); CHARC's
  recommended cap for this package is ONE round with a single cleanup, as WP-T1 and WP-T2.
- **Claude lane** (reviewer = Codex, WSL, codex-cli 0.162.1): per-call flags
  `-m gpt-6-luna -c model_reasoning_effort=medium -s read-only --skip-git-repo-check` (the `fast`
  tier, `docs/codex-reviewer.md`); one probe through the exact invocation first; diff generated
  Windows-side with `git -C <worktree> diff -U8 <base>..HEAD -- . ':!uv.lock' ':!docs/proofs'`.
  Assertions (all `grep -a`): banner model and effort match; every `^ERROR` and `ERROR codex_core`
  line classified by provenance; the `^tokens used` footer; an anchored VERDICT line; at least one
  `^ succeeded in`; `grep -a -n 'docs/proofs\|wp-t4-ledger'` with every hit classified as echo or
  access. The prompt carries the EXECUTED/REASONED paragraph verbatim from `docs/codex-reviewer.md`
  and: "Do NOT read `docs/proofs/` or anything under `clearwater-review-evidence`; those are
  withheld. Never read or list `/mnt/c/Users/rwsmy/clearwater-footage`."
- **Codex lane** (reviewer = Claude, run by the driver between turns): `scripts/codex_cell.py
  review`, `claude -p --model opus --effort high` per the fill's Part 1 lane paragraph, tier fast
  = Sonnet medium; assertions as that paragraph (the `modelUsage` key, `is_error` false, a
  `VERDICT:` line, empty `git status --porcelain` afterwards, every finding EXECUTED or REASONED).
  Findings reach the cell on its next turn for its own adjudication.
- **Evidence:** `C:\Users\rwsmy\clearwater-review-evidence\wp-t4\rN\` with md5s; ledger
  `docs/proofs/wp-t4-ledger.md`.
- **WHAT TO EXAMINE:**
  - whether any test left in the parallel leg still shares a path, cache, port or ordering
    assumption with another (the cold `work/fixtures/generated` cache first);
  - whether the guard refusal on workers is proved by a test that fails without the guard;
  - whether every exception is justified and changed no marker's meaning;
  - whether the lock diff is exactly xdist and execnet and the `pyproject.toml` hunk is the
    `dev` line;
  - whether the partition proof and the leg counts in the report match the commands as run;
  - whether the report's commands are what was executed.
- Reviewer B is the orchestrator's seat pass on the merge candidate (fill Part 2 item 2), always
  the other model from the implementer.

## Notes for the cell

- **Windows (X5).** Every PARALLEL, SERIAL and BASELINE run is a window the dispatcher grants by
  message; one heavy job at a time. Claude lane: run in the background with output to a file under
  `work/wp-t4/`, wait with foreground calls, and read the verdict from the file's summary line AND
  its `EXIT=` line (started and finished are two facts). Codex lane: yield with the exact command
  line; the orchestrator runs it and hands back the output path. Send `WINDOW RELEASED: <summary>`
  after each. Inner loops run only `tests/test_conftest_guard.py` and the files you are fixing.
- **Yields.** Report `scripts/cell_depth.py` at every yield (~250K evaluation point, ~400K STOP).
  YIELD at the end of rung 3 (violator list and exception list), before rung 4.
- **Return report** = your FINAL message, under about 70 lines, delivered to your dispatcher by
  your messaging tool (Codex lane: followed by the FILES CHANGED block): per-commit changes; the
  gate lines (both legs, counts, skips); the partition proof; the guard cases and the positive
  control; the violators and the exception list; the figures table with medians and the memory
  peak; N and why; pre-existing failures raised; review rounds and assertions; the locks; open
  items.
- **STOP for:** any product, `tools/` or `src/clearwater/interfaces/` change; a `tests/conftest.py`
  code change; a guard that does not hold on a worker; more than 20 tests (or a whole file) leaving
  the parallel leg; a lock diff that changes any existing package; any dependency beyond xdist and
  execnet; a violator in a file owned by an in-flight package; memory below 2 GB available at
  N=4; any write outside the worktree, `tmp_path` and `work/`.
- **Working rules:** `uv sync`. Commit by pathspec with `git -c core.autocrlf=false commit -m
  "<type>(wp-t4): ..." -- <paths>` (`build(wp-t4)`, `test(wp-t4)`, `docs(wp-t4)`), one commit per
  logical change, with a `Co-Authored-By:` footer naming your model; every committed blob LF. Never
  `git stash`; never a bare `cd`; never post to a mailbox. The footage folder
  `C:\Users\rwsmy\clearwater-footage\` is read-only: only the SERIAL leg's 16 `footage` tests touch
  it (read-only); every new test uses a fake tree. GoPro IMU and GPS are out of scope: no `gpmd`,
  IMU or GPS data is read or committed, and no location tag appears in a committed record. No
  footage-derived output is committed; outputs go under `work/`.

## Rulings

FINAL (CHARC FINAL `3c3c35d7e40b525e` (2026-10-27 06:33Z, replying to `4b2d7b2e92048eaf`)). Approved: lane by the pace tiebreak at dispatch (third); where a ruling and the
ladder differ, the ruling governs (Q3 and Q7 are AMENDED and change the ladder).

- Q1 where the commands live: ADOPTED ONLY the fill's GATE_CHECKS line (the orchestrator writes it at accept from the report's "Gate text") plus one CLAUDE.md Conventions line (CHARC writes it); NO `docs/testing.md`. AD-28's "or a short docs/testing.md" is withdrawn by this ruling.
- Q2 `tests/conftest.py`: ADOPTED one docstring paragraph only; a code change is a STOP.
- Q3 `tests/fixture_plugin.py` cold-cache race: AMENDED. The race is structurally evident (N workers, one path, no lock) and the cold worktree IS the gate's normal state, so "leave it to timing luck" is not an acceptable end state. The cell REPRODUCES it deterministically (two processes against a cold cache with the generator slowed by an injected delay, e.g. a monkeypatched `generate.generate` that sleeps 2 s before writing), then adds the stdlib exclusive-create lock with re-verify-after-acquire, bounded wait and stale-lock rule, and the two-process test that fails without the lock. If even the slowed form does not reproduce, that is a STOP with the record, not a silent skip.
- Q4 execnet: ADOPTED (lock gains exactly pytest-xdist and execnet; both licences quoted).
- Q5 exception budget: ADOPTED (more than 20 tests or a whole file = yield).
- Q6 reviewer tier: ADOPTED THE ORCHESTRATOR'S form, not the helper's. Claude lane: FAST Codex (`gpt-6-luna`/medium) for A and B (tools class per the fill). Codex lane: the fill's pinned Claude pass (`claude -p --model opus --effort high`) for A and B; there is no "Sonnet medium" variant and nobody improvises the invocation.
- Q7 run counts: AMENDED. TWO interleaved rounds (BASELINE, PARALLEL, SERIAL each), a THIRD only if the two rounds' PARALLEL+SERIAL totals differ by more than 15 %. Saves about an hour of host time; the baseline is not a figure of record.
- Q8 memory floor: ADOPTED (2 GB available at any sample fails the run; the cell never lowers N itself).
- Note: the `gui` partition (411 tests) stays serial under AD-28; whether it can run under workers is a follow-up measurement, not this package's.

## Questions for CHARC (recommended answer first)

1. **Where the two-leg command lives.** Recommended: ONLY in the fill's GATE_CHECKS suite line
   (AD-28: "The recipe lives in `docs/review-gate-clearwater.md` GATE_CHECKS"), written by the
   orchestrator at accept from the report's "Gate text" section, plus a one-line CLAUDE.md pointer
   by CHARC; the cell owns neither and creates NO `docs/testing.md`. Reason: a new `docs/*.md`
   file is "unaccounted" by `tests/harness/test_manifest_accounting.py::
   test_every_tracked_file_is_manifest_or_support` (it is not in `INSTANCE_SURFACE_RELPATHS` in
   `tests/harness/genericity_lists.py`), so `docs/testing.md` needs a harness edit that this
   package puts out of scope. Alternative: own `docs/testing.md` and one registration line in
   `tests/harness/genericity_lists.py`, then run the harness gate.
2. **`tests/conftest.py` ownership.** Recommended: owned for ONE docstring paragraph recording how
   workers derive their basetemp (xdist lines cited) and that the guard runs on the controller
   first; any code change is a STOP with a reproduction. Reason: item 4 of the commission is a
   test, and the module docstring is where the guard's load rules are documented.
3. **`tests/fixture_plugin.py` ownership.** Recommended: owned, changed only if rung 3 reproduces
   the cold-cache race, with a stdlib lock. Reason: a gate worktree has no `work/`, so the race is
   the gate's normal state, and the file is test infrastructure. Alternative: warm the cache once
   in the controller before workers start (it would generate 89 MB even for a subset run).
4. **Transitive `execnet`.** Recommended: accept (the lock gains `pytest-xdist` and `execnet`; MIT
   to be quoted from installed metadata); "nothing else added" read as no other direct dependency
   and no change to an existing package.
5. **Exception budget.** Recommended: yield to CHARC if more than 20 tests, or any whole file,
   must leave the parallel leg. Reason: beyond that the saving erodes and the partition itself may
   need rethinking.
6. **Reviewer tier and rounds.** Recommended: FAST, one round plus cleanup (WP-T2's shape). The
   guard-test additions guard against nothing irreversible themselves; the footage guard code is
   not changed.
7. **Run counts.** Recommended: keep the commission's three rounds, interleaved (about 3-4 hours of
   windows: three baselines of 27-45 min, three parallel legs, three serial legs). Alternative if
   windows are scarce: one baseline plus the AD-28 serial figures (different suite sizes, so
   weaker).
8. **Memory floor.** Recommended: 2 GB available at any 1 s sample at N=4 marks the run failed
   (the reaper kills background runs under memory pressure); the cell reports and does not lower N.

## Return report

Your FINAL message, under about 70 lines, as listed in "Notes for the cell". An undelivered report
is a failed handoff.
