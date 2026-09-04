# E50-A3-R1-C7 Locked Challenger — Held-Out Evaluation

Date: 2026-09-04

## Hypothesis

Higher liquidity floors + mild min-hold to drop fragile names (OOF dual-gate).

## Locked C7

```
top_k=25
rebalance_every=42
exit_multiple=2.0
neutralization=NONE
industry_cap=5
min_hold_cycles=0
liquidity_floor=40000000.0
replace_rank_gap=0
```

## Research decision

**`MIXED_HELDOUT`**

OOF: turnover 2.09%, bootstrap 0.8176, CAGR 10.78%, MDD -30.35%, HAC t 0.862

| Metric | Validation 2019–2022 | Sealed 2023–latest |
|---|---:|---:|
| CAGR | 18.58% | 51.47% |
| MDD | -29.90% | -26.62% |
| Sharpe | 0.922 | 1.900 |
| Sortino | 1.148 | 2.245 |
| Calmar | 0.622 | 1.933 |
| Turnover | 2.53% | 1.77% |
| Cost | 0.1417 | 0.1004 |
| Exposure | 0.9977 | 0.9989 |
| Holdings | 24.93 | 24.97 |
| Bootstrap | 0.3722 | 0.9998 |
| Beats proxy | False | True |
| Turn gate | False | True |
| Boot gate | False | True |
| Exact T+1 | True | True |
