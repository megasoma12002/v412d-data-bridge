# Ops Alerts

Generated: `2026-09-08T00:52:57.181407+00:00`
Overall: **HIGH**
Soft-Frozen **[0.50, 0.95] unchanged**. No auto cutover.

- CRITICAL: 0
- HIGH (PAUSE_REVIEW etc.): 6
- INFO: 16

| Severity | Source | Code | Message |
|---|---|---|---|
| HIGH | `fincap50_month_end` | `PAUSE_REVIEW` | PAUSE_REVIEW: ytd giveback > 5 pp — do not advance cutover discussion (aligns with FIN_CAP_50_GO_LIVE_VERIFY Gate E) |
| HIGH | `fincap50_month_end` | `PAUSE_REVIEW` | PAUSE_REVIEW: trailing_1y giveback > 5 pp — do not advance cutover discussion (aligns with FIN_CAP_50_GO_LIVE_VERIFY Gate E) |
| HIGH | `e45_month_end` | `PAUSE_REVIEW` | PAUSE_REVIEW: ytd giveback > 5 pp — extend observe; Soft-Frozen unchanged; no stitch talk |
| HIGH | `e45_month_end` | `PAUSE_REVIEW` | PAUSE_REVIEW: trailing_1y giveback > 5 pp — extend observe; Soft-Frozen unchanged; no stitch talk |
| HIGH | `e45_blend025_month_end` | `PAUSE_REVIEW` | PAUSE_REVIEW: ytd giveback > 5 pp — extend observe; Soft-Frozen unchanged; no stitch talk |
| HIGH | `e45_blend025_month_end` | `PAUSE_REVIEW` | PAUSE_REVIEW: trailing_1y giveback > 5 pp — extend observe; Soft-Frozen unchanged; no stitch talk |
| INFO | `live_qc` | `QC_PASS` | live QC PASS; Exact T+1 ok |
| INFO | `l4_month_end` | `MONITOR_ALERT` | ALERT: L4_DD_PATH_08_50 sealed MDD worse than BASE (paper) |
| INFO | `fincap50_month_end` | `MONITOR_ALERT` | ALERT: FIN_CAP_50 ytd CAGR giveback > 3.0 pp (paper) |
| INFO | `fincap50_month_end` | `MONITOR_ALERT` | ALERT: FIN_CAP_50 trailing_1y CAGR giveback > 3.0 pp (paper) |
| INFO | `fincap50_month_end` | `CUTOVER_BLOCKED_FLAG` | cutover_blocked=true (expected while Soft-Frozen KEEP) |
| INFO | `blend025_month_end` | `CUTOVER_BLOCKED_FLAG` | cutover_blocked=true (expected while Soft-Frozen KEEP) |
| INFO | `e45_month_end` | `MONITOR_ALERT` | ALERT: CHAL_E45_E3 ytd CAGR giveback > 3.0 pp (paper) |
| INFO | `e45_month_end` | `MONITOR_ALERT` | ALERT: CHAL_E45_E3 trailing_1y CAGR giveback > 3.0 pp (paper) |
| INFO | `e45_month_end` | `CUTOVER_BLOCKED_FLAG` | cutover_blocked=true (expected while Soft-Frozen KEEP) |
| INFO | `e45_blend025_month_end` | `MONITOR_ALERT` | ALERT: BLEND_E45_A25 ytd CAGR giveback > 3.0 pp (paper) |
| INFO | `e45_blend025_month_end` | `MONITOR_ALERT` | ALERT: BLEND_E45_A25 trailing_1y CAGR giveback > 3.0 pp (paper) |
| INFO | `e45_blend025_month_end` | `CUTOVER_BLOCKED_FLAG` | cutover_blocked=true (expected while Soft-Frozen KEEP) |
| INFO | `live_paper_recon` | `RECON_NOTE` | INDEX_DRIFT: max \|live_idx-paper_idx\|=3.9328% > 2% on overlap |
| INFO | `live_paper_recon` | `THIN_LIVE_HISTORY` | overlap_n=11 (<60) — not decision-grade for cutover |
| INFO | `data_source_phase_c_probes` | `PHASE_C_C1_FIN12_HISTORY_SHADOW_NOTE` | DRIFT on 1 ticker(s); does not count toward PASS |
| INFO | `data_source_phase_c_probes` | `PHASE_C_C3_TAIEX_OPTIONAL_FAILOVER_NOTE` | Helper is opt-in only; e21 still uses FinMind TaiwanStockPrice(TAIEX). |

## Routing

- CRITICAL → fail `e21-live-qc-smoke` / block live confidence
- HIGH → month-end pack annotates PAUSE; cutover checklists stay blocked
- INFO → recorded only

Re-run: `python3 scripts/ops_alert_scan.py`
