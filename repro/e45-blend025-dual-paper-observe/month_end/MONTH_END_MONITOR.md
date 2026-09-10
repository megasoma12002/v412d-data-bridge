# E45 Blend-α=0.25 Month-End Paper Monitor — asof 2026-09-09

Generated: `2026-09-10T10:14:58.618086+00:00`
Status: **OPERATING OBSERVE / PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **BLEND_E45_A25** (α=0.25 × E45 `E3_VOLTARGET_WINNER` on early-stack)

> **Dynamic alert windows:** `ytd`, `trailing_1y` (ALERT 3pp / PAUSE 5pp).  
> **Structural windows:** `heldout_2019_plus`, `sealed_2023_plus` (ALERT if MDD worsens or giveback > design+2pp; no structural PAUSE).  
> **`mtd` CAGR is display-only** — **not** a stitch gate.  
> **Stitch / cutover:** always blocked on this observe sleeve.

| Window | BASE CAGR | BASE MDD | BLEND_E45_A25 CAGR | BLEND_E45_A25 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | 568.21%* | -1.35% | 491.44%* | -0.80% | +0.55 | +76.78 | 0.9971 | no |
| ytd | 68.34% | -13.97% | 57.88% | -8.43% | +5.54 | +10.46 | 0.9591 | yes |
| trailing_1y | 53.17% | -13.97% | 42.50% | -8.43% | +5.54 | +10.67 | 0.9333 | yes |
| sealed_2023_plus | 25.03% | -13.97% | 20.79% | -9.35% | +4.62 | +4.24 | 0.8865 | yes |
| heldout_2019_plus | 18.24% | -22.39% | 15.63% | -22.04% | +0.35 | +2.61 | 0.8484 | yes |
| full | 13.85% | -22.39% | 12.57% | -22.04% | +0.35 | +1.28 | 0.8601 | no |

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
