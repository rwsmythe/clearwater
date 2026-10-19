# WP-T2 — footage locator (dispatch brief, FINAL)

**Status:** FINAL, issued by the orchestrator 2026-10-19 on CHARC's rulings `35b13416` (scope),
`e5505505` (sequence: after the WP1.4 merge, on main) and `59860def` (relocate
`VIDEO_EXTENSIONS`). Spec **v0.5.2** (N1 portability; the footage folder is read-only:
CLAUDE.md "Inputs"). Cell: `implementer-sonnet-high` (the brief fixes the function, the rule,
the call sites and the tests). Worktree `.worktrees/wp-t2`, branch `wp-t2`, base = the main
commit named in the dispatch. Not exclusive; records no timing. Tests and tools only; no
product code.

| Field | Content |
|---|---|
| ID and title | WP-T2 — footage locator; closes DR-24 (the three footage tests that skip since the owner's layout change of 2026-10-18) |
| Goal | Every tool and test that names a chapter by stem finds it anywhere under the configured footage folder, so the owner's layout (`Snorkel/`, `SCUBA/`, `edits/`, lowercase `.mp4`) runs the footage tests again: `uv run pytest -q -rs` reports **0 skipped** on this machine. The owner's layout stands; code adapts, never the folder. |
| Files owned | `tools/local_config.py` (ADDITIVE: `VIDEO_EXTENSIONS`, the error class, `find_footage_file`; every existing signature and behaviour unchanged); `tools/inventory.py` (ONE line: line 48's definition becomes `from local_config import VIDEO_EXTENSIONS`; nothing else); `tools/lookcheck/pack.py` (the two chapter resolutions, lines 1274 and 1310, and docstring text naming `.MP4` paths); `tools/statistics_experiments.py` (the two resolutions, lines 370 and 1065, and docstring text); `tests/test_container_spike.py` (line 902 only); `tests/test_lookcheck.py` (line 1289 only); `tests/test_prototype_temporal.py` (test 7, line 839 only); `tests/test_footage_locator.py` (NEW); `docs/proofs/wp-t2-ledger.md` (NEW). NOTHING else: not `tests/test_local_config.py`, not `tests/test_inventory.py`, not `tools/container_spike/`, nothing under `src/`, `scripts/` or `tests/harness/`. |
| Interfaces consumed | `tools/local_config.py` (`load_local_config`, `LocalConfigError`), as built; `tools/inventory.py`'s `VIDEO_EXTENSIONS` value (`{".mp4", ".mov", ".360"}`). |
| Dependencies | None new. |
| Hardware flags | The unit tests carry none (FAKE footage tree). The three switched tests keep their existing markers. |
| Done | Plan section 4.5; the four gates green with `uv run pytest -q -rs` **0 skipped** and `uv run pytest -q -m gpu` green (WinGet links on PATH as usual); the harness gate green (cheap); the ledger written. No separate report: the ledger and the return carry it. |

## Claims

1. **`VIDEO_EXTENSIONS` relocated, not duplicated (CHARC `59860def`).** Its single definition
   moves to `tools/local_config.py` with the value unchanged
   (`frozenset({".mp4", ".mov", ".360"})`) and a docstring. `tools/inventory.py` imports it
   from there, so `inventory.VIDEO_EXTENSIONS is local_config.VIDEO_EXTENSIONS`. Grep proves
   no second literal of the set exists under `tools/`. The WP0.2 suite (`tests/test_inventory.py`,
   unchanged) is the no-behaviour-change proof. `local_config.py` gains no import beyond the
   standard library.
2. **The function.** In `tools/local_config.py`:

       class FootageLookupError(LocalConfigError):
           matches: tuple[Path, ...]   # empty when nothing matched

       def find_footage_file(stem: str, root: Path | None = None) -> Path

   - `root` defaults to `load_local_config().footage_path` (its errors propagate unchanged).
   - Walks `root` RECURSIVELY. A file matches when its stem equals `stem` case-insensitively
     (`str.casefold()` on both) AND its suffix, lower-cased, is in `VIDEO_EXTENSIONS`. So
     `GX011628` matches `Snorkel/GX011628.mp4` and `GX011628.MP4`; a `.LRV`, `.THM`, `.json`
     or `.png` of the same stem never matches.
   - `stem` must be a bare stem: refuse (`ValueError`, naming it) an empty string, a string
     containing a path separator, or one with a suffix in `VIDEO_EXTENSIONS`.
   - **Exactly one match** returns its path (as `root / <relative path>`, not resolved).
     **Zero:** `FootageLookupError` whose message contains `"not in the footage folder"` and
     names `stem` and `root`, with `matches == ()`. **Two or more:** `FootageLookupError`
     naming every match (sorted, relative to `root`), with `matches` set.
   - A missing or non-directory `root`: `FootageLookupError` naming it, `matches == ()`.
   - **Never leaves the root:** do not descend into a directory symlink or a Windows junction
     (Python 3.12: `os.walk(..., followlinks=False)` still descends into junctions, so test
     `os.path.isjunction` explicitly), and skip a matching file that is a symlink. State the
     rule in the docstring.
   - **Never writes**, never changes the cwd, never caches across calls.
   - Deterministic: walk order does not affect the result (sort before deciding).
3. **Call sites.**
   - `tools/lookcheck/pack.py`: `CHAPTERS` and `FLICKER_CHAPTER` stay stems; both
     resolutions go through `find_footage_file(stem, config.footage_path)`. A lookup failure
     is a configuration error on the existing one-line `error:` path, exit 2
     (`FootageLookupError` is a `LocalConfigError`, already caught: confirm it).
   - `tools/statistics_experiments.py`: both resolutions likewise; a lookup failure is refused
     BEFORE any write under `work/wp1.4/` (show the order in the code, and test it with a fake
     tree that lacks the chapter).
   - The three tests: zero matches -> `pytest.skip` with the existing reason text
     (`"GX011628 is not in the footage folder"`, stem only); two or more -> the test FAILS
     (an ambiguous footage folder is a defect, never a skip). Use the `matches` attribute to
     decide, never the message text.
   - Update every docstring or comment that names a root path such as `GX011627.MP4` so it is
     true of the stem lookup.
4. **Tests** (`tests/test_footage_locator.py`), all on a FAKE footage tree under `tmp_path`;
   none reads the real `clearwater.local.toml` or names the real footage folder (assert every
   root lies under `tmp_path` in a helper). Cases:
   - (a) nested match: `Snorkel/GX011628.mp4` found from the root;
   - (b) case: stem `gx011628` finds `GX011628.MP4`; stem `GX011628` finds `gx011628.mp4`;
   - (c) ambiguity: `Snorkel/GX011628.mp4` and `SCUBA/GX011628.MP4` -> `FootageLookupError`
     naming both, `len(matches) == 2`;
   - (d) zero match -> `FootageLookupError`, message contains `"not in the footage folder"`,
     `matches == ()`;
   - (e) sidecars ignored: `GL011628.LRV`, `GX011628.LRV`, `GX011628.THM` and
     `GX011628.json` beside a single `GX011628.mp4` -> the `.mp4`; with no video, -> zero
     match;
   - (f) a prefix is not a match: `GX0116280.mp4`, `GX011628_corrected.mp4` -> zero match;
   - (g) never leaves the root: a directory symlink AND a junction under the root pointing at
     an outside folder that holds `GX011628.mp4` -> zero match; a file symlink named
     `GX011628.mp4` -> zero match. Skip a link variant ONLY where the OS refuses to create it,
     saying so in the skip reason (junctions: `mklink /J` via `subprocess` or `_winapi`);
   - (h) bad stems (`""`, `"a/b"`, `"GX011628.MP4"`) -> `ValueError`;
   - (i) missing root and a root that is a file -> `FootageLookupError`;
   - (j) read-only: the tree's full listing and every file's bytes are unchanged after all
     lookups (one test over the fixtures);
   - (k) `inventory.VIDEO_EXTENSIONS is local_config.VIDEO_EXTENSIONS`;
   - (l) the WP1.4 runner refuses a fake config whose footage lacks the chapter with exit 2
     and creates nothing under the fake working folder.
   - **Positive control:** for (g), plant a version that follows links (locally, not
     committed) and show the test fails by name; record it in the ledger.
5. **Gate assertion restored.** With the real configuration on this machine, `uv run pytest
   -q -rs` reports **0 skipped**: the three footage tests RUN and pass. Quote the line.

## Declared operating envelope

Windows 11, Python 3.12, NTFS, the configured footage folder as the owner laid it out on
2026-10-18 (inventory `docs/reports/inventory-2026-10-18.md`: 35 videos, no duplicate stems).
Out of envelope: other filesystems' case rules, network shares, a footage folder being
modified during a lookup, link forms other than symlinks and junctions.

## Review loop (Reviewer A) -- per `docs/review-gate-clearwater.md` Part 1

- **Tier FAST** (CHARC `35b13416`: tests and tools only, no shipped output). Never tier the
  rigor: the same assertions apply.
- **ONE round.** Fix minors once; a new critical or major is fixed and stated in the return.
  - **Transport and flags:** WSL, codex-cli 0.162.1. Per-call flags
    `-m gpt-5.6-luna -c model_reasoning_effort=medium -s read-only --skip-git-repo-check`
    (the `fast` tier, `docs/codex-reviewer.md`); the banner assertion checks them.
  - **Probe:** one probe through the exact invocation before the round.
  - **Diff:** generated Windows-side with
    `git -C <worktree> diff -U8 <base>..HEAD -- . ':!uv.lock' ':!docs/proofs'`; WSL never runs
    git.
  - **The prompt** carries the claims, the envelope with a request to TAG out-of-envelope
    findings, the EXECUTED/REASONED paragraph verbatim from `docs/codex-reviewer.md`, and:
    "Do NOT read `docs/proofs/` or anything under `clearwater-review-evidence`; those are
    withheld. Never read or list `/mnt/c/Users/rwsmy/clearwater-footage`."
  - **Assertions** (all `grep -a`): the banner's model and effort match the tier; every
    `^ERROR` and `ERROR codex_core` line classified by provenance; the `^tokens used`
    footer; an anchored VERDICT line; at least one `^ succeeded in`;
    `grep -a -n 'docs/proofs\|wp-t2-ledger'` with every hit classified as an echo or an
    access.
  - **Evidence:** `C:\Users\rwsmy\clearwater-review-evidence\wp-t2\r1\` with md5s; ledger
    `docs/proofs/wp-t2-ledger.md`.
- **WHAT TO EXAMINE:** every way the walk can leave the root or match the wrong file (case,
  links, junctions, sidecars, prefixes, a directory named like a video); whether a lookup can
  write or change state; whether a test could touch the real footage; whether the relocation
  changes any inventory behaviour; whether an ambiguous folder can turn into a skip.
- Reviewer B is the orchestrator's own seat pass on the merge candidate (fill Part 2 item 2).

## Notes for the cell

- **The real footage folder is read-only.** The only real-footage contact is the gate run of
  the three existing footage tests; every new test uses the fake tree.
- **Working rules:**
  - The orchestrator copies `clearwater.local.toml` into the worktree; never edit or commit it.
  - `uv sync` in the worktree.
  - Prepend `/c/Users/rwsmy/AppData/Local/Microsoft/WinGet/Links` for pytest runs.
  - Never use a bare `cd`; never `git stash`; never post to a mailbox.
  - Commit by pathspec (`feat(wp-t2): ...`, `test(wp-t2): ...`), with `Co-Authored-By:`
    naming the model you actually run as.
- **STOP for:**
  - a change any existing `local_config` signature or behaviour would need;
  - a needed edit outside the owned files or lines (name it with file:line);
  - two footage files with one stem on the real folder (the gate would fail: report the
    paths, do not pick one);
  - any write outside the worktree, `tmp_path` and `work/`.
- **Return report:** your FINAL message, under about 50 lines: per-commit changes; the gate
  lines including the skip count and the harness gate; the test list with results; the
  positive control; the review round and its assertions; the locks; deviations.
