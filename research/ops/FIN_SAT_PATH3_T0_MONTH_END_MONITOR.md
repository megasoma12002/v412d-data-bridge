# FIN_SAT_PATH3_T0_MONTH_END_MONITOR month-end monitor (asof 2026-09-29)

Status: `OPERATING_OBSERVE` · paper only · base `CTRL_LIVE_A10` vs `P3_T0_STATE`

| Window | MDD dpp | Giveback pp | Score | Rel NAV |
|---|---:|---:|---:|---:|
| mtd | -0.02399878186186699 | -1.3983326614158909 | -0.7231651125698124 | 1.0005 |
| ytd | 0.02103733279175124 | -2.8142754218028143 | -1.386100378109656 | 1.0131 |
| trailing_1y | 0.021037332791717933 | -2.017673699839939 | -0.9877995171282516 | 1.0139 |
| heldout_2019_plus | 0.09952764086511579 | -3.7622147437841758 | -1.781579731026972 | 1.2672 |
| sealed_2023_plus | -0.1650873177246548 | -4.7285250751666785 | -2.529349855307994 | 1.1482 |
| full | 0.09952764086510468 | -3.5526227210549877 | -1.6767837196623891 | 1.5141 |

## Alerts

- ALERT: P3_T0_STATE sealed_2023_plus MDD worse than CTRL_LIVE_A10

## Non-actions

- paper observe only
- Exact T+0 carve-out T0_CARVE_FIN_SAT_SWITCH only — no expand
- no Soft-Frozen clip flip
- no live wire / CONF α flip from this monitor
- COMPOSITE + SAT_RELAX observes KEEP
- cutover BLOCKED

- Soft-Frozen clips KEEP · T0 carve Path3 only · cutover BLOCKED

