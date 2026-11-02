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

Before EACH window: `df -h /c` (STOP below 25 GB for W52-1;
30 GB for W52-2; R3 rechecks 25 GB before generation), available RAM,
`nvidia-smi --query-gpu=clocks.sm,clocks.mem,temperature.gpu,memory.free,memory.used --format=csv`,
and the process strays. Repeat conditions/strays at close. Open/close to CHARC;
no tests, reviewer, V4 witness or other heavy work during a window. GX011625 is
last in W52-1. A failed leg is retried once in a later window before STOP.
Every run log and record carries W52-1 or W52-2. Export failures retain records.
Cleanup of retained evidence follows an explicit keep/delete grant.

Each request below is ONE self-contained bash script in ONE fenced block.
At the seat, save each under the main tree's work/wp5.2 folder and invoke it
as ONE `bash <file>` from the repo root; no shell state crosses blocks.
Script files remain uncommitted. There is no shared setup block.

**R1 / W52-1 alone, about 115 min.** Eight exports in six unchanged legs,
device frames enabled, no --keep. Disk floor: **25 GB**. Configuration/root
validation precedes writes; after bootstrap, disk/bench/record steps each
capture their status in unique receipt files beside the bench records.
Bench exit is captured immediately, including exit 3 for a memory-check
failure. The exact printed RECORD path is read (never a glob), renamed with
the W52-1 prefix, and SHA256 compared before/after. Exit 3 receipts include
the stopped `memory_check`, `idle_before_mib` and device peak; the idle is
stated, never subtracted. Prior attempts remain; no plan resumes after exit 3.

```bash
set -euo pipefail
unset PYTEST_ADDOPTS
WORK52=$(uv run python - <<'PY'
import sys
sys.path.insert(0, 'tools')
from local_config import load_local_config
from spike_io.guard import WriteGuard
cfg = load_local_config()
working = cfg.working_path.resolve()
root = working / 'wp5.2'
assert root.resolve() == root and root.is_relative_to(working)
guard = WriteGuard(root, cfg.footage_path)
guard.folder('v16/W52-1')
print(root.as_posix())
PY
)
: "${WORK52:?}"
export WORK52
R1ROOT="$WORK52/v16/W52-1"
ATTEMPT52="$(date -u +%Y%m%dT%H%M%SZ)-$$"
R1RECEIPT="$R1ROOT/W52-1-$ATTEMPT52"
export R1ROOT R1RECEIPT
if uv run python - > "$R1RECEIPT-disk.log" 2>&1 <<'PY'
import os, shutil
from pathlib import Path
root = Path(os.environ['R1ROOT'])
free = shutil.disk_usage(root).free
print('disk_free_bytes', free, 'required', 25_000_000_000)
raise SystemExit(0 if free >= 25_000_000_000 else 2)
PY
then DISK_STATUS=0; else DISK_STATUS=$?; fi
printf '%s\n' "$DISK_STATUS" > "$R1RECEIPT-disk.exit"
if [ "$DISK_STATUS" -ne 0 ]; then exit "$DISK_STATUS"; fi
R1LOG="$R1RECEIPT-v16.log"
export R1LOG
if uv run python tools/export_bench.py v16 --device-frames --subdir wp5.2/v16/W52-1 > "$R1LOG" 2>&1; then
    BENCH_STATUS=0
else
    BENCH_STATUS=$?
fi
# Capture immediately; 3 is memory-check failure, including unmeasured peak.
printf '%s\n' "$BENCH_STATUS" > "$R1RECEIPT-bench.exit"
export BENCH_STATUS
if uv run python - > "$R1RECEIPT-record.log" 2>&1 <<'PY'
import hashlib, json, os
from pathlib import Path
root = Path(os.environ['R1ROOT']).resolve()
log = Path(os.environ['R1LOG'])
status = int(os.environ['BENCH_STATUS'])
printed = [line[len('RECORD '):].strip()
           for line in log.read_text(encoding='utf-8').splitlines()
           if line.startswith('RECORD ')]
receipt = dict(window='W52-1', bench_exit=status, log=log.name,
               record=None, sha256_before=None, sha256_after=None)
post_status = 0
try:
    if not printed:
        receipt['reason'] = 'bench printed no RECORD path; inspect exit and log'
        post_status = 1
    else:
        assert len(printed) == 1, printed
        source = Path(printed[0]).resolve()
        assert source.parent == root, source
        before = hashlib.sha256(source.read_bytes()).hexdigest()
        record = json.loads(source.read_text(encoding='utf-8'))
        receipt.update(record=source.name, sha256_before=before,
                       run_count=len(record['runs']))
        if status == 3:
            stopped = record['runs'][-1]
            check = stopped.get('memory_check') or {}
            assert check.get('passes') is False
            receipt.update(memory_check=check,
                           idle_before_mib=check.get('idle_before_mib'),
                           device_peak_mib=check.get('device_peak_mib'),
                           failure='memory check failed (a breach, or the device peak unmeasured)')
            print(json.dumps({key: receipt[key] for key in
                  ('memory_check', 'idle_before_mib', 'device_peak_mib', 'failure')}))
        target = source.with_name('W52-1-' + source.name)
        assert not target.exists(), target
        source.rename(target)
        after = hashlib.sha256(target.read_bytes()).hexdigest()
        receipt.update(record=target.name, sha256_after=after)
        assert before == after
        if status == 0:
            assert len(record['runs']) == 8

except Exception as error:
    receipt['reason'] = f'{type(error).__name__}: {error}'
    post_status = 1
receipt['record_step_exit'] = post_status
with Path(os.environ['R1RECEIPT'] + '-record.json').open('x', encoding='ascii') as dst:
    dst.write(json.dumps(receipt, indent=2, ensure_ascii=True) + '\n')
print(json.dumps(receipt, ensure_ascii=True))
raise SystemExit(post_status)
PY
then RECORD_STATUS=0; else RECORD_STATUS=$?; fi
printf '%s\n' "$RECORD_STATUS" > "$R1RECEIPT-record.exit"
# Preserve the bench's status, including 3, even if record handling also failed.
if [ "$BENCH_STATUS" -ne 0 ]; then exit "$BENCH_STATUS"; fi
exit "$RECORD_STATUS"
```

**R2 / W52-2: ONE self-contained bash script.** Save the following ONE
block under the main tree's `work/wp5.2/W52-2/` at the seat and run it as
ONE `bash <file>` invocation from the repo root. The script file is never
committed. No shell state is inherited from R1 or any shared setup. It computes
and validates WORK52, refuses below **30 GB** free, and preserves each attempt
in `W52-2/attempt-<UTC>-<pid>/`. Each stop file is unique to that attempt.
Records retain the required W52-2-r2-held / -free / -cpu names inside it.

WHOLE GX011627 is 681 frames / about 22.7 s, stream-copied without a time
cap or duplication. The holder targets 1536 MiB device-wide free, with an
automated inclusive **1280-1792 MiB** DURING band. Outside that band the script
releases/reaps it and exits 2 before exporting; the seat retries, with no
manual pause or automatic re-size. Holder timeout is **3600 s**.
The held export runs under **timeout 2400**; status **124** is recorded as
the held observation and never gates the independent pair. An EXIT trap releases
the holder on normal shell exits (not an uncatchable kill); liveness receipts
before and after the held export qualify the pressure observation.

The held export's exit is an OBSERVATION: no assertion requires zero. Every
held outcome proceeds to recovery and the free/CPU exports, subject to the
explicit free-card safety guard: after stopping/reaping the holder, poll for
device-wide used <= pre-holder + **100 MiB**, within **30 s**, otherwise
record refusal and exit 2. Free vs CPU comparison is always attempted after
those two exports. Held vs free is compared only on held exit 0 and GPU route;
otherwise the comparison record states why it was skipped. If free or CPU
failed, compare.json still records each failed leg and its exit status,
without attempting to read its incomplete/missing export record. R3 remains the
D111 engagement witness; cross-process pressure does not promise fallback.

```bash
set -euo pipefail
unset PYTEST_ADDOPTS
# All setup, copy, holder, exports and comparison run in THIS bash process.
WORK52=$(uv run python - <<'PY'
import sys
sys.path.insert(0, 'tools')
from local_config import load_local_config
from spike_io.guard import WriteGuard
cfg = load_local_config()
root = cfg.working_path.resolve() / 'wp5.2'
guard = WriteGuard(root, cfg.footage_path)
guard.folder('W52-2')
print(root.as_posix())
PY
)
: "${WORK52:?}"
export WORK52
uv run python - <<'PY'
import os, shutil, sys
from pathlib import Path
sys.path.insert(0, 'tools')
from local_config import load_local_config
cfg = load_local_config()
root = Path(os.environ['WORK52']).resolve()
assert root == cfg.working_path.resolve() / 'wp5.2'
assert root.is_relative_to(cfg.working_path.resolve())
free = shutil.disk_usage(root).free
print('W52-2 disk_free_bytes', free, 'required', 30_000_000_000)
if free < 30_000_000_000:
    raise SystemExit('REFUSED: W52-2 requires at least 30 GB free')
PY
# An attempt folder preserves every retry's logs, receipts and outputs.
ATTEMPT52="$(date -u +%Y%m%dT%H%M%SZ)-$$"
R2ROOT="$WORK52/W52-2/attempt-$ATTEMPT52"
mkdir "$R2ROOT"
export R2ROOT
STOP52="$R2ROOT/W52-2-r2-hold-$ATTEMPT52.stop"
HOLDER_PID=''
release_holder() {
    touch "$STOP52"
    if [ -n "$HOLDER_PID" ]; then
        if wait "$HOLDER_PID"; then HOLDER_STATUS=0; else HOLDER_STATUS=$?; fi
        printf '%s\n' "$HOLDER_STATUS" > "$R2ROOT/W52-2-r2-holder.exit"
        HOLDER_PID=''
    fi
}
cleanup() {
    local status=$?
    trap - EXIT
    set +e
    if [ -n "$HOLDER_PID" ]; then release_holder; fi
    exit "$status"
}
trap cleanup EXIT

uv run python - > "$R2ROOT/W52-2-copy.log" 2>&1 <<'PY'
import os, subprocess, sys
from pathlib import Path
sys.path.insert(0, 'tools')
from local_config import load_local_config, find_footage_file
from clearwater.io.video import find_tool, probe
cfg = load_local_config()
root = Path(os.environ['R2ROOT'])
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

nvidia-smi --id=0 --query-gpu=memory.free,memory.used --format=csv,noheader,nounits > "$R2ROOT/W52-2-r2-before.csv"
HOLD_MIB=$(uv run python -c "import math,sys; from pathlib import Path; free=float(Path(sys.argv[1]).read_text().strip().split(',')[0]); size=math.floor(free)-1536; assert size>0; print(size)" "$R2ROOT/W52-2-r2-before.csv")
printf '%s\n' "$HOLD_MIB" > "$R2ROOT/W52-2-r2-hold-mib.txt"
uv run python tools/device_hold.py --mib "$HOLD_MIB" --stop-file "$STOP52" --timeout-s 3600 > "$R2ROOT/W52-2-r2-holder.jsonl" 2> "$R2ROOT/W52-2-r2-holder.stderr" &
HOLDER_PID=$!
uv run python - "$R2ROOT/W52-2-r2-holder.jsonl" > "$R2ROOT/W52-2-r2-readiness.log" 2>&1 <<'PY'
import json, sys, time
from pathlib import Path
path = Path(sys.argv[1])
deadline = time.monotonic() + 30
while True:
    text = path.read_text() if path.exists() else ''
    if '\n' in text:
        record = json.loads(text.splitlines()[0])
        assert record['held_bytes'] > 0
        assert record['free_before'] > record['free_after']
        print(json.dumps(record))
        break
    assert time.monotonic() < deadline, 'holder readiness timeout'
    time.sleep(0.05)
PY
nvidia-smi --id=0 --query-gpu=memory.free,memory.used --format=csv,noheader,nounits > "$R2ROOT/W52-2-r2-during.csv"
if ! uv run python - "$R2ROOT/W52-2-r2-during.csv" > "$R2ROOT/W52-2-r2-band.log" 2>&1 <<'PY'
import sys
from pathlib import Path
free = float(Path(sys.argv[1]).read_text().strip().split(',')[0])
print('device-wide free MiB', free, 'required band', [1280, 1792])
raise SystemExit(0 if 1280 <= free <= 1792 else 2)
PY
then
    release_holder
    exit 2
fi
for leg in held free cpu; do
    mkdir -p "$R2ROOT/W52-2-r2-$leg/out" "$R2ROOT/W52-2-r2-$leg/cache"
done
run_export() {
    local leg=$1 status
    local -a export_limit=()
    if [ "$leg" = held ]; then export_limit=(timeout 2400); fi
    shift
    # An export exit is a receipt, not an errexit trigger, including held failure.
    if { time "${export_limit[@]}" uv run python tools/headless_export.py "$R2ROOT/W52-2-GX011627-whole.mp4" --out "$R2ROOT/W52-2-r2-$leg/out" --cache-dir "$R2ROOT/W52-2-r2-$leg/cache" --method c3 --encoder auto --quality standard --record "$R2ROOT/W52-2-r2-$leg.json" "$@"; } > "$R2ROOT/W52-2-r2-$leg.log" 2>&1; then
        status=0
    else
        status=$?
    fi
    printf '%s\n' "$status" > "$R2ROOT/W52-2-r2-$leg.exit"
}
if kill -0 "$HOLDER_PID"; then
    printf 'alive\n' > "$R2ROOT/W52-2-r2-holder-alive-before.txt"
else
    printf 'not alive; refused held export\n' > "$R2ROOT/W52-2-r2-holder-alive-before.txt"
    exit 2
fi
run_export held
if kill -0 "$HOLDER_PID"; then
    printf 'alive\n' > "$R2ROOT/W52-2-r2-holder-alive-after.txt"
else
    printf 'not alive; held-pressure witness invalid; continue after recovery\n' > "$R2ROOT/W52-2-r2-holder-alive-after.txt"
fi
# Snapshot failure must not cancel the independent free/CPU observations.
if ! nvidia-smi --id=0 --query-gpu=memory.free,memory.used --format=csv,noheader,nounits > "$R2ROOT/W52-2-r2-held-end.csv"; then
    printf 'held-end nvidia-smi unavailable\n' > "$R2ROOT/W52-2-r2-held-end-unavailable.txt"
fi
release_holder
# Refuse the free-card run unless device-wide used recovers within 30 s.
if ! uv run python - > "$R2ROOT/W52-2-r2-recovery.log" 2>&1 <<'PY'
import json, math, os, subprocess, time
from pathlib import Path
root = Path(os.environ['R2ROOT'])
before = float((root / 'W52-2-r2-before.csv').read_text().strip().split(',')[1])
deadline = time.monotonic() + 30
samples = []
reason = 'device-wide used did not recover within 100 MiB in 30 s'
while time.monotonic() < deadline:
    try:
        reading = subprocess.run(
            ['nvidia-smi', '--id=0', '--query-gpu=memory.free,memory.used',
             '--format=csv,noheader,nounits'], capture_output=True, text=True,
            check=True, timeout=max(0.01, deadline-time.monotonic()))
        free, used = map(float, reading.stdout.strip().split(','))
        assert math.isfinite(free) and math.isfinite(used)
        samples.append(dict(free_mib=free, used_mib=used))
        if time.monotonic() <= deadline and used <= before + 100:
            (root / 'W52-2-r2-after.csv').write_text(reading.stdout, encoding='ascii')
            reason = None
            break
    except (OSError, ValueError, AssertionError, subprocess.SubprocessError) as error:
        samples.append(dict(error=type(error).__name__))
    time.sleep(min(0.2, max(0, deadline-time.monotonic())))
result = dict(before_used_mib=before, tolerance_mib=100, timeout_s=30,
              samples=samples, recovered=reason is None, refusal_reason=reason)
(root / 'W52-2-r2-recovery.json').write_text(json.dumps(result, indent=2), encoding='ascii')
print(json.dumps(result))
raise SystemExit(0 if reason is None else 2)
PY
then
    printf 'REFUSED free-card export: recovery not proved; see recovery.json\n' > "$R2ROOT/W52-2-r2-free-refused.txt"
    exit 2
fi
run_export free
run_export cpu --force-cpu

uv run python - > "$R2ROOT/W52-2-r2-compare.log" 2>&1 <<'PY'
import json, os, subprocess, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, 'tools')
from clearwater.io.video import find_tool, probe
from clearwater.color import decode_filter
root = Path(os.environ['R2ROOT'])
def comparison():
    exits = {label: int((root / f'W52-2-r2-{label}.exit').read_text().strip())
             for label in ('free', 'cpu')}
    failed = [dict(leg=label, exit_status=status,
                   reason=f'{label} export exited {status}; no completed output to compare')
              for label, status in exits.items() if status != 0]
    if failed:
        return dict(window='W52-2', frames=30, cpu_gpu=None, held_free=None,
                    passes=False, skipped=True, failed_legs=failed,
                    skip_reason='; '.join(item['reason'] for item in failed))
    records = {label: json.loads((root / f'W52-2-r2-{label}.json').read_text())
               for label in ('free', 'cpu')}
    for label, record in records.items():
        assert (root / f'W52-2-r2-{label}.exit').read_text().strip() == '0'
        assert len(record['items']) == 1 and not record['cancelled']
        assert record['items'][0]['state'] in ('done', 'done with warnings')
        assert len(record['items'][0]['outputs']) == 1
    assert records['free']['items'][0]['device'] == 'GPU'
    assert records['cpu']['items'][0]['device'] == 'CPU: forced'
    labels = ['free', 'cpu']
    held_status = int((root / 'W52-2-r2-held.exit').read_text().strip())
    held_reason = None
    held_skip = None
    if held_status == 0:
        records['held'] = json.loads((root / 'W52-2-r2-held.json').read_text())
        held = records['held']
        assert len(held['items']) == 1 and not held['cancelled']
        assert held['items'][0]['state'] in ('done', 'done with warnings')
        assert len(held['items'][0]['outputs']) == 1
        held_reason = held['items'][0]['device']
        if held_reason == 'GPU':
            labels.append('held')
        else:
            held_skip = f'held route was {held_reason}; GPU identity comparison inapplicable'
    else:
        held_skip = f'held export exited {held_status}; no completed output to compare'
    held_gpu = 'held' in labels
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
                  held_exit=held_status, held_device_reason=held_reason, held_skip_reason=held_skip,
                  skipped=False, passes=(cpu_gpu['postencode_characterisation_passes']
                          and (held_free is None or held_free['identical'])))
    return result
try:
    result = comparison()
except Exception as error:
    result = dict(window='W52-2', frames=30, cpu_gpu=None, held_free=None,
                  passes=False, skipped=True,
                  skip_reason=f'comparison unavailable: {type(error).__name__}: {error}')
with (root / 'W52-2-r2-compare.json').open('x', encoding='ascii') as dst:
    dst.write(json.dumps(result, indent=2))
print(json.dumps(result))
raise SystemExit(0 if result['passes'] else 1)
PY
```

Record each exit, shell `time` wall and runner/item `elapsed_s`, route,
settings and frames. Free should read `GPU`, forced CPU `CPU: forced`.
Successful exports require 681 frames/completed output. Failed held output
is retained as an observation, without cancelling the independent pair.

Comparison retains literal AD-11 max **2e-3** / mean **2e-4** unit bounds,
and reports strict numeric misses. Encoded outputs do not prove pre-encode
AD-11: the separate allowed post-encode characterisation is mean **3.5/255**,
explicitly labelled. Held/free GPU decoded identity has no tolerance. Failed
comparisons follow the later-window retry/STOP policy; no bounds are tuned.

`headless_export.py` has no `--keep` flag: retain these three dedicated
outputs until comparison/read-back, then delete exactly their recorded output
MP4s. Keep every JSON, CSV, exit/liveness receipt, holder lines, log and raw
comparison sample. No other cleanup is authorised.

**Window estimates (planning, not measurements).** W52-1 remains R1 alone,
about 115 min. W52-2: held GPU about 3.6-3.8 min + free GPU 3.6-3.8 min +
forced CPU provisionally 20 min + R3 generator/two photo legs about 10 min =
37-38 min, budget **40-45 min** with copy, holder, condition snapshots and
comparisons. If held also chooses CPU at the provisional CPU rate, budget
**55-60 min** instead. Record actual walls; failures/retries are additional.
No timed leg is run by this cell. No heavy work beside WP-DR113's reviewer.

**R3 / W52-2: ONE self-contained script.** Disk floor: **25 GB**;
the adapter needs 20,292,626,432 B at 8064x6048 RGB16, leaving
4,707,373,568 B (about 4.71 GB) margin before generation. Configuration/root
is checked independently. Disk/generator/measurement each have an exit
receipt beside the photo record folders, with unique attempt prefixes.
Generation failure writes a measurement-skipped receipt and never launches
the adapter. The PNG uses a fixed same-folder `.tmp` name; existing final
or temporary files refuse with their exact path named. A temporary is never
silently reused or deleted. Publish the final name only after closing the
complete write and checking file size and RGB16 IHDR dimensions. No full-size
input is created by the cell; all of this runs at the EXCLUSIVE seat.

```bash
set -euo pipefail
unset PYTEST_ADDOPTS
WORK52=$(uv run python - <<'PY'
import sys
sys.path.insert(0, 'tools')
from local_config import load_local_config
from spike_io.guard import WriteGuard
cfg = load_local_config()
working = cfg.working_path.resolve()
root = working / 'wp5.2'
assert root.resolve() == root and root.is_relative_to(working)
guard = WriteGuard(root, cfg.footage_path)
guard.folder('W52-2')
guard.folder('photo')
print(root.as_posix())
PY
)
: "${WORK52:?}"
export WORK52
# Receipt files sit beside the adapter's per-leg record folders.
R3ROOT="$WORK52/photo"
ATTEMPT52="$(date -u +%Y%m%dT%H%M%SZ)-$$"
R3RECEIPT="$R3ROOT/W52-2-r3-$ATTEMPT52"
export R3RECEIPT
if uv run python - > "$R3RECEIPT-disk.log" 2>&1 <<'PY'
import os, shutil
from pathlib import Path
root = Path(os.environ['WORK52'])
free = shutil.disk_usage(root).free
need = 20_000_000_000 + 8064 * 6048 * 6
print('disk_free_bytes', free, 'adapter_need_bytes', need,
      'required', 25_000_000_000, 'margin_bytes', 25_000_000_000 - need)
raise SystemExit(0 if free >= 25_000_000_000 else 2)
PY
then DISK_STATUS=0; else DISK_STATUS=$?; fi
printf '%s\n' "$DISK_STATUS" > "$R3RECEIPT-disk.exit"
if [ "$DISK_STATUS" -ne 0 ]; then exit "$DISK_STATUS"; fi
if uv run python - > "$R3RECEIPT-generate48.log" 2>&1 <<'PY'
import os, sys
from pathlib import Path
sys.path.insert(0, 'tools')
from fixtures.stills import unit_content, quantize, png16_bytes, srgb_profile
from local_config import load_local_config
from spike_io.guard import WriteGuard
cfg = load_local_config()
guard = WriteGuard(cfg.working_path.resolve() / 'wp5.2', cfg.footage_path)
output = Path(os.environ['WORK52']) / 'W52-2/W52-2-synthetic-48mp.png'
temporary = output.with_name(output.name + '.tmp')
guard.check(output)
guard.check(temporary)
if output.exists():
    raise FileExistsError(f'REFUSED existing final PNG: {output}')
if temporary.exists():
    raise FileExistsError(f'REFUSED leftover temporary PNG: {temporary}; never reused')
pixels = quantize(unit_content('lowred', width=8064, height=6048), 16)
payload = png16_bytes(pixels, srgb_profile(), 'sRGB')
with guard.check(temporary).open('xb') as dst:
    dst.write(payload)
    dst.flush()
    os.fsync(dst.fileno())
with temporary.open('rb') as src:
    header = src.read(29)
assert len(header) == 29 and header[:8] == b'\x89PNG\r\n\x1a\n'
assert header[12:16] == b'IHDR'
assert int.from_bytes(header[16:20], 'big') == 8064
assert int.from_bytes(header[20:24], 'big') == 6048
assert header[24:26] == b'\x10\x02'
assert temporary.stat().st_size == len(payload)
if output.exists():
    raise FileExistsError(f'REFUSED existing final PNG before rename: {output}')
guard.check(temporary).rename(guard.check(output))
print(output.name, '8064x6048', 'RGB16', 'seeded lowred', 'no EXIF',
      'complete temporary write and IHDR read-back before rename')
PY
then GENERATOR_STATUS=0; else GENERATOR_STATUS=$?; fi
printf '%s\n' "$GENERATOR_STATUS" > "$R3RECEIPT-generate48.exit"
if [ "$GENERATOR_STATUS" -ne 0 ]; then
    printf 'SKIPPED: generator exited %s; input was not measured\n' "$GENERATOR_STATUS" > "$R3RECEIPT-measure-skipped.txt"
    exit "$GENERATOR_STATUS"
fi
if uv run python tools/photo_memory.py measure "$WORK52/W52-2/W52-2-synthetic-48mp.png" --name W52-2 --exclusive > "$R3RECEIPT-photo-memory.log" 2>&1; then
    MEASURE_STATUS=0
else
    MEASURE_STATUS=$?
fi
printf '%s\n' "$MEASURE_STATUS" > "$R3RECEIPT-photo-memory.exit"
exit "$MEASURE_STATUS"
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
Depth: **179,121** (session 2 retirement, dispatcher-supplied). Turn-2 depth is
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
with the 25 GB W52-1 / 30 GB W52-2 disk floors, clocks/temperature/strays and no other heavy work
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
| Session 2 / turn 3 (ruling implementation; not Reviewer A) | 0 / 1 / 1 | 2 in / 0 out | 2 / 0 | 0 | Test + ledger only; tools/product unchanged | Codex exec; depth 179,121 | WDDM assertion replaced as ruled; 156 light tests passed; hardware at seat; YIELD for Reviewer A round 1 |


### Additional report Limits draft (Reviewer A round 1, F13/F14)

`device_within_limit` is `None` (not a bool) when the device read is unavailable;
the measurement failure and exit status are unchanged. `estimate_fits_free_before`
uses the parent's nvidia-smi view, not the runner's per-process free-memory
figure read by the product (DR-114). Quote `device_reason` from the default
runner record as D111 evidence; that estimate predicate is not such a witness.

## Session 3 / Turn 4: Reviewer A round 1 adjudication

Fresh session 3, dispatch HEAD `26f02528`, branch/worktree `wp5.2`.
Session 2 retired at **179,121**, dispatcher-supplied; its turn-3 depth line
and cumulative row above now carry that figure. Current depth (session 3 / turn 4, at yield, codex_cell footer): **111,385**. Seat checks after the turn: `bash -n` on the R2 script OK (identical to the section-5 block); `tests/test_device_hold.py` 1 passed at the seat.

Status: all fifteen findings dispositioned under the binding turn-4 packet;
light/static checks GREEN. **Validation STOP: the seat must run `bash -n`
on the R2 script before windows.** Recommended next action: run
`bash -n work/wp5.2/tmp/turn4-r2.sh` from this worktree at the unrestricted
seat, then Reviewer A round 2. Git Bash cannot initialise under this cell's
restricted token; the attempted syntax check exited 256 before parsing.
This is not a script syntax verdict. GPU holder execution also remains at
the seat, as expressly ordered; its prior `26f02528` PASS was supplied by
the dispatcher, not repeated or claimed for this changed candidate.

Review source: the one authorised external read,
`C:/Users/rwsmy/clearwater-review-evidence/wp5.2/r1/review.txt`, Reviewer A
Claude opus/high (46 turns), verdict **NEW_CRITICAL_MAJOR_FOUND**. No reviewer
or agent was launched by this cell. Scope/rulings/locks remain unchanged.

### Per-finding adjudication and changes

All findings are IN envelope and NEW; none REOPENED, rejected, reverted or
banked outside scope. The review's individual tags total **2 MAJOR, 6 MINOR,
7 ADVISORY**. The dispatch header says **2 MAJOR, 7 MINOR, 6 ADVISORY**;
that tally discrepancy is retained here explicitly, without dropping an ID
or changing a per-finding tag. Both have 15 total and 2 blocking findings.

| Finding / severity | Disposition and independent confirmation | Changed mechanic / surface |
|---|---|---|
| F1 MAJOR | FIXED. Old section 5 needed shell state from four separate blocks; an EXIT trap could release the holder before export. | Section 5 R2 at `docs/proofs/wp5.2-ledger.md:283` is ONE self-contained fenced script, saved/run by the seat as ONE `bash <file>`. It computes/asserts WORK52 and configured-root containment, creates a unique attempt directory and stop file, and owns its EXIT trap. R1/R3 blocks carry WORK52 guards. |
| F2 MAJOR | FIXED. Traced the old held-status assertion and unconditional held-record validation; either could cancel the independent pair. | R2 `run_export` captures statuses inside `if`, always proceeds from a held outcome through recovery to free/cpu, and reads held output only on exit 0. Comparison records the skip reason otherwise; free/cpu are the independent mandatory pair. Held route is not asserted CPU or held exit 0. |
| F3 MINOR | KEPT stop as ruled; FIXED description. Actual `memory_check` with `peak_gpu_memory_used_mib: None` yields failed device check. | `tools/export_bench.py:51` and `:895` distinguish a breach from an unmeasured device peak; `tests/test_export_bench_breach.py:39` plants the actual computed check. R1 seat instructions at ledger `:274` require reading the stopped record's `memory_check` on exit 3. No change inside `memory_check`. |
| F4 MINOR | FIXED. RED reproduced missing top-level `failed` on simultaneous job/memory failure. | Bench `:892` writes exactly the exit-1 `failed` shape before returning 3; test `tests/test_export_bench_breach.py:57` reads the written JSON and checks the full literal entry. Exit 3 keeps precedence and stops subsequent calls. |
| F5 MINOR | KEPT behaviour; DOCUMENTED both commands. | Bench module `:51` explicitly names `v16` and `run`; test `tests/test_export_bench_breach.py:74` requires one recorded call and exit 3 for a three-run request. |
| F6 MINOR | FIXED. Independently traced `photo_verify._disk_check`'s real 20 GB plus budget requirement and adapter catch returning 1 inside a leg. | `tests/test_photo_memory.py:71` stubs only the disk seam; `:196` plants an OutputRefusedError, asserts exit 1/no runner/no record. `tools/photo_memory.py:7` and `:145` document inside-leg refusal as 1, pre-measure refusal as 2. Product/adapter behaviour is retained. |
| F7 MINOR | FIXED as ruled; hardware result PENDING. | `tests/test_device_hold.py:80` documents and permits device-wide recovery <= baseline + 100 MiB. Rise >=200 MiB, own drop >=256 MiB and stop exit <2 s stay intact. |
| F8 MINOR | FIXED with F1. Old recovery requirement was only a comment. | R2 polls nvidia-smi used to <= baseline + 100 MiB, with 30 s total deadline and bounded subprocess timeout; writes samples/result/refusal reason, and refuses free export when recovery is unproved. |
| F9 ADVISORY | ADOPTED. RED reproduced AttributeError on a null check. | Bench `:891` uses `(run.get("memory_check") or {})`; passing/absent/null controls continue the full plan in test `:25`. |
| F10 ADVISORY | ADOPTED; hardware result PENDING. | `tools/device_hold.py:83` flushes a closing `stopped` JSON before finally/release; module `:7` documents stop-file/timeout. `tests/test_device_hold.py:85` requires the second line to be `stop-file` on its normal path. |
| F11 ADVISORY | ADOPTED with F1. | R2 holder timeout is 900 s; trap stops/reaps on shell exit. Uncatchable kill remains a stated limit. |
| F12 ADVISORY | ADOPTED with F1. | R2 self-check refuses free disk below 30,000,000,000 B before stream copy/holder; section 5 and later window summary now distinguish W52-1 25 GB from W52-2 30 GB. |
| F13 ADVISORY | NO code change, as ruled; DISCLOSED. | Additional report Limits draft above records `device_within_limit=None` on unavailable device read and unchanged failure/exit status. |
| F14 ADVISORY | NO code change, as ruled; DISCLOSED. | Same Limits draft distinguishes parent nvidia-smi fit predicate from runner admission input (DR-114), and requires `device_reason` as D111 evidence. |
| F15 ADVISORY | ADOPTED. Old location test did not isolate nested footage. | `tests/test_photo_memory.py:212` configures footage INSIDE working/wp5.2, places a valid PNG16 inside it, and requires the specific footage refusal with no measurement folder. No real footage/config folder read. |

Section 5 is the executable seat request of record. Its local syntax-check
copy is `work/wp5.2/tmp/turn4-r2.sh`, not committed and NEVER executed here.
R2 records now live below `work/wp5.2/W52-2/attempt-<UTC>-<pid>/`, retaining
required W52-2-r2-held/free/cpu names and every failed attempt. R3 still
uses its existing W52-2 paths; its synthetic-input/admission witness is
unchanged. W52-2 remains 40-45 min provisionally, or 55-60 min if held also
selects CPU; these are historical planning estimates, not measurements.

### Validation and verification-loop record

All logs are below this worktree's ignored `work/wp5.2/turn4/`.
Every pytest invocation used `PYTHONPATH=scripts`, unset `PYTEST_ADDOPTS`,
both `-p sandbox_mkdir_shim -p no:cacheprovider`, fresh basetemp below
`work/wp5.2/tmp/`, and
`-m "not gpu and not footage and not gui and not slow and not fullclip"`.

- RED `red.log`: **3 failed, 22 passed in 1.22 s**, exit 1. Failures were
  the intended null-check AttributeError, missing unmeasured-stop explanation,
  and missing persisted `failed` key. New `run`/refusal/footage controls passed
  existing behaviour; no false RED is claimed for those compatibility rows.
- GREEN `light.log`: `test_export_bench_breach.py`, `test_photo_memory.py`,
  existing `test_export_bench.py`: **40 passed in 64.29 s**, exit 0. No skips,
  failures or errors. Holder GPU module was NOT invoked. No full-suite gate.
- `ruff.log`: full `uv run ruff check .`, **All checks passed!**, exit 0.
  `format.log`: full `uv run ruff format --check .`, **311 files already
  formatted**, exit 0. `mypy.log`: full `uv run mypy`, **Success: no issues
  found in 156 source files**, exit 0. The inherited MAIN VIRTUAL_ENV warning
  states uv ignored it; no active-environment override was used.
- `bash-n.log`: attempted `bash -n work/wp5.2/tmp/turn4-r2.sh`, exit **256**:
  `fatal error - CreateFileMapping ... Win32 error 5. Terminating.` Bash never
  reached parsing. No permission escalation or script execution attempted.
- `audit.log`: **7 changed owned paths, ASCII, zero CR; 8 embedded Python
  bodies syntax-valid without execution; extracted R2 matches section 5;
  git diff --check clean**, exit 0. This does not substitute for bash syntax
  validation or runtime seat execution.

Verification loop: suspected/independently confirmed F1/F2 via old shell
state/exit paths; confirmed F3/F4/F9 with the distinguishing RED; traced
F5/F6/F15 against the actual CLI/catch/guard paths and kept compatibility
controls; implemented the explicit F7/F8/F10-F12 operational constraints;
disclosed F13/F14 without changing recorded semantics. Rejected as false
positive: none. Final source/record/recipe pass found no further issue in
the authorised envelope. Bash parsing and hardware remain explicitly unproved.

Only three tools, three test modules and this ledger changed. No product
module, frozen interface, fixture, dependency, local config or brief changed.
No GPU test, timed leg, run request, full-size generation, EXCLUSIVE window,
footage-folder read, MAIN-work read, other-worktree read, mailbox post, commit
or git write occurred. No footage-derived or GPS/IMU bytes were added. All
cell writes stayed in this worktree, including ignored work logs/check files.
One logical round-1 remediation turn bundles the ordered tool/test/request
fixes. Full package acceptance/report/measurements remain pending.

### Cumulative Reviewer A round ledger

Earlier build/ruling turns above are not counted Reviewer A rounds.

| Round | Critical / major / minor / advisory | Envelope | NEW / REOPENED | Reverts | Fix surface | Transport / depth | Outcome |
|---|---|---|---|---|---|---|---|
| A1, session 3 / turn 4 | 0 / 2 / 6 / 7 per-ID review tags (dispatch header 0 / 2 / 7 / 6) | 15 in / 0 out | 15 / 0 | 0 | Tools + tests + run-request text; product code 0; not test-only | Claude opus/high via dispatcher; Codex exec remediation; depth 111,385 | All IDs dispositioned; 40 light tests/static checks GREEN; bash -n blocked by sandbox startup, seat check required; YIELD for A2 |

## Session 3 / Turn 5: Reviewer A round 2 terminating clean-up

Resumed session 3, turn-4 commit `959083eb`. Depth after turn 4:
**111,385**, dispatcher-supplied and already recorded above. Current depth:
**142,196** (session 3 / turn 5, at yield, codex_cell footer). Seat checks: `bash -n` OK on all three scripts, each identical to its section-5 block.

Status: **Reviewer A CONVERGED at round 2; terminating clean-up complete.**
The dispatcher supplied the seat's successful `bash -n` on turn 4's R2
script (identical to section 5 at that commit), and **1 passed** for
`tests/test_device_hold.py` at the seat. Those resolve turn 4's validation
STOP; they are seat evidence, not executions by this cell. This turn changes
only the ledger's live section-5 requests and adds this adjudication record.
No tool, test or brief changed. No pytest or run request was executed.

Review source: the one authorised external read,
`C:/Users/rwsmy/clearwater-review-evidence/wp5.2/r2/review.txt`, Claude
opus/high, 38 turns, verdict **NO_NEW_CRITICAL_MAJOR** on `959083eb`.
The reviewer re-checked round-1 F1/F2/F4/F6 as closed and found the tools
sound on every claim. Its **2 MINOR + 4 ADVISORY** findings are all in the
run requests or ruled design, all IN envelope. No new blocking finding;
the six dispositions below do not open another review round.

### Findings and section-5 changes

| Finding / severity | Disposition and confirmed mechanism | Live ledger lines |
|---|---|---|
| 1 MINOR: holder expires before the held-run contingency | FIXED as ruled. Replace 900 s with `--timeout-s 3600`, matching the binding turn-5 packet and original R2 figure. Unique stop path, EXIT cleanup and pre/post liveness receipts remain. This supersedes round-1 F11's 900 s choice; the bounded held export below now ends at 2400 s. | R2 prose/script, `docs/proofs/wp5.2-ledger.md:374-690`; timeout at `:491`. |
| 2 MINOR: R1/R3 inherit WORK52; R3 continues after failed generation | FIXED. Deleted shared setup, replacing it with an invocation pointer. R1 and R3 each compute/assert WORK52 and configured-root containment within ONE `set -euo pipefail` script, run by the seat as ONE `bash <file>`. Each captures disk and operation exits beside its records with unique attempt prefixes. R1 captures the bench status immediately, reads its exact printed RECORD path, records the stopped check/idle on 3, renames byte-preserving with W52-1 prefix, and records pre/post SHA256. R3 launches measurement ONLY after generator exit 0; failure gets an explicit skipped receipt. | Pointer `:256-259`; R1 `:261-372`; R3 `:716-830`. |
| 3 ADVISORY: interrupted generation leaves a partial final PNG | ADOPTED. Generator writes the same-folder `.png.tmp` with exclusive creation, closes/flushed-syncs it, checks total byte count and RGB16 IHDR dimensions, then renames to final. Existing final refuses; a leftover temporary refuses with its exact name and is never reused/deleted. A generator failure cannot launch measurement. | R3 script `:729-815`. |
| 4 ADVISORY: held export is unbounded | ADOPTED. Only the held leg gets Bash array prefix `timeout 2400`; free/cpu keep their commands. Status 124 is written by the same export-status receipt path and remains an observation, never gating the independent pair. | R2 `run_export`, `:524-537`; prose `:386-389`. |
| 5 ADVISORY: failed free/cpu exit prevents compare.json | ADOPTED. Read both exit receipts before export JSON. If either failed, return a skipped comparison listing each failed leg, its exit status and reason, without opening incomplete/missing runner records. The outer comparison wrapper also records other comparison exceptions, and the shared final write emits compare.json with failure status. Successful comparisons keep literal AD-11 and post-encode bounds, plus the existing held skip rules. | R2 comparison `:593-688`. |
| 6 ADVISORY: device-wide peak contains other processes | NO change, by ruled design. Peak remains device-wide, idle stated rather than subtracted. R1's exit-3 receipt quotes `memory_check`, `idle_before_mib` and `device_peak_mib`; it never infers that all observed use belongs to this export. | R1 record receipt `:328-338`; existing bench unchanged. |

Disk floors: R1 **25 GB**; R2/window opening **30 GB**; R3 rechecks
**25 GB** before generation. At 8064x6048 RGB16 the adapter's current
minimum is 20,000,000,000 + 8064*6048*6 = **20,292,626,432 B**.
The R3 floor supplies **4,707,373,568 B**, about **4.71 GB**, above that
minimum before generation; it does not relax the adapter's own later check.
All paths still derive from configuration, and every seat record/output
stays below configured work/wp5.2. No new deletion grant is introduced.

### Seat syntax-check handoff and checks

Three exact fenced-script copies are ready in THIS worktree for the
dispatcher's `bash -n` checks (not run here):

- `work/wp5.2/tmp/turn5-r1.sh`: R1 block at ledger `:272-371`, 100 lines.
- `work/wp5.2/tmp/turn5-r2.sh`: R2 block at ledger `:404-689`, 286 lines.
- `work/wp5.2/tmp/turn5-r3.sh`: R3 block at ledger `:729-815`, 87 lines.

Each copy is byte-identical to its section-5 body including the final LF,
ASCII and zero CR; none is committed. The seat saves/runs each as one
script invocation from its repo root. This cell did not retry Git Bash:
its startup failure under this restricted token is already established.
Pending seat syntax checks on these revised copies are distinct from the
successful check on turn 4's superseded R2 body. No new STOP or ruling is
requested; the planned windows follow after WP-DR113 acceptance and the
seat's script checks.

Light/formal checks, logs under this worktree's `work/wp5.2/turn5/`:

- `ruff.log`: `uv run ruff check .`, **All checks passed!**, exit 0.
- `format.log`: `uv run ruff format --check .`, **311 files already
  formatted**, exit 0. No source Python changed or formatter mutation ran.
- `audit.log`: only `docs/proofs/wp5.2-ledger.md` changed; ledger and all
  three extracted scripts ASCII/zero CR; exact script-byte identity;
  **13 embedded Python bodies parsed without execution**; `git diff --check`
  clean, exit 0. This is a syntax-only Python audit, not Bash/runtime proof.

Verification/adjudication record: confirmed findings 1/2 against the prior
900 s setting, shared-setup references and missing R3 branch; replaced the
live instructions as ordered. Adopted 3/4/5 with staged write/explicit
timeout/record-before-reading-failed-outputs controls. Kept 6 by the ruled
measurement scope. Rejected as false positive: none. No unrequested
behaviour, tolerance, product, tool, test or brief change. Reverts: **1
ruled request-setting reversal**, 900 -> 3600 s; no code reversion.

No pytest, GPU holder, Bash syntax-check process, run-request script,
full-size generation, timed leg, reviewer, EXCLUSIVE window, footage-folder
read, MAIN-work read, other-worktree read, mailbox post, commit or git write
occurred in this turn. Cell writes are only this ledger and ignored
worktree-local helper/check/log/script files. No footage-derived material,
GPS/IMU bytes, dependency or local-config change. Measurements/report and
the final gate remain with the dispatched later stages.

| Round | Critical / major / minor / advisory | Envelope | NEW / REOPENED | Reverts | Fix surface | Transport / depth | Outcome |
|---|---|---|---|---|---|---|---|
| A2, session 3 / turn 5 | 0 / 0 / 2 / 4 | 6 in / 0 out | 6 / 0 | 1 ruled timeout-setting reversal | Ledger request text only; product/tool/test code 0 | Claude opus/high via dispatcher; Codex exec terminating clean-up; depth 142,196 | NO_NEW_CRITICAL_MAJOR; CONVERGED; all findings dispositioned; three exact scripts staged for seat bash -n; YIELD |


## Session 3 / Turn 6: W52-1 read-back

Resumed session 3, HEAD `d3fadaea`, rebased onto main `6ff6f5d3` after
WP-DR113 acceptance. The dispatcher reports all seven package patch-ids
unchanged by rebase. Prior turn-5 depth: **142,196**, dispatcher-supplied;
current depth (session 3 / turn 6, at yield, codex_cell footer): **194,184** (past the ~200K evaluation point next turn; session 3 retires here and the W52-2 read-back goes to a fresh session 4).

Status: **W52-1 request/receipt/record checks PASS**, eight runs retained in
their original order. This is the seat-run record read-back, not a new run.
No report file is written before W52-2. No N6 recommendation or cause of
the timing difference is inferred. Reviewer A remains converged at round 2.

### Evidence and request identity

Read grant used only for JSON/exit receipts inside
`C:/Users/rwsmy/clearwater/work/wp5.2/v16/W52-1/`, read-only. No synthetic
MP4, run cache, footage folder or other MAIN-work path was opened. The
orchestrator reports W52-1 **2026-11-02 12:48:16Z -> 14:55:15Z**, about
127 min, script exit 0, run from this worktree at `d3fadaea`; the saved
script was byte-identical to section 5. Its save path is dispatcher evidence,
not opened by this cell.

Every table below is **W52-1**. Alias **R** = `W52-1-export-bench-v16-20261102T124817Z.json` in the granted folder;
**r[i]** = `R.runs[i]`, zero-based. Alias **P** =
`W52-1-20261102T124816Z-1856-record.json` beside R. All WP5.2 numeric measurements below come from
R, not a log or the orchestrator notes. Calculated unit conversions, ratios
and percentages are labelled; displayed values are rounded, raw JSON is
the record of record.

Computed SHA256(R) = **`e93f060399e73bb7416cce4f045557b8c0b0cb8be053686036b2d4f4a12c0495`**,
equal to both `P.sha256_before` and `P.sha256_after`. `P.record` names R;
`P.run_count=8`, `P.bench_exit=0`, `P.record_step_exit=0`; the disk, bench
and record `.exit` receipts all read 0. Therefore the byte-preserving
W52-1 rename and receipt chain agree with the actual record bytes.

Read `tools/export_bench.py:144-150` V16_PLAN as AST data, without importing
or executing it. `R.plan` equals those six legs; expanded `r[i].leg` order
is cold x3, warm, ancuti2018, libx265, synthetic 5.3K, sustained LAST.
Every row has `ok=true`, `failure=null`, `memory_check.passes=true`,
`memory_check.device_ok=true`, `memory_check.pool_ok=true`, `device=GPU`,
`force_cpu=false`, `device_frames=true`; top-level `R.device_frames=true`.
Every `device_backend` is the cuda:0 CuPy backend. Resolved `encoder` is
hevc_nvenc except r[5] libx265; Standard/8-bit, full source frame counts
681 / 150 synthetic / 14,938 sustained are checked, and only r[3] starts
with complete cache. No cold row was discarded. D106 arithmetic checked
from `wall_s / frames * frame_rate`; frame rate is `30000/1001` on all rows.

### V16 table of record: WP3.21 -> WP5.2

Exact WP3.21 column set retained. Each numeric pair is published WP3.21
after-optimisation -> W52-1 shipped-build result. The supplemental OFF row
was not part of V16_PLAN and is not added. Baseline rows are
`docs/reports/wp3.21-optimisation.md:232-240` (specific lines below);
warm/pool state and the prior 5.3K/sustained caveats remain at `:250-257`.

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

Column key paths: `r[i].total.s_per_frame`; `r[i].total.min_per_min`;
`r[i].per_frame.{median,p90,max}` (the separately reported first frame is
excluded); `100*r[i].analysis_share_overlapped`;
`r[i].telemetry.peak_tree_rss_bytes / 1048576`;
`r[i].telemetry.peak_gpu_memory_used_mib`. Lead+stall means
`(lead_s + record_wait_s)/wall_s`, independently checked per row, and is
not whole-analysis runtime or the legacy lead-only `analysis_share`.

### Wall, analysis and encoder evidence (W52-1)

| Row | wall_s | legacy analysis_share % | lead_s + record_wait_s | analysis_end_s | encoder; nvenc_proof.tied; PID; samples; active PID rows; window_s |
|---|---|---|---|---|---|
| r[0] | 267.581480 | 9.0065 | 24.099828 + 0.193506 | 210.217561 | hevc_nvenc; true; 38528; 2413; 338; 241.56 |
| r[1] | 244.673201 | 2.6824 | 6.563171 + 12.861951 | 223.115413 | hevc_nvenc; true; 33236; 2313; 354; 236.49 |
| r[2] | 247.427106 | 2.7892 | 6.901276 + 13.475433 | 225.701699 | hevc_nvenc; true; 29452; 2278; 354; 238.53 |
| r[3] | 219.013079 | 0.7965 | 1.744497 + 0.114497 | 122.733931 | hevc_nvenc; true; 4692; 1806; 337; 215.80 |
| r[4] | 226.295916 | 6.5699 | 14.867507 + 20.332149 | 199.947185 | hevc_nvenc; true; 14608; 2021; 307; 209.55 |
| r[5] | 464.529558 | 1.4262 | 6.625220 + 1.692403 | 268.882034 | libx265; false; not an NVENC encode (libx265) |
| r[6] | 201.860550 | 7.4200 | 14.977981 + 0.016778 | 42.318292 | hevc_nvenc; true; 29524; 1621; 99; 179.73 |
| r[7] | 5372.593214 | 0.1198 | 6.434622 + 265.305190 | 5284.375990 | hevc_nvenc; true; 42024; 49955; 7579; 5362.08 |

Keys are `r[i].wall_s`, `100*r[i].analysis_share`, `r[i].lead_s`,
`r[i].record_wait_s`, `r[i].analysis_end_s`, `r[i].encoder`,
`r[i].nvenc_proof.{tied,pid,samples,window_s,reason}` and length of
`r[i].nvenc_proof.pid_samples_with_encoder_load`. The seven NVENC rows
have positive PID-tied encoder-load observations; libx265 is explicitly
not an NVENC encode and is characterisation, not the N6 target.

### GPU memory controls and estimate margins (W52-1)

| Row | device peak / job limit MiB | job estimate / device peak | pool peak / pool limit MiB | pool estimate / pool peak | idle_before_mib |
|---|---|---|---|---|---|
| r[0] | 3,613.0 / 4,065.4 | 1.125215x | 1,510.8 / 2,173.8 | 1.438840x | 662.0 |
| r[1] | 3,669.0 / 4,065.4 | 1.108040x | 1,566.2 / 2,173.8 | 1.387945x | 712.0 |
| r[2] | 3,575.0 / 4,065.4 | 1.137175x | 1,470.5 / 2,173.8 | 1.478273x | 712.0 |
| r[3] | 2,984.0 / 3,582.0 | 1.200402x | 1,342.5 / 2,173.8 | 1.619218x | 736.0 |
| r[4] | 3,505.0 / 4,065.4 | 1.159886x | 1,392.2 / 2,173.8 | 1.561414x | 712.0 |
| r[5] | 3,068.0 / 3,412.7 | 1.112353x | 1,414.5 / 2,173.8 | 1.536797x | 724.0 |
| r[6] | 7,085.0 / 10,330.8 | 1.458123x | 3,993.8 / 6,281.4 | 1.572788x | 712.0 |
| r[7] | 3,638.0 / 4,065.4 | 1.117482x | 1,523.3 / 2,173.8 | 1.427033x | 716.0 |

All fields are under `r[i].memory_check`: `device_peak_mib`,
`job_estimate_mib`, `pool_peak_mib`, `pool_estimate_mib`, `idle_before_mib`.
Each ratio divides the stated estimate by its matching peak; the recorded
estimate/peak values are already rounded by the instrument. The device
peak equals `telemetry.peak_gpu_memory_used_mib` on every row. These job
and pool limits are different estimates, not the base admission estimate or
the physical card capacity. No base admission estimate or device-total
capacity field is carried by these runs; an admission/peak ratio cannot be
claimed from them. All reported job/device and pool/pool ratios are below
2x. The estimates are conservative by design; no estimate was tuned.
At 5.3K the recorded `memory_check.note` makes the pool bound binding and
records the device-wide job check separately. Its historical 4,427 MiB
example is not this run's peak and is not substituted for the current row.

### Conditions present in R, separate from seat observations (W52-1)

| Row | recorded non-own run strays (CPU as recorded) | before -> after temperature C | sampled SM MHz range | sampled memory MHz range | sampled temperature C range | sampled GPU utilisation % range |
|---|---|---|---|---|---|---|
| r[0] | WmiPrvSE.exe pid 10304: 70.4 | 60 -> 72 | 210-2475 | 405-8001 | 59-83 | 0-100 |
| r[1] | WmiPrvSE.exe pid 10304: 66.4; System pid 4: 26.0 | 71 -> 74 | 210-2460 | 405-8001 | 71-87 | 0-100 |
| r[2] | WmiPrvSE.exe pid 10304: 69.3; System pid 4: 26.5 | 73 -> 75 | 210-2460 | 405-8001 | 72-87 | 0-100 |
| r[3] | WmiPrvSE.exe pid 10304: 59.7 | 66 -> 74 | 210-2460 | 405-8001 | 65-86 | 0-100 |
| r[4] | WmiPrvSE.exe pid 10304: 71.2; System pid 4: 33.1 | 73 -> 74 | 210-2460 | 405-8001 | 72-89 | 0-100 |
| r[5] | WmiPrvSE.exe pid 10304: 76.6; MoUsoCoreWorker.exe pid 32600: 44.4 (new, alive_s=7.81); System pid 4: 39.0 | 74 -> 67 | 210-2460 | 405-8001 | 68-86 | 0-99 |
| r[6] | WmiPrvSE.exe pid 10304: 55.7; System pid 4: 26.6 | 65 -> 73 | 210-2475 | 405-8001 | 65-83 | 0-100 |
| r[7] | WmiPrvSE.exe pid 10304: 70.2; System pid 4: 31.1 | 71 -> 75 | 210-2460 | 405-8001 | 70-93 | 0-100 |

Stray keys: `r[i].strays.busy[*].{name,pid,cpu,own,new,alive_s}`; only
`own=false` entries are displayed above. Own=true python.exe pid 39500 is
also recorded, with per-row CPU values 118.9, 118.0, 118.5, 111.3, 119.6, 95.8, 105.3, 123.0.
CPU values are the instrument's process readings, not an attribution of
whole-machine CPU load. Conditions use `before.gpu.temperature.gpu`,
`after.gpu.temperature.gpu`, and min/max of numeric
`telemetry.gpu[*].{clocks.sm,clocks.mem,temperature.gpu,utilization.gpu}`.
The record also carries before/after UTC, CPU snapshots, memory.used,
power.draw and clocks_event_reasons.active; flag bit meanings are not
decoded here and no throttling cause is asserted.

Endpoint stray samples can differ from whole-run entries: the synthetic
row also has before `svchost.exe` pid 31644 CPU 141.0 and WmiPrvSE 95.8,
and after svchost CPU 39.7 (`r[6].before/after.strays.busy`). WmiPrvSE
is present in whole-run observations on every row, System in r[1,2,4,5,6,7],
and a new MoUsoCoreWorker in r[5]. These are recorded conditions; their
contribution to wall time is not isolated. The record does not establish
a causal shipped-code regression, an uncontaminated exclusive host, or
absence of quiet/unreported applications; no controlled temperature/load
A/B is present. Photos, CPU fallback and GUI-path timing are not measured
by R. Peak sampling is not a continuous allocation maximum.

| Row | RSS samples | max RSS gap s | GPU samples | max GPU gap s | telemetry errors |
|---|---|---|---|---|---|
| r[0] | 1078 | 0.426 | 270 | 1.053 | [] |
| r[1] | 988 | 0.371 | 247 | 1.047 | [] |
| r[2] | 998 | 0.398 | 250 | 1.066 | [] |
| r[3] | 884 | 0.353 | 221 | 1.037 | [] |
| r[4] | 914 | 0.365 | 229 | 1.087 | [] |
| r[5] | 1865 | 0.308 | 467 | 1.069 | [] |
| r[6] | 816 | 0.274 | 204 | 1.026 | [] |
| r[7] | 21499 | 0.450 | 5375 | 1.184 | [] |

Keys: `telemetry.rss_samples`, `telemetry.gaps_s.memory.max`, length of
`telemetry.gpu`, `telemetry.gaps_s.gpu.max`, `telemetry.errors`, all per row.
Nominal `telemetry.periods_s` is memory 0.25 s / GPU 1.0 s on every row;
observed gaps above qualify the sampled peaks.

### N6 facts for CHARC (no recommendation)

WP3.21 comparisons use its published rounded figures, so percentage
deltas are approximate `(WP5.2 / WP3.21 - 1)*100`. Cold median is the
median of all three cold `total.min_per_min` values, with no exclusion;
the corresponding s/frame and wall medians are from the same row r[2].

| Quantity | WP3.21 min/min | W52-1 min/min | Delta | WP5.2 key / baseline line |
|---|---|---|---|---|
| GX011627 c3 cold median | 9.78 | 10.888983519 | +11.3393 % | median r[0:3].total.min_per_min; WP3.21 :232-234 |
| GX011625 sustained | 9.58 | 10.779005197 | +12.5157 % | r[7].total.min_per_min; WP3.21 :240 |
| GX011627 warm | 9.06 | 9.638514754 | +6.3854 % | r[3].total.min_per_min; WP3.21 :235 |
| GX011627 ancuti2018 | 8.74 | 9.959024077 | +13.9476 % | r[4].total.min_per_min; WP3.21 :236 |

One sentence of fact for CHARC: W52-1 on `d3fadaea` measured the full-clip
4K c3 NVENC cold median at **10.888984 min/min**, the sustained row at
**10.779005 min/min**, and synthetic 5.3K best effort at
**40.331778 min/min**, with all eight recorded memory checks passing.
The owner retains the N6 decision; the interim D106 target is not reset here.

### V15 video half / DR-70 share read-back

Synthetic 5.3K 8:7, r[6], `size=[4648,5312]`, `frames=150`:
`telemetry.peak_tree_rss_bytes` = **5,599,490,048 B**
(**5,340.089844 MiB**, about 5.599490 GB decimal),
below N4's 16 GB RAM requirement. The device-wide peak is
**7,085 MiB**; `memory_check.job_estimate_mib` =
**10,330.8 MiB**, ratio **1.458123x**.
Pool peak **3,993.8 MiB** / pool estimate **6,281.4 MiB**,
estimate/peak **1.572788x**; idle **712.0 MiB**.
Base admission estimate is NOT carried; its ratio to device peak is N/A,
rather than relabelling a job/pool estimate. Prior WP3.21 row is
`docs/reports/wp3.21-optimisation.md:239`: 7,753 MiB RSS / 7,901 MiB device;
current values are sampled peaks with the cadence/errors table above.

DR-70: sustained `analysis_end_s=5284.375990` against
`wall_s=5372.593214` (derived 98.3580 % of wall),
`record_wait_s=265.305190`, `lead_s=6.434622`,
`analysis_share_overlapped=5.0579 %`.
The legacy `analysis_share` is only lead/wall. WP3.21's comparable
sustained lead+stall share is 5.75 % (`:240`), and its analysis return is
4,690.6 s / frame 14,655 of 14,938 (`:274-276`). The current record places
the analysis return near export end; this does not by itself apportion
CPU/GPU time or prove a cause for the timing delta. No pipeline tuning.

### Orchestrator seat observations (separate provenance)

The following are the orchestrator's supplied readings, NOT substitutions
for any R table cell. Open 12:48Z: C: 84 GB free; GPU SM/memory 210 /
405 MHz, 59 C, 7,404 MiB free / 545 MiB used; free RAM 12.7 GB; CPU about
9 %. Strays: Brave, Battle.net, PianoMarvel, OktaVerify, QNAPRaidMgr, two
Claude sessions; no pytest, Codex turn or reviewer pass. Mid-GX011625 at
14:19Z / 14:50Z: GPU utilisation 65 % / 74 %, SM 1,470 / 1,830 MHz,
88 C / 85 C. Close 14:55Z: C: 84 GB free; GPU SM/memory 210 / 405 MHz,
70 C, 7,413 MiB free / 536 MiB used; free RAM 12.7 GB; strays as at open.
These window snapshots differ in time and scope from per-run R.before,
R.after and telemetry samples, and are not merged with them.

### Checks, verification record and handoff

All identity/hash/ordering/encoder/ok/memory and rate-arithmetic checks
above executed in this cell's read-only read-back helper; log and numeric
extraction are under this worktree's ignored `work/wp5.2/turn6/`. No
request mismatch found, no STOP, no result discarded. Verification loop:
confirmed hashes against actual bytes and receipts; independently expanded
the source plan; checked rate/share arithmetic and matching memory scopes;
kept the missing admission/device-capacity fields explicit. No cause claim
or product defect inferred. False positives/fixes/reverts this turn: none.
Formal checks: `work/wp5.2/turn6/ruff.log`, full `uv run ruff check .`,
**All checks passed!**, exit 0; `format.log`, full `uv run ruff format
--check .`, **311 files already formatted**, exit 0. `audit.log` verifies
the ledger is ASCII/zero CR, the ledger is the sole changed tracked path,
and `git diff --check` is clean, exit 0. No pytest, GPU allocation, timing or run-request execution;
no report/source/test/brief/config/fixture/dependency change. Only this
ledger and ignored worktree-local helper/log files are written; all granted
MAIN-work files remain untouched. No media/GPS/IMU payload is copied.
YIELD for the orchestrator's W52-2 window; report follows its read-back.
