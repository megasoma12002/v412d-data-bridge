# E45 M2 BIL_FX month-end monitor (asof 2026-09-07)

**Status:** `OPERATING_OBSERVE` — **OPERATING (paper only)**
**Locked:** `M2_RELOC_BIL_FX_C35` vs BASE

| Window | MDD dpp | Giveback pp | Rel NAV |
|---|---:|---:|---:|
| mtd | 0.0 | 242.5880571499933 | 0.9976 |
| ytd | 2.288363517446379 | 10.404333361794249 | 0.9607 |
| trailing_1y | 2.28836351744639 | 7.980619760498486 | 0.9518 |
| sealed_2023_plus | 2.288363517446379 | 3.303639538617409 | 0.9113 |
| heldout_2019_plus | 2.223693801227644 | 2.5759489529906476 | 0.8510 |
| full | 2.223693801227644 | 1.7146655664981747 | 0.8178 |

## Alerts

- ALERT: M2_RELOC_BIL_FX_C35 ytd CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: ytd giveback > 5 pp — extend observe; Soft-Frozen unchanged; no stitch talk
- ALERT: M2_RELOC_BIL_FX_C35 trailing_1y CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: trailing_1y giveback > 5 pp — extend observe; Soft-Frozen unchanged; no stitch talk

## Honesty

- BIL_FX = USD T-bill × USDTWD mid (FX risk; mid optimistic; not TWD cash)
- Soft-Frozen KEEP · stitch FORBIDDEN · no live wire

