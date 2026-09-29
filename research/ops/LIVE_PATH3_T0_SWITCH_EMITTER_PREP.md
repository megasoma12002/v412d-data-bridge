# Live Path3 T0 switch emitter — PREP OPERATING

Date: 2026-09-29  
Status: **EXECUTED via 0ka7** · emit flag **ON** · Soft-Frozen Exact T+1 **KEEP** · Path3 observe θ=**0.005** · cutover **BLOCKED** · no broker write

## Implemented

1. SSOT `scripts/live_path3_t0_switch_emitter.py`
   - SAT_LEAD / flip meta (≡ `P3_T0_STATE` observe rule)
   - `build_tagged_switch_order_rows` → `carve_out_id=T0_CARVE_FIN_SAT_SWITCH` + `-P3T0` order_id
   - `maybe_emit_switch_orders` fail-closed without explicit `delta_shares`
   - Shadow propose ledger (`path3_t0_proposed_switches.csv`)
2. `LiveConfig.live_t0_carve_fin_sat_switch_emit = False`
3. `e21_forward_pipeline` hook gated OFF (when ON still fail-closes: weight engine not wired)
4. Unit tests: `tests/test_path3_t0_switch_emitter.py`
5. DRAFT ballot: `LIVE_PATH3_T0_SWITCH_EMITTER_BALLOT_DRAFT.md`

## Shadow propose (this PREP run)

- Signal days: 3365 · proposed flips: **153** · %days SAT **24.16**
- Repro: `repro/fin-sat-path3-t0-emitter-prep/`

## Weight engine (0ka8 Stage A → 0ka9 Stage B)

- Stage A named proxy `P3_SOFT_SLEEVE_EQ_RECON_PROXY` (`plan_sat_equal_recon` helper kept)
- Stage B engine `P3_COMP_SAT_ASOF_RECON_B` wired into e21 (`plan_or_none_for_pipeline`)
- COMP→SAT: SAT RELAX KD · SAT→COMP: OR_K9×HARD150 · both-direction `-P3T0`
- Soft-Frozen coexistence mute → **0kaa Stage A `MUTE_WIRED_DEMO_OK`** · live flag **OFF** · DRAFT ballot `LIVE_SOFT_PATH3_COEXIST_MUTE_BALLOT_DRAFT.md`

## Not implemented (still BLOCKED)

- Soft-Frozen flip-day coexistence mute **live flag ON** (needs ACCEPT of DRAFT ballot)
- Flipping emit/fill already ON (0ka7); broker live-write / Path3 strategy cutover still BLOCKED
- Cloning paper share ledgers (no daily pos SSOT)

## Accept to enable emit flag

```
ACCEPT Live Path3 switch emitter: T0_CARVE_FIN_SAT_SWITCH tagged orders (P3_T0_STATE · Soft-Frozen Exact T+1 KEEP elsewhere · cutover still BLOCKED)
```

Label: `LIVE_PATH3_T0_SWITCH_EMITTER_PREP_2026-09-29__FLAG_OFF__NO_LIVE`
