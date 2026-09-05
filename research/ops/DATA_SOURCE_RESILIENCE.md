# Data Source Resilience — Inventory & Optimization

Date: 2026-09-05  
Status: **OPS / ENGINEERING** — Soft-Frozen **[0.50, 0.95] KEEP**; no live-wire  
KPI: `scripts/data_source_resilience_kpi.py` → `DATA_SOURCE_RESILIENCE_KPI.{json,md}`

## Goal

Make single-vendor risk **visible and prioritized**. Do not pretend blocked scrapers (Goodinfo / Wantgoo / CMoney) are backups.

## Current matrix

| Stream | Primary | Backup today | Grade | Optimize next |
|---|---|---|---|---|
| Fin-12 **history** OHLCV | GitHub `tw-stock-data-release` | **None** (TWSE only ~14d append) | **D** | Phase B: TWSE/Yahoo shadow archive for overlap QC |
| Fin-12 **recent** OHLCV | TWSE `MI_INDEX` | None second exchange | **B** | Keep; extend append window only if needed |
| Telecom / 0050 raw OHLCV | FinMind | **Yahoo** (`fetch_telecom_0050_ohlcv.py`) | **A** | Pattern to copy |
| TAIEX | FinMind only | **None** | **D** | Phase A: Yahoo `^TWII` or TWSE index fetch + diff KPI |
| Adj / corporate-action factors | FinMind | **None** | **D** | Phase C: cross-check vs Yahoo adj (research only) |
| Dividend **amount / ex-date** | FinMind | No second amount feed | **C** | Phase B: Yahoo amount reconcile (flag drift, don’t silent-replace) |
| Dividend **payment date** | FinMind → MOPS → **Yahoo TW** | Goodinfo/Wantgoo/CMoney **FAILED** | **A** | Keep Yahoo; drop dead scrapers from “backup” lists |
| E50 fundamentals | FinMind | None | **D** | Out of Soft-Frozen critical path; charter if needed |
| Runtime live/paper | Committed `live_market.csv` + `e22_dividend_events.csv` | Separate refresh workflows | **B** | Alert if dividend CSV stale vs calendar |

Grade: **A** = primary+working backup · **B** = adequate for live cadence · **C** = works but single-vendor on critical field · **D** = single-point / no backup.

## Optimization phases (objective order)

### Phase A — do now (this change)
1. Publish this matrix as ops authority.  
2. Automated resilience KPI (single-point flags = INFO, not Soft-Frozen flip).  
3. Wire KPI into month-end pack + alert scan (report-only).

### Phase B — next engineering (separate PR)
1. **TAIEX dual-fetch probe**: FinMind vs Yahoo `^TWII` (or TWSE) → overlap RMSE / gap days; write shadow CSV only.  
2. **Dividend amount reconcile**: Yahoo vs FinMind on ex-date keys → drift report; never auto-overwrite formal ledger without human PR.  
3. **Fin-12 recent shadow**: optional Yahoo `.TW` panel vs TWSE append for last N days.

### Phase C — research charter only
1. Second vendor for full Fin-12 history (paid / alternate archive).  
2. Corporate-action factor dual source.  
3. Do **not** re-open Goodinfo/Wantgoo/CMoney as payment-date backups.

## Hard rules

- Soft-Frozen unchanged.  
- No rewrite of `forward/e21` history.  
- Backup ≠ promote; shadow QC ≠ cutover license.  
- Formal E22 books stay FinMind amounts + proven payment-date chain.

## Label

`DATA_SOURCE_RESILIENCE_2026-09-05`
