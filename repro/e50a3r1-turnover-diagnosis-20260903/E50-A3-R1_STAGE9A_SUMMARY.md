# Stage-9A Summary — E45-C1 Freeze / Orth-Def

Date: 2026-09-04  
Track: **E45-C1** (not in-place E45 edit)  
Branch: `cursor/e50a3r1-turnover-diagnosis-d049` (draft PR #19)

## OOF

**`OOF_NEW_E45C1_CONTROLLER_DUAL_GATE_WINNER`** (6 candidates)

| Lock | Spec |
|---|---|
| **S9A1** | `FREEZE_REB` × `COMBO_VOL70_VAL03` |
| Detector | non-crisis ∧ rolling-252d vol ≥ p70 ∧ val_ic_lag21 ≥ 0.03 |
| Controller | skip C4 rebalance while flag on (hold names) |
| OOF share | ~11.7% |

ORTH_DEF improved MDD on broad vol detectors but often failed bootstrap; freeze was the dual-gate stress winner.

## Held-out — S9A1 one shot

**`MIXED_HELDOUT`** (sealed pass; val boot 0.623 < 0.70)

| Metric | S9A1 Val | C4 Val | Note |
|---|---:|---:|---|
| CAGR | 23.5% | 21.7% | S9A1 higher |
| MDD | −29.8% | −31.9% | S9A1 better |
| Bootstrap | **0.623** | 0.559 | S9A1 better than C4 but **gate fail** |
| Stress flag share | **9.9%** | — | travels (~OOF 12%) |
| Stress mean excess | **+0.00078** | +0.00035 | **first stress transfer win vs C4** |
| Sealed boot | 1.000 | 0.998 | both pass |

### Why this matters

Unlike S8B1 (over-fire) and S8C1 (under-fire + worse stress), **S9A1’s rolling detector share travels** and **validation stress excess beats C4**.  
It still fails the EXPERIMENTAL 0.70 bootstrap gate on 2019–2022 → cannot lock as PASS under current R1 gates. **No retune.**

## Stop rule

Stage-9A charter: if controller class saturates without PASS_HELDOUT, **stop A3-R1 controller grids**.

Saturated classes now include: cash, DEF/VAL/QUAL sleeves, freeze-rebalance, orth-def residuals.

## Research conclusion (Stages 1–9A)

| Object | Status |
|---|---|
| TECH2+C4 bull sleeve | Best single risk-on engine; keep as reference |
| Bad months | Non-EW-crisis alpha failure (Stage-8A) |
| Controllers on family scores | OOF wins → almost always `MIXED_HELDOUT` |
| S9A1 | Best *directional* stress transfer; still MIXED under 0.70 gate |
| E45 in-place | Untouched |
| Gate promotion | Not done |

## What NOT to do next on this PR

1. Retune S9A1 detector cuts after held-out  
2. More cash/sleeve/freeze grids on TECH2 families  
3. Promote 2.5% / 0.70 to frozen  
4. Edit E45 in place  
5. Merge as production strategy

## Legitimate next tracks (outside this grid)

1. **New stress alpha engine** (features / labels not in TECH2 family remix) under E45-C1 bar  
2. **Governance**: decide whether MIXED + better-than-C4 stress/boot is actionable, or keep 0.70 hard  
3. Optional EXPERIMENTAL fast-execution as its own hypothesis — only after stress alpha exists  

Artifacts: `E45-C1_CHARTER.md`, `E50-A3-R1_STAGE9A_E45C1_FREEZE_ORTH_OOF.md`, `E50-A3-R1_STAGE9A_S9A1_HELDOUT.md`, `reports/stage9a_*`.
