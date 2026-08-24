# V4.12-D Formal Financial Regime Router

Date: 2026-08-24  
Status: **Validation PASS; Blind/Final benchmark underperformance documented**

## Architecture restored from V4.11–V4.12-C3R

- R1: 2880/2886/2892/5880, Q4 prior plus low-zone mean reversion.
- R2: 2801/2834, slow-recovery model kept separate from public financial holding companies.
- R3: 2884/2885/2890/2891, momentum continuation and financial-sector relative strength.
- R4: 2881/2882, momentum/defensive score with broad financial-regime gate.
- R0: cash for unused Tilt only.
- Upper layer: 80% fixed Core (20% per router) plus 20% monthly Tilt.
- Inner layer: router-specific daily features, but positions change only every 15 or 21 trading days.
- Capital-Lock candidates: 60/75/90 trading days, inherited from the V4.6c robust neighborhood.
- Execution: signal at T close, trade at T+1 open.
- Costs: buy 0.0855%; sell 0.3855%, including securities transaction tax.

## Frozen selection discipline

- Train: 2010-01-01–2018-12-31.
- Validation: 2019-01-01–2022-12-31, rejection only.
- Blind: 2023-01-01–2025-12-31, no tuning.
- Final OOS: 2026-01-01–2026-08-21, no tuning.
- Robust plateau: a Train top-ten candidate must have a neighboring rebalance/Capital-Lock configuration.
- Validation gate was fixed before evaluation: positive return, MDD better than -25%, positive Sharpe, and Sharpe at least as high as the 12-stock equal-weight benchmark.
- No fallback is treated as a pass.

## Selected plateau

- Family 1 (moderate eligibility gates)
- Top 2 stocks inside each router
- Rebalance every 21 trading days
- Capital-Lock: 75 trading days
- Two neighboring family variants at the same 21D/Top2/75D structure also passed Validation.

## Walk-forward results at 1× costs

| Period | Formal Router return | MDD | Sharpe | EqualWeight12 return | MDD | Sharpe |
|---|---:|---:|---:|---:|---:|---:|
| Train | +10.35% | -38.56% | 0.150 | +9.60% | -36.47% | 0.147 |
| Validation | **+39.19%** | **-18.91%** | **0.688** | +27.16% | -26.72% | 0.471 |
| Blind | +35.08% | -18.38% | 0.801 | **+48.79%** | -18.00% | **0.999** |
| Final OOS | +21.46% | -8.51% | 1.821 | **+24.76%** | **-8.34%** | **2.051** |

The formal model genuinely passes the frozen Validation gate. It does not beat the equal-weight benchmark in Blind or Final OOS, so it has passed the requested Validation milestone but has **not** established persistent incremental Alpha.

## Cost robustness

| Cost multiple | Validation return | MDD | Sharpe | Blind return | Final OOS return |
|---:|---:|---:|---:|---:|---:|
| 0× | +50.12% | -18.54% | 0.829 | +43.24% | +22.87% |
| 1× | +39.19% | -18.91% | 0.688 | +35.08% | +21.46% |
| 2× | +29.03% | -19.99% | 0.545 | +27.37% | +20.06% |
| 3× | +19.60% | -21.19% | 0.402 | +20.09% | +18.68% |

At 2× costs the model still exceeds the Validation benchmark return (+27.16%) and Sharpe (0.471), with lower drawdown. The Train result becomes negative at 2×, showing that turnover remains a material weakness.

## R0 and sleeve utilization

Average weights over the full sample:

- R0 cash: 11.68%
- R1: 24.93%
- R2: 19.94%
- R3: 24.94%
- R4: 18.51%

Median cash is 0%; maximum cash is 55.32%. This confirms that R0 is active but does not routinely eliminate the 80% structural Core.

## Verdict

**Milestone achieved: the corrected low-frequency R0–R4 Router with intra-router stock selection passed Validation without using Blind or 2026 for parameter selection.**

Deployment is still rejected because Blind and Final OOS underperform the simple 12-stock equal-weight control. The frozen model should now remain unchanged. A future generation must address turnover, point-in-time universe/survivorship, dividends and total-return benchmarking with a new Train/Validation design; it must not tune this generation using the already revealed Blind or Final periods.
