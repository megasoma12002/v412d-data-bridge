# E50-A3-R1 Locked Challenger — Detailed Held-Out Evaluation

Date: 2026-09-03  
Branch: `cursor/e50a3r1-turnover-diagnosis-d049`  
Sandbox: `repro/e50a3r1-turnover-diagnosis-20260903/`

## Locked challenger (no retune)

```
TECH2 / BREADTH_REGIME / lambda=1.0
top_k=20
rebalance_every=42
exit_multiple=2.0
neutralization=NONE
industry_cap=5
```

Selected on **2011–2018 OOF only**. Held-out windows are evaluation-only.

2.5% turnover and 0.70 bootstrap remain **EXPERIMENTAL**. No promotion. Do not merge yet.

## Research decision

**`MIXED_HELDOUT`**

Validation fails experimental turnover and bootstrap gates; sealed passes both. Exact T+1 intact. Result is mixed across held-out windows.

## Window metrics

| Metric | Validation 2019–2022 | Sealed 2023–latest |
|---|---:|---:|
| CAGR | 21.46% | 60.95% |
| MDD | -28.47% | -22.86% |
| Sharpe (rf0) | 1.022 | 2.192 |
| Sortino (rf0) | 1.259 | 2.638 |
| Calmar | 0.754 | 2.666 |
| Avg daily turnover | 2.69% | 1.73% |
| Total transaction cost | 0.1591 | 0.1098 |
| Mean gross exposure | 0.9973 | 0.9989 |
| Average holdings | 19.94 | 19.98 |
| Bootstrap P(excess>0) | 0.5138 | 1.0000 |
| PIT proxy CAGR | 20.94% | 20.96% |
| Beats PIT proxy | True | True |
| Turnover ≤ 2.5% | False | True |
| Bootstrap ≥ 0.70 | False | True |

## Yearly returns

### VALIDATION_2019_2022

| Year | Return | MDD in year | Avg turnover | Avg holdings |
|---|---:|---:|---:|---:|
| 2019 | 36.78% | -6.45% | 2.12% | 19.9 |
| 2020 | 33.59% | -28.44% | 2.36% | 20.0 |
| 2021 | 33.86% | -12.75% | 2.56% | 20.0 |
| 2022 | -12.92% | -28.09% | 3.71% | 19.8 |

### SEALED_2023_LATEST

| Year | Return | MDD in year | Avg turnover | Avg holdings |
|---|---:|---:|---:|---:|
| 2023 | 56.79% | -8.26% | 1.72% | 19.9 |
| 2024 | 17.41% | -13.93% | 0.98% | 20.0 |
| 2025 | 53.96% | -18.16% | 2.73% | 20.0 |
| 2026 | 82.98% | -18.65% | 1.33% | 20.0 |

## Rolling drawdown summary

| Window | Max DD | Mean DD | Days DD≤-10% | Days DD≤-20% | CSV |
|---|---:|---:|---:|---:|---|
| VALIDATION_2019_2022 | -28.47% | -5.42% | 195 | 50 | `outputs/locked_validation_2019_2022_rolling_drawdown.csv` |
| SEALED_2023_LATEST | -22.86% | -3.29% | 40 | 4 | `outputs/locked_sealed_2023_latest_rolling_drawdown.csv` |

## Verification

- Exact T+1 intact: **True** (same-bar fills val=0, sealed=0)
- No held-out parameter tuning: **True**
- Locked config unchanged: **True**
- Fit cutoffs: val `2018-11-30`, sealed `2022-12-01`
- Leakage: NO_NEW_LEAKAGE_INTRODUCED — Model fit cutoffs precede each held-out window (val 2018-11-30, sealed 2022-12-01). Universe/liquidity filters applied on signal date only in the existing A3/R1 path. Full panel leakage re-audit is preserved in merged PR #17 (repro/e50a3r1-audit-20260903/reports/leakage_audit.json); this run does not retune.
- E45 touched: **False**
- Frozen baselines unchanged: **True**

## Artifacts

- `reports/heldout_detailed_decision.json`
- `outputs/locked_*_daily_nav.csv` / `_trades.csv` / `_market_proxy_nav.csv`
- `outputs/locked_*_yearly_returns.csv`
- `outputs/locked_*_rolling_drawdown.csv`
