# E50-A3-R1-F1 Locked Challenger — Held-Out Evaluation

F1 = `TECH2_VALUE` under fixed C4 portfolio wrapper. Selected on 2011–2018 OOF only.
**No retune after held-out. No promotion. Gates remain EXPERIMENTAL.**

## Locked F1

```
features=['momentum_family_score', 'defensive_family_score', 'pct_book_to_price_proxy', 'pct_earnings_yield_proxy']
mode=BREADTH_REGIME ridge_lambda=1.0
top_k=22 rebalance_every=42 exit_multiple=2.25
industry_cap=5 replace_rank_gap=5 liquidity_floor=20000000
```

## Research decision

**`MIXED_HELDOUT`**

OOF: turnover 1.92%, bootstrap 0.7078, IC 0.1134

| Metric | F1 Validation 2019–2022 | F1 Sealed 2023–latest | C4 TECH2 Val | C4 TECH2 Sealed |
|---|---:|---:|---:|---:|
| CAGR | 18.58% | 48.86% | 21.65% | 47.68% |
| MDD | -29.55% | -19.35% | -31.87% | -20.99% |
| Turnover | 2.23% | 1.04% | 2.19% | 1.19% |
| Bootstrap | 0.3904 | 0.9984 | 0.5588 | 0.9984 |
| Beats proxy | False | True | True | True |
| Turn gate | True | True | True | True |
| Boot gate | False | True | False | True |
| Exact T+1 | True | True | True | True |

Artifact: `reports/stage4_f1_heldout_decision.json`
