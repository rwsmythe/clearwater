# WP-DR113 cumulative round ledger

## Round 0

Base: branch `wp-dr113`, HEAD `dc018f25`. Initial `git status --short`
was empty. This turn maps the commissioned instrument change; no implementation
or committed test change has been made. Reviewer A and Reviewer B have not run.
Transport: Windows-native Codex cell, PowerShell; dispatcher owns the CLI/model
invocation record and commits. All evidence below is inside this worktree.

Depth after turn 1: 147,692 tokens (dispatcher reading supplied with turn 2).

| Round | Critical | Major | Minor | In/out envelope | NEW/REOPENED | Reverts | Fixes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | No reviewer findings yet | No reviewer findings yet | No reviewer findings yet | Mapping only; three discrepancies below | No review round yet | 0 | Documentation only; no product/test fixes |

### 1. Anchors and available facts

Binding anchors: plan `docs/clearwater-implementation-plan.md:89` (4.5),
spec `docs/underwater-correction-spec.md:58` (D20), `:124` (D86), `:132`
(D94), `:143` (D105), `:350` (7.5), `:371` (8.2), `:482` (V4).
The WP-D112 note is in `docs/decisions.md:45` (AD-30).
The dispatch recipe, APPLICATION, CLAUDE, model prompting standard and
review/gate fill were read. The brief's turn ladder and sandbox pytest shim
take precedence over generic workflow defaults. No subagents were launched.

| Mechanic / surface | Base anchor | Present behavior / planned PCM effect |
| --- | --- | --- |
| `compare.Packet` | `tools/container_spike/compare.py:170` | `pts` and `duration` are exact `Fraction` seconds or None; `size` is bytes, `md5` is the payload hash. |
| `compare.Facts` | `tools/container_spike/compare.py:188` | Full probe document, movie boxes, decoded video pts, packet lists by index, stream keys. No new Facts field is necessary. |
| `run_ffprobe` | `tools/container_spike/compare.py:545` | Instrument-owned facts, not the product audio reader. |
| `_time_base`, `_ticks` | `tools/container_spike/compare.py:585`, `:595` | Exact clock parsing and tick-to-second conversion. PCM must validate the stream clocks and recover exact ticks using the SOURCE base. |
| `stream_packets` | `tools/container_spike/compare.py:624` (`:640-656`) | Independently reads pts/duration/size/data_hash with MD5. Missing size becomes -1. Flags and side data are not in Packet. |
| `gather` | `tools/container_spike/compare.py:679` (`:691`, `:705`) | Whole `-show_format -show_streams` document, then independently reads audio/data packet lists. |
| `_sequence_item` | `tools/container_spike/compare.py:777` | Exact full-list equality, summarized only for storage. Keep this compressed path. |
| `_packet_rows` | `tools/container_spike/compare.py:953` | `[exact seconds pts, exact seconds duration, size, MD5]`. Keep unchanged. |
| `_packets_summary` | `tools/container_spike/compare.py:958` | Count, endpoints, whole-list SHA-256. Keep compressed summaries. |
| `_keyed_packets` | `tools/container_spike/compare.py:978` | Stream keys paired with their packet rows. No codec-specific rule today. |
| `_keyed_packet_items` | `tools/container_spike/compare.py:1092` | One item per union key; absent item if no streams. Preserve pairing, item names and absent behavior. |
| `compare_facts` audio item | `tools/container_spike/compare.py:1252-1261` | Calls the generic row comparison; add independent source-codec PCM dispatch here or in an audio-specific helper. Non-audio callers stay on the generic path. |
| `AUDIO_PACKETS`, `ROSTER` | `tools/video_fidelity.py:93`, `:102-145` | The packet name and side-data name (`:143`) stay exactly as written, with no extra roster item. |
| `_cut_items` | `tools/video_fidelity.py:932` | D86 applied before edit/color/depth refinements in `fidelity_items`. |
| `_cut_items` copied-packet branch | `tools/video_fidelity.py:998-1014` | Keeps source packets with absent pts or pts < readable end, then compares exact rows. PCM uses the SAME window, source-only final partial-frame floor and effective durations. Telemetry/compressed branches stay as today. |
| `audio_side_data` | `tools/video_fidelity.py:667-696` | Separate ffprobe call yields `[pts in ticks, discard flag, side data]`. No Facts extension needed; PCM side-data eligibility is read here/from its result. |
| Side-data item and cut handling | `tools/video_fidelity.py:1230-1243` | Currently slices SOURCE by OUTPUT packet count under `cut`; flattening retains one row per packet including pts. For eligible PCM compare its independently selected source window and strict output extents/runs, without harmless boundary rows. For noneligible PCM retain per-packet reading. Compressed slicing/rows remain unchanged. |
| `notes` | `tools/video_fidelity.py:1194`, `:1199`, `:1206`, `:1232`, `:1248` | Today only D86 and edit-list readings are appended. Add successful PCM reading notes after cut normalization has decided the final item, not before it. |
| `roster_item` | `tools/video_fidelity.py:1151-1172` | Strips keyed suffixes and checks exact expected-name set. Unchanged. |
| `fidelity_items`, `fidelity_record` | `tools/video_fidelity.py:1175`, `:1251` | Facts -> base comparisons -> D86 -> edit/color/depth -> configuration/side data -> redact -> roster; record attaches returned notes at `:1274`. Preserve that ordering. |

Per-stream `Facts.probe['streams']` already retains `codec_name`, `time_base`,
`sample_rate`, `channels`, `sample_fmt`, `bits_per_sample` and any
`bits_per_raw_sample` printed by ffprobe. They are untyped probe fields and may
be absent, so the PCM helper must validate them rather than assume availability.
Packed width comes from the independent codec table, not decoded sample_fmt or
bits_per_sample (24-bit PCM commonly decodes to s32). The new derived evidence is
presented/stored totals and maximal contiguous runs, not new probe fields.
Discard flags/side data already come from the V4 instrument's separate read.
Sample bytes/decoded sample hashes are NOT available from this reading.

Product reference, read only: `src/clearwater/io/video/verify.py:873` dispatches
on source PCM; `:910` reads totals, `:952` grants the D86 final-window floor,
`:965` merges runs, `:972-988` binds run equality to equal source ticks,
`:992` compares format fields, `:1017` normalizes only truncated-with-cut source
prefixes, `:1053` compares runs. `PacketTable.pcm_dropped_bytes` is at `:200`.
Compressed `_audio_problems` remains at `:1067`. These references are for
understanding only: `tools/` will import no product audio reading.

### 2. Consumer inventory and effect

Search evidence: `work/wp-dr113/round0/consumers.txt` and
`work/wp-dr113/round0/all-record-consumers.txt` (repository-wide Python call/name
searches, including tools). Consumers use unchanged item names, class/status
fields, roster and summary fields. No consumer edit is needed beyond the new
owned regression rows. Compressed/video/data/BEST-EFFORT behavior is unchanged.

| Consumer / base location | Assertion or use | Effect of the PCM reading |
| --- | --- | --- |
| `tests/test_io_video_encode.py:192-196` `_assert_v4` | Combined MANDATORY+REQUIRED flag true, roster SAME. `Runs.get` builds records at `:102`. | Existing PCM fixture rows gain notes and stay SAME; rechunked/D86 PCM records can now pass without relaxing assertions. |
| Same module `:256`, `:268` | Fixture matrix (including `vid-pcm-irregular`) and intact irregular-PCM control invoke `_assert_v4`. | Preserve all existing assertions and their passing verdicts. |
| Same module `:665`, `:686`, `:711`, `:735`, `:747`, `:757`, `:771`, `:868` | Synthetic offset/edit-list/timecode/VFR/BT.601/5K/truncated-B-frame exports invoke `_assert_v4`; `:698`, `:713` require edit note membership. | AAC fixtures remain identical; PCM note membership must coexist with existing edit/D86 notes. |
| Same module `:932`, `:963` | Planted orientation faults inspect only orientation items. | No change. |
| Same module `:1730`, `:1751`, `:1768`, `:1788-1790`, `:1800` | Planted edit/time/color/audio/bit-depth errors; audio rule explicitly locates items by `AUDIO_PACKETS` prefix and requires a DIFFERENT. | Keep name/prefix and compressed reencode rejection. |
| Same module `:1859-1860` | Real sink GX011627 V4 record, trim and full. | AAC comparison unchanged; no footage run in this cell. |
| Same module `:337`, `:410` | WP-D112 truncated and trimmed-presentation real-sink tests currently check product/decoded bytes, not V4. | Reuse their derivative recipes for ONE new parametrized V4 test; leave their existing assertions unchanged. |
| `tests/acceptance_support.py:338-347` | `assert_fidelity`: combined flag true plus roster SAME. | No assertion relaxation. |
| `tests/acceptance_support.py:350-365` | Builds V4, redacts file paths to names, writes fidelity.json. | New PCM notes survive names-only checks; counts/codec text contain no paths. |
| `tests/test_v51_video_acceptance.py:78-90` | Mutation controls reject false combined flag and missing roster. | Unchanged. |
| Same module `:108-114`, `:152-159`, `:193-216` | Fixture sweep, D86 batch, owner GoPro trim: save V4 and assert_fidelity; exact frames/D86 notes/GPMF independently checked. | Fixture list `:48` has no PCM entry; current AAC paths unchanged. |
| Same module `:343-355` | V9 record feeds color/orientation assertions and mutations. | Audio change does not affect these assertions. No other `test_v51_*` file directly consumes V4. |
| `tests/test_container_spike.py:162`, `:167-212` | compare_files identity/reencode records, mandatory/combined flags, specific audio presence/sync/edit fields. Synthetic generator uses AAC at `:99`. | Existing compressed records unchanged. |
| Same module `:214-333` | B-frame exception, VFR, rotation, offsets, codec/container requirement, combined-flag and frame-loss controls. | No audio relaxation for compressed sources. |
| Same module `:485-498`, `:811`, `:901-908` | CLI JSON/table, FFREPORT guard and GoPro self-comparison. | Same serialization/name contracts; item.note contains PCM disclosure when applicable. No owner-media read this turn. |
| `tests/test_container_spike_compare_equivalences.py:37-77`, `:84`, `:87-90` | Synthetic Facts builder uses PCM but omits sample_fmt and packet evidence; whole comparison must be SAME. | Add a valid sample_fmt to this owned scaffold before enforcing strict PCM evidence. Preserve all existing equivalence tests and their target names. |
| Same module `:98-254` | Translation, SAR and mono layout equivalences with real-difference controls. | Target verdicts stay unchanged; new PCM rows sit beside them. |
| `tests/test_video_fidelity.py:68-72`, `:79-103` | Missing-frame summary, exact roster including keyed AUDIO_PACKETS, deliberately removed bit-depth item. | Keep names/roster/summary and negative controls. |
| Same module `:222-231`, `:247-251` | Base/V4 location redaction and CLI combined flag/output guard. | PCM notes contain only counts/codec labels; existing no-audio/AAC readings unchanged. |
| `tests/test_jobs_export_video.py:106-110`, `:183-184`, `:221`, `:714` | Engine V4 combined flag and roster; fixture sweep, synthetic large frame, owner GoPro trim/full. DECODABLE at `:52` has no PCM entry. | Unchanged AAC and roster assertions. |
| `tests/test_wp42_video_path.py:373-386`, `:400`, `:422`, `:480` | Composition CPU/GPU/V9 V4 summary plus GPMF. | Existing compressed paths unchanged. |
| `tests/test_wp44_mov_input.py:117-126`, `:168`, `:231` | Combined flag/roster on generated stereo PCM qt MOV and IMG_6702 owner MOV. | Existing SAME remains SAME with PCM notes; WP4.4 translation/SAR/mono readings and proof remain untouched. |
| `tests/test_prototype_clip.py:623`, `:834`, `:864` | Prototype comparison combined flag and direct compare_facts mutation use. | AAC shapes unchanged; PCM uses independent new instrument rule if supplied. |
| `tools/container_spike/compare.py:1586-1641`, `:1660`, `:1678`, `:1831-1844` | Serialize Item.note, compute differences/flags, render table and CLI counts. | No schema or roster rename; PCM packet item uses new evidence and note; compressed values remain unchanged. |
| `tools/container_spike/spike.py:864`, `:965` | Reencode comparison records and combined pass display. | New PCM verdict where applicable; record generation otherwise unchanged. |
| `tools/prototype/clip.py:2482-2505`, `:2762` | compare_files wrapper writes comparison record and copies combined/mandatory flags into export record. | Same flags; PCM false-difference repaired when supplied. |
| `tools/video_fidelity.py:1272-1274`, `:1301-1302`, `:1347` | Build record, attach notes, display combined flag and note count, CLI compare/encode. | PCM notes are visible in V4 summary. |

The seven fullclip forms come from `tests/conftest.py:861-880` (gx011627 full
parameter) plus `tests/test_color_roundtrip.py:321`. The V4 consumers are
`tests/test_io_video_encode.py::test_gx011627_through_the_sink_keeps_every_mandatory_and_required_item[full]`
and `tests/test_jobs_export_video.py::test_gx011627_through_the_engine_keeps_every_mandatory_and_required_item[full]`.
The other five are encoder levels (`tests/test_io_video_encode.py:1867`),
three decode checks (`tests/test_io_video_decode_hw.py:135`, `:145`, `:161`),
and color round trip (`tests/test_color_roundtrip.py:324`, first30). They do not
directly assert these two V4 items; encoder levels shares the real sink export.
No fullclip/slow/gpu/footage node was run. `tools/headless_export.py`,
`tools/reviewpack/` and `tools/export_oracle.py` have no direct V4-item consumer.

Committed media PCM source: manifest id `vid-pcm-irregular`,
`tests/fixtures/video/pcm-irregular.mov` (codec facts in
`tests/fixtures/manifest.json:4930`, `:4967`). The generated qt MOV fixture
(`tests/test_wp44_mov_input.py:98-108`) is stereo pcm_s16le but is not committed
media. Recorded owner PCM: WP4.4 IMG_6702 (`docs/reports/wp4.4-mov-input.md:105`,
`:119`) and the IMG_6731 / IMG_6729 witnesses supplied in this brief and
`docs/reports/wp-d112-pcm-audio.md`. Those are documentary facts; this cell has
opened none of those owner media or main-tree work records.

### 3. Notes and the fixed roster

`compare.Item.note` is serialized by `compare.build_record` at `:1632` and
rendered by its markdown table. WP4.4's translation reading has an explicit note
from `compare._matrix_translation_note` (`:904-908`) on both orientation items
(`:1294`, `:1308`). Unset SAR (`:1351-1363`) and mono layout (`:1229-1239`)
normalize their values with no explicit equivalence note. NONE of these three
WP4.4 readings is currently copied into V4 `summary.notes`. By contrast, the
edit-list reading at `video_fidelity.py:1204-1206` returns a separate note for
that summary. This distinction corrects the dispatch question's implied premise.

Proposed exact successful PCM Item.note form (ASCII):

```text
PCM: compared by sample extent and timeline runs; packets 100 -> 99
```

Counts are the actual compared source window and strict output packet counts,
including D86. Each PCM equivalence has this note on its item; V4 appends each
distinct successful PCM note to `summary.notes` after the final cut reading.
For multiple PCM streams the side-data item's aggregate note joins these
per-stream notes with `; `, with stream identity retained in the keyed packet
item. Identical note strings need appear only once in summary.notes; every keyed
PCM packet item still carries its own note.
No PCM note is added for a fallback per-packet pass with side data/discard flags.
Unknown-width failures name their codec in the refusal note.

No item name, item class, clause, keyed-name suffix convention or ROSTER entry
changes. Bare compare/spike records retain Item.note; `summary.notes` belongs to
V4 today and is not added to the bare record schema in this package.

### 4. Independent packed-width table

Chosen home: a private `_PCM_BYTES_PER_SAMPLE` mapping in
`tools/container_spike/compare.py`, beside its new private PCM extent helpers.
`tools/video_fidelity.py` reuses THAT instrument helper, never verify.py.
No new dependency or product import. The helpers validate equal codec, exact
time base, positive rate/channels and supported equal sample_fmt, then read both
totals and source-tick runs. Their docstring explicitly binds source-tick run
equality to equal time bases. Output duration/payload evidence always stays
strict. The D86 cap/floor applies only to kept source packets, with a remainder
allowed only on the final kept packet.

Local authoritative inventory: FFmpeg 9.0.2-full_build-www.gyan.dev, recorded in
`work/wp-dr113/round0/ffmpeg-version.log` and `ffmpeg-codecs.log`. The complete
27-codec fixed-width set in that listing is:

| Packed bytes per channel sample | Exact codec names |
| --- | --- |
| 1 | `pcm_s8`, `pcm_s8_planar`, `pcm_u8` |
| 2 | `pcm_s16be`, `pcm_s16be_planar`, `pcm_s16le`, `pcm_s16le_planar`, `pcm_u16be`, `pcm_u16le`, `pcm_f16le` |
| 3 | `pcm_s24be`, `pcm_s24le`, `pcm_s24le_planar`, `pcm_u24be`, `pcm_u24le`, `pcm_f24le` |
| 4 | `pcm_s32be`, `pcm_s32le`, `pcm_s32le_planar`, `pcm_u32be`, `pcm_u32le`, `pcm_f32be`, `pcm_f32le` |
| 8 | `pcm_s64be`, `pcm_s64le`, `pcm_f64be`, `pcm_f64le` |

Refused set: `pcm_alaw`, `pcm_mulaw`, `pcm_bluray`, `pcm_dvd`, `pcm_lxf`,
`pcm_s24daud`, `pcm_sga`, `pcm_vidc`. Any unlisted `pcm_*` name also refuses,
never infers a width from the decoded sample_fmt. The table includes the listed
f16le/f24le decoder codecs; it invents no absent endian/unsigned/planar names.
Bytes per sample frame = mapped width * channels, also for planar codecs.

### 5. Turn-2 RED list and evidence

These are PROPOSED node IDs, to be written in turn 2, not collected/executed
pytest nodes. No committed test was added this turn. All successful PCM rows
will require the PCM Item.note and V4 `summary.notes` membership, not just SAME.

Synthetic positive nodes in
`tests/test_container_spike_compare_equivalences.py`:

```text
::test_pcm_sample_extent_equivalence[img6731-coalesced]
::test_pcm_sample_extent_equivalence[img6729-moved-boundary]
::test_pcm_sample_extent_equivalence[gapful-rechunked]
```

Use the exact WP-D112 numerical tables at
`tests/test_io_video_encode_units.py:837-878` (100 -> 99, totals
100720/100812; 133 -> 133, totals 134400/134414), and the preserved-gap pair
at `:1137-1143`. Baseline packet item is DIFFERENT for all three (first
differences at 94, 118 and 0 respectively). `work/wp-dr113/round0/synthetic.log`
records those readings, using scratch adapters over those same tables.

D86 positives in `tests/test_video_fidelity.py`:

```text
::test_pcm_d86_sample_extent_equivalence[d86-55]
::test_pcm_d86_sample_extent_equivalence[d86-70]
::test_pcm_d86_sample_extent_equivalence[d86-85]
```

Reuse `_truncated_pcm_pair` (`tests/test_io_video_encode_units.py:1045-1058`):
55 percent 39/39 packets and 38814 samples, 70 percent 50/49 and 49502,
85 percent 61/61 and 60659. Final source payloads 909/860/647 bytes;
presented durations cap at stored samples, dropping only the final incomplete
frame bytes. `_cut_items` baseline packet status is DIFFERENT in all three,
recorded in `synthetic.log`. Stub only unrelated file/probe surfaces in synthetic
V4 tests; retain the real comparison pipeline, source-window selection and notes.

Controls (whole audio verdict DIFFERENT; preserve all existing green controls)
in `tests/test_container_spike_compare_equivalences.py`:

```text
::test_pcm_difference_control[one-sample-fewer]
::test_pcm_difference_control[presented-only]
::test_pcm_difference_control[stored-only]
::test_pcm_difference_control[rate]
::test_pcm_difference_control[format]
::test_pcm_difference_control[channels]
::test_pcm_difference_control[codec-aac]
::test_pcm_difference_control[time-base]
::test_pcm_difference_control[one-tick-shift]
::test_pcm_difference_control[swapped-packets]
::test_pcm_difference_control[closed-gap]
::test_pcm_difference_control[opened-gap]
::test_pcm_difference_control[unknown-alaw]
::test_pcm_difference_control[unknown-mulaw]
::test_pcm_difference_control[unknown-bluray]
::test_pcm_difference_control[unknown-dvd]
::test_pcm_difference_control[unknown-lxf]
::test_pcm_difference_control[unknown-s24daud]
::test_pcm_difference_control[unknown-sga]
::test_pcm_difference_control[unknown-vidc]
::test_pcm_difference_control[unknown-unlisted]
```

`format` and the identical unknown-codec pairs are additional REDs today (see
dispute R0-1). Rate/channels/codec may already fail `audio streams present`
while the old packet item stays SAME with otherwise identical packet rows;
distinguish whole audio verdict from item-specific checks in RED reporting.
Other controls use changed packet rows and remain baseline-green. The negative
controls plant a difference on one side, except unknown-width refusal (identical
unknown evidence on both sides must still refuse under the new rule).

Controls in `tests/test_video_fidelity.py`:

```text
::test_pcm_d86_difference_control[earlier-source-partial]
::test_pcm_d86_difference_control[output-partial]
::test_pcm_side_data_control[discard]
::test_pcm_side_data_control[side-data]
```

Reuse partial cases at `tests/test_io_video_encode_units.py:1088-1098`.
For side-data controls plant one output discard flag or nonempty side-data list;
the per-packet fallback must remain DIFFERENT. Include compressed and mixed
PCM/AAC controls to compare the unchanged compressed Item source/output/status/
note values, and no-audio roster behavior. Preserve the fallback rule rather than
inventing a blanket prohibition on identical side data.

AGREEMENT node in `tests/test_container_spike_compare_equivalences.py`:

```text
::test_pcm_instrument_agrees_with_product[img6731-coalesced]
::test_pcm_instrument_agrees_with_product[img6729-moved-boundary]
::test_pcm_instrument_agrees_with_product[gapful-rechunked]
::test_pcm_instrument_agrees_with_product[d86-55]
::test_pcm_instrument_agrees_with_product[d86-70]
::test_pcm_instrument_agrees_with_product[d86-85]
::test_pcm_instrument_agrees_with_product[one-sample-fewer]
::test_pcm_instrument_agrees_with_product[presented-only]
::test_pcm_instrument_agrees_with_product[stored-only]
::test_pcm_instrument_agrees_with_product[rate]
::test_pcm_instrument_agrees_with_product[format]
::test_pcm_instrument_agrees_with_product[channels]
::test_pcm_instrument_agrees_with_product[time-base]
::test_pcm_instrument_agrees_with_product[closed-gap]
::test_pcm_instrument_agrees_with_product[opened-gap]
::test_pcm_instrument_agrees_with_product[earlier-source-partial]
::test_pcm_instrument_agrees_with_product[output-partial]
```

Both readings will receive the SAME test table. Reuse `_pcm_table` (`:765`),
`_truncated_pcm_pair` (`:1045`), and `_pcm_check` (`:803`) in the WP-D112 unit
module from tests only. Adapt stream fields and each packet's tick pts/duration/
size to independent `compare.Facts`/Packet instances using exact base conversion,
with synthetic per-packet hashes. The real `verify.check_output` is reached by
`_pcm_check`; only unrelated `_edit_problems` is stubbed. The instrument calls
its own `compare_facts` and, for cuts, `_cut_items`. Assert pass <-> SAME, plus
expected outcomes, so shared mistakes cannot make agreement alone sufficient.

Relevant existing WP-D112 rows: sample loss `:887-910`, format `:913-925`,
clock/channels `:963-975`, partial evidence `:1025-1042`, D86 `:1061-1098`,
changed runs `:1113-1134`. Codec-AAC, one-tick, swapping, unknown-width and
flag/side-data plants are new instrument controls, not shapes built by that unit
module; flags/side data have no representation in its PacketTable. They are not
claimed as agreement coverage of the product's narrower audio evidence.

ONE new integration function in `tests/test_io_video_encode.py`:

```text
::test_pcm_derivative_v4_through_real_sink[trim-380-over-472]
::test_pcm_derivative_v4_through_real_sink[trim-148-over-240]
::test_pcm_derivative_v4_through_real_sink[d86-55]
::test_pcm_derivative_v4_through_real_sink[d86-70]
::test_pcm_derivative_v4_through_real_sink[d86-85]
```

Reuse only the committed `vid-pcm-irregular` as input; derive media at test time
in per-test tmp_path. Recipes are the existing `setts` trim / optional `atrim`
recipe (`tests/test_io_video_encode.py:410-466`) and faststart byte-prefix cuts
(`:337-377`). Match neighbors' markers: module ffmpeg_tools fixture, no
gpu/footage/slow/fullclip marker, software libx265 and real sink with no checker
bypass. Assert source shape, product success, decoded audio control as applicable,
full V4 MANDATORY+REQUIRED and roster SAME, and PCM note membership. Assert actual
rechunking for d86-70; do not claim trimmed-tail recipes rechunk.

Executed round-0 reproduction (not a pytest run):

```text
uv run python work/wp-dr113/round0/reproduce.py
uv run python work/wp-dr113/round0/reproduce.py --synthetic-only
```

Both exit 0. Runner output is in `work/wp-dr113/round0/reproduce.log` and
`synthetic.log`; complete V4 records are under
`work/wp-dr113/tmp/round0/<shape>/baseline-v4.json`. The scratch script invokes
the EXISTING WP-D112 integration recipes as functions, then runs the unchanged
V4 instrument. These are direct reproduction results, not a pytest pass count.

| Derivative | Audio packet item today | Priming/side-data today | MANDATORY differences |
| --- | --- | --- | --- |
| d86-55 | DIFFERENT | SAME | Packet item only |
| d86-70 | DIFFERENT | DIFFERENT | Both target items; side data first differs at 48, pts 48048 vs 48600 |
| d86-85 | DIFFERENT | SAME | Packet item only |
| trim-380-over-472 | SAME | SAME | None |
| trim-148-over-240 | SAME | SAME | None |

Trim rows have no PCM note today; their future note assertions are RED even
though their current fidelity verdict is already green. The d86-70 case is the
rechunked integration RED; its real sink successfully preserves decoded bytes
before V4 runs. No fixture or derivative is committed.

Future pytest runs ALWAYS use the sandbox shim and file logging, e.g.
PowerShell env `PYTHONPATH=scripts`, `PYTEST_ADDOPTS` unset, then
`uv run pytest <nodes> --basetemp=work/wp-dr113/tmp/<fresh-run> -p sandbox_mkdir_shim -p no:cacheprovider`.
No pytest run occurred in round 0. Full-suite/three-leg gate and owner witness
remain at the dispatcher's seat after review convergence.

### 6. Disputes, recommended answers first

**R0-1 [MINOR, in envelope, confirmed baseline discrepancy]: Keep the required
DIFFERENT outcomes; classify sample-format-only and identical unknown-width
rows as additional REDs, rather than claiming every control is green today.**
The claim in Tests (2) that these are DIFFERENT today is false for identical
packet rows. `synthetic.log` shows BOTH the packet item and audio-presence item
SAME for a sole s16 -> s32 sample_fmt change and for an identical pcm_alaw pair.
This follows from `audio_layout`'s field list (`compare.py:1234`) and the old
packet comparison (`:1253`). No new product rule or scope is needed.

**R0-2 [MINOR, in envelope, confirmed integration classification]: Use d86-70
as the actual re-chunking RED; retain both trimmed-presentation variants as
baseline-green byte/presentation controls, with new PCM-note assertions RED.**
The unchanged instrument already calls both trimmed variants all MANDATORY
SAME (records and log above). Only the 70-percent recipe changes 50 packets to
49; the 55/85-percent source-only floor still makes their packet item RED.
The requested final behavior remains unchanged. Do not require a new derivative
recipe or claim the trimmed cases reproduce rechunking.

**R0-3 [MINOR, in envelope, confirmed documentation premise]: Add summary
disclosure for PCM only, preserving WP4.4's current note behavior and the bare
compare record schema.** WP4.4 translation is in Item.note, SAR/mono are silent
normalizations; none reaches `summary.notes` today. Base `build_record` has no
summary notes field (`compare.py:1636-1642`). The owned V4 `notes` path is where
this package should meet the new PCM disclosure requirement. No repair of old
equivalence note behavior is commissioned.

These are recommended rulings for the round-0 yield. No implementation is
started while the dispatcher's ruling is outstanding. No frozen-interface,
dependency, source-code or scope dispute was found. The broader content limit
is already explicitly out of scope: PCM totals/runs drop packet MD5 and do not
prove sample CONTENT. Report that limit; decoded-sample MD5 is a possible later
item, not built here (F-B2 remains out).

### Verification / handoff record

- Suspected stale anchors: confirmed their current locations above; no repair.
- Suspected missing PCM evidence: rejected as a need for Facts/probe expansion;
  existing independent probe document, packet fields and side-data read suffice.
- Suspected preexisting control failures: confirmed R0-1 by direct synthetic
  reproduction; baseline classification correction recommended, no code fix yet.
- Suspected integration RED mismatch: confirmed R0-2 with five real-sink
  derivative records; recommended witness/controls split above.
- Suspected note propagation premise: confirmed R0-3 by code tracing; no
  unrelated equivalence change proposed.
- No timing/memory figure is recorded. No full-suite/heavy/marked test run,
  owner-media read, main-tree work read, other-worktree access, local-config edit,
  dependency change, git write, mailbox post or out-of-envelope edit.
- Only this ledger is submitted for commit. Scratch reproduction code/media/logs
  stay ignored under this worktree's work directory. Round-0 yield is the handoff;
  future report/gate/review claims are not claimed complete here.
- Handoff checks: `git status --porcelain` lists only this untracked ledger;
  `git check-ignore` confirms scratch scripts and derivative records are ignored.
  `work/wp-dr113/round0/ledger-validation.log` records CR=0 and ASCII=True, plus
  measured derivative counts 39 -> 39, 50 -> 49, 61 -> 61, 71 -> 71 and 72 -> 72.
  uv's inherited VIRTUAL_ENV mismatch warning says it ignores the main-tree
  environment in favor of this worktree's .venv; its hardlink fallback was a
  copy warning, not a reproduction failure. Both reproduction commands exit 0.

## Turn 2: RED

Parent: `8e1d207d` (round 0 committed by the dispatcher). This turn adds tests
and records their baseline behavior. Instrument/product code is unchanged.
Incoming depth: 147,692 tokens. Depth after turn 2: PENDING DISPATCHER READING.
Reviewer A/B have not run; this is a RED rung, not review convergence or a gate.

### Adopted rulings (verbatim from the turn-2 dispatch)

- **R0-1 ADOPTED:** the sample-format-only row and the identical-unknown-width rows are additional REDs (they read SAME today); every other control is baseline-green. The required end state is unchanged: all read DIFFERENT.
- **R0-2 ADOPTED:** `d86-70` is the integration row that proves re-chunking; the two trimmed-presentation rows are baseline-green controls whose PCM-note assertions are RED; `d86-55` / `d86-85` are RED on the packet item (the source-only floor). Do not claim the trims re-chunk.
- **R0-3 ADOPTED:** the PCM note lives in `Item.note` (compare) AND reaches `video_fidelity`'s record `notes` for every PCM SAME; `compare.build_record`'s bare record schema is NOT changed; WP4.4's existing note behaviour is NOT changed.

### What was written and what each table plants

The 57 new parametrized nodes are all listed below with their observed results.
Eight test functions implement round 0's named rows, including its additional
compressed/mixed/absent controls. No tests were xfailed or skipped. Expected
outcomes and the note wording are fixed test values, not inferred from the
product verdict. The existing WP4.4 scaffold gains only `sample_fmt='s16'` so
that its declared PCM stream has usable format evidence when GREEN is built.

Current helper/consumer locations (these are the turn-2 files' lines):

- `tests/test_container_spike_compare_equivalences.py:273` `_pcm_pair`: common
  literal packet table builder; `:376` `_pcm_facts`: exact tick/byte conversion
  into independent Facts; `:403` audio-item selection; `:408` literal note form.
- Same file `:413` `_pcm_fidelity_reading`: real fidelity_items pipeline with
  ffprobe stream/packet documents supplied at the file boundary. It stubs only
  unrelated readable-video-end and mvhd-duration file reads. Real
  audio_configuration, audio_side_data, `_cut_items`, note collection and roster
  functions execute. No audio comparator is stubbed.
- Same file `:455` synthetic positives, `:471` difference controls, `:485`
  agreement, `:502` compressed/mixed/absent controls.
- `tests/test_video_fidelity.py:319` D86 positives, `:337` D86 partial controls,
  `:348` side-data controls.
- `tests/test_io_video_encode.py:499` ONE new real-sink V4 integration function
  with five parametrizations. It invokes the existing derivative recipes and
  their product-check/decoded-byte assertions, then adds the V4 checks. Its
  module ffmpeg_tools fixture and software libx265 path match its neighbors;
  no gpu, footage, slow or fullclip marker was added.

| Table / plant | Original source mechanic and base file:line | Test-side reproduction / expected outcome |
| --- | --- | --- |
| img6731-coalesced | `tests/test_io_video_encode_units.py:837-848` | Source durations `(1024*70,508,1024*23,736,1024*4,148)`, final stored 240; output `(1024*70,508,1024*27,884)`, final stored 976. 100 -> 99; totals 100720 presented / 100812 stored. SAME plus PCM note. |
| img6729-moved-boundary | `tests/test_io_video_encode_units.py:851-879` | Original 133-packet literal sequences retained; second 736-sample boundary moves by 1024 samples; final presentation/storage 291/305. Totals 134400/134414. SAME plus PCM note. |
| gapful-rechunked | `tests/test_io_video_encode_units.py:1137-1143` | Source durations 1024/508/1024 at 0/1024/2048; output 1532/512/512 at 0/2048/2560. Same runs [0,1532], [2048,3072]. SAME plus PCM note. |
| d86-55/70/85 | `tests/test_io_video_encode_units.py:1045-1058`, exercised at `:1061-1068` | Import `_truncated_pcm_pair`: source payload tails 909/860/647, strict output totals 38814/49502/60659 samples; 39/39, 50/49, 61/61 packets. SAME after SOURCE-only cap/final-frame floor, plus PCM note. |
| one-sample-fewer | `tests/test_io_video_encode_units.py:887-890` | Seven 1024-sample packets become six plus 1023 in output, both extent totals reduced. DIFFERENT. |
| presented-only | `tests/test_io_video_encode_units.py:893-900` | Last output declares 1023, still stores 1024. DIFFERENT. |
| stored-only | `tests/test_io_video_encode_units.py:903-910` | Last output stores 1023, still presents 1024. DIFFERENT. |
| rate / format | `tests/test_io_video_encode_units.py:913-925` | Output-only sample_rate 44100 or sample_fmt s32; packet table unchanged. DIFFERENT. |
| channels / time-base | `tests/test_io_video_encode_units.py:963-975` | Output-only channels 2 or time_base 1/96000. DIFFERENT. |
| codec-aac | Existing real PCM reencode control `tests/test_io_video_encode.py:325-331`; new synthetic mutation at `_pcm_pair` | Output-only codec_name aac with otherwise identical evidence. DIFFERENT via audio format/presence. |
| one-tick-shift | New synthetic mutation at `_pcm_pair` | Shift ONLY the fourth output packet's pts by one source tick; preserve both totals and first pts. DIFFERENT. |
| swapped-packets | New synthetic mutation at `_pcm_pair` | Swap output packet 2/3 pts in file order; preserve count, totals and first pts. DIFFERENT. |
| closed-gap / opened-gap | `tests/test_io_video_encode_units.py:1113-1134` | Reproduce its 72-packet run mutations: close a 1024-tick source gap after packet 30, or retain a 512-tick gap after 10 and add a 1024-tick gap after 30. DIFFERENT. |
| earlier-source-partial / output-partial | `tests/test_io_video_encode_units.py:1088-1098` | Use d86-70, plant first source payload 2047 or last output payload 1803. DIFFERENT; neither floor is permitted. |
| unknown-alaw/mulaw/bluray/dvd/lxf/s24daud/sga/vidc/unlisted | New synthetic mutations at `_pcm_pair`, named refused set from brief | BOTH streams use the same unknown-width codec and identical packet rows. DIFFERENT despite equality, with codec named in the failure note. |
| discard / side-data | New ffprobe-document plants in `_pcm_fidelity_reading`; real `video_fidelity.audio_side_data` consumes them | Identical valid PCM packet tables, output packet 2 gains discard flag KD or Skip Samples side data with skip_samples 1. Packet item SAME, side-data item DIFFERENT under fallback. |
| compressed-intact/rechunked/mixed/absent | New literal Facts in `test_pcm_compressed_and_absent_paths_unchanged` | AAC exact rows SAME; merged AAC packets DIFFERENT; changed AAC payload hash alongside unchanged PCM DIFFERENT; absent audio retains absent/absent SAME and empty note. Compressed source/output summaries and first-difference notes are checked too. |
| trim-380-over-472 / trim-148-over-240 | `tests/test_io_video_encode.py:410-492` (unchanged original function) | Reuse setts and optional atrim/asetnsamples derivative; actual counts 72/72 and 71/71. Product/decoded-byte/V4 controls pass today; new PCM-note assertion fails. |
| integration d86-55/70/85 | `tests/test_io_video_encode.py:337-402` (unchanged original function) | Faststart committed fixture, byte-prefix cuts at test time, real sink and decoded bytes assertions. Independently assert actual packet counts 39/39, 50/49, 61/61 before V4; d86-70 explicitly proves re-chunking. V4 must be all MANDATORY+REQUIRED/roster SAME with PCM notes. |

All imports of `test_io_video_encode_units` and product PacketTable/checking
helpers are in TESTS only. `_pcm_check` (`tests/test_io_video_encode_units.py:803`)
reaches the real `verify.check_output` (`:818`), with only unrelated file-box
checking stubbed. Each agreement row asserts the product's hand-specified
expected verdict, instrument SAME <-> product pass, and the instrument's expected
verdict. The instrument runs its own compare_facts and its own `_cut_items`
when cut. `tools/` imports and implementations were not edited.

### Commands and observed results

PowerShell setup for EVERY pytest command below:

```powershell
$env:PYTHONPATH='scripts'
$env:PYTEST_ADDOPTS=$null
```

The first new-node command (all 57 new nodes, once):

```text
uv run pytest -vv --tb=short tests/test_container_spike_compare_equivalences.py::test_pcm_sample_extent_equivalence tests/test_container_spike_compare_equivalences.py::test_pcm_difference_control tests/test_container_spike_compare_equivalences.py::test_pcm_instrument_agrees_with_product tests/test_container_spike_compare_equivalences.py::test_pcm_compressed_and_absent_paths_unchanged tests/test_video_fidelity.py::test_pcm_d86_sample_extent_equivalence tests/test_video_fidelity.py::test_pcm_d86_difference_control tests/test_video_fidelity.py::test_pcm_side_data_control tests/test_io_video_encode.py::test_pcm_derivative_v4_through_real_sink --basetemp=work/wp-dr113/tmp/t2 -p sandbox_mkdir_shim -p no:cacheprovider --junitxml=work/wp-dr113/t2/red.xml > work/wp-dr113/t2/red.log 2>&1
```

Initial output: **32 failed, 25 passed** (exit 1). Seven failures were UNRELATED
synthetic setup failures, not legitimate RED evidence: `movie_duration_item`
called `movie_duration` (`tools/video_fidelity.py:1037`, `:581`), which tried to
open synthetic source.mov. Reproduced in all seven fidelity-module new nodes;
the real-sink rows did not have the problem. After tracing that file-read
boundary, added one stub for the unrelated mvhd duration read (1/2 second).
The existing real audio reading, cut helper and side-data reader stay real.

Only those seven affected nodes were rerun, as the dispatch requires for an
unrelated failure. A fresh basetemp preserves the first run's integration media:

```text
uv run pytest -vv --tb=short tests/test_video_fidelity.py::test_pcm_d86_sample_extent_equivalence tests/test_video_fidelity.py::test_pcm_d86_difference_control tests/test_video_fidelity.py::test_pcm_side_data_control --basetemp=work/wp-dr113/tmp/t2-setupfixed -p sandbox_mkdir_shim -p no:cacheprovider --junitxml=work/wp-dr113/t2/red-setupfixed.xml > work/wp-dr113/t2/red-setupfixed.log 2>&1
```

Corrected output: **3 failed, 4 passed** (exit 1). Every failure is now the
intended packet-item DIFFERENT-versus-SAME assertion. The earlier-source partial,
output partial, discard flag and planted side-data controls all pass. The
corrected seven outcomes supersede their seven initial setup failures below.
No other new node was rerun.

Combined, valid new-node evidence is **28 RED / 29 baseline GREEN**, 57 unique
nodes. There are no unresolved import, fixture, typo, file-read or setup errors.
The first run's other failures are the intended per-packet refusals, ignored
sample_fmt/unknown-width refusals, product/instrument disagreement or empty PCM
notes. The product verdict assertion succeeded for all 17 agreement rows before
the instrument assertion. The five integration recipes passed all their old
product/decoded-byte assertions before the newly added V4/note assertions.

Existing light regression command (new functions deselected to honor the
new-node-once requirement; marker exclusions honor the cell's prohibition on
gpu/footage/slow/fullclip runs):

```text
uv run pytest -q tests/test_container_spike_compare_equivalences.py tests/test_video_fidelity.py tests/test_io_video_encode.py -k "pcm or audio or equival" -m "not gpu and not footage and not slow and not fullclip" --deselect tests/test_container_spike_compare_equivalences.py::test_pcm_sample_extent_equivalence --deselect tests/test_container_spike_compare_equivalences.py::test_pcm_difference_control --deselect tests/test_container_spike_compare_equivalences.py::test_pcm_instrument_agrees_with_product --deselect tests/test_container_spike_compare_equivalences.py::test_pcm_compressed_and_absent_paths_unchanged --deselect tests/test_video_fidelity.py::test_pcm_d86_sample_extent_equivalence --deselect tests/test_video_fidelity.py::test_pcm_d86_difference_control --deselect tests/test_video_fidelity.py::test_pcm_side_data_control --deselect tests/test_io_video_encode.py::test_pcm_derivative_v4_through_real_sink --basetemp=work/wp-dr113/tmp/t2-light -p sandbox_mkdir_shim -p no:cacheprovider --junitxml=work/wp-dr113/t2/light.xml > work/wp-dr113/t2/light.log 2>&1
```

Result: **56 passed, 187 deselected** (exit 0). The JUnit node sets prove zero
overlap with the new-node set. No existing selected light test broke. This is
the authorized light evidence, not a full suite or hardware gate.

### Per-node results before GREEN

| Node ID | Before GREEN | Observed reason |
| --- | --- | --- |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_sample_extent_equivalence[img6731-coalesced]` | RED | P: old packet rows DIFFERENT for faithful re-chunking |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_sample_extent_equivalence[img6729-moved-boundary]` | RED | P: old packet rows DIFFERENT for faithful re-chunking |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_sample_extent_equivalence[gapful-rechunked]` | RED | P: old packet rows DIFFERENT for faithful re-chunking |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_difference_control[one-sample-fewer]` | GREEN | C: planted format/extent/timeline difference caught |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_difference_control[presented-only]` | GREEN | C: planted format/extent/timeline difference caught |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_difference_control[stored-only]` | GREEN | C: planted format/extent/timeline difference caught |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_difference_control[rate]` | GREEN | C: planted format/extent/timeline difference caught |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_difference_control[format]` | RED | F: old audio items both SAME for changed sample_fmt |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_difference_control[channels]` | GREEN | C: planted format/extent/timeline difference caught |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_difference_control[codec-aac]` | GREEN | C: planted format/extent/timeline difference caught |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_difference_control[time-base]` | GREEN | C: planted format/extent/timeline difference caught |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_difference_control[one-tick-shift]` | GREEN | C: planted format/extent/timeline difference caught |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_difference_control[swapped-packets]` | GREEN | C: planted format/extent/timeline difference caught |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_difference_control[closed-gap]` | GREEN | C: planted format/extent/timeline difference caught |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_difference_control[opened-gap]` | GREEN | C: planted format/extent/timeline difference caught |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_difference_control[unknown-alaw]` | RED | U: old audio items both SAME for identical unknown-width PCM |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_difference_control[unknown-mulaw]` | RED | U: old audio items both SAME for identical unknown-width PCM |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_difference_control[unknown-bluray]` | RED | U: old audio items both SAME for identical unknown-width PCM |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_difference_control[unknown-dvd]` | RED | U: old audio items both SAME for identical unknown-width PCM |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_difference_control[unknown-lxf]` | RED | U: old audio items both SAME for identical unknown-width PCM |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_difference_control[unknown-s24daud]` | RED | U: old audio items both SAME for identical unknown-width PCM |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_difference_control[unknown-sga]` | RED | U: old audio items both SAME for identical unknown-width PCM |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_difference_control[unknown-vidc]` | RED | U: old audio items both SAME for identical unknown-width PCM |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_difference_control[unknown-unlisted]` | RED | U: old audio items both SAME for identical unknown-width PCM |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_instrument_agrees_with_product[img6731-coalesced]` | RED | A+: product PASS, old instrument DIFFERENT |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_instrument_agrees_with_product[img6729-moved-boundary]` | RED | A+: product PASS, old instrument DIFFERENT |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_instrument_agrees_with_product[gapful-rechunked]` | RED | A+: product PASS, old instrument DIFFERENT |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_instrument_agrees_with_product[d86-55]` | RED | A+: product PASS, old instrument DIFFERENT |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_instrument_agrees_with_product[d86-70]` | RED | A+: product PASS, old instrument DIFFERENT |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_instrument_agrees_with_product[d86-85]` | RED | A+: product PASS, old instrument DIFFERENT |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_instrument_agrees_with_product[one-sample-fewer]` | GREEN | A=: product REFUSES and instrument DIFFERENT, expected refusal asserted |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_instrument_agrees_with_product[presented-only]` | GREEN | A=: product REFUSES and instrument DIFFERENT, expected refusal asserted |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_instrument_agrees_with_product[stored-only]` | GREEN | A=: product REFUSES and instrument DIFFERENT, expected refusal asserted |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_instrument_agrees_with_product[rate]` | GREEN | A=: product REFUSES and instrument DIFFERENT, expected refusal asserted |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_instrument_agrees_with_product[format]` | RED | A-: product REFUSES sample_fmt change, old instrument SAME |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_instrument_agrees_with_product[channels]` | GREEN | A=: product REFUSES and instrument DIFFERENT, expected refusal asserted |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_instrument_agrees_with_product[time-base]` | GREEN | A=: product REFUSES and instrument DIFFERENT, expected refusal asserted |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_instrument_agrees_with_product[closed-gap]` | GREEN | A=: product REFUSES and instrument DIFFERENT, expected refusal asserted |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_instrument_agrees_with_product[opened-gap]` | GREEN | A=: product REFUSES and instrument DIFFERENT, expected refusal asserted |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_instrument_agrees_with_product[earlier-source-partial]` | GREEN | A=: product REFUSES and instrument DIFFERENT, expected refusal asserted |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_instrument_agrees_with_product[output-partial]` | GREEN | A=: product REFUSES and instrument DIFFERENT, expected refusal asserted |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_compressed_and_absent_paths_unchanged[compressed-intact]` | GREEN | B: compressed strict rows/notes or absent-audio item preserved |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_compressed_and_absent_paths_unchanged[compressed-rechunked]` | GREEN | B: compressed strict rows/notes or absent-audio item preserved |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_compressed_and_absent_paths_unchanged[mixed]` | GREEN | B: compressed strict rows/notes or absent-audio item preserved |
| `tests/test_container_spike_compare_equivalences.py::test_pcm_compressed_and_absent_paths_unchanged[absent]` | GREEN | B: compressed strict rows/notes or absent-audio item preserved |
| `tests/test_video_fidelity.py::test_pcm_d86_sample_extent_equivalence[d86-55]` | RED | D: old cut packet item DIFFERENT for faithful normalized tail |
| `tests/test_video_fidelity.py::test_pcm_d86_sample_extent_equivalence[d86-70]` | RED | D: old cut packet item DIFFERENT for faithful normalized tail |
| `tests/test_video_fidelity.py::test_pcm_d86_sample_extent_equivalence[d86-85]` | RED | D: old cut packet item DIFFERENT for faithful normalized tail |
| `tests/test_video_fidelity.py::test_pcm_d86_difference_control[earlier-source-partial]` | GREEN | Q: earlier-source/output partial frame remains DIFFERENT |
| `tests/test_video_fidelity.py::test_pcm_d86_difference_control[output-partial]` | GREEN | Q: earlier-source/output partial frame remains DIFFERENT |
| `tests/test_video_fidelity.py::test_pcm_side_data_control[discard]` | GREEN | S: packet item SAME, planted priming/side-data item DIFFERENT |
| `tests/test_video_fidelity.py::test_pcm_side_data_control[side-data]` | GREEN | S: packet item SAME, planted priming/side-data item DIFFERENT |
| `tests/test_io_video_encode.py::test_pcm_derivative_v4_through_real_sink[trim-380-over-472]` | RED | N: V4 already passes; required PCM Item.note is empty |
| `tests/test_io_video_encode.py::test_pcm_derivative_v4_through_real_sink[trim-148-over-240]` | RED | N: V4 already passes; required PCM Item.note is empty |
| `tests/test_io_video_encode.py::test_pcm_derivative_v4_through_real_sink[d86-55]` | RED | I: real sink PASS/decoded bytes equal; V4 packet item DIFFERENT |
| `tests/test_io_video_encode.py::test_pcm_derivative_v4_through_real_sink[d86-70]` | RED | I70: real sink PASS/decoded bytes equal; BOTH V4 audio items DIFFERENT |
| `tests/test_io_video_encode.py::test_pcm_derivative_v4_through_real_sink[d86-85]` | RED | I: real sink PASS/decoded bytes equal; V4 packet item DIFFERENT |

### Checks, verification loop and fresh-session handoff

`uv run ruff format` initially formatted the new compare tests; after all edits,
the required targeted checks are:

```text
uv run ruff check tests/test_container_spike_compare_equivalences.py tests/test_video_fidelity.py tests/test_io_video_encode.py > work/wp-dr113/t2/ruff-final.log 2>&1
uv run ruff format --check tests/test_container_spike_compare_equivalences.py tests/test_video_fidelity.py tests/test_io_video_encode.py > work/wp-dr113/t2/format-final.log 2>&1
uv run python work/wp-dr113/t2/report_results.py > work/wp-dr113/t2/results-summary.log 2>&1
git diff --check
```

The results-summary script merges the actual JUnit outcomes, rejects any remaining
non-AssertionError RED, asserts 57 unique new nodes / 28 RED / 29 GREEN, checks
56 distinct passing old nodes, and validates ASCII plus CR=0 on all four submitted
files. Ruff check/format final results and scope are recorded at the turn's final
verification below. The formatter preserved CRLF in the working test files;
normalization converted only those three owned test files to LF without changing
their logical contents. No behavior-changing edit followed the test evidence.

Verification-loop record:

- Expected packet-boundary REDs: CONFIRMED on three whole-source shapes, three
  synthetic D86 shapes and three real D86 derivatives.
- Adopted extra REDs: CONFIRMED sample_fmt-only plus nine identical unknown-width
  codecs. Unknown codec-name notes remain required assertions for GREEN.
- Product agreement: CONFIRMED all 17 product verdicts match expected outcomes;
  six faithful pairs and the sample_fmt control currently disagree with V4.
- Trimmed derivatives: CONFIRMED both remain baseline-green V4 controls; new
  PCM-note assertions fail. No claim that either trim re-chunks.
- Unrelated synthetic file-read failure: CONFIRMED mvhd read, FIXED in test setup;
  bounded rerun confirms all seven now have intended outcomes. No remaining
  unrelated test failure is counted as RED.
- Strict compressed, mixed/absent and all other controls: CONFIRMED 29 new
  baseline-green controls; existing selected light tests also pass.
- Scope: only the three owned test files and this ledger changed. No tools/src,
  dependency, fixture-media, register, local-config, frozen-interface or mailbox
  change. No owner-media or other-worktree read, and no heavy/marked node run.

Next rung belongs to a fresh GREEN session if the dispatcher re-seats this cell.
Use round 0's independent width table and note/roster locks, the adopted rulings
above, and THESE executable RED rows. Do not import product audio verification
into tools. Preserve the compressed/audio-side fallback and other item behavior.
Keep the sample CONTENT limitation explicit in the later report (decoded-sample
MD5 remains outside this commission). Reviewer A/B, full gate, report and owner
PCM witness remain outstanding at their commissioned rungs/seats.

Final verification: targeted ruff check exits 0, `All checks passed!`
(`work/wp-dr113/t2/ruff-final.log`); targeted format --check exits 0,
`3 files already formatted` (`format-final.log`). The results-summary validates
all four files as ASCII with CR=0, 57 unique new nodes with valid outcomes, and
56 distinct passing existing nodes (`results-summary.log`). `git diff --check`
is clean; `git status --short` names exactly these three tests and this ledger.
This turn is one logical RED-test change; no implementation or completion of
the overall package is claimed. No STOP/dispute remains for this rung.
