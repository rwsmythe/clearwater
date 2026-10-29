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
| W2 (requested, about 5-10 min) | Pending dispatcher | `bash work/wp-t6/w2.sh` | Pending parity/guard counts, two controls and EXIT | Script records bytes; >= 5 GiB required | `work/wp-t6/w2/`; no run yet |

## Review-round ledger

No Reviewer A or B round has run. Future rows carry severity counts,
in-envelope/out-of-envelope, NEW/REOPENED, reverts, product-code/test-only fixes,
transport/model evidence and dispatcher-read depth. Reviewer A uses the
Codex-lane Claude pass at FAST tier under Q11; the fill governs convergence.

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
