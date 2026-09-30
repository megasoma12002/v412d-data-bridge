# Live T0_CARVE_FIN_SAT_SWITCH fill allowlist — PREP → EXECUTED (0ka7)

Date: 2026-09-29  
Status: **EXECUTED via 0ka7** · fill flag **ON** · Soft-Frozen Exact T+1 **KEEP** elsewhere · Path3 observe θ=**0.005** · no broker write

## Implemented

1. SSOT `scripts/t0_carve_fin_sat_switch.py` — tag + authorize helpers  
2. `LiveConfig.live_t0_carve_fin_sat_switch_fill = True` (**0ka7 ACCEPT**)  
3. `live_fill_core`: same-day pending + MOC `reference_close` only for tagged rows when flag True  
4. `e21_qc.exact_t1_from_fills`: exclude tagged same-bar when flag True  
5. Unit tests: `tests/test_t0_carve_fin_sat_switch.py`  
6. EXECUTED ballot: `FIN_SAT_PATH3_OBSERVE_THETA005_T0_LIVE_BALLOT_EXECUTED_ACCEPT.md`

## Not implemented (still BLOCKED)

- Path3 strategy cutover (0kac charter) · broker live-write  
- Expanding carve beyond `T0_CARVE_FIN_SAT_SWITCH`

Label: `LIVE_T0_CARVE_FIN_SAT_SWITCH_FILL_PREP_2026-09-29__EXECUTED_0ka7`
