# Live Path3 T0 switch emitter — PREP → EXECUTED (0ka7+)

Date: 2026-09-29  
Status: **EXECUTED via 0ka7** · emit flag **ON** · Soft-Frozen Exact T+1 **KEEP** · Path3 observe θ=**0.005** · weight **ledger (0kab)** · mute **ON (0kaa)** · cutover **BLOCKED** · no broker write

## Implemented

1. SSOT `scripts/live_path3_t0_switch_emitter.py`
   - SAT_LEAD / flip meta (≡ `P3_T0_STATE` observe rule)
   - `build_tagged_switch_order_rows` → `carve_out_id=T0_CARVE_FIN_SAT_SWITCH` + `-P3T0` order_id
   - `maybe_emit_switch_orders` fail-closed without explicit `delta_shares`
   - Shadow propose ledger (`path3_t0_proposed_switches.csv`)
2. `LiveConfig.live_t0_carve_fin_sat_switch_emit = True` (**0ka7 ACCEPT**)
3. `e21_forward_pipeline` hook ON · weight via `plan_or_none_for_pipeline` (**0kab ledger**) · Soft mute (**0kaa**)
4. Unit tests: `tests/test_path3_t0_switch_emitter.py` · `tests/test_path3_t0_weight_engine.py` · `tests/test_soft_path3_coexist_mute.py`
5. EXECUTED ballot parents: `FIN_SAT_PATH3_OBSERVE_THETA005_T0_LIVE_BALLOT_EXECUTED_ACCEPT.md`

## Shadow propose (original PREP run)

- Signal days: 3365 · proposed flips: **153** · %days SAT **24.16**
- Repro: `repro/fin-sat-path3-t0-emitter-prep/`

## Weight engine (0ka8 → 0ka9 → 0kab LIVE WIRED)

- Stage A named proxy `P3_SOFT_SLEEVE_EQ_RECON_PROXY` (`plan_sat_equal_recon` helper kept)
- Stage B engine `P3_COMP_SAT_ASOF_RECON_B` retained as rollback mode `asof_b`
- **ACCEPT 0kab:** `live_path3_weight_engine_mode=ledger` → `P3_COMP_SAT_DAILY_POS_LEDGER_A` via `plan_or_none_for_pipeline`
- Soft 0050 KEEP · Soft-Frozen Exact T+1 KEEP · broker false · cutover BLOCKED
- Ballot: `LIVE_PATH3_WEIGHT_ENGINE_LEDGER_BALLOT_EXECUTED_ACCEPT.md`
- Soft↔Path3 coexistence mute → **0kaa EXECUTED ACCEPT / LIVE WIRED** · `live_soft_path3_coexist_mute=True` · `LIVE_SOFT_PATH3_COEXIST_MUTE_BALLOT_EXECUTED_ACCEPT.md`

## Not implemented (still BLOCKED)

- Path3 strategy cutover (`PATH3_STRATEGY_CUTOVER` / 0kac CHARTER) — Soft still primary daily; flip carve only
- Broker live-write still BLOCKED
- Daily share ledger refresh past tip (see `PROJECT_CODE_REVIEW_2026-09-29.md` P1 stale)

Label: `LIVE_PATH3_T0_SWITCH_EMITTER_PREP_2026-09-29__EXECUTED_0ka7__LEDGER_0kab`
