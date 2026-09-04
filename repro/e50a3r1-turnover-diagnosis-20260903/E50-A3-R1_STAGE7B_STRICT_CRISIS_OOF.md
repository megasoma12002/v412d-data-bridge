# Stage-7B Strict Crisis Challenger OOF

Crisis def: `STRICT_DD15_OR_VOTE3_HYS25`. OOF crisis share=12.1%.

## Decision: `OOF_NO_NEW_STRICT_CRISIS_CHALLENGER_DUAL_GATE_WINNER`

**Correction:** crisis winner must beat BASE_FULL on crisis_compound or crisis_mean_excess, not merely keep excess ≥ 0.

Baseline crisis_ex=0.001065, crisis_ret=47.77%, util=-0.0456

| challenger | CAGR | MDD | util | boot | crisis_ex | crisis_ret | both |
|---|---:|---:|---:|---:|---:|---:|---|
| BASE_FULL | 10.56% | -30.24% | -0.0456 | 0.8066 | 0.001065 | 47.77% | True |
| STRICT_CASH_090 | 10.29% | -28.70% | -0.0406 | 0.7862 | 0.000979 | 45.52% | True |
| STRICT_CASH_085 | 10.12% | -27.89% | -0.0383 | 0.7754 | 0.000912 | 43.79% | True |
| STRICT_CASH_080 | 9.92% | -27.08% | -0.0362 | 0.7550 | 0.000825 | 41.36% | True |
| STRICT_CASH_070 | 9.50% | -25.46% | -0.0323 | 0.7072 | 0.000619 | 35.63% | True |
| STRICT_SLEEVE_DEF_CASH085 | 5.93% | -31.63% | -0.0988 | 0.3608 | -0.000246 | 9.99% | False |
| STRICT_SLEEVE_DEF | 5.89% | -34.51% | -0.1137 | 0.3684 | -0.000244 | 9.31% | False |

Mild crisis cash (0.90→0.70) clears dual gates and improves utility/MDD, but **reduces** crisis-period compound vs BASE_FULL — not a crisis-profit winner.
Defensive sleeve fails bootstrap and worsens crisis excess.

No held-out (no true crisis-profit dual-gate winner).

Artifact: `reports/stage7b_strict_crisis_oof_summary.json`
