# WP5.3 cumulative ledger

## Dispatch and state

- Package: WP5.3, CP5 visual review pack; Codex implementer lane, STRONG.
- Verified base and current HEAD at round 0: `2050a89a`; initial tracked diff empty.
- Turn 1 is task 1 only. No instrument or test code is written this turn.
- State: **Reviewer A CONVERGED at round 4; executing Reviewer B returned
  NO_NEW_CRITICAL_MAJOR on `2a1e15b1`; turn 11 remediated B-F1/B-F2 and turn 12
  completes the conflict display, with a STOP on failed-excerpt cleanup**.
  Real-build RUN REQUESTS and the final two-leg gate remain at the dispatcher.
  Round 1 remediation is committed as `03731250`.
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
| A2 (session 2 / turn 6 adjudication; session 3 / turn 7 remediation) | 0 / 1 / 4; 8 advisory | 11 / 2 | 12 / 1 by distinct finding; F1 NEW path reopens R1 F1 pattern, A1 repeats rejected R1 F11 | 0 | turn 7: seven accepted instrument behavior fixes and regression controls; zero src/ or frozen-interface changes | Counted claude -p pass; F1-F5 and A3/A7 FIXED under CHARC 0358beda; A2/A5/A6 BANK; A1 REJECT; A4/A8 DECLINE code change; ready for A3, not converged | turn 5: 142,541; turn 6: 198,059; turn 7 dispatcher pending |
| A3 (session 3 / turn 8 adjudication; session 4 / turn 9 remediation) | 0 / 1 / 3; 3 advisory | reviewer: 6 / 1; effective: 7 / 0 under c25ff7a9 R3-3 | 5 NEW / 2 REOPENED distinct findings; F1/F2 also REOPEN silent-loss class | 0 | turn 9: F1-F6 instrument fixes and 13 regression nodes; F7 display documentation; no src/ or interface change | Counted claude -p pass; remediated under c25ff7a9; state audit finds no fourth shrinking path; ready for A4, not converged | turn 7: 143,373; turn 8: 182,934; turn 9: 140,647 |

| A4 (session 4 / turn 10, terminating clean-up) | 0 / 0 / 4; 6 advisory | reviewer nominal 7 / 3; effective 8 / 2 under e4d56665 (R4-9 IN) | 10 NEW / 0 REOPENED distinct findings; R4-1 diagnostic-sidecar loss, not another state-of-record loss | 0 | Six instrument behavior fixes; R4-8 coverage-only; R4-10 and Limits documented; no src/ change | NO_NEW_CRITICAL_MAJOR, CONVERGED at round 4 by CHARC; terminating clean-up verified; executing Reviewer B next | turn 9: 140,647; turn 10 dispatcher pending |
| B (session 5 / turn 11 remediation) | 0 / 0 / 1; 5 advisory | 5 IN / 1 OUT (B-F5) | 6 NEW / 0 REOPENED | 0 | Two instrument fixes plus 14 regression/coverage nodes; write-audit corrections; no product or existing-test change | EXECUTED at dispatcher, NO_NEW_CRITICAL_MAJOR; B-F1/F2 fixed, F3 corrected, F4 measured, F5/F6 Limits staged; YIELD for RUN REQUESTS | session 4 retired at 217,380; turn 11 dispatcher pending |

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
| Session 2 / turn 5 / A1 remediation | same session 2 | 142,541 | Dispatcher supplied in turn 6; remediation committed as 03731250. Session window 475,000; evaluate near 200K and stop near 250K remain binding. |
| Session 2 / turn 6 / A2 adjudication | same session 2 | 198,059 | Dispatcher supplied at turn 7; session 2 retired at the evaluation boundary before multi-finding remediation. |
| Session 3 / turn 7 / A2 remediation | fresh session 3; dispatcher to fill ID | 143,373 | Dispatcher supplied at turn 8; remediation committed ed787934, all five blobs 0 CR; seat format check 293 files clean. |
| Session 3 / turn 8 / A3 adjudication | same session 3 | 182,934 | Dispatcher supplied at turn 9; ledger committed a14a25ed; session 3 retired at the evaluation boundary before seven-item remediation. |
| Session 4 / turn 9 / A3 remediation | fresh session 4; dispatcher to fill ID | 140,647 | Dispatcher supplied at turn 10; committed de884f7d; A4 converged, terminating clean-up commissioned under e4d56665. |
| Session 4 / turn 10 / A4 terminating clean-up | same session 4 | 217,380 | Dispatcher supplied at turn 11; committed 2a1e15b1; session 4 retired. Reviewer B executed and returned NO_NEW_CRITICAL_MAJOR. |
| Session 5 / turn 11 / Reviewer B remediation | fresh session 5; dispatcher to fill ID | dispatcher pending | B-F1/B-F2 RED/GREEN, verification and write-audit correction; YIELD for dispatcher-run real build. |
| Session 5 / turn 12 / B-F1 completion | same session 5 | dispatcher pending | Conflict page/stderr pair identities completed; STOP for ruling on existing failed-excerpt cleanup versus blanket deletion ban. |

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

## Reviewer A round 2 (adjudicated)

### Candidate, transport, depth and round accounting

- Candidate: **03731250**, independently checked; initially clean. This is
  session 2 / turn 6, adjudication ONLY. No test or implementation edits.
- Dispatcher supplied turn-5 depth **142,541** (window 475,000). Recorded without
  revising the earlier supplied figures. Evaluate around 200K, stop at a step
  boundary near 250K. Turn-6 depth is for the dispatcher to fill.
- Transport `claude -p --model opus --effort high`, run by the dispatcher.
  Seat log: exit 0; model claude-opus-5-5; requested high effort; is_error false;
  37 turns; VERDICT NEW_CRITICAL_MAJOR_FOUND; worktree clean afterwards. No CLI
  version is named in that log, so none is inferred. Two permission denials are
  recorded; the findings identify no denied command or dependency on one.
  The round COUNTS under the dispatcher's explicit ruling.
- External review.txt, review-prompt-r2.md and review.seat.log were read in
  place in the dispatcher's wp5.3/r2 evidence folder, never copied into the repo.
  Reviewer ran the light tests FIRST: 92 passed in 31.23 s, slow node included;
  its ruff/format/mypy checks were clean. Dispatcher also reported whole-tree
  ruff/format (293 files), mypy (151) and LF checks clean on this candidate.

Counts retained: **0 critical / 1 major / 4 minor / 8 advisory**, 11 in-envelope /
2 nominally out (A1, A2); 0 reverts. Seven accepted findings (F1-F5 plus A3/A7);
A2 out/banked, A5/A6 banked, A1 rejected, A4/A8 declined as code changes.
F2/F3/F5 have narrowed accepted premises, as detailed below. No fix this turn;
planned fixes change instrument behavior and tests, never product `src/`, frozen
interfaces, dependencies or the runner.

**NEW versus REOPENED:** 12 NEW distinct findings / 1 REOPENED finding (A1 repeats
the R1 F11 matrix-alias claim, again refuted). F1 DOES reopen R1 F1's silent-loss
PATTERN in a new path. It is a NEW blocking defect in the finding column: R1 F1
was failed excerpt -> whole-source fallback; R2 F1 is successful product export
-> failed viewing aid -> unreviewable row with success exit. Its post-export
exception branch existed unchanged at f506b597; no earlier aid-failure repair or
RED control has regressed. The repaired excerpt path still behaves as ruled.
This distinction is explicit so the dispatcher can assess recurrence without
counting an unchanged, previously unexamined arc branch as a pre-existing external
defect. A3 likewise concerns orphaned aid artifacts after a later failure, beyond
R1 F8's repaired empty helper-directory path.

### Own probes, provenance and execution limits

All own scripts/media/logs are in ignored **work/wp5.3/turn6/** inside this
worktree. Inputs are committed fixtures and planted copies only. No owner footage
folder was read/listed/probed, no main-tree work path or other worktree accessed,
and no image was judged.

- `probes.py` / `probes.log`: independently executes F1-F5 and A1, then stops on
  an incorrect A2 probe expectation. Invalid ICC bytes raised OSError (caught by
  the instrument), whereas the probe expected PyCMSError. Exit 1 is retained and
  disclosed; it is a false probe assumption, not a new product/test-suite failure.
- `probes-followup.py` / `.log`: independent A2 controls plus A3-A8, exit 0.
  Invalid bytes again produce caught OSError; a structurally valid LAB ICC profile
  attached to RGB pixels produces uncaught PyCMSError, confirming the narrower
  out-of-envelope condition. No source change was made to get that result.
- F1 runs real headless export on the tiny HEVC fixture, then injects only a
  make_pair failure. A wrapper adds the EXISTING --encoder libx265 flag to this
  probe's force-CPU invocation; the resulting record says done/libx265. No direct
  engine composition and no GPU pair encode. The source remains a planted file.
- `f4-real.py` / `.log`: confirms F4 with a real V-P export and all its CPU viewing
  aids after an old planted V-S excerpt_failed row. V-P is done and reviewable,
  but command returns 1 solely because of V-S. Probe again explicitly selects
  libx265 through the runner; exit 0 of the probe means its assertions held.
- A3 actually completes a software pair and extracts two PNG stills, then injects
  failure at the second browser conversion. The three orphaned files remain.
  A5 creates only a 3 s, 160x90 synthetic open-GOP HEVC using software encoding;
  its excerpt fails loudly with no whole-source substitution. This proves the
  conditional mechanism, not the GOP form or failure rate of any owner file.
- `origins.py` / `.log`: git log -S, with literal arguments rather than shell
  quoting, attributes aid-state handling, raw matrix interpolation, ICC conversion
  and sheet writing to **f506b597**; excerpt_failed and displayed-start guards to
  **03731250**. The runner's cancellation states originate at **f0786c7b**.
  All challenged instrument paths are introduced by this arc; none is dismissed
  as pre-existing. Product states and metadata policy are read-only constraints.

### Per-finding adjudication

| Finding | Verdict / severity / envelope | Own evidence | Planned disposition |
|---|---|---|---|
| F1 | ACCEPTED MAJOR, in | EXECUTED: real product result done/libx265; injected pair failure sets reviewable=False and aid_message. clips and page both return0; sheet has0 rows; item absent from Not built. Product link and group-level Viewing aid note DO remain visible, and tally coverage reports expected115/available0/missing115. This is false success/incomplete accounting, not a proved preference arithmetic error or total disappearance from HTML. | Blocking RED and bounded plan below. Keep the product's done fact, make the review failure explicit and loud, preserve required headline arithmetic and missing coverage. |
| F2 | ACCEPTED MINOR in for BOM; CP1252 claim narrowed | EXECUTED: BOM True before page rebuild, False after; decoded UTF-8 cafe note unchanged. Windows-1252 input raises UnicodeDecodeError with byte184 and no row; CLI catches it and returns2 rather than crashing. CP1252 acceptance is OUT of the commissioned UTF-8 contract. | Terminating cleanup at sheet.py:36/:120: preserve an existing BOM on rewrite; keep strict UTF-8, add row context to invalid-encoding errors, never auto-detect CP1252. Add BOM round-trip and encoding-error controls. |
| F3 | ACCEPTED MINOR in for over-redaction; reject byte-identity premise | EXECUTED: value-free EXIF/GPS sentences become metadata diagnostic withheld, including a planted complete runner-record warning through _invoke; its file bytes change. A planted EXIF GPSLatitude value is correctly withheld. The runner docstring explicitly permits malformed tag values in reader failure texts, so unsanitized byte-identical records are NOT safe or required by the brief. | Terminating cleanup at build.py:39-59/:885-893: preserve allowlisted static/value-free diagnostic forms, still redact values/paths; avoid rewriting a harmless record when sanitization makes no semantic change. Never retain an unsafe raw record in the pack. |
| F4 | ACCEPTED MINOR, in | EXECUTED twice: controlled clean V-P stage and a real successful/reviewable V-P fixture export both exit1 with an old V-S excerpt_failed in state. A pending-only page says128 items accounted for while all128 remain pending. | Terminating cleanup at build.py:1185-1192: compute media-command failures/counts from this invocation's attempted items; page reports pack-wide built/failed/pending coverage separately. Pending does not count as completed or cause an error by itself. |
| F5 | ACCEPTED MINOR, in, premise narrowed | EXECUTED: not run with failure=None maps to failed/empty. A producer-compatible cancelled record (failure=cancelled) maps to failed/cancelled, so the claim that normal cancelled records have empty text is refuted. batch.py:38-44 and headless_export.py:1044-1056 establish that real producer constraint. | Terminating cleanup at build.py:259-260: preserve not run/cancelled states and supplied messages; add an accurate runner-state explanation only when text is absent; include these states in the not-built accounting. No invented cancellation cause. |
| A1 | REJECTED ADVISORY, nominally OUT; REOPENED R1 F11 | EXECUTED: real scale commands with raw bt470bg AND bt2020nc both exit0 on installed FFmpeg, contrary to would refuse. R1 already refuted bt470bg; this probe independently checks both names. Origin f506b597, not external code. | DECLINE matrix expansion; no debt for the disproved rejection claim. |
| A2 | OUT OF ENVELOPE / BANKED ADVISORY | EXECUTED: invalid ICC bytes give caught OSError; inconsistent LAB ICC on RGB gives PyCMSError outside the catch tuple. Valid commissioned product/fixture profiles do not require malformed-profile support. Origin page.py ICC conversion f506b597. | BANK with instrument maintainer/CHARC; trigger: malformed or inconsistent profile derivatives enter a future commissioned set. No current repair or severity escalation. |
| A3 | ACCEPTED ADVISORY, in | EXECUTED: failure at the second still conversion leaves source/corrected temporary PNGs and a completed unreferenced pair. Partial NVENC MP4 residue remains REASONED from make_pair's lack of failure cleanup; no GPU failure was executed. | FIX in terminating cleanup at build.py:961-1010/:762: track artifacts created by this attempt, guard and remove only failed-attempt temporary/partial aids, preserve sources, product outputs and earlier successful artifacts. No broad directory prune. |
| A4 | ACCEPTED observation, ADVISORY in; code change DECLINED | EXECUTED plan arithmetic: duration47 -> start18.8/length30/end48.8. EOF truncation consequence REASONED; follows the literal commissioned rule and actual duration is recorded. | DECLINE changing selection arithmetic. Disclose planned versus actual duration in the later report; only CHARC/owner may amend the commissioned test interval. |
| A5 | BANKED ADVISORY, in, conditional | EXECUTED synthetic open-GOP excerpt -> excerpt_failed, displayed start differs from retained video start, path is not source. No owner GOP was read, so every GoPro fails is unproved. The displayed-start guard originates at03731250 and enforces the ruling. | BANK with CHARC/orchestrator for first V-S RUN REQUEST: inspect excerpt success/failure counts before scheduling the remaining clip pieces; route failures with evidence. Never relax the guard or silently run whole. |
| A6 | BANKED ADVISORY, in, conditional future need | EXECUTED CLI help has no named whole override; a long V-S item still plans an excerpt and manifest identities cannot be reassigned. No authorized named whole RUN REQUEST is currently pending. | BANK with CHARC/orchestrator; trigger: an explicitly authorized whole-long-clip request. Obtain a bounded instrument invocation/override commission then; do not bypass the pack or add an unsolicited general override now. |
| A7 | ACCEPTED ADVISORY, in | EXECUTED: undecided -> judged1/preferred0; page omits that explanation. Yes, leading-space yes and YES each return2 naming row2. Literal lower-case validation and counting are correct under the existing RED controls. | FIX page.py instructions once: blank means unjudged; yes/no/undecided count as judged; only yes preferred; exact lowercase values. Arithmetic and parser stay unchanged. |
| A8 | ADVISORY noted; code change DECLINED, in | EXECUTED: valid undecided/empty sheets exit0; invalid maybe exits2 naming row2. The original explicit RED node test_tally_cli_valid_scores_exit_zero_and_invalid_sheet_exit_two and Q7 strictness already require this behavior; no score-based pass/fail exit exists. | DECLINE changing invalid-input status. Clarify usage in later report: valid tallies always0; invalid CSV is an input error2. Do not weaken strict validation or alter judgement-free scores. |

### F1 blocking RED for turn 7 and fix boundaries

Planned nodes, not written or run this turn:

1. **test_done_item_with_failed_aid_is_loud[photo/video]**: plant the committed
   JPEG and tiny HEVC under commissioned names, complete schema-1 done runner
   results and actual product artifacts. Inject only thumbnail/pair failure at
   the external viewing boundary. Assert the product result remains done and
   linked; reviewable=False with the exact safe aid_message; photos/clips returns
   nonzero; later selected items/groups still run; page writes valid HTML with
   the item and aid reason under Not built (or its explicit unreviewable bucket)
   and returns nonzero. No pretend vote or correction failure is introduced.
2. **test_aid_failure_coverage_preserves_d65_arithmetic**: one valid yes row and
   one done-but-unreviewable headline item, with no prior owner votes on that
   failed pair. Assert only the reviewable row is emitted (Q7), headline stays
   1/1 =100.0 percent, catalog expected115/available1/missing114, and failed-aid
   inventory/coverage is explicit on the page. Never put unviewable items into
   judged, preferred or no, never substitute115 for the mandated judged divisor.
3. **test_page_lists_aid_failure_when_sheet_refuses_stale_pair**: plant an existing
   answered row, then a current unreviewable item. Assert existing owner CSV bytes
   remain unchanged, the command is nonzero and the current page clearly exposes
   the failed aid and retained-sheet condition. The existing sheet-preservation
   guard must not silently transfer or erase a vote to achieve completeness.

Fix anchors: build.py:1104-1110 keeps the product status separate from review
readiness; page.py:117-164 makes the failed review state and safe aid reason
explicit alongside the product link and under Not built; sheet.py:103 continues
one row per REVIEWABLE item, using the existing missing coverage rather than
fabricating a denominator. build.py:1185-1192 ties exits to attempt scope (F4).
Ensure a sheet-preservation error cannot hide the current failed-aid page.

**Subcommand policy to implement and test:** photos/clips/all return nonzero for
failures among items attempted by that invocation (including failed viewing aids
and excerpts; expected HLG refusals remain accounted items). A clean later media
piece does not inherit another piece's old failure exit. Page writes the current
failure inventory, then returns nonzero when that rendered pack has known build /
viewing-aid failures; pending-only partial packs remain valid. Page --check stays
the link-check operation; presets is unaffected; valid tally always returns0.
This applies the R1 loud-excerpt policy consistently rather than inventing votes
or substituting whole inputs. The earlier excerpt regression's page-exit0
expectation will need a **named contract-clarification step**, keeping its existing
record/skip/link/no-vote checks, rather than an unexplained assertion change.
No frozen or product interface must change and no STOP is required for this plan.

### Light baseline and yield

Own unchanged-candidate command (PowerShell sets PYTHONPATH=scripts):

```text
uv run pytest -q tests/test_reviewpack.py --basetemp=work/wp5.3/turn6/baseline-tmp -p sandbox_mkdir_shim -p no:cacheprovider -m "not gpu and not footage and not gui and not fullclip" --durations=0 --junitxml=work/wp5.3/turn6/baseline.xml
```

Result **92 passed in53.03 s**, exit0; JUnit confirms92 nodes, zero failures,
errors or skips. Largest parallel-node aggregate2.014 s (failed-excerpt/later-group
control); sole slow integration36.907 s. No marker change is needed. Baseline
uses the required tiny force-CPU control; its automatic product encoder can use
NVENC as previously disclosed. Own F1/F4 evidence explicitly pins libx265;
all direct aid/GOP encodes were software. No real-media/heavy job or new GPU
quality measurement was run. Baseline/log/status/probe evidence remains ignored.

No tests were added and no remediation occurred. No full gate, new review,
real-media RUN REQUEST, product/interface/config edit, mailbox post, commit/git
mutation, footage read, other-worktree access or image judgement. Only this
ledger changes. Final diff/LF/ownership checks are recorded before return.
Turn6 YIELDS; turn7 owns the blocking RED and authorized instrument remediation.


## Session 3 / Turn 7: round 2 remediation

### Boundary, governing ruling and scope

Session 2 retired at **198,059 depth_input_tokens** (dispatcher supplied), before
this multi-finding remediation. This is fresh session 3 at dispatch HEAD
5b8038db; its ID and turn-7 depth are for the dispatcher to fill. No depth is
estimated. The round-2 finding counts and NEW/REOPENED classifications remain
unchanged in the cumulative table above; this is a remediation turn, not another
review round. Reviewer A round 3 is next at the dispatcher's seat.

CHARC **0358beda** governs the fixes. In particular, its F1 replaces the earlier
planned row exclusion: a successful product export retains its sheet row even
when its viewing aid fails. Its F3 replaces the earlier planned record rewrite:
the runner's original group JSON is never rewritten. The historical turn-6
adjudication evidence above describes the old candidate and its initial plan;
the implemented dispositions below are the current contract.

This turn bundles the five accepted findings and two accepted advisories into
one logical review remediation, as commissioned. All code changes are inside
owned tools/reviewpack files and tests/test_reviewpack.py. No product module,
frozen interface, runner, shared helper, fixture, existing foreign test,
dependency, local configuration or harness file was edited.

### Per-finding RED / GREEN and final behavior

All outputs below are in this worktree's ignored **work/wp5.3/turn7/**. Every
pytest invocation sets PYTHONPATH=scripts and enables sandbox_mkdir_shim with
-p no:cacheprovider and a unique work/wp5.3/turn7/*-tmp basetemp. Logs and JUnit
are retained locally; the external review.txt was read in place and not copied.

| Finding | Observed RED before its fix | Implemented fix and GREEN evidence |
|---|---|---|
| F1 MAJOR / in | f1-red.log/.xml: 4 failed, 92 deselected, 1.35 s. Photo and video pieces incorrectly return 0; an existing answered failed-aid row is refused; a sheet identity error prevents current HTML from being written. | Product status stays done. A failed aid sets viewing_aid_failed=True and the safe aid_message; the row stays on the sheet with viewing_aid_failed=yes. The original corrected output is linked both in its group and under Not built with the aid message. photos/clips/all exit 1 for attempted failures and continue later items. page writes known failures and returns 1; --check remains link-only. Sheet identity errors retain owner bytes and still produce the current page and an escaped sheet notice. f1-f4-green.log: all 6 F1/F4 controls pass, 1.45 s. |
| F2 MINOR / in | minors-red.log/.xml: BOM rebuild drops the BOM; non-UTF-8 rows 1/2/3 lack row and UTF-8 context. The no-BOM multiline control also independently exposes LF -> CRLF mutation inside the owner's note. | Existing BOM presence is preserved; replacement CSV is encoded once and atomically written as bytes with LF row delimiters. Quoted Unicode and multiline notes survive exactly. UTF-8 stays strict; invalid decoding reports the logical CSV row and UTF-8 encoding, including after a multiline cell; no CP1252 inference. All five F2 controls pass in minors-green.log. |
| F3 MINOR / in | Same RED run: harmless EXIF/GPS messages are withheld, and _invoke changes the original runner record bytes. | Known static metadata diagnostics are preserved; parenthesized value details or unclassifiable value-bearing fragments become [withheld]. If the value boundary is uncertain, the whole line is withheld. Only pack-facing projections/logs are filtered; runner records stay byte-for-byte as emitted, including their supplied warning/failure strings, per 0358beda. One boundary test proves unchanged noncanonical JSON bytes plus a safe pack result/log. Five text cases and that boundary pass in minors-green.log; verification refinements below also pass. |
| F4 MINOR / in | f4-red.log: 2 failed, 96 deselected, 3.02 s. An earlier V-S excerpt failure makes a clean later V-R refusal piece return 1; a pending page claims all 128 items accounted for. | Media exit/count scope is this invocation's selected/attempted items only. Expected HLG refusals are accounted without failure; old unrelated failures do not poison later clean pieces. page reports pack-wide known failures; pending-only pages return 0. Pending inventory is shown separately and never counted as accounted. The 6-node F1/F4 GREEN run also verifies link-only page --check. |
| F5 MINOR / in | Four minors-red nodes map not run/cancelled to failed, with absent or supplied messages. | Preserve each runner state word and supplied reason. If absent, say runner reported <state>; no further reason was supplied. Both states appear under Not built, have no review row, and cause their attempted piece to fail. Four mapping/page/sheet controls pass in minors-green.log. |
| A3 ADVISORY / in | a3-red.log/.xml: 5 failed, 114 deselected, 2.22 s. Size extraction, partial pair encode, later browser conversion, second photo thumbnail and partial sRGB conversion each leak files. | Scoped ownership tracks only newly allocated aid paths before writers run. On failure, partial/temp/unreferenced files from that attempt are guarded and removed, stale result links reset; earlier aid files and product/source bytes stay unchanged. Scratch size and sRGB PNGs are always removed. Fresh naming preserves older successful aids. a3-green2.log: 5 passed, 114 deselected, 1.79 s. No directory-wide prune or pre-existing evidence deletion. |
| A7 ADVISORY / in | minors-red page instruction control fails: blank/undecided/case/flag semantics are absent. | Page explains blank = unjudged; yes/no/undecided = judged; only yes = preferred; exact lowercase and no surrounding spaces. Failed-aid rows count normally when judged. Control passes in minors-green.log. |

The combined minors RED was **16 failed, 98 deselected in 1.45 s**, exit 1;
its GREEN was **16 passed, 98 deselected in 0.88 s**, exit 0. All failures
listed as RED above are expected behavior failures, not collection errors.

**D65 counting:** viewing_aid_failed is an instrument-owned sheet column,
appended after note, with blank/yes values. A judged flagged row counts exactly
like every other judged row: yes adds to preferred and judged; no or undecided
adds only to judged. An unjudged flagged row remains available without adding a
vote. Per-group/headline/candidate summaries show the flag count; the required
headline line remains `headline: <preferred>/<judged> = <pct> %  (D65 bar 80 %)`.
The preserved-answer control proves 1 yes + 1 flagged no => 1/2 = 50.0 %, with
available=2, missing=113 and viewing_aid_failed=1. Original exact CP5 headers
remain readable and migrate to the appended flag without losing owner answers;
other malformed headers are still rejected. No preference or artifact judgement
is made by this instrument or cell.

A1 remains REJECTED; A2/A5/A6 remain BANKED; A4/A8 remain declined as code
changes, exactly as adjudicated. No new general whole-clip override, malformed-ICC
support, matrix-name expansion or permissive CSV scoring was added.

### Named contract/control adaptation step

Full run **full1.log/.xml** observed **115 passed / 4 failed in 29.93 s**.
The following four existing checks needed a separately named contract/control
adaptation; no other existing assertion was removed or relaxed:

1. Empty tally's verdict guard used substring `fail`, which now matches the
   required `viewing_aid_failed` field. Match standalone verdict words instead;
   retain zero-judged/zero-preferred and exact headline assertions.
2. The malformed-header case removed the last column. After appending the flag,
   that is the valid original header. Remove the mandatory preferred column
   instead; retain strict header refusal. A separate original-header migration
   control proves preservation and the new flag.
3. The interrupted-write control hooked OutputRoots.write_text. F2 now uses
   write_bytes to preserve BOM and note newlines; move the interruption to that
   actual boundary and still write partial bytes, raise OSError, and assert the
   original owner file is unchanged.
4. The prior excerpt-failure test expected page exit 0. CHARC's generalized loud
   failure policy requires page exit 1. Change only that expected status; retain
   all record/skip/no-submission/no-output/later-refusal/HTML/no-vote assertions.

**contract-green.log:** 7 passed, 112 deselected in 1.84 s, exit 0.
This is an explicit contract and injection-boundary correction, not a change to
expected pixels, packet identities, scores or source preservation.

### Verification loop: suspect / confirm independently / fix / repeat

1. **Confirmed / fixed, F2 follow-through [MINOR]:** the no-BOM multiline
   regression independently showed Path.write_text translating a note's embedded
   LF into CRLF on Windows. The byte writer needed for BOM preservation also
   prevents that mutation; both original assertions now pass unchanged.
2. **Confirmed / fixed, F3 boundary [MINOR]:** inspection suspected an ambiguous
   semicolon could separate an EXIF label from its value. Three independent text
   controls were RED in verification-red.log (3 failed / 119 deselected in 0.31 s):
   `EXIF GPSLatitude; 21.3` leaked its trailing value; parenthesized details lost
   an otherwise static diagnostic; a filename-prefixed static message was
   over-withheld. Withhold an uncertain whole line, redact known parenthesized
   details locally, and recognize a safe filename prefix. verification-green.log:
   all 9 metadata/boundary nodes pass in 0.14 s, including prior controls.
3. **Confirmed / fixed, mechanical:** first A3 edit had an indentation error
   because a code transformation matched the earlier excerpt-cleanup if block.
   a3-green.log records the collection error (no test result claimed). Restore
   that unchanged block from HEAD and scope the transform to make_pair;
   a3-green2 is green. Ruff initially found 14 style violations, then one raw
   regex annotation; format owned files and correct it. Mypy found one Any/None
   return in _available; explicitly return bool. Final checks below are clean.
4. **Rejected mechanical audit assumption (false positive):** the first
   scope-lf-audit.log wrongly demanded a Returns section on the existing
   validate_stream_copy -> None function. Its Google-style Args/Raises docstring
   is present; no code/docstring fix is warranted. Limit that assertion to
   value-returning functions. scope-lf-audit-final.log exits 0 and checks all
   public instrument docstrings, all five changed paths, zero CR and whitespace.
5. **No new finding:** full final run plus scoped diff, docstrings/comments,
   output guards, preservation controls, import/dependency and LF review found
   no further issue. No further finding, revert or product defect this
   turn. Existing rejected/banked advisories retain their dispositions.

### Final light verification / AD-30

PowerShell sets PYTHONPATH=scripts; commands run from this worktree root:

```text
uv run pytest -q tests/test_reviewpack.py --basetemp=work/wp5.3/turn7/final-tmp -p sandbox_mkdir_shim -p no:cacheprovider -m "not gpu and not footage and not gui and not fullclip" --durations=0 --junitxml=work/wp5.3/turn7/final.xml
uv run ruff check tools/reviewpack tests/test_reviewpack.py
uv run ruff format --check tools/reviewpack tests/test_reviewpack.py
uv run mypy
```

- **123 passed in 28.66 s**, exit 0; JUnit has zero failures/errors/skips.
  Exactly one existing slow integration node remains (headless runner + FFmpeg),
  **16.492 s** including setup/teardown. No new slow/GPU/footage/fullclip node.
- Slowest parallel node: excerpt-copy-failure/continuation, **1.116 s** aggregate;
  every parallel node is under 5 s. Per-node measured times are retained in
  per-node-final.csv; summary.log joins counts, maximum times and exit files.
- Ruff **All checks passed**, exit 0 (ruff-final.log/.exit); owned-file format
  **6 files already formatted**, exit 0 (format-final.log/.exit); mypy
  **Success: no issues found in 151 source files**, exit 0 (mypy-final.log/.exit).
  Inherited VIRTUAL_ENV points outside this worktree; uv explicitly reports it
  ignored and uses this project's .venv. No --active or other worktree access.
- The sole slow control retains the commissioned --force-cpu product path and
  existing automatic encoder behavior; its explicit-libx265 excerpt acceptance
  control remains intact. New direct aid controls use software encoding; no
  real NVENC-quality judgement or performance figure of record was run.
- scope-lf-audit-final.log records only the five named owned paths, zero CR per changed
  file, public instrument docstrings, and git diff --check success. No full
  two-leg gate or whole-tree formatting check is claimed: those remain at the
  dispatcher's seat after the reviews.

**Locks and return:** only owned instrument/tests/ledger paths changed; every
new aid write/remove uses OutputRoots checks inside the configured pack. All test
sources are planted committed fixtures, and source/product preservation is
asserted. No owner footage folder was opened, listed or probed; no main-tree
work directory or other worktree was accessed; no local configuration was edited;
no dependency, Qt import, OS-specific behavior, frozen/product/shared-helper
change, commit, git mutation, mailbox post, image judgement or real-media run.
Original runner record bytes are retained under the explicit R2 F3 ruling;
pack state, page-facing messages and logs use sanitized projections. No STOP or
open owner input this turn. Report and real-build RUN REQUESTs remain later
ladder tasks. **YIELD for Reviewer A round 3.**


## Reviewer A round 3 (adjudicated)

### Candidate, transport, depth and ruling

- Reviewed candidate and initial HEAD: **ed787934**. The dispatcher reports all
  five changed blobs have 0 CR and its format check found 293 files formatted.
  Turn-7 depth is **143,373 depth_input_tokens**, session 3, window 475,000;
  recorded verbatim above. Evaluate around 200K and stop at a step boundary near
  250K. Turn-8 depth remains for the dispatcher; no estimate is made.
- Transport **claude -p --model opus --effort high**, executed by the dispatcher:
  exit 0; model claude-opus-5-5; requested effort high; is_error false; 28 turns;
  VERDICT NEW_CRITICAL_MAJOR_FOUND; worktree clean after review. One denied
  heredoc was rerun inline, with no finding losing execution. No CLI version is
  supplied, so none is inferred. This is counted round **3 of 5**. The reviewer
  ran its light tests FIRST: 123 passed in 34.61 s, including the slow node.
- review.txt, review-prompt-r3.md and review.seat.log were read in place in the
  dispatcher's wp5.3/r3 evidence folder, never copied into the repository.
- During this turn, HEAD advanced to **4d5922eb**, folding CHARC **c25ff7a9**
  (2026-11-01T17:59:31Z) into the brief. A read-only diff against ed787934 lists
  only docs/briefs/wp5.3-brief.md; tools/reviewpack and tests/test_reviewpack.py
  are identical. The new ruling was read and governs the dispositions below.
  No instrument/test edit occurred. The new brief fold is the dispatcher's work,
  not a file changed or a commit made by this cell.

Reviewer counts: **0 critical / 1 major / 3 minor / 3 advisory**, nominally
6 in-envelope / 1 out (F3). R3-3 explicitly brings F3 IN, so the effective
remediation envelope is **7 in / 0 out**. Zero reverts, no fix this turn. The
reviewer reports every round-2 fix VERIFIED CLOSED; own baseline remains green.
This is not convergence: F1 is a new blocking path requiring remediation.

**NEW / REOPENED:** five NEW concrete findings (F1/F2/F4/F5/F6); two REOPENED
findings (F3 repeats round-2 A2's exact ICC exception, F7 challenges round-1 F7's
now-consistent transfer policy). **F1 and F2 REOPEN the silent-loss CLASS** under
the generalized ruling: F1 silently discards persisted inventory; F2 loudly
omits a successful product from links and the sheet. They are NEW concrete paths,
not regressions of the previously repaired aid catch: manifest pruning and
neutral-result status handling both originate at f506b597, unchanged by turn 7.
F2 is not silent at the CLI (both pieces return 1). This distinct-path/pattern
accounting follows the same distinction recorded for round 2; both levels are
explicit for the dispatcher's gate decision. No finding is dismissed as external
pre-existing code; all challenged mechanics originate in this package.

### Independent probes and their limits

Own scripts, planted sources, derived artifacts and runner outputs are only in
ignored **work/wp5.3/turn8/** in this worktree. No owner footage folder, real
configuration, main-tree work folder or other worktree was read or written.
Every simulated product uses the complete schema-1 runner shape and writes real
small PNG artifacts; only the expensive external runner boundary is replaced.
These probes prove instrument behavior, not product correction or image quality.
No judgement is made of any image.

- probes.py / probes.log confirms F1, then stops on a **probe assumption error**:
  it expects one 73-photo batch rather than the actual P-A 64 and P-Z 9 batches,
  each with corrected and neutral calls. Its exit 1 is retained and disclosed;
  it is not a product or test-suite failure. probes-followup.py / .log uses
  fresh planted roots and the correct four-batch structure and completes every
  F1-F7 assertion, **exit 0**. No source change was made to get these results.
- F1 uses the real selection, pack persistence, sheet and HTML. Only the runner
  and expensive thumbnails are replaced. A full photos command leaves 128 rows;
  a one-name manifest command saves 1; page returns 0 with a one-row sheet and
  no IMG_6690.HEIC anywhere. A subsequent full photos command actually writes
  64+9 corrected and 64+9 neutral results but STILL saves 1 row, proving the
  missing-append path separately. It prints one item accounted for, pending=0.
- F2 uses actual thumbnail generation and two complete runner records. The
  first corrected export succeeds while its neutral fails; the second photo
  completes. photos/page both return 1. The first corrected PNG exists, but its
  name is absent from HTML and its sheet row is absent. Only the healthy photo
  remains on the sheet. The failure message begins with a semicolon and space.
- F3 constructs a real Pillow LAB ICC profile on RGB PNGs, rather than raising
  a fake exception. ImageCms raises PyCMSError, not OSError; the group has four
  product PNGs but no pack.json and the healthy item's state is lost too.
- F4 first probes an actual planted unreadable MP4 followed by the tiny valid
  committed HEVC fixture: exit 2, no group state written and no later product.
  Separate controlled ffprobe/packet responses prove uncaught StopIteration
  (no video stream), KeyError (keyframe with missing pts_time), TypeError
  (null pts_time), and TypeError from a null duration. These establish fault
  handling defects, not that any commissioned owner file has such metadata.
- F5 executes page on a pending-only 128-row state (exit 0, pending=128), then
  a control with only V-R/V-Z pending (exit 0, pending=4). All four names ARE
  visible under Not built. The 124 other rows are deliberately planted accounted
  placeholders; no real-media completion or judgement is claimed. Its behavior
  was previously allowed by round 2; c25ff7a9 R3-5 now changes that policy.
- F6 executes _safe_text on planted/synthetic strings only. A root-prefixed
  diagnostic retains the Phone folder and separator; an unquoted or quoted
  drive-rooted path with a space retains its trailing folders; a quoted POSIX
  path with a space does too. No synthetic diagnostic path was opened. Summary
  output contains the safe projection, not an owner's full path.
- F7 makes fresh uniform-128, unprofiled RGB PNG controls. Unknown tags remain
  (128,128,128); explicitly tagged bt709/bt709 and smpte432/bt709 both become
  (121,121,121), each tagged sRGB afterwards. frames.colour_filter at :750
  performs range/matrix-to-RGB conversion and its documented PNG path has no
  colour chunk; _browser_frame adds the explicit tagged-SDR display conversion.
  _rgb still performs no ICC transform when its input lacks a profile. Numeric
  display transformation is confirmed; perceptual mismatch/preference is not
  judged. R3-7 now explicitly accepts this treatment of both halves.
- origins.log (git log -S, literal argument vectors) identifies f506b597 for
  manifest pruning, neutral failure mapping, ICC profile conversion, duration
  pre-probe and path filtering; 03731250 for the active excerpt packet indexing
  and consistent tagged-SDR branch; ed787934 for the current _failed/pending
  page policy. Every origin is inside this arc; the banked ICC finding is not
  pre-existing external code. summary.log retains the AST mutation inventory,
  extra quoted/space path controls and independent JUnit timings.

### Per-finding adjudication and turn-9 disposition

| Finding | Verdict / severity / envelope / evidence | Bounded disposition (no fix this turn) |
|---|---|---|
| F1 | ACCEPTED MAJOR, in, EXECUTED. 128 -> 1 persisted rows after a manifest; page/sheet then have 1 and pending=0. A later full photos export still cannot append absent rows. Silent-loss class REOPENED, NEW concrete selection/persistence path. | At build.py:1264 remove persistent pruning; the manifest filters selected inputs only. At :1127/:1177 replace-by-item OR append for excerpt/product rows. Retain the loaded inventory; count pending from commissioned names without a nonpending result, including missing catalog rows. R3-1 requires every state assignment/slice be audited for cannot-shrink behavior; turn 9 returns the final site table. |
| F2 | ACCEPTED MINOR, in, EXECUTED. A done corrected PNG remains on disk but status becomes failed after a neutral error; no product link or sheet row; photos/page return 1. Loud rather than silent, but REOPENED successful-product omission class in a NEW neutral-source path. | At build.py:1162 treat failed neutral export as viewing_aid_failed, reviewable=False, keeping corrected status done and the row; add the neutral reason without a leading separator. page.py links the corrected product under Not built and conditionally omits the unavailable neutral link. Piece exits 1. Same round-2 form, explicitly reaffirmed R3-2. |
| F3 | ACCEPTED MINOR; originally OUT, now IN by R3-3; EXECUTED. Real mismatched LAB/RGB profile raises uncaught PyCMSError, losing group state. REOPENED round-2 A2, origin f506b597. | One-line catch extension at build.py:1171: add ImageCms.PyCMSError at the per-item viewing-aid boundary, yielding the same flagged row/product link/nonzero form and continuing the healthy item. No broad Exception catch or product edit. |
| F4 | ACCEPTED MINOR, in, upgraded from REASONED to EXECUTED controls. Actual probe ValueError aborts the piece; controlled missing/null packet facts escape as KeyError/StopIteration/TypeError. No owner-file fault asserted. | Wrap each item's duration/preparation at build.py:1105 and normalize known schema faults in prepare_excerpt's :656 catch; record safe failed/excerpt_failed item messages, continue later items, aggregate exit 1. R3-4 asks for continuation controls past one ValueError and one KeyError, not a redundant matrix of each exception type. |
| F5 | ACCEPTED ADVISORY, in, EXECUTED; NEW completion-policy challenge at build.py:1270/1283. Pending rows are visible and counted but page returns 0 under the prior policy. R3-5 supersedes that policy. | FIX per R3-5: page header lists pending count/groups, page exits 2 while pending > 0 (distinct from item failure 1), and tally shows pending coverage using the catalog and persisted item facts rather than guessing all missing rows are pending. V-R must be run to obtain refused result rows; include V-R/V-Z in later RUN REQUEST scheduling. No owner handoff before pending=0. |
| F6 | ACCEPTED ADVISORY, in, EXECUTED at build.py:87. Footage-relative separators and quoted/unquoted spaced path tails survive; a full owner path/GPS leak was not shown. Origin f506b597. | FIX per R3-6: collapse any residual path token to its last component; recognize quoted spans and drive-rooted/absolute paths containing spaces before basename projection. Three RED cases: relative Phone form, quoted drive path with a space, POSIX path with a space. |
| F7 | ACCEPTED ADVISORY observation at build.py:989, in, EXECUTED; REOPENED round-1 F7 policy, not a regression or proved preference bias. Tagged grey128 -> 121 equally in both halves; unknown stays128. | ACCEPT AS IS / DOCUMENT under R3-7: no pixel change or reversal. Add the specified BT.1886 -> sRGB/both-halves/player-rendering sentence to the generated pack README and page footer. No new committed README path is needed; the page builder can emit the pack-local README. |

All seven observations have independent evidence. The ruling provides the
bounded policy choices; no adjudication requires an owner answer or product /
frozen-interface change. No STOP this turn. Earlier unrelated banks/rejections
remain unchanged.

### Planned RED for the F1 blocker and cross-path audit

Turn 9, before modifying instrument code:

1. Full-state fixture plus a one-name manifest: persist every catalog item,
   exactly one selected row replaced, all other rows and pending count retained.
   Build the page and sheet and prove all previously reviewable items stay
   linked/available, including unselected owner answers. Keep V-R excluded from
   review rows and keep pending/failed items visible under Not built.
2. A manifest naming an item absent from saved state must append its result;
   a later complete command must not silently discard any newly exported item.
   Missing catalog names contribute to pending coverage, never pending=0 merely
   because the loaded state was pruned. Empty/missing versus explicit pending
   facts are counted consistently against select.catalog().
3. A chosen output identity change must STILL retain the old owner sheet and
   refuse vote transfer. Do not weaken that guard to obtain the row-count RED.
   The catalog-retention test uses a compatible selected identity or a previously
   failed item with no prior vote; it isolates pruning from regeneration.

Current-site inventory from AST inspection of the unchanged candidate (not a
claim that it is safe already):

| Current state site | Present property | Turn-9 no-shrink obligation |
|---|---|---|
| main initial state load/creation, :1224 | New pack starts with catalog; old pruned state is loaded unchanged | Include absent commissioned names in pending accounting; never use loading as a pruning step. |
| _build_groups excerpt result, :1127 | Index replacement cannot shrink, but absent entries are ignored | Replace an existing item or append a missing item; cannot shrink. |
| _build_groups product result, :1177 | Same replacement-only gap | Replace or append; cannot shrink. |
| main manifest comprehension, :1264 | UNSAFE persistent row-count reduction | Remove the assignment; filter inputs in memory only, cannot shrink saved state. |
| main exit scope lists, :1270/:1272 | Filter is ephemeral and not assigned to state | Keep it ephemeral; cannot shrink saved state. |

No AST slice expression of state items exists; the comprehension at :1264 is
the persistent filter. The remediation must repeat this inventory on its FINAL
code and list every mutation/slice with cannot shrink proved, as R3-1 requires.
R3-1 additionally makes a fourth silent-loss finding in round 4 a STOP to CHARC,
not an automatic extra round. Round 4 follows remediation only at the
orchestrator's seat and under its Claude 92-percent hold rule; round 5 remains
the cap and convergence requires an executing pass.

The other planned RED controls are the ruled neutral-source failure row/link,
one actual mismatched-profile row with healthy continuation, probe/prepare
ValueError and KeyError continuation, page/tally pending coverage, and the three
path-with-space/name-only cases. F7 only adds explanation; its numeric control
must remain unchanged. R3-5 requires a named contract amendment of earlier
pending-page exit-0 controls to exit 2, preserving link-only --check semantics.

### Own light baseline and yield

Command from the worktree root, PowerShell sets PYTHONPATH=scripts:

```text
uv run pytest -q tests/test_reviewpack.py --basetemp=work/wp5.3/turn8/baseline-tmp -p sandbox_mkdir_shim -p no:cacheprovider -m "not gpu and not footage and not gui and not fullclip" --durations=0 --junitxml=work/wp5.3/turn8/baseline.xml
```

**123 passed in 28.29 s**, exit 0; JUnit: zero failures/errors/skips. Sole slow
integration aggregate **16.212 s**; largest parallel node (excerpt-failure /
later-group continuation) **1.097 s**, all parallel nodes below 5 s. No marker
change is needed. The baseline retains the tiny force-CPU runner control and
its existing automatic encoder behavior; direct F7 conversion probes are tiny
software FFmpeg operations. No real-media job, performance figure or GPU quality
measurement was commissioned or run.

Only this ledger is edited. No test or instrument remediation, full gate,
new reviewer invocation, dependency/config/product/interface edit, mailbox post,
commit/git mutation, other-worktree access or owner image judgement. The final
scope/LF/diff checks are retained in turn8/scope-lf-audit.log. **YIELD**; turn 9
owns RED and the bounded fixes under c25ff7a9.


## Session 4 / Turn 9: round 3 remediation

### Session boundary, ruling and scope

Session 3 retired at **182,934 depth_input_tokens** (dispatcher supplied).
This is fresh session 4, dispatched at **a14a25ed**. The dispatcher fills this
session's ID and depth; no estimate is made here. CHARC **c25ff7a9** governs all
seven fixes, reusing **0358beda** for the failed-viewing-aid form. This is one
logical round-3 remediation turn, bundling the seven expressly commissioned
items; it is not an additional review round. Reviewer A round 4 remains at the
dispatcher's seat under its 92-percent hold rule. Convergence is not claimed.

The dispatch protocol, application conventions, predecessor's turn-7/turn-8
ledger, round-3 findings and current instrument/tests were re-grounded. The
external review was read in place and not copied into the repository. All
runtime evidence below is ignored **work/wp5.3/turn9/** inside this worktree;
pytest used **work/wp5.3/tmp/** with the required sandbox shim. Only committed
fixtures and planted inputs were opened. No owner footage or another worktree
was accessed.

### Per-finding RED / GREEN

| Finding / classification | RED evidence | Remediation and GREEN evidence |
|---|---|---|
| R3-1 / F1 MAJOR, in | r3-1-red.log/.xml: 3 failed, 123 deselected, 0.81 s. A full 128-row state plus one-name manifest saves 1 row; a state missing the selected product or excerpt-error item never appends it. | Selection filters only inputs. Shared _store_item replaces by identity or appends; it never filters saved rows. Catalog-based pending includes missing rows. r3-1-green.log/.xml: 3 passed, 123 deselected, 0.35 s. Full-state rerun retains 128 rows, exactly one replaced, 127 unchanged and pending=127; missing-product case appends to 128; missing-excerpt-error case preserves the old row and appends the error. These are the already-ruled replacement-only gaps, not a newly found fourth loss path. |
| R3-2 / F2 MINOR, in | Neutral-export node in r3-2-4-red.log/.xml confirms corrected status changes to failed despite the successful PNG. | Keep status done and corrected_name; mark viewing_aid_failed=True, reviewable=False, and record a neutral-source aid message without a leading separator. Skip unavailable neutral thumbnails/link. Sheet keeps the flagged row, page links the product under Not built, photos exits 1, healthy next photo completes. |
| R3-3 / F3 MINOR, brought in envelope | ICC node in r3-2-4-red.log/.xml raises actual ImageCms.PyCMSError from a LAB profile attached to RGB product pixels. | Catch PyCMSError at the viewing-aid boundary, retain done product and flagged row, clean partial aid files, continue healthy next photo; no product edit or broad Exception catch. |
| R3-4 / F4 MINOR, in | Probe ValueError node returns 2 instead of 1; packet KeyError node escapes prepare_excerpt. Both in r3-2-4-red.log/.xml. | Per-item probe/prepare catches ValueError, KeyError, StopIteration and TypeError (plus existing I/O/tool faults), writes a safe failed/excerpt_failed row and continues. Later V-R item reaches the runner and is refused; failed clip never reaches correction. prepare_excerpt normalizes packet faults into the existing excerpt-error record. |
| R3-5 / F5 ADVISORY, fix ordered | Pending page node in r3-5-6-red.log/.xml returns 1 despite 4 catalog items pending (three absent rows and one explicit pending row). | Page header names count and groups; page/all returns 2 while pending, even when failures also exist; link-only --check remains independent. Tally reads companion pack.json for catalog pending including V-R; a detached CSV reports unknown pack coverage rather than inventing it. V-R refusals are accounted results and have no review row. The control reduces pending from 4 to 2 after both V-R refusals, with V-Z still pending. |
| R3-6 / F6 ADVISORY, fix ordered | Five path controls in r3-5-6-red.log/.xml fail: relative Phone token, configured-root tail, quoted Windows space, unquoted Windows space, quoted extensionless POSIX space. | After root stripping, quoted spans and known-extension rooted paths retain only their last component; every remaining separator token also collapses to its last component. All five controls pass without opening a diagnostic path. Existing metadata-redaction and immutable runner-record controls remain green. |
| R3-7 / F7 ADVISORY, accepted as is | No prose-only regression test; prior numeric transfer-policy control retained unchanged. | Generated pack README.md and page footer both explain: Video stills are converted BT.1886 -> sRGB for display; both halves alike; the player's rendering differs. The independent complete-pack control verifies both outputs. No frame/transfer behavior changed. |

The combined R3-2/3/4 RED was **4 failed, 126 deselected in 0.78 s**;
GREEN **4 passed, 126 deselected in 1.06 s**. The R3-5/6 RED was **6 failed,
130 deselected in 0.98 s**; GREEN **6 passed, 130 deselected in 0.65 s**.
All thirteen new regression nodes failed at the intended behavior assertion or
uncaught instrument exception; there were no collection errors. All thirteen
are in the parallel leg and measured below five seconds. No finding is rejected,
banked or downgraded this turn; prior review classifications remain in the
cumulative row, with zero reverts and no product/test-only substitute fix.

### State inventory audit -- every mutation and derived filter

`rg -n 'state\[' tools/reviewpack`, the filtered-selection search, the scoped
diff and an independent AST traversal in verification.py enumerate every site.
The AST rejects whole-list assignment/deletion, slices and list methods other
than append. It finds **one index replacement and one append**, both in the
shared writer. There is **no fourth path that can shrink persisted state**.

| Final site (file:line) | Operation | Cannot shrink: evidence |
|---|---|---|
| tools/reviewpack/build.py:1271 | Load existing state or initialize all 128 catalog rows (:1274). | Existing list loaded unchanged; new list is complete catalog. No manifest applied to state. |
| tools/reviewpack/build.py:1097 | Enumerate saved items for identity lookup. | Read only; caller cannot filter through this iterator. |
| tools/reviewpack/build.py:1099 | Replace one indexed item. | List length unchanged; full-state regression proves exactly one row replaced and 127 unchanged. |
| tools/reviewpack/build.py:1101 | Append absent item. | Length increases by one; missing product and missing excerpt-error regressions both pass. |
| tools/reviewpack/build.py:1158 | Save excerpt failure through _store_item. | Uses only replacement/append above, including an item absent from old state. |
| tools/reviewpack/build.py:1161 | Save per-item probe/prepare fault through _store_item. | Same nonshrinking writer; continuation controls retain failed item and later refusal. |
| tools/reviewpack/build.py:1225 | Save product/aid result through _store_item. | Same nonshrinking writer; neutral/ICC and full-state controls retain product rows. |
| tools/reviewpack/build.py:1299 | Select manifest inputs; kind/group comprehensions at :1300/:1308. | Filters only new selected list, never aliases or assigns saved items. Persistent manifest comprehension removed. |
| tools/reviewpack/build.py:1284 | Pass saved items to sheet writer. | Read-only input projection; rows/answers are written to a separate CSV, never assigned back. |
| tools/reviewpack/build.py:1289 | Pass saved items to page writer. | Read-only rendering; pending/header/not-built lists never assigned back. |
| tools/reviewpack/build.py:1312 | Filter attempted items into exit-scope list. | Temporary comprehension, no state assignment; old unrelated failures do not poison clean pieces. |
| tools/reviewpack/build.py:1314 | Alias full items for page exit scope. | Scope is only iterated for counts; no mutation through alias. |
| tools/reviewpack/build.py:1316 | Read items for catalog pending. | select.pending_items (:170/:179-180) builds a separate accounted set and returns missing/pending catalog identities; never alters input. |
| tools/reviewpack/sheet.py:173 | Read companion saved items for pending tally. | Same pure pending projection; no pack write from tally. |
| tools/reviewpack/build.py:1180 | Persist all current state (also :1226/:1311). | _json_write serializes entire state; no item projection/filter. No state slices anywhere. |

### Named contract/control adaptation step

**full1.log/.xml: 127 passed / 9 failed in 26.07 s**, solely at obsolete
manifest-row positions/counts or the now-ruled pending-page exit. These nine
existing nodes were adapted in a separate named step after inspecting their
failure output, without weakening their product/link/sheet/source assertions:

- Tiny all-stage control now expects 2 for its 125 pending catalog items;
  asserts all 128 saved rows and exactly 125 pending, then looks up GX011604 by
  identity instead of assuming the first video row was selected.
- Real HLG control retains all 128 rows; exactly one nonpending result is
  IMG_6704 refused with the product HLG text. Page expects 2 for 127 pending;
  sheet remains empty and the refusal remains visible.
- Excerpt-failure and two photo/video aid-failure nodes look up their selected
  rows by identity in the 128-row state. Failed/skipped submission guards,
  later-group success/refusal, product links and blank/flagged rows remain.
  Their page/all calls now return 2 while catalog items are pending; media
  pieces still return 1 for their own failures.
- Clean-piece, initial-pending-page and two BOM-preservation nodes now expect
  page exit 2 for catalog pending. Clean clips still exit 0, --check still 0,
  accounted remains zero for pending-only, and BOM/Unicode/multiline owner
  answers remain unchanged.

**full2.log/.xml: 136 passed in 30.86 s**, exit 0. This strengthens inventory
checks while aligning completion statuses with c25ff7a9; it does not relax a
failure, pixel, identity, source-protection or vote-preservation assertion.

### Verification loop: suspect / confirm independently / fix / repeat

1. **Confirmed / fixed [MAJOR, R3-1]:** persisted selection and absent-result
   branches were the ruled loss sites. Three RED controls, shared replacement/
   append, GREEN, then the independent AST/mutation audit above. No additional
   shrinking path found; no fourth-path STOP is triggered.
2. **Confirmed / fixed [MINOR, R3-2/3/4]:** successful products were hidden by
   neutral failure, real ICC exceptions escaped, and malformed probe/packet
   facts aborted later work. Independent boundary controls distinguish all four
   defects; state/product/sheet continuity is verified, not only exit status.
3. **Confirmed / fixed [ADVISORY, R3-5/6]:** pending absence and unsafe path
   tails reproduced in six RED nodes; GREEN proves counted missing rows, V-R
   accounting and name-only text. No diagnostic path was opened.
4. **Confirmed / fixed, mechanical:** first ruff found one E501 after wrapping
   preparation in a per-item try block; owned-file format fixed it. Mypy was
   clean on its first run. The lexical docstring audit also flagged the new
   nested basename helper; a one-line descriptive docstring was added. The same
   audit incorrectly classified the existing nested create closure as public;
   rejected that audit assumption and checked module-level public APIs instead.
   No implementation hypothesis was discarded and no
   existing behavior assertion was weakened; contract adaptations are separate
   above. The rejected nested-closure audit assumption is the only false positive;
   no reviewer finding was dismissed.
5. **Independent terminal controls / no new finding:** verification.py builds
   a fully planted 128-item pack (126 done plus 2 refused), then page exits 0,
   pending=0, headline available=115, candidates=11. One failed aid then keeps
   all rows and product links with page exit 1 and pending=0. The README and
   footer contain the ruled display sentence. AST inventory, scoped diff,
   public docstrings/comments, output checks, preserved runner bytes and source
   checks find no further issue. Final test/style/type/byte checks below are
   the full repeat pass with no new finding. No product defect found or fixed.

### Final light verification / AD-30

PowerShell sets PYTHONPATH=scripts. Exact commands from this worktree root:

```text
uv run pytest -q tests/test_reviewpack.py --basetemp=work/wp5.3/tmp -p sandbox_mkdir_shim -p no:cacheprovider -m "not gpu and not footage and not gui and not fullclip" --durations=0 --junitxml=work/wp5.3/turn9/final.xml
uv run ruff check tools/reviewpack tests/test_reviewpack.py
uv run ruff format --check tools/reviewpack tests/test_reviewpack.py
uv run mypy
```

- Final pytest: **136 passed in 30.60 s**, exit 0; final.xml has zero failures,
  errors or skips. Exactly one existing slow node, no marker changes, no
  footage/fullclip/GPU node added. Source immutability and real headless runner
  plus FFmpeg remain exercised by the tiny force-CPU integration control.
- Slow integration aggregate **17.366 s**. Slowest parallel node:
  test_excerpt_copy_failure_is_recorded_skipped_and_exits_nonzero,
  **1.096 s** including setup/teardown. Every parallel node stays below 5 s.
  All 136 measured node times/statuses are in per-node-final.csv; summary.log
  joins RED/GREEN/final JUnit counts and maximum times. No figure of record.
- Ruff: **All checks passed**, exit 0 (ruff-final.log/.exit). Owned-file format:
  **6 files already formatted**, exit 0 (format-final.log/.exit). Mypy:
  **Success: no issues found in 151 source files**, exit 0 (mypy-final.log/.exit).
  uv reports inherited VIRTUAL_ENV ignored and uses this project's environment;
  no --active or other-worktree read. Two-leg/whole-tree gate stays with dispatcher.
- verification-final.log/.exit: independent complete-state, terminal page exits,
  display documentation and AST audit, exit 0. scope-lf-audit.log records six
  owned changed files, zero CR, public instrument docstrings and diff whitespace
  check. Git's worktree CRLF warnings are conversion advice; byte checks are
  against actual worktree bytes. Dispatcher commits LF blobs.

**Locks / remaining work:** all changes are in the owned instrument, tests and
ledger. Every new production output uses OutputRoots guards. No source pixel,
product module, frozen interface, shared helper, existing other test, local
configuration or dependency changed. No Qt or OS-specific behavior added; no
owner footage, main-tree working folder or another worktree opened; no git
mutation, commit, mailbox post, real-media build or image judgement. Successful
product exports remain authoritative and linked; runner records retain their
bytes under the prior ruling. No open question or STOP. No real-build/report/
gate claim is made; those remain later ladder tasks. **YIELD for Reviewer A
round 4 at the dispatcher's seat.**


## Session 4 / Turn 10: Reviewer A round 4 terminating clean-up (CHARC e4d56665)

### Candidate, convergence, ruling and depth

- Turn 9 is committed **de884f7d**. The dispatcher reports its blobs have 0 CR
  and ruff/format clean. Supplied session-4 turn-9 depth: **140,647 tokens**;
  recorded in the depth table without estimation. The turn-10 starting HEAD is
  **07876a8e**, folding CHARC **e4d56665**. Session ID and turn-10 depth remain
  for the dispatcher to fill. Evaluate around 200K; stop near 250K at a boundary.
- Reviewer A round 4: **Claude opus, high**, executing at the dispatcher's seat
  on de884f7d. Findings read whole, in place in its external r4 evidence folder,
  never copied into the repository. Executed first: **136 passed in 34.56 s**.
  No other transport metadata was supplied and none is inferred.
- Verdict **NO_NEW_CRITICAL_MAJOR**: **CONVERGED at round 4**, explicitly ruled
  by CHARC. Four MINOR and six ADVISORY; effective remediation envelope 8 IN /
  2 OUT (R4-9 brought IN). Ten NEW distinct findings, zero reopened concrete
  findings and zero reverts. The slash-text issue is a regression introduced by
  R3-6; the diagnostic-sidecar loss repeats the broad loss pattern but is NOT a
  fourth state-of-record path. R4-8 newly examines coverage of the already
  working R3-4 TypeError catch. These are disclosed rather than reclassified as
  critical/major or treated as grounds for another A round.
- CHARC's two conditions govern: ONE replace-or-append rule on every item JSON
  write, with the complete write classification below; Reviewer B must check
  that classification and execute a two-manifest sequence on a fixture state.
  This is the terminating clean-up, not a new review round or a final acceptance.

### Per-finding adjudication and RED / GREEN

All evidence is ignored **work/wp5.3/turn10/** inside this worktree. Pytest uses
**work/wp5.3/tmp/** and the sandbox shim. Only planted files and committed tiny
fixtures were opened; no owner footage was read, classified or judged.

| Finding | Classification / RED | Terminating disposition / GREEN |
|---|---|---|
| R4-1 | ACCEPTED MINOR, IN. Two clips then a one-clip manifest leaves one excerpt row instead of two; RED assertion at the retained-count check. | _json_write centrally merges old item rows by identity through _store_item before atomic replacement. Both pack and excerpt files use it. The two-run control retains GX011603 unchanged and replaces only GX011604 with attempt-2 facts; pack stays 128 rows. Raw runner records stay immutable, using fresh names to append invocation history. |
| R4-2 | ACCEPTED MINOR, IN. Both no-preset and one-preset complete-media states return 0 rather than 2 and make the unconditional AD-13 assertion. | Missing starter state/file identities are pending; page header names them, page returns 2, incomplete tables do not carry the AD-13 sentence. After presets, both tables and sentence appear and the complete planted page returns 0. |
| R4-3 | ACCEPTED MINOR, IN. Page creates an absent pack.json and rewrites a deliberately spaced existing one. A held-lock presets command runs instead of refusing. | Page no longer writes pack.json. One exclusive-create .reviewpack.lock covers all mutating CLI stages, including all as one transaction; page also takes it to serialize derived writes. Acquire precedes state load, holder pid/start are reported, stale locks require manual deletion, and only the holder removes its lock on exit. Both absent/existing page-state controls and held-lock refusal pass. A separate error-exit control verifies release. |
| R4-4 | ACCEPTED MINOR, IN. Four slash-bearing product strings fail preservation; the three path rows already pass and remain in the SAME parameterized control. | Collapse only rooted paths or separator tokens with a known extension. time base 1/90000 is not 1/N ticks., (ipco/ipma), (moov/udta), 30000/1001 fps remain unchanged; relative Phone, quoted spaced Windows and quoted spaced POSIX paths collapse to their last component. Existing path and metadata guards stay unchanged. |
| R4-5 | LIMIT ADVISORY, OUT. Executed by reviewer; no commissioned path has this form. | Retain and disclose: an unquoted spaced path with an unlisted extension may retain folder words. README Limits text added; carry forward to the later real-build report. No broader path parser commissioned or claimed. |
| R4-6 | LIMIT ADVISORY, OUT. Reviewer reasoning; all commissioned files are tagged. | Retain and disclose: untagged video still halves can differ in tone because the product defaults missing tags but the viewing adapter converts only explicit tags. README Limits text added; carry forward to report. No pixel/transfer change. |
| R4-7 | ACCEPTED ADVISORY, IN. Done V-R returns 0; unrelated failures have no expected-refusal flag, and merely mentioning HLG mislabels one as refused. Three RED rows. | Recognize the actual product HLG refusal sentence (plus the existing literal fixture form), rather than any HLG substring. Keep actual done/failed state and product message; unexpected V-R results get expected_refusal_failed, appear under Not built with an explanation, and clips exits 1. V-R remains outside the review sheet. |
| R4-8 | ACCEPTED ADVISORY, IN, coverage only. New control is GREEN first: actual _video reaches float(None), existing _build_groups TypeError catch already handles it. | Preserve the working catch. The new row proves a failed item with NoneType text is persisted and the later V-R group still runs. No fictitious RED or code repair claimed. Removing TypeError from that boundary would break this control. |
| R4-9 | ACCEPTED ADVISORY, brought IN. Actual Fraction(0/0) from tmcd average rate and raw subprocess.TimeoutExpired each escape as a traceback; two RED rows. | Normalize ZeroDivisionError and TimeoutExpired at item prepare/view boundaries. _invoke also maps runner launch/timeout faults to failed rows for the batch, with safe diagnostics and nonzero status, so later groups continue. Both controls retain the failed item plus later refusal and exit 1; no whole-source fallback. |
| R4-10 | ACCEPTED ADVISORY, IN, documentation only. Existing link-check exit behavior is intentional. | README and page state: page --check is a link check, not finished; use plain page for completion. Link-only checks retain their previous statuses. Independent output inspection verifies both texts. |

- **r4-1-4-red.log/.xml:** 10 failed, 3 passed, 136 deselected in **6.63 s**.
  The three passing nodes are the already-fixed R3 path cases, intentionally
  paired with the four new product-text cases. No collection error.
- **r4-1-4-green.log/.xml:** **13 passed**, 136 deselected in **9.37 s**.
- **r4-7-9-red.log/.xml:** 5 failed, 3 passed, 149 deselected in **2.47 s**.
  Passing controls are the existing TypeError behavior, immutable fresh runner
  records, and lock release after error (R4-3's implementation already applied).
- **r4-7-9-green.log/.xml:** **8 passed**, 149 deselected in **2.12 s**.
- No existing assertion was changed, removed or weakened. Twenty-one new nodes
  exercise the requested behavior and persistence boundaries. No new marker or
  test-only substitute for a required instrument repair.

### Complete JSON / text-state write classification -- condition (a)

**By-item record** means replace an existing identity or append a new identity;
never discard another identity. For invocation snapshots this is append to a
fresh filename: the original product bytes are never rewritten, as required by
CHARC 0358beda. A preset file has ONE identity (its AD-13 filename), so exporting
that same preset replaces that singleton without affecting its sibling. **Derived
view** means regenerated whole from the authoritative state/facts; it is not used
as an alternative item inventory. Product caches are explicitly derived and
evictable, never a review tally or state of record.

The source/AST enumeration is retained in **write-audit.log** (write_audit.py).
It finds all FOUR _json_write call sites below, and the JSON/text writes and
delegations. The helper's temporary JSON and atomic rename are the same logical
record write, not an extra inventory. No unclassified persistent state write
remains. Binary media derivatives are not JSON/text state. **B-F3 correction
(turn 11):** the table below is relocated to the turn-11 candidate and extended
to include non-JSON media outputs; mkdir and stdout are explicitly not file
writes. The turn-11 source/AST lists are in `work/wp5.3/turn11/`.

| Final file:line / call | File written | Class | Why it cannot shrink, or source of whole regeneration |
|---|---|---|---|
| tools/reviewpack/build.py:126 (:141/:144) | Atomic JSON temporary then destination | by-item record: replace-or-append, never shrinks | Shared helper copies previous items, replaces/appends incoming identities through _store_item, then atomically renames. Used by ALL four sites below; independent three-path control proves both rows remain and incoming state is not mutated. |
| tools/reviewpack/build.py:1238 | records/<group>-excerpts.json | by-item record: replace-or-append, never shrinks | Same helper; executed two-manifest regression preserves other clip's timings/error facts and replaces rerun clip. B-F2 adds its actual fresh excerpt file name. |
| tools/reviewpack/build.py:1244 | records/pack.json (no runnable sources) | by-item record: replace-or-append, never shrinks | Same helper; per-item error rows retained even when a whole group fails preparation. |
| tools/reviewpack/build.py:1292 | records/pack.json (finished group) | by-item record: replace-or-append, never shrinks | Same helper and identity writer; old groups remain alongside current results. |
| tools/reviewpack/build.py:1381 | records/pack.json (non-page stage) | by-item record: replace-or-append, never shrinks | Same helper; page excluded from this write. One CLI lock spans load through save. |
| tools/reviewpack/build.py:294 / :1015 | records/<group>[-neutral][-N].json, through runner --record | by-item record: append-only invocation history, never shrinks | _fresh allocates a new name; product _write_record (headless_export.py:1413) opens exclusively and refuses overwrite. Two-manifest regression proves both prior two-item records remain byte-identical while two new one-item snapshots append. Never merge/rewrite product record bytes. |
| tools/reviewpack/build.py:927 | settings/starter-store[-N]/<preset>.json, via install_starters | by-item record: append singleton preset identities, never shrinks | Store folder is fresh; product installs both fixed named records. No previous store or preset record is removed. |
| tools/reviewpack/build.py:932 | presets/<AD-13 name>.json, via export_preset | by-item record: replace same singleton identity, never shrinks | Each call replaces only its one preset file; both commissioned identities are always exported. Product AD-13 schema/values preserved. Missing output is pending, not quietly omitted. |
| tools/reviewpack/build.py:927 | fresh store's .starters-installed marker | derived view: regenerated whole from product store state | Product marker 1 is written only after the two starter records exist; it is operational installation state, not a review inventory. |
| tools/reviewpack/build.py:1309 / :1322 / :1325 | .reviewpack.lock | by-item record: exclusive singleton holder record (transient) | Exclusive create, holder pid/time write, removal on owning exit; never overwrite another holder. Intentional removal is the R4-3 release protocol, not item-state pruning. A stale holder is never removed by the instrument. |
| tools/reviewpack/build.py:1025 | logs/<fresh runner-record stem>.log | derived view: regenerated whole from invocation facts | Safe stdout/stderr, exit and elapsed facts for that immutable invocation; fresh record stem keeps old logs. No item selection is reconstructed from logs. |
| tools/reviewpack/page.py:237 | README.md | derived view: regenerated whole from state-of-record display/usage policy | Display conversion, link-check meaning, sheet-conflict recovery and Limits; no item inventory or owner votes. |
| tools/reviewpack/page.py:244 | index.html | derived view: regenerated whole from pack state | All saved rows, catalog pending, starter presence and sheet conflicts; HTML escaping and relative links; never written back to state. |
| tools/reviewpack/sheet.py:210 / :211 | review-sheet.csv, atomic temporary then rename | derived view: regenerated whole from pack state plus preserved owner answers | B-F1: answered stale rows retained verbatim, blank rows follow available pairs or stay if unavailable; other rows updated/appended even on conflict. Conflict raised only AFTER guarded replacement. No inferred votes. |
| tools/reviewpack/build.py:1428 | tally stdout print; no file write | stdout only, not persistent state | Votes/artifacts from strict CSV; pending from catalog minus accounted state. No state mutation. Earlier :1418 was a print, not a file-write site. |
| tools/reviewpack/build.py:1007 | output-folder mkdir loop, including cache | mkdir only, not a cache-file write | Earlier cache/write attribution to the invocation region was imprecise. This call creates guarded directories, not JSON or item records. |
| tools/reviewpack/build.py:315 / :1015 | runner --cache-dir argument / subprocess delegation | derived view: product regenerates cache from source and parameters | Product cache stamps and completion index (cache/store.py:471/:689); evictable acceleration data, never CP5 item records. No product edit; real tiny all-stage test exercises it. |
| tools/reviewpack/page.py:82, callers build.py:1059 / :1128 / :1135 | thumbnail and pair-still JPEGs | fresh name or scratch, not state | _aid_files/create allocates fresh guarded names; page._save writes the derived JPEG. Item state links only completed aids. |
| tools/reviewpack/build.py:750 / :763 / :798 | extracted PNG frame, rotated FFmpeg frame and stripped PNG | fresh name or scratch, not state | Fresh aid frames or private .frames-UUID scratch; source pixels unchanged. Unrotated helper scratch removed after guarded copy; rotated command writes guarded target. |
| tools/reviewpack/build.py:1071 / :1090 / :1097 | browser sRGB scratch PNG, copied frame and ICC-tagged frame | fresh name or scratch, not state | A fresh scratch target is normalized then removed; only the fresh viewing frame is overwritten. Product output and source are not edited. |
| tools/reviewpack/build.py:632 / :668 | excerpt MP4/MOV, FFmpeg stream copy | fresh name or scratch, not state | _fresh names every attempt before guarded FFmpeg output; two-run control proves GX011604-2.mp4 is recorded. No source mutation or re-encode. |
| tools/reviewpack/build.py:825 / :898, caller :1105 | pair MP4, FFmpeg hstack encode | fresh name or scratch, not state | Fresh guarded viewing-aid target; failed owned attempt cleaned by _aid_files. Corrected product remains the item of record. |

**Condition (b), acceptance transfer:** Reviewer B must explicitly check EVERY
site/class above and EXECUTE the two-manifest sequence against a fixture state.
The excerpt-record and immutable-runner-snapshot regressions provide the two
sequences: first two commissioned items, then one; untouched item row/record
must remain, rerun identity must update, pack count stays 128, and page must not
rewrite pack.json. Do not substitute a static read for this execution. Reviewer
B is at the dispatcher's seat; no reviewer or mailbox action was started here.

### Verification loop: suspect / confirm independently / fix / repeat

1. **Confirmed and fixed [MINOR]:** excerpt sidecar shrinks on targeted rerun.
   RED proves count loss; shared JSON merge fixes every item-record site, not
   only excerpts. Independent verification.py then exercises three record
   filenames with two old identities and one update: both rows survive, only
   rerun facts change, and caller's one-row input remains unchanged.
2. **Confirmed and fixed [MINOR]:** missing presets falsely complete the page;
   page write-back permits stale state; lock absence permits overlap. RED/GREEN
   proves missing presets are pending, page retains existing bytes (or creates
   no state), held-lock refusal and release on normal/error exit. Independent
   stale-holder control uses an inactive-looking pid and old timestamp, verifies
   refusal with both fields/manual-delete instruction, and identical lock bytes.
3. **Confirmed and fixed [MINOR]:** slash redaction changes actual product
   diagnostics. The paired seven-row test proves safe paths and unchanged
   ratios/box names together. Metadata and name-only controls remain green.
4. **Confirmed and fixed / preserved [ADVISORY]:** V-R done/unrelated-HLG
   failures and zero-rate/timeout escapes are RED then GREEN. Actual float(None)
   already reaches the right catch; its previously missing coverage is added.
   README/page output inspection verifies link-check wording and both Limits.
5. **Rejected suspect [false positive, no code change]:** raw per-group runner
   records might shrink on a one-item rerun. _fresh, the runner's exclusive
   record writer, and an executed two-manifest test independently show old
   bytes remain and new snapshots append. Preserve their immutability under
   the earlier ruling instead of treating an invocation snapshot as an
   aggregate. This is the explicit append-only classification above.
6. **Repeat pass / no new finding:** full **157-node** suite, write-site AST
   enumeration, scoped diff/docstrings/comments, output guards and independent
   merge/lock/documentation controls find no additional defect. Formatting
   corrected only mechanical layout; first ruff and mypy are clean. No public
   interface, owner-input ambiguity, product defect or new STOP surfaced.

### Final light runs / AD-30 / locks

PowerShell sets PYTHONPATH=scripts; commands from this worktree root:

```text
uv run pytest -q tests/test_reviewpack.py --basetemp=work/wp5.3/tmp -p sandbox_mkdir_shim -p no:cacheprovider -m "not gpu and not footage and not gui and not fullclip" --durations=0 --junitxml=work/wp5.3/turn10/full1.xml
uv run ruff check tools/reviewpack tests/test_reviewpack.py
uv run ruff format --check tools/reviewpack tests/test_reviewpack.py
uv run mypy
```

- **157 passed in 47.43 s**, exit 0; full1.xml has zero failures/errors/skips.
  No existing assertion changed. Exactly one existing slow node; no new
  slow/GPU/footage/fullclip marker. The real tiny headless/FFmpeg integration
  remains force-CPU; its pre-existing automatic product encoder policy is
  unchanged, and no owner-media/performance figure or visual judgement is run.
- Sole slow integration aggregate **22.759 s**. Slowest parallel node:
  test_missing_starter_presets_are_pending_until_both_tables_exist[0],
  **3.281 s** in the full pass. First measured RED **2.632 s**, targeted GREEN
  **4.748 s**; each under five seconds, so no marker change required. All 157
  node statuses/times are in per-node-final.csv. verification.log joins counts,
  independent checks and write sites; timings1.log preserves first measurements.
- Final ruff **All checks passed**, format **6 files already formatted**, mypy
  **Success: no issues found in 151 source files**, all exit 0, retained in
  ruff-final.log/.exit, format-final.log/.exit and mypy-final.log/.exit.
  Inherited VIRTUAL_ENV is ignored by uv; no --active or other-worktree access.
- verification.log/.exit: independent merge, stale-lock and documentation
  checks plus JSON-site enumeration, exit 0. scope-lf-audit.log/.exit records
  the four owned changed paths, zero CR, public docstrings, whitespace and no
  unowned edit. Whole-tree/two-leg gate remains at the dispatcher's seat.

Only owned build.py, page.py, tests/test_reviewpack.py and this ledger change.
Every new production write, including lock and JSON temporary, is guarded under
the configured pack root. Footage and source pixels remain untouched; no main
working tree, other worktree, local config, frozen interface, src/, shared
helper, other test, dependency, Qt import or OS-specific behavior was changed.
No git mutation/commit, mailbox post, real-media RUN REQUEST or owner judgement.
R4-5/R4-6 remain OUT Limits and must be carried to the later real-build report;
no out-of-envelope support is claimed. Reviewer A remains CONVERGED at round 4.
**YIELD for executing Reviewer B at the dispatcher's seat**, then the scheduled
RUN REQUEST ladder; no further A round requested.

## Session 5 / Turn 11: Reviewer B remediation

### Boundary, adjudication and scope

Fresh session 5 starts on **2a1e15b1**. Session 4 retired at dispatcher-supplied
**217,380 depth_input_tokens**. This session's ID and depth remain for the
dispatcher to fill; no estimate is made. Reviewer A remains **CONVERGED at round
4**, under CHARC e4d56665. Reviewer B was an **EXECUTING Claude pass** at the
dispatcher on that candidate, including two manifests, page-state SHA and stage
lock; its verdict is **NO_NEW_CRITICAL_MAJOR**. Read-only findings source:
`C:\Users\rwsmy\clearwater-review-evidence\wp5.3\B\review.txt`. It was not copied
into this repository. The turn-11 dispatch adjudicates all six findings; no
ruling, owner input or product/interface decision remains outstanding here.

This turn bundles the TWO explicitly commissioned instrument repairs (B-F1 and
B-F2) and their proof/ledger updates into the required one logical remediation
commit. No existing test assertion was changed, removed or weakened. All new
evidence is ignored **work/wp5.3/turn11/** in this worktree; tests use the
prescribed **work/wp5.3/tmp/** plus sandbox shim. Only planted sources and
committed tiny fixtures were opened, never the owner footage folder.

### Per-finding RED / GREEN and disposition

| Finding | Classification / RED evidence | GREEN / disposition |
|---|---|---|
| B-F1 | ACCEPTED MINOR, IN. Four cases cross blank/answered rows with changed/unavailable outputs. Unchanged code: blank cases return 2 instead of 0/1; answered cases leave 1 row instead of 126. b-f1-red.log/.xml: **4 failed, 157 deselected in 6.46 s**, exit 1. | Blank rows follow the current available identity; blank unavailable rows stay unchanged. Any owner cell protects a stale identity; the status-only viewing_aid_failed cell does not count as an answer. Conflicts preserve the full old record, while every other row updates/appends. **SheetConflictError is raised only AFTER the guarded temp-and-rename write** and carries the conflicting item names. page prints each name to stderr, renders their message plus recovery, and exits 2; ordinary item failures remain 1. README repeats the one-sentence recovery: blank that row's owner cells to accept the current pair at the next page, or restore the earlier output. |
| B-F1 controls | Targeted b-f1-green.log/.xml: **9 passed, 152 deselected in 14.11 s**, exit 0 (includes existing preservation and migration controls). | Four new CLI cases assert later IMG_6702 row added, 126 sheet rows, unchanged pack.json bytes, relative links resolve, stale row bytes/quoting/CRLF survive, conflicts name IMG_6751, and clearing the answer permits the next rebuild. Nine further nodes cover each of eight owner columns and the status-only aid flag. No owner answer transfers to a regenerated output. Existing voted-row byte-preservation, BOM, legacy-header migration, aid failure, and interrupted atomic-write controls remain green. |
| B-F2 | ACCEPTED ADVISORY, IN. Two-item clip run then one-item rerun: the persisted sidecar lacks excerpt.name (None instead of GX011603.mp4). b-f2-red.log/.xml: **1 failed, 161 deselected in 1.40 s**, exit 1. | Every excerpt sidecar row now has name from the actual prepared path (empty only on a failed excerpt with no file). The successful two-manifest control proves GX011603.mp4 retained, GX011604-2.mp4 recorded on rerun, and both names equal pack.json; sidecar stays 2 rows and pack stays 128. b-f2-green.log/.xml: **11 passed, 160 deselected in 1.32 s**, exit 0, including nine owner-cell controls and the earlier failed-excerpt merge regression. |
| B-F3 | ACCEPTED ADVISORY, IN, ledger correction only. | The turn-10 write-site table above is explicitly corrected/relocated to this head, including ALL four _json_write calls and all non-JSON outputs. Thumbnails, extracted/browser frames, pair stills, pair MP4s and excerpt containers are **fresh name or scratch, not state**. tally :1428 is a stdout print; :1007 is a directory-creation loop; actual cache delegation is :315 / :1015. write-audit.log, write-delegations.log and verification-final.log retain the source/AST enumeration. No persistent write lacks a class. |
| B-F4 | ACCEPTED ADVISORY, IN, MEASURE ONLY. | No test/marker change. The two existing missing-starter cases take **4.467 / 4.468 s** in full1 and **4.152 / 4.403 s** on the final code (JUnit setup+call+teardown aggregates). Both below 5 s in these serial light runs; dispatcher still measures under -n 4 at the gate. |
| B-F5 | LIMIT ADVISORY, OUT OF ENVELOPE; staged for report. | A hand-built pack.json with no catalog row counts the missing item as pending without listing its name. Commissioned CLI initialization seeds all 128 catalog rows. No support for a hand-built alternate inventory is claimed; do not edit product or widen this turn. |
| B-F6 | LIMIT ADVISORY, IN, retained for real-build report. | The pair clip relies on the product retaining the source's colour description; stills rely on retaining excerpt timestamps. A violated adapter check becomes viewing_aid_failed, retains the product link/sheet row, and fails the piece loudly. Only fixtures prove this here; the real-build logs/records remain to be inspected at the dispatcher's seat. |

**State accounting:** full catalog **128**, headline **115**, candidates **11**,
expected refused **2**, owner sheet **126** when all items are accounted for.
The four new page regressions start with 128 accounted state rows and one saved
sheet row; rebuild adds the other 125 sheet rows despite any conflict and never
changes pack.json bytes. The excerpt rerun keeps 128 state rows / two sidecar
rows; only the targeted item's excerpt identity changes. No denominator loss.

### Verification loop: suspect / confirm independently / fix / repeat

1. **Confirmed and fixed [MINOR]:** a stale or unavailable pair blocks all CSV
   updates, including a blank row. Four pre-fix failures distinguish the old and
   new behavior. The fix separates answered conflicts from blank identities,
   completes the atomic write, then reports conflicts. An independent planted
   two-conflict sequence (not the pytest helper) verifies an absent item and a
   changed item simultaneously, a later P-Z row still appended, byte-identical
   quoted/multiline records with BOM retained, artifact-only/above-surface-only
   answers protected, and blank recovery accepted. All controls pass.
2. **Confirmed and fixed [ADVISORY]:** the excerpt sidecar omits the fresh file
   identity. RED observes None; GREEN independently compares literal filenames
   GX011603.mp4 / GX011604-2.mp4 with both sidecar and state, and checks existence.
   Existing failed-excerpt replace-or-append controls still pass; no excerpt
   policy, stream mapping or fallback is changed.
3. **Rejected suspect [false positive]:** status-only viewing_aid_failed could
   be mistaken for an owner answer. The explicit ninth owner-column control
   proves it is excluded and the blank row follows its new pair. Existing
   aid-failure vote/denominator controls still pass. No extra repair required.
4. **Static cleanup, fixed:** first ruff found N818 (new exception needed Error
   suffix) and SIM102 (nested condition); renamed SheetConflictError and combined
   the condition. Format was already clean; mypy was already green. The full
   suite was repeated on the resulting final code. No assertion was weakened.
5. **Repeat pass / no new finding:** final full 171-node suite, independent
   persistence/CSV-byte/BOM checks, scoped diff, write-site enumeration, public
   production docstrings and LF audit find no additional issue. Initial audit
   script overreached into inherited test functions and nested local helpers;
   narrowed its public-API check to module/class production declarations, with
   no edit to inherited code. The instrument writes only guarded destinations;
   no new state inventory or shrinking assignment is introduced.

### Final light checks and measured nodes

PowerShell sets PYTHONPATH=scripts. Each command's output and exit are retained
under **work/wp5.3/turn11/**; only summary facts are reported here.

```text
uv run pytest -q tests/test_reviewpack.py --basetemp=work/wp5.3/tmp -p sandbox_mkdir_shim -p no:cacheprovider -m "not gpu and not footage and not gui and not fullclip" --durations=0 --junitxml=work/wp5.3/turn11/full-final.xml
uv run ruff check tools/reviewpack tests/test_reviewpack.py
uv run ruff format --check tools/reviewpack tests/test_reviewpack.py
uv run mypy
uv run python work/wp5.3/turn11/verification.py
```

- **full1.log/.xml:** 171 passed in **84.40 s**, exit 0, before mechanical lint
  cleanup. **full-final.log/.xml:** **171 passed in 74.49 s**, exit 0, on final
  code; zero failures, errors or skips. This includes the sole existing slow
  real headless/FFmpeg integration, aggregate **27.685 s** (first run 35.490 s).
- Fourteen new nodes, all parallel-leg; none measured above 5 s in either full
  light pass. All node identities and aggregate times are retained in
  **full1-nodes.csv / full-final-nodes.csv**. The two B-F4 node measurements are
  given above; no marker or timing-bound assertion was added. This is not an
  EXCLUSIVE run or a product performance figure of record.
- **ruff-final.log/.exit:** All checks passed, exit 0.
  **format-final.log/.exit:** 6 files already formatted, exit 0.
  **mypy-final.log/.exit:** Success: no issues found in 151 source files, exit 0.
- **verification-final.log/.exit:** independent checks, complete write/delegation
  enumeration, public production docstrings, whitespace and scope, exit 0.
  All five changed paths have **0 CR**. No source or shared-interface edit.
  uv ignores the inherited VIRTUAL_ENV mismatch as before; no --active or
  other-worktree environment is used.

Only owned build.py, page.py, sheet.py, tests/test_reviewpack.py and this ledger
change. No dependency, Qt, OS-specific behavior, src/, frozen interface, shared
helper, fixture, existing test, local config or brief was edited. No footage
folder, other worktree or main working folder was accessed. No git mutation,
commit, mailbox post, real-media build or image judgement was performed. B-F5
and B-F6 Limits above are staged for the later real-build report, alongside
the retained R4-5/R4-6 Limits. The report and real-build evidence are not claimed
complete in this turn. **YIELD for the dispatcher's RUN REQUEST sequence**;
the final two-leg gate and CP5 owner judgement remain at their assigned seats.

### Turn 12: B-F1 completion

Starts on **b4416bd7**, turn 11's five files committed unchanged by the
dispatcher. CHARC **79a4f1c7** and the turn-12 dispatch require an explicit
conflict section, both judged/current output identities, current unavailable
status, and an audit of every removal/rename. Session 5 continues; **turn-12
depth_input_tokens: dispatcher to fill**. No self-estimated depth.

**STOP [MINOR, IN; ruling needed on cleanup scope]. Recommended ruling:** retain
the existing cleanup only for a **fresh failed excerpt attempt**, while keeping
all successful excerpts and every existing product output immutable. If the new
ban is intended to include failed attempts, a ruling must also supersede the
existing cleanup assertion before it can be changed. No such assertion was
weakened or changed here. The literal turn-12 requirement ("no path ... removes
... an excerpt copy") is contradicted by build.py:724: an unsuccessful excerpt
validation unlinks its newly written destination, which can be numbered. The
existing **test_excerpt_integrity_rejects_changed_non_tmcd_payload**, final
**tests/test_reviewpack.py:1486**, explicitly asserts that no excerpt MP4 remains
after validation fails. This is an instrument cleanup rule conflict, not a
product defect; no footage or owner decision is involved.

**Cheap independent reproduction:** `uv run python
work/wp5.3/turn12/verification.py` uses only the committed tiny HEVC fixture and
planted worktree files. It plants an earlier accepted GX011604.mp4, runs the
real FFmpeg stream copy into fresh GX011604-2.mp4, and deliberately rejects the
post-copy payload verification. A wrapper around Path.unlink observes the
**21,744-byte GX011604-2.mp4 present immediately before unlink**; afterward it
is absent, the result is excerpt_failed/path=None, and the earlier accepted
copy is byte-identical. Recorded in **verification-final.log/.exit**, exit 0
means the reproduction and its assertions executed, not that the blanket ban
holds. No cleanup behavior was changed. The requested commit subject's blanket
"no numbered output is ever deleted" must not be treated as an audited claim
while this STOP stands.

The independent portions of the turn are complete:

- **[MINOR, IN, fixed] Explicit visible conflicts:** index.html now has an
  escaped `<section id="sheet-conflicts">`, one list entry per conflicting
  item, before the starter tables. A generic item listing is not the assertion
  surface. The section names each conflict and carries the owner recovery step.
- **[MINOR, IN, fixed] Both output identities:** SheetConflictError retains its
  existing items tuple and adds details per item: item, judged_name from the
  preserved CSV row, current_name from state, and current_status. The shared
  format_conflict renders the same facts on the page and on each stderr line;
  absent current output is explicitly `(none)` and absent current state is
  `missing`. Build applies name-only diagnostic sanitizing; page escapes all
  fact values. The sheet row remains verbatim; new details are computed only
  after the guarded sheet replacement and do not alter votes or identities.
- **[MINOR, IN, verified] Existing product outputs:** the rerun construction now
  asserts BOTH IMG_6751_corrected.png and IMG_6751_corrected_2.png exist before
  and after page, while a judged stale row stays byte-identical. The recovery
  sentence is unchanged: it instructs the owner to blank owner cells or restore
  an earlier output, and executes no file deletion/restoration. There is no
  automatic recovery action or numbered product overwrite.

#### Every filesystem remove / unlink / rename site on the turn-12 candidate

Source grep is **delete-overwrite-audit.log**; independent AST enumeration is
**verification-final.log**. String replace at build.py:64/:90 and dataclasses
replace at select.py:194/build.py:1175 are not filesystem operations. No rmtree,
truncate or filesystem replace call exists in tools/reviewpack/. These twelve
sites exhaust the actual filesystem removal/rename calls:

| Site | Operation | What it can touch in the commissioned CLI |
|---|---|---|
| tools/reviewpack/build.py:144 | roots.rename | Guarded atomic JSON temporary to pack.json or a group excerpt JSON sidecar, at the four known _json_write calls; no media destination. |
| tools/reviewpack/build.py:147 | roots.remove | Only that JSON write's unique `.tmp` sibling, if still present. |
| tools/reviewpack/build.py:187 | roots.remove | _aid_files' registered fresh JPEG thumbnails/pair stills, pair MP4s and private scratch PNGs; never a product PNG/MP4 or excerpt path. A thumbnail name can contain _corrected but is a JPEG derivative under thumbs/. |
| tools/reviewpack/build.py:724 | guarded unlink | **STOP EXCEPTION:** the fresh excerpts/ destination after this attempt's failure, including numbered copies. Earlier existing copies remain protected by _fresh. Executed reproduction above; cleanup left unchanged pending ruling. |
| tools/reviewpack/build.py:757 | roots.remove | PNGs inside this extraction's unique `.frames-UUID` scratch directory only. |
| tools/reviewpack/build.py:759 | guarded rmdir | That same scratch directory, only when empty. |
| tools/reviewpack/build.py:836 | guarded unlink | Private `.size-UUID-index.png` frame used to check each half's displayed dimensions. |
| tools/reviewpack/build.py:1091 | guarded unlink | This browser conversion's newly allocated sRGB scratch PNG, after copying to the viewing frame. |
| tools/reviewpack/build.py:1146 | guarded unlink | Temporary source/corrected PNG frames under pairs/ after making the JPEG pair still and thumbnail. |
| tools/reviewpack/build.py:1325 | roots.remove | Only this stage's exclusive `.reviewpack.lock` on owning exit. Never an output or another holder's lock. |
| tools/reviewpack/sheet.py:230 | roots.rename | Guarded atomic CSV temporary to the requested review sheet; no media file. |
| tools/reviewpack/sheet.py:233 | roots.remove | Only that sheet write's unique `.tmp` sibling, if still present. |

**Overwrite audit:** excerpt stream-copy uses fresh names and FFmpeg -n
(build.py:632/:437). Product writes remain delegated to the shipped runner
(build.py:294/:1015), whose safe numbered-output behavior is unchanged.
FFmpeg -y at build.py:768/:860/:1077 targets new scratch frames, fresh pair aids
or browser scratch; page.py:82 JPEG save and build.py:1097 ICC save target fresh
viewing derivatives. Preset overwrite=True (build.py:932) replaces only the
commissioned preset JSON. JSON/CSV renames replace only their records/views.
The audit confirms no commissioned path removes or overwrites an existing
product output or successful earlier excerpt, but it CANNOT confirm the
stronger statement including fresh failed excerpts.

#### RED / GREEN, verification loop and final checks

All runner output is ignored **work/wp5.3/turn12/**. Same prescribed pytest
command and sandbox shim as turn 11, with --durations=0 and JUnit XML; the sole
existing slow real headless/FFmpeg node is included. No old assertion changed.

| Evidence | Result |
|---|---|
| conflict-red.log/.xml, unchanged tool on b4416bd7 | **3 failed, 171 deselected in 3.83 s**, exit 1. Two real page cases show stderr lacks the judged filename; the exception lacks details. |
| section-red.log/.xml, unchanged tool | **1 failed, 174 deselected in 1.07 s**, exit 1. Direct section-surface assertion fails because the visible conflict section is absent. |
| conflict-green.log/.xml | **8 passed, 167 deselected in 9.58 s**, exit 0. Both current-output states, both stderr output names, unavailable status, exception details, two simultaneous visible conflicts, and four earlier rerun cases. |
| full-final.log/.xml | **176 passed in 54.20 s**, exit 0. Five new nodes plus all 171 earlier nodes; zero failures/errors/skips. Existing assertions retained; rerun assertions strengthened for both files. |
| ruff-final.log/.exit | **All checks passed**, exit 0. |
| format-final.log/.exit | **6 files already formatted**, exit 0. First format check requested two purely mechanical layouts, fixed with ruff format; no behavior/assertion change. |
| mypy-final.log/.exit | **Success: no issues found in 151 source files**, exit 0. |
| verification-final.log/.exit | Independent product/CSV preservation, executed failed-excerpt deletion reproduction, complete delete-site audit, scope, public production docstrings, whitespace and **0 CR on all five changed files**, exit 0. |

Verification loop: **suspect -> confirm** the generic item list/README hides the
actual conflict section and the stderr lacks output names (separate REDs);
**fix** the exception facts plus shared formatted entry and render section;
**repeat** all original preservation/identity tests, the full suite, an explicit
HTML-escaping test on every conflict fact, and the independent two-file/CSV-byte
probe. No additional defect found in the changed paths. The deletion suspicion
was independently **confirmed** by real stream copy plus unlink observation and
is **STOPPED**, not downgraded to a Limit or claimed fixed. The repeat audit
finds exactly the one existing exception and no product-output removal path.

Only owned build.py, page.py, sheet.py, tests/test_reviewpack.py and this ledger
change. Footage, other worktrees, main work/, local config, shared helpers,
fixtures, existing assertions, src/, frozen interfaces and dependencies remain
untouched. No commit, mailbox, real-media RUN REQUEST, owner judgement or
automatic file recovery. **YIELD with STOP for the cleanup ruling** and the
completed conflict-display changes; no blanket deletion guarantee is asserted.
