# WP-D112 - PCM audio sample extents and timing

Candidate status at `78d2a03e`: round-1 remediation is locally green.
Reviewer A round 2 and Reviewer B are PENDING. The final gate and post-merge
WP5.3 witness belong to the orchestrator. This is not an acceptance record.

## Changes

The mandatory post-encode check now distinguishes raw PCM from compressed
audio by the SOURCE `codec_name.startswith("pcm_")` branch at
`src/clearwater/io/video/verify.py:873`. Compressed audio retains the packet-pts
rule at `src/clearwater/io/video/verify.py:1067`; that function and its
`_seconds` helper are byte-identical to the pre-package implementation.

For PCM, the check compares the following, independently of packet boundaries:

- PRESENTED samples: sum of each packet's exact integral
  `duration * time_base * sample_rate`; STORED samples:
  `payload_bytes / (channels * packed_bytes_per_channel_sample)`. Both totals must
  match. `_pcm_totals`, `src/clearwater/io/video/verify.py:910`, uses packet
  facts, without falling back to container aggregates. Packed 24-bit PCM
  uses three stored bytes despite decoding to `s32`; codecs without a known
  fixed-byte payload rule refuse as unavailable sample evidence.
- The whole source stream when `audio_end` is None; otherwise a whole source
  packet prefix selected by packet START before the cut. A straddling packet
  contributes its whole extent. The existing two-microsecond `CUT_SLACK_S`
  permits alternative complete prefixes, not intermediate sample counts.
  Both totals and timing must match the SAME prefix
  (`src/clearwater/io/video/verify.py:1016`).
- Equal codec, time base, sample rate, channel count and sample format
  (`src/clearwater/io/video/verify.py:992`), and first packet pts
  (`src/clearwater/io/video/verify.py:1044`).
- Equal maximal contiguous RUNS, continuing only while
  `next_pts == pts + duration`. The merger is at
  `src/clearwater/io/video/verify.py:965`, the comparison at
  `src/clearwater/io/video/verify.py:1053`. Equality is in SOURCE ticks and
  depends on the equal-time-base requirement; the rule's docstring at
  `src/clearwater/io/video/verify.py:972` binds them together. A source gap is
  supported when the output preserves it.

D86 exception, CHARC `b44b0ee7`: only when the source probe reports
`truncated` AND an audio cut is set, each included SOURCE packet stores
`S_i = floor(size_i / bytes-per-frame)` and presents `min(D_i, S_i)`.
A partial frame may be floored only in the final source packet of the
compared window. Earlier partial source packets still refuse. OUTPUT packets
retain strict declared durations and aligned payloads: no cap or floor.
The output's exact presented/stored pair and runs must equal that normalized
source prefix (`src/clearwater/io/video/verify.py:952`, `:1017`).

When normalization drops partial-frame bytes, the read-only, default-zero
`PacketTable.pcm_dropped_bytes` result at
`src/clearwater/io/video/verify.py:200` supplies the warning count. The ONE
granted insertion at `src/clearwater/io/video/encode.py:1105` appends:

```text
audio cut at the last whole sample frame; N bytes of a partial frame dropped
```

CHARC `81ebcf52` grants that warning insertion only. There is no mux/flag
change; `check_output`'s signature/return and IF-5 `SinkReport` are unchanged.
PCM refusals are ASCII and identify `audio stream N (PCM)` and the failed rule.

## DR-112 measurements of record

WP5.3's `clips V-P` run on 2026-11-01 refused nine of seventeen owner iPhone
MOVs in the product's own post-encode check. The two refusal forms were:

```text
The finished video does not match what was written: audio stream 0: packet 119 at 24217/9600 s where the source has 120797/48000 s
99 packets in the output where 100 of the source's 100 were to be copied
```

All used mono 48 kHz `pcm_s16le`. Every refused source had irregular packets
before its last packet. One passing source also had an irregular packet;
their count or position cannot determine acceptance. Raw PCM packet
boundaries are demuxer chunking, so packet-list identity refused preserved
samples. Owner stems are retained only in the ledger.

The orchestrator's experiment, accepted by CHARC in `4bff0b93`, used the
product's own headless export and spawned worker, FFmpeg 9.0.2 Gyan full build.
The following are seat measurements transcribed from the brief and reconciled
by the turn-2 ruling, not owner-media experiments repeated by this cell:

1. A seat-only wrapper logged `check_output`'s problems and returned no
   problems so the two finished outputs were retained. It logged the SAME
   refusals as the pack build.
2. Decoding source/output audio to s16le gave byte-identical pairs:
   201624 bytes for one iPhone MOV, 268828 for the other. Stream facts matched:
   `pcm_s16le`, time base `1/48000`, start 0, and `nb_frames` 100812 / 134414.
   The reconciled PRESENTED/STORED pairs were 100720/100812 and 134400/134414;
   the container trims presentation before the end of the stored final packet.
3. One packet table changed from 100 packets to 99 by coalescing the last two
   source packets. The other's 133-packet table retained its count but moved
   a 736-sample packet boundary from pts 120061 to 121085, by 1024 samples.
   These changes preserved both totals and decoded bytes.
4. Three FFmpeg emulations retained packetization AND samples: stream-copied
   video, libx265 video, and a two-input NUT-pipe shape with the input `-to`
   cut. They used the sink's audio arguments, including `-copyts`, `-c:a copy`,
   `-movflags +negative_cts_offsets` and `-f mp4`. They did not reproduce the
   full product command's re-chunking. Outcome A: fix the PCM check, no mux fix.

## Regression and fixture evidence

Committed fixture: `tests/fixtures/video/pcm-irregular.mov`, manifest id
`vid-pcm-irregular`. Recipe `_build_pcm` at `tools/fixtures/video.py:766`
generates 45 BT.709 limited HEVC frames at 320x180, 30000/1001 fps, then joins
three mono 48 kHz s16le sine segments of 24024 samples each. Each segment uses
`asetnsamples=n=1024:p=0`; the concat demuxer stream-copies them into MOV.
Generation uses bitexact flags and strips metadata. The measured manifest
records 72 audio packets, with 472-sample mid-stream packets at indexes 23
and 47, 72072 presented/stored/decoded sample frames and 144144 decoded bytes.

`test_pcm_irregular_audio_survives_the_real_sink` at
`tests/test_io_video_encode.py:264` uses `video_fidelity.encode_file` and the
real `_RecordingSink(FFmpegVideoSink)`, including its two-input NUT pipe,
`-copyts`, audio copy and MP4 flags. The intact fixture's packetization
SURVIVES unchanged and its decoded bytes match: this is a CONTROL. The
numerical re-chunking unit rows carry the original RED.

The UNMARKED libx265 integration row
`test_truncated_pcm_audio_survives_the_real_sink` at
`tests/test_io_video_encode.py:337` creates faststart derivatives AT TEST TIME
from that committed fixture and retains 55, 70 or 85 percent of their bytes.
It uses the real sink without a checker bypass, verifies the truncated fault,
and compares byte-identical readable PCM. No extra media file is committed.

| Cut | Source / output packets | Readable samples | Final source payload | Partial-frame warning |
| --- | --- | --- | --- | --- |
| 55 percent | 39 / 39 | 38814 | 909 bytes | Exactly once, N=1 |
| 70 percent | 50 / 49 | 49502 | 860 bytes | Absent |
| 85 percent | 61 / 61 | 60659 | 647 bytes | Exactly once, N=1 |

RED/GREEN evidence, with full node records in `docs/proofs/wp-d112-ledger.md`:

| Turn / check | Result | Log under `work/wp-d112/` |
| --- | --- | --- |
| 2: original light RED | 21 failed, 12 passed, 192 deselected | `turn2-red-final.log` |
| 3: initial PCM GREEN | 24 passed, 80 deselected | `turn3-green.log` |
| 3: cut-window regression RED | 1 failed, subsequently fixed | `turn3-window-red.log` |
| 3: final light / whole units | 42 passed, 194 deselected / 109 passed | `turn3-light-final.log`, `turn3-units.log` |
| 4: unchanged refusal guards | 18 passed, 91 deselected | `turn4-guards.log` |
| 5: remediation RED | 13 failed, 7 passed, 236 deselected | `turn5-red.log` |
| 5: new-node GREEN | 20 passed, 236 deselected | `turn5-green.log` |

The turn-5 RED includes three already-refused minus-one cases whose diagnostic
named invalid source evidence or the wrong, unnormalized count. Their GREEN
assertions require the exact normalized sample count. Other RED nodes expose
the three rejected readable tails, four changed timelines and three failed
real-sink exports. Strict guards and positive controls remain green.

Kept green and unchanged: `test_check_output_names_each_mismatch`,
`test_a_cut_audio_stream_must_be_the_source_packets_before_the_cut`, and
`test_planted_audio_reencode_is_caught`. The original numerical PCM shapes,
regular control, independent presented/stored refusals, rate/format/first-pts
refusals, real-sink control and PCM-to-AAC plant also pass. The cell did not
rerun owner/trim/fullclip proofs; those records are not fresh cell measurements.

Turn-3 fixture selection recorded 44 passed, 3 failed, 301 deselected.
The three I/O-audit failures involved sandbox `nul` access and `cmd.exe /c ver`;
the dispatcher reran all three outside the sandbox, 3 passed, and CLOSED
that sandbox-only finding. No consumer assertion was weakened to hide it.

## Final-state cell checks

Turn 5 on the executable state committed as `78d2a03e`:

| Check | Result | Log under `work/wp-d112/` |
| --- | --- | --- |
| Both encode modules, `-k "audio or pcm or check_output"` | 64 passed, 192 deselected | `turn5-light-final.log` |
| Whole encode unit module | 126 passed | `turn5-units.log` |
| Explicit truncated-PCM real-sink node, all ratios | 3 passed | `turn5-real-sink.log` |
| Ruff on four changed Python files | All checks passed | `turn5-ruff-final.log` |
| Format --check on those four files | 4 files already formatted | `turn5-format-check-final.log` |
| Mypy | Success, 149 source files | `turn5-mypy-final.log` |

All pytest commands set `PYTHONPATH=scripts`, unset `PYTEST_ADDOPTS`, load
`-p sandbox_mkdir_shim -p no:cacheprovider`, and use distinct basetemps under
`work/wp-d112/tmp/`. These are light checks, not the final package gate.
This docs-only turn reruns no product test, lint or type check.

## Verification loop, locks and handoff

F1 was confirmed by unit RED and real-sink exports; normalization now preserves
every complete readable sample and rejects each one-sample loss. F2 was
confirmed by shifted/all-zero/closed-gap/opened-gap plants; run equality now
refuses them while accepting a preserved source gap with new packet boundaries.
An independent per-sample timeline oracle confirms all three real truncated
outputs (`work/wp-d112/turn5-timeline-oracle.json`), without using the run merger.
The final turn-5 rule/test/scope pass found nothing new.

Turn-5 scope QA confirms exactly the granted warning insertion in `encode.py`,
byte-identical compressed helpers and the three named kept-green test bodies,
and ASCII/LF changed text (`turn5-scope-qa.json`, `turn5-ledger-qa.log`). No
interface, dependency, mux/flag, video/data rule or local configuration change.
The cell opened no owner's footage, other worktree or main-tree working data.
The report and ledger are the only changes this turn; their ASCII/LF and diff
checks are recorded in `work/wp-d112/turn6-docs-qa.log`.

## Reviewer A round 1

Independent Claude Opus/high pass: `NEW_CRITICAL_MAJOR_FOUND`, with 0 critical,
1 major, 1 minor and 1 advisory. Evidence is the dispatcher's authorized
`C:/Users/rwsmy/clearwater-review-evidence/wp-d112/r1/review.txt`.

| Finding | Ruling / disposition |
| --- | --- |
| F1 MAJOR: truncated PCM rejected despite preserved readable samples | CHARC `b44b0ee7` adopts the D86-only exception; `81ebcf52` grants the warning insertion. Remediated and locally verified in turn 5. |
| F2 MINOR: later pts changes escape first-pts/totals checks | CHARC `b44b0ee7` adopts source-tick run equality and rejects blanket refusal of gapful sources. Remediated and locally verified in turn 5. |
| F3 ADVISORY, pre-existing: compressed source paired with a codec-relabelled output still accepts | BANKED to CHARC for the accept note; no code/test change or extra row in this package. |

Reviewer A round 2: PENDING. Reviewer B: PENDING. No convergence or acceptance
is claimed by this report. Amend these lines after the scheduled reviews.

## Limits

The intact synthetic fixture keeps its packetization through the real sink,
while the seat's two owner MOVs coalesced or moved boundaries. Why the full
command treats them differently is not established and remains outside the
fix scope. A short trailing packet IS one measured trigger: the test-time
70-percent derivative changes 50 source packets to 49 output packets while
carrying all 49502 readable sample frames. This does not explain the intact
owner sources' re-chunking.

The seat observed MOV `lpcm` becoming MP4 `ipcm`; codec-tag equality is not
required by this PCM rule. Codec name, decoded format, both sample extents and
timing remain checked. F3 remains banked: branch selection uses the SOURCE
codec, and compressed behavior is locked in this package.

The orchestrator owns the final three-leg gate after both reviews, including
the commissioned fullclip leg, and the post-merge WP5.3 `clips V-P` rerun,
then `page`, `page --check` and the tally. The nine owner exports have not been
claimed newly passing here. Register closure and the AD-30/F3 notes remain
CHARC's at acceptance.
