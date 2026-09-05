# L4_DD_PATH Month-End Paper Monitor — asof 2026-09-04

Generated: `2026-09-05T06:42:58.654565+00:00`
Status: **PAPER ONLY** — Soft-Frozen live default unchanged.
Locked: **L4_DD_PATH_08_50**

| Window | BASE CAGR | BASE MDD | L4 CAGR | L4 MDD | MDD Δpp | CAGR giveback pp | Rel NAV |
|---|---:|---:|---:|---:|---:|---:|---:|
| mtd | 2025.06% | 0.00% | 1811.49% | 0.00% | +0.00 | +213.57 | 0.9987 |
| ytd | 68.27% | -14.46% | 62.88% | -12.99% | +1.47 | +5.39 | 0.9794 |
| trailing_1y | 54.37% | -14.46% | 49.72% | -12.99% | +1.47 | +4.65 | 0.9712 |
| validation_2019_2022 | 12.33% | -22.64% | 11.13% | -21.01% | +1.63 | +1.20 | 0.9593 |
| sealed_2023_plus | 24.93% | -14.46% | 22.27% | -12.99% | +1.47 | +2.66 | 0.9279 |
| heldout_2019_plus | 18.24% | -22.64% | 16.37% | -21.01% | +1.63 | +1.86 | 0.8898 |
| full | 13.78% | -22.64% | 13.12% | -21.01% | +1.63 | +0.66 | 0.9252 |

## Alerts

- ALERT: L4_DD_PATH_08_50 ytd CAGR giveback > 3.0 pp (paper ops)
- PAUSE_REVIEW: ytd giveback > 5 pp — extend observation; does not revoke PASS_HELDOUT_L4
- ALERT: L4_DD_PATH_08_50 trailing_1y CAGR giveback > 3.0 pp (paper ops)

## Ops note

- Refresh NAVs: `python3 scripts/e16_l4_dd_path_dual_paper_ledgers.py`
- Re-run monitor: `python3 scripts/e16_l4_dd_path_month_end_monitor.py`
- Cutover still requires a **separate human PR**; this monitor never flips Soft-Frozen.
