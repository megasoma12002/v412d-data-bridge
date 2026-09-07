# BLEND_025 Month-End Paper Monitor — asof 2026-09-07

Generated: `2026-09-07T17:20:33.964591+00:00`
Status: **OPERATING OBSERVE / PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **BLEND_025** (α=0.25·FIN50 + 0.75·BASE)

> **Alert windows:** `heldout_2019_plus`, `sealed_2023_plus`, `ytd`, `trailing_1y`.  
> **`mtd` CAGR is display-only** — **not** a cutover gate.  
> **Cutover:** always blocked on this observe sleeve.

| Window | BASE CAGR | BASE MDD | BLEND_025 CAGR | BLEND_025 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | 1358.33%* | 0.00% | 1126.05%* | 0.00% | +0.00 | +232.27 | 0.9972 | no |
| ytd | 71.95% | -11.41% | 68.64% | -10.12% | +1.29 | +3.31 | 0.9876 | yes |
| trailing_1y | 56.19% | -11.41% | 55.18% | -10.12% | +1.29 | +1.01 | 0.9938 | yes |
| sealed_2023_plus | 24.41% | -12.04% | 24.21% | -11.18% | +0.87 | +0.20 | 0.9943 | yes |
| heldout_2019_plus | 17.57% | -22.07% | 17.50% | -21.29% | +0.78 | +0.07 | 0.9956 | yes |
| full | 13.43% | -22.07% | 13.44% | -21.29% | +0.78 | -0.01 | 1.0010 | yes |

\* `mtd` CAGR annualized from a short sample — **non-decision / display-only**.

## Alerts

- ALERT: BLEND_025 ytd CAGR giveback > 3.0 pp (paper)

## Cutover status

- `cutover_blocked`: **True** (always on observe sleeve)
- `cutover_authorized`: **False**
- Soft-Frozen live clip stays **[0.50, 0.95]** — this monitor never flips it.

## Ops note

- Refresh NAVs: `python3 scripts/e16_blend025_dual_paper_ledgers.py`
- Re-run monitor: `python3 scripts/e16_blend025_month_end_monitor.py`
- Or month-end pack: `python3 scripts/ops_month_end_paper_pack.py`
- Live cutover still requires a **separate human PR** after checklist gates.
