# SAT_A20_RELAX_MONTH_END_MONITOR month-end monitor (asof 2026-09-29)

Status: `OPERATING_OBSERVE` · paper only · base `CTRL_LIVE_A10` vs `SAT_A20_RELAX`

| Window | MDD dpp | Giveback pp | Score | Rel NAV |
|---|---:|---:|---:|---:|
| mtd | -0.02399878186186699 | -1.3983326614158909 | -0.7231651125698124 | 1.0005 |
| ytd | 0.021037332791729035 | -0.6872868326275539 | -0.3226060835220479 | 1.0032 |
| trailing_1y | 0.02103733279170683 | -0.7484000773765764 | -0.3531627058965814 | 1.0052 |
| heldout_2019_plus | -0.3084642430070672 | -0.335428886454614 | -0.4761786862343742 | 1.0217 |
| sealed_2023_plus | -0.09929197836232584 | -0.13543139081897415 | -0.16700767377181291 | 1.0040 |
| full | -0.3084642430070561 | -0.20567543409053535 | -0.4113019600523238 | 1.0247 |

## Alerts

- ALERT: SAT_A20_RELAX heldout_2019_plus MDD worse than CTRL_LIVE_A10
- ALERT: SAT_A20_RELAX sealed_2023_plus MDD worse than CTRL_LIVE_A10

## Non-actions

- paper observe only
- no Soft-Frozen clip flip
- no live CONF α densify from this monitor
- SAT_RELAX_HIT tip-first posture · cutover BLOCKED
- COMPOSITE observe KEEP (parallel)

- Soft-Frozen KEEP · cutover BLOCKED · SAT_A20_RELAX tip-first observe

