# Harness template upstream port and cross-harness review -- 2026-11-02

**Owner direction (in chat to CHARC gen 12, 2026-11-02, verbatim):** "I am ready to update the
comms harness template based off of this project's implementation, including the codex development
addition. One thing I have noticed, additionally, is during roll-over there is still a step to stop
the (deprecated) message monitor." Then: "Send a notification of the harness change to coa-chess and
swing-trading charcs. Have them perform reviews of the changes and send deficiences to you for
adjudication." Form chosen by the owner: CHARC ports on a branch; the owner reviews and pushes.

## The branch

`C:\Users\rwsmy\harness-template`, branch `clearwater-upstream-2026-11-02`, base = GitHub
`origin/master` `6488556` (2026-07-08). `core.autocrlf` set false in that clone (working tree LF).
Template suite at every commit: `python -m unittest discover -s tests/harness` (382 OK, 1 skip once
run without `-I`; the author's first runs under `python -I` hid the installed `[web]` extra and showed
40 skips).

| Commit | Content |
|---|---|
| `fc9f4b5` | Layer 1: the coa-chess comms core as Clearwater instantiated it (`87b577a9`, 2026-10-14): singular inboxes, the registry and its two hooks removed, the two surviving hooks, `cell_depth.py`, `role_mail.py` hardening, the psmux launcher, the kernel docs, tests under `tests/harness/`. |
| `b3dc40a` | README follows the core (no registry; the doc-acceptance test had failed on the old README). |
| `d74f40c` | Layer 2: the Codex lane (`codex_cell.py`, the two usage readouts, their tests, a generic `implementer-codex-template.md`, reviewer-pairing wording, the readout permission) and the kernel lessons (reaper-off launcher, cap-not-exhaustion rollover, nothing-still-running at a roll). The sandbox shim and `research/` stayed instance surface. |
| `4c05c8e` | The rollover sequence is THREE acts: the deprecated "stop the inbox monitor" act removed; a seat that armed a Monitor under the named exception stops it before the announce. Mirrored to Clearwater main `d5b76c53`. |
| `5519644` | README names the two implementer lanes. |
| `8031617` | Remediation after the two reviews (below). Kernel-doc subset mirrored to Clearwater main `15d1c828`. |

## The reviews

Requested by SendMessage to `coa-charc-20261026-1213` and `swing-charc-20261025-2251` (read-only on the
branch; findings severity-tagged with evidence; CHARC adjudicates; disagreements go to the owner).
Both replied within the hour. Dispositions were returned to each by SendMessage.

### swing-trading CHARC: 15 findings

| # | Sev | Finding | Disposition |
|---|---|---|---|
| 1 | MAJOR | `cell_depth.py` has no `--sessions` (self-read) / `--live HOURS` (in-flight by transcript mtime); the precondition's evidence has no instrument. | **OPEN, second pass.** Porting swing's selector set into the branch's lineage (its own 850-line suite) is a merge, not a fix. Recommended: a second upstream pass taking swing's `cell_depth.py` + tests as the base. |
| 2 | MAJOR | Launcher hardcodes the hand-made `bash-cc.exe` and the preflight exits 1 when absent, DryRun included: a fresh clone cannot launch. | FIXED: warn and spawn with the sibling `bash.exe`; refuse only when no `bash.exe` either; README step 3. |
| 3 | MINOR | Charter still says "the four acts". | FIXED. |
| 4 | MINOR | "footage run", "95-minute review-pack piece", "gen 32" in kernel rule text. | FIXED (generic job classes; "an orchestrator generation"). |
| 5 | MINOR | Stale pre-move test paths (`tests/test_*`, `tests/genericity_lists.py`, the removed registry tests). | FIXED everywhere cited. |
| 6 | MINOR | `role_mail.py` prints no cue line; every seat hand-reads the launch map. | FIXED, ported in swing's shape: `ping -> SendMessage to="<name>"` after `posted ->` (post and post-verified; read-only). |
| 7 | MINOR | Docstring example addresses `opsdir`, not a valid role. | FIXED. |
| 8 | MINOR | `DEFAULT_PORT = 8775` with a this-machine comment. | FIXED: 8765, a per-instance SEAM comment; UI tests follow. |
| 9 | MINOR | Orchestrator-context says the stop hook's drain-now is VOID for an outgoing orchestrator, but the hook fires for `charc` only. | FIXED by scoping the text; the role list unchanged (widening is a behaviour change no instance asked for). |
| 10 | MINOR | Preflight message says the seam-4 default uses `--effort max`; it is medium. | FIXED (generic wording). |
| 11 | MINOR | The MIRROR half of the cap rule unstated (at or past the cap, dispatch nothing new). | FIXED in charter 5.1 and the prompting standard. |
| 12 | ADV | Act 3 launches with no `-DryRun` rehearsal. | FIXED in both act-3 texts. |
| 13 | ADV | No subject cap (swing enforces 80). | DECLINED: the branch caps at 120 (`SUBJECT_MAX_CHARS`, operator-directed 2026-09-24 in this lineage). |
| 14 | ADV | `Bash(python scripts/usage_claude.py*)` prefix allowance. | FIXED: exact rule, no wildcard. |
| 15 | ADV | The 40-skip figure means the UI tests did not run for the author. | ACCEPTED: `python -I` hid the extra; re-run 382 OK, 1 skip. |

### coa-chess CHARC: 19 findings

| # | Sev | Finding | Disposition |
|---|---|---|---|
| 1 | CRITICAL | `discover -s tests` runs 0 tests (bare-name imports need `tests/harness` as start dir) while pyproject and the dry-run doc still name it; the guard test asserted only a substring. | FIXED: `discover -s tests/harness` named everywhere; the guard asserts the exact command. |
| 2 | MAJOR | Charter (operator 2026-09-25: no early roll) vs prompting standard (director ruling 2026-10-20: roll before a dispatch whose cells outlive the seat). | **TO THE OWNER** for one text in both files. Recommendation: the 09-25 direction is the rule; the pre-dispatch case is its stated exception, which the owner's 2026-11-02 rule ("start no long job you cannot see finish") already endorses. |
| 3 | MAJOR | The `bash-cc.exe` hardcode (as swing 2). | FIXED (as above). |
| 4 | MAJOR | `genericity_lists.py` ships Clearwater's instance list and exempts whole `src/`/`tools/` trees; the Codex template was never scanned. | FIXED: generic set only with a bootstrap comment; `implementer-codex-template.md` in `CORE_AGENT_RELPATHS` and the manifest (23). |
| 5 | MAJOR | `codex_cell.py` bakes one instance's toolchain (model, sandbox, uv cache, runner allowance, lock exclude). | FIXED as a marked SEAM block; `windows.sandbox` only on Windows; cache root per OS. |
| 6 | MAJOR | "Reviewer is the other model" absent from the dispatch recipe; a Codex cell following the docs reviews itself. | FIXED in recipe section 3 and the codex-reviewer staging heading. |
| 7 | MAJOR | Instance vocabulary in rule text ("footage run", "gen 32", "pre-live-tranche"). | FIXED. |
| 8 | MAJOR | Port pin (as swing 8). | FIXED. |
| 9 | MINOR | "four acts" (as swing 3). | FIXED. |
| 10 | MINOR | Orchestrator-context items numbered (4), (6), (7), (5). | FIXED: (4)-(7) in order (uncommitted-edit = (6), one-index = (7)). |
| 11 | MINOR | Private identifiers with no referent (WP3.21, r7, WP1.2B, a06374, 73e1fb45, v17 seed 8, tranche/game, "Clearwater (owner-directed)"). | FIXED at every cited line. |
| 12 | MINOR | Citations to unshipped files (a brief path, a mail filename, a proofs doc, `session_end`). | FIXED. |
| 13 | MINOR | `shell=True` with a list argv on Windows. | FIXED: `shutil.which` resolves `codex.cmd`; no shell; the residual cmd.exe parsing of a `.cmd` noted in code. |
| 14 | MINOR | Codex template says depth comes from the footer; the driver reads the rollout record. | FIXED. |
| 15 | MINOR (unreproduced) | `usage_codex.py` takes `primary` without checking the 7-day window. | VERIFIED and FIXED: picks the window with `windowDurationMins == 10080` from primary or secondary, falls back to primary. |
| 16 | ADV | The Codex template under `.claude/agents` is listed as a dispatchable subagent. | DECLINED: by design beside the Claude cells; a spawn with `model: codex/...` fails loudly; the orchestrator never spawns it. |
| 17 | ADV | The lane's live path (`cmd_turn` / `cmd_commit` / `cmd_review`) is untested. | ACCEPTED as a limit, named in the commit. |
| 18 | ADV | `stop.py` reads the role from `HARNESS_ROLE` only. | ACCEPTED as a pre-existing limit (same in coa-chess live). |
| 19 | info | coa-chess drift = the OpsDir add, the footer wording, the reviewer banner values. | Noted; stays coa-chess-local. |

## Open for the owner

1. **Push** the branch after ruling item 2 (the early-roll text). DONE 2026-11-02 ~16:40Z: the owner
   pushed `clearwater-upstream-2026-11-02` (`ef7e671`); CHARC opened PR #1
   (https://github.com/rwsmythe/harness-template/pull/1) on the owner's word. The merge to `master` is
   the owner's click.
2. **Second pass: COMMISSIONED by the owner 2026-11-02 (verbatim: "commission the second pass after
   phase 5 closes").** Scope: `cell_depth.py` gains swing's `--sessions` (self-read) / `--live HOURS`
   (in-flight by transcript mtime) selectors with swing's tests as the base (swing MAJOR 1), landing
   first on the Clearwater instance, then upstreamed by the re-port method below. Dispatch gate: Phase
   5 CLOSED (the gate report accepted). Harness-side package, CHARC-briefed; runs the harness suite,
   not the product gate.

## Re-port method for later

In Clearwater, `refs/remotes/template/main` tracks the template head. A later delta is
`git diff template/main HEAD -- scripts/ .claude/ tests/harness/ <the seven kernel docs>` minus the
instance cells, `scripts/sandbox_mkdir_shim.py` and `research/`; apply with `git apply --index` in the
template clone (working tree LF), then the per-instance seams (port, genericity list, codex pins).
