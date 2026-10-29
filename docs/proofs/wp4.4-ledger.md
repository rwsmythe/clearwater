# WP4.4 cumulative ledger

## Turn 2 STOP: qt PCM audio layout differs in V4

Recommended disposition: route to CHARC for an audio-mux or V4-instrument scope
ruling; retain the fixture and the house assertion unchanged pending that ruling.
No PCM conversion, fixture substitution, comparison weakening or audio-mux
option has been added. Q2 grants the data map only.

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
Seat reproduction is requested below. This is an environment failure, not an
additional conflicting test expectation.

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
| Turn 2 exit | Pending dispatcher reading | Mandatory task-group yield |

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

After CHARC dispositions the qt STOP, the final fixture/light runs will need
to pass. The three sandbox-blocked UNC nodes need this seat command now (from
Git Bash, estimated scheduling allowance under one minute; no timing figure):

```bash
env -u VIRTUAL_ENV uv run pytest -q tests/test_headless_export.py::test_g1_inside_sees_every_spelling_of_the_same_folder 'tests/test_headless_export.py::test_g1_main_refuses_every_footage_check_through_another_spelling[unc]' tests/test_headless_export.py::test_g1_the_redactor_hides_the_extended_spellings --basetemp=work/wp4.4/t2-seat-unc > work/wp4.4/t2/seat-unc.txt 2>&1
```

Format at the seat as commissioned:

```bash
env -u VIRTUAL_ENV uv run ruff format --check . > work/wp4.4/t2/seat-format.txt 2>&1
```

Reviewer A has not run; no convergence or package-completion claim is made.

| Round / boundary | Critical / major / minor | In / environment or pre-existing | NEW / REOPENED | Reverts | Product / test fixes | Verdict | Depth |
|---|---|---|---|---|---|---|---|
| Turn 2 author verification (not Reviewer A) | 0 / 1 / 2 | 1 / 2 | 3 / 0 | 0 | Routing, naming, data map / RED tests and granted fixture token | STOP: qt MANDATORY audio difference; no out-of-envelope remediation | Pending dispatcher |

Verification-loop record: resolved the granted round-0 test conflict; confirmed
the new qt audio difference independently with plain FFmpeg; confirmed UNC
failures originate in the unchanged test helper before product assertions;
confirmed non-ASCII is inherited rather than introduced. No false-positive
rejections, no reverts, and no fix to the unowned audio-mux/instrument surface.
