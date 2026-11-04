# WP-T8 — Tools and tests paydown: DR-119 (c)-(e), DR-120, DR-118, DR-116 (dispatch brief, FINAL)

**Status:** FINAL 2026-11-04 ~08:40Z by CHARC (generation 14) on gen 40's dispatch fill `7a8f5135` with its two corrections nodded (one Codex cell at a time: WP6.2 first, WP-T8 after WP6.2 yields for its nets; WP-T8's gate legs and WP6.1's build / timing windows never overlap, sequenced by the orchestrator). Earlier: DRAFT 2026-11-04 by CHARC (generation 14), the Phase 6 paydown pass the register deferred to Phase 6. The orchestrator fills the dispatch section; CHARC marks it FINAL. Runs beside WP6.1's non-timing turns and WP6.2; never beside WP6.1's exclusive window. Owner decisions inside the package: none.

| Field | Content |
|---|---|
| ID and title | WP-T8 — Tools and tests paydown: the four register rows deferred to Phase 6 that touch only tools, tests and one cache-folder guard |
| Lane | **CODEX** (`implementer-codex-sol-high`): every item is specified by its register row. Reviewer A = Claude at the cell's seat; Reviewer B = Claude at the orchestrator's seat. Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp-t8\`. |
| Tier and size | STANDARD. Size S. Evaluate at about 200K, STOP near 250K; the DR-116 measurement turn re-seats fresh if needed. |
| Base | main at dispatch. Worktree `.worktrees/wp-t8`, branch `wp-t8`. |
| Goal | (a) **DR-119 (c)-(e):** `tools/export_bench.py` writes its JSON to a temp name and renames (no torn file on interrupt); `tools/halo_part3.py` stages its V3 output folder like the sheet, refuses `--cache-dir` inside `<out>/items`, and `build_sheet`'s docstring names `sheet-<stamp>/sheet.json`; `tools/core_speed.py` and `tests/test_core_speed.py` read the N6 figure (12 min/min, 0.4004 s per frame at 29.97 fps) from ONE constant shared with `export_bench.py` (a new `tools/n6.py` or the existing module both import; D106 / spec v0.5.8 named in its docstring), one test. (b) **DR-120:** `tests/fixture_plugin.py`'s generated-sample cache resolves under `--basetemp` when one is given (a gate leg is then contained by its basetemp), else under the MAIN checkout's `work/fixtures/generated` as today; one test. (c) **DR-118:** `cache/store.py` `_entry_for_write` refuses to create or write through a pre-existing junction / symlink at the entry path, with the same refusal the scan applies (`is_symlink() or is_junction()`), one test with a planted junction (skipped where the test cannot create one). (d) **DR-116:** the suite-cost pass: a per-node wall delta of the serial leg against WP-T6's run (`docs/reports/wp-t6-gate-sizing.md` figures) from the gate junits already archived (no new serial run needed for the table), DR-86's banked candidates listed with their measured cost; apply only the no-risk reductions the report names (a fixture reused, a redundant parameterisation dropped) and leave the rest as a recommendation. |
| Sources | `docs/debt-register.md` rows DR-116, DR-118, DR-119, DR-120, DR-86; `tools/export_bench.py`, `tools/halo_part3.py`, `tools/core_speed.py`, `tests/test_core_speed.py`, `tests/test_export_bench.py`, `tests/test_tools_halo_part3.py`, `tests/fixture_plugin.py`, `tests/conftest.py` (WP-T1 guard), `src/clearwater/cache/store.py` (:573, :652-672), the archived serial junits under `clearwater-review-evidence\` (the WP-T6 run and `release-1.0.0\g40-p55-serial.xml`). |
| Files owned | The files named in Goal plus NEW `tools/n6.py` (if chosen) and the tests named; `docs/reports/wp-t8-paydown.md`. |
| NOT owned | Any other product file (the DR-118 change is the one product edit, in one function); the spec; frozen interfaces; `tests/harness/`. |
| Locks | No figure of record changes (the N6 constant is a label, the figures are unchanged); the cache store's on-disk format is unchanged; the fixture cache's content is unchanged (only its location rule); 0 CR blobs; ruff / mypy; the three gate legs on the final candidate (the store and the fixture plugin are on every leg's path). |
| Markers | New tests parallel-leg unless they need footage or the GPU (none should). The junction test is `slow`-free and skips with a reason when a junction cannot be created. |
| Hardware flags | None (DR-116's table is from archived junits). |
| Out of scope | A new serial-leg run for DR-116 (the report may recommend one); any product behaviour beyond the DR-118 refusal; the harness suite. |
| Debt and decided items | At the accept CHARC closes DR-119 in full, DR-120, DR-118; DR-116 closed or re-scoped on the report's recommendation; DR-86 updated. |
| Done | Every item in Goal with its test; the paydown report with the DR-116 table and recommendation; ruff / mypy / the three legs green; Reviewer A converged; Reviewer B clean. |

## Questions (CHARC's recommended answers)

- **Q1 The shared N6 constant's home.** Recommended: a new `tools/n6.py` (`N6_MIN_PER_MIN = 12.0`, `FRAME_BUDGET_S_29_97 = 12.0 / 29.97`, the docstring naming D106 / spec v0.5.8 and the owner's ruling date); `export_bench.py` and `core_speed.py` import it; the tests assert the figures against the spec text by a grep of `docs/underwater-correction-spec.md` N6's line.
- **Q2 DR-120's rule.** Recommended: basetemp when given (the gate), else the main checkout's `work/` (a developer run); the worktree's own `work/` is never used.
- **Q3 DR-118's refusal.** Recommended: refuse (raise the store's existing error class, logged) rather than delete the junction; the entry is then skipped for the write, the export continues uncached, exactly as the scan's refusal behaves.

## Completion report (`docs/reports/wp-t8-paydown.md`)

Each item: the change, the test, the register row it pays; the DR-116 table and recommendation; gate figures; limits.

## Yields and depth

Turn 1 = round 0 (read every row and site; the DR-116 junit inventory; Q1-Q3) and YIELD; turn 2 = (a)-(c) RED then GREEN; turn 3 = (d) the table and report; the nets.

## Orchestrator dispatch fill (for CHARC to finalise)

- Lane paces at dispatch; base commit; worktree; evidence folder.
- GATE_CHECKS: static; collection identity; the three legs (the store and the fixture plugin are on every path); `git diff --name-only main` = the owned paths; 0 CR.

## Dispatch fill (orchestrator gen 40, 2026-11-04 ~08:25Z)

This section fills the one above. Where it differs, it governs once CHARC marks it FINAL. Corrections are marked **[corr]**.

- **Base, worktree and evidence.**
  - Base = main at dispatch.
  - Worktree `.worktrees/wp-t8`, branch `wp-t8`, with `clearwater.local.toml` copied in. The gate legs need the footage guard and FFmpeg.
  - Evidence: `C:\Users\rwsmy\clearwater-review-evidence\wp-t8\` (`cell\`, `A\`, `B\`, `gate\`).
- **Lane paces at 08:17Z.** Codex 23 % / 0.233 (resets 10:07Z); Claude 22 % / 0.799.
  - CODEX lane as briefed, a FRESH session.
  - Reviewer A and Reviewer B = Claude passes at my seat.
- **[corr] Scheduling.**
  - **One Codex cell at a time:** WP-T8 starts when WP6.2 has yielded for its nets, not beside it.
  - **One heavy job at a time:** WP-T8's three gate legs (about 70 minutes, the serial leg EXCLUSIVE) never overlap a WP6.1 build or timing window, and vice versa. I sequence them.
  - The DR-116 table is from archived junits, so it is not heavy.
- **Sources verified at the seat (08:20Z).**
  - `cache/store.py`: the scan's refusal is at `:573` (`item.is_symlink() or item.is_junction() or not item.is_dir(follow_symlinks=False)`); `_entry_for_write` is at `:652`.
  - `tools/export_bench.py` already carries `D106_MIN_PER_MIN = 12.0` (WP5.5 paid DR-119 (a)). Q1's shared constant replaces it with an import and does not duplicate it.
  - **Archived serial junits for DR-116:**
    - `clearwater-review-evidence\release-1.0.0\g40-p55-serial.xml` (the 1.0.0 gate of record);
    - `wp-dr25\gate\g38-pdr25-serial.xml`, `wp-dr113\gate\g35-dr113-serial.xml`, `wp-d112\gate\g34-d112-serial.xml`, `wp-t7\gate\g31-t7-serial.xml`, `wp-d54\gate\g30-wpd54-serial2.xml`;
    - WP-T6's run under `wp-t6\work-copy\` (`wp-t6\gate-g1\serial.xml`, `mc\serial.xml`, `w3\...`).
  - Round 0 names which WP-T6 file matches `docs/reports/wp-t6-gate-sizing.md`'s 1,389 s figure of record, and uses it as the baseline.
- **The DR-118 edit is the one product change.** It goes in `_entry_for_write` only. The store's on-disk format is unchanged, and so is its behaviour without a junction (the 1.0.0 cache tests stay green). Any wider change = STOP.
- **Turns.**
  - Turn 1 = round 0, read-only: every row and site; the junit inventory; Q1-Q3. YIELD.
  - Turn 2 = (a)-(c) RED then GREEN. I commit.
  - Turn 3 = (d) the table and the report. YIELD for Reviewer A.
  - Depth: evaluate at about 200K, STOP near 250K. The DR-116 turn re-seats fresh if needed.
- **GATE_CHECKS** (my seat, after Reviewer B, alone on the machine):
  - `df -h /c` (25 GB floor);
  - static (ruff, format, mypy);
  - collection identity;
  - parallel, serial and fullclip legs, one at a time with the stall watch;
  - the harness suite only if a harness file changes (it must not);
  - `git diff --name-only main...wp-t8` = the owned paths;
  - 0 CR.
  - The fullclip leg is included because `tests/fixture_plugin.py` and `cache/store.py` sit on every leg's path, and the brief says "the three legs".
- **CHARC at FINAL (gen 14, 2026-11-04 ~08:40Z; gen 40's `0d673aea`).** Both corrections NODDED: the brief's "beside" wording yields to CLAUDE.md's one-Codex-cell rule and to the hardware rule (no heavy job beside WP6.1's exclusive window). The fill's site and junit facts stand; the audit counts platform conditionals and platform assumptions as two classes. Everything else in the fill governs as written.
- **CHARC ruling at round 0 (gen 14, 2026-11-04 ~10:30Z; gen 41's `aa8a8aa2`; Codex return-1).** (1) **Q3 premise corrected, RULED as recommended:** the store has no custom error class and the scan's refusal is a silent skip, so the brief's "continues uncached" cannot hold inside one function. `_entry_for_write` logs a WARNING naming the path and raises `OSError` when the entry path is a pre-existing junction or symlink, leaving the junction and its target untouched; the job then fails with a readable message. A planted junction inside the cache folder is abnormal; refusing to write through it is DR-118's point. The in-memory fallback alternative is DECLINED (a product behaviour change across analysis and export, outside the lock). DR-118's register row records the failure mode at the accept. (2) **GRANTED, test additions only:** `tests/test_cache_store.py` (the DR-118 junction test, with its explicit skip and reason where a junction cannot be created) and `tests/test_fixtures.py` (DR-120's basetemp / main-checkout rule). (3) Noted: the N6 figure read from the spec's N6 line; `core_speed.py` / its test lose the stale 25 / 0.834 by the shared constant (a label, not a figure of record; DR-119 (e)); the prototype budgets untouched and disclosed; Q2 via `tmp_path_factory.getbasetemp()` else the main checkout through git's common dir; the DR-116 baseline and 1.0.0 junits as named. Turn 2 released.
