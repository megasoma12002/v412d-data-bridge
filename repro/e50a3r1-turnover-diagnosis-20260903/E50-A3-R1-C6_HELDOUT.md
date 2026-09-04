# E50-A3-R1-C6 Locked Challenger — Held-Out Evaluation

Date: 2026-09-04

## Hypothesis

Industry neutralization / industry_cap variants for stabler OOF excess.

## Locked C6

```
top_k=20
rebalance_every=42
exit_multiple=2.25
neutralization=NONE
industry_cap=4
min_hold_cycles=0
liquidity_floor=20000000.0
replace_rank_gap=0
```

## Research decision

**`MIXED_HELDOUT`**

OOF: turnover 2.11%, bootstrap 0.8060, CAGR 10.56%, MDD -30.00%, HAC t 0.759

| Metric | Validation 2019–2022 | Sealed 2023–latest |
|---|---:|---:|
| CAGR | 21.14% | 54.19% |
| MDD | -27.31% | -23.28% |
| Sharpe | 1.010 | 1.991 |
| Sortino | 1.255 | 2.378 |
| Calmar | 0.774 | 2.328 |
| Turnover | 2.64% | 1.76% |
| Cost | 0.1536 | 0.1069 |
| Exposure | 0.9973 | 0.9989 |
| Holdings | 19.94 | 19.98 |
| Bootstrap | 0.5026 | 0.9998 |
| Beats proxy | True | True |
| Turn gate | False | True |
| Boot gate | False | True |
| Exact T+1 | True | True |
