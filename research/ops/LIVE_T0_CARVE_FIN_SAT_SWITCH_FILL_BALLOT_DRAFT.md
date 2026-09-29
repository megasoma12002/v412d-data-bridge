# Live fill carve-out — Ballot DRAFT (T0_CARVE_FIN_SAT_SWITCH same-bar)

Date: 2026-09-29  
Status: **DRAFT — NOT AUTHORIZED** · Soft-Frozen Exact T+1 **KEEP** elsewhere · Path3 observe **KEEP** · live wire **false** until ACCEPT  
Parents: 0k9r policy carve OPEN · 0k9s `T0_SAMEBAR_ONLY` · 0k9t `ORACLE_ONLY` · fill impl PREP

## Purpose

Policy carve-out already ACCEPTed for paper observe.  
0k9t shows hybrid/MOC tip−; tip needs **same-bar fill**.  
This ballot enables the **named live fill allowlist** already wired (default OFF).

## What flips on ACCEPT

| Item | Before | After ACCEPT |
|---|---|---|
| `LIVE.live_t0_carve_fin_sat_switch_fill` | `False` | `True` |
| Tagged Path3 switch orders (`carve_out_id=T0_CARVE_FIN_SAT_SWITCH`) | Exact T+1 only | same-bar MOC (`reference_close`) allowed |
| Untagged Soft-Frozen / sleeve / FUSE fills | Exact T+1 | **Exact T+1 KEEP** |
| Path3 live router / COMP↔SAT book wiring | not live | still **not** auto-wired — needs separate orders path |

## Exact ACCEPT line

```
ACCEPT Live fill carve-out: T0_CARVE_FIN_SAT_SWITCH same-bar (Path3 P3_T0_STATE only · Soft-Frozen Exact T+1 KEEP elsewhere)
```

## Non-actions

- Do not expand carve-out to other mechanisms  
- Do not flip Soft-Frozen clips / CONF α  
- Do not broker SendOrder from this ballot alone  
- Cutover of Path3 **strategy** still BLOCKED until dedicated router ACCEPT

## Code PREP (already on branch)

- `scripts/t0_carve_fin_sat_switch.py`  
- `live_config.live_t0_carve_fin_sat_switch_fill=False`  
- `live_fill_core` / `e21_qc` allowlist hooks  
- Tests: `tests/test_t0_carve_fin_sat_switch.py`

Label: `LIVE_T0_CARVE_FIN_SAT_SWITCH_FILL_BALLOT_DRAFT_2026-09-29__AWAITING_HUMAN`
