# Stage-8C Plan — Multi-Sleeve / E45-Class Challenger

Date: 2026-09-04  
Status: executing OOF screen  
Constraint: **not an in-place E45 edit**; no retune of C2/C4/C8/F1/R6B1/S8B1.

## Why

S8B1 (`CASH_070` × absolute OOF p80 vol) won OOF then `MIXED_HELDOUT`:
flag share 12% → 57–70%, stress PnL worse than C4 on validation.

Cash on the bull sleeve cannot deliver 壞月也賺. Need a **separate stress return engine**.

## Design

| Piece | Spec |
|---|---|
| Bull | Frozen TECH2 + C4 |
| Stress sleeves | DEF / VAL / QUAL (C4 wrapper) |
| Detectors | Rolling 252d vol percentile, value-IC, combos, crisis∪vol — **no absolute p80 lock** |
| Controllers | Hard sleeve switch ± mild CASH_085 on stress days |
| Pass | Dual gates + stress PnL > BASE + util ≥ BASE−0.005 |
| Share band | Stress days ∈ [5%, 40%] else skip detector |
| Held-out | One shot only if OOF winner; no retune |

## Artifacts

- `scripts/e50a3r1_stage8c_multisleeve_oof.py`
- `E50-A3-R1_STAGE8C_MULTISLEEVE_OOF.md`
- later `E50-A3-R1_STAGE8C_S8C1_HELDOUT.md` if locked
