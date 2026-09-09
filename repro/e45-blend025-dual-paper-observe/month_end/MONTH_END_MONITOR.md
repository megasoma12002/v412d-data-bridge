# E45 Blend-α=0.25 Month-End Paper Monitor — asof 2026-09-08

Generated: `2026-09-09T12:06:50.216152+00:00`
Status: **OPERATING OBSERVE / PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **BLEND_E45_A25** (α=0.25 × E45 `E3_VOLTARGET_WINNER` on early-stack)

> **Dynamic alert windows:** `ytd`, `trailing_1y` (ALERT 3pp / PAUSE 5pp).  
> **Structural windows:** `heldout_2019_plus`, `sealed_2023_plus` (ALERT if MDD worsens or giveback > design+2pp; no structural PAUSE).  
> **`mtd` CAGR is display-only** — **not** a stitch gate.  
> **Stitch / cutover:** always blocked on this observe sleeve.

| Window | BASE CAGR | BASE MDD | BLEND_E45_A25 CAGR | BLEND_E45_A25 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | 1838.06%* | 0.00% | 1161.99%* | 0.00% | +0.00 | +676.08 | 0.9915 | no |
| ytd | 72.46% | -13.97% | 60.29% | -8.43% | +5.54 | +12.17 | 0.9538 | yes |
| trailing_1y | 56.87% | -13.97% | 45.18% | -8.43% | +5.54 | +11.68 | 0.9287 | yes |
| sealed_2023_plus | 25.55% | -13.97% | 21.10% | -9.35% | +4.62 | +4.45 | 0.8815 | yes |
| heldout_2019_plus | 18.47% | -22.39% | 15.77% | -22.04% | +0.35 | +2.70 | 0.8437 | yes |
| full | 13.97% | -22.39% | 12.64% | -22.04% | +0.35 | +1.33 | 0.8553 | no |

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
