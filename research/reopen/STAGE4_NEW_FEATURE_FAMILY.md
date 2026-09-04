# Research Stage 4 — New 3A Feature Family

Date: 2026-09-04  
Prior: Stage/Round-3 stopped `z(oi_yoy)-z(amihud)` (`STOP_THIS_FEATURE_SET`)  
Rule: **no retune** of stopped score; new family only

## Stage goal

Test one **new** causal feature pair outside the stopped set and outside TECH2/PRICE8:

| Feature | Source | PIT key |
|---|---|---|
| `rev_yoy_12m` | A1 `causal_monthly_revenue` | `available_date` |
| `cfo_yoy` | A1 `CashFlowsFromOperatingActivities` | `available_date` |

**Not used:** OperatingIncome YoY, Amihud, TECH2, S9A1, A3-R1 model.

## Pre-registered portfolio

- Score: `z(rev_yoy_12m) + z(cfo_yoy)` within month  
- Long top 20% EW vs universe EW  
- Dev 2019–2024 → adversarial-lite (cost 40bps, turnover, industry cap, LOYO)  
- Sealed held-out 2025+ opened only after dev gates  

## Decisions

| Outcome | Action |
|---|---|
| Dev net40 fail | `STOP_STAGE4_FEATURE_SET` |
| Dev pass, held-out fail | `FAIL_HELD_OUT_STOP` |
| Both pass | `PASS_ADVERSARIAL_LITE` (still no auto-promote) |

## Explicit non-goals

- Reopening E22_v3 / E16 micro-variants / E45 promote / G4 shorts this stage  
- Same-panel alpha grids  

Official path remains E22_v2 + core; E45 = B.
