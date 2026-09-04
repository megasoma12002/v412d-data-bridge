# E50 Hedge Charter (G4)

Date: 2026-09-04  
Status: **CHARTER ONLY** — no hedge code, no shorts, no options sleeve  
Decision: **`NOT_REQUIRED_NOW`**

## Product question (must answer before any code)

Does the product still require **「股災也要賺 / 深度避險」** after:

- formal crisis baseline remains **V4.12-D** (E45-C1 → decision **B**),
- paper four-layer already **cuts alpha before core** via E45 exposure signal,
- Option-2 alpha is **MIXED / saturated** (fork 3B)?

If the answer is **no** (or undecided), **do not** open a hedge challenger.

## Evidence already in hand

| Fact | Implication |
|---|---|
| E45-C1: E3 improves MDD vs D but fails return/Sharpe floor | No promoted E45 de-lever engine; D stays formal |
| `forward/e50_stack/` alpha-cut-first QC PASS | Operating hedge ≈ **reduce risk**, not crash PnL |
| Alpha-only MDD ~−50% on four-layer window | Any future hedge should target **alpha sleeve tail**, not rewrite E16 |
| No product sign-off for shorts / puts / inverse ETF | Charter stop rule applies |

## Decision

**`NOT_REQUIRED_NOW`**

Interpretation:

- Current stack meets the **documented** risk path: D crisis baseline + paper alpha-cut-first + cash residual.
- “Crash also profit” is a **product upgrade**, not a research debt.
- Opening shorts/options without sign-off would violate GAP_FILL_PLAN stop rules.

## Reopen criteria (all required)

1. Explicit product / governance request for crash PnL beyond de-lever.  
2. Written budget: hedge notional ≤ X% of NAV; funded by cutting alpha first, then core tilt.  
3. Separate challenger folder (never silent-add into E16 membership).  
4. Evaluation pre-registered: crisis-window mean excess vs core+alpha without hedge; bull-regime cost drag.  
5. Higher promotion bar than alpha; Exact T+1 / PIT unchanged.

## If reopened — allowed instruments (EXPERIMENTAL only)

- Cash buffer (already used in alpha-cut) — prefer first  
- Index short / inverse ETF / put budget — only after budget rule  
- **Not allowed:** treating S9A1 as hedge; editing E16 Crisis tilt in place as “hedge”

## Explicit non-actions (this charter)

- No `scripts/e50_hedge_*.py` until reopen criteria pass  
- No change to `forward/e21/` or SOFT_FROZEN versions  
- No claim that four-layer util proves crash profitability  

## Sign-off

| Role | Status |
|---|---|
| Research (this PR) | Recommends `NOT_REQUIRED_NOW` |
| Product / governance | **Pending** — silence = stay closed |
