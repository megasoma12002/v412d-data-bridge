# E50-A3-R1-C5 Locked Challenger — Held-Out Evaluation

Date: 2026-09-04

## Hypothesis

Prefer joint OOF margins: require bootstrap>=0.78 if available else max bootstrap; then turnover headroom; then utility.

## Locked C5

```
top_k=24
rebalance_every=42
exit_multiple=2.0
neutralization=NONE
industry_cap=5
min_hold_cycles=0
liquidity_floor=20000000.0
replace_rank_gap=0
```

## Research decision

**`MIXED_HELDOUT`**

OOF: turnover 2.13%, bootstrap 0.7882, CAGR 10.35%, MDD -30.60%, HAC t 0.744

| Metric | Validation 2019–2022 | Sealed 2023–latest |
|---|---:|---:|
| CAGR | 19.01% | 55.34% |
| MDD | -29.20% | -23.23% |
| Sharpe | 0.938 | 1.997 |
| Sortino | 1.172 | 2.391 |
| Calmar | 0.651 | 2.383 |
| Turnover | 2.55% | 1.70% |
| Cost | 0.1435 | 0.1025 |
| Exposure | 0.9976 | 0.9989 |
| Holdings | 23.93 | 23.97 |
| Bootstrap | 0.3930 | 0.9998 |
| Beats proxy | False | True |
| Turn gate | False | True |
| Boot gate | False | True |
| Exact T+1 | True | True |
