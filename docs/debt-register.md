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
| DR-6 | 2026-10-15 | WP0.2 accept (Codex B2 major, out of scope) | A truncated JPEG/HEIC with an intact header is inventoried as a success row (no pixel decoding by brief). `size_bytes` is in every row. | An inventory run while the footage download is incomplete; or any package that reads photo pixels (it must validate the file itself). | OPEN |
| DR-7 | 2026-10-15 | WP0.2 accept | HEIC `orientation` column is the EXIF value, not derived from the container `irot`; Apple files carry both and agree. | A non-Apple HEIC in the footage. | OPEN |
| DR-8 | 2026-10-15 | WP0.2 accept (B2 minor) | A size-0 ISOBMFF top-level box before `meta` yields a graceful "HEIF rotation unreadable" note. | A real file producing that note. | OPEN (graceful; low) |
| DR-9 | 2026-10-15 | WP0.2 accept | The `footage` skip reason in `tests/conftest.py` (WP0.1) says "not configured" when the config exists but the folder is absent. Cosmetic. | The next package that edits `tests/conftest.py`. | OPEN |
| DR-10 | 2026-10-15 | WP0.2 accept (out of envelope) | Inventory CSV cells are not neutralised against spreadsheet formula injection from hostile file names (the owner's own camera files). | Footage from an untrusted source. | OPEN (out of envelope) |
| DR-11 | 2026-10-15 | WP1.1 author return (orchestrator Q2) | The prototype's input reader (Pillow 12.3) reads 16-bit RGB at 8-bit precision (run.py warns and continues) and cannot read HEIC (pillow-heif not granted to WP1.1). | WP1.3/WP1.4 commissioning: that brief picks the 16-bit frame reader (N13-licensed) and decides whether pillow-heif extends to the prototype. Owner: CHARC. | OPEN |
| DR-12 | 2026-10-15 | WP1.1 author return (orchestrator Q3) | Codex cites a 3C mask kernel of 20 from the 3C paper (pp. 2657-58); unverified (no PDF in the repo). The prototype keeps mask smoothing at 0.01 of the short side. | WP1.3 tuning: verify against the paper and set the default. | OPEN |
