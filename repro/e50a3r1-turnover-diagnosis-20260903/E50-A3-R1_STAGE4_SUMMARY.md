# Stage-4 Research Summary

Draft only. **No retune of C2/C4/C8/F1. No promotion. No E45. PR #19 stays draft.**

## 1. Bad-month attribution (diagnosis only)

Shared 13 negative-excess months (C2/C4/C8). Held-out deltas are **navigation only**.

| Signal | Pattern |
|---|---|
| Relatively resilient | defensive / vol / drawdown / book-to-price |
| Fragile | monthly revenue YoY, ROE |
| C4 buys in bad months | high vol/defensive tilt; low momentum tilt |

Artifact: `E50-A3-R1_STAGE4_BAD_MONTH_ATTRIBUTION.md`

## 2. Atomic feature OOF screen (C4 wrapper fixed)

**Decision: `OOF_NEW_ATOMIC_FEATURE_DUAL_GATE_WINNER`**

| Cell | IC | turn | boot | both |
|---|---:|---:|---:|---|
| TECH2 (baseline) | 0.1147 | 2.05% | 0.8066 | True |
| **TECH2_VALUE (F1)** | 0.1134 | 1.92% | **0.7078** | **True** |
| DEF3 | 0.1084 | 1.87% | 0.6840 | False (near miss) |
| TECH2_QUAL / TECH2_REV | ~0.11 | ~2% | ~0.50–0.54 | False |
| Pure VALUE/REV/QUAL/MOM mixes | low | — | ≪0.05 | False |

F1 features: momentum + defensive family + `pct_book_to_price_proxy` + `pct_earnings_yield_proxy`

Artifact: `E50-A3-R1_STAGE4_ATOMIC_FEATURE_OOF.md`

## 3. F1 held-out (one shot, no retune)

**Decision: `MIXED_HELDOUT`**

| | F1 Val | F1 Sealed | C4 TECH2 Val | C4 TECH2 Sealed |
|---|---:|---:|---:|---:|
| Bootstrap | **0.3904 FAIL** | 0.9984 PASS | 0.5588 FAIL | 0.9984 PASS |
| Turnover | 2.23% PASS | 1.04% PASS | (ref) | (ref) |

F1 does **not** fix the shared validation bootstrap failure; val boot is worse than C4 TECH2. Sealed remains strong. **Do not retune F1 after this look.**

Artifact: `E50-A3-R1_STAGE4_F1_HELDOUT.md`

## 4. Stage-4 implication

Saturated under experimental gates:

1. Portfolio rules (C2/C4/C8) → MIXED_HELDOUT  
2. TECH2/PRICE8 × regime × λ → no new OOF winner  
3. Family-score × regime cuts → no new OOF winner  
4. Atomic/hybrid OOF → F1 TECH2_VALUE → **MIXED_HELDOUT**, val worse than C4  

Next leverage (if any) needs a **new OOF-selected hypothesis** that is not a small TECH2 tilt — e.g. different label/horizon, interaction/orthogonalization with explicit OOF degeneracy checks, or a structural regime that is non-degenerate **and** dual-gate. Do not promote 2.5%/0.70. Do not merge #19.
