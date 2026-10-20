# WP2.2 — Accept record (interface module, IF-1 to IF-10)

**Accepted 2026-10-20 by the orchestrator** (generation 3, session
`clearwater-orchestrator-20261019-2346`). Gate per `docs/review-gate-clearwater.md` Part 2.
Tier STRONG.
- Commission: CHARC `9fb52c00bbb58a9b`.
- Brief approval and rulings: CHARC `8d7880255daf7c79`.
- Round-1 ruling: CHARC `b7b012f7c6d5a1e6`.
- Follow-up ruling: CHARC `cda92ceb18e8451a` (`Parameter.nullable`; rotation sign). It is
  mirrored in `docs/architecture.md` at `2a43d3a`, and the `Frame.pts` comment was corrected at
  `597c2df`.
- **From this accept, IF-1 to IF-10 are FROZEN (AD-20).**

| Item | Value |
|---|---|
| Brief | `docs/briefs/wp2.2-brief.md` (DRAFT `020ed86`; FINAL `d3bcdba`). Spec v0.5.3. |
| Base SHA | `d3bcdba` |
| Author heads | `7aac9c5` (Reviewer A converged); `70e554a` (the ONE Reviewer B remediation). |
| Cell and depth | `wp22-cell` (implementer-sonnet-high), one cell, no re-seat. Readings: 0 at dispatch; 148,021 / 36 turns at the round-1 ruling yield; 190,481 / 63 at round 1; 206,440 / 73 at round 2; 217,013 / 80 at return. |
| Merged head | `wp2.2-mc` = `70e554a` rebased onto main `597c2df` (`2a7f092`), plus this record and DR-32. Main fast-forwarded. |
| Byte identity | `git patch-id --stable` = `6e17752afe8799d90f15df10cc54e72d986c79e2` on `d3bcdba..70e554a` and on the B re-run candidate `597c2df..2a7f092`. CHARC held main from B to the merge. |
| Gates on the candidate | `ruff check` clean; `ruff format --check` 56 files; `mypy` strict 39 files clean; full pytest (see below); harness gate 366 OK. |
| Gates on main | Full pytest on main `9a27dc4` (code identical to `b288533`), run by orchestrator generation 4 on 2026-10-20: 892 passed, 1 warning (CuPy "CUDA path could not be detected"), 469 s, exit 0. |
| Reviewer A | gpt-5.6-sol / high, WSL. Converged at R3 (`NO_NEW_CRITICAL_MAJOR`). No reverts. Evidence `clearwater-review-evidence\wp2.2\r1`-`r3`. |
| Reviewer B | Pass 1 on `7d31825`: `NEW_CRITICAL_MAJOR_FOUND` (1 major, 2 minor), with ONE remediation (`70e554a`). Re-run on `2a7f092`: `NEW_CRITICAL_MAJOR_FOUND` (1 major), adjudicated at the gate as NOT BLOCKING (below). |

**Reviewer A rounds:**
- R1, 0/5/4. Five fixed; two rejected (uint8 proxies, as ruled; int accepted for a float
  parameter, documented). Two raised to CHARC and ruled: the nullable gain caps, and the rotation
  sign.
- R2, 0/1/3. The major: the `Frame.pts` docstring had the conversion inverted, copied from the
  section-3 comment, which CHARC then corrected.
- R3, 0/0/1. Converged.

## Reviewer B

**Pass 1** (on `7d31825`). Transcript `clearwater-review-evidence\wp2.2\reviewB\review-B.txt`,
md5 `ad7439d7...`; prompt `e9f87804`; diff `2185c012`.
- Assertions: banner gpt-5.6-sol / high; `^ERROR` 0; footer present; 19 `succeeded in`; VERDICT
  anchored. Every `docs/proofs` mention is an exclusion glob or the brief's own text; there was
  no read.
- Findings:
  - **MAJOR:** non-finite floats were accepted at the dict boundary.
  - **minor:** a `created` tzinfo with `utcoffset() is None` was accepted.
  - **minor:** the stub `closed_form` returned None for an unknown stage.
- All three were fixed in ONE remediation (`70e554a`): a recursive `check_finite` on
  `from_dict`, `to_dict` and `to_json`, the `utcoffset` check, and `ValueError` in the stub. The
  cell's suite on its head: 892 passed.

**Re-run** (on `2a7f092`). Transcript `...\wp2.2\reviewB2\review-B.txt`, md5 `2b217918...`;
stderr `26c68623`; prompt `a7aed0ad`; diff `0ecc3f3c`; `md5s.txt` beside them.
- Assertions: banner; `^ERROR` 0; footer; 21 `succeeded in`; VERDICT anchored. No withheld read:
  the only `docs/proofs` text is an exclusion glob.
- B verified fixes 2 and 3 end to end. It also verified non-finite VALUES refused at every
  depth, and found no signature, field, frozen, protocol, stub, c3-stage, dependency or
  docstring discrepancy.
- **The one finding, a MAJOR as B classed it:** `check_finite` does not examine mapping KEYS, so
  `source={"probe": {float("nan"): 1}}` passes `from_dict` and `to_dict`, and fails later at
  `to_json` with a `ValueError`.

**Adjudication at the gate (orchestrator): NOT BLOCKING; banked as DR-32.** This is the second
blocking B, so it is adjudicated here, per the established practice.
- The trigger needs a crafted non-string key below a mapping whose public type is
  `Mapping[str, Any]`. No in-envelope producer creates one: provenance `source` is built by
  Phase 3 code from a probe summary with string keys.
- The failure is loud (`ValueError` at serialisation), not a silent corruption.
- The related, quieter gap goes with it: `json.dumps` coerces non-string keys such as `1` to
  `"1"`, so the round trip changes. DR-32 assigns both to WP3.15, which owns the provenance and
  settings files: refuse non-string keys at any depth in `to_dict`/`from_dict`.

## Rulings during the package

Recorded in the ledger (`docs/proofs/wp2.2-ledger.md`) with their CHARC message ids:
- round 1 (nine types, annotations, `Settings` defaults png 16 / encoder "auto" / quality
  "standard", the c3 stage list);
- the follow-up (`nullable`, rotation);
- the R2 withheld-glob incident: the reviewer's `rg` printed ledger lines (the already-ruled c3
  table). It was recorded, and the prompt was fixed for R3.

## Open items carried

- WP3.2 declares `red_gain_cap` / `blue_gain_cap` with `nullable=True`.
- WP3.15 owns the settings file paths, `format_version` migration, and DR-32.
- `tools/inventory.py` reports rotation clockwise; IF-5 is counter-clockwise, and the docstring
  says so.
- `ParameterSet` mappings are not deep-frozen (JSON-native values only).
- `Image.__eq__` is unusable on arrays, which is inherent to section 3's frozen dataclass.

## CHARC QA

2026-10-20 ~15:35Z at the CHARC seat: `git patch-id --stable` = `6e17752a` on `d3bcdba..wp2.2`,
`d3bcdba..70e554a` and `597c2df..2a7f092` (match; the main range differs only by the accept
record); review-B.txt md5s `ad7439d7` (pass 1) and `2b217918` (re-run) verify against `md5s.txt`;
DR-32 present; `Parameter.nullable` and the round-1 rulings are in the merged tree
(`src/clearwater/interfaces/method.py:62`); harness gate on main `9a27dc4`: 366 OK (1 skipped).
**DR-32 adjudication CONFIRMED**: a non-string mapping key under `Mapping[str, Any]` cannot come
from any in-envelope producer, `to_json` still fails loudly, and WP3.15 owns the boundary; not
blocking. **QA CONFIRMED.** IF-1 to IF-10 are FROZEN (AD-20) from this accept. The full pytest on
main is generation 4's first act and is recorded by it above.
