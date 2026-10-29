# WP4.2b -- Output-name containment in jobs.naming (DR-80) (dispatch brief, FINAL)

**Status:** FINAL 2026-10-29 on CHARC `5c056d647ad9ca99` (its WP4.2b paragraph, carried verbatim
below, governs this brief). Drafted by a drafting helper for the orchestrator (generation 18).
Spec v0.5.6; no spec clause changes. One validation in `jobs/naming.py`, plus its tests.

| Field | Content |
|---|---|
| ID and title | WP4.2b -- Output-name containment in jobs.naming (DR-80) |
| Lane | **CODEX**: `implementer-codex-sol-high` (gpt-6.1-sol / high), `codex exec` turns driven by `scripts/codex_cell.py`. Paces at dispatch (orchestrator fills): Codex `<pace>` vs Claude `<pace>`. The cell ends every turn with a FILES CHANGED block; the orchestrator commits and runs every heavy command the cell yields. |
| Tier and nets | Tier **STRONG** (footage-containment surface). Reviewer A = the Claude pass, `scripts/codex_cell.py review` (`claude -p --model opus --effort high`, read-only), between turns, to convergence, five-round gate. Reviewer B = the Claude pass at the orchestrator's seat. Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp4.2b\rN\`, `reviewB\`. |
| Base, worktree | Base = main at dispatch, AFTER WP4.2a's accept (its `check_outputs` parent guard and choice 3 on main). Worktree `.worktrees/wp4.2b`, branch `wp4.2b`. |
| Concurrency | CONCURRENT with WP4.2's build, on disjoint files: WP4.2 calls `jobs.naming` and never edits it. WP4.2b must NOT touch WP4.2's files: `src/clearwater/app/composition.py`, `tools/headless_export.py`, `src/clearwater/jobs/export.py`, `src/clearwater/core/backend.py`, `src/clearwater/analysis/engine.py`, `tests/test_wp42_*.py`, `tests/test_wp321_fft_release.py`, `tests/test_app_composition.py`, `tests/test_headless_export.py`, `docs/reports/wp4.2-video-path.md`, `docs/proofs/wp4.2-ledger.md`. |
| Gate | STACKED with WP4.2's two-leg suite if timing allows (one window; per-package `git patch-id` and each package's own Reviewer B, as the stacked form says), else its own window. The orchestrator decides by timing and tells CHARC. Every new test is parallel-leg (no `slow`, `gpu`, `footage` or `gui` marker). |
| Goal | No caller of `jobs.naming` can be given an output path outside its folder or carrying a stream name: the composed output NAME is checked as one portable name component before any plan exists. |
| Files owned | Exactly the ruling's list: `src/clearwater/jobs/naming.py` (that validation only, with the `Raises:` lines of `final_output_path` and `plan_output` that now name it); `tests/test_jobs_naming.py` (new tests only); ONE test in NEW `tests/test_wp42b_naming_guard.py`; `docs/reports/wp4.2b-naming-guard.md`; `docs/proofs/wp4.2b-ledger.md`. |
| NOT owned | Everything else, explicitly: `tools/headless_export.py` (WP4.2a's parent check STAYS as defence in depth; do not remove or weaken it), `src/clearwater/jobs/export.py`, every WP4.2 file above, `src/clearwater/interfaces/` (IF-1..IF-10 FROZEN), every existing test, `pyproject.toml`, `uv.lock`, `tests/conftest.py`, the register. |
| Done | Plan 4.5; ruff check, ruff format --check, mypy strict; the gate as above, both legs green; Reviewer A converged; report and ledger written. **DR-80 CLOSES** (CHARC rewrites the row at the accept). BINDING at the latest for WP4.3 (the GUI export reaches the plan). No harness gate. |

## The ruling (CHARC `5c056d647ad9ca99`, its WP4.2b paragraph, verbatim)

**The fix = WP4.2b, a Codex-lane micro-package** (the existing lane rule: well-specified, `jobs/naming.py` is not a frozen interface), dispatched AFTER WP4.2a's accept, CONCURRENT with WP4.2's build (disjoint: WP4.2 calls `naming` and never edits it; `tests/test_jobs_naming.py` is not WP4.2's). Scope, verbatim from DR-80: `_base_plan` (or `OutputPlan.path`) validates the composed NAME as one portable name component with the suffix's own rule (no separator, no drive, no `:`, `Path(name).name == name`, `os.path.splitdrive(name)[0] == ''`) and raises `ValueError` naming the source by name only; RED-first tests in `tests/test_jobs_naming.py` for `c:x`, `carrier:x` and a control; one runner test that the refusal is readable (exit 2 / failed item, no path printed; WP4.2a's choice 3 already leaves a naming `ValueError` to the engine's refusal, so check that route gives a readable failed item, not a traceback). Owned: `src/clearwater/jobs/naming.py` (that validation only), `tests/test_jobs_naming.py`, one test in a new `tests/test_wp42b_naming_guard.py`, report + ledger. Nets: A and B = Claude passes as for WP4.2a; tier STRONG (footage-containment surface). Gate: STACKED with WP4.2's two-leg suite if timing allows (one window, per-package patch-id and own B as the stacked form says), else its own window; your call by timing, tell me which. WP4.2a's runner parent check stays as defence in depth. Draft the short brief after WP4.2a's accept; one FYI with the FINAL brief, no ruling round unless it adds scope. BINDING at the latest for WP4.3 (the GUI export reaches the plan).

DR-80 (`docs/debt-register.md`, OPEN), its entry (the scope), verbatim: "BINDING, product defect outside WP4.2a's scope: `jobs/naming.py` `OutputPlan.path` (:268, `folder / (stem + extension)`) composes the output name from the source stem unchecked, so a source named `<letter>:<rest>` (an NTFS stream of a one-letter file) gives a DRIVE-RELATIVE planned path (`c:input_corrected.png`, drive `c:`, parent `c:`) that escapes the folder every caller checked; a longer stem (`carrier:input`) stays in the folder as a stream name. The suffix is validated (`:54-75`) but the stem is not. WP4.2a closes only the runner's route (`check_outputs` refuses a planned file whose parent is not the checked folder); the GUI's export (WP4.3) and any other caller of the plan still reach it."

Its signal / trigger, verbatim: "**WP4.2b** (Codex lane, after WP4.2a's accept, concurrent with WP4.2's build; disjoint files): `_base_plan` (or `OutputPlan.path`) validates the composed NAME as one portable name component with the suffix's own rule (no separator, no drive, no `:`, `Path(name).name == name`, `os.path.splitdrive(name)[0] == ''`) and raises `ValueError` naming the source by name only; RED-first tests in `tests/test_jobs_naming.py` for `c:x`, `carrier:x` and a control; one runner test that the refusal is readable (exit 2 / failed item, no path printed). At the latest WP4.3 (the GUI export reaches the plan). WP4.2a's runner check stays as defence in depth."

## The defect and the route (read at `32099ae`)

- The entry above is the defect (WP4.2a Reviewer A F1, EXECUTED through `main`). One addition:
  a video keeps `source.suffix` (`_base_plan`), so `x.mp4:s` carries `:` in the EXTENSION; the
  check covers the whole composed name (base plus extension).
- The export route of a planning `ValueError`: `ExportEngine._plan` (`export.py:675-687`) calls
  `plan_output` at `:679`, after the photo read (`:711`, plan at `:753`) or the video probe
  (`:808`, plan at `:837`); the `ValueError` propagates to `_run`'s `except Exception` (`:606`),
  which calls `_describe` (`:631-638`): `ValueError` is not in `_READABLE_ERRORS` (`:106`), so
  the item fails with `"<source name>: ValueError: <message>"`, `ascii_text`-escaped, no
  traceback. In the runner, WP4.2a's `check_outputs` leaves a naming `ValueError` to the engine
  (its choice 3), so the same failed item results with or without a configured footage folder.

## Task ladder

1. **Read and map.** `jobs/naming.py` (`validate_suffix`, `_FORBIDDEN_SUFFIX_CHARS`, `OutputPlan`,
   `_base_plan`, `final_output_path`, `plan_output`, `is_taken`); `tests/test_jobs_naming.py`;
   the route above in `jobs/export.py`; WP4.2a's `check_outputs` on main.
2. **Round-0 note in the ledger, then YIELD.** (a) WHERE the check sits. Recommended:
   `_base_plan`. It is the only place that composes a plan (`naming.py:292`; called by
   `final_output_path` at `:324` and `plan_output` at `:380`). It already runs `validate_suffix`,
   so the refusal comes before any plan, filesystem read or reservation. Collision numbering only
   appends `_<N>`, so checking `base + extension` once holds for every number. `OutputPlan.path`
   is a property read on every candidate (`plan_output`, `is_taken`, reservations); a raising
   property would surface there mid-loop. Record the choice with this reason, or the reason for
   `OutputPlan.path` if the code shows otherwise. (b) The rule, exactly the ruling's parenthetical
   applied to the composed name: no separator (`/`, `\`), no drive, no `:`,
   `Path(name).name == name`, `os.path.splitdrive(name)[0] == ''`. The `:` test is the portable
   core: on POSIX `splitdrive` returns `''` and `c:x` is a plain name. The suffix rule's OTHER
   items are not extended to the stem: `* ? " < > |`, control characters, `..`, a trailing dot
   or space, the temporary marker. Those exist to guard a typed fragment, and a source that
   already exists with such a name is legitimate on its OS. (c) The message names the source by
   NAME only (`source.name`, never the folder). (d) The RED list, (e) the depth figure. YIELD.
3. **RED, the validation, GREEN.** In `tests/test_jobs_naming.py`, RED first on the base:
   `c:x.jpg` and `carrier:x.jpg` through BOTH `final_output_path` and `plan_output`, photo and
   video, each raising `ValueError` whose text carries the source name and no folder; a video
   source whose extension carries `:` (`x.mp4:s`). Control: every WP2.3 fixture file name (the
   `tests/fixtures/` manifest) plans to the same path as on the base, at the default suffix, both
   with an output folder and beside the source. Then the validation; then GREEN on the whole file.
4. **The runner test** (`tests/test_wp42b_naming_guard.py`, ONE test, may be parametrised over a
   stand-in footage folder and none). Use the library `run` with
   `exports=composition.export_jobs(reader=<a reader double>)`, so the source need not exist
   and the planning is reached. The reader double returns a WP2.3 still's image for any path.
   Pass a source named `c:input.jpg` in `tmp_path`, built from a string
   (`Path(f"{tmp_path}{os.sep}c:input.jpg")`). `tmp_path / "c:input.jpg"` does NOT give that name
   on Windows: pathlib drops the colon on the same drive and yields a bare `c:input.jpg` on
   another. Use an output-folder setting, and run with the cwd
   monkeypatched to an empty `tmp_path` folder. Assert: the item `failed` with the readable text
   above (`ValueError` named, the source name, no `tmp_path` spelling); no traceback; nothing
   written in the output folder or in the cwd folder.
5. **Report and ledger.** `docs/reports/wp4.2b-naming-guard.md`: where the check sits and why;
   the rule; the RED/GREEN node ids; the control; the export route (file:line); WP4.2a's parent
   check kept as defence in depth; a "for CHARC" line with the DR-80 closure text.
   `docs/proofs/wp4.2b-ledger.md`: rounds, depth readings, every heavy run (command, counts, EXIT).
6. **Lint and types**, then `RUN REQUEST` (Codex lane: yield the command) for the gate as decided.

## Notes and STOP

- Light runs need no window: `uv run pytest -q tests/test_jobs_naming.py
  tests/test_wp42b_naming_guard.py -m "not gpu and not footage and not slow"`. The two-leg
  suite runs only in the posted window. Yields: round 0; after each review round, end the turn
  once the verdict is adjudicated, before remediating. Depth read every turn (~250K evaluation
  point, ~400K STOP).
- Commits (by the orchestrator): `fix(wp4.2b): ...`, `test(wp4.2b): ...`, `docs(wp4.2b): ...`;
  by pathspec, `-c core.autocrlf=false`, LF blobs, a `Co-Authored-By:` footer.
- STOP for: any edit outside the owned list; any existing test that must change; any change to
  a name that a legitimate source would have produced (the WP2.3 control shows none); a need to
  touch `export.py`, the runner or an interface; any write outside `tmp_path`, the worktree and
  `work/`.
