# L4_DD_PATH Month-End Paper Monitor — asof 2026-09-07

Generated: `2026-09-07T17:02:52.667429+00:00`
Status: **PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **L4_DD_PATH_08_50**

> **Decision windows:** `validation_2019_2022`, `sealed_2023_plus`, `ytd`, `trailing_1y`.  
> **`mtd` CAGR is display-only** (annualized MTD is unstable) — **not** a cutover gate.

| Window | BASE CAGR | BASE MDD | L4 CAGR | L4 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | 1643.44%* | 0.00% | 1431.98%* | 0.00% | +0.00 | +211.46 | 0.9979 | no |
| ytd | 71.83% | -15.10% | 66.44% | -13.62% | +1.48 | +5.40 | 0.9797 | yes |
| trailing_1y | 57.90% | -15.10% | 53.01% | -13.62% | +1.48 | +4.89 | 0.9705 | yes |
| validation_2019_2022 | 12.84% | -23.36% | 11.40% | -22.13% | +1.23 | +1.44 | 0.9515 | yes |
| sealed_2023_plus | 25.64% | -15.10% | 23.29% | -13.62% | +1.48 | +2.36 | 0.9361 | yes |
| heldout_2019_plus | 18.85% | -23.36% | 16.99% | -22.13% | +1.23 | +1.86 | 0.8901 | yes |
| full | 14.19% | -23.36% | 13.48% | -22.13% | +1.23 | +0.71 | 0.9204 | yes |

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
