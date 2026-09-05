# FIN_CAP_50 Month-End Dual-Paper Runbook

Status: **PAPER OPS** — Soft-Frozen live Financial clip stays **[0.50, 0.95]**.  
Authoritative go-live: **`NOT_READY_SEALED_CAGR`** (`FIN_CAP_50_GO_LIVE_VERIFY.md`).  
Related: `research/gaps/FIN_CAP_50_PROMOTE_PROPOSAL.md` (proposal only — cutover frozen)

## Cadence

1. On/after each month-end (or research refresh):
   ```bash
   python3 scripts/e16_fincap50_dual_paper_ledgers.py
   python3 scripts/e16_fincap50_month_end_monitor.py
   ```
2. Read `research/gaps/FIN_CAP_50_MONTH_END_MONITOR.md`
3. File alerts into the debt board / ops note — **do not** edit Soft-Frozen

## Alert policy (paper) — aligned with go-live Gate E

Alert windows: **`heldout_2019_plus`**, **`ytd`**, **`trailing_1y`**.  
`mtd` is reported only (not a cutover gate).

| Condition | Action |
|---|---|
| No alerts **and** go-live READY | Continue dual-paper; cutover still needs human PR |
| MDD worse than BASE (alert window) | Escalate; do not discuss cutover |
| CAGR giveback > 3 pp (alert window) | Alert — extend observation |
| CAGR giveback > 5 pp (`PAUSE_REVIEW`) | Freeze cutover discussion until new research |
| Go-live `NOT_READY_SEALED_CAGR` | Cutover frozen regardless of month-end alerts |

## Cutover (blocked by default)

Cutover requires **all** of:
1. Go-live verify READY (currently **not**)
2. ≥1 clean month-end (no PAUSE_REVIEW on ytd/1y/held-out)
3. Explicit human PR editing live Soft-Frozen clip

This runbook never flips live clips and never rewrites `forward/e21` history.

## Label

`FIN_CAP_50_MONTH_END_PAPER_RUNBOOK`
