# E22_v3 Challenger Charter

Status: **H1_RERUN_DONE** (2026-09-04) — interesting, **not promoted**  
Baseline: **`E22_v2_CASH_EX_OFFICIAL_PATH`** (preserved)

## Hypothesis set (pre-registered, small)

| ID | Hypothesis | Challenger rule | Status |
|---|---|---|---|
| H1 | Credit on **payment_date** instead of cash_ex_date | Timing only | **Ran** with 100% payment dates → `H1_PAY_DATE_INTERESTING_CONTINUE_SANDBOX` (see `E22_V3_H1_DECISION.md`) |
| H2 | Credit on cash_ex_date with **tax haircut** (0%/10%/20%) | Tax treatment | Grid in same sandbox; tax hurts both clocks |
| H3 | Hold-through-ex vs sell-before-ex economic NAV | Decision policy | Not rerun this turn |

## Method

1. Sandbox under `repro/e22-v3-h1-20260904/`  
2. Same E16/E18 loop as v2; only dividend cashflow rule changes  
3. Side-by-side vs v2 full-history + Exact T+1 QC  
4. Decision PASS/FAIL/INCONCLUSIVE → governance for `E22_v3_*` only if approved  

## Stop rules

- Do not edit `e22_v2_forward_pipeline.py` or `forward/e22_v2/` history  
- Do not backfill dividends into `forward/e21/`  
- Tax grid max 3 pre-registered points; no hunting after held-out look  
- **No auto-promote** even when H1 clears the util bar  

## Paper challenger

Seeded: `forward/e22_v3_challenger/` (`E22_v3_CASH_PAY_PAPER_CHALLENGER`, EXPERIMENTAL).

## Latest deliverable

`research/reopen/E22_V3_H1_DECISION.md` + `repro/e22-v3-h1-20260904/`