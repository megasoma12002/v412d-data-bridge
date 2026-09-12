# E45 Blend-α=0.05 Month-End Paper Monitor — asof 2026-09-09

Generated: `2026-09-12T00:11:23.484449+00:00`
Status: **OPERATING OBSERVE / PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **BLEND_E45_A05** (α=0.05 × E45 `E3_VOLTARGET_WINNER` on early-stack)

> **Dynamic alert windows:** `ytd`, `trailing_1y` (ALERT 3pp / PAUSE 5pp).  
> **Structural windows:** `heldout_2019_plus`, `sealed_2023_plus` (ALERT if MDD worsens or giveback > design+2pp; no structural PAUSE).  
> **`mtd` CAGR is display-only** — **not** a stitch gate.  
> **Stitch / cutover:** always blocked on this observe sleeve.

| Window | BASE CAGR | BASE MDD | BLEND_E45_A05 CAGR | BLEND_E45_A05 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | 568.21%* | -1.35% | 526.44%* | -1.15% | +0.20 | +41.78 | 0.9985 | no |
| ytd | 68.34% | -13.97% | 64.27% | -11.22% | +2.75 | +4.07 | 0.9842 | yes |
| trailing_1y | 53.17% | -13.97% | 48.56% | -11.22% | +2.75 | +4.61 | 0.9712 | yes |
| sealed_2023_plus | 25.03% | -13.97% | 23.79% | -11.22% | +2.75 | +1.25 | 0.9656 | yes |
| heldout_2019_plus | 18.24% | -22.39% | 17.39% | -21.75% | +0.64 | +0.85 | 0.9483 | yes |
| full | 13.85% | -22.39% | 13.45% | -21.75% | +0.64 | +0.40 | 0.9545 | no |

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
