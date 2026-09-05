# FIN_CAP_50 Month-End Paper Monitor — asof 2026-09-04

Generated: `2026-09-05T01:45:27.312074+00:00`
Status: **PAPER ONLY** — Soft-Frozen live default unchanged.

| Window | BASE CAGR | BASE MDD | FIN_CAP_50 CAGR | FIN_CAP_50 MDD | MDD Δpp | CAGR giveback pp | Rel NAV |
|---|---:|---:|---:|---:|---:|---:|---:|
| mtd | 2025.06% | nan% | 528.68% | nan% | +0.00 | +1496.38 | 0.9856 |
| ytd | 68.27% | -14.46% | 51.54% | -7.60% | +6.86 | +16.73 | 0.9353 |
| trailing_1y | 54.37% | -14.46% | 47.16% | -7.60% | +6.86 | +7.21 | 0.9553 |
| heldout_2019_plus | 18.24% | -22.64% | 16.60% | -19.58% | +3.06 | +1.63 | 0.9027 |
| full | 13.78% | -22.64% | 12.70% | -19.58% | +3.06 | +1.08 | 0.8810 |

## Alerts

- None

## Ops note

- Refresh NAVs: `python3 scripts/e16_fincap50_dual_paper_ledgers.py`
- Re-run monitor: `python3 scripts/e16_fincap50_month_end_monitor.py`
- Cutover still requires a **separate human PR**; this monitor never flips Soft-Frozen.
