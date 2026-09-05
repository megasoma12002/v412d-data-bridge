# FIN_CAP_50 Month-End Paper Monitor — asof 2026-09-04

Generated: `2026-09-05T07:03:54.377304+00:00`
Status: **PAPER ONLY** — Soft-Frozen live default unchanged.

| Window | BASE CAGR | BASE MDD | FIN_CAP_50 CAGR | FIN_CAP_50 MDD | MDD Δpp | CAGR giveback pp | Rel NAV |
|---|---:|---:|---:|---:|---:|---:|---:|
| mtd | 2025.06% | 0.00% | 528.68% | 0.00% | +0.00 | +1496.38 | 0.9856 |
| ytd | 68.27% | -14.46% | 51.54% | -7.60% | +6.86 | +16.73 | 0.9353 |
| trailing_1y | 54.37% | -14.46% | 47.16% | -7.60% | +6.86 | +7.21 | 0.9553 |
| heldout_2019_plus | 18.24% | -22.64% | 16.60% | -19.58% | +3.06 | +1.63 | 0.9027 |
| full | 13.78% | -22.64% | 12.70% | -19.58% | +3.06 | +1.08 | 0.8810 |

## Alerts

Alert windows (match go-live Gate E): `heldout_2019_plus`, `ytd`, `trailing_1y`. `mtd` CAGR is **display-only / non-decision** (annualized MTD unstable) — **not** used for cutover alerts.

- ALERT: FIN_CAP_50 ytd CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: ytd giveback > 5 pp — do not advance cutover discussion (aligns with FIN_CAP_50_GO_LIVE_VERIFY Gate E)
- ALERT: FIN_CAP_50 trailing_1y CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: trailing_1y giveback > 5 pp — do not advance cutover discussion (aligns with FIN_CAP_50_GO_LIVE_VERIFY Gate E)

## Cutover status

- `cutover_blocked`: **True**
- Authoritative go-live: **`NOT_READY_SEALED_CAGR`** (see `FIN_CAP_50_GO_LIVE_VERIFY.md`)
- Soft-Frozen live clip stays **[0.50, 0.95]** — this monitor never flips it.

## Ops note

- Refresh NAVs: `python3 scripts/e16_fincap50_dual_paper_ledgers.py`
- Re-run monitor: `python3 scripts/e16_fincap50_month_end_monitor.py`
- Cutover still requires a **separate human PR** after go-live READY + clean month-end.
