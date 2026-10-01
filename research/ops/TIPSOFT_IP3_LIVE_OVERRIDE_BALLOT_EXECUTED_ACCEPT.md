# tip Soft Exact T+1 LIVE_OVERRIDE — Ballot EXECUTED (ACCEPT)

Date: 2026-09-30  
Status: **EXECUTED ACCEPT / LIVE WIRED (gate stamps / telemetry)** · Exact T+1 · Path3 WITHIN **KEEP** · Soft FIN/TEL stay **OFF** · Soft clips+0050 **KEEP** · T0 carve **KEEP** · Path4 **OFF** · broker **false** · dual-paper observe **KEEP** · **not** research return-blend on tip orders

Register: **0kb2** · Parents: observe OPEN · 0kb5 `T0_NOT_DRIVER` · ACCEPT ballot OPEN

## Human (exact)

```
ACCEPT live wire: TIPSOFT_P3_LIVE_OVERRIDE_W42_M05_K3
(Exact T+1 · 0kb1 MUTE_S3_SAT + force LIVE when lag42 live leads champ by >0.5% for 3d ·
 Path3 WITHIN_SLEEVE KEEP · Soft FIN/TEL stay OFF · Soft clips+0050 KEEP ·
 T0_CARVE_FIN_SAT_SWITCH KEEP · Path4 OFF · broker false · dual-paper observe KEEP)
```

## What changed

| Item | Before | After ACCEPT |
|---|---|---|
| `LIVE.live_tipsoft_live_override` | False / absent | **True** |
| `LIVE.live_tipsoft_live_override_policy` | — | **`TIPSOFT_P3_LIVE_OVERRIDE_W42_M05_K3`** |
| tip Soft Exact T+1 LIVE_OVERRIDE gate | paper observe only | **LIVE WIRED** (`gate_stamps_telemetry` · session stamps + causal lag42 gate · **no** `order_rows` blend) |
| Path3 `WITHIN_SLEEVE_PATH3` | ON | **KEEP** |
| Soft Exact T+1 FIN∪TEL | OFF daily | **stay OFF** |
| Soft Exact T+1 0050 / Soft clips | KEEP | **KEEP** |
| T+0 carve `T0_CARVE_FIN_SAT_SWITCH` | ON | **KEEP** |
| Path4 live | OFF | **OFF** |
| Broker | false | **false** |
| Dual-paper observe 0kb2 | OPERATING | **KEEP OPERATING** |

## Wire

- `scripts/live_config.py` — flag / policy / ballot
- `scripts/live_tipsoft_live_override.py` — gate SSOT + session meta
- `scripts/live_tip_meta.py` — cutover stamps
- `scripts/e21_forward_pipeline.py` — session signal stamps
- Tests: `tests/test_tipsoft_live_override.py`

## Evidence

- Observe dual-paper: held vs live **+1.61** · tipY **+6.04** · sealed **−0.05**
- 0kb5 `T0_NOT_DRIVER` — gap not from T+0
- ACCEPT ballot OPEN superseded by this EXECUTED

## Non-actions

- Do not enable broker live-write from this ballot
- Do not undo Path3 WITHIN / re-enable Soft FIN/TEL
- Do not promote Path4 / hybrid T+0 / year-cut
- Soft FIN/TEL parity with research Soft shell is **out of scope** (Path3 WITHIN KEEP)

Supersedes OPEN: `TIPSOFT_IP3_LIVE_OVERRIDE_ACCEPT_BALLOT_OPEN.md`

Label: `TIPSOFT_IP3_LIVE_OVERRIDE_BALLOT_EXECUTED_ACCEPT_2026-09-30__ACCEPT__LIVE_WIRE__NO_BROKER`
