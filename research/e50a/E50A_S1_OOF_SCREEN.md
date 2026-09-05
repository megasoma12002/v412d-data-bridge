# E50-A3-S1 Track B — OOF Screen

Generated: `2026-09-04T19:33:44.327832+00:00`

**EXPERIMENTAL.** No live wire. No held-out in this step.

## Decision: `OOF_S1_DUAL_GATE_STRESS_WINNER_READY_FOR_ADV_LITE`

Rows=24 candidates=2

| family | detector | shell | util | boot | TO | stress_ex | both |
|---|---|---|---:|---:|---:|---:|---|
| S1-QRES | COMBO_VOL80_VAL00 | k22/r42/e2.25 | -0.0493 | 0.7880 | 0.0249 | 0.0001471156962107832 | True |
| S1-DEFRES | COMBO_VOL70_VAL03 | k22/r42/e2.25 | -0.0411 | 0.8290 | 0.0214 | 0.00012737792771346307 | True |
| S1-DEFRES | COMBO_VOL70_VAL00 | k22/r42/e2.25 | -0.0499 | 0.7656 | 0.0222 | 0.00011493519874377107 | True |
| S1-DEFRES | COMBO_VOL80_VAL00 | k22/r42/e2.25 | -0.0497 | 0.7662 | 0.0215 | -1.4879851983458923e-06 | True |
| S1-DEFRES | COMBO_VOL80_VAL03 | k22/r42/e2.25 | -0.0408 | 0.8278 | 0.0208 | -3.3461815483230866e-05 | True |
| S1-QRES | COMBO_VOL80_VAL03 | k22/r42/e2.25 | -0.0576 | 0.7216 | 0.0233 | -5.9831560695138305e-05 | True |
| S1-QRES | COMBO_VOL70_VAL00 | k22/r42/e2.25 | -0.0544 | 0.7538 | 0.0259 | 0.00019217387300816656 | False |
| S1-QRES | COMBO_VOL70_VAL03 | k22/r42/e2.25 | -0.0627 | 0.6858 | 0.0243 | 4.959273779406604e-05 | False |
| S1-VALRES | COMBO_VOL80_VAL00 | k22/r42/e2.25 | -0.2272 | 0.0308 | 0.0682 | -0.00017566983290389344 | False |
| S1-DEFRES | VOL70 | k22/r42/e2.25 | -0.0398 | 0.6828 | 0.0235 | -0.00019330450427055589 | False |
| S1-VALRES | COMBO_VOL70_VAL00 | k22/r42/e2.25 | -0.2272 | 0.0308 | 0.0682 | -0.00019961558193875762 | False |
| S1-VALRES | COMBO_VOL80_VAL03 | k22/r42/e2.25 | -0.2272 | 0.0308 | 0.0682 | -0.0002709120150303639 | False |
| S1-VALRES | COMBO_VOL70_VAL03 | k22/r42/e2.25 | -0.2272 | 0.0308 | 0.0682 | -0.0002754326674943779 | False |
| S1-DEFRES | VOL80 | k22/r42/e2.25 | -0.0389 | 0.6854 | 0.0228 | -0.000291860516137674 | False |
| S1-QRES | VOL80 | k22/r42/e2.25 | -0.1032 | 0.4422 | 0.0269 | -0.00032132224894343664 | False |
| S1-QRES | VOL70 | k22/r42/e2.25 | -0.1134 | 0.3496 | 0.0282 | -0.0003378322531375121 | False |
| S1-VALRES | VOL80 | k22/r42/e2.25 | -0.2272 | 0.0308 | 0.0682 | -0.0003691858491548926 | False |
| S1-VALRES | VOL70 | k22/r42/e2.25 | -0.2272 | 0.0308 | 0.0682 | -0.0005558585641848732 | False |

## Recommended (OOF only — not held-out)

- family `S1-QRES` detector `COMBO_VOL80_VAL00`
- shell top_k=22 reb=42 exit=2.25
- util=-0.0493 boot=0.788 stress_ex=0.0001471156962107832

Next: adversarial-lite → one held-out. Only `PASS_HELDOUT` replaces Track A.

Artifacts:
- `repro/e50a-dual-track/track_b_s1_oof/reports/s1_oof_summary.json`
- `repro/e50a-dual-track/track_b_s1_oof/outputs/s1_oof_grid.csv`
