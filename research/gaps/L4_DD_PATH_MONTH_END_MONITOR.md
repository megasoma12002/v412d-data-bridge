# L4_DD_PATH Month-End Paper Monitor — asof 2026-09-07

Generated: `2026-09-07T15:50:26.337922+00:00`
Status: **PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **L4_DD_PATH_08_50**

> **Decision windows:** `validation_2019_2022`, `sealed_2023_plus`, `ytd`, `trailing_1y`.  
> **`mtd` CAGR is display-only** (annualized MTD is unstable) — **not** a cutover gate.

| Window | BASE CAGR | BASE MDD | L4 CAGR | L4 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | 1461.75%* | 0.00% | 1411.97%* | 0.00% | +0.00 | +49.78 | 0.9995 | no |
| ytd | 68.28% | -12.85% | 67.90% | -13.74% | -0.89 | +0.37 | 0.9986 | yes |
| trailing_1y | 53.33% | -12.85% | 54.15% | -13.74% | -0.89 | -0.82 | 1.0051 | yes |
| validation_2019_2022 | 11.18% | -22.39% | 10.97% | -21.96% | +0.43 | +0.21 | 0.9928 | yes |
| sealed_2023_plus | 25.20% | -12.85% | 24.42% | -13.74% | -0.89 | +0.78 | 0.9783 | yes |
| heldout_2019_plus | 17.72% | -22.39% | 17.26% | -21.96% | +0.43 | +0.46 | 0.9714 | yes |
| full | 13.78% | -22.39% | 13.50% | -21.96% | +0.43 | +0.28 | 0.9676 | yes |

\* `mtd` CAGR annualized from a short sample — **non-decision / display-only**.

## Alerts

Alert windows: `sealed` / `validation` (research gates) and `ytd` / `trailing_1y` (ops). `mtd` is **never** used for alerts or cutover.

- ALERT: L4_DD_PATH_08_50 sealed MDD worse than BASE (paper)

## Ops note

- Refresh NAVs: `python3 scripts/e16_l4_dd_path_dual_paper_ledgers.py`
- Re-run monitor: `python3 scripts/e16_l4_dd_path_month_end_monitor.py`
- Or month-end pack: `python3 scripts/ops_month_end_paper_pack.py`
- Cutover still requires a **separate human PR**; this monitor never flips Soft-Frozen.
