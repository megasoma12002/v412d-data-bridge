# E45 M2 BIL_FX month-end monitor (asof 2026-09-07)

**Status:** `OPERATING_OBSERVE` — **OPERATING (paper only)**
**Locked:** `M2_RELOC_BIL_FX_C35` vs BASE

| Window | MDD dpp | Giveback pp | Rel NAV |
|---|---:|---:|---:|
| mtd | 0.0 | 141.103004248407 | 0.9984 |
| ytd | 0.847639939138134 | 9.508101920169821 | 0.9641 |
| trailing_1y | 0.8476399391381229 | 6.274226468500221 | 0.9617 |
| sealed_2023_plus | -0.655458146199861 | 3.1087957269206212 | 0.9156 |
| heldout_2019_plus | 2.308622276182526 | 2.0426327897418384 | 0.8789 |
| full | 2.308622276182537 | 1.4297765316865663 | 0.8448 |

## Alerts

- ALERT: M2_RELOC_BIL_FX_C35 ytd CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: ytd giveback > 5 pp — extend observe; Soft-Frozen unchanged; no stitch talk
- ALERT: M2_RELOC_BIL_FX_C35 trailing_1y CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: trailing_1y giveback > 5 pp — extend observe; Soft-Frozen unchanged; no stitch talk
- ALERT: M2_RELOC_BIL_FX_C35 sealed_2023_plus MDD worse than BASE (structural window; design expected MDD improve)

## Honesty

- BIL_FX = USD T-bill × USDTWD mid (FX risk; mid optimistic; not TWD cash)
- Soft-Frozen KEEP · stitch FORBIDDEN · no live wire

