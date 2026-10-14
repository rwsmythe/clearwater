# Clearwater -- technical-debt register (CHARC-maintained)

Evidence-based entries, each with its observable signal and the trigger that reopens it
(charter section 4). Paydown is proposed at phase boundaries; the owner commissions it.
Closed items are marked CLOSED, never deleted. Entries are added only from accept records
(banked findings) or from CHARC's own audits; the text of other roles' artifacts is theirs.

| ID | Opened | Source | Entry | Signal / trigger | Status |
|---|---|---|---|---|---|
| DR-1 | 2026-10-14 | WP0.1 accept (Reviewer A r1/r2, B2) | `load_local_config` has no tests for Windows-only path forms (case folding, UNC, drive-relative). Case folding was measured correct at the orchestrator seat. | Any change to the path rule in `tools/local_config.py`; or a bug report involving a UNC or drive-relative path. | OPEN |
| DR-2 | 2026-10-14 | WP0.1 accept | `parse_nvidia_smi` reads the first GPU line only (first-line-only by brief; multi-GPU out of envelope). | A second GPU on the target machine; or any package that selects a GPU by index. | OPEN |
| DR-3 | 2026-10-14 | WP0.1 accept, banked item 3 | Dispatch recipe named a `Claude-Session:` trailer no commit ever carried; bootstrap bring-up block said "no co-author footer". | -- | CLOSED 2026-10-14: recipe and bootstrap now require `Co-Authored-By:` only (practice on every commit on main). |
| DR-4 | 2026-10-14 | WP0.1 accept, banked item 2 | Gate fill recorded codex-cli 0.157.0; live version at the accept was 0.162.1 (banner held). | A banner-format change on the next re-probe. | CLOSED 2026-10-14: fill updated. |
| DR-5 | 2026-10-14 | WP0.1 accept, banked item 1 | Spec section 14.2 / D117 still say the CPU and graphics card are unconfirmed; WP0.1 measured them. Spec text is owner-reserved. | Owner's word on the proposed amendment (decision request 2026-10-14). | OPEN -- awaiting owner |
