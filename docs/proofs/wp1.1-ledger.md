# WP1.1 -- cumulative review round ledger (Reviewer A)

Tier strong; transport WSL; codex-cli 0.162.1; flags `-m gpt-5.6-sol -c model_reasoning_effort=high -s read-only --skip-git-repo-check`.
Bring-up probe: one `^ succeeded in` line before round 1 (`probe/transcript.txt`). Evidence: `C:\Users\rwsmy\clearwater-review-evidence\wp1.1\rN\` (prompt, diff, transcript, adjudication, md5s); analysis scripts behind the report numbers in `...\wp1.1\analysis\`.

| Round | Head reviewed | crit / major / minor | In / out envelope | NEW / REOPENED | Reverts | Fixes changed | Assertions | Verdict | Depth |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 4ac854e | 0 / 4 / 2 | all in | 6 NEW / 0 | 0 | product (WB maximum >= 1; sigma floor removed) + tests (4 discriminating oracles, defaults 2x test) + report text; fixed in b9ca3e4 | banner ok; ^ERROR 0; `ERROR codex_core` 1 = echoed brief text; WSL vsock lines = reviewer's sandboxed .exe attempt; footer 1; succeeded 14 | BLOCKING_FINDINGS | (dispatcher-read) |

## Findings and adjudication

Round 1: (1) major, REASONED, `max_white_balance_gain` below 1 made strength 0 non-neutral -- confirmed, Params now rejects it. (2) major, REASONED, the 0.5 px sigma floor broke resolution independence of the defaults and the 2x test avoided it -- confirmed, floor removed, defaults 2x test added (512 x 768 textured scene), thumbnail-size limit disclosed in the open-values report. (3) major, REASONED, no test pinned the 3C Cb equation -- confirmed by mutation, pixel-by-pixel oracle added. (4) major, REASONED, weights tested only on flat images and fusion tests satisfied by a per-pixel blend -- confirmed by mutation, oracles added (edge, coloured patch, Lab references, weight seam). (5) minor, EXECUTED, private helpers without docstrings -- fixed. (6) minor, REASONED, pyramid wording in the report -- rejected on substance (the coarsest level is the whole scene at the same 16 px resolution for both sizes), wording rewritten. Every added test was checked to fail on the mutation it targets. Reviewer sandbox could not run uv or pytest; it said so.
