# E45 Blend-α=0.05 Month-End Paper Monitor — asof 2026-09-07

Generated: `2026-09-07T17:02:54.356280+00:00`
Status: **OPERATING OBSERVE / PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **BLEND_E45_A05** (α=0.05 × E45 `E3_VOLTARGET_WINNER` on early-stack)

> **Dynamic alert windows:** `ytd`, `trailing_1y` (ALERT 3pp / PAUSE 5pp).  
> **Structural windows:** `heldout_2019_plus`, `sealed_2023_plus` (ALERT if MDD worsens or giveback > design+2pp; no structural PAUSE).  
> **`mtd` CAGR is display-only** — **not** a stitch gate.  
> **Stitch / cutover:** always blocked on this observe sleeve.

| Window | BASE CAGR | BASE MDD | BLEND_E45_A05 CAGR | BLEND_E45_A05 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | 1635.40%* | 0.00% | 1507.80%* | 0.00% | +0.00 | +127.60 | 0.9988 | no |
| ytd | 71.86% | -15.09% | 68.37% | -12.97% | +2.12 | +3.50 | 0.9869 | yes |
| trailing_1y | 57.90% | -15.09% | 53.73% | -12.97% | +2.12 | +4.17 | 0.9748 | yes |
| sealed_2023_plus | 25.68% | -15.09% | 24.59% | -12.97% | +2.12 | +1.09 | 0.9700 | yes |
| heldout_2019_plus | 18.89% | -23.37% | 18.05% | -22.75% | +0.62 | +0.84 | 0.9492 | yes |
| full | 14.21% | -23.37% | 13.77% | -22.75% | +0.62 | +0.44 | 0.9497 | no |

\* `mtd` CAGR annualized from a short sample — **non-decision / display-only**.

## Alerts

- ALERT: BLEND_E45_A05 ytd CAGR giveback > 3.0 pp (paper)
- ALERT: BLEND_E45_A05 trailing_1y CAGR giveback > 3.0 pp (paper)

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
