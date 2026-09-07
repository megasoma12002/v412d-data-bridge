# L4_DD_PATH Month-End Paper Monitor — asof 2026-09-07

Generated: `2026-09-07T17:20:33.334118+00:00`
Status: **PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **L4_DD_PATH_08_50**

> **Decision windows:** `validation_2019_2022`, `sealed_2023_plus`, `ytd`, `trailing_1y`.  
> **`mtd` CAGR is display-only** (annualized MTD is unstable) — **not** a cutover gate.

| Window | BASE CAGR | BASE MDD | L4 CAGR | L4 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | 1358.33%* | 0.00% | 1283.82%* | 0.00% | +0.00 | +74.51 | 0.9992 | no |
| ytd | 71.95% | -11.41% | 66.64% | -11.36% | +0.05 | +5.30 | 0.9801 | yes |
| trailing_1y | 56.19% | -11.41% | 52.77% | -11.36% | +0.05 | +3.41 | 0.9792 | yes |
| validation_2019_2022 | 11.55% | -22.07% | 11.17% | -20.02% | +2.06 | +0.38 | 0.9868 | yes |
| sealed_2023_plus | 24.41% | -12.04% | 23.51% | -11.36% | +0.68 | +0.90 | 0.9750 | yes |
| heldout_2019_plus | 17.57% | -22.07% | 16.95% | -20.02% | +2.06 | +0.62 | 0.9615 | yes |
| full | 13.43% | -22.07% | 13.36% | -20.02% | +2.06 | +0.06 | 0.9927 | yes |

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
