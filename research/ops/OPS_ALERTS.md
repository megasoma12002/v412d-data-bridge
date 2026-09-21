# Ops Alerts

Generated: `2026-09-21T16:30:56.109894+00:00`
Overall: **HIGH**
Soft-Frozen **[0.60, 0.90] unchanged**. No auto cutover.

- CRITICAL: 0
- HIGH (PAUSE_REVIEW etc.): 7
- INFO: 27

| Severity | Source | Code | Message |
|---|---|---|---|
| HIGH | `l4_month_end` | `PAUSE_REVIEW` | PAUSE_REVIEW: ytd giveback > 5 pp — extend observation; does not revoke PASS_HELDOUT_L4 |
| HIGH | `l4_month_end` | `PAUSE_REVIEW` | PAUSE_REVIEW: trailing_1y giveback > 5 pp — extend observation; does not revoke PASS_HELDOUT_L4 |
| HIGH | `fincap50_month_end` | `PAUSE_REVIEW` | PAUSE_REVIEW: ytd giveback > 5 pp — extend observe; Soft-Frozen unchanged; no cutover talk |
| HIGH | `fincap50_month_end` | `PAUSE_REVIEW` | PAUSE_REVIEW: trailing_1y giveback > 5 pp — extend observe; Soft-Frozen unchanged; no cutover talk |
| HIGH | `blend025_month_end` | `PAUSE_REVIEW` | PAUSE_REVIEW: ytd giveback > 5 pp — extend observe; Soft-Frozen unchanged; no cutover talk |
| HIGH | `e45_month_end` | `PAUSE_REVIEW` | PAUSE_REVIEW: CHAL_E45_E3 ytd giveback > 5 pp |
| HIGH | `e45_month_end` | `PAUSE_REVIEW` | PAUSE_REVIEW: CHAL_E45_E3 trailing_1y giveback > 5 pp |
| INFO | `live_qc` | `QC_PASS` | live QC PASS; Exact T+1 ok |
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
| INFO | `live_paper_recon` | `RECON_NOTE` | INDEX_DRIFT: max \|live_idx-paper_idx\|=3.3350% > 2% on overlap |
| INFO | `live_paper_recon` | `THIN_LIVE_HISTORY` | overlap_n=18 (<60) — not decision-grade for cutover |
| INFO | `r4_settlement_estimate` | `R4_ESTIMATE_PRESENT` | R4 settlement_cash_estimate present — settled_cash_estimate=50415.51358572836 is liquidity view NOT portfolio NAV / Soft-Frozen cash |
| INFO | `data_source_phase_c_probes` | `PHASE_C_C1_FIN12_HISTORY_SHADOW_NOTE` | DRIFT on 1 ticker(s); does not count toward PASS |
| INFO | `data_source_phase_c_probes` | `PHASE_C_C3_TAIEX_OPTIONAL_FAILOVER_NOTE` | Helper is opt-in only; e21 still uses FinMind TaiwanStockPrice(TAIEX). |

## Routing

- CRITICAL → fail `e21-live-qc-smoke` / block live confidence
- HIGH → month-end pack annotates PAUSE; R4 missing; cutover checklists stay blocked
- INFO → tip lag / R4 present (liquidity ≠ NAV) / recorded only

Re-run: `python3 scripts/ops_alert_scan.py`
