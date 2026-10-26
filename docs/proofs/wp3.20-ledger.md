# WP3.20 -- Settings: cumulative round ledger

Cell: implementer, seat 1 (Sonnet 5.5). Worktree `.worktrees/wp3.20`, branch `wp3.20`, base main
`718324b`. Brief `docs/briefs/wp3.20-brief.md` (FINAL; its Rulings govern). Reviewer A: STRONG,
five-round gate.

## Round 0 (read and table; no product code)

Read: recipe, brief, review-gate Part 1, frame sections 1, 2, 4, 5, `gui/contract.py`,
`gui/shell.py` (start-up, `_open_settings`, close save), `gui/session.py` (`set_settings`),
`gui/engines.py`, `gui/jobs.py` (head), `gui/messages.py` (owners), `tests/gui_support.py`,
`tests/test_gui_deps.py`, `config/settings_store.py`, `jobs/naming.py` (`validate_suffix`),
`interfaces/stubs.py` (sink, cache), `wp3.10:capability.py` (`resolve_encoder`, read-only).
Foreign changes in the worktree: none (`git status` clean at `718324b`).

### Control table (G12 order)

One rule for all fields: a control that is still at the value it first displayed does NOT
overwrite its field; the new `Settings` is `dataclasses.replace(session.settings(), <only the
edited fields>)`. So a stored value the control cannot show exactly (cache bytes not a whole GB,
an out-of-set quality, a stored unavailable encoder, a stored 10-bit True on an 8-bit encoder) is
written back unchanged unless the user edits that control.

| G12 setting | `Settings` field | Widget | Shown | Stored | Validation | Disabled-with-reason |
|---|---|---|---|---|---|---|
| Output folder (D34) | `output_folder` | label + "Choose..." + "Use source folder" buttons | "Same folder as the source" or the path | `None` or `Path` | none here (writability is WP3.14) | none |
| Output suffix (D36) | `output_suffix` | `QLineEdit` + error label | the text | `str` as typed | `jobs.validate_suffix` on every edit (and on the initial text, and again at accept); the `ValueError` text beside the field | OK disabled while invalid |
| PNG bit depth (D22) | `png_bit_depth` | `QComboBox` | "16-bit", "8-bit" | `16` / `8` | closed set | none |
| Video encoder (D26, D74) | `video_encoder` | `QComboBox` (encoder rule below) | "Automatic (NVENC when available)", then one item per capability | `"auto"` or the capability name | an unavailable item cannot be chosen | unavailable item disabled, text "<name> (unavailable: <reason>)", tool tip the reason; control disabled with "Detecting encoders..." until the list arrives |
| Quality (D75) | `quality_level` | `QComboBox` | "High", "Standard", "Draft" | `"high"` / `"standard"` / `"draft"` | closed set | none |
| 10-bit for 8-bit (D76) | `ten_bit_for_eight_bit` | `QCheckBox` | checked state | `bool` | none | disabled with "<encoder> cannot write 10-bit video." when the selected (or resolved "auto") encoder's `bit_depths` lacks 10; "No video encoder is available." when "auto" resolves to nothing; stored True stays shown checked |
| Provenance (D91) | `provenance` | `QCheckBox` | state | `bool` | none | none |
| Cache limit (D71) | `cache_limit_bytes` | `QSpinBox` "GB" (1 .. 100000) | `round(bytes / 10**9)`, at least 1 | `gb * 10**9`, only when edited | range of the spin box | none |
| Clear cache (D71) | -- | `QPushButton` | "Clear cache", "Clearing..." while the job runs | -- | confirmation first | disabled "The cache cannot be cleared while a clip is being analysed." while `session.analysis().phase == "running"`; disabled while its own job runs |
| Force CPU (AD-9) | `force_cpu` | `QCheckBox` in an "Advanced" `QGroupBox` | state | `bool` | none | none |

First-run check (test 1): on `Settings()` the controls show 16-bit, "Automatic", Standard, 20 GB,
provenance on, force CPU off, suffix `_corrected`, "Same folder as the source", 10-bit off.

### Encoder list rule (Q3 as amended) and the 10-bit rule

- Items: "Automatic (NVENC when available)" (data `"auto"`) first, then one per
  `EncoderCapability` in the sink's order. `available` False -> item disabled (item flags
  without `ItemIsEnabled`, so keyboard and mouse cannot select it), text and tool tip as in the
  table.
- A stored encoder the sink does not report: an extra item "<name> (unavailable: not found on this
  computer)", disabled, current, written back unchanged unless the user picks another.
- "auto" is resolved ONLY through the injectable `resolve_encoder(setting, capabilities) -> str`
  (WP3.10's signature). Until WP3.10 merges, the module default is an interim stub of WP3.10's
  rule (`hevc_nvenc` when available, else `libx265` when available, else it raises); the dialog
  treats any exception as "unresolved". WP3.10's accept or WP4.3 swaps the one default argument.
  The dialog does not restate the rule beyond the stub.
- 10-bit: capability of the selected name; for "auto" of the resolved name; unresolved ->
  "No video encoder is available."; a selected name with no capability (stored, not found) ->
  "<name> cannot write 10-bit video." The checkbox is re-evaluated on every encoder change and
  when the capability list arrives.
- Capabilities (Q2): see STOP S1 for where the detection job starts.

### Accept sequence (OK) and failure paths

1. OK is disabled while the suffix is invalid, so accept is reached only with a valid suffix; accept
   re-runs `validate_suffix` anyway (defence) and, on failure, stays open.
2. `new = dataclasses.replace(session.settings(), <edited fields>)` (so `last_parameters` stays as
   the session holds it).
3. `session.settings_refusal()` is None: `save_settings(locations.config_dir, new)`.
   - success: `messages.clear(owner="settings")`.
   - `FormatError`, `ValueError`, `OSError`: present `Message("error", "The settings could not be
     saved to <file>: <error>", path=<file>, owner="settings")` (ASCII-safe); the session still
     gets `new`, and the close save retries.
4. `session.settings_refusal()` is not None (Q1): nothing is written; the file bytes are untouched.
5. `session.set_settings(new)` (the shell re-selects the backend; force CPU reads "CPU: forced").
6. `cache_limit_bytes` differs from the session's previous value: one job through `context.jobs`
   runs `engines.cache.set_limit_bytes(n)`; a failed `JobResult` -> error with owner `"settings"`
   ("The cache limit could not be set: <failure>").
7. The dialog closes. Cancel (reject): nothing changes.

The refusal text (Q1): the dialog shows at its top "Changes apply to this session only; <file> was
left unchanged." followed by the refusal's own text (file name from `refusal.path`, else
`settings.json`).

### Clear-cache sequence

Button click -> `choosers.confirm("Remove every cached proxy and statistic? ...")`; declined ->
nothing. Accepted -> button text "Clearing...", disabled; one job through `context.jobs` runs
`engines.cache.clear()` (worker thread); `on_done`: restore the button (unless analysis is
running), success -> status label "Cache cleared." only if the dialog is still open, failure ->
error with owner `"settings"`. The button is also disabled, with the reason as its tool tip and
status text, while `session.analysis().phase == "running"` and re-evaluated on `analysis_changed`
(connected for the dialog's life, disconnected at `finished`).

### Chooser seam

`SettingsChoosers` (Protocol): `choose_folder(initial: Path | None) -> Path | None`,
`confirm(text: str) -> bool`; `QtChoosers` is the default (`QFileDialog.getExistingDirectory`,
`QMessageBox.question`). Tests inject a recording fake; no test blocks on a modal.

### Test list (`tests/test_gui_settings_dialog.py`, all `gui`)

1. first run: every control equals G12's first-run default.
2. each G12 setting round-trips (parametrised: folder, suffix, PNG depth, encoder, quality,
   10-bit, provenance, cache GB, force CPU): `load_settings` and `session.settings()` carry it;
   `last_parameters` unchanged.
3. G13: a second `MainWindow` on the same `Locations` opens with the saved values.
4. D74: unavailable `hevc_nvenc` item disabled with reason (text and tool tip), not selectable by
   `setCurrentIndex` from the UI path (item flags); 10-bit disabled with reason for an 8-bit-only
   encoder, enabled for `libx265` 8/10; "auto" resolved through the injected resolver; unresolved
   auto; stored-unavailable encoder kept and written back unchanged.
5. DR-35: separator, `..`, trailing dot, the temporary marker, forbidden character each disable OK
   with the `ValueError` text; a valid suffix enables it; an empty suffix is valid.
6. AD-9: force CPU on -> `session.backend()` and the status bar read "CPU: forced".
7. refusal: unsupported `format_version` file at start-up -> OK applies to the session, file bytes
   unchanged, dialog shows the refusal text.
8. D71: clear cache after confirmation calls `clear()` once, on a non-interface thread; nothing on
   decline; disabled with the reason while analysis runs and enabled again when it ends;
   "Cache cleared." shown; failure -> `"settings"` error; limit change calls `set_limit_bytes(n)`
   in bytes on a non-interface thread; unchanged limit -> no call; a non-whole-GB stored limit is
   written back unchanged.
9. DR-44 (b): a `"shell.preview"` error survives a successful save; a `"settings"` error is
   cleared by it; a save failure (`config_dir` blocked by a file) presents a `"settings"` error
   naming the file and the session still gets the settings.
10. planted wrong implementations fail by name: save while refused; `last_parameters` dropped;
    `clear()` on the interface thread; an unavailable encoder selectable. (Each as a test that
    asserts the right behaviour and was first shown failing against a deliberately wrong variant.)
11. Cancel changes nothing (no save, no session change, no job).
12. dependency rule: `tests/test_gui_deps.py` run as is.

### Answers to the open questions

Q1 (OK while refused: session-only), Q3 (list and "auto" through WP3.10's one rule), Q4 (clear
disabled while analysing), Q5 (D75 names), Q6, Q7: as ruled. No other choice is taken silently;
the two below are STOPs.

### STOPs (choices the brief leaves open)

- **S1. Where the capability detection job starts.** Q2 (ruled) says `install_settings_dialog`
  starts the job. `install_settings_dialog(window: ShellWindow)` has no `ShellContext` at install
  time: the contract's `ShellWindow` has no `context` (only `MainWindow.context`, not a contract
  name), and the factory receives the context only when Tools > Settings is triggered.
  Recommended: the catalog (cached tuple, a `Signal`) is created in `install_settings_dialog`
  but its one job (`engines.video_sink.capabilities()` through `context.jobs`) starts at the FIRST
  factory call; the encoder control shows "Detecting encoders..." (disabled) until it arrives, then
  is cached for the session (a failure leaves only "Automatic" with the failure as the reason).
  Alternatives: read `window.context` by `getattr` (not a contract name; rejected), or add
  `context` to the contract (a contract change; STOP territory). No first-open latency for the
  stub; for WP3.10's sink, a one-off "Detecting encoders..." on the first open only.
- **S2. Signature additions.** `install_settings_dialog(window, *, choosers=None,
  resolve_encoder=None)` and `settings_dialog(context, *, choosers=None, resolve_encoder=None,
  catalog=None)` take keyword-only injection arguments (the brief names the chooser seam; the
  resolver seam is the ruling's "injectable seam"). Recommended: yes, keyword-only, defaults are
  the Qt choosers and the interim resolver stub. Say no and tests would have to monkeypatch module
  attributes.

Open reading, not a stop: `save_settings` writes `last_parameters` as the session holds it (the
start-up value), not the live parameters (the shell writes those at close); a crash after a
dialog save therefore leaves the start-up value, as before. Also one owner key `"settings"` means a
successful save clears an earlier cache-clear failure banner too.

### Gates and depth

No code, no tests run this round (host hold). `uv sync` done. Depth reading: not
self-readable (`scripts/cell_depth.py` reads my transcript); dispatcher fills: ____

## Cumulative round ledger

| Round | Critical | Major | Minor | In envelope | Out | NEW | REOPENED | Reverts | Fixes (product / test-only) | Transport | Depth | Adjudication |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | 101,295 (dispatcher) | read and table only |
| 1 | 0 | 0 | 1 | 1 in / 0 out | -- | 1 NEW | 0 | 0 | none yet (cleanup pending: product + test) | codex-cli 0.162.1 via WSL, gpt-5.6-sol high, read-only; head `8f54e53` | 187,529 (dispatcher) | `NO_NEW_CRITICAL_MAJOR`; converged |

### Round 1 detail (Reviewer A, head `8f54e53`)

Evidence: `C:\Users\rwsmy\clearwater-review-evidence\wp3.20\r1\` (prompt, diff, transcript,
`adjudication.md`, `md5sums.txt`, `test-summary.txt`: 60 passed). Mechanical assertions all met
(model and effort match the tier; tokens footer; 19 `succeeded in`; no ERROR; VERDICT anchored).

Before the round: the first run of the new tests showed one test-code error (`itemToolTip` does
not exist on `QComboBox`) and one product defect (`resolve_encoder` was called with an empty
capability list while the list was still being read); both fixed in `8f54e53` (product + test).
The four planted-wrong tests pass only because the wrong dialog raises `AssertionError` in the
scenario.

| # | Severity | Tag | In envelope | NEW/REOPENED | Finding | Adjudication |
|---|---|---|---|---|---|---|
| 1 | MINOR | REASONED | yes | NEW | `settings_dialog.py:452`: after a failed capability read with a stored non-auto encoder, the stored encoder is appended as a second item reasoned "not found on this computer" (wrong cause); the failed-detection test uses `auto` only | ACCEPTED, non-blocking: terminating cleanup shows the failure as that item's reason and the test is seeded with a stored encoder |

Gate status: zero NEW blocking findings, so Reviewer A has converged at round 1. Pending: the
terminating cleanup for finding 1 (product and test), then the full pytest window.

### Terminating cleanup (CHARC ruling: round 1 upheld, no round 2)

Finding 1 fixed in `a6ae225`: with a failed capability read the stored encoder stays a disabled
item (Q3) and its reason is the detection failure. New test
`test_a_failed_detection_gives_a_stored_encoder_the_failure_as_its_reason` fails on `8f54e53`
(shown) and passes after; 61 passed with `tests/test_gui_deps.py`; ruff, format and mypy green.
Report `docs/reports/wp3.20-settings.md` written. Next: full pytest window.

### Reviewer B remediation (orchestrator's seat, candidate `wp3.20-mc` `bbf44e2`; depth 204,057)

One remediation on branch `wp3.20`, one commit per item (no Reviewer A round; B re-runs):

| Item | Severity | Commit | Test (fails on `a6ae225`) |
|---|---|---|---|
| Clear cache re-checks `_analysing()` (and `_closed`) after `confirm()` returns | MAJOR | `d5808a9` | `test_an_analysis_that_starts_while_the_confirmation_is_open_blocks_the_clear` |
| Shown cache GB clamped in integer arithmetic (no float overflow) | MINOR | `d454b06` | `test_a_huge_stored_limit_opens_clamped_and_is_written_back_unchanged` (10**400) |
| Report and test-docstring wording (gui marker, counts) | MINOR | `34075f2` | -- |
| `itemToolTip` test defect added to the pre-review defect record | ADVISORY | `34075f2` | -- |

Results (20:21Z, 11.6 GB free, foreground, `QT_QPA_PLATFORM=offscreen`):

- Before: an extracted `git archive a6ae225` copy with the new test file copied in, run with that
  tree's `src` first on `PYTHONPATH` (module path confirmed under `work/old/src`): the two new
  tests FAIL (`OverflowError: integer division result too large for a float` for the huge limit;
  an `AssertionError` for the confirmation test, the cache was cleared). The whole module on that
  copy: 2 failed, 57 passed, 1 error (the error is the teardown of the overflowing window).
- After, on head `34075f2`: `tests/test_gui_settings_dialog.py` plus `tests/test_gui_deps.py`:
  63 passed (59 module cases, 4 deps tests). ruff check, ruff format --check, mypy strict (118
  files) green.
