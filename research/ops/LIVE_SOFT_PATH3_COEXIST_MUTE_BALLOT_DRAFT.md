# LIVE_SOFT_PATH3_COEXIST_MUTE_BALLOT_DRAFT

Date: 2026-09-29
Status: **DRAFT** · awaiting human ACCEPT · Stage A verdict **`MUTE_WIRED_DEMO_OK`**
Soft-Frozen clips / Exact T+1 KEEP elsewhere · broker false · cutover BLOCKED

## Proposed ACCEPT line

```
ACCEPT Soft↔Path3 coexist mute: MUTE_SOFT_FIN_TEL (flip-day Soft FIN/TEL Exact T+1 muted · Soft 0050 KEEP · Path3 -P3T0 KEEP · cutover still BLOCKED)
```

## Effect if ACCEPT

- Flip `live_soft_path3_coexist_mute=True` in `live_config.py`
- Policy `MUTE_SOFT_FIN_TEL`: Path3 flip+hit → mute Soft FIN∪TEL Exact T+1
- Soft 0050 Exact T+1 KEEP · Path3 `-P3T0` KEEP · COOL/FUSE/CONF_RET3 KEEP
- Does **not** authorize broker write or Path3 strategy cutover

Parent decision: `FIN_SAT_SOFT_PATH3_COEXIST_MUTE_STAGEA_DECISION_PACK.md`

Label: `LIVE_SOFT_PATH3_COEXIST_MUTE_BALLOT_DRAFT_2026-09-29__DRAFT__FLAG_OFF`
