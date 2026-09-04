# E22_v3 Challenger Charter

Status: **OPEN** (authorized 2026-09-04)  
Baseline: **`E22_v2_CASH_EX_OFFICIAL_PATH`** (preserved)

## Hypothesis set (pre-registered, small)

| ID | Hypothesis | Challenger rule |
|---|---|---|
| H1 | Credit on **payment_date** instead of cash_ex_date | Timing only |
| H2 | Credit on cash_ex_date with **tax haircut** (e.g. 0%/10%/20% research grid ≤3 pts) | Tax treatment |
| H3 | Hold-through-ex vs sell-before-ex economic NAV (research ledger already exists) | Decision policy, not fill rewrite |

## Method

1. Sandbox under `repro/e22-v3-<date>/` or `forward/e22_v3_challenger/`  
2. Same E16/E18 loop as v2; only dividend cashflow rule changes  
3. Side-by-side vs v2 full-history + paper QC (Exact T+1)  
4. Decision PASS/FAIL/INCONCLUSIVE → governance for `E22_v3_*` only if approved  

## Stop rules

- Do not edit `e22_v2_forward_pipeline.py` or `forward/e22_v2/` history  
- Do not backfill dividends into `forward/e21/`  
- Tax grid max 3 pre-registered points; no hunting after held-out look  

## Round-1 deliverable

Payment-date vs ex-date NAV delta on early-stack book (`research_reopen_round1.py`).
