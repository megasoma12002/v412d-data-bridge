# FIN_CAP_50 Month-End Dual-Paper Runbook

Status: **PAPER OPS** — Soft-Frozen live Financial clip stays **[0.50, 0.95]**.  
Related: `research/gaps/FIN_CAP_50_PROMOTE_PROPOSAL.md` (#43 lineage)

## Cadence

1. On/after each month-end (or research refresh):
   ```bash
   python3 scripts/e16_fincap50_dual_paper_ledgers.py
   python3 scripts/e16_fincap50_month_end_monitor.py
   ```
2. Read `research/gaps/FIN_CAP_50_MONTH_END_MONITOR.md`
3. File alerts into the debt board / ops note — **do not** edit Soft-Frozen

## Alert policy (paper)

| Condition | Action |
|---|---|
| No alerts | Continue dual-paper observation |
| Held-out MDD worse than BASE | Escalate; do not discuss cutover |
| CAGR giveback > 3 pp | Alert — extend observation |
| CAGR giveback > 5 pp (`PAUSE_REVIEW`) | Freeze cutover discussion until new research |

## Cutover (still blocked by default)

Cutover requires a **separate human PR** after ≥1 clean month-end review and explicit approval.  
This runbook never flips live clips and never rewrites `forward/e21` history.

## Label

`FIN_CAP_50_MONTH_END_PAPER_RUNBOOK`
