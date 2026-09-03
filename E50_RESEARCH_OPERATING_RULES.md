# E50 Research Operating Rules

Operating rules for all future E50 research agents.

Authoritative class definitions live in `FROZEN_GOVERNANCE.md`.
This file is the day-to-day research workflow contract.
If a workflow note disagrees with `FROZEN_GOVERNANCE.md` on class membership, governance wins.

Do not change strategy logic under these rules. Documentation / governance only.

---

## 1. Frozen Governance

### HARD_FROZEN — 研究正確性底線

- Point-in-Time (PIT)
- No look-ahead
- No survivorship bias
- Exact T+1 causal execution
- Walk-Forward
- Embargo
- No future-aware normalization / ranking / model selection

Cannot be relaxed to improve CAGR, Sharpe, turnover, or drawdown.

### SOFT_FROZEN — current official strategy versions

- E16 Core Allocation
- E18 Execution Layer
- E22 execution / dividend / turnover extensions

### SOFT_FROZEN_CRITICAL

- E45 Crisis Protection Core

May be challenged only by a separate challenger with a higher validation bar than E16 / E18 / E22.
The higher bar is a **process** requirement. It does not invent a new MDD, turnover, or bootstrap number.

### EXPERIMENTAL

Includes, without limitation:

- new threshold
- new weight
- new rebalance rule
- new model
- new router
- 2.5% OOF turnover gate
- 0.70 bootstrap gate
- any new acceptance / model-selection gate

**Any EXPERIMENTAL rule must not auto-promote.**

---

## 2. Research Order

Every new research effort must follow this sequence. No skipping.

```
Hypothesis
-> Train / selection window
-> OOF
-> Cost check
-> Stability check
-> Held-out sealed test
-> Stress / Monte Carlo
-> Portfolio integration
-> Governance review
```

---

## 3. Held-out Rule

Once 2019–2022 and/or 2023–latest are used for validation, they must not be used again to tune the same config.

If parameters are changed after looking at held-out results:

1. create a **new challenger**
2. the original held-out window is no longer pure held-out for that new challenger

---

## 4. Performance Target

Long-term targets:

- CAGR >= 20%
- MDD about 10–15%

Targets are not a license to break:

- Exact T+1
- PIT
- OOS discipline
- transaction costs
- frozen baselines
- risk control

Causal correctness outranks performance.

---

## 5. Portfolio Semantics

E50-A is an **Alpha Overlay**, not the whole strategy.

| Regime | Behavior |
|---|---|
| Normal | E16 Core + E50 Alpha |
| Alpha weak | Reduce Alpha first |
| Risk transmission | Shut Alpha down; reduce core risk |
| Crisis | E45 takes over |

Do not treat E50-A as the full portfolio.

---

## 6. Challenger Promotion

A challenger may be proposed for promotion only if at least all of the following hold:

- OOS valid
- held-out valid
- survives costs
- MDD not degraded to an unacceptable level
- Monte Carlo / stress survival
- not relying on hidden leverage
- not relying on excessive concentration
- not relying on high turnover alone
- not relying on a single market year
- reproducible artifacts present

Promotion path (from `FROZEN_GOVERNANCE.md`):

```
FROZEN_BASELINE
-> CHALLENGER
-> OOS VALIDATION
-> COST VALIDATION
-> STRESS / MONTE CARLO VALIDATION
-> GOVERNANCE REVIEW
-> EXPLICIT APPROVAL
-> NEW FROZEN VERSION
```

---

## 7. Failed Experiments

`FAIL` / `INCONCLUSIVE` results must not be deleted.

Every run must retain:

- config
- dataset hash
- metrics
- failure reason
- decision label

---

## 8. Versioning

Do not edit E16 / E18 / E22 / E45 in place.

To challenge an official version, create a named challenger such as:

- `E16-C1`
- `E18-C1`
- `E22-C1`
- `E45-C1`

Only after governance approval may a challenger become a new frozen version beside the prior one.

---

## 9. Current E50-A3-R1 Rule

Current challenger selection uses **2011–2018 OOF only**.

After a config is locked:

1. then inspect 2019–2022
2. then inspect 2023–latest

After looking at held-out results, do **not** retune that same locked config.

R1 numeric gates (2.5% turnover, 0.70 bootstrap, beat-proxy, utility weight, grid) remain **EXPERIMENTAL**.

---

## 10. Final Decision Labels

Each research round must use exactly one of:

- `PASS`
- `FAIL`
- `INCONCLUSIVE`

If the round is a strategy-promotion review, also label one of:

- `PROMOTE`
- `RETAIN_BASELINE`
- `REJECT_CHALLENGER`
