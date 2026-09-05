# Data Source Resilience — Phase C Charter

Date: 2026-09-05  
Status: **CHARTER CLOSED — Phase C prep DONE** — Soft-Frozen **[0.50, 0.95] KEEP**  
Parent: `research/ops/DATA_SOURCE_RESILIENCE.md`  
Authority: `HUMAN_DECISION_REGISTER.md` (no Soft-Frozen flip; no silent ledger overwrite)  
Artifacts: `DATA_SOURCE_PHASE_C_PROBES.*` · `scripts/taiex_fetch_with_failover.py`

## Problem

Phase A/B made single-points visible and added Yahoo **shadow** QC for TAIEX returns, Fin recent returns, and dividend amounts. Remaining gaps:

1. **Fin-12 full history** still single-vendor (GitHub archive); no second full-history store.  
2. **Corporate-action / adj layer** still FinMind-only.  
3. **TAIEX** has Yahoo shadow but **no runtime failover** if FinMind fails mid-job.

## In scope (this phase)

| ID | Deliverable | Bound |
|---|---|---|
| C1 | Fin history **second-vendor shadow** (Yahoo `.TW` vs `live_market` full overlap) | Research / flag-only |
| C2 | Adj **dual-source shadow** (live `close`/`adj_close` path vs Yahoo Close/AdjClose) | Research / flag-only |
| C3 | **Optional TAIEX runtime failover helper** (FinMind → Yahoo `^TWII`) behind explicit flag | Ops tool; default **off** for e21 |
| C4 | Update resilience matrix + KPI + pack wire | Docs / cadence |

## Out of scope / WON’T

- Soft-Frozen flip or live cutover  
- Rewrite `forward/e21` history  
- Auto-overwrite E22 dividend amounts  
- Re-open Goodinfo / Wantgoo / CMoney  
- Quietly change e21 forward to Yahoo-primary without human PR  
- Paid TEJ/Bloomberg Fin-12 history purchase (charter may **recommend**; not execute here)

## Pass criteria

1. C1/C2 probes emit JSON/MD + detail CSVs under `repro/data-source-phase-c/`.  
2. C3 helper: FinMind success path + forced Yahoo failover path both demonstrable.  
3. e21 default path unchanged unless `--enable-taiex-yahoo-failover` used in **isolated** tool runs.  
4. Soft-Frozen KEEP asserted in all artifacts.

## Exit

| Outcome | Action |
|---|---|
| Probes green | Phase C **prep DONE**; runtime failover remains opt-in |
| Material DRIFT | Keep Soft-Frozen; file flags; do not auto-switch vendor |
| Need paid history | Separate procurement charter |

**2026-09-05:** Probes implemented; see `DATA_SOURCE_PHASE_C_PROBES.*`. Runtime TAIEX failover stays opt-in.

## Label

`DATA_SOURCE_RESILIENCE_PHASE_C_CHARTER_2026-09-05`
