# E45 Month-End Paper Monitor — asof 2026-09-07

Generated: `2026-09-07T15:50:27.283077+00:00`
Status: **OPERATING OBSERVE / PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **CHAL_E45_E3** (E45 `E3_VOLTARGET_WINNER` on early-stack)

> **Dynamic alert windows:** `ytd`, `trailing_1y` (ALERT 3pp / PAUSE 5pp).  
> **Structural windows:** `heldout_2019_plus`, `sealed_2023_plus` (ALERT if MDD worsens or giveback > design+2pp; no structural PAUSE).  
> **`mtd` CAGR is display-only** — **not** a stitch gate.  
> **Stitch / cutover:** always blocked on this observe sleeve.

| Window | BASE CAGR | BASE MDD | CHAL_E45_E3 CAGR | CHAL_E45_E3 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | 1509.63%* | 0.00% | 840.94%* | 0.00% | +0.00 | +668.69 | 0.9915 | no |
| ytd | 68.87% | -13.04% | 49.75% | -9.47% | +3.57 | +19.12 | 0.9257 | yes |
| trailing_1y | 53.96% | -13.04% | 39.07% | -9.47% | +3.57 | +14.89 | 0.9077 | yes |
| sealed_2023_plus | 25.33% | -13.04% | 17.87% | -9.47% | +3.57 | +7.46 | 0.8072 | yes |
| heldout_2019_plus | 17.78% | -22.39% | 14.20% | -21.64% | +0.74 | +3.58 | 0.7966 | yes |
| full | 13.81% | -22.39% | 11.84% | -21.64% | +0.74 | +1.97 | 0.7928 | no |

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
