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
