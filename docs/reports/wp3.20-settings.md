# WP3.20 report: the settings dialog

Package WP3.20 (plan section 6, Phase 3; spec G12, G13, D22, D26, D34, D36, D71, D74, D75, D76,
D89, D91, AD-9). Cell: implementer, seat 1. Files: `src/clearwater/gui/settings_dialog.py`,
`tests/test_gui_settings_dialog.py`, this report, `docs/proofs/wp3.20-ledger.md`. Nothing else
changed: no existing file of `clearwater.gui`, `clearwater.config`, `clearwater.interfaces`,
`pyproject.toml` or `uv.lock`.

## Public API (what WP4.3 and WP3.14 consume)

- `install_settings_dialog(window, *, choosers=None, resolve_encoder=None) -> None`: registers
  the factory with `ShellWindow.set_settings_dialog`; WP4.3 calls it once. It creates the
  session's `EncoderCatalog`, shared by every dialog the factory builds.
- `settings_dialog(context, *, choosers=None, resolve_encoder=None, catalog=None) ->
  SettingsDialog`: a new dialog per trigger, initialised from `session.settings()`.
- `SettingsChoosers` (protocol: `choose_folder(initial) -> Path | None`, `confirm(text) -> bool`)
  and `QtChoosers`, the Qt default (`QFileDialog.getExistingDirectory`, `QMessageBox.question`).
- `EncoderResolver` (type), `interim_resolve_encoder`, `EncoderCatalog`, `SettingsDialog`, and the
  constants `OWNER_SETTINGS = "settings"`, `AUTO`, `GB`, `MIN_CACHE_GB`, `MAX_CACHE_GB` and the
  user-facing texts.

## Controls (G12 order)

| G12 setting | `Settings` field | Widget | Stored form |
|---|---|---|---|
| Output folder (D34) | `output_folder` | label with "Choose..." and "Use source folder" | `None` ("Same folder as the source") or `Path` |
| Output suffix (D36) | `output_suffix` | line edit, `validate_suffix` on every edit, error beside the field, OK disabled | the text |
| PNG bit depth (D22) | `png_bit_depth` | combo "16-bit", "8-bit" | `16` / `8` |
| Video encoder (D26, D74) | `video_encoder` | combo: "Automatic (NVENC when available)", then the sink's capabilities in order | `"auto"` or the capability name |
| Quality (D75) | `quality_level` | combo "High", "Standard", "Draft" | `"high"`, `"standard"`, `"draft"` |
| 10-bit for 8-bit (D76) | `ten_bit_for_eight_bit` | check box | `bool` |
| Provenance (D91) | `provenance` | check box | `bool` |
| Cache limit (D71) | `cache_limit_bytes` | spin box in whole GB, 1 to 100000 (1 GB = 10**9 bytes) | `gb * 10**9`, only when edited |
| Clear cache (D71) | -- | button | -- |
| Force CPU (AD-9) | `force_cpu` | check box in an "Advanced" group | `bool` |

A control still at the value it first displayed never overwrites its field; the new settings are
`dataclasses.replace(session.settings(), <edited fields>)`.

## Encoder and 10-bit rules

- An unavailable capability is a disabled item, "<name> (unavailable: <reason>)", the reason also
  its tool tip; an unavailable encoder cannot be accepted (OK is disabled if one is selected by
  any route and was not the stored value).
- A stored encoder the sink does not report stays as a disabled, selected item and is written back
  unchanged unless the user picks another; its reason is "not found on this computer", or the
  detection failure when the report could not be read.
- "auto" is resolved only through `resolve_encoder(setting, capabilities)`; the dialog needs the
  result only for the 10-bit rule. 10-bit is disabled with "<encoder> cannot write 10-bit video."
  when the (resolved) encoder's `bit_depths` lacks 10, with "No video encoder is available." when
  "auto" resolves to nothing, and with "Detecting encoders..." until the report arrives. A stored
  True stays shown and is written back.

## Accept sequence

Validate the suffix; build the new settings; when `session.settings_refusal()` is None save with
`save_settings(locations.config_dir, new)` (a `FormatError`, `ValueError` or `OSError` is an
error with owner `"settings"` naming the file, a success clears that owner's errors); when it is
not None write nothing; `session.set_settings(new)`; when the cache limit changed run
`engines.cache.set_limit_bytes(n)` in a job (a failure is an error with owner `"settings"`).
Cancel changes nothing. The refusal text at the top of the dialog reads "Changes apply to this
session only; <file> was left unchanged." and the refusal's own text.

## Claims and evidence

Tests are in `tests/test_gui_settings_dialog.py` (43 test functions; parametrised ones collect to
more cases), headless, folders under `tmp_path`, injected choosers. The module carries the `gui`
marker on every test through its `pytestmark`; one of them, `test_interim_rule_matches_the_wp310_rule`,
calls the function directly and creates no Qt object. `tests/test_gui_deps.py` (4 tests, run
unchanged) is not `gui`-marked and creates no Qt object.

| Claim | Evidence (test) |
|---|---|
| Every control shows G12's first-run default | `test_first_run_shows_g12_defaults`, `test_quality_names_and_stored_forms` |
| Each setting is edited, saved and applied; `last_parameters` unchanged | `test_each_setting_round_trips` (nine cases) |
| Settings persist across sessions (G13) | `test_second_window_opens_with_the_saved_values` |
| Cancel changes nothing | `test_cancel_changes_nothing`, `test_use_source_folder_and_cancelled_chooser` |
| Unavailable encoders are disabled with their reason and cannot be accepted | `test_unavailable_encoder_is_disabled_with_its_reason`, `test_an_unavailable_encoder_cannot_be_accepted` |
| Capabilities are read once, off the interface thread; a failure leaves only "Automatic" | `test_encoder_list_waits_for_the_sink_and_is_read_once`, `test_a_failed_detection_leaves_only_automatic`, `test_a_failed_detection_gives_a_stored_encoder_the_failure_as_its_reason` |
| A stored unreported encoder is kept | `test_a_stored_encoder_this_computer_does_not_report_is_kept` |
| 10-bit rule and a stored True | `test_ten_bit_follows_the_encoder_and_keeps_a_stored_true`, `test_ten_bit_is_enabled_for_an_encoder_with_10`, `test_auto_is_resolved_by_the_injected_rule` |
| The interim rule has WP3.10's behaviour | `test_interim_rule_matches_the_wp310_rule` |
| DR-35: an invalid suffix disables OK with the error text | `test_an_invalid_suffix_disables_ok_with_the_error_text` (nine suffixes), `test_an_empty_suffix_is_valid`, `test_a_stored_invalid_suffix_disables_ok_until_fixed` |
| AD-9: force CPU shows "CPU: forced" | `test_force_cpu_shows_cpu_forced_in_the_status_bar` |
| A refused settings file is never written, the session still gets the settings | `test_ok_while_the_file_is_refused_is_session_only` (bytes compared before OK, after OK and after close) |
| D71: clear after confirmation, off the interface thread; the analysis guard is checked twice: the button is disabled and the click ignored while the phase is "running", and the phase is checked again after the confirmation returns (the box runs a nested event loop), so an analysis that starts while it is open blocks the clear | `test_clear_cache_runs_off_the_interface_thread_after_a_confirmation`, `test_declined_confirmation_clears_nothing`, `test_clear_cache_is_disabled_while_a_clip_is_analysed`, `test_clear_cache_disabled_from_the_start_when_analysis_is_running`, `test_an_analysis_that_starts_while_the_confirmation_is_open_blocks_the_clear` |
| Cache failures and a result after close | `test_clear_cache_failure_is_a_settings_error`, `test_clear_cache_result_after_the_dialog_closed_is_safe`, `test_a_limit_failure_is_a_settings_error` |
| Limit in bytes, off the interface thread, not called when unchanged; odd stored limits kept | `test_a_limit_change_sets_the_limit_in_bytes_off_the_interface_thread`, `test_an_unchanged_limit_calls_nothing_and_a_stored_odd_limit_is_kept`, `test_cache_spin_has_a_minimum_of_one_gb` |
| DR-44 (b): owners | `test_a_save_clears_only_the_settings_errors`, `test_a_failed_save_names_the_file_and_the_session_still_gets_the_settings`, `test_every_message_of_the_dialog_is_ascii` |
| Planted wrong implementations are caught by name | `test_planted_save_while_refused_is_caught`, `test_planted_dropped_last_parameters_is_caught`, `test_planted_clear_on_the_interface_thread_is_caught`, `test_planted_selectable_unavailable_encoder_is_caught` (each also has a test that the same scenario passes on the real dialog) |
| Dependency and `QSettings` rules | `tests/test_gui_deps.py`, run unchanged, covers the new module |

Defects found by the first run of the tests, before the review (both fixed in `8f54e53`): a test
used `QComboBox.itemToolTip`, which does not exist (test code; the tool tip is read with
`itemData(i, ToolTipRole)`), and `resolve_encoder` was called with an empty capability list while
the list was being read (product code).

## Gates

Static gates on the final head: `uv run ruff check .`, `uv run ruff format --check .`,
`uv run mypy` (strict, 118 files): green. Targeted tests on the final head:
`tests/test_gui_settings_dialog.py` and `tests/test_gui_deps.py`: the counts are in the ledger. Full pytest: run by the
orchestrator on the merge candidate (stacked gate). Reviewer A (STRONG, `gpt-5.6-sol` high, codex-cli
0.162.1 over WSL): one round, no critical or major finding, one minor (a stored encoder after a
failed detection carried the wrong reason), fixed in the terminating cleanup; ledger
`docs/proofs/wp3.20-ledger.md`, evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.20\r1\`.

## Limits

- **Encoder detection starts at the first open, not at install.** The contract's `ShellWindow`
  carries no context, so `install_settings_dialog` cannot start the job; the first dialog that
  opens does, and shows "Detecting encoders..." until the report arrives; the result is cached
  for the session. Detection at start-up is WP4.3's. A failed detection is cached too (no retry
  in the session).
- **The "auto" rule is a stand-in.** `interim_resolve_encoder` has WP3.10's `resolve_encoder`
  signature and rule (`hevc_nvenc` when available, else `libx265`, else it raises). It is removed
  when WP3.10 is on main; the real function becomes the default of the `resolve_encoder`
  parameters. With the generic stub sink (one encoder named `"stub"`) "auto" resolves to nothing,
  so 10-bit is disabled with "No video encoder is available.".
- **`last_parameters` is written as the session holds it.** A dialog save writes the value from
  start-up (`session.settings().last_parameters`), not the live parameters; the shell writes the
  live ones once at close. A crash after a dialog save leaves the start-up value, as before.
- **One owner key `"settings"`.** A successful save clears every earlier `"settings"` error,
  including a cache-clear or cache-limit failure that is still true.
- A cache-limit job that fails leaves the new limit in the settings (no retry); the change is
  detected against the session's previous settings, not `cache.limit_bytes()`.
- `save_settings` runs on the interface thread (a small atomic write; out of envelope: a settings
  folder on a slow network share).
- The suffix check is `validate_suffix` only; a reserved device name formed with the stem (DR-35
  (a)) is WP3.14's.
- The cache spin box tops out at 100000 GB; a stored limit above that is shown clamped and written
  back unchanged unless edited.
- Spec 8.2's example quality names (Standard / High / Very High) differ from D75's; D75 governs
  (ruling Q5); noted for the next spec revision.

## Consumer notes

- **WP3.14 (export):** resolve the encoder setting `"auto"` with WP3.10's `resolve_encoder`, the
  one rule; the dialog calls the same function for its 10-bit check, so the dialog and the export
  agree. Provenance records the resolved name. `output_folder` is not validated for writability
  here (`MissingFolderError` is yours).
- **WP4.3:** call `install_settings_dialog(window)` after the shell is built; create the real
  `DiskProxyCache` with `Settings.cache_limit_bytes`, because the dialog calls `set_limit_bytes`
  only when the limit changes. When WP3.10 merges, replace `interim_resolve_encoder` as the
  default in `settings_dialog.py` with `clearwater.io.video.capability.resolve_encoder` (or pass
  it as `resolve_encoder=`) and delete the stand-in and `test_interim_rule_matches_the_wp310_rule`.
  Detection at start-up needs `install_settings_dialog` to accept a catalog; it does not
  today (a small addition for WP4.3).
- **WP3.18 (analysis):** the dialog disables Clear cache while `Session.analysis().phase ==
  "running"`; keep setting the phase through `Session.set_analysis`.
