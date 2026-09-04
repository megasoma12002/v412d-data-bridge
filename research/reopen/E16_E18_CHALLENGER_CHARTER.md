# E16 / E18 Challenger Charter

Status: **OPEN** (authorized 2026-09-04)  
Baselines: official E16 path in E21 / E22_v2; E18 Exact T+1 + fees

## Allowed experiment classes

| Class | Examples | Forbidden |
|---|---|---|
| E16 sleeve bounds | Crisis tilt amplitude, 0050 cap, FIN/TEL floors (pre-reg ≤4 variants) | Silent membership swap of frozen FIN/TEL lists without challenger label |
| E16 rebalance friction | L1 gap threshold, trade fraction 0.75, cap 0.20 (pre-reg ≤3) | Same-bar fill |
| E18 costs | Fee/tax/slippage stress (±mult) for robustness — not “better by assuming 0 cost” | Claiming zero-cost as new official |
| Execution lot policy | Lot rounding variants | Future open substitution |

## Method

1. New folder `repro/e16-e18-challenger-<date>/`  
2. Copy constants; do not patch `e21_forward_pipeline.py` in place  
3. Full-history sandbox NAV + live paper dir if promoted later  
4. Must keep Exact T+1 HARD_FROZEN  

## Round-1 deliverable

Register baseline metrics from early-stack `E16_E18_E22` and document the pre-registered variant list (no mega-grid).
