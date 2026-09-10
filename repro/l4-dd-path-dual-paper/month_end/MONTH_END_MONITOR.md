# L4_DD_PATH Month-End Paper Monitor — asof 2026-09-09

Generated: `2026-09-10T10:14:57.322481+00:00`
Status: **PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **L4_DD_PATH_08_50**

> **Decision windows:** `validation_2019_2022`, `sealed_2023_plus`, `ytd`, `trailing_1y`.  
> **`mtd` CAGR is display-only** (annualized MTD is unstable) — **not** a cutover gate.

| Window | BASE CAGR | BASE MDD | L4 CAGR | L4 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | 567.68%* | -1.35% | 551.25%* | -1.21% | +0.13 | +16.44 | 0.9994 | no |
| ytd | 68.30% | -13.95% | 63.17% | -12.85% | +1.10 | +5.13 | 0.9801 | yes |
| trailing_1y | 53.13% | -13.95% | 48.90% | -12.85% | +1.10 | +4.23 | 0.9736 | yes |
| validation_2019_2022 | 12.25% | -22.39% | 11.12% | -20.76% | +1.63 | +1.14 | 0.9613 | yes |
| sealed_2023_plus | 25.02% | -13.95% | 22.40% | -12.85% | +1.10 | +2.61 | 0.9288 | yes |
| heldout_2019_plus | 18.24% | -22.39% | 16.43% | -20.76% | +1.63 | +1.81 | 0.8925 | yes |
| full | 13.85% | -22.39% | 13.17% | -20.76% | +1.63 | +0.69 | 0.9226 | yes |

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
