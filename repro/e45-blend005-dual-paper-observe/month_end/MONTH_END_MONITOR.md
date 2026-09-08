# E45 Blend-α=0.05 Month-End Paper Monitor — asof 2026-09-07

Generated: `2026-09-08T00:52:28.041812+00:00`
Status: **OPERATING OBSERVE / PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **BLEND_E45_A05** (α=0.05 × E45 `E3_VOLTARGET_WINNER` on early-stack)

> **Dynamic alert windows:** `ytd`, `trailing_1y` (ALERT 3pp / PAUSE 5pp).  
> **Structural windows:** `heldout_2019_plus`, `sealed_2023_plus` (ALERT if MDD worsens or giveback > design+2pp; no structural PAUSE).  
> **`mtd` CAGR is display-only** — **not** a stitch gate.  
> **Stitch / cutover:** always blocked on this observe sleeve.

| Window | BASE CAGR | BASE MDD | BLEND_E45_A05 CAGR | BLEND_E45_A05 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | 1509.63%* | 0.00% | 1441.31%* | 0.00% | +0.00 | +68.32 | 0.9993 | no |
| ytd | 68.87% | -13.04% | 67.00% | -12.24% | +0.79 | +1.86 | 0.9929 | yes |
| trailing_1y | 53.96% | -13.04% | 52.06% | -12.24% | +0.79 | +1.91 | 0.9882 | yes |
| sealed_2023_plus | 25.33% | -13.04% | 24.64% | -12.24% | +0.79 | +0.69 | 0.9809 | yes |
| heldout_2019_plus | 17.78% | -22.39% | 17.69% | -22.24% | +0.14 | +0.09 | 0.9943 | yes |
| full | 13.81% | -22.39% | 13.74% | -22.24% | +0.14 | +0.07 | 0.9923 | no |

\* `mtd` CAGR annualized from a short sample — **non-decision / display-only**.

## Alerts

- None (dynamic windows clean; stitch still blocked)

## Stitch / cutover status

- `stitch_blocked`: **True** (always on observe sleeve)
- `cutover_blocked`: **True**
- `stitch_authorized`: **False**
- Soft-Frozen live clip stays **[0.50, 0.95]** — this monitor never flips it.
- Live DEFAULT books stay **`E22_v2s_tw`**.

## Ops note

- Refresh NAVs: `python3 scripts/e45_blend005_dual_paper_ledgers.py`
- Re-run monitor: `python3 scripts/e45_blend005_month_end_monitor.py`
- Or month-end pack: `python3 scripts/ops_month_end_paper_pack.py`
- Live stitch still requires a **second dedicated human ACCEPT** after checklist.
