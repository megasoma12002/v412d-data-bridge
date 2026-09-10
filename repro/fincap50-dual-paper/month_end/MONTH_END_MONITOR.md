# FIN_CAP_50 Month-End Paper Monitor — asof 2026-09-09

Generated: `2026-09-10T10:14:57.645103+00:00`
Status: **PAPER ONLY** — Soft-Frozen live default unchanged.

| Window | BASE CAGR | BASE MDD | FIN_CAP_50 CAGR | FIN_CAP_50 MDD | MDD Δpp | CAGR giveback pp | Rel NAV |
|---|---:|---:|---:|---:|---:|---:|---:|
| mtd | 567.68% | -1.35% | 318.58% | -0.44% | +0.91 | +249.10 | 0.9889 |
| ytd | 68.30% | -13.95% | 53.39% | -7.64% | +6.31 | +14.91 | 0.9414 |
| trailing_1y | 53.13% | -13.95% | 46.69% | -7.64% | +6.31 | +6.43 | 0.9598 |
| heldout_2019_plus | 18.24% | -22.39% | 16.80% | -19.58% | +2.81 | +1.44 | 0.9137 |
| full | 13.85% | -22.39% | 12.81% | -19.58% | +2.81 | +1.04 | 0.8850 |

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
