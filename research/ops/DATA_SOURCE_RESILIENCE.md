# Data Source Resilience — Inventory & Optimization

Date: 2026-09-05 (Phase C probes landed)  
Status: **OPS / ENGINEERING** — Soft-Frozen **[0.50, 0.95] KEEP**; no live-wire  
KPI: `scripts/data_source_resilience_kpi.py` → `DATA_SOURCE_RESILIENCE_KPI.{json,md}`  
Shadow B: `scripts/data_source_shadow_reconcile.py` → `DATA_SOURCE_SHADOW_RECONCILE.{json,md}`  
Phase C: `scripts/data_source_phase_c_probes.py` → `DATA_SOURCE_PHASE_C_PROBES.{json,md}`  
TAIEX opt-in: `scripts/taiex_fetch_with_failover.py` (default **off** for e21)

## Goal

Make single-vendor risk **visible and prioritized**. Do not pretend blocked scrapers (Goodinfo / Wantgoo / CMoney) are backups.

## Current matrix

| Stream | Primary | Backup / shadow today | Grade | Notes |
|---|---|---|---|---|
| Fin-12 **history** OHLCV | GitHub `tw-stock-data-release` | **Yahoo `.TW` shadow** (returns, Phase C) | **C** | Flag-only; not runtime failover |
| Fin-12 **recent** OHLCV | TWSE / live_market path | **Yahoo `.TW` shadow** (returns gate) | **B** | Phase B: `fin12_recent` check |
| Telecom / 0050 raw OHLCV | FinMind | **Yahoo** (`fetch_telecom_0050_ohlcv.py`) | **A** | Runtime fallback |
| TAIEX | FinMind → live_market | **Yahoo `^TWII` shadow** + **opt-in failover helper** | **C** | e21 default still FinMind |
| Adj / corporate-action factors | live_market `adj_close` | **Yahoo Adj Close shadow** (Phase C) | **C** | Flag-only; methodology may differ |
| Dividend **amount / ex-date** | FinMind | **Yahoo amount shadow** (flag-only) | **B** | Phase B: no auto-overwrite |
| Dividend **payment date** | FinMind → MOPS → **Yahoo TW** | Goodinfo/Wantgoo/CMoney **FAILED** | **A** | Keep Yahoo |
| E50 fundamentals | FinMind | None | **D** | Non-critical for Soft-Frozen |
| Runtime live/paper | Committed CSVs | Separate refresh workflows | **B** | — |

Grade: **A** = primary+working backup · **B** = adequate · **C** = single-vendor mitigated by shadow · **D** = single-point.

## Phases

### Phase A — DONE (#68)
Matrix + resilience KPI + pack/alert wire.

### Phase B — DONE (#69)
1. **TAIEX** live_market vs Yahoo `^TWII` — daily **returns** corr/MAE.  
2. **Dividend amounts** FinMind ledger vs Yahoo — **flag-only**, never auto-overwrite.  
3. **Fin sleeve recent** live_market vs Yahoo `.TW` — gate on returns; level scale noted.

Script: `scripts/data_source_shadow_reconcile.py`  
Artifacts: `research/ops/DATA_SOURCE_SHADOW_RECONCILE.*`, `repro/data-source-shadow/`

### Phase C — DONE (this change)
1. **Fin-12 full history** Yahoo `.TW` return shadow vs `live_market` close.  
2. **Adj dual-source** Yahoo Adj Close vs `live_market` adj_close (flag-only).  
3. **Optional TAIEX runtime failover helper** (`--enable-yahoo-failover`); e21 default unchanged.  
4. Do **not** re-open Goodinfo/Wantgoo/CMoney as payment-date backups.

Charter: `research/ops/DATA_SOURCE_RESILIENCE_PHASE_C_CHARTER.md`  
Scripts: `data_source_phase_c_probes.py`, `taiex_fetch_with_failover.py`  
Artifacts: `research/ops/DATA_SOURCE_PHASE_C_PROBES.*`, `repro/data-source-phase-c/`

## Hard rules

- Soft-Frozen unchanged.  
- No rewrite of `forward/e21` history.  
- Backup ≠ promote; shadow QC ≠ cutover license.  
- Formal E22 books stay FinMind amounts + proven payment-date chain.  
- Yahoo TAIEX failover stays **opt-in** until a human wiring PR.

## Label

`DATA_SOURCE_RESILIENCE_2026-09-05_PHASE_C`
