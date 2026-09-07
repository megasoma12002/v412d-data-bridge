# E45 Blend-α=0.10 FIN_ONLY Month-End Paper Monitor — asof 2026-09-07

Generated: `2026-09-07T17:20:35.252025+00:00`
Status: **OPERATING OBSERVE / PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **SLEEVE_FIN_ONLY_A10** (α=0.10 FIN_ONLY × E45 `E3_VOLTARGET_WINNER` on early-stack)

> **Dynamic alert windows:** `ytd`, `trailing_1y` (ALERT 3pp / PAUSE 5pp).  
> **Structural windows:** `heldout_2019_plus`, `sealed_2023_plus` (ALERT if MDD worsens or giveback > design+2pp; no structural PAUSE).  
> **`mtd` CAGR is display-only** — **not** a stitch gate.  
> **Stitch / cutover:** always blocked on this observe sleeve.

| Window | BASE CAGR | BASE MDD | SLEEVE_FIN_ONLY_A10 CAGR | SLEEVE_FIN_ONLY_A10 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | 1346.96%* | 0.00% | 1153.87%* | 0.00% | +0.00 | +193.09 | 0.9977 | no |
| ytd | 71.84% | -11.40% | 67.68% | -9.52% | +1.88 | +4.15 | 0.9844 | yes |
| trailing_1y | 56.15% | -11.40% | 51.90% | -9.52% | +1.88 | +4.25 | 0.9741 | yes |
| sealed_2023_plus | 24.50% | -11.84% | 23.02% | -11.93% | -0.09 | +1.48 | 0.9591 | yes |
| heldout_2019_plus | 17.61% | -22.08% | 16.66% | -21.53% | +0.55 | +0.95 | 0.9422 | yes |
| full | 13.44% | -22.08% | 12.96% | -21.53% | +0.55 | +0.48 | 0.9451 | no |

\* `mtd` CAGR annualized from a short sample — **non-decision / display-only**.

## Alerts

- ALERT: SLEEVE_FIN_ONLY_A10 ytd CAGR giveback > 3.0 pp (paper)
- ALERT: SLEEVE_FIN_ONLY_A10 trailing_1y CAGR giveback > 3.0 pp (paper)
- ALERT: SLEEVE_FIN_ONLY_A10 sealed_2023_plus MDD worse than BASE (structural window; design expected MDD improve)

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
