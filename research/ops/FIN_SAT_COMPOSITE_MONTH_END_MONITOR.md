# FIN_SAT_COMPOSITE_MONTH_END_MONITOR month-end monitor (asof 2026-09-24)

Status: `OPERATING_OBSERVE` · paper only · base `CTRL_LIVE_A10` vs `COMP_H150_x_A20`

| Window | MDD dpp | Giveback pp | Score | Rel NAV |
|---|---:|---:|---:|---:|
| mtd | -0.05667562192775977 | 60.636955680043016 | -30.375153461949267 | 0.9823 |
| ytd | 0.9278208444160718 | 13.359102919624565 | -5.751730615396211 | 0.9388 |
| trailing_1y | 0.9278208444160829 | 9.020652972174004 | -3.582505641670919 | 0.9383 |
| heldout_2019_plus | -0.10882811199984799 | -0.5415301072626111 | -0.37959316563115353 | 1.0351 |
| sealed_2023_plus | -0.35602328353421253 | -1.8154954469024487 | -1.2637710069854369 | 1.0548 |
| full | -0.654111227882892 | -0.002480986570296828 | -0.6553517211680404 | 1.0003 |

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

