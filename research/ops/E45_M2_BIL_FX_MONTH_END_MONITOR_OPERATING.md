# E45 M2 BIL_FX month-end monitor (asof 2026-09-04)

**Status:** `OPERATING_OBSERVE` — **OPERATING (paper only)**
**Locked:** `M2_RELOC_BIL_FX_C50` vs BASE

| Window | MDD dpp | Giveback pp | Rel NAV |
|---|---:|---:|---:|
| mtd | 0.0 | 293.15676712071195 | 0.9982 |
| ytd | 2.6529631455861846 | 13.270848717038387 | 0.9489 |
| trailing_1y | 2.6529631455861957 | 9.576924916228368 | 0.9405 |
| sealed_2023_plus | 2.652963145586207 | 4.755390094477008 | 0.8735 |
| heldout_2019_plus | 2.9585299388856345 | 3.431416298385259 | 0.8050 |
| full | 2.9585299388856234 | 2.460065535531619 | 0.7478 |

## Alerts

- ALERT: M2_RELOC_BIL_FX_C50 ytd CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: ytd giveback > 5 pp — extend observe; Soft-Frozen unchanged; no stitch talk
- ALERT: M2_RELOC_BIL_FX_C50 trailing_1y CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: trailing_1y giveback > 5 pp — extend observe; Soft-Frozen unchanged; no stitch talk

## Honesty

- BIL_FX = USD T-bill × USDTWD mid (FX risk; mid optimistic; not TWD cash)
- Soft-Frozen KEEP · stitch FORBIDDEN · no live wire

