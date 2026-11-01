# WP5.3 — Visual review pack for CP5 (dispatch brief)

**Status:** FINAL 2026-11-01 on CHARC commission post `05533fa67a11cee3` (file `20261101T081408Z-...-b488ac53.md`, 2026-11-01T08:14:08Z); drafted by CHARC (generation 10, session `clearwater-charc-20261031-2201`); the dispatch fill (base, lane, GATE_CHECKS, yields) folded in by the orchestrator (generation 28) at the end of this brief. AMENDED by CHARC's round-0 ruling `f99fca742e060f14` (2026-11-01T08:27:19Z), folded in verbatim as `## Round-0 ruling` before the Dispatch fill; it GOVERNS where it differs from the text above.
No tripwire (plan section 3): instrument code under `tools/`, no new
dependency, no product module, no frozen interface. Spec v0.5.7, no clause changes. Owner decisions
inside: NONE (the look check and V2 are the owner's at CP5; this package only builds what the owner
judges). The Questions carry CHARC's recommended answers; a round-0 dispute with evidence is a STOP to
CHARC.

| Field | Content |
|---|---|
| ID and title | WP5.3 — Visual review pack: the owner's photos and footage, shallow and deep, corrected by the PRODUCT pipeline at the shipped defaults, paged for the CP5 judgement (V2, D65) with the starter presets shown (AD-13) and a review sheet the owner fills |
| Lane | **CODEX**: `implementer-codex-sol-high` (well-specified instrument; no frozen interface; the Claude lane is at its weekly ceiling until 2026-11-02 10:00Z). Reviewer A = the Claude pass (`claude -p --model opus --effort high`) between turns, to convergence, five-round gate. Reviewer B = the Claude pass at the orchestrator's seat. Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp5.3\`. |
| Tier and size | **STRONG** (the pack is the evidence the owner judges at CP5; a mislabelled pair or a wrong pose misleads an owner-reserved decision). Size S (one instrument package, one page builder, one sheet, one report). Codex STOP line near 250K; the orchestrator names the yields. |
| Base | main at dispatch (`dd3cf1eb` + the fill commit; WP4.3 accepted `28c4a75` is the floor: the runner and the composition root are real). Worktree `.worktrees/wp5.3`, branch `wp5.3`. |
| Goal | A committed, re-runnable instrument `tools/reviewpack/` that (1) selects the CP5 test set by NAME from the inventory of record (section "Test set" below; no scene classification), (2) runs every item through `tools/headless_export.py` (the product's composition root, in-process engine) at the shipped defaults, photos also at the neutral parameters for the source view, (3) writes browser-viewable pairs, thumbnails, side-by-side clips and an `index.html` under `work/wp5.3/`, (4) writes the review sheet the owner fills and a `tally` that applies D65's 80 % rule to the filled sheet, (5) shows both starter presets as the product exports them; plus the report. **Nothing is judged by any agent**: the pack and the sheet go to the owner; CHARC carries the result as CP5. |
| Spec / decision clauses | V2 / D65 (≥ 80 % preferred; no obvious halos, banding, colour errors, shimmer, flicker); D38 / AD-13 (starter presets "Snorkel (shallow)" and "Scuba (deep)", both AD-8's defaults in v1, values shown and changeable by the owner at CP5); AD-8 (the defaults: method c3, caps 2.0, WB gain 3.0, blend 0.0); D96 (shimmer seen at CP5 triggers WP5.4); spec 8.1-8.3 (PNG photos with ICC, MP4 HEVC video, `_corrected` naming); 5.3 (HLG refused: the two HLG MOVs appear as refused items); N8 (sources never modified; the footage folder is read-only); AD-13's privacy rule (file NAMES only in every page, sheet and report; no full paths, no GPS or EXIF content); plan 4.3 (one heavy job on the host at a time; this build is NOT a figure of record, so not EXCLUSIVE, but it is granted and scheduled by the orchestrator against the open windows). |
| Files owned | **NEW:** `tools/reviewpack/__init__.py`, `tools/reviewpack/select.py` (the named test set and groups), `tools/reviewpack/build.py` (CLI: `photos`, `clips`, `presets`, `page`, `tally`, `all`), `tools/reviewpack/page.py` (index and thumbnails), `tools/reviewpack/sheet.py` (sheet writer and tally), `tests/test_reviewpack.py`, `docs/reports/wp5.3-review-pack.md`, `docs/proofs/wp5.3-ledger.md`. **READ / IMPORT only:** `tools/headless_export.py` (library API `main(argv)` or the CLI as a subprocess; Q2), `tools/lookcheck/frames.py` (`run_tool`, `tool_env`, `probe_stream`, `check_output_path`, `excerpt`, `extract`: reuse, never edit), `tools/local_config.py` (`find_footage_file`, the two folders). |
| NOT owned | `src/clearwater/` whole (a product defect found while building is a STOP to CHARC with the evidence, never a fix here); `tools/headless_export.py`, `tools/lookcheck/`, `tools/photo_check.py`, `tools/inventory.py`; `tests/conftest.py`, `tests/fixtures/`; every existing test; `pyproject.toml`, `uv.lock` (no dependency: Pillow, NumPy, FFmpeg and ffprobe only); the register and the decisions log (CHARC's). |
| Locks | Footage folder READ-ONLY: every output path passes `check_output_path` against the working folder root `work/wp5.3/` before a write, and a target inside the footage folder (however spelled) is a configuration error, exit 2. No pixel of a source is modified; every excerpt is a stream copy under `work/wp5.3/excerpts/`. No full path, GPS or EXIF content in the page, the sheet, the record or the report (file names only). No Qt. No new dependency. The product is driven ONLY through `tools/headless_export.py` (no direct engine composition: the pack must show what the shipped application does). The build is run at the ORCHESTRATOR's seat as RUN REQUESTS (the Codex sandbox cannot write `work/` of the main tree); the cell commits the instrument and the tests. |
| Markers | `tests/test_reviewpack.py`: parallel-leg for the pure parts (selection lists, excerpt plan, sheet and tally, page from planted files); ONE `slow` node runs `build.py all` on a planted tiny set (two fixture stills, `tests/fixtures/video/hevc8-bt709-full.mp4`, `--force-cpu`) under `tmp_path` with the reason "runs the headless runner and FFmpeg"; no `footage` node (the real build is the RUN REQUEST). Each node measured first (AD-30); a parallel node over 5 s is `slow` with a reason. |
| Hardware flags | GPU (the runner's default device; CPU fallback is a product matter and is recorded, not forced). Heavy: about 15 min of 4K footage plus about 14 min of phone video plus 73 photos at about 10 min/min at 4K (WP3.21) = roughly 3-4 h of GPU time, in pieces (`photos`, then `clips` per group), in the background at the orchestrator's seat, ONE heavy job on the host at a time (the WP4.6 V7 window and the WP3.6P windows take precedence; the orchestrator schedules). Disk: at least 25 GB free on C: before `clips` (`df -h /c`), about 15 GB written. Not a figure of record; no EXCLUSIVE window needed. |
| Out of scope | Any judgement of the correction (owner, CP5); the V3 figure on real footage (judged in V2 by eye; the synthetic V3 is WP5.1's); parameter changes or preset value changes (owner at CP5; a change becomes a spec/AD-13 amendment by CHARC); the prototype's variants (CP2's pack); Insta360 (ON HOLD); a GUI walkthrough (the owner may open items in the shell by hand; not built here); WP5.4 (conditional on CP5). |
| Debt and decided items | At the accept CHARC writes: AD-13 NOTE (the two starter presets are value-identical in v1; CP5 is where the owner rules whether "Scuba (deep)" diverges); a register row if the build surfaces a product defect (routed as a STOP first); the CP5 record pointer (`docs/proofs/cp5-visual-review.md`, written by CHARC after the owner's sheet). The cell writes no register row and no spec text. |
| Done | Plan 4.5. ruff check, ruff format --check, mypy strict clean on `tools/reviewpack/`; `tests/test_reviewpack.py` green; the real build run at the orchestrator's seat (`photos`, `clips`, `presets`, `page`) with exit 0 and every item accounted for (done, or refused with the product's text); `index.html` opens and every link resolves (a link checker in `page.py --check`); the sheet has one row per reviewable item; `tally` on the EMPTY sheet reports 0 judged without error; Reviewer A converged; Reviewer B returned; the ONE two-leg gate on the final candidate per GATE_CHECKS at dispatch (no fullclip leg: this package adds no fullclip node); the report written. Then CHARC hands the pack to the owner for CP5. |

## Why

Plan section 6: "WP5.3 produces the corrected test set and the starter-preset samples for CP5";
checkpoint CP5 "Judges the corrected test set against the 80 % rule and the artifact list (D65);
views the starter presets" (plan :138). CP2's pack (WP1.3, WP1.3D) showed the owner the PROTOTYPE
under three variants on extracted frames; CP5 must show the PRODUCT as shipped, on the owner's own
files end to end (decode, analysis with temporal smoothing, render, encode, metadata), because that
is what V2 accepts. The owner's phone footage (2026-10-29) gives the shallow photos and phone video,
the Snorkel folder the shallow GoPro set, the SCUBA folder the deep set (spec: "spanning shallow and
deeper conditions").

## Test set (by name; `select.py` carries these lists verbatim and a test asserts them)

Names come from `docs/reports/inventory-2026-10-29.md` (section 2 and 10) and the 2026-10-18
inventory CSV durations (`work/reports/inventory-20261018T235556Z.csv`). Every file is located with
`tools/local_config.find_footage_file` (stem lookup, missing or ambiguous = configuration error).

| Group | Items | Treatment |
|---|---|---|
| **P-A photos** | the 62 `Phone/*.HEIC` and the 2 JPGs that are NOT in P-Z below (`IMG_*.JPG` outside the Z/M list) | runner at the defaults, 8-bit PNG (`--bit-depth 8`), provenance on; plus a `--neutral` export as the source view (Q1) |
| **P-Z photos (pre-corrected candidates)** | `IMG_6791.JPG`, `IMG_6793.JPG`, `IMG_6794.JPG`, `IMG_6795.JPG`, `IMG_6798.JPG`, `IMG_6799.JPG`, `IMG_6800.JPG`, `IMG_6801.JPG`, `IMG_6802.JPG` (inventory section 10 (b)) | same treatment; OWN section and OWN tally rows; excluded from the headline 80 % figure, reported beside it |
| **V-S GoPro Snorkel** | the 26 `Snorkel/GX0116xx.mp4` | whole clip when duration ≤ 45 s; else ONE 30 s stream-copied excerpt starting at 40 % of the duration (Q3) |
| **V-D GoPro SCUBA** | the 8 `SCUBA/GX0115xx.mp4` and `GX011600`, `GX011601` | same rule (GX011589 6.4 s and GX011592 42.3 s whole; the other six excerpted) |
| **V-P phone video** | the 17 non-HLG `Phone/IMG_*.MOV` | whole clip (all under 2 min) |
| **V-R refused** | `IMG_6704.MOV`, `IMG_6772.MOV` (HLG, Dolby Vision) | run through the runner; the refusal text is recorded and shown; no review row |
| **V-Z video pre-corrected candidates** | `Phone/dp_color_video_1791675261.mp4`; `edits/compilation-20261010-1080p60.mp4` (whole clip when ≤ 45 s, else excerpt) | same treatment as V-S; OWN section and OWN tally rows, excluded from the headline figure |

Headline tally set = P-A + V-S + V-D + V-P (about 64 photos + 34 GoPro + 17 phone items). The
above-surface question is the owner's at review time (inventory 10 (a): none can be named from tags;
the sheet has a column for it).

## The design (the cell builds this; round 0 may dispute with evidence)

```
work/wp5.3/
  photos/<stem>_corrected.png           runner output, defaults            (P-A, P-Z)
  photos/<stem>_neutral.png             runner output, --neutral = the source view (Q1)
  excerpts/<stem>.mp4 | .mov            stream copies (or whole-clip copies are NOT made: a whole
                                        clip is read in place from the footage folder, read-only)
  clips/<stem>_corrected.mp4            runner output, defaults            (V-S, V-D, V-P, V-Z)
  pairs/<stem>_pair.mp4                 source | corrected side by side, half size each (Q4)
  pairs/<stem>_<pct>.jpg                stills at 10 / 50 / 90 % of the item: source left, corrected right
  thumbs/<stem>_{source,corrected}.jpg  short side 540, sRGB (Q5)
  presets/Snorkel (shallow).json, Scuba (deep).json   as the product exports them (Q6)
  records/<group>.json                  the runner's --record files (file names only, by design)
  review-sheet.csv                      one row per reviewable item (Q7)
  index.html                            sections per group; how to judge (D65); presets; refused
  logs/
```

1. **`select.py`**: the lists above as constants, `items() -> tuple[Item, ...]` with `stem`, `group`,
   `kind`, `excerpt: bool`, resolved paths through `find_footage_file`; the excerpt plan from the
   probed duration (`probe_stream`): start = 40 % of duration, length 30 s; the ACTUAL start is
   whatever FFmpeg's keyframe seek gives (`-ss` before `-i`, `-c copy`, `-map 0`), probed back and
   recorded.
2. **`build.py photos`**: for each P item two runner invocations into `photos/` (defaults with
   `--suffix _corrected`; neutral with `--suffix _neutral`), one `--record` per group under
   `records/`; cache not needed for photos. The runner's exit status and every failed item are
   recorded; a refusal or failure is a pack row with the text, never a crash of the build.
3. **`build.py clips`**: excerpts first (stream copy, probe check: stream count and codec tags equal
   the source's; else exit 2), then the runner over the group with `--cache-dir work/wp5.3/cache`
   and `--record`; then pairs (Q4) and stills (`extract` on the source excerpt and on the corrected
   clip at the same pts, `frames.py`), thumbs.
4. **`build.py presets`**: the shipped starter presets written through the product's own preset
   exporter (Q6) into `presets/`, and their values rendered on the page.
5. **`build.py page`**: `index.html` (plain HTML, no script, relative links, file names only), the
   sheet (Q7), and `--check` that every `href`/`src` resolves under `work/wp5.3/`.
6. **`build.py tally SHEET`**: prints per group and for the headline set: judged n, preferred n and
   fraction, the five artifact counts, above-surface count; the headline line reads
   `headline: <preferred>/<judged> = <pct> %  (D65 bar 80 %)`; exit 0 always, no judgement words.
7. **The report** `docs/reports/wp5.3-review-pack.md`: what ran (commands, exit statuses, counts per
   group, the excerpt table with planned and actual starts, informal wall times), the refused items
   with the product's text, any failed item, where the pack is, how the owner uses the sheet, and
   the statement that no agent judged any image. Ends with the empty CP5 sheet header.

## Questions (CHARC's recommended answers; the cell builds these unless round 0 disputes)

- **Q1. Source view for photos.** Recommended: the runner's `--neutral` export (V9 identity path):
  same orientation (AD-24), same ICC handling, same bit depth as the corrected output, so the pair
  differs ONLY by the correction. The page says so in one sentence. Alternative (not recommended):
  an FFmpeg or Pillow decode of the HEIC, which would mix two readers' orientation and colour rules
  into the pair.
- **Q2. Runner invocation.** Recommended: the CLI as a subprocess (`uv run python
  tools/headless_export.py ...`), one process per group, so the pack shows the shipped runner and a
  failure is isolated; `--record` per group. Settings dir = a pack-local folder (`work/wp5.3/
  settings`, so the owner's real settings are untouched).
- **Q3. Excerpt rule.** Recommended: whole clip ≤ 45 s; else one 30 s excerpt at 40 %. 30 s is
  fifteen smoothing windows (2 s): the analysis settles and the owner sees motion. The excerpt is a
  stream copy, so the product receives the real container, tags and data tracks; its start is
  keyframe-aligned and the actual start is recorded. A clip that fails stream copy is run whole.
- **Q4. Side-by-side clips.** Recommended: FFmpeg `hstack` of the source excerpt (or whole clip) and
  the corrected output, each scaled to half width (4K: 1920x1080 each, 3840x1080 out; phone
  1920x1440: 960x720 each), NVENC HEVC 8-bit 4:2:0 at the source's colour tags and frame rate,
  audio dropped, a 2-pixel white separator. The product's own output stays linked beside it as the
  item of record; the pair clip is a viewing aid.
- **Q5. Thumbnails and pair stills.** Recommended: Pillow; convert the output PNG to sRGB with
  `ImageCms` from its embedded profile (the Display P3 photos otherwise show desaturated in a
  browser that ignores ICC); when no profile is embedded, no transform; JPEG quality 90; short
  side 540 (thumbs) and 1080 per half (pair stills). Video stills: `frames.extract` to PNG then the
  same path.
- **Q6. Presets.** Recommended: call the product's preset export for the two shipped starter presets
  by their AD-13 names through `clearwater.config` (the cell locates the shipped definitions, cites
  file:line in round 0); the page renders both value tables and states verbatim: "In v1 both starter
  presets carry AD-8's defaults, so the corrected items on this page are what both presets produce;
  at CP5 the owner may change either preset's values (AD-13)."
- **Q7. The sheet.** Recommended CSV columns: `item`, `group`, `kind`, `source_name`,
  `corrected_name`, `preferred` (yes / no / undecided; blank = not judged), `halos`, `banding`,
  `color_errors`, `shimmer`, `flicker` (blank or yes), `above_surface` (blank or yes), `note`. UTF-8,
  comma, header row; the owner fills it in any spreadsheet. `tally` reads it back strictly (unknown
  value = error naming the row).
- **Q8. Order and scheduling.** Recommended RUN REQUEST order at the orchestrator's seat: `photos`
  (about 1 h, GPU), `presets`, `page` (so the owner can start on photos), then `clips` V-P (phone,
  about 40 min), V-S, V-D (about 2.5 h), then `page` again. Each piece is one heavy job; none runs
  while a window is open.

## Task ladder (the cell; depth read at every yield)

1. Read and map: this brief, `tools/headless_export.py` docstring and `main`, `tools/lookcheck/
   frames.py` (`excerpt`, `extract`, `check_output_path`), `tools/local_config.py`, AD-13 / AD-8 in
   `docs/decisions.md`, the inventory report sections 2 and 10. Round-0 note: the Q6 preset location
   (file:line), the runner flags used, any dispute. `uv sync`.
2. RED: `tests/test_reviewpack.py` (selection lists and groups; excerpt plan arithmetic; the
   footage-root refusal; sheet write and tally on a planted sheet including the error path; page
   build and `--check` on planted files; the `slow` end-to-end node on the tiny planted set).
3. GREEN: `select.py`, `sheet.py`, `page.py`, `build.py`.
4. Reviewer A rounds to convergence (ledger per round).
5. RUN REQUESTS to the orchestrator in Q8's order; the cell reads the records and the logs back,
   fixes instrument defects (a PRODUCT defect = STOP to CHARC with the evidence), rebuilds the page.
6. Report; Reviewer B at the orchestrator's seat; the one gate; accept.

## Round-0 ruling (CHARC `f99fca742e060f14`, verbatim; binding)

RULING on e03fc37c (WP5.3 round 0), PRIMARY: CHARC. All three recommended answers GRANTED, each with one constraint. The brief is amended by this message (fold the four lines below into the brief at the next commit on the wp5.3 branch; Status line cites this id).

R0-1 GRANTED: an instrument-local, name-only photo resolver in tools/reviewpack/select.py for the commissioned photo suffixes (.HEIC, .JPG, case-insensitive) and the exact inventory names; it mirrors find_footage_file's missing / ambiguous refusals and its link / junction pruning; find_footage_file stays the resolver for every video item and tools/local_config.py is not edited. CONSTRAINT: a test plants a root with a duplicate name in two folders and asserts the ambiguous refusal, and one with a junction and asserts the prune (the same two properties the video resolver proves).

R0-2 GRANTED: a rotation-aware viewing adapter inside tools/reviewpack/ for the pair clips and pair stills of rotated items; tools/lookcheck/frames.py is not edited and keeps serving unrotated items. CONSTRAINT: the adapter applies the display orientation by FFmpeg's own default autorotate on BOTH halves (source and corrected read the same way; no hand-written transpose), asserts both halves have equal rotated dimensions before hstack, and is proved on tests/fixtures/video/rotated.mp4 with the oriented dimensions asserted. The product's corrected output stays linked as the item of record; the page says the pair clip is a viewing aid.

R0-3 GRANTED as recommended: every V-P item whole, IMG_6762.MOV (749 s) included and run LAST within V-P; the brief's "all under 2 min" was my error; the schedule estimate for V-P is the measured durations at your seat (about 27 min of 1080p / 1440p footage). No scope change.

Q6 noted: presets.py:42 / :45 / :228 / :478 / :504; pack-local store, both starters exported. R0-4 noted (the CSV copy under the worktree's gitignored work/ is fine).

Codex turn 2 (RED) resumes on this post. Claude figure 84 % noted.

## Dispatch fill (orchestrator generation 28, 2026-11-01; FINAL)

- **Status:** FINAL on CHARC commission post `05533fa67a11cee3` (file `20261101T081408Z-...-b488ac53.md`, 2026-11-01T08:14:08Z).
- **Base:** main `dd3cf1eb` plus this fill (docs only); the worktree is created from main at the fill commit. Worktree `C:\Users\rwsmy\clearwater\.worktrees\wp5.3`, branch `wp5.3`. Codex session: a FRESH one (its id is recorded in the ledger after turn 1).
- **Lane:** CODEX, `implementer-codex-sol-high`, driven by `scripts/codex_cell.py` (evidence `C:\Users\rwsmy\clearwater-review-evidence\wp5.3\cell\`; Reviewer A rounds under `...\wp5.3\rN\`). Paces at this dispatch (read 2026-11-01 08:15:23-24Z): Codex 0.196 (11 % used at 56.0 % of its window, resets 2026-11-04 10:07Z) vs Claude 0.992 (84 % at 84.7 %, resets 2026-11-02 09:59Z). Lane share at this commission: Codex 3 live packages (WP3.6P, WP5.3, WP5.1); Claude 1 (WP4.6, past convergence, at its window/report). Every Codex package's Reviewer A and B are Claude passes, so the Claude lane's burn continues through them until the 2026-11-02 reset.
- **GATE_CHECKS** (`docs/review-gate-clearwater.md` Part 2, at the orchestrator's seat on the final candidate rebased onto main): `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`; the two legs from Git Bash with `PYTEST_ADDOPTS` unset, parallel `uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow and not fullclip" --basetemp=work/<run>-parallel` then serial `uv run pytest -q -rs -m "(gpu or footage or gui or slow) and not fullclip" --basetemp=work/<run>-serial`; NO `fullclip` leg (this package adds no fullclip node); collection identity parallel + serial + fullclip = all; the LF blob check (0 CR) on every file in `git diff --name-only <base>..<candidate>`; no harness gate unless the diff touches `scripts/`, `.claude/`, the kernel docs or `tests/harness/`. **DR-99:** `tests/test_io_video_encode_bench.py::test_run_once_records_the_row_and_deletes_the_output` failing on `telemetry_origin` the same way AND alone on main is recorded under DR-99, not a STOP; any other failure is a STOP.
- **Yields (binding):** turn 1 = task 1 (round 0 in `docs/proofs/wp5.3-ledger.md`: the Q6 preset location with file:line, the runner flags used, the planned RUN REQUESTs, the RED list, any dispute with evidence); then after RED (task 2, committed RED); after GREEN (task 3); after each Reviewer A round is ADJUDICATED (no remediation in that turn); after each RUN REQUEST returns; before the report.
- **RUN REQUESTs (binding):** the cell never reads the footage folder and never writes the main tree's `work/`. Every real build piece (`photos`, `presets`, `page`, `clips <group>`) is a `RUN REQUEST:` line with the exact command runnable from the worktree root, its expected wall time and its outputs under `work/wp5.3/`. The orchestrator runs it at its seat in the background, in Q8's order, only after (a) `df -h /c` (at least 25 GB free before any `clips` piece) and (b) the check that no EXCLUSIVE window is open and no other heavy job runs on the host (the WP4.6 V7 window and the WP3.6P export and memory windows take precedence). The cell's light runs in its sandbox: `PYTHONPATH=scripts uv run pytest -q tests/test_reviewpack.py --basetemp=work/wp5.3/tmp -p sandbox_mkdir_shim -p no:cacheprovider -m "not gpu and not footage and not gui and not fullclip"` (the `slow` end-to-end node included when the cell needs it), `uv run ruff check tools/reviewpack tests/test_reviewpack.py`, `uv run mypy`; the orchestrator runs `ruff format --check` at its seat.
- **Concurrent work:** WP3.6P (Codex, `.worktrees/wp3.6p`), WP5.1 (Codex, `.worktrees/wp5.1`) and WP4.6 (Claude, `.worktrees/wp4.6`) are live. Never read or write another worktree. The orchestrator schedules turns and run requests around the windows; a turn may be held while a window is open.
- **Depth:** the orchestrator reads the turn footer's `depth_input_tokens` and gives it to the cell at the next turn; the ledger keeps a depth table. Evaluate at about 200K; STOP at a step boundary near 250K.

## Reviewer A round 1 F1 ruling (CHARC, 2026-11-01T09:56:58Z, verbatim; binding; it GOVERNS Q3 / design step 1 and the excerpt fallback)

> RULING on 57077b6a (WP5.3 R1 F1, GoPro tmcd), PRIMARY: CHARC. GRANTED, the WP1.5 / WP-T6 form, with the fallback rule REVISED.
>
> Q3 / design step 1 amended: the excerpt maps and stream-copies video, audio and every non-`tmcd` data track (`gpmd`), and REGENERATES `tmcd` with `-write_tmcd 1` from the source's `timecode` tag advanced by the selected start (the WP-T6 trim form, `wp-t6-gate-sizing.md:193-204`); verification by stream IDENTITY (count, codec tags, non-`tmcd` packet identity per matched stream, not mux order), the regenerated timecode start checked against the source tag plus the actual keyframe start. No pixel re-encoded; the lock holds.
>
> FALLBACK REVISED (my brief's "a clip that fails stream copy is run whole" is WITHDRAWN): a failed excerpt is an instrument ERROR for that item, recorded in the group record as `excerpt_failed` with FFmpeg's last stderr line, the item SKIPPED by the clip pieces and listed on the page under "not built"; the build goes on and exits nonzero at the end. Whole-clip export of a long GoPro source happens only on an explicit RUN REQUEST naming the clip (the orchestrator asks me first if more than two). Reason: a silent whole-source fallback turns a 30 s piece into hours of GPU and misdescribes the pack; failing loudly is cheaper than any heuristic.
>
> F2 (make_zero + displayed start verified), F3 (explicit NVENC quality for the viewing aid: the product's `standard` mapping or an explicit CQ; the page states which), F4-F9, F12 as the clean-up, F10 banked (Limit), F11 rejected on the executed control: all noted, no ruling needed. Turn 5 remediates RED-first; Reviewer A round 2 under the 92 % rule (Claude 86 %).
>
> WP4.6 gate after WP5.1 turn 8 returns, then 5c-16 and 5d: concurred.
>
> Owner-pending inputs: none. Open owner decisions: none. Owner action pending: none. Next owner checkpoint: CP5.

## Reviewer A round 2 ruling (CHARC `0358beda`, 2026-11-01T10:52:12Z, verbatim; binding)

> ACK d79a075a (WP5.3 A R2), PRIMARY: CHARC. One pre-emptive ruling so turn 6 need not STOP on F1.
>
> F1: the R1 F1 rule GENERALISES to every per-item failure in the build, viewing aids included: an item whose product export is "done" but whose pair clip, pair stills, size check or thumbnail fails is listed under "Not built" WITH the aid's message AND its product output still linked as the item of record (the owner can still judge it from the corrected file; the sheet row is KEPT with a `viewing_aid_failed` flag so the D65 denominator does not silently shrink), and the piece exits nonzero. Silent loss in any path is the defect; the reviewer's proposed fix is accepted with the two refinements above (row kept, output linked).
>
> F2-F5: concurred as minors for turn 7 (BOM preserved on rebuild; a sheet decoding error names the row and the encoding; the EXIF/GPS word filter withholds only the VALUE-bearing fragment or, if it cannot, the line with a "[withheld]" marker, never a rewrite of the runner's record; the exit check is per piece; "not run" / "cancelled" keep their own status words). Round 3 after turn 7; round 2 of 5.
>
> Claude 87 % noted.
>
> Owner-pending inputs: none. Open owner decisions: none. Owner action pending: none. Next owner checkpoint: CP5.

## Reviewer A round 3 ruling (CHARC `c25ff7a9`, 2026-11-01T17:59:31Z, verbatim; binding)

> RULING WP5.3 Reviewer A round 3 (on ed787934; your dd5bfc66). PRIMARY: CHARC for all seven items; the adjudication turn 8 and the remediation plan follow these. I verified F1 (build.py:1264-1267 filters state["items"] to the manifest's names and :1270 writes it) and F6 (the regex at build.py:87 stops at whitespace; a root-stripped remainder keeps its leading separator) in the worktree at ed787934 before ruling.
>
> R3-1 (F1, MAJOR): CONCUR, fix as proposed. The manifest is a SELECTION filter, never a STATE filter: pack.json is replace-by-item or append, and no option on any stage may reduce its row count. Pending is counted against select.catalog() minus the rows present, not against the loaded state. Rows: (a) full-state fixture + a one-name manifest -> row count unchanged, exactly one row replaced, pending unchanged; (b) a manifest naming an item with no row -> appended. GENERAL RULE for this remediation (third silent-loss path): the turn audits EVERY assignment to state["items"] and every slice of it, and the return lists each site with "cannot shrink" shown (a one-line table in the ledger). A fourth silent-loss finding in round 4 is a STOP to me, not a round.
>
> R3-2 (F2, MINOR): the round-2 form applies verbatim. The neutral source view is a viewing aid: the row is KEPT, the corrected product linked, viewing_aid_failed set, reviewable false, exit 1. Not "failed".
>
> R3-3 (F3, MINOR, out of envelope): BROUGHT IN ENVELOPE (tools/ only, no product edit): catch ImageCms.PyCMSError at the viewing-aid boundary and record it in the SAME form as R3-2. A crash that loses a group's state is the loss the fail-loudly rule exists to prevent; the catch is a few lines. One row with a planted mismatched profile.
>
> R3-4 (F4, MINOR): CONCUR. A per-item probe or prepare fault (ValueError, KeyError, StopIteration, TypeError) is an ITEM error row (message through _safe_text), the piece continues, exit 1 at the piece end. One row per exception class is not needed; one row proving the piece continues past a planted ValueError and one past a planted KeyError.
>
> R3-5 (F5, advisory -> fix): the final `page` with pending > 0 is NOT a finished pack: the page header names the pending count and the groups; `page` exits 2 (distinct from 1 = item failures) while pending > 0; the sheet's tally shows pending. The pack goes to the owner only at pending = 0. V-R (the two HLG MOVs) are RESULTS, not pending items: the clips stage runs them and records the probe's refusal text as the row (status refused), so a Q8 order that never ran V-R shows them pending, which is correct and loud.
>
> R3-6 (F6, advisory -> fix): AD-13's file-name rule binds the pack. After root stripping, any remaining token with a path separator collapses to its LAST component (so "\Phone\IMG_6702.MOV" -> "IMG_6702.MOV"); the Windows-path pattern must survive a space inside the path (match a drive-rooted path up to a known extension or to the end of the quoted span, then collapse to the base name). Rows: the footage-relative form, a quoted path with a space, a POSIX path with a space.
>
> R3-7 (F7, advisory): ACCEPTED AS IS, documented. A BT.1886 -> sRGB conversion applied alike to both halves is a fair viewing aid for stills; add one sentence to the pack README and the page footer ("video stills are converted BT.1886 -> sRGB for display; both halves alike; the player's rendering differs") so the owner does not read a still's tone as the export's. No frame change.
>
> Rounds: round 4 (Claude pass) follows the remediation turn under the 92 % rule; Claude 89 % now. If 92 % is reached before round 4 can start, HOLD the pass (Codex turns continue). Round 5 remains the cap; convergence needs an executing pass.
