# FIN_CAP_50 Month-End Paper Monitor — asof 2026-09-08

Generated: `2026-09-09T12:45:20.895464+00:00`
Status: **PAPER ONLY** — Soft-Frozen live default unchanged.

| Window | BASE CAGR | BASE MDD | FIN_CAP_50 CAGR | FIN_CAP_50 MDD | MDD Δpp | CAGR giveback pp | Rel NAV |
|---|---:|---:|---:|---:|---:|---:|---:|
| mtd | 1835.01% | 0.00% | 596.73% | 0.00% | +0.00 | +1238.28 | 0.9799 |
| ytd | 72.42% | -13.95% | 54.85% | -7.64% | +6.31 | +17.57 | 0.9328 |
| trailing_1y | 56.82% | -13.95% | 48.91% | -7.64% | +6.31 | +7.91 | 0.9517 |
| heldout_2019_plus | 18.47% | -22.39% | 16.88% | -19.58% | +2.81 | +1.59 | 0.9053 |
| full | 13.97% | -22.39% | 12.85% | -19.58% | +2.81 | +1.12 | 0.8769 |

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
