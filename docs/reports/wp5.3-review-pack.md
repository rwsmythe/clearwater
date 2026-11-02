# WP5.3: CP5 visual review pack build report

**2026-11-02; NOT OWNER-READY.** The pack accounts for all **128** commissioned
items: **117 done, 9 failed V-P items, 2 expected HLG refusals, pending 0**.
The nine failures are the **OPEN product defect DR-112** (PCM audio with
irregular packet sizes, as routed by the dispatcher), assigned to **WP-D112**.
This package does not repair or work around the product. CP5 waits for
WP-D112's merge, a successful `clips V-P` rerun, then `page`, `page --check`
and `tally`, with **pending 0 AND failed 0**, before owner handoff. The current
`page` exit is **1**, link-only `page --check` is **0**, and `tally` is **0**.
These facts come from the turn-19 publication read-back and its receipts.

**No agent judged any image.** Preference, above-surface classification,
artifacts, preset changes and the CP5 decision belong to the owner. All owner
answer cells remain blank. The report records build/accounting evidence only.

## Evidence and location

The real pack is **`work/wp5.3/`** in the configured main working folder.
Open **index.html** there; keep its companion files together. **review-sheet.csv**
is the owner sheet, **README.md** explains viewing/recovery limits, and
**pack.json** is the saved state of record. Product outputs use
`<stem>_corrected.png` or `<stem>_corrected.mp4`; photo source views use
`<stem>_neutral.png`. Pages, sheet and this report use file names only.

Evidence labels below disambiguate identically named receipts without exposing
machine paths. The ledger is **wp5.3-ledger.md**.

| Label | Evidence |
|---|---|
| R32 | Generation-32 summary.txt and the completed photos.log, presets.log, page.log, page-build.log, page-check.log, tally-1.log and clips-V-P.log receipts |
| R33 | Generation-33 summary.txt and clips-V-S.log, clips-V-D.log, clips-V-Z.log, clips-V-R.log, page.log, page_check.log and tally.log receipts |
| L13 | Ledger, Session 5 / Turn 13: photo, preset and initial publication read-back |
| L14 | Ledger, Session 6 / Turn 14: V-P results and exact failure strings |
| L15 | Ledger, Session 6 / Turn 15: V-S rerun, interruption/recovery and excerpt timing table |
| L16 | Ledger, Session 6 / Turn 16: V-D results and excerpt timing table |
| L17 | Ledger, Session 6 / Turn 17: V-Z results and excerpt timing table |
| L18 | Ledger, Session 6 / Turn 18: V-R expected refusals |
| L19 | Ledger, Session 6 / Turn 19: final publication, links, empty tally and readiness |
| P | Read-only pack.json; P-A.json, P-A-neutral.json, P-Z.json, P-Z-neutral.json, V-P.json, V-S.json, V-D.json, V-Z.json, V-R.json; V-S-excerpts.json, V-D-excerpts.json, V-Z-excerpts.json; index.html, review-sheet.csv and both exported starter JSON files |

This reporting turn reads receipts/records only; it runs no real-pack stage,
opens no footage or owner media, and writes nothing to the real pack. Earlier
read-backs checked record identity, file existence and publication links without
quality judgement. No source-media re-probe or independent pixel-fidelity claim
is added here.

## What ran

The following are historical RUN REQUEST receipts, **not new run requests**.
Commands run from the worktree root and resolve the configured working folder.
Every product correction was driven through **headless_export.py**, in a
subprocess per group/pose, at shipped defaults. The instrument supplies
`--out`, `--suffix`, `--settings-dir` and `--record`; photos also use
`--bit-depth 8`, and source views add `--neutral` with suffix `_neutral`.
Videos use `--cache-dir`. Settings/cache/output destinations are pack-local;
the owner's settings are not used. Product records show provenance enabled,
`force_cpu=false`, method **c3**, video quality **standard** and encoder **auto**.
The recorded photo exports used GPU; successful videos report GPU and
**hevc_nvenc** (L13-L17, P). No CPU override or fallback is inferred.

All elapsed times and free-disk readings below are **informal build receipts,
not figures of record**, benchmarks or acceptance measurements. Preserve the
receipted seconds even where coarse clock stamps differ. `missing` means the
receipt/ledger does not supply that field; no head, time or disk value has been
estimated or carried forward from an adjacent piece. Times are UTC: initial
pieces are on **2026-11-01**, and the rerun/later pieces on **2026-11-02**.
Free-disk values reproduce the ledger's GB readings. Every recorded clips-start
reading exceeds the commissioned **25 GB** prerequisite.

| Piece / exact command | Head | Exit | Informal wall / UTC interval | Free disk before -> after (GB) | Evidence |
|---|---|---:|---|---|---|
| `uv run python -m tools.reviewpack.build photos` | 6d470028 | 0 | 673 s; 22:00:18-22:11:32 | 171 -> 167 | R32, L13 |
| `uv run python -m tools.reviewpack.build presets` | missing | 0 | 1 s; 22:12:15-22:12:16 | missing -> missing | R32, L13 |
| `uv run python -m tools.reviewpack.build page --check` (mistaken initial order) | missing | 2 | 0 s; 22:12:16-22:12:16 | missing -> missing | R32, L13 |
| `uv run python -m tools.reviewpack.build page` (initial actual build) | missing | 2 | 1 s; start 22:12:33, end missing | missing -> missing | R32, L13 |
| `uv run python -m tools.reviewpack.build page --check` (after initial build) | missing | 0 | missing | missing -> missing | R32, L13 |
| T below (initial empty tally) | missing | 0 | missing | missing -> missing | R32, L13; ledger RUN REQUEST table |
| `uv run python -m tools.reviewpack.build clips V-P` | 6d470028 | 1 | 2,961 s; 22:12:54-23:02:14 | 167 -> 165 | R32, L14 |
| `uv run python -m tools.reviewpack.build clips V-S` (lost attempt) | ef7cbf15 | missing; process died | missing; 23:03:35 to about 00:36:53 next day | 165 -> missing | R32, L15 |
| `uv run python -m tools.reviewpack.build clips V-S` (rerun) | 0b04e372 | 0 | 8,740 s; 00:39:08-03:04:48 | 161 -> 155 | R33, L15 |
| `uv run python -m tools.reviewpack.build clips V-D` | 1f8b036a | 0 | 3,162 s; 04:31:56-05:24:38 | 155 -> 152 | R33, L16 |
| `uv run python -m tools.reviewpack.build clips V-Z` | bcc498c1 | 0 | 374 s; 05:28:32-05:34:46 | 152 -> 151 | R33, L17 |
| `uv run python -m tools.reviewpack.build clips V-R` | 6bf8ce99 | 0 | 3 s; 05:37:56-05:37:59 | 151 -> 151 | R33, L18 |
| `uv run python -m tools.reviewpack.build page` (final publication) | 792ee22c | 1 | 2 s; 05:41:16-05:41:18 | missing -> missing | R33, L19 |
| `uv run python -m tools.reviewpack.build page --check` (final links) | 792ee22c | 0 | 1 s; 05:41:18-05:41:19 | missing -> missing | R33, L19 |
| T below (final empty tally) | 792ee22c | 0 | 1 s; 05:41:19-05:41:20 | missing -> missing | R33, L19 |

T is the ledger's exact config-resolved tally request, avoiding any literal
machine path or accidental use of the worktree's scratch sheet:

```text
uv run python -c "import sys; sys.path.insert(0,'tools'); from local_config import load_local_config; from tools.reviewpack.build import main; raise SystemExit(main(['tally',str(load_local_config().working_path/'wp5.3'/'review-sheet.csv')]))"
```

The mistaken first link check found no index.html. The actual initial page
then exited 2 because **55** video items were pending; its subsequent link check
passed. That page/sheet had **73** photo rows and **295** resolving targets.
The initial tally was empty: headline expected **115**, available **64**,
missing **51**; candidates expected **11**, available **9**, missing **2**
(R32, L13). These are historical states, superseded by L19 below.

The V-P receipt names 6d470028; the ledger confirms the instrument unchanged
through ef7cbf15. All V-P inputs were whole, with **IMG_6762.MOV last**.
The first V-S process was lost when the orchestrator pane closed during
**GX011623**; no exit receipt or completed V-S runner/pack result was saved.
The dispatcher moved **33** orphan files to its recovery archive: **20** completed
MP4s, **1** partial, **11** excerpts and the excerpt sidecar. It copied the stale
lock as **stale-reviewpack.lock**, then removed the real stale lock manually.
The successful rerun produced the current V-S results. L15 records **34**
archived files including that copied lock. This cell performed none of that
recovery and did not adopt the orphan media as completed results.

## Current accounting and empty tally

Counts are from P and L13-L19, with the final coverage lines independently
matched to R33's tally.log in L19. Done includes the product's "done with
warnings" results. There are no current failed viewing aids.

| Group | Commissioned | Done / available sheet rows | Failed | Refused | Pending | Headline treatment |
|---|---:|---:|---:|---:|---:|---|
| P-A photos | 64 | 64 | 0 | 0 | 0 | Included |
| P-Z pre-corrected photo candidates | 9 | 9 | 0 | 0 | 0 | Separate candidates |
| V-S Snorkel | 26 | 26 | 0 | 0 | 0 | Included |
| V-D SCUBA | 8 | 8 | 0 | 0 | 0 | Included |
| V-P phone | 17 | 8 | 9 | 0 | 0 | Included; missing coverage remains visible |
| V-Z pre-corrected video candidates | 2 | 2 | 0 | 0 | 0 | Separate candidates |
| V-R HLG | 2 | 0 | 0 | 2 | 0 | Expected refusals; no review rows |
| Total | 128 | 117 | 9 | 2 | 0 | No CP5 handoff yet |

L19 verifies **128** unique page articles and **117** unique sheet rows with
the exact saved source/corrected identities. All owner answers and status flags
are blank. **603** distinct relative targets resolve inside the pack:
**117** corrected products, **73** neutral photo source views, **234** thumbnails,
**44** pair clips, **132** pair stills, the sheet and **2** preset files.
Link success says nothing about preference or completion.

```text
pack pending: 0
headline: 0/0 = 0.0 %  (D65 bar 80 %)
  coverage: expected=115, available=106, missing=9, unjudged=106
candidates: 0/0 = 0.0 %
  coverage: expected=11, available=11, missing=0, unjudged=11
```

Every per-group judged/preferred count, and all halos, banding, color_errors,
shimmer, flicker, above_surface and viewing_aid_failed counts, are **0**
(R33, L19). **106/115 is coverage, not a preference fraction.** Failed products
remain missing from expected coverage; they are not owner "no" votes and do
not authorize a reduced CP5 test set. The valid empty tally exits 0 without
making a visual judgement. Page exits 1 for the recorded failures; exit 2 is
reserved for pending items/presets or sheet conflicts. Link-only `--check`
does not establish readiness.

## Excerpt record

For the commissioned GoPro/candidate videos, inputs of at most **45 s** are
whole; longer inputs plan **30 s** starting at **40 %** of duration. V-P is
whole regardless of length. Excerpts stream-copy video/audio and non-tmcd data;
GoPro tmcd is regenerated under the R1 ruling. Preparation verifies stream
identity, retained packet identity and displayed start/timecode. A failed
excerpt is recorded and skipped with a nonzero piece exit, never silently
replaced by a whole long input. No excerpt failed in the completed builds.

All **18** excerpt records are below, in seconds, from the completed sidecars
and the matching L15-L17 tables. Actual starts/durations are recorded build
facts, not source timestamps newly probed for this report. Do not treat the
planned interval as the actual keyframe-aligned interval.

| Group / source name | Planned start | Actual start | Planned duration | Actual duration | Evidence |
|---|---:|---:|---:|---:|---|
| V-S / GX011603.mp4 | 27.6542932 | 27.027 | 30 | 30.630600 | L15, V-S-excerpts.json |
| V-S / GX011609.mp4 | 27.7877600 | 27.027 | 30 | 30.764067 | L15, V-S-excerpts.json |
| V-S / GX011611.mp4 | 29.8831868 | 29.029 | 30 | 30.864167 | L15, V-S-excerpts.json |
| V-S / GX011612.mp4 | 21.7817600 | 21.021 | 30 | 30.764067 | L15, V-S-excerpts.json |
| V-S / GX011615.mp4 | 19.3526668 | 19.019 | 30 | 29.362667 | L15, V-S-excerpts.json |
| V-S / GX011619.mp4 | 30.1901600 | 30.030 | 30 | 30.163467 | L15, V-S-excerpts.json |
| V-S / GX011621.mp4 | 31.0843868 | 31.031 | 30 | 30.063367 | L15, V-S-excerpts.json |
| V-S / GX011622.mp4 | 22.9829600 | 22.022 | 30 | 30.964267 | L15, V-S-excerpts.json |
| V-S / GX011624.mp4 | 32.9128800 | 32.032 | 30 | 30.897533 | L15, V-S-excerpts.json |
| V-S / GX011625.mp4 | 199.3725068 | 199.199 | 30 | 30.196833 | L15, V-S-excerpts.json |
| V-S / GX011626.mp4 | 98.0312668 | 97.097 | 30 | 30.964267 | L15, V-S-excerpts.json |
| V-D / GX011590.mp4 | 41.2678932 | 41.041 | 30 | 30.230200 | L16, V-D-excerpts.json |
| V-D / GX011591.mp4 | 55.2818932 | 55.055 | 30 | 30.230200 | L16, V-D-excerpts.json |
| V-D / GX011593.mp4 | 222.5823600 | 222.222 | 30 | 30.363667 | L16, V-D-excerpts.json |
| V-D / GX011598.mp4 | 210.1299200 | 209.209 | 30 | 30.930900 | L16, V-D-excerpts.json |
| V-D / GX011600.mp4 | 418.6048532 | 418.418 | 30 | 30.196833 | L16, V-D-excerpts.json |
| V-D / GX011601.mp4 | 188.3748532 | 188.188 | 30 | 30.196833 | L16, V-D-excerpts.json |
| V-Z / compilation-20261010-1080p60.mp4 | 71.971900 | 70.904167 | 30 | 31.131100 | L17, V-Z-excerpts.json |

GX011615's shorter duration is retained as recorded. The compilation's timecode
is null; no GoPro timecode was invented. The other **15 V-S**, **2 V-D** and
**1 V-Z** items are whole (L15-L17). Whole inputs are read in place; no
whole-source copies are made for the pack.

## Product refusals and open failures

Both V-R items are expected **refused** results under spec 5.3, with no media
or sheet rows. The product runner's raw exit is 1, preserved in their rows;
the V-R stage exits 0 because those are the commissioned expected results.
Exact product text from V-R.json, independently read back in L18/L19:

```text
IMG_6704.MOV: This video uses HLG HDR, which Clearwater does not support. Record in standard (SDR) mode instead.
IMG_6772.MOV: This video uses HLG HDR, which Clearwater does not support. Record in standard (SDR) mode instead.
```

The following **nine V-P failures remain OPEN under DR-112**. They have no
completed product or review row and appear under **Not built** with the same
text. This is a product blocker, not an HLG refusal or an instrument retry.
The PCM packet-size association is the dispatcher's diagnosis; the cell did
not open sources to reproduce it. Product strings are verbatim from V-P.json
and agree with L14/L19:

| Item | Product text |
|---|---|
| IMG_6729.MOV | IMG_6729.MOV: The finished video does not match what was written: audio stream 0: packet 119 at 24217/9600 s where the source has 120797/48000 s |
| IMG_6731.MOV | IMG_6731.MOV: The finished video does not match what was written: audio stream 0: 99 packets in the output where 100 of the source's 100 were to be copied |
| IMG_6733.MOV | IMG_6733.MOV: The finished video does not match what was written: audio stream 0: packet 72 at 192/125 s where the source has 18247/12000 s |
| IMG_6735.MOV | IMG_6735.MOV: The finished video does not match what was written: audio stream 0: packet 72 at 192/125 s where the source has 36361/24000 s |
| IMG_6736.MOV | IMG_6736.MOV: The finished video does not match what was written: audio stream 0: packet 119 at 20191/8000 s where the source has 20143/8000 s |
| IMG_6738.MOV | IMG_6738.MOV: The finished video does not match what was written: audio stream 0: 77 packets in the output where 78 of the source's 78 were to be copied |
| IMG_6741.MOV | IMG_6741.MOV: The finished video does not match what was written: audio stream 0: packet 143 at 145277/48000 s where the source has 144989/48000 s |
| IMG_6742.MOV | IMG_6742.MOV: The finished video does not match what was written: audio stream 0: packet 72 at 192/125 s where the source has 6069/4000 s |
| IMG_6760.MOV | IMG_6760.MOV: The finished video does not match what was written: audio stream 0: packet 143 at 36289/12000 s where the source has 36217/12000 s |

After WP-D112 merges, the scheduled plain `clips V-P` command selects all
**17** V-P items, including the **8** current successes; it is not automatic
failed-only resume. Fresh records and collision-numbered outputs preserve
earlier files. A dispatcher-selected manifest can instead name only the
failures, but this report creates none. No output should be adopted by guessed
filename. Rebuild/check/tally must then be read back: the expected successful
state has **126** reviewable rows, headline available **115**, missing **0**,
candidates **11**, and the same **2** expected HLG refusals (L19).

## Starter presets as exported

**Snorkel (shallow).json** and **Scuba (deep).json** were exported through the
product's PresetStore from a pack-local store. Their entire serialized fields
are equal; an empty parameter map means effective method defaults, not absent
correction. Evidence: both exported files, index.html and L13.

| Export field | Snorkel (shallow) | Scuba (deep) |
|---|---|---|
| format_version | 1 | 1 |
| method | c3 | c3 |
| parameters | {} | {} |
| created | 2026-11-01T22:12:16.062509+00:00 | 2026-11-01T22:12:16.062509+00:00 |
| app_version | 0.0.0 | 0.0.0 |

The two page tables show these identical **effective c3 method defaults**;
these are resolved schema values, not extra fields inserted into either export:

| Parameter | Value in both starters |
|---|---:|
| c3_strength | 1.0 |
| white_balance_strength | 1.0 |
| sharpen_strength | 1.0 |
| blend_with_original | 0.0 |
| kappa | 1.0 |
| lambda_ | 0.7 |
| max_white_balance_gain | 3.0 |
| gamma | 1.5 |
| pyramid_min_level_size | 16 |
| c3_kernel_fraction | 0.05 |
| c3_mask_threshold | 0.85 |
| c3_mask_smooth_fraction | 0.01 |
| sharpen_blur_fraction | 0.005 |
| normalisation_low | 0.5 |
| normalisation_high | 99.5 |
| laplacian_fraction | 0.001 |
| saliency_blur_fraction | 0.003 |
| weight_delta | 0.1 |

In v1 both starter presets carry AD-8's defaults, so the corrected items on this page are what both presets produce; at CP5 the owner may change either preset's values (AD-13).

## How the owner uses the pack after recovery

Once the dispatcher confirms the readiness conditions above, open index.html
and compare source on the left with corrected on the right. Photo source views
are the product's neutral exports with the same orientation, ICC handling and
bit depth. Pair clips/stills are viewing aids; the linked corrected product
output remains the item of record. Both halves use the same display orientation.
Pair encoding is **NVENC HEVC, p5/hq, VBR CQ 20, no bitrate target**, as stated
on index.html. Video stills are converted BT.1886 -> sRGB for display; both
halves alike; the player's rendering differs.

Fill review-sheet.csv in a spreadsheet without changing identity columns.
Use exact lowercase `yes`, `no` or `undecided` in preferred; blank means not
judged. All nonblank preferences count as judged, and only `yes` counts as
preferred. For halos, banding, color_errors, shimmer, flicker and above_surface,
use blank or `yes`; add observations in note. Leave viewing_aid_failed as the
instrument's status flag. No above-surface exclusion is inferred automatically.
P-Z and V-Z stay in their own tally, outside the headline set.

Run the config-resolved T command on the filled sheet to obtain group,
headline and candidate counts. Invalid values are errors naming the row.
D65 asks for at least **80 %** preferred with no obvious halos, banding,
colour errors, shimmer or flicker; the tally prints counts without deciding
acceptance. The owner/CHARC records CP5 and any D96 shimmer follow-up.

If a later rebuild changes a pair that already has owner answers, the tool
preserves those answers and reports a sheet conflict rather than transferring
a vote. Follow README.md: blank that row's owner cells to accept the new pair
at the next page build, or restore the earlier output. Do not judge the current
incomplete pack as a reduced test set.

## Limits, review and remaining work

- **R4-5 privacy-parser limit:** an unquoted path with spaces and an unlisted
  extension can retain folder words. The commissioned names are covered; L19
  found no full-path candidates on page/sheet/README. No broader parser claim
  is made, and no GPS or EXIF values are published here.
- **R4-6 display limit:** untagged video still halves can differ in tone because
  the product defaults absent tags while the adapter converts explicit tags.
  Commissioned sources are tagged. Do not generalize the pack to untagged input.
- **B-F5 inventory limit:** a hand-built pack.json missing a catalog row counts
  it as pending without listing that name. Commissioned CLI initialization
  seeds the full catalog; alternate hand-built inventories are unsupported.
- **B-F6 viewing-adapter limit:** pair clips rely on retained source colour
  description and stills on retained excerpt timestamps. A detected adapter
  failure keeps the product link/sheet row, flags viewing_aid_failed and fails
  the piece. Completed records show no such failure; read-backs establish file
  and record identity, not an independent real-media colour/timing proof.
- **Interrupted groups (L15):** a hard kill can leave finished outputs
  unrecorded, a partial and a stale lock. Group results are saved only after
  the runner returns; excerpt sidecars may already exist. There is no automatic
  crash resume/checkpoint adoption. A rerun may repeat expensive work and number
  around surviving files. Recovery requires explicit seat handling, as the
  lost V-S attempt demonstrates; no source or product change is made here.
- **Recovery naming (L15/L19):** the successful V-S rerun reuses **31** archived
  basenames. Basenames alone cannot distinguish archived and current copies.
  L19 found no archived-location reference and every current link resolved
  inside the pack. Zero basename overlap or independent archived-media
  equivalence is not claimed.
- Commands are supported from the worktree root. No invocation guarantee
  from a different current directory is made. Missing receipt fields are named
  in the run table; there is no invented total elapsed time or disk figure.

Reviewer A **converged at round 4** under CHARC's ruling; the executing
Reviewer B returned **NO_NEW_CRITICAL_MAJOR**, with findings closed before the
real builds (ledger review table and turns 10-13). This report does not claim
the final two-leg gate, WP-D112 recovery or CP5 acceptance. Those remain at the
dispatcher/owner seats. No dependency, product, frozen interface or code changes
are part of this reporting turn; only the report and ledger change.

Fresh turn-20 light verification includes the tiny planted headless/FFmpeg
integration, never the real pack. **177 tests passed in 46.24 s**, exit 0;
ruff check passed, format check reported **6 files already formatted**, and
mypy reported no issues in **151 source files**, all exit 0. Evidence is the
worktree's ignored full.log/full.xml, ruff.log, format.log and mypy.log for
turn 20. The mandatory sandbox mkdir shim was retained. These checks do not
close DR-112 or replace the dispatcher's final gate.

## Empty CP5 sheet header

The current instrument adds the governed viewing_aid_failed status column to
the commissioned owner columns. The header below is copied from the current
review-sheet.csv; no answers or sample judgements follow it.

```csv
item,group,kind,source_name,corrected_name,preferred,halos,banding,color_errors,shimmer,flicker,above_surface,note,viewing_aid_failed
```
