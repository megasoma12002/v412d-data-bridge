# FINCAP L4-BLEND-025 — Dual-Paper Promote Proposal (NOT LIVE)

Date: 2026-09-05  
Status: **OPERATING OBSERVE** — dual-paper sleeve open (paper only)  
Screen: `research/gaps/FINCAP50_SEALED_CAGR_CHARTER_SCREEN.md`  
Charter: `research/gaps/FINCAP50_SEALED_CAGR_IMPROVE_CHARTER.md`  
Observe artifacts: `research/gaps/BLEND_025_DUAL_PAPER_OBSERVE.md` · `BLEND_025_MONTH_END_MONITOR.md`

## Decision from charter screen

| Item | Value |
|---|---|
| Family | L4-BLEND-LIGHT |
| ID | **BLEND_025** (α=0.25·FIN50 + 0.75·Soft-Frozen BASE) |
| Hist gates | **PASS** (OOF MDD / OOF+late CAGR gb / sealed MDD+CAGR) |
| Trailing ytd / 1y | **PASS** (ytd gb ≈ 2.48 pp; trailing_1y gb ≈ 0.29 pp) |
| Screen decision | **`PAPER_PROMOTE_PROPOSAL_ONLY`** → sleeve **opened** |

## Observe sleeve (opened)

| Item | Path / command |
|---|---|
| Dual-paper ledgers | `scripts/e16_blend025_dual_paper_ledgers.py` → `repro/blend025-dual-paper/` |
| Month-end monitor | `scripts/e16_blend025_month_end_monitor.py` |
| Month-end runbook | `research/gaps/BLEND_025_MONTH_END_RUNBOOK.md` |
| Month-end pack | wired in `ops_month_end_paper_pack.py` (`blend025_*`) |
| Alert scan | `ops_alert_scan.py` reads `BLEND_025_MONTH_END_MONITOR.json` |

## What this does NOT authorize

- Soft-Frozen clip flip (stays **[0.50, 0.95]**)
- Live cutover / live-wire
- Retune of FIN_CAP_50 lock `[0.35, 0.50]`
- Closing FIN50 dual-paper (still OPERATING / `NOT_READY_SEALED_CAGR`)
- Treating observe PASS as cutover license

## Ongoing ops steps

1. Refresh ledgers on cadence (`--refresh-ledgers` or standalone script).  
2. Re-check charter trailing gates each month-end.  
3. Live cutover only after `CUTOVER_CHECKLIST_FIN50.md` green + human PR (separate).

## Operating context (still blocked for live)

| Sleeve | Trailing | Cutover |
|---|---|---|
| FIN_CAP_50 dual-paper | PAUSE_REVIEW | FROZEN (`NOT_READY_SEALED_CAGR`) |
| L4_DD_PATH_08_50 dual-paper | PAUSE_REVIEW | FROZEN |
| **BLEND_025 dual-paper** | **OPERATING OBSERVE** | **Always blocked on this sleeve** |

## Reproducers

```bash
python3 scripts/e16_blend025_dual_paper_ledgers.py
python3 scripts/e16_blend025_month_end_monitor.py
python3 scripts/fincap50_sealed_cagr_charter_screen.py
# artifacts:
#   research/gaps/BLEND_025_DUAL_PAPER_OBSERVE.{json,md}
#   research/gaps/BLEND_025_MONTH_END_MONITOR.{json,md}
#   repro/blend025-dual-paper/
```
