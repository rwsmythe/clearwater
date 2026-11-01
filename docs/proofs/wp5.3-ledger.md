# WP5.3 cumulative ledger

## Dispatch and state

- Package: WP5.3, CP5 visual review pack; Codex implementer lane, STRONG.
- Verified base and current HEAD at round 0: `2050a89a`; initial tracked diff empty.
- Turn 1 is task 1 only. No instrument or test code is written this turn.
- State: **Reviewer A round 1 remediated in turn 5; ready for round 2**.
  CHARC's complete F1 ruling is committed in the brief at `abeef516`; no ruling
  remains outstanding. CHARC granted R0-1, R0-2
  and R0-3 in `f99fca742e060f14`, folded into the brief at `b7c95a46`.
  R0-4 is resolved by the dispatcher-provided inventory CSV. No ruling is pending.
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

### R0-4 [minor, in-envelope, NEW at round 0] Baseline CSV availability

At round 0, `Test-Path work/reports/inventory-20261018T235556Z.csv` returned False.
At turn 2 the dispatcher supplied that file in this worktree's ignored `work/reports/`.
It was read for GoPro file names and durations only. No CSV path or other metadata
is copied into a committed file; the CSV itself is not committed. The duration table
under Turn 2 records planned intervals, not live probes or actual keyframe starts.
Disposition: resolved; no inventory-preflight RUN REQUEST is needed. Live build
probes remain authoritative.

## Implementation design (round-0 rulings applied)

### Modules, CLI and item state

- `__init__.py`: module documentation only; no Qt imports or import-time work.
- `select.py`: literal inventory-name constants and group membership, immutable
  `Item` records, pure duration-to-excerpt planning, runtime resolution through
  configured roots. `items() -> tuple[Item, ...]` returns the commissioned set.
  An item carries stem, group, kind, source name, runtime source path and excerpt
  eligibility. Probed duration determines the final excerpt bool and plan.
  Photo resolution is authorized by R0-1; no scene classification or glob-based
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
  Reuse `extract` within its envelope. R0-2 authorizes an owned rotation adapter:
  FFmpeg default autorotate on both halves, no manual transpose, and equal oriented
  dimensions checked before hstack. Product output stays linked as the record.
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

Q8 order, including candidate/refusal coverage omitted from its shorthand:

| Order | Exact queued command | Expected wall time | Outputs under work/wp5.3/ |
|---|---|---|---|
| 1 | `RUN REQUEST: uv run python -m tools.reviewpack.build photos` | about 1 hour, GPU | photos, thumbnails, P-A/P-Z corrected and neutral records, state, logs |
| 2 | `RUN REQUEST: uv run python -m tools.reviewpack.build presets` | <1 minute | both preset JSON files, pack-local store and marker, state/log |
| 3 | `RUN REQUEST: uv run python -m tools.reviewpack.build page --check` | <2 minutes | index.html, initial review-sheet.csv, link-check log |
| 4 | `RUN REQUEST: uv run python -m tools.reviewpack.build clips V-P` | reserve about 2.5 hours, provisional; CHARC's allowance is about 27 minutes of source material | 17 whole product clips, IMG_6762.MOV last, pair clips/stills, thumbnails, V-P record, state/logs/cache |
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
| 0 (mapping, not Reviewer A) | 0 / 3 / 1 | 4 / 0 | 4 / 0 | 0 | none / none | R0-1..3 granted at turn 2; R0-4 resolved by CSV copy; uv Python probe exit 0 | 118,603 after turn 1 |
| Session 2 / turn 3 (GREEN verification, not Reviewer A) | 0 / 6 / 0 | 6 / 0 | 6 / 0 | 0 | instrument fixes / regression additions | Six independently reproduced instrument gaps fixed; 70 nodes green; Reviewer A pending | 142,467 after turn 3 |
| A1 (session 2 / turn 4 adjudication; turn 5 remediation) | 0 / 3 / 3; 6 advisory | 10 / 2 after adjudication | 12 / 0; accepted blocking 3 | 0 | turn 5: 10 instrument behavior fixes with regression controls; no src/ changes | Counted Claude pass; 10 ACCEPTED fixed under F1 ruling; F10 OUT/banked Limit; F11 REJECTED; ready for A2 | turn 3: 142,467; turn 4: 36,709 (dispatcher supplied) |

Subsequent Reviewer A turns adjudicate every finding, update this cumulative table
and yield without remediation. Fixes belong to a separately dispatched turn.
At rounds 5, 10, ... STOP with the ledger for approval to continue under the fill.

## Depth table

| Turn / boundary | Session ID | depth_input_tokens (dispatcher read) | Action |
|---|---|---|---|
| Turn 1 / round 0 | dispatcher pending | 118,603 | Dispatcher supplied after turn 1; round-0 ledger committed as e7beee05. |
| Turn 2 / RED | session 1, same session | 179,868 | Dispatcher supplied at session-2 dispatch; RED commit 10f1f70b; session 1 retired. |
| Session 2 / turn 3 / GREEN | fresh session; dispatcher to fill ID | 142,467 | Dispatcher supplied in turn 4; GREEN committed as f506b597. |
| Session 2 / turn 4 / A1 adjudication | same session 2 | 36,709 | Dispatcher supplied in turn 5; adjudication committed as 0553d317. Figure is recorded verbatim despite its decrease from turn 3; no independent counter is available. |
| Session 2 / turn 5 / A1 remediation | same session 2 | dispatcher pending | Complete ruling at abeef516; RED-first remediation, then yield for A2. |

Evaluate near 200K; stop at a step boundary near 250K. No self-estimated figures.


## Turn 2: RED

### Ruling applied and scope

Turn starts from `b7c95a46`, following round-0 ledger commit `e7beee05`.
CHARC ruling `f99fca742e060f14` governs: owned photo resolution only for the
commissioned HEIC/JPG names, duplicate refusal and junction pruning; owned video
viewing adapter with default FFmpeg autorotation on both halves and equality of
display dimensions checked before hstack; every V-P item whole with IMG_6762.MOV
last. R0-4 is closed by the provided CSV. The depth after turn 1 is 118,603 tokens.

Built `tests/test_reviewpack.py` and five importable skeleton modules. Skeleton
functions and properties raise named `NotImplementedError`; their only additional
code is the two immutable data declarations and imports. No selection, correction,
file writer, runner invocation, video adapter or tally implementation was added.
No frozen interface or unowned file was edited. Local configuration was not edited;
the owner source folder was not traversed and no owner file was read. Synthetic
roots were passed explicitly; the existing pytest temp-root guard is used unchanged
with the required sandbox shim (including its normal configuration safety check).

### Roster as built and changes from round 0

The original 14 roster rows are represented by 60 independently collected nodes.
They cover inventory names/counts and V-P ordering; exact source resolution; missing,
ambiguous, case-insensitive and unsafe photo lookup; real junction/link pruning;
whole/excerpt boundaries and invalid durations; output/config refusal; neutral vs
default runner arguments, provenance and cache; collision-numbered output mapping
and failed-item retention; stream-copy arguments/integrity, actual source packet
start and copy-failure fallback; rotated-frame and real pair-video dimensions;
pre-hstack size refusal; sheet exclusion, preservation and changed-pair rejection;
empty/filled strict tallies and CLI statuses; planted HTML, link failures and escaping;
ICC-aware/unprofiled thumbnails and pair-still side order; product preset exports;
and the one actual-runner/FFmpeg integration node.

Changes from the proposed roster:

- Collection/import failure is replaced by explicit named raising entry points,
  as turn 2 requires. Each node now reaches the contract entry point it exercises.
- R0-1 adds the duplicate-in-two-folders and real junction/link negative controls.
  On this host junction creation succeeded; no capability skip was taken.
- R0-2 has three nodes: oriented frame size 180x320, real oriented pair size
  182x160 (two half-width 90x160 views plus separator), and rejecting unequal
  display sizes before any hstack process. Tests observe real FFmpeg command
  arguments to exclude noautorotate/manual transpose while checking decoded output.
- The unequal-size control permits read-only probes/decodes and forbids hstack;
  it does not incorrectly forbid the probes needed to determine dimensions.
- Excerpt expectations use literal durations from the supplied baseline CSV.
- One malformed-row test initially failed in test setup: the keyword `item`
  collided with the helper argument. Renamed that helper argument and reran; the
  final run has only intended stub failures. Import/style and regex-literal lint
  findings were fixed in the owned test/skeleton files before the final checks.
- Exactly one node carries `slow`, with reason `runs the headless runner and FFmpeg`.
  There are no footage, gpu, gui or fullclip nodes. The slow node fails immediately
  at `build.main` in RED, so no headless export or video encoding ran this turn.

### Commands and results

All runner outputs are under this worktree, not the main working folder.
Final pytest invocation (stdout/stderr captured in `turn2-red-final.log`):

```powershell
$env:PYTHONPATH='scripts'
uv run pytest -q tests/test_reviewpack.py --basetemp=work/wp5.3/tmp -p sandbox_mkdir_shim -p no:cacheprovider -m 'not gpu and not footage and not gui and not fullclip' --durations=0 --junitxml=work/wp5.3/turn2-red-final.xml
```

- Pytest exit 1: `60 failed in 1.29s`. JUnit independently confirms 60 failures,
  zero collection/setup errors, zero skipped nodes and zero passing nodes. Each
  failure message is the intended named `NotImplementedError` below. This is RED
  evidence, not a claim that the behavior assertions passed.
- `uv run ruff check tools/reviewpack tests/test_reviewpack.py`: exit 0,
  `All checks passed!` (`turn2-ruff-final.log`).
- `uv run mypy`: exit 0, `Success: no issues found in 151 source files`
  (`turn2-mypy-final.log`).
- `uv run ruff format tools/reviewpack tests/test_reviewpack.py`: exit 0,
  `1 file reformatted, 5 files left unchanged` on the last format invocation
  (`turn2-format-final.log`). No format-check gate is claimed; that stays at the
  dispatcher seat per the dispatch fill.
- Scope/LF audit: exit 0; seven owned changed files, zero CR bytes and no trailing
  whitespace. AST audit confirms all 24 skeleton callables contain only a docstring
  and a named `NotImplementedError`; exactly one slow test is declared.
  `git diff --check` exits 0. Evidence: `turn2-scope-lf-check.log`.

Evidence file names above are under `work/wp5.3/`; `turn2-red-final.xml` carries
per-node times and the exact exception locations. Initial development evidence is
`turn2-red.log` / `turn2-red.xml`; the initial unrelated setup failure is superseded
by the final run. Full suite, real build, Reviewer A and Reviewer B were not run.
AD-30 timing here measures RED stub bodies only, not implemented feature cost.
Re-measure every node on first GREEN execution and move any parallel node over
five seconds to slow with a reason; the end-to-end node is slow from the outset.

### Observed node failures

| Node ID | Failure line on this candidate | Exception message | RED seconds |
|---|---|---|---|
| `tests/test_reviewpack.py::test_inventory_names_and_group_membership` | `tools/reviewpack/select.py:58: NotImplementedError` | `NotImplementedError: catalog` | 0.001 |
| `tests/test_reviewpack.py::test_items_resolve_exact_names_without_scene_classification` | `tools/reviewpack/select.py:70: NotImplementedError` | `NotImplementedError: items` | 0.080 |
| `tests/test_reviewpack.py::test_photo_resolver_case_insensitive_exact_commissioned_name` | `tools/reviewpack/select.py:83: NotImplementedError` | `NotImplementedError: find_photo` | 0.003 |
| `tests/test_reviewpack.py::test_photo_resolver_missing_refusal` | `tools/reviewpack/select.py:83: NotImplementedError` | `NotImplementedError: find_photo` | 0.002 |
| `tests/test_reviewpack.py::test_photo_resolver_ambiguous_duplicate_in_two_folders` | `tools/reviewpack/select.py:83: NotImplementedError` | `NotImplementedError: find_photo` | 0.003 |
| `tests/test_reviewpack.py::test_photo_resolver_prunes_directory_junction_or_link` | `tools/reviewpack/select.py:83: NotImplementedError` | `NotImplementedError: find_photo` | 0.028 |
| `tests/test_reviewpack.py::test_photo_resolver_refuses_uncommissioned_or_path_name[unknown]` | `tools/reviewpack/select.py:83: NotImplementedError` | `NotImplementedError: find_photo` | 0.003 |
| `tests/test_reviewpack.py::test_photo_resolver_refuses_uncommissioned_or_path_name[path]` | `tools/reviewpack/select.py:83: NotImplementedError` | `NotImplementedError: find_photo` | 0.003 |
| `tests/test_reviewpack.py::test_photo_resolver_refuses_uncommissioned_or_path_name[suffix]` | `tools/reviewpack/select.py:83: NotImplementedError` | `NotImplementedError: find_photo` | 0.003 |
| `tests/test_reviewpack.py::test_excerpt_plan_boundaries_and_phone_rule[V-D-6.406-0.0-6.406-False]` | `tools/reviewpack/select.py:96: NotImplementedError` | `NotImplementedError: excerpt_plan` | 0.001 |
| `tests/test_reviewpack.py::test_excerpt_plan_boundaries_and_phone_rule[V-D-42.342-0.0-42.342-False]` | `tools/reviewpack/select.py:96: NotImplementedError` | `NotImplementedError: excerpt_plan` | 0.001 |
| `tests/test_reviewpack.py::test_excerpt_plan_boundaries_and_phone_rule[V-S-45.0-0.0-45.0-False]` | `tools/reviewpack/select.py:96: NotImplementedError` | `NotImplementedError: excerpt_plan` | 0.001 |
| `tests/test_reviewpack.py::test_excerpt_plan_boundaries_and_phone_rule[V-S-45.001-18.0004-30.0-True]` | `tools/reviewpack/select.py:96: NotImplementedError` | `NotImplementedError: excerpt_plan` | 0.001 |
| `tests/test_reviewpack.py::test_excerpt_plan_boundaries_and_phone_rule[V-D-1046.512-418.6048-30.0-True]` | `tools/reviewpack/select.py:96: NotImplementedError` | `NotImplementedError: excerpt_plan` | 0.001 |
| `tests/test_reviewpack.py::test_excerpt_plan_boundaries_and_phone_rule[V-Z-179.93-71.972-30.0-True]` | `tools/reviewpack/select.py:96: NotImplementedError` | `NotImplementedError: excerpt_plan` | 0.001 |
| `tests/test_reviewpack.py::test_excerpt_plan_boundaries_and_phone_rule[V-P-749.033333-0.0-749.033333-False]` | `tools/reviewpack/select.py:96: NotImplementedError` | `NotImplementedError: excerpt_plan` | 0.001 |
| `tests/test_reviewpack.py::test_excerpt_plan_boundaries_and_phone_rule[V-R-44.0-0.0-44.0-False]` | `tools/reviewpack/select.py:96: NotImplementedError` | `NotImplementedError: excerpt_plan` | 0.001 |
| `tests/test_reviewpack.py::test_excerpt_plan_rejects_invalid_duration[0.0]` | `tools/reviewpack/select.py:96: NotImplementedError` | `NotImplementedError: excerpt_plan` | 0.001 |
| `tests/test_reviewpack.py::test_excerpt_plan_rejects_invalid_duration[-1.0]` | `tools/reviewpack/select.py:96: NotImplementedError` | `NotImplementedError: excerpt_plan` | 0.001 |
| `tests/test_reviewpack.py::test_excerpt_plan_rejects_invalid_duration[nan]` | `tools/reviewpack/select.py:96: NotImplementedError` | `NotImplementedError: excerpt_plan` | 0.001 |
| `tests/test_reviewpack.py::test_excerpt_plan_rejects_invalid_duration[inf]` | `tools/reviewpack/select.py:96: NotImplementedError` | `NotImplementedError: excerpt_plan` | 0.001 |
| `tests/test_reviewpack.py::test_output_guard_refuses_footage_and_parent_escape` | `tools/reviewpack/build.py:23: NotImplementedError` | `NotImplementedError: check_target` | 0.004 |
| `tests/test_reviewpack.py::test_cli_refuses_working_folder_inside_footage_before_write` | `tools/reviewpack/build.py:185: NotImplementedError` | `NotImplementedError: main` | 0.002 |
| `tests/test_reviewpack.py::test_photo_runner_arguments_pin_pose_and_preserve_defaults[False]` | `tools/reviewpack/build.py:46: NotImplementedError` | `NotImplementedError: runner_arguments` | 0.002 |
| `tests/test_reviewpack.py::test_photo_runner_arguments_pin_pose_and_preserve_defaults[True]` | `tools/reviewpack/build.py:46: NotImplementedError` | `NotImplementedError: runner_arguments` | 0.002 |
| `tests/test_reviewpack.py::test_video_runner_arguments_use_checked_cache_and_explicit_cpu_only` | `tools/reviewpack/build.py:46: NotImplementedError` | `NotImplementedError: runner_arguments` | 0.002 |
| `tests/test_reviewpack.py::test_record_mapping_uses_numbered_product_output_and_retains_failures` | `tools/reviewpack/build.py:60: NotImplementedError` | `NotImplementedError: read_runner_record` | 0.003 |
| `tests/test_reviewpack.py::test_stream_copy_arguments_preserve_all_streams_and_seek_before_input` | `tools/reviewpack/build.py:77: NotImplementedError` | `NotImplementedError: stream_copy_command` | 0.002 |
| `tests/test_reviewpack.py::test_stream_copy_integrity_refuses_lost_stream_or_changed_tag[stream-count]` | `tools/reviewpack/build.py:89: NotImplementedError` | `NotImplementedError: validate_stream_copy` | 0.001 |
| `tests/test_reviewpack.py::test_stream_copy_integrity_refuses_lost_stream_or_changed_tag[codec-tag]` | `tools/reviewpack/build.py:89: NotImplementedError` | `NotImplementedError: validate_stream_copy` | 0.001 |
| `tests/test_reviewpack.py::test_actual_excerpt_start_uses_source_packet_not_rebased_zero` | `tools/reviewpack/build.py:104: NotImplementedError` | `NotImplementedError: actual_excerpt_start` | 0.000 |
| `tests/test_reviewpack.py::test_failed_stream_copy_falls_back_to_whole_source` | `tools/reviewpack/build.py:121: NotImplementedError` | `NotImplementedError: prepare_excerpt` | 0.008 |
| `tests/test_reviewpack.py::test_rotation_adapter_extracts_oriented_fixture_dimensions` | `tools/reviewpack/build.py:138: NotImplementedError` | `NotImplementedError: extract_view_frame` | 0.003 |
| `tests/test_reviewpack.py::test_rotated_pair_autorotates_both_halves_with_equal_dimensions` | `tools/reviewpack/build.py:161: NotImplementedError` | `NotImplementedError: make_pair` | 0.002 |
| `tests/test_reviewpack.py::test_pair_refuses_unequal_display_dimensions_before_hstack` | `tools/reviewpack/build.py:161: NotImplementedError` | `NotImplementedError: make_pair` | 0.003 |
| `tests/test_reviewpack.py::test_sheet_header_rows_exclude_failed_refused_and_not_built` | `tools/reviewpack/sheet.py:25: NotImplementedError` | `NotImplementedError: write_sheet` | 0.002 |
| `tests/test_reviewpack.py::test_sheet_preserves_answers_when_later_groups_arrive` | `tools/reviewpack/sheet.py:25: NotImplementedError` | `NotImplementedError: write_sheet` | 0.002 |
| `tests/test_reviewpack.py::test_sheet_refuses_to_transfer_vote_to_regenerated_output` | `tools/reviewpack/sheet.py:25: NotImplementedError` | `NotImplementedError: write_sheet` | 0.004 |
| `tests/test_reviewpack.py::test_tally_empty_sheet_is_zero_judged_without_verdict` | `tools/reviewpack/sheet.py:37: NotImplementedError` | `NotImplementedError: tally` | 0.003 |
| `tests/test_reviewpack.py::test_tally_filled_headline_candidates_artifacts_and_above_surface` | `tools/reviewpack/sheet.py:37: NotImplementedError` | `NotImplementedError: tally` | 0.003 |
| `tests/test_reviewpack.py::test_tally_invalid_value_names_row[preferred-maybe]` | `tools/reviewpack/sheet.py:37: NotImplementedError` | `NotImplementedError: tally` | 0.003 |
| `tests/test_reviewpack.py::test_tally_invalid_value_names_row[halos-no]` | `tools/reviewpack/sheet.py:37: NotImplementedError` | `NotImplementedError: tally` | 0.003 |
| `tests/test_reviewpack.py::test_tally_invalid_value_names_row[above_surface-false]` | `tools/reviewpack/sheet.py:37: NotImplementedError` | `NotImplementedError: tally` | 0.003 |
| `tests/test_reviewpack.py::test_tally_invalid_value_names_row[group-not-a-group]` | `tools/reviewpack/sheet.py:37: NotImplementedError` | `NotImplementedError: tally` | 0.003 |
| `tests/test_reviewpack.py::test_tally_invalid_value_names_row[item-../secret]` | `tools/reviewpack/sheet.py:37: NotImplementedError` | `NotImplementedError: tally` | 0.003 |
| `tests/test_reviewpack.py::test_tally_refuses_malformed_sheet[header]` | `tools/reviewpack/sheet.py:37: NotImplementedError` | `NotImplementedError: tally` | 0.003 |
| `tests/test_reviewpack.py::test_tally_refuses_malformed_sheet[duplicate]` | `tools/reviewpack/sheet.py:37: NotImplementedError` | `NotImplementedError: tally` | 0.003 |
| `tests/test_reviewpack.py::test_tally_refuses_malformed_sheet[extra-cell]` | `tools/reviewpack/sheet.py:37: NotImplementedError` | `NotImplementedError: tally` | 0.003 |
| `tests/test_reviewpack.py::test_tally_refuses_malformed_sheet[missing-cell]` | `tools/reviewpack/sheet.py:37: NotImplementedError` | `NotImplementedError: tally` | 0.003 |
| `tests/test_reviewpack.py::test_tally_cli_valid_scores_exit_zero_and_invalid_sheet_exit_two` | `tools/reviewpack/build.py:185: NotImplementedError` | `NotImplementedError: main` | 0.003 |
| `tests/test_reviewpack.py::test_page_planted_groups_labels_presets_and_name_only_links` | `tools/reviewpack/page.py:28: NotImplementedError` | `NotImplementedError: write_page` | 0.013 |
| `tests/test_reviewpack.py::test_page_escapes_refusal_text_instead_of_rendering_markup` | `tools/reviewpack/page.py:28: NotImplementedError` | `NotImplementedError: write_page` | 0.003 |
| `tests/test_reviewpack.py::test_page_check_detects_missing_escaping_and_nonlocal_links[missing]` | `tools/reviewpack/page.py:41: NotImplementedError` | `NotImplementedError: check_links` | 0.003 |
| `tests/test_reviewpack.py::test_page_check_detects_missing_escaping_and_nonlocal_links[escape]` | `tools/reviewpack/page.py:41: NotImplementedError` | `NotImplementedError: check_links` | 0.003 |
| `tests/test_reviewpack.py::test_page_check_detects_missing_escaping_and_nonlocal_links[nonlocal]` | `tools/reviewpack/page.py:41: NotImplementedError` | `NotImplementedError: check_links` | 0.003 |
| `tests/test_reviewpack.py::test_thumbnail_converts_embedded_p3_to_srgb_and_strips_other_metadata` | `tools/reviewpack/page.py:55: NotImplementedError` | `NotImplementedError: thumbnail` | 0.008 |
| `tests/test_reviewpack.py::test_thumbnail_without_icc_keeps_rgb_and_drops_text` | `tools/reviewpack/page.py:55: NotImplementedError` | `NotImplementedError: thumbnail` | 0.003 |
| `tests/test_reviewpack.py::test_pair_still_uses_source_left_corrected_right_and_separator` | `tools/reviewpack/page.py:70: NotImplementedError` | `NotImplementedError: pair_still` | 0.003 |
| `tests/test_reviewpack.py::test_presets_export_product_starters_without_expanding_serialized_maps` | `tools/reviewpack/build.py:173: NotImplementedError` | `NotImplementedError: export_presets` | 0.002 |
| `tests/test_reviewpack.py::test_all_tiny_set` | `tools/reviewpack/build.py:185: NotImplementedError` | `NotImplementedError: main` | 0.013 |

Maximum RED per-node time: 0.080 s. All 60 nodes reached their named stubs.

### Supplied CSV: planned GoPro intervals

These numbers are inventory inputs, not a new probe, a performance measurement or
an actual-start claim. Names only are retained. A planned start of zero denotes
whole-clip input. Actual keyframe starts remain pending the real orchestrator runs.

| Group | File name | Inventory duration (s) | Planned start (s) | Planned length (s) |
|---|---|---|---|---|
| V-D | GX011589.mp4 | 6.406 | 0.0000 | 6.406 |
| V-D | GX011590.mp4 | 103.170 | 41.2680 | 30.000 |
| V-D | GX011591.mp4 | 138.205 | 55.2820 | 30.000 |
| V-D | GX011592.mp4 | 42.342 | 0.0000 | 42.342 |
| V-D | GX011593.mp4 | 556.456 | 222.5824 | 30.000 |
| V-D | GX011598.mp4 | 525.325 | 210.1300 | 30.000 |
| V-D | GX011600.mp4 | 1046.512 | 418.6048 | 30.000 |
| V-D | GX011601.mp4 | 470.937 | 188.3748 | 30.000 |
| V-S | GX011603.mp4 | 69.136 | 27.6544 | 30.000 |
| V-S | GX011604.mp4 | 15.682 | 0.0000 | 15.682 |
| V-S | GX011605.mp4 | 10.811 | 0.0000 | 10.811 |
| V-S | GX011606.mp4 | 8.976 | 0.0000 | 8.976 |
| V-S | GX011607.mp4 | 9.443 | 0.0000 | 9.443 |
| V-S | GX011608.mp4 | 26.059 | 0.0000 | 26.059 |
| V-S | GX011609.mp4 | 69.469 | 27.7876 | 30.000 |
| V-S | GX011610.mp4 | 32.232 | 0.0000 | 32.232 |
| V-S | GX011611.mp4 | 74.708 | 29.8832 | 30.000 |
| V-S | GX011612.mp4 | 54.454 | 21.7816 | 30.000 |
| V-S | GX011613.mp4 | 5.339 | 0.0000 | 5.339 |
| V-S | GX011614.mp4 | 39.873 | 0.0000 | 39.873 |
| V-S | GX011615.mp4 | 48.382 | 19.3528 | 30.000 |
| V-S | GX011616.mp4 | 3.604 | 0.0000 | 3.604 |
| V-S | GX011617.mp4 | 26.727 | 0.0000 | 26.727 |
| V-S | GX011618.mp4 | 42.276 | 0.0000 | 42.276 |
| V-S | GX011619.mp4 | 75.475 | 30.1900 | 30.000 |
| V-S | GX011620.mp4 | 41.275 | 0.0000 | 41.275 |
| V-S | GX011621.mp4 | 77.711 | 31.0844 | 30.000 |
| V-S | GX011622.mp4 | 57.457 | 22.9828 | 30.000 |
| V-S | GX011623.mp4 | 42.409 | 0.0000 | 42.409 |
| V-S | GX011624.mp4 | 82.282 | 32.9128 | 30.000 |
| V-S | GX011625.mp4 | 498.431 | 199.3724 | 30.000 |
| V-S | GX011626.mp4 | 245.078 | 98.0312 | 30.000 |
| V-S | GX011627.mp4 | 22.723 | 0.0000 | 22.723 |
| V-S | GX011628.mp4 | 14.481 | 0.0000 | 14.481 |

Totals: V-S 26 items = 15 whole + 11 excerpts, 1694.493 source seconds and
671.910 planned input seconds. V-D 8 items = 2 whole + 6 excerpts, 2889.353 source
seconds and 228.748 planned input seconds. Planned GoPro inputs total 900.658 s.
All durations/start plans are read or calculated from the copied inventory only;
no live source duration or actual seek position was measured in the cell.

### Verification-loop record and yield

Suspected unrelated test setup failure -> confirmed by initial JUnit exception ->
fixed helper argument -> final JUnit confirms only 60 intended raising-stub failures.
Ruff style/regex findings -> confirmed -> fixed -> final ruff clean. Mypy clean.
No product-code fix or false-positive review finding is claimed. No agent judged
an image. Next rung is GREEN; this turn ends at the required committed-RED yield.


## Session 2 / Turn 3: GREEN

### Session boundary, scope and built behavior

Fresh session 2 starts at RED commit `10f1f70b`, with the task-3-only dispatch.
Session 1's supplied depth after turn 2 is 179,868; this session's ID and depth
remain for the dispatcher to read and fill. No depth estimate is made here.
The round-0 ruling is applied without a new interface or design ruling.

Implemented the five `tools/reviewpack/` modules:

- Selection is the exact 128-name commissioned catalog (64 / 9 / 26 / 8 / 17 /
  2 / 2 by group). The photo resolver refuses missing/ambiguous names, prunes
  directory links/junctions, and accepts only commissioned HEIC/JPG names.
  Videos retain the existing locator. IMG_6762.MOV is whole and last in V-P.
- The CLI supports `photos`, `clips [GROUP]`, `presets`, `page [--check]`,
  `tally SHEET`, and `all`, plus guarded config/manifest fixture controls.
  Direct script commands and the standalone module link checker work.
- Product correction runs only through the headless-export CLI, once per group
  and pose. Defaults are not overlaid except the required photo PNG depth and
  suffix; neutral is a separate photo invocation and record. The CPU switch is
  explicit and used only on planted test inputs. Product record names, numbered
  output names, exits, warnings, devices and allowlisted video facts are retained.
- Pack state and sheets are replaced atomically within guarded pack folders.
  Reruns use fresh runner-record, excerpt, pair and still names; product output
  collision names come from the runner record. Existing answers are preserved;
  a changed or no-longer-reviewable pair is refused before sheet replacement.
- Excerpts use input seek and all-stream copy, verify count/codec tags, match the
  first retained video packet hash back to the source PTS, and record planned and
  measured timings. A failed copy records whole-source fallback; an integrity or
  packet-identity mismatch is an instrument error, not a labelled successful copy.
- Viewing clips apply FFmpeg's default autorotation to both inputs, prove equal
  decoded display dimensions before hstack, halve each view, add the 2-pixel white
  separator, drop audio, and preserve source colour/rate tags. CPU pair encoding
  is limited to the explicit fixture flag; normal aids use HEVC NVENC.
  Unrotated stills reuse the shared extractor; rotated stills independently select
  exact rational PTS and confirm the decode's showinfo ticks/time base. Pair stills
  use matched PTS. ICC-bearing photos are converted to sRGB for JPEG derivatives;
  unprofiled photos receive no inferred transform. Video browser derivatives
  handle non-BT709 primaries explicitly. No source/product pixels are overwritten.
- Presets are installed into a fresh pack-local product store and exported by
  `PresetStore.export_preset`; exported empty parameter maps remain empty.
  The HTML shows effective schema defaults and the required AD-13 sentence.
- The page has separate groups, neutral/source and corrected labels, source-left
  viewing aids, linked product items of record, failure/refusal text, presets and
  D65 instructions. Local links are checked for existence and containment.
  Diagnostic text is ASCII-safe and scrubbed for paths/metadata; generated runner
  record failure/warning strings receive that same policy. HLG refusal text is
  preserved. Product failures and viewing-aid failures are accounted separately;
  incomplete aids are explicitly nonreviewable instead of silently entering tally.
- The CSV has the exact 13 columns. Its strict reader checks header/shape,
  commissioned identity, duplicate items, corrected-name association and allowed
  values. Numeric group/headline/candidate tallies count undecided as judged,
  count all marked artifacts and above-surface flags, and issue no quality verdict.

Only the owned instrument, owned test file and this ledger changed. Every one of
45 original RED functions (tests, fixture and helpers) is AST-identical to HEAD;
no original test assertion was changed. Nine additional regression/verification
functions add ten nodes. No test was declared wrong or weakened, and no separate
wrong-test correction step was needed. The turn bundles the commissioned GREEN
rung and its verification fixes as the dispatch requires one commit per turn.

### Commands and final evidence

Runner outputs are files below this worktree's `work/wp5.3/`. Commands are run
from the worktree root. The final shell removed only its inherited VIRTUAL_ENV
variable so uv no longer emits the main-environment mismatch warning; no config,
project environment selection or dependency file changed.

```powershell
$env:PYTHONPATH='scripts'
uv run pytest -q tests/test_reviewpack.py --basetemp=work/wp5.3/tmp -p sandbox_mkdir_shim -p no:cacheprovider -m 'not gpu and not footage and not gui and not fullclip' --durations=0 --junitxml=work/wp5.3/turn3-green-final.xml
uv run ruff check tools/reviewpack tests/test_reviewpack.py
uv run mypy
uv run python tools/reviewpack/build.py page --check --config work/wp5.3/tmp/test_all_tiny_set0/working/tiny.toml
uv run python tools/reviewpack/build.py tally work/wp5.3/tmp/test_all_tiny_set0/working/wp5.3/review-sheet.csv
uv run python -m tools.reviewpack.page --check --root work/wp5.3/tmp/test_all_tiny_set0/working/wp5.3
```

| Check | Exit / observed result | Evidence file |
|---|---|---|
| Final sandbox-shim pytest, slow node included | 0; `70 passed in 16.21s`; 0 failed/errors/skips in JUnit | `turn3-green-final.log`, `.xml`, `.exit` |
| Ruff on owned code/tests | 0; `All checks passed!` | `turn3-ruff-final.log` |
| Strict mypy, whole configured target | 0; `Success: no issues found in 151 source files` | `turn3-mypy-final.log` |
| Format application on owned code/tests | 0; formatting applied; dispatcher still owns format-check gate | `turn3-format-final.log` |
| Direct-script page link check on planted pack | 0; no unresolved links | `turn3-cli-link-check.log` |
| Direct-script tally on planted empty sheet | 0; `headline: 0/0 = 0.0 %  (D65 bar 80 %)`; candidates 0/0 | `turn3-cli-empty-tally.log` |
| Module page link check on planted pack | 0; no unresolved links | `turn3-module-link-check.log` |
| Scope / LF / AST / JUnit / planted privacy audit | 0; owned files only, zero CR, original assertions unchanged, docstrings present, no Qt imports, no planted absolute roots/GPS fields in page/sheet/records | `turn3-scope-lf-audit.log` |
| Diff whitespace check | 0 | `turn3-diff-check.log` |

The first GREEN execution was `60 passed in 16.75s` (`turn3-green-first.log` /
`.xml`): original slow node 13.32 s, maximum parallel call 1.54 s. Final times below
include JUnit setup/call/teardown, rounded to milliseconds. Every parallel node
stays below 5 s; no marker change is needed. There is exactly one slow node with
reason `runs the headless runner and FFmpeg`; there are no footage/gpu/gui/fullclip
nodes in this test file. These are informal fixture timings, not figures of record.

### Per-node results on the final candidate

| Node (tests/test_reviewpack.py) | Result | Seconds (JUnit) |
|---|---|---|
| `test_inventory_names_and_group_membership` | PASS | 0.001 |
| `test_items_resolve_exact_names_without_scene_classification` | PASS | 0.259 |
| `test_photo_resolver_case_insensitive_exact_commissioned_name` | PASS | 0.005 |
| `test_photo_resolver_missing_refusal` | PASS | 0.002 |
| `test_photo_resolver_ambiguous_duplicate_in_two_folders` | PASS | 0.003 |
| `test_photo_resolver_prunes_directory_junction_or_link` | PASS | 0.034 |
| `test_photo_resolver_refuses_uncommissioned_or_path_name[unknown]` | PASS | 0.002 |
| `test_photo_resolver_refuses_uncommissioned_or_path_name[path]` | PASS | 0.002 |
| `test_photo_resolver_refuses_uncommissioned_or_path_name[suffix]` | PASS | 0.002 |
| `test_excerpt_plan_boundaries_and_phone_rule[V-D-6.406-0.0-6.406-False]` | PASS | 0.000 |
| `test_excerpt_plan_boundaries_and_phone_rule[V-D-42.342-0.0-42.342-False]` | PASS | 0.000 |
| `test_excerpt_plan_boundaries_and_phone_rule[V-S-45.0-0.0-45.0-False]` | PASS | 0.000 |
| `test_excerpt_plan_boundaries_and_phone_rule[V-S-45.001-18.0004-30.0-True]` | PASS | 0.000 |
| `test_excerpt_plan_boundaries_and_phone_rule[V-D-1046.512-418.6048-30.0-True]` | PASS | 0.000 |
| `test_excerpt_plan_boundaries_and_phone_rule[V-Z-179.93-71.972-30.0-True]` | PASS | 0.000 |
| `test_excerpt_plan_boundaries_and_phone_rule[V-P-749.033333-0.0-749.033333-False]` | PASS | 0.000 |
| `test_excerpt_plan_boundaries_and_phone_rule[V-R-44.0-0.0-44.0-False]` | PASS | 0.000 |
| `test_excerpt_plan_rejects_invalid_duration[0.0]` | PASS | 0.000 |
| `test_excerpt_plan_rejects_invalid_duration[-1.0]` | PASS | 0.000 |
| `test_excerpt_plan_rejects_invalid_duration[nan]` | PASS | 0.000 |
| `test_excerpt_plan_rejects_invalid_duration[inf]` | PASS | 0.000 |
| `test_output_guard_refuses_footage_and_parent_escape` | PASS | 0.004 |
| `test_cli_refuses_working_folder_inside_footage_before_write` | PASS | 0.006 |
| `test_photo_runner_arguments_pin_pose_and_preserve_defaults[False]` | PASS | 0.005 |
| `test_photo_runner_arguments_pin_pose_and_preserve_defaults[True]` | PASS | 0.005 |
| `test_video_runner_arguments_use_checked_cache_and_explicit_cpu_only` | PASS | 0.005 |
| `test_record_mapping_uses_numbered_product_output_and_retains_failures` | PASS | 0.006 |
| `test_stream_copy_arguments_preserve_all_streams_and_seek_before_input` | PASS | 0.002 |
| `test_stream_copy_integrity_refuses_lost_stream_or_changed_tag[stream-count]` | PASS | 0.000 |
| `test_stream_copy_integrity_refuses_lost_stream_or_changed_tag[codec-tag]` | PASS | 0.000 |
| `test_actual_excerpt_start_uses_source_packet_not_rebased_zero` | PASS | 0.000 |
| `test_failed_stream_copy_falls_back_to_whole_source` | PASS | 0.046 |
| `test_rotation_adapter_extracts_oriented_fixture_dimensions` | PASS | 0.174 |
| `test_rotated_pair_autorotates_both_halves_with_equal_dimensions` | PASS | 0.541 |
| `test_pair_refuses_unequal_display_dimensions_before_hstack` | PASS | 0.393 |
| `test_sheet_header_rows_exclude_failed_refused_and_not_built` | PASS | 0.006 |
| `test_sheet_preserves_answers_when_later_groups_arrive` | PASS | 0.009 |
| `test_sheet_refuses_to_transfer_vote_to_regenerated_output` | PASS | 0.005 |
| `test_tally_empty_sheet_is_zero_judged_without_verdict` | PASS | 0.005 |
| `test_tally_filled_headline_candidates_artifacts_and_above_surface` | PASS | 0.004 |
| `test_tally_invalid_value_names_row[preferred-maybe]` | PASS | 0.004 |
| `test_tally_invalid_value_names_row[halos-no]` | PASS | 0.003 |
| `test_tally_invalid_value_names_row[above_surface-false]` | PASS | 0.004 |
| `test_tally_invalid_value_names_row[group-not-a-group]` | PASS | 0.004 |
| `test_tally_invalid_value_names_row[item-../secret]` | PASS | 0.003 |
| `test_tally_refuses_malformed_sheet[header]` | PASS | 0.003 |
| `test_tally_refuses_malformed_sheet[duplicate]` | PASS | 0.004 |
| `test_tally_refuses_malformed_sheet[extra-cell]` | PASS | 0.004 |
| `test_tally_refuses_malformed_sheet[missing-cell]` | PASS | 0.004 |
| `test_tally_cli_valid_scores_exit_zero_and_invalid_sheet_exit_two` | PASS | 0.008 |
| `test_page_planted_groups_labels_presets_and_name_only_links` | PASS | 0.535 |
| `test_page_escapes_refusal_text_instead_of_rendering_markup` | PASS | 0.005 |
| `test_page_check_detects_missing_escaping_and_nonlocal_links[missing]` | PASS | 0.018 |
| `test_page_check_detects_missing_escaping_and_nonlocal_links[escape]` | PASS | 0.008 |
| `test_page_check_detects_missing_escaping_and_nonlocal_links[nonlocal]` | PASS | 0.013 |
| `test_thumbnail_converts_embedded_p3_to_srgb_and_strips_other_metadata` | PASS | 0.035 |
| `test_thumbnail_without_icc_keeps_rgb_and_drops_text` | PASS | 0.011 |
| `test_pair_still_uses_source_left_corrected_right_and_separator` | PASS | 0.048 |
| `test_presets_export_product_starters_without_expanding_serialized_maps` | PASS | 0.029 |
| `test_all_tiny_set` | PASS | 11.697 |
| `test_direct_cli_help_runs_without_pythonpath[build]` | PASS | 0.284 |
| `test_direct_cli_help_runs_without_pythonpath[page]` | PASS | 0.263 |
| `test_sheet_refuses_stale_row_after_item_becomes_unreviewable` | PASS | 0.006 |
| `test_viewing_pts_uses_ticks_instead_of_rounded_decimal` | PASS | 0.116 |
| `test_stream_copy_success_records_a_matched_source_packet` | PASS | 0.206 |
| `test_rotated_frame_at_nonzero_pts` | PASS | 0.170 |
| `test_refused_fixture_is_recorded_without_a_review_row` | PASS | 1.058 |
| `test_tally_refuses_unrelated_corrected_filename` | PASS | 0.005 |
| `test_non_hlg_failure_in_refused_group_is_not_mislabelled` | PASS | 0.006 |
| `test_sheet_write_failure_preserves_original_answers` | PASS | 0.009 |


### Verification loop: suspect, independently confirm, fix, repeat

These are self-verification findings before Reviewer A, not reviewer rounds.
All six confirmed gaps are [major, in-envelope, NEW] relative to this instrument's
role in CP5 evidence; none is a product defect or an owner visual judgement.
There are no reopened findings or reverts. All fixes are instrument fixes with
regression additions; none is a test-only weakening.

| Item | Suspect and independent confirmation | Disposition / fix | Evidence |
|---|---|---|---|
| V-1 [major] CLI import path | Direct `build.py --help` exited 1 with ModuleNotFoundError; two subprocess tests with PYTHONPATH removed failed for build/page | Confirmed; bootstrap the tools package for direct-script and tools-module entry points | `turn3-cli-probe.log`; `turn3-verification-red.log` -> `turn3-verification-green.log` |
| V-2 [major] Rounded timestamps | Independent ffprobe integer ticks on vfr.mp4 gave 1001/30000; instrument returned 33367/1000000, which can select the next frame | Confirmed; use integer ticks times exact time base; rotated showinfo verification also compares exact ticks | Same RED/GREEN logs; nonzero rotated and real-copy verification nodes also pass |
| V-3 [major] Stale owner row | Planted existing yes row plus a now-failed item did not raise | Confirmed; refuse absent/nonreviewable pairs before touching the sheet | Same RED/GREEN logs; original sheet bytes preserved |
| V-4 [major] Unrelated corrected file | A safe basename from another commissioned item passed strict tally | Confirmed; validate association with the item's corrected export name, allowing actual collision/excerpt variants | `turn3-verification-second-red.log` -> final pytest |
| V-5 [major] Mislabelled refusal | A planted unrelated input-read error in V-R was incorrectly labelled refused | Confirmed; V-R is labelled refused only when the product's failure text identifies HLG; other errors stay failed | `turn3-verification-third-red.log` -> final pytest |
| V-6 [major] Interrupted sheet write | Independent injected partial write replaced the original owner's CSV bytes | Confirmed; guarded temporary sibling plus atomic replacement, with temporary cleanup; state JSON uses the same guarded replacement discipline | Same third RED log -> final pytest |

Rejected-as-false-positive suspicions: none claimed. Independent positive checks
also confirmed a real all-stream excerpt with a matched source packet, rotated
extraction at nonzero PTS, and the actual runner's HLG refusal reaching the page
with zero owner rows. Initial style/type findings were fixed (including optional
ICC return typing and a reused loop variable); final lint and mypy outputs above
are clean. The final requirement/code pass plus the full 70-node targeted rerun,
CLI checks and scope/AST/privacy audit found no new issue. Verification converged
for this GREEN rung; Reviewer A convergence is not claimed.

### Locks, deviations and yield

- No owner footage folder/file was opened or traversed by the cell; all media
  checks used planted inputs or committed fixtures. Sources remain byte-identical
  in the end-to-end test. The real build remains RUN REQUESTs at the dispatcher.
- No local configuration edit, main-tree work output, other worktree access,
  frozen-interface edit, product/helper edit, dependency change, Qt import,
  mailbox post or git mutation/commit occurred. All output guards use explicit
  pack/footage roots. No new OS-specific product code was introduced.
- No agent judged an image. Pixel/size assertions are mechanical fixture controls.
- No STOP, unresolved question, product defect or new design deviation is raised.
  The authorized round-0 amendments remain the only design departures from the
  original brief. Diagnostic redaction and atomic replacement implement its
  privacy/preservation locks; they do not change product exports.
- Full-suite/two-leg gate, dispatcher format-check, actual owner-media build,
  Reviewer A, Reviewer B and the final report are not run/claimed this turn.
  The report remains unwritten at the required pre-report yield boundary.
- Task 3 is ready for Reviewer A round 1 at the dispatcher's seat. No run request
  is issued ahead of that review boundary. Dispatcher fills this session's depth.

## Reviewer A round 1 (adjudicated)

### Candidate, transport and counted-round assertions

- Candidate independently checked: `f506b597`; initial worktree clean. Session 2 /
  turn 4 is adjudication ONLY. No implementation or test source changed.
  Dispatcher-supplied depth after turn 3: **142,467**; turn-4 depth remains for
  the dispatcher. Evaluation/stop thresholds remain about 200K/250K.
- Transport: `claude -p --model opus --effort high`, run by the dispatcher.
  Seat model `claude-opus-5-5`; requested effort high; exit 0; is_error false;
  38 turns; verdict NEW_CRITICAL_MAJOR_FOUND; worktree clean afterwards.
  The supplied seat log names no CLI version; none is inferred.
- The round COUNTS under the dispatcher's ruling. The seat log reports one
  permission denial (an inline ffprobe fixture loop), although the review's opening
  paragraph says no command was refused. Adopt the seat log's account. None of
  these findings rests on that denied loop. Own probes were not denied.
- The three external evidence files were read in place in the dispatcher's
  `wp5.3/r1/` evidence folder; none was copied into the repo. Reviewer baseline:
  70 passed in 16.51 s. Own shim baseline: **70 passed in 17.22 s**, exit 0;
  JUnit has zero failures/errors/skips.

Round counts: reviewer 0 critical / 3 major / 3 minor / 6 advisory, initially
11 in-envelope / 1 out. All severity grades are retained; F10 is additionally
outside the expressly supported invocation envelope. Final: **10 in / 2 out**;
12 NEW / 0 REOPENED; 0 reverts. Dispositions: 10 ACCEPTED (3 major, 3 minor,
4 advisory), F10 OUT/banked advisory, F11 REJECTED advisory (also outside the
commissioned colour tags). No remediation this turn. Planned fixes change
instrument behavior plus regression controls, not only tests, and never `src/`,
frozen interfaces or the headless runner.

### Own evidence and execution limits

All own probe scripts, media and output logs are in this worktree's ignored
`work/wp5.3/turn4-adjudication/`. Inputs were committed fixtures and planted copies;
the owner footage folder was not opened/listed/probed. No image was judged.

- `probes.py` / `probes.log` exercise F1-F12 on the unchanged candidate. The final
  assertion expected F11's claimed failure; it exited 1 because FFmpeg SUCCEEDED.
  This false hypothesis remains in the log. `F11-followup.py` / `.log` independently
  prove alias equivalence with a saturated testsrc2 positive distinction; exit 0.
  This is a failed probe expectation, not a failing product/test-suite result.
- Each external command has separate stdout/stderr files. The actual tmcd mux
  failure is in `F1-literal.stderr.log`; the literal/candidate product records are
  in the planted pack's records folder. Only names and selected technical facts
  are brought into this ledger, not paths or owner metadata.
- The first two successful product controls used `--force-cpu`. Their records
  identify processing as `CPU: forced` but encoding as **hevc_nvenc**. This is
  disclosed in `encoder-audit.log`: force-cpu does not promise software encoding.
  The baseline uses the same authorized tiny-fixture path. The direct F3 NVENC
  pair command was intercepted before encoding. To isolate excerpt acceptance
  from encoder choice, both positive controls were rerun with the existing
  `--encoder libx265` flag and fresh outputs/records: both exit 0, done, encoder
  libx265 (`software-controls.py` / `.log`). No real-media/heavy GPU job was run.
- `ffmpeg-version.log`: installed `9.0.2-full_build-www.gyan.dev`.
  `nvenc-help.log`: installed defaults include preset p4, rc -1 and cq 0 automatic.
  F3's 2M default was also checked against primary upstream
  [FFmpeg encoder defaults](https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/libavcodec/nvenc_hevc.c#L193).
  This establishes the upstream default, not the measured bitrate or quality of
  an encoded pair on this seat. No artifact judgement is inferred from it.

### F1-F12 adjudication

| Finding | Verdict / severity / envelope | Own basis | Disposition / fix plan |
|---|---|---|---|
| F1 | ACCEPTED MAJOR, in-envelope; STOP for brief mismatch | EXECUTED: planted HEVC + AAC + tmcd source made by copying the committed fixture. prepare_excerpt(0.6, 0.5) returns excerpt=False, whole duration 1.5015 s. Literal copy fails with `Could not find tag for codec none in stream #2`. Scratch regeneration candidate preserves the stream-roster multiset and passes both product encoder controls. | Conditional RED and fix below; selective mapping/regenerated tmcd changes the literal brief and requires CHARC's ruling. |
| F2 | ACCEPTED MAJOR, in-envelope, introduced excerpt/product mismatch | EXECUTED: literal successful copy has 33 packets, first PTS -0.600600 / KD_, but only 15 displayed frames. Recorded actual_start_s=0.0 names discarded pre-roll; displayed head is source 0.6006. Product exits 1 with the trim-edit-list refusal. Scratch make_zero candidate decodes 33 frames and passes both product encoder controls. | RED and in-envelope timestamp fix below; never change the product's edit-list refusal. |
| F3 | ACCEPTED MAJOR, in-envelope | REASONED quality consequence, with EXECUTED command inspection: GPU hstack branch specifies hevc_nvenc but no b:v/cq/rc/preset/qp/crf. Installed quality defaults are automatic; primary upstream b default is 2M. Actual artifacts/bitrate were not measured or visually judged. | RED and explicit viewing-aid quality plan below; product runner defaults remain unchanged. |
| F4 | ACCEPTED MINOR, in-envelope, BOM only | EXECUTED: a valid one-row UTF-8-BOM sheet raises the header error; the plain UTF-8 control tallies. cp1252 with a non-ASCII note raises UnicodeDecodeError, outside the UTF-8 contract. | Terminating cleanup: read with utf-8-sig at sheet.py:36; continue writing UTF-8 and rejecting non-UTF-8. Add BOM tally/preservation control; no cp1252 auto-detection. |
| F5 | ACCEPTED MINOR, in-envelope | EXECUTED: one yes row prints headline 1/1 = 100.0 %, with no expected/available/missing fields despite the 115-item commissioned headline. Prescribed preferred/judged arithmetic is correct; coverage is absent. | Terminating cleanup at sheet.py:128-187: add catalog-derived available/expected/missing/unjudged counts, plus a coverage line; preserve the prescribed headline line and judgement-free arithmetic. |
| F6 | ACCEPTED MINOR, in-envelope | EXECUTED: a generated valid done photo item carries a warning sentinel in data but the HTML omits it. | Terminating cleanup at page.py:117-146: display escaped warning text beside the item, with a markup-bearing warning control. Retain existing diagnostic privacy policy. |
| F7 | ACCEPTED ADVISORY, in-envelope, numeric consistency gap | EXECUTED: grey128 with smpte432/bt709 becomes (121,121,121); bt709/bt709 remains (128,128,128). Both halves use the same path; this does not demonstrate preference bias. Pair-clip perceptual mismatch was not judged. | FIX once in terminating cleanup at build.py:743-777: apply one explicit primary/transfer policy consistently to tagged SDR inputs, with neutral/colour controls. Keep untagged/no-inferred-profile behavior. |
| F8 | ACCEPTED ADVISORY, in-envelope | EXECUTED: one successful unrotated extraction leaves one empty .frames-* directory after the PNG is moved. | FIX once in terminating cleanup at build.py:440-447: guarded cleanup of the instrument-owned extraction directory after moving its known file; never remove unrelated files. |
| F9 | ACCEPTED ADVISORY, in-envelope | EXECUTED: VFR fixture has 30 frames with intervals 0.03337 / 0.06673 s; software pair has 30 frames with only 0.04449 s intervals. CFR forcing changes timing even when frame count stays the same. No judder/flicker was visually judged. | FIX once in terminating cleanup at build.py:561-562: remove -r forcing, use passthrough timing and explicit filter time base; assert source-relative PTS against the CPU VFR pair. |
| F10 | OUT OF ENVELOPE, nominal ADVISORY; BANKED | EXECUTED: runner argument is relative, exists from the worktree root and does not exist from the alternate planted cwd. Dispatch expressly requires RUN REQUESTs runnable from the worktree root; that supported execution passes baseline. | No current fix. Bank with instrument maintainer/CHARC; trigger: a future commission supports execution outside the worktree root. This is introduced code, not a pre-existing-code dismissal. |
| F11 | REJECTED ADVISORY; nominal trigger also OUT OF ENVELOPE | EXECUTED refutation: raw bt470bg scale succeeds. On saturated testsrc2, its RGB bytes equal shared-helper bt470 and differ from bt709 (positive distinction). Inventory matrices are bt709/smpte170m anyway. | DECLINE; no fix/debt for the refuted failure claim. git log -S identifies f506b597 as origin; not dismissed as pre-existing. No generic colour-format expansion. |
| F12 | ACCEPTED ADVISORY, in-envelope | EXECUTED HTML inspection: two alt labels Source/Corrected, zero figure captions. The global left/right sentence and neutral-source link exist; this is local-label usability, not mispairing. | FIX once in terminating cleanup at page.py:131-135: add visible adjacent Source/Corrected captions; keep alt text and ordering; assert local visible labels. |

### Blocking RED roster and bounded remediation plan (not implemented)

1. **F1, conditional on ruling:** new node
   `test_gopro_tmcd_excerpt_preserves_stream_roster_without_whole_fallback`.
   Plant the committed HEVC/AAC fixture with FFmpeg's timecode track; add a gpmd
   payload-copy control if required by the ruling. Assert excerpt=True, no whole
   fallback, equal count/type/codec/tag roster, non-tmcd packet identity, and source
   bytes unchanged. Fix `build.py:282-331`, `:362-418`: selective non-tmcd mapping,
   authorized regeneration, integrity verification by stream identity (allow mux
   reordering). Nonzero source-interval timecode adjustment also needs a control;
   the current fixture's retained start is zero and does not prove that case.
2. **F2:** new fast node
   `test_stream_copy_command_rebases_preroll_for_product` asserts make_zero on the
   non-keyframe plan. Extend the existing sole slow `test_all_tiny_set` with a
   non-keyframe excerpt fed through the real runner: assert exit 0 and displayed
   first-source-frame identity equals recorded actual_start_s. Preserve all
   existing assertions and the one-slow-node rule. Fix `build.py:282-314`,
   `:334-418`: `-avoid_negative_ts make_zero`, plus independent displayed-start
   verification before recording actual start. No product policy change.
3. **F3:** new node `test_gpu_pair_has_explicit_quality_control`: use a small
   fixture pair, execute the real command-construction branch but intercept
   hstack before GPU execution; assert explicit p5/hq/VBR/CQ20/b:v=0 rather than
   an implicit rate target. Fix options at `build.py:537-576`. CQ20/p5/hq already
   appears in the repository's WP1.5 container-spike recipe; this is viewing-aid
   encoding only. A later scheduled synthetic NVENC control must verify the
   options take effect before real clips. No GPU window requested this turn.

### STOP: F1 scope ruling required before remediation

**Recommended answer first:** CHARC grant an instrument-local amendment to Q3 /
design step 1: map/copy video, audio and non-tmcd data; regenerate tmcd through
FFmpeg's timecode writer; verify stream count/codec tags and non-tmcd packet
identity by stable stream identity rather than mux order. Require regenerated
timecode to correspond to the actual selected source interval. Retain whole-input
fallback for genuinely failed copies. Combine with F2's tested make_zero
normalization and displayed-start verification. No source pixel re-encoding or
product/interface edit is proposed.

Evidence: WP1.5 container-spike report lines 229-233 records the tmcd-copy refusal
and regeneration mechanism. WP-T6 gate-sizing report lines 193-204 independently
uses non-tmcd mapping plus write_tmcd, compares stream identities across mux order
and records video/audio/tmcd/gpmd. These are precedents, not authorization to alter
this package's literal `-map 0 -c copy` contract. Scratch candidates show planted
feasibility only. No universal claim is made that EVERY live GoPro contains tmcd,
and the reviewer's 12-hour/disk forecasts were not measured here. The proven
conditional failure is sufficient to stop silently relying on the excerpt-sized
workload. If regeneration is not granted, CHARC must explicitly approve the
whole-clip workload/disk/schedule alternative or another selection design.

F2 is an induced bad-input mismatch, not a product defect to fix. Independent
`git log -S 'an edit list whose media segment starts'` identifies `af11d782`,
WP3.10 round-2 #2, as the deliberate product guard's origin. Likewise,
`git log -S 'in_color_matrix={tags.color_space}'` identifies `f506b597` for F11's
introduced instrument expression. No finding was dismissed with unsupported
pre-existing provenance.

### Light command and yield

Own baseline used `PYTHONPATH=scripts uv run pytest -q tests/test_reviewpack.py
--basetemp=work/wp5.3/turn4-adjudication/tmp -p sandbox_mkdir_shim
-p no:cacheprovider -m "not gpu and not footage and not gui and not fullclip"
--junitxml=work/wp5.3/turn4-adjudication/baseline.xml` (PowerShell set PYTHONPATH
before invocation). Output/status files: baseline.log / baseline.exit. Result:
70 passed in 17.22 s, exit 0; no skipped/error/failure nodes. No full-suite gate,
format gate, new reviewer or real-media build was run. Probes are ignored scratch
evidence, not added tests or implementation remediation.

The main probe's false F11 expectation, successful follow-up and actual product
encoder choices are disclosed above. No mailbox, git mutation/commit, local-config
edit or other-worktree access occurred. Only this owned ledger changes for the
dispatcher. No RUN REQUEST is issued. Turn 4 YIELDS with the F1 STOP; turn-5 RED /
remediation waits for CHARC's complete ruling packet. Accepted minors/advisories
remain queued for the terminating round's single cleanup and do not drive rounds.

## Turn 5: Reviewer A round 1 remediation

### Ruling, boundary and depth

- Start HEAD `abeef516`: the instrument matches `0553d317` / `f506b597`; the
  additional commit carries CHARC's complete F1 ruling in the brief. The ruling
  was read before tests or implementation. It authorizes timecode regeneration
  and WITHDRAWS the whole-source fallback. No product/interface edit is needed.
- Turn-4 depth supplied by the dispatcher: **36,709** input tokens. Preserve
  the prior supplied 142,467 after turn 3 as well. The numbers decrease, but this
  cell has no independent depth counter and does not infer a cumulative total.
  Turn-5 figure remains for the dispatcher. No new estimate is made.
- This turn bundles the three blocking fixes and the expressly dispatched single
  cleanup (F4-F9, F12); F10 receives Limit text and F11 remains rejected. Reviewer
  A round 2 is the dispatcher's next step, not a new review run by this cell.

### RED before instrument changes

Only `tests/test_reviewpack.py` changed before both RED runs. All runner output
and JUnit evidence lives in ignored `work/wp5.3/turn5/`; no external review files
were copied into the repository. The shim is enabled for every pytest command.

Exact command pattern (PowerShell first sets `PYTHONPATH=scripts`):

```text
uv run pytest -q tests/test_reviewpack.py --basetemp=work/wp5.3/turn5/red-tmp -p sandbox_mkdir_shim -p no:cacheprovider -k "gopro_tmcd or excerpt_copy_failure or stream_copy_command_rebases or excerpt_recorded_start or gpu_pair_has or page_names_viewing or failed_stream_copy_never or all_tiny_set" --durations=0 --junitxml=work/wp5.3/turn5/red.xml
```

Result: exit 1, **9 failed / 68 deselected in 29.29 s** (`red.log`, `red.exit`).
The following lines are the failing assertion/call lines AT RED, before format
and subsequent fixture/control additions; final node definition lines differ.
Every ID below has prefix `tests/test_reviewpack.py::`.

| Finding | RED node suffix | RED line | Distinguishing observation |
|---|---|---|---|
| F1 | test_failed_stream_copy_never_falls_back_to_whole_source | 551 | Old implementation returns the whole source path instead of None. |
| F1 | test_gopro_tmcd_excerpt_preserves_stream_roster_without_whole_fallback[0.6-0.0-01:00:00:00] | 1160 | Literal tmcd copy fails and returns excerpt=False. |
| F1 | test_gopro_tmcd_excerpt_preserves_stream_roster_without_whole_fallback[2.1-1.5015-01:00:01:15] | 1160 | Same failure at a later source interval. |
| F1 | test_excerpt_copy_failure_is_recorded_skipped_and_exits_nonzero | 1201 / 1196 | Failed copy reaches the subsequent clip/runner boundary. |
| F2 | test_stream_copy_command_rebases_preroll_for_product | 1219 | make_zero absent. |
| F2 | test_excerpt_recorded_start_is_first_displayed_frame | 1234 | Decoded first-frame MD5 differs from the recorded source start. |
| F2 | test_all_tiny_set (extended existing sole slow node) | 978 | Unmodified product refuses the planted non-keyframe excerpt. |
| F3 | test_gpu_pair_has_explicit_quality_control | 1254 / 1249 | Real GPU command lacks explicit preset/quality controls. |
| F3 | test_page_names_viewing_aid_quality | 1259 | Generated page does not name NVENC/CQ quality. |

The old fallback test was renamed and its fallback expectations explicitly
replaced in a named **contract amendment step**, because the committed F1 ruling
withdraws that behavior. No original RED assertion was weakened to obtain green.
The existing slow node retains all original assertions and gains a real-runner,
explicit-libx265 excerpt-acceptance control.

Cleanup RED used the same command with `--basetemp=work/wp5.3/turn5/cleanup-red-tmp`,
`--junitxml=work/wp5.3/turn5/cleanup-red.xml` and
`-k "stream_identity_validation or bom_sheet or partial_set_coverage or escaped_warnings or cleans_owned or browser_sdr or variable_presentation"`.
Result: exit 1, **7 failed / 77 deselected in 5.46 s** (`cleanup-red.log`).
RED lines: mux-reordering 1268; BOM 1275; coverage 1285; warnings/captions 1295;
temporary-directory cleanup 1305; browser transfer 1316; VFR intervals 1329.
These are observed behavioral failures, including the expected header/coverage
exceptions, not collection or fixture errors.

### Per-finding remediation and envelope

All fixes below change the **product of this instrument plus tests**, not only
tests; none changes Clearwater product code, helpers, fixtures or frozen APIs.
Anchors refer to the final turn-5 source.

| Finding | Fix / final control |
|---|---|
| F1 MAJOR | build.py:283 stream_copy_command maps each non-tmcd stream, copies payloads and regenerates tmcd with an advanced source tag and write_tmcd=1. prepare_excerpt at :492 verifies the roster multiset, matches stream identities and ordinals, verifies contiguous retained SHA256 payload sequences for video/audio/gpmd, checks regenerated video/tmcd tags and the displayed source start. Failed copy/validation returns path=None and excerpt_failed; partial excerpt removed. _build_groups at :1011 records group excerpt facts in V-S-excerpts.json (likewise other groups), persists failed pack rows, skips all downstream pieces for that item and continues later groups. CLI clips/all exits 1 after accounting; page lists Not built. The forced-failure control also runs a later real HLG-refusal group and proves no failed input reached the runner. Real tmcd/gpmd controls plus three injected payload-corruption controls prove preservation and loud rejection; source bytes stay unchanged. |
| F2 MAJOR | build.py:283 adds avoid_negative_ts=make_zero. _displayed_start at :461 joins the first decoded frame to its retained packet by file position, checks it is the earliest retained video PTS, then verifies its payload against the probed source seek keyframe. A repeated payload is constrained by the independently probed keyframe timestamp rather than arbitrarily matched elsewhere. First decoded-frame MD5 and real product acceptance pass. |
| F3 MAJOR | make_pair at build.py:667 sets hevc_nvenc p5/hq, VBR CQ20, b:v=0 explicitly. Generated page names those viewing-aid settings; product runner settings remain defaults. GPU command inspected at the encoder boundary without executing that pair encode; actual NVENC pair quality is not judged or measured. |
| F4 MINOR | sheet.py:36 reads utf-8-sig, retaining strict UTF-8 and existing write encoding. BOM tally and Unicode owner-answer preservation control passes. No cp1252 inference added. |
| F5 MINOR | sheet.py:128 tally adds catalog-derived expected/available/missing/unjudged fields for every group, headline and candidates. format_tally at :163 adds a coverage line and preserves the mandated preferred/judged headline verbatim. Partial-sheet control expects 115/2/113/1. |
| F6 MINOR | page.py:65 write_page displays escaped per-item warnings, with a markup-bearing sentinel control. Existing diagnostic sanitization remains in force. |
| F7 ADVISORY | build.py:926 _browser_frame applies explicit primaries/transfer-to-sRGB conversion to both BT709 and other fully tagged SDR inputs. Untagged inputs keep the no-inferred-transform branch. Neutral128 controls for BT709 and P3 both produce121. This is a numeric consistency check, not image judgement. |
| F8 ADVISORY | build.py:593 extract_view_frame cleans its unique owned extraction folder in finally, removing only helper PNGs after guarded checks and removing the folder only when empty. Success control proves no empty directory remains. |
| F9 ADVISORY | make_pair uses passthrough timing, the source's exact rational filter time base and encoder time base=filter; removes the average-rate forcing. Real software pair has exactly the source's relative VFR PTS sequence, not just matching frame count. |
| F10 OUT / ADVISORY | BANKED Limit: generated page says invocation is supported from the worktree root. Trigger for reconsideration remains a future commission supporting another cwd. No runner-resolution expansion. |
| F11 REJECTED / ADVISORY | No change. Turn-4 executed alias controls remain the basis; no unsupported codec/colour expansion. |
| F12 ADVISORY | page.py adds adjacent visible Source/Corrected figcaptions while preserving alt text, ordering and relative links. Escaping/caption control passes. |

### Verification loop: suspect / independently confirm / fix / repeat

1. **Confirmed and fixed (implementation):** first full run `green1.log` was
   81 passed / 3 failed in 44.15 s. Two tmcd controls exposed repeated packet
   payloads in the looped fixture; independent `diagnose.log` confirmed ambiguous
   global hash matches. Bind the displayed hash to the probed seek keyframe.
   VFR control exposed microsecond rounding from AVTB (33367/1000000 instead of
   1001/30000); keep the source time base exactly. No assertion relaxed.
2. **Confirmed and fixed (fixture, named separate step):** `focused2.log` was
   2 passed / 1 failed. The looped audio/video input's format duration was
   1.522833 s, so stream_loop put its second keyframe there rather than the
   hand-planned 1.5015 s video duration. This was a faulty planted input, not a
   faulty timecode assertion. A copy-only video remux before looping makes the
   keyframe interval exactly 45 frames; independently probed later keyframe and
   timecode now satisfy the ORIGINAL 1.5015 / 01:00:01:15 assertions.
   `focused3.log`: 2 passed in 1.53 s.
3. **Confirmed and fixed (mechanical):** initial lint reported 10 formatting/style
   findings; initial mypy reported two variable-length tuple-key annotations.
   Correct annotations/style and format owned files. `ruff2` and `mypy2` clean.
4. **No new issue:** full `green2.log`: 87 passed in 35.95 s. Added five small
   independent one-frame timecode-boundary controls (non-drop, 29.97 and 59.94
   drop-frame, tenth minute, day rollover) to cover the new arithmetic's remaining
   unexercised branches. No additional implementation change was necessary.
5. **Full final pass found nothing new:** final 92-node run, static checks,
   owned-file diff/docstring/comment/privacy review and byte checks. No new
   behavior finding, false-positive dismissal, revert, product defect or pending
   scope question. Existing rejected F11 and banked F10 keep their classifications.

### Final light runs and AD-30

```text
PYTHONPATH=scripts uv run pytest -q tests/test_reviewpack.py --basetemp=work/wp5.3/turn5/final-tmp -p sandbox_mkdir_shim -p no:cacheprovider -m "not gpu and not footage and not gui and not fullclip" --durations=0 --junitxml=work/wp5.3/turn5/final.xml
uv run ruff check tools/reviewpack tests/test_reviewpack.py
uv run ruff format --check tools/reviewpack tests/test_reviewpack.py
uv run mypy
```

- Final pytest: **92 passed in 30.22 s**, exit 0; JUnit: 92 nodes, zero failures,
  errors or skips. Exactly one existing slow node; no new slow/fullclip/footage/GPU
  marker. `final.log`, `.exit`, `.xml` retained. Product processing is force-CPU
  in the tiny all-stage control; its auto encoder may still use NVENC as already
  disclosed in turn 4. The added real excerpt acceptance control pins libx265.
- `per-node-final.csv` records all 92 node statuses and elapsed seconds (JUnit
  setup/call/teardown aggregate), generated from final.xml. `summary.log` records
  all RED node/line joins, run counts, final timings and command exit statuses.
  Slow integration: **19.580 s**; maximum other node: forced-failure/later-group
  continuation **1.373 s**. Every parallel-leg node remains under 5 s.
- Delta controls (seconds): tmcd start0 **0.516**, later start **0.560**;
  failure/skip/continue **1.373**; pre-roll command **0.004**; decoded-head
  identity **0.385**; GPU command **0.460**; quality page **0.007**; reordered
  roster **0.000**; three payload-corruption controls **0.337/0.332/0.383**;
  five timecode boundaries **0.000-0.001**; BOM **0.016**; coverage **0.007**;
  warnings/captions **0.010**; temporary cleanup **0.194**; SDR consistency
  **0.125**; VFR **0.812**. The unchanged and extended original nodes' individual
  results are in the same per-node file.
- Final ruff: **All checks passed**, exit 0 (`ruff-final.log/.exit`). Owned-file
  format check: **6 files already formatted**, exit 0
  (`format-check-final.log/.exit`). Final mypy: **Success: no issues found in
  151 source files**, exit 0 (`mypy-final.log/.exit`). Whole-tree format/two-leg
  gate remain the dispatcher's responsibility; neither is claimed here.
- LF byte checks: 0 CR in all changed source/test files; final ledger/diff checks
  are recorded before return. No new dependency, product/helper/interface/config
  edit, footage access, other-worktree access, git mutation/commit, mailbox post,
  image judgement or real-media RUN REQUEST. Only the five owned files listed
  in the return report change. The final report remains at its later yield.

Turn 5 yields for Reviewer A round 2. No STOP remains under the complete ruling.
