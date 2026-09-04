# E50-A3-R1-S8B1 CASH_070 × HIGH_VOL_NONCRISIS — Held-Out Evaluation

Locked OOF: scale to **0.70** when `not crisis_vote2` and `mkt_vol_60d >= OOF p80`. **No retune. E45 untouched.**

## Research decision

**`MIXED_HELDOUT`**

OOF: util=-0.0263, MDD=-0.2616, boot=0.7958, stress_ex=0.0005614611079759957

| Metric | S8B1 Val | S8B1 Sealed | C4 Full Val | C4 Full Sealed |
|---|---:|---:|---:|---:|
| CAGR | 18.04% | 38.70% | 21.65% | 47.68% |
| MDD | -26.29% | -14.99% | -31.87% | -20.99% |
| Utility | 0.0490 | 0.3120 | 0.0572 | 0.3718 |
| Turnover | 1.87% | 1.11% | 2.19% | 1.19% |
| Bootstrap | 0.3480 | 0.9908 | 0.5588 | 0.9984 |
| Gross exp | 0.832 | 0.806 | 0.999 | 0.999 |
| Stress flag share | 57.3% | 70.2% | — | — |
| Stress mean excess | -0.0003523287434980224 | 0.0008329910150263528 | -0.00021797233405200847 | 0.001086628088943834 |
| Stress compound | 0.25728867231573194 | 0.8112313446460202 | 0.32272911060415455 | 1.0542951223558124 |
| Turn gate | True | True | True | True |
| Boot gate | False | True | False | True |
| Exact T+1 | True | True | True | True |

Artifact: `reports/stage8b_s8b1_heldout_decision.json`
