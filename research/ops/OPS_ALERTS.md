# Ops Alerts

Generated: `2026-09-28T04:28:13.826027+00:00`
Overall: **HIGH**
Soft-Frozen **[0.60, 0.80] unchanged**. No auto cutover.

- CRITICAL: 0
- HIGH (PAUSE_REVIEW etc.): 13
- INFO: 45

| Severity | Source | Code | Message |
|---|---|---|---|
| HIGH | `l4_month_end` | `PAUSE_REVIEW` | PAUSE_REVIEW: ytd giveback > 5 pp — extend observation; does not revoke PASS_HELDOUT_L4 |
| HIGH | `l4_month_end` | `PAUSE_REVIEW` | PAUSE_REVIEW: trailing_1y giveback > 5 pp — extend observation; does not revoke PASS_HELDOUT_L4 |
| HIGH | `fincap50_month_end` | `PAUSE_REVIEW` | PAUSE_REVIEW: ytd giveback > 5 pp — extend observe; Soft-Frozen unchanged; no cutover talk |
| HIGH | `fincap50_month_end` | `PAUSE_REVIEW` | PAUSE_REVIEW: trailing_1y giveback > 5 pp — extend observe; Soft-Frozen unchanged; no cutover talk |
| HIGH | `blend025_month_end` | `PAUSE_REVIEW` | PAUSE_REVIEW: ytd giveback > 5 pp — extend observe; Soft-Frozen unchanged; no cutover talk |
| HIGH | `e45_month_end` | `PAUSE_REVIEW` | PAUSE_REVIEW: CHAL_E45_E3 ytd giveback > 5 pp |
| HIGH | `e45_month_end` | `PAUSE_REVIEW` | PAUSE_REVIEW: CHAL_E45_E3 trailing_1y giveback > 5 pp |
| HIGH | `fin_buy_quality_month_end` | `PAUSE_REVIEW` | PAUSE_REVIEW: A_SEED_MA120 ytd giveback > 5 pp |
| HIGH | `fin_buy_quality_month_end` | `PAUSE_REVIEW` | PAUSE_REVIEW: A_SEED_MA120 trailing_1y giveback > 5 pp |
| HIGH | `fin_buy_quality_month_end` | `PAUSE_REVIEW` | PAUSE_REVIEW: B_MA120_OR_K9 ytd giveback > 5 pp |
| HIGH | `fin_buy_quality_month_end` | `PAUSE_REVIEW` | PAUSE_REVIEW: B_MA120_OR_K9 trailing_1y giveback > 5 pp |
| HIGH | `fin_buy_quality_month_end` | `PAUSE_REVIEW` | PAUSE_REVIEW: C_OR_K9_AND_BELOW_MA60 ytd giveback > 5 pp |
| HIGH | `fin_buy_quality_month_end` | `PAUSE_REVIEW` | PAUSE_REVIEW: C_OR_K9_AND_BELOW_MA60 trailing_1y giveback > 5 pp |
| INFO | `live_qc` | `QC_PASS` | live QC PASS; Exact T+1 ok |
| INFO | `fin_priv_v7_f05` | `FINPRIV_PX_FRESH` | Class D priv panel fresh vs tip asof 2026-09-24 (lag≤5d) |
| INFO | `l4_month_end` | `MONITOR_ALERT` | ALERT: L4_DD_PATH_08_50 sealed MDD worse than BASE (paper) |
| INFO | `l4_month_end` | `MONITOR_ALERT` | ALERT: L4_DD_PATH_08_50 ytd CAGR giveback > 3.0 pp (paper ops) |
| INFO | `l4_month_end` | `MONITOR_ALERT` | ALERT: L4_DD_PATH_08_50 trailing_1y CAGR giveback > 3.0 pp (paper ops) |
| INFO | `l4_month_end` | `CUTOVER_BLOCKED_FLAG` | cutover_blocked=true (expected while Soft-Frozen KEEP) |
| INFO | `fincap50_month_end` | `MONITOR_ALERT` | ALERT: FIN_CAP_50 heldout_2019_plus MDD worse than BASE (paper) |
| INFO | `fincap50_month_end` | `MONITOR_ALERT` | ALERT: FIN_CAP_50 ytd CAGR giveback > 3.0 pp (paper) |
| INFO | `fincap50_month_end` | `MONITOR_ALERT` | ALERT: FIN_CAP_50 trailing_1y CAGR giveback > 3.0 pp (paper) |
| INFO | `fincap50_month_end` | `CUTOVER_BLOCKED_FLAG` | cutover_blocked=true (expected while Soft-Frozen KEEP) |
| INFO | `blend025_month_end` | `MONITOR_ALERT` | ALERT: BLEND_025 sealed_2023_plus MDD worse than BASE (paper) |
| INFO | `blend025_month_end` | `MONITOR_ALERT` | ALERT: BLEND_025 ytd CAGR giveback > 3.0 pp (paper) |
| INFO | `blend025_month_end` | `MONITOR_ALERT` | ALERT: BLEND_025 trailing_1y CAGR giveback > 3.0 pp (paper) |
| INFO | `blend025_month_end` | `CUTOVER_BLOCKED_FLAG` | cutover_blocked=true (expected while Soft-Frozen KEEP) |
| INFO | `e45_month_end` | `MONITOR_ALERT` | ALERT: CHAL_E45_E3 ytd MDD worse than BASE_E16_E18_E22_v2s |
| INFO | `e45_month_end` | `MONITOR_ALERT` | ALERT: CHAL_E45_E3 ytd CAGR giveback > 3.0 pp |
| INFO | `e45_month_end` | `MONITOR_ALERT` | ALERT: CHAL_E45_E3 trailing_1y MDD worse than BASE_E16_E18_E22_v2s |
| INFO | `e45_month_end` | `MONITOR_ALERT` | ALERT: CHAL_E45_E3 trailing_1y CAGR giveback > 3.0 pp |
| INFO | `e45_month_end` | `CUTOVER_BLOCKED_FLAG` | cutover_blocked=true (expected while Soft-Frozen KEEP) |
| INFO | `soft_assist_month_end` | `CUTOVER_BLOCKED_FLAG` | cutover_blocked=true (expected while Soft-Frozen KEEP) |
| INFO | `sleeve_tilt_month_end` | `CUTOVER_BLOCKED_FLAG` | cutover_blocked=true (expected while Soft-Frozen KEEP) |
| INFO | `fuse_additive_month_end` | `CUTOVER_BLOCKED_FLAG` | cutover_blocked=true (expected while Soft-Frozen KEEP) |
| INFO | `e45_defend_handoff_month_end` | `CUTOVER_BLOCKED_FLAG` | cutover_blocked=true (expected while Soft-Frozen KEEP) |
| INFO | `cool_c8_proxy_month_end` | `CUTOVER_BLOCKED_FLAG` | cutover_blocked=true (expected while Soft-Frozen KEEP) |
| INFO | `beta_0050_densify_month_end` | `MONITOR_ALERT` | ALERT: BETA_F0.60-0.80_T0.03-0.35_E0.00-0.50 heldout_2019_plus MDD worse than LIVE_FUSE_COOL |
| INFO | `beta_0050_densify_month_end` | `CUTOVER_BLOCKED_FLAG` | cutover_blocked=true (expected while Soft-Frozen KEEP) |
| INFO | `priv_finhc_v7_bull_side_f05_month_end` | `MONITOR_ALERT` | ALERT: V7_REG_BULL_SIDE_F05_KDMAY heldout_2019_plus MDD worse than BASE_LIVE_FUSE_COOL |
| INFO | `priv_finhc_v7_bull_side_f05_month_end` | `CUTOVER_BLOCKED_FLAG` | cutover_blocked=true (expected while Soft-Frozen KEEP) |
| INFO | `cool_631l_short_assist_month_end` | `MONITOR_ALERT` | ALERT: CONF_RET3_A10_H5 heldout_2019_plus MDD worse than BASE_LIVE_FUSE_COOL |
| INFO | `cool_631l_short_assist_month_end` | `CUTOVER_BLOCKED_FLAG` | cutover_blocked=true (expected while Soft-Frozen KEEP) |
| INFO | `fin_buy_quality_month_end` | `MONITOR_ALERT` | ALERT: A_SEED_MA120 ytd CAGR giveback > 3.0 pp |
| INFO | `fin_buy_quality_month_end` | `MONITOR_ALERT` | ALERT: A_SEED_MA120 trailing_1y CAGR giveback > 3.0 pp |
| INFO | `fin_buy_quality_month_end` | `MONITOR_ALERT` | ALERT: B_MA120_OR_K9 ytd CAGR giveback > 3.0 pp |
| INFO | `fin_buy_quality_month_end` | `MONITOR_ALERT` | ALERT: B_MA120_OR_K9 trailing_1y CAGR giveback > 3.0 pp |
| INFO | `fin_buy_quality_month_end` | `MONITOR_ALERT` | ALERT: C_OR_K9_AND_BELOW_MA60 ytd CAGR giveback > 3.0 pp |
| INFO | `fin_buy_quality_month_end` | `MONITOR_ALERT` | ALERT: C_OR_K9_AND_BELOW_MA60 trailing_1y CAGR giveback > 3.0 pp |
| INFO | `fin_buy_quality_month_end` | `MONITOR_ALERT` | ALERT: C_OR_K9_AND_BELOW_MA60 sealed_2023_plus MDD worse than BASE_LIVE_FUSE_COOL |
| INFO | `fin_buy_quality_month_end` | `CUTOVER_BLOCKED_FLAG` | cutover_blocked=true (expected while Soft-Frozen KEEP) |
| INFO | `live_paper_recon` | `RECON_NOTE` | INDEX_DRIFT: max \|live_idx-paper_idx\|=3.3350% > 2% on overlap |
| INFO | `live_paper_recon` | `THIN_LIVE_HISTORY` | overlap_n=18 (<60) — not decision-grade for cutover |
| INFO | `r4_settlement_estimate` | `R4_ESTIMATE_PRESENT` | R4 settlement_cash_estimate present — settled_cash_estimate=50415.51358572836 is liquidity view NOT portfolio NAV / Soft-Frozen cash |
| INFO | `r5_broker_reconcile` | `R5_RECONCILE_OK` | R5 observe pack fixtures/r5_reconcile_observe/t2_broker_reconcile_latest.json all_ok=True — T+2 custody vs estimate (NOT NAV); broker live-write still PREP / EXECUTE blocked |
| INFO | `broker_prep_gates` | `BROKER_PREP_GATES_CLOSED` | broker live-write PREP: fill_port=paper · broker_live_write_accepted=False · API_WIRED=False · SendStockOrder/SendAlgo blocked |
| INFO | `data_source_phase_c_probes` | `PHASE_C_C1_FIN12_HISTORY_SHADOW_NOTE` | DRIFT on 1 ticker(s); does not count toward PASS |
| INFO | `data_source_phase_c_probes` | `PHASE_C_C3_TAIEX_OPTIONAL_FAILOVER_NOTE` | Helper is opt-in only; e21 still uses FinMind TaiwanStockPrice(TAIEX). |

## Routing

- CRITICAL → fail `e21-live-qc-smoke` / block live confidence
- HIGH → month-end pack annotates PAUSE; R4 missing; cutover checklists stay blocked
- INFO → tip lag / R4 present (liquidity ≠ NAV) / recorded only

Re-run: `python3 scripts/ops_alert_scan.py`
