# Path3 weight engine → ledger-scaled recon — Ballot EXECUTED (ACCEPT)

Date: 2026-09-29  
Status: **EXECUTED ACCEPT / LIVE WIRED** · Soft-Frozen Exact T+1 **KEEP** elsewhere · Soft 0050 **KEEP** · broker write **false** · strategy cutover **BLOCKED**

Register: **0kab** · Parents: Stage A `LEDGER_SSOT_BUILT` · 0ka9 weight-engine Stage B · 0ka7 emit/fill

## Human (exact)

```
ACCEPT Path3 weight engine: P3_COMP_SAT_DAILY_POS_LEDGER_A (ledger-scaled recon · Soft 0050 KEEP · cutover still BLOCKED)
```

## What changed

| Item | Before | After ACCEPT |
|---|---|---|
| `LIVE.live_path3_weight_engine_mode` | *(absent / Stage B default)* | **`ledger`** |
| `plan_or_none_for_pipeline` | Stage B `P3_COMP_SAT_ASOF_RECON_B` | **`P3_COMP_SAT_DAILY_POS_LEDGER_A`** ledger-scaled |
| Rollback mode | — | set mode to `asof_b` (Stage B overlays) |
| Soft 0050 / Soft-Frozen Exact T+1 | KEEP | **KEEP** |
| Path3 `-P3T0` emit/fill (0ka7) | ON | **ON** |
| Broker SendOrder / Path3 router cutover | BLOCKED | **BLOCKED** |

## Evidence (Stage A)

- Verdict **`LEDGER_SSOT_BUILT`** → live **`LEDGER_LIVE_WIRED`**
- COMP **27480** / SAT **29646** daily Soft share rows
- Flip demos vs Stage B: jaccard≈0.86 both directions
- Tests: `tests/test_path3_daily_share_ssot.py` · `tests/test_path3_t0_weight_engine.py`

## Non-actions

- Do not enable broker live-write from this ballot
- Do not authorize Path3 strategy cutover
- Do not flip Soft clips / CONF α / expand T+0 carve
- Do not delete Stage B asof recon (rollback via `asof_b`)

Label: `LIVE_PATH3_WEIGHT_ENGINE_LEDGER_BALLOT_EXECUTED_2026-09-29__ACCEPT__LEDGER__NO_BROKER`
