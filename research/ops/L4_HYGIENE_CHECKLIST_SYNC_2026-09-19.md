# L4 hygiene — cutover checklist sync (2026-09-19)

Status: **DOCS / OPS HYGIENE ONLY** — Soft-Frozen KEEP · no L4 live cutover · no broker write.  
Scope: refresh stale L4 cutover prep SSOT to match latest month-end monitor.

## Why

`CUTOVER_CHECKLIST_L4.md` still cited **asof 2026-09-04** YTD giveback ~5.39 pp.  
Latest pack (`L4_DD_PATH_MONTH_END_MONITOR.json`, asof **2026-09-16**, generated 2026-09-19) shows worse trailing and dual `PAUSE_REVIEW`. Stale gate table risks reading “almost clean” when cutover talk stays frozen.

## What changed

| Artifact | Change |
|---|---|
| `CUTOVER_CHECKLIST_L4.md` | Gate table → asof 2026-09-16; YTD ~9.53 pp · 1y ~5.33 pp dual PAUSE; sealed MDD ALERT; register #4 / runbook pointers |
| `OPS_STATUS.md` | L4 row: YTD **and** trailing_1y PAUSE_REVIEW |
| `STRATEGY_DEBT_BOARD.md` | Eng/hygiene residue bullet for this sync |

## Explicit non-changes

- No Soft-Frozen / FINBAND edit  
- No L4 live-wire / cutover PR  
- No FIN50 / BLEND_025 / Soft / Sleeve / priv promote  
- No regenerate of dual-paper ledgers (NAV already refreshed under ops residual pack)  
- No force-POINTER on near-duplicate `repro/l4-*/` MDs (`kept_distinct` under MD-dedupe policy)

## Evidence (decision windows, asof 2026-09-16)

| Window | MDD Δ pp | CAGR giveback pp | Flag |
|---|---:|---:|---|
| ytd | −0.53 | **9.53** | PAUSE_REVIEW |
| trailing_1y | −0.53 | **5.33** | PAUSE_REVIEW |
| sealed_2023_plus | −0.32 | 2.99 | ALERT (MDD worse) |
| heldout_2019_plus | +1.48 | 1.88 | held-out PASS unchanged |

Register #4 remains **DEFER** until ≥1 clean month-end (no YTD/1y PAUSE) + checklist all YES + human PR.

## Label

`L4_HYGIENE_CHECKLIST_SYNC_2026-09-19__DOCS_ONLY`
