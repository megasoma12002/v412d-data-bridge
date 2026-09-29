# Live Path3 switch emitter — Ballot DRAFT

Date: 2026-09-29  
Status: **DRAFT — NOT AUTHORIZED** · Soft-Frozen Exact T+1 **KEEP** · Path3 observe **KEEP** · cutover **BLOCKED** · live wire **false** until ACCEPT  
Parents: 0k9r Path3 observe · 0k9u fill allowlist PREP · 0k9v fill-sim `FILL_CARVE_CLOSE_ONLY` (draft PR)

## Purpose

Fill allowlist (0k9u) only helps if Path3 emits **tagged** switch orders.  
This ballot enables the **named emitter** already wired (default OFF).

## What flips on ACCEPT

| Item | Before | After ACCEPT |
|---|---|---|
| `LIVE.live_t0_carve_fin_sat_switch_emit` | `False` | `True` |
| Pipeline Path3 hook | no-op | calls `maybe_emit_switch_orders` |
| Tagged orders without `delta_shares` | — | still **empty** (`weight_engine_not_wired`) until Stage-B engines |
| Soft-Frozen sleeve fills | Exact T+1 | **Exact T+1 KEEP** |
| Fill same-bar allowlist | separate flag (0k9u) | **unchanged** by this ballot |

## Exact ACCEPT line

```
ACCEPT Live Path3 switch emitter: T0_CARVE_FIN_SAT_SWITCH tagged orders (P3_T0_STATE · Soft-Frozen Exact T+1 KEEP elsewhere · cutover still BLOCKED)
```

## Non-actions

- Do not invent COMP↔SAT share deltas from Soft-Frozen alone  
- Do not flip fill flag / Soft-Frozen clips / CONF α from this ballot  
- Do not broker SendOrder · cutover still BLOCKED  

## Code PREP

- `scripts/live_path3_t0_switch_emitter.py`  
- `live_config.live_t0_carve_fin_sat_switch_emit=False`  
- `e21_forward_pipeline` gated hook  
- Tests: `tests/test_path3_t0_switch_emitter.py`  
- Prep note: `LIVE_PATH3_T0_SWITCH_EMITTER_PREP.md`

Label: `LIVE_PATH3_T0_SWITCH_EMITTER_BALLOT_DRAFT_2026-09-29__AWAITING_HUMAN`
