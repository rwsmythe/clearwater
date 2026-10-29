# WP4.3a — Spawn helper and import / redaction hardening (dispatch brief, FINAL)

**Status:** FINAL on CHARC `8fb519bac1878075` (2026-10-29 12:32:36Z; main `1270021`); its Rulings at the end GOVERN the Questions. DRAFT 2026-10-29, carved by a drafting helper for the
orchestrator (generation 20) from the FINAL WP4.3 brief (`docs/briefs/wp4.3-brief.md`, CHARC
`7c7df3dbe237ceb7`, main `101f181`; its Q14 split). The ruled text below is carried VERBATIM and
governs this brief. Spec v0.5.6; no spec clause changes. Base = main at dispatch. Worktree
`.worktrees/wp4.3a`, branch `wp4.3a`. Owner decisions: none.

| Field | Content |
|---|---|
| ID and title | WP4.3a — the AD-23 spawn helper (DR-58 (b)), DR-81 (a)(b)(c), DR-76, DR-77 and DR-85 |
| Lane | **CODEX**: `implementer-codex-sol-high` (gpt-6.1-sol / high), `codex exec` turns driven by `scripts/codex_cell.py`. The orchestrator fills the paces at dispatch: Codex `<pace>` vs Claude `<pace>`. The cell ends every turn with a FILES CHANGED block; the orchestrator commits and runs every heavy command the cell yields. |
| Tier and nets | Tier **STRONG** (product code). Reviewer A = the Claude pass, `scripts/codex_cell.py review` (`claude -p --model opus --effort high`, read-only), between turns, to convergence, five-round gate. Reviewer B = the Claude pass at the orchestrator's seat. Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp4.3a\rN\`, `reviewB\`. |
| Sequencing | The Codex lane is ONE cell; WP4.3a dispatches when WP-T6's cell stands down (ruling Q14). CONCURRENT with WP4.3 (opus-high) on disjoint files. Merge order = whichever is ready first; the other rebases, patch-id re-proved. |
| Goal | (1) Every FFmpeg and ffprobe child in `src/clearwater` is spawned through ONE helper in `io/video/pipes.py` that sets CREATE_NO_WINDOW on Windows (0 elsewhere) and the `FFREPORT`-free environment (AD-23 extended; N1 approval per Q13 as ruled). (2) The ffprobe timeout text carries no tool path, and the runner redacts mixed separators and a raising footage-folder resolution (DR-81). (3) A writer-made provenance imports as a preset (DR-76), and a year-1 `created` stamp is a readable refusal in `PresetStore` and a set-aside in `load_settings`, never an `OverflowError` (DR-77, DR-85). |
| Files owned | Exactly the ruling's Q14 list, each with its origin package: `src/clearwater/io/video/pipes.py` (WP3.9: the helper), `capability.py`, `encode.py`, `verify.py` (WP3.10: their spawn sites; `tool_env` delegates; `verify.py` also DR-81 (c)), `decode.py` (WP3.9: its spawn sites), `probe.py` (WP3.7: its spawn site; DR-58 (b)); NEW `tests/test_io_video_spawn.py`; `tools/headless_export.py` (WP4.1, extended by WP4.2, WP4.2a, WP4.2b: DR-81 (a)(b), and the key set at `:143` with its docstring `:593-599`, Q20; nothing else); NEW `tests/test_wp43_runner_redaction.py`; `src/clearwater/config/presets.py` (WP3.15: `:69`, `:577`), `src/clearwater/config/settings_store.py` (WP3.15: `:71`); `tests/test_config_presets.py` and `tests/test_config_settings.py` (WP3.15: new tests only); `docs/reports/wp4.3a-hardening.md`; `docs/proofs/wp4.3a-ledger.md`. |
| NOT owned | `src/clearwater/interfaces/` (IF-1..IF-10 FROZEN; DR-77's root cause `interfaces/parameters.py:211` stays), `src/clearwater/gui/`, `src/clearwater/app/`, `src/clearwater/jobs/`, `src/clearwater/io/photo/` (the writer's `"profile"` key is unchanged, Q20), every other `io/video/` and `config/` module, every file WP4.3 owns (its brief's "Files owned", including `tests/test_app_startup.py`, which carries DR-85's start-up test), every existing test (beyond the two config test files' new tests), `tests/conftest.py`, `tests/fixtures/`, `pyproject.toml`, `uv.lock`, the register. |
| Locks | No frozen interface; no `gui/` or `app/` file. N1: the flag lives in the helper only, `subprocess.CREATE_NO_WINDOW` when `sys.platform == "win32"`, else `0`; no spawn site sets `creationflags` itself (Q13 as ruled). No new `io/video` module (`tests/test_io_video_probe_rules.py:31` pins the set). No dependency. No write under the footage folder; every test writes under `tmp_path`. AD-28 / AD-30: every new test is parallel-leg (no `gpu`, `footage`, `gui` or `slow` marker) unless a reason is written beside its marker; no test on the whole footage clip. |
| Done | Plan 4.5; ruff check, ruff format --check, mypy strict; the touched tests and the light layering set green; Reviewer A converged; Reviewer B returned (clean, or its one remediation and re-run); then the ONE two-leg gate at the orchestrator's seat on the final candidate, per the fill's GATE_CHECKS at dispatch (fill Part 2, Order). DR-58 (b), DR-76, DR-77, DR-81 (a)(b)(c) and DR-85 CLOSE (CHARC rewrites the rows; the AD-13 and AD-23 notes are CHARC's at this accept). Report and ledger written. No harness gate. |

**Why.** CHARC's FINAL ruling on WP4.3's Revision 1 split these items off: none touches a
frozen interface, `gui/` or `app/`, and every rule is already written (ruling Q14). The console
flash under the GUI (WP3.9's limit), an operator-set `FFREPORT` writing logs from every probe and
decoder (DR-58 (b)), a tool path in a failure text (DR-81 (c)), and a corrupt preset or settings
file that crashes rather than refuses (DR-77, DR-85; DR-85 stops start-up) are all reachable
once WP4.3 starts the program.

## The register rows (main `101f181`, verbatim)

| Row | Entry (verbatim) | Signal / trigger (verbatim) | Disposition |
|---|---|---|---|
| DR-58 (b) | (a) Reviewer A R5 #10: several GPUs -- `capability.py` detects the first NVENC device only; (b) WP3.7's `probe.py` inherits `FFREPORT` from the environment, so an operator-set report path makes every probe write a log; (c) a test-only timing bound: `test_run_once_records_the_row_and_deletes_the_output` asserts `-0.05 < offsets["telemetry_origin"]` and failed twice for seat 9 under another load (-0.069, -0.062), passing every isolated and quiet run and the gate suite. | (a) owner hardware (one GPU); (b) WP3.7's next touch clears `FFREPORT` for the probe; (c) CLOSED 2026-10-28 by WP-T4 (E1): the test carries `@pytest.mark.slow` with a reason and runs in the serial leg; it passed in every baseline, serial leg and durations run of rung 4 and the final legs. (a) and (b) remain OPEN. (b) RE-SIGHTED 2026-10-29 by WP4.2's Reviewer B (B10, pre-existing): an inherited `FFREPORT` also reaches the decoder launches and two WP4.2 test launches; the clearing belongs at the one launch site WP3.7's touch owns. | **CLOSES (b)** by task 3: every spawn site in `src/` gets the helper's `FFREPORT`-free environment. Residual named in the closure (Q-B): the test launches `tests/test_wp42_v3_product.py:141` (command at `:134`) and `tests/test_wp321_fft_release.py:165`. (a): NOT REACHED. |
| DR-76 | Two accepted components disagree: the photo writer's HEIC provenance JSON carries `"profile": "built-in sRGB"` (WP3.6 7624f5c) and the accepted `PresetStore.import_preset` (WP3.15 75d7dc5) refuses that file, as the WP4.1 runner's `--parameters` does; IF-9 and AD-13 hold; the runner's docstring names the AD-13 forms the importer reads. | WP4.3 (presets are imported there): decide whether the importer accepts the writer's provenance form or the writer's field is renamed to an AD-13 key; one test imports an exported HEIC's provenance. | **CLOSES** by task 4 (Q20 as ruled). |
| DR-77 | MINOR: `PresetStore.import_preset` (WP3.15, accepted) lets an `OverflowError` escape on a provenance `created` at year 1 with a +01:00 offset (the runner's own copy of the parse was fixed in WP4.1's terminating-round cleanup 23fc88b with a failing-first test); a hostile or corrupt preset file reaches the GUI as a traceback rather than a readable refusal. | WP4.3's touch of the preset import path (the settings dialog / preset panel wiring): catch and refuse readably, with the same failing-first test. | **CLOSES** by task 4 (Q21 as ruled). |
| DR-81 | MINOR, two pre-existing runner redaction gaps in `tools/headless_export.py`: (a) a known folder spelled with MIXED separators is not redacted in argparse's text (the `Redactor` builds backslash, forward-slash and escaped forms, not arbitrary mixes); (b) a footage-folder resolution that RAISES escapes `_main` raw with the full path (defensive only; not reproduced on Python 3.12 / Windows). Note N5 (ADVISORY, origin WP4.1 `715fd08`): `equal_statistics`' scalar branch in `tests/test_wp41_v8.py` equates float32 +0.0 and -0.0; unreachable today (statistics are dicts of ndarray). (c) added 2026-10-29 at WP4.2's accept (Reviewer B re-run B'1, banked; origin WP3.7 `io/video/verify.py:234`): a packet-listing TIMEOUT's text carries the full ffprobe executable path into the failure record, and the `Redactor` does not know the tool folder; reachable only on the 120 s ffprobe timeout. | WP4.3 (the runner's next redaction touch; WP4.2 made no `Redactor` edit): (a), (b) and (c) close together, (c) by adding the tool folder to the known folders or by redacting the timeout text at its source. N5 closes with the next touch of `equal_statistics`. | **CLOSES (a)(b)(c)** by task 5 (Q23 as ruled; Q-A on the limit). N5: NOT REACHED. |
| DR-85 | MAJOR, pre-existing start-up crash, the sibling of DR-77: a `settings.json` whose `last_parameters.created` is `0001-01-01T00:00:00+01:00` makes `load_settings` raise `OverflowError` ("date value out of range") because `config/settings_store.py:71` maps only `(ValueError, RecursionError)` into the set-aside path; the shell's `start_up` (`gui/shell.py:148`) catches only `UnsupportedFormatVersionError`, so the program cannot start until the user deletes the file. Root cause `interfaces/parameters.py:211` `astimezone(UTC)` (FROZEN IF-9; not touched). Reachable only by a hand-edited or foreign settings file (the writer never emits such a value). | WP4.3a (Codex, Q21 as ruled): `OverflowError` joins the decode-failure tuple at `settings_store.py:71` (file set aside, defaults used) and at `presets.py:577` (DR-77); failing-first tests; WP4.3's `tests/test_app_startup.py` starts the program over such a file (xfail strict with this row's id until WP4.3a is on main). | **CLOSES** by task 4 (Q21 as ruled). WP4.3's start-up test drops its `xfail(strict)` once this is on main. |

## The ruled text this brief inherits (verbatim)

From the WP4.3 brief's Questions (recommended answers, adopted as ruled below):

9. **The spawn helper's place (AD-23 extended).** Recommended: `io/video/pipes.py`.
   - It is the AD-23 module, it imports nothing from the package, and `probe.py` cannot import
     `capability.py` without a cycle (`capability.py` imports `probe.find_tool`).
   - The helper returns the `Popen`/`run` keyword arguments (`creationflags`, `env` without
     `FFREPORT`). `capability.tool_env` stays as a name and delegates to it.
   - No new `io/video` module, so the module-set pin is unchanged.
   Alternative: a new `io/video/spawn.py`, which changes `test_io_video_probe_rules.py`'s pinned
   set (a test change to rule).
   The flag itself is Windows-specific code: question 13.
13. **N1: CREATE_NO_WINDOW is Windows-specific code.** N1: "no OS-specific code without the
    architect's approval".
    - Ground: WP3.10 accept line 93 ("**WP4.3:** the shared CREATE_NO_WINDOW spawn helper");
      WP3.9 accept ("CREATE_NO_WINDOW banked to WP4.3 (AD-23 extended by CHARC, `df21ab0`)");
      AD-23's extension ("spawned with the Windows CREATE_NO_WINDOW creation flag (a no-op
      elsewhere) ... implemented once in a shared spawn helper by WP4.3").
    - Recommended: CHARC CONFIRMS that AD-23's 2026-10-21 extension is the N1 approval for this
      one helper, with no new AD row, on three conditions:
      - the flag is set in ONE place (the helper), as `subprocess.CREATE_NO_WINDOW` when
        `sys.platform == "win32"`, else `0`;
      - the fallback on every other OS is `creationflags=0` (subprocess's own default), so the
        same call runs unchanged with the same `FFREPORT`-free environment;
      - tests cover both branches (the Windows value asserted on this laptop, the other branch
        by a monkeypatched platform) and an AST test pins that no spawn site sets
        `creationflags` itself.
    - Alternative: a new AD row recording the approval separately (more paperwork, the same
      code). Without approval: no flag, and a console may flash under the GUI on Windows (the
      WP3.9 limit stays).
14. **Lane: one Codex-eligible sibling.** Recommended: split **WP4.3a** onto the Codex lane
    (`implementer-codex-sol-high`, the Claude pass as both nets; STRONG):
    - the spawn helper (questions 9 and 13 as ruled; `io/video/pipes.py`, `capability.py`,
      `decode.py`, `encode.py`, `probe.py`, `verify.py`, `tests/test_io_video_spawn.py`; DR-58 (b));
    - DR-81 (a)(b)(c) (Q23; `tools/headless_export.py`, `tests/test_wp43_runner_redaction.py`);
    - DR-76 and DR-77 with the start-up sibling (Q20, Q21; `config/presets.py`,
      `config/settings_store.py`, `tests/test_config_presets.py`, `tests/test_config_settings.py`).

    Ground: none of it touches a frozen interface, `gui/` or `app/`. Every rule is written: the
    ruled Q9 and Q13, the rows' text and Q20/Q21 as ruled. Its files are disjoint from WP4.3's, so
    it can run concurrently with WP4.3's round 0 and build, and it shrinks an L package that WP4.1
    and WP4.2 needed four cells each to land. Cost: one more gate (about 52 min), and AD-23's
    "applied by" note moves to WP4.3a's accept. It also serves the owner's 2026-10-29 lane
    balance.
    Alternative: keep all of it in WP4.3: one gate, a larger review surface.
20. **DR-76: which side.** Recommended: the IMPORTER side.
    - `config/presets.py:69` adds `"profile"` to the provenance keys that are dropped (reported in
      `dropped_keys`, so the panel's existing "carried provenance (...); it was not kept" warning
      names it, `gui/preset_panel.py:395-406`).
    - The runner's copy (`tools/headless_export.py:143`) moves in step.
    - The writer (`io/photo/writer.py:23`, `:79-81`) is unchanged, so every PNG already written
      stays importable. CHARC adds an AD-13 note naming `"profile"` as a writer provenance key.
    - Test: export a tagged nclx HEIC through the real engine, write its provenance text to a
      file, import it: OK, `profile` dropped.

    Alternative: rename the writer's key into AD-13's set. That is an `io/photo` grant and a
    change of the D91 provenance shape, and files already written keep the old key.
21. **DR-77 and its start-up sibling.** EXECUTED at the drafting seat on `cde1cd9`:
    - a `settings.json` whose `last_parameters.created` is `0001-01-01T00:00:00+01:00` makes
      `load_settings` raise `OverflowError` ("date value out of range"), because
      `config/settings_store.py:71` maps only `(ValueError, RecursionError)`;
    - the shell's `start_up` (`gui/shell.py:148`) does not catch it, so the program cannot start
      until the user deletes the file;
    - `PresetStore.import_preset` raises the same (DR-77); the root cause is
      `interfaces/parameters.py:211` (`astimezone(UTC)`, FROZEN IF-9; not touched).

    Recommended:
    - add `OverflowError` to the decode-failure mapping at `config/presets.py:577` (import, load
      and list all refuse readably as `FormatError`) and at `config/settings_store.py:71` (the
      file is set aside, defaults are used, the existing path);
    - each fix gets a failing-first test, and `tests/test_app_startup.py` starts the program over
      such a file;
    - CHARC registers a row for the sibling (closed by this touch).

    Alternative: widen `gui/preset_panel.py:47` `_FAILURES` (WP3.17). That covers only the
    panel, and start-up still fails.
23. **DR-81 (a)(b)(c).** Recommended:
    - (c) at its SOURCE: the timeout text at `io/video/verify.py:233-234` names the file and the
      120 s limit, not the ffprobe command, so the GUI's failed item is clean too. `verify.py` is
      already a spawn-site edit;
    - (a): the `Redactor` matches a known folder under any mix of `\` and `/`;
    - (b): a raising footage-folder resolution in `main` becomes a redacted usage refusal (exit
      2);
    - each fix gets a RED-first test in `tests/test_wp43_runner_redaction.py`; N5 is NOT REACHED.

    Alternative for (c): add the tool folder to the `Redactor`'s known folders (runner only; the
    GUI's text keeps the path).

From CHARC `2c4476d9869df056` (2026-10-28, the WP4.3 paragraph, verbatim extracts):

Q9 `io/video/pipes.py` as recommended (helper returns the spawn keyword arguments; `tool_env` delegates; the five spawn sites edited; no new `io/video` module; DR-58 (b) CLOSES).

Q13 CONFIRMED: AD-23's 2026-10-21 extension IS the N1 approval for this one helper, no new AD row, on the three conditions as written (one place, `subprocess.CREATE_NO_WINDOW` on `win32` else 0; every other OS the same call with `creationflags=0` and the same `FFREPORT`-free environment; both branches tested + an AST pin that no spawn site sets `creationflags`). I add a dated "applied by WP4.3" note to AD-23 at the accept.

From CHARC `7c7df3dbe237ceb7` (2026-10-29, verbatim):

**Q14 split WP4.3a to the Codex lane: CONCUR.** WP4.3a = the AD-23 spawn helper with DR-58 (b) (Q9/Q13 as ruled: `io/video/pipes.py`, `capability.py`, `decode.py`, `encode.py`, `probe.py`, `verify.py`, NEW `tests/test_io_video_spawn.py`); DR-81 (a)(b)(c) (Q23: (c) at its source in `verify.py`, (a)(b) in `tools/headless_export.py`, NEW `tests/test_wp43_runner_redaction.py`); DR-76 and DR-77 with the start-up sibling (Q20, Q21: `config/presets.py`, `config/settings_store.py`, the two config test files, the runner's key set at `headless_export.py:143`). No frozen interface, no `gui/`, no `app/`; every rule written; files disjoint from WP4.3. Lane `implementer-codex-sol-high`, Claude pass as both nets, tier STRONG (product code). SEQUENCING: the Codex lane is ONE cell and WP-T6 holds it; WP4.3a dispatches when WP-T6's cell stands down (its gate may still be running at your seat), from a SHORT brief your helper carves from this one's ruled text (the rows above, Q9/Q13/Q20/Q21/Q23 verbatim, locks, a Done, its own ladder) for a quick ruling of mine. WP4.3 (opus-high) dispatches NOW on this FINAL and does not wait. Merge order = whichever is ready first; the other rebases, patch-id re-proved. AD-23's "applied by" note moves to WP4.3a's accept (mine). WP4.3's text keeps a one-line pointer per moved row ("WP4.3a") so its register table stays complete. Codex-built packages would become 7 of the accepts with it.

**Q20 DR-76 importer side: CONCUR** (`config/presets.py:69` drops `"profile"` reported in `dropped_keys`; the runner's copy in step; the writer unchanged so every PNG already written stays importable). The AD-13 note naming `"profile"` as a writer provenance key is mine at WP4.3a's accept. (Moves to WP4.3a.)

**Q21 DR-77 and the start-up sibling: CONCUR** (`OverflowError` joins both decode-failure tuples; failing-first tests; `tests/test_app_startup.py` in WP4.3 starts the program over such a file once WP4.3a's fix is on main, or carries the test `xfail(strict)` with the DR-85 reason until it is). **NEW ROW DR-85** written now at my commit named in the cue: pre-existing start-up crash, reproduced by the drafting seat and by you on `cde1cd9`; closes at WP4.3a's accept. STOP candidate 2 closed. (Fix moves to WP4.3a; the start-up test stays in WP4.3.)

**Q23 DR-81: CONCUR** ((c) at its source in `verify.py:233-234`, naming the file and the 120 s limit; (a) mixed separators; (b) a raising resolution -> redacted usage refusal exit 2; RED-first tests; N5 NOT REACHED). (Moves to WP4.3a.)

The AD-23 "applied by WP4.3" note in `2c4476d9869df056`'s Q13 is superseded by Q14 above: it
moves to WP4.3a's accept.

## Task ladder

1. **Read.** `uv sync`. Read this brief, AD-23 and AD-13 (`docs/decisions.md`), the five rows,
   `io/video/pipes.py`, the seven spawn sites, `capability.tool_env` (`capability.py:73-83`), the
   runner's `Redactor` (`tools/headless_export.py:379`) and `_main` (`:1304-1309`), and
   `config/presets.py` `_read` (`:566-578`) and `config/settings_store.py` `load_settings`
   (`:33-73`).
2. **Round 0 note (turn 1, no product code), in the ledger:**
   - every spawn call in `src/clearwater` by line. On `101f181` they are `capability.py:89`,
     `decode.py:171`, `:330`, `:344`, `encode.py:879`, `probe.py:127` and `verify.py:225`; say
     which pass `env=tool_env()` today (`capability.py:95`, `encode.py:884`, `verify.py:231`; not
     `decode.py` or `probe.py`);
   - DR-58 (b)'s two WP4.2-era test launches by line: `tests/test_wp42_v3_product.py:141`
     (command built at `:134`) and `tests/test_wp321_fft_release.py:165`. Both inherit the
     environment and are not owned (Q-B);
   - the helper's signature and how `tool_env` delegates; how the import graph stays acyclic
     (`pipes.py` imports nothing from the package; `probe.py` cannot import `capability.py`);
   - the DR-81 (c) text and limit (Q-A); the `Redactor` mixed-separator rule; the (b) route in
     `_main`;
   - the fixture for DR-76's test: a WP2.3 HEIC tagged sRGB by `nclx` without an ICC profile
     (`heic8-gradient-none` and the others in `tests/test_wp41_photo_path.py:48-52`), exported
     through `clearwater.app.composition.export_jobs()` with `force_cpu`; its `iTXt`
     `clearwater-provenance` text (`io/photo/png.py:26`) written to a file and imported;
   - every test you will add, with the base it fails on.
   YIELD.
3. **The spawn helper (Q9, Q13 as ruled).** RED first: an AST test that every
   `subprocess.run`/`Popen` call in `src/clearwater` goes through the helper and that no spawn site
   sets `creationflags`; a test that the Windows branch gives `subprocess.CREATE_NO_WINDOW` on this
   laptop and a monkeypatched other platform gives `0` with the same environment; a test that a
   child spawned with `FFREPORT` set in the parent writes no report file (under `tmp_path`). Then
   the helper and the seven sites. CHECK: WP3.7, WP3.9 and WP3.10 tests pass unchanged; the
   module-set pin is unchanged.
4. **The config readers (Q20, Q21 as ruled).** RED first, each failing on the base:
   - DR-77: `PresetStore.import_preset` of a preset whose `created` is
     `0001-01-01T00:00:00+01:00` raises a `PresetImportError`, not `OverflowError`; the same file
     stored as a preset is refused readably by `load` and listed as unreadable by
     `list_presets` (its catch at `presets.py:326-327`);
   - DR-85: `load_settings` over a `settings.json` whose `last_parameters.created` is that value
     sets the file aside and returns defaults;
   - DR-76: the exported provenance (round 0) imports, `profile` reported in `dropped_keys`; the
     runner's `--parameters` accepts the same file.
   Then `OverflowError` joins the two decode-failure tuples (`presets.py:577`,
   `settings_store.py:71`) and `"profile"` joins the dropped keys (`presets.py:69`,
   `headless_export.py:143`, the docstring `:593-599` in step).
5. **DR-81 (Q23 as ruled).** RED first in `tests/test_wp43_runner_redaction.py`: (a) a known
   folder spelled with mixed separators is redacted in argparse's text; (b) a raising footage-folder
   resolution is a redacted usage refusal, exit 2; and in `tests/test_io_video_spawn.py` (or a
   verify-side case there) (c) a forced packet-listing timeout's text names the file and the limit,
   not the ffprobe path. Then the fixes.
6. **Light runs** (the cell's): the touched tests; `tests/test_io_video_*.py`,
   `tests/test_config_*.py`, `tests/test_headless_export.py`, `tests/test_wp42a_runner_hardening.py`,
   `tests/test_wp42b_naming_guard.py`; the layering set `tests/test_core_deps.py`,
   `tests/test_color_deps.py`, `tests/test_io_video_decode_rules.py`,
   `tests/test_io_video_probe_rules.py`, `tests/test_analysis_deps.py`, `tests/test_gui_deps.py`,
   `tests/test_app_deps.py`. The orchestrator runs anything heavier the cell yields.
7. **Reviewer A rounds** (the Claude pass between turns) to convergence; report FINAL.
8. **Then the orchestrator's** Reviewer B (the Claude pass at its seat) and the ONE two-leg gate
   on the final candidate, per the fill's GATE_CHECKS at dispatch (WP-T6 may have amended the
   expressions with `and not fullclip`).

## STOP for

A change needed in a frozen interface, `gui/`, `app/`, `jobs/` or any file not owned; a
dependency; any OS-specific code beyond the one helper; a new `io/video` module; any write under
the footage folder; a choice this brief leaves open.

## Questions for CHARC (recommended answer first)

- **Q-A. DR-81 (c)'s limit is 600 s, not 120 s.** `verify.py:45` sets `READ_TIMEOUT_S = 600`, the
  timeout of the listing at `:229`; the 120 s in DR-81 (c), WP4.2's accept and ruling Q23 is
  `probe.py:47` `TOOL_TIMEOUT_S`, whose timeout text is already fixed text (`probe.py:128-131`).
  Recommended: the new text names the limit through `READ_TIMEOUT_S` (so 600 s today), and CHARC
  corrects the row's figure at the accept. Alternative: change `READ_TIMEOUT_S` to 120 (a
  behaviour change for long clips; not recommended).
- **Q-B. DR-58 (b)'s two test launches.** `tests/test_wp42_v3_product.py:141` and
  `tests/test_wp321_fft_release.py:165` spawn FFmpeg with the inherited environment; neither file
  is in Q14's list. Recommended: NOT owned; the closure names them as the test-only residual (a
  test run with an operator-set `FFREPORT` is outside the envelope). Alternative: grant those two
  lines `env=tool_env()` (two test files outside Q14's list).
- **Q-C. The same leak class at `decode.py:178`.** `_check_cuda` returns
  `f"{type(error).__name__}: {error}"`; a `TimeoutExpired`'s text carries the full ffmpeg
  command, and `decode.py:148` logs it as a WARNING. Recommended: fix it in the same touch
  (`decode.py` is already a spawn-site edit): a fixed text naming the
  `CUDA_CHECK_TIMEOUT_S` (`decode.py:65`, 30 s) limit, one RED-first test. Alternative: bank it as
  a DR-81 (d) candidate (log only, never a user message).

## Rulings (CHARC `8fb519bac1878075`, 2026-10-29 12:32:36Z, verbatim; they GOVERN the Questions above)

**CHARC RULING on the WP4.3a brief DRAFT (query f62006da3a574003; `brief-wp4.3-rev` bc0b8a2, `docs/briefs/wp4.3a-brief.md`, 230 lines, 0 CR, read in full; Q-A/Q-B/Q-C citations verified at `verify.py:45/:229-234`, `probe.py:47`, `decode.py:65/:148/:172-178`, the two test launches): FINAL on this post.** Append this ruling verbatim under a Rulings section, commit it onto main, dispatch when WP-T6's Codex cell stands down.

- **Q-A (the limit is 600 s): CONCUR, recommended.** `READ_TIMEOUT_S = 600` is the listing's timeout; the 120 s in DR-81 (c), WP4.2's accept and my Q23 was `probe.py`'s `TOOL_TIMEOUT_S`. The new text names the limit THROUGH the constant (so it reads 600 s today and follows any later change), never the ffprobe command or path. I have corrected DR-81 (c)'s figure in the register at my commit named in the cue; the constant is not changed.
- **Q-B (the two test launches): CONCUR, recommended.** `tests/test_wp42_v3_product.py:141` and `tests/test_wp321_fft_release.py:165` are NOT owned; the DR-58 (b) closure names them as the test-only residual, and a test run under an operator-set `FFREPORT` is outside the envelope. (They can take `env=tool_env()` at their files' next touch; WP-T6 does not own them either.)
- **Q-C (`decode.py:178`): CONCUR, recommended, WIDENED to both branches.** `_check_cuda`'s `except (OSError, subprocess.TimeoutExpired)` returns fixed text in BOTH cases: for `TimeoutExpired`, the limit through `CUDA_CHECK_TIMEOUT_S` (30 s); for `OSError`, the error class and `strerror` only (an `OSError` from a failed spawn carries the executable path in its `filename`, which is the same leak class). Neither branch includes the command, the path or the raw `str(error)`. One RED-first test per branch. The WARNING at `:148` stays a log line; the test asserts the text, not the logger. Record it as DR-81 (d) CLOSED in the same touch (I add (d) to the row at the accept, closed on arrival).
- **The rest as drafted:** files owned = exactly Q14's list; the ruled Q9/Q13/Q20/Q21/Q23 text governs; round 0 as laid out (the seven spawn sites by line, which pass `env=tool_env()` today, the acyclic import argument, DR-76's fixture route through `export_jobs()` with `force_cpu`); every new test parallel-leg unless a reason sits beside its marker; Reviewer A = the Claude pass to convergence, B = the Claude pass at your seat, then the ONE gate with whatever expressions the fill carries at dispatch.
- **Owed by me at WP4.3a's accept:** AD-13 note (`"profile"` as a writer provenance key), AD-23 "applied by WP4.3a" note, closures of DR-58 (b), DR-76, DR-77, DR-81 (a)(b)(c)(d), DR-85.

**WP-T6 rung-3 grant (F401 on `test_io_video_encode.py:48`): CONCUR**, your call was right and inside the jobs file's own rule; nothing further from me. **WP4.3 dispatched on 038f02e: noted**; the round-0 table comes to me.
