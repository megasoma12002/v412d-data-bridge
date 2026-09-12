# E45 Month-End Paper Monitor — asof 2026-09-11

Generated: `2026-09-12T13:42:11.104833+00:00`
Status: **OPERATING OBSERVE / PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **CHAL_E45_E3** (E45 `E3_VOLTARGET_WINNER` on early-stack)

> **Dynamic alert windows:** `ytd`, `trailing_1y` (ALERT 3pp / PAUSE 5pp).  
> **Structural windows:** `heldout_2019_plus`, `sealed_2023_plus` (ALERT if MDD worsens or giveback > design+2pp; no structural PAUSE).  
> **`mtd` CAGR is display-only** — **not** a stitch gate.  
> **Stitch / cutover:** always blocked on this observe sleeve.

| Window | BASE CAGR | BASE MDD | CHAL_E45_E3 CAGR | CHAL_E45_E3 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | 869.28%* | -1.35% | 512.09%* | -0.56% | +0.79 | +357.19 | 0.9855 | no |
| ytd | 74.25% | -13.97% | 49.64% | -7.27% | +6.70 | +24.61 | 0.9046 | yes |
| trailing_1y | 56.43% | -13.97% | 35.99% | -7.27% | +6.70 | +20.44 | 0.8746 | yes |
| sealed_2023_plus | 25.93% | -13.97% | 16.38% | -9.51% | +4.45 | +9.55 | 0.7585 | yes |
| heldout_2019_plus | 18.65% | -22.39% | 13.06% | -20.83% | +1.56 | +5.59 | 0.7002 | yes |
| full | 14.07% | -22.39% | 11.07% | -20.83% | +1.56 | +3.00 | 0.7011 | no |

\* `mtd` CAGR annualized from a short sample — **non-decision / display-only**.

## Alerts

- ALERT: CHAL_E45_E3 ytd CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: ytd giveback > 5 pp — extend observe; Soft-Frozen unchanged; no stitch talk
- ALERT: CHAL_E45_E3 trailing_1y CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: trailing_1y giveback > 5 pp — extend observe; Soft-Frozen unchanged; no stitch talk

## Stitch / cutover status

- `stitch_blocked`: **True** (always on observe sleeve)
- `cutover_blocked`: **True**
- `stitch_authorized`: **False**
- Soft-Frozen live clip stays **[0.50, 0.95]** — this monitor never flips it.
- Live DEFAULT books stay **`E22_v2s_tw`**.

## Ops note

- Refresh NAVs: `python3 scripts/e45_dual_paper_ledgers.py`
- Re-run monitor: `python3 scripts/e45_month_end_monitor.py`
- Or month-end pack: `python3 scripts/ops_month_end_paper_pack.py`
- Live stitch still requires a **second dedicated human ACCEPT** after checklist.
