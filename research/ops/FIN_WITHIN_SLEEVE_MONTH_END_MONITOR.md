# FIN within-sleeve month-end monitor (asof 2026-09-08)

**Status:** `OPERATING_OBSERVE` — **paper only**
**Books:** `FIN_EQUAL` ∥ `FIN_RS_SOFT_TILT_EXDIV` ∥ `MIX_L75` ∥ `KD_OPT`

## FIN_RS_SOFT_TILT_EXDIV vs FIN_EQUAL

| Window | MDD dpp | Giveback pp | Rel NAV |
|---|---:|---:|---:|
| mtd | 0.0 | 344.75370539951837 | 0.9962 |
| ytd | 2.722142747879508 | 6.269218855309244 | 0.9765 |
| trailing_1y | 2.722142747879508 | 6.677606737125097 | 0.9595 |
| sealed_2023_plus | 2.722142747879519 | 1.6452259928403157 | 0.9550 |
| heldout_2019_plus | 1.1116588036636066 | 1.1630172428419128 | 0.9299 |
| full | 1.1116588036635955 | 0.6653664856857588 | 0.9251 |

## MIX_L75 vs FIN_EQUAL

| Window | MDD dpp | Giveback pp | Rel NAV |
|---|---:|---:|---:|
| mtd | 0.0 | 113.81622209532551 | 0.9988 |
| ytd | 0.7668936128127246 | 2.101515852102742 | 0.9921 |
| trailing_1y | 0.7668936128127246 | 2.262974371683635 | 0.9863 |
| sealed_2023_plus | 0.7668936128127246 | 0.5652499184702009 | 0.9844 |
| heldout_2019_plus | 0.30259323641050884 | 0.35116300722883853 | 0.9784 |
| full | 0.30259323641048663 | 0.19551170948508556 | 0.9774 |

## KD_OPT vs FIN_EQUAL

| Window | MDD dpp | Giveback pp | Rel NAV |
|---|---:|---:|---:|
| mtd | 0.0 | 93.70052399950701 | 0.9990 |
| ytd | 1.1789090714417694 | 1.2988977782536715 | 0.9952 |
| trailing_1y | 1.1789090714417805 | 1.5872881136167472 | 0.9904 |
| sealed_2023_plus | 1.1789090714417805 | 0.46757526403025107 | 0.9871 |
| heldout_2019_plus | 0.8066279142484256 | 0.3186621887207419 | 0.9804 |
| full | 0.8066279142484256 | 0.0383209536001905 | 0.9955 |

## Alerts

- ALERT: FIN_RS_SOFT_TILT_EXDIV ytd CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: FIN_RS_SOFT_TILT_EXDIV ytd giveback > 5 pp — extend observe; Soft-Frozen unchanged; no live wire
- ALERT: FIN_RS_SOFT_TILT_EXDIV trailing_1y CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: FIN_RS_SOFT_TILT_EXDIV trailing_1y giveback > 5 pp — extend observe; Soft-Frozen unchanged; no live wire

## Hard rules

- Soft-Frozen KEEP · live FIN equal-split untouched · no cutover from this monitor

