# FIN_SAT_COMPOSITE_MONTH_END_MONITOR month-end monitor (asof 2026-09-29)

Status: `OPERATING_OBSERVE` · paper only · base `CTRL_LIVE_A10` vs `COMP_H150_x_A20`

| Window | MDD dpp | Giveback pp | Score | Rel NAV |
|---|---:|---:|---:|---:|
| mtd | 0.1670012288985001 | 38.0908118386549 | -18.87840469042895 | 0.9846 |
| ytd | 0.9278208444160718 | 12.4811756742639 | -5.312766992715878 | 0.9409 |
| trailing_1y | 0.9278208444160496 | 8.934309724275113 | -3.539334017721507 | 0.9382 |
| heldout_2019_plus | -0.10882811199984799 | -0.5764459177932002 | -0.3970510708964481 | 1.0375 |
| sealed_2023_plus | -0.35602328353421253 | -1.883560478820523 | -1.297803522944474 | 1.0573 |
| full | -0.654111227882892 | -0.02205995822710527 | -0.6651412069964446 | 1.0026 |

## Alerts

- ALERT: COMP_H150_x_A20 ytd CAGR giveback > 3.0 pp
- PAUSE_REVIEW: COMP_H150_x_A20 ytd giveback > 5 pp
- ALERT: COMP_H150_x_A20 trailing_1y CAGR giveback > 3.0 pp
- PAUSE_REVIEW: COMP_H150_x_A20 trailing_1y giveback > 5 pp
- ALERT: COMP_H150_x_A20 heldout_2019_plus MDD worse than CTRL_LIVE_A10
- ALERT: COMP_H150_x_A20 sealed_2023_plus MDD worse than CTRL_LIVE_A10

## Non-actions

- paper observe only
- no Soft-Frozen clip flip
- no live CONF α densify / HARD150 wire from this monitor
- COMPOSITE_HIT observe posture only · cutover BLOCKED
- SELL_a75 KEEP · live CONF α=0.10 KEEP

- Soft-Frozen KEEP · cutover BLOCKED · FIN×SAT COMPOSITE COMP_H150_x_A20 observe

