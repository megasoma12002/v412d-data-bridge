# Stage-4 Research Summary

Draft only. **No retune of C2/C4/C8. No promotion. No E45. PR #19 stays draft.**

## 1. Bad-month attribution (diagnosis only)

Shared 13 negative-excess months (C2/C4/C8). Held-out deltas are **navigation only**.

| Signal | Pattern |
|---|---|
| Relatively resilient | defensive / vol / drawdown / book-to-price |
| Fragile | monthly revenue YoY, ROE |
| C4 buys in bad months | high vol/defensive tilt; low momentum tilt |

Artifact: `E50-A3-R1_STAGE4_BAD_MONTH_ATTRIBUTION.md`

## 2. Atomic feature OOF screen (C4 wrapper fixed)

Axes: MOM3/DEF3/QUAL4/VALUE3/REV3/GROW3 + mixes + TECH2_* hybrids. Mode/λ fixed to BREADTH_REGIME / 1.0.

**Decision: `OOF_NEW_ATOMIC_FEATURE_DUAL_GATE_WINNER`**

| Cell | IC | turn | boot | both |
|---|---:|---:|---:|---|
| TECH2 (baseline) | 0.1147 | 2.05% | 0.8066 | True |
| **TECH2_VALUE (F1)** | 0.1134 | 1.92% | **0.7078** | **True** |
| DEF3 | 0.1084 | 1.87% | 0.6840 | False |
| TECH2_QUAL / TECH2_REV | ~0.11 | ~2% | ~0.50–0.54 | False |
| Pure VALUE/REV/QUAL/MOM mixes | low | — | ≪0.05 | False |

F1 features: `momentum_family_score, defensive_family_score, pct_book_to_price_proxy, pct_earnings_yield_proxy`

Note: F1 clears dual gates but OOF bootstrap is **below** TECH2 baseline (0.71 vs 0.81). Held-out is one-shot; no retune.

Artifact: `E50-A3-R1_STAGE4_ATOMIC_FEATURE_OOF.md`

## 3. F1 held-out (pending / see F1 report)

Lock F1 → evaluate 2019–2022 + 2023–latest once → label PASS/FAIL/MIXED/INCONCLUSIVE.

Do not promote 2.5% / 0.70. Do not merge PR #19 yet.
