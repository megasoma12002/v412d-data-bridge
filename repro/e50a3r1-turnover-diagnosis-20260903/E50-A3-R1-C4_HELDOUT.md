# E50-A3-R1-C4 Locked Challenger — Held-Out Evaluation

Date: 2026-09-04

## Hypothesis

Maximize OOF HAC t-stat (excess strength) among dual-gate passers with turnover headroom.

## Locked C4

```
top_k=22
rebalance_every=42
exit_multiple=2.25
neutralization=NONE
industry_cap=5
min_hold_cycles=0
liquidity_floor=20000000.0
replace_rank_gap=5
```

## Research decision

**`MIXED_HELDOUT`**

OOF: turnover 2.05%, bootstrap 0.8066, CAGR 10.56%, MDD -30.24%, HAC t 0.773

| Metric | Validation 2019–2022 | Sealed 2023–latest |
|---|---:|---:|
| CAGR | 21.65% | 47.68% |
| MDD | -31.87% | -20.99% |
| Sharpe | 0.969 | 1.915 |
| Sortino | 1.231 | 2.290 |
| Calmar | 0.679 | 2.271 |
| Turnover | 2.19% | 1.19% |
| Cost | 0.1338 | 0.0652 |
| Exposure | 0.9990 | 0.9989 |
| Holdings | 21.72 | 22.02 |
| Bootstrap | 0.5588 | 0.9984 |
| Beats proxy | True | True |
| Turn gate | True | True |
| Boot gate | False | True |
| Exact T+1 | True | True |
