# BLEND_025 Month-End Paper Monitor — asof 2026-09-08

Generated: `2026-09-09T12:52:47.087893+00:00`
Status: **OPERATING OBSERVE / PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **BLEND_025** (α=0.25·FIN50 + 0.75·BASE)

> **Alert windows:** `heldout_2019_plus`, `sealed_2023_plus`, `ytd`, `trailing_1y`.  
> **`mtd` CAGR is display-only** — **not** a cutover gate.  
> **Cutover:** always blocked on this observe sleeve.

| Window | BASE CAGR | BASE MDD | BLEND_025 CAGR | BLEND_025 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | 1835.01%* | 0.00% | 1490.45%* | 0.00% | +0.00 | +344.55 | 0.9961 | no |
| ytd | 72.42% | -13.95% | 70.17% | -11.94% | +2.01 | +2.25 | 0.9915 | yes |
| trailing_1y | 56.82% | -13.95% | 56.84% | -11.94% | +2.01 | -0.02 | 1.0001 | yes |
| sealed_2023_plus | 25.54% | -13.95% | 25.13% | -11.94% | +2.01 | +0.41 | 0.9887 | yes |
| heldout_2019_plus | 18.47% | -22.39% | 18.46% | -21.68% | +0.71 | +0.01 | 0.9995 | yes |
| full | 13.97% | -22.39% | 13.94% | -21.68% | +0.71 | +0.03 | 0.9964 | yes |

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
