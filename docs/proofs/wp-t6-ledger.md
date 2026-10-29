# WP-T6 cumulative ledger

This package implements AD-30's gate sizing under the FINAL brief at
`docs/briefs/wp-t6-brief.md`, including CHARC ruling `7458b470a82d2dc3`.
The dispatcher runs all footage, GPU and heavy commands. This cell yields at
each required boundary; it does not commit or post to a mailbox.

## Dispatcher depth and tokens

Only dispatcher-supplied figures belong here. A tokens-used footer is not
context depth (HD-1); the dispatcher's last-request input-token reading governs
the evaluation and re-seat lines. Turn 1's figures were supplied at turn 2.

| Turn / gate | Tokens-used footer | Last-request input tokens | Context window | Supplied by / disposition |
|---|---:|---:|---:|---|
| Turn 1, rung 0 / W1 script | 101,355 | 104,555 | 258,400 | Dispatcher at turn 2; turn 1 committed as `c06c808`; dispatch pace Codex 0.54 is not a depth figure |
| Turn 2, W1 corrections | 120,962 | 123,658 | 258,400 | Dispatcher at turn 3; committed as `d88365d` |
| Turn 3, semantic creation_time amendment | 129,889 | 131,810 | 258,400 | Dispatcher at turn 4; committed as `78e0094` |
| Turn 4, round-0 table | 152,628 | 152,018 | 258,400 | Dispatcher generation 20 at turn 5; committed as `65b9f4f`; CHARC authorizes rung 2 in this cell |
| Turn 5, rung-2 build | 358,551 | 202,787 | 258,400 (footer reported 475,000, unexplained; CHARC: the window of record stands) | Dispatcher generation 20; committed as `0afec17`; above 200K, so CHARC ruled RE-SEAT NOW (`6f5ebd09c017753c`, option 1): seat 1 (session `01a18757-14d0-7840-9bf3-bd6590722181`) retired |
| Seat 2 turn 1 (ledger turn 6), marker registration | 68,477 | 73,738 | 258,400 | Dispatcher generation 20 at seat 2 turn 2; committed as `5f204e3` |
| Seat 2 turn 2 (ledger turn 7), W2 controls ruling | 164,768 | 101,282 | 258,400 | Dispatcher generation 20 at seat 2 turn 3; committed as `13a5fe6` |
| Seat 2 turn 3 (ledger turn 8), cuts / import-scope STOP | 215,059 | 122,744 | 258,400 | Dispatcher generation 20 at seat 2 turn 4; turn-8 changes remained uncommitted for this turn's per-file handoff |
| Seat 2 turn 4 (ledger turn 9), import grant / W3 script | 247,499 | 152,719 | 258,400 | Dispatcher generation 20 at seat 2 turn 5; R1 `1f86873`, R2-R3 `a2420fc`, R4 `5520ee4`, R5-R7 `7970d0b`, ledger `89f9500` |
| Seat 2 turn 5 (ledger turn 10), W3 results / rung 4 request | 279,339 | 183,073 | 258,400 | Dispatcher generation 20 at seat 2 turn 6; committed as `b540844` |
| Seat 2 turn 6 (ledger turn 11), collections / W4 results / report | 454,498 | 98,187 | 258,400 | Dispatcher generation 20 at seat 2 turn 7; report `7664b82`, ledger `04b01d2`; tokens-used footer is not input depth |
| Seat 2 turn 7 (ledger turn 12), Reviewer A R1 cleanup / W2b request | 517,709 | 157,267 | 258,400 | Dispatcher generation 20 at turn-12 footer, supplied by generation 21 at seat 2 turn 8; conftest `18e2d53`, report `6892bbd`, ledger `f10d13b` |
| Seat 2 turn 8 (ledger turn 13), W2b results / R1 convergence | Pending dispatcher | Pending dispatcher | 258,400 | Docs only; dispatcher generation 21, CHARC generation 7; depth pending dispatcher |

## RESUME HERE (seat 2; written by the dispatcher, generation 20, 2026-10-29 ~12:12Z)

Seat 1 retired at turn 5's commit (`0afec17`). Seat 2 is a fresh Codex session; it starts from this section, the brief (its Rulings GOVERN) and the verbatim rulings below in this ledger.

- **Rulings in force (all verbatim in this ledger):** brief Rulings `7458b470a82d2dc3`; W1 STOP 1 `5b9dd6b0dfacc46e` (R-a pairing, R-b `-movflags use_metadata_tags`, R-c scoped allow-list, R-d); W1 STOP 2 `42a1be58329e3559` (R-e semantic `creation_time`, R-b kept, the ADDED rung-3 V4 best-effort-delta check with its STOP and fallback); round-0 `22065ec5da3b4dbe` (CHARC's post id `6d87249c`: PROCEED, all seven CUT, R4 to six, row 10 banked); re-seat `6f5ebd09c017753c`.
- **The trim of record:** N = 90, T = 3.003 s, keyframes every 30 frames; the fixed stream-copy flags of the brief's "The trim fixture" step 3 plus R-b's `-movflags use_metadata_tags` and nothing else; checks 4(a)-(e) PASS (W1 run 3); the allowed differences are the R-c muxer-written keys by scope plus R-e's format `creation_time` (2 parts, every part equal); audio `timecode` does not survive (a Limit).
- **The seven CUT rows and their sizes:** R1 `test_jobs_export_video.py::test_gx011627_through_the_engine_keeps_every_mandatory_and_required_item` -> `gx011627` (`[trim]` / `[full]`); R2 `test_io_video_encode.py::test_gx011627_nvenc_levels_give_distinct_sizes` and R3 `...::test_gx011627_through_the_sink_keeps_every_mandatory_and_required_item` -> one fixture `gx011627_standard_encode` on `gx011627` (`[trim]` / `[full]`; R3's frame count is the ONE operand change, Q3); R4 `test_color_roundtrip.py::test_pair_round_trip_on_the_owners_main_case` -> `frames` parametrised `[first6]` (gate) / `[first30]` (`fullclip`); R5-R7 `test_io_video_decode_hw.py` real-clip tests (`:119`, `:129`, `:142`) -> `gx011627` with `footage_frames`, `FOOTAGE_FRAMES` deleted. Each change exactly as the brief's map row says.
- **The shared checker:** `tests/conftest.py`: `pair_streams` (R-a, copied verbatim from `w1.sh`) and `gx011627_trim_checks(source, trim, count)` (4(a)-(e), R-c, R-e; returns a sanitized record); the locator `_gx011627_source()`, the plan `_gx011627_trim_plan(...)`; fixtures `gx011627_trim` (session) and `gx011627` (session, `trim` / `full` with `marks=pytest.mark.fullclip`). The parity test `tests/test_io_video_decode_hw.py::test_the_gx011627_trim_is_a_stream_copy_of_the_source` reaches the checker by a function-local `from conftest import ...`.
- **W2 run 1 (12:08:17-12:09:05Z, 10.46 GB available): `W2 STOP stage=2`.** Stage 1 parity test 1 passed in 3.57 s. Stage 2 `tests/test_conftest_guard.py` 58 passed, 2 failed (`test_pytests_own_child_decides_when_the_root_cannot_be_listed`, `test_a_check_that_cannot_be_made_refuses`), both `'fullclip' not found in markers configuration option`. Cause: both load the REAL conftest in-process (`_load_guard()`, `test_conftest_guard.py:525-533`), so the module-level `pytest.mark.fullclip` is evaluated against the outer session's `--strict-markers` config, where rung 4's marker is not yet registered. Stage 3 (controls) did not run. Cleanup EXIT 0: scratch removed, no trim left in either basetemp.
- **Remedy (dispatcher's, reported to CHARC):** bring rung 4's ONE `pyproject.toml` marker line forward, verbatim, now; then W2 runs again in full. Rung 4 keeps its collection identities and W4.
- **Next:** seat 2 turn 1 = the marker line + a W2 RUN REQUEST (`w2.sh` unchanged unless the marker line demands otherwise; md5 `1f4025ca3fa944daf62908e658f6423f`). Turn 2 = W2's results and the two controls into this ledger, then rung 3 (with the V4 best-effort-delta check) and the W3 RUN REQUEST. Then rung 4, the report, Reviewer A, Reviewer B, the ONE gate.
- **Reviewer A lens (CHARC, not a STOP):** the function-local `from conftest import ...` resolves to pytest's own conftest module under the default prepend import mode (`tests/` has no `__init__.py`); under importlib mode it would make a second module. If Reviewer A objects, the remedy is a tiny importable helper module under `tests/` (additive), not a conftest change.

## Seat 2 turn 1 -- marker registration

| Change | Reason / disposition |
|---|---|
| Register `fullclip` in `pyproject.toml` | Rung 4's exact marker line is moved forward under the seat-2 dispatch: the two W2 guard tests load the real conftest in-process, so its fixture parameter mark must already be registered under the outer session's `--strict-markers`. Rung 4's collection identities and W4 remain required. |

Starting HEAD is `7b84890`; the worktree was clean before this turn. The marker
line is the only `pyproject.toml` change. `work/wp-t6/w2.sh` is unchanged, with
MD5 `1f4025ca3fa944daf62908e658f6423f` verified this turn. No footage or GPU
command ran in the cell. W2 is requested again in full at the dispatcher's
seat, with outputs under `work/wp-t6/w2/`; run 1's evidence remains under
`work/wp-t6/w2-run1/`.

| Light verification | Result / evidence |
|---|---|
| `PYTHONPATH=scripts uv run pytest tests/test_conftest_guard.py --basetemp=work/wp-t6/tmp -p sandbox_mkdir_shim -p no:cacheprovider` | Ran: 43 passed, 17 failed in 40.37 s; EXIT 1. `work/wp-t6/seat2-turn1-guard.log`. Failures include child-pytest `PermissionError [WinError 5]` diagnostics despite the outer shim; no unregistered-`fullclip` diagnostic remains. The two W2 run-1 failing node names are absent from this run's failure list. This is not a green guard-suite result; seat-side W2 must supply it. |
| `git diff --check` | PASS, EXIT 0; `work/wp-t6/seat2-turn1-diff-check.log`. Git's line-ending conversion warnings do not change the on-disk LF check recorded in the scope proof. |
| Exact marker / owned scope / LF | PASS; `work/wp-t6/seat2-turn1-scope-proof.json`: `pyproject.toml` differs by exactly the required one-line insertion; only it and this ledger changed, both LF. |

Verification loop: the known marker failure motivated the dispatched one-line
fix. The fresh guard run contains no marker-registration error but cannot
validate the entire guard suite under the sandbox's child-process permissions.
No guard test or sandbox shim was changed. W2's parity test and two controls
remain pending the seat-side run. No new STOP or question is raised; the
existing W2 request provides the required unsandboxed validation.

## W2 run 2 -- STOP stage 3

The dispatcher ran W2 from 2026-10-29 12:14:25Z through 12:15:41Z, with
10.37 GB available, using unchanged `w2.sh` MD5
`1f4025ca3fa944daf62908e658f6423f`. Evidence is preserved under
`work/wp-t6/w2-run2/`. Stage 1: parity test 1 passed in 3.63 s. Stage 2:
guard suite 60 passed in 41.20 s; the marker registration fixed stage 2.
Stage 3 stopped: the re-encode control returned `command_completed: false`,
`error_type: AssertionError`, so it did not prove a named checker rejection.
The N+1 control returned PASS for every check 4(a)-(e), with 91 requested
frames and the expected count still 90. Cleanup EXIT 0: scratch removed,
no trim left in either basetemp. `04-cleanup.json` records stage EXIT 1.

`-frames:v N+1` alone is masked by `-t T` (the belt working, not a defect).

The checker called `pair_streams` unconditionally; that helper asserts equal
pairing-group counts. A changed video codec identifier is the suspected
re-encode trigger, not yet a real-stream observation: run 2 saved no pairing
keys before the assertion. Run 3 records the differing (`codec_type`,
`codec_tag_string`) keys and counts, never container tag values, to confirm
the cause at the dispatcher's seat without a cell-side footage probe.

## CHARC W2 controls ruling (verbatim)

Message `ce2069c54c57a1a1`, 2026-10-29 12:17:34Z, supplied by orchestrator
generation 20 at seat 2 turn 2:

**CHARC RULING on WP-T6 W2 run 2 (query 3bd1625d4d9deed2): Q-A option 1, Q-B option 1, each as recommended, with one clause made explicit.**

**Q-A (re-encode control): option 1.** `gx011627_trim_checks` never raises on a pairing-count mismatch; it records it as a named 4(d) FAIL (stream parity) and still computes and returns 4(b) and the rest. The fixture keeps asserting every check PASS, so R-a's equal-count guarantee holds through 4(d). The control passes iff 4(b) FAILs, with 4(d) recorded beside it. Seat 2 confirms the cause by the video codec-tag KEY only (the tag string, never a value from the clip).

**Q-B (off-by-one control): option 1, the realistic plant in the cut PLAN**: `-frames:v N+1` AND `-t` = the (N+1)th packet's pts (T + 1001/30000 s), both flags one frame late. EXPLICIT: 4(b)'s FIRST clause is 'the trim's video packet count equals N' (then the per-packet equality of the first N); so 91 packets FAIL 4(b) and 4(c) both. The control passes iff 4(b) or 4(c) FAILs, recorded which. `-frames:v N+1` alone being masked by `-t T` is the belt working, and the ledger says so in one line; it is not a defect.

Sequencing as you have it: seat 2 turn 2 = the checker change + a W2 run 3 request; rung 3 only after W2 is green. Nothing heavy at my seat during W2 run 3.

## Seat 2 turn 2 -- checker and control changes

Only rung-2-added lines in `tests/conftest.py` change. Before calling the
unchanged `pair_streams`, the checker compares pairing-group counts. A mismatch
returns 4(d) FAIL, reason `pairing counts differ`, and differing stream kinds,
codec identifiers and counts. It deliberately marks 4(e) and data equality
FAIL when pairing cannot be established, rather than comparing partial pairs.
Format-tag checks still run. Packet checks remain independent; a missing trim
video stream returns 4(c) FAIL. No broad exception handler was added.

4(b) is the conjunction of two named returned verdicts: `4b_count` asserts the
trim's video packet count equals N; `4b_packets` asserts N source packets exist
and the first N packet facts match in order. The fixture's five named asserts
and data-packet equality assert remain unchanged, so no bad trim reaches a
consumer. The source count, packet equality, stream/tag predicates and
scoped exceptions are retained.

Only stage 3 of gitignored `w2.sh` changes: the re-encode records 4(d), pairing
differences and the split 4(b) verdicts, and requires 4(b) FAIL. The extra-frame
plant moves both `-frames:v` and `-t` one frame late. It computes the latter as
T + 1001/30000 with Decimal and formats it to the source plan's fractional
precision (six places for the trim of record); it still requires 4(b) or 4(c)
FAIL and records every failed check. New script MD5:
`e97c51289cb85137cf5553619970cf31`. Rung 3 remains unbuilt.

| Validation | Result / evidence |
|---|---|
| Synthetic mismatched codec groups, before change | Reproduced `AssertionError: stream pairing counts differ`, EXIT 1; `work/wp-t6/seat2-turn2-synthetic-before.log` |
| Synthetic checker, after change | PASS, EXIT 0; `seat2-turn2-synthetic-after.log`: valid copy passes; differing codec groups and unequal counts within one group return 4(d), 4(e), data FAIL without exceptions; missing video returns 4(c) FAIL; extra/missing packet counts fail `4b_count`; first-N equality remains independently visible; changed packet facts fail `4b_packets` |
| `uv run ruff check tests/conftest.py` | PASS, EXIT 0; `work/wp-t6/seat2-turn2-ruff.log` |
| `uv run mypy` | PASS, EXIT 0; 141 source files; `work/wp-t6/seat2-turn2-mypy.log` |
| `py_compile` | PASS, EXIT 0; conftest and all three embedded W2 Python programs; `work/wp-t6/seat2-turn2-static-proof.log` |
| Additive conftest / consumer asserts / late-cut flags / LF / scope | PASS; `work/wp-t6/seat2-turn2-static-proof.json`: every pre-rung-2 line preserved, fixture AST unchanged, actual plant AST produces 91 and 3.036367 from N=90 and T=3.003000, only two owned tracked paths changed, all edited blobs LF |
| `git diff --check` | PASS, EXIT 0; `work/wp-t6/seat2-turn2-diff-check.log` |
| Real re-encode codec identifiers / control verdicts | Pending W2 run 3 at the dispatcher; synthetic identifiers do not establish the real clip's identifiers |
| Bash syntax / full format check | Deferred to the dispatcher's seat per the sandbox limits; neither claimed here |

Verification loop: reproduced the early pairing assertion with synthetic
documents, applied Q-A's guarded pairing and Q-B's split count predicate,
then confirmed the valid path and independent failure paths above. Both
source-probe and packet readers were replaced by synthetic data for this
light check; no footage was located or probed. Full W2 run 3 remains the
required real control proof; the dispatcher moves `w2/` aside before running.

## W2 run 3 -- DONE

The dispatcher reports an exclusive run starting 2026-10-29 12:23:16Z,
10.02 GB available, script MD5 `e97c51289cb85137cf5553619970cf31`.
`work/wp-t6/w2/00-window.json` records 12:23:17.480106Z and
10,016,727,040 available bytes. The saved logs confirm parity 1 passed in
3.57 s and guards 60 passed in 41.55 s, both EXIT 0. The dispatcher reports
`W2 DONE`, EXIT 0; cleanup records end 12:24:30.353107Z, all steps complete,
stage EXIT 0, scratch removed and no trim left in either basetemp.

The two control JSON files confirm:

| Control | Named checks / result |
|---|---|
| Re-encode | Caught; command completed; 4(b), 4(d), 4(e) FAIL; `4b_count` PASS, `4b_packets` FAIL. Pairing differs only for video codec identifiers: source `hvc1` count 1 vs trim 0; source `hev1` count 0 vs trim 1. This confirms the real-stream pairing-assertion cause suspected after run 2. |
| Both flags one frame late | Caught; 91 requested vs 90 expected; 4(b), 4(c) FAIL; `4b_count` FAIL, `4b_packets` PASS; 4(d), 4(e) PASS. |

`-frames:v N+1` alone is masked by `-t T` (the belt working, not a defect).

Rung 2 is CLOSED: the parity and guard tests pass at the seat, both real
controls fail by their required checks, and teardown leaves no trim. Evidence
is `work/wp-t6/w2/`; earlier runs remain in `w2-run1/` and `w2-run2/`.

## Seat 2 turn 3 -- mapped cuts and import-scope STOP

The four owned test files now contain the mapped R1-R7 edits: engine, shared
sink/levels fixture and three decoder paths use `gx011627`; sink and decode
counts read the independently asserted count; the colour round trip has
`first6` / `first30`, the latter marked `fullclip`. Only the mapped jobs
locator and its now-unused imports were removed, after checking their uses.
The encode locator and its own skip-rule test remain. Module-scoped decode
fixtures now consume the session-parametrised source, so they are rebuilt
once per source parameter as intended. R4's bounds and plants are unchanged;
the report still owes the side-by-side base figures and deterministic-filter
sentence from CHARC's round-0 ruling.

**STOP: minor, confirmed, NEW, edit outside the named blocks needed.**
`uv run ruff check tests/test_jobs_export_video.py tests/test_io_video_encode.py
tests/test_color_roundtrip.py tests/test_io_video_decode_hw.py` reports exactly
one F401, EXIT 1: `local_config.load_local_config` imported but unused at
`tests/test_io_video_encode.py:48:65` (`work/wp-t6/seat2-turn3-ruff.log`).
The grep reproduction in `seat2-turn3-locator-uses.txt` shows its only remaining
occurrence is that import; `FootageLookupError` and `find_footage_file` still
serve the retained encode locator and test. The mapped source substitutions
eliminate all encode-file calls of `load_local_config`.

The brief permits encode-file edits ONLY in the shared fixture and two tests;
the turn instruction permits deleting unused imports only in the jobs file.
The cell leaves the encode import unchanged and requests the one-name import
removal as a scope exception. Recommended ruling: allow removal of only
`load_local_config` from the encode import, keeping the other two names.
W3 script, collection, mypy and heavy runs are deferred at this STOP; no
W3 or gate result is claimed. The mapped edits are available for per-file
commits; the next turn can perform that cleanup and prepare W3 after a ruling.

## Seat 2 turn 4 -- dispatcher import grant and W3 plan

**Dispatcher grant (generation 20, seat 2 turn 4):** remove ONLY
`load_local_config` from `tests/test_io_video_encode.py`'s local-config import;
leave the other names and `_footage_clip` unchanged. Ground supplied by the
dispatcher: the same rule the brief gives the jobs file ("IF nothing else in
the module uses them after the edit (ruff F401 decides; grep first)"). It is
a direct consequence of the mapped cuts, not a new change. The dispatcher
reports it to CHARC. The grant is applied; the prior STOP is resolved.

All seven mapped cuts are built across the four owned test files. No test is
deleted. A static AST comparison against HEAD confirms every assertion is
unchanged after mapping only the ruled frame-count operands (`681` to `frames`,
`FOOTAGE_FRAMES` to the selected count); every function/class outside the named
blocks is unchanged, except the authorized jobs locator removal and new decode
count fixture. The selected full forms still reach 681 or 30 as specified.
The new R4 comment explicitly describes the retained half of each positive
30-frame margin. The report's side-by-side base figures and bit-exact-filter
sentence remain required; no full report or final gate claim is made here.

### W3 script (requested, not run)

`work/wp-t6/w3.sh` MD5 `5c98800cf7e6ba18d9b7dd3400e6dab0` is gitignored.
It runs from Git Bash at the worktree root, unsets `PYTEST_ADDOPTS`, sets
headless Qt, records start/free memory and requires >= 5 GiB before each pytest
session. The dispatcher commits all five tracked paths before running: the
script requires clean tests and an empty working and staged diff at entry.

1. One fresh Python process calls `pytest.main` on exactly the seven changed
   gate IDs (`trim` or `first6`) plus the parity test, with the amended SERIAL
   expression, no `-n`, `--durations=0` and
   `--junitxml=work/wp-t6/w3/w3-serial.xml`. A temporary plugin wraps the real
   `vf.encode_file` and `vf.fidelity_record`. The main session requires eight
   passes with no skips/errors, exactly ONE successful standard encode call
   from `gx011627_standard_encode`, and one engine V4 record with all
   MANDATORY/REQUIRED items and the roster SAME. The standard encode's count,
   NVENC tied boolean and sample count are recorded as observations.
2. The plugin captures the engine run's actual fidelity record synchronously
   before the unchanged test deletes its output. Only difference-item NAMES,
   the node ID and SAME booleans are saved in `02-engine-v4-names.json`; the
   raw record never goes to disk. A separate step reads the specified full
   reference at `C:/Users/rwsmy/clearwater/work/wp4.2/v4/gx/record.json` at the
   dispatcher's seat and projects its three difference lists only. The
   comparator saves `same`, `only_trim`, `only_full` by class in
   `03-v4-delta.json`, checks the full reference has eight best-effort items
   and no MANDATORY/REQUIRED differences, and STOPs on any new trim
   MANDATORY/REQUIRED item. Identical best-effort sets proceed; a delta limited
   to `creation time: container tag` or `container tags other than creation_time`
   carries the R-e/R-b/R-c representation reasons as a Limit; other names STOP
   for explanation. This step is attempted even when the main tests failed,
   so an available named engine failure can still produce branch-ii evidence.
3. A separate fresh session runs only the trim levels test. During setup of
   `gx011627_standard_encode`, the plugin changes its real encode's requested
   quality from standard to draft, so that fixture yields a draft encode as
   standard. The original fixture teardown still deletes that output. A
   successful control requires exactly one call-phase failure on the named
   levels node, `AssertionError`, at
   `level is not None and level.name == expected[quality]`, and one recorded
   plant. An encoder/setup error cannot count as rejection.
4. Another fresh session runs only R5. A fixture-setup hook shortens the real
   reference by one and updates pytest's cached result, then requires exactly
   one call-phase `AssertionError` on R5 at
   `len(footage_reference) == footage_frames`, with one plant. Both controls
   record pytest's real EXIT 1 separately from the control verifier's EXIT 0.
   No tracked test file is edited or planted.
5. All three fresh basetemps and the temporary runner lie inside the owned
   `work/wp-t6/w3-scratch/`. An EXIT/INT/TERM trap removes that entire scratch
   tree after checking its resolved target. Entry refuses pre-existing scratch.
   Cleanup verifies the four tests' bytes against their pre-run code hashes,
   `git status --porcelain -- tests` empty, and `git diff --quiet` successful;
   any failure is W3 STOP. It lists retained evidence filenames and remaining
   scratch filenames. Only count/name/verdict JSON, pytest logs and junit XML
   stay under `work/wp-t6/w3/`. The final line is `W3 DONE` or `W3 STOP stage=<n>`.

All runner outputs go to files with EXIT lines. This is a plan plus light
validation, not a W3 result. Expected seat window: about 10 minutes, one heavy
job at a time. Exact command: `bash work/wp-t6/w3.sh`.

### Seat-2 turn-4 light checks

| Check | Result / evidence |
|---|---|
| Ruff on the four changed test files | PASS, EXIT 0; `work/wp-t6/seat2-turn4-ruff.log` |
| `uv run mypy` | PASS, EXIT 0; 141 source files; `seat2-turn4-mypy.log` |
| Four-file `--collect-only -q` | Ran with `PYTHONPATH=scripts`, the sandbox shim, `-p no:cacheprovider`, and `--basetemp=work/wp-t6/turn4-collect`: 217 tests collected in 0.79 s, EXIT 0; `seat2-turn4-collection.log` |
| Assertion retention / owned blocks / syntax / LF | PASS, EXIT 0; `seat2-turn4-static-proof.json`: unchanged assertions after ruled operand mapping, no test deleted, untouched blocks equal, four test modules and four embedded W3 programs compile, 217 unique IDs including seven full and seven gate forms; edited blobs LF |
| Embedded runner undefined-name checks | PASS, EXIT 0; `ruff check --select F821,F811` on the four extracted programs; `seat2-turn4-w3-lint.log` |
| W3 plugin synthetic main | PASS, EXIT 0; `seat2-turn4-plugin-main.log`: two real miniature pytest tests share one synthetic standard fixture encode; the same-call engine projection is captured. Sandbox shim loaded; no footage/GPU used |
| W3 plugin synthetic controls | PASS, EXIT 0 for each harness check; `seat2-turn4-plugin-draft.log`, `seat2-turn4-plugin-reference.log`: each inner miniature pytest session fails at its expected assertion, proving draft substitution and cached-reference truncation reach the tests. These are synthetic checks, not W3's real controls |
| V4 delta synthetic branches | PASS, EXIT 0; `seat2-turn4-delta-check.log`: same/ruled representation delta proceeds, new MANDATORY and unexplained best-effort names STOP, unrelated synthetic metadata is absent from saved projection |
| `git diff --check` | PASS, EXIT 0; `seat2-turn4-diff-check.log` |
| Seat-side Bash syntax / full format check / W3 | Pending dispatcher; no claim made for them |

Verification loop: the granted import removal clears the reproduced F401.
Fresh ruff and collection pass; the AST check confirms the map's assertion
retention and scope. The synthetic plugin checks independently exercise the
runtime controls without touching tracked tests. The scope-proof log reader
was corrected for PowerShell's UTF-16 log encoding, then passed. The W3
measurement and CHARC's branch decision remain pending the real seat run.

## W3 run 1 -- reference-path STOP and dispatcher edits

Run 1 evidence is preserved in `work/wp-t6/w3-run1/`. Window start was
2026-10-29 12:42:26.485311Z, with 10,686,595,072 available bytes; cleanup
ended 12:48:00.365103Z. Stage 1 passed all eight cases in 322.26 s, EXIT 0,
and the observer verified the combined run. Stage 2 stopped with
`KeyError: 'summary'`; controls did not run. Cleanup records stage EXIT 1,
scratch removed, clean tests/diff and unchanged test bytes.

The dispatcher identified its reference-path slip: the originally supplied
`work/wp4.2/v4/gx/record.json` is a headless runner record without fidelity
data. It corrected W3's baseline to
`C:/Users/rwsmy/clearwater/work/wp3.10/wp4.2-v4/v4-GX011627-c3-gpu/GX011627_corrected.compare.json`,
as named by `work/wp4.2/v4/logs/cmp-v4-GX011627-c3-gpu.log`. The cell did not
read that outside-worktree compare record. The second dispatcher edit widened
the explanation table to EXACTLY the six item names ruled below; any other
best-effort delta still stops. No tracked test or product code changed.

The ruling quotes interim script MD5 prefix `cd2e47e2`; the final dispatched
script is MD5 `0dd11553112ae203b95a0952c9485f96`, verified this turn and used
for run 2. This supersedes the cell's original `5c98800c...` W3 script for the
measurement evidence, without changing any mapped test assertion.

## CHARC W3 stage-2 ruling (verbatim)

Message `c80aacc9844cd837`, 2026-10-29 12:50:19Z, supplied by orchestrator
generation 20 at seat 2 turn 5:

**CHARC RULING on WP-T6 W3 stage 2 (query 89d8d15e712cf983): BRANCH (i), PROCEED, option 1 as recommended.** MANDATORY and REQUIRED are empty on both sides, so the STOP condition is not met. The six-name best-effort delta is recorded as a Limit with its two reasons:

- **Three trim-only items** (`creation time: container tag`, `creation time: mvhd`, `creation time: per-stream tags`) are the R-e two-part `creation_time` the export writes back as one value: the trim's own container representation, already accepted at STOP 2.
- **Three full-only items** (`edit lists as written, non-video tracks`, `timecode value (stream tags)`, `track layout`) are FEWER differences on the trim because its container is FFmpeg-muxed and carries no audio `timecode` (R-c's Limit). The `[trim]` form therefore does not exercise those three best-effort items against a camera-written container; the `fullclip` form does, in W4 now and in package windows after. None of them is a gate assertion (R1 asserts MANDATORY and REQUIRED only).

The script's explanation table widens to EXACTLY these six names; any other name stays a STOP. The report's Limits carry the six names with the two reasons, and the accept record repeats the sentence "the trim form proves V4 MANDATORY and REQUIRED; three best-effort container items are proved by the fullclip form only". Re-run W3 in full (stage 1, the delta, both controls).

Your reference-path slip (the runner record for the compare record) is acknowledged; the corrected `w3.sh` (md5 cd2e47e2) is the one that runs. Stage 1's 322 s for the eight rows against 1,567 s baseline is noted as evidence; the gate's per-test sum stays the verdict (Q6).

## W3 run 2 -- DONE; rung 3 CLOSED

Evidence is `work/wp-t6/w3/`. The dispatcher reports W3 DONE, EXIT 0, in its
rounded 12:51-12:57Z window. Saved window/cleanup records bound the run more
precisely at 2026-10-29 12:50:55.706810Z to 12:56:23.544816Z (327.84 s), with
11,001,569,280 bytes available before the window; each subprocess also records
its own memory reading. The main session started with 10,989,305,856 bytes.

| Step | Confirmed result |
|---|---|
| Sized SERIAL cases | 8 passed, 1 warning in 258.91 s; pytest EXIT 0; observer verified. Exactly one standard encode from `gx011627_standard_encode`, 90 frames, NVENC tied true with 169 samples. Exactly one engine fidelity record, MANDATORY/REQUIRED all SAME, roster SAME. |
| V4 delta | `branch=i-proceed`, no unexplained items, no MANDATORY/REQUIRED differences on either side. Each side has eight best-effort differences, five shared plus the three-only lists below. |
| Draft-as-standard control | Caught, verified; pytest EXIT 1, one call-phase `AssertionError` on the trim levels node at `level is not None and level.name == expected[quality]`; verifier EXIT 0. The real fixture encoded draft and wrote 90 frames. |
| Truncated reference control | Caught, verified; pytest EXIT 1, one call-phase `AssertionError` on R5 at `len(footage_reference) == footage_frames`; one plant shortened 90 to 89; verifier EXIT 0. |
| Cleanup | EXIT 0; steps complete, scratch removed, no remaining scratch files, tests status empty, `git diff --quiet` true and test bytes unchanged. No planted code was committed. |

The six exact observed best-effort item names, retained as Limits for the
report and accept record, are:

| Direction | Item names | Ruled reason |
|---|---|---|
| Trim only | `creation time: container tag`; `creation time: mvhd (seconds since 1904)`; `creation time: per-stream tags` | R-e's two-part trim `creation_time` is written back as one value. |
| Full only | `edit lists as written, non-video tracks (media_time in media seconds)`; `timecode value (stream tags)`; `track layout (key:sample entry:tkhd flags)` | The trim is FFmpeg-muxed and lacks audio `timecode` (R-c); these camera-container items require the preserved full form. |

The trim form proves V4 MANDATORY and REQUIRED; three best-effort container
items are proved by the fullclip form only. CHARC branch (i) is taken on the
measured empty MANDATORY/REQUIRED lists and the explained six-name delta.
Branch (ii)'s fallback is not needed. The R3 frame-count operand remains Q3's
KEPT property, not a loss. Rung 3 is CLOSED. W3 is development evidence; its
258.91 s is not the final gate's per-CUT sum or Q6's verdict.

## Seat 2 turn 5 -- rung 4 collection and W4 requests

The marker was registered earlier in `5f204e3`; no additional marker or
`pyproject.toml` edit is made. Installed pytest is 8.4.2, confirmed by the
light script-compile command; the seat-side collection checker also records
its own imported version to prove the fixture parameter marks on that version.

Full-repository collection is requested at the dispatcher's seat, using the
established fallback for rung 0's non-returning sandbox collection. That
earlier hang remains unexplained; no new full-repo sandbox attempt or GPU
probe is made. The successful four-file collection from turn 4 is not treated
as the all-repo collection proof.

`work/wp-t6/cand-collect.sh`, MD5 `07744aa8ee2eebafacfd15ae78c6f751`,
collects all / amended parallel / amended serial / fullclip separately with
fresh basetemps under `work/wp-t6/`, `PYTEST_ADDOPTS` unset and headless Qt.
It saves runner logs with EXIT lines, writes node-ID-only `cand-*.txt`, checks
each count against pytest's own summary, then requires all of:

- No duplicates; the three partitions pairwise disjoint and
  parallel + serial + fullclip = all.
- Fullclip equals exactly six `[full]` IDs and R4's `[first30]` ID.
- ALL removes exactly seven unsuffixed CUT IDs and adds their fourteen
  suffixed forms plus the parity test.
- SERIAL removes the same seven and adds the seven gate forms plus parity;
  PARALLEL is unchanged against `base-*`.

Expected counts remain ALL 6,457, PARALLEL 5,313, SERIAL 1,137, FULLCLIP 7;
these are predictions, not observed rung-4 results. The actual collection
identity and version will be in `cand-collection-summary.json`. The checker
passed a synthetic generated-map exercise and rejected duplicate and missing
gate-ID controls; that validates the checker only, not the candidate collection.

`work/wp-t6/w4.sh`, MD5 `16847bf19ddb53f9cc88f018fc9b8ad5`, must run
AFTER the collection proof passes. It records window start/free memory,
requires >= 5 GiB and a clean committed candidate, then runs the brief's
FULLCLIP command once with the additional temporary observer plugin:

```text
PYTHONPATH=work/wp-t6/w4-scratch uv run pytest -q -rs -m "fullclip" --basetemp=work/wp-t6/w4-fullclip --durations=0 --junitxml=work/wp-t6/w4/w4-fullclip.xml -p wp_t6_w4_observer
```

The observer never changes tests or fixtures. A passing call report on the
full sink node reads its already-resolved source count and encode report,
checks the actual test still asserts `run.report.frames_written == frames`,
and records both operands equal to 681. Final verification requires exactly
the seven collected full IDs passing, no skips/failures, this one 681-frame
observation and zero `gx011627_trim` setups. A false observation forces the
session EXIT nonzero. Only counts, node IDs and verdicts are retained; no
footage path, metadata value, frame or packet digest is saved by the observer.

Both `w4-fullclip/` (all pytest outputs/caches) and `w4-scratch/` (the temporary
plugin) are newly created and owned by the script. Pre-existing targets are
refused and preserved. The EXIT/INT/TERM trap checks resolved absolute targets
stay under this worktree's `work/wp-t6/`, removes only those two owned trees,
checks clean tests/diff and lists retained JSON/log/XML filenames under `w4/`.
The last line is `W4 DONE` or `W4 STOP stage=<n>`. Expected W4 window is about
27 minutes; these figures are information, never a V16 row.

| Light validation | Result / evidence |
|---|---|
| Five embedded Python programs compile / scripts LF / pytest version | PASS, EXIT 0; `work/wp-t6/seat2-turn5-script-compile.log`; pytest 8.4.2 |
| Embedded F821/F811 checks | PASS, EXIT 0; `seat2-turn5-script-lint.log` |
| Synthetic collection identities | PASS, EXIT 0; `seat2-turn5-identity-check.log`; generated map accepted, duplicate and missing-gate plants rejected; no real collection claimed |
| Synthetic W4 observer at 681 | PASS, EXIT 0; seven miniature tests pass and observer verifies; `seat2-turn5-observer-681.log`; sandbox shim loaded, no footage/GPU used |
| Synthetic W4 observer at 680 | PASS for the harness check, EXIT 0; all seven miniature tests pass their equal-count assertions, but observer deliberately forces pytest EXIT 1 for non-681 operands; `seat2-turn5-observer-680.log` |
| `git diff --check` / owned scope / LF | PASS, EXIT 0; `seat2-turn5-diff-check.log`, `seat2-turn5-scope-proof.json`; only the ledger is tracked as changed |
| Seat collections / Bash syntax / W4 | Pending dispatcher; no success claim made |

Verification loop: W3's saved main/delta/control/cleanup JSON and concise log
summaries confirm rung 3. The new scripts compile and pass targeted synthetic
checks, including a passing sink assertion at 680 that the W4 observer rejects.
Rung 4 remains open until the real collection identities and W4 are returned.

## Candidate collections -- DONE

The dispatcher ran `bash work/wp-t6/cand-collect.sh`, MD5
`07744aa8ee2eebafacfd15ae78c6f751`. It ended `CAND COLLECTION DONE`,
EXIT 0. `work/wp-t6/cand-collection-summary.json` records pytest 8.4.2 and
completion at 2026-10-29 13:06:30.821536Z. The four node-ID-only files are
`cand-all.txt`, `cand-parallel.txt`, `cand-serial.txt`, `cand-fullclip.txt`.

| Set | Observed count | Collection EXIT |
|---|---:|---:|
| All | 6,457 | 0 |
| Amended parallel | 5,313 | 0 |
| Amended serial | 1,137 | 0 |
| Fullclip | 7 | 0 |

The summary confirms no duplicates, pairwise-disjoint parallel/serial/fullclip
sets, and **parallel + serial + fullclip = all**. Fullclip is exactly the six
`[full]` forms (R1-R3, R5-R7) and R4's `[first30]`. Against the base:

- ALL removes exactly the seven unsuffixed CUT IDs and adds their fourteen
  suffixed forms plus the rung-2 parity test.
- SERIAL removes exactly those same seven and adds the seven gate forms
  (`[trim]` / `[first6]`) plus parity.
- PARALLEL is unchanged.

This is the actual pytest 8.4.2 collection proof of fixture-parameter marks;
the earlier synthetic identity checks and predicted counts are superseded by
the seat evidence. Decode's module-scoped fixtures rebuild per session source
parameter as intended. No additional marker change was needed.

## W4 -- DONE; rung 4 CLOSED

The dispatcher ran `bash work/wp-t6/w4.sh`, MD5
`16847bf19ddb53f9cc88f018fc9b8ad5`, after collection passed. The window
record `work/wp-t6/w4/00-window.json` starts at
2026-10-29 13:06:46.706213Z with 11,047,211,008 available bytes, above the
5 GiB floor. The exact pytest invocation with temporary runtime observer is
in the preceding W4 plan; it ran once, serially, with `-m fullclip`,
`--durations=0` and `--junitxml=work/wp-t6/w4/w4-fullclip.xml`.

`01-fullclip.log` reports **7 passed, 6450 deselected, 1 warning in
1556.05 s**, EXIT 0. `02-fullclip-check.json` verifies seven passing calls,
no failures/skips, the full sink's actual
`run.report.frames_written == frames` assertion with both operands 681, and
zero `gx011627_trim` fixture setups. Verification ended 13:32:43.746701Z.

Times below are from `w4-fullclip.xml` and the log's duration lines. JUnit
includes teardown; setup below the display threshold is "not listed", not
assumed exactly zero. The shared standard encode setup is charged once to
the sink, and the independent decoder reference setup once to R5.

| Full form | Displayed setup s | Displayed call s | JUnit total s |
|---|---:|---:|---:|
| R1 engine `[full]` | Not listed | 445.65 | 445.748 |
| R2 levels `[full]` | Not listed | 327.71 | 327.713 |
| R3 sink `[full]` | 163.24 | 60.30 | 223.542 |
| R4 round trip `[first30]` | 0.01 | 167.28 | 167.290 |
| R5 decode `[full]` | 42.94 | 107.31 | 150.251 |
| R6 forced default pipe `[full]` | Not listed | 135.28 | 135.280 |
| R7 CUDA `[full]` | Not listed | 104.02 | 104.019 |
| Sum of JUnit totals | | | 1,553.843 |

`03-cleanup.json` ends at 13:32:45.218973Z, records stage 2 complete,
steps/cleanup EXIT 0, removes both `w4-scratch` and `w4-fullclip`, and verifies
empty test status plus `git diff --quiet`. The dispatcher reports `W4 DONE`.
Only JSON/log/XML evidence remains. No trim was made by the full forms.
These are package-window proof figures, never a V16 row or the AFTER gate.
Collections and W4 satisfy rung 4; **rung 4 is CLOSED**.

## Seat 2 turn 6 -- report written; review and gate pending

Added `docs/reports/wp-t6-gate-sizing.md` from saved evidence only. It covers
the seven CUT and 31 KEEP rows, preserved assertions and ruled count operands,
W1 estimates versus W3/W4 measurements (with setup separated), trim rules and
checks, R2's chain, R4 figures at every candidate and at 30 plus signed margins,
row 10's banked tools lever, collection identities, W2-W4 controls and limits.
The six-name V4 delta and its two reasons are explicit, including CHARC's
required sentence about the three best-effort items exercised only by fullclip.
The report carries accept actions for CHARC and a clearly pending AFTER table.

Verification loop: compared saved W3/W4 JUnit times with displayed duration
phases. Confirmed that setup ownership moved between sink/levels and must be
charged once; report tables distinguish setup/call from totals with teardown.
Confirmed collection identities, the observed 681 sink operands, lazy full
fixture (zero trim setups), and cleanup in the saved JSON. No new footage,
GPU, collection, benchmark or pytest run occurred in this cell turn. Report
figures cite their saved source paths; historical baseline/map figures cite
the brief's recorded source, since the original baseline log is not copied
into this worktree. No metadata value, digest or footage path was copied.

| Turn-6 static check | Result / evidence |
|---|---|
| `uv run ruff check .` | PASS, EXIT 0, `All checks passed!`; `work/wp-t6/seat2-turn6-ruff.log`; uv ignored the inherited main-tree virtualenv and used this project's environment |
| `git diff --check` | PASS, EXIT 0; `work/wp-t6/seat2-turn6-diff-check.log`; Git's future CRLF-conversion notice does not change the current LF blobs |
| Report evidence / scope / LF proof | PASS, EXIT 0; `work/wp-t6/seat2-turn6-doc-proof.log`; seven CUT and 31 KEEP rows, all W3/W4 JUnit totals, observed collection counts, required Limit sentence, pending AFTER, no digest-like value or absolute Windows path, both blobs LF, only report and ledger changed |

Turn-6 verification disposition: suspected timing-category mismatch CONFIRMED
as setup attribution plus teardown inclusion, FIXED in the report's labels
and separate phase table. A suspected full-form trim setup is REJECTED by
the observer's zero setup count. The final evidence/scope pass found nothing
new. No product/test-code fix or new acceptance deviation was required.

Reviewer A (dispatcher-run Claude FAST pass), Reviewer B and the ONE final
two-leg gate remain pending. No convergence, gate PASS or Q6 saving verdict
is claimed. The next review findings are adjudicated under the fill's round
policy and recorded in the cumulative review-round ledger.

## Reviewer A R1 -- adjudication and single cleanup (seat 2 turn 7)

Read `work/wp-t6/rA1/review-r1.txt` in full. The dispatcher ran the
read-only Claude pass on `6ecc4e5..04b01d2`: model `claude-opus-5-5`,
effort high, 32 turns, `is_error=false`, model assertion passed,
`worktree_clean_after=true`. The CLI version and run start/end were not
supplied; no value is inferred. All ten permission denials were scratch
writes to `/tmp` or `%TEMP%`, not withheld-path access or transport failure.
The recorded verdict is `NO_NEW_CRITICAL_MAJOR`: zero critical, zero major,
three minor, eight advisory. The reviewer executed assertion/diff, guard,
collection and module-identity checks; workfile citations were withheld and
its report arithmetic was reasoned independently.

Durable evidence is the dispatcher's
`C:\Users\rwsmy\clearwater-review-evidence\wp-t6\r1\`.
Dispatcher-supplied MD5 prefixes: prompt `809caafc`, diff `f8965a99`,
input `eb983638`, JSON `08f7b6c1`, review `68b2ac99`.
The source transcript remains the authority for EXECUTED/REASONED tags.

| Finding | Severity / envelope / origin | Disposition | Confirmation and cited ground |
|---|---|---|---|
| F1 | Minor / in / NEW; EXECUTED | REPORT-ONLY | Confirmed: packet selectors cover video and non-tmcd data, not audio. Report now says "video and data packets" and lists audio's roster/rate/channels/tags limits. The brief's 4(b) is video-only and lock 2 governs data; an audio packet check would extend the explicitly fixed trim checks. No audio check added. |
| F2 | Minor / in / NEW; EXECUTED | FIX, result-bearing | Confirmed: a shorter nonempty data prefix formerly passed. Preserve prefix equality and additionally require copied count equal to source packets with `pts_time < T`, using exact `Fraction` comparison. Record expected count, count equality and packet equality; fixture's existing data assertion still requires `equal`. Synthetic boundary packet at T is excluded and shortened data now fails only the new count while video verdicts stay PASS. W2b positive parity and truncated-data controls now re-prove the guard; no timing tolerance or new metadata exception. |
| F3 | Minor / in / NEW; EXECUTED | FIX, result-bearing | Confirmed: contiguous 75-frame cut formerly passed without checking source packet 75. New `4c_cut_on_keyframe` requires packet at `count` to exist, carry K and have PTS equal to T; 4(c) conjoins it with its existing time-base/PTS check. Fixture passes planned T; three-argument callers independently derive the first eligible keyframe T. Synthetic N=75 and inconsistent T both fail by name. Original 4(a)-(e) and data assertions remain. W2b parity passes and N=75 fails the named cut sub-result, completing real re-proof. |
| F4 | Advisory / in / NEW; EXECUTED | REPORT-ONLY | Confirmed session-parametrisation grouping from reviewer collection: trim items move to the decode module block before remaining encode/jobs tests. Report flags changed warm-up/state order for the final gate's KEEP-row comparison; W3's restricted timing does not measure whole-leg order. No reordering plugin or test-order change introduced as a remedy. |
| F5 | Advisory / out (no NVENC) / NEW; REASONED | REPORT-ONLY | Fixture setup precedes body skip. Report R1 now says "first within the test body" and names the out-of-envelope failure-before-skip case. The mapped R1 instruction retains the body readiness check and adds the source fixture; changing dependency order is outside the mapped cut. |
| F6 | Advisory / in / NEW; REASONED | REPORT-ONLY | Old decode locator skipped a walk error; shared locator raises it. Report discloses the stricter R5-R7 rule. This is intentional under brief trim step 1 (unsearchable/missing folder RAISE), R5-R7's locator replacement, and DR-27 (1); encode/jobs locator behaviour remains as ruled. |
| F7 | Advisory / in / NEW; REASONED | DECLINE additional committed locator test | The conftest locator's direct test is absent; its branches remain code-reviewed. Brief "Files owned" grants exactly one new decode test (rung-2 parity), forbids changes to the existing encode lookup test, and does not grant a new locator-test module. This cleanup's new controls are limited to F2/F3 as dispatched. No unsupported claim of direct-test coverage is made. |
| F8 | Advisory / out (importlib mode) / NEW; EXECUTED | REPORT-ONLY | Report now states that importlib mode fails earlier importing the existing `fixture_plugin`, before the parity import. The pre-existing `pytest_plugins` line must stay byte-identical (conftest ownership lock); the default import mode remains the declared/proved envelope. |
| F9 | Advisory / in / NEW; REASONED | DECLINE retry/recovery policy | A lingering handle can make `rmtree` raise and the leg fail; this is a visible refusal, not silent acceptance with surviving media. The brief requires teardown removal and a nonzero failure if cleanup cannot establish it; it does not specify retry timing or recovery. Adding Windows-specific handling would also require N1's grant, which this brief does not provide. No handle-leak failure was demonstrated; no new retry policy is introduced in this bounded cleanup. |
| F10 | Advisory / in / NEW; REASONED | REPORT-ONLY | Confirmed `-video_track_timescale` fixes trim time base. Report now distinguishes the trim's forced 1/30000 check from `[full]` proof of the camera container's original time base. Full assertion remains unchanged. |
| F11 | Advisory / style, in / NEW; REASONED | FIX attribute docstring; DECLINE remaining style edits | Added one scoped attribute docstring for `ALLOWED_TAG_DIFFS` (plan 4.5). Retain R-a/rung-2's verbatim `pair_streams` copy and formatter fence rather than changing its annotations/style; tests are outside configured mypy. Retain literal `first6`, explicitly directed by seat-2 turn 3 and the selected six-frame map; no dynamic count is selected at runtime. No R4 code change is needed. |

This accounts for all eleven findings: three FIX items (F2/F3 and F11's
docstring), six REPORT-ONLY items, two wholly DECLINED items; F11's remaining
style suggestions are declined with their own grounds. No critical/major,
reopened finding or revert. Product-code fixes: zero. Result-bearing test
helper fixes: F2 and F3; test assertion changes in R1-R7: zero. No added
dependency, OS-specific code, metadata exception or pre-package conftest line
change. R1 meets the fill's zero-new-blocking round-termination criterion;
this is Q11's single cleanup. Its result-bearing trim guards were re-proved
in W2b, recorded below. R1 is converged; there is no round 2 under Q11.

### W2b request -- cleaned checker, four controls

`bash work/wp-t6/w2b.sh`, expected 2-5 minutes, runs alone at the dispatcher's
seat from this worktree root. It unsets `PYTEST_ADDOPTS`, sets headless Qt,
records start/free bytes and enforces >= 5 GiB before testing and controls.
Outputs are under `work/wp-t6/w2b/`. Fresh basetemps `w2b-trim` and
`w2b-guard`, plus `w2b-scratch`, are refused if pre-existing; each resolved
path must be under this worktree's work root and outside configured footage.

1. Parity test alone, requiring one pass (no skipped proof).
2. Guard suite, requiring all 60 passes.
3. Four real candidates through the same checker, no tracked-code edits:
   re-encode must FAIL 4(b); both flags late must FAIL 4(b) or 4(c); count 75
   with the source packet's own PTS must FAIL `4c_cut_on_keyframe`; copied data
   shortened by a 0.5 s second input must FAIL `data_count_to_cut` while the
   original packet-prefix equality and 4(a)-(e) still PASS. The second input
   supplies only non-tmcd data; video/audio retain the normal original input,
   fixed metadata flags and copy codec. No data decode occurs. The script
   asserts source count before 0.5 s is smaller than before T; unavailable
   plants or command/helper errors are STOPs, never counted as caught.
4. EXIT/INT/TERM cleanup removes only this invocation's owned scratch and
   basetemps after checking resolved absolute paths. JSON records counts,
   named PASS/FAIL results, pairing keys and file names only. Every runner has
   a separate log and `EXIT=` line; final output is `W2b DONE` or
   `W2b STOP stage=<n>`. No footage-derived scratch is kept.

Script MD5: `273352e4c1ac2efd61ef6999b2ae5a9f`. The request above was
executed successfully as W2b below. Historical W2-W4 figures remain historical;
W4 did not set up a trim and no R1-R7 assertion changed in cleanup.

### R1 cleanup light verification

| Check | Result / evidence |
|---|---|
| New checker sub-results, synthetic documents only | PASS, EXIT 0; `work/wp-t6/rA1-cleanup-synthetic.log`; good explicit/default T, packet at T excluded, non-keyframe, mismatched T, extra video count, truncated data, changed data bytes, pairing mismatch and original-line/LF proof |
| `uv run ruff check tests/conftest.py` | PASS, EXIT 0, all checks passed; `work/wp-t6/rA1-cleanup-ruff.log` |
| `uv run mypy` | PASS, EXIT 0, 141 source files; `work/wp-t6/rA1-cleanup-mypy.log`; configured mypy excludes tests |
| Formatter stdin comparison | PASS, EXIT 0, no formatting difference; `work/wp-t6/rA1-cleanup-format.log`; `uv run ruff format --stdin-filename tests/conftest.py -` wrote only captured output under work; no old line rewritten; final seat `--check` remains dispatcher's |
| Python syntax, embedded W2b programs and LF | PASS, EXIT 0; `work/wp-t6/rA1-cleanup-script-compile.log`; all three programs compile and script is LF |
| Embedded Python undefined/redefined names | PASS, EXIT 0; `work/wp-t6/rA1-cleanup-script-lint.log` |
| Exact W2b control program with synthetic I/O | PASS, EXIT 0; `work/wp-t6/rA1-cleanup-wrapper-synthetic.log`; all four named controls caught, new F2 count fails while prefix equality passes, F3 keyframe sub-result fails, shortened-input maps preserve original video/audio and copy codec; separate synthetic artifact folder, no real window evidence produced |
| Final `git diff --check`, ownership and baseline-line proof | PASS, EXIT 0; `work/wp-t6/rA1-cleanup-diff-check.log`, `rA1-cleanup-scope.log`; only conftest/report/ledger, all R1-R7 files and fixture assertion ASTs unchanged, every pre-package conftest line preserved, all three blobs LF |

Verification loop: confirmed F2/F3 with independent synthetic packet documents
before the seat re-proof. The positive trim passes both old and new guards;
each new plant fails its own sub-result. Explicitly checked that data
comparisons do not overwrite the independently reported video 4(b) value.
The final real four-control pass is not substituted with these synthetic
checks. No footage read, probe, pytest or GPU execution occurred in this cell
turn; Bash syntax validation is requested at the seat.

## W2b -- DONE; Reviewer A R1 converged (seat 2 turn 8)

Dispatcher generation 21 took the seat at 14:25Z on 2026-10-29; CHARC is
generation 7, with R1 cleanup position unchanged. The dispatcher reports
`bash work/wp-t6/w2b.sh` ran exclusively from 14:27:13Z through 14:28:28Z
(75 s), ending **W2b DONE, EXIT 0**. The saved window timestamp is
14:27:14.410635Z; cleanup ends 14:28:28.190149Z. Available memory was
9,408,053,248 bytes before the window and 9,428,738,048 bytes before controls,
both above the 5 GiB floor (`00-window.json`, `03-memory.json`). The script
MD5 remains `273352e4c1ac2efd61ef6999b2ae5a9f`.

Read all nine named evidence files under `work/wp-t6/w2b/` and independently
matched every MD5 against the dispatcher's table; verification is saved in
`work/wp-t6/seat2-turn8-w2b-md5.json`. These are record/log checksums, not
packet digests. No footage-derived file or tag value is copied here.

| Evidence file under `work/wp-t6/w2b/` | Verified MD5 |
|---|---|
| `00-window.json` | `feb3af23f6f4d3a1d4156d08f4af6c88` |
| `01-trim.log` | `ea6cb8f42866b322f1d2ed935ae53a5d` |
| `02-guard.log` | `8be8c52ba0c216ba96c11dc75cd6f7db` |
| `03-memory.json` | `c3700b8e7d429307efa5826066a25a97` |
| `03-reencode.json` | `9c093af5bd4da0910340f021082143f1` |
| `03-extra_frame.json` | `a66a276ef6beaf15173c8f301cc9eb99` |
| `03-non_keyframe.json` | `380493ab5bbc0248caabed70729cc31e` |
| `03-truncated_data.json` | `7dc75ffe50e8472febf06173abaa621e` |
| `04-cleanup.json` | `1a6c679ffccec81f945e4af071a8b5e0` |

Stage 1: `test_the_gx011627_trim_is_a_stream_copy_of_the_source` passed,
**1 passed in 3.29 s, EXIT 0** (`01-trim.log`). Stage 2:
`tests/test_conftest_guard.py` passed, **60 passed in 41.67 s, EXIT 0**
(`02-guard.log`). Stage 3: all four controls completed and were caught,
EXIT 0 (`03-controls.log` and the four `03-*.json` control records).

| Control | Frames expected / requested | Failed `checks` | `4b_count` | `4b_packets` | `4c_cut_on_keyframe` | `data_count_to_cut` | Caught |
|---|---|---|---|---|---|---|---|
| reencode | 90 / 90 | 4b, 4d, 4e | PASS | FAIL | PASS | FAIL | Yes |
| extra_frame | 90 / 91 | 4b, 4c | FAIL | PASS | PASS | PASS | Yes |
| non_keyframe | 75 / 75 | 4c | PASS | PASS | FAIL | FAIL | Yes |
| truncated_data | 90 / 90 | None | PASS | PASS | PASS | FAIL | Yes, data-packet record |

The truncated-data record has `failed_checks=[]` because data count is outside
`checks`; `count_equal=false`, `packets_equal=true`, `trim_packets=1` versus
`expected_packets_before_cut=3`, and therefore `equal=false`. It is rejected
by the fixture's separate `assert all(item["equal"] for item in
record["data_packet_checks"]), "data packets"` at `tests/conftest.py:853`.
This **matches F2's adjudication**: retain the old prefix predicate and require
its conjunction with the complete count to T, enforced by the existing data
assertion. The runner inspected this record to count the plant as caught;
it did not run a separate failing pytest consumer for that plant.

For re-encode, `data_count_to_cut=FAIL` reflects pairing failure rather than
a numeric data-shortage assertion. For the non-keyframe cut the independent
F3 sub-result FAIL is the required catch; its data record additionally reports
two copied packets versus three expected before T. Neither incidental result
is substituted for the required named control failure.

Stage 4 cleanup: EXIT 0, all steps complete. `04-cleanup.json` confirms removal
of `w2b-scratch`, `w2b-trim` and `w2b-guard`; only evidence records/logs remain.
No footage-derived scratch survives. The cleaned checker has a positive
parity pass plus the two old and two new caught controls. **Reviewer A R1 is
converged: the single cleanup is complete and re-proved, with no round 2
under Q11.** All eleven findings remain dispositioned as above; no severity,
envelope, NEW/REOPENED, fix or revert count changes.

Turn 13 changes only ledger/report documentation. The report replaces W2b
pending labels with these figures beside the historical W2 results; no code,
test assertion or runner script changed. Reviewer B, rebase and the ONE gate
remain at the dispatcher's seat. AFTER figures and Q6's verdict remain open.
Final `git diff --check` is recorded in
`work/wp-t6/seat2-turn8-diff-check.log` before handoff.

## Rung 0 facts (2026-10-29)

| Check | Observed result | Evidence / limits |
|---|---|---|
| HEAD | `6ecc4e5174dfd15080cc6fd59d63940839a9b430` | `git rev-parse HEAD`; matches the dispatch base |
| Branch | `wp-t6` | `git branch --show-current` |
| Initial worktree state | Clean; no porcelain output | `git status --porcelain` before writing this ledger |
| Baseline code identity | Empty diff stat | `git diff --stat 8bc927a..HEAD -- src tests tools pyproject.toml`; baseline of record stands |
| Environment sync | Already performed by dispatcher | Dispatch says `.venv` is synced; no new dependency or lock change |
| Installed pytest | `8.4.2` | Imported version only; `work/wp-t6/rung0-facts.json` |
| Configuration | Left untouched | Dispatcher supplied the gitignored local configuration; the cell did not open it |
| Baseline all collection at seat | 6,449; EXIT 0 | Dispatcher ran `base-collect.sh`; `work/wp-t6/base-all.txt` and `base-collection-summary.json` |
| Baseline parallel collection at seat | 5,313; EXIT 0 | Current expression; `work/wp-t6/base-parallel.txt` |
| Baseline serial collection at seat | 1,136; EXIT 0 | Current expression; `work/wp-t6/base-serial.txt` |
| Baseline collection identity at seat | PASS | Dispatcher reports no duplicates, disjoint legs, 5,313 + 1,136 = 6,449; `base-collection-summary.json` |

The attempted collection used the current expressions, `PYTEST_ADDOPTS` unset,
`QT_QPA_PLATFORM=offscreen`, `PYTHONPATH=scripts`, and the dispatched pytest shim:

```text
uv run python -m pytest --collect-only -q --basetemp=work/wp-t6/base-collect-all -p sandbox_mkdir_shim -p no:cacheprovider
```

The child started at about 11:07:31Z and was stopped after the 11:12:30Z reading
(296.125 CPU seconds). Captured runner output and its empty ID list are retained
as `work/wp-t6/base-sandbox-all.log` and `base-sandbox-all.txt`. There is no valid
pytest collection summary, no inferred count, and no asserted collection identity.
The hang's cause is unconfirmed. Collection does execute a module-level
`select_backend("auto")` in `tests/test_prototype_backend.py`; this is an observed
import mechanic, not a diagnosis of the hang. No further GPU probe was run.

The dispatcher completed the fallback `work/wp-t6/base-collect.sh` at its seat.
It writes separate logs, retains node-ID lines only in
`base-{all,parallel,serial}.txt`, checks each count against pytest's own summary,
then checks duplicates, disjointness and `parallel + serial = all`. The results
above supersede the incomplete sandbox attempt; the sandbox attempt remains
documented as a substrate limitation, not a test failure.

## W1 script and validation

`work/wp-t6/w1.sh` is gitignored scratch, not a committed file. It is run from
Git Bash at the worktree root, with `PYTEST_ADDOPTS` unset and headless Qt. Each
item has separate outputs under `work/wp-t6/w1/`; `driver.log` ends in `W1 DONE`
or `W1 STOP <why>`. Its `status.json` records the stage and UTC bounds. Each
measurement stage records free memory before work and refuses less than 5 GiB.
The dispatcher supplies the exclusive window conditions.

The script locates GX011627 only through `find_footage_file`, follows the exact
specified stream-copy flags as amended by CHARC R-b below, and checks 4(a)-(e)
before any trim encode. `ALLOWED_TAG_DIFFS` applies R-c by scope: format
`major_brand`, `minor_version`, `compatible_brands`, `encoder`; per-stream
`handler_name`, `language`; audio-only `timecode`. Every tag difference records
scope, KEY and allowed status only. Format `creation_time` additionally uses
R-e's semantic rule below, not an unconditional allow-list entry: split trim
text on `;`, require both keys and at least one part, and require every part
equal to the source text. Only the part count and equality boolean are recorded.
Missing either key is disallowed. Any disallowed difference stops 4(e).
Other failed trim checks and a levels/size-chain failure also stop the run.

Location values are removed from probe tag dictionaries before comparison.
Probe documents and packet hashes remain in memory; saved packet results carry
counts and equality status. Non-timecode data is compared as copied packet
prefixes, with pts, duration, size and hash, without decoding telemetry. Streams
are paired by kind and codec tag, in index order within a key, with equal counts
asserted and zero-based ordinals recorded. Raw
subprocess diagnostics and helper exception strings are withheld to prevent
metadata escaping into a log. A failed check records its named status and
privacy-filtered diagnostics; no raw probe document is retained.

The round-trip step measures all six plants from the existing test's own AST
dictionary at 30, 6, 10 and 15 frames. The fresh 30-frame run is necessary for
Q4's measured time-saving and half-margin comparisons. It records both signed
margins (mean minus 1.0, share minus 0.01), half-margin comparisons for positive
30-frame margins only, and verdicts for every plant. Nonpositive 30-frame margins
are marked untested, with a null half-margin verdict. Selection remains the next
turn's round-0 table; no
test count is changed this turn. The single row-10 cProfile run retains its
top 15 cumulative rows plus the bench-module rows from that same profile.

The script removes only its newly created `work/wp-t6/w1-scratch/` tree at exit,
after checking its resolved absolute path. It refuses pre-existing scratch and
asserts scratch is outside footage. The script, reports, summary JSON and
profile text stay; the trim, encoded files, binary profile and pytest temp files
inside scratch are removed. A cleanup failure becomes `W1 STOP`.

Scratch-script MD5s (W1 updated at turn 2):

- `work/wp-t6/w1.sh`: `47a9b605f54242f336c6cdf3b4c357ed` (turn 3).
  Turn 2's script was `d7b695280f2d5f48444d0cfa7f96cdd3`.
  Turn 1's script was `7e6d01a6a9ce5483a5e44ba254b0c135` (17,356 bytes).
- `work/wp-t6/base-collect.sh`: `7e5b253bec40c5b9e16ecda6c1d931ed`
  (2,641 bytes).

| Validation | Result | Evidence |
|---|---|---|
| Turn-1 embedded Python compile / LF bytes | PASS at turn 1 | `work/wp-t6/w1-static-check.json`; turn-2 validation below supersedes it for the corrected script |
| Synthetic location-value removal | PASS | `work/wp-t6/w1-helper-check.json`; a synthetic sentinel value is absent from the filtered document |
| Synthetic matching packet / stream / tag facts | PASS | Same helper check; 4(a)-(e) all PASS |
| Synthetic changed packet hash | Caught by 4(b) | Same helper check; scratch-only helper validation, not W2's real re-encode control |
| Synthetic extra video packet | Caught by 4(b) and 4(c) | Same helper check; not W2's real N+1 control |
| Collection-summary parser | PASS | `work/wp-t6/w1-static-check.json`; plain, fraction and selected-count summary forms checked |
| Bash syntax invocation | Sandbox blocked, not verified | `work/wp-t6/w1-bash-syntax.log`: Git Bash exits 256 with `CreateFileMapping ... Win32 error 5` before parsing; seat-side `bash -n` requested |
| W1 run 1 at seat | STOP at 4(d), 4(e) | Run 1 and diagnosis below; real footage and GPU commands remain exclusively at the dispatcher's seat |
| Turn-2 extracted program | `python -m py_compile` PASS, EXIT 0 | `work/wp-t6/turn2-py-compile.log`; extracted as `w1-embedded-turn2.py` |
| Turn-2 isolated pairing helper | PASS, EXIT 0 | `work/wp-t6/turn2-self-check.json`: swapped tmcd/gpmd pairs, unequal counts raise, two audio streams pair by sorted index and ordinal |
| Turn-2 checker integration and margin logic | PASS, EXIT 0 | Same self-check: correctly paired gpmd has three packets; audio timecode difference allowed, video timecode and firmware differences stop; negative baseline margin not tested, positive margin below half rejected |

Turn-3 seat-side re-run request (completed as run 3): move the old `work/wp-t6/w1/` to
`work/wp-t6/w1-run2/` first, preserving every run-2 artifact. Then run W1 in full:

```bash
bash work/wp-t6/w1.sh > work/wp-t6/w1-seat-driver.log 2>&1
```

The dispatcher completed this request in an exclusive window and supplied the
outputs for turn 4's round-0 table below. Runs 1 and 2 are preserved in
`w1-run1/` and `w1-run2/`. No build follows before CHARC reads the table.

## W1 run 1 -- STOP and diagnosis

The dispatcher ran turn 1's W1 from 2026-10-29 11:18:06.838947Z through
11:18:09.255278Z. It stopped at `stage=02-trim` with 4(d) and 4(e) failing.
`01-packets.json` records N = 90, T = 3.003000 s, 180 packets listed and
keyframe spacing of 30 frames. Checks 4(a), 4(b), 4(c) PASS: the 90 video
packets match in order, including their hashes, and their sorted pts are
contiguous at time base 1/30000. Scratch removal PASS in `06-cleanup.json`.
No levels, round-trip or profile measurements ran after the STOP.

The cell's checker incorrectly paired streams by container index. The source
order is video, audio, tmcd, gpmd; the trim order is video, audio, gpmd, tmcd.
tmcd's position is muxer placement, not a difference. This crossed the data
stream tags and compared source gpmd against trim tmcd, producing the incorrect
one-packet gpmd observation. The dispatcher's `work/wp-t6/w1diag/diag.json`
confirms the trim actually has three equal gpmd packets. It also shows the
format `firmware` key missing under the initial flags and present with
`-movflags use_metadata_tags`; audio `timecode` is absent in both trim variants.
The re-run will report audio timecode key presence again under the ruled flags.

The diagnosis also found `-t T` alone cut exactly 90 video and three gpmd
packets: draft correction (f) did not reproduce. Both `-frames:v N` and `-t T`
remain. No tag values or packet digests are reproduced in this ledger.

Finding classification: **major, confirmed, in-envelope, NEW, script-only**:
index-based stream pairing falsely failed a valid reordered roster and crossed
tag/data comparisons. Fixed through one self-contained `pair_streams` helper,
used for fields, rotation, tags, location-key presence and data packets; equal
per-key counts are asserted, and ordinals are recorded. The stream roster is
now a sorted multiset, retaining duplicates. The synthetic controls above
confirm the fix and reject mismatched counts. No product or test code changed.

CHARC authorized the separate metadata flag and scoped tag exceptions below.
The only added FFmpeg option is `-movflags use_metadata_tags`, before `-f mp4`.
Privacy handling, the 5 GiB guard, failure-text policy and scratch cleanup are
unchanged. W1 must run in full again before any real-measurement verdict.

## CHARC W1 ruling (verbatim)

Ruling ID `5b9dd6b0dfacc46e`, status `12fb9fd7`, supplied by the dispatcher at
turn 2. The following text governs the brief's trim steps 3-4:

**CHARC RULING on the WP-T6 W1 STOP (query 5b9dd6b0dfacc46e): R-a, R-b, R-c, R-d all CONCURRED, with one tightening (R-a) and one Limit sentence (R-c). Re-run W1 in full on turn 2's corrected `w1.sh`.** The diagnosis is sound: 4(b) and 4(c) passing on 90 packets with equal MD5s is the fact that matters (a true stream copy), and both failures are the check pairing streams by index after the muxer placed the regenerated `tmcd` last.

- **(R-a) CONCUR.** 4(d)'s roster is a MULTISET of (`codec_type`, `codec_name`, `codec_tag_string`); per-stream fields, tags and data packets are PAIRED by (`codec_type`, `codec_tag_string`). TIGHTENING: if more than one source stream shares a pairing key, pair them in source index order within that key, and the fixture asserts the trim has the same count under that key; the ordinal is recorded so a future two-audio clip cannot cross-pair silently. The fixture, the rung-2 test and `w1.sh` use ONE pairing helper. `tmcd`'s position is muxer placement, not a difference; the report says so in one sentence.
- **(R-b) CONCUR.** `-movflags use_metadata_tags` joins the FIXED flags (the trim is a SOURCE stand-in, so it keeps as much of the source's container as a copy can; `firmware` is what a real-container test may read). It is the only addition; the no-other-flag rule stands after it. The re-run reports whether the stream-level audio `timecode` survives under it (by key).
- **(R-c) CONCUR.** `ALLOWED_TAG_DIFFS` = muxer-written keys only: format `major_brand`, `minor_version`, `compatible_brands`, `encoder`; per stream `handler_name`, `language`; audio `timecode`. Any other key = STOP. Keys and scopes only, never a value. LIMIT for the report and the accept record: V4's tag items that read `handler_name` or the audio `timecode` are exercised against the real container only by the `fullclip` form; the `[trim]` form exercises them against the trim (the output is compared with what the test read).
- **(R-d) CONCUR.** The draft's correction (f) did not reproduce (`-t T` alone cut exactly 90 video and 3 `gpmd` packets); recorded in the report; `-frames:v N -t T` both stay.

For the record at the accept: N = 90, T = 3.003 s, keyframes every 30 frames (counts only). Codex depth 104,555 of 258,400 after turn 1: the ~250K evaluation point is at about turn 5 at this rate; plan the yields so the round-0 table and rung 2 land before it, and re-seat at the rung-2 commit if the figure says so.

Additional binding turn-2 instruction on Q4: test half-margin retention only
for a margin strictly positive at 30 frames; report both margins regardless.
The script marks other margins untested and applies every positive margin's
half-margin test. The unit check uses the script's actual comparison AST.

## W1 run 2 -- STOP 2

The dispatcher ran turn 2's corrected script (MD5 `d7b695280f2d5f48444d0cfa7f96cdd3`)
at its seat on 2026-10-29 from 11:27:22Z to 11:27:25Z. Checks 4(a)-4(d) PASS;
4(e) FAIL. The only disallowed tag difference is format `creation_time`.
Pairing now correctly matches source gpmd index 3 with trim index 2: three trim
packets equal the source prefix. The audio `timecode` key is present in the
source and absent in the trim (`survives_by_key` false), answering R-b's question.
No levels, round-trip or profile measurements ran after this STOP.

The dispatcher's boolean-only probe at
`work/wp-t6/w1diag/creation_time.json` reports byte-identical format
`creation_time` without `use_metadata_tags`. Under that flag it reports two
semicolon-separated parts, each equal to the source's text. It also records
scratch removal. No tag text is copied into this ledger or the saved checks.

Turn 3 adds the format-only semantic check inside the existing `trim_checks`
helper. The record is exactly scope, key, parts and every-part-equals-source;
tag differences also retain their allowed status. Neither the scoped R-c
allow-list nor the FFmpeg flags change. No other tag receives semantic treatment.
The extracted program passes `python -m py_compile`, EXIT 0
(`work/wp-t6/turn3-py-compile.log`). Synthetic checks pass for equal repeated
parts, an unequal part, a missing key on either side, both keys missing, and
rejection of the same exception on stream tags, EXIT 0
(`work/wp-t6/turn3-self-check.json`, `turn3-self-check.log`).

## CHARC STOP 2 ruling (verbatim)

Ruling ID `42a1be58329e3559`, status `33ff5687`, supplied at turn 3:

**CHARC RULING on WP-T6 W1 STOP 2 (query 42a1be58329e3559): R-e CONCURRED, R-b KEPT, with ONE rung-3 check that can still flip to your alternative on evidence. Re-run W1 on turn 3's one-key amendment.**

- **(R-e) CONCUR.** Format `creation_time` is allowed under the SEMANTIC rule: the trim's value split on `;` gives one or more parts and EVERY part equals the source's value; anything else is a STOP. The shared helper checks it; the record carries only `parts` and `every_part_equals_source`. No other key gets a semantic rule; the allow-list (R-c) is otherwise unchanged. Audio `timecode` not surviving under the flag is recorded as answered (R-b's question) and stays in the allow-list.
- **R-b stays** because `firmware` is why the flag exists: the trim is a source stand-in, and a V4 comparison between an export and its source should see the same best-effort tag differences on the trim as on the real clip.
- **ADDED rung-3 CHECK (the measurement that settles it).** The `[trim]` engine run's `fidelity_record` lists its MANDATORY, REQUIRED and BEST-EFFORT differences by item NAME. Compare the best-effort list with the full clip's known eight (WP4.2 task 10, `work\wp4.2\v4\`). (i) Same set, or the trim's set differs only by items the trim's own container representation explains (the duplicated `creation_time` key, the kept `firmware`): record the delta by item name as a Limit and proceed. (ii) Any MANDATORY or REQUIRED item differs on the trim that is SAME on the real clip: STOP, and the fallback is your alternative (drop R-b, `creation_time` byte-identical, `firmware` joins the allow-list), re-running W1 and W3. The report states which branch was taken and why.
- **Slip 2 (the `creation_time` value printed once to your terminal):** acknowledged, no action. It is a recording timestamp, not a location key and not the footage path; it reached no file, post or report. Lock 3 still holds for every artefact: no tag VALUE in the report, the ledger or the evidence folder, this one included.
- **Slip 1 (bare cd, read-only, cell idle):** acknowledged, no action.

Depth: Codex 123,658 of 258,400 after turn 2; turns 3 (amendment) and 4 (round-0 table) are small. The rung-2 fixture build is the first real turn; if the figure after turn 4 is above about 190K, re-seat BEFORE rung 2 so the build and rung 3 happen in one cell.

## Rung-3 plan notes -- added fidelity check

The trim engine run must retain its `fidelity_record` difference item NAMES
separately for MANDATORY, REQUIRED and BEST-EFFORT. Compare BEST-EFFORT names
with the full clip's known eight from WP4.2 task 10 (`work/wp4.2/v4/`). The
same set, or a delta explained only by duplicated format `creation_time` or
kept `firmware`, proceeds with the named delta recorded as a Limit. Any
MANDATORY or REQUIRED trim difference that is SAME on the real clip is a STOP:
drop R-b, require byte-identical `creation_time`, add `firmware` to the scoped
allow-list, and re-run W1 and W3. The report must name the branch and evidence.
This is a future measurement obligation; neither branch is claimed yet.

## Rung-1 round-0 table -- W1 run 3

Evidence is `work/wp-t6/w1/`, script MD5
`47a9b605f54242f336c6cdf3b4c357ed`. The dispatcher ran it exclusively from
2026-10-29 11:33:05.984516Z through 11:41:23.101978Z (497.12 s), with
10,804,830,208 available bytes before item 1 (about 10.06 GiB). `status.json`
records `W1 DONE`; dispatcher reports EXIT 0. `06-cleanup.json` confirms
scratch removal. All figures below come from these saved outputs; turn 4 ran
no new measurement, profile or test.

| Item | Round-0 result / recommendation |
|---|---|
| 1. Cut point | N = 90, T = 3.003000 s; keyframes every 30 frames (180 packets listed). |
| 2. Trim checks | 4(a) PASS; 4(b) PASS; 4(c) PASS; 4(d) PASS; 4(e) PASS. gpmd pairs source 3 -> trim 2, ordinal 0, three packets equal the source prefix; source has 23 packets. Location-key presence equal. |
| 3. Tag rules | Retain R-c's scope-aware allow-list and R-e's format-only semantic rule. Every observed difference is allowed; all scopes, keys and reasons appear in the tag table below. No new exception proposed. |
| 4. Audio timecode | Does not survive: source has the key, trim lacks it, `survives_by_key=false`. This answers R-b; audio-only exception remains under R-c. |
| 5. R2 levels / sizes | PASS: high 27,731,069 bytes / 5.2 Main; standard 13,720,197 / 5.1 Main; draft 6,639,630 / 5.0 Main. Ratios 2.021186 and 2.066410, both > 1.25. Three-encode wall 76.565051 s; standard proof tied, 123 samples, 90 frames written. |
| 6. R4 count | CUT to six, the smallest candidate: base and all six plants pass, all nine applicable positive-baseline half-margin tests pass. Six-frame wall 35.772337 s; 30-frame wall 160.467322 s; saving 124.694986 s > 30 s. Per-plant margins below. |
| 7. Row 10 | Tools lever named: `tools/prototype/bench.py:1305` `stray_processes`, four calls, 59.501 s cumulative, performing repeated per-process CPU sampling. `stop` at line 1211 takes 16.303 s cumulatively (thread join and final sample). Keep the test unchanged; bank the instrument overhead for follow-on. |
| 8. Updated estimate | R1-R7 estimated after sum 230.73 s vs baseline 1,567.37 s: gross saving 1,336.64 s. Add measured packet-list/trim setup 2.21 s: net serial saving about 1,334.44 s, projected AFTER about 1,286.88 s, plus unmeasured fixed/setup and new trim-test overhead. Per-row model below; this is not the gate result. |
| 9. Rungs 2-4 | Proceed only after CHARC's round-0 reply. Share the corrected checker and single pairing helper (pairing helper copied verbatim); retain R-b, R-c and R-e. R4 gate form is `[first6]`, full form `[first30]`; the six other CUT tests use `[trim]` / `[full]`. Added rung-3 fidelity comparison and fallback remain mandatory; details below. |

Observed tag differences (each grouped row enumerates every key that differed):

| Scope | Keys | Allowed | Reason |
|---|---|---|---|
| format | `compatible_brands`, `encoder`, `major_brand`, `minor_version` | true for each | Muxer-written keys, R-c |
| format | `creation_time` | true | R-e semantic rule; two parts, every part equals source |
| stream-audio-mp4a-0 | `handler_name`, `language`, `timecode` | true for each | Muxer-written keys, R-c; timecode allowed only on audio |
| stream-data-tmcd-0 | `handler_name` | true | Muxer-written key, R-c |
| stream-data-gpmd-0 | `language` | true | Muxer-written key, R-c |

The semantic record is:

```json
{"scope": "format", "key": "creation_time", "parts": 2, "every_part_equals_source": true}
```

`ALLOWED_TAG_DIFFS` remains format {`major_brand`, `minor_version`,
`compatible_brands`, `encoder`}; every stream {`handler_name`, `language`};
audio only {`timecode`}. Format `creation_time` is checked semantically, never
unconditionally allowed. Missing either key or a nonmatching part stops the
check. `firmware` needs no exception: it is retained by R-b's flag. tmcd's
position is muxer placement, not a difference. The R-c Limit still applies:
real-container `handler_name` and audio `timecode` are exercised only by the
fullclip forms; trim exports are compared with the trim's own tags.

R4's base at six frames has mean 0.684298522 and share-over-2 0.007303268;
at 30 it has mean 0.686802822 and share 0.007224387. Both means are <= 1.0
and both shares <= 0.01. Every plant exceeds at least one bound at six and 30.
Margins below are signed figure-minus-bound; mean is in 1/255 units and share
is a proportion (not percent). Half-margin retention tests only columns whose
30-frame margin is positive.

| Plant | Mean margin, 6 | Mean margin, 30 | Share margin, 6 | Share margin, 30 | Applicable half tests |
|---|---:|---:|---:|---:|---|
| encode range | 4.108201094 | 4.323826024 | 0.705041460 | 0.719845802 | Both PASS |
| encode matrix | 2.111772140 | 1.980265734 | 0.587846894 | 0.560920048 | Both PASS |
| accurate_rnd dropped in both halves | 0.131466726 | 0.141306802 | 0.059446286 | 0.063483034 | Both PASS |
| accurate_rnd dropped in the first decode | -0.219201817 | -0.204205750 | 0.027213441 | 0.030655778 | Share PASS; mean untested |
| siting center | -0.301407543 | -0.294479357 | 0.005481804 | 0.006681069 | Share PASS; mean untested |
| siting topleft | -0.272250575 | -0.265261700 | 0.009787849 | 0.011094204 | Share PASS; mean untested |

The saved comparisons also show all verdicts and applicable half-margin tests
passing at 10 and 15. Six is therefore the smallest qualifying N; the other
candidates do not alter the selection. The mean/share bounds and every planted
defect assertion remain unchanged. This is a measured CUT decision, not a loss
of an assertion.

The row-10 cProfile reports 80.481 s overall; the enclosing command wall is
80.873235 s. `05-result.json` records EXIT 0 and `1 passed, 1 warning in 79.54s`.
The first top-15 block contains pytest/runpy wrappers. The separate bench block
from the same profile names `bench.main` at 78.325 s and `stray_processes` at
59.501 s in four calls. The latter samples other processes' CPU use before and
after its sampling interval (`psutil.process_iter` and per-process
`cpu_percent`). The `stop` method joins the sampling thread and takes a final
sample. Cumulative timings overlap; the table is not an additive attribution.
The follow-on lever is repeated whole-system sampling and sampler shutdown,
not frame count. No deeper profile was run, no claim of a specific fix is made,
and no profiled timing replaces the unprofiled baseline row in the projection.
Disposition: BANKED follow-on candidate for CHARC's accept register, owner as
trigger under Q7; no `tools/` change in WP-T6.

Updated estimate, seconds (baseline setup+call totals, matching the brief):

| CUT | Baseline | Estimated after | Estimated saving | Model / measurement |
|---|---:|---:|---:|---|
| R1 engine | 456.31 | 60.31 | 396.00 | Baseline x 90/681; unmeasured |
| R2 levels | 330.02 | 51.04 | 278.98 | Two thirds of measured 76.565051 s encode triplet; allocation estimated |
| R3 sink | 221.69 | 32.15 | 189.54 | Remaining encode third + baseline V4 call 50.12 x 90/681; allocation/check cost estimated |
| R4 round trip | 169.97 | 35.77 | 134.20 | Six-frame wall measured in W1 |
| R5 real decode | 152.09 | 20.10 | 131.99 | Baseline x 90/681; unmeasured |
| R6 default pipe | 131.88 | 17.43 | 114.45 | Baseline x 90/681; unmeasured |
| R7 CUDA decode | 105.41 | 13.93 | 91.48 | Baseline x 90/681; unmeasured |
| Total | 1,567.37 | 230.73 | 1,336.64 | Rounded rows; sums calculated before rounding |

The encode split is an allocation convention, not three per-quality timings:
only their combined 76.565051 s is measured. It counts the shared standard
encode exactly once. R3's 171.57 s baseline setup is replaced by its allocated
standard encode; its 50.12 s V4 call is scaled separately. R5's scaled figure
includes its reference setup, which is not charged again to R6 or R7.

Packet listing (0.213327 s) plus trim/check setup (1.992035 s) add 2.205362 s
once per session in this model. Keeping the rest of the baseline leg fixed
gives 2,621.32 - 1,336.643625 + 2.205362 = 1,286.881737 s (about 21.45 min),
before the unmeasured repeated checks in the new trim test and retained fixed
costs in the scaled rows. Scaling an entire setup/call by frame count is
optimistic about startup cost; W3 and the one final gate must replace the
estimate. W1's within-run R4 saving is 124.694986 s; the 134.197663 s baseline
comparison includes the 9.502678 s difference between the baseline and W1's
30-frame runs and is not all attributable to sizing. Host spread remains the
316 s between the identical-code WP4.2 legs, with single-test movements up to
40 s. KEEP rows are not newly measured here. Q6's per-CUT-sum verdict remains
pending the final gate's junit figures. The 900 s target remains out of reach
in this estimate and is not a pass criterion.

Build-plan consequences: rung 2 adds the guarded session trim and lazy trim/full
fixture, the single stream-pairing helper and the shared R-c/R-e checks, with
the fixed flags including R-b. Existing conftest lines remain byte-identical.
W2's real re-encode and N+1 controls, guard tests and teardown proof remain
required. Rung 3 implements all seven CUT rows, including R4 at six, preserving
full-size assertions. The added engine fidelity check above compares all
MANDATORY/REQUIRED/BEST-EFFORT difference names with WP4.2's full-clip record:
only the ruled explained best-effort delta may proceed as a Limit; the stated
mandatory/required mismatch triggers the R-b fallback and W1/W3 re-runs.
No branch of that future check has been selected by W1.

Rung 4 registers the marker and verifies seven fullclip forms (six `[full]`,
one `[first30]`). Expected collection arithmetic, not yet observed: all 6,457,
parallel 5,313 unchanged, serial 1,137, fullclip 7; pairwise disjoint and their
union equal to all. Seven unsuffixed CUT IDs become fourteen suffixed forms,
plus one new trim test. W4 must run all fullclip forms once, including the
681-frame sink assertion. No build occurred at turn 4; yield this table for
CHARC before rung 2, with the dispatcher's depth check at about 190K.

## CHARC round-0 ruling (verbatim)

Message `22065ec5da3b4dbe`, 2026-10-29 11:50:01Z, supplied by orchestrator
generation 20 at turn 5:

**CHARC RULING on the WP-T6 round-0 table (query 075c1ac8226a2a08, ledger 65b9f4f): PROCEED to rung 2 on the table as it stands. All seven rows CUT; R4 to six frames; row 10 BANKED.**

- **Trim:** N = 90, T = 3.003 s, keyframes every 30; checks 4(a)-(e) PASS under R-a/R-c/R-e; the five allowed differences are exactly the muxer-written keys plus the semantic `creation_time` (2 parts, every part equal). The audio `timecode` loss stands as the Limit I named. ACCEPTED as the trim of record; the fixture reproduces these flags and checks verbatim.
- **R2 (levels):** PASS on the trim: 5.2 / 5.1 / 5.0 Main, ratios 2.02 and 2.07 against the 1.25 links, standard proof tied, 90 frames written, three encodes 76.6 s. Whole-trim count as ruled (Q5).
- **R4 (round trip): CUT to six frames**, by Q4's rule: base inside both bounds at 6 (mean 0.684 of 1.0; share 0.0073 of 0.010), every plant exceeds a bound with the same verdict pattern as at 30 (the three siting/first-decode plants detect by share only at BOTH counts, so nothing changed in kind), all nine applicable half-margin tests pass, wall 35.8 s against 160.5 s. ADDED for the report: the base's figures at 6 AND at 30 side by side (the share headroom at 6 is 27 %, and a reader must see that the 30-frame base was no wider), and the sentence that FFmpeg's bit-exact filters make these verdicts deterministic (`test_color_roundtrip.py:49-50`).
- **Row 10: BANKED, lever named.** `tools/prototype/bench.py:1305` `stray_processes` costs 59.5 s over four calls of an 80.9 s run, sampler `stop` 16.3 s more. Not this package (no `tools/`). I write the DR row at WP-T6's accept and RECOMMEND a Codex micro-package right after (one file, one function, the gate's own figure as the proof): about 60-75 s off the serial leg for a one-line brief. The owner's Q7 trigger covers the rest of the gap list; this item is cheap enough to go without waiting.
- **Estimate:** CUT rows 1,567 -> about 231 s; projected serial leg about 1,287 s plus the trim test; Q6's verdict is the per-test sum at the gate, as ruled. 900 s stays a target.
- **Depth:** 152,018 of 258,400 after turn 4: proceed to rung 2 in this cell. Re-evaluate after rung 2's commit: if the figure is above about 200K, re-seat BEFORE rung 3 (the rung-3 edits touch four files and carry the V4-delta check; they belong in one cell with the report).
- **Rung 2 as planned:** the shared pairing/semantic helper, `gx011627_trim` and `gx011627` in `conftest.py` additive, the trim-parity test with its two planted controls; W2 = that test plus `test_conftest_guard.py`.

## Rung 2 -- build

Turn 5 adds `GX011627_FRAMES = 681` (documented), R-c's scoped
`ALLOWED_TAG_DIFFS`, the session `gx011627_trim` and lazy trim/full `gx011627`
fixtures, and the shared checker in `tests/conftest.py`. The module docstring
gains one paragraph naming the fixtures. Every pre-existing conftest line is
byte-identical: the static proof admits only equal/insert diff operations.
The guard, skip hook, release fixture and plugin statement are unchanged.
Only stdlib imports were added at module level (`Iterator`, `Any`); all
video-fidelity, product, subprocess and probe imports are inside function bodies.

The single `pair_streams` helper is copied verbatim from W1, with a local
formatter fence preserving that copy. `gx011627_trim_checks` ports W1's same
comparison predicates and returns its sanitized record instead of writing a
file and raising at the runner boundary. This lets both the fixture and the
parity test assert each of 4(a)-(e) by name and also assert copied data-packet
equality. W1/current comparison ASTs are identical after helper-name mapping.
The roster diagnostic's fixed-width zip now has `strict=True` to satisfy ruff;
each projected tuple has exactly the three roster fields, so its result is
unchanged. No assertion or tag exception is weakened.

The helpers filter location values before comparisons, retain packet digests
only in memory, pair repeated stream keys by index/ordinal, and apply R-e only
to format `creation_time`. The shared trim-plan helper reproduces the ruled
packet listing and fixed copy flags, including only R-b's added
`-movflags use_metadata_tags`. The source locator retains the ruled exact skip
rule: only an absent clip after a successful folder search skips; ambiguous,
missing-folder and unsearchable-folder cases raise.

The trim fixture checks both its temp root and folder against the configured
footage folder, asserts the folder remains under the resolved session root,
and removes its own trim folder in `finally`, including failed setup. The full
fixture requests the trim dynamically only for its trim parameter; the full
parameter locates the source and yields the 681-frame constant. The marker is
applied to the full parameter as specified; registration remains rung 4.

`tests/test_io_video_decode_hw.py` gains only
`test_the_gx011627_trim_is_a_stream_copy_of_the_source`, marked footage/slow.
It imports the checker and locator locally from `conftest`, selecting the same
loaded module as the fixture and avoiding a duplicate helper or new support
file. All earlier bytes of that test file are an unchanged prefix. Rung-3
decode cuts are not implemented yet.

### W2 plan and control integrity

`work/wp-t6/w2.sh` runs from Git Bash at the worktree root, unsets
`PYTEST_ADDOPTS`, sets headless Qt, and records the window start/free bytes.
It enforces >= 5 GiB before the parity test and again before controls. Pytest
commands and every runner result go to separate logs under `work/wp-t6/w2/`
with `EXIT=` lines; fresh basetemps are `w2-trim` and `w2-guard`.

1. Run the new parity node alone. A skip is not accepted as a positive proof:
   the command must exit zero and report one passed test.
2. Run `tests/test_conftest_guard.py`, requiring exit zero.
3. Import the same conftest checker/trim plan in the seat-side control program.
   Make scratch trims under `work/wp-t6/w2-scratch/`: replace `-c copy` with
   `-c:v libx265`, and separately change `-frames:v N` to `N+1`. The original
   expected count N is passed to the checker. Record named PASS/FAIL checks,
   caught status, counts and key-only diagnostics in `03-reencode.json` and
   `03-extra_frame.json`. A command/helper error is not a caught control;
   both controls are attempted and the step fails unless the re-encode fails
   4(b) and N+1 fails 4(b) or 4(c).
4. The EXIT trap removes only scratch created by this invocation, after checking
   its resolved absolute path. Pre-existing scratch is refused and preserved.
   It lists remaining `GX011627-trim.mp4` filenames in both basetemps and fails
   if any remain. `04-cleanup.json` records the end time and cleanup results;
   the script prints `W2 DONE` or `W2 STOP stage=<n>` last. All reports/logs stay.

The N+1 plant retains the fixed `-t T`; the script will report an uncaught
control and STOP if that cap prevents an extra packet. It will not manufacture
a rejection by changing the check's expected count or adding an unruled flag.
Likewise a re-encode command failing before checks cannot count as 4(b) failing.
These are control-integrity conditions, not results: W2 has not run in the cell.

W2 script MD5: `1f4025ca3fa944daf62908e658f6423f` (gitignored).
Expected seat window: about 5-10 minutes, with the CPU re-encode the uncertain
part; no other heavy work. Exact command: `bash work/wp-t6/w2.sh`.

### Rung-2 static checks and verification record

| Check | Result | Evidence |
|---|---|---|
| `uv run ruff check tests/conftest.py tests/test_io_video_decode_hw.py` | PASS, EXIT 0 | `work/wp-t6/rung2-ruff.log`; initial B905 fixed with strict fixed-width zip, then its long line wrapped |
| `uv run mypy` | PASS, EXIT 0; 141 source files | `work/wp-t6/rung2-mypy.log` |
| Bash `-n work/wp-t6/w2.sh` | Sandbox blocked, EXIT 256 | `work/wp-t6/rung2-bash-syntax.log`; `CreateFileMapping ... Win32 error 5` before parsing; seat syntax check requested |
| Additive conftest / appended test | PASS, EXIT 0 | `work/wp-t6/rung2-static-proof.json`; every old conftest line and test byte preserved |
| Single shared pairing / predicates | PASS | Same proof: pairing source verbatim, comparison ASTs unchanged |
| Python syntax / W2 names | PASS | Two owned files and three embedded W2 programs compile; embedded F821/F811 check passes, EXIT 0 (`rung2-w2-python-lint.log`) |
| Module-level dependency envelope / LF | PASS | Same proof; no product/video-fidelity import at module level, all edited blobs LF |
| Full `ruff format --check .` | Dispatcher seat pending | Only the new fragment was formatted in scratch; existing conftest bytes preserved |
| `git diff --check` / owned scope | PASS, EXIT 0; only three owned paths | `work/wp-t6/rung2-diff-check.log`; conftest 456 insertions / zero deletions, decode test 19 insertions / zero deletions |
| W2 footage, guard and planted controls | Pending seat | No footage/GPU command or pytest execution in this cell turn |

The verification loop found one lint issue in the moved diagnostic zip; its
strictness and wrapping were corrected inside added code. The byte-preservation,
single-helper and unchanged-predicate checks passed after that fix. No source,
tool, dependency or fixture-manifest change occurred. The final report must
retain the side-by-side R4 base figures at six and 30 and state that FFmpeg's
bit-exact filters make these verdicts deterministic in the declared envelope
(`tests/test_color_roundtrip.py:49-50`), as the ruling requires.

## Heavy-run ledger

One row per actual heavy run will include start, end, exact command, selected
counts, EXIT, free memory before and evidence paths. Requested runs are explicitly
pending and are not validation results.

| Window | Start / end UTC | Command | Counts / EXIT | Free memory before | Evidence / disposition |
|---|---|---|---|---|---|
| W1 run 1 | 2026-10-29 11:18:06.838947Z / 11:18:09.255278Z | `bash work/wp-t6/w1.sh > work/wp-t6/w1-seat-driver.log 2>&1` | N=90; 4(a)-(c) PASS, 4(d)-(e) FAIL; STOP; process EXIT not supplied | 10,942,857,216 bytes before item 1; 10,942,246,912 before item 2; guard passed | `work/wp-t6/w1/` to be preserved as `w1-run1/`; checker fixed, re-run requested |
| W1 run 2 | 2026-10-29 11:27:22Z / 11:27:25Z | `bash work/wp-t6/w1.sh > work/wp-t6/w1-seat-driver.log 2>&1` | 4(a)-(d) PASS, 4(e) FAIL; STOP; process EXIT not supplied | Not supplied at turn 3 | `work/wp-t6/w1/` to be preserved as `w1-run2/`; semantic amendment authorized |
| W1 run 3 | 2026-10-29 11:33:05.984516Z / 11:41:23.101978Z | `bash work/wp-t6/w1.sh > work/wp-t6/w1-seat-driver.log 2>&1` | 4(a)-(e) PASS; three encodes; four round-trip counts; row 10: 1 passed, 1 warning; W1 DONE, EXIT 0 | 10,804,830,208 bytes before item 1; exclusive per dispatcher | `work/wp-t6/w1/`; scratch removed; round-0 table above |
| W2 run 2 | 2026-10-29 12:14:25Z / 12:15:41Z | `bash work/wp-t6/w2.sh` | Parity 1 passed in 3.63 s; guard 60 passed in 41.20 s; controls not caught, STOP stage 3, stage EXIT 1; cleanup EXIT 0 | 10.37 GB per dispatcher | `work/wp-t6/w2-run2/`; scratch removed, no trim left; controls ruling above |
| W2 run 3 | 2026-10-29 12:23:16Z (dispatcher; window record 12:23:17.480106Z) / 12:24:30.353107Z | `bash work/wp-t6/w2.sh` | Parity 1 passed in 3.57 s; guard 60 passed in 41.55 s; both controls caught; W2 DONE, EXIT 0; cleanup EXIT 0 | 10,016,727,040 bytes in window record | `work/wp-t6/w2/`; script MD5 `e97c51289cb85137cf5553619970cf31`; scratch removed, no trim left |
| W3 run 1 | 2026-10-29 12:42:26.485311Z / 12:48:00.365103Z | `bash work/wp-t6/w3.sh` | 8 passed in 322.26 s; stage 2 STOP on reference-path slip; controls not run; stage EXIT 1, cleanup EXIT 0 | 10,686,595,072 bytes | `work/wp-t6/w3-run1/`; scratch removed, tests/diff clean and bytes unchanged |
| W3 run 2 | 2026-10-29 12:50:55.706810Z / 12:56:23.544816Z | `bash work/wp-t6/w3.sh` | 8 passed in 258.91 s; one standard encode; V4 branch (i); both controls caught; W3 DONE EXIT 0, cleanup EXIT 0 | 11,001,569,280 bytes before window; 10,989,305,856 before main pytest | `work/wp-t6/w3/`; script MD5 `0dd11553112ae203b95a0952c9485f96`; scratch removed, tests/diff clean and bytes unchanged |
| W4 | 2026-10-29 13:06:46.706213Z / 13:32:45.218973Z | `bash work/wp-t6/w4.sh` (after candidate collections passed) | 7 passed, 6450 deselected, 1 warning in 1556.05 s; W4 DONE, pytest/cleanup EXIT 0; observed both sink operands 681; zero trim setups | 11,047,211,008 bytes | `work/wp-t6/w4/`; script MD5 `16847bf19ddb53f9cc88f018fc9b8ad5`; scratch/basetemp removed, tests/diff clean |
| W2b, R1 cleanup | 2026-10-29 14:27:13Z (dispatcher; window record 14:27:14.410635Z) / 14:28:28.190149Z | `bash work/wp-t6/w2b.sh` | Parity 1 passed in 3.29 s; guard 60 passed in 41.67 s; four controls caught; W2b DONE, all stage/cleanup EXIT 0 | 9,408,053,248 bytes at window; 9,428,738,048 before controls | `work/wp-t6/w2b/`; script MD5 `273352e4c1ac2efd61ef6999b2ae5a9f`; scratch and both basetemps removed |

## Review-round ledger

Reviewer A uses the Codex-lane Claude pass at FAST tier under Q11; the fill
governs convergence. Per-finding dispositions and evidence are in the R1
section above. No Reviewer B pass has run.

| Round | Critical / major / minor / advisory | In / out | NEW / REOPENED | Reverts | Fixes | Transport / assertions / depth | Disposition |
|---|---|---|---|---|---|---|---|
| A R1, `6ecc4e5..04b01d2` | 0 / 0 / 3 / 8 | 9 / 2 (F5, F8 out; style F11 in) | 11 / 0; NEW blocking 0 | 0 | Product 0; test helper 2 result-bearing (F2, F3); attribute docstring and report/ledger cleanup; no R1-R7 assertion edits | Dispatcher native Claude process, `claude-opus-5-5`, high, 32 turns; model ok, `is_error=false`, clean worktree after; 10 scratch-write denials classified, no withheld access; CLI version not supplied. Seat-2 turn-6 input depth 98,187 / 258,400 | `NO_NEW_CRITICAL_MAJOR`; single cleanup complete, W2b positive proof and four controls caught; R1 CONVERGED, no round 2 under Q11. All F1-F11 adjudicated; B pending |

## Verification loop and turn boundary

Turn 1 examined the script against rung 1, its fixed flags and privacy locks.
Synthetic checks confirmed that the in-memory checker rejects changed packet
bytes and an extra packet, and discards location values. The helper checks are
script validation only; W2's real controls remain pending. An initial multi-path
shell `PYTHONPATH` was replaced with explicit portable Python path entries,
avoiding dependence on Git Bash path-list conversion. The final script compile
and helper checks are repeated after that edit. No product or test code changed.

Turn 2 applies the ruling above to W1 and records the dispatcher's baseline
collections. The isolated pairing and integration controls and extracted-program
`py_compile` pass, EXIT 0; the corrected script MD5 is recorded above. This is
script validation, not real footage evidence or W2's planted controls.

Turn 3 changes only W1's format `creation_time` comparison and this ledger.
The semantic rule and its failure cases pass synthetic checks; the extracted
program compiles. No footage or GPU command ran in the cell.

Turn 4 confirms W1 run 3's saved results and records the round-0 table, the
measured R2 chain and R4 six-frame choice, the row-10 tools lever and the
explicitly estimated projection. No test, measurement, profile or build ran in
this turn. Pending at handoff: CHARC's round-0 reply and dispatcher depth check
before rung 2. That historical handoff was answered by CHARC's ruling above.
Turn 5 builds rung 2 within the two owned test files plus this ledger and
prepares the gitignored W2 script. Pending now: seat W2, full format check and
the supplied turn-5 depth. If depth exceeds about 200K, re-seat before rung 3.
The next turn records W2's actual controls and results; no gate or completion
claim is made for this unrun rung.
