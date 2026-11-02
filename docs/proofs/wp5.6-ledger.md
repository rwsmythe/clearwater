# WP5.6 - Trace and turn ledger

## Turn 1

Wrote the complete Phase 5 report DRAFT except gate p5b results, whose
table is a skeleton for turn 2. Status names the two owner fields:
V2 / CP5 and N6. Filled the V-matrix from accepted records, D111 witness,
register through DR-115, N6 proposal, prune candidates and next actions.

FILES CHANGED:
- docs/reports/wp5.6-gate-report.md
- docs/proofs/wp5.6-ledger.md

Depth at turn-1 end: 165,453 input tokens of a 258,400 window (driver footer, turn 1, 21:12Z start; read at the yield)

Reviewer A is replaced by this trace table plus the orchestrator's
independent fact-check (brief Review nets). Reviewer B is the Claude pass
at the orchestrator's seat after gate transfer; neither external check
is claimed to have run in this turn.

### Verification-loop record

| Suspected / observed | Independent confirmation / disposition |
|---|---|
| Brief calls WP-D112's 2,635 s the last fullclip figure | Confirmed newer WP-DR113 record: 1,595 s (accept :28). Both retained with chronology; no source edited. |
| WP5.3 accept says 117 done / 9 failed, current report says 126 / 0 | Confirmed historical versus post-WP-D112 witness states (accept :23; current report :3). Current report used, historical record disclosed. |
| GUI near 11.7-11.8 could be read as measured | Brief :32 supplies proposal projection; WP5.2 :84-91 explicitly does not manufacture a new GUI rate. Qualified as proposal projection. |
| Orphan size and report-worktree sizes missing from inventory | Confirmed absence of subtree/wp5.6r size rows. Marked UNTRACED; no scan or estimate. |
| DR-44 status heading conflicts with completed-looking subparts | Register :53 still OPEN; (a)/(b) ADDRESSED, (c) CLOSED/reconfirmed. Carried as not wholly CLOSED without inventing residual work. |
| Register counts | Final status-column classification gives 64 not wholly CLOSED + 51 wholly CLOSED = 115; all row ids carried. |
| Possible premature source closure/paydown | DR-25(3), DR-99 and partial rows preserved as registered. Report does not close debt. |

Final document checks: report 32,582 bytes and ledger initially 49,173
bytes; both 0 CR and 0 non-ASCII bytes. Report relative file links: 0
missing. Acceptance ids: 20 (V1-V18, N10 / D92, D91). OPEN/partial table:
64 rows, 64 unique ids. Trace table: 327 rows. Gate-pending marker and
dispatcher depth placeholder present. Read-only git status lists exactly
the two owned NEW files. Final trailing-whitespace/table and byte checks
are run after this ledger entry; no product gate result is implied.
No pytest, FFmpeg, GPU tool, tools instrument, uv sync, du, ruff or mypy
was run. No footage folder or other worktree content was read.
No commit, mailbox post, deletion, dependency/interface/product edit.
Only read-only git metadata/listing commands accompanied source reads.

### UNTRACED / handoff items

- V-S orphan subtree size: brief says about 2 GB; inventory only supplies
  enclosing orch-g33 3.1G. Need a seat-supplied subtree measurement to fill.
- wp5.6r whole/work sizes: inventory lists membership/KEEP but no size.
- Nonempty work folders do not establish whether outputs are unarchived.
  Report says archive verification required; it makes no unsupported
  archive-completeness claim.
- Gate files arrive for turn 2; gate results intentionally not asserted.
- Source-state differences above are chronology/wording discrepancies,
  not evidence that the historical measurements themselves disagree.
- Ledger rows below cite source claims as records, not independently
  re-executed product behaviour. Main moved during read-only worktree
  listing; the report remains pinned to the commissioned gate snapshot.

## Turn 2

Filled Result 1 from the transferred p5b summary and leg logs: GREEN,
with head, start/end, free disk, literal count lines, timing scopes and
skip reasons. Kept all three fullclip comparisons and added WP-DR113's
serial comparison. The report remains DRAFT with the same two owner fields.

FILES CHANGED:
- docs/reports/wp5.6-gate-report.md
- docs/proofs/wp5.6-ledger.md

Depth at turn-2 end: 199,699 input tokens of a 258,400 window (driver footer, turn 2; read at the yield)

### Fact-check dispositions

The following severities are the cell's classifications of the returned
fact-check items, not a Reviewer B verdict. All three are NEW, in-envelope
and text-bearing; no reverts, product-code or test changes. Reviewer B
remains at the orchestrator's seat after this turn.

| Item | Severity | Confirmation | Disposition |
|---|---|---|---|
| FC-1 | ADVISORY | New inventory :263 measures V-S orphans 3.0G; :264 supplies wp5.6r whole 17M, work under 1M (inputs only at measurement). | ACCEPTED / FIXED: replaced missing size cells and traces; retained earlier about-2-GB estimate as superseded, not current measurement. |
| FC-2 | MINOR | Summary :11 serial wall 2,046 s exceeds register :95 threshold about 25 min (1,500 s) by 546 s; WP-DR113 accept :27 gives 2,036 s. | ACCEPTED / FIXED: trigger explicitly FIRES, with comparison; paydown remains CHARC's / the owner's. |
| FC-3 | MINOR | Register :34 assigns the staged >=182-frame run to WP5.2. Case-insensitive search for DR-25, staged, staging, or a 182-frame-run phrase finds no match in WP5.2 report/accept; accept commit 2da5d0c7 is already recorded. | ACCEPTED / FIXED: assignment is historical; accepted without evidence; disposition and next action CHARC's. No new owner decision or register edit. |

Fact-check totals: 0 critical, 0 major, 2 minor, 1 advisory; 3 NEW,
0 REOPENED; 3 in-envelope, 0 out; 0 reverts; documentation-only fixes.
The dispatcher independently confirmed the other listed turn-1 facts
(open/closed row sets, V7/V15/V16/D111, pack counts/accept, newer fullclip)
in the turn-2 dispatch. This is not a claim that Reviewer B has run.

### Verification-loop record and limits

The gate summary and final log lines agree on exits and counts. The
summary separately records enclosing product-leg wall seconds and the
pytest count-line durations; both scopes are retained, never substituted.
The harness records test runtime only. Static and separate collection /
harness enclosing wall times are not supplied; they remain UNTRACED.
Harness skip count is 1 but its nonverbose log supplies no name/reason;
that reason remains UNTRACED. Product skip reasons were checked directly
from the -rs lines, with source paths reduced to names in the report.

Both turn-1 size gaps are RESOLVED by the added inventory block. The
turn-1 historical handoff list above is preserved as history, not current
missing data. The report makes no archive-completeness claim. Gate
results were read, not rerun; all execution and path locks remain honored.
The FC-3 search first matched an unrelated numeric substring with a broad
182 expression; a word/phrase-bounded search rejected that false positive
and confirmed no staged-run/DR-25 mention in either source.

Document validation after these edits checks ASCII/LF/final newline,
trailing whitespace, Markdown table columns, relative links, acceptance
ids, unchanged register-row coverage, two owner fields, and owned-file
scope. No pytest, FFmpeg, GPU/tool instrument, du, uv sync, static runner,
commit, mailbox post, deletion or write outside the two owned files.

Validation result: PASS for ASCII, LF, final newline, no trailing
whitespace, consistent table columns, and 0 missing relative file links.
Acceptance coverage remains 20 unique ids; the 64 OPEN/partial row ids
are identical to turn 1. Gate-transfer fields, FC-1/2/3 text, the two
pending owner fields and dispatcher depth placeholder are present; stale
gate-pending and missing-size cells are absent. Trace table now has 377
rows (50 added this turn; affected inherited rows updated). git diff
--check passed; status shows only the two owned files modified. Git emits
an autocrlf advisory, but direct byte checks confirm both current files
contain 0 CR and 0 non-ASCII bytes. No new text issue was found by this
document-check pass; this is not an independent Reviewer B verdict.

## Turn 3

Final bounded turn: folded the N6 ruling and all eight Reviewer B items.
The report cites spec v0.5.8 and ruling commit 1db84842; N6 is SET at
about 12 min/min at 4K and V16 is PASS. CP5 / V2 is the only
DRAFT-pending field. The gate remains the recorded p5b run, not a rerun.

FILES CHANGED:
- docs/reports/wp5.6-gate-report.md
- docs/proofs/wp5.6-ledger.md

Depth at turn-3 end: 49,258 input tokens (driver footer, turn 3, as reported; turn 2 read 199,699: the footer figure fell, read at the yield; final turn)

Reviewer B: Claude opus, orchestrator's seat, verdict
NO_NEW_CRITICAL_MAJOR; 0 critical, 0 major, 4 minor, 4 advisory.
Source: work/wp5.6/review-B.txt:3; :26-63; model/seat from turn-3 dispatch.
All 8 findings NEW, 0 REOPENED; 6 in the report envelope, 2 on the brief;
0 reverts; 0 product-code or test-only fixes. All in-envelope changes are
documentation changes. The brief findings are noted without editing it.

| B item | Severity / classification | Confirmation and final disposition |
|---|---|---|
| MINOR-1 | MINOR, report, text-bearing | Confirmed the serial series against each named record. Added all seven walls and CHARC condition d4224524 beside DR-86; next action CHARC's (DR row or DR-86 paydown), no proposed remedy. |
| MINOR-2 | MINOR, report, text-bearing | Confirmed historical real-sized still nodes skipped at WP5.1 and again at p5b. Named both nodes and cited WP4.3 crop mean/p99 figures in [0,1] as historical still k>1 evidence. |
| MINOR-3 | MINOR, report, text-bearing | Replaced still-to-run sentence with actual Claude opus verdict and 4 MINOR + 4 ADVISORY folded in turn 3. |
| MINOR-4 | MINOR, report, text-bearing | Added all listed inventory entries, including five zero folders. charc-g12/g13 and charc-qa* explicitly require CHARC's word. |
| ADVISORY-5 | ADVISORY, report, text-bearing | Added held/free item walls 240.078 / 242.110 s beside shell 243.764 / 243.268 s; distinct scope/order and Battle.net write overlap disclosed. |
| ADVISORY-6 | ADVISORY, report, text-bearing | D91 now says the source name without a path (WP5.1 :322). |
| ADVISORY-7 | ADVISORY, brief, out of report envelope | NOTED: brief asks for WP5.1 V3 chapter wording, absent there. Report already sources chapter deferral to spec D64/change note; no report change for this item, no brief edit. |
| ADVISORY-8 | ADVISORY, brief, out of report envelope | NOTED: brief's two commits between gate/base is off; git rev-list 1934bcbb..ac033be7 has one, ac033be7. Report already states the one-document difference correctly; no report/brief change. |

### Verification-loop record and remaining gaps

N6 ruling independently grounded in charc-n6-ruled.txt:14-20, spec
v0.5.8 :18/:145/:455/:498, AD-21 :30, and commit 1db84842. WP5.2 rates
10.888984 and 10.779005 are below the set 12; no new timing was run.
Review B also independently confirmed the gate, counts, arithmetic,
register set/closures, D111 and prune figures (review-B.txt:5-24).
Reviewer B was withheld the ledger (review-B.txt:61); this turn does not
claim an independent review of this ledger or of the final cleanup text.

The unchanged UNTRACED items are static wall times, separate enclosing
walls for collection/harness, and the harness skip's name/reason. Their
absence is explicit in the supplied summary/nonverbose log. No source
gap is filled by an estimate, and no archive-completeness claim is made.

New source disagreement, out of owned files: spec v0.5.8 :18/:145 labels
GX011627 as 4K 60, while WP5.2 report :61-62 records GX011627 681 frames
and all W52-1 rows at 30000/1001 fps. Both sides were read this turn.
This report carries the rates of record and does not copy that frame-rate
label; the source correction is CHARC's, not made by this package.

The branch was rebased onto main 1db84842 before this turn (dispatch);
prior implementation commits are b81e32c8 / 068f7636, content unchanged.
Earlier turn sections remain history, including the formerly pending N6
field. Inherited spec anchors refer to the pre-v0.5.8 snapshot at
ac033be7; updated current claims below cite v0.5.8 line anchors explicitly.

Final validation checks ASCII/LF, whitespace, tables, relative links,
all acceptance ids, unchanged register row coverage, current N6/CP5 and
review status, new trace coverage and two-file scope. No pytest, FFmpeg,
GPU/tool instrument, du, uv sync, static runner, commit, mailbox post,
deletion, footage read or other-worktree content read was performed.

Validation result: PASS. Both files have 0 CR and 0 non-ASCII bytes,
final LF, no trailing whitespace and consistent Markdown table columns.
Report relative links: 0 missing. Acceptance coverage: 20 unique ids;
register coverage: the same 64 OPEN/partial ids as turn 2. Trace table:
426 rows (49 added this turn, inherited current claims updated). Current
N6/CP5/B claims and all 8 B dispositions are present; stale report text
is absent. git diff --check passed and only the two owned files changed.
Git's autocrlf advisory does not describe the current bytes, checked
directly above. Final byte/diff checks follow this ledger-only addition.

## Trace table

One row per acceptance disposition, register row, inventory figure or
other report claim; expanded numeric witnesses are separately listed.
Inherited line anchors refer to the turn-1 source snapshot; turn-2 source
additions and the gate transfer are identified below. A shorthand :N after
a file means another line in that same file. Source ranges identify a
bounded table/section; no source logs were rerun.

| Report section | Claim (short) | Source file:line or commit | Checked how |
|---|---|---|---|
| Status | DRAFT pending CP5 / V2 only; N6 SET, CHARC finalises after CP5 | work/wp5.6/charc-n6-ruled.txt:20; docs/underwater-correction-spec.md:145; :455; :498; commit 1db84842 | read; turn-3 dispatch |
| Status / turn3 | N6 SET about12min/min; CP5/V2 only DRAFT-pending | work/wp5.6/charc-n6-ruled.txt:20; docs/underwater-correction-spec.md:145; :455; :498; commit 1db84842 | read |
| Status / turn3 | Spec v0.5.8 on main1db84842; text-only ruling | docs/underwater-correction-spec.md:5; :18; work/wp5.6/charc-n6-ruled.txt:18; commit 1db84842 | read; git show --stat 1db84842 |
| Status / B | Claude opus at orchestrator seat; NO_NEW_CRITICAL_MAJOR; 4 MINOR +4 ADVISORY foldedturn3 | work/wp5.6/review-B.txt:3; :26-63; turn-3 dispatch | read; dispatch (model/seat) |
| 1 / B-M1 | WP-T6 serial wall 1389.24s | docs/reports/wp-t6-gate-sizing.md:475 | read |
| 1 / B-M1 | WP5.1 serial wall 2039s | docs/proofs/wp5.1-accept.md:27 | read |
| 1 / B-M1 | w53 serial wall 2752s | docs/proofs/wp5.3-accept.md:32 | read |
| 1 / B-M1 | WP-D112 serial wall 2760s | docs/proofs/wp-d112-accept.md:27 | read |
| 1 / B-M1 | WP5.2 serial wall 1974s | docs/proofs/wp5.2-accept.md:35 | read |
| 1 / B-M1 | WP-DR113 serial wall 2036s | docs/proofs/wp-dr113-accept.md:27 | read |
| 1 / B-M1 | p5b serial wall 2046s | work/wp5.6/gate/summary.txt:11 | read |
| 1 / B-M1 | CHARC d4224524: D112 near2000s =load; repeatedslowtime -> DRrow at Phase5 gate | docs/proofs/wp5.3-accept.md:32 | read |
| 1 / B-M1 | D1122760s repeats w532752s; condition due beside firedDR86, CHARC disposition | docs/proofs/wp-d112-accept.md:27; docs/proofs/wp5.3-accept.md:32; docs/debt-register.md:95; turn-3 dispatch MINOR-1 | read; facts only |
| Next / B-M1 | CHARC action: disposition DRrow or DR86paydown, none commissioned by report | docs/proofs/wp5.3-accept.md:32; docs/debt-register.md:95; turn-3 dispatch MINOR-1 | read |
| 2 / B-M2 | Named real-sized shell stillnode: test_v8_photo_k_above_1_on_real_sized_content, 1skip at WP5.1 | docs/reports/wp5.1-acceptance.md:118 | read |
| 2 / B-M2 | Named methodnode: test_v8_preview_against_the_downscaled_export, 8skips in WP5.1 matrix | docs/reports/wp5.1-acceptance.md:121 | read |
| 2 / B-M2 | p5b real-sized legs skipped again for archived frames | work/wp5.6/gate/serial.log:1910-1913; docs/proofs/wp-dr113-accept.md:27 | read |
| 2 / B-M2 | WP4.3 historical crop k2mean0.00117, p990.00459 in[0,1] | docs/reports/wp4.3-application-wiring.md:165-169 | read |
| 2 / B-M2 | WP4.3 historical crop k4mean0.00156, p990.0146 in[0,1] | docs/reports/wp4.3-application-wiring.md:165-169 | read |
| 2 / B-M2 | Historical crop within still mean1/255, p992/255k2,4/255k4 limits | docs/reports/wp5.1-acceptance.md:247-249; docs/reports/wp4.3-application-wiring.md:169 | read; .00117/.00156<1/255; .00459<2/255; .0146<4/255 |
| 2 / V16 SET | 10.888984 (10.89 rounded) and10.779005 (10.78) below SET12: PASS | docs/reports/wp5.2-performance-memory.md:78-79; docs/underwater-correction-spec.md:498; commit 1db84842 | read; numeric comparison |
| 2 / V16 SET | 5.3K40.331778 best effort, outside4K target | docs/reports/wp5.2-performance-memory.md:82; docs/underwater-correction-spec.md:145; :455 | read |
| 2 / B-A6 | D91 source name without a path | docs/reports/wp5.1-acceptance.md:322 | read |
| 4 / B-A5 | Held itemwall240.078s, free242.110s (rounded) | docs/reports/wp5.2-performance-memory.md:157 | read |
| 4 / B-A5 | Held/free shell243.764/243.268s, approximately4m4s/4m3s; reversed ordering vs item scope | docs/reports/wp5.2-performance-memory.md:157-159 | read; compare separate scopes |
| 4 / B-A5 | Battle.net at least9x1GB writes15:04-15:11Z overlap both exports15:04-15:12Z | docs/reports/wp5.2-performance-memory.md:320(a) | read |
| 4 / B-A5 | Held/free walls are DR114 evidence, not N6figures | docs/reports/wp5.2-performance-memory.md:320(a) | read |
| 5 / SET | Owner answered15f100ae on2026-11-02~21:30Z: Concur with12 | work/wp5.6/charc-n6-ruled.txt:14; docs/underwater-correction-spec.md:18; :145 | read |
| 5 / SET | N6 wording set about12min/min end-to-end4K recordingmodes;5.3K supportedbest-effort | docs/underwater-correction-spec.md:145; :455; work/wp5.6/charc-n6-ruled.txt:16; commit 1db84842 | read |
| 5 / SET | AD21 CLOSED-SET; interim25 historical | docs/decisions.md:30; docs/underwater-correction-spec.md:145; :455; commit 1db84842 | read |
| 5 / SET | SetV16 at specsection11:498 | docs/underwater-correction-spec.md:498 | read |
| 5 / SET | GUI11.7-11.8 indicative projection retained as supportingruling evidence | docs/underwater-correction-spec.md:18; :145; docs/reports/wp5.2-performance-memory.md:84-91 | read |
| 5 / history | Alternatives15,retain25,clean-host remeasure historical; ownerchose12 | docs/briefs/wp5.6-brief.md:32; work/wp5.6/charc-n6-ruled.txt:14 | read |
| 6 / B-M4 | work/charc-g12 140K | work/wp5.6/prune-inventory.txt:115 | read |
| 6 / B-M4 | work/charc-g13 91K | work/wp5.6/prune-inventory.txt:109 | read |
| 6 / B-M4 | work/charc-qa-wp1.3.log 1.0K | work/wp5.6/prune-inventory.txt:7 | read |
| 6 / B-M4 | work/charc-qa-wpt1.log 1.0K | work/wp5.6/prune-inventory.txt:8 | read |
| 6 / B-M4 | work/wp3.5-bt601.mp4 96K | work/wp5.6/prune-inventory.txt:110 | read |
| 6 / B-M4 | work/g28-seat-r31-green 128K | work/wp5.6/prune-inventory.txt:113 | read |
| 6 / B-M4 | work/g28-seat-r31-red 4.0K | work/wp5.6/prune-inventory.txt:48 | read |
| 6 / B-M4 | work/claude_usage_probe.py 4.0K | work/wp5.6/prune-inventory.txt:46 | read |
| 6 / B-M4 | work/orch-g20 0 | work/wp5.6/prune-inventory.txt:2 | read |
| 6 / B-M4 | work/pytest-main-9ae9bf9-benchnode 0 | work/wp5.6/prune-inventory.txt:3 | read |
| 6 / B-M4 | work/wp4.2-c3-p2 0 | work/wp5.6/prune-inventory.txt:4 | read |
| 6 / B-M4 | work/wp4.2-rebase-check2 0 | work/wp5.6/prune-inventory.txt:5 | read |
| 6 / B-M4 | work/wp4.4-seat 0 | work/wp5.6/prune-inventory.txt:6 | read |
| 6 / B-M4 | charc-g12/g13 and charc-qa* need CHARCword | docs/proofs/prune-2026-10-29.md:54; turn-3 dispatch MINOR-4 | read; dispatch |
| Ledger / B-A7 | Brief's requested WP5.1 V3chapterwording absent; reportuses specdeferral correctly | work/wp5.6/review-B.txt:57; docs/underwater-correction-spec.md at ac033be7:21; :102 | read; NOTED, no report change |
| Ledger / B-A8 | Only1commit1934bcbb..ac033be7, not2 asbriefsays | work/wp5.6/review-B.txt:59; commit ac033be7 | git rev-list --count; git log |
| Ledger / sourcegap | MINOR out-of-scope: specv0.5.8 callsGX0116274K60; W52 reportall30000/1001fps | docs/underwater-correction-spec.md:18; :145; docs/reports/wp5.2-performance-memory.md:61-62 | read; disclosed to CHARC, no source edit |
| Status / review | p5b GREEN; FC-1..FC-3 dispositioned; Reviewer B NO_NEW_CRITICAL_MAJOR, 4 MINOR + 4 ADVISORY, folded turn 3 | work/wp5.6/gate/summary.txt:2 through :13; work/wp5.6/review-B.txt:3; :63 | read; turn-3 dispatch (Claude opus, seat) |
| 1 / p5b | Head 1934bcbb | work/wp5.6/gate/summary.txt:1 | read |
| 1 / p5b | Start 20:57:01Z, 2026-11-02 | work/wp5.6/gate/summary.txt:1; report status date / turn-2 dispatch | read |
| 1 / p5b | C: free at start 57G | work/wp5.6/gate/summary.txt:1; turn-2 dispatch (volume) | read |
| 1 / p5b | End 22:06:38Z | work/wp5.6/gate/summary.txt:14 | read |
| 1 / p5b | C: free at end 52G | work/wp5.6/gate/summary.txt:14; turn-2 dispatch (volume) | read |
| 1 / static | ruff exit 0; All checks passed! | work/wp5.6/gate/summary.txt:2; work/wp5.6/gate/ruff.txt:1 | read |
| 1 / static | format exit 0; 311 files already formatted | work/wp5.6/gate/summary.txt:3; work/wp5.6/gate/format.txt:1 | read |
| 1 / static | mypy exit 0; Success: no issues found in 156 source files | work/wp5.6/gate/summary.txt:4; work/wp5.6/gate/mypy.txt:1 | read |
| 1 / static | Static wall times UNTRACED, absent from supplied authority | work/wp5.6/gate/summary.txt:2 through :4 | read; no duration supplied |
| 1 / collection | all exit 0; literal count line: 7877 tests collected in 3.14s; ids/unique 7877 | work/wp5.6/gate/summary.txt:5 | read |
| 1 / collection | all reported collection time 3.14s; not enclosing wall | work/wp5.6/gate/summary.txt:5 | read |
| 1 / collection | parallel exit 0; literal count line: 6598/7877 tests collected (1279 deselected) in 3.12s; ids/unique 6598 | work/wp5.6/gate/summary.txt:6 | read |
| 1 / collection | parallel reported collection time 3.12s; not enclosing wall | work/wp5.6/gate/summary.txt:6 | read |
| 1 / collection | serial exit 0; literal count line: 1272/7877 tests collected (6605 deselected) in 3.10s; ids/unique 1272 | work/wp5.6/gate/summary.txt:7 | read |
| 1 / collection | serial reported collection time 3.10s; not enclosing wall | work/wp5.6/gate/summary.txt:7 | read |
| 1 / collection | fullclip exit 0; literal count line: 7/7877 tests collected (7870 deselected) in 3.20s; ids/unique 7 | work/wp5.6/gate/summary.txt:8 | read |
| 1 / collection | fullclip reported collection time 3.20s; not enclosing wall | work/wp5.6/gate/summary.txt:8 | read |
| 1 / collection | Union 7877; duplicates 0; difference versus all 0; 6598+1272+7=7877 | work/wp5.6/gate/summary.txt:5 through :9 | read; arithmetic |
| 1 / collection | Separate enclosing wall UNTRACED | work/wp5.6/gate/summary.txt:5 through :9 | read; only collection-reported times supplied |
| 1 / parallel | exit 0; 6597 passed, 1 skipped, 5 warnings in 512.86s (0:08:32) | work/wp5.6/gate/summary.txt:10; work/wp5.6/gate/parallel.log:112 | read |
| 1 / parallel | enclosing wall 515s; pytest duration separately retained | work/wp5.6/gate/summary.txt:10 | read |
| 1 / serial | exit 0; 1261 passed, 11 skipped, 6605 deselected, 1 warning in 2041.95s (0:34:01) | work/wp5.6/gate/summary.txt:11; work/wp5.6/gate/serial.log:1914 | read |
| 1 / serial | enclosing wall 2046s; pytest duration separately retained | work/wp5.6/gate/summary.txt:11 | read |
| 1 / fullclip | exit 0; 7 passed, 7870 deselected, 1 warning in 1568.04s (0:26:08) | work/wp5.6/gate/summary.txt:12; work/wp5.6/gate/fullclip.log:174 | read |
| 1 / fullclip | enclosing wall 1569s; pytest duration separately retained | work/wp5.6/gate/summary.txt:12 | read |
| 1 / harness | exit 0; Ran 382 tests in 21.664s OK (skipped=1) | work/wp5.6/gate/summary.txt:13; work/wp5.6/gate/harness.txt:14; :16 | read |
| 1 / harness | 21.664s supplied test runtime; enclosing wall UNTRACED | work/wp5.6/gate/summary.txt:13; work/wp5.6/gate/harness.txt:14 | read; no enclosing duration supplied |
| 1 / skips | Parallel 1 swscale yuvj full-range refusal, test_color_roundtrip.py:123 | work/wp5.6/gate/parallel.log:111 | read |
| 1 / skips | Serial 1 generic absent look-check frame at test_app_v8_v18.py:134 | work/wp5.6/gate/serial.log:1910 | read |
| 1 / skips | Serial 5 absent GX011625_0024.925.png method cases | work/wp5.6/gate/serial.log:1911 | read |
| 1 / skips | Serial 4 absent GX011625_0114.648.png method cases | work/wp5.6/gate/serial.log:1912 | read |
| 1 / skips | Serial 1 absent GX011625_0024.925.png WP4.1 case; absent-frame total 11 | work/wp5.6/gate/serial.log:1913; :1910 through :1912 | read; 1+5+4+1=11 |
| 1 / skips | Product skips standing; look-check frames archived to D: | docs/proofs/wp-dr113-accept.md:26; :27; docs/proofs/prune-2026-10-29.md:32 | read |
| 1 / skips | Fullclip 0 skipped; all 7 pass | work/wp5.6/gate/summary.txt:12; work/wp5.6/gate/fullclip.log:174 | read |
| 1 / skips | Harness 1 skip, name/reason UNTRACED in nonverbose log | work/wp5.6/gate/harness.txt:12 through :16; work/wp5.6/gate/summary.txt:13 | read; no skip-detail line |
| 1 / comparison | p5b 1569s near WP-T6 about 26min / reported W4 1556.05s | work/wp5.6/gate/summary.txt:12; docs/reports/wp-t6-gate-sizing.md:335 | read; scopes stated |
| 1 / comparison | p5b fullclip 1066s shorter than D112 2635s | work/wp5.6/gate/summary.txt:12; docs/proofs/wp-d112-accept.md:28 | read; 2635-1569=1066 |
| 1 / comparison | p5b fullclip 26s shorter than DR113 1595s | work/wp5.6/gate/summary.txt:12; docs/proofs/wp-dr113-accept.md:28 | read; 1595-1569=26 |
| 1 / comparison | WP-DR113 serial 2036s, alongside WP-T6 1389.24s | docs/proofs/wp-dr113-accept.md:27; docs/reports/wp-t6-gate-sizing.md:475 | read |
| 1 / FC-2 | DR-86 trigger fires: phase-end 2046s > about25min=1500s, 546s excess | docs/debt-register.md:95; work/wp5.6/gate/summary.txt:11 | read; arithmetic |
| 1 / FC-2 | Suite-cost paydown remains CHARC/owner, no commissioning/row by report | docs/debt-register.md:3; :95; docs/briefs/wp5.6-brief.md:16; :17 | read |
| 6 / FC-1 | Added inventory measurement time 2026-11-02T21:22Z | work/wp5.6/prune-inventory.txt:262 | read |
| 6 / FC-1 | V-S orphans 3.0G measurement supersedes earlier about2GB estimate | work/wp5.6/prune-inventory.txt:263; docs/briefs/wp5.6-brief.md:34 | read |
| 6 / FC-1 | wp5.6r whole 17M | work/wp5.6/prune-inventory.txt:264 | read |
| 6 / FC-1 | wp5.6r work under1M, wp5.6 inputs only at measurement | work/wp5.6/prune-inventory.txt:264 | read |
| 6 / keep | Gate completed; gate evidence KEEP until acceptance | work/wp5.6/gate/summary.txt:14; work/wp5.6/prune-inventory.txt:256 | read |
| 4 / FC-3 | DR-25(3) register assigns staged >=182-frame run to WP5.2, still open | docs/debt-register.md:34 | read |
| 4 / FC-3 | WP5.2 accepted at 2da5d0c7 without staged-run evidence in either report/accept | docs/reports/wp5.2-performance-memory.md; docs/proofs/wp5.2-accept.md; commit 2da5d0c7 | read; bounded rg -n -i query returns no match; turn-2 fact-check confirms |
| Next / FC-3 | CHARC action to reconcile assignment, not new owner decision | docs/debt-register.md:1; :4; :34; turn-2 dispatch FC-3 | read; dispatch |
| Status | Report date 2026-11-02; no release acceptance | docs/briefs/wp5.6-brief.md:3; :18 | read |
| Status | Spec v0.5.8 and section-11 / N1-N13 scope; ruling main 1db84842 | docs/underwater-correction-spec.md:5; :18; CLAUDE.md:8; work/wp5.6/charc-n6-ruled.txt:18; commit 1db84842 | read |
| Status | AMD Ryzen 9 7940HS | docs/reports/wp1.6-gate-report.md:10 | read |
| Status | RTX 4070 Laptop 8 GB | docs/reports/wp1.6-gate-report.md:10 | read |
| Status | Windows 11 | docs/reports/wp1.6-gate-report.md:11 | read |
| Status | Owner best effort, 2026-10-19; shared non-idle host | docs/reports/wp1.6-gate-report.md:11; docs/reports/wp5.2-performance-memory.md:257 | read |
| Results table | WP5.1 report wp5.1-acceptance.md; accept 0e8f0e00 | docs/proofs/wp5.1-accept.md:3; report pointer; commit 0e8f0e00 | read; git log --oneline -- record |
| Results table | WP5.2 report wp5.2-performance-memory.md; accept 2da5d0c7 | docs/proofs/wp5.2-accept.md:3; report pointer; commit 2da5d0c7 | read; git log --oneline -- record |
| Results table | WP5.3 report wp5.3-review-pack.md; accept 91db201b | docs/proofs/wp5.3-accept.md:3; report pointer; commit 91db201b | read; git log --oneline -- record |
| Results table | WP4.6 report wp4.6-export-process.md; accept bbb4ef3e | docs/proofs/wp4.6-accept.md:3; report pointer; commit bbb4ef3e | read; git log --oneline -- record |
| Results table | WP-D112 report wp-d112-pcm-audio.md; accept 92d9ff77 | docs/proofs/wp-d112-accept.md:3; report pointer; commit 92d9ff77 | read; git log --oneline -- record |
| Results table | WP-DR113 report wp-dr113-v4-pcm.md; accept 6ff6f5d3 | docs/proofs/wp-dr113-accept.md:3; report pointer; commit 6ff6f5d3 | read; git log --oneline -- record |
| Results table | WP-D54 report wp-d54-warning-words.md; accept 4ece5183 | docs/proofs/wp-d54-accept.md:3; report pointer; commit 4ece5183 | read; git log --oneline -- record |
| Status | Reviewer A substitution, orchestrator fact-check, Claude Reviewer B | docs/briefs/wp5.6-brief.md:9 | read |
| 1 | p5b GREEN after transfer; all gate exits 0, no failing node | work/wp5.6/gate/summary.txt:2 through :13 | read; count lines agree with transferred logs |
| 1 | Gate 1934bcbb product-identical to ac033be7; only CHARC state differs | docs/briefs/wp5.6-brief.md:11; commits 1934bcbb / ac033be7 | git diff --name-only 1934bcbb ac033be7 |
| 1 | Phase-end fullclip and disjoint collection identity rule | CLAUDE.md, Conventions, Tests bullet | read |
| 1 | WP-T6 parallel 714 s rounded / 714.41 s | docs/reports/wp-t6-gate-sizing.md:474 | read |
| 1 | WP-T6 serial 1,389 s rounded / 1,389.24 s | docs/reports/wp-t6-gate-sizing.md:475 | read |
| 1 | WP-T6 fullclip about 26 min / 1,556.05 s | docs/reports/wp-t6-gate-sizing.md:335 | read |
| 1 | WP-D112 fullclip 2,635 s; carry comparison, no row | docs/proofs/wp-d112-accept.md:28; :38 | read |
| 1 | Newer WP-DR113 fullclip 1,595 s; brief calls D112 last | docs/proofs/wp-dr113-accept.md:28; docs/briefs/wp5.6-brief.md:24 | read |
| 2 | WP5.1 roster carried at acceptance-id granularity; N10/D91 included | docs/reports/wp5.1-acceptance.md:56; :152; :157; docs/clearwater-implementation-plan.md:373; :375 | read |
| 2 / V1 | PASS: stage correctness on CPU/GPU, both compensation methods, caps, kernels, statistics ordering and edge cases. | docs/reports/wp5.1-acceptance.md:71; :169 | read |
| 2 / V2 | PENDING CP5: owner's preference >=80% and no obvious artifacts (D65); no automated preference oracle. | docs/reports/wp5.1-acceptance.md:91; :177 | read |
| 2 / V3 | PASS: region-based synthetic flicker <=25% of unsmoothed for each measure. No truly static real clip identified; real subjective flicker belongs to V2. Chapter seam deferred with chapter handling to v2 (CP1). | docs/reports/wp5.1-acceptance.md:92; :171; docs/underwater-correction-spec.md:21; :102 | read |
| 2 / V4 | PASS: fixture and real-trim mandatory/required fidelity; best-effort creation-time loss remains DR-111. Raw PCM product check fixed by WP-D112; V4 instrument GREEN on IMG_6731.MOV, 46 items, mandatory/required all SAME, best-effort DIFFERENT 9. | docs/reports/wp5.1-acceptance.md:95; :181; docs/debt-register.md:120; docs/proofs/wp-d112-accept.md:3; docs/proofs/wp-dr113-accept.md:38 | read |
| 2 / V5 | PASS: photo metadata, depth, ICC and orientation; two independent decoders stand in for multiple viewers. Windows Photos/browser viewing remains an optional owner CP5 leg. | docs/reports/wp5.1-acceptance.md:103; :215 | read |
| 2 / V6 | PASS: unsupported/damaged input handling and literal BT.709/limited warning; WP-D54 fixed the export warning. | docs/reports/wp5.1-acceptance.md:106; :187 | read |
| 2 / V7 | PASS against 100 ms longest gap: (a) 18, (b) 19, (c) 39, (d) 56, (e) 48, (f) 50.6 ms. (c)/(e) are WP4.6's accepted figures; its 67 ms batch control does not replace (d). DR-98 CLOSED. | docs/reports/wp5.1-acceptance.md:113; :226; docs/proofs/wp4.6-accept.md:13 | read |
| 2 / V8 | PASS by cited historical crop figures; real-sized still nodes named and skipped in carried gates; AD-11 limits retained | docs/reports/wp5.1-acceptance.md:118; :121; :247; docs/reports/wp4.3-application-wiring.md:165-169; work/wp5.6/gate/serial.log:1910-1913 | read |
| 2 / V9 | PASS within AD-11 pre-encode max 2/255, mean 0.2/255. Runner post-encode is separately characterised at mean <=3.5/255, not proof of the encoder-free bound. | docs/reports/wp5.1-acceptance.md:122; :283 | read |
| 2 / V10 | PASS: numbering, cross-format clashes, existing outputs and sources unchanged. | docs/reports/wp5.1-acceptance.md:125; :323 | read |
| 2 / V11 | PASS: cancellation, crash/disk-full cleanup and next-start leftovers. Deterministic D85 same-file probe is the witness; crash race's allowed not-observable skip was not observed in recorded successful runs. | docs/reports/wp5.1-acceptance.md:131; :326 | read |
| 2 / V12 | Deferred to v2: chapter grouping. | docs/reports/wp5.1-acceptance.md:141; :178 | read |
| 2 / V13 | PASS: preset round trip. | docs/reports/wp5.1-acceptance.md:142; :174 | read |
| 2 / V14 | PASS: all six N5 results with decisions recorded; prototype gate CLOSED 2026-10-20 at CP3. This does not retroactively pass the original prototype speed target. | docs/reports/wp5.1-acceptance.md:143; :256; docs/reports/wp1.6-gate-report.md:3; :16 | read |
| 2 / V15 | Measured peaks meet 16 GB decimal in the recorded cases: synthetic 5.3K 8:7 video tree RSS 5,599,490,048 B (5.599490 GB; 5,340.090 MiB), device 7,085 MiB; synthetic 48 MP PNG16 automatic CPU tree RSS 6,635,884,544 B (6.635885 GB), device 117 MiB; forced CPU RSS 6,168,494,080 B (6.168494 GB). Largest cited owner photo IMG_6690 (24.5 MP HEIC) RSS 1,926,164,480 B GPU / 3,138,392,064 B CPU. D111 witnessed below; supported-photo-resolution choice remains the owner's. | docs/reports/wp5.2-performance-memory.md:101; :111; :112; :113; :114; :115; :124; :130 | read |
| 2 / V16 | PASS against SET N6 about12min/min: 10.888984 cold / 10.779005 sustained below12; 5.3K best effort 40.331778 | docs/reports/wp5.2-performance-memory.md:78; :79; :82; docs/underwater-correction-spec.md:145; :455; :498; commit 1db84842 | read; numeric comparison |
| 2 / V17 | PASS: unchanged reopen skips decode; cache-format mismatch triggers reanalysis. | docs/reports/wp5.1-acceptance.md:146; :174 | read |
| 2 / V18 | PASS: corrected provisional frame precedes completion and updates to smoothed statistics. Real-trim H12 strengthens the prior not-None check; full-clip record remains WP4.3's. | docs/reports/wp5.1-acceptance.md:150; :270 | read |
| 2 / N10 / D92 | PASS: repeated pre-encode pixels on one device bit-identical; CPU/GPU bounds max 2e-3, mean 2e-4 in [0,1]. Encoded-byte identity is recorded, not required. | docs/reports/wp5.1-acceptance.md:152; :287 | read |
| 2 / D91 | PASS: default-on provenance with app version, parameters, source name without a path; disabled comment absent; photo V5 | docs/reports/wp5.1-acceptance.md:157; :320-323 | read |
| 2 / V7 | (a) longest gap 18 ms | docs/reports/wp5.1-acceptance.md:233 | read |
| 2 / V7 | (b) longest gap 19 ms | docs/reports/wp5.1-acceptance.md:234 | read |
| 2 / V7 | (c) longest gap 39 ms | docs/reports/wp5.1-acceptance.md:235; docs/proofs/wp4.6-accept.md:17; :18 | read |
| 2 / V7 | (d) longest gap 56 ms | docs/reports/wp5.1-acceptance.md:236 | read |
| 2 / V7 | (e) longest gap 48 ms | docs/reports/wp5.1-acceptance.md:237; docs/proofs/wp4.6-accept.md:17; :18 | read |
| 2 / V7 | (f) longest gap 50.6 ms | docs/reports/wp5.1-acceptance.md:238 | read |
| 2 | V7 bound 100 ms; batch control 67 ms does not replace 56 | docs/reports/wp5.1-acceptance.md:228; :244; docs/proofs/wp4.6-accept.md:19 | read |
| 2 | V8 exact k=1, mean 1/255, still p99 2/255 k2 and 4/255 k4; video 2.5/255 k2 | docs/reports/wp5.1-acceptance.md:247 | read |
| 2 | V9 max 2/255; mean 0.2/255; postencode mean 3.5/255 | docs/reports/wp5.1-acceptance.md:285; :296; :317 | read |
| 2 | N10 CPU/GPU max 2e-3, mean 2e-4; encoded bytes not required | docs/reports/wp5.1-acceptance.md:287 | read |
| 2 | V3 <=25% each synthetic measure; real flicker owner; chapter seam deferred | docs/reports/wp5.1-acceptance.md:171; docs/underwater-correction-spec.md:21 | read |
| 2 | V4 PCM witness 46 items, mandatory/required SAME, 9 best-effort DIFFERENT | docs/proofs/wp-dr113-accept.md:38 | read |
| 2 | Synthetic 5.3K RSS 5,599,490,048 B / 5.599490 GB / 5,340.090 MiB | docs/reports/wp5.2-performance-memory.md:111; :48 | read |
| 2 | Synthetic 5.3K graphics peak 7,085 MiB | docs/reports/wp5.2-performance-memory.md:111 | read |
| 2 | 48 MP automatic CPU RSS 6,635,884,544 B / 6.635885 GB; graphics 117 MiB | docs/reports/wp5.2-performance-memory.md:112 | read |
| 2 | 48 MP forced CPU RSS 6,168,494,080 B / 6.168494 GB | docs/reports/wp5.2-performance-memory.md:113 | read |
| 2 | Owner IMG_6690 24.5 MP; GPU-route RSS 1,926,164,480 B | docs/reports/wp5.2-performance-memory.md:114 | read |
| 2 | Owner IMG_6690 CPU-route RSS 3,138,392,064 B | docs/reports/wp5.2-performance-memory.md:115 | read |
| 2 | RAM threshold 16 GB decimal; supported photo size choice remains owner's | docs/reports/wp5.2-performance-memory.md:106; :130 | read |
| 2 | V16 cold median 10.888984 min/min | docs/reports/wp5.2-performance-memory.md:78 | read |
| 2 | V16 sustained 10.779005 min/min | docs/reports/wp5.2-performance-memory.md:79 | read |
| 2 | Synthetic 5.3K 40.331778 min/min, best effort | docs/reports/wp5.2-performance-memory.md:82; docs/underwater-correction-spec.md:454 | read |
| 2 | CP5 current 128 items, 126 done, 2 HLG refusals, 0 failed / pending | docs/reports/wp5.3-review-pack.md:3 | read |
| 2 | CP5 115 headline / 11 candidates available and unjudged, not preference | docs/reports/wp5.3-review-pack.md:146 | read |
| 2 | Earlier accept 117 done / 9 failed; later nine-item witness supersedes build state | docs/proofs/wp5.3-accept.md:23; docs/reports/wp5.3-review-pack.md:3; :215 | read |
| 3 | R3 generated RGB16 PNG 8064x6048 / 48,771,072 pixels, not owner photo | docs/reports/wp5.2-performance-memory.md:124 | read |
| 3 | D111 force_cpu=false; CPU estimate 11,649 MiB vs free 7,064 MiB | docs/reports/wp5.2-performance-memory.md:135 | read |
| 3 | Automatic/capacity fallback true; runner exit 0, PNG16 complete, no failed checks | docs/reports/wp5.2-performance-memory.md:135 | read |
| 3 | Default fallback RSS 6,635,884,544 B (~6.6 GB) | docs/reports/wp5.2-performance-memory.md:112; docs/proofs/wp5.2-accept.md:25 | read |
| 3 | Forced CPU leg is not engagement witness | docs/reports/wp5.2-performance-memory.md:139 | read |
| 3 | D111 no new row; no 48 MP GPU AD-11 comparison; video postencode not preencode proof | docs/proofs/wp5.2-accept.md:20; :26; :42 | read |
| 3 | DR-114 separate pressure limitation | docs/reports/wp5.2-performance-memory.md:246 | read |
| 4 | Register authority / owner commissions; rows through DR-115 | docs/debt-register.md:3; :124 | read |
| 4 | 64 not wholly CLOSED; 51 wholly CLOSED; 115 total | docs/debt-register.md:10 through :124 | read; classify final status cell prefix CLOSED (markdown stripped), retain OPEN/PARTLY |
| 4 / DR-1 | Windows path-form test gap. Trigger: change the local-config path rule or a UNC/drive-relative report; no separate paydown named. | docs/debt-register.md:10 | read |
| 4 / DR-2 | First GPU only in environment parsing. Trigger: second GPU or indexed GPU selection. | docs/debt-register.md:11 | read |
| 4 / DR-6 | Intact-header truncated photos inventory as successes. Trigger: incomplete download or pixel reader; the reader must validate pixels. | docs/debt-register.md:15 | read |
| 4 / DR-7 | HEIC inventory orientation uses EXIF, not irot. Trigger: non-Apple HEIC. | docs/debt-register.md:16 | read |
| 4 / DR-8 | Size-0 box before meta yields graceful rotation-unreadable note. Trigger: a real file with that note. | docs/debt-register.md:17 | read |
| 4 / DR-10 | CSV formula injection from hostile names, outside envelope. Trigger: untrusted footage. | docs/debt-register.md:19 | read |
| 4 / DR-11 | Prototype 16-bit RGB loses precision / no HEIC reader. WP1.3/WP1.4 commissioning picks licensed reader and HEIC scope; CHARC owns it. | docs/debt-register.md:20 | read |
| 4 / DR-12 | 3C paper's mask kernel unverified. WP1.3 tuning verifies the paper and default. | docs/debt-register.md:21 | read |
| 4 / DR-13 | Contrast weight calibration owed; Advanced exposure did not calibrate it. WP1.3 look-check tuning / WP2.1 outcome. | docs/debt-register.md:22 | read |
| 4 / DR-15 | B-frame edit-list convention question remains; hypothesised nonzero owner example absent. WP2.1 rules the convention, WP3.10 tests presentation on iPhone. | docs/debt-register.md:24 | read |
| 4 / DR-16 | Spike containment check/use junction race, outside threat model. Product 8.4 safe writing must prove its form. | docs/debt-register.md:25 | read |
| 4 / DR-20 | Instrument-only items (2),(3),(5),(8),(9): PTS deduplication, percent paths, cover art, record provenance and test gaps. Any reuse beyond WP1.4 re-reads row; product ownership/paydowns remain as recorded. | docs/debt-register.md:29 | read |
| 4 / DR-22 | Temp guard limits. Early plugin if pre-conftest writes revisited; next guard/helper touch fixes (4)-(9), retests fixture containment. Trigger is guard itself, not additive conftest changes. | docs/debt-register.md:31 | read |
| 4 / DR-25 | Only (3) open; >=182-frame staged run assigned to WP5.2 by register, accepted without it; CHARC disposition; AD-3 PROVISIONAL | docs/debt-register.md:34; docs/proofs/wp5.2-accept.md at 2da5d0c7; docs/reports/wp5.2-performance-memory.md | read; bounded text search in both WP5.2 records returned no match |
| 4 / DR-27 | Unreadable footage lookup can skip; stale chapter docstring. Next local-config/affected-test touch distinguishes unreadable from absent and corrects text. | docs/debt-register.md:36 | read |
| 4 / DR-29 | Look-check CLI/cache validation limits. Next lookcheck touch or WP5.3 reuse rejects shallow --part and hashes changing sources. | docs/debt-register.md:38 | read |
| 4 / DR-30 | Noise edge-test and GPMF strict parsing gaps. Reuser adds Immerkaer edge test / strict nesting, padding and SCAL rules or reference parser. | docs/debt-register.md:39 | read |
| 4 / DR-31 | Spike PNG keyword and advisory timing gate. Product writer enforces keyword rule if adopted; future timed instrument requires idle gate or records absence. | docs/debt-register.md:40 | read |
| 4 / DR-34 | Preset no-replace prediction, corrupt-settings set-aside failure, logging reconfiguration limits. Next presets/settings/log touch (WP3.17/WP3.20) or loss report; row names no further remedy. | docs/debt-register.md:43 | read |
| 4 / DR-35 | (a) reserved stem refused rather than renumbered; (d) NumPy import dependency. Refusal shown by WP4.3; owner decides renumbering; (d) unchanged. | docs/debt-register.md:44 | read |
| 4 / DR-36 | (c)-(f) partial-tag warning, malformed tails, fraction coercion and whole-file tail decode. WP3.9 consumer touch or another ffprobe build entering envelope. | docs/debt-register.md:45 | read |
| 4 / DR-37 | Only (c): local config permits footage inside working folder. Next tools/local_config.py touch. | docs/debt-register.md:46 | read |
| 4 / DR-39 | (b) noncontiguous RGB not refused; (c) widened conversion coverage partial, (d) float bit-depth acceptance out of envelope. Consumer briefs / widening supported set trigger. | docs/debt-register.md:48 | read |
| 4 / DR-40 | Per-call constant uploads remain recorded; performance fix stays WP3.21's. | docs/debt-register.md:49 | read |
| 4 / DR-41 | Custom codec id reuse can collide. First product nonregistered codec consumer replaces pid/id with registry or per-object token. | docs/debt-register.md:50 | read |
| 4 / DR-42 | Non-ICC PNG/TIFF colour, hostile PNG checks, WhiteIsZero alpha. Owner wide-gamut report / first PNG-TIFF, hostile-input requirement, or next tiff.py touch respectively; invert colour samples only for (c). | docs/debt-register.md:51 | read |
| 4 / DR-43 | Dropped EXIF has no GUI warning signal; owner photos showed no drops. Next io.photo touch or lost-metadata report; reader-side signal needs interface/warnings design. | docs/debt-register.md:52 | read |
| 4 / DR-44 | Row still headed OPEN although (a)/(b) ADDRESSED and (c) CLOSED/reconfirmed. Preserve its recorded triggers: exact-PTS decode signal, message owner, real-job close/cancellation; no fresh unresolved subpart inferred. | docs/debt-register.md:53 | read |
| 4 / DR-45 | (a) concurrent public FrameStream.close can return before shutdown. First cross-thread consumer / WP4.2 routes public close through shutdown so caller waits. | docs/debt-register.md:54 | read |
| 4 / DR-46 | Mixed bool/number handmade records accepted. Next Y-2 checker touch refuses bool elements in method and store. | docs/debt-register.md:55 | read |
| 4 / DR-47 | (b)/(c) cancellation near completion/publication. Next analysis/engine.py touch; serialise cancel with final publication without progress under lock. | docs/debt-register.md:56 | read |
| 4 / DR-49 | Future parameters beyond 15-decimal spin-box resolution. New such schema widens control or refuses schema at install. | docs/debt-register.md:58 | read |
| 4 / DR-51 | Only (b): oracle does not reject transient position update during drag. Next drag-lane touch adds intermediate-state check. | docs/debt-register.md:60 | read |
| 4 / DR-56 | Audio sub-packet tail trim unexamined. Owner audible-tail report triggers WP4.x; otherwise documented limit. | docs/debt-register.md:65 | read |
| 4 / DR-57 | Only (d): integer rotation comparison, unreachable with current writer. No paydown trigger named. | docs/debt-register.md:66 | read |
| 4 / DR-58 | (a) first NVENC GPU, owner hardware trigger; (b) two test launches retain FFREPORT residual. Product spawn helper closed (b); (c) closed. | docs/debt-register.md:67 | read |
| 4 / DR-59 | UTF-16/compressed XMP scan gap. First iTXt PNG or generator XMP adds marker/GPS and inflated-iTXt plants. | docs/debt-register.md:68 | read |
| 4 / DR-60 | Malformed fixture checker limits. Next regeneration or first committed real HEIC bounds boxes, validates format/rate, checks duration count/stderr. | docs/debt-register.md:69 | read |
| 4 / DR-66 | Worker-only unsafe temp branch reasoned, not executed. Worker temp derivation change or guard-test touch triggers; serial/fullclip must stay without -n. | docs/debt-register.md:75 | read |
| 4 / DR-69 | Device-wide job estimate bench-only, frozen IF-8 gap. If GUI shows total, CHARC interface decision; otherwise remains bench-only. | docs/debt-register.md:78 | read |
| 4 / DR-70 | Export analysis-bound; optimise analysis, not stream step. Owner wish below N6 / WP5.2 remeasure; shipped-build reread leaves lever unchanged. | docs/debt-register.md:79 | read |
| 4 / DR-83 | Cache write through planted link. Next cache touch checks is_link before every write, with junction test. | docs/debt-register.md:92 | read |
| 4 / DR-86 | Further serial-cost candidates; phase-end >about 25min trigger FIRES: p5b 2,046s >1,500s; paydown CHARC/owner | docs/debt-register.md:95; work/wp5.6/gate/summary.txt:11 | read; 25*60=1500; 2046-1500=546 |
| 4 / DR-88 | Trim fixture self-check trusts plan. Next fixture touch adds independent cut derivation beside plan time. | docs/debt-register.md:97 | read |
| 4 / DR-89 | Missing removable-drive journal entry discarded. Next startup-journal touch or stale-partial report; keep entry until seen again is a design candidate. | docs/debt-register.md:98 | read |
| 4 / DR-90 | Clear cache can fail another clip's export. Next Clear/export-cache coupling touch exposes export activity and refuses Clear during it. | docs/debt-register.md:99 | read |
| 4 / DR-91 | Frozen IF-10 reason repr can disclose values. Next IF-10 ruling or unredacted consumer routes through redactor / names field without value. | docs/debt-register.md:100 | read |
| 4 / DR-92 | Escaped mixed-separator Unicode redaction gap, no product producer. Next redactor touch or such product text adds forms / normalises before escape. | docs/debt-register.md:101 | read |
| 4 / DR-95 | Data tracks paired by position can falsely report gpmd missing. Next verify.py touch or mixed-track source pairs by codec tag/order with RED test. | docs/debt-register.md:104 | read |
| 4 / DR-96 | Startup test races timeout/delay. Next startup/test touch makes overrun event-controlled. | docs/debt-register.md:105 | read |
| 4 / DR-97 | V4 records normalised values and spurious translation note. Next compare.py touch preserves raw values and emits note only for nonzero translation. | docs/debt-register.md:106 | read |
| 4 / DR-99 | (a) sampler-start bound load-sensitive: next bench/test touch or second gate failure; align clocks or reasoned bound. (b) frame-release timing bound: slow marker in WP5.3 witness read-back, covered by WP5.2 gate. Register remains OPEN. | docs/debt-register.md:108 | read |
| 4 / DR-100 | Source matching temporary pattern can be deleted on next start. Next naming-pattern/cleanup touch; exact journal paths or age check are remedy candidates. | docs/debt-register.md:109 | read |
| 4 / DR-101 | Last video analysis retained while photo open. Next app/main.py touch drops adapter on photo change with test. | docs/debt-register.md:110 | read |
| 4 / DR-103 | Malformed child JSON progress floods warnings; unreachable shipped worker. Next export_process.py touch classifies JSON failure as invalid progress and fixes docstring. | docs/debt-register.md:112 | read |
| 4 / DR-104 | D87 cache growth charged to output volume, scratch outside GUI accounting. Next D87/cache-layout touch rechecks cache volume when different; seeding requires CHARC decision. | docs/debt-register.md:113 | read |
| 4 / DR-105 | Export failure text may carry full path. Next jobs/export.py failure-text touch names last component for user, full path only in log. | docs/debt-register.md:114 | read |
| 4 / DR-106 | Unused held/progress test sinks. Next owner of both tests re-points/retires window driver, then deletes helpers. | docs/debt-register.md:115 | read |
| 4 / DR-107 | Open warning incorrectly says limited for full-range source. Owner disagreement report or next probe/messages touch aligns resolved-range branches with tests. | docs/debt-register.md:116 | read |
| 4 / DR-108 | Intermittent GUI export-panel test deadlock. Second occurrence STOP, or next rig/test touch runs 50 times under concurrent pytest with timeout; capture stacks on reproduction. | docs/debt-register.md:117 | read |
| 4 / DR-110 | EXIF-only sRGB JPEG spuriously assumed. Owner warning report or next colour.py touch reads ColorSpace 1 declared; 2/65535 untagged, test each. | docs/debt-register.md:119 | read |
| 4 / DR-111 | Best-effort creation time lost on three carriers. Owner export-date sorting report or next metadata mapping carries container/stream tags and reruns real-trim V4. | docs/debt-register.md:120 | read |
| 4 / DR-114 | WDDM per-process free memory hides external GPU pressure. Real held-export evidence benign; failure/stall with another GPU app triggers device-wide-read vs documented-limit owner decision, post-v1 candidate. | docs/debt-register.md:123 | read |
| 4 / DR-115 | No encoder-stall detector; force-cpu processing still feeds NVENC. Single repeat completed, so intermittent. Stopped progress with live encoder triggers; post-Phase-5 owner scopes watchdog and encoder preference. | docs/debt-register.md:124 | read |
| 4 / DR-3 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:12 | read |
| 4 / DR-4 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:13 | read |
| 4 / DR-5 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:14 | read |
| 4 / DR-9 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:18 | read |
| 4 / DR-14 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:23 | read |
| 4 / DR-17 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:26 | read |
| 4 / DR-18 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:27 | read |
| 4 / DR-19 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:28 | read |
| 4 / DR-21 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:30 | read |
| 4 / DR-23 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:32 | read |
| 4 / DR-24 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:33 | read |
| 4 / DR-26 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:35 | read |
| 4 / DR-28 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:37 | read |
| 4 / DR-32 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:41 | read |
| 4 / DR-33 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:42 | read |
| 4 / DR-38 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:47 | read |
| 4 / DR-48 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:57 | read |
| 4 / DR-50 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:59 | read |
| 4 / DR-52 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:61 | read |
| 4 / DR-53 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:62 | read |
| 4 / DR-54 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:63 | read |
| 4 / DR-55 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:64 | read |
| 4 / DR-61 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:70 | read |
| 4 / DR-62 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:71 | read |
| 4 / DR-63 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:72 | read |
| 4 / DR-64 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:73 | read |
| 4 / DR-65 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:74 | read |
| 4 / DR-67 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:76 | read |
| 4 / DR-68 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:77 | read |
| 4 / DR-71 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:80 | read |
| 4 / DR-72 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:81 | read |
| 4 / DR-73 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:82 | read |
| 4 / DR-74 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:83 | read |
| 4 / DR-75 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:84 | read |
| 4 / DR-76 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:85 | read |
| 4 / DR-77 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:86 | read |
| 4 / DR-78 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:87 | read |
| 4 / DR-79 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:88 | read |
| 4 / DR-80 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:89 | read |
| 4 / DR-81 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:90 | read |
| 4 / DR-82 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:91 | read |
| 4 / DR-84 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:93 | read |
| 4 / DR-85 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:94 | read |
| 4 / DR-87 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:96 | read |
| 4 / DR-93 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:102 | read |
| 4 / DR-94 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:103 | read |
| 4 / DR-98 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:107 | read |
| 4 / DR-102 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:111 | read |
| 4 / DR-109 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:118 | read |
| 4 / DR-112 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:121 | read |
| 4 / DR-113 | Wholly CLOSED; closing commit or its absence as grouped in report | docs/debt-register.md:122 | read |
| 4 | DR-62 closure 28c4a75; bbb4ef3e later confirmation | docs/debt-register.md:71 | read |
| 4 | Two performance/memory product findings DR-114 / DR-115; earlier acceptance findings retained | docs/briefs/wp5.6-brief.md:30; docs/debt-register.md:111; :120; :121; :123; :124 | read |
| 4 | DR-114 mechanic cudaMemGetInfo + pool; second-process hold invisible | docs/debt-register.md:123; src/clearwater/core/backend.py:797 (mechanic cited by register, not re-executed) | read |
| 4 | DR-114 external hold 5,861 MiB | docs/debt-register.md:123; docs/reports/wp5.2-performance-memory.md:144 | read |
| 4 | DR-114 device-wide free 1,421 MiB | docs/debt-register.md:123; docs/reports/wp5.2-performance-memory.md:149 | read |
| 4 | DR-114 GPU held/free completed exit 0; 4m4s / 4m3s | docs/debt-register.md:123; docs/proofs/wp5.2-accept.md:25 | read |
| 4 | DR-114 first 30 decoded frames identical; not constant hold proof | docs/reports/wp5.2-performance-memory.md:152; :160 | read |
| 4 | DR-114 allocation failure unmeasured; device-wide read or limit is owner candidate | docs/debt-register.md:123 | read |
| 4 | DR-115 no stall detector, pipe full, encoder spin/no I/O; near 670/681 frames | docs/debt-register.md:124; docs/reports/wp5.2-performance-memory.md:290 | read |
| 4 | DR-115 partial 82,177,867 B; ~35min wait, encoder ended, exit 1 and D85 cleanup | docs/debt-register.md:124; docs/reports/wp5.2-performance-memory.md:293 | read |
| 4 | DR-115 repeat exit 0 in 109m45s, 9.67s/frame; one of two intermittent | docs/debt-register.md:124; docs/proofs/wp5.2-accept.md:26 | read |
| 4 | DR-115 root NVENC cause not established; force-cpu moves processing only | docs/reports/wp5.2-performance-memory.md:300; :305 | read |
| 4 | DR-115 watchdog + software encoder choice owner scope | docs/debt-register.md:124 | read |
| 5 | CHARC request 15f100ae posted 2026-11-02T20:51:43Z; proposal 12min/min 4K | docs/briefs/wp5.6-brief.md:32; docs/decisions.md:30 | read |
| 5 | SET wording: end-to-end including decode/encode, owner's recording modes; 5.3K best effort | docs/underwater-correction-spec.md:145; :455; commit 1db84842 | read |
| 5 / history | Interim25min/min superseded by SET12; AD-21 CLOSED-SET | docs/underwater-correction-spec.md:145; :455; docs/decisions.md:30; commit 1db84842 | read |
| 5 | Cold 10.89 vs prototype 9.78, +11.3% | docs/reports/wp5.2-performance-memory.md:78 | read |
| 5 | Sustained 10.78 vs 9.58, +12.5% | docs/reports/wp5.2-performance-memory.md:79 | read |
| 5 | GUI historical margin +7.3..8.2% | docs/reports/wp5.2-performance-memory.md:84; docs/proofs/wp4.6-accept.md:22 | read |
| 5 | GUI 11.7-11.8 proposal projection, not new measurement | docs/briefs/wp5.6-brief.md:32; docs/reports/wp5.2-performance-memory.md:88 | read |
| 5 | Synthetic 5.3K 8:7 40.33min/min | docs/reports/wp5.2-performance-memory.md:82 | read |
| 5 | Cold analysis/cache margin scope; no causal regression isolated | docs/reports/wp5.2-performance-memory.md:87; :277 | read |
| 5 | Alternatives 15, retain 25, clean-host remeasure | docs/briefs/wp5.6-brief.md:32 | read |
| 6 | Sizes solely seat inventory; main work snapshot 20:54Z, worktree list 21:12Z, 2026-11-02 | work/wp5.6/prune-inventory.txt:1; :223 | read |
| 6 | Parent/child sizes overlap; archive state not established by nonzero size | work/wp5.6/prune-inventory.txt:181; :211; :214; docs/proofs/prune-2026-11-01.md:26 | read; scope limitation (no archive audit) |
| 6 / main | work/wp5.3 16G | work/wp5.6/prune-inventory.txt:185 | read |
| 6 / main | work/wp5.2 1.1G | work/wp5.6/prune-inventory.txt:181 | read |
| 6 / main | work/wp3.6p 1.4G | work/wp5.6/prune-inventory.txt:182 | read |
| 6 / main | work/wp3.6 3.8G | work/wp5.6/prune-inventory.txt:184 | read |
| 6 / main | work/wp2.1s 594M | work/wp5.6/prune-inventory.txt:180 | read |
| 6 / main | work/wp4.3-c6 314M | work/wp5.6/prune-inventory.txt:179 | read |
| 6 / main | work/wp4.2 217M | work/wp5.6/prune-inventory.txt:176 | read |
| 6 / main | work/wp4.1 65K | work/wp5.6/prune-inventory.txt:103 | read |
| 6 / main | work/wp3.21 41M | work/wp5.6/prune-inventory.txt:158 | read |
| 6 / main | work/wp3.14 38M | work/wp5.6/prune-inventory.txt:156 | read |
| 6 / main | work/wp3.10 940K | work/wp5.6/prune-inventory.txt:130 | read |
| 6 / main | work/wp3.4 48K | work/wp5.6/prune-inventory.txt:101 | read |
| 6 / main | work/wp3.1 20K | work/wp5.6/prune-inventory.txt:92 | read |
| 6 / main | work/wp1.5 141M | work/wp5.6/prune-inventory.txt:175 | read |
| 6 / main | work/wp1.5-B 261M | work/wp5.6/prune-inventory.txt:177 | read |
| 6 / main | work/wp1.3-witness 314M | work/wp5.6/prune-inventory.txt:178 | read |
| 6 / main | work/wp1.2a 144K | work/wp5.6/prune-inventory.txt:116 | read |
| 6 / main | work/wp1.2a-B 60K | work/wp5.6/prune-inventory.txt:102 | read |
| 6 / main | work/wp1.2a-B2 36K | work/wp5.6/prune-inventory.txt:98 | read |
| 6 / main | work/wp4.2a 457K | work/wp5.6/prune-inventory.txt:126 | read |
| 6 / main | work/wp4.2b 807K | work/wp5.6/prune-inventory.txt:128 | read |
| 6 / main | work/wp-t1-qa 124K | work/wp5.6/prune-inventory.txt:112 | read |
| 6 / main | work/wp-t2 40K | work/wp5.6/prune-inventory.txt:99 | read |
| 6 / main | work/wp-t5 8.5M | work/wp5.6/prune-inventory.txt:148 | read |
| 6 / main | work/wp-t6 44K | work/wp5.6/prune-inventory.txt:100 | read |
| 6 / main | work/orch-g28 120K | work/wp5.6/prune-inventory.txt:111 | read |
| 6 / main | work/orch-g29 22M | work/wp5.6/prune-inventory.txt:153 | read |
| 6 / main | work/orch-g30 1.5M | work/wp5.6/prune-inventory.txt:135 | read |
| 6 / main | work/orch-g31 3.0M | work/wp5.6/prune-inventory.txt:139 | read |
| 6 / main | work/orch-g32 27M | work/wp5.6/prune-inventory.txt:154 | read |
| 6 / main | work/orch-g33 3.1G | work/wp5.6/prune-inventory.txt:183 | read |
| 6 / main | work/orch-g34 3.3M | work/wp5.6/prune-inventory.txt:140 | read |
| 6 / main | work/orch-g35 6.5M | work/wp5.6/prune-inventory.txt:145 | read |
| 6 / main | work/orch-g36 1.5M | work/wp5.6/prune-inventory.txt:136 | read |
| 6 / main | work/fixtures 86M | work/wp5.6/prune-inventory.txt:174 | read |
| 6 / main | work/reports 16K | work/wp5.6/prune-inventory.txt:90 | read |
| 6 / main | work/charc-handoff 28K | work/wp5.6/prune-inventory.txt:94 | read |
| 6 / main | Keep CP5 pack; keep shared fixtures/reports/handoff until owning seat's word | work/wp5.6/prune-inventory.txt:258; docs/proofs/prune-2026-10-29.md:54; :56 | read |
| 6 / main | Previous prune kept wp4.2 and wp3.10; wp3.21 oracle archived | docs/proofs/prune-2026-10-29.md:30; :55 | read |
| 6 / main | Individual review/repro basetemps and loose logs; no inferred aggregate | work/wp5.6/prune-inventory.txt:2 through :185 | read |
| 6 / worktrees | wp-d112 whole 5.3G | work/wp5.6/prune-inventory.txt:211 | read |
| 6 / worktrees | wp-d112 work 2.3G; archive status not established | work/wp5.6/prune-inventory.txt:211 | read |
| 6 / worktrees | wp-dr113 whole 5.1G | work/wp5.6/prune-inventory.txt:212 | read |
| 6 / worktrees | wp-dr113 work 2.1G; archive status not established | work/wp5.6/prune-inventory.txt:212 | read |
| 6 / worktrees | wp5.1 whole 5.8G | work/wp5.6/prune-inventory.txt:213 | read |
| 6 / worktrees | wp5.1 work 2.8G; archive status not established | work/wp5.6/prune-inventory.txt:213 | read |
| 6 / worktrees | wp5.2 whole 5.0G | work/wp5.6/prune-inventory.txt:214 | read |
| 6 / worktrees | wp5.2 work 2.0G; archive status not established | work/wp5.6/prune-inventory.txt:214 | read |
| 6 / worktrees | wp5.3 whole 5.3G | work/wp5.6/prune-inventory.txt:215 | read |
| 6 / worktrees | wp5.3 work 2.3G; archive status not established | work/wp5.6/prune-inventory.txt:215 | read |
| 6 / worktrees | wp5.6 whole 4.5G | work/wp5.6/prune-inventory.txt:216 | read |
| 6 / worktrees | wp5.6 work 1.5G; archive status not established | work/wp5.6/prune-inventory.txt:216 | read |
| 6 / worktrees | brief-dr113 whole 17M; no work size supplied | work/wp5.6/prune-inventory.txt:188 | read |
| 6 / worktrees | brief-dr87 whole 14M; no work size supplied | work/wp5.6/prune-inventory.txt:189 | read |
| 6 / worktrees | brief-phase5 whole 15M; no work size supplied | work/wp5.6/prune-inventory.txt:190 | read |
| 6 / worktrees | brief-wp3.6p whole 14M; no work size supplied | work/wp5.6/prune-inventory.txt:191 | read |
| 6 / worktrees | brief-wp4.4 whole 13M; no work size supplied | work/wp5.6/prune-inventory.txt:192 | read |
| 6 / worktrees | brief-wp5.2 whole 17M; no work size supplied | work/wp5.6/prune-inventory.txt:193 | read |
| 6 / worktrees | orch-state-g21 13M; no work size supplied | work/wp5.6/prune-inventory.txt:194 | read |
| 6 / worktrees | orch-state-g22 13M; no work size supplied | work/wp5.6/prune-inventory.txt:195 | read |
| 6 / worktrees | orch-state-g23 14M; no work size supplied | work/wp5.6/prune-inventory.txt:196 | read |
| 6 / worktrees | orch-state-g24 14M; no work size supplied | work/wp5.6/prune-inventory.txt:197 | read |
| 6 / worktrees | orch-state-g25 14M; no work size supplied | work/wp5.6/prune-inventory.txt:198 | read |
| 6 / worktrees | orch-state-g26 14M; no work size supplied | work/wp5.6/prune-inventory.txt:199 | read |
| 6 / worktrees | orch-state-g27 15M; no work size supplied | work/wp5.6/prune-inventory.txt:200 | read |
| 6 / worktrees | orch-state-g28 15M; no work size supplied | work/wp5.6/prune-inventory.txt:201 | read |
| 6 / worktrees | orch-state-g29 15M; no work size supplied | work/wp5.6/prune-inventory.txt:202 | read |
| 6 / worktrees | orch-state-g30 15M; no work size supplied | work/wp5.6/prune-inventory.txt:203 | read |
| 6 / worktrees | orch-state-g31 15M; no work size supplied | work/wp5.6/prune-inventory.txt:204 | read |
| 6 / worktrees | orch-state-g32 16M; no work size supplied | work/wp5.6/prune-inventory.txt:205 | read |
| 6 / worktrees | orch-state-g33 16M; no work size supplied | work/wp5.6/prune-inventory.txt:206 | read |
| 6 / worktrees | orch-state-g34 17M; no work size supplied | work/wp5.6/prune-inventory.txt:207 | read |
| 6 / worktrees | orch-state-g35 17M; no work size supplied | work/wp5.6/prune-inventory.txt:208 | read |
| 6 / worktrees | orch-state-g36 17M; no work size supplied | work/wp5.6/prune-inventory.txt:209 | read |
| 6 / worktrees | tmp-wp36p-red 4.0K folder, not registered | work/wp5.6/prune-inventory.txt:210; :259 | read |
| 6 / worktrees | wp5.6r whole 17M, work under 1M (inputs only at measurement); KEEP | work/wp5.6/prune-inventory.txt:264; :257 | read; FC-1 resolves turn-1 gap |
| 6 / worktrees | wp5.3 KEEP CP5 tally; gate/report worktrees KEEP until accept | work/wp5.6/prune-inventory.txt:256; :257; :258 | read |
| 6 / worktrees | Inventory registered worktree membership checked live | work/wp5.6/prune-inventory.txt:223 through :253 | read; git worktree list (main moved to bc4dd024, report/gate bases unchanged) |
| 6 / worktrees | WP-D112 released after merge | docs/proofs/wp-d112-accept.md:42 | read |
| 6 / worktrees | WP-DR113 released after merge | docs/proofs/wp-dr113-accept.md:42 | read |
| 6 / worktrees | WP5.2 released after merge | docs/proofs/wp5.2-accept.md:47 | read |
| 6 / worktrees | WP5.1 accept conditions release on CHARC act; current release not asserted | docs/proofs/wp5.1-accept.md:38 | read |
| 6 / worktrees | Brief/state trees candidate only, owning seat confirms release | docs/briefs/wp5.6-brief.md:34; docs/proofs/prune-2026-11-01.md:69 | read; candidate recommendation, not release assertion |
| 6 / residuals | pytest temp 16G at seat | work/wp5.6/prune-inventory.txt:219 | read |
| 6 / residuals | CHARC pytest temp 15.4GB, no equivalence/conversion asserted | work/wp5.6/prune-inventory.txt:260 | read |
| 6 / residuals | V-S orphans measured 3.0G, supersedes about-2-GB estimate; enclosing orch-g33 3.1G | work/wp5.6/prune-inventory.txt:263; :183; docs/briefs/wp5.6-brief.md:34 | read; FC-1 resolves turn-1 gap |
| 6 / residuals | V-S orphan files moved to orch-g33/vs-orphans, await owner's prune word | docs/proofs/wp5.3-accept.md:24 | read |
| 6 / residuals | Whole-clip input copy 158,459,032 B (~158MB) and exact work location | work/wp5.6/prune-inventory.txt:221; docs/proofs/wp5.2-accept.md:27 | read |
| 6 / archives | 2026-10-29 WP3.21 oracle moved to D:/clearwater-archive/work | docs/proofs/prune-2026-10-29.md:30; :18 | read |
| 6 / archives | 2026-10-29 whole deep CP2 wp1.3d moved to D:/clearwater-archive/work | docs/proofs/prune-2026-10-29.md:31; :18 | read |
| 6 / archives | 2026-10-29 whole shallow CP2 wp1.3 moved to D:/clearwater-archive/work | docs/proofs/prune-2026-10-29.md:32; :18 | read |
| 6 / archives | 2026-10-29 wp1.4 moved to D:/clearwater-archive/work | docs/proofs/prune-2026-10-29.md:33; :18 | read |
| 6 / archives | 2026-10-29 wp1.4b moved to D:/clearwater-archive/work | docs/proofs/prune-2026-10-29.md:34; :18 | read |
| 6 / archives | 2026-10-29 wp-t4 moved to D:/clearwater-archive/work | docs/proofs/prune-2026-10-29.md:35; :18 | read |
| 6 / archives | wp1.2b, wp2.2, pt-main-wp39 incomplete copies not completed archives; owner deleted sources/copies, logs kept | docs/proofs/prune-2026-10-29.md:36; :37; :38; :42 | read |
| 6 / archives | 2026-11-01 WP3.6P facts archived to D:/clearwater-archive/worktrees | docs/proofs/prune-2026-11-01.md:30; :26 | read |
| 6 / archives | 2026-11-01 WP-T7 cell records archived to D:/clearwater-archive/worktrees | docs/proofs/prune-2026-11-01.md:31; :26 | read |
| 6 / archives | 2026-11-01 WP4.6 V7 window archived to D:/clearwater-archive/worktrees | docs/proofs/prune-2026-11-01.md:32; :26 | read |
| 6 / archives | 2026-11-01 WP4.6 dry window archived to D:/clearwater-archive/worktrees | docs/proofs/prune-2026-11-01.md:33; :26 | read |
| 6 / archives | 2026-11-01 WP4.6 shape/probe/support folders archived to D:/clearwater-archive/worktrees | docs/proofs/prune-2026-11-01.md:34; :26 | read |
| 6 / archives | 2026-11-01 Loose files from three trees archived to D:/clearwater-archive/worktrees | docs/proofs/prune-2026-11-01.md:35; :26 | read |
| 6 / archives | Gate files copied to review evidence | docs/proofs/prune-2026-11-01.md:46 through :53 | read |
| 6 / archives | WP-D54/T7/3.6P/4.6 basetemps deleted; worktrees removed, branches kept | docs/proofs/prune-2026-11-01.md:55 through :68 | read |
| 6 / decision | No prune done; owner word/keep list required, orchestrator executes | docs/briefs/wp5.6-brief.md:17; :34; docs/dispatch-recipe.md, deletion grant discipline | read; scope lock |
| Next | CP5 review/tally/owner decision; >=80% no obvious artifacts | docs/briefs/wp5.6-brief.md:28; :36; docs/underwater-correction-spec.md:103; :474; docs/reports/wp5.3-review-pack.md:303 | read |
| 5 / completed | N6 owner ruling complete, removed from next actions; CP5 only pending | work/wp5.6/charc-n6-ruled.txt:14-20; docs/underwater-correction-spec.md:498; commit 1db84842 | read |
| Next | DR-115 watchdog and software-encoder owner scope at close | docs/debt-register.md:124; docs/briefs/wp5.6-brief.md:36 | read |
| Next | WP5.5 after close; license notices/install/usage/version | docs/briefs/wp5.6-brief.md:36; docs/clearwater-implementation-plan.md:365 | read |
| Next | WP5.4 conditional V3 failure or CP5 shimmer; synthetic V3 passed | docs/clearwater-implementation-plan.md:364; docs/underwater-correction-spec.md:134; docs/reports/wp5.1-acceptance.md:92 | read |

