# Stage-5 Horizon + Structure OOF

Portfolio fixed to **C4 wrapper**. Selection: 2011–2018 OOF only.
Hypotheses: train horizon 63d; defensive/vol structure; mom orthogonalization; mom×inv-vol.
Does **not** redo TECH2_VALUE / family×regime / PRICE8.

## Decision: `OOF_NO_NEW_HORIZON_STRUCTURE_DUAL_GATE_WINNER`

Baseline TECH2_H21: IC=0.1147, turn=0.0205, boot=0.8066

| cell | h | IC | turn | boot | both | CAGR | MDD |
|---|---:|---:|---:|---:|---|---:|---:|
| TECH2_H21 | 21 | 0.1147 | 2.05% | 0.8066 | True | 10.56% | -30.24% |
| MOM_ORTH_DEF_H21 | 21 | 0.1253 | 2.08% | 0.6596 | False | 9.03% | -30.31% |
| DEF_ONLY_H21 | 21 | 0.1136 | 1.87% | 0.5914 | False | 8.60% | -27.91% |
| DEF4_H21 | 21 | 0.1105 | 1.68% | 0.5754 | False | 8.59% | -28.80% |
| ORTH_DEF_VAL_H63 | 63 | 0.1521 | 1.66% | 0.5316 | False | 8.12% | -28.53% |
| DEF_VALUE_H63 | 63 | 0.1459 | 1.69% | 0.5248 | False | 7.64% | -28.53% |
| TECH2_DEF_H21 | 21 | 0.1258 | 1.87% | 0.5002 | False | 7.20% | -27.25% |
| ORTH_DEF_VAL_H21 | 21 | 0.1119 | 1.63% | 0.3378 | False | 6.09% | -27.02% |
| DEF_VALUE_H21 | 21 | 0.1113 | 1.65% | 0.3292 | False | 5.87% | -27.02% |
| TECH2_H63 | 63 | 0.1440 | 1.74% | 0.2858 | False | 3.98% | -42.68% |
| TECH2_DEF_H63 | 63 | 0.1592 | 1.80% | 0.2398 | False | 4.38% | -30.72% |
| TECH2_INTER_H21 | 21 | 0.1100 | 1.70% | 0.2288 | False | 3.64% | -43.17% |
| TECH2_INTER_H63 | 63 | 0.1425 | 1.73% | 0.1738 | False | 3.13% | -33.26% |
| MOM_ORTH_VAL_H63 | 63 | 0.1433 | 1.18% | 0.1680 | False | 2.73% | -39.01% |
| MOM_ORTH_VAL_H21 | 21 | 0.1037 | 1.17% | 0.1616 | False | 2.67% | -39.01% |

No new horizon/structure dual-gate winner beyond TECH2_H21.

Artifact: `reports/stage5_horizon_structure_oof_summary.json`
