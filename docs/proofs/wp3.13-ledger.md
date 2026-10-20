# WP3.13 ledger (output naming and safe writing)

Cell: implementer-sonnet-high. Worktree `.worktrees/wp3.13`, branch `wp3.13`, base `9735282`.
Spec v0.5.4, architecture FINAL 1.0, brief FINAL (rulings 13.1, 13.4, 13.6 and the recommended
answers to open questions 1-6 bind).

## Cumulative round ledger

| Round | Critical | Major | Minor | In envelope / out | NEW / REOPENED | Reverts | Fix changed | Transport, CLI | Depth |
|---|---|---|---|---|---|---|---|---|---|
| 0 (design table) | - | - | - | - | - | - | none (no code) | - | 62,046 (dispatcher-read at the round-0 yield) |
| 1 | 1 | 4 | 1 | 6 in / 0 out | 6 NEW / 0 REOPENED | 0 | PRODUCT code (d92ea8d) | WSL, codex-cli, gpt-5.6-sol high | 118,143 (dispatcher-read at the window grant) |
| 2 | 0 | 3 (1 banked, out of envelope) | 1 | 2 in + 1 out / 0 | 3 NEW / 0 REOPENED | 0 | PRODUCT code (this commit) | WSL, codex-cli, gpt-5.6-sol high | 182,256 (dispatcher-read at the round-2 yield) |

## Round 0: design table (no product code yet)

All modules are stdlib only, no OS-specific branches (frame rule 11, AD-25b). Package
`clearwater.jobs` (`__init__.py`: docstring and re-exports only, ruling X1).

### 1. Public API

`jobs/naming.py`

| Name | Signature / shape | Purpose |
|---|---|---|
| `MediaKind` | `enum.Enum`: `VIDEO`, `PHOTO` | Decides the extension rule (video keeps the source extension; photo gets `.png`). The caller classifies the source. |
| `OutputPlan` | frozen dataclass: `folder: Path`, `base: str` (source stem + suffix), `extension: str`, `number: int` (1 = unnumbered); property `path`, method `numbered(n) -> OutputPlan` | One planned final name. `path` is `folder/base+ext` for number 1, `folder/base_N+ext` for N >= 2. |
| `Reservations` | class, thread-safe: `try_reserve(path) -> bool`, `release(path)`, `__contains__`, `__len__` | In-run registry of names planned but not yet on disk (a batch plans many outputs first). Key = `os.path.normcase(os.path.abspath(p)).casefold()`, a deliberately conservative over-approximation (see 3). |
| `final_output_path(source, settings, kind) -> Path` | pure, no filesystem | The unnumbered 8.3 name (`GX010123.MP4` -> `GX010123_corrected.MP4`; `IMG_1234.HEIC` -> `IMG_1234_corrected.png`). |
| `plan_output(source, settings, kind, reservations=None) -> OutputPlan` | reads the filesystem, reserves the result when `reservations` is given | First number n >= 1 whose final name is free on disk (filesystem decides: `os.path.lexists`), whose temporary name is free on disk, and which no other reservation holds. |
| `TEMP_MARKER = ".clearwater-partial"`, `temporary_path(final) -> Path`, `is_temporary_name(name) -> bool` | | The temporary-name pattern (section 2). |
| `validate_suffix(suffix) -> None` | raises `ValueError` | Rejects a suffix that is not a single portable name fragment (separators, `:*?"<>|`, control chars, NUL, `..`, or containing the marker, case-insensitive). Called by `final_output_path`. |

`jobs/safe_write.py`

| Name | Signature / shape | Purpose |
|---|---|---|
| `SafeWrite` | `SafeWrite(plan, reservations=None, *, source=None)`; context manager; `begin() -> Path`, `commit() -> Path`, `abort() -> bool`; properties `temp_path`, `final_path`, `state` | begin / commit / abort. `__enter__` calls `begin()` and returns the object (the writer reads `.temp_path`); `__exit__` calls `abort()` on an exception AND when the block ends without `commit()` (safe default); never suppresses the exception. |
| `SafeWriteError` | `OSError` subclass | commit on a missing temporary, commit after abort, source-path guard. |
| `is_disk_full(exc) -> bool` | | True for `ENOSPC`, `EDQUOT`, Windows `winerror` 112 and 39. WP3.14 uses it to report "disk full" distinctly. |
| `remove_leftovers(folders) -> LeftoverReport` | `LeftoverReport(removed: tuple[Path, ...], failed: tuple[tuple[Path, str], ...])` | Clean-up (section 5). |

`jobs/disk_space.py`

| Name | Signature / shape | Purpose |
|---|---|---|
| `estimate_video_bytes(source_size, settings, source_bit_depth) -> int` | | Section 6. |
| `estimate_photo_bytes(width, height, bit_depth) -> int` | | Section 6. |
| `check_free_space(folder, needed) -> SpaceCheck` | `SpaceCheck(needed: int, free: int, ok: bool)`, `message()` returns an ASCII string carrying both figures | `shutil.disk_usage` of the nearest existing ancestor of `folder`. A batch sums its estimates per volume and checks once (WP3.14). |
| `QUALITY_RATIO`, `MARGIN`, `PHOTO_OVERHEAD_BYTES` | module constants | The formula constants in one place (AD-12 is PROVISIONAL until WP3.10). |

### 2. Temporary-name pattern (open question 2, ruled as recommended)

`<final base>.clearwater-partial<final extension>`: `GX010123_corrected.clearwater-partial.MP4`,
`IMG_1234_corrected_2.clearwater-partial.png`. The extension stays last, so FFmpeg picks the
container and the PNG writer sees `.png`. The temporary is derived from the NUMBERED final name,
so two live jobs never share one (the reservation makes final names unique).

`is_temporary_name(name)` is true only when the name is `<non-empty>.clearwater-partial` followed
by nothing or by exactly one `.ext` with no further dot and no separator, compared case-insensitively
(a case-insensitive volume may report the name in any case). No camera name (GoPro `GX*`/`GH*`/`GOPR*`,
iPhone `IMG_*`, `*.LRV`, `*.THM`) can match it: they contain no `.clearwater-partial`. A user name
that does is out of any plausible input; `plan_output` additionally raises `ValueError` if the
computed FINAL name would itself match (only reachable from a source literally named with the
marker plus an empty suffix), so a final output can never be deleted by the clean-up.

`begin()` creates the temporary exclusively and empty (`O_CREAT|O_EXCL`). Consequences:
(a) the temporary is visible on disk, so "temporary files of other jobs count as taken" is decided
by the filesystem, including case folding; (b) a stale temporary left by a crash makes `begin`
fail with `FileExistsError` rather than silently reuse it; (c) the writer must open the path for
writing with truncation (FFmpeg needs `-y`; the PNG writer opens `"wb"`). QUESTION FOR CHARC (c):
confirm that WP3.10 can pass `-y`; the alternative is a `begin` that only reserves the name and
does not create the file (weaker: then temporary visibility rests on the writer).

`begin()` creates a missing output folder (`mkdir(parents=True, exist_ok=True)`). QUESTION FOR
CHARC: confirm, or rule that the missing folder is an error WP3.14 must handle first.

### 3. Collision rule and reservations

Number n = 1 is the unnumbered name; n >= 2 is `<base>_<n><ext>` (`_corrected_2`, so the first
numbered name is `_2`). Candidate n is TAKEN when any of: `os.path.lexists(final_n)` (the
filesystem decides, so a case-insensitive volume treats `img_corrected.PNG` as a clash with
`IMG_corrected.png`; `lexists` also catches a dangling symlink); `os.path.lexists(temp_n)`; or
the `Reservations` registry holds it. The registry compares casefolded absolute paths on EVERY
platform: on a case-sensitive volume this may skip one number for two names differing only in
case, which wastes a number but cannot overwrite (conservative). The on-disk check is never a
string comparison. An empty suffix in the source folder: `GX010123.MP4` exists (it is the source)
so the plan is `GX010123_2.MP4`; `SafeWrite` also refuses (`SafeWriteError`) a final path that is
`os.path.samefile` / equal to the optional `source=` argument.

### 4. Rename mechanism and its no-replace guarantee (open question 4, ruling 13.4)

`commit()` loop over candidate numbers starting at the plan's number, re-deciding "taken" at THIS
moment (filesystem plus registry; a bump reserves the new name and releases the old atomically):

1. `os.link(temp, final)` (a hard link, then `os.unlink(temp)`). The OS refuses to create a link
   over an existing name (`FileExistsError`), on every platform; this IS the no-replace guarantee
   with no check-then-act window. `FileExistsError` -> bump to the next number, retry.
2. Any other `OSError` from `os.link` (links unsupported: exFAT, FAT, some SD cards and external
   drives; or `AttributeError`/`NotImplementedError` where `os.link` is absent) -> fallback:
   `os.path.lexists(final)`? then bump; else `os.rename(temp, final)`; `FileExistsError` -> bump.

| Filesystem in the envelope | Path taken | No-replace guarantee |
|---|---|---|
| Windows NTFS (local) | link | OS refuses over an existing name (no window). If the temporary unlink fails afterwards (a scanner holds it open), the final is already correct and the stale temporary is removed by the next-start clean-up. |
| Windows exFAT (SD card, external drive) | fallback | re-check, then `os.rename`; Windows refuses to rename over an existing file (documented stdlib behaviour: `FileExistsError` is always raised), so the guarantee is the OS's. No window. |
| Same code on POSIX (not run, N1) | link where supported; fallback on vfat | link: no window. fallback only: `os.rename` replaces silently, so a file created between the re-check and the rename (a second writer) would be replaced. Single-owner, one-process threat model: stays under DR-16; documented in the report. |

`os.replace` and `shutil.move` are never used. `commit()` never deletes anything at a final name.
After commit, `abort()` is a no-op (it never deletes the final). If `commit()` raises, the context
manager aborts (temporary removed).

### 5. Leftover clean-up rule

`remove_leftovers(folders)`: for each folder (not recursive), `os.scandir`; remove an entry only
when `entry.is_file(follow_symlinks=False)` AND `is_temporary_name(entry.name)`. Directories,
symlinks (even named like a temporary; the link is skipped, so no target outside is reached) and
every non-matching file are left untouched. A missing folder is skipped silently; an `OSError` on
one entry is recorded in `failed` and the scan goes on. The call never raises for a per-file
problem. Which folders to scan, and the in-flight journal, are WP4.3 / WP3.14 (open question 3);
the caller must not pass a folder while a job is writing there (second instance is out of envelope).

### 6. Disk-space formula (open question 5, ruled as recommended)

- Video: `ceil(source_size * QUALITY_RATIO[settings.quality_level] * MARGIN)`, `QUALITY_RATIO =
  {"high": 1.0, "standard": 0.5, "draft": 0.25}`, `MARGIN = 1.25`; times 2 when
  `settings.ten_bit_for_eight_bit` and `source_bit_depth == 8` (D76). An unknown level raises
  `ValueError`.
- Photo: `width * height * 3 * bit_depth // 8 + PHOTO_OVERHEAD_BYTES` (1 MiB), the uncompressed
  upper bound.
- `check_free_space`: `ok = free >= needed`; nearest existing ancestor of the destination folder is
  measured; `message()` reads e.g. `Not enough free space in D:\out: need 1,234,567 bytes, 987,654 free.`
- Out-of-space during a write: the writer raises `OSError(ENOSPC)`; the `SafeWrite` block aborts and
  removes the temporary (nothing is left); `is_disk_full` lets WP3.14 classify it.

### 7. Test plan (names fixed now, files `tests/test_jobs_*.py`, all under `tmp_path`)

Every 8.3 example literally; suffix edited / empty; folder set / None; collisions 1..n; case-insensitive
clash (skips with a reason on a case-sensitive volume, volume detected by probe); cross-format clash;
in-run reservations; commit with the final name appeared after planning; abort on exception, on cancel
and on `ENOSPC` (monkeypatched writer); abort idempotent and a no-op after commit; crash simulation
(temporary left, then `remove_leftovers` removes it and nothing else); link-unsupported fallback
(monkeypatched `os.link` raising `OSError`); source byte-identical and mtime unchanged after each
scenario; planted wrong implementations that must fail by name (overwriting rename, numbering from `_1`,
string-compare collision check, clean-up deleting a non-temporary file); import test: `clearwater.jobs`
loads no `clearwater.gui`, `clearwater.methods`, `PySide6` or `cupy` (subprocess, `python -I`).

### 8. Questions for the round-0 ruling

1. (c) `begin()` creates the temporary empty and exclusively; WP3.10 must pass `-y` to FFmpeg. OK?
2. `begin()` creates a missing output folder. OK?
3. `plan_output` returns an `OutputPlan` (not a bare `Path`) so that `commit` can bump numbers; WP3.14
   reads `plan.path`. OK?
4. The `source=` guard on `SafeWrite` is optional; WP3.14 should pass it. OK?

## Round-0 ruling (orchestrator gen 5, relaying CHARC's brief rulings) as applied

1. `begin()` creates the temporary empty and exclusively; WP3.10 passes `-y`. A stale temporary at
   the planned number gives a bump at planning (test `test_stale_temporary_at_planned_number_gives_a_bump_not_a_failure`).
2. AMENDED: `begin()` does not create a missing folder; it raises `MissingFolderError` (a
   `SafeWriteError`) naming the folder and creates nothing (test `test_missing_output_folder_raises_and_creates_nothing`).
3. `plan_output` returns the frozen `OutputPlan`.
4. AMENDED: `OutputPlan.source` carries the source; the `source=` keyword is dropped; `SafeWrite`
   always refuses a final path that is the source (`is_same_path`: `os.path.samefile` when both exist,
   else absolute normcased case-folded comparison), at `begin` (raises) and at every bumped
   candidate in `commit` (skipped). Planted-defect test `test_planted_missing_source_guard_fails_by_name`.

Deviation from the round-0 table: `SpaceCheck` also carries `folder` (used by `message()`).

## Build status (before the first full-pytest window)

Own tests `tests/test_jobs_*.py`: 114 passed, 0 skipped (NTFS: the case-insensitive and symlink tests ran).
ruff check, ruff format --check, mypy strict clean on the worktree.

## Full-pytest window (granted by the dispatcher)

Head c701a04: `1252 passed, 1 warning in 531.75s (0:08:51)`, exit 0; the warning is CuPy's "CUDA path could
not be detected" (environment, not this package). Output `work/tmp/full.txt` in the worktree. The
`SpaceCheck.folder` deviation was accepted by the dispatcher.

## Round 1 (Reviewer A, strong: gpt-5.6-sol, effort high; head c701a04)

Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.13\r1\` (prompt, diff, `full-transcript.txt`,
`review.txt`, `adjudication.md`, `md5s.txt`). Assertions all met (see adjudication.md). VERDICT:
NEW_CRITICAL_MAJOR_FOUND. Six findings, all EXECUTED, all confirmed, all in envelope, all NEW:

1. CRITICAL: `remove_leftovers` deletes a user file named like a temporary (pattern-only identity).
2. MAJOR: `final_output_path` returns the source for an empty suffix in the source folder.
3. MAJOR: `SafeWrite.__enter__` leaks reservations when `begin()` raises (missing folder).
4. MAJOR: commit-time bump ignores the bumped name's temporary on disk.
5. MAJOR: `abort()` can unlink another job's re-created temporary (identity not tracked).
6. MINOR: `SpaceCheck.message()` is not ASCII for a Unicode folder.

Proposed remediation (NOT yet applied; per the dispatcher the round ends here): findings 2-6 as in
`adjudication.md`. Finding 1 changes the round-0 temporary-name pattern, so it needs a ruling: the proposal
is `<base>.clearwater-partial-<12 hex>[.ext]` with a fresh `secrets.token_hex(6)` per `SafeWrite`; the
cleanup regex requires the token; planning and commit decide "another job's temporary exists" by scanning the
destination folder for that final name's token form (the filesystem decides, case-insensitively);
`validate_suffix` and the final-name guard keep working. Residual accepted limitation: a user file
deliberately named with marker plus 12 hex digits would be removed. Alternative if the dispatcher prefers no
token: accept the literal-marker case as an out-of-practice input and bank it (not recommended: the brief's
examine list names this invariant).

## Round-1 ruling (dispatcher, depth 143,034 at the round-1 yield) as applied

SUPERSEDES the round-0 temporary-name pattern: the temporary is now
`<base>.clearwater-partial-<12 hex>[.ext]` with a fresh `secrets.token_hex(6)` per `SafeWrite`
(`naming.new_token`, `naming.temporary_path(final, token)`); the clean-up regex requires the token, hex
matched case-insensitively; planning and commit decide "a temporary of this final name exists" with one
rule, `naming.scan_temporaries` / `temporaries_of` (any token, folder listing, case-insensitive). Residual
limit (for the report): a user file deliberately named marker plus 12 hex digits would be removed.

| Finding | Fix | Test that fails on the unfixed code (mutation-checked) |
|---|---|---|
| 1 CRITICAL | token pattern; user file `holiday.clearwater-partial.png` is not a temporary | `test_other_names_do_not_match[holiday.clearwater-partial*]`, `test_user_file_in_the_old_marker_form_survives_the_cleanup` (marker regex mutated to optional token: fails) |
| 2 MAJOR | `final_output_path` lexical source guard, first numbered name `_2` | `test_final_output_path_is_never_the_source_for_an_empty_suffix` (guard removed: fails) |
| 3 MAJOR | `__enter__` aborts (releases the reservations) when `begin()` raises | `test_failed_begin_inside_with_releases_the_reservation`, `test_source_guard_failure_inside_with_releases_the_reservation` (abort removed: fails) |
| 4 MAJOR | commit skips a candidate with a temporary of another write (`_foreign_temporary`, same scan as planning) | `test_commit_bump_skips_a_bumped_name_that_has_a_temporary`, `test_commit_skips_the_planned_name_when_another_write_holds_a_temporary_for_it` (check removed: fails) |
| 5 MAJOR | AMENDED by the dispatcher: closed by construction (the per-write token); NO st_dev/st_ino identity check (the file index is not dependable on exFAT under Windows) | `test_abort_keeps_a_temporary_another_job_created_under_its_own_token`, `test_two_writes_of_one_final_name_never_share_a_temporary` |
| 6 MINOR | folder text escaped to ASCII (`backslashreplace`) | `test_message_is_ascii_for_a_unicode_folder` (escape removed: fails) |

Inner loop after remediation: 132 own tests passed, ruff check, ruff format --check, mypy clean. Full pytest
not yet re-run (window requested at the round-1 remediation yield).

Depth figures (dispatcher-read): round-1 yield 143,034; remediation yield 169,145. Window for round 2 queued behind WP3.7 and WP3.1.

## Round 2 (Reviewer A, strong; head 114b322; window: 1270 passed in 518.06s, exit 0)

Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.13\r2\` (prompt with a THIS IS ROUND 2 section, diff,
`full-transcript.txt`, `review.txt`, `adjudication.md`, `md5s.txt`). Assertions met. VERDICT:
NEW_CRITICAL_MAJOR_FOUND: 0 critical, 3 major, 1 minor, all EXECUTED except the minor, all NEW; none of
round 1's six reopened. Adjudication in `adjudication.md`:

1. MAJOR, BANKED OUT-OF-ENVELOPE: `import clearwater.jobs` needs NumPy via `clearwater.interfaces` (WP2.2,
   `bf76136`; NumPy is a locked dependency). Cheap cleanup anyway: `Settings` under `TYPE_CHECKING`.
2. MAJOR, in envelope: `begin()` sets `_created` after `os.close`, so a failing close strands the temporary.
3. MAJOR, in envelope: `final_output_path` lexical guard misses an alias (junction) of the source folder; use
   `is_same_path`.
4. MINOR: `final_output_path` docstring contradiction.

Remediation not yet applied (the round ends here).

## Round-2 ruling (dispatcher; depth 182,256 at the round-2 yield) as applied

- Finding 1 BANKED, pre-existing and out of envelope; NO cleanup (the dispatcher amended: no `TYPE_CHECKING`
  move, no "NumPy not loaded" assertion, because WP3.14 modules reach methods through IF-3, which imports
  NumPy). Provenance: `git log -S"import numpy" --oneline -- src/clearwater/interfaces/image.py` gives
  `bf76136 feat(wp2.2): interface module IF-1 to IF-10, stubs, tests and round-1 ledger`; NumPy is in the
  locked `dev` group (`numpy>=2.1,<3`). Reachability: only an interpreter without NumPy. The dispatcher banks
  it in the debt register at accept.
- Finding 2 FIXED: `begin()` sets `_created` before `os.close`. Test
  `test_failing_close_of_the_new_temporary_is_cleaned_up` (fails with the old order, checked).
- Finding 3 FIXED: `final_output_path` uses `is_same_path` (samefile when both exist). Test
  `test_final_output_path_is_never_the_source_through_a_folder_alias` (fails with the lexical guard, checked).
  It RAN here: a directory symlink can be made on this machine (developer mode); I also confirmed by hand
  that an NTFS junction (`mklink /J`) gives `GX_2.MP4`. The test skips with a reason where neither a symlink
  nor a junction can be made.
- Finding 4 FIXED: the `final_output_path` docstring now states the one exception to "no number".

Inner loop: 134 own tests passed, 0 skipped; ruff check, ruff format --check, mypy clean. Full pytest window
to be requested; round 3 follows.
