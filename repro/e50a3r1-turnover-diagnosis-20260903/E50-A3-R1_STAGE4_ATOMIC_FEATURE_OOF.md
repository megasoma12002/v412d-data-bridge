# Stage-4A Atomic Feature Families (OOF)

Portfolio fixed to **C4 wrapper**. Regime/mode: baseline BREADTH + `BREADTH_REGIME`, λ=1.0.
Selection: 2011–2018 OOF only. No family-score recombinations / no PRICE8 redo.

## Decision: `OOF_NEW_ATOMIC_FEATURE_DUAL_GATE_WINNER`

Baseline TECH2: IC=0.1147, turn=0.0205, boot=0.8066

| feature_set | mode | n | IC | turn | boot | both | CAGR | MDD |
|---|---|---:|---:|---:|---:|---|---:|---:|
| TECH2 | BREADTH_REGIME | 2 | 0.1147 | 2.05% | 0.8066 | True | 10.56% | -30.24% |
| TECH2_VALUE | BREADTH_REGIME | 4 | 0.1134 | 1.92% | 0.7078 | True | 9.42% | -30.24% |
| DEF3 | BREADTH_REGIME | 3 | 0.1084 | 1.87% | 0.6840 | False | 9.23% | -28.50% |
| TECH2_QUAL | BREADTH_REGIME | 4 | 0.1048 | 1.89% | 0.5368 | False | 7.47% | -30.24% |
| TECH2_REV | BREADTH_REGIME | 4 | 0.1139 | 2.25% | 0.5044 | False | 6.80% | -30.78% |
| TECH2_GLOBAL | GLOBAL | 2 | 0.0604 | 0.60% | 0.1460 | False | 3.65% | -26.56% |
| QUAL4 | BREADTH_REGIME | 4 | 0.0356 | 1.17% | 0.0304 | False | -0.76% | -35.14% |
| MOM_REV | BREADTH_REGIME | 4 | 0.0488 | 2.40% | 0.0134 | False | -4.18% | -43.01% |
| QUAL_VALUE | BREADTH_REGIME | 4 | 0.0507 | 1.30% | 0.0110 | False | -2.44% | -35.14% |
| REV3 | BREADTH_REGIME | 3 | 0.0316 | 2.32% | 0.0088 | False | -4.69% | -43.09% |
| VALUE3 | BREADTH_REGIME | 3 | 0.0580 | 1.36% | 0.0076 | False | -1.91% | -38.43% |
| REV_QUAL | BREADTH_REGIME | 4 | 0.0278 | 2.21% | 0.0022 | False | -5.21% | -45.29% |
| GROW3 | BREADTH_REGIME | 3 | 0.0159 | 1.81% | 0.0020 | False | -3.71% | -50.48% |
| MOM_VALUE | BREADTH_REGIME | 4 | 0.0321 | 1.80% | 0.0018 | False | -7.30% | -61.05% |
| MOM3 | BREADTH_REGIME | 3 | 0.0191 | 2.44% | 0.0016 | False | -8.58% | -56.38% |
| MOM_QUAL | BREADTH_REGIME | 4 | 0.0048 | 1.78% | 0.0012 | False | -9.42% | -60.59% |

## Recommended (OOF only — not yet held-out)

- `TECH2_VALUE` features=`momentum_family_score,defensive_family_score,pct_book_to_price_proxy,pct_earnings_yield_proxy`
- boot `0.7078`, turn `0.0192`, IC `0.1134`

Next: lock as F1 and run held-out once.

Artifact: `reports/stage4_atomic_feature_oof_summary.json`
