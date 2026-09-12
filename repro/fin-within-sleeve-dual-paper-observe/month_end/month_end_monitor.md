# FIN within-sleeve month-end monitor (asof 2026-09-11)

**Status:** `OPERATING_OBSERVE` — **paper only**
**Books:** `FIN_EQUAL` ∥ `FIN_RS_SOFT_TILT_EXDIV` ∥ `MIX_L75` ∥ `KD_OPT`

## FIN_RS_SOFT_TILT_EXDIV vs FIN_EQUAL

| Window | MDD dpp | Giveback pp | Rel NAV |
|---|---:|---:|---:|
| mtd | 0.21383855586825096 | 66.60265852901048 | 0.9977 |
| ytd | 2.5939580096013604 | 4.790313540770663 | 0.9818 |
| trailing_1y | 2.5939580096013715 | 5.45836009078573 | 0.9666 |
| sealed_2023_plus | 2.5939580096013826 | 1.4185661519003467 | 0.9611 |
| heldout_2019_plus | 0.8926195082533894 | 0.9929627703258559 | 0.9399 |
| full | 0.8926195082533894 | 0.57888183503918 | 0.9345 |

## MIX_L75 vs FIN_EQUAL

| Window | MDD dpp | Giveback pp | Rel NAV |
|---|---:|---:|---:|
| mtd | 0.042147230145661574 | 24.64581805653694 | 0.9992 |
| ytd | 0.6862354707974583 | 1.546565722485771 | 0.9941 |
| trailing_1y | 0.6862354707974805 | 1.7332710668204632 | 0.9894 |
| sealed_2023_plus | 0.6862354707974805 | 0.4526735198653542 | 0.9875 |
| heldout_2019_plus | 0.22403955244294504 | 0.2735289953181397 | 0.9831 |
| full | 0.22403955244295615 | 0.16154619355499555 | 0.9813 |

## KD_OPT vs FIN_EQUAL

| Window | MDD dpp | Giveback pp | Rel NAV |
|---|---:|---:|---:|
| mtd | 0.09022801008877757 | 10.356351309481049 | 0.9997 |
| ytd | 1.1616332365690263 | 0.6324034883169904 | 0.9976 |
| trailing_1y | 1.1616332365690263 | 1.1222268663954704 | 0.9931 |
| sealed_2023_plus | 1.1616332365690374 | 0.3564446669667598 | 0.9901 |
| heldout_2019_plus | 0.6664522064959488 | 0.25569550589275014 | 0.9842 |
| full | 0.6664522064959599 | 0.0482079646936473 | 0.9944 |

## Alerts

- ALERT: FIN_RS_SOFT_TILT_EXDIV ytd CAGR giveback > 3.0 pp (paper)
- ALERT: FIN_RS_SOFT_TILT_EXDIV trailing_1y CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: FIN_RS_SOFT_TILT_EXDIV trailing_1y giveback > 5 pp — extend observe; Soft-Frozen unchanged; no live wire

## Hard rules

- Soft-Frozen KEEP · live FIN equal-split untouched · no cutover from this monitor

