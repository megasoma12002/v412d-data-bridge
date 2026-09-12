# FIN_CAP_50 Month-End Paper Monitor — asof 2026-09-11

Generated: `2026-09-12T13:42:10.497557+00:00`
Status: **PAPER ONLY** — Soft-Frozen live default unchanged.

| Window | BASE CAGR | BASE MDD | FIN_CAP_50 CAGR | FIN_CAP_50 MDD | MDD Δpp | CAGR giveback pp | Rel NAV |
|---|---:|---:|---:|---:|---:|---:|---:|
| mtd | 868.54% | -1.35% | 301.84% | -0.44% | +0.91 | +566.70 | 0.9725 |
| ytd | 74.21% | -13.95% | 54.95% | -7.64% | +6.31 | +19.26 | 0.9257 |
| trailing_1y | 56.39% | -13.95% | 46.55% | -7.64% | +6.31 | +9.85 | 0.9397 |
| heldout_2019_plus | 18.65% | -22.39% | 16.94% | -19.58% | +2.81 | +1.71 | 0.8984 |
| full | 14.07% | -22.39% | 12.89% | -19.58% | +2.81 | +1.18 | 0.8702 |

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
