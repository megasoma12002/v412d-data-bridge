# E45 Blend-α=0.05 Month-End Paper Monitor — asof 2026-09-04

Generated: `2026-09-06T03:03:59.846741+00:00`
Status: **OPERATING OBSERVE / PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **BLEND_E45_A05** (α=0.05 × E45 `E3_VOLTARGET_WINNER` on early-stack)

> **Dynamic alert windows:** `ytd`, `trailing_1y` (ALERT 3pp / PAUSE 5pp).  
> **Structural windows:** `heldout_2019_plus`, `sealed_2023_plus` (ALERT if MDD worsens or giveback > design+2pp; no structural PAUSE).  
> **`mtd` CAGR is display-only** — **not** a stitch gate.  
> **Stitch / cutover:** always blocked on this observe sleeve.

| Window | BASE CAGR | BASE MDD | BLEND_E45_A05 CAGR | BLEND_E45_A05 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | 1992.20%* | 0.00% | 1600.88%* | 0.00% | +0.00 | +391.32 | 0.9975 | no |
| ytd | 68.37% | -14.09% | 63.50% | -11.31% | +2.78 | +4.87 | 0.9814 | yes |
| trailing_1y | 54.17% | -14.09% | 48.99% | -11.31% | +2.78 | +5.17 | 0.9679 | yes |
| sealed_2023_plus | 24.89% | -14.09% | 23.47% | -11.31% | +2.78 | +1.42 | 0.9610 | yes |
| heldout_2019_plus | 18.20% | -22.54% | 17.24% | -21.84% | +0.70 | +0.96 | 0.9417 | yes |
| full | 13.79% | -22.54% | 13.37% | -21.84% | +0.70 | +0.42 | 0.9516 | no |

\* `mtd` CAGR annualized from a short sample — **non-decision / display-only**.

## Alerts

- ALERT: BLEND_E45_A05 ytd CAGR giveback > 3.0 pp (paper)
- ALERT: BLEND_E45_A05 trailing_1y CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: trailing_1y giveback > 5 pp — extend observe; Soft-Frozen unchanged; no stitch talk

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
