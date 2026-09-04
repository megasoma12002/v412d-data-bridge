# Stage-10 Five-Round Stress Alpha — Final Summary

Date: 2026-09-04  
Detector locked: S9A1 `COMBO_VOL70_VAL03` (no retune)  
Bull sleeve: TECH2+C4  
**Not an in-place E45 edit. Gates remain EXPERIMENTAL.**

## Round log

| Round | Action | Result |
|---|---|---|
| **R1** | OOF atomic/hybrid stress sleeves | Winner **S10R1** = `SLEEVE` / `QUAL_VALUE` |
| **R2** | Held-out S10R1 | **`MIXED_HELDOUT`** val_boot=0.485; stress_ex 0.00047 > C4 0.00035 |
| **R3** | OOF residual / short-rev expansion | Winner **S10R3** = `RESID_SLEEVE` / `SAFE4` |
| **R4** | Held-out S10R3 | **`MIXED_HELDOUT`** val_boot=0.587; stress_ex **0.00082** > C4 |
| **R5** | OOF re-screen → same theme; held-out S10R5 | **`MIXED_HELDOUT`** (same as S10R3) |

No `PASS_HELDOUT` under the 0.70 bootstrap gate.

## Best directional lock: S10R3 / S10R5

`RESID_SLEEVE` × `SAFE4` = residualized (`pct_cash_to_assets`, `pct_current_ratio`, `pct_leverage`, `pct_drawdown_63d`) vs TECH2 score, switched on S9A1 stress days.

| Metric | S10R3 Val | C4 Val | S9A1 Val (freeze) |
|---|---:|---:|---:|
| CAGR | ~similar band | 21.7% | 23.5% |
| Bootstrap | **0.587** | 0.559 | 0.623 |
| Stress mean excess | **0.00082** | 0.00035 | 0.00078 |
| Boot gate (0.70) | Fail | Fail | Fail |

Stress transfer remains the consistent win; dual-gate PASS does not.

## Saturation call

Across Stages 8–10, every OOF dual-gate stress winner that was held-out once returned **`MIXED_HELDOUT`**. Further TECH2-adjacent feature remixes / sleeve controllers are not expected to clear 0.70 on 2019–2022 without either:

1. A **genuinely new** information set (not panel family/`pct_*` recombinations), or  
2. A **governance** decision that MIXED + better-than-C4 stress/boot is actionable

## Stop

- Do not retune S10R* / S9A1 / prior locks after held-out  
- Do not promote 2.5%/0.70 gates in this PR  
- Do not edit E45 in place  
- Stop automatic A3-R1 controller / stress-sleeve grids on this feature panel

Artifacts: `E50-A3-R1_STAGE10_R*.md`, `E50-A3-R1_STAGE10_S10R*_HELDOUT.md`, `reports/stage10_*`.
