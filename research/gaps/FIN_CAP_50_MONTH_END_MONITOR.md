# FIN_CAP_50 Month-End Paper Monitor — asof 2026-09-07

Generated: `2026-09-07T17:20:33.647786+00:00`
Status: **PAPER ONLY** — Soft-Frozen live default unchanged.

| Window | BASE CAGR | BASE MDD | FIN_CAP_50 CAGR | FIN_CAP_50 MDD | MDD Δpp | CAGR giveback pp | Rel NAV |
|---|---:|---:|---:|---:|---:|---:|---:|
| mtd | 1358.33% | 0.00% | 595.35% | 0.00% | +0.00 | +762.98 | 0.9883 |
| ytd | 71.95% | -11.41% | 53.52% | -7.54% | +3.87 | +18.43 | 0.9297 |
| trailing_1y | 56.19% | -11.41% | 47.93% | -7.54% | +3.87 | +8.26 | 0.9496 |
| heldout_2019_plus | 17.57% | -22.07% | 16.77% | -19.56% | +2.51 | +0.80 | 0.9508 |
| full | 13.43% | -22.07% | 12.84% | -19.56% | +2.51 | +0.58 | 0.9338 |

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
