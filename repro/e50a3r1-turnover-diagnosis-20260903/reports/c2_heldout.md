# E50-A3-R1-C2 Locked Challenger — Held-Out Evaluation

Date: 2026-09-04  
Branch: `cursor/e50a3r1-turnover-diagnosis-d049`  
Sandbox: `repro/e50a3r1-turnover-diagnosis-20260903/`

## Locked C2 (no retune)

```
TECH2 / BREADTH_REGIME / lambda=1.0
top_k=20
rebalance_every=42
exit_multiple=2.5
neutralization=NONE
industry_cap=5
min_hold_cycles=0
replace_rank_gap=0
```

Selected on **2011–2018 OOF only** as Round-2 dual-gate winner (lower OOF turnover headroom vs C1).
C1 remains MIXED_HELDOUT and was not retuned.

## Research decision

**`MIXED_HELDOUT`**

## OOF reconfirm

- Turnover 2.01% (PASS ≤2.5%)
- Bootstrap 0.7554 (PASS ≥0.70)
- CAGR 9.91%, MDD -31.09%

## Window metrics

| Metric | Validation 2019–2022 | Sealed 2023–latest |
|---|---:|---:|
| CAGR | 21.40% | 59.82% |
| MDD | -29.38% | -19.86% |
| Sharpe (rf0) | 1.024 | 2.190 |
| Sortino (rf0) | 1.271 | 2.617 |
| Calmar | 0.728 | 3.013 |
| Avg daily turnover | 2.43% | 1.49% |
| Total transaction cost | 0.1429 | 0.0994 |
| Mean gross exposure | 0.9973 | 0.9989 |
| Average holdings | 19.94 | 19.98 |
| Bootstrap P(excess>0) | 0.5108 | 1.0000 |
| PIT proxy CAGR | 20.94% | 20.96% |
| Beats PIT proxy | True | True |
| Turnover ≤ 2.5% | True | True |
| Bootstrap ≥ 0.70 | False | True |
| Exact T+1 | True | True |

## Yearly returns

### VALIDATION_2019_2022

| Year | Return | MDD in year | Avg turnover | Avg holdings |
|---|---:|---:|---:|---:|
| 2019 | 35.99% | -6.27% | 1.93% | 19.9 |
| 2020 | 35.86% | -26.68% | 2.21% | 20.0 |
| 2021 | 34.66% | -12.86% | 2.06% | 20.0 |
| 2022 | -14.51% | -29.38% | 3.51% | 19.8 |

### SEALED_2023_LATEST

| Year | Return | MDD in year | Avg turnover | Avg holdings |
|---|---:|---:|---:|---:|
| 2023 | 57.53% | -8.10% | 1.52% | 19.9 |
| 2024 | 23.09% | -13.14% | 0.67% | 20.0 |
| 2025 | 57.13% | -18.37% | 2.41% | 20.0 |
| 2026 | 66.29% | -17.22% | 1.29% | 20.0 |

## Verification

- Exact T+1 intact: **True**
- No held-out parameter tuning: **True**
- E45 touched: **False**
- Frozen baselines unchanged: **True**
- No promotion / do not merge yet

## Artifacts

- `reports/c2_heldout_decision.json`
- `reports/round2_oof_summary.json`
- `outputs/round2_oof_challenger_grid.csv`
- `outputs/c2_*_daily_nav.csv` / `_trades.csv` / `_yearly_returns.csv` / `_rolling_drawdown.csv`
