# WP1.2 Part B — Remediation after Reviewer B (dispatch brief, FINAL)

**Status:** FINAL, issued by the orchestrator 2026-10-19. This is the ONE remediation after a blocking Reviewer B pass at
the orchestrator's seat, on candidate `wp1.2b-mc` `6e538d7` (= the cell's `2fa0ac8` rebased onto main
`d7a281e`; patch-id `342f070f`).
- Evidence: `C:\Users\rwsmy\clearwater-review-evidence\wp1.2b\reviewB\` (transcript md5
  `4f6ed9f6ffe6188c3e544b65ad0ee04f`).
- Spec v0.5.3; Part B itself was issued against v0.5.2, and nothing it measures changed.
- Cell: the same `wp12b-cell`, worktree `.worktrees/wp1.2b`, branch `wp1.2b`, from head `2fa0ac8`.
- Owned files: the parent brief's five, unchanged (`docs/briefs/wp1.2b-brief.md`).

**NO timed window is re-run.** Every remediation either:
- corrects text against the records that already exist;
- adds an UNTIMED verification run on outputs that already exist; or
- changes a code path outside the timing bracket.

Say so in the report and the ledger. The owner's best-effort release and its rules (CHARC
`d4188563639bc453`) stand.

## Findings and required dispositions

| # | B finding (severity, tag) | Disposition | Required |
|---|---|---|---|
| 1 | W3b labelled CLEAN, but its closing probe's `ambient.stray_processes_after` records `python.exe` PID 17192 at 53.0 % (MAJOR, EXECUTED; confirmed at my seat) | VALID: fix | Apply the stated rule. W3b is CONTAMINATED unless a record identifies PID 17192 as the instrument's own process tree, in which case show the record and say why it is excluded. Propagate to every place that leans on it: the windows table, claim 4's "clean" row and its "best short-run indication" sentence, and candidate #6's estimate. |
| 2 | Contaminated rows given as point figures, some with p95 instead of max, against the ruling's min/median/max spread (MAJOR, EXECUTED) | VALID: fix | Every contaminated row (W2 both decodes, W3, the W4 resident row, W5, and any other) gains the per-frame min / median / max from its own record, beside the bracket s/frame. The bracket figure stays the headline, labelled contaminated. The figures come from the records by script, and the script is named in the ledger. |
| 3 | The "content witness" runs in `_Reader` on the decode side, so it cannot catch a writer-ordering, conversion or encoder defect after correction (MAJOR, REASONED) | VALID in substance: fix | (a) Report wording: state exactly what the in-loop witness covers (the render's input matches the analysis input) and what it does not. (b) An UNTIMED output witness, added to `clip.py` with a test, run on BOTH existing exports: GX011627 production `bench/W4/...-223431/` and GX011625 `bench/...-231103/`. For at least 20 frame indices spread over each clip, including the first and the last, it decodes output frame i, recomputes `correct(source frame i, params, statistics=smoothed_i)` through the same conversions, and requires: PSNR(output i, expected i) at or above a floor stated with its basis; and that score strictly better than against expected i-1 and i+1, which catches an ordering slip. The test plants a frame swap and a wrong statistics index; each must fail by name. Record under the run folder as `output-witness.json`; give the report the result and the floor. |
| 4 | Export failure leaves a partial MP4 at the final name; `-y` can truncate a prior good output (MAJOR, REASONED) | VALID: fix | Encode to a temporary name in the same folder. Rename to the final name only after a successful close and the checks. Refuse to overwrite an existing final file. Remove the partial on every failure path. Tests: a planted core exception and a planted encoder failure each leave no partial and keep a pre-existing final file byte-identical. State that this is outside the timing bracket (the rename follows the encoder's exit), so no figure moves. |
| 5 | Provenance does not compare the full decode command, `time_base`, `frame_rate` or bit depth (MINOR, REASONED) | VALID: fix | Compare them; add a refusal test for each. If the existing records lack a field, say so and show that the existing exports' records match on what they hold. |
| 6 | `timing.closed` is taken after reaping the decoder and then the encoder, not at the encoder's exit (MINOR, REASONED) | VALID: wording | Report and docstring: the bracket ends when BOTH child processes have been reaped. From the records, say which exited first and the size of the gap, if recorded; if not, say so. No re-timing. |
| 7 | `decode_frames` buffers FFmpeg stderr through `tempfile.TemporaryFile()` in the OS temp folder (MINOR, REASONED) | VALID: fix | Put it under `work/wp1.2b/` (through the checked output root), or drop the temporary file. Add a test. |
| 8 | "Sampled every 50 ms" is false: the sampler sleeps 50 ms and then queries, and W5 averaged 81 ms (154,868 samples over 12,526.8 s) (MINOR, EXECUTED) | VALID: wording | State the actual cadence from the records for each whole-clip run. |
| 9 | "+18 % attributed to concurrency" and "with #1 + #3 + #5 the core stays near 0.2 s" are not established by a controlled run; #3 targets c3 only, and #1 and #5 overlap (MINOR, REASONED) | VALID: wording | Label both as hypotheses or estimates, with what they rest on and the run that would confirm them. Correct the combination arithmetic: #3 does not apply to ancuti2018, and #1/#5 overlap. No new runs. |

## Process

- Reviewer A: STRONG (`gpt-5.6-sol` / high), WSL, as the parent brief. Run on the remediation diff
  (`2fa0ac8..<new head>`) plus the report until zero new valid blocking findings. The ledger
  continues with a remediation section.
- The gates are as the parent's: ruff, format, mypy, pytest with gpu and footage RUN and 0 skipped.
- The output witness and the gpu tests use the card. No timed window is opened, and the
  windows' records are not rewritten. New records go only beside them.
- Then return. The orchestrator runs a second, final Reviewer B on the new candidate. Under the
  gate rules there is no third remediation: a second blocking B is adjudicated at the gate.

## STOP conditions

- Any fix needs a change outside the five owned files (`pipeline.py`, `params.py`,
  `backend.py`, `pyproject.toml`).
- The output witness FAILS on a real export. That is a correctness defect in the measured loop:
  STOP and report with the frames. Do not re-time.
- Any fix would move a timed figure.
