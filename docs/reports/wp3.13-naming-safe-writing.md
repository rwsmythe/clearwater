# WP3.13 -- Output naming and safe writing (report)

Cell: implementer-sonnet-high. Worktree `.worktrees/wp3.13`, branch `wp3.13`, base `9735282`. Spec v0.5.4
(8.3, 8.4; D34, D35, D36, D44, D84, D85, D87), architecture FINAL 1.0, AD-25b, DR-16. Ledger:
`docs/proofs/wp3.13-ledger.md`. Reviewer A evidence: `C:\Users\rwsmy\clearwater-review-evidence\wp3.13\r1`, `r2`, `r3`.

## What was built (`src/clearwater/jobs/`, stdlib only, no OS-specific branches)

- `naming.py`: `MediaKind`, `OutputPlan` (source, folder, base, extension, number; `.path`), `Reservations`,
  `final_output_path`, `plan_output`, `is_taken`, `validate_suffix`, `is_temporary_name`, `temporary_path`,
  `new_token`, `scan_temporaries`, `temporaries_of`, `is_same_path`.
- `safe_write.py`: `SafeWrite` (begin / commit / abort, context manager), `SafeWriteState`, `SafeWriteError`,
  `MissingFolderError`, `is_disk_full`, `remove_leftovers` -> `LeftoverReport`.
- `disk_space.py`: `estimate_video_bytes`, `estimate_photo_bytes`, `check_free_space` -> `SpaceCheck`,
  constants `QUALITY_RATIO`, `MARGIN`, `PHOTO_OVERHEAD_BYTES` (AD-12 ratios PROVISIONAL until WP3.10).
- `__init__.py`: docstring and re-exports only (ruling X1).
- Tests: `tests/test_jobs_naming.py`, `tests/test_jobs_safe_write.py`, `tests/test_jobs_disk_space.py`.

## Contract in one paragraph

`plan_output(source, settings, kind, reservations)` returns an `OutputPlan` whose `.path` is the first free
name: `<stem><suffix><ext>`, then `_2`, `_3`, ... after the suffix. Video keeps the source extension; photos get
`.png`. Free means: not on disk (`os.path.lexists`, so the filesystem decides, including case folding), no
temporary of that final name on disk (any token), not held in the run's `Reservations`, not the source (by
`samefile` when both exist), and not itself shaped like a temporary. `SafeWrite(plan, reservations)` creates
`<base>.clearwater-partial-<12 hex>[.ext]` (random token per write) in the destination folder, empty and
exclusively; `commit()` re-checks the final name at that moment and renames without ever replacing; `abort()`
(and leaving the `with` block without a commit, or by an exception) deletes the temporary and never raises.

## Rename mechanism and its limits (open question 4, ruling 13.4, AD-25b)

`os.link(temp, final)` then unlink of the temporary. Every platform's `link` refuses to create an existing
name, so there is no check-then-act window. Where links fail (exFAT, FAT, some SD cards), the fallback
re-checks the final name and calls `os.rename`.

| Volume | Path | No-replace guarantee |
|---|---|---|
| Windows NTFS | link | the OS refuses an existing name; if unlinking the temporary then fails the final is already correct and the stale temporary is removed at the next start |
| Windows exFAT / FAT | rename fallback | Windows refuses to rename over an existing file (documented `FileExistsError`); no window |
| POSIX with links | link | no window |
| POSIX vfat (links unsupported) | rename fallback | `os.rename` replaces silently, so a file created between re-check and rename could be replaced; single-owner, one process, outside the threat model (DR-16) |

`os.replace` and `shutil.move` are never used. The exFAT row rests on the documented Windows behaviour and on a
test that forces the fallback (`os.link` monkeypatched to fail, `os.rename` monkeypatched to refuse); it was NOT
run against a real exFAT card on this machine. The POSIX rows were not run (N1: portable, not run).

## Scenario table

| Scenario | Test (file) | Result |
|---|---|---|
| 8.3 examples literally (video, photo, extension case, folder, suffix, empty suffix) | `test_example_*`, `test_empty_suffix_*` (naming) | pass |
| Numbering `_2`, `_3`, many; planted "from `_1`" fails | `test_collisions_*`, `test_planted_numbering_from_one_fails_by_name` | pass |
| Case-insensitive clash; planted string-compare fails | `test_case_insensitive_clash`, `test_planted_string_compare_collision_fails_by_name` | pass (NTFS; skip on a case-sensitive volume) |
| Cross-format HEIC/JPG clash | `test_cross_format_*` | pass |
| In-run reservations, case-folded, release by exact holder | `test_in_run_reservations_*`, `test_reservations_*`, `test_release_*` | pass |
| Other jobs' temporaries count as taken (planning and commit) | `test_other_jobs_temporary_*`, `test_planning_skips_*`, `test_commit_bump_skips_*`, `test_commit_skips_the_planned_name_*` | pass |
| Temporary pattern vs camera and user names; token form only | `test_temporary_names_match`, `test_other_names_do_not_match`, `test_user_file_in_the_old_marker_form_*` | pass |
| Stem + suffix that spell a temporary, `_N` names never match | `test_stem_and_suffix_that_spell_*`, `test_numbered_names_never_match_*`, `test_final_name_that_looks_temporary_*` | pass |
| Source guard (empty suffix, case variant, folder alias/junction); planted guard removal fails | `test_empty_suffix_*`, `test_begin_refuses_the_source_path*`, `test_final_output_path_is_never_the_source_*`, `test_planted_missing_source_guard_fails_by_name` | pass (alias test ran: directory symlink here, junction checked by hand) |
| Commit when the final name appeared after planning | `test_final_name_taken_since_planning_*`, `test_commit_skips_names_held_by_other_jobs` | pass |
| No-replace rename on link path, rename fallback, rename refusal; planted `os.replace` fails | `test_install_*`, `test_planted_overwriting_rename_fails_by_name`, `test_commit_fallback_end_to_end` | pass |
| Abort on exception, cancel, simulated `ENOSPC` (write and commit and close), idempotent, after commit, foreign temporary survives | `test_exception_*`, `test_cancel_*`, `test_simulated_enospc_*`, `test_enospc_during_commit_*`, `test_failing_close_*`, `test_abort_*` | pass |
| Missing output folder: named error, nothing created, reservation released | `test_missing_output_folder_*`, `test_failed_begin_inside_with_*` | pass |
| Crash simulation; clean-up removes only temporaries (not folders, symlinks, other files); planted delete-all fails | `test_crash_*`, `test_planted_cleanup_*`, `test_cleanup_*` | pass |
| Source byte-identical and mtime unchanged after every write scenario | the `source` fixture in `test_jobs_safe_write.py` | pass |
| Disk-space formula, 10-bit doubling only from 8-bit, both figures, ASCII message | `tests/test_jobs_disk_space.py` | pass |
| Dependency rule: no `clearwater.gui`, `clearwater.methods`, `PySide6`, `cupy` | `test_importing_jobs_loads_no_gui_methods_or_heavy_libraries` | pass |

## Gates (final head: see the ledger's last block for the head and the full-run line)

ruff check, ruff format --check and mypy strict clean; own tests 173 passed; full pytest on the final head is
recorded in the ledger (earlier heads: c701a04 1252, 114b322 1270, f4f14f8 1272 passed).

## Reviewer A (strong: gpt-5.6-sol, effort high, WSL codex-cli)

| Round | Head | Verdict | Findings |
|---|---|---|---|
| 1 | c701a04 | NEW_CRITICAL_MAJOR_FOUND | 1 critical, 4 major, 1 minor; all confirmed and fixed (tokened temporary names, `final_output_path` source guard, `__enter__` abort, commit-time temporary scan, ASCII message; the inode check was rejected by ruling) |
| 2 | 114b322 | NEW_CRITICAL_MAJOR_FOUND | 3 major, 1 minor; 1 banked (pre-existing NumPy import via `clearwater.interfaces`, bf76136, out of envelope), 2 fixed (created-flag before close, `is_same_path` in `final_output_path`), 1 doc fix |
| 3 | f4f14f8 | NEW_CRITICAL_MAJOR_FOUND (labelled MAJOR) | 1 finding classified MINOR and non-blocking by the dispatcher (deliberate-input only); fixed in the terminating cleanup (temporary-shaped final names move to `_2`), no further round |

Loop CONVERGED at round 3 by the dispatcher's ruling; every fix was product code with a mutation-checked test.

## Limits and open items

- Residual accepted (ruling): a user file deliberately named with the marker plus exactly 12 hex digits before
  the extension is treated as a temporary by `remove_leftovers`.
- `abort()` identifies its temporary by name (unique per write through the token), not by file identity (the
  Windows file index is not dependable on exFAT; ruling).
- POSIX rename fallback race (above); DR-16 stays as documented.
- Importing `clearwater.jobs` imports NumPy through `clearwater.interfaces` (WP2.2); banked by the dispatcher.
- `remove_leftovers` is not recursive and does not choose folders; which folders to scan and the in-flight
  journal belong to WP4.3 / WP3.14 (open question 3).
- The disk-space ratios are AD-12's PROVISIONAL targets until WP3.10; they live in `QUALITY_RATIO`.
- Per-recording-group suffix: out of scope (D83 amended 0.5.3; V10 / plan row corrected by ruling 13.1).
- `VideoSink.abort` docstring cites D84 for "remove the partial"; D44/D85 is right (ruling 13.6, next interface touch).

## Consumer notes (WP3.10, WP3.14, WP3.19/3.20, WP4.3)

- Read `SafeWrite.temp_path`; never build a temporary name by hand. The temporary exists, empty, from `begin()`.
- (b) WP3.10 passes FFmpeg the TEMPORARY path with `-y` (the file already exists, empty), never the final path.
  The PNG writer opens it `"wb"`. The writer must close the file before `commit()`.
- (a) WP3.14 and the GUI (G12) validate the output-folder setting when it is set and again at export start, so
  the missing-folder `MissingFolderError` (a `SafeWriteError`) is the last net, not the first. `begin()` never
  creates a folder.
- WP3.14: pass the same `Reservations` to `plan_output` and `SafeWrite`; plan every output of a batch first;
  read the final path from `commit()`'s return value (it may be renumbered). Catch `OSError`, classify disk-full
  with `is_disk_full`, and let the `with` block clean up. Sum the estimates per destination volume before one
  `check_free_space`.
- WP4.3: call `remove_leftovers` at start-up over the configured output folder plus the folders of in-flight
  writes (the journal is not built here), before any job runs.

## Erratum at the gate (orchestrator, 2026-10-20)

The rename table's "POSIX with links: no window" holds only while `os.link` succeeds. Any `OSError`
from `os.link` (not only "links unsupported") takes the re-check-then-`os.rename` fallback, whose
residual POSIX race stays under DR-16 (Reviewer B advisory 4; out of envelope).
