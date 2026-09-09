# E45 Blend-α=0.05 Month-End Paper Monitor — asof 2026-09-08

Generated: `2026-09-09T12:08:30.086691+00:00`
Status: **OPERATING OBSERVE / PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **BLEND_E45_A05** (α=0.05 × E45 `E3_VOLTARGET_WINNER` on early-stack)

> **Dynamic alert windows:** `ytd`, `trailing_1y` (ALERT 3pp / PAUSE 5pp).  
> **Structural windows:** `heldout_2019_plus`, `sealed_2023_plus` (ALERT if MDD worsens or giveback > design+2pp; no structural PAUSE).  
> **`mtd` CAGR is display-only** — **not** a stitch gate.  
> **Stitch / cutover:** always blocked on this observe sleeve.

| Window | BASE CAGR | BASE MDD | BLEND_E45_A05 CAGR | BLEND_E45_A05 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | 1838.06%* | 0.00% | 1519.64%* | 0.00% | +0.00 | +318.42 | 0.9964 | no |
| ytd | 72.46% | -13.97% | 67.74% | -11.22% | +2.75 | +4.72 | 0.9822 | yes |
| trailing_1y | 56.87% | -13.97% | 51.93% | -11.22% | +2.75 | +4.94 | 0.9699 | yes |
| sealed_2023_plus | 25.55% | -13.97% | 24.23% | -11.22% | +2.75 | +1.32 | 0.9637 | yes |
| heldout_2019_plus | 18.47% | -22.39% | 17.59% | -21.75% | +0.64 | +0.88 | 0.9464 | yes |
| full | 13.97% | -22.39% | 13.56% | -21.75% | +0.64 | +0.42 | 0.9526 | no |

\* `mtd` CAGR annualized from a short sample — **non-decision / display-only**.

## Alerts

- ALERT: BLEND_E45_A05 ytd CAGR giveback > 3.0 pp (paper)
- ALERT: BLEND_E45_A05 trailing_1y CAGR giveback > 3.0 pp (paper)

## Stitch / cutover status

- `stitch_blocked`: **True** (always on observe sleeve)
- `cutover_blocked`: **True**
- `stitch_authorized`: **False**
- Soft-Frozen live clip stays **[0.60, 0.90]** — this monitor never flips it.
- Live DEFAULT books stay **`E22_v2s_tw`**.

## Ops note

- Refresh NAVs: `python3 scripts/e45_blend005_dual_paper_ledgers.py`
- Re-run monitor: `python3 scripts/e45_blend005_month_end_monitor.py`
- Or month-end pack: `python3 scripts/ops_month_end_paper_pack.py`
- Live stitch still requires a **second dedicated human ACCEPT** after checklist.
