# V4.12-E1 Crisis Budget + Turnover Buffer

Date: 2026-08-24  
Decision: **VALIDATION FAIL — not promoted**

## Research protocol

- Canonical signals and portfolio decisions use raw/unadjusted OHLCV only.
- A signal formed at close T is executed at open T+1.
- Corporate-action-adjusted prices are used only for performance evaluation.
- Model selection window: 2005-03-01 through 2011-12-30.
- Frozen Validation gate: 2012-01-01 through 2014-12-31.
- 2015–2026 was not used to choose or rescue an E1 candidate after the gate failed.
- Frozen parent: V4.12-D, family 1, top 2 per router, 21-day rebalance, 75-day capital lock, 80% Core + 20% monthly Tilt.

## E1 additions

### Crisis Budget

The full portfolio, including Core, can be scaled when at least two of three causal signals agree:

1. Equal-weight financial proxy 120-day drawdown.
2. Equal-weight proxy 20-day annualized volatility.
3. Fraction of available stocks above their 60-day EMA.

Two consecutive crisis observations are required to enter and five clear observations to exit. The state known at T only changes exposure at T+1 open.

### Turnover Buffer

- Rank buffer: 0 or 1 place beyond the normal top-2 selection.
- Challenger score gap: 0, 0.05, or 0.10.
- Minimum hold: 0, 21, or 42 trading days.
- The inherited 75-day Capital Lock remains active.

Four predeclared crisis definitions crossed with 18 buffer settings produced 72 Train candidates. A robust-plateau filter selected eight candidates for one-time Validation.

## Frozen Validation gate

Every condition had to pass:

- return > 0;
- maximum drawdown > -25%;
- Sharpe at least the frozen D Sharpe;
- return at least 80% of frozen D return.

## Results

Best Train candidate:

| Parameter | Value |
|---|---:|
| Drawdown threshold | -18% |
| Volatility threshold | 30% |
| Breadth threshold | 30% |
| Crisis exposure | 25% |
| Rank buffer | 0 |
| Score gap | 0.00 |
| Minimum hold | 42 days |

| Window / metric | E1 | Frozen D | Result |
|---|---:|---:|---|
| 2005–2011 Train return | 23.38% | — | selection only |
| 2005–2011 Train max drawdown | -30.84% | — | selection only |
| 2005–2011 Train Sharpe | 0.251 | — | selection only |
| 2008–2009 max drawdown | -30.84% | — | materially crisis-protective |
| 2012–2014 Validation return | 30.07% | 40.86% | fail: below 80% floor |
| 2012–2014 Validation max drawdown | -17.21% | -14.32% | worse |
| 2012–2014 Validation Sharpe | 0.675 | 0.856 | fail |

All eight Train-selected plateau candidates failed. The strongest Validation return among them was about 30.99%, still below the frozen D return floor and with lower Sharpe.

## Interpretation

The crisis layer demonstrated useful early-crisis protection, but the binary 25% exposure state stayed too defensive during subsequent recovery conditions. The turnover buffers did not offset that opportunity cost. Because the failure appears in the frozen 2012–2014 gate, later performance must not be consulted to select this version.

## Decision and next admissible iteration

V4.12-E1 is retained as a reproducible rejected experiment. It must not replace V4.12-D.

The next clean hypothesis is E1.1: a graduated crisis budget (for example 100% / 70% / 40%) with a recovery ramp and a separate turnover no-trade band. It should reuse the same Train/Validation boundary and receive a new, predeclared gate before any 2015–2026 evaluation. This is a structural change, not a threshold rescue of E1.

## Reproducibility

- `v412e1_crisis_buffer.py`: causal simulator and gate.
- `e1_train_grid.csv`: all 72 Train outcomes.
- `e1_validation_gate.csv`: eight plateau candidates and the fixed gate.
- `e1_status.json`: machine-readable rejection status.

