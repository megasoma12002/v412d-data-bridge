# FIN within-sleeve month-end monitor (asof 2026-09-07)

**Status:** `OPERATING_OBSERVE` — **paper only**
**Books:** `FIN_EQUAL` ∥ `FIN_RS_SOFT_TILT_EXDIV` ∥ `MIX_L75`

## FIN_RS_SOFT_TILT_EXDIV vs FIN_EQUAL

| Window | MDD dpp | Giveback pp | Rel NAV |
|---|---:|---:|---:|
| mtd | 0.0 | 262.1422180293253 | 0.9973 |
| ytd | 2.722142747879508 | 5.90309330489307 | 0.9776 |
| trailing_1y | 2.722142747879508 | 6.441682777635793 | 0.9606 |
| sealed_2023_plus | 2.722142747879519 | 1.6011368119133618 | 0.9561 |
| heldout_2019_plus | 1.1116588036636066 | 1.1436922478520017 | 0.9310 |
| full | 1.1116588036635955 | 0.655357065105755 | 0.9261 |

## MIX_L75 vs FIN_EQUAL

| Window | MDD dpp | Giveback pp | Rel NAV |
|---|---:|---:|---:|
| mtd | 0.0 | 92.60459803339583 | 0.9991 |
| ytd | 0.7668936128127246 | 2.0017826748320866 | 0.9924 |
| trailing_1y | 0.7668936128127246 | 2.197617123929163 | 0.9866 |
| sealed_2023_plus | 0.7668936128127246 | 0.5537598650254161 | 0.9847 |
| heldout_2019_plus | 0.30259323641050884 | 0.34623771993473884 | 0.9787 |
| full | 0.30259323641048663 | 0.19298642869620686 | 0.9777 |

## Alerts

- ALERT: FIN_RS_SOFT_TILT_EXDIV ytd CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: FIN_RS_SOFT_TILT_EXDIV ytd giveback > 5 pp — extend observe; Soft-Frozen unchanged; no live wire
- ALERT: FIN_RS_SOFT_TILT_EXDIV trailing_1y CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: FIN_RS_SOFT_TILT_EXDIV trailing_1y giveback > 5 pp — extend observe; Soft-Frozen unchanged; no live wire

## Hard rules

- Soft-Frozen KEEP · live FIN equal-split untouched · no cutover from this monitor

