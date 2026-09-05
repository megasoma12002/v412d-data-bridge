# L4_DD_PATH_08_50 Month-End Dual-Paper Runbook

Status: **PAPER OPS** — Soft-Frozen live Financial clip stays **[0.50, 0.95]**.  
Related: `research/gaps/L4_DD_PATH_PROMOTE_PROPOSAL.md`, `research/gaps/MDD_L4_HELDOUT.md`

## Cadence

1. On/after each month-end (or research refresh):
   ```bash
   python3 scripts/e16_l4_dd_path_dual_paper_ledgers.py
   python3 scripts/e16_l4_dd_path_month_end_monitor.py
   ```
2. Read `research/gaps/L4_DD_PATH_MONTH_END_MONITOR.md`
3. File alerts into the debt board / ops note — **do not** edit Soft-Frozen

## Alert policy (paper)

| Condition | Action |
|---|---|
| No alerts | Continue dual-paper observation |
| Val or sealed MDD worse than BASE | Escalate; do not discuss cutover |
| CAGR giveback > 3 pp (val or sealed) | Alert — extend observation |
| CAGR giveback > 5 pp on val/sealed (`PAUSE_REVIEW`) | Freeze cutover discussion until new research |
| YTD / trailing-1y giveback > 3 pp | Ops alert — extend observation (does **not** revoke `PASS_HELDOUT_L4`) |
| YTD / trailing-1y giveback > 5 pp | Soft `PAUSE_REVIEW` on cutover talk only; held-out PASS unchanged |

## Cutover (still blocked by default)

Cutover requires a **separate human PR** after ≥1 clean month-end review and explicit approval.  
Unlike FIN_CAP_50, cutover would wire **path-dependent DD-path logic** (not a static clip swap).  
This runbook never flips live clips and never rewrites `forward/e21` history.

## Parallel note

FIN_CAP_50 dual-paper month-end continues separately (`NOT_READY_SEALED_CAGR`). Do not conflate the two promote paths.

## Label

`L4_DD_PATH_MONTH_END_PAPER_RUNBOOK`
