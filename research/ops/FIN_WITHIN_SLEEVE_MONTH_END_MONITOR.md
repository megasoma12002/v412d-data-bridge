# FIN_WITHIN_SLEEVE_MONTH_END_MONITOR month-end monitor (asof 2026-09-16)

**Status:** `OPERATING_OBSERVE` — **paper only**
**Books:** `FIN_EQUAL` ∥ `FIN_RS_SOFT_TILT_EXDIV` ∥ `MIX_L75` ∥ `KD_OPT`

## FIN_RS_SOFT_TILT_EXDIV vs FIN_EQUAL

| Window | MDD dpp | Giveback pp | Rel NAV |
|---|---:|---:|---:|
| mtd | -0.5948152272908014 | -32.696728591850466 | 1.0023 |
| ytd | -3.1258972421022047 | -0.8993090685381677 | 1.0037 |
| trailing_1y | -3.1258972421022047 | -3.7202608786424785 | 1.0249 |
| heldout_2019_plus | 0.5536506905494232 | -0.07528205645082053 | 1.0048 |
| sealed_2023_plus | 0.23749242776465174 | -2.2742480675583376 | 1.0681 |
| full | 0.553650690549401 | 0.29956775964066207 | 0.9651 |

## MIX_L75 vs FIN_EQUAL

| Window | MDD dpp | Giveback pp | Rel NAV |
|---|---:|---:|---:|
| mtd | 0.18649669957860882 | -68.96669805189708 | 1.0048 |
| ytd | 0.012359284949026161 | -1.177272901349724 | 1.0049 |
| trailing_1y | 0.012359284949026161 | -1.007514642159335 | 1.0068 |
| heldout_2019_plus | -0.08776488573204455 | -0.3564072087623771 | 1.0231 |
| sealed_2023_plus | 1.003777729317512 | -0.9933950674747338 | 1.0294 |
| full | -0.08776488573205565 | -0.1538232537013906 | 1.0184 |

## KD_OPT vs FIN_EQUAL

| Window | MDD dpp | Giveback pp | Rel NAV |
|---|---:|---:|---:|
| mtd | -0.42387312459120086 | -133.88256594582825 | 1.0089 |
| ytd | -4.70454996523979 | -2.0604497848165426 | 1.0085 |
| trailing_1y | -4.704549965239768 | -5.65412279484403 | 1.0379 |
| heldout_2019_plus | -1.0198312814840294 | -0.8181862193419098 | 1.0536 |
| sealed_2023_plus | -1.3411602953729451 | -3.501160899080813 | 1.1062 |
| full | -1.0198312814840516 | -0.3789339215908294 | 1.0459 |

## Alerts

- ALERT: FIN_RS_SOFT_TILT_EXDIV ytd MDD worse than FIN_EQUAL
- ALERT: FIN_RS_SOFT_TILT_EXDIV trailing_1y MDD worse than FIN_EQUAL
- ALERT: MIX_L75 heldout_2019_plus MDD worse than FIN_EQUAL
- ALERT: KD_OPT ytd MDD worse than FIN_EQUAL
- ALERT: KD_OPT trailing_1y MDD worse than FIN_EQUAL
- ALERT: KD_OPT heldout_2019_plus MDD worse than FIN_EQUAL
- ALERT: KD_OPT sealed_2023_plus MDD worse than FIN_EQUAL

## Non-actions

- OPERATING_OBSERVE — paper only
- No Soft-Frozen flip
- No live e21 FIN within-sleeve wire

- Soft-Frozen KEEP · live FIN equal-split untouched · no cutover from this monitor

