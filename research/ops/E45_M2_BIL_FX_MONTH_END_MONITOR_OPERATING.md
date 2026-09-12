# E45 M2 BIL_FX month-end monitor (asof 2026-09-11)

**Status:** `OPERATING_OBSERVE` — **OPERATING (paper only)**
**Locked:** `M2_RELOC_BIL_FX_C35` vs BASE

| Window | MDD dpp | Giveback pp | Rel NAV |
|---|---:|---:|---:|
| mtd | 0.13095247563643664 | 58.00939444403532 | 0.9980 |
| ytd | 1.1999153776515503 | 8.362458707585851 | 0.9681 |
| trailing_1y | 1.1999153776515614 | 5.03099426104352 | 0.9692 |
| sealed_2023_plus | 1.1999153776515614 | 3.026408310199935 | 0.9183 |
| heldout_2019_plus | 2.5296553863856097 | 2.07278508224098 | 0.8780 |
| full | 2.5296553863855986 | 1.54036082451956 | 0.8344 |

## Alerts

- ALERT: M2_RELOC_BIL_FX_C35 ytd CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: ytd giveback > 5 pp — extend observe; Soft-Frozen unchanged; no stitch talk
- ALERT: M2_RELOC_BIL_FX_C35 trailing_1y CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: trailing_1y giveback > 5 pp — extend observe; Soft-Frozen unchanged; no stitch talk

## Honesty

- BIL_FX = USD T-bill × USDTWD mid (FX risk; mid optimistic; not TWD cash)
- Soft-Frozen KEEP · stitch FORBIDDEN · no live wire

