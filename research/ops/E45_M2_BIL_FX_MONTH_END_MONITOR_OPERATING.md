# E45_M2_BIL_FX_MONTH_END_MONITOR month-end monitor (asof 2026-09-16)

Status: `OPERATING_OBSERVE` · paper only · base `BASE_E16_E18_E22_v2s` vs `M2_RELOC_BIL_FX_C35`

| Window | MDD dpp | Giveback pp | Score | Rel NAV |
|---|---:|---:|---:|---:|
| mtd | -0.14246024933376455 | -5.40078709866636 | None | 1.0004 |
| ytd | 0.6579825167345121 | 9.516800024425276 | None | 0.9603 |
| trailing_1y | 0.6579825167345121 | 3.496546786494603 | None | 0.9766 |
| heldout_2019_plus | 6.215328045687107 | 1.810099076915872 | None | 0.8897 |
| sealed_2023_plus | 1.7365794992347583 | 3.1410164962151654 | None | 0.9111 |
| full | 6.215328045687086 | 1.3024942940583095 | None | 0.8561 |

## Alerts

- ALERT: M2_RELOC_BIL_FX_C35 ytd CAGR giveback > 3.0 pp
- PAUSE_REVIEW: M2_RELOC_BIL_FX_C35 ytd giveback > 5 pp
- ALERT: M2_RELOC_BIL_FX_C35 trailing_1y CAGR giveback > 3.0 pp

## Non-actions

- OPERATING_OBSERVE — paper only
- No Soft-Frozen / DEFAULT / stitch
- No live orders

- Honesty: BIL×USDTWD mid is a paper DEF proxy, not a live tradable book

