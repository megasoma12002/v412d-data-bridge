# Five-Layer Gap Checklist — Operable System

Date: 2026-09-05 (hardening round: alerts + E22 KPI)  
Live Soft-Frozen Financial clip: **[0.50, 0.95] KEEP**  
Authority: `research/STRATEGY_DEBT_BOARD.md` · map: `OPS_STATUS.md`

Legend: **DONE** · **PARTIAL** · **OPEN** · **DEFERRED** (gated / out of scope)

## Layer 1 — Strategy

| Item | Status | Notes |
|---|---|---|
| Live = Soft-Frozen core only (E16+E18+E22_v2s) | **DONE** | |
| Paper sleeves split (FIN50 / L4 / Track A) | **DONE** | |
| Cutover checklists (prep only) | **DONE** | `CUTOVER_CHECKLIST_{L4,FIN50}.md` |
| L4 YTD/1y clean for cutover | **OPEN** | PAUSE_REVIEW — observe |
| FIN50 sealed CAGR gate | **OPEN** | `NOT_READY_SEALED_CAGR` |
| Alpha / E45 live stitch | **DEFERRED** | needs new charter + human PR |

## Layer 2 — Live / ops cadence

| Item | Status | Notes |
|---|---|---|
| Weekday live forward GHA | **DONE** | `v412f-forward-paper` |
| Live QC smoke | **DONE** | `e21-live-qc-smoke` |
| Month-end one-button pack | **DONE** | `ops-month-end-paper-pack` |
| Live↔paper Soft-Frozen recon | **PARTIAL** | works; thin live history (~10d) |
| QC FAIL / PAUSE alert routing | **DONE** | `ops_alert_scan` + GHA step summary/artifacts |
| Grow live history to decision-grade | **OPEN** | need ≥~60 sessions before recon is cutover-grade |

## Layer 3 — Data / execution

| Item | Status | Notes |
|---|---|---|
| E22_v2s formal books wired | **DONE** | |
| Exact T+1 QC field preserved | **DONE** | |
| E22 payment/ex-date KPI in month-end | **DONE** | `e22_data_quality_kpi` → `E22_DATA_QUALITY_KPI.*` |
| TW odd-lot variant promote | **DEFERRED** | named research variant only |
| Ongoing dividend gap monitoring | **PARTIAL** | KPI flags; re-check each pack |

## Layer 4 — Governance / docs

| Item | Status | Notes |
|---|---|---|
| OPS_STATUS one-pager | **DONE** | |
| README → ops entry | **DONE** | |
| Artifact retention doc | **DONE** | |
| Forward legacy config note | **DONE** | `FORWARD_LEGACY_NOTE.md` |
| Phase 0–2 merged to main | **DONE** | #58 / #59 / #60 |
| Obs #57 closed | **DONE** | superseded |

## Layer 5 — Engineering / repo

| Item | Status | Notes |
|---|---|---|
| Soft-Frozen single source | **DONE** | `e16_soft_frozen_base` |
| Challenger constant single-source polish | **PARTIAL** | hot path done; archive scripts residual |
| Shadow E6/E9/E10 labeled not-live | **DONE** | OPS_STATUS + legacy note |
| Archive `or 0` / `or 9` hygiene | **OPEN** | low priority |

---

## This round completed

1. Merged **#60** (Phase 2) to main  
2. Added **`ops_alert_scan`** + wired into QC smoke / month-end pack summaries  
3. Added **`e22_data_quality_kpi`** into month-end pack  
4. Added **`FORWARD_LEGACY_NOTE.md`**  
5. Published this checklist  

## Still highest-value OPEN items

1. Keep running month-end pack until L4 YTD PAUSE clears (Layer 1/2)  
2. Let live `forward/e21` history lengthen; re-check INDEX_DRIFT (Layer 2)  
3. Optional: sealed-CAGR **new research charter** if pursuing FIN50 (Layer 1 DEFERRED path)  

**Not OPEN for auto-work:** Soft-Frozen flip, L4/FIN50 live cutover without human checklist green.
