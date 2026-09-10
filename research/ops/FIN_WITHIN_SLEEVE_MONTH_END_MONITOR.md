# FIN within-sleeve month-end monitor (asof 2026-09-09)

**Status:** `OPERATING_OBSERVE` — **paper only**
**Books:** `FIN_EQUAL` ∥ `FIN_RS_SOFT_TILT_EXDIV` ∥ `MIX_L75` ∥ `KD_OPT`

## FIN_RS_SOFT_TILT_EXDIV vs FIN_EQUAL

| Window | MDD dpp | Giveback pp | Rel NAV |
|---|---:|---:|---:|
| mtd | 0.21383855586825096 | 41.597260569513764 | 0.9985 |
| ytd | 2.5939580096013604 | 4.499767125683873 | 0.9825 |
| trailing_1y | 2.5939580096013826 | 5.310030921156161 | 0.9668 |
| sealed_2023_plus | 2.5939580096013826 | 1.385814366849769 | 0.9618 |
| heldout_2019_plus | 0.8926195082533894 | 0.9789885162456935 | 0.9405 |
| full | 0.8926195082533894 | 0.5718910187622939 | 0.9352 |

## MIX_L75 vs FIN_EQUAL

| Window | MDD dpp | Giveback pp | Rel NAV |
|---|---:|---:|---:|
| mtd | 0.042147230145661574 | 19.474878659640904 | 0.9993 |
| ytd | 0.6862354707974583 | 1.48313139003311 | 0.9943 |
| trailing_1y | 0.6862354707974694 | 1.7069572465702176 | 0.9893 |
| sealed_2023_plus | 0.6862354707974805 | 0.4464184145289485 | 0.9876 |
| heldout_2019_plus | 0.22403955244294504 | 0.27106226954756174 | 0.9832 |
| full | 0.22403955244295615 | 0.16035989788723004 | 0.9814 |

## KD_OPT vs FIN_EQUAL

| Window | MDD dpp | Giveback pp | Rel NAV |
|---|---:|---:|---:|
| mtd | 0.09022801008877757 | 3.5018465649256036 | 0.9999 |
| ytd | 1.1616332365690263 | 0.5627199775966707 | 0.9978 |
| trailing_1y | 1.1616332365690152 | 1.0859693698443307 | 0.9932 |
| sealed_2023_plus | 1.1616332365690374 | 0.34700163204750556 | 0.9903 |
| heldout_2019_plus | 0.6664522064959488 | 0.2516306978320504 | 0.9844 |
| full | 0.6664522064959599 | 0.046296421849323366 | 0.9946 |

## Alerts

- ALERT: FIN_RS_SOFT_TILT_EXDIV ytd CAGR giveback > 3.0 pp (paper)
- ALERT: FIN_RS_SOFT_TILT_EXDIV trailing_1y CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: FIN_RS_SOFT_TILT_EXDIV trailing_1y giveback > 5 pp — extend observe; Soft-Frozen unchanged; no live wire

## Hard rules

- Soft-Frozen KEEP · live FIN equal-split untouched · no cutover from this monitor

