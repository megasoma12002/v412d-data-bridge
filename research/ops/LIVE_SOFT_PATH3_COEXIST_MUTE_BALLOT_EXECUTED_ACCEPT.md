# Soft↔Path3 coexist mute — Ballot EXECUTED (ACCEPT)

Date: 2026-09-29  
Status: **EXECUTED ACCEPT** · Soft-Frozen clips / Exact T+1 **KEEP** elsewhere · mute flag **ON** · Path3 emit/fill/engine B **ON** · broker write **false** · strategy cutover **BLOCKED**

Register: **0kaa** · Parents: Stage A `MUTE_WIRED_DEMO_OK` · 0ka9 weight-engine Stage B · 0ka7 emit/fill

## Human (exact)

```
ACCEPT Soft↔Path3 coexist mute: MUTE_SOFT_FIN_TEL (flip-day Soft FIN/TEL Exact T+1 muted · Soft 0050 KEEP · Path3 -P3T0 KEEP · cutover still BLOCKED)
```

## What changed

| Item | Before | After ACCEPT |
|---|---|---|
| `LIVE.live_soft_path3_coexist_mute` | False | **True** |
| Policy | `MUTE_SOFT_FIN_TEL` | **`MUTE_SOFT_FIN_TEL`** (unchanged) |
| Flip-day Soft FIN∪TEL Exact T+1 | coexist with `-P3T0` | **muted** when Path3 hit |
| Soft 0050 Exact T+1 | KEEP | **KEEP** |
| Path3 `-P3T0` / COOL / FUSE / CONF_RET3 | KEEP | **KEEP** |
| Soft-Frozen clips / CONF α | KEEP | **KEEP** |
| Broker SendOrder / Path3 router cutover | BLOCKED | **BLOCKED** |

## Evidence (Stage A)

- Verdict **`MUTE_WIRED_DEMO_OK`** → live **`MUTE_LIVE_WIRED_OK`**
- COMP→SAT / SAT→COMP: Soft FIN/TEL muted **7** · Path3 **6** `-P3T0` · Soft 0050 + satellite KEEP
- no-flip Soft intact (n_muted=0)
- Tests: `tests/test_soft_path3_coexist_mute.py`

## Non-actions

- Do not enable broker live-write from this ballot
- Do not authorize Path3 strategy cutover
- Do not flip Soft clips / CONF α / expand T+0 carve

Supersedes DRAFT: `LIVE_SOFT_PATH3_COEXIST_MUTE_BALLOT_DRAFT.md`

Label: `LIVE_SOFT_PATH3_COEXIST_MUTE_BALLOT_EXECUTED_2026-09-29__ACCEPT__MUTE_SOFT_FIN_TEL__NO_BROKER`
