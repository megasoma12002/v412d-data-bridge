# FIN_CAP_50 Month-End Paper Monitor — asof 2026-09-07

Generated: `2026-09-07T17:02:53.004360+00:00`
Status: **PAPER ONLY** — Soft-Frozen live default unchanged.

| Window | BASE CAGR | BASE MDD | FIN_CAP_50 CAGR | FIN_CAP_50 MDD | MDD Δpp | CAGR giveback pp | Rel NAV |
|---|---:|---:|---:|---:|---:|---:|---:|
| mtd | 1643.44% | 0.00% | 595.35% | 0.00% | +0.00 | +1048.09 | 0.9855 |
| ytd | 71.83% | -15.10% | 53.52% | -7.54% | +7.56 | +18.32 | 0.9301 |
| trailing_1y | 57.90% | -15.10% | 47.93% | -7.54% | +7.56 | +9.97 | 0.9398 |
| heldout_2019_plus | 18.85% | -23.36% | 16.77% | -19.56% | +3.79 | +2.08 | 0.8782 |
| full | 14.19% | -23.36% | 12.84% | -19.56% | +3.79 | +1.35 | 0.8537 |

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
