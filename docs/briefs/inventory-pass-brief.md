# Inventory pass — the real footage inventory (dispatch brief, FINAL)

**Status:** FINAL, issued by the orchestrator 2026-10-18. Released by CHARC `1c889fc60c25c8ba`,
which relays the owner's "download complete" word (2026-10-18). Spec **v0.5.2**.
- **Cell:** `implementer-sonnet-medium`. This is a mechanical run of a committed instrument, with
  NO code change.
- **Where:** worktree `.worktrees/inventory`, branch `inventory`, base = the main commit named
  in the dispatch.
- **Not exclusive:** the run records no timing. It may run beside the WP1.4 remediation.

| Field | Content |
|---|---|
| Goal | Run WP0.2's committed inventory tool over the owner's complete footage folder and turn its output into one committed report that CHARC carries to the owner for CP1 (footage categories, owner-reserved). |
| Instrument | `tools/inventory.py` as committed (WP0.2, accepted). Do NOT edit it; if it misbehaves, STOP and report. |
| Command | From the worktree, with the copied local configuration: `uv run python tools/inventory.py`. It writes `C:\Users\rwsmy\clearwater\work\reports\inventory-<stamp>.csv` and `...-summary.md` (never overwrites). Prepend `/c/Users/rwsmy/AppData/Local/Microsoft/WinGet/Links` to PATH (it needs `ffprobe`). |
| Files owned | `docs/reports/inventory-2026-10-18.md` (NEW). Nothing else. |
| Footage | `C:\Users\rwsmy\clearwater-footage\` is READ-ONLY. Never write, rename or delete there; never point a pytest temp root there. |

## The report (`docs/reports/inventory-2026-10-18.md`)

1. **Run:** the command, the tool commit, the UTC time, and the two output paths with the md5
   of each.
2. **Counts per folder** (`Snorkel/`, `SCUBA/`): files, total size, and total duration.
3. **Recording modes:** resolution, frame rate, codec, bit depth, colour tags and HDR or Log
   flags, each with its count per folder. Quote the tool's own summary tables; do not
   recompute them by hand.
4. **Chaptered recordings:** the GoPro chapter groups the tool found (`GX01xxxx` / `GX02xxxx`
   ...), per folder.
5. **Error rows:** every row with `error` set, quoted, and skipped files.
6. **Uncovered GoPro names:** any file whose name does not follow the GoPro scheme.
7. **One line each:**
   - **No photos and no `.LRV`/`.THM`:** both columns are all-absent, not gaps (the owner,
     2026-10-15). CHARC is asking whether still photos are still to come.
   - **One non-indexed file:**
     - `Snorkel/6aca1cf5db06c242d9d53130.json` (318 MB) is not indexed, because the tool skips
       the `.json` extension.
     - CHARC probed it: an MP4 (ftyp isom), H.264 1920x1080 59.94, 180.08 s, encoder
       Lavf61.7.100, created 2026-10-10T11:12Z.
     - It is a cloud-made re-encode or highlight edit, not camera footage, and no original has
       that duration.
     - Do NOT probe or open it yourself; quote CHARC's finding.
8. **The WP0.2 footage test:** run
   `uv run pytest -q -rs tests -k test_real_footage_has_one_row_per_media_file` once and quote
   the result line. It should now be stable, because the download is complete.
9. **Nothing assigned:** no category is assigned, because categories are the owner's at CP1.
   The CSV's `category` column stays empty.

## Review

This is a deterministic read-only run of an accepted instrument, with no code change. The
adversarial nets are substituted by the orchestrator's independent verification. Reason:
nothing executable changes, and the report's claims are counts that I re-derive from the CSV at
my seat. No Reviewer A round.

## Notes for the cell

- **Setup:**
  - The orchestrator copies `clearwater.local.toml` into the worktree; never edit or commit it.
  - Run `uv sync` first.
  - Never use a bare `cd`; never `git stash`; never post to a mailbox.
- **Commit:** by pathspec (`git add -- docs/reports/inventory-2026-10-18.md` first), message
  `docs(inventory): real footage inventory 2026-10-18`, with `Co-Authored-By:` naming the model
  you actually run as.
- **STOP for:**
  - a tool error that aborts the run;
  - any need to edit code;
  - any write outside `work\reports\`, the worktree and pytest's temp folder.
- **Return report:** your FINAL message, under about 40 lines:
  - the commit;
  - the two output paths and their md5s;
  - the counts per folder and mode;
  - the chaptered groups;
  - the error rows;
  - the uncovered names;
  - the test result;
  - the locks.
