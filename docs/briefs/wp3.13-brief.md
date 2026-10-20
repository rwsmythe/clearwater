# WP3.13 — Output naming and safe writing (dispatch brief, APPROVED)

**Status:** APPROVED by CHARC `871a371855bb1630` with rulings (section "Rulings"); draft `6611b3d`, written by
the orchestrator (generation 4) at CHARC's commission (`a05f065e53e696d7`). FINAL at dispatch,
once WP2.3 has merged (no v0.5.4 item changes it). Owner decisions: none inside the package.
- Spec **v0.5.3**. Architecture DRAFT 0.1 section 2 (export data flow: "jobs.naming / safe
  write (D34-D36, D83-D85)") and section 7; AD-19, AD-23. Frame
  `docs/briefs/wp2.4-phase3-frame.md`. DR-16.
- Cell: `implementer-sonnet-high`. Tier **STRONG**.
- Worktree `.worktrees/wp3.13`, branch `wp3.13`, base = the main commit named at dispatch.

**Why.** N8 "source files never modified; existing outputs never overwritten" rests on this
package (plan section 7: "N8 non-destructive | WP3.13"). Export and batch (WP3.14, plan "Depends
on WP3.13") and the photo and video paths of Phase 4 write every output through it.

| Field | Content |
|---|---|
| ID and title | WP3.13 — Output naming and safe writing; plan Phase 3 row WP3.13 (size S); module `clearwater.jobs` (plan 8.1: "Naming, safe writing, export, batch") |
| Goal | Pure functions that turn a source path and the settings into a final output path that collides with nothing on disk, and a safe-write primitive that writes to a temporary name in the destination folder, renames on success without ever replacing an existing file, removes the temporary on cancel or failure, and cleans leftovers on the next start; plus a disk-space estimate and check. |
| Spec / decision clauses | 8.3 "same folder as the source by default; a setting allows a different output folder"; "source filename plus suffix, default `_corrected`"; "Photos change extension to `.png`"; examples "`GX010123.MP4` → `GX010123_corrected.MP4`; `IMG_1234.HEIC` → `IMG_1234_corrected.png`"; "existing files are never overwritten; a number is appended (`_corrected_2`, …)"; "Source files are never modified." 8.4 "written to a temporary name and renamed to the final name only on success (D85)"; "Leftover temporary files from a crash are cleaned up on the next start"; "On cancel or failure, the temporary file is deleted (consistent with D44)"; "required disk space is estimated and the user warned if insufficient; running out of space during export fails cleanly without leaving a partial output (D87)". D34, D35, D36, D44, D84 (cross-format photo clashes), D85, D87; D83 as amended 0.5.3 ("the grouping clause and the per-recording-group collision suffix are deferred with chapter handling"). N8. Feeds V10 ("collision numbering ... cross-format photo clashes, and no source or existing output ever overwritten") and V11 ("cancel and simulated failures (crash, disk full) leave no partial outputs; leftover temporaries removed on next start"). DR-16 ("WP3.x that owns 8.4 proves the race-free form"). |
| Depends on | WP2.2 merged (IF-10 `Settings`). WP2.3 merged (the frame's dispatch order); no WP2.3 sample is needed: every test uses synthetic paths under pytest's `tmp_path`. |
| Files owned | `src/clearwater/jobs/__init__.py` (NEW; WP3.14 later adds its modules beside these and may extend this file); `src/clearwater/jobs/naming.py`; `src/clearwater/jobs/safe_write.py`; `src/clearwater/jobs/disk_space.py`; `tests/test_jobs_naming.py`, `tests/test_jobs_safe_write.py`, `tests/test_jobs_disk_space.py`; `docs/reports/wp3.13-naming-safe-writing.md`; `docs/proofs/wp3.13-ledger.md`. NOT owned: `src/clearwater/interfaces/`, `pyproject.toml` (no dependency), `tests/conftest.py`, every other module. |
| Interfaces provided | No frozen interface: naming and safe writing are not among IF-1..IF-10. The public names this package defines become WP3.14's inputs, so the round 0 yield tables them for CHARC (task 1). |
| Interfaces consumed | IF-10 `Settings.output_folder` (`Path | None`; None = the source folder, D34) and `Settings.output_suffix` (default `DEFAULT_OUTPUT_SUFFIX = "_corrected"`, D36). Python stdlib only (`os`, `pathlib`, `shutil.disk_usage`). |
| Wave-2 consumers | None in wave 2 has a build dependency on WP3.13. WP3.6 (photo, wave 2) writes to whatever `out_path` its `PhotoSink.write` is given, which in Phase 4 is this package's temporary path. Wave 3: WP3.10 (its `VideoSink.open` receives the temporary path; `VideoSink.abort` "removes the partial"). Wave 4: WP3.14 (plan "Depends on WP3.13"). Phase 4: WP4.1, WP4.3 (start-up leftover clean-up, plan WP4.3). Stubs: `stubs.py` has none for naming (no frozen interface); until this merges, consumers pass paths directly and `stubs.StubVideoSink` / `stubs.StubPhotoSink` record the `out_path` they were given. |
| Hardware flags | None. No footage, no GPU, no timing. |
| Out of scope | The per-recording-group shared collision suffix (D83 amended 0.5.3; chapter handling deferred to v2) even though plan WP3.13 and V10 still name it (open question 1); sidecar exclusion (WP3.7, AD-19); encoding or writing any file content (the sinks write; this package names, reserves, renames, removes); export, batch, progress and the end-of-run report (WP3.14); GUI warnings (WP3.19/3.20); deciding which folders to clean at start-up (open question 3); any write to the footage folder or the source folder outside the computed output path; OS-specific code (frame rule 11). |
| Done | Plan 4.5; frame section 2 rules 1-11 apply; ruff check, ruff format --check, mypy strict, full pytest green; every 8.3/8.4 sentence above has a named test; Reviewer A converged. |

## Task ladder

1. **Round 0 yield: the design table.** Before product code, write in the ledger: the public
   function names and signatures; the temporary-name pattern (open question 2); the rename
   mechanism and its no-replace guarantee on each filesystem in the envelope (open question
   4); the leftover-clean-up rule; the disk-space formula (open question 5). YIELD for the
   dispatcher.
2. **Final name (8.3).**
   - Folder: `settings.output_folder`, or the source's folder when None (D34).
   - Name: source stem + `settings.output_suffix` + extension. Video keeps the source
     extension exactly (`GX010123.MP4` → `GX010123_corrected.MP4`). Photos get `.png`
     (`IMG_1234.HEIC` → `IMG_1234_corrected.png`).
   - The result is never the source path (an empty suffix in the source folder is the case to
     prove).
3. **Collision numbering (D35, D84).**
   - When the final name exists, append `_2`, `_3`, ... after the suffix (`_corrected_2`); the
     first numbered name is `_2`.
   - "Exists" is decided by the filesystem, not by string comparison, so a case-insensitive
     volume treats `img_1234_corrected.PNG` as a clash with `IMG_1234_corrected.png`.
   - Cross-format clash: `IMG_1234.HEIC` and `IMG_1234.JPG` → `IMG_1234_corrected.png` and
     `IMG_1234_corrected_2.png`.
   - Names reserved earlier in the same run but not yet on disk count as taken (a batch plans
     several outputs before any is written).
   - Temporary files of other jobs count as taken.
4. **Safe write (D85, D44, 8.4).** A context-manager or begin / commit / abort API:
   - `begin` creates the temporary path in the destination folder (same volume, so the rename
     is a rename, not a copy) and hands it to the writer;
   - `commit` renames it to the final name, which is re-checked at that moment; a final name
     taken since planning moves to the next collision number, and an existing file is never
     replaced;
   - `abort` (cancel, failure, an exception inside the context) deletes the temporary file;
     it is idempotent, because `VideoSink.abort` may already have removed it;
   - nothing is ever written to, renamed or deleted at the source path.
5. **Leftovers (8.4).** A function that, given folders, removes files matching the temporary
   pattern only; it never touches a non-matching file, a folder, or a symlink target outside
   the folder.
6. **Disk space (D87).** An estimate of bytes needed for a planned output, and a check against
   `shutil.disk_usage` of the destination that reports "insufficient" with both figures. An
   out-of-space `OSError` while writing goes through `abort`, leaving no partial (V11 "disk
   full").
7. **Tests** (all under `tmp_path`; run the suite with a basetemp under `work/`):
   - every 8.3 example literally;
   - suffix edited and empty; output folder set and None;
   - collisions 1..n; case-insensitive clash (skip with a reason where the volume is
     case-sensitive);
   - the cross-format clash; in-run reservations;
   - commit when the final name appeared after planning;
   - abort on an exception, on cancel and on a simulated `ENOSPC`;
   - crash simulation (a temporary left behind, then the leftover clean-up removes it and
     nothing else);
   - the source file byte-identical and its mtime unchanged after every scenario;
   - a planted wrong implementation fails by name: an overwriting rename, numbering from `_1`,
     a string-compare collision check, a clean-up that deletes a non-temporary file;
   - dependency rule (plan 8.1, frame rule 5): importing `clearwater.jobs` loads nothing from
     `clearwater.gui` or `clearwater.methods` and no `PySide6` or `cupy`; `jobs` reaches
     methods only through IF-3, and these modules need no method at all.

## Declared operating envelope

Windows 11, NTFS and exFAT local volumes (an output folder may be the source's own, which may
be an SD card or an external drive); one Clearwater process at a time; single owner (DR-16:
a concurrent hostile process racing the rename is outside the threat model). Out of envelope:
network shares, other operating systems (the code is portable, N1, but not run there), a
second Clearwater instance writing the same folder.

## Review loop (Reviewer A), per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG**. Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.13\rN\`; ledger
  `docs/proofs/wp3.13-ledger.md`. Copy the runner and prompt shape from
  `C:\Users\rwsmy\clearwater-review-evidence\wp2.2\r3\run_review.sh` and `review-prompt.md`;
  exclude `docs/proofs` with `--glob '!docs/proofs/**'`. Five-round gate.
- **WHAT TO EXAMINE:**
  - every path to an overwrite: the rename, a collision decided by string, a reservation lost
    between planning and commit, case folding;
  - the source never touched;
  - abort and clean-up delete only temporaries;
  - the temporary pattern cannot match a camera or user file name;
  - the `ENOSPC` path leaves nothing;
  - portability of the rename (N1);
  - the 8.3 examples exactly.
- Reviewer B is the orchestrator's seat pass on the merge candidate.

## Notes for the cell

- **Return report** = your FINAL message, under about 70 lines (`docs/dispatch-recipe.md`
  section 4): the public API, the scenario table (scenario, test, result), the rename
  mechanism and its limits, the gates, the Reviewer A rounds and verdict, open items.
- **STOP for:** a no-replace rename that needs OS-specific code; any scenario where an
  existing file could be replaced; a test that needs a real footage or source folder; a
  dependency.
- **Working rules:** `uv sync`. Commit by pathspec, `feat(wp3.13): ...`, with a
  `Co-Authored-By:` footer naming your model. Never a bare `cd`. Never post to a mailbox. The
  full pytest (8-15 min, 892+ tests) runs in the background with output to a file under
  `work/`. Gates: ruff check, ruff format --check, mypy strict, full pytest; no harness gate.
  Report `docs/reports/wp3.13-naming-safe-writing.md` (claims, evidence paths, limits). Yield
  at every round boundary; the dispatcher reads your depth (~250K evaluation, ~400K stop).

## Rulings (CHARC `871a371855bb1630`, 2026-10-20)

The questions below were raised as drafted. **Every recommended answer is the ruling**
unless a line here amends it. Cross-brief rulings: X1 (owned files outside the module path,
below), X2 (WP3.15 ships `clearwater.config.paths` at its round-0 yield), X3 (manifest ids filled
at dispatch from the merged WP2.3 manifest), X5 (parallel cells allowed; the dispatcher
serialises full-pytest runs at gate windows; inner loops run only the cell's own tests).
- **X1:** WP3.13 creates `src/clearwater/jobs/__init__.py` (docstring and exports only);
  WP3.14 adds sibling modules and may append exports, nothing else.
- **13.1:** v0.5.4 proposal item 14 is extended on main (`7926fd3`) with V10's group-suffix
  phrase and the plan row.
- **13.4 RULED:** the link-then-unlink / re-check-then-rename no-replace sequence is a portable
  algorithm with a documented platform difference, NOT OS-specific code under N1 (AD-25). The
  residual POSIX race stays documented under DR-16.
- **13.6:** the architecture comment is corrected on main (`7926fd3`: abort = D44/D85); the
  interfaces docstring follows at the next interface touch, not in this package.

### Questions as drafted (recommended answer = ruling unless amended above)


1. **The recording-group shared suffix.** Plan WP3.13 ("shares one collision suffix across a
   recording group") and V10 ("shared suffix per recording group") still name it; D83 amended
   0.5.3 defers it with chapter handling, and the v0.5.4 proposal item 14 deletes other
   chapter remnants but not V10's. Recommended: out of scope here; V10's phrase is added to
   item 14 and the plan row corrected.
2. **Temporary-name pattern.** Not defined by the spec. Recommended: the final name with a
   marker before the extension, for example `GX010123_corrected.clearwater-partial.MP4`, so
   FFmpeg and the PNG writer still see the right extension and no camera or iPhone name can
   match it.
3. **Which folders the start-up clean-up scans.** 8.4 says "on the next start", but outputs go
   to source folders the next start does not know. Recommended: WP3.13 provides
   `remove_leftovers(folders)`; the start-up wiring (WP4.3) passes the configured output folder
   plus the folders of a small journal of in-flight writes, and the journal (a file in app
   data, WP3.15's paths) is added by WP3.14 or WP4.3, not here.
4. **The no-replace rename (DR-16).** `os.rename` refuses to replace on Windows but replaces on
   POSIX; `os.link` then `os.unlink` refuses on both but fails on exFAT and FAT. Recommended:
   `os.link` + unlink where links work, else re-check then `os.rename` with Windows's refusal as
   the guarantee, the residual POSIX-without-links race documented under DR-16's threat model.
   CHARC to confirm that this is not "OS-specific code" under N1.
5. **The disk-space formula.** D87 gives none. Recommended: video = source size x the AD-12
   level's target ratio (High 1.0, Standard 0.5, Draft 0.25) x 1.25 margin, doubled for 10-bit
   from 8-bit (D76); photo = width x height x 3 x bit depth / 8, uncompressed, plus 1 MiB for
   the profile and EXIF. AD-12 is PROVISIONAL until WP3.10, so the ratios are constants in one
   place.
6. **D84's citation in IF-5.** `VideoSink.abort` says "removes the partial output (D84)"; spec
   D84 is the cross-format photo clash, and partial removal is D44/D85. Recommended: a CHARC
   docstring erratum at the next interface touch; no code change here.
