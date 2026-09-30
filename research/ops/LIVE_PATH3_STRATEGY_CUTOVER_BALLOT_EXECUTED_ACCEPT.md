# Path3 strategy cutover — Ballot EXECUTED (ACCEPT)

Date: 2026-09-30  
Status: **EXECUTED ACCEPT / LIVE WIRED** · Soft clips+0050 Exact T+1 **KEEP** · Soft FIN/TEL Exact T+1 **OFF** · Path3 ledger **daily** · T0 carve **KEEP** · broker **false** · overlays **KEEP**

Register: **0kac** · Parents: Stage A `CUTOVER_SCOPE_DEFINED` · Stage B **0kam** `PAPER_WITHIN_HIT` · pre-ACCEPT disposition

## Human (exact)

```
ACCEPT Path3 strategy cutover: WITHIN_SLEEVE_PATH3
(Soft clips+0050 Exact T+1 KEEP · Soft FIN/TEL Exact T+1 OFF · Path3 ledger daily ·
 T0_CARVE_FIN_SAT_SWITCH KEEP · broker false · overlays KEEP)
```

## What changed

| Item | Before | After ACCEPT |
|---|---|---|
| `LIVE.live_path3_strategy_cutover` | False / absent | **True** |
| `LIVE.live_path3_strategy_cutover_scope` | — | **`WITHIN_SLEEVE_PATH3`** |
| Soft Exact T+1 FIN∪TEL | daily Soft (mute only on flip) | **OFF daily** |
| Soft Exact T+1 0050 / Soft clips | KEEP | **KEEP** |
| Path3 ledger recon | flip only | **daily** toward active COMP/SAT book |
| Path3 `-P3T0` emit/fill | ON (flip) | **ON** (flip **or** daily cutover deltas) |
| Flip mute `MUTE_SOFT_FIN_TEL` | ON | **superseded-when-ON** (flag kept) |
| T+0 carve `T0_CARVE_FIN_SAT_SWITCH` | ON | **KEEP** |
| Broker `broker_live_write_accepted` | false | **false** |
| COOL / FUSE / CONF_RET3 / FinPriv | KEEP | **KEEP** |
| COMPOSITE / SAT_RELAX / P3_T0_STATE observes | OPEN | **KEEP OPEN** |

## Wire

- `scripts/live_config.py` — cutover flag/scope/ballot
- `scripts/live_path3_strategy_cutover.py` — Soft FIN/TEL suppress + daily recon gate
- `scripts/live_path3_t0_weight_engine.py` — ledger without flip when cutover ON
- `scripts/live_path3_t0_switch_emitter.py` — emit without flip when cutover ON
- `scripts/e21_forward_pipeline.py` — suppress Soft FIN/TEL; mute superseded; signal fields
- Tests: `tests/test_path3_strategy_cutover.py` (+ weight-engine status-quo mock)

## Evidence

- Stage B paper **`PAPER_WITHIN_HIT`**: WITHIN−FLIP held **+3.04** · tipY **+0.27** · sealed MDD **+7.24** · yearly **14–1**
- Pre-ACCEPT disposition: sealed/wrong-stay/2022/overlay-design cited

## Non-actions

- Do not enable broker live-write from this ballot
- Do not promote `FULL_SOFT_REPLACE` / Soft clip densify / CONF α change
- Do not expand T+0 carve beyond `T0_CARVE_FIN_SAT_SWITCH`
- Do not close COMPOSITE / SAT_RELAX / P3_T0_STATE observes
- Path4 Soft-0050 remains separate (`KEEP_STAGEA_RENORM`)

Supersedes OPEN: `PATH3_STRATEGY_CUTOVER_ACCEPT_BALLOT_OPEN.md`

Label: `LIVE_PATH3_STRATEGY_CUTOVER_BALLOT_EXECUTED_2026-09-30__ACCEPT__WITHIN_SLEEVE_PATH3__NO_BROKER`
