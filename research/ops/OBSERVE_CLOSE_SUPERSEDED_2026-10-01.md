# OBSERVE_CLOSE_SUPERSEDED_2026-10-01

Date: 2026-10-01
Status: **EXECUTED** · Soft KEEP · Path3 WITHIN KEEP · T0 carve KEEP · ledger KEEP · DD_SWITCH tip apply KEEP · broker false · no live undo

## Human (exact)

```
CLOSE paper observe: TIPSOFT_P3_THETA_NEARPEAK3 + TIPSOFT_P3_ON_UNLESS_MUTE_FT_CASH + TIPSOFT_P3_TRAIL42_FT_CASH
(superseded by TIPSOFT_P3_TRAIL42_L4_DD_SWITCH tip apply LIVE · Soft FIN/TEL stay OFF · Path3 WITHIN KEEP)

CLOSE paper observe: COMP_H150_x_A20 + SAT_A20_RELAX + P3_T0_STATE
(Path3 WITHIN + T0 carve + ledger already LIVE · Soft KEEP · DD_SWITCH tip apply KEEP)
```

## DOWN — tip Soft old stack

| Reg | Policy | Why |
|---|---|---|
| `0kaw` | `TIPSOFT_P3_THETA_NEARPEAK3` | superseded by DD_SWITCH tip apply LIVE (via OVERRIDE→MUTE/TRAIL chain) |
| `0kba` | `TIPSOFT_P3_ON_UNLESS_MUTE_FT_CASH` | superseded by DD_SWITCH tip apply LIVE (KEEPBOTH already NO) |
| `0kbb` | `TIPSOFT_P3_TRAIL42_FT_CASH` | twin leg absorbed into DD_SWITCH tip apply LIVE |

## DOWN — Path3 paper shadows

| Reg | Policy | Why |
|---|---|---|
| `0k9b` | `COMP_H150_x_A20` | Path3 WITHIN + ledger already LIVE (paper COMPOSITE shadow) |
| `0k9d` | `SAT_A20_RELAX` | Path3 WITHIN + ledger already LIVE (paper SAT shadow) |
| `0k9r` | `P3_T0_STATE` | T0 carve + Path3 cutover already LIVE (paper observe shadow) |

## KEEP (unchanged)

- Live: Path3 `WITHIN_SLEEVE_PATH3` · T0 carve fill/emit · ledger · **DD_SWITCH tip apply** · Soft clips+0050 · COOL/FUSE/SELL_a75/CONF/TEL
- Observe KEEP: `TIPSOFT_P3_TRAIL42_L4_DD_SWITCH` dual-paper (live twin monitor)
- LIVE_OVERRIDE stamps (0kb2) unchanged this ballot

## Binding

1. CLOSE ≠ delete evidence/scripts; month-end + alert queue **SKIP** only.
2. Re-open any CLOSED observe needs **new human OPEN** ballot.
3. Do **not** unwind Path3 WITHIN / T0 carve / ledger / DD_SWITCH tip apply.
4. Soft FIN/TEL Exact T+1 stay OFF.

## Wiring

- `scripts/ops_month_end_paper_pack.py` — COMPOSITE / SAT_RELAX / P3_T0 monitors+ledgers commented
- `scripts/ops_alert_scan.py` — COMPOSITE / SAT_RELAX / P3_T0 alert sources commented
- Register / OPS_STATUS / portfolio archive updated

Label: `OBSERVE_CLOSE_SUPERSEDED_2026-10-01__TIPSOFT_OLDSTACK__PATH3_SHADOW`

