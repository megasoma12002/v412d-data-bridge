# BLEND_025 Month-End Paper Monitor — asof 2026-09-04

Generated: `2026-09-05T08:08:55.165654+00:00`
Status: **OPERATING OBSERVE / PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **BLEND_025** (α=0.25·FIN50 + 0.75·BASE)

> **Alert windows:** `heldout_2019_plus`, `sealed_2023_plus`, `ytd`, `trailing_1y`.  
> **`mtd` CAGR is display-only** — **not** a cutover gate.  
> **Cutover:** always blocked on this observe sleeve.

| Window | BASE CAGR | BASE MDD | BLEND_025 CAGR | BLEND_025 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | 2025.06%* | 0.00% | 1563.90%* | 0.00% | +0.00 | +461.16 | 0.9971 | no |
| ytd | 68.27% | -14.46% | 65.79% | -12.34% | +2.11 | +2.48 | 0.9906 | yes |
| trailing_1y | 54.37% | -14.46% | 54.08% | -12.34% | +2.11 | +0.29 | 0.9982 | yes |
| sealed_2023_plus | 24.93% | -14.46% | 24.42% | -12.34% | +2.11 | +0.51 | 0.9859 | yes |
| heldout_2019_plus | 18.24% | -22.64% | 18.11% | -21.82% | +0.82 | +0.12 | 0.9924 | yes |
| full | 13.78% | -22.64% | 13.69% | -21.82% | +0.82 | +0.09 | 0.9894 | yes |

\* `mtd` CAGR annualized from a short sample — **non-decision / display-only**.

## Alerts

- None (trailing/charter windows clean; cutover still blocked)

## Cutover status

- `cutover_blocked`: **True** (always on observe sleeve)
- `cutover_authorized`: **False**
- Soft-Frozen live clip stays **[0.50, 0.95]** — this monitor never flips it.

## Ops note

- Refresh NAVs: `python3 scripts/e16_blend025_dual_paper_ledgers.py`
- Re-run monitor: `python3 scripts/e16_blend025_month_end_monitor.py`
- Or month-end pack: `python3 scripts/ops_month_end_paper_pack.py`
- Live cutover still requires a **separate human PR** after checklist gates.
