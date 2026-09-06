# E45 Blend-α=0.10 FIN_ONLY Month-End Paper Monitor — asof 2024-12-31

Generated: `2026-09-06T04:28:44.747722+00:00`
Status: **OPERATING OBSERVE / PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **SLEEVE_FIN_ONLY_A10** (α=0.10 FIN_ONLY × E45 `E3_VOLTARGET_WINNER` on early-stack)

> **Dynamic alert windows:** `ytd`, `trailing_1y` (ALERT 3pp / PAUSE 5pp).  
> **Structural windows:** `heldout_2019_plus`, `sealed_2023_plus` (ALERT if MDD worsens or giveback > design+2pp; no structural PAUSE).  
> **`mtd` CAGR is display-only** — **not** a stitch gate.  
> **Stitch / cutover:** always blocked on this observe sleeve.

| Window | BASE CAGR | BASE MDD | SLEEVE_FIN_ONLY_A10 CAGR | SLEEVE_FIN_ONLY_A10 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | -9.82%* | -5.70% | -10.64%* | -5.07% | +0.63 | +0.82 | 0.9992 | no |
| ytd | 21.87% | -6.82% | 18.98% | -6.59% | +0.23 | +2.89 | 0.9773 | yes |
| trailing_1y | 21.87% | -6.82% | 18.98% | -6.59% | +0.23 | +2.89 | 0.9773 | yes |
| sealed_2023_plus | 14.79% | -6.97% | 15.48% | -6.82% | +0.16 | -0.69 | 1.0115 | yes |
| heldout_2019_plus | 13.25% | -22.54% | 12.93% | -21.63% | +0.91 | +0.32 | 0.9837 | yes |
| full | 10.84% | -22.54% | 10.80% | -21.63% | +0.91 | +0.03 | 0.9964 | no |

\* `mtd` CAGR annualized from a short sample — **non-decision / display-only**.

## Alerts

- None (dynamic windows clean; stitch still blocked)

## Stitch / cutover status

- `stitch_blocked`: **True** (always on observe sleeve)
- `cutover_blocked`: **True**
- `stitch_authorized`: **False**
- Soft-Frozen live clip stays **[0.50, 0.95]** — this monitor never flips it.
- Live DEFAULT books stay **`E22_v2s_tw`**.

## Ops note

- Refresh NAVs: `python3 scripts/e45_sleeve_local_dual_paper_ledgers.py`
- Re-run monitor: `python3 scripts/e45_sleeve_local_month_end_monitor.py`
- Or month-end pack: `python3 scripts/ops_month_end_paper_pack.py`
- Live stitch still requires a **second dedicated human ACCEPT** after checklist.
