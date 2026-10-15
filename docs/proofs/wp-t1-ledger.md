# WP-T1 -- round ledger (Reviewer A, one round)

Evidence (outside every repo tree, with `MD5SUMS.txt`): `C:\Users\rwsmy\clearwater-review-evidence\wp-t1\r1\`.
Transport WSL, codex-cli 0.162.1, `-m gpt-5.6-sol -c model_reasoning_effort=high -s read-only
--skip-git-repo-check`, tier STRONG. Probe through the exact invocation: banner gpt-5.6-sol / high,
`^ succeeded in` present. Dispatcher-read context depth: not reported to the cell at this point.

| Round | Result | Counts (crit/major/minor) | In envelope | NEW/REOPENED | Reverts | Fix kind |
|---|---|---|---|---|---|---|
| 1a | VOID (capture defect: stdout and stderr redirected to one file overwrote the banner, so assertion 1 could not be read) | 1/1/4 (findings adjudicated) | 5 in, 1 out (bytes tempdir) | NEW | 0 | product (conftest) + tests |
| 1b (counted) | all assertions pass; `VERDICT: BLOCKING_FINDINGS` | 1/4/1 | 6 in, 1 minor conservative-by-design | NEW (all new; 1a's fixes held) | 0 | product + tests |

Round 1b assertions: banner `gpt-5.6-sol` / `high`; `^ERROR` and `ERROR codex_core`: 0 lines;
`^tokens used` footer present (1); anchored VERDICT in the final message; 14 `^ succeeded in`;
`docs/proofs|wp-t1-ledger|clearwater-review-evidence|clearwater-footage` grep: 1 hit, an ECHO of the
prompt's own withhold paragraph (line 37), no access.

## Adjudication (all findings REASONED; the sandbox could not run pytest)

Round 1a:
1. critical, `\?\` prefix bypass: CONFIRMED (the test failed against the unfixed code and pytest
   wiped the fake footage). FIXED: prefix stripped before a drive letter; file-identity backstop.
2. major, default root equal to the parent of a footage folder named `pytest-of-*`: CONFIRMED by
   reasoning; FIXED (`_holds_pytest_of`) + test.
3. major, test module reads the real config via the outer conftest: REJECTED as designed: that read is
   the guard's own purpose; no test reads it. Docstring unchanged in substance.
4. major (out of envelope), bytes `tempfile.tempdir`: FIXED (`os.fsdecode`).
5. minor, every uncached candidate checked: KEPT by design (conservative; the cached tempdir is the
   normal case). Wording of the message corrected.
6. minor, apostrophe in a TOML path in the tests: FIXED (escaped basic strings).

Round 1b:
1. critical, pytest capture and tempfile probe write random-named files in `TMPDIR`/`TEMP`/`TMP`
   before any conftest loads: CONFIRMED EXECUTED with an audit hook (`capture-writes-audit.log`):
   one probe file created and removed, two capture temp files opened; nothing existing touched.
   NOT FIXABLE inside the owned files. This is the brief's STOP item (an ordering that lets pytest
   write before any conftest hook); documented in the conftest docstring and the report, raised in
   the return report with the early-plugin mitigation (needs `pyproject.toml` + `tools/`).
2. major, a `pytest-of-*` link at a safe root leading into footage: CONFIRMED by reasoning; FIXED
   (`_pytest_of_child_in`) + test (failed on the previous code).
3. major, `\?\Volume{GUID}` corrupted by the prefix strip: FIXED (strip only before a drive
   letter) + test (a regression test; Python's resolve() already normalises that form here).
4. major, NUL in the configured path raised ValueError: CONFIRMED by reasoning; FIXED (inert) + test
   (failed on the previous code).
5. major, fail-open when the footage path cannot be resolved: REJECTED with citation: claim 3
   requires the guard never to fail a run merely because footage is unavailable; the fallback still
   compares the absolute spelling and file identity.
6. major, outer run reads the real config: REJECTED, as 1a item 3. Test-module docstring says what
   it covers.
7. minor, uncached candidates over-refuse: KEPT by design, as 1a item 5.

Per the brief: one round; the fixes made after round 1b were not re-reviewed.
