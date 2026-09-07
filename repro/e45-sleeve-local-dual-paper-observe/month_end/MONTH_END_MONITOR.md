# E45 Blend-α=0.10 FIN_ONLY Month-End Paper Monitor — asof 2026-09-07

Generated: `2026-09-07T15:50:28.241485+00:00`
Status: **OPERATING OBSERVE / PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **SLEEVE_FIN_ONLY_A10** (α=0.10 FIN_ONLY × E45 `E3_VOLTARGET_WINNER` on early-stack)

> **Dynamic alert windows:** `ytd`, `trailing_1y` (ALERT 3pp / PAUSE 5pp).  
> **Structural windows:** `heldout_2019_plus`, `sealed_2023_plus` (ALERT if MDD worsens or giveback > design+2pp; no structural PAUSE).  
> **`mtd` CAGR is display-only** — **not** a stitch gate.  
> **Stitch / cutover:** always blocked on this observe sleeve.

| Window | BASE CAGR | BASE MDD | SLEEVE_FIN_ONLY_A10 CAGR | SLEEVE_FIN_ONLY_A10 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | 1509.63%* | 0.00% | 1385.74%* | 0.00% | +0.00 | +123.89 | 0.9987 | no |
| ytd | 68.87% | -13.04% | 65.89% | -11.78% | +1.26 | +2.98 | 0.9886 | yes |
| trailing_1y | 53.96% | -13.04% | 51.16% | -11.78% | +1.26 | +2.80 | 0.9827 | yes |
| sealed_2023_plus | 25.33% | -13.04% | 24.44% | -11.78% | +1.26 | +0.90 | 0.9752 | yes |
| heldout_2019_plus | 17.78% | -22.39% | 17.47% | -21.91% | +0.47 | +0.31 | 0.9807 | yes |
| full | 13.81% | -22.39% | 13.63% | -21.91% | +0.47 | +0.17 | 0.9798 | no |

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
