# V4.12-E4 Execution Efficiency — Three-Round Iteration

Date: 2026-08-24  
Decision: **Engineering champion identified; not eligible for formal promotion until new unseen data arrives.**

## Scope and research-integrity limitation

E4 preserves the frozen E3 volatility-targeted exposure controller and changes only execution. Because 2021–2026 was already revealed during E3, E4's later-period checks are robustness engineering, not fresh Blind/OOS validation. No result below is relabeled as new OOS.

Signals remain raw/unadjusted through close T, execution remains T+1 open, and adjusted prices remain evaluation-only.

## E4-A — Cost-aware hurdle and holding hysteresis

Candidates crossed rank buffer 0/1, score hurdle 5/10/20/30 times estimated round-trip cost, and minimum holds of 42/63/84 trading days.

Winner: rank buffer 0, 5× hurdle, minimum hold 84 days.

The 5× through 30× hurdle settings frequently produced identical results. The hurdle usually did not bind; extending the holding period to 84 days generated the real turnover reduction.

## E4-B — Partial rebalancing

Candidates moved 25%, 50%, 75%, or 100% of the distance toward each new target, subject to target-weight-change floors of 5%, 10%, or 20%.

Winner: **25% partial rebalance, 5% floor**. The three floors were often identical, showing again that threshold size was not the main driver. Partial execution was the effective mechanism.

## E4-C — D/E3 execution blend

The E4-B execution target was blended with the original D target at 25%, 50%, 75%, and 100% efficient-strategy weight. The robust winner retained **100% E4-B**. Mixing D execution back in increased turnover and reduced the cross-regime score.

## Final engineering candidate

- E3 continuous volatility/risk exposure controller.
- Maximum exposure cut: 50%.
- Target volatility: 14%.
- 20-day slow recovery.
- Minimum stock holding: 84 trading days.
- Cost hurdle: 5× estimated round-trip cost.
- Rebalance only 25% of the distance toward a new stock target.

## Cross-regime comparison

| Period | Strategy | Return | MDD | Sharpe | Turnover |
|---|---|---:|---:|---:|---:|
| 2015–2017 | E4-B | 19.34% | **-22.45%** | **0.635** | **6.81** |
|  | D | 20.01% | -25.31% | 0.564 | 26.38 |
| 2018–2020 | E4-B | 22.73% | **-21.19%** | 0.685 | **7.15** |
|  | D | 29.18% | -24.09% | 0.723 | 28.07 |
| 2021–2022 | E4-B | 26.21% | **-17.51%** | **0.969** | **4.88** |
|  | D | 27.69% | -19.47% | 0.888 | 19.84 |
| 2023–2025 | E4-B | **51.31%** | **-15.54%** | **1.177** | **7.04** |
|  | D | 50.44% | -16.44% | 1.045 | 26.74 |
| 2026 | E4-B | 21.70% | **-7.02%** | **2.273** | **1.41** |
|  | D | 26.39% | -7.47% | 2.210 | 5.23 |

Turnover reduction versus D is consistently about 73%–75%. E4-B improves D's MDD in every shown regime and improves Sharpe in four of five regimes, while sacrificing return in 2018–2020 and 2026.

## Cost stress

| Cost multiple | 2021–2022 return | 2023–2025 return | 2026 return |
|---:|---:|---:|---:|
| 0× | 27.68% | 53.81% | 22.14% |
| 1× | 26.21% | 51.31% | 21.70% |
| 2× | 24.75% | 48.86% | 21.27% |
| 3× | 23.31% | 46.44% | 20.84% |

Unlike E3, the gap between 0× and 1× costs is now small. Three-times-cost outcomes remain positive and risk-adjusted performance remains usable.

## Decision

- E4-A identifies longer holding hysteresis as useful; score hurdles alone are mostly non-binding.
- E4-B is the execution-efficiency winner.
- E4-C rejects mixing D execution back into the candidate.
- **Formal live/research benchmark remains V4.12-D** because no unseen historical window remains.
- E4-B should be frozen now as the forward paper-trading challenger. No further historical parameter tuning should occur before new observations accumulate.

## Reproducibility files

- `v412e4_execution_efficiency.py`
- `e4a_grid.csv`, `e4a_confirmation.csv`
- `e4b_grid.csv`, `e4b_confirmation.csv`
- `e4c_grid.csv`, `e4_multiregime_summary.csv`
- `e4c_cost_stress.csv`, `e4c_weights.csv`
- `e4_status.json`

