# WP5.2 performance and memory

Spec v0.5.7; shipped-build instruments, full clips, c3 defaults, with no
product, estimate, dependency or frozen-interface change. Instruments ran
at the orchestrator's seat in EXCLUSIVE windows; the cell read their
records read-only and wrote this report. This is measurement evidence for
CHARC and the owner's N6 decision, not final acceptance or a new N6 value.

Evidence aliases below are relative to the configured working folder's
`wp5.2/` (not this worktree's ignored scratch folder):

| Alias / window | Exact record path / read-back |
|---|---|
| R / W52-1 | `v16/W52-1/W52-1-export-bench-v16-20261102T124817Z.json`; `r[i]=R.runs[i]`, zero-based; ledger **Session 3 / Turn 6: W52-1 read-back** |
| A / W52-2 | `W52-2/attempt-20261102T150359Z-1621/`; held/free/CPU files `W52-2-r2-{held,free,cpu}.json`; ledger **Session 4 / Turn 7: W52-2 read-back** |
| D / W52-2 | `photo/W52-2-default-d9c469d756db/record.json` and adjacent `runner.json`; same turn-7 ledger section |
| P / W52-2 | `photo/W52-2-cpu-dcd7c55c3970/record.json` and adjacent `runner.json`; same turn-7 section |
| S / W52-3 | `W52-3/attempt-20261102T175410Z-1752/`; `W52-3-r2-cpu.json`, `W52-3-progress.csv`, `W52-3-compare.json`; ledger **Session 4 / Turn 8: W52-3 read-back** |
| I / W52-2 | `A/W52-2-r2-held-free.json`; independent seat-run follow-up after W52-2, read back in turn 8 |

The [cumulative ledger](../proofs/wp5.2-ledger.md) contains the exact
requests, receipt paths, rulings and raw-key maps. R's SHA256 is
`e93f060399e73bb7416cce4f045557b8c0b0cb8be053686036b2d4f4a12c0495`,
confirmed again in turn 8. Outputs/media remain uncommitted; no media or
GPS/IMU payload is included here. GB means decimal bytes/1e9; MiB means
bytes/1048576. Ratios, percentages and unit conversions are derived from
the named records; displayed rounding does not replace their raw values.

## 1. V16 full-clip rate: WP3.21 -> WP5.2

Exact WP3.21 column set, with each numeric cell the pair **WP3.21
after-optimisation -> WP5.2 W52-1**. Prior values/notes are cited from
[WP3.21 V16](wp3.21-optimisation.md#v16-the-re-measure-task-10-exclusive-windows-figures-of-record);
current values are R, identified by r[i] in every row. The supplemental
device-frames-OFF row is not in V16_PLAN and is not added. Each run is
GPU, device frames ON, Standard/8-bit, auto -> hevc_nvenc except libx265;
all eight `ok` and `memory_check.passes` values are true. The seven NVENC
rows have PID-tied encoder-load evidence; libx265 is characterisation.

| Row | s/frame | min/min (D106 25) | per frame median / p90 / max | lead + stall share | peak tree RSS MiB | peak GPU MiB (device-wide) |
|---|---|---|---|---|---|---|
| W52-1 r[0] GX011627 c3 cold 1 (baseline :232) | 0.3195 -> 0.392924 | 9.57 -> 11.775954 | 0.290 / 0.322 / 0.602 -> 0.316343 / 0.342331 / 0.429582 | 7.39 % -> 9.0789 % | 3,394 -> 3,522.703 | 3,244 -> 3,613 |
| W52-1 r[1] GX011627 c3 cold 2 (baseline :233) | 0.3264 -> 0.359285 | 9.78 -> 10.767787 | 0.297 / 0.332 / 0.624 -> 0.327670 / 0.368823 / 0.835539 | 7.39 % -> 7.9392 % | 3,417 -> 3,532.195 | 3,142 -> 3,669 |
| W52-1 r[2] GX011627 c3 cold 3 (baseline :234) | 0.3310 -> 0.363329 | 9.92 -> 10.888984 | 0.302 / 0.334 / 0.688 -> 0.330838 / 0.367174 / 0.858039 | 7.44 % -> 8.2354 % | 3,396 -> 3,556.125 | 3,130 -> 3,575 |
| W52-1 r[3] GX011627 c3 warm (a) (baseline :235) | 0.3022 -> 0.321605 | 9.06 -> 9.638515 | 0.296 / 0.319 / 0.359 -> 0.314386 / 0.342360 / 0.389250 | 0.81 % -> 0.8488 % | 2,456 -> 2,555.789 | 2,601 -> 2,984 |
| W52-1 r[4] GX011627 ancuti2018 cold (baseline :236) | 0.2917 -> 0.332299 | 8.74 -> 9.959024 | 0.255 / 0.271 / 1.212 -> 0.278721 / 0.308780 / 1.593705 | 11.66 % -> 15.5547 % | 3,396 -> 3,530.621 | 3,014 -> 3,505 |
| W52-1 r[5] GX011627 c3 libx265 cold (baseline :237) | 0.4869 -> 0.682129 | 14.59 -> 20.443414 | 0.426 / 0.552 / 3.593 -> 0.507169 / 1.162660 / 5.022489 | 2.10 % -> 1.7905 % | 4,963 -> 5,119.070 | 2,761 -> 3,068 |
| W52-1 r[6] synthetic 5.3K 8:7 c3 cold (baseline :239) | 1.2229 -> 1.345737 | 36.65 -> 40.331778 | 1.074 / 1.178 / 4.654 -> 1.115174 / 1.137576 / 1.186678 | - -> 7.4283 % | 7,753 -> 5,340.090 | 7,901 -> 7,085 |
| W52-1 r[7] GX011625 c3 cold, sustained (baseline :240) | 0.3195 -> 0.359659 | 9.58 -> 10.779005 | 0.299 / 0.337 / 4.117 -> 0.338958 / 0.372027 / 4.222788 | 5.75 % -> 5.0579 % | 3,653 -> 3,731.852 | 3,277 -> 3,638 |


Current key map: `total.{s_per_frame,min_per_min}`,
`per_frame.{median,p90,max}`, `100*analysis_share_overlapped`,
`telemetry.peak_tree_rss_bytes/1048576`,
`telemetry.peak_gpu_memory_used_mib` under each r[i]. First-frame cost
is separately recorded and excluded from the per-frame median/p90/max;
total wall includes startup/analysis/render/encode. Cold rows have empty
fresh caches; only warm r[3] starts complete. Warm priming uses the
product's own analysis state, including its pool; it is not a cold sample.

R `frames=source_frames`: GX011627 **681**, synthetic **150**, sustained
GX011625 **14,938**, all **30000/1001 fps**. No cold result was excluded;
sustained r[7] ran last. The synthetic 5.3K row is **5312x4648 (8:7)**;
no real owner recording in that mode was available. Prior WP3.21's
synthetic row is its ruled memory rerun (b), and its sustained RSS
includes unrelated browser members (c); those caveats remain in the
cited baseline and are not adjusted away here.

## 2. N6 facts for CHARC and the owner

D106 min/min is `wall_s / frames * frame_rate`, seconds spent per second
of source. Cold median uses all three R r[0:3] `total.min_per_min` values.
Baseline percentages use WP3.21's published rounded numbers, so deltas
are approximate. Every current cell below is from **W52-1 / R**.

| Quantity / R key | WP3.21 min/min | WP5.2 min/min | Approximate delta |
|---|---|---|---|
| GX011627 c3 cold median, median r[0:3] | 9.78 | **10.888984** | +11.3393% |
| GX011625 sustained, r[7] | 9.58 | **10.779005** | +12.5157% |
| GX011627 warm, r[3] | 9.06 | **9.638515** | +6.3854% |
| GX011627 ancuti2018, r[4] | 8.74 | **9.959024** | +13.9476% |
| Synthetic 5.3K best effort, r[6] | 36.65 | **40.331778** | +10.0458% |

**GUI-path margin, CITED, not re-run:** WP4.6's **v7c** window of record
measured **226.2 s** on GX011627 versus in-process **209.1-210.9 s**,
**+7.3..8.2%** ([WP4.6 export-wall table](wp4.6-export-process.md#the-export-wall-n6--d106),
window 2026-11-01 08:46:17Z-09:08:23Z). That comparison includes worker
cold analysis versus an already complete GUI cache, not a pure spawn
cost. No new GUI rate or adjusted cold-rate figure is manufactured by
applying that margin to R. The in-process figure and historical margin
are supplied together for the owner's decision.

**One sentence of fact for CHARC:** W52-1 measured full-clip 4K c3 NVENC
at **10.888984 min/min cold median** and **10.779005 min/min sustained**,
with synthetic 5.3K best effort **40.331778 min/min** and all eight
recorded memory checks passing (R r[0:3], r[7], r[6]).

The cell makes no recommendation and does not reset interim D106/N6;
CHARC proposes the figure and the owner rules.

## 3. V15 video and photo peaks

Every current figure is tied to its W52 record alias; owner rows are
**CITED** from [WP3.6P Result 2 / 5d](wp3.6p-real-photos.md#largest-owner-photo-memory-leg-result-2),
its seat-turn8 **5d-default / 5d-cpu** receipts, not re-run in W52.
All tree-RSS figures below are under **16 GB decimal**. Device peaks
are device-wide, including idle/other use, with no baseline subtracted.

| Row / window / record | Route | Tree RSS bytes (GB) | Device-wide peak | Estimate and scope | Estimate / device peak; estimate / RSS |
|---|---|---|---|---|---|
| Synthetic 5.3K 8:7 video / W52-1 R r[6] | GPU | 5,599,490,048 (5.599490) | 7,085 MiB | Job 10,330.8 MiB; admission not recorded | Job/device **1.458123x**; admission/RSS N/A |
| Synthetic approximately 48 MP PNG16 / W52-2 D | Automatic CPU | 6,635,884,544 (6.635885) | 122,683,392 B (117 MiB) | Admission 12,214,137,856 B | GPU-work ratio N/A (CPU); admission/RSS **1.840619x** |
| Same PNG16 / W52-2 P | Forced CPU | 6,168,494,080 (6.168494) | 0 B | Admission 12,214,137,856 B | GPU-work ratio N/A (CPU); admission/RSS **1.980084x** |
| Owner IMG_6690, 24.5 MP HEIC -> PNG16 / cited 5d-default | GPU | 1,926,164,480 (1.926164) | 4,108,320,768 B (4.108321 GB) | Admission 6,128,796,496 B | **1.491801x**; **3.181866x** |
| Same owner photo / cited 5d-cpu | Forced CPU | 3,138,392,064 (3.138392) | 145,752,064 B (unchanged baseline) | Admission 6,128,796,496 B | GPU-work ratio N/A (CPU); admission/RSS **1.952846x** |

Video keys are r[6] `telemetry.peak_tree_rss_bytes` and
`memory_check.{device_peak_mib,job_estimate_mib}`; its pool peak/estimate
are **3,993.8 / 6,281.4 MiB**, estimate/pool **1.572788x**. Photo keys
are D/P `rss_tree_peak_bytes`, `device_used_peak_bytes`, `estimate_bytes`.
The RAM ratios compare a graphics admission estimate to CPU/tree RSS;
they are disclosed cross-resource arithmetic, not a graphics fit bound.

R3's input is **8064x6048**, **48,771,072 pixels**, RGB16, seeded lowred,
generated through `tools/fixtures/stills.py`, not an owner photograph
(W52-2 generator receipt in ledger turn 7). Both D/P `runner_exit=0`,
`failed_checks=[]`, `ram_within_limit=true`, `device_within_limit=true`.
Device total/limit is **8,188 MiB** in D/P. The default processing route
is CPU, an expected capacity result, not a failed GPU measurement. This
package supplies a ceiling measurement without deciding the owner's
still-open supported-photo-resolution choice.

## 4. Automatic fallback and real-export comparisons

**D111 engagement witness of record, W52-2 D:** `force_cpu=false`,
`device_reason="CPU: estimate 11,649 MiB exceeds free 7,064 MiB"`,
`automatic_fallback=true`, `memory_capacity_fallback=true`; runner exit
**0**, completed PNG16, no failed checks. The adjacent runner agrees
and records the CPU warning. P instead reads **`CPU: forced`**, exit 0,
and is not an automatic witness. This is D111's estimated-not-to-fit
branch on a real photo export; video fallback under pressure is a
separate observation.

**DR-114 real export, W52-2 A:** holder request **5,861 MiB**,
`W52-2-r2-holder.jsonl` first line
`{"held_bytes":6145703936,"free_before":7411335168,"free_after":1262485504}`.
The holder was alive before and after held export, stopped by stop file,
exit **0**. Device-wide nvidia-smi (`memory.free,memory.used`, MiB):
`before.csv` **7,397 / 552**, `during.csv` **1,421 / 6,528** (inside the
**1,280-1,792 MiB** initial band), `held-end.csv` **3,059 / 4,890**,
`after.csv` **7,756 / 193**; all names carry `W52-2-r2-` under A.
`recovery.json` confirms recovery within the pre-holder-used +100 MiB
guard. The held-end reading and liveness do not prove constant residency
or constant 1.5 GiB free throughout export.

A held/free records both say **`GPU`**, `done with warnings`, exit **0**,
NVENC, with item walls **240.078227 / 242.110169 s** (batch
**240.080799 / 242.112675 s**; shell **243.764 / 243.268 s**, separate
scopes). WDDM pressure did not engage CPU selection on this export.
Independent identity record **I / W52-2** compares **30 decoded frames**:
max **0.0/255**, mean **0.0/255**, `identical=true`, `passes=true`.
Only those first 30 frames, not the complete encoded files, were compared.

**CPU/GPU real-export characterisation, W52-3 S:** the repeat's
`W52-3-r2-cpu.json` reads **`CPU: forced`**, `done with warnings`,
`video.encoder=hevc_nvenc`, exit **0**. It completed all **681** frames
(successful comparison's output-probe guard; runner JSON has no frame
counter). Item wall **6,585.155312 s** divided by 681 at **30000/1001 fps**
gives CPU-route **9.669831589 s/frame**, **289.805142514 min/min** by
D106; this is a **CPU-route RATE, not a target**. Shell real was
**109m44.814s**, not the numerator used for that rate (ledger turn 8).

S `W52-3-compare.json` compares the first **30** frames against A's free
GPU output: `comparison="post-encode free vs forced CPU"`,
`max_abs_255=85.0`, `mean_abs_255=3.3288222133809158`,
`max_abs_unit=0.3333333333333333`, `mean_abs_unit=0.013054204758356532`.
`postencode_mean_limit_255=3.5`,
`postencode_characterisation_passes=true`, `passes=true`, `skipped=false`,
`export_exits={free:0,cpu:0}`, `failed_legs=[]`, `timeout_observed=false`.
Literal AD-11 numeric limits max **0.002** / mean **0.0002** are **not met
through the encoder**: `ad11_numeric_bounds_met=false`,
`preencode_ad11_proved=false`. The allowed WP5.1 post-encode
characterisation passes; this leg does not prove pre-encode AD-11.

## 5. Estimate margins across the rows

Every W52-1 run's ratios below use r[i]
`memory_check.{job_estimate_mib,device_peak_mib,pool_estimate_mib,pool_peak_mib,idle_before_mib}`.
The first ratio is job estimate / device-wide peak; the second is pool
estimate / pool peak. These are different scopes from the base admission
estimate, which R does not carry. Idle is stated and never subtracted.

| Window / record | Job estimate / device peak MiB | Ratio | Pool estimate / pool peak MiB | Ratio | Idle MiB |
|---|---|---|---|---|---|
| W52-1 r[0] | 4,065.4 / 3,613.0 | 1.125215x | 2,173.8 / 1,510.8 | 1.438840x | 662.0 |
| W52-1 r[1] | 4,065.4 / 3,669.0 | 1.108040x | 2,173.8 / 1,566.2 | 1.387945x | 712.0 |
| W52-1 r[2] | 4,065.4 / 3,575.0 | 1.137175x | 2,173.8 / 1,470.5 | 1.478273x | 712.0 |
| W52-1 r[3] | 3,582.0 / 2,984.0 | 1.200402x | 2,173.8 / 1,342.5 | 1.619218x | 736.0 |
| W52-1 r[4] | 4,065.4 / 3,505.0 | 1.159886x | 2,173.8 / 1,392.2 | 1.561414x | 712.0 |
| W52-1 r[5] | 3,412.7 / 3,068.0 | 1.112353x | 2,173.8 / 1,414.5 | 1.536797x | 724.0 |
| W52-1 r[6] | 10,330.8 / 7,085.0 | 1.458123x | 6,281.4 / 3,993.8 | 1.572788x | 712.0 |
| W52-1 r[7] | 4,065.4 / 3,638.0 | 1.117482x | 2,173.8 / 1,523.3 | 1.427033x | 716.0 |

Every recorded device/pool check passes and these matching-scope ratios
are below 2x. At 5.3K the pool estimate is the selection bound; the job
total can exceed physical capacity and is not the admission operand.
The historical 4,427 MiB example embedded in `memory_check.note` is not
the current peak and is not substituted for r[6].

Photo estimate ratios are in section 3, all tied to D/P or cited owner
5d. Requested raw D admission/device arithmetic is **99.558201x**,
but CPU did the processing, so it is **not a GPU-work estimate margin**;
P has a zero denominator and no finite admission/device ratio. Owner
GPU admission/device is **1.491801x**; owner admission/RSS **3.181866x**
is a different resource/scope. No applicable measured GPU-work ratio
exceeds 2x, and these measurements do not establish an owner mode falsely
falling back. They do not measure what 48 MP GPU residency would have
been if admitted. R2/S headless records carry no memory estimate/peak
fields, so no margin is invented for those exports. The admission/job/
pool estimates are **conservative by design**; none is tuned here.

## 6. Limits and host conditions

**Sampling.** R / W52-1 nominal RSS/GPU cadence is **0.25 / 1.0 s**;
observed maximum gaps across the eight rows are **0.450 / 1.184 s**,
with `telemetry.errors=[]` throughout. Synthetic r[6] has **816 RSS /
204 GPU samples**, max gaps **0.274 / 1.026 s**. D/P / W52-2 nominal
waits are **0.05 / 0.2 s**, `wait-after-sample`; actual RSS max gaps
are **0.094 s** both, device max gaps **1.406 / 1.515 s**, errors empty
(ledger turns 6/7, actual `gaps_s` / `sampling_cadence_s` keys). Peaks
are sampled, not instantaneous maxima. The inherited photo sampler's
approved attach/background peak-update race can lose a startup peak;
no loss is established here ([WP3.6P Limits](wp3.6p-real-photos.md#limits-and-debt-disposition-for-charc)).
S / W52-3 progress is nominally **60 s**, **110 rows**, **107** with
encoder counters; missing fields remain empty (turn-8 CSV read-back).

**F13/F14 (Reviewer A, disclosed, unchanged semantics).** When a device
read is unavailable, `device_within_limit=None`, not false/true; the
measurement failure and exit status are unchanged. D/P have valid
reads, not that condition. `estimate_fits_free_before` uses the parent's
nvidia-smi reading; it is not the runner's later per-process admission
operand or a D111 witness. D/P pre-run free is **7,948 MiB**, while D's
actual route reason reads **7,064 MiB**; only that actual reason proves
engagement (turn-7 records and ledger's F13/F14 Limits draft).

**WDDM / DR-114.** The ruled seat probe recorded test-process free
**7,407,142,400 B** unchanged during a hold; a second process read
**7,411,335,168 B** before/during/after. The holder itself reported
**2,147,483,648 B** held, free **7,411,335,168 -> 5,261,754,368 B**,
while device-wide used was **2,826 MiB during / 663 MiB after**.
These are earlier seat observations accepted by CHARC eade11c9,
not W52-2 measurements (ledger **Report Limits draft (seat evidence,
DR-114)**). A's actual held export extends the finding: it remained GPU.
Cross-process physical pressure is not guaranteed to alter the product's
free-memory operand; DR-114 is not closed by R3's distinct witness.

**Shared laptop and window readings.** Values below are the orchestrator's
opening/closing snapshots in ledger turns 6/7/8, not continuous traces.
The conditions do not prove an otherwise idle host or a causal code
regression. No tests/reviewer/heavy package jobs were authorised in these
EXCLUSIVE windows; the listed host applications and sampled activity
remain conditions of the measurements.

| Window / UTC interval | Open -> close free disk GB; available RAM GB | Open -> close GPU SM/memory MHz; C; free/used MiB | Strays / other readings |
|---|---|---|---|
| W52-1, 12:48:16-14:55:15Z, 2026-11-02 | 84 -> 84; 12.7 -> 12.7 | 210/405 -> 210/405; 59 -> 70; 7404/545 -> 7413/536 | Brave, Battle.net, PianoMarvel, OktaVerify, QNAPRaidMgr, two Claude sessions; open CPU about 9% |
| W52-2, 15:03:59-17:42:42Z (close reading 17:43Z) | 84 -> 83; 12.4 -> 13.9 | 210/405 -> 1980/8001; 58 -> 63; 7397/552 -> 7948/0 | Brave, Battle.net, PianoMarvel, OktaVerify, Claude sessions; open CPU about 12% |
| W52-3, 17:54:10-19:44:14Z (close reading 19:45Z) | 79 -> 63; 12.5 -> 14.5 | 1980/8001 -> 1800/7001; 60 -> 60; 7948/0 -> 7948/0 | Same strays as W52-2; open CPU 28%, GPU 0% utilisation |

W52-3's approximately **16 GB disk drop** is an unexplained host event:
the seat reports all `work/wp5.2` about **1.3 GB**, with the consumption
elsewhere, not this package's paths. No outside-grant investigation was
performed or cause asserted. The seat saw no surviving export/ffmpeg at
close. Window preflights passed their floors (W52-1 25 GB; W52-2/3
30 GB; R3 recheck 25 GB), not a guarantee about other host disk activity.

**Rate comparison conditions.** R's whole-run non-own strays include
WmiPrvSE on every row, System on r[1,2,4,5,6,7], and a new
MoUsoCoreWorker on libx265 r[5]; endpoint samples add svchost on synthetic
r[6]. W52-1 sampled SM spans **210-2,475 MHz**, memory **405-8,001 MHz**,
and temperature reaches **93 C** on sustained r[7] (R `telemetry.gpu`,
ledger turn 6). WP3.21 had its own System/browser caveats, not matching
controlled conditions. Main 4K aggregates in section 2 are roughly
**6-14% slower** than WP3.21; that is not a bound on every sample:
cold r[0] is about **23.05%** slower than its prior row, and libx265
characterisation about **40.12%** slower. Samples/strays/temperatures are
recorded; their individual wall contribution and a shipped-code cause
are not isolated. No load/temperature-controlled A/B was run.

**DR-115, intermittent hang.** In W52-2 A, CPU processing with NVENC
stopped progressing around **17:02:57Z**, about **670/681** frames at
roughly **9.9 s/frame** by the seat's observations. At **17:38:10Z** the
seat ended only its encoder; headless then failed, exit **1**, shell
**146m10.234s**, and removed the partial. The granted hang snapshot
`work/orch-g35/w52-2-cpu-hang.txt` records encoder pid **42972**, main
thread Running at **2109.9 CPU s**, partial **82,177,867 B** last
written 17:02:57Z (ledger turn 7). The repeated no-I/O/spinning diagnosis
is the seat's observation; the saved text itself is one snapshot.

W52-3 S completed on the same encoder, so this single retry did not
reproduce the hang. Its CSV encoder pid **1436** increased from
**0.734375** to **41.796875 process CPU s**, and reads from
**85,812,422** to **16,828,871,544 B** over populated samples; these are
process counters, distinct from the hung thread counter. No cause is
inferred from the difference. There is no product encoder-stall detector;
the shell timeout was instrumentation. `--force-cpu` moves **processing,
not the encoder**. The completed CPU-route rate is the section-4
**289.805143 min/min**, not an N6 target; DR-115 remains an observed
intermittent defect and D85 cleanup does not establish stall detection.

**Input/path and comparison coverage.** The 5.3K video and 48 MP PNG16
are synthetic; owner photo/GUI results are cited, not re-run. No footage
folder content was opened by the reporting cell. Held/free equality and
CPU/GPU characterisation cover first **30** decoded frames, not every
output frame or encoded-byte identity. Successful post-encode
characterisation does not remove the recorded strict AD-11 numeric
misses or prove pre-encode equivalence. Admission conservatism and real
GPU residency at an unadmitted photo size are not tuned or established.

## 7. DR-70 analysis-share re-read

Every row below is **W52-1 / R**, retaining both named share keys.
Legacy `analysis_share` is lead/wall, not whole-analysis runtime;
`analysis_share_overlapped=(lead_s+record_wait_s)/wall_s` is the comparable
lead-plus-stall share. It is not the percentage of GPU/CPU compute spent
inside analysis.

| Record | analysis_share % | lead_s + record_wait_s | analysis_share_overlapped % | analysis_end_s / wall_s |
|---|---|---|---|---|
| W52-1 r[0] | 9.0065 | 24.099828 + 0.193506 | 9.0789 | 210.217561 / 267.581480 |
| W52-1 r[1] | 2.6824 | 6.563171 + 12.861951 | 7.9392 | 223.115413 / 244.673201 |
| W52-1 r[2] | 2.7892 | 6.901276 + 13.475433 | 8.2354 | 225.701699 / 247.427106 |
| W52-1 r[3] | 0.7965 | 1.744497 + 0.114497 | 0.8488 | 122.733931 / 219.013079 |
| W52-1 r[4] | 6.5699 | 14.867507 + 20.332149 | 15.5547 | 199.947185 / 226.295916 |
| W52-1 r[5] | 1.4262 | 6.625220 + 1.692403 | 1.7905 | 268.882034 / 464.529558 |
| W52-1 r[6] | 7.4200 | 14.977981 + 0.016778 | 7.4283 | 42.318292 / 201.860550 |
| W52-1 r[7] | 0.1198 | 6.434622 + 265.305190 | 5.0579 | 5284.375990 / 5372.593214 |

Sustained r[7] analysis returns at **5,284.375990 / 5,372.593214 s**,
derived **98.3580%** of export wall; lead **6.434622 s**, record wait
**265.305190 s**, overlap share **5.0579%** versus cited WP3.21 **5.75%**.
WP3.21 analysis returned at **4,690.6 s**, frame **14,655 / 14,938**
([WP3.21 STREAM_STEP discussion](wp3.21-optimisation.md#v16-the-re-measure-task-10-exclusive-windows-figures-of-record)).
The analysis return is again near export end, consistent with the
previous overlap/analysis-bound observation. These keys do not isolate
the cause of the rate difference or apportion all compute time; DR-70's
analysis-pass lever remains a follow-on tuning question, untouched here.

## 8. Ledger, review and gate

[WP5.2 cumulative ledger](../proofs/wp5.2-ledger.md): round-0 map and
rulings; Reviewer A rounds 1/2 and convergence; section-5 exact requests;
session 3 turn 6 (W52-1), session 4 turn 7 (W52-2), session 4 turn 8
(W52-3 and report), with raw-key maps, receipt paths and verification.
DR-72's bench stop is implemented/instrumented; registry closure, the
N6 proposal/owner ruling and acceptance transfer remain with CHARC and
the orchestrator. This report does not close debt by itself.

Reviewer B: PENDING (orchestrator seat)

Gate: PENDING (orchestrator seat)
