# WP4.4 cumulative ledger

## RESUME HERE -- seat 2, turn 2: R1 cleanup and report handed off

WP4.4 MOV input, CODEX lane, tier STRONG. Product base `5e3537d`;
branch `wp4.4`; this turn's entry HEAD `d427dc9`. Entry status was clean.
Seat 2 turn 1 was committed as `feat(wp4.4): normalize granted V4 comparison
equivalences`. Original MOV routing/naming/data allowlist and rotated fixture
are built; this turn completes the authorized terminating-round cleanup and
creates `docs/reports/wp4.4-mov-input.md`.

Reviewer A R1 (Claude opus/high, read-only) converged:
`NO_NEW_CRITICAL_MAJOR`, 0 critical / 0 major / 4 minor / 5 advisory.
The generation-25 dispatch explicitly authorizes adjudication, the listed
cleanup and report together this turn; it supersedes the earlier
adjudication-only yield for this terminating round. No behavior beyond that
cleanup was changed; no additional Reviewer A round is requested.

Remaining actions belong to the orchestrator: commit these paths, final phone
rerun because capture handling changed, attach safe edit-list rows, Reviewer B,
the ONE standard two-leg gate, and accept. No fullclip leg or harness gate.
The report says B and gate pending; no accepted/package-complete claim.
The exact safe-row payload was not supplied to the cell; supplied media_time 0,
negative ctts and SAME edit-list verdicts are recorded without inventing rows.
A seat-only allowlisted row extractor is supplied below. No footage read here.

Current checks: 1122 passed / 3 confirmed UNC sandbox failures / 5 deselected
in required six-file light selection. Ruff check, whole-tree format check and
mypy all EXIT 0. All 33 synthetic equivalence nodes and four new case-only
collision witnesses are included in the light run. Existing naming product
behavior already passes all four case-only witnesses; no new naming change.

### Governing grants and locks

- `197131faf8764ebd`: Q1 existing naming/GUI edits only; Q2 deterministic
  `MP4_DATA_CODEC_TAGS = frozenset({"gpmd"})`, tmcd excluded; Q3 house V4,
  no runner pixel bound; Q4 DR-15 OPEN/corroboration only; Q5 DV clips out,
  inventory transfer and code refusal text in report.
- `73d2797750c57625`: ONE token, tests/test_io_video_encode_units.py:80,
  meta -> gpmd. The original map assertions remain verbatim; line 753 meta
  remains unchanged because it is a packet-table row, not a map input.
- `093384f126589674`: stereo PCM qt fixture retained. Its prospective
  mono-layout row was superseded/folded into the next grant; no row opens.
- `9c8f461b73ec8c05`: compare.py THREE equivalences only: exclude matrix
  translation alone, absent/null SAR equals 1:1, absent/null layout equals
  mono at one channel. R1 keeps matrix indices 0,1,2,3,4,5,8 exact and notes
  source/output translations 6,7. Tests are in the new equivalence file.
- `fd2269acf257054d`: encode.py module/write docstrings only, original
  anchors 6/703, updated to describe the allowlist; no verify.py edit.
  Positional mixed-data warning limit goes in report; CHARC owns register.
- `5a8339db3b9c6b4a`: new case-only naming collision tests, never overwrite;
  no product fix unless a new STOP (none needed).
- Orchestrator gen 24 turn-4 ruling: phone record state done with warnings,
  successful exit, one output and exactly two mebx omissions. Assertions
  remain unchanged in this cleanup; runner capture now drains in finally.

Owned paths are listed in the report, including every extension/grant.
Only seven owned/granted files change this turn. No config, register,
interface, dependency, other existing test or footage content changes.
All new committed content is ASCII/LF; inherited GUI-test non-ASCII content
is outside this turn and was not normalized. No git writes, mailbox posts,
footage/GUI/GPU/slow/fullclip tests, or kept-basetemp deletions.

### Seat results supplied at generation 25

At d427dc9, gen 24, 23:35Z (not cell executions):

| Log under work/wp4.4/s2t1/ | Command/node | Result | EXIT |
|---|---|---|---|
| seat-footage.txt | tests/test_wp44_mov_input.py::test_phone_mov_runner_and_v4 -m footage | 1 passed in 60.15 s; footage figure of record | 0 |
| seat-prototype.txt | tests/test_prototype_clip.py light | 52 passed / 10 deselected | 0 |

The prototype collection stall at the cell is confirmed as a sandbox artifact,
an environment MINOR, not a product defect. The phone pass resolves the
turn-4 orientation/SAR witness after the granted equivalences; final cleanup
rerun remains requested. Safe format facts and privacy checks are in report.

### Depth

Seat-2 turn-1 yield / turn-2 entry: **151,726 input tokens**, binding window
**258,400**, dispatcher footer reading. Evaluate around 200K, STOP at a
step boundary near 250K. Do not substitute account pace for context depth.
This turn stays bounded to the dispatched cleanup, report, checks and yield.
Exit depth is for the dispatcher to read; no estimate is substituted.

### RUN REQUESTS -- orchestrator only, Git Bash

Create/retain the work-local log parent; remove VIRTUAL_ENV for each command.
No sandbox shim is used at the seat. Run the final phone node:

```bash
env -u VIRTUAL_ENV uv run pytest -q -rs tests/test_wp44_mov_input.py::test_phone_mov_runner_and_v4 -m footage --basetemp=work/wp4.4/s2t2-seat-footage > work/wp4.4/s2t2/seat-footage.txt 2>&1
```

After success, extract only format rows for the report's Q4 corroboration:

```bash
env -u VIRTUAL_ENV uv run python work/wp4.4/s2t2/edit_rows.py work/wp4.4/s2t2-seat-footage > work/wp4.4/s2t2/seat-edit-rows.txt 2>&1
```

The second command reads the configured IMG_6702 and the sole corrected output
under that fresh test root, uses read_movie only, and prints only vide/soun
edit duration, media_time and rate. Its errors are fixed text without paths.
It does not print tags, track names, records or arbitrary exception text.
Supply those rows at the seat; do not infer missing duration/rate. DR-15
remains OPEN. No new DV footage test or real-file DV run is requested.

Then Reviewer B and the standard gate at the orchestrator's seat:
parallel `-n 4 -m "not gpu and not footage and not gui and not slow and not fullclip"`,
serial `-m "(gpu or footage or gui or slow) and not fullclip"`.
The gate also rechecks the three sandbox-only UNC nodes in their real environment.

## Turn 3 STOP resolved: phone record state versus required warnings

Orchestrator generation 24 ruled at turn 4 (FINAL unless CHARC overrides):
the phone record assertion requires `state == "done with warnings"`, exit 0,
the one expected MP4, and exactly the not-carried data-track warnings, including
`data track mebx`, with no other warning text. The warning count is asserted
exactly when deterministic. This follows CHARC Q2's required disclosure; the
brief's `done` means a successful item. No product behavior change is authorized.
The test is now authorized for implementation; it remains a seat-only run.

**[major, in-envelope, NEW, REASONED + EXECUTED]** Task 6 and the turn-3
dispatch require the runner record's item `done`. The existing product reports
a successful item with warnings as `done with warnings`. Q2 necessarily adds
warnings for the two omitted mebx tracks:

1. `verify.not_carried` emits `data track mebx` for each absent data track
   (`src/clearwater/io/video/verify.py:890-895`).
2. `ExportEngine` carries those into `JobResult.warnings` as
   `Not carried to the output: <item>`
   (`src/clearwater/jobs/export.py:1029-1033`, unchanged and NOT owned).
3. `BatchItem.state` returns `done with warnings` for `ok=True` and nonempty
   warnings (`src/clearwater/jobs/batch.py:37-44`, unchanged and NOT owned).
4. The runner writes `item.state` directly to the JSON record
   (`tools/headless_export.py:1050`) and accepts both successful states for
   exit 0 (`tools/headless_export.py:148`, `1134`).

Cheap reproduction, no footage or FFmpeg: constructed real `ExportRequest`,
`JobResult`, `BatchItem`, `BatchReport` and `he.RunRecord` values, then called
`he.record_object` and `he.exit_status`. The warning-free positive control
reports state `done`, exit 0. Adding only
`Not carried to the output: data track mebx` reports state
`done with warnings`, exit 0. Both assertions passed; EXIT 0.
Log: `work/wp4.4/t3/record-state-conflict.txt`. No record or metadata values
were printed; only the two states, warning counts and exit codes.

This is a brief/assertion conflict, not a new existing-test conflict. It is
raised under plan 4.5's no-assumptions rule before implementing the phone test.
Neither warning suppression nor batch/runner changes are in this package's
grant. The exact-state assertion received the ruling above at the turn-4 boundary.

## Turn 2 STOP resolved: qt PCM audio layout differs in V4

CHARC `093384f126589674` (2026-10-29T22:14:29Z) ruled (a): the qt fixture
becomes stereo pcm_s16le with `-ac 2`; the house V4 assertion is unchanged.
The fixture stays stereo. CHARC `9c8f461b73ec8c05` subsequently grants the
one-channel mono/absent-layout equivalence in compare.py, implemented in seat 2.
The original failure evidence below is retained; no mono-layout register row
opens. Product mux changes remain outside the grant; Q2 owns the data map only.

Seat PCM probe (FFmpeg 9.0.2, supplied at turn 3, script
`work/wp4.4-seat/pcm_layout.py`, stream copy to MP4): synthetic mono sowt with
layout mono becomes ipcm, one channel, layout absent; synthetic stereo sowt with
layout stereo becomes ipcm, two channels, stereo SAME; IMG_6702 lpcm is mono
with no layout in both source and output, SAME. The cell did not read footage
or rerun that seat probe.

The prospective MINOR row from `093384f126589674` is folded into the
`9c8f461b73ec8c05` comparison fix. The report records this as fixed; the cell
touches no register and no mono-layout row is due at the accept.

**[major, in-envelope, NEW, EXECUTED]**
`tests/test_wp44_mov_input.py::test_qt_mov_probe_decode_runner_and_v4` exports
successfully (runner exit 0, sole `clip_corrected.mp4`), but the MANDATORY item
`audio streams present` is DIFFERENT. The synthetic MOV reports pcm_s16le,
48000 Hz, one channel, `channel_layout=mono`; the output reports the same codec,
sample rate and channel count but no `channel_layout` field. All other MANDATORY
and REQUIRED items are SAME; the roster is present. This violates task 5's house
V4 requirement. Product changes outside the granted map are not authorized.

Root cause evidence, synthetic files only:

- `work/wp4.4/t2/qt-green.txt`: qt fixture/export test, 1 failed, EXIT 1.
- `work/wp4.4/t2/qt-audio-facts.txt`: independently read only codec/type/rate/
  channel/layout fields from source and product output with ffprobe, EXIT 0.
- `work/wp4.4/t2/qt-direct-copy-facts.txt`: plain FFmpeg stream copy from the
  same synthetic MOV to MP4, EXIT 0, reproduces the missing output layout.
  The direct copy bypasses correction, runner, product sink and the new data map.
- The comparator's `audio_layout` at
  `tools/container_spike/compare.py:1194-1209` includes `channel_layout` using
  `s.get(k)`, so `mono` versus an absent field makes this MANDATORY item DIFFERENT.
  No comparison code was changed.

Exact independent reproduction command (source/output are synthetic work files):

```bash
ffmpeg -nostdin -hide_banner -v error -y -i work/wp4.4/tmp/t2-qt-green/test_qt_mov_probe_decode_runne0/clip.MOV -map 0 -c copy -f mp4 work/wp4.4/t2/qt-direct-copy.mp4
```

**[minor, environment, NEW, EXECUTED]** Three existing runner tests fail in
`tests/test_headless_export.py:615`, inside `_unc_extended`, because the sandbox
token cannot access the localhost administrative share. Each raises
`PermissionError [WinError 5]` before it can exercise the intended product
assertion. The runner's `inside`, `plain_path`, and `Redactor` ASTs are unchanged
from `5e3537d`; no existing test or helper was altered to hide these failures.
Seat reproduction completed as recorded below. This is an environment failure, not an
additional conflicting test expectation.

Disposition at turn 3: CONFIRMED sandbox artifact. All three UNC nodes passed
at the orchestrator's seat (3 passed, EXIT 0;
`work/wp4.4/t2/seat-unc.txt`), using the exact requested command below.

**[minor, pre-existing encoding, REASONED + EXECUTED]** The inherited
`tests/test_gui_open.py` contains U+00E9 on base line 368 (current line 369).
All added lines are ASCII and the baseline non-ASCII sequence is unchanged.
Whole-blob ASCII conversion would exceed Q1's three permitted edits; it was not
performed. Dispatcher should resolve the literal whole-blob ASCII requirement
against this inherited test content. Evidence:
`work/wp4.4/t2/baseline-encoding.txt`, `work/wp4.4/t2/locks-final.txt`.

## Round 0: additional existing-test conflict, STOP resolved

CHARC `73d2797750c57625` (2026-10-29T21:59:13Z), brief commit `0b71bd3`,
GRANTED (a): the single fixture correction at
`tests/test_io_video_encode_units.py:80`, replacing the synthetic copied tag
`meta` with the proved HERO13 tag `gpmd`. Keep the map assertion at lines
365-372 unchanged. This line alone is now owned. Option (b), adding `meta`
to the allowlist, was DECLINED for lack of HERO13 evidence.

**[major, in-envelope, NEW, REASONED + EXECUTED]** Q2's gpmd-only
allowlist conflicts with that existing test. `_probe` supplies data streams
`tmcd` at index 2 and `meta` at index 3; the test requires maps
`["0:v:0", "1:1", "1:3"]`. The ruled filter must omit `meta`, producing
`["0:v:0", "1:1"]`. Adding `meta` to the allowlist would violate the grant:
it is not a proved HERO13 codec tag. Q1 authorizes no change to this file.
The turn-1 STOP for existing-test changes beyond Q1 was resolved by the grant
above. Product scope is unchanged.

Cheap reproduction on unchanged product code: `uv run python -` loaded the
existing unit module with `runpy.run_path`, called its `_command(_probe())`,
then called `_command` with a dataclass copy whose data tuple was filtered
to `gpmd`. No FFmpeg, footage, product mutation or test mutation was involved.
Output: `work/wp4.4/r0/allowlist-conflict.txt`; EXIT 0. Summary:

```text
BASE synthetic data tags: ['tmcd', 'meta']
BASE maps: ['0:v:0', '1:1', '1:3']
Q2 gpmd-only maps: ['0:v:0', '1:1']
CONFIRMED: Q2 conflicts with the existing meta-map assertion; no file was changed
```

## Dispatch and depth

Base: `5e3537d`, branch `wp4.4`; clean at entry. Product and tests remain
unchanged in turn 1. Protocol, APPLICATION, CLAUDE, prompting standard,
review/gate fill and the binding clauses have been read. This is a dispatched
implementer; the using-superpowers skill explicitly exempts dispatched agents.
The user-specified task ladder and yield schedule govern the work.

| Boundary | Dispatcher-supplied cell depth | Action |
|---|---|---|
| Turn 1 entry | Fresh session; no numeric depth supplied | Round 0 only |
| Turn 1 exit / turn 2 entry | 102,496 input tokens; window 475,000 (dispatcher reading) | Continue tasks 3-5; evaluate near 200K, stop at a boundary near 250K |
| Turn 2 exit / turn 3 entry | 163,747 input tokens; smaller reported window 258,400 binds | Bounded fixture/test turn, then dispatcher evaluation |
| Turn 3 exit / turn 4 entry | 189,237 input tokens; binding window 258,400 | Bounded test and run-request turn; fresh seat for report/reviews |
| Turn 4 exit | 206,634 input tokens; binding window 258,400 (dispatcher reading) | Seat 1 retired; seat 2 implements the Footage STOP GRANT |
| Seat 2 turn 1 entry | Fresh session; no numeric depth supplied | Granted comparator equivalences only, then yield for footage run/report |
| Seat 2 turn 1 yield / turn 2 entry | 151,726 input tokens; binding window 258,400, dispatcher footer reading | Bounded R1 cleanup, report and handoff; A converged |

The dispatch's Codex/Claude pace readings describe account usage, not this
cell's context depth; they are not substituted for a depth reading.

## Relocated anchors on 5e3537d

Every anchor in the brief's "The code today" is mapped below. Unchanged means
both line and described meaning hold. These are base references, before edits.

| Mechanic and surface | Base anchor | Change from brief |
|---|---|---|
| GUI `VIDEO_SUFFIXES` and its docstring | `src/clearwater/gui/sources.py:25-26` | Unchanged: MP4 only |
| GUI `file_filter` derives the video patterns | `src/clearwater/gui/sources.py:32-42`, especially 39 | Unchanged |
| GUI `route` lowercases and tests suffix membership | `src/clearwater/gui/sources.py:46-62`, especially 57-61 | Unchanged |
| GUI route callers | `src/clearwater/gui/shell.py:421`; `src/clearwater/gui/batch_panel.py:274` | Unchanged |
| Runner's separate suffix set and GUI pin docstring | `tools/headless_export.py:142-143` | Was 140-141; still MP4 only |
| Runner `route`, lowercase membership, refusal | `tools/headless_export.py:586-603`; refusal at 603 | Was 544-561; text unchanged |
| GUI-marked table/text equality pin | `tests/test_headless_export.py:114-122` (function 115) | Unchanged; leave intact |
| Naming `_base_plan` extension selection | `src/clearwater/jobs/naming.py:291-296` | Unchanged |
| DR-80 validation of the composed name | `src/clearwater/jobs/naming.py:297-305` | Unchanged; follows extension selection |
| Temporary marker and suffix of the final path | `src/clearwater/jobs/naming.py:28`; `119-130` | Unchanged |
| Naming rule docstrings | `src/clearwater/jobs/naming.py:317-318`, `329`, `386` | Unchanged |
| Probe's shared MOV/MP4 demuxer acceptance | `src/clearwater/io/video/probe.py:567-575`, check at 572 | Was 565-569; same meaning |
| Probe's HEVC/H.264 codec set | `src/clearwater/io/video/probe.py:65` | Was 64 |
| Probe's yuvj-capable pixel-format pattern | `src/clearwater/io/video/probe.py:66` | Was 65 |
| Sink maps video, every audio, non-tmcd data | `src/clearwater/io/video/encode.py:378-383` | Unchanged; Q2 edit point |
| Sink copies audio/data and forces MP4 | `src/clearwater/io/video/encode.py:422-425`, `436-437` | Unchanged |
| Best-effort `not_carried` data-track comparison | `src/clearwater/io/video/verify.py:866-903`, especially 890-899 | Was 862-897; same meaning |
| Prior report's unsupported data/audio limitation | `docs/reports/wp3.10-video-encode.md:385-387` | Unchanged; Q2 supersedes the mebx mapping behavior only |
| Product sink witness `encode_file` | `tools/video_fidelity.py:350-394` | Unchanged; bypasses suffix routing |
| V4 `fidelity_record` | `tools/video_fidelity.py:1251-1286` | Unchanged |
| House V4 assertion and roster item | `tests/test_wp42_video_path.py:373-385`; `tools/video_fidelity.py:148` | Unchanged |
| V4 neutral-pixel example (not required by Q3) | `tests/test_wp42_video_path.py:464-482` | Unchanged |
| Output-only MP4 requirement | `tools/container_spike/compare.py:1284-1289` | Unchanged |
| `container_kind` recognizes qt major brand | `tools/container_spike/compare.py:1023-1035` | Unchanged |
| ftyp brands are BEST-EFFORT | `tools/container_spike/compare.py:1403-1410` | Unchanged |
| Location-like values withheld before comparison | `tools/video_fidelity.py:46-50`, `151-155` | Brief cited 48-50 and 151; same meaning |
| Synthetic recipe `_ffmpeg`, `Clips.make` | `tests/test_io_video_encode.py:110-153` | Unchanged |
| Inventory's synthetic FFmpeg recipe | `tests/test_inventory.py:61-64` | Unchanged |
| Footage extension set and lookup | `tools/local_config.py:19`, `152-177` | Unchanged; MOV already included |
| Skip-only-when-absent helper | `tests/test_io_video_encode.py:1477-1488` | Unchanged |
| Collection-time footage skip | `tests/conftest.py:338-346` | Unchanged |

Additional binding anchors: Q1 naming assertion
`tests/test_jobs_naming.py:64-66`; GUI filter/routing rows
`tests/test_gui_open.py:93`, `109`; WP2.3 naming control
`tests/test_jobs_naming.py:508-528`. Spec 5.2 is at 213, 8.3 at 384,
D25 at 63, D105 at 143, V4 at 482-485; plan 4.5 is at 89-102.
The two-leg gate remains `docs/review-gate-clearwater.md:171-172`.

## RED roster for turns 2-3

Base for every prediction below is unchanged product code at `5e3537d`.
These are planned node IDs and failure predictions, NOT executed RED results.
Existing controls that already pass are identified as controls.
New tests use per-test `tmp_path`; only the phone export is footage-marked.

| File / node or parameter family | Expected base result |
|---|---|
| NEW `tests/test_wp44_mov_input.py::test_runner_routes_mov[a.mov]`, `[a.MOV]`, `[a.Mov]` | RED: runner returns refusal, expected `video` |
| NEW `test_runner_unknown_extension_refusal_is_unchanged` (`notes.txt`) | GREEN control: exact existing refusal text |
| EDIT `tests/test_gui_open.py::test_file_dialog_route_uses_the_injected_chooser` | RED: `*.mov` absent from filter |
| EDIT `test_routing_by_extension[a.mov-video]`, ADD `[a.MOV-video]` | RED: GUI returns refusal |
| EDIT `tests/test_jobs_naming.py::test_video_extension_case_is_preserved` (Q1's clip.mov row) | RED: `.mov` retained, expected `.mp4` |
| ADD `test_mp4_extension_case_is_preserved` (`clip.Mp4`) | GREEN control: mixed-case MP4 retained |
| ADD `test_mov_output_extension[final/plan-source-suffix]` with sources `IMG_6702.MOV`, `x.mov`, `x.Mov`, suffixes `_corrected`, `_fixed`, empty | RED through BOTH `final_output_path` and `plan_output`: expected lowercase `.mp4`; empty suffix uses a separate destination to isolate extension mapping |
| ADD `test_mov_and_mp4_share_collision_sequence` | RED: shared `Reservations` should give `_corrected.mp4` then `_corrected_2.mp4`; base plans MOV separately |
| ADD `test_mov_collision_uses_mapped_extension[final/temporary]` | RED: existing mapped final or its partial should force `_2.mp4`; base ignores the MP4 name |
| ADD `test_mov_temporary_path_uses_mp4` | RED: temporary of mapped final should end `.mp4` |
| ADD `test_mov_extension_stream_is_refused[final/plan]` (`x.mov:s`) | GREEN guard control: still raises `OutputNameError` |
| NEW `test_data_map_only_carries_proved_mp4_tags` | RED: synthetic unknown tag `zzzz` is currently mapped; include `gpmd` positive and `tmcd` exclusion controls; inspect real `encode_command`, no FFmpeg |
| NEW `test_qt_mov_probe_decode_runner_and_v4` | Probe/decode and fixture-shape controls expected GREEN; runner RED at `.MOV` routing. Assert qt major brand, HEVC with B-frames, PCM, 180-degree display matrix, full decoded count, exit 0, sole `clip_corrected.mp4`, V4 mandatory/required and roster SAME |
| NEW `test_phone_mov_runner_and_v4` (`footage`: reads owner footage) | RED: runner refuses MOV; even after suffix acceptance, base sink maps mebx and mux fails per Q2 seat evidence. Assert exit 0, sole `IMG_6702_corrected.mp4`, runner record item done, 15 frames, V4 roster and display-orientation item SAME |

The qt fixture is authored under `tmp_path` with lavfi testsrc2 192x144,
30 fps, 0.5 s, libx265 `bframes=2:log-level=error`, 48 kHz PCM s16le,
`-f mov`; apply 180-degree input display rotation on a stream-copy remux.
FFmpeg cannot author mebx per Q2: the phone test is that track's witness.
No synthetic mebx mux witness is claimed. Q3 requires no runner pixel bound.

Collection delta required by Q1: remove
`tests/test_gui_open.py::test_routing_by_extension[a.mov-refusal]`; add
`[a.mov-video]` and `[a.MOV-video]`. The existing naming node is retained
with its authorized changed expected extension; the new MP4-case node preserves
its former intent. Other existing tests remain unchanged, subject to the STOP.

## Q2 allowlist design and reporting path

Proposed constant: `MP4_DATA_CODEC_TAGS = frozenset({"gpmd"})`, beside the
data-map logic in `encode.py`. The map condition becomes
`data.codec_tag != TIMECODE_TAG and data.codec_tag in MP4_DATA_CODEC_TAGS`.
One command, one mux attempt; no retry and no codec probing for the choice.

The base map at `encode.py:381-383` is generic: it proves how a tag is mapped,
not which tags the owner's HERO13 actually has. The explicit roster is
`tests/test_io_video_probe_rules.py:117`: `{ "tmcd", "gpmd" }`.
`docs/reports/wp1.5-container-spike.md:198` identifies those same two data
stream tags; `docs/reports/wp3.10-video-encode.md:199` records gpmd SAME.
Thus `gpmd` is the sole copied allowlist member. `tmcd` remains excluded and
regenerated (`encode.py:430-431`; `verify.py:48` names `TIMECODE_TAG`).
No `meta` or `fdsc` codec tag is established by that HERO13 evidence.

The new unit test constructs a `ProbeResult` with gpmd, tmcd and synthetic
zzzz data streams, invokes public `encode_command` with libx265 and checks
the `-map` values, audio copy and deterministic exclusion. It needs neither
FFmpeg nor footage. The existing meta-based unit fixture has the one-token
grant above; its map assertion stays verbatim.

Grant condition checked in turn 2: the `meta` at
`tests/test_io_video_encode_units.py:753` is a `StreamRow` in the packet table
for `test_not_carried_lists_best_effort_items`. It is passed to
`verify.not_carried`, not to `encode_command`. That function compares the
source and output packet tables; the probe's data tuple does not choose their
tags. The row, its `data track meta` expectation, and all other lines in that
test remain unaffected by changing `_probe`'s map input at line 80.

No reporting change is needed: `FFmpegVideoSink` constructs its `SinkReport`
using `not_carried(probe, source, output)` at `encode.py:1096`.
`verify.not_carried` compares source/output non-timecode tracks at 890-899;
line 895 emits `data track <tag>` for an absent track. The two omitted mebx
streams will therefore be reported by that existing path as best-effort D105
items. Dropped Core Media tracks stay out of the output.

## RUN REQUEST: unchanged-base phone mux

Run at the orchestrator's seat BEFORE product edits (a ledger-only commit
does not alter the product base). Git Bash command from this worktree:

```bash
env -u VIRTUAL_ENV uv run python work/wp4.4/r0/round0.py > work/wp4.4/r0/round0-summary.txt 2>&1
```

Estimated scheduling allowance: 1-3 minutes, CPU only, not a timing figure.
Outputs stay under `work/wp4.4/r0/`; source lookup is exactly
`tools.local_config.find_footage_file("IMG_6702")`, no hard-coded footage path.
The script calls
`vf.encode_file(source, output, encoder="libx265", bit_depth=8)` and, if it
succeeds, `vf.fidelity_record(..., bit_depth=8, run=run)`.
It reports stream types/codecs/codec tags, script exit, encoder exit when
available, safe fixed diagnostic fragments, and DIFFERENT item NAMES by class.
It never writes the full fidelity record, prints source paths, or persists
arbitrary exception text or metadata. Non-format diagnostic text is withheld
explicitly rather than risk disclosing private values.

Observed at the orchestrator's seat on the unchanged base (reported at turn 2):
stage `encode`, `VideoEncodeError`, kind `encoder_failed`, script EXIT 1,
encoder exit 4294967274. Streams: video hevc/hvc1; audio pcm_s16le/lpcm;
two data mebx streams (codec_name null). Failure fragments:
`Could not find tag for codec none`, `codec not currently supported in container`,
`Could not write header`, `Invalid argument`,
`Nothing was written into output file`.
The record is `work/wp4.4/r0/round0-summary.txt`; comparison was not reached,
so DIFFERENT names are null, not an empty pass. This confirms the ruled Q2
failure; no new product-scope STOP arises from that seat result.
An unexpected failure or any MANDATORY/REQUIRED difference is a STOP to CHARC
through the dispatcher. The already-ruled mebx failure is baseline evidence.
Footage, GPU, network and heavy runs have NOT been executed by the cell.

## Validation and review record

| Turn / run | Command or artifact | Counts / outcome | EXIT |
|---|---|---|---|
| 1, cheap conflict reproduction | `uv run python -` (existing `_probe` / `_command`, in-memory filtered data) | One confirmed existing-test conflict; no FFmpeg or footage | 0 |
| 1, scratch-script lint | `uv run ruff check work/wp4.4/r0/round0.py` | All checks passed; `work/wp4.4/r0/ruff-script.txt` | 0 |
| 1, artifact check | `uv run python -` (AST parse, import without main, ledger byte check) | PASS: script imports without executing footage code; ledger ASCII/LF; `work/wp4.4/r0/artifact-check.txt` | 0 |
| Seat, round-0 witness (reported turn 2) | `env -u VIRTUAL_ENV uv run python work/wp4.4/r0/round0.py > work/wp4.4/r0/round0-summary.txt 2>&1` | encoder_failed on mebx; encoder exit 4294967274; no V4 comparison | 1 |

| Round | Critical / major / minor | In / out | NEW / REOPENED | Reverts | Product / test fixes | Reviewer / verdict | Depth |
|---|---|---|---|---|---|---|---|
| 0 (author mapping) | 0 / 1 / 0 | 1 / 0 | 1 / 0 | 0 | None / none | STOP resolved by grant 73d2797750c57625; Reviewer A not yet run | 102,496 at turn-1 yield |

Verification loop: suspected unlisted existing-test conflict; independently
confirmed by fixture/expectation trace and command-construction reproduction;
not fixed in turn 1 because unowned, then granted at the turn boundary.
No rejected false positives. Round 0 ended at its mandatory yield.

## Turn 2 build record (tasks 3-5)

### Changes within the grants

- Both suffix sets accept MOV case-insensitively and their docstrings cite
  spec 5.2 (0.5.7). Q1's GUI filter and routing rows are changed exactly.
  The existing GUI/runner equality test is unchanged and passed.
- `_base_plan` maps exactly the case-insensitive `.mov` extension to `.mp4`,
  before the existing portable-name guard. Photo and other video extensions,
  collision numbering, reservations, partial marker and source guard are intact.
  Three naming docstring locations now state the rule. New tests cover both
  planners, suffix overrides, same-folder empty suffix, shared MOV/MP4 naming,
  disk/partial collisions, mapped partial names and the `x.mov:s` refusal.
- `MP4_DATA_CODEC_TAGS = frozenset({"gpmd"})` and its docstring are the only
  added encode constant; the only changed encode logic is the deterministic
  data-map membership condition beside the tmcd exclusion. No mux retry.
  The synthetic-tag unit exercises gpmd copied, tmcd excluded, zzzz excluded,
  audio/data stream-copy and one command list with two inputs.
- CHARC grant `73d2797750c57625`: only
  `tests/test_io_video_encode_units.py:80` changes meta to gpmd. The original
  map assertion (365-372) and packet-table row 753 are verbatim against base.
  The entire unit file differs by exactly the granted token; its 80 tests pass.
- The test-local qt fixture authors 192x144, 30 fps, 15-frame HEVC with
  B-frames and 48 kHz PCM s16le, then applies a 180-degree display rotation on
  remux to `clip.MOV`. Its qt brand, B-frames, display matrix, PCM facts,
  probe and full decode checks passed. The runner then exports, but V4 exposes
  the audio-layout STOP above. This test was written before suffix changes,
  and its initial RED was the base runner's MOV refusal.

No footage test or final report was written this turn. No footage was accessed
by the cell. No dependency, frozen interface, local config, register or other
worktree was changed. All generated media and runner logs stay in `work/wp4.4/`.

### RED/GREEN node identities

Routing RED on unchanged product code (`routing-red2.txt`):

```text
tests/test_wp44_mov_input.py::test_runner_routes_mov[a.mov]
tests/test_wp44_mov_input.py::test_runner_routes_mov[a.MOV]
tests/test_wp44_mov_input.py::test_runner_routes_mov[a.Mov]
tests/test_wp44_mov_input.py::test_qt_mov_probe_decode_runner_and_v4
tests/test_gui_open.py::test_file_dialog_route_uses_the_injected_chooser
tests/test_gui_open.py::test_routing_by_extension[a.mov-video]
tests/test_gui_open.py::test_routing_by_extension[a.MOV-video]
```

Failures were MOV refusal / absent `*.mov`; 7 failed, 14 passed, EXIT 1.
The first attempt (`routing-red.txt`) had 5 failed, 14 passed, 2 setup errors
because the new nested basetemp parent did not exist. Creating the legitimate
work-local parent allowed a fresh-basetemp rerun; no sandbox workaround.
After the suffix edit, all routing nodes plus the unchanged equality pin pass:
21 passed, 1 qt node deselected, EXIT 0 (`routing-green.txt`).

Naming RED on unchanged naming code (`naming-red.txt`):

```text
tests/test_jobs_naming.py::test_video_extension_case_is_preserved
tests/test_jobs_naming.py::test_mov_output_extension[<folder>-<suffix>-<name>-<planner>]
tests/test_jobs_naming.py::test_mov_and_mp4_share_collision_sequence
tests/test_jobs_naming.py::test_mov_collision_uses_mapped_extension[final]
tests/test_jobs_naming.py::test_mov_collision_uses_mapped_extension[temporary]
tests/test_jobs_naming.py::test_mov_temporary_path_uses_mp4[final]
tests/test_jobs_naming.py::test_mov_temporary_path_uses_mp4[plan]
```

The parameter-family row denotes these exact 36 node IDs, the Cartesian product
in the order displayed: folder = `out`, `beside`; suffix = `default`, `edited`,
`empty`; name = `IMG_6702.MOV`, `x.mov`, `x.Mov`; planner = `final`, `plan`.
All 42 failing nodes retained MOV extensions (or selected the old source-guard
number) rather than the mapped MP4 names; 4 controls passed, 819 deselected,
EXIT 1. After the extension rule: the entire naming file, including every
unchanged WP2.3 control, passed: 865 passed, EXIT 0 (`naming-green.txt`).

Allowlist RED on unchanged encode code (`map-red.txt`):
`tests/test_wp44_mov_input.py::test_data_map_only_carries_proved_mp4_tags`
failed because `1:4` (zzzz) was included; the existing map and not_carried
controls passed: 1 failed, 2 passed, EXIT 1. After the map and one-token grant:
81 passed, EXIT 0 (`map-green.txt`, new unit plus entire encode unit file).

The qt node's latest RED is the MANDATORY audio-layout STOP, not the initial
suffix failure. It was not weakened. All fixture-shape assertions and the
real export complete before that failure.

### Commands and outcomes

Every pytest command below uses `PYTHONPATH=scripts`,
`-p sandbox_mkdir_shim -p no:cacheprovider`, and a fresh
`--basetemp=work/wp4.4/tmp/<run>`; GUI runs also set
`QT_QPA_PLATFORM=offscreen`. VIRTUAL_ENV is removed in each process.
Logs are `work/wp4.4/t2/<log>.txt`.

| Run / log | Command targets and selection | Counts / result | EXIT |
|---|---|---|---|
| routing-red | `uv run pytest -q tests/test_wp44_mov_input.py tests/test_gui_open.py::test_file_dialog_route_uses_the_injected_chooser tests/test_gui_open.py::test_routing_by_extension -m "not gpu and not footage and not slow and not fullclip"` | 5 failed / 14 passed / 2 setup errors, absent basetemp parent | 1 |
| routing-red2 | Same targets/selection, fresh root | 7 failed / 14 passed, expected routing RED including qt node | 1 |
| routing-green | Same targets plus `tests/test_headless_export.py::test_the_routing_tables_and_texts_equal_the_interfaces`, `-k "not qt_mov_probe_decode_runner_and_v4"` | 21 passed / 1 deselected | 0 |
| naming-red | `uv run pytest -q tests/test_jobs_naming.py -k "mov or extension_case_is_preserved"` | 42 failed / 4 passed / 819 deselected | 1 |
| naming-green | `uv run pytest -q tests/test_jobs_naming.py -m "not gpu and not footage and not gui and not slow and not fullclip"` | 865 passed | 0 |
| map-red | `uv run pytest -q tests/test_wp44_mov_input.py::test_data_map_only_carries_proved_mp4_tags tests/test_io_video_encode_units.py::test_the_map_copies_audio_and_data_but_not_the_timecode_track tests/test_io_video_encode_units.py::test_not_carried_lists_best_effort_items` | 1 failed / 2 passed | 1 |
| map-green | `uv run pytest -q tests/test_wp44_mov_input.py::test_data_map_only_carries_proved_mp4_tags tests/test_io_video_encode_units.py -m "not gpu and not footage and not gui and not slow and not fullclip"` | 81 passed | 0 |
| qt-green (attempt) | `uv run pytest -q tests/test_wp44_mov_input.py::test_qt_mov_probe_decode_runner_and_v4` | 1 failed: audio streams present DIFFERENT | 1 |
| light | `uv run pytest -q tests/test_wp44_mov_input.py tests/test_jobs_naming.py tests/test_headless_export.py tests/test_io_video_encode_units.py -m "not gpu and not footage and not gui and not slow and not fullclip"` | 1020 passed / 4 failed / 1 deselected | 1 |
| gui | `uv run pytest -q tests/test_gui_open.py` | 31 passed | 0 |
| ruff | `uv run ruff check .` | All checks passed | 0 |
| ruff-final | `uv run ruff check .` (after test-only layout cleanup) | All checks passed | 0 |
| mypy | `uv run mypy` | Success: no issues in 141 source files | 0 |
| wp44-final | `uv run pytest -q tests/test_wp44_mov_input.py -m "not gpu and not footage and not gui and not slow and not fullclip"` | 5 passed / 1 failed, same MANDATORY audio-layout difference | 1 |
| diff-check | `git -c core.autocrlf=false diff --check` | No whitespace errors | 0 |
| locks (initial) | `uv run python -` (whole-artifact ASCII check) | Found pre-existing U+00E9 in GUI test, not introduced | 1 |
| locks-final | `uv run python -` (added-line ASCII, granted-token diff and AST comparisons) | PASS, including verbatim map assertion and line 753 | 0 |
| qt-audio-facts | `uv run python -` (restricted ffprobe format fields) | Confirmed source mono versus absent output layout | 0 |
| qt-direct-copy-facts | `uv run python -` (plain FFmpeg copy plus same ffprobe fields) | Reproduces missing layout without product path | 0 |

The four failed nodes in the light run are exactly:

```text
tests/test_wp44_mov_input.py::test_qt_mov_probe_decode_runner_and_v4
tests/test_headless_export.py::test_g1_inside_sees_every_spelling_of_the_same_folder
tests/test_headless_export.py::test_g1_main_refuses_every_footage_check_through_another_spelling[unc]
tests/test_headless_export.py::test_g1_the_redactor_hides_the_extended_spellings
```

No full-suite, footage, GPU, network, fullclip or heavy benchmark was requested
directly by the cell. The existing UNC helper attempted its administrative-share
access during the authorized light run and failed; no network workaround was
attempted. Ruff format checking remains at the dispatcher's seat as instructed.

### Seat RUN REQUESTS

The following three-node seat request was completed at the turn-3 boundary:
3 passed, EXIT 0 (`work/wp4.4/t2/seat-unc.txt`), confirming the restricted-token
artifact. The command was (Git Bash):

```bash
env -u VIRTUAL_ENV uv run pytest -q tests/test_headless_export.py::test_g1_inside_sees_every_spelling_of_the_same_folder 'tests/test_headless_export.py::test_g1_main_refuses_every_footage_check_through_another_spelling[unc]' tests/test_headless_export.py::test_g1_the_redactor_hides_the_extended_spellings --basetemp=work/wp4.4/t2-seat-unc > work/wp4.4/t2/seat-unc.txt 2>&1
```

The following seat format check identified two files needing formatting:
`src/clearwater/jobs/naming.py` and `tests/test_wp44_mov_input.py`. The
orchestrator applied mechanical formatting before commit `35391b0`, with no
semantic changes, and reported ruff check clean. Both files were re-read on
disk before turn-3 edits. The check's log is `work/wp4.4/t2/seat-format.txt`;
its numeric exit was not supplied.

```bash
env -u VIRTUAL_ENV uv run ruff format --check . > work/wp4.4/t2/seat-format.txt 2>&1
```

Reviewer A has not run; no convergence or package-completion claim is made.

| Round / boundary | Critical / major / minor | In / environment or pre-existing | NEW / REOPENED | Reverts | Product / test fixes | Verdict | Depth |
|---|---|---|---|---|---|---|---|
| Turn 2 author verification (not Reviewer A) | 0 / 1 / 2 | 1 / 2 | 3 / 0 | 0 | Routing, naming, data map / RED tests and granted fixture token | qt STOP resolved by 093384f126589674; UNC artifact confirmed at seat | 163,747 at turn-2 yield |

Verification-loop record: resolved the granted round-0 test conflict; confirmed
the new qt audio difference independently with plain FFmpeg; confirmed UNC
failures originate in the unchanged test helper before product assertions;
confirmed non-ASCII is inherited rather than introduced. No false-positive
rejections, no reverts, and no fix to the unowned audio-mux/instrument surface.

## Turn 3 build and validation record

Applied CHARC `093384f126589674` only in the owned test file: the qt fixture
now requests `-ac 2`, and its self-check requires two channels and stereo
layout. The house `_assert_v4` helper and every V4 requirement are unchanged.
The qt node passes; the turn-2 MANDATORY difference is resolved for the ruled
fixture. The inherited declared-mono limitation remains CHARC's register item
at the accept. No register was edited.

Footage task 6 was investigated but not implemented, because its literal record
state conflicts with required warnings as confirmed in the new STOP above.
No footage was read; no footage test was run or silently skipped. A footage
RUN REQUEST cannot yet name a runnable node, so it is deferred until that
assertion is ruled. No report was written this turn.

Commands below ran with VIRTUAL_ENV removed. Each pytest invocation used
`PYTHONPATH=scripts`, `-p sandbox_mkdir_shim -p no:cacheprovider`, and the fresh
basetemp shown. Logs are under `work/wp4.4/t3/`.

| Run / log | Exact command or probe | Counts / result | EXIT |
|---|---|---|---|
| qt-green.txt | `uv run pytest -q tests/test_wp44_mov_input.py::test_qt_mov_probe_decode_runner_and_v4 --basetemp=work/wp4.4/tmp/t3-qt-green -p sandbox_mkdir_shim -p no:cacheprovider` | 1 passed; qt/stereo/rotation/full decode/export/V4 checks passed | 0 |
| record-state-conflict.txt | `uv run python -` constructing successful real batch/runner records with zero and one data-track warning | `done` / `done with warnings`, both exit 0; two assertions passed | 0 |
| light.txt | `uv run pytest -q tests/test_wp44_mov_input.py tests/test_jobs_naming.py tests/test_headless_export.py tests/test_io_video_encode_units.py --basetemp=work/wp4.4/tmp/t3-light -p sandbox_mkdir_shim -p no:cacheprovider -m "not gpu and not footage and not gui and not slow and not fullclip"` | 1021 passed / 3 failed / 1 deselected; only the known UNC helper failures | 1 |
| ruff.txt | `uv run ruff check .` | All checks passed | 0 |
| mypy.txt | `uv run mypy` | Success: no issues in 141 source files | 0 |
| diff-check.txt | `git -c core.autocrlf=false diff --check` | No whitespace errors | 0 |
| locks.txt | `uv run python -` comparing `_assert_v4` AST to 35391b0 and checking both modified files' encoding | House helper unchanged; both files ASCII | 0 |

The three light-run failures remain exactly the UNC nodes listed in turn 2.
They passed at the seat; no test was changed, masked, or skipped by the cell.
Only `tests/test_wp44_mov_input.py` and this ledger changed during turn 3.
All added text is ASCII; product code, frozen interfaces, dependencies, local
configuration, the register and all other worktrees remain unchanged.

| Boundary (not Reviewer A) | Critical / major / minor | In / out | NEW / REOPENED | Reverts | Product / test fixes | Verdict | Depth |
|---|---|---|---|---|---|---|---|
| Turn 3 author verification | 0 / 1 / 0 | 1 / 0 | 1 / 0 | 0 | None / ruled stereo fixture, with layout self-check | STOP resolved by orchestrator gen 24's turn-4 ruling; no footage access | 189,237 at turn-3 yield; binding window 258,400 |

Verification-loop record: applied the ruled stereo fixture and confirmed V4
passes; discovered the phone-state requirement conflict while tracing its
record schema; independently confirmed the warning-free and warned states using
real serializer calls. No false positives, no reverts, no out-of-scope fix.
Reviewer A has not run. Yielding at the bounded turn's boundary for the
dispatcher's depth evaluation and ruling; no package-completion claim.

## Turn 4 test, validation and handoff record

Applied the turn-4 orchestrator ruling without product changes. Added
`tests/test_wp44_mov_input.py::test_phone_mov_runner_and_v4`, the file's ONE
footage-marked node, with the reason beside its marker. `_phone_mov` uses
local_config and the established skip-only-when-absent pattern: ambiguity,
search errors and invalid roots are not silently skipped. The node runs the
CPU libx265 runner with `--record`; all output/cache/record paths are under
tmp_path. It checks exit 0, the sole expected MP4, successful-with-warnings
record state, exactly two expected mebx omission notices, house V4, source and
output frame counts 15, and the explicitly named display orientation SAME.

Deterministic count proof: verify.py:890-895 enumerates each non-timecode
source data stream and appends once if missing. Both mebx tracks are absent
from the gpmd-only output, so it appends `data track mebx` twice, without
deduplication. export.py:1031-1033 prefixes both entries once. The test requires
two total warnings and two exact expected entries, leaving no other text.
Prefix and count checks use precomputed booleans/integers so failures do not
print arbitrary warnings. The record, source tags and fidelity record are
never printed. The runner's captured stdout/stderr is discarded before
assertions; assertions expose output names, states, counts and V4 item names.

No footage execution was performed by the cell, including no manual call to
the lookup helper. No footage result is claimed. The seat command is in
RESUME HERE; any new MANDATORY/REQUIRED difference is STOP. No report or
register change was made. Product files, prior tests, frozen interfaces,
dependencies, configuration and all other worktrees remain unchanged.

At entry, the orchestrator supplied clean ruff format (272 files), clean ruff
check and zero CR at `e4141f8`. Current cell runs remove VIRTUAL_ENV; pytest
sets `PYTHONPATH=scripts`. All logs are in `work/wp4.4/t4/`.

| Run / log | Exact command or check | Counts / outcome | EXIT |
|---|---|---|---|
| light.txt | `uv run pytest -q tests/test_wp44_mov_input.py --basetemp=work/wp4.4/tmp/t4-light -p sandbox_mkdir_shim -p no:cacheprovider -m "not footage and not gpu and not gui and not slow and not fullclip"` | 6 passed, 1 footage node deselected | 0 |
| ruff.txt | `uv run ruff check .` | All checks passed | 0 |
| mypy.txt | `uv run mypy` | Success: no issues in 141 source files | 0 |
| diff-check.txt | `git -c core.autocrlf=false diff --check` | No whitespace errors | 0 |
| seat-footage.txt | Git Bash phone-node request in the turn-4 handoff | Seat supplied: 1 failed in 59.4 s, V4-only failure; see seat-2 grant record below | 1 |
| locks.txt | `uv run python -` (AST and byte checks, without importing or executing the test) | Both modified files ASCII/LF; house helper unchanged; exactly one footage node | 0 |

Verification-loop record: traced the fixed warning count against the unchanged
verify/export code; checked that state and warning assertions implement the
new ruling; ran the non-footage node selection to green without executing the
new marker; no new suspect, confirmed defect, false positive or revert.
Reviewer A has not run. Handoff is to a fresh seat after this bounded turn.

| Boundary (not Reviewer A) | Critical / major / minor | In / out | NEW / REOPENED | Reverts | Product / test fixes | Verdict | Depth |
|---|---|---|---|---|---|---|---|
| Turn 4 author verification | 0 / 0 / 0 | 0 / 0 | 0 / 0 | 0 | None / ruled phone test written | Seat footage STOP resolved by 9c8f461b73ec8c05; fresh seat implements grant | 206,634 / 258,400 at yield |

## Turn-4 seat footage evidence and Footage STOP GRANT

Dispatcher-supplied evidence, not a cell footage run: the phone node at
`c353dfd` returned 1 failed in 59.4 s, EXIT 1. The runner itself returned 0,
wrote the sole expected output, and recorded done with warnings with exactly
two data track mebx omissions. V4 differed on the two MANDATORY orientation
items (ffprobe display matrix and tkhd matrix) and REQUIRED frame size/SAR.

The seat's restricted format probe showed rotation -180 on both sides and
identical linear matrix entries. The source translation row was
`[125829120, 94371840]`, the output `[0, 0]`; size was 1920x1440 on both
sides, source SAR unset/null and output 1:1. These are supplied format facts,
not cell observations, timing benchmarks or private metadata values.

CHARC `9c8f461b73ec8c05` granted exactly the three instrument equivalences
listed in RESUME HERE and no product mux change. The earlier declared-mono
MINOR-register proposal is folded into the third fix; no register row opens.
The footprint additionally owns compare.py and a NEW synthetic test file;
the report/accept record must name this grant. Prior prohibitions in the
historical turn-2 record describe that earlier ruling, not the current grant.

## Seat 2 turn 1 build and validation record

Entry HEAD `af4ccc0`, branch wp4.4, empty git status. Read the dispatch
protocol, APPLICATION, CLAUDE, prompting standard and review/gate fill; the
dispatched-implementer exemption in using-superpowers applies. No agent was
spawned, no review round was run and no footage was read or tested here.

Relocated comparison anchors on entry: audio_layout 1194-1201 and its item
1203-1213; ffprobe orientation 1250-1256; tkhd orientation 1263-1268;
frame size/SAR 1308-1312. On this turn's candidate, matrix parsing/linear/note
helpers are 882/899/904, normalized ffprobe rotation 911, audio_layout 1229,
orientation item names 1289/1303 and geometry normalization 1351/1358.

Implemented only the granted equivalences in compare.py:

- Valid ffprobe matrix text is parsed as three labelled integer rows. Both
  orientation items compare the 2x2 linear entries; the ffprobe item also
  compares rotation. Translation terms appear in each item's BEST-EFFORT
  note, outside equality comparison. Unparseable ffprobe text stays exact.
- Only absent/null SAR normalizes to 1:1; width and height remain exact.
- Only absent/null channel_layout at channels == 1 normalizes to mono.
  Channel counts, other layouts, codec, profile and sample rate stay exact.

The qt fixture remains stereo, unchanged: retain its existing integration
witness and cover the mono equivalence directly with synthetic facts. No
existing test file changed. All new tests use synthetic Facts/probe dicts
and never invoke FFmpeg or read a file. The real phone witness is requested
at the seat; no pass is claimed before it arrives.

### RED/GREEN and controls

RED on unchanged compare.py at af4ccc0: 12 failed, 15 passed, EXIT 1.
All failing IDs use the prefix
`tests/test_container_spike_compare_equivalences.py::`:

```text
test_translation_is_equivalent[forward-side]
test_translation_is_equivalent[forward-tkhd]
test_translation_is_equivalent[reverse-side]
test_translation_is_equivalent[reverse-tkhd]
test_unset_square_sar_is_equivalent[forward-absent]
test_unset_square_sar_is_equivalent[forward-null]
test_unset_square_sar_is_equivalent[reverse-absent]
test_unset_square_sar_is_equivalent[reverse-null]
test_unset_mono_layout_is_equivalent[forward-absent]
test_unset_mono_layout_is_equivalent[forward-null]
test_unset_mono_layout_is_equivalent[reverse-absent]
test_unset_mono_layout_is_equivalent[reverse-null]
```

GREEN after the three changes: all 27 passed, EXIT 0. Named control run
before the change: 14 passed / 13 deselected, EXIT 0. The same 14 controls
also pass in the full verbose GREEN run, each asserting DIFFERENT:

```text
test_orientation_change_control[quarter-side]
test_orientation_change_control[quarter-tkhd]
test_orientation_change_control[mirror-side]
test_orientation_change_control[mirror-tkhd]
test_ffprobe_rotation_change_control
test_geometry_change_control[nonsquare]
test_geometry_change_control[width]
test_geometry_change_control[height]
test_audio_change_control[channels]
test_audio_change_control[stereo-5.1]
test_audio_change_control[stereo-absent]
test_audio_change_control[mono-stereo]
test_audio_change_control[rate]
test_audio_change_control[codec]
```

The stereo-versus-5.1 control deliberately holds channel count constant to
isolate layout comparison; the separate channel-count control catches 1 vs 2.
The scaffold self-comparison passes on both versions, every item SAME.
No translation equality is asserted by any test.

### Commands and outcomes

All logs are work-local under `work/wp4.4/s2t1/`. Runner output is routed to
files; only summaries enter the return. VIRTUAL_ENV is removed; every pytest
command sets PYTHONPATH=scripts and uses the sandbox shim/no-cacheprovider.
Marker expression is `not gpu and not footage and not gui and not slow and
not fullclip` unless a narrower test-only control selection is stated.

The broader light targets are tests/test_wp44_mov_input.py,
tests/test_container_spike.py, tests/test_container_spike_compare_equivalences.py,
tests/test_wp42_video_path.py, tests/test_prototype_clip.py,
tests/test_video_fidelity.py, tests/test_jobs_export_video.py and
tests/test_io_video_encode.py. This is every file importing container_spike
compare, confirmed by rg, including the new file; no unrelated suite is run.

| Log | Command (pytest also uses `-p sandbox_mkdir_shim -p no:cacheprovider`) | Result | EXIT |
|---|---|---|---|
| red.txt | `uv run pytest -q tests/test_container_spike_compare_equivalences.py --basetemp=work/wp4.4/tmp/s2t1-red -m "not gpu and not footage and not gui and not slow and not fullclip"` | 12 failed / 15 passed, expected equivalence RED | 1 |
| controls-before.txt | `uv run pytest -v tests/test_container_spike_compare_equivalences.py -k control --basetemp=work/wp4.4/tmp/s2t1-controls-before` | 14 passed / 13 deselected; DIFFERENT controls retained | 0 |
| green.txt | `uv run pytest -v tests/test_container_spike_compare_equivalences.py --basetemp=work/wp4.4/tmp/s2t1-green -m "not gpu and not footage and not gui and not slow and not fullclip"` | 27 passed | 0 |
| ruff.txt | `uv run ruff check .` | All checks passed | 0 |
| mypy.txt | `uv run mypy` | Success: no issues in 141 source files | 0 |
| format.txt | `uv run ruff format tools/container_spike/compare.py tests/test_container_spike_compare_equivalences.py` | 2 owned files reformatted; whole-tree format check remains at seat | 0 |
| disk.txt | `uv run python -c` with shutil.disk_usage('.') before the fixture run | 178.4 GiB free; no prune performed | 0 |
| light.txt | Broad pytest target list with literal `tests/test_container_spike*.py` | PowerShell did not expand wildcard; pytest found no matching file, no tests executed | 4 |
| light-expanded.txt | Broad pytest target list above, `-q -rs --basetemp=work/wp4.4/tmp/s2t1-light-expanded` and marker expression above | Collection stalled; no basetemp/test execution; only identified pytest process terminated | -1 (tool termination) |
| light-verbose.txt | Same targets/markers, `-v -rs --basetemp=work/wp4.4/tmp/s2t1-light-verbose -o faulthandler_timeout=60`, unbuffered output | Again stalled during collection, no basetemp; only identified pytest process terminated | -1 (tool termination) |
| prototype-import.txt | `uv run python -u -c` with runpy.run_path on test_prototype_clip.py and a 20 s traceback alarm | Import completed; isolated import does not reproduce pytest's stall | 0 |
| import-order.txt | `uv run python -u -` importing all eight target modules in order using runpy, 20 s alarm | All eight imports completed; not a pytest/test result | 0 |
| collection-probe.txt | `uv run python -u -` with pytest.main, all eight targets, collect-only, shim, marker expression, fresh s2t1-collect-probe basetemp, 20 s alarm | Bounded diagnostic exited but captured no traceback; no test result claimed | 1 |
| collection-stack.txt / collection-stack-run.txt | Same collect-only diagnostic with fresh s2t1-collect-stack basetemp, 10 s faulthandler alarm writing directly to a work-local file | Reproduces stall in tempfile._mkstemp_inner from CuPy cache save during test_prototype_clip.py import | 1 |
| light-remaining.txt | `uv run pytest -q -rs` on the same target list EXCEPT test_prototype_clip.py, same markers/shim, `--basetemp=work/wp4.4/tmp/s2t1-light-remaining` | 250 passed / 35 deselected; deferred file remains a named seat RUN REQUEST | 0 |
| remaining-collect.txt | `uv run pytest --collect-only -q` on those seven targets, same markers/shim, `--basetemp=work/wp4.4/tmp/s2t1-remaining-collect` | 250/285 nodes selected, 35 deselected; matches execution counts | 0 |
| diff-check.txt | `git -c core.autocrlf=false diff --check` | No whitespace errors before ledger update | 0 |
| ruff-final.txt | `uv run ruff check .` after formatting | All checks passed | 0 |
| locks.txt | `uv run python -` checking git path set, ASCII/LF and top-level comparator AST changes | Exactly three owned paths; all ASCII/LF; other functions/classes unchanged | 0 |
| locks-final.txt | `uv run python -` checking final git path set, byte encoding and public/module docstrings | Exactly three owned paths; ASCII/LF; docstrings present | 0 |
| diff-check-final.txt | `git -c core.autocrlf=false diff --check` after ledger finalization | No whitespace errors | 0 |

Verification-loop record: confirmed the three equivalences RED through the
actual shared compare_facts entry point; checked every mandated planted
difference remains DIFFERENT before/after; retained unparseable side-matrix
text comparison rather than treating it as equivalent. Corrected the wildcard
invocation by spelling out its two files, without changing markers or tests.
No new comparator defect, out-of-envelope fix or revert. The
scope check confirms only compare.py, the NEW test file and this ledger
changed; no existing test, product module, frozen interface, dependency,
config or register was edited. All three changed files are ASCII/LF.
The broad light run's final outcome is recorded in the table before yield.

| Boundary (not Reviewer A) | Critical / major / minor | In / out | NEW / REOPENED | Reverts | Product / test fixes | Verdict | Depth |
|---|---|---|---|---|---|---|---|
| Seat 2 turn 1 author verification | 0 / 0 / 1 new environment finding | 0 / 1 | 1 / 0 | 0 | Three granted shared-instrument equivalences / 27 new synthetic nodes | 250 passed / 35 deselected in available light selection; prototype importer and phone seat RUN REQUESTS pending; report next turn | Fresh seat; numeric exit depth pending dispatcher |

Reviewer A rounds: none yet; driver supplies findings between turns. Reviewer
B and the ONE two-leg gate remain pending at the seat. This turn is the
single logical compare.py GRANT, with its tests/evidence, not completion of
the whole package. No test node was removed or renamed during this turn.

### Environment finding and verification-loop disposition

**[minor, environment, NEW, EXECUTED]** The requested eight-file light run
stalls during collection before any test/temp fixture. A bounded independent
collect-only probe writes a traceback directly to work-local
collection-stack.txt: test_prototype_clip.py:41 calls select_backend("auto"),
prototype/backend.py:211 calls cupy.arange, CuPy compiler cache save enters
NamedTemporaryFile and remains in tempfile._mkstemp_inner. CUDA/NVRTC modules
were loaded in the first stalled pytest process. CUPY_CACHE_DIR is unset;
the installed CuPy _compiler_cache.py:89-93 documents/selects its default
home-directory cache, and :140 creates the temporary file there, outside the
writable workspace. No successful external write was observed or is claimed. No cache
relocation or permission workaround was attempted. This is an unchanged
module-level GPU probe, not a comparator regression or an executed GPU test.

The first hypothesis (the isolated module import itself always hangs) was
rejected by both runpy probes, which finish. The actual pytest collection
stall is independently reproduced by the work-file traceback. Termination
targeted only each identified pytest interpreter, checking its PID and exact
start time; no other process or file was removed. The two terminated runs
have no test counts and are not passing evidence. The traceback alarms are
diagnostic ceilings, not product timing assertions or performance figures.

Disposition: COMMISSIONED WP4.4 seat RUN REQUEST for unchanged
test_prototype_clip.py with the same non-heavy marker expression; the seven
remaining importer files passed here (250 passed / 35 deselected, EXIT 0).
No existing test is masked/edited, no marker changed, no dependency added.
No product fix or CHARC scope extension is requested for this environment
finding. The full package gate still belongs to the orchestrator's seat.

## Seat 2 turn 2 -- Reviewer A R1 cleanup and report

Read the allowed R1 finding file `clearwater-review-evidence/wp4.4/r1/review.txt`
in full. Reviewer: Claude pass, opus/high, read-only, run by the dispatcher.
Transport is the dispatcher's codex_cell review/Claude process lane; exact
CLI build/version was not supplied and is not invented here. Verdict supplied
by reviewer/dispatcher: NO_NEW_CRITICAL_MAJOR, converged. This is the first
Reviewer A round; author/environment rows above are not reviewer rounds.

### Cumulative Reviewer A round ledger

| Round | Critical / major / minor / advisory | In / out | NEW / REOPENED | Reverts | Product-code / test-only fixes | Verdict | Depth |
|---|---|---|---|---|---|---|---|
| R1 | 0 / 0 / 4 / 5 | 8 / 1 | 9 / 0 | 0 | F1 non-translation projection; F3/F6 docs/comments only / F4 note tests, F9 capture cleanup; four additionally commissioned naming controls | NO_NEW_CRITICAL_MAJOR, converged; authorized terminating cleanup applied | 151,726 / 258,400 at prior yield, supplied this dispatch |

All findings are NEW, none reopened. Finding 2 is outside the authorized
remediation surface; all other dispositions are in envelope, including
finding 7's requested documentation-only disposition.
No revert, relaxed assertion, hidden marker or retry was used. No new round
or five-round continuation gate is due. B/gate/accept stay pending at seat.

### Every R1 finding and disposition

1. **MINOR, confirmed/fixed, in envelope.** `_matrix_linear` excluded
   perspective u/v and homogeneous w as well as translation. Four synthetic
   controls proved the error at d427dc9: doubled w index 8 and nonzero u/v
   indices 2/5 each read SAME on both orientation items. RED ids below.
   Retain indices (0,1,2,3,4,5,8), excluding ONLY 6/7. This narrows the
   existing equivalence under 9c8f461b73ec8c05; no new comparison behavior
   beyond the dispatched fix. GREEN confirms all four DIFFERENT.
2. **MINOR, confirmed, out of envelope; report limit.** Positional
   verify.py data pairing may falsely warn gpmd in [mebx,gpmd] -> [gpmd].
   No owner source has the mix. CHARC fd2269acf257054d Q-B(a) owns any
   register row at accept. No verify.py or register change.
3. **MINOR, confirmed/fixed, in envelope.** encode.py module and write
   docstrings still promised all non-timecode data. Corrected only those
   two statements under fd2269acf257054d (base anchors 6/703, now 6/705).
   Executable AST equality against HEAD independently passes.
4. **MINOR, confirmed coverage gap/fixed, in envelope.** Add
   test_translation_note_records_both_sides[side/tkhd]: source and output
   translations must appear in BEST-EFFORT note, verdict SAME. Independent
   in-memory mutation deleting the note makes BOTH tests reject it (2/2).
5. **ADVISORY, accepted/report, in envelope.** FFmpeg qt fixture rotation
   has zero translation; only synthetic and actual IMG_6702 witness the
   translation equivalence. No stronger fixture claim in report.
6. **ADVISORY, confirmed/fixed, in envelope.** Comment now states any
   codec at one channel gets mono/absent equivalence, not PCM alone.
7. **ADVISORY, accepted, in envelope/report only; no code change.** Empty codec tag
   warns `data track `; uppercase GPMD is not mapped. Report safe-side limit.
8. **ADVISORY, settled by seat, in envelope/report.** Location does not
   reach output. Only key names and zero atom counts in report; no value
   read at cell, no private tags/record copied. Supplied generation-25
   evidence: source has two named location keys; output key-name set has
   none, and loci/(c)xyz/keys atom counts are all zero.
9. **ADVISORY, confirmed/fixed, in envelope.** he.main call is inside
   try/finally; capsys.readouterr drains even a raising runner. AST comparison
   proves every prior phone assertion unchanged. Footage never run here;
   final-state seat RUN REQUEST in RESUME HERE.

### Additional CHARC naming witnesses

CHARC 5a8339db3b9c6b4a authorizes these NEW nodes in test_jobs_naming.py:

```text
test_mov_and_uppercase_mp4_share_run_registry[mov-first]
test_mov_and_uppercase_mp4_share_run_registry[mp4-first]
test_mov_collision_with_uppercase_mp4_on_disk[final]
test_mov_collision_with_uppercase_mp4_on_disk[temporary]
```

All four pass on unchanged naming product code. Registry preserves each
planned MP4 suffix case while numbering across case-only extensions in either
order; existing uppercase final or partial also forces _2.mp4 for MOV.
The planted occupied file bytes remain unchanged. No case-sensitive-assumption
failure and no naming STOP/fix. Existing test functions remain verbatim.

### RED/GREEN ids and loop record

RED before product cleanup, d427dc9, exact new failing ids:

```text
tests/test_container_spike_compare_equivalences.py::test_nontranslation_matrix_change_control[w-side]
tests/test_container_spike_compare_equivalences.py::test_nontranslation_matrix_change_control[w-tkhd]
tests/test_container_spike_compare_equivalences.py::test_nontranslation_matrix_change_control[uv-side]
tests/test_container_spike_compare_equivalences.py::test_nontranslation_matrix_change_control[uv-tkhd]
```

4 failed / 6 passed / 892 deselected, EXIT 1. The six passed are both new
note tests and all four naming witnesses. Same selection after the fix:
10 passed / 892 deselected, EXIT 0. Full light includes all 33 equivalence
nodes and the original real-difference controls, which remain DIFFERENT.

Verification loop: suspect R1 exclusion overreach -> reproduce four false
SAMEs independently -> fix ONLY non-translation coefficients -> focused
GREEN and broad light. Confirmed note-coverage gap -> new tests -> independently
remove note in memory -> both reject deletion. Confirmed docs/comment and
capture issues -> minimal fixes -> AST checks and lint/types. Final pass finds
no new product issue within the owned surface. The known UNC failures repeat
as an environment artifact; no product remediation. No finding rejected as
a false positive; the earlier prototype stall is environment-only, settled by
52-passed seat run. No new unresolved design choice.

### Commands, logs and exits

All logs below are under `work/wp4.4/s2t2/`. Pytest commands use
`PYTHONPATH=scripts`, VIRTUAL_ENV removed, `-p sandbox_mkdir_shim
-p no:cacheprovider`, fresh basetemp `work/wp4.4/tmp/<run>`, and
`-m "not gpu and not footage and not gui and not slow and not fullclip"`.
No forbidden marker was executed in this turn.

| Log | Command / selection | Result | EXIT |
|---|---|---|---|
| red.txt | `uv run pytest -v tests/test_container_spike_compare_equivalences.py tests/test_jobs_naming.py -k "nontranslation_matrix_change_control or translation_note_records_both_sides or mov_and_uppercase_mp4_share_run_registry or mov_collision_with_uppercase_mp4_on_disk" --basetemp=work/wp4.4/tmp/s2t2-red` plus shim/markers | 4 failed / 6 passed / 892 deselected, expected RED | 1 |
| green.txt | Same selection, basetemp s2t2-green | 10 passed / 892 deselected | 0 |
| format-fix.txt | `uv run ruff format tools/container_spike/compare.py tests/test_container_spike_compare_equivalences.py tests/test_jobs_naming.py tests/test_wp44_mov_input.py src/clearwater/io/video/encode.py` | 5 files left unchanged | 0 |
| light.txt | `uv run pytest -q tests/test_wp44_mov_input.py tests/test_jobs_naming.py tests/test_container_spike_compare_equivalences.py tests/test_container_spike.py tests/test_io_video_encode_units.py tests/test_headless_export.py --basetemp=work/wp4.4/tmp/s2t2-final` plus shim/markers | 1122 passed / 3 failed / 5 deselected in 56.93 s | 1 |
| ruff.txt | `uv run ruff check .` | All checks passed | 0 |
| format.txt | `uv run ruff format --check .` | 273 files already formatted | 0 |
| mypy.txt | `uv run mypy` | No issues in 141 source files | 0 |
| verification.txt | Scratch `uv run python -` note-deletion/AST check | Tooling import failed: tools missing from sys.path; no product/test ran | 1 |
| verification-final.txt | Same scratch check, explicit tools path like test harness | 2/2 note deletions rejected; encode executable AST unchanged; all phone assertions unchanged, capture finally confirmed | 0 |
| ledger-write.txt | Work-local ledger update via `uv run python -` | Historical records retained, new RESUME HERE; uv emitted inherited VIRTUAL_ENV warning, write succeeded | 0 |
| locks.txt | Work-local `uv run python -`: changed-path allowlist, ASCII/LF, syntax, naming prefix against HEAD, script syntax, git diff --check | Exactly seven granted paths; existing naming functions unchanged; safe row extractor not executed | 0 |
| ruff-final.txt | `uv run ruff check .` after clarifying the module docstring's unconditional audio-copy sentence | All checks passed | 0 |
| format-final.txt | `uv run ruff format --check .` after that docstring clarification | 273 files already formatted | 0 |
| locks-final.txt | Final ownership/ASCII/LF, encode executable AST, diff whitespace and all six grant IDs in report/ledger | All checks pass; exactly seven changed paths | 0 |

Light failures are the already-confirmed sandbox UNC PermissionError [WinError 5]
nodes in test_headless_export.py: test_g1_inside_sees_every_spelling_of_the_same_folder,
test_g1_main_refuses_every_footage_check_through_another_spelling[unc],
test_g1_the_redactor_hides_the_extended_spellings. No workaround or file edit.
The gate rechecks them at seat. Prototype was not rerun after its authoritative
seat 52 passed / 10 deselected result. No full test-suite green is claimed.

The new report includes spec 5.2/8.3 quotes (ASCII HTML arrow references),
rule sites, RED/GREEN and Q1 collection diff, every grant, phone/r0 evidence,
two mebx omissions, privacy key names/counts, fixed mono equivalence, Q5 HLG
refusal code text, Q4 corroboration and explicitly missing raw rows, Limits
2/7, review disposition and remaining seat actions. No register change.
