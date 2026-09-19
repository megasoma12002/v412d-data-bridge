# L4_DD_PATH_MONTH_END_PAPER_MONITOR month-end monitor (asof 2026-09-16)

Status: `OPERATING_OBSERVE` · paper only · base `BASE_E16` vs `L4_DD_PATH_08_50`

| Window | MDD dpp | Giveback pp | Score | Rel NAV |
|---|---:|---:|---:|---:|
| mtd | 0.2554858757042089 | 164.69630596705233 | None | 0.9905 |
| ytd | -0.5317537800048067 | 9.527221329209157 | None | 0.9629 |
| trailing_1y | -0.5317537800047956 | 5.332785493463743 | None | 0.9667 |
| sealed_2023_plus | -0.3184969690686934 | 2.9934755001865154 | None | 0.9174 |
| heldout_2019_plus | 1.4786100777752331 | 1.877682130119318 | None | 0.8871 |
| full | 1.4786100777752442 | 1.0253359517665483 | None | 0.8858 |
| validation_2019_2022 | 1.4786100777752331 | 0.9586955939638875 | None | 0.9669 |

## Alerts

- ALERT: L4_DD_PATH_08_50 sealed MDD worse than BASE (paper)
- ALERT: L4_DD_PATH_08_50 ytd CAGR giveback > 3.0 pp (paper ops)
- PAUSE_REVIEW: ytd giveback > 5 pp — extend observation; does not revoke PASS_HELDOUT_L4
- ALERT: L4_DD_PATH_08_50 trailing_1y CAGR giveback > 3.0 pp (paper ops)
- PAUSE_REVIEW: trailing_1y giveback > 5 pp — extend observation; does not revoke PASS_HELDOUT_L4

## Non-actions

- paper monitor only
- no Soft-Frozen clip flip
- cutover requires separate human PR

