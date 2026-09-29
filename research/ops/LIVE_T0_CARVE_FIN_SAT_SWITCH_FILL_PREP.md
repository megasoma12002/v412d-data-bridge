# Live T0_CARVE_FIN_SAT_SWITCH fill allowlist — PREP OPERATING

Date: 2026-09-29  
Status: **PREP / flag OFF** · Soft-Frozen Exact T+1 **KEEP** · Path3 observe **KEEP** · no live Path3 router · no broker write

## Implemented

1. SSOT `scripts/t0_carve_fin_sat_switch.py` — tag + authorize helpers  
2. `LiveConfig.live_t0_carve_fin_sat_switch_fill = False` (fail-closed default)  
3. `live_fill_core`: same-day pending + MOC `reference_close` only for tagged rows when flag True  
4. `e21_qc.exact_t1_from_fills`: exclude tagged same-bar when flag True  
5. Unit tests enforce default OFF + tagged allowlist behavior  
6. DRAFT ballot: `LIVE_T0_CARVE_FIN_SAT_SWITCH_FILL_BALLOT_DRAFT.md`

## Not implemented (still BLOCKED)

- Path3 COMP↔SAT live order emitter / router  
- Flipping the live flag (needs human ACCEPT line)  
- Broker live-write

## Accept to enable flag

```
ACCEPT Live fill carve-out: T0_CARVE_FIN_SAT_SWITCH same-bar (Path3 P3_T0_STATE only · Soft-Frozen Exact T+1 KEEP elsewhere)
```

Label: `LIVE_T0_CARVE_FIN_SAT_SWITCH_FILL_PREP_2026-09-29__FLAG_OFF__NO_LIVE`
