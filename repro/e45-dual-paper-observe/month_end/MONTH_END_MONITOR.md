# E45 Month-End Paper Monitor — asof 2026-09-07

Generated: `2026-09-07T17:20:34.295764+00:00`
Status: **OPERATING OBSERVE / PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **CHAL_E45_E3** (E45 `E3_VOLTARGET_WINNER` on early-stack)

> **Dynamic alert windows:** `ytd`, `trailing_1y` (ALERT 3pp / PAUSE 5pp).  
> **Structural windows:** `heldout_2019_plus`, `sealed_2023_plus` (ALERT if MDD worsens or giveback > design+2pp; no structural PAUSE).  
> **`mtd` CAGR is display-only** — **not** a stitch gate.  
> **Stitch / cutover:** always blocked on this observe sleeve.

| Window | BASE CAGR | BASE MDD | CHAL_E45_E3 CAGR | CHAL_E45_E3 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | 1346.96%* | 0.00% | 592.60%* | 0.00% | +0.00 | +754.35 | 0.9884 | no |
| ytd | 71.84% | -11.40% | 47.98% | -6.75% | +4.65 | +23.86 | 0.9084 | yes |
| trailing_1y | 56.15% | -11.40% | 36.10% | -6.75% | +4.65 | +20.05 | 0.8773 | yes |
| sealed_2023_plus | 24.50% | -11.84% | 15.88% | -9.64% | +2.20 | +8.62 | 0.7786 | yes |
| heldout_2019_plus | 17.61% | -22.08% | 12.53% | -20.46% | +1.61 | +5.08 | 0.7223 | yes |
| full | 13.44% | -22.08% | 10.76% | -20.46% | +1.61 | +2.69 | 0.7270 | no |

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
