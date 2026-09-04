# Stage-6 Risk Overlay OOF (Profit ↑ / MDD ↓)

Alpha frozen: **TECH2 scores + C4 name selection**. Sleeve exposure overlays only.
Selection: 2011–2018 OOF. **E45 not touched.** Gates EXPERIMENTAL.

## Decision: `OOF_NO_NEW_RISK_OVERLAY_DUAL_GATE_WINNER`

Baseline BASE_FULL: CAGR=0.1056, MDD=-0.3024, util=-0.0456, turn=0.0205, boot=0.8066

| overlay | CAGR | MDD | utility | turn | boot | gross | both |
|---|---:|---:|---:|---:|---:|---:|---|
| BASE_FULL | 10.56% | -30.24% | -0.0456 | 2.05% | 0.8066 | 0.999 | True |
| REGIME_OFF_050 | 7.33% | -16.41% | -0.0087 | 1.74% | 0.4264 | 0.822 | False |
| STATIC_050 | 5.87% | -16.02% | -0.0214 | 1.10% | 0.2576 | 0.541 | False |
| VOL15_x_DD | 7.28% | -20.17% | -0.0281 | 1.80% | 0.4356 | 0.897 | False |
| STATIC_070 | 8.11% | -21.94% | -0.0287 | 1.54% | 0.5248 | 0.754 | False |
| DD_BRAKE | 7.07% | -20.55% | -0.0321 | 1.80% | 0.4192 | 0.914 | False |
| VOL_TARGET_15 | 8.69% | -26.62% | -0.0461 | 1.92% | 0.6058 | 0.939 | False |
| VOTE_CRISIS | 8.76% | -29.05% | -0.0576 | 1.97% | 0.6324 | 0.962 | False |

No dual-gate overlay that improves utility (or qualifies) vs BASE_FULL.
Do not held-out near-misses. Do not retune alpha.


## Research note

Raising CAGR while cutting MDD on a fully invested sleeve usually needs **risk budget** (cash/exposure), not another TECH2 tilt. This stage tests that class under OOF dual gates.

Artifact: `reports/stage6_risk_overlay_oof_summary.json`
