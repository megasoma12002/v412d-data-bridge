# V4.12-E0 Historical Expansion

Date: 2026-08-24  
Status: **raw history PASS; corporate-action-adjusted research layer PASS**

## Deliverables

- Canonical raw/unadjusted OHLCV expanded from 2010 to the earliest available 2004 archive.
- Daily point-in-time trading/252-day indicator eligibility table.
- Separate corporate-action event table.
- Separate backward-adjusted research price layer; never used for execution.
- Historical stress evaluation of the frozen V4.12-D model; no E0 parameter selection.

## Data coverage and QC

- Source archives: yearly 2004–2025 plus 2026 weekly archives.
- Combined rows: 64,535, up from 48,411.
- Eleven stocks begin around 2004-02-11; 5880 begins at its actual 2011-12-01 availability.
- All 12 end at 2026-08-21.
- Duplicate dates: zero.
- OHLC/negative-volume violations: zero.
- One official 2884 missing-price row was skipped and documented.
- Corporate-action events: 304 across the 12 stocks.
- Adjusted research rows: 64,535.

The adjusted layer multiplies each historical raw price by future official-event `after_price / before_price` factors. Event-day price remains raw. It is a research-grade corporate-action-adjusted series, not an exchange-provided individual-stock total-return index.

## Frozen-model historical stress

Frozen model: family 1, Top 2, 21-day rebalance, 75-day Capital-Lock. The model was not reselected using the added years.

| Window | Formal Router adjusted | MDD | Sharpe | EqualWeight12 adjusted | MDD | Sharpe |
|---|---:|---:|---:|---:|---:|---:|
| 2005–2007 | +3.71% | -19.55% | 0.163 | -3.05% | -19.37% | 0.038 |
| 2008–2009 | +17.12% | -58.44% | 0.400 | +10.06% | -59.86% | 0.325 |
| 2010–2014 | +35.18% | -30.92% | 0.411 | +48.90% | -32.08% | 0.497 |
| 2015–2017 | +20.01% | -25.31% | 0.564 | +23.89% | -27.52% | 0.627 |
| 2018–2020 | +29.18% | -24.09% | 0.723 | +35.87% | -26.65% | 0.802 |
| 2021–2022 | +27.69% | -19.47% | 0.888 | +31.53% | -21.71% | 0.967 |
| 2023–2025 revealed | +50.44% | -16.44% | 1.045 | +75.88% | -15.95% | 1.404 |
| 2026 Final | +26.39% | -7.47% | 2.210 | +30.70% | -8.34% | 2.497 |

## Interpretation

- The formal router helped in the newly added 2005–2009 history relative to equal weight.
- It did not prevent the severe 2008 crisis drawdown; R0/Tilt-only cash is insufficient as a crisis veto.
- From 2010 onward, it usually reduced drawdown modestly but sacrificed more return and Sharpe than justified.
- Raw-price performance was materially lower than corporate-action-adjusted performance, confirming that dividend/corporate-action separation was necessary for financial stocks.
- This E0 stress result does not change the frozen model and does not turn old history into chronological OOS, because the frozen model was developed later.

## Remaining bias

`router` currently records the present research classification with an explicit warning. Historical corporate identity/business-model classification and disappeared financial stocks have not yet been reconstructed, so full survivorship and point-in-time classification bias remain unresolved.

## E0 verdict

Historical data expansion is complete and materially useful. The next admissible generation should be V4.12-E1 Crisis Budget and Turnover Buffer: retain the 80% Core concept under normal conditions, add a separately trained absolute crisis-risk budget, and reduce unnecessary turnover with ranking buffers. Its parameters must be trained on early walk-forward folds rather than the already revealed 2023–2026 periods.
