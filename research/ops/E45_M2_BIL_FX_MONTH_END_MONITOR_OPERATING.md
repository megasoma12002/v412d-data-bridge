# E45 M2 BIL_FX month-end monitor (asof 2026-09-09)

**Status:** `OPERATING_OBSERVE` — **OPERATING (paper only)**
**Locked:** `M2_RELOC_BIL_FX_C35` vs BASE

| Window | MDD dpp | Giveback pp | Rel NAV |
|---|---:|---:|---:|
| mtd | 0.13095247563643664 | 31.90577494384703 | 0.9988 |
| ytd | 1.1999153776515503 | 7.979085723001078 | 0.9689 |
| trailing_1y | 1.1999153776515614 | 4.919524535217268 | 0.9693 |
| sealed_2023_plus | 1.1999153776515614 | 2.9838121441228216 | 0.9190 |
| heldout_2019_plus | 2.5296553863856097 | 2.055310081167483 | 0.8787 |
| full | 2.5296553863855986 | 1.5315787278481041 | 0.8351 |

## Alerts

- ALERT: M2_RELOC_BIL_FX_C35 ytd CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: ytd giveback > 5 pp — extend observe; Soft-Frozen unchanged; no stitch talk
- ALERT: M2_RELOC_BIL_FX_C35 trailing_1y CAGR giveback > 3.0 pp (paper)

## Honesty

- BIL_FX = USD T-bill × USDTWD mid (FX risk; mid optimistic; not TWD cash)
- Soft-Frozen KEEP · stitch FORBIDDEN · no live wire

