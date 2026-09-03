# Frozen Governance

This document is the Frozen Governance contract for the whole research program.

It applies to:

- E16 Core Allocation
- E18 / E22 Execution Layer
- E44 Exact T+1 clock
- E45 Crisis Protection Core
- E50-A overlay research
- all future E50 challengers (R1, R2, A4, routers, cost models, crisis handoff tests)

If a later note disagrees with this file, this file wins until a new frozen version is explicitly approved.

---

## 0. Purpose

Frozen rules exist to protect causal correctness, Exact T+1, point-in-time integrity, and baseline reproducibility.

They do **not** exist to lock in a performance number.

Long-term targets (CAGR >= 20%, MDD about 10–15%) remain targets. They are not a license to relax HARD_FROZEN rules.

---

## 1. Rule classes

Every research rule is one of:

### HARD_FROZEN

Cannot be relaxed to improve CAGR, Sharpe, turnover, or drawdown.

A HARD_FROZEN rule may be *implemented more strictly*, but it may not be weakened, bypassed, or renamed as “research-only” in a production-claiming result.

### SOFT_FROZEN

The current baseline implementation is retained.

It may be challenged only through a separate challenger experiment. The original baseline artifacts, code path, and reported metrics must be preserved. The challenger must not overwrite or delete the prior frozen baseline.

A SOFT_FROZEN challenger that looks better is still not the new baseline until the promotion path completes.

### EXPERIMENTAL

Temporary research settings: thresholds, weights, bootstrap cutoffs, rebalance frequencies, model rules, router rules, cost-stress numbers, and overlay promotion gates.

EXPERIMENTAL rules **never become frozen automatically**, including when:

- a backtest looks strong
- sealed-period CAGR is high
- CI is green
- a filename contains `frozen_`
- a README says “selected configuration”

Default: any newly introduced threshold, weight, bootstrap cutoff, rebalance frequency, model rule, or router rule is **EXPERIMENTAL** unless it is explicitly promoted.

---

## 2. Promotion path

No SOFT_FROZEN or EXPERIMENTAL rule may replace a baseline except through:

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

Required properties of a challenger:

1. New experiment branch / output folder.
2. Named hypothesis.
3. Original frozen baseline kept intact (code, artifacts, metrics, hashes).
4. Side-by-side report: baseline, challenger, incremental benefit, additional risk, OOS stability, transaction-cost impact.
5. Decision: PASS / FAIL / INCONCLUSIVE.
6. Explicit human approval before any new frozen version is recorded.
7. Prior frozen version remains readable forever. Never overwrite. Never delete.

A new frozen version, if approved, is additive: `FROZEN_vN` stays, `FROZEN_vN+1` is published beside it.

---

## 3. HARD_FROZEN

These cannot be relaxed for performance.

### Causal clock

- Information(T) -> Feature(T) -> Signal(T) -> Order -> next market session -> T+1 open fill
- No same-bar execution
- No Close(T) signal filled at Close(T)
- No replacing a missing T+1 open with a future-selected substitute name

### Point-in-time and leakage

- No future financial releases
- No revised data leaked backward
- No future constituent membership
- No future corporate actions as pre-event signals
- No future normalization statistics
- No future delisting knowledge
- No full-sample ranking or full-sample scaling
- No label leakage into features
- No train/validation/test contamination
- No survivorship-only universe

### Walk-forward

- Fit / transform / calibration use only the allowed train window
- Embargo remains in force where the current causal pipeline requires it
- Validation and sealed/test windows are not used to select the model or portfolio rule being tested

### Portfolio role

- E50-A is an alpha overlay, not the whole portfolio
- E16 remains the core allocation role
- E18/E22 remains the execution-layer role
- E45 remains the crisis-protection role, not an alpha model
- Alpha weakening is not crisis
- Alpha is reduced before the core portfolio
- Crisis-level risk control is handed to E45
- 0050 leveraged ETF (0050 正二) is not in the core strategy

### Baseline integrity

- Do not overwrite or delete a prior frozen baseline
- Do not restart the portfolio from scratch
- Do not rebuild E50-A0/A1/A2 unless a reproducible upstream defect is identified
- Do not claim PASS without reproducible evidence
- Failed experiments are retained

---

## 4. SOFT_FROZEN

These are current baselines. Challenge them only with a preserved-baseline challenger.

### E16 Core Allocation

- Role is HARD_FROZEN.
- Current implementation is SOFT_FROZEN: public-financial sleeve, telecom sleeve, 0050 sleeve, and the current E16 target-construction path (including the E21 forward ledger).
- A new E16 weight, membership list, or sleeve mix is a challenger, not an in-place edit.

### E18 / E22 Execution Layer

- Exact T+1 as a clock is HARD_FROZEN.
- Current execution implementation is SOFT_FROZEN: live/forward fill policy, turnover/rebalance friction as coded in the E21/E18 path, E22 dividend event ledger, and the hold-through-ex vs sell-before-ex economic-return research.
- Changing fees, tax, slippage, lot policy, or dividend cashflow timing in that baseline path requires a challenger folder. Do not patch the baseline ledger in place.

### E45 Crisis Protection Core

- Role is HARD_FROZEN: crisis-level reduction of equity exposure; not an alpha model.
- Current crisis implementation / parameters / reported MDD benchmark are SOFT_FROZEN.
- The handoff claim “MDD about -13.16%” remains a baseline claim that must be verified from artifacts; it is not a performance target that can be traded off by weakening E45.
- Retuning E45 thresholds, vote rules, or exposure schedules requires a challenger that still reports the original E45 baseline.

### E50 data contracts currently used by A3/R1

- PIT / delisting / available_date contracts are HARD_FROZEN.
- The pinned A0/A1/A2 artifact versions currently referenced by A3/R1 workflows are SOFT_FROZEN data baselines.
- Replacing those artifacts is a data-challenger event. Do not silently rebuild.

### Router architecture currently retained

- Financial vs private-financial split, Telecom Harvest -> Financial Reentry, 0050 as beta/risk-on/allocation alternative, and cash/short-bond as a low-edge parking role are SOFT_FROZEN retained architecture.
- Specific router weights, lookbacks, and rebalance days inside those modules are EXPERIMENTAL unless a later frozen version names them.

---

## 5. EXPERIMENTAL

Never auto-promoted. Includes, without limitation:

### E50-A3 / E50-A3-R1

- Feature sets (`TECH2`, `PRICE8`, family scores)
- Ridge lambdas
- Breadth-regime definition and cutoffs
- Neutralization mode
- `top_k`, `rebalance_every`, `exit_multiple`, `industry_cap`
- Rank-buffer multiples 1.25 / 1.5 / 2.0
- Utility `CAGR - 0.5 * abs(MDD)`
- R1 2.5% average daily turnover ceiling
- Bootstrap positive-excess cutoff 0.70
- “Beat PIT market proxy after costs” promotion test
- A3 overlay simulator costs (14.25bp, 30bp tax, 5bp slippage) when used inside E50-A research, as distinct from the E18/E22 baseline path
- NT$20 million liquidity filter
- Incomplete-session 75% quote-count rule inside A3
- Any `frozen_model.json` / `frozen_repair_model.json` selected config (filename does not confer frozen status)

### Future E50 work

- Tree / boosting / ensemble / new regime-aware models
- New router weights, sleeves, or rebalance calendars
- New cost, slippage, or delay assumptions
- New crisis-overlay handoff thresholds between Alpha and E45
- Audit-only diagnostics (for example gross-exposure > 1.001)

If a number is not listed in HARD_FROZEN or SOFT_FROZEN above, it is EXPERIMENTAL.

---

## 6. Layer-specific application

| Layer | HARD_FROZEN | SOFT_FROZEN | EXPERIMENTAL |
|---|---|---|---|
| E16 | Core-allocation *role*; core does not exit because alpha is weak | Current sleeve set and target path | Any new weight, name list, or mix |
| E18/E22 | Exact T+1 clock; no same-bar; no theoretical fill in place of an executable policy | Current forward/dividend implementation | Any new fee, tax, slippage, lot, or rebalance friction number |
| E44 | Causal clock contract | Current named clock audit/implementation path | Extra diagnostic cutoffs |
| E45 | Crisis-protection *role*; not an alpha model; crisis ≠ alpha-weak | Current crisis baseline implementation | New vote cuts, scales, ramps, or handoff thresholds |
| E50-A | Overlay *role*; PIT; walk-forward; Exact T+1; no leakage-for-CAGR | Pinned A0/A1/A2 artifacts now used by A3/R1 | All model, grid, bootstrap, turnover, and overlay cost numbers |
| Future E50 challengers | Inherit all HARD_FROZEN rows | Must keep the then-current baseline beside the challenger | Default class for every new rule |

---

## 7. Cursor / agent constraints

Agents may not:

- weaken HARD_FROZEN rules to hit CAGR or MDD targets
- edit E16, E18/E22, or E45 baseline files in place and still call them the original baseline
- promote an EXPERIMENTAL threshold because a sealed window looks strong
- delete failed experiments
- rebuild A0/A1/A2 without a reproducible upstream defect
- treat `frozen_*.json` output names as governance promotion

Agents must:

- write challengers to a new folder / branch
- classify every new number as EXPERIMENTAL
- keep baseline vs challenger artifacts
- stop performance work when leakage or clock contamination is found
