# E50-A3-R1-C8 Locked Challenger — Held-Out Evaluation

Date: 2026-09-04

## Hypothesis

Slower rebalance + replace-rank-gap around low-turnover region (new configs only).

## Locked C8

```
top_k=22
rebalance_every=42
exit_multiple=2.25
neutralization=NONE
industry_cap=5
min_hold_cycles=0
liquidity_floor=20000000.0
replace_rank_gap=10
```

## Research decision

**`MIXED_HELDOUT`**

OOF: turnover 2.02%, bootstrap 0.7604, CAGR 9.95%, MDD -30.24%, HAC t 0.632

| Metric | Validation 2019–2022 | Sealed 2023–latest |
|---|---:|---:|
| CAGR | 21.53% | 46.98% |
| MDD | -31.87% | -20.99% |
| Sharpe | 0.965 | 1.899 |
| Sortino | 1.228 | 2.266 |
| Calmar | 0.676 | 2.238 |
| Turnover | 2.18% | 1.18% |
| Cost | 0.1332 | 0.0637 |
| Exposure | 0.9990 | 0.9989 |
| Holdings | 21.72 | 21.97 |
| Bootstrap | 0.5544 | 0.9982 |
| Beats proxy | True | True |
| Turn gate | True | True |
| Boot gate | False | True |
| Exact T+1 | True | True |
