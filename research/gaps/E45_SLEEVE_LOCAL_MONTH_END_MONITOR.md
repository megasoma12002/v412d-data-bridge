# E45 Blend-α=0.10 FIN_ONLY Month-End Paper Monitor — asof 2026-09-09

Generated: `2026-09-10T10:14:59.269939+00:00`
Status: **OPERATING OBSERVE / PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **SLEEVE_FIN_ONLY_A10** (α=0.10 FIN_ONLY × E45 `E3_VOLTARGET_WINNER` on early-stack)

> **Dynamic alert windows:** `ytd`, `trailing_1y` (ALERT 3pp / PAUSE 5pp).  
> **Structural windows:** `heldout_2019_plus`, `sealed_2023_plus` (ALERT if MDD worsens or giveback > design+2pp; no structural PAUSE).  
> **`mtd` CAGR is display-only** — **not** a stitch gate.  
> **Stitch / cutover:** always blocked on this observe sleeve.

| Window | BASE CAGR | BASE MDD | SLEEVE_FIN_ONLY_A10 CAGR | SLEEVE_FIN_ONLY_A10 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | 568.21%* | -1.35% | 524.36%* | -1.07% | +0.28 | +43.85 | 0.9984 | no |
| ytd | 68.34% | -13.97% | 63.11% | -10.62% | +3.35 | +5.23 | 0.9797 | yes |
| trailing_1y | 53.17% | -13.97% | 47.46% | -10.62% | +3.35 | +5.71 | 0.9643 | yes |
| sealed_2023_plus | 25.03% | -13.97% | 23.36% | -10.62% | +3.35 | +1.67 | 0.9542 | yes |
| heldout_2019_plus | 18.24% | -22.39% | 17.02% | -21.69% | +0.70 | +1.22 | 0.9266 | yes |
| full | 13.85% | -22.39% | 13.27% | -21.69% | +0.70 | +0.58 | 0.9344 | no |

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
