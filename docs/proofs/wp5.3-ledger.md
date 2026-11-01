# WP5.3 cumulative ledger

## Dispatch and state

- Package: WP5.3, CP5 visual review pack; Codex implementer lane, STRONG.
- Verified base and current HEAD at round 0: `2050a89a`; initial tracked diff empty.
- Turn 1 is task 1 only. No instrument or test code is written this turn.
- State: **STOP for CHARC's round-0 ruling** on R0-1, R0-2 and R0-3 below.
  The design and run commands below are conditional proposals, not approved departures.
- The dispatcher reported `uv sync` already run at its seat. It was not repeated.
  The planted reproduction ran successfully using `uv run --no-sync python -c ...`.
- No owner file or footage folder was opened. Only repository sources, committed
  fixtures and newly planted worktree files were read. Local configuration was not
  edited. No other worktree was accessed; no commit or mailbox command was run.
- Session ID and depth figures: dispatcher to fill from the turn footer; no estimate.

## Round 0: anchors on 2050a89a

Each row names the mechanic and the surface inspected. Paths here identify repository
code or generated pack artifacts; owner media are identified only by file name.

| Mechanic | Verified anchor | Surface / consequence |
|---|---|---|
| Dispatch build, isolation and return protocol | `docs/dispatch-recipe.md`, sections 0-5 | Read in full; task boundaries yield to the dispatcher. |
| Scope and ambiguity rule | `docs/clearwater-implementation-plan.md:85`, `:89`, `:100` | Only owned files; a brief mismatch needs a ruling before implementation. |
| V2 and D65 | `docs/underwater-correction-spec.md:103`, `:474` | Owner preference and five artifact types; no agent judges pixels. |
| Output contract and HLG refusal | `docs/underwater-correction-spec.md:219`, `:361`, `:371`, `:382` | PNG with ICC, HEVC MP4, orientation, naming and immutable sources. |
| Defaults and starter-preset decision | `docs/decisions.md:17`, `:22` | AD-8 and AD-13; name-only provenance, two value-identical v1 starters. |
| Runner composition and command contract | `tools/headless_export.py:1`, `:17`, `:28` | No Qt; product composition root and batch engine; statuses 0 / 1 / 2. |
| Actual runner parser | `tools/headless_export.py:1184` | Sources; required `--out`; suffix, PNG depth, CPU, method, neutral, settings, record and cache options. |
| Default and neutral parameter sets | `tools/headless_export.py:669`, `:709` | Default method is `c3`; empty map means method defaults; neutral reads each schema parameter's neutral value. |
| Runner main and invocation ordering | `tools/headless_export.py:1311`, `:1368` | Write checks precede settings and exports; video requires cache; batch records even failed items. |
| Record schema and serialization | `tools/headless_export.py:48`, `:1024` | Schema 1; top-level tool, app_version, method, parameters_from, settings, counts, cancelled, elapsed_s, items. |
| Item record and settings fields | `tools/headless_export.py:1046`, `:1095` | Item index, source name, kind, state, output names, warnings, failure, device, elapsed_s, video facts; settings omit folder and last parameters. |
| Record reuse restriction | `tools/headless_export.py:38`, `:1413` | An existing record is refused; reruns must use fresh record names and read actual numbered output names. |
| Write containment guard | `tools/lookcheck/frames.py:164` | Resolves links and case; refuses footage, outside-root targets and existing multiply linked files. |
| Guarded output operations | `tools/lookcheck/frames.py:201` | `OutputRoots` wraps check, mkdir, text/bytes writes, removal and rename. Pass explicit WP5.3 roots. |
| Subprocess and environment helpers | `tools/lookcheck/frames.py:92`, `:104` | `tool_env` removes FFREPORT; `run_tool` captures bytes without shell or stdin and enforces timeout. |
| Stream probe | `tools/lookcheck/frames.py:462` | Duration, coded size, average rate, time base and colour tags; rotated input is explicitly refused at :482-486. |
| Exact still extraction | `tools/lookcheck/frames.py:928` | `extract` selects first frame at/after requested timestamp; decode verifies PTS; returns 16-bit RGB PNGs. Rotation refusal applies transitively. |
| Meaning of existing excerpt helper | `tools/lookcheck/frames.py:972` | `excerpt` decodes a time range into PNG frames; it is not a container stream-copy helper. |
| Local path configuration | `tools/local_config.py:87` | Reads both roots; pack root is configured working folder / `wp5.3`, never a hard-coded owner path. |
| Footage locator and suffix restriction | `tools/local_config.py:19`, `:152`, `:196` | Locator searches only video suffixes, rejects missing/ambiguous stems and skips links/junctions. This blocks the photo requirement (R0-1). |
| Inventory counts and GoPro names | `docs/reports/inventory-2026-10-29.md:68`, `:117` | 73 photos, 26 Snorkel, 8 SCUBA, 20 phone videos and one edits video. SCUBA's eight include GX011600 and GX011601. |
| Photo names and candidate partition | `docs/reports/inventory-2026-10-29.md:193`, `:208`, `:236`, `:366` | 62 enumerated HEICs; P-A JPGs IMG_6751.JPG and IMG_6771.JPG; nine P-Z JPGs. Only names/counts are carried into this ledger. |
| Phone video names and exceptional duration | `docs/reports/inventory-2026-10-29.md:278`, `:308`, `:348` | 19 MOV names; two refused names come from the brief. IMG_6762.MOV duration is about 749.033 s, not under two minutes (R0-3). |
| Review and gate policy | `docs/review-gate-clearwater.md`, Parts 1-3 | Read in full; Claude A/B at dispatcher seat, cumulative severity ledger, five-round gates, one final two-leg gate. Dispatch's adjudication-only yields override cleanup ordering. |
| Gate-time verification and reporting | `docs/model-prompting-standard.md`, sections 1-7 | Read in full; evidence before claims; no ambient full-suite repetition. |

### Q6: shipped definitions and exporter

The presets exist exactly under the AD-13 names. No Q6 STOP is needed.

- `src/clearwater/config/presets.py:42` and `:45`: `STARTER_SNORKEL` and
  `STARTER_SCUBA` name the two starters.
- `src/clearwater/config/presets.py:48`: `STARTER_METHOD = "c3"`.
- `src/clearwater/config/presets.py:228`: `starter_presets()` returns both sets
  with empty parameter maps; its docstring explicitly says these use method defaults.
- `src/clearwater/config/presets.py:504`: `PresetStore.install_starters()` writes
  the starters and the once-only marker into a caller-selected store.
- `src/clearwater/config/presets.py:478`: `PresetStore.export_preset(name,
  destination)` exports the stored set using product serialization and atomic writing.
- `src/clearwater/config/__init__.py:42`, `:46`: store and starter factory are
  public exports through `clearwater.config`.
- `src/clearwater/app/composition.py:69`: `correction_methods()` returns the
  registered methods. Read their parameter schemas for the page's effective values;
  this is introspection, not direct engine composition or correction.
- `src/clearwater/methods/schema.py:295`, `:320`, `:351`: C3 schema and resolution
  of missing entries to `Parameter.default`. Preserve exported JSON's empty maps;
  label the page's table as effective method defaults rather than serialized values.
  C3 has no red/blue gain-cap parameters; do not invent them in its value table.

Planned call sequence: guard the pack-local store, marker and export destinations;
construct `PresetStore` in a new pack-local settings subfolder, call
`install_starters()`, then `export_preset()` for each AD-13 name into `presets/`.
No user preset store is consulted or changed. Product helpers make temporary sibling
files internally; guard their containing folders and all caller-supplied targets.

The page includes the brief's required sentence verbatim:

> In v1 both starter presets carry AD-8's defaults, so the corrected items on this page are what both presets produce; at CP5 the owner may change either preset's values (AD-13).

## Round-0 findings and requested rulings

### R0-1 [major, in-envelope, NEW] Photo lookup cannot meet the required API

Recommended ruling: authorize an instrument-local, name-only photo resolver in
`select.py`, with the existing locator still used unchanged for all video items.
The photo resolver would mirror missing/ambiguity refusal and link/junction pruning,
restrict matches to the commissioned photo suffixes and exact inventory names, and
never patch `VIDEO_EXTENSIONS` or modify `tools/local_config.py`.

Evidence: :19 and :196 restrict `find_footage_file` to video suffixes. A cheap
reproduction supplied an explicit planted root, with empty JPG, HEIC and MP4 files;
the first two lookups raised `FootageLookupError` with zero matches while MP4 resolved.
No configured footage traversal occurred. Summary in `round0-probes.log`:

```text
planted-photo: FootageLookupError; matches=0
planted-heic: FootageLookupError; matches=0
planted-video: found planted-video.mp4
```

This is a brief/API mismatch, not an identified product correction defect. No fix
has been made. A helper change outside the owned files would require a separate grant.

### R0-2 [major, in-envelope, NEW] Reused frame helpers refuse rotated phone video

Recommended ruling: authorize a rotation-aware viewing adapter inside the owned
instrument, using `run_tool` / `tool_env` with FFmpeg and selected ffprobe fields.
Retain the existing `probe_stream` / `extract` path for unrotated material. The
adapter must select/confirm PTS, apply display orientation consistently in both
halves, honour the colour conversion, strip thumbnail metadata, and be proved on
the committed rotated fixture. Product inputs and outputs remain untouched.

Evidence: `probe_stream` raises at :482-486; `extract` calls it at :961. The inventory
lists rotated commissioned MOVs at :281-299. The committed fixture independently
reproduced the helper failure without reading any owner file:

```text
rotated fixture: ExtractError: rotated.mp4 is rotated by 90 degrees: outside the envelope
```

`round0-probes.log` records the result; command exit 0 means the probe observed and
reported its expected exceptions, not that rotated extraction succeeded. Leaving
these required items as helper failures would not satisfy the commissioned pack.
No helper or product module has been changed.

### R0-3 [major, in-envelope, NEW] Phone whole-clip duration premise is false

Recommended ruling: retain the brief's explicit whole-clip treatment for all 17
non-HLG phone MOVs, including IMG_6762.MOV, and revise V-P's scheduling allowance.
Do not silently excerpt it using the GoPro rule.

Evidence: the inventory's :348-349 records IMG_6762.MOV at 749.033333... seconds.
Independently, its row at :328 gives a segment duration of 33032370 at movie scale
44100: `33032370 / 44100 = 749.033333...`. This contradicts the brief's parenthesis
"all under 2 min". The report's total 876.269 seconds covers all 20 phone videos
(:78), consistent with this long clip dominating the set. No owner-file probe was
run. The inventory alone is sufficient to dispute the scheduling premise; current
source duration still needs the orchestrator's run. Forty minutes for V-P is not
an evidence-backed allowance for an almost 12.5-minute source plus the other clips.

### R0-4 [minor, in-envelope, NEW] Baseline CSV is absent in this worktree

`Test-Path work/reports/inventory-20261018T235556Z.csv` returned False. No attempt
was made to search the main tree, another worktree, or footage. The report supplies
all required names; exact GoPro durations and excerpt starts remain unmeasured.
The preflight RUN REQUEST below transfers only file names and durations from the
configured working folder's inventory CSV. Live build probes remain authoritative.
Disposition: pending dispatcher execution, not a reason to weaken missing-file rules.

## Conditional implementation design

### Modules, CLI and item state

- `__init__.py`: module documentation only; no Qt imports or import-time work.
- `select.py`: literal inventory-name constants and group membership, immutable
  `Item` records, pure duration-to-excerpt planning, runtime resolution through
  configured roots. `items() -> tuple[Item, ...]` returns the commissioned set.
  An item carries stem, group, kind, source name, runtime source path and excerpt
  eligibility. Probed duration determines the final excerpt bool and plan.
  Photo resolution is conditional on R0-1; no scene classification or glob-based
  expansion of the commissioned list.
- `build.py`: `photos`, `clips [GROUP]`, `presets`, `page`, `tally SHEET`, `all`.
  `clips` allows V-P, V-S, V-D, V-R and V-Z; absence of GROUP covers all video groups.
  `--force-cpu` is passed to the runner only when explicitly requested (tiny test).
  No real run forces CPU, method overrides or encoding overrides.
  Proposed test support: `--config FILE` for synthetic roots and `--manifest FILE`
  for a tiny planted selection, validated with the same guards and record machinery.
  Normal runs use local configuration and the literal commissioned constants.
- A JSON pack-state file under `records/` joins group membership, source names,
  runner record names, real output names, per-pass states, warnings/refusal/failure
  text, viewing-artifact names, excerpt timings and device facts. Persist only
  names / pack-relative artifact references and allowlisted scalar facts; runtime
  absolute paths never serialize. Never discover a pair by guessing filenames.
- Expected membership: P-A 64, P-Z 9, V-S 26, V-D 8, V-P 17, V-R 2, V-Z 2;
  total 128. At full success 126 review rows, headline set 115, candidates 11;
  V-R has no row. The phrase "8 ... and GX011600, GX011601" denotes eight total,
  as the brief's own 34-GoPro headline and inventory enumeration establish.

### Guarding, product invocation and reruns

Derive the real pack root from local configuration's working folder / `wp5.3`.
Every caller-controlled output, directory, log, cache, settings target, record,
temporary output, viewing aid, sheet and page passes `check_output_path` against
that pack root and the configured footage root before writing. Invalid config,
missing/ambiguous source, unsafe target or failed stream-copy integrity check is
exit 2; per-item product failure is recorded and does not abort later items.
Sanitize external diagnostic text before persisting it; do not write raw command
arguments or unfiltered probe metadata into a report or pack artifact.

Invoke `uv run python tools/headless_export.py` as a subprocess without a shell,
one batch per group and photo pose. Use argument vectors and a checked pack-local
settings directory. Refuse a settings file carrying overrides rather than silently
loading non-default values or overwriting it. The following are argument templates,
with sources resolved only at the orchestrator's seat:

```text
<photo sources> --out <pack>/photos --suffix _corrected --bit-depth 8 --settings-dir <pack>/settings --record <pack>/records/<group>.json
<photo sources> --out <pack>/photos --suffix _neutral --bit-depth 8 --neutral --settings-dir <pack>/settings --record <pack>/records/<group>-neutral.json
<video sources or excerpts> --out <pack>/clips --suffix _corrected --settings-dir <pack>/settings --cache-dir <pack>/cache --record <pack>/records/<group>.json
```

Provenance stays on by omitting `--no-provenance`. `--method`, `--parameters`,
`--encoder`, `--quality`, `--ten-bit` and `--force-cpu` are omitted on real builds.
The separate neutral record is necessary to account for both photo invocations;
the corrected record keeps the brief's canonical group name. A rerun uses fresh
record names, accounts for the runner's collision-numbered output names from its
record and updates state explicitly. Preserve prior evidence and owner sheet values;
do not attach an existing vote to a changed source/corrected pair.

### Excerpts and viewing aids

- Whole source in place for V-P, V-R and GoPro/V-Z duration <=45 seconds;
  other eligible videos plan start `0.4 * duration`, length 30 seconds.
- Stream copy through FFmpeg with `-ss` before `-i`, `-t 30`, `-map 0`, `-c copy`;
  checked output in `excerpts/`. Do not call `frames.excerpt` for this operation:
  it produces PNG frames. Reuse `run_tool` and `tool_env` instead.
- Probe source/excerpt stream counts and codec tags using a narrow allowlist.
  A successful copy with a mismatch is exit 2. A failed copy falls back to running
  the whole original and records that fallback, per Q3.
- Record planned start and actual retained source start separately. Match the
  first retained video packet back to the source's timestamp (packet hash where
  needed); rebased excerpt `start_time` alone does not prove actual source start.
  Record measured excerpt duration; do not label keyframe seeking as exact.
- Pair videos are viewing aids: scale each display-oriented half to half size,
  use a two-pixel white separator, HEVC NVENC 8-bit 4:2:0, source colour tags/rate,
  no audio. Link the untouched product output as the item of record. A viewing-aid
  failure is distinct from a failed product export and remains visible.
- Stills at 10/50/90 percent use matching actual PTS, not independent percentage
  rounding of two different timelines. Verify selected timestamps before pairing.
  Reuse `extract` within its envelope; rotated support awaits R0-2's ruling.
- `page.py`: Pillow/ImageCms thumbnail conversion from embedded ICC to sRGB;
  strip other metadata, JPEG quality 90, short side 540. Pair still halves use
  short side 1080. Unprofiled images get no inferred ICC transform. Video RGB
  primaries must be handled consistently with source tags when making browser aids.

### Page, sheet and tally

- `page.py`: plain HTML, no script, separate sections for each group, file-name
  captions, escaped text and relative URLs. Explicit left/source and right/corrected
  labels; photo source view is the product's neutral export with matching orientation,
  colour handling and bit depth. Display failed/refused items and product text.
  Include D65 instructions, all five artifact types, effective starter values and
  preset downloads. No preference or quality verdict is generated.
- Both `build.py page --check` and `python -m tools.reviewpack.page --check` are
  planned: validate every local href/src is present and resolves inside the pack;
  reject traversal/escaping links. No links back into the source folder. Page can
  be built after photos and rebuilt after each video group from persisted state.
- `sheet.py`: UTF-8 CSV with the brief's exact columns. One row per completed,
  genuinely viewable source/corrected item; failed/refused and not-yet-built items
  stay visible in page/state accounting, outside the review rows. Never silently
  truncate an existing owner's sheet when later groups are added. Preserve matching
  rows and append new ones; changed-pair identity is an explicit error to resolve.
- `preferred`: blank means unjudged; yes/no/undecided are the allowed nonblank
  values. Count each nonblank value as judged and only yes as preferred. Artifact
  and above_surface fields allow blank/yes only; note is free text. Strictly validate
  header, row shape, group/item identity, duplicate rows and values; error names row.
- `tally`: per-group, headline and separate candidate counts; above-surface is
  counted, not silently excluded. Empty sheet reports zero judged without error.
  Valid tallies exit 0 irrespective of percentage/artifacts and use the prescribed
  headline format, with no judgement words. Malformed CSV/value is a usage error,
  exit 2, as required by Q7 rather than a zero-status false result.
- `all`: photos, presets, video groups, page/check; no owner judgement and no real
  runs in the cell. The integration test uses two planted fixture stills and the
  committed tiny HEVC fixture, real runner and FFmpeg, `--force-cpu`.

## Planned RUN REQUESTs

These are queued proposals, **not permission to start a build before GREEN and
Reviewer A convergence**. Every real piece runs only at the orchestrator's seat,
with no other heavy job and no EXCLUSIVE window open. WP4.6 V7 and WP3.6P export /
memory windows take precedence. Before every clips piece the dispatcher runs
`df -h /c` and requires at least 25 GB free. Commands are runnable from this worktree
root after implementation; configured roots route outputs under `work/wp5.3/`.
Wall times are scheduling estimates, not figures of record.

Inventory preflight (light, independent of Q8's heavy-job order):

```text
RUN REQUEST: uv run python -c "import csv,json,sys; from pathlib import Path; sys.path.insert(0,'tools'); from local_config import load_local_config; from lookcheck.frames import OutputRoots; c=load_local_config(); r=OutputRoots(allowed=c.working_path/'wp5.3',footage=c.footage_path); p=c.working_path/'reports'/'inventory-20261018T235556Z.csv'; rows=list(csv.DictReader(p.open(encoding='utf-8-sig',newline=''))); data=[{'name':Path(x['path']).name,'duration_seconds':x['duration_seconds']} for x in rows]; r.write_text(r.allowed/'records'/'inventory-durations.json',json.dumps(data,indent=2)+'\n')"
```

Expected <1 minute; output `records/inventory-durations.json` (35 name/duration
rows only). If the CSV is absent at the seat too, return that fact and obtain
durations through the scheduled build probes; do not search footage in the cell.

Q8 order, including candidate/refusal coverage omitted from its shorthand:

| Order | Exact queued command | Expected wall time | Outputs under work/wp5.3/ |
|---|---|---|---|
| 1 | `RUN REQUEST: uv run python -m tools.reviewpack.build photos` | about 1 hour, GPU | photos, thumbnails, P-A/P-Z corrected and neutral records, state, logs |
| 2 | `RUN REQUEST: uv run python -m tools.reviewpack.build presets` | <1 minute | both preset JSON files, pack-local store and marker, state/log |
| 3 | `RUN REQUEST: uv run python -m tools.reviewpack.build page --check` | <2 minutes | index.html, initial review-sheet.csv, link-check log |
| 4 | `RUN REQUEST: uv run python -m tools.reviewpack.build clips V-P` | reserve up to about 2.5 hours pending R0-3 and measured durations | 17 product clips, pair clips/stills, thumbnails, V-P record, state/logs/cache |
| 5 | `RUN REQUEST: uv run python -m tools.reviewpack.build clips V-S` | about 1.5-2 hours, provisional | 26 clips and aids, excerpts where needed, V-S record, state/logs/cache |
| 6 | `RUN REQUEST: uv run python -m tools.reviewpack.build clips V-D` | about 40-70 minutes, provisional | 8 clips and aids, excerpts where needed, V-D record, state/logs/cache |
| 7 | `RUN REQUEST: uv run python -m tools.reviewpack.build clips V-Z` | about 10-20 minutes, provisional | 2 candidate clips and aids, excerpt as needed, V-Z record, state/logs/cache |
| 8 | `RUN REQUEST: uv run python -m tools.reviewpack.build clips V-R` | <2 minutes for expected refusals | 2 product refusal records/texts, state/logs; no review rows |
| 9 | `RUN REQUEST: uv run python -m tools.reviewpack.build page --check` | <2 minutes | final index and merged sheet, all links checked |
| 10 | Config-resolved tally request below | <1 minute | zero-judged tally, console captured by dispatcher under logs |

Order 10 resolves the configured working folder so that invocation from the
worktree root cannot mistake the worktree's scratch folder for the real pack:

```text
RUN REQUEST: uv run python -c "import sys; sys.path.insert(0,'tools'); from local_config import load_local_config; from tools.reviewpack.build import main; raise SystemExit(main(['tally',str(load_local_config().working_path/'wp5.3'/'review-sheet.csv')]))"
```

All pieces need per-item accounting read back before the next relevant handoff.
A product defect is a STOP to CHARC, not an instrument fix.

## RED roster (task 2, not run or written this turn)

Every node initially fails on the absent `tools.reviewpack` package/API on this
base. Task 2 will record the actual failure summary, not claim assertions ran past
collection if import failure prevents it. Pure tests use independent `tmp_path`s;
first GREEN execution records node durations (AD-30). Any node exceeding five
seconds moves to `slow` with a reason. Exactly one planned end-to-end slow node;
no new footage, gpu, gui or fullclip node.

| Proposed test | Contract / planted negative control | Expected RED on base |
|---|---|---|
| test_inventory_names_and_group_membership | Assert all 128 exact inventory names, group counts, no duplicates, 115 headline and 11 candidate members. | select import/API missing |
| test_locator_missing_ambiguous_and_suffixes | Explicit planted root; videos use existing locator; photo behaviour follows R0-1 ruling; reject ambiguity/links instead of selecting first. | select import/API missing |
| test_excerpt_plan_boundaries_and_phone_rule | 6.4, 42.3, 45 and >45 seconds; 40%/30s arithmetic; V-P whole even long, V-Z eligible; reject invalid durations. | select import/API missing |
| test_output_guard_refuses_footage_and_escape | Planted roots, traversal and aliases where portable; CLI exit 2 and no written output. | build import/API missing |
| test_runner_arguments_and_record_mapping | Defaults vs neutral, provenance on, isolated settings/cache, nonzero runner results, actual numbered output names and distinct neutral records. | build import/API missing |
| test_stream_copy_plan_checks_and_actual_start | Assert seek/map/copy arguments; matching count/tags, mismatch exit 2, copy-failure whole fallback; rebased zero is not source start. | build import/API missing |
| test_rotated_viewing_adapter | Fixture-based or narrow planted probes according to R0-2 ruling; orientation/PTS consistency instead of treating a helper refusal as completed. | build import/API missing |
| test_sheet_header_rows_and_preservation | Exact columns; no refused/failed rows; separate candidates; preserve existing answers when later groups append; refuse changed pair identity. | sheet import/API missing |
| test_tally_empty_and_filled | Empty zero judged; e.g. yes/no/undecided counts, headline excludes P-Z/V-Z; artifact and above-surface counts; no verdict words. | sheet import/API missing |
| test_tally_strict_errors | Bad value/header/row shape, duplicate or unknown identity produces row-specific error and CLI exit 2. | sheet import/API missing |
| test_page_planted_artifacts_and_links | All groups, labels, neutral sentence, preset values and exact AD-13 sentence; escaped names; every link resolves. Plant missing/escaping link and require failed check. | page import/API missing |
| test_thumbnail_icc_and_metadata_policy | ICC-aware sRGB derivative, no inferred profile when absent, expected size, no carried source metadata. | page import/API missing |
| test_presets_use_product_exporter | Product starter installation/export, empty JSON maps preserved, effective values reflect schema defaults, owner store untouched. | build import/API missing |
| test_all_tiny_set (slow) | Two fixture stills plus hevc8-bt709-full.mp4, actual all/runner/FFmpeg, force-cpu, no Qt; output records and pairs, link check, rows and empty tally. Reason: "runs the headless runner and FFmpeg". | build module/CLI missing |

## Verification and review ledger

Round-0 verification: suspected photo API mismatch -> independently planted JPG /
HEIC / MP4 lookup -> confirmed; suspected rotated-helper mismatch -> committed
rotated fixture probe -> confirmed; suspected phone duration mismatch -> independent
inventory fraction -> confirmed. No false positive claimed, no product/test fix
made. Findings await rulings; no clean implementation pass or review convergence
is claimed. Probe summary log: `round0-probes.log`, under this worktree's
`work/wp5.3/`. Scratch planted files are ignored and not part of the commit.

No pytest, ruff, mypy, real build, Reviewer A or Reviewer B was run in task 1.
The final gate remains the dispatch fill's one two-leg gate, with no fullclip leg;
DR-99 is handled only under its stated main-alone equivalence condition.

| Round | Critical / major / minor | In / out envelope | NEW / REOPENED | Reverts | Product / test-only fixes | Disposition / transport | Depth |
|---|---|---|---|---|---|---|---|
| 0 (mapping, not Reviewer A) | 0 / 3 / 1 | 4 / 0 | 4 / 0 | 0 | none / none | R0-1..3 STOP to CHARC; R0-4 queued preflight; uv Python probe exit 0 | dispatcher pending |

Subsequent Reviewer A turns adjudicate every finding, update this cumulative table
and yield without remediation. Fixes belong to a separately dispatched turn.
At rounds 5, 10, ... STOP with the ledger for approval to continue under the fill.

## Depth table

| Turn / boundary | Session ID | depth_input_tokens (dispatcher read) | Action |
|---|---|---|---|
| Turn 1 / round 0 | dispatcher pending | dispatcher pending | Task 1 ledger only; yield for rulings. |

Evaluate near 200K; stop at a step boundary near 250K. No self-estimated figures.
