# E45 M2 BIL_FX month-end monitor (asof 2026-09-04)

**Status:** `OPERATING_OBSERVE` — **OPERATING (paper only)**
**Locked:** `M2_RELOC_BIL_FX_C35` vs BASE

| Window | MDD dpp | Giveback pp | Rel NAV |
|---|---:|---:|---:|
| mtd | 0.0 | 175.10512251258598 | 0.9990 |
| ytd | 1.5267479674788698 | 8.683488729154742 | 0.9667 |
| trailing_1y | 1.5267479674788698 | 5.988747935946526 | 0.9628 |
| sealed_2023_plus | 1.5267479674788698 | 3.157810884254153 | 0.9146 |
| heldout_2019_plus | 2.619027821648412 | 2.226804669213278 | 0.8694 |
| full | 2.619027821648401 | 1.6183767748173539 | 0.8266 |

## Alerts

- ALERT: M2_RELOC_BIL_FX_C35 ytd CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: ytd giveback > 5 pp — extend observe; Soft-Frozen unchanged; no stitch talk
- ALERT: M2_RELOC_BIL_FX_C35 trailing_1y CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: trailing_1y giveback > 5 pp — extend observe; Soft-Frozen unchanged; no stitch talk

## Honesty

- BIL_FX = USD T-bill × USDTWD mid (FX risk; mid optimistic; not TWD cash)
- Soft-Frozen KEEP · stitch FORBIDDEN · no live wire

