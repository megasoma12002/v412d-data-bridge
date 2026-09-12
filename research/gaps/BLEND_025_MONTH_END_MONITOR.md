# BLEND_025 Month-End Paper Monitor — asof 2026-09-11

Generated: `2026-09-12T13:42:10.801663+00:00`
Status: **OPERATING OBSERVE / PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **BLEND_025** (α=0.25·FIN50 + 0.75·BASE)

> **Alert windows:** `heldout_2019_plus`, `sealed_2023_plus`, `ytd`, `trailing_1y`.  
> **`mtd` CAGR is display-only** — **not** a cutover gate.  
> **Cutover:** always blocked on this observe sleeve.

| Window | BASE CAGR | BASE MDD | BLEND_025 CAGR | BLEND_025 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | 868.54%* | -1.35% | 698.31%* | -1.20% | +0.15 | +170.24 | 0.9939 | no |
| ytd | 74.21% | -13.95% | 71.39% | -11.94% | +2.01 | +2.82 | 0.9893 | yes |
| trailing_1y | 56.39% | -13.95% | 55.81% | -11.94% | +2.01 | +0.58 | 0.9964 | yes |
| sealed_2023_plus | 25.92% | -13.95% | 25.43% | -11.94% | +2.01 | +0.49 | 0.9865 | yes |
| heldout_2019_plus | 18.65% | -22.39% | 18.61% | -21.68% | +0.71 | +0.04 | 0.9973 | yes |
| full | 14.07% | -22.39% | 14.02% | -21.68% | +0.71 | +0.05 | 0.9942 | yes |

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
