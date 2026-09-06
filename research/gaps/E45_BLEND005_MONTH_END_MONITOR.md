# E45 Blend-α=0.05 Month-End Paper Monitor — asof 2024-12-31

Generated: `2026-09-06T04:28:44.155636+00:00`
Status: **OPERATING OBSERVE / PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **BLEND_E45_A05** (α=0.05 × E45 `E3_VOLTARGET_WINNER` on early-stack)

> **Dynamic alert windows:** `ytd`, `trailing_1y` (ALERT 3pp / PAUSE 5pp).  
> **Structural windows:** `heldout_2019_plus`, `sealed_2023_plus` (ALERT if MDD worsens or giveback > design+2pp; no structural PAUSE).  
> **`mtd` CAGR is display-only** — **not** a stitch gate.  
> **Stitch / cutover:** always blocked on this observe sleeve.

| Window | BASE CAGR | BASE MDD | BLEND_E45_A05 CAGR | BLEND_E45_A05 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | -9.82%* | -5.70% | -10.61%* | -5.22% | +0.48 | +0.79 | 0.9993 | no |
| ytd | 21.87% | -6.82% | 19.58% | -6.64% | +0.18 | +2.29 | 0.9820 | yes |
| trailing_1y | 21.87% | -6.82% | 19.58% | -6.64% | +0.18 | +2.29 | 0.9820 | yes |
| sealed_2023_plus | 14.79% | -6.97% | 15.32% | -6.87% | +0.10 | -0.53 | 1.0088 | yes |
| heldout_2019_plus | 13.25% | -22.54% | 13.02% | -21.84% | +0.70 | +0.22 | 0.9886 | yes |
| full | 10.84% | -22.54% | 10.83% | -21.84% | +0.70 | +0.01 | 0.9990 | no |

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
