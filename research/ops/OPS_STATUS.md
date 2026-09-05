# Ops Status — One-Page Map

Date: 2026-09-05 (Layer-3 Gap #6 fidelity KPI)  
Charter: `research/ops/OPS_CONVERGENCE_CHARTER.md`  
Live Soft-Frozen Financial clip: **[0.50, 0.95] KEEP**

## What is live (only this)

| Item | Value |
|---|---|
| Stack | **E16 + Exact T+1 E18 + E22_v2s** |
| Path | `forward/e21/` |
| Clip | Financial **[0.50, 0.95]** via `scripts/e16_soft_frozen_base.py` |
| Daily job | `.github/workflows/v412f-forward-paper.yml` (weekdays) |
| QC smoke | `.github/workflows/e21-live-qc-smoke.yml` |
| QC | `scripts/e21_qc.py` → `forward/e21/qc_status.json` |

**Not live:** E45, E50-A overlay, FIN_CAP_50, L4_DD_PATH, Track A/B, E6/E9/E10 shadows.

## Paper sleeves (observe only)

| Sleeve | Status | Cutover |
|---|---|---|
| FIN_CAP_50 | Dual-paper OPERATING; YTD/1y PAUSE | **`NOT_READY_SEALED_CAGR` / FROZEN** — checklist: `CUTOVER_CHECKLIST_FIN50.md` |
| L4_DD_PATH_08_50 | Held-out PASS; YTD PAUSE_REVIEW | **FROZEN** — checklist: `CUTOVER_CHECKLIST_L4.md` |
| Track A S9A1 | KEEP (paper/monitor) | N/A — pointer: `TRACK_A_RUNBOOK_POINTER.md` |
| Track B S1 | STOP | Closed |

## Cadence

| Cadence | How |
|---|---|
| Daily live | `v412f-forward-paper` |
| Live QC smoke | `e21-live-qc-smoke` |
| Month-end pack | `ops-month-end-paper-pack` / `scripts/ops_month_end_paper_pack.py` |
| Live↔paper recon | Inside pack + `scripts/e21_live_vs_paper_recon.py` |

Latest pack: `research/ops/MONTH_END_PAPER_PACK.md`  
Alerts: `research/ops/OPS_ALERTS.md`  
E22 KPI: `research/ops/E22_DATA_QUALITY_KPI.md`  
Gap #6 fidelity: `research/ops/E22_GAP6_FIDELITY_KPI.md`  
Odd-lot promote (DEFERRED): `research/ops/ODD_LOT_PROMOTE_CHECKLIST.md`  
Five-layer gaps: `research/ops/FIVE_LAYER_GAP_CHECKLIST.md`  
Legacy forward config: `research/ops/FORWARD_LEGACY_NOTE.md`

## Commands

```bash
python3 scripts/e21_qc.py --state-dir forward/e21
python3 scripts/ops_month_end_paper_pack.py
python3 scripts/ops_alert_scan.py --report-only
python3 scripts/e22_data_quality_kpi.py
python3 scripts/e22_gap6_fidelity_kpi.py
python3 scripts/e21_live_vs_paper_recon.py
```

## Authority

1. Cutover / Now-Next: `research/STRATEGY_DEBT_BOARD.md`  
2. This map: `research/ops/OPS_STATUS.md`  
3. Plan: `research/ops/OPS_CONVERGENCE_CHARTER.md`  
4. Retention: `research/ops/ARTIFACT_RETENTION.md`  
5. Class ≠ live: `FROZEN_GOVERNANCE.md`

## Hard rules

- No auto Soft-Frozen flip  
- Dual-paper / held-out PASS ≠ cutover  
- Never rewrite `forward/e21` history  
- **`mtd` annualized CAGR = display-only** (non-decision)  
- Strategy merge only via human PR after checklist gates  
