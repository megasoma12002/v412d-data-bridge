# E45 M2 BIL_FX month-end monitor (asof 2026-09-08)

**Status:** `OPERATING_OBSERVE` — **OPERATING (paper only)**
**Locked:** `M2_RELOC_BIL_FX_C35` vs BASE

| Window | MDD dpp | Giveback pp | Rel NAV |
|---|---:|---:|---:|
| mtd | 0.0 | 228.70202103526083 | 0.9975 |
| ytd | 1.1999153776515503 | 8.56000556511547 | 0.9676 |
| trailing_1y | 1.1999153776515614 | 5.518401967032638 | 0.9663 |
| sealed_2023_plus | 1.1999153776515614 | 3.0461167172473935 | 0.9178 |
| heldout_2019_plus | 2.5296553863856097 | 2.0813426599607165 | 0.8776 |
| full | 2.5296553863855986 | 1.5448708156320157 | 0.8340 |

## Alerts

- ALERT: M2_RELOC_BIL_FX_C35 ytd CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: ytd giveback > 5 pp — extend observe; Soft-Frozen unchanged; no stitch talk
- ALERT: M2_RELOC_BIL_FX_C35 trailing_1y CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: trailing_1y giveback > 5 pp — extend observe; Soft-Frozen unchanged; no stitch talk

## Honesty

- BIL_FX = USD T-bill × USDTWD mid (FX risk; mid optimistic; not TWD cash)
- Soft-Frozen KEEP · stitch FORBIDDEN · no live wire

