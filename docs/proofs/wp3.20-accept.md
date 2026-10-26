# WP3.20 accept record (orchestrator generation 12, 2026-10-26)

**Package:** WP3.20 settings dialog (`clearwater.gui.settings_dialog`: `install_settings_dialog`, `settings_dialog`,
`SettingsDialog`, `EncoderCatalog`, `CacheLimiter`, `interim_resolve_encoder`), brief `docs/briefs/wp3.20-brief.md`
(FINAL; its Rulings govern; STOPs S1 detection at the first open, S2 keyword-only injection). One seat (implementer,
Sonnet 5.5, seat 1, STRONG): round 0 (101,295), R1 (187,529), Reviewer B pass-1 remediation (204,057), pass-2
remediation (218,410), each dispatcher-read.

**Candidate:** author branch `wp3.20` (`1e0aae8`, base `718324b`, 13 commits); merge candidate `wp3.20-mc` (`e47c8d2`,
base `7fff7be`, 13 commits). Gate: stacked branch `stackB` = main `ccaecd7` + WP3.17 + WP3.19 + WP3.20 + WP3.18
(cherry-picked ranges, file sets disjoint; head `d71d994` at drafting); every owned file byte-identical in `stackB`,
`wp3.20-mc` and `wp3.20` (`git diff`, 0 lines). Merged: one `git merge --ff-only` of `stackB-acc` onto main; this record's own commit follows the package's last commit.

**Footprint (checked at this seat):** owned files only: `src/clearwater/gui/settings_dialog.py`,
`tests/test_gui_settings_dialog.py`, the report `docs/reports/wp3.20-settings.md`, the ledger. `interfaces/`,
`gui/__init__.py`, `contract.py`, `config/`, `pyproject.toml`, `uv.lock` untouched; 0 CR bytes in every owned blob.

**Results:** every G12 setting in order, round-tripped and persisted (G13); a control still at its first value never
overwrites its field; unavailable encoders disabled with their reason (D74); 10-bit rule (D76); DR-35 suffix check
disables OK; AD-9 "CPU: forced"; a refused settings file is never written (session only); D71 clear cache after a
confirmation, off the interface thread, guarded before and after the confirmation; cache-limit calls serialised by
`CacheLimiter` (the last accepted limit wins). Targeted: 64 passed (60 module cases, 4 deps tests), twice.

## Nets

| Net | Result |
|---|---|
| Reviewer A (cell, STRONG, WSL codex-cli 0.162.1 / gpt-5.6-sol high, read-only) | R1 0/0/1 NO_NEW_CRITICAL_MAJOR (converged; a stored encoder after a failed detection carried the wrong reason), CHARC ruling: R1 upheld, no R2; cleanup `a6ae225` (test fails on `8f54e53`), 61 passed. 19 "succeeded in"; evidence `clearwater-review-evidence\wp3.20\r1` |
| Reviewer B pass 1 (this seat, `bbf44e2`, kept as branch `wp3.20-mc1`) | NEW_CRITICAL_MAJOR_FOUND; banner gpt-5.6-sol / high, read-only; 0 `^ERROR`; 18 "succeeded in" (20 by a raw grep, 2 are prompt echoes); 159,950 tokens. #1 MAJOR (clear-cache check before the modal confirmation only), #2, #3 MINOR, #4 ADVISORY -> `d5808a9`, `d454b06`, `34075f2`; on `a6ae225` 2 failed / 57 passed / 1 error, 63 passed on the head. md5 `review-B.txt` 24d1bd31aef5... (`reviewB\md5sums.txt`) |
| Reviewer B pass 2 (this seat, `78a5a8e`, kept as branch `wp3.20-mc2`) | NEW_CRITICAL_MAJOR_FOUND; banner gpt-5.6-sol / high, read-only; 0 `^ERROR`; 19 "succeeded in" (21 by a raw grep, 2 are prompt echoes); 147,508 tokens. 1 MAJOR (pre-existing: independent cache-limit jobs, a delayed earlier job wins). SECOND BLOCKING PASS, ADJUDICATED AT THE GATE (generation 11), CHARC UPHELD (msg d329e80e351c3dcc): `CacheLimiter` fix `06f5937` + test; VERIFIED BY EXECUTION at the orchestrator's seat: failed on `34075f2` (cache ended at 5 GB, not 7), 64 passed on the candidate. md5 `review-B.txt` 2d5251a5847b... (`reviewB2\md5sums.txt`) |
| Candidate full pytest (this seat, stack top `d71d994` = main `ccaecd7` + WP3.17 + WP3.19 + WP3.20 + WP3.18) | 4501 passed, 2 skipped, 1579 s, exit 0 (CuPy as installed, offscreen, one background process; log `.worktrees/stackB/work/g12-full.log`). This is also main's figure by code identity: main after the merge differs from `d71d994` in the four accept records only |
| Harness gate | 366 OK (1 skipped) on `d71d994`; ruff clean, 217 formatted, mypy 126 clean; CR check 0 on every changed blob |

**Debt:** no DR row named by the ledger or report; DR-35 (a) (reserved device name with the stem) is WP3.14's. The
interim `resolve_encoder` stub (`interim_resolve_encoder`) stays until WP4.3 swaps in WP3.10's (ruled at the gate);
row by CHARC at QA if it is to be tracked. Other limits in the report (detection at first open, failed detection cached
for the session; one owner key `"settings"`; `last_parameters` written as the session holds it).

**Consumer notes:** WP4.3 calls `install_settings_dialog(window)` after the shell is built, creates the real
`DiskProxyCache` with `Settings.cache_limit_bytes` (the dialog calls `set_limit_bytes` only on a change), replaces
`interim_resolve_encoder` with `clearwater.io.video.capability.resolve_encoder` and deletes the stand-in and
`test_interim_rule_matches_the_wp310_rule`; detection at start-up needs a catalog argument (small addition). WP3.14
resolves `"auto"` with WP3.10's `resolve_encoder` (the same rule the dialog uses). WP3.18 keeps setting the phase
through `Session.set_analysis` (Clear cache is disabled while "running").
