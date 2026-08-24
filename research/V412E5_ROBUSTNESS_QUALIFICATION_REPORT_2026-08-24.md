# V4.12-E5 Robustness Qualification — Four-Round Study

Date: 2026-08-24  
Decision: **Frozen E4 passes robustness qualification; remains a forward challenger, not a formally promoted replacement.**

## Integrity boundary

E5 does not tune E4. It tests the already frozen E4 weights and nearby mechanics. Since 2021–2026 had already been revealed, the results are robustness evidence rather than new Blind/OOS validation.

The E4 baseline was independently reconstructed from saved weights. Return, MDD, and Sharpe differences versus the prior E4 output were below approximately 1.2e-14, passing numerical reconciliation.

## Round 1 — Paired moving-block bootstrap

One thousand paired resamples were run at 21-day and 63-day block lengths, preserving local serial dependence and sampling E4 and D on identical dates.

| Period | Block | P(E4 return > D) | P(E4 MDD better) | P(E4 Sharpe > D) |
|---|---:|---:|---:|---:|
| 2015–2020 | 21 | 22.1% | 93.6% | 57.0% |
| 2015–2020 | 63 | 19.1% | 89.9% | 52.5% |
| 2021–2022 | 21 | 38.5% | 89.3% | 65.1% |
| 2021–2022 | 63 | 28.0% | 95.3% | 60.6% |
| 2023–2025 | 21 | 57.0% | 92.0% | 85.3% |
| 2023–2025 | 63 | 59.3% | 92.2% | 89.1% |
| 2026 | 21 | 11.7% | 97.4% | 71.6% |
| 2026 | 63 | 3.9% | 97.0% | 78.5% |

Conclusion: E4's drawdown advantage is highly stable and its Sharpe advantage is more likely than not, but its return advantage is not general. E4 must be described as a defensive/risk-adjusted strategy, not a return-maximizer.

## Round 2 — Leave-one-stock-out

Each of the 12 stocks was removed in turn and its weight redistributed only across other currently held names while preserving total exposure.

Worst observed results remained positive:

| Period | Worst return | Worst Sharpe | Worst MDD |
|---|---:|---:|---:|
| 2015–2020 | 42.78% (exclude 2884) | 0.618 (exclude 2884) | -23.53% (exclude 2801) |
| 2021–2022 | 23.02% (exclude 2881) | 0.903 (exclude 2881) | -18.53% (exclude 2801) |
| 2023–2025 | 46.52% (exclude 2881) | 1.103 (exclude 2891) | -16.65% (exclude 2801) |
| 2026 | 19.69% (exclude 2885) | 2.140 (exclude 2885) | -7.26% (exclude 5880) |

No individual stock is required for the candidate to remain profitable. This materially reduces single-name dependence concern.

## Round 3 — Frozen parameter neighborhood

The neighborhood crossed minimum holds of 63/84/105 trading days with partial rebalance fractions of 20%/25%/33%. No winner was selected.

| Period | Return range | Sharpe range | MDD range |
|---|---:|---:|---:|
| 2015–2020 | 45.43%–47.29% | 0.646–0.669 | -22.49% to -22.10% |
| 2021–2022 | 25.80%–27.04% | 0.960–0.993 | -18.08% to -17.44% |
| 2023–2025 | 50.57%–53.48% | 1.160–1.225 | -15.88% to -14.96% |
| 2026 | 21.58%–22.21% | 2.269–2.303 | -7.05% to -6.78% |

All nine neighboring configurations remain usable and positive. The frozen 84-day/25% point lies on a broad plateau rather than an isolated optimum.

## Round 4 — Execution shocks

The worst combined shock adds two trading days of execution delay, triples fees/tax assumptions, and adds 25 bps of slippage per unit of turnover.

| Period | Return | MDD | Sharpe |
|---|---:|---:|---:|
| 2015–2020 | 33.45% | -24.26% | 0.509 |
| 2021–2022 | 22.19% | -18.43% | 0.835 |
| 2023–2025 | 44.54% | -16.17% | 1.051 |
| 2026 | 21.16% | -7.15% | 2.209 |

All stressed periods remain positive. The 25% partial-rebalance design substantially reduces sensitivity to operational friction.

## Qualification decision

All predeclared checks passed:

- baseline numerical reconciliation;
- bootstrap drawdown/Sharpe majority criterion;
- positive return for every leave-one-out scenario;
- positive return throughout the parameter neighborhood;
- positive return under the worst combined execution shock.

Therefore E4 is **robustness-qualified as a low-volatility forward challenger**. It is not formally promoted because there is no unused historical OOS window. V4.12-D remains the formal benchmark, while E4 should now be frozen for future paper-trading comparison.

No further historical optimization is recommended. The next legitimate evidence must come from newly arriving daily data.

## Reproducibility files

- `v412e5_robustness_qualification.py`
- `e5_baseline_reconciliation.csv`
- `e5_round1_block_bootstrap.csv`
- `e5_round2_leave_one_out.csv`
- `e5_round3_parameter_neighborhood.csv`
- `e5_round4_execution_shocks.csv`
- `e5_status.json`

