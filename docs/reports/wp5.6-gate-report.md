# WP5.6 - Phase 5 gate report

**Status: DRAFT, 2026-11-02.** Owner fields: **V2 / CP5: PENDING**;
**N6: PROPOSED, PENDING the owner's ruling**. CHARC fills these fields and
marks the report FINAL after the owner's decisions. Gate p5b is GREEN as
recorded below; this report makes no release claim.
Authority: [WP5.6 brief](../briefs/wp5.6-brief.md), status and Done.

Spec **v0.5.7**, section 11 (V1-V18), N1-N13; plan section 7 completion
pointers. Machine: the owner's laptop, **AMD Ryzen 9 7940HS, RTX 4070 Laptop
8 GB, Windows 11**. The owner's 2026-10-19 best-effort ruling permits figures
on a shared, non-idle host. Host/load caveats remain attached to measurements;
these are not controlled clean-host comparisons.
Source: [WP1.6](wp1.6-gate-report.md), machine paragraph; [WP5.2](wp5.2-performance-memory.md),
section 6.

| Result | Package | Report | Accept record / main commit |
|---|---|---|---|
| Automated acceptance matrix | WP5.1 | [Acceptance](wp5.1-acceptance.md) | [Accept](../proofs/wp5.1-accept.md), `0e8f0e00` |
| Performance, memory, D111 | WP5.2 | [Performance and memory](wp5.2-performance-memory.md) | [Accept](../proofs/wp5.2-accept.md), `2da5d0c7` |
| CP5 review pack | WP5.3 | [Review pack](wp5.3-review-pack.md) | [Accept](../proofs/wp5.3-accept.md), `91db201b`; subsequent DR-112 witness in the report |
| V7 export responsiveness of record | WP4.6 | [Export process](wp4.6-export-process.md) | [Accept](../proofs/wp4.6-accept.md), `bbb4ef3e` |
| Raw PCM product check | WP-D112 | [PCM audio](wp-d112-pcm-audio.md) | [Accept](../proofs/wp-d112-accept.md), `92d9ff77` |
| Raw PCM V4 instrument | WP-DR113 | [V4 PCM](wp-dr113-v4-pcm.md) | [Accept](../proofs/wp-dr113-accept.md), `6ff6f5d3` |
| D54 warning wording | WP-D54 | [Warning words](wp-d54-warning-words.md) | [Accept](../proofs/wp-d54-accept.md), `4ece5183` |

Accept commits above were checked with `git log --oneline -- <record>`.
The ledger maps every result to its source; the orchestrator independently
fact-checks it and runs Reviewer B (Claude). The turn-2 fact-check returned
FC-1..FC-3, dispositioned in the ledger; Reviewer B is still to run.
The brief replaces Reviewer A
with the trace table and that fact-check for this deterministic documentation arc.

## Result 1 - Phase-end gate

**Verdict: GREEN - static, collection identity, parallel, serial, fullclip and harness checks exited 0; no failing node.**

Run `p5b` is at the orchestrator's seat on main snapshot `1934bcbb` in the
separate gate worktree. It is product-identical to brief base `ac033be7`;
the intervening difference is the CHARC state document only
(`git diff --name-only 1934bcbb ac033be7`). This report does not track a
moving main HEAD. The phase-end fullclip leg is required by CLAUDE.md,
Conventions. Authority for exit, counts and supplied timings is
`work/wp5.6/gate/summary.txt` (lines 1-14); skip reasons come from the
transferred leg logs. On 2026-11-02 the gate started **20:57:01Z** with
**57G C: free** and ended **22:06:38Z** with **52G C: free** (summary
lines 1 and 14). This reporting cell read those files and ran no gate leg.

| Leg | Exit | Count line | Wall s / supplied timing scope | Comparison figure and source |
|---|---|---|---|---|
| Static: ruff check / format / mypy | 0 / 0 / 0 | `All checks passed!`; `311 files already formatted`; `Success: no issues found in 156 source files` | UNTRACED: wall times not supplied | No comparison figure requested |
| Collection identity | 0 for all four collections | `7877 tests collected in 3.14s`; `6598/7877 tests collected (1279 deselected) in 3.12s`; `1272/7877 tests collected (6605 deselected) in 3.10s`; `7/7877 tests collected (7870 deselected) in 3.20s`; `identity: union 7877 dup 0 diff-vs-all 0` | Reported collection times: all 3.14, parallel 3.12, serial 3.10, fullclip 3.20; enclosing wall not supplied | Parallel + serial + fullclip = all; CLAUDE.md, Conventions |
| Parallel | 0 | `6597 passed, 1 skipped, 5 warnings in 512.86s (0:08:32)` | 515 (summary wall) | WP-T6 714 s (714.41 s), report Gate |
| Serial | 0 | `1261 passed, 11 skipped, 6605 deselected, 1 warning in 2041.95s (0:34:01)` | 2,046 (summary wall) | WP-T6 1,389 s (1,389.24 s), report Gate; WP-DR113 2,036 s, accept Gate |
| Fullclip | 0 | `7 passed, 7870 deselected, 1 warning in 1568.04s (0:26:08)` | 1,569 (summary wall) | WP-T6 about 26 min (1,556.05 s, W4); WP-D112 2,635 s, accept Gate; WP-DR113 1,595 s, accept Gate |
| Harness | 0 | `Ran 382 tests in 21.664s OK (skipped=1)` | 21.664 (test runtime; enclosing wall not supplied) | No comparison figure requested |

Timing scopes are preserved: the summary's parallel/serial/fullclip wall
seconds are distinct from pytest's elapsed figures inside the literal
count lines. Static wall times and separate enclosing walls for collection
and harness are **UNTRACED** in the supplied summary; no estimate replaces
them. The ruff success wording is from `ruff.txt:1`; the summary records
its exit only. Format/mypy counts are summary lines 3-4.

Skips by recorded reason (product logs, `-rs`):

| Leg | Count by reason | Log source |
|---|---|---|
| Parallel | 1: `swscale reads a yuvj format as full whatever in_range says (refused instead)` at `tests/test_color_roundtrip.py:123` | `parallel.log:111` |
| Serial | 11 absent look-check frames: 1 `the look-check frame is absent` at `test_app_v8_v18.py:134`; 5 + 1 `look-check frame absent` for `GX011625_0024.925.png` at `test_methods_assembly_v8.py:44` / `test_wp41_v8.py:193`; 4 for `GX011625_0114.648.png` at `test_methods_assembly_v8.py:44` | `serial.log:1910-1913` |
| Fullclip | 0 skips; all 7 passed | `fullclip.log:174`; summary line 12 |
| Harness | 1 skip, name/reason not reported by the supplied nonverbose log (UNTRACED); no reason inferred | `harness.txt:12-16`; summary line 13 |

The product skips are the standing swscale refusal and archived look-check
frames, not new failures. The archive provenance is WP-DR113 accept, Gate,
and the 2026-10-29 prune record's MOVED section; log paths are reduced to
file names here.

Comparison sources: [WP-T6](wp-t6-gate-sizing.md), W4 and Gate;
[WP-D112 accept](../proofs/wp-d112-accept.md), Gate and Dispositions;
[WP-DR113 accept](../proofs/wp-dr113-accept.md), Gate.
The brief calls WP-D112 the last fullclip figure; WP-DR113 records a later
1,595 s run. Both are carried so the p5b fullclip result can be compared
against WP-T6 and WP-D112 as commissioned, with the newer record visible.
p5b fullclip wall **1,569 s** is near WP-T6's **about 26 min** (its W4
reported **1,556.05 s**), **1,066 s shorter** than WP-D112's **2,635 s**,
and **26 s shorter** than WP-DR113's **1,595 s**. These are historical
gate timings with differing host conditions, not a controlled speedup claim.

**DR-86 trigger fires:** this phase-end serial wall is **2,046 s** against
about **25 min = 1,500 s**, exceeding the threshold by **546 s** (summary
line 11; register DR-86). For context, WP-T6 recorded **1,389.24 s** and
WP-DR113 **2,036 s**. Paydown disposition remains CHARC's / the owner's;
this report neither commissions a suite-cost pass nor adds a register row.

## Result 2 - Acceptance matrix carried forward

The source roster is [WP5.1, Acceptance matrix](wp5.1-acceptance.md#acceptance-matrix),
accepted at `0e8f0e00`. This is one row per acceptance id, including its
N10 and D91 rows; the node addresses remain in that report. PASS below
means the cited result of record, with its limits, rather than a new run
by this reporting cell. Plan section 7's WP5.1 and WP5.2 completion pointers
identify the handoff.

| ID | Result of record and disposition | Source |
|---|---|---|
| V1 | PASS: stage correctness on CPU/GPU, both compensation methods, caps, kernels, statistics ordering and edge cases. | WP5.1 Acceptance matrix and V1 discussion; accept `0e8f0e00` |
| V2 | PENDING CP5: owner's preference >=80% and no obvious artifacts (D65); no automated preference oracle. | WP5.1 V2; spec D65 / V2; WP5.3 current report |
| V3 | PASS: region-based synthetic flicker <=25% of unsmoothed for each measure. No truly static real clip identified; real subjective flicker belongs to V2. Chapter seam deferred with chapter handling to v2 (CP1). | WP5.1 Acceptance matrix / V3 discussion; spec D64 / V3 and v0.5.3 change note |
| V4 | PASS: fixture and real-trim mandatory/required fidelity; best-effort creation-time loss remains DR-111. Raw PCM product check fixed by WP-D112; V4 instrument GREEN on IMG_6731.MOV, 46 items, mandatory/required all SAME, best-effort DIFFERENT 9. | WP5.1 V4 observations; WP-D112 accept; WP-DR113 accept, GREEN witness |
| V5 | PASS: photo metadata, depth, ICC and orientation; two independent decoders stand in for multiple viewers. Windows Photos/browser viewing remains an optional owner CP5 leg. | WP5.1 Acceptance matrix / V5 observations |
| V6 | PASS: unsupported/damaged input handling and literal BT.709/limited warning; WP-D54 fixed the export warning. | WP5.1 V6 observations; WP-D54 accept `4ece5183` |
| V7 | PASS against 100 ms longest gap: (a) 18, (b) 19, (c) 39, (d) 56, (e) 48, (f) 50.6 ms. (c)/(e) are WP4.6's accepted figures; its 67 ms batch control does not replace (d). DR-98 CLOSED. | WP5.1 V7 figures table; WP4.6 accept, V7 of record, `bbb4ef3e` |
| V8 | PASS with standing archived-frame availability skips. AD-11: 1:1 exact; k>1 mean <=1/255, still p99 <=2/255 at k=2 and <=4/255 at k=4; video k=2 p99 <=2.5/255. | WP5.1 Acceptance matrix / V8 figures and skip table |
| V9 | PASS within AD-11 pre-encode max 2/255, mean 0.2/255. Runner post-encode is separately characterised at mean <=3.5/255, not proof of the encoder-free bound. | WP5.1 V9, N10, provenance and tolerances |
| V10 | PASS: numbering, cross-format clashes, existing outputs and sources unchanged. | WP5.1 Acceptance matrix / provenance and tolerances |
| V11 | PASS: cancellation, crash/disk-full cleanup and next-start leftovers. Deterministic D85 same-file probe is the witness; crash race's allowed not-observable skip was not observed in recorded successful runs. | WP5.1 V11, STOPs and SKIPs |
| V12 | Deferred to v2: chapter grouping. | WP5.1 Acceptance matrix; spec V12 |
| V13 | PASS: preset round trip. | WP5.1 Acceptance matrix / V13 discussion |
| V14 | PASS: all six N5 results with decisions recorded; prototype gate CLOSED 2026-10-20 at CP3. This does not retroactively pass the original prototype speed target. | WP5.1 V14 discussion; WP1.6 status and six-result table |
| V15 | Measured peaks meet 16 GB decimal in the recorded cases: synthetic 5.3K 8:7 video tree RSS 5,599,490,048 B (5.599490 GB; 5,340.090 MiB), device 7,085 MiB; synthetic 48 MP PNG16 automatic CPU tree RSS 6,635,884,544 B (6.635885 GB), device 117 MiB; forced CPU RSS 6,168,494,080 B (6.168494 GB). Largest cited owner photo IMG_6690 (24.5 MP HEIC) RSS 1,926,164,480 B GPU / 3,138,392,064 B CPU. D111 witnessed below; supported-photo-resolution choice remains the owner's. | WP5.2 sections 1, 3-4; accept `2da5d0c7` |
| V16 | Measured full-clip GPU c3 NVENC: GX011627 cold median 10.888984 min/min; GX011625 sustained 10.779005. Within current interim 25 min/min at 4K; final N6 re-set is the owner's. Synthetic 5.3K 8:7 40.331778 is best-effort, outside the 4K target. | WP5.2 sections 1-2; spec D106 / N6; accept `2da5d0c7` |
| V17 | PASS: unchanged reopen skips decode; cache-format mismatch triggers reanalysis. | WP5.1 Acceptance matrix and cache discussion |
| V18 | PASS: corrected provisional frame precedes completion and updates to smoothed statistics. Real-trim H12 strengthens the prior not-None check; full-clip record remains WP4.3's. | WP5.1 V18 figures of record |
| N10 / D92 | PASS: repeated pre-encode pixels on one device bit-identical; CPU/GPU bounds max 2e-3, mean 2e-4 in [0,1]. Encoded-byte identity is recorded, not required. | WP5.1 N10 / reproducibility discussion |
| D91 | PASS: default-on parseable provenance with app version, parameters and source name only; disabled video comment absent; photo coverage in V5. | WP5.1 Acceptance matrix / provenance discussion |

Decision: carry these results and their stated limits into Phase 5 close.
The owner decides V2 at CP5 and the N6 re-set; CHARC records both.
The current CP5 pack is ready at `work/wp5.3/index.html`: 128 items,
126 done and 2 expected HLG refusals, failed 0, pending 0. Its 115 headline
items and 11 candidates are available and unjudged. Coverage is not preference.
Source: WP5.3 report, opening status and empty tally. Its earlier accept record
still records 117 done / 9 V-P failures; the subsequent nine-item WP-D112
witness in the current report supersedes that historical build state.

## Result 3 - D111 automatic CPU fallback witness

WP5.2 R3 / W52-2 default-device exported a generated 8064x6048 RGB16 PNG
(48,771,072 pixels), not an owner photograph. With `force_cpu=false` it
recorded **`CPU: estimate 11,649 MiB exceeds free 7,064 MiB`**,
`automatic_fallback=true` and `memory_capacity_fallback=true`.
Runner exit 0, completed PNG16, no failed checks; tree RSS was
6,635,884,544 B (about 6.6 GB). The adjacent forced-CPU leg says
`CPU: forced` and is not the automatic witness.
Source: WP5.2 sections 3-4; accept, W52-2 and D111 disposition.

Decision: D111 engagement is demonstrated for the estimated-not-to-fit
photo branch. DR-114 remains a separate cross-process pressure limitation.
No CPU/GPU AD-11 comparison exists for this 48 MP leg because GPU admission
was refused; WP5.2's video post-encode characterisation does not prove
pre-encode AD-11. CHARC's accept disposition needs no new D111 row
(WP5.2 accept, Windows / Dispositions and Reviewer B B-6).

## Result 4 - Debt register through DR-115

Source of authority: [debt register](../debt-register.md), rows DR-1..DR-115.
This snapshot has **64 rows not wholly CLOSED** (including PARTLY and the
DR-44 row still headed OPEN) and **51 wholly CLOSED rows**. A row with a
closed subpart remains listed below. Paydowns/triggers are carried from the
register; where it names only a trigger, no new remedy is invented.
CHARC owns register changes; the owner commissions phase-boundary paydown.

| OPEN / partial row | Remaining issue and recorded paydown / trigger |
|---|---|
| DR-1 | Windows path-form test gap. Trigger: change the local-config path rule or a UNC/drive-relative report; no separate paydown named. |
| DR-2 | First GPU only in environment parsing. Trigger: second GPU or indexed GPU selection. |
| DR-6 | Intact-header truncated photos inventory as successes. Trigger: incomplete download or pixel reader; the reader must validate pixels. |
| DR-7 | HEIC inventory orientation uses EXIF, not irot. Trigger: non-Apple HEIC. |
| DR-8 | Size-0 box before meta yields graceful rotation-unreadable note. Trigger: a real file with that note. |
| DR-10 | CSV formula injection from hostile names, outside envelope. Trigger: untrusted footage. |
| DR-11 | Prototype 16-bit RGB loses precision / no HEIC reader. WP1.3/WP1.4 commissioning picks licensed reader and HEIC scope; CHARC owns it. |
| DR-12 | 3C paper's mask kernel unverified. WP1.3 tuning verifies the paper and default. |
| DR-13 | Contrast weight calibration owed; Advanced exposure did not calibrate it. WP1.3 look-check tuning / WP2.1 outcome. |
| DR-15 | B-frame edit-list convention question remains; hypothesised nonzero owner example absent. WP2.1 rules the convention, WP3.10 tests presentation on iPhone. |
| DR-16 | Spike containment check/use junction race, outside threat model. Product 8.4 safe writing must prove its form. |
| DR-20 | Instrument-only items (2),(3),(5),(8),(9): PTS deduplication, percent paths, cover art, record provenance and test gaps. Any reuse beyond WP1.4 re-reads row; product ownership/paydowns remain as recorded. |
| DR-22 | Temp guard limits. Early plugin if pre-conftest writes revisited; next guard/helper touch fixes (4)-(9), retests fixture containment. Trigger is guard itself, not additive conftest changes. |
| DR-25 | Only (3) open: provisional staged smoothing/default evidence. The >=182-frame staged run is assigned to WP5.2 by the register; WP5.2 accepted at `2da5d0c7` without it (neither report nor accept record mentions DR-25 or a staged run). AD-3 remains PROVISIONAL; disposition CHARC's. |
| DR-27 | Unreadable footage lookup can skip; stale chapter docstring. Next local-config/affected-test touch distinguishes unreadable from absent and corrects text. |
| DR-29 | Look-check CLI/cache validation limits. Next lookcheck touch or WP5.3 reuse rejects shallow --part and hashes changing sources. |
| DR-30 | Noise edge-test and GPMF strict parsing gaps. Reuser adds Immerkaer edge test / strict nesting, padding and SCAL rules or reference parser. |
| DR-31 | Spike PNG keyword and advisory timing gate. Product writer enforces keyword rule if adopted; future timed instrument requires idle gate or records absence. |
| DR-34 | Preset no-replace prediction, corrupt-settings set-aside failure, logging reconfiguration limits. Next presets/settings/log touch (WP3.17/WP3.20) or loss report; row names no further remedy. |
| DR-35 | (a) reserved stem refused rather than renumbered; (d) NumPy import dependency. Refusal shown by WP4.3; owner decides renumbering; (d) unchanged. |
| DR-36 | (c)-(f) partial-tag warning, malformed tails, fraction coercion and whole-file tail decode. WP3.9 consumer touch or another ffprobe build entering envelope. |
| DR-37 | Only (c): local config permits footage inside working folder. Next tools/local_config.py touch. |
| DR-39 | (b) noncontiguous RGB not refused; (c) widened conversion coverage partial, (d) float bit-depth acceptance out of envelope. Consumer briefs / widening supported set trigger. |
| DR-40 | Per-call constant uploads remain recorded; performance fix stays WP3.21's. |
| DR-41 | Custom codec id reuse can collide. First product nonregistered codec consumer replaces pid/id with registry or per-object token. |
| DR-42 | Non-ICC PNG/TIFF colour, hostile PNG checks, WhiteIsZero alpha. Owner wide-gamut report / first PNG-TIFF, hostile-input requirement, or next tiff.py touch respectively; invert colour samples only for (c). |
| DR-43 | Dropped EXIF has no GUI warning signal; owner photos showed no drops. Next io.photo touch or lost-metadata report; reader-side signal needs interface/warnings design. |
| DR-44 | Row still headed OPEN although (a)/(b) ADDRESSED and (c) CLOSED/reconfirmed. Preserve its recorded triggers: exact-PTS decode signal, message owner, real-job close/cancellation; no fresh unresolved subpart inferred. |
| DR-45 | (a) concurrent public FrameStream.close can return before shutdown. First cross-thread consumer / WP4.2 routes public close through shutdown so caller waits. |
| DR-46 | Mixed bool/number handmade records accepted. Next Y-2 checker touch refuses bool elements in method and store. |
| DR-47 | (b)/(c) cancellation near completion/publication. Next analysis/engine.py touch; serialise cancel with final publication without progress under lock. |
| DR-49 | Future parameters beyond 15-decimal spin-box resolution. New such schema widens control or refuses schema at install. |
| DR-51 | Only (b): oracle does not reject transient position update during drag. Next drag-lane touch adds intermediate-state check. |
| DR-56 | Audio sub-packet tail trim unexamined. Owner audible-tail report triggers WP4.x; otherwise documented limit. |
| DR-57 | Only (d): integer rotation comparison, unreachable with current writer. No paydown trigger named. |
| DR-58 | (a) first NVENC GPU, owner hardware trigger; (b) two test launches retain FFREPORT residual. Product spawn helper closed (b); (c) closed. |
| DR-59 | UTF-16/compressed XMP scan gap. First iTXt PNG or generator XMP adds marker/GPS and inflated-iTXt plants. |
| DR-60 | Malformed fixture checker limits. Next regeneration or first committed real HEIC bounds boxes, validates format/rate, checks duration count/stderr. |
| DR-66 | Worker-only unsafe temp branch reasoned, not executed. Worker temp derivation change or guard-test touch triggers; serial/fullclip must stay without -n. |
| DR-69 | Device-wide job estimate bench-only, frozen IF-8 gap. If GUI shows total, CHARC interface decision; otherwise remains bench-only. |
| DR-70 | Export analysis-bound; optimise analysis, not stream step. Owner wish below N6 / WP5.2 remeasure; shipped-build reread leaves lever unchanged. |
| DR-83 | Cache write through planted link. Next cache touch checks is_link before every write, with junction test. |
| DR-86 | Further serial-cost candidates, not additive predictions. Owner suite-cost commission or phase-end serial wall >about 25 min triggers. Trigger FIRES at p5b: 2,046 s >1,500 s; paydown CHARC's / the owner's. |
| DR-88 | Trim fixture self-check trusts plan. Next fixture touch adds independent cut derivation beside plan time. |
| DR-89 | Missing removable-drive journal entry discarded. Next startup-journal touch or stale-partial report; keep entry until seen again is a design candidate. |
| DR-90 | Clear cache can fail another clip's export. Next Clear/export-cache coupling touch exposes export activity and refuses Clear during it. |
| DR-91 | Frozen IF-10 reason repr can disclose values. Next IF-10 ruling or unredacted consumer routes through redactor / names field without value. |
| DR-92 | Escaped mixed-separator Unicode redaction gap, no product producer. Next redactor touch or such product text adds forms / normalises before escape. |
| DR-95 | Data tracks paired by position can falsely report gpmd missing. Next verify.py touch or mixed-track source pairs by codec tag/order with RED test. |
| DR-96 | Startup test races timeout/delay. Next startup/test touch makes overrun event-controlled. |
| DR-97 | V4 records normalised values and spurious translation note. Next compare.py touch preserves raw values and emits note only for nonzero translation. |
| DR-99 | (a) sampler-start bound load-sensitive: next bench/test touch or second gate failure; align clocks or reasoned bound. (b) frame-release timing bound: slow marker in WP5.3 witness read-back, covered by WP5.2 gate. Register remains OPEN. |
| DR-100 | Source matching temporary pattern can be deleted on next start. Next naming-pattern/cleanup touch; exact journal paths or age check are remedy candidates. |
| DR-101 | Last video analysis retained while photo open. Next app/main.py touch drops adapter on photo change with test. |
| DR-103 | Malformed child JSON progress floods warnings; unreachable shipped worker. Next export_process.py touch classifies JSON failure as invalid progress and fixes docstring. |
| DR-104 | D87 cache growth charged to output volume, scratch outside GUI accounting. Next D87/cache-layout touch rechecks cache volume when different; seeding requires CHARC decision. |
| DR-105 | Export failure text may carry full path. Next jobs/export.py failure-text touch names last component for user, full path only in log. |
| DR-106 | Unused held/progress test sinks. Next owner of both tests re-points/retires window driver, then deletes helpers. |
| DR-107 | Open warning incorrectly says limited for full-range source. Owner disagreement report or next probe/messages touch aligns resolved-range branches with tests. |
| DR-108 | Intermittent GUI export-panel test deadlock. Second occurrence STOP, or next rig/test touch runs 50 times under concurrent pytest with timeout; capture stacks on reproduction. |
| DR-110 | EXIF-only sRGB JPEG spuriously assumed. Owner warning report or next colour.py touch reads ColorSpace 1 declared; 2/65535 untagged, test each. |
| DR-111 | Best-effort creation time lost on three carriers. Owner export-date sorting report or next metadata mapping carries container/stream tags and reruns real-trim V4. |
| DR-114 | WDDM per-process free memory hides external GPU pressure. Real held-export evidence benign; failure/stall with another GPU app triggers device-wide-read vs documented-limit owner decision, post-v1 candidate. |
| DR-115 | No encoder-stall detector; force-cpu processing still feeds NVENC. Single repeat completed, so intermittent. Stopped progress with live encoder triggers; post-Phase-5 owner scopes watchdog and encoder preference. |

The **two product findings of Phase 5 performance/memory work** are DR-114
and DR-115 (the brief's Phase 5 findings pair). This does not erase earlier
acceptance findings such as DR-102, DR-111 and the now-closed DR-112.

**DR-114 cause / evidence / paydown.** CupyBackend's free-device reading
uses cudaMemGetInfo plus pool free blocks, per-process under WDDM. A touched
external hold did not change a second process's reported free bytes.
W52-2 R2 held 5,861 MiB externally; device-wide free read 1,421 MiB.
The whole-GX011627 export completed on GPU, exit 0, 4 min 4 s versus
4 min 3 s free-card; the first 30 decoded frames were identical.
That measured case is benign; allocation failure remains unmeasured.
A device-wide read beside the per-process operand or a documented limit
is an owner product decision if the case fails/degrades; nothing was tuned.
Source: register DR-114; WP5.2 sections 4 and 6. The report notes the
holder readings do not prove constant residency/free memory throughout.

**DR-115 cause / evidence / paydown.** The product has no encoder-progress
watchdog. In W52-2 forced CPU processing with auto=NVENC stopped near
670/681 frames; the encoder thread spun with no I/O, decoder/export idle,
pipe full. The partial stayed at 82,177,867 B; after about 35 min the seat
ended only the encoder, and the product failed exit 1 and removed the
partial under D85. The underlying NVENC hang cause is not established.
One W52-3 retry completed exit 0 in 109 min 45 s (9.67 s/frame):
intermittent, one occurrence in two. `--force-cpu` moves processing, not
encoding. Paydown is an owner-scoped worker watchdog (no pipe read while
frames wait => fail with encoder named and D85 cleanup), plus a decision
whether CPU/fallback processing should prefer software encoding.
Source: register DR-115; WP5.2 section 6 and accept Windows.

Wholly CLOSED rows, with closing commits only where the register supplies
them (no commit inferred from dates or a linked record):

| Closing commit | Rows |
|---|---|
| Not supplied as a closing commit | DR-3, DR-4, DR-5, DR-14, DR-32, DR-64 |
| `f6a34a4` | DR-9, DR-21 |
| `47bc6d6` | DR-17, DR-18, DR-26 |
| `ad15ab4` | DR-19, DR-38 |
| `47235b6` | DR-23 |
| `8c9d780` | DR-24 |
| `ba6e923` | DR-28, DR-48 |
| `2aca60e` | DR-33 |
| `28c4a75` | DR-50, DR-52, DR-61, DR-62, DR-68, DR-75, DR-82, DR-84 |
| `dbb5858` | DR-53, DR-54, DR-55 |
| `7e228fb` | DR-63 |
| `4933a45` | DR-65 |
| `ff234ee` | DR-67, DR-71, DR-73, DR-74 |
| `2da5d0c7` | DR-72 |
| `649be3d` | DR-76, DR-77, DR-81, DR-85 |
| `3aa25a5` | DR-78, DR-79 |
| `3cedac6` | DR-80 |
| `f78e92c` | DR-87, DR-93, DR-94 |
| `bbb4ef3e` | DR-98 |
| `4ece5183` | DR-102 |
| `5b922662` | DR-109 |
| `92d9ff77` | DR-112 |
| `6ff6f5d3` | DR-113 |

DR-62's parent-lock confirmation at WP4.6 `bbb4ef3e` is a later note,
not a second closure.

## Result 5 - N6 proposal for the owner

**PROPOSED, PENDING the owner's ruling.** CHARC decision request
`15f100ae`, posted 2026-11-02T20:51:43Z, recommends:

> Export takes at most about 12 minutes of processing per minute of 4K
> footage on the owner's laptop, end to end including decode and encode,
> in the owner's recording modes; 5.3K is supported but best-effort on speed.

This is CHARC's proposal, not the current spec. D106 / N6 today remains
**interim 25 min/min**. Sources: [AD-21](../decisions.md), note committed
at `51a0cfd4`; WP5.6 brief, Content 6; spec D106 and N6.

| Evidence for ruling | Figure | Source / scope |
|---|---|---|
| GX011627 c3 NVENC cold median | 10.89 min/min versus WP3.21 9.78, +11.3% | WP5.2 section 2, W52-1; full clip, in-process |
| GX011625 sustained | 10.78 versus WP3.21 9.58, +12.5% | Same, sustained full clip |
| Historical GUI worker margin | +7.3..8.2%; near 11.7-11.8 min/min indicative GUI projection in CHARC's proposal | WP4.6 V7 window; WP5.6 brief Content 6 |
| Synthetic 5.3K 8:7 | 40.33 min/min | WP5.2 section 2; supported, best-effort |

The near-11.7-11.8 figure is a proposal-side projection from the historical
margin, not a newly measured GUI rate: WP5.2 section 2 explicitly does
not manufacture an adjusted rate. The historical comparison includes cold
worker analysis versus a complete GUI cache, not pure process-start cost.
Shared-host/load/temperature conditions do not isolate a code regression.
Alternatives in the request: **15 min/min**, retain interim **25**, or a
**clean-host re-measure**. The owner decides; CHARC writes the ruled figure.

## Result 6 - Prune candidates for the owner's word

No prune is performed by this package. All current sizes below come
**only** from `work/wp5.6/prune-inventory.txt`, the orchestrator's seat
snapshot (main work sizes 2026-11-02T20:54Z, worktree list 21:12Z;
orphan/report-worktree measurements added 21:22Z).
Units/rounding are preserved as recorded; parent and child entries overlap,
so these are not additive reclaimable-space totals. Archive state is not
proved by a nonzero work-folder size; retained evidence must be checked
before any later authorised prune.

### Main work folders by package

| Package / folder | Recorded size | Candidate / keep condition |
|---|---|---|
| WP5.3 `work/wp5.3` | 16G | KEEP: CP5 pack and tally |
| WP5.2 `work/wp5.2` | 1.1G | Candidate after facts of record retained; whole-clip input copy named below |
| WP3.6P `work/wp3.6p` | 1.4G | Candidate after facts retained; distinct from previously archived worktree outputs |
| WP3.6 `work/wp3.6` | 3.8G | Candidate after evidence check |
| WP2.1S `work/wp2.1s` | 594M | Candidate after evidence check |
| WP4.3 `work/wp4.3-c6` | 314M | Candidate after evidence check |
| WP4.2 `work/wp4.2` | 217M | Previous prune explicitly kept this; renewed owner word required |
| WP4.1 `work/wp4.1` | 65K | Candidate; related basetemps in inventory |
| WP3.21 `work/wp3.21` | 41M | Oracle already archived; remaining folder requires check |
| WP3.14 `work/wp3.14` | 38M | Candidate after evidence check |
| WP3.10 `work/wp3.10` | 940K | Previous prune explicitly kept this; renewed owner word required |
| WP3.4 / WP3.1 | 48K / 20K | `work/wp3.4`, `work/wp3.1`; candidates |
| WP1.5 / WP1.5-B | 141M / 261M | `work/wp1.5`, `work/wp1.5-B`; candidates |
| WP1.3 witness | 314M | `work/wp1.3-witness`; candidate, distinct from archived CP2 pack |
| WP1.2A / A-B / A-B2 | 144K / 60K / 36K | `work/wp1.2a`, `work/wp1.2a-B`, `work/wp1.2a-B2`; candidates |
| WP4.2a / WP4.2b | 457K / 807K | `work/wp4.2a`, `work/wp4.2b`; candidates |
| WP-T1 QA / WP-T2 / WP-T5 / WP-T6 | 124K / 40K / 8.5M / 44K | `work/wp-t1-qa`, `work/wp-t2`, `work/wp-t5`, `work/wp-t6`; candidates after evidence check |
| Orchestrator g28 / g29 / g30 / g31 / g32 | 120K / 22M / 1.5M / 3.0M / 27M | `work/orch-g28` through `work/orch-g32`; candidate records/basetemps |
| Orchestrator g33 / g34 / g35 / g36 | 3.1G / 3.3M / 6.5M / 1.5M | `work/orch-g33` through `work/orch-g36`; preserve gate/window facts first |
| Shared fixtures / reports / CHARC handoff | 86M / 16K / 28K | `work/fixtures`, `work/reports`, `work/charc-handoff`; KEEP pending owning seat's word |

The inventory also enumerates individual WP4.1/WP4.2 review/reproduction
basetemps and loose gate logs. These are candidate support material only
after evidence retention; their individual sizes remain in the inventory,
not an inferred package aggregate.

### Worktrees

The inventory's `git worktree list` was checked against the live read-only
listing. Worktree sizes below are the inventory's, not a new scan.
Released package trees retain nonempty ignored work folders; **unarchived
output status is not established by this inventory**. The accept records
release WP-D112, WP-DR113 and WP5.2 after merge; WP5.1's accept held it until
CHARC's accept-side commit, so confirm release before removal.

| Worktree | Whole / work size | Disposition and output status |
|---|---|---|
| `wp-d112` | 5.3G / 2.3G | Released; work retained, archive verification required |
| `wp-dr113` | 5.1G / 2.1G | Released; work retained, archive verification required |
| `wp5.1` | 5.8G / 2.8G | Conditional candidate: confirm accept-side release, then archive verification |
| `wp5.2` | 5.0G / 2.0G | Released; work retained, archive verification required |
| `wp5.3` | 5.3G / 2.3G | KEEP: CP5 tally when owner's sheet returns |
| `wp5.6` | 4.5G / 1.5G | KEEP: p5b gate evidence until WP5.6 accepts |
| `wp5.6r` | 17M / under 1M (only `work/wp5.6/` inputs at measurement) | KEEP: this report's worktree until WP5.6 accepts; inventory added block, line 264 |
| `brief-dr113`, `brief-dr87`, `brief-phase5` | 17M, 14M, 15M / no work size reported | Candidate state/brief trees; owner confirms release |
| `brief-wp3.6p`, `brief-wp4.4`, `brief-wp5.2` | 14M, 13M, 17M / no work size reported | Same |
| `orch-state-g21` through `g28` | 13M, 13M, 14M, 14M, 14M, 14M, 15M, 15M / no work size reported | Candidate older state trees, owning seat confirms |
| `orch-state-g29` through `g36` | 15M, 15M, 15M, 16M, 16M, 17M, 17M, 17M / no work size reported | Candidate state trees, owning seat confirms which remain needed |
| `tmp-wp36p-red` folder | 4.0K / no work size reported | Not registered in git worktree list; inventory explicitly notes folder only |

### Named large residuals and existing archives

| Item | Recorded size / disposition | Source |
|---|---|---|
| `%LOCALAPPDATA%\Temp\pytest-of-rwsmy` | 16G at the seat; inventory also records CHARC's 15.4 GB. Preserve both reported units, no conversion asserted. Candidate on owner's word. | Inventory, pytest temp and orchestrator notes |
| `work/orch-g33/vs-orphans/` | 3.0G measured at the seat, superseding CHARC's earlier about-2-GB estimate carried in the brief; enclosing `work/orch-g33` is 3.1G. Candidate on owner's word. | Inventory added block, line 263; main work line 183; WP5.3 accept, real build |
| `work/wp5.2/W52-2/attempt-20261102T150359Z-1621/W52-2-GX011627-whole.mp4` | 158,459,032 B (about 158 MB), input stream copy still retained. Candidate on owner's word. | Inventory whole-clip copy; WP5.2 accept Windows |

[2026-10-29 prune](../proofs/prune-2026-10-29.md), MOVED section, already
archived to `D:\clearwater-archive\work\`: WP3.21 oracle, whole deep/shallow
CP2 packs (wp1.3d/wp1.3), wp1.4, wp1.4b and wp-t4. The three failed
exFAT link-containing copies (wp1.2b, wp2.2, pt-main-wp39) were subsequently
deleted by the owner, including their incomplete archive copies; manifests
and logs remain. They are not completed archives.

[2026-11-01 prune](../proofs/prune-2026-11-01.md), MOVED section, archived
to `D:\clearwater-archive\worktrees\`: WP3.6P facts of record, WP-T7 cell
records, WP4.6 V7 window and dry window, its listed shape/probe/support
folders, and loose files from those trees. Gate files were also copied
to review evidence as named there. WP-D54, WP-T7, WP3.6P and WP4.6
worktree basetemps/fixtures were deleted and those trees removed (branches
kept); the current list is not a request to repeat those completed prunes.

Decision: the owner supplies the prune word and its keep list; the
orchestrator checks evidence retention and executes the approved list.
This report supplies candidates, not deletion authority.

## Open with the owner / next

- **CP5 / V2:** owner reviews the WP5.3 pack and returns the sheet.
  The orchestrator tallies it separately; D65 requires >=80% preference
  and no obvious artifacts. CHARC records the owner's result.
- **N6 ruling:** owner chooses the proposed target or alternative;
  CHARC updates the ruled figure and spec.
- **DR-115 scope:** CHARC brings the encoder-watchdog and CPU-route
  encoder-choice question at the Phase 5 close.
- **DR-25(3), CHARC action:** reconcile the register's WP5.2 assignment
  for the >=182-frame staged smoothing run with accepted WP5.2's absent
  evidence. Disposition is CHARC's; no owner decision is asserted here.
- **WP5.5:** release preparation is commissioned after the close;
  dependency-license compatibility/notices, installation/usage and version
  tagging belong there (plan Phase 5 / N13).
- **WP5.4:** conditional on CP5 shimmer (D96); plan also names a V3 failure
  as a trigger. V3's cited synthetic result passes; no weight-map smoothing
  package is commissioned by this report.

