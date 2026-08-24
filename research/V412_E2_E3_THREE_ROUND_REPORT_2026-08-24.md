# V4.12 E2 → E2.1 → E3 Automatic Three-Round Research

Date: 2026-08-24  
Final decision: **E3 passes its frozen Validation gate, but is not promoted over V4.12-D because later OOS superiority is inconsistent.**

## Chronological protocol

| Round | Development data | Untouched Validation | Result |
|---|---|---|---|
| E2 | 2005–2014 | 2015–2017 | FAIL |
| E2.1 | 2005–2017 | 2018–2020 | FAIL |
| E3 | 2005–2020 | 2021–2022 | PASS (6/8 plateau candidates) |

The Validation window advances after each use. The 2023–2025 Blind and 2026 Final windows remained sealed until E3 passed.

Signals use raw/unadjusted OHLCV through close T; orders execute at T+1 open. Corporate-action-adjusted prices are used only for performance evaluation.

## Frozen gate

Every candidate had to satisfy:

- positive Validation return;
- MDD greater than -25%;
- Sharpe at least the frozen V4.12-D Sharpe;
- return at least 80% of frozen V4.12-D return.

Validation can reject but cannot reorder Train-selected plateau candidates.

## Round 1 — E2 Continuous Risk Budget

E2 replaced discrete crisis states with a linear continuous risk score derived from raw 120-day drawdown, 20-day volatility, and 60-day breadth. Exposure updates weekly with fast reduction and slow restoration. The stock-change hurdle equals a fixed multiple of estimated round-trip cost.

Result: **FAIL**. The best plateau candidates reduced drawdown but surrendered too much return and Sharpe in 2015–2017. Best shown candidate returned about 11.34% versus frozen D 20.01%; Sharpe about 0.373 versus 0.564.

## Round 2 — E2.1 Tail-Aware Risk

E2.1 combined average risk with the worst of the three risk components, attempting to react more strongly to concentrated tail stress.

Result: **FAIL**. Best shown Validation result was approximately 17.76% return and 0.540 Sharpe versus frozen D 29.18% and 0.723. Tail protection remained too costly during recoveries.

## Round 3 — E3 Volatility-Targeted Continuous Budget

E3 blends the continuous risk budget with a raw-data volatility target. The frozen winner is:

| Parameter | Value |
|---|---:|
| Maximum exposure cut | 50% |
| Target volatility | 14% |
| Risk / volatility-target blend | 50% / 50% |
| Recovery horizon | 20 trading days |
| Rank buffer | 0 |
| Cost hurdle | 5 × estimated round-trip cost |
| Minimum hold | 42 trading days |

### E3 Validation

| 2021–2022 | E3 | Frozen D | Equal Weight 12 |
|---|---:|---:|---:|
| Return | 25.66% | 27.69% | 31.53% |
| MDD | **-18.49%** | -19.47% | -21.71% |
| Sharpe | **0.919** | 0.888 | 0.967 |
| Volatility | **13.85%** | 15.55% | 15.92% |

E3 passed because it retained 92.65% of D's return while improving D's MDD, Sharpe, and volatility.

## Blind and Final OOS

| Window | Strategy | Return | MDD | Sharpe | Volatility |
|---|---|---:|---:|---:|---:|
| 2023–2025 Blind | E3 | 46.33% | -16.56% | 1.060 | 13.42% |
|  | Frozen D | 50.44% | -16.44% | 1.045 | 14.71% |
|  | Equal Weight 12 | 75.88% | -15.95% | 1.404 | 14.86% |
| 2026 Final | E3 | 19.21% | **-6.38%** | 2.055 | **14.81%** |
|  | Frozen D | 26.39% | -7.47% | 2.210 | 18.46% |
|  | Equal Weight 12 | 30.70% | -8.34% | 2.497 | 18.60% |

E3 reduces volatility and improves the 2026 drawdown, but it does not demonstrate a stable return or Sharpe advantage over D and continues to trail Equal Weight 12 materially.

## Transaction-cost sensitivity

| Cost multiple | 2023–2025 return | 2026 return |
|---:|---:|---:|
| 0× | 55.99% | 20.73% |
| 1× | 46.33% | 19.21% |
| 2× | 37.25% | 17.69% |
| 3× | 28.72% | 16.20% |

Performance remains positive under 3× cost, but the gap between 0× and 1× shows that turnover is still economically important. The cost hurdle did not eliminate enough low-value switching.

## Research decision

- **E2:** rejected.
- **E2.1:** rejected.
- **E3:** Validation survivor and useful low-volatility overlay; not a production replacement for D.
- **Formal strategy remains V4.12-D.**

The next admissible work is an execution-efficiency iteration, not another crisis-threshold search: preserve the frozen E3 exposure controller and redesign only the internal stock-change mechanism using explicit expected edge after cost, partial rebalancing, and longer holding hysteresis.

## Reproducibility files

- `v412e2_e3_three_rounds.py`
- Train grids and Validation gates for E2, E2.1, and E3
- `e3_oos_summary.csv`
- `e3_cost_sensitivity.csv`
- `e3_curves.csv`, `e3_weights.csv`
- `three_round_status.json`

