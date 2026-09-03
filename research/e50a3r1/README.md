# V4.12-E50-A3-R1 Repair Research

R1 attempts to repair the failed E50-A3 baseline without reading the frozen
2019-2022 validation period during model or portfolio selection.

## Repair layers

1. A fixed, causal market-breadth regime separates risk-on and risk-off model
   coefficients. The state uses only T-close 63-session breadth and momentum.
2. A candidate score can be neutralized against T-known industry and liquidity
   buckets. Historical par-value value proxies remain excluded.
3. A rank buffer retains existing positions until they fall outside 1.25x,
   1.5x or 2x the entry breadth, reducing forced round trips.
4. Industry caps prevent one sector from dominating the attack sleeve.

All feature sets, model modes, ridge penalties, breadth, rebalance interval,
buffer and caps are selected on embargoed 2011-2018 OOF results only. A daily
turnover ceiling of 2.5% is imposed before maximizing after-cost
`CAGR - 0.5 * abs(max drawdown)`.
If no candidate satisfies that ceiling, the report records zero feasible
candidates and promotion is blocked even when a later period looks strong.

## Promotion gate

These numeric gates are EXPERIMENTAL under `FROZEN_GOVERNANCE.md`
(新模型 / 新門檻 / 新權重 / 新 rebalancing). They are not HARD_FROZEN and
not part of the official E16 / E18 / E22 / E45 versions. A strong sealed
window does not auto-promote them.

R1 remains research-only unless both 2019-2022 and 2023-latest beat the
point-in-time market proxy after costs and both 21-session block-bootstrap
positive-excess probabilities reach 70%. E45 remains untouched until a later
approved overlay-to-crisis handoff experiment says otherwise. The 2.5%
turnover ceiling, 70% bootstrap cutoff, grid, and utility formula stay
EXPERIMENTAL until explicit approval creates a new frozen version. The prior
E16 / E18 / E22 / E45 official versions must not be overwritten.
