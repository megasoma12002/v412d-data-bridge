# Ops Alerts

Generated: `2026-09-05T07:03:55.012025+00:00`
Overall: **HIGH**
Soft-Frozen **[0.50, 0.95] unchanged**. No auto cutover.

- CRITICAL: 0
- HIGH (PAUSE_REVIEW etc.): 3
- INFO: 9

| Severity | Source | Code | Message |
|---|---|---|---|
| HIGH | `l4_month_end` | `PAUSE_REVIEW` | PAUSE_REVIEW: ytd giveback > 5 pp — extend observation; does not revoke PASS_HELDOUT_L4 |
| HIGH | `fincap50_month_end` | `PAUSE_REVIEW` | PAUSE_REVIEW: ytd giveback > 5 pp — do not advance cutover discussion (aligns with FIN_CAP_50_GO_LIVE_VERIFY Gate E) |
| HIGH | `fincap50_month_end` | `PAUSE_REVIEW` | PAUSE_REVIEW: trailing_1y giveback > 5 pp — do not advance cutover discussion (aligns with FIN_CAP_50_GO_LIVE_VERIFY Gate E) |
| INFO | `live_qc` | `QC_PASS` | live QC PASS; Exact T+1 ok |
| INFO | `l4_month_end` | `MONITOR_ALERT` | ALERT: L4_DD_PATH_08_50 ytd CAGR giveback > 3.0 pp (paper ops) |
| INFO | `l4_month_end` | `MONITOR_ALERT` | ALERT: L4_DD_PATH_08_50 trailing_1y CAGR giveback > 3.0 pp (paper ops) |
| INFO | `l4_month_end` | `CUTOVER_BLOCKED_FLAG` | cutover_blocked=true (expected while Soft-Frozen KEEP) |
| INFO | `fincap50_month_end` | `MONITOR_ALERT` | ALERT: FIN_CAP_50 ytd CAGR giveback > 3.0 pp (paper) |
| INFO | `fincap50_month_end` | `MONITOR_ALERT` | ALERT: FIN_CAP_50 trailing_1y CAGR giveback > 3.0 pp (paper) |
| INFO | `fincap50_month_end` | `CUTOVER_BLOCKED_FLAG` | cutover_blocked=true (expected while Soft-Frozen KEEP) |
| INFO | `live_paper_recon` | `RECON_NOTE` | INDEX_DRIFT: max \|live_idx-paper_idx\|=2.2320% > 2% on overlap |
| INFO | `live_paper_recon` | `THIN_LIVE_HISTORY` | overlap_n=10 (<60) — not decision-grade for cutover |

## Routing

- CRITICAL → fail `e21-live-qc-smoke` / block live confidence
- HIGH → month-end pack annotates PAUSE; cutover checklists stay blocked
- INFO → recorded only

Re-run: `python3 scripts/ops_alert_scan.py`
