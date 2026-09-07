# FIN_CAP_50 Month-End Paper Monitor — asof 2026-09-07

Generated: `2026-09-07T15:50:26.650204+00:00`
Status: **PAPER ONLY** — Soft-Frozen live default unchanged.

| Window | BASE CAGR | BASE MDD | FIN_CAP_50 CAGR | FIN_CAP_50 MDD | MDD Δpp | CAGR giveback pp | Rel NAV |
|---|---:|---:|---:|---:|---:|---:|---:|
| mtd | 1461.75% | 0.00% | 559.82% | 0.00% | +0.00 | +901.93 | 0.9864 |
| ytd | 68.28% | -12.85% | 52.77% | -7.02% | +5.84 | +15.51 | 0.9397 |
| trailing_1y | 53.33% | -12.85% | 46.49% | -7.02% | +5.84 | +6.84 | 0.9575 |
| heldout_2019_plus | 17.72% | -22.39% | 17.00% | -19.24% | +3.15 | +0.71 | 0.9561 |
| full | 13.78% | -22.39% | 13.07% | -19.24% | +3.15 | +0.70 | 0.9208 |

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
