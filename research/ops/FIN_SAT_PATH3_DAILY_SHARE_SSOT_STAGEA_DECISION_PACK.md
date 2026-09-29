# FIN_SAT_PATH3_DAILY_SHARE_SSOT_STAGEA_DECISION_PACK

Date: 2026-09-29 · Verdict: **`LEDGER_SSOT_BUILT`** → live **`LEDGER_LIVE_WIRED`**
Status: Soft-Frozen **KEEP** · broker **false** · cutover **BLOCKED** · ledger engine **LIVE WIRED** (`mode=ledger`)
Register: **0kab** · Engine: `P3_COMP_SAT_DAILY_POS_LEDGER_A` · Parent: 0ka9

## Answer

COMP ledger: **27480** rows · SAT ledger: **29646** rows.
Flip demos: COMP→SAT ledgerΔ=7 vs BΔ=6 (jaccard=0.8571) · SAT→COMP ledgerΔ=7 vs BΔ=6 (jaccard=0.8571).

## Implication

- `LEDGER_SSOT_BUILT`：日股數 SSOT 落地 · ledger-scaled recon API 可用
- **ACCEPT executed:** `plan_or_none_for_pipeline` → ledger (`LIVE_PATH3_WEIGHT_ENGINE_LEDGER_BALLOT_EXECUTED_ACCEPT.md`)
- Rollback: set `live_path3_weight_engine_mode=asof_b`
- CONF α A10/A20 仍正交 · 另票

Screen: `FIN_SAT_PATH3_DAILY_SHARE_SSOT_STAGEA_SCREEN.md` · Charter: `FIN_SAT_PATH3_DAILY_SHARE_SSOT_STAGEA_CHARTER.md`

Label: `FIN_SAT_PATH3_DAILY_SHARE_SSOT_STAGEA_DECISION_PACK_2026-09-29__LEDGER_SSOT_BUILT__NO_BROKER`
