# Stage-3 New Feature Families × Regime Definitions (OOF)

Portfolio fixed to **C4 wrapper**. Selection: 2011–2018 OOF only.

## Decision: `OOF_NO_NEW_FEATURE_REGIME_DUAL_GATE_WINNER`

Baseline TECH2 / BREADTH_BASE / BREADTH_REGIME: IC=0.1147, turn=0.0205, boot=0.8066

### Regime degeneracy vs BREADTH_BASE (OOF day labels)

- `BREADTH_21`: disagree=574/1972
- `BREADTH_STRICT55`: disagree=111/1972
- `TREND_ONLY`: disagree=0/1972 — **identical (not a new regime)**
- `VOL_REGIME`: disagree=664/1972

Excluded dual-gate twins (not counted as new winners):

- `TECH2` / `TREND_ONLY` — regime_identical_to_BREADTH_BASE_on_OOF

| feature | regime | mode | IC | turn | boot | both | CAGR | MDD | risk_on_share |
|---|---|---|---:|---:|---:|---|---:|---:|---:|
| TECH2 | TREND_ONLY | BREADTH_REGIME | 0.1147 | 2.05% | 0.8066 | True | 10.56% | -30.24% | 0.760 |
| TECH2 | BREADTH_BASE | BREADTH_REGIME | 0.1147 | 2.05% | 0.8066 | True | 10.56% | -30.24% | 0.760 |
| VALUE2 | TREND_ONLY | BREADTH_REGIME | 0.0964 | 1.42% | 0.4104 | False | 5.68% | -39.01% | 0.760 |
| VALUE2 | BREADTH_BASE | BREADTH_REGIME | 0.0964 | 1.42% | 0.4104 | False | 5.68% | -39.01% | 0.760 |
| QUALITY2 | VOL_REGIME | BREADTH_REGIME | 0.0584 | 1.79% | 0.2448 | False | 4.76% | -25.55% | 0.423 |
| FAMILY5 | BREADTH_BASE | BREADTH_REGIME | 0.1066 | 1.95% | 0.2440 | False | 4.05% | -38.54% | 0.760 |
| FAMILY5 | TREND_ONLY | BREADTH_REGIME | 0.1066 | 1.95% | 0.2440 | False | 4.05% | -38.54% | 0.760 |
| TECH2 | VOL_REGIME | BREADTH_REGIME | 0.0870 | 1.92% | 0.2232 | False | 4.51% | -30.93% | 0.423 |
| QUALITY2 | BREADTH_BASE | GLOBAL | 0.0662 | 0.65% | 0.1906 | False | 3.97% | -25.47% | 0.760 |
| QUALITY2 | BREADTH_BASE | BREADTH_REGIME | 0.0946 | 0.94% | 0.1714 | False | 3.29% | -25.49% | 0.760 |
| QUALITY2 | TREND_ONLY | BREADTH_REGIME | 0.0946 | 0.94% | 0.1714 | False | 3.29% | -25.49% | 0.760 |
| QUALITY2 | BREADTH_STRICT55 | BREADTH_REGIME | 0.0852 | 1.09% | 0.1706 | False | 3.42% | -25.49% | 0.704 |
| TECH2 | BREADTH_STRICT55 | BREADTH_REGIME | 0.1092 | 2.48% | 0.1662 | False | 3.08% | -36.03% | 0.704 |
| VALUE2 | BREADTH_BASE | GLOBAL | 0.0677 | 0.75% | 0.1594 | False | 3.56% | -22.27% | 0.760 |
| VALUE2 | BREADTH_21 | BREADTH_REGIME | 0.0542 | 1.33% | 0.1554 | False | 2.92% | -40.95% | 0.666 |
| TECH2 | BREADTH_BASE | GLOBAL | 0.0604 | 0.60% | 0.1460 | False | 3.65% | -26.56% | 0.760 |
| VALUE2 | VOL_REGIME | BREADTH_REGIME | 0.0698 | 0.92% | 0.1222 | False | 2.86% | -26.23% | 0.423 |
| VAL_MOM | TREND_ONLY | BREADTH_REGIME | 0.0236 | 1.88% | 0.1088 | False | 0.27% | -46.44% | 0.760 |
| VAL_MOM | BREADTH_BASE | BREADTH_REGIME | 0.0236 | 1.88% | 0.1088 | False | 0.27% | -46.44% | 0.760 |
| QUALITY2 | BREADTH_21 | BREADTH_REGIME | 0.0456 | 1.37% | 0.0870 | False | -0.32% | -44.24% | 0.666 |
| TECH2 | BREADTH_21 | BREADTH_REGIME | 0.0493 | 1.95% | 0.0774 | False | 0.41% | -40.89% | 0.666 |
| VALUE2 | BREADTH_STRICT55 | BREADTH_REGIME | 0.0889 | 1.76% | 0.0544 | False | -0.39% | -39.74% | 0.704 |
| VAL_MOM | BREADTH_STRICT55 | BREADTH_REGIME | 0.0232 | 1.92% | 0.0504 | False | -1.43% | -52.10% | 0.704 |
| FAMILY5 | BREADTH_STRICT55 | BREADTH_REGIME | 0.1018 | 2.14% | 0.0412 | False | 0.38% | -42.87% | 0.704 |
| GROWTH2 | BREADTH_STRICT55 | BREADTH_REGIME | 0.0393 | 2.25% | 0.0322 | False | -1.73% | -44.35% | 0.704 |
| QUAL_VAL | BREADTH_BASE | BREADTH_REGIME | 0.0036 | 1.41% | 0.0286 | False | -0.43% | -38.07% | 0.760 |
| QUAL_VAL | TREND_ONLY | BREADTH_REGIME | 0.0036 | 1.41% | 0.0286 | False | -0.43% | -38.07% | 0.760 |
| QUAL_VAL | BREADTH_STRICT55 | BREADTH_REGIME | 0.0040 | 1.41% | 0.0270 | False | -0.59% | -37.27% | 0.704 |
| QUAL_VAL | VOL_REGIME | BREADTH_REGIME | 0.0145 | 1.49% | 0.0210 | False | -0.47% | -38.63% | 0.423 |
| GROWTH2 | TREND_ONLY | BREADTH_REGIME | 0.0382 | 2.15% | 0.0178 | False | -4.12% | -48.85% | 0.760 |
| GROWTH2 | BREADTH_BASE | BREADTH_REGIME | 0.0382 | 2.15% | 0.0178 | False | -4.12% | -48.85% | 0.760 |
| FAMILY3 | BREADTH_BASE | BREADTH_REGIME | 0.0312 | 2.11% | 0.0102 | False | -5.45% | -45.66% | 0.760 |
| FAMILY3 | TREND_ONLY | BREADTH_REGIME | 0.0312 | 2.11% | 0.0102 | False | -5.45% | -45.66% | 0.760 |
| VAL_MOM | VOL_REGIME | BREADTH_REGIME | 0.0286 | 1.94% | 0.0100 | False | -2.71% | -45.75% | 0.423 |
| FAMILY3 | BREADTH_STRICT55 | BREADTH_REGIME | 0.0318 | 2.13% | 0.0070 | False | -3.77% | -46.23% | 0.704 |
| FAMILY5 | VOL_REGIME | BREADTH_REGIME | 0.0752 | 1.94% | 0.0068 | False | -1.56% | -41.07% | 0.423 |
| VAL_MOM | BREADTH_21 | BREADTH_REGIME | 0.0169 | 1.54% | 0.0062 | False | -3.49% | -47.46% | 0.666 |
| FAMILY5 | BREADTH_BASE | GLOBAL | 0.0587 | 1.10% | 0.0040 | False | -1.30% | -39.31% | 0.760 |
| FAMILY5 | BREADTH_21 | BREADTH_REGIME | 0.0571 | 2.21% | 0.0030 | False | -4.07% | -46.02% | 0.666 |
| QUAL_VAL | BREADTH_21 | BREADTH_REGIME | 0.0102 | 1.40% | 0.0028 | False | -3.13% | -37.89% | 0.666 |
| GROWTH2 | VOL_REGIME | BREADTH_REGIME | 0.0280 | 2.21% | 0.0002 | False | -7.08% | -51.53% | 0.423 |
| GROWTH2 | BREADTH_21 | BREADTH_REGIME | 0.0182 | 1.83% | 0.0002 | False | -7.17% | -50.56% | 0.666 |
| FAMILY3 | VOL_REGIME | BREADTH_REGIME | 0.0253 | 2.34% | 0.0000 | False | -9.32% | -57.90% | 0.423 |
| FAMILY3 | BREADTH_BASE | GLOBAL | 0.0140 | 1.59% | 0.0000 | False | -7.76% | -55.11% | 0.760 |
| FAMILY3 | BREADTH_21 | BREADTH_REGIME | 0.0139 | 1.94% | 0.0000 | False | -8.62% | -57.33% | 0.666 |

No **genuinely new** feature×regime dual-gate winner beyond TECH2/BREADTH_BASE.
VALUE2/QUALITY2/GROWTH2/FAMILY* and non-degenerate regimes all fail OOF bootstrap.
Do **not** held-out TREND_ONLY (OOF-identical to BREADTH_BASE).

Artifact: `reports/stage3_feature_regime_oof_summary.json`
