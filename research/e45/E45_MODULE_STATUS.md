# E45 Module Status

Date: 2026-09-04  
Module: `scripts/e45_crisis_core.py`  
Status: **`CHALLENGER_CANDIDATE_NOT_PROMOTED`**

## What was wrong

Governance named **E45** as `SOFT_FROZEN_CRITICAL`, but the repo only had:

- a **role** in `FROZEN_STRATEGY_SPEC.md`
- a scattered lineage (E1 / E1.1 / E2 / E2.1 / E3)
- a text claim MDD ≈ −13.16% with **no matching artifact**
- **no** importable `e45` package

## What this module is

A **named Python surface** that packages lineage controllers without editing E1/E11/E2–E3 scripts and without self-promoting:

| Profile | Meaning |
|---|---|
| `PASSTHROUGH` | exposure = 1 |
| `E1_BINARY` | binary crisis × scale 0.50 (E1-style) |
| `E3_VOLTARGET_WINNER` | locked E3 winner from `research/v412e2e3/e3_status.json` (**default**) |

Machine status: `research/e45/e45_status.json`

## What this is NOT

- Not a promotion to `SOFT_FROZEN_CRITICAL`
- Not a verification of MDD ≈ −13.16% (still `UNVERIFIED_TEXT_ONLY`)
- Not a replacement for formal strategy **V4.12-D** (E3 remains `validation_pass_but_not_promoted`)

## E45-C1 result (2026-09-04)

Ran `scripts/e45_c1_verified_baseline.py` on reconstructed 12-stock PIT panel.

**Recommendation: `B_KEEP_D_AS_BASELINE_E45_API_ONLY`**

- E3 improves Validation/Full/Crisis MDD vs D (MC P(better MDD)≈0.99)
- Fails return ≥80% of D and Sharpe ≥ D on Validation
- Therefore: **keep V4.12-D as crisis baseline**; named module stays API packaging
- Artifacts: `research/e45/E45_C1_DECISION.md`, `e45_verified_baseline.json`

## Promotion path (unchanged)

Separate challenger folder → preserve baseline → crisis stress + MC → cost validation → **explicit governance approval** → new frozen version.  
See `FROZEN_GOVERNANCE.md` §1 / §4.

## Integration

Early-stack sandbox wires the named module:

```bash
python3 scripts/e50_early_stack_combined_nav.py \
  --market forward/e21/live_market.csv \
  --dividends data/dividend_events/e22_dividend_events.csv \
  --out repro/early-stack-combined-nav-20260904
```

Variants include `E16_E18_E22_E45_E3` and `E16_E18_E22_E45_E1`.
