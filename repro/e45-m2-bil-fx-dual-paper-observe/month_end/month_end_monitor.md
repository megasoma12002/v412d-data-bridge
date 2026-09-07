# E45 M2 BIL_FX month-end monitor (asof 2026-09-07)

**Status:** `OPERATING_OBSERVE` — **OPERATING (paper only)**
**Locked:** `M2_RELOC_BIL_FX_C35` vs BASE

| Window | MDD dpp | Giveback pp | Rel NAV |
|---|---:|---:|---:|
| mtd | 0.0 | 135.54534018732483 | 0.9986 |
| ytd | 0.8100032504814947 | 7.561229307588935 | 0.9710 |
| trailing_1y | 0.8100032504815058 | 4.76242969054792 | 0.9705 |
| sealed_2023_plus | 0.8100032504814725 | 2.3706898772334117 | 0.9356 |
| heldout_2019_plus | 2.5206912403308412 | 1.4268883738174365 | 0.9141 |
| full | 2.520691240330808 | 1.0913155664906693 | 0.8797 |

## Alerts

- ALERT: M2_RELOC_BIL_FX_C35 ytd CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: ytd giveback > 5 pp — extend observe; Soft-Frozen unchanged; no stitch talk
- ALERT: M2_RELOC_BIL_FX_C35 trailing_1y CAGR giveback > 3.0 pp (paper)

## Honesty

- BIL_FX = USD T-bill × USDTWD mid (FX risk; mid optimistic; not TWD cash)
- Soft-Frozen KEEP · stitch FORBIDDEN · no live wire

