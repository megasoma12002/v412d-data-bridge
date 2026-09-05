# BLEND_025 Month-End Dual-Paper Runbook

Status: **OPERATING OBSERVE / PAPER OPS** — Soft-Frozen live Financial clip stays **[0.50, 0.95]**.  
Sleeve: Exact T+1 BASE Soft-Frozen vs **BLEND_025** (α=0.25·FIN50 + 0.75·BASE).  
Parent: `FINCAP50_SEALED_CAGR_IMPROVE_CHARTER.md` · screen · `FINCAP_BLEND025_DUAL_PAPER_PROMOTE_PROPOSAL.md`  
Observe artifacts: `BLEND_025_DUAL_PAPER_OBSERVE.md` · `BLEND_025_MONTH_END_MONITOR.md`

## Cadence

1. On/after each month-end (or research refresh):
   ```bash
   python3 scripts/e16_blend025_dual_paper_ledgers.py
   python3 scripts/e16_blend025_month_end_monitor.py
   ```
   Or via pack:
   ```bash
   python3 scripts/ops_month_end_paper_pack.py              # monitor only
   python3 scripts/ops_month_end_paper_pack.py --refresh-ledgers  # slow
   ```
2. Read `research/gaps/BLEND_025_MONTH_END_MONITOR.md`
3. File alerts into the debt board / ops note — **do not** edit Soft-Frozen

## Alert policy (paper) — charter trailing gates

Alert windows: **`heldout_2019_plus`**, **`sealed_2023_plus`**, **`ytd`**, **`trailing_1y`**.  
`mtd` is reported only (not a cutover gate).

| Condition | Action |
|---|---|
| No alerts | Continue dual-paper **observe** |
| MDD worse than BASE (alert window) | Escalate; do not discuss cutover |
| CAGR giveback > 3 pp (alert window) | Alert — extend observation |
| CAGR giveback > 5 pp (`PAUSE_REVIEW`) | Freeze cutover talk; Soft-Frozen unchanged |
| Clean trailing alone | Still **not** a cutover license |

## Cutover (always blocked on this sleeve)

This observe sleeve **never** authorizes live cutover. Cutover would require:

1. Separate human checklist + PR (FIN50 path / new charter — not this runbook)
2. Soft-Frozen clip stays **[0.50, 0.95]** until that PR
3. No rewrite of `forward/e21` history

`cutover_blocked=true` is permanent for BLEND_025 month-end JSON.

## Parallel note

- FIN_CAP_50 dual-paper continues separately (`NOT_READY_SEALED_CAGR`)
- L4_DD_PATH dual-paper continues separately (YTD PAUSE / cutover FROZEN)
- Do not conflate BLEND_025 observe PASS with FIN50 or L4 promote

## Label

`BLEND_025_MONTH_END_PAPER_RUNBOOK`
