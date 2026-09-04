# E50-A3-R1-C3 Locked Challenger — Held-Out Evaluation

Date: 2026-09-04  
Branch: `cursor/e50a3r1-turnover-diagnosis-d049`

## Locked C3 (no retune)

```
TECH2 / BREADTH_REGIME / lambda=1.0
top_k=25
rebalance_every=42
exit_multiple=2.0
neutralization=NONE
industry_cap=5
```

Selected on **2011–2018 OOF only** with bootstrap-first rule. C1/C2 not retuned.

## Research decision

**`MIXED_HELDOUT`**

## OOF reconfirm

- Turnover 2.11% PASS
- Bootstrap 0.8078 PASS (margin 0.1078)
- CAGR 10.60%, MDD -30.33%

## Window metrics

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
| PIT proxy CAGR | 20.94% | 20.96% |
| Beats proxy | False | True |
| Turnover ≤2.5% | False | True |
| Bootstrap ≥0.70 | False | True |
| Exact T+1 | True | True |

## Yearly returns

### VALIDATION_2019_2022

| Year | Return | MDD in year | Avg turnover | Avg holdings |
|---|---:|---:|---:|---:|
| 2019 | 34.89% | -5.56% | 2.09% | 24.9 |
| 2020 | 34.16% | -26.70% | 2.24% | 25.0 |
| 2021 | 26.84% | -15.95% | 2.29% | 25.0 |
| 2022 | -15.93% | -29.90% | 3.51% | 24.8 |

### SEALED_2023_LATEST

| Year | Return | MDD in year | Avg turnover | Avg holdings |
|---|---:|---:|---:|---:|
| 2023 | 47.11% | -10.19% | 1.77% | 24.9 |
| 2024 | 12.58% | -13.40% | 1.17% | 25.0 |
| 2025 | 41.92% | -19.99% | 2.52% | 25.0 |
| 2026 | 78.26% | -18.18% | 1.52% | 25.0 |

## Verification

- Exact T+1 intact: **True**
- No held-out retune / no promotion / E45 untouched / frozen baselines unchanged
