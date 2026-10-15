# WP0.2 -- cumulative review round ledger (Reviewer A)

Tier fast; transport WSL; codex-cli 0.162.1; flags `-m gpt-5.6-luna -c model_reasoning_effort=medium -s read-only --skip-git-repo-check`.
Bring-up probe: one `^ succeeded in` line before round 1. Evidence: `C:\Users\rwsmy\clearwater-review-evidence\wp0.2\rN\` (prompt, diff, transcript, adjudication, md5s).

| Round | Head reviewed | crit / major / minor | In / out envelope | NEW / REOPENED | Reverts | Fixes changed | Assertions | Verdict | Depth |
|---|---|---|---|---|---|---|---|---|---|
| 1 | c0cff8a | 0 / 1 / 0 | all in | 1 NEW / 0 | 0 | product (resolved `working/reports` checked against the footage root) + 1 test | banner ok; ^ERROR 0; `ERROR codex_core` 1 = echoed brief text; footer 1; succeeded 5 | BLOCKING_FINDINGS | (dispatcher-read) |
| 2 | 26752eb | 0 / 0 / 2 | all in | 2 NEW / 0 | 0 | cleanup only: 1 product line (rotation snapped to quarter turns) + test assertions | banner ok; ^ERROR 0; `ERROR codex_core` 2 = 1 echoed brief text + 1 reviewer command that failed to launch in its sandbox; footer 1; succeeded 7 | NO_NEW_CRITICAL_MAJOR (converged) | (dispatcher-read) |

## Findings and adjudication

Round 1: (1) major, REASONED, `main()` checked `working` but not `working/reports`, which may be a symlink or junction into the footage folder -- confirmed by a test (pre-fix main returned 0 and wrote under the footage tree; post-fix returns 2), fixed in 26752eb.

Round 2: (1) minor, REASONED, rotation values not snapped to {0, 90, 180, 270} -- fixed. (2) minor, collision test did not assert the returned names for the CSV-only case -- fixed. Reviewer sandbox could not run uv, pytest or ffprobe; its conclusions were source-based.

Banked: CSV cells are not neutralised against spreadsheet formula injection from hostile file names (out of envelope: the footage is the owner's own).
