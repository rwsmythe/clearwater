# WP-H1 ledger (orchestrator generation 40, 2026-11-04)

`scripts/cell_depth.py` second pass: swing's selectors `--sessions`, `--live HOURS` with the parked-cell rule, and `--agent ID`, on the Clearwater reader.

**Brief:** `docs/briefs/wp-h1-brief.md`.
- Gen 40's dispatch fill `3823b645`.
- FINAL by CHARC at `d799ba4a`, ruling Q4 = exit 0 on an empty window and Q5 = the project ruff gate.
- Round-0 ruling (A) at `0d26e240`.
- F3 ruling at `fe6486ec`.

**Lane: CODEX** (`implementer-codex-sol-high`, GPT-6.1 Sol / high), one session, `01a1a51b`. Both nets are Claude (`claude-opus-5-5`, high), the other model, run read-only at the orchestrator's seat.

**Evidence:** `C:\Users\rwsmy\clearwater-review-evidence\wp-h1\`
- `cell\`: dispatch / prompt / return / turn 1-5;
- `A\r1`, `A\r2`;
- `B\`;
- `gate\`: live reads and harness logs.

**Paces:**

| When | Codex | Claude |
|---|---|---|
| Dispatch, 05:46Z | 22 % / 0.226 | 19 % / 0.729 |
| First yield, 06:09Z | 22 % / 0.225 | 19 % / 0.723 |

## Rounds

| # | What | Depth after | Outcome |
|---|---|---|---|
| 0 | Turn 1, round 0, read-only | 101,975 | STOP: the brief's row-column design against its 47-test lock (an anchored row regex). **CHARC ruled (A):** re-pin that one pattern exactly; 46 byte-unchanged; one row format in every mode. The shimmed harness form was verified at the seat (382 OK) and nodded. |
| 1 | Turn 2, build | 151,819 | RED 25 failing, then GREEN 67. STOP: the doc guard bans the literal `--session ` in the recipe. **My ruling:** use the `=` form, since the spelling was my dispatch's. |
| 1b | Turn 3, recipe fix | 155,804 | The "0 of 70" sentence restored. **Commit `b4e6a19e`.** Unshimmed harness 402 OK; live reads at the seat. |
| A r1 | `b4e6a19e` | n/a | **NEW_CRITICAL_MAJOR_FOUND**. See the A r1 findings below. |
| 2 | Turn 4, A r1 fixes | 184,810 | **Commit `6bd5fb99`.** Unshimmed harness 415 OK. Live re-check: exact `--agent`, prefix → 4, `--live -1` → 4. |
| A r2 | `6bd5fb99` | n/a | **NO_NEW_CRITICAL_MAJOR = CONVERGED.** F1-F6 FIXED, verified by mutation. MINOR 1: a name reused in one session gives two rows. Advisories 2-8. |
| 3 | Turn 5, A r2 tidy + report | 60,176 (the Codex session auto-compacted in this turn) | The reused-name NOTE plus a recipe sentence; pins for the empty id under a discovery error and for the session / parent `<=` boundaries (mutations killed); exit 3 names the unmatched ids; `-0` normalised; the added fixtures renamed neutral. A2 advisories 5 and 7 and F7 are KEPT, as Limits. Report `docs/reports/wp-h1-cell-depth.md`. **Commit `411ce22f`.** Unshimmed harness **420 OK** (1 skipped). Reader module 85. Project ruff and format clean; explicit path 25 → 25. Test lock holds (one removed line against `d427d223`). |
| B | `f6b53883` (`411ce22f` + this ledger) | n/a | **NO_NEW_CRITICAL_MAJOR**. No false-clean path; 14 of 16 mutations killed; 420 OK unshimmed. MINORs: **B1** the re-port diff would carry a stale docstring line ("v17's seed 8 attempt 2") back into the template, undoing template commit `80316172`; **B2** a name reused across sessions gives no note; **B3** the `--sessions` `is_file()` failure path is untested (2 mutations survived); **B4** report statements stale. Advisories B5-B11. |
| 4 | Turn 6, B's single remediation | 84,621 | B1 template wording restored (the delta now carries package changes only; no `v17` / `seed`); B2 cross-session NOTE; B3 strict / collecting / CLI `is_file` failure pins (mutations killed); B6 filter named in the no-cells line; B7 neutral test docstring; B8 fixed clock in `_run`; report refreshed (B5, B9-B11 kept as Limits). **Commit `3dba892b`.** Verified at the seat, no further round: unshimmed harness **423 OK** (1 skipped); ruff project clean, explicit path 25; lock holds; 0 CR / 0 non-ASCII; the re-port delta scanned for instance vocabulary, 0 hits. |

**A r1 findings:**
- **F1 MAJOR:** no test pinned the in-window error guard; three mutations were unkilled.
- **F2:** `--live` negative or NaN gave exit 0.
- **F3:** `--agent` was a prefix match, so it could silently read the wrong cell. **CHARC ruled an EXACT match:** the cell name, or the full `agent-a<ID>` stem; an empty id gives 4.
- **F4:** the recipe's precondition read the dispatcher's own session, not the cell.
- **F5:** a listing failure under `--agent` gave 4, not 3.
- **F6:** the clamp and boundary were unpinned.
- **F7:** any project-level `*.jsonl` reads as a session (goes to Limits).
- **F8:** my prompt's test command needed `discover -s`.

## Seat facts

- **Sources.**
  - Clearwater reader: 551 lines, tests 850 lines / 47 tests, harness 382.
  - Swing reader: 365 lines, tests 471 lines / 29 tests (15 selector tests), with its commits `b09bbc02`, `d4986324` and `4e412db9`.
- **Template clone** at dispatch: `master` = `origin/master` = `refs/remotes/template/main` = `4335ff6`, clean.
- **Merges of main INTO `wp-h1`** (`--no-ff`), so that every cited hash stays reachable:
  - `d427d223`: the round-0 ruling;
  - `4a107a00`: the F3 ruling.
- **Sandbox.** The Codex restricted token cannot list `tempfile.mkdtemp`'s 0o700 directories. The cell runs the harness with `scripts/sandbox_mkdir_shim.py` preloaded. Three launcher / subprocess tests fail only in the sandbox; they pass at the seat unshimmed. The suite of record is the seat's.
