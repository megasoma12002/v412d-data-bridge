# V4.12-E1.1 Graduated Crisis Budget + Recovery Ramp

Date: 2026-08-24  
Decision: **VALIDATION FAIL — not promoted**

## Purpose

E1.1 tests whether E1 failed because its binary 25% crisis exposure was too defensive. It replaces that switch with graduated exposure and a recovery ramp, while retaining raw-only signals, T+1 open execution, and adjusted-price evaluation.

## Frozen protocol

- Train: 2005-03-01 to 2011-12-30.
- Validation: 2012-01-01 to 2014-12-31.
- Frozen parent: V4.12-D family 1, top 2, 21-day rebalance, 75-day Capital Lock, 80% Core + 20% Tilt.
- Crisis thresholds inherited from the E1 Train plateau: 120-day drawdown -18%, volatility 30%, breadth 30%.
- 2015–2026 remains sealed unless a candidate passes Validation.

## Structural changes

- Medium and severe exposure levels replace the binary 25% exposure state.
- Risk deterioration requires two consecutive confirmations.
- Recovery is ramped over 10 or 20 trading days.
- An independent portfolio-weight no-trade band of 5% or 10% suppresses small reallocations.
- Rank buffer, challenger score gap, and minimum hold remain causal.

Three exposure/ramp structures crossed with 16 turnover structures produced 48 Train candidates. Eight robust-plateau candidates received one-time Validation.

## Frozen gate

Every condition had to pass: return > 0; MDD > -25%; Sharpe at least frozen D; return at least 80% of frozen D.

## Results

Best Train candidate used medium exposure 80%, severe exposure 40%, 20-day recovery, rank buffer 0, score gap 0, minimum hold 42 days, and a 5% or 10% no-trade band.

| Metric | E1.1 | Frozen D | Gate result |
|---|---:|---:|---|
| 2012–2014 return | 38.46% | 40.86% | passes 80% return floor |
| 2012–2014 MDD | -15.81% | -14.32% | worse than parent |
| 2012–2014 Sharpe | 0.832 | 0.856 | fail |
| 2008–2009 Train MDD | -37.47% | — | better than full exposure, weaker than E1 |

All eight candidates failed. E1.1 closes most of E1's recovery-period performance gap, but it does not improve the frozen parent's risk-adjusted Validation outcome.

## Diagnostics

1. Graduated exposure fixes much of the binary budget's opportunity-cost problem.
2. The 5% and 10% no-trade bands produced identical outcomes. Rebalance target changes are generally larger than 10%, so these bands do not bind.
3. The remaining problem is not merely the recovery speed. Discrete risk voting still reduces exposure during drawdowns that subsequently reverse, producing slightly worse MDD and Sharpe than D.
4. Reusing 2012–2014 for further threshold tuning would contaminate the gate. E1.1 is therefore archived without opening 2015–2026.

## Next admissible research stage

The next version should be **V4.12-E2 Continuous Risk Budget + Stateful Trade Hurdle**:

- replace discrete crisis votes with a clipped continuous risk score;
- adjust exposure weekly, with an asymmetric fast-down/slow-up controller;
- apply the turnover hurdle to expected score improvement net of estimated trading cost, rather than total target-weight distance;
- roll the research clock forward: incorporate the now-consumed 2012–2014 evidence into development and use 2015–2017 as the next untouched Validation window;
- preserve 2018–2026 as untouched OOS.

This avoids repeatedly tuning against the same Validation period.

## Files

- `v412e11_graduated_crisis.py`
- `e11_train_grid.csv`
- `e11_validation_gate.csv`
- `e11_status.json`

