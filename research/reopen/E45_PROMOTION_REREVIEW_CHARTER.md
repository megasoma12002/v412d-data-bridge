# E45 Promotion Re-review Charter

Status: **OPEN** (authorized 2026-09-04)  
Prior decision: **B_KEEP_D_AS_BASELINE_E45_API_ONLY** (PIT + original v412e0)  
Formal baseline: **V4.12-D**

## What re-review means

Authorization to **re-open the governance tradeoff**, not to retune E3 locks.

E45-C1 already showed:

- E3 **improves MDD** vs D (MC P≈0.99)
- E3 **fails** Validation return ≥80% of D and Sharpe ≥ D

Re-review options:

| Option | Meaning |
|---|---|
| **B stays** | Default unless new evidence or explicit promote approval |
| **A with accepted tradeoff** | Promote E3-locked profile as `E45_v1` **knowing** return/Sharpe drop |
| **A'** | New exposure schedule challenger (≤1 EXPERIMENTAL schedule) under higher E45 bar |

## Method

1. Publish return–MDD tradeoff table from original v412e0 C1 curves  
2. Optional: one new schedule marked EXPERIMENTAL in `repro/e45-c2-<date>/`  
3. Promotion still requires SOFT_FROZEN_CRITICAL path + human phrase  

## Stop rules

- No retune of locked E3 winner hyperparameters after looking at Blind/Final  
- No claiming −13.16% until an artifact matches  
- Do not edit D or E45 in place  

## Round-1 deliverable

Tradeoff summary JSON/MD from `repro/e45-c1-v412e0-original-20260904/`.
