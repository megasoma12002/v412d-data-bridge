# tip Soft Exact T+1 LIVE_OVERRIDE — ACCEPT ballot **OPEN**

Date opened: 2026-09-30  
Status: **OPEN — awaiting human** · Soft KEEP · Path4 OFF · broker **false** · live flag still **OFF**  
Register: **0kb2** · Parents: Stage A `IP3_LIVE_STACK_RACE_HIT` · observe OPEN · 0kb5 `T0_NOT_DRIVER`  
Pre-ACCEPT: observe OPERATING · cutover checklist was BLOCKED pending this ballot

## Why open now

- Dual-paper observe OPEN: held vs live **+1.61** · tipY **+6.04** · sealed **−0.05**
- 0kb5: gap is **not** T+0 — same-clock Exact T+1 stack (mute+override)
- Human path confirmed: **追上 live = ACCEPT 上 Exact T+1 LIVE_OVERRIDE**
- This OPEN does **not** wire today — execute only after exact ACCEPT reply below

## Coexistence (must stay explicit)

| Layer | Status after proposed ACCEPT |
|---|---|
| Path3 `WITHIN_SLEEVE_PATH3` (0kac) | **KEEP** — Soft FIN/TEL Exact T+1 stay **OFF** |
| Path3 T+0 carve `T0_CARVE_FIN_SAT_SWITCH` | **KEEP** |
| tip Soft Exact T+1 `LIVE_OVERRIDE_W42_M05_K3` | **LIVE WIRE** (new) |
| Soft clips + Soft 0050 Exact T+1 | **KEEP** |
| Path4 live | **OFF** |
| Broker | **false** (separate) |

Note: research NAV lead was measured vs Soft+FUSE+COOL Exact T+1 (L3). Live Path3 WITHIN already replaced Soft FIN/TEL daily. ACCEPT wires tip Soft override on the **Exact T+1 tip Soft shell** (Soft+FUSE+COOL + stack gate); it does **not** undo Path3 WITHIN or re-enable Soft FIN/TEL.

## Exact human replies (pick one)

### ACCEPT (authorize EXECUTED wire)

```
ACCEPT live wire: TIPSOFT_P3_LIVE_OVERRIDE_W42_M05_K3
(Exact T+1 · 0kb1 MUTE_S3_SAT + force LIVE when lag42 live leads champ by >0.5% for 3d ·
 Path3 WITHIN_SLEEVE KEEP · Soft FIN/TEL stay OFF · Soft clips+0050 KEEP ·
 T0_CARVE_FIN_SAT_SWITCH KEEP · Path4 OFF · broker false · dual-paper observe KEEP)
```

### DEFER

```
DEFER live wire: TIPSOFT_P3_LIVE_OVERRIDE_W42_M05_K3
```

### REJECT

```
REJECT live wire: TIPSOFT_P3_LIVE_OVERRIDE_W42_M05_K3
```

## What ACCEPT authorizes (EXECUTED follow-up only)

| Item | After EXECUTED ACCEPT |
|---|---|
| `LIVE.live_tipsoft_live_override` | **True** |
| Policy | Exact T+1 · MUTE_S3_SAT base · OVERRIDE W42/M0.5%/K3 |
| Path3 WITHIN / T0 carve | **KEEP** |
| Soft FIN/TEL Exact T+1 | **stay OFF** (0kac) |
| Soft clips + 0050 | **KEEP** |
| Path4 live | **OFF** |
| Broker | **false** |
| Dual-paper observe 0kb2 | **KEEP OPERATING** |

Wire files (EXECUTED only): `live_config.py` · `live_tipsoft_live_override.py` (new) · `e21_forward_pipeline.py` / tip meta stamps · tests.

## What this OPEN ballot does **not** do

- Does **not** flip any live flag today
- Does **not** authorize broker SendOrder
- Does **not** undo Path3 `WITHIN_SLEEVE_PATH3`
- Does **not** promote Path4 / hybrid T+0 / year-cut

## Evidence index

- Observe: `TIPSOFT_IP3_LIVE_OVERRIDE_OBSERVE_BALLOT_EXECUTED_OPEN.md`
- Operating: `TIPSOFT_IP3_LIVE_OVERRIDE_DUAL_PAPER_OBSERVE_OPERATING.md`
- T+0 attrib: `TIPSOFT_IP3_T0_GAP_ATTRIB_STAGEA_DECISION_PACK.md` (`T0_NOT_DRIVER`)
- Cutover: `CUTOVER_CHECKLIST_TIPSOFT_IP3_LIVE_OVERRIDE.md`

Label: `TIPSOFT_IP3_LIVE_OVERRIDE_ACCEPT_BALLOT_OPEN_2026-09-30__AWAITING_ACCEPT__NO_LIVE_WIRE`
