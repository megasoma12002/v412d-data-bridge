# FIN_SELL_DIAG_BREAK5_MONITOR_STAGEA_SCREEN

Date: 2026-09-28 · Generated `2026-09-28T07:57:39Z`
Status: **MONITOR_READY** · Soft-Frozen **KEEP** · SELL_a75 **KEEP** · `fin_sell_ok` **not applied** · live wire **false**

Track **C** · Parent: `research/ops/FIN_SELL_DIAG_ROLE_STAGEA_CHARTER.md` (A_BREAK5 = DIAG_SIGNAL).
Base `CTRL_BASE` = live Soft-Frozen + FUSE **SELL_a75** + COOL_c8 · Exact T+1.
Role: **diagnostic monitor/log** of `A_BREAK5` on FIN SELL fills (H=21, win = fwd ret&lt;0).
Unconditional sell WR = **34.96%** (n=924).

Ready bar: lift≥**+3.0pp** · n≥**80** · coverage ∈[5.0,70.0]%.
Weak bar: lift≥**+1.5pp** · n≥**50** · same coverage · else DRIFT/NO_SIGNAL.

## A_BREAK5 vs unconditional

| Attr | n | WR% | WR↑pp | cov% | READY | WEAK |
|---|---:|---:|---:|---:|---|---|
| A_BREAK5 | 98 | 38.7755 | 3.8188 | 10.6061 | True | False |

Monitor CSV: `repro/fin-sell-diag-break5-monitor-stagea/outputs/sell_break5_monitor.csv` (columns: date, code, break5, fwd_ret_21, win).

Verdict: **`MONITOR_READY`**

Label: `FIN_SELL_DIAG_BREAK5_MONITOR_STAGEA_SCREEN_2026-09-28__MONITOR_READY`
