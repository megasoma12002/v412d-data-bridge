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

A **named Python surface** that packages lineage controllers without editing E1/E11/E2–E3 scripts and without self-promoting.

Machine status: `research/e45/e45_status.json`

## E45-C1 (authoritative = original v412e0)

Recovered Actions artifact run `32733969384` (`v412e0-historical-expansion`).

**Recommendation: `B_KEEP_D_AS_BASELINE_E45_API_ONLY`** (confirmed on original raw+adjusted)

- E3 improves Validation/Full/Crisis MDD vs D (MC P≈0.99)
- Fails return ≥80% of D and Sharpe ≥ D on Validation
- Keep **V4.12-D** as crisis baseline; named module stays API packaging
- Handoff MDD −13.16%: still `UNVERIFIED_TEXT_ONLY`

Artifacts:

- `research/e45/E45_C1_DECISION.md` (original panel)
- `research/e45/e45_verified_baseline.json`
- `repro/e45-c1-v412e0-original-20260904/`
- PIT reconstruction kept as secondary: `E45_C1_DECISION_PIT.md`

## Explicit non-actions

- Not promoted to `SOFT_FROZEN_CRITICAL`
- No in-place E45 freeze
- No retune of E3 winner
