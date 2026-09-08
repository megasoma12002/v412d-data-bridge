# BLEND_025 Month-End Paper Monitor — asof 2026-09-07

Generated: `2026-09-08T00:52:27.082455+00:00`
Status: **OPERATING OBSERVE / PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **BLEND_025** (α=0.25·FIN50 + 0.75·BASE)

> **Alert windows:** `heldout_2019_plus`, `sealed_2023_plus`, `ytd`, `trailing_1y`.  
> **`mtd` CAGR is display-only** — **not** a cutover gate.  
> **Cutover:** always blocked on this observe sleeve.

| Window | BASE CAGR | BASE MDD | BLEND_025 CAGR | BLEND_025 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | 1461.75%* | 0.00% | 1189.19%* | 0.00% | +0.00 | +272.57 | 0.9970 | no |
| ytd | 68.28% | -12.85% | 66.21% | -10.55% | +2.31 | +2.07 | 0.9921 | yes |
| trailing_1y | 53.33% | -12.85% | 53.22% | -10.55% | +2.31 | +0.11 | 0.9993 | yes |
| sealed_2023_plus | 25.20% | -12.85% | 25.18% | -10.55% | +2.31 | +0.02 | 0.9994 | yes |
| heldout_2019_plus | 17.72% | -22.39% | 18.19% | -21.55% | +0.83 | -0.47 | 1.0296 | yes |
| full | 13.78% | -22.39% | 13.92% | -21.55% | +0.83 | -0.14 | 1.0171 | yes |

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
