# E45 Blend-α=0.05 Month-End Paper Monitor — asof 2026-09-11

Generated: `2026-09-12T13:42:11.721296+00:00`
Status: **OPERATING OBSERVE / PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **BLEND_E45_A05** (α=0.05 × E45 `E3_VOLTARGET_WINNER` on early-stack)

> **Dynamic alert windows:** `ytd`, `trailing_1y` (ALERT 3pp / PAUSE 5pp).  
> **Structural windows:** `heldout_2019_plus`, `sealed_2023_plus` (ALERT if MDD worsens or giveback > design+2pp; no structural PAUSE).  
> **`mtd` CAGR is display-only** — **not** a stitch gate.  
> **Stitch / cutover:** always blocked on this observe sleeve.

| Window | BASE CAGR | BASE MDD | BLEND_E45_A05 CAGR | BLEND_E45_A05 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | 869.28%* | -1.35% | 795.43%* | -1.15% | +0.20 | +73.85 | 0.9975 | no |
| ytd | 74.25% | -13.97% | 69.84% | -11.22% | +2.75 | +4.41 | 0.9832 | yes |
| trailing_1y | 56.43% | -13.97% | 51.65% | -11.22% | +2.75 | +4.78 | 0.9707 | yes |
| sealed_2023_plus | 25.93% | -13.97% | 24.64% | -11.22% | +2.75 | +1.29 | 0.9647 | yes |
| heldout_2019_plus | 18.65% | -22.39% | 17.78% | -21.75% | +0.64 | +0.87 | 0.9474 | yes |
| full | 14.07% | -22.39% | 13.67% | -21.75% | +0.64 | +0.41 | 0.9536 | no |

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
