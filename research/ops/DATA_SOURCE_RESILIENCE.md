# Data Source Resilience — Inventory & Optimization

Date: 2026-09-05 (Phase B shadow reconcile landed)  
Status: **OPS / ENGINEERING** — Soft-Frozen **[0.50, 0.95] KEEP**; no live-wire  
KPI: `scripts/data_source_resilience_kpi.py` → `DATA_SOURCE_RESILIENCE_KPI.{json,md}`  
Shadow: `scripts/data_source_shadow_reconcile.py` → `DATA_SOURCE_SHADOW_RECONCILE.{json,md}`

## Goal

Make single-vendor risk **visible and prioritized**. Do not pretend blocked scrapers (Goodinfo / Wantgoo / CMoney) are backups.

## Current matrix

| Stream | Primary | Backup / shadow today | Grade | Notes |
|---|---|---|---|---|
| Fin-12 **history** OHLCV | GitHub `tw-stock-data-release` | **None** (TWSE ~14d append only) | **D** | Phase C for second full-history vendor |
| Fin-12 **recent** OHLCV | TWSE / live_market path | **Yahoo `.TW` shadow** (returns gate) | **B→B+** | Phase B: `fin12_recent` check |
| Telecom / 0050 raw OHLCV | FinMind | **Yahoo** (`fetch_telecom_0050_ohlcv.py`) | **A** | Runtime fallback |
| TAIEX | FinMind → live_market | **Yahoo `^TWII` shadow** (returns) | **D→C** | Phase B: shadow OK; not yet runtime failover |
| Adj / corporate-action factors | FinMind | **None** | **D** | Phase C research |
| Dividend **amount / ex-date** | FinMind | **Yahoo amount shadow** (flag-only) | **C→B** | Phase B: 114 overlaps, 0 flags (latest run) |
| Dividend **payment date** | FinMind → MOPS → **Yahoo TW** | Goodinfo/Wantgoo/CMoney **FAILED** | **A** | Keep Yahoo |
| E50 fundamentals | FinMind | None | **D** | Non-critical for Soft-Frozen |
| Runtime live/paper | Committed CSVs | Separate refresh workflows | **B** | — |

Grade: **A** = primary+working backup · **B** = adequate · **C** = single-vendor mitigated by shadow · **D** = single-point.

## Phases

### Phase A — DONE (#68)
Matrix + resilience KPI + pack/alert wire.

### Phase B — DONE (this change)
1. **TAIEX** live_market vs Yahoo `^TWII` — daily **returns** corr/MAE.  
2. **Dividend amounts** FinMind ledger vs Yahoo — **flag-only**, never auto-overwrite.  
3. **Fin sleeve recent** live_market vs Yahoo `.TW` — gate on returns; level scale noted.

Script: `scripts/data_source_shadow_reconcile.py`  
Artifacts: `research/ops/DATA_SOURCE_SHADOW_RECONCILE.*`, `repro/data-source-shadow/`

### Phase C — research charter only
1. Second vendor for full Fin-12 history.  
2. Corporate-action factor dual source.  
3. Optional **runtime** TAIEX failover (today shadow-only).  
4. Do **not** re-open Goodinfo/Wantgoo/CMoney as payment-date backups.

## Hard rules

- Soft-Frozen unchanged.  
- No rewrite of `forward/e21` history.  
- Backup ≠ promote; shadow QC ≠ cutover license.  
- Formal E22 books stay FinMind amounts + proven payment-date chain.

## Label

`DATA_SOURCE_RESILIENCE_2026-09-05_PHASE_B`
