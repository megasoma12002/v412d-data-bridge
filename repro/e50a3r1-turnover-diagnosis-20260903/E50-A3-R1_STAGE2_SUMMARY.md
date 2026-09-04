# Stage-2 Research Summary

Draft only. **No retune of C2/C4/C8. No promotion. No E45. PR #19 stays draft.**

## 1. References retained
- **C2** / **C4** / **C8** — only val-turnover-pass cluster; C4 had best val bootstrap (~0.56)

## 2. Validation excess diagnosis (no retune)

Common weak years for **all three** references vs PIT proxy:
- **2021** and especially **2022** (negative excess; 2022 also higher turnover / lower hit rate)

Other notes:
- Crowding is moderate (top10 name gross ~19%; top industry ~18%) — not an extreme single-name blowup story
- For C4/C8, mean excess in deep drawdown (≤-10%) is worse than in mild DD — excess failure is partly regime/DD-linked
- Cost alone does not explain bootstrap failure (C4/C8 already lower turnover than many fails)

Artifact: `E50-A3-R1_STAGE2_VAL_EXCESS_DIAGNOSIS.md`

## 3. Alpha/model OOF screen (C4 portfolio wrapper fixed)

Axes: `TECH2|PRICE8` × `GLOBAL|BREADTH_REGIME` × λ∈{0.1,1,10,100}

**Decision: `OOF_NO_NEW_MODEL_DUAL_GATE_WINNER`**

| Finding | Detail |
|---|---|
| Dual-gate survivors | Only **TECH2 + BREADTH_REGIME** (λ almost inert) |
| GLOBAL | IC≈0.06, bootstrap≈0.13–0.15 — collapse |
| PRICE8 + BREADTH | IC≈0.112 (close to TECH2) but OOF bootstrap **≈0.51–0.53 FAIL** |
| λ-only TECH2/BREADTH twins | Not treated as a new model hypothesis |

Artifact: `E50-A3-R1_STAGE2_MODEL_OOF.md`

## 4. Stage-2 implication / next stage

Portfolio rules **and** the existing TECH2/PRICE8 × regime × λ grid are both saturated under experimental gates.

Next research should be one of:
1. **New feature families** beyond TECH2/PRICE8 (still OOF-selected), or
2. **New regime definition** (not just GLOBAL vs current BREADTH cut), or
3. Deeper **2021–2022 excess failure autopsy** without retuning locks

Do not promote 2.5% / 0.70. Do not merge PR #19 yet.
