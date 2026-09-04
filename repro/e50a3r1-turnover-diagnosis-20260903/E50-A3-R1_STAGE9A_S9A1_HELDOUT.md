# E50-A3-R1-S9A1 FREEZE_REB × COMBO_VOL70_VAL03 — Held-Out (E45-C1)

Locked OOF: skip rebalance while rolling-vol p70 & val IC≥0.03 & non-crisis. **No retune. Not an in-place E45 edit.**

## Research decision

**`MIXED_HELDOUT`**

OOF: util=-0.0468, boot=0.7846, mdd=-0.3024

| Metric | S9A1 Val | S9A1 Sealed | C4 Full Val | C4 Full Sealed |
|---|---:|---:|---:|---:|
| CAGR | 23.45% | 59.00% | 21.65% | 47.68% |
| MDD | -29.79% | -25.01% | -31.87% | -20.99% |
| Utility | 0.0855 | 0.4650 | 0.0572 | 0.3718 |
| Turnover | 2.38% | 1.38% | 2.19% | 1.19% |
| Bootstrap | 0.6232 | 1.0000 | 0.5588 | 0.9984 |
| Stress flag share | 9.9% | 18.6% | — | — |
| Stress mean excess | 0.0007770435301989302 | 0.001094896017991568 | 0.0003472895953742069 | 0.001556890645892672 |
| Stress compound | -0.0014831151933610842 | 0.1767500646020419 | -0.04291230416507075 | 0.27670050189279793 |
| Turn gate | True | True | True | True |
| Boot gate | False | True | False | True |
| Exact T+1 | True | True | True | True |

Artifact: `reports/stage9a_s9a1_heldout_decision.json`
