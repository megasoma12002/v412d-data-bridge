# Path3 strategy cutover — ACCEPT ballot **OPEN**

Date opened: 2026-09-30  
Status: **OPEN — awaiting human** · Soft clips+0050 Exact T+1 **KEEP** · broker **false** · live flag still **OFF**  
Status: **SUPERSEDED by EXECUTED ACCEPT** · see `LIVE_PATH3_STRATEGY_CUTOVER_BALLOT_EXECUTED_ACCEPT.md` · Soft clips+0050 Exact T+1 **KEEP** · broker **false** · live flag still **OFF**  
Register parents: **0kac** / **0kam** `PAPER_WITHIN_HIT` · Pre-ACCEPT: `PATH3_STRATEGY_CUTOVER_PREACCEPT_DISPOSITION.md`

## Why open now

Stage B paper dual hit **`PAPER_WITHIN_HIT`** (WITHIN−FLIP held **+3.04** · tipY **+0.27** · sealed MDD **+7.24** · yearly **14–1**).  
Pre-ACCEPT disposition cites sealed / wrong-stay / 2022 / overlay-design / parent-observe KEEP.

## Exact human replies (pick one)

### ACCEPT (authorize wire prep + flag ON under scope)

```
ACCEPT Path3 strategy cutover: WITHIN_SLEEVE_PATH3
(Soft clips+0050 Exact T+1 KEEP · Soft FIN/TEL Exact T+1 OFF · Path3 ledger daily ·
 T0_CARVE_FIN_SAT_SWITCH KEEP · broker false · overlays KEEP)
```

### DEFER

```
DEFER Path3 strategy cutover: WITHIN_SLEEVE_PATH3
```

### REJECT

```
REJECT Path3 strategy cutover: WITHIN_SLEEVE_PATH3
```

## What ACCEPT authorizes (EXECUTED follow-up)

| Item | After EXECUTED ACCEPT |
|---|---|
| `LIVE.live_path3_strategy_cutover` | **True** |
| `LIVE.live_path3_strategy_cutover_scope` | **`WITHIN_SLEEVE_PATH3`** |
| Soft Exact T+1 FIN∪TEL | **OFF** (daily) |
| Soft Exact T+1 0050 + Soft clips | **KEEP** |
| Path3 ledger recon | **daily** toward active COMP/SAT book |
| T+0 carve | **narrow KEEP** `T0_CARVE_FIN_SAT_SWITCH` |
| Flip mute | superseded-when-ON |
| Broker `broker_live_write_accepted` | **false** (separate ballot) |
| COMPOSITE / SAT_RELAX / P3_T0_STATE observes | **KEEP OPEN** |

Wire files (EXECUTED only): `live_config.py` · `live_path3_strategy_cutover.py` (new) · `e21_forward_pipeline.py` · optional weight-engine `require_flip=False` · tests.

## What this OPEN ballot does **not** do

- Does **not** flip any live flag today
- Does **not** authorize broker SendOrder
- Does **not** promote `FULL_SOFT_REPLACE` / Soft clip densify / CONF α change
- Does **not** close Path4 Soft-0050 track

## Evidence index

- Charter: `FIN_SAT_PATH3_STRATEGY_CUTOVER_STAGEA_CHARTER.md`
- Paper HIT: `FIN_SAT_PATH3_STRATEGY_CUTOVER_STAGEB_DECISION_PACK.md` (0kam)
- Pre-ACCEPT: `PATH3_STRATEGY_CUTOVER_PREACCEPT_DISPOSITION.md`
- Checklist: `CUTOVER_CHECKLIST_PATH3_STRATEGY.md`

Label: `PATH3_STRATEGY_CUTOVER_ACCEPT_BALLOT_OPEN_2026-09-30__AWAITING_HUMAN__NO_LIVE`
