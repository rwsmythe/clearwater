# WP-DR113: V4 raw PCM fidelity reading

## Summary

V4 now recognizes raw PCM re-chunking as a fourth equivalence beside WP4.4's
orientation, SAR and mono-layout readings (`docs/briefs/wp-dr113-brief.md:28`).
For a source `pcm_*` codec, codec/time base/rate/channels/sample format must
match; PRESENTED and STORED sample totals and maximal contiguous timeline runs
must match in source ticks, which depends on equal time bases
(`tools/container_spike/compare.py:1182`, `:1224`). The side-data item uses this
reading only without discard flags or packet side data on either side;
otherwise it retains the per-packet rule (`tools/video_fidelity.py:1026`).
When `cut` is true, D86 caps kept source
packets at their stored samples and permits a partial-frame floor only on the
final KEPT source packet; output remains strict (`compare.py:1182`,
`video_fidelity.py:1003`). Successful packet `Item.note` names the reading and
both packet counts; record `notes` also carry the stream key
(`compare.py:1267`, `video_fidelity.py:1315`, `:1358`). This mirrors WP-D112's
post-encode check (`src/clearwater/io/video/verify.py:910`, `:972`) without
importing its audio reading: the instrument owns its width table and reads
`Facts`; the preexisting verify import serves video readable-end discovery
only (ledger, Session 2 / Turn 3, Implementation and contracts).

## The finding it pays

DR-113 was a faithful re-chunked PCM export reported DIFFERENT by packet-row
comparison. The orchestrator's RED record `work\wp3.10\dr113-red` on
`IMG_6731` contained 46 items, with 2 MANDATORY differences: audio packets
`[soun#0]` first differed at index 94, and audio priming/packet side data at
index 95. Nine BEST-EFFORT differences remained. These are the supplied seat
results in `docs/briefs/wp-dr113-brief.md:14`; this cell did not read that
record or owner footage.

GREEN witness (orchestrator seat, 2026-11-02 ~12:50Z, on the gated candidate
`2ef05dd9`): `tools/video_fidelity.py compare` over the same pair, out
`work\wp3.10\dr113-green`: EXIT 0; 46 items; DIFFERENT by class MANDATORY 0,
REQUIRED 0, BEST-EFFORT 9; MANDATORY + REQUIRED all SAME. Against the RED, the
item names are identical and exactly two statuses changed, both DIFFERENT ->
SAME: `audio packets passed through (pts, duration, size, MD5) [soun#0]` and
`audio priming and packet side data`, each with the note `PCM: compared by
sample extent and timeline runs; packets 100 -> 99`; the record's `notes` carry
it with its stream key `[soun#0]`. The nine BEST-EFFORT differences are
unchanged.

## Tests

The package adds 53 nodes in `tests/test_container_spike_compare_equivalences.py`,
7 in `tests/test_video_fidelity.py`, and 5 in `tests/test_io_video_encode.py`:
65 total. The original counts were 45/7/5; round-1 cleanup added six agreement
rows, an uncut partial-source note control and a two-track record row. Existing
PCM summary-note assertions now require stream keys (ledger, Turn 2: RED,
What was written; Session 2 / Turn 4, Added node outcomes and Commands).

At `a7e99af0`, 28 of the original 57 nodes were RED and 29 baseline GREEN;
all 57 passed at `b48c94b3`. Cleanup `586d08f2` preserved those passes and
passed all eight added nodes; its six intentional note-assertion failures
became GREEN. Final light results were 178 passed / 3 deselected for the
three V4 modules and 121 passed / 130 deselected for the brief's light run
(ledger, Session 2 / Turns 3 and 4, Commands and observed results).

The 23 agreement rows feed both readers the WP-D112 tables for IMG_6731,
IMG_6729, faithful gapful re-chunking, D86 55/70/85-percent cuts, separate
presented/stored sample loss, rate/format/channels/time-base changes, changed
gaps, earlier-source/output partial frames, first-pts-plus-one,
shift-after-30, all-zero pts, and negative/missing/fractional duration evidence.
Each asserts the expected product verdict and product pass <-> instrument SAME
(`tests/test_container_spike_compare_equivalences.py:249`, `:556`). Additional
controls reject AAC re-encoding, a one-tick shift, swapped packets,
unknown-width PCM, discard flags and side data (`:233`;
`tests/test_video_fidelity.py:348`).

`tests/test_io_video_encode.py::test_pcm_derivative_v4_through_real_sink`
derives two trimmed-presentation and three truncated sources from the committed
fixture at test time, retaining decoded-byte/product assertions and requiring
V4 plus notes. Only d86-70 proves re-chunking, 50 -> 49 packets. Isolated
durations were 3.452/3.110 seconds for the trim rows and 2.813/2.969/2.884
seconds for d86-55/70/85; no `slow` marker was needed (ledger, Session 2 /
Turn 4, Integration duration evidence). That turn's ruff/format/mypy checks
passed; no full-suite gate is claimed (same section, Commands).

## Reviews

Reviewer A round 1 (Claude) returned `NO_NEW_CRITICAL_MAJOR`: 2 MINOR and
6 ADVISORY. M1's helper-input change is disclosed below; M2's agreement gaps
are covered. A3 is an out-of-envelope limit; A4's note wording and A5's stream
keys are fixed; A6's preexisting window and A7's storage/rendering are limits;
A8's measurements required no marker change. Round 1 is converged with its
terminating cleanup (ledger, Session 2 / Turn 4, Every finding and its
disposition).

Reviewer B (Claude, the orchestrator's seat, on `fc167059`) returned
`NO_NEW_CRITICAL_MAJOR`: 0 MINOR, 5 ADVISORY, all banked (accept record
`docs/proofs/wp-dr113-accept.md`). Base-versus-head on the committed AAC
fixtures read identical items, notes and records; on `pcm-irregular.mov` only
the two target items changed.

Gate (three legs, on the rebased candidate `2ef05dd9`): parallel 6,572 passed,
1 skipped; serial 1,260 passed, 11 skipped; fullclip 7 passed; 0 failed;
collection 7,851 with identity; ruff, format, mypy and the harness gate clean
(accept record).

## Limits

F-B2: the PCM reading drops per-packet MD5, so it does not compare sample
CONTENT; decoded-sample MD5 is a possible later item, not built here. A3:
stored samples moved between packets while durations, totals and runs stay
equal read SAME in both readers; this needs a container whose `stts` and
`stsz` disagree (ledger, Session 2 / Turn 4, ADVISORY 3).

B-A3 (Reviewer B): for a cut source the side-data rule reads only the
source packets inside the readable window, so a discard flag or side data on a
source packet after the readable end does not send the item back to the
per-packet rule; that packet is never copied, and the per-packet rule trimmed
the source rows the same way.

A6: the instrument's preexisting D86 window is strictly `pts < end`, while
the product admits whole prefixes within `CUT_SLACK_S`. A D86 cap yielding a
nonintegral run end when the time base is not 1/sample_rate refuses in both
readings (`tools/video_fidelity.py:1003`;
`src/clearwater/io/video/verify.py:1014`; ledger, Session 2 / Turn 4,
ADVISORY 6). A7: the record stores the full runs list and renders source-tick
values in `exact()`'s seconds-style form (`tools/container_spike/compare.py:724`,
`:1220`; same ledger section, ADVISORY 7).

M1: the shared WP4.4 `_facts` helper gained `"sample_fmt": "s16"`; the
assertion of `test_synthetic_facts_self_comparison` is unchanged. Real ffprobe
reports that field; omitting it makes the PCM reader refuse missing evidence
(`tests/test_container_spike_compare_equivalences.py:67`, `:92`; ledger,
Session 2 / Turn 4, MINOR 1). The `mebx` tracks remain omitted under D105;
this package does not change their treatment (`docs/reports/wp4.4-mov-input.md:124`).

## Ledger pointer

`docs/proofs/wp-dr113-ledger.md` records RED/GREEN evidence, verification loops,
round-1 dispositions and pending acceptance work.
