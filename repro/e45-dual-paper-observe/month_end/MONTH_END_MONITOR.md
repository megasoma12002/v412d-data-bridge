# E45_MONTH_END_PAPER_MONITOR month-end monitor (asof 2026-09-16)

Status: `OPERATING_OBSERVE` · paper only · base `BASE_E16_E18_E22_v2s` vs `CHAL_E45_E3`

| Window | MDD dpp | Giveback pp | Score | Rel NAV |
|---|---:|---:|---:|---:|
| mtd | -0.04895456271234444 | 100.89930105356206 | -50.498605089493374 | 0.9919 |
| ytd | -0.1611721113205955 | 11.416653243362118 | -5.869498733001654 | 0.9523 |
| trailing_1y | -0.1611721113205955 | 5.029313096963017 | -2.675828659802104 | 0.9663 |
| heldout_2019_plus | 4.075926552779796 | 2.2454060338332305 | 2.953223535863181 | 0.8648 |
| sealed_2023_plus | 0.9064031049189403 | 3.5692453138469693 | -0.8782195520045444 | 0.8994 |
| full | 4.075926552779774 | 1.2457212751060043 | 3.4530659152267718 | 0.8620 |

## Alerts

- ALERT: CHAL_E45_E3 ytd MDD worse than BASE_E16_E18_E22_v2s
- ALERT: CHAL_E45_E3 ytd CAGR giveback > 3.0 pp
- PAUSE_REVIEW: CHAL_E45_E3 ytd giveback > 5 pp
- ALERT: CHAL_E45_E3 trailing_1y MDD worse than BASE_E16_E18_E22_v2s
- ALERT: CHAL_E45_E3 trailing_1y CAGR giveback > 3.0 pp
- PAUSE_REVIEW: CHAL_E45_E3 trailing_1y giveback > 5 pp

## Non-actions

- paper observe only
- no Soft-Frozen clip flip
- no E45 stitch
- no live wire from this monitor

- Stitch / Soft-Frozen flip still require a separate human ACCEPT PR

