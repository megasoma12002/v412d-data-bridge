# Stage-6B Mild Risk Overlay OOF

Follow-up to 6A (aggressive overlays cut MDD/utility-loss but fail bootstrap).

## Decision: `OOF_NEW_MILD_OVERLAY_UTILITY_WINNER`

Baseline util=-0.0456 MDD=-0.3024 boot=0.8066

| overlay | CAGR | MDD | utility | turn | boot | gross | both |
|---|---:|---:|---:|---:|---:|---:|---|
| STATIC_085 | 9.74% | -26.21% | -0.0337 | 1.86% | 0.7294 | 0.909 | True |
| REGIME_OFF_085 | 9.73% | -26.21% | -0.0337 | 1.98% | 0.7346 | 0.963 | True |
| STATIC_090 | 10.12% | -27.59% | -0.0368 | 1.95% | 0.7662 | 0.950 | True |
| STATIC_095 | 10.37% | -28.96% | -0.0411 | 2.01% | 0.7884 | 0.981 | True |
| BASE_FULL | 10.56% | -30.24% | -0.0456 | 2.05% | 0.8066 | 0.999 | True |
| VOTE_SEVERE_080 | 10.56% | -30.24% | -0.0456 | 2.05% | 0.8066 | 0.999 | True |
| DD_BRAKE_MILD | 9.49% | -28.70% | -0.0486 | 2.01% | 0.7210 | 0.985 | True |
| VOL_TARGET_20 | 9.91% | -29.71% | -0.0495 | 2.00% | 0.7410 | 0.982 | True |
| VOL_TARGET_18 | 9.38% | -29.53% | -0.0538 | 1.98% | 0.6900 | 0.968 | False |

Recommended: `STATIC_085` — lock R6B1, held-out once.

Artifact: `reports/stage6b_mild_overlay_oof_summary.json`
