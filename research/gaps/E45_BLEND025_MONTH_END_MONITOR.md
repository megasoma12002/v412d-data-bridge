# E45 Blend-α=0.25 Month-End Paper Monitor — asof 2026-09-07

Generated: `2026-09-08T00:52:27.721332+00:00`
Status: **OPERATING OBSERVE / PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **BLEND_E45_A25** (α=0.25 × E45 `E3_VOLTARGET_WINNER` on early-stack)

> **Dynamic alert windows:** `ytd`, `trailing_1y` (ALERT 3pp / PAUSE 5pp).  
> **Structural windows:** `heldout_2019_plus`, `sealed_2023_plus` (ALERT if MDD worsens or giveback > design+2pp; no structural PAUSE).  
> **`mtd` CAGR is display-only** — **not** a stitch gate.  
> **Stitch / cutover:** always blocked on this observe sleeve.

| Window | BASE CAGR | BASE MDD | BLEND_E45_A25 CAGR | BLEND_E45_A25 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | 1509.63%* | 0.00% | 1251.79%* | 0.00% | +0.00 | +257.84 | 0.9972 | no |
| ytd | 68.87% | -13.04% | 61.54% | -10.71% | +2.33 | +7.33 | 0.9719 | yes |
| trailing_1y | 53.96% | -13.04% | 47.73% | -10.71% | +2.33 | +6.23 | 0.9614 | yes |
| sealed_2023_plus | 25.33% | -13.04% | 23.13% | -10.71% | +2.33 | +2.21 | 0.9399 | yes |
| heldout_2019_plus | 17.78% | -22.39% | 16.91% | -21.98% | +0.41 | +0.87 | 0.9470 | yes |
| full | 13.81% | -22.39% | 13.31% | -21.98% | +0.41 | +0.50 | 0.9437 | no |

\* `mtd` CAGR annualized from a short sample — **non-decision / display-only**.

## Alerts

- ALERT: BLEND_E45_A25 ytd CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: ytd giveback > 5 pp — extend observe; Soft-Frozen unchanged; no stitch talk
- ALERT: BLEND_E45_A25 trailing_1y CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: trailing_1y giveback > 5 pp — extend observe; Soft-Frozen unchanged; no stitch talk

## Stitch / cutover status

- `stitch_blocked`: **True** (always on observe sleeve)
- `cutover_blocked`: **True**
- `stitch_authorized`: **False**
- Soft-Frozen live clip stays **[0.50, 0.95]** — this monitor never flips it.
- Live DEFAULT books stay **`E22_v2s_tw`**.

## Ops note

- Refresh NAVs: `python3 scripts/e45_blend025_dual_paper_ledgers.py`
- Re-run monitor: `python3 scripts/e45_blend025_month_end_monitor.py`
- Or month-end pack: `python3 scripts/ops_month_end_paper_pack.py`
- Live stitch still requires a **second dedicated human ACCEPT** after checklist.
