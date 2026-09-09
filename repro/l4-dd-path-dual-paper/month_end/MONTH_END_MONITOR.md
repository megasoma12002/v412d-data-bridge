# L4_DD_PATH Month-End Paper Monitor — asof 2026-09-08

Generated: `2026-09-09T12:52:46.470081+00:00`
Status: **PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **L4_DD_PATH_08_50**

> **Decision windows:** `validation_2019_2022`, `sealed_2023_plus`, `ytd`, `trailing_1y`.  
> **`mtd` CAGR is display-only** (annualized MTD is unstable) — **not** a cutover gate.

| Window | BASE CAGR | BASE MDD | L4 CAGR | L4 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | 1835.01%* | 0.00% | 1653.75%* | 0.00% | +0.00 | +181.26 | 0.9981 | no |
| ytd | 72.42% | -13.95% | 66.78% | -12.85% | +1.10 | +5.64 | 0.9787 | yes |
| trailing_1y | 56.82% | -13.95% | 52.32% | -12.85% | +1.10 | +4.50 | 0.9725 | yes |
| validation_2019_2022 | 12.25% | -22.39% | 11.12% | -20.76% | +1.63 | +1.14 | 0.9613 | yes |
| sealed_2023_plus | 25.54% | -13.95% | 22.86% | -12.85% | +1.10 | +2.68 | 0.9275 | yes |
| heldout_2019_plus | 18.47% | -22.39% | 16.64% | -20.76% | +1.63 | +1.84 | 0.8913 | yes |
| full | 13.97% | -22.39% | 13.27% | -20.76% | +1.63 | +0.70 | 0.9213 | yes |

\* `mtd` CAGR annualized from a short sample — **non-decision / display-only**.

## Alerts

Alert windows: `sealed` / `validation` (research gates) and `ytd` / `trailing_1y` (ops). `mtd` is **never** used for alerts or cutover.

- ALERT: L4_DD_PATH_08_50 ytd CAGR giveback > 3.0 pp (paper ops)
- PAUSE_REVIEW: ytd giveback > 5 pp — extend observation; does not revoke PASS_HELDOUT_L4
- ALERT: L4_DD_PATH_08_50 trailing_1y CAGR giveback > 3.0 pp (paper ops)

## Ops note

- Refresh NAVs: `python3 scripts/e16_l4_dd_path_dual_paper_ledgers.py`
- Re-run monitor: `python3 scripts/e16_l4_dd_path_month_end_monitor.py`
- Or month-end pack: `python3 scripts/ops_month_end_paper_pack.py`
- Cutover still requires a **separate human PR**; this monitor never flips Soft-Frozen.
