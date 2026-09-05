# Ops Status — One-Page Map

Date: 2026-09-05 (strategy closure prep)  
Charter: `research/ops/OPS_CONVERGENCE_CHARTER.md`  
Live Soft-Frozen Financial clip: **[0.50, 0.95] KEEP**  
Binding decisions: `research/ops/HUMAN_DECISION_REGISTER.md`  
Live claims: `research/ops/LIVE_CLAIM_TARGET_POLICY.md`  
Strategy update SOP: `research/ops/STRATEGY_UPDATE_STANDARD_PROCESS.md`

## What is live (only this)

| Item | Value |
|---|---|
| Stack | **E16 + Exact T+1 E18 + E22_v2s** |
| Path | `forward/e21/` |
| Clip | Financial **[0.50, 0.95]** via `scripts/e16_soft_frozen_base.py` |
| Daily job | `.github/workflows/v412f-forward-paper.yml` (weekdays) |
| QC smoke | `.github/workflows/e21-live-qc-smoke.yml` |
| QC | `scripts/e21_qc.py` → `forward/e21/qc_status.json` |

**Not live:** E45, E50-A overlay, FIN_CAP_50, L4_DD_PATH, BLEND_025, Track A/B, E6/E9/E10 shadows.

## Paper sleeves (observe only)

| Sleeve | Status | Cutover |
|---|---|---|
| FIN_CAP_50 | Dual-paper OPERATING; YTD/1y PAUSE | **REJECT static cutover for now** (`NOT_READY_SEALED_CAGR`) — register #2 |
| L4_DD_PATH_08_50 | Held-out PASS; YTD PAUSE_REVIEW | **DEFER** cutover — register #4; checklist: `CUTOVER_CHECKLIST_L4.md` |
| BLEND_025 | Dual-paper **OPERATING OBSERVE** | Sole sealed-CAGR successor (register #3); live **NOT READY** (#5); checklist prep: `CUTOVER_CHECKLIST_BLEND025.md` |
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
Data-source resilience: `research/ops/DATA_SOURCE_RESILIENCE.md`  
Data-source resilience KPI: `research/ops/DATA_SOURCE_RESILIENCE_KPI.md`  
Data-source shadow reconcile (Phase B): `research/ops/DATA_SOURCE_SHADOW_RECONCILE.md`  
Odd-lot promote (DEFERRED): `research/ops/ODD_LOT_PROMOTE_CHECKLIST.md`  
Odd-lot promote decision pack (awaiting human): `research/ops/ODD_LOT_PROMOTE_DECISION_PACK.md`  
Par-value lookup charter (blocks odd-lot promote): `research/ops/PAR_VALUE_LOOKUP_CHARTER.md`  
Par-value inventory: `research/ops/PAR_VALUE_INVENTORY.md` · `data/corporate_actions/par_value_by_code.csv`  
Tax/receivable formal books charter (draft): `research/ops/FORMAL_TAX_RECEIVABLE_BOOKS_CHARTER.md`  
E45 live-stitch charter (draft, not accepted): `research/ops/E45_LIVE_STITCH_CHARTER.md`  
FIN50 sealed-CAGR charter: `research/gaps/FINCAP50_SEALED_CAGR_IMPROVE_CHARTER.md`  
FIN50 charter screen: `research/gaps/FINCAP50_SEALED_CAGR_CHARTER_SCREEN.md`  
BLEND_025 paper-promote proposal: `research/gaps/FINCAP_BLEND025_DUAL_PAPER_PROMOTE_PROPOSAL.md`  
BLEND_025 dual-paper observe: `research/gaps/BLEND_025_DUAL_PAPER_OBSERVE.md`  
BLEND_025 month-end: `research/gaps/BLEND_025_MONTH_END_MONITOR.md`  
BLEND_025 month-end runbook: `research/gaps/BLEND_025_MONTH_END_RUNBOOK.md`  
BLEND_025 cutover checklist (prep): `research/ops/CUTOVER_CHECKLIST_BLEND025.md`  
Live claim / target policy: `research/ops/LIVE_CLAIM_TARGET_POLICY.md`  
Live E22 evidence readiness: `research/ops/LIVE_E22_FIELD_EVIDENCE.md`  
Post-forward E22 verify: `research/ops/POST_FORWARD_E22_VERIFY_RUNBOOK.md`  
Archive sentinel policy: `research/ops/ARCHIVE_SENTINEL_HYGIENE.md`  
Five-layer gaps: `research/ops/FIVE_LAYER_GAP_CHECKLIST.md`  
Human decision register: `research/ops/HUMAN_DECISION_REGISTER.md`  
Strategy update SOP: `research/ops/STRATEGY_UPDATE_STANDARD_PROCESS.md`  
Legacy forward config: `research/ops/FORWARD_LEGACY_NOTE.md`

## Commands

```bash
python3 scripts/e21_qc.py --state-dir forward/e21
python3 scripts/ops_month_end_paper_pack.py
python3 scripts/ops_alert_scan.py --report-only
python3 scripts/e22_data_quality_kpi.py
python3 scripts/e22_gap6_fidelity_kpi.py
python3 scripts/data_source_resilience_kpi.py
python3 scripts/data_source_shadow_reconcile.py
python3 scripts/data_source_phase_c_probes.py
python3 scripts/taiex_fetch_with_failover.py --help
python3 scripts/e21_live_vs_paper_recon.py
python3 scripts/e16_blend025_dual_paper_ledgers.py
python3 scripts/e16_blend025_month_end_monitor.py
```

## Authority

1. Cutover / Now-Next: `research/STRATEGY_DEBT_BOARD.md`  
2. Strategy update SOP: `research/ops/STRATEGY_UPDATE_STANDARD_PROCESS.md`  
3. This map: `research/ops/OPS_STATUS.md`  
4. Plan: `research/ops/OPS_CONVERGENCE_CHARTER.md`  
5. Retention: `research/ops/ARTIFACT_RETENTION.md`  
6. Class ≠ live: `FROZEN_GOVERNANCE.md`

## Hard rules

- No auto Soft-Frozen flip  
- Dual-paper / held-out PASS ≠ cutover  
- Never rewrite `forward/e21` history  
- **`mtd` annualized CAGR = display-only** (non-decision)  
- Strategy merge only via human PR after checklist gates  
