# WP-D112 cumulative ledger

## Round 0

Base: `7d48e26a`, branch `wp-d112`. Mapping and synthetic experiments only.
No product code, existing test, generator, manifest or committed fixture changed.
All line anchors below refer to this base. Evidence is under this worktree's
`work/wp-d112/`; no owner's footage or another worktree was opened.

Depth: PENDING -- dispatcher to fill from the transcript; no cell estimate.

### 1. Anchors and unchanged readers

| Anchor | Location | Mechanic / implication |
| --- | --- | --- |
| `CUT_SLACK_S` | `src/clearwater/io/video/verify.py:51` | Two microseconds around an input cut; keep this convention. |
| `_STREAM_ENTRIES` | `src/clearwater/io/video/verify.py:56` | Currently lacks codec name, rate, channels and sample format. |
| `_PACKET_ENTRIES` | `src/clearwater/io/video/verify.py:63` | Currently requests `stream_index,pts,flags`, no duration. |
| `StreamRow` | `src/clearwater/io/video/verify.py:108` | Existing fields end with defaulted `frames`; append defaulted facts only. |
| `PacketTable` | `src/clearwater/io/video/verify.py:139` | `audio_pts` at 166; preserve its meaning and existing defaults. |
| `read_packet_table` | `src/clearwater/io/video/verify.py:486` | Stream listing at 507, selected audio listing at 535, construction at 543 and 564. |
| `check_output` | `src/clearwater/io/video/verify.py:767` | Audio roster at 815; paired-stream loop at 822 calls `_audio_problems` at 823. |
| `_audio_problems` | `src/clearwater/io/video/verify.py:838` | Whole/cut packet-count interval, then exact prefix pts equality; leave this compressed rule unchanged. |
| Existing mismatch unit row | `tests/test_io_video_encode_units.py:707` | `test_check_output_names_each_mismatch`; existing AAC messages stay byte-for-byte compatible. |
| Existing cut unit row | `tests/test_io_video_encode_units.py:726` | `test_a_cut_audio_stream_must_be_the_source_packets_before_the_cut`; preserve every assertion. |
| Existing planted re-encode row | `tests/test_io_video_encode.py:1547` | `test_planted_audio_reencode_is_caught`; AAC source, real sink with `-c:a aac` planted; sink refusal or fidelity difference is required. |
| Real sink command | `src/clearwater/io/video/encode.py:402` | `-copyts`, NUT `pipe:0` input at 408-410, original source as second input, `-c:a copy` at 427, MP4 flags at 440. Read only; no change authorized. |
| Sink read-back | `src/clearwater/io/video/encode.py:1091` | Strict output table, then `check_output` at 1096. Source table is read at 668. |

Complete `rg` search of `src/` and `tests/` for `audio_pts`, `_STREAM_ENTRIES`
and `_PACKET_ENTRIES`: entry strings are used only inside `verify.py` (507,
523, 536). `audio_pts` is declared/read/written only there (150, 166, 514,
535-541, 577, 825-826), plus the existing unit table constructors at
`tests/test_io_video_encode_units.py:99` and `:692`. No other reader exists.
Evidence search: `work/wp-d112/table-readers.txt`.

Proposed internal additions: defaulted `StreamRow.codec_name`, `sample_rate`,
`channels`, `sample_fmt`, and defaulted `PacketTable.audio_durations` aligned
one-for-one with the existing `audio_pts`. Extend the two listing strings to
read these facts and packet `duration`. Existing positional constructors and
compressed/video/data behavior remain compatible. Missing or non-integral PCM
sample evidence must refuse with a PCM message rather than silently use an
aggregate or the compressed rule.

### 2. Manifest consumers and fixture consequences

Search coverage: literal manifest paths, `load_manifest`, `fixture_manifest`,
`sample_ids`, `sample_entry`, `sample(...)`, `VIDEO_IDS`, video ids and direct
fixture paths across `src/`, `tests/`, `tools/`. Raw inventories:
`work/wp-d112/consumers.txt`, `direct-consumers.txt`, `manifest-refs.txt`, and
`sample-call-sites.json`. No product module reads the fixtures manifest.

#### Manifest-wide or all-video consumers

| Consumer (file:line) | What it asserts / does per sample | Effect of one new committed PCM MOV |
| --- | --- | --- |
| `tools/fixtures/generate.py:50` | Builds selected groups, collects entries; full build writes sorted validated manifest at 86. | Video group gains one entry; no generator-dispatch edit needed. |
| `tools/fixtures/manifest.py:220`, `:328`, `:375` | Builds and validates every entry, expectation field names against frozen dataclasses, ids, limits, fault names. | New entry validated; `kind="mov"` is permitted (kind is descriptive, not an MP4 enum). No schema/interface edit. |
| `tools/fixtures/manifest.py:411` | Every committed file's presence, size, optional md5, no unlisted files; individual and aggregate caps. | New file included; record measured facts/size and keep below caps. |
| `tests/fixture_plugin.py:51`, `:127`, `:160`, `:168`, `:268`, `:281`, `:297`, `:303`, `:309` | Loads/validates all entries, indexes by id, filters ids, hands out committed paths and fails on missing files; generated verification applies to generated storage only. | New id available without generating it. No fixed inventory or codec expectation; no edit. |
| `tests/test_fixtures.py:45`, `:48`, `:70`, `:75`, `:83` | Reads all entries; validates JSON, sorted ids, ASCII serialization and on-disk identity. | Included automatically; manifest must be written by established serializer. |
| `tests/test_fixtures.py:87` | Exact inventory and explicit eight video ids at 103. | NEEDS EDIT: append new id to explicit expected video set; `video.SPECS` must include it. |
| `tests/test_fixtures.py:116` | Each entry's faults equal named exceptions, otherwise none. | New clean PCM entry expects no faults; no edit. |
| `tests/test_fixtures.py:220`, `:233`, `:241`, `:249`, `:261` | Mutated manifests and copied fixture trees catch invalid entries, oversize, total cap, missing/changed files; exact cap constants. | Includes new file automatically; planted targets remain named existing samples. No expectation edit. |
| `tests/test_fixtures.py:527` | Scans every committed file's bytes for XMP/GPS findings. | Scans MOV as well; must remain synthetic and metadata-free. No edit. |
| `tests/test_fixtures.py:619` | All `VIDEO_IDS` are treated as MP4s; explicitly requires eight, empty udta/meta, and presence of udta. | NEEDS EDIT: filter this MP4-specific test to `.mp4`, retaining its eight MP4 expectations. MOV stays covered by general privacy scan. |
| `tests/test_fixtures.py:979` | Parametrized `test_video_is_what_the_manifest_says`: remeasures each video, finds its `Spec`, compares every measured fact, `mismatches`, `expectation`, independent `_probe_view`. | One new case automatically; add matching Spec and PCM-aware intent. Existing row itself needs no edit. |
| `tests/test_fixtures.py:992` | Iterates all video ids; measures colour/VUI; named tag controls and signal-type flags on all tagged clips. | New BT.709-tagged video included automatically; no edit. |
| `tests/test_fixtures.py:1049` | Named rotated clip is 90 degrees; every other video has zero rotation. | New MOV is zero rotation; no edit. |
| `tests/test_fixtures.py:1071` | Iterates every video: currently hard-codes AAC, no data streams, no location. | NEEDS EDIT: PCM-specific codec expectation for new id; preserve old AAC expectations and no-data/no-location checks. |
| `tests/test_fixtures.py:1390` | Full regeneration's manifest equals committed bytes; intermediates removed; generated root contains no video group. | New entry/file comes from `video.build`; no assertion edit if generation remains deterministic. |
| `tests/test_fixtures.py:1403` | Iterates all video ids and compares regenerated/committed decoded video hashes and pts hashes. | New decoded-frame case in the loop; no edit. Audio packet facts need separate PCM assertions. |
| `tests/test_fixtures.py:1443`, `:1516`, `:1529`, `:1560` | Generator sources cannot access footage; audited whole generation reads/writes/spawns only under permitted roots. | New recipe is exercised in full audit. Absolute MOV paths are already audited; no assertion edit needed. |
| `tests/test_jobs_naming.py:516`, `:525` | Every manifest path x two planners x photo/video x beside/out uses original extension for VIDEO. | Eight new cases; FOUR video cases FAIL because a MOV correctly becomes `.mp4`. NEEDS EDIT of this expectation, pending ruling. Existing dedicated MOV test at 543 already expects MP4. |

`expectation()` at `tools/fixtures/video.py:591` and `mismatches()` at `:629`
both hard-code AAC (624, 659-661). They need a defaulted per-Spec audio codec
field (`"aac"` for all existing Specs; `"pcm_s16le"` for the new one), consumed
by both functions. No new field in frozen `ProbeResult`/`AudioStreamInfo` is
needed. `measure()` at 494 already measures codec/rate/channels; add a PCM-only
facts block with sample format and audio packet pts/durations so the manifest
actually records and regeneration checks the two irregular mid-stream packets.
`build()` at 704 currently hard-codes `.mp4` at 730 and `kind="mp4"` at 783;
new recipe needs `.mov` and the corresponding kind, inside this owned file.

#### Named video consumers (no automatic new cases or expectation changes)

The following consumers use named ids or fixed id lists rather than discovering
all video entries. File:line identifies the id roster or sample call; their
existing assertions continue on the same samples.

| Consumer | Per-sample purpose |
| --- | --- |
| `tests/test_io_video_probe.py:29`, `:86`, `:154`, `:274` | Fixed eight-video roster: probe fields/faults exactly match manifest; intact/truncated/HDR, tags, rotations and malformed plants. New id is not in this roster. |
| `tests/test_io_video_decode.py:36`, `:108`, `:136`, `:140`, `:248`, `:262`, `:283` | Fixed decodable/refused/intact lists: pixels, frame counts, order, exact pts/hash, colour and decode failure rules. |
| `tests/test_io_video_decode_hw.py:29`, `:64` | Fixed synthetic decode roster, CPU/CUDA agreement. |
| `tests/test_io_video_decode_rules.py:41`, `:119`, `:140` | Named HEVC control for decoder ordering/time-base/fault plants. |
| `tests/test_io_video_decode_lifecycle.py:39`, `:74`, `:456` | Fixed roster and named controls: early-close, cancellation, stream resources, fallback pixels/pts parity. |
| `tests/test_color_swscale.py:37`, `:94`, `:262`, `:349` | Fixed colour-conversion argument roster, HDR refusal and untagged colour rules. |
| `tests/test_color_roundtrip.py:67`, `:68`, `:172`, `:194`, `:206` | Fixed three round-trip and three regression samples; AD-11 pixel tolerances and colour plants. |
| `tests/test_io_video_encode.py:54`, `:73`, `:249`, `:254` | Fixed DECODABLE roster x encoders/depths; V4 mandatory/required fidelity, frames and bit depth. Add new id explicitly here for the new V4 cases. Remaining named controls (264 onward) do not discover it. |
| `tests/test_video_fidelity.py:61`, `:94`, `:244` | Named VFR fixture validates fidelity report/CLI and adversarial comparisons. |
| `tests/test_jobs_export_video.py:52`, `:161`, `:173`, `:198` | Fixed decodable/refused rosters; product-engine V4 output/failure behavior. |
| `tests/test_analysis_breakdown.py:107`, `:172`, `:195`, `:316` | Named SAMPLE: instrument decomposition, optional profiling/frame logs and output safety. |
| `tests/test_export_bench.py:80`, `:122`, `:160`, `:237` | Named SAMPLE: bench runner/records, output retention and refusal safety. |
| `tests/test_export_oracle.py:87`, `:102`, `:210` | Named SAMPLE: oracle recording/comparison and refusal safety. |
| `tests/test_io_video_encode_bench.py:275`, `:339`, `:373`, `:404`, `:459`, `:506`, `:528`, `:555`, `:594`, `:635`, `:710`, `:732` | Named SAMPLE: encode bench CLI, metrics/record validation and output safety. |
| `tests/test_wp321_bench.py:40` | Named SAMPLE for device-frame bench report. |
| `tests/test_wp321_device_frames.py:33`, `:185`, `:195`, `:207`, `:245`, `:331`, `:358` | Fixed SAMPLES and named VFR control: host/device frames, pixel parity, sink behavior and cleanup. |
| `tests/test_wp321_fft_release.py:145`, `:232`, `:241`, `:248`, `:261` | Named SAMPLE: GPU pool-release boundary, failure and cancellation. |
| `tests/test_wp42_composition.py:155` | Named HEVC fixture verifies real composition adapters. |
| `tests/test_wp42_device_backend.py:281` | Named HEVC fixture verifies device/backend propagation. |
| `tests/test_wp42_runner_video.py:60` | Fixed sample-id parametrization: headless video runner behavior. |
| `tests/test_wp42_video_path.py:122`, `:181`, `:431`, `:490`, `:533`, `:635` | Named CLIP/rotated/truncated or fixed cases: analysis/render/export, V9 pixels, stats, cancellation, batch/cache behavior. |
| `tests/test_app_analysis_adapter.py:161` | Named truncated clip verifies analysis adapter faults. |
| `tests/test_app_leftovers.py:424` | Named HEVC bytes verify video crash-leftover cleanup. |
| `tests/test_app_startup.py:145`, `:361` | Named HEVC/CLIP: startup and responsive open-source wiring. |
| `tests/test_app_activity.py:220`, `:435`, `:462`, `:505` | Named CLIP: source activity/exclusion and export interactions. |
| `tests/test_app_wiring.py:141`, `:201`, `:286`, `:386`, `:434`, `:465`, `:533`, `:740` | Named CLIP/fixed case lists: source routing, GUI/export/batch wiring, source guards, cache invalidation. |
| `tests/test_v51_shell_acceptance.py:57` | Named untagged fixture: shell warning acceptance. Never edit. |
| `tests/test_v51_video_acceptance.py:65`, `:105`, `:147`, `:246`, `:272`, `:321`, `:379`, `:397`, `:417`, `:461`, `:555`, `:576` | Fixed FIXTURES and named clips: video acceptance, V4/G10, cancellation, runner behavior. Never edit. |

Other manifest loaders explicitly exclude video: `tests/test_io_photo_read.py:35-36`,
`tests/test_io_photo_write.py:34`, `tests/test_wp41_photo_path.py:39-41` select
`group == "stills"`; `tests/test_v51_photo_acceptance.py:363` filters stills
for a maximum-area assertion. `tests/test_fixture_cache_lock.py:68`, `:136`
loads the whole manifest but requests only named `ad14-flicker` for locking
and regeneration. The plugin test at `tests/test_fixtures.py:1601` requests
named committed files and `ids("files")`. None gains a video case or needs edits.
No `sample_ids("video")` consumer exists; the only test caller selects `files`
at `tests/test_io_video_probe.py:528`.

V4 sweep module/node:
`tests/test_io_video_encode.py::test_every_sample_keeps_every_mandatory_and_required_item`
(249-261). Its `Runs.get` (96) calls `video_fidelity.encode_file` (350), whose
`_RecordingSink` subclasses the real `FFmpegVideoSink` (305); `sink.open` /
`write` / `close` are at 381-386. This is the real two-input NUT path, not an
FFmpeg command emulation. Add `vid-pcm-irregular: 8` to DECODABLE for V4 and
a focused `test_pcm_irregular_audio_survives_the_real_sink` row using this path,
decoded audio equality, packet/format measurements and the mandatory check.

### 3. Sample-count source and cut rule

Choice: per-packet ffprobe `duration`. Convert each duration in stream ticks to
sample frames with exact `Fraction(duration) * time_base * sample_rate`, require
an integral nonnegative result and sum it. A sample frame counts one temporal
sample in every channel, not the sum of channel scalars. This permits cuts by
source packet start and survives packet splitting/coalescing. `nb_frames` and
`duration_ts` are useful cross-checks, not the chosen count: neither tells which
source packet durations lie before a cut, and an unreadable tail can leave
container aggregates describing unreadable data.

Measured with FFmpeg 9.0.2 full Gyan build, all synthetic:

| File under `work/wp-d112/tmp/` | Tag / rate / format | Packet count | Sum of packet durations in samples | nb_frames / duration_ts | Decoded samples |
| --- | --- | --- | --- | --- | --- |
| `pcm-irregular.mov` | sowt / 48000 / s16 / mono | 72 | 72072 | 72072 / 72072 | 72072 |
| `pcm-remux.mp4` | ipcm / 48000 / s16 / mono | 72 | 72072 | 72072 / 72072 | 72072 |
| `out/pcm-irregular_corrected.mp4` (PRODUCT) | ipcm / 48000 / s16 / mono | 72 | 72072 | 72072 / 72072 | 72072 |
| `pcm-coalesced.mp4` (synthetic repacketization control) | ipcm / 48000 / s16 / mono | 71 | 72072 | 72072 / 72072 | 72072 |
| `pcm-96k.mov` | lpcm / 96000 / s16 / mono | 141 | 144144 | 144144 / 144144 | 144144 |
| `pcm-96k.mp4` | ipcm / 96000 / s16 / mono | 141 | 144144 | 144144 / 144144 | 144144 |
| `pcm-96k-coalesced.mp4` | ipcm / 96000 / s16 / mono | 141 | 144144 | 144144 / 144144 | 144144 |

For every measured packet, `duration * time_base * sample_rate` also equals
packet `size / (2 * channels)`. The 48 kHz files decode to identical 144144
bytes, SHA-256 `086691f53b341fa75ff0765698cb9ae70cd0af370fb1f3cb00282f7b1dfdf6f8`.
The 96 kHz files decode to identical 288288 bytes, SHA-256
`e31cae9fb2caadd53649c06e157cb221f22da5a2d891454371c6c33e7f61753f`.
The MOV `lpcm`/MP4 `ipcm` copy moves two boundaries from pts 49120/97168
to 51168/99216 (duration 944 each); the sum stays exact. The coalesced 48 kHz
control removes both short mid-stream packets: 70 x 1024 plus a final 392,
instead of three groups of 23 x 1024 plus 472. Its unchanged sample bytes are
refused by today's full `check_output` with
`audio stream 0: 71 packets in the output where 72 of the source's 72 were to be copied`.
This independently confirms the check defect without bypassing a product check.
The explicit `-tag:a lpcm` trial on 48 kHz was normalized by FFmpeg back to
`sowt`; a separate 96 kHz MOV supplies actual `lpcm` evidence, with no tag spoof.

Evidence: `tmp/facts.json`, `tmp/more-facts.json`, `tmp/lpcm-facts.json`,
`tmp/check-evidence.json`, full `*.mov.json` / `*.mp4.json` packet tables,
and `tmp/commands.log`. Summary logs: `experiment.log`, `measure-more.log`,
`lpcm-measure.log`, `check-evidence.log`. All experiments exited 0.

Cut semantics: count an ENTIRE source packet when its START is before the cut,
including a packet straddling it. Example source durations `[1024, 508, 1024]`,
pts `[0, 1024, 1532]`, cut `1200/48000`: expected 1532 samples, not 1200.
Keep/drop ambiguity is only for source packet starts within `CUT_SLACK_S`, as
today. Accept only the complete admissible PREFIX TOTALS, not every integer
between the smallest/largest total: at cut `1024/48000`, admissible totals are
1024 and 1532, and 1025 must refuse. Count every output packet; also compare
first packet pts, time base, sample rate, channels and sample format, with the
rule named `audio stream 0 (PCM)` in refusals. No tolerance in the sample count.

### 4. Fixture recipe and real export experiment

Candidate id/path: `vid-pcm-irregular`, `video/pcm-irregular.mov`.
Recipe prototype: `work/wp-d112/tmp/experiment.py`; exact commands/stderr:
`work/wp-d112/tmp/commands.log`.

1. Generate 45 frames of `testsrc2=size=320x180:rate=30000/1001` with
   libx265, no B frames or version SEI, BT.709 limited tags, yuv420p,
   `-video_track_timescale 30000`, `-fflags +bitexact`, `-flags:v +bitexact`,
   and `-map_metadata -1`; audio is supplied separately.
2. Generate three audio-only MOV segments, each sine 440 Hz, mono 48000 Hz,
   `-af atrim=end_sample=24024,asetnsamples=n=1024:p=0`, `-c:a pcm_s16le`,
   `-fflags +bitexact -flags:a +bitexact -map_metadata -1`.
3. Concatenate those segments with the concat demuxer, map the 45-frame video
   from input 0 and audio from concat input 1, `-c copy`, timescale 30000,
   `-fflags +bitexact -map_metadata -1`, output MOV. This is fixture creation,
   not the integration export path.

Full ffprobe packet table is `tmp/pcm-irregular.mov.json`. Compact complete
table (zero-based packet numbers):

| Packet indexes | pts | duration | size |
| --- | --- | --- | --- |
| 0..22 | `1024 * i` | 1024 | 2048 |
| 23 | 23552 | 472 | 944 |
| 24..46 | `24024 + 1024 * (i - 24)` | 1024 | 2048 |
| 47 | 47576 | 472 | 944 |
| 48..70 | `48048 + 1024 * (i - 48)` | 1024 | 2048 |
| 71 (last) | 71600 | 472 | 944 |

Thus TWO irregular mid-stream packets, plus an irregular last packet, and
72072 samples total. Generated twice byte-identically on this toolchain:
219463 bytes, SHA-256
`b06fb7979c6f5e28432f8aa250aa40b247ef197c31ddf6158f08e1422a8cf72b`.
Evidence `work/wp-d112/determinism.log` (the nested repeat log is also kept).
No fixture was copied into `tests/fixtures/` this turn.

Created out/settings/cache folders first, then ran the authorized command:

```text
uv run python tools/headless_export.py --force-cpu --out work/wp-d112/tmp/out --settings-dir work/wp-d112/tmp/settings --cache-dir work/wp-d112/tmp/cache --record work/wp-d112/tmp/export-record.json work/wp-d112/tmp/pcm-irregular.mov
```

Exit 0; `Batch of 1: 1 done`. The original check was active. No wrapper,
monkeypatch or emulated sink command was used. Product output has the SAME 72
audio packet pts/durations and decoded audio bytes. Evidence `export.log`,
`tmp/export-record.json`, `tmp/out/pcm-irregular_corrected.mp4.json` and
`tmp/more-facts.json`. The CLI also exercised the composition/export worker.
The default auto encoder recorded `hevc_nvenc`; `--force-cpu` selected CPU
frames/backend, not a software encoder. A second actual product export with
`--encoder libx265`, separate `tmp/out-x265` and `tmp/export-record-x265.json`,
also exited 0 (`Batch of 1: 1 done`) with the same 72 pts/durations and decoded
audio hash. Evidence `export-x265.log`, `export-x265-measure.log` and its full
packet JSON. Thus the measured control status also covers the light row's
software encoder; neither run was a pytest GPU node or a performance claim.
The new real-sink integration row is therefore a CONTROL on this candidate;
the pure-table rows carry RED. No GPU/footage/fullclip/slow pytest node ran.

Limit for the eventual report: The committed synthetic fixture's two irregular
boundaries survive the actual product export on this toolchain, whereas the
orchestrator's owner-file experiment reports coalesced or moved boundaries.
The observed difference is input/path-dependent mux chunking; its exact cause
has not been established and is outside this package. The integration control
proves the real sink can preserve this PCM fixture; the numerical unit rows
and independent equal-sample synthetic repacketization prove that the check
must permit harmless chunking changes. No claim is made to explain the owner's
different packetization or to reproduce it with an emulated command.

### 5. RED list and kept-green verification roster

Turn 2 is tests-only RED. Use test-side frozen dataclass subclasses of the
existing table/stream to plant the proposed additive metadata before the
production fields exist. This makes failures occur at check assertions, not
at unsupported constructor keywords. GREEN may use the same compatible fields.

Common PCM facts: `codec_name=pcm_s16le`, rate 48000, channels 1, format `s16`,
time base `1/48000`, first pts 0; unchanged four-frame video and stubbed edit
comparison as in neighboring pure-table unit rows. All labels use numbers,
not owner file stems. The numerical discrepancy below must be ruled before
locking the first two totals.

| Proposed unit row | Planted tables / expected result on today's check |
| --- | --- |
| `test_check_output_pcm_accepts_coalesced_packets` | Source durations `70*[1024] + [508] + 23*[1024] + [736] + 4*[1024] + [148]` (100 packets); output `70*[1024] + [508] + 27*[1024] + [884]` (99). pts are cumulative starts. Both total 100720 from stated boundaries. Expect no problems: RED packet-count refusal. |
| `test_check_output_pcm_accepts_moved_packet_boundaries` | Source `70*[1024]+[541]+23*[1024]+[736]+23*[1024]+[736]+13*[1024]+[291]`; output `70*[1024]+[541]+23*[1024]+[736]+24*[1024]+[736]+12*[1024]+[291]`. Both 133 packets, 134400 samples. Boundary 120061 moves to 121085; packet 119 becomes 121085 rather than 120797. Expect no problems: RED pts refusal. |
| `test_check_output_pcm_regular_packets_are_unchanged` | Seven identical 1024-sample packets, cumulative pts, 7168 samples. PASS control on old and new check. |
| `test_check_output_pcm_refuses_one_sample_fewer` | Same seven pts as regular control; final duration 1023 instead of 1024 (7167 vs 7168). Expect PCM sample-count refusal: RED today. |
| `test_check_output_pcm_refuses_another_sample_rate` | Same packet tables; output rate 44100 instead of 48000. Expect named PCM rate refusal: RED today. |
| `test_check_output_pcm_refuses_another_sample_format` | Same tables; output `s32` instead of `s16`. Expect named PCM format refusal: RED today. |
| `test_check_output_pcm_refuses_another_first_pts` | Same duration totals; output first pts 1 instead of 0. Expect PCM first-pts refusal: today's generic packet refusal fails the named-rule assertion (ADDITION 1). |
| `test_check_output_pcm_cut_counts_the_whole_straddling_packet` | Durations `[1024,508,1024]`, starts `[0,1024,1532]`, cut `1200/48000`; rechunk output as `[1532]` at pts 0. PASS expected, RED today. 1200- or 1531-sample output must refuse. |
| `test_check_output_pcm_cut_slack_allows_only_complete_packet_totals` | Same source, cut `1024/48000`; accept 1024 or 1532 samples, reject 1025. Last output shape may be one packet; GREEN must not turn slack into a sample-count range. |
| `test_check_output_pcm_refuses_another_time_base_or_channel_count` | Separate parameters: output `1/96000` or 2 channels. Mandatory format controls; expect PCM message. |
| `test_check_output_pcm_refuses_missing_sample_evidence` | Missing duration, missing rate/time base/format or missing first pts; no aggregate fallback. Named PCM refusal. |

Integration: add the fixed PCM id to V4 DECODABLE and the focused real-sink
row named above (ADDITION 2). On the measured fixture this row is GREEN before
the fix and is explicitly a control. Assert at least two non-last irregular
source packets independently of manifest intent, decode source/output PCM to
compare exact bytes, and assert unchanged sample extent/format. Keep the
existing AAC planted re-encode test unedited; add a separate PCM planted
re-encode/format-refusal row if needed, without changing that existing control.

Light verification after GREEN: the two brief modules with
`-k "audio or pcm or check_output"`, always with `PYTHONPATH=scripts`,
`-p sandbox_mkdir_shim -p no:cacheprovider` and basetemp under this worktree.
Keep `PYTEST_ADDOPTS` unset. Select out gpu/footage/gui/slow/fullclip nodes.
Also run the new V4 libx265 PCM cases explicitly because their node names do
not necessarily match that audio keyword filter; NVENC cases wait for the seat.

Fixture checks to run after GREEN: manifest validity/serialization/file checks,
inventory, fault roster, size/copy plants, privacy scan, MP4 udta row, new
`test_video_is_what_the_manifest_says[vid-pcm-irregular]`, tag/rotation/audio
rows, regeneration manifest/hash rows, generator static and audited I/O rows
listed in section 2. The generator-wide checks use only short synthetic media.
After ruling, run the new naming cases and existing dedicated MOV cases.
Ruff check/format and mypy remain required. No pytest was run this mapping turn;
the naming reproduction calls the existing function directly, with its new path.

Kept-green rows: both named unit tests at 707/726; unchanged AAC planted
re-encode at 1547; V4 `test_gx011627_through_the_sink_keeps_every_mandatory_and_required_item`
at 1621 using `gx011627_trim` (orchestrator's seat); WP4.4's existing owner MOV
proof (orchestrator, no cell footage access). No fidelity-instrument change.

Fullclip gate trigger IS PRESENT: `tests/conftest.py:861-880` parametrizes
`gx011627` with marked full and trim forms. The full forms of
`tests/test_io_video_encode.py:1621`, `:1635` use the real sink via the standard
encode fixture (162-181) / `vf.encode_file`; the full product-engine row
`tests/test_jobs_export_video.py:700` reaches it too. Sink close calls the changed
check at `encode.py:1096`. Therefore this brief's exception to omitting fullclip
applies. Schedule the required fullclip check at the orchestrator's seat;
the cell has no heavy/footage grant. Do not run it beside WP5.3 or another suite.

### 6. Disputes, recommended rulings and verification record

1. **[minor, NEW, in envelope] Recommended: grant narrow consumer edits before
   the fixture turn.** Allow only `test_sample_inventory_matches_the_brief`,
   `test_mp4_user_data_holds_nothing_beyond_the_empty_meta`,
   `test_video_has_audio_and_no_data_streams_or_location` in
   `tests/test_fixtures.py`, and the expectation in
   `tests/test_jobs_naming.py::test_wp23_fixture_names_keep_output_paths`.
   Evidence/anchors are in section 2. Cheap reproduction in
   `tmp/check_evidence.py` calls the existing naming test for the new path:
   four VIDEO combinations fail, four PHOTO combinations pass. Correct product
   behavior is already separately asserted by its dedicated MOV row. No such
   consumer edit has been made; the brief explicitly requires ruling first.
2. **[major, NEW, in envelope] Recommended: retain the stated packet-boundary
   shapes with their calculated totals for the two RED rows, and treat the
   decoded-byte figures as separate seat evidence pending reconciliation.**
   The coalesced example's source/output boundaries both imply 100720 samples,
   while the decoded-byte figure implies 100812 (difference 92). The moved
   example's boundary end is 134109 + 291 = 134400, while the decoded-byte figure
   implies 134414 (difference 14). Arithmetic is reproduced in
   `tmp/check-evidence.json`. This could be an omitted timing/trim detail or a
   transcription difference; the cell cannot decide which and did not open the
   originals. Before claiming per-packet duration equals those exact owner's
   decoded counts, the seat must reconcile its existing packet/stream logs.
   Synthetic evidence does prove exact duration counts for MOV lpcm and MP4
   ipcm and byte-identical coalescence. Do not silently change the brief's facts.
3. **[minor, NEW, in envelope] Recommended: supply the other seven refused
   owner stems at the reporting boundary, if all nine are required in this
   ledger.** Supplied refused stems are IMG_6729 and IMG_6731; IMG_6734 is a
   passing control, not a ninth failure. No committed evidence found supplies
   the other seven in this worktree. They cannot be inferred; footage and the
   main tree's work evidence are prohibited. Keep owner stems in this ledger
   only; eventual report can cite the ledger and the aggregate count.

Nonblocking citation correction for the dispatcher: spec N3 is the shared
CPU/GPU compute rule (`docs/underwater-correction-spec.md:441`), not the ASCII
rule. The brief's explicit ASCII lock still governs, with no product scope
change or spec edit requested.

Verification-loop record: suspected manifest hard-codes CONFIRMED by source
trace; naming consequence CONFIRMED by calling the existing assertion; presumed
fixture-driven RED REJECTED by actual successful headless product export;
PCM packet-identity defect CONFIRMED independently on byte-identical synthetic
72-to-71 packet control; exact sample-count field CONFIRMED on synthetic
MOV/MP4, lpcm/ipcm, moved/coalesced boundaries; brief numerical consistency
REJECTED by arithmetic, routed for ruling. No fixes this mapping turn. Two
fixture generations were byte-identical. No timing or memory performance claim.

| Round | Reviewer | Critical / major / minor | In / out | NEW / REOPENED | Reverts | Product / test fixes | Depth |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | Mapping, no Reviewer A pass | 0 / 1 / 2 | 3 / 0 | 3 / 0 | 0 | 0 / 0 | Dispatcher pending |

Reviewer A/B not started; both belong to the dispatcher after the reset named
in the brief. Full gate, footage proofs and WP5.3 witness remain at its seat.
This is the required round-0 YIELD, not package completion.

Round-0 artifact QA: `work/wp-d112/round0-qa.log`, exit 0. All seven listed
synthetic packet tables satisfy exact per-packet duration/payload sample-count
equality. Ledger ASCII decoding succeeds and CR count is 0; `git diff --check`
is clean, and status shows only this new ledger. Existing committed fixtures
total 894960 bytes; candidate MOV is 219463 bytes (comfortably under both caps).

## Turn 2: rulings and RED

Base: `0cd8eca3` (round-0 ledger committed by the dispatcher).
Depth: PENDING -- dispatcher to fill from the transcript; no cell estimate.
This turn changes only the PCM unit rows and this ledger. No product change,
fixture, manifest, generator or consumer-test edit; no commit attempted.

### Rulings received (quoted)

> 1. **Consumer edits: GRANTED, exactly the four you named** (`tests/test_fixtures.py::test_sample_inventory_matches_the_brief`, `::test_mp4_user_data_holds_nothing_beyond_the_empty_meta`, `::test_video_has_audio_and_no_data_streams_or_location`, and the expectation in `tests/test_jobs_naming.py::test_wp23_fixture_names_keep_output_paths`), each changed only to admit the new sample with its true facts, in a separately named step in the fixture turn, never weakening an assertion for the existing samples. Any fifth consumer is a new ruling.
>
> 2. **The numerical discrepancy: RECONCILED at my seat; your arithmetic is right and the brief's two decoded figures are the STORED count.** ffprobe on the two owner sources and the product's kept outputs: IMG_6731 source 100 packets, sum(packet `duration`) **100,720** = stream `duration_ts`, sum(payload `size`)/2 **100,812** = stream `nb_frames` = the decoded s16le count; the ONLY packet whose duration differs from its stored samples is the LAST (duration 148, stored 240); output 99 packets, sum(duration) 100,720, sum(size)/2 100,812, last packet duration 884 / stored 976. IMG_6729 source and output: 133 packets each, sum(duration) **134,400**, sum(size)/2 **134,414**, last packet duration 291 / stored 305 in both. So the container presents fewer samples than the last packet stores (the track's duration trims the tail), and BOTH totals are identical between source and output. **RULING: the PCM rule compares BOTH totals within the cut window: (a) PRESENTED samples = the sum of packet `duration`s, and (b) STORED samples = the sum of payload bytes / (channels x bytes per sample) for the sample format; both must equal the source's.** A refusal names which total failed. Your two RED rows keep the stated boundary shapes with their duration totals (100,720 and 134,400) AND plant the last packet's payload so the stored totals are 100,812 and 134,414 on both sides, by number only. Add one row each where only (a) differs and only (b) differs (both REFUSED). The cut-window rule counts whole packets for both totals as your straddling rows already do.
>
> 3. **The seven other refused stems** (ledger only, privacy lock): IMG_6733, IMG_6735, IMG_6736, IMG_6738, IMG_6741, IMG_6742, IMG_6760 (with IMG_6729 and IMG_6731: nine). IMG_6734 is a passing control, as you said.
>
> 4. **Your N3 citation correction: accepted** (the ASCII lock stands as the brief's own lock; no spec edit).
>
> 5. **Fullclip trigger: accepted.** The gate runs the fullclip leg at my seat (alone); you never run it.
>
> 6. **The fixture row is a CONTROL** (your measured result: the real sink keeps the fixture's packetization, NVENC and libx265); the unit rows carry the RED; the report carries the one-paragraph Limit CHARC's ADDITION 2 names (why the owner's files re-chunk through the product and the fixture does not is not established; out of scope as a fix).

The two-total ruling above governs the implementation; round 0's duration-only
proposal was not implemented. Add `audio_sizes` alongside `audio_durations` to
the planned packet facts. The quoted owner-file measurements are the
dispatcher's evidence, not experiments repeated by this cell. All three routed
round-0 items are resolved; the granted consumer edits wait for their separately
named fixture step. There is no remaining STOP or new scope request this turn.

### Tests built

Added test-only frozen `_PcmStreamRow` / `_PcmPacketTable` subclasses and pure
tables in `tests/test_io_video_encode_units.py:749-995`. They plant codec name,
sample rate, channel count, sample format, packet durations and payload sizes
without changing production dataclasses. `_pcm_check` calls the real
`check_output`; only the unrelated file edit-list read is stubbed, as in the
neighboring existing rows. Probe audio facts identify PCM, not AAC.

The two acceptance rows retain the exact numerical shapes: 100-to-99 packets
with presented/stored totals 100720/100812 (last source duration/stored 148/240,
output 884/976); 133-to-133 packets with totals 134400/134414 (last 291/305 on
both sides). Literal preconditions on totals and the moved/last pts pass before
each check assertion. No test contains an owner's stem.

The regular control is seven packets of 1024 samples. Refusal rows change one
sample, rate, format, first packet pts, time base or channels; the two added
rows independently change only presented or only stored samples. Missing
duration/size and stream facts must not be filled from unchanged container
aggregates. Cut rows count whole packets in both totals and permit only whole
source-prefix totals at the two-microsecond boundary, never a partial count.

### RED record

All node suffixes below follow the exact prefix
`tests/test_io_video_encode_units.py::`. Line numbers refer to the final test
file at this turn. Refusal rows fail the shared assertion at line 827; the table
also records each test's call line. `[]` means today's check incorrectly reports
no problems. A generic packet refusal is a failure when the contract instead
requires a named PCM rule and the failed comparison. No constructor error or
fixture error is counted as RED.

| Node suffix | Expected rule | Failure line(s) | Today's check result / assertion message |
| --- | --- | --- | --- |
| `test_check_output_pcm_accepts_coalesced_packets` | Accept equal presented AND stored samples across 100-to-99 re-chunking. | 844 | `audio stream 0: 99 packets in the output where 100 of the source's 100 were to be copied` |
| `test_check_output_pcm_accepts_moved_packet_boundaries` | Accept equal totals despite moved packet boundary. | 875 | `audio stream 0: packet 119 at 24217/9600 s where the source has 120797/48000 s` |
| `test_check_output_pcm_refuses_one_sample_fewer` | PCM presented 7167 vs 7168; both totals lost one. | 886, 827 | `[]` |
| `test_check_output_pcm_refuses_only_presented_samples_changed` | PCM presented 7167 vs 7168; stored remains 7168. | 896, 827 | `[]` |
| `test_check_output_pcm_refuses_only_stored_samples_changed` | PCM stored 7167 vs 7168; presented remains 7168. | 906, 827 | `[]` |
| `test_check_output_pcm_refuses_another_sample_rate` | PCM sample rate 44100 vs 48000. | 914, 827 | `[]` |
| `test_check_output_pcm_refuses_another_sample_format` | PCM sample format s32 vs s16. | 922, 827 | `[]` |
| `test_check_output_pcm_refuses_another_first_pts` | PCM first packet pts mismatch. | 930, 827 | `audio stream 0: packet 0 at 1/48000 s where the source has 0 s` (no PCM label) |
| `test_check_output_pcm_cut_counts_the_whole_straddling_packet[whole]` | Accept 1532 samples coalesced into one packet across cut at 1200. | 941 | `audio stream 0: 1 packets in the output where 2 of the source's 3 were to be copied` |
| `test_check_output_pcm_cut_counts_the_whole_straddling_packet[at-cut]` | PCM presented 1200 vs required 1532. | 943, 827 | `audio stream 0: 1 packets in the output where 2 of the source's 3 were to be copied` (wrong comparison, no PCM label) |
| `test_check_output_pcm_cut_counts_the_whole_straddling_packet[one-fewer]` | PCM presented 1531 vs required 1532. | 943, 827 | `audio stream 0: 1 packets in the output where 2 of the source's 3 were to be copied` (wrong comparison, no PCM label) |
| `test_check_output_pcm_cut_slack_allows_only_complete_packet_totals[partial]` | Refuse 1025 samples; only complete totals 1024 or 1532 are admissible. | 956, 827 | `[]` |
| `test_check_output_pcm_refuses_another_time_base_or_channel_count[time-base]` | PCM time base mismatch. | 971, 827 | `audio stream 0: packet 1 at 4/375 s where the source has 8/375 s` (no PCM label) |
| `test_check_output_pcm_refuses_another_time_base_or_channel_count[channels]` | PCM channel-count mismatch. | 971, 827 | `[]` |
| `test_check_output_pcm_refuses_missing_sample_evidence[duration]` | PCM refusal without a packet duration. | 994, 827 | `[]` |
| `test_check_output_pcm_refuses_missing_sample_evidence[size]` | PCM refusal without a packet payload size. | 994, 827 | `[]` |
| `test_check_output_pcm_refuses_missing_sample_evidence[sample_rate]` | PCM refusal without a sample rate. | 994, 827 | `[]` |
| `test_check_output_pcm_refuses_missing_sample_evidence[time_base]` | PCM refusal without a time base. | 994, 827 | `audio stream 0: packet 1 at 1024 s where the source has 8/375 s` (no PCM label) |
| `test_check_output_pcm_refuses_missing_sample_evidence[channels]` | PCM refusal without a channel count. | 994, 827 | `[]` |
| `test_check_output_pcm_refuses_missing_sample_evidence[sample_fmt]` | PCM refusal without a sample format. | 994, 827 | `[]` |
| `test_check_output_pcm_refuses_missing_sample_evidence[first_pts]` | PCM refusal without a first packet pts. | 994, 827 | `audio stream 0: packet 0 at None s where the source has 0 s` (no PCM label) |

Three new controls pass on today's implementation:

- `test_check_output_pcm_regular_packets_are_unchanged`.
- `test_check_output_pcm_cut_slack_allows_only_complete_packet_totals[drop]`.
- `test_check_output_pcm_cut_slack_allows_only_complete_packet_totals[keep]`.

The full node/line/message data from JUnit is stored at
`work/wp-d112/turn2-red-final-record.json`; the final pytest transcript is
`work/wp-d112/turn2-red-final.log` and JUnit is `turn2-red-final.xml`.

### Validation and verification-loop record

Final permitted light command (PowerShell environment assignments set
`PYTHONPATH=scripts` and unset `PYTEST_ADDOPTS` before this command):

```text
uv run pytest -q tests/test_io_video_encode_units.py tests/test_io_video_encode.py -k "audio or pcm or check_output" -m "not gpu and not footage and not gui and not slow and not fullclip" --basetemp=work/wp-d112/tmp/turn2-red-final -p sandbox_mkdir_shim -p no:cacheprovider --tb=short --junitxml=work/wp-d112/turn2-red-final.xml
```

Result: pytest exit 1, **21 failed, 12 passed, 192 deselected**. All 21 failures
are the intentional new check assertions above. The three new controls and all
nine existing nodes selected by the authorized filter passed, without skips or
errors. The other 192 nodes were deselected, not run or claimed green. No
gpu/footage/gui/slow/fullclip node or full suite ran.

Existing selected GREEN nodes (unchanged):

- `tests/test_io_video_encode_units.py::test_the_map_copies_audio_and_data_but_not_the_timecode_track`.
- `tests/test_io_video_encode_units.py::test_check_output_names_each_mismatch`.
- `tests/test_io_video_encode_units.py::test_a_cut_audio_stream_must_be_the_source_packets_before_the_cut`.
- `tests/test_io_video_encode.py::test_a_truncated_source_cuts_audio_at_the_readable_end`.
- `tests/test_io_video_encode.py::test_the_cut_short_reading_keeps_media_time_rate_and_the_audio_effect[video-media-time]`.
- `tests/test_io_video_encode.py::test_the_cut_short_reading_keeps_media_time_rate_and_the_audio_effect[video-rate]`.
- `tests/test_io_video_encode.py::test_the_cut_short_reading_keeps_media_time_rate_and_the_audio_effect[audio-duration]`.
- `tests/test_io_video_encode.py::test_the_cut_short_reading_keeps_media_time_rate_and_the_audio_effect[audio-media-time]`.
- `tests/test_io_video_encode.py::test_planted_audio_reencode_is_caught`.

Other checks:

| Command / check | Observed result | Evidence |
| --- | --- | --- |
| `uv run ruff check tests/test_io_video_encode_units.py` | Exit 0, `All checks passed!` | `work/wp-d112/turn2-ruff.log` |
| `uv run ruff format --check tests/test_io_video_encode_units.py` | Exit 0, `1 file already formatted` | `work/wp-d112/turn2-format.log` |
| `uv run mypy` | Exit 0, `Success: no issues found in 149 source files` | `work/wp-d112/turn2-mypy.log` |
| Existing two unit rows against HEAD | AST-identical | `work/wp-d112/turn2-eol-qa.log` |
| Changed-file byte and diff QA | ASCII, zero CR, no whitespace errors | `work/wp-d112/turn2-final-qa.log` |

Verification loop: suspected constructor-error RED REJECTED (all tables reach
the real check; no errors, all failure sites are check assertions); each
presented/stored acceptance precondition CONFIRMED by its literal assertions;
existing selected regression behavior CONFIRMED GREEN. Initial lint found one
long line, FIXED with ruff format; final lint/format are clean. Byte QA found
formatter-preserved CRLF, FIXED by LF normalization; the subsequent AST check
confirmed the two protected unit functions are unchanged. Both RED runs show
the same 21 failures / 12 passes; the second followed formatting and supplies
the final failure lines. LF normalization does not change code or line numbers.
No additional product issue or scope dispute was found in this test-only pass.

No Reviewer A/B pass was started. No register, decision, frozen interface,
dependency or local configuration was changed. No owner's footage or another
worktree was opened.
The dispatcher owns review scheduling, the heavy/fullclip gate and witness.

| Round / turn | Reviewer | Critical / major / minor | In / out | NEW / REOPENED | Reverts | Product / test changes | Depth |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | Mapping | 0 / 1 / 2 | 3 / 0 | 3 / 0 | 0 | 0 / 0 | Dispatcher pending |
| Turn 2 | RED only; no review | 0 / 0 / 0 new; all 3 prior items ruled | 0 / 0 new | 0 / 0 | 0 | 0 product; 24 new unit cases (21 RED, 3 controls) | Dispatcher pending |

Turn 2 YIELD. GREEN, fixture, granted consumers and report remain for later turns.


## Session 2 / Turn 3: GREEN and the fixture

Session boundary: session 1 retired at 199,970 (dispatcher-supplied figure).
Session 2 base: `62fe3caa`, branch `wp-d112`. Depth: PENDING -- dispatcher to
fill from this transcript; the cell makes no estimate. This turn bundles the
two expressly ordered steps, GREEN and then fixture/consumer admission, into
the dispatcher's one commit. No cell commit, mailbox post or subagent.

### GREEN: product rule and node-by-node record

`verify.py` adds defaulted stream codec/rate/channels/sample-format facts and
aligned packet duration/size mappings. All existing positional constructors
remain valid. The PCM branch checks format (including codec identity), first
packet pts, and BOTH totals from the turn-2 ruling. PRESENTED is exact integral
`duration * time_base * sample_rate`; STORED is payload bytes divided by channel
count and the packed codec's bytes per sample frame. In particular, packed
24-bit PCM has three bytes per channel sample although FFmpeg decodes it as
`s32`. Missing, negative or non-integral evidence refuses with a named PCM
message; no aggregate fallback. Variants without an exact fixed-byte codec
width are conservatively refused as unavailable sample evidence.

Cuts count a whole source packet if its start is before the cut. The existing
`CUT_SLACK_S` admits whole prefix lengths only; the presented/stored pair must
belong to ONE prefix. Duration/size evidence beyond the latest admissible
prefix is excluded; every output packet is counted. No sample tolerance.
The compressed `_audio_problems` function is source-text identical to HEAD:
SHA-256 `515a9d9883471d7b90ef1c57cb650df787726aac77153a7bdc024ba5392cfb8e`.
No video/data rule, `encode.py`, interface, dependency or configuration changed.

Initial GREEN: `turn3-green.log` / `turn3-green.xml`, 24 passed, 80 deselected;
the 21 previous RED cases and three controls follow. Node prefix for every row:
`tests/test_io_video_encode_units.py::`.

| Node suffix | Before GREEN | Turn 3 |
| --- | --- | --- |
| `test_check_output_pcm_accepts_coalesced_packets` | Previously RED | PASS |
| `test_check_output_pcm_accepts_moved_packet_boundaries` | Previously RED | PASS |
| `test_check_output_pcm_regular_packets_are_unchanged` | Kept-green control | PASS |
| `test_check_output_pcm_refuses_one_sample_fewer` | Previously RED | PASS |
| `test_check_output_pcm_refuses_only_presented_samples_changed` | Previously RED | PASS |
| `test_check_output_pcm_refuses_only_stored_samples_changed` | Previously RED | PASS |
| `test_check_output_pcm_refuses_another_sample_rate` | Previously RED | PASS |
| `test_check_output_pcm_refuses_another_sample_format` | Previously RED | PASS |
| `test_check_output_pcm_refuses_another_first_pts` | Previously RED | PASS |
| `test_check_output_pcm_cut_counts_the_whole_straddling_packet[whole]` | Previously RED | PASS |
| `test_check_output_pcm_cut_counts_the_whole_straddling_packet[at-cut]` | Previously RED | PASS |
| `test_check_output_pcm_cut_counts_the_whole_straddling_packet[one-fewer]` | Previously RED | PASS |
| `test_check_output_pcm_cut_slack_allows_only_complete_packet_totals[drop]` | Kept-green control | PASS |
| `test_check_output_pcm_cut_slack_allows_only_complete_packet_totals[keep]` | Kept-green control | PASS |
| `test_check_output_pcm_cut_slack_allows_only_complete_packet_totals[partial]` | Previously RED | PASS |
| `test_check_output_pcm_refuses_another_time_base_or_channel_count[time-base]` | Previously RED | PASS |
| `test_check_output_pcm_refuses_another_time_base_or_channel_count[channels]` | Previously RED | PASS |
| `test_check_output_pcm_refuses_missing_sample_evidence[duration]` | Previously RED | PASS |
| `test_check_output_pcm_refuses_missing_sample_evidence[size]` | Previously RED | PASS |
| `test_check_output_pcm_refuses_missing_sample_evidence[sample_rate]` | Previously RED | PASS |
| `test_check_output_pcm_refuses_missing_sample_evidence[time_base]` | Previously RED | PASS |
| `test_check_output_pcm_refuses_missing_sample_evidence[channels]` | Previously RED | PASS |
| `test_check_output_pcm_refuses_missing_sample_evidence[sample_fmt]` | Previously RED | PASS |
| `test_check_output_pcm_refuses_missing_sample_evidence[first_pts]` | Previously RED | PASS |

### Separate step: fixture and four granted consumers

Recipe: `tools/fixtures/video.py::_build_pcm` generates 45 limited BT.709 HEVC
frames (libx265 ultrafast, no B frames/version SEI, bitexact, timescale 30000)
and three mono 48000 Hz s16le MOV audio segments, each exactly 24024 samples,
with `asetnsamples=n=1024:p=0`. The concat demuxer joins the three audio segments
while stream-copying them and the video to MOV, bitexact and metadata-free.
All intermediate paths pass the existing write guard and are removed by build.
Defaulted `Spec.audio_codec`/`container` preserve all eight prior recipes.
Measurements and intended PCM packets/totals are validated by `mismatches`;
the manifest's new row was built by `manifest.entry` and `manifest.build`.

Fixture: `tests/fixtures/video/pcm-irregular.mov`, id `vid-pcm-irregular`.
Size 219463 bytes; SHA-256
`b06fb7979c6f5e28432f8aa250aa40b247ef197c31ddf6158f08e1422a8cf72b`.
Two independently built video groups under `fixture-gen-a` / `fixture-gen-b`
produce byte-identical MOVs and identical measured entries. Every existing
video entry matches the committed entry exactly. Full manifest regeneration
also passes byte-for-byte. The manifest leaves cross-build video byte identity
unclaimed, as for the existing video samples.

Complete compact audio packet table (zero-based):

| Packet indexes | pts | duration | payload bytes |
| --- | --- | --- | --- |
| 0..22 | `1024 * i` | 1024 | 2048 |
| 23 | 23552 | 472 | 944 |
| 24..46 | `24024 + 1024 * (i - 24)` | 1024 | 2048 |
| 47 | 47576 | 472 | 944 |
| 48..70 | `48048 + 1024 * (i - 48)` | 1024 | 2048 |
| 71 (last) | 71600 | 472 | 944 |

72 packets; PRESENTED = STORED = decoded = 72072 sample frames, 144144 decoded
bytes, decoded s16le SHA-256
`086691f53b341fa75ff0765698cb9ae70cd0af370fb1f3cb00282f7b1dfdf6f8`.
Mid-stream packets 23 and 47 are irregular independently of the last packet.
Format: pcm_s16le, time base 1/48000, 48000 Hz, one channel, s16, first pts 0.
Source and libx265 product output have identical complete audio packet tables.
Full lists/measurements: `fixture-gen-a/entries.json`, `fixture-gen-b/entries.json`,
`turn3-artifact-facts.json`; generator transcript `turn3-build-fixture.log` and
completed transfer summary `turn3-build-fixture-final.log`. The initial scratch
transfer script used a nonexistent manifest loader AFTER both generations;
corrected to JSON loading and reused the two already-generated groups. No
committed generator defect or extra generation is hidden by that correction.

Granted consumer edits, with no existing-sample assertion weakened:

| Consumer | Before | After |
| --- | --- | --- |
| `test_sample_inventory_matches_the_brief` | Exactly eight explicit video ids | Same eight plus `vid-pcm-irregular` |
| `test_mp4_user_data_holds_nothing_beyond_the_empty_meta` | All video ids assumed MP4, count eight | Select `.mp4` only, still require exactly eight and the same empty udta/meta assertions |
| `test_video_has_audio_and_no_data_streams_or_location` | Every video must have AAC | Only the new id must have pcm_s16le; every old id still AAC; every id still no data/location |
| `test_wp23_fixture_names_keep_output_paths` | VIDEO output keeps source suffix | MOV VIDEO expects `.mp4` under WP4.4; all other extensions and PHOTO expectations retained |

`DECODABLE` now explicitly includes `vid-pcm-irregular: 8`; the two libx265
8/10-bit V4 cases pass. New real-sink row:
`tests/test_io_video_encode.py::test_pcm_irregular_audio_survives_the_real_sink`.
It uses `Runs.get` -> `video_fidelity.encode_file` -> `_RecordingSink`, a real
`FFmpegVideoSink` with unmodified NUT-pipe two-input command, `-copyts`,
`-c:a copy`, MP4 flags, open/write/close and mandatory read-back. It asserts
two non-last irregular packets, exact source/output format/start/totals and
decoded PCM byte equality. Like its synthetic V4 neighbors it is UNMARKED
(no slow/gpu/footage/gui/fullclip mark), and was run explicitly by node id:
`turn3-real-sink.log` / `.xml`, 1 passed. Source/output facts and the complete
pre-fix `check_output` loaded from HEAD independently return no problems:
`turn3-artifact-check.log`. This is a CONTROL, not a RED claim. New planted
PCM-to-AAC re-encode refuses with the PCM codec message; the existing AAC
planted re-encode row is unchanged and passes.

Limit for the later report: the synthetic fixture keeps all packet boundaries
through the real sink, while the seat experiment's two owner sources coalesced
or moved boundaries. Equal decoded bytes and both extent totals establish the
harmlessness of those owner changes; they do not establish which source or
full-command detail causes re-chunking. Its cause is unknown and outside this
package's fix scope. The unit numerical shapes carry the RED; the fixture is
the commissioned real-sink control. No owner's footage was opened by this cell.

### Light checks and the pre-existing audit failure

All evidence below is relative to this worktree's `work/wp-d112/`. Every pytest
run sets `PYTHONPATH=scripts`, unsets `PYTEST_ADDOPTS`, loads
`-p sandbox_mkdir_shim -p no:cacheprovider` and has its own basetemp under
`work/wp-d112/tmp/`. No heavy/footage/GPU/GUI/fullclip test was run.

| Check | Result | Evidence |
| --- | --- | --- |
| Initial PCM GREEN | 24 passed, 80 deselected | `turn3-green.log` / `.xml` |
| Initial keyword light run | 37 passed, 194 deselected | `turn3-light.log` / `.xml` |
| Whole unit module after cut-window verification fix | 109 passed | `turn3-units.log` / `.xml` |
| Final two-module keyword light run (`audio or pcm or check_output`, non-heavy markers) | 42 passed, 194 deselected | `turn3-light-final.log` / `.xml` |
| Real-sink libx265 control, explicit node | 1 passed | `turn3-real-sink.log` / `.xml` |
| Fixture roster from round 0 section 5 | 44 passed, 3 failed, 301 deselected | `turn3-fixtures.log` / `.xml` |
| Naming manifest cases + existing MOV extension/collision rows | 741 passed, 136 deselected | `turn3-naming.log` / `.xml` |

The fixture selection includes validity, serialization, all committed files,
inventory, faults, cap/missing-file plants, privacy, eight-MP4 udta, all nine
video fact rows, stream tags, rotation, audio/data/location, full regenerated
manifest and decoded hashes, static generator scan/plants, and all three I/O
audit rows. Only those last three audit rows fail:

- `test_generators_write_only_inside_their_output_folders`: extra write `nul`.
- `test_generators_read_only_their_own_code_and_libraries`: extra read `nul`.
- `test_ffmpeg_is_told_to_write_only_into_the_output_folders`: 55 allowed
  ffmpeg/ffprobe processes among 56 subprocesses; extra `cmd.exe /c ver`.

**[major, PRE-EXISTING, OUT OF ENVELOPE]** Independently reproduced WITHOUT
fixture generation or any call to the new PCM helpers: isolated Python calls
unchanged `fixtures.flicker.normalisation_spread(flicker.still())`. Its import
chain is `prototype.pipeline` -> `prototype.backend` -> SciPy ndimage ->
`numpy.testing._private.utils` -> `platform.machine` -> `win32_ver` ->
`_syscmd_ver` -> `cmd.exe /c ver`, with Python opening its `nul` device.
Trace: `turn3-audit-spread-trace.log`; audited event extraction:
`turn3-audit-finding.log`; initial imports alone have no process:
`turn3-audit-import-trace.log`. Existing mechanic at
`tools/fixtures/flicker.py:482`, originated in `e60162c6` (`git log -S
normalisation_spread`, `turn3-audit-origin.log`); `git diff --quiet` for that
file exits 0. No additional consumer edit was made and none is proposed as an
in-envelope fix. Disposition: BANKED to the dispatcher for a seat re-run of
these three rows before acceptance, or a separately ruled scope if they fail
there. This turn does NOT claim a fully green fixture roster or package gate.

### Verification loop

| Suspect | Independent confirmation / rejection | Disposition |
| --- | --- | --- |
| New check unnecessarily requires duration/size AFTER the source cut | A pure-table row with a valid 1532-sample included prefix and missing facts only in the excluded third packet fails `turn3-window-red.log` (1 failed) | CONFIRMED, FIXED: accumulate only through the latest admissible source prefix; regression passes in 109-unit and 42-light runs |
| Cut slack might combine totals from different prefixes | Planted output pair `(1024,1624)` has individually admissible totals, but no jointly admissible source prefix; new row refuses by named paired-total rule | REJECTED as a fault in the implementation; retained regression control |
| Invalid duration/payload fractions could silently round | Negative duration, odd s16 payload byte count and half-sample presentation duration independently refuse; three added parameter rows pass | REJECTED; retained controls |
| Compressed rule drift or re-encode hole | Exact function-text hash equality, unchanged named cut/mismatch unit rows, existing AAC plant and new real PCM-to-AAC plant | REJECTED |
| Fixture is accidentally claimed RED | Old complete check accepts measured product output and source/output packet lists are identical | REJECTED; labeled CONTROL throughout |
| Fixture audit regression from the new recipe | Direct unchanged flicker-only import path reproduces cmd/ver and nul, with origin trace above | CONFIRMED pre-existing outside envelope; BANKED to dispatcher, no unauthorized fix |

The final pass over owned code, fixture measurements, four consumer assertions,
cut edge cases, message ASCII handling and compressed-rule identity found no
new issue. The known audit failures remain explicitly open for the seat.
No reviewer pass has started and no Reviewer A round is credited this turn.
Reviewer A round 1, Reviewer B, the two-leg/fullclip gate, trim/owner proofs and
post-merge witness remain COMMISSIONED to the dispatcher under the brief.

Final lint/type and byte checks are recorded in `turn3-ruff-final.log`,
`turn3-format-final.log`, `turn3-mypy-final.log`, `turn3-byte-qa.log` and
`turn3-diff-check.log`; the return message quotes their actual summaries.
All changed text is LF with zero CR. `.gitattributes` already has
`tests/fixtures/** -text`; `git check-attr text` is unset for the new MOV,
and `git diff --no-index --numstat NUL <fixture>` reports `- -` (binary).
The MOV is retained byte-for-byte; zero-CR applies to text, not binary data.

| Turn | Reviewer | Critical / major / minor | In / out | NEW / REOPENED | Reverts | Product / test fixes | Depth |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Session 2 / 3 | Build verification; A pending | 0 / 2 / 0 confirmed verification findings | 1 / 1 | 1 introduced / 0 reopened; 1 pre-existing | 0 | PCM rule and cut-prefix fix / fixture and controls | Dispatcher pending |

YIELD for Reviewer A and the audit disposition. This is turn-3 build evidence,
not acceptance or the final package report.

## Dispatcher record after turn 3 (orchestrator gen 33, 2026-11-01 ~23:55Z)

- Session 2 depth at the turn-3 yield: 136,826 input tokens (`depth_input_tokens`
  in `turn-3.driver.stdout`).
- The banked audit disposition: the three I/O audit rows re-run at the
  dispatcher's seat on head `202d1b2e`, outside the Codex sandbox, with
  `PYTEST_ADDOPTS` unset: **3 passed in 22.64 s**
  (`clearwater-review-evidence/wp-d112/audit-d112.log` / `.xml`). The `nul` read and
  write and the `cmd.exe /c ver` process are artefacts of the Codex sandbox, not of
  the package. No scope ruling is needed; the package proceeds to Reviewer A.
- Reviewer A round 1 (a Claude pass) is held under the 92 % rule (Claude weekly
  use 94 % at 23:54Z, reset 2026-11-02 10:00Z).

## Session 2 / Turn 4: Reviewer A round 1 adjudication

Base: `bd655a07`, branch `wp-d112`; clean at entry. The dispatcher recorded
session 2's turn-3 depth as **136,826** above. Current turn-4 depth: PENDING --
dispatcher to fill; no cell estimate. This turn changes this ledger only.
Product code, tests, generator, manifest and committed media are unchanged.
Scratch probes and their output remain under this worktree's `work/wp-d112/`.

Read Reviewer A's authorized `r1/review.txt` IN FULL at
`C:/Users/rwsmy/clearwater-review-evidence/wp-d112/r1/review.txt`.
Its verdict is `NEW_CRITICAL_MAJOR_FOUND`; all three findings are tagged
EXECUTED. Reviewer identity/conditions supplied by the dispatcher: Claude
Opus, independent, 26 turns, no refused command, clean worktree afterward.
The allowed report does not contain a CLI version or invocation banner;
those mechanical assertions remain with the dispatcher's invocation record,
not an inferred cell claim. No second reviewer or subagent was started.

The turn-3 audit item is CLOSED as a sandbox-only finding on the dispatcher's
new evidence: the three audit rows pass at its seat, 3 passed. No fifth
consumer edit or scope ruling is needed for that item.

### Round-1 disposition, one row per finding

| Finding | Classification / provenance | IN / OUT | Independent evidence | Proposal / status |
| --- | --- | --- | --- | --- |
| F1 | **MAJOR, NEW**, introduced by the PCM check | **IN**: D86 explicitly accepts the readable portion of truncated supported MOVs; actual probe returns warning-only and the real sink reaches read-back | All three faststart MOV cuts reproduce; 55/85 percent passed base, all three now refuse despite identical decoded source/output PCM; details below | CONFIRMED. STOP for CHARC to amend truncated-source sample evidence as specified below; no remediation this turn |
| F2 | **MINOR, NEW** timing-verification gap; current implementation follows the commissioned first-pts-plus-totals rule | **IN** for detecting sink/muxer timing damage under D94; strengthening the ruled rule requires CHARC | Real fixture table with a +1024-tick shift after packet 30, or all-zero pts, returns no problems; numeric owner shapes and real fixture are contiguous | CONFIRMED. Recommend contiguity in both compared timelines, with an explicit policy that a noncontiguous source refuses; STOP for that new rule / acceptance restriction |
| F3 | **ADVISORY, PRE-EXISTING**, not a regression | **OUT** of remediation envelope: compressed behavior is expressly locked | AAC table with PCM-relabelled output returns no problems under BOTH current and base checks; source-only branch confirmed at `verify.py:848` | RETAIN unchanged compressed path. BANKED to CHARC for a separately commissioned codec-identity check if desired; no fix or extra in-envelope round |

### F1: independent reproduction and envelope

Probe driver: `work/wp-d112/turn4_probes.py`; main transcript:
`work/wp-d112/turn4-probes.log`; commands and FFmpeg diagnostics:
`work/wp-d112/turn4-probes/commands.log`; complete measured tables and results:
`work/wp-d112/turn4-probes/f1.json`. No owner media was opened.

Recipe: stream-copy the committed `tests/fixtures/video/pcm-irregular.mov`
to `turn4-probes/faststart.mov` with FFmpeg `-c copy -movflags +faststart`.
The resulting 219495-byte MOV is cut at `len(bytes) * percent // 100` for
55, 70 and 85 percent. These are scratch derivatives, not new committed files.
Each is probed and passed through `video_fidelity.encode_file`, libx265, 8-bit:
the real `_RecordingSink(FFmpegVideoSink)` NUT-pipe/two-input path, with no
command emulation. The check observer calls the CURRENT check and base
`9d37169b`'s check on the SAME finished output, records its packet facts,
retains a scratch copy before abort, and returns the current check's actual
problems. It does NOT suppress the refusal. Each real sink therefore raises
`VideoEncodeError(kind="verify_failed")`, as the product would today.
All three paths ran in this sandbox; no reproduction step was unavailable.

| Cut | Bytes retained | Probe readable video frames / faults | audio_end (s) | Source audio packets / final pts, duration, bytes | Source declared PRESENTED / complete STORED | Output packets / PRESENTED = STORED = decoded | Current / base |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 55 percent | 120722 | 24/45; only `truncated`, `warn` | `1001/1250` | 39; `38360, 1024, 909` | 39384 / 38814 | 39 / 38814 | Invalid exact evidence / PASS |
| 70 percent | 153646 | 31/45; only `truncated`, `warn` | `31031/30000` | 50; `49072, 1024, 860` | 50096 / 49502 | 49 / 49502 | Presented 49502 vs 50096 / packet-count refusal |
| 85 percent | 186570 | 38/45; only `truncated`, `warn` | `19019/15000` | 61; `60336, 1024, 647` | 61360 / 60659 | 61 / 60659 | Invalid exact evidence / PASS |

All listed source audio packets start before the respective cut (separate
calculation in `turn4-window-membership.log`); no CUT_SLACK ambiguity accounts
for the difference. Decoding both tracks to s16le returns status 0 in all six
decode calls (`turn4-decode-status.log`). The decoded source/output bytes are
IDENTICAL at each cut: 38814, 49502 and 60659 complete sample frames. Odd
payloads 909/647 contribute 454/323 complete mono s16 frames, respectively;
their final unmatched byte does not decode to a sample frame. At 70 percent,
860 bytes contribute 430 frames despite the stated 1024-frame duration.
Only the final listed audio packet has a duration/payload discrepancy.

The 70-percent product output re-chunks this measured source tail:
`47576(472), 48048(1024), 49072(1024 duration, 860 bytes)` becomes
`47576(1024), 48600(902)`. This supplies a concrete truncated-tail trigger for
harmless re-chunking. It does not establish why the intact owner files
re-chunk, and does not authorize an `encode.py` change. Carry this new measured
fact into the eventual report's Limit paragraph.

Envelope evidence at this head:

- Spec D86, `docs/underwater-correction-spec.md:124`, and damaged inputs
  section 5.4 at `:225`: process the readable portion of truncated/corrupt
  sources and warn. A MOV need not come from an iPhone to be in that contract.
- `probe.py:538` (`probe`) accepts supported MOV/MP4, codecs and formats.
  `_tail_fault` at `:489`, its condition at `:504`, and its use at `:634`
  turn a partial-file report, corrupt last video packet or short frame count
  into `Fault("truncated", "warn", ...)`, not a refusal. The three measured
  derivatives have exactly that warning and no refuse fault.
- `encode.py:652` refuses only `severity == "refuse"`; `_check_source` at
  `:834` applies SAR/edit-list/pts checks and passes these files.
- `_plan_tracks` at `encode.py:857` uses the readable video portion; at `:888`
  it sets `audio_end`. `verify.py:680` (`readable_end`) requires the retained
  source sample table when a later frame is not listed. These faststart files
  retain a readable moov and satisfy that requirement.
- The real failure occurs only at `encode.py:1096-1105`, after successful
  encoding. `_pcm_totals` at `verify.py:894` rejects odd payload sizes; at
  `:896-900` it otherwise counts the overstated source duration without an
  EOF cap. `_pcm_problems` at `:939-946` demands that impossible duration total.

Therefore F1 is a confirmed MAJOR IN-envelope regression. The reviewer caveat
about whether a particular real iPhone MOV retains moov does not remove the
supported synthetic faststart MOV from D86. The evidence establishes three
failing shapes, not a claim that every possible truncated PCM file fails.

### F1: exact proposed ruling text (STOP, not implemented)

**Recommended: approve the following source-only D86 exception.** It changes
the turn-2 raw duration / exact-payload rule and therefore requires CHARC's
ruling before code or tests change.

1. Enable the exception only when the source ProbeResult has a `truncated`
   fault AND `audio_end is not None`. A cut value alone is insufficient.
   No exception for an intact source, an `unreadable_tail` copied whole, a
   compressed source, or any output packet. This is a private verifier input,
   derived from the existing ProbeResult; no frozen interface change.
2. Keep the source-packet-start cut window and `CUT_SLACK_S` prefix choices
   exactly as now. A complete packet straddling the cut is still counted
   whole; this exception concerns absent payload at physical EOF, not clipping
   a complete packet to the cut timestamp.
3. Let `B = channels * packed_codec_bytes_per_channel_sample`, and for each
   included source packet let `D_i = duration_i * time_base * sample_rate`.
   D_i must still be a known, nonnegative INTEGER. For a frame-aligned payload,
   `S_i = size_i / B` exactly. A remainder is allowed ONLY for the LAST LISTED
   packet of that source audio stream (physical readable tail), and only if
   that packet is included: then `S_i = floor(size_i / B)`. Remainders in an
   earlier source packet remain invalid; being merely the last packet of a
   chosen cut prefix does not qualify it. Missing/negative sizes and missing
   format/clock facts still refuse.
4. In that truncated source window define effective PRESENTED as
   `sum(min(D_i, S_i))` PER PACKET, and complete STORED as `sum(S_i)`.
   Do not use `min(sum(D_i), sum(S_i))`: padding in one packet must not mask
   absent readable samples in another. If stored exceeds presented, its full
   complete stored count remains independently required; this preserves the
   distinction that resolved the original owner-file totals.
5. Count the OUTPUT strictly as today: integral nonnegative declared
   durations and frame-aligned payload bytes in every packet; no cap and no
   floor. Its exact `(PRESENTED, STORED)` pair must equal the normalized source
   pair of ONE admissible whole source prefix. No new tolerance. Format and
   codec equality, time base, rate, channels, sample format and first pts
   checks remain mandatory, with ASCII messages naming PCM and the failed
   total. This permits discarding only bytes that cannot make a complete
   decoded source sample frame; it never excuses a lost complete sample.
6. If the source does not satisfy BOTH conditions in item 1, retain the
   present implementation's duration and payload rules exactly, including
   rejection of odd payloads. F1 alone makes no other non-truncated change.

Arithmetic-only oracle (NOT remediation or a claimed implemented fix):
`turn4_rule_oracle.py`, `turn4-rule-oracle.log`, and
`turn4-probes/rule-oracle.json`. The proposed source pairs are exactly
`(38814,38814)`, `(49502,49502)`, `(60659,60659)`, matching the three measured
outputs. Subtracting one complete output sample fails each exact pair test.

Proposed RED roster for a ruled implementation turn:

| Proposed row | Pure table / expected result |
| --- | --- |
| `test_check_output_truncated_pcm_uses_complete_readable_tail[55]` | Take the first 39 packets of `((1024 x 23),472) x 3`; final source size 909, duration 1024, pts 38360. Source has truncated fault and cut `1001/1250`. Output keeps first 38 durations, final duration 454, aligned size 908. Expect accept 38814/38814; today's invalid-evidence refusal is RED |
| Same `[70]` | First 50 source packets, last size 860, duration 1024, pts 49072, cut `31031/30000`. Output durations are the first 47 source durations plus `(1024,902)`, 49 packets total with aligned sizes. Expect accept 49502/49502; today's presented-total refusal is RED |
| Same `[85]` | First 61 source packets, last size 647, duration 1024, pts 60336, cut `19019/15000`. Output keeps first 60 durations, final duration 323, aligned size 646. Expect accept 60659/60659; today's invalid-evidence refusal is RED |
| Truncated normalized tail minus one complete output sample | For each of the three shapes reduce output's last duration and stored count by one; expect PCM refusal, not a tolerance pass |
| Partial earlier source packet / partial OUTPUT packet | Floor is not available in either position; expect named PCM invalid-evidence refusal |
| Same odd terminal source with no truncated fault, or with `audio_end=None` | Strict original rule still refuses; a cut alone and a warning alone cannot activate the exception |

Feasible integration RED: a new libx265 row under `tests/test_io_video_encode.py`
builds the 70-percent faststart derivative from the committed PCM fixture at
test time, verifies the truncation warning and short readable audio tail,
and calls the real sink with NO checker bypass. It must export and retain
identical decoded readable PCM after the fix; today it raises verify_failed,
as independently measured. Re-chunking is permitted. Use its synthetic
neighbors' marks and assert the intended short-tail precondition. No new
committed fixture, generator change or manifest/consumer edit is needed.

Existing expected outcomes: **none change**. `_pcm_check` would need only an
optional, default-off way to plant a truncated fault for new rows. Existing
complete straddling-packet and cut-slack rows retain their outcomes and
assertions. In particular `test_check_output_pcm_refuses_inexact_sample_evidence`
with `[partial-sample]` remains a strict, NON-truncated refusal. Existing
one-sample-fewer, rate, format, first-pts, time-base and channel-count rows
continue refusing: they never enter the source-only exception, and the format
and start checks do not move behind normalization. A fresh run of the existing
refusal roster (`-k "pcm and refuses"`) passes **18 rows, 91 deselected**:
`turn4-guards.log` / `.xml`, with the required sandbox shim and no cacheprovider,
PYTEST_ADDOPTS unset, basetemp `work/wp-d112/tmp/turn4-guards`.
This is evidence of the current guards plus a precise branch-isolation argument;
it is NOT a claim that the not-yet-implemented rule has passed tests. Its
remediation turn must run the complete touched light roster again.

### F2: reproduction, proposed timing guard and source policy (STOP)

`turn4-probes/f2.json` records direct calls to the real `_pcm_problems` on pure
tables. Starting from the committed fixture's real packet table:

- Leave packet 0..30 pts unchanged and shift packets 31..71 by +1024 ticks:
  current problems `[]`; the contiguity break is exactly before packet 31.
- Set all 72 pts to zero: current problems `[]`; contiguity breaks before
  every packet 1..71. First pts, format and both totals still match.
- Give BOTH source and output the same shifted table: current problems `[]`;
  the source is itself noncontiguous before packet 31. This makes the source
  acceptance consequence of the proposed rule explicit, not hypothetical
  arithmetic silently omitted from the return.

Mechanic: `_pcm_totals` reads pts only for presence/alignment of the mapping,
`verify.py:888-891`; `_pcm_problems` uses source pts to select the window and
then checks only the first output pts at `:960-967`. No later timestamp is
compared or constrained. The hole is reachable under a broken sink/muxer,
and base's packet-identity rule would catch a changed output with an unchanged
source. It is MINOR here because the cell followed the explicit ruled check
definition; adding the missing D94 evidence is a rule amendment, not an
unilateral reinterpretation to fix inline.

**Recommended: require contiguity of BOTH compared PCM timelines**, with the
following explicit source policy for CHARC to approve:

- For each candidate source prefix and for ALL output packets, every adjacent
  pair must satisfy `next_pts == current_pts + current_duration` in exact
  stream ticks. For an F1-normalized source use its effective presented extent
  in exact time (`next_pts * time_base == current_pts * time_base + P_i/rate`);
  ordinary source packets use the existing declared duration. No timing slack.
  F1's short physical tail has no successor, so no false adjacency is created.
- Check only the compared source prefix for a cut, never ignored packets
  beyond it. Existing CUT_SLACK alternatives still require one valid prefix
  whose exact pair matches the output. Output contiguity is always required.
- Preserve the current first-pts, format and paired-total requirements.
  Contiguity plus equal start and total presented extent fixes the entire
  presented timeline without requiring matching packet boundaries.
- A SOURCE that is itself noncontiguous in the compared prefix is REFUSED
  with a named PCM source-timing message; do not repair its gaps or silently
  normalize overlaps. This is a NEW acceptance restriction relative to
  first-pts-plus-totals and must be explicitly ruled. No evidence in this
  turn establishes that all possible supported PCM sources are contiguous.
  If CHARC requires preserving gapful sources, commission a gap-preserving
  timeline rule separately rather than silently adopting this restriction.

Prefer adjacency over only equal final end time: compensating interior
gap/overlap changes can restore the same last end while moving samples inside
the stream. That observation is the reason for the proposed guard, not a new
scope claim or a claim about any owner's media.

Measured positive controls for this proposal (source and output both have
ZERO adjacency failures, and current full audio problems are `[]`):

| Control | Source / output packets | First pts; PRESENTED / STORED | Adjacency result |
| --- | --- | --- | --- |
| IMG_6731 numerical owner shape from the committed unit rows, not owner media | 100 / 99 | 0; 100720 / 100812 | Both contiguous |
| IMG_6729 numerical moved-boundary shape from the committed unit rows | 133 / 133 | 0; 134400 / 134414 | Both contiguous |
| Committed fixture's measured real packet table | 72 / 72 identity control | 0; 72072 / 72072 | Contiguous across both mid-stream 472-sample packets |
| All three newly observed truncated source/output pairs | 39/39, 50/49, 61/61 | Normalized totals as above | Both contiguous; short final packet has no following adjacency |

The two numerical source/output tables retain the original presented/stored
tail discrepancy and re-chunking shapes. No owner's file was inspected to make
these claims. For the fixture, the prior real-sink control's measured packet
identity is already recorded in turn 3; this turn re-reads the committed real
packet table and records fresh real-sink truncated derivative tables.

Proposed timing RED rows: shifted output after packet 30, all-zero output pts,
and noncontiguous SOURCE (including source/output same-gap); all must refuse
with PCM timing messages under an approved source-refusal policy. Keep the two
existing owner-shape acceptance rows and real-sink fixture control as positive
controls, plus a synthetic re-chunked contiguous output. No current expected
test assertion needs weakening. F2 is nonblocking by severity and does not
independently extend the review loop; it is routed now because this dispatch
expressly requires adjudication without remediation.

### F3: compressed behavior locked; no remediation recommended

Independent table reproduction in `turn4-probes/f3.json`: read the committed
AAC fixture `video/hevc10.mp4`, relabel only the output audio StreamRow's
codec name/tag as `pcm_s16le`/`ipcm`, leave its packet pts unchanged, and call
complete current/base `check_output`. Both return `[]`. This is table evidence
of a codec-identity hole, not a claim that an actual AAC-to-PCM export occurred.

The branch is chosen at `verify.py:848` using the SOURCE codec. The locked
compressed `_audio_problems` at `:977` compares only source-prefix packet pts.
Provenance: `git log -S "def _audio_problems"` names `b2d761c9` (WP3.10);
`work/wp-d112/turn4-f3-origin.log`. The pre-package base independently accepts
the same relabel, so this is pre-existing, not a WP-D112 regression.

Recommendation: RETAIN compressed behavior exactly; do not route by output
codec or add a codec check to compressed streams inside this package. BANKED
to CHARC to commission a separate compressed-format check if desired, before
any such behavior is changed. No cell register edit, new requirement, or
additional review round is commissioned by this advisory.

### Cumulative round ledger and turn boundary

| Reviewer round | Verdict | Critical / major / minor / advisory | IN / OUT | NEW / REOPENED / pre-existing | Reverts | Product / test fixes THIS TURN | Transport / depth |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | NEW_CRITICAL_MAJOR_FOUND | 0 / 1 / 1 / 1 | 2 / 1 | 2 / 0 / 1 | 0 | 0 / 0; adjudication only | Dispatcher-run Claude Opus process; CLI version in dispatcher record; prior turn depth 136826, current PENDING |

F1 and F2 remain OPEN pending CHARC's two explicit rule rulings; no code or
test remediation has been attempted. F3 is nonblocking and banked outside
the package. Reviewer A has NOT converged. Final gate, Reviewer B, report,
owner/trim proofs and witness retain their commissioned dispositions.

Locks this turn: no footage read; no other worktree or main-tree work read;
only the authorized single file read in the external review-evidence folder; no commit,
stash, mailbox post, dependency, interface or product/test edit. Final ledger
ASCII/LF, scope and `git diff --check` evidence are in
`work/wp-d112/turn4-ledger-qa.log`. YIELD for the ruling packet, not an
implementation promise or a completion claim.

## Session 3 / Turn 5: round 1 remediation

Fresh session 3, base `981724b9`. Session 2 retired at dispatcher-reported
184,370 tokens. Depth THIS TURN: PENDING -- dispatcher to fill from transcript;
no cell estimate. This turn bundles the commissioned RED and GREEN for F1/F2
and the warning grant into one logical round-1 remediation, with no cell commit.

Binding packet: CHARC `b44b0ee7` adopts the D86-only source exception (F1,
MAJOR) and gap-preserving run equality (F2, MINOR), rejects source-gap refusal,
and banks F3 without a code/test change. CHARC `81ebcf52` grants exactly one
insertion after `encode.py`'s post-encode `check_output` call: append the named
partial-frame warning, using a default-zero read-only verifier result. No mux,
flags, IF-5 or other `encode.py` changes are authorized or made.

### RED before GREEN

Evidence paths below are relative to `work/wp-d112/`. The pre-product-edit run
`turn5-red.log` / `.xml` has **13 failed, 7 passed, 236 deselected**. It ran
both owned test modules, selecting `truncated_pcm or changed_timeline_runs or
same_gap or manifest_packet_table or odd_source_requires`. Failures were
assertions on the real check/sink, not collection or setup errors. The three
minus-one rows already refused at base, but failed their required normalized
sample-count diagnostics: odd source tails gave invalid evidence, and the
aligned short tail gave the unnormalized declared count.

All 20 nodes map to PASS in final `turn5-light-final.xml`; machine-readable
before/after table: `turn5-node-results.json`. Node names below omit their
module prefix: units except the final three integration nodes.

| Node | Before | After |
| --- | --- | --- |
| `test_check_output_truncated_pcm_uses_complete_readable_tail[55]` | FAIL: invalid evidence | PASS |
| `test_check_output_truncated_pcm_uses_complete_readable_tail[70]` | FAIL: 50096 declared vs 49502 readable | PASS |
| `test_check_output_truncated_pcm_uses_complete_readable_tail[85]` | FAIL: invalid evidence | PASS |
| `test_check_output_truncated_pcm_refuses_one_readable_sample_fewer[55]` | FAIL: wrong refusal diagnostic | PASS |
| `test_check_output_truncated_pcm_refuses_one_readable_sample_fewer[70]` | FAIL: wrong expected sample count | PASS |
| `test_check_output_truncated_pcm_refuses_one_readable_sample_fewer[85]` | FAIL: wrong refusal diagnostic | PASS |
| `test_check_output_truncated_pcm_refuses_other_partial_packets[earlier-source]` | PASS: strict guard | PASS |
| `test_check_output_truncated_pcm_refuses_other_partial_packets[output]` | PASS: strict guard | PASS |
| `test_check_output_pcm_odd_source_requires_both_d86_conditions[False-False]` | PASS: strict guard | PASS |
| `test_check_output_pcm_odd_source_requires_both_d86_conditions[False-True]` | PASS: strict guard | PASS |
| `test_check_output_pcm_odd_source_requires_both_d86_conditions[True-False]` | PASS: strict guard | PASS |
| `test_check_output_pcm_refuses_changed_timeline_runs[shift-after-30]` | FAIL: accepted changed timeline | PASS |
| `test_check_output_pcm_refuses_changed_timeline_runs[all-zero]` | FAIL: accepted changed timeline | PASS |
| `test_check_output_pcm_refuses_changed_timeline_runs[closes-gap]` | FAIL: accepted changed timeline | PASS |
| `test_check_output_pcm_refuses_changed_timeline_runs[opens-gap]` | FAIL: accepted changed timeline | PASS |
| `test_check_output_pcm_accepts_same_gap_with_different_packet_boundaries` | PASS: positive control | PASS |
| `test_check_output_pcm_accepts_the_manifest_packet_table` | PASS: measured control | PASS |
| `test_truncated_pcm_audio_survives_the_real_sink[55-38814-1]` | FAIL: verify_failed | PASS |
| `test_truncated_pcm_audio_survives_the_real_sink[70-49502-0]` | FAIL: verify_failed | PASS |
| `test_truncated_pcm_audio_survives_the_real_sink[85-60659-1]` | FAIL: verify_failed | PASS |

The opens-gap plant was refined after the first GREEN to open an additional
gap while preserving a pre-existing source gap; shift-after-30 remains the
contiguous-source plant. The same-gap control also re-chunks the two runs.
Neither plant changes a predecessor's expected result.

### Implemented rule and warning

| Mechanic | File:line | Behavior |
| --- | --- | --- |
| Source-PCM branch | `src/clearwater/io/video/verify.py:873` | Passes the probe's truncated fault to the private comparison; compressed branch still uses the unchanged packet rule. |
| `_pcm_totals` | `src/clearwater/io/video/verify.py:910` | Exact duration-to-sample arithmetic and codec-width payload count. Under D86, each included source packet stores `floor(size / bytes-per-frame)` and presents `min(declared, stored)`. Only its window's final packet may have a remainder. Output uses neither cap nor floor. |
| `_pcm_problems` | `src/clearwater/io/video/verify.py:972` | Enables D86 only for `truncated AND end is not None`; retains equal format/clock/first pts and admissible whole-prefix cut semantics. |
| Candidate extents | `src/clearwater/io/video/verify.py:1016` | Compares paired presented/stored totals from ONE admissible source prefix, never independent alternatives or intermediate totals. |
| Run merge and match | `src/clearwater/io/video/verify.py:965`, `:1053` | Merge only exact adjacency in file order; output runs must equal the SAME prefix's runs. Source gaps remain supported. The rule docstring explicitly binds equality in SOURCE ticks to the equal-time-base check. |
| Read-only warning result | `src/clearwater/io/video/verify.py:200`, `:903` | `PacketTable.pcm_dropped_bytes` recalculates the successful PCM verdict without mutation or I/O; `_PcmResult` is frozen and defaults dropped bytes to zero. No `check_output` signature/return change. |
| Granted warning insertion | `src/clearwater/io/video/encode.py:1105` | Append exactly one warning when matching D86 normalization floored bytes: `audio cut at the last whole sample frame; N bytes of a partial frame dropped`. Only this six-line insertion changes encode.py. |

The new integration node at `tests/test_io_video_encode.py:337` is parametrized
over all three ratios and is UNMARKED like the synthetic libx265 PCM control:
no gpu/footage/gui/slow/fullclip marker. It remuxes the committed fixture with
`-c copy -movflags +faststart`, truncates only its per-test derivative, checks
the probe fault and exact short payload, and calls `vf.encode_file` ->
`_RecordingSink(FFmpegVideoSink)` without checker bypass or command emulation.
It checks byte-identical decoded readable PCM, the existing cut-short warning,
and exactly one partial-frame warning for 55/85 percent, none for 70 percent.
No new committed media or fixture/manifest/generator/consumer edit.

| Derivative | Source / output packets | Complete samples | Final source bytes | Partial warning |
| --- | --- | --- | --- | --- |
| 55 percent | 39 / 39 | 38814 | 909 | Exactly one, N=1 |
| 70 percent | 50 / 49 | 49502 | 860 | Absent |
| 85 percent | 61 / 61 | 60659 | 647 | Exactly one, N=1 |

Independent evidence: `turn5_timeline_oracle.py` expands each real source and
output presentation into individual sample ticks, rather than using the
production run merger, and finds all three timelines equal. Results:
`turn5-timeline-oracle.json` / `.log`. Its first scratch glob did not account
for pytest's shortened folder names (StopIteration); corrected to find each
`cut-N.mov` under this run's basetemp and reran successfully. No product or
test change resulted from that scratch-driver correction.

Limit to carry into the report turn: a short trailing packet is one measured
trigger for sink re-chunking (70 percent: 50 source packets become 49 output
packets). The intact synthetic control retains its packet boundaries. The
cause of the intact owner's sources' re-chunking remains unknown and outside
this fix's scope; no owner's media was read to investigate it.

### Checks and verification loop

Every pytest invocation sets `PYTHONPATH=scripts`, unsets `PYTEST_ADDOPTS`,
loads `-p sandbox_mkdir_shim -p no:cacheprovider`, and uses a fresh basetemp
under `work/wp-d112/tmp/t5-*`. Runner outputs are files under this worktree.

| Check | Result | Evidence |
| --- | --- | --- |
| Initial new-node GREEN | 20 passed, 236 deselected | `turn5-green.log` / `.xml` |
| Initial keyword light run | 64 passed, 192 deselected | `turn5-light.log` / `.xml` |
| Final required keyword light run, both modules, `audio or pcm or check_output` | 64 passed, 192 deselected | `turn5-light-final.log` / `.xml` |
| Whole unit module | 126 passed | `turn5-units.log` / `.xml` |
| Explicit real-sink integration node, all three ratios | 3 passed | `turn5-real-sink.log` / `.xml` |
| Ruff on four changed Python files | All checks passed | `turn5-ruff-final.log` |
| Ruff format --check on four changed Python files | 4 files already formatted | `turn5-format-check-final.log` |
| Mypy | Success, 149 source files | `turn5-mypy-final.log` |
| Scope/identity and LF check | PASS | `turn5-scope-qa.log` / `.json`; final ledger QA below |

No predecessor row's assertion or expected result changed. `_pcm_check` only
adds a default-off truncated-fault switch. Both numerical owner shapes,
regular PCM, whole straddling packets, slack prefix pairing, all strict
refusals, the real-sink control and PCM-to-AAC plant pass in the final light
run. The three named kept-green rows are byte-identical to HEAD and pass;
`_seconds` and `_audio_problems` are also byte-identical. Evidence:
`turn5_qa.py`, `turn5-scope-qa.json`. No owner/trim/fullclip proof was rerun
in this remediation turn; the orchestrator's final gate/proof schedule stands.

| Suspected | Independently confirmed / rejected | Fix / final observation |
| --- | --- | --- |
| F1 D86 short/odd-tail refusal | Confirmed MAJOR by 3 failing unit acceptances and 3 failing real-sink derivatives; byte equality checked after GREEN | Source-only per-packet normalization, final partial-frame floor, exact normalized pair and warning; 3 real exports pass with identical readable bytes. |
| Lost complete sample might be excused | Rejected by 3 minus-one rows against exact normalized counts | All refuse with PCM presented-count diagnostics; no tolerance. |
| Exception might leak to earlier source/output or lack one enabling condition | Rejected by 5 strict guard nodes | All refuse; source cap/floor remains D86-only. |
| F2 timing hidden by equal totals | Confirmed MINOR by 4 RED timeline plants; gap-preserving positive control passes | Source-tick run equality fixes all four; source-gap refusal was not implemented. |
| Style/type slips in first GREEN | Confirmed: one long warning line, two tuple-concatenation lint items, one Fraction union annotation | Fixed; changed-file lint/format and full mypy pass. |
| Compressed-path or frozen-interface drift | Rejected by helper byte comparison, diff review and named unchanged test evidence | No compressed, video, data, mux, flag or interface behavior changed. |
| Final pass over rule, warning, tests, locks and evidence | No new finding | Required final light/unit/real-sink checks green; scope identity and LF assertions pass. |

### Cumulative round ledger and boundary

| Reviewer round | Verdict / disposition | Critical / major / minor / advisory | IN / OUT | NEW / REOPENED / pre-existing | Reverts | Product / test fixes THIS TURN | Transport / depth |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | F1/F2 remediated per CHARC; F3 BANKED; A2 PENDING | 0 / 1 / 1 / 1 | 2 / 1 | 2 / 0 / 1 | 0 | 2 ruled product fixes plus granted warning; 20 new test nodes (17 unit + 3 integration) | Dispatcher-run Claude; session 2 retired at 184370; current depth PENDING |

F1 and F2 are fixed and locally verified, not claimed independently converged.
F3 remains BANKED to CHARC for the accept's note; no row or code change.
Reviewer A round 2, Reviewer B, final three-leg gate, report and post-merge
V-P witness remain pending at their commissioned seats. No request to start
a Claude pass or heavy gate is made by this cell.

Locks: only verify.py, the one granted encode.py insertion, the two owned test
modules and this ledger changed. No footage, main-tree work or other worktree
opened; no mailbox, stash, commit, dependency, media/manifest, interface or
other product edit. Code/test files have zero CR; the appended ledger text is
ASCII and its final LF/scope/diff QA is `turn5-ledger-qa.log`. YIELD for A2.

## Session 3 / Turn 6: the report

Base `78d2a03e`, clean at entry. Dispatcher-supplied depth after turn 5:
106,962 tokens. Depth THIS TURN: PENDING -- dispatcher to fill from the
transcript; no cell estimate.

Wrote `docs/reports/wp-d112-pcm-audio.md`, following the headings and scale of
`docs/reports/wp-dr87.md`. It records DR-112 without owner stems, the four
accepted seat-experiment facts and the reconciled presented/stored counts,
the current PCM rule and D86 warning, the fixture/control and test-time
derivatives, per-turn RED/GREEN evidence, review rulings and explicit pending
reviews/gate/witness. It carries the short-tail re-chunking observation,
codec-tag distinction, unknown full-command cause and banked F3 limit.

Verification: relocated every report file:line against the unchanged source
at `78d2a03e`; checked figures against the brief and this ledger's turn-2,
turn-3, turn-4 and turn-5 evidence. Confirmed the turn-3 sandbox audit item
was closed by the dispatcher's three passing seat reruns. No product result
was rerun or promoted to final-gate/acceptance evidence. Report/ledger ASCII,
zero CR, report line lengths, no owner stems in report, code-anchor checks,
owned-file scope and `git diff --check` are recorded in
`work/wp-d112/turn6-docs-qa.log`. Corrected one source anchor to the exact
partial-frame remainder calculation during documentation QA; the final pass
finds nothing new. No product finding or scope deviation.

Only the report and this ledger changed. No footage, other worktree/main work,
mailbox, commit, stash, product/test/fixture/interface/dependency edit or
reviewer process. Reviewer A round 2 and B remain PENDING; the report will be
amended if adjudication changes the candidate. YIELD to the orchestrator.
