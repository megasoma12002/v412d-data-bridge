# E45 Blend-α=0.10 FIN_ONLY Month-End Paper Monitor — asof 2026-09-07

Generated: `2026-09-07T17:02:54.671775+00:00`
Status: **OPERATING OBSERVE / PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **SLEEVE_FIN_ONLY_A10** (α=0.10 FIN_ONLY × E45 `E3_VOLTARGET_WINNER` on early-stack)

> **Dynamic alert windows:** `ytd`, `trailing_1y` (ALERT 3pp / PAUSE 5pp).  
> **Structural windows:** `heldout_2019_plus`, `sealed_2023_plus` (ALERT if MDD worsens or giveback > design+2pp; no structural PAUSE).  
> **`mtd` CAGR is display-only** — **not** a stitch gate.  
> **Stitch / cutover:** always blocked on this observe sleeve.

| Window | BASE CAGR | BASE MDD | SLEEVE_FIN_ONLY_A10 CAGR | SLEEVE_FIN_ONLY_A10 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | 1635.40%* | 0.00% | 1371.57%* | 0.00% | +0.00 | +263.83 | 0.9974 | no |
| ytd | 71.86% | -15.09% | 65.87% | -11.72% | +3.37 | +5.99 | 0.9774 | yes |
| trailing_1y | 57.90% | -15.09% | 51.29% | -11.72% | +3.37 | +6.61 | 0.9601 | yes |
| sealed_2023_plus | 25.68% | -15.09% | 23.88% | -11.72% | +3.37 | +1.80 | 0.9508 | yes |
| heldout_2019_plus | 18.89% | -23.37% | 17.52% | -22.22% | +1.15 | +1.37 | 0.9180 | yes |
| full | 14.21% | -23.37% | 13.52% | -22.22% | +1.15 | +0.69 | 0.9221 | no |

\* `mtd` CAGR annualized from a short sample — **non-decision / display-only**.

## Alerts

- ALERT: SLEEVE_FIN_ONLY_A10 ytd CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: ytd giveback > 5 pp — extend observe; Soft-Frozen unchanged; no stitch talk
- ALERT: SLEEVE_FIN_ONLY_A10 trailing_1y CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: trailing_1y giveback > 5 pp — extend observe; Soft-Frozen unchanged; no stitch talk

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
