# WP-DR25 -- Staged smoothing on long excerpts

The 2 s `median_gaussian` leaves less staged flicker than 1 s on both
20 s excerpts and both methods, using each candidate's own edge-free interior.
The reductions are **23.24% / 10.23% for c3** and **13.52% / 8.07% for
ancuti2018**, in GX011627 / GX011625 order. Thus the direction of WP1.4's
ground 2 holds here, but its "about a fifth" margin is not reproduced on
both chapters, including for the shipped default c3. AD-3's status remains
CHARC's ruling at acceptance; this report changes no decision or default.

## 1. Scope and durable evidence

This is the DR-25 (3) remeasurement of
[WP1.4 section 4](wp1.4-statistics.md#4-result-smoothing-candidates-141-temporal-smoothing-filter-type-and-default-window),
under spec 7.2 / D95, AD-3 and D98. The instrument uses the read-only
prototype, with two-stage c3 and three-stage Ancuti (blue compensation off).
WP1.4's smoothing-window study and ground-2 figures were **Ancuti-only**;
this package supplies the c3 window evidence needed for the shipped default.
It does not reevaluate visual equivalence under D98 or V3.

All new measured figures below come exclusively from the successful second
analysis's durable copies:

```text
C:\Users\rwsmy\clearwater-review-evidence\wp-dr25\runs2\
  GX011627-long\
  GX011625-long\
    excerpt.json
    results.json
    statistics-raw.json
    statistics-staged.json
    statistics-flat.json
    flicker.png
  cdr25-analyse-long-2.log
  dr25-runs.txt
```

The successful analysis ran on `68caf100`. The two `results.json` SHA-256s,
in GX011627 / GX011625 order, are:

```text
cfd5bb8cc029eb103095d130a974b2715870e5b173f9ebfab7745d83493617d6
9905a812ab91f4d35596ab81a53efdde9a8f15423fa33c88461b4805ea14c845
```

The report audit read these files without modifying them; before/after
SHA-256s agree for all 14 files in `runs2`. The earlier directory
`C:\Users\rwsmy\clearwater-review-evidence\wp-dr25\runs\` is superseded
and is cited only for the failed first analysis, never for reported levels.

## 2. Excerpts and timing

Both excerpts request 20.0 s, skip full-frame statistics and clip rendering,
and contain the original 6 s frame sets. Sources are the configured footage
folder's `Snorkel\GX011627.mp4` and `Snorkel\GX011625.mp4`, found by chapter
stem. Both recorded duration sources are **stream**. The actual clamp is
`min(fraction * stream_duration_s, stream_duration_s - 20.0)`.

| Excerpt | Stream duration (s) | Start fraction | Requested start (s) | Actual start (s) | Frames | First / last PTS ticks | First / last PTS (s) |
|---|---:|---:|---:|---:|---:|---|---|
| GX011627-long | 22.722700 | 0.30 | 6.816810 | 2.722700 | 599 | 82082 / 680680 | 2.736066667 / 22.689333333 |
| GX011625-long | 498.431267 | 0.50 | 249.2156335 | 249.2156335 | 599 | 7477470 / 8076068 | 249.249000000 / 269.202266667 |

The stored frame rate is `30000/1001`, time base `1/30000`, and every tick
step is 1001 in both excerpts and all saved statistics series, including
the staged measurements. The selected interval is 20 s; first-to-last
sample time is 598 * 1001 / 30000 = 19.953266667 s. The earlier report
rounded GX011625's chapter duration to 498.43 s; this run records its
probed 498.431267 s. All color tags are recorded, with no assumptions:
`yuvj420p`, full range (`pc`), BT.709 matrix, primaries and transfer.
The records name the backend `gpu`.

## 3. Interior accounting and read-only audit

For `median_gaussian` at 1 / 2 / 4 s, the single-filter radii are
15 / 30 / 60 frames (Gaussian 14 / 29 / 59, plus the median's one frame).
`staged_reach` multiplies by two for c3 and three for Ancuti; flat uses
one radius. The following are each candidate record's own `reach_frames`,
`edge_free_frames`, `edge_free_steps` and `interior_steps`; both excerpts
have the same counts because both have N=599.

| Analysis | Method | Window (s) | Reach per end | Edge-free frames | Edge-free steps | Step slice [start, stop) |
|---|---|---:|---:|---:|---:|---|
| staged | c3 | 1 | 30 | 539 | 538 | [30, 568) |
| staged | c3 | 2 | 60 | 479 | 478 | [60, 538) |
| staged | c3 | 4 | 120 | 359 | 358 | [120, 478) |
| staged | ancuti2018 | 1 | 45 | 509 | 508 | [45, 553) |
| staged | ancuti2018 | 2 | 90 | 419 | 418 | [90, 508) |
| staged | ancuti2018 | 4 | 180 | 239 | 238 | [180, 418) |
| flat | both | 1 | 15 | 569 | 568 | [15, 583) |
| flat | both | 2 | 30 | 539 | 538 | [30, 568) |
| flat | both | 4 | 60 | 479 | 478 | [60, 538) |

This follows CHARC's chosen instrument convention: frames
`[reach, N-reach)`, steps `[reach, N-1-reach)`. Counts are N-2*reach frames
and N-1-2*reach steps. Both 2 s staged interiors exceed the required 182
frames; even the 4 s Ancuti interior has 239 frames.
WP3.11 instead requires the support endpoints to be strictly inside the
span (`first > 0 and last < N-1`); applied to these full spans, that
convention would remove two more frames and two more steps from every
nonempty row. The tables use the ruled instrument convention throughout.

The top-level `interior_margin_frames=60` and `interior_steps=[60,538]`
apply **only to `flicker`**, whose staged/flat comparison uses Gaussian
1 s. They do not define the `smoothing` candidates' interiors. Likewise,
`statistics-staged.json` and `statistics-flat.json` store that Gaussian
1 s comparison, not the 1 / 2 / 4 s median-Gaussian window study.
The latter's auditable per-step arrays are in `results.json.smoothing`.

Scratch audit: `work/cdr25-6-audit.py` in this worktree, with output
`work/cdr25-6-audit.log` (neither committed). It reads only `runs2` and
uses the following arithmetic for every candidate:

```python
candidate = results["smoothing"][method][label][analysis]
a, b = candidate["interior_steps"]
measured = fmean(candidate["per_step"][a:b])
unsmoothed = fmean(results["flicker"][method]["unsmoothed"]["per_step"][a:b])
percent_drop = 100 * (1 - staged_2s["interior"] / staged_1s["interior"])
```

The measured mean must match the saved `interior` to absolute/relative
tolerance 1e-12. Every candidate's `all` is also checked against its
whole per-step mean. The same checks cover available top-level flicker
rows on their own top-level slice. Coverage: both methods, all 12 windows/
filters per method, both analyses, both excerpts; tick alignment and
ordered saved N{} bounds are checked too. No method/window is missing.
Only the two permitted trend rows are unavailable (section 8).
Observed output:

```text
AUDIT_PASS sequence_records 110 max_mean_abs_error 2.7755575615628914e-17 unchanged_files 14
```

## 4. Flicker levels and the WP1.4 figures

All levels are the instrument's mean residual frame-step change in 8-bit
levels: average of `|(s[t+1]-s[t])-(r[t+1]-r[t])|` over R, G, B and
BT.709 luma means. The reference renders the same proxies with constant
statistics equal to the method's raw-series mean. This cancels content
change to first order; it also counts wanted drift and is not V3.

Each staged and flat value below is its record's **own** `interior`.
`U staged` and `U flat` re-trim the unsmoothed per-step array to that
particular row's staged or flat slice. Thus each baseline is matched to
its candidate; the staged and flat columns themselves use different
step sets and their difference alone does not measure a staging effect.
Values are rounded to six decimals; calculations use saved precision.

| Chapter | Method | Window (s) | Staged interior | U staged | Flat interior | U flat |
|---|---|---:|---:|---:|---:|---:|
| GX011627 | c3 | 1 | 0.032020 | 0.090123 | 0.033492 | 0.093437 |
| GX011627 | c3 | 2 | 0.024577 | 0.087773 | 0.024193 | 0.090123 |
| GX011627 | c3 | 4 | 0.017416 | 0.084947 | 0.020670 | 0.087773 |
| GX011627 | ancuti2018 | 1 | 0.117788 | 0.192658 | 0.113303 | 0.190124 |
| GX011627 | ancuti2018 | 2 | 0.101864 | 0.202042 | 0.098132 | 0.189961 |
| GX011627 | ancuti2018 | 4 | 0.076408 | 0.193988 | 0.083023 | 0.195390 |
| GX011625 | c3 | 1 | 0.073744 | 0.217423 | 0.073262 | 0.214707 |
| GX011625 | c3 | 2 | 0.066203 | 0.225169 | 0.063329 | 0.217423 |
| GX011625 | c3 | 4 | 0.063482 | 0.240926 | 0.056350 | 0.225169 |
| GX011625 | ancuti2018 | 1 | 0.109015 | 0.259512 | 0.102279 | 0.250799 |
| GX011625 | ancuti2018 | 2 | 0.100218 | 0.278640 | 0.086784 | 0.254514 |
| GX011625 | ancuti2018 | 4 | 0.092226 | 0.266393 | 0.077566 | 0.265306 |

For orientation only, the long **whole-span** unsmoothed levels are
0.095348 / 0.212627 (c3, GX011627 / GX011625), and 0.190295 / 0.247387
(Ancuti). They are not substituted for the matched baselines above.

Beside these long-run results, WP1.4 section 4 reported these 6 s
`median_gaussian` values for **Ancuti only**:

| Chapter | Window (s) | Old staged, all steps | Old flat, all steps | Old staged, fixed-60 interior |
|---|---:|---:|---:|---:|
| GX011627 | 1 | 0.133 | 0.129 | 0.185 |
| GX011627 | 2 | 0.106 | 0.101 | 0.169 (boundary-influenced) |
| GX011627 | 4 | 0.081 | 0.080 | 0.142 (boundary-influenced) |
| GX011625 | 1 | 0.067 | 0.064 | 0.049 |
| GX011625 | 2 | 0.053 | 0.050 | 0.037 (boundary-influenced) |
| GX011625 | 4 | 0.042 | 0.041 | 0.031 (boundary-influenced) |

Its Ancuti unsmoothed all / fixed-60 interior levels were 0.236 / 0.261
and 0.151 / 0.127. Its ground-2 erratum gives the **flat edge-free**
2 s comparison as 0.168 / 0.036 versus 1 s 0.183 / 0.048 (8% / 25% less).
These historical rounded figures retain the old report's step sets and
references; they are not additional long-run measurements. No historical
c3 window study exists to populate corresponding c3 2 s or 4 s cells.

## 5. Ground-2 reading

The primary comparison uses each staged row's own interior, as commissioned:

| Method | Chapter | 1 s staged | 2 s staged | Drop (levels) | Drop from 1 s (%) |
|---|---|---:|---:|---:|---:|
| c3 | GX011627 | 0.032020 | 0.024577 | 0.007443 | 23.24 |
| c3 | GX011625 | 0.073744 | 0.066203 | 0.007541 | 10.23 |
| ancuti2018 | GX011627 | 0.117788 | 0.101864 | 0.015924 | 13.52 |
| ancuti2018 | GX011625 | 0.109015 | 0.100218 | 0.008797 | 8.07 |

These step sets shrink as the window grows. As a like-for-like control,
re-trimming the 1 s staged per-step array to the **2 s staged interior**
gives 1 s levels 0.032603 / 0.077469 for c3 and 0.119878 / 0.119530 for
Ancuti. Relative to those values, the same 2 s levels are lower by
24.62% / 14.54% and 15.03% / 16.16%, respectively. Both comparisons
therefore favor 2 s on these excerpts; neither reproduces an approximately
20% reduction uniformly. In particular the new c3 evidence supports the
direction, with a smaller second-chapter gap than the original claim.
CHARC determines what this means for AD-3 at acceptance.

The 4 s own-interior levels are lower again in all four cases (section 4),
but use shorter interiors. This report makes no responsiveness/default
tradeoff decision and does not rerun WP1.4's filter-response experiment.

## 6. Boundary exposure of the original 6 s figures

The old Ancuti 2 s reach is 90 frames per end, so the old 180 / 179-frame
excerpts have **zero edge-free staged 2 s steps**. That boundary exposure
is established; the following re-trims assess its apparent size without
conflating the new whole-interior population with the old frames.

**Reference qualification:** the long runs render references with the
20 s mean statistics, whereas WP1.4 used the 6 s mean. Re-trimming long
arrays to old PTS gives a closely comparable figure, not the identical
quantity, and cannot isolate a pure boundary-bias effect.

All slices below index the **long** Ancuti `median_gaussian 2 s` per-step
array. A step at i joins long frames i and i+1. Old PTS endpoints are
205205..384384 for GX011627 and 7477470..7655648 for GX011625.

| Chapter / subset | Long step slice | Steps | Long staged 2 s | Matched long unsmoothed | Old reported staged 2 s | Edge-free under long reach? |
|---|---|---:|---:|---:|---:|---|
| GX011627, all old frames | [123,302) | 179 | 0.108547 | 0.237573 | 0.106 | Yes |
| GX011627, old fixed-60 interior | [183,242) | 59 | 0.169025 | 0.262119 | 0.169 | Yes |
| GX011625, all old frames | [0,178) | 178 | 0.052638 | 0.145096 | 0.053 | No, first 90 steps remain exposed |
| GX011625, old span intersect long interior | [90,178) | 88 | 0.074361 | 0.183692 | No matching old subset reported | Yes |
| GX011625, old fixed-60 interior | [60,118) | 58 | 0.037349 | 0.119567 | 0.037 | No, first 30 steps remain exposed |
| GX011625, old interior intersect long interior | [90,118) | 28 | 0.050864 | 0.131307 | No matching old subset reported | Yes |

GX011627's now edge-free old-span value is close to the old 0.106;
its old fixed-60 interior agrees at the old report's three-decimal
precision. This provides no evidence of a large boundary shift there,
subject to the reference qualification. GX011625's all-old-span value
also stays near 0.053, but its start was not moved, so that comparison
still includes the original left boundary. Its edge-free intersection
has a higher level (0.074361), on a different population of steps.
The records therefore do not establish the isolated sign or magnitude
of boundary bias in 0.106 / 0.053, or prove it absent. They do supply
the fully edge-free staged window comparisons that WP1.4 lacked.

## 7. Commands and resources

The dispatcher ran these commands from this worktree using its local
configuration (default device `gpu`). No explicit footage/output path
override, render phase or extraction rerun was used:

```text
uv run python tools/statistics_experiments.py extract --long
uv run python tools/statistics_experiments.py analyse --long
uv run python tools/statistics_experiments.py analyse --long
```

The second and third lines are the first failed and second successful
analysis attempts, respectively. These resources are the dispatcher's
records, not timings measured by this report cell:

| Phase / head | UTC on 2026-11-03 | Exit / elapsed | C: free before -> after | Outcome |
|---|---|---|---|---|
| extract | 08:42:48-08:56:01 | 0 / recorded 791 s | 82 -> 72 GB | Both excerpts; 7.1 GB kept |
| first analyse / `45bca4db` | ended 09:42:25 | 2 / elapsed not supplied | 72 GB after extract -> 71 GB at failure | GX011625 auxiliary linear fit crossed; superseded |
| second analyse / `68caf100` | 10:49:48-12:14:08 | 0 / logged 5,056 s | 59 -> 64 GB | Both excerpts complete; R1 unavailable rows recorded |

`runs2\dr25-runs.txt` records the exits/disk snapshots;
`runs2\cdr25-analyse-long-2.log` ends with `elapsed 5056 s` and both
completed excerpt paths. The extract elapsed, initial 82 GB free and
7.1 GB retained are supplied in the dispatch. Logged process elapsed
need not equal the enclosing launch/exit timestamp interval.
The failed analysis and its independent diagnosis are recorded in
[the ledger, turn 4](../proofs/wp-dr25-ledger.md#turn-4----gx011625-long-analyse-failure).
No source footage was written; output routing uses the local
configuration and the instrument's checked output roots.

## 8. Limits and deep-step context

- Two chapters, both snorkel footage. These results do not characterize
  deep footage, other frame rates, VFR, visual preference, or V3. Means
  miss local shimmer and retain some content-change residue and wanted
  drift. The prototype's index kernels are used on these CFR samples;
  this is not a new test of the product's PTS-based smoother.
- **Under-20 s chapters are out of envelope.** The long-spec clamp would
  produce a negative start for a chapter shorter than 20 s. Both
  commissioned chapters exceed 20 s; no general short-chapter support
  is claimed or added.
- **GX011625's `linear_trend` is UNAVAILABLE for both methods.** Each
  record says `fitted normalisation_bounds.low exceeds normalisation_bounds.high`
  and lists 57 crossing frames, zero-based indices 542..598. The first
  is frame 542, ticks 8020012, PTS 267.3337333333333 s. Fitted low/high
  there are -0.0010472760167360845 / -0.0012093584930396722 (c3), and
  -0.0010379406363364915 / -0.0011621024076525072 (Ancuti). As CHARC
  ruled: **the crossing is a property of fitting the two N{} bounds
  independently over a 20 s excerpt whose spread narrows; not a product
  defect (the product never fits a trend; no measured, staged or flat
  pair crosses; the refusal is the prototype's `check_statistics`).**
  The whole method's trend diagnostic is unavailable, without a numeric
  level; it is not repaired by clipping, sorting or dropping frames.
  The staged/flat window figures remain available. GX011627's trend
  rows are available; no other unavailable row occurs in either record.
- The changed 20 s reference and the different per-window interiors
  constrain historical and cross-window interpretation (sections 5-6).
  Flat/staged own-interior values alone are not a new D98 equivalence
  measurement. No full-resolution clips or CP2 visual comparison were
  produced in this package.

The separate deep-step evidence is
[WP3.11's step-aware design task](wp3.11-analysis.md#step-aware-design-task-ad-3-question-6)
and `tools/step_aware_eval.py`; neither was rerun here. It used GX011600,
a 359-frame / 11.95 s span: the original 6 s excerpt from 662.031 s
widened by 3 s on each side, with results on the original 179 frames.
The step was at excerpt frame 27, PTS 662.962 s. Under WP3.11's strict
endpoint convention, `median_gaussian` had 179/179 edge-free target
frames for c3 (reach 60), and 177/179 for Ancuti (reach 90).
Both step-aware kinds had zero edge-free frames because their global
noise scale reads the entire span. Their flicker figures and uint8
FFmpeg-resized proxies are separate evidence, not pooled with this run's
float32 NumPy area-average proxies.

## 9. Verification and acceptance transfer

This report turn changes only this report and the owned ledger. The
instrument/test changes through turn 5 remain at `68caf100`: long routing,
start/source records, method/reach-specific studies and the ruled R1
diagnostic; synthetic controls pin default records to the WP1.4 base.
No product/prototype code, frozen interface, dependency, smoother/default
decision or WP1.4 report is changed. This cell performed no GPU phase,
footage write, main-tree working-folder write, mailbox post or git commit.
Scratch scripts/logs/temp files stay under this worktree's ignored `work/`.

Light checks run on this report turn, each exit 0:

| Check | Observed summary | Worktree log |
|---|---|---|
| New synthetic module | `22 passed in 4.53s` | `work/cdr25-6-green.log` |
| Ruff, whole tree | `All checks passed!` | `work/cdr25-6-ruff.log` |
| Format, whole tree | `312 files already formatted` | `work/cdr25-6-format.log` |
| Configured mypy scope | `Success: no issues found in 156 source files` | `work/cdr25-6-mypy.log` |

Exact cell commands (PowerShell, all runner output redirected):

```powershell
$env:PYTHONPATH='scripts'
$env:PYTHONDONTWRITEBYTECODE='1'
Remove-Item Env:VIRTUAL_ENV -ErrorAction SilentlyContinue
uv run python work/cdr25-6-audit.py > work/cdr25-6-audit.log 2>&1
uv run pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_tools_statistics_experiments.py --timeout 120 --basetemp=work/cdr25-6-green > work/cdr25-6-green.log 2>&1
uv run ruff check . > work/cdr25-6-ruff.log 2>&1
uv run ruff format --check . > work/cdr25-6-format.log 2>&1
uv run mypy > work/cdr25-6-mypy.log 2>&1
```

Verification loop: suspected wrong interiors/missing methods were rejected
by the independent re-trim, counts and tick checks; the anticipated trend
exception was confirmed exactly as ruled; unequal comparison step sets
were addressed with matched unsmoothed baselines and the common-2 s-slice
control; attributing a historical difference solely to boundaries was
rejected because references and, for GX011625, populations differ.
The final report pass found no additional in-envelope instrument defect.
No implementation change or STOP was needed.

The final scratch document check (`work/cdr25-6-report-check.py`, output
`work/cdr25-6-report-check.log`, exit 0) reconciled 31 long-run table rows
with the durable records, confirmed both owned files are ASCII/LF, checked
local link targets and the two-file scope, and ran `git diff --check`
successfully. Git's prospective LF-to-CRLF warning concerns its configured
future checkout behavior; the audited files on disk contain no CR bytes.

Reviewer A round 2 is dispatcher-reported **CONVERGED** (0 critical,
0 major, 1 minor, 3 advisory); its F1/F3 test cleanup and R1 were fixed
in turn 5, and the carried F2/F4, A1 F4/F8 and resource obligations are
covered here. This is not a fresh review pass. Importers were not rerun
because no code changed. Reviewer B, the parallel/serial gate (including
the two named instrument importers), harness gate and collection identity
remain at the dispatcher's seat; no full-gate pass is claimed here.
The DR-25 (3) register note, AD-3 ruling and one-line WP1.4 erratum pointer
are CHARC's acceptance actions and remain outside this cell's ownership.
