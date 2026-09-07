# E45 Blend-α=0.05 Month-End Paper Monitor — asof 2026-09-07

Generated: `2026-09-07T17:20:34.945719+00:00`
Status: **OPERATING OBSERVE / PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **BLEND_E45_A05** (α=0.05 × E45 `E3_VOLTARGET_WINNER` on early-stack)

> **Dynamic alert windows:** `ytd`, `trailing_1y` (ALERT 3pp / PAUSE 5pp).  
> **Structural windows:** `heldout_2019_plus`, `sealed_2023_plus` (ALERT if MDD worsens or giveback > design+2pp; no structural PAUSE).  
> **`mtd` CAGR is display-only** — **not** a stitch gate.  
> **Stitch / cutover:** always blocked on this observe sleeve.

| Window | BASE CAGR | BASE MDD | BLEND_E45_A05 CAGR | BLEND_E45_A05 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | 1346.96%* | 0.00% | 1164.32%* | 0.00% | +0.00 | +182.64 | 0.9979 | no |
| ytd | 71.84% | -11.40% | 67.77% | -9.58% | +1.81 | +4.06 | 0.9847 | yes |
| trailing_1y | 56.15% | -11.40% | 51.87% | -9.58% | +1.81 | +4.28 | 0.9739 | yes |
| sealed_2023_plus | 24.50% | -11.84% | 23.16% | -11.63% | +0.20 | +1.34 | 0.9631 | yes |
| heldout_2019_plus | 17.61% | -22.08% | 16.74% | -21.64% | +0.44 | +0.86 | 0.9472 | yes |
| full | 13.44% | -22.08% | 13.00% | -21.64% | +0.44 | +0.45 | 0.9488 | no |

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
