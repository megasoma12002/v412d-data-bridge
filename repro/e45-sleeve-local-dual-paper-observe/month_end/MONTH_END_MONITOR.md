# E45 Blend-α=0.10 FIN_ONLY Month-End Paper Monitor — asof 2026-09-04

Generated: `2026-09-06T05:28:05.617677+00:00`
Status: **OPERATING OBSERVE / PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **SLEEVE_FIN_ONLY_A10** (α=0.10 FIN_ONLY × E45 `E3_VOLTARGET_WINNER` on early-stack)

> **Dynamic alert windows:** `ytd`, `trailing_1y` (ALERT 3pp / PAUSE 5pp).  
> **Structural windows:** `heldout_2019_plus`, `sealed_2023_plus` (ALERT if MDD worsens or giveback > design+2pp; no structural PAUSE).  
> **`mtd` CAGR is display-only** — **not** a stitch gate.  
> **Stitch / cutover:** always blocked on this observe sleeve.

| Window | BASE CAGR | BASE MDD | SLEEVE_FIN_ONLY_A10 CAGR | SLEEVE_FIN_ONLY_A10 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | 1992.20%* | 0.00% | 1522.46%* | 0.00% | +0.00 | +469.74 | 0.9970 | no |
| ytd | 68.37% | -14.09% | 62.41% | -10.67% | +3.42 | +5.97 | 0.9772 | yes |
| trailing_1y | 54.17% | -14.09% | 47.91% | -10.67% | +3.42 | +6.25 | 0.9612 | yes |
| sealed_2023_plus | 24.89% | -14.09% | 23.09% | -10.67% | +3.42 | +1.80 | 0.9506 | yes |
| heldout_2019_plus | 18.20% | -22.54% | 16.95% | -21.63% | +0.91 | +1.25 | 0.9246 | yes |
| full | 13.79% | -22.54% | 13.23% | -21.63% | +0.91 | +0.56 | 0.9365 | no |

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
