# FIN_SAT_PATH3_DAILY_SHARE_SSOT_STAGEA_CHARTER

Date: 2026-09-29
Status: **Stage A — Path3 COMP/SAT daily share SSOT** · Soft-Frozen **KEEP** · broker **false** · cutover **BLOCKED** · no live wire of ledger engine
Parents: 0ka9 `P3_COMP_SAT_ASOF_RECON_B` · COMPOSITE/SAT_A20 dual-paper observe
Register: **0kab**

## Question

Can we build path-dependent daily Soft share ledgers for `COMP_H150_x_A20` and `SAT_A20_RELAX` and plan flip deltas by **ledger-scaled recon** (freeze live Soft sleeve $ × paper within-sleeve mix), closing the Stage B asof-recon fidelity gap without broker/cutover/α flip?

## Method

- Engine `P3_COMP_SAT_DAILY_POS_LEDGER_A`
- Hook `simulate_core(..., daily_pos_sink=...)` → long `date,code,shares`
- COMP: OR_K9×HARD150 · SAT: RELAX (base pre-ex) · densify α=0.20 schedule
- Flip plan: `plan_delta_shares_ledger` · Soft 0050 KEEP
- Compare to Stage B asof recon on last COMP→SAT / SAT→COMP flips (live e21 pos)

## Non-goals

- Absolute paper share clone onto live NAV (scale mismatch)
- CONF α A10↔A20 align · broker · Path3 cutover · Soft clip flip
- Replacing live `plan_or_none_for_pipeline` (Stage B of this track)

Label: `FIN_SAT_PATH3_DAILY_SHARE_SSOT_STAGEA_CHARTER_2026-09-29__DAILY_POS_LEDGER__NO_BROKER`
