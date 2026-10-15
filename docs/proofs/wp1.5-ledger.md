# WP1.5 -- cumulative review round ledger (Reviewer A)

Tier strong; transport WSL; codex-cli 0.162.1; flags `-m gpt-5.6-sol -c model_reasoning_effort=high -s read-only --skip-git-repo-check`.
Bring-up probe (2026-10-15): banner gpt-5.6-sol / high, one `^ succeeded in` line, footer present (`probe/`).
Evidence: `C:\Users\rwsmy\clearwater-review-evidence\wp1.5\rN\` (prompt, diff, transcript, head, adjudication, md5s). Staging files (`wp15-*`) live in the session scratchpad, never in the worktree, and are deleted at teardown. Base `7048fd7`.

| Round | Head reviewed | crit / major / minor | In / out envelope | NEW / REOPENED | Reverts | Fixes changed | Assertions | Verdict | Depth |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 135ab46 | 0 / 2 / 2 | 2 in / 2 out | 4 NEW / 0 | 0 | product (spike.py, compare.py: per-file write checks, GPU evidence in proofs, exact container start) + tests; in 21d418d; report 1163ff1 | banner ok; ^ERROR 0; `ERROR codex_core` 2 = sandbox rejecting the reviewer's own `rm -f` probe, and a brief echo; footer 1; succeeded 4; withheld-path hits = prompt/brief echoes, exclusion globs, one incidental rg hit in docs/proofs/wp1.2-accept.md (wp1.5 ledger absent) | BLOCKING 1 2 | (dispatcher-read) |

## Findings and adjudication

Round 1 (all REASONED: the reviewer's sandbox had no writable temp): (1) major, record files written without a per-file path check, so a link planted at a record's name could redirect a write into the footage folder -- confirmed by two new tests that fail on 135ab46 (CLI wrote through a planted link; reencode did not raise); fixed. The sub-point on the test helper writing synthetic clips under pytest's tmp_path declined: the brief's assertion binds spike.py runs, and test inputs go to pytest's own folder, neither footage nor working. (2) major, an NVENC proof could be proven without nvidia-smi naming a GPU, and a non-zero nvidia-smi exit counted as a sample -- fixed (NVENC proof needs a named GPU and an NVENC session; decode proof needs a named GPU; at least one sample always taken); three negative/positive tests; real proofs re-run on 21d418d, all held (3 samples, 1 session each). (3) minor, out of envelope, container start compared as ffprobe's 6-decimal text -- fixed (exact earliest stream start). (4) minor, out of envelope, ctts v0 read as signed -- declined: the edit-effect media start must sit on the composition timeline the demuxer uses for the compared pts, and FFmpeg reads ctts signed in both versions; a unit test pins it.
