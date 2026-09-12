# L4_DD_PATH Month-End Paper Monitor — asof 2026-09-11

Generated: `2026-09-12T13:42:10.196216+00:00`
Status: **PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **L4_DD_PATH_08_50**

> **Decision windows:** `validation_2019_2022`, `sealed_2023_plus`, `ytd`, `trailing_1y`.  
> **`mtd` CAGR is display-only** (annualized MTD is unstable) — **not** a cutover gate.

| Window | BASE CAGR | BASE MDD | L4 CAGR | L4 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| mtd | 868.54%* | -1.35% | 831.97%* | -1.21% | +0.13 | +36.57 | 0.9988 | no |
| ytd | 74.21% | -13.95% | 68.81% | -12.85% | +1.10 | +5.41 | 0.9795 | yes |
| trailing_1y | 56.39% | -13.95% | 52.04% | -12.85% | +1.10 | +4.35 | 0.9734 | yes |
| validation_2019_2022 | 12.25% | -22.39% | 11.12% | -20.76% | +1.63 | +1.14 | 0.9613 | yes |
| sealed_2023_plus | 25.92% | -13.95% | 23.27% | -12.85% | +1.10 | +2.65 | 0.9282 | yes |
| heldout_2019_plus | 18.65% | -22.39% | 16.83% | -20.76% | +1.63 | +1.82 | 0.8920 | yes |
| full | 14.07% | -22.39% | 13.38% | -20.76% | +1.63 | +0.69 | 0.9220 | yes |

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
