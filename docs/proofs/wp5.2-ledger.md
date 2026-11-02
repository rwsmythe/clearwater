# WP5.2 cumulative ledger

Package: WP5.2, performance and memory runs. Dispatch base and observed HEAD:
`70c3a5db26a9711c519d8ed1152d84c7f66e5b96`. Branch/worktree: `wp5.2` /
`C:/Users/rwsmy/clearwater/.worktrees/wp5.2`. This ledger records mapping and
proposed seat commands, not measured performance or acceptance. No N6 proposal
is made by the cell. The dispatcher owns commits, reviews and EXCLUSIVE windows.

## Round 0

Status: **STOP to CHARC through the dispatcher; T1 mapped, YIELD before T2.**
Depth: **169,581** (session 1, supplied by the dispatcher at session 2 dispatch).
Session 1 retired after round 0; no cell estimate substituted.

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

### 5. Revised RUN REQUESTS (CHARC 6e0128fd / eade11c9; seat only, NOT executed)

R0-F1-F5 are ruled, as folded into `docs/briefs/wp5.2-brief.md` under
"Round 0 ruling". The seat's configured working folder remains the main tree's
work. The cell never opens or writes that folder; seat records must be supplied
back to the cell through a subsequent authorised read-back. Commands below run
at the ORCHESTRATOR seat from the repo root in Git Bash, after Reviewer A and
the WP-DR113 gate, with no WP-DR113 reviewer or other heavy activity. No window
is opened by this turn.

Before EACH window: `df -h /c` (STOP below 25 GB free), available RAM,
`nvidia-smi --query-gpu=clocks.sm,clocks.mem,temperature.gpu,memory.free,memory.used --format=csv`,
and the process strays. Repeat conditions/strays at close. Open/close to CHARC;
no tests, reviewer, V4 witness or other heavy work during a window. GX011625 is
last in W52-1. A failed leg is retried once in a later window before STOP.
Every run log and record carries W52-1 or W52-2. Export failures retain records.
Cleanup of retained evidence follows an explicit keep/delete grant.

Shared seat setup (reads configuration; do not substitute this cell's cwd):

```bash
unset PYTEST_ADDOPTS
WORK52=$(uv run python -c "import sys; sys.path.insert(0,'tools'); from local_config import load_local_config; print((load_local_config().working_path/'wp5.2').as_posix())")
export WORK52
mkdir -p "$WORK52/v16/W52-1" "$WORK52/W52-2"
```

**R1 / W52-1 alone, about 115 min.** Eight exports in the six unchanged legs
mapped in section 1, device frames enabled, no --keep:

```bash
uv run python tools/export_bench.py v16 --device-frames --subdir wp5.2/v16/W52-1 > "$WORK52/v16/W52-1/W52-1-v16.log" 2>&1
```

Read exit status immediately (3 means memory breach; never continue the plan).
Use the exact printed RECORD path to rename that JSON byte-preserving with
the `W52-1-` prefix, beside the original location, recording pre/post SHA256.
Keep prior failed attempts too; do not select an arbitrary glob result. Require
eight records on success, read memory checks, resolved encoders and all keys
in section 1. No benchmark edit beyond DR-72 is commissioned.

**R2 preparation / W52-2.** WHOLE GX011627: 681 frames / about 22.7 s.
No time cap, frame duplication, or session-trim substitution. Exact stream copy:

```bash
uv run python - > "$WORK52/W52-2/W52-2-copy.log" 2>&1 <<'PY'
import os, subprocess, sys
from pathlib import Path
sys.path.insert(0, 'tools')
from local_config import load_local_config, find_footage_file
from clearwater.io.video import find_tool, probe
cfg = load_local_config()
root = Path(os.environ['WORK52']) / 'W52-2'
assert root.is_relative_to(cfg.working_path.resolve())
source = find_footage_file('GX011627', cfg.footage_path)
info = probe(source)
maps = ['-map', '0:v:0']
for stream in info.audio:
    maps += ['-map', f'0:{stream.index}']
for stream in info.data:
    if stream.codec_tag != 'tmcd':
        maps += ['-map', f'0:{stream.index}']
output = root / 'W52-2-GX011627-whole.mp4'
command = [str(find_tool('ffmpeg')), '-nostdin', '-hide_banner', '-v', 'error',
           '-n', '-i', str(source), *maps, '-c', 'copy', '-map_metadata', '0',
           '-map_metadata:s:v:0', '0:s:v:0', '-write_tmcd', '1',
           '-video_track_timescale', str(info.video.time_base.denominator),
           '-movflags', 'use_metadata_tags', '-f', 'mp4', str(output)]
subprocess.run(command, check=True)
copied = probe(output).video
assert copied.nb_frames == 681
print('WHOLE', output.name, 'frames', copied.nb_frames, 'fps', str(copied.frame_rate))
PY
```

**R2 holder and THREE exports / W52-2 (WDDM ruling / DR-114).**
The existing whole-GX011627 stream-copy command above is unchanged: 681 frames,
about 22.7 s, no time cap. R2 is now the held/free/forced-CPU characterisation;
it does NOT promise automatic fallback under cross-process memory pressure.
R3 supplies the D111 engagement witness. Before starting the holder, size it
from DEVICE-WIDE free MiB reported by nvidia-smi, never another process's
`cudaMemGetInfo` or `free_device_bytes()`:

```bash
unset PYTEST_ADDOPTS
nvidia-smi --id=0 --query-gpu=memory.free,memory.used --format=csv,noheader,nounits > "$WORK52/W52-2/W52-2-r2-before.csv" || exit $?
HOLD_MIB=$(uv run python -c "import math,sys; from pathlib import Path; free=float(Path(sys.argv[1]).read_text().strip().split(',')[0]); size=math.floor(free)-1536; assert size>0; print(size)" "$WORK52/W52-2/W52-2-r2-before.csv") || exit $?
printf '%s\n' "$HOLD_MIB" > "$WORK52/W52-2/W52-2-r2-hold-mib.txt"
STOP52="$WORK52/W52-2/W52-2-r2-hold.stop"
test ! -e "$STOP52" || exit 2
trap 'touch "$STOP52"; if [ -n "${HOLDER_PID:-}" ]; then wait "$HOLDER_PID"; fi' EXIT
uv run python tools/device_hold.py --mib "$HOLD_MIB" --stop-file "$STOP52" --timeout-s 3600 > "$WORK52/W52-2/W52-2-r2-holder.jsonl" 2> "$WORK52/W52-2/W52-2-r2-holder.stderr" &
HOLDER_PID=$!
uv run python - "$WORK52/W52-2/W52-2-r2-holder.jsonl" > "$WORK52/W52-2/W52-2-r2-readiness.log" 2>&1 <<'PY'
import json, sys, time
from pathlib import Path
path = Path(sys.argv[1])
deadline = time.monotonic() + 30
while True:
    text = path.read_text() if path.exists() else ''
    if text.endswith('\n'):
        record = json.loads(text)
        assert record['held_bytes'] > 0
        assert record['free_before'] > record['free_after']
        print(json.dumps(record))
        break
    assert time.monotonic() < deadline, 'holder readiness timeout'
    time.sleep(0.05)
PY
test $? -eq 0 || exit 1
kill -0 "$HOLDER_PID" || exit 1
nvidia-smi --id=0 --query-gpu=memory.free,memory.used --format=csv,noheader,nounits > "$WORK52/W52-2/W52-2-r2-during.csv" || exit $?
```

The size targets 1536 MiB (1.5 GiB) device-wide free; the holder's CUDA
context can reduce it further. Inspect the measured DURING free figure before
exporting and require about 1.5 GiB free; if context/strays make it materially
different, stop/re-size the holder from that observed discrepancy and retain
the calibration readings. Do not call the holder's own free-after a
device-wide reading. Keep its flushed line and before/during/after CSVs.
The holder must stay alive throughout the held export. Exact export commands
(same input, settings, separate fresh cache/output directories):

```bash
for leg in held free cpu; do
    mkdir -p "$WORK52/W52-2/W52-2-r2-$leg/out" "$WORK52/W52-2/W52-2-r2-$leg/cache"
done
{ time uv run python tools/headless_export.py "$WORK52/W52-2/W52-2-GX011627-whole.mp4" --out "$WORK52/W52-2/W52-2-r2-held/out" --cache-dir "$WORK52/W52-2/W52-2-r2-held/cache" --method c3 --encoder auto --quality standard --record "$WORK52/W52-2/W52-2-r2-held.json"; } > "$WORK52/W52-2/W52-2-r2-held.log" 2>&1
R2_HELD_STATUS=$?
printf '%s\n' "$R2_HELD_STATUS" > "$WORK52/W52-2/W52-2-r2-held.exit"
nvidia-smi --id=0 --query-gpu=memory.free,memory.used --format=csv,noheader,nounits > "$WORK52/W52-2/W52-2-r2-held-end.csv"
kill -0 "$HOLDER_PID" || exit 1
touch "$STOP52"
wait "$HOLDER_PID"
HOLDER_STATUS=$?
printf '%s\n' "$HOLDER_STATUS" > "$WORK52/W52-2/W52-2-r2-holder.exit"
trap - EXIT
nvidia-smi --id=0 --query-gpu=memory.free,memory.used --format=csv,noheader,nounits > "$WORK52/W52-2/W52-2-r2-after.csv" || exit $?
test "$R2_HELD_STATUS" -eq 0 && test "$HOLDER_STATUS" -eq 0 || exit 1
# Inspect AFTER and prove recovery before the free-card run; poll briefly if needed.
{ time uv run python tools/headless_export.py "$WORK52/W52-2/W52-2-GX011627-whole.mp4" --out "$WORK52/W52-2/W52-2-r2-free/out" --cache-dir "$WORK52/W52-2/W52-2-r2-free/cache" --method c3 --encoder auto --quality standard --record "$WORK52/W52-2/W52-2-r2-free.json"; } > "$WORK52/W52-2/W52-2-r2-free.log" 2>&1
R2_FREE_STATUS=$?
printf '%s\n' "$R2_FREE_STATUS" > "$WORK52/W52-2/W52-2-r2-free.exit"
test "$R2_FREE_STATUS" -eq 0 || exit "$R2_FREE_STATUS"
{ time uv run python tools/headless_export.py "$WORK52/W52-2/W52-2-GX011627-whole.mp4" --out "$WORK52/W52-2/W52-2-r2-cpu/out" --cache-dir "$WORK52/W52-2/W52-2-r2-cpu/cache" --method c3 --encoder auto --quality standard --force-cpu --record "$WORK52/W52-2/W52-2-r2-cpu.json"; } > "$WORK52/W52-2/W52-2-r2-cpu.log" 2>&1
R2_CPU_STATUS=$?
printf '%s\n' "$R2_CPU_STATUS" > "$WORK52/W52-2/W52-2-r2-cpu.exit"
test "$R2_CPU_STATUS" -eq 0 || exit "$R2_CPU_STATUS"
```

Record each exit, shell `time` wall and record `elapsed_s` / item `elapsed_s`,
device reason, settings, frames and output path. Held route is an OBSERVATION,
not an expected capacity-CPU assertion; free-card should read `GPU`, forced
CPU should read `CPU: forced` (AD-9). Require 681 frames/completed output on
each successful run. Inspect and retain any failure before the later-window
retry policy; never fabricate a successful held result.

`headless_export.py` has NO `--keep` option (parser at `:1185-1240`); it retains
outputs by default. The ruling's `--keep` intent is implemented by retaining
these THREE dedicated video outputs through comparison, rather than passing
an unsupported flag. R1 still omits --keep. After successful comparison and
read-back, the seat deletes exactly these three output MP4s named by their
runner records; keep all JSON, CSVs, logs, holder line, comparison records and
raw comparison samples. No other cleanup is authorised by this request.

**R2 first 30 decoded frames / W52-2.** Compare FREE vs forced CPU, and also
HELD vs FREE if the held run completed on GPU (expected identical decoded
frames). Record the literal CPU-vs-GPU AD-11 bounds (max 2e-3, mean 2e-4) in
unit scale and whether decoded pixels meet them. These exports include the
encoder, so this is not a pre-encode AD-11 proof. The brief's R2(e) allowance
and AD-11's clarification still apply: the separate post-encode
characterisation is mean <=3.5/255, explicitly labeled, never a replacement
pre-encode tolerance. Report both results, including any strict numeric miss;
if the post-encode characterisation also fails, follow the retry/STOP policy.
The held/free identity check has no tolerance. No bound or encoder is tuned.
Exact memory-bounded comparison request (WP5.1 decode colour conventions):

```bash
uv run python - > "$WORK52/W52-2/W52-2-r2-compare.log" 2>&1 <<'PY'
import json, os, subprocess, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, 'tools')
from clearwater.io.video import find_tool, probe
from clearwater.color import decode_filter
root = Path(os.environ['WORK52']) / 'W52-2'
records = {label: json.loads((root / f'W52-2-r2-{label}.json').read_text())
           for label in ('held', 'free', 'cpu')}
for label, record in records.items():
    assert (root / f'W52-2-r2-{label}.exit').read_text().strip() == '0'
    assert len(record['items']) == 1 and not record['cancelled']
    assert record['items'][0]['state'] in ('done', 'done with warnings')
    assert len(record['items'][0]['outputs']) == 1
assert records['free']['items'][0]['device'] == 'GPU'
assert records['cpu']['items'][0]['device'] == 'CPU: forced'
labels = ['free', 'cpu']
held_gpu = records['held']['items'][0]['device'] == 'GPU'
if held_gpu:
    labels.append('held')
arrays, signatures = {}, []
for label in labels:
    # Runner records deliberately redact outputs to basenames.
    name = records[label]['items'][0]['outputs'][0]
    assert Path(name).name == name
    video = root / f'W52-2-r2-{label}' / 'out' / name
    stream = probe(video).video
    assert stream.bit_depth == 8 and stream.nb_frames == 681
    signatures.append((stream.height, stream.width, stream.frame_rate))
    raw = root / f'W52-2-r2-{label}-first30.rgb'
    subprocess.run([str(find_tool('ffmpeg')), '-nostdin', '-v', 'error', '-n',
                    '-noautorotate', '-i', str(video), '-map', '0:v:0', '-frames:v', '30',
                    '-vf', decode_filter(stream), '-pix_fmt', 'gbrp',
                    '-fps_mode', 'passthrough', '-f', 'rawvideo', str(raw)], check=True)
    assert raw.stat().st_size == 30 * 3 * stream.height * stream.width
    arrays[label] = np.memmap(raw, dtype=np.uint8, mode='r',
                             shape=(30, 3, stream.height, stream.width))
assert len(set(signatures)) == 1
def compare(left, right):
    largest, total, count = 0.0, 0.0, 0
    for a, b in zip(arrays[left], arrays[right], strict=True):
        diff = np.abs(a.astype(np.float32) - b.astype(np.float32))
        largest = max(largest, float(diff.max()))
        total += float(diff.sum(dtype=np.float64))
        count += diff.size
    return dict(max_abs_255=largest, mean_abs_255=total/count,
                max_abs_unit=largest/255, mean_abs_unit=total/count/255)
cpu_gpu = compare('free', 'cpu')
cpu_gpu.update(ad11_numeric_max_limit=2e-3, ad11_numeric_mean_limit=2e-4,
               ad11_numeric_bounds_met=(cpu_gpu['max_abs_unit'] <= 2e-3
                                        and cpu_gpu['mean_abs_unit'] <= 2e-4),
               preencode_ad11_proved=False, comparison='post-encode free vs forced CPU',
               postencode_mean_limit_255=3.5,
               postencode_characterisation_passes=cpu_gpu['mean_abs_255'] <= 3.5)
held_free = compare('held', 'free') if held_gpu else None
if held_free is not None:
    held_free['identical'] = held_free['max_abs_255'] == 0
result = dict(window='W52-2', frames=30, cpu_gpu=cpu_gpu, held_free=held_free,
              held_device_reason=records['held']['items'][0]['device'],
              passes=(cpu_gpu['postencode_characterisation_passes']
                      and (held_free is None or held_free['identical'])))
with (root / 'W52-2-r2-compare.json').open('x', encoding='ascii') as dst:
    dst.write(json.dumps(result, indent=2))
print(json.dumps(result))
raise SystemExit(0 if result['passes'] else 1)
PY
```

**Window estimates (planning, not measurements).** W52-1 remains R1 alone,
about 115 min. W52-2: held GPU about 3.6-3.8 min + free GPU 3.6-3.8 min +
forced CPU provisionally 20 min + R3 generator/two photo legs about 10 min =
37-38 min, budget **40-45 min** with copy, holder, condition snapshots and
comparisons. If held also chooses CPU at the provisional CPU rate, budget
**55-60 min** instead. Record actual walls; failures/retries are additional.
No timed leg is run by this cell. No heavy work beside WP-DR113's reviewer.

**R3 / W52-2.** Generate the synthetic under the configured working folder,
then measure through the commissioned adapter. No full-size input is created
by the cell; no generated image/output is committed. Recipe:

```bash
uv run python - > "$WORK52/W52-2/W52-2-generate48.log" 2>&1 <<'PY'
import os, sys
from pathlib import Path
sys.path.insert(0, 'tools')
from fixtures.stills import unit_content, quantize, png16_bytes, srgb_profile
from local_config import load_local_config
from spike_io.guard import WriteGuard
cfg = load_local_config()
guard = WriteGuard(cfg.working_path.resolve() / 'wp5.2', cfg.footage_path)
output = Path(os.environ['WORK52']) / 'W52-2/W52-2-synthetic-48mp.png'
pixels = quantize(unit_content('lowred', width=8064, height=6048), 16)
with guard.check(output).open('xb') as dst:
    dst.write(png16_bytes(pixels, srgb_profile(), 'sRGB'))
print(output.name, '8064x6048', 'RGB16', 'seeded lowred', 'no EXIF')
PY
uv run python tools/photo_memory.py measure "$WORK52/W52-2/W52-2-synthetic-48mp.png" --name W52-2 --exclusive > "$WORK52/W52-2/W52-2-photo-memory.log" 2>&1
```

Records are `<working>/wp5.2/photo/W52-2-{default,cpu}-<unique>/record.json`.
Both legs are fresh runners, c3 defaults, PNG16; the first is default device,
the second explicit forced CPU. Read every 5d memory key mapped in section 1
and section 2 below. Expected base admission about 12.21 GB on an 8 GB card
means default CPU fallback is the D111 engagement witness of record: the
default-device record's `device_reason` must be the `CPU: estimate ... exceeds
free ...` capacity form. Forced CPU is not that witness. If the default leg
fits and selects GPU instead, record that result and state in Limits that
this package has no real D111 engagement witness. Either outcome is a result,
never a failed GPU attempt merely because the default used CPU. Record
device/RAM peaks on both, but graphics-work estimate ratios are N/A on CPU.
Allow about 10 min provisionally for generation plus the two legs. GUI margin
and 24.5 MP owner photo remain CITED (Q1/R4), no re-run.

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
| 0 (T1, not Reviewer A) | 0 / 4 / 1 dispatch-premise findings | 5 in / 0 out | 5 / 0 | 0 | Documentation only; no tool/product/test edits | Session 1 Codex exec; depth 169,581 | STOP for F1-F4 ruling; F5 planning correction; YIELD |

Reviewer A/B, their executed witnesses, both gate legs and T4/T5 remain pending.

## Session 2 / Turn 2: T2, T3 and the photo adapter

Status: tools built; light validation green; **STOP for the holder's
hardware verification retry**. Recommended disposition: permit ONE fresh
node-id run with the now-pinned per-test CuPy cache before Reviewer A / windows.
No Reviewer A round has run and no EXCLUSIVE window is open.
Depth: **140,094** (session 2 after turn 2, supplied by the dispatcher at
turn 3). Prior session retired at **169,581**, dispatcher-supplied.

### 1. Build and RED/GREEN evidence

One logical instrument-build change bundles T2/T3 and the R0-F3 adapter, as
ordered for this turn. No commit is attempted by the cell. Logs below are
under this worktree's ignored `work/wp5.2/turn2/`.

| Nodes / control | Before | After | Evidence |
|---|---|---|---|
| `test_v16_stops_on_memory_breach_and_keeps_records[0,1,2]` | All three FAIL: exit 0 instead of 3; pre-change plan runs onward. | PASS in first GREEN run. | `red-light-2.log`, `green-light.log` |
| `test_v16_continues_without_a_memory_breach[memory_check0,memory_check1]`; `test_v16_preserves_job_failure_status` | All three PASS (positive / compatibility controls). | PASS in first GREEN run. | Same logs. |
| Initial seven photo-adapter nodes | Seven setup ERRORs from explicit missing-module assertion; no production adapter exists. This is missing-feature RED, not a runtime result. | All seven PASS in first GREEN run. Later location tests use valid existing PNG16 outside the allowed root, so missing-file refusal cannot satisfy them. | Same logs. |
| Holder CLI absence control | `python tools/device_hold.py ...` exits 2: executable absent, before any CUDA import/allocation. | Built CLI; hardware node result is STALLED, not GREEN. | `red-holder.log`, `green-holder.log` |
| `tests/test_device_hold.py::test_device_hold_releases_on_stop_file` | GPU node not invoked in RED, reserving the dispatch's ONCE-only invocation for hardware GREEN; the CLI absence control above is the disclosed substitution. | Invoked exactly ONCE by node id; stalled in parent backend probe, before holder subprocess/readiness. Killed own pytest PID 43224 after the 300 s stack dump identified the cache write. No passed/failed pytest summary. | `green-holder.log` stack, `holder-stop.log`; tool wrapper observed exit -1. |

The first RED invocation (`red-light.log`) had 13 temp-setup ERRORs because
the basetemp's parent did not exist. Created `work/wp5.2/tmp`, then used a
NEW basetemp for the distinguishing RED above: **3 failed, 3 passed, 7 errors
in 1.06 s**. First GREEN: **13 passed in 1.00 s**. Temp-parent errors are not
counted as regression evidence. Hardware RED/GREEN remains incomplete.

### 2. Rules implemented and record schema

- T2: `tools/export_bench.py:890` checks an explicitly false
  `memory_check.passes` after append/write/row output; returns 3 immediately,
  exiting both loops. Inapplicable checks lacking `passes` continue. Earlier
  records AND the breached record stay on disk. Module exit-status docstring
  at `:55` names 3 beside 0/1/2. No other bench behaviour was edited.
- T3: `tools/device_hold.py:37` parses finite positive timeout and positive
  integral MiB, requires an absent stop file in an existing parent, selects
  device 0, establishes context, reads free-before, holds ONE CuPy byte buffer,
  touches/synchronises, and flushes ONE JSON readiness line. `held_bytes` is
  the actual allocator block size; `free_after` is while still holding. The
  50 ms monotonic loop observes the stop file or timeout; finally drops the
  buffer and frees the pool. It only inspects the stop file. No OS-specific
  API/dependency is added; external hard kill relies on process CUDA cleanup.
- Holder test at `tests/test_device_hold.py:15` uses a parent backend
  `free_device_bytes()` before/during/after the subprocess, checks >=256 MiB
  drop, stop-file exit AND full free recovery inside 2 s, and reaps on failure.
  `gpu` module marker places this node in serial. At `:21`, the test now pins
  `CUPY_CACHE_DIR` to its own tmp folder before backend import, inherited by
  the child. This remedy has NOT been hardware-retried under the ONCE lock.
- R3 adapter: `tools/photo_memory.py:137` requires `--exclusive`, validates
  the name, resolves input through `WriteGuard` before reading it, refuses
  footage/outside/root-directory/missing/non-PNG16 inputs, and checks RGB16
  IHDR before creating outputs. Output guard is `<working>/wp5.2/photo`.
  It runs default then forced CPU (`:178`) in fresh isolated runner folders.
  It imports `photo_verify.MemorySampler` (`:71`) and `launch_runner` (`:77`)
  with the existing caller guard/sampler contexts (`:72-90`), never copies
  either implementation. `photo_verify.py` is untouched. Existing private
  header/disk/version/reason/name helpers are imported through that module;
  no new shared or frozen API is introduced. The 48 MP generator is the
  documented recipe through `fixtures.stills`, not a fixture/blob or cell run.
- Photo summary keys match 5d: `schema`, `command`, `file`, `class`,
  `stored_size`, `method`, `force_cpu`, `forced_cpu`, `exclusive`,
  `estimate_bytes`, `device_free_before_bytes`, `device_total_bytes`,
  `estimate_exceeds_free_before`, `estimate_fits_free_before`, `rss_scope`,
  `decoder_versions`, `ram_limit_bytes`, `device_limit_bytes`,
  `measured_at_utc`, all keys of imported `MemorySampler.record()`
  (`rss_baseline_bytes`, `rss_tree_peak_bytes`, `os_peak_working_set_bytes`,
  `device_used_baseline_bytes`, `device_used_peak_bytes`, `rss_samples`,
  `device_samples`, `rss_active_samples`, `device_active_samples`,
  `sample_intervals_s`, `sample_interval_kind`, `sampling_cadence_s`,
  `sampler_elapsed_s`, `sampler_errors`, `rss_scope`), `runner_exit`,
  `device_reason`, `read_ok`, `automatic_fallback`,
  `memory_capacity_fallback`, `ram_within_limit`, `device_within_limit`,
  `failed_checks`. `class` is honestly `synthetic-png16`; no owner HEIC/JPEG
  class is fabricated. RSS cap is 16,000,000,000 B and device cap 8188 MiB,
  as 5d. Inactive/missing samples cannot pass, and a known peak breach cannot
  be erased by missing active samples. Both legs' summaries persist even if
  one reports failed checks. Runner exceptions stop with exit 1.

### 3. Verification loop, deviations and open items

| Suspect | Independently confirmed / rejected | Disposition |
|---|---|---|
| DR-72 ignores memory breach | Confirmed by three planted prefixes through existing `run_once` and persisted JSON, with passing and job-failure controls. | FIXED in owned bench control; GREEN above. |
| New location controls might pass just because outside inputs are absent | Confirmed from initial test fixture setup; no product failure inferred. | Test inputs now include valid existing RGB16 copies outside/root sibling/fake footage. No real footage accessed. |
| GPU test stalled in parent before the holder | Confirmed by 300 s faulthandler stack: `backend_for` -> `_probe_gpu` -> CuPy arange compiler -> `_compiler_cache._write_encoded` -> `tempfile._mkstemp_inner`. No holder files/subprocess had been created. | Own stalled pytest killed; no further GPU invocation. |
| CuPy cache defaults outside sandbox writable roots | Confirmed independently by installed `_compiler_cache.py:27,93,140`: default `~/.cupy/kernel_cache`, overridden by `CUPY_CACHE_DIR`, temporary cache write uses that directory. Actual failed outside write effect is NOT claimed or inspected. | Test pins cache under tmp; confirmation by hardware rerun is STOP / dispatcher decision, not a claimed fix. |
| Photo adapter could silently pass missing samples, RAM breach or failed runner | Controlled light cases at runner/sampler seam, plus literal capacity-reason check, all passed in final regression. | Rejected as a remaining fault; protected by tests. |
| Fullclip exposure / product changes | Rejected by round-0 consumer map and current owned-file diff; no src/interface/fixture/dependency change. | Existing fullclip exclusion stands; collection identity belongs to seat gate. |

RUN REQUESTS in round-0 section 5 have been REPLACED with the ruled,
seat-only configured-working-root commands: R1 W52-1 (~115 min) and R2+R3
W52-2, whole GX011627 (no `-t`), decoded prefix comparison, 48 MP recipe,
and `photo_memory.py measure`. No measured figure, N6 proposal or report
table is invented; T4/T5 await seat windows/read-back. No reviewer, gate,
mailbox post, commit, footage/media read, MAIN-work read or other-worktree
read was performed by the cell. No local config or unowned source edited.
All deliberate cell file writes stay in this worktree/work/uv cache. The
stalled CuPy probe attempted its default external compiler-cache write;
no successful external effect is asserted. No footage-derived bytes or
GPS/IMU values are in the changed files.

### 4. Final light validation and cumulative status

Final targeted light command, with `PYTHONPATH=scripts`, `PYTEST_ADDOPTS`
unset and `CUPY_CACHE_DIR` under this worktree's work folder:

```text
uv run pytest -q -rs tests/test_export_bench_breach.py tests/test_photo_memory.py tests/test_export_bench.py tests/test_photo_verify.py -m "not gpu and not footage and not slow and not fullclip" --basetemp=work/wp5.2/tmp/green-regression -p sandbox_mkdir_shim -p no:cacheprovider
```

Result: **156 passed, 1 deselected in 90.70 s**, exit 0, no skips/failures/errors;
log `work/wp5.2/turn2/green-regression.log`. Only the existing footage-marked
photo node was deselected. New breach controls were already included in the
1.00 s first GREEN, within their <5 s envelope; no wall bound is added to a
parallel test. No GPU test is included in this regression command.
The single GPU node command was:

```text
uv run pytest -q -rs tests/test_device_hold.py::test_device_hold_releases_on_stop_file --basetemp=work/wp5.2/tmp/green-holder -p sandbox_mkdir_shim -p no:cacheprovider
```

That invocation is STALLED/terminated, not passed, as section 1 records. No
GPU retry has been run. All pytest basetemps are fresh under the required tmp
root and every invocation loaded both mandated plugin switches. Full suite,
Reviewer A/B, collection identity and both gate legs remain at the dispatcher
seat; no full suite is authorised for this turn.

Static checks on all six changed Python files: `ruff-final.log` **All checks
passed!**; `format-final.log` **6 files already formatted**. Full `uv run mypy`
in `mypy-first.log`: **Success: no issues found in 156 source files**. Final
post-documentation checks: `ruff-handoff.log` **All checks passed!**, exit 0;
`format-handoff.log` **6 files already formatted**, exit 0;
`mypy-handoff.log` **Success: no issues found in 156 source files**, exit 0.
`audit-handoff.log` exits 0: all seven owned paths ASCII/LF/zero CR,
all three seat-only Python recipe bodies syntax-valid (NOT executed), exact
seven-path scope, and `git diff --check` clean.
No dependency manifests changed. Final source/contract pass found no new
in-envelope implementation issue beyond the explicitly unverified holder
hardware control. The executable generator lives in section 5; the tool
docstring points there, avoiding a shell-quoted multiline `python -c` recipe.

| Round / turn | Critical / major / minor | Envelope | NEW / REOPENED | Reverts | Fix surface | Transport / depth | Outcome |
|---|---|---|---|---|---|---|---|
| Session 2 / turn 2 (build; not Reviewer A) | 0 / 1 / 0 validation blocker | 1 in / 0 out | 1 / 0 | 0 | Tools + tests + ledger; no product module | Codex exec; depth 140,094 | T2 light GREEN; adapter light GREEN; holder hardware STALLED; STOP for one cache-pinned retry; YIELD |

The validation blocker is the once-only holder run, not a measured D111
product failure. Recommended next dispatch: authorise one GPU-node retry
with the writable cache, then Reviewer A before any EXCLUSIVE window.

## Session 2 / Turn 3: the WDDM ruling

Status: WDDM test assertion and run-request changes implemented; YIELD for
the dispatcher's seat-only holder run and Reviewer A round 1 before windows.
This turn executes NO gpu test invocation, holder launch, timed leg or
EXCLUSIVE window. The turn-2 STOP is resolved by the binding WDDM ruling;
hardware verification remains at the seat, with no sandbox retry requested.
Depth: **dispatcher to fill from this turn's transcript**. Turn-2 depth is
**140,094**, dispatcher-supplied, now recorded in its own depth line and row.
Binding ruling: CHARC `eade11c9`, folded at `3fcad7a9` in the brief's newest
"WDDM ruling" section. It replaces the disputed cross-process premise; no
frozen interface, product module, tolerance or dependency is changed here.

### Change and adjudication

- **[MAJOR, IN, NEW, ruled] Cross-process memory assertion:** accepted on
  the dispatcher's executed seat evidence, not retested in the sandbox.
  Removed every parent `backend_for` / `free_device_bytes` / CUDA probe from
  `tests/test_device_hold.py`. The test's baseline and subsequent readings
  now call `video_fidelity._nvidia_smi` with device 0,
  `--query-gpu=memory.used --format=csv,noheader,nounits` (`:18-24`). It
  follows that helper's unavailable/timeout/nonzero-exit handling and skips
  with an explicit device-wide-memory reason before starting the holder
  when nvidia-smi is unavailable. No independent sampler implementation is
  copied; malformed numeric readings fail instead of satisfying the bound.
- Holder JSON still requires `held_bytes >= 256 MiB` and its OWN
  `free_before - free_after >= 256 MiB`. Device-wide used must rise at least
  200 MiB from the pre-holder baseline (`:64-71`). The stop file must produce
  exit 0 within 2 s (`:72-77`); after exit, separately poll device-wide used
  back to at most baseline (`:78-84`). Rise/recovery each use a 5 s polling
  budget with 50 ms waits; individual nvidia-smi calls retain the existing
  helper's 30 s subprocess sanity timeout. `CUPY_CACHE_DIR` stays below
  `tmp_path`, inherited by the child. Failure/skip cleanup still stops/reaps
  the holder. The module remains `gpu`; the hardware result is PENDING the
  seat, not inferred from lint or the light suite.
- `tools/device_hold.py` is UNCHANGED: its own-process readiness figures,
  allocation and stop/release mechanism already match ruling (c). The
  invalid assumption belonged to the observing test, not the holder.
- **[MINOR, IN, confirmed and fixed] Comparison record-reading control:**
  source tracing at `headless_export.record_object` (`:1045-1069`) and
  `BatchReport.counts` (`src/clearwater/jobs/batch.py:57`) confirms that
  outputs are basenames and terminal states are `done` / `done with
  warnings`, not a `completed` counter. The revised comparison joins each
  output basename to its named leg's `out` folder and checks actual item
  state, output count and exit receipts. This is a correction to the
  unexecuted seat recipe, with no product change or real-file read.

### Revised run requests and expected windows

The live commands in round-0 section 5 have been REPLACED under the WDDM
ruling. R1 stays exactly `uv run python tools/export_bench.py v16
--device-frames --subdir wp5.2/v16/W52-1`; W52-1 alone, about 115 min, final
GX011625 row last, record renamed byte-preserving with the W52-1 prefix.

R2 in W52-2 now has THREE full-681-frame headless exports with named records,
dedicated output/cache folders, logs, shell wall times and exit receipts:
`W52-2-r2-held`, `W52-2-r2-free`, `W52-2-r2-cpu`. Only the last passes
`--force-cpu` (AD-9). The holder is sized from nvidia-smi DEVICE-WIDE free
MiB minus 1536, then verified by device-wide before/during/after readings
and its own JSON. Read and record the actual held-run route, completion,
wall and exit, without asserting automatic fallback from the holder.
The commands retain exactly these three video outputs through comparison;
headless_export has no literal --keep flag, so no unsupported argument is
added. Delete just those three output MP4s after comparison/read-back; keep
records, raw comparison samples, CSVs and logs. R1 keeps its existing policy.

The first 30 decoded frames compare free-card GPU vs forced CPU, recording
the literal AD-11 max/mean numeric bounds and whether decoded outputs meet
them, plus the explicitly distinct post-encode 3.5/255 mean characterisation
allowed by the brief's R2(e). Do not claim a pre-encode AD-11 proof from these
encoded MP4s. If the held run completed on GPU, compare held/free as well,
with exact decoded identity expected. Every strict numeric miss is reported,
not hidden by the separate characterisation result. No threshold is changed.

R3's exact generator and `photo_memory.py measure ... --name W52-2
--exclusive` commands remain in section 5. Its DEFAULT-device 48 MP record
is the D111 engagement witness: require the CPU estimate/exceeds-free reason
as the witness, while recording GPU selection instead if it fits. In that
case the report explicitly says this package has no real D111 witness.
The forced-CPU photo leg does not establish automatic fallback.

W52-2 planning: about 3.6-3.8 min held GPU + 3.6-3.8 min free GPU + 20 min
forced CPU + 10 min R3 generator/two photo legs = 37-38 min, reserve
**40-45 min** with setup/comparisons. If held also selects CPU, reserve
**55-60 min** instead. These extrapolate historical rates, not newly
measured figures. All windows remain at the seat, opened/closed to CHARC,
with the 25 GB disk floor, clocks/temperature/strays and no other heavy work
(including WP-DR113's reviewer). No window is requested open by this turn.

### Report Limits draft (seat evidence, DR-114)

On this Windows/WDDM card, CUDA's free-memory figure is process-local:
the test process read **7,407,142,400 B** both before and during the hold;
a second-process 2 GiB probe read **7,411,335,168 B** before/during/after,
while the holder itself reported `held_bytes=2147483648`,
`free_before=7411335168`, `free_after=5261754368`, and device-wide
nvidia-smi used memory was **2,826 MiB during / 663 MiB after**. These are
the dispatcher's seat observations accepted by CHARC `eade11c9`, not cell
measurements. Consequently cross-process physical pressure may not alter
the product's admission free-memory operand; **DR-114 remains OPEN** and
R2's actual held route is recorded as its evidence. R3's own image estimate
supplies D111's engagement witness if its default-device record selects the
CPU for the capacity reason; otherwise this package reports no real witness.

### Light validation, verification loop and cumulative status

All test execution this turn is limited to the four authorised parallel-leg
modules (`test_export_bench_breach.py`, `test_photo_memory.py`, existing
`test_export_bench.py` and `test_photo_verify.py`), with
`-m "not gpu and not footage and not slow and not fullclip"`. Environment:
`PYTHONPATH=scripts`, `PYTEST_ADDOPTS` unset, fresh
`--basetemp=work/wp5.2/tmp/turn3-light`, both `-p sandbox_mkdir_shim` and
`-p no:cacheprovider`; CuPy cache also pinned under this turn's work folder.
Log: `work/wp5.2/turn3/light.log`: **156 passed, 1 deselected in 72.31 s**,
exit 0, no skips/failures/errors. The one existing footage node is deselected,
as in turn 2. The holder's gpu module is deliberately not invoked, even for
a retry. `ruff.log`: **All checks passed!**, exit 0; `format.log`: **6 files
already formatted**, exit 0; full `uv run mypy` in `mypy.log`: **Success: no
issues found in 156 source files**, exit 0. These paths are under
`work/wp5.2/turn3/`. Final byte/scope and recipe-syntax audit is in
`audit.log`; the seat-only recipe bodies are syntax-checked, not executed.

Verification loop: confirmed the ruled test premise against the old
assertion and supplied seat evidence, changed only the observer; traced and
fixed both recipe record-shape errors against actual serialization; checked
that R3 rather than a forced route is the capacity witness; rejected the
need to change the holder tool because its own-process facts are already
correct. The final pass found no further in-envelope issue; hardware results
are explicitly pending, not inferred from the green light/static checks.
No footprint outside the two changed owned paths and ignored work files;
no local-config, footage/media, MAIN-work or other-worktree read; no product,
interface, fixture, dependency, mailbox or git write. No performance/N6
figure or hardware GREEN is asserted. Reviewer A remains dispatcher-run.

| Round / turn | Critical / major / minor | Envelope | NEW / REOPENED | Reverts | Fix surface | Transport / depth | Outcome |
|---|---|---|---|---|---|---|---|
| Session 2 / turn 3 (ruling implementation; not Reviewer A) | 0 / 1 / 1 | 2 in / 0 out | 2 / 0 | 0 | Test + ledger only; tools/product unchanged | Codex exec; depth dispatcher to fill | WDDM assertion replaced as ruled; 156 light tests passed; hardware at seat; YIELD for Reviewer A round 1 |
