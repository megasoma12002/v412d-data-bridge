# BLEND_025 Month-End Paper Monitor — asof 2026-09-07

Generated: `2026-09-07T17:02:53.340788+00:00`
Status: **OPERATING OBSERVE / PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **BLEND_025** (α=0.25·FIN50 + 0.75·BASE)

> **Alert windows:** `heldout_2019_plus`, `sealed_2023_plus`, `ytd`, `trailing_1y`.  
> **`mtd` CAGR is display-only** — **not** a cutover gate.  
> **Cutover:** always blocked on this observe sleeve.

| Window | BASE CAGR | BASE MDD | BLEND_025 CAGR | BLEND_025 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | 1643.44%* | 0.00% | 1364.56%* | 0.00% | +0.00 | +278.88 | 0.9972 | no |
| ytd | 71.83% | -15.10% | 69.12% | -12.52% | +2.58 | +2.71 | 0.9898 | yes |
| trailing_1y | 57.90% | -15.10% | 56.75% | -12.52% | +2.58 | +1.15 | 0.9931 | yes |
| sealed_2023_plus | 25.64% | -15.10% | 25.28% | -12.52% | +2.58 | +0.37 | 0.9898 | yes |
| heldout_2019_plus | 18.85% | -23.36% | 18.59% | -22.05% | +1.31 | +0.26 | 0.9842 | yes |
| full | 14.19% | -23.36% | 14.00% | -22.05% | +1.31 | +0.19 | 0.9781 | yes |

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
