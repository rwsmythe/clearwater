# DR-44 contract amendment -- record (orchestrator, 2026-10-21)

**What:** the wave-3 pre-dispatch commit CHARC ruled (`e7745b2be6fdd55c`; the `f4cd1e4` form): additive
`clearwater.gui.contract` members for DR-44 (a) and (b), the shell adapted to them, the shell's tests extended.
DR-44 (c) (`QtJobRunner.close()` timing) stays OPEN for WP4.3.

**Base and commits (on main, fast-forward):** base `0f51822`; `701055d` (members: `Message.owner`,
`MessagePresenter.clear(severity=None, *, owner=None)`, `FrameOutcome`, `Session.frame_decoded`; shell owners
`shell.start/open/preview/frame`; `tests/gui_support.CapturingPresenter.clear` takes `owner`), `7bee620`
(Reviewer B pass-1 remediation), `de206e2` (pass-2 minors, tests only). Authored by the orchestrator in the
worktree `.worktrees/dr44` (branch `dr44`, kept), after the uncommitted-main-tree slip that became kernel
hazard (7).

## Tests

| Tree | Run | Result |
|---|---|---|
| `273c64c` (= `701055d` before rebase over docs-only commits) | full pytest, offscreen | 3564 passed, 2 skipped, 947 s |
| `f6f2dbb` (= `7bee620`) | full pytest, offscreen | 3569 passed, 2 skipped, 820 s |
| `de206e2` worktree (test-only delta) | `tests/test_gui_*.py` | 130 passed; a planted unfiltered preview `clear("error")` fails the new test |
| main `de206e2` | harness; ruff; format; mypy | 366 OK; clean; 174 formatted; 107 files clean |
| main `de206e2` | full pytest, offscreen | 3570 passed, 2 skipped, 845 s, exit 0 |

## Reviewer B (the orchestrator's single Codex pass; both nets at this seat)

Runner `codex exec -m gpt-5.6-sol -c model_reasoning_effort=high -s read-only --skip-git-repo-check`.
Evidence: `C:\Users\rwsmy\clearwater-review-evidence\dr44\reviewB\` and `...\reviewB2\` (prompt, diff,
transcript, stderr, `md5s.txt`).

| Pass | Tree | Assertions | Verdict | md5 of `review-B.txt` |
|---|---|---|---|---|
| 1 | `273c64c` | banner gpt-5.6-sol / high; 0 `^ERROR`; 9 "succeeded in"; tokens footer 80,324; VERDICT anchored; withheld paths only as `--glob '!docs/proofs/**'` exclusions | NEW_CRITICAL_MAJOR_FOUND | `2f0dfd283b2ef969e31a0aefb8e32ff1` |
| 2 (re-run) | `f6f2dbb` | banner gpt-5.6-sol / high; 0 `^ERROR`; 30 "succeeded in"; tokens footer 96,652; VERDICT anchored | NO_NEW_CRITICAL_MAJOR | `09f1f456696f6d7a6532685b9bbed174` |

Pass 1: #1 MAJOR, the successful open called an unfiltered `presenter.clear()`, removing panels' messages
(DR-44 (b) still open on that path) -> the open path clears `messages.SHELL_OWNERS` only, documented in the
contract; #2 no `frame_decoded` once the window closes -> documented exemption; #3-#5 test gaps -> five tests;
#6 the settings refusal owned by `shell.start`. Pass 2: pass-1 #1-#6 closed, none reopened; three test
minors: #1 (a scheduling race in the source-change test) and #3 (preview-success owner isolation) fixed in
`de206e2`; #2 (emission order and the `frame_decoded` -> `set_statistics` pairing as a test) banked for
WP3.18, whose cell consumes the signal.

## Consumer note (GUI cells)

The shell clears only its own banners (`shell.*`) when a new source opens; a panel clears its own, for
example on `source_changed` (contract `MessagePresenter.clear`).
