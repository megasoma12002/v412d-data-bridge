# FIN_SAT_PATH3_T0_MONTH_END_MONITOR month-end monitor (asof 2026-09-24)

Status: `OPERATING_OBSERVE` · paper only · base `CTRL_LIVE_A10` vs `P3_T0_STATE`

| Window | MDD dpp | Giveback pp | Score | Rel NAV |
|---|---:|---:|---:|---:|
| mtd | -0.037486185709534325 | -1.4582600328258088 | -0.7666162021224388 | 1.0004 |
| ytd | 0.021037332791740138 | -2.732537325539819 | -1.3452313299781693 | 1.0123 |
| trailing_1y | 0.02103733279175124 | -1.7356034444965251 | -0.8467643894565113 | 1.0118 |
| heldout_2019_plus | 0.09952764086510468 | -3.4758344578240674 | -1.638389588046929 | 1.2441 |
| sealed_2023_plus | -0.1650873177247214 | -4.782229067657684 | -2.5562018515535634 | 1.1490 |
| full | 0.09952764086508248 | -3.228254309244716 | -1.5145995137572754 | 1.4577 |

## Alerts

- ALERT: P3_T0_STATE sealed_2023_plus MDD worse than CTRL_LIVE_A10
- Disposition: human **ACCEPTABLE** (−0.17pp; abs sealed |MDD|≪full/held) · `FIN_SAT_PATH3_T0_SEALED_MDD_DISPOSITION.md` · cutover still BLOCKED

## Non-actions

- paper observe only
- Exact T+0 carve-out T0_CARVE_FIN_SAT_SWITCH only — no expand
- no Soft-Frozen clip flip
- no live wire / CONF α flip from this monitor
- COMPOSITE + SAT_RELAX observes KEEP
- cutover BLOCKED

- Soft-Frozen clips KEEP · T0 carve Path3 only · cutover BLOCKED

