# WP4.4 cumulative ledger

## RESUME HERE -- fresh Codex seat after turn 4

### State and immediate next steps

WP4.4 is the MOV-input package, CODEX lane, product tier STRONG. The binding
brief is `docs/briefs/wp4.4-brief.md`; its CHARC Rulings govern the Questions.
Read the dispatch protocol, APPLICATION and CLAUDE for a fresh dispatch, and
use this ledger for the completed work and evidence. Do not re-derive the
resolved STOPs or read another worktree.

Worktree/branch: `.worktrees/wp4.4`, `wp4.4`; product base `5e3537d`.
Known commits: round-0 ledger `7483e91`; round-0 grant in brief `0b71bd3`;
MOV implementation `35391b0`; stereo fixture `e4141f8`. Turn 4 starts at
`e4141f8`; the dispatcher will commit the two turn-4 paths and supply that
HEAD to the fresh seat. No cell commits or .git writes are allowed.

Product implementation is done within the grants: both suffix sets accept
MOV; naming maps only case-insensitive MOV to lowercase MP4; the sink copies
only gpmd data, excludes tmcd as before, drops other data deterministically
and reports it through the existing not_carried path. Tests cover routing,
naming, synthetic allowlist behavior and rotated stereo qt export with V4.
Turn 4 adds the ONE footage test, now written but NOT RUN by the cell.

Immediate dependency: the orchestrator must run the phone node below. Expect
one pass with exit 0 and exactly two mebx omission warnings; this is an
expectation, not footage evidence yet. Any new V4 MANDATORY/REQUIRED difference
is a STOP to CHARC through the dispatcher, with item NAMES only. No broader
audio, probe, decode, mux, comparison or interface change is authorized.

After that evidence arrives: Reviewer A to convergence, final report per
task 7, then the orchestrator's Reviewer B and ONE two-leg gate, in the order
the dispatcher commissions. No Reviewer A or B has run so far; no gate has run.
Do not claim package completion until all required evidence is supplied.

### Rulings that must survive the re-seat

1. CHARC `197131faf8764ebd` (original brief FINAL): Q1 permits only the old
   clip.mov naming expected-value edit plus a new MP4-case control, and the
   GUI filter/MOV routing edits. Q2 grants encode.py's explicit
   `MP4_DATA_CODEC_TAGS = frozenset({"gpmd"})` data map only, one deterministic
   command/no retry, omitted tags reported through existing not_carried.
   Synthetic zzzz unit plus real mebx footage witness; no synthetic mebx authoring.
   Q3 is house V4 (MANDATORY/REQUIRED and roster SAME), no runner pixel bound.
   Q4 leaves DR-15 OPEN: add edit-list corroboration only; touch no register.
   Q5 keeps Dolby Vision clips OUT, with the report fact below. Rotation is
   required on the synthetic fixture and explicitly asserted on the phone output.
2. CHARC `73d2797750c57625` (round-0 GRANT, 2026-10-29T21:59:13Z):
   `tests/test_io_video_encode_units.py:80` changes only
   `DataStreamInfo(3, "meta")` to `DataStreamInfo(3, "gpmd")`.
   Adding meta to the allowlist is DECLINED. The assertion at base 365-372 is
   verbatim; base row 753 is unchanged because it is a packet-table input to
   not_carried, not the map probe. Verified by whole-file one-token diff and
   80 passing encoder units. Report's owned-files list and accept record must
   name the granted file/line and message ID.
3. CHARC `093384f126589674` (2026-10-29T22:14:29Z): the qt fixture uses
   stereo pcm_s16le (`-ac 2`); house V4 is unchanged. Shared-comparator change
   DECLINED; no product fix exists/wanted. Owner mono lpcm has absent layout
   in both files (seat probe); the synthetic declared-mono limitation is
   CHARC's MINOR row at accept, quoted in full in the resolved STOP below.
   The report must name that limit in one line. The cell touches no register.
4. Orchestrator generation 24, turn 4 (FINAL unless CHARC overrides): phone
   record state is `done with warnings`, exit 0, sole expected MP4. Warnings
   must be exactly the not-carried data-track notices, including mebx, with no
   other text. Two source mebx tracks and no copied data produce exactly two
   identical `Not carried to the output: data track mebx` warnings: verify.py
   enumerates missing source tracks without deduplication. The new test checks
   prefix, total count 2, and exact mebx count 2, with safe count-only failures.

### Remaining report content and evidence

Report path (not created yet): `docs/reports/wp4.4-mov-input.md`.
Quote spec 5.2 at 213 and 8.3 at 384; explain the suffix/naming/allowlist sites;
list RED/GREEN node IDs and final-state light results; include seat round-0
failure and the forthcoming phone result as format facts only. Name omitted
best-effort items only; the expected mebx list has two entries, not deduplicated.
For CHARC, provide IMG_6702's edit-list source/output rows as DR-15 corroboration
only. Have the seat supply a safe subset of comparison facts if needed; the
test does not save or print the full fidelity record. Do not dump record/tag data.
The known source video edit is media_time 0 with negative ctts (inventory/seat
evidence), not a new cell observation or a DR-15 closure.

Q5 report facts are already grounded in the accepted inventory, no DV footage
run needed: `IMG_6704.MOV` and `IMG_6772.MOV` are C2 in
`docs/reports/inventory-2026-10-29.md:282,299`; C2 transfer is `arib-std-b67`
(HLG), line 268. Spec 5.3 refuses HLG. The probe branch at
`src/clearwater/io/video/probe.py:443-452` yields the text:
`This video uses HLG HDR, which Clearwater does not support. Record in standard (SDR) mode instead.`
Report only the clip names, transfer tag and refusal text, with clear attribution
to inventory/code; they were not tested here. No second footage test or register row.

Keep the one-line declared-mono PCM limit in the report, and leave its MINOR
register entry to CHARC at accept. Retain the inherited encoding note:
`tests/test_gui_open.py` has pre-existing U+00E9 (base 368/current 369);
new lines are ASCII, original Unicode unchanged because Q1 does not permit
normalizing that unrelated test. No ruling on whole-blob ASCII was supplied.

### Validation state and run request

Turn 4: the final non-footage file run is GREEN, 6 passed / 1 footage node
deselected; ruff check GREEN; mypy GREEN, 141 source files. Commands/logs are
in the turn-4 record below. The house helper is unchanged. Turn 3 full light
run: 1021 passed, 3 UNC sandbox failures, 1 gui pin deselected. The same three
UNC nodes PASS at the seat (3 passed, EXIT 0), so they are confirmed artifacts;
never mask them or change the existing helper. Whole GUI file passed 31 in
turn 2, naming file 865, encoder file 80 plus the new map test. Seat format at
turn-4 entry: clean, 272 files; ruff check clean; zero CR (dispatcher-supplied).
No full suite or harness gate is due from the cell.

**RUN REQUEST (Git Bash, orchestrator seat only):**

```bash
env -u VIRTUAL_ENV uv run pytest -q -rs tests/test_wp44_mov_input.py::test_phone_mov_runner_and_v4 -m footage --basetemp=work/wp4.4/t4-seat-footage > work/wp4.4/t4/seat-footage.txt 2>&1
```

Scheduling allowance 1-3 minutes, CPU libx265; not a timing figure. All outputs,
cache and runner-record.json are in that test's tmp_path under the basetemp.
The source is located through local_config, read-only. No test execution at
the cell and no source path, tag value, full record or private metadata in the
ledger or return. A skip is not a phone proof; only genuinely absent footage
may skip, while missing/unreadable/ambiguous roots are errors after conftest's
configuration handling.

### Frozen scope and operating disciplines

Owned implementation paths are gui/sources.py (suffix set/docstring only),
jobs/naming.py (extension rule/docstrings), tools/headless_export.py (suffix
set/docstring only), io/video/encode.py (data map/allowlist only),
tests/test_jobs_naming.py (new tests and Q1 expected value),
tests/test_gui_open.py (Q1 edits only), the one-token encoder-unit grant,
tests/test_wp44_mov_input.py, the report and this ledger. Every other existing
test, fixtures, conftest, interfaces, export engine, V4 instruments, spec,
register, dependencies and config are NOT owned. Any new existing-test
conflict or need to cross that envelope is STOP, with a cheap reproduction.

Footage is read-only and never accessed at the cell. Footage/GPU/network/heavy
runs are exact RUN REQUESTS at the orchestrator's seat, scheduled around the
other package's exclusive windows; never read another worktree. All output/logs
are worktree-local under work/wp4.4; no writes outside the sandbox. No mailbox
posts, no commits, no git stash, no deletion of kept basetemps. All runner
output goes to files; report summaries, never dump logs. Keep new text ASCII/LF.

Cell pytest always uses `PYTHONPATH=scripts` and
`-p sandbox_mkdir_shim -p no:cacheprovider`, a fresh work-local basetemp, and
the permitted non-heavy marker expression. Do not work around unreachable
FFmpeg/index/sandbox restrictions. Ruff format is checked at the seat.
Attribution and commits are the dispatcher's responsibility; every turn ends
with FILES CHANGED and the conventional wp4.4 commit subject.

Reviewer A is the driver-run Claude opus/high read-only pass between turns,
not an agent the cell spawns. Adjudication turns modify only the ledger and
YIELD before remediation. Maintain the cumulative round counts (severity,
in/out, NEW/REOPENED, reverts, product versus test fixes, transport/version and
dispatcher depth). Round 5 and every fifth round STOP for approval; convergence
follows `docs/review-gate-clearwater.md`. Reviewer B and the ONE two-leg gate
run at the orchestrator's seat after A converges and B returns; no fullclip leg
and no harness gate for this package. See the fill for collection accounting.
Report every lock, deviation, per-change list, review disposition and exact
node additions/removals. Only removed ID so far is
`tests/test_gui_open.py::test_routing_by_extension[a.mov-refusal]`, replaced
by `[a.mov-video]` and `[a.MOV-video]`; naming's existing node is retained.

Last dispatcher depth: 189,237 input tokens, binding window 258,400. This
turn ends at the mandatory boundary; next work belongs to a FRESH cell as
commissioned, not another build burst in this context. Do not estimate depth.

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
The real mono path is witnessed by IMG_6702's footage test. Comparator changes
are DECLINED for this package; no product fix exists or is wanted. The original
synthetic declared-mono limitation is retained as evidence below, not remediated.
Q2 still grants the data map only.

Seat PCM probe (FFmpeg 9.0.2, supplied at turn 3, script
`work/wp4.4-seat/pcm_layout.py`, stream copy to MP4): synthetic mono sowt with
layout mono becomes ipcm, one channel, layout absent; synthetic stereo sowt with
layout stereo becomes ipcm, two channels, stereo SAME; IMG_6702 lpcm is mono
with no layout in both source and output, SAME. The cell did not read footage
or rerun that seat probe.

CHARC owns this MINOR register row at the accept; the cell touches no register:

> a QuickTime PCM track that DECLARES a mono layout leaves the MP4 with the
> channel count but no layout declaration (FFmpeg 9.0.2 ipcm writer; stream copy
> cannot set one); V4's audio item reads DIFFERENT for such a source; the owner's
> iPhone clips are unaffected (lpcm, no layout). Trigger: the next V4 instrument
> touch (treat mono and absent as equal at channels == 1) or an owner MOV whose
> V4 reads DIFFERENT on that item alone.

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
| Turn 4 exit | Pending dispatcher reading | Mandatory yield and fresh-seat handoff |

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
| seat-footage.txt | Git Bash RUN REQUEST in RESUME HERE | Pending at orchestrator seat; NEVER run at cell | Pending |
| locks.txt | `uv run python -` (AST and byte checks, without importing or executing the test) | Both modified files ASCII/LF; house helper unchanged; exactly one footage node | 0 |

Verification-loop record: traced the fixed warning count against the unchanged
verify/export code; checked that state and warning assertions implement the
new ruling; ran the non-footage node selection to green without executing the
new marker; no new suspect, confirmed defect, false positive or revert.
Reviewer A has not run. Handoff is to a fresh seat after this bounded turn.

| Boundary (not Reviewer A) | Critical / major / minor | In / out | NEW / REOPENED | Reverts | Product / test fixes | Verdict | Depth |
|---|---|---|---|---|---|---|---|
| Turn 4 author verification | 0 / 0 / 0 | 0 / 0 | 0 / 0 | 0 | None / ruled phone test written; seat run pending | No open build STOP; await footage evidence, fresh seat for remaining work | Pending dispatcher; entry 189,237 / 258,400 |
