# FIN within-sleeve month-end monitor (asof 2026-09-08)

**Status:** `OPERATING_OBSERVE` — **paper only**
**Books:** `FIN_EQUAL` ∥ `FIN_RS_SOFT_TILT_EXDIV` ∥ `MIX_L75` ∥ `KD_OPT`

## FIN_RS_SOFT_TILT_EXDIV vs FIN_EQUAL

| Window | MDD dpp | Giveback pp | Rel NAV |
|---|---:|---:|---:|
| mtd | 0.0 | 329.35780506908475 | 0.9963 |
| ytd | 2.5939580096013604 | 5.198778163169027 | 0.9804 |
| trailing_1y | 2.5939580096013826 | 5.639826029235673 | 0.9656 |
| sealed_2023_plus | 2.5939580096013826 | 1.470104844284159 | 0.9597 |
| heldout_2019_plus | 0.8926195082533894 | 1.0159269894833844 | 0.9385 |
| full | 0.8926195082533894 | 0.5911262675240447 | 0.9332 |

## MIX_L75 vs FIN_EQUAL

| Window | MDD dpp | Giveback pp | Rel NAV |
|---|---:|---:|---:|
| mtd | 0.0 | 107.41995416491044 | 0.9989 |
| ytd | 0.6862354707974583 | 1.641592842007622 | 0.9938 |
| trailing_1y | 0.6862354707974583 | 1.7758186020952138 | 0.9892 |
| sealed_2023_plus | 0.6862354707974805 | 0.4640827829000216 | 0.9872 |
| heldout_2019_plus | 0.22403955244294504 | 0.2785842804694294 | 0.9828 |
| full | 0.22403955244295615 | 0.16423259310764937 | 0.9810 |

## KD_OPT vs FIN_EQUAL

| Window | MDD dpp | Giveback pp | Rel NAV |
|---|---:|---:|---:|
| mtd | 0.0 | 98.9054356288328 | 0.9990 |
| ytd | 1.1616332365690263 | 0.8227996463336051 | 0.9969 |
| trailing_1y | 1.1616332365690374 | 1.2023236437952889 | 0.9927 |
| sealed_2023_plus | 1.1616332365690374 | 0.38161132984990687 | 0.9894 |
| heldout_2019_plus | 0.6664522064959488 | 0.266918547101902 | 0.9835 |
| full | 0.6664522064959599 | 0.05418908379983822 | 0.9937 |

## Alerts

- ALERT: FIN_RS_SOFT_TILT_EXDIV ytd CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: FIN_RS_SOFT_TILT_EXDIV ytd giveback > 5 pp — extend observe; Soft-Frozen unchanged; no live wire
- ALERT: FIN_RS_SOFT_TILT_EXDIV trailing_1y CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: FIN_RS_SOFT_TILT_EXDIV trailing_1y giveback > 5 pp — extend observe; Soft-Frozen unchanged; no live wire

## Hard rules

- Soft-Frozen KEEP · live FIN equal-split untouched · no cutover from this monitor

