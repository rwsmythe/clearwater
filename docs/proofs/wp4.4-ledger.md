# WP4.4 cumulative ledger

## Round 0: STOP for an additional existing-test conflict

Recommended ruling: grant the single fixture correction at
`tests/test_io_video_encode_units.py:80`, replacing the synthetic copied tag
`meta` with the proved HERO13 tag `gpmd`. Keep the map assertion at lines
365-372 unchanged. This file is currently NOT owned; no edit has been made.

**[major, in-envelope, NEW, REASONED + EXECUTED]** Q2's gpmd-only
allowlist conflicts with that existing test. `_probe` supplies data streams
`tmcd` at index 2 and `meta` at index 3; the test requires maps
`["0:v:0", "1:1", "1:3"]`. The ruled filter must omit `meta`, producing
`["0:v:0", "1:1"]`. Adding `meta` to the allowlist would violate the grant:
it is not a proved HERO13 codec tag. Q1 authorizes no change to this file.
This needs a ruling before turn 2, under the dispatch's STOP for existing-test
changes beyond Q1. It does not require widening product scope.

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
unchanged this turn. Protocol, APPLICATION, CLAUDE, prompting standard,
review/gate fill and the binding clauses have been read. This is a dispatched
implementer; the using-superpowers skill explicitly exempts dispatched agents.
The user-specified task ladder and yield schedule govern the work.

| Boundary | Dispatcher-supplied cell depth | Action |
|---|---|---|
| Turn 1 entry | Fresh session; no numeric depth supplied | Round 0 only |
| Turn 1 exit | Pending dispatcher reading | Yield; evaluate near 200K, stop at a boundary near 250K |

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
FFmpeg nor footage. The existing meta-based unit assertion is the STOP above.

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

Expected from ruled Q2 evidence: encode failure on mebx (script EXIT 1),
video hevc/hvc1, audio pcm_s16le/lpcm, two data mebx tracks. This is a prediction,
not a cell run. On failure, comparison names remain null (not an empty pass).
An unexpected failure or any MANDATORY/REQUIRED difference is a STOP to CHARC
through the dispatcher. The already-ruled mebx failure is baseline evidence.
Footage, GPU, network and heavy runs have NOT been executed by the cell.

## Validation and review record

| Turn / run | Command or artifact | Counts / outcome | EXIT |
|---|---|---|---|
| 1, cheap conflict reproduction | `uv run python -` (existing `_probe` / `_command`, in-memory filtered data) | One confirmed existing-test conflict; no FFmpeg or footage | 0 |
| 1, scratch-script lint | `uv run ruff check work/wp4.4/r0/round0.py` | All checks passed; `work/wp4.4/r0/ruff-script.txt` | 0 |
| 1, artifact check | `uv run python -` (AST parse, import without main, ledger byte check) | PASS: script imports without executing footage code; ledger ASCII/LF; `work/wp4.4/r0/artifact-check.txt` | 0 |
| 1, round-0 witness | Seat command above | REQUESTED, not run | Pending |

| Round | Critical / major / minor | In / out | NEW / REOPENED | Reverts | Product / test fixes | Reviewer / verdict | Depth |
|---|---|---|---|---|---|---|---|
| 0 (author mapping) | 0 / 1 / 0 | 1 / 0 | 1 / 0 | 0 | None / none | STOP for scope ruling; Reviewer A not yet run | Pending dispatcher |

Verification loop: suspected unlisted existing-test conflict; independently
confirmed by fixture/expectation trace and command-construction reproduction;
not fixed because unowned. No rejected false positives. Round 0 ends at its
mandatory yield; further build work awaits the dispatcher's next turn.
