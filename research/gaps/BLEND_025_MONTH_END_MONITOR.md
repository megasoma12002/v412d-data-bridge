# BLEND_025 Month-End Paper Monitor — asof 2026-09-09

Generated: `2026-09-10T10:14:57.969034+00:00`
Status: **OPERATING OBSERVE / PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **BLEND_025** (α=0.25·FIN50 + 0.75·BASE)

> **Alert windows:** `heldout_2019_plus`, `sealed_2023_plus`, `ytd`, `trailing_1y`.  
> **`mtd` CAGR is display-only** — **not** a cutover gate.  
> **Cutover:** always blocked on this observe sleeve.

| Window | BASE CAGR | BASE MDD | BLEND_025 CAGR | BLEND_025 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | 567.68%* | -1.35% | 504.42%* | -1.20% | +0.15 | +63.26 | 0.9976 | no |
| ytd | 68.30% | -13.95% | 66.50% | -11.94% | +2.01 | +1.79 | 0.9930 | yes |
| trailing_1y | 53.13% | -13.95% | 53.37% | -11.94% | +2.01 | -0.24 | 1.0015 | yes |
| sealed_2023_plus | 25.02% | -13.95% | 24.67% | -11.94% | +2.01 | +0.35 | 0.9902 | yes |
| heldout_2019_plus | 18.24% | -22.39% | 18.26% | -21.68% | +0.71 | -0.02 | 1.0011 | yes |
| full | 13.85% | -22.39% | 13.84% | -21.68% | +0.71 | +0.02 | 0.9980 | yes |

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
