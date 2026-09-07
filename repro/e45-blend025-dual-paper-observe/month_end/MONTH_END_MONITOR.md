# E45 Blend-α=0.25 Month-End Paper Monitor — asof 2026-09-07

Generated: `2026-09-07T17:20:34.616680+00:00`
Status: **OPERATING OBSERVE / PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **BLEND_E45_A25** (α=0.25 × E45 `E3_VOLTARGET_WINNER` on early-stack)

> **Dynamic alert windows:** `ytd`, `trailing_1y` (ALERT 3pp / PAUSE 5pp).  
> **Structural windows:** `heldout_2019_plus`, `sealed_2023_plus` (ALERT if MDD worsens or giveback > design+2pp; no structural PAUSE).  
> **`mtd` CAGR is display-only** — **not** a stitch gate.  
> **Stitch / cutover:** always blocked on this observe sleeve.

| Window | BASE CAGR | BASE MDD | BLEND_E45_A25 CAGR | BLEND_E45_A25 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | 1346.96%* | 0.00% | 911.00%* | 0.00% | +0.00 | +435.96 | 0.9943 | no |
| ytd | 71.84% | -11.40% | 62.13% | -8.30% | +3.09 | +9.71 | 0.9633 | yes |
| trailing_1y | 56.15% | -11.40% | 46.84% | -8.30% | +3.09 | +9.31 | 0.9431 | yes |
| sealed_2023_plus | 24.50% | -11.84% | 20.99% | -10.78% | +1.05 | +3.50 | 0.9052 | yes |
| heldout_2019_plus | 17.61% | -22.08% | 15.46% | -21.53% | +0.54 | +2.15 | 0.8728 | yes |
| full | 13.44% | -22.08% | 12.38% | -21.53% | +0.54 | +1.07 | 0.8818 | no |

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
