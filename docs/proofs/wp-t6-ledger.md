# WP-T6 cumulative ledger

This package implements AD-30's gate sizing under the FINAL brief at
`docs/briefs/wp-t6-brief.md`, including CHARC ruling `7458b470a82d2dc3`.
The dispatcher runs all footage, GPU and heavy commands. This cell yields at
each required boundary; it does not commit or post to a mailbox.

## Dispatcher depth and tokens

Only dispatcher-supplied figures belong here. A tokens-used footer is not
context depth (HD-1); the dispatcher's last-request input-token reading governs
the evaluation and re-seat lines. No token/depth reading was supplied for turn 1.

| Turn / gate | Tokens-used footer | Last-request input tokens | Context window | Supplied by / disposition |
|---|---:|---:|---:|---|
| Turn 1, rung 0 / W1 script | Pending dispatcher | Pending dispatcher | Pending dispatcher | Fill after this turn; dispatch pace Codex 0.54, not a depth figure |

## Rung 0 facts (2026-10-29)

| Check | Observed result | Evidence / limits |
|---|---|---|
| HEAD | `6ecc4e5174dfd15080cc6fd59d63940839a9b430` | `git rev-parse HEAD`; matches the dispatch base |
| Branch | `wp-t6` | `git branch --show-current` |
| Initial worktree state | Clean; no porcelain output | `git status --porcelain` before writing this ledger |
| Baseline code identity | Empty diff stat | `git diff --stat 8bc927a..HEAD -- src tests tools pyproject.toml`; baseline of record stands |
| Environment sync | Already performed by dispatcher | Dispatch says `.venv` is synced; no new dependency or lock change |
| Installed pytest | `8.4.2` | Imported version only; `work/wp-t6/rung0-facts.json` |
| Configuration | Left untouched | Dispatcher supplied the gitignored local configuration; the cell did not open it |
| Baseline all collection | Incomplete, no count | Sandbox command below produced no stdout/stderr in about five minutes; child stopped by the cell; `EXIT=4294967295` is termination, not a pytest failure verdict |
| Baseline parallel / serial collection | Not run | The sequential collector stopped after its all-collection assertion; both remain requested at the seat |

The attempted collection used the current expressions, `PYTEST_ADDOPTS` unset,
`QT_QPA_PLATFORM=offscreen`, `PYTHONPATH=scripts`, and the dispatched pytest shim:

```text
uv run python -m pytest --collect-only -q --basetemp=work/wp-t6/base-collect-all -p sandbox_mkdir_shim -p no:cacheprovider
```

The child started at about 11:07:31Z and was stopped after the 11:12:30Z reading
(296.125 CPU seconds). Captured runner output and its empty ID list are retained
as `work/wp-t6/base-sandbox-all.log` and `base-sandbox-all.txt`. There is no valid
pytest collection summary, no inferred count, and no asserted collection identity.
The hang's cause is unconfirmed. Collection does execute a module-level
`select_backend("auto")` in `tests/test_prototype_backend.py`; this is an observed
import mechanic, not a diagnosis of the hang. No further GPU probe was run.

The fallback `work/wp-t6/base-collect.sh` runs all three current collections at
the seat, writes separate logs, retains node-ID lines only in
`base-{all,parallel,serial}.txt`, checks each count against pytest's own summary,
then checks duplicates, disjointness and `parallel + serial = all`. Those results
are pending. A baseline collection failure stops the handoff before W1 runs.

## W1 script and validation

`work/wp-t6/w1.sh` is gitignored scratch, not a committed file. It is run from
Git Bash at the worktree root, with `PYTEST_ADDOPTS` unset and headless Qt. Each
item has separate outputs under `work/wp-t6/w1/`; `driver.log` ends in `W1 DONE`
or `W1 STOP <why>`. Its `status.json` records the stage and UTC bounds. Each
measurement stage records free memory before work and refuses less than 5 GiB.
The dispatcher supplies the exclusive window conditions.

The script locates GX011627 only through `find_footage_file`, follows the exact
specified stream-copy flags, and checks 4(a)-(e) before any trim encode. No tag
exception has yet been ruled: the provisional `ALLOWED_TAG_DIFFS` is empty. A tag
diff therefore records its scope and KEY only, fails 4(e), and stops for the
round-0 ruling; the script never invents a metadata exception or changes flags.
Other failed trim checks and a levels/size-chain failure also stop the run.

Location values are removed from probe tag dictionaries before comparison.
Probe documents and packet hashes remain in memory; saved packet results carry
counts and equality status. Non-timecode data is compared as copied packet
prefixes, with pts, duration, size and hash, without decoding telemetry. Raw
subprocess diagnostics and helper exception strings are withheld to prevent
metadata escaping into a log. A failed check records its named status and
privacy-filtered diagnostics; no raw probe document is retained.

The round-trip step measures all six plants from the existing test's own AST
dictionary at 30, 6, 10 and 15 frames. The fresh 30-frame run is necessary for
Q4's measured time-saving and half-margin comparisons. It records both signed
margins (mean minus 1.0, share minus 0.01), both half-margin comparisons and
verdicts for every plant. Selection remains the next turn's round-0 table; no
test count is changed this turn. The single row-10 cProfile run retains its
top 15 cumulative rows plus the bench-module rows from that same profile.

The script removes only its newly created `work/wp-t6/w1-scratch/` tree at exit,
after checking its resolved absolute path. It refuses pre-existing scratch and
asserts scratch is outside footage. The script, reports, summary JSON and
profile text stay; the trim, encoded files, binary profile and pytest temp files
inside scratch are removed. A cleanup failure becomes `W1 STOP`.

Final scratch-script MD5s for this turn:

- `work/wp-t6/w1.sh`: `7e6d01a6a9ce5483a5e44ba254b0c135` (17,356 bytes).
- `work/wp-t6/base-collect.sh`: `7e5b253bec40c5b9e16ecda6c1d931ed`
  (2,641 bytes).

| Validation | Result | Evidence |
|---|---|---|
| Embedded Python compile / LF bytes | PASS | `work/wp-t6/w1-static-check.json` (refreshed after edits) |
| Synthetic location-value removal | PASS | `work/wp-t6/w1-helper-check.json`; a synthetic sentinel value is absent from the filtered document |
| Synthetic matching packet / stream / tag facts | PASS | Same helper check; 4(a)-(e) all PASS |
| Synthetic changed packet hash | Caught by 4(b) | Same helper check; scratch-only helper validation, not W2's real re-encode control |
| Synthetic extra video packet | Caught by 4(b) and 4(c) | Same helper check; not W2's real N+1 control |
| Collection-summary parser | PASS | `work/wp-t6/w1-static-check.json`; plain, fraction and selected-count summary forms checked |
| Bash syntax invocation | Sandbox blocked, not verified | `work/wp-t6/w1-bash-syntax.log`: Git Bash exits 256 with `CreateFileMapping ... Win32 error 5` before parsing; seat-side `bash -n` requested |
| Real footage / GPU / W1 | Not run by cell | Requested below; no measurement claims yet |

Seat-side run request, in order (all redirects are Git Bash):

```bash
bash -n work/wp-t6/base-collect.sh > work/wp-t6/base-collect-syntax-seat.log 2>&1
bash -n work/wp-t6/w1.sh > work/wp-t6/w1-syntax-seat.log 2>&1
bash work/wp-t6/base-collect.sh > work/wp-t6/base-seat-driver.log 2>&1
bash work/wp-t6/w1.sh > work/wp-t6/w1-seat-driver.log 2>&1
```

Continue to each next command only after the preceding command exits zero.
Collection is requested as the rung-0 sandbox fallback (a few minutes, no
measurement claim); W1 requests one exclusive window of about 15 minutes.
Read the collection driver's summary, then W1's final DONE/STOP and its item
summaries. Return those paths to the cell for the round-0 table; do not proceed
to a build.

## Heavy-run ledger

One row per actual heavy run will include start, end, exact command, selected
counts, EXIT, free memory before and evidence paths. Requested runs are explicitly
pending and are not validation results.

| Window | Start / end UTC | Command | Counts / EXIT | Free memory before | Evidence / disposition |
|---|---|---|---|---|---|
| W1 (requested, about 15 min) | Pending dispatcher | `bash work/wp-t6/w1.sh` | Pending | Script records bytes per stage; >= 5 GiB required | `work/wp-t6/w1/`; no real run yet |

## Review-round ledger

No Reviewer A or B round has run. Future rows carry severity counts,
in-envelope/out-of-envelope, NEW/REOPENED, reverts, product-code/test-only fixes,
transport/model evidence and dispatcher-read depth. Reviewer A uses the
Codex-lane Claude pass at FAST tier under Q11; the fill governs convergence.

## Verification loop and turn boundary

Turn 1 examined the script against rung 1, its fixed flags and privacy locks.
Synthetic checks confirmed that the in-memory checker rejects changed packet
bytes and an extra packet, and discards location values. The helper checks are
script validation only; W2's real controls remain pending. An initial multi-path
shell `PYTHONPATH` was replaced with explicit portable Python path entries,
avoiding dependence on Git Bash path-list conversion. The final script compile
and helper checks are repeated after that edit. No product or test code changed.

Pending at handoff: seat-side baseline collections, Bash syntax check, W1 and
its round-0 table/ruling. No build in `tests/` or `pyproject.toml` is authorized
before that ruling. The one tracked change this turn is this ledger; the two
run scripts and their validation evidence remain under gitignored `work/`.
