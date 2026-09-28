# FIN buy-quality Stage C — 2015 / 2020 stress-window backtest

Date: 2026-09-28  
Status: **STRESS_SLICE_DONE** · Soft-Frozen **KEEP** · no live wire  
Parent: Stage C `HYBRID_PARETO` · champion `C_OR_K9_AND_BELOW_MA60`  
Source NAV: `repro/fin-buy-quality-stagec/outputs/nav_*.csv`

## Windows

| ID | Span |
|---|---|
| `2015_summer_crash` | 2015-04-01 → 2015-09-30 |
| `2020_covid_crash` | 2020-01-15 → 2020-04-30 |
| `2020_feb_mar` | 2020-02-01 → 2020-03-31 |

MDD inside window (renormalized). `mddΔ` vs CTRL: **positive = shallower** (better).

## Results vs `CTRL_BASE`

### 2015 summer

| Book | ret% | MDD% | mddΔ vs CTRL |
|---|---:|---:|---:|
| CTRL_BASE | -1.267 | -9.42 | — |
| P_SEED_MA120 | -1.103 | -9.593 | -0.173pp |
| P_B_OR_K9 | -1.077 | -9.603 | -0.183pp |
| **C_OR_K9_AND_BELOW_MA60** | **-1.077** | **-9.603** | **-0.183pp** |

### 2020 COVID

| Book | covid MDD% | feb–mar MDD% | covid mddΔ | feb–mar mddΔ |
|---|---:|---:|---:|---:|
| CTRL_BASE | -14.108 | -13.298 | — | — |
| P_SEED_MA120 | -13.216 | -11.721 | +0.892 | +1.577 |
| P_B_OR_K9 | -12.058 | -10.917 | +2.050 | +2.381 |
| **C_OR_K9_AND_BELOW_MA60** | **-14.044** | **-12.553** | **+0.064** | **+0.745** |

## Binding takeaway

1. Verdict: **`CHAMP_STRESS_MIXED`**
2. 2015 summer mddΔ vs CTRL: **-0.183pp**
3. 2020 COVID mddΔ vs CTRL: **+0.064pp** · Feb–Mar: **+0.745pp**
4. Does **not** authorize live wire; supports Stage C paper observe case if stress not worse.

CSV: `repro/fin-buy-quality-stagec/reports/FIN_BUY_QUALITY_STAGEC_STRESS_2015_2020.csv`  
Label: `FIN_BUY_QUALITY_STAGEC_STRESS_2015_2020_2026-09-28__CHAMP_STRESS_MIXED`
