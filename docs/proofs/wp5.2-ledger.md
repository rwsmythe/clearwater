# WP5.2 cumulative ledger

Package: WP5.2, performance and memory runs. Dispatch base and observed HEAD:
`70c3a5db26a9711c519d8ed1152d84c7f66e5b96`. Branch/worktree: `wp5.2` /
`C:/Users/rwsmy/clearwater/.worktrees/wp5.2`. This ledger records mapping and
proposed seat commands, not measured performance or acceptance. No N6 proposal
is made by the cell. The dispatcher owns commits, reviews and EXCLUSIVE windows.

## Round 0

Status: **STOP to CHARC through the dispatcher; T1 mapped, YIELD before T2.**
Depth: **dispatcher to fill from transcript** (evaluate around 200K; stop near
250K at a step boundary). No cell estimate substituted.

### Findings requiring a ruling

Recommended dispositions appear first. These are dispatch-premise findings,
not Reviewer A findings; no review round has been counted.

| ID / severity | Recommended disposition | Confirmed mechanism and evidence |
|---|---|---|
| R0-F1 [MAJOR, IN, NEW] | Correct R1 to `v16 --device-frames --subdir wp5.2/v16/W52-1`, after F2 is resolved; no additional bench edit. | `tools/export_bench.py:805` defines `--subdir`, not `--out`; `:798` makes device frames opt-in. The dispatched R1 command exits 2 during argument parsing: `unrecognized arguments: --out work/wp5.2/v16`. Executed with `--dry-run`, which still parses before config/lookup; log `work/wp5.2/round0/r1-parser.log`. Omitting `--device-frames` measures the host conversion path (`:603`), whereas the comparable WP3.21 rows used it (`docs/reports/wp3.21-optimisation.md:222`). |
| R0-F2 [MAJOR, IN, NEW] | Dispatcher supplies/corrects the local configuration so its working path is this worktree's `work`; cell leaves the protected local file untouched. | `clearwater.local.toml:17` currently names `C:/Users/rwsmy/clearwater/work`, not this worktree's `work`. `tools/export_bench.py:839` joins the configured working path and subdir; `tools/photo_verify.py:289` likewise joins its fixed root. The current configuration would send these instruments into the explicitly forbidden MAIN working folder. Pure TOML/string-path comparison confirms the mismatch without opening either configured folder (`work/wp5.2/round0/map-probe.log`). |
| R0-F3 [MAJOR, IN, NEW] | Keep Q2's synthetic 48 MP goal, but commission a seat-only measurement adapter using the existing sampler/runner APIs, or explicitly grant an instrument extension. CHARC must select the mechanism; no edit to `photo_verify.py` is currently owned. | The dispatched R3 CLI has no synthetic-input path: `photo_verify.py:1811` requires a class map; `:317` requires the exact seven owner classes/counts; `:331` permits HEIC/JPEG names only; `_selection` at `:1837` resolves inputs under configured `Phone`; `:1926` checks actual owner class. Outputs are hard-rooted at `<working>/wp3.6p` (`:289`), contrary to this package's `work/wp5.2` lock. An AST-extracted, unchanged `_selection` rejects `synthetic-48mp.png` with `ValueError: unlisted input` before accessing config or any file (map-probe log). The cited WP3.6P report/brief do not supply a 48 MP generator recipe; the reusable PNG16 mechanism actually found is WP2.3's `tools/fixtures/stills.py:125`, `:162`, `:197`. |
| R0-F4 [MAJOR, IN, NEW] | Use the entire GX011627 (22.7227 s, 681 frames), stream-copied into this worktree, for R2; alternatively name a longer source. This disputes Q3's literal 30 s source premise. | Committed `docs/reports/wp3.14-export-batch.md:221` records 681 frames, `:264` records 22.72 s / 29.970 fps; WP3.21 independently records all 681 exported frames (`docs/reports/wp3.21-optimisation.md:210`). `681 * 1001 / 30000 = 22.7227 s`; a 30 s cut cannot be made from it without duplication or concatenation, neither authorised. No footage opened to establish this. The brief's approximately 5,900-frame premise is inconsistent with both reports. |
| R0-F5 [MINOR, IN, NEW] | Budget R1 at about 108-115 min, rather than 70 min; reserve the sustained row last. | The unchanged plan has eight runs in six legs. Prior frame counts and s/frame imply 105.957 min of timed export alone, including 79.545 min for GX011625. Warm priming, condition snapshots, joins, synthetic generation and host spread add time. Arithmetic is in map-probe log; these are planning extrapolations, not new timing measurements. |

F1/F2/F3/F4 prevent an executable, compliant T4 plan as dispatched. No workaround
has been implemented, no question is treated as answered, and no window is open.
The rest of this round supplies the requested map/design for that ruling.

### 1. Instrument and evidence map (anchors on the dispatch base)

Binding scope: plan `docs/clearwater-implementation-plan.md:73` (paths), `:80`
(exclusive/full clips), `:85` (ownership), `:89` (done, including no assumptions
at `:100`), `:362` (WP5.2). Spec `docs/underwater-correction-spec.md:148` D110,
`:149` D111, `:454` N6, `:496` V15, `:497` V16. Read dispatch recipe in full,
APPLICATION.md, CLAUDE.md, model-prompting standard and the review/gate fill.
Explicit dispatched-cell ordering governs this turn; no ambient skill review
or delegated agent replaces the dispatcher-run Claude reviews.

**Bench surface.** `tools/export_bench.py:1` describes the in-process engine,
`:15` distinguishes analysis lead from overlapped analysis, `:28` the two memory
instruments, `:36` lookup/retention, `:51` existing exit statuses. Today: 0 all
jobs OK; 1 job/measurement exception or `ok == false`; 2 parser/config/lookup/
disk refusal. There is no memory-breach exit yet. `main` at `:784` consumes the
dict returned by `run_once` at `:870`; appends and persists it at `:885-886`, then
checks only `ok` at `:888`. This is an in-memory record-return seam, not a JSON
input CLI. `_write` at `:757` writes the accumulated record after each run.

`Leg` defaults (`:133-138`): cold, c3, auto, standard. Exact `V16_PLAN` at
`:141-148` follows. Expected walls are extrapolated from WP3.21 rates and the
committed counts, not promises or measured WP5.2 figures. Auto must resolve to
`hevc_nvenc`, proved in each record; standard/8-bit follows the source.

| Leg / source anchor | Clip | Runs | Method | Encoder | Quality | Cache | Expected wall |
|---|---|---|---|---|---|---|---|
| 1 / `export_bench.py:142` | GX011627, 681 frames | 3 | c3 | auto -> NVENC | standard | cold, separate empty cache/run | 217.58 / 222.28 / 225.41 s; about 11.1 min total |
| 2 / `:143` | GX011627 | 1 | c3 | auto -> NVENC | standard | warm | 205.80 s timed, plus untimed whole-analysis prime (`:606`, `:446`) |
| 3 / `:144` | GX011627 | 1 | ancuti2018 | auto -> NVENC | standard | cold | 198.65 s |
| 4 / `:145` | GX011627 | 1 | c3 | libx265 | standard | cold | 331.58 s; characterisation, not N6 target |
| 5 / `:146` | synthetic-5k3, 5312x4648 / 150 frames | 1 | c3 | auto -> NVENC | standard | cold | 183.44 s, plus first-use generation; allow about 5 min |
| 6 / `:147` | GX011625, 14,938 frames | 1 | c3 | auto -> NVENC | standard | cold | 4,772.69 s / 79.54 min, LAST |

Synthetic dimensions/duration/generator: `export_bench.py:103-110`, `:157-190`.
No device-frames-OFF leg is in V16_PLAN; WP3.21's supplemental OFF row must be
cited as such, not silently added to this package's runs.

**Bench record keys for T5.** Top level `plan`, `pid`, `device_frames`, `runs`
(`:858-863`), optional `failed` (`:880`, `:889`). Run identity/settings:
`leg.{clip,runs,cache,method,encoder,quality}`, `clip`, `force_cpu` (`:598`),
`device_frames`, `device_backend`, optional `prime_s`, `cache_complete_at_start`
(`:604-609`). Result/rate: `ok`, `failure`, `warnings`, `device`, resolved
`encoder`, `bit_depth`, `size` in H/W order, `frame_rate`, `source_frames`,
`frames`, `wall_s`, `total.{s_per_frame,min_per_min}`, `d106_min_per_min`,
`meets_d106` (`:652-667`; rate helper `video_io_bench.py:496`). Phase/spread:
`phases_s`, `analysis_share` (lead-only legacy value), `lead_s`, `analysis_end_s`,
`record_reads`, `record_wait_s`, `record_wait_max_s`,
`analysis_share_overlapped` (`export_bench.py:265-287`, `:668-670`), `stages`,
`first_frame_s`, `per_frame.{median,p90,max}`, `per_frame_s`, `analysis_reports`,
`strays`, `output_bytes`, `source_bytes` (`:671-680`). NVENC evidence:
`nvenc_proof`, `sink_report` (`:683-701`). Keep `before`, `after`, including
`utc`, GPU clocks/temperature/memory, CPU and strays (`:610`, `:702`;
`video_io_bench.py:324-346`).

`telemetry` is supplied by `Telemetry` (`video_io_bench.py:349-458`): nominal
`periods_s` (bench 0.25 s RSS / 1.0 s GPU, `export_bench.py:802-803`), actual
`gaps_s`, `peak_tree_rss_bytes`, `peak_tree_rss_members`, `peak_tree_rss_at_s`,
`rss_samples`, `rss`, `peak_gpu_memory_used_mib`, `gpu`, `errors`. RSS is a
sampled simultaneous process-tree sum; GPU is device-wide, not per process.
Independent sampler threads avoid a slow GPU query delaying RSS (`:372-378`),
but observed gaps/errors must still accompany the peaks. Tool pool peak uses
`_PoolPeak` at `export_bench.py:290`, normally 0.1 s sampling.

`memory_check` at `export_bench.py:339-389`, attached at `:703`: `applies`,
`decoders`, `nvenc`, `device_peak_mib`, `idle_before_mib`, `job_estimate_mib`,
`device_ok`, `pool_peak_mib`, `pool_estimate_mib`, `pool_ok`, `passes`, `note`.
Off-GPU/no-pool/probe: only `applies: false`, with no `passes`; do not call that
a breach. Both checks must pass when applicable. Idle is stated, not subtracted.
Warm uses one decoder, cold two. The 5.3K note (`:330`) names the pool check as
binding there; the device-wide check is still recorded. N4 RAM and physical
card capacity remain additional report checks, not synonymous with `passes`.

**Backend choice/estimates.** `src/clearwater/core/memory.py:45-66` computes
`ceil((25 + 40/3 + 11.75) * 1.25 * 4 * H * W) + 1 MiB` for both methods.
Base estimate: 4K 2,078,104,577 B / 1,981.835 MiB; synthetic 5.3K
6,183,880,150 B / 5,897.408 MiB; 8064x6048 12,214,137,857 B / 11,648.310 MiB.
`backend.py:777-795` adds the FFT bound for the backend pool estimate;
`memory.py:136-174` adds context and NVDEC/NVENC sessions for the separate job
estimate. These three estimates must not share an unlabeled ratio column.

`backend.py:797-806` reads CUDA driver free plus this process's pool-free bytes;
the holder's live allocation in ANOTHER process is unavailable to that pool.
`select_backend` at `:1001-1043` uses the BASE estimate, checks force CPU first,
then GPU probe, then this free figure on every call. Strict `estimate < free`
selects GPU; equality also falls back. Reasons are exactly `GPU` or
`CPU: estimate {ceil_MiB:,} MiB exceeds free {floor_MiB:,} MiB` for capacity;
`CPU: forced` is not a capacity witness. No selection formula is tuned here.

**Headless runner.** `tools/headless_export.py:17-38` documents CLI and refusals;
`:1194` output folder must exist, `:1226` record flag, `:1228` cache flag;
`:1384-1385` requires a pre-existing cache directory for video. `--record` must
be new JSON with existing parent (`:1300-1306`), written exclusively at
`:1413-1423`. Device reason is `items[0].device` (`:1054`), with item state,
outputs, warnings, failure and elapsed time (`:1045-1056`), batch `elapsed_s`,
counts, settings and defaults provenance (`:1062-1073`). Actual device-frame /
encoder/decode-pass evidence is `items[0].video` (`:210-212`, `:299-305`, `:1078`).
Separate empty cache directories and separate output directories are required
for the paired fallback/free-card runs. CLI has no `--keep`: it retains outputs.

**Photo memory.** 5d commands of record: `docs/proofs/wp3.6p-ledger.md:1928-1929`
and receipts `:2371-2372`: `photo_verify.py memory --class-map ... --name ...
--file IMG_6690.HEIC --bit-depth 16 --exclusive`, then `--force-cpu` in a fresh
run. `photo_verify.py:1315-1377` launches a fresh non-neutral runner; memory
measurement/record code is `:1391-1515`. Relevant keys: `stored_size`,
`method`, `force_cpu`, `forced_cpu`, `exclusive`, `estimate_bytes`,
`device_free_before_bytes`, `device_total_bytes`, pre-run fit/exceeds flags,
`rss_scope`, `ram_limit_bytes`, `device_limit_bytes`, `measured_at_utc`, sampler
peaks/counts/gaps/errors, `runner_exit`, `device_reason`, `read_ok`,
`automatic_fallback`, `memory_capacity_fallback`, `failed_checks`. Source
`device_free_before_bytes` is a separately sampled nvidia-smi reading before
runner CUDA context creation, not the backend's later free-memory operand.

**Cited reports.** WP3.21 table is `docs/reports/wp3.21-optimisation.md:230-240`:
Row; s/frame; min/min (D106 25); per frame median/p90/max; lead + stall share;
peak tree RSS MiB; peak GPU MiB (device-wide). Preserve that set in T5 and label
WP3.14 -> WP3.21 -> WP5.2 comparisons. Notes (a) `:250`: warm includes primed
product pool state, no proxy FFT plans; (b) `:253`: 5.3K re-run is of record,
frame-16 max during overlap, System stray retained as spread; (c) `:257`:
sustained RSS includes five Edge members not started by job, peak as observed.
Memory attribution/table: `:323-342`. DR-70 share re-read compares
`analysis_share_overlapped`, `analysis_end_s`, wait times and frames: previous
sustained analysis returned at 4,690.6 s / frame 14,655 of 14,938 (`:274-278`),
not simply the small lead fraction.

WP3.6P 5d table: `docs/reports/wp3.6p-real-photos.md:231-297`. Owner 24,470,208
pixels, c3 defaults/PNG16; GPU estimate 6,128,796,496 B, tree RSS 1,926,164,480 B,
device peak 4,108,320,768 B; forced CPU tree RSS 3,138,392,064 B. GPU estimate /
device peak 1.491801; CPU graphics ratio is inapplicable, not a tiny useful peak.
Run moments and record receipts are cited above. Sampling/startup-race and
free-before limitations are `:272-290`, `:330-340`.

WP4.6 GUI margin: `docs/reports/wp4.6-export-process.md:62-72` window
2026-11-01 08:46:17Z-09:08:23Z, `:78` 226.2 s export, `:92-104` +7.3..8.2 %
versus 209.1..210.9 s. This is cited, not re-run. Margin includes worker cold
analysis versus GUI-cache complete analysis in the comparison; do not describe
it as isolated IPC cost or apply it as a newly measured cold-path multiplier.

### 2. Holder design (T3; not built this turn)

CLI `--mib`, `--stop-file`, `--timeout-s`. Validate finite positive sizes/time
and usable stop-file spelling before allocating; initialise the process's CUDA
context, select the same default card as the backend, read free-before, request
one live CuPy byte allocation. MiB requests are integer byte counts; CuPy pool
rounding is handled by reporting the actual allocation block size as held_bytes,
rather than claiming the nominal request is the card's observable consumption.
Use the allocator's rounded block size; do not guess a WDDM reservation quantum.
The 256 MiB request is already aligned to 512 B and larger power-of-two granularities.
Exact driver consumption is observed through free figures, not asserted from
alignment. Touch the buffer and synchronise before announcing readiness.

Print ONE flushed JSON line while holding: `held_bytes` = actual live allocation,
`free_before` = driver free just before allocation (context already established),
`free_after` = driver free after allocation/touch/sync. Thus free_after means
after acquiring the hold, not after releasing it. Loop with monotonic deadline
and a short wait (about 50 ms), stop on stop-file existence or timeout. A
`finally` drops the allocation and frees cached pool blocks; normal stop/timeout
returns 0. Interrupt/error unwinds finally; process teardown releases its CUDA
context even if externally terminated. No code can guarantee Python finally on
an uncatchable process kill. The holder only checks the supplied stop path;
it does not create/delete a stop file, open footage or discover repository paths.

GPU test design: create/prime the backend in the PARENT test process, read
`free_device_bytes()` immediately before subprocess start; use `sys.executable`
to start holder at 256 MiB with stdout/stderr and stop file under `tmp_path`.
Poll its flushed JSON from a file with a startup sanity timeout; fail on early
exit, bad JSON or inconsistent held_bytes. While ready and alive, parent free
must have fallen by at least 256 MiB. Touch stop file, measure a monotonic 2 s
deadline encompassing child exit AND parent free-memory recovery; require exit
0 and recovery to the pre-hold figure, with any context/load deviation reported
as a failing observation, not hidden by a large tolerance. Finally stop/reap the
child even on assertion failure. `pytest.mark.gpu` places it in the serial leg.
No GPU test/allocation occurred this turn. The real holder witness belongs at
the dispatcher seat; if this exact release bound proves unstable, report it.

### 3. Breach test design (T2; not built this turn)

Use `bench.main` and monkeypatch the EXISTING `run_once` record-return seam
(`export_bench.py:870`), not a new record loader or a real job. In a per-test
`tmp_path`, replace `load_local_config` with a local config stub,
`find_footage_file` with local placeholder paths, `check_disk` with a no-op;
replace `row_line` with a deterministic summary to isolate stop/record control.
Supply a small controlled tuple of `Leg`s, including a repeated-run first leg
and a later leg so both nested loops are exercised without clips or GPU.

Return `ok: true`, `failure: null`, and `memory_check: {applies: true,
passes: false}` at a named call. Assert exit 3, exact call count/prefix (no next
run or next leg), read the actual written JSON under `tmp_path` and prove all
prior records PLUS the breached record survive. Positive control returns
`passes: true` and requires every planned call/record and exit 0. Cover a breach
at the first record and after a passing record. An inapplicable check without
`passes` must continue; preserve existing job-failure exit 1. RED must fail on
the exit/stop assertion on this base; passing-record control must pass. No test
is run this turn. Planned edit: after preserving the run, stop on an explicitly
false `memory_check.passes`, with exit 3 documented alongside 0/1/2 at `:51-54`.
Only this DR-72 change is owned; no pipeline or schema redesign.

### 4. Q1-Q4 dispositions

| Question | Round-0 disposition |
|---|---|
| Q1 GUI path | TAKE recommended citation of WP4.6, with cache-state caveat above. |
| Q2 largest supported photo | TAKE the recommended 8064x6048 synthetic/owner-photo citation coverage; STOP on the unavailable CLI/recipe mechanism (F3), without dropping the leg. 8064x6048 is 48,771,072 pixels, approximately 48.8 MP. Base admission estimate is about 12.21 GB, so default is expected to fall back on this 8 GB card; that is a result, not a failed GPU attempt. |
| Q3 fallback clip | DISPUTE literal first-30-s GX011627 premise (F4). Recommended revised answer: full 22.7227-s GX011627, not the 90-frame session trim; requires CHARC ruling. No invented/duplicated frames. |
| Q4 libx265 | TAKE recommended existing plan leg; encoder fallback characterisation, not N6 target. |

### 5. RUN REQUESTS (not executed; blocked changes clearly identified)

All commands below are for the ORCHESTRATOR seat from this worktree root in
Git Bash, with `unset PYTEST_ADDOPTS`. Do not run them until rulings resolve the
STOPs and T2/T3 tool review is green. No EXCLUSIVE window is being requested
open by this turn. Each future window: `df -h /c`, stop below 25 GB free, RAM /
GPU conditions and strays before/after, no other heavy job, no WP-DR113 activity,
open/close to CHARC. Conditions logs and names include W52-N. Only R2 export
outputs need retention through the comparison. R1 omits --keep. Headless/photo
runner outputs are retained without a --keep option; their cleanup must follow
the dispatcher's explicit keep/delete grant, not an invented cleanup policy.

**R1 / W52-1 (after F1/F2 ruling).** Proposed corrected command:

```bash
unset PYTEST_ADDOPTS
mkdir -p work/wp5.2/v16/W52-1
uv run python tools/export_bench.py v16 --device-frames --subdir wp5.2/v16/W52-1 > work/wp5.2/v16/W52-1/W52-1-v16.log 2>&1
```

This writes below `<configured-working>/wp5.2/v16/W52-1`, which must first equal
this worktree's `work/wp5.2/v16/W52-1` (F2). Do not substitute `--subdir
work/wp5.2/...` (that would add another work component). About 108-115 min;
eight run records, final sustained row last. No --keep; bench deletes per-run
cache/output directories, retains JSON and synthetic input. Read back all keys
in section 1, confirm eight runs and resolved encoders/cache states, then read
the cold median, sustained ratio, 5.3K peaks, every memory verdict and both
estimate ratios. The benchmark auto-names its JSON without a window token
(`export_bench.py:857`); seat can prefix the completed record filename with
`W52-1-` within this same directory, byte-preserving, after capturing its printed
RECORD path. This needs no bench edit. Keep failed prefixes/records as evidence.

**R2 preparation / W52-2 (F4 ruling needed).** There is no valid command that
creates a 30-second stream-copied GX011627 from the recorded 22.7227-second
source. The following exact proposed seat command caps at 30 s but copies the
whole available clip; it MUST be described as 22.7227 s if this is ruled in.
It follows `tests/conftest.py:786-821`'s mapping/metadata form, excluding tmcd
from explicit data mappings and regenerating timecode as that helper does.

```bash
mkdir -p work/wp5.2/W52-2
uv run python - > work/wp5.2/W52-2/W52-2-cut.log 2>&1 <<'PY'
import subprocess, sys
from pathlib import Path
sys.path.insert(0, 'tools')
from local_config import load_local_config, find_footage_file
from clearwater.io.video import find_tool, probe
cfg = load_local_config()
root = Path.cwd() / 'work/wp5.2/W52-2'
assert root.is_relative_to(cfg.working_path.resolve())
source = find_footage_file('GX011627', cfg.footage_path)
info = probe(source)
maps = ['-map', '0:v:0']
for stream in info.audio:
    maps += ['-map', f'0:{stream.index}']
for stream in info.data:
    if stream.codec_tag != 'tmcd':
        maps += ['-map', f'0:{stream.index}']
output = root / 'W52-2-GX011627-cap30.mp4'
command = [str(find_tool('ffmpeg')), '-nostdin', '-hide_banner', '-v', 'error',
           '-n', '-i', str(source), *maps, '-c', 'copy', '-map_metadata', '0',
           '-map_metadata:s:v:0', '0:s:v:0', '-write_tmcd', '1',
           '-video_track_timescale', str(info.video.time_base.denominator),
           '-t', '30', '-movflags', 'use_metadata_tags', '-f', 'mp4', str(output)]
subprocess.run(command, check=True)
copied = probe(output).video
print('CUT', output.name, 'frames', copied.nb_frames, 'fps', str(copied.frame_rate))
PY
```

Preparation expected seconds, not a benchmark. The session trim's automatic
keyframe choice is at >=3 seconds (`tests/conftest.py:782`); that helper cannot
be presented unchanged as a 30 s helper. Seat should record actual copied frame
count/duration and packet identity if the revised full-clip choice is approved.

**R2 (a).** Under the future W52-2 window, get free MiB AFTER card initialisation,
choose a positive integer HOLD_MIB = floor(free_before/2**20) - 1500, record
the input reading, and ensure the stop file is fresh/absent. Proposed invocation
(HOLD_MIB is a measured seat value, never a cell guess):

```bash
uv run python tools/device_hold.py --mib "$HOLD_MIB" --stop-file work/wp5.2/W52-2/W52-2-hold.stop --timeout-s 3600 > work/wp5.2/W52-2/W52-2-holder.jsonl 2> work/wp5.2/W52-2/W52-2-holder.stderr &
HOLDER_PID=$!
```

Wait for flushed readiness JSON and verify actual free-after below the base
4K estimate; context overhead means nominal subtraction is not proof. Keep
holder alive through (b), with cleanup trap in the seat driver so an export
failure cannot strand it. Holder can also expire; record reason/exit.

**R2 (b)-(d).** Corrected parser-complete commands, pending F2/F4. Separate
outputs and caches avoid suffix collisions and warm-cache comparisons; no
--force-cpu anywhere in this witness. Expected CPU wall is uncertain: brief's
20 min was based on 900 frames that this clip does not have. Reserve about
20 min provisionally, validate actual rate; GPU about 3.6-3.8 min at prior rate.

```bash
mkdir -p work/wp5.2/W52-2/fallback-cpu/out work/wp5.2/W52-2/fallback-cpu/cache work/wp5.2/W52-2/fallback-gpu/out work/wp5.2/W52-2/fallback-gpu/cache
uv run python tools/headless_export.py work/wp5.2/W52-2/W52-2-GX011627-cap30.mp4 --out work/wp5.2/W52-2/fallback-cpu/out --cache-dir work/wp5.2/W52-2/fallback-cpu/cache --method c3 --encoder auto --quality standard --record work/wp5.2/W52-2/W52-2-fallback-cpu.json > work/wp5.2/W52-2/W52-2-fallback-cpu.log 2>&1
touch work/wp5.2/W52-2/W52-2-hold.stop
wait "$HOLDER_PID"
uv run python tools/headless_export.py work/wp5.2/W52-2/W52-2-GX011627-cap30.mp4 --out work/wp5.2/W52-2/fallback-gpu/out --cache-dir work/wp5.2/W52-2/fallback-gpu/cache --method c3 --encoder auto --quality standard --record work/wp5.2/W52-2/W52-2-fallback-gpu.json > work/wp5.2/W52-2/W52-2-fallback-gpu.log 2>&1
```

Before (d), prove holder exit/free recovery. Read both exit codes and records:
`counts`, `cancelled`, settings.force_cpu=false, method=c3,
parameters_from=defaults, items[0].state/outputs/device/elapsed_s/video. Quote
capacity reason verbatim and `GPU` on free card; no CPU-forced surrogate.

**R2 (e), proposed comparison request.** Use WP5.1's `decode_video_rgb`
(`tests/acceptance_support.py:298-335`) colour-pair/deep-sample conventions,
leading 30 frames. Choose the brief's explicitly permitted POST-ENCODE branch:
report mean <=3.5/255 as characterisation, with measured max separately, NOT
as proof of AD-11 pre-encode 2e-3 max / 2e-4 mean. WP5.1's 3.5/255 value was a
neutral/libx265 characterisation (`tests/test_v51_video_acceptance.py:50-55`),
so disclose this comparison's corrected/NVENC context. If the dispatcher wants
strict pre-encode AD-11 on THIS memory-pressure leg, it needs a seat observer
driver; the existing headless CLI emits no pre-encode frame records.

Exact proposed comparison command (first 30 frames, raw on disk / framewise
numeric reduction to avoid simultaneously holding two 30-frame float64 arrays):

```bash
uv run python - > work/wp5.2/W52-2/W52-2-compare.log 2>&1 <<'PY'
import json, subprocess, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, 'tools')
from clearwater.io.video import find_tool, probe
from clearwater.color import decode_filter
root = Path('work/wp5.2/W52-2')
source = root / 'W52-2-GX011627-cap30.mp4'
stream = probe(source).video
assert stream.bit_depth == 8
arrays = []
for label in ('cpu', 'gpu'):
    record = json.loads((root / f'W52-2-fallback-{label}.json').read_text())
    output = root / f'fallback-{label}/out' / record['items'][0]['outputs'][0]
    raw = root / f'W52-2-{label}-first30.raw'
    command = [str(find_tool('ffmpeg')), '-nostdin', '-hide_banner', '-v', 'error',
               '-noautorotate', '-i', str(output), '-map', '0:v:0', '-an', '-sn',
               '-dn', '-vf', decode_filter(stream), '-frames:v', '30',
               '-fps_mode', 'passthrough', '-f', 'rawvideo', 'pipe:1']
    with raw.open('xb') as dst:
        subprocess.run(command, stdout=dst, check=True)
    assert raw.stat().st_size == 30 * 3 * stream.height * stream.width
    arrays.append(np.memmap(raw, dtype=np.uint8, mode='r',
                            shape=(30, 3, stream.height, stream.width)))
largest, total, count = 0.0, 0.0, 0
for left, right in zip(*arrays, strict=True):
    difference = np.abs(left.astype(np.float32) - right.astype(np.float32))
    largest = max(largest, float(difference.max()))
    total += float(difference.sum(dtype=np.float64))
    count += difference.size
result = dict(window='W52-2', comparison='post-encode CPU vs GPU', frames=30,
              max_abs_255=largest, mean_abs_255=total/count,
              max_abs_unit=largest/255, mean_abs_unit=total/count/255,
              characterisation_mean_limit_255=3.5, passes=total/count <= 3.5)
(root / 'W52-2-fallback-compare.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result))
raise SystemExit(0 if result['passes'] else 1)
PY
```

Comparison expected seconds to a few minutes; seat records its actual wall but
it is not an export target. Verify identical dimensions/count/settings and no
sampler/runner errors. Keep both MP4s through comparison; only after read-back
and the explicit keep/delete grant remove them. No --keep switch exists on
headless_export. No comparison driver is committed or executed by this turn.

**R3 / W52-2 (F3 ruling needed).** There is NO valid current
`photo_verify.py memory` CLI satisfying synthetic PNG input AND wp5.2-only
outputs. Thus no falsely executable measurement command is supplied. Proposed
generator, for the seat ONLY after a ruling, using existing WP2.3 PNG16 form:

```bash
uv run python - > work/wp5.2/W52-2/W52-2-generate48.log 2>&1 <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, 'tools')
from fixtures.stills import unit_content, quantize, png16_bytes, srgb_profile
from local_config import load_local_config
root = Path.cwd() / 'work/wp5.2/W52-2'
assert root.is_relative_to(load_local_config().working_path.resolve())
output = root / 'W52-2-synthetic-48mp.png'
assert not output.exists()
pixels = quantize(unit_content('lowred', width=8064, height=6048), 16)
with output.open('xb') as dst:
    dst.write(png16_bytes(pixels, srgb_profile(), 'sRGB'))
print(output.name, '8064x6048', 'RGB16', 'seeded lowred', 'no EXIF')
PY
```

This is a PROPOSED replacement for the missing WP3.6P recipe, not an assertion
of a commissioned generator. Never run fixture generation at this size during
a light turn. After CHARC commissions the measurement mechanism, request two
fresh-runner legs, c3 defaults/PNG16, default then force CPU, exclusive=true,
roots `work/wp5.2/W52-2/photo48-default` and `photo48-cpu`, named W52-2 JSON.
Reuse `MemorySampler` and `launch_runner` (`photo_verify.py:1181`, `:1315`) with
a wp5.2 WriteGuard and assemble equivalent memory facts without mislabeling a
PNG as HEIC. Exact adapter/CLI commands remain a STOP item, not silently guessed.
Allow about 10 min for generation and both photo legs provisionally; prior owner
24.5 MP CPU 58.4 s is a different size/decoder and not a 48 MP prediction.
Read back stored_size, input/output depth, base estimate/free/reason, tree and
OS RSS peaks, full device peak, samples/active counts/gaps/errors and limits.
Ratios for a CPU-selected leg must say graphics-work ratio N/A. Neither photo
leg needs --keep; current memory tool retains output by default.

**R4.** Citation only, no run: owner 5d records and moments in section 1. No read
of the MAIN tree's old work outputs is authorised to this cell; committed report
and ledger receipts supply this round's citations, and seat supplies any later
record copy needed for audit.

### 6. Fullclip consumers / gate mapping

Repository search `rg` over all test Python files finds exactly these direct
consumers, retained in `work/wp5.2/round0/bench-consumers.log`:

| Test file | Consumer anchors | fullclip impact |
|---|---|---|
| `tests/test_export_bench.py` | `:17` import; `:182` onward main/record CLI tests; `:77` run_once tests | No fullclip marker or parameter. Module uses ffmpeg_tools fixture (`:21`). |
| `tests/test_wp321_bench.py` | `:16`, `:19` imports; `:39` run_once and folder/overlap tests | No fullclip marker or parameter; GPU node at `:51` is serial. |
| `tests/test_wp321_job_memory.py` | `:16` import; `:133`, `:148`, `:162` memory_check tests | No fullclip marker or parameter; pure bound/record checks. |

No test imports these three test modules. No fullclip node reads the changed
bench control path on this base; no fullclip leg requested. This is a static
consumer map, not a claimed collected-node identity run. Final gate at the seat
still recollects all/parallel/serial/fullclip and proves the disjoint union and
moved DR-99/B-F4 nodes. New breach test is parallel (<5 s); holder is gpu/serial.

### Validation, verification-loop record, and handoff

- `uv sync` exit 0; full output `work/wp5.2/round0/uv-sync.log`. uv noted the
  inherited MAIN VIRTUAL_ENV mismatched this worktree and ignored it; it created
  this worktree's `.venv`, not an active-MAIN installation. No lock/dependency
  manifest changed.
- Parser probe exit 2, expected refusal reproduced before footage/config lookup;
  map probe exit 0, all source/pure-arithmetic assertions passed. These are light
  source/CLI probes, not pytest runs or timing/memory measurements.
- Verification pass suspected then confirmed F1-F5 using separate parser/source/
  report surfaces above. Suspected fullclip exposure rejected by consumer and
  marker scan. Fixed: none (rulings required); no product fix attempted. No
  further independent unreported mapping issue found in the final text pass.
- No pytest, static-suite gate, GPU allocation, footage-folder read, MAIN-work
  read, other-worktree read, timed leg, reviewer process, mailbox post or commit.
  All new writes are this ledger, this worktree's ignored `.venv`/work and uv
  cache. Config untouched; product/frozen interfaces/fixtures/dependencies
  unchanged. No footage-derived bytes or GPS/IMU content in this ledger.
- Validation of ledger: LF/zero CR, ASCII text, required six sections and
  dispatcher-depth placeholder, `git diff --check`; results recorded in
  `work/wp5.2/round0/ledger-check.log`. Runtime validity of proposed window
  commands is pending the STOP rulings and future seat execution.

### Cumulative round ledger

| Round | Critical / major / minor | Envelope | NEW / REOPENED | Reverts | Fix surface | Transport / depth | Outcome |
|---|---|---|---|---|---|---|---|
| 0 (T1, not Reviewer A) | 0 / 4 / 1 dispatch-premise findings | 5 in / 0 out | 5 / 0 | 0 | Documentation only; no tool/product/test edits | Fresh Codex exec; depth dispatcher to fill | STOP for F1-F4 ruling; F5 planning correction; YIELD |

Reviewer A/B, their executed witnesses, both gate legs and T4/T5 remain pending.
