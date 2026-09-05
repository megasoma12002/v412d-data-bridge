# Artifact retention (ops)

Date: 2026-09-05  
Applies to live forward + paper monitors. Soft-Frozen clip policy unchanged.

## Canonical vs raw

| Kind | Canonical (read/commit) | Raw / scratch |
|---|---|---|
| Live ledgers | `forward/e21/` | GHA artifact zip (90d) |
| Live QC | `forward/e21/qc_status.json` | same |
| L4 / FIN50 month-end | `research/gaps/*_MONTH_END_MONITOR.*` | `repro/*/month_end/` mirrors |
| Track A status | `research/e50a/TRACK_A_S9A1_MONITOR_STATUS.*` | `repro/e50a-dual-track/track_a_s9a1_monitor/` |
| Ops pack summary | `research/ops/MONTH_END_PAPER_PACK.*` | GHA artifact `ops-month-end-paper-pack-*` |
| Live↔paper recon | `research/ops/LIVE_PAPER_RECON.*` | — |

If `repro/` and `research/gaps/` disagree, **trust `research/gaps/`** for month-end decisions.

## Retention

| Store | Policy |
|---|---|
| Git-tracked monitors / ops JSON+MD | Keep on `main` (append/update in place) |
| GHA `v412f-forward-paper` artifacts | 90 days |
| GHA `ops-month-end-paper-pack` artifacts | 90 days |
| Local untracked `repro/**/outputs/*fills*` scratch | Do not commit unless charter says so |

## Non-decision displays

- **`mtd` annualized CAGR** in month-end tables = display-only  
- Live windows shorter than ~60 sessions = not decision-grade for cutover

## Do not

- Rewrite `forward/e21` history to “fix” recon  
- Promote dual-paper PASS into Soft-Frozen from artifact alone  
- Treat GHA artifact expiry as loss of truth if git mirrors exist  
