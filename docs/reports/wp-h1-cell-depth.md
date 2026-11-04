# WP-H1: cell_depth selectors completion report

Candidate: build `b4e6a19e`, Reviewer A r1 fixes `6bd5fb99`, and the uncommitted
Reviewer A r2 tidy reported here. Date: 2026-11-04. Reviewer B: PENDING (orchestrator's seat).
The package changes the harness reader, its tests, and one dispatch-recipe paragraph.
It changes no product file, dependency, transcript, or frozen depth interface.

## Port and preserved behavior

Read-only sources were swing's `scripts/cell_depth.py` and
`tests/scripts/test_cell_depth.py`, with these commits:

| Swing commit | Ported behavior | Clearwater destination |
| --- | --- | --- |
| `b09bbc02` | Selector base, including named-agent reads and own-transcript mtime selection | `find_agents`, `_build_parser`, and selection in `main`; session scanning from `scan(sessions=)` becomes `discover_sessions` |
| `d4986324` | R-3 retention of old cells under fresh parents; parked flags | `session_transcript_path`, `session_transcript_age_hours`, `select_live`, and row flags in `main` |
| `4e412db9` | One guarded parent `stat`, avoiding the existence-check/stat race | `_transcript_age_hours` and `session_transcript_age_hours`; disappearance is harmless, other failures remain incomplete |

Function-by-function integration:

- `scan(sessions=)` maps to a separate `discover_sessions`. It uses the existing
  `_scan_dir_entries`/`os.scandir` discipline, `BadSession` validation, and strict or
  accumulating `DiscoveryError` handling. It reads only project-level main JSONL
  files; `--session` selects the corresponding exact session id in this mode.
- `find_agents` reuses discovered named and anonymous cells. CHARC's later exact-match
  ruling supersedes swing's prefix glob: parsed name/hash equals ID, or the stem
  equals `agent-a<ID>`. Repeated IDs do not duplicate rows. Reusing a name within one
  session prints one NOTE per ID/session, preserving selection and exit status.
- `session_transcript_path` derives the parent from the cell's own path. It cannot
  cross into another project. Parent age uses one guarded stat; a missing parent
  excludes an old cell without crashing, while permission errors remain visible.
- `select_live` keeps own age <= H, or an older cell with parent age <= H as `parked`.
  Session mode tests only its own mtime. Future mtimes clamp to zero. Selection occurs
  before transcript reading; age/stat/discovery failures cannot become a clean empty window.
- `_build_parser` groups `--all` (default), `--live`, and repeatable `--agent` mutually
  exclusively. `--sessions` composes with all/live; agent plus sessions is usage error.
  Existing positional substring, project, and session filters remain available.
- Swing's `format_rows` behavior is fitted to Clearwater's existing row production
  in `main`: existing fields retain their order, spacing, and optional PAST-CAP marker;
  age and flags are appended in every mode. OVER precedes parked when both apply.

Deliberately not ported: swing's depth arithmetic, request folding, discovery rules,
cap policy/default, or exit-number conventions. Clearwater's `read_transcript`,
`_request_depth`, named/anonymous parsing, `discover_cells`, and default project
resolution remain unchanged. Folding by `message.id`, PEAK versus current, CLI depth
evidence, and PEAK-over-cap precedence are preserved. No JSON mode or Codex transcript
reader was added. The round-0 grep found references but no row parser in scripts,
the kernel docs, or `.claude/`.

## Exit contract

| Case | Swing | Clearwater | Pin |
| --- | --- | --- | --- |
| PEAK over cap | 1 | 2 | `test_exit_map_over_cap_exits_2` |
| No transcript discovered | 2 | 1; LOUD `NO CELLS FOUND` on stderr | `test_exit_map_no_transcripts_exits_1_loud` |
| Unknown agent after clean discovery | 2 | 4; searched forms on stderr | `test_exit_map_unknown_agent_exits_4` |
| argparse usage error | 2 | 4 via `_ConfigError` | `test_exit_map_argparse_usage_exits_4` |
| Nonempty discovery, empty live window (Q4) | 0 | 0; one stdout line, nothing to check | `test_exit_map_empty_live_window_exits_0` |

Clean measurements return 0. Incomplete discovery/reading returns 3; an observed
over-cap row returns 2 even if other errors exist. Discovery-empty is distinct from
an empty live selection. Missing agent lookup with discovery errors returns 3 because
absence cannot be established, and prints both DISCOVERY ERROR and searched forms
for each unmatched ID (F5 and A2 advisory 4). A clean missing ID returns 4 without
measuring the other requested IDs (P9 retained).

F2 rejects negative values, negative infinity, and NaN as usage errors (4). Zero,
negative zero normalized to zero, and positive infinity are valid. Positive infinity
intentionally includes every measurable transcript. F3 requires exact identity and
rejects an empty ID with 4 before discovery, including when discovery would fail.
Agent plus live, and agent plus sessions, return 4.

## Row format and the protected test

Real fixture output captured in `work/wp-h1/turn2/old-row.log` and `new-row.log`:

```text
fixture-cell  current=450002  peak=450002  turns=3  session=session-  cli=none-recorded  PAST-CAP
fixture-cell  current=450002  peak=450002  turns=3  session=session-  cli=none-recorded  PAST-CAP  age=0.1h  flag=OVER
```

Both runs return 2. Columns remain name, current, peak, turns, session, CLI, optional
PAST-CAP, then the new age and flag fields, separated by two spaces. Age has one
decimal hour; flags are `ok`, `OVER`, `parked`, or `OVER,parked`. This is one row
form for default, all, live, agent, and sessions modes.

CHARC's round-0 ruling (A) permits only the anchored regex re-pin in
`MainCliTest.test_past_cap_exits_2_end_to_end`; its name, exit assertion, message,
and prefix remain unchanged. The other 46 tests and old helpers remain unchanged.
The diff against `d427d223` removes exactly the single old regex-pattern line.

## Test inventory and results

The 15 selector ports use synthetic project trees. Names are identical across the
two modules except the two exit-code renames explicitly shown:

| Swing name | Clearwater name |
| --- | --- |
| `test_live_filter_selects_by_transcript_age` | same |
| `test_sessions_mode_reads_main_transcripts_and_excludes_cells` | same |
| `test_agent_reads_a_parked_cell_older_than_the_live_window` | same |
| `test_agent_is_repeatable_and_applies_the_cap` | same |
| `test_agent_unknown_id_exits_2_naming_the_searched_glob` | `test_agent_unknown_id_exits_4_naming_the_searched_glob` |
| `test_agent_with_live_is_a_usage_error` | same |
| `test_r3_a_old_cell_with_a_fresh_parent_is_listed_and_flagged_parked` | same |
| `test_r3_b_old_cell_with_an_old_parent_is_not_listed` | same |
| `test_r3_c_a_fresh_cell_is_listed_not_flagged_parked` | same |
| `test_r3_d_a_parked_cell_over_the_cap_exits_1` | `test_r3_d_a_parked_cell_over_the_cap_exits_2` |
| `test_r3_a_missing_parent_transcript_does_not_crash` | same |
| `test_r3_toctou_deletion_between_check_and_stat_does_not_crash` | same |
| `test_r3_session_transcript_path_never_crosses_project_dirs` | same |
| `test_r3_sessions_mode_with_live_is_unaffected_by_parked_logic` | same |
| `test_r3_over_cap_and_parked_flag_form_is_OVER_comma_parked` | same |

The five exit-map tests are named in the exit table. Reviewer A r1 added 13 tests:

- F1: `test_live_unreadable_cell_is_incomplete`,
  `test_live_cell_age_stat_failure_is_incomplete`,
  `test_live_parent_stat_failure_is_incomplete`, and
  `test_sessions_live_unreadable_or_unstatable_is_incomplete`.
- F2: `test_live_invalid_window_is_usage_error` and
  `test_live_zero_and_infinity_are_valid`.
- F3: `test_agent_exact_name_excludes_longer_sibling`,
  `test_agent_missing_exact_name_with_prefix_sibling_exits_4`,
  `test_agent_full_name_hash_selects_one_transcript`, and
  `test_agent_empty_id_is_usage_error`.
- F5: `test_agent_listing_failure_is_incomplete_not_unknown`.
- F6: `test_future_mtime_is_clamped_to_zero_age` and
  `test_cell_exactly_at_live_boundary_is_listed`.

Reviewer A r2 adds five tests:
`test_agent_reused_name_warns_once_per_session`,
`test_agent_empty_id_with_discovery_error_is_usage_error`,
`test_session_exactly_at_live_boundary_is_listed`,
`test_parent_exactly_at_live_boundary_retains_parked_cell`, and
`test_agent_listing_failure_reports_each_unmatched_id`.
The existing added zero/infinity test also asserts negative-zero normalization.
All newly added fixture names are neutral; no locked fixture was renamed.

Counts: reader 47 -> 67 (build) -> 80 (A r1) -> 85 (A r2 tidy);
harness 382 -> 402 -> 415 -> 420. Turn-5 RED ran 85 tests with four expected
assertion/subtest failures (warning, missing-id diagnostics, and negative zero),
with no import errors. Shimmed GREEN ran 85 tests successfully. The shimmed
whole suite ran 420 tests with three known sandbox failures and one skip.
The dispatcher's unshimmed suite passed 415 before this tidy; final 420-test
seat verification remains the orchestrator's gate.

The exact requested unshimmed reader command was also executed:
`uv run --no-sync python -m unittest discover -s tests/harness -p test_cell_depth.py`.
Under the restricted token it ran 85 tests with 71 PermissionErrors and two
assertion failures caused by temp-directory permissions. Loading the supplied
`sandbox_mkdir_shim` gives the 85-test GREEN result. The suite command was:

```text
PYTHONPATH=scripts uv run --no-sync python -c "import sandbox_mkdir_shim, unittest, sys; sys.exit(0 if unittest.main(module=None, argv=['unittest','discover','-s','tests/harness'], exit=False).result.wasSuccessful() else 1)"
```

TMP/TEMP point inside `work/wp-h1/turn5/tmp`. Logs are in `work/wp-h1/turn5/`.
The three whole-suite sandbox residuals, unchanged from the preceding turn, are:

- `test_dependency_posture.DependencyPostureTest.test_subprocess_no_site_packages_runs_core`:
  its isolated child does not inherit the shim's temp-directory permission change.
- `test_launch_role_content.LaunchRoleDryRunGoldenTest.test_bash_cc_preflight_refusal_positive_control`:
  launcher/environment behavior under the restricted token.
- `test_launch_role_content.LaunchRoleDryRunGoldenTest.test_resolve_main_checkout_root_falls_back_when_git_unavailable_or_fails`:
  the redirected temporary non-repository fixture is inside the worktree repository.

All three pass in the dispatcher's unshimmed seat run. They were not changed.

## Verification loop and review nets

| Round / finding | Classification and disposition | Evidence / action |
| --- | --- | --- |
| Round 0 | STOP: anchored row assertion conflicted with appending fields | CHARC ruled (A): preserve prefix and permit only the regex tail re-pin |
| Build doc guard | STOP: literal retired `--session ` spelling was banned | Dispatcher ruled `--session="<session-id>"`; parser equivalence verified; doc guard then passed |
| A r1 F1 | MAJOR, confirmed and fixed | Error-path tests and corrected non-vacuous comment; isolated mutations dropping discovery guard, unreadable guard, or parent-error propagation were killed |
| A r1 F2 | MINOR, confirmed and fixed | Negative/NaN validation and tests; positive infinity deliberately valid |
| A r1 F3 | MINOR, confirmed and fixed under CHARC ruling | Exact parsed name/hash or full stem; sibling, missing exact ID, full stem, and empty ID tests |
| A r1 F4 | MINOR, confirmed and fixed | Recipe precondition and round gate read the cell; census and dispatcher's own read are additional commands |
| A r1 F5 | ADVISORY, implemented | Failed listing plus unmatched ID exits 3; clean missing ID exits 4; P9 retained |
| A r1 F6 | ADVISORY, implemented | Fixed-time future clamp and inclusive own-age boundary tests; both mutations killed |
| A r1 F7 | ADVISORY, retained limit | Project-level JSONL files are session candidates; no filename exclusion invented |
| A r1 F8 | ADVISORY, operational requirement retained | Run the module through discovery so sibling `_loader` resolves |
| A r2 | CONVERGED: `NO_NEW_CRITICAL_MAJOR` on `6bd5fb99` | Reviewer verified F1-F6, protected core, lock, nine row modes, recipe commands, read-only behavior, and mutation evidence |
| A2 MINOR 1 | Confirmed and implemented in tidy | Reused-name NOTE per ID/session; multiple rows and status retained; full stem selects one; recipe sentence added |
| A2 advisory 2 | Implemented | Empty ID with discovery failure stays 4; empty-ID guard deletion killed by new test |
| A2 advisory 3 | Implemented | Session and parent exactly H tests; each <= to < mutation killed |
| A2 advisory 4 | Implemented | Exit 3 now also names each unmatched ID through searched lines |
| A2 advisory 5 | KEPT, no change | Cosmetic first searched form may describe an unparseable named non-hex bare filename; exact-match explanation and second form remain |
| A2 advisory 6 | Implemented | Negative zero normalized; output assertion prevents -0h |
| A2 advisory 7 | KEPT, no change | Read-error tests remain useful bookkeeping coverage; stat-error cases pin the empty-window guards |
| A2 advisory 8 | Implemented | Only added fixture strings renamed to neutral names |
| Reviewer B | PENDING (orchestrator's seat) | Final candidate and live/gate evidence go to the dispatcher |

Verification followed suspect -> independently confirm -> fix -> rerun. No confirmed
finding was rejected as a false positive. The two STOPs were resolved by explicit
rulings. Reviewer's r2 full pass found no new critical/major issue; its accepted tidy
items are now covered by the 85-test run. The final B net has not run at this cell.
Three extra turn-5 mutations (empty-ID guard removed, session boundary exclusive,
parent boundary exclusive) each ran all 85 tests and failed the intended new test,
with no errors. Mutation copies and logs stayed under `work/wp-h1/turn5/`; the
tracked reader's SHA-256 was unchanged by the mutation runs.

## Live reads at the orchestrator's seat

Evidence: `work/wp-h1/seat/live-reads.txt`, supplied by the dispatcher. This cell
did not read the real projects directory. The recorded command prefix is:

```text
uv run --no-sync python .worktrees/wp-h1/scripts/cell_depth.py --project "C:\Users\rwsmy\.claude\projects\C--Users-rwsmy-clearwater"
```

The following recorded suffixes and outcomes summarize the reads:

| Arguments appended to the prefix | Recorded outcome |
| --- | --- |
| `--sessions --live 24` | Seven main session rows, three OVER; exit 2. Fresh seat sessions `6e4f361a` and `df12d3dd` have PEAK 333893 and 293788 |
| `--live 6` | `no cells written in the last 6h (cap 400,000); nothing to check`; exit 0 |
| `--session=d3dc239c-9491-4fa3-8d45-32cd86b95431 --agent wp57-cell9 --agent wp57-cell8` | Two phase-cell rows at any age: PEAK 173058 and 335605; exit 0 |
| `--live 24` | Nine phase-cell rows, all under cap; exit 0 |

The post-`6bd5fb99` reads also record exact `--agent wp57-cell` selecting one row
(PEAK 292210), and `--agent wp57-cell9-733ddec728fc8315` selecting one row
(PEAK 173058), both exit 0. Missing exact `--agent wp57-cel`, empty `--agent=`,
and `--live -1` each return 4. The repeated `--live 6` read returns the same quiet
window line with exit 0. `--sessions --live 1` lists the two fresh sessions above,
with current depths 215437 and 190909 and their unchanged peaks, exit 0.
Earlier conflicting selector reads also return 4. The quiet six-hour census is
the seat witness for Q4; parked retention is exercised by synthetic tests rather
than claimed from a parked row in this quiet-seat read.

## Static checks and transfer

Project `ruff check .` passes; `ruff format --check .` reports 317 files already
formatted. Explicit `ruff check scripts/cell_depth.py --statistics` stays 25 -> 25:
D205=10, D209=6, N818=2, D301=2, ANN201=1, D103=1, D107=1, RUF023=1, I001=1.
No new rule code appears; the pre-existing findings were not tidied. The project
excludes scripts and harness tests from that gate, as ruled in Q5. Mypy was not run
on `scripts/`; configured files are `src/clearwater` and `tools`.

The re-port delta is exactly:

- `scripts/cell_depth.py`
- `tests/harness/test_cell_depth.py`
- `docs/dispatch-recipe.md`

The report and ledger are instance records. The template re-port is the orchestrator's
act at accept, with its template-state checks and template harness suite; no push
without the owner's word. No template clone was modified by this cell.

Tracked changes against `d427d223` consist of those three delta files plus the
docs-only merge files `CLAUDE.md`, `docs/briefs/wp-h1-brief.md`, and
`docs/charc-state.md`. This new report is an additional untracked owned file until
the dispatcher commits it. The four cell-owned changed files have zero CR and
zero non-ASCII bytes. There is no out-of-envelope implementation change.

## Limits and remaining handoff

- Codex cells are not covered; their depth comes from the `codex exec` footer.
- Parked retention depends on the parent transcript's mtime; a quiet parent does
  not move that timestamp.
- F7 remains: any project-level `*.jsonl` reads as a session candidate.
- A name reused within one session gives several rows. The NOTE and full
  `<name>-<hash>` stem identify the remedy; selection is intentionally unchanged.
- An ID that is a 16-hex name can also match an anonymous hash.
- The three listed sandbox residuals are environmental; final unshimmed 420-test
  verification is still the dispatcher's responsibility.
- `_loader` is a sibling import, so run the reader tests with `discover -s`.
- A2 advisories 5 and 7, and F7, intentionally remain unchanged. Reviewer B,
  final seat gates, acceptance, and template re-port remain at the orchestrator's seat.
