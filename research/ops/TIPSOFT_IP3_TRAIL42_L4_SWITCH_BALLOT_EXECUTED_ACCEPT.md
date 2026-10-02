# TIPSOFT_IP3_TRAIL42_L4_SWITCH — Ballot EXECUTED (ACCEPT tip apply)

Date: 2026-10-01  
Status: **EXECUTED ACCEPT / LIVE WIRED (tip apply)** · Exact T+1 · Path3 WITHIN **KEEP** · Soft FIN/TEL stay **OFF** · Soft clips+0050 **KEEP** · T0 carve **KEEP** · Path4 **OFF** · broker **false** · dual-paper observe **KEEP** · **not** stamps-only · **not** year-switch · **not** research return-blend on tip Soft shell

Register: **0kbd** · Parents: observe OPEN · Stage A `SIGNAL_SWITCH_HIT` · 0kbb/0kba/0kbc/0kac

## Human (exact)

```
ACCEPT tip apply: TIPSOFT_P3_TRAIL42_L4_DD_SWITCH
(tip Soft Exact T+1 · dual-book DD switch · Soft FIN/TEL stay OFF ·
 Path3 WITHIN KEEP · Path4 OFF · broker false · NOT year-switch · NOT stamps-only)
```

## What changed

| Item | Before | After ACCEPT |
|---|---|---|
| `LIVE.live_tipsoft_dd_switch` | False / absent | **True** |
| `LIVE.live_tipsoft_dd_switch_policy` | — | **`TIPSOFT_P3_TRAIL42_L4_DD_SWITCH`** |
| tip Soft Exact T+1 DD_SWITCH | paper observe only | **LIVE WIRED** (`path3_gate_ft_cash_apply`) |
| Path3 gate | always WITHIN daily | **TRAIL if TRAIL_DD≥L4_DD else L4**; TRAIL days: TRAIL42 ON→WITHIN / OFF→FIN∪TEL→cash (`-P3T0`) |
| Path3 `WITHIN_SLEEVE_PATH3` cutover | ON | **KEEP** |
| Soft Exact T+1 FIN∪TEL | OFF daily | **stay OFF** |
| Soft Exact T+1 0050 / Soft clips | KEEP | **KEEP** |
| T+0 carve `T0_CARVE_FIN_SAT_SWITCH` | ON | **KEEP** |
| Path4 live | OFF | **OFF** |
| Broker | false | **false** |
| Dual-paper observe 0kbd | OPERATING | **KEEP** · 0kba/0kbb **CLOSED** 2026-10-01 |
| LIVE_OVERRIDE stamps (0kb2) | ON | **KEEP** (stamps/telemetry; not superseded) |

## Wire

- `scripts/live_config.py` — flag / policy / ballot
- `scripts/live_tipsoft_dd_switch.py` — dual-book DD + TRAIL42 gate SSOT · FIN∪TEL flatten
- `scripts/e21_forward_pipeline.py` — mutate Path3 deltas before `-P3T0` emit · session stamps
- `scripts/live_tip_meta.py` — cutover stamps
- Tests: `tests/test_tipsoft_dd_switch.py`

## Evidence

- Stage A `SIGNAL_SWITCH_HIT` · champ `SW_TRAIL_WHEN_TR_DD_GTE_L4` held **+3.5275** tipY **+27.5471** sealedMDD **+0.4692**
- Observe OPEN / OPERATING: `TIPSOFT_IP3_TRAIL42_L4_SWITCH_OBSERVE_BALLOT_EXECUTED_OPEN.md`
- Dual-paper: `TIPSOFT_IP3_TRAIL42_L4_SWITCH_DUAL_PAPER_OBSERVE_OPERATING.md`

## Non-actions

- Soft-Frozen KEEP
- Soft FIN/TEL Exact T+1 stay OFF (no Soft-refill)
- Path4 live OFF
- Calendar-year switch / year-oracle FORBIDDEN
- Research return-blend on tip Soft shell FORBIDDEN (wire is Path3 gate + FT→CASH)
- LIVE_OVERRIDE stamps KEEP (separate mechanism)
- Sibling 0kba / 0kbb observes **CLOSED** 2026-10-01 (`OBSERVE_CLOSE_SUPERSEDED_2026-10-01`)
- Broker false

Label: `TIPSOFT_IP3_TRAIL42_L4_SWITCH_BALLOT_EXECUTED_ACCEPT_2026-10-01__ACCEPT__TIP_APPLY__NO_BROKER`
