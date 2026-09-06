# Project Code Review — 2026-09-06

Scope: entire repo engineering surface (`scripts/`, live `forward/e21` gates, ops monitors), against `CODING_STANDARDS.md` + Soft-Frozen / Exact T+1 governance.  
Soft-Frozen Financial **[0.50, 0.95] KEEP** · live stitch **FORBIDDEN** · no Soft-Frozen flip.

## Verdict

| Area | Grade | Notes |
|---|---|---|
| Live Soft-Frozen envelope | **P0 found → fixed this pass** | clip-then-renormalize could push FIN &lt; 0.50 |
| Exact T+1 fail-closed | **P1 found → fixed this pass** | empty/corrupt fill schema was fail-open |
| Ops alert Exact T+1 visibility | **P1 found → fixed this pass** | missing `exact_t1_ok` was silent |
| Live QC Soft-Frozen band check | **Added this pass** | QC now asserts FIN ∈ Soft-Frozen clip |
| Coding-standards hygiene gates | **PASS** | E45 + project checkers green |
| E45 paper harness adoption | **OPEN (P2)** | harness exists; most paper scripts still fork locals |
| Book-ID consistency | **Partial** | cost-turnover BASE join bug fixed; more aliases remain |
| Claim-label honesty | **Partial** | early-stack retired-status wired; historical MD may still say NOT_VERIFIED |

**Overall:** Live path is now fail-closed on the Soft-Frozen envelope + Exact T+1 schema gaps found in this review. Research debt remains (harness adoption, book-ID aliases, oversized OOF monoliths) — tracked below, not Soft-Frozen/stitch work.

## P0 — Live correctness (fixed)

### L1 Soft-Frozen renormalize breach
- **Where:** `scripts/e16_soft_frozen_base.py` `apply_soft_frozen_clips`
- **Bug:** clip then `/sum` could yield FIN≈0.417 from `[0.50,0.35,0.35]`
- **Fix:** bounded box∩simplex projection; unit-checked FIN≥0.50 and sum=1
- **QC:** `e21_qc.py` now checks `soft_frozen_fin_clip`

## P1 — Live / ops fail-closed (fixed)

### L2 Exact T+1 schema fail-open
- **Where:** `scripts/e21_qc.py` `exact_t1_from_fills`
- **Bug:** non-empty fills missing date columns returned `exact_t1_ok=True`
- **Fix:** empty → ok; non-empty missing schema → **fail**

### L3 Ops alert silent on missing Exact T+1
- **Where:** `scripts/ops_alert_scan.py`
- **Bug:** only alerted when `exact_t1_ok is False`; `None` with PASS was silent
- **Fix:** `EXACT_T1_MISSING` CRITICAL when key absent

## P1 — Research correctness (fixed this pass)

### R1 Cost-turnover BASE join bug
- **Where:** `scripts/e45_alpha_cost_turnover_paper.py`
- **Bug:** emitted `BASE_E16_E18_E22_v2s` but filtered `book == "BASE"`
- **Fix:** filter via `book_id(0.0)`

### R2 Deprecated claim emitter
- **Where:** `scripts/e50_early_stack_combined_nav.py`
- **Bug:** `claim_status: NOT_FOUND_IN_ARTIFACTS`
- **Fix:** emit `e45.CLAIMED_MDD_STATUS` (`RETIRED_HISTORICAL_NARRATIVE`) when claim not numerically found

## P1 / P2 — Still open (not blocking Soft-Frozen KEEP)

| ID | Sev | Finding | Recommendation |
|---|---|---|---|
| O1 | P1 | E45 paper screens still fork `load_market` / `blend` / `window_stats` instead of `e45_paper_harness` | Migrate regenerators on next paper run |
| O2 | P1 | Parallel book namespaces (`REF_BLEND_*`, `CONST_*`, bare `BLEND_A*`, `ALL_FULL`) | Emit only canonical IDs; keep aliases as optional display tags |
| O3 | P1 | Some packs still use metric key `mdd` vs `max_drawdown` | Normalize emitters to `max_drawdown` |
| O4 | P2 | Pipeline market-path substring gate (alias risk) | Prefer `Path.resolve()` equality like state-dir |
| O5 | P2 | Month-end pack `--report-only` never fails on CRITICAL | Optional `--fail-on critical` for gated packs |
| O6 | P2 | Universe lists duplicated in pipeline/QC vs Soft-Frozen base | Import `FIN`/`TEL` from `e16_soft_frozen_base` |
| O7 | P2 | Oversized research monoliths (900+ line adversarial / gap packs) | Split only when next touched |
| O8 | P2 | Hygiene gates do not yet enforce harness imports / f-string book IDs | Extend `check_e45_paper_hygiene.py` |

## What was already healthy

- Soft-Frozen **constants** single-sourced (`SOFT_FROZEN_FIN_LO/HI/CLIP`)
- Live pipeline Exact T+1 hard-fail on same-bar fills (write path)
- `research_metric_helpers` None-safe deltas; project `or 0` metric emitters cleared in prior sweep
- No fee/sleeve monkeypatches remaining under `scripts/`
- No eval/exec / hardcoded secret emitters found in scan

## Hygiene re-check

```bash
PYTHONPATH=scripts python3 scripts/check_project_coding_hygiene.py
PYTHONPATH=scripts python3 scripts/check_e45_paper_hygiene.py
```

## Explicit non-goals of this review

- Soft-Frozen flip / DEFAULT change / live stitch
- Inventing a the retired handoff MDD narrative replacement number
- Re-running all historical research grids
- Full harness migration of every E45 paper script in one shot

## Label

`PROJECT_CODE_REVIEW_2026-09-06__LIVE_P0_FIXED__RESEARCH_DEBT_TRACKED`

## Debt closure pass — 2026-09-06 (follow-up)

Closed without Soft-Frozen / DEFAULT / stitch changes:

| ID | Action | Status |
|---|---|---|
| O1 | Migrated E45 paper regenerators + dual/blend ledgers onto `e45_paper_harness` (removed local `load_market`/`window_stats`/`blend`) | **CLOSED** |
| O2 | Canonicalized `REF_BLEND_*` / `CONST_*` / `ALL_FULL` / `PAPER_BLEND_A10` emitters to `BLEND_E45_A*` / `CHAL_E45_E3` | **CLOSED** |
| O3 | Active E45 emitters normalized to `max_drawdown` (incl. year attribution / named packs / stage3 windows) | **CLOSED** |
| O4 | `e21_forward_pipeline` market gate now `Path.resolve()` equality vs canonical live market | **CLOSED** |
| O5 | `ops_month_end_paper_pack --fail-on-critical` (default unchanged: `--report-only`) | **CLOSED** |
| O6 | Live pipeline / build_market / QC universe import `FIN`/`TEL` from `e16_soft_frozen_base` | **CLOSED** |
| O7 | Oversized monoliths | **DEFERRED** (split when next touched) |
| O8 | `check_e45_paper_hygiene` enforces harness import on regenerators + bans forked defs | **CLOSED** |

Verification: both hygiene checkers PASS; A05/A25 month-end monitors EXIT:0; `load_market` parity vs harness; residual E45 forks = 0.

Label: `PROJECT_CODE_REVIEW_DEBT_CLOSURE_2026-09-06__O1-O6_O8_CLOSED__O7_DEFERRED__STITCH_FORBIDDEN`
